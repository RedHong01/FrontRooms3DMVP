using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The room module panel's sections (notes, room, the selected prop, where
/// the generator may use it, checks), drawn the same in the module's
/// Inspector and in the Level Designer window. Edits go through
/// FrontRoomsModuleEditing, so they are undoable and rebuild the preview.
/// </summary>
public static class FrontRoomsModuleGUI
{
    // A slider is held: its module rebuilds the preview when it is let go, as after a plan drag.
    static FrontRoomsRoomModule held;

    /// <summary>After a field edit: let the preview follow now, or once the slider being dragged is let go.</summary>
    static void Edited(FrontRoomsRoomModule module)
    {
        if (GUIUtility.hotControl == 0)
        {
            FrontRoomsModuleEditing.Changed(module);
            return;
        }
        EditorUtility.SetDirty(module);
        held = module;
    }

    /// <summary>
    /// Once the held slider is let go, rebuild the preview. Each panel calls
    /// it at the end of its GUI pass, and with <paramref name="force"/> when
    /// it closes, so a slider drag cut short still reaches the preview.
    /// </summary>
    public static void Release(bool force = false)
    {
        if (held == null || (!force && GUIUtility.hotControl != 0)) return;
        var module = held;
        held = null;
        FrontRoomsRoomModule.NotifyChanged(module);
    }

    /// <summary>Free text for the team; the preview does not change.</summary>
    public static void Notes(FrontRoomsRoomModule module)
    {
        EditorGUI.BeginChangeCheck();
        var notes = EditorGUILayout.TextArea(module.notes ?? "", GUILayout.MinHeight(32));
        if (EditorGUI.EndChangeCheck())
        {
            FrontRoomsModuleEditing.Record(module, "Edit notes");
            module.notes = notes;
            EditorUtility.SetDirty(module);
        }
    }

    /// <summary>
    /// Footprint, theme, ceiling, fill and columns. <paramref name="resizeFrom"/>
    /// is the caller's snapshot while a size slider is held, so passing
    /// through a smaller size loses nothing.
    /// </summary>
    public static void Room(FrontRoomsRoomModule module, ref RoomModuleData resizeFrom)
    {
        var m = module.data;
        EditorGUI.BeginChangeCheck();
        var width = EditorGUILayout.IntSlider(new GUIContent("Width (cells, X)", "3 m each"), m.width, 1, RoomModuleData.MaxCells);
        var depth = EditorGUILayout.IntSlider(new GUIContent("Depth (cells, Z)", "3 m each"), m.depth, 1, RoomModuleData.MaxCells);
        var theme = (ZoneTheme)EditorGUILayout.EnumPopup(new GUIContent("Theme", "Level 0 paper and carpet, or a Level 4 office (Standard height only)"), m.theme);
        var height = theme == ZoneTheme.Office ? ZoneHeight.Standard : (ZoneHeight)EditorGUILayout.EnumPopup(new GUIContent("Ceiling", "Low 2.4 m, Standard 2.9 m, Tall 5.4 m"), m.height);
        var fill = (ModuleFill)EditorGUILayout.EnumPopup(new GUIContent("Fill", "Auto: as a generated room. Office: the Office kit fills round your props. Pile: a furniture pile."), m.fill);
        var columns = (ModuleColumns)EditorGUILayout.EnumPopup(new GUIContent("Columns", "Auto: the map's 6 m grid rule where the room lands. Custom: click inner corners in the plan."), m.columns);
        if (EditorGUI.EndChangeCheck())
        {
            FrontRoomsModuleEditing.Record(module, "Edit room module");
            if (width != m.width || depth != m.depth)
            {
                if (resizeFrom == null) resizeFrom = m.Clone();
                var resized = resizeFrom.Clone();
                resized.Resize(width, depth);
                CopyFootprint(resized, m);
            }
            m.theme = theme;
            m.height = height;
            m.fill = fill;
            m.columns = columns;
            m.Normalize();
            Edited(module);
        }
        if (GUIUtility.hotControl == 0) resizeFrom = null;

        EditorGUILayout.LabelField(m.width * 3 + " × " + m.depth * 3 + " m · ceiling " + MapGrid.CeilingHeight(m.height).ToString("0.0") + " m · clear floor "
            + ModuleUnits.ClearSpan(m.width).ToString("0.00") + " × " + ModuleUnits.ClearSpan(m.depth).ToString("0.00") + " m", EditorStyles.miniLabel);
    }

    static void CopyFootprint(RoomModuleData from, RoomModuleData to)
    {
        to.width = from.width;
        to.depth = from.depth;
        to.south = from.south; to.north = from.north; to.west = from.west; to.east = from.east;
        to.innerEast = from.innerEast; to.innerNorth = from.innerNorth;
        to.lamps = from.lamps;
        to.customColumns = from.customColumns;
    }

