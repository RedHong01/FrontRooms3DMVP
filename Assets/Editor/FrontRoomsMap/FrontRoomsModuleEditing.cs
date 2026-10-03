using System;
using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Edits to a room module asset (its props and gameplay markers), shared by
/// the Inspector, the Level Designer window, the Scene view tools and the
/// batch tests, so every way of placing a kit places it the same way. Each
/// edit is recorded for Undo on the asset
/// and raises FrontRoomsRoomModule.Changed, which rebuilds the preview.
/// </summary>
public static class FrontRoomsModuleEditing
{
    /// <summary>Props and markers snap to this in the plan, the palette and the Scene view (LEVEL_MODULE_SPEC §9).</summary>
    public const float Grid = .05f;
    /// <summary>DragAndDrop generic-data key of a kit dragged from the palette (its name).</summary>
    public const string DragKey = "FrontRoomsKit";
    /// <summary>A wall unit's back stands this far off the wall face.</summary>
    public const float WallGap = .03f;
    /// <summary>Hung pieces (a kit with a "hang" anchor: the clock) go up this high, as in the samples.</summary>
    const float HangHeight = 2.1f;

    /// <summary>Where the wall is, seen from a prop standing against it.</summary>
    public enum WallSide { South, North, West, East }

    static string[] kits;

    // Found again after any import, so a kit just exported from Blender shows without a script reload.
    [InitializeOnLoadMethod]
    static void WatchKits() => EditorApplication.projectChanged += () => kits = null;

    /// <summary>Kit assets to choose from (Resources/Props/Models), without stray copies ("Kit_X 2") or the axis probe.</summary>
    public static string[] Kits()
    {
        if (kits == null)
            kits = AssetDatabase.FindAssets("t:GameObject", new[] { "Assets/Resources/" + FrontRoomsKitLibrary.ModelFolder.TrimEnd('/') })
                .Select(g => System.IO.Path.GetFileNameWithoutExtension(AssetDatabase.GUIDToAssetPath(g)))
                .Where(n => !n.Contains(" ") && !n.StartsWith("Kit_AxisProbe"))
                .Distinct().OrderBy(n => n, StringComparer.Ordinal).ToArray();
        return kits;
    }

    /// <summary>
    /// The kit being dragged from the palette, or null. Only palette drags
    /// carry no paths or objects: generic drag data outlives its drag (only
    /// PrepareStartDrag resets it), so a file dragged in from the Finder would
    /// otherwise read the last kit.
    /// </summary>
    public static string DraggedKit() =>
        (DragAndDrop.paths?.Length ?? 0) == 0 && (DragAndDrop.objectReferences?.Length ?? 0) == 0 ? DragAndDrop.GetGenericData(DragKey) as string : null;

    /// <summary>A kit has been dropped: forget it, so no later drag reads it.</summary>
    public static void DragDone() => DragAndDrop.SetGenericData(DragKey, null);

    /// <summary>The palette's kits: those of one placement ("All", "Floor", "Wall", "DeskTop") whose name contains <paramref name="search"/>.</summary>
    public static List<string> PaletteKits(string placement, string search) =>
        Kits().Where(n => (placement == "All" || Placement(n) == placement)
            && (string.IsNullOrEmpty(search) || n.IndexOf(search, StringComparison.OrdinalIgnoreCase) >= 0)).ToList();

    /// <summary>The kit's placement from its sidecar (Floor, Wall, DeskTop, Ceiling), or "" if unknown.</summary>
    public static string Placement(string kit) => FrontRoomsKitLibrary.GetInfo(kit)?.placement ?? "";

    /// <summary>A kit's footprint about its pivot (min x, min z, max x, max z, height), or a 0.6 m stand-in for a missing asset.</summary>
    public static float[] Footprint(string kit) => FrontRoomsMapWorld.KitFootprint(kit) ?? new[] { -.3f, -.3f, .3f, .3f, 1f };

    public static string Short(string kit) => string.IsNullOrEmpty(kit) ? "?" : kit.StartsWith("Kit_") ? kit.Substring(4) : kit;

    public static float Snap(float v, float step = Grid) => Mathf.Round(v / step) * step;

