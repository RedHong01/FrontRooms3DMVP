using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The map's interaction hooks and the module build rules, checked without
/// playing the game:
/// - the Relay's door blows: BlowIndex 0..4 at 0.5 / 1.0 / 1.5 / 2.0 / 2.4 s
///   into BreakDoor, the door giving at 2.5 s (the rig's DoorBlow contract);
/// - DoorSqueeze: 0 at a shut door, near 1 on the line of the open one it
///   walks through, 0 in the middle of a room;
/// - ListenPoint: the last noise heard;
/// - DoorUnlocked (doors need keys): a locked door stays shut and raises
///   DoorLocked; with the key it raises DoorUnlocked once, with the zone and
///   the lock point on the opener's side, then swings after UnlockSwingDelay;
///   a second use while the key turns does nothing, and later uses are plain;
///   with no delay it swings at once; with keys off it never raises;
/// - module props on a column are left out of the build;
/// - the Office kit filling a module keeps off its inner walls and inner doorways;
/// - a chunk whose build throws is undone, logged, not retried while in range,
///   and counts as done for ReadyAround / Settled;
/// - P4 tiers: the Relay's effective tuning per tier, blows 5 → 3, a break keeps
///   its length when the tier changes mid-break, zones → tier, chunks keep the
///   tier they were generated at (until a shift), module tier ranges, lamp odds;
/// - P4 markers: a module key spot takes the zone key; the Relay appears at a
///   module Relay entry behind the player and raises Arrived with its tag;
/// - P4 live tuning: ApplyLive moves the build radius; ReplaceModule rebuilds
///   only the module's chunk.
/// Writes Verification/map-interaction-tests.json.
/// Headless: -executeMethod FrontRoomsMapInteractionTests.RunBatch -quit (throws on FAIL).
/// </summary>
public static class FrontRoomsMapInteractionTests
{
    const float Dt = 1f / 60f;

    [Serializable]
    sealed class Report
    {
        public string verdict;
        public int passed, failed;
        public List<string> checks = new List<string>();
    }

    static Report report;

    static void Check(bool ok, string what)
    {
        if (ok) report.passed++; else report.failed++;
        report.checks.Add((ok ? "ok   " : "FAIL ") + what);
    }

    [MenuItem("FrontRooms/Map/Test map interactions")]
    public static void Run() => Execute(false);

    public static void RunBatch() => Execute(true);

    static void Execute(bool throwOnFail)
    {
        report = new Report();
        var ambientMode = RenderSettings.ambientMode;
        var sky = RenderSettings.ambientSkyColor;
        var equator = RenderSettings.ambientEquatorColor;
        var ground = RenderSettings.ambientGroundColor;
        var reflection = RenderSettings.reflectionIntensity;
        var fog = RenderSettings.fog;
        var fogMode = RenderSettings.fogMode;
        var fogColor = RenderSettings.fogColor;
        var fogDensity = RenderSettings.fogDensity;
        var skybox = RenderSettings.skybox;
        var roots = new List<GameObject>();
        var profiles = new List<FrontRoomsLevelProfile>();
        try
        {
            Relay(roots);
            Keys(roots, profiles, 1.1f);
            Keys(roots, profiles, 0f);
            Columns(roots, profiles);
            InnerWalls(roots, profiles);
            FillKeepsClear(roots, profiles);
            BuildGuard(roots);
            Tiers(roots, profiles);
            KeySpot(roots, profiles);
            RelayEntry(roots, profiles);
            Live(roots, profiles);
        }
        catch (Exception e)
        {
            Check(false, "exception: " + e.GetType().Name + " " + e.Message + "\n" + e.StackTrace);
        }
        finally
        {
            foreach (var r in roots)
            {
                if (r == null) continue;
                // Free the chunk meshes and the map's own materials (OnDestroy does not run for it in edit mode).
                var w = r.GetComponent<FrontRoomsMapWorld>();
                if (w != null) w.Release();
                UnityEngine.Object.DestroyImmediate(r);
            }
            foreach (var p in profiles) if (p != null) UnityEngine.Object.DestroyImmediate(p);
            RenderSettings.ambientMode = ambientMode;
            RenderSettings.ambientSkyColor = sky;
            RenderSettings.ambientEquatorColor = equator;
            RenderSettings.ambientGroundColor = ground;
            RenderSettings.reflectionIntensity = reflection;
            RenderSettings.fog = fog;
            RenderSettings.fogMode = fogMode;
            RenderSettings.fogColor = fogColor;
            RenderSettings.fogDensity = fogDensity;
            RenderSettings.skybox = skybox;
            DynamicGI.UpdateEnvironment();
        }

        var pass = report.failed == 0 && report.passed > 0;
        report.verdict = (pass ? "PASS" : "FAIL") + ": " + report.passed + " passed, " + report.failed + " failed";
        var path = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "map-interaction-tests.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        File.WriteAllText(path, JsonUtility.ToJson(report, true));
        var text = "[MapInteractionTests] " + report.verdict + "\n" + string.Join("\n", report.checks);
        if (pass) Debug.Log(text); else Debug.LogError(text);
        if (throwOnFail && !pass) throw new Exception(report.verdict);
    }

