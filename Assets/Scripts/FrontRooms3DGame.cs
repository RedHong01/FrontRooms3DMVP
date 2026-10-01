using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using UiDocument = UnityEngine.UIElements.UIDocument;
using UiImage = UnityEngine.UIElements.Image;
using UiVectorImage = UnityEngine.UIElements.VectorImage;
using UiVisualElement = UnityEngine.UIElements.VisualElement;
using UiPanelSettings = UnityEngine.UIElements.PanelSettings;
using UiPanelScaleMode = UnityEngine.UIElements.PanelScaleMode;
using UiPanelScreenMatchMode = UnityEngine.UIElements.PanelScreenMatchMode;
using UiDisplayStyle = UnityEngine.UIElements.DisplayStyle;
using UiPosition = UnityEngine.UIElements.Position;
using UiOverflow = UnityEngine.UIElements.Overflow;
using UiPickingMode = UnityEngine.UIElements.PickingMode;
using UiLength = UnityEngine.UIElements.Length;
using UiLengthUnit = UnityEngine.UIElements.LengthUnit;

[ExecuteAlways]
// A separate first-person experiment. World X/Z uses the same authored five-cell topology as 2D.
public sealed class FrontRooms3DGame : MonoBehaviour
{
    enum Phase { Title, Playing, Paused, Escaped, Caught }
    enum HunterState { Listen, Hunt, Search, Chase, BreakDoor }
    FrontRoomsLevel level;
    Phase phase;
    HunterState state;
    Camera cam;
    Transform world, hunter;
    Vector2 playerPos, hunterPos, hunterTarget, lastSeen;
    FrontRoom room;
    FrontOpening breakingDoor;
    List<Vector2Int> path = new List<Vector2Int>();
    readonly HashSet<int> keys = new HashSet<int>();
    readonly Dictionary<int, GameObject> openingObjects = new Dictionary<int, GameObject>();
    readonly Dictionary<int, GameObject> openingLintels = new Dictionary<int, GameObject>();
    readonly Dictionary<int, GameObject> keyObjects = new Dictionary<int, GameObject>();
    readonly Dictionary<int, Renderer> noteObjects = new Dictionary<int, Renderer>();
    readonly List<string> events = new List<string>();
    Material wallMat, floorMat, redMat, darkMat, glassMat, yellowMat, whiteMat, ceilingMat;
    readonly Dictionary<RoomRule, Material> wallMats = new Dictionary<RoomRule, Material>();
    readonly Dictionary<RoomRule, Material> floorMats = new Dictionary<RoomRule, Material>();
    readonly Dictionary<RoomRule, Material> ceilingMats = new Dictionary<RoomRule, Material>();
    Material trimMat, seamMat, fixtureMat;
    // Door materials are kept separate from the generic dark furniture
    // material so serialized editor doors can be repaired without losing the
    // authored laminate, gasket and brushed-hardware treatment.
    Material doorMat, doorTrimMat, doorHardwareMat, doorHandleHighlightMat;
    readonly Dictionary<int, List<DoorHandleVisual>> doorHandleVisuals = new Dictionary<int, List<DoorHandleVisual>>();
    int highlightedDoorId = -1;
    float doorHandlePulse;
    AudioSource hum;
    AudioClip playerStepClip, playerRunStepClip, hunterStepClip, glassClip, keyClip, doorClip, slamClip, bangClip, caughtClip, escapeClip;
    FrontRoomsFoley foley;
    Text roomMetaText, roomText, threatStateText, distanceText, contextText, overlayText, crosshair, notebook, displaySettingsText;
    Image logoImage;
    Image logoLeftImage, logoSlideImage;
    Transform logoMotionRoot;
    UiDocument vectorLogoDocument;
    UiVisualElement vectorLogoRoot;
    UiImage vectorLogoLeftImage, vectorLogoS1Image, vectorLogoS2Image;
    UiVectorImage vectorLogoLeftAsset, vectorLogoS1Asset, vectorLogoS2Asset;
    readonly List<UiVisualElement> vectorLogoLetterMasks = new List<UiVisualElement>();
    readonly List<float> vectorLogoLetterWidths = new List<float>();
    UiVisualElement vectorLogoSolidSMask;
    bool vectorLogoActive;
    Material whiteLogoMaterial;
    Sprite brandLogo;
    enum LogoMotionVariation { SlideThenFade, FullLockup }
    [SerializeField, Tooltip("Title logo test: SlideThenFade isolates the SS mark; FullLockup keeps the complete wordmark.")]
    LogoMotionVariation logoMotionVariation = LogoMotionVariation.SlideThenFade;
    [SerializeField, Tooltip("Initial display mode. The player can switch HDR on or off from Display Settings while paused.")]
    bool defaultHdr = true;
    const string HdrPreferenceKey = "FrontRooms.Display.HDR";
    bool hdrEnabled;
    bool displaySettingsOpen;
    Font monoFont, bayonFont, serifFont;
    GameObject overlay, roomPanel, threatPanel, contextPanel, journalPanel, displaySettingsPanel;
    CanvasGroup roomHudGroup, threatHudGroup, contextHudGroup, crosshairHudGroup;
    Image overlayImage;
    Outline logoOutline;
    Transform titleWorld;
    FrontRoomsRoomStream roomStream;
    enum StreamThreatState { Dormant, Listening, Chase, Lost }
    StreamThreatState streamThreatState;
    GameObject streamThreatObject;
    Transform streamThreatBody, streamThreatHead, streamThreatArmLeft, streamThreatArmRight, streamThreatLegLeft, streamThreatLegRight;
    Vector2 streamThreatPos;
    float streamThreatStateTime, streamThreatStepTime, streamThreatGrace;
    bool streamThreatTriggered;
    [SerializeField, Tooltip("Optional room prefab/template copied into each streamed title room.")]
    GameObject streamedRoomTemplate;
    readonly List<TitleSegment> titleSegments = new List<TitleSegment>();
    float titleCameraZ, titleNextZ, titleElapsed, titleLogoAlpha;
    float logoMotionElapsed;
    bool titleHandoffPending;
    bool streamedPlay;
    float titleHandoffTargetZ;
    // Keep the runtime title layer away from the authored gameplay greybox.
    // FrontRoomsRoomStream uses the camera's initial X as its room centerline.
    const float TitleCenterX = 256f;
    const float TitleSegmentLength = 12f;
    const float TitleLookAhead = 72f;
    const float TitleSpeed = 1.15f;
    const float TitleDoorTriggerDistance = 4f;
    const float TitleDoorOpenDuration = .9f;
    const float TitleHandoffDepth = 2f;
    const float LogoScale = .75f;
    // The trailing S forms are deliberately sequenced instead of sharing the
    // same reveal clock: the near afterimage settles first, then the far one
    // pushes out to create the depth trail in the wordmark.
    const float LogoS1SettleAt = .58f;
    // Start the far afterimage while the near S is in its final approach.
    // The relay is intentionally earlier than the near S settle point so the
    // two forms overlap in motion instead of waiting for a hard hand-off.
    const float LogoS2StartAt = .50f;
    const float LogoGlyphWipeStartDelay = .12f;
    const float LogoGlyphWipeStagger = .055f;
    const float LogoGlyphWipeLetterSeconds = .72f;
    const float LogoGlyphCount = 10f;
    const float LogoGlyphWipeCompleteSeconds = LogoGlyphWipeStartDelay + (LogoGlyphCount - 1f) * LogoGlyphWipeStagger + LogoGlyphWipeLetterSeconds;
    const float LogoRelaySeconds = 1.35f;
    const float GameplayHudFadeSeconds = .9f;
    float gameplayHudAlpha;
    float yaw = 90f, pitch, elapsed, stateTime, repathTime, lostTime, stepTime, hunterStepTime, actionTime, flashTime, shiftTime, endWait;
    string flash = "", actionIdentity = "";
    bool released, shiftWarning, journal;
    int notesRead, windowsBroken, doorsBroken, shifts, transitions;
    const float Radius = .27f;
    const float Walk = 3.2f, Run = 5.5f;
    Vector2 testMove;
    bool testRun, testInteract;
    string testDir, testRoute = "door";
    bool testFailed;
    static bool restart;

    sealed class TitleSegment
    {
        public GameObject root;
        public float start;
        public float end;
        public float width;
        public GameObject door;
        public float doorClosedY;
        public bool doorOpening;
        public bool doorOpened;
        public float doorTimer;
    }

    sealed class DoorHandleVisual
    {
        public Renderer renderer;
        public Material baseMaterial;
    }

    void OnEnable()
    {
        // The editor preview is kept inactive while Play Mode owns the runtime
        // world. Re-enable the serialized preview when the scene returns to edit
        // mode so the hierarchy and Scene view remain useful after a test run.
        if (!Application.isPlaying)
        {
            var preview = EditorPreviewTransform();
            if (preview != null) preview.gameObject.SetActive(true);
        }
    }

    Transform EditorPreviewTransform()
    {
        // Transform.Find treats '/' as a hierarchy separator. The slash is part
        // of the readable object name, so inspect direct children instead.
        for (var i = 0; i < transform.childCount; i++)
            if (transform.GetChild(i).name == "EDITOR_PREVIEW / FrontRooms3D") return transform.GetChild(i);
        return null;
    }

    void InitializeLevel()
    {
        if (level != null) return;
        var fallback = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        monoFont = Resources.Load<Font>("Fonts/IBMPlexMono-Regular") ?? fallback;
        bayonFont = Resources.Load<Font>("Fonts/Bayon-Regular") ?? fallback;
        serifFont = Resources.Load<Font>("Fonts/SourceSerif4-Variable") ?? fallback;
        level = new FrontRoomsLevel();
        level.Openings[3].Sealed = true;
        playerPos = FrontRoomsLevel.CenterOf(level.PlayerStart);
        hunterPos = FrontRoomsLevel.CenterOf(level.HunterStart);
        hunterTarget = hunterPos;
        room = level.Rooms[0];
    }

    /// <summary>
    /// Builds the authored first-person greybox into the scene asset while the
    /// editor is idle. This is deliberately public so the scene builder can
    /// finish serialization deterministically instead of relying on a later
    /// Play Mode frame.
    /// </summary>
    public void EnsureEditorPreview()
    {
        if (Application.isPlaying) return;
        InitializeLevel();
        var existing = EditorPreviewTransform();
        if (existing != null)
        {
            existing.gameObject.SetActive(true);
            world = existing;
            cam = existing.GetComponentInChildren<Camera>(true);
            hunter = existing.Find("Hunter");
            openingObjects.Clear();
            openingLintels.Clear();
            RebindSerializedWorld();
            RepairSerializedOpeningHeights();
            return;
        }

        BuildWorld();
        if (world == null) return;
        world.name = "EDITOR_PREVIEW / FrontRooms3D";
        world.SetParent(transform, true);
        if (cam != null) cam.transform.SetParent(world, true);
    }

