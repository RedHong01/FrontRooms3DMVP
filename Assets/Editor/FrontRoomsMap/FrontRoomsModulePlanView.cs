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
/// Delete removes it, Esc deselects. Gameplay markers (K key spot, R Relay
/// entry) are picked before props and move, turn and go the same way; their
/// selection is the plan's own (props are also selected in the Scene view,
/// markers are not), and a prop and a marker are never selected together.
/// Click an edge to cycle wall → arch → open. Right-click a cell for its lamp,
/// or a key spot or Relay entry there. With Custom columns, click an inner
/// corner (Shift: 0.9 m). With a palette kit or a marker kind armed, a click
/// places it (Shift keeps it armed); a kit dragged from the palette lands
/// where it is dropped.
/// </summary>
public sealed class FrontRoomsModulePlanView
{
    static readonly Color Floor0 = new Color(.42f, .38f, .24f), FloorOffice = new Color(.30f, .34f, .36f);
    static readonly Color WallColor = new Color(.95f, .94f, .90f), ArchColor = new Color(.96f, .85f, .25f), OpenColor = new Color(1f, 1f, 1f, .12f);
    static readonly Color PropColor = new Color(.55f, .75f, .95f, .55f), PropSelected = new Color(1f, .6f, .2f, .75f), GhostColor = new Color(.4f, 1f, .5f, .45f);
    static readonly Color StripColor = new Color(.3f, .9f, .4f, .12f);
    static readonly Color KeyColor = new Color(1f, .82f, .2f, .95f), RelayColor = new Color(.8f, .4f, 1f, .95f), MarkerSelected = Color.white;
    const float Edge = 7f;
    static GUIStyle centeredMini, markerLetter;

    readonly Action repaint;
    FrontRoomsRoomModule module;
    int selected = -1;
    // The props array the selection was last checked against, and the selected prop then (see Follow).
    ModuleProp[] selectedIn;
    ModuleProp selectedProp;
    // The selected marker, the markers array it was last checked against, and the marker then (as for props).
    int selectedMarker = -1;
    ModuleMarker[] markerIn;
    ModuleMarker markerData;
    // A prop or (markerDrag) a marker is held by the mouse, and whether the drag has moved it yet.
    bool dragging, moved, markerDrag;
    Vector2 dragOffset;
    // The armed or dragged kit and the module point under the mouse, drawn where it would land.
    (string kit, Vector2 at)? ghost;
    // The module point under the mouse while a marker kind is armed.
    Vector2? markerGhost;
    string armedKit;
    ModuleMarkerKind? armedMarker;

    /// <param name="repaint">Repaints the panel that draws this plan.</param>
    public FrontRoomsModulePlanView(Action repaint) => this.repaint = repaint;

    /// <summary>Raised when the designer picks a prop here or in the prop fields (-1: none). The window selects it in the Scene too.</summary>
    public event Action<int> SelectionChanged;

    /// <summary>The kit a click in the plan places, or null. The window's palette arms it; arming one disarms a marker kind.</summary>
    public string ArmedKit
    {
        get => armedKit;
        set
        {
            armedKit = value;
            if (value != null) armedMarker = null;
            markerGhost = null;
        }
    }

    /// <summary>The marker kind a click in the plan places, or null. The Markers section arms it; arming one disarms a kit.</summary>
    public ModuleMarkerKind? ArmedMarker
    {
        get => armedMarker;
        set
        {
            armedMarker = value;
            if (value != null) armedKit = null;
            ghost = null;
            markerGhost = null;
        }
    }

    /// <summary>The selected prop's index, or -1.</summary>
    public int Selected => selected;

    /// <summary>The selected marker's index, or -1.</summary>
    public int SelectedMarker => selectedMarker;

    /// <summary>What a click in the plan does now, for the line under it.</summary>
    public string Help => ArmedKit != null ? "Click to place " + ArmedKit + " (Shift: keep placing). Esc stops."
        : ArmedMarker != null ? "Click to place a " + FrontRoomsModuleEditing.MarkerName(ArmedMarker.Value) + " (Shift: keep placing). Esc stops."
        : "Click a prop or a marker (K key spot, R Relay entry) to select (again: the one under it), drag to move, R turns, Delete removes, Esc deselects. "
          + "Click an edge: wall → arch → open. Right-click a cell: its lamp, or a key spot or Relay entry there.";