    public static void Record(FrontRoomsRoomModule module, string label) => Undo.RecordObject(module, label);

    /// <summary>After an edit: mark the asset dirty and let the preview and the panels follow.</summary>
    public static void Changed(FrontRoomsRoomModule module)
    {
        EditorUtility.SetDirty(module);
        FrontRoomsRoomModule.NotifyChanged(module);
    }

    // ---------- Placing kits ----------

    /// <summary>
    /// Add a kit where the designer put it, in module metres: a click with a
    /// palette kit armed, a kit dropped on the plan or on the Scene view's floor.
    /// Returns the new prop's index.
    /// </summary>
    public static int AddKit(FrontRoomsRoomModule module, string kit, Vector2 at)
    {
        var m = module.data;
        m.Normalize();
        Record(module, "Add " + Short(kit));
        m.props = m.props.Append(NewProp(m, kit, at)).ToArray();
        Changed(module);
        return m.props.Length - 1;
    }

    /// <summary>
    /// The prop a kit becomes at a point: snapped to 0.05 m inside the room;
    /// wall units with their back to the nearest wall face (a hung piece at
    /// 2.1 m); desk-top items on the top of the prop under them, turned with
    /// it and without a collider.
    /// </summary>
    public static ModuleProp NewProp(RoomModuleData m, string kit, Vector2 at)
    {
        at = new Vector2(Mathf.Clamp(Snap(at.x), 0f, m.WidthMetres), Mathf.Clamp(Snap(at.y), 0f, m.DepthMetres));
        var info = FrontRoomsKitLibrary.GetInfo(kit);
        switch (info?.placement)
        {
            case "Wall":
                var hung = info.TryAnchor("hang", out _);
                return SnapToWall(m, kit, at, hung ? Mathf.Min(HangHeight, MapGrid.CeilingHeight(m.height) - ModuleUnits.CeilingClearance - info.Height) : 0f);
            case "DeskTop":
                var p = new ModuleProp { kit = kit, x = at.x, z = at.y, noCollider = true };
                if (SurfaceUnder(m, at, out var top, out var yaw)) { p.y = top; p.yaw = yaw; }
                return p;
            default:
                return new ModuleProp { kit = kit, x = at.x, z = at.y };
        }
    }

    /// <summary>
    /// A prop with its back to a wall, 3 cm off the wall face, its front into
    /// the room, its footprint centred on <paramref name="along"/>.
    /// <paramref name="line"/> is the wall's cell line (x for a west or east
    /// wall, z for a south or north one). Uses the real footprint, which need
    /// not be centred on the pivot.
    /// </summary>
    public static ModuleProp AgainstWall(string kit, WallSide side, float line, float along, float y = 0f)
    {
        var f = Footprint(kit);
        var gap = ModuleUnits.WallHalf + WallGap;
        var cx = (f[0] + f[2]) * .5f; // the footprint's centre across the front, in local X
        switch (side)
        {
            // yaw 0: local -Z (the back) faces south.
            case WallSide.South: return new ModuleProp { kit = kit, x = along - cx, z = line + gap - f[1], y = y, yaw = 0f };
            // yaw 180: local x and z turn round.
            case WallSide.North: return new ModuleProp { kit = kit, x = along + cx, z = line - gap + f[1], y = y, yaw = 180f };
            // yaw 90: local (x, z) -> world (z, -x).
            case WallSide.West: return new ModuleProp { kit = kit, x = line + gap - f[1], z = along + cx, y = y, yaw = 90f };
            // yaw 270: local (x, z) -> world (-z, x).
            default: return new ModuleProp { kit = kit, x = line - gap + f[1], z = along - cx, y = y, yaw = 270f };
        }
    }

    /// <summary>Against one of the room's own four walls (the sample modules are written this way).</summary>
    public static ModuleProp AgainstRoomWall(string kit, float along, WallSide side, RoomModuleData m, float y = 0f) =>
        AgainstWall(kit, side, side == WallSide.North ? m.DepthMetres : side == WallSide.East ? m.WidthMetres : 0f, along, y);

