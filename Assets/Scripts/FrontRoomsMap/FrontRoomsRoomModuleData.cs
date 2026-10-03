using System;
using System.Collections.Generic;

namespace FrontRooms.Map
{
    /// <summary>
    /// What a room module puts on one of its edges. Doors and windows are not
    /// here: the map decides those where the module meets a zone of another
    /// height (Red's decision 1, doors and windows only on zone borders).
    /// </summary>
    public enum ModuleEdge : byte { Wall, Open, Arch }

    /// <summary>Columns inside the module: the map's 6 m grid rule, none, or the module's own list.</summary>
    public enum ModuleColumns : byte { Auto, None, Custom }

    /// <summary>How the module's room is filled beyond its own props.</summary>
    public enum ModuleFill : byte
    {
        /// <summary>Only the module's props.</summary>
        None,
        /// <summary>As a generated room: Office rooms get the Office kit, Level 0 halls of 4 x 4 or more may get a pile.</summary>
        Auto,
        /// <summary>The Office kit fills round the module's props and columns.</summary>
        Office,
        /// <summary>A furniture pile in the room, whatever the theme.</summary>
        Pile,
    }

    /// <summary>A lamp's temperament, per cell. Auto rolls it from the seed, as everywhere else.</summary>
    public enum ModuleLamp : byte { Auto, Steady, Stutter, Failing, Dead, Dim, Off }

    /// <summary>
    /// One prop: a kit asset at a point in metres from the module's south-west
    /// corner (a cell line), y metres above the floor (wall pieces: a clock,
    /// a window), turned by yaw degrees (0 = front faces +Z).
    /// </summary>
    [Serializable]
    public struct ModuleProp
    {
        public string kit;
        public float x, z, yaw;
        public float y;
        public bool noCollider;
    }

    /// <summary>A column on an inner cell corner of the module, (1..width-1, 1..depth-1).</summary>
    [Serializable]
    public struct ModuleColumn
    {
        public int x, y;
        public bool large;
    }

    /// <summary>
    /// A room authored by a level designer: its footprint in 3 m cells, ceiling
    /// height, theme, what every edge is, columns, props, lamps and where the
    /// generator may use it. Plain data (FrontRoomsRoomModule wraps it as an
    /// asset) so the stamp and its checks run without Unity.
    /// Cell (i, j): i along +X (width), j along +Z (depth).
    /// </summary>
    [Serializable]
    public sealed class RoomModuleData
    {
        public const int MaxCells = MapGrid.ChunkCells;

        public int width = 3, depth = 3;
        public ZoneHeight height = ZoneHeight.Standard;
        public ZoneTheme theme = ZoneTheme.Level0;

        // Perimeter, one entry per cell edge: south and north run along X
        // (width entries, west to east), west and east along Z (depth entries,
        // south to north).
        public ModuleEdge[] south = new ModuleEdge[0], north = new ModuleEdge[0], west = new ModuleEdge[0], east = new ModuleEdge[0];
        // Inside: between cell (i, j) and (i+1, j) at i + j*(width-1); between
        // (i, j) and (i, j+1) at i + j*width. Open unless the designer
        // partitions the room.
        public ModuleEdge[] innerEast = new ModuleEdge[0], innerNorth = new ModuleEdge[0];

        public ModuleColumns columns = ModuleColumns.Auto;
        public ModuleColumn[] customColumns = new ModuleColumn[0];
        public ModuleFill fill = ModuleFill.Auto;
        public ModuleProp[] props = new ModuleProp[0];
        // Per cell, i + j*width.
        public ModuleLamp[] lamps = new ModuleLamp[0];

        // Where the generator may use it (P3).
        public float weight = 1f;
        public bool allowRotate = true;
        public int minTier = 0, maxTier = 4;

        public float WidthMetres => width * MapGrid.CellSize;
        public float DepthMetres => depth * MapGrid.CellSize;

