using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The Level Designer's right-hand panel: the Inspector of a room module.
/// A plan of the room (north up) where clicks edit it, the props and their
/// placement, the module's settings, and its checks. The preview scene on
/// the left (FrontRooms → Level Designer → Open) rebuilds on every edit.
///
/// Plan: click an edge to cycle wall → arch → open; right-click a cell for its
/// lamp; drag a prop to move it (snaps to 0.05 m, hold Ctrl for 0.5 m), R
/// turns the selected prop 90°, Delete removes it. With Custom columns,
/// click an inner corner to add or remove a column (Shift: 0.9 m).
/// </summary>
[CustomEditor(typeof(FrontRoomsRoomModule))]
public sealed class FrontRoomsRoomModuleEditor : Editor
{
    static readonly Color Floor0 = new Color(.42f, .38f, .24f), FloorOffice = new Color(.30f, .34f, .36f);
    static readonly Color WallColor = new Color(.95f, .94f, .90f), ArchColor = new Color(.96f, .85f, .25f), OpenColor = new Color(1f, 1f, 1f, .12f);
    static readonly Color PropColor = new Color(.55f, .75f, .95f, .55f), PropSelected = new Color(1f, .6f, .2f, .75f);
    static readonly Color StripColor = new Color(.3f, .9f, .4f, .12f);
    const float Edge = 7f;

    int selected = -1;
    bool dragging;
    Vector2 dragOffset;
    int addKit;
    bool showGenerator;
    static string[] kits;

    FrontRoomsRoomModule Module => (FrontRoomsRoomModule)target;

    static string[] Kits()
    {
        if (kits == null) kits = FrontRoomsKitLibrary.AllNames().ToArray();
        return kits;
    }

