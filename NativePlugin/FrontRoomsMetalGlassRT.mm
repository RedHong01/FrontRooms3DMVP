// FrontRoomsMetalGlassRT.mm
//
// Small, project-owned Metal ray-tracing bridge for the FrontRooms glass
// reflection prototype. This file deliberately does not vendor or copy a
// third-party path tracer. It owns only the minimum BLAS/TLAS and one-bounce
// reflection path needed by the project's glass experiment.
//
// Unity 6000.3.10f1 interop contract is documented above each exported
// function. The managed side may keep this plugin completely disabled: if the
// library is absent or Metal reports no ray-tracing support, the existing URP
// planar/probe fallback remains authoritative.

#import <Metal/Metal.h>
#import <Foundation/Foundation.h>
#import <simd/simd.h>

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>

#include "IUnityInterface.h"
#include "IUnityGraphics.h"
#include "IUnityGraphicsMetal.h"

namespace
{

constexpr uint32_t kGlassMaterial = 1u << 0;
constexpr uint32_t kMaxInstances = 256;
constexpr uint32_t kMaxMaterials = 256;

struct MeshRecord
{
    id<MTLBuffer> vertexBuffer;
    uint32_t vertexStride = 0;
    uint32_t positionOffset = 0;
    id<MTLBuffer> indexBuffer;
    uint32_t indexSize = 0;
    uint32_t indexByteOffset = 0;
    uint32_t triangleCount = 0;
    id<MTLAccelerationStructure> blas;
};

// This is the managed interop contract. Keep field order/types stable.
// MaterialDesc is intentionally simple: baseColor is linear RGBA and flags
// bit 0 marks the first-hit geometry as glass.
struct MaterialDesc
{
    float baseColor[4];
    float metallic;
    float smoothness;
    uint32_t flags;
    uint32_t pad;
};

// Rows of a 3x4 object-to-world transform. The matrix is also used to
// transform the geometric triangle normal in this small prototype.
struct InstanceDesc
{
    int32_t meshIndex;
    int32_t materialIndex;
    float objectToWorld[3][4];
};

struct EventData
{
    // xyz vectors; w values are ignored and exist for 16-byte managed packing.
    float cameraOrigin[4];
    float cameraRight[4];
    float cameraUp[4];
    float cameraForward[4];
    float tanFovY;
    float aspect;
    uint32_t width;
    uint32_t height;
    float glassStrength;
    uint32_t frameIndex;
    uint32_t reset;
    uint32_t pad0;
};

// Shader-side instance records. The pointer fields are Metal 3 GPU virtual
// addresses; MSL turns them back into device pointers for geometric normal
// fetches after an intersection result identifies the primitive.
struct GpuInstanceInfo
{
    uint64_t vertices;
    uint64_t indices;
    uint32_t vertexStride;
    uint32_t positionOffset;
    uint32_t indexSize;
    uint32_t indexByteOffset;
    uint32_t triangleCount;
    uint32_t materialIndex;
    float objectToWorld[3][4];
};

struct GpuMaterial
{
    float baseColor[4];
    float metallic;
    float smoothness;
    uint32_t flags;
    uint32_t pad;
};

IUnityInterfaces* s_UnityInterfaces = nullptr;
IUnityGraphics* s_Graphics = nullptr;
IUnityGraphicsMetalV2* s_Metal = nullptr;
id<MTLDevice> s_Device;
id<MTLCommandQueue> s_Queue;
id<MTLComputePipelineState> s_TracePipeline;
id<MTLTexture> s_OutputTexture;
id<MTLAccelerationStructure> s_Tlas;
id<MTLBuffer> s_TlasScratch;
id<MTLBuffer> s_InstanceDescriptorBuffer;
id<MTLBuffer> s_InstanceInfoBuffer;
id<MTLBuffer> s_MaterialBuffer;

std::vector<MeshRecord> s_Meshes;
std::vector<MaterialDesc> s_Materials;
std::vector<InstanceDesc> s_Instances;
std::mutex s_StateMutex;
std::string s_LastError;

// MSL is compiled at runtime because this source uses Metal's
// instance_acceleration_structure and intersector types, which cannot be
// represented by Unity's regular HLSL/compute path.
static const char* kTraceSource = R"MSL(
#include <metal_stdlib>
using namespace metal;

struct EventData
{
    float4 cameraOrigin;
    float4 cameraRight;
    float4 cameraUp;
    float4 cameraForward;
    float tanFovY;
    float aspect;
    uint width;
    uint height;
    float glassStrength;
    uint frameIndex;
    uint reset;
    uint pad0;
};

struct InstanceInfo
{
    device const uchar* vertices;
    device const uchar* indices;
    uint vertexStride;
    uint positionOffset;
    uint indexSize;
    uint indexByteOffset;
    uint triangleCount;
    uint materialIndex;
    float4 objectToWorld0;
    float4 objectToWorld1;
    float4 objectToWorld2;
};

struct MaterialInfo
{
    float4 baseColor;
    float metallic;
    float smoothness;
    uint flags;
    uint pad;
};

static uint3 LoadTriangle(constant InstanceInfo& info, uint primitive)
{
    primitive = min(primitive, max(info.triangleCount, 1u) - 1u);
    device const uchar* address = info.indices + info.indexByteOffset;
    if (info.indexSize == 2u)
    {
        device const ushort* p = (device const ushort*)address;
        return uint3(p[primitive * 3u], p[primitive * 3u + 1u],
                     p[primitive * 3u + 2u]);
    }
    device const uint* p = (device const uint*)address;
    return uint3(p[primitive * 3u], p[primitive * 3u + 1u],
                 p[primitive * 3u + 2u]);
}

static float3 LoadPosition(constant InstanceInfo& info, uint index)
{
    device const uchar* address = info.vertices +
      info.vertexStride * index + info.positionOffset;
    return *(device const packed_float3*)address;
}

static float3 ToWorld(constant InstanceInfo& info, float3 p)
{
    float4 hp = float4(p, 1.0f);
    return float3(dot(info.objectToWorld0, hp),
                  dot(info.objectToWorld1, hp),
                  dot(info.objectToWorld2, hp));
}

static float3 ToWorldDirection(constant InstanceInfo& info, float3 p)
{
    float4 hp = float4(p, 0.0f);
    return normalize(float3(dot(info.objectToWorld0, hp),
                            dot(info.objectToWorld1, hp),
                            dot(info.objectToWorld2, hp)));
}

static float3 GeometricNormal(constant InstanceInfo& info, uint primitive)
{
    uint3 tri = LoadTriangle(info, primitive);
    float3 a = ToWorld(info, LoadPosition(info, tri.x));
    float3 b = ToWorld(info, LoadPosition(info, tri.y));
    float3 c = ToWorld(info, LoadPosition(info, tri.z));
    return normalize(cross(b - a, c - a));
}

static float3 Environment(float3 direction)
{
    float t = saturate(direction.y * 0.5f + 0.5f);
    return mix(float3(0.015f, 0.02f, 0.035f),
               float3(0.16f, 0.24f, 0.38f), t);
}

static float3 ShadeHit(intersection_result<triangle_data, instancing> hit,
                       ray r,
                       constant InstanceInfo* instances,
                       constant MaterialInfo* materials)
{
    constant InstanceInfo& info = instances[hit.instance_id];
    constant MaterialInfo& material = materials[info.materialIndex];
    float3 n = GeometricNormal(info, hit.primitive_id);
    if (dot(n, -r.direction) < 0.0f) n = -n;
    float3 sun = normalize(float3(0.35f, 0.82f, 0.28f));
    float ndl = saturate(dot(n, sun));
    float3 base = material.baseColor.xyz;
    return base * (0.12f + 0.88f * ndl) + base * 0.035f;
}

kernel void FrontRoomsGlassTrace(
    texture2d<float, access::write> output [[texture(0)]],
    instance_acceleration_structure scene [[buffer(0)]],
    constant EventData& frame [[buffer(1)]],
    constant InstanceInfo* instances [[buffer(2)]],
    constant MaterialInfo* materials [[buffer(3)]],
    uint2 id [[thread_position_in_grid]])
{
    if (id.x >= frame.width || id.y >= frame.height) return;

    // Default is transparent/empty. This keeps non-glass pixels out of the
    // composite pass and lets the existing URP glass fallback show through.
    output.write(float4(0.0f), id);
    if (frame.reset != 0u && frame.frameIndex > 0u) return;

    float2 uv = (float2(id) + 0.5f) /
                float2(float(frame.width), float(frame.height));
    float2 ndc = uv * 2.0f - 1.0f;
    float3 direction = normalize(frame.cameraForward.xyz +
      frame.cameraRight.xyz * (ndc.x * frame.tanFovY * frame.aspect) +
      frame.cameraUp.xyz * (ndc.y * frame.tanFovY));

    ray primary;
    primary.origin = frame.cameraOrigin.xyz;
    primary.direction = direction;
    primary.min_distance = 0.001f;
    primary.max_distance = 10000.0f;

    auto intersector = intersector<triangle_data, instancing>();
    auto first = intersector.intersect(primary, scene);
    if (first.type != intersection_type::triangle) return;

    constant InstanceInfo& firstInfo = instances[first.instance_id];
    constant MaterialInfo& firstMaterial = materials[firstInfo.materialIndex];
    if ((firstMaterial.flags & 1u) == 0u) return;

    float3 hitPosition = primary.origin + primary.direction * first.distance;
    float3 normal = GeometricNormal(firstInfo, first.primitive_id);
    if (dot(normal, -primary.direction) < 0.0f) normal = -normal;

    ray reflected;
    reflected.origin = hitPosition + normal * 0.002f;
    reflected.direction = normalize(reflect(primary.direction, normal));
    reflected.min_distance = 0.001f;
    reflected.max_distance = 10000.0f;

    auto second = intersector.intersect(reflected, scene);
    float3 color;
    if (second.type == intersection_type::triangle)
        color = ShadeHit(second, reflected, instances, materials);
    else
        color = Environment(reflected.direction);

    float edge = 1.0f - saturate(dot(-primary.direction, normal));
    float fresnel = mix(0.04f, 1.0f, edge * edge * edge * edge * edge);
    float strength = saturate(frame.glassStrength);
    color *= mix(0.15f, 1.0f, fresnel) * strength;
    output.write(float4(color, 1.0f), id);
}
)MSL";

