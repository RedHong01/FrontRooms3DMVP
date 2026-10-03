# 02 — Glass and breakables audit

Status: IN PROGRESS (written incrementally). Sections 2–4 are verified against the code; 5–9 are being filled.
Date: 2026-10-02. Scope: every glass material in FrontRooms, the URP settings that decide how glass can look, and the hold-to-break window interaction.

Line numbers: other chats were editing `FrontRoomsMapWorld.cs` and `FrontRoomsSoundDirector.cs` while this audit ran (MapWorld was saved at 20:37 and lines moved by about 9). Every `file:line` below was re-read at about 20:45 on 2026-10-02. If a line has moved, search for the quoted identifier.

## 1. Summary

(pending — written last)

## 2. Pipeline and platform facts that limit glass

| Setting | Value | Where | What it means for glass |
|---|---|---|---|
| Render pipeline | URP 17.3.0, Forward+ | `Packages/manifest.json` (URP 17.3.0); `Assets/Settings/FrontRooms_URP_Renderer.asset:50` (`m_RenderingMode: 2` = Forward+) | Forward+ is fine for many lights. URP has no screen-space reflections (see §6). |
| Pipeline asset on all 6 quality levels | `FrontRooms_URP.asset` (guid 9f471c95…) | `ProjectSettings/QualitySettings.asset:51,104,157,210,263,316`; `ProjectSettings/GraphicsSettings.asset:40` | Every quality level uses the same URP asset, so "Ultra" and "Low" look the same in URP terms. Quality levels only change the built-in settings (texture mip limit, anisotropy, realtime probes, LOD bias). |
| Current editor quality level | 3 = "High" | `QualitySettings.asset:7`; WebGL default 3, Standalone default 5 (`:338-339`) | "High" has `realtimeReflectionProbes: 1` (`:187`). That does nothing, because there are no probes. |
| Opaque texture | **Off** | `FrontRooms_URP.asset:23` (`m_RequireOpaqueTexture: 0`) | Refraction is not possible. A glass shader cannot sample `_CameraOpaqueTexture` to bend or blur what is behind it. |
| Depth texture | On | `FrontRooms_URP.asset:22` | Available for soft-particle shards and depth-faded dust. |
| HDR | On, default precision | `FrontRooms_URP.asset:26-27` | Highlights on glass can go above 1 and bloom (bloom threshold 1.05, `FrontRoomsRenderSetup.cs:197`). |
| MSAA | 4x | `FrontRooms_URP.asset:28`; camera AA post-filter is None (`FrontRoomsPostStack.cs:72`) | MSAA smooths geometric edges of panes and shards. It does not smooth specular aliasing on a mirror-smooth pane. |
| Reflection probe blending | **Off** | `FrontRooms_URP.asset:54` | Each renderer takes one probe only (`unity_SpecCube0`). |
| Reflection probe box projection | **Off** | `FrontRooms_URP.asset:55` | Even if probes existed, reflections would be "at infinity": they would not line up with the room's walls. |
| Reflection probe atlas | On | `FrontRooms_URP.asset:56` | Only used when blending is on. |
| Reflection probes in scenes | **None** | No `ReflectionProbe:` component in any `.unity` or `.prefab` under `Assets` (grep). The 16 hits for "ReflectionProbe" in `FrontRooms3D.unity` are the `m_ReflectionProbeUsage` field on renderers, not probes. No script creates a `ReflectionProbe` (grep of `Assets/Scripts`, `Assets/Editor`). | Glass can only reflect the scene's default environment cubemap. |
| Skybox | **None** in every scene, and cleared at runtime | `FrontRooms3D.unity:29`, `FrontRoomsMapTest.unity:29`, `FrontRoomsLevelDesigner.unity:29` (`m_SkyboxMaterial: {fileID: 0}`); `FrontRoomsMapWorld.cs:491` (`RenderSettings.skybox = null`) | The default reflection source is "Skybox" (`m_DefaultReflectionMode: 0`, `FrontRooms3D.unity:35`), but there is no skybox. The environment cubemap is therefore black or near-black (UNVERIFIED exact content; see §4.1). |
| Reflection intensity | 0.3 | `FrontRoomsLook.cs:20,30`; `FrontRooms3D.unity:38` | The (empty) environment reflection is scaled down further to 30%. |
| Baked lighting | None | `m_LightingDataAsset: {fileID: 20201, guid: 0000000000000000f…}` in all three scenes (`FrontRooms3D.unity:96`) = Unity's empty default | No baked probes, and the map is generated at runtime, so per-room probes cannot be baked in the editor anyway (see §6). |
| Fog | Exp² 0.014 | `FrontRoomsLook.cs:18-19,31-34` | Fog is applied to transparent URP Lit too; fine. |
| Active build target (editor) | StandaloneOSX (decoded from the binary `Library/EditorUserBuildSettings.asset`: active target 2, group "Standalone") | — | Red is judging the look in the editor on an Apple M3 Max (Metal), per `~/Library/Logs/Unity/Editor.log` lines 136-140. The editor is not GPU-limited. |
| Builds on disk | `Builds/Mac` and `Builds/WebGL` are **stale** (Oct 1). The Mac `Assembly-CSharp.dll` has no `FrontRoomsMapWorld` class and its `Managed` folder has no URP assembly. | `Builds/Mac/Frontrooms3D.app/Contents/Resources/Data/Managed` | Neither build shows the current map or glass. Do not judge glass from them. |
| macOS build menu removes URP | `BuildMac()` sets `GraphicsSettings.defaultRenderPipeline = null` and `QualitySettings.renderPipeline = null` before building | `Assets/Editor/FrontRooms3DBuild.cs:61-62` | **A macOS build made from this menu ships the Built-in pipeline, not URP.** FrontRooms/Surface is URP-only, so such a build would lose the whole look. This alone can make a build look "low level". (It also leaves the editor without a pipeline until someone re-runs Rendering setup.) |
| WebGL build menu | Switches target to WebGL and forces quality level 3 | `FrontRooms3DBuild.cs:86,159` | The WebGL target is real and must set the budget (see §6.6). |

