using System;
using System.Collections.Generic;

namespace FrontRooms.Map
{
    /// <summary>What separates two neighbouring cells.</summary>
    public enum EdgeKind : byte { Open, Arch, Wall, Door, Window }

    /// <summary>
    /// Ceiling class of a zone. Where two heights meet, the taller side decides
    /// the exit: a door into a standard zone, a window into a tall one.
    /// </summary>
    public enum ZoneHeight : byte { Low, Standard, Tall }

    /// <summary>What a zone is dressed as: Level 0 paper and carpet, or a Level 4 office.</summary>
    public enum ZoneTheme : byte { Level0, Office }

    /// <summary>A rectangle of cells inside one chunk, in local cell coordinates.</summary>
    [Serializable]
    public struct CellRect
    {
        public int x, y, w, h;
        public CellRect(int x, int y, int w, int h) { this.x = x; this.y = y; this.w = w; this.h = h; }
        public bool Overlaps(CellRect o) => x < o.x + o.w && o.x < x + w && y < o.y + o.h && o.y < y + h;
        public bool Contains(int cx, int cy) => cx >= x && cx < x + w && cy >= y && cy < y + h;
    }

    [Serializable]
    public struct GridCoord : IEquatable<GridCoord>
    {
        public int x;
        public int y;

        public GridCoord(int x, int y) { this.x = x; this.y = y; }

        public bool Equals(GridCoord other) => x == other.x && y == other.y;
        public override bool Equals(object obj) => obj is GridCoord other && Equals(other);
        public override int GetHashCode() => unchecked(x * 73856093 ^ y * 19349663);
        public static bool operator ==(GridCoord a, GridCoord b) => a.Equals(b);
        public static bool operator !=(GridCoord a, GridCoord b) => !a.Equals(b);
        public static GridCoord operator +(GridCoord a, GridCoord b) => new GridCoord(a.x + b.x, a.y + b.y);
        public override string ToString() => "(" + x + ", " + y + ")";
    }

    /// <summary>
    /// World layout of the map. A cell is a 3 m square, one corridor wide; a
    /// chunk is 8 x 8 cells (24 m) and is the unit that is built and dropped
    /// around the player. Cell (x, y) covers world X [3x, 3x+3) and Z [3y, 3y+3).
    /// </summary>
    public static class MapGrid
    {
        public const float CellSize = 3f;
        public const int ChunkCells = 8;
        public const int CellsPerChunk = ChunkCells * ChunkCells;
        public const float ChunkSize = CellSize * ChunkCells;

        public static int FloorDiv(int a, int b) => a >= 0 ? a / b : -((-a + b - 1) / b);
        public static GridCoord ChunkOf(GridCoord cell) => new GridCoord(FloorDiv(cell.x, ChunkCells), FloorDiv(cell.y, ChunkCells));
        public static GridCoord ChunkOrigin(GridCoord chunk) => new GridCoord(chunk.x * ChunkCells, chunk.y * ChunkCells);
        public static int LocalIndex(int i, int j) => i + j * ChunkCells;

        public static float CeilingHeight(ZoneHeight height)
        {
            switch (height)
            {
                case ZoneHeight.Low: return 2.4f;
                case ZoneHeight.Tall: return 5.4f;
                default: return 2.9f;
            }
        }

        public static bool Passable(EdgeKind kind) => kind != EdgeKind.Wall;
    }

    /// <summary>Designer-facing generation numbers. Every value is a share or a chance from 0 to 1 unless it is a cell count.</summary>
    [Serializable]
    public sealed class MapSettings
    {
        public int seed = 20261001;

        // Zone heights. The design plan raises the tall share with each tier.
        public float lowShare = .35f;
        public float standardShare = .55f;
        public float tallShare = .10f;

        // Each chunk is first carved as a maze: a random spanning tree whose
        // edges are never walls. This share of the maze edges becomes a
        // doorless doorway; the rest stay open corridor.
        public float lowDoorway = .25f, standardDoorway = .30f, tallDoorway = .10f;

        // Every other edge inside a zone is a wall, a doorway or open, in that
        // order. Standard zones are the Level 0 maze, low zones leak, tall
        // zones are halls.
        public float lowWall = .50f, lowArch = .20f;
        public float standardWall = .82f, standardArch = .10f;
        public float tallWall = .30f, tallArch = .10f;

