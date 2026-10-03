using System;
using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// The Level Designer's live preview (Assets/Scenes/FrontRoomsLevelDesigner.unity):
/// it builds the real game map around one room module, with the same
/// builder, lamps, kits and look as the game, and rebuilds whenever the
/// module changes. In Play only the room's chunk is rebuilt and the walker
/// stays where it stands (RebuildLive); a new size, height, theme or seed
/// rebuilds everything and starts it at the entrance again.
///
/// The module is stamped into chunk (0, 0), centred, in a maze whose zones
/// all take the module's height and theme, so the map's own rules (columns,
/// dressing, lamps) apply exactly as they will in the game. Its props carry
/// a FrontRoomsModulePropTag, and ModuleToWorld / WorldToModule convert
/// between module metres and the scene, so the Level Designer's Scene view
/// tools can write edits back to the module.
/// </summary>
[ExecuteAlways]
public sealed class FrontRoomsModulePreview : MonoBehaviour
{
    [Tooltip("The room module to preview. Edit it in the Inspector; the preview follows.")]
    public FrontRoomsRoomModule module;
    [Tooltip("Generation and look. Empty: the project's level profile. The preview overrides zone heights and theme to match the module.")]
    public FrontRoomsLevelProfile profile;
    [Tooltip("Seed of the maze around the room, the lamps' temperaments and the kits' rolls.")]
    public int seed = 1;
    [Range(0, 3), Tooltip("Quarter turns clockwise, to check the room as the generator may place it.")]
    public int rotation;
    [Tooltip("Camera at eye height in the room's entrance, for the Game view.")]
    public Camera eye;

    FrontRoomsMapWorld world;
    FrontRoomsLevelProfile previewProfile;
    bool dirty = true;

    /// <summary>Raised before a rebuild throws the old map away (the Scene view tools note which props were selected) and after the new one is built.</summary>
    public static event Action<FrontRoomsModulePreview> Rebuilding, Rebuilt;

    /// <summary>The map world currently built, or null.</summary>
    public FrontRoomsMapWorld World => world;

    /// <summary>A rebuild is queued for the next editor tick (MarkDirty) and has not run yet.</summary>
    public bool RebuildQueued => dirty;

    /// <summary>The module data the current map was stamped with (turned), or null. The props it placed carry this very object in their tag.</summary>
    public RoomModuleData Stamped { get; private set; }

    int Turns => ((rotation % 4) + 4) % 4;

    /// <summary>Where the module sits: chunk (0, 0), centred.</summary>
    public static void Placement(RoomModuleData module, out int x, out int y) => Placement(module.width, module.depth, out x, out y);

    static void Placement(int width, int depth, out int x, out int y)
    {
        x = (MapGrid.ChunkCells - width) / 2;
        y = (MapGrid.ChunkCells - depth) / 2;
    }

    // ---------- Module space <-> scene (the module must be set) ----------

    /// <summary>
    /// A point in module metres (x, z from the south-west corner of the
    /// module as authored, as props store it) to world space, through the
    /// stamp's turn and placement. A clockwise quarter turn maps (x, z) to
    /// (z, W - x), W the width before the turn, as RoomModuleData.Rotated does.
    /// </summary>
    public Vector3 ModuleToWorld(Vector2 moduleXZ, float height = 0f)
    {
        var m = module.data;
        float x = moduleXZ.x, z = moduleXZ.y, w = m.WidthMetres, d = m.DepthMetres;
        for (var t = 0; t < Turns; t++)
        {
            (x, z) = (z, w - x);
            (w, d) = (d, w);
        }
        return transform.TransformPoint(StampOrigin() + new Vector3(x, height, z));
    }

    /// <summary>The inverse of ModuleToWorld on the floor: a world point to module metres (height dropped).</summary>
    public Vector2 WorldToModule(Vector3 world)
    {
        var local = transform.InverseTransformPoint(world) - StampOrigin();
        var m = module.data;
        float x = local.x, z = local.z;
        // The turned footprint: odd turns swap width and depth.
        float w = Turns % 2 == 0 ? m.WidthMetres : m.DepthMetres, d = Turns % 2 == 0 ? m.DepthMetres : m.WidthMetres;
        for (var t = 0; t < Turns; t++)
        {
            // Undo one turn: the frame before it was d wide, so (x, z) came from (d - z, x).
            (x, z) = (d - z, x);
            (w, d) = (d, w);
        }
        return new Vector2(x, z);
    }

