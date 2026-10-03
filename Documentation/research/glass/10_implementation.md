# 10 — Glass and zone reflections: implementation (G1–G4, G6)

Date: 2026-10-02/03. Status: **DONE in the clone, not promoted.** Nothing in `Frontrooms3D/` was changed
except this folder (`10_implementation.md`, `images/`, `logs/`).

All work is in the private clone
`/private/tmp/claude-501/-Users-redwang-Desktop-ArtCenter-Fall26T7-EGAM-401A-01-Individual-Game-Project/5656cffd-bc90-45f6-86a3-09b26549df8d/scratchpad/proj_glass`
(**the clone**; paths below are relative to its root). The clone is shared with the G11 ray-tracing
bench (`Assets/Editor/G11Bench`); every Unity run here waited until no other Unity had the clone open
(`glass_work/run_unity.sh` in the scratchpad). Values and plan: `interaction_audit/10_audit_report.md`
§4.1–4.3 and `Documentation/VISUAL_CHAT_TASKS.md` rows G1–G4, G6.

Tags: **UNVERIFIED** = not confirmed by a run, the code, or a page I read.

---

## 1. Short answer

| Row | Result |
|---|---|
| G1 shader | `FrontRooms/Glass` (HLSL, URP lighting): transparent, premultiplied "Alpha + Preserve Specular", ZWrite off, no shadow caster, Cull Back. Audit §4.2 values. Grime laid out in pane metres. Crack and palm hooks. Compiles offline for WebGL 2 (GLES3x) and Metal with no errors. |
| G2 grime maps | 6 CC0 ambientCG scans packed into 2 textures by a script. Desktop: BC7 1024 px and 512 px. WebGL: DXT5 at half size. |
| G3 materials | `Glass_Window` (FrontRooms/Glass + grime), `Glass_Edge` and `Glass_Shard` (URP Lit, opaque, with MotionVectors) in `Resources/Surfaces`. Made by a new editor file, plus a one-line hook in RenderSetup. |
| G4 prop glass | `Prop_Glass` and `Prop_BottleBlue` moved onto `FrontRooms/Glass` without grime. The kit look holds (§6.3). After the hook, the old generator's SrcAlpha write is overridden (checked). |
| G6 reflections | Four 256 px HDR cubes (Level0, Office, Tall, DeadLamp) captured in the **real map**, with lamps lit exactly as the game lights them. `FrontRoomsLook.SetZoneReflection` is implemented. A **play-mode test proves** that a runtime change reaches URP: a mirror sphere renders cube A, then the 0.5 s fade, then cube B. The two paths match (mean difference 0.04/255). |

Three findings change how to read the audit's numbers:

1. **Unity applies the reflection-intensity slider in gamma.** At runtime, URP's decode multiplier is
   `GammaToLinear(intensity)`: 0.5 becomes 0.214, 0.25 becomes 0.051, and today's 0.3 is only 0.073
   (`logs/reflection_test.txt`, the "decode" values and the measured 0.245 ratio against a predicted 0.238).
   So "keep intensity ≤ 0.5" means at most 21 % of the captured radiance. The audit's "tune toward 0.7–1.0"
   means 45–100 % linear.
2. **Clear glass with the audit's values is nearly invisible in these rooms, even with the grime
   maps**, as audit 05 predicted. The maps alone did not fix it. Two art-directed terms were added
   to make it read (§3.3): grime that scatters room light from both sides, and a reflection floor on
   glass only (`_ReflectionMin`, 0.6 linear on windows). Floors and walls keep the global ≤ 0.5.
3. **WebGL's automatic format for an HDR cube is DXT1, which is LDR** (importer log), so lamp
   reflections would clip at 1.0. The cubes now override WebGL to RGB9e5: HDR, 4 bytes per pixel,
   supported by desktop and mobile browsers.

---

## 2. Files (all in the clone)

