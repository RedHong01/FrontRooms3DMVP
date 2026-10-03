# 03 — Research: what production ray-traced glass reflections should look like in FrontRooms

Date: 2026-10-03. Status: COMPLETE (research step of the RT glass track). Read-only for the real project: the only
files written under `Frontrooms3D/` are this report and `03_bench/` next to it. Nothing in Unity was opened.

Task: Red asked the visual chat to understand ChatGPT's independent hardware ray-traced glass prototype (commit
`edfbc92`) and take it on. This report answers: what should the production version of real-time ray-traced
reflections for GLASS look like in this game, at the highest desktop spec, and what do Apple, shipped games and
Unity say about each part of it.

Conventions. **MEASURED** = timed on Red's Mac for this report (§2.3). **ESTIMATE** = arithmetic or judgement.
**UNVERIFIED** = not confirmed from a source read for this report. Sources are numbered [A..] Apple, [G..] games and
graphics papers, [U..] Unity, [P..] physics, and listed in full in §9. `file:line` paths are relative to
`Frontrooms3D/` (commit `edfbc92`).

---

## 0. Short answer (for Red)

1. **Ray tracing on your Mac is real, but only through a native plugin.** Unity 6.3 still reports no ray tracing on
   Metal (our G11 measurement), but Metal itself gives a plugin hardware ray tracing on M3-class GPUs. Apple calls the
   M3 "hardware-accelerated ray tracing ... on the Mac for the first time" [A8]. So the G11 line "no ray tracing on the
   M3 Max" is superseded **for desktop Mac only**. WebGL and HDRP conclusions do not change.
2. **It is cheap on the M3 Max.** MEASURED with a standalone Metal benchmark of an office-like scene (2,912
   instances, 15 M instanced triangles): one reflection ray per glass pixel, with lamp shading and shadow rays, costs
   **about 0.5 ms at 1080p and about 0.8-1.0 ms at 1440p** when glass covers a quarter of the screen (a held pane).
   Rebuilding the whole top-level structure (TLAS) every frame costs **0.3 ms for 1,792 instances and 0.5 ms for
   4,096**. Scene size barely matters: 256 instances and 2,912 instances trace at almost the same speed (§2.3).
3. **What the production version looks like** (§6): rasterize the glass panes into a small "glass G-buffer" (position,
   normal) after the opaque pass; trace one mirror ray per glass pixel from it on Unity's own Metal command buffer;
   shade the hit like the game shades that surface (same textures in world metres, same lamps, emissive troffer lenses
   that flicker in sync, same fog); write `_FR_GlassRTReflection`; the FrontRooms/Glass shader uses it **before**
   tonemapping and bloom. No denoiser and no TAA are needed, because clean glass is a mirror (SEED: clear glass
   "No filtering required" [G2]).
