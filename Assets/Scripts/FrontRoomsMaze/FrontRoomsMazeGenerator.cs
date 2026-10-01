using System;
using System.Collections.Generic;
using UnityEngine;

namespace FrontRooms.Maze
{
    /// <summary>
    /// Seeded room-and-connection generator for the FrontRooms labyrinth.
    /// It first creates a spanning tree so every cell is reachable, then adds a
    /// small, bounded number of loops to produce backtracking without becoming
    /// a uniform grid. The same seed produces the same layout in 2D and 3D.
    /// </summary>
    public static class FrontRoomsMazeGenerator
    {
        struct Rng
        {
            uint state;
            public Rng(int seed) { state = unchecked((uint)seed); if (state == 0) state = 0xA341316Cu; }
            public uint Next() { state ^= state << 13; state ^= state >> 17; state ^= state << 5; return state; }
            public int Range(int min, int max) { return max <= min ? min : min + (int)(Next() % (uint)(max - min)); }
            public float Value() { return (Next() & 0x00ffffffu) / 16777216f; }
        }

        struct EdgeKey : IEquatable<EdgeKey>
        {
            public readonly int a; public readonly int b;
            public EdgeKey(int first, int second) { a = Mathf.Min(first, second); b = Mathf.Max(first, second); }
            public bool Equals(EdgeKey other) { return a == other.a && b == other.b; }
            public override bool Equals(object obj) { return obj is EdgeKey && Equals((EdgeKey)obj); }
            public override int GetHashCode() { return (a * 397) ^ b; }
        }