        /// <summary>
        /// Change the footprint, keeping every edge, lamp, prop and column
        /// that still fits where it was (cells keep their coordinates).
        /// </summary>
        public void Resize(int newWidth, int newDepth)
        {
            Normalize();
            newWidth = Clamp(newWidth, 1, MaxCells);
            newDepth = Clamp(newDepth, 1, MaxCells);
            if (newWidth == width && newDepth == depth) return;
            var old = Clone();
            width = newWidth;
            depth = newDepth;
            south = north = west = east = innerEast = innerNorth = null;
            lamps = null;
            Normalize();
            for (var j = 0; j < depth; j++)
            for (var i = 0; i < width; i++)
            {
                if (i < old.width && j < old.depth) lamps[i + j * width] = old.LampAt(i, j);
                // Perimeter edges stay on their side; inner edges keep their cells.
                if (j == 0 && i < old.width) south[i] = old.south[i];
                if (j == depth - 1 && i < old.width) north[i] = old.north[i];
                if (i == 0 && j < old.depth) west[j] = old.west[j];
                if (i == width - 1 && j < old.depth) east[j] = old.east[j];
                if (i < width - 1 && i < old.width - 1 && j < old.depth) innerEast[i + j * (width - 1)] = old.innerEast[i + j * (old.width - 1)];
                if (j < depth - 1 && j < old.depth - 1 && i < old.width) innerNorth[i + j * width] = old.innerNorth[i + j * old.width];
            }
            var keep = new List<ModuleColumn>();
            foreach (var c in customColumns) if (c.x > 0 && c.y > 0 && c.x < width && c.y < depth) keep.Add(c);
            customColumns = keep.ToArray();
        }

        /// <summary>Clamp the footprint and size every array to it (after loading, or when arrays are missing).</summary>
        public void Normalize()
        {
            width = Clamp(width, 1, MaxCells);
            depth = Clamp(depth, 1, MaxCells);
            if (theme == ZoneTheme.Office) height = ZoneHeight.Standard;
            south = Resize(south, width, ModuleEdge.Wall);
            north = Resize(north, width, ModuleEdge.Wall);
            west = Resize(west, depth, ModuleEdge.Wall);
            east = Resize(east, depth, ModuleEdge.Wall);
            innerEast = Resize(innerEast, Math.Max(0, width - 1) * depth, ModuleEdge.Open);
            innerNorth = Resize(innerNorth, width * Math.Max(0, depth - 1), ModuleEdge.Open);
            lamps = Resize(lamps, width * depth, ModuleLamp.Auto);
            customColumns = customColumns ?? new ModuleColumn[0];
            props = props ?? new ModuleProp[0];
            // NaN and negative weights mean never; a huge one is capped so totals stay finite.
            weight = weight > 0f ? Math.Min(weight, 1000f) : 0f;
            minTier = Clamp(minTier, 0, 9);
            maxTier = Clamp(maxTier, minTier, 9);
        }

        static T[] Resize<T>(T[] a, int n, T fill)
        {
            if (a != null && a.Length == n) return a;
            var result = new T[n];
            for (var k = 0; k < n; k++) result[k] = a != null && k < a.Length ? a[k] : fill;
            return result;
        }

        static int Clamp(int v, int lo, int hi) => v < lo ? lo : v > hi ? hi : v;

        public RoomModuleData Clone()
        {
            var c = (RoomModuleData)MemberwiseClone();
            c.south = (ModuleEdge[])south?.Clone();
            c.north = (ModuleEdge[])north?.Clone();
            c.west = (ModuleEdge[])west?.Clone();
            c.east = (ModuleEdge[])east?.Clone();
            c.innerEast = (ModuleEdge[])innerEast?.Clone();
            c.innerNorth = (ModuleEdge[])innerNorth?.Clone();
            c.customColumns = (ModuleColumn[])customColumns?.Clone();
            c.props = (ModuleProp[])props?.Clone();
            c.lamps = (ModuleLamp[])lamps?.Clone();
            return c;
        }

        // ---------- Edges by cell ----------

        /// <summary>The edge between module cell (i, j) and its neighbour in direction (dx, dy); outside the footprint it is a perimeter edge.</summary>
        public ModuleEdge EdgeAt(int i, int j, int dx, int dy)
        {
            if (dx == 1) return i == width - 1 ? east[j] : innerEast[i + j * (width - 1)];
            if (dx == -1) return i == 0 ? west[j] : innerEast[i - 1 + j * (width - 1)];
            if (dy == 1) return j == depth - 1 ? north[i] : innerNorth[i + j * width];
            return j == 0 ? south[i] : innerNorth[i + (j - 1) * width];
        }

