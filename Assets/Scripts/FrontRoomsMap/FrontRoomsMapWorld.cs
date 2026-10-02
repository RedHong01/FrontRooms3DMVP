using System.Collections.Generic;
using FrontRooms.Map;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Walkable test of the generated map, used only by FrontRoomsMapTest.unity;
/// the main game still runs on FrontRoomsRoomStream. Builds the 3 x 3 chunks
/// around the player as greybox geometry (walls, doorways, doors, windows,
/// ceilings at the zone height, one fluorescent fixture per cell), drops the
/// rest, and gives a chunk a shifted interior when the player comes back to it
/// after being away for at least shiftAfterSeconds. Every fixture runs its own
/// flicker: nothing is triggered per room.
/// </summary>
public sealed class FrontRoomsMapWorld : MonoBehaviour
{
    const float WallThickness = .16f;
    const float BlockCells = 2;
    const float DoorWidth = 1f, DoorHeight = 2.1f;
    const float WindowWidth = 1.4f, WindowSill = .35f, WindowTop = 2.0f;
    const float WallpaperRepeat = 1.2f, CarpetRepeat = 1.5f, CeilingRepeat = 1.2f;

    [SerializeField] MapSettings settings = new MapSettings();
    [SerializeField, Tooltip("Pick a new seed every time Play starts.")] bool randomSeedOnPlay = false;
    [SerializeField, Min(1), Tooltip("Chunks kept built around the player in each direction. 1 = 3 x 3.")] int buildRadius = 1;
    [SerializeField, Tooltip("A chunk the player has been away from for at least this long comes back with a shifted interior.")] float shiftAfterSeconds = 30f;
    [SerializeField, Tooltip("Fixture lights beyond this distance are switched off. The fog ends first.")] float lightRadius = 14f;
    [SerializeField] float fogStart = 4f;
    [SerializeField, Tooltip("Sight ends here. Keep it under the 24 m distance to the first unbuilt chunk.")] float fogEnd = 20f;
    [SerializeField] Color fogColor = new Color(.30f, .28f, .19f);
    [SerializeField] Color ambientColor = new Color(.34f, .32f, .23f);
    [SerializeField, Tooltip("Off: doors open without the zone key, so a test walk never gets stuck. Keys are still collected.")] bool doorsNeedKeys = false;

    public FrontRoomsMapCache Cache { get; private set; }
    public Transform Player => player;
    public int ShiftedChunks { get; private set; }
    public int KeysHeld => keysHeld.Count;
    public int Seed => settings.seed;

    sealed class Fixture
    {
        public Light light;
        public Renderer panel;
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
        public GridCoord a, b;
        public bool open;
        public float progress;
    }

    public sealed class Window
    {
        public GameObject pane;
        public long edge;
        public float hold;
    }

