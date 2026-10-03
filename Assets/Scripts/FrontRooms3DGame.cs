using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using FrontRooms.Map;
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
// First-person FrontRooms. The title is the looping room stream; when the
// player presses Space they take over where the camera is, the stream stops
// at its next shut door, and the generated Level 0 maze (FrontRoomsMapWorld)
// lies behind that door. There the serialized Relay hunts them
// (FrontRoomsMapHunter).
public sealed class FrontRooms3DGame : MonoBehaviour
{
    enum Phase { Title, Playing, Paused, Caught }
    Phase phase;
    Camera cam;
    [SerializeField, Tooltip("The Relay rig serialized in this scene. It stays hidden until the hunter is released.")]
    Transform hunter;
    [SerializeField, Tooltip("When the Relay is released, how it listens, hunts, searches, chases and breaks doors.")]
    FrontRoomsHunterTuning hunterTuning = new FrontRoomsHunterTuning();
    /// <summary>A map run began (the player took over in the title's stream room): the map and the Relay exist. For listeners such as the sound layer.</summary>
    public static event Action<FrontRoomsMapWorld, FrontRoomsMapHunter> MapRunStarted;
    /// <summary>The map run is torn down (restart reloads the scene, or Play stops).</summary>
    public static event Action MapRunEnded;
    /// <summary>The player started climbing through a broken window, at its opening.</summary>
    public static event Action<Vector3> PlayerClimbed;

    [SerializeField, Tooltip("The Level 0 maze's numbers: generation, run seed, streaming, light budget, dressing (Assets/Levels/FrontRoomsLevel0.asset). Empty: the code defaults.")]
    FrontRoomsLevelProfile levelProfile;
    FrontRoomsRelayRig hunterRig;
    FrontRoomsMapWorld map;
    FrontRoomsMapHunter relay;
    Transform playerRoot;
    CharacterController playerBody;
    Vector2 playerPos;
    readonly List<string> events = new List<string>();
    Material wallMat, floorMat, darkMat, ceilingMat;
    readonly Dictionary<RoomRule, Material> wallMats = new Dictionary<RoomRule, Material>();
    readonly Dictionary<RoomRule, Material> floorMats = new Dictionary<RoomRule, Material>();
    readonly Dictionary<RoomRule, Material> ceilingMats = new Dictionary<RoomRule, Material>();
    Material trimMat, fixtureMat;
    AudioSource hum;
    AudioClip playerStepClip, playerRunStepClip, hunterStepClip, doorClip, bangClip, caughtClip;
    FrontRoomsFoley foley;
    Text roomMetaText, roomText, threatStateText, distanceText, contextText, overlayText, keyText, displaySettingsText;
    Image crosshairImage, keyImage;
    Text promptText;
    Image holdBarFill;
    GameObject holdBar;
    readonly Image[] staminaSegments = new Image[5];
    GameObject keyPanel;
    Image logoImage;
    Image logoLeftImage, logoSlideImage;
    Transform logoMotionRoot;
    UiDocument vectorLogoDocument;
    UiVisualElement vectorLogoRoot;
    UiImage vectorLogoLeftImage, vectorLogoS1Image, vectorLogoS2Image;
    UiVectorImage vectorLogoLeftAsset, vectorLogoS1Asset, vectorLogoS2Asset;
    readonly List<UiVisualElement> vectorLogoLetterMasks = new List<UiVisualElement>();
    readonly List<float> vectorLogoLetterWidths = new List<float>();
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
    GameObject overlay, roomPanel, threatPanel, contextPanel, displaySettingsPanel;
    CanvasGroup roomHudGroup, threatHudGroup, contextHudGroup, crosshairHudGroup, keyHudGroup;
    Image overlayImage;
    Outline logoOutline;
    Transform titleWorld;
    FrontRoomsRoomStream roomStream;
    [SerializeField, Tooltip("Optional room prefab/template copied into each streamed title room.")]
    GameObject streamedRoomTemplate;
    float titleLogoAlpha;
    float logoMotionElapsed;
    // The wordmark fades out over the first moments of play instead of vanishing.
    bool logoFading;
    const float LogoExitSeconds = .55f;
    bool mapPlay;
    // The run starts in the title's stream rooms (the map's start area). The
    // door out of them opens once the map behind it is built, and shuts for
    // good once the player is well into the map; then the rooms go dark and,
    // when the map has dropped every chunk round them, they are removed.
    bool inStartRooms, leftStartRooms, startDoorOpened;
    GridCoord startDoorCell;
    Vector3 startDoorPoint;
    Light[] streamLights;
    float[] streamLightLevels;
    float streamFade = -1f, startRearZ, startDoorHeldFor;
    // The door opens once the map in sight through it is built and
    // furnished, and never later than this after Space.
    const float StreamFadeSeconds = 1.2f, StartDoorShutDistance = 4f, StartDoorHoldLimit = 3f, StartLampsRiseSeconds = .6f;
    // The stream rooms take a 5-cell (15 m) strip of the map: the 11.76 m room plus the gaps to the map's walls.
    const int StartAreaHalfCells = 2;
    // The title camera's drift, eased out when the player takes over, so control does not start with a jolt.
    Vector3 glide;
    const float GlideSeconds = .6f;
    // Cursor lock can report one large mouse delta: ignore the first frames of play.
    int mouseSettleFrames;
    // The runtime stream runs on its own centerline, clear of the edit-mode
    // profile preview at X = 0. It sits on a map cell centre (3 m cells from
    // world 0, so x ≡ 1.5 mod 3): the stream door then opens onto one cell of
    // the map the run continues in.
    public const float TitleCenterX = 256.5f;
    const string EditorPreviewName = "EDITOR_PREVIEW / Room profiles (generated)";
    const float LogoScale = .75f;
    // The trailing S forms are deliberately sequenced instead of sharing the
    // same reveal clock: the near afterimage settles first, then the far one
    // pushes out to create the depth trail in the wordmark.
    const float LogoS1SettleAt = .58f;
    // Start the far afterimage while the near S is in its final approach.
    // The relay is intentionally earlier than the near S settle point so the
    // two forms overlap in motion instead of waiting for a hard hand-off.
    const float LogoS2StartAt = .50f;
    const float GameplayHudFadeSeconds = .9f;
    const string CalmHint = "Shift to sprint. About 5 seconds, and it hears every step.";
    const float CalmHintSeconds = 9f;
    float gameplayHudAlpha;
    float yaw, pitch, elapsed, stepTime, hunterStepTime, flashTime;
    string flash = "";
    const float Walk = 3.2f, Run = 5.5f;
    // Sprint stamina: about 5 s of running, refilling after a 1 s breather.
    const float StaminaSeconds = 5f, StaminaRecoverDelay = 1f, StaminaRecoverRate = 1f;
    const float EyeHeight = ModuleUnits.PlayerEye, Reach = 2.4f, GlassNoiseRadius = 40f;
    float stamina = StaminaSeconds, sinceSprint, fallSpeed;
    // Climbing through a broken window: the sill (0.35 m) is above the step
    // height and the opening (1.65 m) is lower than the player, so walking
    // into the frame vaults through it, ducking under the head.
    const float ClimbSeconds = .6f, ClimbLift = .35f, ClimbDuck = .55f;
    float climbTime = -1f;
    Vector3 climbFrom, climbTo;
    Collider aimed;
    bool aimedHold;
    float holdProgress;
    string prompt;
    readonly HashSet<GridCoord> zonesVisited = new HashSet<GridCoord>();
    GridCoord currentZone;
    int keysTaken, runSeed;
    static bool restart;

    void OnEnable()
    {
        // Edit mode shows the generator itself: one room per profile, built by
        // the same code as the runtime pool. Play Mode builds the live stream
        // instead, so the preview is never saved into the scene or a build.
        if (!Application.isPlaying) BuildEditorPreview();
    }

    void OnDisable()
    {
        if (!Application.isPlaying) DestroyEditorPreview();
    }

    void BuildEditorPreview()
    {
        DestroyEditorPreview();
        BuildMaterials();
        var preview = new GameObject(EditorPreviewName);
        preview.transform.SetParent(transform, false);
        var stream = preview.AddComponent<FrontRoomsRoomStream>();
        stream.roomTemplate = streamedRoomTemplate;
        stream.BuildEditorPreview(WallMaterial(RoomRule.Lobby), FloorMaterial(RoomRule.Lobby), CeilingMaterial(RoomRule.Lobby), trimMat, fixtureMat, darkMat,
            ProfileMaterials(wallMats), ProfileMaterials(floorMats), ProfileMaterials(ceilingMats));
        foreach (var child in preview.GetComponentsInChildren<Transform>(true))
            child.gameObject.hideFlags = HideFlags.DontSave;
    }

    void DestroyEditorPreview()
    {
        for (var i = transform.childCount - 1; i >= 0; i--)
        {
            var child = transform.GetChild(i).gameObject;
            if (child.name != EditorPreviewName) continue;
            if (Application.isPlaying) Destroy(child);
            else DestroyImmediate(child);
        }
    }

    static Material[] ProfileMaterials(Dictionary<RoomRule, Material> materials)
    {
        var profiles = (RoomRule[])Enum.GetValues(typeof(RoomRule));
        var result = new Material[profiles.Length];
        for (var i = 0; i < profiles.Length; i++) materials.TryGetValue(profiles[i], out result[i]);
        return result;
    }

    void InitializeFonts()
    {
        var fallback = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        monoFont = Resources.Load<Font>("Fonts/IBMPlexMono-Regular") ?? fallback;
        bayonFont = Resources.Load<Font>("Fonts/Bayon-Regular") ?? fallback;
        serifFont = Resources.Load<Font>("Fonts/SourceSerif4-Variable") ?? fallback;
    }

    /// <summary>The scene's first-person camera, used by Create Scene and as a runtime fallback.</summary>
    public static Camera CreateCamera(Transform parent)
    {
        var camera = new GameObject("First-person camera").AddComponent<Camera>();
        camera.transform.SetParent(parent, false);
        camera.transform.localPosition = new Vector3(TitleCenterX, 1.62f, 0f);
        camera.fieldOfView = 76f; camera.nearClipPlane = .06f; camera.farClipPlane = 80f;
        camera.allowHDR = true;
        camera.allowMSAA = true;
        camera.useOcclusionCulling = true;
        camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = C("22231C"); camera.gameObject.AddComponent<AudioListener>();
        FrontRoomsPostStack.ConfigureCamera(camera);
        return camera;
    }

    // A standalone player can restore a serialized camera's enabled/viewport
    // state from an earlier editor session or a display-mode change. Keep the
    // runtime output deterministic: one active camera, full screen viewport,
    // and no off-screen target texture. This is intentionally a no-op for the
    // normal scene camera and does not alter its lens, clipping, or rendering
    // quality settings.
    static void EnsureRuntimeCamera(Camera camera)
    {
        if (camera == null) return;
        if (!camera.gameObject.activeSelf) camera.gameObject.SetActive(true);
        camera.enabled = true;
        camera.rect = new Rect(0f, 0f, 1f, 1f);
        camera.targetTexture = null;
    }