    static GUIStyle CenteredMini => centeredMini ?? (centeredMini = new GUIStyle(EditorStyles.miniLabel) { alignment = TextAnchor.MiddleCenter, normal = { textColor = Color.white } });

    static GUIStyle MarkerLetter => markerLetter ?? (markerLetter = new GUIStyle(EditorStyles.miniBoldLabel) { alignment = TextAnchor.MiddleCenter, normal = { textColor = Color.black } });

    /// <summary>Select a prop (-1: none). <paramref name="notify"/> is false when the selection comes from the Scene view. A selected marker is let go.</summary>
    public void Select(int index, bool notify = true)
    {
        // Given by an edit that knows where its prop went: trusted as it is.
        selectedIn = null;
        if (index >= 0 && selectedMarker >= 0)
        {
            selectedMarker = -1;
            markerIn = null;
            repaint();
        }
        if (index == selected) return;
        selected = index;
        if (notify) SelectionChanged?.Invoke(index);
        repaint();
    }

    /// <summary>
    /// Select a marker (-1: none). Markers live only in the module, so the
    /// Scene selection is not touched, except that a selected prop is let go
    /// (there and here).
    /// </summary>
    public void SelectMarker(int index)
    {
        // Given by an edit that knows where its marker went: trusted as it is.
        markerIn = null;
        if (index >= 0) Select(-1);
        if (index == selectedMarker) return;
        selectedMarker = index;
        repaint();
    }

    /// <summary>The panel shows another module: end a drag (it reaches the old module's preview) and select nothing, without telling the Scene view.</summary>
    public void Forget()
    {
        EndDrag();
        selected = selectedMarker = -1;
        selectedIn = null;
        markerIn = null;
        repaint();
    }

    /// <summary>Call when the panel closes: a move cut short still reaches the preview.</summary>
    public void EndDrag()
    {
        if (dragging && moved && module != null) FrontRoomsRoomModule.NotifyChanged(module);
        dragging = moved = markerDrag = false;
    }

    /// <summary>
    /// Keep the selection on its prop or marker when the array has been
    /// replaced: props or markers removed, reordered or added in the other
    /// panel or the Scene view, or an undo. If it is gone, nothing is
    /// selected. Draw calls it first.
    /// </summary>
    public void Follow(RoomModuleData m)
    {
        if (selected >= 0 && selectedIn != null && !ReferenceEquals(selectedIn, m.props))
        {
            var at = Array.IndexOf(m.props, selectedProp);
            // Not found, but the same kit where it was in a list as long: the prop itself was edited (an undone turn).
            selected = at >= 0 ? at
                : m.props.Length == selectedIn.Length && selected < m.props.Length && m.props[selected].kit == selectedProp.kit ? selected
                : -1;
        }
        if (selected >= m.props.Length) selected = -1;
        selectedIn = m.props;
        if (selected >= 0) selectedProp = m.props[selected];

        if (selectedMarker >= 0 && markerIn != null && !ReferenceEquals(markerIn, m.markers))
        {
            var at = Array.IndexOf(m.markers, markerData);
            // Not found, but the same kind where it was in a list as long: the marker itself was edited (an undone move).
            selectedMarker = at >= 0 ? at
                : m.markers.Length == markerIn.Length && selectedMarker < m.markers.Length && m.markers[selectedMarker].kind == markerData.kind ? selectedMarker
                : -1;
        }
        if (selectedMarker >= m.markers.Length) selectedMarker = -1;
        markerIn = m.markers;
        if (selectedMarker >= 0) markerData = m.markers[selectedMarker];
    }