    /// <summary>
    /// A wall unit against the wall face nearest <paramref name="at"/>: the
    /// room's walls and its inner walls, a cell edge at a time (openings and
    /// doorways are not walls), centred where it was put along the wall. Its
    /// whole footprint stays on the run of wall it stands against, clear of
    /// the corner, doorway or crossing wall at each end. A room without walls
    /// uses its nearest side.
    /// </summary>
    public static ModuleProp SnapToWall(RoomModuleData m, string kit, Vector2 at, float y = 0f)
    {
        m.Normalize();
        var cs = MapGrid.CellSize;
        float width = m.WidthMetres, depth = m.DepthMetres;
        var best = float.MaxValue;
        var side = WallSide.South;
        int line = 0, cell = 0;
        var along = at.x;
        // The wall edge at cell k of a cell line (a line index, 0 at the south or west wall); across is the point's distance from it.
        void Consider(WallSide s, int l, int k, float across, float pointAlong)
        {
            float a = k * cs, b = a + cs;
            var off = Mathf.Max(a - pointAlong, 0f, pointAlong - b);
            var d = across * across + off * off;
            if (d >= best) return;
            best = d;
            side = s;
            line = l;
            cell = k;
            along = Mathf.Clamp(pointAlong, a, b);
        }
        // Each wall has a face on each side inside the room: the one facing the point.
        for (var l = 0; l <= m.depth; l++)
        for (var i = 0; i < m.width; i++)
        {
            if (!WallAlongX(m, l, i)) continue;
            var z = l * cs;
            if (l < m.depth && (l == 0 || at.y >= z)) Consider(WallSide.South, l, i, at.y - z, at.x);
            if (l > 0 && (l == m.depth || at.y < z)) Consider(WallSide.North, l, i, z - at.y, at.x);
        }
        for (var l = 0; l <= m.width; l++)
        for (var j = 0; j < m.depth; j++)
        {
            if (!WallAlongZ(m, l, j)) continue;
            var x = l * cs;
            if (l < m.width && (l == 0 || at.x >= x)) Consider(WallSide.West, l, j, at.x - x, at.y);
            if (l > 0 && (l == m.width || at.x < x)) Consider(WallSide.East, l, j, x - at.x, at.y);
        }

        bool alongX;
        float r0 = 0f, r1;
        if (best == float.MaxValue)
        {
            // No walls at all: the nearest side, all of it.
            var sides = new[] { (WallSide.South, 0, at.y), (WallSide.North, m.depth, depth - at.y), (WallSide.West, 0, at.x), (WallSide.East, m.width, width - at.x) };
            (side, line, _) = sides.OrderBy(q => q.Item3).First();
            alongX = side == WallSide.South || side == WallSide.North;
            along = alongX ? at.x : at.y;
            r1 = alongX ? width : depth;
        }
        else
        {
            // The run of wall it stands against: this edge and its neighbours on the line, up to
            // a corner, a doorway, or a wall or doorway that meets the line on the unit's side.
            alongX = side == WallSide.South || side == WallSide.North;
            var count = alongX ? m.width : m.depth;
            var near = side == WallSide.South || side == WallSide.West ? line : line - 1;
            bool Wall(int k) => k >= 0 && k < count && (alongX ? WallAlongX(m, line, k) : WallAlongZ(m, line, k));
            bool Crossed(int k) => alongX ? m.EdgeAt(k, near, 1, 0) != ModuleEdge.Open : m.EdgeAt(near, k, 0, 1) != ModuleEdge.Open;
            int lo = cell, hi = cell;
            while (Wall(lo - 1) && !Crossed(lo - 1)) lo--;
            while (Wall(hi + 1) && !Crossed(hi)) hi++;
            r0 = lo * cs;
            r1 = (hi + 1) * cs;
        }
        var f = Footprint(kit);
        var margin = ModuleUnits.WallHalf + WallGap + (f[2] - f[0]) * .5f;
        along = r1 - r0 >= 2f * margin ? Mathf.Clamp(along, r0 + margin, r1 - margin) : (r0 + r1) * .5f;
        return AgainstWall(kit, side, line * cs, along, y);
    }