| File | New / changed | Lines | What |
|---|---|---|---|
| `Assets/Resources/Rendering/FrontRoomsGlass.shader` | new | 412 | `FrontRooms/Glass` |
| `Assets/Resources/Rendering/FrontRoomsReflectionBlend.shader` | new | 78 | `Hidden/FrontRooms/ReflectionBlend`: cube crossfade, one face and mip per draw |
| `Assets/Scripts/Rendering/FrontRoomsZoneReflection.cs` | new | 340 | runtime zone reflection (snap, fade, dip, retarget) |
| `Assets/Scripts/Rendering/FrontRoomsZoneReflectionDriver.cs` | new | 11 | hidden `LateUpdate` tick, created on the first fade |
| `Assets/Scripts/Rendering/FrontRoomsGlassPane.cs` | new | 55 | map helpers: `ImpactUV(pane, hitPoint)`, `SetCrack(renderer, crack, uv, seed, palm)`, material names |
| `Assets/Scripts/Rendering/FrontRoomsLook.cs` | **changed** | 57 | `SetZoneReflection` calls `FrontRoomsZoneReflection.Set` (`:35`); `ApplyAmbient` ends with `FrontRoomsZoneReflection.Reapply()` (`:55`). Signature unchanged. |
| `Assets/Editor/Rendering/FrontRoomsGlassSetup.cs` | new | 226 | materials + texture importers; menu *FrontRooms → Rendering → Set up glass materials*; batch `FrontRoomsGlassSetup.RunBatch` |
| `Assets/Editor/Rendering/FrontRoomsReflectionCapture.cs` | new | 295 | cube capture in the real map; menu *… → Capture zone reflection cubemaps*; batch `RunBatch`, `RunImportersBatch` |
| `Assets/Editor/Rendering/FrontRoomsGlassVerification.cs` | new | 655 | play-mode proof (`RunReflectionTestBatch`, run **without** `-quit`), window and prop look-dev |
| `Assets/Editor/Rendering/FrontRoomsGlassCompileCheck.cs` | new | 79 | hook check + offline WebGL/Metal shader compile (`RunBatch`) |
| `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs` | **one line** | `:44` | `FrontRoomsGlassSetup.EnsureAll(); // GLASS HOOK (G1-G4) …`, added after `EnsureGlassMaterials();`. Nothing else in the file was touched. |
| `Tools/lookdev/pack_glass_grime.py` | new | 73 | packs the CC0 scans |
| `Assets/Resources/Surfaces/Textures/GlassGrime_M.png`, `GlassSmear_N.png` (+ .meta) | new | | packed maps (3.1 MB and 0.5 MB source PNG) |
| `Assets/Resources/Surfaces/Glass_Window.mat`, `Glass_Edge.mat`, `Glass_Shard.mat` (+ .meta) | new | | |
| `Assets/Resources/Surfaces/Prop_Glass.mat`, `Prop_BottleBlue.mat` | changed (GUID kept) | | now `FrontRooms/Glass` |
| `Assets/Resources/Rendering/Reflections/Refl_{Level0,Office,Tall,DeadLamp}.exr` (+ .meta, folder .meta) | new | | 1.1–1.3 MB EXR each |

`FrontRoomsLook.cs` and `FrontRoomsRenderSetup.cs` in the real project still match the files the clone
started from (md5 checked 00:08), so both patches apply cleanly. To promote, copy every path above
**with its `.meta`**. The shader and texture GUIDs are referenced by the materials.

---

## 3. G1 — `FrontRooms/Glass`

### 3.1 Render state and lighting

- `Blend One OneMinusSrcAlpha`, `ZWrite Off`, `Cull [_Cull]` (Back) (`FrontRoomsGlass.shader:81-83`).
  There is one pass, `UniversalForward`, and no ShadowCaster, DepthOnly or MotionVectors pass, so the
  pane casts no shadow whatever the renderer's setting.
