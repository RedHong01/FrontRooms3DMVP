using System;
using System.Collections.Generic;
using System.Reflection;
using FrontRooms.Map;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Builds the generated Level 0 map as geometry around the player. The main
/// game creates it embedded (CreateEmbedded, then Begin) after the title's
/// noclip; FrontRoomsMapTest.unity runs it standalone with its own walker.
/// It keeps the chunks within buildRadius built (one new chunk per frame,
/// nearest first) and drops the rest; a chunk the player comes back to after
/// shiftAfterSeconds is rebuilt with a shifted interior. Every fixture runs its
/// own flicker. Office rooms and large halls are furnished through
/// FrontRoomsOfficeKit and FrontRoomsFurniturePile when those exist.
/// </summary>
public sealed class FrontRoomsMapWorld : MonoBehaviour
{
    // Sizes come from the modular unit spec (FrontRoomsModuleUnits.cs).
    const float WallThickness = ModuleUnits.WallThickness;
    const int BlockCells = 2;
    const float DoorWidth = ModuleUnits.DoorWidth, DoorHeight = ModuleUnits.DoorHeight;
    const float WindowWidth = ModuleUnits.WindowWidth, WindowSill = ModuleUnits.WindowSill, WindowTop = ModuleUnits.WindowTop;
    // Mesh-UV repeats. Only the fallback materials read them: the surface
    // materials are world-projected and use their own tile sizes.
    const float WallpaperRepeat = 1.2f, CarpetRepeat = 1.5f, CeilingRepeat = 1.2f;

    [SerializeField, Tooltip("The level's numbers (Assets/Levels). Empty: the code defaults.")] FrontRoomsLevelProfile profile;
    [SerializeField, Tooltip("Pick a new seed every time Play starts (standalone test scene only).")] bool randomSeedOnPlay = false;
    [SerializeField, Tooltip("On: the test scene, which spawns its own walker and sets fog. The main game creates the map embedded instead.")] bool standalone = true;

    // Working copies of the profile, taken when the map starts, so the asset
    // is never changed by a run.
    MapSettings settings;
    int buildRadius, chunksPerFrame;
    float shiftAfterSeconds, lightRadius, shadowRadius, pileChance;
    bool doorsNeedKeys, dressOffices;

    public FrontRoomsMapCache Cache { get; private set; }
    public Transform Player => player;
    public int ShiftedChunks { get; private set; }
    public int KeysHeld => keysHeld.Count;
    /// <summary>The assigned profile, or the code defaults.</summary>
    public FrontRoomsLevelProfile Profile
    {
        get => profile != null ? profile : FrontRoomsLevelProfile.Default;
        set => profile = value;
    }
    public int Seed => settings != null ? settings.seed : Profile.generation.seed;
    public int BuiltChunkCount => built.Count;
    public int BuildRadius => settings != null ? buildRadius : Mathf.Max(1, Profile.buildRadius);
    public Color FogColor => FrontRoomsLook.FogColor;
    /// <summary>Camera far plane: just short of the first chunk that may not be built yet.</summary>
    public float SightDistance => BuildRadius * MapGrid.ChunkSize - 2f;

    /// <summary>A door moved (opened or shut by the player): a noise at the door.</summary>
    public event Action<Vector3> DoorMoved;
    /// <summary>The player broke a window: the loudest noise in the game.</summary>
    public event Action<Vector3> GlassBroken;
    /// <summary>The Relay broke a door down.</summary>
    public event Action<Vector3> DoorBroken;
    /// <summary>The player picked up a zone key.</summary>
    public event Action<GridCoord> KeyTaken;

    /// <summary>What lies between two side-by-side cells right now.</summary>
    public enum Passage { Open, Wall, ClosedDoor, Glass }

    sealed class Fixture
    {
        public Light light;
        public Renderer panel;
        public Color emission;
        public float baseIntensity;
        public bool castsShadow;
        public int mode;
        public uint rng;
        public float clock;
        public float nextEvent;
        public float eventEnd;
        public float phase;
        public float level = 1f;
    }

    public sealed class Door
    {
        public Transform hinge;
        public Quaternion closed;
        public Collider leaf;
        public GridCoord a, b;
        public long edge;
        public Vector3 position;
        public bool open;
        public bool broken;
        public float progress;
        /// <summary>+1 or -1: which side the leaf swings to. Doors swing away from whoever opens or breaks them.</summary>
        public float swing = 1f;
    }

    public sealed class Window
    {
        public GameObject pane;
        public long edge;
        public Vector3 position;
        public float hold;
    }

    sealed class BuiltChunk
    {
        public GameObject root;
        public readonly List<Fixture> fixtures = new List<Fixture>();
        public readonly List<Door> doors = new List<Door>();
        public readonly List<Window> windows = new List<Window>();
        public readonly List<(GameObject go, GridCoord zone)> keys = new List<(GameObject, GridCoord)>();
    }

    sealed class MeshBuilder
    {
        public readonly List<Vector3> vertices = new List<Vector3>();
        public readonly List<Vector3> normals = new List<Vector3>();
        public readonly List<Vector2> uvs = new List<Vector2>();
        public readonly List<int> triangles = new List<int>();

        public void Box(Vector3 center, Vector3 size, Vector3 worldOffset, float repeat)
        {
            var h = size * .5f;
            Face(center + Vector3.right * h.x, Vector3.right, Vector3.up, Vector3.forward, h.y, h.z, worldOffset, repeat);
            Face(center - Vector3.right * h.x, Vector3.left, Vector3.forward, Vector3.up, h.z, h.y, worldOffset, repeat);
            Face(center + Vector3.up * h.y, Vector3.up, Vector3.forward, Vector3.right, h.z, h.x, worldOffset, repeat);
            Face(center - Vector3.up * h.y, Vector3.down, Vector3.right, Vector3.forward, h.x, h.z, worldOffset, repeat);
            Face(center + Vector3.forward * h.z, Vector3.forward, Vector3.right, Vector3.up, h.x, h.y, worldOffset, repeat);
            Face(center - Vector3.forward * h.z, Vector3.back, Vector3.up, Vector3.right, h.y, h.x, worldOffset, repeat);
        }

        // u x v points along the normal, so (0,1,2)(0,2,3) winds clockwise as seen from the front.
        void Face(Vector3 c, Vector3 normal, Vector3 u, Vector3 v, float uHalf, float vHalf, Vector3 worldOffset, float repeat)
        {
            var i = vertices.Count;
            Corner(c - u * uHalf - v * vHalf, normal, worldOffset, repeat);
            Corner(c + u * uHalf - v * vHalf, normal, worldOffset, repeat);
            Corner(c + u * uHalf + v * vHalf, normal, worldOffset, repeat);
            Corner(c - u * uHalf + v * vHalf, normal, worldOffset, repeat);
            triangles.Add(i); triangles.Add(i + 1); triangles.Add(i + 2);
            triangles.Add(i); triangles.Add(i + 2); triangles.Add(i + 3);
        }

        void Corner(Vector3 p, Vector3 normal, Vector3 worldOffset, float repeat)
        {
            vertices.Add(p);
            normals.Add(normal);
            var w = p + worldOffset;
            // World-space planar UVs: the print keeps one scale on every wall
            // and continues across chunk borders.
            var uv = Mathf.Abs(normal.x) > .5f ? new Vector2(w.z, w.y) : Mathf.Abs(normal.y) > .5f ? new Vector2(w.x, w.z) : new Vector2(w.x, w.y);
            uvs.Add(uv / repeat);
        }

        public Mesh ToMesh(string name)
        {
            var mesh = new Mesh { name = name };
            if (vertices.Count > 65000) mesh.indexFormat = IndexFormat.UInt32;
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateTangents();
            mesh.RecalculateBounds();
            return mesh;
        }
    }

    sealed class ThemeMaterials
    {
        public Material wall, floor, ceiling, lens;
        public float lampIntensity;
    }

