using System;
using System.Collections.Generic;

namespace FrontRooms.Map
{
    [Serializable]
    public sealed class MapSeedReport
    {
        public int seed;
        public bool passed;
        public int cells;
        public int reachable;
        public int zones;
        public int lowZones;
        public int standardZones;
        public int tallZones;
        public int keys;
        public int open;
        public int arch;
        public int wall;
        public int door;
        public int window;
        public int pillars;
        public int modulesPlaced;
        public List<string> errors = new List<string>();
    }

    [Serializable]
    public sealed class MapVerificationReport
    {
        public string suite = "FrontRooms map data";
        public string scope = "Generated cells, edges, zones, pillars and keys for a square of chunks per seed. Geometry, rendering and human playability are separate.";
        public string timestampUtc;
        public int radiusChunks;
        public int seedCount;
        public int passed;
        public int failed;
        public List<MapSeedReport> seeds = new List<MapSeedReport>();
    }

    /// <summary>
    /// Checks the rules the rest of the game relies on. For each seed it builds
    /// the chunks in [-radius, radius) on both axes and verifies:
    /// neighbours agree on every shared edge; every cell is reachable when
    /// walls are the only blockers; doors and windows appear only where the
    /// ceiling height changes; every key zone with cells in the square has a
    /// key inside it; a rebuilt chunk is identical; and a shifted chunk keeps
    /// its borders.
    /// </summary>
    public static class FrontRoomsMapValidator
    {
        public static MapVerificationReport Run(MapSettings settings, int firstSeed, int seedCount, int radius, IReadOnlyList<RoomModuleData> modules = null)
        {
            var report = new MapVerificationReport { radiusChunks = radius, seedCount = seedCount, timestampUtc = DateTime.UtcNow.ToString("o") };
            for (var i = 0; i < seedCount; i++)
            {
                var s = (settings ?? new MapSettings()).Clone();
                s.seed = unchecked(firstSeed + i * 7919);
                var result = ValidateSeed(s, radius, modules);
                report.seeds.Add(result);
                if (result.passed) report.passed++; else report.failed++;
            }
            return report;
        }