## 3. Glass material inventory

Shader abbreviations: **URP Lit** = `Universal Render Pipeline/Lit`; **FR Surface** = `FrontRooms/Surface` (`Assets/Resources/Rendering/FrontRoomsSurface.shader`), an opaque world-projected PBR shader (`Tags Queue=Geometry`, `ZWrite On`, `:46,83-85`) that calls `UniversalFragmentPBR` with `alpha = 1` (`:243-255`).

| Material | Used by | Shader / surface | Blend | Base colour (alpha) | Smoothness / metallic | Spec. highlights / env. reflections | Queue / ZWrite | Cull | Shadow caster | Geometry |
|---|---|---|---|---|---|---|---|---|---|---|
| **Map test / glass** (runtime) | Every map window pane | URP Lit, Transparent (`FrontRoomsMapWorld.cs:1662-1677`) | SrcBlend One, DstBlend OneMinusSrcAlpha, `_ALPHAPREMULTIPLY_ON`, `_Blend 0` (`:1667-1675`). This is URP's "Alpha + Preserve Specular" set by hand. Alpha channel blend stays at the shader defaults One/Zero (`Lit.shader:54-55`). | (.75, .85, .88, **.28**) (`:1659`) | .90 / 0 (`:1666`) | On / On (shader defaults `Lit.shader:22-23`) | 3000 / Off (`:1670,1676`) | Back (default `Lit.shader:50`) | **Enabled** (never turned off; the cube from `CreatePrimitive` casts shadows by default) | `CreatePrimitive(Cube)` scaled to 1.40 × 1.65 × **0.030 m** (`:900-905`; sizes `FrontRoomsModuleUnits.cs:59`). A closed box: back-face culling shows only the faces turned to the camera, so one glass surface is lit, not two. |
| **Prop_Glass** | Hutch, Hutch_Cherry, DisplayCabinet, VendingMachine, WallClock (slots in `Assets/Resources/Props/Models/*.json`) | URP Lit, Transparent (`Assets/Resources/Surfaces/Prop_Glass.mat:11-23`) | Saved as SrcBlend **1** (One), `_ALPHAPREMULTIPLY_ON`, `_BlendModePreserveSpecular 1` (`:15,94,116`). The generator asks for SrcAlpha (`FrontRoomsRenderSetup.cs:414`), but URP's material validation rewrites it to One + premultiply because Preserve Specular defaults to 1 (`BaseShaderGUI.cs:1098-1114` in the URP package). | (.82, .88, .88, **.16**) (`.mat:123`) | .92 / 0 (`:113,108`) | On / On (`:115,104`) | 3000 / Off (`:21,121`) | Back (`:98`) | Disabled, with DepthOnly and MotionVectors (`:24-27`; URP disables ShadowCaster for transparent Lit, `BaseShaderGUI.cs:777-800`) | Kit meshes; panes are single quads or 8 mm boxes (e.g. `display_cabinet.py:104`, `vending_machine.py:161`). |
| **Prop_BottleBlue** | WaterCooler bottle and cold tap | Same as Prop_Glass (`.mat` differs only in colour and smoothness) | Same | (.36, .58, .80, **.42**) | .90 / 0 | On / On | 3000 / Off | Back | Disabled | Kit mesh. |
| **Office_BlackedGlass** | Title corridor (RoomStream) gurney wheels and exit-sign housings (`FrontRoomsRoomStream.cs:1398,1468,1478`) | FR Surface, opaque (`Office_BlackedGlass.mat:11`) | Opaque | (.018, .02, .022) | .95 / 0 (`:60,58`) | Always on (FR Surface has no toggles) | 2000 / On | Back | Yes | Boxes. Despite the name it is not used as glass anywhere now; it is a near-black gloss paint. |
| **Prop_GlassCRT** | Kit_InteriorWindow pane, Kit_DeskPhone display | FR Surface, opaque (`Prop_GlassCRT.mat:11`) | Opaque | (.059, .078, .071) | .84 / 0 (`:61,59`) | Always on | 2000 / On | Back | Yes | Interior window: one single-sided quad, 6 mm nominal (`interior_window.py:54,92`). The script itself says the window "reads as a framed black slab" (`interior_window.py:31-34`). |
| **Troffer_Lens** | Level 0 and Office fixture lenses (`FrontRoomsSurfaces.cs:43-48`) | FR Surface, opaque, emissive (`Troffer_Lens.mat:11-16`) | Opaque | white × albedo map | **1.0** (no mask map, `_MaskMap` = white default → `mask.r * _Smoothness` = 1, `FrontRoomsSurface.shader:17,207`) / 0 | Always on | 2000 / On | Back | Lens renderer has shadows off (`FrontRoomsMapWorld.cs:1045`) | Primitive cube. A prismatic or opal acrylic lens is not mirror-smooth; smoothness 1 gives a pin-sharp reflection on a diffuser. Minor, because emission (2.2, 2.1, 1.8) dominates. |
| **Office_Louver** | `ParabolicLouver` only (`FrontRoomsSurfaces.cs:49`); the map now uses the frosted lens instead | FR Surface, opaque, emissive, metallic .85 | Opaque | white × map | 1.0 × mask / .85 | Always on | 2000 / On | Back | — | Mesh UV. A metallic louver reflects the environment cubemap. With no probes it reflects black, which is why metal louvers look dead. |
| **Map / Level 0 lens** (runtime) | Map fixture fallback (`FrontRoomsMapWorld.cs` `BuildMaterials`) | URP Lit, opaque, emissive (`FrontRoomsSurfaces.cs:86-101`) | Opaque | (1, .98, .92) | .10 / 0 | On / On | 2000 | Back | Off on the lens renderer | Cube. |
| **Map test / key** (runtime) | Zone keys | URP Lit, opaque, emissive (`FrontRoomsMapWorld.cs:1658`) | Opaque | (.96, .87, .23) | .40 / 0 | On / On | 2000 | Back | Yes | A cube 0.32 × 0.12 × 0.12 m (`:730-736`). Not glass, listed because Red named it. |

