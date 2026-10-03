using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// Orthographic three-view concept sheets for the prop kit: every kit asset
/// alone at the origin of an empty scene, neutral studio light, transparent
/// background, one round scale per sheet (pngPpm in the manifest) so sizes compare
/// directly on each sheet (SheetScales). Third-angle views:
///   front  camera on +Z looking -Z (the kit's front faces +Z)
///   side   the asset's right as seen from its front (Unity -X), camera on -X
///   top    camera above, the asset's front toward the bottom of the image
///   persp  a 3/4 hero from the front-left (the look-dev close-up angle)
/// Each image is the asset extent x pngPpm plus Padding on every side,
/// so the ground (y = 0) sits exactly Padding px above the bottom edge of the
/// front and side images. The studio rig (key upper-left of the camera with
/// soft shadows, dim fill from the right, flat 0.55 ambient, no fog) turns
/// with each camera so every view of every asset is lit the same way.
/// Writes &lt;Name&gt;_front/_side/_top/_persp.png and manifest.json.
/// Batch: -executeMethod FrontRoomsThreeView.RunBatch [-threeViewOut DIR] [-threeViewOnly A,B]
/// (needs graphics: do not pass -nographics).
/// </summary>
public static class FrontRoomsThreeView
{
    /// <summary>
    /// Sheet scales in px per metre on the 1920 x 1080 Figma sheet. Each asset
    /// gets the largest step whose third-angle layout (W + D wide, D + H tall)
    /// fits the sheet's drawing area, so every sheet reads at a round scale.
    /// </summary>
    static readonly float[] SheetScales = { 2000f, 1000f, 500f, 250f, 125f };
    const float DrawingWidth = 1080f, DrawingHeight = 688f;
    const float FurnitureScale = 250f;   // anything 0.75 m or larger shares one scale so furniture compares sheet to sheet
    const float FurnitureSize = .75f;
    const float Oversample = 2f;     // PNG px per sheet px
    public const int Padding = 16;   // PNG px of clear margin around the bounds
    const int HeroWidth = 1152, HeroHeight = 864;
    const float HeroFov = 30f;
    const int MaxTarget = 8192;      // largest supersampled target edge; no MSAA, the supersample is the AA
    static readonly Color Ambient = new Color(.55f, .55f, .55f);
    const float KeyIntensity = 1.0f;
    const float FillIntensity = .3f;

    enum View { Front, Side, Top, Persp }

    [MenuItem("FrontRooms/Rendering/Capture prop kit three-views")]
    public static void Capture() => Run(null, null);