    /// <summary>A module prop's yaw as a world rotation: the stamp adds 90 degrees per quarter turn, then the preview's own rotation.</summary>
    public Quaternion ModuleToWorldRotation(float yaw) => transform.rotation * Quaternion.Euler(0f, yaw + 90f * Turns, 0f);

    /// <summary>The module yaw of a world rotation: its heading on the floor (a tilt is ignored), back through the preview and the turns.</summary>
    public float WorldToModuleYaw(Quaternion rotation)
    {
        var forward = Quaternion.Inverse(transform.rotation) * rotation * Vector3.forward;
        return Mathf.Repeat(Mathf.Atan2(forward.x, forward.z) * Mathf.Rad2Deg - 90f * Turns, 360f);
    }

    /// <summary>The floor the room stands on (the preview's own y = 0 plane).</summary>
    public Plane FloorPlane => new Plane(transform.up, transform.position);

    /// <summary>The stamped (turned) module's south-west corner in the preview's local space: chunk (0, 0) starts at its origin.</summary>
    Vector3 StampOrigin()
    {
        var m = module.data;
        var odd = Turns % 2 == 1;
        Placement(odd ? m.depth : m.width, odd ? m.width : m.depth, out var x0, out var y0);
        return new Vector3(x0 * MapGrid.CellSize, 0f, y0 * MapGrid.CellSize);
    }

    void OnEnable()
    {
        FrontRoomsRoomModule.Changed += OnModuleChanged;
        FrontRoomsLevelProfile.Changed += OnProfileChanged;
        MarkDirty();
    }

    void OnDisable()
    {
        FrontRoomsRoomModule.Changed -= OnModuleChanged;
        FrontRoomsLevelProfile.Changed -= OnProfileChanged;
        Clear();
    }

    // Play: the running preview map takes the profile's live numbers. Its world runs on a clone
    // (previewProfile), so the world's own check never sees the asset; the preview keeps its own
    // build radius (1) and its zone and module overrides (ApplyLive does not read the generation).
    void OnProfileChanged(FrontRoomsLevelProfile changed)
    {
        if (!Application.isPlaying || world == null || previewProfile == null || changed == null || changed != profile) return;
        previewProfile.chunksPerFrame = changed.chunksPerFrame;
        previewProfile.shiftAfterSeconds = changed.shiftAfterSeconds;
        previewProfile.lightRadius = changed.lightRadius;
        previewProfile.shadowRadius = changed.shadowRadius;
        previewProfile.doorsNeedKeys = changed.doorsNeedKeys;
        previewProfile.dressOffices = changed.dressOffices;
        previewProfile.pileChance = changed.pileChance;
        previewProfile.tiers = changed.tiers;
        world.ApplyLive(previewProfile);
    }

    void OnValidate() => MarkDirty();

    void OnModuleChanged(FrontRoomsRoomModule changed)
    {
        // In Play only the module's chunk is rebuilt and the walker stays where it stands (RebuildLive).
        if (changed == module) MarkDirty();
    }

    /// <summary>Rebuild on the next editor tick (edits come in bursts while dragging).</summary>
    public void MarkDirty()
    {
        dirty = true;
#if UNITY_EDITOR
        if (!Application.isPlaying)
        {
            UnityEditor.EditorApplication.delayCall -= RebuildIfDirty;
            UnityEditor.EditorApplication.delayCall += RebuildIfDirty;
        }
#endif
    }

    void Update()
    {
        if (Application.isPlaying) RebuildIfDirty();
    }

    void RebuildIfDirty()
    {
        if (this == null || !dirty || !isActiveAndEnabled) return;
        dirty = false;
        if (Application.isPlaying && RebuildLive()) return;
        Rebuild();
    }

    // The seed and profile the current map was built with: either is a new maze or look, so a full rebuild.
    int builtSeed;
    FrontRoomsLevelProfile builtProfile;