- `#define _SURFACE_TYPE_TRANSPARENT 1` and `#define _ALPHAPREMULTIPLY_ON 1` (`:105-106`). These are
  plain defines, not keywords, so they add no variants. With premultiply on, URP multiplies only the
  diffuse by alpha (`BRDF.hlsl:71`, package `com.unity.render-pipelines.universal@37e0d4fc2503`). That
  is "Preserve Specular": lamp highlights and the environment reflection stay at full strength.
- Lighting is URP's own `UniversalFragmentPBR`, with the same `multi_compile` set as `FrontRooms/Surface`
  except SSAO (transparent surfaces do not take it). It includes Forward+ (`_CLUSTER_LIGHT_LOOP`),
  cookies, light layers and fog.
- Fog is applied for premultiplied output: toward `fogColour × alpha`, not the full fog colour (`:401`).
- SRP Batcher: every material property sits in one `UnityPerMaterial` cbuffer (`:110-139`, 200 bytes in
  the compiled variant). Each texture has its own sampler (`:140-141`), as WebGL/GLES needs.

### 3.2 Values (audit §4.2) and where they act

| Input | Value | Shader |
|---|---|---|
| Base | linear (.02, .025, .022) → `_DustColor` linear (.42, .40, .34) by dust | `:339-340` |
| Alpha | `_AlphaFace` .08 + `_AlphaFresnel` .55 × Fresnel⁵ + `_DustAlpha` .25 × dust (+ .05 × smudge, cracks) | `:341` |
| Metallic | 0 | |
| Smoothness | .96 → `_SmudgeSmoothness` .62 by smudge; → .45 by dust × .6 | `:336-338` |
| Normal | flat + `_RollStrength` .02 long-wave roll (period .37 m, phase per pane) + smear normal × `_SmudgeNormal` .05 | `:290`, `:313` |
| Edge faces | `_AutoEdge`: the four thin faces of the box use `_EdgeColor` linear (.28, .42, .34), alpha .92, smoothness .6 | `:345-348` |

**Pane frame, so that any pane size works.** In the vertex stage, the thinnest scaled object axis is
the pane normal. *v* is object up (unless the pane lies flat) and *u* is the remaining axis (`:197`).
Grime is laid out in metres from the pane centre. This matches how the map builds panes, as a scaled
unit cube with no rotation (`FrontRoomsMapWorld.cs:953-957` in the clone). A mesh modelled in metres
sets `_PaneSize`.

**Grime layout** (`_FR_GLASS_GRIME`, windows only, `:293-315`), with three samples of one RGBA map plus
one normal sample:

- dust: a thin film everywhere (0.14), dense in the bottom 14 cm, in the corners (12 cm) and along the
  glazing stop (2 cm), broken up by mottling and specks;
- smears: 0.80–1.65 m above `_FloorY` (full strength 0.95–1.45 m), in patches;
- prints: within 22 cm of the side edges, 0.85–1.75 m high, thresholded so only a few show;
- per-pane random offset, so neighbouring panes differ.

### 3.3 Two art-directed additions (not in the audit spec, needed to make the glass read)

The first look-dev ([02](images/02_window_old_vs_new.jpg), row "NEW glass") showed what audit 05
predicted: with these values the pane disappears straight-on and at 50–60°. The debug view
([03](images/03_window_close_masks.jpg), bottom left) confirms the masks are in the right places. They
were just too faint to see. Two additions:

- **`_Scatter` (window: 3).** Dust, smudges and crack lines add the room's ambient light from *both*
  sides of the pane as emission: `(dust + .6·smudge + 3·crack + 2·crush) × dustColour × ½(SH(n) + SH(−n))`
  (`:380`). Dust on real glass is lit from both sides. Without this term it can only darken.
- **`_ReflectionMin` (window: 0.6 linear; props: 0.45).** The global default reflection stays ≤ 0.5 on
  the slider, which is 0.214 linear. On glass only, the shader tops the environment reflection up to
  `_ReflectionMin`. It reads the current linear intensity from URP's `_GlossyEnvironmentCubeMap_HDR.x`
  (`Input.hlsl:103`) and adds `(min / current − 1)` × the env-BRDF reflection (`:389-399`). It
  self-adjusts: once the global intensity rises to 0.6 or more, it adds nothing. It skips
  RGBM-encoded cubes (`.w ≠ 0`). Cost: one extra cube sample on glass pixels.