    public override void OnInspectorGUI()
    {
        var module = Module;
        var m = module.data ?? (module.data = new RoomModuleData());
        m.Normalize();

        using (new EditorGUILayout.HorizontalScope())
        {
            if (GUILayout.Button("Open in Level Designer")) FrontRoomsLevelDesigner.Open(module);
            if (GUILayout.Button("Frame preview", GUILayout.Width(110))) FrontRoomsLevelDesigner.FramePreview();
        }
        EditorGUILayout.Space(4);

        // ---------- Room ----------
        EditorGUI.BeginChangeCheck();
        var notes = EditorGUILayout.TextArea(module.notes ?? "", GUILayout.MinHeight(32));
        var width = EditorGUILayout.IntSlider(new GUIContent("Width (cells, X)", "3 m each"), m.width, 1, RoomModuleData.MaxCells);
        var depth = EditorGUILayout.IntSlider(new GUIContent("Depth (cells, Z)", "3 m each"), m.depth, 1, RoomModuleData.MaxCells);
        var theme = (ZoneTheme)EditorGUILayout.EnumPopup(new GUIContent("Theme", "Level 0 paper and carpet, or a Level 4 office (Standard height only)"), m.theme);
        var height = theme == ZoneTheme.Office ? ZoneHeight.Standard : (ZoneHeight)EditorGUILayout.EnumPopup(new GUIContent("Ceiling", "Low 2.4 m, Standard 2.9 m, Tall 5.4 m"), m.height);
        var fill = (ModuleFill)EditorGUILayout.EnumPopup(new GUIContent("Fill", "Auto: as a generated room. Office: the Office kit fills round your props. Pile: a furniture pile."), m.fill);
        var columns = (ModuleColumns)EditorGUILayout.EnumPopup(new GUIContent("Columns", "Auto: the map's 6 m grid rule where the room lands. Custom: click inner corners in the plan."), m.columns);
        if (EditorGUI.EndChangeCheck())
        {
            Record("Edit room module");
            module.notes = notes;
            m.Resize(width, depth);
            m.theme = theme;
            m.height = height;
            m.fill = fill;
            m.columns = columns;
            m.Normalize();
            Changed();
        }

        EditorGUILayout.LabelField(m.width * 3 + " × " + m.depth * 3 + " m · ceiling " + MapGrid.CeilingHeight(m.height).ToString("0.0") + " m · clear floor "
            + ModuleUnits.ClearSpan(m.width).ToString("0.00") + " × " + ModuleUnits.ClearSpan(m.depth).ToString("0.00") + " m", EditorStyles.miniLabel);

        // ---------- Plan ----------
        EditorGUILayout.Space(6);
        EditorGUILayout.LabelField("Plan (north up)", EditorStyles.boldLabel);
        DrawPlan(m);
        EditorGUILayout.LabelField("Click an edge: wall → arch → open.  Right-click a cell: lamp.  Drag props; R turns, Delete removes.", EditorStyles.wordWrappedMiniLabel);

        // ---------- Props ----------
        EditorGUILayout.Space(6);
        EditorGUILayout.LabelField("Props (" + m.props.Length + ")", EditorStyles.boldLabel);
        var names = Kits();
        using (new EditorGUILayout.HorizontalScope())
        {
            addKit = names.Length == 0 ? 0 : EditorGUILayout.Popup(Mathf.Clamp(addKit, 0, names.Length - 1), names);
            using (new EditorGUI.DisabledScope(names.Length == 0))
                if (GUILayout.Button("Add", GUILayout.Width(50)))
                {
                    Record("Add prop");
                    var list = m.props.ToList();
                    list.Add(new ModuleProp { kit = names[addKit], x = m.WidthMetres * .5f, z = m.DepthMetres * .5f });
                    m.props = list.ToArray();
                    selected = m.props.Length - 1;
                    Changed();
                }
        }
        if (selected >= m.props.Length) selected = -1;
        if (selected >= 0) DrawSelectedProp(m, names);

        // ---------- Generator (P3) ----------
        EditorGUILayout.Space(6);
        showGenerator = EditorGUILayout.Foldout(showGenerator, "Where the generator may use it", true);
        if (showGenerator)
        {
            EditorGUI.BeginChangeCheck();
            var weight = EditorGUILayout.FloatField(new GUIContent("Weight", "Relative chance among modules that fit"), m.weight);
            var rotate = EditorGUILayout.Toggle(new GUIContent("May rotate", "The generator may turn it by quarter turns"), m.allowRotate);
            var minTier = EditorGUILayout.IntField("From tier", m.minTier);
            var maxTier = EditorGUILayout.IntField("To tier", m.maxTier);
            if (EditorGUI.EndChangeCheck())
            {
                Record("Edit room module");
                m.weight = weight;
                m.allowRotate = rotate;
                m.minTier = minTier;
                m.maxTier = maxTier;
                m.Normalize();
                Changed();
            }
        }

        // ---------- Checks ----------
        EditorGUILayout.Space(6);
        var errors = new List<string>();
        var warnings = new List<string>();
        module.Validate(errors, warnings);
        if (errors.Count == 0 && warnings.Count == 0) EditorGUILayout.HelpBox("Ready: no problems found.", MessageType.Info);
        foreach (var e in errors) EditorGUILayout.HelpBox(e, MessageType.Error);
        foreach (var w in warnings) EditorGUILayout.HelpBox(w, MessageType.Warning);
    }

    void DrawSelectedProp(RoomModuleData m, string[] names)
    {
        var p = m.props[selected];
        using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
        {
            EditorGUI.BeginChangeCheck();
            var index = System.Array.IndexOf(names, p.kit);
            var newIndex = EditorGUILayout.Popup("Kit", Mathf.Max(0, index), names);
            var x = EditorGUILayout.Slider("X (m from west wall line)", p.x, 0f, m.WidthMetres);
            var z = EditorGUILayout.Slider("Z (m from south wall line)", p.z, 0f, m.DepthMetres);
            var y = EditorGUILayout.Slider(new GUIContent("Height above floor", "For wall pieces: a clock, an interior window"), p.y, 0f, MapGrid.CeilingHeight(m.height));
            var yaw = EditorGUILayout.Slider("Yaw (0 = front faces north)", p.yaw, 0f, 359f);
            var noCollider = EditorGUILayout.Toggle(new GUIContent("No collider", "Desk-top clutter: the player and the Relay pass through it"), p.noCollider);
            if (EditorGUI.EndChangeCheck())
            {
                Record("Edit prop");
                m.props[selected] = new ModuleProp { kit = names.Length > 0 ? names[newIndex] : p.kit, x = Snap(x, .05f), z = Snap(z, .05f), y = Snap(y, .05f), yaw = Mathf.Repeat(yaw, 360f), noCollider = noCollider };
                Changed();
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Turn 90°")) TurnSelected(m);
                if (GUILayout.Button("Duplicate"))
                {
                    Record("Duplicate prop");
                    var list = m.props.ToList();
                    var copy = m.props[selected];
                    copy.x = Mathf.Min(copy.x + .5f, m.WidthMetres);
                    list.Add(copy);
                    m.props = list.ToArray();
                    selected = m.props.Length - 1;
                    Changed();
                }
                if (GUILayout.Button("Remove")) RemoveSelected(m);
            }
        }
    }

