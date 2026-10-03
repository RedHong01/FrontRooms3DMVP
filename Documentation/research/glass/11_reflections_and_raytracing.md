# 11 — Reflections and ray tracing: what FrontRooms can actually have (G11)

Date: 2026-10-02, 23:10–23:45. Status: COMPLETE (G11). Read-only for the real project: nothing under
`Frontrooms3D/` changed except this file and `g11_bench/`. The measurements ran in the private clone `proj_glass`.

Task: `Documentation/VISUAL_CHAT_TASKS.md` row G11 (Red: "try whether ray tracing can be done"), plus Red's
WebGL brief (rows WG1–WG4, 23:2x): keep picture quality on WebGL, work out how many high-detail renders can
exist at once, and spend high detail only where the player can see it, without visible seams.

Conventions. `file:line` paths are relative to `Frontrooms3D/` unless they start with `URP/` (the installed
package `Library/PackageCache/com.unity.render-pipelines.universal@37e0d4fc2503/`) or `Core/`
(`com.unity.render-pipelines.core@04ab0eefa0c3/`). "Manual" means the offline Unity 6000.3.10f1 manual in
`/Applications/Unity/Hub/Editor/6000.3.10f1/Documentation/en/`, read for this report. **MEASURED** = from the
bench in §2.0 (this Mac, editor). **ESTIMATE** = arithmetic or judgement. **UNVERIFIED** = not confirmed.

---

## 0. Short answer (for Red)

1. **Ray-traced reflections are not possible for FrontRooms as built.** URP has none. HDRP has them, but
   only on Windows with DirectX 12 and an RTX 20+/RX 6000+ class card. On your M3 Max, Unity 6000.3.10f1
   reports no ray-tracing support at all (measured: `supportsRayTracing`, `supportsRayTracingShaders`,
   `supportsInlineRayTracing` all False on Metal). WebGL and WebGPU have no ray tracing, and Unity's software
   ray-tracing library is excluded from Web builds. Moving to HDRP would cost the WebGL build and 3–5 weeks of
   rewrites, and on your Mac it would still give you SSR, not ray tracing (§1, §2.6).
2. **What ray tracing would have bought, we can get piece by piece:**
   - the room reflected with correct parallax: **zone cubes + box-projected room probes** (G6, G7). These cost
     no rendering, and the cubes work on the Web too;
   - the Relay appearing behind you in the window you are breaking: **a planar reflection camera for that one
     pane, only while you hold it**. A full planar at 12 m costs 12–20% of a frame (desktop). A **Relay-only**
     planar costs about 7%, the fixed cost of one extra camera, and is the one live reflection the Web gets
     (§2.4, measured);
   - glossy floors: **screen-space reflections when the project moves to Unity 6.7**, where Unity ships URP SSR
     (Unity staff: "No plans to backport"). SSR does almost nothing for a window seen head-on, because the reflected rays
     leave the screen toward the camera (§2.3).
3. **What not to do:** re-render realtime probes in normal play (+47 ms per frame unsliced; a one-shot refresh
   is a 40–70 ms hitch, or ~8 frames of up to +20–35 ms when sliced; §2.5), write our own SSR on 6.3, or leave a
   full planar running.
4. **WebGL (your brief):** the only reflection rendered live on the Web is the Relay in the held window.
   Everything else is a pre-captured cube, box-projected only in rooms the player can see, with
   lights + probes in view ≤ 32 so URP's Forward+ tiles stay fine. Probes switch only off-screen, nearest
   first with hysteresis, so nothing pops (§3).
5. **Tiers:** Web = zone cubes (+ optional PVS probes) + Relay-only overlay. High = cubes + room probes + a
   planar for the held pane. Cinematic = High at full quality + realtime re-capture at hero windows + floor
   SSR/planar. The full table is in §4.1.

All costs are from an editor bench on your Mac (§2.0). They are ratios, not player or browser timings.

---

## 1. Can FrontRooms have ray-traced reflections?

**No, not as a feature of this project. There are three separate blockers, and any one of them is enough.**

### 1.1 URP has no ray-traced anything

- The Unity 6.3 feature table lists, for URP: Ray-traced Reflections **No**, Ray-traced GI **No**, Ray-traced
  Shadows **No**, Ray-traced AO **No**, Ray-traced Recursive Rendering **No**; and also Screen Space Reflections
  **No**, Planar Reflections **No**, Screen Space Refractions **No**. HDRP has all of them
  (Manual `render-pipelines-feature-comparison.html`, "Raytracing" and "Realtime Global Illumination" tables).
- The installed URP 17.3.0 confirms it: `URP/Runtime/RendererFeatures/` holds Decal, FullScreenPass,
  OnTilePostProcess, RenderObjects, SSAO, ScreenSpaceShadows and SurfaceCacheGI. There is no reflection feature.
- The one ray-tracing-based thing inside URP 17.3 is **Surface Cache GI**, a diffuse-GI preview. Its source is
  compiled only when the scripting define `SURFACE_CACHE` is set
  (`URP/Runtime/RendererFeatures/SurfaceCacheGI/SurfaceCacheGlobalIlluminationRendererFeature.cs:1`), and it is
  built from compute shaders (`:30-43`). It gives bounce light, not reflections. Unity's thread on it says it
  targets 6.7 LTS (cited in `interaction_audit/03_rendering_quality.md` §8; not re-read).

### 1.2 HDRP ray tracing does not run on Red's Mac, and never in a browser

- HDRP 17.3: "HDRP only supports ray tracing using the DirectX 12 API, so ray tracing only works in the Unity
  Editor or the Windows Unity Player when they render with DirectX 12", plus "specific console platforms"
  (https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/Ray-Tracing-Getting-Started.html).
- Hardware: NVIDIA RTX 20/30-series, Quadro RTX, AMD RX 6000 / Radeon Pro W6000, or NVIDIA's fallback on some
  GTX 10/16 cards; Windows 1809 or later
  (https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/raytracing-requirements.html).
  macOS, Metal and Apple Silicon are not mentioned on either page.