        public static FrontRoomsMazeSpec Generate(int seed, int width = 9, int height = 7, float loopRatio = .18f)
        {
            width = Mathf.Clamp(width, 3, 31);
            height = Mathf.Clamp(height, 3, 31);
            loopRatio = Mathf.Clamp01(loopRatio);
            var spec = new FrontRoomsMazeSpec
            {
                seed = seed,
                width = width,
                height = height,
                requestedLoopRatio = loopRatio,
                start = new Vector2Int(0, height / 2),
                exit = new Vector2Int(width - 1, height / 2),
            };

            var count = width * height;
            var visited = new bool[count];
            var treeEdges = new HashSet<EdgeKey>();
            var allEdges = new List<EdgeKey>();
            var rng = new Rng(seed);
            for (var y = 0; y < height; y++)
                for (var x = 0; x < width; x++)
                {
                    var id = Id(x, y, width);
                    if (x + 1 < width) allEdges.Add(new EdgeKey(id, Id(x + 1, y, width)));
                    if (y + 1 < height) allEdges.Add(new EdgeKey(id, Id(x, y + 1, width)));
                }

            // Randomized depth-first carve. It gives long sightline breaks and
            // dead ends, unlike a perfectly regular room grid.
            var stack = new List<int> { Id(spec.start.x, spec.start.y, width) };
            visited[stack[0]] = true;
            while (stack.Count > 0)
            {
                var current = stack[stack.Count - 1];
                var cx = current % width;
                var cy = current / width;
                var choices = new List<int>(4);
                AddUnvisited(choices, cx + 1, cy, width, height, visited);
                AddUnvisited(choices, cx - 1, cy, width, height, visited);
                AddUnvisited(choices, cx, cy + 1, width, height, visited);
                AddUnvisited(choices, cx, cy - 1, width, height, visited);
                if (choices.Count == 0) { stack.RemoveAt(stack.Count - 1); continue; }
                var next = choices[rng.Range(0, choices.Count)];
                visited[next] = true;
                treeEdges.Add(new EdgeKey(current, next));
                stack.Add(next);
            }

            // Add a controlled number of non-tree connections. These are the
            // route-choice loops; they never remove the guaranteed tree path.
            var extras = new List<EdgeKey>();
            foreach (var edge in allEdges)
                if (!treeEdges.Contains(edge)) extras.Add(edge);
            Shuffle(extras, ref rng);
            var desiredLoops = Mathf.RoundToInt((count - 1) * loopRatio);
            var chosenLoops = Mathf.Min(desiredLoops, extras.Count);
            var openEdges = new HashSet<EdgeKey>(treeEdges);
            for (var i = 0; i < chosenLoops; i++) openEdges.Add(extras[i]);

            var distances = Distances(openEdges, spec.start, width, height);
            var exitDistances = Distances(openEdges, spec.exit, width, height);
            var mainPath = ShortestPath(openEdges, spec.start, spec.exit, width, height);
            var mainSet = new HashSet<int>(mainPath);
            for (var y = 0; y < height; y++)
                for (var x = 0; x < width; x++)
                {
                    var id = Id(x, y, width);
                    var type = AssignType(id, x, y, mainSet.Contains(id), distances[id], exitDistances[id], ref rng, spec.start, spec.exit);
                    spec.cells.Add(new FrontRoomsMazeCell
                    {
                        id = id,
                        coord = new Vector2Int(x, y),
                        type = type,
                        isMainRoute = mainSet.Contains(id),
                        distanceFromStart = distances[id],
                        distanceToExit = exitDistances[id],
                        seedRoll = (int)(rng.Next() & 0x7fffffff),
                        read = ReadFor(type),
                    });
                }

            var doorIndex = Mathf.Clamp(mainPath.Count / 2 - 1, 0, Mathf.Max(0, mainPath.Count - 2));
            var doorA = mainPath.Count > 1 ? mainPath[doorIndex] : -1;
            var doorB = mainPath.Count > 1 ? mainPath[doorIndex + 1] : -1;
            var connectionId = 0;
            foreach (var edge in openEdges)
            {
                var isMain = mainSet.Contains(edge.a) && mainSet.Contains(edge.b) && AreAdjacentOnPath(mainPath, edge.a, edge.b);
                var isDoorEdge = (edge.a == doorA && edge.b == doorB) || (edge.a == doorB && edge.b == doorA);
                var kind = isDoorEdge ? MazeConnectionKind.Door :
                    isMain ? MazeConnectionKind.Hall : (rng.Value() < .42f ? MazeConnectionKind.Threshold : MazeConnectionKind.Service);
                spec.connections.Add(new FrontRoomsMazeConnection
                {
                    id = connectionId++, from = edge.a, to = edge.b, kind = kind, open = true,
                    isMainRoute = isMain, requiresKey = kind == MazeConnectionKind.Door,
                    traversalSeconds = kind == MazeConnectionKind.Door ? 4.2f : kind == MazeConnectionKind.Service ? 2.8f : 1.7f,
                });
            }
            spec.mainRoute.AddRange(mainPath);
            spec.validation = Validate(spec);
            return spec;
        }

        public static FrontRoomsMazeValidation Validate(FrontRoomsMazeSpec spec)
        {
            var result = new FrontRoomsMazeValidation { totalCells = spec == null ? 0 : spec.width * spec.height };
            if (spec == null) { result.errors.Add("spec is null"); return result; }
            var open = new HashSet<EdgeKey>();
            foreach (var c in spec.connections) open.Add(new EdgeKey(c.from, c.to));
            var distances = Distances(open, spec.start, spec.width, spec.height);
            var reachable = 0;
            foreach (var distance in distances.Values) if (distance < int.MaxValue) reachable++;
            result.reachableCells = reachable;
            result.openConnections = open.Count;
            result.loopConnections = Mathf.Max(0, open.Count - (spec.width * spec.height - 1));
            result.loopRatio = spec.width * spec.height <= 1 ? 0f : result.loopConnections / (float)(spec.width * spec.height - 1);
            result.mainPathLength = spec.mainRoute == null ? 0 : spec.mainRoute.Count;
            if (reachable != result.totalCells) result.errors.Add("unreachable room cell");
            if (spec.mainRoute == null || spec.mainRoute.Count < 2) result.errors.Add("missing start to exit route");
            if (spec.cells.Count != result.totalCells) result.errors.Add("cell list mismatch");
            if (spec.connections.Count < result.totalCells - 1) result.errors.Add("connection graph is not spanning");
            if (result.loopRatio < .05f || result.loopRatio > .35f) result.errors.Add("loop ratio outside playable range");
            result.passed = result.errors.Count == 0;
            return result;
        }