- Also `_GrimeDebug` (`:403`) shows the masks: R dust, G smudge, B crack.

The result reads as glass at 0.7 m (smear streaks and a dust haze) and still looks clear at 1.5 m. It
is clearly less veiled than today's pane at 50° ([02](images/02_window_old_vs_new.jpg), rows 1 vs 3;
[03](images/03_window_close_masks.jpg), top row against the no-pane reference). **Red must judge it.**
These are look-dev frames in an edit-mode build of the map, not the G10 harness capture.

### 3.4 Crack and palm hooks (placeholder until G8's baked masks)

`_Crack` (0–1) is the reach of 9–14 radial cracks from `_ImpactUV`. They meander slightly and differ in
length per ray (seed `_CrackSeed`). Ring segments appear at `_Crack` 0.30, 0.55 and 0.80, plus a
crushed spot at the impact. Each wedge between two cracks tilts by up to ±0.03, so the reflection breaks
into facets (`CrackMask`, `:220`). `_Palm` (0–1) draws a hand smudge (heel, four fingers, thumb) at
`_ImpactUV` (`PalmMask`, `:253`).

Both are ALU only, behind a uniform `[branch]`, so a pane at 0 pays nothing. The lines are
anti-aliased with the pixel footprint in metres (no derivatives inside the branch). One bug was found
and fixed: the projection's `_m11` is negative when rendering into a flipped target, which made the
cracks render as solid wedges. The code now uses `abs()`. Frames: [04](images/04_crack_palm_hooks.jpg).
The palm reads only faintly. That matches the push stage in §3.5 of the audit, but it may need more
strength once the shot exists.

The map drives the hooks with `FrontRoomsGlassPane.SetCrack(paneRenderer, crack, FrontRoomsGlassPane.ImpactUV(pane, hit.point), seed, palm)`.
That call uses a property block on that one renderer. The renderer leaves the SRP Batcher only while
it is cracked.

---

## 4. G2 — grime maps

Sources: ambientCG, CC0 1.0, approved by Red on 2026-10-02 and listed in
`Frontrooms3D/Tools/lookdev/cc0_src/SOURCES.txt`: Smear007, Fingerprints002, SurfaceImperfections001,
007, 013 and 015 (`https://ambientcg.com/a/<name>`; the URLs come from SOURCES.txt and were not
re-opened). No attribution is required. The 1K JPG zips were read from the real project's git-ignored
`Tools/lookdev/cc0_src/ambientcg/` (read-only).

`python Tools/lookdev/pack_glass_grime.py <cc0_src> Assets/Resources/Surfaces/Textures` stretches each
channel between its 2nd and 99.5th percentiles:

| Texture | Channels | Desktop import | WebGL override |
|---|---|---|---|
| `GlassGrime_M.png` 1024² RGBA, linear | R Smear007 opacity · G Fingerprints002 opacity · B max(SI007, 0.7·SI013) specks · A 0.6·SI015 + 0.4·SI001 mottling | BC7, 1024, mips, trilinear, aniso 4, repeat | DXT5, 512 (≈ 0.35 MB with mips) |
| `GlassSmear_N.png` 512² | Smear007 NormalGL | normal map, BC7, 512 | DXT5, 256 (≈ 0.09 MB) |

(Formats from `[FrontRoomsGlass]` lines in the setup log. WebGL sizes are computed, not measured in a
build.)

---

## 5. G3, G4 — materials

`FrontRoomsGlassSetup.EnsureAll()` writes all five materials in place (GUIDs kept). Colours are set as
`Color.gamma` of the linear values, because material colours are sRGB and URP linearises them.

