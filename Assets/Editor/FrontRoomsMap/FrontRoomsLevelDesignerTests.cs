using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>
/// Headless checks of the Level Designer's P2 tools on a temporary module:
/// -executeMethod FrontRoomsLevelDesignerTests.RunBatch -quit.
/// Palette placement through the window's own calls (a floor kit, a wall
/// unit against each wall and each face of an inner wall, a hung clock, a
/// desk-top item on a desk), the preview's module/world conversions for
/// every turn against the props the map really built 26 world periods out,
/// the Scene view write-back, drop and delete with Undo, the generator
/// toggle with Undo, and the module's own checks. Writes
/// Verification/level-designer-tests.json and throws if anything failed.
/// </summary>
public static class FrontRoomsLevelDesignerTests
{
    const string Folder = "Assets/LevelDesignerTest";
    const float Near = 2e-3f;

    [Serializable]
    sealed class Report
    {
        public string verdict;
        public int passed, failed;
        public List<string> checks = new List<string>();
        public List<string> failures = new List<string>();
    }

    static Report report;

    static void Check(string name, bool ok, string detail = "")
    {
        var line = (ok ? "ok   " : "FAIL ") + name + (string.IsNullOrEmpty(detail) ? "" : " — " + detail);
        report.checks.Add(line);
        if (ok) report.passed++;
        else
        {
            report.failed++;
            report.failures.Add(line);
            Debug.LogError("[LevelDesignerTests] " + line);
        }
    }

    public static void RunBatch()
    {
        report = new Report();
        var profile = FrontRoomsLevelProfiles.Resolve();
        var savedModules = profile.modules?.ToArray();
        float savedChance = profile.generation.moduleChance;
        int savedTier = profile.generation.moduleTier;
        GameObject root = null;
        try
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var module = TempModule();
            var kits = Placement(module);
            var preview = Conversions(module, out root);
            SceneTools(preview, kits);
            Generator(profile, module);
            var errors = new List<string>();
            var warnings = new List<string>();
            module.Validate(errors, warnings);
            Check("module checks: no errors", errors.Count == 0, errors.Count + " error(s), " + warnings.Count + " warning(s): " + string.Join(" | ", errors.Concat(warnings)));
        }
        catch (Exception e)
        {
            Check("no exception", false, e.ToString());
        }
        finally
        {
            if (root != null) Object.DestroyImmediate(root);
            Selection.objects = new Object[0];
            // Leave the level profile as it was, whatever happened above.
            if (EditorUtility.IsPersistent(profile))
            {
                profile.modules = savedModules;
                profile.generation.moduleChance = savedChance;
                profile.generation.moduleTier = savedTier;
            }
            AssetDatabase.DeleteAsset(Folder);
        }