Glass slot colours in Blender (`Tools/Blender/frontrooms_kit/kitlib.py:72-80,169-170`) use Transmission 0.85 and roughness 0.05 for preview only; they do not reach Unity (the importer remaps slots to `Resources/Surfaces/<slot>.mat`, `FrontRoomsKitImporter.cs:8-15`).

## 4. Why the map window reads wrong

The brief listed four possible causes. Two are wrong and two are right; the real problem is a fifth one.

### 4.1 The main cause: the glass has nothing to reflect

- URP Lit with Preserve Specular **does** keep its reflections at full strength. In the shader, only the diffuse part is multiplied by alpha (`BRDF.hlsl:65-72` in the URP 17.3 package: "we only alpha blend the diffuse part"), and the blend is One / OneMinusSrcAlpha. So "premultiplied alpha with low alpha hides the reflection" is **not** what is happening.
- URP Lit **does** have a Fresnel term on reflections: `fresnelTerm = Pow4(1 - NoV)` lerps F0 (0.04 for a dielectric) toward a grazing value (`GlobalIllumination.hlsl:514-519`, `BRDF.hlsl:157-167`). So "no Fresnel" is also **not** the cause.
- What the pane reflects is `unity_SpecCube0` (`GlobalIllumination.hlsl:445-448`), with no probe, which is the default environment reflection. That is built from the skybox, and there is no skybox (§2). On top of that, `reflectionIntensity` is 0.3. So a perfect glass shader would still mirror black. At normal incidence that is 4% of black; at grazing angles it is up to 100% of black. **The pane can only show the troffer highlights.** The direct specular highlight from each spot light is the only "reflection" on screen.
- UNVERIFIED: whether Unity 6 fills the default cubemap with black or with the camera's clear colour when the skybox is null. Either way it carries no room detail.

