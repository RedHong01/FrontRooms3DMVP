using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

/// <summary>
/// Marks a runtime-created pane as a candidate for the desktop Metal RT
/// reflection pass. The pane remains rendered by URP; this component only
/// supplies the geometry/material identity used by the native reflection
/// renderer.
/// </summary>
public sealed class FrontRoomsMetalGlassTarget : MonoBehaviour
{
    [Min(0f)] public float reflectionStrength = 1f;
}

/// <summary>
/// Desktop-only hardware ray-traced reflection bridge for the hero glass.
/// The Metal plugin traces the camera ray to a glass first hit, reflects it
/// once through the nearby scene, and writes RGBA where the first hit is a
/// marked glass material. URP composites that texture over its normal glass.
/// If the plugin is unavailable, this controller stays inert and the existing
/// probe/planar paths continue to render.
/// </summary>
[DefaultExecutionOrder(9000)]
public sealed class FrontRoomsMetalGlassRTController : MonoBehaviour
{
    public static FrontRoomsMetalGlassRTController Instance { get; private set; }

    [SerializeField, Min(2f)] float registrationRadius = 18f;
    [SerializeField, Range(1, 512)] int maxInstances = 256;
    [SerializeField, Min(.1f)] float rescanSeconds = 1f;
    [SerializeField, Range(0f, 2f)] float reflectionStrength = 1f;

    readonly Dictionary<Mesh, int> meshIndices = new Dictionary<Mesh, int>();
    readonly Dictionary<Material, int> materialIndices = new Dictionary<Material, int>();
    readonly List<FrontRoomsMetalGlassRTNative.MaterialDesc> materials = new List<FrontRoomsMetalGlassRTNative.MaterialDesc>();
    readonly List<FrontRoomsMetalGlassRTNative.InstanceDesc> instances = new List<FrontRoomsMetalGlassRTNative.InstanceDesc>();
    readonly List<Renderer> registeredRenderers = new List<Renderer>();
    IntPtr eventData;
    RenderTexture result;
    RTHandle resultHandle;
    uint frameIndex;
    float nextScan;
    bool reset = true;
    bool nativeAvailable;
    bool ready;
    bool warned;

    public bool IsReady => ready && resultHandle != null;
    public RTHandle ResultHandle => resultHandle;
    public Material CompositeMaterial { get; internal set; }
    public float Strength => reflectionStrength;

    public static FrontRoomsMetalGlassRTController Ensure()
    {
        if (Instance != null) return Instance;
        var go = new GameObject("FrontRooms Metal Glass RT");
        DontDestroyOnLoad(go);
        return go.AddComponent<FrontRoomsMetalGlassRTController>();
    }

