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
    const float WallThickness = .16f;
    const int BlockCells = 2;
    const float DoorWidth = 1f, DoorHeight = 2.1f;
    const float WindowWidth = 1.4f, WindowSill = .35f, WindowTop = 2.0f;
    const float WallpaperRepeat = 1.2f, CarpetRepeat = 1.5f, CeilingRepeat = 1.2f;

    [SerializeField] MapSettings settings = new MapSettings();
    [SerializeField, Tooltip("Pick a new seed every time Play starts (standalone test scene only).")] bool randomSeedOnPlay = false;
    [SerializeField, Tooltip("On: the test scene, which spawns its own walker and sets fog. The main game creates the map embedded instead.")] bool standalone = true;
    [SerializeField, Min(1), Tooltip("Chunks kept built around the player in each direction. 1 = 3 x 3, 2 = 5 x 5.")] int buildRadius = 1;
    [SerializeField, Min(1), Tooltip("New chunks built per frame while streaming. The first build around the spawn is always complete.")] int chunksPerFrame = 1;
    [SerializeField, Tooltip("A chunk the player has been away from for at least this long comes back with a shifted interior.")] float shiftAfterSeconds = 30f;
    [SerializeField, Tooltip("Fixture lights beyond this distance are switched off.")] float lightRadius = 14f;
    [SerializeField] float fogStart = 4f;
    [SerializeField, Tooltip("Standalone only. Keep it under the distance to the first unbuilt chunk.")] float fogEnd = 20f;
    [SerializeField] Color fogColor = new Color(.30f, .28f, .19f);
    [SerializeField] Color ambientColor = new Color(.34f, .32f, .23f);
    [SerializeField, Tooltip("Off: doors open without the zone key, so a walk never gets stuck. Keys are still collected.")] bool doorsNeedKeys = false;
    [SerializeField, Tooltip("Furnish Office-zone rooms with FrontRoomsOfficeKit when it exists.")] bool dressOffices = true;
    [SerializeField, Range(0f, 1f), Tooltip("Chance that a hall of at least 4 x 4 cells gets a FrontRoomsFurniturePile when it exists.")] float pileChance = .35f;

    public FrontRoomsMapCache Cache { get; private set; }
    public Transform Player => player;
    public int ShiftedChunks { get; private set; }
    public int KeysHeld => keysHeld.Count;
    public int Seed => settings.seed;
    public int BuiltChunkCount => built.Count;
    public int BuildRadius => buildRadius;
    public Color FogColor => fogColor;
    public float SightDistance => standalone ? fogEnd + 2f : buildRadius * MapGrid.ChunkSize - 2f;

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
    readonly Dictionary<Collider, Door> doorByCollider = new Dictionary<Collider, Door>();
    readonly Dictionary<long, Door> doorByEdge = new Dictionary<long, Door>();
    readonly Dictionary<Collider, Window> windowByCollider = new Dictionary<Collider, Window>();
    readonly List<GridCoord> scratch = new List<GridCoord>();
    readonly List<Door> movingDoors = new List<Door>();
    Transform player;
    MaterialPropertyBlock block;
    ThemeMaterials level0, office;
    Material trim, doorLeaf, glass, keyGlow;
    int savedPixelLights = -1;
    bool begun;

    static bool dressersResolved;
    static MethodInfo officeDress, pileBuild;

    void Awake()
    {
        if (randomSeedOnPlay && standalone) settings.seed = UnityEngine.Random.Range(int.MinValue, int.MaxValue);
        Cache = new FrontRoomsMapCache(settings);
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
    public static FrontRoomsMapWorld CreateEmbedded(Transform parent, MapSettings settings, int buildRadius, bool doorsNeedKeys)
    {
        var go = new GameObject("Level 0 map");
        go.SetActive(false);
        go.transform.SetParent(parent, false);
        var world = go.AddComponent<FrontRoomsMapWorld>();
        world.settings = (settings ?? new MapSettings()).Clone();
        world.standalone = false;
        world.buildRadius = Mathf.Max(1, buildRadius);
        world.doorsNeedKeys = doorsNeedKeys;
        world.lightRadius = 16f;
        // Awake runs here, with the fields above already set.
        go.SetActive(true);
        return world;
    }

    /// <summary>Build everything around the player at once, then stream from Update.</summary>
    public void Begin(Transform playerTransform)
    {
        player = playerTransform;
        begun = true;
        Stream(ChunkOf(player.position), int.MaxValue);
        TickFixtures(0f);
    }

    void OnDestroy()
    {
        if (savedPixelLights >= 0) QualitySettings.pixelLightCount = savedPixelLights;
    }

    /// <summary>
    /// Edit-mode build of the chunks around the spawn, used for captures.
    /// Returns the eye position. The caller restores render settings.
    /// </summary>
    public Vector3 BuildForCapture()
    {
        Cache = new FrontRoomsMapCache(settings);
        block = new MaterialPropertyBlock();
        BuildMaterials();
        ApplyRenderSettings();
        var eye = new GameObject("CAPTURE / eye").transform;
        eye.SetParent(transform, false);
        eye.localPosition = SpawnPoint();
        Begin(eye);
        return transform.TransformPoint(SpawnPoint() + Vector3.up * 1.62f);
    }

    static void Kill(UnityEngine.Object target)
    {
        if (target == null) return;
        if (Application.isPlaying) Destroy(target); else DestroyImmediate(target);
    }

    void ApplyRenderSettings()
    {
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogStartDistance = fogStart;
        RenderSettings.fogEndDistance = fogEnd;
        RenderSettings.fogColor = fogColor;
        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = ambientColor;
        RenderSettings.skybox = null;
        savedPixelLights = QualitySettings.pixelLightCount;
        QualitySettings.pixelLightCount = 8;
    }

    Vector3 SpawnPoint()
    {
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

    public bool HasKeyFor(GridCoord zone) => keysHeld.Contains(zone);

    void Update()
    {
        if (!begun || player == null) return;
        Stream(ChunkOf(player.position), chunksPerFrame);
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
        foreach (var c in chunk.root.GetComponentsInChildren<Collider>(true)) windowByCollider.Remove(c);
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

        const int blocks = n / BlockCells;
        var builders = new Dictionary<Material, MeshBuilder>[blocks * blocks];
        for (var b = 0; b < builders.Length; b++) builders[b] = new Dictionary<Material, MeshBuilder>();
        MeshBuilder Get(int blockIndex, Material material)
        {
            if (!builders[blockIndex].TryGetValue(material, out var builder)) builders[blockIndex][material] = builder = new MeshBuilder();
            return builder;
        }
        var collision = new MeshBuilder();
        int BlockOf(int i, int j) => i / BlockCells + j / BlockCells * blocks;

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
            var b = BlockOf(i, j);
            var cellCenter = new Vector3((i + .5f) * cs, 0f, (j + .5f) * cs);
            Solid(b, theme.floor, cellCenter + Vector3.down * .1f, new Vector3(cs, .2f, cs), CarpetRepeat);
            Solid(b, theme.ceiling, cellCenter + Vector3.up * (height + .08f), new Vector3(cs, .16f, cs), CeilingRepeat);

            // East and north edges of every cell. Chunk borders on the east and
            // north belong to this chunk; west and south ones to the neighbour.
            var east = new GridCoord(cell.x + 1, cell.y);
            var north = new GridCoord(cell.x, cell.y + 1);
            var eastZone = Cache.ZoneOf(east);
            var northZone = Cache.ZoneOf(north);
            BuildEdge(chunk, data.east[index], cell, east, new Vector3((i + 1) * cs, 0f, j * cs), Vector3.forward,
                Mathf.Max(height, MapGrid.CeilingHeight(eastZone.height)), theme.wall, Theme(eastZone.theme).wall, b, Get, Solid, origin);
            BuildEdge(chunk, data.north[index], cell, north, new Vector3(i * cs, 0f, (j + 1) * cs), Vector3.right,
                Mathf.Max(height, MapGrid.CeilingHeight(northZone.height)), theme.wall, Theme(northZone.theme).wall, b, Get, Solid, origin);

            if (data.pillar[i + j * (n + 1)])
                Solid(b, theme.wall, new Vector3(i * cs, height * .5f, j * cs), new Vector3(.5f, height, .5f), WallpaperRepeat);

            BuildFixture(chunk, cell, cellCenter, height, theme);
        }

        for (var b = 0; b < builders.Length; b++)
        {
            if (builders[b].Count == 0) continue;
            var go = new GameObject("Block " + b);
            go.transform.SetParent(chunk.root.transform, false);
            foreach (var pair in builders[b]) AddRenderer(go, pair.Key, pair.Value);
        }
        var col = new GameObject("Collision");
        col.transform.SetParent(chunk.root.transform, false);
        col.AddComponent<MeshCollider>().sharedMesh = collision.ToMesh("Chunk collision " + coord);

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
        Furnish(chunk, data);
        built[coord] = chunk;
    }

    void AddRenderer(GameObject parent, Material material, MeshBuilder builder)
    {
        if (builder.vertices.Count == 0 || material == null) return;
        var go = new GameObject(material.name);
        go.transform.SetParent(parent.transform, false);
        go.AddComponent<MeshFilter>().sharedMesh = builder.ToMesh(parent.name + " " + material.name);
        var r = go.AddComponent<MeshRenderer>();
        r.sharedMaterial = material;
        r.shadowCastingMode = ShadowCastingMode.On;
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

        var edgeHash = MapHash.Hash(Cache.Generator.Seed, a.x * 2 + (along.x > .5f ? 1 : 0), a.y, 97);
        float width, c, openingTop, sill = 0f;
        if (kind == EdgeKind.Arch)
        {
            width = 1.1f + .7f * MapHash.Unit(edgeHash);
            var margin = .2f + width * .5f;
            c = Mathf.Lerp(margin, length - margin, MapHash.Unit(MapHash.Hash((int)edgeHash, 3, 7, 11)));
            openingTop = Mathf.Min(2.2f, height - .2f);
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
        var frame = .07f;
        var jambDepth = WallThickness + .04f;
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
            leaf.transform.localPosition = new Vector3(0f, (DoorHeight - .02f) * .5f, width * .5f);
            leaf.transform.localScale = new Vector3(.05f, DoorHeight - .02f, width - .02f);
            leaf.GetComponent<Renderer>().sharedMaterial = doorLeaf;
            var door = new Door { hinge = hinge, closed = hinge.localRotation, leaf = leaf.GetComponent<Collider>(), a = a, b = b, edge = edge, position = openingCenter };
            if (brokenDoors.Contains(edge)) { door.broken = door.open = true; }
            else if (openDoors.Contains(edge)) door.open = true;
            if (door.open)
            {
                door.progress = 1f;
                hinge.localRotation = door.closed * Quaternion.Euler(0f, -95f, 0f);
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
            pane.transform.localScale = Abs(along * width + across * .03f + Vector3.up * (openingTop - sill));
            pane.GetComponent<Renderer>().sharedMaterial = glass;
            var window = new Window { pane = pane, edge = edge, position = openingCenter };
            chunk.windows.Add(window);
            windowByCollider[pane.GetComponent<Collider>()] = window;
        }
    }

    static Vector3 Abs(Vector3 v) => new Vector3(Mathf.Abs(v.x), Mathf.Abs(v.y), Mathf.Abs(v.z));

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
    public void BreakDoor(Door door)
    {
        if (door == null) return;
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
        SetDoor(door, true);
        return true;
    }

    // ---------- Fixtures: each lamp keeps its own state ----------

    void BuildFixture(BuiltChunk chunk, GridCoord cell, Vector3 localCenter, float height, ThemeMaterials theme)
    {
        var seed = Cache.Generator.Seed;
        var fixture = new Fixture { rng = MapHash.Hash(seed, cell.x, cell.y, 211) | 1u };
        var root = new GameObject("Fixture " + cell);
        root.transform.SetParent(chunk.root.transform, false);
        root.transform.localPosition = localCenter + Vector3.up * height;
        var panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
        panel.name = "Lens";
        Kill(panel.GetComponent<Collider>());
        panel.transform.SetParent(root.transform, false);
        panel.transform.localPosition = new Vector3(0f, -.02f, 0f);
        panel.transform.localScale = new Vector3(1.2f, .025f, .6f);
        var pr = panel.GetComponent<Renderer>();
        pr.sharedMaterial = theme.lens;
        pr.shadowCastingMode = ShadowCastingMode.Off;
        fixture.panel = pr;
        fixture.emission = theme.lens.HasProperty("_EmissionColor") ? theme.lens.GetColor("_EmissionColor") : Color.black;

        // A troffer only throws light downward: a wide spot at the lens, as
        // in the room stream, so the lit lens reads against the ceiling.
        var lightGo = new GameObject("Light");
        lightGo.transform.SetParent(root.transform, false);
        lightGo.transform.localPosition = new Vector3(0f, -.06f, 0f);
        lightGo.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
        var light = lightGo.AddComponent<Light>();
        light.type = LightType.Spot;
        light.spotAngle = 162f;
        light.innerSpotAngle = 96f;
        light.color = new Color(1f, .93f, .78f);
        light.range = height > 4f ? 10f : height < 2.6f ? 5.5f : 6.5f;
        light.shadows = LightShadows.None;
        fixture.baseIntensity = theme.lampIntensity * (height > 4f ? 1.8f : 1f);
        fixture.light = light;

        // Lamp temperament, rolled once per lamp from the seed and its cell:
        // 0 steady, 1 stutters now and then, 2 failing, 3 dead with rare blinks, 4 dim.
        var roll = Rand(ref fixture.rng);
        fixture.mode = roll < .62f ? 0 : roll < .82f ? 1 : roll < .92f ? 2 : roll < .97f ? 3 : 4;
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
            if (kit != null && officeDress == null)
                officeDress = kit.GetMethod("Dress", BindingFlags.Public | BindingFlags.Static, null,
                    new[] { typeof(Transform), typeof(Rect), typeof(float), typeof(int), typeof(Rect[]) }, null);
            var pile = assembly.GetType("FrontRoomsFurniturePile");
            if (pile != null && pileBuild == null)
                pileBuild = pile.GetMethod("Build", BindingFlags.Public | BindingFlags.Static, null,
                    new[] { typeof(Transform), typeof(Vector3), typeof(float), typeof(float), typeof(int) }, null);
        }
    }

    /// <summary>
    /// Office-zone rooms get an office layout; large halls sometimes get a
    /// furniture pile. Rooms that overlap an earlier one are skipped. Cells
    /// that lead out of the room are kept clear.
    /// </summary>
    void Furnish(BuiltChunk chunk, MapChunk data)
    {
        ResolveDressers();
        if (officeDress == null && pileBuild == null) return;
        var cs = MapGrid.CellSize;
        var seed = Cache.Generator.Seed;
        var taken = new List<CellRect>();
        for (var r = 0; r < data.rooms.Length; r++)
        {
            var room = data.rooms[r];
            var overlaps = false;
            foreach (var other in taken) if (room.Overlaps(other)) { overlaps = true; break; }
            if (overlaps) continue;
            taken.Add(room);
            var first = data.Cell(room.x, room.y);
            var zone = Cache.ZoneOf(first);
            var sameZone = true;
            for (var y = room.y; y < room.y + room.h && sameZone; y++)
            for (var x = room.x; x < room.x + room.w && sameZone; x++)
                if (Cache.ZoneOf(data.Cell(x, y)).id != zone.id) sameZone = false;
            if (!sameZone) continue;
            var height = MapGrid.CeilingHeight(zone.height);
            var roomSeed = (int)MapHash.Hash(seed, data.coord.x * 16 + r, data.coord.y, 307, data.revision);
            try
            {
                if (zone.theme == ZoneTheme.Office && dressOffices && officeDress != null)
                {
                    var floor = new Rect(room.x * cs, room.y * cs, room.w * cs, room.h * cs);
                    officeDress.Invoke(null, new object[] { chunk.root.transform, floor, height, roomSeed, KeepClear(data, room) });
                }
                else if (pileBuild != null && Mathf.Min(room.w, room.h) >= 4 && MapHash.Unit((uint)roomSeed) < (zone.height == ZoneHeight.Tall ? Mathf.Max(pileChance, .6f) : pileChance))
                {
                    var center = new Vector3((room.x + room.w * .5f) * cs, 0f, (room.y + room.h * .5f) * cs);
                    var radius = Mathf.Min(3.2f, Mathf.Min(room.w, room.h) * cs * .22f);
                    pileBuild.Invoke(null, new object[] { chunk.root.transform, center, radius, height, roomSeed });
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[FrontRoomsMap] Furnishing room " + r + " of chunk " + data.coord + " failed: " + (e.InnerException ?? e).Message);
            }
        }
    }

    /// <summary>Room cells with an opening to the outside stay clear of furniture.</summary>
    Rect[] KeepClear(MapChunk data, CellRect room)
    {
        var cs = MapGrid.CellSize;
        var clear = new List<Rect>();
        for (var y = room.y; y < room.y + room.h; y++)
        for (var x = room.x; x < room.x + room.w; x++)
        {
            var cell = data.Cell(x, y);
            var opens = false;
            foreach (var d in new[] { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) })
            {
                var lx = x + d.x;
                var ly = y + d.y;
                if (room.Contains(lx, ly)) continue;
                if (MapGrid.Passable(Cache.Edge(cell, cell + d))) { opens = true; break; }
            }
            if (opens) clear.Add(new Rect(x * cs, y * cs, cs, cs));
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
        SetDoor(door, !door.open);
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

    void TickDoors(float dt)
    {
        for (var i = movingDoors.Count - 1; i >= 0; i--)
        {
            var door = movingDoors[i];
            if (door.hinge == null) { movingDoors.RemoveAt(i); continue; }
            var speed = door.broken ? .18f : .55f;
            door.progress = Mathf.MoveTowards(door.progress, door.open ? 1f : 0f, dt / speed);
            var e = door.progress * door.progress * (3f - 2f * door.progress);
            door.hinge.localRotation = door.closed * Quaternion.Euler(0f, -95f * e, 0f);
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
            lampIntensity = 1.6f,
        };
        var officeLens = FrontRoomsSurfaces.OfficeLouver;
        office = new ThemeMaterials
        {
            wall = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Wall),
            floor = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Floor),
            ceiling = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Ceiling),
            lens = officeLens != null && officeLens.HasProperty("_EmissionColor") ? officeLens : level0Lens,
            lampIntensity = 1.9f,
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