| Material | Shader | Values |
|---|---|---|
| `Glass_Window` | FrontRooms/Glass + `_FR_GLASS_GRIME` | base lin (.02, .025, .022); alpha .08 + .55 F⁵; dust alpha .25; smoothness .96 → .62; roll .02 @ .37 m; smudge normal .05; dust/smear/prints 1; `_FloorY` 0; `_AutoEdge` on, edge lin (.28, .42, .34), α .92, smoothness .6; `_Scatter` 3; `_ReflectionMin` .6; queue 3000 |
| `Glass_Edge` | URP Lit, opaque | base lin (.28, .42, .34), smoothness .6, metallic 0 |
| `Glass_Shard` | URP Lit, opaque | base lin (.02, .025, .022), smoothness .95. Shard meshes need two material slots: faces `Glass_Shard`, edges `Glass_Edge`. URP Lit keeps its MotionVectors pass. |
| `Prop_Glass` | FrontRooms/Glass, no grime | base lin (.02, .025, .022); alpha .10 + .55 F⁵; smoothness .94; roll 0; `_ReflectionMin` .45 |
| `Prop_BottleBlue` | FrontRooms/Glass, no grime | base sRGB (.36, .58, .80) (unchanged hue); alpha .30 + .50 F⁵ (was a flat .42); smoothness .90; `_ReflectionMin` .45 |

**G4: which option was taken.** Both props were moved onto the glass shader. The old generator
`FrontRoomsRenderSetup.EnsureGlassMaterials` still runs first and still writes URP Lit with SrcAlpha.
The hook then overrides it. `FrontRoomsGlassCompileCheck` ran exactly that order:
`Prop_Glass = Universal Render Pipeline/Lit` after the old pass, and `FrontRooms/Glass`, no stray
keywords, queue 3000 after the hook (`logs/compile_check.txt`). `EnsureGlassMaterials` and `GlassDefs`
are now dead code. Delete them once the wallpaper workflow's edits to RenderSetup have landed (owner:
visual).

**Kit look** ([05](images/05_props_old_vs_new.jpg)): the cabinet, vending front and clock glass read
clearer and darker. The interiors show through instead of a pale veil. The hutch doors now read as dark
glass over a dark interior. The water-cooler bottle is a little more saturated. Nothing reads as broken,
but Red should look at the hutch.

---

## 6. G6 — zone reflection cubes and `SetZoneReflection`

### 6.1 Capture (`FrontRoomsReflectionCapture.RunBatch`)

1. An edit-mode build of the shipped profile's map (seed 20261001, 25 chunks, 1,597 lamps) through the
   map's own `BuildForCapture`.
2. One cell is picked per zone type (`logs/reflection_capture.txt`):

   | Cube | Cell | Why |
   |---|---|---|
   | `Refl_Level0` | (1, 4) | Level0/Standard, own lamp steady, 8 of 8 neighbours lit |
   | `Refl_Office` | (−5, 21) | Office/Standard, steady, 8/8 lit |
   | `Refl_Tall` | (14, −15) | Level0/Tall, steady, 4/7 lit |
   | `Refl_DeadLamp` | (1, 6) | Level0/Standard, own lamp **dead** (mode 3), 8/8 neighbours lit |

   Cells with anything within 0.45 m of the capture point are skipped.
3. The lamps are lit as the game lights them with the player standing there. The tool calls the map's
   own private `TickFixtures` (temperaments, the 16 m light radius, the nearest-9 m shadow set):
   60–87 lamps on within 16 m, 7–11 of them shadowed.
4. A 256 px HDR cube is baked at eye height (1.62 m) with a Custom `ReflectionProbe` that also renders
   dynamic objects, through `Lightmapping.BakeReflectionProbe` (URP renders the faces; Unity writes the
   EXR and convolves its mips). Settings: solid clear to the fog colour; reflections off inside the
   capture (first bounce only); no post.
