using FrontRooms.Map;
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
        // The user has saved or discarded: start from an empty scene so the asset can be created beside it.
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) == null)
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        EnsureSceneAsset();
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
    }

    /// <summary>
    /// Create the scene asset if it is missing, without touching the scenes
    /// that are open. An unsaved, unchanged untitled scene (batch mode starts
    /// with one) is replaced instead, since Unity cannot add a scene beside it.
    /// </summary>
    public static void EnsureSceneAsset()
    {
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) != null) return;
        var active = SceneManager.GetActiveScene();
        var replaceUntitled = string.IsNullOrEmpty(active.path) && SceneManager.sceneCount == 1 && !active.isDirty;
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, replaceUntitled ? NewSceneMode.Single : NewSceneMode.Additive);
        var root = new GameObject("FrontRooms map test");
        SceneManager.MoveGameObjectToScene(root, scene);
        root.AddComponent<FrontRoomsMapWorld>().Profile = FrontRoomsLevelProfiles.EnsureAsset();
        EditorSceneManager.SaveScene(scene, ScenePath);
        if (!replaceUntitled) EditorSceneManager.CloseScene(scene, true);
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

    /// <summary>About 5 km out, on a whole world period (4992 m) so world-projected surfaces line up with the cells as they do at the origin.</summary>
    static Vector3 CaptureOffset => new Vector3(26f * ModuleUnits.WorldPeriod, 0f, 26f * ModuleUnits.WorldPeriod);

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
            CaptureViews(CaptureFolder, CaptureOffset);
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
    /// <summary>
    /// Batch: build the profile's map with the seed given by -captureSeed N
    /// (default 2554, which spawns in an Office zone) and render one view of
    /// the first Level 0, Office and tall-hall column found near the spawn to
    /// Verification/map-columns-*.png.
    /// </summary>
    public static void CaptureColumnsBatch()
    {
        var seed = 2554;
        var args = System.Environment.GetCommandLineArgs();
        for (var i = 0; i < args.Length - 1; i++) if (args[i] == "-captureSeed") int.TryParse(args[i + 1], out seed);
        var root = new GameObject("CAPTURE / columns") { hideFlags = HideFlags.DontSave };
        var profile = Object.Instantiate(FrontRoomsLevelProfiles.Resolve());
        profile.hideFlags = HideFlags.DontSave;
        profile.generation = profile.Generation(seed);
        try
        {
            root.transform.position = CaptureOffset;
            var world = root.AddComponent<FrontRoomsMapWorld>();
            world.Profile = profile;
            world.BuildForCapture();
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
            var found = new System.Collections.Generic.HashSet<string>();
            var spawn = MapGrid.ChunkOf(world.CellOf(world.SpawnWorldPosition));
            const int n = MapGrid.ChunkCells;
            for (var cy = spawn.y - 2; cy <= spawn.y + 2; cy++)
            for (var cx = spawn.x - 2; cx <= spawn.x + 2; cx++)
            {
                var data = world.Cache.Get(new GridCoord(cx, cy));
                for (var r = 0; r < data.rooms.Length; r++)
                {
                    var room = data.rooms[r];
                    for (var j = room.y + 1; j < room.y + room.h; j++)
                    for (var i = room.x + 1; i < room.x + room.w; i++)
                    {
                        if (!data.pillar[i + j * (n + 1)]) continue;
                        var zone = world.ZoneOf(data.Cell(i, j));
                        var kind = zone.height == ZoneHeight.Tall ? "tall" : zone.theme == ZoneTheme.Office ? "office" : "level0";
                        if (!found.Add(kind)) continue;
                        var corner = root.transform.TransformPoint(new Vector3((data.Cell(i, j).x) * MapGrid.CellSize, 0f, (data.Cell(i, j).y) * MapGrid.CellSize));
                        var centre = root.transform.TransformPoint(new Vector3((data.Cell(room.x, room.y).x + room.w * .5f) * MapGrid.CellSize, 0f, (data.Cell(room.x, room.y).y + room.h * .5f) * MapGrid.CellSize));
                        var away = centre - corner;
                        away.y = 0f;
                        if (away.sqrMagnitude < .01f) away = new Vector3(1f, 0f, .6f);
                        away = Quaternion.Euler(0f, 35f, 0f) * away.normalized;
                        var height = MapGrid.CeilingHeight(zone.height);
                        cameraObject.transform.position = corner + away * 3.4f + Vector3.up * ModuleUnits.PlayerEye;
                        cameraObject.transform.LookAt(corner + Vector3.up * Mathf.Min(height * .55f, 2.2f));
                        cam.targetTexture = rt;
                        cam.Render();
                        RenderTexture.active = rt;
                        tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0);
                        tex.Apply();
                        RenderTexture.active = null;
                        File.WriteAllBytes(Path.Combine(CaptureFolder, "map-columns-" + kind + ".png"), tex.EncodeToPNG());
                    }
                }
            }
            // The ceiling straight above the spawn cell, to check troffers sit in whole 0.6 m tiles.
            var spawnFeet = world.SpawnWorldPosition;
            cameraObject.transform.position = spawnFeet + Vector3.up * ModuleUnits.PlayerEye;
            cameraObject.transform.rotation = Quaternion.Euler(-90f, 0f, 0f);
            cam.targetTexture = rt;
            cam.Render();
            RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0);
            tex.Apply();
            RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(CaptureFolder, "map-ceiling.png"), tex.EncodeToPNG());
            cam.targetTexture = null;
            Object.DestroyImmediate(rt);
            Object.DestroyImmediate(tex);
            Debug.Log("[FrontRoomsMap] Column views (seed " + seed + "): " + string.Join(", ", found) + "; ceiling view above the spawn");
        }
        finally
        {
            Object.DestroyImmediate(root);
            Object.DestroyImmediate(profile);
        }
    }

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
            world.Profile = FrontRoomsLevelProfiles.Resolve();
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