    static readonly GridCoord[] Steps = { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) };

    static FrontRoomsMapWorld World(List<GameObject> roots, FrontRoomsLevelProfile profile, float period, string name)
    {
        var root = new GameObject(name) { hideFlags = HideFlags.DontSave };
        roots.Add(root);
        // Far from the open scene, on whole world periods so surfaces stay on the lattice.
        root.transform.position = new Vector3(period * ModuleUnits.WorldPeriod, 0f, -27f * ModuleUnits.WorldPeriod);
        var world = root.AddComponent<FrontRoomsMapWorld>();
        world.Profile = profile;
        return world;
    }

    /// <summary>A closed door between built cells a (near) and b, with an open cell c behind a.</summary>
    static bool FindDoor(FrontRoomsMapWorld world, out GridCoord a, out GridCoord b, out GridCoord c)
    {
        a = b = c = default;
        var mid = world.CellOf(world.SpawnWorldPosition);
        for (var y = mid.y - 12; y <= mid.y + 12; y++)
        for (var x = mid.x - 12; x <= mid.x + 12; x++)
        {
            var cell = new GridCoord(x, y);
            if (!world.IsBuilt(cell)) continue;
            foreach (var s in Steps)
            {
                var other = cell + s;
                if (!world.IsBuilt(other) || world.Cache.Edge(cell, other) != EdgeKind.Door) continue;
                var door = world.DoorBetween(cell, other);
                if (door == null || door.open || door.broken) continue;
                // Directly opposite the door, so the only short route from c to b is through a.
                var behind = new GridCoord(cell.x - s.x, cell.y - s.y);
                if (!world.IsBuilt(behind) || world.PassageBetween(cell, behind) != FrontRoomsMapWorld.Passage.Open) continue;
                a = cell; b = other; c = behind;
                return true;
            }
        }
        return false;
    }

    // ---------- The Relay: blows, squeeze, listen point ----------

    static void Relay(List<GameObject> roots)
    {
        var world = World(roots, FrontRoomsLevelProfiles.Resolve(), -27f, "MAP INTERACTION TEST / relay");
        world.BuildForCapture();
        if (!FindDoor(world, out var a, out var b, out var c)) { Check(false, "relay: no closed door with an open cell behind it near the spawn"); return; }
        var door = world.DoorBetween(a, b);

        var player = new GameObject("test player").transform;
        player.SetParent(world.transform, false);
        var body = player.gameObject.AddComponent<CapsuleCollider>();
        body.height = ModuleUnits.PlayerHeight;
        body.radius = ModuleUnits.PlayerRadius;
        body.center = Vector3.up * (ModuleUnits.PlayerHeight * .5f);
        // Blind: it hunts by ear, through the shut door.
        var tuning = new FrontRoomsHunterTuning { sightRange = 0f };
        var hunter = new FrontRoomsMapHunter(world, tuning, body, null, 5);
        Check(hunter.BlowCount == 5, "relay: BlowCount " + hunter.BlowCount + " at breakDoorSeconds " + tuning.breakDoorSeconds + " (expected 5)");

        var target = world.CellCenter(b);
        player.position = target + new Vector3(0f, 0f, 0f);
        Physics.SyncTransforms();
        hunter.DebugPlace(world.CellCenter(c));
        var middleSqueeze = hunter.DoorSqueeze;
        hunter.Noise(target, 1000f);
        Check(hunter.ListenPoint.HasValue && (hunter.ListenPoint.Value - target).sqrMagnitude < 1e-6f, "relay: ListenPoint is the noise it heard");

        var blows = new List<(int index, float at)>();
        var breakAt = -1f;
        var t = 0f;
        var breakStart = -1f;
        hunter.DoorBlow += _ => blows.Add((hunter.BlowIndex, t - breakStart));
        world.DoorBroken += _ => breakAt = t - breakStart;
        var squeezeAtShutDoor = 0f;
        var maxSqueeze = 0f;
        var crossed = false;
        for (; t < 40f; t += Dt)
        {
            hunter.Tick(Dt, target, target + Vector3.up * ModuleUnits.PlayerEye, Vector3.forward);
            world.TickDoorsForTools(Dt);
            Physics.SyncTransforms();
            // StateTime is 0 on the tick it enters BreakDoor; later events are logged as StateTime.
            if (hunter.State == HunterState.BreakDoor && breakStart < 0f) breakStart = t - hunter.StateTime;
            if (hunter.State == HunterState.BreakDoor && !door.broken) squeezeAtShutDoor = Mathf.Max(squeezeAtShutDoor, hunter.DoorSqueeze);
            if (door.broken) maxSqueeze = Mathf.Max(maxSqueeze, hunter.DoorSqueeze);
            if (world.CellOf(hunter.Position) == b) crossed = true;
            if (crossed && hunter.State == HunterState.Search) break;
        }
        Check(breakStart >= 0f && door.broken, "relay: it broke into the door " + a + "→" + b);
        var expected = new[] { .5f, 1f, 1.5f, 2f, tuning.breakDoorSeconds - .1f };
        Check(blows.Count == 5, "relay: " + blows.Count + " blows (expected 5): " + string.Join(", ", blows.Select(x => x.index + "@" + x.at.ToString("0.000"))));
        for (var i = 0; i < Mathf.Min(5, blows.Count); i++)
            Check(blows[i].index == i && Mathf.Abs(blows[i].at - expected[i]) <= Dt * .6f, "relay: blow " + blows[i].index + " at " + blows[i].at.ToString("0.000") + " s (expected " + i + " at " + expected[i].ToString("0.00") + ")");
        Check(Mathf.Abs(breakAt - tuning.breakDoorSeconds) <= Dt * .6f && blows.Count > 0 && breakAt > blows[blows.Count - 1].at + .05f,
            "relay: the door gives at " + breakAt.ToString("0.000") + " s, after the last blow (expected " + tuning.breakDoorSeconds + ")");
        Check(squeezeAtShutDoor == 0f, "relay: DoorSqueeze 0 while the door is shut (" + squeezeAtShutDoor.ToString("0.00") + ")");
        Check(crossed && maxSqueeze >= .85f && maxSqueeze <= 1f, "relay: walking through the broken door, DoorSqueeze peaks at " + maxSqueeze.ToString("0.00") + " (expected ≥ 0.85)");
        Check(middleSqueeze == 0f, "relay: DoorSqueeze 0 in the middle of a cell (" + middleSqueeze.ToString("0.00") + ")");
    }

    // ---------- Keys: DoorUnlocked and the swing delay ----------

    static void Keys(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles, float delay)
    {
        var label = "keys (delay " + delay.ToString("0.0") + " s): ";
        var profile = UnityEngine.Object.Instantiate(FrontRoomsLevelProfiles.Resolve());
        profile.hideFlags = HideFlags.DontSave;
        profile.doorsNeedKeys = true;
        profiles.Add(profile);
        var world = World(roots, profile, delay > 0f ? -28f : -29f, "MAP INTERACTION TEST / keys");
        world.BuildForCapture();
        world.UnlockSwingDelay = delay;
        if (!FindDoor(world, out var a, out var b, out _)) { Check(false, label + "no closed door near the spawn"); return; }
        var door = world.DoorBetween(a, b);
        var player = world.Player;
        player.position = world.CellCenter(a) + Vector3.up * .05f;

        var unlocked = new List<(FrontRoomsMapWorld.Door door, GridCoord zone, Vector3 at)>();
        var locked = 0;
        var moved = 0;
        world.DoorUnlocked += (d, z, p) => unlocked.Add((d, z, p));
        world.DoorLocked += _ => locked++;
        world.DoorMoved += _ => moved++;

        world.Use(door.leaf);
        Check(locked == 1 && !door.open && unlocked.Count == 0, label + "without the key the door stays shut and raises DoorLocked (locked " + locked + ", open " + door.open + ")");

        // Give the key of the player's zone (as walking over it would).
        var zone = world.ZoneOf(a).id;
        var keys = (HashSet<GridCoord>)typeof(FrontRoomsMapWorld).GetField("keysHeld", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).GetValue(world);
        keys.Add(zone);
        world.Use(door.leaf);
        Check(unlocked.Count == 1 && unlocked[0].door == door && unlocked[0].zone == zone, label + "with the key: DoorUnlocked once, for this door and zone " + zone);
        if (unlocked.Count > 0)
        {
            var at = unlocked[0].at;
            var rotation = door.hinge.parent.rotation * door.closed;
            var along = rotation * Vector3.forward;
            var across = rotation * Vector3.right;
            var offset = at - door.position;
            var playerSide = Mathf.Sign(Vector3.Dot(player.position - door.position, across));
            var face = Vector3.Dot(offset, across);
            Check(Mathf.Abs(offset.y - ModuleUnits.DoorHandleHeight) < .01f
                && Mathf.Abs(Vector3.Dot(offset, along) - (ModuleUnits.DoorWidth * .5f - ModuleUnits.DoorHandleInset)) < .01f
                && Mathf.Sign(face) == playerSide && Mathf.Abs(Mathf.Abs(face) - (ModuleUnits.DoorLeafThickness * .5f + ModuleUnits.DoorHandleProud)) < .01f,
                label + "lock point " + offset.ToString("F3") + " from the opening: 1.0 m up, 0.08 m in from the latch jamb, on the player's face");
        }
        if (delay > 0f)
        {
            Check(!door.open, label + "the door waits while the key turns");
            world.Use(door.leaf);
            Check(unlocked.Count == 1 && !door.open, label + "a second use while the key turns does nothing");
            for (var s = 0f; s < delay - .1f; s += Dt) world.TickDoorsForTools(Dt);
            Check(!door.open, label + "still shut just before the delay ends");
            for (var s = 0f; s < .2f; s += Dt) world.TickDoorsForTools(Dt);
            Check(door.open, label + "it swings once the delay is over");
        }
        else Check(door.open, label + "no delay: it swings at once");
        for (var s = 0f; s < 1f; s += Dt) world.TickDoorsForTools(Dt);
        world.Use(door.leaf);
        for (var s = 0f; s < 1f; s += Dt) world.TickDoorsForTools(Dt);
        Check(!door.open, label + "shut again");
        world.Use(door.leaf);
        Check(door.open && unlocked.Count == 1, label + "opening it again is plain: no second DoorUnlocked, no wait");
        // From the other side, whose zone's key the player does not hold: a door a key has opened stays unlocked.
        for (var s = 0f; s < 1f; s += Dt) world.TickDoorsForTools(Dt);
        world.Use(door.leaf);
        for (var s = 0f; s < 1f; s += Dt) world.TickDoorsForTools(Dt);
        player.position = world.CellCenter(b) + Vector3.up * .05f;
        var otherZone = world.ZoneOf(b).id;
        var lockedBefore = locked;
        world.Use(door.leaf);
        Check(otherZone != zone && !keys.Contains(otherZone) && door.open && locked == lockedBefore && unlocked.Count == 1,
            label + "from the far side without its zone's key, the unlocked door opens (no DoorLocked, no second DoorUnlocked)");

        // Keys off: never raised.
        if (delay > 0f) return;
        var keysOff = UnityEngine.Object.Instantiate(FrontRoomsLevelProfiles.Resolve());
        keysOff.hideFlags = HideFlags.DontSave;
        keysOff.doorsNeedKeys = false;
        profiles.Add(keysOff);
        var plain = World(roots, keysOff, -30f, "MAP INTERACTION TEST / no keys");
        plain.BuildForCapture();
        var count = 0;
        plain.DoorUnlocked += (_, __, ___) => count++;
        if (FindDoor(plain, out var pa, out var pb, out _))
        {
            plain.Player.position = plain.CellCenter(pa) + Vector3.up * .05f;
            var d = plain.DoorBetween(pa, pb);
            plain.Use(d.leaf);
            Check(d.open && count == 0, "keys off: the door opens and DoorUnlocked is never raised");
        }
        else Check(false, "keys off: no closed door near the spawn");
    }

    // ---------- P4: tiers ----------

    static void Tiers(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        var rules = new FrontRoomsTierRules();
        var baseTuning = new FrontRoomsHunterTuning();
        var counts = new List<int>();
        for (var t = 1; t <= 5; t++)
        {
            var e = new FrontRoomsHunterTuning();
            e.CopyFrom(baseTuning);
            rules.At(t).ApplyTo(e);
            counts.Add(Mathf.Max(1, Mathf.RoundToInt(e.breakDoorSeconds / .5f)));
            if (t == 5)
                Check(Mathf.Abs(e.chaseSpeed - 4.2f * 1.29f) < .01f && Mathf.Abs(e.hearing - 1.4f * 1.6f) < .01f && Mathf.Abs(e.breakDoorSeconds - 1.3f) < .01f && Mathf.Abs(e.searchMaxSeconds - 24f) < .01f,
                    "tiers: tier 5 is chase " + e.chaseSpeed.ToString("0.00") + " m/s, hearing " + e.hearing.ToString("0.00") + ", break " + e.breakDoorSeconds.ToString("0.00") + " s, search " + e.searchMaxSeconds.ToString("0.0") + " s");
        }
        Check(string.Join(",", counts) == "5,4,4,3,3", "tiers: blows per door by tier " + string.Join(",", counts) + " (expected 5,4,4,3,3)");
        Check(baseTuning.chaseSpeed == 4.2f && baseTuning.breakDoorSeconds == 2.5f, "tiers: the base tuning is never changed");
        Check(rules.TierForZones(1) == 1 && rules.TierForZones(4) == 1 && rules.TierForZones(5) == 2 && rules.TierForZones(16) == 4 && rules.TierForZones(40) == 5,
            "tiers: zones 1-4 tier 1, 5 tier 2, 16 tier 4, 40 capped at 5");
        var t1 = rules.At(1);
        Check(t1.LampMode(.61f) == 0 && t1.LampMode(.63f) == 1 && t1.LampMode(.83f) == 2 && t1.LampMode(.93f) == 3 && t1.LampMode(.98f) == 4,
            "tiers: tier 1 lamp odds are the old 62 / 20 / 10 / 5 / 3");

        // A break keeps the length it started with when the tuning changes mid-break.
        var world = World(roots, FrontRoomsLevelProfiles.Resolve(), -34f, "MAP INTERACTION TEST / tier break");
        world.BuildForCapture();
        if (FindDoor(world, out var a, out var b, out var c))
        {
            var player = new GameObject("test player").transform;
            player.SetParent(world.transform, false);
            var body = player.gameObject.AddComponent<CapsuleCollider>();
            body.height = ModuleUnits.PlayerHeight;
            body.radius = ModuleUnits.PlayerRadius;
            body.center = Vector3.up * (ModuleUnits.PlayerHeight * .5f);
            var tuning = new FrontRoomsHunterTuning { sightRange = 0f };
            var hunter = new FrontRoomsMapHunter(world, tuning, body, null, 5);
            var target = world.CellCenter(b);
            player.position = target;
            Physics.SyncTransforms();
            hunter.DebugPlace(world.CellCenter(c));
            hunter.Noise(target, 1000f);
            var blows = new List<(int index, int count)>();
            hunter.DoorBlow += _ => blows.Add((hunter.BlowIndex, hunter.BlowCount));
            var door = world.DoorBetween(a, b);
            var changed = false;
            for (var t = 0f; t < 30f && !door.broken; t += Dt)
            {
                hunter.Tick(Dt, target, target + Vector3.up * ModuleUnits.PlayerEye, Vector3.forward);
                world.TickDoorsForTools(Dt);
                Physics.SyncTransforms();
                // At 1.2 s into the break, the tier drops the break time to 1.3 s.
                if (!changed && hunter.State == HunterState.BreakDoor && hunter.StateTime >= 1.2f) { tuning.breakDoorSeconds = 1.3f; changed = true; }
            }
            Check(changed && door.broken && blows.Count == 5 && blows.All(x => x.count == 5) && blows[blows.Count - 1].index == 4,
                "tiers: a break that started at 2.5 s keeps 5 blows when the break time drops mid-break (" + string.Join(" ", blows.Select(x => x.index + "/" + x.count)) + ")");
            // Once the leaf has fallen and it walks on, the next break takes the new time.
            for (var t = 0f; t < 2f && hunter.State == HunterState.BreakDoor; t += Dt)
            {
                hunter.Tick(Dt, target, target + Vector3.up * ModuleUnits.PlayerEye, Vector3.forward);
                world.TickDoorsForTools(Dt);
            }
            Check(hunter.State != HunterState.BreakDoor && hunter.BlowCount == 3, "tiers: after the break, BlowCount follows the new time (" + hunter.BlowCount + ")");
            // A real second break, on the same hunter behind another closed door, takes the new 1.3 s.
            if (FindDoor(world, out var a2, out var b2, out var c2))
            {
                var target2 = world.CellCenter(b2);
                var door2 = world.DoorBetween(a2, b2);
                player.position = target2;
                Physics.SyncTransforms();
                hunter.DebugPlace(world.CellCenter(c2));
                hunter.Noise(target2, 1000f);
                blows.Clear();
                float t2 = 0f, start2 = -1f, gave2 = -1f;
                world.DoorBroken += _ => { if (start2 >= 0f && gave2 < 0f) gave2 = t2 - start2; };
                for (; t2 < 30f && !door2.broken; t2 += Dt)
                {
                    hunter.Tick(Dt, target2, target2 + Vector3.up * ModuleUnits.PlayerEye, Vector3.forward);
                    world.TickDoorsForTools(Dt);
                    Physics.SyncTransforms();
                    if (hunter.State == HunterState.BreakDoor && start2 < 0f) start2 = t2 - hunter.StateTime;
                }
                Check(door2.broken && blows.Count == 3 && blows.All(x => x.count == 3) && blows.Select(x => x.index).SequenceEqual(new[] { 0, 1, 2 }) && Mathf.Abs(gave2 - 1.3f) <= Dt * .6f,
                    "tiers: the next break takes the new time (" + string.Join(" ", blows.Select(x => x.index + "/" + x.count)) + ", gives at " + gave2.ToString("0.000") + " s; expected 0/3 1/3 2/3 at 1.3 s)");
            }
            else Check(false, "tiers: no second closed door near the spawn for the next break");
        }
        else Check(false, "tiers: no closed door near the spawn");

        // Generation: chunks keep the tier they were generated at; a shift takes the tier of its time.
        var cache = new FrontRoomsMapCache(FrontRoomsLevelProfiles.Resolve().Generation(4242));
        var first = cache.Get(new GridCoord(0, 0));
        cache.Tier = 3;
        var again = cache.Get(new GridCoord(0, 0));
        var fresh = cache.Get(new GridCoord(5, 0));
        cache.Shift(new GridCoord(0, 0));
        var shifted = cache.Get(new GridCoord(0, 0));
        Check(first.tier == 1 && ReferenceEquals(first, again) && fresh.tier == 3 && shifted.tier == 3,
            "tiers: a generated chunk keeps tier 1 after the run reaches tier 3; a new chunk and a shifted one take 3");
        // Module tier: a module for tiers 2+ never comes at tier 1, and does at tier 3.
        var m = Room(3, 3, ZoneTheme.Level0);
        m.minTier = 1; m.maxTier = 9; m.weight = 1f; m.allowRotate = true;
        var settings = FrontRoomsLevelProfiles.Resolve().Generation(777);
        settings.moduleChance = 1f;
        // The base tier is under test, not the profile's value.
        settings.moduleTier = 0;
        var lib = new List<RoomModuleData> { m };
        int Placed(int tier) => PlacedWith(lib, tier);
        int PlacedWith(List<RoomModuleData> library, int tier)
        {
            var cc = new FrontRoomsMapCache(settings, library) { Tier = tier };
            var n = 0;
            for (var y = -6; y < 6; y++)
            for (var x = -6; x < 6; x++)
            {
                var d = cc.Get(new GridCoord(x, y));
                for (var r = 0; r < d.rooms.Length; r++) if (d.ModuleOf(r) != null) n++;
            }
            return n;
        }
        int at1 = Placed(1), at3 = Placed(3);
        Check(at1 == 0 && at3 > 0, "tiers: a module with tiers 1-9 is placed " + at1 + " times at run tier 1 and " + at3 + " at tier 3 (module tier = base + tier - 1)");
        // The upper bound: a module for tiers 0-1 comes at run tiers 1 and 2, never at 3.
        var early = Room(3, 3, ZoneTheme.Level0);
        early.minTier = 0; early.maxTier = 1; early.weight = 1f; early.allowRotate = true;
        var libEarly = new List<RoomModuleData> { early };
        int e1 = PlacedWith(libEarly, 1), e2 = PlacedWith(libEarly, 2), e3 = PlacedWith(libEarly, 3);
        Check(e1 > 0 && e2 > 0 && e3 == 0, "tiers: a module with tiers 0-1 is placed " + e1 + "/" + e2 + "/" + e3 + " times at run tiers 1/2/3");
    }

    // ---------- P4: markers ----------

    static void KeySpot(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        // A 6 x 6 room over chunk (0, 0)'s cells 1..6 holds its zone's key cell (always local 1..6).
        var m = Room(6, 6, ZoneTheme.Level0);
        var probe = ModuleWorld(roots, profiles, m, 1, 1, -35f, "MAP INTERACTION TEST / key probe");
        var data = probe.Cache.Get(new GridCoord(0, 0));
        if (!data.hasKey) { Check(false, "key spot: chunk (0, 0) has no key in this profile (tall zone?)"); return; }
        var site = data.keySiteCell;
        var cs = MapGrid.CellSize;
        // The marker in the key's own cell, off its centre, on the floor, turned 30°.
        var mx = (site.x - 1 + .5f) * cs + .6f;
        var mz = (site.y - 1 + .5f) * cs - .4f;
        m.markers = new[] { new ModuleMarker { kind = ModuleMarkerKind.KeySpot, x = mx, z = mz, y = 0f, yaw = 30f } };
        var world = ModuleWorld(roots, profiles, m, 1, 1, -36f, "MAP INTERACTION TEST / key spot");
        var d2 = world.Cache.Get(new GridCoord(0, 0));
        Check(d2.keySpot && d2.keyCell == site && Mathf.Abs(d2.keyX - (cs + mx)) < .001f && Mathf.Abs(d2.keyZ - (cs + mz)) < .001f,
            "key spot: the module's key spot takes the zone key (cell " + d2.keyCell + ", at " + d2.keyX.ToString("0.00") + ", " + d2.keyZ.ToString("0.00") + ")");
        var key = world.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name.StartsWith("Key · zone"));
        var expected = new Vector3(cs + mx, .06f, cs + mz);
        Check(key != null && (key.localPosition - expected).sqrMagnitude < 1e-4f && Mathf.Abs(Mathf.DeltaAngle(key.localEulerAngles.y, 30f)) < .5f,
            "key spot: the key lies at the marker, turned with it (" + (key != null ? key.localPosition.ToString("F2") : "none") + ")");
        // Without a key spot the key keeps its cell centre.
        var data0 = probe.Cache.Get(new GridCoord(0, 0));
        Check(!data0.keySpot && data0.keyCell == data0.keySiteCell, "key spot: without one the key stays at its site cell");
    }

    /// <summary>Walking distance in cells (open edges and doors, not glass) from a cell, up to maxDepth.</summary>
    static Dictionary<GridCoord, int> Walk(FrontRoomsMapWorld world, GridCoord start, int maxDepth)
    {
        var depth = new Dictionary<GridCoord, int> { [start] = 0 };
        var queue = new Queue<GridCoord>();
        queue.Enqueue(start);
        while (queue.Count > 0)
        {
            var cell = queue.Dequeue();
            if (depth[cell] >= maxDepth) continue;
            foreach (var s in Steps)
            {
                var n = cell + s;
                if (depth.ContainsKey(n) || !world.IsBuilt(n)) continue;
                var p = world.PassageBetween(cell, n);
                if (p == FrontRoomsMapWorld.Passage.Wall || p == FrontRoomsMapWorld.Passage.Glass) continue;
                depth[n] = depth[cell] + 1;
                queue.Enqueue(n);
            }
        }
        return depth;
    }

    static void RelayEntry(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        var m = Room(3, 3, ZoneTheme.Level0);
        m.markers = new[] { new ModuleMarker { kind = ModuleMarkerKind.RelayEntry, x = 4.5f, z = 4.5f, tag = "doorway" } };
        var world = ModuleWorld(roots, profiles, m, 3, 3, -37f, "MAP INTERACTION TEST / relay entry");
        var list = new List<(Vector3 pos, string tag)>();
        world.RelayEntries(list);
        Check(list.Count == 1 && list[0].tag == "doorway", "relay entry: the map lists the module's entry (" + list.Count + ")");
        if (list.Count != 1) return;
        var entry = list[0].pos;
        var entryCell = world.CellOf(entry);
        // A player 10-14 cells of walking away that cannot see the entry, facing away from it.
        var depth = Walk(world, entryCell, 14);
        var eye = Vector3.up * ModuleUnits.PlayerEye;
        GridCoord? spot = null;
        foreach (var pair in depth.OrderBy(x => x.Value))
        {
            if (pair.Value < 10) continue;
            var feet = world.CellCenter(pair.Key);
            if (!Physics.Linecast(feet + eye, entry + Vector3.up * 1.6f) || !Physics.Linecast(feet + eye, entry + Vector3.up * 1.95f)) continue;
            spot = pair.Key;
            break;
        }
        if (!spot.HasValue) { Check(false, "relay entry: no cell 10-14 cells from the entry that cannot see it"); return; }
        var player = new GameObject("test player").transform;
        player.SetParent(world.transform, false);
        var body = player.gameObject.AddComponent<CapsuleCollider>();
        body.height = ModuleUnits.PlayerHeight;
        body.radius = ModuleUnits.PlayerRadius;
        body.center = Vector3.up * (ModuleUnits.PlayerHeight * .5f);
        var p = world.CellCenter(spot.Value);
        player.position = p;
        Physics.SyncTransforms();
        var forward = (p - entry);
        forward.y = 0f;
        forward.Normalize();
        var tuning = new FrontRoomsHunterTuning { releaseDelaySeconds = 0f };
        var hunter = new FrontRoomsMapHunter(world, tuning, body, null, 9);
        var arrivals = new List<(Vector3 pos, string tag)>();
        hunter.Arrived += (pos, tag) => arrivals.Add((pos, tag));
        hunter.Tick(Dt, p, p + eye, forward);
        Check(hunter.Released && arrivals.Count == 1 && arrivals[0].tag == "doorway" && Flat(arrivals[0].pos - entry) < .01f && Flat(hunter.Position - entry) < .01f,
            "relay entry: released at the module's entry behind the player, Arrived with tag 'doorway' (" + (arrivals.Count > 0 ? arrivals[0].tag + " at " + arrivals[0].pos.ToString("F2") : "no arrival") + ")");
        // A relay to an unmarked cell raises Arrived with no tag: stand next to the entry so it is out of the band.
        var near = world.CellCenter(entryCell);
        player.position = near;
        Physics.SyncTransforms();
        var hunter2 = new FrontRoomsMapHunter(world, tuning, body, null, 9);
        var tags = new List<string>();
        hunter2.Arrived += (pos, tag) => tags.Add(tag);
        hunter2.Tick(Dt, near, near + eye, Vector3.forward);
        Check(hunter2.Released && tags.Count == 1 && tags[0] == null, "relay entry: an arrival in an unmarked cell has no tag");
    }

    static float Flat(Vector3 v) => new Vector2(v.x, v.z).magnitude;

    /// <summary>The Office fill keeps off a module's Relay entry (0.8 m) and its floor key (1 m): both are put where the kit stood without them.</summary>
    static void FillKeepsClear(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        var cs = MapGrid.CellSize;
        var m = Room(6, 6, ZoneTheme.Office);   // 6 x 6 at (1, 1) holds the key's site cell (local 1..6)
        m.fill = ModuleFill.Office;
        var probe = ModuleWorld(roots, profiles, m, 1, 1, -39f, "MAP INTERACTION TEST / fill clear probe");
        var data = probe.Cache.Get(new GridCoord(0, 0));
        var origin = probe.transform.TransformPoint(new Vector3(cs, 0f, cs));
        // Non-vacuous: put the entry where the kit put furniture when nothing was kept clear.
        var hit = probe.GetComponentsInChildren<Transform>(true).Where(t => t.name == "office dressing")
            .SelectMany(t => t.GetComponentsInChildren<Collider>(true)).Select(c => c.bounds)
            .Where(b => b.min.y <= ModuleUnits.RelayHeight)
            .Select(b => new Vector2(b.center.x - origin.x, b.center.z - origin.z))
            .FirstOrDefault(p => p.x > 1.5f && p.y > 1.5f && p.x < m.WidthMetres - 1.5f && p.y < m.DepthMetres - 1.5f);
        if (hit == default) { Check(false, "fill clear: the Office kit put nothing inside the probe room"); return; }
        var markers = new List<ModuleMarker> { new ModuleMarker { kind = ModuleMarkerKind.RelayEntry, x = hit.x, z = hit.y, tag = "vent", host = "" } };
        var site = data.keySiteCell;
        if (data.hasKey) markers.Add(new ModuleMarker { kind = ModuleMarkerKind.KeySpot, x = (site.x - 1 + .5f) * cs, z = (site.y - 1 + .5f) * cs, y = 0f, host = "" });
        m.markers = markers.ToArray();
        var world = ModuleWorld(roots, profiles, m, 1, 1, -40f, "MAP INTERACTION TEST / fill clear");
        var d = world.Cache.Get(new GridCoord(0, 0));
        var keep = new List<(Rect r, string what)> { (new Rect(cs + hit.x - .4f, cs + hit.y - .4f, .8f, .8f), "Relay entry") };
        if (d.hasKey && d.keySpot) keep.Add((new Rect(d.keyX - .5f, d.keyZ - .5f, 1f, 1f), "floor key"));
        var bad = new List<string>(); var n = 0;
        foreach (var root in world.GetComponentsInChildren<Transform>(true).Where(t => t.name == "office dressing"))
        foreach (var c in root.GetComponentsInChildren<Collider>(true))
        {
            var b = c.bounds; if (b.min.y > ModuleUnits.RelayHeight) continue;
            var lo = world.transform.InverseTransformPoint(b.min); var hi = world.transform.InverseTransformPoint(b.max);
            n++;
            foreach (var (r, what) in keep)
                if (lo.x < r.xMax - .02f && r.xMin + .02f < hi.x && lo.z < r.yMax - .02f && r.yMin + .02f < hi.z) bad.Add(what + ": " + c.name);
        }
        Check(n > 0 && bad.Count == 0, "fill clear: the Office fill keeps off the Relay entry (0.8 m) and the floor key (1 m) (" + string.Join(", ", bad.Take(6)) + ")");
        Check(!data.hasKey || (d.keySpot && keep.Count == 2), "fill clear: the key spot took the zone key");
        // Optional: reuse RelayEntry's release procedure (factored out as a helper) on `world` and assert Arrived with tag "vent" at the entry.
    }

    // ---------- P4: live tuning ----------

    static void Live(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        var m = Room(3, 3, ZoneTheme.Level0);
        var world = ModuleWorld(roots, profiles, m, 3, 3, -38f, "MAP INTERACTION TEST / live");
        var live = UnityEngine.Object.Instantiate(FrontRoomsLevelProfiles.Resolve());
        live.hideFlags = HideFlags.DontSave;
        profiles.Add(live);
        live.buildRadius = 3;
        var applied = 0;
        world.LiveApplied += () => applied++;
        var before = world.SightDistance;
        world.ApplyLive(live);
        Check(applied == 1 && world.BuildRadius == 3 && world.SightDistance > before, "live: ApplyLive takes the build radius (sight " + before + " → " + world.SightDistance + " m)");
        // ReplaceModule rebuilds chunk (0, 0) and leaves the others as they were.
        var others = world.GetComponentsInChildren<Transform>(true).Where(t => t.parent == world.transform && t.name.StartsWith("Chunk ") && !t.name.StartsWith("Chunk (0, 0)")).Select(t => t.gameObject).ToList();
        var oldChunk = world.GetComponentsInChildren<Transform>(true).First(t => t.parent == world.transform && t.name.StartsWith("Chunk (0, 0)")).gameObject;
        var m2 = Room(3, 3, ZoneTheme.Level0);
        m2.innerEast[0] = ModuleEdge.Wall;
        world.ReplaceModule(new GridCoord(0, 0), m2, 3, 3);
        var newChunk = world.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.parent == world.transform && t.name.StartsWith("Chunk (0, 0)") && t.gameObject.activeSelf);
        var data = world.Cache.Get(new GridCoord(0, 0));
        Check(newChunk != null && newChunk.gameObject != oldChunk && others.All(o => o != null) && data.east[MapGrid.LocalIndex(3, 3)] == EdgeKind.Wall,
            "live: ReplaceModule rebuilt chunk (0, 0) with the new module (inner wall in) and kept the " + others.Count + " other chunks");
        // The rebuilt chunk's Relay entries are registered again, and a removed one is gone.
        var m3 = Room(3, 3, ZoneTheme.Level0);
        m3.markers = new[] { new ModuleMarker { kind = ModuleMarkerKind.RelayEntry, x = 4.5f, z = 4.5f, tag = "t" } };
        world.ReplaceModule(new GridCoord(0, 0), m3, 3, 3);
        var list = new List<(Vector3 pos, string tag)>();
        world.RelayEntries(list);
        var withEntry = list.Count == 1 && list[0].tag == "t";
        world.ReplaceModule(new GridCoord(0, 0), Room(3, 3, ZoneTheme.Level0), 3, 3);
        world.RelayEntries(list);
        Check(withEntry && list.Count == 0, "live: a rebuilt chunk registers its module's Relay entry again, and drops it when the module no longer has one");
    }

    // ---------- The guard round Build ----------

    static void BuildGuard(List<GameObject> roots)
    {
        var world = World(roots, FrontRoomsLevelProfiles.Resolve(), -33f, "MAP INTERACTION TEST / build guard");
        // The chunk east of the spawn chunk throws.
        var spawnChunk = MapGrid.ChunkOf(new GridCoord(0, 0));
        var failing = default(GridCoord);
        var calls = 0;
        world.FailBuildForTools = c =>
        {
            if (c != failing) return false;
            calls++;
            return true;
        };
        // The spawn is in the middle of chunk (0, 0) unless overridden.
        failing = new GridCoord(spawnChunk.x + 1, spawnChunk.y);
        world.BuildForCapture();
        var origin = MapGrid.ChunkOrigin(failing);
        var cell = new GridCoord(origin.x + 3, origin.y + 3);
        var leftovers = world.GetComponentsInChildren<Transform>(true).Count(t => t.name.StartsWith("Chunk " + failing + " "));
        Check(calls == 1 && world.FailedChunkCount == 1, "build guard: the failing chunk " + failing + " was tried once and marked failed (calls " + calls + ", failed " + world.FailedChunkCount + ")");
        Check(leftovers == 0 && !world.IsBuilt(cell), "build guard: nothing of it is left in the scene or registered (leftovers " + leftovers + ")");
        Check(world.BuiltChunkCount > 0 && world.IsBuilt(world.CellOf(world.SpawnWorldPosition)), "build guard: the rest of the map is built (" + world.BuiltChunkCount + " chunks)");
        var stream = typeof(FrontRoomsMapWorld).GetMethod("Stream", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var center = MapGrid.ChunkOf(world.CellOf(world.SpawnWorldPosition));
        stream.Invoke(world, new object[] { center, int.MaxValue });
        stream.Invoke(world, new object[] { center, int.MaxValue });
        Check(calls == 1, "build guard: streaming again does not retry it while it is in range (calls " + calls + ")");
        Check(world.Settled && world.ReadyAround(1), "build guard: Settled and ReadyAround count the failed chunk as done");
        // Out of range and back: one more try.
        var far = new GridCoord(center.x + 10, center.y);
        stream.Invoke(world, new object[] { far, int.MaxValue });
        stream.Invoke(world, new object[] { center, int.MaxValue });
        Check(calls == 2 && world.FailedChunkCount == 1, "build guard: after leaving range it is tried once more (calls " + calls + ")");
    }

    // ---------- Module builds ----------

    /// <summary>A floor kit at least 1.2 m long (a desk) and a small kit to stand on it.</summary>
    static bool DeskKits(out string desk, out string item)
    {
        desk = item = null;
        foreach (var name in FrontRoomsKitLibrary.AllNames())
        {
            var info = FrontRoomsKitLibrary.GetInfo(name);
            var f = FrontRoomsMapWorld.KitFootprint(name);
            if (info == null || f == null) continue;
            float w = f[2] - f[0], d = f[3] - f[1];
            if (desk == null && info.placement == "Floor" && w >= 1.2f && w <= 2f && d <= 1f && f[4] < 1.2f) desk = name;
            if (item == null && info.placement == "DeskTop" && w <= .5f && d <= .5f) item = name;
        }
        return desk != null && item != null;
    }

    static string FloorKit()
    {
        foreach (var name in FrontRoomsKitLibrary.AllNames())
        {
            var info = FrontRoomsKitLibrary.GetInfo(name);
            var f = FrontRoomsMapWorld.KitFootprint(name);
            if (info == null || f == null || info.placement != "Floor") continue;
            if (f[2] - f[0] > .3f && f[2] - f[0] < 1.4f && f[3] - f[1] > .3f && f[3] - f[1] < 1.4f && f[4] < 1.6f) return name;
        }
        return null;
    }

    /// <summary>A world whose zones all take the module's height and theme, with the module in chunk (0, 0) at (x0, y0), as the Level Designer preview builds it.</summary>
    static FrontRoomsMapWorld ModuleWorld(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles, RoomModuleData m, int x0, int y0, float period, string name)
    {
        var profile = UnityEngine.Object.Instantiate(FrontRoomsLevelProfiles.Resolve());
        profile.hideFlags = HideFlags.DontSave;
        profiles.Add(profile);
        var g = profile.Generation(3);
        g.lowShare = m.height == ZoneHeight.Low ? 1f : 0f;
        g.standardShare = m.height == ZoneHeight.Standard ? 1f : 0f;
        g.tallShare = m.height == ZoneHeight.Tall ? 1f : 0f;
        g.officeShare = m.theme == ZoneTheme.Office ? 1f : 0f;
        g.moduleChance = 0f;
        profile.generation = g;
        profile.buildRadius = 1;
        var world = World(roots, profile, period, name);
        world.TagModuleProps = true;
        world.PlaceModule(m, new GridCoord(0, 0), x0, y0);
        world.BuildForCapture();
        return world;
    }

    static RoomModuleData Room(int w, int d, ZoneTheme theme)
    {
        var m = new RoomModuleData { width = w, depth = d, height = ZoneHeight.Standard, theme = theme, columns = ModuleColumns.None, fill = ModuleFill.None };
        m.Normalize();
        for (var i = 0; i < m.south.Length; i++) m.south[i] = ModuleEdge.Arch;
        for (var i = 0; i < m.north.Length; i++) m.north[i] = ModuleEdge.Arch;
        return m;
    }

    static void Columns(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        var kit = FloorKit();
        if (kit == null) { Check(false, "columns: no floor kit with a known footprint in the kit library"); return; }
        var m = Room(4, 4, ZoneTheme.Level0);
        m.columns = ModuleColumns.Custom;
        m.customColumns = new[] { new ModuleColumn { x = 2, y = 2, large = true } };
        // Prop 0 on the column (corner (2, 2) = 6 m, 6 m); prop 1 well clear of it and the strips.
        var props = new List<ModuleProp> { new ModuleProp { kit = kit, x = 6f, z = 6f }, new ModuleProp { kit = kit, x = 3f, z = 6f } };
        // A desk reaching into the column (2), an item on that desk clear of the column (3), and an item on the kept prop (4).
        var desks = DeskKits(out var desk, out var item);
        if (desks)
        {
            var df = FrontRoomsMapWorld.KitFootprint(desk);
            var half = (df[2] - df[0]) * .5f;
            props.Add(new ModuleProp { kit = desk, x = 6f + half - .1f, z = 6f });
            props.Add(new ModuleProp { kit = item, x = 6f + 2f * half - .35f, z = 6f, y = .74f, noCollider = true });
            props.Add(new ModuleProp { kit = item, x = 3f, z = 6f, y = .74f, noCollider = true });
        }
        m.props = props.ToArray();
        var errors = new List<string>();
        var warnings = new List<string>();
        m.Validate(errors, warnings, FrontRoomsMapWorld.KitFootprint);
        Check(warnings.Any(w => w.StartsWith("Prop 1") && w.Contains("a column stands")) && !warnings.Any(w => w.StartsWith("Prop 2") && w.Contains("column")),
            "columns: Validate warns about the prop on the column only (" + string.Join(" | ", warnings) + ")");
        var world = ModuleWorld(roots, profiles, m, 2, 2, -31f, "MAP INTERACTION TEST / columns");
        var built = world.GetComponentsInChildren<FrontRoomsModulePropTag>(true).Select(x => x.index).OrderBy(x => x).ToArray();
        Check(built.Contains(1) && !built.Contains(0), "columns: the prop on the column is left out of the build, the other stands (built " + string.Join(", ", built) + ", kit " + kit + ")");
        if (desks)
            Check(!built.Contains(2) && !built.Contains(3) && built.Contains(4),
                "columns: the desk reaching into the column goes, and the item on it with it; the item on the kept prop stays (built " + string.Join(", ", built) + ", " + desk + " / " + item + ")");
        else Check(false, "columns: no desk and desk-top kit pair in the kit library");
    }

    static void InnerWalls(List<GameObject> roots, List<FrontRoomsLevelProfile> profiles)
    {
        // A 6 x 5 Office room with an inner wall line at x = 3 cells: wall on rows 0-1 and 3-4, an arch on row 2.
        var m = Room(6, 5, ZoneTheme.Office);
        m.fill = ModuleFill.Office;
        for (var j = 0; j < m.depth; j++) m.innerEast[2 + j * (m.width - 1)] = j == 2 ? ModuleEdge.Arch : ModuleEdge.Wall;
        var errors = new List<string>();
        var warnings = new List<string>();
        m.Validate(errors, warnings, FrontRoomsMapWorld.KitFootprint);
        Check(warnings.Any(w => w.Contains("furnishes the room as one open space")), "inner walls: Validate warns about Office fill with inner walls");
        var world = ModuleWorld(roots, profiles, m, 1, 1, -32f, "MAP INTERACTION TEST / inner walls");
        var dressing = world.GetComponentsInChildren<Transform>(true).Where(x => x.name == "office dressing").ToArray();
        if (dressing.Length == 0) { Check(false, "inner walls: the Office kit did not dress the module (is FrontRoomsOfficeKit in the project?)"); return; }
        // The room's inner strips in world space.
        var cs = MapGrid.CellSize;
        var origin = world.transform.TransformPoint(new Vector3(1 * cs, 0f, 1 * cs));
        var strips = m.InnerStrips();
        var inWall = new List<string>();
        var inDoorway = new List<string>();
        var colliders = 0;
        foreach (var root in dressing)
        foreach (var c in root.GetComponentsInChildren<Collider>(true))
        {
            // Only the dressing in this module's room.
            var b = c.bounds;
            var lx0 = b.min.x - origin.x; var lz0 = b.min.z - origin.z; var lx1 = b.max.x - origin.x; var lz1 = b.max.z - origin.z;
            if (lx1 < 0f || lz1 < 0f || lx0 > m.WidthMetres || lz0 > m.DepthMetres) continue;
            colliders++;
            if (b.min.y > ModuleUnits.RelayHeight) continue;
            foreach (var s in strips)
            {
                // A 2 cm tolerance for touching faces.
                if (!(lx0 < s[2] - .02f && s[0] + .02f < lx1 && lz0 < s[3] - .02f && s[1] + .02f < lz1)) continue;
                (s[4] > 0f ? inWall : inDoorway).Add(c.name + " < " + c.transform.parent?.name);
            }
        }
        Check(colliders > 0, "inner walls: the Office kit placed " + colliders + " colliders in the module");
        Check(inWall.Count == 0, "inner walls: nothing stands in an inner wall (" + string.Join(", ", inWall.Take(6)) + ")");
        Check(inDoorway.Count == 0, "inner walls: the inner doorway's clear floor stays clear (" + string.Join(", ", inDoorway.Take(6)) + ")");
    }
}
