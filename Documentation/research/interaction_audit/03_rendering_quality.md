# 03 — Rendering quality vs a AAA bar

Status: COMPLETE (2026-10-02). Audit only: nothing in the project was edited. Paths are relative to `Frontrooms3D/`.

Scope: whole-frame rendering quality (pipeline, lights, shadows, GI, reflections, AA, post, materials, textures, camera, frame budget), measured against what a AAA first-person horror frame has, with an honest split between the WebGL target and a desktop target. The interaction shots (key close-up, glass shatter) are covered in the sibling reports; this report covers the rendering under them, including why glass cannot reflect anything today.

Owners used below: **map chat** = `FrontRooms3DGame.cs`, `Scripts/FrontRoomsMap/*` (lamps, windows, keys, doors). **visual chat** = `Scripts/Rendering/*`, `Editor/Rendering/*`, `Resources/Rendering/*`, `FrontRoomsRoomStream.cs`, prop kit. `Editor/FrontRooms3DBuild.cs` has no stated owner (flagged below).

---

## 0. The short answer

1. **The builds Red can run are not the current game.** `Builds/Mac` and `Builds/WebGL` were made on 2026-10-01 before URP existed in the project. They are Built-in Render Pipeline builds with no surface shader, no SSAO and no post stack (§1.1). And the macOS build script still switches URP off before building (`Editor/FrontRooms3DBuild.cs:61-62`). Fix this before judging anything else.
2. **The URP frame is flat because of five specific things, not because URP is weak.** (a) There is no indirect light except one flat three-colour ambient (`Scripts/Rendering/FrontRoomsLook.cs:24-37`). (b) There is nothing to reflect: no skybox, no reflection probe in any scene, reflection intensity 0.3. (c) Lamp shadows barely exist: only one lamp in three casts, and the 162° spot cone makes URP's shadow bias about 9-13 cm, which erases contact shadows. (d) A directional fill light leaks through every ceiling at 82%, which flattens the light pools. (e) The map's troffers are plain white cubes.
3. **"AAA" has to be split by platform.** WebGL2 has no compute shaders, only baked GI, a 32-light cap and no DBuffer decals. A WebGL tier can be polished, but it cannot be AAA. A desktop tier on URP 17.3 plus a few custom passes can get close to a modern AA/AAA indoor look. A true AAA feature set (ray-traced GI and reflections, HDRP volumetrics, contact shadows) needs HDRP or a lot of custom work, and HDRP rules out WebGL.
4. **Recommended:** three explicit tiers (Web / High / Cinematic, §5) and the ten changes in §6, ranked by visual gain per cost. Most of the top five cost hours, not weeks.

---

## 1. Current state (facts)

### 1.1 The shipped builds are not the URP game

- `Builds/Mac/FrontRooms3D.app` data was written 2026-10-01 19:08-19:32. `Builds/WebGL/Build/*` was written 2026-10-01 17:49.
- The URP assets were created later that evening: `Assets/Settings/FrontRooms_URP.asset.meta` at 19:54:27, `FrontRooms_URP.asset` at 20:04:45. `ProjectSettings/GraphicsSettings.asset` and `QualitySettings.asset` were also created at 20:04:45. `Packages/manifest.json` was last modified at 19:51:57.
- The Mac player's `Contents/Resources/Data/Managed/` has no `Unity.RenderPipelines.Universal.Runtime.dll`, and none of its data files mention URP. It is a Built-in Render Pipeline build. The WebGL files are Brotli-compressed and were not opened; by date they are older still.
- `Assets/Editor/FrontRooms3DBuild.cs:61-62` (`BuildMac`) runs `GraphicsSettings.defaultRenderPipeline = null; QualitySettings.renderPipeline = null;` before building. Running "FrontRooms 3D → Build macOS" today would clear URP from the default slot and from the active quality level. Which pipeline the player then starts on depends on its startup quality level (Standalone default level 5 still points at URP). That outcome is UNVERIFIED, but the line should go either way.
- `BuildWebGL` forces quality level 3 (`FrontRooms3DBuild.cs:146`) and the Generic texture subtarget (`:142`).
- Active build target: the editor's latest script compile (`Library/Bee/200b0aE-inputdata.json`, 2026-10-02 19:41) has `"BuildTarget":"StandaloneOSX"`. The previous one (`Library/Bee/2000b0aE-inputdata.json`, 2026-10-01 17:29) had `"BuildTarget":"WebGL"`. The editor runs on Metal on an Apple M3 Max (`~/Library/Logs/Unity/Editor.log`, device init lines).

### 1.2 Pipeline asset — `Assets/Settings/FrontRooms_URP.asset`

| Setting | Value | Line |
|---|---|---|
| HDR / buffer precision | on / 32-bit (R11G11B10) | 26-27 |
| MSAA | 4x | 28 |
| Render scale / upscaler | 1.0 / Auto (no STP, no FSR in use) | 29-30 |
| Light probe system | legacy light probes, not APV | 36 |
| Main light | per pixel, shadows on, 2048 map | 44-46 |
| Additional lights | per pixel, 8 per object, shadows on, 4096 atlas, tiers 256/512/1024 | 47-53 |
| Reflection probe blending / box projection | **off / off** | 54-55 |
| Shadow distance / cascades | 40 m / 2 (split 0.25) | 57-59 |
| Depth / normal bias | 0.6 / 0.6 | 63-64 |
| Soft shadows | on, quality High | 66, 69 |
| Cookies | supported, 2048 atlas | 70-71, 75 |
| Light layers | **off** | 76 |
| Colour grading | HDR, 32 LUT | 80-81 |
| GPU Resident Drawer | off | 86 |