void SetError(const char* message)
{
    s_LastError = message ? message : "unknown MetalGlassRT error";
}

void SetError(NSString* message)
{
    SetError(message ? message.UTF8String : "unknown MetalGlassRT error");
}

bool EnsureDevice()
{
    if (s_Device && s_Queue) return true;
    if (!s_Metal)
    {
        SetError("Unity Metal interface is unavailable.");
        return false;
    }

    s_Device = s_Metal->MetalDevice();
    if (!s_Device)
    {
        SetError("Unity did not expose an MTLDevice.");
        return false;
    }
    if (!s_Device.supportsRaytracing)
    {
        SetError("This Metal device has no hardware ray-tracing support.");
        return false;
    }

    s_Queue = s_Metal->CommandQueue();
    if (!s_Queue)
    {
        SetError("Unity did not expose a Metal command queue.");
        return false;
    }

    NSError* error = nil;
    NSString* source = [NSString stringWithUTF8String:kTraceSource];
    id<MTLLibrary> library = [s_Device newLibraryWithSource:source
                                                    options:nil
                                                      error:&error];
    if (!library)
    {
        SetError(error.localizedDescription);
        return false;
    }
    id<MTLFunction> function = [library newFunctionWithName:@"FrontRoomsGlassTrace"];
    if (!function)
    {
        SetError("Metal ray-tracing function was not found.");
        return false;
    }
    s_TracePipeline = [s_Device newComputePipelineStateWithFunction:function
                                                                 error:&error];
    if (!s_TracePipeline)
    {
        SetError(error.localizedDescription);
        return false;
    }
    return true;
}

