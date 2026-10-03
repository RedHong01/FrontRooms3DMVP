using System.Collections.Generic;
using System.IO;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// The Level Designer (P1): the preview scene on the left (Scene or Game
/// view), the selected room module's Inspector on the right
/// (FrontRoomsRoomModuleEditor). Menu: FrontRooms → Level Designer.
/// Headless: -executeMethod FrontRoomsLevelDesigner.SetupBatch -quit creates the
/// scene and the sample modules; CaptureBatch renders every module to
/// Verification/designer-*.png.
/// </summary>
public static class FrontRoomsLevelDesigner
{
    public const string ScenePath = "Assets/Scenes/FrontRoomsLevelDesigner.unity";

    [MenuItem("FrontRooms/Level Designer/Open", priority = 0)]
    public static void OpenMenu() => Open(Selection.activeObject as FrontRoomsRoomModule ?? Modules().FirstOrDefault());

    /// <summary>Open the preview scene on a module and select it, so its Inspector is the right-hand panel.</summary>
    public static void Open(FrontRoomsRoomModule module)
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return;
        if (!Application.isBatchMode && SceneManager.GetActiveScene().path != ScenePath && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        // The user has saved or discarded: start from an empty scene so the designer scene can be created beside nothing.
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) == null && SceneManager.GetActiveScene().path != ScenePath)
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        EnsureScene();
        if (SceneManager.GetActiveScene().path != ScenePath) EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var preview = Object.FindFirstObjectByType<FrontRoomsModulePreview>();
        if (preview != null && module != null && preview.module != module)
        {
            Undo.RecordObject(preview, "Preview module");
            preview.module = module;
            EditorUtility.SetDirty(preview);
        }
        preview?.Rebuild();
        if (module != null) Selection.activeObject = module;
        FramePreview();
    }

    /// <summary>Point the Scene view down into the previewed room.</summary>
    public static void FramePreview()
    {
        var preview = Object.FindFirstObjectByType<FrontRoomsModulePreview>();
        if (preview == null || preview.module == null) return;
        var m = preview.module.data.Rotated(preview.rotation);
        FrontRoomsModulePreview.Placement(m, out var x0, out var y0);
        var cs = MapGrid.CellSize;
        var centre = preview.transform.TransformPoint(new Vector3((x0 + m.width * .5f) * cs, 1f, (y0 + m.depth * .5f) * cs));
        var view = SceneView.lastActiveSceneView;
        if (view == null) return;
        view.LookAt(centre, Quaternion.Euler(50f, -25f, 0f), Mathf.Max(m.width, m.depth) * cs * .9f);
        view.Repaint();
    }

    [MenuItem("FrontRooms/Level Designer/New room module", priority = 1)]
    public static void NewModule()
    {
        EnsureFolder();
        var path = AssetDatabase.GenerateUniqueAssetPath(FrontRoomsRoomModule.Folder + "/RoomModule.asset");
        var module = ScriptableObject.CreateInstance<FrontRoomsRoomModule>();
        module.data = new RoomModuleData { width = 3, depth = 3 };
        module.data.Normalize();
        module.data.south[1] = ModuleEdge.Arch;
        AssetDatabase.CreateAsset(module, path);
        AssetDatabase.SaveAssets();
        Open(module);
        EditorGUIUtility.PingObject(module);
    }

    /// <summary>Create the sample modules that are missing. Existing ones (and edits to them) are left alone.</summary>
    [MenuItem("FrontRooms/Level Designer/Create sample modules", priority = 20)]
    public static void CreateSamples()
    {
        EnsureFolder();
        var made = 0;
        foreach (var (name, notes, data) in Samples())
        {
            var path = FrontRoomsRoomModule.Folder + "/" + name + ".asset";
            if (AssetDatabase.LoadAssetAtPath<FrontRoomsRoomModule>(path) != null) continue;
            var module = ScriptableObject.CreateInstance<FrontRoomsRoomModule>();
            module.notes = notes;
            module.data = data;
            AssetDatabase.CreateAsset(module, path);
            made++;
        }
        AssetDatabase.SaveAssets();
        Debug.Log("[FrontRoomsLevelDesigner] " + made + " sample module(s) created in " + FrontRoomsRoomModule.Folder + "; existing ones left as they are.");
    }

    /// <summary>Put the sample modules back as shipped (asks first in the editor; keeps their assets, so links survive).</summary>
    [MenuItem("FrontRooms/Level Designer/Reset sample modules", priority = 21)]
    public static void ResetSamples()
    {
        if (!Application.isBatchMode && !EditorUtility.DisplayDialog("Reset sample modules", "Put the four sample modules back as shipped? Edits to them are lost.", "Reset", "Cancel")) return;
        EnsureFolder();
        foreach (var (name, notes, data) in Samples())
        {
            var path = FrontRoomsRoomModule.Folder + "/" + name + ".asset";
            var module = AssetDatabase.LoadAssetAtPath<FrontRoomsRoomModule>(path);
            if (module == null)
            {
                module = ScriptableObject.CreateInstance<FrontRoomsRoomModule>();
                AssetDatabase.CreateAsset(module, path);
            }
            Undo.RecordObject(module, "Reset sample module");
            module.notes = notes;
            module.data = data;
            EditorUtility.SetDirty(module);
            FrontRoomsRoomModule.NotifyChanged(module);
        }
        AssetDatabase.SaveAssets();
    }

    /// <summary>Batch: the preview scene and the sample modules.</summary>
    public static void SetupBatch()
    {
        CreateSamples();
        EnsureScene();
    }

    public static IEnumerable<FrontRoomsRoomModule> Modules() =>
        AssetDatabase.FindAssets("t:FrontRoomsRoomModule").Select(AssetDatabase.GUIDToAssetPath).OrderBy(p => p, System.StringComparer.Ordinal)
            .Select(AssetDatabase.LoadAssetAtPath<FrontRoomsRoomModule>).Where(m => m != null);

    static void EnsureFolder()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Levels")) AssetDatabase.CreateFolder("Assets", "Levels");
        if (!AssetDatabase.IsValidFolder(FrontRoomsRoomModule.Folder)) AssetDatabase.CreateFolder("Assets/Levels", "Modules");
    }

    /// <summary>Create the preview scene if it is missing: the preview, an eye camera and the post stack.</summary>
    static void EnsureScene()
    {
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) != null) return;
        var active = SceneManager.GetActiveScene();
        var replace = string.IsNullOrEmpty(active.path) && SceneManager.sceneCount == 1 && !active.isDirty;
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, replace ? NewSceneMode.Single : NewSceneMode.Additive);
        var root = new GameObject("Level Designer");
        SceneManager.MoveGameObjectToScene(root, scene);
        var preview = root.AddComponent<FrontRoomsModulePreview>();
        var profile = FrontRoomsLevelProfiles.Resolve();
        preview.profile = AssetDatabase.Contains(profile) ? profile : null;
        preview.module = Modules().FirstOrDefault();
        var eye = new GameObject("Eye (Game view)");
        eye.transform.SetParent(root.transform, false);
        eye.tag = "MainCamera";
        var cam = eye.AddComponent<Camera>();
        cam.fieldOfView = 76f;
        cam.nearClipPlane = .05f;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = FrontRoomsLook.FogColor;
        FrontRoomsPostStack.ConfigureCamera(cam);
        FrontRoomsPostStack.Ensure(root.transform);
        preview.eye = cam;
        EditorSceneManager.SaveScene(scene, ScenePath);
        if (!replace) EditorSceneManager.CloseScene(scene, true);
        Debug.Log("[FrontRoomsLevelDesigner] Created " + ScenePath);
    }

    // ---------- Captures ----------

    /// <summary>Batch: every module, built by the preview, from its entrance and from above.</summary>
    public static void CaptureBatch()
    {
        var folder = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification");
        Directory.CreateDirectory(folder);
        var count = 0;
        foreach (var module in Modules())
        {
            var root = new GameObject("CAPTURE / designer") { hideFlags = HideFlags.DontSave };
            // On a whole world period, so surfaces line up as at the origin (LEVEL_MODULE_SPEC §5).
            root.transform.position = new Vector3(26f * ModuleUnits.WorldPeriod, 0f, 26f * ModuleUnits.WorldPeriod);
            try
            {
                var preview = root.AddComponent<FrontRoomsModulePreview>();
                preview.module = module;
                preview.profile = FrontRoomsLevelProfiles.Resolve();
                var camGo = new GameObject("eye");
                camGo.transform.SetParent(root.transform, false);
                var cam = camGo.AddComponent<Camera>();
                cam.fieldOfView = 76f;
                cam.nearClipPlane = .05f;
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = FrontRoomsLook.FogColor;
                preview.eye = cam;
                preview.Rebuild();
                const int layer = 31;
                foreach (var t in root.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = layer;
                cam.cullingMask = 1 << layer;
                Render(cam, Path.Combine(folder, "designer-" + module.name + "-eye.png"));

                // From just under the ceiling, looking straight down.
                var m = module.data;
                FrontRoomsModulePreview.Placement(m, out var x0, out var y0);
                var cs = MapGrid.CellSize;
                cam.orthographic = true;
                cam.orthographicSize = Mathf.Max(m.depth * cs * .5f, m.width * cs * .5f * 9f / 16f) + 1f;
                cam.nearClipPlane = .01f;
                cam.transform.position = root.transform.TransformPoint(new Vector3((x0 + m.width * .5f) * cs, MapGrid.CeilingHeight(m.height) - .05f, (y0 + m.depth * .5f) * cs));
                cam.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                Render(cam, Path.Combine(folder, "designer-" + module.name + "-plan.png"));
                count++;
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }
        Debug.Log("[FrontRoomsLevelDesigner] Captured " + count + " modules to " + folder);
    }

    static void Render(Camera cam, string path)
    {
        var rt = new RenderTexture(1600, 900, 24) { antiAliasing = 4 };
        var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false);
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0);
        tex.Apply();
        RenderTexture.active = null;
        cam.targetTexture = null;
        File.WriteAllBytes(path, tex.EncodeToPNG());
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(tex);
    }

    // ---------- Samples ----------

    /// <summary>
    /// A prop with its back to a wall, 3 cm off the wall face, its front into
    /// the room, centred on <paramref name="along"/>. Uses the real footprint,
    /// which need not be centred on the pivot.
    /// </summary>
    static ModuleProp Wall(string kit, float along, string side, RoomModuleData m, float y = 0f)
    {
        var f = FrontRoomsMapWorld.KitFootprint(kit) ?? new[] { -.3f, -.3f, .3f, .3f, 1f };
        var gap = ModuleUnits.WallHalf + .03f;
        var cx = (f[0] + f[2]) * .5f; // the footprint's centre across the front, in local X
        switch (side)
        {
            // yaw 0: local -Z (the back) faces south.
            case "south": return new ModuleProp { kit = kit, x = along - cx, z = gap - f[1], y = y, yaw = 0f };
            // yaw 180: local x and z turn round.
            case "north": return new ModuleProp { kit = kit, x = along + cx, z = m.DepthMetres - gap + f[1], y = y, yaw = 180f };
            // yaw 90: local (x, z) -> world (z, -x).
            case "west": return new ModuleProp { kit = kit, x = gap - f[1], z = along + cx, y = y, yaw = 90f };
            // yaw 270: local (x, z) -> world (-z, x).
            default: return new ModuleProp { kit = kit, x = m.WidthMetres - gap + f[1], z = along - cx, y = y, yaw = 270f };
        }
    }

    static IEnumerable<(string, string, RoomModuleData)> Samples()
    {
        // A Level 0 waiting room: a partition with a doorway, a row of chairs against the wall, a clock, one dead lamp.
        var a = new RoomModuleData { width = 4, depth = 3, height = ZoneHeight.Standard, theme = ZoneTheme.Level0, fill = ModuleFill.None, columns = ModuleColumns.None };
        a.Normalize();
        a.south[1] = ModuleEdge.Arch;
        a.north[2] = ModuleEdge.Open;
        a.west[1] = ModuleEdge.Arch;
        a.innerEast[2 + 0 * 3] = ModuleEdge.Wall;
        a.innerEast[2 + 1 * 3] = ModuleEdge.Arch;
        a.innerEast[2 + 2 * 3] = ModuleEdge.Wall;
        a.props = new[]
        {
            Wall("Kit_LadderChair", 1.2f, "north", a), Wall("Kit_LadderChair", 1.8f, "north", a), Wall("Kit_LadderChair", 2.4f, "north", a),
            Wall("Kit_SideTableTurned", 3.2f, "north", a), Wall("Kit_WallClock", 4.5f, "north", a, 2.1f),
            Wall("Kit_Torchiere", 6.6f, "west", a),
        };
        a.lamps[1 + 1 * 4] = ModuleLamp.Dead;
        a.lamps[3 + 2 * 4] = ModuleLamp.Failing;
        yield return ("L0_WaitingRoom_4x3", "Level 0: a waiting room cut in two by a partition with a doorway. Chairs face nobody.", a);

        // An Office bullpen: the Office kit fills round a copier and a water cooler; columns follow the 6 m grid.
        var b = new RoomModuleData { width = 4, depth = 4, height = ZoneHeight.Standard, theme = ZoneTheme.Office, fill = ModuleFill.Office, columns = ModuleColumns.Auto };
        b.Normalize();
        b.south[1] = ModuleEdge.Open; b.south[2] = ModuleEdge.Open;
        b.east[1] = ModuleEdge.Arch;
        b.north[3] = ModuleEdge.Arch;
        b.props = new[] { Wall("Kit_Copier", 2.0f, "west", b), Wall("Kit_WaterCooler", 9.2f, "west", b), Wall("Kit_FilingCabinet", 1.0f, "north", b), Wall("Kit_FilingCabinet", 1.4f, "north", b) };
        b.lamps[0 + 3 * 4] = ModuleLamp.Dim;
        yield return ("Office_Bullpen_4x4", "Level 4: an open-plan office. The Office kit lays out the pods; the copier, cooler and files are fixed.", b);

        // A tall pillar hall: 6 m columns, a furniture pile, most lamps dead.
        var c = new RoomModuleData { width = 6, depth = 5, height = ZoneHeight.Tall, theme = ZoneTheme.Level0, fill = ModuleFill.Pile, columns = ModuleColumns.Auto };
        c.Normalize();
        c.west[0] = ModuleEdge.Open; c.west[4] = ModuleEdge.Arch;
        c.east[2] = ModuleEdge.Open;
        c.north[3] = ModuleEdge.Arch;
        for (var k = 0; k < c.lamps.Length; k += 3) c.lamps[k] = ModuleLamp.Dead;
        c.lamps[2 + 2 * 6] = ModuleLamp.Failing;
        yield return ("Tall_PillarHall_6x5", "Level 0 tall hall: a colonnade on the 6 m grid and a pile of furniture in one bay.", c);

        // A low storage room: one way in, crates and a bookcase, dim and failing lamps.
        var d = new RoomModuleData { width = 2, depth = 3, height = ZoneHeight.Low, theme = ZoneTheme.Level0, fill = ModuleFill.None, columns = ModuleColumns.None };
        d.Normalize();
        d.south[0] = ModuleEdge.Arch;
        d.props = new[]
        {
            Wall("Kit_Bookcase", 7.4f, "east", d), Wall("Kit_PlyCabinet", 5.2f, "east", d),
            new ModuleProp { kit = "Kit_Crate", x = 1.4f, z = 7.6f, yaw = 12f }, new ModuleProp { kit = "Kit_Pallet", x = 1.4f, z = 5.4f, yaw = 0f },
        };
        d.lamps[0 + 0 * 2] = ModuleLamp.Dim;
        d.lamps[1 + 1 * 2] = ModuleLamp.Off;
        d.lamps[0 + 2 * 2] = ModuleLamp.Failing;
        yield return ("Low_Storage_2x3", "Level 0 low room: a dead-end store with one doorway.", d);
    }
}
