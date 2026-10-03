using System;
using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// A room module's plan (north up), where clicks edit the room. The module's
/// Inspector and the Level Designer window each keep one, with its own
/// selection and drag state, and behave the same.
///
/// Click a prop to select it (again: the one under it), drag to move (0.05 m
/// snap, Ctrl 0.5 m; the preview rebuilds when you let go), R turns it 90°,
/// Delete removes it, Esc deselects. Click an edge to cycle wall → arch →
/// open. Right-click a cell for its lamp. With Custom columns, click an inner
/// corner (Shift: 0.9 m). With a palette kit armed, a click places it (Shift
/// keeps it armed); a kit dragged from the palette lands where it is dropped.
/// </summary>
public sealed class FrontRoomsModulePlanView
{
    static readonly Color Floor0 = new Color(.42f, .38f, .24f), FloorOffice = new Color(.30f, .34f, .36f);
    static readonly Color WallColor = new Color(.95f, .94f, .90f), ArchColor = new Color(.96f, .85f, .25f), OpenColor = new Color(1f, 1f, 1f, .12f);
    static readonly Color PropColor = new Color(.55f, .75f, .95f, .55f), PropSelected = new Color(1f, .6f, .2f, .75f), GhostColor = new Color(.4f, 1f, .5f, .45f);
    static readonly Color StripColor = new Color(.3f, .9f, .4f, .12f);
    const float Edge = 7f;
    static GUIStyle centeredMini;

    readonly Action repaint;
    FrontRoomsRoomModule module;
    int selected = -1;
    bool dragging;
    Vector2 dragOffset;
    // The armed or dragged kit and the module point under the mouse, drawn where it would land.
    (string kit, Vector2 at)? ghost;

    /// <param name="repaint">Repaints the panel that draws this plan.</param>
    public FrontRoomsModulePlanView(Action repaint) => this.repaint = repaint;

    /// <summary>Raised when the designer picks a prop here or in the prop fields (-1: none). The window selects it in the Scene too.</summary>
    public event Action<int> SelectionChanged;

    /// <summary>The kit a click in the plan places, or null. The window's palette arms it.</summary>
    public string ArmedKit { get; set; }

    /// <summary>The selected prop's index, or -1.</summary>
    public int Selected => selected;

    static GUIStyle CenteredMini => centeredMini ?? (centeredMini = new GUIStyle(EditorStyles.miniLabel) { alignment = TextAnchor.MiddleCenter, normal = { textColor = Color.white } });

    /// <summary>Select a prop (-1: none). <paramref name="notify"/> is false when the selection comes from the Scene view.</summary>
    public void Select(int index, bool notify = true)
    {
        if (index == selected) return;
        selected = index;
        if (notify) SelectionChanged?.Invoke(index);
        repaint();
    }

    /// <summary>Call when the panel closes: a drag cut short still reaches the preview.</summary>
    public void EndDrag()
    {
        if (dragging && module != null) FrontRoomsRoomModule.NotifyChanged(module);
        dragging = false;
    }