    readonly Dictionary<GridCoord, BuiltChunk> built = new Dictionary<GridCoord, BuiltChunk>();
    readonly Dictionary<GridCoord, float> droppedAt = new Dictionary<GridCoord, float>();
    readonly HashSet<GridCoord> keysHeld = new HashSet<GridCoord>();
    readonly HashSet<long> brokenWindows = new HashSet<long>();
    readonly HashSet<long> openDoors = new HashSet<long>();
    readonly HashSet<long> brokenDoors = new HashSet<long>();
    // Which way each opened or broken door swung (+1 or -1), kept across rebuilds.
    readonly Dictionary<long, float> doorSwing = new Dictionary<long, float>();
    readonly Dictionary<Collider, Door> doorByCollider = new Dictionary<Collider, Door>();
    readonly Dictionary<long, Door> doorByEdge = new Dictionary<long, Door>();
    readonly Dictionary<Collider, Window> windowByCollider = new Dictionary<Collider, Window>();
    readonly HashSet<Collider> shellColliders = new HashSet<Collider>();
    // Modules placed by hand (the Level Designer preview), stamped whenever their chunk is generated.
    readonly List<(RoomModuleData module, GridCoord chunk, int x, int y)> placedModules = new List<(RoomModuleData, GridCoord, int, int)>();
    Vector3? spawnOverride;
    readonly List<GridCoord> scratch = new List<GridCoord>();
    readonly List<Door> movingDoors = new List<Door>();
    Transform player;
    MaterialPropertyBlock block;
    ThemeMaterials level0, office;
    Material trim, doorLeaf, glass, keyGlow;
    bool begun;

    static bool dressersResolved;
    static MethodInfo officeDress, officeDressOld, pileBuild;

    /// <summary>A room waiting to be furnished. Rooms are dressed one per frame after their chunk is built.</summary>
    struct DressJob
    {
        public BuiltChunk chunk;
        public MapChunk data;
        public int room;
    }
    readonly Queue<DressJob> dressQueue = new Queue<DressJob>();

    void Awake()
    {
        if (settings == null)
        {
            var seed = Profile.generation.seed;
            if (randomSeedOnPlay && standalone) seed = UnityEngine.Random.Range(int.MinValue, int.MaxValue);
            TakeProfile(Profile, seed);
        }
        CreateCache();
        block = new MaterialPropertyBlock();
        BuildMaterials();
        if (!standalone || !Application.isPlaying) return;
        ApplyRenderSettings();
        Begin(FrontRoomsMapWalker.Spawn(this, SpawnWorldPosition).transform);
    }

    /// <summary>
    /// Create the map inside the main game: no walker and no change to the
    /// scene's render settings. Place the player at SpawnWorldPosition, then
    /// call Begin.
    /// </summary>
    public static FrontRoomsMapWorld CreateEmbedded(Transform parent, FrontRoomsLevelProfile profile, int seed)
    {
        var go = new GameObject("Level 0 map");
        go.SetActive(false);
        go.transform.SetParent(parent, false);
        var world = go.AddComponent<FrontRoomsMapWorld>();
        world.profile = profile;
        world.standalone = false;
        world.TakeProfile(world.Profile, seed);
        // Awake runs here, with the fields above already set.
        go.SetActive(true);
        return world;
    }

    /// <summary>Copy the profile's numbers into this map, with the given seed.</summary>
    void TakeProfile(FrontRoomsLevelProfile source, int seed)
    {
        settings = source.Generation(seed);
        buildRadius = Mathf.Max(1, source.buildRadius);
        chunksPerFrame = Mathf.Max(1, source.chunksPerFrame);
        shiftAfterSeconds = source.shiftAfterSeconds;
        lightRadius = source.lightRadius;
        shadowRadius = source.shadowRadius;
        doorsNeedKeys = source.doorsNeedKeys;
        dressOffices = source.dressOffices;
        pileChance = source.pileChance;
    }

    /// <summary>Build everything around the player at once, then stream from Update.</summary>
    public void Begin(Transform playerTransform)
    {
        player = playerTransform;
        begun = true;
        Stream(ChunkOf(player.position), int.MaxValue);
        // The first build is hidden (the noclip white-out, or an edit-mode capture): furnish it all now.
        while (DressNext()) { }
        TickFixtures(0f);
    }

    /// <summary>
    /// Edit-mode build of the chunks around the spawn, used for captures.
    /// Returns the eye position. The caller restores render settings.
    /// </summary>
    public Vector3 BuildForCapture()
    {
        TakeProfile(Profile, Profile.generation.seed);
        CreateCache();
        block = new MaterialPropertyBlock();
        BuildMaterials();
        ApplyRenderSettings();
        var eye = new GameObject("CAPTURE / eye").transform;
        eye.SetParent(transform, false);
        eye.localPosition = SpawnPoint();
        Begin(eye);
        return transform.TransformPoint(SpawnPoint() + Vector3.up * ModuleUnits.PlayerEye);
    }

    void CreateCache()
    {
        Cache = new FrontRoomsMapCache(settings);
        foreach (var p in placedModules) Cache.Place(p.chunk, p.module, p.x, p.y);
    }

    /// <summary>
    /// Stamp a room module into chunk <paramref name="chunk"/> with its
    /// south-west cell at chunk-local (x, y), whenever that chunk is built.
    /// Call before the map starts (Awake, BuildForCapture). See RoomModuleStamp.
    /// </summary>
    public void PlaceModule(RoomModuleData module, GridCoord chunk, int x, int y)
    {
        placedModules.Add((module, chunk, x, y));
        Cache?.Place(chunk, module, x, y);
    }

    /// <summary>Start the walker or capture eye here (map space) instead of the middle of chunk (0, 0).</summary>
    public void OverrideSpawn(Vector3 mapPosition) => spawnOverride = mapPosition;

    static void Kill(UnityEngine.Object target)
    {
        if (target == null) return;
        if (Application.isPlaying) Destroy(target); else DestroyImmediate(target);
    }

    /// <summary>
    /// The test scene shares the game's ambient bounce and haze
    /// (FrontRoomsLook), so the maze looks the same there as in the game.
    /// </summary>
    void ApplyRenderSettings()
    {
        FrontRoomsLook.ApplyAmbient();
        RenderSettings.skybox = null;
    }

    Vector3 SpawnPoint()
    {
        if (spawnOverride.HasValue) return spawnOverride.Value;
        var mid = MapGrid.ChunkCells / 2;
        return new Vector3((mid + .5f) * MapGrid.CellSize, .05f, (mid + .5f) * MapGrid.CellSize);
    }

    /// <summary>Where the player starts: the middle of chunk (0, 0), in world space.</summary>
    public Vector3 SpawnWorldPosition => transform.TransformPoint(SpawnPoint());

    /// <summary>Map cell under a point given in map space (this object's local space).</summary>
    public static GridCoord CellAt(Vector3 mapPosition) =>
        new GridCoord(Mathf.FloorToInt(mapPosition.x / MapGrid.CellSize), Mathf.FloorToInt(mapPosition.z / MapGrid.CellSize));

    /// <summary>Map cell under a world-space point.</summary>
    public GridCoord CellOf(Vector3 worldPosition) => CellAt(transform.InverseTransformPoint(worldPosition));

    GridCoord ChunkOf(Vector3 worldPosition) => MapGrid.ChunkOf(CellOf(worldPosition));

    /// <summary>Centre of a cell on the floor, in world space.</summary>
    public Vector3 CellCenter(GridCoord cell) =>
        transform.TransformPoint(new Vector3((cell.x + .5f) * MapGrid.CellSize, 0f, (cell.y + .5f) * MapGrid.CellSize));

    public bool IsBuilt(GridCoord cell) => built.ContainsKey(MapGrid.ChunkOf(cell));

    public ZoneInfo ZoneOf(GridCoord cell) => Cache.ZoneOf(cell);

    /// <summary>
    /// True for the map's own architecture: chunk walls, floors and ceilings,
    /// doors and glass. False for furniture and anything else the kits add.
    /// </summary>
    public bool IsArchitecture(Collider c) => c != null && (shellColliders.Contains(c) || doorByCollider.ContainsKey(c) || windowByCollider.ContainsKey(c));

    /// <summary>True when two side-by-side cells share a window whose glass is broken: an opening to climb through.</summary>
    public bool IsBrokenWindow(GridCoord a, GridCoord b) =>
        Mathf.Abs(a.x - b.x) + Mathf.Abs(a.y - b.y) == 1 && Cache.Edge(a, b) == EdgeKind.Window && brokenWindows.Contains(EdgeId(a, b));