        public void SetEdge(int i, int j, int dx, int dy, ModuleEdge kind)
        {
            if (dx == 1) { if (i == width - 1) east[j] = kind; else innerEast[i + j * (width - 1)] = kind; }
            else if (dx == -1) { if (i == 0) west[j] = kind; else innerEast[i - 1 + j * (width - 1)] = kind; }
            else if (dy == 1) { if (j == depth - 1) north[i] = kind; else innerNorth[i + j * width] = kind; }
            else { if (j == 0) south[i] = kind; else innerNorth[i + (j - 1) * width] = kind; }
        }

        public ModuleLamp LampAt(int i, int j) => lamps[i + j * width];

        // ---------- Rotation ----------

        /// <summary>
        /// This module turned clockwise (seen from above) by quarter turns.
        /// Cell (i, j) of a quarter turn goes to (j, width-1-i); props and
        /// columns turn with it and props' yaw grows by 90 per turn.
        /// </summary>
        public RoomModuleData Rotated(int quarterTurns)
        {
            var turns = ((quarterTurns % 4) + 4) % 4;
            var r = Clone();
            for (var t = 0; t < turns; t++) r = r.RotatedOnce();
            return r;
        }

        RoomModuleData RotatedOnce()
        {
            var r = Clone();
            r.width = depth;
            r.depth = width;
            r.south = new ModuleEdge[0]; r.north = new ModuleEdge[0]; r.west = new ModuleEdge[0]; r.east = new ModuleEdge[0];
            r.innerEast = new ModuleEdge[0]; r.innerNorth = new ModuleEdge[0]; r.lamps = new ModuleLamp[0];
            r.Normalize();
            // Clockwise about +Y: +X -> -Z, +Z -> +X. Old cell (i, j) -> new (j, width-1-i).
            for (var j = 0; j < depth; j++)
            for (var i = 0; i < width; i++)
            {
                int ni = j, nj = width - 1 - i;
                r.lamps[ni + nj * r.width] = LampAt(i, j);
                // Old +X edge becomes new -Z edge; old +Z becomes new +X.
                r.SetEdge(ni, nj, 0, -1, EdgeAt(i, j, 1, 0));
                r.SetEdge(ni, nj, 1, 0, EdgeAt(i, j, 0, 1));
                r.SetEdge(ni, nj, 0, 1, EdgeAt(i, j, -1, 0));
                r.SetEdge(ni, nj, -1, 0, EdgeAt(i, j, 0, -1));
            }
            var w = WidthMetres;
            for (var k = 0; k < r.props.Length; k++)
            {
                var p = r.props[k];
                r.props[k] = new ModuleProp { kit = p.kit, x = p.z, z = w - p.x, y = p.y, yaw = (p.yaw + 90f) % 360f, noCollider = p.noCollider };
            }
            for (var k = 0; k < r.customColumns.Length; k++)
            {
                var c = r.customColumns[k];
                r.customColumns[k] = new ModuleColumn { x = c.y, y = width - c.x, large = c.large };
            }
            return r;
        }

        // ---------- Checks ----------