    /// <summary>The serialized Relay: an editable rig that the hunter brain drives at runtime.</summary>
    public static Transform CreateHunter(Transform parent)
    {
        var relay = new GameObject("Hunter").transform;
        relay.SetParent(parent, false);
        relay.gameObject.AddComponent<FrontRoomsRelayRig>().Configure(Mat("Relay / body", C("2B2928")), Mat("Relay / blank head", C("D8D4C8")), Mat("Relay / detail", C("A99E78")));
        return relay;
    }

    /// <summary>
    /// Scene lighting for a fresh scene. Kept out of Awake so lighting tuned in
    /// the editor's Lighting window survives into Play Mode and builds.
    /// </summary>
    public static void ApplySceneLighting(Transform parent)
    {
        // Trilight bounce and haze shared with the maze and the shipped scene;
        // it also rebuilds URP's ambient probe, without which they do nothing.
        FrontRoomsLook.ApplyAmbient();
        var fill = new GameObject("Soft ambient direction").AddComponent<Light>();
        fill.transform.SetParent(parent);
        fill.type = LightType.Directional; fill.intensity = .22f; fill.color = C("D6D3B4");
        fill.shadows = LightShadows.Soft;
        fill.shadowStrength = .18f;
        fill.shadowBias = .045f;
        fill.shadowNormalBias = .28f;
        fill.shadowNearPlane = .1f;
        fill.transform.rotation = Quaternion.Euler(70f, -30f, 0f);
    }

    void BindHunter()
    {
        if (hunter == null) hunter = transform.Find("Hunter");
        if (hunter == null) hunter = CreateHunter(transform);
        hunterRig = hunter.GetComponent<FrontRoomsRelayRig>();
        hunter.gameObject.SetActive(false);
    }

    void Awake()
    {
        if (!Application.isPlaying) return;

        Application.targetFrameRate = 60;
        // Full-resolution textures; MSAA, HDR and shadows come from the URP
        // pipeline asset (Assets/Settings/FrontRooms_URP).
        QualitySettings.globalTextureMipmapLimit = 0;
        Time.timeScale = 1f;
        DestroyEditorPreview();
#if UNITY_EDITOR
        AutopilotStart();
#endif
        // URP lights surfaces with the ambient probe, which is only rebuilt
        // from the scene's ambient colours on a bake or here.
        DynamicGI.UpdateEnvironment();
        InitializeFonts();
        cam = GetComponentInChildren<Camera>(true);
        if (cam == null) cam = CreateCamera(transform);
        EnsureRuntimeCamera(cam);
        FrontRoomsPostStack.ConfigureCamera(cam);
        FrontRoomsPostStack.Ensure(transform);
        BindHunter();
        BuildMaterials();
        hdrEnabled = PlayerPrefs.GetInt(HdrPreferenceKey, defaultHdr ? 1 : 0) != 0;
        ApplyHdrMode(hdrEnabled, false);
        BuildHud();
        BuildSound();
        // The map's first-use loads happen now, before the first frame, not
        // in the frames after Space while the player is watching.
        FrontRoomsMapWorld.Prewarm();
        BuildTitleCorridor();
        SetPhase(Phase.Title);
        if (restart)
        {
            restart = false;
            StartCanonicalStreamedRestart();
        }
        Log("READY · manual title, first-person · display " + Screen.width + "x" + Screen.height
            + " " + Screen.fullScreenMode + " · camera " + (cam != null && cam.enabled ? "active" : "missing"));
    }

    static Color C(string hex) { ColorUtility.TryParseHtmlString("#" + hex, out var c); return c; }
    static Vector3 V(Vector2 p, float y = 0f) => new Vector3(p.x, y, p.y);
    static Material Mat(string name, Color color, bool emission = false)
        => FrontRoomsSurfaces.Lit(name, color, .12f, 0f, emission ? color * .8f : (Color?)null);

    Material WallMaterial(RoomRule rule) => wallMats.TryGetValue(rule, out var m) ? m : wallMat;
    Material FloorMaterial(RoomRule rule) => floorMats.TryGetValue(rule, out var m) ? m : floorMat;
    Material CeilingMaterial(RoomRule rule) => ceilingMats.TryGetValue(rule, out var m) ? m : ceilingMat;

    /// <summary>
    /// The room profile palette, read from the editable surface materials in
    /// Resources/Surfaces: Level 0 chevron paper, loop-pile carpet and 2'x4'
    /// tiles for Lobby/Shift/Exit; drywall, carpet tiles and 2'x2' tiles for
    /// the Office; the white hospital corridor for Run.
    /// </summary>
    void BuildMaterials()
    {
        wallMats.Clear(); floorMats.Clear(); ceilingMats.Clear();
        foreach (RoomRule rule in Enum.GetValues(typeof(RoomRule)))
        {
            wallMats[rule] = FrontRoomsSurfaces.Room(rule, FrontRoomsSurfaces.Slot.Wall);
            floorMats[rule] = FrontRoomsSurfaces.Room(rule, FrontRoomsSurfaces.Slot.Floor);
            ceilingMats[rule] = FrontRoomsSurfaces.Room(rule, FrontRoomsSurfaces.Slot.Ceiling);
        }
        wallMat = wallMats[RoomRule.Lobby];
        floorMat = floorMats[RoomRule.Lobby];
        ceilingMat = ceilingMats[RoomRule.Lobby];
        trimMat = FrontRoomsSurfaces.CoveBase;
        fixtureMat = FrontRoomsSurfaces.TrofferLens;
        darkMat = FrontRoomsSurfaces.DoorVeneer;
    }

    void BuildTitleCorridor()
    {
        // Fast Enter Play Mode can preserve the previous generated stream.
        // Rebuild it so the title always starts with a fresh wipe/relay clock.
        if (titleWorld != null) StopTitleCorridor();
        titleWorld = new GameObject("Title sequence / recycled corridor").transform;
        // The camera stays in the same generated room through the handoff;
        // the room it is in when Space is pressed is where play starts. Z 0
        // puts every room boundary on a multiple of 3 m (rooms are 12 m,
        // starting 6 m behind the camera), so the door the map is attached
        // behind always lies on a map cell line.
        if (cam != null)
        {
            cam.transform.position = new Vector3(TitleCenterX, EyeHeight, 0f);
            cam.transform.rotation = Quaternion.identity;
        }
        roomStream = titleWorld.gameObject.AddComponent<FrontRoomsRoomStream>();
        roomStream.roomTemplate = streamedRoomTemplate;
        roomStream.Initialize(cam, WallMaterial(RoomRule.Lobby), FloorMaterial(RoomRule.Lobby), CeilingMaterial(RoomRule.Lobby), trimMat, fixtureMat, darkMat,
            foley == null ? doorClip : foley.Doors.hinge,
            foley == null ? null : foley.Doors.latch,
            foley == null ? null : foley.Doors.travel,
            ProfileMaterials(wallMats), ProfileMaterials(floorMats), ProfileMaterials(ceilingMats));
        titleLogoAlpha = 0f;
        logoMotionElapsed = 0f;
        logoFading = false;
        mapPlay = false;
        if (cam != null) cam.transform.rotation = Quaternion.identity;
    }

    void UpdateTitleSequence(float dt)
    {
        if (roomStream == null || cam == null) return;
        roomStream.Tick(dt);
        // Historical title clock: the complete wordmark stays present while
        // the first streamed door drives the two trailing-S relays.
        logoMotionElapsed += dt;
        titleLogoAlpha = roomStream.LogoVisibility;
        UpdateLogoMotion();
    }

    // The wordmark shows on the title and while it fades out as play starts.
    bool LogoShown => phase == Phase.Title || logoFading;

    void UpdateLogoFade(float dt)
    {
        titleLogoAlpha = Mathf.MoveTowards(titleLogoAlpha, 0f, dt / LogoExitSeconds);
        if (titleLogoAlpha <= 0f) logoFading = false;
        UpdateLogoMotion();
    }

    void UpdateLogoMotion()
    {
        if (vectorLogoActive)
        {
            var vectorVisible = LogoShown;
            if (vectorLogoRoot != null) vectorLogoRoot.style.display = vectorVisible ? UiDisplayStyle.Flex : UiDisplayStyle.None;
            if (!vectorVisible || vectorLogoLeftImage == null || vectorLogoS1Image == null || vectorLogoS2Image == null) return;

            // Historical 11:53 title motion: the complete wordmark is
            // stationary and the two afterimage S forms relay from the final
            // S as the first streamed door opens. The later per-letter wipe is
            // intentionally disabled; room/gameplay systems are unchanged.
            var doorProgress = roomStream == null ? 0f : roomStream.FirstDoorProgress;
            var s1End = logoMotionVariation == LogoMotionVariation.FullLockup ? .66f : LogoS1SettleAt;
            var s2Start = logoMotionVariation == LogoMotionVariation.FullLockup ? .70f : LogoS2StartAt;
            var vectorS1T = Mathf.Clamp01(doorProgress / s1End);
            vectorS1T = vectorS1T * vectorS1T * (3f - 2f * vectorS1T);
            var vectorS2T = Mathf.Clamp01((doorProgress - s2Start) / (1f - s2Start));
            vectorS2T = vectorS2T * vectorS2T * (3f - 2f * vectorS2T);
            // VectorImage assets are imported at their painted bounds (about
            // 78px wide), so their CSS left value is already the visible
            // glyph position. Do not subtract the original SVG viewBox x
            // coordinates here; that would move both afterimages to the
            // far-left edge of the wordmark.
            var vectorS1X = Mathf.Lerp(798f, 842f, vectorS1T);
            // The far S follows the first afterimage until the relay point,
            // then continues from the first S's actual position at that point.
            // This keeps the earlier hand-off continuous and preserves the
            // intended left-to-right depth relationship.
            var s2StartS1T = Mathf.Clamp01(s2Start / s1End);
            s2StartS1T = s2StartS1T * s2StartS1T * (3f - 2f * s2StartS1T);
            // Historical relay baseline: the far S starts from the current
            // first-S position at the handoff, not from a second, tighter
            // offset. This keeps the two trailing glyphs evenly tracked.
            var vectorS2StartX = Mathf.Lerp(798f, 842f, s2StartS1T);
            var vectorS2X = doorProgress < s2Start
                ? vectorS1X
                : Mathf.Lerp(vectorS2StartX, 880f, vectorS2T);
            vectorLogoS1Image.style.left = new UiLength(vectorS1X, UiLengthUnit.Pixel);
            vectorLogoS2Image.style.left = new UiLength(vectorS2X, UiLengthUnit.Pixel);
            // Keep the vector mark on the same fade-in clock as the title
            // corridor. It remains at full opacity after the reveal; the
            // player handoff fades it out (UpdateLogoFade).
            var vectorAlpha = Mathf.Clamp01(titleLogoAlpha);
            vectorLogoLeftImage.style.opacity = vectorAlpha;
            vectorLogoS1Image.style.opacity = vectorAlpha;
            vectorLogoS2Image.style.opacity = vectorAlpha;
            return;
        }
        if (logoMotionRoot == null || logoLeftImage == null || logoSlideImage == null) return;
        var visible = LogoShown;
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
    }

