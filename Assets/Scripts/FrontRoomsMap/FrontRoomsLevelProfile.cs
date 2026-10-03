using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// One level's tunable numbers as an asset (Assets/Levels/FrontRoomsLevel0.asset):
/// how the maze is generated, how it streams, and what it costs. The main
/// game, the map test scene, the debug window and the 100-seed check all read
/// the same asset, so a change here is what the next run plays.
/// The geometry it is built from is fixed by <see cref="ModuleUnits"/>.
/// Edits made during Play are kept (it is an asset) and take effect on the
/// next run; the running map works on a copy.
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
        var list = new System.Collections.Generic.List<(string, RoomModuleData)>();
        if (modules != null)
            foreach (var m in modules)
                if (m != null && m.data != null) list.Add((m.name, m.data.Clone()));
        list.Sort((a, b) => string.CompareOrdinal(a.Item1, b.Item1));
        var result = new System.Collections.Generic.List<RoomModuleData>();
        foreach (var (_, d) in list) result.Add(d);
        return result;
    }

    void OnValidate()
    {
        if (generation == null) generation = new MapSettings();
        shadowRadius = Mathf.Min(shadowRadius, lightRadius);
    }
}
