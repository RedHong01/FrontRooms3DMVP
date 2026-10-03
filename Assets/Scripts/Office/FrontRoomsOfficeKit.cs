using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Furnishes an office floor (Level 4 look): cubicle pods and wall rows of
/// fabric panels, laminate desks, beige CRTs and task chairs; a vending
/// machine, water cooler, copier and filing cabinets against the walls; a
/// blacked-out interior window; paper, binders and bins; rarely a structural
/// column (Red: the Backrooms is a maze of walls, not a pillar hall).
///
/// Called by the maze (FrontRoomsMapWorld, Office zones) through reflection
/// and by the look-dev hall. Everything is parented under
/// <paramref name="parent"/> and is a pure function of the seed, so a chunk
/// that is destroyed and rebuilt gets the same furniture.
///
/// Contract (Documentation/LEVEL_MODULE_SPEC.md):
/// * floorXZ is the clear floor in parent-local metres (x→X, y→Z, floor at
///   y = 0). Its edges are walls except where a keepClear strip touches them.
/// * keepClear strips (doorways, arches, open edges, breakable windows) stay
///   empty, and every strip stays connected to every other through aisles at
///   least <see cref="MinAisle"/> wide (each placement is flood-fill tested).
/// * Map rooms are n x 3 m cells with 0.16 m walls on the cell edges, so the
///   clear width is n·3 − 0.16; when the rect matches, columns sit on interior
///   cell corners and decor windows centre on a single cell's wall stretch.
/// * Unit sizes: desk 1.524 x 0.762, panel 1.524 / 0.762 wide, station
///   1.524 x 1.70, pod aisles ≥ 1.6 m, wall units keep a 0.5 m service zone.
/// </summary>
public static class FrontRoomsOfficeKit
{
    public const float Aisle = 1.6f;      // between pods: the chase lane
    public const float MinAisle = 1.0f;   // between any keepClear strips
    const float Cell = .25f;
    const float MapCell = 3f;
    const float MapWall = .16f;

    // Kit asset names (Resources/Props/Models). Missing assets are skipped.
    public const string Panel = "Kit_CubiclePanel";           // 1.524 m wide fabric panel, front +Z
    public const string PanelShort = "Kit_CubiclePanelShort"; // 0.762 m end panel (desk depth)
    public const string PanelTall = "Kit_CubiclePanelTall";   // 1.65 m spine panel (blocks the Relay's 1.6 m sight ray)
    public const string Post = "Kit_PanelPost";               // 64 mm connector post at panel joints
    public const string PostTall = "Kit_PanelPostTall";
    const float PostWidth = .064f;
    public const string Desk = "Kit_OfficeDesk";              // 1.524 x 0.762 m worksurface + pedestal
    public const string Monitor = "Kit_CRTMonitor";
    public const string PC = "Kit_PCDesktop";
    public const string Keyboard = "Kit_Keyboard";
    public const string Mouse = "Kit_Mouse";
    public const string Chair = "Kit_TaskChair";
    public const string Phone = "Kit_DeskPhone";
    public const string Paper = "Kit_PaperStack";
    public const string Binders = "Kit_Binders";
    public const string Bin = "Kit_TrashBin";
    public const string Vending = "Kit_VendingMachine";
    public const string Cooler = "Kit_WaterCooler";
    public const string Copier = "Kit_Copier";
    public const string Filing = "Kit_FilingCabinet";
    public const string Window = "Kit_InteriorWindow";

    // ------------------------------------------------------------- occupancy
    sealed class Occupancy
    {
        readonly Rect floor;
        readonly int w, h;
        readonly bool[] prop;      // physical obstacles
        readonly bool[] reserved;  // keepClear, service zones, aisles: walkable but not furnishable

        public Occupancy(Rect floor)
        {
            this.floor = floor;
            w = Mathf.Max(1, Mathf.CeilToInt(floor.width / Cell));
            h = Mathf.Max(1, Mathf.CeilToInt(floor.height / Cell));
            prop = new bool[w * h];
            reserved = new bool[w * h];
        }

        Occupancy(Occupancy o)
        {
            floor = o.floor; w = o.w; h = o.h;
            prop = (bool[])o.prop.Clone();
            reserved = (bool[])o.reserved.Clone();
        }

        public Occupancy Clone() => new Occupancy(this);

        void Range(Rect r, out int x0, out int y0, out int x1, out int y1)
        {
            x0 = Mathf.Max(0, Mathf.FloorToInt((r.xMin - floor.xMin) / Cell + 1e-3f));
            y0 = Mathf.Max(0, Mathf.FloorToInt((r.yMin - floor.yMin) / Cell + 1e-3f));
            x1 = Mathf.Min(w, Mathf.CeilToInt((r.xMax - floor.xMin) / Cell - 1e-3f));
            y1 = Mathf.Min(h, Mathf.CeilToInt((r.yMax - floor.yMin) / Cell - 1e-3f));
        }

