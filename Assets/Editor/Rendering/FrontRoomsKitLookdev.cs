using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// Look-dev for the Office kit and the furniture piles, independent of the
/// room stream and the maze. Builds three throwaway rooms and renders fixed
/// shots to Verification/kit_lookdev (nothing is saved to any scene):
///   A  a 12 x 12 m Office room at map size (4 x 4 cells, n·3 − 0.16 clear),
///      with a south doorway and an east opening as keepClear strips, the
///      Office zone grade and FrontRoomsOfficeKit.Dress;
///   B  an empty 18 x 16 m Level 0 hall with a FrontRoomsFurniturePile at its
///      centre (R = min(3.2, 0.22 · min side), the map's rule), seen from the
///      doorway like the film's first room;
///   C  a line-up of every kit model, plus one in-engine close-up per asset.
/// Batch: -executeMethod FrontRoomsKitLookdev.RunBatch [-kitSeed N] [-kitShots a,b|assets]
/// </summary>
public static class FrontRoomsKitLookdev
{
    const float Height = 2.9f;
    const float GridX = .6f;    // the printed ceiling grid (metric module)
    const float GridZ = 1.2f;
    static readonly Vector3 OfficeOrigin = Vector3.zero;
    static readonly Vector3 HallOrigin = new Vector3(40f, 0f, 0f);
    static readonly Vector3 LineupOrigin = new Vector3(80f, 0f, 0f);

    struct Shot { public string name; public Vector3 position; public Vector3 euler; public float fov; }

    [MenuItem("FrontRooms/Rendering/Capture office kit look-dev")]
    public static void Capture() => Run(1, null);

