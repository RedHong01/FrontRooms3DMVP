using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// One-step URP setup for FrontRooms: the pipeline asset (Forward+, soft
/// shadows on every fixture, HDR), the renderer with SSAO, the global post
/// stack, and one editable material asset per room surface. Re-running it
/// updates the generated values in place and keeps every asset GUID, so it is
/// safe to run after changing a texture or a number below.
/// Menu: FrontRooms → Rendering → Set up URP, post and surfaces.
/// Batch: -executeMethod FrontRoomsRenderSetup.RunBatch
/// </summary>
public static class FrontRoomsRenderSetup
{
    const string SettingsDir = "Assets/Settings";
    const string PipelinePath = SettingsDir + "/FrontRooms_URP.asset";
    const string RendererPath = SettingsDir + "/FrontRooms_URP_Renderer.asset";
    const string PostPath = "Assets/Resources/Rendering/FrontRoomsPost.asset";
    const string SurfaceDir = "Assets/Resources/Surfaces";
    const string TextureDir = SurfaceDir + "/Textures";

    // World tile sizes. Each divides the room stream's 256 m rebase.
    const float Roll = 256f / 373f;      // one 27" wallpaper roll
    const float FourFoot = 256f / 210f;  // 4' ceiling grid / 2 x 2' carpet tiles / 4 x 12" VCT

    [MenuItem("FrontRooms/Rendering/Set up URP, post and surfaces")]
    public static void SetUp()
    {
        Directory.CreateDirectory(SettingsDir);
        Directory.CreateDirectory(Path.GetDirectoryName(PostPath));
        var pipeline = EnsurePipeline();
        EnsurePost();
        EnsureSurfaces();
        ConvertSceneMaterials();
        GraphicsSettings.defaultRenderPipeline = pipeline;
        var activeLevel = QualitySettings.GetQualityLevel();
        for (var i = 0; i < QualitySettings.names.Length; i++)
        {
            QualitySettings.SetQualityLevel(i, false);
            QualitySettings.renderPipeline = pipeline;
        }
        QualitySettings.SetQualityLevel(activeLevel, false);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("[FrontRoomsRender] URP pipeline, post profile and " + SurfaceDefs.Length + " surface materials are up to date.");
    }

    public static void RunBatch() => SetUp();

    static UniversalRenderPipelineAsset EnsurePipeline()
    {
        var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(RendererPath);
        if (renderer == null)
        {
            // URP's own factory fills in the post-process data and shader references.
            var factory = typeof(UniversalRenderPipelineAsset).GetMethod("CreateRendererAsset", BindingFlags.Static | BindingFlags.NonPublic);
            if (factory != null)
                renderer = factory.Invoke(null, new object[] { RendererPath, RendererType.UniversalRenderer, false, "Renderer" }) as UniversalRendererData;
            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                AssetDatabase.CreateAsset(renderer, RendererPath);
            }
        }
        renderer.renderingMode = RenderingMode.ForwardPlus;
        EditorUtility.SetDirty(renderer);
        EnsureSsao(renderer);