id<MTLAccelerationStructure> BuildBLAS(const MeshRecord& mesh)
{
    if (!EnsureDevice()) return nil;

    MTLAccelerationStructureTriangleGeometryDescriptor* geometry =
      [MTLAccelerationStructureTriangleGeometryDescriptor descriptor];
    geometry.vertexBuffer = mesh.vertexBuffer;
    geometry.vertexBufferOffset = mesh.positionOffset;
    geometry.vertexStride = mesh.vertexStride;
    geometry.indexBuffer = mesh.indexBuffer;
    geometry.indexBufferOffset = mesh.indexByteOffset;
    geometry.indexType = mesh.indexSize == 2 ? MTLIndexTypeUInt16 : MTLIndexTypeUInt32;
    geometry.triangleCount = mesh.triangleCount;

    MTLPrimitiveAccelerationStructureDescriptor* descriptor =
      [MTLPrimitiveAccelerationStructureDescriptor descriptor];
    descriptor.geometryDescriptors = @[geometry];

    MTLAccelerationStructureSizes sizes =
      [s_Device accelerationStructureSizesWithDescriptor:descriptor];
    id<MTLAccelerationStructure> blas =
      [s_Device newAccelerationStructureWithSize:sizes.accelerationStructureSize];
    id<MTLBuffer> scratch =
      [s_Device newBufferWithLength:sizes.buildScratchBufferSize
                            options:MTLResourceStorageModePrivate];
    if (!blas || (sizes.buildScratchBufferSize && !scratch))
    {
        SetError("Failed to allocate Metal BLAS buffers.");
        return nil;
    }

    id<MTLCommandBuffer> command = [s_Queue commandBuffer];
    id<MTLAccelerationStructureCommandEncoder> encoder =
      [command accelerationStructureCommandEncoder];
    [encoder buildAccelerationStructure:blas descriptor:descriptor
                          scratchBuffer:scratch scratchBufferOffset:0];
    [encoder endEncoding];
    [command commit];
    [command waitUntilCompleted];
    if (command.status != MTLCommandBufferStatusCompleted)
    {
        SetError(command.error.localizedDescription);
        return nil;
    }
    return blas;
}

