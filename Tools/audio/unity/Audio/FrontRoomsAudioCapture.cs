using System.Collections.Generic;
using FMODUnity;
using UnityEngine;

namespace FrontRooms.Audio
{
    /// <summary>
    /// Verification only (-audioCapture on the command line, never in normal play): records
    /// what a run actually sounds like, so a playtest proves which audio system is heard.
    /// - FMOD: once FMOD is ready its output is switched to FMOD's WAV writer, so the real
    ///   in-game FMOD mix lands in "fmodoutput.wav" in the working directory.
    /// - Unity: built-in audio is disabled in ProjectSettings (m_DisableAudio), so legacy
    ///   AudioSources cannot make sound at all; the status line still lists any that think
    ///   they are playing.
    /// - Once a second the trace gets the FMOD channel count and the legacy state
    ///   (listener volume, which AudioSources are playing).
    /// </summary>
    public sealed class FrontRoomsAudioCapture : MonoBehaviour
    {
        bool fmodCapturing;
        float nextStatus;

        public static bool Requested => System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-audioCapture") >= 0;

        void Update()
        {
            if (!fmodCapturing && FrontRoomsFmod.Ready)
            {
                fmodCapturing = true;
                var r = RuntimeManager.CoreSystem.setOutput(FMOD.OUTPUTTYPE.WAVWRITER);
                FrontRoomsFmod.Note("capture fmod " + r + " -> " + System.IO.Path.Combine(System.IO.Directory.GetCurrentDirectory(), "fmodoutput.wav"));
            }
            if (Time.unscaledTime >= nextStatus && fmodCapturing)
            {
                nextStatus = Time.unscaledTime + 1f;
                RuntimeManager.CoreSystem.getChannelsPlaying(out var channels, out var real);
                var playing = new List<string>();
                foreach (var source in FindObjectsByType<AudioSource>(FindObjectsSortMode.None))
                    if (source.isPlaying) playing.Add(source.clip != null ? source.clip.name : source.gameObject.name);
                FrontRoomsFmod.Note("status fmod channels=" + channels + " real=" + real + " | legacy listener=" +
                                    AudioListener.volume.ToString("0.00") + " playing=" + playing.Count +
                                    (playing.Count > 0 ? " [" + string.Join(",", playing.GetRange(0, Mathf.Min(6, playing.Count))) + "]" : ""));
            }
        }
    }
}