    void OnEnable()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(this);
            return;
        }
        Instance = this;
        eventData = Marshal.AllocHGlobal(FrontRoomsMetalGlassRTNative.EventDataSize);

        if (Application.platform != RuntimePlatform.OSXEditor &&
            Application.platform != RuntimePlatform.OSXPlayer)
            return;

        try
        {
            nativeAvailable = FrontRoomsMetalGlassRTNative.DeviceSupportsRaytracing() == 1;
            ready = nativeAvailable;
            Debug.Log($"[FrontRoomsMetalGlassRT] Native Metal ray-tracing capability: {nativeAvailable}");
        }
        catch (DllNotFoundException)
        {
            nativeAvailable = false;
            ready = false;
            if (!warned) Debug.LogWarning("[FrontRoomsMetalGlassRT] Native Metal plugin is missing; using the normal glass fallback.");
            warned = true;
        }
        catch (EntryPointNotFoundException)
        {
            nativeAvailable = false;
            ready = false;
            if (!warned) Debug.LogWarning("[FrontRoomsMetalGlassRT] Native Metal plugin is out of date; using the normal glass fallback.");
            warned = true;
        }
    }

    void OnDisable()
    {
        if (Instance == this) Instance = null;
        resultHandle?.Release();
        resultHandle = null;
        if (result != null) result.Release();
        result = null;
        if (eventData != IntPtr.Zero)
        {
            Marshal.FreeHGlobal(eventData);
            eventData = IntPtr.Zero;
        }
        try { FrontRoomsMetalGlassRTNative.Reset(); } catch { }
    }

    void Update()
    {
        if (!nativeAvailable || Time.unscaledTime < nextScan) return;
        nextScan = Time.unscaledTime + rescanSeconds;
        RebuildScene();
    }

    void RebuildScene()
    {
        var camera = Camera.main;
        var targets = FindObjectsByType<FrontRoomsMetalGlassTarget>(FindObjectsSortMode.None);
        if (targets.Length == 0)
        {
            ready = false;
            return;
        }

        var focus = camera != null ? camera.transform.position : targets[0].transform.position;
        FrontRoomsMetalGlassTarget nearest = null;
        var nearestSqr = float.PositiveInfinity;
        foreach (var target in targets)
        {
            if (!target.isActiveAndEnabled) continue;
            var d = (target.transform.position - focus).sqrMagnitude;
            if (d < nearestSqr) { nearestSqr = d; nearest = target; }
        }
        if (nearest == null) { ready = false; return; }

        var all = FindObjectsByType<MeshRenderer>(FindObjectsSortMode.InstanceID);
        var selected = new List<Renderer>(Mathf.Min(maxInstances, all.Length));
        foreach (var renderer in all)
        {
            if (!renderer.enabled || renderer.sharedMaterial == null) continue;
            var filter = renderer.GetComponent<MeshFilter>();
            if (filter == null || filter.sharedMesh == null) continue;
            var isGlass = renderer.GetComponent<FrontRoomsMetalGlassTarget>() != null;
            var within = (renderer.bounds.center - nearest.transform.position).sqrMagnitude <= registrationRadius * registrationRadius;
            if (!isGlass && !within) continue;
            if (selected.Count >= maxInstances) break;
            selected.Add(renderer);
        }
        if (selected.Count == 0) { ready = false; return; }

        try
        {
            FrontRoomsMetalGlassRTNative.Reset();
            meshIndices.Clear();
            materialIndices.Clear();
            materials.Clear();
            instances.Clear();
            registeredRenderers.Clear();

            foreach (var renderer in selected)
            {
                var filter = renderer.GetComponent<MeshFilter>();
                var mesh = filter.sharedMesh;
                if (!meshIndices.TryGetValue(mesh, out var meshIndex))
                {
                    var stream = mesh.GetVertexAttributeStream(VertexAttribute.Position);
                    if (mesh.GetVertexAttributeFormat(VertexAttribute.Position) != VertexAttributeFormat.Float32 ||
                        mesh.GetVertexAttributeDimension(VertexAttribute.Position) != 3 ||
                        mesh.GetTopology(0) != MeshTopology.Triangles)
                        continue;
                    var indexSize = mesh.indexFormat == IndexFormat.UInt16 ? 2u : 4u;
                    meshIndex = FrontRoomsMetalGlassRTNative.AddMesh(
                        mesh.GetNativeVertexBufferPtr(stream),
                        (uint)mesh.GetVertexBufferStride(stream),
                        (uint)mesh.GetVertexAttributeOffset(VertexAttribute.Position),
                        mesh.GetNativeIndexBufferPtr(), indexSize,
                        (uint)(mesh.GetIndexStart(0) * indexSize),
                        (uint)(mesh.GetIndexCount(0) / 3));
                    if (meshIndex < 0) continue;
                    meshIndices.Add(mesh, meshIndex);
                }

                var material = renderer.sharedMaterial;
                if (!materialIndices.TryGetValue(material, out var materialIndex))
                {
                    var isGlass = renderer.GetComponent<FrontRoomsMetalGlassTarget>() != null;
                    materialIndex = materials.Count;
                    materials.Add(FrontRoomsMetalGlassRTNative.MaterialDesc.From(material, isGlass));
                    materialIndices.Add(material, materialIndex);
                }

                var l2w = renderer.transform.localToWorldMatrix;
                instances.Add(new FrontRoomsMetalGlassRTNative.InstanceDesc
                {
                    meshIndex = meshIndex,
                    materialIndex = materialIndex,
                    objectToWorld0 = l2w.GetRow(0),
                    objectToWorld1 = l2w.GetRow(1),
                    objectToWorld2 = l2w.GetRow(2)
                });
                registeredRenderers.Add(renderer);
            }

            if (instances.Count == 0) { ready = false; return; }
            if (FrontRoomsMetalGlassRTNative.SetMaterials(materials.ToArray(), materials.Count) != 0)
                throw new InvalidOperationException(FrontRoomsMetalGlassRTNative.LastError());
            if (FrontRoomsMetalGlassRTNative.BuildInstances(instances.ToArray(), instances.Count) != 0)
                throw new InvalidOperationException(FrontRoomsMetalGlassRTNative.LastError());
            reset = true;
            ready = true;
        }
        catch (Exception ex) when (ex is DllNotFoundException || ex is EntryPointNotFoundException || ex is InvalidOperationException)
        {
            ready = false;
            if (!warned) Debug.LogWarning("[FrontRoomsMetalGlassRT] Scene registration failed: " + ex.Message);
            warned = true;
        }
    }

    internal void Record(CommandBuffer command, Camera camera)
    {
        if (!IsReady || camera == null || eventData == IntPtr.Zero) return;
        var width = Mathf.Max(1, camera.pixelWidth);
        var height = Mathf.Max(1, camera.pixelHeight);
        EnsureResult(width, height);
        if (result == null) return;

        var t = camera.transform;
        FrontRoomsMetalGlassRTNative.WriteEventData(eventData,
            t.position, t.right, t.up, t.forward,
            camera.fieldOfView * Mathf.Deg2Rad, (float)width / height,
            (uint)width, (uint)height,
            reflectionStrength, frameIndex++, reset);
        FrontRoomsMetalGlassRTNative.SetOutput(result.GetNativeTexturePtr());
        reset = false;
        command.IssuePluginEventAndData(FrontRoomsMetalGlassRTNative.GetRenderEventFunc(), FrontRoomsMetalGlassRTNative.RenderEventId, eventData);
    }

    void EnsureResult(int width, int height)
    {
        if (result != null && result.width == width && result.height == height) return;
        resultHandle?.Release();
        if (result != null) result.Release();
        result = new RenderTexture(width, height, 0, RenderTextureFormat.ARGBFloat)
        {
            enableRandomWrite = true,
            filterMode = FilterMode.Bilinear,
            name = "FrontRooms Metal Glass RT"
        };
        result.Create();
        resultHandle = RTHandles.Alloc(result);
        reset = true;
    }
}

