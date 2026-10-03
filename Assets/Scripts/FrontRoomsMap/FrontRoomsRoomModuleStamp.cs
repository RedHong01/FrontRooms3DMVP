using System;
using System.Collections.Generic;

namespace FrontRooms.Map
{
    /// <summary>
    /// Writes a room module into a generated chunk. The one way modules reach
    /// the map: the Level Designer preview uses it now, the generator will use
    /// it to place modules (P3), so what the designer sees is what the game builds.
    ///
    /// It keeps the map's guarantees:
    /// - only edges inside the chunk change: chunk borders are shared with the
    ///   neighbours and stay as generated;
    /// - where a module edge meets a zone of another height the map's rule
    ///   stands (door, window or wall);
    /// - the module becomes the chunk's last room, so it is one open space
    ///   (generated rooms it cuts into are no longer dressed);
    /// - columns are re-placed for every room (the module's own mode for it);
    /// - if the module's walls cut the chunk apart, walls are opened to join it
    ///   again, generated ones first, then the module's perimeter, its inside last.
    /// </summary>
    public static class RoomModuleStamp
    {
        const int N = MapGrid.ChunkCells;

        /// <summary>
        /// Stamp <paramref name="module"/> with its south-west cell at chunk-local
        /// (x0, y0). False, with the chunk unchanged, if the footprint leaves the
        /// chunk or a cell's height or theme differs from the module's.
        /// </summary>
        public static bool Apply(FrontRoomsMapGenerator generator, MapChunk chunk, RoomModuleData module, int x0, int y0)
        {
            if (generator == null || chunk == null || module == null) return false;
            module.Normalize();
            int w = module.width, d = module.depth;
            if (x0 < 0 || y0 < 0 || x0 + w > N || y0 + d > N) return false;
            for (var j = y0; j < y0 + d; j++)
            for (var i = x0; i < x0 + w; i++)
            {
                var zone = generator.ZoneOf(chunk.Cell(i, j));
                if (zone.height != module.height || zone.theme != module.theme) return false;
            }

            // Edge ownership for the repair: 1 = module perimeter, 2 = module inside.
            var owner = new byte[2 * N * N];
            for (var j = 0; j < d; j++)
            for (var i = 0; i < w - 1; i++)
                Set(chunk, owner, x0 + i, y0 + j, true, module.innerEast[i + j * (w - 1)], 2);
            for (var j = 0; j < d - 1; j++)
            for (var i = 0; i < w; i++)
                Set(chunk, owner, x0 + i, y0 + j, false, module.innerNorth[i + j * w], 2);
            for (var i = 0; i < w; i++)
            {
                if (y0 > 0 && SameHeight(generator, chunk, x0 + i, y0 - 1, module.height))
                    Set(chunk, owner, x0 + i, y0 - 1, false, module.south[i], 1);
                if (y0 + d < N && SameHeight(generator, chunk, x0 + i, y0 + d, module.height))
                    Set(chunk, owner, x0 + i, y0 + d - 1, false, module.north[i], 1);
            }
            for (var j = 0; j < d; j++)
            {
                if (x0 > 0 && SameHeight(generator, chunk, x0 - 1, y0 + j, module.height))
                    Set(chunk, owner, x0 - 1, y0 + j, true, module.west[j], 1);
                if (x0 + w < N && SameHeight(generator, chunk, x0 + w, y0 + j, module.height))
                    Set(chunk, owner, x0 + w - 1, y0 + j, true, module.east[j], 1);
            }

            // The module is the last room, so no later room cuts into it.
            var rooms = new List<CellRect>(chunk.rooms) { new CellRect(x0, y0, w, d) };
            var modules = new List<RoomModuleData>(chunk.roomModules ?? new RoomModuleData[0]);
            while (modules.Count < rooms.Count - 1) modules.Add(null);
            modules.Add(module);
            chunk.rooms = rooms.ToArray();
            chunk.roomModules = modules.ToArray();

            for (var j = 0; j < d; j++)
            for (var i = 0; i < w; i++)
                chunk.lamp[MapGrid.LocalIndex(x0 + i, y0 + j)] = module.LampAt(i, j);

            generator.PlaceColumns(chunk, chunk.revision);
            Reconnect(generator, chunk, owner);
            return true;
        }

        static bool SameHeight(FrontRoomsMapGenerator generator, MapChunk chunk, int i, int j, ZoneHeight height) =>
            generator.HeightOf(chunk.Cell(i, j)) == height;

        static void Set(MapChunk chunk, byte[] owner, int i, int j, bool east, ModuleEdge kind, byte by)
        {
            var index = MapGrid.LocalIndex(i, j);
            if (east) chunk.east[index] = RoomModuleData.ToEdge(kind);
            else chunk.north[index] = RoomModuleData.ToEdge(kind);
            owner[(east ? 0 : N * N) + index] = by;
        }

        /// <summary>
        /// Join the chunk's cells into one piece again. Each round opens the
        /// cheapest wall between two pieces: generated walls first, then the
        /// module's perimeter, its inside last; between two heights it opens as
        /// the map's exit (door, or window next to a tall zone).
        /// </summary>
        static void Reconnect(FrontRoomsMapGenerator generator, MapChunk chunk, byte[] owner)
        {
            var parent = new int[N * N];
            while (true)
            {
                for (var k = 0; k < parent.Length; k++) parent[k] = k;
                int Find(int k) { while (parent[k] != k) k = parent[k] = parent[parent[k]]; return k; }
                for (var j = 0; j < N; j++)
                for (var i = 0; i < N; i++)
                {
                    var k = MapGrid.LocalIndex(i, j);
                    if (i < N - 1 && MapGrid.Passable(chunk.east[k])) parent[Find(k)] = Find(k + 1);
                    if (j < N - 1 && MapGrid.Passable(chunk.north[k])) parent[Find(k)] = Find(k + N);
                }
                var root = Find(0);
                var joined = true;
                for (var k = 1; k < parent.Length && joined; k++) joined = Find(k) == root;
                if (joined) return;

                var best = -1;
                var bestCost = int.MaxValue;
                for (var j = 0; j < N; j++)
                for (var i = 0; i < N; i++)
                {
                    var k = MapGrid.LocalIndex(i, j);
                    if (i < N - 1 && chunk.east[k] == EdgeKind.Wall && Find(k) != Find(k + 1) && owner[k] < bestCost) { best = k; bestCost = owner[k]; }
                    if (j < N - 1 && chunk.north[k] == EdgeKind.Wall && Find(k) != Find(k + N) && owner[N * N + k] < bestCost) { best = N * N + k; bestCost = owner[N * N + k]; }
                }
                if (best < 0) return; // nothing left to open (cannot happen: every inner edge can open)
                var isEast = best < N * N;
                var a = best % (N * N);
                var cellA = chunk.Cell(a % N, a / N);
                var cellB = isEast ? new GridCoord(cellA.x + 1, cellA.y) : new GridCoord(cellA.x, cellA.y + 1);
                var ha = generator.HeightOf(cellA);
                var hb = generator.HeightOf(cellB);
                var kind = ha == hb ? EdgeKind.Arch : ha == ZoneHeight.Tall || hb == ZoneHeight.Tall ? EdgeKind.Window : EdgeKind.Door;
                if (isEast) chunk.east[a] = kind; else chunk.north[a] = kind;
            }
        }
    }
}