All of this is written by `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs:87-105`.

### 1.3 Renderer — `Assets/Settings/FrontRooms_URP_Renderer.asset`

- Forward+ (`m_RenderingMode: 2`, line 50; set at `FrontRoomsRenderSetup.cs:77`).
- One renderer feature: SSAO (lines 27-28, 57-82). Blue-noise method, depth-normals source, full resolution, high samples, high (bilateral) blur, intensity 1.6, radius 0.45 m, direct-lighting strength 0.35 (`FrontRoomsRenderSetup.cs:130-141`).
- No Decal feature, no Screen Space Shadows, no full-screen passes, no volumetrics. Opaque texture is off (`FrontRooms_URP.asset:23`), so no refraction is possible.

### 1.4 Quality levels are not tiers — `ProjectSettings/QualitySettings.asset`

- All six levels point at the same URP asset (guid `9f47…`, lines 51, 104, 157, 210, 263, 316). In URP, MSAA, shadows, SSAO, HDR and render scale live in the pipeline asset, so the six levels are visually almost identical. They differ only in aniso, LOD bias and vSync.
- `FrontRoomsRenderSetup.cs:48-54` forces every level back to that one asset on each run. Any tier work has to change this loop, or the next "Set up URP" run will undo it.
- Defaults: Standalone = 5 "Ultra", WebGL = 3 "High" (lines 338-339).

### 1.5 Player / platform — `ProjectSettings/ProjectSettings.asset`

- Linear colour space (line 50). Graphics APIs automatic (line 543): WebGL2 on web, Metal on Mac. WebGPU is not enabled.
- WebGL: static batching off (537-539), IL2CPP, 1 GB max heap (815), high-performance power preference (820). Canvas 1280×720. The default template does not force `devicePixelRatio = 1` on desktop (`Builds/WebGL/index.html:75, 102`), so a Retina screen renders about 2560×1440 into a 720p canvas. That is UNVERIFIED in a browser, but it is a big hidden cost.

### 1.6 GI, probes and environment — `Assets/Scenes/FrontRooms3D.unity`

- No skybox (`m_SkyboxMaterial: {fileID: 0}`). Default reflection source is Skybox (`m_DefaultReflectionMode: 0`). Reflection intensity is 0.3 (also `FrontRoomsLook.cs:20`).
- Zero `ReflectionProbe` and zero `LightProbeGroup` components in all three scenes.
- Baked and realtime GI are both off (`m_EnableBakedLightmaps: 0`, `m_EnableRealtimeLightmaps: 0`). No LightingData asset.
- Ambient is a Trilight gradient plus Exp² fog at 0.014 (`FrontRoomsLook.cs:15-37`).
- The map is generated at runtime in 3 m cells (`FrontRoomsMap.cs:52`). Classic lightmaps and APV both need static geometry at bake time, so neither can simply be "turned on" for the maze (§3, row 1).

Net effect: every rough surface gets the same three ambient colours whatever room it is in. Every glossy surface reflects the default environment (no sky, so most likely black or near-black — UNVERIFIED; confirm in the Frame Debugger) scaled by 0.3. That is why glass, VCT floors, CRT screens, chrome and the shader's "damp carpet" gloss show nothing but light-source highlights.

### 1.7 Surface shader — `Assets/Resources/Rendering/FrontRoomsSurface.shader`

Strengths: URP metallic PBR (`UniversalFragmentPBR`, line 255), normal + mask (smoothness, cavity) maps, world-projected tiling, and a well-designed two-scale macro-wear layer with water stains, damp patches that darken and gloss the carpet, floor grime and ceiling streaks (lines 189-223). For a hand-written shader this is good work. 83 of the 86 `Resources/Surfaces/*.mat` use it.

Gaps against URP's own Lit shader (package `Shaders/Lit.shader:142-169`):
- Indirect diffuse is SH only (`inputData.bakedGI = SampleSH(...)`, line 240). There is no `LIGHTMAP_ON`/`DIRLIGHTMAP_COMBINED`, no APV include (`ProbeVolumeVariants.hlsl`) and no `_SCREEN_SPACE_IRRADIANCE`, so the surfaces cannot receive lightmaps, APV or future screen-space GI even if those are enabled.
- No `_REFLECTION_PROBE_BOX_PROJECTION` keyword, so it compiles to 0 (`ShaderLibrary/GlobalIllumination.hlsl:38-39, 311`): probes can never be box-projected on these surfaces. Forward+ still clusters probes (`GlobalIllumination.hlsl:291`).
- No `_DBUFFER_MRT1/2/3`, so DBuffer decals will not show on walls, floors or ceilings.
- No `LOD_FADE_CROSSFADE`, no parallax/height, no detail normal map.
- The DepthNormals pass uses geometric normals (lines 302-317), so SSAO does not see wallpaper or carpet relief.

### 1.8 Lights

**Map lamps** — `Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:1027-1076`, map chat:
- One spot per 3 m cell (`:706`), 162° outer / 96° inner, range 10 m (12 m in tall zones), no cookie, colour (1, .96, .88) (`:1055-1063`).
- Shadows: about one lamp in three (`:1067`), and only within `shadowRadius` 9 m (`:1121`; `Levels/FrontRoomsLevel0.asset:49`).
- Lamps beyond `lightRadius` 16 m are switched off (`:1117-1119`). A 16 m radius covers about 89 cells, so up to roughly 80 lamps can be live around the player.
- The code itself notes that a lamp with no shadow "lights straight through the rooms' walls" (`:1082-1085`).
- The lens is a primitive cube with a plain URP Lit material and constant emission (`:1037-1046`, `:1632`). Its emission is rewritten through a MaterialPropertyBlock every frame (`:1123-1125`).