- **MEASURED on Red's machine.** Unity 6000.3.10f1 on the Apple M3 Max with Metal reports
  `SystemInfo.supportsRayTracing = False`, `supportsRayTracingShaders = False`,
  `supportsInlineRayTracing = False`, `supportsComputeShaders = True` (bench log, §2.0; same in edit mode and
  play mode). The M3 GPU has ray-tracing hardware (Apple's M3 launch material; not re-read for this report), but
  Unity 6.3 does not expose it on Metal. So even a full HDRP
  migration would give Red SSR on his Mac, not ray tracing. Ray-traced frames would need a Windows DX12 PC with
  one of the GPUs above.
- HDRP ray tracing is also incompatible with MSAA, volumetric fog, vertex animation, tessellation, and
  `Graphics.DrawMesh`/`RenderMesh`, and a mesh whose material is not tagged for HDRP is left out of the
  acceleration structure (same Getting Started page, "Limitations" and "Ray tracing and Meshes"). Every
  `FrontRooms/Surface` material would have to be rebuilt first (§2.6).
- HDRP itself "doesn't support OpenGL or OpenGL ES devices" and needs compute shaders; its platform list has no
  Web entry (https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/System-Requirements.html).
  WebGL2 is OpenGL ES 3.0 class (Manual `WebGL2.html`).

### 1.3 The web has no ray tracing

- WebGL2 "almost matches with the OpenGL ES 3.0 functionality" (Manual `WebGL2.html`): no compute, no ray
  tracing.
- WebGPU in Unity 6.3 is "experimental and not supported by all browsers and devices"; the features it adds
  over WebGL2 are compute shaders, indirect rendering, GPU skinning and VFX Graph. Ray tracing is not on the
  list (Manual `WebGPU.html`, `WebGPU-features.html`).
- The WebGPU standard itself has no ray-tracing API. On the W3C GPU list in 2018, Kai Ninomiya (Google) wrote
  that an extension would be looked at only once WebGPU and the native ray-tracing APIs had matured
  (https://lists.w3.org/Archives/Public/public-gpu/2018Dec/0003.html). Whether anything has been standardised
  since is UNVERIFIED; nothing in Unity's 6.3 WebGPU pages uses it.
- Unity's software ray-tracing library is explicitly excluded from Web builds:
  `Core/Runtime/UnifiedRayTracing/Unity.UnifiedRayTracing.Runtime.asmdef` has `"excludePlatforms": ["WebGL"]`.

### 1.4 The one "ray tracing" that does run on the Mac: software rays in compute (not recommended)

- Unity 6.3 added the **UnifiedRayTracing API**, which "enables ray tracing workloads on GPUs without dedicated
  hardware acceleration ... via a compute shader-based fallback" (Manual `WhatsNewUnity63.html`). It picks the
  hardware backend when `SystemInfo.supportsRayTracing` is true, otherwise the compute backend
  (`Core/Runtime/UnifiedRayTracing/RayTracingContext.cs:68, 98-104`).
- **MEASURED:** on this Mac, `IsBackendSupported(Hardware) = False`, `IsBackendSupported(Compute) = True`.
- So Red could, in principle, trace reflection rays on the Mac in a custom URP render-graph pass. But the
  library only finds hits; it does not shade them. We would have to upload the maze to a BVH on every chunk
  build, give the hit shader access to every `FrontRooms/Surface` material's textures and the lamp list, and
  denoise the result. Unity's own URP SSR author says evaluating materials during ray tracing "might be more
  tricky to achieve in URP, especially in the presence of custom shaders"
  (https://discussions.unity.com/t/preview-of-screen-space-reflections-for-urp/1721494, reply of 2026-07-02).
  This is a research project of several weeks for a desktop-only result, and it is impossible on WebGL. Not
  recommended this semester.

### 1.5 What Red should take away

"Ray tracing" in FrontRooms would mean: switch to HDRP, lose the WebGL build, rewrite the surface shader, post
stack and every runtime material, and then see the ray-traced result only on a Windows PC with an RTX/RX 6000
card, not on the Mac he works on. The things that make the glass shots read as AAA (§4 of the audit: timing,
debris, a real glass material, something to reflect) do not need ray tracing. What ray tracing would add over
the plan below is mostly correct reflections of things behind the player. §2.4 gets that one effect, the
Relay reflected in the window, for a small fraction of the cost.

---

## 2. The alternatives, for this game's glass, VCT and metal

### 2.0 How the costs were measured

- **Bench:** a G11-only editor script that ran in the private clone `proj_glass` (removed from the clone after
  the runs so it cannot be promoted; source kept as `g11_bench/FrontRoomsG11ReflectionBench.cs.txt` next to this
  report, entry points `RunBatch`, `RunBatchProbe`, `RunBatchOverlay`). It plays `Assets/Scenes/FrontRooms3D.unity` with
  the audit harness's start (`Random.InitState(4242)` before the title start, run seed 516574485), stands
  1.5 m from the first Level 0 window (window (282,206)→(282,207), camera-side zone Level0/Low, pane centre
  (271.50, 1.18, 45.00)) and times each option as **Stopwatch around the render(s) + a 1-pixel ReadPixels that
  waits for the GPU**, median of 20 samples after 4 warm-ups. The probe pass instead measures whole-frame
  intervals (§2.5). Logs: `g11_bench/bench_log_run1.txt` (planar, cube), `bench_log_run2_probe.txt`
  (realtime probes), `bench_log_run4_overlay.txt` (fixed camera cost, Relay overlay, far sweep). Run 3 is
  not used: it did not find the Relay rig, which is inactive until released.
- **What the numbers are:** editor play mode on an M3 Max, Metal, 1920×1080, 4× MSAA, quality level High
  (`realtimeReflectionProbes` on). The editor adds a lot of CPU overhead: the game camera alone measured
  **44.2 ms median (CPU part 33.5 ms)** at this spot, and 55.0 ms when re-measured at the end of the same run,
  so the absolute values are inflated and noisy (±20%). **Read them as ratios to the game camera in the same
  run.** At this spot 655 renderers are in the camera frustum and 111 lights are enabled (37 whose range reaches
  the camera). None of this is a player build or a browser.
- **The pattern that matters for WebGL:** 60–75% of every measured render is CPU time (culling, draw
  submission, URP's render-graph setup: 33.5 of 44.2 ms for the game camera, 5.5 of 9.0 ms for a 12 m planar),
  and it scales with how many renderers the extra view sees, not with its resolution. Unity says WebGL draw-call dispatch on the CPU "is slower than in native OpenGL" and that Web
  C# is single-threaded (Manual `webgl-performance.html`), so on the Web an extra camera costs at least as large
  a share of the frame as in this table (ESTIMATE; the WebGL BUDGETS agent measures browsers,
  `research/webgl/03_measured_budgets.md`).

### 2.1 Option 1 — per-zone custom cubemaps (G6)

| | |
|---|---|
| What | One captured HDR cube per zone type (lit Level 0, lit Office, Tall, dead-lamp) set as the default reflection; `SetZoneReflection` crossfades. |
| Glass | Gives the pane its first real reflection: a lit room, at infinity. On a head-on pane the reflection "slides" with the camera because it has no parallax. |
| VCT / metal | The biggest gain per cost: metal stops reading as plastic; floors get a sheen with lamp-coloured highlights. |
| Runtime cost | One bound cube, no rendering. URP binds `ReflectionProbe.defaultTexture` as the global environment cube when it sets up a camera (`URP/Runtime/UniversalRenderPipeline.cs:2201`). The 0.5 s fade can blend two cubes into a cube render texture with `ReflectionProbe.BlendCubemap(src, dst, blend, target)` (Manual `ScriptReference/ReflectionProbe.BlendCubemap.html`), six small blits per frame only while fading. |
| Memory | ESTIMATE, uncompressed RGBA half with mips: 128 px ≈ 1.0 MB, 256 px ≈ 4.2 MB per cube. Four zones at 128 px ≈ 4 MB. |
| Artifacts | No parallax; same content everywhere in a zone; a frozen copy of the wallpaper print (the wallpaper chat's caveat: keep intensity modest on glossy, wall-facing surfaces until the print is captured per state); every glossy surface changes at once on a zone crossing, so crossfade. |
| WebGL | Yes, all tiers. This is the Web tier's main reflection. |

### 2.2 Option 2 — per-room box-projected probes with blending (G7)

| | |
|---|---|
| What | At chunk build, one Custom `ReflectionProbe` per room (or per window cell) sized to the room box, box projection on, using the zone cube from 2.1. |
| Glass | Big improvement over 2.1 for a pane in a box room: the reflected walls, ceiling grid and troffer rows line up and move with correct parallax as the player walks past. Content is still the generic zone room, not the actual one; no props, no Relay. |
| VCT / metal | Floors and wall-mounted metal get reflections that stay put on the right wall. |
| Runtime cost | No rendering. Per pixel: the Forward+ probe loop (box intersection + 1–2 cube samples per probe in the tile). Probes are Forward+ items: `itemsPerTile = localLights + reflectionProbeCount` and `wordsPerTile = (itemsPerTile + 31) / 32` (`URP/Runtime/ForwardLights.cs:237-246`), capped at `min(maxVisibleAdditionalLights, 64)` visible probes (`URP/Runtime/UniversalRenderPipeline.cs:172`). Needs blending and box projection on (`Assets/Settings/FrontRooms_URP.asset:54-55`, both 0 today) and the two `#define`s in `FrontRooms/Surface` (audit §4.3). Atlas memory: measure. |
| WebGL detail | WebGL2 is a GLES3 device, so `maxVisibleAdditionalLights` is the mobile value, 32 (`UniversalRenderPipeline.cs:139-152`), probes are capped at 32, and `maxTileWords` is 4096 words (`:171`). While lights + probes in view stay at 32 or fewer, each tile needs one word; at 33–64 it needs two and URP doubles the tile size until it fits (`ForwardLights.cs:248-254`): at 1280×720 that is 16 px tiles → 32 px tiles (ESTIMATE from that loop), so every pixel loops over more lights. **Web budget: visible lights + visible probes ≤ 32.** |
| Artifacts | Box mismatch where a room is not a box (L-shaped merged cells, arches); seams where two probes meet if blend distance is 0; a probe switched on or off in view shifts the reflection (no content change, since both sources are the same zone cube). |
| WebGL | Optional on the Web tier, only for rooms in the potentially-visible set and only if the browser test passes (§3). |

### 2.3 Option 3 — a custom screen-space-reflection pass in URP 17.3

**Who has done it.**
- **Unity itself, but not for 6.3.** Unity is shipping URP SSR in **Unity 6.7**: preview thread opened
  2026-05-29, 6000.7.0b1 released with SSR improvements on 2026-09-18, and "No plans to backport" (Unity staff,
  2026-09-01) (https://discussions.unity.com/t/preview-of-screen-space-reflections-for-urp/1721494). It marches
  rays against the depth buffer, reads the **previous frame's colour** (a reply quoting the 17.6 source names
  `BeforeTransparentsColorHistory` / `RawColorHistory`), falls back to probes off-screen, needs a DepthNormals
  pass that writes smoothness into alpha, and does not support Unlit Shader Graph. On transparency, Unity's
  developer: it is "a single pass screenspace technique ... you can only have 1 reflection per pixel"; a window
  either steals the reflection of what is behind it, or writes depth and hides the reflections behind it, or
  uses probes (reply of 2026-07-07). MSAA compatibility only arrived in 6.7 b1. WebGL support: not stated
  (UNVERIFIED).
- **jiaozi158/UnitySSReflectionURP** (MIT, open source): URP 14+, any rendering path, "Multiple Render Targets
  support (at least OpenGL ES 3.0 or equivalent)", extra steps for OpenGL; in Forward it renders its own GBuffer
  pass, which URP's shaders exclude on OpenGL, so they must be modified; "Transparent objects are ignored by
  reflections" (https://github.com/jiaozi158/UnitySSReflectionURP README;
  https://github.com/jiaozi158/UnitySSPathTracingURP/blob/main/Documentation/ForwardPathSupport.md).
- **Kronnect Shiny SSR 2** (Asset Store, $25.99 on sale when read): the store page lists Built-in and URP, not
  HDRP. A search snippet says it supports WebGL 2 and Render Graph; the store page I could read does not say so
  (UNVERIFIED; https://assetstore.unity.com/packages/slug/188638).

**What it would take here.**
- The inputs mostly exist on desktop: the depth texture is on (`FrontRooms_URP.asset:22`) and SSAO already uses
  the DepthNormals source (`Assets/Settings/FrontRooms_URP_Renderer.asset:74`, `Source: 1` =
  `DepthNormals`, `URP/Runtime/RendererFeatures/ScreenSpaceAmbientOcclusion.cs:28-32`), so a normals texture
  is drawn every frame. URP 17.3 keeps a previous-frame colour history for cameras that request it
  (`URP/Runtime/UniversalRenderer.cs:1652-1692`; Manual `urp/render-graph-add-textures-to-camera-history.html`).
- What is missing: smoothness. `FrontRooms/Surface`'s DepthNormals pass uses URP's plain
  `DepthNormalsPass.hlsl` (`Assets/Resources/Rendering/FrontRoomsSurface.shader:302-315`), which writes
  normals only. To blend SSR into lighting properly, Surface must either write smoothness into that alpha or
  sample the SSR texture in its forward pass. Both are edits to a shader another workflow is changing now.
- The pass itself must be a Render Graph pass (URP 17.3 has no compatibility mode here, audit §5.1).
- Cost: a half-resolution ray march plus a blur, roughly 0.5–1.5 ms at 1080p on a mid desktop GPU (ESTIMATE,
  not measured; no implementation exists to bench). Effort: L (1–2 weeks including the Surface changes,
  history reprojection and tuning).

**Artifacts on this game's surfaces.**
- **Window glass viewed head-on: SSR finds almost nothing.** A ray reflected off a pane you face goes back
  toward you, out of the screen, so it falls back to the probe. At the audit's oblique frames (about 50°) the
  rays leave the side of the screen. In a first-person game, SSR is the wrong tool for vertical windows.
- **VCT, damp carpet, polished floors:** the classic good case. Rays go up and forward into walls and troffers
  that are on screen. Holes appear at screen edges and behind pillars; the troffer streaks fade out toward the
  bottom of the screen.
- **Small metal (door hardware, rails, chrome):** curved, small, rough: little visible gain over probes.
- **Glass as a transparent:** per Unity's answer above, glass either steals or hides reflections. Keep SSR off
  the pane and let the pane use probe + planar.

**WebGL2 viability: no, in practice.** Nothing in SSR needs compute, so a fragment-shader version is
possible on WebGL2. But it needs a full DepthNormals geometry pass every frame (a second pass over every
visible renderer, i.e. roughly double the draw calls; whether the Web tier keeps SSAO's DepthNormals pass is
the WebGL plan's call), a previous-frame colour copy, a float target and new variants in Surface. On a platform
whose limit is CPU draw dispatch, that is the most expensive kind of feature. **Recommendation:** don't write
our own. Plan floor SSR for when the project moves to Unity 6.7 (§4), desktop tiers only.

### 2.4 Option 4 — a planar reflection for the ONE window the player looks at or holds

**How:** a second camera mirrored about the pane plane, with an oblique near plane at the pane so nothing
beyond the glass is drawn, rendered into a texture that the glass shader samples in screen space (the mirrored
image is flipped in U). This is what Unity's BoatAttack sample does for water (`RenderPipelineManager
.beginCameraRendering`, `GL.invertCulling`, resolution Full/Half/Third/Quarter, optional shadows, fog off,
`maximumLODLevel = 1`, LOD bias halved) — https://github.com/Unity-Technologies/BoatAttack/blob/master/Packages/com.verasl.water-system/Scripts/Rendering/PlanarReflections.cs.
In URP 17.3, `UniversalRenderPipeline.RenderSingleCamera` (which BoatAttack calls) is obsolete; the
replacement is `RenderPipeline.SubmitRenderRequest` with `UniversalRenderPipeline.SingleCameraRequest`
(`URP/Runtime/UniversalRenderPipeline.cs:683`, request handling `:550-620`).

**Why it is the right tool for the held window:** it is exact for a flat pane, it has the parallax the cube
lacks, and it is the only cheap option that can show **the Relay behind the player in the glass**, which is a
horror beat, not just fidelity.

**MEASURED, run 1 (game camera = 44.2 ms in the same run; far plane = the game camera's 46 m,
`map.SightDistance`, set in `FrontRooms3DGame.cs:727-729`):**

| Planar camera config (window 1.5 m away) | Planar alone | Game camera + planar | Extra over game camera |
|---|---|---|---|
| Full 1920×1080, shadows on, far 46 m | 37.3 ms | 92.0 ms | +47.8 ms (+108%) |
| Half 960×540, shadows on, far 46 m | 38.7 ms | 74.2 ms | +30.0 ms (+68%) |
| Half 960×540, shadows off, far 46 m | 26.7 ms | 71.8 ms | +27.6 ms (+62%) |
| Quarter 480×270, shadows off, far 46 m | 24.3 ms | 74.1 ms | +29.9 ms (+68%) |
| **Quarter 480×270, shadows off, far 12 m** | **9.0 ms** | **55.5 ms** | **+11.3 ms (+26%)** |

**MEASURED, run 4 (far-clip sweep, quarter res, shadows off; game camera = 36.7 ms; renderers counted in a
normal frustum of that far distance on the player's side of the pane):**

| Planar far plane | 6 m | 9 m | 12 m | 20 m | 40 m | 80 m |
|---|---|---|---|---|---|---|
| Renderers in the mirrored view | 57 | 67 | 102 | 178 | 617 | 1,511 |
| Planar alone | 3.9 ms | 4.0 ms | 4.3 ms | 7.0 ms | 17.2 ms | 34.1 ms |
| Share of the game camera | 11% | 11% | 12% | 19% | 47% | 93% |

- The cost follows the number of renderers the mirrored view sees (about 20 µs each in the editor, on top of
  a fixed ~2.5 ms per camera, below), not its resolution. **Draw distance is the main lever, then shadows
  (turning them off cut the half-res planar from 38.7 to 26.7 ms in run 1); resolution below full barely
  matters.** The mirrored view looks back across the player's room and through every opening behind it, so with
  the game's 46 m far plane it sees about as many renderers as the game camera (617 at 40 m, against 655 in the
  game camera's frustum at this spot), which is why it then costs about a second frame.
- Run-to-run noise is large: the same 12 m config measured 9.0 ms (20% of the frame) in run 1 and 4.3 ms (12%)
  in run 4. Use **12–20% of a frame** for a 12 m planar.
- What the mirrored camera sees from this window: `g11_bench/01_planar_half_view_mirrored.jpg` (left-right
  mirrored; post-processing off, so it reads brighter than the game frame `00_main_view.jpg`).
- The bench builds the mirror camera with a proper rotation (cost-identical); production should use the
  reflection matrix with `GL.invertCulling` as BoatAttack does, so the texture lines up with screen UVs.

**Recursion.** A window reflecting another window: the reflected view must not render its own planar (skip
reflection cameras in the callback, as BoatAttack does with `CameraType.Reflection`), so other panes inside the
reflection fall back to their probe. One level is enough; nobody can see the second bounce.

**Time slicing.** While the player holds the glass (1 s, audit §3.5) the camera barely moves. The planar can
render at hold start and then every 2nd–4th frame (15–30 Hz), or only when the Relay moves. While walking past
windows, the pane uses probes (2.1/2.2) and no planar renders at all.

**WebGL:** a full planar adds a second pass of draw calls on the platform where draw calls are the limit.
Even at 12 m (57–102 extra renderers here) it is 12–20% of an editor frame, and probably more in a browser
(§2.0). Not for normal play. The Relay-only variant (§2.4b) is the Web candidate.

#### 2.4b The Relay-only overlay: the room from the probe, the Relay from a tiny planar

**Idea.** The room behind the player does not change during a hold, so the probe (2.1/2.2) can supply it. The
only thing that moves is the Relay. Render a planar camera whose culling mask contains **only the Relay**,
cleared to transparent, and let the glass shader lay it over the probe reflection.

**MEASURED, run 4** (Relay placed 2.4 m behind the player, its 16 renderers moved to a spare layer for the
test; game camera 36.7 ms):

| Extra camera | Renderers drawn | Alone |
|---|---|---|
| Empty camera (culling mask = an unused layer): URP's fixed per-camera cost | 0 | 2.55 ms (CPU 1.36) ≈ 7% of the frame |
| **Relay-only planar, 480×270** | 16 | **2.51 ms** ≈ 7% |
| Relay-only planar, 960×540 | 16 | 2.74 ms ≈ 7% |
| Full planar, quarter, far 12 m (same run) | 102 | 4.29 ms ≈ 12% |

- The Relay-only planar costs the same as an empty camera: the fixed cost of a URP camera (culling, render
  graph setup), plus 16 draws. ("Game camera + planar" deltas in this run were within ±5 ms noise and are not
  used.)
- Images: `g11_bench/02_relay_only_planar_half_mirrored.jpg` (what the overlay holds; the rig is still shaded, but
  whether the lamps reach it through a Relay-only culling mask or only ambient does is UNVERIFIED) and `03_full_planar_with_relay_half_mirrored.jpg` (the full
  planar with the Relay in it). The rig is the current, known-broken one (memory: head at 2.3–3.1 m); the
  images only show what the camera sees.
- **What it needs:** a "Relay" layer (a `ProjectSettings/TagManager.asset` change; today every renderer is on
  `Default`, `TagManager.asset` layers 6–31 are empty), the transparent clear, and the glass shader's overlay
  input (§4.2). The Relay's shadow and the lamps' light on it stay as in the main view.
- **Limit:** anything else that moves behind the player (a door swinging, a thrown key) is not in the overlay.
  The probe shows it in its old state.

### 2.5 Option 5 — realtime probe re-render when the hold starts

**How:** when a hold (or an approach within ~3 m facing a window) starts, call `RenderProbe()` once on that
room's probe (`refreshMode = ViaScripting`), so the box-projected reflection shows the actual room (its props,
its dead or live lamps) instead of the generic zone cube.

**Unity's own description:** six faces rendered by a camera at the probe, then the mip chain blurred; Time
Slicing "All Faces at Once" finishes in 9 frames, "Individual Faces" in 14, "No Time Slicing" in one frame
"but the processing cost can be prohibitive"; real-time cubes are not compressed (Manual
`RefProbePerformance.html`). Real-time probes are on at quality levels High, Very High and Ultra only
(`ProjectSettings/QualitySettings.asset:28, 81, 134` = 0; `:187, 240, 293` = 1). WebGL's default quality level
is 3, High (`QualitySettings.asset:339`).

**MEASURED (run 2, whole-frame intervals; game camera only = 39.0 ms median, 45.7 ms at the end of the run):**

| Probe refresh | Frames until `IsFinishedRendering` | Cost |
|---|---|---|
| Every frame, No Time Slicing, 128 px | 1 | +47.5 ms every frame (more than doubles the frame) |
| Every frame, All Faces at Once | — | +11.6 ms median, spikes to 97.7 ms |
| Every frame, Individual Faces | — | +6.0 ms median, spikes to 57.9 ms |
| **One-shot**, No Time Slicing, 128 or 256 px | 1 | one frame of 77–108 ms: a **hitch of +40–70 ms** |
| One-shot, All Faces at Once, 128/256 px | 3 | worst frame 107–143 ms (no better than no slicing here) |
| **One-shot, Individual Faces, 128/256 px** | 8 | worst frame 66–77 ms (**+20–35 ms**), roughly 250 ms of extra work spread over the refresh |

- Resolution (128 vs 256) made no clear difference, and `shadowDistance = 0` on the probe did not reduce the
  one-shot hitch (UNVERIFIED why; possibly URP ignores it). The six-face render itself, done with a camera,
  measured 70.7 ms with shadows and 34.5 ms without (run 1, 128 px; one face 10.2 ms without shadows).
- `IsFinishedRendering` became true after 3 and 8 frames, not the documented 9 and 14. Whether the mip blur
  finishes later than the flag is UNVERIFIED.
- **Verdict:** Cinematic only, as a one-shot Individual Faces refresh on **approach** to a hero window (not at
  hold start, so it is finished before the shot starts), with the probe's `cullingMask` excluding small props.
  On High only if a player-build test shows the ~8-frame refresh is invisible. Not on the Web tier: frames
  50–90% longer for ~8 frames is a visible stutter on the platform with the least headroom.

### 2.6 Option 6 — migrate to HDRP

**What it would give:** SSR and transparent SSR, planar reflection probes, probe proxy volumes, SSGI (feature
table), plus volumetric fog and contact shadows (audit 03 §4). On a Windows DX12 PC with an RTX/RX 6000 card:
ray-traced reflections, GI, shadows, AO, path tracing.

**What breaks or must be redone (inventory of the clone, 2026-10-02 23:10 snapshot):**

| Area | Today | In HDRP |
|---|---|---|
| WebGL build | works (URP cloud build of 22:15) | **lost**: HDRP has no OpenGL ES / Web support |
| Ray tracing on Red's Mac | — | **still none**: HDRP RT is DX12-only and Metal reports no RT support (§1.2) |
| `FrontRooms/Surface` (320 lines, 4 URP passes, world-projected UVs, wear) | `Assets/Resources/Rendering/FrontRoomsSurface.shader` | rewrite as an HDRP Shader Graph or HDRP-format shader; 83 of 86 `Resources/Surfaces` materials use it (audit F4) |
| `VolumetricBeam.shader` (84 lines) | URP includes | replace with HDRP local volumetric fog |
| Runtime materials | 7 × `"Universal Render Pipeline/Lit"` + 1 × `"Simple Lit"` created in code in `FrontRoomsMapWorld.cs` (map chat), `FrontRoomsSurfaces.cs`, `FrontRoomsMazePreview.cs`, `FrontRoomsStreamVerification.cs`, `FrontRoomsRenderSetup.cs` | `HDRP/Lit` with different keywords and transparent setup |
| Post stack | URP `WhiteBalance, ColorAdjustments, LiftGammaGain, ShadowsMidtonesHighlights, FilmGrain, ChromaticAberration, Tonemapping (ACES), Bloom, Vignette, LensDistortion` (`FrontRoomsRenderSetup.cs:164-232`), camera data in `FrontRoomsPostStack.cs:70-72`, SSAO renderer feature (`:112`) | HDRP namespaces and parameters; exposure must be authored |
| Lights | intensities set in code in 4 scripts (7 assignments: `FrontRooms3DGame.cs`, `FrontRoomsRoomStream.cs`, `FrontRoomsMazePreview.cs`, `FrontRoomsMapWorld.cs`) | physical units; every lamp retuned |
| Tools | RenderSetup (41 KB), lookdev captures, kit importer slot materials (`Prop_*`), audit harness | rewrite |
| AA | 4× MSAA | HDRP RT is incompatible with MSAA; TAA/DLSS instead, which ghosts on the shots Red named (audit §5.3) |

**Effort (ESTIMATE):** 3–5 weeks for one person before the frame looks as good as today, during which the map,
sound and wallpaper chats keep changing the same files. **Benefit on Red's Mac:** SSR and better volumetrics;
no ray tracing. **Verdict: no.** Revisit only if the course target becomes "Windows desktop only" and a DX12
RTX machine is available for captures.

---

## 3. WebGL: how many reflection renders at once, and only where the player looks

Red's brief for the Web build (VISUAL_CHAT_TASKS §1b) applies to reflections like this. Red's hard rule
(2026-10-02, quoted in `research/webgl/01_platform_and_build.md`) is that WebGL changes apply only to WebGL
builds; everything here is scoped to the Web quality level / URP asset / `#if UNITY_WEBGL`.

### 3.1 The reflection budget per Web frame

| Kind of reflection "render" | How many at once on Web | Why |
|---|---|---|
| Zone cube (default reflection) | 1 bound, 2 during a 0.5 s crossfade | no render cost; ~1 MB each at 128 px (ESTIMATE) |
| Box-projected Custom probes sharing the zone cube | 0 by default; up to **N = 32 − visible lights** (e.g. 8 if the Web tier keeps 24 lights), only for rooms in the potentially-visible set | no render cost; each one is a Forward+ item, and above 32 items per view URP doubles the tile size (§2.2) |
| Full planar / realtime probe refresh / SSR | **0** | each is a second pass over hundreds of renderers on a CPU-bound, single-threaded platform (§2.0, §2.4, §2.5) |
| Relay-only planar on the held pane | **at most 1**, only during a hold, quarter res, optionally every 2nd frame | 16 draws plus the fixed cost of a URP camera, ≈ 7% of an editor frame (§2.4b); the browser share is UNVERIFIED and must pass the WebGL plan's frame-time gate |

Put plainly: on the Web, the only reflection that is rendered live is the Relay in the one window the player
is holding. Everything else is a pre-captured cube, placed (box-projected) only in rooms the player can see.

### 3.2 Visible-only, without seams

- **Probes switch only off-screen.** A probe is turned on when its room enters the potentially-visible set
  (the WebGL visibility plan, `research/webgl/02_visibility_portals.md`) and off when it leaves, never while its
  box is inside the view frustum. Because the probe and the default reflection hold the same zone cube, a late
  switch would only change parallax, not content, but the rule avoids even that.
- **Nearest first, with hysteresis.** Rank PVS rooms by distance along the portal path; keep a probe until it
  falls 2 ranks below the cut, so a player standing on a boundary does not flip it every frame.
- **Zone crossings crossfade** over 0.5 s (G6). Panes that sit on a zone border take the cube of the side the
  camera is on, so the reflected room matches the room behind the player.
- **The Relay-only planar starts before it is visible:** start rendering it on the first frame of the hold (the
  Relay is not in the glass yet in most cases) and fade its alpha in over 0.2 s, so it never pops in mid-shot.

---

## 4. Recommended stack per tier

### 4.1 The stack

| Surface / feature | Web (WebGL2; WebGL-only settings) | High (Mac / Windows desktop) | Cinematic (captures) |
|---|---|---|---|
| Default reflection | zone cube, 128 px, crossfade 0.5 s (G6) | zone cube, 256 px (G6) | same as High |
| Room probes (box-projected, Custom, sharing the zone cube) | off by default; at most 32 − visible lights, PVS rooms only, switched off-screen, after a browser test (§3) | nearest 8–12 rooms, 64–128 px (G7) | every built room within 20 m |
| Re-capture of the actual room | no | no by default (the one-shot refresh is a visible hitch, §2.5) | one-shot, Individual Faces, on approach to a hero window; probe `cullingMask` without small props |
| The held window (glass) | G1 glass shader + probe + **Relay-only planar overlay** during the hold | G1 + probe + **full planar** during the hold: quarter→half res, shadows off, far 12 m, 15–30 Hz | full planar at half/full res with shadows, every frame, for the held window and any window a scripted shot frames |
| Floors (VCT, damp carpet, gloss paint) | probe | probe; URP SSR after a move to Unity 6.7 | 6.7 SSR, or one planar for the floor plane (every map floor slab sits at the cell height, `FrontRoomsMapWorld.cs:723` in the clone), far ≤ 20 m |
| Metal (hardware, rails, chrome) | probe | probe | probe |
| Ray tracing | none possible | none possible on the Mac; Windows-DX12-only via HDRP (rejected, §2.6) | none in Unity. For stills only, the same Blender kit could be rendered in Cycles outside the game (whether Cycles uses the M3's ray-tracing hardware is UNVERIFIED) |
| Reflection cost, held window (from the bench, editor ratios) | ≈ 7% during holds only | 12–20% during holds only | not budgeted |
| Reflection cost, normal play | ~0 render cost; per-pixel probe cost | ~0 render cost; per-pixel probe cost; atlas memory (measure) | — |

### 4.2 What the glass shader (G1) needs from this report

Proposed inputs, so G1 can be written once for all tiers without new keywords (WebGL variant budget):
- `_FR_PlanarTex` (global texture) and `_FR_PlanarWeight` (per material, default 0). The held pane gets a
  second material, e.g. `Glass_Window_Held` (same shader, weight 1), swapped in for the hold, so no
  `MaterialPropertyBlock` breaks SRP batching on the other panes.
- `_FR_PlanarMode` (global float): 0 = full planar replaces the probe reflection, 1 = overlay (Relay-only,
  composite with the texture's alpha over the probe reflection). A uniform branch, not a keyword.
- The planar texture is sampled in screen space with the reflection-matrix camera (BoatAttack's construction),
  distorted by the pane's normal map and blurred by the smudge roughness (sample a lower mip).
- Crack stages (`_Crack`) should also break the planar image: each crack facet offsets the screen UV slightly,
  which is where a planar beats a cube visually.

### 4.3 Contracts and rows this creates (proposals; nothing is filed)

- **Map chat:** an event or query for "hold started / ended on pane X" with the pane's renderer and transform,
  so the visual side can swap the material and run the planar only then. (G9 already plans `Hold()` with the
  hit point and `GlassCracked`.)
- **Relay layer:** a dedicated layer for the Relay rig's renderers (TagManager change; ask Red). The map chat
  must keep the rig on it when it rebuilds or swaps the rig (the squeezed-giant rig swap).
- **New visual rows (suggested):** G13 planar for the held pane (High/Cinematic), G14 Relay-only overlay (all
  tiers), G15 floor SSR when the project moves to Unity 6.7 (desktop only), G16 Cinematic one-shot probe
  re-capture at hero windows.
- **WebGL plan (WG3/WG4):** add "lights + probes in view ≤ 32" and "≤ 1 extra camera, only during a hold" to the
  Web tier budget.

---

## 5. Sources read for this report

**Unity documentation (offline manual for 6000.3.10f1, `/Applications/Unity/Hub/Editor/6000.3.10f1/Documentation/en/`):**
`Manual/render-pipelines-feature-comparison.html` (Raytracing, Reflections, Reflection Probes tables);
`Manual/WhatsNewUnity63.html` (UnifiedRayTracing API, Ray tracing API, reflection-probe rotation in URP);
`Manual/WhatsNewUnity6.html`, `WhatsNew20231.html`, `WhatsNew20232.html` (DXR 1.1 / inline ray tracing on
"DXR1.1-capable Windows platforms, Xbox Series X/S, and Playstation 5"; HDRP RT out of experimental in 2023.1);
`Manual/choose-a-render-pipeline.html`; `Manual/WebGL2.html`; `Manual/WebGPU.html`; `Manual/WebGPU-features.html`;
`Manual/WebGPU-limitations.html`; `Manual/web-graphics-apis-intro.html`; `Manual/webgl-performance.html`;
`Manual/RefProbePerformance.html`; `Manual/urp/lighting/reflection-probes-introduction.html`;
`Manual/urp/lighting/reflection-probes-troubleshooting.html`; `Manual/urp/lighting/light-limits-in-urp.html`;
`ScriptReference/SystemInfo-supportsRayTracing.html`, `-supportsRayTracingShaders.html`,
`-supportsInlineRayTracing.html`; `ScriptReference/Rendering.RayTracingAccelerationStructure.html`;
`ScriptReference/ReflectionProbe.BlendCubemap.html`.

**Web pages read (2026-10-02):**
- HDRP 17.3, Set up ray tracing: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/Ray-Tracing-Getting-Started.html
- HDRP 17.3, Ray tracing hardware requirements: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/raytracing-requirements.html
- HDRP 17.3, Ray-Traced Reflections: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/Ray-Traced-Reflections.html
- HDRP 17.3, System requirements: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.3/manual/System-Requirements.html
- Unity Discussions, "Preview of Screen Space Reflections for URP" (all 76 posts read through the forum's JSON): https://discussions.unity.com/t/preview-of-screen-space-reflections-for-urp/1721494
- jiaozi158, UnitySSReflectionURP README: https://github.com/jiaozi158/UnitySSReflectionURP ; Forward path notes: https://github.com/jiaozi158/UnitySSPathTracingURP/blob/main/Documentation/ForwardPathSupport.md
- Kronnect, Shiny SSR 2 store page: https://assetstore.unity.com/packages/slug/188638
- Unity BoatAttack, `PlanarReflections.cs`: https://github.com/Unity-Technologies/BoatAttack/blob/master/Packages/com.verasl.water-system/Scripts/Rendering/PlanarReflections.cs
- W3C GPU for the Web, Kai Ninomiya on ray tracing (2018-12-21): https://lists.w3.org/Archives/Public/public-gpu/2018Dec/0003.html

**Package source (installed URP / Core 17.3.0 in the clone):**
`URP/Runtime/UniversalRenderPipeline.cs:139-152, 169-172, 550-620, 683, 2085-2098, 2201`;
`URP/Runtime/ForwardLights.cs:237-254`; `URP/Runtime/UniversalRenderer.cs:1652-1692`;
`URP/Runtime/RendererFeatures/` (listing); `URP/Runtime/RendererFeatures/ScreenSpaceAmbientOcclusion.cs:28-32`;
`URP/Runtime/RendererFeatures/SurfaceCacheGI/SurfaceCacheGlobalIlluminationRendererFeature.cs:1, 30-43`;
`URP/Runtime/Data/UniversalRenderPipelineAsset.cs:1418-1453`; `URP/ShaderLibrary/GlobalIllumination.hlsl:34-39`;
`Core/Runtime/UnifiedRayTracing/RayTracingContext.cs:13-23, 68, 98-104`;
`Core/Runtime/UnifiedRayTracing/Unity.UnifiedRayTracing.Runtime.asmdef`.

**Project files (clone snapshot 2026-10-02 23:10):** `Assets/Settings/FrontRooms_URP.asset:22-29, 54-56`;
`Assets/Settings/FrontRooms_URP_Renderer.asset:50, 70-82`; `ProjectSettings/QualitySettings.asset:28, 81, 134,
187, 240, 293, 328-343`; `ProjectSettings/TagManager.asset` (layers); `Assets/Resources/Rendering/FrontRoomsSurface.shader:50-315`;
`Assets/Scripts/Rendering/FrontRoomsLook.cs:22-34`; `Assets/Scripts/Rendering/FrontRoomsPostStack.cs:70-72`;
`Assets/Editor/Rendering/FrontRoomsRenderSetup.cs:112, 164-243`; `Assets/Scripts/FrontRooms3DGame.cs:49-51, 227, 282-284, 727-729, 983-1000`;
`Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:213, 723`; `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs:119, 264`;
`Assets/Plugins/FMOD/src/RuntimeManager.cs:10-11`. Audit context: `research/interaction_audit/10_audit_report.md`
§2 F3/F4/F12, §4, §5, §9; `02_glass_and_breakables.md` §6; `03_rendering_quality.md` §0–§5.

**Measurements:** `g11_bench/` (bench source, three logs, five frames). Editor, M3 Max, Metal; not a player or
a browser.

---

## 6. Open items / UNVERIFIED

1. **Browser numbers.** Every cost here is editor-on-Mac. The Relay-only overlay (≈ 7%) and the probe budget
   (lights + probes ≤ 32) must be measured in a WebGL build in a browser (WebGL BUDGETS agent,
   `research/webgl/03_measured_budgets.md`) before they go into the Web tier.
2. **Relay-only camera lighting.** Whether the lamps light the Relay when the camera's culling mask holds only
   the Relay layer (the test frame is shaded, but it may be ambient only). If not, put the lamp `Light`
   objects (which have no renderers) on a "Lights" layer and include it in the mask.
3. **Probe atlas memory** for G7 (`URP Reflection Probe Atlas` in the Memory Profiler), and the per-pixel cost
   of the Forward+ probe loop on WebGL.
4. **Realtime probe details:** `IsFinishedRendering` became true after 3 / 8 frames (docs say 9 / 14 for the full
   update); `shadowDistance = 0` did not reduce the one-shot cost. Both unexplained.
5. **Unity 6.7 URP SSR on WebGL**: not stated in the preview thread. Also when 6.7 becomes LTS, and what moving
   from 6.3 LTS costs this project (FMOD, render-graph passes, the map and sound chats' code).
6. **Metal ray tracing in later Unity versions**: Unity 6.3 reports none on the M3 Max (measured). Whether a
   later 6.x exposes it, and whether HDRP would then support it, is UNVERIFIED.
7. **Shiny SSR 2 WebGL 2 support**: seen only in a search snippet, not on the store page.
8. **The cube crossfade** via `ReflectionProbe.BlendCubemap` in URP: documented API, not tested here (G6 owns
   `SetZoneReflection` and its proof).
9. **Editor noise**: the game camera alone measured 36.7–55.0 ms across runs at the same spot. The ratios hold
   the conclusions; the absolute numbers do not describe a player build.
