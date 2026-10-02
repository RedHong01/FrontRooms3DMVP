using System;
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
// First-person FrontRooms. The title corridor and the playable level are the
// same infinite room stream; the camera is handed to the player in place and
// the serialized Relay hunts them through it.
public sealed class FrontRooms3DGame : MonoBehaviour
{
    enum Phase { Title, Playing, Paused, Caught }
    Phase phase;
    Camera cam;
    [SerializeField, Tooltip("The Relay rig serialized in this scene. It stays hidden until the hunter is released.")]
    Transform hunter;
    [SerializeField, Tooltip("When the Relay is released, how it listens, hunts, searches, chases and breaks doors.")]
    FrontRoomsHunterTuning hunterTuning = new FrontRoomsHunterTuning();
    FrontRoomsRelayRig hunterRig;
    FrontRoomsHunterBrain hunterBrain;
    Vector2 playerPos;
    readonly List<string> events = new List<string>();
    Material wallMat, floorMat, darkMat, ceilingMat;
    readonly Dictionary<RoomRule, Material> wallMats = new Dictionary<RoomRule, Material>();
    readonly Dictionary<RoomRule, Material> floorMats = new Dictionary<RoomRule, Material>();
    readonly Dictionary<RoomRule, Material> ceilingMats = new Dictionary<RoomRule, Material>();
    Material trimMat, fixtureMat;
    // Procedural materials and textures made for the edit-mode preview, so
    // they can be released with it instead of leaking on every reload.
    readonly List<UnityEngine.Object> previewAssets = new List<UnityEngine.Object>();
    AudioSource hum;
    AudioClip playerStepClip, playerRunStepClip, hunterStepClip, doorClip, bangClip, caughtClip;
    FrontRoomsFoley foley;
    Text roomMetaText, roomText, threatStateText, distanceText, contextText, overlayText, crosshair, displaySettingsText;
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
    CanvasGroup roomHudGroup, threatHudGroup, contextHudGroup, crosshairHudGroup;
    Image overlayImage;
    Outline logoOutline;
    Transform titleWorld;
    FrontRoomsRoomStream roomStream;
    [SerializeField, Tooltip("Optional room prefab/template copied into each streamed title room.")]
    GameObject streamedRoomTemplate;
    float titleLogoAlpha;
    float logoMotionElapsed;
    bool titleHandoffPending;
    bool streamedPlay;
    // The runtime stream runs on its own centerline, clear of the edit-mode
    // profile preview at X = 0.
    public const float TitleCenterX = 256f;
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
    float gameplayHudAlpha;
    float yaw, pitch, elapsed, stepTime, hunterStepTime, flashTime;
    string flash = "";
    int startRoom;
    const float Walk = 3.2f, Run = 5.5f;
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
        foreach (var asset in previewAssets)
            if (asset != null) DestroyImmediate(asset);
        previewAssets.Clear();
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
        // Keep the room readable through local fixtures rather than flooding the
        // whole map with a flat grey/yellow ambient wash.  Trilight gives the
        // unlit side of the walls a cool ceiling bounce and a much darker floor
        // bounce, which is closer to a real fluorescent room and keeps doorways
        // and corners from looking like unlit solid-colour blocks.
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
        // Set ambientLight first: in Unity's built-in renderer this property is
        // an alias for the sky colour and would otherwise overwrite it.
        RenderSettings.ambientLight = new Color(.16f, .15f, .12f);
        RenderSettings.ambientSkyColor = C("8D8E78");
        RenderSettings.ambientEquatorColor = C("4A4231");
        RenderSettings.ambientGroundColor = C("252016");
        RenderSettings.reflectionIntensity = .3f;
        RenderSettings.fog = true; RenderSettings.fogMode = FogMode.ExponentialSquared;
        RenderSettings.fogColor = C("29271E"); RenderSettings.fogDensity = .012f;
        QualitySettings.shadowDistance = 48f;
        QualitySettings.shadowCascades = 4;
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
        // Keep the first-person image and overlay text at native resolution.
        // The project previously requested MSAA on the camera but left the
        // active Ultra quality level at 0x, so the Game view/build could show
        // soft geometry and UI edges.
        QualitySettings.antiAliasing = 4;
        QualitySettings.globalTextureMipmapLimit = 0;
        Time.timeScale = 1f;
        DestroyEditorPreview();
        InitializeFonts();
        cam = GetComponentInChildren<Camera>(true);
        if (cam == null) cam = CreateCamera(transform);
        EnsureRuntimeCamera(cam);
        BindHunter();
        BuildMaterials();
        hdrEnabled = PlayerPrefs.GetInt(HdrPreferenceKey, defaultHdr ? 1 : 0) != 0;
        ApplyHdrMode(hdrEnabled, false);
        BuildHud();
        BuildSound();
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