**Title corridor** — `Scripts/FrontRoomsRoomStream.cs`, visual chat:
- 12 spots per room (3 columns × 4 rows, lines 62-67), 162°/96°, range 10 m (6.5 m in Run), intensity 4.2-6.0 (lines 1101-1105, 1366-1378).
- The 4 centre spots cast soft shadows (line 1110). The pool holds 5 rooms (line 15).

**Fill** — `FrontRooms3DGame.cs:268-276`, scene `FrontRooms3D.unity:2221-2241`, map chat:
- A directional "Soft ambient direction" light, intensity 0.16 in the scene (0.22 in code), soft shadows at strength 0.18.
- It is the main light, so it pays for a 2-cascade, 40 m, 2048 shadow map. At 18% shadow strength it still lights 82% through every ceiling and wall.

**Why the shadows don't land (calculation from URP 17.3 source):**
- URP sizes spot shadow bias from the frustum: `frustumSize = tan(spotAngle/2) × range` (`Library/PackageCache/com.unity.render-pipelines.universal@37e0d4fc2503/Runtime/ShadowUtils.cs:390`).
- Then `texelSize = frustumSize / resolution`, and depth and normal bias are `0.6 × texelSize` (`:414-416`). Both are multiplied by the PCF kernel radius, 2.5 or 3.5, for soft shadows (`:435-447`). New lights default to the High tier, 1024 (`UniversalAdditionalLightData.cs:71`).
- For 162° and 10 m: tan 81° × 10 = 63 m, so the texel is 6.2 cm and each bias is **about 9-13 cm**. For a 120° cone: 17 m, 1.7 cm texel, about 2.5-3.6 cm. For 90°: about 1.5-2 cm.
- The same wide frustum also spreads the 1024 map so thinly that a texel on the floor under the lamp is about 3.5 cm wide, against about 1 cm at 120°.
- Result: furniture legs, the Relay's feet, door gaps and baseboards lose their contact shadow. That is exactly what the frames show (§1.11). If more than 16 shadowed lamps compete for the 4096 atlas, URP has to shrink them further — UNVERIFIED for this scene.

**Fake shafts:** "volumetric" beams are additive frustum meshes (`Resources/Lighting/VolumetricBeam.shader:15-17`, `Blend One One`, `ZWrite Off`), built per fixture in `FrontRoomsRoomStream.cs:1157-1179`. They do not sample scene depth, so they cut hard lines where they meet geometry, and they ignore shadows.

**WebGL light cap:** in URP 17.3 a WebGL2 (GLES3 shader API) build compiles `MAX_VISIBLE_LIGHTS` to the mobile limit of 32 (`ShaderLibrary/Input.hlsl:17-24`; `com.unity.render-pipelines.universal-config/Runtime/ShaderConfig.cs:20`). The map can have far more than 32 lamps on screen, so on the web URP will drop some.

### 1.9 Camera, AA and post

- Camera: FOV 76°, near 0.06 m, far 80 m (clamped to sight distance in map play, `FrontRooms3DGame.cs:713`), solid-colour clear, not a physical camera (`FrontRooms3DGame.cs:226-231`).
- Camera AA is forced to None (`FrontRoomsPostStack.cs:72`), so MSAA 4x is the only AA. Dithering is on. `targetFrameRate = 60` (`FrontRooms3DGame.cs:291`).
- Global profile `Resources/Rendering/FrontRoomsPost.asset` (written by `FrontRoomsRenderSetup.cs:184-237`):
  - ACES tonemapping
  - bloom threshold 1.05, intensity 0.55, scatter 0.72, HQ filtering, no lens dirt
  - white balance +9 / −7
  - contrast −6, saturation −8, post-exposure +0.15
  - warm lift +0.035
  - vignette 0.26, film grain Medium3 0.22, chromatic aberration 0.06, lens distortion −0.04
- Office zone profile: `FrontRoomsPost_Office.asset`, set at `FrontRoomsRenderSetup.cs:156-182`.
- Not used: depth of field, motion blur, screen-space lens flare, Panini, bloom dirt. URP has no auto exposure (§3).

### 1.10 Textures and meshes

- 166 PNGs in `Resources/Surfaces/Textures`. Architecture is 2048² (carpet, ceiling, VCT) and 2048×3072 (wallpaper, over 0.75 × 1.125 m, about 2,700 px/m). Drywall, fabric and louver are 1024². **Texel density is not the problem.**
- Importer: mips, trilinear, aniso 16, max 4096, CompressedHQ (`FrontRoomsRenderSetup.cs:617-641`). No per-platform overrides (`overridden: 0` in every `.meta`). Mip streaming is off. WebGL uses the Generic texture subtarget (`FrontRooms3DBuild.cs:142`).
- 54 prop FBX files in `Resources/Props/Models`, none with LODs and no `LODGroup` prefabs.

### 1.11 Evidence frames (read for this audit)

- `Verification/main-autopilot/03_play_10s.png`, `04_play_19s.png` (map play, URP, editor, 1600×900):
  - Even wash of light with no readable pools.
  - Troffers are flat clipped-white rectangles.
  - The window glass shows the wallpaper behind it and no reflection.
  - Pillar and wall bases have almost no contact darkening.