    /// <summary>True for the leaf of a door that is open, opening or broken.</summary>
    public bool IsOpenDoorLeaf(Collider c) => c != null && doorByCollider.TryGetValue(c, out var door) && door.open;

    public bool HasKeyFor(GridCoord zone) => keysHeld.Contains(zone);

    void Update()
    {
        if (!begun || player == null) return;
        Stream(ChunkOf(player.position), chunksPerFrame);
        DressNext();
        TickFixtures(Time.deltaTime);
        TickDoors(Time.deltaTime);
        CollectKeys();
    }

    void Stream(GridCoord center, int budget)
    {
        scratch.Clear();
        foreach (var coord in built.Keys)
            if (Mathf.Abs(coord.x - center.x) > buildRadius || Mathf.Abs(coord.y - center.y) > buildRadius) scratch.Add(coord);
        foreach (var coord in scratch) Drop(coord);
        // Nearest ring first, so the chunk the player walks into is never the one still waiting.
        for (var ring = 0; ring <= buildRadius && budget > 0; ring++)
        for (var dy = -ring; dy <= ring && budget > 0; dy++)
        for (var dx = -ring; dx <= ring && budget > 0; dx++)
        {
            if (Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)) != ring) continue;
            var coord = new GridCoord(center.x + dx, center.y + dy);
            if (built.ContainsKey(coord)) continue;
            // Decision 2: a chunk the player left long enough ago comes back
            // rearranged. It is always at least one chunk (24 m) away when it
            // is rebuilt, so the change is never seen.
            if (droppedAt.TryGetValue(coord, out var left) && Time.time - left >= shiftAfterSeconds)
            {
                Cache.Shift(coord);
                ShiftedChunks++;
            }
            droppedAt.Remove(coord);
            Build(coord);
            budget--;
        }
    }

    void Drop(GridCoord coord)
    {
        if (!built.TryGetValue(coord, out var chunk)) return;
        foreach (var door in chunk.doors)
        {
            movingDoors.Remove(door);
            doorByEdge.Remove(door.edge);
            if (door.leaf != null) doorByCollider.Remove(door.leaf);
        }
        foreach (var c in chunk.root.GetComponentsInChildren<Collider>(true))
        {
            windowByCollider.Remove(c);
            shellColliders.Remove(c);
        }
        Kill(chunk.root);
        built.Remove(coord);
        droppedAt[coord] = Time.time;
    }

    ThemeMaterials Theme(ZoneTheme theme) => theme == ZoneTheme.Office ? office : level0;

    void Build(GridCoord coord)
    {
        const int n = MapGrid.ChunkCells;
        var cs = MapGrid.CellSize;
        var data = Cache.Get(coord);
        var chunk = new BuiltChunk();
        var origin = new Vector3(coord.x * MapGrid.ChunkSize, 0f, coord.y * MapGrid.ChunkSize);
        chunk.root = new GameObject("Chunk " + coord + " · revision " + data.revision);
        chunk.root.transform.SetParent(transform, false);
        chunk.root.transform.localPosition = origin;

        // One set of meshes per 6 m block and ceiling height, so each renderer
        // can carry its own _CeilingHeight for the surface shader's grime band.
        const int blocks = n / BlockCells;
        const int heights = 3;
        var builders = new Dictionary<Material, MeshBuilder>[blocks * blocks * heights];
        for (var b = 0; b < builders.Length; b++) builders[b] = new Dictionary<Material, MeshBuilder>();
        MeshBuilder Get(int blockIndex, Material material)
        {
            if (!builders[blockIndex].TryGetValue(material, out var builder)) builders[blockIndex][material] = builder = new MeshBuilder();
            return builder;
        }
        var collision = new MeshBuilder();
        int BlockOf(int i, int j, float ceiling) => (i / BlockCells + j / BlockCells * blocks) * heights + HeightClass(ceiling);

        void Solid(int blockIndex, Material material, Vector3 center, Vector3 size, float repeat)
        {
            Get(blockIndex, material).Box(center, size, origin, repeat);
            collision.Box(center, size, origin, 1f);
        }

        for (var j = 0; j < n; j++)
        for (var i = 0; i < n; i++)
        {
            var index = MapGrid.LocalIndex(i, j);
            var cell = data.Cell(i, j);
            var zone = Cache.ZoneOf(cell);
            var theme = Theme(zone.theme);
            var height = MapGrid.CeilingHeight(data.height[index]);
            var b = BlockOf(i, j, height);
            var cellCenter = new Vector3((i + .5f) * cs, 0f, (j + .5f) * cs);
            Solid(b, theme.floor, cellCenter + Vector3.down * (ModuleUnits.FloorSlab * .5f), new Vector3(cs, ModuleUnits.FloorSlab, cs), CarpetRepeat);
            Solid(b, theme.ceiling, cellCenter + Vector3.up * (height + ModuleUnits.CeilingSlab * .5f), new Vector3(cs, ModuleUnits.CeilingSlab, cs), CeilingRepeat);

            // East and north edges of every cell. Chunk borders on the east and
            // north belong to this chunk; west and south ones to the neighbour.
            var east = new GridCoord(cell.x + 1, cell.y);
            var north = new GridCoord(cell.x, cell.y + 1);
            var eastZone = Cache.ZoneOf(east);
            var northZone = Cache.ZoneOf(north);
            var eastHeight = Mathf.Max(height, MapGrid.CeilingHeight(eastZone.height));
            var northHeight = Mathf.Max(height, MapGrid.CeilingHeight(northZone.height));
            BuildEdge(chunk, data.east[index], cell, east, new Vector3((i + 1) * cs, 0f, j * cs), Vector3.forward,
                eastHeight, theme.wall, Theme(eastZone.theme).wall, BlockOf(i, j, eastHeight), Get, Solid, origin);
            BuildEdge(chunk, data.north[index], cell, north, new Vector3(i * cs, 0f, (j + 1) * cs), Vector3.right,
                northHeight, theme.wall, Theme(northZone.theme).wall, BlockOf(i, j, northHeight), Get, Solid, origin);

            if (data.pillar[i + j * (n + 1)]) BuildColumn(data.pillarStyle[i + j * (n + 1)], new Vector3(i * cs, 0f, j * cs), height, zone.theme, theme, b, Get, Solid, origin);

            BuildFixture(chunk, cell, cellCenter, height, theme, data.lamp[index]);
        }

        for (var b = 0; b < builders.Length; b++)
        {
            if (builders[b].Count == 0) continue;
            var ceiling = HeightOfClass(b % heights);
            var go = new GameObject("Block " + b / heights + " · " + ceiling.ToString("0.0") + " m");
            go.transform.SetParent(chunk.root.transform, false);
            foreach (var pair in builders[b]) AddRenderer(go, pair.Key, pair.Value, chunk.root.transform.position.y + ceiling);
        }
        var col = new GameObject("Collision");
        col.transform.SetParent(chunk.root.transform, false);
        var shell = col.AddComponent<MeshCollider>();
        shell.sharedMesh = collision.ToMesh("Chunk collision " + coord);
        shellColliders.Add(shell);

        if (data.hasKey && !keysHeld.Contains(data.ownZone.id))
        {
            var key = GameObject.CreatePrimitive(PrimitiveType.Cube);
            key.name = "Key · zone " + data.ownZone.id;
            Kill(key.GetComponent<Collider>());
            key.transform.SetParent(chunk.root.transform, false);
            key.transform.localPosition = new Vector3((data.keyCell.x + .5f) * cs, 1.05f, (data.keyCell.y + .5f) * cs) - origin;
            key.transform.localScale = new Vector3(.32f, .12f, .12f);
            key.GetComponent<Renderer>().sharedMaterial = keyGlow;
            chunk.keys.Add((key, data.ownZone.id));
        }
        AddZoneGrades(chunk, data);
        Furnish(chunk, data);
        built[coord] = chunk;
    }

    static readonly int CeilingHeightId = Shader.PropertyToID("_CeilingHeight");

    static int HeightClass(float ceiling) => ceiling < 2.65f ? 0 : ceiling < 4f ? 1 : 2;
    static float HeightOfClass(int c) => c == 0 ? ModuleUnits.LowCeiling : c == 1 ? ModuleUnits.StandardCeiling : ModuleUnits.TallCeiling;

    /// <summary>
    /// A shell renderer. <paramref name="ceilingWorldY"/> is the world height
    /// of its ceiling plane: the surface shader grimes the 1.6 m under it.
    /// </summary>
    void AddRenderer(GameObject parent, Material material, MeshBuilder builder, float ceilingWorldY)
    {
        if (builder.vertices.Count == 0 || material == null) return;
        var go = new GameObject(material.name);
        go.transform.SetParent(parent.transform, false);
        go.AddComponent<MeshFilter>().sharedMesh = builder.ToMesh(parent.name + " " + material.name);
        var r = go.AddComponent<MeshRenderer>();
        r.sharedMaterial = material;
        r.shadowCastingMode = ShadowCastingMode.On;
        if (material.HasProperty(CeilingHeightId))
        {
            var props = new MaterialPropertyBlock();
            props.SetFloat(CeilingHeightId, ceilingWorldY);
            r.SetPropertyBlock(props);
        }
    }

    delegate MeshBuilder BuilderFn(int blockIndex, Material material);
    delegate void SolidFn(int blockIndex, Material material, Vector3 center, Vector3 size, float repeat);

    /// <summary>
    /// One 3 m edge from <paramref name="start"/> along <paramref name="along"/>.
    /// Where the two sides are different themes the wall is split in two
    /// halves, each faced in its own room's paper. Doorway width and position
    /// come from the edge's hash, so no two doorways line up.
    /// </summary>
    void BuildEdge(BuiltChunk chunk, EdgeKind kind, GridCoord a, GridCoord b, Vector3 start, Vector3 along, float height,
        Material wallA, Material wallB, int blockIndex, BuilderFn get, SolidFn solid, Vector3 origin)
    {
        if (kind == EdgeKind.Open) return;
        var length = MapGrid.CellSize;
        // Positive "across" points from cell a into cell b.
        var across = new Vector3(along.z, 0f, along.x);
        void Piece(float from, float to, float bottom, float top, bool extendStart, bool extendEnd)
        {
            if (from > 0f) extendStart = false;
            if (to < length) extendEnd = false;
            var f = from - (extendStart ? WallThickness * .5f : 0f);
            var t = to + (extendEnd ? WallThickness * .5f : 0f);
            if (t - f < .05f || top - bottom < .05f) return;
            var center = start + along * ((f + t) * .5f) + Vector3.up * ((bottom + top) * .5f);
            if (wallA == wallB)
            {
                var size = along * (t - f) + across * WallThickness + Vector3.up * (top - bottom);
                solid(blockIndex, wallA, center, Abs(size), WallpaperRepeat);
                return;
            }
            var half = along * (t - f) + across * (WallThickness * .5f) + Vector3.up * (top - bottom);
            solid(blockIndex, wallA, center - across * (WallThickness * .25f), Abs(half), WallpaperRepeat);
            solid(blockIndex, wallB, center + across * (WallThickness * .25f), Abs(half), WallpaperRepeat);
        }

        if (kind == EdgeKind.Wall) { Piece(0f, length, 0f, height, true, true); return; }

        float width, c, openingTop, sill = 0f;
        if (kind == EdgeKind.Arch)
        {
            ArchOpening(a, along.x > .5f, out width, out c);
            openingTop = Mathf.Min(ModuleUnits.ArchTop, height - ModuleUnits.ArchHeaderMin);
        }
        else if (kind == EdgeKind.Door)
        {
            width = DoorWidth;
            c = length * .5f;
            openingTop = DoorHeight;
        }
        else
        {
            width = WindowWidth;
            c = length * .5f;
            openingTop = WindowTop;
            sill = WindowSill;
        }
        Piece(0f, c - width * .5f, 0f, height, true, false);
        Piece(c + width * .5f, length, 0f, height, false, true);
        Piece(c - width * .5f, c + width * .5f, openingTop, height, false, false);
        if (sill > 0f) Piece(c - width * .5f, c + width * .5f, 0f, sill, false, false);

        if (kind == EdgeKind.Arch) return;

        // Frame: two jambs and a head in the trim colour.
        var trims = get(blockIndex, trim);
        var frame = ModuleUnits.TrimFace;
        var jambDepth = WallThickness + ModuleUnits.TrimProud * 2f;
        foreach (var s in new[] { -1f, 1f })
        {
            var jc = start + along * (c + s * (width * .5f + frame * .5f)) + Vector3.up * ((sill + openingTop) * .5f);
            trims.Box(jc, Abs(along * frame + across * jambDepth + Vector3.up * (openingTop - sill)), origin, 1f);
        }
        trims.Box(start + along * c + Vector3.up * (openingTop + frame * .5f), Abs(along * (width + frame * 2f) + across * jambDepth + Vector3.up * frame), origin, 1f);

        var edge = EdgeId(a, b);
        var openingCenter = chunk.root.transform.TransformPoint(start + along * c);
        if (kind == EdgeKind.Door)
        {
            // The hinge sits on one jamb and faces along the wall, so the leaf
            // spans the opening on its local Z and swings about the hinge's Y.
            var hinge = new GameObject("Door hinge " + a + "-" + b).transform;
            hinge.SetParent(chunk.root.transform, false);
            hinge.localPosition = start + along * (c - width * .5f);
            hinge.localRotation = Quaternion.LookRotation(along, Vector3.up);
            var leaf = GameObject.CreatePrimitive(PrimitiveType.Cube);
            leaf.name = "Door leaf";
            leaf.transform.SetParent(hinge, false);
            leaf.transform.localPosition = new Vector3(0f, (DoorHeight - ModuleUnits.DoorLeafGap) * .5f, width * .5f);
            leaf.transform.localScale = new Vector3(ModuleUnits.DoorLeafThickness, DoorHeight - ModuleUnits.DoorLeafGap, width - ModuleUnits.DoorLeafGap);
            leaf.GetComponent<Renderer>().sharedMaterial = doorLeaf;
            var door = new Door { hinge = hinge, closed = hinge.localRotation, leaf = leaf.GetComponent<Collider>(), a = a, b = b, edge = edge, position = openingCenter,
                swing = doorSwing.TryGetValue(edge, out var swung) ? swung : 1f };
            if (brokenDoors.Contains(edge)) { door.broken = door.open = true; }
            else if (openDoors.Contains(edge)) door.open = true;
            if (door.open)
            {
                door.progress = 1f;
                hinge.localRotation = door.closed * Quaternion.Euler(0f, -ModuleUnits.DoorSwingDegrees * door.swing, 0f);
            }
            chunk.doors.Add(door);
            doorByCollider[door.leaf] = door;
            doorByEdge[edge] = door;
        }
        else
        {
            if (brokenWindows.Contains(edge)) return;
            var pane = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pane.name = "Window pane " + a + "-" + b;
            pane.transform.SetParent(chunk.root.transform, false);
            pane.transform.localPosition = start + along * c + Vector3.up * ((sill + openingTop) * .5f);
            pane.transform.localScale = Abs(along * width + across * ModuleUnits.GlassThickness + Vector3.up * (openingTop - sill));
            pane.GetComponent<Renderer>().sharedMaterial = glass;
            var window = new Window { pane = pane, edge = edge, position = openingCenter };
            chunk.windows.Add(window);
            windowByCollider[pane.GetComponent<Collider>()] = window;
        }
    }

    static Vector3 Abs(Vector3 v) => new Vector3(Mathf.Abs(v.x), Mathf.Abs(v.y), Mathf.Abs(v.z));

    /// <summary>
    /// A structural column on a 6 m grid corner (see MapSettings): faced in
    /// the room's wall material, on a cove base. Office columns carry a
    /// bulkhead to the next column on the grid. The bulkhead is
    /// above every head, so it has no collision.
    /// </summary>
    void BuildColumn(byte style, Vector3 at, float height, ZoneTheme zoneTheme, ThemeMaterials theme, int blockIndex, BuilderFn get, SolidFn solid, Vector3 origin)
    {
        var w = (style & MapChunk.ColumnLarge) != 0 ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall;
        solid(blockIndex, theme.wall, at + Vector3.up * (height * .5f), new Vector3(w, height, w), WallpaperRepeat);
        var cove = w + ModuleUnits.CoveProud * 2f;
        get(blockIndex, trim).Box(at + Vector3.up * (ModuleUnits.CoveHeight * .5f), new Vector3(cove, ModuleUnits.CoveHeight, cove), origin, 1f);
        if (zoneTheme != ZoneTheme.Office) return;
        var span = ModuleUnits.ColumnGrid - w;
        var y = height - ModuleUnits.BulkheadDepth * .5f;
        if ((style & MapChunk.ColumnBeamEast) != 0)
            get(blockIndex, theme.wall).Box(at + new Vector3(ModuleUnits.ColumnGrid * .5f, y, 0f), new Vector3(span, ModuleUnits.BulkheadDepth, w), origin, WallpaperRepeat);
        if ((style & MapChunk.ColumnBeamNorth) != 0)
            get(blockIndex, theme.wall).Box(at + new Vector3(0f, y, ModuleUnits.ColumnGrid * .5f), new Vector3(w, ModuleUnits.BulkheadDepth, span), origin, WallpaperRepeat);
    }

    /// <summary>
    /// Width and position (metres from the edge's start) of a doorless
    /// doorway, from the edge's hash. <paramref name="a"/> is the west or
    /// south cell; <paramref name="alongX"/> is true for its north edge.
    /// </summary>
    void ArchOpening(GridCoord a, bool alongX, out float width, out float center)
    {
        var edgeHash = MapHash.Hash(Cache.Generator.Seed, a.x * 2 + (alongX ? 1 : 0), a.y, 97);
        width = ModuleUnits.ArchMinWidth + ModuleUnits.ArchWidthSpread * MapHash.Unit(edgeHash);
        var margin = ModuleUnits.ArchCornerMargin + width * .5f;
        center = Mathf.Lerp(margin, MapGrid.CellSize - margin, MapHash.Unit(MapHash.Hash((int)edgeHash, 3, 7, 11)));
    }

    /// <summary>
    /// Where to cross from one cell into its neighbour, in world space: the
    /// middle of the doorway, door or window, or of the shared edge when it is
    /// open. Doorways sit off-centre, so walking centre to centre can hit wall.
    /// </summary>
    public Vector3 CrossingPoint(GridCoord a, GridCoord b)
    {
        var lo = a;
        var hi = b;
        if (hi.x < lo.x || hi.y < lo.y) { lo = b; hi = a; }
        var cs = MapGrid.CellSize;
        var eastward = hi.x > lo.x;
        var start = eastward ? new Vector3((lo.x + 1) * cs, 0f, lo.y * cs) : new Vector3(lo.x * cs, 0f, (lo.y + 1) * cs);
        var along = eastward ? Vector3.forward : Vector3.right;
        var center = cs * .5f;
        if (Cache.Edge(lo, hi) == EdgeKind.Arch) ArchOpening(lo, !eastward, out _, out center);
        return transform.TransformPoint(start + along * center);
    }

    static long EdgeId(GridCoord a, GridCoord b)
    {
        if (b.x < a.x || b.y < a.y) { var t = a; a = b; b = t; }
        var dir = b.x > a.x ? 1L : 0L;
        return ((long)a.x << 33) ^ ((long)(a.y & 0x7fffffff) << 1) ^ dir;
    }

    // ---------- Passage, for the Relay and the autopilot ----------

    /// <summary>What lies between two side-by-side cells right now.</summary>
    public Passage PassageBetween(GridCoord a, GridCoord b)
    {
        // Only side-by-side cells share an edge; anything else is no way through.
        if (Mathf.Abs(a.x - b.x) + Mathf.Abs(a.y - b.y) != 1) return Passage.Wall;
        switch (Cache.Edge(a, b))
        {
            case EdgeKind.Open:
            case EdgeKind.Arch:
                return Passage.Open;
            case EdgeKind.Door:
                var id = EdgeId(a, b);
                if (brokenDoors.Contains(id) || openDoors.Contains(id)) return Passage.Open;
                return doorByEdge.TryGetValue(id, out var door) && door.open && door.progress > .6f ? Passage.Open : Passage.ClosedDoor;
            case EdgeKind.Window:
                return brokenWindows.Contains(EdgeId(a, b)) ? Passage.Open : Passage.Glass;
            default:
                return Passage.Wall;
        }
    }

    /// <summary>The built door between two cells, or null.</summary>
    public Door DoorBetween(GridCoord a, GridCoord b) => doorByEdge.TryGetValue(EdgeId(a, b), out var door) ? door : null;

    /// <summary>The Relay forces a door: it stays open for good.</summary>
    public void BreakDoor(Door door, Vector3 from)
    {
        if (door == null) return;
        if (!door.open) SwingAway(door, from);
        door.broken = true;
        door.open = true;
        brokenDoors.Add(door.edge);
        if (!movingDoors.Contains(door)) movingDoors.Add(door);
        DoorBroken?.Invoke(door.position);
    }

    /// <summary>Open a door without aiming at it (autopilot). Respects the key rule.</summary>
    public bool TryOpenDoor(GridCoord a, GridCoord b)
    {
        var door = DoorBetween(a, b);
        if (door == null || door.open) return door != null;
        if (doorsNeedKeys && !HasKeyHere()) return false;
        SwingAway(door, CellCenter(a));
        SetDoor(door, true);
        return true;
    }

    // ---------- Fixtures: each lamp keeps its own state ----------

    void BuildFixture(BuiltChunk chunk, GridCoord cell, Vector3 localCenter, float height, ThemeMaterials theme, ModuleLamp lamp)
    {
        // A module can take a lamp out altogether.
        if (lamp == ModuleLamp.Off) return;
        var seed = Cache.Generator.Seed;
        var fixture = new Fixture { rng = MapHash.Hash(seed, cell.x, cell.y, 211) | 1u };
        var root = new GameObject("Fixture " + cell);
        root.transform.SetParent(chunk.root.transform, false);
        // The lens fills whole 0.6 m ceiling tiles: X [1.2, 1.8], Z [1.2, 2.4] of the cell.
        root.transform.localPosition = localCenter + new Vector3(0f, height, ModuleUnits.TrofferOffsetZ);
        var panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
        panel.name = "Lens";
        Kill(panel.GetComponent<Collider>());
        panel.transform.SetParent(root.transform, false);
        panel.transform.localPosition = new Vector3(0f, -ModuleUnits.TrofferDrop, 0f);
        panel.transform.localScale = new Vector3(ModuleUnits.TrofferShort, ModuleUnits.TrofferLens, ModuleUnits.TrofferLong);
        var pr = panel.GetComponent<Renderer>();
        pr.sharedMaterial = theme.lens;
        pr.shadowCastingMode = ShadowCastingMode.Off;
        fixture.panel = pr;
        fixture.emission = theme.lens.HasProperty("_EmissionColor") ? theme.lens.GetColor("_EmissionColor") : Color.black;

        // A troffer only throws light downward: a wide spot at the lens, as
        // in the room stream, so the lit lens reads against the ceiling.
        var lightGo = new GameObject("Light");
        lightGo.transform.SetParent(root.transform, false);
        lightGo.transform.localPosition = new Vector3(0f, -ModuleUnits.LampDrop, 0f);
        lightGo.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
        var light = lightGo.AddComponent<Light>();
        light.type = LightType.Spot;
        light.spotAngle = 162f;
        light.innerSpotAngle = 96f;
        light.color = new Color(1f, .96f, .88f);
        light.range = height > 4f ? 12f : 10f;
        light.shadows = LightShadows.None;
        light.shadowStrength = .92f;
        light.shadowNearPlane = .1f;
        fixture.baseIntensity = theme.lampIntensity * (height > 4f ? 1.6f : 1f);
        fixture.light = light;
        // About one lamp in three may cast shadows, and only near the player.
        fixture.castsShadow = MapHash.Unit(MapHash.Hash(seed, cell.x, cell.y, 223)) < .34f;

        // Lamp temperament, rolled once per lamp from the seed and its cell:
        // 0 steady, 1 stutters now and then, 2 failing, 3 dead with rare blinks, 4 dim.
        var roll = Rand(ref fixture.rng);
        fixture.mode = roll < .62f ? 0 : roll < .82f ? 1 : roll < .92f ? 2 : roll < .97f ? 3 : 4;
        // A module's lamp: Steady..Dim map onto modes 0..4.
        if (lamp != ModuleLamp.Auto) fixture.mode = (int)lamp - 1;
        fixture.phase = Rand(ref fixture.rng) * 50f;
        fixture.nextEvent = 2f + Rand(ref fixture.rng) * 14f;
        chunk.fixtures.Add(fixture);
    }

    void TickFixtures(float dt)
    {
        if (player == null) return;
        var p = player.position;
        foreach (var chunk in built.Values)
        foreach (var f in chunk.fixtures)
        {
            f.clock += dt;
            f.level = Level(f);
            var lp = f.light.transform.position;
            var d = Vector2.Distance(new Vector2(lp.x, lp.z), new Vector2(p.x, p.z));
            var fade = Mathf.Clamp01((lightRadius - d) / 3f);
            var on = fade > 0f && f.level > .01f;
            if (f.light.enabled != on) f.light.enabled = on;
            if (on) f.light.intensity = f.baseIntensity * f.level * fade;
            var shadows = f.castsShadow && on && d < shadowRadius ? LightShadows.Soft : LightShadows.None;
            if (f.light.shadows != shadows) f.light.shadows = shadows;
            f.panel.GetPropertyBlock(block);
            block.SetColor("_EmissionColor", f.emission * Mathf.Max(.04f, f.level));
            f.panel.SetPropertyBlock(block);
        }
    }

    static float Level(Fixture f)
    {
        var t = f.clock + f.phase;
        switch (f.mode)
        {
            case 1:
                // Steady, then a short stutter at its own random interval.
                if (f.clock >= f.nextEvent && f.eventEnd <= f.clock)
                {
                    f.eventEnd = f.clock + .15f + Rand(ref f.rng) * .7f;
                    f.nextEvent = f.eventEnd + 5f + Rand(ref f.rng) * 15f;
                }
                if (f.clock < f.eventEnd) return Mathf.PerlinNoise(t * 23f, f.phase) > .45f ? .95f : .05f;
                return .97f + .03f * Mathf.Sin(t * 120f);
            case 2:
                // Failing ballast: never settles, drops out at its own rhythm.
                var wave = .5f + .5f * Mathf.Sin(t * 3.1f) * (.7f + .3f * Mathf.Sin(t * 1.27f));
                var dropout = Mathf.PerlinNoise(t * 1.4f, f.phase) > .72f ? .05f : 1f;
                return (.25f + .45f * wave) * dropout;
            case 3:
                // Dead tube that blinks once in a long while.
                if (f.clock >= f.nextEvent && f.eventEnd <= f.clock)
                {
                    f.eventEnd = f.clock + .06f + Rand(ref f.rng) * .12f;
                    f.nextEvent = f.eventEnd + 8f + Rand(ref f.rng) * 20f;
                }
                return f.clock < f.eventEnd ? .8f : 0f;
            case 4:
                return .42f + .03f * Mathf.Sin(t * 90f);
            default:
                return .98f + .02f * Mathf.Sin(t * 110f);
        }
    }

    static float Rand(ref uint state)
    {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        return (state & 0xffffff) / 16777216f;
    }

    // ---------- Furnishing (through the visual session's kits, when present) ----------

    static void ResolveDressers()
    {
        if (dressersResolved) return;
        dressersResolved = true;
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            var kit = assembly.GetType("FrontRoomsOfficeKit");
            if (kit != null && officeDress == null && officeDressOld == null)
            {
                // Two overloads share the name: bind by parameter types. The
                // newer one takes the room's columns as obstacles.
                officeDress = kit.GetMethod("Dress", BindingFlags.Public | BindingFlags.Static, null,
                    new[] { typeof(Transform), typeof(Rect), typeof(float), typeof(int), typeof(Rect[]), typeof(Rect[]) }, null);
                if (officeDress == null)
                    officeDressOld = kit.GetMethod("Dress", BindingFlags.Public | BindingFlags.Static, null,
                        new[] { typeof(Transform), typeof(Rect), typeof(float), typeof(int), typeof(Rect[]) }, null);
            }
            var pile = assembly.GetType("FrontRoomsFurniturePile");
            if (pile != null && pileBuild == null)
                pileBuild = pile.GetMethod("Build", BindingFlags.Public | BindingFlags.Static, null,
                    new[] { typeof(Transform), typeof(Vector3), typeof(float), typeof(float), typeof(int) }, null);
        }
    }

    /// <summary>
    /// Queue the chunk's rooms for furnishing: Office rooms get an office
    /// layout, large halls sometimes a furniture pile. Only rooms that are one
    /// open rectangle qualify: no later room cuts into them, and every cell
    /// has the same height and theme.
    /// </summary>
    void Furnish(BuiltChunk chunk, MapChunk data)
    {
        ResolveDressers();
        if (officeDress == null && officeDressOld == null && pileBuild == null) return;
        for (var r = 0; r < data.rooms.Length; r++)
            if (data.RoomIntact(r) && Cache.Generator.Uniform(data, data.rooms[r]))
                dressQueue.Enqueue(new DressJob { chunk = chunk, data = data, room = r });
    }

    /// <summary>Furnish the next queued room whose chunk is still standing. Returns false when the queue is empty.</summary>
    bool DressNext()
    {
        while (dressQueue.Count > 0)
        {
            var job = dressQueue.Dequeue();
            if (job.chunk.root == null || !built.TryGetValue(job.data.coord, out var current) || current != job.chunk) continue;
            Dress(job.chunk, job.data, job.room);
            return true;
        }
        return false;
    }

    void Dress(BuiltChunk chunk, MapChunk data, int r)
    {
        var cs = MapGrid.CellSize;
        var room = data.rooms[r];
        var zone = Cache.ZoneOf(data.Cell(room.x, room.y));
        var height = MapGrid.CeilingHeight(zone.height);
        var roomSeed = (int)MapHash.Hash(Cache.Generator.Seed, data.coord.x * 16 + r, data.coord.y, 307, data.revision);
        var columns = Columns(data, room);
        var clear = new List<Rect>(KeepClear(data, room));
        // The player starts in the middle of chunk (0, 0): keep that spot clear too.
        var mid = MapGrid.ChunkCells / 2;
        if (data.coord.x == 0 && data.coord.y == 0 && room.Contains(mid, mid))
        {
            var spawn = SpawnPoint();
            clear.Add(new Rect(spawn.x - 1f, spawn.z - 1f, 2f, 2f));
        }
        try
        {
            // A module's own props go in first; the kits fill round them.
            var module = data.ModuleOf(r);
            var obstacles = new List<Rect>(columns);
            if (module != null) obstacles.AddRange(PlaceProps(chunk, room, module));
            var fill = module == null ? ModuleFill.Auto : module.fill;
            var office = fill == ModuleFill.Office || (fill == ModuleFill.Auto && zone.theme == ZoneTheme.Office);
            if (office)
            {
                if (!dressOffices) return;
                // The clear floor between wall faces; keep-clear strips and columns are in the same chunk-local metres.
                var floor = new Rect(room.x * cs + ModuleUnits.WallHalf, room.y * cs + ModuleUnits.WallHalf,
                    room.w * cs - ModuleUnits.WallThickness, room.h * cs - ModuleUnits.WallThickness);
                if (officeDress != null) officeDress.Invoke(null, new object[] { chunk.root.transform, floor, height, roomSeed, clear.ToArray(), obstacles.ToArray() });
                else if (officeDressOld != null) officeDressOld.Invoke(null, new object[] { chunk.root.transform, floor, height, roomSeed, clear.ToArray() });
                return;
            }
            var pile = fill == ModuleFill.Pile
                || (fill == ModuleFill.Auto && Mathf.Min(room.w, room.h) >= 4 && MapHash.Unit((uint)roomSeed) < (zone.height == ZoneHeight.Tall ? Mathf.Max(pileChance, .6f) : pileChance));
            if (pile && pileBuild != null)
            {
                // The pile keeps off the module's props as it does off the strips.
                var keepOff = new List<Rect>(clear);
                keepOff.AddRange(obstacles.GetRange(columns.Count, obstacles.Count - columns.Count));
                if (PileSpot(room, columns, keepOff, out var center, out var radius))
                    pileBuild.Invoke(null, new object[] { chunk.root.transform, center, radius, height, roomSeed });
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning("[FrontRoomsMap] Furnishing room " + r + " of chunk " + data.coord + " failed: " + (e.InnerException ?? e).Message);
        }
    }

    /// <summary>
    /// A module's props, placed with the visual chat's kit library at their
    /// module positions. Returns their footprints in chunk-local metres.
    /// </summary>
    List<Rect> PlaceProps(BuiltChunk chunk, CellRect room, RoomModuleData module)
    {
        var footprints = new List<Rect>();
        if (module.props == null || module.props.Length == 0) return footprints;
        var cs = MapGrid.CellSize;
        var root = new GameObject("module props").transform;
        root.SetParent(chunk.root.transform, false);
        float ox = room.x * cs, oz = room.y * cs;
        foreach (var p in module.props)
        {
            if (string.IsNullOrEmpty(p.kit)) continue;
            if (FrontRoomsKitLibrary.Spawn(p.kit, root, new Vector3(ox + p.x, 0f, oz + p.z), p.yaw, null, !p.noCollider, p.kit) == null) continue;
            var f = KitFootprint(p.kit);
            if (f == null) continue;
            RoomModuleData.Bounds(p, f, out var x0, out var z0, out var x1, out var z1);
            footprints.Add(Rect.MinMaxRect(ox + x0, oz + z0, ox + x1, oz + z1));
        }
        return footprints;
    }

    /// <summary>A kit asset's footprint about its pivot and its height: (min x, min z, max x, max z, height), or null.</summary>
    public static float[] KitFootprint(string kit)
    {
        var info = FrontRoomsKitLibrary.GetInfo(kit);
        if (info == null) return null;
        var f = info.Footprint;
        return new[] { f.xMin, f.yMin, f.xMax, f.yMax, info.Height };
    }

    /// <summary>
    /// The visual chat's local Office grade (FrontRoomsPostStack.EnsureZoneVolume)
    /// over this chunk's Office cells: runs of Office cells per row, merged
    /// into rectangles down the rows, one volume each. Its 2.5 m blend hides
    /// the seams between them.
    /// </summary>
    void AddZoneGrades(BuiltChunk chunk, MapChunk data)
    {
        const int n = MapGrid.ChunkCells;
        var cs = MapGrid.CellSize;
        var open = new List<(int x0, int x1, int y0, int y1)>();
        var done = new List<(int x0, int x1, int y0, int y1)>();
        for (var j = 0; j <= n; j++)
        {
            var runs = new List<(int, int)>();
            for (var i = 0; j < n && i < n;)
            {
                if (Cache.ZoneOf(data.Cell(i, j)).theme != ZoneTheme.Office) { i++; continue; }
                var start = i;
                while (i < n && Cache.ZoneOf(data.Cell(i, j)).theme == ZoneTheme.Office) i++;
                runs.Add((start, i));
            }
            var next = new List<(int x0, int x1, int y0, int y1)>();
            foreach (var rect in open)
            {
                var k = runs.IndexOf((rect.x0, rect.x1));
                if (k >= 0) { next.Add((rect.x0, rect.x1, rect.y0, j + 1)); runs.RemoveAt(k); }
                else done.Add(rect);
            }
            foreach (var run in runs) next.Add((run.Item1, run.Item2, j, j + 1));
            open = next;
        }
        for (var k = 0; k < done.Count; k++)
        {
            var rect = done[k];
            var size = new Vector3((rect.x1 - rect.x0) * cs, ModuleUnits.StandardCeiling, (rect.y1 - rect.y0) * cs);
            var center = new Vector3(rect.x0 * cs + size.x * .5f, size.y * .5f, rect.y0 * cs + size.z * .5f);
            // EnsureZoneVolume keeps one volume per parent, so each rectangle gets its own.
            var holder = new GameObject("Office grade " + k).transform;
            holder.SetParent(chunk.root.transform, false);
            FrontRoomsPostStack.EnsureZoneVolume(holder, "Office", new Bounds(center, size), 2.5f);
        }
    }

    /// <summary>Footprints of the columns inside a room, in chunk-local metres.</summary>
    List<Rect> Columns(MapChunk data, CellRect room)
    {
        const int n = MapGrid.ChunkCells;
        var cs = MapGrid.CellSize;
        var result = new List<Rect>();
        for (var j = room.y + 1; j < room.y + room.h; j++)
        for (var i = room.x + 1; i < room.x + room.w; i++)
        {
            if (!data.pillar[i + j * (n + 1)]) continue;
            var w = (data.pillarStyle[i + j * (n + 1)] & MapChunk.ColumnLarge) != 0 ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall;
            result.Add(new Rect(i * cs - w * .5f, j * cs - w * .5f, w, w));
        }
        return result;
    }

    /// <summary>
    /// Where a furniture pile goes: the room centre, or with columns the
    /// centre of the 6 m bay nearest it, sized so the pile and its 0.6 m
    /// clear ring keep off the columns and the walls, and the pile itself off
    /// every keep-clear strip (openings, the spawn). False if no pile fits.
    /// </summary>
    bool PileSpot(CellRect room, List<Rect> columns, List<Rect> clear, out Vector3 center, out float radius)
    {
        const float ring = .6f, minRadius = 1.2f;
        var cs = MapGrid.CellSize;
        var min = new Vector2(room.x * cs + ModuleUnits.WallHalf, room.y * cs + ModuleUnits.WallHalf);
        var max = new Vector2((room.x + room.w) * cs - ModuleUnits.WallHalf, (room.y + room.h) * cs - ModuleUnits.WallHalf);
        var c = (min + max) * .5f;
        if (columns.Count > 0)
        {
            // Bay centres sit half a grid off the column lines (chunk origins are multiples of 24 m, so local = world phase).
            var g = ModuleUnits.ColumnGrid;
            c = new Vector2((Mathf.Floor(c.x / g) + .5f) * g, (Mathf.Floor(c.y / g) + .5f) * g);
        }
        radius = Mathf.Min(3.2f, Mathf.Min(room.w, room.h) * cs * .22f);
        radius = Mathf.Min(radius, Mathf.Min(Mathf.Min(c.x - min.x, max.x - c.x), Mathf.Min(c.y - min.y, max.y - c.y)) - ring);
        foreach (var col in columns) radius = Mathf.Min(radius, Distance(col, c) - ring);
        foreach (var strip in clear) radius = Mathf.Min(radius, Distance(strip, c));
        center = new Vector3(c.x, 0f, c.y);
        return radius >= minRadius;
    }

    /// <summary>
    /// Every passable stretch of the room's boundary (open, doorway, door or
    /// window) gets a strip of floor kept clear along the inside of that
    /// cell edge: <see cref="ModuleUnits.EntryClearDepth"/> deep, or
    /// <see cref="ModuleUnits.DoorClearDepth"/> for a door so its leaf can
    /// swing. Dress treats the boundary as wall wherever no strip touches it.
    /// </summary>
    Rect[] KeepClear(MapChunk data, CellRect room)
    {
        var cs = MapGrid.CellSize;
        var clear = new List<Rect>();
        for (var y = room.y; y < room.y + room.h; y++)
        for (var x = room.x; x < room.x + room.w; x++)
        {
            var cell = data.Cell(x, y);
            foreach (var d in new[] { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) })
            {
                if (room.Contains(x + d.x, y + d.y)) continue;
                var kind = Cache.Edge(cell, cell + d);
                if (!MapGrid.Passable(kind)) continue;
                // Strips start on the cell line, so they reach their depth from the wall face.
                var depth = (kind == EdgeKind.Door ? ModuleUnits.DoorClearDepth : ModuleUnits.EntryClearDepth) + ModuleUnits.WallHalf;
                if (d.x != 0) clear.Add(new Rect(d.x > 0 ? (x + 1) * cs - depth : x * cs, y * cs, depth, cs));
                else clear.Add(new Rect(x * cs, d.y > 0 ? (y + 1) * cs - depth : y * cs, cs, depth));
            }
        }
        return clear.ToArray();
    }

    // ---------- Interaction ----------

    public string Describe(Collider c, out bool holdToUse)
    {
        holdToUse = false;
        if (c == null) return null;
        if (doorByCollider.TryGetValue(c, out var door))
        {
            if (door.broken) return null;
            if (door.open) return "E  ·  SHUT DOOR";
            if (HasKeyHere()) return "E  ·  OPEN DOOR";
            return doorsNeedKeys ? "LOCKED  ·  NEEDS THIS ZONE'S KEY" : "E  ·  OPEN DOOR";
        }
        if (windowByCollider.ContainsKey(c))
        {
            holdToUse = true;
            return "HOLD E  ·  BREAK GLASS";
        }
        return null;
    }

    public void Use(Collider c)
    {
        if (c == null || !doorByCollider.TryGetValue(c, out var door) || door.broken) return;
        if (!door.open && doorsNeedKeys && !HasKeyHere()) return;
        if (!door.open && player != null) SwingAway(door, player.position);
        SetDoor(door, !door.open);
    }

    /// <summary>
    /// Make the leaf swing to the far side from a point, as a pushed door does.
    /// The hinge is on the edge's low jamb; with swing +1 an east edge's leaf
    /// goes west (into a) and a north edge's goes north (into b).
    /// </summary>
    void SwingAway(Door door, Vector3 worldFrom)
    {
        // Leaf still moving (closing): keep its side, so the door just reverses.
        if (door.progress > 0f) return;
        var p = transform.InverseTransformPoint(worldFrom);
        var mid = transform.InverseTransformPoint(door.position);
        var eastEdge = door.b.x != door.a.x;
        var fromB = eastEdge ? p.x > mid.x : p.z > mid.z;
        door.swing = eastEdge ? (fromB ? 1f : -1f) : (fromB ? -1f : 1f);
        doorSwing[door.edge] = door.swing;
    }

    void SetDoor(Door door, bool open)
    {
        door.open = open;
        if (open) openDoors.Add(door.edge); else openDoors.Remove(door.edge);
        if (!movingDoors.Contains(door)) movingDoors.Add(door);
        DoorMoved?.Invoke(door.position);
    }

    /// <summary>Hold progress on a window; returns true the frame the glass breaks.</summary>
    public bool Hold(Collider c, float dt, out float progress)
    {
        progress = 0f;
        if (c == null || !windowByCollider.TryGetValue(c, out var window)) return false;
        window.hold += dt;
        progress = Mathf.Clamp01(window.hold / 1f);
        if (window.hold < 1f) return false;
        brokenWindows.Add(window.edge);
        windowByCollider.Remove(c);
        Kill(window.pane);
        GlassBroken?.Invoke(window.position);
        return true;
    }

    public void ReleaseHold(Collider c)
    {
        if (c != null && windowByCollider.TryGetValue(c, out var window)) window.hold = 0f;
    }

    bool HasKeyHere() => player != null && keysHeld.Contains(Cache.ZoneOf(CellOf(player.position)).id);

    /// <summary>Tools and tests in edit mode, where Update does not run: move doors that are opening or breaking.</summary>
    public void TickDoorsForTools(float dt) => TickDoors(dt);

    void TickDoors(float dt)
    {
        for (var i = movingDoors.Count - 1; i >= 0; i--)
        {
            var door = movingDoors[i];
            if (door.hinge == null) { movingDoors.RemoveAt(i); continue; }
            var speed = door.broken ? .18f : .55f;
            door.progress = Mathf.MoveTowards(door.progress, door.open ? 1f : 0f, dt / speed);
            var e = door.progress * door.progress * (3f - 2f * door.progress);
            door.hinge.localRotation = door.closed * Quaternion.Euler(0f, -ModuleUnits.DoorSwingDegrees * door.swing * e, 0f);
            if (Mathf.Approximately(door.progress, door.open ? 1f : 0f)) movingDoors.RemoveAt(i);
        }
    }

    void CollectKeys()
    {
        var p = player.position;
        foreach (var chunk in built.Values)
            for (var i = chunk.keys.Count - 1; i >= 0; i--)
            {
                var (go, zone) = chunk.keys[i];
                if (go == null) { chunk.keys.RemoveAt(i); continue; }
                go.transform.Rotate(0f, 90f * Time.deltaTime, 0f, Space.World);
                var d = go.transform.position - p;
                if (new Vector2(d.x, d.z).sqrMagnitude > .9f * .9f) continue;
                keysHeld.Add(zone);
                Kill(go);
                chunk.keys.RemoveAt(i);
                KeyTaken?.Invoke(zone);
            }
    }

    // ---------- Materials ----------

    /// <summary>
    /// The map uses the game's URP surfaces (Resources/Surfaces): Level 0
    /// chevron paper, loop-pile carpet and 2'x4' ceiling grid; the Office
    /// zones use the office drywall, carpet tiles and 2'x2' grid. All are
    /// projected in world metres by FrontRooms/Surface. Run FrontRooms →
    /// Rendering → Set up URP, post and surfaces once if they are missing.
    /// </summary>
    void BuildMaterials()
    {
        var level0Lens = FrontRoomsSurfaces.Lit("Map / Level 0 lens", new Color(1f, .98f, .92f), .1f, 0f, new Color(1f, .96f, .84f) * 2.6f);
        level0 = new ThemeMaterials
        {
            wall = FrontRoomsSurfaces.Room(RoomRule.Lobby, FrontRoomsSurfaces.Slot.Wall),
            floor = FrontRoomsSurfaces.Room(RoomRule.Lobby, FrontRoomsSurfaces.Slot.Floor),
            ceiling = FrontRoomsSurfaces.Room(RoomRule.Lobby, FrontRoomsSurfaces.Slot.Ceiling),
            lens = level0Lens,
            lampIntensity = 5f,
        };
        var officeLens = FrontRoomsSurfaces.OfficeLouver;
        office = new ThemeMaterials
        {
            wall = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Wall),
            floor = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Floor),
            ceiling = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Ceiling),
            lens = officeLens != null && officeLens.HasProperty("_EmissionColor") ? officeLens : level0Lens,
            lampIntensity = 5.5f,
        };
        if (level0.wall == null) level0.wall = FrontRoomsSurfaces.Lit("Map / wall fallback", new Color(.80f, .74f, .48f), .06f);
        if (level0.floor == null) level0.floor = FrontRoomsSurfaces.Lit("Map / floor fallback", new Color(.55f, .49f, .30f), 0f);
        if (level0.ceiling == null) level0.ceiling = FrontRoomsSurfaces.Lit("Map / ceiling fallback", new Color(.86f, .83f, .70f), .02f);
        if (office.wall == null) office.wall = level0.wall;
        if (office.floor == null) office.floor = level0.floor;
        if (office.ceiling == null) office.ceiling = level0.ceiling;
        trim = FrontRoomsSurfaces.CoveBase ?? FrontRoomsSurfaces.Lit("Map test / frame", new Color(.55f, .50f, .36f), .2f);
        doorLeaf = FrontRoomsSurfaces.DoorVeneer ?? FrontRoomsSurfaces.Lit("Map test / door", new Color(.72f, .66f, .50f), .25f);
        keyGlow = FrontRoomsSurfaces.Lit("Map test / key", new Color(.96f, .87f, .23f), .4f, 0f, new Color(.96f, .87f, .23f) * .8f);
        glass = TransparentGlass("Map test / glass", new Color(.75f, .85f, .88f, .28f));
    }

    static Material TransparentGlass(string name, Color color)
    {
        var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = name };
        m.SetColor("_BaseColor", color);
        m.SetFloat("_Smoothness", .9f);
        m.SetFloat("_Surface", 1f);      // transparent
        m.SetFloat("_Blend", 0f);        // alpha
        m.SetFloat("_AlphaClip", 0f);
        m.SetFloat("_ZWrite", 0f);
        m.SetFloat("_SrcBlend", (float)BlendMode.One);
        m.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
        m.SetOverrideTag("RenderType", "Transparent");
        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        m.EnableKeyword("_ALPHAPREMULTIPLY_ON");
        m.renderQueue = (int)RenderQueue.Transparent;
        return m;
    }
}