    // ---------- Plan view ----------

    void DrawPlan(RoomModuleData m)
    {
        var available = EditorGUIUtility.currentViewWidth - 40f;
        var cell = Mathf.Clamp(Mathf.Floor(available / Mathf.Max(m.width, m.depth)), 24f, 64f);
        var size = new Vector2(m.width * cell, m.depth * cell);
        var area = GUILayoutUtility.GetRect(size.x + 2 * Edge, size.y + 2 * Edge, GUILayout.ExpandWidth(false));
        var origin = new Vector2(area.x + Edge, area.y + Edge);
        var metre = cell / MapGrid.CellSize;
        Rect CellRect(int i, int j) => new Rect(origin.x + i * cell, origin.y + (m.depth - 1 - j) * cell, cell, cell);
        Vector2 ToPlan(float x, float z) => new Vector2(origin.x + x * metre, origin.y + size.y - z * metre);
        Vector2 ToModule(Vector2 p) => new Vector2((p.x - origin.x) / metre, (origin.y + size.y - p.y) / metre);

        var e = Event.current;
        if (e.type == EventType.Repaint)
        {
            for (var j = 0; j < m.depth; j++)
            for (var i = 0; i < m.width; i++)
            {
                var r = CellRect(i, j);
                EditorGUI.DrawRect(r, m.theme == ZoneTheme.Office ? FloorOffice : Floor0);
                DrawLamp(r, m.LampAt(i, j));
            }
            foreach (var s in m.EntryStrips())
            {
                var a = ToPlan(s[0], s[3]);
                var b = ToPlan(s[2], s[1]);
                EditorGUI.DrawRect(new Rect(a.x, a.y, b.x - a.x, b.y - a.y), StripColor);
            }
        }

        // Edges: each cell's east and north, plus the south row and west column.
        for (var j = 0; j < m.depth; j++)
        for (var i = 0; i < m.width; i++)
        {
            var r = CellRect(i, j);
            EdgeControl(m, new Rect(r.xMax - Edge * .5f, r.y + 3f, Edge, r.height - 6f), i, j, 1, 0, true);
            EdgeControl(m, new Rect(r.x + 3f, r.y - Edge * .5f, r.width - 6f, Edge), i, j, 0, 1, false);
            if (i == 0) EdgeControl(m, new Rect(r.x - Edge * .5f, r.y + 3f, Edge, r.height - 6f), i, j, -1, 0, true);
            if (j == 0) EdgeControl(m, new Rect(r.x + 3f, r.yMax - Edge * .5f, r.width - 6f, Edge), i, j, 0, -1, false);
        }

        // Columns.
        for (var j = 1; j < m.depth; j++)
        for (var i = 1; i < m.width; i++)
        {
            var c = ToPlan(i * MapGrid.CellSize, j * MapGrid.CellSize);
            var custom = m.customColumns.FirstOrDefault(k => k.x == i && k.y == j);
            var has = m.columns == ModuleColumns.Custom && m.customColumns.Any(k => k.x == i && k.y == j);
            var auto = m.columns == ModuleColumns.Auto && AutoColumnPossible(m, i, j);
            var w = (has && custom.large) || (auto && (m.theme == ZoneTheme.Office || m.height == ZoneHeight.Tall)) ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall;
            var rect = new Rect(c.x - w * metre * .5f, c.y - w * metre * .5f, w * metre, w * metre);
            if (e.type == EventType.Repaint && (has || auto)) EditorGUI.DrawRect(rect, has ? WallColor : new Color(1f, 1f, 1f, .35f));
            if (m.columns == ModuleColumns.Custom && e.type == EventType.MouseDown && e.button == 0 && new Rect(c.x - 6f, c.y - 6f, 12f, 12f).Contains(e.mousePosition))
            {
                Record("Toggle column");
                var list = m.customColumns.ToList();
                var k = list.FindIndex(q => q.x == i && q.y == j);
                if (k >= 0) list.RemoveAt(k); else list.Add(new ModuleColumn { x = i, y = j, large = e.shift });
                m.customColumns = list.ToArray();
                Changed();
                e.Use();
            }
        }

        // Props: footprints, selection and dragging.
        for (var k = 0; k < m.props.Length; k++)
        {
            var p = m.props[k];
            var f = FrontRoomsMapWorld.KitFootprint(p.kit) ?? new[] { -.25f, -.25f, .25f, .25f, .5f };
            var corners = Corners(p, f).Select(q => (Vector3)ToPlan(q.x, q.y)).ToArray();
            if (e.type == EventType.Repaint)
            {
                Handles.color = k == selected ? PropSelected : PropColor;
                Handles.DrawAAConvexPolygon(corners);
                Handles.color = Color.black;
                Handles.DrawAAPolyLine(2f, corners[0], corners[1], corners[2], corners[3], corners[0]);
                // Front edge marker: the +Z side of the footprint.
                var front = Corners(p, new[] { f[0], f[3] - .02f, f[2], f[3], f[4] }).Select(q => (Vector3)ToPlan(q.x, q.y)).ToArray();
                Handles.color = new Color(.1f, .1f, .1f, .9f);
                Handles.DrawAAConvexPolygon(front);
                var label = ToPlan(p.x, p.z);
                GUI.Label(new Rect(label.x - 40f, label.y - 8f, 80f, 16f), Short(p.kit), CenteredMini);
            }
            if (e.type == EventType.MouseDown && e.button == 0 && Inside(corners, e.mousePosition))
            {
                selected = k;
                dragging = true;
                dragOffset = ToModule(e.mousePosition) - new Vector2(p.x, p.z);
                GUIUtility.hotControl = GUIUtility.GetControlID(FocusType.Passive);
                e.Use();
                Repaint();
            }
        }
        if (dragging && selected >= 0 && e.type == EventType.MouseDrag)
        {
            var target = ToModule(e.mousePosition) - dragOffset;
            var step = e.control || e.command ? .5f : .05f;
            Record("Move prop");
            var p = m.props[selected];
            p.x = Mathf.Clamp(Snap(target.x, step), 0f, m.WidthMetres);
            p.z = Mathf.Clamp(Snap(target.y, step), 0f, m.DepthMetres);
            m.props[selected] = p;
            Changed();
            e.Use();
        }
        if (dragging && e.rawType == EventType.MouseUp)
        {
            dragging = false;
            GUIUtility.hotControl = 0;
            e.Use();
        }
        if (selected >= 0 && e.type == EventType.KeyDown)
        {
            if (e.keyCode == KeyCode.R) { TurnSelected(m); e.Use(); }
            else if (e.keyCode == KeyCode.Delete || e.keyCode == KeyCode.Backspace) { RemoveSelected(m); e.Use(); }
        }

        // Right-click a cell: its lamp.
        if (e.type == EventType.ContextClick || (e.type == EventType.MouseDown && e.button == 1))
            for (var j = 0; j < m.depth; j++)
            for (var i = 0; i < m.width; i++)
            {
                if (!CellRect(i, j).Contains(e.mousePosition)) continue;
                var ci = i;
                var cj = j;
                var menu = new GenericMenu();
                foreach (ModuleLamp lamp in System.Enum.GetValues(typeof(ModuleLamp)))
                {
                    var value = lamp;
                    menu.AddItem(new GUIContent("Lamp/" + value), m.LampAt(ci, cj) == value, () =>
                    {
                        Record("Set lamp");
                        m.lamps[ci + cj * m.width] = value;
                        Changed();
                    });
                }
                menu.ShowAsContext();
                e.Use();
            }
    }