        // Rooms carved into each chunk on top of the maze, sized in cells.
        public int lowRooms = 2, lowRoomMin = 2, lowRoomMax = 3;
        public int standardRooms = 2, standardRoomMin = 2, standardRoomMax = 4;
        public int tallRooms = 1, tallRoomMin = 5, tallRoomMax = 7;

        // Where the ceiling height changes, an edge is a wall unless it is the
        // required connection or this roll opens it as a door or window.
        public float borderOpening = .15f;

        // Columns stand on a world 6 m structural grid (cell corners whose
        // indices are both even), only inside carved rooms of at least
        // columnMinRoomCells on both sides, never in Low zones or corridors.
        // A room that qualifies rolls once; if it hits, every grid corner
        // inside it gets a column. Level 0 rooms take 0.6 m columns; Office
        // rooms and tall halls 0.9 m, Office ones joined by bulkheads.
        public int columnMinRoomCells = 3;
        public float level0ColumnRooms = .25f, officeColumnRooms = .75f, tallColumnHalls = .7f;

        // Share of standard-height zones dressed as a Level 4 office.
        public float officeShare = .3f;

        public MapSettings Clone() => (MapSettings)MemberwiseClone();
    }

    /// <summary>
    /// A zone is the set of cells nearest to one site. Every chunk owns exactly
    /// one site, so a zone is named by the chunk its site lies in.
    /// </summary>
    [Serializable]
    public struct ZoneInfo
    {
        public GridCoord id;
        public ZoneHeight height;
        public ZoneTheme theme;
        public float siteX;
        public float siteZ;
    }

    /// <summary>
    /// One generated chunk. East[i + j*8] separates local cell (i, j) from
    /// (i+1, j); North[i + j*8] separates (i, j) from (i, j+1). Index 7 of a
    /// row or column is the chunk border, and West/South repeat the borders
    /// owned by the neighbours so a chunk can be drawn or walked on its own.
    /// </summary>
    [Serializable]
    public sealed class MapChunk
    {
        public GridCoord coord;
        public int revision;
        public GridCoord[] zone = new GridCoord[MapGrid.CellsPerChunk];
        public ZoneHeight[] height = new ZoneHeight[MapGrid.CellsPerChunk];
        public EdgeKind[] east = new EdgeKind[MapGrid.CellsPerChunk];
        public EdgeKind[] north = new EdgeKind[MapGrid.CellsPerChunk];
        public EdgeKind[] west = new EdgeKind[MapGrid.ChunkCells];
        public EdgeKind[] south = new EdgeKind[MapGrid.ChunkCells];
        // Corners (0..8, 0..8), index i + j*9; corner (i, j) is the south-west
        // corner of local cell (i, j). Columns only stand strictly inside
        // rooms, so border corners never carry one.
        public bool[] pillar = new bool[(MapGrid.ChunkCells + 1) * (MapGrid.ChunkCells + 1)];
        // Per corner, for columns: ColumnLarge (0.9 m, else 0.6 m), and
        // ColumnBeamEast / ColumnBeamNorth for a bulkhead to the next column
        // on the 6 m grid (two corners on).
        public byte[] pillarStyle = new byte[(MapGrid.ChunkCells + 1) * (MapGrid.ChunkCells + 1)];
        public const byte ColumnLarge = 1, ColumnBeamEast = 2, ColumnBeamNorth = 4;
        // The key of the zone whose site lies in this chunk. Tall zones are left
        // through windows and carry no key.
        public bool hasKey;
        public GridCoord keyCell;
        public ZoneInfo ownZone;
        // Rooms carved on top of the maze, in carving order. A later room can
        // overlap an earlier one.
        public CellRect[] rooms = new CellRect[0];
        // Per room: the authored module stamped there (RoomModuleStamp), or null for a generated room.
        public RoomModuleData[] roomModules = new RoomModuleData[0];
        // Per cell (i + j*8): a lamp a module set; Auto rolls it from the seed.
        public ModuleLamp[] lamp = new ModuleLamp[MapGrid.CellsPerChunk];

        /// <summary>The module stamped as room r, or null.</summary>
        public RoomModuleData ModuleOf(int r) => roomModules != null && r >= 0 && r < roomModules.Length ? roomModules[r] : null;

        public GridCoord Origin => MapGrid.ChunkOrigin(coord);

