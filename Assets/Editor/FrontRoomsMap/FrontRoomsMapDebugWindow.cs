using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Top-down view of the generated map, read through the same chunk cache the
/// game will stream from. Scroll to zoom, drag to pan, hover a cell for its
/// zone. "Shift hovered chunk" rebuilds that chunk's interior to preview how a
/// dropped chunk could come back different.
/// </summary>
public sealed class FrontRoomsMapDebugWindow : EditorWindow
{
    static readonly Color Background = new Color(.07f, .07f, .065f);
    static readonly Color LowColor = new Color(.29f, .27f, .18f);
    static readonly Color StandardColor = new Color(.44f, .40f, .26f);
    static readonly Color TallColor = new Color(.63f, .57f, .38f);
    static readonly Color WallColor = new Color(.96f, .95f, .91f);
    static readonly Color DoorColor = new Color(.957f, .875f, .231f);
    static readonly Color WindowColor = new Color(.60f, .78f, .85f);
    static readonly Color ChunkLine = new Color(0f, 0f, 0f, .6f);
    static readonly Color HoverColor = new Color(.957f, .875f, .231f, .35f);

    [SerializeField] FrontRoomsLevelProfile profile;
    [SerializeField] int previewSeed = 20261001;
    [SerializeField] int radius = 5;
    [SerializeField] float cellPixels = 10f;
    [SerializeField] Vector2 pan;
    [SerializeField] bool showChunks = true;
    [SerializeField] bool showSettings;

    FrontRoomsMapCache cache;
    SerializedObject profileObject;
    GridCoord hoverCell;
    bool hasHover;
    string status = "";

    [MenuItem("FrontRooms/Map/Debug map")]
    public static void Open()
    {
        var window = GetWindow<FrontRoomsMapDebugWindow>("FrontRooms map");
        window.minSize = new Vector2(560f, 420f);
    }

    void OnEnable()
    {
        wantsMouseMove = true;
        Undo.undoRedoPerformed += OnUndoRedo;
        Rebuild();
    }

    void OnDisable() => Undo.undoRedoPerformed -= OnUndoRedo;

    void OnUndoRedo()
    {
        Rebuild();
        Repaint();
    }

    /// <summary>The level profile being previewed: the one picked here, else the project's.</summary>
    FrontRoomsLevelProfile Profile
    {
        get
        {
            if (profile == null) profile = FrontRoomsLevelProfiles.Resolve();
            return profile;
        }
    }

    // The preview seed is this window's own; it is never written to the profile.
    void Rebuild() => cache = new FrontRoomsMapCache(Profile.Generation(previewSeed));

