using System;
using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Edits to a room module asset, shared by the Inspector, the Level Designer
/// window, the Scene view tools and the batch tests, so every way of placing
/// a kit places it the same way. Each edit is recorded for Undo on the asset
/// and raises FrontRoomsRoomModule.Changed, which rebuilds the preview.
/// </summary>
public static class FrontRoomsModuleEditing
{
    /// <summary>Props snap to this in the plan, the palette and the Scene view (LEVEL_MODULE_SPEC §9).</summary>
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

    /// <summary>Kit assets to choose from: the kit library's names, without stray copies ("Kit_X 2").</summary>
    public static string[] Kits()
    {
        if (kits == null) kits = FrontRoomsKitLibrary.AllNames().Where(n => !n.Contains(" ")).ToArray();
        return kits;
    }

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
    /// doorways are not walls), centred where it was put along that edge and
    /// kept clear of the walls at its ends. A room without walls uses its nearest side.
    /// </summary>
    public static ModuleProp SnapToWall(RoomModuleData m, string kit, Vector2 at, float y = 0f)
    {
        m.Normalize();
        var cs = MapGrid.CellSize;
        float width = m.WidthMetres, depth = m.DepthMetres;
        var best = float.MaxValue;
        var side = WallSide.South;
        float line = 0f, along = at.x;
        // A wall stretch from a to b along its line; across is the point's distance from the line.
        void Consider(WallSide s, float l, float a, float b, float across, float pointAlong)
        {
            var off = Mathf.Max(a - pointAlong, 0f, pointAlong - b);
            var d = across * across + off * off;
            if (d >= best) return;
            best = d;
            side = s;
            line = l;
            along = Mathf.Clamp(pointAlong, a, b);
        }
        for (var i = 0; i < m.width; i++)
        {
            if (m.south[i] == ModuleEdge.Wall) Consider(WallSide.South, 0f, i * cs, (i + 1) * cs, at.y, at.x);
            if (m.north[i] == ModuleEdge.Wall) Consider(WallSide.North, depth, i * cs, (i + 1) * cs, depth - at.y, at.x);
        }
        for (var j = 0; j < m.depth; j++)
        {
            if (m.west[j] == ModuleEdge.Wall) Consider(WallSide.West, 0f, j * cs, (j + 1) * cs, at.x, at.y);
            if (m.east[j] == ModuleEdge.Wall) Consider(WallSide.East, width, j * cs, (j + 1) * cs, width - at.x, at.y);
        }
        for (var j = 0; j < m.depth; j++)
        for (var i = 0; i < m.width; i++)
        {
            // An inner wall has a face on each side: the one facing the point.
            if (i < m.width - 1 && m.innerEast[i + j * (m.width - 1)] == ModuleEdge.Wall)
            {
                var x = (i + 1) * cs;
                Consider(at.x >= x ? WallSide.West : WallSide.East, x, j * cs, (j + 1) * cs, at.x - x, at.y);
            }
            if (j < m.depth - 1 && m.innerNorth[i + j * m.width] == ModuleEdge.Wall)
            {
                var z = (j + 1) * cs;
                Consider(at.y >= z ? WallSide.South : WallSide.North, z, i * cs, (i + 1) * cs, at.y - z, at.x);
            }
        }
        if (best == float.MaxValue)
        {
            Consider(WallSide.South, 0f, 0f, width, at.y, at.x);
            Consider(WallSide.North, depth, 0f, width, depth - at.y, at.x);
            Consider(WallSide.West, 0f, 0f, depth, at.x, at.y);
            Consider(WallSide.East, width, 0f, depth, width - at.x, at.y);
        }

        // Keep the whole footprint off the walls at the ends of the run.
        var f = Footprint(kit);
        var half = (f[2] - f[0]) * .5f;
        var span = side == WallSide.South || side == WallSide.North ? width : depth;
        var margin = ModuleUnits.WallHalf + WallGap + half;
        along = margin <= span - margin ? Mathf.Clamp(along, margin, span - margin) : span * .5f;
        return AgainstWall(kit, side, line, along, y);
    }

    /// <summary>
    /// The top ("top" support) of the topmost floor prop under a point, for a
    /// desk-top item: its height above the floor and the prop's yaw.
    /// </summary>
    static bool SurfaceUnder(RoomModuleData m, Vector2 at, out float top, out float yaw)
    {
        for (var k = m.props.Length - 1; k >= 0; k--)
        {
            var p = m.props[k];
            var info = FrontRoomsKitLibrary.GetInfo(p.kit);
            if (info == null || info.placement == "DeskTop" || !info.TrySupport("top", out var centre, out var size)) continue;
            // The point in the prop's own frame (Unity yaw: world = (x cos + z sin, -x sin + z cos)).
            var rad = p.yaw * Mathf.Deg2Rad;
            float c = Mathf.Cos(rad), s = Mathf.Sin(rad), dx = at.x - p.x, dz = at.y - p.z;
            float lx = dx * c - dz * s, lz = dx * s + dz * c;
            if (Mathf.Abs(lx - centre.x) > size.x * .5f || Mathf.Abs(lz - centre.z) > size.y * .5f) continue;
            top = p.y + centre.y;
            yaw = p.yaw;
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
}