4. **The prototype is a valid proof that the plumbing works, not a base to ship.** Of the 10 suspected defects, 8
   are confirmed by reading or by the parallel review, #2 (vertical flip) needs a runtime check and #9 is inert but
   should be fenced (§1). The research adds five more: no residency calls for the acceleration structures and
   buffers it reads indirectly (Apple: this "can cause command buffer failures, GPU restarts, or even image
   corruption" [A5]); its command buffers run outside Unity's frame order; render-thread races on the shared pointers;
   moving things (Relay, doors) update only once a second; and `supportsRaytracing` is also true on M1/M2, which
   have no ray-tracing hardware.
5. **What makes interior window glass read as real** (§5): a clean pane reflects about 8 % face-on (two surfaces,
   ~4 % each) and 16 % at 60°. Against a **lit** room behind it only the troffer lenses show clearly (about twice
   the brightness of the room seen through the glass); against a **dark** room the whole lit room appears, like a
   one-way mirror. The second (back-surface) image of 6 mm glass is offset 2-4.5 mm, which is a few pixels only for
   things within about a metre. The troffers are the objects that matter most.
6. **Windows can feed the same texture.** URP 17.3 can use Unity's `RayTracingAccelerationStructure` with inline
   ray tracing in a compute shader on DX12 (DXR 1.1). No HDRP is needed. Unity's own UnifiedRayTracing library in
   Core 17.3 already does the instance tables and vertex fetch (§4). It needs a DX12 PC with an RTX/RX 6000-class GPU
   to test.
7. **What I need from the other chats** (§6.6): the map chat adds four small events or queries (chunk built, chunk
   releasing, room dressed, live lamp list). The glass track adds one optional prepass
   (`FRGlassRTPrepass`) so the traced ray uses the shader's own smudged normal. The destruction track gives every
   piece its own renderer, plus the marker component.

---

## 1. The prototype, checked against the research

What it does (read in full: `NativePlugin/FrontRoomsMetalGlassRT.mm` 763 lines,
`Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs` 394 lines, the renderer feature, the composite shader):
a native plugin gets Unity's `MTLDevice` and queue through `IUnityGraphicsMetalV2`, builds one bottom-level
acceleration structure (BLAS) per mesh straight from Unity's vertex and index `MTLBuffer`s, and a TLAS of up to 256
instances. It compiles an MSL kernel at runtime. Each frame it re-traces a camera ray per pixel, keeps pixels whose
first hit is flagged glass, reflects once, and shades the hit with the flat material colour x a fixed "sun" plus a
blue sky gradient on a miss (`.mm:239, 296`). URP then alpha-blends the result over the finished frame
(`FrontRoomsMetalGlassRTRendererFeature.cs:17`).

| # | Suspected defect | What the research / code reading says | Status |
|---|---|---|---|
| 1 | FOV in radians where `tan(fov/2)` is expected | `FrontRoomsMetalGlassRT.cs:240` passes `camera.fieldOfView * Deg2Rad`. The camera is 76° (`FrontRooms3DGame.cs:247`), so 1.326 is written where 0.781 belongs: rays fan out **1.70x** too wide, and the traced pane comes out 1/1.70 = 0.59x the real size. The parallel review measured 0.58x until `tan(fov/2)` (`images/01_review_trace_output.jpg`). | Confirmed |
| 2 | Possible vertical mirror | Kernel row 0 is the top of the Metal texture and gets `ndc.y = -1` (down); the composite flips `uv.y` again (`FrontRoomsMetalGlassRTComposite.shader:39`). Whether the two flips cancel depends on Unity's Metal render-texture convention. | Runtime check (review step) |
| 3 | Composite after post | `AfterRenderingPostProcessing` blends linear HDR over the graded, tonemapped image. BFV, Control, Lumen and HDRP all put the traced reflection into the lighting, before post ([G1] "Light Combine" -> "Lit Raster result"; [G12]). | Confirmed by design |
| 4 | Primary visibility re-traced against a partial scene | The kernel decides "is this pixel glass" with its own camera ray against at most 256 instances within 18 m (`.cs:33-34`), no depth test. Every shipped hybrid renderer uses the **raster** result for primary visibility ("We still rasterize our G-Buffer -- it plays the role of our primary rays" [A3]; SEED "Rasterize primary visibility" [G2]). | Confirmed by design |
| 5 | 1 s full rebuild on the main thread with `waitUntilCompleted` | `.mm:401-408, 483-490`: every BLAS and the TLAS are built with `waitUntilCompleted`, called from C# on the main thread (`.cs:121`). Unity: `GetNativeVertexBufferPtr`/`GetNativeIndexBufferPtr` "will synchronize with the rendering thread (a slow operation), so best practice is to set up necessary buffer pointers only at initialization time" [U1]. Multithreaded rendering is on (`ProjectSettings.asset:54 m_MTRendering: 1`). Apple: builds "run entirely on the GPU timeline with no CPU synchronization" [A1], so nothing needs to wait. | Confirmed by code |
| 6 | BLAS hold Unity's buffers that Unity may free | The kernel reads vertex and index data through their GPU addresses (`.mm:503`). The `MeshRecord` keeps strong ARC references, so a freed `Mesh` leaks rather than faults; but a mesh whose CPU data changes gets **new** GPU buffers [U1 `Mesh.GetVertexBuffer`], and chunk shells are destroyed on release (`FrontRoomsMapWorld.cs` `Unregister` -> `FreeMeshes`). Whether Unity 6.3 sub-allocates mesh buffers on Metal (offset not 0) is UNVERIFIED. | Confirmed risk |
| 7 | Hit shading ignores textures, lamps, emission, fog; blue sky on miss | `.mm:230-245` (`ShadeHit`), `:296`. BFV's rule: "Shader output must match!" between raster and ray hits [G1 slide 80]. | Confirmed |
| 8 | 30 mm cube pane: two faces, no thin-glass model | Both big faces are glass-flagged; the back face only matters if the camera is on the other side (correct). Real thin glass has a front and back reflection of near-equal strength (§5.2); nothing models that. | Confirmed (minor) |
| 9 | Feature in the one shared URP renderer | `FrontRooms_URP_Renderer.asset:95`. It is inert off macOS (`.cs:76` early-out, `AddRenderPasses` returns when not ready). The `.meta` of the dylib has no importer block (only a `guid`), so its platform settings are Unity's defaults; set them explicitly. | Inert, keep it provably so (§6.7) |
| 10 | GPU cost unmeasured | Measured here for the production shape of the work (§2.3), not for the prototype itself. | Done (§2.3) |
| 11 | **New:** no residency calls | The TLAS references BLASes, and the kernel reads vertex/index buffers through raw GPU addresses; the prototype never calls `useResource`/`useHeap`. Apple: "it is very important that apps flag residency to Metal for all indirectly accessed resources ... This can cause command buffer failures, GPU restarts, or even image corruption" [A5]; WWDC23 binds the TLAS and then calls `useHeap` to "Make the acceleration structures referenced in your instance acceleration structure available on the GPU" [A6]. | Confirmed by code |
| 12 | **New:** own command buffers on Unity's queue | `RenderEvent` (`.mm:583-620`) creates and commits its own command buffer instead of encoding into Unity's current one. Unity's header says to end Unity's encoder and use the current command buffer for custom work [U3]. Ordering against the frame's depth and transparents is therefore not guaranteed (exact behaviour UNVERIFIED). | Confirmed by code |
| 13 | **New:** render-thread races | `FRGlassRT_Reset` (main thread, under a mutex) sets `s_Tlas = nil` (`.mm:668`) while `RenderEvent` (render thread) reads `s_Tlas` with no lock; `FRGlassRT_SetOutput` writes `s_OutputTexture` unlocked (`.mm:745`); one shared `eventData` block is rewritten every frame while the render thread may still read the previous one. | Confirmed by code |
| 14 | **New:** moving things update once a second | Instance transforms are only sent in `RebuildScene` (every `rescanSeconds = 1`, `.cs:35`). A walking Relay or a swinging door jumps in the glass once a second. | Confirmed by code |
| 15 | **New:** wrong hardware test | `supportsRaytracing` (`.mm:652`) is true on every Apple6+ GPU: Metal Feature Set Tables list "Ray tracing in compute pipelines ... Apple6" [A12], i.e. M1 and M2 too, which trace in software. Hardware intersection is Apple family 9 ("Apple A17, M3, and M4" [A11]); M3 hardware RT per [A7]. Test `supportsFamily(MTLGPUFamilyApple9)` for the full-quality tier. | Confirmed by docs |

Also: the output is `ARGBFloat` (128-bit per pixel, `.cs:253`); half float (`RGBA16F`) is enough for HDR radiance and
halves the bandwidth. The prototype's good parts are worth keeping: the `IUnityGraphicsMetalV2` route, BLAS per
`Mesh`, the per-instance info table with GPU addresses, and a glass flag per material.

---

## 2. Metal ray tracing on Apple silicon (item 1)

### 2.1 Hardware and families

- M3 family: "hardware-accelerated ray tracing comes to the Mac for the first time"; "Rendering speeds are now up to
  2.5x faster than on the M1 family"; M3 Max has a 40-core GPU [A8]. Red's machine: Apple M3 Max, 40 cores, Metal 4,
  macOS 26.6.2 (`system_profiler`).
- What the hardware does (Apple tech talk, Jedd Haberstro): the traversal runs on "fixed function hardware", each ray
  independently; intersection functions still run as shader code, grouped by a "reorder stage" so divergence is
  "reduced or even completely eliminated" [A7]. Apple publishes **no rays-per-second figure**; §2.3 measures one.
- Apple's M3 advice [A7]: "use the intersector object API whenever possible" (the intersection-query API "increases
  the amount of ray trace scratch memory ... as well as disables the reorder stage"); one intersection function per
  logical routine, not an uber-function; keep the ray payload small; mark geometry **opaque** so the built-in
  triangle test is used.
- Families [A12]: ray tracing in compute and render pipelines from **Apple6**; residency sets from Apple6;
  "Acceleration structure build options", "Intersection function buffers", "MetalFX denoised upscaling" from
  **Apple9**. An intersector can traverse 32 levels, an intersection query 16 [A12].

### 2.2 Acceleration structures: what Apple recommends

| Topic | Apple guidance | For FrontRooms |
|---|---|---|
| Levels | Primitive AS = triangles; instance AS = transformed copies of primitive AS, "to reduce memory usage" [A1]. Multi-level instancing exists (an instance AS inside an instance AS) [A6]. | Two levels are enough: BLAS per mesh, one TLAS. |
| BLAS per mesh vs merged | Geometry descriptors can hold several geometries, each with its own buffers [A1]. WWDC22 suggests merging overlapping instances into one primitive AS with transforms "to reduce the instance count" [A4]. | One BLAS per **Unity `Mesh`**: chunk shell meshes are already merged per 6 m block and material by the map (`FrontRoomsMapWorld.cs` `BuildInto`/`AddRenderer`), panes, lenses, door leaves and keys share Unity's cube, props share kit meshes. |
| Refit vs rebuild | "Refitting an existing acceleration structure is much faster than a full rebuild"; refit "a handful of deforming or animated models" each frame [A4]; refit when geometry "only changes slightly" [A6]. Refit needs the `refit` usage flag [A11]. | Refit only for **deforming** meshes (a future skinned Relay). Rigid moving things (doors, Relay parts, falling glass pieces) need **no** BLAS work: only their instance transform changes. |
| TLAS per frame | "You should also do a full rebuild of the instance acceleration structure ... Doing a full rebuild is fine ... it usually only contains at most a few thousand objects" [A4]. Static/dynamic split possible [A6]. | Rebuild the TLAS every frame from live transforms (0.3-0.5 ms MEASURED, §2.3). This also absorbs the 192 m world rebase (`ModuleUnits.WorldPeriod`) for free. |
| Batching | Builds run in parallel when encoded on one encoder: "up to 2.8 times faster"; use a small pool of scratch buffers, not one [A4]; reuse scratch between batches [A6]. | Encode all BLAS builds of a chunk on one encoder, inside Unity's frame (§6.4). |
| Build flags | `refit`, `preferFastBuild`, `preferFastIntersection`, `minimizeMemory`, `extendedLimits` [A11]; per-build flags are an Apple9 feature [A9][A12]. | Default (fast trace) for static shells and props; `refit` only on deforming meshes. |
| Compaction | Metal over-allocates; after the build, `writeCompactedSize` then `copyAndCompact`; "especially valuable for primitive acceleration structures" [A6]. | MEASURED: compacted BLAS = **46 %** of built size (§2.3). Compact static meshes a few frames after their build (async size readback). |
| Heaps | AS can live in `MTLHeap`s; "you can flag them all resident in a single call to useHeap" [A5]; a small speed-up seen from replacing `useResource` with one `useHeap` [A4]. Heaps are untracked unless opted in, so builds must be synchronized by you [A5]. | Allocate BLASes and our own geometry copies from one heap. |
| Vertex formats / primitive data | Half and normalized formats are accepted directly; per-primitive data gave "10% to 16%" gains in Apple's tests [A4]. | Positions are float3; per-primitive data not needed (we fetch the triangle). |

### 2.3 MEASURED: a standalone Metal benchmark on Red's M3 Max

Not Unity, not the game: a 308-line Objective-C++ program (`03_bench/rt_bench.mm.txt`) that builds an office-like
scene and times GPU work with command-buffer GPU timestamps (median of 7-22 runs). The scene: a 96 m square of 6 m
cells, each with floor and ceiling slabs, 0-2 walls, two 0.6 x 1.2 m lens boxes, and 6 props drawn from 16 meshes of
2,048-20,480 triangles: **2,912 instances, 15.05 M instanced triangles, 17 unique meshes (160 k triangles)**. A virtual
pane 1.5 m in front of the camera (1.6 m eye height, 76° vertical FOV, like the game) covers 25 % or 100 % of the
screen; each covered pixel traces one reflection ray (max 30 m), fetches the hit triangle to get its normal, loops over
32 lamps (N·L, range 10 m), and casts shadow rays for the first 4 or 8 lamps. Logs: `03_bench/bench_run1.txt`,
`bench_run2_threadgroups.txt`. Other Unity batch jobs were using the GPU during the runs, so treat values as ±30 %.

| Work | MEASURED (M3 Max) |
|---|---|
| BLAS build, 17 meshes / 160 k triangles, one encoder | 1.8-3.1 ms default; 1.7 ms `preferFastBuild` |
| BLAS build, one 20,480-triangle mesh | 0.63 ms; **refit 0.17 ms** |
| BLAS build, one 12-triangle box (fixed cost of one build pass) | 0.16 ms |
| BLAS memory before / after compaction | 13.6 MB / 6.2 MB (**46 %**); vertex + index data 2.8 MB |
| TLAS rebuild: 256 / 1,024 / 1,792 / 4,096 / 16,384 instances | 0.18 / 0.25 / 0.29 / 0.52 / 2.06 ms |
| Trace, 1080p, glass 25 %, nearest 256 instances, no lamps | 0.32-0.39 ms |
| Trace, 1080p, glass 25 %, full 2,912 instances, no lamps | 0.34-0.48 ms |
| + 32 lamps unshadowed | 0.47-0.51 ms |
| + 32 lamps, 4 shadowed / 8 shadowed | 0.46-0.65 ms / 0.46-0.78 ms |
| 1080p, glass **100 %**, 32 lamps, 4 shadowed | 1.47-1.91 ms |
| **1440p**, glass 25 %, 32 lamps, 4 shadowed | **0.81-1.01 ms** |
| 2160p, glass 25 %, 32 lamps, 4 shadowed | 1.70-2.67 ms |
| Max ray length 30 m vs 10,000 m | no measurable difference |
| Threadgroup 8x8 vs 16x16 vs 32x32 | no consistent difference (within noise) |

What this means:
- **Throughput**: about 1.0-1.6 billion reflection rays per second including the simple shading, i.e. the 0.52 M
  rays of a held pane at 1080p take a third of a millisecond. Hardware traversal scales with log(scene), so
  **registering the whole neighbourhood costs almost nothing**; the prototype's 256-instance cap saves nothing and
  causes defect 4.
- **Shadow rays**: the bench only shadows the first lamps in its list, some of which are out of range, so the shadow
  cost is a lower bound. Budget about +0.1-0.3 ms at 1080p for 4-8 shadowed lamps (ESTIMATE).
- **Not included**: texture sampling at the hit, URP-matching light falloff, the game's real triangle counts, the glass
  prepass, and Unity's own GPU load. ESTIMATE for the production pass at 1440p with a held pane: **1-2 ms GPU**. The
  G11 editor bench measured a CPU-bound 37-55 ms frame, so this is small; still, time it in a player build.

### 2.4 Tracing API: what to use

- **Intersector, not intersection query**, on M3 [A7]. Result fields on a triangle hit: `distance`,
  `primitive_id`, `instance_id`, `triangle_barycentric_coord` (with the `triangle_data` tag), and with
  `world_space_data` the object-to-world transform [A2][A6]. Barycentrics interpolate UVs:
  `uv0*b.x + uv1*b.y + uv2*b.z` [A6].
- **User instance IDs** (`MTLAccelerationStructureUserIDInstanceDescriptor`, read as `user_instance_id`) carry "per-instance
  material ID or per-instance flags" [A2]: this is where the per-piece **glass flag** for destruction lives.
- **Instance masks** (8 bits) let one ray type skip a class of objects (e.g. shadow rays ignore glass) [A3].
- **Shadow rays**: `accept_any_intersection(true)` and a max distance to the light [A3].
- **Alpha**: intersection functions or the query loop do alpha testing [A1][A2]. FrontRooms has no alpha-tested
  surfaces in the glass's reflection range that I know of; keep everything **opaque** for the hardware path.
- **Payload**: the WWDC20 talk warns that combining heavy shading with the intersection step "may end up with a compute
  kernel that runs at lower occupancy" [A1]. For one bounce this is fine; profile.
- Apple's own reflection sample is titled "Rendering reflections in real time using ray tracing" ("dynamically
  generating reflection maps by encoding a ray-tracing compute pass") [A13]; its code was not downloaded.

### 2.5 Residency and bindless hit shading

- Anything the kernel reaches **indirectly** (BLASes referenced by the TLAS, vertex/index buffers read through GPU
  addresses, textures read through resource IDs) must be made resident per pass with `useResource:usage:` or
  `useHeap:` [A5][A6][A11 `useResource`]. Metal's shader validation reports a missing one with the buffer label [A5].
- Metal 3 bindless: write `gpuAddress` and `gpuResourceID` straight into a buffer struct ("Metal 3 simplifies writing
  argument buffers by allowing you to directly write into them like any other CPU-side structure") [A5]. Apple's hybrid
  talk: hit shading that reads "vertex data and Metal resources from the compute kernel directly" is "achieved with a
  bindless binding model which in Metal is represented as argument buffers" [A3].
- For FrontRooms the simpler, cross-platform choice is a **material table + one `Texture2DArray`** of albedo/mask maps
  (§6.3), because the Windows path has no bindless in Unity. On Mac, the array's native pointer is one resource to
  make resident.

### 2.6 Unity interop facts that shape the design

- Native rendering must run on the render thread via `IssuePluginEvent`/`IssuePluginEventAndData`; with multithreaded
  rendering "the rendering API commands run on a separate thread from MonoBehaviour scripts" [U1
  low-level-native-plugin-rendering-extensions].
- `IUnityGraphicsMetalV2` exposes `CurrentCommandBuffer()`, `EndCurrentCommandEncoder()` and
  `CommitCurrentCommandBuffer()`; "you should end unity's encoder before creating your own and end yours before
  returning control to unity" [U3]. Encoding the BLAS/TLAS updates and the trace into Unity's current command buffer
  puts them exactly between the opaque pass and the transparents.
- `GetNativeTexturePtr`, `GetNativeVertexBufferPtr`, `GetNativeIndexBufferPtr`, `GraphicsBuffer.GetNativeBufferPtr`
  all synchronize with the render thread; call them only when a resource is (re)created [U1]. So the RT output and
  prepass targets must be **persistent RTHandles imported into RenderGraph**, not per-frame transient textures.
- Changing a mesh's CPU data can re-create its GPU buffers; call `GetVertexBuffer` again [U1]. Skinned meshes expose
  their skinned output with `SkinnedMeshRenderer.GetVertexBuffer()` after requesting `GraphicsBuffer.Target.Raw` [U1].

### 2.7 MetalFX and Metal 4: not for this pass

- WWDC25: the MetalFX denoised upscaler takes noisy ray-traced colour plus world normals, diffuse and specular albedo,
  roughness, motion vectors and depth, and goes "after jittered rendering, and before post effects" [A9];
  `MTLFXTemporalDenoisedScaler` needs macOS 26 [A11] and Apple9 [A12]. It replaces the whole AA/upscale stage with a
  temporal one. FrontRooms renders with 4x MSAA and no TAA on purpose (ghosting on the key shots, audit §5.3), and
  mirror glass needs no denoising, so **do not use it here**. It is the tool if Red ever wants path-traced GI.
- WWDC26 session 359 is about MetalFX neural denoising for path tracing (checked for relevance only) [A10].
- Metal 4 adds intersection function buffers (DirectX shader-table style) and per-build flags [A9]; not needed for an
  opaque one-bounce trace.

---

## 3. Hybrid ray-traced reflections in shipped games (item 2)

| Game / engine | Which pixels trace, ray budget | Hit shading | Miss / far | Denoise | Glass |
|---|---|---|---|---|---|
| **Battlefield V** (DICE, Frostbite, 2018) [G1][G3][G4] | Variable-rate tracing per screen tile ("More Rays on Water", "on grazing angles"); presets: smoothness cut-off 0.9 (Low/Med) or 0.5 (High/Ultra), max rays 15-40 % of screen pixels [G3, partly verified] | Closest-hit shaders auto-generated from the raster shaders ("Shader output must match!", ~3,000 per level, ~250 per frame); payload = G-buffer format; per-cell light lists; mip 0 texture sampling | Screen-space march first, rays only where it fails ("SS-Hybridization") | Spatial BRDF filter + own temporal filter + an image filter sized by {angle, roughness}; 6.29 ms total on 2018 hardware | Windows listed among traced surfaces ("windows, cars, tanks, lamp posts, tiles, puddles and weapons", C. Holmquist [G4]); particles traced in a second TLAS with an order-independent any-hit (0.96 -> 0.34 ms) |
| **PICA PICA** (EA SEED research, 2018) [G2] | Rasterize primary visibility; trace at half resolution (1 of 2x2 pixels), reconstruct at full res | Material layers; shadow ray at hit | — | Stochastic-SSR-style spatial reuse, colour-box clamped history, variance-guided bilateral | Glass by refracted rays with IOR transitions and tint; "Clear: No filtering required"; rough glass opens a cone, needs more samples or temporal filtering |
| **Control** (Remedy, Northlight, 2019) [G5][G6][G7] | Separate settings for opaque and **transparent** reflections | Northlight precomputed voxel GI helps light reflections and diffuse (per [G5] search summary; detail UNVERIFIED) | SSR or cubemaps when off [G6] | Effect-specific denoisers [G7, not read] | "Adding ray-traced reflections to glass is no different than ray tracing a puddle, if the background is opaque. When it's transparent, with detail visible on the other side, in an office for instance, extra work is required"; transparent reflections trace "without blocking the visibility of detail beyond the window" [G5] |
| **Metro Exodus Enhanced Edition** (4A, 2021) [G8] | "We use RTR to fill these gaps where SSR fails"; rays "only ... when absolutely necessary" | "the same, low level of detail, material system as the diffuse Ray Tracing pipeline, but ... the higher quality PBR lighting model to accurately reflect data from analytic light sources"; emissive surfaces add light when sampled | — | not stated | not stated |
| **Cyberpunk 2077** (CD Projekt RED, 2020) [G9] | Opaque and transparent surfaces | — | — | (NRD per secondary sources, UNVERIFIED) | "glass exhibits transparent reflections"; reflections of neon on cars, water, buildings |
| **UE5 Lumen** (Epic) [G10] | Screen traces first; "Max Roughness to Trace" | Surface Cache by default "significantly faster"; **Hit Lighting** "for higher quality" | falls back to other tracing | temporal | "High Quality Translucency Reflections": "mirror reflections on the front layer of translucent surfaces. Other layers will use the lower quality Radiance Cache"; "increases GPU cost"; water forced to mirror |
| **Unity HDRP** RT reflections [G12] | "Minimum Smoothness"; "Full Resolution: One ray per pixel, per frame", else one ray per four pixels; sample and bounce counts | Light cluster at hit | "Ray Miss": reflection probes, sky, both, nothing | Optional spatio-temporal filter | Builds on the SSR override; HDRP RT needs DX12 (G11) |
| **AMD FidelityFX Hybrid Reflections** (2023) [G13] | SSSR first, hardware rays for the rest, "per-pixel feedback to reduce hybridization cost", FSR 1 upscale of low-res reflections | reshades re-projected pixels | — | FidelityFX reflection denoiser | — |
| **Spider-Man: Miles Morales** (Insomniac, PS5, 2020) | UNVERIFIED (from memory, not re-read: web search budget was used up): reduced-resolution reflections; fewer NPCs/cars and lower LODs in the ray-traced scene in the 60 fps mode; skyscraper windows combine an interior cubemap (what is behind) with the traced reflection (what is in front) | | | | the two-layer window look FrontRooms needs |
| **RE Engine** (Capcom: RE Village 2021 and later) | UNVERIFIED (not re-read): hybrid screen-space + ray-traced reflections at reduced resolution | | | | |

**Denoisers and TAA.** SVGF reconstructs 1-sample path tracing "in approximately 10ms at 1920x1080" with temporal
accumulation and a variance-guided wavelet filter [G15]. NVIDIA's NRD needs non-jittered motion vectors, normals,
roughness, view Z and hit distance, does its own temporal accumulation, and its sample shows a "denoising-free" glass
path; for pure mirrors it recommends "Primary Surface Replacement" [G14]. All of these exist to clean **rough**
reflections traced with few rays.

**Lessons for FrontRooms glass:**
1. Raster decides primary visibility; rays start from the G-buffer of the surface (all of [A3][G1][G2][G10]).
2. Glass is the cheap case: **mirror rays are noise-free**. Trace one ray per glass pixel at full resolution. Use
   the half resolution of PICA PICA/HDRP only on a weaker tier.
3. Smudges are the only "rough" part. Blur them deterministically by roughness and hit distance, as BFV's image
   filter does ({angle, roughness} -> kernel size for a unit-length ray [G1]). Do not use a temporal filter:
   no motion-vector dependence, no ghosting, works with MSAA.
4. Hit shading must match the raster (BFV's rule [G1]) and needs real lights. Metro uses its analytic lights with
   PBR [G8]; Lumen offers "Hit Lighting" for quality [G10]. For an office lit by troffers, **emissive lenses + lamp
   lights at the hit** are the content.
5. Glass with something visible behind it is a special case (Control's "extra work", Lumen's "front layer"). The
   reflection is **added** over what is seen through the pane and never hides it. FrontRooms/Glass already works
   this way ("Preserve Specular" premultiplied blend).
6. Cull the ray-traced scene by distance and angular size (BFV: 4° culling took 5,000 -> 400 BLAS rebuilds and
   20,000 -> 2,800 instances, 64 -> 14.5 ms, then 1.15 ms with staggered refits and fast-build flags [G1]). Our scene
   is far smaller (§2.3).

---

## 4. Unity on Windows: a DX12 path that feeds the same texture (item 3)

**Yes, URP 17.3 can do it without HDRP.** The ray-tracing API is pipeline-agnostic:
- `RayTracingAccelerationStructure` "enables you to efficiently intersect rays against a subset of the Scene geometry
  using the GPU"; it is passed to compute shaders with `ComputeShader.SetRayTracingAccelerationStructure` or
  `CommandBuffer.SetRayTracingAccelerationStructure`; Unity's own example on that page is a **compute shader per
  screen pixel using inline ray tracing**, checking `SystemInfo.supportsInlineRayTracing` [U1].
- Inline ray tracing = `RayQuery` in compute and raster stages; "In DirectX 12 (DX12), this property corresponds to
  DirectX Raytracing (DXR) Tier 1.1 support"; use `UnityRayQuery.cginc`'s `UnityRayQuery` for portability [U1];
  shaders declare `#pragma require inlineraytracing` (added in 2023.1, with `ComputeShader.SetRayTracingAccelerationStructure`)
  [U1 WhatsNew20231]. The Ray Tracing API left experimental in 2023.1 [U1].
- **Requirements**: Windows, DX12 as the active API, a DXR 1.1 GPU. HDRP's list (RTX 20+, RX 6000+) is the practical
  floor (G11 §1.2). The project's `m_BuildTargetGraphicsAPIs` is empty (Unity's defaults). Whether Unity 6.3 defaults
  to DX12 or DX11 on Windows is UNVERIFIED, so set DX12 explicitly for that build.

**Instance management** (all in the 6.3 scripting reference [U1]): `ManagementMode.Manual`;
`AddInstance(Renderer, subMeshFlags, enableTriangleCulling, frontTriangleCounterClockwise, mask, id)` (the `id` comes
back in HLSL as `InstanceID()`), or `AddInstance(ref RayTracingMeshInstanceConfig, matrix, ...)` for meshes without
a renderer; `UpdateInstanceTransform`; `RemoveInstance`; `CullInstances` with `RayTracingInstanceCullingConfig` "to
add only the instances which match certain criteria"; `CommandBuffer.BuildRayTracingAccelerationStructure(rtas,
relativeOrigin)` must run before tracing after any change. Unity builds and refits BLASes itself (dynamic-geometry
flags for skinned meshes).

**RenderGraph integration (URP 17.3 source).** The legacy builder has `Read/WriteRayTracingAccelerationStructure` and
`RenderGraph.ImportRayTracingAccelerationStructure` (`Core/Runtime/RenderGraph/RenderGraphBuilder.cs:146-163`,
`RenderGraph.cs:1268`), but URP's new `AddComputePass`/`AddUnsafePass` builders do not track acceleration structures.
`ComputeCommandBuffer` wraps `BuildRayTracingAccelerationStructure` and `SetRayTracingAccelerationStructure(ComputeShader,
...)` (`Core/Runtime/CommandBuffers/ComputeCommandBuffer.cs:558-600`). So: one compute pass that reads the glass
prepass textures, writes the output RTHandle, calls `AllowPassCulling(false)`, builds the RTAS and dispatches the
trace kernel.

**Vertex data at the hit.** HLSL in Unity has no bindless buffer arrays, so per-mesh vertex buffers cannot be indexed
by instance. Two options:
1. Our own geometry pool (one big `GraphicsBuffer`, meshes copied in at registration with
   `Mesh.vertexBufferTarget |= Raw` + `GetVertexBuffer`) [U1].
2. **Unity's UnifiedRayTracing (URT) library in Core 17.3**, which already does this: `MeshInstanceDesc` (mesh,
   sub-mesh, transform, mask, `instanceID`, `opaqueGeometry`), a `Hit` with `instanceID`, `primitiveIndex`,
   `uvBarycentrics`, `hitDistance`, `isFrontFace`, and `FetchHitGeomAttributes` for positions, normals and UVs
   (`Core/Runtime/UnifiedRayTracing/IRayTracingAccelStruct.cs:8-66`, `CommonStructs.hlsl:28-34`,
   `FetchGeometry.hlsl:65-116`). It picks the hardware backend when `SystemInfo.supportsRayTracing` is true, the
   compute backend otherwise (`RayTracingContext.cs:101`; G11 §1.4). "Ray tracing with the UnifiedRayTracing API" is in
   the 6.3 manual [U1 WhatsNewUnity63]. **Recommendation: write the Windows path on URT.** The same HLSL hit shader
   then also runs, slowly, on the compute backend anywhere for debugging.

**Shared contract.** The Windows pass writes the same `_FR_GlassRTReflection` (RGBA16F) and `_FR_GlassRTWeight`, from
the same glass prepass, with the same material table, lamp list and hit-shading rules as Mac (§6.3). Only the trace
kernel differs: MSL in the plugin vs HLSL/URT in Unity. Limitation: Red has no DX12 RTX machine here (G11), so this
path cannot be tested on this Mac. Effort ESTIMATE 4-6 days plus a test PC.

---

## 5. What makes a reflection in interior window glass read as real (item 4)

### 5.1 How strong a clean pane reflects (physics)

Fresnel for glass n = 1.52, unpolarized, computed here (ESTIMATE from the Fresnel equations [P1]: "about 4%" per
surface at normal incidence; Brewster's angle "around 56°"). A pane has two surfaces; light reflected inside adds up
(no interference in window glass):

| View angle from the pane normal | One surface | Whole pane (front + back) | Back-surface image alone | Offset of the back image, 6 mm pane | 30 mm prototype cube |
|---|---|---|---|---|---|
| 0° (face-on) | 4.3 % | **8.2 %** | 3.9 % | 0 mm | 0 mm |
| 30° | 4.4 % | 8.4 % | 4.0 % | 3.6 mm | 18 mm |
| 45° | 5.3 % | 9.8 % | 4.4 % | 4.5 mm | 22 mm |
| 60° | 9.3 % | 15.7 % | 6.2 % | 4.2 mm | 21 mm |
| 70° | 17.5 % | 27.5 % | 9.3 % | 3.2 mm | 16 mm |
| 80° | 39 % | 54 % | 12.5 % | 1.8 mm | 9 mm |

Consequences:
- URP's dielectric F0 of 0.04 models **one** surface. A real pane is about **twice** as reflective face-on.
  Recommendation to the glass track: F0 ≈ 0.08 for window panes (Schlick with 0.078 gives 7.8 % / 8.0 % / 10.7 % /
  19 % at 0/45/60/70°, close to the exact two-surface curve up to 60°; above that the shader's own grazing term
  dominates anyway).
- **The second image is almost as strong as the first** (3.9 % vs 4.3 % face-on). It is offset by 2-4.5 mm on 6 mm
  glass. Seen from the camera the two images separate by offset / (path length). That is 3 px at 1080p and 4 px at
  1440p for something 1 m away along the reflected path, and under 1 px beyond about 4 m. So it shows only on near
  bright edges (a lens at arm's length, the Relay right behind the player). The prototype's 30 mm "pane" would
  double things by 15-20 px, which is one more reason to treat the thin box as a single sheet (§6.3).

### 5.2 Reflection vs the light behind the glass

Whether you see the reflection or the room behind is decided by the ratio of the reflected luminance to the
transmitted luminance. The one-way-mirror principle: "The light from the bright room reflected from the mirror back
into the room itself is much greater than the light transmitted from the dark room" [P2]. For FrontRooms (ESTIMATE;
troffer lens about 2,000 cd/m² assuming ~4,000 lm over a 0.72 m² prismatic lens; a bare fluorescent tube is about
12,000 cd/m² [P5]; a lit office wall about 95 cd/m² at 500 lx and 60 % reflectance; an unlit room seen through
glass about 2-5 cd/m²; transmission ≈ 0.9):

| Behind the glass | Seen through it | Reflected wall (8 %) | Reflected troffer lens (8 %) | What reads |
|---|---|---|---|---|
| A lit room | ~86 cd/m² | ~8 cd/m² = **9 %** of the background | ~160 cd/m² = **~2x** the background | Only the troffers (and other bright things) show; the room is a faint ghost |
| A dark room | ~2-5 cd/m² | ~8 cd/m² = **2-4x** the background | ~160 cd/m² = 30-80x | A mirror: the whole lit room, the player's side, the Relay behind you |
| Lit room, pane at 60° | ~80 cd/m² | ~15 cd/m² = 19 % | ~310 cd/m² | Walls start to show at grazing angles |

So in this game the dark windows between lit and unlit rooms are the ones where RT pays off most. They become
mirrors of the player's room. Lit-to-lit windows mostly show **troffer rows**. A luminance difference of ~1-2 % is
roughly the visibility threshold for large areas (textbook Weber fraction, not re-read). Verify the lens-to-wall
ratio in the game in linear HDR: if the lenses are not about 20x brighter than the walls they light, the reflections
will not rank the way they do in a real office.

### 5.3 What breaks a reflection up (and makes it believable)

- **Flatness and waviness.** Float glass has "uniform thickness and a very flat surface" [P4]. Tempered glass "does
  exhibit surface waves caused by contact with flattening rollers" [P3]. US codes require tempered or laminated glass
  "near doorways", in "large windows" and "windows which extend close to floor level" [P3]. In an office that means
  the sidelights next to doors are the ones most likely to show roller waves. ESTIMATE: a roller wave of 0.05 mm
  amplitude and 300 mm period tilts the normal by about 1 mrad, which bends the reflection by about 0.12°: a slow
  1-2 px wobble on long straight lines (troffer rows, ceiling grid) as the player walks. That is subtle and real.
  Note: the glass track's `_RollStrength` 0.02 (`proj_glass` FrontRooms/Glass) tilts the normal by about 20 mrad, a
  2.3° swing of the reflected ray, which is about 20x a real roller wave. On a cube map at infinity it hardly shows.
  With a traced reflection that has correct parallax it will look like warped plastic. Suggest 0.001-0.003 when RT
  is on, or per-pane variety (tempered sidelights wavy, annealed panes almost flat).
- **Grime.** Smears and prints raise roughness locally (the shader's 0.96 -> 0.62). Each smudge blurs the reflection
  inside its outline and adds a little haze, so the reflection stays sharp between smudges. That contrast between
  sharp and blurred patches is a strong "this is a real surface" cue. Dust at the bottom edge cuts the reflection
  and scatters lamp light. All of this is the glass shader's job; the RT pass only has to deliver a sharp mirror
  image plus the hit distance to blur it correctly.
- **The troffers dominate.** Lenses are the brightest reflected objects. Their reflections must flicker in sync with
  the real lamps: the map sets each lens's `_EmissionColor` per frame through a `MaterialPropertyBlock`
  (`FrontRoomsMapWorld.cs` fixture tick), so the hit shader needs the **per-instance current emission**, not the
  shared material's value. The prototype reads the shared material and so cannot do this.
- **Parallax and occlusion.** The reflected room must move correctly as the player walks and must include what is
  behind the player (a lamp going dark, the Relay). A cube map cannot do this; a planar camera can, but only for one
  pane (G11 §2.4). RT does it for every pane.
- **The player.** A first-person camera with no body casts no reflection. In a mirror-dark window the room appears
  but the player does not. Whether that is a bug or a horror beat is Red's call (open item 6).

---

## 6. The production design this research points to

### 6.1 Frame order (desktop, Mac M3+ first)

1. Opaques (URP Forward+, 4x MSAA) -> resolved `_CameraDepthTexture` (already on).
2. **Glass RT prepass** (new raster pass, 1x resolution, after opaques, before transparents): draws only the glass
   renderers (panes and glass pieces) and tests by hand against `_CameraDepthTexture`. Two persistent targets:
   `GlassPos` RGBA32F (world position, w = instance key) and `GlassNrm` RGBA16F (world normal, smoothness). Writing
   world position directly avoids every camera-reconstruction convention, which is what broke the prototype
   (defects 1 and 2).
3. **Trace** (unsafe pass -> `IssuePluginEventAndData`): in the native callback, `EndCurrentCommandEncoder`, then on
   Unity's `CurrentCommandBuffer`: (a) acceleration-structure encoder for pending BLAS builds (budgeted), refits, and
   the TLAS rebuild for this frame; (b) compute encoder with `useHeap`/`useResource` for everything referenced, one
   mirror ray per glass pixel, hit shading (§6.3), output `_FR_GlassRTReflection` RGBA16F (RGB linear HDR radiance,
   A coverage). Hit distance goes to an internal R16F. (c) A small post kernel applies the roughness-and-distance
   blur and the optional back-surface image (§6.3), so the glass shader samples the result 1:1.
4. Transparents: FrontRooms/Glass samples `_FR_GlassRTReflection` in screen space. Where `_FR_GlassRTWeight` x
   coverage > 0 it replaces its environment/planar term, multiplied by its own Fresnel and grime (the glass track's
   agreed interface).
5. Post (bloom, grade, ACES): the reflections are graded and bloomed with the scene (fixes defect 3). The
   full-screen composite and its after-post event are deleted.

### 6.2 Where rays start and which pixels trace

- Every pixel of every visible pane traces. Glass smoothness is 0.62-0.96, well above BFV's 0.5 cut-off and HDRP's
  usual minimum; no stochastic sampling is needed.
- Full resolution on Mac M3+ and DXR PCs (measured headroom, §2.3). Half resolution (one ray per 2x2, as PICA PICA/HDRP)
  only for an M1/M2 tier, whose Metal RT is software. That tier's speed is UNVERIFIED; default it off.
- Reflection ray max length 24-30 m; beyond that or on a miss, coverage = 0 and the pane keeps its probe/planar
  reflection (HDRP's "Ray Miss: reflection probes" behaviour [G12]). Exponential-squared fog (density 0.014,
  `FrontRoomsLook.cs:20-21`) is 6 % at 18 m and 16 % at 30 m, so a longer ray adds little.
- The normal: best is the glass shader's **own** perturbed normal (roll, smudge normal, crack facets), written by a
  tiny `FRGlassRTPrepass` pass in FrontRooms/Glass (contract request, §6.6). Fallback without it: geometric normal
  in the prepass, and the glass shader distorts its RT lookup in screen space by its micro-normal and samples a lower
  mip under smudges (the G11 §4.2 recipe for planar textures).

### 6.3 Hit shading spec (one bounce, must match the raster)

Per instance (built on the CPU when registered, flags and emission updated per frame): material index, flags (glass,
emissive lens, Relay, door, glass piece), current emission colour, object-to-world matrix, geometry offsets into our
own position/normal/UV pool.

| Surface hit | Shading at the hit |
|---|---|
| FrontRooms/Surface (walls, floors, ceilings: 83 of 86 surface materials, G11) | Rebuild the UV exactly as the shader does: `PlanarFrame(positionWS, geometric normal)` -> metres / `_TileSize` x `_BaseMap_ST` (`FrontRoomsSurface.shader:157-183`). No mesh UVs needed. Albedo and mask (smoothness) from the RT texture array; macro wear at 8 m / 12.8 m in world space; colour `_BaseColor`. |
| URP/Lit props (office kit) | UV0 by barycentric interpolation from our geometry pool; albedo from the texture array; mip level from distance (ray-cone texture LOD, Akenine-Möller et al., Ray Tracing Gems 2019, not re-read) |
| Troffer lens (`URP/Lit` emissive cube) | Emission = this instance's **current** `_EmissionColor` (per-lamp `MaterialPropertyBlock`, flicker and dimming included) |
| Another glass pane | Continue the ray through it once (x0.9 transmission) instead of reflecting again; at most 2 glass layers |
| Relay parts, doors, keys | Normal materials; transforms live every frame |
| Lighting at every hit | The lamps the map has **on this frame** (lit within `lightRadius` 16 m: a few dozen of ~1,500 lights), with URP's distance and spot falloff and their current intensity. Shadow rays **only** for lamps whose `Light.shadows` is on this frame (about one in three, within `shadowRadius` 9 m); unshadowed lamps stay unshadowed, exactly as in the raster. Diffuse plus GGX specular, like Metro's "higher quality PBR lighting model" [G8]. Ambient from the same ambient SH/colour as the raster. |
| After lighting | Exp² fog over the **hit distance** only (the glass shader fogs camera-to-glass itself) |
| Not traced | Volumetric beams and particles (transparent; BFV needed a second TLAS for its particles [G1]); revisit if the beams read as missing in mirror-dark windows |

Blur and thin glass (post kernel, before the glass shader reads it):
- **Smudge blur**: kernel radius from the pane's roughness at that pixel, the hit distance and the view distance,
  BFV-style ({angle, roughness} LUT scaled by ray length [G1]). Bilateral on the pane key so panes do not bleed into
  each other. Deterministic, no history.
- **Back-surface image** (Cinematic option): a second tap shifted by 2·t·tanθt·cosθi / (camera distance + hit
  distance), weighted 3.9/8.2 of the total (§5.1), with t = 6 mm (not the 30 mm of the box).

**Parity test** (BFV's "Verifying correctness" [G1]): a debug mode traces **primary** rays through the same hit
shader and compares them per pixel to the raster frame. Every non-zero difference is a hit-shading bug. The same test
would have caught the FOV and flip defects on day one.

### 6.4 Scene management

- **BLAS per Unity `Mesh`**, ref-counted, built from **our own copy** of positions (+ normals/UVs for props) in one
  `MTLHeap`. The copy is made with Unity's `GetVertexBuffer` + a GPU copy, or from CPU mesh data for the map's
  generated shells. This removes defect 6, Unity's sub-allocation risk and the per-registration render-thread syncs.
  Build on registration, inside Unity's frame, batched on one encoder, at most ~100 k triangles per frame (~1-2 ms,
  §2.3); compact a few frames later (-54 %).
- **When to register** (events from the map chat, §6.6): chunk built -> shell meshes, panes, doors, lenses; room
  dressed -> its props; chunk releasing -> drop its instances at once, free BLASes 3 frames later.
- **TLAS rebuilt every frame** from live transforms, for instances within ~36 m of the camera (12 m pane distance +
  24-30 m rays), with BFV-style angular-size culling and a cap of ~4,096 (0.5 ms). No 1 s rescans, no
  `FindObjectsByType`.
- **Dynamic things**: a marker component with a static registry (enable/disable registers/unregisters) on doors,
  Relay parts, keys and glass pieces; their transforms are read every frame. The Relay rig in the clone is built from
  primitives (`FrontRoomsRelayRig.cs:294`), so it needs no refit. A future skinned Relay would refit its BLAS every
  frame from `SkinnedMeshRenderer.GetVertexBuffer()` (~0.2 ms for 20 k triangles, §2.3).
- **Destruction**: pre-fractured stage meshes get their BLASes **at load time**, so swapping stages is only a TLAS
  change and never a build hitch. Every piece is its own instance with flags `glass | piece` (user instance ID [A2]),
  drawn by the prepass with its own normal. The reflection breaks up per facet by construction, which is what
  cracked glass looks like. Falling pieces only move transforms; there is nothing to refit.
- **Threading**: main thread -> render thread through a lock-protected command queue (add/remove mesh, add/remove
  instance) and a 3-slot ring of per-frame data (camera, lamp list, dynamic transforms). No `waitUntilCompleted`
  anywhere; compaction sizes are read back in a completion handler.

### 6.5 Tiers and budgets (desktop only; WebGL unchanged)

| Tier | Detection | Trace | Expected GPU (ESTIMATE from §2.3) |
|---|---|---|---|
| RT Cinematic (Mac M3/M4, DXR PCs) | `supportsFamily(Apple9)` / `supportsInlineRayTracing` | All panes within 12 m, full res, 30 m rays, all shadowed lamps, back-surface image, 4K captures | 1440p ~1-2 ms; 4K ~2-3 ms |
| RT High (same hardware, default) | same | All panes within 12 m, full res, 24 m rays, shadow rays for the nearest 4 shadowed lamps | 1080p ~0.5-1 ms; 1440p ~1-1.5 ms |
| RT Low (M1/M2, software traversal) | `supportsRaytracing` but not Apple9 | Held pane only, half res | UNVERIFIED; measure before enabling |
| No RT (everything else, all WebGL) | — | `_FR_GlassRTWeight = 0`: probes + planar from G11 | 0 |

### 6.6 Contract requests (nothing filed; exact signatures)

**Map chat** (`FrontRoomsMapWorld.cs`; the map chat confirmed these hook points exist and events are cheap):
1. `public event Action<GridCoord, Transform> ChunkBuilt;` raised at the end of `BuildInto`, after
   `built[coord] = chunk`, with `chunk.root.transform`.
2. `public event Action<GridCoord, Transform> ChunkReleasing;` raised at the **start** of `Unregister(chunk)`,
   **before** `FreeMeshes` and `Kill`, for drops, failed builds and live rebuilds (needs the chunk's coord stored in
   `BuiltChunk`; `Transform` may be null for a failed build).
3. `public event Action<GridCoord, Transform> RoomDressed;` raised when `Furnish` finishes one room (one room per
   frame), with the room's prop root.
4. `public int GetLitLamps(List<FrontRoomsLampSample> into);` filled each frame from the fixture tick:
   `struct FrontRoomsLampSample { public Light light; public Renderer lens; public Color lensEmission; public bool shadowsOn; }`
   (current intensity and colour come from `light`).
5. Keep `FrontRoomsMetalGlassRTController.Ensure()` and the pane `FrontRoomsMetalGlassTarget` (already merged); later
   rename to a neutral `FrontRoomsGlassRT` when the Windows path lands.

**Glass track** (`FrontRooms/Glass`):
6. Keep exactly `_FR_GlassRTReflection` / `_FR_GlassRTWeight` as agreed (no extra inputs needed).
7. Optional, for the best result: a pass `Tags { "LightMode" = "FRGlassRTPrepass" }` that writes world position
   (RGBA32F) and the shader's final normal + smoothness (RGBA16F), with the same grime/roll/crack code, no blending.
   It also helps a later screen-space effect.
8. F0 ≈ 0.08 for window panes, and a far smaller `_RollStrength` when RT is on (§5.1, §5.3).

**Destruction track**: each piece a separate renderer whose mesh BLAS can be prebuilt; the marker component on every
piece; stage meshes known at load.

### 6.7 Keeping WebGL and other platforms provably untouched

- Put the whole native layer under `#if UNITY_EDITOR_OSX || UNITY_STANDALONE_OSX` (and the later Windows layer under
  `UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN`). The WebGL build then does not even contain the P/Invokes. Excluding
  code from a platform does not change that platform's output.