bool BuildTLAS(const std::vector<InstanceDesc>& instances)
{
    if (!EnsureDevice()) return false;
    if (instances.empty())
    {
        SetError("No instances were registered for the Metal glass scene.");
        return false;
    }
    if (s_Materials.empty())
    {
        SetError("Materials must be uploaded before building the Metal glass TLAS.");
        return false;
    }

    NSMutableArray<id<MTLAccelerationStructure>>* blasArray =
      [NSMutableArray arrayWithCapacity:instances.size()];
    for (const InstanceDesc& source : instances)
    {
        if (source.meshIndex < 0 || source.meshIndex >= (int32_t)s_Meshes.size())
        {
            SetError("An instance references an invalid mesh index.");
            return false;
        }
        [blasArray addObject:s_Meshes[source.meshIndex].blas];
    }

    MTLInstanceAccelerationStructureDescriptor* descriptor =
      [MTLInstanceAccelerationStructureDescriptor descriptor];
    descriptor.instancedAccelerationStructures = blasArray;
    descriptor.instanceCount = (NSUInteger)instances.size();

    MTLAccelerationStructureSizes sizes =
      [s_Device accelerationStructureSizesWithDescriptor:descriptor];
    id<MTLAccelerationStructure> tlas =
      [s_Device newAccelerationStructureWithSize:sizes.accelerationStructureSize];
    id<MTLBuffer> scratch =
      [s_Device newBufferWithLength:sizes.buildScratchBufferSize
                            options:MTLResourceStorageModePrivate];
    id<MTLBuffer> descriptors =
      [s_Device newBufferWithLength:sizeof(MTLAccelerationStructureInstanceDescriptor) * instances.size()
                            options:MTLResourceStorageModeShared];
    if (!tlas || !descriptors || (sizes.buildScratchBufferSize && !scratch))
    {
        SetError("Failed to allocate Metal TLAS buffers.");
        return false;
    }

    auto* destination = (MTLAccelerationStructureInstanceDescriptor*)descriptors.contents;
    std::memset(destination, 0,
                sizeof(MTLAccelerationStructureInstanceDescriptor) * instances.size());
    for (NSUInteger i = 0; i < instances.size(); i++)
    {
        const InstanceDesc& source = instances[i];
        MTLAccelerationStructureInstanceDescriptor& destinationEntry = destination[i];
        for (int column = 0; column < 4; column++)
            destinationEntry.transformationMatrix.columns[column] =
              MTLPackedFloat3Make(source.objectToWorld[0][column],
                                  source.objectToWorld[1][column],
                                  source.objectToWorld[2][column]);
        destinationEntry.options = MTLAccelerationStructureInstanceOptionOpaque;
        destinationEntry.mask = 0xff;
        destinationEntry.accelerationStructureIndex = (NSUInteger)source.meshIndex;
    }

    descriptor.instanceDescriptorBuffer = descriptors;
    descriptor.instanceDescriptorStride = sizeof(MTLAccelerationStructureInstanceDescriptor);
    id<MTLCommandBuffer> command = [s_Queue commandBuffer];
    id<MTLAccelerationStructureCommandEncoder> encoder =
      [command accelerationStructureCommandEncoder];
    [encoder buildAccelerationStructure:tlas descriptor:descriptor
                          scratchBuffer:scratch scratchBufferOffset:0];
    [encoder endEncoding];
    [command commit];
    [command waitUntilCompleted];
    if (command.status != MTLCommandBufferStatusCompleted)
    {
        SetError(command.error.localizedDescription);
        return false;
    }

    std::vector<GpuInstanceInfo> gpuInstances;
    gpuInstances.reserve(instances.size());
    for (const InstanceDesc& source : instances)
    {
        const MeshRecord& mesh = s_Meshes[source.meshIndex];
        GpuInstanceInfo info{};
        info.vertices = mesh.vertexBuffer.gpuAddress;
        info.indices = mesh.indexBuffer.gpuAddress;
        info.vertexStride = mesh.vertexStride;
        info.positionOffset = mesh.positionOffset;
        info.indexSize = mesh.indexSize;
        info.indexByteOffset = mesh.indexByteOffset;
        info.triangleCount = mesh.triangleCount;
        info.materialIndex = std::clamp(source.materialIndex, 0, (int32_t)s_Materials.size() - 1);
        std::memcpy(info.objectToWorld, source.objectToWorld, sizeof(info.objectToWorld));
        gpuInstances.push_back(info);
    }

    s_InstanceDescriptorBuffer = descriptors;
    s_TlasScratch = scratch;
    s_InstanceInfoBuffer = [s_Device newBufferWithBytes:gpuInstances.data()
                                                   length:sizeof(GpuInstanceInfo) * gpuInstances.size()
                                                  options:MTLResourceStorageModeShared];
    if (!s_InstanceInfoBuffer)
    {
        SetError("Failed to allocate the instance info buffer.");
        return false;
    }
    s_Tlas = tlas;
    return true;
}