- `02_relay.png`, `05_play_28s.png`: the Relay and the keys are untextured primitives, and the Relay's feet leave no shadow.
- `Verification/lookdev/0_Lobby_forward.png`, `2_Office_forward.png` (title corridor): moodier and better composed, but the ceiling is flat, the lenses are flat, there are no shafts and the VCT floor reflects nothing.
- `Verification/kit_lookdev/office_round2.jpg`, `kit_round2_overview.jpg`: the best frames in the project, with textured troffers, real prop materials and macro wear on the ceilings. Remaining tells:
  - furniture piles sit on the carpet with no contact shadow;
  - glass cabinet fronts and the vending-machine glass read flat;
  - only every third lamp casts a shadow (`Editor/Rendering/FrontRoomsKitLookdev.cs:223`).
- `scratchpad/proj/Verification/hunter_concepts/Hunter_B_NightShift_close.png`, `Relay_Current_corridor.png`: characters are single-colour materials with no skin or cloth response. The scalloped light on the corridor walls is the strongest lighting moment in the project and shows what wall-grazing practicals can do.
- Lookdev renders into an 8-bit `ARGB32` texture with MSAA 4 (`FrontRoomsLookdevCapture.cs:53`, `FrontRoomsKitLookdev.cs:126`). That is fine for review but is not the player's output path.

### 1.12 Frame budget (what we know)

From `Verification/main-autopilot/report.json` (editor, M3 Max): average 58.7 fps under the 60 fps cap, p95 16.8 ms, p99 19.4 ms, and one 1,440 ms spike at 3.0 s (Office zone, 25 chunks built).

GPU headroom is unknown: the frame rate is capped, no GPU timings were captured, and the editor is not a player. There is no WebGL measurement at all.

### 1.13 Documentation drift

`Documentation/LIGHTING_SPEC.md:9-10, 15-21` describes point lights, fog 0.024 and intensities around 1. The code uses wide spots, fog 0.014 and intensities 4.2-6.0 (§1.8). The spec should be rewritten around the tiers in §5.

---

## 2. Diagnosis: why the frame reads "low level"

Ranked by how much each contributes to Red's impression:

1. **Wrong build.** Any judgment made from `Builds/` is of a pre-URP game (§1.1).
2. **No light structure.**
   - Wide 162° unshadowed spots, plus a directional fill leaking through ceilings, give an even wash. AAA interiors read through contrast: pools under each lamp, falloff up the walls, darkness between fixtures, occlusion in corners.
   - Here the only darkening comes from SSAO (radius 0.45 m) and fog.
   - The corridor wall scallops in the hunter concepts show the look this project could have everywhere.
3. **Missing contact shadows.** The bias calculation in §1.8 removes the 2-10 cm of shadow that grounds objects. AAA frames add screen-space contact shadows on top of good shadow maps; here even the shadow maps cannot reach.
4. **Nothing to reflect.** No sky, no probes, intensity 0.3. Every glossy material — glass, VCT, wet carpet, CRT, chrome, brass, varnished wood — loses its strongest cue. This is the rendering-side root cause of "glass material and reflection values are wrong". The material-side causes are covered in the glass report:
   - `Prop_Glass` uses plain alpha blending at α 0.16, which multiplies reflections by alpha (`FrontRoomsRenderSetup.cs:375, 412-415`).
   - The map's glass is premultiplied, which keeps specular (`FrontRoomsMapWorld.cs:1662-1677`; package `ShaderLibrary/BRDF.hlsl:67-72`), but it still has nothing to reflect.
5. **One ambient for the whole world.** The Trilight colours are the same in Lobby, Office, Run and Exit. Without bounce, a red exit-sign corridor and a beige lobby get identical fill, which reads as CG.
6. **The most-seen object looks placeholder.** Map troffers are untextured emissive cubes, and the Relay and keys are primitives. Rendering cannot hide placeholder assets.
7. **AA that fixes the wrong thing.** MSAA 4x smooths triangle edges but not specular or texture shimmer on wallpaper, carpet and thin cubicle trims (Unity: MSAA does not address "shader aliasing issues" — URP anti-aliasing page, §8).
8. **No camera craft.** No DOF, motion blur or shot-specific grading exists. The key and window shots Red described are camera work that needs these tools (§6 item 8).

---

## 3. Gap analysis vs a AAA first-person horror frame

Reference point for "AAA horror": Resident Evil Village is described as using ray-traced GI and reflections, volumetric particles for dust and soot, mostly dynamic lights, and subsurface skin shading (gamingbolt analysis, §8). Alan Wake 2 and similar titles add path-traced or RT lighting; those are out of reach here and are not used as the bar.

Notes on the columns:
- "URP 17.3 native" cites the Unity 6.3 feature-comparison page unless stated.
- Cost classes are engineering estimates for a 1080p desktop GPU. They were **not measured in this project (UNVERIFIED)** and must be checked with the GPU profiler. N = negligible (<0.2 ms), L = low (0.2-0.7 ms), M = medium (0.7-2 ms), H = high (>2 ms).