- `AddRenderPasses` returns before enqueueing anything unless the controller is ready (it already does).
- Give the dylib explicit importer settings: Editor (OSX) + Standalone OSX, ARM64, every other platform off. Today
  its `.meta` has only a `guid`.

### 6.8 Effort (ESTIMATE)

| Work | Days |
|---|---|
| Native plugin rewrite: render-thread queue, ring buffers, own geometry pool + heap, residency, BLAS lifecycle and compaction, Unity command buffer | 4-6 |
| Glass prepass + RenderGraph passes + persistent RTHandles | 2 |
| Hit shading parity (Surface world UVs, Lit UVs, texture array, lamps with URP falloff, shadow rays, emission per lamp, fog) + parity test | 3-4 |
| Smudge blur + back-surface image | 1-2 |
| Destruction pieces + dynamic registry | 1-2 |
| Map events (map chat) | 0.5 |
| Windows path on URT (needs a DX12 RTX/RX 6000 PC) | 4-6 |

---

## 7. What this changes in earlier documents

- `11_reflections_and_raytracing.md` §0.1, §1.2, §4.1 "Ray tracing: none possible on the Mac": superseded for
  desktop Mac through a native Metal plugin (this report). Unchanged: URP has no built-in RT, HDRP RT is DX12-only,
  WebGL/WebGPU have none.
