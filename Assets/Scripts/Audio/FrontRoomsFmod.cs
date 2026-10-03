using FMOD.Studio;
using FMODUnity;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// Thin, allocation-free helpers over FMOD for Unity. Every call is a no-op
    /// until FMOD has initialised and its banks really resolve events, and no
    /// call can throw into gameplay code: an FMOD error switches the layer off
    /// and the director hands the sound back to the legacy Unity audio.
    /// </summary>
    public static class FrontRoomsFmod
    {
        static bool failed;
        public static bool Failed => failed;

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

        public static void Note(string what) => Trace("note", what);

        static float nextStartAttempt;

        /// <summary>
        /// FMOD for Unity creates its runtime on first use, and nothing in the scenes
        /// uses it (no emitters or listeners are placed by hand), so the director
        /// starts it. Banks then load per the FMOD settings (all banks).
        /// </summary>
        public static void EnsureStarted()
        {
            if (failed || RuntimeManager.IsInitialized || Time.unscaledTime < nextStartAttempt) return;
            nextStartAttempt = Time.unscaledTime + 1f;
            try
            {
                RuntimeManager.StudioSystem.isValid();
                Note("fmod started");
            }
            catch (System.Exception e)
            {
                failed = true;
                Note("fmod failed: " + e.Message);
                Debug.LogWarning("[FrontRoomsAudio] FMOD failed to start, the legacy Unity audio stays on: " + e.Message);
            }
        }

        public static void WriteTrace(string file)
        {
            if (!Tracing) return;
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(file));
            System.IO.File.WriteAllLines(file, trace);
            Debug.Log("[FrontRoomsAudio] audio trace: " + trace.Count + " requests -> " + file);
        }

        static bool probed;

        /// <summary>
        /// FMOD is usable: initialised, banks loaded, and a known event really resolves
        /// (a runtime with no banks configured reports "all loaded" but finds nothing).
        /// </summary>
        public static bool Ready
        {
            get
            {
                if (failed) return false;
                try
                {
                    if (!RuntimeManager.IsInitialized || !RuntimeManager.HaveAllBanksLoaded) return false;
                    if (probed) return true;
                    if (RuntimeManager.StudioSystem.getEvent(SoundIds.HumBed, out _) == FMOD.RESULT.OK) return probed = true;
                    Fail("FMOD started but no FrontRooms banks are loaded (FMOD settings list no banks; run FrontRooms/Audio/Configure FMOD).");
                    return false;
                }
                catch (System.Exception e)
                {
                    Fail("FMOD unavailable: " + e.Message);
                    return false;
                }
            }
        }

        /// <summary>Audio must never throw into gameplay code: any FMOD error turns the layer off for the session.</summary>
        static void Fail(string why)
        {
            if (failed) return;
            failed = true;
            Note("fmod failed: " + why);
            Debug.LogWarning("[FrontRoomsAudio] " + why + " The legacy Unity audio stays on.");
        }

        public static EventInstance Create(string path, Vector3 position)
        {
            Trace("start", path);
            if (!Ready) return default;
            try
            {
                var instance = RuntimeManager.CreateInstance(path);
                instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
                return instance;
            }
            catch (System.Exception e) { Fail(e.Message); return default; }
        }

        public static EventInstance Create2D(string path)
        {
            Trace("start", path);
            if (!Ready) return default;
            try { return RuntimeManager.CreateInstance(path); }
            catch (System.Exception e) { Fail(e.Message); return default; }
        }

        /// <summary>Fire-and-forget one-shot with up to three parameters.</summary>
        public static void OneShot(string path, Vector3 position, string p1 = null, float v1 = 0f, string p2 = null, float v2 = 0f,
            string p3 = null, float v3 = 0f)
        {
            Trace("oneshot", path, p1, v1, p2, v2, p3, v3);
            if (!Ready) return;
            try
            {
                var instance = RuntimeManager.CreateInstance(path);
                instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
                if (p1 != null) instance.setParameterByName(p1, v1);
                if (p2 != null) instance.setParameterByName(p2, v2);
                if (p3 != null) instance.setParameterByName(p3, v3);
                instance.start();
                instance.release();
            }
            catch (System.Exception e) { Fail(e.Message); }
        }

        public static void OneShot2D(string path, string p1 = null, float v1 = 0f)
        {
            Trace("oneshot", path, p1, v1);
            if (!Ready) return;
            try
            {
                var instance = RuntimeManager.CreateInstance(path);
                if (p1 != null) instance.setParameterByName(p1, v1);
                instance.start();
                instance.release();
            }
            catch (System.Exception e) { Fail(e.Message); }
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
            try { RuntimeManager.StudioSystem.setParameterByName(name, value); }
            catch (System.Exception e) { Fail(e.Message); }
        }

        /// <summary>Looks up a parameter id once so per-frame updates can use setParameterByID.</summary>
        public static FMOD.Studio.PARAMETER_ID ParameterId(string eventPath, string parameter)
        {
            if (!Ready) return default;
            try
            {
                var description = RuntimeManager.GetEventDescription(eventPath);
                description.getParameterDescriptionByName(parameter, out PARAMETER_DESCRIPTION info);
                return info.id;
            }
            catch (System.Exception e) { Fail(e.Message); return default; }
        }

        public static void Move(EventInstance instance, Vector3 position)
        {
            if (instance.isValid()) instance.set3DAttributes(RuntimeUtils.To3DAttributes(position));
        }
    }
}
