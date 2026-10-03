using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// The Level Designer's live preview (Assets/Scenes/FrontRoomsLevelDesigner.unity):
/// it builds the real game map around one room module, with the same
/// builder, lamps, kits and look as the game, and rebuilds whenever the
/// module changes. In Play mode the walker spawns inside the room.
///
/// The module is stamped into chunk (0, 0), centred, in a maze whose zones
/// all take the module's height and theme, so the map's own rules (columns,
/// dressing, lamps) apply exactly as they will in the game.
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

    /// <summary>The map world currently built, or null.</summary>
    public FrontRoomsMapWorld World => world;

    /// <summary>Where the module sits: chunk (0, 0), centred.</summary>
    public static void Placement(RoomModuleData module, out int x, out int y)
    {
        x = (MapGrid.ChunkCells - module.width) / 2;
        y = (MapGrid.ChunkCells - module.depth) / 2;
    }

    void OnEnable()
    {
        FrontRoomsRoomModule.Changed += OnModuleChanged;
        MarkDirty();
    }

    void OnDisable()
    {
        FrontRoomsRoomModule.Changed -= OnModuleChanged;
        Clear();
    }

    void OnValidate() => MarkDirty();

    void OnModuleChanged(FrontRoomsRoomModule changed)
    {
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
        Rebuild();
    }

    /// <summary>Throw the old map away and build the module's again.</summary>
    public void Rebuild()
    {
        // Any build consumes a pending one (Open and the captures build at once).
        dirty = false;
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
        previewProfile.generation = g;
        previewProfile.buildRadius = 1;

        var go = new GameObject("PREVIEW / map");
        go.SetActive(false);
        go.transform.SetParent(transform, false);
        world = go.AddComponent<FrontRoomsMapWorld>();
        world.Profile = previewProfile;
        Placement(data, out var x0, out var y0);
        world.PlaceModule(data, new GridCoord(0, 0), x0, y0);
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