- G11's planar camera for the held pane (§2.4) stays as the fallback for non-RT desktops and the reference image for
  validating the RT mirror. The Relay-only overlay stays the WebGL plan.

---

## 8. Open items / UNVERIFIED

1. **M1/M2 speed**: Metal RT runs there without hardware traversal; how slow it is for this scene is unmeasured.
2. **Unity's Metal mesh buffers**: whether `GetNativeVertexBufferPtr` can return a shared, sub-allocated buffer (non-zero
   offset). Avoided by the own-copy design, but it matters if any prototype code is kept.
3. **Command ordering** of the prototype's separate command buffers relative to Unity's current one (defect 12): not
   tested; the production design removes it.
4. **Real textures and lighting at the hit**: the bench uses flat shading; texture-array sampling and URP falloff
   will add cost (ESTIMATE +30-50 %); measure in a player build with GPU timestamps.
5. **Troffer luminance ratio in the game**: measure lens vs lit-wall linear radiance in a capture (§5.2).
6. **The player's reflection**: no body mesh means no self-reflection in mirror-dark windows. Red decides.
7. **Spider-Man and RE Engine rows** (§3) are from memory; the session's web-search budget ran out. BFV preset
   numbers [G3] come from search summaries of the Eurogamer interview, whose page could not be fetched. Control's
   RTG II chapter [G7] and the Lumen SIGGRAPH 2022 slides [G11] were too large to fetch.