        /// <summary>
        /// Problems a designer must fix (errors) or should know (warnings).
        /// <paramref name="footprint"/> gives a kit asset's footprint as
        /// (min x, min z, max x, max z, height) about its pivot, or null if unknown.
        /// </summary>
        public void Validate(List<string> errors, List<string> warnings, Func<string, float[]> footprint = null)
        {
            Normalize();
            var ceiling = MapGrid.CeilingHeight(height);

            // At least one way in, and every cell reachable from the others.
            var openings = 0;
            foreach (var e in south) if (e != ModuleEdge.Wall) openings++;
            foreach (var e in north) if (e != ModuleEdge.Wall) openings++;
            foreach (var e in west) if (e != ModuleEdge.Wall) openings++;
            foreach (var e in east) if (e != ModuleEdge.Wall) openings++;
            if (openings == 0) errors.Add("No way in: every perimeter edge is a wall.");
            var seen = new bool[width * depth];
            var stack = new Stack<int>();
            stack.Push(0);
            seen[0] = true;
            var reached = 1;
            while (stack.Count > 0)
            {
                var k = stack.Pop();
                int i = k % width, j = k / width;
                foreach (var d in Steps)
                {
                    int ni = i + d[0], nj = j + d[1];
                    if (ni < 0 || nj < 0 || ni >= width || nj >= depth) continue;
                    if (EdgeAt(i, j, d[0], d[1]) == ModuleEdge.Wall || seen[ni + nj * width]) continue;
                    seen[ni + nj * width] = true;
                    reached++;
                    stack.Push(ni + nj * width);
                }
            }
            if (reached < width * depth) errors.Add("Inner walls cut off " + (width * depth - reached) + " cell(s) from the rest of the room.");

            if (columns == ModuleColumns.Custom)
            {
                foreach (var c in customColumns)
                    if (c.x <= 0 || c.y <= 0 || c.x >= width || c.y >= depth) errors.Add("Column at corner (" + c.x + ", " + c.y + ") is not inside the room.");
                if (customColumns.Length > 0 && (width < 3 || depth < 3)) warnings.Add("Columns in a room under 3 x 3 cells: the map's own rule never puts them there.");
            }

            if (width >= MaxCells - 1 || depth >= MaxCells - 1)
                warnings.Add("A side of 7 or 8 cells meets the chunk border: the map decides the edges there and may open one of your walls to keep the maze connected. Keep props off those walls.");
            if (fill == ModuleFill.Office && theme != ZoneTheme.Office) warnings.Add("Office fill in a Level 0 room.");
            var dresses = fill == ModuleFill.Office || fill == ModuleFill.Pile || (fill == ModuleFill.Auto && (theme == ZoneTheme.Office || (width >= 4 && depth >= 4)));
            if (dresses && InnerStrips().Count > 0)
                warnings.Add("Fill " + fill + " furnishes the room as one open space: the Office kit or a pile may stand in an inner wall or block an inner doorway. Use Fill None with inner walls.");
            if (fill == ModuleFill.Pile && (width < 4 || depth < 4)) warnings.Add("A pile needs a hall of 4 x 4 cells to look right.");

            // Columns run floor to ceiling: the corners where one stands, or may stand in a turn the generator can use.
            var columnAt = new List<(int i, int j, float size, string what)>();
            var autoSize = theme == ZoneTheme.Office || height == ZoneHeight.Tall ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall;
            for (var j = 1; j < depth; j++)
            for (var i = 1; i < width; i++)
            {
                if (columns == ModuleColumns.Custom)
                {
                    foreach (var c in customColumns)
                        if (c.x == i && c.y == j) { columnAt.Add((i, j, c.large ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall, "a column stands")); break; }
                    continue;
                }
                for (var t = 0; t < (allowRotate ? 4 : 1); t++)
                    if (AutoColumnAt(i, j, t)) { columnAt.Add((i, j, autoSize, t == 0 ? "an Auto column may stand" : "an Auto column may stand when the room is turned " + t * 90 + "°")); break; }
            }

            // Props: inside the clear floor, under the ceiling, off the openings and columns.
            var clearMin = ModuleUnits.WallHalf;
            for (var k = 0; k < props.Length; k++)
            {
                var p = props[k];
                var label = "Prop " + (k + 1) + " (" + (string.IsNullOrEmpty(p.kit) ? "no kit" : p.kit) + ")";
                if (string.IsNullOrEmpty(p.kit)) { errors.Add(label + ": choose a kit asset."); continue; }
                var f = footprint?.Invoke(p.kit);
                if (f == null) { warnings.Add(label + ": no footprint known (asset missing?)."); continue; }
                Bounds(p, f, out var x0, out var z0, out var x1, out var z1);
                if (x0 < clearMin - .01f || z0 < clearMin - .01f || x1 > WidthMetres - clearMin + .01f || z1 > DepthMetres - clearMin + .01f)
                    errors.Add(label + ": stands in or beyond a wall.");
                if (p.y + f[4] > ceiling - ModuleUnits.CeilingClearance) errors.Add(label + ": reaches " + (p.y + f[4]).ToString("0.00") + " m, the ceiling is " + ceiling.ToString("0.0") + " m.");
                foreach (var c in columnAt)
                {
                    float cx = c.i * MapGrid.CellSize, cz = c.j * MapGrid.CellSize, r = c.size * .5f;
                    if (x0 < cx + r && cx - r < x1 && z0 < cz + r && cz - r < z1) { warnings.Add(label + ": stands where " + c.what + " (corner " + c.i + ", " + c.j + ")."); break; }
                }
                if (p.y > ModuleUnits.RelayHeight) continue; // wall pieces up high leave the floor free
                // The map keeps these strips clear when it builds (FrontRoomsMapWorld.KeepClear): a prop with a collider there is left out.
                foreach (var strip in EntryStrips())
                {
                    if (!(x0 < strip[2] && strip[0] < x1 && z0 < strip[3] && strip[1] < z1)) continue;
                    if (p.noCollider) warnings.Add(label + ": stands in the floor kept clear inside an opening (" + ModuleUnits.EntryClearDepth.ToString("0.0") + " m).");
                    else errors.Add(label + ": blocks the floor inside an opening (keep " + ModuleUnits.EntryClearDepth.ToString("0.0") + " m clear); the map leaves it out of the build. Move it, or tick No collider for clutter.");
                    break;
                }
                foreach (var strip in InnerStrips())
                {
                    if (!(x0 < strip[2] && strip[0] < x1 && z0 < strip[3] && strip[1] < z1)) continue;
                    if (strip[4] > 0f) errors.Add(label + ": stands in an inner wall.");
                    else warnings.Add(label + ": blocks the floor at an inner doorway.");
                    break;
                }
            }

            // Can the player get from every opening to every other, and into every cell, past the props and inner walls?
            if (errors.Count == 0 && openings > 0 && !Walkable(footprint, out var problem)) errors.Add(problem);
        }