        public bool Inside(Rect r) =>
            r.xMin >= floor.xMin - 1e-3f && r.yMin >= floor.yMin - 1e-3f && r.xMax <= floor.xMax + 1e-3f && r.yMax <= floor.yMax + 1e-3f;

        public bool Free(Rect r)
        {
            if (!Inside(r)) return false;
            Range(r, out var x0, out var y0, out var x1, out var y1);
            for (var y = y0; y < y1; y++)
                for (var x = x0; x < x1; x++)
                    if (prop[y * w + x] || reserved[y * w + x]) return false;
            return true;
        }

        /// <summary>Free of props only (a placement may border a reserved zone).</summary>
        public bool FreeOfProps(Rect r)
        {
            Range(r, out var x0, out var y0, out var x1, out var y1);
            for (var y = y0; y < y1; y++)
                for (var x = x0; x < x1; x++)
                    if (prop[y * w + x]) return false;
            return true;
        }

        public void TakeProp(Rect r) => Mark(prop, r);
        public void Reserve(Rect r) => Mark(reserved, r);

        void Mark(bool[] layer, Rect r)
        {
            Range(r, out var x0, out var y0, out var x1, out var y1);
            for (var y = y0; y < y1; y++)
                for (var x = x0; x < x1; x++)
                    layer[y * w + x] = true;
        }

        /// <summary>
        /// Every keepClear strip reachable from the first through cells at
        /// least clearance/2 from any prop (a capsule walking down the aisle).
        /// </summary>
        public bool Connected(Rect[] strips, float clearance)
        {
            if (strips == null || strips.Length < 2) return true;
            var walk = Walkable(clearance);
            var seen = Flood(strips[0], walk);
            for (var s = 1; s < strips.Length; s++)
                if (!Reached(strips[s], seen)) return false;
            return true;
        }

        /// <summary>
        /// The largest set of strips that are connected to each other. Used once per
        /// room when the obstacles handed in (module props, a pile) already cut the
        /// floor apart: dressing then keeps those strips joined instead of failing
        /// every placement. Returns the input unchanged in a normal room.
        /// </summary>
        public Rect[] Joined(Rect[] strips, float clearance)
        {
            if (strips == null || strips.Length < 2 || Connected(strips, clearance)) return strips;
            var walk = Walkable(clearance);
            var done = new bool[strips.Length];
            var best = new List<Rect>();
            for (var s = 0; s < strips.Length; s++)
            {
                if (done[s]) continue;
                var seen = Flood(strips[s], walk);
                var group = new List<Rect>();
                for (var t = 0; t < strips.Length; t++)
                    if (t == s || (!done[t] && Reached(strips[t], seen))) { group.Add(strips[t]); done[t] = true; }
                if (group.Count > best.Count) best = group;
            }
            return best.ToArray();
        }

        bool Reached(Rect strip, bool[] seen)
        {
            Range(strip, out var x0, out var y0, out var x1, out var y1);
            if (x1 <= x0 || y1 <= y0) return true;   // sub-cell strip: nothing to reach
            for (var y = y0; y < y1; y++)
                for (var x = x0; x < x1; x++)
                    if (seen[y * w + x]) return true;
            return false;
        }

        bool[] Flood(Rect from, bool[] walk)
        {
            var seen = new bool[w * h];
            var queue = new Queue<int>();
            Seed(from, walk, seen, queue);
            while (queue.Count > 0)
            {
                var i = queue.Dequeue();
                int x = i % w, y = i / w;
                Visit(x + 1, y, walk, seen, queue); Visit(x - 1, y, walk, seen, queue);
                Visit(x, y + 1, walk, seen, queue); Visit(x, y - 1, walk, seen, queue);
            }
            return seen;
        }

        /// <summary>Cells at least clearance/2 from any prop (a capsule walking down the aisle).</summary>
        bool[] Walkable(float clearance)
        {
            var r = Mathf.CeilToInt(clearance * .5f / Cell);
            var walk = new bool[w * h];
            for (var y = 0; y < h; y++)
                for (var x = 0; x < w; x++)
                {
                    var ok = true;
                    for (var dy = -r; dy <= r && ok; dy++)
                        for (var dx = -r; dx <= r && ok; dx++)
                        {
                            int xx = x + dx, yy = y + dy;
                            if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue; // walls are the strips' own business
                            if (prop[yy * w + xx]) ok = false;
                        }
                    walk[y * w + x] = ok;
                }
            return walk;
        }