    static GUIStyle centeredMini;
    static GUIStyle CenteredMini => centeredMini ?? (centeredMini = new GUIStyle(EditorStyles.miniLabel) { alignment = TextAnchor.MiddleCenter, normal = { textColor = Color.white } });

    void EdgeControl(RoomModuleData m, Rect rect, int i, int j, int dx, int dy, bool vertical)
    {
        var kind = m.EdgeAt(i, j, dx, dy);
        var perimeter = (dx == 1 && i == m.width - 1) || (dx == -1 && i == 0) || (dy == 1 && j == m.depth - 1) || (dy == -1 && j == 0);
        var e = Event.current;
        if (e.type == EventType.Repaint)
        {
            var thick = perimeter ? 4f : 3f;
            var line = vertical ? new Rect(rect.center.x - thick * .5f, rect.y, thick, rect.height) : new Rect(rect.x, rect.center.y - thick * .5f, rect.width, thick);
            if (kind == ModuleEdge.Wall) EditorGUI.DrawRect(line, WallColor);
            else if (kind == ModuleEdge.Arch)
            {
                // A doorway: wall stubs either side, gap in the middle.
                var a = line; var b = line;
                if (vertical) { a.height = b.height = line.height * .25f; b.y = line.yMax - b.height; }
                else { a.width = b.width = line.width * .25f; b.x = line.xMax - b.width; }
                EditorGUI.DrawRect(a, ArchColor);
                EditorGUI.DrawRect(b, ArchColor);
            }
            else EditorGUI.DrawRect(line, OpenColor);
            EditorGUIUtility.AddCursorRect(rect, MouseCursor.Link);
        }
        if (e.type == EventType.MouseDown && e.button == 0 && rect.Contains(e.mousePosition))
        {
            Record("Edit edge");
            m.SetEdge(i, j, dx, dy, kind == ModuleEdge.Wall ? ModuleEdge.Arch : kind == ModuleEdge.Arch ? ModuleEdge.Open : ModuleEdge.Wall);
            Changed();
            e.Use();
        }
    }