        /// <summary>
        /// True when no later room overlaps room r. Later rooms win overlaps,
        /// so only such a room is one open rectangle: an earlier rect keeps
        /// maze edges (walls, arches) where a later one cut into it.
        /// </summary>
        public bool RoomIntact(int r)
        {
            for (var k = r + 1; k < rooms.Length; k++)
                if (rooms[r].Overlaps(rooms[k])) return false;
            return true;
        }
        public GridCoord Cell(int i, int j) => new GridCoord(coord.x * MapGrid.ChunkCells + i, coord.y * MapGrid.ChunkCells + j);
    }

    static class MapHash
    {
        public const int SiteX = 11, SiteZ = 13, Height = 17, EdgeEast = 23, EdgeNorth = 29,
            GateEast = 31, GateNorth = 37, Tree = 41, Pillar = 43, ZoneTint = 47, Rooms = 53, Theme = 59, Columns = 61;

        static uint Mix(uint h)
        {
            unchecked
            {
                h ^= h >> 16; h *= 0x7feb352du;
                h ^= h >> 15; h *= 0x846ca68bu;
                h ^= h >> 16;
                return h;
            }
        }

        public static uint Hash(int seed, int a, int b, int salt, int revision = 0)
        {
            unchecked
            {
                var h = Mix((uint)seed ^ 0x9e3779b9u);
                h = Mix(h ^ (uint)a * 0x85ebca6bu);
                h = Mix(h ^ (uint)b * 0xc2b2ae35u);
                h = Mix(h ^ (uint)salt * 0x27d4eb2fu);
                h = Mix(h ^ (uint)revision * 0x165667b1u);
                return h;
            }
        }

        public static float Unit(uint h) => (h >> 8) * (1f / 16777216f);
    }

    /// <summary>
    /// Deterministic, infinite map. Everything that two chunks share (zones,
    /// heights, border edges) is a pure function of the seed and world
    /// coordinates, so neighbours agree no matter which is built first. A
    /// chunk's revision only reshuffles its own interior walls, rooms and
    /// columns, which is how a dropped chunk can come back shifted.
    /// </summary>
    public sealed class FrontRoomsMapGenerator
    {
        readonly MapSettings settings;
        readonly Dictionary<GridCoord, ZoneInfo> zones = new Dictionary<GridCoord, ZoneInfo>();
        readonly Dictionary<GridCoord, GridCoord> cellZone = new Dictionary<GridCoord, GridCoord>();
        readonly int[] stack = new int[MapGrid.CellsPerChunk];
        readonly bool[] visited = new bool[MapGrid.CellsPerChunk];
        readonly int[] choices = new int[4];
        readonly byte[] room = new byte[MapGrid.CellsPerChunk];

        public FrontRoomsMapGenerator(MapSettings settings)
        {
            this.settings = (settings ?? new MapSettings()).Clone();
        }

        public int Seed => settings.seed;
        public MapSettings Settings => settings.Clone();

        /// <summary>The zone whose site lies in this chunk.</summary>
        public ZoneInfo Zone(GridCoord siteChunk)
        {
            if (zones.TryGetValue(siteChunk, out var zone)) return zone;
            var seed = settings.seed;
            zone.id = siteChunk;
            // Keep sites off the chunk edge so zones do not collapse into slivers.
            zone.siteX = (siteChunk.x + .15f + .7f * MapHash.Unit(MapHash.Hash(seed, siteChunk.x, siteChunk.y, MapHash.SiteX))) * MapGrid.ChunkSize;
            zone.siteZ = (siteChunk.y + .15f + .7f * MapHash.Unit(MapHash.Hash(seed, siteChunk.x, siteChunk.y, MapHash.SiteZ))) * MapGrid.ChunkSize;
            var roll = MapHash.Unit(MapHash.Hash(seed, siteChunk.x, siteChunk.y, MapHash.Height));
            var total = Math.Max(1e-4f, settings.lowShare + settings.standardShare + settings.tallShare);
            roll *= total;
            zone.height = roll < settings.lowShare ? ZoneHeight.Low
                : roll < settings.lowShare + settings.standardShare ? ZoneHeight.Standard
                : ZoneHeight.Tall;
            zone.theme = zone.height == ZoneHeight.Standard && MapHash.Unit(MapHash.Hash(seed, siteChunk.x, siteChunk.y, MapHash.Theme)) < settings.officeShare
                ? ZoneTheme.Office : ZoneTheme.Level0;
            zones[siteChunk] = zone;
            return zone;
        }