        /// <summary>
        /// True if the map's column rule (FrontRoomsMapGenerator.PlaceColumns) may put an
        /// Auto column on inner corner (i, j) with the room placed <paramref name="turns"/>
        /// quarter turns clockwise. The generator lands an Auto-column module on the world
        /// 6 m grid phase of its turned footprint centred in a chunk, as the preview shows it,
        /// so an odd side moves the columns to the other corners in odd turns. Never in Low
        /// rooms, rooms under <paramref name="minCells"/> a side, or where inner walls or doorways meet.
        /// </summary>
        public bool AutoColumnAt(int i, int j, int turns, int minCells = 3)
        {
            if (columns != ModuleColumns.Auto || height == ZoneHeight.Low || width < minCells || depth < minCells) return false;
            if (i <= 0 || j <= 0 || i >= width || j >= depth) return false;
            if (EdgeAt(i - 1, j, 1, 0) != ModuleEdge.Open || EdgeAt(i - 1, j - 1, 1, 0) != ModuleEdge.Open
                || EdgeAt(i - 1, j - 1, 0, 1) != ModuleEdge.Open || EdgeAt(i, j - 1, 0, 1) != ModuleEdge.Open) return false;
            int w = width, d = depth, ci = i, cj = j;
            for (var t = 0; t < ((turns % 4) + 4) % 4; t++)
            {
                // Clockwise: corner (x, y) of a w x d room goes to (y, w - x) of the d x w room.
                (ci, cj) = (cj, w - ci);
                (w, d) = (d, w);
            }
            return ((MaxCells - w) / 2 + ci) % 2 == 0 && ((MaxCells - d) / 2 + cj) % 2 == 0;
        }

        /// <summary>
        /// Inner edges as (x0, z0, x1, z1, isWall) in module metres: an inner
        /// wall's 0.16 m band, or the floor kept clear both sides of an inner
        /// doorway (arch). Open inner edges are just floor.
        /// </summary>
        public List<float[]> InnerStrips()
        {
            var cs = MapGrid.CellSize;
            var h = ModuleUnits.WallHalf;
            var d = ModuleUnits.EntryClearDepth + h;
            var strips = new List<float[]>();
            for (var j = 0; j < depth; j++)
            for (var i = 0; i < width; i++)
            {
                if (i < width - 1 && innerEast[i + j * (width - 1)] != ModuleEdge.Open)
                {
                    var wall = innerEast[i + j * (width - 1)] == ModuleEdge.Wall;
                    var r = wall ? h : d;
                    var x = (i + 1) * cs;
                    strips.Add(new[] { x - r, j * cs, x + r, (j + 1) * cs, wall ? 1f : 0f });
                }
                if (j < depth - 1 && innerNorth[i + j * width] != ModuleEdge.Open)
                {
                    var wall = innerNorth[i + j * width] == ModuleEdge.Wall;
                    var r = wall ? h : d;
                    var z = (j + 1) * cs;
                    strips.Add(new[] { i * cs, z - r, (i + 1) * cs, z + r, wall ? 1f : 0f });
                }
            }
            return strips;
        }