    void OnGUI()
    {
        if (cache == null) Rebuild();
        var rebuild = false;
        using (new EditorGUILayout.HorizontalScope(EditorStyles.toolbar))
        {
            GUILayout.Label("Seed", GUILayout.Width(32));
            var seed = EditorGUILayout.DelayedIntField(previewSeed, EditorStyles.toolbarTextField, GUILayout.Width(96));
            if (seed != previewSeed) { previewSeed = seed; rebuild = true; }
            if (GUILayout.Button("New seed", EditorStyles.toolbarButton, GUILayout.Width(70)))
            {
                previewSeed = Random.Range(int.MinValue, int.MaxValue);
                rebuild = true;
            }
            GUILayout.Space(8f);
            GUILayout.Label("Chunks", GUILayout.Width(44));
            radius = EditorGUILayout.IntSlider(radius, 1, 12, GUILayout.Width(170));
            showChunks = GUILayout.Toggle(showChunks, "Chunk grid", EditorStyles.toolbarButton, GUILayout.Width(76));
            showSettings = GUILayout.Toggle(showSettings, "Settings", EditorStyles.toolbarButton, GUILayout.Width(64));
            GUILayout.FlexibleSpace();
            using (new EditorGUI.DisabledScope(!hasHover))
                if (GUILayout.Button("Shift hovered chunk", EditorStyles.toolbarButton, GUILayout.Width(128)))
                    cache.Shift(MapGrid.ChunkOf(hoverCell));
            if (GUILayout.Button("Verify 100 seeds", EditorStyles.toolbarButton, GUILayout.Width(108)))
                status = FrontRoomsMapVerification.Run(false);
        }
        if (showSettings)
        {
            var picked = (FrontRoomsLevelProfile)EditorGUILayout.ObjectField("Level profile", Profile, typeof(FrontRoomsLevelProfile), false);
            if (picked != profile) { profile = picked; profileObject = null; rebuild = true; }
            if (profileObject == null || profileObject.targetObject != Profile) profileObject = new SerializedObject(Profile);
            profileObject.Update();
            EditorGUI.BeginChangeCheck();
            EditorGUILayout.PropertyField(profileObject.FindProperty("generation"), new GUIContent("Generation (edits the profile asset)"), true);
            if (EditorGUI.EndChangeCheck()) { profileObject.ApplyModifiedProperties(); rebuild = true; }
        }
        if (rebuild) Rebuild();

        var rect = GUILayoutUtility.GetRect(10f, 10f, GUILayout.ExpandWidth(true), GUILayout.ExpandHeight(true));
        HandleInput(rect);
        if (Event.current.type == EventType.Repaint) DrawMap(rect);

        EditorGUILayout.LabelField(HoverText(), EditorStyles.miniLabel);
        EditorGUILayout.LabelField("Low · standard · tall zones get lighter.   White wall, gap = arch, yellow = door, blue = window, dot = pillar, K = zone key.", EditorStyles.miniLabel);
        if (!string.IsNullOrEmpty(status)) EditorGUILayout.LabelField(status, EditorStyles.miniBoldLabel);
    }

    void HandleInput(Rect rect)
    {
        var e = Event.current;
        if (!rect.Contains(e.mousePosition) && e.type != EventType.MouseDrag) return;
        switch (e.type)
        {
            case EventType.ScrollWheel:
                cellPixels = Mathf.Clamp(cellPixels * (e.delta.y > 0f ? .9f : 1.1f), 4f, 64f);
                e.Use();
                Repaint();
                break;
            case EventType.MouseDrag:
                pan += e.delta;
                e.Use();
                Repaint();
                break;
            case EventType.MouseMove:
                var local = e.mousePosition - rect.position;
                var center = rect.size * .5f + pan;
                hoverCell = new GridCoord(Mathf.FloorToInt((local.x - center.x) / cellPixels), Mathf.FloorToInt((center.y - local.y) / cellPixels));
                hasHover = true;
                Repaint();
                break;
        }
    }

