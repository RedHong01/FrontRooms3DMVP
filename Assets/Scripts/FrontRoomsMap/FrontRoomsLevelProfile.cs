using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// One level's tunable numbers as an asset (Assets/Levels/FrontRoomsLevel0.asset):
/// how the maze is generated, how it streams, and what it costs. The main
/// game, the map test scene, the debug window and the 100-seed check all read
/// the same asset, so a change here is what the next run plays.
/// The geometry it is built from is fixed by <see cref="ModuleUnits"/>.
/// Edits made during Play are kept (it is an asset). The running map takes the
/// light, shadow, streaming, shift, key and dressing numbers at once
/// (FrontRoomsMapWorld.ApplyLive) and the tier table on the next frame; the
/// generation numbers and the module list take effect on the next run.
/// </summary>
[CreateAssetMenu(menuName = "FrontRooms/Level profile", fileName = "FrontRoomsLevel")]
public sealed class FrontRoomsLevelProfile : ScriptableObject
{
    public const string DefaultPath = "Assets/Levels/FrontRoomsLevel0.asset";

    [Tooltip("Generation numbers: zone heights, maze, rooms, exits, Office share. Its seed is used by the test scene, the debug window and the 100-seed check; the game uses Run Seed.")]
    public MapSettings generation = new MapSettings();

    [Header("Run")]
    [Tooltip("0 picks a new maze every run. Any other value replays that maze.")]
    public int runSeed = 0;
    [Range(1, 3), Tooltip("Chunks kept built around the player in each direction. 2 = 5 x 5 chunks, 120 m across. Also sets the camera's far plane (radius x 24 m - 2 m).")]
    public int buildRadius = 2;
    [Range(1, 4), Tooltip("New chunks built per frame while streaming. The first build around the spawn is always complete.")]
    public int chunksPerFrame = 1;
    [Min(5f), Tooltip("A chunk the player has been away from for at least this long comes back with a shifted interior.")]
    public float shiftAfterSeconds = 30f;
    [Tooltip("Off: doors open without the zone key. Keys are still collected and shown.")]
    public bool doorsNeedKeys = false;

    [Header("Light budget")]
    [Min(4f), Tooltip("Fixture lights beyond this distance are switched off (they fade over the last 3 m).")]
    public float lightRadius = 16f;
    [Min(0f), Tooltip("Only lamps this close cast shadows (one lamp in three).")]
    public float shadowRadius = 9f;

    [Header("Room modules")]
    [Tooltip("Designer rooms (Assets/Levels/Modules) the generator may place into carved rooms they fit. The chance and tier are in Generation (Module Chance, Module Tier).")]
    public FrontRoomsRoomModule[] modules = new FrontRoomsRoomModule[0];

    [Header("Difficulty tiers (DP08 proposal)")]
    [Tooltip("The run's tier rises every Zones Per Tier new zones, or after Stall Seconds without one. Each row scales the Relay's tuning (on the FrontRooms 3D object) and sets the lamp odds and module tier of chunks generated at that tier. Edits apply at once, also during Play.")]
    public FrontRoomsTierRules tiers = new FrontRoomsTierRules();

    [Header("Dressing")]
    [Tooltip("Furnish Office-zone rooms with FrontRoomsOfficeKit when it exists.")]
    public bool dressOffices = true;
    [Range(0f, 1f), Tooltip("Chance that a hall of at least 4 x 4 cells gets a FrontRoomsFurniturePile (at least 0.6 in tall zones).")]
    public float pileChance = .35f;

    static FrontRoomsLevelProfile fallback;

    /// <summary>The code defaults, for when no asset is assigned. Never saved.</summary>
    public static FrontRoomsLevelProfile Default
    {
        get
        {
            if (fallback == null)
            {
                fallback = CreateInstance<FrontRoomsLevelProfile>();
                fallback.name = "FrontRoomsLevel (defaults)";
                fallback.hideFlags = HideFlags.DontSave;
            }
            return fallback;
        }
    }

    /// <summary>A copy of the generation numbers with the given seed; the asset itself is never changed.</summary>
    public MapSettings Generation(int seed)
    {
        var copy = (generation ?? new MapSettings()).Clone();
        copy.seed = seed;
        return copy;
    }

    /// <summary>The modules' data, in a stable order (by asset name), for the generator. Never the assets' own data objects.</summary>
    public System.Collections.Generic.List<RoomModuleData> ModuleData()
    {
        // Each asset once (a duplicate would double its weight); ties in name keep the list's order.
        var seen = new System.Collections.Generic.HashSet<FrontRoomsRoomModule>();
        var list = new System.Collections.Generic.List<(string, RoomModuleData)>();
        if (modules != null)
            foreach (var m in modules)
                if (m != null && m.data != null && seen.Add(m)) list.Add((m.name, m.data.Clone()));
        var order = new System.Collections.Generic.List<(string, RoomModuleData)>(list);
        list.Sort((a, b) => { var c = string.CompareOrdinal(a.Item1, b.Item1); return c != 0 ? c : order.IndexOf(a).CompareTo(order.IndexOf(b)); });
        var result = new System.Collections.Generic.List<RoomModuleData>();
        foreach (var (_, d) in list) result.Add(d);
        return result;
    }