    /// <summary>
    /// Play: stamp the edited module into the running map's chunk (0, 0) and
    /// rebuild only that chunk, keeping the walker where it stands (back at the
    /// entrance if the edit put something where it stood). False when the turned
    /// room's size, height or theme, or the seed or profile, changed: that needs a full rebuild.
    /// </summary>
    bool RebuildLive()
    {
        if (world == null || Stamped == null || module == null || module.data == null || seed != builtSeed || profile != builtProfile) return false;
        var data = module.data.Rotated(rotation);
        data.Normalize();
        if (data.width != Stamped.width || data.depth != Stamped.depth || data.height != Stamped.height || data.theme != Stamped.theme) return false;
        Rebuilding?.Invoke(this);
        Placement(data, out var x0, out var y0);
        world.ReplaceModule(new GridCoord(0, 0), data, x0, y0);
        Stamped = data;
        KeepWalker(data, x0, y0);
        Rebuilt?.Invoke(this);
        return true;
    }

    /// <summary>After a live rebuild: if the walker's body now overlaps something (a moved prop, a new inner wall), it goes back to the entrance.</summary>
    void KeepWalker(RoomModuleData data, int x0, int y0)
    {
        var walker = world.Player;
        if (walker == null) return;
        Physics.SyncTransforms();
        var r = ModuleUnits.PlayerRadius;
        var feet = walker.position;
        var blocked = false;
        foreach (var c in Physics.OverlapCapsule(feet + Vector3.up * (r + .05f), feet + Vector3.up * (ModuleUnits.PlayerHeight - r), r, ~0, QueryTriggerInteraction.Ignore))
            if (!c.transform.IsChildOf(walker)) { blocked = true; break; }
        if (!blocked && world.Cache != null)
        {
            // The shell is one non-convex mesh: an overlap only meets its faces, so a body wholly inside a new column is caught here.
            var chunk = world.Cache.Get(new GridCoord(0, 0));
            var local = world.transform.InverseTransformPoint(feet);
            const int n = MapGrid.ChunkCells;
            for (var j = 0; j <= n && !blocked; j++)
            for (var i = 0; i <= n && !blocked; i++)
            {
                var k = i + j * (n + 1);
                if (!chunk.pillar[k]) continue;
                var reach = ((chunk.pillarStyle[k] & MapChunk.ColumnLarge) != 0 ? ModuleUnits.ColumnLarge : ModuleUnits.ColumnSmall) * .5f + r;
                blocked = Mathf.Abs(local.x - i * MapGrid.CellSize) < reach && Mathf.Abs(local.z - j * MapGrid.CellSize) < reach;
            }
        }
        if (!blocked) return;
        Entrance(data, x0, y0, out var spawn, out var look);
        var position = world.transform.TransformPoint(spawn);
        var heading = world.transform.TransformDirection(look - spawn);
        var yaw = heading.sqrMagnitude > 1e-6f ? Mathf.Atan2(heading.x, heading.z) * Mathf.Rad2Deg : walker.eulerAngles.y;
        // The walker keeps its own yaw and look: tell it, or it turns back on the next frame.
        var mover = walker.GetComponent<FrontRoomsMapWalker>();
        if (mover != null) { mover.Teleport(position, yaw); return; }
        var body = walker.GetComponent<CharacterController>();
        if (body != null) body.enabled = false;
        walker.SetPositionAndRotation(position, Quaternion.Euler(0f, yaw, 0f));
        if (body != null) body.enabled = true;
    }