        /// <summary>The zone a cell belongs to: the nearest site to the cell centre.</summary>
        public ZoneInfo ZoneOf(GridCoord cell)
        {
            if (cellZone.TryGetValue(cell, out var id)) return Zone(id);
            var chunk = MapGrid.ChunkOf(cell);
            var cx = (cell.x + .5f) * MapGrid.CellSize;
            var cz = (cell.y + .5f) * MapGrid.CellSize;
            var best = float.MaxValue;
            var bestId = chunk;
            // A cell's own site is at most ~34 m away; anything two chunks out
            // starts 24 m away, so a 5 x 5 search can never miss the nearest.
            for (var dy = -2; dy <= 2; dy++)
            for (var dx = -2; dx <= 2; dx++)
            {
                var candidate = Zone(new GridCoord(chunk.x + dx, chunk.y + dy));
                var ex = candidate.siteX - cx;
                var ez = candidate.siteZ - cz;
                var d = ex * ex + ez * ez;
                if (d < best - 1e-4f || (Math.Abs(d - best) <= 1e-4f && Less(candidate.id, bestId)))
                {
                    best = d;
                    bestId = candidate.id;
                }
            }
            cellZone[cell] = bestId;
            return Zone(bestId);
        }

        public ZoneHeight HeightOf(GridCoord cell) => ZoneOf(cell).height;

        static bool Less(GridCoord a, GridCoord b) => a.x < b.x || (a.x == b.x && a.y < b.y);

        /// <summary>
        /// An edge on a chunk border, between a cell and its east or north
        /// neighbour in the next chunk. Each border has one required opening,
        /// so every chunk always connects to all four neighbours.
        /// </summary>
        public EdgeKind BorderEdge(GridCoord cell, bool east)
        {
            var chunk = MapGrid.ChunkOf(cell);
            var seed = settings.seed;
            var local = east ? cell.y - chunk.y * MapGrid.ChunkCells : cell.x - chunk.x * MapGrid.ChunkCells;
            var gate = (int)(MapHash.Hash(seed, chunk.x, chunk.y, east ? MapHash.GateEast : MapHash.GateNorth) % MapGrid.ChunkCells);
            var other = east ? new GridCoord(cell.x + 1, cell.y) : new GridCoord(cell.x, cell.y + 1);
            var roll = MapHash.Unit(MapHash.Hash(seed, cell.x, cell.y, east ? MapHash.EdgeEast : MapHash.EdgeNorth));
            return Resolve(cell, other, local == gate, false, roll);
        }

        EdgeKind Resolve(GridCoord a, GridCoord b, bool required, bool inRoom, float roll)
        {
            var ha = HeightOf(a);
            var hb = HeightOf(b);
            if (ha != hb)
            {
                var exit = ha == ZoneHeight.Tall || hb == ZoneHeight.Tall ? EdgeKind.Window : EdgeKind.Door;
                return required || roll < settings.borderOpening ? exit : EdgeKind.Wall;
            }
            if (inRoom) return EdgeKind.Open;
            Grammar(ha, out var doorway, out var wall, out var arch);
            if (required) return roll < doorway ? EdgeKind.Arch : EdgeKind.Open;
            return roll < wall ? EdgeKind.Wall : roll < wall + arch ? EdgeKind.Arch : EdgeKind.Open;
        }

        void Grammar(ZoneHeight height, out float doorway, out float wall, out float arch)
        {
            switch (height)
            {
                case ZoneHeight.Low: doorway = settings.lowDoorway; wall = settings.lowWall; arch = settings.lowArch; break;
                case ZoneHeight.Tall: doorway = settings.tallDoorway; wall = settings.tallWall; arch = settings.tallArch; break;
                default: doorway = settings.standardDoorway; wall = settings.standardWall; arch = settings.standardArch; break;
            }
        }

        void Rooms(ZoneHeight height, out int count, out int min, out int max)
        {
            switch (height)
            {
                case ZoneHeight.Low: count = settings.lowRooms; min = settings.lowRoomMin; max = settings.lowRoomMax; break;
                case ZoneHeight.Tall: count = settings.tallRooms; min = settings.tallRoomMin; max = settings.tallRoomMax; break;
                default: count = settings.standardRooms; min = settings.standardRoomMin; max = settings.standardRoomMax; break;
            }
            min = Math.Max(1, Math.Min(min, MapGrid.ChunkCells));
            max = Math.Max(min, Math.Min(max, MapGrid.ChunkCells));
        }

