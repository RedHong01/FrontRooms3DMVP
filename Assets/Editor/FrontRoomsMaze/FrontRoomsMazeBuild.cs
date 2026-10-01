using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using FrontRooms.Maze;

public static class FrontRoomsMazeBuild
{
    const string RootName = "EDITOR_PREVIEW / Level 0 maze";

    [MenuItem("FrontRooms/Maze/Build or refresh editor preview")]
    public static void BuildPreview()
    {
        var game = Object.FindFirstObjectByType<FrontRooms3DGame>();
        var parent = game == null ? null : game.transform;
        var existing = GameObject.Find(RootName);
        if (existing == null)
        {
            existing = new GameObject(RootName);
            if (parent != null) existing.transform.SetParent(parent, false);
        }
        var preview = existing.GetComponent<FrontRoomsMazePreview>() ?? existing.AddComponent<FrontRoomsMazePreview>();
        preview.Rebuild();
        EditorUtility.SetDirty(existing);
        EditorSceneManager.MarkSceneDirty(existing.scene);
        EditorSceneManager.SaveOpenScenes();
        var report = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "maze-layout-latest.json");
        Directory.CreateDirectory(Path.GetDirectoryName(report));
        File.WriteAllText(report, JsonUtility.ToJson(preview.spec, true));
        Debug.Log("[FrontRoomsMaze] Built seed " + preview.seed + " · " + preview.spec.validation.reachableCells + "/" + preview.spec.validation.totalCells + " cells reachable · " + report);
    }

    [MenuItem("FrontRooms/Maze/Verify 25 seeds")]
    public static void VerifySeeds()
    {
        var failures = 0;
        for (var i = 0; i < 25; i++)
        {
            var spec = FrontRoomsMazeGenerator.Generate(20261001 + i * 7919);
            if (spec.validation == null || !spec.validation.passed) failures++;
        }
        Debug.Log("[FrontRoomsMaze] " + (failures == 0 ? "PASS" : "FAIL") + " · " + (25 - failures) + "/25 seeds");
    }
}
