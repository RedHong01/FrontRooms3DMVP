using System;
using System.Collections.Generic;
using System.IO;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Hunts across the built map with furniture in the way, without playing the
/// game. It builds the level profile's map around the spawn (with the real
/// Office dressing when the kit is there), scatters test boxes in every open
/// room (desk to cabinet sizes, no aisles promised), then sends the Relay to
/// 60 points 5–14 cells away, frame by frame at 60 Hz.
/// It checks: no exceptions; the body never stands in a wall, column or door;
/// it never stands in furniture except while it passes through it with no
/// way round; and how many hunts arrive.
/// Writes Verification/relay-nav-test.json.
/// Headless: -executeMethod FrontRoomsRelayNavTest.RunBatch -quit (throws on FAIL).
/// </summary>
public static class FrontRoomsRelayNavTest
{
    const int Trials = 60;
    const float Dt = 1f / 60f, TrialSeconds = 30f;

    [Serializable]
    sealed class Report
    {
        public string verdict;
        public int seed;
        public int boxes;
        public int officeRoomsDressed;
        public int trials;
        public int arrived;
        public int endedBeside;
        public int ghosts;
        public int exceptions;
        public int wallFrames;
        public int furnitureFramesNotGhosting;
        public float averageSeconds;
        public float worstPlanMs;
        public List<string> failures = new List<string>();
    }

    [MenuItem("FrontRooms/Map/Test Relay navigation")]
    public static void Run() => Execute(false);

    public static void RunBatch() => Execute(true);