sealed class FrontRoomsMetalGlassRTPass : ScriptableRenderPass
{
    sealed class PassData
    {
        public Camera Camera;
        public TextureHandle Color;
        public FrontRoomsMetalGlassRTController Controller;
        public Material Material;
    }

    readonly Material material;
    public FrontRoomsMetalGlassRTController Controller { get; set; }

    public FrontRoomsMetalGlassRTPass(Material material) => this.material = material;

    public override void RecordRenderGraph(RenderGraph renderGraph, ContextContainer frameData)
    {
        if (Controller == null || !Controller.IsReady || material == null) return;
        var resourceData = frameData.Get<UniversalResourceData>();
        var cameraData = frameData.Get<UniversalCameraData>();
        using var builder = renderGraph.AddUnsafePass<PassData>("FrontRooms Metal Glass RT", out var data);
        data.Camera = cameraData.camera;
        data.Color = resourceData.activeColorTexture;
        data.Controller = Controller;
        data.Material = material;
        builder.UseTexture(data.Color, AccessFlags.Write);
        builder.AllowPassCulling(false);
        builder.SetRenderFunc((PassData d, UnsafeGraphContext ctx) =>
        {
            var cmd = CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd);
            d.Controller.Record(cmd, d.Camera);
            if (d.Controller.ResultHandle == null) return;
            cmd.SetGlobalTexture(FrontRoomsMetalGlassRTNative.ResultTextureId, d.Controller.ResultHandle);
            cmd.SetGlobalFloat(FrontRoomsMetalGlassRTNative.ResultStrengthId, d.Controller.Strength);
            cmd.SetRenderTarget(d.Color);
            CoreUtils.DrawFullScreen(cmd, d.Material);
        });
    }
}

internal static class FrontRoomsMetalGlassRTNative
{
    const string Plugin = "FrontRoomsMetalGlassRT";
    public static readonly int ResultTextureId = Shader.PropertyToID("_FrontRoomsMetalGlassRT");
    public static readonly int ResultStrengthId = Shader.PropertyToID("_FrontRoomsMetalGlassRTStrength");

    [StructLayout(LayoutKind.Sequential)]
    public struct MaterialDesc
    {
        public Vector4 baseColor;
        public float metallic;
        public float smoothness;
        public uint flags;
        public uint pad;