8. **Windows**: Unity 6.3's default Windows graphics API; URT hardware-backend performance; no DX12 RTX PC available.
9. **Roller-wave amplitude and period** for 1990-era tempered sidelights (§5.3) are ESTIMATES; ASTM C1048 limits
   were not read.

---

## 9. Sources

**Apple**
- [A1] "Discover ray tracing with Metal", Sean James, Apple, WWDC20 session 10012, 2020. https://developer.apple.com/videos/play/wwdc2020/10012/
- [A2] "Enhance your app with Metal ray tracing", Juan Rodriguez Cuellar, Apple, WWDC21 session 10149, 2021. https://developer.apple.com/videos/play/wwdc2021/10149/
- [A3] "Explore hybrid rendering with Metal ray tracing", Ali de Jong and David Núñez Rubio, Apple, WWDC21 session 10150, 2021. https://developer.apple.com/videos/play/wwdc2021/10150/
- [A4] "Maximize your Metal ray tracing performance", Yi and Dominik (Apple GPU software), WWDC22 session 10105, 2022. https://developer.apple.com/videos/play/wwdc2022/10105/
- [A5] "Go bindless with Metal 3", Alè Segovia Azapian and Mayur, Apple, WWDC22 session 10101, 2022. https://developer.apple.com/videos/play/wwdc2022/10101/
- [A6] "Your guide to Metal ray tracing", Pawel Szczerbuk, Apple, WWDC23 session 10128, 2023. https://developer.apple.com/videos/play/wwdc2023/10128/
- [A7] "Explore GPU advancements in M3 and A17 Pro", Jedd Haberstro, Apple tech talk 111375, 2023. https://developer.apple.com/videos/play/tech-talks/111375/
- [A8] "Apple unveils M3, M3 Pro, and M3 Max, the most advanced chips for a personal computer", Apple Newsroom, 30 Oct 2023. https://www.apple.com/newsroom/2023/10/apple-unveils-m3-m3-pro-and-m3-max-the-most-advanced-chips-for-a-personal-computer/
- [A9] "Go further with Metal 4 games", Matias Koskela, Apple, WWDC25 session 211, 2025. https://developer.apple.com/videos/play/wwdc2025/211/
- [A10] "Build real-time neural rendering pipelines with Metal", Apple, WWDC26 session 359, 2026 (scope only). https://developer.apple.com/videos/play/wwdc2026/359/
- [A11] Apple developer documentation, read 2026-10-03: `MTLAccelerationStructureUsage` https://developer.apple.com/documentation/metal/mtlaccelerationstructureusage ; `useResource(_:usage:)` https://developer.apple.com/documentation/metal/mtlcomputecommandencoder/useresource(_:usage:) ; `MTLInstanceAccelerationStructureDescriptor` https://developer.apple.com/documentation/metal/mtlinstanceaccelerationstructuredescriptor ; `supportsRaytracing` https://developer.apple.com/documentation/metal/mtldevice/supportsraytracing ; `MTLGPUFamily.apple9` https://developer.apple.com/documentation/metal/mtlgpufamily/apple9 ; `MTLFXTemporalDenoisedScaler` https://developer.apple.com/documentation/metalfx/mtlfxtemporaldenoisedscaler
- [A12] "Metal Feature Set Tables", Apple, revision of 21 May 2026. https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf
- [A13] Apple sample-code pages (descriptions read; code not downloaded): "Accelerating ray tracing using Metal" https://developer.apple.com/documentation/metal/accelerating-ray-tracing-using-metal ; "Rendering reflections in real time using ray tracing" https://developer.apple.com/documentation/metal/rendering-reflections-in-real-time-using-ray-tracing