bool UploadMaterials()
{
    if (!EnsureDevice()) return false;
    if (s_Materials.empty())
    {
        SetError("No materials were registered for the Metal glass scene.");
        return false;
    }
    std::vector<GpuMaterial> gpu;
    gpu.reserve(s_Materials.size());
    for (const MaterialDesc& source : s_Materials)
    {
        GpuMaterial material{};
        std::memcpy(material.baseColor, source.baseColor, sizeof(material.baseColor));
        material.metallic = source.metallic;
        material.smoothness = source.smoothness;
        material.flags = source.flags;
        gpu.push_back(material);
    }
    s_MaterialBuffer = [s_Device newBufferWithBytes:gpu.data()
                                              length:sizeof(GpuMaterial) * gpu.size()
                                             options:MTLResourceStorageModeShared];
    if (!s_MaterialBuffer)
    {
        SetError("Failed to allocate the material buffer.");
        return false;
    }
    return true;
}

void OnGraphicsDeviceEvent(UnityGfxDeviceEventType eventType)
{
    if (eventType == kUnityGfxDeviceEventInitialize)
    {
        if (!s_Metal || s_Graphics->GetRenderer() != kUnityGfxRendererMetal) return;
        s_Device = s_Metal->MetalDevice();
        s_Queue = s_Metal->CommandQueue();
        if (s_Device && s_Device.supportsRaytracing) EnsureDevice();
    }
    else if (eventType == kUnityGfxDeviceEventShutdown)
    {
        std::lock_guard<std::mutex> lock(s_StateMutex);
        s_TracePipeline = nil;
        s_Tlas = nil;
        s_InstanceInfoBuffer = nil;
        s_InstanceDescriptorBuffer = nil;
        s_TlasScratch = nil;
        s_MaterialBuffer = nil;
        s_OutputTexture = nil;
        s_Queue = nil;
        s_Device = nil;
    }
}