        static MazeRoomType AssignType(int id, int x, int y, bool main, int fromStart, int toExit, ref Rng rng, Vector2Int start, Vector2Int exit)
        {
            if (x == start.x && y == start.y) return MazeRoomType.Lobby;
            if (x == exit.x && y == exit.y) return MazeRoomType.Exit;
            if (main && fromStart > 2 && toExit > 2 && rng.Value() < .11f) return MazeRoomType.Threat;
            if (!main && rng.Value() < .10f) return MazeRoomType.Landmark;
            var roll = rng.Value();
            if (roll < .18f) return MazeRoomType.Shift;
            if (roll < .30f) return MazeRoomType.Office;
            return MazeRoomType.Standard;
        }

        static string ReadFor(MazeRoomType type)
        {
            switch (type)
            {
                case MazeRoomType.Lobby: return "entry / stable fluorescent";
                case MazeRoomType.Shift: return "familiar geometry with one shifted seam";
                case MazeRoomType.Office: return "wider room / sightline break";
                case MazeRoomType.Threat: return "sound and light pressure / keep moving";
                case MazeRoomType.Landmark: return "rare landmark / reset orientation";
                case MazeRoomType.Exit: return "cold contrast / route completion";
                default: return "80% familiar / 20% wrong";
            }
        }

        static Dictionary<int, int> Distances(HashSet<EdgeKey> edges, Vector2Int start, int width, int height)
        {
            var result = new Dictionary<int, int>();
            for (var i = 0; i < width * height; i++) result[i] = int.MaxValue;
            var q = new Queue<int>();
            var startId = Id(start.x, start.y, width); result[startId] = 0; q.Enqueue(startId);
            while (q.Count > 0)
            {
                var id = q.Dequeue();
                foreach (var n in Neighbours(id, width, height))
                {
                    if (!edges.Contains(new EdgeKey(id, n)) || result[n] != int.MaxValue) continue;
                    result[n] = result[id] + 1; q.Enqueue(n);
                }
            }
            return result;
        }

        static List<int> ShortestPath(HashSet<EdgeKey> edges, Vector2Int start, Vector2Int exit, int width, int height)
        {
            var startId = Id(start.x, start.y, width); var exitId = Id(exit.x, exit.y, width);
            var previous = new Dictionary<int, int>(); var q = new Queue<int>(); q.Enqueue(startId); previous[startId] = -1;
            while (q.Count > 0)
            {
                var id = q.Dequeue(); if (id == exitId) break;
                foreach (var n in Neighbours(id, width, height))
                    if (edges.Contains(new EdgeKey(id, n)) && !previous.ContainsKey(n)) { previous[n] = id; q.Enqueue(n); }
            }
            var path = new List<int>(); if (!previous.ContainsKey(exitId)) return path;
            for (var id = exitId; id >= 0; id = previous[id]) { path.Add(id); if (id == startId) break; }
            path.Reverse(); return path;
        }

        static bool AreAdjacentOnPath(List<int> path, int a, int b)
        {
            for (var i = 0; i < path.Count - 1; i++) if ((path[i] == a && path[i + 1] == b) || (path[i] == b && path[i + 1] == a)) return true;
            return false;
        }

        static IEnumerable<int> Neighbours(int id, int width, int height)
        {
            var x = id % width; var y = id / width;
            if (x > 0) yield return id - 1; if (x + 1 < width) yield return id + 1;
            if (y > 0) yield return id - width; if (y + 1 < height) yield return id + width;
        }
        static void AddUnvisited(List<int> list, int x, int y, int width, int height, bool[] visited)
        {
            if (x >= 0 && y >= 0 && x < width && y < height) { var id = Id(x, y, width); if (!visited[id]) list.Add(id); }
        }
        static int Id(int x, int y, int width) { return y * width + x; }
        static void Shuffle<T>(List<T> list, ref Rng rng)
        {
            for (var i = list.Count - 1; i > 0; i--) { var j = rng.Range(0, i + 1); var t = list[i]; list[i] = list[j]; list[j] = t; }
        }
    }
}