**Games and graphics research**
- [G1] "'It Just Works': Ray-Traced Reflections in 'Battlefield V'", Johannes Deligiannis and Jan Schmid, EA DICE, NVIDIA GTC 2019 session S91023 (slides read in full). https://developer.download.nvidia.com/video/gputechconf/gtc/2019/presentation/s91023-it-just-works-ray-traced-reflections-in-battlefield-v.pdf
- [G2] "Shiny Pixels and Beyond: Real-Time Raytracing at SEED", Johan Andersson and Colin Barré-Brisebois, EA SEED, GDC 2018 (slides read). https://media.contentapi.ea.com/content/dam/ea/seed/presentations/gdc2018-seed-shiny-pixels-and-beyond-real-time-raytracing-at-seed.pdf
- [G3] "Battlefield 5's ray tracing: the DICE tech interview", Digital Foundry / Eurogamer with Yasin Uludag (DICE), Nov 2018: page blocked; preset numbers from search summaries only (partly verified). https://www.eurogamer.net/digitalfoundry-2018-battlefield-5-rtx-ray-tracing-analysis
- [G4] "Ray tracing comes to Battlefield 5", EA / DICE (Christian Holmquist), 2018. https://www.ea.com/games/battlefield/news/ray-tracing-comes-to-battlefield-5
- [G5] "Control: Multiple Stunning Ray-Traced Effects Raise The Bar For Game Graphics", NVIDIA GeForce news, 2019. https://www.nvidia.com/en-us/geforce/news/control-rtx-ray-tracing-dlss-out-now/
- [G6] "Control Graphics and Performance Guide", NVIDIA, 2019. https://www.nvidia.com/en-us/geforce/guides/control-graphics-and-performance-guide/
- [G7] "Ray Tracing in Control", Juha Sjöholm, Paula Jukarainen, Tatu Aalto, Ray Tracing Gems II ch. 46, Apress 2021 (not read; announcement read). https://developer.nvidia.com/blog/free-ray-tracing-gems-ii-chapter-covers-ray-tracing-in-remedys-control
- [G8] "In-depth technical dive into Metro Exodus PC Enhanced Edition", 4A Games, 6 May 2021. https://www.4a-games.com.mt/4a-dna/in-depth-technical-dive-into-metro-exodus-pc-enhanced-edition
- [G9] "Cyberpunk 2077 Available Now With Stunning Ray-Traced Effects and Performance Accelerating NVIDIA DLSS", NVIDIA, Dec 2020. https://www.nvidia.com/en-au/geforce/news/cyberpunk-2077-rtx-dlss-out-now/
- [G10] "Lumen Global Illumination and Reflections in Unreal Engine" and "Lumen Technical Details", Epic Games documentation (UE 5.x). https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine ; https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine
- [G11] "Lumen: Real-time Global Illumination in Unreal Engine 5", Daniel Wright, Krzysztof Narkowicz, Patrick Kelly, SIGGRAPH 2022 Advances in Real-Time Rendering (not read; file over the fetch limit). https://advances.realtimerendering.com/s2022/SIGGRAPH2022-Advances-Lumen-Wright%20et%20al.pdf
- [G12] HDRP 17.3, Screen Space Reflection override, ray-traced properties, Unity. https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/reference-screen-space-reflection.html ; "Ray-traced reflections" https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/Ray-Traced-Reflections.html
- [G13] "AMD FidelityFX Hybrid Reflections", AMD GPUOpen, SDK 1.0 2023 (page v1.1.4, 2025). https://gpuopen.com/fidelityfx-hybrid-reflections/
- [G14] "NRD: NVIDIA Real-time Denoisers" README, NVIDIA. https://github.com/NVIDIA-RTX/NRD
- [G15] "Spatiotemporal Variance-Guided Filtering: Real-Time Reconstruction for Path-Traced Global Illumination", Christoph Schied et al., NVIDIA / KIT, High Performance Graphics 2017. https://research.nvidia.com/publication/2017-07_spatiotemporal-variance-guided-filtering-real-time-reconstruction-path-traced