    static void Execute(bool throwOnFail)
    {
        var report = new Report();
        var root = new GameObject("RELAY NAV TEST") { hideFlags = HideFlags.DontSave };
        root.transform.position = new Vector3(-5000f, 0f, -5000f);
        var boxes = new HashSet<Collider>();
        try
        {
            var world = root.AddComponent<FrontRoomsMapWorld>();
            world.Profile = FrontRoomsLevelProfiles.Resolve();
            world.BuildForCapture();
            report.seed = world.Seed;
            report.officeRoomsDressed = 0;
            foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name == "office dressing") report.officeRoomsDressed++;

            // Test furniture in every open room of the central 3 x 3 chunks.
            var rng = new System.Random(12345);
            var cs = MapGrid.CellSize;
            var mid = MapGrid.ChunkOf(world.CellOf(world.SpawnWorldPosition));
            for (var cy = mid.y - 1; cy <= mid.y + 1; cy++)
            for (var cx = mid.x - 1; cx <= mid.x + 1; cx++)
            {
                var data = world.Cache.Get(new GridCoord(cx, cy));
                for (var r = 0; r < data.rooms.Length; r++)
                {
                    if (!data.RoomIntact(r)) continue;
                    var room = data.rooms[r];
                    var area = room.w * room.h * cs * cs;
                    var count = (int)(area / 7f);
                    for (var k = 0; k < count; k++)
                    {
                        var size = new Vector3(.5f + (float)rng.NextDouble() * 1.1f, .75f + (float)rng.NextDouble() * .85f, .5f + (float)rng.NextDouble() * .5f);
                        if (rng.Next(2) == 0) size = new Vector3(size.z, size.y, size.x);
                        // Keep 1.2 m off the room's boundary, as the keep-clear strips would.
                        var x = room.x * cs + 1.2f + size.x * .5f + (float)rng.NextDouble() * Mathf.Max(0f, room.w * cs - 2.4f - size.x);
                        var z = room.y * cs + 1.2f + size.z * .5f + (float)rng.NextDouble() * Mathf.Max(0f, room.h * cs - 2.4f - size.z);
                        var local = new Vector3(cx * MapGrid.ChunkSize + x, size.y * .5f, cy * MapGrid.ChunkSize + z);
                        var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        box.name = "test furniture";
                        box.transform.SetParent(root.transform, false);
                        box.transform.localPosition = local;
                        box.transform.localScale = size;
                        boxes.Add(box.GetComponent<Collider>());
                        report.boxes++;
                    }
                }
            }
            Physics.SyncTransforms();

            var player = new GameObject("test player").transform;
            player.SetParent(root.transform, false);
            var playerCollider = player.gameObject.AddComponent<CapsuleCollider>();
            playerCollider.height = ModuleUnits.PlayerHeight;
            playerCollider.radius = ModuleUnits.PlayerRadius;
            playerCollider.center = Vector3.up * (ModuleUnits.PlayerHeight * .5f);
            // Blind, so every trial is a hunt by ear; the player stands at the goal.
            var tuning = new FrontRoomsHunterTuning { sightRange = 0f };
            var hunter = new FrontRoomsMapHunter(world, tuning, playerCollider, null, 7);

            var cells = new List<GridCoord>();
            var o = MapGrid.ChunkOrigin(mid);
            for (var y = o.y - MapGrid.ChunkCells; y < o.y + 2 * MapGrid.ChunkCells; y++)
            for (var x = o.x - MapGrid.ChunkCells; x < o.x + 2 * MapGrid.ChunkCells; x++)
                cells.Add(new GridCoord(x, y));

            var probe = new Collider[16];
            var totalSeconds = 0f;
            var stopwatch = new System.Diagnostics.Stopwatch();
            for (var trial = 0; trial < Trials * 4 && report.trials < Trials; trial++)
            {
                var start = cells[rng.Next(cells.Count)];
                var goal = Reachable(world, start, rng, 5, 14);
                if (goal == start) continue;
                var startFeet = world.CellCenter(start);
                if (Touches(startFeet, probe, null, playerCollider)) continue;
                var goalFeet = world.CellCenter(goal);
                report.trials++;
                player.position = goalFeet;
                Physics.SyncTransforms();
                hunter.DebugPlace(startFeet);
                hunter.Noise(goalFeet, 1000f);
                var arrived = false;
                var t = 0f;
                for (; t < TrialSeconds; t += Dt)
                {
                    try
                    {
                        stopwatch.Restart();
                        hunter.Tick(Dt, goalFeet, goalFeet + Vector3.up * ModuleUnits.PlayerEye, Vector3.forward);
                        stopwatch.Stop();
                        report.worstPlanMs = Mathf.Max(report.worstPlanMs, (float)stopwatch.Elapsed.TotalMilliseconds);
                        world.TickDoorsForTools(Dt);
                        Physics.SyncTransforms();
                    }
                    catch (Exception e)
                    {
                        report.exceptions++;
                        if (report.failures.Count < 12) report.failures.Add("trial " + report.trials + ": " + e.GetType().Name + " " + e.Message);
                        break;
                    }
                    var hit = Touch(hunter.Position, probe, playerCollider, world, boxes, out var touched);
                    if (hit == 1)
                    {
                        report.wallFrames++;
                        if (report.failures.Count < 12) report.failures.Add("trial " + report.trials + ": body in architecture at " + hunter.Position + " (" + world.CellOf(hunter.Position) + ")");
                    }
                    else if (hit == 2 && !hunter.Ghosting)
                    {
                        report.furnitureFramesNotGhosting++;
                        if (report.failures.Count < 24) report.failures.Add("trial " + report.trials + " t " + t.ToString("F2") + ": in furniture '" + touched + "' at " + hunter.Position.ToString("F2") + " " + hunter.State + " · " + hunter.DebugSteering);
                    }
                    if (t > TrialSeconds - .5f && report.failures.Count < 24) report.failures.Add("trial " + report.trials + " stuck t " + t.ToString("F2") + " at " + hunter.Position.ToString("F2") + " · " + hunter.DebugSteering);
                    if (hunter.State == HunterState.Search)
                    {
                        arrived = true;
                        break;
                    }
                }
                if (arrived)
                {
                    report.arrived++;
                    totalSeconds += t;
                    if (Flat(hunter.Position - goalFeet) > .1f) report.endedBeside++;
                }
                else if (report.failures.Count < 12) report.failures.Add("trial " + report.trials + ": no arrival from " + start + " to " + goal + ", ended at " + world.CellOf(hunter.Position) + " in " + hunter.State);
            }
            report.ghosts = hunter.Ghosts;
            report.averageSeconds = report.arrived > 0 ? totalSeconds / report.arrived : 0f;
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(root);
        }