        /// <summary>
        /// True when every cell of the rect has the same ceiling height and
        /// theme. A room may straddle two zones; if they match it is still
        /// one space (the edges between them resolve as open room edges).
        /// </summary>
        public bool Uniform(MapChunk chunk, CellRect rect)
        {
            var first = ZoneOf(chunk.Cell(rect.x, rect.y));
            for (var y = rect.y; y < rect.y + rect.h; y++)
            for (var x = rect.x; x < rect.x + rect.w; x++)
            {
                var zone = ZoneOf(chunk.Cell(x, y));
                if (zone.height != first.height || zone.theme != first.theme) return false;
            }
            return true;
        }

        /// <summary>True for a cell corner on the 6 m structural grid (both world indices even).</summary>
        public static bool OnColumnGrid(GridCoord corner) => (corner.x & 1) == 0 && (corner.y & 1) == 0;

        /// <summary>
        /// Columns of one chunk: every 6 m grid corner strictly inside a room
        /// that qualifies and wins its roll. See MapSettings for the rule.
        /// </summary>
        public void PlaceColumns(MapChunk chunk, int revision)
        {
            const int n = MapGrid.ChunkCells;
            Array.Clear(chunk.pillar, 0, chunk.pillar.Length);
            Array.Clear(chunk.pillarStyle, 0, chunk.pillarStyle.Length);
            for (var r = 0; r < chunk.rooms.Length; r++)
            {
                var rect = chunk.rooms[r];
                var module = chunk.ModuleOf(r);
                if (module != null && module.columns == ModuleColumns.None) continue;
                if (module != null && module.columns == ModuleColumns.Custom)
                {
                    // A module's own columns stand where it says, inside its room.
                    if (!chunk.RoomIntact(r)) continue;
                    foreach (var c in module.customColumns)
                    {
                        if (c.x <= 0 || c.y <= 0 || c.x >= rect.w || c.y >= rect.h) continue;
                        chunk.pillar[rect.x + c.x + (rect.y + c.y) * (n + 1)] = true;
                        chunk.pillarStyle[rect.x + c.x + (rect.y + c.y) * (n + 1)] = c.large ? MapChunk.ColumnLarge : (byte)0;
                    }
                    continue;
                }
                if (rect.w < settings.columnMinRoomCells || rect.h < settings.columnMinRoomCells || !chunk.RoomIntact(r)) continue;
                var zone = ZoneOf(chunk.Cell(rect.x, rect.y));
                if (zone.height == ZoneHeight.Low || !Uniform(chunk, rect)) continue;
                var office = zone.theme == ZoneTheme.Office;
                var chance = zone.height == ZoneHeight.Tall ? settings.tallColumnHalls : office ? settings.officeColumnRooms : settings.level0ColumnRooms;
                if (MapHash.Unit(MapHash.Hash(settings.seed, chunk.coord.x * 16 + r, chunk.coord.y, MapHash.Columns, revision)) >= chance) continue;
                var style = office || zone.height == ZoneHeight.Tall ? MapChunk.ColumnLarge : (byte)0;
                for (var j = rect.y + 1; j < rect.y + rect.h; j++)
                for (var i = rect.x + 1; i < rect.x + rect.w; i++)
                {
                    if (!OnColumnGrid(chunk.Cell(i, j))) continue;
                    chunk.pillar[i + j * (n + 1)] = true;
                    var flags = style;
                    // Office columns carry a bulkhead to the next column on the grid inside the same room.
                    if (office && i + 2 < rect.x + rect.w) flags |= MapChunk.ColumnBeamEast;
                    if (office && j + 2 < rect.y + rect.h) flags |= MapChunk.ColumnBeamNorth;
                    chunk.pillarStyle[i + j * (n + 1)] = flags;
                }
            }
        }