**Unity**
- [U1] Unity 6000.3.10f1 offline documentation (`/Applications/Unity/Hub/Editor/6000.3.10f1/Documentation/en/`): ScriptReference `Rendering.RayTracingAccelerationStructure`, `.AddInstance`, `.CullInstances`, `.UpdateInstanceTransform`, `Rendering.CommandBuffer.BuildRayTracingAccelerationStructure`, `SystemInfo-supportsInlineRayTracing`, `SystemInfo-supportsRayTracing`, `SystemInfo-supportsRayTracingShaders`, `Mesh.GetNativeVertexBufferPtr`, `Mesh.GetNativeIndexBufferPtr`, `Mesh.GetVertexBuffer`, `Mesh-vertexBufferTarget`, `SkinnedMeshRenderer.GetVertexBuffer`, `SkinnedMeshRenderer-vertexBufferTarget`, `GraphicsBuffer.GetNativeBufferPtr`, `Texture.GetNativeTexturePtr`, `GL.IssuePluginEvent`, `Rendering.CommandBuffer.IssuePluginEventAndData`; Manual `SL-Pragma-require`, `WhatsNew20231`, `WhatsNewUnity63`, `low-level-native-plugin-rendering-extensions`.
- [U2] Installed packages in the clone: `com.unity.render-pipelines.core@04ab0eefa0c3` `Runtime/RenderGraph/RenderGraph.cs:1268`, `RenderGraphBuilder.cs:146-163`, `RenderGraphResourceAccelerationStructure.cs:11-30`, `Runtime/CommandBuffers/ComputeCommandBuffer.cs:558-600`, `Runtime/UnifiedRayTracing/IRayTracingAccelStruct.cs:8-66`, `CommonStructs.hlsl:28-34`, `FetchGeometry.hlsl:65-116`, `RayTracingContext.cs:101`.
- [U3] `IUnityGraphicsMetal.h`, Unity Native Plugin API, 6000.3.10f1 (`Unity.app/Contents/PluginAPI/`).

