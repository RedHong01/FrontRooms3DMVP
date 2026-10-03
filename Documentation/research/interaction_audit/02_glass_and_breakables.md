# 02 — Glass and breakables audit

Status: DONE (2026-10-02). Read-only audit: no project file was changed except this report.
Scope: every glass material in FrontRooms, the URP settings that decide how glass can look, and the hold-to-break window interaction. Sibling reports: `01_interaction_inventory.md` (all interactions, incl. keys and the camera), `03_rendering_quality.md` (whole-frame render quality), `04_aaa_references.md`.

Line numbers: other chats were editing `FrontRoomsMapWorld.cs` (saved 20:37), `FrontRooms3DGame.cs` (saved 20:45) and `Audio/FrontRoomsSoundDirector.cs` (saved 20:48) while this audit ran, and lines moved by 4–15. Every `file:line` below was re-read between 20:40 and 21:00 on 2026-10-02. If a line has moved, search for the quoted identifier.

Tags: **UNVERIFIED** = not confirmed from code or a page I read. **ESTIMATE** = my engineering estimate, not a measured number.

---

## 1. Summary

**What Red sees is right, and the cause is mostly not the glass shader.**

1. **The glass has nothing to reflect.** No scene has a reflection probe, no scene has a skybox, and the environment reflection is scaled to 0.3. Every glossy surface in the game (glass, chrome, brass, the gloss paint, the metallic louvers) reflects a black or empty cubemap. The only "reflection" on a window is the highlight of each troffer. This is the largest single reason the frame does not read as AAA. (§2, §4.1)
2. **Two causes in the brief are wrong.** URP's "Alpha + Preserve Specular" mode, which the map glass uses, keeps reflections at full strength; low alpha does not hide them. URP Lit also already has a Fresnel term. Changing alpha or adding Fresnel alone will not fix the window. (§4.1)
3. **The map pane is a tinted veil, not glass.** It has 28% of a pale blue-grey diffuse colour, it is 30 mm thick (real: 6 mm), it has no glazing stop or sill trim, its edges are as clear as its face (real edges look green), and it casts a solid shadow from shadow-casting troffers. (§4.2–4.4)
4. **Breaking is a delete.** At 1.0 s of hold the pane is destroyed in one frame. There are no crack stages, shards, frame teeth, floor glass or camera response. The FMOD side already has a stress loop and crack hits at 35% and 70%, so the sound has beats the picture does not. (§8)
5. **"AAA" on this platform.** The game targets WebGL2 via URP. URP has no screen-space reflections, no planar reflections and no screen-space refraction (Unity's own comparison table), and WebGL2 has no compute shaders, so VFX Graph is out. What *is* reachable is the last-generation AAA recipe: captured cubemaps with box projection, a proper glass shader with smudge maps, pre-fractured breakage, and mesh-particle shards. That is how *Remember Me* (2013) did interior reflections. Ray-traced or SSR glass is not reachable on WebGL. (§6.7)
6. **Build trap.** `FrontRooms 3D/Build macOS` sets the render pipeline to null before building (`FrontRooms3DBuild.cs:61-62`), so a Mac build made from that menu is Built-in RP, not URP. Both builds on disk (`Builds/Mac`, `Builds/WebGL`, Oct 1) are older than the map and do not show it. (§2)

**Top fixes in order:** (1) give the game something to reflect: a captured room cubemap as the default reflection, then box-projected probes; (2) replace the code-built map glass with a real glass material and a 6 mm pane in a glazing stop, with shadows off; (3) build the crack → break → shards → teeth → floor-glass sequence on the existing 1 s hold, synced to the existing FMOD beats. Owners and steps are in §9.

---

## 2. Pipeline and platform facts that limit glass

| Setting | Value | Where | What it means for glass |
|---|---|---|---|
| Render pipeline | URP 17.3.0, Forward+ | `Packages/manifest.json` (URP 17.3.0); `Assets/Settings/FrontRooms_URP_Renderer.asset:50` (`m_RenderingMode: 2` = Forward+) | URP has no screen-space reflections (see §6.4). |
| Pipeline asset on all 6 quality levels | `FrontRooms_URP.asset` (guid 9f471c95…) | `ProjectSettings/QualitySettings.asset:51,104,157,210,263,316`; `ProjectSettings/GraphicsSettings.asset:40` | Every quality level uses the same URP asset. The levels only change the built-in settings (texture mip limit, anisotropy, realtime probes, LOD bias). |
| Current editor quality level | 3 = "High" | `QualitySettings.asset:7`; WebGL default 3, Standalone default 5 (`:338-339`) | "High" has `realtimeReflectionProbes: 1` (`:187`); Very Low/Low/Medium have 0 (`:28,81,134`). This does nothing today, because there are no probes. |
| Opaque texture | **Off** | `FrontRooms_URP.asset:23` (`m_RequireOpaqueTexture: 0`); downsampling 2x bilinear if turned on (`:24`) | Refraction is not possible. A glass shader cannot sample `_CameraOpaqueTexture`. |
| Depth texture | On | `FrontRooms_URP.asset:22` | Available for soft-particle shards and depth-faded dust. |
| HDR | On | `FrontRooms_URP.asset:26-27` | Glass highlights can exceed 1 and bloom (threshold 1.05, `FrontRoomsRenderSetup.cs:197`). |
| MSAA | 4x | `FrontRooms_URP.asset:28`; camera AA filter None (`FrontRoomsPostStack.cs:72`) | Smooths pane and shard silhouettes. Does not fix specular aliasing on mirror-smooth surfaces. |
| Reflection probe blending | **Off** | `FrontRooms_URP.asset:54` | Each renderer takes one probe (`unity_SpecCube0`). |
| Reflection probe box projection | **Off** | `FrontRooms_URP.asset:55` | Even with probes, reflections would sit "at infinity" and not line up with the room. |
| Reflection probes in scenes | **None** | No `ReflectionProbe:` component in any `.unity` or `.prefab` under `Assets` (grep). The 16 "ReflectionProbe" hits in `FrontRooms3D.unity` are the `m_ReflectionProbeUsage` field on renderers. No script creates a `ReflectionProbe` (grep of `Assets/Scripts`, `Assets/Editor`). | Glass can only reflect the default environment cubemap. |
| Skybox | **None** (the game's scene has none; `RenderSettings.skybox = null` below runs only in the standalone map scene and captures [review fix 22:55, see 10 §9]) | `m_SkyboxMaterial: {fileID: 0}` at line 29 of `FrontRooms3D.unity`, `FrontRoomsMapTest.unity`, `FrontRoomsLevelDesigner.unity`; `FrontRoomsMapWorld.cs:491` (`RenderSettings.skybox = null`) | The default reflection source is "Skybox" (`m_DefaultReflectionMode: 0`, `FrontRooms3D.unity:35`), but there is no skybox, so the environment cubemap holds no room. |
| Reflection intensity | 0.3 | `FrontRooms3D.unity:38` (the runtime source); `FrontRoomsLook.cs:20,30` never runs in the game [review fix 22:55, see 10 §9] | The empty environment reflection is scaled to 30%. |
| Baked lighting | None | `m_LightingDataAsset: {fileID: 20201, guid: 0000000000000000f…}` (Unity's empty default) at `FrontRooms3D.unity:96` and line 96 of the other two scenes | No baked probes. The map is generated at runtime, so per-room probes cannot be baked in the editor anyway (§6.2). |
| Active build target (editor) | StandaloneOSX | Decoded from the binary `Library/EditorUserBuildSettings.asset` (active target 2, group "Standalone"); moderately confident | Red judges the look in the editor on an Apple M3 Max with Metal (`~/Library/Logs/Unity/Editor.log`, device lines near the top). The editor is not GPU-limited. |
| Builds on disk | Both **stale** (Oct 1) | `Builds/Mac/…/Managed/Assembly-CSharp.dll` has no `FrontRoomsMapWorld` class; the Mac `Managed` folder has no URP assembly | Neither build shows the current map or glass. |
| macOS build menu removes URP | `BuildMac()` sets `GraphicsSettings.defaultRenderPipeline = null` and `QualitySettings.renderPipeline = null` | `Assets/Editor/FrontRooms3DBuild.cs:61-62` | **A Mac build from this menu ships the Built-in pipeline.** FrontRooms/Surface is URP-only, so that build loses the whole look. It also leaves the editor without a pipeline until Rendering setup runs again. |
| WebGL build menu | Switches target to WebGL, single-threaded, quality 3 | `FrontRooms3DBuild.cs:86,127,146` | WebGL is a real target and sets the budget (§6.7). Physics and any mesh fracture run on one thread there. |

---

## 3. Glass material inventory

Shader abbreviations: **URP Lit** = `Universal Render Pipeline/Lit`. **FR Surface** = `FrontRooms/Surface` (`Assets/Resources/Rendering/FrontRoomsSurface.shader`), an opaque world-projected PBR shader (`Queue=Geometry`, `ZWrite On`, `:46,83-85`) that calls `UniversalFragmentPBR` with `alpha = 1` (`:243-255`).

| Material | Used by | Shader / surface | Blend | Base colour (alpha) | Smoothness / metallic | Highlights / env. reflections | Queue / ZWrite | Cull | Shadow caster | Geometry |
|---|---|---|---|---|---|---|---|---|---|---|
| **Map test / glass** (built in code) | Every map window pane | URP Lit, Transparent (`FrontRoomsMapWorld.cs:1662-1677`) | SrcBlend One, DstBlend OneMinusSrcAlpha, `_ALPHAPREMULTIPLY_ON`, `_Blend 0`: URP's "Alpha + Preserve Specular", set by hand. The alpha-channel blend stays at the shader defaults One/Zero (`Lit.shader:54-55`). | (.75, .85, .88, **.28**) (`:1659`) | .90 / 0 (`:1666`) | On / On (shader defaults, `Lit.shader:22-23`) | 3000 / Off | Back (`Lit.shader:50`) | **On**: the pass is never disabled and `CreatePrimitive` renderers cast shadows by default | `CreatePrimitive(Cube)` scaled to 1.40 × 1.65 × **0.030 m** (`:900-905`; sizes `FrontRoomsModuleUnits.cs:59`). A closed box with back-face culling: one lit glass surface, not two. |
| **Prop_Glass** | Hutch, Hutch_Cherry, DisplayCabinet, VendingMachine, WallClock (slots in `Assets/Resources/Props/Models/*.json`) | URP Lit, Transparent (`Assets/Resources/Surfaces/Prop_Glass.mat:11-23`) | Saved as SrcBlend **1 (One)** with `_ALPHAPREMULTIPLY_ON` and `_BlendModePreserveSpecular 1` (`:15,94,116`). The generator asks for SrcAlpha (`FrontRoomsRenderSetup.cs:414`), but URP's material validation rewrites it, because Preserve Specular defaults to on (`BaseShaderGUI.cs:1098-1114` in the URP package). So `01_interaction_inventory.md`'s note that this material is SrcAlpha/OneMinusSrcAlpha describes the code, not the saved asset. | (.82, .88, .88, **.16**) (`.mat:123`) | .92 / 0 | On / On (`:115,104`) | 3000 / Off | Back (`:98`) | Off, with DepthOnly and MotionVectors (`:24-27`; URP turns ShadowCaster off for transparent Lit, `BaseShaderGUI.cs:777-800`) | Kit meshes; panes are single quads or 8 mm boxes (e.g. `display_cabinet.py:104`, `vending_machine.py:161`). |
| **Prop_BottleBlue** | WaterCooler bottle and cold tap | Same as Prop_Glass; only colour and smoothness differ | Same | (.36, .58, .80, **.42**) | .90 / 0 | On / On | 3000 / Off | Back | Off | Kit mesh. |
| **Office_BlackedGlass** | Title corridor (RoomStream) gurney wheels and exit-sign housings (`FrontRoomsRoomStream.cs:1398,1468,1478`) | FR Surface, opaque | Opaque | (.018, .02, .022) | .95 / 0 | Always on (FR Surface has no toggles) | 2000 / On | Back | Yes | Boxes. It is not used as glass anywhere now; it is a near-black gloss paint. |
| **Prop_GlassCRT** | Kit_InteriorWindow pane, Kit_DeskPhone display | FR Surface, opaque | Opaque | (.059, .078, .071) | .84 / 0 | Always on | 2000 / On | Back | Yes | Interior window: one single-sided quad, 6 mm nominal (`interior_window.py:54,92`). The asset script itself says the window "reads as a framed black slab" (`interior_window.py:31-34`). |
| **Troffer_Lens** | Office-zone map fixtures (`FrontRoomsMapWorld.cs:1641-1647`), title corridor (`FrontRoomsRoomStream.cs:1539`), game fixtures (`FrontRooms3DGame.cs:357`) | FR Surface, opaque, emissive | Opaque | white × albedo map | **1.0** (no mask map; the mask defaults to white, `FrontRoomsSurface.shader:17,207`) / 0 | Always on | 2000 / On | Back | Off on the map lens (`FrontRoomsMapWorld.cs:1045`) | Primitive cube. An opal or prismatic lens is not mirror-smooth. Minor, because emission (2.2, 2.1, 1.8) dominates. |
| **Office_Louver** | `FrontRoomsSurfaces.ParabolicLouver` only (`FrontRoomsSurfaces.cs:49`) | FR Surface, opaque, emissive, metallic .85 | Opaque | white × map | mask × 1 / .85 | Always on | 2000 | Back | — | A metal louver reflecting a black cubemap looks like dark plastic. |
| **Map / Level 0 lens** (built in code) | Level 0 map fixtures (`FrontRoomsMapWorld.cs:1632,1638`) | URP Lit, opaque, emissive (`FrontRoomsSurfaces.cs:86-101`) | Opaque | (1, .98, .92) | .10 / 0 | On / On | 2000 | Back | Off on the lens | Cube. |
| **Map test / key** (built in code) | Zone keys | URP Lit, opaque, emissive (`FrontRoomsMapWorld.cs:1658`) | Opaque | (.96, .87, .23) | .40 / 0 | On / On | 2000 | Back | Yes | A 0.32 × 0.12 × 0.12 m cube (`:730-736`). Not glass; listed because Red named keys. |

Blender slot colours (`Tools/Blender/frontrooms_kit/kitlib.py:72-80,169-170`) use Transmission 0.85 and roughness 0.05 for previews only. They do not reach Unity: the importer remaps each slot to `Resources/Surfaces/<slot>.mat` (`Assets/Editor/Rendering/FrontRoomsKitImporter.cs:8-15`).

---

## 4. Why the map window reads wrong

The brief listed four likely causes. Two are wrong, two are right, and the main cause was not on the list.

### 4.1 Main cause: the glass has nothing to reflect

- **Low alpha does not hide the reflection.** In URP Lit with `_ALPHAPREMULTIPLY_ON`, only the diffuse term is multiplied by alpha. The package comment says it plainly: "we only alpha blend the diffuse part" (`ShaderLibrary/BRDF.hlsl:65-72`). Reflections and highlights are added at full strength. Unity's Lit page says the same: Preserve Specular "keeps specular highlights on transparent surfaces by not applying the alpha value" ([URP Lit shader](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/lit-shader.html)).
- **URP Lit already has Fresnel.** `fresnelTerm = Pow4(1 - NoV)` lerps F0 (0.04 for a non-metal) toward a grazing value (`GlobalIllumination.hlsl:514-519`, `BRDF.hlsl:157-167`).
- **What it reflects is empty.** Reflections come from `unity_SpecCube0` (`GlobalIllumination.hlsl:445-448`). With no probe this is the default environment reflection, built from the skybox. There is no skybox (§2), and the intensity is 0.3. A perfect glass shader would still mirror an empty room. The pane only shows the troffer highlights.
- UNVERIFIED: whether Unity 6.3 fills the default cubemap with black or with the clear colour when the skybox is null. Unity's Lighting window page did not say ([Lighting window](https://docs.unity3d.com/6000.3/Documentation/Manual/lighting-window.html)). Either way it holds no room.

### 4.2 The pane is a tinted veil

- Alpha .28 over a (.75, .85, .88) albedo lays 28% of a pale blue-grey *lit diffuse colour* over the room behind. Clear 6 mm float glass has no diffuse colour: it transmits about 90% of visible light and reflects about 8% in total from its two faces ([Glas Trösch EUROFLOAT](https://glastroesch.com/en/products/basic-float-glass): 6 mm, 90% transmission, 8% reflection). The veil is what reads as "plastic film". Prop_Glass at .16 has the same fault, less strongly.
- Because the veil is diffuse, it brightens and darkens with the troffers like paint.

### 4.3 Thickness and edges

- The map pane is 30 mm thick (`FrontRoomsModuleUnits.cs:59`), five times real 6 mm glass.
- The frame is two jambs and a head (`FrontRoomsMapWorld.cs:860-866`). The pane's bottom edge sits on the bare wall block under the opening (`:853`): no sill trim, no glazing stop, no bead. From above, the player sees a 30 mm clear edge face. A frame with nothing holding the glass is a strong "prototype" cue.
- The edge faces use the face material, so they are as clear as the face. Real float glass edges look green, because light runs along the pane through iron impurities ([Low-iron glass](https://en.wikipedia.org/wiki/Low-iron_glass): the green tint "is from iron impurities"; Glas Trösch notes a "slight distinctive green colour" that depends on thickness).

### 4.4 Shadows and sorting

- The code-built glass keeps its ShadowCaster pass, and the cube casts shadows. About a third of map fixtures cast soft shadows near the player (`FrontRoomsMapWorld.cs:1068,1121-1122`). Near such a lamp the "transparent" pane throws a **solid** shadow. Prop_Glass escapes this only because URP's editor validation turned the pass off.
- Transparent queue, no depth write: anything else transparent in the frame (shards, dust) sorts by object centre. That matters for the breakage design (§8).

### 4.5 Why the whole frame reads as "low render level"

This reaches past glass, but it is the same cause (see `03_rendering_quality.md` for the full-frame audit):

1. No reflections anywhere. Gloss paint (Office_BlackedGlass .95), chrome (Prop_Chrome, metallic 1, smoothness .85), brass, aluminium and the metallic louver all reflect the same empty cubemap. Metal with nothing in its reflection looks like dark plastic.
2. Ambient is a flat three-colour gradient (in the game from the scene, `FrontRooms3D.unity:23-27`; `FrontRoomsLook.cs:24-29` is editor-only [review fix 22:55, see 10 §9]), not a probe, so there is no directional bounce.
3. The FR Surface shader does not declare the probe keywords (`FrontRoomsSurface.shader:96-110` has no `_REFLECTION_PROBE_BLENDING` / `_BOX_PROJECTION` / `_ATLAS`), so URP's include sets blending and box projection to 0 for it (`GlobalIllumination.hlsl:34-40`). Turning them on in the pipeline asset alone will not reach walls, floors or props.

---

## 5. Target glass spec (1990 office interior window / door lite)

Period: the project's era lock is 1990 (working window 1988–1991, nothing designed after 1993) (`Documentation/research/office_and_film/22_era_lock.md` §1–2).

### 5.1 Physical facts

| Property | Real value | Source |
|---|---|---|
| Refractive index | ≈ 1.5 | standard; R0 formula below |
| Reflectance at normal incidence, per surface | R0 = ((n1 − n2)/(n1 + n2))² = 0.04 for air/glass | [Schlick's approximation](https://en.wikipedia.org/wiki/Schlick%27s_approximation) |
| Total visible reflectance, 6 mm clear float (both faces) | 8% | [Glas Trösch EUROFLOAT](https://glastroesch.com/en/products/basic-float-glass) |
| Visible transmittance, 6 mm clear float | 90% (4 mm 90%, 10 mm 89%) | same |
| Colour | slight green, stronger with thickness and on the edge | same; [Low-iron glass](https://en.wikipedia.org/wiki/Low-iron_glass) |
| Grazing behaviour | reflectance rises toward 1 at grazing angles: R(θ) = R0 + (1 − R0)(1 − cos θ)⁵ | [Schlick's approximation](https://en.wikipedia.org/wiki/Schlick%27s_approximation) |
| How annealed glass breaks | "irregular and sharp pieces" | [Tempered glass](https://en.wikipedia.org/wiki/Tempered_glass) |
| How tempered glass breaks | "small rounded chunks" | same |
| Where US codes require safety glazing | near doorways, large windows, windows "close to floor level", among others | same |
| Wired glass | used for fire resistance; the wire keeps cracked glass in the frame; "effectively banned" by the US IBC in 2006, so it is correct for 1990 | [Wired glass](https://en.wikipedia.org/wiki/Wired_glass) |
| Crack pattern on impact | radial cracks run out from the impact point; concentric cracks form around it when the pane is held on all sides; later cracks stop at earlier ones | [Forensic Field: glass fractures](https://forensicfield.blog/glass-fractures-their-types/) |

Notes:
- The map window's sill is 0.35 m (`FrontRoomsModuleUnits.cs:59`), which is "close to floor level". A code-compliant pane there would be tempered and would crumble into granules. Large shards and frame teeth are an **art-direction choice** (annealed glass), justified because the Backrooms is not a code-compliant building. §8 offers both.
- Georgian wired glass mesh size (about 12–13 mm squares) is UNVERIFIED; the Wikipedia page I read names the product but gives no size.

### 5.2 Game values

**Pane geometry (map chat, `FrontRoomsMapWorld` window build):**
- Thickness **6 mm** (`GlassThickness .03 → .006`).
- A glazing stop on both faces: 15–20 mm wide, 12 mm deep, in the trim material, on all four sides; a sill/stool trim under the opening. This hides the edge and gives the pane a believable "held" border.
- Edge faces get their own material: near-opaque green (linear ≈ (.28, .42, .34), smoothness .6). With a 6 mm pane in a stop, the edge mostly shows after the break, on the teeth (§8), where it matters most.

**Face material (visual chat), as a URP Shader Graph Lit target, Transparent, Alpha, Preserve Specular on** (supported by the URP Shader Graph Lit target: `Editor/ShaderGraph/Targets/UniversalLitSubTarget.cs`, `UniversalTarget.cs:954-972` in the package):

| Input | Clean value | With grime map | Why |
|---|---|---|---|
| Base colour (diffuse) | near black, linear (.02, .025, .022) | dust (.42, .40, .34) × dust mask | Glass has no diffuse colour; only dust scatters light. |
| Alpha | `0.08 + 0.55 × F` where `F = Fresnel Effect(Power 5)` | `+ 0.25 × dust` | 0.08–0.10 face-on matches ~90% transmission; rises at grazing angles like real glass. The [Fresnel Effect node](https://docs.unity3d.com/Packages/com.unity.shadergraph@17.3/manual/Fresnel-Effect-Node.html) is `pow(1 − saturate(N·V), Power)`. |
| Metallic | 0 | 0 | Gives F0 = 0.04 automatically. |
| Smoothness | .96 | `lerp(.96, .62, smudge)` | Clean glass is near-mirror; fingerprints and smears blur the reflection, which is what makes glass read as glass under room light. |
| Normal | flat | very weak (0.05) from the smudge normal; float glass has slight long-wave roll | A perfectly flat pane reads as CG. |
| Transmission tint | (.92, .96, .93) face-on | — | Stock URP alpha blend cannot tint what is behind. Options: (a) skip it face-on (90% neutral is close enough) and put the green on the edges; (b) a second Multiply pass in a hand-written shader (UNVERIFIED in this project; must be tested with the SRP Batcher); (c) with the opaque texture on, sample Scene Color and multiply by the tint (§6.6). Recommend (a) now. |
| Cull | Back on a closed 6 mm box | — | Both faces render as you walk around it. |
| Shadow casting | Off | — | Glass should not cast an opaque shadow. |

**Grime maps:** the project already has CC0 sources on disk, not yet imported: `Tools/lookdev/cc0_src/ambientcg/Fingerprints002/Fingerprints002_1K-JPG.zip` (Color, NormalGL, Opacity, Roughness; CC0 per [ambientCG Fingerprints002](https://ambientcg.com/a/Fingerprints002)), plus `Smear007`, `SurfaceImperfections001/007/013/015` and `Scratches005` in the same folder. The synthesis already picked Fingerprints002 for windows (`office_and_film/10_synthesis.md:453`). Layout: dust thickest along the bottom 10–15 cm and in the stop corners; smears at hand height 0.9–1.5 m; a few fingerprints near the edges where people push the frame.

**Variants:**
- *Clear interior window (map)*: as above.
- *Wired glass (door lites, fire corridors)*: the same face material plus a wire grid in the base colour and alpha (dark satin steel, thin), slightly lower smoothness (.88), faint ripple normal. Breaks differently (§8.6).
- *Kit_InteriorWindow (decor)*: keep it opaque, but replace Prop_GlassCRT with an **interior-mapping** pane: a shader that ray-casts a fake room (ceiling, floor, walls) behind the glass and adds the glass reflection on top. It was published by van Dongen in 2008 and is cheap ray-plane math ([Game Developer: Interior Mapping](https://www.gamedeveloper.com/programming/interior-mapping-rendering-real-rooms-without-geometry)). This closes the asset's own open question T15 (`interior_window.py:31-34`; `10_synthesis.md:214`).
- *Shards*: opaque, not transparent (§8.4).

---

## 6. Reflections in URP 17 — options and cost

Unity 6.3's feature table, URP column ([render pipeline feature comparison, 6.3 LTS](https://docs.unity3d.com/6000.3/Documentation/Manual/render-pipelines-feature-comparison.html)): Screen Space Reflections **No**; Planar Reflections **No**; Screen Space Refractions **No**; Reflection Probe box projection **Yes**; blending **Yes**, "sky + 1 local probe, or 2 probes if there is no sky"; real-time probes **Yes**. I also checked the installed package: `Runtime/RendererFeatures/` in URP 17.3.0 has Decal, FullScreenPass, OnTilePostProcess, RenderObjects, SSAO, ScreenSpaceShadows and SurfaceCacheGI, and no reflection feature.

### 6.1 Step 0 — a default environment cubemap (cheapest, biggest change)

Capture one HDR cubemap from the middle of a lit Level 0 room and one from a lit Office room (in the editor, with the fixtures on). Set it as the scene's custom reflection: `RenderSettings.defaultReflectionMode = Custom` and `RenderSettings.customReflectionTexture = <cube>` in `FrontRoomsLook.ApplyAmbient()`; switch the cube per zone when the zone changes. Note: `ApplyAmbient()` never runs on the game's runtime path, so the game must start calling it (or the scene's Lighting settings must change) [review fix 22:55, see 10 §9]. Both APIs exist in the 6000.3.10f1 WebGL player (`UnityEngine.CoreModule.dll` in `PlaybackEngines/WebGLSupport/Managed` contains `customReflectionTexture` and `DefaultReflectionMode`). Then re-tune `reflectionIntensity` (0.3 was set when there was nothing to reflect; try 0.7–1.0).
- Cost: no per-frame cost; one 128–256 px HDR cube per zone in memory. ESTIMATE.
- Effect: every glossy surface (glass, metal, gloss paint, damp carpet) reflects "a fluorescent room". Reflections are "at infinity", so they slide oddly on large flat panes, but this is still far better than black.

### 6.2 Step 1 — box-projected probes per room

Box projection corrects where reflected things appear by intersecting the reflection ray with a box around the room. Without it "reflected objects are not at the right position"; it works best in box-shaped rooms and was used in *Remember Me* ([Lagarde, parallax-corrected cubemaps](https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/)). FrontRooms rooms are boxes on a 3 m grid, which is the best case.

Because the map is generated at runtime, editor-baked per-room probes are impossible. Two ways round it:

| Option | How | Cost | Fit |
|---|---|---|---|
| **A. Custom probes with shared cubemaps** | At chunk build, spawn one `ReflectionProbe` (type Custom) per room or per window cell, sized to the room, box projection on, using the zone's captured cube from §6.1. | No render cost; one probe component per room. ESTIMATE. | Best for WebGL. Reflections line up with the room's walls; content is generic, which is acceptable in a liminal space where every room looks alike. |
| **B. Real-time probes rendered once** | Same probes, type Realtime, Refresh Mode "Via Scripting", rendered when the chunk is built with time slicing. | Each probe renders six cube faces and blurs the mip chain; time slicing spreads it over 9 frames (all faces at once) or 14 (individual faces); real-time cubes are uncompressed in memory ([Reflection Probe](https://docs.unity3d.com/6000.2/Documentation/Manual/class-ReflectionProbe.html), [probe performance](https://docs.unity3d.com/6000.2/Documentation/Manual/RefProbePerformance.html)). Needs `realtimeReflectionProbes` on, which only High and above have (`QualitySettings.asset:187`). | Use only for hero spots (one per window being broken, rendered once). Risky on WebGL if many chunks build at once. |

Required switches (visual chat): `m_ReflectionProbeBoxProjection: 1` (`FrontRooms_URP.asset:55`); probe "Box Projection" on each probe (Unity: box projection must be enabled on the probe and in the URP asset, [Reflection Probe](https://docs.unity3d.com/6000.2/Documentation/Manual/class-ReflectionProbe.html)); `m_ReflectionProbeBlending: 1` (`:54`), which is required, not optional: the map shell is merged into one renderer per 6 m block, and without blending Forward+ gives each renderer one probe [review fix 22:55, see 10 §9]. URP Lit and Shader Graph glass get the keywords automatically (`Lit.shader:142-144`). **FR Surface must opt in** or its walls, floors and props will keep ignoring probes (§4.5). Correction [review fix 22:55, see 10 §9]: three `multi_compile_fragment` lines would multiply its variants by up to 8. If every tier has blending and box projection on, `#define _REFLECTION_PROBE_BLENDING 1` and `#define _REFLECTION_PROBE_BOX_PROJECTION 1` before the URP includes add no variants (`GlobalIllumination.hlsl:34-39`); never declare `_REFLECTION_PROBE_ATLAS` (`Clustering.hlsl:9`). Unity warns that unneeded variants cost memory on the web ([Web graphics APIs intro](https://docs.unity3d.com/6000.3/Documentation/Manual/web-graphics-apis-intro.html)).

### 6.3 Planar reflection

A second camera renders the scene mirrored about the plane, every frame. Unity's own BoatAttack sample does exactly this, at full, half, third or quarter resolution, with a layer mask and optional shadows ([BoatAttack `PlanarReflections.cs`](https://github.com/Unity-Technologies/BoatAttack/blob/master/Packages/com.verasl.water-system/Scripts/Rendering/PlanarReflections.cs)). URP has no built-in planar reflection (feature table). Cost: roughly one extra scene render per reflective plane (ESTIMATE), and windows face many directions. **Not viable on WebGL for windows.** At most one scripted hero mirror.

### 6.4 SSR

Not available in URP 17.3 (feature table "No"; no renderer feature in the package). Third-party URP SSR exists but was not researched (UNVERIFIED), would be heavy on WebGL2, and SSR generally does not shade transparent glass well because glass does not write depth or normals (UNVERIFIED general claim). **Do not plan on SSR.**

### 6.5 Fresnel

Already present in URP Lit for reflections (§4.1). What is missing is *alpha* that rises at grazing angles. Use the Shader Graph Fresnel Effect node on alpha (§5.2).

### 6.6 Refraction via the opaque texture

Turning on `m_RequireOpaqueTexture` (`FrontRooms_URP.asset:23`) makes URP copy the colour buffer after opaques into `_CameraOpaqueTexture`, "a snapshot of the scene right before URP renders any transparent meshes" ([URP asset](https://docs.unity3d.com/Manual/urp/universalrp-asset.html), served as 6000.6 when read). The Shader Graph Scene Color node samples it, in the fragment stage, from a transparent material ([Scene Color node](https://docs.unity3d.com/Packages/com.unity.shadergraph@17.3/manual/Scene-Color-Node.html)).
- Cost: one full-screen copy per frame (2x bilinear downsample is already selected, `:24`). It can be enabled per camera instead of globally.
- Value for clear 6 mm panes: small. Flat glass barely shifts what is behind it. The value is in **cracked glass** (each crack segment bends the view a little differently, §8), wired and obscure glass, and thick shards.
- Caution: on mobile without StoreAndResolve, URP ignores MSAA when the opaque texture is on (URP asset page). Not a desktop-browser issue as far as I know (UNVERIFIED for WebGL).
- Recommendation: off for now; turn on per camera only if the crack stage needs distortion.

### 6.7 What "AAA" can honestly mean here

- The editor on an M3 Max can render much more than WebGL2 in a browser. The design should be judged in a WebGL build, not only in the editor.
- Current-generation AAA glass (ray-traced or screen-space reflections, screen-space refraction, GPU particle shards) needs features URP and WebGL2 do not have: URP has no SSR, planar reflections or SSR-refraction (feature table); VFX Graph needs compute shaders and does not support OpenGL ES ([VFX Graph requirements](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.3/manual/System-Requirements.html)), and Unity lists compute shaders as a WebGPU feature, not WebGL2 ([Web graphics APIs](https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-graphics.html)). Web also supports baked GI only ([Web graphics APIs intro](https://docs.unity3d.com/6000.3/Documentation/Manual/web-graphics-apis-intro.html); an earlier draft cited the WebGL2 page, which does not say this [review fix 22:55, see 10 §9]).
- **Reachable, and what last-generation AAA interiors shipped with:** captured and box-projected cubemaps, a glass shader with Fresnel alpha and smudge-driven roughness, a proper glazing stop, pre-fractured breakage with mesh particles, persistent debris, and tight sync between picture and sound. Most of the "AAA" read of a breaking window comes from timing, debris and reflections, not from ray tracing.

---

## 7. Breakage research

| Technique | How it works | Where seen | Cost | Fits FrontRooms (WebGL)? |
|---|---|---|---|---|
| Delete pane (current) | Destroy the pane | `FrontRoomsMapWorld.cs:1570` | none | No: nothing to see. |
| Grid break with edge connectivity | Pane split into a grid of cells; broken cells disappear; cells no longer connected to the frame fall; each cell picks a texture from its neighbours (16 cases) to draw jagged edges | A Godot showcase ([dev.to](https://dev.to/justind/technical-showcase-breakable-glass-4k5h): "Larger sections will break themselves once enough squares were no longer connected"). Source's `func_breakable_surf` breaks only where hit and leaves jagged edges in the frame ([World of Level Design, CS:GO glass](https://worldofleveldesign.com/categories/csgo-tutorials/csgo-creating-glass-windows.php)). | Very cheap; deterministic; easy to save | Good for *partial* breaks. Looks gridded up close. |
| Pre-fractured mesh swap | Fracture the pane offline (Voronoi, clustered, or **radial** from a centre point); swap the intact pane for the pieces at the break | Unreal Chaos does this in an editor Fracture Mode with Uniform, Cluster, Radial, Planar, Slice, Brick and Mesh tools ([UE fracture guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/fracturing-geometry-collections-user-guide)). Blender's Cell Fracture extension makes Voronoi pieces from points (Blender 4.2+, GPL) ([Cell Fracture](https://extensions.blender.org/add-ons/cell-fracture/)). | Mesh memory small; physics only for the pieces that move | **Best fit.** Author 3–4 radial variants per pane size; pick one by window seed; rotate or mirror for variety. |
| Runtime fracture | Slice the mesh at runtime | OpenFracture for Unity: runtime or editor, recursive slicing, async, MIT; needs closed meshes, one submesh, and "cannot perform localized fracturing based on impact points" ([OpenFracture](https://github.com/dgreenheck/OpenFracture)) | CPU at the moment of breaking; WebGL is single-threaded here (`FrontRooms3DBuild.cs:127`) | No: hitch risk, and no impact-centred radial pattern. |
| Crack overlay | Cracks drawn on the pane before the break | — | Shader cost only | Yes, but URP decals cannot do it: "The decal projection does not work on transparent surfaces" ([URP Decal renderer feature](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/renderer-feature-decal.html)). Cracks must live in the glass shader (a crack mask revealed by a threshold) or on thin overlay quads. |
| Shard particles | Mesh particles with collision | Unity Particle System Collision module: World mode; High quality uses physics, Medium/Low cache in voxels, cheaper; Bounce, Dampen, Lifetime Loss; collision callbacks ([Collision module](https://docs.unity3d.com/6000.3/Documentation/Manual/PartSysCollisionModule.html)) | Cheap at a few hundred particles (ESTIMATE) | Yes. VFX Graph is out on WebGL (§6.7). |
| Frame teeth | Pieces touching the frame stay | Source and the grid method above | None after the break | Yes: mark edge pieces of each pre-fractured variant as teeth. |
| Persistent floor glass | Settled pieces become static; a glint decal on the floor | — | Static meshes, one material | Yes, if the break state is saved per window (§8.5). URP decals work on the opaque carpet. |

---

## 8. FrontRooms hold-to-break design

### 8.1 Today

- Hold E on a pane for 1.0 s: `Hold()` adds `dt`, raises `GlassHold(position, progress)` every frame, and at 1.0 s adds the edge to `brokenWindows`, destroys the pane and raises `GlassBroken` (`FrontRoomsMapWorld.cs:1560-1571`). Letting go resets the hold to 0 (`:1575-1579`).
- Picture: a 120 × 4 px HUD bar (`FrontRooms3DGame.cs:1532-1533`) and, after the break, a text flash (`:785`). Nothing on the glass.
- Sound (FMOD): a `Window/Stress` loop driven by progress; `Window/Crack` one-shots when progress passes **0.35** and **0.70**; `Window/Shatter` on the break (`Audio/FrontRoomsSoundDirector.cs`, `OnGlassHold` / `OnGlassBroken`, about `:443-463` at 21:00; event paths `Audio/FrontRoomsSoundIds.cs:28-30`).
- Legacy sound: `OnGlassBroken` plays the **door-break** impact clip (`FrontRooms3DGame.cs:781-783`), which is muted whenever FMOD is running (`FrontRoomsSoundDirector.cs:140`). `FrontRoomsAudio.Glass()` exists (`FrontRoomsAudio.cs:84`) and is never called.
- The Relay hears the break within 40 m (`FrontRooms3DGame.cs:149,784`).
- Climb: walking into the empty frame within 0.95 m starts a 0.6 s climb with a 0.55 m duck (`FrontRooms3DGame.cs:154,887-929`).
- When a chunk rebuilds, a broken window simply has no pane (`FrontRoomsMapWorld.cs:899`).

### 8.2 Recommended glass type

- **Default, Level 0 and the open office: annealed look.** Big radial shards, teeth left in the frame, glass on both sides of the wall. It reads instantly, and the teeth make the climb feel dangerous. (Art-direction choice; see §5.1 on codes.)
- **Option: tempered look.** The hold produces a fine "crazed" web; at the break the whole pane drops as a cascade of small chunks; no teeth. Cheaper (particles only) and safer to climb through; less dramatic.
- **Option: wired glass on door lites** (§8.6).

### 8.3 Timeline for the 1-second hold

Times are hold progress (0–1 = 0–1.0 s), so they line up with the FMOD parameter and the two crack one-shots that already exist. The impact point is the crosshair hit point, clamped at least 0.2 m from the frame.

| Progress | Stage | Glass (visual chat shader + map chat state) | Camera / screen (map chat) | Sound sync (sound chat) |
|---|---|---|---|---|
| 0.00–0.35 | **Push** | A palm smudge fades in at the impact point (smudge mask, smoothness drops locally). The pane bows up to 2–3 mm at the centre (vertex offset), so reflections swim. Fine dust drifts from the stop at the top. | Lean 4–6 cm toward the pane; FOV eases 76° → 73° (base FOV `FrontRooms3DGame.cs:226`). Hold bar stays as a secondary cue or is removed. | Stress loop rises with progress (exists). |
| **0.35** | **First crack** | Crack mask threshold jumps: 5–7 radial cracks from the impact point, 25–35% of the way to the frame, revealed over about 60 ms. Crack lines are bright, sharp highlights. 3–6 chip particles drop. | Small rotational shake, about 0.4°, 120 ms, rotation only. Do not shake position. | `Window/Crack` #1 (exists, same threshold). |
| 0.35–0.70 | **Spread** | Cracks creep outward slowly (threshold animates with progress). | FOV holds; lean holds. | Stress loop gets grittier (FMOD parameter). |
| **0.70** | **Second crack** | Radials reach the frame; one or two concentric rings appear 8–20 cm around the impact point (§5.1: concentric cracks form when the pane is held on all sides). Each crack segment tilts by a fraction of a degree, so the reflection breaks into facets: **the strongest "cracked glass" cue, and it needs §6.1 reflections to show.** A few centre chips fall out. | Second small shake, about 0.6°. | `Window/Crack` #2 (exists). |
| 0.70–1.00 | **Creak** | Pieces inside the first ring shift 1–3 mm toward the far side. | — | Stress loop peaks. |
| **1.00** | **Break** | Swap the pane for the pre-fractured radial variant aligned to the same crack seed. Inner pieces fly away from the player at 2–4 m/s with spin. Middle pieces drop with a stagger of 0–300 ms (glass falling *after* the break sells weight). Edge pieces stay as teeth. A burst of 150–250 glint particles and a dust puff. ESTIMATES. | Shake about 1.5°, decaying over 250 ms; FOV punch 73° → 70° → 76° over 300 ms; release the lean. | `Window/Shatter` at t = 0 (exists). |
| +0.35–0.6 s | **Settle** | Falling pieces reach the floor (a piece falling 1.2 m takes √(2h/g) ≈ 0.49 s). Pieces stop, then become static (§8.5). | — | Shard-impact tinkles at real landing times (new; or bake the tail into the shatter event). |
| After | **Aftermath** | Teeth in the frame; glass on the floor, about two thirds on the far side; a glint decal under the window; dust in the air for 2 s. | — | Footsteps on glass for a few steps near the window (new surface). |

Camera shake: the GDC 2016 talk "Juicing Your Cameras With Math" covers shake types ([Game Developer summary](https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math)). The "rotation only in 3D" and "shake = trauma²" rules are commonly attributed to it; UNVERIFIED, I did not watch the talk.

### 8.4 Shards and teeth

- **Shards are opaque, not transparent.** Small glass pieces read through highlights and dark edges, not through transparency. An opaque, dark, very smooth shard material with a bright green-tinted rim avoids transparent sorting problems (§4.4) and overdraw, and catches troffer highlights on the floor. ESTIMATE / design advice.
- Dynamic pieces: at most about 24 rigidbodies per break with box colliders, sleeping after 1.5 s (ESTIMATE). Everything else is mesh particles (Collision module, World, Medium quality).
- Teeth: kinematic, part of the window's rebuilt geometry. During the climb, play a crunch and let the bottom-rail teeth snap off (small particle burst) so the player does not pass through solid glass.
- Pre-fractured variants: 3–4 per pane size, generated in the Blender kit (`Tools/Blender/frontrooms_kit`) from a radial point set, with pieces tagged *inner / middle / tooth*. The pane is only 6 mm, so the pieces are 2.5-D (flat slabs with green edge faces).

### 8.5 State and persistence (map chat)

- Replace `HashSet<long> brokenWindows` with per-window break data: `{ stage 0–3, impact point (u, v), seed, side }`. Rebuilding a chunk then recreates the same cracks, teeth and settled floor glass as **static** meshes, with no physics.
- **Cracks do not heal.** Today a release resets the hold to 0 (`FrontRoomsMapWorld.cs:1579`). Keep the reached stage: releasing after 0.35 makes the next hold start at 0.35, after 0.70 at 0.70. A half-cracked window is also good set dressing.
- Events: add `GlassCracked(position, stage)` and give `GlassBroken` the impact point, normal and seed. The sound director can then fire cracks from stages instead of thresholds. As written, it resets `lastStressProgress` to 0 whenever it re-creates the stress loop, so a resumed hold that starts above 0.35 would replay the crack (`FrontRoomsSoundDirector.cs`, `OnGlassHold`).
- `Hold()` needs the hit point. `UpdateAim` already has it (`FrontRooms3DGame.cs`, the `Physics.Raycast` in `UpdateAim`).

### 8.6 Wired glass (door lites, fire corridors)

Cracks spread the same way, but the wire holds the pieces: at "break" the centre sags and hangs instead of falling, and a second hold (or the Relay) tears it out. That is a stronger horror beat for a locked door's vision lite than a clean break. Optional; P2.

### 8.7 Budget summary (ESTIMATES)

| Item | Per break | Persistent |
|---|---|---|
| Rigidbody pieces | ≤ 24 for ≤ 2 s | 0 (made static) |
| Mesh particles | 150–250 for ≤ 2 s | 0 |
| Static shard meshes | — | 1 combined mesh per window (teeth + floor pieces) |
| Extra draw calls | about 25–35 during the break (≤ 24 shards are separate renderers with unique meshes, plus particles), with shadow casting off on moving pieces [review fix 22:55, see 10 §9] | 1–2 per broken window |
| Shader | crack mask + smudge in the glass shader | same |

---

## 9. Remediation plan by owner

Priorities: **P0** fixes the look of every window and every glossy surface; **P1** delivers the break sequence; **P2** is polish. Effort is an ESTIMATE in focused days.

### Visual chat (rendering, prop kit)

| # | Pri | Task | Files | Effort |
|---|---|---|---|---|
| V1 | P0 | Capture a Level 0 and an Office HDR cubemap; use them as the custom default reflection per zone; retune `reflectionIntensity` (§6.1). | `Assets/Scripts/Rendering/FrontRoomsLook.cs`, new `Assets/Resources/Lighting/` cubemaps | 0.5–1 |
| V2 | P0 | A `FrontRooms/Glass` Shader Graph (Lit, Transparent, Preserve Specular, Fresnel alpha, smudge/dust maps from the local CC0 Fingerprints002 / Smear007, crack mask with a `_Crack` 0–1 threshold, palm-smudge position). Ship `Glass_Window`, `Glass_Edge` and `Glass_Shard` materials in `Resources/Surfaces`; move Prop_Glass and Prop_BottleBlue onto it. | `Assets/Resources/Rendering/`, `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs` (`GlassDefs`, `EnsureGlassMaterials`) | 2–3 |
| V3 | P1 | Box projection on (and blending if wanted) in `FrontRooms_URP.asset:54-55`; add the probe keywords to FR Surface (§6.2). | `FrontRoomsRenderSetup.cs` `EnsurePipeline`, `FrontRoomsSurface.shader` | 0.5 |
| V4 | P1 | Pre-fractured radial pane variants with inner / middle / tooth tags; shard and glint particle prefabs. | `Tools/Blender/frontrooms_kit`, `Assets/Resources/Props` | 2 |
| V5 | P2 | Interior-mapping pane for Kit_InteriorWindow (T15). | `interior_window.py`, new shader | 1–2 |
| V6 | P2 | Troffer_Lens smoothness 1.0 → about 0.4 (or give it a mask). | `FrontRoomsRenderSetup.cs:300` | 0.1 |

### Map chat (game flow, interactions)

| # | Pri | Task | Files | Effort |
|---|---|---|---|---|
| M1 | P0 | Stop building glass in code: use the visual chat's `Glass_Window` (fallback to today's material if missing); pane 6 mm; glazing stop and sill trim; **shadow casting off** on the pane renderer. | `FrontRoomsMapWorld.cs` window build (`:899-908`), `BuildMaterials`/`TransparentGlass` (`:1659-1677`), `FrontRoomsModuleUnits.cs:59` | 0.5–1 |
| M2 | P1 | Per-window break state (stage, impact point, seed); stages persist on release; `GlassCracked` event; `Hold()` takes the hit point; swap to the fractured variant instead of `Kill(window.pane)`; static rebuild of teeth and floor glass. | `FrontRoomsMapWorld.cs:1560-1580`, `:899`; `FrontRooms3DGame.cs` `UpdateAim` | 2 |
| M3 | P1 | Camera beats from §8.3 (lean, FOV, shake). Coordinate with the key push-in work in `01_interaction_inventory.md` so both use one camera-shot helper. | `FrontRooms3DGame.cs` | 1 |
| M4 | P1 | Climb through teeth: crunch, snap bottom teeth, glass footsteps near broken windows. | `FrontRooms3DGame.cs:887-929` | 0.5 |
| M5 | P2 | Replace the legacy door-break clip on glass with `FrontRoomsAudio.Glass()` for the FMOD-failed fallback. | `FrontRooms3DGame.cs:783` | 0.1 |

### Sound chat (FMOD)

| # | Pri | Task | Files |
|---|---|---|---|
| S1 | P1 | Drive crack one-shots from `GlassCracked(stage)` so a resumed hold does not replay them; add a shard-landing tail (about 0.35–0.6 s after the shatter) and a glass footstep surface. | `Assets/Scripts/Audio/FrontRoomsSoundDirector.cs`, FMOD project |

### Unassigned (Red to decide)

| # | Pri | Task | File |
|---|---|---|---|
| U1 | P0 | `BuildMac()` nulls the render pipeline; remove those two lines or the Mac build is not the URP game. Rebuild both players before judging builds. | `Assets/Editor/FrontRooms3DBuild.cs:61-62` |

### Order of work

1. V1 + M1 (one day of work, and every window and metal surface improves at once).
2. V2 (the glass looks like glass).
3. M2 + V4 + S1 + M3 (the break sequence).
4. V3, then the P2 items.

---

## 10. Sources

### Project code (read directly)

`Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `FrontRoomsModuleUnits.cs`; `Assets/Scripts/FrontRooms3DGame.cs`; `Assets/Scripts/Rendering/FrontRoomsLook.cs`, `FrontRoomsSurfaces.cs`, `FrontRoomsPostStack.cs`; `Assets/Scripts/Audio/FrontRoomsSoundDirector.cs`, `FrontRoomsSoundIds.cs`; `Assets/Scripts/FrontRoomsAudio.cs`; `Assets/Scripts/FrontRoomsRoomStream.cs`; `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs`, `FrontRoomsKitImporter.cs`; `Assets/Editor/FrontRooms3DBuild.cs`; `Assets/Resources/Rendering/FrontRoomsSurface.shader`; `Assets/Resources/Surfaces/{Prop_Glass,Prop_BottleBlue,Office_BlackedGlass,Prop_GlassCRT,Troffer_Lens,Office_Louver}.mat`; `Assets/Resources/Props/Models/*.json`; `Tools/Blender/frontrooms_kit/assets/interior_window.py`, `kitlib.py`; `Assets/Settings/FrontRooms_URP.asset`, `FrontRooms_URP_Renderer.asset`; `ProjectSettings/QualitySettings.asset`, `GraphicsSettings.asset`; the three `.unity` scenes; `Library/EditorUserBuildSettings.asset` (binary, decoded); `Builds/Mac`, `Builds/WebGL`.

URP 17.3.0 package (`Library/PackageCache/com.unity.render-pipelines.universal@37e0d4fc2503`): `ShaderLibrary/BRDF.hlsl:65-72,157-167`; `ShaderLibrary/GlobalIllumination.hlsl:34-40,287-300,420-455,514-519`; `ShaderLibrary/Clustering.hlsl:9`; `Shaders/Lit.shader:22-23,48-57,106-108,125-163`; `Editor/ShaderGUI/BaseShaderGUI.cs:777-800,1098-1114`; `Editor/ShaderGraph/Targets/UniversalTarget.cs:954-972`; `Runtime/UniversalRenderPipeline.cs:1972-1975`; `Runtime/Data/UniversalRenderPipelineAsset.cs:1418-1425`; `Runtime/RendererFeatures/` (listing).

### Web (pages read on 2026-10-02)

- Unity, Render pipeline feature comparison (6.3 LTS): https://docs.unity3d.com/6000.3/Documentation/Manual/render-pipelines-feature-comparison.html
- Unity, Reflection Probes in URP: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/lighting/reflection-probes-introduction.html
- Unity, Reflection Probe component (6.2): https://docs.unity3d.com/6000.2/Documentation/Manual/class-ReflectionProbe.html
- Unity, Reflection probe performance (6.2): https://docs.unity3d.com/6000.2/Documentation/Manual/RefProbePerformance.html
- Unity, URP asset reference (served as 6000.6): https://docs.unity3d.com/Manual/urp/universalrp-asset.html
- Unity, URP Lit shader (6.3): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/lit-shader.html
- Unity, Lighting window (6.3): https://docs.unity3d.com/6000.3/Documentation/Manual/lighting-window.html
- Unity, URP Decal renderer feature (6.3): https://docs.unity3d.com/6000.3/Documentation/Manual/urp/renderer-feature-decal.html
- Unity, Shader Graph Scene Color node (17.3): https://docs.unity3d.com/Packages/com.unity.shadergraph@17.3/manual/Scene-Color-Node.html
- Unity, Shader Graph Fresnel Effect node (17.3): https://docs.unity3d.com/Packages/com.unity.shadergraph@17.3/manual/Fresnel-Effect-Node.html
- Unity, VFX Graph system requirements (17.3): https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.3/manual/System-Requirements.html
- Unity, Web graphics APIs (6.3): https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-graphics.html
- Unity, Web graphics APIs intro (6.3): https://docs.unity3d.com/6000.3/Documentation/Manual/web-graphics-apis-intro.html (replaces the WebGL2 page [review fix 22:55, see 10 §9])
- Unity, Particle System Collision module (6.3): https://docs.unity3d.com/6000.3/Documentation/Manual/PartSysCollisionModule.html
- Unity BoatAttack, PlanarReflections.cs: https://github.com/Unity-Technologies/BoatAttack/blob/master/Packages/com.verasl.water-system/Scripts/Rendering/PlanarReflections.cs
- Sébastien Lagarde, parallax-corrected cubemaps (2012): https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/
- Game Developer, Interior Mapping: https://www.gamedeveloper.com/programming/interior-mapping-rendering-real-rooms-without-geometry
- Game Developer, camera math talk summary: https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math
- Epic, Fracturing Geometry Collections: https://dev.epicgames.com/documentation/en-us/unreal-engine/fracturing-geometry-collections-user-guide
- Blender Extensions, Cell Fracture: https://extensions.blender.org/add-ons/cell-fracture/
- OpenFracture (Unity): https://github.com/dgreenheck/OpenFracture
- dev.to, breakable glass showcase: https://dev.to/justind/technical-showcase-breakable-glass-4k5h
- World of Level Design, CS:GO glass windows: https://worldofleveldesign.com/categories/csgo-tutorials/csgo-creating-glass-windows.php
- Glas Trösch, EUROFLOAT basic float glass: https://glastroesch.com/en/products/basic-float-glass
- Wikipedia, Schlick's approximation: https://en.wikipedia.org/wiki/Schlick%27s_approximation
- Wikipedia, Low-iron glass: https://en.wikipedia.org/wiki/Low-iron_glass
- Wikipedia, Tempered glass: https://en.wikipedia.org/wiki/Tempered_glass
- Wikipedia, Wired glass: https://en.wikipedia.org/wiki/Wired_glass
- Forensic Field, glass fractures: https://forensicfield.blog/glass-fractures-their-types/
- ambientCG, Fingerprints002 (CC0): https://ambientcg.com/a/Fingerprints002

Not readable (HTTP 403), so not used as evidence: Valve Developer Community `Func_breakable_surf`; Pilkington via specifiedby.com; an ArtStation glass system page. The NIST glass-fracture PDF could not be parsed.