    void RequestTitleStart()
    {
        if (mapPlay || roomStream == null || cam == null) return;
        StartRunInPlace();
    }

    void StartCanonicalStreamedRestart()
    {
        if (roomStream == null) return;
        SetPhase(Phase.Title);
        // A retry starts in the title's first room with a fresh maze (or the
        // same one when Map Seed is set) behind its door, like a first run.
        RequestTitleStart();
        // The title never crawled here, so there is no drift to ease out.
        glide = Vector3.zero;
        Log("RESTART · in the first stream room, maze behind its door");
    }

    /// <summary>
    /// Space on the title. The player takes over where the camera is, in the
    /// stream room they are watching: no glide to an anchor and no white-out.
    /// The stream ends at its first door that is still shut (nothing past it
    /// has been seen), and the Level 0 map is attached behind that door:
    /// placed so the door opens onto one of its cells, with the stream rooms
    /// left out of it as its start area. The map fills in at the normal
    /// streaming budget, round the door first, and the door stays shut until
    /// it is built and furnished, so nothing is ever built in view.
    /// </summary>
    void StartRunInPlace()
    {
        var terminal = roomStream.FirstClosedDoorSequence();
        if (terminal < 0)
        {
            Log("START · no shut stream door is loaded yet");
            return;
        }
        var watch = System.Diagnostics.Stopwatch.StartNew();
        var profile = levelProfile != null ? levelProfile : FrontRoomsLevelProfile.Default;
        runSeed = profile.runSeed != 0 ? profile.runSeed : UnityEngine.Random.Range(1, int.MaxValue);
#if UNITY_EDITOR
        if (autopilot && autopilotSeed != 0) runSeed = autopilotSeed;
#endif
        map = FrontRoomsMapWorld.CreateEmbedded(transform, profile, runSeed);
        var createMs = watch.Elapsed.TotalMilliseconds;

        // The door line is a map cell line and the stream centreline a cell
        // centre (BuildTitleCorridor, TitleCenterX), so the door opens onto
        // one cell; the stream rooms take the 5-cell strip behind it.
        var centerX = roomStream.CenterX;
        var doorZ = roomStream.RoomStartZ(terminal) + FrontRoomsRoomStream.RoomLength;
        var rearZ = roomStream.RoomStartZ(roomStream.OldestSequence);
        var rows = Mathf.RoundToInt((doorZ - rearZ) / MapGrid.CellSize);
        map.transform.SetPositionAndRotation(MapRootFor(map, centerX, doorZ, rows), Quaternion.identity);
        var placeMs = watch.Elapsed.TotalMilliseconds - createMs;
        startDoorCell = map.CellOf(new Vector3(centerX, 0f, doorZ + MapGrid.CellSize * .5f));
        startDoorPoint = new Vector3(centerX, 0f, doorZ);
        startRearZ = rearZ;
        startDoorHeldFor = 0f;
        var rearCell = map.CellOf(new Vector3(centerX, 0f, rearZ + MapGrid.CellSize * .5f));
        map.SetStartArea(new RectInt(startDoorCell.x - StartAreaHalfCells, rearCell.y, StartAreaHalfCells * 2 + 1, startDoorCell.y - rearCell.y), startDoorCell);
        // The facade ends inside the start area's side walls (centred on the cell lines), not on their faces.
        roomStream.EndStreamAt(terminal, (StartAreaHalfCells + .5f) * MapGrid.CellSize + ModuleUnits.WallHalf - .01f);
        roomStream.TerminalDoorHeld = true;

        // The player is a capsule the camera rides on, standing where the
        // camera is. Walls and doors are colliders: the stream rooms' boxes,
        // then the map's.
        var eye = cam.transform.position;
        playerRoot = new GameObject("Player").transform;
        playerRoot.SetParent(transform, false);
        playerRoot.position = ClearStandingSpot(new Vector3(eye.x, eye.y - EyeHeight, eye.z));
        playerBody = playerRoot.gameObject.AddComponent<CharacterController>();
        playerBody.height = ModuleUnits.PlayerHeight;
        playerBody.radius = ModuleUnits.PlayerRadius;
        playerBody.center = new Vector3(0f, ModuleUnits.PlayerHeight * .5f, 0f);
        playerBody.stepOffset = .3f;
        playerBody.skinWidth = .03f;
        cam.transform.SetParent(playerRoot, false);
        cam.transform.localPosition = new Vector3(0f, EyeHeight, 0f);
        cam.transform.localRotation = Quaternion.identity;
        yaw = 0f;
        pitch = 0f;
        fallSpeed = 0f;
        climbTime = -1f;
        stamina = StaminaSeconds;
        sinceSprint = 0f;
        glide = Vector3.forward * FrontRoomsRoomStream.TitleSpeed;
        mouseSettleFrames = 2;
        inStartRooms = true;
        leftStartRooms = false;
        startDoorOpened = false;
        streamFade = -1f;
        streamLights = null;
        map.DoorMoved += OnDoorMoved;
        map.GlassBroken += OnGlassBroken;
        map.KeyTaken += OnKeyTaken;
        map.StreamFocus = map.CellCenter(startDoorCell);
        map.StartLampsNorth = 0f;
        map.StartLampsSouth = 0f;
        map.Begin(playerRoot, false);

        relay = new FrontRoomsMapHunter(map, hunterTuning, playerBody, hunter, runSeed);
        relay.StateChanged += state => Event("hunter", state.ToString());
        relay.DoorBlow += p => FoleyDoorBreak(Flat(p));
        relay.Caught += End;

        zonesVisited.Clear();
        keysTaken = 0;
        playerPos = Flat(playerRoot.position);
        elapsed = 0f;
        mapPlay = true;
        logoFading = true;
        SetPhase(Phase.Playing);
        Event("start", "map seed " + runSeed + ", stream room " + terminal);
        MapRunStarted?.Invoke(map, relay);
        Log("START · in place in stream room " + terminal + " · maze seed " + runSeed + " behind its door, map root " + map.transform.position + ", door cell " + startDoorCell
            + " · " + watch.Elapsed.TotalMilliseconds.ToString("0.0", CultureInfo.InvariantCulture) + " ms (map " + createMs.ToString("0.0", CultureInfo.InvariantCulture) + ", placing " + placeMs.ToString("0.0", CultureInfo.InvariantCulture) + ")");
    }

    /// <summary>
    /// Where the map's root goes: a multiple of 192 m (ModuleUnits.WorldPeriod,
    /// so the printed ceiling grid stays on the troffers), chosen so that the
    /// row of cells the stream door opens onto, all five across the start
    /// area, is Standard-height Level 0 (the stream room's 2.9 m ceiling and
    /// Lobby paper carry straight on), and so that the way on is straight
    /// ahead: the door's open leaves stand 1.12 m into its cell, too close to
    /// the cell's side walls to pass, so the cell's far edge must be open and
    /// lead into the maze (the stream rooms' strip of <paramref name="rows"/>
    /// cells behind the door can cut cells off from the rest of their chunk).
    /// The map is infinite and fixed by its seed; this only picks which part
    /// of it the door leads into.
    /// </summary>
    static Vector3 MapRootFor(FrontRoomsMapWorld map, float centerX, float doorZ, int rows)
    {
        var period = ModuleUnits.WorldPeriod;
        var probe = new Vector3(centerX, 0f, doorZ + MapGrid.CellSize * .5f);
        Vector3? reachable = null;
        for (var ring = 0; ring <= 24; ring++)
        for (var b = -ring; b <= ring; b++)
        for (var a = -ring; a <= ring; a++)
        {
            if (Mathf.Max(Mathf.Abs(a), Mathf.Abs(b)) != ring) continue;
            var root = new Vector3(a * period, 0f, b * period);
            var door = FrontRoomsMapWorld.CellAt(probe - root);
            var area = new RectInt(door.x - StartAreaHalfCells, door.y - rows, StartAreaHalfCells * 2 + 1, rows);
            var standard = true;
            for (var dx = -StartAreaHalfCells; dx <= StartAreaHalfCells && standard; dx++)
            {
                var zone = map.ZoneOf(new GridCoord(door.x + dx, door.y));
                standard = zone.height == ZoneHeight.Standard && zone.theme == ZoneTheme.Level0;
            }
            if (!standard && reachable.HasValue) continue;
            var ahead = new GridCoord(door.x, door.y + 1);
            var onward = map.Cache.Edge(door, ahead);
            if (onward == EdgeKind.Wall || onward == EdgeKind.Window || !LeadsIntoMaze(map.Cache, ahead, area, door)) continue;
            if (standard) return root;
            reachable = root;
        }
        Log("START · no Standard Level 0 row found for the stream door" + (reachable.HasValue ? "; using one that only leads on" : "; the map stays at the origin"));
        return reachable ?? Vector3.zero;
    }