**Physics and glass**
- [P1] "Fresnel equations", Wikipedia (read 2026-10-03). https://en.wikipedia.org/wiki/Fresnel_equations
- [P2] "One-way mirror", Wikipedia. https://en.wikipedia.org/wiki/One-way_mirror
- [P3] "Tempered glass", Wikipedia. https://en.wikipedia.org/wiki/Tempered_glass
- [P4] "Float glass", Wikipedia. https://en.wikipedia.org/wiki/Float_glass
- [P5] "Orders of magnitude (luminance)", Wikipedia. https://en.wikipedia.org/wiki/Orders_of_magnitude_(luminance)

**Project files read** (commit `edfbc92` in the real project, read-only; the private clone for package source):
`NativePlugin/FrontRoomsMetalGlassRT.mm`, `NativePlugin/build_frontrooms_metal_glass_rt.sh`,
`Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs`, `FrontRoomsMetalGlassRTRendererFeature.cs`,
`Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`, `Assets/Plugins/macOS/libFrontRoomsMetalGlassRT.dylib.meta`,
`Assets/Settings/FrontRooms_URP_Renderer.asset:95`, `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs` (`BuildInto`,
`Unregister`, `AddRenderer`, window panes `:1043-1052`, troffers `:1181-1215`, fixture tick `:1270-1290`, `:347`),
`FrontRoomsModuleUnits.cs:29, 61, 86`, `FrontRoomsLevelProfile.cs:37-39`, `Assets/Scripts/FrontRooms3DGame.cs:247`,
`Assets/Scripts/Rendering/FrontRoomsLook.cs:20-50`, `Assets/Resources/Rendering/FrontRoomsSurface.shader:1-80, 157-183`,
`Assets/Scripts/FrontRoomsRelayRig.cs:294`, `ProjectSettings/ProjectSettings.asset:54, 543`; glass track's
`proj_glass/Assets/Resources/Rendering/FrontRoomsGlass.shader:1-60, 278-398`; the review image
`images/01_review_trace_output.jpg`.

**Measurements**: `03_bench/` (benchmark source, two logs). Standalone Metal on the M3 Max, macOS 26.6.2, other GPU jobs
running at the same time. No frames were captured for this report.
