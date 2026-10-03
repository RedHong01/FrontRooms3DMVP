# Visual chat (游戏视觉) — task queue

Updated 2026-10-02 23:0x. This lists everything open from the visual chat's conversation with Red, with its status and what it depends on.

**Owner areas:** Rendering/*, Editor/Rendering/*, Office/*, FrontRoomsRoomStream.cs, FrontRoomsRelayRig.cs, the prop and creature kits (Tools/Blender), Tools/lookdev, surface and glass materials, the post stack, look-dev.

**Working rules:**
- Red has the real project open, so work happens in a private Unity copy, and only compiled, verified files are promoted.
- No AudioSources: sound goes through events and 声音 (Documentation/AUDIO_CONTRACT.md).
- Kit names are frozen.
- Era lock: 1990 (research/office_and_film/22_era_lock.md).

Status legend: **RUNNING** (a workflow is in progress) · **QUEUED** (next up) · **WAIT-RED** (needs Red's call) · **WAIT-CHAT** (waiting on another chat) · **DONE**.

---

## 1. Glass: material, reflections, breakage (Red asked for this explicitly; top priority after the running jobs)

Red: "the glass material and reflection values are wrong; the render level is too low." The diagnosis and the plan are in research/interaction_audit/02_glass_and_breakables.md and 10_audit_report.md §4. Evidence frames are in interaction_audit/images/.

**What's wrong today:**
- The map's pane is a flat cube, 30 mm thick, using `TransparentGlass` (alpha .28, tinted (.75,.85,.88), smoothness .9) built in MapWorld code.
- There is no reflection probe, so the pane reflects only the default ambient/sky, and it reads as a milky veil.
- No fresnel, no grime, no edges.
- It casts shadows.
- Prop_Glass's generator code doesn't match the saved asset.
- Kit_InteriorWindow's pane is an opaque black slab.
- Breaking the glass deletes the pane.

**Tasks:**

| # | Task | Owner | Status |
|---|---|---|---|
| G1 | `FrontRooms/Glass` (Shader Graph or HLSL): transparent, Preserve Specular, base (.02,.025,.022), alpha .08 + .55·Fresnel⁵, smoothness .96, smudge-driven roughness, a long-wave normal roll; `_Crack/_ImpactUV/_CrackSeed/_Palm` hooks | visual | RUNNING (workflow glass-track, clone proj_glass) |
| G2 | Import the CC0 grime maps already on disk (Fingerprints002, Smear007, SurfaceImperfections001/007/013/015). Layout: dust low and in the corners, smears at 0.9–1.5 m, a few prints | visual | RUNNING (glass-track) |
| G3 | Materials `Glass_Window`, `Glass_Edge` (green float-glass edge), `Glass_Shard` (opaque) in Resources/Surfaces, made by RenderSetup | visual | RUNNING (glass-track) |
| G4 | Prop_Glass / Prop_BottleBlue onto the glass graph; make the generator code write what the saved assets actually hold (premultiplied + Preserve Specular) | visual | RUNNING (glass-track) |
| G5 | Kit_InteriorWindow pane onto the glass graph (with an interior-mapping back layer) | visual | QUEUED after G1 |
| G6 | Zone reflection cubemaps (lit Level 0, lit Office, dead-lamp; plus the title-stream rooms) + `FrontRoomsLook.SetZoneReflection(kind)`. Keep intensity ≤ 0.5 at first; crossfade 0.5 s. Prove a runtime change reaches URP in a play-mode test. Caveat from the wallpaper chat: a baked cube shows a frozen print, so keep it low on glossy surfaces | visual (+ map calls it at run start and on zone change) | RUNNING (glass-track). Stub with the final signature is IN MAIN (`ReflectionZone {Level0, Office, Tall, DeadLamp}`, `SetZoneReflection(zone, blend=.5)`); the map chat calls it + ApplyAmbient |
| G7 | Per-room Custom ReflectionProbes at chunk build (desktop tiers): probe blending + box projection in the URP asset; `_REFLECTION_PROBE_BLENDING/BOX_PROJECTION` defines in Surface.shader; 64–128 px; measure atlas memory | visual (asset/shader) + map (spawning) | QUEUED (desktop tier) |
| G8 | Fracture variants: 3×3 impact centres × 2 = 18 pre-fractured panes (Blender, 6 mm slab, green edges), each with its own crack mask; teeth that stay in the frame + floor glass; opaque shards, no shadows on moving pieces | visual | QUEUED (shared with the interactables kit's window remnants) |
| G9 | Map side: pane 6 mm, glazing stops, a stool trim, shadows off, load `Glass_Window`; a per-edge record (break stage, impact uv, seed); `Hold()` passes the hit point; `GlassCracked` + `WindowShattered`; keep `GlassBroken` firing (声音 relies on it) | map chat | WAIT-CHAT: contract to be sent with the audit |
| G11 | **Ray-traced reflections? (Red: "try whether ray tracing works")** Feasibility study.
- **Known going in:** URP 17 has no hardware ray tracing (DXR is HDRP-only, desktop DX12/Vulkan), and WebGL has none at all.
- **Alternatives to evaluate and measure:** a custom screen-space-reflection renderer feature; a time-sliced planar reflection for the window being looked at; per-room probes (G7); a realtime probe at the window on hold start.
- **Also report** what switching to HDRP would cost, so Red can decide the target. | visual | RUNNING (glass-track) |
| G12 | **Staged physical fracture (Red):**
- crack stages during the 1 s hold, tied to the progress;
- at the break, shards fall with physics (Rigidbody, no shadows on movers) and break again on hitting the floor (second-level fracture);
- floor glass and teeth remain in the frame;
- a WebGL budget (piece caps, pooling, settle-to-static).
- **Runtime component:** a visual-chat VFX script subscribing to the map's `GlassCracked` / `WindowShattered` (hit point, impulse). Meshes come from the interactables kit's fracture set (R3/1d). | visual (+ map events) | QUEUED (meshes in R3) |
| G10 | Verification capture of the combined result (clear values + grime + zone cube) with the audit's in-engine harness (proj_audit, seed 4242 frames 01/04/23/34/35 + dead lamp) before sign-off | visual | RUNNING (glass-track verify) |

## 1b. WebGL optimisation (Red, 2026-10-02 23:2x)

**Red:** "optimise specifically for WebGL: keep the display quality, work out how many renders at what detail can coexist, and render high detail only where the player can see it, without visible popping or seams."

**HARD RULE (Red):** every WebGL change applies **only to WebGL builds**. It never touches the Mac/Windows clients, **Editor Play Mode**, or the editor default, and the game does not pivot to WebGL. Only provably identical changes may apply everywhere.
- **Quality and URP:** a WebGL-only Quality Level is the WebGL platform default, with its own URP asset; Standalone keeps `FrontRooms_URP.asset`. FrontRoomsRenderSetup must stop forcing one asset on every level.
- **Imports:** texture and audio overrides on the WebGL tab only.
- **Code:** `#if UNITY_WEBGL` or a runtime platform check, with the desktop path unchanged.
- **Builds:** WebGL-only build settings and entry point.
- **Proof:** prove that desktop output is unchanged.

| # | Task | Status |
|---|---|---|
| WG0 | Fixes already landed: the RoomStream.Cylinder CapsuleCollider (no CreatePrimitive) | DONE |
| WG1 | Facts: the WebGL2 / URP 17.3 limits (32 visible lights, no compute, variants, texture formats, the heap), today's 207.7 MB cloud WebGL build (size breakdown, load time), measurements in a browser | RUNNING (workflow webgl-optimisation, clone proj_web) |
| WG2 | Visibility: a room/portal visibility system for the procedural maze (cells, doors, windows, arches; shut doors block). Unity's baked occlusion can't work for runtime-built chunks. Typical potentially-visible room counts per seed | RUNNING (workflow webgl-optimisation, clone proj_web) |
| WG3 | A detail budget model: draw calls, triangles, lights, shadow casters, texture memory per tier, i.e. "how many high-detail rooms, props, lights and shadows at once". A hero room at full detail, neighbours reduced, beyond that impostors or off. Hysteresis and cross-fades so nothing pops in view | RUNNING (workflow webgl-optimisation, clone proj_web) |
| WG5 | **SRP Batcher restore (measured by the WebGL perf session):**
- **Problem:** MaterialPropertyBlocks on every chunk shell renderer (`_CeilingHeight`, set in MapWorld.AddRenderer) and on every lens cube (emission) break batching, causing about 1,000 per-object UBO uploads per frame. The lens material has instancing off.
- **Fix:** a ceiling height derived from world Y/vertex data or 3 material variants; lens emission without MPBs; instancing on. The map side gets a change list. | QUEUED (after the plan) |
| WG6 | **Lighting passes:** SSAO Source=DepthNormals costs a full geometry prepass (A/B Source=Depth). The "Soft ambient direction" directional light renders 2 cascades of the whole maze every frame, and the audit says it leaks 82% through ceilings, so remove it or make it shadowless. About 1,500 lights + 1,500 lens cubes exist at once, so cull them per cell | QUEUED |
| WG7 | **Textures:** 434 MB uncompressed = 97% of the build. 11 byte-identical duplicate PNGs in Surfaces/Textures; pack S maps into A/N alpha; WebGL-tab compression overrides only | QUEUED |
| WG-split | The WebGL perf session (WebGL 卡顿性能分析, uds 86253) owns build settings, CPU hitches in map/game code, hosting (GitHub Pages serves LFS pointers, so the game doesn't load online), IL2CPP Master + 256 MB heap + the WebGPU test menu (Red-approved), and a WebGL-only TickFixtures branch in MapWorld. We own the render tier, materials/shaders/lights look, visibility detail levels, and dressing cost. Its baseline: `research/webgl/00_measured_baseline_2026-10-02.md` (about 13 fps, CPU-bound, ~2,300 draws/frame) | — |
| WG4 | The plan: the WebGL tier settings, a visibility-driven detail manager (an ownership split with the map chat: chunk streaming and visibility vs LOD, materials, lights, URP), build-size reduction, measurement gates | RUNNING (workflow webgl-optimisation, clone proj_web) |

## 2. Running now

| # | Task | Status |
|---|---|---|
| R1 | Interaction + render-quality audit | **DONE**: verified, 71 review items applied (10_audit_report.md §9). The contract went to the map chat (events, camera rig, BaseEye rules, DoorUnlocked moved to the commit beat) and to 声音 (SFX events). FrontRoomsShotTimings proposal delivered (interaction_audit/FrontRoomsShotTimings.proposal.cs.txt, head-dip included). PNG→JPG pending Red (W7) |
| R2 | Wallpaper as motion graphics, P0: split paper and print; `_FR_PRINT` layer with a static `_PrintTex` fallback; T1 parity ≤ 1/255; T2 specular invariance. Channel B is reserved for phosphor | RUNNING (in the private copy) |
| R4 | **Door gaps (Red, 2026-10-02 23:0x):** shut doors show see-through slits at the frame: the visible leaf is the 0.98 × 2.08 collider cube hung from the hinge, so 2 cm sit at the latch side and at the head, with no stop or threshold, and the doors swing both ways. Red wants RE8's door construction researched and replicated. Folded into R3: RE8 research, evidence of today's gap from both sides, a gap-free frame/stop/casing/threshold + an overlapping visual leaf (the collider unchanged), swing-clipping tests both ways. Option A (RE8-faithful single-swing with stops) needs the map chat to change its swing rule; option B keeps both-ways swing → **WAIT-RED/WAIT-CHAT on the choice** | RUNNING (in R3) |
| R7 | **Door family per level (Red, 23:3x):**
- Lobby/Level 0, Office, Run and the true Exit doors.
- Same visual grammar (frame, stop, casing logic, hardware language, lock position), each fitting its level's theme.
- A free and a locked version per level.
- Structurally refined: profiled casings, stiles/rails/panels or banded flush skins, glazing beads, hinge knuckles, kick plates, closers.
- **Single-acting (option A, decided by Red):** real stops; the map chat implements the fixed swing side and pulls. | RUNNING (folded into R3 at the spec stage) |
| R8 | **A real keyable lock (Red):** a cylinder with a real keyway matching the key blade, pin chambers, a plug that rotates 90° with the key, a sliding deadbolt, and a lever. Separate animatable parts with pivots and anchors, matched to FrontRoomsShotTimings.Unlock (insert 2.5 cm, 90° turn, bolt at the commit beat), and joined to the head-dip key shot | RUNNING (in R3) |
| R9 | **Windows with real structure (Red, 23:5x):** research period-correct windows (interior borrowed lights / relites, hollow-metal / aluminium / wood frames, glazing stops holding a 6 mm pane, sill/stool + apron, mullions/transoms, mini-blinds) and build a WINDOW FAMILY per level (Lobby/Office/Run/Exit) sharing the door grammar. Render-only, outside the opening when broken; the fracture set fits the stop | RUNNING (R3: researcher 06 + spec/build/render) |
| R10 | **Put every new model in Figma's Prop Kit section** (2324:852, owned by 平面视觉): three-view sheets (ortho front/side/top, a 3/4 hero, variants, materials, era) for doors, locks, keys, windows, glass. The workflow's last stage renders `interactables/threeview/` + index.json; then the sheets are placed as K46+ in the section's format. **平面视觉 places them (option a)** as K46+ in a new sub-block "K46–Kxx · INTERACTABLES (doors · locks · keys · windows)", re-rendering our FBX through its Tools/three_view. We hand off `interactables/threeview/index.json` (its fields) + README + fallback renders (transparent, 16 px padding, its px/m scales). Its era notes are binding: interchangeable-core cylinders, plastic ring key tags with paper inserts (Courier Prime/VT323), 1-inch aluminium mini-blinds; no keypads, card readers or LEDs | RUNNING (hand-off is the workflow's last stage) |
| R5 | **Locked vs free doors read differently from afar (Red).** New research grounded in the Figma research (IP RESEARCH 2312:852, THREE-VIEW + ERA 2324:852, REAL vs MODEL 2349:852, Hunter HR03) + the era lock picks a door type for key-locked doors, e.g. a hollow-metal back-of-house door with a keyed deadbolt, kick plate, wired lite and signage vs the free office door. A readability test at 6/12/20 m in Level 0 and Office. Then build both variants on the gap-free frame. The map spawns the locked variant on key-locked doors | RUNNING (in R3) |
| R6 | **Key-use "head-dip" shot (Red):**
- using a key, the camera pushes in like a person lowering their head to unlock, ending on the key turning in the keyed cylinder;
- the door swings after `UnlockSwingDelay`.
- **Ours:** the camera curve and timing, the anchors on the key and cylinder (R3), and the shot spec.
- **Map chat's:** the FrontRooms3DGame camera takeover (input locked, a timeline hook, the `Paused` event respected).
- **SFX** via events to 声音. | anchors RUNNING (R3); shot spec in the audit contract → WAIT-CHAT |
| R3 | Interactables kit (Red: "keys etc. have no real models"): zone keys + tags + hosts, lockset/handle at DoorHandle* constants, hinges, the door leaf (≤ 0.05), the interior window frame, glass remnants. All render-only, following the map's binding constraints (research/interactables/00_map_constraints.md). Then an in-engine render, a critic pass and the map contract | RUNNING |

## 3. Queued (visual chat)

| # | Task | Depends on |
|---|---|---|
| Q1 | Wallpaper P1: `_FR_PrintWarp` (curl warp, exact spec from the wallpaper chat; phase in y, 3 m period, albedo only) in the P0 `PrintUV` helper; look-dev at the subliminal and scripted ranges | P0 passing |
| Q2 | Wallpaper later: a phosphor glow-ink emission path (B × ZnS green × per-cell charge × paper cavity), with a per-cell lamp/charge texture from the map chat | design + map chat |
| Q3 | Audit remediation, visual side (beyond glass): render quality tiers (WebGL vs desktop cinematic), the ranked render changes in 10_audit_report.md §5; shatter VFX; post pulses API (grain/CA bump on first sight) | the audit landing |
| Q4 | Title → map seam: make the map's lamp match the stream troffer (pan + lens + beam). Coordinate with the map chat (MapWorld geometry) | map chat |
| Q5 | Light leak: (i) the title-stream side lamps light the map floor through walls; (ii) the map chat reports 2 of 3 map lamps cast no shadows (budget), so lit rooms bleed through walls and door slits. Options: URP rendering layers / per-room light masks, cheaper shadow strategy (shadowed nearest-N lamps, cached shadow maps), or wall-light occlusion in the surface shader. Map facts: FrontRoomsMapWorld.BuildFixture creates lights with shadows None; ~1 in 3 marked castsShadow; TickFixtures enables shadows within profile shadowRadius 9 m and lights within lightRadius 16 m (3 m fade). A different split or per-room light-blocking volumes = send the rule to the map chat; shader/URP-only fixes are ours. Acceptance: Office playtests seeds 2554/20388 ≥ 55 fps, p99 ≤ 33 ms. Check the WebGL/Forward+ cost; tell the title session before flipping | measurement |
| Q6 | Review the map chat's Office look-around frames (Verification/main-autopilot/NN_office_*) and tune the Office dressing and grade | — |
| Q7 | Furniture pile density (use sofas more) | — |
| Q8 | Optional shader prewarm (the known 3.0 s first-compile spike) | — |
| Q9 | `Kit_CubiclePanelTall` 1.65 m so the panels block sight (open item in the module contract) | — |
| Q10 | Promote the editor look-dev tools (HunterLookdev, the KitLookdev ceiling-height overload) and the creature material defs (Creature_* in RenderSetup) after P0 merges | P0 merge |
| Q11 | Clean up the private clones (proj_audit, proj_int) after the work lands; delete the stray `creatures/zz_frame_test.py` | — |
| Q13 | **Dressing hitch (measured by the map chat):** one Office/pile room dressed in a single frame costs 42–166 ms (seed 20388, chunk (16,10)), the biggest gameplay hitch after the shader compile. The plan: profile, optimise with bit-identical output, add a time-sliced `Step(budgetMs)` API (the WebGL budget gated to WebGL), prove it with seed hashes + timings, then a map contract | RUNNING (workflow office-dress-hitch, clone proj_rs) |
| Q14 | **Coordinate with the new session "WebGL 卡顿性能分析" (WebGL stutter):** split the scope (they take hitches in map/game code; we take the render tier, detail levels and dressing cost), protect our files, and share findings | WAIT-CHAT (message sent) |
| Q12 | Use 平面视觉's 1990 period type kit (Assets/Fonts/Period1990, Documentation/FONTS_PERIOD_1990.md) for in-world printing: key tags, labels, signage | interactables kit |

## 4. Waiting on Red

| # | Decision | Where |
|---|---|---|
| W1 | Hunter: which body (A Floor Sample / B Night Shift / C Duplicate / D Delivery, as the squeezed giant); keep the long craned neck or let the face sit about 0.3 m higher; catch distance 0.7 → about 1.3 m; every door a squeeze? | Figma page 2099:76, Hunter section, HR16 |
| W2 | Prop period fixes from 平面视觉's REAL vs MODEL: the torchiere to brass with a glass/acrylic shade; the task chair to armless grey/coloured fabric (keep the black armed one as a variant) | — |
| W3 | Delete Codex's unreferenced `FrontRoomsOfficeFurniture` + `Models/Office`? | — |
| W5 | **Which doors are locked?** Today `doorsNeedKeys` is all-or-nothing (all doors, or none by default), so "locked doors look different" needs a per-door rule. The map chat proposes `lockedDoorShare` ≈ 0.35 (a deterministic edge hash, stable per seed), keeping "the key of the zone you stand in" (always solvable). Alternatives: only doors leading deeper, or only doors into Office zones. Red picks; the map chat implements; the kit provides both variants | map chat / R5 |
| W6 | **DONE: Red chose A** (single-acting with stops, relayed via 声音 + the map chat, 23:3x). Door gaps option A vs B: RE8-faithful single swing with stops (map: a fixed swing side per door, pulls with a short step-back takeover, the Relay breaks toward the swing side; about an evening) vs gap-free while keeping the both-ways swing (no map change) | the door report (R4) |
| W7 | Convert the audit's 124 MB of evidence PNGs (already committed and pushed in 6498c2a) to JPG? It replaces committed files; a history rewrite is the repo owner's call | the audit |
| W9 | **ANSWERED (Red, 23:55, via the WebGL perf session):** WebGL is a separate track. Nothing for WebGL may change Editor Play Mode or Mac/Win rendering or logic, and there's no pivot of the game to WebGL. Only provably identical changes (e.g. deleting a byte-identical duplicate texture) may apply everywhere; everything else is WebGL-only (gated `#if UNITY_WEBGL && !UNITY_EDITOR` / platform check) | done |
| W10 | **The project is on the iCloud-synced Desktop.** iCloud keeps making "<name> 2/3/4" conflict copies when files are overwritten mid-sync. A stale `FrontRoomsRelayRig 2.cs` broke Red's compile at 23:37 (声音 quarantined it). Found at 23:4x: 21 duplicate FMOD banks (声音's; they bloat the WebGL build), `Resources/PerformanceTestRunSettings 2.json`, `ProjectSettings/ShaderGraphSettings 2.asset`. **Fix: move the project out of iCloud** (or exclude it from iCloud sync). The visual chat's promote script now quarantines conflict siblings of everything it promotes | Red |
| W8 | The audit's §7 questions: platform bar (Mac desktop recommended, WebGL a reduced tier); camera language (answered by Red: a camera head-dip, no hands); keys rule (W5); an "ajar, then push" door state; annealed vs tempered glass; hold vs strikes; enable the particle module?; build-script owner; where Red saw the low render level (his last player run was a pre-URP build saved in SDR); which AAA references; mobile in scope?; should the Relay see through intact glass? | 10_audit_report.md §7 |
| W4 | Render target: honest "AAA" on WebGL vs a desktop cinematic tier (see the audit §5) | the audit |

## 5. After Red picks the Hunter (W1)

| # | Task |
|---|---|
| H1 | Production Hunter: one skinned mesh (8–12 k tris, 24–36 bones, mirrored armature) blending the low/std/door/tall poses from `CeilingHeight` / `DoorSqueeze`; set `PressesCeiling`; raise `CeilingBrush`/`Squeeze` from real contact |
| H2 | Swap it in place of the primitive rig in the scene's Hunter (the API is unchanged); the map chat raises the catch distance |
| H3 | Retopologise / bake normal maps (fold creases, quilting); 2–3 materials; promote the Creature_* materials |
| H4 | Tell 声音 the final body (footstep, brush and squeeze identity) |

## 6. Done today (for reference)

- **Office:** redo, kit round 2, piles. Cut-room dressing fix (`Occupancy.Joined`); kit cache reset (`ClearCache` + the importer hook).
- **Era-lock fixes:** labels 1989/1990, CRT thumbwheels, docstrings. The copier was done by 平面视觉.
- **Hunter:**
  - research (01–04, 10, critic) and the squeezed-giant brief (11);
  - blockouts A–D (human scale, round 1) and giants A–D (four poses, round 2);
  - in-engine renders and the Figma section 2331:852, HR01–HR16.
- **Relay rig hooks:** Search state, SetListenTarget, DoorBlow, Step, CeilingHeight, DoorSqueeze, CeilingBrush, Squeeze, PressesCeiling. The map chat has wired them.
- **iCloud conflict copies:** the " 2" files in my folders were quarantined.