    static readonly GridCoord[] Steps4 = { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) };

    /// <summary>
    /// From <paramref name="start"/>, through anything but a wall and never
    /// back into the door cell or the start area, the walk reaches a good
    /// part of the maze (150 cells; a pocket cut off by the strip is far smaller).
    /// </summary>
    static bool LeadsIntoMaze(FrontRoomsMapCache cache, GridCoord start, RectInt area, GridCoord door)
    {
        var seen = new HashSet<GridCoord> { start, door };
        var queue = new Queue<GridCoord>();
        queue.Enqueue(start);
        while (queue.Count > 0)
        {
            var cell = queue.Dequeue();
            foreach (var step in Steps4)
            {
                var next = cell + step;
                if (seen.Contains(next) || area.Contains(new Vector2Int(next.x, next.y))) continue;
                if (cache.Edge(cell, next) == EdgeKind.Wall) continue;
                seen.Add(next);
                if (seen.Count >= 150) return true;
                queue.Enqueue(next);
            }
        }
        return false;
    }

    /// <summary>
    /// Feet under the camera, unless the body would stand in a door leaf or
    /// return there; then the nearest clear spot back along the corridor.
    /// </summary>
    static Vector3 ClearStandingSpot(Vector3 feet)
    {
        Physics.SyncTransforms();
        var r = ModuleUnits.PlayerRadius;
        for (var step = 0; step <= 30; step++)
        {
            var p = feet + Vector3.back * (step * .1f);
            // Above the floor and below the ceiling: only walls and doors count.
            if (!Physics.CheckCapsule(p + Vector3.up * (r + .2f), p + Vector3.up * (ModuleUnits.PlayerHeight - r), r, ~0, QueryTriggerInteraction.Ignore))
                return p;
        }
        return feet;
    }

    /// <summary>
    /// The stream rooms the run starts in. Their door into the map opens once
    /// the map behind it is ready; leaving them hands the camera the map's
    /// sight distance. Once the player is well into the map the door swings
    /// shut for good (the Relay is let loose from then on), the rooms' lamps
    /// fade out, and when the map has dropped every chunk round them they are
    /// removed and the map takes the ground back.
    /// </summary>
    void UpdateStartRooms(float dt)
    {
        if (roomStream == null) return;
        var feet = playerRoot.position;
        var inside = map.InStartArea(map.CellOf(feet));
        if (!inside && !leftStartRooms)
        {
            leftStartRooms = true;
            map.StreamFocus = null;
            Event("start rooms", "left");
        }
        // Out of the rooms, the player sees into them only through the door,
        // and walks straight into the cells beside them: bring those lamps up.
        if (leftStartRooms) map.StartLampsSouth = Mathf.MoveTowards(map.StartLampsSouth, 1f, dt / StreamFadeSeconds);
        inStartRooms = inside;
        // Far enough to see down the stream rooms to their rear wall, never
        // further past the door than the map is built (SightDistance of it).
        cam.farClipPlane = inside
            ? Mathf.Clamp(feet.z - startRearZ + 2f, map.SightDistance, map.SightDistance + Mathf.Max(0f, startDoorPoint.z - feet.z))
            : map.SightDistance;
        if (streamFade < 0f)
        {
            roomStream.Tick(dt);
            if (!startDoorOpened)
            {
                // Everything in sight through the door: every chunk in range built and furnished.
                var ready = map.ReadyAround(map.BuildRadius);
                if (!ready && elapsed > StartDoorHoldLimit && roomStream.TerminalDoorHeld) Log("START · map round the door not ready after " + StartDoorHoldLimit + " s; opening anyway");
                roomStream.TerminalDoorHeld = !ready && elapsed <= StartDoorHoldLimit;
                if (roomStream.TerminalDoorHeld && inside && Vector2.Distance(Flat(feet), Flat(startDoorPoint)) < 4f) startDoorHeldFor += dt;
                if (roomStream.TerminalDoorOpen)
                {
                    startDoorOpened = true;
                    roomStream.TerminalDoorHeld = false;
                    Event("start door", "opens");
                }
            }
            else
            {
                // The maze's lamps by the door come up with the swing, as the stream's rooms do.
                map.StartLampsNorth = Mathf.MoveTowards(map.StartLampsNorth, 1f, dt / StartLampsRiseSeconds);
                if (!inside && Vector2.Distance(Flat(feet), Flat(startDoorPoint)) >= StartDoorShutDistance)
                    roomStream.CloseTerminalDoor();
            }
            if (!roomStream.TerminalDoorShut) return;
            // Nothing of the stream can be seen any more: fade its lamps out,
            // gently, for their light on the map's side and the hum that reads them.
            streamFade = 0f;
            streamLights = titleWorld.GetComponentsInChildren<Light>();
            streamLightLevels = new float[streamLights.Length];
            for (var i = 0; i < streamLights.Length; i++) streamLightLevels[i] = streamLights[i].enabled ? streamLights[i].intensity : 0f;
            Event("start door", "shut");
            return;
        }
        if (streamFade < 1f)
        {
            streamFade = Mathf.Min(1f, streamFade + dt / StreamFadeSeconds);
            map.StartLampsNorth = 1f;
            for (var i = 0; i < streamLights.Length; i++)
            {
                if (streamLights[i] == null) continue;
                streamLights[i].intensity = streamLightLevels[i] * (1f - streamFade);
                if (streamFade >= 1f) Destroy(streamLights[i]);
            }
            return;
        }
        // One room a frame, behind the shut door; the last one keeps facing the maze.
        if (roomStream.DisposeOneRoom() || map.StartAreaBuilt) return;
        // Every chunk round the rooms is gone, far out of sight: so is the last of them.
        StopTitleCorridor();
        map.ClearStartArea();
        inStartRooms = false;
        Event("start rooms", "removed");
    }

    void OnDoorMoved(Vector3 p)
    {
        Sound(doorClip, Flat(p), .8f);
        relay?.Noise(p, hunterTuning.doorNoiseRadius);
        Event("door", Flat(p).ToString());
    }

    void OnGlassBroken(Vector3 p)
    {
        FoleyDoorBreak(Flat(p));
        relay?.Noise(p, GlassNoiseRadius);
        Flash("GLASS BROKEN  /  WALK INTO THE FRAME TO CLIMB THROUGH");
        Event("glass", Flat(p).ToString());
    }

    void OnKeyTaken(GridCoord zone)
    {
        keysTaken++;
        Flash("KEY  /  OPENS THIS ZONE'S DOORS");
        Event("key", zone.ToString());
    }

    static Vector2 Flat(Vector3 p) => new Vector2(p.x, p.z);

    void UpdateMapPlay(float dt)
    {
        if (map == null || playerBody == null) return;
        Vector2 local;
        bool sprintHeld;
#if UNITY_EDITOR
        if (autopilot) AutopilotSteer(dt, out local, out sprintHeld);
        else
#endif
        {
            if (mouseSettleFrames > 0) mouseSettleFrames--;
            else
            {
                yaw += Input.GetAxisRaw("Mouse X") * 2.1f;
                pitch = Mathf.Clamp(pitch - Input.GetAxisRaw("Mouse Y") * 2.1f, -75f, 75f);
            }
            // Keep the authored InputManager axes, but also read the physical
            // keys directly. This makes the standalone Mac/WebGL player robust
            // when a platform starts with the new input backend.
            var horizontal = Input.GetAxisRaw("Horizontal");
            var vertical = Input.GetAxisRaw("Vertical");
            if (Mathf.Abs(horizontal) < .01f)
                horizontal = (Input.GetKey(KeyCode.D) ? 1f : 0f) - (Input.GetKey(KeyCode.A) ? 1f : 0f);
            if (Mathf.Abs(vertical) < .01f)
                vertical = (Input.GetKey(KeyCode.W) ? 1f : 0f) - (Input.GetKey(KeyCode.S) ? 1f : 0f);
            local = new Vector2(horizontal, vertical);
            sprintHeld = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        }
        playerRoot.rotation = Quaternion.Euler(0f, yaw, 0f);
        cam.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
        var wish = playerRoot.right * local.x + playerRoot.forward * local.y;
        if (wish.sqrMagnitude > 1f) wish.Normalize();
        var sprinting = sprintHeld && wish.sqrMagnitude > .01f && stamina > 0f;
        if (sprinting)
        {
            stamina = Mathf.Max(0f, stamina - dt);
            sinceSprint = 0f;
        }
        else
        {
            sinceSprint += dt;
            if (sinceSprint > StaminaRecoverDelay) stamina = Mathf.Min(StaminaSeconds, stamina + StaminaRecoverRate * dt);
        }
        fallSpeed = playerBody.isGrounded ? -1f : fallSpeed - 9.81f * dt;
        var before = playerPos;
        if (climbTime >= 0f || TryStartClimb(wish)) Climb(dt);
        else playerBody.Move((wish * (sprinting ? Run : Walk) + glide + Vector3.up * fallSpeed) * dt);
        glide = Vector3.MoveTowards(glide, Vector3.zero, FrontRoomsRoomStream.TitleSpeed / GlideSeconds * dt);
        playerPos = Flat(playerRoot.position);
        if (Vector2.Distance(before, playerPos) > .001f)
        {
            stepTime += dt;
            if (stepTime > (sprinting ? .3f : .5f))
            {
                stepTime = 0f;
                FoleyFootstep(playerPos, FrontRoomsFoleyActor.Player, FrontRoomsFoleySurface.Carpet, sprinting, sprinting ? .48f : .15f);
                if (sprinting) relay?.Noise(playerRoot.position, hunterTuning.sprintNoiseRadius);
            }
        }
        UpdateStartRooms(dt);
        // Zones count from the first step into the map.
        if (!inStartRooms)
        {
            var zone = map.ZoneOf(map.CellOf(playerRoot.position)).id;
            if (zone != currentZone || zonesVisited.Count == 0)
            {
                currentZone = zone;
                if (zonesVisited.Add(zone)) Event("zone", zone.ToString());
            }
        }
        UpdateAim(dt);
#if UNITY_EDITOR
        var tickWatch = autopilot ? System.Diagnostics.Stopwatch.StartNew() : null;
#endif
        // Dormant until the door back to the stream rooms has shut behind the
        // player: its release clock only starts once they are in the maze for good.
        if (relay.Released || streamFade >= 0f || roomStream == null)
            relay.Tick(dt, playerRoot.position, cam.transform.position, playerRoot.forward);
#if UNITY_EDITOR
        if (tickWatch != null && tickWatch.Elapsed.TotalMilliseconds > autoRelayTickMs)
        {
            autoRelayTickMs = (float)tickWatch.Elapsed.TotalMilliseconds;
            autoRelayTickAt = autoPlayClock;
        }
#endif
        UpdateRelayRig(dt);
    }

    /// <summary>Walking into a broken window's frame from up to 0.95 m away starts a climb through it.</summary>
    bool TryStartClimb(Vector3 wish)
    {
        if (wish.sqrMagnitude < .1f) return false;
        var feet = playerRoot.position;
        var here = map.CellOf(feet);
        foreach (var step in new[] { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) })
        {
            var next = here + step;
            if (!map.IsBrokenWindow(here, next)) continue;
            var center = map.CrossingPoint(here, next);
            var dir = map.CellCenter(next) - map.CellCenter(here);
            dir.y = 0f;
            dir.Normalize();
            var rel = feet - center;
            rel.y = 0f;
            var along = Vector3.Dot(rel, dir);
            var lateral = (rel - dir * along).magnitude;
            if (along < -.95f || along > 0f || lateral > .45f || Vector3.Dot(wish.normalized, dir) < .5f) continue;
            climbFrom = feet;
            climbTo = center + dir * .75f;
            climbTo.y = feet.y;
            climbTime = 0f;
            FoleyFootstep(Flat(feet), FrontRoomsFoleyActor.Player, FrontRoomsFoleySurface.Carpet, false, .3f);
            PlayerClimbed?.Invoke(center);
            return true;
        }
        return false;
    }

    void Climb(float dt)
    {
        climbTime += dt;
        var t = Mathf.Clamp01(climbTime / ClimbSeconds);
        var arc = Mathf.Sin(t * Mathf.PI);
        playerBody.enabled = false;
        playerRoot.position = Vector3.Lerp(climbFrom, climbTo, t * t * (3f - 2f * t)) + Vector3.up * (arc * ClimbLift);
        playerBody.enabled = true;
        cam.transform.localPosition = new Vector3(0f, EyeHeight - arc * ClimbDuck, 0f);
        fallSpeed = 0f;
        if (t < 1f) return;
        climbTime = -1f;
        cam.transform.localPosition = new Vector3(0f, EyeHeight, 0f);
    }

    /// <summary>What the crosshair is on: E opens or shuts a door, holding E breaks glass.</summary>
    void UpdateAim(float dt)
    {
        var previous = aimed;
        aimed = null;
        prompt = null;
        aimedHold = false;
        if (Physics.Raycast(new Ray(cam.transform.position, cam.transform.forward), out var hit, Reach, ~0, QueryTriggerInteraction.Ignore))
        {
            prompt = map.Describe(hit.collider, out aimedHold);
            if (prompt != null) aimed = hit.collider;
        }
        if (previous != null && previous != aimed) map.ReleaseHold(previous);
        if (aimed == null)
        {
            holdProgress = 0f;
            return;
        }
        if (!aimedHold)
        {
            holdProgress = 0f;
            if (Input.GetKeyDown(KeyCode.E)) map.Use(aimed);
            return;
        }
        if (Input.GetKey(KeyCode.E))
        {
            if (map.Hold(aimed, dt, out holdProgress))
            {
                aimed = null;
                holdProgress = 0f;
            }
        }
        else
        {
            map.ReleaseHold(aimed);
            holdProgress = 0f;
        }
    }

    void UpdateRelayRig(float dt)
    {
        if (relay == null || hunter == null) return;
        if (hunter.gameObject.activeSelf != relay.Released) hunter.gameObject.SetActive(relay.Released);
        if (!relay.Released) return;
        var position = relay.Position;
        hunter.position = position;
        var facing = relay.SeesPlayer ? Flat(playerRoot.position - position) : Flat(relay.Heading);
        if (facing.sqrMagnitude > .0001f) hunter.rotation = Quaternion.Euler(0f, Mathf.Atan2(facing.x, facing.y) * Mathf.Rad2Deg, 0f);
        var state = relay.State;
        if (hunterRig != null)
        {
            var motion = state == HunterState.Chase ? FrontRoomsRelayRig.MotionState.Run
                : state == HunterState.BreakDoor ? FrontRoomsRelayRig.MotionState.BreakDoor
                : state == HunterState.Hunt || state == HunterState.Wander || (state == HunterState.Search && relay.Moving) ? FrontRoomsRelayRig.MotionState.Walk
                : FrontRoomsRelayRig.MotionState.IdleListen;
            hunterRig.TickAnimation(dt, motion, relay.Moving, state == HunterState.Chase ? 1.15f : 1f);
        }
        if (!relay.Moving) return;
        hunterStepTime += dt;
        if (hunterStepTime < (state == HunterState.Chase ? .29f : .44f)) return;
        hunterStepTime = 0f;
        var p = Flat(position);
        var distance = Vector2.Distance(playerPos, p);
        FoleyFootstep(p, FrontRoomsFoleyActor.Hunter, FrontRoomsFoleySurface.Carpet, state == HunterState.Chase, .36f + Mathf.Clamp01(1f - distance / 24f) * (state == HunterState.Chase ? .64f : .40f));
    }

    static string ZoneName(ZoneInfo zone)
    {
        if (zone.theme == ZoneTheme.Office) return "LEVEL 4 / OFFICE";
        switch (zone.height)
        {
            case ZoneHeight.Low: return "LEVEL 0 / LOW ROOMS";
            case ZoneHeight.Tall: return "LEVEL 0 / TALL HALLS";
            default: return "LEVEL 0 / THE MAZE";
        }
    }

    void BuildSound()
    {
        var recordedDoorCreak = Resources.Load<AudioClip>("Audio/door-creak");
        foley = new FrontRoomsFoley(recordedDoorCreak);
        playerStepClip = FrontRoomsAudio.PlayerStep(); playerRunStepClip = FrontRoomsAudio.PlayerRunStep(); hunterStepClip = FrontRoomsAudio.HunterStep();
        // The Foley door set layers a latch, hinge recording, movement bed and
        // break impact. The plain clips are fallbacks when Foley is unavailable.
        doorClip = foley.Doors.hinge;
        bangClip = foley.Doors.breakImpact;
        caughtClip = FrontRoomsAudio.Caught();
        hum = cam.gameObject.AddComponent<AudioSource>(); hum.clip = FrontRoomsAudio.Hum(); hum.loop = true; hum.volume = .18f; hum.Play();
    }
    void Sound(AudioClip clip, Vector2 p, float volume = .7f)
    {
        var g = new GameObject("Spatial sound"); g.transform.position = V(p, 1f);
        var source = g.AddComponent<AudioSource>(); source.clip = clip; source.spatialBlend = 1f; source.minDistance = 2f; source.maxDistance = 26f; source.volume = volume; source.Play();
        Destroy(g, clip.length + .1f);
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
        var lifetime = Mathf.Max(selection.impact.length, selection.texture.length, selection.cloth.length) + .06f;
        Destroy(g, lifetime);
    }

    void FoleyDoorBreak(Vector2 p)
    {
        if (foley == null)
        {
            Sound(bangClip, p, 1f);
            return;
        }
        var g = new GameObject("Foley / door / break");
        g.transform.position = V(p, 1f);
        var source = g.AddComponent<AudioSource>();
        source.spatialBlend = 1f;
        source.minDistance = 2f;
        source.maxDistance = 26f;
        source.rolloffMode = AudioRolloffMode.Logarithmic;
        source.dopplerLevel = .06f;
        source.priority = 48;
        source.pitch = .97f + UnityEngine.Random.Range(-.025f, .025f);
        source.PlayOneShot(foley.Doors.breakImpact, 1f);
        Destroy(g, foley.Doors.breakImpact.length + .1f);
    }

    Font UiFont(string name, int fontSize)
    {
        if (name.Contains("Room meta") || name.Contains("Distance") || name.Contains("Aim")) return monoFont;
        if (name.Contains("Threat") || name.Contains("Key") || name.Contains("Menu text")) return bayonFont;
        return serifFont;
    }
    Text Text(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, int fontSize, TextAnchor alignment)
    {
        var g = new GameObject(name); g.transform.SetParent(parent, false); var t = g.AddComponent<Text>();
        t.font = UiFont(name, fontSize); t.fontSize = fontSize; t.color = C("ECEAE0"); t.alignment = alignment; t.raycastTarget = false;
        t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Overflow;
        var rt = t.rectTransform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor; rt.anchoredPosition = pos; rt.sizeDelta = size;
        t.lineSpacing = 1f;
        return t;
    }
    GameObject Panel(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Color color)
    {
        var g = new GameObject(name); g.transform.SetParent(parent, false); var image = g.AddComponent<Image>(); image.color = color; image.raycastTarget = false;
        var rt = image.rectTransform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor; rt.anchoredPosition = pos; rt.sizeDelta = size;
        return g;
    }
    Sprite LoadHudSprite(string resourceName)
    {
        var texture = Resources.Load<Texture2D>(resourceName);
        if (texture == null) return null;
        return Sprite.Create(texture, new Rect(0f, 0f, texture.width, texture.height), new Vector2(.5f, .5f), 100f, 0, SpriteMeshType.FullRect);
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

        // Restore the 11:53 lockup: one complete FRONTROOMS vector wordmark
        // plus the two trailing S assets. The source white lockup paints the
        // two translucent afterimages first and the solid wordmark last; keep
        // that painter order so the gray SS never washes over the final solid
        // S when their paths overlap.
        vectorLogoLetterMasks.Clear();
        vectorLogoLetterWidths.Clear();
        // Unity imports each S at its painted bounds. Place both visible glyphs
        // on the final solid-S baseline; do not apply the source SVG viewBox
        // x coordinates a second time.
        vectorLogoS1Image = VectorLogoImage("SVG trailing S 1", s1Asset, 798f, 17.8f);
        vectorLogoS2Image = VectorLogoImage("SVG trailing S 2", s2Asset, 798f, 17.8f);
        vectorLogoRoot.Add(vectorLogoS2Image);
        vectorLogoRoot.Add(vectorLogoS1Image);
        vectorLogoLeftImage = VectorLogoImage("SVG complete wordmark", leftAsset, 8f, 17.6f);
        vectorLogoRoot.Add(vectorLogoLeftImage);
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
        roomPanel = TypographyGroup(g.transform, "Room typography", new Vector2(0, 1), new Vector2(72, -72), new Vector2(505, 144));
        roomHudGroup = roomPanel.AddComponent<CanvasGroup>();
        roomMetaText = Text(roomPanel.transform, "Room meta", new Vector2(0, 1), new Vector2(24, -18), new Vector2(660, 22), 13, TextAnchor.UpperLeft);
        roomMetaText.color = C("BDBAB0");
        roomText = Text(roomPanel.transform, "Room", new Vector2(0, 1), new Vector2(24, -44), new Vector2(505, 72), 50, TextAnchor.UpperLeft);
        roomText.color = paper;
        roomText.horizontalOverflow = HorizontalWrapMode.Overflow;
        roomText.verticalOverflow = VerticalWrapMode.Overflow;

        threatPanel = TypographyGroup(g.transform, "Threat typography", Vector2.one, new Vector2(-72, -72), new Vector2(720, 144));
        threatHudGroup = threatPanel.AddComponent<CanvasGroup>();
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
        contextText = Text(contextPanel.transform, "Context", new Vector2(.5f, .5f), new Vector2(10, 0), new Vector2(820, 72), 24, TextAnchor.MiddleCenter);
        contextText.color = paper;

        var crosshairObject = Panel(g.transform, "HUD / Crosshair", new Vector2(.5f, .5f), Vector2.zero, new Vector2(32, 32), Color.white);
        crosshairImage = crosshairObject.GetComponent<Image>();
        crosshairImage.sprite = LoadHudSprite("UI/HUD_Crosshair");
        crosshairImage.preserveAspect = true;
        crosshairHudGroup = crosshairObject.AddComponent<CanvasGroup>();
        // Prompt, hold ring and stamina sit under the crosshair and share its fade.
        promptText = Text(crosshairObject.transform, "Key prompt", new Vector2(.5f, .5f), new Vector2(0f, -44f), new Vector2(720f, 26f), 20, TextAnchor.MiddleCenter);
        promptText.color = paper;
        promptText.horizontalOverflow = HorizontalWrapMode.Overflow;
        holdBar = Panel(crosshairObject.transform, "Hold bar", new Vector2(.5f, .5f), new Vector2(0f, -68f), new Vector2(120f, 4f), new Color(1f, 1f, 1f, .25f));
        holdBarFill = Panel(holdBar.transform, "Hold bar fill", new Vector2(0f, .5f), Vector2.zero, new Vector2(0f, 4f), accent).GetComponent<Image>();
        holdBar.SetActive(false);
        for (var i = 0; i < staminaSegments.Length; i++)
        {
            staminaSegments[i] = Panel(crosshairObject.transform, "Stamina " + (i + 1), new Vector2(.5f, .5f), new Vector2(-60f + i * 30f, -92f), new Vector2(24f, 6f), accent).GetComponent<Image>();
            staminaSegments[i].enabled = false;
        }

        keyPanel = TypographyGroup(g.transform, "HUD / Key", new Vector2(0, 0), new Vector2(72, 118), new Vector2(147, 22));
        keyHudGroup = keyPanel.AddComponent<CanvasGroup>();
        keyImage = Panel(keyPanel.transform, "Key glyph", new Vector2(0, 0), Vector2.zero, new Vector2(40, 22), Color.white).GetComponent<Image>();
        keyImage.sprite = LoadHudSprite("UI/HUD_KeyGlyph");
        keyImage.preserveAspect = true;
        keyText = Text(keyPanel.transform, "Key label", new Vector2(0, 0), new Vector2(54, 0), new Vector2(110, 22), 20, TextAnchor.MiddleLeft);
        keyText.color = paper;
        keyText.text = "LEVEL 0 KEY";
        keyText.horizontalOverflow = HorizontalWrapMode.Overflow;
        keyText.verticalOverflow = VerticalWrapMode.Overflow;
        gameplayHudAlpha = 0f;
        ApplyGameplayHudAlpha();

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
        overlay.SetActive(!playing); if (crosshairImage != null) crosshairImage.enabled = playing;
        if (overlayImage != null) overlayImage.color = p == Phase.Title ? new Color(0f, 0f, 0f, 0f) : new Color(.93f, .92f, .88f, .98f);
        if (logoImage != null)
        {
            logoImage.enabled = p == Phase.Title && logoMotionRoot == null && !vectorLogoActive;
            if (p == Phase.Title && logoMotionRoot == null) logoImage.color = new Color(1f, 1f, 1f, titleLogoAlpha);
        }
        // The vector wordmark is its own panel: it keeps fading out over the start of play.
        if (vectorLogoRoot != null) vectorLogoRoot.style.display = LogoShown ? UiDisplayStyle.Flex : UiDisplayStyle.None;
        if (logoMotionRoot != null)
        {
            if (logoLeftImage != null) logoLeftImage.enabled = LogoShown;
            if (logoSlideImage != null) logoSlideImage.enabled = LogoShown;
        }
        if (roomPanel != null) roomPanel.SetActive(playing);
        if (threatPanel != null) threatPanel.SetActive(playing);
        if (keyPanel != null) keyPanel.SetActive(playing);
        if (contextPanel != null) contextPanel.SetActive(false);
        ApplyGameplayHudAlpha();
        Cursor.lockState = playing ? CursorLockMode.Locked : CursorLockMode.None; Cursor.visible = !playing;
        if (p == Phase.Title)
        {
            overlayText.text = "";
            overlayText.enabled = false;
        }
        else overlayText.enabled = true;
        if (p == Phase.Paused) overlayText.text = "<size=88><b>PAUSED</b></size>\n\n<size=13>WASD  MOVE    MOUSE  LOOK    SHIFT  SPRINT    E  DOOR    HOLD E  BREAK GLASS\nR  RESTART    O  DISPLAY SETTINGS</size>\n\n<color=#F4DF3B><size=20>ESC  RESUME</size></color>";
        if (p == Phase.Caught)
            overlayText.text = "<size=88><b>CAUGHT</b></size>\n\n<size=24>" + Mathf.RoundToInt(elapsed) + " S  /  " + zonesVisited.Count + " ZONES  /  " + keysTaken + " KEYS  /  " + (relay == null ? 0 : relay.DoorsBroken) + " DOORS BROKEN</size>\n\n<color=#F4DF3B><size=20>R  TRY AGAIN</size></color>";
    }
    void OnApplicationFocus(bool focused)
    {
#if UNITY_EDITOR
        if (autopilot) return;
#endif
        if (!focused && phase == Phase.Playing) SetPhase(Phase.Paused);
    }
    void Update()
    {
        if (!Application.isPlaying) return;
        if (phase == Phase.Title && (Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.Return))) RequestTitleStart();
        else if (phase == Phase.Paused && Input.GetKeyDown(KeyCode.O)) ToggleDisplaySettings();
        else if (displaySettingsOpen && Input.GetKeyDown(KeyCode.H)) ApplyHdrMode(!hdrEnabled, true);
        else if (Input.GetKeyDown(KeyCode.Escape) && displaySettingsOpen) ToggleDisplaySettings();
        else if (Input.GetKeyDown(KeyCode.Escape) && (phase == Phase.Playing || phase == Phase.Paused)) SetPhase(phase == Phase.Playing ? Phase.Paused : Phase.Playing);
        if (Input.GetKeyDown(KeyCode.R) && phase != Phase.Playing && phase != Phase.Title) { restart = true; SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex); }
        var dt = Mathf.Min(Time.deltaTime, .1f);