    /// <summary>Draw the plan, as large as fits <paramref name="availableWidth"/>, and handle its events.</summary>
    public void Draw(FrontRoomsRoomModule target, float availableWidth)
    {
        // Another module: a selection or a drag of the old one must not carry over (Follow would find a like prop or marker).
        if (module != null && target != module) Forget();
        module = target;
        var m = module.data;
        Follow(m);
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
        var markerAt = m.markers.Select(q => ToPlan(q.x, q.z)).ToArray();
        // At least a few pixels across, so a marker can be picked in a big room.
        float MarkerRadius(ModuleMarkerKind kind) => kind == ModuleMarkerKind.RelayEntry ? Mathf.Max(7f, ModuleUnits.RelayRadius * metre) : Mathf.Max(6f, .15f * metre);
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
            var dragged = FrontRoomsModuleEditing.DraggedKit();
            if (dragged != null && inside)
            {
                DragAndDrop.visualMode = DragAndDropVisualMode.Copy;
                ghost = (dragged, ToModule(e.mousePosition));
                if (e.type == EventType.DragPerform)
                {
                    DragAndDrop.AcceptDrag();
                    FrontRoomsModuleEditing.DragDone();
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
        if ((e.type == EventType.DragExited || e.type == EventType.MouseLeaveWindow) && (ghost != null || markerGhost != null))
        {
            ghost = null;
            markerGhost = null;
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
        if (ArmedMarker != null && (e.type == EventType.MouseMove || e.type == EventType.MouseDrag))
        {
            var now = inside ? ToModule(e.mousePosition) : (Vector2?)null;
            if (now != markerGhost)
            {
                markerGhost = now;
                repaint();
            }
        }

        // Left click: an armed kit or marker is placed; else markers first, then props (topmost; again cycles to the one
        // under it), then columns, then edges, else deselect.
        if (e.type == EventType.MouseDown && e.button == 0 && inside)
        {
            GUIUtility.keyboardControl = 0;
            var markerHits = new List<int>();
            for (var k = m.markers.Length - 1; k >= 0; k--) if ((markerAt[k] - e.mousePosition).magnitude <= MarkerRadius(m.markers[k].kind) + 2f) markerHits.Add(k);
            var hits = new List<int>();
            for (var k = m.props.Length - 1; k >= 0; k--) if (Inside(polys[k], e.mousePosition)) hits.Add(k);
            var columnHit = ColumnAt(m, e.mousePosition, ToPlan);
            var edgeHit = edges.FindIndex(q => q.rect.Contains(e.mousePosition));
            if (ArmedKit != null)
            {
                Place(ArmedKit, ToModule(e.mousePosition));
                if (!e.shift) Disarm();
            }
            else if (ArmedMarker != null)
            {
                PlaceMarker(module, ArmedMarker.Value, ToModule(e.mousePosition));
                if (!e.shift) Disarm();
            }
            else if (markerHits.Count > 0)
            {
                var at = markerHits.IndexOf(selectedMarker);
                SelectMarker(at >= 0 ? markerHits[(at + 1) % markerHits.Count] : markerHits[0]);
                dragging = markerDrag = true;
                moved = false;
                dragOffset = ToModule(e.mousePosition) - new Vector2(m.markers[selectedMarker].x, m.markers[selectedMarker].z);
                Undo.IncrementCurrentGroup();
                FrontRoomsModuleEditing.Record(module, "Move marker");
            }
            else if (hits.Count > 0)
            {
                var at = hits.IndexOf(selected);
                Select(at >= 0 ? hits[(at + 1) % hits.Count] : hits[0]);
                dragging = true;
                markerDrag = false;
                moved = false;
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
            else
            {
                Select(-1);
                SelectMarker(-1);
            }
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
            var turns = PreviewTurns(module);
            var minCells = FrontRoomsLevelProfiles.Resolve().generation?.columnMinRoomCells ?? 3;
            for (var j = 1; j < m.depth; j++)
            for (var i = 1; i < m.width; i++)
            {
                var custom = m.customColumns.FirstOrDefault(k => k.x == i && k.y == j);
                var has = m.columns == ModuleColumns.Custom && m.customColumns.Any(k => k.x == i && k.y == j);
                var auto = m.AutoColumnAt(i, j, turns, minCells);
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
            // Markers on top of the props, the selected one ringed in white.
            for (var k = 0; k < m.markers.Length; k++) DrawMarker(markerAt[k], m.markers[k], MarkerRadius(m.markers[k].kind), k == selectedMarker, 1f);
            // Where the armed or dragged kit would go, wall units already against their wall.
            if (ghost != null)
            {
                Shape(FrontRoomsModuleEditing.NewProp(m, ghost.Value.kit, ghost.Value.at), band, ToPlan, out var poly, out var front);
                DrawProp(poly, front, GhostColor);
            }
            // Where the armed marker would go.
            if (ArmedMarker != null && markerGhost != null)
            {
                var g = FrontRoomsModuleEditing.NewMarker(m, ArmedMarker.Value, markerGhost.Value);
                DrawMarker(ToPlan(g.x, g.z), g, MarkerRadius(g.kind), false, .5f);
            }
            foreach (var q in edges) EditorGUIUtility.AddCursorRect(q.rect, MouseCursor.Link);
            if (ArmedKit != null || ArmedMarker != null) EditorGUIUtility.AddCursorRect(area, MouseCursor.ArrowPlus);
        }

        if (dragging && e.type == EventType.MouseDrag && (markerDrag ? selectedMarker >= 0 : selected >= 0))
        {
            // Moves show in the plan at once; the preview rebuilds when the drag ends. An axis changes
            // only once the mouse takes it to another snap step, so a wall unit slid along its wall keeps its exact gap.
            var to = ToModule(e.mousePosition) - dragOffset;
            var step = e.control || e.command ? .5f : FrontRoomsModuleEditing.Grid;
            if (markerDrag)
            {
                var mk = m.markers[selectedMarker];
                var at = Dragged(m, new Vector2(mk.x, mk.z), to, step);
                if (at.x != mk.x || at.y != mk.z)
                {
                    mk.x = at.x;
                    mk.z = at.y;
                    m.markers[selectedMarker] = mk;
                    moved = true;
                    EditorUtility.SetDirty(module);
                }
            }
            else
            {
                var p = m.props[selected];
                var at = Dragged(m, new Vector2(p.x, p.z), to, step);
                if (at.x != p.x || at.y != p.z)
                {
                    p.x = at.x;
                    p.z = at.y;
                    m.props[selected] = p;
                    moved = true;
                    EditorUtility.SetDirty(module);
                }
            }
            e.Use();
            repaint();
        }
        if (dragging && e.rawType == EventType.MouseUp)
        {
            // A click that only selects leaves the preview as it is.
            if (moved) Changed();
            dragging = moved = markerDrag = false;
            e.Use();
        }
        // Keys only when no field is being typed in.
        var any = selected >= 0 || selectedMarker >= 0;
        if ((any || ArmedKit != null || ArmedMarker != null) && e.type == EventType.KeyDown && GUIUtility.keyboardControl == 0 && !EditorGUIUtility.editingTextField && !(e.control || e.command || e.alt))
        {
            if (e.keyCode == KeyCode.Escape)
            {
                if (ArmedKit != null || ArmedMarker != null) Disarm();
                else
                {
                    Select(-1);
                    SelectMarker(-1);
                }
                e.Use();
                repaint();
            }
            else if (any && e.keyCode == KeyCode.R)
            {
                if (selectedMarker >= 0) FrontRoomsModuleEditing.TurnMarker(module, selectedMarker);
                else FrontRoomsModuleEditing.TurnProp(module, selected);
                e.Use();
                repaint();
            }
            else if (any && (e.keyCode == KeyCode.Delete || e.keyCode == KeyCode.Backspace)) { RemoveSelectedAny(); e.Use(); }
        }
        // Edit → Delete (⌘⌫, or Delete where the shortcut takes the key) arrives as a command.
        if (any && (e.type == EventType.ValidateCommand || e.type == EventType.ExecuteCommand) && (e.commandName == "SoftDelete" || e.commandName == "Delete")
            && GUIUtility.keyboardControl == 0 && !EditorGUIUtility.editingTextField)
        {
            if (e.type == EventType.ExecuteCommand) RemoveSelectedAny();
            e.Use();
        }

        // Right-click a cell: a marker there, or its lamp.
        if (e.type == EventType.ContextClick || (e.type == EventType.MouseDown && e.button == 1))
            for (var j = 0; j < m.depth; j++)
            for (var i = 0; i < m.width; i++)
            {
                if (!CellRect(i, j).Contains(e.mousePosition)) continue;
                var ci = i;
                var cj = j;
                var lampModule = module;
                var point = ToModule(e.mousePosition);
                var menu = new GenericMenu();
                menu.AddItem(new GUIContent("Key spot here"), false, () => PlaceMarker(lampModule, ModuleMarkerKind.KeySpot, point));
                menu.AddItem(new GUIContent("Relay entry here"), false, () => PlaceMarker(lampModule, ModuleMarkerKind.RelayEntry, point));
                menu.AddSeparator("");
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

    /// <summary>Remove the selected marker (Delete in the plan, Remove in the marker fields).</summary>
    public void RemoveSelectedMarker()
    {
        if (selectedMarker < 0) return;
        FrontRoomsModuleEditing.RemoveMarkers(module, new[] { selectedMarker });
        SelectMarker(-1);
    }

    void RemoveSelectedAny()
    {
        if (selectedMarker >= 0) RemoveSelectedMarker();
        else RemoveSelected();
    }

    void Place(string kit, Vector2 at) => Select(FrontRoomsModuleEditing.AddKit(module, kit, at));

    void PlaceMarker(FrontRoomsRoomModule target, ModuleMarkerKind kind, Vector2 at)
    {
        var index = FrontRoomsModuleEditing.AddMarker(target, kind, at);
        if (target == module) SelectMarker(index);
        repaint();
    }

    void Disarm()
    {
        ArmedKit = null;
        ArmedMarker = null;
        ghost = null;
    }

    /// <summary>Where a drag takes a point: snapped inside the room, an axis changing only once the mouse takes it to another snap step.</summary>
    static Vector2 Dragged(RoomModuleData m, Vector2 was, Vector2 to, float step)
    {
        var x = Mathf.Clamp(FrontRoomsModuleEditing.Snap(to.x, step), 0f, m.WidthMetres);
        var z = Mathf.Clamp(FrontRoomsModuleEditing.Snap(to.y, step), 0f, m.DepthMetres);
        return new Vector2(x != Mathf.Clamp(FrontRoomsModuleEditing.Snap(was.x, step), 0f, m.WidthMetres) ? x : was.x,
            z != Mathf.Clamp(FrontRoomsModuleEditing.Snap(was.y, step), 0f, m.DepthMetres) ? z : was.y);
    }

    /// <summary>A marker: a disc (a Relay entry as wide as its body), its letter, a tick for its yaw (0 = north, up), a Relay entry's tag under it.</summary>
    static void DrawMarker(Vector2 centre, ModuleMarker mk, float radius, bool selected, float alpha)
    {
        var key = mk.kind == ModuleMarkerKind.KeySpot;
        if (selected)
        {
            Handles.color = MarkerSelected;
            Handles.DrawSolidDisc(centre, Vector3.forward, radius + 2.5f);
        }
        var fill = key ? KeyColor : RelayColor;
        fill.a *= alpha;
        Handles.color = fill;
        Handles.DrawSolidDisc(centre, Vector3.forward, radius);
        var rad = mk.yaw * Mathf.Deg2Rad;
        var heading = new Vector2(Mathf.Sin(rad), -Mathf.Cos(rad));
        Handles.color = new Color(.08f, .08f, .08f, .95f * alpha);
        Handles.DrawAAPolyLine(2.5f, centre + heading * radius * .6f, centre + heading * (radius + 5f));
        GUI.Label(new Rect(centre.x - 10f, centre.y - 8f, 20f, 16f), key ? "K" : "R", MarkerLetter);
        if (!key && !string.IsNullOrEmpty(mk.tag)) GUI.Label(new Rect(centre.x - 40f, centre.y + radius, 80f, 14f), mk.tag, CenteredMini);
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

    /// <summary>
    /// The designer preview's quarter turns when it shows this module, else 0.
    /// Auto columns (pale squares, RoomModuleData.AutoColumnAt) are drawn for
    /// that turn: the generator lands Auto-column modules on the same 6 m grid
    /// phase, so they match the game for it, and another turn can move them.
    /// </summary>
    static int PreviewTurns(FrontRoomsRoomModule module)
    {
        var preview = FrontRoomsDesignerSceneTools.ScenePreview();
        return preview != null && preview.module == module ? ((preview.rotation % 4) + 4) % 4 : 0;
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