void UNITY_INTERFACE_API RenderEvent(int eventId, void* data)
{
    if (eventId != 1 || !data) return;
    if (!EnsureDevice()) return;

    EventData frame = *(const EventData*)data;
    id<MTLTexture> output = s_OutputTexture;
    if (!output || !s_Tlas || !s_InstanceInfoBuffer || !s_MaterialBuffer)
    {
        SetError("The output, TLAS, or scene buffers are not ready.");
        return;
    }
    if (frame.width == 0 || frame.height == 0) return;

    id<MTLCommandBuffer> command = [s_Queue commandBuffer];
    id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
    [encoder setComputePipelineState:s_TracePipeline];
    [encoder setTexture:output atIndex:0];
    [encoder setAccelerationStructure:s_Tlas atBufferIndex:0];
    [encoder setBytes:&frame length:sizeof(EventData) atIndex:1];
    [encoder setBuffer:s_InstanceInfoBuffer offset:0 atIndex:2];
    [encoder setBuffer:s_MaterialBuffer offset:0 atIndex:3];

    NSUInteger width = std::min<NSUInteger>(frame.width, output.width);
    NSUInteger height = std::min<NSUInteger>(frame.height, output.height);
    MTLSize grid = MTLSizeMake(width, height, 1);
    NSUInteger tw = std::max<NSUInteger>(1, s_TracePipeline.threadExecutionWidth);
    NSUInteger th = std::max<NSUInteger>(1, s_TracePipeline.maxTotalThreadsPerThreadgroup / tw);
    MTLSize threads = MTLSizeMake(std::min(tw, width), std::min(th, height), 1);
    [encoder dispatchThreads:grid threadsPerThreadgroup:threads];
    [encoder endEncoding];
    [command commit];
}

} // namespace