        report.verdict = report.failed == 0 ? "PASS" : "FAIL";
        var folder = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification");
        Directory.CreateDirectory(folder);
        File.WriteAllText(Path.Combine(folder, "level-designer-tests.json"), JsonUtility.ToJson(report, true));
        Debug.Log("[LevelDesignerTests] " + report.verdict + ": " + report.passed + " passed, " + report.failed + " failed\n" + string.Join("\n", report.checks));
        if (report.failed > 0) throw new Exception("[LevelDesignerTests] " + report.failed + " check(s) failed: " + string.Join("; ", report.failures));
    }

    /// <summary>12 x 9 m, a doorway south, open north, and one inner wall between cells (1, 1) and (2, 1), on x = 6 m.</summary>
    static FrontRoomsRoomModule TempModule()
    {
        if (!AssetDatabase.IsValidFolder(Folder)) AssetDatabase.CreateFolder("Assets", Path.GetFileName(Folder));
        var module = ScriptableObject.CreateInstance<FrontRoomsRoomModule>();
        var m = new RoomModuleData { width = 4, depth = 3, height = ZoneHeight.Standard, theme = ZoneTheme.Level0, fill = ModuleFill.None, columns = ModuleColumns.None };
        m.Normalize();
        m.south[1] = ModuleEdge.Arch;
        m.north[2] = ModuleEdge.Open;
        m.innerEast[1 + 1 * (m.width - 1)] = ModuleEdge.Wall;
        module.data = m;
        AssetDatabase.CreateAsset(module, Folder + "/TestModule.asset");
        return module;
    }

    static bool Close(float a, float b, float within = 1e-3f) => Mathf.Abs(a - b) <= within;

    static bool CloseYaw(float a, float b) => Mathf.Abs(Mathf.DeltaAngle(a, b)) < .05f;

    // ---------- Palette placement ----------

    /// <summary>The kits the later steps use: (floor kit, its prop index), (wall unit, the index of the one on the west wall).</summary>
    static (string floor, int floorIndex, string wall, int westIndex) Placement(FrontRoomsRoomModule module)
    {
        var all = FrontRoomsModuleEditing.PaletteKits("All", "");
        var floors = FrontRoomsModuleEditing.PaletteKits("Floor", "");
        var walls = FrontRoomsModuleEditing.PaletteKits("Wall", "");
        var desks = FrontRoomsModuleEditing.PaletteKits("DeskTop", "");
        Check("palette lists kits by placement", floors.Count > 0 && walls.Count > 0 && desks.Count > 0 && floors.Count + walls.Count + desks.Count <= all.Count,
            all.Count + " kits: " + floors.Count + " floor, " + walls.Count + " wall, " + desks.Count + " desk-top");
        Check("palette leaves out sync copies", all.All(n => !n.Contains(" ")));
        Check("palette search", FrontRoomsModuleEditing.PaletteKits("All", "crate").All(n => n.IndexOf("crate", StringComparison.OrdinalIgnoreCase) >= 0));

        var m = module.data;
        var floor = floors.Contains("Kit_Crate") ? "Kit_Crate" : floors[0];
        var floorIndex = FrontRoomsModuleEditing.AddKit(module, floor, new Vector2(3.03f, 4.48f));
        var p = m.props[floorIndex];
        Check("floor kit snaps to 0.05 m where it was put", p.kit == floor && Close(p.x, 3.05f) && Close(p.z, 4.5f) && p.yaw == 0f && p.y == 0f, P(p));

        // A wall unit against each wall, on wall stretches; its back 3 cm off the wall face, its front into the room, centred where it was put.
        var wall = walls.Contains("Kit_FilingCabinet") ? "Kit_FilingCabinet" : walls.First(k => !FrontRoomsKitLibrary.GetInfo(k).TryAnchor("hang", out _));
        var f = FrontRoomsModuleEditing.Footprint(wall);
        var gap = ModuleUnits.WallHalf + FrontRoomsModuleEditing.WallGap;
        float W = m.WidthMetres, D = m.DepthMetres;
        int westIndex = -1;
        void Wall(string name, Vector2 at, float yaw, Func<float, float, float, float, bool> backOnFace, Func<float, float, float, float, float> centreAlong, float along)
        {
            var index = FrontRoomsModuleEditing.AddKit(module, wall, at);
            var q = m.props[index];
            RoomModuleData.Bounds(q, f, out var x0, out var z0, out var x1, out var z1);
            Check("wall unit, " + name + ": back to the wall face, front into the room, centred",
                CloseYaw(q.yaw, yaw) && backOnFace(x0, z0, x1, z1) && Close(centreAlong(x0, z0, x1, z1), along) && q.y == 0f,
                P(q) + " box (" + x0.ToString("0.000") + ", " + z0.ToString("0.000") + ")-(" + x1.ToString("0.000") + ", " + z1.ToString("0.000") + ")");
            if (name == "west wall") westIndex = index;
        }
        Wall("south wall", new Vector2(1.5f, .4f), 0f, (x0, z0, x1, z1) => Close(z0, gap), (x0, z0, x1, z1) => (x0 + x1) * .5f, 1.5f);
        Wall("north wall", new Vector2(10.5f, 8.6f), 180f, (x0, z0, x1, z1) => Close(z1, D - gap), (x0, z0, x1, z1) => (x0 + x1) * .5f, 10.5f);
        Wall("west wall", new Vector2(.4f, 4.5f), 90f, (x0, z0, x1, z1) => Close(x0, gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 4.5f);
        Wall("east wall", new Vector2(W - .4f, 1.5f), 270f, (x0, z0, x1, z1) => Close(x1, W - gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 1.5f);
        Wall("inner wall, east face", new Vector2(6.4f, 4.5f), 90f, (x0, z0, x1, z1) => Close(x0, 6f + gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 4.5f);
        Wall("inner wall, west face", new Vector2(5.6f, 4.5f), 270f, (x0, z0, x1, z1) => Close(x1, 6f - gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 4.5f);
        // Into a corner: kept clear of the side wall.
        Wall("south-west corner", new Vector2(.2f, .2f), 0f, (x0, z0, x1, z1) => Close(z0, gap) && x0 >= gap - 1e-3f, (x0, z0, x1, z1) => x0, gap);

        // The south doorway is not a wall: a unit put there goes to the wall beside it.
        var arch = Add(module, wall, new Vector2(4.5f, .3f));
        Check("wall unit put in a doorway goes to the wall beside it", arch.x <= 3f + 1e-3f || arch.x >= 6f - 1e-3f, P(arch));

        if (FrontRoomsKitLibrary.GetInfo("Kit_WallClock") != null)
        {
            var clock = Add(module, "Kit_WallClock", new Vector2(4.5f, 8.8f));
            Check("hung kit goes up 2.1 m on its wall", CloseYaw(clock.yaw, 180f) && Close(clock.y, 2.1f), P(clock));
        }

        var desk = floors.Contains("Kit_OfficeDesk") ? "Kit_OfficeDesk" : floors.First(k => FrontRoomsKitLibrary.GetInfo(k).TrySupport("top", out _, out _));
        FrontRoomsKitLibrary.GetInfo(desk).TrySupport("top", out var top, out _);
        FrontRoomsModuleEditing.AddKit(module, desk, new Vector2(2f, 6.5f));
        var item = desks.Contains("Kit_Keyboard") ? "Kit_Keyboard" : desks[0];
        var onDesk = Add(module, item, new Vector2(2f, 6.5f));
        Check("desk-top item lands on the desk under it, without a collider", Close(onDesk.y, top.y) && onDesk.noCollider && Close(onDesk.x, 2f) && Close(onDesk.z, 6.5f), P(onDesk) + " desk top " + top.y);
        var onFloor = Add(module, item, new Vector2(8f, 4.5f));
        Check("desk-top item with no desk under it stays on the floor", onFloor.y == 0f && onFloor.noCollider, P(onFloor));
        var outside = Add(module, floor, new Vector2(-2f, 20f));
        Check("a kit put outside the room is kept inside it", Close(outside.x, 0f) && Close(outside.z, D), P(outside));
        FrontRoomsModuleEditing.RemoveProps(module, new[] { m.props.Length - 1 });
        return (floor, floorIndex, wall, westIndex);
    }

    /// <summary>Add a kit as the palette does and return the prop it became (AddKit replaces the props array, so index it afterwards).</summary>
    static ModuleProp Add(FrontRoomsRoomModule module, string kit, Vector2 at)
    {
        var index = FrontRoomsModuleEditing.AddKit(module, kit, at);
        return module.data.props[index];
    }

    static string P(ModuleProp p) => p.kit + " x " + p.x.ToString("0.000") + " z " + p.z.ToString("0.000") + " y " + p.y.ToString("0.00") + " yaw " + p.yaw.ToString("0.0");

    // ---------- Conversions ----------

    /// <summary>A preview 26 world periods out; for each turn, round trips and the built props against ModuleToWorld. Left at one quarter turn.</summary>
    static FrontRoomsModulePreview Conversions(FrontRoomsRoomModule module, out GameObject root)
    {
        root = new GameObject("TEST / level designer") { hideFlags = HideFlags.DontSave };
        root.transform.position = new Vector3(26f * ModuleUnits.WorldPeriod, 0f, 26f * ModuleUnits.WorldPeriod);
        var preview = root.AddComponent<FrontRoomsModulePreview>();
        preview.module = module;
        preview.profile = FrontRoomsLevelProfiles.Resolve();
        var m = module.data;
        var points = new[] { Vector2.zero, new Vector2(m.WidthMetres, 0f), new Vector2(m.WidthMetres, m.DepthMetres), new Vector2(0f, m.DepthMetres), new Vector2(1.3f, 2.7f), new Vector2(7.45f, 8.05f) };
        for (var turn = 0; turn < 4; turn++)
        {
            preview.rotation = turn;
            preview.Rebuild();
            Check("turn " + turn + ": preview built", preview.World != null);

            var worst = points.Max(q => (preview.WorldToModule(preview.ModuleToWorld(q)) - q).magnitude);
            Check("turn " + turn + ": module -> world -> module round trip", worst < 1e-3f, "worst " + worst.ToString("0.00000") + " m");
            var yaws = new[] { 0f, 37f, 90f, 180f, 271.5f };
            Check("turn " + turn + ": yaw round trip", yaws.All(y => CloseYaw(preview.WorldToModuleYaw(preview.ModuleToWorldRotation(y)), y)));

            // The footprint lands on the cells the stamp gave the turned module.
            var turned = m.Rotated(turn);
            FrontRoomsModulePreview.Placement(turned, out var cx, out var cy);
            var local = points.Take(4).Select(q => preview.transform.InverseTransformPoint(preview.ModuleToWorld(q))).ToArray();
            var cs = MapGrid.CellSize;
            Check("turn " + turn + ": footprint on the stamped cells",
                Close(local.Min(v => v.x), cx * cs) && Close(local.Min(v => v.z), cy * cs) && Close(local.Max(v => v.x), (cx + turned.width) * cs) && Close(local.Max(v => v.z), (cy + turned.depth) * cs),
                "cells (" + cx + ", " + cy + ") " + turned.width + " x " + turned.depth);

            // Every prop the map built, against where the conversions put it.
            var tags = preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true);
            var bad = new List<string>();
            foreach (var tag in tags)
            {
                var p = m.props[tag.index];
                var at = preview.WorldToModule(tag.transform.position);
                if ((tag.transform.position - preview.ModuleToWorld(new Vector2(p.x, p.z), p.y)).magnitude > Near
                    || Quaternion.Angle(tag.transform.rotation, preview.ModuleToWorldRotation(p.yaw)) > .05f
                    || !CloseYaw(preview.WorldToModuleYaw(tag.transform.rotation), p.yaw)
                    || (at - new Vector2(p.x, p.z)).magnitude > Near)
                    bad.Add(tag.index + " " + p.kit);
            }
            Check("turn " + turn + ": built props tagged and where the conversions say", tags.Length > 0 && bad.Count == 0,
                tags.Length + " of " + m.props.Length + " props built" + (bad.Count > 0 ? "; off: " + string.Join(", ", bad) : ""));
        }
        preview.rotation = 1;
        preview.Rebuild();
        return preview;
    }

    static FrontRoomsModulePropTag Tag(FrontRoomsModulePreview preview, int index) =>
        preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true).FirstOrDefault(t => t.index == index);

    /// <summary>
    /// Move a prop as the Move and Rotate tools do, recorded for Undo; the
    /// flush is where Unity calls Undo.postprocessModifications (after every
    /// drag step), then the tools' write-back runs as on the next editor update.
    /// </summary>
    static void MoveInScene(FrontRoomsModulePropTag tag, Vector3 position, Quaternion rotation)
    {
        Undo.RecordObject(tag.transform, "Move");
        tag.transform.SetPositionAndRotation(position, rotation);
        Undo.FlushUndoRecordObjects();
        FrontRoomsDesignerSceneTools.Sync();
    }

    // ---------- Scene view tools ----------

    static void SceneTools(FrontRoomsModulePreview preview, (string floor, int floorIndex, string wall, int westIndex) kits)
    {
        var module = preview.module;
        var m = module.data;

        // Move and turn a prop as the Move and Rotate tools do, then write it back.
        var tag = Tag(preview, kits.floorIndex);
        Check("write-back: the floor prop was built", tag != null);
        if (tag == null) return;
        Selection.activeGameObject = tag.gameObject;
        var before = m.props[kits.floorIndex];
        var world = preview.World;
        Undo.IncrementCurrentGroup();
        MoveInScene(tag, preview.ModuleToWorld(new Vector2(before.x + .52f, before.z - .31f), before.y), Quaternion.Euler(0f, 90f, 0f) * tag.transform.rotation);
        var after = m.props[kits.floorIndex];
        Check("write-back: x and z (0.05 m) and yaw follow the Scene, height and kit stay",
            Close(after.x, FrontRoomsModuleEditing.Snap(before.x + .52f)) && Close(after.z, FrontRoomsModuleEditing.Snap(before.z - .31f))
            && CloseYaw(after.yaw, before.yaw + 90f) && after.y == before.y && after.kit == before.kit, P(before) + " -> " + P(after));
        Check("write-back: no rebuild while the prop is moving (the dragged object lives on)", preview.World == world && tag != null && FrontRoomsDesignerSceneTools.RebuildPending);
        MoveInScene(tag, tag.transform.position, tag.transform.rotation);
        Check("write-back: a prop that has not moved again leaves the module alone", m.props[kits.floorIndex].Equals(after));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("write-back: one Undo puts the module prop and the object back", m.props[kits.floorIndex].Equals(before)
            && (tag.transform.position - preview.ModuleToWorld(new Vector2(before.x, before.z), before.y)).magnitude < Near, P(m.props[kits.floorIndex]));

        // Moved along one axis only: the other keeps its exact value (a wall unit's gap is not on the 0.05 m grid).
        var wallTag = Tag(preview, kits.westIndex);
        if (wallTag != null)
        {
            var w0 = m.props[kits.westIndex];
            Undo.IncrementCurrentGroup();
            MoveInScene(wallTag, preview.ModuleToWorld(new Vector2(w0.x, w0.z + .4f), w0.y), wallTag.transform.rotation);
            var w1 = m.props[kits.westIndex];
            Check("write-back: moved along the wall, the distance from the wall is kept exactly", w1.x == w0.x && Close(w1.z, FrontRoomsModuleEditing.Snap(w0.z + .4f)) && w1.yaw == w0.yaw, P(w0) + " -> " + P(w1));
            Undo.FlushUndoRecordObjects();
            Undo.PerformUndo();
            Check("write-back: Undo after a move along the wall", m.props[kits.westIndex].Equals(w0));
        }
        else Check("write-back: the west wall unit was built", false);

        // The move ends: the preview rebuilds, the prop stands at its new place and is selected again.
        preview.Rebuild();
        tag = Tag(preview, kits.floorIndex);
        Selection.activeGameObject = tag.gameObject;
        Undo.IncrementCurrentGroup();
        MoveInScene(tag, preview.ModuleToWorld(new Vector2(before.x + 1f, before.z), before.y), tag.transform.rotation);
        FrontRoomsDesignerSceneTools.Commit(preview);
        var rebuilt = Tag(preview, kits.floorIndex);
        var selected = Selection.activeGameObject != null ? Selection.activeGameObject.GetComponent<FrontRoomsModulePropTag>() : null;
        Check("commit: rebuilt prop at its new place, selected again", rebuilt != null && rebuilt != tag
            && (rebuilt.transform.position - preview.ModuleToWorld(new Vector2(before.x + 1f, before.z), before.y)).magnitude < Near
            && selected == rebuilt && !FrontRoomsDesignerSceneTools.RebuildPending, selected != null ? "selected index " + selected.index : "nothing selected");
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("commit: Undo puts the module prop back", m.props[kits.floorIndex].Equals(before), P(m.props[kits.floorIndex]));
        preview.Rebuild();

        // A kit dropped on the floor in the Scene view: a ray from above a module point.
        var count = m.props.Length;
        var target = new Vector2(8.03f, 2.02f);
        var ray = new Ray(preview.ModuleToWorld(target) + Vector3.up * 10f, Vector3.down);
        var hit = FrontRoomsDesignerSceneTools.FloorPoint(preview, ray, out var at);
        Check("drop: the ray meets the floor at the module point", hit && (at - target).magnitude < Near, at.ToString("0.000"));
        Check("drop: a ray far outside the room is refused", !FrontRoomsDesignerSceneTools.FloorPoint(preview, new Ray(preview.ModuleToWorld(new Vector2(-5f, -5f)) + Vector3.up * 10f, Vector3.down), out _));
        Undo.IncrementCurrentGroup();
        var index = FrontRoomsDesignerSceneTools.Drop(preview, kits.floor, at);
        preview.Rebuild();
        var dropped = m.props.Length == count + 1 ? m.props[index] : default;
        selected = Selection.activeGameObject != null ? Selection.activeGameObject.GetComponent<FrontRoomsModulePropTag>() : null;
        Check("drop: the kit is added at the point (0.05 m) and selected after the rebuild", dropped.kit == kits.floor && Close(dropped.x, 8.05f) && Close(dropped.z, 2f)
            && selected != null && selected.index == index, P(dropped));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("drop: Undo takes it away", m.props.Length == count);

        // Delete in the Scene view removes the prop from the module.
        preview.Rebuild();
        tag = Tag(preview, kits.westIndex);
        Selection.activeGameObject = tag.gameObject;
        var kept = m.props.ToArray();
        Undo.IncrementCurrentGroup();
        var removed = FrontRoomsDesignerSceneTools.RemoveSelected(preview);
        Check("delete: the selected prop leaves the module", removed && m.props.Length == kept.Length - 1 && Selection.objects.Length == 0
            && m.props.SequenceEqual(kept.Where((p, k) => k != kits.westIndex)));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("delete: Undo brings it back", m.props.SequenceEqual(kept));
        preview.Rebuild();
    }

    // ---------- Generator ----------

    static void Generator(FrontRoomsLevelProfile profile, FrontRoomsRoomModule module)
    {
        if (!EditorUtility.IsPersistent(profile))
        {
            Check("generator: the project has a level profile asset", false);
            return;
        }
        var before = (profile.modules ?? new FrontRoomsRoomModule[0]).ToArray();
        Undo.IncrementCurrentGroup();
        FrontRoomsLevelDesigner.SetUsedByGenerator(profile, module, true);
        Check("generator: the toggle adds the module to the profile", profile.modules.Contains(module) && profile.modules.Length == before.Length + 1 && EditorUtility.IsDirty(profile));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("generator: Undo takes it out again", !profile.modules.Contains(module) && profile.modules.SequenceEqual(before));

        // Two clicks: each is its own undo step.
        Undo.IncrementCurrentGroup();
        FrontRoomsLevelDesigner.SetUsedByGenerator(profile, module, true);
        Undo.FlushUndoRecordObjects();
        Undo.IncrementCurrentGroup();
        FrontRoomsLevelDesigner.SetUsedByGenerator(profile, module, false);
        Check("generator: the toggle off removes it", !profile.modules.Contains(module) && profile.modules.SequenceEqual(before));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("generator: Undo of the toggle off puts it back", profile.modules.Contains(module));
        Undo.PerformUndo();
        Check("generator: and Undo again leaves the profile as it was", profile.modules.SequenceEqual(before));

        var chance = profile.generation.moduleChance;
        var tier = profile.generation.moduleTier;
        Undo.IncrementCurrentGroup();
        FrontRoomsLevelDesigner.SetModuleGeneration(profile, .77f, tier + 2);
        Check("generator: module chance and tier are set on the profile", Close(profile.generation.moduleChance, .77f) && profile.generation.moduleTier == tier + 2);
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("generator: Undo restores chance and tier", profile.generation.moduleChance == chance && profile.generation.moduleTier == tier);
    }
}
