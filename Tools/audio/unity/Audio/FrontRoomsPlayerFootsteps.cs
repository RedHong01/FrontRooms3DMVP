using System;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// Player foot contacts from distance travelled, not a timer: the cadence
    /// follows the real speed (wall slides, stamina drop, stopping). Also
    /// mirrors the game's stamina rule (5 s sprint, recover after 1 s) to
    /// drive the breath layer without reaching into the game's private state.
    /// </summary>
    public sealed class FrontRoomsPlayerFootsteps : MonoBehaviour
    {
        const float WalkSpeed = 3.2f, RunSpeed = 5.5f;
        const float WalkStride = 1.45f, RunStride = 1.72f;
        const float StaminaSeconds = 5f, RecoverDelay = 1f, RecoverRate = 1f;

        public Func<Vector3, SoundIds.Surface> surfaceAt;

        CharacterController body;
        Vector3 last;
        float distance, speed, stamina = StaminaSeconds, sinceSprint;
        bool wasMoving;

        public float Speed => speed;
        public float Stamina01 => stamina / StaminaSeconds;
        public bool Sprinting { get; private set; }

        void Awake()
        {
            body = GetComponent<CharacterController>();
            last = transform.position;
        }

        void Update()
        {
            var dt = Time.deltaTime;
            if (dt <= 0f) return;
            var p = transform.position;
            var delta = p - last;
            delta.y = 0f;
            last = p;
            var step = delta.magnitude;
            if (step > 2f) { distance = 0f; return; }                // respawn / teleport

            speed = Mathf.Lerp(speed, step / dt, 1f - Mathf.Exp(-dt * 12f));
            Sprinting = speed > 4.4f;
            if (Sprinting) { stamina = Mathf.Max(0f, stamina - dt); sinceSprint = 0f; }
            else
            {
                sinceSprint += dt;
                if (sinceSprint > RecoverDelay) stamina = Mathf.Min(StaminaSeconds, stamina + RecoverRate * dt);
            }

            var grounded = body == null || body.isGrounded;
            var moving = grounded && speed > .4f;
            if (moving)
            {
                var stride = Mathf.Lerp(WalkStride, RunStride, Mathf.InverseLerp(WalkSpeed, RunSpeed, speed));
                if (!wasMoving) distance = stride * .6f;              // the first step lands soon after starting
                distance += step;
                if (distance >= stride)
                {
                    distance -= stride;
                    Contact(Sprinting ? SoundIds.Gait.Run : SoundIds.Gait.Walk);
                }
                wasMoving = true;
            }
            else if (wasMoving && speed < .25f)
            {
                Contact(SoundIds.Gait.Stop);
                wasMoving = false;
                distance = 0f;
            }
        }

        Vector3 Feet()
        {
            if (body == null) return transform.position;
            return transform.TransformPoint(body.center) - Vector3.up * (body.height * .5f);
        }

        void Contact(SoundIds.Gait gait)
        {
            if (!FrontRoomsFmod.Ready) return;
            var feet = Feet();
            var surface = surfaceAt != null ? surfaceAt(feet) : SoundIds.Surface.Carpet;
            FrontRoomsFmod.OneShot(SoundIds.Footstep, feet,
                SoundIds.Param.Surface, (float)surface, SoundIds.Param.Gait, (float)gait);
        }
    }
}