        void Seed(Rect r, bool[] walk, bool[] seen, Queue<int> queue)
        {
            Range(r, out var x0, out var y0, out var x1, out var y1);
            for (var y = y0; y < y1; y++)
                for (var x = x0; x < x1; x++)
                    if (walk[y * w + x] && !seen[y * w + x]) { seen[y * w + x] = true; queue.Enqueue(y * w + x); }
        }

        void Visit(int x, int y, bool[] walk, bool[] seen, Queue<int> queue)
        {
            if (x < 0 || y < 0 || x >= w || y >= h) return;
            var i = y * w + x;
            if (seen[i] || !walk[i]) return;
            seen[i] = true;
            queue.Enqueue(i);
        }
    }

    /// <summary>Deterministic pseudo-random stream (no UnityEngine.Random state).</summary>
    sealed class Rng
    {
        uint state;
        public Rng(int seed) { state = (uint)seed * 2654435761u + 0x9E3779B9u; if (state == 0) state = 1; }
        public float Next() { state ^= state << 13; state ^= state >> 17; state ^= state << 5; return (state & 0xFFFFFF) / 16777216f; }
        public float Range(float a, float b) => a + (b - a) * Next();
        public int Range(int a, int bExclusive) => a + Mathf.Min(bExclusive - a - 1, (int)(Next() * (bExclusive - a)));
        public bool Chance(float p) => Next() < p;
        public void Shuffle<T>(IList<T> list) { for (var i = list.Count - 1; i > 0; i--) { var k = Range(0, i + 1); (list[i], list[k]) = (list[k], list[i]); } }
    }

    /// <summary>The map's 3 m cell lattice under this floor, if the rect is a map room.</summary>
    struct Lattice
    {
        public bool on;
        public int nx, nz;
        public Vector2 origin; // cell corner below-left of the floor

        public static Lattice Of(Rect f)
        {
            var nx = Mathf.RoundToInt((f.width + MapWall) / MapCell);
            var nz = Mathf.RoundToInt((f.height + MapWall) / MapCell);
            var on = nx >= 1 && nz >= 1
                && Mathf.Abs(nx * MapCell - MapWall - f.width) < .06f
                && Mathf.Abs(nz * MapCell - MapWall - f.height) < .06f;
            return new Lattice { on = on, nx = nx, nz = nz, origin = new Vector2(f.xMin - MapWall * .5f, f.yMin - MapWall * .5f) };
        }
    }

    struct WallSide
    {
        public Vector2 a, b;      // along the wall, in floor coordinates
        public Vector2 inward;
        public float yaw;         // kit front (+Z) turned toward the room
        public float Length => Vector2.Distance(a, b);
        public Vector2 Along => (b - a) / Mathf.Max(Length, 1e-4f);
    }

    // =================================================================== Dress

    /// <summary>
    /// Map path (LEVEL_MODULE_SPEC column rule v1): the map owns columns and
    /// passes their footprints as <paramref name="obstacles"/>; Dress treats
    /// them as occupied with a 0.45 m halo and places no columns itself.
    /// </summary>
    public static void Dress(Transform parent, Rect floorXZ, float ceilingHeight, int seed, Rect[] keepClear, Rect[] obstacles)
    {
        DressRoom(parent, floorXZ, ceilingHeight, seed, keepClear, obstacles ?? Array.Empty<Rect>(), placeColumns: false);
    }

    /// <summary>Look-dev / room-stream path: Dress places its own (0.9 m Office) columns.</summary>
    public static void Dress(Transform parent, Rect floorXZ, float ceilingHeight, int seed, Rect[] keepClear)
    {
        DressRoom(parent, floorXZ, ceilingHeight, seed, keepClear, Array.Empty<Rect>(), placeColumns: true);
    }

    static void DressRoom(Transform parent, Rect floorXZ, float ceilingHeight, int seed, Rect[] keepClear, Rect[] obstacles, bool placeColumns)
    {
        if (parent == null || floorXZ.width < 2.4f || floorXZ.height < 2.4f) return;
        var root = new GameObject("office dressing").transform;
        root.SetParent(parent, false);
        var rng = new Rng(seed);
        var occ = new Occupancy(floorXZ);
        var clear = ClipStrips(keepClear, floorXZ);
        foreach (var r in clear) occ.Reserve(Expand(r, .25f));
        foreach (var o in obstacles) { occ.TakeProp(o); occ.Reserve(Expand(o, .45f)); }
        // Obstacles from the map (module props, a pile) can already cut the strips
        // apart. Every strip stays reserved, but placements only have to keep the
        // largest still-joined set connected; otherwise every TryCommit fails and
        // the room is left empty.
        var joined = occ.Joined(clear, MinAisle);
        if (joined.Length < clear.Length)
            Debug.LogWarning("[FrontRoomsOfficeKit] Obstacles cut " + (clear.Length - joined.Length) + " strip(s) off; dressing round the rest.");
        clear = joined;
        var lattice = Lattice.Of(floorXZ);
        var sides = Sides(floorXZ);
        rng.Shuffle(sides);

        if (placeColumns) PlaceColumns(root, floorXZ, ceilingHeight, rng, occ, lattice, clear);
        PlaceWallUnits(root, floorXZ, ceilingHeight, rng, occ, clear, sides, lattice);
        // Every pod and wall row keeps a full chase lane (Aisle) to every other.
        var runs = new List<Rect>();
        var minSide = Mathf.Min(floorXZ.width, floorXZ.height);
        if (minSide < 7f) PlaceWallRows(root, floorXZ, rng, occ, clear, sides, 2, runs);
        else
        {
            PlacePods(root, floorXZ, rng, occ, clear, runs);
            PlaceWallRows(root, floorXZ, rng, occ, clear, sides, 1, runs);
        }
    }