    void DrawMap(Rect rect)
    {
        EditorGUI.DrawRect(rect, Background);
        GUI.BeginClip(rect);
        var center = rect.size * .5f + pan;
        var s = cellPixels;
        var n = MapGrid.ChunkCells;
        Rect CellRect(GridCoord c) => new Rect(center.x + c.x * s, center.y - (c.y + 1) * s, s, s);

        for (var cy = -radius; cy < radius; cy++)
        for (var cx = -radius; cx < radius; cx++)
        {
            var chunk = cache.Get(new GridCoord(cx, cy));
            for (var j = 0; j < n; j++)
            for (var i = 0; i < n; i++)
            {
                var index = MapGrid.LocalIndex(i, j);
                EditorGUI.DrawRect(CellRect(chunk.Cell(i, j)), ZoneColor(chunk.height[index], chunk.zone[index]));
            }
        }
        if (hasHover) EditorGUI.DrawRect(CellRect(hoverCell), HoverColor);

        var t = Mathf.Max(2f, s * .12f);
        for (var cy = -radius; cy < radius; cy++)
        for (var cx = -radius; cx < radius; cx++)
        {
            var chunk = cache.Get(new GridCoord(cx, cy));
            for (var j = 0; j < n; j++)
            for (var i = 0; i < n; i++)
            {
                var index = MapGrid.LocalIndex(i, j);
                var r = CellRect(chunk.Cell(i, j));
                DrawEdge(chunk.east[index], new Vector2(r.xMax, r.yMin), new Vector2(r.xMax, r.yMax), t);
                DrawEdge(chunk.north[index], new Vector2(r.xMin, r.yMin), new Vector2(r.xMax, r.yMin), t);
                if (i == 0 && cx == -radius) DrawEdge(chunk.west[j], new Vector2(r.xMin, r.yMin), new Vector2(r.xMin, r.yMax), t);
                if (j == 0 && cy == -radius) DrawEdge(chunk.south[i], new Vector2(r.xMin, r.yMax), new Vector2(r.xMax, r.yMax), t);
            }
            var origin = chunk.Origin;
            var p = Mathf.Max(2f, s * .16f);
            for (var j = 0; j <= n; j++)
            for (var i = 0; i <= n; i++)
            {
                if (!chunk.pillar[i + j * (n + 1)]) continue;
                var x = center.x + (origin.x + i) * s;
                var y = center.y - (origin.y + j) * s;
                EditorGUI.DrawRect(new Rect(x - p * .5f, y - p * .5f, p, p), WallColor);
            }
            if (chunk.hasKey)
            {
                var k = CellRect(chunk.keyCell);
                var size = Mathf.Max(5f, s * .38f);
                EditorGUI.DrawRect(new Rect(k.center.x - size * .5f, k.center.y - size * .5f, size, size), DoorColor);
            }
            if (showChunks)
            {
                var c = new Rect(center.x + origin.x * s, center.y - (origin.y + n) * s, n * s, n * s);
                EditorGUI.DrawRect(new Rect(c.xMin, c.yMin, c.width, 1f), ChunkLine);
                EditorGUI.DrawRect(new Rect(c.xMin, c.yMin, 1f, c.height), ChunkLine);
            }
        }
        GUI.EndClip();
    }

    static Color ZoneColor(ZoneHeight height, GridCoord zone)
    {
        var baseColor = height == ZoneHeight.Low ? LowColor : height == ZoneHeight.Tall ? TallColor : StandardColor;
        // A small per-zone shade so neighbouring zones of the same height stay readable.
        var shade = ((zone.x * 92821 + zone.y * 68917) & 7) / 7f - .5f;
        return baseColor * (1f + shade * .12f) + new Color(0f, 0f, 0f, 1f - baseColor.a);
    }

    static void DrawEdge(EdgeKind kind, Vector2 a, Vector2 b, float thickness)
    {
        if (kind == EdgeKind.Open) return;
        if (kind == EdgeKind.Wall) { Segment(a, b, 0f, 1f, thickness, WallColor); return; }
        Segment(a, b, 0f, .3f, thickness, WallColor);
        Segment(a, b, .7f, 1f, thickness, WallColor);
        if (kind == EdgeKind.Door) Segment(a, b, .3f, .7f, thickness * 1.7f, DoorColor);
        else if (kind == EdgeKind.Window) Segment(a, b, .3f, .7f, thickness * 1.7f, WindowColor);
    }

    static void Segment(Vector2 a, Vector2 b, float from, float to, float thickness, Color color)
    {
        var p0 = Vector2.Lerp(a, b, from);
        var p1 = Vector2.Lerp(a, b, to);
        var r = Mathf.Approximately(a.x, b.x)
            ? new Rect(p0.x - thickness * .5f, Mathf.Min(p0.y, p1.y), thickness, Mathf.Abs(p1.y - p0.y))
            : new Rect(Mathf.Min(p0.x, p1.x), p0.y - thickness * .5f, Mathf.Abs(p1.x - p0.x), thickness);
        EditorGUI.DrawRect(r, color);
    }

    string HoverText()
    {
        if (!hasHover || cache == null) return "Hover a cell for its zone.";
        var zone = cache.ZoneOf(hoverCell);
        var chunk = MapGrid.ChunkOf(hoverCell);
        var home = cache.Get(zone.id);
        var key = home.hasKey ? "key at " + home.keyCell : "no key (left through windows)";
        return "Cell " + hoverCell + " · chunk " + chunk + " · zone " + zone.id + " · " + zone.height + " " + MapGrid.CeilingHeight(zone.height).ToString("0.0") + " m · " + key;
    }
}
