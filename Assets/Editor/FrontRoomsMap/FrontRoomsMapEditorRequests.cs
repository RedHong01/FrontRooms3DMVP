using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;

/// <summary>
/// Lets a coding session drive the open editor without clicking. Once a second
/// it looks for Temp/frontrooms-map-request.txt and, only while the editor is
/// idle (not playing, compiling or importing), runs each line: create-scene,
/// verify, capture. Results go to Temp/frontrooms-map-response.txt. The open
/// scenes are never changed. Delete this file to remove the hook.
/// </summary>
[InitializeOnLoad]
static class FrontRoomsMapEditorRequests
{
    const string RequestPath = "Temp/frontrooms-map-request.txt";
    const string ResponsePath = "Temp/frontrooms-map-response.txt";
    static double nextPoll;

    static FrontRoomsMapEditorRequests()
    {
        EditorApplication.update += Poll;
    }

    static void Poll()
    {
        if (EditorApplication.timeSinceStartup < nextPoll) return;
        nextPoll = EditorApplication.timeSinceStartup + 1d;
        if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
        if (!File.Exists(RequestPath)) return;
        string[] lines;
        try
        {
            lines = File.ReadAllLines(RequestPath);
            File.Delete(RequestPath);
        }
        catch (IOException)
        {
            return;
        }
        var log = new List<string>();
        foreach (var raw in lines)
        {
            var command = raw.Trim();
            if (command.Length == 0) continue;
            try
            {
                switch (command)
                {
                    case "create-scene":
                        FrontRoomsMapTestScene.EnsureSceneAsset();
                        log.Add("create-scene: " + FrontRoomsMapTestScene.ScenePath);
                        break;
                    case "verify":
                        log.Add("verify: " + FrontRoomsMapVerification.Run(false));
                        break;
                    case "capture":
                        FrontRoomsMapTestScene.CaptureInTempScene();
                        log.Add("capture: Verification/map-test-*.png");
                        break;
                    default:
                        log.Add(command + ": unknown command");
                        break;
                }
            }
            catch (Exception e)
            {
                log.Add(command + ": FAILED " + e.GetType().Name + ": " + e.Message);
            }
        }
        File.WriteAllLines(ResponsePath, log);
    }
}