    /// <summary>Draw the plan, as large as fits <paramref name="availableWidth"/>, and handle its events.</summary>
    public void Draw(FrontRoomsRoomModule target, float availableWidth)
    {
        module = target;
        var m = module.data;
        // An undo can take the selected prop away.
        if (selected >= m.props.Length) selected = -1;
        var cell = Mathf.Clamp(Mathf.Floor(availableWidth / Mathf.Max(m.width, m.depth)), 24f, 64f);
        var size = new Vector2(m.width * cell, m.depth * cell);
        var area = GUILayoutUtility.GetRect(size.x + 2 * Edge, size.y + 2 * Edge, GUILayout.ExpandWidth(false));
        var origin = new Vector2(area.x + Edge, area.y + Edge);
        var metre = cell / MapGrid.CellSize;
        Rect CellRect(int i, int j) => new Rect(origin.x + i * cell, origin.y + (m.depth - 1 - j) * cell, cell, cell);
        Vector2 ToPlan(float x, float z) => new Vector2(origin.x + x * metre, origin.y + size.y - z * metre);
        Vector2 ToModule(Vector2 p) => new Vector2((p.x - origin.x) / metre, (origin.y + size.y - p.y) / metre);

        // Shapes for drawing and hit testing.
        var polys = new Vector3[m.props.Length][];
        var fronts = new Vector3[m.props.Length][];
        var band = Mathf.Max(3f / metre, .08f);
        for (var k = 0; k < m.props.Length; k++) Shape(m.props[k], band, ToPlan, out polys[k], out fronts[k]);
        var edges = new List<(Rect rect, int i, int j, int dx, int dy, bool vertical)>();
        for (var j = 0; j < m.depth; j++)
        for (var i = 0; i < m.width; i++)
        {
            var r = CellRect(i, j);
            edges.Add((new Rect(r.xMax - Edge * .5f, r.y + 3f, Edge, r.height - 6f), i, j, 1, 0, true));
            edges.Add((new Rect(r.x + 3f, r.y - Edge * .5f, r.width - 6f, Edge), i, j, 0, 1, false));
            if (i == 0) edges.Add((new Rect(r.x - Edge * .5f, r.y + 3f, Edge, r.height - 6f), i, j, -1, 0, true));
            if (j == 0) edges.Add((new Rect(r.x + 3f, r.yMax - Edge * .5f, r.width - 6f, Edge), i, j, 0, -1, false));
        }

        var e = Event.current;
        var inside = area.Contains(e.mousePosition);

        // A kit dragged from the palette: show where it lands, add it on drop.
        if (e.type == EventType.DragUpdated || e.type == EventType.DragPerform)
        {
            var dragged = DragAndDrop.GetGenericData(FrontRoomsModuleEditing.DragKey) as string;
            if (dragged != null && inside)
            {
                DragAndDrop.visualMode = DragAndDropVisualMode.Copy;
                ghost = (dragged, ToModule(e.mousePosition));
                if (e.type == EventType.DragPerform)
                {
                    DragAndDrop.AcceptDrag();
                    Place(dragged, ToModule(e.mousePosition));
                    ghost = null;
                }
                e.Use();
                repaint();
            }
            else if (ghost != null)
            {
                ghost = null;
                repaint();
            }
        }
        if ((e.type == EventType.DragExited || e.type == EventType.MouseLeaveWindow) && ghost != null)
        {
            ghost = null;
            repaint();
        }
        if (ArmedKit != null && (e.type == EventType.MouseMove || e.type == EventType.MouseDrag))
        {
            var now = inside ? (ArmedKit, ToModule(e.mousePosition)) : ((string, Vector2)?)null;
            if (!Equals(now, ghost))
            {
                ghost = now;
                repaint();
            }
        }

        // Left click: an armed kit is placed; else props first (topmost; again cycles to the one under it), then columns, then edges, else deselect.
        if (e.type == EventType.MouseDown && e.button == 0 && inside)
        {
            GUIUtility.keyboardControl = 0;
            var hits = new List<int>();
            for (var k = m.props.Length - 1; k >= 0; k--) if (Inside(polys[k], e.mousePosition)) hits.Add(k);
            var columnHit = ColumnAt(m, e.mousePosition, ToPlan);
            var edgeHit = edges.FindIndex(q => q.rect.Contains(e.mousePosition));
            if (ArmedKit != null)
            {
                Place(ArmedKit, ToModule(e.mousePosition));
                if (!e.shift) Disarm();
            }
            else if (hits.Count > 0)
            {
                var at = hits.IndexOf(selected);
                Select(at >= 0 ? hits[(at + 1) % hits.Count] : hits[0]);
                dragging = true;
                dragOffset = ToModule(e.mousePosition) - new Vector2(m.props[selected].x, m.props[selected].z);
                Undo.IncrementCurrentGroup();
                FrontRoomsModuleEditing.Record(module, "Move prop");
            }
            else if (m.columns == ModuleColumns.Custom && columnHit.x > 0)
            {
                FrontRoomsModuleEditing.Record(module, "Toggle column");
                var list = m.customColumns.ToList();
                var k = list.FindIndex(q => q.x == columnHit.x && q.y == columnHit.y);
                if (k >= 0) list.RemoveAt(k); else list.Add(new ModuleColumn { x = columnHit.x, y = columnHit.y, large = e.shift });
                m.customColumns = list.ToArray();
                Changed();
            }
            else if (edgeHit >= 0)
            {
                var q = edges[edgeHit];
                var kind = m.EdgeAt(q.i, q.j, q.dx, q.dy);
                FrontRoomsModuleEditing.Record(module, "Edit edge");
                m.SetEdge(q.i, q.j, q.dx, q.dy, kind == ModuleEdge.Wall ? ModuleEdge.Arch : kind == ModuleEdge.Arch ? ModuleEdge.Open : ModuleEdge.Wall);
                Changed();
            }
            else Select(-1);
            e.Use();
            repaint();
        }

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
            foreach (var q in edges) DrawEdge(m, q.rect, q.i, q.j, q.dx, q.dy, q.vertical);
            var turns = PreviewTurns();
            for (var j = 1; j < m.depth; j++)
            for (var i = 1; i < m.width; i++)
            {
                var custom = m.customColumns.FirstOrDefault(k => k.x == i && k.y == j);
                var has = m.columns == ModuleColumns.Custom && m.customColumns.Any(k => k.x == i && k.y == j);
                var auto = m.columns == ModuleColumns.Auto && AutoColumnPossible(m, i, j, turns);
                if (!has && !auto) continue;
                var w = (has && custom.large) || (auto && (m.theme == ZoneTheme.Office || m.height == ZoneHeight.Tall)) ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall;
                var c = ToPlan(i * MapGrid.CellSize, j * MapGrid.CellSize);
                EditorGUI.DrawRect(new Rect(c.x - w * metre * .5f, c.y - w * metre * .5f, w * metre, w * metre), has ? WallColor : new Color(1f, 1f, 1f, .35f));
            }
            for (var k = 0; k < m.props.Length; k++)
            {
                DrawProp(polys[k], fronts[k], k == selected ? PropSelected : PropColor);
                var label = ToPlan(m.props[k].x, m.props[k].z);
                GUI.Label(new Rect(label.x - 40f, label.y - 8f, 80f, 16f), FrontRoomsModuleEditing.Short(m.props[k].kit), CenteredMini);
            }
            // Where the armed or dragged kit would go, wall units already against their wall.
            if (ghost != null)
            {
                Shape(FrontRoomsModuleEditing.NewProp(m, ghost.Value.kit, ghost.Value.at), band, ToPlan, out var poly, out var front);
                DrawProp(poly, front, GhostColor);
            }
            foreach (var q in edges) EditorGUIUtility.AddCursorRect(q.rect, MouseCursor.Link);
            if (ArmedKit != null) EditorGUIUtility.AddCursorRect(area, MouseCursor.ArrowPlus);
        }