extern "C"
{

UNITY_INTERFACE_EXPORT UNITY_INTERFACE_API
void UnityPluginLoad(IUnityInterfaces* interfaces)
{
    s_UnityInterfaces = interfaces;
    s_Graphics = interfaces ? interfaces->Get<IUnityGraphics>() : nullptr;
    s_Metal = interfaces ? interfaces->Get<IUnityGraphicsMetalV2>() : nullptr;
    if (s_Graphics)
    {
        s_Graphics->RegisterDeviceEventCallback(OnGraphicsDeviceEvent);
        OnGraphicsDeviceEvent(kUnityGfxDeviceEventInitialize);
    }
}

UNITY_INTERFACE_EXPORT UNITY_INTERFACE_API
void UnityPluginUnload()
{
    if (s_Graphics) s_Graphics->UnregisterDeviceEventCallback(OnGraphicsDeviceEvent);
    s_Metal = nullptr;
    s_Graphics = nullptr;
    s_UnityInterfaces = nullptr;
}

// Returns 1 only when the active Unity Metal device exposes the M3-class
// hardware ray-tracing intersector. Unity's SystemInfo.supportsRayTracing can
// still be false on Metal; this is an independent native capability probe.
UNITY_INTERFACE_EXPORT int UNITY_INTERFACE_API
FRGlassRT_DeviceSupportsRaytracing()
{
    if (!s_Metal) return 0;
    id<MTLDevice> device = s_Metal->MetalDevice();
    return device && device.supportsRaytracing ? 1 : 0;
}

UNITY_INTERFACE_EXPORT const char* UNITY_INTERFACE_API
FRGlassRT_LastError()
{
    return s_LastError.c_str();
}

// Clears all meshes, instances, materials, and acceleration structures.
UNITY_INTERFACE_EXPORT void UNITY_INTERFACE_API FRGlassRT_Reset()
{
    std::lock_guard<std::mutex> lock(s_StateMutex);
    s_Meshes.clear();
    s_Instances.clear();
    s_Materials.clear();
    s_Tlas = nil;
    s_InstanceDescriptorBuffer = nil;
    s_InstanceInfoBuffer = nil;
    s_TlasScratch = nil;
    s_MaterialBuffer = nil;
    s_OutputTexture = nil;
    s_LastError.clear();
}

// Builds one BLAS directly from Unity's Metal vertex/index buffers.
// `indexSize` is bytes per index (2 or 4), and indexByteOffset addresses the
// first index of submesh 0. Return value is a stable mesh index or -1.
UNITY_INTERFACE_EXPORT int UNITY_INTERFACE_API
FRGlassRT_AddMesh(void* vertexBuffer, uint32_t vertexStride,
                  uint32_t positionOffset, void* indexBuffer,
                  uint32_t indexSize, uint32_t indexByteOffset,
                  uint32_t triangleCount)
{
    if (!vertexBuffer || !indexBuffer || vertexStride == 0 ||
        (indexSize != 2 && indexSize != 4) || triangleCount == 0)
    {
        SetError("Invalid mesh buffer arguments.");
        return -1;
    }
    std::lock_guard<std::mutex> lock(s_StateMutex);
    if (s_Meshes.size() >= kMaxInstances)
    {
        SetError("Metal glass RT mesh limit reached.");
        return -1;
    }
    MeshRecord mesh;
    mesh.vertexBuffer = (__bridge id<MTLBuffer>)vertexBuffer;
    mesh.vertexStride = vertexStride;
    mesh.positionOffset = positionOffset;
    mesh.indexBuffer = (__bridge id<MTLBuffer>)indexBuffer;
    mesh.indexSize = indexSize;
    mesh.indexByteOffset = indexByteOffset;
    mesh.triangleCount = triangleCount;
    mesh.blas = BuildBLAS(mesh);
    if (!mesh.blas) return -1;
    s_Meshes.push_back(mesh);
    return (int)s_Meshes.size() - 1;
}

// Copies simple linear material records. flags bit 0 means glass.
UNITY_INTERFACE_EXPORT int UNITY_INTERFACE_API
FRGlassRT_SetMaterials(const MaterialDesc* materials, int count)
{
    if (!materials || count <= 0 || count > (int)kMaxMaterials)
    {
        SetError("Invalid material table.");
        return -1;
    }
    std::lock_guard<std::mutex> lock(s_StateMutex);
    s_Materials.assign(materials, materials + count);
    return UploadMaterials() ? 0 : -1;
}

// Copies instance transforms and rebuilds the TLAS immediately. The call is
// expected from the render thread before the event is issued.
UNITY_INTERFACE_EXPORT int UNITY_INTERFACE_API
FRGlassRT_BuildInstances(const InstanceDesc* instances, int count)
{
    if (!instances || count <= 0 || count > (int)kMaxInstances)
    {
        SetError("Invalid instance table.");
        return -1;
    }
    std::lock_guard<std::mutex> lock(s_StateMutex);
    s_Instances.assign(instances, instances + count);
    return BuildTLAS(s_Instances) ? 0 : -1;
}

// Stores an MTLTexture pointer obtained from RenderTexture.GetNativeTexturePtr.
UNITY_INTERFACE_EXPORT void UNITY_INTERFACE_API
FRGlassRT_SetOutput(void* texture)
{
    s_OutputTexture = texture ? (__bridge id<MTLTexture>)texture : nil;
}

UNITY_INTERFACE_EXPORT UnityRenderingEventAndData UNITY_INTERFACE_API
FRGlassRT_GetRenderEventFunc()
{
    return RenderEvent;
}

// Event id 1 consumes EventData and traces a camera primary ray. It writes an
// opaque RGBA reflection only when that primary hit has the glass material bit;
// every non-glass/background pixel is written as (0,0,0,0).
UNITY_INTERFACE_EXPORT int UNITY_INTERFACE_API
FRGlassRT_RenderEventId()
{
    return 1;
}

} // extern "C"