    /// <summary>The plan's selected prop: kit, place, height, yaw, collider, and Turn / Duplicate / Remove.</summary>
    public static void SelectedProp(FrontRoomsRoomModule module, FrontRoomsModulePlanView plan)
    {
        var m = module.data;
        var selected = plan.Selected;
        if (selected < 0 || selected >= m.props.Length) return;
        var p = m.props[selected];
        var names = FrontRoomsModuleEditing.Kits();
        using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
        {
            // A kit not in the list keeps its own entry, so editing other fields never swaps it.
            var index = System.Array.IndexOf(names, p.kit);
            var options = index >= 0 ? names : new[] { "(missing) " + p.kit }.Concat(names).ToArray();
            var current = Mathf.Max(0, index);
            EditorGUI.BeginChangeCheck();
            var picked = EditorGUILayout.Popup("Kit", current, options);
            var x = EditorGUILayout.Slider("X (m from west wall line)", p.x, 0f, m.WidthMetres);
            var z = EditorGUILayout.Slider("Z (m from south wall line)", p.z, 0f, m.DepthMetres);
            var y = EditorGUILayout.Slider(new GUIContent("Height above floor", "For wall pieces: a clock, an interior window"), p.y, 0f, MapGrid.CeilingHeight(m.height));
            var yaw = EditorGUILayout.Slider("Yaw (0 = front faces north)", p.yaw, 0f, 359f);
            var noCollider = EditorGUILayout.Toggle(new GUIContent("No collider", "Desk-top clutter: the player and the Relay pass through it"), p.noCollider);
            if (EditorGUI.EndChangeCheck())
            {
                FrontRoomsModuleEditing.Record(module, "Edit prop");
                var kit = picked != current ? options[picked] : p.kit;
                // Only a field that changed snaps (an untouched slider hands back the stored value), so a wall unit keeps its exact gap.
                float Snapped(float v, float was) => v != was ? FrontRoomsModuleEditing.Snap(v) : was;
                m.props[selected] = new ModuleProp
                {
                    kit = kit, x = Snapped(x, p.x), z = Snapped(z, p.z), y = Snapped(y, p.y),
                    yaw = Mathf.Repeat(yaw, 360f), noCollider = noCollider,
                };
                Edited(module);
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Turn 90°")) FrontRoomsModuleEditing.TurnProp(module, selected);
                if (GUILayout.Button("Duplicate")) plan.Select(FrontRoomsModuleEditing.DuplicateProp(module, selected));
                if (GUILayout.Button("Remove")) plan.RemoveSelected();
            }
        }
    }

    /// <summary>Weight, may rotate and tier range: where the generator may use the module. They do not change the room, so the preview is left alone.</summary>
    public static void GeneratorFields(FrontRoomsRoomModule module)
    {
        var m = module.data;
        EditorGUI.BeginChangeCheck();
        var weight = EditorGUILayout.FloatField(new GUIContent("Weight", "Relative chance among modules that fit"), m.weight);
        var rotate = EditorGUILayout.Toggle(new GUIContent("May rotate", "The generator may turn it by quarter turns"), m.allowRotate);
        var minTier = EditorGUILayout.IntField("From tier", m.minTier);
        var maxTier = EditorGUILayout.IntField("To tier", m.maxTier);
        if (EditorGUI.EndChangeCheck())
        {
            FrontRoomsModuleEditing.Record(module, "Edit room module");
            m.weight = weight;
            m.allowRotate = rotate;
            m.minTier = minTier;
            m.maxTier = maxTier;
            m.Normalize();
            EditorUtility.SetDirty(module);
        }
    }

    /// <summary>
    /// The share of the generator's carved rooms of the module's height that
    /// can take it in an allowed turn: each side of a carved room is rolled
    /// from min to max cells (FrontRoomsMapGenerator.Rooms, clamped to the
    /// chunk), and the module must fit inside it. -1 when that height carves no rooms.
    /// </summary>
    public static float FitShare(RoomModuleData m, MapSettings g, out int min, out int max)
    {
        int count;
        switch (m.height)
        {
            case ZoneHeight.Low: count = g.lowRooms; min = g.lowRoomMin; max = g.lowRoomMax; break;
            case ZoneHeight.Tall: count = g.tallRooms; min = g.tallRoomMin; max = g.tallRoomMax; break;
            default: count = g.standardRooms; min = g.standardRoomMin; max = g.standardRoomMax; break;
        }
        min = Mathf.Clamp(min, 1, MapGrid.ChunkCells);
        max = Mathf.Clamp(max, min, MapGrid.ChunkCells);
        if (count <= 0) return -1f;
        var fits = 0;
        for (var w = min; w <= max; w++)
        for (var h = min; h <= max; h++)
            if ((m.width <= w && m.depth <= h) || (m.allowRotate && m.depth <= w && m.width <= h)) fits++;
        return fits / (float)((max - min + 1) * (max - min + 1));
    }

    /// <summary>Whether the generator can place the module at all, and how often its rooms are big enough.</summary>
    public static void Fit(FrontRoomsRoomModule module, FrontRoomsLevelProfile profile)
    {
        var m = module.data;
        if (profile == null || profile.generation == null) return;
        var share = FitShare(m, profile.generation, out var min, out var max);
        var rooms = "carved " + m.height + (m.theme == ZoneTheme.Office ? " Office" : "") + " rooms (" + min + "–" + max + " cells a side)";
        var size = m.width + " × " + m.depth;
        if (share < 0f) EditorGUILayout.HelpBox("Never placed: the level carves no " + m.height + " rooms.", MessageType.Warning);
        else if (share == 0f) EditorGUILayout.HelpBox("Never fits: " + rooms + " are all smaller than this " + size + " module.", MessageType.Warning);
        else if (share < .25f) EditorGUILayout.HelpBox("Rarely fits: only " + (share * 100f).ToString("0") + " % of " + rooms + " can take this " + size + " module.", MessageType.Warning);
        else EditorGUILayout.LabelField("Fits " + (share * 100f).ToString("0") + " % of " + rooms + ".", EditorStyles.miniLabel);
    }

    /// <summary>The module's errors and warnings, or that it is ready.</summary>
    public static void Checks(FrontRoomsRoomModule module)
    {
        var errors = new List<string>();
        var warnings = new List<string>();
        module.Validate(errors, warnings);
        if (errors.Count == 0 && warnings.Count == 0) EditorGUILayout.HelpBox("Ready: no problems found.", MessageType.Info);
        foreach (var e in errors) EditorGUILayout.HelpBox(e, MessageType.Error);
        foreach (var w in warnings) EditorGUILayout.HelpBox(w, MessageType.Warning);
    }
}