        if (dragging && selected >= 0 && e.type == EventType.MouseDrag)
        {
            // Moves show in the plan at once; the preview rebuilds when the drag ends.
            var to = ToModule(e.mousePosition) - dragOffset;
            var step = e.control || e.command ? .5f : FrontRoomsModuleEditing.Grid;
            var p = m.props[selected];
            p.x = Mathf.Clamp(FrontRoomsModuleEditing.Snap(to.x, step), 0f, m.WidthMetres);
            p.z = Mathf.Clamp(FrontRoomsModuleEditing.Snap(to.y, step), 0f, m.DepthMetres);
            m.props[selected] = p;
            EditorUtility.SetDirty(module);
            e.Use();
            repaint();
        }
        if (dragging && e.rawType == EventType.MouseUp)
        {
            dragging = false;
            Changed();
            e.Use();
        }
        // Keys only when no field is being typed in.
        if ((selected >= 0 || ArmedKit != null) && e.type == EventType.KeyDown && GUIUtility.keyboardControl == 0 && !EditorGUIUtility.editingTextField && !(e.control || e.command || e.alt))
        {
            if (e.keyCode == KeyCode.Escape)
            {
                if (ArmedKit != null) Disarm(); else Select(-1);
                e.Use();
                repaint();
            }
            else if (selected >= 0 && e.keyCode == KeyCode.R) { FrontRoomsModuleEditing.TurnProp(module, selected); e.Use(); repaint(); }
            else if (selected >= 0 && (e.keyCode == KeyCode.Delete || e.keyCode == KeyCode.Backspace)) { RemoveSelected(); e.Use(); }
        }
        // Edit → Delete (⌘⌫, or Delete where the shortcut takes the key) arrives as a command.
        if (selected >= 0 && (e.type == EventType.ValidateCommand || e.type == EventType.ExecuteCommand) && (e.commandName == "SoftDelete" || e.commandName == "Delete")
            && GUIUtility.keyboardControl == 0 && !EditorGUIUtility.editingTextField)
        {
            if (e.type == EventType.ExecuteCommand) RemoveSelected();
            e.Use();
        }