#if UNITY_EDITOR
        if (autopilot) AutopilotTick(dt);
#endif
        if (phase == Phase.Title) UpdateTitleSequence(dt);
        if (logoFading) UpdateLogoFade(dt);
        if (phase == Phase.Playing && mapPlay)
        {
            elapsed += dt;
            flashTime -= dt;
            UpdateMapPlay(dt);
        }
        UpdateHud();
    }
    void UpdateHud()
    {
        bool play = phase == Phase.Playing;
        if (play)
            gameplayHudAlpha = Mathf.MoveTowards(gameplayHudAlpha, 1f, Time.unscaledDeltaTime / GameplayHudFadeSeconds);
        else
            gameplayHudAlpha = 0f;
        ApplyGameplayHudAlpha();
        if (!mapPlay || map == null || playerRoot == null) return;
        // In the stream rooms the run starts in: Level 0's lobby, before zone 01.
        var zone = inStartRooms ? new ZoneInfo { height = ZoneHeight.Standard, theme = ZoneTheme.Level0 } : map.ZoneOf(map.CellOf(playerRoot.position));
        var released = relay != null && relay.Released;
        var threat = !released ? "" : relay.State == HunterState.BreakDoor ? "RELAY  /  BREAKING DOOR" : "RELAY  /  " + relay.State.ToString().ToUpperInvariant();
        roomMetaText.text = play ? "ZONE " + zonesVisited.Count.ToString("00") + "  /  " + zone.height.ToString().ToUpperInvariant() + "  " + MapGrid.CeilingHeight(zone.height).ToString("0.0") + " M" : "";
        roomText.text = play ? (inStartRooms ? "LEVEL 0 / THE LOBBY" : ZoneName(zone)) : "";
        var showThreat = play && released;
        threatStateText.text = showThreat ? threat : "";
        distanceText.text = showThreat ? "RELAY  " + Mathf.RoundToInt(RelayDistance()) + " M" : "";
        if (crosshairImage != null) crosshairImage.enabled = play;
        // The hint card is timed: the first-run hint, then only flashes.
        var hint = flashTime > 0f && !string.IsNullOrEmpty(flash) ? flash : elapsed < CalmHintSeconds ? CalmHint : "";
        contextText.text = play ? hint : "";
        if (promptText != null) promptText.text = play && prompt != null ? prompt : "";
        if (holdBar != null)
        {
            holdBar.SetActive(play && holdProgress > 0f);
            holdBarFill.rectTransform.sizeDelta = new Vector2(120f * holdProgress, 4f);
        }
        var tired = play && stamina < StaminaSeconds - .01f;
        for (var i = 0; i < staminaSegments.Length; i++)
        {
            if (staminaSegments[i] == null) continue;
            staminaSegments[i].enabled = tired;
            staminaSegments[i].color = stamina >= (i + .5f) * (StaminaSeconds / staminaSegments.Length) ? new Color(.957f, .875f, .231f) : new Color(1f, 1f, 1f, .25f);
        }
        if (roomPanel != null) roomPanel.SetActive(play);
        if (threatPanel != null) threatPanel.SetActive(showThreat);
        if (keyPanel != null) keyPanel.SetActive(play && !inStartRooms && map.HasKeyFor(zone.id));
        if (contextPanel != null) contextPanel.SetActive(play && hint.Length > 0);
    }

    float RelayDistance() => relay == null || !relay.Released ? -1f : Vector2.Distance(playerPos, Flat(relay.Position));
    void ApplyGameplayHudAlpha()
    {
        if (roomHudGroup != null) roomHudGroup.alpha = gameplayHudAlpha;
        if (threatHudGroup != null) threatHudGroup.alpha = gameplayHudAlpha;
        if (contextHudGroup != null) contextHudGroup.alpha = gameplayHudAlpha;
        if (crosshairHudGroup != null) crosshairHudGroup.alpha = gameplayHudAlpha;
        if (keyHudGroup != null) keyHudGroup.alpha = gameplayHudAlpha;
    }
    void Flash(string message, float duration = 3f) { flash = message; flashTime = duration; }
    void Event(string kind, string detail) { events.Add(elapsed.ToString("0.000", CultureInfo.InvariantCulture) + "," + kind + ",\"" + detail.Replace("\"", "\"\"") + "\"," + RelayDistance().ToString("0.00", CultureInfo.InvariantCulture)); }
    void OnDestroy()
    {
        if (map != null) MapRunEnded?.Invoke();
    }

    void End()
    {
        if (phase != Phase.Playing) return;
        SetPhase(Phase.Caught); Sound(caughtClip, playerPos); Event("outcome", "caught");
        string dir = Application.persistentDataPath; Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, "events-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".csv"), "time_s,event,detail,relay_m\n" + string.Join("\n", events));
        Log(phase + " · " + elapsed.ToString("0.0") + " s");
    }
    static void Log(string message) => Debug.Log("[FrontRooms3D] " + message);