5. Importer: Cube, Specular convolution, 9 mips, BC6H at 256 on desktop, **RGB9e5 at 128 on WebGL**
   (§1 point 3; Unity 6.3 manual, *GPU texture formats reference*, lists RGB9e5 for desktop and mobile
   browsers; BC6H falls back to RGBA Half on macOS browsers).

Previews: the mirror spheres in [01](images/01_reflection_proof.jpg) (Level0: wallpaper and troffers;
Office: grey carpet and windows; Tall: high lamps; DeadLamp: no lens overhead).

**Caveat (wallpaper chat).** Each cube holds a frozen copy of the wallpaper print. The print will
animate later, so reflection intensity on wall-facing glossy surfaces stays modest: ≤ 0.5 on the slider
(0.214 linear) for everything, and 0.6 linear on window glass, where the print reflects at roughly 4 %
(Fresnel) face-on.

**Brittle point.** The capture tool reads `FrontRoomsMapWorld.built`, `BuiltChunk.fixtures` and
`TickFixtures` by reflection. If the map chat renames them, the tool logs an error and captures
nothing. The game is unaffected.

### 6.2 Runtime (`FrontRoomsZoneReflection.cs`)

- **How it reaches URP 17.** It sets `RenderSettings.defaultReflectionMode = Custom` and
  `RenderSettings.customReflectionTexture = cube` (`customReflection` is deprecated in favour of
  `customReflectionTexture` in this engine; found in `UnityEngine.CoreModule.dll` strings).
  - With probe blending off (today, `FrontRooms_URP.asset:54`), Forward+ asks for per-object probe data
    (`UniversalRenderPipeline.cs:2092-2098`), and renderers without a probe sample it as
    `unity_SpecCube0` (`GlobalIllumination.hlsl:446`).
  - With blending on (G7), URP binds it per camera as `_GlossyEnvironmentCubeMap` from
    `ReflectionProbe.defaultTexture` (`UniversalRenderPipeline.cs:2201-2202`; used at
    `GlobalIllumination.hlsl:409-415`).
  - The test logs `ReflectionProbe.defaultTexture` switching to our texture at runtime.
- **Blend mode (desktop).** One HDR cube render texture (RGB111110Float, 256 px, 9 mips, about 2.1 MB)
  stays bound for the whole run. A zone change redraws it each frame as lerp(from, to) for every face
  and mip, which is 54 tiny draws per frame and only while a fade runs. The mips are already convolved,
  so lerping each mip is exact. Intensity lerps with it. A retarget in the middle of a fade first
  freezes the current mix into a second render texture (allocated only then), so nothing pops.
- **Dip mode (WebGL, or no HDR render texture).** Intensity fades to 0, the cube asset is swapped at the
  midpoint, and intensity fades back. This touches only `RenderSettings`, so it does not depend on
  render-to-cube support in the browser.
- **API.** `SetZoneReflection(zone, blendSeconds = .5f)`:
  - Calling it every frame with the same zone is a no-op (`FrontRoomsZoneReflection.cs:103`).
  - The first call, any call outside Play mode, and `blendSeconds` 0 switch at once.
  - `SetImmediate(zone)` always snaps (for captures and tests).
  - Intensities: Level0 .5, Office .5, Tall .45, DeadLamp .5, clamped to `MaxIntensity` .5 (`:35-38`).
  - `ApplyAmbient()` re-applies the zone, so the map can call the two in either order.

### 6.3 Play-mode proof (`FrontRoomsGlassVerification.RunReflectionTestBatch`, Metal, M3 Max)

Setup: an empty scene in Play mode, two metal spheres (mirror, and smoothness .6), no lights, black
ambient, post off. Every pixel is the default reflection. Results from `logs/reflection_test.txt`
(the last run, 23:59; identical to the two earlier runs); frames in
[01](images/01_reflection_proof.jpg):

