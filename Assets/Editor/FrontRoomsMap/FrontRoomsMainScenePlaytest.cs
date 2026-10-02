using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// Plays the main scene unattended: title → Space → noclip → about 75 s in
/// the maze with the Relay, on FrontRooms3DGame's editor-only autopilot.
/// Frames and report.json go to Verification/main-autopilot. In batch mode
/// the editor exits 0 on PASS and 1 otherwise.
/// Run with -executeMethod FrontRoomsMainScenePlaytest.RunBatch (no -quit);
/// add -autopilotSeed N to play a fixed maze.
/// </summary>
[InitializeOnLoad]
public static class FrontRoomsMainScenePlaytest
{
    const string ScenePath = "Assets/Scenes/FrontRooms3D.unity";
    const string ActiveKey = "FrontRooms.Playtest.Active";
    const string DeadlineKey = "FrontRooms.Playtest.Deadline";
    const string PlayedKey = "FrontRooms.Playtest.Played";
    const float TimeoutSeconds = 240f;

    // Entering Play reloads the domain; this re-attaches the watcher.
    static FrontRoomsMainScenePlaytest()
    {
        if (SessionState.GetBool(ActiveKey, false)) EditorApplication.update += Watch;
    }

    [MenuItem("FrontRooms/Map/Play main scene on autopilot")]
    public static void Run()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var done = DonePath;
        if (File.Exists(done)) File.Delete(done);
        SessionState.SetBool(FrontRooms3DGame.AutopilotKey, true);
        SessionState.SetInt(FrontRooms3DGame.AutopilotSeedKey, SeedArgument());
        SessionState.SetBool(ActiveKey, true);
        SessionState.SetFloat(DeadlineKey, (float)EditorApplication.timeSinceStartup + TimeoutSeconds);
        SessionState.EraseBool(PlayedKey);
        EditorApplication.update -= Watch;
        EditorApplication.update += Watch;
        EditorApplication.EnterPlaymode();
    }

    public static void RunBatch() => Run();

    static int SeedArgument()
    {
        var args = System.Environment.GetCommandLineArgs();
        for (var i = 0; i < args.Length - 1; i++)
            if (args[i] == "-autopilotSeed" && int.TryParse(args[i + 1], out var seed)) return seed;
        return 0;
    }

    static string DonePath => Path.Combine(Directory.GetParent(Application.dataPath).FullName, FrontRooms3DGame.AutopilotDoneFile);

    static void Watch()
    {
        if (EditorApplication.isPlaying) SessionState.SetBool(PlayedKey, true);
        var done = File.Exists(DonePath);
        var timedOut = EditorApplication.timeSinceStartup > SessionState.GetFloat(DeadlineKey, float.MaxValue);
        // Play was left before the autopilot finished: clean up now, so the next manual Play is a normal one.
        var aborted = !done && SessionState.GetBool(PlayedKey, false) && !EditorApplication.isPlayingOrWillChangePlaymode;
        if (!done && !timedOut && !aborted) return;
        if (EditorApplication.isPlaying || EditorApplication.isPlayingOrWillChangePlaymode)
        {
            if (EditorApplication.isPlaying) EditorApplication.ExitPlaymode();
            return;
        }
        EditorApplication.update -= Watch;
        SessionState.EraseBool(ActiveKey);
        SessionState.EraseBool(PlayedKey);
        SessionState.EraseBool(FrontRooms3DGame.AutopilotKey);
        SessionState.EraseInt(FrontRooms3DGame.AutopilotSeedKey);
        var verdict = done ? File.ReadAllText(DonePath)
            : aborted ? "FAIL · Play mode was left before the autopilot finished"
            : "FAIL · timed out after " + TimeoutSeconds + " s";
        var passed = verdict.StartsWith("PASS");
        if (passed) Debug.Log("[FrontRoomsPlaytest] " + verdict);
        else Debug.LogError("[FrontRoomsPlaytest] " + verdict);
        if (Application.isBatchMode) EditorApplication.Exit(passed ? 0 : 1);
    }
}