    // A soft, antialiased stroke used by the printed wallpaper glyphs. Keeping
    // the motif as a color modulation (rather than geometry) avoids turning the
    // paper into a wireframe when the wall catches a grazing light.
    static float PrintedStroke(float px, float py, float x1, float y1, float x2, float y2, float width)
    {
        var vx = x2 - x1;
        var vy = y2 - y1;
        var lengthSq = vx * vx + vy * vy;
        var t = lengthSq > .0001f ? Mathf.Clamp01(((px - x1) * vx + (py - y1) * vy) / lengthSq) : 0f;
        var dx = px - (x1 + vx * t);
        var dy = py - (y1 + vy * t);
        var distance = Mathf.Sqrt(dx * dx + dy * dy);
        return 1f - Mathf.SmoothStep(width, width + 1.15f, distance);
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
        tex.mipMapBias = -1.10f;
        var pixels = new Color[size * size];
        for (var y = 0; y < size; y++)
            for (var x = 0; x < size; x++)
            {
                var fiber = Mathf.Sin((x + style * 23) * .19f + Mathf.Sin(y * .07f)) * .012f
                    + Mathf.Sin((y + style * 17) * .11f) * .008f;
                var v = 0.965f + fiber;
                var c = baseColor * v;
                var pattern = 0f;
                var variant = ((style % 3) + 3) % 3;
                if (variant == 0)
                {
                    // Level 0's recognizable print is a very fine, repeated
                    // vertical chevron/diamond glyph. The reference motif is
                    // two quiet ink tones on yellow paper: it should read as a
                    // woven print at a glance, not as dark V-shaped geometry.
                    // Use a larger source glyph and a tighter world repeat.
                    // This keeps the diagonal strokes above the trilinear
                    // mip footprint at first-person distance while preserving
                    // the small, period-wallpaper rhythm in metres.
                    var cellW = 96f;
                    var cellH = 128f;
                    var cellX = Mathf.Repeat(x + style * 11f, cellW);
                    var cellY = Mathf.Repeat(y + style * 17f, cellH);
                    var center = cellW * .5f;
                    // Outer broken diamond and its inner echo. Short strokes
                    // keep adjacent repeats visually separated at wall scale.
                    var outer = 0f;
                    outer = Mathf.Max(outer, PrintedStroke(cellX, cellY, center, 10f, center - 22f, 42f, 9.0f));
                    outer = Mathf.Max(outer, PrintedStroke(cellX, cellY, center, 10f, center + 22f, 42f, 9.0f));
                    outer = Mathf.Max(outer, PrintedStroke(cellX, cellY, center - 22f, 42f, center, 74f, 9.0f));
                    outer = Mathf.Max(outer, PrintedStroke(cellX, cellY, center + 22f, 42f, center, 74f, 9.0f));
                    var inner = 0f;
                    inner = Mathf.Max(inner, PrintedStroke(cellX, cellY, center, 22f, center - 12f, 42f, 5.5f));
                    inner = Mathf.Max(inner, PrintedStroke(cellX, cellY, center, 22f, center + 12f, 42f, 5.5f));
                    inner = Mathf.Max(inner, PrintedStroke(cellX, cellY, center - 12f, 42f, center, 60f, 5.5f));
                    inner = Mathf.Max(inner, PrintedStroke(cellX, cellY, center + 12f, 42f, center, 60f, 5.5f));
                    // The tiny stem and dot are what make the print feel like
                    // paper from the period instead of a modern logo.
                    var stem = cellX > center - 3.5f && cellX < center + 3.5f && cellY > 76f && cellY < 112f ? .78f : 0f;
                    var dotDx = cellX - center;
                    var dotDy = cellY - 118f;
                    var dot = Mathf.Clamp01(1f - Mathf.Sqrt(dotDx * dotDx + dotDy * dotDy) / 4.2f);
                    pattern = outer * .80f + inner * .34f + stem * .20f + dot * .12f;
                }
                else if (variant == 1)
                {
                    // Sparse floral medallions: readable only in near light,
                    // like a second print run in the practical set.
                    var cx = Mathf.Repeat(x + 22f, 96f) - 48f;
                    var cy = Mathf.Repeat(y + 34f, 96f) - 48f;
                    var radial = Mathf.Sqrt(cx * cx + cy * cy);
                    pattern = Mathf.Clamp01(1f - Mathf.Abs(radial - 19f) / 3.5f) * .075f;
                    pattern += Mathf.Clamp01(1f - radial / 6f) * .05f;
                }
                else
                {
                    var diamond = Mathf.Abs(Mathf.Repeat(x + y, 88f) - 44f) < 2.3f
                        || Mathf.Abs(Mathf.Repeat(x - y + 88f, 88f) - 44f) < 2.3f;
                    pattern = diamond ? .08f : 0f;
                }
                if (pattern > 0f) c = Color.Lerp(c, patternColor, Mathf.Clamp01(pattern));
                pixels[y * size + x] = new Color(c.r, c.g, c.b, 1f);
            }
        // Keep this generated source readable until the paired micro-normal is
        // derived in TexturedMat. It is still mipmapped and reused by every
        // streamed room; dropping CPU readability here would make runtime
        // builds fail before the first frame.
        tex.SetPixels(pixels); tex.Apply(true, false);
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
                // Two crossing pile directions plus a broad, low-contrast wear
                // field read as carpet under a soft fluorescent source. The
                // broad field prevents the old single checker repeat from
                // looking like a tiled procedural texture.
                var strandA = Mathf.Sin((x + style * 17) * .92f + Mathf.Sin(y * .08f)) * .028f;
                var strandB = Mathf.Sin((y - style * 11) * 1.07f + Mathf.Sin(x * .06f)) * .024f;
                var broadWear = Mathf.Sin(x * .035f + style * .7f) * Mathf.Sin(y * .027f + 1.2f) * .055f;
                var weave = strandA + strandB + broadWear;
                var c = baseColor * (1f + weave);
                if ((x + style * 20) % 96 == 0 || (y + style * 9) % 121 == 0) c *= .89f;
                pixels[y * size + x] = new Color(c.r, c.g, c.b, 1f);
            }
        tex.SetPixels(pixels); tex.Apply(true, false);
        return tex;
    }

    Texture2D NormalFromAlbedo(Texture2D source, float strength)
    {
        if (source == null) return null;
        var width = source.width;
        var height = source.height;
        var sourcePixels = source.GetPixels();
        var normalPixels = new Color[sourcePixels.Length];
        float HeightAt(int x, int y)
        {
            x = (x % width + width) % width;
            y = (y % height + height) % height;
            return sourcePixels[y * width + x].grayscale;
        }
        for (var y = 0; y < height; y++)
            for (var x = 0; x < width; x++)
            {
                var dx = (HeightAt(x + 1, y) - HeightAt(x - 1, y)) * strength;
                var dy = (HeightAt(x, y + 1) - HeightAt(x, y - 1)) * strength;
                var n = new Vector3(-dx, -dy, 1f).normalized;
                normalPixels[y * width + x] = new Color(n.x * .5f + .5f, n.y * .5f + .5f, n.z * .5f + .5f, 1f);
            }
        var normal = new Texture2D(width, height, TextureFormat.RGBA32, true, true);
        normal.name = source.name + " / micro normal";
        normal.wrapMode = TextureWrapMode.Repeat;
        normal.filterMode = FilterMode.Trilinear;
        normal.anisoLevel = 4;
        normal.SetPixels(normalPixels);
        normal.Apply(true, true);
        if (!Application.isPlaying) previewAssets.Add(normal);
        return normal;
    }

    Material TexturedMat(string name, Color baseColor, Texture2D texture, Vector2 scale, bool emission = false)
    {
        var m = Mat(name, baseColor, emission);
        // The generated texture already contains the authored base color and
        // printed ink. Multiplying that albedo a second time through the
        // material tint crushed the paper contrast in the built player and
        // made the chevron print disappear at corridor distance.
        m.color = Color.white;
        m.mainTexture = texture;
        m.mainTextureScale = scale;
        var carpet = name.IndexOf("Carpet", StringComparison.OrdinalIgnoreCase) >= 0;
        // Printed wallpaper is a flat ink layer. Deriving a normal from its
        // chevrons made the glyph edges catch grazing light like raised wire
        // strips; reserve the procedural normal for the carpet weave.
        var normal = carpet ? NormalFromAlbedo(texture, 9.5f) : null;
        if (normal != null && m.HasProperty("_BumpMap"))
        {
            m.EnableKeyword("_NORMALMAP");
            m.SetTexture("_BumpMap", normal);
            m.SetFloat("_BumpScale", carpet ? .34f : .08f);
        }
        m.SetFloat("_Metallic", 0f);
        m.SetFloat("_Glossiness", carpet ? .18f : .09f);
        m.SetFloat("_OcclusionStrength", carpet ? .72f : .62f);
        return m;
    }

    Material WallMaterial(RoomRule rule) => wallMats.TryGetValue(rule, out var m) ? m : wallMat;
    Material FloorMaterial(RoomRule rule) => floorMats.TryGetValue(rule, out var m) ? m : floorMat;
    Material CeilingMaterial(RoomRule rule) => ceilingMats.TryGetValue(rule, out var m) ? m : ceilingMat;

    /// <summary>
    /// The room profile palette. The visual grammar follows the deck: yellowed
    /// repeating wallpaper, low-sheen carpet, and room-specific temperature and
    /// contrast changes, one material per profile so a transition is legible.
    /// </summary>
    void BuildMaterials()
    {
        wallMats.Clear(); floorMats.Clear(); ceilingMats.Clear();
        // FilmSurface meshes expose metre-space UVs. Keep the printed motif at
        // roughly 2 m wide and the carpet weave at a few centimetres instead of
        // stretching a default Cube's 0..1 UVs across the whole slab.
        var paperRepeat = new Vector2(.62f, .52f);
        wallMats[RoomRule.Lobby] = TexturedMat("Wallpaper / lobby", C("C5BB7B"), WallpaperTexture(C("C5BB7B"), C("6A786E"), 0), paperRepeat);
        wallMats[RoomRule.Shift] = TexturedMat("Wallpaper / level 0", C("C2B875"), WallpaperTexture(C("C2B875"), C("6A786E"), 0), paperRepeat);
        wallMats[RoomRule.Office] = TexturedMat("Wallpaper / office / woven beige", C("B7AE94"), WallpaperTexture(C("B7AE94"), C("87806E"), 2), paperRepeat);
        wallMats[RoomRule.Run] = TexturedMat("Wall / run / chalky utility", C("766B60"), WallpaperTexture(C("766B60"), C("554B45"), 5), paperRepeat);
        wallMats[RoomRule.Exit] = TexturedMat("Wallpaper / exit", C("5D7770"), WallpaperTexture(C("5D7770"), C("334B46"), 4), paperRepeat);

        floorMats[RoomRule.Lobby] = TexturedMat("Carpet / lobby", C("9A8554"), CarpetTexture(C("9A8554"), 0), new Vector2(2.8f, 2.8f));
        floorMats[RoomRule.Shift] = TexturedMat("Carpet / level 0", C("8E7A4E"), CarpetTexture(C("8E7A4E"), 1), new Vector2(2.8f, 2.8f));
        floorMats[RoomRule.Office] = TexturedMat("Carpet / office / worn grey brown", C("6E665A"), CarpetTexture(C("6E665A"), 2), new Vector2(2.8f, 2.8f));
        floorMats[RoomRule.Run] = TexturedMat("Floor / run / dirty concrete", C("55504A"), CarpetTexture(C("55504A"), 5), new Vector2(1.75f, 1.75f));
        floorMats[RoomRule.Exit] = TexturedMat("Carpet / exit", C("283A38"), CarpetTexture(C("283A38"), 4), new Vector2(2.8f, 2.8f));

        ceilingMats[RoomRule.Lobby] = Mat("Ceiling / lobby", C("777266"));
        ceilingMats[RoomRule.Shift] = Mat("Ceiling / level 0", C("696355"));
        ceilingMats[RoomRule.Office] = Mat("Ceiling / office / acoustic tile", C("706D68"));
        ceilingMats[RoomRule.Run] = Mat("Ceiling / run / exposed service", C("2B2926"));
        ceilingMats[RoomRule.Exit] = Mat("Ceiling / exit", C("354846"));
        wallMat = wallMats[RoomRule.Lobby];
        floorMat = floorMats[RoomRule.Lobby];
        ceilingMat = ceilingMats[RoomRule.Lobby];
        trimMat = Mat("Aged wall trim", C("716440"));
        fixtureMat = Mat("Fluorescent diffuser", C("F7F2D8"), true);
        darkMat = Mat("Door and furniture", C("4B463C"));
        if (Application.isPlaying) return;
        foreach (var material in new[] { trimMat, fixtureMat, darkMat }) previewAssets.Add(material);
        foreach (var set in new[] { wallMats, floorMats, ceilingMats })
            foreach (var material in set.Values)
            {
                previewAssets.Add(material);
                if (material.mainTexture != null) previewAssets.Add(material.mainTexture);
            }
    }

    void BuildTitleCorridor()
    {
        // Fast Enter Play Mode can preserve the previous generated stream.
        // Rebuild it so the title always starts with a fresh wipe/relay clock.
        if (titleWorld != null) StopTitleCorridor();
        titleWorld = new GameObject("Title sequence / recycled corridor").transform;
        // The camera stays in the same generated room through the handoff;
        // the title corridor simply becomes the level.
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
            ProfileMaterials(wallMats), ProfileMaterials(floorMats), ProfileMaterials(ceilingMats));
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
        // Historical title clock: the complete wordmark stays present while
        // the first streamed door drives the two trailing-S relays.
        logoMotionElapsed += dt;
        titleLogoAlpha = roomStream.LogoVisibility;
        UpdateLogoMotion();
        if (titleHandoffPending && roomStream.HasControl) EnterGameplayFromTitle();
    }

    void UpdateLogoMotion()
    {
        if (vectorLogoActive)
        {
            var vectorVisible = phase == Phase.Title;
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
            // corridor. It remains at full opacity after the reveal; only the
            // player handoff hides it.
            var vectorAlpha = Mathf.Clamp01(titleLogoAlpha);
            vectorLogoLeftImage.style.opacity = vectorAlpha;
            vectorLogoS1Image.style.opacity = vectorAlpha;
            vectorLogoS2Image.style.opacity = vectorAlpha;
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
    }

    void RequestTitleStart()
    {
        if (titleHandoffPending || streamedPlay) return;
        if (roomStream == null) return;
        roomStream.RequestStart();
        titleHandoffPending = true;
    }

    void StartCanonicalStreamedRestart()
    {
        if (roomStream == null) return;
        SetPhase(Phase.Title);
        // A retry reuses the title's first door and camera handoff, so it lands
        // in the same stream, with the same Relay, as a first run.
        RequestTitleStart();
        Log("RESTART · streamed route");
    }

    void EnterGameplayFromTitle()
    {
        if (!titleHandoffPending || streamedPlay) return;
        titleHandoffPending = false;
        streamedPlay = true;
        // The same camera remains in the same generated room. Only its input
        // ownership changes, so the player never sees a loading cut.
        playerPos = new Vector2(cam.transform.position.x, cam.transform.position.z);
        yaw = 0f;
        pitch = 0f;
        elapsed = 0f;
        // The handoff room and the next ones stay empty Lobby rooms; furnished
        // rooms are dressed out of sight. The Relay stays dormant until the
        // player has spent a moment in the first furnished room.
        roomStream.BeginPlayableSequence();
        startRoom = roomStream.CurrentRoomNumber;
        hunterBrain = new FrontRoomsHunterBrain(roomStream, hunterTuning);
        hunterBrain.StateChanged += state => Event("hunter", state.ToString());
        hunterBrain.DoorBlow += FoleyDoorBreak;
        hunterBrain.DoorBroken += door => Event("door_broken", door.ToString());
        // The Run room is the alarm beat: once the door behind the player has
        // shut, the Relay is brought up behind it and hunts them from there.
        hunterBrain.Alarmed += room =>
        {
            Flash("RUN  /  KEEP THE RED ROOM MOVING");
            Event("alarm", room.ToString());
        };
        hunterBrain.Caught += End;
        SetPhase(Phase.Playing);
        Flash("WASD + MOUSE  /  WALK THE ROOMS", 6f);
        Event("start", "streamed-room");
    }


    void UpdateStreamedPlay(float dt)
    {
        yaw += Input.GetAxisRaw("Mouse X") * 2.1f;
        pitch = Mathf.Clamp(pitch - Input.GetAxisRaw("Mouse Y") * 2.1f, -75f, 75f);
        // Keep the authored InputManager axes, but also read the physical
        // keys directly. This makes the standalone Mac/WebGL player robust
        // when a platform starts with the new input backend.
        var horizontal = Input.GetAxisRaw("Horizontal");
        var vertical = Input.GetAxisRaw("Vertical");
        if (Mathf.Abs(horizontal) < .01f)
            horizontal = (Input.GetKey(KeyCode.D) ? 1f : 0f) - (Input.GetKey(KeyCode.A) ? 1f : 0f);
        if (Mathf.Abs(vertical) < .01f)
            vertical = (Input.GetKey(KeyCode.W) ? 1f : 0f) - (Input.GetKey(KeyCode.S) ? 1f : 0f);
        var local = new Vector2(horizontal, vertical);
        var forward = new Vector2(Mathf.Sin(yaw * Mathf.Deg2Rad), Mathf.Cos(yaw * Mathf.Deg2Rad));
        var right = new Vector2(forward.y, -forward.x);
        var sprint = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        var before = new Vector2(cam.transform.position.x, cam.transform.position.z);
        var movement = (right * local.x + forward * local.y).normalized * (sprint ? Run : Walk) * dt;
        var moved = roomStream == null ? cam.transform.position : roomStream.Move(movement);
        var after = new Vector2(moved.x, moved.z);
        cam.transform.position = new Vector3(after.x, 1.62f, after.y);
        cam.transform.rotation = Quaternion.Euler(pitch, yaw, 0f);
        playerPos = after;
        if (Vector2.Distance(before, after) > .001f)
        {
            stepTime += dt;
            if (stepTime > (sprint ? .3f : .5f))
            {
                stepTime = 0f;
                FoleyFootstep(after, FrontRoomsFoleyActor.Player, SurfaceOf(roomStream.CurrentRule), sprint, sprint ? .48f : .15f);
                if (sprint && hunterBrain != null) hunterBrain.Noise(after, hunterTuning.sprintNoiseRadius);
            }
        }
        UpdateRelay(dt);
    }

    void UpdateRelay(float dt)
    {
        if (hunterBrain == null || roomStream == null) return;
        hunterBrain.Tick(dt, playerPos);
        if (hunter == null) return;
        if (hunter.gameObject.activeSelf != hunterBrain.Released) hunter.gameObject.SetActive(hunterBrain.Released);
        if (!hunterBrain.Released) return;
        var position = hunterBrain.Position;
        hunter.position = V(position);
        var facing = playerPos - position;
        if (facing.sqrMagnitude > .0001f) hunter.rotation = Quaternion.Euler(0f, Mathf.Atan2(facing.x, facing.y) * Mathf.Rad2Deg, 0f);
        var state = hunterBrain.State;
        if (hunterRig != null)
        {
            var motion = state == HunterState.Chase ? FrontRoomsRelayRig.MotionState.Run
                : state == HunterState.BreakDoor ? FrontRoomsRelayRig.MotionState.BreakDoor
                : state == HunterState.Hunt ? FrontRoomsRelayRig.MotionState.Walk
                : FrontRoomsRelayRig.MotionState.IdleListen;
            hunterRig.TickAnimation(dt, motion, hunterBrain.Moving, state == HunterState.Chase ? 1.15f : 1f);
        }
        if (!hunterBrain.Moving) return;
        hunterStepTime += dt;
        if (hunterStepTime < (state == HunterState.Chase ? .29f : .44f)) return;
        hunterStepTime = 0f;
        var distance = Vector2.Distance(playerPos, position);
        var surface = SurfaceOf(roomStream.RuleAt(roomStream.SequenceAtZ(position.y)));
        FoleyFootstep(position, FrontRoomsFoleyActor.Hunter, surface, state == HunterState.Chase, .36f + Mathf.Clamp01(1f - distance / 24f) * (state == HunterState.Chase ? .64f : .40f));
    }

    static FrontRoomsFoleySurface SurfaceOf(RoomRule rule)
    {
        switch (rule)
        {
            case RoomRule.Office: return FrontRoomsFoleySurface.Tile;
            case RoomRule.Run: return FrontRoomsFoleySurface.Concrete;
            case RoomRule.Exit: return FrontRoomsFoleySurface.Metal;
            default: return FrontRoomsFoleySurface.Carpet;
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

        // Restore the 11:53 lockup: one complete FRONTROOMS vector wordmark
        // plus the two trailing S assets. The individual glyph resources stay
        // available for later variants, but are not used by this title motion.
        vectorLogoLetterMasks.Clear();
        vectorLogoLetterWidths.Clear();
        vectorLogoLeftImage = VectorLogoImage("SVG complete wordmark", leftAsset, 8f, 17.6f);
        vectorLogoRoot.Add(vectorLogoLeftImage);

        // Unity imports each S at its painted bounds. Place both visible glyphs
        // on the final solid-S baseline; do not apply the source SVG viewBox
        // x coordinates a second time.
        vectorLogoS1Image = VectorLogoImage("SVG trailing S 1", s1Asset, 798f, 17.8f);
        vectorLogoS2Image = VectorLogoImage("SVG trailing S 2", s2Asset, 798f, 17.8f);
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
        ApplyGameplayHudAlpha();
        Cursor.lockState = playing ? CursorLockMode.Locked : CursorLockMode.None; Cursor.visible = !playing;
        if (p == Phase.Title)
        {
            overlayText.text = "";
            overlayText.enabled = false;
        }
        else overlayText.enabled = true;
        if (p == Phase.Paused) overlayText.text = "<size=88><b>PAUSED</b></size>\n\n<size=13>WASD  MOVE    MOUSE  LOOK    SHIFT  RUN\nR  RESTART    O  DISPLAY SETTINGS</size>\n\n<color=#F4DF3B><size=20>ESC  RESUME</size></color>";
        if (p == Phase.Caught)
            overlayText.text = "<size=88><b>CAUGHT</b></size>\n\n<size=24>" + Mathf.RoundToInt(elapsed) + " S  /  " + RoomsReached() + " ROOMS</size>\n\n<color=#F4DF3B><size=20>R  TRY AGAIN</size></color>";
    }
    void OnApplicationFocus(bool focused) { if (!focused && phase == Phase.Playing) SetPhase(Phase.Paused); }
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
        if (phase == Phase.Title) UpdateTitleSequence(dt);
        else if (phase == Phase.Playing && streamedPlay)
        {
            elapsed += dt;
            flashTime -= dt;
            UpdateTitleSequence(dt);
            UpdateStreamedPlay(dt);
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
        if (!streamedPlay) return;
        var rule = roomStream == null ? RoomRule.Lobby : roomStream.CurrentRule;
        var roomName = rule == RoomRule.Office ? "LEVEL 4 / OFFICE" : rule == RoomRule.Run ? "LEVEL ! / RUN" : rule == RoomRule.Shift ? "LEVEL 0 / SHIFT" : rule == RoomRule.Exit ? "EXIT / COLD THRESHOLD" : "LOBBY / THRESHOLD";
        var released = hunterBrain != null && hunterBrain.Released;
        var threat = !released ? "THREAT  /  QUIET" : hunterBrain.State == HunterState.BreakDoor ? "RELAY  /  BREAKING DOOR" : "RELAY  /  " + hunterBrain.State.ToString().ToUpperInvariant();
        roomMetaText.text = play ? "ROOM " + RoomsReached().ToString("00") + "  /  ACTIVE" : "";
        roomText.text = play ? roomName : "";
        threatStateText.text = play ? threat : "";
        distanceText.text = play ? (released ? "RELAY  " + Mathf.RoundToInt(RelayDistance()) + " M" : "RELAY  /  OUT OF RANGE") : "";
        crosshair.enabled = play;
        contextText.text = play && flashTime > 0f ? flash : "";
        if (roomPanel != null) roomPanel.SetActive(play);
        if (threatPanel != null) threatPanel.SetActive(play);
        if (contextPanel != null) contextPanel.SetActive(play && contextText.text != "");
    }

    int RoomsReached() => roomStream == null ? 1 : roomStream.CurrentRoomNumber - startRoom + 1;
    float RelayDistance() => hunterBrain == null || !hunterBrain.Released ? -1f : Vector2.Distance(playerPos, hunterBrain.Position);
    void ApplyGameplayHudAlpha()
    {
        if (roomHudGroup != null) roomHudGroup.alpha = gameplayHudAlpha;
        if (threatHudGroup != null) threatHudGroup.alpha = gameplayHudAlpha;
        if (contextHudGroup != null) contextHudGroup.alpha = gameplayHudAlpha;
        if (crosshairHudGroup != null) crosshairHudGroup.alpha = gameplayHudAlpha;
    }
    void Flash(string message, float duration = 3f) { flash = message; flashTime = duration; }
    void Event(string kind, string detail) { events.Add(elapsed.ToString("0.000", CultureInfo.InvariantCulture) + "," + kind + ",\"" + detail.Replace("\"", "\"\"") + "\"," + RelayDistance().ToString("0.00", CultureInfo.InvariantCulture)); }
    void End()
    {
        if (phase != Phase.Playing) return;
        SetPhase(Phase.Caught); Sound(caughtClip, playerPos); Event("outcome", "caught");
        string dir = Application.persistentDataPath; Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, "events-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".csv"), "time_s,event,detail,relay_m\n" + string.Join("\n", events));
        Log(phase + " · " + elapsed.ToString("0.0") + " s");
    }
    static void Log(string message) => Debug.Log("[FrontRooms3D] " + message);

}