    /// <summary>Raised when the asset is edited (also during Play): a running map applies the numbers it can take live (FrontRoomsMapWorld.ApplyLive).</summary>
    public static event System.Action<FrontRoomsLevelProfile> Changed;

    void OnValidate()
    {
        if (generation == null) generation = new MapSettings();
        shadowRadius = Mathf.Min(shadowRadius, lightRadius);
        if (tiers == null) tiers = new FrontRoomsTierRules();
        tiers.Normalize();
        Changed?.Invoke(this);
    }
}

/// <summary>One difficulty tier: multipliers on the Relay's base tuning, and the Auto lamp odds of chunks generated at this tier.</summary>
[System.Serializable]
public sealed class FrontRoomsTier
{
    [Min(.1f), Tooltip("Chase speed, times the base (4.2 m/s).")]
    public float chaseSpeed = 1f;
    [Min(.1f), Tooltip("Hearing, times the base (1.4).")]
    public float hearing = 1f;
    [Min(.05f), Tooltip("Door break time, times the base (2.5 s). Blows land every 0.5 s, so 2.5 s is 5 blows, 1.3 s is 3.")]
    public float breakDoor = 1f;
    [Min(.1f), Tooltip("Search: the listening pause at each spot and the give-up time, times the base.")]
    public float search = 1f;
    [Header("Auto lamps (the rest are dim)")]
    [Range(0f, 1f)] public float lampSteady = .62f;
    [Range(0f, 1f)] public float lampStutter = .20f;
    [Range(0f, 1f)] public float lampFailing = .10f;
    [Range(0f, 1f)] public float lampDead = .05f;

    public FrontRoomsTier() { }

    public FrontRoomsTier(float chase, float hear, float breakDoor, float search, float steady, float stutter, float failing, float dead)
    {
        chaseSpeed = chase; hearing = hear; this.breakDoor = breakDoor; this.search = search;
        lampSteady = steady; lampStutter = stutter; lampFailing = failing; lampDead = dead;
    }

    /// <summary>Scale a copy of the base tuning (never the base itself).</summary>
    public void ApplyTo(FrontRoomsHunterTuning t)
    {
        t.chaseSpeed *= chaseSpeed;
        t.hearing *= hearing;
        t.breakDoorSeconds *= breakDoor;
        t.searchLookSeconds *= search;
        t.searchMaxSeconds *= search;
    }

    /// <summary>An Auto lamp's mode from a roll in [0, 1): 0 steady, 1 stutter, 2 failing, 3 dead, 4 dim (FrontRoomsMapWorld fixtures).</summary>
    public int LampMode(float roll)
    {
        float a = lampSteady, b = a + lampStutter, c = b + lampFailing, d = c + lampDead;
        return roll < a ? 0 : roll < b ? 1 : roll < c ? 2 : roll < d ? 3 : 4;
    }
}

/// <summary>When the run's tier rises, and what each tier does (DP08: 5 tiers, every 4 zones or 2 minutes).</summary>
[System.Serializable]
public sealed class FrontRoomsTierRules
{
    [Min(1), Tooltip("New zones per tier: zones 1-4 are tier 1, 5-8 tier 2, and so on.")]
    public int zonesPerTier = 4;
    [Min(10f), Tooltip("Seconds without a new zone (out of the start rooms) before the tier rises anyway.")]
    public float stallSeconds = 120f;
    [Tooltip("Tier 1 first. Tier 1 is today's game: the base tuning and lamp odds.")]
    public FrontRoomsTier[] tiers = Defaults();

    public static FrontRoomsTier[] Defaults() => new[]
    {
        new FrontRoomsTier(1f, 1f, 1f, 1f, .62f, .20f, .10f, .05f),
        new FrontRoomsTier(1.07f, 1.15f, .88f, 1.15f, .57f, .21f, .12f, .06f),
        new FrontRoomsTier(1.14f, 1.3f, .76f, 1.3f, .52f, .22f, .14f, .08f),
        new FrontRoomsTier(1.21f, 1.45f, .64f, 1.45f, .46f, .24f, .16f, .10f),
        new FrontRoomsTier(1.29f, 1.6f, .52f, 1.6f, .40f, .25f, .18f, .12f),
    };

    public int MaxTier => tiers == null || tiers.Length == 0 ? 1 : tiers.Length;

    /// <summary>Tier n (1-based), clamped to the table.</summary>
    public FrontRoomsTier At(int tier)
    {
        Normalize();
        return tiers[Mathf.Clamp(tier, 1, tiers.Length) - 1];
    }

    /// <summary>The tier the zone count alone gives (1 for the first Zones Per Tier zones).</summary>
    public int TierForZones(int zones) => Mathf.Clamp(1 + Mathf.Max(0, zones - 1) / Mathf.Max(1, zonesPerTier), 1, MaxTier);

    public void Normalize()
    {
        if (tiers == null || tiers.Length == 0) tiers = Defaults();
        for (var i = 0; i < tiers.Length; i++) if (tiers[i] == null) tiers[i] = new FrontRoomsTier();
        zonesPerTier = Mathf.Max(1, zonesPerTier);
        stallSeconds = Mathf.Max(10f, stallSeconds);
    }
}