    void Awake()
    {
        InitializeLevel();
        if (!Application.isPlaying)
        {
            EnsureEditorPreview();
            return;
        }

        Application.targetFrameRate = 60;
        // Keep the first-person image and overlay text at native resolution.
        // The project previously requested MSAA on the camera but left the
        // active Ultra quality level at 0x, so the Game view/build could show
        // soft geometry and UI edges.
        QualitySettings.antiAliasing = 4;
        QualitySettings.globalTextureMipmapLimit = 0;
        Time.timeScale = 1f;
        var args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "-verify3d" && i + 1 < args.Length) testDir = args[i + 1];
            if (args[i] == "-route" && i + 1 < args.Length) testRoute = args[i + 1];
        }
        // Use the serialized scene world in Play Mode as well. That makes a
        // material, light, camera or wall adjustment made in the editor survive
        // into a test run instead of being replaced by a second generated copy.
        var preview = EditorPreviewTransform();
        world = preview;
        cam = preview == null ? null : preview.GetComponentInChildren<Camera>(true);
        hunter = preview == null ? null : preview.Find("Hunter");
        openingObjects.Clear(); openingLintels.Clear(); keyObjects.Clear(); noteObjects.Clear();
        wallMats.Clear(); floorMats.Clear(); ceilingMats.Clear();
        if (world == null) BuildWorld();
        else { RebindSerializedWorld(); RepairSerializedOpeningHeights(); }
        ResolveSerializedMaterials();
        hdrEnabled = PlayerPrefs.GetInt(HdrPreferenceKey, defaultHdr ? 1 : 0) != 0;
        ApplyHdrMode(hdrEnabled, false);
        BuildHud();
        BuildSound();
        BuildTitleCorridor();
        SetPhase(Phase.Title);
        if (testDir != null) { Directory.CreateDirectory(testDir); StartCoroutine(VerifyRoute()); }
        else if (restart) StartGame();
        Log("READY · manual title, first-person · " + (testDir == null ? "no automation" : "explicit verification"));
    }

    static Color C(string hex) { ColorUtility.TryParseHtmlString("#" + hex, out var c); return c; }
    static Vector3 V(Vector2 p, float y = 0f) => new Vector3(p.x, y, p.y);
    static Vector2 P(Vector3 p) => new Vector2(p.x, p.z);
    Material Mat(string name, Color color, bool emission = false)
    {
        var shader = Shader.Find("Standard");
        if (shader == null) shader = Shader.Find("UI/Default");
        var m = new Material(shader);
        m.name = name;
        m.color = color;
        m.SetFloat("_Glossiness", .12f);
        if (emission) { m.EnableKeyword("_EMISSION"); m.SetColor("_EmissionColor", color * .8f); }
        return m;
    }

    Texture2D WallpaperTexture(Color baseColor, Color patternColor, int style)
    {
        // The film's wall is a printed, slightly warm beige under fluorescent
        // light, not a saturated yellow bitmap. A single 256px tile keeps this
        // material cheap for WebGL while the world-size repeat prevents wide
        // wall slabs from stretching the pattern.
        const int size = 256;
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, true, false);
        tex.name = "Procedural wallpaper";
        tex.wrapMode = TextureWrapMode.Repeat;
        tex.filterMode = FilterMode.Trilinear;
        tex.anisoLevel = 4;
        tex.mipMapBias = -0.35f;
        var pixels = new Color[size * size];
        for (var y = 0; y < size; y++)
            for (var x = 0; x < size; x++)
            {
                var fiber = Mathf.Sin((x + style * 23) * .19f + Mathf.Sin(y * .07f)) * .012f
                    + Mathf.Sin((y + style * 17) * .11f) * .008f;
                var v = 0.965f + fiber;
                var c = baseColor * v;
                var shiftedX = x + style * 19;
                var seam = shiftedX % 112 == 0 || shiftedX % 112 == 1;
                var pattern = 0f;
                var variant = ((style % 3) + 3) % 3;
                if (variant == 0)
                {
                    // A low-contrast southwestern chevron, derived from the
                    // reference pattern without copying a film frame.
                    var diagonal = Mathf.Abs(Mathf.Repeat(x + y, 72f) - 36f);
                    var diagonal2 = Mathf.Abs(Mathf.Repeat(x - y + 72f, 72f) - 36f);
                    pattern = Mathf.Max(0f, 1f - Mathf.Min(diagonal, diagonal2) / 5f) * .075f;
                }
                else if (variant == 1)
                {
                    // Sparse floral medallions: readable only in near light,
                    // like a second print run in the practical set.
                    var cx = Mathf.Repeat(x + 22f, 96f) - 48f;
                    var cy = Mathf.Repeat(y + 34f, 96f) - 48f;
                    var radial = Mathf.Sqrt(cx * cx + cy * cy);
                    pattern = Mathf.Clamp01(1f - Mathf.Abs(radial - 19f) / 3.5f) * .055f;
                    pattern += Mathf.Clamp01(1f - radial / 6f) * .035f;
                }
                else
                {
                    var diamond = Mathf.Abs(Mathf.Repeat(x + y, 88f) - 44f) < 2.3f
                        || Mathf.Abs(Mathf.Repeat(x - y + 88f, 88f) - 44f) < 2.3f;
                    pattern = diamond ? .05f : 0f;
                }
                if (seam) c = Color.Lerp(c, patternColor, .22f);
                else if (pattern > 0f) c = Color.Lerp(c, patternColor, pattern);
                pixels[y * size + x] = new Color(c.r, c.g, c.b, 1f);
            }
        tex.SetPixels(pixels); tex.Apply(true, true);
        return tex;
    }

    Texture2D CarpetTexture(Color baseColor, int style)
    {
        const int size = 256;
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, true, false);
        tex.name = "Procedural carpet weave";
        tex.wrapMode = TextureWrapMode.Repeat;
        tex.filterMode = FilterMode.Trilinear;
        tex.anisoLevel = 4;
        var pixels = new Color[size * size];
        for (var y = 0; y < size; y++)
            for (var x = 0; x < size; x++)
            {
                var weave = ((x + y + style * 44) % 16 == 0 ? .07f : -.025f);
                var c = baseColor * (1f + weave);
                if ((x + style * 20) % 96 == 0) c *= .86f;
                pixels[y * size + x] = new Color(c.r, c.g, c.b, 1f);
            }
        tex.SetPixels(pixels); tex.Apply(true, true);
        return tex;
    }

    Material TexturedMat(string name, Color baseColor, Texture2D texture, Vector2 scale, bool emission = false)
    {
        var m = Mat(name, baseColor, emission);
        m.mainTexture = texture;
        m.mainTextureScale = scale;
        return m;
    }

    Material WallMaterial(RoomRule rule) => wallMats.TryGetValue(rule, out var m) ? m : wallMat;
    Material FloorMaterial(RoomRule rule) => floorMats.TryGetValue(rule, out var m) ? m : floorMat;
    Material CeilingMaterial(RoomRule rule) => ceilingMats.TryGetValue(rule, out var m) ? m : ceilingMat;

    static float HeightFor(FrontRoom room)
    {
        if (room == null) return 2.9f;
        switch (room.Rule)
        {
            case RoomRule.Run: return 4.8f;
            case RoomRule.Office: return 3.5f;
            default: return 2.9f;
        }
    }

    static float OpeningHeight(FrontOpening opening)
    {
        return Mathf.Max(HeightFor(opening == null ? null : opening.Owner), HeightFor(opening == null ? null : opening.Other));
    }

    static void SetOpeningHeight(GameObject opening, float height)
    {
        if (opening == null) return;
        var position = opening.transform.localPosition;
        position.y = height * .5f;
        opening.transform.localPosition = position;
        var scale = opening.transform.localScale;
        scale.y = height;
        opening.transform.localScale = scale;
    }

    /// <summary>
    /// Repairs an already serialized greybox after the procedural opening
    /// dimensions change, so an old preview cannot reintroduce a door-height
    /// slit when the scene is opened or built.
    /// </summary>
    public void RepairSerializedOpeningHeights()
    {
        InitializeLevel();
        if (world == null) return;
        if (openingObjects.Count == 0 || openingLintels.Count == 0)
        {
            openingObjects.Clear();
            openingLintels.Clear();
            RebindSerializedWorld();
        }

        const float headerHeight = .24f;
        foreach (var opening in level.Openings)
        {
            var height = OpeningHeight(opening);
            var leafHeight = Mathf.Max(.1f, height - .04f);
            if (openingObjects.TryGetValue(opening.Id, out var slab)) SetOpeningHeight(slab, leafHeight);
            if (openingLintels.TryGetValue(opening.Id, out var lintel))
            {
                var position = lintel.transform.localPosition;
                position.y = height - headerHeight * .5f;
                lintel.transform.localPosition = position;
                var scale = lintel.transform.localScale;
                scale.y = headerHeight;
                lintel.transform.localScale = scale;
            }
        }
    }

    GameObject Box(string name, Vector3 pos, Vector3 scale, Material mat)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cube);
        g.name = name; g.transform.SetParent(world); g.transform.position = pos; g.transform.localScale = scale;
        g.GetComponent<Renderer>().sharedMaterial = mat;
        return g;
    }
    void BuildWorld()
    {
        world = new GameObject("Five rooms / first-person").transform;
        wallMat = Mat("Warm wallpaper", C("B5A66A"));
        floorMat = Mat("Carpet", C("51472F"));
        redMat = Mat("Red corridor", C("571E21"));
        darkMat = Mat("Door and furniture", C("252525"));
        glassMat = Mat("Frosted blue glass", C("8DBAC2"), true);
        yellowMat = Mat("Brass", C("EACB37"), true);
        whiteMat = Mat("Paper", C("EBE6CF"));
        ceilingMat = Mat("Ceiling", C("797467"));

        // The visual grammar follows the deck: yellowed repeating wallpaper,
        // low-sheen carpet, and room-specific temperature/contrast changes.
        // Each room gets a material instance so the transition itself is legible.
        wallMats[RoomRule.Lobby] = TexturedMat("Wallpaper / lobby", C("BDB18C"), WallpaperTexture(C("BDB18C"), C("958B6A"), 0), new Vector2(1.15f, 1.15f));
        wallMats[RoomRule.Shift] = TexturedMat("Wallpaper / level 0", C("A8A07D"), WallpaperTexture(C("A8A07D"), C("81785F"), 1), new Vector2(1.05f, 1.2f));
        wallMats[RoomRule.Office] = TexturedMat("Wallpaper / office / woven beige", C("B7AE94"), WallpaperTexture(C("B7AE94"), C("87806E"), 2), new Vector2(1.35f, 1.18f));
        wallMats[RoomRule.Run] = TexturedMat("Wall / run / chalky utility", C("766B60"), WallpaperTexture(C("766B60"), C("554B45"), 5), new Vector2(1.05f, 1.35f));
        wallMats[RoomRule.Exit] = TexturedMat("Wallpaper / exit", C("5D7770"), WallpaperTexture(C("5D7770"), C("334B46"), 4), new Vector2(.9f, 2f));

        floorMats[RoomRule.Lobby] = TexturedMat("Carpet / lobby", C("51472F"), CarpetTexture(C("51472F"), 0), new Vector2(2.8f, 2.8f));
        floorMats[RoomRule.Shift] = TexturedMat("Carpet / level 0", C("4B4330"), CarpetTexture(C("4B4330"), 1), new Vector2(2.8f, 2.8f));
        floorMats[RoomRule.Office] = TexturedMat("Carpet / office / worn grey brown", C("4A453C"), CarpetTexture(C("4A453C"), 2), new Vector2(2.35f, 2.35f));
        floorMats[RoomRule.Run] = TexturedMat("Floor / run / dirty concrete", C("3B3735"), CarpetTexture(C("3B3735"), 5), new Vector2(2.8f, 2.8f));
        floorMats[RoomRule.Exit] = TexturedMat("Carpet / exit", C("283A38"), CarpetTexture(C("283A38"), 4), new Vector2(2.8f, 2.8f));

        ceilingMats[RoomRule.Lobby] = Mat("Ceiling / lobby", C("777266"));
        ceilingMats[RoomRule.Shift] = Mat("Ceiling / level 0", C("696355"));
        ceilingMats[RoomRule.Office] = Mat("Ceiling / office / acoustic tile", C("706D68"));
        ceilingMats[RoomRule.Run] = Mat("Ceiling / run / exposed service", C("2B2926"));
        ceilingMats[RoomRule.Exit] = Mat("Ceiling / exit", C("354846"));
        trimMat = Mat("Aged wall trim", C("716440"));
        seamMat = Mat("Wallpaper seam", C("81744A"));
        fixtureMat = Mat("Fluorescent diffuser", C("F7F2D8"), true);

        // Keep the room readable through local fixtures rather than flooding the
        // whole map with a flat grey/yellow ambient wash.  Trilight gives the
        // unlit side of the walls a cool ceiling bounce and a much darker floor
        // bounce, which is closer to a real fluorescent room and keeps doorways
        // and corners from looking like unlit solid-colour blocks.
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
        // Set ambientLight first: in Unity's built-in renderer this property is
        // an alias for the sky colour and would otherwise overwrite it.
        RenderSettings.ambientLight = new Color(.16f, .15f, .12f);
        RenderSettings.ambientSkyColor = C("74776D");
        RenderSettings.ambientEquatorColor = C("393329");
        RenderSettings.ambientGroundColor = C("1B1813");
        RenderSettings.reflectionIntensity = .3f;
        RenderSettings.fog = true; RenderSettings.fogMode = FogMode.ExponentialSquared;
        RenderSettings.fogColor = C("1B1A17"); RenderSettings.fogDensity = .024f;
        QualitySettings.shadowDistance = 48f;
        QualitySettings.shadowCascades = 4;
        var fill = new GameObject("Soft ambient direction").AddComponent<Light>();
        fill.transform.SetParent(world);
        fill.type = LightType.Directional; fill.intensity = .16f; fill.color = C("C4D0CC");
        fill.shadows = LightShadows.Soft;
        fill.shadowStrength = .18f;
        fill.shadowBias = .045f;
        fill.shadowNormalBias = .28f;
        fill.shadowNearPlane = .1f;
        fill.transform.rotation = Quaternion.Euler(70f, -30f, 0f);
        foreach (var r in level.Rooms)
        {
            float height = HeightFor(r);
            var center = V(r.Center);
            Box(r.Name + " / floor", center + Vector3.down * .12f, new Vector3(12f, .24f, 10f), FloorMaterial(r.Rule));
            Box(r.Name + " / ceiling", center + Vector3.up * (height + .1f), new Vector3(12f, .2f, 10f), CeilingMaterial(r.Rule));
            BuildRoomTrim(r, height);
            for (int i = 0; i < 3; i++)
            {
                var lampPos = new Vector3(r.Interior.xMin + 2f + i * 3.3f, height - .08f, 5f);
                var fixture = Box(r.Name + " / fluorescent fixture", lampPos, new Vector3(1.7f, .1f, .36f), r.Rule == RoomRule.Run ? yellowMat : fixtureMat);
                var light = new GameObject("Room light").AddComponent<Light>();
                light.transform.SetParent(world); light.transform.position = lampPos - Vector3.up * .28f;
                light.type = LightType.Point;
                // Point lights naturally fall off with distance.  The lower
                // ranges and intensities make each fluorescent fixture read as
                // a small pool of light, leaving the seams, trim and corners in
                // believable shade instead of evenly lighting the whole room.
                light.range = r.Rule == RoomRule.Shift ? 6.8f : r.Rule == RoomRule.Run ? 7.2f : r.Rule == RoomRule.Office ? 8f : 7.6f;
                light.intensity = r.Rule == RoomRule.Shift ? 1.05f : r.Rule == RoomRule.Run ? 1.35f : r.Rule == RoomRule.Office ? 1.45f : 1.2f;
                light.color = r.Rule == RoomRule.Run ? C("D7C2A4") : r.Rule == RoomRule.Shift ? C("B9B694") : r.Rule == RoomRule.Office ? C("F1DFC5") : r.Rule == RoomRule.Exit ? C("A9D7D0") : C("E6D5A7");
                light.shadows = LightShadows.Soft;
                light.shadowStrength = r.Rule == RoomRule.Run ? .82f : .67f;
                light.shadowBias = .035f;
                light.shadowNormalBias = .18f;
                light.shadowNearPlane = .06f;
                light.bounceIntensity = .18f;
                var flicker = light.gameObject.AddComponent<FrontRoomsLightFlicker>();
                flicker.baseIntensity = light.intensity;
                flicker.rule = r.Rule;
                flicker.seed = r.Id * 17 + i * 31;
            }
            if (r.Rule != RoomRule.Run && r.Rule != RoomRule.Exit)
            {
                var notePos = V(FrontRoomsLevel.CenterOf(r.TellTile), 1.15f);
                var stand = Box("Note stand", notePos + Vector3.down * .57f, new Vector3(.1f, 1.1f, .1f), darkMat);
                var board = Box("Readable note", notePos, new Vector3(.09f, .72f, .62f), whiteMat);
                noteObjects[r.Id] = board.GetComponent<Renderer>();
                for (int n = 0; n < 3; n++) Box("Ink on note", notePos + new Vector3(-.052f, .18f - n * .14f, 0f), new Vector3(.008f, .025f, .4f), darkMat);
            }
            if (r.HasKey)
            {
                var g = new GameObject("Office key"); g.transform.SetParent(world); g.transform.position = V(FrontRoomsLevel.CenterOf(r.KeyTile), .85f);
                var key = Box("Key shaft", g.transform.position, new Vector3(.6f, .07f, .07f), yellowMat); key.transform.SetParent(g.transform);
                var tooth = Box("Key tooth", g.transform.position + new Vector3(.22f, -.08f, 0f), new Vector3(.08f, .2f, .07f), yellowMat); tooth.transform.SetParent(g.transform);
                var bow = GameObject.CreatePrimitive(PrimitiveType.Sphere); bow.name = "Key bow"; bow.transform.SetParent(g.transform); bow.transform.localPosition = new Vector3(-.35f, 0f, 0f); bow.transform.localScale = Vector3.one * .25f; bow.GetComponent<Renderer>().sharedMaterial = yellowMat;
                keyObjects[r.Id] = g;
            }
            if (r.Rule == RoomRule.Office)
            {
                // Level 4 reads as an abandoned office building: low modular
                // partitions, empty desk islands and a few ordinary supplies.
                // The centre lane stays clear so the player can still read the
                // threshold and the Relay silhouette. One partition is offset
                // by design: a small architectural error is more unsettling
                // than a room filled with random props.
                var officeDesk = Mat("Office / stained laminate", C("4D4A43"));
                var officeMetal = Mat("Office / oxidized steel", C("66635D"));
                var officePaper = Mat("Office / paper", C("D7D0BB"));
                for (int i = -1; i <= 1; i++)
                {
                    var x = 29f + i * 2.45f + (i == 1 ? .22f : 0f);
                    var z = 6.65f;
                    Box("Office desk surface", new Vector3(x, .72f, z), new Vector3(1.75f, .12f, .72f), officeDesk);
                    Box("Office desk leg left", new Vector3(x - .67f, .35f, z), new Vector3(.12f, .62f, .45f), officeMetal);
                    Box("Office desk leg right", new Vector3(x + .67f, .35f, z), new Vector3(.12f, .62f, .45f), officeMetal);
                    Box("Office CRT monitor", new Vector3(x, 1.08f, z + .18f), new Vector3(.48f, .34f, .08f), officeMetal);
                    Box("Office monitor stand", new Vector3(x, .88f, z + .1f), new Vector3(.08f, .18f, .08f), officeMetal);
                    Box("Office paper stack", new Vector3(x - .42f, .82f, z - .16f), new Vector3(.22f, .03f, .28f), officePaper);
                    Box("Office low partition", new Vector3(x, 1.2f, z + .82f), new Vector3(1.45f, 1.0f, .09f), WallMaterial(r.Rule));
                }
                // A cooler and a filing cabinet make the office legible without
                // turning the room into a prop museum.
                Box("Office water cooler body", new Vector3(32.9f, .9f, 3.8f), new Vector3(.48f, .9f, .48f), officeMetal);
                Box("Office water cooler bottle", new Vector3(32.9f, 1.58f, 3.8f), new Vector3(.31f, .42f, .31f), glassMat);
                Box("Office filing cabinet", new Vector3(25.25f, .78f, 8.15f), new Vector3(.56f, .78f, .52f), officeMetal);
                Box("Office cabinet handle", new Vector3(25.25f, 1.02f, 7.87f), new Vector3(.22f, .035f, .035f), officePaper);
            }
            else if (r.Rule == RoomRule.Run)
            {
                // Run is a utility transition rather than a red-painted room:
                // neutral chalky walls carry the space, while emergency red is
                // reserved for a warning source near the next threshold.
                var runMetal = Mat("Run / galvanized cabinet", C("5D5B57"));
                var runCable = Mat("Run / rubber cable", C("1B1A19"));
                var runHazard = Mat("Run / emergency warning", C("B54A36"), true);
                Box("Run utility cabinet left", new Vector3(38.4f, 1.0f, 4.1f), new Vector3(.7f, 1.0f, 1.0f), runMetal);
                Box("Run utility cabinet right", new Vector3(45.1f, 1.0f, 7.7f), new Vector3(.7f, 1.0f, 1.0f), runMetal);
                Box("Run cable tray", new Vector3(0f + 42f, 2.48f, 7.0f), new Vector3(4.2f, .12f, .18f), runCable);
                Box("Run hazard marker left", new Vector3(37.25f, 1.2f, 9.5f), new Vector3(.08f, 1.25f, 1.1f), runHazard);
                Box("Run hazard marker right", new Vector3(46.25f, 1.2f, 9.5f), new Vector3(.08f, 1.25f, 1.1f), runHazard);
                Box("Run service cart", new Vector3(45.15f, .52f, 3.8f), new Vector3(.72f, .12f, .48f), runMetal);
                Box("Run cart handle", new Vector3(45.15f, .95f, 4.12f), new Vector3(.62f, .08f, .08f), runCable);
                var runEmergency = new GameObject("Run emergency light").AddComponent<Light>();
                runEmergency.transform.SetParent(world); runEmergency.transform.position = new Vector3(42f, 2.35f, 10.7f);
                runEmergency.type = LightType.Point; runEmergency.range = 6.5f; runEmergency.intensity = .65f;
                runEmergency.color = C("C84C39"); runEmergency.shadows = LightShadows.Soft; runEmergency.shadowStrength = .7f;
            }
            for (int i = 0; i < 5 && r.Rule != RoomRule.Exit; i++)
                Box("Footprint", new Vector3(r.Interior.xMin + .8f + i * .5f, .013f, 3.5f + (i % 2 == 0 ? .12f : -.12f)), new Vector3(.19f, .015f, .1f), darkMat);
        }
        BuildContinuousWallSlabs();
        foreach (var o in level.Openings)
        {
            var center = V(o.Center);
            var openingHeight = OpeningHeight(o);
            var leafHeight = Mathf.Max(.1f, openingHeight - .04f);
            var slab = Box(o.Kind.ToString(), center + Vector3.up * (leafHeight * .5f), new Vector3(.3f, leafHeight, o.Tiles.Count), o.Kind == OpeningKind.Window ? glassMat : o.Kind == OpeningKind.Door ? darkMat : wallMat);
            openingObjects[o.Id] = slab;
            if (o.Kind == OpeningKind.Hall) slab.SetActive(o.Sealed);
            var lintel = Box("Lintel", center + Vector3.up * (openingHeight - .12f), new Vector3(1f, .24f, o.Tiles.Count), wallMat);
            openingLintels[o.Id] = lintel;
            if (o.Kind == OpeningKind.Door) Box("Brass lock", center + new Vector3(-.17f, 1.15f, -.55f), new Vector3(.06f, .18f, .18f), yellowMat).transform.SetParent(slab.transform, true);
            if (o.Kind == OpeningKind.Window)
                for (int n = -1; n <= 1; n++) Box("Glass frame", center + new Vector3(0f, leafHeight * .5f, n * o.Tiles.Count * .45f), new Vector3(.38f, leafHeight, .06f), darkMat).transform.SetParent(slab.transform, true);
        }
        Box("Exit light", new Vector3(58f, .025f, 5.5f), new Vector3(2f, .05f, 3f), Mat("Exit glow", C("B2F6DA"), true));
        cam = new GameObject("First-person camera").AddComponent<Camera>();
        cam.fieldOfView = 76f; cam.nearClipPlane = .06f; cam.farClipPlane = 80f;
        cam.allowHDR = true;
        cam.allowMSAA = true;
        cam.useOcclusionCulling = true;
        cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = C("22231C"); cam.gameObject.AddComponent<AudioListener>();
        hunter = new GameObject("Hunter").transform; hunter.SetParent(world);
        var body = GameObject.CreatePrimitive(PrimitiveType.Capsule); body.transform.SetParent(hunter); body.transform.localPosition = new Vector3(0f, 1.05f, 0f); body.transform.localScale = new Vector3(.65f, 1.05f, .65f); body.GetComponent<Renderer>().sharedMaterial = darkMat;
        var head = GameObject.CreatePrimitive(PrimitiveType.Sphere); head.transform.SetParent(hunter); head.transform.localPosition = new Vector3(0f, 2.03f, 0f); head.transform.localScale = Vector3.one * .46f; head.GetComponent<Renderer>().sharedMaterial = whiteMat;
        PositionView();
    }

    void RebindSerializedWorld()
    {
        if (world == null) return;
        var direct = new Dictionary<string, List<GameObject>>();
        foreach (Transform child in world)
        {
            if (!direct.TryGetValue(child.name, out var list)) direct[child.name] = list = new List<GameObject>();
            list.Add(child.gameObject);
        }

        GameObject[] candidates(string name)
        {
            return direct.TryGetValue(name, out var list) ? list.ToArray() : Array.Empty<GameObject>();
        }
        var halls = candidates("Hall");
        var doors = candidates("Door");
        var windows = candidates("Window");
        var lintels = candidates("Lintel");
        var hallIndex = 0;
        var doorIndex = 0;
        var windowIndex = 0;
        var lintelIndex = 0;
        foreach (var opening in level.Openings)
        {
            var source = opening.Kind == OpeningKind.Hall ? halls : opening.Kind == OpeningKind.Door ? doors : windows;
            var index = opening.Kind == OpeningKind.Hall ? hallIndex++ : opening.Kind == OpeningKind.Door ? doorIndex++ : windowIndex++;
            if (lintelIndex < lintels.Length) openingLintels[opening.Id] = lintels[lintelIndex++];
            if (index >= source.Length) continue;
            openingObjects[opening.Id] = source[index];
            source[index].SetActive(opening.Kind == OpeningKind.Hall ? opening.Sealed : true);
            var renderer = source[index].GetComponent<Renderer>();
            if (renderer != null)
            {
                if (opening.Kind == OpeningKind.Window && glassMat == null) glassMat = renderer.sharedMaterial;
                if (opening.Kind == OpeningKind.Door && darkMat == null) darkMat = renderer.sharedMaterial;
            }
        }

        var keysFound = candidates("Office key");
        var keyIndex = 0;
        foreach (var room in level.Rooms)
            if (room.HasKey && keyIndex < keysFound.Length) keyObjects[room.Id] = keysFound[keyIndex++];

        var notesFound = candidates("Readable note");
        var noteIndex = 0;
        foreach (var room in level.Rooms)
        {
            if (room.Rule == RoomRule.Run || room.Rule == RoomRule.Exit) continue;
            if (noteIndex >= notesFound.Length) break;
            var renderer = notesFound[noteIndex++].GetComponent<Renderer>();
            if (renderer != null)
            {
                noteObjects[room.Id] = renderer;
                if (whiteMat == null) whiteMat = renderer.sharedMaterial;
            }
        }

        if (yellowMat == null)
        {
            var lockObject = world.GetComponentsInChildren<Transform>(true);
            foreach (var t in lockObject)
            {
                if (t.name != "Brass lock" && t.name != "Key shaft") continue;
                var renderer = t.GetComponent<Renderer>();
                if (renderer != null) { yellowMat = renderer.sharedMaterial; break; }
            }
        }
        if (cam == null) cam = world.GetComponentInChildren<Camera>(true);
        if (hunter == null) hunter = world.Find("Hunter");
        PositionView();
    }

    void ResolveSerializedMaterials()
    {
        // Play Mode normally reuses the serialized editor preview. Recover the
        // shared materials from that preview so the title corridor keeps the
        // same wallpaper/carpet language without generating a second set of
        // procedural textures.
        if (world == null) return;
        foreach (var renderer in world.GetComponentsInChildren<Renderer>(true))
        {
            var material = renderer.sharedMaterial;
            if (material == null) continue;
            var name = renderer.gameObject.name;
            if (wallMat == null && name.Contains("continuous wallpaper")) wallMat = material;
            if (floorMat == null && name.EndsWith(" / floor", StringComparison.Ordinal)) floorMat = material;
            if (ceilingMat == null && name.EndsWith(" / ceiling", StringComparison.Ordinal)) ceilingMat = material;
            if (trimMat == null && name.Contains("baseboard")) trimMat = material;
            if (darkMat == null && (name == "Door" || name.Contains("Brass lock"))) darkMat = material;
        }
        if (wallMat == null) wallMat = Mat("Title wallpaper", C("D4C37B"));
        if (floorMat == null) floorMat = Mat("Title carpet", C("51472F"));
        if (ceilingMat == null) ceilingMat = Mat("Title ceiling", C("777266"));
        if (darkMat == null) darkMat = Mat("Title door", C("252525"));
    }

    GameObject TitleBox(Transform parent, string name, Vector3 position, Vector3 scale, Material material)
    {
        var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = name;
        box.transform.SetParent(parent, false);
        box.transform.position = position;
        box.transform.localScale = scale;
        var renderer = box.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = material;
        return box;
    }

    void BuildTitleCorridor()
    {
        // Fast Enter Play Mode can preserve the previous generated stream.
        // Rebuild it so the title always starts with a fresh wipe/relay clock.
        if (titleWorld != null) StopTitleCorridor();
        titleWorld = new GameObject("Title sequence / recycled corridor").transform;
        // Keep the runtime title layer away from the authored gameplay greybox.
        // The camera stays in the same generated room through handoff, then the
        // separate StartGame path returns it to the serialized map for route
        // verification and ordinary editor-authored play.
        if (cam != null)
        {
            var titlePosition = cam.transform.position;
            titlePosition.x = TitleCenterX;
            titlePosition.y = 1.62f;
            cam.transform.position = titlePosition;
            cam.transform.rotation = Quaternion.identity;
        }
        roomStream = titleWorld.gameObject.AddComponent<FrontRoomsRoomStream>();
        roomStream.roomTemplate = streamedRoomTemplate;
        roomStream.Initialize(cam, WallMaterial(RoomRule.Lobby), FloorMaterial(RoomRule.Lobby), CeilingMaterial(RoomRule.Lobby), trimMat, fixtureMat, darkMat,
            foley == null ? doorClip : foley.Doors.hinge,
            foley == null ? null : foley.Doors.latch,
            foley == null ? null : foley.Doors.travel,
            new[] { WallMaterial(RoomRule.Lobby), WallMaterial(RoomRule.Shift), WallMaterial(RoomRule.Office), WallMaterial(RoomRule.Run), WallMaterial(RoomRule.Exit) },
            new[] { FloorMaterial(RoomRule.Lobby), FloorMaterial(RoomRule.Shift), FloorMaterial(RoomRule.Office), FloorMaterial(RoomRule.Run), FloorMaterial(RoomRule.Exit) },
            new[] { CeilingMaterial(RoomRule.Lobby), CeilingMaterial(RoomRule.Shift), CeilingMaterial(RoomRule.Office), CeilingMaterial(RoomRule.Run), CeilingMaterial(RoomRule.Exit) });
        BuildStreamThreat();
        titleCameraZ = cam == null ? 0f : cam.transform.position.z;
        titleLogoAlpha = 0f;
        logoMotionElapsed = 0f;
        titleHandoffPending = false;
        streamedPlay = false;
        if (cam != null) cam.transform.rotation = Quaternion.identity;
    }

    void UpdateTitleSequence(float dt)
    {
        if (roomStream == null || cam == null) return;
        roomStream.Tick(dt);
        titleElapsed += dt;
        // The editorial letter wipe is a start transition, not an idle-title
        // animation. Keep the complete wordmark visible while the title
        // waits for input, then restart the wipe clock from zero when the
        // player triggers the game.
        if (titleHandoffPending) logoMotionElapsed += dt;
        titleCameraZ = roomStream.CameraZ;
        titleLogoAlpha = roomStream.LogoVisibility;
        UpdateLogoMotion();
        // The camera can arrive at the next-room anchor before the editorial
        // logo transition finishes. Hold the title state until both the
        // per-letter wipe and the two-stage S relay have completed, then hand
        // control to the player on the same camera position.
        if (titleHandoffPending && roomStream.HasControl
            && logoMotionElapsed >= LogoGlyphWipeCompleteSeconds + LogoRelaySeconds)
            EnterGameplayFromTitle();
    }

    void UpdateLogoMotion()
    {
        if (vectorLogoActive)
        {
            var vectorVisible = phase == Phase.Title;
            if (vectorLogoRoot != null) vectorLogoRoot.style.display = vectorVisible ? UiDisplayStyle.Flex : UiDisplayStyle.None;
            if (!vectorVisible || vectorLogoLeftImage == null || vectorLogoS1Image == null || vectorLogoS2Image == null) return;

            // Each front glyph owns a local, hard-edged clipping box. The
            // source SVG stays stationary; only the mask width grows from
            // left to right. A small stagger creates the editorial rhythm
            // without fading, scaling, or wiping the word as one object.
            var wipeElapsed = titleHandoffPending
                ? Mathf.Max(0f, logoMotionElapsed - LogoGlyphWipeStartDelay)
                : LogoGlyphWipeCompleteSeconds;
            for (var i = 0; i < vectorLogoLetterMasks.Count; i++)
            {
                var stagger = i * LogoGlyphWipeStagger;
                var reveal = Mathf.Clamp01((wipeElapsed - stagger) / LogoGlyphWipeLetterSeconds);
                reveal = reveal * reveal * (3f - 2f * reveal);
                vectorLogoLetterMasks[i].style.width = new UiLength(vectorLogoLetterWidths[i] * reveal, UiLengthUnit.Pixel);
            }
            // FRONTROOMS includes the solid base S. It follows the same local
            // left-to-right wipe as the nine preceding glyphs; only after this
            // tenth glyph is complete may the two relay S forms travel right.
            if (vectorLogoSolidSMask != null)
            {
                var solidSReveal = Mathf.Clamp01((wipeElapsed - 9f * LogoGlyphWipeStagger) / LogoGlyphWipeLetterSeconds);
                solidSReveal = solidSReveal * solidSReveal * (3f - 2f * solidSReveal);
                vectorLogoSolidSMask.style.width = new UiLength(83f * solidSReveal, UiLengthUnit.Pixel);
            }

            // Door progress is the motion clock. The afterimage S forms begin
            // exactly on top of the solid final S, then peel away one at a time
            // as the first physical door opens. The full title stays visible
            // after the movement completes while the corridor keeps looping.
            // The physical first door still starts on the same player trigger,
            // but the relay waits until FRONTROOMS has finished its wipe. This
            // preserves the existing S1 -> S2 hand-off without letting the
            // afterimages appear before the wordmark is readable.
            var relayClock = titleHandoffPending
                ? Mathf.Clamp01((logoMotionElapsed - LogoGlyphWipeCompleteSeconds) / LogoRelaySeconds)
                : 0f;
            var doorProgress = relayClock;
            var s1End = logoMotionVariation == LogoMotionVariation.FullLockup ? .66f : LogoS1SettleAt;
            var s2Start = logoMotionVariation == LogoMotionVariation.FullLockup ? .70f : LogoS2StartAt;
            var vectorS1T = Mathf.Clamp01(doorProgress / s1End);
            vectorS1T = vectorS1T * vectorS1T * (3f - 2f * vectorS1T);
            var vectorS2T = Mathf.Clamp01((doorProgress - s2Start) / (1f - s2Start));
            vectorS2T = vectorS2T * vectorS2T * (3f - 2f * vectorS2T);
            var vectorS1X = Mathf.Lerp(814f, 846f, vectorS1T);
            // The far S follows the first afterimage until the relay point,
            // then continues from the first S's actual position at that point.
            // This keeps the earlier hand-off continuous and preserves the
            // intended left-to-right depth relationship.
            var s2StartS1T = Mathf.Clamp01(s2Start / s1End);
            s2StartS1T = s2StartS1T * s2StartS1T * (3f - 2f * s2StartS1T);
            var vectorS2StartX = Mathf.Lerp(814f, 846f, s2StartS1T);
            var vectorS2X = doorProgress < s2Start
                ? vectorS1X
                : Mathf.Lerp(vectorS2StartX, 880f, vectorS2T);
            // Position by the painted left edge of each imported SVG. Using
            // the asset's full viewBox here shifts the relay S forms left and
            // leaves a white sliver beside the F. The painted bounds are the
            // actual optical baseline for the lockup.
            vectorLogoS1Image.style.left = new UiLength(vectorS1X - 841.734f, UiLengthUnit.Pixel);
            vectorLogoS2Image.style.left = new UiLength(vectorS2X - 879.734f, UiLengthUnit.Pixel);
            // Keep the vector mark on the same fade-in clock as the title
            // corridor. It remains at full opacity after the reveal; only the
            // player handoff hides it.
            // Keep the mark fully visible for the complete trigger transition.
            // The room stream may reach its handoff anchor first and begin its
            // own exit fade; that fade must not cut the S relay short.
            var vectorAlpha = titleHandoffPending ? 1f : Mathf.Clamp01(titleLogoAlpha);
            vectorLogoLeftImage.style.opacity = vectorAlpha;
            // The idle title keeps only FRONTROOMS visible. During the
            // triggered transition the nearer S appears first, then the far
            // S joins from the nearer S's moving position.
            var relayNearAlpha = titleHandoffPending ? 1f : 0f;
            var relayFarAlpha = titleHandoffPending
                ? Mathf.Clamp01((relayClock - s2Start) / .12f)
                : 0f;
            vectorLogoS1Image.style.opacity = vectorAlpha * relayNearAlpha;
            vectorLogoS2Image.style.opacity = vectorAlpha * relayFarAlpha;
            return;
        }
        if (logoMotionRoot == null || logoLeftImage == null || logoSlideImage == null) return;
        var visible = phase == Phase.Title;
        logoLeftImage.enabled = visible;
        logoSlideImage.enabled = visible;
        if (!visible) return;
        var doorProgressFallback = roomStream == null ? 0f : roomStream.FirstDoorProgress;
        var slideT = doorProgressFallback;
        slideT = slideT * slideT * (3f - 2f * slideT);
        var slideRect = logoSlideImage.rectTransform;
        var restX = -75f;
        var startX = restX - 118f;
        slideRect.anchoredPosition = new Vector2(Mathf.Lerp(startX, restX, slideT), 0f);
        logoLeftImage.color = new Color(1f, 1f, 1f, titleLogoAlpha);
        logoSlideImage.color = new Color(1f, 1f, 1f, titleLogoAlpha);
    }

    void StopTitleCorridor()
    {
        if (titleWorld != null)
        {
            if (Application.isPlaying) Destroy(titleWorld.gameObject);
            else DestroyImmediate(titleWorld.gameObject);
        }
        titleWorld = null;
        roomStream = null;
        titleSegments.Clear();
        streamThreatObject = null;
        streamThreatBody = null;
        streamThreatHead = null;
        streamThreatArmLeft = null;
        streamThreatArmRight = null;
        streamThreatLegLeft = null;
        streamThreatLegRight = null;
    }

    void RequestTitleStart()
    {
        if (titleHandoffPending || streamedPlay) return;
        if (roomStream == null) return;
        // Arm the per-glyph wipe exactly when the player presses Start. The
        // title can sit in its fully revealed state indefinitely beforehand.
        logoMotionElapsed = 0f;
        roomStream.RequestStart();
        titleHandoffPending = true;
    }

    void EnterGameplayFromTitle()
    {
        if (!titleHandoffPending || streamedPlay) return;
        titleHandoffPending = false;
        streamedPlay = true;
        // The same camera remains in the same generated room. Only its input
        // ownership changes, so the player never sees a reset to the authored
        // five-room origin or a loading cut.
        playerPos = new Vector2(cam.transform.position.x, cam.transform.position.z);
        yaw = 0f;
        pitch = 0f;
        elapsed = 0f;
        if (hunter != null) hunter.gameObject.SetActive(false);
        streamThreatState = StreamThreatState.Dormant;
        streamThreatStateTime = 0f;
        streamThreatStepTime = 0f;
        streamThreatGrace = 0f;
        streamThreatTriggered = false;
        if (streamThreatObject != null) streamThreatObject.SetActive(false);
        // The title pool is intentionally Lobby-only until this handoff.
        // Once the camera reaches the first room's Entry anchor, reveal the
        // authored sequence so subsequent doors become Shift → Office → Run → Exit.
        roomStream.BeginPlayableSequence();
        SetPhase(Phase.Playing);
        Event("start", "streamed-room");
    }

    void UpdateStreamedPlay(float dt)
    {
        yaw += Input.GetAxisRaw("Mouse X") * 2.1f;
        pitch = Mathf.Clamp(pitch - Input.GetAxisRaw("Mouse Y") * 2.1f, -75f, 75f);
        var local = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        var forward = new Vector2(Mathf.Sin(yaw * Mathf.Deg2Rad), Mathf.Cos(yaw * Mathf.Deg2Rad));
        var right = new Vector2(forward.y, -forward.x);
        var sprint = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        var before = new Vector2(cam.transform.position.x, cam.transform.position.z);
        var movement = (right * local.x + forward * local.y).normalized * (sprint ? Run : Walk) * dt;
        var moved = roomStream == null ? cam.transform.position : roomStream.Move(movement);
        var after = new Vector2(moved.x, moved.z);
        cam.transform.position = new Vector3(after.x, 1.62f, after.y);
        cam.transform.rotation = Quaternion.Euler(pitch, yaw, 0f);
        titleCameraZ = after.y;
        if (Vector2.Distance(before, after) > .001f)
        {
            stepTime += dt;
            if (stepTime > (sprint ? .3f : .5f))
            {
                stepTime = 0f;
                FoleyFootstep(after, FrontRoomsFoleyActor.Player, StreamSurface(), sprint, sprint ? .48f : .15f);
            }
        }
        UpdateStreamThreat(dt, after, sprint);
    }

    FrontRoomsFoleySurface StreamSurface()
    {
        if (roomStream == null) return FrontRoomsFoleySurface.Carpet;
        switch (roomStream.CurrentRule)
        {
            case RoomRule.Office: return FrontRoomsFoleySurface.Tile;
            case RoomRule.Run: return FrontRoomsFoleySurface.Concrete;
            case RoomRule.Exit: return FrontRoomsFoleySurface.Metal;
            default: return FrontRoomsFoleySurface.Carpet;
        }
    }

    void BuildStreamThreat()
    {
        if (titleWorld == null || streamThreatObject != null) return;
        streamThreatObject = new GameObject("STREAM THREAT / RELAY");
        streamThreatObject.transform.SetParent(titleWorld, false);
        streamThreatObject.SetActive(false);
        streamThreatBody = StreamPrimitive(PrimitiveType.Capsule, "body / hunched", streamThreatObject.transform, new Vector3(0f, 1.15f, 0f), new Vector3(.55f, 1.15f, .55f), darkMat);
        streamThreatHead = StreamPrimitive(PrimitiveType.Sphere, "head / blank", streamThreatObject.transform, new Vector3(0f, 2.15f, .02f), new Vector3(.62f, .7f, .52f), whiteMat);
        streamThreatArmLeft = StreamPrimitive(PrimitiveType.Cube, "arm / left", streamThreatObject.transform, new Vector3(-.52f, 1.18f, 0f), new Vector3(.18f, .9f, .18f), darkMat);
        streamThreatArmRight = StreamPrimitive(PrimitiveType.Cube, "arm / right", streamThreatObject.transform, new Vector3(.52f, 1.18f, 0f), new Vector3(.18f, .9f, .18f), darkMat);
        streamThreatLegLeft = StreamPrimitive(PrimitiveType.Cube, "leg / left", streamThreatObject.transform, new Vector3(-.2f, .45f, 0f), new Vector3(.2f, .85f, .2f), darkMat);
        streamThreatLegRight = StreamPrimitive(PrimitiveType.Cube, "leg / right", streamThreatObject.transform, new Vector3(.2f, .45f, 0f), new Vector3(.2f, .85f, .2f), darkMat);
    }

    Transform StreamPrimitive(PrimitiveType type, string name, Transform parent, Vector3 localPosition, Vector3 scale, Material material)
    {
        var primitive = GameObject.CreatePrimitive(type);
        primitive.name = name;
        primitive.transform.SetParent(parent, false);
        primitive.transform.localPosition = localPosition;
        primitive.transform.localScale = scale;
        var renderer = primitive.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = material;
        return primitive.transform;
    }

    void UpdateStreamThreat(float dt, Vector2 player, bool sprint)
    {
        if (roomStream == null || streamThreatObject == null) return;
        var rule = roomStream.CurrentRule;
        // A title can be left running for several cycles before Space is
        // pressed. Trigger from either side of the Office -> Run beat so the
        // encounter is never skipped when the player hands control over in
        // the red room.
        if (!streamThreatTriggered && roomStream.CurrentRoomNumber >= 2 && (rule == RoomRule.Office || rule == RoomRule.Run))
        {
            streamThreatTriggered = true;
            streamThreatState = StreamThreatState.Listening;
            streamThreatStateTime = 0f;
            // Give the player a readable reveal window after the handoff. The
            // Relay is deliberately behind the camera's entry point, rather
            // than inside the same doorway, so a room transition can never
            // resolve as an instant catch on the first gameplay frame.
            streamThreatGrace = 2.25f;
            streamThreatPos = new Vector2(player.x, player.y - 8f);
            streamThreatObject.SetActive(true);
            Event("threat", "relay-listening");
        }
        if (!streamThreatTriggered) return;

        streamThreatStateTime += dt;
        streamThreatGrace = Mathf.Max(0f, streamThreatGrace - dt);
        if (rule == RoomRule.Run && streamThreatState != StreamThreatState.Chase)
        {
            streamThreatState = StreamThreatState.Chase;
            streamThreatStateTime = 0f;
            Event("threat", "relay-chase");
            Flash("RUN  /  KEEP THE RED ROOM MOVING", 3f);
        }
        if (streamThreatState == StreamThreatState.Listening && (sprint || streamThreatStateTime > 3.2f))
        {
            streamThreatState = StreamThreatState.Chase;
            streamThreatStateTime = 0f;
            Event("threat", "relay-chase");
        }
        if (streamThreatState == StreamThreatState.Chase)
        {
            var speed = sprint ? 4.35f : 3.72f;
            streamThreatPos = Vector2.MoveTowards(streamThreatPos, player, speed * dt);
            streamThreatStepTime += dt;
            if (streamThreatStepTime > (sprint ? .29f : .43f))
            {
                streamThreatStepTime = 0f;
                FoleyFootstep(streamThreatPos, FrontRoomsFoleyActor.Hunter, StreamSurface(), sprint, .34f);
            }
            if (streamThreatGrace <= 0f && Vector2.Distance(streamThreatPos, player) < .8f)
            {
                streamThreatState = StreamThreatState.Lost;
                streamThreatObject.SetActive(false);
                End(false);
                return;
            }
        }
        var threatTransform = streamThreatObject.transform;
        threatTransform.position = V(streamThreatPos);
        var facing = Mathf.Atan2(player.x - streamThreatPos.x, player.y - streamThreatPos.y) * Mathf.Rad2Deg;
        threatTransform.rotation = Quaternion.Euler(0f, facing, 0f);
        var gait = streamThreatState == StreamThreatState.Chase ? Mathf.Sin(Time.time * 18f) : Mathf.Sin(Time.time * 2.2f) * .12f;
        if (streamThreatArmLeft != null) streamThreatArmLeft.localRotation = Quaternion.Euler(gait * 28f, 0f, 0f);
        if (streamThreatArmRight != null) streamThreatArmRight.localRotation = Quaternion.Euler(-gait * 28f, 0f, 0f);
        if (streamThreatLegLeft != null) streamThreatLegLeft.localRotation = Quaternion.Euler(-gait * 20f, 0f, 0f);
        if (streamThreatLegRight != null) streamThreatLegRight.localRotation = Quaternion.Euler(gait * 20f, 0f, 0f);
        if (streamThreatHead != null) streamThreatHead.localRotation = Quaternion.Euler(0f, Mathf.Sin(Time.time * 1.8f) * 6f, 0f);
    }

    /// <summary>
    /// The first greybox made one cube per wall tile. That read as a row of
    /// pillars in first person. Merge adjacent wall cells into continuous
    /// slabs, breaking only at openings and room-material changes, so the
    /// wallpaper reads as an actual building surface.
    /// </summary>
    void BuildContinuousWallSlabs()
    {
        var used = new bool[level.Width, level.Height];
        for (var y = 0; y < level.Height; y++)
        {
            for (var x = 0; x < level.Width; x++)
            {
                if (used[x, y] || level.Tiles[x, y] != TileKind.Wall) continue;
                var room = WallRoomAt(x, y);
                var horizontalNeighbor = IsWall(x - 1, y) || IsWall(x + 1, y);
                var verticalNeighbor = IsWall(x, y - 1) || IsWall(x, y + 1);

                if (horizontalNeighbor || !verticalNeighbor)
                {
                    var end = x;
                    while (end + 1 < level.Width && !used[end + 1, y] && IsWall(end + 1, y) && SameWallRoom(room, WallRoomAt(end + 1, y))) end++;
                    MarkWallRun(used, x, end, y, y);
                    AddWallSlab(room, x, end, y, y);
                }
                else
                {
                    var end = y;
                    while (end + 1 < level.Height && !used[x, end + 1] && IsWall(x, end + 1) && SameWallRoom(room, WallRoomAt(x, end + 1))) end++;
                    MarkWallRun(used, x, x, y, end);
                    AddWallSlab(room, x, x, y, end);
                }
            }
        }
    }

    bool IsWall(int x, int y) => x >= 0 && y >= 0 && x < level.Width && y < level.Height && level.Tiles[x, y] == TileKind.Wall;

    FrontRoom WallRoomAt(int x, int y)
    {
        var around = new[] { Vector2Int.left, Vector2Int.right, Vector2Int.down, Vector2Int.up };
        foreach (var d in around)
        {
            var p = new Vector2Int(x + d.x, y + d.y);
            if (!level.InBounds(p)) continue;
            var room = level.RoomOf(p);
            if (room != null) return room;
        }
        return level.Rooms[Mathf.Clamp(x / FrontRoomsLevel.CellW, 0, level.Rooms.Count - 1)];
    }

    static bool SameWallRoom(FrontRoom a, FrontRoom b) => a == null || b == null || a.Rule == b.Rule;

    void MarkWallRun(bool[,] used, int x0, int x1, int y0, int y1)
    {
        for (var x = x0; x <= x1; x++)
            for (var y = y0; y <= y1; y++)
                used[x, y] = true;
    }

    void AddWallSlab(FrontRoom room, int x0, int x1, int y0, int y1)
    {
        var h = HeightFor(room);
        var center = new Vector3((x0 + x1 + 1f) * .5f, h * .5f, (y0 + y1 + 1f) * .5f);
        var scale = new Vector3(x1 - x0 + 1f, h, y1 - y0 + 1f);
        var slab = Box(room.Name + " / continuous wallpaper", center, scale, WallMaterial(room.Rule));

        // A cube's default UVs are 0..1 regardless of its transform scale.  Set
        // the wallpaper transform from the slab's actual dimensions so a 1-cell
        // wall and a 4-cell wall keep the same physical paper repeat.  This also
        // makes every generated slab a useful, editable material instance in the
        // serialized scene rather than relying on one global stretched material.
        var renderer = slab.GetComponent<Renderer>();
        if (renderer != null)
        {
            var material = new Material(WallMaterial(room.Rule));
            material.name = room.Name + " / wallpaper material (" + (x1 - x0 + 1) + "x" + (y1 - y0 + 1) + ")";
            var horizontal = x1 > x0 || y1 == y0;
            var runLength = horizontal ? scale.x : scale.z;
            const float paperRepeatX = 2.25f;
            const float paperRepeatY = 2.4f;
            material.mainTextureScale = new Vector2(Mathf.Max(.25f, runLength / paperRepeatX), Mathf.Max(.25f, h / paperRepeatY));
            // Keep the paper pattern phase continuous across adjacent slabs.
            var runStart = horizontal ? x0 : y0;
            material.mainTextureOffset = new Vector2(runStart / paperRepeatX, 0f);
            renderer.sharedMaterial = material;
        }
    }

    void BuildRoomTrim(FrontRoom room, float height)
    {
        // A narrow baseboard and ceiling shadow line keep the large repeated rooms
        // readable in first person without introducing furniture that blocks routes.
        var x0 = room.Interior.xMin + .06f;
        var x1 = room.Interior.xMax - .06f;
        var z0 = room.Interior.yMin + .06f;
        var z1 = room.Interior.yMax - .06f;
        var width = room.Interior.width - .12f;
        var depth = room.Interior.height - .12f;
        Box(room.Name + " / baseboard front", new Vector3(room.Center.x, .18f, z0), new Vector3(width, .16f, .08f), trimMat);
        Box(room.Name + " / baseboard back", new Vector3(room.Center.x, .18f, z1), new Vector3(width, .16f, .08f), trimMat);
        Box(room.Name + " / baseboard left", new Vector3(x0, .18f, room.Center.y), new Vector3(.08f, .16f, depth), trimMat);
        Box(room.Name + " / baseboard right", new Vector3(x1, .18f, room.Center.y), new Vector3(.08f, .16f, depth), trimMat);
        for (var i = 1; i < 4; i++)
        {
            var x = room.Interior.xMin + room.Interior.width * i / 4f;
            Box(room.Name + " / paper seam", new Vector3(x, height * .5f, z0 + .045f), new Vector3(.028f, height * .82f, .012f), seamMat);
            Box(room.Name + " / paper seam", new Vector3(x, height * .5f, z1 - .045f), new Vector3(.028f, height * .82f, .012f), seamMat);
        }
    }
    void BuildSound()
    {
        var recordedDoorCreak = Resources.Load<AudioClip>("Audio/door-creak");
        foley = new FrontRoomsFoley(recordedDoorCreak);
        playerStepClip = FrontRoomsAudio.PlayerStep(); playerRunStepClip = FrontRoomsAudio.PlayerRunStep(); hunterStepClip = FrontRoomsAudio.HunterStep();
        glassClip = FrontRoomsAudio.Glass(); keyClip = FrontRoomsAudio.Key();
        // The Foley door set layers a latch, hinge recording, movement bed and
        // settle/impact. Keep the old clips as fallbacks for verification tools.
        doorClip = foley.Doors.hinge;
        slamClip = foley.Doors.slam; bangClip = foley.Doors.breakImpact;
        caughtClip = FrontRoomsAudio.Caught(); escapeClip = FrontRoomsAudio.Escape();
        hum = cam.gameObject.AddComponent<AudioSource>(); hum.clip = FrontRoomsAudio.Hum(); hum.loop = true; hum.volume = .18f; hum.Play();
    }
    void Sound(AudioClip clip, Vector2 p, float volume = .7f)
    {
        var g = new GameObject("Spatial sound"); g.transform.position = V(p, 1f);
        var source = g.AddComponent<AudioSource>(); source.clip = clip; source.spatialBlend = 1f; source.minDistance = 2f; source.maxDistance = 26f; source.volume = volume; source.Play();
        Destroy(g, clip.length + .1f);
    }

    FrontRoomsFoleySurface SurfaceFor(FrontRoom sourceRoom)
    {
        if (sourceRoom == null) return FrontRoomsFoleySurface.Carpet;
        switch (sourceRoom.Rule)
        {
            case RoomRule.Office: return FrontRoomsFoleySurface.Tile;
            case RoomRule.Run: return FrontRoomsFoleySurface.Concrete;
            case RoomRule.Exit: return FrontRoomsFoleySurface.Metal;
            default: return FrontRoomsFoleySurface.Carpet;
        }
    }

    FrontRoomsFoleySurface SurfaceAt(Vector2 p)
    {
        return level == null ? FrontRoomsFoleySurface.Carpet : SurfaceFor(level.RoomOf(FrontRoomsLevel.TileOf(p)));
    }

    void FoleyFootstep(Vector2 p, FrontRoomsFoleyActor actor, FrontRoomsFoleySurface surface, bool running, float volume)
    {
        if (foley == null)
        {
            var fallback = actor == FrontRoomsFoleyActor.Hunter ? hunterStepClip : (running ? playerRunStepClip : playerStepClip);
            Sound(fallback, p, volume);
            return;
        }
        var selection = foley.PickStep(actor, surface, running);
        var g = new GameObject("Foley / " + actor + " / " + surface);
        g.transform.position = V(p, actor == FrontRoomsFoleyActor.Hunter ? .45f : .08f);
        var source = g.AddComponent<AudioSource>();
        source.spatialBlend = 1f;
        source.minDistance = actor == FrontRoomsFoleyActor.Hunter ? 1.25f : 1.1f;
        source.maxDistance = actor == FrontRoomsFoleyActor.Hunter ? 32f : 18f;
        source.rolloffMode = AudioRolloffMode.Logarithmic;
        source.dopplerLevel = actor == FrontRoomsFoleyActor.Hunter ? .15f : .04f;
        source.spread = actor == FrontRoomsFoleyActor.Hunter ? 28f : 12f;
        source.priority = actor == FrontRoomsFoleyActor.Hunter ? 64 : 90;
        source.pitch = selection.pitch;
        source.PlayOneShot(selection.impact, volume);
        source.PlayOneShot(selection.texture, volume * (actor == FrontRoomsFoleyActor.Hunter ? .72f : .62f));
        source.PlayOneShot(selection.cloth, volume * .34f);
        if (actor == FrontRoomsFoleyActor.Hunter)
        {
            var low = g.AddComponent<AudioLowPassFilter>();
            low.cutoffFrequency = 1450f;
            low.lowpassResonanceQ = 1.1f;
        }
        Destroy(g, .52f);
    }

    void FoleyDoor(Vector2 p, bool closing = false, bool breaking = false)
    {
        if (foley == null)
        {
            Sound(breaking ? bangClip : closing ? slamClip : doorClip, p, breaking || closing ? 1f : .7f);
            return;
        }
        var g = new GameObject("Foley / door / " + (breaking ? "break" : closing ? "slam" : "open"));
        g.transform.position = V(p, 1f);
        var source = g.AddComponent<AudioSource>();
        source.spatialBlend = 1f;
        source.minDistance = 2f;
        source.maxDistance = 26f;
        source.rolloffMode = AudioRolloffMode.Logarithmic;
        source.dopplerLevel = .06f;
        source.priority = breaking ? 48 : 72;
        source.pitch = .97f + UnityEngine.Random.Range(-.025f, .025f);
        if (breaking)
        {
            source.PlayOneShot(foley.Doors.breakImpact, 1f);
            Destroy(g, foley.Doors.breakImpact.length + .1f);
            return;
        }
        if (closing)
        {
            source.PlayOneShot(foley.Doors.slam, .9f);
            Destroy(g, foley.Doors.slam.length + .1f);
            return;
        }
        source.PlayOneShot(foley.Doors.latch, .42f);
        source.PlayOneShot(foley.Doors.hinge, .78f);
        source.PlayOneShot(foley.Doors.travel, .42f);
        Destroy(g, Mathf.Max(foley.Doors.hinge.length, foley.Doors.travel.length) + .12f);
    }

    void HunterSound(Vector2 p, float volume)
    {
        FoleyFootstep(p, FrontRoomsFoleyActor.Hunter, SurfaceAt(p), state == HunterState.Chase, volume);
    }
    Font UiFont(string name, int fontSize)
    {
        if (name.Contains("Room meta") || name.Contains("Distance") || name.Contains("Aim")) return monoFont;
        if (name.Contains("Threat") || name.Contains("Menu text")) return bayonFont;
        return serifFont;
    }
    Text Text(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, int fontSize, TextAnchor alignment)
    {
        var g = new GameObject(name); g.transform.SetParent(parent, false); var t = g.AddComponent<Text>();
        t.font = UiFont(name, fontSize); t.fontSize = fontSize; t.color = C("ECEAE0"); t.alignment = alignment; t.raycastTarget = false;
        t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Overflow;
        var rt = t.rectTransform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor; rt.anchoredPosition = pos; rt.sizeDelta = size;
        t.lineSpacing = 1f;
        if (name != "Menu text") g.AddComponent<Outline>().effectColor = new Color(0, 0, 0, .7f); return t;
    }
    GameObject Panel(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Color color)
    {
        var g = new GameObject(name); g.transform.SetParent(parent, false); var image = g.AddComponent<Image>(); image.color = color; image.raycastTarget = false;
        var rt = image.rectTransform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor; rt.anchoredPosition = pos; rt.sizeDelta = size;
        return g;
    }
    void LoadBrandLogo()
    {
        vectorLogoLeftAsset = Resources.Load<UiVectorImage>("Brand/FrontRoomsLogo_Left");
        vectorLogoS1Asset = Resources.Load<UiVectorImage>("Brand/FrontRoomsLogo_S1");
        vectorLogoS2Asset = Resources.Load<UiVectorImage>("Brand/FrontRoomsLogo_S2");
        if (vectorLogoLeftAsset != null && vectorLogoS1Asset != null && vectorLogoS2Asset != null
            && BuildVectorLogo(vectorLogoLeftAsset, vectorLogoS1Asset, vectorLogoS2Asset))
        {
            vectorLogoActive = true;
            if (logoImage != null) logoImage.enabled = false;
            return;
        }
        var texture = Resources.Load<Texture2D>("Brand/FrontRoomsLogo");
        if (texture == null) return;
        brandLogo = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height), new Vector2(.5f, .5f), 100f);
        brandLogo.name = "FrontRooms brand logo (runtime)";
        if (logoImage != null)
        {
            logoImage.sprite = brandLogo;
            logoImage.preserveAspect = true;
            logoImage.color = Color.white;
            var whiteLogoShader = Resources.Load<Shader>("Brand/WhiteLogoUI") ?? Shader.Find("UI/FrontRooms White Logo");
            if (whiteLogoShader != null)
            {
                whiteLogoMaterial = new Material(whiteLogoShader);
                whiteLogoMaterial.name = "FrontRooms logo white (runtime)";
                logoImage.material = whiteLogoMaterial;
            }
            ConfigureLogoMotion(texture);
        }
    }

    bool BuildVectorLogo(UiVectorImage leftAsset, UiVectorImage s1Asset, UiVectorImage s2Asset)
    {
        if (leftAsset == null || s1Asset == null || s2Asset == null) return false;
        var host = new GameObject("FrontRooms vector logo");
        vectorLogoDocument = host.AddComponent<UiDocument>();
        var settings = ScriptableObject.CreateInstance<UiPanelSettings>();
        settings.clearColor = false;
        settings.clearDepthStencil = false;
        settings.scaleMode = UiPanelScaleMode.ScaleWithScreenSize;
        settings.referenceResolution = new Vector2Int(1920, 1080);
        settings.screenMatchMode = UiPanelScreenMatchMode.MatchWidthOrHeight;
        settings.match = .5f;
        settings.sortingOrder = 100;
        vectorLogoDocument.panelSettings = settings;
        var panel = vectorLogoDocument.rootVisualElement;
        if (panel == null) return false;
        panel.pickingMode = UiPickingMode.Ignore;
        panel.style.position = UiPosition.Absolute;
        panel.style.left = 0f; panel.style.top = 0f;
        panel.style.width = UiLength.Percent(100); panel.style.height = UiLength.Percent(100);

        vectorLogoRoot = new UiVisualElement { name = "FrontRooms SVG lockup" };
        vectorLogoRoot.style.position = UiPosition.Absolute;
        vectorLogoRoot.style.left = UiLength.Percent(50);
        vectorLogoRoot.style.top = UiLength.Percent(50);
        vectorLogoRoot.style.width = 965f; vectorLogoRoot.style.height = 192f;
        vectorLogoRoot.style.marginLeft = -482.5f; vectorLogoRoot.style.marginTop = -96f;
        vectorLogoRoot.style.scale = new UnityEngine.UIElements.Scale(new Vector3(LogoScale, LogoScale, 1f));
        vectorLogoRoot.style.overflow = UiOverflow.Hidden;
        vectorLogoRoot.pickingMode = UiPickingMode.Ignore;
        panel.Add(vectorLogoRoot);

        vectorLogoLetterMasks.Clear();
        vectorLogoLetterWidths.Clear();
        // The supplied left SVG contains FRONTROOMS. Each front glyph now
        // uses its own cropped VectorImage so the local mask reveals the
        // correct letter instead of repeating the source SVG's first F.
        var glyphNames = new[] { "F", "R", "O1", "N", "T", "R2", "O2", "O3", "M" };
        // Five px optical tracking between the imported glyph viewBoxes keeps
        // the word readable at the title scale while retaining the original
        // 965 px lockup width.
        var glyphStarts = new[] { 8f, 85f, 177f, 267f, 353f, 444f, 537f, 626f, 715f };
        var glyphEnds = new[] { 80f, 172f, 262f, 348f, 439f, 532f, 621f, 710f, 809f };
        var glyphAssets = new UiVectorImage[glyphNames.Length];
        for (var i = 0; i < glyphNames.Length; i++)
        {
            glyphAssets[i] = Resources.Load<UiVectorImage>("Brand/FrontRoomsGlyph_" + glyphNames[i]);
            if (glyphAssets[i] == null) return false;
            var mask = MaskedVectorGlyph("SVG front glyph " + i.ToString("00"), glyphAssets[i], glyphStarts[i], glyphEnds[i], out _);
            vectorLogoLetterMasks.Add(mask);
            vectorLogoLetterWidths.Add(glyphEnds[i] - glyphStarts[i]);
            vectorLogoRoot.Add(mask);
        }

        var solidSAsset = Resources.Load<UiVectorImage>("Brand/FrontRoomsGlyph_S");
        if (solidSAsset == null) return false;
        vectorLogoSolidSMask = MaskedVectorGlyph("SVG solid S mask", solidSAsset, 814f, 897f, out vectorLogoLeftImage);
        vectorLogoRoot.Add(vectorLogoSolidSMask);
        // Keep the original full-width viewBox so each relay S retains its
        // gradient. The painted paths start at these source x coordinates;
        // subtract them so both visible glyphs begin on the solid S baseline.
        vectorLogoS1Image = VectorLogoImage("SVG trailing S 1", s1Asset, 814f - 841.734f, 0f);
        vectorLogoS2Image = VectorLogoImage("SVG trailing S 2", s2Asset, 814f - 879.734f, 0f);
        vectorLogoRoot.Add(vectorLogoS1Image);
        vectorLogoRoot.Add(vectorLogoS2Image);
        vectorLogoRoot.style.display = UiDisplayStyle.None;
        return vectorLogoLeftImage != null && vectorLogoS1Image != null && vectorLogoS2Image != null;
    }

    UiVisualElement MaskedVectorGlyph(string name, UiVectorImage vectorImage, float glyphStart, float glyphEnd, out UiImage innerImage)
    {
        var mask = new UiVisualElement { name = name + " / hard wipe mask" };
        mask.style.position = UiPosition.Absolute;
        mask.style.left = glyphStart;
        mask.style.top = 0f;
        mask.style.width = 0f;
        mask.style.height = 192f;
        mask.style.overflow = UiOverflow.Hidden;
        mask.pickingMode = UiPickingMode.Ignore;
        // The VectorImage is already cropped to this glyph's local viewBox.
        // Keep it stationary at the mask origin; only the mask width changes.
        innerImage = VectorLogoImage(name + " / stationary glyph source", vectorImage, 0f, 0f);
        // The imported VectorImage reports painted bounds, which are slightly
        // narrower than the original local viewBox. Use the source lockup box
        // so the final M and solid S are never trimmed by their masks.
        innerImage.style.width = glyphEnd - glyphStart;
        innerImage.style.height = 192f;
        innerImage.style.opacity = 1f;
        mask.Add(innerImage);
        return mask;
    }

    UiImage VectorLogoImage(string name, UiVectorImage vectorImage, float left, float top)
    {
        var image = new UiImage { name = name, vectorImage = vectorImage };
        image.scaleMode = UnityEngine.ScaleMode.StretchToFill;
        image.tintColor = Color.white;
        image.style.position = UiPosition.Absolute;
        image.style.left = left; image.style.top = top;
        // VectorImage bounds are the painted path bounds. Stretching the small
        // S asset to the full 965px viewBox turns it into a ribbon, so preserve
        // each imported asset's native size and place it in the shared lockup.
        image.style.width = vectorImage.width; image.style.height = vectorImage.height;
        image.style.opacity = 0f;
        image.pickingMode = UiPickingMode.Ignore;
        return image;
    }

    void ApplyHdrMode(bool enabled, bool persist)
    {
        var supported = SystemInfo.SupportsRenderTextureFormat(RenderTextureFormat.DefaultHDR);
        if (cam != null) cam.allowHDR = enabled && supported;
        // Unity 6 no longer exposes a readable Camera.hdr property. The
        // support check plus the value applied to allowHDR is the portable
        // runtime state for the built-in renderer and WebGL fallback.
        hdrEnabled = enabled && supported;
        if (persist)
        {
            PlayerPrefs.SetInt(HdrPreferenceKey, hdrEnabled ? 1 : 0);
            PlayerPrefs.Save();
        }
        UpdateDisplaySettingsText();
    }

    void UpdateDisplaySettingsText()
    {
        if (displaySettingsText == null) return;
        var mode = hdrEnabled ? "HDR RENDER  /  ON" : "HDR RENDER  /  OFF  (SDR)";
        displaySettingsText.text = "<size=30><b>DISPLAY SETTINGS</b></size>\n\n"
            + "OUTPUT\n<size=34><color=#F4DF3B>" + mode + "</color></size>\n\n"
            + "H  TOGGLE HDR\nESC  CLOSE";
    }

    void ToggleDisplaySettings()
    {
        if (phase != Phase.Paused || displaySettingsPanel == null) return;
        displaySettingsOpen = !displaySettingsOpen;
        displaySettingsPanel.SetActive(displaySettingsOpen);
        if (overlayText != null) overlayText.enabled = !displaySettingsOpen;
        UpdateDisplaySettingsText();
    }

    void ConfigureLogoMotion(Texture2D texture)
    {
        if (texture == null || logoImage == null || logoImage.transform.parent == null) return;
        var parent = logoImage.transform.parent;
        var rootObject = new GameObject("FrontRooms logo motion");
        if (rootObject == null) return;
        logoMotionRoot = rootObject.transform;
        if (logoMotionRoot == null) return;
        logoMotionRoot.SetParent(parent, false);
        var rootRect = rootObject.GetComponent<RectTransform>();
        if (rootRect == null) rootRect = rootObject.AddComponent<RectTransform>();
        if (rootRect == null) return;
        rootRect.anchorMin = rootRect.anchorMax = new Vector2(.5f, .5f);
        rootRect.pivot = new Vector2(.5f, .5f);
        rootRect.anchoredPosition = Vector2.zero;
        rootRect.sizeDelta = new Vector2(texture.width, texture.height);
        logoMotionRoot.localScale = Vector3.one * LogoScale;

        // The supplied lockup reserves the final 150 px for the two offset S
        // forms. Keeping those pixels as a separate sprite lets the title use
        // the requested slide-and-fade motion without redrawing the artwork.
        const int splitX = 815;
        var leftWidth = Mathf.Clamp(splitX, 1, texture.width - 1);
        var rightWidth = texture.width - leftWidth;
        var leftSprite = Sprite.Create(texture, new Rect(0f, 0f, leftWidth, texture.height), new Vector2(.5f, .5f), 100f);
        var rightSprite = Sprite.Create(texture, new Rect(leftWidth, 0f, rightWidth, texture.height), new Vector2(.5f, .5f), 100f);
        leftSprite.name = "FrontRooms logo left lockup";
        rightSprite.name = "FrontRooms logo sliding SS";
        logoLeftImage = LogoPart(logoMotionRoot, "Logo left lockup", leftSprite, leftWidth, -((texture.width - leftWidth) * .5f));
        logoSlideImage = LogoPart(logoMotionRoot, "Logo sliding SS", rightSprite, rightWidth, -((texture.width - leftWidth) * .5f));
        if (logoLeftImage == null || logoSlideImage == null) return;
        if (whiteLogoMaterial != null)
        {
            logoLeftImage.material = whiteLogoMaterial;
            logoSlideImage.material = whiteLogoMaterial;
        }
        if (logoImage != null) logoImage.enabled = false;
        logoLeftImage.enabled = false;
        logoSlideImage.enabled = false;
    }

    Image LogoPart(Transform parent, string name, Sprite sprite, float width, float x)
    {
        if (parent == null || sprite == null) return null;
        var objectForImage = new GameObject(name);
        if (objectForImage == null) return null;
        objectForImage.transform.SetParent(parent, false);
        var image = objectForImage.AddComponent<Image>();
        if (image == null) return null;
        image.sprite = sprite;
        image.preserveAspect = false;
        image.raycastTarget = false;
        var rect = image.rectTransform;
        rect.anchorMin = rect.anchorMax = new Vector2(.5f, .5f);
        rect.pivot = new Vector2(.5f, .5f);
        rect.anchoredPosition = new Vector2(x, 0f);
        rect.sizeDelta = new Vector2(width, sprite.rect.height);
        return image;
    }
    GameObject TypographyGroup(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size)
    {
        // A RectTransform-only group keeps the HUD typography positioned without
        // introducing a visible card behind information that belongs to the world.
        var g = new GameObject(name); g.transform.SetParent(parent, false);
        var rt = g.AddComponent<RectTransform>(); rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor; rt.anchoredPosition = pos; rt.sizeDelta = size;
        return g;
    }
    GameObject Rule(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Color color)
    {
        return Panel(parent, name, anchor, pos, size, color);
    }
    void BuildHud()
    {
        var g = new GameObject("Minimal HUD"); var c = g.AddComponent<Canvas>(); c.renderMode = RenderMode.ScreenSpaceOverlay; c.pixelPerfect = true;
        var scale = g.AddComponent<CanvasScaler>(); scale.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scale.referenceResolution = new Vector2(1920, 1080); scale.matchWidthOrHeight = .5f;
        var media = new Color(.078f, .078f, .078f, .9f);
        var paper = C("F4F1E8");
        var accent = C("F4DF3B");

        // The play HUD follows the 72px outer margin and 24px internal rhythm from UI_SYSTEM.
        // Room and threat are direct typography overlays. Their cards obscured the
        // environment and allowed long room names to bleed past the top-left edge.
        roomPanel = TypographyGroup(g.transform, "Room typography", new Vector2(0, 1), new Vector2(72, -72), new Vector2(720, 144));
        roomHudGroup = roomPanel.AddComponent<CanvasGroup>();
        Rule(roomPanel.transform, "Room accent", new Vector2(0, 1), new Vector2(0, -24), new Vector2(4, 72), accent);
        roomMetaText = Text(roomPanel.transform, "Room meta", new Vector2(0, 1), new Vector2(24, -18), new Vector2(660, 22), 13, TextAnchor.UpperLeft);
        roomMetaText.color = C("BDBAB0");
        roomText = Text(roomPanel.transform, "Room", new Vector2(0, 1), new Vector2(24, -44), new Vector2(660, 72), 50, TextAnchor.UpperLeft);
        roomText.color = paper;
        roomText.horizontalOverflow = HorizontalWrapMode.Overflow;
        roomText.verticalOverflow = VerticalWrapMode.Overflow;

        threatPanel = TypographyGroup(g.transform, "Threat typography", Vector2.one, new Vector2(-72, -72), new Vector2(720, 144));
        threatHudGroup = threatPanel.AddComponent<CanvasGroup>();
        Rule(threatPanel.transform, "Threat accent", new Vector2(1, 1), new Vector2(0, -24), new Vector2(4, 72), accent);
        threatStateText = Text(threatPanel.transform, "Threat state", new Vector2(1, 1), new Vector2(-24, -18), new Vector2(660, 34), 20, TextAnchor.UpperRight);
        threatStateText.color = accent; threatStateText.fontStyle = FontStyle.Bold;
        threatStateText.horizontalOverflow = HorizontalWrapMode.Overflow;
        threatStateText.verticalOverflow = VerticalWrapMode.Truncate;
        distanceText = Text(threatPanel.transform, "Distance", new Vector2(1, 1), new Vector2(-24, -57), new Vector2(660, 24), 13, TextAnchor.UpperRight);
        distanceText.color = C("BDBAB0");
        distanceText.horizontalOverflow = HorizontalWrapMode.Overflow;
        distanceText.verticalOverflow = VerticalWrapMode.Truncate;

        contextPanel = Panel(g.transform, "Context panel", new Vector2(.5f, 0), new Vector2(0, 72), new Vector2(920, 120), media);
        contextHudGroup = contextPanel.AddComponent<CanvasGroup>();
        Rule(contextPanel.transform, "Context accent", new Vector2(0, .5f), new Vector2(24, 0), new Vector2(4, 72), accent);
        contextText = Text(contextPanel.transform, "Context", new Vector2(.5f, .5f), new Vector2(12, 0), new Vector2(790, 72), 24, TextAnchor.MiddleCenter);
        contextText.color = paper;

        crosshair = Text(g.transform, "Aim", new Vector2(.5f, .5f), Vector2.zero, new Vector2(32, 32), 20, TextAnchor.MiddleCenter); crosshair.text = "·";
        crosshairHudGroup = crosshair.gameObject.AddComponent<CanvasGroup>();
        crosshair.color = accent;
        gameplayHudAlpha = 0f;
        ApplyGameplayHudAlpha();
        journalPanel = Panel(g.transform, "Notes panel", new Vector2(.5f, .5f), Vector2.zero, new Vector2(1296, 744), new Color(.055f, .055f, .05f, .96f));
        Rule(journalPanel.transform, "Notes accent", new Vector2(0, 1), new Vector2(48, -48), new Vector2(4, 120), accent);
        notebook = Text(journalPanel.transform, "Notebook", new Vector2(0, 1), new Vector2(96, -56), new Vector2(1110, 620), 24, TextAnchor.UpperLeft);
        notebook.color = paper;
        journalPanel.SetActive(false);
        displaySettingsPanel = Panel(g.transform, "Display settings", new Vector2(.5f, .5f), Vector2.zero, new Vector2(920, 420), new Color(.055f, .055f, .05f, .97f));
        Rule(displaySettingsPanel.transform, "Display settings accent", new Vector2(0, .5f), new Vector2(28, 0), new Vector2(4, 176), accent);
        displaySettingsText = Text(displaySettingsPanel.transform, "Display settings text", new Vector2(.5f, .5f), new Vector2(18, 0), new Vector2(760, 320), 24, TextAnchor.MiddleCenter);
        displaySettingsText.color = paper;
        displaySettingsPanel.SetActive(false);
        overlay = new GameObject("Menu"); overlay.transform.SetParent(g.transform, false); var image = overlay.AddComponent<Image>(); overlayImage = image;
        // The title uses the supplied brand asset with a white runtime shader;
        // the room remains visible behind it while the mark fades in.
        image.color = new Color(.93f, .92f, .88f, .98f);
        var rt = image.rectTransform; rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
        overlayText = Text(overlay.transform, "Menu text", new Vector2(.5f, .5f), Vector2.zero, new Vector2(1440, 760), 20, TextAnchor.MiddleCenter);
        overlayText.color = C("0A0A0A");
        overlayText.rectTransform.anchoredPosition = new Vector2(0f, -170f);
        // Keep the settings card inside the pause overlay so its dark surface
        // renders above the light pause wash.  It is still created with the
        // same canvas-scale coordinates, then normalized after reparenting.
        if (displaySettingsPanel != null)
        {
            displaySettingsPanel.transform.SetParent(overlay.transform, false);
            var settingsRect = displaySettingsPanel.GetComponent<RectTransform>();
            settingsRect.anchorMin = settingsRect.anchorMax = new Vector2(.5f, .5f);
            settingsRect.pivot = new Vector2(.5f, .5f);
            settingsRect.anchoredPosition = Vector2.zero;
            settingsRect.sizeDelta = new Vector2(920f, 420f);
        }
        logoImage = Panel(overlay.transform, "FrontRooms brand logo", new Vector2(.5f, .5f), Vector2.zero, new Vector2(965f, 192f), Color.white).GetComponent<Image>();
        logoImage.raycastTarget = false;
        logoOutline = logoImage.gameObject.AddComponent<Outline>();
        logoOutline.effectDistance = new Vector2(2f, -2f);
        logoOutline.effectColor = new Color(1f, .86f, .34f, 0f);
        LoadBrandLogo();
        UpdateDisplaySettingsText();
    }
    void SetPhase(Phase p)
    {
        var wasPlaying = phase == Phase.Playing;
        phase = p; bool playing = p == Phase.Playing;
        if (playing && !wasPlaying) gameplayHudAlpha = 0f;
        if (!playing) gameplayHudAlpha = 0f;
        if (p != Phase.Paused)
        {
            displaySettingsOpen = false;
            if (displaySettingsPanel != null) displaySettingsPanel.SetActive(false);
        }
        overlay.SetActive(!playing); crosshair.enabled = playing;
        if (overlayImage != null) overlayImage.color = p == Phase.Title ? new Color(0f, 0f, 0f, 0f) : new Color(.93f, .92f, .88f, .98f);
        if (logoImage != null)
        {
            logoImage.enabled = p == Phase.Title && logoMotionRoot == null && !vectorLogoActive;
            if (p == Phase.Title && logoMotionRoot == null) logoImage.color = new Color(1f, 1f, 1f, titleLogoAlpha);
        }
        if (vectorLogoRoot != null) vectorLogoRoot.style.display = p == Phase.Title ? UiDisplayStyle.Flex : UiDisplayStyle.None;
        if (logoMotionRoot != null)
        {
            if (logoLeftImage != null) logoLeftImage.enabled = p == Phase.Title;
            if (logoSlideImage != null) logoSlideImage.enabled = p == Phase.Title;
        }
        if (roomPanel != null) roomPanel.SetActive(playing);
        if (threatPanel != null) threatPanel.SetActive(playing);
        if (contextPanel != null) contextPanel.SetActive(false);
        if (journalPanel != null) journalPanel.SetActive(false);
        ApplyGameplayHudAlpha();
        Cursor.lockState = playing && testDir == null ? CursorLockMode.Locked : CursorLockMode.None; Cursor.visible = !playing;
        if (p == Phase.Title)
        {
            overlayText.text = "";
            overlayText.enabled = false;
        }
        else overlayText.enabled = true;
        if (p == Phase.Paused) overlayText.text = "<size=88><b>PAUSED</b></size>\n\n<size=13>WASD  MOVE    MOUSE  LOOK    SHIFT  RUN\nHOLD E  READ OR BREAK    E  OPEN KEYED DOOR\nTAB  NOTES    R  RESTART\nO  DISPLAY SETTINGS</size>\n\n<color=#F4DF3B><size=20>ESC  RESUME</size></color>";
        if (p == Phase.Escaped || p == Phase.Caught)
            overlayText.text = "<size=88><b>" + (p == Phase.Escaped ? "ESCAPED" : "CAUGHT") + "</b></size>\n\n<size=24>" + Mathf.RoundToInt(elapsed) + " S  /  " + notesRead + " NOTES</size>\n\n<color=#F4DF3B><size=20>R  TRY AGAIN</size></color>";
    }
    void StartGame()
    {
        streamedPlay = false;
        titleHandoffPending = false;
        StopTitleCorridor();
        if (cam != null && world != null) cam.transform.SetParent(world, true);
        playerPos = FrontRoomsLevel.CenterOf(level.PlayerStart);
        hunterPos = FrontRoomsLevel.CenterOf(level.HunterStart);
        hunterTarget = hunterPos;
        room = level.Rooms[0];
        if (hunter != null) hunter.gameObject.SetActive(true);
        elapsed = 0; SetPhase(Phase.Playing); PositionView(); Event("start", "first-person");
    }
    void OnApplicationFocus(bool focused) { if (!focused && phase == Phase.Playing && testDir == null) SetPhase(Phase.Paused); }
    void Update()
    {
        if (!Application.isPlaying) return;
        if (testDir == null)
        {
            if (phase == Phase.Title && (Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.Return))) RequestTitleStart();
            else if (phase == Phase.Paused && Input.GetKeyDown(KeyCode.O)) ToggleDisplaySettings();
            else if (displaySettingsOpen && Input.GetKeyDown(KeyCode.H)) ApplyHdrMode(!hdrEnabled, true);
            else if (Input.GetKeyDown(KeyCode.Escape) && displaySettingsOpen) ToggleDisplaySettings();
            else if (Input.GetKeyDown(KeyCode.Escape) && (phase == Phase.Playing || phase == Phase.Paused)) SetPhase(phase == Phase.Playing ? Phase.Paused : Phase.Playing);
            if (Input.GetKeyDown(KeyCode.R) && phase != Phase.Playing && phase != Phase.Title) { restart = true; SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex); }
            if (Input.GetKeyDown(KeyCode.Tab) && phase == Phase.Playing) journal = !journal;
        }
        if (phase == Phase.Title)
        {
            UpdateTitleSequence(Mathf.Min(Time.deltaTime, .1f));
            UpdateHud();
            return;
        }
        if (phase == Phase.Playing && streamedPlay)
        {
            var dt = Mathf.Min(Time.deltaTime, .1f);
            elapsed += dt;
            UpdateTitleSequence(dt);
            UpdateStreamedPlay(dt);
            UpdateHud();
            return;
        }
        if (phase == Phase.Playing)
        {
            float dt = Mathf.Min(Time.deltaTime, .1f); elapsed += dt; flashTime -= dt;
            if (testDir == null) { yaw += Input.GetAxisRaw("Mouse X") * 2.1f; pitch = Mathf.Clamp(pitch - Input.GetAxisRaw("Mouse Y") * 2.1f, -75f, 75f); }
            var local = testDir == null ? new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical")) : Vector2.zero;
            var forward = new Vector2(Mathf.Sin(yaw * Mathf.Deg2Rad), Mathf.Cos(yaw * Mathf.Deg2Rad));
            var right = new Vector2(forward.y, -forward.x);
            var move = testDir == null ? right * local.x + forward * local.y : testMove;
            bool sprint = testDir == null ? Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift) : testRun;
            bool interact = testDir == null ? Input.GetKey(KeyCode.E) : testInteract;
            if (actionTime > 0f && interact) move = Vector2.zero;
            var before = playerPos;
            playerPos = Move(playerPos, move.normalized * (sprint ? Run : Walk) * dt);
            if (Vector2.Distance(before, playerPos) > .001f)
            {
                stepTime += dt;
                if (stepTime > (sprint ? .3f : .5f))
                {
                    stepTime = 0;
                    FoleyFootstep(playerPos, FrontRoomsFoleyActor.Player, SurfaceAt(playerPos), sprint, sprint ? .48f : .15f);
                    if (sprint) Noise(playerPos, 7f, "running");
                }
            }
            var next = level.RoomOf(FrontRoomsLevel.TileOf(playerPos));
            if (next != null && next != room) { room = next; transitions++; Event("room", room.Name); if (room.Rule == RoomRule.Run) { Noise(playerPos, 999f, "alarm"); Flash("Run. Break the window ahead."); } }
            PositionView(); Interactions(interact, dt); UpdateDoors(dt); UpdateShift(dt); UpdateHunter(dt);
            if (phase == Phase.Playing && level.ExitTiles.Contains(FrontRoomsLevel.TileOf(playerPos))) End(true);
        }
        PositionView(); UpdateHud();
    }
    Vector2 Move(Vector2 pos, Vector2 delta)
    {
        int steps = Mathf.Max(1, Mathf.CeilToInt(delta.magnitude / .15f)); var d = delta / steps;
        for (int i = 0; i < steps; i++)
        {
            var nx = pos + new Vector2(d.x, 0); if (Free(nx)) pos = nx;
            var ny = pos + new Vector2(0, d.y); if (Free(ny)) pos = ny;
        }
        return pos;
    }
    bool Free(Vector2 p)
    {
        for (int i = 0; i < 4; i++) if (!level.PlayerPassable(FrontRoomsLevel.TileOf(p + new Vector2(i % 2 == 0 ? -Radius : Radius, i < 2 ? -Radius : Radius)))) return false;
        // Match the visible office desk islands, keeping the front and back routes clear.
        for (int i = 0; i < 3; i++) if (Mathf.Abs(p.x - (28f + i * 2.6f)) < .85f + Radius && Mathf.Abs(p.y - 5.9f) < .5f + Radius) return false;
        return true;
    }
    void PositionView()
    {
        cam.transform.position = V(playerPos, 1.62f); cam.transform.rotation = Quaternion.Euler(pitch, yaw, 0);
        hunter.position = V(hunterPos); hunter.rotation = Quaternion.Euler(0, Mathf.Atan2(playerPos.x - hunterPos.x, playerPos.y - hunterPos.y) * Mathf.Rad2Deg, 0);
    }
    bool Looking(Vector2 p, float reach)
    {
        var delta = p - playerPos;
        if (delta.magnitude > reach) return false;
        if (delta.magnitude < .35f) return true;
        return Vector2.Dot(delta.normalized, P(cam.transform.forward).normalized) > .72f;
    }
    float Distance(FrontOpening o, Vector2 p)
    {
        float best = float.MaxValue;
        foreach (var t in o.Tiles) best = Mathf.Min(best, Vector2.Distance(p, FrontRoomsLevel.CenterOf(t)));
        return best;
    }
    FrontOpening NearOpening()
    {
        FrontOpening best = null; float distance = 2f;
        foreach (var o in room.AllOpenings)
        {
            if (o.Kind == OpeningKind.Hall || o.Open) continue;
            float d = Distance(o, playerPos);
            if (d < distance && Looking(o.Center, 2.5f)) { best = o; distance = d; }
        }
        return best;
    }
    void Interactions(bool holding, float dt)
    {
        foreach (var r in level.Rooms)
            if (r.HasKey && !r.KeyTaken && Vector2.Distance(playerPos, FrontRoomsLevel.CenterOf(r.KeyTile)) < .9f)
            {
                r.KeyTaken = true; keys.Add(r.Id); keyObjects[r.Id].SetActive(false); Sound(keyClip, playerPos); Noise(playerPos, 10f, "key"); Event("key", r.Name); Flash("Key taken.");
            }
        string id = ""; float duration = 1.5f; var o = NearOpening();
        bool note = noteObjects.ContainsKey(room.Id) && !room.Read && Looking(FrontRoomsLevel.CenterOf(room.TellTile), 2f);
        if (o != null)
        {
            if (o.Kind == OpeningKind.Door)
            {
                if (holding && keys.Contains(o.Owner.Id)) { o.Open = true; openingObjects[o.Id].SetActive(false); Noise(o.Center, 5f, "door"); FoleyDoor(o.Center); Event("door_open", o.Id.ToString()); }
            }
            else { id = "window" + o.Id; duration = 1f; }
        }
        else if (note) id = "note" + room.Id;
        if (!holding || id == "") { actionTime = 0; actionIdentity = ""; return; }
        if (actionIdentity != id) { actionTime = 0; actionIdentity = id; Event("interaction_start", id); }
        actionTime += dt;
        if (actionTime < duration) return;
        actionTime = 0; actionIdentity = "";
        if (o != null && o.Kind == OpeningKind.Window)
        {
            o.Open = o.Broken = true; openingObjects[o.Id].SetActive(false); windowsBroken++;
            Noise(o.Center, 999f, "glass"); Sound(glassClip, o.Center, 1f); Event("glass", o.Id.ToString()); Flash("The hunter heard the glass.");
            for (int n = 0; n < 7; n++) Box("Broken glass", V(o.Center + new Vector2(UnityEngine.Random.Range(-.8f, .8f), UnityEngine.Random.Range(-1f, 1f)), .025f), new Vector3(.12f, .035f, .2f), glassMat);
        }
        else if (note)
        {
            room.Read = true; notesRead++; noteObjects[room.Id].sharedMaterial = yellowMat; Event("note", room.Name); Flash(room.RuleText, 7f);
        }
    }
    void UpdateDoors(float dt)
    {
        foreach (var o in level.Openings)
        {
            if (o.Kind != OpeningKind.Door || !o.Open || o.Broken) continue;
            if (Distance(o, playerPos) > 1.7f && Distance(o, hunterPos) > 1.3f) o.CloseTimer += dt; else o.CloseTimer = 0;
            if (o.CloseTimer > .6f) { o.Open = false; o.CloseTimer = 0; openingObjects[o.Id].SetActive(true); FoleyDoor(o.Center, true); }
        }
    }
    void UpdateShift(float dt)
    {
        var a = level.Openings[2]; var b = level.Openings[3];
        bool visible = Visible(a) || Visible(b);
        bool occupied = Distance(a, playerPos) < 2f || Distance(b, playerPos) < 2f || Distance(a, hunterPos) < 2f || Distance(b, hunterPos) < 2f;
        if (visible || occupied) { shiftTime = 0; shiftWarning = false; }
        else
        {
            shiftTime += dt;
            if (shiftTime > 5f) shiftWarning = true;
            if (shiftTime > 6f)
            {
                a.Sealed = !a.Sealed; b.Sealed = !a.Sealed; openingObjects[a.Id].SetActive(a.Sealed); openingObjects[b.Id].SetActive(b.Sealed);
                shiftTime = 0; shiftWarning = false; shifts++; Repath(hunterTarget); Event("shift", a.Sealed ? "upper" : "lower");
            }
        }
        hum.volume = shiftWarning ? .025f : .18f;
    }
    bool Visible(FrontOpening o)
    {
        var viewport = cam.WorldToViewportPoint(V(o.Center, 1.4f));
        if (viewport.z <= 0 || viewport.x < 0 || viewport.x > 1 || viewport.y < 0 || viewport.y > 1) return false;
        var near = o.Center + (playerPos - o.Center).normalized * .8f;
        return level.LineOfSight(playerPos, near);
    }
    void Noise(Vector2 p, float radius, string cause)
    {
        Event("noise", cause);
        if (!released || Vector2.Distance(hunterPos, p) > radius || state == HunterState.Chase) return;
        hunterTarget = p; if (state != HunterState.BreakDoor) SetHunter(HunterState.Hunt); Repath(hunterTarget);
    }
    void SetHunter(HunterState s) { if (s == state) return; state = s; stateTime = 0; Event("hunter", s.ToString()); }
    void Repath(Vector2 p) { path = level.FindHunterPath(FrontRoomsLevel.TileOf(hunterPos), FrontRoomsLevel.TileOf(p)); repathTime = 0; }
    void UpdateHunter(float dt)
    {
        if (!released)
        {
            if (elapsed < 10f) return;
            released = true; hunterTarget = new Vector2(15.5f, 3.5f); SetHunter(HunterState.Hunt); Repath(hunterTarget);
        }
        stateTime += dt; repathTime += dt;
        float distance = Vector2.Distance(hunterPos, playerPos);
        bool sees = distance < 8f && level.LineOfSight(hunterPos, playerPos);
        if (sees)
        {
            lastSeen = playerPos; lostTime = 0;
            if (state != HunterState.Chase && state != HunterState.BreakDoor) { SetHunter(HunterState.Chase); Repath(lastSeen); }
        }
        var before = hunterPos;
        switch (state)
        {
            case HunterState.Listen:
                if (stateTime > 2f) { var r = level.RoomOf(FrontRoomsLevel.TileOf(hunterPos)); hunterTarget = level.Rooms[Mathf.Min(4, (r == null ? 0 : r.Id) + 1)].Center; SetHunter(HunterState.Hunt); Repath(hunterTarget); }
                break;
            case HunterState.Hunt: if (Follow(2.5f, dt)) SetHunter(HunterState.Search); break;
            case HunterState.Search: if (stateTime > 2.5f) SetHunter(HunterState.Listen); break;
            case HunterState.Chase:
                if (repathTime > .25f) Repath(sees ? playerPos : lastSeen);
                if (sees && distance < 1.5f) hunterPos = Vector2.MoveTowards(hunterPos, playerPos, 4f * dt); else Follow(4f, dt);
                if (!sees) { lostTime += dt; if (lostTime > 1.5f) { hunterTarget = lastSeen; SetHunter(HunterState.Hunt); Repath(hunterTarget); } }
                break;
            case HunterState.BreakDoor:
                hunterStepTime += dt;
                if (hunterStepTime > .5f) { FoleyDoor(breakingDoor.Center, false, true); hunterStepTime = 0; }
                if (stateTime >= 2.5f)
                {
                    breakingDoor.Open = breakingDoor.Broken = true; openingObjects[breakingDoor.Id].SetActive(false); doorsBroken++;
                    Event("door_broken", breakingDoor.Id.ToString()); breakingDoor = null; SetHunter(HunterState.Hunt); Repath(hunterTarget);
                }
                break;
        }
        if (Vector2.Distance(before, hunterPos) > .001f)
        {
            hunterStepTime += dt;
            var cadence = state == HunterState.Chase ? .29f : .44f;
            if (hunterStepTime > cadence)
            {
                hunterStepTime = 0;
                var hunterDistance = Vector2.Distance(playerPos, hunterPos);
                HunterSound(hunterPos, .36f + Mathf.Clamp01(1f - hunterDistance / 24f) * (state == HunterState.Chase ? .64f : .40f));
            }
        }
        if (Vector2.Distance(hunterPos, playerPos) < .62f && level.LineOfSight(hunterPos, playerPos)) End(false);
    }
    bool Follow(float speed, float dt)
    {
        if (path.Count == 0) return true;
        var next = path[0]; if (!level.CanHunterTraverse(next)) { Repath(hunterTarget); return false; }
        var o = level.OpeningOf(next);
        if (o != null && o.Kind == OpeningKind.Door && !o.Open) { breakingDoor = o; SetHunter(HunterState.BreakDoor); hunterStepTime = .5f; return false; }
        var goal = FrontRoomsLevel.CenterOf(next); hunterPos = Vector2.MoveTowards(hunterPos, goal, speed * dt);
        if (Vector2.Distance(hunterPos, goal) < .04f) path.RemoveAt(0);
        return path.Count == 0;
    }
    void UpdateHud()
    {
        bool play = phase == Phase.Playing;
        if (play)
            gameplayHudAlpha = Mathf.MoveTowards(gameplayHudAlpha, 1f, Time.unscaledDeltaTime / GameplayHudFadeSeconds);
        else
            gameplayHudAlpha = 0f;
        ApplyGameplayHudAlpha();
        if (streamedPlay)
        {
            var streamRule = roomStream == null ? RoomRule.Lobby : roomStream.CurrentRule;
            var streamName = streamRule == RoomRule.Office ? "LEVEL 4 / OFFICE" : streamRule == RoomRule.Run ? "LEVEL ! / RUN" : streamRule == RoomRule.Shift ? "LEVEL 0 / SHIFT" : streamRule == RoomRule.Exit ? "EXIT / COLD THRESHOLD" : "LOBBY / THRESHOLD";
            var streamLabel = streamThreatState == StreamThreatState.Chase ? "RELAY  /  CHASE" : streamThreatState == StreamThreatState.Listening ? "RELAY  /  LISTEN" : streamThreatState == StreamThreatState.Lost ? "RELAY  /  LOST" : "DOOR  /  LISTEN";
            roomMetaText.text = play ? "ROOM " + ((roomStream == null ? 0 : roomStream.CurrentRoomNumber) + 1).ToString("00") + "  /  ACTIVE" : "";
            roomText.text = play ? streamName : "";
            threatStateText.text = play ? streamLabel : "";
            distanceText.text = play && streamThreatTriggered && streamThreatObject != null && streamThreatObject.activeSelf ? "RELAY  " + Mathf.RoundToInt(Vector2.Distance(new Vector2(cam.transform.position.x, cam.transform.position.z), streamThreatPos)) + " M" : "";
            crosshair.enabled = play;
            contextText.text = "";
            notebook.text = "";
            if (journalPanel != null) journalPanel.SetActive(false);
            if (roomPanel != null) roomPanel.SetActive(play);
            if (threatPanel != null) threatPanel.SetActive(play);
            if (contextPanel != null) contextPanel.SetActive(false);
            return;
        }
        roomMetaText.text = play ? "ROOM " + (room.Id + 1).ToString("00") + "  /  ACTIVE" : "";
        roomText.text = play ? Name(room).ToUpperInvariant() : "";
        var hunterDistance = Mathf.RoundToInt(Vector2.Distance(playerPos, hunterPos));
        var hunterLabel = !released ? "QUIET" : state.ToString().ToUpperInvariant();
        threatStateText.text = play ? "THREAT  /  " + hunterLabel : "";
        distanceText.text = play ? (released ? "HUNTER  " + hunterDistance + " M" : "HUNTER  /  OUT OF RANGE") : "";
        crosshair.enabled = play && !journal;
        contextText.text = "";
        notebook.text = "";
        if (journalPanel != null) journalPanel.SetActive(play && journal);
        if (roomPanel != null) roomPanel.SetActive(play && !journal);
        if (threatPanel != null) threatPanel.SetActive(play && !journal);
        if (contextPanel != null) contextPanel.SetActive(false);
        if (!play) return;
        if (journal)
        {
            notebook.text = "<size=20><b>NOTES</b></size>\n\n";
            foreach (var r in level.Rooms) if (r.Read) notebook.text += Name(r) + "\n" + r.RuleText + "\n\n";
            if (notesRead == 0) notebook.text += "No notes yet.\n\n";
            notebook.text += "<size=13>Tab  CLOSE    /    THE HUNTER KEEPS MOVING</size>";
            return;
        }
        var o = NearOpening();
        if (o != null)
        {
            if (o.Kind == OpeningKind.Door) contextText.text = keys.Contains(o.Owner.Id) ? "E  /  OPEN DOOR" : "LOCKED  /  FIND THE OFFICE KEY";
            else contextText.text = actionTime > 0 ? "BREAKING GLASS  /  " + Mathf.RoundToInt(actionTime * 100f) + "%" : "HOLD E  /  BREAK GLASS";
        }
        else if (noteObjects.ContainsKey(room.Id) && !room.Read && Looking(FrontRoomsLevel.CenterOf(room.TellTile), 2f))
            contextText.text = actionTime > 0 ? "READING  /  " + Mathf.RoundToInt(actionTime / 1.5f * 100f) + "%" : "HOLD E  /  READ NOTE";
        else if (flashTime > 0) contextText.text = flash;
        if (contextPanel != null) contextPanel.SetActive(play && contextText.text != "");
    }
    void ApplyGameplayHudAlpha()
    {
        if (roomHudGroup != null) roomHudGroup.alpha = gameplayHudAlpha;
        if (threatHudGroup != null) threatHudGroup.alpha = gameplayHudAlpha;
        if (contextHudGroup != null) contextHudGroup.alpha = gameplayHudAlpha;
        if (crosshairHudGroup != null) crosshairHudGroup.alpha = gameplayHudAlpha;
    }
    string Name(FrontRoom r) => r.Rule == RoomRule.Lobby ? "Lobby" : r.Rule == RoomRule.Shift ? "Level 0" : r.Rule == RoomRule.Office ? "Level 4 / Office" : r.Rule == RoomRule.Run ? "Level ! / Run" : "Exit";
    void Flash(string message, float duration = 3f) { flash = message; flashTime = duration; }
    void Event(string kind, string detail) { events.Add(elapsed.ToString("0.000", CultureInfo.InvariantCulture) + "," + kind + ",\"" + detail.Replace("\"", "\"\"") + "\"," + Vector2.Distance(playerPos, hunterPos).ToString("0.00", CultureInfo.InvariantCulture)); }
    void End(bool escaped)
    {
        if (phase != Phase.Playing) return;
        SetPhase(escaped ? Phase.Escaped : Phase.Caught); Sound(escaped ? escapeClip : caughtClip, playerPos); Event("outcome", escaped ? notesRead == 3 && keys.Count > 0 ? "informed" : "fast" : "caught");
        string dir = testDir ?? Application.persistentDataPath; Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, "events-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".csv"), "time_s,event,detail,hunter_m\n" + string.Join("\n", events));
        Log(phase + " · " + elapsed.ToString("0.0") + " s");
    }
    static void Log(string message) => Debug.Log("[FrontRooms3D] " + message);

    IEnumerator WalkTo(Vector2 target, bool run = true)
    {
        float timeout = 0; testRun = run;
        while (phase == Phase.Playing && Vector2.Distance(playerPos, target) > .12f && timeout < 14f)
        {
            var delta = target - playerPos; testMove = delta; yaw = Mathf.Atan2(delta.x, delta.y) * Mathf.Rad2Deg; pitch = 0;
            timeout += Time.deltaTime; yield return null;
        }
        testMove = Vector2.zero; testRun = false;
        if (timeout >= 14f) { testFailed = true; Log("MOVE TIMEOUT " + playerPos + " -> " + target); }
    }
    IEnumerator HoldAt(Vector2 target, float seconds)
    {
        var delta = target - playerPos; yaw = Mathf.Atan2(delta.x, delta.y) * Mathf.Rad2Deg; pitch = 0; testInteract = true;
        yield return new WaitForSeconds(seconds); testInteract = false; yield return null;
    }
    [Serializable] sealed class Report { public bool passed; public string route, outcome, evidence; public int notes, keys, windows, breachedDoors, transitions, shifts; public float seconds; }
    IEnumerator VerifyRoute()
    {
        yield return null; StartGame();
        if (testRoute == "caught") yield return new WaitForSeconds(16f);
        else
        {
            if (testRoute == "door") { yield return WalkTo(new Vector2(7.3f, 5.5f)); yield return HoldAt(new Vector2(8.5f, 5.5f), 1.6f); }
            yield return WalkTo(new Vector2(10.5f, 3.5f)); yield return WalkTo(new Vector2(14f, 3.5f));
            if (testRoute == "door") { yield return WalkTo(new Vector2(16.2f, 5.5f)); yield return HoldAt(new Vector2(17.5f, 5.5f), 1.6f); }
            var gate = level.Openings[2].Sealed ? level.Openings[3] : level.Openings[2];
            yield return WalkTo(new Vector2(22.5f, gate.Center.y)); yield return WalkTo(new Vector2(26.5f, gate.Center.y));
            if (testRoute == "door")
            {
                yield return WalkTo(new Vector2(26.5f, 5.5f)); yield return HoldAt(new Vector2(29.5f, 5.5f), .05f);
                // Approach the note from the front lane, outside the physical desk volumes.
                yield return WalkTo(new Vector2(29.5f, 4.35f)); yield return HoldAt(new Vector2(29.5f, 5.5f), 1.6f);
                yield return WalkTo(new Vector2(26.5f, 4.3f)); yield return WalkTo(new Vector2(26.5f, 8.5f)); yield return WalkTo(new Vector2(33.5f, 8.5f));
                yield return WalkTo(new Vector2(35.4f, 8.5f)); yield return WalkTo(new Vector2(35.4f, 3f)); yield return HoldAt(level.Openings[4].Center, .15f);
                yield return WalkTo(new Vector2(39f, 3f));
                float wait = 0; while (phase == Phase.Playing && state != HunterState.BreakDoor && wait < 30f) { wait += Time.deltaTime; yield return null; }
                if (wait >= 30f) testFailed = true;
            }
            else
            {
                yield return WalkTo(new Vector2(26.5f, 8f)); yield return WalkTo(new Vector2(35.4f, 8f)); yield return HoldAt(level.Openings[5].Center, 1.1f); yield return WalkTo(new Vector2(39f, 8f));
            }
            yield return WalkTo(new Vector2(47.35f, 5f)); yield return HoldAt(level.Openings[6].Center, 1.1f); yield return WalkTo(new Vector2(51f, 5f)); yield return WalkTo(new Vector2(57.5f, 5f));
        }
        bool expected = testRoute == "caught" ? phase == Phase.Caught : phase == Phase.Escaped && transitions == 4 && windowsBroken >= (testRoute == "door" ? 1 : 2);
        if (testRoute == "door") expected &= notesRead == 3 && keys.Count == 1 && doorsBroken >= 1;
        if (testRoute == "fast") expected &= notesRead == 0 && keys.Count == 0;
        var report = new Report { passed = !testFailed && expected, route = testRoute, outcome = phase.ToString(), notes = notesRead, keys = keys.Count, windows = windowsBroken, breachedDoors = doorsBroken, transitions = transitions, shifts = shifts, seconds = elapsed, evidence = "Scripted runtime interaction and pursuit checks. Mouse look, audio quality, and human playability require separate inspection." };
        File.WriteAllText(Path.Combine(testDir, "result.json"), JsonUtility.ToJson(report, true));
        Log("VERIFY " + (report.passed ? "PASS" : "FAIL")); yield return new WaitForSeconds(.1f); Application.Quit(report.passed ? 0 : 1);
    }
}