        /// <summary>
        /// Floods the floor on a 0.25 m grid with the player's 0.3 m body,
        /// from the first opening, past walls (perimeter and inner) and props
        /// on the floor. False, with the reason, if an opening or a cell is
        /// cut off. Inner doorways count as open along their whole edge (where
        /// the map puts the gap varies), so this is a lower bound on trouble.
        /// </summary>
        public bool Walkable(Func<string, float[]> footprint, out string problem)
        {
            problem = null;
            const float step = .25f;
            var cs = MapGrid.CellSize;
            var body = ModuleUnits.PlayerRadius;
            int nx = (int)Math.Round(WidthMetres / step), nz = (int)Math.Round(DepthMetres / step);
            var blocked = new bool[nx * nz];
            var rects = new List<float[]>();
            foreach (var p in props)
            {
                if (p.noCollider || p.y > ModuleUnits.RelayHeight || string.IsNullOrEmpty(p.kit)) continue;
                var f = footprint?.Invoke(p.kit);
                if (f == null) continue;
                Bounds(p, f, out var x0, out var z0, out var x1, out var z1);
                rects.Add(new[] { x0, z0, x1, z1 });
            }
            foreach (var w in InnerStrips()) if (w[4] > 0f) rects.Add(new[] { w[0], w[1], w[2], w[3] });
            for (var k = 0; k < blocked.Length; k++)
            {
                float x = (k % nx + .5f) * step, z = (k / nx + .5f) * step;
                // Perimeter walls: everywhere but the openings.
                var nearWall = x < ModuleUnits.WallHalf + body || z < ModuleUnits.WallHalf + body || x > WidthMetres - ModuleUnits.WallHalf - body || z > DepthMetres - ModuleUnits.WallHalf - body;
                if (nearWall && !InOpening(x, z, body)) { blocked[k] = true; continue; }
                foreach (var r in rects)
                    if (x > r[0] - body && x < r[2] + body && z > r[1] - body && z < r[3] + body) { blocked[k] = true; break; }
            }

            // One seed per perimeter opening: a free node inside the floor kept
            // clear behind it, nearest the opening's middle. None: the opening is blocked.
            var seeds = new List<int>();
            var names = new List<string>();
            void Seed(float[] strip, string name)
            {
                float cx = (strip[0] + strip[2]) * .5f, cz = (strip[1] + strip[3]) * .5f;
                var best = -1;
                var bestD = float.MaxValue;
                for (var k = 0; k < blocked.Length; k++)
                {
                    if (blocked[k]) continue;
                    float x = (k % nx + .5f) * step, z = (k / nx + .5f) * step;
                    if (x < strip[0] || x > strip[2] || z < strip[1] || z > strip[3]) continue;
                    var d2 = (x - cx) * (x - cx) + (z - cz) * (z - cz);
                    if (d2 < bestD) { bestD = d2; best = k; }
                }
                seeds.Add(best);
                names.Add(name);
            }
            var depthClear = ModuleUnits.EntryClearDepth + ModuleUnits.WallHalf;
            for (var i = 0; i < width; i++)
            {
                if (south[i] != ModuleEdge.Wall) Seed(new[] { i * cs, 0f, (i + 1) * cs, depthClear }, "the south opening of column " + (i + 1));
                if (north[i] != ModuleEdge.Wall) Seed(new[] { i * cs, DepthMetres - depthClear, (i + 1) * cs, DepthMetres }, "the north opening of column " + (i + 1));
            }
            for (var j = 0; j < depth; j++)
            {
                if (west[j] != ModuleEdge.Wall) Seed(new[] { 0f, j * cs, depthClear, (j + 1) * cs }, "the west opening of row " + (j + 1));
                if (east[j] != ModuleEdge.Wall) Seed(new[] { WidthMetres - depthClear, j * cs, WidthMetres, (j + 1) * cs }, "the east opening of row " + (j + 1));
            }
            for (var s = 0; s < seeds.Count; s++)
                if (seeds[s] < 0) { problem = "Props block " + names[s] + "."; return false; }
            if (seeds.Count == 0) return true;

            var seen = new bool[blocked.Length];
            var queue = new Queue<int>();
            queue.Enqueue(seeds[0]);
            seen[seeds[0]] = true;
            while (queue.Count > 0)
            {
                var k = queue.Dequeue();
                int x = k % nx, z = k / nx;
                if (x > 0) Visit(k - 1);
                if (x < nx - 1) Visit(k + 1);
                if (z > 0) Visit(k - nx);
                if (z < nz - 1) Visit(k + nx);
            }
            void Visit(int k)
            {
                if (seen[k] || blocked[k]) return;
                seen[k] = true;
                queue.Enqueue(k);
            }
            for (var s = 1; s < seeds.Count; s++)
                if (!seen[seeds[s]]) { problem = "Props or inner walls cut " + names[s] + " off from " + names[0] + "."; return false; }
            var per = (int)Math.Round(cs / step);
            for (var j = 0; j < depth; j++)
            for (var i = 0; i < width; i++)
            {
                var any = false;
                for (var b = 0; b < per && !any; b++)
                for (var a = 0; a < per && !any; a++)
                    any = seen[i * per + a + (j * per + b) * nx];
                if (!any) { problem = "Props or inner walls leave cell (" + (i + 1) + ", " + (j + 1) + ") unreachable."; return false; }
            }
            return true;
        }

