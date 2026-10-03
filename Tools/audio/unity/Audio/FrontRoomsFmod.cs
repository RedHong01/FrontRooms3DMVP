using FMOD.Studio;
using FMODUnity;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// Thin, allocation-free helpers over FMOD for Unity. Every call is a no-op
    /// until FMOD has initialised and all banks are loaded, so batchmode
    /// harnesses and builds without audio stay inert.
    /// </summary>
    public static class FrontRoomsFmod
    {
        static bool failed;

        public static bool Ready
        {
            get
            {
                if (failed) return false;
                try { return RuntimeManager.IsInitialized && RuntimeManager.HaveAllBanksLoaded; }
                catch (System.Exception e)
                {
                    failed = true;
                    Debug.LogWarning("[FrontRoomsAudio] FMOD unavailable, audio layer stays silent: " + e.Message);
                    return false;
                }
            }
        }

        public static EventInstance Create(string path, Vector3 position)
        {
            if (!Ready) return default;
            var instance = RuntimeManager.CreateInstance(path);
            instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
            return instance;
        }

        public static EventInstance Create2D(string path)
        {
            if (!Ready) return default;
            return RuntimeManager.CreateInstance(path);
        }

        /// <summary>Fire-and-forget one-shot with up to three parameters.</summary>
        public static void OneShot(string path, Vector3 position, string p1 = null, float v1 = 0f, string p2 = null, float v2 = 0f,
            string p3 = null, float v3 = 0f)
        {
            if (!Ready) return;
            var instance = RuntimeManager.CreateInstance(path);
            instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
            if (p1 != null) instance.setParameterByName(p1, v1);
            if (p2 != null) instance.setParameterByName(p2, v2);
            if (p3 != null) instance.setParameterByName(p3, v3);
            instance.start();
            instance.release();
        }

        public static void OneShot2D(string path, string p1 = null, float v1 = 0f)
        {
            if (!Ready) return;
            var instance = RuntimeManager.CreateInstance(path);
            if (p1 != null) instance.setParameterByName(p1, v1);
            instance.start();
            instance.release();
        }

        public static void Stop(ref EventInstance instance, bool immediate = false)
        {
            if (!instance.isValid()) return;
            instance.stop(immediate ? STOP_MODE.IMMEDIATE : STOP_MODE.ALLOWFADEOUT);
            instance.release();
            instance = default;
        }

        public static void SetGlobal(string name, float value)
        {
            if (!Ready) return;
            RuntimeManager.StudioSystem.setParameterByName(name, value);
        }

        /// <summary>Looks up a parameter id once so per-frame updates can use setParameterByID.</summary>
        public static FMOD.Studio.PARAMETER_ID ParameterId(string eventPath, string parameter)
        {
            var description = RuntimeManager.GetEventDescription(eventPath);
            description.getParameterDescriptionByName(parameter, out PARAMETER_DESCRIPTION info);
            return info.id;
        }

        public static void Move(EventInstance instance, Vector3 position)
        {
            if (instance.isValid()) instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
        }
    }
}