        // Right-click a cell: its lamp.
        if (e.type == EventType.ContextClick || (e.type == EventType.MouseDown && e.button == 1))
            for (var j = 0; j < m.depth; j++)
            for (var i = 0; i < m.width; i++)
            {
                if (!CellRect(i, j).Contains(e.mousePosition)) continue;
                var ci = i;
                var cj = j;
                var lampModule = module;
                var menu = new GenericMenu();
                foreach (ModuleLamp lamp in Enum.GetValues(typeof(ModuleLamp)))
                {
                    var value = lamp;
                    menu.AddItem(new GUIContent("Lamp/" + value), m.LampAt(ci, cj) == value, () =>
                    {
                        FrontRoomsModuleEditing.Record(lampModule, "Set lamp");
                        lampModule.data.lamps[ci + cj * lampModule.data.width] = value;
                        FrontRoomsModuleEditing.Changed(lampModule);
                        repaint();
                    });
                }
                menu.ShowAsContext();
                e.Use();
            }
    }

    /// <summary>Remove the selected prop (Delete in the plan, Remove in the prop fields).</summary>
    public void RemoveSelected()
    {
        if (selected < 0) return;
        FrontRoomsModuleEditing.RemoveProps(module, new[] { selected });
        Select(-1);
    }

    void Place(string kit, Vector2 at) => Select(FrontRoomsModuleEditing.AddKit(module, kit, at));

    void Disarm()
    {
        ArmedKit = null;
        ghost = null;
    }

    void Changed()
    {
        FrontRoomsModuleEditing.Changed(module);
        repaint();
    }

    /// <summary>A prop's footprint and its front band (the +Z side) in plan pixels.</summary>
    static void Shape(ModuleProp p, float band, Func<float, float, Vector2> toPlan, out Vector3[] poly, out Vector3[] front)
    {
        var f = FrontRoomsMapWorld.KitFootprint(p.kit) ?? new[] { -.25f, -.25f, .25f, .25f, .5f };
        poly = Corners(p, f).Select(q => (Vector3)toPlan(q.x, q.y)).ToArray();
        front = Corners(p, new[] { f[0], f[3] - band, f[2], f[3], f[4] }).Select(q => (Vector3)toPlan(q.x, q.y)).ToArray();
    }

    static void DrawProp(Vector3[] poly, Vector3[] front, Color fill)
    {
        Handles.color = fill;
        Handles.DrawAAConvexPolygon(poly);
        // The front: a dark band along the +Z side of the footprint.
        Handles.color = new Color(.08f, .08f, .08f, .95f);
        Handles.DrawAAConvexPolygon(front);
        Handles.color = Color.black;
        Handles.DrawAAPolyLine(1.5f, poly[0], poly[1], poly[2], poly[3], poly[0]);
    }

    /// <summary>The inner corner under the mouse, or (0, 0).</summary>
    static Vector2Int ColumnAt(RoomModuleData m, Vector2 mouse, Func<float, float, Vector2> toPlan)
    {
        for (var j = 1; j < m.depth; j++)
        for (var i = 1; i < m.width; i++)
        {
            var c = toPlan(i * MapGrid.CellSize, j * MapGrid.CellSize);
            if (new Rect(c.x - 7f, c.y - 7f, 14f, 14f).Contains(mouse)) return new Vector2Int(i, j);
        }
        return Vector2Int.zero;
    }

    static void DrawEdge(RoomModuleData m, Rect rect, int i, int j, int dx, int dy, bool vertical)
    {
        var kind = m.EdgeAt(i, j, dx, dy);
        var perimeter = (dx == 1 && i == m.width - 1) || (dx == -1 && i == 0) || (dy == 1 && j == m.depth - 1) || (dy == -1 && j == 0);
        var thick = perimeter ? 4f : 3f;
        var line = vertical ? new Rect(rect.center.x - thick * .5f, rect.y, thick, rect.height) : new Rect(rect.x, rect.center.y - thick * .5f, rect.width, thick);
        if (kind == ModuleEdge.Wall) EditorGUI.DrawRect(line, WallColor);
        else if (kind == ModuleEdge.Arch)
        {
            // A doorway: wall stubs either side, the gap in the middle.
            var a = line;
            var b = line;
            if (vertical) { a.height = b.height = line.height * .25f; b.y = line.yMax - b.height; }
            else { a.width = b.width = line.width * .25f; b.x = line.xMax - b.width; }
            EditorGUI.DrawRect(a, ArchColor);
            EditorGUI.DrawRect(b, ArchColor);
        }
        else EditorGUI.DrawRect(line, OpenColor);
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

    /// <summary>The open preview's quarter turns (0 without one): auto columns are shown as it places the room.</summary>
    static int PreviewTurns()
    {
        var preview = UnityEngine.Object.FindFirstObjectByType<FrontRoomsModulePreview>();
        return preview != null ? ((preview.rotation % 4) + 4) % 4 : 0;
    }

    /// <summary>
    /// Where the map's own column rule could put a column (it also rolls per
    /// room): the corner on the 6 m grid with the module turned and placed
    /// as the open preview shows it.
    /// </summary>
    static bool AutoColumnPossible(RoomModuleData m, int i, int j, int turns)
    {
        if (m.width < 3 || m.depth < 3 || m.height == ZoneHeight.Low) return false;
        int w = m.width, d = m.depth, ci = i, cj = j;
        for (var t = 0; t < turns; t++)
        {
            // Clockwise: corner (x, y) of a w x d room goes to (y, w - x) of the d x w room.
            var x = ci;
            ci = cj;
            cj = w - x;
            var swap = w;
            w = d;
            d = swap;
        }
        int x0 = (MapGrid.ChunkCells - w) / 2, y0 = (MapGrid.ChunkCells - d) / 2;
        return FrontRoomsMapGenerator.OnColumnGrid(new GridCoord(x0 + ci, y0 + cj));
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
}