        /// <summary>Build one chunk. Revision 0 is the first build; a higher revision reshuffles only the interior.</summary>
        public MapChunk Generate(GridCoord coord, int revision = 0)
        {
            const int n = MapGrid.ChunkCells;
            var seed = settings.seed;
            var chunk = new MapChunk { coord = coord, revision = revision, ownZone = Zone(coord) };
            for (var j = 0; j < n; j++)
            for (var i = 0; i < n; i++)
            {
                var zone = ZoneOf(chunk.Cell(i, j));
                chunk.zone[MapGrid.LocalIndex(i, j)] = zone.id;
                chunk.height[MapGrid.LocalIndex(i, j)] = zone.height;
            }

            // A random depth-first maze over the chunk's cells: its edges are
            // never walls, so every cell of the chunk stays reachable, and its
            // long winding branches read as corridors.
            var treeEast = new bool[MapGrid.CellsPerChunk];
            var treeNorth = new bool[MapGrid.CellsPerChunk];
            var rng = MapHash.Hash(seed, coord.x, coord.y, MapHash.Tree, revision) | 1u;
            Array.Clear(visited, 0, visited.Length);
            var top = 0;
            var start = (int)(Next(ref rng) % MapGrid.CellsPerChunk);
            stack[top++] = start;
            visited[start] = true;
            while (top > 0)
            {
                var current = stack[top - 1];
                int ci = current % n, cj = current / n, count = 0;
                if (ci + 1 < n && !visited[current + 1]) choices[count++] = current + 1;
                if (ci > 0 && !visited[current - 1]) choices[count++] = current - 1;
                if (cj + 1 < n && !visited[current + n]) choices[count++] = current + n;
                if (cj > 0 && !visited[current - n]) choices[count++] = current - n;
                if (count == 0) { top--; continue; }
                var next = choices[(int)(Next(ref rng) % (uint)count)];
                if (next == current + 1) treeEast[current] = true;
                else if (next == current - 1) treeEast[next] = true;
                else if (next == current + n) treeNorth[current] = true;
                else treeNorth[next] = true;
                visited[next] = true;
                stack[top++] = next;
            }

            // Rooms on top of the maze: every edge inside one is open, so the
            // maze opens into rooms of different sizes. Later rooms overwrite
            // earlier ones where they overlap.
            Array.Clear(room, 0, room.Length);
            Rooms(chunk.ownZone.height, out var roomCount, out var roomMin, out var roomMax);
            var roomRng = MapHash.Hash(seed, coord.x, coord.y, MapHash.Rooms, revision) | 1u;
            chunk.rooms = new CellRect[Math.Max(0, roomCount)];
            chunk.roomModules = new RoomModuleData[chunk.rooms.Length];
            for (var r = 1; r <= roomCount; r++)
            {
                var w = roomMin + (int)(Next(ref roomRng) % (uint)(roomMax - roomMin + 1));
                var h = roomMin + (int)(Next(ref roomRng) % (uint)(roomMax - roomMin + 1));
                var x0 = (int)(Next(ref roomRng) % (uint)(n - w + 1));
                var y0 = (int)(Next(ref roomRng) % (uint)(n - h + 1));
                chunk.rooms[r - 1] = new CellRect(x0, y0, w, h);
                for (var y = y0; y < y0 + h; y++)
                for (var x = x0; x < x0 + w; x++)
                    room[MapGrid.LocalIndex(x, y)] = (byte)r;
            }

            for (var j = 0; j < n; j++)
            for (var i = 0; i < n; i++)
            {
                var index = MapGrid.LocalIndex(i, j);
                var cell = chunk.Cell(i, j);
                chunk.east[index] = i < n - 1
                    ? Resolve(cell, new GridCoord(cell.x + 1, cell.y), treeEast[index], room[index] != 0 && room[index] == room[index + 1], MapHash.Unit(MapHash.Hash(seed, cell.x, cell.y, MapHash.EdgeEast, revision)))
                    : BorderEdge(cell, true);
                chunk.north[index] = j < n - 1
                    ? Resolve(cell, new GridCoord(cell.x, cell.y + 1), treeNorth[index], room[index] != 0 && room[index] == room[index + n], MapHash.Unit(MapHash.Hash(seed, cell.x, cell.y, MapHash.EdgeNorth, revision)))
                    : BorderEdge(cell, false);
            }
            for (var k = 0; k < n; k++)
            {
                chunk.west[k] = BorderEdge(chunk.Cell(-1, k), true);
                chunk.south[k] = BorderEdge(chunk.Cell(k, -1), false);
            }
            PlaceColumns(chunk, revision);

            PlaceKey(chunk);
            return chunk;
        }