    /// <summary>A wall on the cell line z = l cells (0: the south wall, depth: the north wall) at column i.</summary>
    static bool WallAlongX(RoomModuleData m, int l, int i) => (l < m.depth ? m.EdgeAt(i, l, 0, -1) : m.EdgeAt(i, l - 1, 0, 1)) == ModuleEdge.Wall;

    /// <summary>A wall on the cell line x = l cells (0: the west wall, width: the east wall) at row j.</summary>
    static bool WallAlongZ(RoomModuleData m, int l, int j) => (l < m.width ? m.EdgeAt(l, j, -1, 0) : m.EdgeAt(l - 1, j, 1, 0)) == ModuleEdge.Wall;

    /// <summary>The height above the floor of a prop's top (its "top" support: desks, cabinets), or null; desk-top items land there.</summary>
    public static float? TopHeight(ModuleProp p)
    {
        var info = FrontRoomsKitLibrary.GetInfo(p.kit);
        if (info == null || info.placement == "DeskTop" || !info.TrySupport("top", out var centre, out _)) return null;
        return p.y + centre.y;
    }

    /// <summary>Whether a module point is over a prop's top, and that top's height above the floor.</summary>
    public static bool OnTop(ModuleProp p, Vector2 at, out float top)
    {
        top = 0f;
        var info = FrontRoomsKitLibrary.GetInfo(p.kit);
        if (info == null || info.placement == "DeskTop" || !info.TrySupport("top", out var centre, out var size)) return false;
        // The point in the prop's own frame (Unity yaw: world = (x cos + z sin, -x sin + z cos)).
        var rad = p.yaw * Mathf.Deg2Rad;
        float c = Mathf.Cos(rad), s = Mathf.Sin(rad), dx = at.x - p.x, dz = at.y - p.z;
        float lx = dx * c - dz * s, lz = dx * s + dz * c;
        if (Mathf.Abs(lx - centre.x) > size.x * .5f || Mathf.Abs(lz - centre.z) > size.y * .5f) return false;
        top = p.y + centre.y;
        return true;
    }

    /// <summary>The top of the topmost floor prop under a point, for a desk-top item: its height above the floor and the prop's yaw.</summary>
    static bool SurfaceUnder(RoomModuleData m, Vector2 at, out float top, out float yaw)
    {
        for (var k = m.props.Length - 1; k >= 0; k--)
        {
            if (!OnTop(m.props[k], at, out top)) continue;
            yaw = m.props[k].yaw;
            return true;
        }
        top = yaw = 0f;
        return false;
    }

    // ---------- Props by index ----------

    public static void TurnProp(FrontRoomsRoomModule module, int index)
    {
        Record(module, "Turn prop");
        var p = module.data.props[index];
        p.yaw = Mathf.Repeat(p.yaw + 90f, 360f);
        module.data.props[index] = p;
        Changed(module);
    }

    /// <summary>A copy half a metre east of the original. Returns its index.</summary>
    public static int DuplicateProp(FrontRoomsRoomModule module, int index)
    {
        var m = module.data;
        Record(module, "Duplicate prop");
        var copy = m.props[index];
        copy.x = Mathf.Min(copy.x + .5f, m.WidthMetres);
        m.props = m.props.Append(copy).ToArray();
        Changed(module);
        return m.props.Length - 1;
    }

    public static void RemoveProps(FrontRoomsRoomModule module, IEnumerable<int> indices)
    {
        var gone = new HashSet<int>(indices);
        if (gone.Count == 0) return;
        Record(module, gone.Count == 1 ? "Remove prop" : "Remove props");
        module.data.props = module.data.props.Where((p, k) => !gone.Contains(k)).ToArray();
        Changed(module);
    }

    /// <summary>Move a prop to another place in the list (the order the map places them in). Returns where it ended up.</summary>
    public static int ReorderProp(FrontRoomsRoomModule module, int index, int to)
    {
        var list = module.data.props.ToList();
        to = Mathf.Clamp(to, 0, list.Count - 1);
        if (to == index) return index;
        Record(module, "Reorder props");
        var p = list[index];
        list.RemoveAt(index);
        list.Insert(to, p);
        module.data.props = list.ToArray();
        Changed(module);
        return to;
    }

