using FMOD.Studio;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// Door Foley driven by the hinge's actual rotation, read every frame, so
    /// the sound shares the door's own clock: it starts when the leaf starts
    /// moving and stops when it stops, whatever the trajectory (half open,
    /// re-pushed, slammed, broken open).
    ///
    /// Manual (map doors) and Automatic: Handle + Unlatch (or AutoOperator)
    /// when it leaves the frame, a Swing loop driven by |angular velocity|
    /// while it moves, then exactly one of StopLimit / StopMid / LatchStrike
    /// when it comes to rest.
    ///
    /// Stream (the room stream's double doors): a scripted swing, 0 to 88
    /// degrees in 0.9 s on a smoothstep, both leaves together, pushed by
    /// nobody. Each leaf plays one recorded swing for the whole motion:
    /// StreamOpen out of the frame, StreamClose back into it. The left leaf
    /// is the Lead, the right the Follow (other takes, 28 ms later), so a
    /// pair never doubles; the pair's own layers ride on the Lead. The swing
    /// eases to zero speed, so nothing plays at rest, except StreamLock once
    /// the terminal door is shut for good. Snapping shut for recycling is a
    /// jump, not a motion: silent.
    /// </summary>
    public sealed class FrontRoomsDoorSound : MonoBehaviour
    {
        public enum Mode { Manual, Automatic, Stream }

        const float MoveStart = 6f;        // deg/s to count as moving
        const float MoveStop = 2f;         // deg/s to count as stopped
        const float VelocityFull = 320f;   // deg/s that maps to AngularVelocity 1
        const float ClosedAngle = 1.5f;    // degrees from closed
        const float LockHeight = 1.05f;    // Stream: the lock sits at the meeting stiles, at hand height

        public Mode mode = Mode.Manual;
        public float openLimit = 95f;
        /// <summary>Stream mode, set by the director: the pair's other hinge (may be null) and this leaf's role.</summary>
        public Transform pairedHinge;
        public SoundIds.Leaf leaf;

        Quaternion closed;
        float previousAngle, lastMovingSpeed, stillTime;
        bool moving, initialised;
        EventInstance swing;
        PARAMETER_ID velocityId, opennessId;
        bool idsReady;
        bool broken;
        float suppressedUntil;

        // Stream mode
        Vector3 leafCentre;                // hinge-local centre of the leaf, measured shut
        FrontRoomsRoomStream stream;
        bool closing;

        static readonly System.Collections.Generic.List<FrontRoomsDoorSound> active = new System.Collections.Generic.List<FrontRoomsDoorSound>();
        const float DoorReach = 1.6f;      // a door's hinges sit within this of the position MapWorld reports for it

        /// <summary>The door at this position was broken down: its leaves no longer make door Foley.</summary>
        public static void MarkBroken(Vector3 doorPosition)
        {
            foreach (var d in active)
                if ((d.transform.position - doorPosition).sqrMagnitude < DoorReach * DoorReach) { d.broken = true; d.Silence(); }
        }

        /// <summary>The door at this position is being struck or rattled: ignore its leaf motion for a while.</summary>
        public static void Suppress(Vector3 doorPosition, float seconds)
        {
            foreach (var d in active)
                if ((d.transform.position - doorPosition).sqrMagnitude < DoorReach * DoorReach)
                {
                    d.suppressedUntil = Mathf.Max(d.suppressedUntil, Time.time + seconds);
                    d.Silence();
                }
        }

        void Silence()
        {
            moving = false;
            FrontRoomsFmod.Stop(ref swing, true);
        }

        void OnEnable() => active.Add(this);

        public float Openness => Mathf.Clamp01(previousAngle / openLimit);

        void Start()
        {
            closed = transform.localRotation;
            previousAngle = 0f;
            if (mode == Mode.Stream)
            {
                leafCentre = LeafCentre();
                stream = GetComponentInParent<FrontRoomsRoomStream>();
            }
            initialised = true;
        }

        void LateUpdate()
        {
            if (!initialised) return;
            var dt = Time.deltaTime;
            if (dt <= 0f) return;
            var angle = Quaternion.Angle(closed, transform.localRotation);
            if (Mathf.Abs(angle - previousAngle) > 45f)
            {
                // A pooled room was recycled and its leaves snapped back: not a motion, no sound.
                // A recycled door is a new, intact door.
                broken = false;
                Silence();
                previousAngle = angle;
                return;
            }
            if (broken || Time.time < suppressedUntil)
            {
                previousAngle = angle;
                return;
            }
            var speed = Mathf.Abs(angle - previousAngle) / dt;

            if (!moving && speed > MoveStart)
                BeginMotion(angle);
            if (moving)
            {
                if (speed > MoveStop)
                {
                    stillTime = 0f;
                    lastMovingSpeed = speed;
                    UpdateSwing(angle, speed);
                }
                else if ((stillTime += dt) > .05f)
                {
                    EndMotion(angle);
                }
            }
            previousAngle = angle;
        }

        void BeginMotion(float angle)
        {
            moving = true;
            stillTime = 0f;
            if (mode == Mode.Stream)
            {
                BeginStreamSwing(angle);
                return;
            }
            var p = transform.position;
            if (mode == Mode.Automatic)
            {
                // The operator motor drives the leaf both ways: out of the frame and back from the stop.
                if (previousAngle < ClosedAngle || previousAngle >= openLimit - 3f)
                    FrontRoomsFmod.OneShot(SoundIds.DoorAutoOperator, p);
            }
            else if (previousAngle < ClosedAngle)
            {
                FrontRoomsFmod.OneShot(SoundIds.DoorHandle, p);
                FrontRoomsFmod.OneShot(SoundIds.DoorUnlatch, p);
            }
            if (!idsReady && FrontRoomsFmod.Ready)
            {
                velocityId = FrontRoomsFmod.ParameterId(SoundIds.DoorSwing, SoundIds.Param.AngularVelocity);
                opennessId = FrontRoomsFmod.ParameterId(SoundIds.DoorSwing, SoundIds.Param.Openness);
                idsReady = true;
            }
            swing = FrontRoomsFmod.Create(SoundIds.DoorSwing, p);
            if (swing.isValid()) swing.start();
        }

        void UpdateSwing(float angle, float speed)
        {
            if (!swing.isValid()) return;
            swing.setParameterByID(velocityId, Mathf.Clamp01(speed / VelocityFull));
            swing.setParameterByID(opennessId, Mathf.Clamp01(angle / openLimit));
            FrontRoomsFmod.Move(swing, transform.position);
        }

        void EndMotion(float angle)
        {
            moving = false;
            if (mode == Mode.Stream)
            {
                EndStreamSwing(angle);
                return;
            }
            FrontRoomsFmod.Stop(ref swing);
            var impact = Mathf.Clamp01(lastMovingSpeed / VelocityFull);
            var p = transform.position;
            if (angle >= openLimit - 3f)
                FrontRoomsFmod.OneShot(SoundIds.DoorStopLimit, p, SoundIds.Param.Impact, impact);
            else if (angle <= ClosedAngle)
                FrontRoomsFmod.OneShot(SoundIds.DoorLatchStrike, p, SoundIds.Param.Impact, impact);
            else
                FrontRoomsFmod.OneShot(SoundIds.DoorStopMid, p);
        }

        // ------------------------------------------------------------ stream doors
        /// <summary>
        /// One recorded swing per leaf covers the whole scripted motion, so no Swing loop and no
        /// operator. The direction picks the take; the event gives Lead and Follow disjoint takes
        /// and starts the Follow 28 ms later.
        /// </summary>
        void BeginStreamSwing(float angle)
        {
            closing = angle < previousAngle;
            FrontRoomsFmod.OneShot(closing ? SoundIds.DoorStreamClose : SoundIds.DoorStreamOpen,
                transform.TransformPoint(leafCentre), SoundIds.Param.Leaf, (float)leaf);
        }

        /// <summary>
        /// The scripted swing eases to zero speed: no stop, settle or latch hit (StreamClose carries
        /// its own seat on the stop). The one rest that is heard on its own is the terminal door
        /// shut for good behind the player, once per pair, from the Lead.
        /// </summary>
        void EndStreamSwing(float angle)
        {
            if (!closing || angle > ClosedAngle || leaf != SoundIds.Leaf.Lead) return;
            if (stream == null || !stream.TerminalDoorShut) return;
            var centre = pairedHinge != null ? (transform.position + pairedHinge.position) * .5f : transform.position;
            FrontRoomsFmod.OneShot(SoundIds.DoorStreamLock, centre + Vector3.up * LockHeight);
        }

        /// <summary>The leaf is the largest renderer under the hinge (the pull bars are small).</summary>
        Vector3 LeafCentre()
        {
            var best = 0f;
            var centre = Vector3.up * 1.2f;
            foreach (var r in GetComponentsInChildren<Renderer>())
            {
                var size = r.bounds.size;
                var volume = size.x * size.y * size.z;
                if (volume <= best) continue;
                best = volume;
                centre = transform.InverseTransformPoint(r.bounds.center);
            }
            return centre;
        }

        void OnDisable()
        {
            active.Remove(this);
            Silence();
        }
    }
}