        var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
        if (pipeline == null)
        {
            pipeline = UniversalRenderPipelineAsset.Create(renderer);
            AssetDatabase.CreateAsset(pipeline, PipelinePath);
        }
        var so = new SerializedObject(pipeline);
        Set(so, "m_SupportsHDR", true);
        Set(so, "m_MSAA", 4);
        Set(so, "m_RenderScale", 1f);
        Set(so, "m_RequireDepthTexture", true);
        Set(so, "m_MainLightShadowsSupported", true);
        Set(so, "m_AdditionalLightsRenderingMode", (int)LightRenderingMode.PerPixel);
        Set(so, "m_AdditionalLightsPerObjectLimit", 8);
        Set(so, "m_AdditionalLightShadowsSupported", true);
        Set(so, "m_AdditionalLightsShadowmapResolution", 4096);
        Set(so, "m_ShadowDistance", 40f);
        Set(so, "m_ShadowCascadeCount", 2);
        Set(so, "m_SoftShadowsSupported", true);
        Set(so, "m_SoftShadowQuality", (int)SoftShadowQuality.High);
        Set(so, "m_ShadowDepthBias", .6f);
        Set(so, "m_ShadowNormalBias", .6f);
        Set(so, "m_ColorGradingMode", (int)ColorGradingMode.HighDynamicRange);
        Set(so, "m_ColorGradingLutSize", 32);
        so.ApplyModifiedPropertiesWithoutUndo();
        EditorUtility.SetDirty(pipeline);
        return pipeline;
    }

    static void EnsureSsao(UniversalRendererData renderer)
    {
        var ssaoType = typeof(ScreenSpaceAmbientOcclusion);
        var feature = renderer.rendererFeatures.FirstOrDefault(f => f != null && f.GetType() == ssaoType);
        if (feature == null)
        {
            feature = (ScriptableRendererFeature)ScriptableObject.CreateInstance(ssaoType);
            feature.name = "Screen Space Ambient Occlusion";
            AssetDatabase.AddObjectToAsset(feature, renderer);
            AssetDatabase.SaveAssets();
            AssetDatabase.TryGetGUIDAndLocalFileIdentifier(feature, out _, out long localId);
            var rso = new SerializedObject(renderer);
            var list = rso.FindProperty("m_RendererFeatures");
            var map = rso.FindProperty("m_RendererFeatureMap");
            list.arraySize++;
            list.GetArrayElementAtIndex(list.arraySize - 1).objectReferenceValue = feature;
            map.arraySize = list.arraySize;
            map.GetArrayElementAtIndex(map.arraySize - 1).longValue = localId;
            rso.ApplyModifiedPropertiesWithoutUndo();
        }
        // Room-scale contact shadows: corners, baseboards, furniture legs, the
        // gap under doors. Radius is in metres.
        var fso = new SerializedObject(feature);
        Set(fso, "m_Settings.Source", 1);        // depth normals
        Set(fso, "m_Settings.NormalSamples", 2); // high
        Set(fso, "m_Settings.Intensity", 1.6f);
        Set(fso, "m_Settings.DirectLightingStrength", .35f);
        Set(fso, "m_Settings.Radius", .45f);
        Set(fso, "m_Settings.Falloff", 40f);
        Set(fso, "m_Settings.Samples", 0);       // high
        Set(fso, "m_Settings.BlurQuality", 0);   // high
        fso.ApplyModifiedPropertiesWithoutUndo();
        EditorUtility.SetDirty(feature);
        EditorUtility.SetDirty(renderer);
    }

    /// <summary>
    /// The film look: practical fluorescents only, a slightly green-yellow
    /// white balance, soft halation on the tubes, a haze that lifts the blacks
    /// like a CRT, fine grain and a little lens falloff. No glossy contrast.
    /// </summary>
    static void EnsurePost()
    {
        var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(PostPath);
        if (profile == null)
        {
            profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, PostPath);
        }

        var tone = Get<Tonemapping>(profile);
        tone.mode.Override(TonemappingMode.ACES);

        var bloom = Get<Bloom>(profile);
        bloom.threshold.Override(1.05f);
        bloom.intensity.Override(.55f);
        bloom.scatter.Override(.72f);
        bloom.tint.Override(new Color(1f, .93f, .78f));
        bloom.highQualityFiltering.Override(true);

        var white = Get<WhiteBalance>(profile);
        white.temperature.Override(9f);
        white.tint.Override(-7f); // toward green: Cox's "warm green-yellow"

        var color = Get<ColorAdjustments>(profile);
        color.postExposure.Override(.15f);
        color.contrast.Override(-6f);
        color.saturation.Override(-8f);

        var lgg = Get<LiftGammaGain>(profile);
        lgg.lift.Override(new Vector4(1f, .99f, .94f, .035f)); // lifted, slightly warm blacks: the haze

        var smh = Get<ShadowsMidtonesHighlights>(profile);
        smh.shadows.Override(new Vector4(.97f, 1f, .94f, 0f));
        smh.highlights.Override(new Vector4(1f, .99f, .93f, 0f));

        var vignette = Get<Vignette>(profile);
        vignette.intensity.Override(.26f);
        vignette.smoothness.Override(.45f);
        vignette.color.Override(new Color(.05f, .045f, .03f));

        var grain = Get<FilmGrain>(profile);
        grain.type.Override(FilmGrainLookup.Medium3);
        grain.intensity.Override(.22f);
        grain.response.Override(.75f);

        var ca = Get<ChromaticAberration>(profile);
        ca.intensity.Override(.06f);

        var lens = Get<LensDistortion>(profile);
        lens.intensity.Override(-.04f); // wide-lens barrel, very slight
        lens.scale.Override(1.01f);

        EditorUtility.SetDirty(profile);
    }

    static T Get<T>(VolumeProfile profile) where T : VolumeComponent
    {
        if (!profile.TryGet<T>(out var component))
        {
            component = profile.Add<T>(true);
            component.name = typeof(T).Name;
            AssetDatabase.AddObjectToAsset(component, profile);
        }
        component.active = true;
        return component;
    }

    // ---------------------------------------------------------------- surfaces

    sealed class SurfaceDef
    {
        public string name;          // material asset name, also FrontRoomsSurfaces key
        public string texture;       // texture stem in Surfaces/Textures, or null for a plain colour
        public Vector2 tile;         // metres per texture repeat
        public bool meshUV;
        public Color tint = Color.white;
        public float bump = 1f, smooth = 1f, metallic, occlusion = .8f;
        public float macroTone = .3f, macroDirt = .2f, stain, wet, floorGrime, ceilingGrime;
        public float ceilingHeight = 2.9f;
        public Color stainColor = new Color(.42f, .31f, .16f);
        public string emission;      // emission texture stem
        public Color emissionColor = Color.black;
        public Vector4 st = new Vector4(1, 1, 0, 0); // texture scale/offset after the metre tile
    }

    static readonly SurfaceDef[] SurfaceDefs =
    {
        // Level 0 family: Lobby, Shift (stained), Exit (cold print run).
        new SurfaceDef { name = "L0_Wallpaper", texture = "Wallpaper_Chevron", tile = new Vector2(Roll, Roll * 1.5f), bump = .8f, macroTone = .45f, macroDirt = .3f, stain = .18f, floorGrime = .6f, ceilingGrime = .5f },
        new SurfaceDef { name = "L0_Wallpaper_Shift", texture = "Wallpaper_Chevron", tile = new Vector2(Roll, Roll * 1.5f), tint = new Color(.9f, .88f, .8f), bump = .8f, macroTone = .6f, macroDirt = .45f, stain = .45f, floorGrime = .8f, ceilingGrime = .85f },
        new SurfaceDef { name = "L0_Carpet", texture = "Carpet_LoopPile", tile = Vector2.one, macroTone = .4f, macroDirt = .35f, wet = .55f },
        new SurfaceDef { name = "L0_Carpet_Shift", texture = "Carpet_LoopPile", tile = Vector2.one, tint = new Color(.92f, .9f, .84f), macroTone = .5f, macroDirt = .5f, wet = .85f },
        new SurfaceDef { name = "L0_Ceiling", texture = "Ceiling_Fissured", tile = new Vector2(FourFoot, FourFoot), macroTone = .25f, stain = .22f },
        new SurfaceDef { name = "L0_Ceiling_Shift", texture = "Ceiling_Fissured", tile = new Vector2(FourFoot, FourFoot), tint = new Color(.93f, .92f, .86f), macroTone = .45f, stain = .55f },
        new SurfaceDef { name = "Exit_Wallpaper", texture = "Wallpaper_Chevron_Cold", tile = new Vector2(Roll, Roll * 1.5f), bump = .8f, macroTone = .35f, macroDirt = .2f, floorGrime = .4f, ceilingGrime = .2f, stainColor = new Color(.30f, .34f, .32f) },
        new SurfaceDef { name = "Exit_Carpet", texture = "Carpet_LoopPile", tile = Vector2.one, tint = new Color(.66f, .72f, .74f), macroTone = .35f, wet = .3f },

        // Level 4 / Office.
        new SurfaceDef { name = "Office_Wall", texture = "Office_Drywall", tile = new Vector2(FourFoot, FourFoot), bump = .8f, macroTone = .3f, macroDirt = .2f, floorGrime = .4f, ceilingGrime = .2f },
        new SurfaceDef { name = "Office_Carpet", texture = "Office_CarpetTile", tile = new Vector2(FourFoot, FourFoot), bump = .8f, macroTone = .3f, macroDirt = .3f, wet = .15f },
        new SurfaceDef { name = "Office_Ceiling", texture = "Office_Ceiling2x2", tile = new Vector2(FourFoot, FourFoot), macroTone = .25f, stain = .3f },
        new SurfaceDef { name = "Office_Fabric", texture = "Office_CubicleFabric", tile = Vector2.one, meshUV = true, macroTone = .2f },
        new SurfaceDef { name = "Office_Louver", texture = "Office_Louver", tile = new Vector2(FourFoot * .5f, FourFoot * .5f), meshUV = true, metallic = .85f, macroTone = 0f, macroDirt = 0f, emission = "Office_Louver", emissionColor = new Color(1.6f, 1.55f, 1.4f) },
        new SurfaceDef { name = "Office_BlackedGlass", tint = new Color(.018f, .02f, .022f), smooth = .95f, macroTone = .1f },

        // Level ! / Run: a hospital corridor lit red by its exit signs.
        new SurfaceDef { name = "Run_Wall", texture = "Run_HospitalWall", tile = new Vector2(FourFoot, FourFoot), bump = .6f, macroTone = .25f, macroDirt = .25f, floorGrime = .45f, ceilingGrime = .15f },
        new SurfaceDef { name = "Run_Floor", texture = "Run_VCT", tile = new Vector2(FourFoot, FourFoot), macroTone = .2f, macroDirt = .35f },
        new SurfaceDef { name = "Run_Ceiling", texture = "Office_Ceiling2x2", tile = new Vector2(FourFoot, FourFoot), tint = new Color(1.04f, 1.04f, 1.04f), macroTone = .2f, stain = .2f },
        // The sign faces are quads whose U runs right-to-left as seen from the
        // front, so the print is flipped back with a -1 scale and +1 offset.
        new SurfaceDef { name = "Run_ExitSign", texture = "Run_ExitSign", tile = new Vector2(.36f, .18f), meshUV = true, macroTone = 0f, macroDirt = 0f, emission = "Run_ExitSign", emissionColor = new Color(3.2f, 3.2f, 3.2f), st = new Vector4(-1, 1, 1, 0) },

        // Shared construction.
        new SurfaceDef { name = "Door_Veneer", texture = "DoorVeneer", tile = new Vector2(1.12f, 2.62f), meshUV = true, macroTone = .15f, macroDirt = .1f },
        new SurfaceDef { name = "Painted_Metal", texture = "PaintedMetal", tile = Vector2.one, meshUV = true, macroTone = .15f, macroDirt = .15f },
        new SurfaceDef { name = "Troffer_Lens", texture = "TrofferLens", tile = new Vector2(FourFoot * .5f, FourFoot), meshUV = true, macroTone = 0f, macroDirt = 0f, emission = "TrofferLens", emissionColor = new Color(2.2f, 2.1f, 1.8f) },
        new SurfaceDef { name = "Cove_Base", tint = new Color(.23f, .19f, .14f), smooth = .38f, macroTone = .2f },
    };

    static void EnsureSurfaces()
    {
        Directory.CreateDirectory(SurfaceDir);
        var shader = Shader.Find("FrontRooms/Surface");
        if (shader == null)
        {
            Debug.LogError("[FrontRoomsRender] FrontRooms/Surface shader is missing; surface materials were not generated.");
            return;
        }
        var macro = Tex("MacroWear_M");
        foreach (var d in SurfaceDefs)
        {
            var path = SurfaceDir + "/" + d.name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(shader) { name = d.name };
                AssetDatabase.CreateAsset(m, path);
            }
            m.shader = shader;
            if (d.texture != null)
            {
                m.SetTexture("_BaseMap", Tex(d.texture + "_A"));
                m.SetTexture("_BumpMap", Tex(d.texture + "_N"));
                m.SetTexture("_MaskMap", Tex(d.texture + "_S"));
            }
            m.SetColor("_BaseColor", d.tint);
            m.SetTextureScale("_BaseMap", new Vector2(d.st.x, d.st.y));
            m.SetTextureOffset("_BaseMap", new Vector2(d.st.z, d.st.w));
            m.SetVector("_TileSize", new Vector4(d.tile.x <= 0 ? 1 : d.tile.x, d.tile.y <= 0 ? 1 : d.tile.y, 0, 0));
            m.SetFloat("_BumpScale", d.bump);
            m.SetFloat("_Smoothness", d.smooth);
            m.SetFloat("_Metallic", d.metallic);
            m.SetFloat("_OcclusionStrength", d.occlusion);
            m.SetTexture("_MacroMap", macro);
            m.SetFloat("_MacroTone", d.macroTone);
            m.SetFloat("_MacroDirt", d.macroDirt);
            m.SetColor("_StainColor", d.stainColor);
            m.SetFloat("_StainStrength", d.stain);
            m.SetFloat("_WetStrength", d.wet);
            m.SetFloat("_FloorGrime", d.floorGrime);
            m.SetFloat("_CeilingGrime", d.ceilingGrime);
            m.SetFloat("_CeilingHeight", d.ceilingHeight);
            m.SetFloat("_MeshUV", d.meshUV ? 1f : 0f);
            if (d.meshUV) m.EnableKeyword("_FR_MESH_UV"); else m.DisableKeyword("_FR_MESH_UV");
            if (d.emission != null)
            {
                m.SetTexture("_EmissionMap", Tex(d.emission + "_E"));
                m.SetColor("_EmissionColor", d.emissionColor);
                m.SetFloat("_UseEmission", 1f);
                m.EnableKeyword("_EMISSION");
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            else
            {
                m.SetFloat("_UseEmission", 0f);
                m.DisableKeyword("_EMISSION");
            }
            EditorUtility.SetDirty(m);
        }
    }

    /// <summary>
    /// The scene stores a few materials inline (the Relay rig's body, head and
    /// detail). Move any that still use the built-in Standard shader to URP
    /// Lit, keeping colour, smoothness, metal and emission.
    /// </summary>
    static void ConvertSceneMaterials()
    {
        const string scenePath = "Assets/Scenes/FrontRooms3D.unity";
        if (!File.Exists(scenePath)) return;
        var lit = Shader.Find("Universal Render Pipeline/Lit");
        if (lit == null) return;
        // Never swap the scene under someone working in the editor: convert
        // the open scene in place, and only open it automatically in batch mode.
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (scene.path != scenePath)
        {
            if (!Application.isBatchMode)
            {
                Debug.LogWarning("[FrontRoomsRender] Open " + scenePath + " and run the setup again to convert its inline materials.");
                return;
            }
            scene = UnityEditor.SceneManagement.EditorSceneManager.OpenScene(scenePath, UnityEditor.SceneManagement.OpenSceneMode.Single);
        }
        var converted = 0;
        foreach (var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            foreach (var m in renderer.sharedMaterials)
            {
                if (m == null || m.shader == null || m.shader.name != "Standard") continue;
                var color = m.HasProperty("_Color") ? m.GetColor("_Color") : Color.white;
                var gloss = m.HasProperty("_Glossiness") ? m.GetFloat("_Glossiness") : .3f;
                var metal = m.HasProperty("_Metallic") ? m.GetFloat("_Metallic") : 0f;
                var emissive = m.IsKeywordEnabled("_EMISSION");
                var emission = m.HasProperty("_EmissionColor") ? m.GetColor("_EmissionColor") : Color.black;
                var tex = m.HasProperty("_MainTex") ? m.GetTexture("_MainTex") : null;
                m.shader = lit;
                m.SetColor("_BaseColor", color);
                if (tex != null) m.SetTexture("_BaseMap", tex);
                m.SetFloat("_Smoothness", gloss);
                m.SetFloat("_Metallic", metal);
                if (emissive) { m.EnableKeyword("_EMISSION"); m.SetColor("_EmissionColor", emission); }
                converted++;
            }
        }
        // No realtime GI: Trilight stands in for the bounce. The ceiling faces
        // down and takes the ground colour, so that is the warm carpet bounce;
        // walls take the equator; floors the dim sky.
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(.20f, .19f, .15f);
        RenderSettings.ambientEquatorColor = new Color(.26f, .24f, .17f);
        RenderSettings.ambientGroundColor = new Color(.40f, .36f, .24f);
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.ExponentialSquared;
        RenderSettings.fogColor = new Color(.16f, .15f, .11f);
        RenderSettings.fogDensity = .014f;
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(scene);
        UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
        Debug.Log("[FrontRoomsRender] Scene materials moved to URP Lit: " + converted);
    }

    static Texture2D Tex(string stem)
    {
        var path = TextureDir + "/" + stem + ".png";
        var t = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        if (t == null) Debug.LogWarning("[FrontRoomsRender] Missing surface texture " + path);
        return t;
    }

    static void Set(SerializedObject so, string path, object value)
    {
        var p = so.FindProperty(path);
        if (p == null)
        {
            Debug.LogWarning("[FrontRoomsRender] " + so.targetObject.GetType().Name + " has no serialized field " + path + "; kept its default.");
            return;
        }
        switch (p.propertyType)
        {
            case SerializedPropertyType.Boolean: p.boolValue = Convert.ToBoolean(value); break;
            case SerializedPropertyType.Float: p.floatValue = Convert.ToSingle(value); break;
            case SerializedPropertyType.Integer: p.intValue = Convert.ToInt32(value); break;
            case SerializedPropertyType.Enum: p.intValue = Convert.ToInt32(value); break;
            default: Debug.LogWarning("[FrontRoomsRender] Unsupported field type for " + path); break;
        }
    }
}

/// <summary>
/// Import rules for the generated surface textures: albedo/emission in sRGB,
/// normals as normal maps, masks linear; full mip chain, trilinear and 16x
/// anisotropy so floors and ceilings stay sharp at grazing angles.
/// </summary>
public sealed class FrontRoomsSurfaceTextureImporter : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        if (!assetPath.Replace('\\', '/').Contains("/Resources/Surfaces/Textures/")) return;
        var importer = (TextureImporter)assetImporter;
        var stem = Path.GetFileNameWithoutExtension(assetPath);
        importer.mipmapEnabled = true;
        importer.filterMode = FilterMode.Trilinear;
        importer.anisoLevel = 16;
        importer.wrapMode = stem.StartsWith("Run_ExitSign") ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
        importer.maxTextureSize = 4096;
        importer.textureCompression = TextureImporterCompression.CompressedHQ;
        importer.alphaSource = TextureImporterAlphaSource.FromInput;
        if (stem.EndsWith("_N"))
        {
            importer.textureType = TextureImporterType.NormalMap;
            importer.sRGBTexture = false;
        }
        else
        {
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = stem.EndsWith("_A") || stem.EndsWith("_E");
        }
    }
}
