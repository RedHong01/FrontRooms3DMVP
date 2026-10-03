using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The room module panel's sections (notes, room, the selected prop, the
/// gameplay markers, where the generator may use it, checks), drawn the
/// same in the module's Inspector and in the Level Designer window. Edits go through
/// FrontRoomsModuleEditing, so they are undoable and rebuild the preview.
/// </summary>
public static class FrontRoomsModuleGUI
{
    // A slider is held or a field typed in: its module rebuilds the preview when it is let go, as after a plan drag.
    static FrontRoomsRoomModule held;

    /// <summary>
    /// A slider is held, or a text or number field has the keyboard. The
    /// focus counts too: a field that is no longer drawn (another marker was
    /// picked) can leave editingTextField set, and the click took the focus.
    /// </summary>
    static bool Holding => GUIUtility.hotControl != 0 || (EditorGUIUtility.editingTextField && GUIUtility.keyboardControl != 0);

    /// <summary>After a field edit: let the preview follow now, or once the slider is let go or the typing is done.</summary>
    static void Edited(FrontRoomsRoomModule module)
    {
        if (!Holding)
        {
            FrontRoomsModuleEditing.Changed(module);
            return;
        }
        EditorUtility.SetDirty(module);
        held = module;
    }

    /// <summary>
    /// Once the held slider is let go or the field typed in loses the
    /// keyboard, rebuild the preview. Each panel calls it at the end of its
    /// GUI pass, and with <paramref name="force"/> when it closes, so a drag
    /// or typing cut short still reaches the preview.
    /// </summary>
    public static void Release(bool force = false)
    {
        if (held == null || (!force && Holding)) return;
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

    // ---------- Gameplay markers ----------

    static readonly Color RowSelected = new Color(.24f, .48f, .90f, .45f);
    static readonly string[] TagPresets = { "vent", "doorway" };

    /// <summary>One line for a marker: its letter and kind, where it is, its height, tag or host.</summary>
    public static string MarkerLine(ModuleMarker mk)
    {
        var key = mk.kind == ModuleMarkerKind.KeySpot;
        var line = (key ? "K  key spot" : "R  Relay entry") + "   (" + mk.x.ToString("0.00") + ", " + mk.z.ToString("0.00") + ")";
        if (key && mk.y > 0f) line += " ↑" + mk.y.ToString("0.00");
        line += "  " + mk.yaw.ToString("0") + "°";
        if (key && !string.IsNullOrEmpty(mk.host)) line += "  on " + FrontRoomsModuleEditing.Short(mk.host);
        if (!key && !string.IsNullOrEmpty(mk.tag)) line += "  \"" + mk.tag + "\"";
        return line;
    }

    /// <summary>
    /// The module's gameplay markers: buttons that arm a key spot or a Relay
    /// entry for the plan, one row per marker (click selects it in the plan,
    /// ✕ removes it), and the selected marker's fields.
    /// </summary>
    public static void Markers(FrontRoomsRoomModule module, FrontRoomsModulePlanView plan)
    {
        var m = module.data;
        using (new EditorGUILayout.HorizontalScope())
        {
            EditorGUILayout.LabelField("Place", GUILayout.Width(40f));
            foreach (ModuleMarkerKind kind in System.Enum.GetValues(typeof(ModuleMarkerKind)))
            {
                var armed = plan.ArmedMarker == kind;
                var label = kind == ModuleMarkerKind.KeySpot ? new GUIContent("Key spot", "Where the zone key lies when it falls in this room (only the first key spot is used). Then click in the plan; Shift keeps placing.")
                    : new GUIContent("Relay entry", "Where the Relay may appear when it is released or relays, on the floor; its tag goes to the sound with the arrival. Then click in the plan; Shift keeps placing.");
                if (GUILayout.Toggle(armed, label, kind == ModuleMarkerKind.KeySpot ? EditorStyles.miniButtonLeft : EditorStyles.miniButtonRight) != armed)
                {
                    // Out of any field, so Esc in the plan reaches the armed marker.
                    GUIUtility.keyboardControl = 0;
                    plan.ArmedMarker = armed ? (ModuleMarkerKind?)null : kind;
                }
            }
        }
        if (m.markers.Length == 0) EditorGUILayout.LabelField("No markers: the key lies where the map puts it, the Relay appears out of sight.", EditorStyles.wordWrappedMiniLabel);
        for (var k = 0; k < m.markers.Length; k++)
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                var r = GUILayoutUtility.GetRect(GUIContent.none, EditorStyles.label, GUILayout.ExpandWidth(true));
                var e = Event.current;
                if (e.type == EventType.Repaint && k == plan.SelectedMarker) EditorGUI.DrawRect(r, RowSelected);
                GUI.Label(r, (k + 1) + "  " + MarkerLine(m.markers[k]));
                if (e.type == EventType.MouseDown && e.button == 0 && r.Contains(e.mousePosition))
                {
                    GUIUtility.keyboardControl = 0;
                    plan.SelectMarker(k);
                    e.Use();
                }
                if (GUILayout.Button("✕", EditorStyles.miniButton, GUILayout.Width(22f)))
                {
                    var selected = plan.SelectedMarker;
                    FrontRoomsModuleEditing.RemoveMarkers(module, new[] { k });
                    // The selection stays on the same marker; the removed one leaves none.
                    plan.SelectMarker(selected == k ? -1 : selected > k ? selected - 1 : selected);
                    break;
                }
            }
        }
        SelectedMarker(module, plan);
    }

    /// <summary>
    /// The plan's selected marker: kind, place, yaw; a key spot's height (with
    /// a button that lays it on the prop under it) and host kit; a Relay
    /// entry's tag. Turn 90° and Remove.
    /// </summary>
    public static void SelectedMarker(FrontRoomsRoomModule module, FrontRoomsModulePlanView plan)
    {
        var m = module.data;
        var selected = plan.SelectedMarker;
        if (selected < 0 || selected >= m.markers.Length) return;
        var mk = m.markers[selected];
        var key = mk.kind == ModuleMarkerKind.KeySpot;
        using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
        {
            EditorGUI.BeginChangeCheck();
            var kind = (ModuleMarkerKind)EditorGUILayout.EnumPopup(new GUIContent("Kind", "Key spot: where the zone key lies. Relay entry: where the Relay may appear."), mk.kind);
            var x = EditorGUILayout.Slider("X (m from west wall line)", mk.x, 0f, m.WidthMetres);
            var z = EditorGUILayout.Slider("Z (m from south wall line)", mk.z, 0f, m.DepthMetres);
            var y = key ? EditorGUILayout.Slider(new GUIContent("Height above floor", "A key on a desk, a cabinet; 0 on the floor"), mk.y, 0f, MapGrid.CeilingHeight(m.height)) : mk.y;
            var yaw = EditorGUILayout.Slider(new GUIContent("Yaw (0 = north)", key ? "How the key lies" : "The way the Relay faces when it appears"), mk.yaw, 0f, 359f);
            var tag = mk.tag ?? "";
            var host = mk.host ?? "";
            if (key)
            {
                // A host not in the list keeps its own entry, so editing other fields never swaps it.
                var names = FrontRoomsModuleEditing.Kits();
                var known = System.Array.IndexOf(names, host);
                var missing = !string.IsNullOrEmpty(host) && known < 0;
                var options = new[] { "(default)" }.Concat(missing ? new[] { "(missing) " + host } : new string[0]).Concat(names).ToArray();
                var index = string.IsNullOrEmpty(host) ? 0 : missing ? 1 : known + 1;
                var picked = EditorGUILayout.Popup(new GUIContent("Host", "The kit the key hangs on or lies in; (default): the key as it is"), index, options);
                if (picked != index) host = picked == 0 ? "" : options[picked];
            }
            else
            {
                // Written as it is typed, to the marker the field shows; the preview rebuilds once the typing is done (Edited, Release).
                tag = EditorGUILayout.TextField(new GUIContent("Tag", "What the Relay comes out of (\"vent\", \"doorway\", anything): the sound hears it with the arrival. Empty for none."), tag);
            }
            if (EditorGUI.EndChangeCheck())
            {
                FrontRoomsModuleEditing.Record(module, "Edit marker");
                // Only a field that changed snaps (an untouched slider hands back the stored value).
                float Snapped(float v, float was) => v != was ? FrontRoomsModuleEditing.Snap(v) : was;
                // Kept as typed (a trailing space while typing a second word); the map and the sound take it as it is.
                var edited = new ModuleMarker { kind = kind, x = Snapped(x, mk.x), z = Snapped(z, mk.z), y = Snapped(y, mk.y), yaw = Mathf.Repeat(yaw, 360f), tag = tag, host = host };
                // A Relay entry stands on the floor and hangs on nothing; a key spot has no tag.
                if (kind == ModuleMarkerKind.RelayEntry) { edited.y = 0f; edited.host = ""; }
                else edited.tag = "";
                m.markers[selected] = edited;
                Edited(module);
            }
            if (!key)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    EditorGUILayout.PrefixLabel(" ");
                    foreach (var preset in TagPresets)
                        if (GUILayout.Toggle(mk.tag == preset, preset, EditorStyles.miniButton) && mk.tag != preset)
                        {
                            // Out of the tag field first, so its text cannot write over the preset later.
                            GUIUtility.keyboardControl = 0;
                            var q = mk;
                            q.tag = preset;
                            FrontRoomsModuleEditing.SetMarker(module, selected, q, "Marker tag");
                        }
                }
            }
            else
            {
                var top = FrontRoomsModuleEditing.TopUnder(m, new Vector2(mk.x, mk.z));
                using (new EditorGUILayout.HorizontalScope())
                {
                    EditorGUILayout.PrefixLabel(" ");
                    if (GUILayout.Button(new GUIContent(top != null ? "On the prop under it (" + top.Value.ToString("0.00") + " m)" : "On the floor",
                        "Lay the key on the top of the prop under it (its top surface, or the top of its footprint box), or on the floor if there is none")))
                    {
                        var q = mk;
                        q.y = top ?? 0f;
                        FrontRoomsModuleEditing.SetMarker(module, selected, q, "Key on the prop under it");
                    }
                }
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Turn 90°")) FrontRoomsModuleEditing.TurnMarker(module, selected);
                if (GUILayout.Button("Remove")) plan.RemoveSelectedMarker();
            }
        }
    }

    /// <summary>
    /// The run tiers, <paramref name="first"/> to <paramref name="last"/> of
    /// 1..<paramref name="runTiers"/>, at which the generator may use a module:
    /// at run tier t it takes the modules whose tier range holds the level's
    /// module tier + t - 1 (FrontRoomsMapGenerator). False if at none.
    /// </summary>
    public static bool RunTiers(RoomModuleData m, int moduleTier, int runTiers, out int first, out int last)
    {
        int lo = moduleTier, hi = moduleTier + Mathf.Max(1, runTiers) - 1;
        first = Mathf.Max(lo, m.minTier) - lo + 1;
        last = Mathf.Min(hi, m.maxTier) - lo + 1;
        return first <= last;
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