        bool InOpening(float x, float z, float body)
        {
            var cs = MapGrid.CellSize;
            var i = Math.Min(width - 1, Math.Max(0, (int)(x / cs)));
            var j = Math.Min(depth - 1, Math.Max(0, (int)(z / cs)));
            var lo = ModuleUnits.WallHalf + body;
            if (z < lo && south[i] != ModuleEdge.Wall) return true;
            if (z > DepthMetres - lo && north[i] != ModuleEdge.Wall) return true;
            if (x < lo && west[j] != ModuleEdge.Wall) return true;
            if (x > WidthMetres - lo && east[j] != ModuleEdge.Wall) return true;
            return false;
        }

        static readonly int[][] Steps = { new[] { 1, 0 }, new[] { -1, 0 }, new[] { 0, 1 }, new[] { 0, -1 } };

        /// <summary>The axis-aligned box a prop covers, in module metres.</summary>
        public static void Bounds(ModuleProp p, float[] f, out float x0, out float z0, out float x1, out float z1)
        {
            var rad = p.yaw * (Math.PI / 180.0);
            float c = (float)Math.Cos(rad), s = (float)Math.Sin(rad);
            x0 = z0 = float.MaxValue;
            x1 = z1 = float.MinValue;
            foreach (var cx in new[] { f[0], f[2] })
            foreach (var cz in new[] { f[1], f[3] })
            {
                // Unity yaw: x' = x cos + z sin, z' = -x sin + z cos.
                var wx = p.x + cx * c + cz * s;
                var wz = p.z - cx * s + cz * c;
                if (wx < x0) x0 = wx; if (wx > x1) x1 = wx;
                if (wz < z0) z0 = wz; if (wz > z1) z1 = wz;
            }
        }

        /// <summary>Floor kept clear inside every opening of the perimeter, as (x0, z0, x1, z1) in module metres.</summary>
        public List<float[]> EntryStrips()
        {
            var cs = MapGrid.CellSize;
            var d = ModuleUnits.EntryClearDepth + ModuleUnits.WallHalf;
            var strips = new List<float[]>();
            for (var i = 0; i < width; i++)
            {
                if (south[i] != ModuleEdge.Wall) strips.Add(new[] { i * cs, 0f, (i + 1) * cs, d });
                if (north[i] != ModuleEdge.Wall) strips.Add(new[] { i * cs, DepthMetres - d, (i + 1) * cs, DepthMetres });
            }
            for (var j = 0; j < depth; j++)
            {
                if (west[j] != ModuleEdge.Wall) strips.Add(new[] { 0f, j * cs, d, (j + 1) * cs });
                if (east[j] != ModuleEdge.Wall) strips.Add(new[] { WidthMetres - d, j * cs, WidthMetres, (j + 1) * cs });
            }
            return strips;
        }

        public static EdgeKind ToEdge(ModuleEdge e) => e == ModuleEdge.Open ? EdgeKind.Open : e == ModuleEdge.Arch ? EdgeKind.Arch : EdgeKind.Wall;
    }
}