    static Rect[] ClipStrips(Rect[] strips, Rect floor)
    {
        var list = new List<Rect>();
        if (strips != null)
            foreach (var s in strips)
            {
                var xMin = Mathf.Max(s.xMin, floor.xMin); var yMin = Mathf.Max(s.yMin, floor.yMin);
                var xMax = Mathf.Min(s.xMax, floor.xMax); var yMax = Mathf.Min(s.yMax, floor.yMax);
                if (xMax - xMin > .05f && yMax - yMin > .05f) list.Add(Rect.MinMaxRect(xMin, yMin, xMax, yMax));
            }
        return list.ToArray();
    }

    static List<WallSide> Sides(Rect f) => new List<WallSide>
    {
        // South wall (yMin) faces +Z, north faces -Z, west faces +X, east faces -X.
        new WallSide { a = new Vector2(f.xMin, f.yMin), b = new Vector2(f.xMax, f.yMin), inward = Vector2.up, yaw = 0f },
        new WallSide { a = new Vector2(f.xMax, f.yMax), b = new Vector2(f.xMin, f.yMax), inward = Vector2.down, yaw = 180f },
        new WallSide { a = new Vector2(f.xMin, f.yMax), b = new Vector2(f.xMin, f.yMin), inward = Vector2.right, yaw = 90f },
        new WallSide { a = new Vector2(f.xMax, f.yMin), b = new Vector2(f.xMax, f.yMax), inward = Vector2.left, yaw = -90f },
    };

    /// <summary>Commit a footprint only if every keepClear strip stays connected.</summary>
    static bool TryCommit(Occupancy occ, Rect[] clear, Rect footprint, Rect? service)
    {
        var trial = occ.Clone();
        trial.TakeProp(footprint);
        if (!trial.Connected(clear, MinAisle)) return false;
        occ.TakeProp(footprint);
        if (service.HasValue) occ.Reserve(service.Value);
        return true;
    }

    // ================================================================ columns

