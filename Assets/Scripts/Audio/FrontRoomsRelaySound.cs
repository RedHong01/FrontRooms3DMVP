using FMOD.Studio;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// The Relay's body sound. Foot contacts come from the rig's own legs: a
    /// heel strike is the moment a foot reaches its forward-most point, so the
    /// footfall can never drift from the animation. Occlusion counts walls on
    /// the line from the listener, so a Relay in the same room is full-band
    /// and one behind walls is muffled (FMOD low-pass on the event).
    /// </summary>
    public sealed class FrontRoomsRelaySound : MonoBehaviour
    {
        const float LegReach = .9f;
        const float MinStepGap = .16f;

        public FrontRoomsMapHunter hunter;
        public Transform listener;

        FrontRoomsRelayRig rig;
        Transform legL, legR;
        float prevL, prevR, slopeL, slopeR, lastStepL, lastStepR;
        Vector3 lastPosition;
        float speed, occlusion, nextOcclusionCheck;
        readonly RaycastHit[] hits = new RaycastHit[12];
        EventInstance presence;
        PARAMETER_ID proximityId, occlusionId;
        bool idsReady;

        public float Occlusion => occlusion;
        public float Speed => speed;

        void Awake()
        {
            rig = GetComponent<FrontRoomsRelayRig>();
            if (rig != null) { legL = rig.LegLeft; legR = rig.LegRight; }
            lastPosition = transform.position;
        }

        void Update()
        {
            var dt = Time.deltaTime;
            if (dt <= 0f) return;
            var p = transform.position;
            var delta = p - lastPosition;
            delta.y = 0f;
            lastPosition = p;
            if (delta.magnitude > 3f) return;                         // relayed / teleported closer
            speed = Mathf.Lerp(speed, delta.magnitude / dt, 1f - Mathf.Exp(-dt * 10f));

            var released = hunter != null && hunter.Released;
            if (released) DetectContacts(dt);
            UpdateOcclusion();
            UpdatePresence(released);
        }

        float Reach(Transform leg)
        {
            var foot = leg.TransformPoint(new Vector3(0f, -LegReach, 0f));
            return Vector3.Dot(foot - transform.position, transform.forward);
        }

        void DetectContacts(float dt)
        {
            if (legL == null || legR == null) return;
            var moving = speed > .25f;
            var l = Reach(legL);
            var r = Reach(legR);
            var sl = l - prevL;
            var sr = r - prevR;
            var now = Time.time;
            if (moving && slopeL > 0f && sl <= 0f && l > .05f && now - lastStepL > MinStepGap) { lastStepL = now; Step(legL); }
            if (moving && slopeR > 0f && sr <= 0f && r > .05f && now - lastStepR > MinStepGap) { lastStepR = now; Step(legR); }
            slopeL = sl; slopeR = sr; prevL = l; prevR = r;
        }

        void Step(Transform leg)
        {
            if (!FrontRoomsFmod.Ready) return;
            var gait = SoundIds.RelayGait.Walk;
            if (hunter != null && hunter.State == HunterState.Chase) gait = SoundIds.RelayGait.Run;
            else if (speed < 1.2f) gait = SoundIds.RelayGait.Drag;
            var foot = leg.TransformPoint(new Vector3(0f, -LegReach, 0f));
            FrontRoomsFmod.OneShot(SoundIds.RelayFootstep, foot,
                SoundIds.Param.RelayGait, (float)gait, SoundIds.Param.Occlusion, occlusion);
        }

        void UpdateOcclusion()
        {
            if (listener == null || Time.time < nextOcclusionCheck) return;
            nextOcclusionCheck = Time.time + .1f;
            var from = listener.position;
            var to = transform.position + Vector3.up * 1.4f;
            var dir = to - from;
            var dist = dir.magnitude;
            if (dist < .01f) return;
            var count = Physics.RaycastNonAlloc(from, dir / dist, hits, dist, ~0, QueryTriggerInteraction.Ignore);
            var walls = 0;
            for (var i = 0; i < count; i++)
            {
                var t = hits[i].collider.transform;
                if (t.IsChildOf(transform) || t.IsChildOf(listener.root)) continue;
                walls++;
            }
            var target = walls == 0 ? 0f : walls == 1 ? .55f : .85f;
            occlusion = Mathf.MoveTowards(occlusion, target, .35f);
        }

        void UpdatePresence(bool released)
        {
            if (!FrontRoomsFmod.Ready || listener == null) return;
            if (!released) { FrontRoomsFmod.Stop(ref presence); return; }
            if (!presence.isValid())
            {
                presence = FrontRoomsFmod.Create(SoundIds.RelayPresence, transform.position);
                if (!presence.isValid()) return;
                if (!idsReady)
                {
                    proximityId = FrontRoomsFmod.ParameterId(SoundIds.RelayPresence, SoundIds.Param.Proximity);
                    occlusionId = FrontRoomsFmod.ParameterId(SoundIds.RelayPresence, SoundIds.Param.Occlusion);
                    idsReady = true;
                }
                presence.start();
            }
            var proximity = 1f - Mathf.Clamp01(Vector3.Distance(listener.position, transform.position) / 30f);
            presence.setParameterByID(proximityId, proximity);
            presence.setParameterByID(occlusionId, occlusion);
            FrontRoomsFmod.Move(presence, transform.position + Vector3.up * 1.2f);
        }

        void OnDisable() => FrontRoomsFmod.Stop(ref presence, true);
    }
}