        var pass = report.trials >= Trials && report.exceptions == 0 && report.wallFrames == 0
            && report.furnitureFramesNotGhosting == 0 && report.arrived >= report.trials * .95f;
        report.verdict = (pass ? "PASS" : "FAIL") + " · " + report.arrived + "/" + report.trials + " hunts arrived, " + report.ghosts + " pass-throughs, "
            + report.wallFrames + " frames in architecture, " + report.furnitureFramesNotGhosting + " frames in furniture outside a pass-through, " + report.exceptions + " exceptions";
        var path = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "relay-nav-test.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        File.WriteAllText(path, JsonUtility.ToJson(report, true));
        if (pass) Debug.Log("[FrontRoomsMap] Relay navigation " + report.verdict);
        else Debug.LogError("[FrontRoomsMap] Relay navigation " + report.verdict + "\n" + string.Join("\n", report.failures));
        if (throwOnFail && !pass) throw new Exception(report.verdict);
    }

    static float Flat(Vector3 v) => new Vector2(v.x, v.z).magnitude;

    /// <summary>A cell reachable from start in between minSteps and maxSteps, through open edges and doors (not glass).</summary>
    static GridCoord Reachable(FrontRoomsMapWorld world, GridCoord start, System.Random rng, int minSteps, int maxSteps)
    {
        var depth = new Dictionary<GridCoord, int> { [start] = 0 };
        var queue = new Queue<GridCoord>();
        queue.Enqueue(start);
        var far = new List<GridCoord>();
        var steps = new[] { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) };
        while (queue.Count > 0)
        {
            var c = queue.Dequeue();
            var d = depth[c];
            if (d >= minSteps) far.Add(c);
            if (d >= maxSteps) continue;
            foreach (var s in steps)
            {
                var n = c + s;
                if (depth.ContainsKey(n) || !world.IsBuilt(n)) continue;
                var p = world.PassageBetween(c, n);
                if (p == FrontRoomsMapWorld.Passage.Wall || p == FrontRoomsMapWorld.Passage.Glass) continue;
                depth[n] = d + 1;
                queue.Enqueue(n);
            }
        }
        return far.Count == 0 ? start : far[rng.Next(far.Count)];
    }

    /// <summary>The Relay's tested body (0.4–1.95 m, r 0.3) touches anything besides the player.</summary>
    static bool Touches(Vector3 feet, Collider[] buffer, Transform ignore, Collider player)
    {
        var count = Physics.OverlapCapsuleNonAlloc(feet + Vector3.up * .7f, feet + Vector3.up * 1.65f, ModuleUnits.RelayRadius, buffer, ~0, QueryTriggerInteraction.Ignore);
        for (var i = 0; i < count; i++) if (buffer[i] != player) return true;
        return false;
    }

    /// <summary>0 nothing, 1 architecture (walls, columns, doors, glass), 2 furniture. A slightly smaller body than the planner's, so grazes don't count.</summary>
    static int Touch(Vector3 feet, Collider[] buffer, Collider player, FrontRoomsMapWorld world, HashSet<Collider> boxes, out string touched)
    {
        touched = null;
        var count = Physics.OverlapCapsuleNonAlloc(feet + Vector3.up * .7f, feet + Vector3.up * 1.65f, ModuleUnits.RelayRadius - .05f, buffer, ~0, QueryTriggerInteraction.Ignore);
        var result = 0;
        for (var i = 0; i < count; i++)
        {
            var c = buffer[i];
            if (c == null || c == player) continue;
            touched = c.name + (c.transform.parent != null ? " < " + c.transform.parent.name : "");
            if (world.IsArchitecture(c) && !world.IsOpenDoorLeaf(c)) return 1;
            result = 2;
        }
        return result;
    }
}
