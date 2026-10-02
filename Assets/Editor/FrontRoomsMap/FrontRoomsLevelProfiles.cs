using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// Finds, creates and wires the level profile asset. Every map tool resolves
/// the profile here, so the debug window, the 100-seed check, the test scene
/// and the main game all read the same numbers.
/// Headless: -executeMethod FrontRoomsLevelProfiles.SetupBatch -quit creates
/// Assets/Levels/FrontRoomsLevel0.asset and assigns it to the main scene.
/// </summary>
public static class FrontRoomsLevelProfiles
{
    const string MainScenePath = "Assets/Scenes/FrontRooms3D.unity";

    /// <summary>The project's level profile: the default asset, else the first one found, else the code defaults.</summary>
    public static FrontRoomsLevelProfile Resolve()
    {
        var profile = AssetDatabase.LoadAssetAtPath<FrontRoomsLevelProfile>(FrontRoomsLevelProfile.DefaultPath);
        if (profile != null) return profile;
        var first = AssetDatabase.FindAssets("t:FrontRoomsLevelProfile")
            .Select(AssetDatabase.GUIDToAssetPath)
            .OrderBy(p => p, System.StringComparer.Ordinal)
            .FirstOrDefault();
        if (first != null) return AssetDatabase.LoadAssetAtPath<FrontRoomsLevelProfile>(first);
        return FrontRoomsLevelProfile.Default;
    }

    /// <summary>The default asset, created from the code defaults if it is missing.</summary>
    public static FrontRoomsLevelProfile EnsureAsset()
    {
        var profile = AssetDatabase.LoadAssetAtPath<FrontRoomsLevelProfile>(FrontRoomsLevelProfile.DefaultPath);
        if (profile != null) return profile;
        var folder = Path.GetDirectoryName(FrontRoomsLevelProfile.DefaultPath).Replace('\\', '/');
        if (!AssetDatabase.IsValidFolder(folder)) AssetDatabase.CreateFolder("Assets", Path.GetFileName(folder));
        profile = ScriptableObject.CreateInstance<FrontRoomsLevelProfile>();
        AssetDatabase.CreateAsset(profile, FrontRoomsLevelProfile.DefaultPath);
        AssetDatabase.SaveAssets();
        Debug.Log("[FrontRoomsMap] Created " + FrontRoomsLevelProfile.DefaultPath + " from the code defaults.");
        return profile;
    }

    [MenuItem("FrontRooms/Map/Select level profile")]
    public static void Select()
    {
        var profile = EnsureAsset();
        Selection.activeObject = profile;
        EditorGUIUtility.PingObject(profile);
    }

    [MenuItem("FrontRooms/Map/Assign level profile to main scene")]
    public static void AssignToMainScene()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        // Open the scene first: opening it unloads assets nothing references yet.
        var scene = EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
        var profile = EnsureAsset();
        var game = Object.FindFirstObjectByType<FrontRooms3DGame>();
        if (game == null)
        {
            Debug.LogError("[FrontRoomsMap] No FrontRooms3DGame in " + MainScenePath);
            return;
        }
        var so = new SerializedObject(game);
        var field = so.FindProperty("levelProfile");
        if (field.objectReferenceValue == profile)
        {
            Debug.Log("[FrontRoomsMap] " + MainScenePath + " already uses " + FrontRoomsLevelProfile.DefaultPath);
            return;
        }
        field.objectReferenceValue = profile;
        so.ApplyModifiedPropertiesWithoutUndo();
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        Debug.Log("[FrontRoomsMap] " + MainScenePath + " now uses " + FrontRoomsLevelProfile.DefaultPath);
    }

    public static void SetupBatch() => AssignToMainScene();
}