    /// <summary>Throw the old map away and build the module's again.</summary>
    public void Rebuild()
    {
        // Any build consumes a pending one (Open and the captures build at once).
        dirty = false;
        Rebuilding?.Invoke(this);
        Clear();
        if (module == null || module.data == null) return;
        var data = module.data.Rotated(rotation);
        data.Normalize();

        // A copy of the profile whose maze takes the module's height and theme everywhere.
        previewProfile = Instantiate(profile != null ? profile : FrontRoomsLevelProfile.Default);
        previewProfile.hideFlags = HideFlags.DontSave;
        var g = previewProfile.Generation(seed);
        g.lowShare = data.height == ZoneHeight.Low ? 1f : 0f;
        g.standardShare = data.height == ZoneHeight.Standard ? 1f : 0f;
        g.tallShare = data.height == ZoneHeight.Tall ? 1f : 0f;
        g.officeShare = data.theme == ZoneTheme.Office ? 1f : 0f;
        // Only this module: the generator's own modules would put other designer rooms around it.
        g.moduleChance = 0f;
        previewProfile.generation = g;
        previewProfile.buildRadius = 1;

        var go = new GameObject("PREVIEW / map");
        go.SetActive(false);
        go.transform.SetParent(transform, false);
        world = go.AddComponent<FrontRoomsMapWorld>();
        world.Profile = previewProfile;
        // Props carry their module index, so Scene view edits can be written back.
        world.TagModuleProps = true;
        Placement(data, out var x0, out var y0);
        world.PlaceModule(data, new GridCoord(0, 0), x0, y0);
        Stamped = data;
        builtSeed = seed;
        builtProfile = profile;
        Entrance(data, x0, y0, out var spawn, out var look);
        var heading = look - spawn;
        world.OverrideSpawn(spawn, Mathf.Atan2(heading.x, heading.z) * Mathf.Rad2Deg);
        if (Application.isPlaying)
        {
            // Awake builds it standalone, with the walker at the spawn.
            go.SetActive(true);
        }
        else
        {
            go.SetActive(true);
            world.BuildForCapture();
            foreach (var t in go.GetComponentsInChildren<Transform>(true)) t.gameObject.hideFlags = HideFlags.DontSave;
        }
        FrontRoomsPostStack.Ensure(transform);
        if (eye != null)
        {
            // In Play the walker's camera is the Game view.
            eye.enabled = !Application.isPlaying;
            eye.transform.position = transform.TransformPoint(spawn + Vector3.up * ModuleUnits.PlayerEye);
            eye.transform.rotation = Quaternion.LookRotation(transform.TransformDirection(look - spawn), Vector3.up) * Quaternion.Euler(4f, 0f, 0f);
            eye.farClipPlane = world.SightDistance;
            FrontRoomsPostStack.ConfigureCamera(eye);
        }
        Rebuilt?.Invoke(this);
    }

    /// <summary>
    /// A standing spot just inside the room's first opening (south, west,
    /// north, east, in that order), looking at the room's centre; the room's
    /// centre if it has none. Map space.
    /// </summary>
    public static void Entrance(RoomModuleData m, int x0, int y0, out Vector3 spawn, out Vector3 look)
    {
        var cs = MapGrid.CellSize;
        look = new Vector3((x0 + m.width * .5f) * cs, 0f, (y0 + m.depth * .5f) * cs);
        spawn = look;
        // The whole 0.3 m body stays inside the floor kept clear behind the opening (1.08 m from the cell line).
        const float inside = ModuleUnits.EntryClearDepth + ModuleUnits.WallHalf - ModuleUnits.PlayerRadius;
        for (var i = 0; i < m.width; i++)
            if (m.south[i] != ModuleEdge.Wall) { spawn = new Vector3((x0 + i + .5f) * cs, 0f, y0 * cs + inside); break; }
        if (spawn != look) { spawn.y = .05f; return; }
        for (var j = 0; j < m.depth; j++)
            if (m.west[j] != ModuleEdge.Wall) { spawn = new Vector3(x0 * cs + inside, 0f, (y0 + j + .5f) * cs); break; }
        if (spawn != look) { spawn.y = .05f; return; }
        for (var i = 0; i < m.width; i++)
            if (m.north[i] != ModuleEdge.Wall) { spawn = new Vector3((x0 + i + .5f) * cs, 0f, (y0 + m.depth) * cs - inside); break; }
        if (spawn != look) { spawn.y = .05f; return; }
        for (var j = 0; j < m.depth; j++)
            if (m.east[j] != ModuleEdge.Wall) { spawn = new Vector3((x0 + m.width) * cs - inside, 0f, (y0 + j + .5f) * cs); break; }
        spawn.y = .05f;
        if (spawn == new Vector3(look.x, .05f, look.z)) look += Vector3.forward;
    }

    void Clear()
    {
        if (world != null)
        {
            // Play mode: the standalone map spawned its walker at the scene root, not under the map.
            if (Application.isPlaying && world.Player != null && world.Player.GetComponent<FrontRoomsMapWalker>() != null) Destroy(world.Player.gameObject);
            world.Release();
            if (Application.isPlaying) Destroy(world.gameObject); else DestroyImmediate(world.gameObject);
        }
        world = null;
        Stamped = null;
        // Leftovers from a domain reload.
        for (var i = transform.childCount - 1; i >= 0; i--)
        {
            var child = transform.GetChild(i);
            if (child.name != "PREVIEW / map") continue;
            if (Application.isPlaying) Destroy(child.gameObject); else DestroyImmediate(child.gameObject);
        }
        if (previewProfile != null)
        {
            if (Application.isPlaying) Destroy(previewProfile); else DestroyImmediate(previewProfile);
        }
        previewProfile = null;
    }
}