    public static void RunBatch()
    {
        var args = Environment.GetCommandLineArgs();
        var seed = 1;
        string shots = null;
        for (var i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "-kitSeed") int.TryParse(args[i + 1], out seed);
            if (args[i] == "-kitShots") shots = args[i + 1];
        }
        Run(seed, shots);
    }

    static void Run(int seed, string onlyShots)
    {
        // Re-import the kit so slot remaps pick up materials created since.
        if (AssetDatabase.IsValidFolder("Assets/Resources/Props/Models"))
            AssetDatabase.ImportAsset("Assets/Resources/Props/Models", ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate);
        var previous = EditorSceneManager.GetActiveScene();
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, Application.isBatchMode ? NewSceneMode.Single : NewSceneMode.Additive);
        EditorSceneManager.SetActiveScene(scene);
        try
        {
            var root = new GameObject("KIT LOOKDEV").transform;
            FrontRoomsLook.ApplyAmbient();
            FrontRoomsPostStack.Ensure(root);
            var shots = new List<Shot>();

            // ---------------------------------------------------------- A office
            var office = Room(root, "A office", OfficeOrigin, 12f, 12f, RoomRule.Office,
                new[] { new Opening { side = 0, centre = 0f, width = 1.2f }, new Opening { side = 3, centre = 8.1f, width = 1.6f } });
            var floor = new Rect(-6f + .08f, .08f, 12f - .16f, 12f - .16f);
            var keepClear = new[] { new Rect(-.6f, .08f, 1.2f, 1.2f), new Rect(6f - .08f - 1f, 7.3f, 1f, 1.6f) };
            FrontRoomsOfficeKit.Dress(office, floor, Height, seed, keepClear);
            FrontRoomsPostStack.EnsureZoneVolume(office, "Office", new Bounds(new Vector3(0f, Height * .5f, 6f), new Vector3(12f, Height, 12f)), 1.5f);
            shots.Add(new Shot { name = "office_entrance", position = OfficeOrigin + new Vector3(0f, 1.62f, .4f), euler = new Vector3(4f, 0f, 0f), fov = 72f });
            shots.Add(new Shot { name = "office_diagonal", position = OfficeOrigin + new Vector3(-5.3f, 1.62f, .7f), euler = new Vector3(6f, 40f, 0f), fov = 72f });
            shots.Add(new Shot { name = "office_back", position = OfficeOrigin + new Vector3(5.2f, 1.62f, 11.3f), euler = new Vector3(5f, 220f, 0f), fov = 72f });
            shots.Add(new Shot { name = "office_desk", position = OfficeOrigin + new Vector3(-1.5f, 1.5f, 3.2f), euler = new Vector3(20f, -35f, 0f), fov = 60f });

            // ------------------------------------------------------------ B hall
            const float hallW = 18f, hallD = 16f;
            var hall = Room(root, "B hall", HallOrigin, hallW, hallD, RoomRule.Lobby, new[] { new Opening { side = 0, centre = 0f, width = 1.2f } });
            var radius = Mathf.Min(3.2f, .22f * Mathf.Min(hallW, hallD));
            var pile = FrontRoomsFurniturePile.BuildPile(hall, new Vector3(0f, 0f, hallD * .5f), radius, Height, seed, null);
            Debug.Log("[KitLookdev] Dress ok; pile " + (pile != null ? pile.name : "none"));
            shots.Add(new Shot { name = "pile", position = HallOrigin + new Vector3(0f, 1.62f, .5f), euler = new Vector3(2f, 0f, 0f), fov = 72f });
            shots.Add(new Shot { name = "pile_close", position = HallOrigin + new Vector3(-3.6f, 1.5f, 3.4f), euler = new Vector3(4f, 38f, 0f), fov = 60f });
            shots.Add(new Shot { name = "pile_side", position = HallOrigin + new Vector3(6.8f, 1.62f, 12.5f), euler = new Vector3(3f, 245f, 0f), fov = 72f });

            // ----------------------------------------------------------- C lineup
            var lineupRoom = Room(root, "C lineup", LineupOrigin, 20f, 14f, RoomRule.Office, Array.Empty<Opening>());
            var spawned = new List<(string name, Transform t)>();
            var lineupCam = LineUp(lineupRoom, spawned, 20f, 14f);
            if (lineupCam.HasValue)
                shots.Add(new Shot { name = "lineup", position = LineupOrigin + lineupCam.Value, euler = new Vector3(12f, 0f, 0f), fov = 70f });
            foreach (var (assetName, t) in spawned)
            {
                var info = FrontRoomsKitLibrary.GetInfo(assetName);
                if (info == null) continue;
                var centre = t.TransformPoint((info.Min + info.Max) * .5f);
                var r = Mathf.Max(info.Size.magnitude * .5f, .2f);
                var front = t.rotation * Vector3.forward;                 // kit assets face local +Z
                var dir = Quaternion.Euler(0f, -35f, 0f) * front;         // front-left 3/4
                var position = centre + dir * r * 2.6f + Vector3.up * r * .55f;
                shots.Add(new Shot { name = "asset_" + assetName, position = position, euler = Quaternion.LookRotation(centre - position).eulerAngles, fov = 45f });
            }

            Render(shots, onlyShots);
        }
        finally
        {
            if (!Application.isBatchMode)
            {
                EditorSceneManager.CloseScene(scene, true);
                if (previous.IsValid()) EditorSceneManager.SetActiveScene(previous);
            }
        }
    }

    static void Render(List<Shot> shots, string onlyShots)
    {
        var outDir = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "kit_lookdev");
        Directory.CreateDirectory(outDir);
        var cameraObject = new GameObject("KIT LOOKDEV camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.nearClipPlane = .05f;
        camera.farClipPlane = 80f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = Color.black;
        FrontRoomsPostStack.ConfigureCamera(camera);
        var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
        camera.targetTexture = rt;
        var filter = string.IsNullOrEmpty(onlyShots) ? null : new HashSet<string>(onlyShots.Split(','));
        foreach (var shot in shots)
        {
            if (filter != null && !filter.Contains(shot.name) && !(filter.Contains("assets") && shot.name.StartsWith("asset_"))) continue;
            camera.fieldOfView = shot.fov;
            camera.transform.SetPositionAndRotation(shot.position, Quaternion.Euler(shot.euler));
            // Local volumes blend by camera position: render twice so the
            // stack and shadows settle for this pose.
            camera.Render();
            camera.Render();
            Save(rt, Path.Combine(outDir, shot.name + ".png"));
        }
        camera.targetTexture = null;
        rt.Release();
        Debug.Log("[KitLookdev] Wrote shots to " + outDir);
    }

    struct Opening { public int side; public float centre; public float width; } // side 0 S, 1 N, 2 W, 3 E; centre along x (S/N) or z (W/E)

    /// <summary>A walled room of width x depth at origin (south wall on z = 0), troffer grid, profile surfaces.</summary>
    static Transform Room(Transform root, string name, Vector3 origin, float width, float depth, RoomRule rule, Opening[] openings)
    {
        var room = new GameObject(name).transform;
        room.SetParent(root, false);
        room.localPosition = origin;
        var wall = FrontRoomsSurfaces.Room(rule, FrontRoomsSurfaces.Slot.Wall);
        var floorMat = FrontRoomsSurfaces.Room(rule, FrontRoomsSurfaces.Slot.Floor);
        var ceiling = FrontRoomsSurfaces.Room(rule, FrontRoomsSurfaces.Slot.Ceiling);
        Box(room, "floor", new Vector3(0f, -.1f, depth * .5f), new Vector3(width + .4f, .2f, depth + .4f), floorMat);
        Box(room, "ceiling", new Vector3(0f, Height + .1f, depth * .5f), new Vector3(width + .4f, .2f, depth + .4f), ceiling);
        const float t = .16f;
        WallWithGaps(room, wall, new Vector3(-width * .5f, 0f, 0f), Vector3.right, width, t, Gaps(openings, 0, width * .5f), new Vector3(0f, 0f, -t * .5f + .08f));
        WallWithGaps(room, wall, new Vector3(-width * .5f, 0f, depth), Vector3.right, width, t, Gaps(openings, 1, width * .5f), new Vector3(0f, 0f, t * .5f - .08f));
        WallWithGaps(room, wall, new Vector3(-width * .5f, 0f, 0f), Vector3.forward, depth, t, Gaps(openings, 2, 0f), new Vector3(-t * .5f + .08f, 0f, 0f));
        WallWithGaps(room, wall, new Vector3(width * .5f, 0f, 0f), Vector3.forward, depth, t, Gaps(openings, 3, 0f), new Vector3(t * .5f - .08f, 0f, 0f));
        Troffers(room, width, depth, rule == RoomRule.Office ? FrontRoomsSurfaces.OfficeLens : FrontRoomsSurfaces.TrofferLens);
        return room;
    }

    static List<Vector2> Gaps(Opening[] openings, int side, float offset)
    {
        var list = new List<Vector2>();
        foreach (var o in openings) if (o.side == side) list.Add(new Vector2(o.centre + offset - o.width * .5f, o.centre + offset + o.width * .5f));
        list.Sort((a, b) => a.x.CompareTo(b.x));
        return list;
    }

    static void WallWithGaps(Transform room, Material wall, Vector3 start, Vector3 along, float length, float thickness, List<Vector2> gaps, Vector3 inset)
    {
        var cursor = 0f;
        var cove = FrontRoomsSurfaces.CoveBase;
        void Segment(float a, float b, float y0, float y1)
        {
            if (b - a < .01f) return;
            var mid = start + along * ((a + b) * .5f) + inset;
            var size = along.x != 0 ? new Vector3(b - a, y1 - y0, thickness) : new Vector3(thickness, y1 - y0, b - a);
            Box(room, "wall", mid + Vector3.up * ((y0 + y1) * .5f), size, wall);
            if (y0 < .01f)
            {
                var coveSize = along.x != 0 ? new Vector3(b - a, .1f, thickness + .02f) : new Vector3(thickness + .02f, .1f, b - a);
                Box(room, "cove", mid + Vector3.up * .05f, coveSize, cove);
            }
        }
        foreach (var g in gaps)
        {
            Segment(cursor, g.x, 0f, Height);
            Segment(g.x, g.y, 2.1f, Height); // door head
            cursor = g.y;
        }
        Segment(cursor, length, 0f, Height);
    }

    static void Troffers(Transform room, float width, float depth, Material lens)
    {
        var pan = FrontRoomsSurfaces.PaintedMetal;
        var index = 0;
        var half = Mathf.FloorToInt(width * .5f / GridX);
        for (var cx = -half + 2; cx <= half - 2; cx += 4)
        for (var cz = 1; (cz + 1) * GridZ < depth - .5f; cz += 3)
        {
            var fixture = new GameObject("troffer " + index).transform;
            fixture.SetParent(room, false);
            fixture.localPosition = new Vector3((cx + .5f) * GridX, 0f, (cz + .5f) * GridZ);
            Box(fixture, "pan", new Vector3(0f, Height - .015f, 0f), new Vector3(GridX - .012f, .03f, GridZ - .012f), pan);
            Box(fixture, "lens", new Vector3(0f, Height - .033f, 0f), new Vector3(GridX - .06f, .006f, GridZ - .06f), lens);
            var light = new GameObject("light").AddComponent<Light>();
            light.transform.SetParent(fixture, false);
            light.transform.localPosition = new Vector3(0f, Height - .05f, 0f);
            light.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            light.type = LightType.Spot;
            light.spotAngle = 162f;
            light.innerSpotAngle = 96f;
            light.range = 10f;
            light.intensity = 5f;
            light.color = new Color(1f, .96f, .88f);
            light.shadows = index % 3 == 0 ? LightShadows.Soft : LightShadows.None;
            light.shadowStrength = .9f;
            light.shadowNearPlane = .1f;
            index++;
        }
    }

    /// <summary>Every kit model in centred rows; returns the camera spot (room-local).</summary>
    static Vector3? LineUp(Transform room, List<(string name, Transform t)> spawned, float width, float depth)
    {
        var names = new List<string>(FrontRoomsKitLibrary.AllNames());
        if (names.Count == 0) return null;
        const float gap = .45f;
        var maxRow = width - 3f;
        var rows = new List<List<(string name, float half)>> { new List<(string, float)>() };
        var rowWidth = 0f;
        var maxHeight = 0f;
        foreach (var n in names)
        {
            var info = FrontRoomsKitLibrary.GetInfo(n);
            var half = info != null ? info.HalfFootprint.x : .5f;
            if (info != null) maxHeight = Mathf.Max(maxHeight, info.Height);
            if (rowWidth + half * 2 > maxRow && rows[rows.Count - 1].Count > 0) { rows.Add(new List<(string, float)>()); rowWidth = 0f; }
            rows[rows.Count - 1].Add((n, half));
            rowWidth += half * 2 + gap;
        }
        var z = depth - 1.6f;
        foreach (var items in rows)
        {
            var total = -gap;
            foreach (var item in items) total += item.half * 2 + gap;
            var x = -total * .5f;
            foreach (var item in items)
            {
                x += item.half;
                var instance = FrontRoomsKitLibrary.Spawn(item.name, room, new Vector3(x, 0f, z), 180f, null, false);
                if (instance != null) spawned.Add((item.name, instance.transform));
                x += item.half + gap;
            }
            z -= 2.2f;
        }
        return new Vector3(0f, 1.6f, Mathf.Max(.6f, z + 2.2f - 6.5f));
    }

    static GameObject Box(Transform parent, string name, Vector3 position, Vector3 size, Material material)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localScale = size;
        UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
        go.GetComponent<MeshRenderer>().sharedMaterial = material;
        return go;
    }

    static void Save(RenderTexture rt, string path)
    {
        var previous = RenderTexture.active;
        RenderTexture.active = rt;
        var image = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        image.Apply();
        RenderTexture.active = previous;
        File.WriteAllBytes(path, image.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(image);
    }
}