| # | AAA feature | FrontRooms now | URP 17.3 native | Custom work needed | Cost | WebGL2 |
|---|---|---|---|---|---|---|
| 1 | **Indirect light / GI** (bounce colour, room-dependent fill) | Trilight SH for the whole world (`FrontRoomsLook.cs:24-37`) | Baked lightmaps, APV (baked from static geometry), light probes. SSGI "No". Surface Cache GI exists in package source (`Runtime/RendererFeatures/SurfaceCacheGI/`) but Unity calls it a preview targeted at 6.7 LTS, compute-only | (a) Cheap: per-zone ambient SH swapped by zone (`RenderSettings.ambientProbe`) plus a "floor bounce" term per lit cell. (b) Real: per-module baked lightmaps stored with each room module and re-applied at spawn, plus the shader keywords (§1.7). The procedural maze rules out a single scene bake | (a) N (b) N at runtime, high authoring | Baked GI only on Web; (a) and (b) both work |
| 2 | **Contact shadows** | None; spot bias 9-13 cm erases them | "No" | Screen-space contact-shadow pass (short depth ray-march toward 1-2 key lights), or fix the shadow maps first (row 3) and push SSAO | L-M | Fragment-only, feasible at half res |
| 3 | **Shadowed practicals** (most lamps near the player cast) | 1 in 3 lamps, ≤9 m, 162° cone | Yes: Forward+ shadow atlas, soft PCF (High = 7×7), cookies | Narrow shadowed cones (~110-120°) plus a wide unshadowed low fill; choose the nearest N lamps instead of a 1-in-3 hash; rendering layers to stop leaks through walls | M (shadow-map renders) | Keep 4-6 casters at 512 |
| 4 | **SSAO / GTAO** | URP SSAO, full res, high | SSAO (depth or normals). No GTAO | GTAO would be custom; not needed. Tune radius, and use the normal map in DepthNormals if relief is wanted | M (Downsample is the "Very high"-impact switch — SSAO reference, §8) | Yes; downsample and low samples |
| 5 | **Reflections** (probes, SSR, planar) | No probes, no sky, intensity 0.3 | Reflection probes (baked/realtime), box projection, blending (max two per object). SSR "No" in 6.3 | Bake 3-5 interior cubemaps once (lobby, office, run, exit, corridor) from the lookdev rooms; swap per zone as the custom reflection, or place probes in modules; add the box-projection keyword to the surface shader | N (baked) / H (realtime) | Baked: yes. Realtime: avoid |
| 6 | **Volumetric fog and light shafts** | Exp² fog; additive frustum beams with no depth fade | Fog Linear/Exp only; no volumetrics | (a) Depth-faded, noise-modulated beam shader. (b) Half/quarter-res ray-marched spot scattering pass that reads the spot shadow maps (custom renderer feature) | (a) L (b) H | (a) yes; (b) only a low-res fragment version; froxel/compute versions no |
| 7 | **Emissive fixtures with halation** | Map lens = flat white cube; stream uses textured `Troffer_Lens` | Bloom (with dirt texture), Lens Flare (SRP), Screen Space Lens Flare; both flare types work "on all platforms" (§8) | Use the textured lens in the map; author a bloom dirt texture; subtle SSLF streaks; per-lamp flicker already exists | L | Yes |
| 8 | **AA / temporal stability / upscaling** | MSAA 4x only; camera AA forced off | FXAA, SMAA, TAA (not with MSAA), STP (needs SM5 + compute, not GLES), FSR1 | Per-tier choice (§5). TAA needs motion vectors; the custom shader has no MotionVectors pass, which is fine for static walls, but moving props need URP Lit or a pass | TAA L; STP L-M (pays for itself at 0.77 render scale) | MSAA or SMAA/FXAA. STP no. TAA UNVERIFIED on WebGL2 |
| 9 | **Material detail** (detail normals, POM, specular occlusion, wetness/grime) | Strong macro wear, damp and grime (`FrontRoomsSurface.shader:189-223`); no detail or height | URP Lit has detail maps and parallax ("Pixel displacement only") | Add a detail-normal tile and optional parallax to `FrontRooms/Surface` for carpet, ceiling tile and wallpaper seams | L | Yes |
| 10 | **Decals** (stains, scuffs, footprints, water damage, signage) | None | Decal feature: DBuffer (Forward/Forward+, "does not support the OpenGL and OpenGL ES API") or Screen Space | Add `_DBUFFER_MRT1/2/3` plus `ApplyDecalToSurfaceData` to the surface shader; a decal atlas; placement by module tags | L-M | Screen Space technique only (DBuffer on WebGL2 UNVERIFIED, likely no) |
| 11 | **Glass and transparency** | Plain alpha (`Prop_Glass`) or premultiplied (map) Lit; no refraction, smudge or thickness | Lit transparent; screen-space refraction "No"; opaque texture available | Thin-glass shader: premultiplied, Fresnel, smudge map driving roughness, refraction offset from `_CameraOpaqueTexture`, crack mask for the break state | L (opaque copy is a bandwidth cost) | Yes (downsample the opaque texture) |
| 12 | **Exposure** ("physically plausible") | Fixed post-exposure +0.15 | Exposure "Supported types: Fixed"; no physical light units; physical camera "affects field of view only" | Calibrated fixed-EV workflow (one exposure target per zone via the zone volumes); optional custom eye adaptation from a downsampled luminance mip | N / L | Yes (fragment mip method) |
| 13 | **Lens and camera** (DOF, motion blur, CA, grain, distortion) | CA, grain, distortion, vignette | DOF Bokeh and Gaussian; camera and object motion blur | Shot-specific volume profiles for interactions (key push-in, window break); no gameplay DOF | Gaussian L, Bokeh M-H, MB L | Gaussian yes; Bokeh costly |
| 14 | **Characters** (skin/cloth response, SSS, rim, wet) | Single-colour Lit primitives | SSS "No" | Wrap/pre-integrated diffuse in a small character shader, cloth sheen, fresnel rim from practicals; mainly an art/model task | L | Yes |
| 15 | **Asset density and LODs** | 54 props, no LODs, primitives for keys and Relay | LOD groups, LOD cross-fade, GPU Resident Drawer (Forward+, compute, not GLES) | LODs for props; add the cross-fade keyword to the surface shader | saves cost | GRD no on web; LODs yes |
| 16 | **Dust / particles** | None | Shuriken particles; VFX Graph needs compute | Dust motes in lamp cones (Shuriken, soft-particle depth fade) | L | Shuriken yes |
| 17 | **HDR output and grading** | ACES + LUT 32 | Yes | Grade per zone (exists for Office); consider Neutral tonemap plus a LUT authored in Resolve for more control | N | Yes |