| Check | Result |
|---|---|
| Before any call | mode Skybox, `defaultTexture` = Default-Skybox-Cubemap |
| `SetZoneReflection(Level0)` (first call, snap) | mode Custom, `defaultTexture` = our render texture; image differs from the sky by 14.9/255 mean |
| Same zone again | no fade started |
| `SetZoneReflection(Office, .5)`: t = 0 | identical to Level0 (0.00/255) |
| … t = 0.25 s | between the two (1.79/255 from A, 1.43/255 from B) |
| … t = 0.67 s | fade finished; mirror mean (.212, .193, .147) vs Level0 (.223, .187, .093) |
| Render-texture path vs the plain cube asset (same zone) | **0.04/255 mean, max 1/255** (orientation and HDR decode correct on Metal) |
| Same, with the face rows flipped | 3.56/255, image upside down: rejected, `FlipY = false` |
| Intensity 0.50 → 0.25 | sphere ratio 0.245 / 0.238; predicted `GammaToLinear` ratio 0.238. Decode x 0.214 → 0.051 |
| `ApplyAmbient()` afterwards | identical (0.00/255): cube and intensity kept |
| Dip mode, 0.25 s | near black (intensity 0.024), cube already swapped |
| Dip mode, end | matches the render-texture path for DeadLamp (0.03/255) |
| Retarget Office → Tall mid-fade | frame before = frame after the call (0.00/255); end = Tall snapped (0.00/255) |

---

## 7. WebGL notes, and the "full detail only where the player looks" question

What this work costs, per the shader compile check (`logs/compile_check.txt`: GLES3x for
`BuildTarget.WebGL`, 0 errors on every tested keyword set) and computed sizes:

- **Per pane:** one transparent draw (SRP Batcher), no depth, shadow or motion pass. Fragment cost is
  URP lighting + 3 grime samples + 1 normal + 1 extra cube sample (`_ReflectionMin`). The heaviest WebGL
  variant uses 7 of 16 texture units. Cost scales with **pixels covered**, not with pane count: a pane
  10 m away covers a few hundred pixels. So glass needs no LOD tier of its own until a browser profile
  says otherwise (UNVERIFIED: nothing was measured in a browser).
- **Overdraw:** one layer per pane (Cull Back on the closed box), two where windows line up.
- **Crack/palm:** zero cost unless the property block sets them, and only on the held pane.
- **Variants:** one new local keyword (`_FR_GLASS_GRIME`, `shader_feature_local_fragment`, so only used
  combinations ship). The rest is URP's set, mirrored from `FrontRooms/Surface`. No new global keywords.
- **Memory:**
  - WebGL: cubes 4 × 128 px RGB9e5 ≈ 4 × 0.52 MB; grime ≈ 0.44 MB.
  - Desktop: cubes 4 × 0.52 MB BC6H, plus the 2.1 MB blend texture (and 2.1 MB more only after a
    mid-fade retarget).
  - The EXR sources are 1.1–1.3 MB each on disk. The built size per platform is UNVERIFIED (no build
    was made).
- **Reflections on the Web tier stay at step 0:** one global cube per zone type and no per-room probes
  (G7 is desktop only, as the audit says). Never realtime probes or planar mirrors on WebGL.

How this fits the WG3/WG4 rows (a detail manager that keeps full detail only where the player can see,
without visible switches):

- Zone reflections are already "one per visible zone": the map calls `SetZoneReflection` from the
  player's cell and lamp state, and the 0.5 s fade hides the switch.
- On WebGL the switch is a dip, not a crossfade. Keep `blendSeconds` ≥ 0.4 so the dip reads as a lamp
  flicker rather than a pop. This is a design note, untested in a browser.
- Per-room probes (G7) are where "only near rooms" matters. Enable them for the nearest 8–12 rooms
  only, with the zone cube as the fallback. A probe that leaves the set then falls back to a cube that
  is already shown.
- Not verified here: the dip and blend paths in a real browser (the render-to-cube path is disabled on
  WebGL on purpose); `FlipY` on GL-family targets (only relevant if someone enables the blend path on
  WebGL); and frame time anywhere except this editor.

---

## 8. Not done, and contracts for other chats