        /// <summary>
        /// The zone's key goes in the zone cell nearest its site. The search
        /// covers the 5 x 5 chunks around the site, which contains every cell
        /// that can belong to the zone.
        /// </summary>
        void PlaceKey(MapChunk chunk)
        {
            var zone = chunk.ownZone;
            chunk.hasKey = false;
            if (zone.height == ZoneHeight.Tall) return;
            var best = float.MaxValue;
            for (var y = (chunk.coord.y - 2) * MapGrid.ChunkCells; y < (chunk.coord.y + 3) * MapGrid.ChunkCells; y++)
            for (var x = (chunk.coord.x - 2) * MapGrid.ChunkCells; x < (chunk.coord.x + 3) * MapGrid.ChunkCells; x++)
            {
                var cell = new GridCoord(x, y);
                if (ZoneOf(cell).id != zone.id) continue;
                var ex = (x + .5f) * MapGrid.CellSize - zone.siteX;
                var ez = (y + .5f) * MapGrid.CellSize - zone.siteZ;
                var d = ex * ex + ez * ez;
                if (d >= best) continue;
                best = d;
                chunk.keyCell = cell;
                chunk.hasKey = true;
            }
        }

        static uint Next(ref uint state)
        {
            state ^= state << 13;
            state ^= state >> 17;
            state ^= state << 5;
            return state;
        }
    }

    /// <summary>
    /// The chunks currently built, keyed by coordinate. The runtime streams
    /// through this; the debug map and the verification read it the same way.
    /// </summary>
    public sealed class FrontRoomsMapCache
    {
        readonly Dictionary<GridCoord, MapChunk> chunks = new Dictionary<GridCoord, MapChunk>();
        readonly Dictionary<GridCoord, int> revisions = new Dictionary<GridCoord, int>();

        public FrontRoomsMapCache(MapSettings settings) { Generator = new FrontRoomsMapGenerator(settings); }

        public FrontRoomsMapGenerator Generator { get; }
        public int Count => chunks.Count;
        public IEnumerable<MapChunk> Built => chunks.Values;

        // Modules placed by hand (the Level Designer preview), per chunk.
        readonly Dictionary<GridCoord, List<(RoomModuleData module, int x, int y)>> placements = new Dictionary<GridCoord, List<(RoomModuleData, int, int)>>();

        public MapChunk Get(GridCoord coord)
        {
            if (chunks.TryGetValue(coord, out var chunk)) return chunk;
            revisions.TryGetValue(coord, out var revision);
            chunk = Generator.Generate(coord, revision);
            if (placements.TryGetValue(coord, out var list))
                foreach (var p in list) RoomModuleStamp.Apply(Generator, chunk, p.module, p.x, p.y);
            chunks[coord] = chunk;
            return chunk;
        }

        /// <summary>
        /// Stamp a module into a chunk, with its south-west cell at chunk-local
        /// (x, y), every time that chunk is generated (and again after a shift).
        /// </summary>
        public void Place(GridCoord chunk, RoomModuleData module, int x, int y)
        {
            if (!placements.TryGetValue(chunk, out var list)) placements[chunk] = list = new List<(RoomModuleData, int, int)>();
            list.Add((module, x, y));
            chunks.Remove(chunk);
        }

        public bool IsBuilt(GridCoord coord) => chunks.ContainsKey(coord);
        public void Drop(GridCoord coord) => chunks.Remove(coord);

        /// <summary>Drop a chunk and make its next build a different interior.</summary>
        public void Shift(GridCoord coord)
        {
            revisions.TryGetValue(coord, out var revision);
            revisions[coord] = revision + 1;
            chunks.Remove(coord);
        }

        /// <summary>The edge between two side-by-side cells.</summary>
        public EdgeKind Edge(GridCoord a, GridCoord b)
        {
            if (b.x < a.x || b.y < a.y) { var t = a; a = b; b = t; }
            var east = b.x == a.x + 1 && b.y == a.y;
            if (!east && !(b.x == a.x && b.y == a.y + 1)) throw new ArgumentException("Cells " + a + " and " + b + " are not neighbours.");
            var chunk = Get(MapGrid.ChunkOf(a));
            var o = chunk.Origin;
            var index = MapGrid.LocalIndex(a.x - o.x, a.y - o.y);
            return east ? chunk.east[index] : chunk.north[index];
        }

        public ZoneInfo ZoneOf(GridCoord cell) => Generator.ZoneOf(cell);
    }
}
