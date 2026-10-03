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
    /// Modules: Handle + Unlatch (or AutoOperator) when it leaves the frame,
    /// a Swing loop driven by |angular velocity| while it moves, then exactly
    /// one of StopLimit / StopMid / LatchStrike when it comes to rest.
    /// </summary>
    public sealed class FrontRoomsDoorSound : MonoBehaviour
    {
        public enum Mode { Manual, Automatic }

        const float MoveStart = 6f;        // deg/s to count as moving
        const float MoveStop = 2f;         // deg/s to count as stopped
        const float VelocityFull = 320f;   // deg/s that maps to AngularVelocity 1
        const float ClosedAngle = 1.5f;    // degrees from closed

        public Mode mode = Mode.Manual;
        public float openLimit = 95f;

        Quaternion closed;
        float previousAngle, lastMovingSpeed, stillTime;
        bool moving, initialised;
        EventInstance swing;
        PARAMETER_ID velocityId, opennessId;
        bool idsReady;

        public float Openness => Mathf.Clamp01(previousAngle / openLimit);

        void Start()
        {
            closed = transform.localRotation;
            previousAngle = 0f;
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
                moving = false;
                FrontRoomsFmod.Stop(ref swing, true);
                previousAngle = angle;
                return;
            }
            var speed = Mathf.Abs(angle - previousAngle) / dt;

            if (!moving && speed > MoveStart)
                BeginMotion();
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

        void BeginMotion()
        {
            moving = true;
            stillTime = 0f;
            if (!FrontRoomsFmod.Ready) return;
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
            if (!idsReady)
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

        void OnDisable()
        {
            moving = false;
            FrontRoomsFmod.Stop(ref swing, true);
        }
    }
}