**Map chat (G9; reads this, does not need this workflow):**

- Load `Resources.Load<Material>("Surfaces/Glass_Window")` (`FrontRoomsGlassPane.Window`), and keep
  `TransparentGlass` as the fallback.
- Keep the pane a scaled unit cube with no rotation, or set `_PaneSize`.
- Use a thickness of 6 mm and turn shadows off on the renderer.
- The smear band assumes the floor is at world y = `_FloorY` (0). If the map root ever moves vertically,
  set `_FloorY` on the material.
- Call `FrontRoomsLook.ApplyAmbient()` and `SetZoneReflection(zone)` at run start, then on zone and
  dead-lamp changes. Every frame is fine.
- Drive the cracks with `FrontRoomsGlassPane.SetCrack` and `ImpactUV`.

**Not done:**

| Item | Why / where |
|---|---|
| G5 `Kit_InteriorWindow` onto the glass shader | out of scope (queued after G1) |
| G7 per-room probes | desktop tier; the shader already reads `_GlossyEnvironmentCubeMap_HDR`, which stays valid with blending on |
| G8 fracture variants, G10 harness capture (seed 4242, frames 01/04/23/34/35 + dead lamp) | not run; the look-dev here is **not** the G10 sign-off |
| Title-stream cubes (Lobby, Shift, Office, Run in red, Exit in cyan) | the fixed API has 4 zones; owner: RoomStream |
| `FrontRoomsRenderSetup.RunBatch` end to end | not run (it rewrites ~86 materials and the URP asset in a clone shared with G11); the hook order was checked directly instead (§5) |
| Promotion to `Frontrooms3D/` | not done by this workflow |

**Risks:**

- `_ReflectionMin` and `_Scatter` are art-directed numbers chosen from 5 look-dev frames. Red should
  tune them in the G10 capture.
- The prop materials now use a custom shader, so URP's material upgrader and inspector will not manage
  them.
- WebGL is UNVERIFIED in a browser (§7).

---

## 9. Sources and method

- **Package source** (clone `Library/PackageCache`, URP `@37e0d4fc2503`, core `@04ab0eefa0c3`):
  - `UniversalRenderPipeline.cs:2084-2098, 2189-2203`
  - `ShaderLibrary/GlobalIllumination.hlsl:34-40, 286-455`
  - `ShaderLibrary/BRDF.hlsl:65-72, 157`
  - `ShaderLibrary/Input.hlsl:103-105`
  - `ShaderLibrary/ShaderVariablesFunctions.hlsl:239-280, 452`
  - `ShaderLibrary/Clustering.hlsl:9`
  - `Shaders/Lit.shader` (ForwardLit pragmas)
  - core `ShaderLibrary/Sampling/Sampling.hlsl:58-108` (cube face basis)
  - core `ShaderLibrary/EntityLighting.hlsl:194`
- **Offline Unity 6000.3 docs** (`/Applications/Unity/Hub/Editor/6000.3.10f1/Documentation/en/`):
  - `ScriptReference/RenderSettings-customReflection.html`
  - `Lightmapping.BakeReflectionProbe.html`
  - `ReflectionProbe-defaultTexture.html`
  - `ReflectionProbe-defaultTextureHDRDecodeValues.html`
  - `TextureImporter.GetAutomaticFormat.html`
  - `ShaderData.Pass.CompileVariant.html`
  - `Rendering.ShaderCompilerPlatform.html`
  - `Manual/texture-formats-reference.html`
  - `Manual/webgl-texture-compression.html`
- **Web:** no web pages were read for this work.
- **Runs** (logs in the scratchpad `glass_work/logs/`, results copied to `logs/` here):
  - setup ×4, capture ×1, importers ×2;
  - the play-mode proof ×3 (the first timed out after finishing all checks, because of a test-exit bug
    that is now fixed);
  - window look-dev ×4, prop look-dev ×1, compile check ×4.
- **Full-resolution frames:** `<clone>/Verification/glass/*.png` (temporary).