    static void DrawLamp(Rect cell, ModuleLamp lamp)
    {
        // The troffer sits in X [1.2, 1.8], Z [1.2, 2.4] of the cell (north up in the plan).
        var s = cell.width / MapGrid.CellSize;
        var r = new Rect(cell.x + 1.2f * s, cell.y + (MapGrid.CellSize - 2.4f) * s, .6f * s, 1.2f * s);
        Color c;
        switch (lamp)
        {
            case ModuleLamp.Off: return;
            case ModuleLamp.Dead: c = new Color(.25f, .25f, .25f); break;
            case ModuleLamp.Failing: c = new Color(.9f, .5f, .2f); break;
            case ModuleLamp.Stutter: c = new Color(.95f, .85f, .4f); break;
            case ModuleLamp.Dim: c = new Color(.6f, .58f, .45f); break;
            case ModuleLamp.Steady: c = Color.white; break;
            default: c = new Color(1f, 1f, 1f, .45f); break;
        }
        EditorGUI.DrawRect(r, c);
    }

    /// <summary>Where the map's own column rule could put a column with the module at its preview spot (it also rolls per room).</summary>
    static bool AutoColumnPossible(RoomModuleData m, int i, int j)
    {
        if (m.width < 3 || m.depth < 3 || m.height == ZoneHeight.Low) return false;
        FrontRoomsModulePreview.Placement(m, out var x0, out var y0);
        return FrontRoomsMapGenerator.OnColumnGrid(new GridCoord(x0 + i, y0 + j));
    }

    static Vector2[] Corners(ModuleProp p, float[] f)
    {
        var rad = p.yaw * Mathf.Deg2Rad;
        float c = Mathf.Cos(rad), s = Mathf.Sin(rad);
        Vector2 W(float x, float z) => new Vector2(p.x + x * c + z * s, p.z - x * s + z * c);
        return new[] { W(f[0], f[1]), W(f[2], f[1]), W(f[2], f[3]), W(f[0], f[3]) };
    }

    static bool Inside(Vector3[] poly, Vector2 p)
    {
        var inside = false;
        for (int a = 0, b = poly.Length - 1; a < poly.Length; b = a++)
            if ((poly[a].y > p.y) != (poly[b].y > p.y) && p.x < (poly[b].x - poly[a].x) * (p.y - poly[a].y) / (poly[b].y - poly[a].y) + poly[a].x)
                inside = !inside;
        return inside;
    }

    static string Short(string kit) => string.IsNullOrEmpty(kit) ? "?" : kit.StartsWith("Kit_") ? kit.Substring(4) : kit;

    static float Snap(float v, float step) => Mathf.Round(v / step) * step;

    void TurnSelected(RoomModuleData m)
    {
        if (selected < 0) return;
        Record("Turn prop");
        var p = m.props[selected];
        p.yaw = Mathf.Repeat(p.yaw + 90f, 360f);
        m.props[selected] = p;
        Changed();
    }

    void RemoveSelected(RoomModuleData m)
    {
        if (selected < 0) return;
        Record("Remove prop");
        var list = m.props.ToList();
        list.RemoveAt(selected);
        m.props = list.ToArray();
        selected = -1;
        Changed();
    }

    void Record(string label) => Undo.RecordObject(Module, label);

    void Changed()
    {
        EditorUtility.SetDirty(Module);
        FrontRoomsRoomModule.NotifyChanged(Module);
        Repaint();
    }
}
