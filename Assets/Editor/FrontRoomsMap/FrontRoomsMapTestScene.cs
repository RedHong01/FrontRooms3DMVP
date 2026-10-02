using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// The walkable map test scene. It holds one object with FrontRoomsMapWorld;
/// the level, the player and the lights are built when Play starts. The main
/// game scene is not touched.
/// Headless: -executeMethod FrontRoomsMapTestScene.CreateBatch creates the scene,
/// -executeMethod FrontRoomsMapTestScene.CaptureBatch renders four views to Verification/map-test-*.png.
/// </summary>
public static class FrontRoomsMapTestScene
{
    public const string ScenePath = "Assets/Scenes/FrontRoomsMapTest.unity";

    [MenuItem("FrontRooms/Map/Open walkable test scene")]
    public static void Open()
    {
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        EnsureSceneAsset();
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
    }

    /// <summary>Create the scene asset if it is missing, without touching the scenes that are open.</summary>
    public static void EnsureSceneAsset()
    {
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) != null) return;
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
        var root = new GameObject("FrontRooms map test");
        SceneManager.MoveGameObjectToScene(root, scene);
        root.AddComponent<FrontRoomsMapWorld>();
        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorSceneManager.CloseScene(scene, true);
        Debug.Log("[FrontRoomsMap] Created " + ScenePath);
    }

    public static void CreateBatch() => EnsureSceneAsset();

    /// <summary>Batch: create the scene, verify 100 seeds (throws on failure) and capture the four views.</summary>
    public static void PrepareBatch()
    {
        EnsureSceneAsset();
        FrontRoomsMapVerification.Run(true);
        CaptureViews(CaptureFolder, Vector3.zero);
    }

    static string CaptureFolder => Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification");

    [MenuItem("FrontRooms/Map/Capture test views")]
    public static void Capture() => CaptureInTempScene();

    public static void CaptureBatch() => CaptureViews(CaptureFolder, Vector3.zero);

    /// <summary>
    /// Capture inside a temporary additive scene placed 5 km from the origin,
    /// so the open scenes are neither changed nor in shot.
    /// </summary>
    public static void CaptureInTempScene()
    {
        var previous = SceneManager.GetActiveScene();
        var temp = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
        try
        {
            SceneManager.SetActiveScene(temp);
            CaptureViews(CaptureFolder, new Vector3(5000f, 0f, 5000f));
        }
        finally
        {
            if (previous.IsValid() && previous.isLoaded) SceneManager.SetActiveScene(previous);
            EditorSceneManager.CloseScene(temp, true);
        }
    }

    /// <summary>
    /// Builds the 3 x 3 chunks around the spawn in edit mode and renders the
    /// view from the spawn in four directions, at the in-game camera settings.
    /// </summary>
    public static void CaptureViews(string folder, Vector3 offset)
    {
        Directory.CreateDirectory(folder);
        var root = new GameObject("CAPTURE / map test") { hideFlags = HideFlags.DontSave };
        var fog = RenderSettings.fog;
        var fogMode = RenderSettings.fogMode;
        var fogStart = RenderSettings.fogStartDistance;
        var fogEnd = RenderSettings.fogEndDistance;
        var fogColor = RenderSettings.fogColor;
        var ambientMode = RenderSettings.ambientMode;
        var ambient = RenderSettings.ambientLight;
        var pixelLights = QualitySettings.pixelLightCount;
        try
        {
            root.transform.position = offset;
            var world = root.AddComponent<FrontRoomsMapWorld>();
            var eye = world.BuildForCapture();
            // Render only the capture: other open scenes stay out of shot.
            const int layer = 31;
            foreach (var t in root.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = layer;
            var cameraObject = new GameObject("CAPTURE / camera") { hideFlags = HideFlags.DontSave };
            cameraObject.transform.SetParent(root.transform, false);
            var cam = cameraObject.AddComponent<Camera>();
            cam.fieldOfView = 72f;
            cam.nearClipPlane = .05f;
            cam.farClipPlane = world.SightDistance;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = world.FogColor;
            cam.cullingMask = 1 << layer;
            var rt = new RenderTexture(1600, 900, 24) { antiAliasing = 4 };
            var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false);
            var names = new[] { "north", "east", "south", "west" };
            for (var i = 0; i < 4; i++)
            {
                cameraObject.transform.position = eye;
                cameraObject.transform.rotation = Quaternion.Euler(4f, i * 90f, 0f);
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0);
                tex.Apply();
                RenderTexture.active = null;
                File.WriteAllBytes(Path.Combine(folder, "map-test-" + names[i] + ".png"), tex.EncodeToPNG());
            }
            cam.targetTexture = null;
            Object.DestroyImmediate(rt);
            Object.DestroyImmediate(tex);
            Debug.Log("[FrontRoomsMap] Captured 4 views to " + folder);
        }
        finally
        {
            Object.DestroyImmediate(root);
            RenderSettings.fog = fog;
            RenderSettings.fogMode = fogMode;
            RenderSettings.fogStartDistance = fogStart;
            RenderSettings.fogEndDistance = fogEnd;
            RenderSettings.fogColor = fogColor;
            RenderSettings.ambientMode = ambientMode;
            RenderSettings.ambientLight = ambient;
            QualitySettings.pixelLightCount = pixelLights;
        }
    }
}
