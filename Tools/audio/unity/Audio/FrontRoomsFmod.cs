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

        /// <summary>
        /// Verification only (-audioTrace on the command line): every sound request is
        /// recorded with its time and parameters, whether or not FMOD could start, so
        /// a batch playtest can prove which gameplay moments reach the audio layer.
        /// </summary>
        public static bool Tracing;
        static readonly System.Collections.Generic.List<string> trace = new System.Collections.Generic.List<string>(512);

        static void Trace(string kind, string path, string p1 = null, float v1 = 0f, string p2 = null, float v2 = 0f, string p3 = null, float v3 = 0f)
        {
            if (!Tracing) return;
            var sb = new System.Text.StringBuilder(96);
            sb.Append(Time.time.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture)).Append('\t').Append(kind).Append('\t').Append(path);
            if (p1 != null) sb.Append('\t').Append(p1).Append('=').Append(v1.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture));
            if (p2 != null) sb.Append('\t').Append(p2).Append('=').Append(v2.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture));
            if (p3 != null) sb.Append('\t').Append(p3).Append('=').Append(v3.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture));
            trace.Add(sb.ToString());
        }

        public static void WriteTrace(string file)
        {
            if (!Tracing) return;
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(file));
            System.IO.File.WriteAllLines(file, trace);
            Debug.Log("[FrontRoomsAudio] audio trace: " + trace.Count + " requests -> " + file);
        }

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
            Trace("start", path);
            if (!Ready) return default;
            var instance = RuntimeManager.CreateInstance(path);
            instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
            return instance;
        }

        public static EventInstance Create2D(string path)
        {
            Trace("start", path);
            if (!Ready) return default;
            return RuntimeManager.CreateInstance(path);
        }

        /// <summary>Fire-and-forget one-shot with up to three parameters.</summary>
        public static void OneShot(string path, Vector3 position, string p1 = null, float v1 = 0f, string p2 = null, float v2 = 0f,
            string p3 = null, float v3 = 0f)
        {
            Trace("oneshot", path, p1, v1, p2, v2, p3, v3);
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
            Trace("oneshot", path, p1, v1);
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