    sealed class BuiltChunk
    {
        public GameObject root;
        public readonly List<Fixture> fixtures = new List<Fixture>();
        public readonly List<Door> doors = new List<Door>();
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
            mesh.RecalculateBounds();
            return mesh;
        }
    }

    readonly Dictionary<GridCoord, BuiltChunk> built = new Dictionary<GridCoord, BuiltChunk>();
    readonly Dictionary<GridCoord, float> droppedAt = new Dictionary<GridCoord, float>();
    readonly HashSet<GridCoord> keysHeld = new HashSet<GridCoord>();
    readonly HashSet<long> brokenWindows = new HashSet<long>();
    readonly Dictionary<Collider, Door> doorByCollider = new Dictionary<Collider, Door>();
    readonly Dictionary<Collider, Window> windowByCollider = new Dictionary<Collider, Window>();
    readonly List<GridCoord> scratch = new List<GridCoord>();
    readonly List<Door> movingDoors = new List<Door>();
    Transform player;
    MaterialPropertyBlock block;
    Material wallpaper, carpet, ceiling, trim, doorLeaf, glass, fixtureOn, keyGlow;
    Color fixtureEmission;
    int savedPixelLights = -1;

    void Awake()
    {
        if (randomSeedOnPlay) settings.seed = Random.Range(int.MinValue, int.MaxValue);
        Cache = new FrontRoomsMapCache(settings);
        block = new MaterialPropertyBlock();
        BuildMaterials();
        ApplyRenderSettings();
        player = FrontRoomsMapWalker.Spawn(this, transform.TransformPoint(SpawnPoint())).transform;
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
        var spawn = SpawnPoint();
        player = new GameObject("CAPTURE / eye").transform;
        player.SetParent(transform, false);
        player.localPosition = spawn;
        Stream(MapGrid.ChunkOf(CellOf(player.position)));
        TickFixtures(0f);
        return transform.TransformPoint(spawn + Vector3.up * 1.62f);
    }

    static void Kill(Object target)
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
        // Each 6 m block of geometry is its own renderer, so eight per-pixel
        // lights cover the fixtures around it.
        savedPixelLights = QualitySettings.pixelLightCount;
        QualitySettings.pixelLightCount = 8;
    }

    public Color FogColor => fogColor;
    public float SightDistance => fogEnd + 2f;

    Vector3 SpawnPoint()
    {
        var mid = MapGrid.ChunkCells / 2;
        return new Vector3((mid + .5f) * MapGrid.CellSize, .05f, (mid + .5f) * MapGrid.CellSize);
    }

    /// <summary>Map cell under a point given in map space (this object's local space).</summary>
    public static GridCoord CellAt(Vector3 mapPosition) =>
        new GridCoord(Mathf.FloorToInt(mapPosition.x / MapGrid.CellSize), Mathf.FloorToInt(mapPosition.z / MapGrid.CellSize));

    /// <summary>Map cell under a world-space point. The map can sit anywhere: captures build it far from the main scene.</summary>
    public GridCoord CellOf(Vector3 worldPosition) => CellAt(transform.InverseTransformPoint(worldPosition));

    void Update()
    {
        if (player == null) return;
        Stream(MapGrid.ChunkOf(CellOf(player.position)));
        TickFixtures(Time.deltaTime);
        TickDoors(Time.deltaTime);
        CollectKeys();
    }

    void Stream(GridCoord center)
    {
        scratch.Clear();
        foreach (var coord in built.Keys)
            if (Mathf.Abs(coord.x - center.x) > buildRadius || Mathf.Abs(coord.y - center.y) > buildRadius) scratch.Add(coord);
        foreach (var coord in scratch) Drop(coord);
        for (var dy = -buildRadius; dy <= buildRadius; dy++)
        for (var dx = -buildRadius; dx <= buildRadius; dx++)
        {
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
        }
    }

    void Drop(GridCoord coord)
    {
        if (!built.TryGetValue(coord, out var chunk)) return;
        foreach (var door in chunk.doors) movingDoors.Remove(door);
        foreach (var c in chunk.root.GetComponentsInChildren<Collider>(true))
        {
            doorByCollider.Remove(c);
            windowByCollider.Remove(c);
        }
        Kill(chunk.root);
        built.Remove(coord);
        droppedAt[coord] = Time.time;
    }

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

        var blocks = n / (int)BlockCells;
        var wallBuilders = new MeshBuilder[blocks * blocks];
        var floorBuilders = new MeshBuilder[blocks * blocks];
        var ceilingBuilders = new MeshBuilder[blocks * blocks];
        var trimBuilders = new MeshBuilder[blocks * blocks];
        for (var b = 0; b < wallBuilders.Length; b++)
        {
            wallBuilders[b] = new MeshBuilder();
            floorBuilders[b] = new MeshBuilder();
            ceilingBuilders[b] = new MeshBuilder();
            trimBuilders[b] = new MeshBuilder();
        }
        var collision = new MeshBuilder();
        int BlockOf(int i, int j) => (i / (int)BlockCells) + (j / (int)BlockCells) * blocks;

        void Solid(MeshBuilder target, Vector3 center, Vector3 size, float repeat)
        {
            target.Box(center, size, origin, repeat);
            collision.Box(center, size, origin, 1f);
        }

        // Floors: one slab per block.
        for (var by = 0; by < blocks; by++)
        for (var bx = 0; bx < blocks; bx++)
        {
            var side = BlockCells * cs;
            Solid(floorBuilders[bx + by * blocks], new Vector3((bx + .5f) * side, -.1f, (by + .5f) * side), new Vector3(side, .2f, side), CarpetRepeat);
        }

        for (var j = 0; j < n; j++)
        for (var i = 0; i < n; i++)
        {
            var index = MapGrid.LocalIndex(i, j);
            var cell = data.Cell(i, j);
            var height = MapGrid.CeilingHeight(data.height[index]);
            var b = BlockOf(i, j);
            var cellCenter = new Vector3((i + .5f) * cs, 0f, (j + .5f) * cs);
            Solid(ceilingBuilders[b], cellCenter + Vector3.up * (height + .08f), new Vector3(cs, .16f, cs), CeilingRepeat);

            // East and north edges of every cell. Chunk borders on the east and
            // north belong to this chunk; west and south ones to the neighbour.
            var east = new GridCoord(cell.x + 1, cell.y);
            var north = new GridCoord(cell.x, cell.y + 1);
            BuildEdge(chunk, data.east[index], cell, east, new Vector3((i + 1) * cs, 0f, j * cs), Vector3.forward,
                Mathf.Max(height, MapGrid.CeilingHeight(Cache.ZoneOf(east).height)), wallBuilders[b], trimBuilders[b], Solid, origin);
            BuildEdge(chunk, data.north[index], cell, north, new Vector3(i * cs, 0f, (j + 1) * cs), Vector3.right,
                Mathf.Max(height, MapGrid.CeilingHeight(Cache.ZoneOf(north).height)), wallBuilders[b], trimBuilders[b], Solid, origin);

            if (data.pillar[i + j * (n + 1)])
                Solid(wallBuilders[b], new Vector3(i * cs, height * .5f, j * cs), new Vector3(.5f, height, .5f), WallpaperRepeat);

            BuildFixture(chunk, cell, cellCenter, height);
        }

        for (var b = 0; b < wallBuilders.Length; b++)
        {
            var go = new GameObject("Block " + b);
            go.transform.SetParent(chunk.root.transform, false);
            AddRenderer(go, "walls", wallBuilders[b], wallpaper);
            AddRenderer(go, "carpet", floorBuilders[b], carpet);
            AddRenderer(go, "ceiling", ceilingBuilders[b], ceiling);
            AddRenderer(go, "trim", trimBuilders[b], trim);
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
        built[coord] = chunk;
    }

    void AddRenderer(GameObject parent, string name, MeshBuilder builder, Material material)
    {
        if (builder.vertices.Count == 0) return;
        var go = new GameObject(name);
        go.transform.SetParent(parent.transform, false);
        go.AddComponent<MeshFilter>().sharedMesh = builder.ToMesh(parent.name + " " + name);
        var r = go.AddComponent<MeshRenderer>();
        r.sharedMaterial = material;
        r.shadowCastingMode = ShadowCastingMode.Off;
    }

    delegate void SolidFn(MeshBuilder target, Vector3 center, Vector3 size, float repeat);

    /// <summary>
    /// One 3 m edge, starting at <paramref name="start"/> and running along
    /// <paramref name="along"/>. Doorway width and position come from the
    /// edge's hash, so no two doorways line up.
    /// </summary>
    void BuildEdge(BuiltChunk chunk, EdgeKind kind, GridCoord a, GridCoord b, Vector3 start, Vector3 along, float height,
        MeshBuilder walls, MeshBuilder trims, SolidFn solid, Vector3 origin)
    {
        if (kind == EdgeKind.Open) return;
        var length = MapGrid.CellSize;
        var across = new Vector3(along.z, 0f, along.x);
        void Piece(float from, float to, float bottom, float top, bool extendStart, bool extendEnd)
        {
            if (from > 0f) extendStart = false;
            if (to < length) extendEnd = false;
            var f = from - (extendStart ? WallThickness * .5f : 0f);
            var t = to + (extendEnd ? WallThickness * .5f : 0f);
            if (t - f < .05f || top - bottom < .05f) return;
            var center = start + along * ((f + t) * .5f) + Vector3.up * ((bottom + top) * .5f);
            var size = along * (t - f) + across * WallThickness + Vector3.up * (top - bottom);
            solid(walls, center, new Vector3(Mathf.Abs(size.x), size.y, Mathf.Abs(size.z)), WallpaperRepeat);
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
        var frame = .07f;
        var jambDepth = WallThickness + .04f;
        foreach (var s in new[] { -1f, 1f })
        {
            var jc = start + along * (c + s * (width * .5f + frame * .5f)) + Vector3.up * ((sill + openingTop) * .5f);
            var js = along * frame + across * jambDepth + Vector3.up * (openingTop - sill);
            trims.Box(jc, new Vector3(Mathf.Abs(js.x), js.y, Mathf.Abs(js.z)), origin, 1f);
        }
        var hc = start + along * c + Vector3.up * (openingTop + frame * .5f);
        var hs = along * (width + frame * 2f) + across * jambDepth + Vector3.up * frame;
        trims.Box(hc, new Vector3(Mathf.Abs(hs.x), hs.y, Mathf.Abs(hs.z)), origin, 1f);

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
            var door = new Door { hinge = hinge, closed = hinge.localRotation, a = a, b = b };
            chunk.doors.Add(door);
            doorByCollider[leaf.GetComponent<Collider>()] = door;
        }
        else
        {
            var edge = EdgeId(a, b);
            if (brokenWindows.Contains(edge)) return;
            var pane = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pane.name = "Window pane " + a + "-" + b;
            pane.transform.SetParent(chunk.root.transform, false);
            pane.transform.localPosition = start + along * c + Vector3.up * ((sill + openingTop) * .5f);
            var ps = along * width + across * .03f + Vector3.up * (openingTop - sill);
            pane.transform.localScale = new Vector3(Mathf.Abs(ps.x), ps.y, Mathf.Abs(ps.z));
            pane.GetComponent<Renderer>().sharedMaterial = glass;
            windowByCollider[pane.GetComponent<Collider>()] = new Window { pane = pane, edge = edge };
        }
    }

    static long EdgeId(GridCoord a, GridCoord b)
    {
        if (b.x < a.x || b.y < a.y) { var t = a; a = b; b = t; }
        var dir = b.x > a.x ? 1L : 0L;
        return ((long)a.x << 33) ^ ((long)(a.y & 0x7fffffff) << 1) ^ dir;
    }

    // ---------- Fixtures: each lamp keeps its own state ----------

    void BuildFixture(BuiltChunk chunk, GridCoord cell, Vector3 localCenter, float height)
    {
        var seed = Cache.Generator.Seed;
        var fixture = new Fixture { rng = MapHash.Hash(seed, cell.x, cell.y, 211) | 1u };
        var root = new GameObject("Fixture " + cell);
        root.transform.SetParent(chunk.root.transform, false);
        root.transform.localPosition = localCenter + Vector3.up * height;
        var panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
        panel.name = "Diffuser";
        Kill(panel.GetComponent<Collider>());
        panel.transform.SetParent(root.transform, false);
        panel.transform.localPosition = new Vector3(0f, -.025f, 0f);
        panel.transform.localScale = new Vector3(1.2f, .03f, .6f);
        var pr = panel.GetComponent<Renderer>();
        pr.sharedMaterial = fixtureOn;
        pr.shadowCastingMode = ShadowCastingMode.Off;
        fixture.panel = pr;

        var lightGo = new GameObject("Light");
        lightGo.transform.SetParent(root.transform, false);
        lightGo.transform.localPosition = new Vector3(0f, -.3f, 0f);
        var light = lightGo.AddComponent<Light>();
        light.type = LightType.Point;
        light.color = new Color(1f, .93f, .76f);
        light.range = height > 4f ? 8.5f : height < 2.6f ? 4.8f : 5.6f;
        light.shadows = LightShadows.None;
        light.renderMode = LightRenderMode.Auto;
        fixture.baseIntensity = height > 4f ? 1.35f : .9f;
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
            block.SetColor("_EmissionColor", fixtureEmission * Mathf.Max(.04f, f.level));
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

    // ---------- Interaction ----------

    public string Describe(Collider c, out bool holdToUse)
    {
        holdToUse = false;
        if (c == null) return null;
        if (doorByCollider.TryGetValue(c, out var door))
        {
            if (door.open) return "E  ·  SHUT DOOR";
            if (HasKeyHere()) return "E  ·  OPEN DOOR";
            return doorsNeedKeys ? "LOCKED  ·  NEEDS THIS ZONE'S KEY" : "E  ·  OPEN DOOR  (NO KEY · TEST)";
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
        if (c == null || !doorByCollider.TryGetValue(c, out var door)) return;
        if (!door.open && doorsNeedKeys && !HasKeyHere()) return;
        door.open = !door.open;
        if (!movingDoors.Contains(door)) movingDoors.Add(door);
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
        return true;
    }

    public void ReleaseHold(Collider c)
    {
        if (c != null && windowByCollider.TryGetValue(c, out var window)) window.hold = 0f;
    }

    bool HasKeyHere() => keysHeld.Contains(Cache.ZoneOf(CellOf(player.position)).id);

    void TickDoors(float dt)
    {
        for (var i = movingDoors.Count - 1; i >= 0; i--)
        {
            var door = movingDoors[i];
            if (door.hinge == null) { movingDoors.RemoveAt(i); continue; }
            door.progress = Mathf.MoveTowards(door.progress, door.open ? 1f : 0f, dt / .55f);
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
            }
    }

    // ---------- Materials ----------

    /// <summary>
    /// The map test uses the game's URP surfaces (Resources/Surfaces): the
    /// Level 0 chevron paper, loop-pile carpet and 2'x4' ceiling grid, all
    /// projected in world metres by FrontRooms/Surface, so the test chunks
    /// look like the real level. Run FrontRooms → Rendering → Set up URP,
    /// post and surfaces once if they are missing.
    /// </summary>
    void BuildMaterials()
    {
        fixtureEmission = new Color(1f, .96f, .84f) * 2.6f;
        wallpaper = FrontRoomsSurfaces.Room(RoomRule.Lobby, FrontRoomsSurfaces.Slot.Wall);
        carpet = FrontRoomsSurfaces.Room(RoomRule.Lobby, FrontRoomsSurfaces.Slot.Floor);
        ceiling = FrontRoomsSurfaces.Room(RoomRule.Lobby, FrontRoomsSurfaces.Slot.Ceiling);
        trim = FrontRoomsSurfaces.Lit("Map test / frame", new Color(.55f, .50f, .36f), .2f);
        doorLeaf = FrontRoomsSurfaces.Lit("Map test / door", new Color(.72f, .66f, .50f), .25f);
        fixtureOn = FrontRoomsSurfaces.Lit("Map test / diffuser", new Color(1f, .98f, .92f), .1f, 0f, fixtureEmission);
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