    public static void RunBatch()
    {
        var args = Environment.GetCommandLineArgs();
        string outDir = null, only = null;
        for (var i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "-threeViewOut") outDir = args[i + 1];
            if (args[i] == "-threeViewOnly") only = args[i + 1];
        }
        Run(outDir, only);
    }

    static void Run(string outDir, string only)
    {
        if (string.IsNullOrEmpty(outDir))
            outDir = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "threeview");
        Directory.CreateDirectory(outDir);
        var filter = string.IsNullOrEmpty(only) ? null : new HashSet<string>(only.Split(','));

        if (AssetDatabase.IsValidFolder("Assets/Resources/Props/Models"))
            AssetDatabase.ImportAsset("Assets/Resources/Props/Models", ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate);

        var previous = EditorSceneManager.GetActiveScene();
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, Application.isBatchMode ? NewSceneMode.Single : NewSceneMode.Additive);
        EditorSceneManager.SetActiveScene(scene);

        // Tight shadow range so small props get crisp contact shadows.
        var urp = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
        var oldShadowDistance = urp != null ? urp.shadowDistance : 0f;
        var oldCascades = urp != null ? urp.shadowCascadeCount : 0;
        var oldFog = RenderSettings.fog;
        Cubemap environment = null;
        var entries = new List<string>();
        var failed = new List<string>();
        try
        {
            if (urp != null) { urp.shadowDistance = 12f; urp.shadowCascadeCount = 1; }
            environment = Studio();

            var rigRoot = new GameObject("THREEVIEW rig").transform;
            var key = MakeLight(rigRoot, "key", KeyIntensity, LightShadows.Soft);
            var fill = MakeLight(rigRoot, "fill", FillIntensity, LightShadows.None);

            var cameraObject = new GameObject("THREEVIEW camera");
            cameraObject.transform.SetParent(rigRoot, false);
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0f, 0f, 0f, 0f);
            camera.allowHDR = false;
            camera.allowMSAA = false;
            var data = camera.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = false;
            data.antialiasing = AntialiasingMode.None;
            data.renderShadows = true;
            data.dithering = false;

            foreach (var assetName in FrontRoomsKitLibrary.AllNames())
            {
                if (assetName.StartsWith("Kit_AxisProbe", StringComparison.Ordinal) || assetName.StartsWith("Kit_ZZ", StringComparison.Ordinal)) continue;
                if (filter != null && !filter.Contains(assetName)) continue;
                GameObject instance = null;
                try
                {
                    instance = FrontRoomsKitLibrary.Spawn(assetName, null, Vector3.zero, 0f, null, false);
                    if (instance == null) { failed.Add(assetName + " (no model)"); continue; }
                    ForceLod0(instance);
                    // Studio shadows on every piece, small ones included.
                    foreach (var r in instance.GetComponentsInChildren<MeshRenderer>())
                        if (r.enabled) r.shadowCastingMode = ShadowCastingMode.On;
                    var info = FrontRoomsKitLibrary.GetInfo(assetName);
                    var bounds = Frame(instance, info);
                    var sheet = SheetScale(bounds.size);
                    var px = new Dictionary<View, Vector2Int>();
                    foreach (View view in Enum.GetValues(typeof(View)))
                    {
                        var size = Shoot(camera, key, fill, view, bounds, sheet * Oversample, Path.Combine(outDir, assetName + "_" + view.ToString().ToLowerInvariant() + ".png"));
                        px[view] = size;
                    }
                    entries.Add(Entry(assetName, info, bounds, sheet, px));
                    Debug.Log("[ThreeView] " + assetName + " ok");
                }
                catch (Exception e)
                {
                    failed.Add(assetName + " (" + e.Message + ")");
                    Debug.LogException(e);
                }
                finally
                {
                    if (instance != null) UnityEngine.Object.DestroyImmediate(instance);
                }
            }
            UnityEngine.Object.DestroyImmediate(rigRoot.gameObject);

            var json = new StringBuilder();
            json.Append("{\n \"oversample\": ").Append(F(Oversample)).Append(",\n \"padding\": ").Append(Padding)
                .Append(",\n \"assets\": [\n").Append(string.Join(",\n", entries)).Append("\n ],\n \"failed\": [");
            for (var i = 0; i < failed.Count; i++) json.Append(i > 0 ? ", " : "").Append(Q(failed[i]));
            json.Append("]\n}\n");
            File.WriteAllText(Path.Combine(outDir, "manifest.json"), json.ToString());
            Debug.Log("[ThreeView] Wrote " + entries.Count + " assets to " + outDir + (failed.Count > 0 ? "; failed: " + string.Join(", ", failed) : ""));
        }
        finally
        {
            if (urp != null) { urp.shadowDistance = oldShadowDistance; urp.shadowCascadeCount = oldCascades; }
            RenderSettings.fog = oldFog;
            if (environment != null) UnityEngine.Object.DestroyImmediate(environment);
            if (!Application.isBatchMode)
            {
                EditorSceneManager.CloseScene(scene, true);
                if (previous.IsValid()) EditorSceneManager.SetActiveScene(previous);
            }
        }
    }

    // ------------------------------------------------------------------ studio

    /// <summary>Flat grey ambient, no fog, and a soft grey studio cube for reflections (bright top, dark floor).</summary>
    static Cubemap Studio()
    {
        RenderSettings.fog = false;
        RenderSettings.skybox = null;
        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = Ambient;
        RenderSettings.ambientIntensity = 1f;
        var cube = new Cubemap(16, TextureFormat.RGBA32, false) { name = "THREEVIEW studio" };
        foreach (CubemapFace face in Enum.GetValues(typeof(CubemapFace)))
        {
            if (face == CubemapFace.Unknown) continue;
            var c = face == CubemapFace.PositiveY ? new Color(.85f, .85f, .85f) : face == CubemapFace.NegativeY ? new Color(.22f, .22f, .22f) : new Color(.5f, .5f, .5f);
            var pixels = new Color[16 * 16];
            for (var i = 0; i < pixels.Length; i++) pixels[i] = c;
            cube.SetPixels(pixels, face);
        }
        cube.Apply();
        RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
        RenderSettings.customReflectionTexture = cube;
        RenderSettings.reflectionIntensity = 1f;
        DynamicGI.UpdateEnvironment();
        return cube;
    }

    static Light MakeLight(Transform parent, string name, float intensity, LightShadows shadows)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var light = go.AddComponent<Light>();
        light.type = LightType.Directional;
        light.color = Color.white;
        light.intensity = intensity;
        light.shadows = shadows;
        light.shadowStrength = .75f;
        light.shadowBias = .02f;
        light.shadowNormalBias = .2f;
        return light;
    }

    /// <summary>Key over the camera's upper-left shoulder; fill low from the camera's right.</summary>
    static void PlaceRig(Light key, Light fill, Quaternion cameraRotation)
    {
        var keyFrom = new Vector3(-.55f, .7f, -.6f);   // camera space: left, up, toward the camera
        var fillFrom = new Vector3(.8f, .1f, -.55f);
        key.transform.rotation = Quaternion.LookRotation(cameraRotation * -keyFrom.normalized, cameraRotation * Vector3.up);
        fill.transform.rotation = Quaternion.LookRotation(cameraRotation * -fillFrom.normalized, cameraRotation * Vector3.up);
    }

    // ------------------------------------------------------------------- views

    static Bounds Frame(GameObject instance, FrontRoomsKitLibrary.Info info)
    {
        Bounds? rendered = null;
        foreach (var r in instance.GetComponentsInChildren<MeshRenderer>())
        {
            if (!r.enabled) continue;
            if (rendered == null) rendered = r.bounds;
            else { var b = rendered.Value; b.Encapsulate(r.bounds); rendered = b; }
        }
        if (info != null && info.boundsMin != null && info.boundsMax != null)
        {
            var b = new Bounds((info.Min + info.Max) * .5f, info.Size);
            if (rendered.HasValue)
            {
                var d = Vector3.Max(rendered.Value.max - b.max, b.min - rendered.Value.min);
                if (d.x > .005f || d.y > .005f || d.z > .005f)
                    Debug.LogWarning("[ThreeView] " + instance.name + " renders outside its sidecar bounds by " + d.ToString("F3"));
            }
            return b;
        }
        return rendered ?? new Bounds(Vector3.up * .5f, Vector3.one);
    }

    static float SheetScale(Vector3 size)
    {
        var fit = Mathf.Min(DrawingWidth / Mathf.Max(.01f, size.x + size.z), DrawingHeight / Mathf.Max(.01f, size.z + size.y));
        if (Mathf.Max(size.x, Mathf.Max(size.y, size.z)) >= FurnitureSize) fit = Mathf.Min(fit, FurnitureScale);
        foreach (var step in SheetScales) if (step <= fit) return step;
        return SheetScales[SheetScales.Length - 1];
    }

    static Vector2Int Shoot(Camera camera, Light key, Light fill, View view, Bounds b, float ppm, string path)
    {
        int w, h;
        Quaternion rotation;
        Vector3 position;
        var reach = b.extents.magnitude + 1f;
        if (view == View.Persp)
        {
            w = HeroWidth;
            h = HeroHeight;
            // Look-dev hero angle: 35 deg to the front-left, 22 deg above.
            var dir = Quaternion.Euler(0f, -35f, 0f) * new Vector3(0f, Mathf.Sin(22f * Mathf.Deg2Rad), Mathf.Cos(22f * Mathf.Deg2Rad));
            rotation = Quaternion.LookRotation(-dir, Vector3.up);
            position = FitPerspective(b, rotation, HeroFov, (float)w / h, .86f);
            camera.orthographic = false;
            camera.fieldOfView = HeroFov;
            camera.nearClipPlane = .01f;
            camera.farClipPlane = (position - b.center).magnitude + reach * 2f;
        }
        else
        {
            Vector2 extent;
            switch (view)
            {
                case View.Front:
                    rotation = Quaternion.Euler(0f, 180f, 0f);
                    position = new Vector3(b.center.x, b.center.y, b.max.z + 1f);
                    extent = new Vector2(b.size.x, b.size.y);
                    break;
                case View.Side:
                    rotation = Quaternion.Euler(0f, 90f, 0f);
                    position = new Vector3(b.min.x - 1f, b.center.y, b.center.z);
                    extent = new Vector2(b.size.z, b.size.y);
                    break;
                default:
                    rotation = Quaternion.Euler(90f, 180f, 0f);
                    position = new Vector3(b.center.x, b.max.y + 1f, b.center.z);
                    extent = new Vector2(b.size.x, b.size.z);
                    break;
            }
            w = Mathf.CeilToInt(extent.x * ppm - .01f) + Padding * 2;
            h = Mathf.CeilToInt(extent.y * ppm - .01f) + Padding * 2;
            camera.orthographic = true;
            camera.orthographicSize = h * .5f / ppm;
            camera.nearClipPlane = .01f;
            camera.farClipPlane = b.size.magnitude + 2f;
            // Snap the image centre so the ground and the bounds land on whole pixels:
            // shift by the rounding slack so the bounds' min edge sits exactly Padding px in.
            var slack = new Vector2(w - Padding * 2 - extent.x * ppm, h - Padding * 2 - extent.y * ppm) * (.5f / ppm);
            position += rotation * new Vector3(slack.x, slack.y, 0f);
        }
        camera.transform.SetPositionAndRotation(position, rotation);
        PlaceRig(key, fill, rotation);

        var image = RenderTransparent(camera, w, h);
        File.WriteAllBytes(path, image.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(image);
        return new Vector2Int(w, h);
    }

    /// <summary>Camera position that fits all eight bounds corners in a frame of the given aspect.</summary>
    static Vector3 FitPerspective(Bounds b, Quaternion rotation, float fov, float aspect, float fill)
    {
        var t = Mathf.Tan(fov * .5f * Mathf.Deg2Rad) * fill;
        var tx = t * aspect;
        var inverse = Quaternion.Inverse(rotation);
        var target = b.center;
        var distance = 0f;
        for (var pass = 0; pass < 4; pass++)
        {
            distance = 0f;
            float minX = float.MaxValue, maxX = float.MinValue, minY = float.MaxValue, maxY = float.MinValue;
            for (var i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                var local = inverse * (corner - target);
                distance = Mathf.Max(distance, Mathf.Abs(local.x) / tx - local.z, Mathf.Abs(local.y) / t - local.z);
            }
            // Re-centre the projected box.
            for (var i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                var local = inverse * (corner - target);
                var z = local.z + distance;
                minX = Mathf.Min(minX, local.x / z); maxX = Mathf.Max(maxX, local.x / z);
                minY = Mathf.Min(minY, local.y / z); maxY = Mathf.Max(maxY, local.y / z);
            }
            target += rotation * new Vector3((minX + maxX) * .5f * distance, (minY + maxY) * .5f * distance, 0f);
        }
        return target - rotation * Vector3.forward * distance;
    }

    /// <summary>
    /// Render at up to 4x the size on a single-sampled
    /// transparent clear, box-filter down in linear premultiplied space and
    /// un-premultiply. If the pipeline does not keep alpha, render on black
    /// and on white and recover it (alpha = 1 - (white - black)).
    /// </summary>
    static Texture2D RenderTransparent(Camera camera, int w, int h)
    {
        // A multisampled target makes URP 17 request a sample count the target
        // does not have (BlitFinalToBackBuffer 4 vs 8) and the frame comes back
        // empty, so the target is single-sampled and the supersample is the AA.
        var supersample = Mathf.Clamp(MaxTarget / Mathf.Max(w, h), 1, 4);
        int sw = w * supersample, sh = h * supersample;
        var rt = RenderTexture.GetTemporary(new RenderTextureDescriptor(sw, sh, RenderTextureFormat.ARGB32, 24) { msaaSamples = 1, sRGB = true });
        camera.aspect = (float)w / h;
        camera.targetTexture = rt;
        camera.backgroundColor = new Color(0f, 0f, 0f, 0f);
        var black = Read(camera, rt);
        var bp = black.GetPixels();
        UnityEngine.Object.DestroyImmediate(black);
        var premult = new Color[bp.Length];   // linear rgb premultiplied, alpha
        var keepsAlpha = bp[0].a < .01f && bp[bp.Length - 1].a < .01f;
        if (keepsAlpha)
        {
            for (var i = 0; i < bp.Length; i++) { var l = bp[i].linear; l.a = bp[i].a; premult[i] = l; }
        }
        else
        {
            if (!warnedAlpha) { Debug.Log("[ThreeView] Camera target has opaque alpha; recovering it from black/white renders."); warnedAlpha = true; }
            camera.backgroundColor = new Color(1f, 1f, 1f, 0f);
            var white = Read(camera, rt);
            var wp = white.GetPixels();
            UnityEngine.Object.DestroyImmediate(white);
            camera.backgroundColor = new Color(0f, 0f, 0f, 0f);
            for (var i = 0; i < bp.Length; i++)
            {
                var bl = bp[i].linear;
                var wl = wp[i].linear;
                var alpha = Mathf.Clamp01(1f - ((wl.r - bl.r) + (wl.g - bl.g) + (wl.b - bl.b)) / 3f);
                premult[i] = new Color(bl.r, bl.g, bl.b, alpha);
            }
        }
        camera.targetTexture = null;
        RenderTexture.ReleaseTemporary(rt);

        var output = new Color[w * h];
        var n = 1f / (supersample * supersample);
        var covered = 0;
        for (var y = 0; y < h; y++)
        for (var x = 0; x < w; x++)
        {
            float r = 0f, g = 0f, b = 0f, a = 0f;
            for (var dy = 0; dy < supersample; dy++)
            for (var dx = 0; dx < supersample; dx++)
            {
                var c = premult[(y * supersample + dy) * sw + x * supersample + dx];
                r += c.r; g += c.g; b += c.b; a += c.a;
            }
            r *= n; g *= n; b *= n; a *= n;
            Color o;
            if (a < .002f) o = new Color(0f, 0f, 0f, 0f);
            else
            {
                o = new Color(Mathf.Clamp01(r / a), Mathf.Clamp01(g / a), Mathf.Clamp01(b / a), 1f).gamma;
                o.a = a;
                covered++;
            }
            output[y * w + x] = o;
        }
        if (covered == 0) Debug.LogWarning("[ThreeView] Empty render " + w + "x" + h + " from " + camera.transform.position);
        var image = new Texture2D(w, h, TextureFormat.RGBA32, false);
        image.SetPixels(output);
        image.Apply();
        return image;
    }

    static bool warnedAlpha;

    static Texture2D Read(Camera camera, RenderTexture rt)
    {
        // Twice: the first settles shadows and SSAO for the new pose.
        camera.Render();
        camera.Render();
        var previous = RenderTexture.active;
        RenderTexture.active = rt;
        var image = new Texture2D(rt.width, rt.height, TextureFormat.RGBA32, false);
        image.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        image.Apply();
        RenderTexture.active = previous;
        return image;
    }

    /// <summary>Show only LOD0: the sheet documents the authored model.</summary>
    static void ForceLod0(GameObject instance)
    {
        foreach (var group in instance.GetComponentsInChildren<LODGroup>())
        {
            var lods = group.GetLODs();
            var keep = new HashSet<Renderer>();
            if (lods.Length > 0) foreach (var r in lods[0].renderers) if (r != null) keep.Add(r);
            for (var i = 1; i < lods.Length; i++)
                foreach (var r in lods[i].renderers)
                    if (r != null && !keep.Contains(r)) r.enabled = false;
            group.enabled = false;
        }
        foreach (var r in instance.GetComponentsInChildren<MeshRenderer>())
            if (r.name.IndexOf("_LOD", StringComparison.OrdinalIgnoreCase) >= 0 && r.name.IndexOf("_LOD0", StringComparison.OrdinalIgnoreCase) < 0)
                r.enabled = false;
    }

    // ---------------------------------------------------------------- manifest

    static string Entry(string assetName, FrontRoomsKitLibrary.Info info, Bounds b, float sheet, Dictionary<View, Vector2Int> px)
    {
        var s = new StringBuilder();
        s.Append("  {\"name\": ").Append(Q(assetName));
        s.Append(", \"sheetPpm\": ").Append(F(sheet)).Append(", \"pngPpm\": ").Append(F(sheet * Oversample));
        s.Append(", \"size_m\": [").Append(F(b.size.x)).Append(", ").Append(F(b.size.y)).Append(", ").Append(F(b.size.z)).Append("]");
        s.Append(", \"boundsMin\": [").Append(F(b.min.x)).Append(", ").Append(F(b.min.y)).Append(", ").Append(F(b.min.z)).Append("]");
        s.Append(", \"boundsMax\": [").Append(F(b.max.x)).Append(", ").Append(F(b.max.y)).Append(", ").Append(F(b.max.z)).Append("]");
        s.Append(", \"triangles\": ").Append(info != null ? info.triangles : 0);
        s.Append(", \"trianglesLod1\": ").Append(info != null ? info.trianglesLod1 : 0);
        s.Append(", \"slots\": ").Append(Arr(info?.slots));
        s.Append(", \"tags\": ").Append(Arr(info?.tags));
        s.Append(", \"pile\": ").Append(info?.pile != null && !string.IsNullOrEmpty(info.pile.cls) ? Q(info.pile.cls) : "null");
        s.Append(", \"palette\": ").Append(info?.pile != null && !string.IsNullOrEmpty(info.pile.palette) ? Q(info.pile.palette) : "null");
        s.Append(", \"placement\": ").Append(info != null && !string.IsNullOrEmpty(info.placement) ? Q(info.placement) : "null");
        s.Append(", \"px\": {");
        var first = true;
        foreach (var kv in px)
        {
            s.Append(first ? "" : ", ").Append(Q(kv.Key.ToString().ToLowerInvariant())).Append(": [").Append(kv.Value.x).Append(", ").Append(kv.Value.y).Append("]");
            first = false;
        }
        s.Append("}}");
        return s.ToString();
    }

    static string F(float v) => Math.Round(v, 4).ToString(CultureInfo.InvariantCulture);
    static string Q(string v) => "\"" + (v ?? string.Empty).Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
    static string Arr(string[] a)
    {
        if (a == null) return "[]";
        var parts = new string[a.Length];
        for (var i = 0; i < a.Length; i++) parts[i] = Q(a[i]);
        return "[" + string.Join(", ", parts) + "]";
    }
}