---

## 4. What "AAA" can honestly mean on each platform

**WebGL2 (current web target).**
- No compute shaders, so no STP, no GPU Resident Drawer, no Surface Cache GI and no compute volumetrics (Unity web graphics page and STP page, §8).
- Only baked GI.
- 32 visible additional lights (§1.8). DBuffer decals are documented as unsupported on OpenGL/GLES (WebGL2 inherits this — UNVERIFIED).
- It runs on integrated GPUs inside a browser, often at 2× pixel ratio.
- WebGPU would lift the compute limits, but Unity calls it "experimental and not recommended for production usage" (web graphics page, §8).
- **Realistic bar:** a polished, art-directed indie frame. Strong light pools, baked cubemap reflections, fake but depth-aware shafts, decals, good grading. Not AAA, and Red should hear that plainly.

**Desktop (macOS Metal / Windows DX12), URP 17.3.**
- With the changes in §6 plus two custom passes (contact shadows, ray-marched spot scattering) and STP, the indoor frame can reach a convincing AA/"indie-AAA" level, close to what URP horror games ship.
- What stays out of reach on URP without very large custom work: ray-traced GI and reflections, true SSR (absent in 6.3; Unity's Surface Cache GI preview post refers to URP SSR as upcoming), HDRP-quality volumetric fog, area-light shading and subsurface skin.

**HDRP.** It has volumetrics, contact shadows, SSR/SSGI, physical light units and auto exposure natively. But it drops WebGL and would need a rewrite of `FrontRooms/Surface`, the post stack, the lookdev tools and every runtime-created material. Not recommended for this semester. Recommend instead a desktop "Cinematic" URP tier for presentation captures.

---

## 5. Recommended quality tiers

One URP asset and one renderer per tier. QualitySettings maps the tiers: WebGL default = Web, Standalone default = High, Cinematic selectable and used for capture. `FrontRoomsRenderSetup.SetUp` must stop forcing one asset into every level (`FrontRoomsRenderSetup.cs:48-54`), and `FrontRoomsPostStack.ConfigureCamera` must pick AA per tier instead of `None` (`FrontRoomsPostStack.cs:72`).

| Setting | **Web** (WebGL2, 720p, DPR capped to 1) | **High** (desktop default, 1080p-1440p @ 60) | **Cinematic** (desktop capture, strong GPUs) |
|---|---|---|---|
| Path | Forward+ | Forward+ | Forward+ |
| AA | MSAA 2x or SMAA; render scale 1.0 | TAA (or SMAA if ghosting bothers); MSAA off | STP at 0.77 render scale (implies TAA) |
| HDR | on (LDR fallback if unsupported) | on, 32-bit | on, 64-bit if banding shows |
| Lamp light radius | ~12 m (stay under 32 visible) | 16 m | 20 m |
| Shadowed lamps | nearest 4, tier 512, atlas 2048, soft Medium | nearest 8-10, tier 1024, atlas 4096, soft High | nearest 14-16, tier 1024-2048, atlas 8192, soft High |
| Shadowed cone | ~110-120° plus unshadowed wide fill | same | same |
| Main directional | **off** | off | off |
| Ambient | per-zone SH | per-zone SH | per-zone SH (+ per-module lightmaps when built) |
| SSAO | downsample on, samples Low, Kawase blur, radius .35 | full res, Medium samples, radius .5 | full res, High, radius .5 |
| Contact shadows | off (or 1 light, half res) | 1-2 key lamps, half res | 2-4 lamps, full res |
| Reflections | baked zone cubemaps, intensity ~1 | baked cubemaps + box-projected module probes | + one time-sliced realtime probe near the player |
| Shafts / volumetrics | depth-faded beam meshes | beam meshes + quarter-res scattering | half-res scattering with shadows |
| Decals | Screen Space | DBuffer (Albedo Normal MAOS) | DBuffer |
| Post | ACES, bloom (fewer iterations), grain, vignette; CA/distortion off | + SSLF, bloom dirt, CA | + Bokeh DOF and object motion blur in shots |
| Interaction shots | Gaussian DOF + short camera motion blur | Bokeh DOF + camera MB | Bokeh + object MB |
| Textures | WebGL override max 1024-2048, mip streaming on | 2048 | 4096 where authored |
| Target (proposed, unmeasured) | 30-60 fps on an M1 / Iris Xe class laptop | 60 fps on a mid desktop GPU | 30-60 fps; capture tier |

Proposed High-tier GPU budget at 60 fps (a plan to measure against, not a measurement):

| Pass | Budget |
|---|---|
| Opaque + lighting | 5.5 ms |
| Shadows | 2.5 ms |
| SSAO | 1.0 ms |
| Contact shadows | 0.5 ms |
| Transparents + beams | 0.8 ms |
| Volumetric scattering | 1.5 ms |
| Post incl. TAA | 1.5 ms |
| UI | 0.3 ms |
| Headroom | 3 ms |

---

## 6. Top 10 changes, ranked by visual gain per cost

| Rank | Change | Gain | Cost | Owner | WebGL |
|---|---|---|---|---|---|
| 1 | **Rebuild both players on URP and stop the Mac build nulling the pipeline** (`FrontRooms3DBuild.cs:61-62`). Add a build check that fails if `GraphicsSettings.defaultRenderPipeline` is null. Re-capture `Verification/` frames from the player, not only the editor. | Very high: the shipped build gains the whole URP look | < 1 h | build-script owner (unassigned — map chat by default, since it owns game flow), with visual chat | yes |
| 2 | **Lamp shadows that land.** Shadowed lamps get ~115° outer cones (bias drops from ~9-13 cm to ~3 cm, §1.8) plus a rectangular troffer cookie. Choose the nearest N lamps by distance instead of the 1-in-3 hash (`FrontRoomsMapWorld.cs:1067, 1121`). The same change in the stream (`FrontRoomsRoomStream.cs:1101-1110`). | High: contact under furniture, Relay feet, door leaves; readable pools | hours | map chat (MapWorld), visual chat (RoomStream, shared constants and cookie) | yes, with fewer casters |
| 3 | **Give glossy surfaces something to reflect.** Bake 3-5 zone cubemaps from the lookdev rooms. Swap them per zone as the default/custom reflection, or as box-projected probes in modules. Raise reflection intensity from 0.3 (`FrontRoomsLook.cs:20`). Add `_REFLECTION_PROBE_BOX_PROJECTION` to `FrontRoomsSurface.shader` and enable it in the URP asset (`FrontRooms_URP.asset:55`). | High: glass, VCT, damp carpet, CRT, chrome come alive; the rendering root of Red's glass complaint | 0.5-1 day | visual chat (bake tool, shader, Look API); map chat calls the per-zone swap | yes (baked) |
| 4 | **Remove the leaking directional fill; per-zone ambient instead.** Delete or disable "Soft ambient direction" (`FrontRooms3DGame.cs:268-276`, scene `FrontRooms3D.unity:2221-2241`). Turn off main-light shadows. Have `FrontRoomsLook` expose per-zone SH (Lobby warm, Office olive, Run red, Exit cyan) that the zone volumes switch. | Medium-high: contrast between lamps, darker corners; saves the main shadow pass | hours | map chat (light, scene), visual chat (Look API) | yes |
| 5 | **Make the troffer the hero.** Map lamps use the textured `Troffer_Lens` / office lens (`FrontRoomsMapWorld.cs:1632` builds a plain Lit cube instead). Add a bloom dirt texture and subtle Screen Space Lens Flare streaks. Keep the existing per-lamp flicker. | Medium-high: it is in nearly every frame | hours | map chat (material choice), visual chat (post profile, dirt texture) | yes |
| 6 | **Real tiers and temporal AA.** Three URP assets (§5). Desktop High uses TAA instead of MSAA, Cinematic uses STP. Fix `FrontRoomsRenderSetup.cs:48-54` and `FrontRoomsPostStack.cs:72`. Cap WebGL DPR to 1 in the template. | Medium: shimmer-free wallpaper and trims read as "expensive"; frees bandwidth | 1 day | visual chat (+ build-script owner for the template) | Web tier keeps MSAA/SMAA |
| 7 | **Thin-glass material.** Premultiplied (not alpha) `Prop_Glass` (`FrontRoomsRenderSetup.cs:412-415`). Enable the opaque texture (`FrontRooms_URP.asset:23`) for refraction offset. Add a smudge/dust map driving roughness, Fresnel edge tint, and a crack mask for the break state. The shatter mechanics belong to the glass report. | High on the exact shot Red named; medium elsewhere | 1-2 days | visual chat (shader/material); map chat uses it for windows (`FrontRoomsMapWorld.cs:900-906, 1659`) | yes (downsampled opaque) |
| 8 | **Shot profiles for interactions.** A volume profile per shot (key insert push-in, window break): Gaussian DOF on Web, Bokeh on desktop, short camera motion blur, vignette and exposure push, blended in by weight for the shot's duration. URP-native, no new rendering code. | High for the two shots Red asked for | hours (profiles) + the camera work in the shot reports | visual chat (profiles + `FrontRoomsPostStack.EnsureShotVolume`-style API); map chat triggers | yes |
| 9 | **Decals.** Add the DBuffer keywords and `ApplyDecalToSurfaceData` to `FrontRoomsSurface.shader`. Add the Decal renderer feature (Screen Space on Web). Author an atlas: water damage, scuffs at door frames, footprints in damp carpet, switch-plate grime, posted notices. Place by module tags. | Medium-high: breaks repetition, adds history | 2-3 days | visual chat (shader, feature, atlas); map chat (placement hooks) | Screen Space only |
| 10 | **Light you can see.** (a) Beam shader with soft depth fade, distance fade and drifting noise, plus Shuriken dust motes in cones — all tiers. (b) Desktop: a half/quarter-res ray-marched spot-scattering renderer feature reading the spot shadow maps, so the Relay casts a shadow into the haze. | (a) Medium; (b) high for mood | (a) hours; (b) 3-5 days | visual chat | (a) yes; (b) no / very low res |

**Just outside the top 10** (big gain, high cost):
- (11) Per-module baked lightmaps plus shader lightmap keywords: the single biggest step toward AAA indoor light, but a project, not a tweak, because the map is procedural.
- (12) Screen-space contact shadows for 1-2 key lamps.
- (13) A modelled, textured Relay with a small skin/cloth shader.
- (14) Prop LODs and LOD cross-fade in the surface shader.

---

## 7. How to verify

1. Fresh URP player builds per tier (macOS and WebGL), launched outside the editor.
2. Frame Debugger: check what the default reflection cubemap actually is with no skybox (§1.6, UNVERIFIED), and confirm the number of additional lights and shadow slices per frame in map play.
3. GPU timings per pass with the Profiler's GPU module in the player for Web and High.
4. Before/after captures from fixed viewpoints, reusing `FrontRoomsLookdevCapture` and the autopilot frames:
   - lobby corridor
   - office bullpen
   - furniture pile close-up (contact shadows)
   - window from 1 m (reflection)
   - Relay at 3 m (ground contact)
5. The WebGL tier tested on a non-Apple-Silicon laptop at DPR 1 and DPR 2.

---

## 8. Sources

**Web pages read for this report:**
- Unity 6.3 LTS, Render pipeline feature comparison (URP vs HDRP: SSR/SSGI/contact shadows "No", fog Linear/Exp, exposure "Supported types: Fixed", TAA limits, decals, APV, probe blending, DOF/MB, lens flare, parallax, physical camera FOV only, no physical light units, no SSS, STP and FSR1): https://docs.unity3d.com/6000.3/Documentation/Manual/render-pipelines-feature-comparison.html
- Unity 6.3, STP upscaler (Shader Model 5.0, compute, not OpenGL ES, enables TAA): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/stp/stp-upscaler.html
- Unity 6.3, Web graphics APIs (WebGL2 default; WebGPU "experimental and not recommended for production usage"): https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-graphics.html
- Unity 6.3, WebGL2 page (Web "only supports Baked Global Illumination"): https://docs.unity3d.com/6000.3/Documentation/Manual/WebGL2.html
- Unity, Adaptive Probe Volumes concept (baked from static geometry; page served as 6000.6): https://docs.unity3d.com/Manual/urp/probevolumes-concept.html
- Unity 6.3, URP anti-aliasing (TAA incompatible with MSAA; MSAA does not fix shader aliasing): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/anti-aliasing.html
- Unity 6.3, Decal renderer feature reference (DBuffer "does not support the OpenGL and OpenGL ES API"; Screen Space technique): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/renderer-feature-decal-reference.html
- Unity 6.3, Reflection probes introduction (per-pixel blending, max two probes per object): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/lighting/reflection-probes-introduction.html
- Unity, SSAO renderer feature reference (performance impact per property; page served as 6000.6): https://docs.unity3d.com/Manual/urp/ssao-renderer-feature-reference.html
- Unity, Choose a lens flare type (both types work on all platforms; SSLF is GPU-only; page served as 6000.6): https://docs.unity3d.com/Manual/urp/shared/lens-flare/choose-a-lens-flare-type.html
- Unity, Light limits in URP (256 desktop / 32 mobile / 16 GLES3-and-earlier; page served as 6000.6): https://docs.unity3d.com/Manual/urp/lighting/light-limits-in-urp.html
- Unity 6.3, GPU Resident Drawer (Forward+ only, compute, not OpenGL ES): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/gpu-resident-drawer.html
- Unity Discussions, Surface Cache GI preview (dynamic diffuse GI, URP only, planned for 6.7 LTS, built on the UnifiedRayTracing library): https://discussions.unity.com/t/surface-cache-gi-preview/1720494
- GamingBolt, Resident Evil Village graphics analysis (RT GI and reflections, volumetric particles, dynamic lights, SSS): https://gamingbolt.com/resident-evil-village-graphics-analysis-improvements-over-resident-evil-7-ps5-vs-pc-comparison-and-more

**Package source read** (local, `Library/PackageCache/`):
- `com.unity.render-pipelines.universal@37e0d4fc2503`:
  - `Shaders/Lit.shader:142-169`
  - `ShaderLibrary/GlobalIllumination.hlsl:34-39, 291, 311`
  - `ShaderLibrary/BRDF.hlsl:67-72`
  - `ShaderLibrary/Input.hlsl:17-24`
  - `Runtime/ShadowUtils.cs:390, 414-447`
  - `Runtime/UniversalAdditionalLightData.cs:71`
  - `Runtime/RendererFeatures/SurfaceCacheGI/`
- `com.unity.render-pipelines.universal-config@8dc1aab4af1d/Runtime/ShaderConfig.cs:17-23`

**UNVERIFIED items (need an in-engine or in-browser check):**
- the default reflection cubemap with no skybox
- the Mac player's pipeline after running today's `BuildMac`
- WebGL DPR in practice
- URP TAA and DBuffer behaviour on WebGL2
- shadow-atlas downscaling with 16+ casters
- all cost classes and the frame budgets in §3 and §5
- the 6000.6-served doc pages applying unchanged to 6000.3

**Fetch attempts that failed (not used):**
- `.../6000.3/Documentation/Manual/urp/urp-feature-comparison.html` (404)
- `.../6000.3/Documentation/Manual/urp/rendering/forward-plus-rendering-path.html` (404)
- `.../6000.3/Documentation/Manual/urp/post-processing-screen-space-lens-flare.html` (404)