#if UNITY_EDITOR
    // ---------- Autopilot: a scripted play-through for batch verification ----------
    // FrontRoomsMainScenePlaytest sets the session flag and enters Play. The
    // autopilot presses Space, takes over in the stream room, walks out
    // through its door into the maze, walks the maze along breadth-first
    // routes (opening doors on the way), sprints once, captures frames to
    // Verification/main-autopilot, writes report.json and a done file. It
    // never runs in a build or in a normal Play session.
    public const string AutopilotKey = "FrontRooms.Autopilot";
    /// <summary>Session key for a fixed maze seed on the autopilot (0 = the profile's).</summary>
    public const string AutopilotSeedKey = "FrontRooms.Autopilot.Seed";
    int autopilotSeed, autoSkipFrames, autoGhostsSeen;
    float autoWorstFrameMs, autoRelayTickMs, autoRelayTickAt, autoHandoffWorstMs;
    // When (play seconds) the start door opened, the player left the stream rooms, the door shut behind them, the rooms were removed.
    float autoStartDoorAt = -1f, autoLeftStartAt = -1f, autoStartShutAt = -1f, autoStreamRemovedAt = -1f, autoSettledAt = -1f;
    bool autoDoorShot, autoLookBackShot;
    // When the autopilot presses Space (title seconds). -autopilotSpaceAt 1.0 starts with the
    // first stream door still shut 4.85 m ahead, so the door is reached while the map is building.
    float autoSpaceAt = 1.8f;
    readonly List<(float ms, string text)> autoHandoffFrames = new List<(float, string)>();
    const float AutoHandoffSeconds = 4f;
    readonly List<string> autoGhostLog = new List<string>();
    readonly List<float> autoFrameMs = new List<float>();
    readonly List<string> autoSpikes = new List<string>();
    public const string AutopilotDoneFile = "Temp/frontrooms-autopilot-done.txt";
    const float AutopilotPlaySeconds = 75f;
    static readonly GridCoord[] AutoSteps = { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) };
    bool autopilot, autoFinished, autoRelayShot, autoOfficeShot;
    float autoOfficeCheckAt;
    float autoClock, autoPlayClock, autoNextShot, autoStuckClock, autoDistance, autoReleaseTime = -1f, autoMinRelay = float.MaxValue;
    int autoShots, autoFrames, autoErrors, autoRoutes, autoDoorsOpened, autoMaxChunks;
    Vector3 autoLastPosition;
    Vector2 autoLastFlat;
    string autoOutDir;
    readonly List<GridCoord> autoRoute = new List<GridCoord>();
    int autoRouteIndex;
    readonly HashSet<GridCoord> autoCells = new HashSet<GridCoord>();
    readonly List<string> autoErrorLog = new List<string>();
    readonly List<string> autoStates = new List<string>();

    [Serializable]
    sealed class AutopilotReport
    {
        public string verdict;
        public int seed;
        public float playSeconds;
        public float distanceWalked;
        public int cellsVisited;
        public int zonesVisited;
        public int maxChunksBuilt;
        public int routes;
        public int doorsOpened;
        public int keysTaken;
        public float relayReleasedAt = -1f;
        public float closestRelayMetres;
        public string relayFinalState;
        public int relayDoorsBroken;
        public int relayRelays;
        public int relayGhosts;
        public bool caught;
        public float averageFps;
        public float worstFrameMs;
        public float p95FrameMs;
        public float p99FrameMs;
        public float relayTickMaxMs;
        public float relayTickMaxAt;
        // The handoff from the title: the worst frame in the first 4 s after Space (nothing is hidden any more),
        // and when the start door opened, the player left the stream rooms, the door shut, the rooms were removed (-1: never).
        public float handoffWorstFrameMs;
        public List<string> handoffSlowestFrames = new List<string>();
        public float spacePressedAt;
        public float mapReadyAt = -1f;
        public float startDoorHeldSeconds;
        public float startDoorOpenedAt = -1f;
        public float leftStartRoomsAt = -1f;
        public float startDoorShutAt = -1f;
        public float streamRemovedAt = -1f;
        public List<string> frameSpikes = new List<string>();
        public int officeRoomsDressed;
        public int errors;
        public List<string> errorLog = new List<string>();
        public List<string> relayStates = new List<string>();
        public List<string> relayGhostLog = new List<string>();
        public List<string> frames = new List<string>();
    }

    readonly List<string> autoFrameNames = new List<string>();

    void AutopilotStart()
    {
        autopilot = UnityEditor.SessionState.GetBool(AutopilotKey, false);
        autopilotSeed = UnityEditor.SessionState.GetInt(AutopilotSeedKey, 0);
        if (!autopilot) return;
        var args = Environment.GetCommandLineArgs();
        for (var i = 0; i < args.Length - 1; i++)
            if (args[i] == "-autopilotSpaceAt" && float.TryParse(args[i + 1], NumberStyles.Float, CultureInfo.InvariantCulture, out var at)) autoSpaceAt = Mathf.Max(.2f, at);
        autoOutDir = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "main-autopilot");
        Directory.CreateDirectory(autoOutDir);
        foreach (var old in Directory.GetFiles(autoOutDir, "*.png")) File.Delete(old);
        Application.logMessageReceived += AutopilotLog;
        Log("AUTOPILOT on · frames to " + autoOutDir);
    }

    void AutopilotLog(string condition, string stack, LogType type)
    {
        if (type != LogType.Error && type != LogType.Exception && type != LogType.Assert) return;
        autoErrors++;
        if (autoErrorLog.Count < 20) autoErrorLog.Add(type + ": " + condition);
    }

    void AutopilotTick(float dt)
    {
        if (autoFinished) return;
        autoClock += dt;
        autoFrames++;
        // Streaming and dressing hitches, from the frame Space is pressed: the
        // map now builds while the player is in the stream room, in view.
        // Frames right after an autopilot capture carry its PNG encode, not the game's cost.
        if (autoSkipFrames > 0) autoSkipFrames--;
        else if (mapPlay)
        {
            var ms = Time.unscaledDeltaTime * 1000f;
            autoWorstFrameMs = Mathf.Max(autoWorstFrameMs, ms);
            if (autoPlayClock < AutoHandoffSeconds)
            {
                autoHandoffWorstMs = Mathf.Max(autoHandoffWorstMs, ms);
                // The six slowest handoff frames and what the map did in them.
                autoHandoffFrames.Add((ms, autoPlayClock.ToString("0.00", CultureInfo.InvariantCulture) + " s: " + ms.ToString("0.0") + " ms" + (map.WorkInFrame(Time.frameCount - 1).Length > 0 ? ", map: " + map.WorkInFrame(Time.frameCount - 1) : "")));
                autoHandoffFrames.Sort((x, y) => y.ms.CompareTo(x.ms));
                if (autoHandoffFrames.Count > 6) autoHandoffFrames.RemoveAt(6);
            }
            autoFrameMs.Add(ms);
            // Spikes with their time, to tell streaming or dressing hitches from one-off editor shader compiles.
            if (ms > 50f && autoSpikes.Count < 12)
                autoSpikes.Add(autoPlayClock.ToString("0.0", CultureInfo.InvariantCulture) + " s: " + ms.ToString("0") + " ms, zone " + ZoneName(map.ZoneOf(map.CellOf(playerRoot.position))) + ", chunks " + map.BuiltChunkCount
                    + (map.WorkInFrame(Time.frameCount - 1).Length > 0 ? ", map: " + map.WorkInFrame(Time.frameCount - 1) : ""));
        }
        if (relay != null && relay.Ghosts != autoGhostsSeen)
        {
            autoGhostsSeen = relay.Ghosts;
            if (autoGhostLog.Count < 20)
                autoGhostLog.Add(autoPlayClock.ToString("0.0", CultureInfo.InvariantCulture) + " s " + relay.State + " at " + relay.Position.ToString("F2") + " cell " + map.CellOf(relay.Position) + " · " + relay.DebugSteering + " · " + relay.DebugBlocker);
        }
        if (!mapPlay)
        {
            if (phase == Phase.Title)
            {
                if (autoShots == 0 && autoClock > Mathf.Min(1.2f, autoSpaceAt - .3f)) AutopilotCapture("00_title");
                if (autoClock > autoSpaceAt) RequestTitleStart();
            }
            if (autoClock > 40f) AutopilotFinish("never reached the maze");
            return;
        }
        autoPlayClock += dt;
        if (playerRoot != null)
        {
            var flat = Flat(playerRoot.position);
            if (autoPlayClock > dt) autoDistance += Vector2.Distance(flat, autoLastFlat);
            autoLastFlat = flat;
            if (!inStartRooms) autoCells.Add(map.CellOf(playerRoot.position));
        }
        if (autoStartDoorAt < 0f && startDoorOpened) autoStartDoorAt = autoPlayClock;
        if (autoLeftStartAt < 0f && leftStartRooms) autoLeftStartAt = autoPlayClock;
        if (autoStartShutAt < 0f && streamFade >= 0f) autoStartShutAt = autoPlayClock;
        if (autoStreamRemovedAt < 0f && roomStream == null) autoStreamRemovedAt = autoPlayClock;
        // The seam, from both sides: the map through the open stream door, and the shut door from the maze.
        if (!autoDoorShot && autoStartDoorAt >= 0f && autoPlayClock - autoStartDoorAt > .6f && inStartRooms)
        {
            autoDoorShot = true;
            AutopilotCapture((autoShots < 10 ? "0" : "") + autoShots + "_start_door");
        }
        if (!autoLookBackShot && autoStartShutAt >= 0f && autoPlayClock - autoStartShutAt > .3f)
        {
            // From the door cell, eye height, looking back at the shut door and either side of it.
            autoLookBackShot = true;
            var from = startDoorPoint + Vector3.forward * 2.7f + Vector3.up * EyeHeight;
            foreach (var side in new[] { 0f, -2.4f, 2.4f })
                AutopilotLookFrom(from, startDoorPoint + new Vector3(side, 1.3f, 0f), "start_door_from_maze" + (side < 0f ? "_left" : side > 0f ? "_right" : ""));
        }
        if (autoSettledAt < 0f && map.Settled) autoSettledAt = autoPlayClock;
        autoMaxChunks = Mathf.Max(autoMaxChunks, map.BuiltChunkCount);
        if (relay != null)
        {
            if (autoStates.Count == 0 || autoStates[autoStates.Count - 1].EndsWith(relay.State.ToString()) == false)
                autoStates.Add(autoPlayClock.ToString("0.0", CultureInfo.InvariantCulture) + " s " + relay.State);
            if (relay.Released)
            {
                if (autoReleaseTime < 0f) autoReleaseTime = autoPlayClock;
                autoMinRelay = Mathf.Min(autoMinRelay, RelayDistance());
                if (!autoRelayShot && autoPlayClock - autoReleaseTime > 1.5f)
                {
                    autoRelayShot = true;
                    AutopilotCaptureRelay();
                }
            }
        }
        // The first time the walk is in a dressed Office room: look round it (four views), for the furniture.
        if (!autoOfficeShot && playerRoot != null && autoPlayClock >= autoOfficeCheckAt && map.ZoneOf(map.CellOf(playerRoot.position)).theme == ZoneTheme.Office)
        {
            autoOfficeCheckAt = autoPlayClock + .5f;
            if (OfficeDressingNear(playerRoot.position, 4.5f))
            {
                autoOfficeShot = true;
                AutopilotLookAround("office");
            }
        }
        if (autoPlayClock > .6f && autoPlayClock >= autoNextShot)
        {
            autoNextShot = autoPlayClock + 9f;
            AutopilotCapture((autoShots < 10 ? "0" : "") + autoShots + "_play_" + Mathf.RoundToInt(autoPlayClock) + "s");
        }
        if (phase == Phase.Caught) AutopilotFinish("caught");
        else if (autoPlayClock >= AutopilotPlaySeconds) AutopilotFinish("time");
    }

    /// <summary>Walk the current route; plan a new far route when it ends or the walk stalls.</summary>
    void AutopilotSteer(float dt, out Vector2 local, out bool sprint)
    {
        local = Vector2.zero;
        sprint = false;
        // Out of the stream rooms first: down the centreline, through the door
        // and on past its open leaves into the cell ahead (always open, MapRootFor).
        if (inStartRooms || (map.CellOf(playerRoot.position) == startDoorCell && playerRoot.position.z < startDoorPoint.z + 2.2f))
        {
            var aim = map.CellCenter(startDoorCell) + Vector3.forward * 1.2f - playerRoot.position;
            aim.y = 0f;
            var aimYaw = Mathf.Atan2(aim.x, aim.z) * Mathf.Rad2Deg;
            yaw = Mathf.MoveTowardsAngle(yaw, aimYaw, 300f * dt);
            pitch = Mathf.MoveTowards(pitch, 0f, 60f * dt);
            local = new Vector2(0f, 1f);
            return;
        }
        var here = map.CellOf(playerRoot.position);
        autoStuckClock += dt;
        if (autoStuckClock > 2.5f)
        {
            if ((playerRoot.position - autoLastPosition).magnitude < .4f) autoRouteIndex = autoRoute.Count;
            autoLastPosition = playerRoot.position;
            autoStuckClock = 0f;
        }
        if (autoRouteIndex >= autoRoute.Count) AutopilotPlan(here);
        if (autoRouteIndex >= autoRoute.Count) return;
        var next = autoRoute[autoRouteIndex];
        if (here == next)
        {
            autoRouteIndex++;
            return;
        }
        if (Mathf.Abs(here.x - next.x) + Mathf.Abs(here.y - next.y) != 1)
        {
            autoRouteIndex = autoRoute.Count;
            return;
        }
        var passage = map.PassageBetween(here, next);
        if (passage == FrontRoomsMapWorld.Passage.ClosedDoor)
        {
            if (map.TryOpenDoor(here, next)) autoDoorsOpened++;
        }
        else if (passage != FrontRoomsMapWorld.Passage.Open)
        {
            autoRouteIndex = autoRoute.Count;
            return;
        }
        var target = map.CrossingPoint(here, next) + (map.CellCenter(next) - map.CellCenter(here)).normalized * .45f;
        var to = target - playerRoot.position;
        to.y = 0f;
        var desiredYaw = Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg;
        yaw = Mathf.MoveTowardsAngle(yaw, desiredYaw, 300f * dt);
        pitch = Mathf.MoveTowards(pitch, 0f, 60f * dt);
        local = new Vector2(0f, Mathf.Abs(Mathf.DeltaAngle(yaw, desiredYaw)) < 45f ? 1f : .15f);
        sprint = autoPlayClock > 16f && autoPlayClock < 22f;
    }

    /// <summary>Breadth-first route to a far cell (depth 18–30) through open edges and doors.</summary>
    void AutopilotPlan(GridCoord from)
    {
        autoRoute.Clear();
        autoRouteIndex = 0;
        var cameFrom = new Dictionary<GridCoord, GridCoord>();
        var depth = new Dictionary<GridCoord, int> { [from] = 0 };
        var queue = new Queue<GridCoord>();
        queue.Enqueue(from);
        var far = new List<GridCoord>();
        while (queue.Count > 0)
        {
            var cell = queue.Dequeue();
            var d = depth[cell];
            if (d >= 18) far.Add(cell);
            if (d >= 30) continue;
            foreach (var step in AutoSteps)
            {
                var n = cell + step;
                if (depth.ContainsKey(n) || !map.IsBuilt(n)) continue;
                var p = map.PassageBetween(cell, n);
                if (p == FrontRoomsMapWorld.Passage.Wall || p == FrontRoomsMapWorld.Passage.Glass) continue;
                depth[n] = d + 1;
                cameFrom[n] = cell;
                queue.Enqueue(n);
            }
        }
        if (far.Count == 0)
            foreach (var pair in depth) if (pair.Value > 0) far.Add(pair.Key);
        if (far.Count == 0) return;
        var goal = far[UnityEngine.Random.Range(0, far.Count)];
        for (var c = goal; c != from; c = cameFrom[c]) autoRoute.Add(c);
        autoRoute.Reverse();
        autoRoutes++;
    }

    void AutopilotCapture(string name)
    {
        if (cam == null) return;
        AutopilotRender(cam, name);
    }

    /// <summary>One view from a point towards another, with the player's lens.</summary>
    void AutopilotLookFrom(Vector3 from, Vector3 target, string label)
    {
        if (cam == null) return;
        var go = new GameObject("AUTOPILOT / look-at camera");
        var shot = go.AddComponent<Camera>();
        shot.CopyFrom(cam);
        shot.enabled = false;
        go.transform.position = from;
        go.transform.LookAt(target);
        AutopilotRender(shot, (autoShots < 10 ? "0" : "") + autoShots + "_" + label);
        Destroy(go);
    }

    bool OfficeDressingNear(Vector3 point, float radius)
    {
        // Dressing roots sit directly under the chunk roots, which sit directly under the map.
        foreach (Transform chunk in map.transform)
            foreach (Transform t in chunk)
                if (t.name == "office dressing")
                    foreach (var r in t.GetComponentsInChildren<Renderer>())
                        if ((r.bounds.center - point).sqrMagnitude < radius * radius) return true;
        return false;
    }

    /// <summary>Four views from the player's eye, a quarter turn apart, level.</summary>
    void AutopilotLookAround(string label)
    {
        if (cam == null) return;
        var go = new GameObject("AUTOPILOT / look-around camera");
        var shot = go.AddComponent<Camera>();
        shot.CopyFrom(cam);
        shot.enabled = false;
        go.transform.position = cam.transform.position;
        for (var i = 0; i < 4; i++)
        {
            go.transform.rotation = Quaternion.Euler(6f, yaw + i * 90f, 0f);
            AutopilotRender(shot, (autoShots < 10 ? "0" : "") + autoShots + "_" + label + "_" + i * 90);
        }
        Destroy(go);
    }

    /// <summary>A third-person look at the Relay from behind the player's side of it, to check the rig is placed and animating.</summary>
    void AutopilotCaptureRelay()
    {
        if (relay == null || cam == null) return;
        var go = new GameObject("AUTOPILOT / relay camera");
        var shot = go.AddComponent<Camera>();
        shot.CopyFrom(cam);
        shot.enabled = false;
        // Stand in the most open of eight directions around the Relay, so the
        // shot is not taken from inside a wall.
        var target = relay.Position + Vector3.up * 1.3f;
        var bestDir = Vector3.back;
        var bestClear = -1f;
        for (var i = 0; i < 8; i++)
        {
            var dir = Quaternion.Euler(0f, i * 45f, 0f) * Vector3.forward;
            var clear = Physics.Raycast(target, dir, out var hit, 3.2f, ~0, QueryTriggerInteraction.Ignore) && !hit.collider.transform.IsChildOf(hunter) ? hit.distance : 3.2f;
            if (clear > bestClear) { bestClear = clear; bestDir = dir; }
        }
        go.transform.position = target + bestDir * Mathf.Max(.6f, bestClear - .35f) + Vector3.up * .3f;
        go.transform.LookAt(target);
        AutopilotRender(shot, (autoShots < 10 ? "0" : "") + autoShots + "_relay");
        Destroy(go);
    }

    void AutopilotRender(Camera source, string name)
    {
        autoSkipFrames = 2;
        var rt = RenderTexture.GetTemporary(1600, 900, 24, RenderTextureFormat.ARGB32);
        var previous = source.targetTexture;
        source.targetTexture = rt;
        source.Render();
        source.Render();
        source.targetTexture = previous;
        var active = RenderTexture.active;
        RenderTexture.active = rt;
        var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        tex.Apply();
        RenderTexture.active = active;
        RenderTexture.ReleaseTemporary(rt);
        File.WriteAllBytes(Path.Combine(autoOutDir, name + ".png"), tex.EncodeToPNG());
        Destroy(tex);
        autoFrameNames.Add(name + ".png");
        autoShots++;
    }

    static float Percentile(List<float> values, float q)
    {
        if (values.Count == 0) return 0f;
        var sorted = new List<float>(values);
        sorted.Sort();
        return sorted[Mathf.Clamp(Mathf.CeilToInt(q * sorted.Count) - 1, 0, sorted.Count - 1)];
    }

    static int CountNamed(Transform root, string name)
    {
        var count = 0;
        foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name == name) count++;
        return count;
    }

    void AutopilotFinish(string reason)
    {
        if (autoFinished) return;
        autoFinished = true;
        var report = new AutopilotReport
        {
            seed = runSeed,
            playSeconds = autoPlayClock,
            distanceWalked = autoDistance,
            cellsVisited = autoCells.Count,
            zonesVisited = zonesVisited.Count,
            maxChunksBuilt = autoMaxChunks,
            routes = autoRoutes,
            doorsOpened = autoDoorsOpened,
            keysTaken = keysTaken,
            relayReleasedAt = autoReleaseTime,
            closestRelayMetres = autoMinRelay == float.MaxValue ? -1f : autoMinRelay,
            relayFinalState = relay == null ? "none" : relay.State.ToString(),
            relayDoorsBroken = relay == null ? 0 : relay.DoorsBroken,
            relayRelays = relay == null ? 0 : relay.Relays,
            relayGhosts = relay == null ? 0 : relay.Ghosts,
            caught = phase == Phase.Caught,
            averageFps = autoClock > 0f ? autoFrames / autoClock : 0f,
            worstFrameMs = autoWorstFrameMs,
            p95FrameMs = Percentile(autoFrameMs, .95f),
            p99FrameMs = Percentile(autoFrameMs, .99f),
            relayTickMaxMs = autoRelayTickMs,
            relayTickMaxAt = autoRelayTickAt,
            handoffWorstFrameMs = autoHandoffWorstMs,
            handoffSlowestFrames = autoHandoffFrames.ConvertAll(f => f.text),
            spacePressedAt = autoSpaceAt,
            mapReadyAt = autoSettledAt,
            startDoorHeldSeconds = startDoorHeldFor,
            startDoorOpenedAt = autoStartDoorAt,
            leftStartRoomsAt = autoLeftStartAt,
            startDoorShutAt = autoStartShutAt,
            streamRemovedAt = autoStreamRemovedAt,
            frameSpikes = autoSpikes,
            officeRoomsDressed = map == null ? 0 : CountNamed(map.transform, "office dressing"),
            errors = autoErrors,
            errorLog = autoErrorLog,
            relayStates = autoStates,
            relayGhostLog = autoGhostLog,
            frames = autoFrameNames,
        };
        var reached = mapPlay && autoDistance > 20f && autoCells.Count > 8;
        report.verdict = (reached && autoErrors == 0 && relay != null && relay.Released ? "PASS" : "FAIL") + " · ended by " + reason;
        File.WriteAllText(Path.Combine(autoOutDir, "report.json"), JsonUtility.ToJson(report, true));
        var done = Path.Combine(Directory.GetParent(Application.dataPath).FullName, AutopilotDoneFile);
        Directory.CreateDirectory(Path.GetDirectoryName(done));
        File.WriteAllText(done, report.verdict);
        Log("AUTOPILOT " + report.verdict);
    }
#endif
}