        public static MaterialDesc From(Material material, bool glass)
        {
            var c = material != null && material.HasProperty("_BaseColor") ? material.GetColor("_BaseColor") : Color.white;
            return new MaterialDesc
            {
                baseColor = c.linear,
                metallic = material != null && material.HasProperty("_Metallic") ? material.GetFloat("_Metallic") : 0f,
                smoothness = material != null && material.HasProperty("_Smoothness") ? material.GetFloat("_Smoothness") : .5f,
                flags = glass ? 1u : 0u
            };
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct InstanceDesc
    {
        public int meshIndex;
        public int materialIndex;
        public Vector4 objectToWorld0;
        public Vector4 objectToWorld1;
        public Vector4 objectToWorld2;
    }

    public const int EventDataSize = 160;

    [DllImport(Plugin)] static extern int FRGlassRT_DeviceSupportsRaytracing();
    [DllImport(Plugin)] public static extern void FRGlassRT_Reset();
    [DllImport(Plugin)] static extern int FRGlassRT_AddMesh(IntPtr vertexBuffer, uint vertexStride, uint positionOffset, IntPtr indexBuffer, uint indexSize, uint indexByteOffset, uint triangleCount);
    [DllImport(Plugin)] static extern int FRGlassRT_SetMaterials([In] MaterialDesc[] materials, int count);
    [DllImport(Plugin)] static extern int FRGlassRT_BuildInstances([In] InstanceDesc[] instances, int count);
    [DllImport(Plugin)] static extern IntPtr FRGlassRT_LastError();
    [DllImport(Plugin)] static extern void FRGlassRT_SetOutput(IntPtr texture);
    [DllImport(Plugin)] static extern IntPtr FRGlassRT_GetRenderEventFunc();
    [DllImport(Plugin)] static extern int FRGlassRT_RenderEventId();

    public static int DeviceSupportsRaytracing() => FRGlassRT_DeviceSupportsRaytracing();
    public static void Reset() => FRGlassRT_Reset();
    public static int AddMesh(IntPtr vb, uint stride, uint posOffset, IntPtr ib, uint indexSize, uint indexByteOffset, uint triangleCount) => FRGlassRT_AddMesh(vb, stride, posOffset, ib, indexSize, indexByteOffset, triangleCount);
    public static int SetMaterials(MaterialDesc[] value, int count) => FRGlassRT_SetMaterials(value, count);
    public static int BuildInstances(InstanceDesc[] value, int count) => FRGlassRT_BuildInstances(value, count);
    public static string LastError()
    {
        var ptr = FRGlassRT_LastError();
        return ptr == IntPtr.Zero ? "unknown native error" : Marshal.PtrToStringAnsi(ptr);
    }
    public static void SetOutput(IntPtr texture) => FRGlassRT_SetOutput(texture);
    public static IntPtr GetRenderEventFunc() => FRGlassRT_GetRenderEventFunc();
    public static int RenderEventId => FRGlassRT_RenderEventId();

    public static void WriteEventData(IntPtr ptr, Vector3 origin, Vector3 right, Vector3 up, Vector3 forward, float fovRadians, float aspect, uint width, uint height, float strength, uint frame, bool reset)
    {
        Marshal.WriteInt32(ptr, 0, BitConverter.SingleToInt32Bits(origin.x));
        Marshal.WriteInt32(ptr, 4, BitConverter.SingleToInt32Bits(origin.y));
        Marshal.WriteInt32(ptr, 8, BitConverter.SingleToInt32Bits(origin.z));
        Marshal.WriteInt32(ptr, 12, BitConverter.SingleToInt32Bits(fovRadians));
        WriteVec(ptr, 16, right, aspect);
        WriteVec(ptr, 32, up, 0f);
        WriteVec(ptr, 48, forward, 0f);
        Marshal.WriteInt32(ptr, 64, BitConverter.SingleToInt32Bits(fovRadians));
        Marshal.WriteInt32(ptr, 68, BitConverter.SingleToInt32Bits(aspect));
        Marshal.WriteInt32(ptr, 72, (int)width);
        Marshal.WriteInt32(ptr, 76, (int)height);
        Marshal.WriteInt32(ptr, 80, BitConverter.SingleToInt32Bits(strength));
        Marshal.WriteInt32(ptr, 84, (int)frame);
        Marshal.WriteInt32(ptr, 88, reset ? 1 : 0);
    }

    static void WriteVec(IntPtr ptr, int offset, Vector3 v, float w)
    {
        Marshal.WriteInt32(ptr, offset + 0, BitConverter.SingleToInt32Bits(v.x));
        Marshal.WriteInt32(ptr, offset + 4, BitConverter.SingleToInt32Bits(v.y));
        Marshal.WriteInt32(ptr, offset + 8, BitConverter.SingleToInt32Bits(v.z));
        Marshal.WriteInt32(ptr, offset + 12, BitConverter.SingleToInt32Bits(w));
    }
}
