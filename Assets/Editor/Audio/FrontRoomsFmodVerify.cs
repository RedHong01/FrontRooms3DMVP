using System.Collections.Generic;
using System.IO;
using FrontRooms.Audio;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Contract check between the game code and the built FMOD banks: every
/// event path and parameter the audio layer uses must exist in the banks.
/// Runs its own FMOD Studio system in the editor, so it needs no play mode.
///
/// Batch: Unity -batchmode -projectPath &lt;project&gt; -executeMethod FrontRoomsFmodVerify.RunBatch
/// </summary>
public static class FrontRoomsFmodVerify
{
    const string BankFolder = "FMOD/FrontRooms/Build/Desktop";

    static readonly Dictionary<string, string[]> Contract = new Dictionary<string, string[]>
    {
        { SoundIds.HumBed, new[] { SoundIds.Param.Tension } },
        { SoundIds.AirBed, new[] { SoundIds.Param.Zone } },
        { SoundIds.Fixture, new[] { SoundIds.Param.Level } },
        { SoundIds.FixtureEvent, new[] { SoundIds.Param.FixtureEvent } },
        { SoundIds.DoorHandle, new string[0] },
        { SoundIds.DoorUnlatch, new string[0] },
        { SoundIds.DoorSwing, new[] { SoundIds.Param.AngularVelocity, SoundIds.Param.Openness } },
        { SoundIds.DoorStopLimit, new[] { SoundIds.Param.Impact } },
        { SoundIds.DoorStopMid, new string[0] },
        { SoundIds.DoorLatchStrike, new[] { SoundIds.Param.Impact } },
        { SoundIds.DoorLocked, new string[0] },
        { SoundIds.DoorBlow, new[] { SoundIds.Param.Damage } },
        { SoundIds.DoorBreak, new string[0] },
        { SoundIds.DoorAutoOperator, new string[0] },
        { SoundIds.DoorStreamOpen, new[] { SoundIds.Param.Leaf } },
        { SoundIds.DoorStreamClose, new[] { SoundIds.Param.Leaf } },
        { SoundIds.DoorStreamLock, new string[0] },
        { SoundIds.WindowStress, new[] { SoundIds.Param.Progress } },
        { SoundIds.WindowCrack, new string[0] },
        { SoundIds.WindowShatter, new string[0] },
        { SoundIds.Footstep, new[] { SoundIds.Param.Surface, SoundIds.Param.Gait, SoundIds.Param.Dampness } },
        { SoundIds.Cloth, new string[0] },
        { SoundIds.KeyPickup, new string[0] },
        { SoundIds.RelayFootstep, new[] { SoundIds.Param.RelayGait, SoundIds.Param.Occlusion, SoundIds.Param.Dampness } },
        { SoundIds.RelayPresence, new[] { SoundIds.Param.Proximity, SoundIds.Param.Occlusion } },
        { SoundIds.RelayClicks, new string[0] },
        { SoundIds.RelayStinger, new[] { SoundIds.Param.RelayState } },
        { SoundIds.Breath, new[] { SoundIds.Param.Stamina } },
        { SoundIds.Heartbeat, new[] { SoundIds.Param.Proximity } },
        { SoundIds.Tinnitus, new string[0] },
        { SoundIds.MusicTitle, new string[0] },
    };

    static readonly string[] Globals = { SoundIds.Param.Tension, SoundIds.Param.Zone, SoundIds.Param.Tier };
    static readonly string[] Buses = { SoundIds.BusAmbience, SoundIds.BusSfx, SoundIds.BusMusic, SoundIds.BusSubjective };

    [MenuItem("FrontRooms/Audio/Verify FMOD banks against code")]
    public static bool Verify()
    {
        var failures = new List<string>();
        FMOD.Studio.System.create(out var system);
        system.initialize(64, FMOD.Studio.INITFLAGS.NORMAL, FMOD.INITFLAGS.NORMAL, System.IntPtr.Zero);
        try
        {
            var folder = Path.GetFullPath(BankFolder);
            foreach (var bank in new[] { "Master.bank", "Master.strings.bank", "Ambience.bank", "SFX.bank", "Music.bank" })
            {
                var result = system.loadBankFile(Path.Combine(folder, bank), FMOD.Studio.LOAD_BANK_FLAGS.NORMAL, out _);
                if (result != FMOD.RESULT.OK) failures.Add("bank " + bank + ": " + result);
            }
            foreach (var pair in Contract)
            {
                if (system.getEvent(pair.Key, out var description) != FMOD.RESULT.OK) { failures.Add("missing event " + pair.Key); continue; }
                foreach (var parameter in pair.Value)
                    if (description.getParameterDescriptionByName(parameter, out _) != FMOD.RESULT.OK)
                        failures.Add("missing parameter " + parameter + " on " + pair.Key);
            }
            foreach (var parameter in Globals)
                if (system.getParameterDescriptionByName(parameter, out _) != FMOD.RESULT.OK) failures.Add("missing global parameter " + parameter);
            foreach (var bus in Buses)
                if (system.getBus(bus, out _) != FMOD.RESULT.OK) failures.Add("missing bus " + bus);
        }
        finally
        {
            system.release();
        }
        if (failures.Count == 0) Debug.Log("[FrontRoomsAudio] FMOD contract OK: " + Contract.Count + " events, " + Globals.Length + " globals, " + Buses.Length + " buses");
        else Debug.LogError("[FrontRoomsAudio] FMOD contract FAILED:\n" + string.Join("\n", failures));
        return failures.Count == 0;
    }

    public static void RunBatch()
    {
        EditorApplication.Exit(Verify() ? 0 : 1);
    }
}