    static void PlaceColumns(Transform root, Rect floor, float ceiling, Rng rng, Occupancy occ, Lattice lattice, Rect[] clear)
    {
        // Few, structural columns (the map's rule v1 uses 0.9 m in Office zones):
        // interior cell corners of the map lattice, or a 6 m grid off the map.
        const float size = .9f;
        var candidates = new List<Vector2>();
        int max;
        if (lattice.on)
        {
            if (lattice.nx < 3 || lattice.nz < 3) return;
            max = lattice.nx >= 4 && lattice.nz >= 4 ? rng.Range(1, 5) : (rng.Chance(.6f) ? 1 : 0);
            for (var i = 1; i < lattice.nx; i++)
                for (var j = 1; j < lattice.nz; j++)
                    candidates.Add(lattice.origin + new Vector2(i * MapCell, j * MapCell));
        }
        else
        {
            if (floor.width < 9f || floor.height < 9f) return;
            max = floor.width * floor.height > 140f ? rng.Range(1, 5) : (rng.Chance(.6f) ? 1 : 0);
            for (var x = floor.xMin + 3f; x <= floor.xMax - 3f; x += 6f)
                for (var z = floor.yMin + 3f; z <= floor.yMax - 3f; z += 6f)
                    candidates.Add(new Vector2(x, z));
        }
        rng.Shuffle(candidates);
        var wall = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Wall);
        var cove = FrontRoomsSurfaces.CoveBase;
        var placed = 0;
        foreach (var c in candidates)
        {
            if (placed >= max) break;
            var footprint = new Rect(c.x - size * .5f, c.y - size * .5f, size, size);
            if (!occ.Free(footprint)) continue;
            if (!TryCommit(occ, clear, footprint, Expand(footprint, .45f))) continue;
            var column = new GameObject("office column").transform;
            column.SetParent(root, false);
            column.localPosition = new Vector3(c.x, 0f, c.y);
            Block(column, "column drywall", new Vector3(0f, ceiling * .5f, 0f), new Vector3(size, ceiling, size), wall, true);
            Block(column, "column cove base", new Vector3(0f, .05f, 0f), new Vector3(size + .02f, .1f, size + .02f), cove, false);
            placed++;
        }
    }

    // ============================================================= wall units

    static void PlaceWallUnits(Transform root, Rect floor, float ceiling, Rng rng, Occupancy occ, Rect[] clear, List<WallSide> sides, Lattice lattice)
    {
        var area = floor.width * floor.height;
        var wishes = new List<string>();
        if (ceiling >= 2.6f && rng.Chance(.5f)) wishes.Add(Window);
        if (rng.Chance(area > 60f ? .7f : .3f)) wishes.Add(Vending);
        if (rng.Chance(.65f)) wishes.Add(Cooler);
        if (rng.Chance(area > 50f ? .6f : .25f)) wishes.Add(Copier);
        var filingRun = area > 40f ? rng.Range(2, 5) : rng.Range(0, 3);

        var sideIndex = 0;
        foreach (var asset in wishes)
        {
            if (!PlaceOnWall(root, asset, rng, occ, clear, sides, sideIndex, lattice, ceiling, out _)) sideIndex++;
            else sideIndex += rng.Range(0, 2);
        }
        // Filing cabinets stand side by side in one run.
        if (filingRun > 0 && FrontRoomsKitLibrary.GetInfo(Filing) is FrontRoomsKitLibrary.Info filing)
        {
            if (PlaceOnWall(root, Filing, rng, occ, clear, sides, sideIndex + 1, lattice, ceiling, out var first))
            {
                var width = filing.Size.x + .01f;
                for (var i = 1; i < filingRun; i++)
                {
                    var c = first.centre + first.side.Along * width * i;
                    if (!TryWallAt(root, Filing, occ, clear, first.side, c, ceiling, filing)) break;
                }
            }
        }
    }

    struct WallSpot { public WallSide side; public Vector2 centre; }

    static bool PlaceOnWall(Transform root, string asset, Rng rng, Occupancy occ, Rect[] clear, List<WallSide> sides, int startSide, Lattice lattice, float ceiling, out WallSpot spot)
    {
        spot = default;
        var info = FrontRoomsKitLibrary.GetInfo(asset);
        if (info == null) return false;
        var halfW = info.HalfFootprint.x;
        for (var s = 0; s < sides.Count; s++)
        {
            var side = sides[(startSide + s) % sides.Count];
            var length = side.Length;
            if (length < halfW * 2f + .4f) continue;
            var positions = new List<float>();
            if (asset == Window && lattice.on)
            {
                // Centre on a single cell's wall stretch so no perpendicular wall lands on it.
                var aAlong = Vector2.Dot(side.a - lattice.origin, side.Along);
                for (var k = 0; k < 8; k++)
                {
                    var t = MapCell * (k + .5f) - aAlong;
                    if (t > halfW + .1f && t < length - halfW - .1f) positions.Add(t);
                }
            }
            else
                for (var k = 0; k < 8; k++) positions.Add(rng.Range(halfW + .2f, length - halfW - .2f));
            rng.Shuffle(positions);
            foreach (var t in positions)
            {
                var basePoint = side.a + side.Along * t;
                if (TryWallAt(root, asset, occ, clear, side, basePoint, ceiling, info))
                {
                    spot = new WallSpot { side = side, centre = basePoint };
                    return true;
                }
            }
        }
        return false;
    }

    static bool TryWallAt(Transform root, string asset, Occupancy occ, Rect[] clear, WallSide side, Vector2 basePoint, float ceiling, FrontRoomsKitLibrary.Info info)
    {
        var halfW = info.HalfFootprint.x;
        var depth = info.Depth;
        var isWindow = asset == Window;
        // Windows are set 2 cm into the wall face; everything else stands 3 cm off it.
        var centre = basePoint + side.inward * (isWindow ? depth * .5f - .02f : depth * .5f + .03f);
        var footprint = FootprintRect(centre, side.Along, side.inward, halfW, Mathf.Max(depth * .5f, .06f));
        var service = isWindow ? footprint : FootprintRect(centre + side.inward * (depth * .5f + .25f), side.Along, side.inward, halfW, .25f);
        if (!occ.Inside(footprint) || !occ.Free(isWindow ? footprint : Union(footprint, service))) return false;
        if (TouchesClear(Expand(footprint, isWindow ? .5f : .1f), clear)) return false;
        if (isWindow) occ.Reserve(footprint);
        else if (!TryCommit(occ, clear, footprint, service)) return false;
        // Spec: decor window sill at 0.90 m (lower only if the ceiling is low).
        var y = isWindow ? Mathf.Min(.90f, ceiling - info.Height - .25f) : 0f;
        FrontRoomsKitLibrary.Spawn(asset, root, new Vector3(centre.x, y, centre.y), side.yaw, null, !isWindow);
        return true;
    }

    // ================================================================== rows

    /// <summary>1-3 stations side by side with their back panels on a wall.</summary>
    static bool LaneClear(List<Rect> runs, Rect rect)
    {
        foreach (var r in runs) if (Expand(r, Aisle).Overlaps(rect)) return false;
        return true;
    }

    static void PlaceWallRows(Transform root, Rect floor, Rng rng, Occupancy occ, Rect[] clear, List<WallSide> sides, int maxRows, List<Rect> runs)
    {
        var desk = FrontRoomsKitLibrary.GetInfo(Desk);
        if (desk == null) return;
        var stationW = Mathf.Max(1.5f, desk.Size.x) + PostWidth; // desk + one connector post
        var stationD = Mathf.Max(.75f, desk.Size.z) + .94f;
        var rows = 0;
        foreach (var side in sides)
        {
            if (rows >= maxRows) break;
            var fit = Mathf.FloorToInt((side.Length - 1.2f) / stationW);
            if (fit < 1) continue;
            var count = Mathf.Min(fit, rng.Range(1, 4));
            var span = count * stationW;
            for (var attempt = 0; attempt < 6; attempt++)
            {
                var t = rng.Range(.6f + span * .5f, side.Length - .6f - span * .5f);
                var mid = side.a + side.Along * t;
                var centre = mid + side.inward * stationD * .5f;
                var footprint = FootprintRect(centre, side.Along, side.inward, span * .5f + .05f, stationD * .5f);
                var aisle = FootprintRect(centre + side.inward * (stationD * .5f + .5f), side.Along, side.inward, span * .5f, .5f);
                if (!occ.Free(Union(footprint, aisle)) || TouchesClear(footprint, clear) || !LaneClear(runs, footprint)) continue;
                if (!TryCommit(occ, clear, footprint, aisle)) continue;
                runs.Add(footprint);
                var row = new GameObject("cubicle row").transform;
                row.SetParent(root, false);
                row.localPosition = new Vector3(mid.x, 0f, mid.y) + new Vector3(side.inward.x, 0f, side.inward.y) * .045f;
                row.localRotation = Quaternion.Euler(0f, side.yaw, 0f);
                BuildRun(row, count, 1, stationW, stationD, rng, back: true);
                rows++;
                break;
            }
        }
    }

    // ================================================================== pods

    static void PlacePods(Transform root, Rect floor, Rng rng, Occupancy occ, Rect[] clear, List<Rect> runs)
    {
        var desk = FrontRoomsKitLibrary.GetInfo(Desk);
        if (desk == null) return;
        var stationW = Mathf.Max(1.5f, desk.Size.x) + PostWidth; // desk + one connector post
        var stationD = Mathf.Max(.75f, desk.Size.z) + .94f;
        // A planned cubicle farm (the reference office): pods in rows along the
        // room's long axis, separated by exact chase lanes, 1.05 m off the walls.
        var alongX = floor.width >= floor.height;
        var longLen = alongX ? floor.width : floor.height;
        var shortLen = alongX ? floor.height : floor.width;
        var rows = shortLen >= 2 * stationD + 2.1f + Aisle ? 2 : 1;
        var cols = longLen >= 2 * stationW + 2.1f ? 2 : 1;
        var podLong = cols * stationW + PostWidth;
        var podShort = rows * stationD + .07f;
        var nLong = Mathf.Max(0, Mathf.FloorToInt((longLen - 2.1f + Aisle) / (podLong + Aisle)));
        var nShort = Mathf.Max(0, Mathf.FloorToInt((shortLen - 2.1f + Aisle) / (podShort + Aisle)));
        var placed = 0;
        if (nLong > 0 && nShort > 0)
        {
            var spanLong = nLong * podLong + (nLong - 1) * Aisle;
            var spanShort = nShort * podShort + (nShort - 1) * Aisle;
            var startLong = (longLen - spanLong) * .5f;
            var startShort = (shortLen - spanShort) * .5f;
            for (var i = 0; i < nLong; i++)
                for (var j = 0; j < nShort; j++)
                {
                    if (rng.Chance(.08f)) continue; // an emptied bay, as in a half-vacated floor
                    var a0 = startLong + i * (podLong + Aisle);
                    var b0 = startShort + j * (podShort + Aisle);
                    // Try the full pod, then a single-column pod in the same bay.
                    for (var variant = 0; variant < 2; variant++)
                    {
                        var c = variant == 0 ? cols : 1;
                        var pl = c * stationW + PostWidth;
                        var la = a0 + (podLong - pl) * .5f;
                        var rect = alongX ? new Rect(floor.xMin + la, floor.yMin + b0, pl, podShort)
                                          : new Rect(floor.xMin + b0, floor.yMin + la, podShort, pl);
                        var halo = Expand(rect, Aisle * .5f);
                        if (!occ.Free(rect) || !occ.FreeOfProps(halo) || !LaneClear(runs, rect)) continue;
                        if (!TryCommit(occ, clear, rect, halo)) continue;
                        runs.Add(rect);
                        var pod = new GameObject("cubicle pod").transform;
                        pod.SetParent(root, false);
                        pod.localPosition = new Vector3(rect.center.x, 0f, rect.center.y);
                        pod.localRotation = Quaternion.Euler(0f, alongX ? 0f : 90f, 0f);
                        BuildRun(pod, c, rows, stationW, stationD, rng, back: false, tall: rng.Chance(.15f) && FrontRoomsKitLibrary.Has(PanelTall));
                        placed++;
                        break;
                    }
                }
        }
        if (placed > 0) return;
        // Odd-shaped rooms: fall back to scattered pods.
        for (var tries = 0; tries < 40 && placed < 4; tries++)
        {
            var c = rng.Range(1, 3);
            var r = rng.Chance(.7f) ? 2 : 1;
            var ax = floor.width >= floor.height ? rng.Chance(.75f) : rng.Chance(.25f);
            var pw = c * stationW + PostWidth;
            var pd = r * stationD + .07f;
            var w = ax ? pw : pd;
            var d = ax ? pd : pw;
            var xMin = floor.xMin + 1.05f; var xMax = floor.xMax - 1.05f - w;
            var zMin = floor.yMin + 1.05f; var zMax = floor.yMax - 1.05f - d;
            if (xMax < xMin || zMax < zMin) continue;
            var rect = new Rect(Snap(rng.Range(xMin, xMax)), Snap(rng.Range(zMin, zMax)), w, d);
            var halo = Expand(rect, Aisle * .5f);
            if (!occ.Free(rect) || !occ.FreeOfProps(halo) || !LaneClear(runs, rect)) continue;
            if (!TryCommit(occ, clear, rect, halo)) continue;
            runs.Add(rect);
            var pod = new GameObject("cubicle pod").transform;
            pod.SetParent(root, false);
            pod.localPosition = new Vector3(rect.center.x, 0f, rect.center.y);
            pod.localRotation = Quaternion.Euler(0f, ax ? 0f : 90f, 0f);
            BuildRun(pod, c, r, stationW, stationD, rng, back: false, tall: rng.Chance(.15f) && FrontRoomsKitLibrary.Has(PanelTall));
            placed++;
        }
    }

    /// <summary>
    /// cols stations wide, rows deep (2 = back to back over a shared spine).
    /// Local frame: x along the stations, z across; row 0 faces +Z. With
    /// back = true the spine sits at z = 0 (a wall row), otherwise the run is
    /// centred on the origin.
    /// </summary>
    static void BuildRun(Transform run, int cols, int rows, float stationW, float stationD, Rng rng, bool back, bool tall = false)
    {
        var halfW = cols * stationW * .5f;
        var spine = back ? 0f : (rows == 2 ? 0f : -stationD * .5f);
        var panel = FrontRoomsKitLibrary.GetInfo(PanelShort);
        var endDepth = panel != null ? panel.Size.x : .762f;
        for (var r = 0; r < rows; r++)
        {
            var facing = r == 0 ? 1f : -1f;
            for (var c = 0; c < cols; c++)
            {
                var station = new GameObject("workstation").transform;
                station.SetParent(run, false);
                station.localPosition = new Vector3(-halfW + stationW * (c + .5f), 0f, spine);
                station.localRotation = Quaternion.Euler(0f, facing > 0 ? 0f : 180f, 0f);
                BuildStation(station, stationW, rng);
            }
            // Side panels the depth of the desk, at each end and between stations.
            var z = spine + facing * (endDepth * .5f + .035f);
            for (var c = 0; c <= cols; c++)
                FrontRoomsKitLibrary.Spawn(PanelShort, run, new Vector3(-halfW + stationW * c, 0f, z), 90f, null, true, c == 0 || c == cols ? "end panel" : "divider panel");
        }
        // Spine panels between the posts; tall pods block the Relay's sight.
        for (var c = 0; c < cols; c++)
            FrontRoomsKitLibrary.Spawn(tall ? PanelTall : Panel, run, new Vector3(-halfW + stationW * (c + .5f), 0f, spine), 0f, null, true, "spine panel");
        for (var c = 0; c <= cols; c++)
            FrontRoomsKitLibrary.Spawn(tall ? PostTall : Post, run, new Vector3(-halfW + stationW * c, 0f, spine), 0f, null, false, "panel post");
    }

    /// <summary>One desk in station space: back panel at z = 0, user side +Z.</summary>
    static void BuildStation(Transform station, float stationW, Rng rng)
    {
        var desk = FrontRoomsKitLibrary.GetInfo(Desk);
        var deskDepth = desk != null ? desk.Size.z : .762f;
        var deskZ = deskDepth * .5f + .045f;
        FrontRoomsKitLibrary.Spawn(Desk, station, new Vector3(0f, 0f, deskZ), 0f);
        var top = .74f;
        if (desk != null && desk.TrySupport("top", out var topCentre, out _)) top = topCentre.y;
        var side = rng.Chance(.5f) ? -1f : 1f;
        if (!rng.Chance(.12f))
        {
            // Monitor toward the back corner, keyboard and mouse in front of it.
            var monitorX = side * stationW * .16f;
            var onCase = rng.Chance(.5f) && FrontRoomsKitLibrary.Has(PC);
            var monitorY = top;
            if (onCase)
            {
                FrontRoomsKitLibrary.Spawn(PC, station, new Vector3(monitorX, top, deskZ - .1f), rng.Range(-3f, 3f));
                var pc = FrontRoomsKitLibrary.GetInfo(PC);
                monitorY += pc != null && pc.TrySupport("top", out var pcCentre, out _) ? pcCentre.y : .13f;
            }
            FrontRoomsKitLibrary.Spawn(Monitor, station, new Vector3(monitorX, monitorY, deskZ - .1f), rng.Range(-9f, 9f));
            FrontRoomsKitLibrary.Spawn(Keyboard, station, new Vector3(monitorX + rng.Range(-.04f, .04f), top, deskZ + .2f), rng.Range(-6f, 6f), null, false);
            FrontRoomsKitLibrary.Spawn(Mouse, station, new Vector3(monitorX + .3f, top, deskZ + .22f), rng.Range(-30f, 30f), null, false);
            if (rng.Chance(.6f)) FrontRoomsKitLibrary.Spawn(Paper, station, new Vector3(-side * stationW * .3f, top, deskZ + rng.Range(-.12f, .12f)), rng.Range(-25f, 25f), null, false);
            if (rng.Chance(.45f)) FrontRoomsKitLibrary.Spawn(Phone, station, new Vector3(-side * stationW * .1f, top, deskZ - .18f), rng.Range(-20f, 20f), null, false);
            if (rng.Chance(.35f)) FrontRoomsKitLibrary.Spawn(Binders, station, new Vector3(-side * stationW * .38f, top, deskZ - .24f), rng.Range(-5f, 5f), null, false);
        }
        if (rng.Chance(.85f))
        {
            // Chairs are left where people stood up: pushed out, turned.
            var chairZ = deskZ + deskDepth * .5f + rng.Range(.15f, .55f);
            FrontRoomsKitLibrary.Spawn(Chair, station, new Vector3(rng.Range(-.25f, .25f), 0f, chairZ), 180f + rng.Range(-50f, 50f));
        }
        if (rng.Chance(.5f)) FrontRoomsKitLibrary.Spawn(Bin, station, new Vector3(side * stationW * .36f, 0f, deskZ - .12f), rng.Range(0f, 360f));
    }

    // ================================================================ helpers

    static float Snap(float v) => Mathf.Round(v / Cell) * Cell;

    static Rect Expand(Rect r, float m) => new Rect(r.xMin - m, r.yMin - m, r.width + 2 * m, r.height + 2 * m);

    static Rect Union(Rect a, Rect b) => Rect.MinMaxRect(Mathf.Min(a.xMin, b.xMin), Mathf.Min(a.yMin, b.yMin), Mathf.Max(a.xMax, b.xMax), Mathf.Max(a.yMax, b.yMax));

    static Rect FootprintRect(Vector2 centre, Vector2 along, Vector2 inward, float halfAlong, float halfIn)
    {
        var ex = Mathf.Abs(along.x) * halfAlong + Mathf.Abs(inward.x) * halfIn;
        var ez = Mathf.Abs(along.y) * halfAlong + Mathf.Abs(inward.y) * halfIn;
        return new Rect(centre.x - ex, centre.y - ez, ex * 2f, ez * 2f);
    }

    static bool TouchesClear(Rect r, Rect[] clear)
    {
        foreach (var c in clear) if (c.Overlaps(r)) return true;
        return false;
    }

    static GameObject Block(Transform parent, string name, Vector3 position, Vector3 size, Material material, bool collider)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localScale = size;
        if (!collider)
        {
            var c = go.GetComponent<Collider>();
            if (Application.isPlaying) UnityEngine.Object.Destroy(c); else UnityEngine.Object.DestroyImmediate(c);
        }
        go.GetComponent<MeshRenderer>().sharedMaterial = material;
        return go;
    }
}