        public static MapSeedReport ValidateSeed(MapSettings settings, int radius, IReadOnlyList<RoomModuleData> modules = null)
        {
            var report = new MapSeedReport { seed = settings.seed };
            var cache = new FrontRoomsMapCache(settings, modules);
            var gen = cache.Generator;
            const int n = MapGrid.ChunkCells;
            int min = -radius, max = radius;
            for (var cy = min; cy < max; cy++)
            for (var cx = min; cx < max; cx++)
            {
                var built = cache.Get(new GridCoord(cx, cy));
                for (var r = 0; r < built.rooms.Length; r++) if (built.ModuleOf(r) != null) report.modulesPlaced++;
            }

            void Fail(string message) { if (report.errors.Count < 12) report.errors.Add(message); }

            // 1. Neighbours agree on shared border edges and border pillars.
            for (var cy = min; cy < max; cy++)
            for (var cx = min; cx < max; cx++)
            {
                var c = cache.Get(new GridCoord(cx, cy));
                if (cx + 1 < max)
                {
                    var e = cache.Get(new GridCoord(cx + 1, cy));
                    for (var k = 0; k < n; k++)
                        if (c.east[MapGrid.LocalIndex(n - 1, k)] != e.west[k]) Fail("border east of chunk " + c.coord + " row " + k);
                    for (var k = 0; k <= n; k++)
                        if (c.pillar[n + k * (n + 1)] != e.pillar[k * (n + 1)]) Fail("pillar on east border of chunk " + c.coord);
                }
                if (cy + 1 < max)
                {
                    var u = cache.Get(new GridCoord(cx, cy + 1));
                    for (var k = 0; k < n; k++)
                        if (c.north[MapGrid.LocalIndex(k, n - 1)] != u.south[k]) Fail("border north of chunk " + c.coord + " column " + k);
                    for (var k = 0; k <= n; k++)
                        if (c.pillar[k + n * (n + 1)] != u.pillar[k]) Fail("pillar on north border of chunk " + c.coord);
                }
            }

            // 2. Reachability and 3. zone rules, over every cell and edge in the square.
            int x0 = min * n, x1 = max * n, y0 = min * n, y1 = max * n;
            int w = x1 - x0, h = y1 - y0;
            report.cells = w * h;
            var seen = new bool[w * h];
            var queue = new Queue<GridCoord>();
            var start = new GridCoord(x0, y0);
            seen[0] = true;
            queue.Enqueue(start);
            while (queue.Count > 0)
            {
                var cell = queue.Dequeue();
                report.reachable++;
                Visit(cell, new GridCoord(cell.x + 1, cell.y));
                Visit(cell, new GridCoord(cell.x - 1, cell.y));
                Visit(cell, new GridCoord(cell.x, cell.y + 1));
                Visit(cell, new GridCoord(cell.x, cell.y - 1));
            }
            void Visit(GridCoord from, GridCoord to)
            {
                if (to.x < x0 || to.x >= x1 || to.y < y0 || to.y >= y1) return;
                var index = (to.x - x0) + (to.y - y0) * w;
                if (seen[index] || !MapGrid.Passable(cache.Edge(from, to))) return;
                seen[index] = true;
                queue.Enqueue(to);
            }
            if (report.reachable != report.cells) Fail("only " + report.reachable + " of " + report.cells + " cells reachable");

            var zonesWithCells = new HashSet<GridCoord>();
            for (var y = y0; y < y1; y++)
            for (var x = x0; x < x1; x++)
            {
                var cell = new GridCoord(x, y);
                zonesWithCells.Add(gen.ZoneOf(cell).id);
                if (x + 1 < x1) CheckEdge(cell, new GridCoord(x + 1, y));
                if (y + 1 < y1) CheckEdge(cell, new GridCoord(x, y + 1));
                if (x > x0 && y > y0)
                {
                    var c = cache.Get(MapGrid.ChunkOf(cell));
                    var o = c.Origin;
                    if (c.pillar[(x - o.x) + (y - o.y) * (n + 1)])
                    {
                        report.pillars++;
                        // 7. Columns stand strictly inside an intact room: on the 6 m grid and
                        // never in a Low zone, unless a module placed its own.
                        var owner = -1;
                        for (var r = 0; r < c.rooms.Length && owner < 0; r++)
                        {
                            var room = c.rooms[r];
                            if (c.RoomIntact(r) && x - o.x > room.x && x - o.x < room.x + room.w && y - o.y > room.y && y - o.y < room.y + room.h) owner = r;
                        }
                        var custom = owner >= 0 && c.ModuleOf(owner) != null && c.ModuleOf(owner).columns == ModuleColumns.Custom;
                        if (owner < 0 || (!custom && !gen.Uniform(c, c.rooms[owner]))) Fail("column outside an intact room at " + cell);
                        if (!custom && !FrontRoomsMapGenerator.OnColumnGrid(cell)) Fail("column off the 6 m grid at " + cell);
                        if (!custom && gen.HeightOf(cell) == ZoneHeight.Low) Fail("column in a Low zone at " + cell);
                    }
                }
            }
            void CheckEdge(GridCoord a, GridCoord b)
            {
                var kind = cache.Edge(a, b);
                switch (kind)
                {
                    case EdgeKind.Open: report.open++; break;
                    case EdgeKind.Arch: report.arch++; break;
                    case EdgeKind.Wall: report.wall++; break;
                    case EdgeKind.Door: report.door++; break;
                    case EdgeKind.Window: report.window++; break;
                }
                var ha = gen.HeightOf(a);
                var hb = gen.HeightOf(b);
                if (ha == hb && (kind == EdgeKind.Door || kind == EdgeKind.Window)) Fail(kind + " between two " + ha + " cells at " + a + "-" + b);
                if (ha != hb && (kind == EdgeKind.Open || kind == EdgeKind.Arch)) Fail(kind + " across a height change at " + a + "-" + b);
                var tall = ha == ZoneHeight.Tall || hb == ZoneHeight.Tall;
                if (kind == EdgeKind.Door && tall) Fail("door into a tall zone at " + a + "-" + b);
                if (kind == EdgeKind.Window && !tall) Fail("window without a tall zone at " + a + "-" + b);
            }

            // 4. Keys: every low or standard zone whose site is in the square
            // carries a key that sits inside the zone itself.
            foreach (var id in zonesWithCells)
            {
                if (id.x < min || id.x >= max || id.y < min || id.y >= max) continue;
                var zone = gen.Zone(id);
                report.zones++;
                if (zone.height == ZoneHeight.Low) report.lowZones++;
                else if (zone.height == ZoneHeight.Standard) report.standardZones++;
                else report.tallZones++;
                var home = cache.Get(id);
                if (zone.height == ZoneHeight.Tall)
                {
                    if (home.hasKey) Fail("tall zone " + id + " has a key");
                    continue;
                }
                if (!home.hasKey) { Fail("zone " + id + " has no key"); continue; }
                report.keys++;
                if (gen.ZoneOf(home.keyCell).id != id) Fail("key of zone " + id + " lies outside it at " + home.keyCell);
            }

            // 5. Determinism: a fresh generator building in a different order
            // produces identical chunks. 6. A shifted chunk keeps its borders.
            var fresh = new FrontRoomsMapGenerator(settings, modules);
            for (var cy = max - 1; cy >= min; cy -= 3)
            for (var cx = max - 1; cx >= min; cx -= 3)
            {
                var coord = new GridCoord(cx, cy);
                var a = cache.Get(coord);
                var b = fresh.Generate(coord);
                if (!Same(a.east, b.east) || !Same(a.north, b.north) || !Same(a.west, b.west) || !Same(a.south, b.south) || !Same(a.pillar, b.pillar) || !Same(a.pillarStyle, b.pillarStyle) || a.keyCell != b.keyCell || a.keySpot != b.keySpot || a.keyX != b.keyX || a.keyZ != b.keyZ || a.keyY != b.keyY || a.tier != b.tier
                    || !Same(a.rooms, b.rooms) || !Same(a.lamp, b.lamp) || !SameModules(a, b))
                    Fail("chunk " + coord + " differs when rebuilt");
                var shifted = fresh.Generate(coord, 1);
                for (var k = 0; k < n; k++)
                {
                    if (shifted.east[MapGrid.LocalIndex(n - 1, k)] != a.east[MapGrid.LocalIndex(n - 1, k)] || shifted.west[k] != a.west[k]
                        || shifted.north[MapGrid.LocalIndex(k, n - 1)] != a.north[MapGrid.LocalIndex(k, n - 1)] || shifted.south[k] != a.south[k])
                        Fail("shifted chunk " + coord + " changed a border");
                }
            }

            report.passed = report.errors.Count == 0;
            return report;
        }

        /// <summary>The same modules in the same rooms, by value (every generator clones its library).</summary>
        static bool SameModules(MapChunk a, MapChunk b)
        {
            if (a.rooms.Length != b.rooms.Length) return false;
            for (var r = 0; r < a.rooms.Length; r++)
            {
                RoomModuleData x = a.ModuleOf(r), y = b.ModuleOf(r);
                if ((x == null) != (y == null)) return false;
                if (x != null && (x.width != y.width || x.depth != y.depth || !Same(x.lamps, y.lamps) || !Same(x.props, y.props) || !Same(x.markers, y.markers)
                    || !Same(x.innerEast, y.innerEast) || !Same(x.innerNorth, y.innerNorth))) return false;
            }
            return true;
        }

        static bool Same<T>(T[] a, T[] b)
        {
            if (a.Length != b.Length) return false;
            var comparer = EqualityComparer<T>.Default;
            for (var i = 0; i < a.Length; i++) if (!comparer.Equals(a[i], b[i])) return false;
            return true;
        }
    }
}
