using FMOD.Studio;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// The Relay's body sound. Footsteps come from the rig's own Step event (a foot
    /// plant from the gait phase), so the footfall can never drift from the
    /// animation. Occlusion counts walls on the line from the listener, so a Relay
    /// in the same room is full-band and one behind walls is muffled and quieter
    /// (FMOD low-pass + level on the event).
    /// </summary>
    public sealed class FrontRoomsRelaySound : MonoBehaviour
    {
        public FrontRoomsMapHunter hunter;
        public FrontRoomsMapWorld map;
        public Transform listener;
        public System.Func<Vector3, float> dampnessAt;

        FrontRoomsRelayRig rig;
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
            lastPosition = transform.position;
        }

        void OnEnable()
        {
            if (rig != null) rig.Step += OnStep;
        }

        void OnDisable()
        {
            if (rig != null) rig.Step -= OnStep;
            FrontRoomsFmod.Stop(ref presence, true);
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
            UpdateOcclusion();
            UpdatePresence(hunter != null && hunter.Released);
        }

        void OnStep(int foot, Vector3 position)
        {
            if (hunter != null && !hunter.Released) return;
            var gait = SoundIds.RelayGait.Walk;
            if (hunter != null && hunter.State == HunterState.Chase) gait = SoundIds.RelayGait.Run;
            else if (speed < 1.2f) gait = SoundIds.RelayGait.Drag;
            var damp = dampnessAt != null ? dampnessAt(position) : .4f;
            FrontRoomsFmod.OneShot(SoundIds.RelayFootstep, position,
                SoundIds.Param.RelayGait, (float)gait, SoundIds.Param.Occlusion, occlusion, SoundIds.Param.Dampness, damp);
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
                var c = hits[i].collider;
                if (c.transform.IsChildOf(transform)) continue;
                // Count only the map's walls, doors and windows, and not an open door's leaf: the same test the
                // hunter's own hearing uses. (The old 'skip anything under the listener's root' skipped every
                // wall, because the map is built under the same root as the player: 3D audit 3D-04.)
                if (map != null ? !map.IsArchitecture(c) || map.IsOpenDoorLeaf(c) : c.transform.IsChildOf(listener)) continue;
                walls++;
            }
            var target = walls == 0 ? 0f : walls == 1 ? .55f : .85f;
            occlusion = Mathf.MoveTowards(occlusion, target, .35f);
        }

        void UpdatePresence(bool released)
        {
            if (!FrontRoomsFmod.Ready || listener == null) return;
            if (!released) { FrontRoomsFmod.Stop(ref presence); return; }
            if (FrontRoomsFmod.Finished(ref presence))
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
    }
}
