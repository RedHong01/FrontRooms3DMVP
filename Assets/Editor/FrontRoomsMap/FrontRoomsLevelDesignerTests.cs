using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using FrontRooms.Map;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

/// <summary>
/// Headless checks of the Level Designer's P2 tools on a temporary module:
/// -executeMethod FrontRoomsLevelDesignerTests.RunBatch -quit.
/// Palette placement through the window's own calls (a floor kit, a wall
/// unit against each wall, each face of an inner wall and beside a doorway,
/// a hung clock, desk-top items on a turned desk), the preview's
/// module/world conversions for every turn against the props the map really
/// built 26 world periods out, the Scene view write-back (through Unity's
/// own Undo callback, with the rebuild held back while a handle is held or
/// a field typed in), drop, duplicate and delete with Undo, the plan
/// selection following its prop, the generator toggle with Undo and how
/// often the generator's rooms fit a module, and the module's own checks.
/// Gameplay markers (P4): the conversions against RoomModuleData.Rotated for
/// every turn, the checks' errors and warnings for markers (in a wall, an
/// inner wall, a prop, a column, shut in; a key on a prop top passes), the
/// edits with Undo and the plan's marker selection, the window letting go of
/// the old module's selection when it switches, the sample modules (code and
/// assets) with no errors or warnings, the preview's live rebuild (the one
/// Play uses) run in edit mode, and the run tiers a module comes at.
/// Writes Verification/level-designer-tests.json and throws if anything failed.
/// The Scene view's own events (DragPerform, the Delete and Duplicate
/// commands, handles) need a Scene view and are not run here.
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

    /// <summary>What Placement made that the later steps use.</summary>
    sealed class Made
    {
        public string floor, wall, desk, item;
        public int floorIndex, westIndex, archIndex, deskIndex;
    }

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
        // A new scene unloads assets nothing references: the profile is loaded after it.
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var profile = FrontRoomsLevelProfiles.Resolve();
        var profileWasDirty = EditorUtility.IsDirty(profile);
        var savedModules = profile.modules?.ToArray();
        float savedChance = profile.generation.moduleChance;
        int savedTier = profile.generation.moduleTier;
        GameObject root = null;
        try
        {
            var module = TempModule();
            var made = Placement(module);
            var preview = Conversions(module, out root);
            SceneTools(preview, made);
            MarkerConversions(preview);
            MarkerChecks();
            MarkerEdits(module, made);
            Samples();
            PanelSwitch(module);
            FieldTyping(module);
            LiveRebuild(preview, made);
            Generator(profile, module);
            var errors = new List<string>();
            var warnings = new List<string>();
            module.Validate(errors, warnings);
            Check("module checks: no errors or warnings", errors.Count == 0 && warnings.Count == 0, errors.Count + " error(s), " + warnings.Count + " warning(s): " + string.Join(" | ", errors.Concat(warnings)));
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
                // As it was, so the editor does not write it out again on quit.
                if (!profileWasDirty) EditorUtility.ClearDirty(profile);
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

    static Made Placement(FrontRoomsRoomModule module)
    {
        var made = new Made();
        var all = FrontRoomsModuleEditing.PaletteKits("All", "");
        var floors = FrontRoomsModuleEditing.PaletteKits("Floor", "");
        var walls = FrontRoomsModuleEditing.PaletteKits("Wall", "");
        var desks = FrontRoomsModuleEditing.PaletteKits("DeskTop", "");
        Check("palette lists kits by placement", floors.Count > 0 && walls.Count > 0 && desks.Count > 0 && floors.Count + walls.Count + desks.Count <= all.Count,
            all.Count + " kits: " + floors.Count + " floor, " + walls.Count + " wall, " + desks.Count + " desk-top");
        var crates = FrontRoomsModuleEditing.PaletteKits("All", "crate");
        Check("palette search (any case)", crates.Contains("Kit_Crate") && crates.All(n => n.IndexOf("crate", StringComparison.OrdinalIgnoreCase) >= 0), string.Join(", ", crates));

        var m = module.data;
        made.floor = floors.Contains("Kit_Crate") ? "Kit_Crate" : floors[0];
        made.floorIndex = FrontRoomsModuleEditing.AddKit(module, made.floor, new Vector2(3.03f, 4.48f));
        var p = m.props[made.floorIndex];
        Check("floor kit snaps to 0.05 m where it was put", p.kit == made.floor && Close(p.x, 3.05f) && Close(p.z, 4.5f) && p.yaw == 0f && p.y == 0f, P(p));

        // A wall unit against each wall, on wall stretches; its back 3 cm off the wall face, its front into the room, centred where it was put.
        made.wall = walls.Contains("Kit_FilingCabinet") ? "Kit_FilingCabinet" : walls.First(k => !FrontRoomsKitLibrary.GetInfo(k).TryAnchor("hang", out _));
        var f = FrontRoomsModuleEditing.Footprint(made.wall);
        var gap = ModuleUnits.WallHalf + FrontRoomsModuleEditing.WallGap;
        float W = m.WidthMetres, D = m.DepthMetres;
        int Wall(string name, Vector2 at, float yaw, Func<float, float, float, float, bool> backOnFace, Func<float, float, float, float, float> centreAlong, float along)
        {
            var index = FrontRoomsModuleEditing.AddKit(module, made.wall, at);
            var q = m.props[index];
            RoomModuleData.Bounds(q, f, out var x0, out var z0, out var x1, out var z1);
            Check("wall unit, " + name + ": back to the wall face, front into the room, " + (along < 0f ? "clear of the doorway" : "centred"),
                CloseYaw(q.yaw, yaw) && backOnFace(x0, z0, x1, z1) && (along < 0f || Close(centreAlong(x0, z0, x1, z1), along)) && q.y == 0f,
                P(q) + " box (" + x0.ToString("0.000") + ", " + z0.ToString("0.000") + ")-(" + x1.ToString("0.000") + ", " + z1.ToString("0.000") + ")");
            return index;
        }
        Wall("south wall", new Vector2(1.5f, .4f), 0f, (x0, z0, x1, z1) => Close(z0, gap), (x0, z0, x1, z1) => (x0 + x1) * .5f, 1.5f);
        Wall("north wall", new Vector2(10.5f, 8.6f), 180f, (x0, z0, x1, z1) => Close(z1, D - gap), (x0, z0, x1, z1) => (x0 + x1) * .5f, 10.5f);
        made.westIndex = Wall("west wall", new Vector2(.4f, 4.5f), 90f, (x0, z0, x1, z1) => Close(x0, gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 4.5f);
        Wall("east wall", new Vector2(W - .4f, 1.5f), 270f, (x0, z0, x1, z1) => Close(x1, W - gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 1.5f);
        Wall("inner wall, east face", new Vector2(6.4f, 4.5f), 90f, (x0, z0, x1, z1) => Close(x0, 6f + gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 4.5f);
        Wall("inner wall, west face", new Vector2(5.6f, 4.5f), 270f, (x0, z0, x1, z1) => Close(x1, 6f - gap), (x0, z0, x1, z1) => (z0 + z1) * .5f, 4.5f);
        // Into a corner: kept clear of the side wall.
        Wall("south-west corner", new Vector2(.2f, .2f), 0f, (x0, z0, x1, z1) => Close(z0, gap) && x0 >= gap - 1e-3f, (x0, z0, x1, z1) => x0, gap);
        // The south doorway (x 3 to 6) is not a wall: a unit put there goes to the wall beside it, its whole box off the doorway.
        made.archIndex = Wall("beside the south doorway", new Vector2(4.5f, .3f), 0f, (x0, z0, x1, z1) => Close(z0, gap) && (x1 <= 3f + 1e-3f || x0 >= 6f - 1e-3f), null, -1f);

        if (FrontRoomsKitLibrary.GetInfo("Kit_WallClock") != null)
        {
            var clock = Add(module, "Kit_WallClock", new Vector2(4.5f, 8.8f));
            Check("hung kit goes up 2.1 m on its wall", CloseYaw(clock.yaw, 180f) && Close(clock.y, 2.1f), P(clock));
        }

        // Desk-top items on a desk turned a quarter, then 45° (a wrong rotation sign shows only off the quarter turns).
        made.desk = floors.Contains("Kit_OfficeDesk") ? "Kit_OfficeDesk" : floors.First(k => FrontRoomsKitLibrary.GetInfo(k).TrySupport("top", out _, out _));
        FrontRoomsKitLibrary.GetInfo(made.desk).TrySupport("top", out var top, out _);
        made.deskIndex = FrontRoomsModuleEditing.AddKit(module, made.desk, new Vector2(2f, 6.5f));
        FrontRoomsModuleEditing.TurnProp(module, made.deskIndex);
        var desk = m.props[made.deskIndex];
        made.item = desks.Contains("Kit_Keyboard") ? "Kit_Keyboard" : desks[0];
        // Desk-local (0.6, 0) at yaw 90 is module (2, 5.9).
        var onDesk = Add(module, made.item, new Vector2(2f, 5.9f));
        Check("desk-top item lands on the turned desk under it, turned with it, without a collider",
            Close(onDesk.y, desk.y + top.y) && CloseYaw(onDesk.yaw, desk.yaw) && onDesk.noCollider && Close(onDesk.x, 2f) && Close(onDesk.z, 5.9f), P(onDesk) + " desk " + P(desk));
        var count = m.props.Length;
        var offEnd = Add(module, made.item, new Vector2(2.6f, 6.5f));
        Check("a point the unturned desk would cover, past the turned top, is the floor", offEnd.y == 0f, P(offEnd));
        desk.yaw = 45f;
        m.props[made.deskIndex] = desk;
        // Desk-local (0.566, 0) at 45°; a wrong sign would read (0, -0.566), off the 0.74 m depth.
        var onSlant = Add(module, made.item, new Vector2(2.4f, 6.1f));
        Check("desk-top item on a desk at 45° (rotation sign)", Close(onSlant.y, desk.y + top.y) && CloseYaw(onSlant.yaw, 45f), P(onSlant));
        desk.yaw = 90f;
        m.props[made.deskIndex] = desk;
        FrontRoomsModuleEditing.RemoveProps(module, Enumerable.Range(count, m.props.Length - count));

        var onFloor = Add(module, made.item, new Vector2(8f, 4.5f));
        Check("desk-top item with no desk under it stays on the floor", onFloor.y == 0f && onFloor.noCollider, P(onFloor));
        var outside = Add(module, made.floor, new Vector2(-2f, 20f));
        Check("a kit put outside the room is kept inside it", Close(outside.x, 0f) && Close(outside.z, D), P(outside));
        FrontRoomsModuleEditing.RemoveProps(module, new[] { m.props.Length - 1 });
        return made;
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

            // Every prop the stamp built, against where the conversions put it.
            var tags = preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true);
            Check("turn " + turn + ": every tagged prop is the previewed module's (the generator's own modules stay out of the preview)", tags.All(t => t.module == preview.Stamped), tags.Length + " tagged");
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
            Check("turn " + turn + ": every prop built, tagged and where the conversions say", tags.Length == m.props.Length && bad.Count == 0,
                tags.Length + " of " + m.props.Length + " props built" + (bad.Count > 0 ? "; off: " + string.Join(", ", bad) : ""));
        }
        preview.rotation = 1;
        preview.Rebuild();
        return preview;
    }

    static FrontRoomsModulePropTag Tag(FrontRoomsModulePreview preview, int index) =>
        preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true).FirstOrDefault(t => t.index == index && t.module == preview.Stamped);

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

    static FrontRoomsModulePropTag SelectedTag() => Selection.activeGameObject != null ? Selection.activeGameObject.GetComponent<FrontRoomsModulePropTag>() : null;

    static void SceneTools(FrontRoomsModulePreview preview, Made made)
    {
        var module = preview.module;
        var m = module.data;
        Check("the wall unit beside the doorway is built (the map leaves out props on an opening's strip)", Tag(preview, made.archIndex) != null);

        // Move and turn a prop as the Move and Rotate tools do, then write it back.
        var tag = Tag(preview, made.floorIndex);
        Check("write-back: the floor prop was built", tag != null);
        if (tag == null) return;
        Check("the preview's props are DontSave", (tag.gameObject.hideFlags & HideFlags.DontSave) == HideFlags.DontSave);
        Selection.activeGameObject = tag.gameObject;
        var before = m.props[made.floorIndex];
        var world = preview.World;
        var changes = 0;
        var seen = 0;
        Action<FrontRoomsRoomModule> onChanged = c => { if (c == module) changes++; };
        UndoPropertyModification[] Seen(UndoPropertyModification[] mods)
        {
            seen += mods.Count(q => q.currentValue?.target == tag.transform);
            return mods;
        }
        FrontRoomsRoomModule.Changed += onChanged;
        Undo.postprocessModifications += Seen;
        Undo.IncrementCurrentGroup();
        try { MoveInScene(tag, preview.ModuleToWorld(new Vector2(before.x + .52f, before.z - .31f), before.y), Quaternion.Euler(0f, 90f, 0f) * tag.transform.rotation); }
        finally
        {
            FrontRoomsRoomModule.Changed -= onChanged;
            Undo.postprocessModifications -= Seen;
        }
        Check("Unity reports the move of a DontSave prop through Undo.postprocessModifications", seen > 0, seen + " modification(s)");
        var after = m.props[made.floorIndex];
        Check("write-back: x and z (0.05 m) and yaw follow the Scene, height and kit stay",
            Close(after.x, FrontRoomsModuleEditing.Snap(before.x + .52f)) && Close(after.z, FrontRoomsModuleEditing.Snap(before.z - .31f))
            && CloseYaw(after.yaw, before.yaw + 90f) && after.y == before.y && after.kit == before.kit, P(before) + " -> " + P(after));
        Check("write-back: no rebuild while the prop is moving, none queued (the dragged object lives on)",
            preview.World == world && tag != null && changes == 0 && !preview.RebuildQueued && FrontRoomsDesignerSceneTools.RebuildPending, changes + " Changed event(s)");
        // The prop now stands about 2 cm off its snapped place: a nudge under the thresholds re-snaps to the same values.
        MoveInScene(tag, tag.transform.position + new Vector3(.002f, 0f, -.002f), Quaternion.Euler(0f, .03f, 0f) * tag.transform.rotation);
        Check("write-back: a prop nudged under the thresholds leaves the module alone", m.props[made.floorIndex].Equals(after), P(m.props[made.floorIndex]));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("write-back: one Undo puts the module prop and the object back", m.props[made.floorIndex].Equals(before)
            && (tag.transform.position - preview.ModuleToWorld(new Vector2(before.x, before.z), before.y)).magnitude < Near, P(m.props[made.floorIndex]));
        FrontRoomsDesignerSceneTools.Sync();

        // Why the write waits for the next update: an Undo record made inside the callback is lost.
        var notes = module.notes;
        UndoPropertyModification[] Inside(UndoPropertyModification[] mods)
        {
            Undo.RecordObject(module, "Inside the callback");
            module.notes = "written inside the callback";
            return mods;
        }
        Undo.postprocessModifications += Inside;
        Undo.IncrementCurrentGroup();
        try
        {
            Undo.RecordObject(tag.transform, "Move");
            tag.transform.position += Vector3.right * .1f;
            Undo.FlushUndoRecordObjects();
        }
        finally { Undo.postprocessModifications -= Inside; }
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("an Undo record made inside postprocessModifications is lost (so the write-back waits for the next update)", module.notes == "written inside the callback");
        module.notes = notes;
        FrontRoomsDesignerSceneTools.Sync();

        // Moved along one axis only: the other keeps its exact value (a wall unit's gap is not on the 0.05 m grid).
        var wallTag = Tag(preview, made.westIndex);
        if (wallTag != null)
        {
            var w0 = m.props[made.westIndex];
            Undo.IncrementCurrentGroup();
            MoveInScene(wallTag, preview.ModuleToWorld(new Vector2(w0.x, w0.z + .4f), w0.y), wallTag.transform.rotation);
            var w1 = m.props[made.westIndex];
            Check("write-back: moved along the wall, the distance from the wall is kept exactly", w1.x == w0.x && Close(w1.z, FrontRoomsModuleEditing.Snap(w0.z + .4f)) && w1.yaw == w0.yaw, P(w0) + " -> " + P(w1));
            MoveInScene(wallTag, wallTag.transform.position + preview.ModuleToWorld(new Vector2(w1.x + .002f, w1.z), w1.y) - preview.ModuleToWorld(new Vector2(w1.x, w1.z), w1.y), wallTag.transform.rotation);
            Check("write-back: a 2 mm nudge (under MovedMetres) keeps the off-grid wall distance", m.props[made.westIndex].Equals(w1), P(m.props[made.westIndex]));
            Undo.FlushUndoRecordObjects();
            Undo.PerformUndo();
            Check("write-back: Undo after a move along the wall", m.props[made.westIndex].Equals(w0));
        }
        else Check("write-back: the west wall unit was built", false);

        // The move ends: the editor update rebuilds only after 0.3 s, with no handle held and no field typed in;
        // then the prop stands at its new place and is selected again.
        preview.Rebuild();
        tag = Tag(preview, made.floorIndex);
        Selection.activeGameObject = tag.gameObject;
        Undo.IncrementCurrentGroup();
        MoveInScene(tag, preview.ModuleToWorld(new Vector2(before.x + 1f, before.z), before.y), tag.transform.rotation);
        var update = typeof(FrontRoomsDesignerSceneTools).GetMethod("Update", BindingFlags.NonPublic | BindingFlags.Static);
        update.Invoke(null, null);
        Check("commit: not before the prop has been still 0.3 s", FrontRoomsDesignerSceneTools.RebuildPending && Tag(preview, made.floorIndex) == tag);
        Thread.Sleep(350);
        GUIUtility.hotControl = 1;
        try { update.Invoke(null, null); }
        finally { GUIUtility.hotControl = 0; }
        Check("commit: held back while a handle is held", FrontRoomsDesignerSceneTools.RebuildPending && Tag(preview, made.floorIndex) == tag);
        EditorGUIUtility.editingTextField = true;
        try { update.Invoke(null, null); }
        finally { EditorGUIUtility.editingTextField = false; }
        Check("commit: held back while a field is typed in", FrontRoomsDesignerSceneTools.RebuildPending && Tag(preview, made.floorIndex) == tag);
        update.Invoke(null, null);
        var rebuilt = Tag(preview, made.floorIndex);
        var selected = SelectedTag();
        Check("commit: rebuilt prop at its new place, selected again", rebuilt != null && rebuilt != tag
            && (rebuilt.transform.position - preview.ModuleToWorld(new Vector2(before.x + 1f, before.z), before.y)).magnitude < Near
            && selected == rebuilt && !FrontRoomsDesignerSceneTools.RebuildPending, selected != null ? "selected index " + selected.index : "nothing selected");
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("commit: Undo puts the module prop back", m.props[made.floorIndex].Equals(before), P(m.props[made.floorIndex]));
        preview.Rebuild();

        // A prop the map leaves out (a crate on the south doorway's strip): picking it in the plan must not stop later selections.
        var unbuilt = FrontRoomsModuleEditing.AddKit(module, made.floor, new Vector2(4.5f, .6f));
        preview.Rebuild();
        Check("a prop on an opening's strip is left out of the build", Tag(preview, unbuilt) == null);
        FrontRoomsDesignerSceneTools.SelectProps(preview, new[] { unbuilt });
        tag = Tag(preview, made.floorIndex);
        Selection.activeGameObject = tag.gameObject;
        Undo.IncrementCurrentGroup();
        MoveInScene(tag, preview.ModuleToWorld(new Vector2(before.x + 1f, before.z), before.y), tag.transform.rotation);
        FrontRoomsDesignerSceneTools.Commit(preview);
        selected = SelectedTag();
        Check("after an unbuilt prop was picked, a moved prop is still selected again after the rebuild", selected != null && selected.index == made.floorIndex, selected != null ? "selected index " + selected.index : "nothing selected");
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        FrontRoomsModuleEditing.RemoveProps(module, new[] { unbuilt });
        preview.Rebuild();

        // A kit dropped on the floor in the Scene view: a ray from above a module point.
        var count = m.props.Length;
        var target = new Vector2(8.03f, 2.02f);
        var ray = new Ray(preview.ModuleToWorld(target) + Vector3.up * 10f, Vector3.down);
        var hit = FrontRoomsDesignerSceneTools.FloorPoint(preview, ray, made.floor, out var at);
        Check("drop: the ray meets the floor at the module point", hit && (at - target).magnitude < Near, at.ToString("0.000"));
        Check("drop: a ray far outside the room is refused", !FrontRoomsDesignerSceneTools.FloorPoint(preview, new Ray(preview.ModuleToWorld(new Vector2(-5f, -5f)) + Vector3.up * 10f, Vector3.down), made.floor, out _));
        Undo.IncrementCurrentGroup();
        var index = FrontRoomsDesignerSceneTools.Drop(preview, made.floor, at);
        preview.Rebuild();
        var dropped = m.props.Length == count + 1 ? m.props[index] : default;
        selected = SelectedTag();
        Check("drop: the kit is added at the point (0.05 m) and selected after the rebuild", dropped.kit == made.floor && Close(dropped.x, 8.05f) && Close(dropped.z, 2f)
            && selected != null && selected.index == index, P(dropped));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("drop: Undo takes it away", m.props.Length == count);

        // A desk-top kit aimed at the desk top from a slant (the Scene view's 50° pitch): it lands on the desk, not on the floor behind it.
        var deskProp = m.props[made.deskIndex];
        var deskTop = FrontRoomsModuleEditing.TopHeight(deskProp) ?? 0f;
        var aim = preview.ModuleToWorld(new Vector2(deskProp.x, deskProp.z), deskTop);
        var slant = Quaternion.Euler(50f, 30f, 0f) * Vector3.forward;
        var slanted = new Ray(aim - slant * 10f, slant);
        FrontRoomsDesignerSceneTools.FloorPoint(preview, slanted, made.item, out var onTop);
        FrontRoomsDesignerSceneTools.FloorPoint(preview, slanted, made.floor, out var onFloor);
        var landed = FrontRoomsModuleEditing.NewProp(m, made.item, onTop);
        Check("drop at a slant: a desk-top kit lands on the desk top the mouse is on", (onTop - new Vector2(deskProp.x, deskProp.z)).magnitude < Near && Close(landed.y, deskTop),
            "aimed at (" + deskProp.x + ", " + deskProp.z + "), lands (" + onTop.x.ToString("0.000") + ", " + onTop.y.ToString("0.000") + ") y " + landed.y + "; a floor kit lands " + (onFloor - onTop).magnitude.ToString("0.00") + " m further");

        // Duplicate in the Scene view adds a copy to the module, selected after the rebuild.
        preview.Rebuild();
        tag = Tag(preview, made.floorIndex);
        Selection.activeGameObject = tag.gameObject;
        count = m.props.Length;
        Undo.IncrementCurrentGroup();
        var duplicated = FrontRoomsDesignerSceneTools.DuplicateSelected(preview);
        preview.Rebuild();
        var copy = m.props.Last();
        selected = SelectedTag();
        Check("duplicate: a copy joins the module half a metre east and is selected", duplicated && m.props.Length == count + 1 && copy.kit == before.kit
            && Close(copy.x, before.x + .5f) && Close(copy.z, before.z) && selected != null && selected.index == count, P(copy));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("duplicate: Undo takes the copy away", m.props.Length == count);

        // Delete in the Scene view removes the prop from the module; the window's plan keeps to its own prop.
        preview.Rebuild();
        var plan = new FrontRoomsModulePlanView(() => { });
        var watched = made.westIndex + 1;
        var watchedProp = m.props[watched];
        plan.Select(watched, false);
        plan.Follow(m);
        tag = Tag(preview, made.westIndex);
        Selection.activeGameObject = tag.gameObject;
        var kept = m.props.ToArray();
        Undo.IncrementCurrentGroup();
        var removed = FrontRoomsDesignerSceneTools.RemoveSelected(preview);
        Check("delete: the selected prop leaves the module", removed && m.props.Length == kept.Length - 1 && Selection.objects.Length == 0
            && m.props.SequenceEqual(kept.Where((p, k) => k != made.westIndex)));
        plan.Follow(m);
        Check("delete: the plan's selection stays on its prop, which moved down one", plan.Selected == watched - 1 && m.props[plan.Selected].Equals(watchedProp), "plan " + plan.Selected);
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("delete: Undo brings it back", m.props.SequenceEqual(kept));
        plan.Follow(m);
        Check("delete: after Undo the plan's selection is on its prop again", plan.Selected == watched, "plan " + plan.Selected);
        plan.Select(made.westIndex, false);
        plan.Follow(m);
        FrontRoomsModuleEditing.RemoveProps(module, new[] { made.westIndex });
        plan.Follow(m);
        Check("delete: a deleted prop leaves nothing selected in the plan", plan.Selected == -1, "plan " + plan.Selected);
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        preview.Rebuild();
    }

    // ---------- Gameplay markers ----------

    /// <summary>For every turn, each marker where ModuleToWorld puts it is where the turned module (RoomModuleData.Rotated) has it on the stamped cells, and back.</summary>
    static void MarkerConversions(FrontRoomsModulePreview preview)
    {
        var m = preview.module.data;
        var saved = m.markers;
        m.markers = new[]
        {
            new ModuleMarker { kind = ModuleMarkerKind.KeySpot, x = 1.3f, z = 2.7f, y = .74f, yaw = 0f, tag = "", host = "Kit_OfficeDesk" },
            new ModuleMarker { kind = ModuleMarkerKind.RelayEntry, x = 7.45f, z = 8.05f, yaw = 37f, tag = "vent", host = "" },
            new ModuleMarker { kind = ModuleMarkerKind.RelayEntry, x = m.WidthMetres - .4f, z = .4f, yaw = 271.5f, tag = "doorway", host = "" },
        };
        var cs = MapGrid.CellSize;
        try
        {
            for (var turn = 0; turn < 4; turn++)
            {
                preview.rotation = turn;
                preview.Rebuild();
                var turned = m.Rotated(turn);
                FrontRoomsModulePreview.Placement(turned, out var cx, out var cy);
                var bad = new List<string>();
                for (var k = 0; k < m.markers.Length; k++)
                {
                    var mk = m.markers[k];
                    var t = turned.markers[k];
                    var world = preview.ModuleToWorld(new Vector2(mk.x, mk.z), mk.y);
                    var expected = preview.transform.TransformPoint(new Vector3(cx * cs + t.x, t.y, cy * cs + t.z));
                    var rotation = preview.ModuleToWorldRotation(mk.yaw);
                    if ((world - expected).magnitude > Near || Quaternion.Angle(rotation, preview.transform.rotation * Quaternion.Euler(0f, t.yaw, 0f)) > .05f
                        || (preview.WorldToModule(world) - new Vector2(mk.x, mk.z)).magnitude > Near || !CloseYaw(preview.WorldToModuleYaw(rotation), mk.yaw)
                        || t.kind != mk.kind || t.tag != mk.tag || t.host != mk.host)
                        bad.Add((k + 1) + " at " + (world - expected).magnitude.ToString("0.0000") + " m");
                }
                Check("turn " + turn + ": markers: ModuleToWorld and its rotation match RoomModuleData.Rotated on the stamped cells, and back", bad.Count == 0, string.Join(", ", bad));
                // What the built map registered for the Relay, against where the conversions put each entry (on the floor), with its tag.
                var entries = new List<(Vector3 pos, string tag)>();
                preview.World.RelayEntries(entries);
                var relays = m.markers.Where(q => q.kind == ModuleMarkerKind.RelayEntry).ToArray();
                Check("turn " + turn + ": the built map registers each Relay entry where ModuleToWorld puts it, with its tag",
                    entries.Count == relays.Length && relays.All(mk => entries.Any(x => x.tag == mk.tag && (x.pos - preview.ModuleToWorld(new Vector2(mk.x, mk.z))).magnitude <= Near)),
                    entries.Count + " registered: " + string.Join(", ", entries.Select(x => (x.tag ?? "-") + " " + x.pos.ToString("F3"))));
            }
            // One quarter turn at a time (Rotated(4) is the no-turn copy).
            var round = m.Rotated(1).Rotated(1).Rotated(1).Rotated(1).markers;
            Check("markers: four quarter turns, one at a time, put every marker back", round.Select((q, k) => Close(q.x, m.markers[k].x) && Close(q.z, m.markers[k].z) && Close(q.y, m.markers[k].y)
                && CloseYaw(q.yaw, m.markers[k].yaw) && q.kind == m.markers[k].kind && q.tag == m.markers[k].tag && q.host == m.markers[k].host).All(ok => ok));
        }
        finally
        {
            m.markers = saved;
            preview.rotation = 1;
            preview.Rebuild();
        }
    }

    /// <summary>A 9 x 9 m room, a doorway south, no columns, no props: markers are checked in it.</summary>
    static RoomModuleData MarkerRoom(params ModuleMarker[] markers)
    {
        var d = new RoomModuleData { width = 3, depth = 3, height = ZoneHeight.Standard, theme = ZoneTheme.Level0, fill = ModuleFill.None, columns = ModuleColumns.None };
        d.Normalize();
        d.south[1] = ModuleEdge.Arch;
        d.markers = markers;
        return d;
    }

    static ModuleMarker KeyAt(float x, float z, float y = 0f) => new ModuleMarker { kind = ModuleMarkerKind.KeySpot, x = x, z = z, y = y, tag = "", host = "" };

    static ModuleMarker RelayAt(float x, float z) => new ModuleMarker { kind = ModuleMarkerKind.RelayEntry, x = x, z = z, tag = "", host = "" };

    static ModuleProp Crate(float x, float z, float yaw = 0f) => new ModuleProp { kit = "Kit_Crate", x = x, z = z, yaw = yaw };

    /// <summary>The checks of a room, with the kit library's real footprints.</summary>
    static (List<string> errors, List<string> warnings) Validate(RoomModuleData d)
    {
        var errors = new List<string>();
        var warnings = new List<string>();
        d.Validate(errors, warnings, FrontRoomsMapWorld.KitFootprint);
        return (errors, warnings);
    }

    /// <summary>Whether a list has a message about marker <paramref name="number"/> that contains <paramref name="text"/>.</summary>
    static bool Says(List<string> messages, int number, string text) => messages.Any(x => x.StartsWith("Marker " + number + " (") && x.Contains(text));

    static string Messages((List<string> errors, List<string> warnings) r) => r.errors.Count + " error(s), " + r.warnings.Count + " warning(s): " + string.Join(" | ", r.errors.Concat(r.warnings));

    /// <summary>The markers' errors and warnings (RoomModuleData.ValidateMarkers), each against a room that is otherwise fine.</summary>
    static void MarkerChecks()
    {
        if (FrontRoomsMapWorld.KitFootprint("Kit_Crate") == null)
        {
            Check("marker checks: the crate kit is in the library", false);
            return;
        }
        var r = Validate(MarkerRoom(KeyAt(4.5f, 4.5f), RelayAt(2.1f, 2.1f)));
        Check("marker checks: a key spot and a Relay entry on open floor pass", r.errors.Count == 0 && r.warnings.Count == 0, Messages(r));

        r = Validate(MarkerRoom(KeyAt(.1f, 4.5f), RelayAt(.3f, 4.5f)));
        Check("marker checks: a key spot and a Relay entry in the west wall are errors", Says(r.errors, 1, "in or beyond a wall") && Says(r.errors, 2, "in or beyond a wall"), Messages(r));

        var d = MarkerRoom(RelayAt(3.1f, 4.5f));
        d.innerEast[0 + 1 * (d.width - 1)] = ModuleEdge.Wall;
        r = Validate(d);
        Check("marker checks: a Relay entry in an inner wall is an error", Says(r.errors, 1, "in an inner wall"), Messages(r));

        d = MarkerRoom(RelayAt(4.5f, 4.5f), KeyAt(4.5f, 4.5f, .3f));
        d.props = new[] { Crate(4.5f, 4.5f) };
        r = Validate(d);
        Check("marker checks: a Relay entry in a prop, and a key inside one, are errors", Says(r.errors, 1, "stands in prop 1 (Kit_Crate)") && Says(r.errors, 2, "is inside prop 1 (Kit_Crate)"), Messages(r));

        // On the crate's lid, near its south edge so it can be taken from the floor.
        d = MarkerRoom();
        d.props = new[] { Crate(4.5f, 4.5f) };
        var top = FrontRoomsModuleEditing.TopUnder(d, new Vector2(4.5f, 4.2f));
        var placed = FrontRoomsModuleEditing.NewMarker(d, ModuleMarkerKind.KeySpot, new Vector2(4.52f, 4.19f));
        d.markers = new[] { placed };
        r = Validate(d);
        Check("marker checks: a key spot put on a prop lies on its top (0.75 m) and passes", top.HasValue && Close(top.Value, .75f) && Close(placed.y, .75f) && r.errors.Count == 0 && r.warnings.Count == 0,
            "top " + (top?.ToString("0.000") ?? "none") + ", key y " + placed.y.ToString("0.000") + "; " + Messages(r));
        var floorKey = FrontRoomsModuleEditing.NewMarker(d, ModuleMarkerKind.KeySpot, new Vector2(7f, 7f));
        var floorRelay = FrontRoomsModuleEditing.NewMarker(d, ModuleMarkerKind.RelayEntry, new Vector2(4.5f, 4.5f));
        Check("marker checks: a key spot on bare floor lies on it, a Relay entry over a prop still stands on the floor", floorKey.y == 0f && floorRelay.y == 0f);

        d = MarkerRoom(KeyAt(3.1f, 3.1f));
        d.columns = ModuleColumns.Custom;
        d.customColumns = new[] { new ModuleColumn { x = 1, y = 1 } };
        r = Validate(d);
        Check("marker checks: a key spot in a custom column is an error", Says(r.errors, 1, "stands in a column (corner 1, 1)"), Messages(r));
        d.columns = ModuleColumns.Auto;
        d.markers = new[] { KeyAt(6f, 6f) };
        r = Validate(d);
        Check("marker checks: where an Auto column may stand is a warning, not an error", r.errors.Count == 0 && Says(r.warnings, 1, "an Auto column may stand"), Messages(r));

        // Four crates box a spot in; every cell can still be reached round them.
        d = MarkerRoom(RelayAt(4.5f, 4.5f), KeyAt(4.5f, 4.5f));
        d.props = new[] { Crate(4.5f, 3.6f), Crate(4.5f, 5.4f), Crate(3.6f, 4.5f, 90f), Crate(5.4f, 4.5f, 90f) };
        r = Validate(d);
        Check("marker checks: shut in by props, a Relay entry and a key spot are errors (and nothing else is)",
            Says(r.errors, 1, "could not walk out of it") && Says(r.errors, 2, "nobody can get within 0.9 m") && r.errors.Count == 2, Messages(r));

        d = MarkerRoom(KeyAt(4.5f, 4.5f), KeyAt(7f, 7f), RelayAt(2.1f, 2.1f));
        d.markers[2].y = .5f;
        r = Validate(d);
        Check("marker checks: a second key spot and a raised Relay entry are warnings", r.errors.Count == 0 && Says(r.warnings, 2, "only the first key spot is used") && Says(r.warnings, 3, "height is ignored"), Messages(r));

        r = Validate(MarkerRoom(KeyAt(4.5f, 4.5f, 1.9f)));
        Check("marker checks: a key spot above 1.8 m is a warning (over the eye line), not an error", r.errors.Count == 0 && Says(r.warnings, 1, "above the player's eye line"), Messages(r));
        r = Validate(MarkerRoom(KeyAt(4.5f, 4.5f, MapGrid.CeilingHeight(ZoneHeight.Standard))));
        Check("marker checks: a key spot at the ceiling is an error, and not also the eye-line warning", Says(r.errors, 1, "ceiling") && !Says(r.warnings, 1, "eye line"), Messages(r));
    }

    /// <summary>Add, move, turn, edit and remove markers on the module asset, each one Undo; the plan's marker selection follows its marker and never sits with a prop's.</summary>
    static void MarkerEdits(FrontRoomsRoomModule module, Made made)
    {
        var m = module.data;
        var before = m.markers.ToArray();
        var plan = new FrontRoomsModulePlanView(() => { });

        Undo.IncrementCurrentGroup();
        var relay = FrontRoomsModuleEditing.AddMarker(module, ModuleMarkerKind.RelayEntry, new Vector2(8.03f, 2.02f));
        var r0 = m.markers[relay];
        Check("marker edits: a Relay entry is added at the point (0.05 m), on the floor", m.markers.Length == before.Length + 1 && r0.kind == ModuleMarkerKind.RelayEntry && Close(r0.x, 8.05f) && Close(r0.z, 2f) && r0.y == 0f, M(r0));
        Undo.FlushUndoRecordObjects();
        Undo.IncrementCurrentGroup();
        var desk = m.props[made.deskIndex];
        var key = FrontRoomsModuleEditing.AddMarker(module, ModuleMarkerKind.KeySpot, new Vector2(desk.x, desk.z));
        var k0 = m.markers[key];
        var deskTop = FrontRoomsModuleEditing.TopHeight(desk) ?? -1f;
        Check("marker edits: a key spot put on the desk lies on its top", key == relay + 1 && Close(k0.y, deskTop), M(k0) + ", desk top " + deskTop.ToString("0.000"));
        Undo.FlushUndoRecordObjects();

        plan.SelectMarker(key);
        plan.Follow(m);
        plan.Select(made.floorIndex, false);
        var propClears = plan.SelectedMarker == -1 && plan.Selected == made.floorIndex;
        plan.SelectMarker(key);
        plan.Follow(m);
        Check("marker edits: selecting a prop lets the marker go, and the other way round", propClears && plan.Selected == -1 && plan.SelectedMarker == key, "prop " + plan.Selected + ", marker " + plan.SelectedMarker);

        Undo.IncrementCurrentGroup();
        FrontRoomsModuleEditing.MoveMarker(module, key, new Vector2(desk.x + .33f, desk.z + .21f));
        var moved = m.markers[key];
        plan.Follow(m);
        Check("marker edits: a move snaps to 0.05 m and keeps the height", Close(moved.x, FrontRoomsModuleEditing.Snap(desk.x + .33f)) && Close(moved.z, FrontRoomsModuleEditing.Snap(desk.z + .21f)) && moved.y == k0.y, M(moved));
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        plan.Follow(m);
        Check("marker edits: Undo puts the move back, the plan keeps the marker", m.markers[key].Equals(k0) && plan.SelectedMarker == key, M(m.markers[key]) + ", plan " + plan.SelectedMarker);

        Undo.IncrementCurrentGroup();
        FrontRoomsModuleEditing.TurnMarker(module, key);
        FrontRoomsModuleEditing.TurnMarker(module, key);
        FrontRoomsModuleEditing.TurnMarker(module, key);
        FrontRoomsModuleEditing.TurnMarker(module, key);
        var full = m.markers[key].yaw;
        FrontRoomsModuleEditing.TurnMarker(module, key);
        Check("marker edits: turns add 90° and wrap at 360°", CloseYaw(full, k0.yaw) && full < 360f && CloseYaw(m.markers[key].yaw, k0.yaw + 90f), "yaw " + m.markers[key].yaw);
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("marker edits: one Undo puts the turns back", m.markers[key].Equals(k0), M(m.markers[key]));

        Undo.IncrementCurrentGroup();
        var tagged = m.markers[relay];
        tagged.tag = "vent";
        FrontRoomsModuleEditing.SetMarker(module, relay, tagged);
        var set = m.markers[relay].tag == "vent";
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        Check("marker edits: a tag is set, and Undo clears it", set && m.markers[relay].Equals(r0), M(m.markers[relay]));

        // The Relay entry goes from in front of the selected key: the plan's selection stays on the key, one down.
        plan.SelectMarker(key);
        plan.Follow(m);
        Undo.IncrementCurrentGroup();
        FrontRoomsModuleEditing.RemoveMarkers(module, new[] { relay });
        plan.Follow(m);
        Check("marker edits: removing the marker in front keeps the plan on its marker, one down", m.markers.Length == before.Length + 1 && plan.SelectedMarker == key - 1 && m.markers[plan.SelectedMarker].Equals(k0), "plan " + plan.SelectedMarker);
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();
        plan.Follow(m);
        Check("marker edits: Undo brings it back, the plan is on its marker again", m.markers.Length == before.Length + 2 && m.markers[relay].Equals(r0) && plan.SelectedMarker == key, "plan " + plan.SelectedMarker);
        Undo.IncrementCurrentGroup();
        FrontRoomsModuleEditing.RemoveMarkers(module, new[] { key });
        plan.Follow(m);
        Check("marker edits: a removed marker leaves nothing selected", plan.SelectedMarker == -1 && m.markers.Length == before.Length + 1);
        Undo.FlushUndoRecordObjects();
        Undo.PerformUndo();

        Undo.PerformUndo();
        Undo.PerformUndo();
        Check("marker edits: Undo of both adds leaves the markers as they were", m.markers.SequenceEqual(before), m.markers.Length + " marker(s)");
    }

    static string M(ModuleMarker mk) => mk.kind + " x " + mk.x.ToString("0.000") + " z " + mk.z.ToString("0.000") + " y " + mk.y.ToString("0.000") + " yaw " + mk.yaw.ToString("0.0") + (string.IsNullOrEmpty(mk.tag) ? "" : " tag " + mk.tag);

    /// <summary>The sample modules as the code ships them and as their assets are: no errors, no warnings, and their markers.</summary>
    static void Samples()
    {
        var kinds = new HashSet<string>();
        foreach (var (name, _, data) in FrontRoomsLevelDesigner.Samples())
        {
            var r = Validate(data);
            Check("sample " + name + " (code): no errors or warnings", r.errors.Count == 0 && r.warnings.Count == 0 && data.markers.Length > 0, data.markers.Length + " marker(s); " + Messages(r));
            foreach (var mk in data.markers) kinds.Add(mk.kind == ModuleMarkerKind.KeySpot ? "key" : mk.tag);
            var asset = AssetDatabase.LoadAssetAtPath<FrontRoomsRoomModule>(FrontRoomsRoomModule.Folder + "/" + name + ".asset");
            if (asset == null)
            {
                Check("sample " + name + " (asset): exists", false);
                continue;
            }
            r = Validate(asset.data.Clone());
            Check("sample " + name + " (asset): no errors or warnings", r.errors.Count == 0 && r.warnings.Count == 0, asset.data.markers.Length + " marker(s); " + Messages(r));
        }
        Check("samples: a key spot, a \"vent\" and a \"doorway\" Relay entry among them", kinds.Contains("key") && kinds.Contains("vent") && kinds.Contains("doorway"), string.Join(", ", kinds));
    }

    // ---------- Panels ----------

    /// <summary>
    /// The window switching module: nothing of the old one stays selected. A
    /// marker selection would otherwise be found again by Follow in a module
    /// with a like marker (a duplicate).
    /// </summary>
    static void PanelSwitch(FrontRoomsRoomModule module)
    {
        var window = ScriptableObject.CreateInstance<FrontRoomsLevelDesignerWindow>();
        var a = ScriptableObject.CreateInstance<FrontRoomsRoomModule>();
        var b = ScriptableObject.CreateInstance<FrontRoomsRoomModule>();
        try
        {
            a.hideFlags = b.hideFlags = HideFlags.DontSave;
            a.data = module.data.Clone();
            a.data.markers = new[] { KeyAt(4.5f, 4.5f), RelayAt(2.1f, 2.1f) };
            b.data = a.data.Clone();
            var plan = (FrontRoomsModulePlanView)typeof(FrontRoomsLevelDesignerWindow).GetField("plan", BindingFlags.NonPublic | BindingFlags.Instance).GetValue(window);
            var setModule = typeof(FrontRoomsLevelDesignerWindow).GetMethod("SetModule", BindingFlags.NonPublic | BindingFlags.Instance);
            setModule.Invoke(window, new object[] { a });
            plan.SelectMarker(1);
            plan.Follow(a.data);
            setModule.Invoke(window, new object[] { b });
            plan.Follow(b.data);
            var marker = plan.SelectedMarker;
            setModule.Invoke(window, new object[] { a });
            plan.Select(0, false);
            plan.Follow(a.data);
            setModule.Invoke(window, new object[] { b });
            plan.Follow(b.data);
            Check("window: switching module leaves no marker or prop of the old one selected", marker == -1 && plan.Selected == -1 && plan.SelectedMarker == -1, "marker " + marker + ", prop " + plan.Selected);
        }
        finally
        {
            Object.DestroyImmediate(window);
            Object.DestroyImmediate(a);
            Object.DestroyImmediate(b);
        }
    }

    /// <summary>
    /// A field typed in (a Relay entry's tag, a number) writes the module at
    /// once but rebuilds the preview only when the field lets go of the
    /// keyboard, and also when the focus has gone while editingTextField
    /// stays set (the field is no longer drawn: another marker was picked).
    /// </summary>
    static void FieldTyping(FrontRoomsRoomModule module)
    {
        var gui = typeof(FrontRoomsModuleGUI);
        var edited = gui.GetMethod("Edited", BindingFlags.NonPublic | BindingFlags.Static);
        var changes = 0;
        Action<FrontRoomsRoomModule> onChanged = c => { if (c == module) changes++; };
        FrontRoomsRoomModule.Changed += onChanged;
        try
        {
            EditorGUIUtility.editingTextField = true;
            GUIUtility.keyboardControl = 4242;
            edited.Invoke(null, new object[] { module });
            FrontRoomsModuleGUI.Release();
            var whileTyping = changes;
            GUIUtility.keyboardControl = 0;
            FrontRoomsModuleGUI.Release();
            Check("fields: typing holds the preview back; it rebuilds once the field has lost the keyboard (even with editingTextField left set)", whileTyping == 0 && changes == 1,
                whileTyping + " rebuild(s) while typing, " + changes + " after");
        }
        finally
        {
            FrontRoomsRoomModule.Changed -= onChanged;
            EditorGUIUtility.editingTextField = false;
            GUIUtility.keyboardControl = 0;
            FrontRoomsModuleGUI.Release(true);
        }
    }

    // ---------- Live rebuild ----------

    /// <summary>
    /// FrontRoomsModulePreview.RebuildLive, which Play uses for every edit,
    /// run in edit mode (the walker is then the map's plain eye transform): an
    /// edit away from the walker rebuilds the room's chunk in the same map
    /// and leaves the walker where it stands; a prop or a column put where it
    /// stands sends it to the entrance; a new size, seed or profile asks for
    /// a full rebuild. The module is put back afterwards.
    /// </summary>
    static void LiveRebuild(FrontRoomsModulePreview preview, Made made)
    {
        var live = typeof(FrontRoomsModulePreview).GetMethod("RebuildLive", BindingFlags.NonPublic | BindingFlags.Instance);
        if (live == null)
        {
            Check("live rebuild: FrontRoomsModulePreview.RebuildLive exists", false);
            return;
        }
        var module = preview.module;
        var m = module.data;
        var saved = JsonUtility.ToJson(m);
        var savedSeed = preview.seed;
        var savedProfile = preview.profile;
        bool Live() => (bool)live.Invoke(preview, null);
        try
        {
            preview.rotation = 0;
            preview.Rebuild();
            var world = preview.World;
            var eye = world != null ? world.Player : null;
            if (eye == null)
            {
                Check("live rebuild: the preview's map has a walker", false);
                return;
            }
            // The walker stands on free floor in the east half of the room.
            var standing = preview.ModuleToWorld(new Vector2(9f, 4.5f), .05f);
            eye.position = standing;

            // (a) A prop moved and a Relay entry added away from the walker.
            var crate = m.props[made.floorIndex];
            crate.z += .5f;
            m.props[made.floorIndex] = crate;
            m.markers = m.markers.Append(RelayAt(10.5f, 1.5f)).ToArray();
            var ok = Live();
            var rebuilt = preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true).FirstOrDefault(t => t.index == made.floorIndex && t.gameObject.activeInHierarchy);
            var entries = new List<(Vector3 pos, string tag)>();
            preview.World.RelayEntries(entries);
            Check("live rebuild: an edit away from the walker rebuilds the room in the same map, the walker stays where it stands",
                ok && preview.World == world && world.Player == eye && (eye.position - standing).magnitude < 1e-4f,
                "live " + ok + ", same map " + (preview.World == world) + ", walker moved " + (eye.position - standing).magnitude.ToString("0.000") + " m");
            Check("live rebuild: the moved prop and the new Relay entry are in the rebuilt chunk",
                rebuilt != null && (rebuilt.transform.position - preview.ModuleToWorld(new Vector2(crate.x, crate.z), crate.y)).magnitude < Near
                && entries.Count == 1 && (entries[0].pos - preview.ModuleToWorld(new Vector2(10.5f, 1.5f))).magnitude < Near,
                (rebuilt != null ? "prop off by " + (rebuilt.transform.position - preview.ModuleToWorld(new Vector2(crate.x, crate.z), crate.y)).magnitude.ToString("0.000") + " m" : "prop not found") + ", " + entries.Count + " entry(ies)");

            // Where the walker goes when something now stands where it stood.
            FrontRoomsModulePreview.Placement(preview.Stamped, out var x0, out var y0);
            FrontRoomsModulePreview.Entrance(preview.Stamped, x0, y0, out var spawn, out _);
            var entrance = world.transform.TransformPoint(spawn);

            // (b) A crate put where the walker stands.
            m.props = m.props.Append(Crate(9f, 4.5f)).ToArray();
            ok = Live();
            Check("live rebuild: a prop put where the walker stands sends it to the entrance", ok && preview.World == world && (eye.position - entrance).magnitude < 1e-3f,
                "live " + ok + ", walker " + (eye.position - entrance).magnitude.ToString("0.000") + " m from the entrance");
            m.props = m.props.Take(m.props.Length - 1).ToArray();

            // (b) A column put on the corner where the walker stands (inner corner (3, 1), at 9, 3 m).
            standing = preview.ModuleToWorld(new Vector2(9f, 3f), .05f);
            eye.position = standing;
            ok = Live();
            var stayed = ok && (eye.position - standing).magnitude < 1e-4f;
            m.columns = ModuleColumns.Custom;
            m.customColumns = new[] { new ModuleColumn { x = 3, y = 1 } };
            ok = Live();
            Check("live rebuild: a column put where the walker stands sends it to the entrance", stayed && ok && (eye.position - entrance).magnitude < 1e-3f,
                "stood still before " + stayed + ", live " + ok + ", walker " + (eye.position - entrance).magnitude.ToString("0.000") + " m from the entrance");

            // (c) What needs the whole map again.
            m.Resize(m.width - 1, m.depth);
            var resized = Live();
            JsonUtility.FromJsonOverwrite(saved, m);
            preview.seed = savedSeed + 1;
            var reseeded = Live();
            preview.seed = savedSeed;
            preview.profile = savedProfile != null ? null : FrontRoomsLevelProfiles.Resolve();
            var reprofiled = Live();
            preview.profile = savedProfile;
            Check("live rebuild: a new size, seed or profile asks for a full rebuild", !resized && !reseeded && !reprofiled && preview.World == world,
                "size " + resized + ", seed " + reseeded + ", profile " + reprofiled);
        }
        finally
        {
            JsonUtility.FromJsonOverwrite(saved, m);
            preview.seed = savedSeed;
            preview.profile = savedProfile;
            preview.rotation = 1;
            preview.Rebuild();
        }
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

        // How often the generator's carved rooms take a module: each side rolled from min to max cells.
        var g = new MapSettings { standardRooms = 2, standardRoomMin = 2, standardRoomMax = 4, tallRooms = 0 };
        var m = module.data.Clone();
        // 4 x 3 in rooms of 2-4 a side: 4 x 3 and 4 x 4 as it is, 3 x 4 turned.
        Check("generator fit: a 4 x 3 module fits 3 of 9 room sizes", Close(FrontRoomsModuleGUI.FitShare(m, g, out _, out _), 3f / 9f));
        m.allowRotate = false;
        Check("generator fit: unturned, 2 of 9", Close(FrontRoomsModuleGUI.FitShare(m, g, out _, out _), 2f / 9f));
        m.Resize(5, 3);
        Check("generator fit: wider than the largest room never fits", FrontRoomsModuleGUI.FitShare(m, g, out _, out _) == 0f);
        g.standardRoomMax = 12;
        m.Resize(8, 8);
        Check("generator fit: room sizes clamp to the chunk (8 x 8 fits only an 8 x 8 room)", Close(FrontRoomsModuleGUI.FitShare(m, g, out _, out var max), 1f / 49f) && max == MapGrid.ChunkCells);
        m.height = ZoneHeight.Tall;
        Check("generator fit: a height that carves no rooms never places it", FrontRoomsModuleGUI.FitShare(m, g, out _, out _) < 0f);

        // Over a run the module tier is the level's module tier + run tier - 1.
        m.minTier = 2;
        m.maxTier = 3;
        var from = FrontRoomsModuleGUI.RunTiers(m, 0, 5, out var first, out var last);
        Check("generator tiers: module tiers 2-3 at module tier 0 come at run tiers 3-4 of 5", from && first == 3 && last == 4, first + "-" + last);
        Check("generator tiers: at module tier 4 the run (4-8) is past the module (2-3): never", !FrontRoomsModuleGUI.RunTiers(m, 4, 5, out first, out last), first + "-" + last);
        Check("generator tiers: one run tier at module tier 0 never reaches 2-3", !FrontRoomsModuleGUI.RunTiers(m, 0, 1, out first, out last), first + "-" + last);
        m.minTier = 0;
        m.maxTier = 9;
        Check("generator tiers: a module of every tier comes at every run tier", FrontRoomsModuleGUI.RunTiers(m, 1, 5, out first, out last) && first == 1 && last == 5, first + "-" + last);
    }
}