### 4.2 The pane is a flat tinted veil

- Alpha .28 over a (.75, .85, .88) albedo means 28% of a pale blue-grey diffuse colour is laid over the room behind. Real clear float glass has no diffuse colour at all: it transmits about 90% and reflects about 4–8% (see §5). The .28 veil is what reads as "plastic film" or "frosted sheet". The kit's Prop_Glass at .16 has the same problem, less strongly.
- The pane is lit by the same troffers as the walls, so it gets brighter and darker like a painted surface, not like a window.

### 4.3 Thickness and edges

- The map pane is 30 mm thick (`FrontRoomsModuleUnits.cs:59`), 5× real 6 mm glass. The jambs hide the vertical edges (jamb depth = wall 0.16 m + 2 × 0.02 m, `FrontRoomsMapWorld.cs:860-866`: two jambs and a head only), but the **bottom edge sits on the bare sill block** (`FrontRoomsMapWorld.cs:853` builds the wall piece under the opening; there is no sill trim, stop or glazing bead), so the 30 mm edge face is visible from above.
- The edge faces use the same material, so they are as transparent as the face. Real glass edges look green and nearly opaque because light travels the long way through iron oxide. Nothing here imitates that.
- No glazing stop, bead or putty line: the glass just ends at the jamb. That is the strongest "game prototype" cue on the window.

### 4.4 Shadows and sorting

- The runtime glass keeps its ShadowCaster pass and the primitive casts shadows. About a third of map fixtures cast soft shadows near the player (`FrontRoomsMapWorld.cs:1068,1121-1122`). When one of those is near a window, the "transparent" pane drops a **solid** shadow on the floor. Prop_Glass avoids this only because URP's editor validation turned the pass off.
- Transparent queue, no depth write: shards or particles drawn after it will sort by object centre. Fine for one pane, a problem for shards inside the frame (see §8).

### 4.5 Why the whole frame reads as "low render level"

This affects more than glass, but it is the same cause and Red named it:

1. No reflections anywhere. Gloss paint (Office_BlackedGlass .95), chrome (Prop_Chrome .85 metallic), brass, aluminium and the metallic louver all reflect the same black cubemap. Metals with black reflections look like dark plastic. This is the single largest "not AAA" cue in an interior.
2. Ambient is a flat trilight colour (`FrontRoomsLook.cs:24-29`), not a probe, so there is no directional bounce.
3. Every surface material is opaque PBR with world-projected tiling: good. The issue is light transport, not textures.
4. The macOS build path strips URP (`FrontRooms3DBuild.cs:61-62`).

## 5. Target glass spec (1990 office interior window / door lite)

(pending)

## 6. Reflections in URP 17 — options and cost

(pending)

## 7. Breakage research

(pending)

## 8. FrontRooms hold-to-break design

(pending)

## 9. Remediation plan by owner

(pending)

## 10. Sources

Code (read directly, URP package at `Library/PackageCache/com.unity.render-pipelines.universal@37e0d4fc2503`, version 17.3.0 per its `package.json`):
- `ShaderLibrary/BRDF.hlsl:65-72,157-167`, `ShaderLibrary/GlobalIllumination.hlsl:34-40,420-455,514-519`, `ShaderLibrary/Clustering.hlsl:9`, `Shaders/Lit.shader:22-23,48-57,106-108,125-163`, `Editor/ShaderGUI/BaseShaderGUI.cs:777-800,1098-1114`, `Runtime/UniversalRenderPipeline.cs:1972-1975`, `Runtime/Data/UniversalRenderPipelineAsset.cs:1418-1425`, `Runtime/RendererFeatures/` (no SSR feature).

Web: (pending)