    // ---------- Gameplay markers ----------
    // Adds and removes replace the markers array, moves and edits assign in
    // place, as for props: the plan's selection follows its marker by that.

    public static string MarkerName(ModuleMarkerKind kind) => kind == ModuleMarkerKind.KeySpot ? "key spot" : "Relay entry";

    /// <summary>
    /// The top of the highest prop over a module point, as the checks see it:
    /// the prop's "top" support where the point is over it (a desk, a
    /// cabinet), else the top of its footprint box. Null over bare floor.
    /// A key put there lies on the prop instead of inside it.
    /// </summary>
    public static float? TopUnder(RoomModuleData m, Vector2 at)
    {
        float? best = null;
        foreach (var p in m.props)
        {
            var f = string.IsNullOrEmpty(p.kit) ? null : FrontRoomsMapWorld.KitFootprint(p.kit);
            if (f == null) continue;
            // The same box the checks use (RoomModuleData.ValidateMarkers).
            RoomModuleData.Bounds(p, f, out var x0, out var z0, out var x1, out var z1);
            if (at.x <= x0 || at.x >= x1 || at.y <= z0 || at.y >= z1) continue;
            var top = OnTop(p, at, out var surface) ? surface : p.y + f[4];
            if (best == null || top > best.Value) best = top;
        }
        return best;
    }

    /// <summary>
    /// The marker a click makes at a point: snapped to 0.05 m inside the room;
    /// a key spot over a prop lies on its top, a Relay entry stands on the floor.
    /// </summary>
    public static ModuleMarker NewMarker(RoomModuleData m, ModuleMarkerKind kind, Vector2 at)
    {
        at = new Vector2(Mathf.Clamp(Snap(at.x), 0f, m.WidthMetres), Mathf.Clamp(Snap(at.y), 0f, m.DepthMetres));
        var mk = new ModuleMarker { kind = kind, x = at.x, z = at.y, tag = "", host = "" };
        if (kind == ModuleMarkerKind.KeySpot) mk.y = TopUnder(m, at) ?? 0f;
        return mk;
    }

    /// <summary>Add a marker where the designer put it (a click with a marker armed, the plan's right-click menu). Returns its index.</summary>
    public static int AddMarker(FrontRoomsRoomModule module, ModuleMarkerKind kind, Vector2 at)
    {
        var m = module.data;
        m.Normalize();
        Record(module, "Add " + MarkerName(kind));
        m.markers = m.markers.Append(NewMarker(m, kind, at)).ToArray();
        Changed(module);
        return m.markers.Length - 1;
    }

    /// <summary>Move a marker to a module point (0.05 m snap, inside the room); its height stays.</summary>
    public static void MoveMarker(FrontRoomsRoomModule module, int index, Vector2 to)
    {
        var m = module.data;
        Record(module, "Move marker");
        var mk = m.markers[index];
        mk.x = Mathf.Clamp(Snap(to.x), 0f, m.WidthMetres);
        mk.z = Mathf.Clamp(Snap(to.y), 0f, m.DepthMetres);
        m.markers[index] = mk;
        Changed(module);
    }

    public static void TurnMarker(FrontRoomsRoomModule module, int index)
    {
        Record(module, "Turn marker");
        var mk = module.data.markers[index];
        mk.yaw = Mathf.Repeat(mk.yaw + 90f, 360f);
        module.data.markers[index] = mk;
        Changed(module);
    }

    /// <summary>Replace a marker's fields (the marker fields' buttons: on the prop under it, a tag preset, the host).</summary>
    public static void SetMarker(FrontRoomsRoomModule module, int index, ModuleMarker marker, string label = "Edit marker")
    {
        Record(module, label);
        module.data.markers[index] = marker;
        Changed(module);
    }

    public static void RemoveMarkers(FrontRoomsRoomModule module, IEnumerable<int> indices)
    {
        var gone = new HashSet<int>(indices);
        if (gone.Count == 0) return;
        Record(module, gone.Count == 1 ? "Remove marker" : "Remove markers");
        module.data.markers = module.data.markers.Where((mk, k) => !gone.Contains(k)).ToArray();
        Changed(module);
    }
}
