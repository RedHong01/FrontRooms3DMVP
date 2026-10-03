# 10 — Interaction, glass and render-quality audit (for Red)

Date: 2026-10-02. Status: COMPLETE (synthesis of 01–05; about 21:15).
Read-only audit. Nothing in the project was changed except files in this folder.

This is the synthesis of five sibling reports in this folder:
[01 interaction inventory](01_interaction_inventory.md), [02 glass and breakables](02_glass_and_breakables.md),
[03 rendering quality](03_rendering_quality.md), [04 AAA references](04_aaa_references.md),
[05 in-engine evidence](05_in_engine_evidence.md) (81 frames from the real game camera, 55 in `images/`).

**How to read the citations.** `file:line` is relative to `Frontrooms3D/`. Short names:

| Short name | File |
|---|---|
| `Game.cs` | `Assets/Scripts/FrontRooms3DGame.cs` |
| `MapWorld.cs` | `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs` |
| `Hunter.cs` | `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs` |
| `Units.cs` | `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs` |
| `SoundDirector.cs` / `DoorSound.cs` / `SoundIds.cs` | `Assets/Scripts/Audio/FrontRooms{SoundDirector,DoorSound,SoundIds}.cs` |
| `Look.cs` / `PostStack.cs` | `Assets/Scripts/Rendering/FrontRooms{Look,PostStack}.cs` |
| `RenderSetup.cs` | `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs` |
| `Build.cs` | `Assets/Editor/FrontRooms3DBuild.cs` |
| `Surface.shader` | `Assets/Resources/Rendering/FrontRoomsSurface.shader` |
| `URP.asset` | `Assets/Settings/FrontRooms_URP.asset` |
| `Level0.asset` | `Assets/Levels/FrontRoomsLevel0.asset` |
| other scripts | `FrontRoomsRoomStream.cs`, `FrontRoomsRelayRig.cs`, `FrontRoomsHunter.cs` are in `Assets/Scripts/`; `FrontRoomsMapWalker.cs`, `FrontRoomsLevelProfile.cs` are in `Assets/Scripts/FrontRoomsMap/` |

Line numbers were re-read for this report at about 21:05 on 2026-10-02 (`MapWorld.cs` saved 20:58,
`Game.cs` 21:02). The map chat is still editing those files, so the symbol named next to each line
is the stable anchor. Line numbers in the sibling reports are a few lines older in places.

Tags: **UNVERIFIED** = not confirmed in code, in engine or on a page that was read.
**ESTIMATE** = engineering judgement, not a measurement.

---

## 1. Verdict

Red is right on all three counts, and each has a specific cause.

1. **No interaction has a shot.** Every interaction is "press E, the world changes in one frame, a HUD line explains it". Keys do nothing in the shipped level (`doorsNeedKeys: 0`), and a keyed door opens with the same 0.55 s swing as any other door. Glass is deleted, not broken. There is also nothing to stage a shot with: the camera only moves during the window climb, and there are no hands.
2. **The glass is a lit, pale veil on a 30 mm box, and there is nothing in the world for it to reflect.** There is no reflection probe, no skybox, and reflection intensity is 0.3. That same gap makes every metal and gloss surface in the game look like plastic.
3. **The URP settings are fine. What we feed them is not.** The game already runs Forward+, HDR, 4x MSAA, SSAO and a full film post stack at about 14 ms per 1080p frame (M3 Max, editor). It reads as "low level" because of primitive cubes for keys, doors and panes, a capsule Relay, lamp shadows erased by a 162° cone, a fill light leaking through every ceiling, and no reflections. Also, the builds in `Builds/` were made before URP was added. Don't use them to judge the look.
4. **AAA is a platform question.** The things that make these shots read as AAA are timing, staging, debris and reflections. A desktop build can do all of them, and so can WebGL2. The lighting and reflection quality of a modern AAA frame is out of reach on WebGL2 and partly within reach on a desktop URP build. My recommendation is to make the Mac desktop build the quality bar and treat WebGL as a reduced tier.

---

## 2. Findings, ranked

Severity: **S1** breaks immersion or blocks the fix; **S2** reads noticeably cheap; **S3** polish.
Effort: **S** ≤ 1 day, **M** 1–3 days, **L** > 3 days (ESTIMATE). Frame cost: **N** < 0.2 ms, **L** 0.2–0.7 ms,
**M** 0.7–2 ms, **H** > 2 ms at 1080p on a desktop GPU (ESTIMATE; nothing was GPU-profiled, see 03 §1.12).
Owners: **map** = map chat (game flow, interactions, camera, player, Relay AI); **visual** = visual chat
(rendering, post, prop kit, Blender, RoomStream); **sound** = sound chat (FMOD). The first owner listed leads.

| # | Sev | Finding | Owner | Effort |
|---|---|---|---|---|
| F1 | S1 | Using a key has no shot, and keys do nothing in the shipped level | map + visual + sound | M |
| F2 | S1 | Glass is deleted in one frame; the hold shows nothing while the sound cracks | visual + map + sound | M |
| F3 | S1 | The window pane is a lit pale veil on a 30 mm box | map + visual | S |
| F4 | S1 | Nothing in the world can be reflected (no probe, no sky, intensity 0.3) | visual | S |
| F5 | S1 | Light has no structure: lamp shadows erased, fill leaks through ceilings | map + visual | S |
| F6 | S1 | No camera system: no takeover, no FOV/shake layers, no viewmodel mount | map (+ visual for post) | M |
| F7 | S1 | The builds on disk are not the URP game, and the Mac build menu removes URP | unassigned (map by default) | S |
| F8 | S1 | Caught is a same-frame hard cut to a white card; the Relay is never framed | map + visual + sound | M |
| F9 | S1 blocker | Particle and animation modules are not installed | visual (Red approves) | S |
| F10 | S2 | Primitive content in every hero position (key, doors, Relay, map troffers) | visual + map | L |
| F11 | S2 | The Relay's door break is visually inert, with a handle sound on a smash | map + visual + sound | M |
| F12 | S2 | The six quality levels are one tier; AA is fixed; WebGL limits are unplanned | visual | M |
| F13 | S2 | The window climb has no glass, no plant, no tilt | map + sound | S |
| F14 | S2 | Key pickup is an automatic vacuum of a spinning yellow box | map + visual | S |
| F15 | S2 | The chase is told by HUD text and an exact metre readout | map + visual | S |
| F16 | S3 | Polish and process items (aim feedback, pause, fallbacks, duplicate loop, verification frames) | various | S each |

### F1 (S1) Using a key has no shot, and keys do nothing in the shipped level

![Key door at 0.25 s: the same swing as any door](images/60_door_key_open_t0250ms.png)

- **Player sees:** with a key held, E on a door gives the same 0.55 s swing as a door that never needed one, frame for frame. Compare frames [59](images/59_door_key_open_t0000ms.png)–[62](images/62_door_key_open_t0750ms.png) with [40](images/40_door_normal_t0000ms.png)–[43](images/43_door_normal_t0750ms.png). The key never appears again after pickup. The door has no lock, lever or handle to put a key into. In the shipped level no door is ever locked, so the pickup text "KEY / OPENS THIS ZONE'S DOORS" is a promise the game does not keep. When locks are forced on, a locked press changes nothing on screen ([48](images/48_door_locked_before_hud.png), [50](images/50_door_locked_after_use_hud.png), [51](images/51_door_locked_0.5s.png)).
- **Why it reads cheap:** the most important beat in a key-and-door game is told only by a prompt string. There is no object, no camera, and no change of state you can see.
- **Evidence:**
  - `Use()` checks for the key and then runs the same `SwingAway` + `SetDoor` as any door (`MapWorld.cs:1523-1533`). There is no key-use or unlock event; the full event list is `MapWorld.cs:59-71`.
  - Locks are off in the shipped level: `doorsNeedKeys: 0` (`Level0.asset:47`), and the default is also false (`FrontRoomsLevelProfile.cs:31`).
  - The door leaf is a `CreatePrimitive(Cube)` with no hardware (`MapWorld.cs:879-883`). The title doors have handles and kick plates (`FrontRoomsRoomStream.cs:1255-1269`).
  - The key check uses the zone the **player** stands in, not the door's zone (`HasKeyHere`, `MapWorld.cs:1584`).
  - The locked feedback is a prompt (`MapWorld.cs:1513`) plus an FMOD one-shot (`SoundDirector.cs:472`).
- **Fix:**
  - Add a door state machine: Locked → Unlocking (shot) → Ajar → Open, with `DoorUnlocked` and `DoorRattled` events.
  - `Use()` must hold the door while the shot plays.
  - Visual chat ships a door leaf with a lever, a lock cylinder and a `LockAnchor` transform.
  - Fix the zone check so it uses the door's zone.
  - Turn `doorsNeedKeys` on only once the shot exists.
  - Shot designs: §3.2 and §3.4.
- **Owner · effort · frame cost · WebGL:** map + visual + sound · M · N · yes.

### F2 (S1) Glass is deleted in one frame; the hold shows nothing while the sound cracks

![First frame after the break: the pane is simply gone](images/16_window_L0_break_next_frame.png)

- **Player sees:** during the 1 s hold the pane is pixel-for-pixel unchanged ([14](images/14_window_L0_hold_0.5s_hud.png)). The only change is a 120 × 4 px bar. At 1.0 s the pane vanishes ([16](images/16_window_L0_break_next_frame.png)), and +0.25 s and +1 s are a clean empty frame ([18](images/18_window_L0_break_%2B0.25s.png), [19](images/19_window_L0_after_1s.png), [20](images/20_window_L0_after_1s_oblique.png)). A text card explains what the picture did not show ([17](images/17_window_L0_break_next_frame_hud.png)).
- **Why it reads cheap:** there are no cracks, shards, falling glass, teeth in the frame or camera reaction. Meanwhile FMOD plays two cracks and a shatter over a pane that does not change, so sound and picture disagree.
- **Evidence:**
  - `Hold()` destroys the pane at 1.0 s with `Kill(window.pane)` and raises `GlassBroken` (`MapWorld.cs:1561-1574`).
  - Letting go resets the hold to 0 (`MapWorld.cs:1580`).
  - A rebuilt chunk simply skips the pane (`MapWorld.cs:900`).
  - The hold bar is the only picture (`Game.cs:1537`).
  - FMOD cracks fire at 0.35 and 0.70 (`SoundDirector.cs:452-453`), and the shatter fires on break (`SoundDirector.cs:459-463`).
  - The legacy fallback plays the door-break clip for glass (`Game.cs:785-787`).
- **Fix:**
  - Show crack stages on the existing 0.35 / 0.70 / 1.0 beats.
  - At the break, swap in a pre-fractured pane: inner pieces fly, middle pieces drop, edge pieces stay as teeth.
  - Settled glass becomes static meshes and persists per window.
  - Cracks persist when the player lets go.
  - Shot and spec: §3.5, §4.
- **Owner · effort · frame cost · WebGL:** visual (shader, fracture assets) + map (break state, events) + sound (stage-driven cracks, shard tail) · M · L for about 2 s during a break, N after (≤ 24 rigidbodies, 150–250 mesh particles, 3–5 extra draws; 02 §8.7) · yes, with fewer particles.

### F3 (S1) The window pane is a lit pale veil on a 30 mm box

![Level 0 window, intact, 1.5 m: a grey-teal haze](images/02_window_L0_intact_1.5m.png)

- **Player sees:** a cool grey-teal haze over the far room, lighter than the same view with the pane gone (compare [02](images/02_window_L0_intact_1.5m.png) with [16](images/16_window_L0_break_next_frame.png)). At grazing angles the panes turn flat pale cyan ([04](images/04_window_L0_intact_oblique.png), [23](images/23_window_Office_intact_oblique.png), [25](images/25_window_Office_intact_steep.png)). There are no smudges, no edge, and nothing holding the glass in the frame.
- **Why it reads cheap:** clear glass has almost no diffuse colour. Here 28% of a pale, lit colour is painted over the view, so the pane looks like plastic film that brightens and darkens with the lamps.
- **Evidence:**
  - The material is built in code as URP Lit Transparent, base (.75, .85, .88, **.28**), smoothness .9 (`MapWorld.cs:1660`, `TransparentGlass` at `:1663-1680`).
  - The pane is a primitive cube (`MapWorld.cs:901-905`), 30 mm thick (`GlassThickness = .03f`, `Units.cs:61`).
  - The frame is two jambs and a head, with no glazing stop or sill trim (`MapWorld.cs:860-866`).
  - The ShadowCaster pass is left on (05 runtime dump: `shadowCastingMode On`). Whether that throws a visible solid shadow is UNVERIFIED (05 §H).
- **Correction to the brief:**
  - The blend is not the bug. One-plus-premultiply ("Alpha + Preserve Specular") keeps reflections at full strength, because only the diffuse part is multiplied by alpha (URP 17.3 `BRDF.hlsl:65-72`, per 02 §4.1).
  - URP Lit already has a Fresnel term (02 §4.1).
  - Two experiments show that changing values alone is not enough. A probe alone barely changes the pane ([07](images/07_window_L0_EXPERIMENT_with_probe.png)). Clear values plus a probe make the pane invisible ([08](images/08_window_L0_EXPERIMENT_clear_glass_probe.png), [11](images/11_window_L0_EXPERIMENT_clear_glass_probe_1.5m.png)).
- **Fix:**
  - Make the pane 6 mm, in a glazing stop with a sill trim.
  - Turn shadows off on the pane.
  - Give the edge faces their own green material.
  - Use a shared `FrontRooms/Glass` material: near-black base, Fresnel-driven alpha, smudge and dust maps driving roughness.
  - The pane also needs F4 (something to reflect). Spec: §4.
- **Owner · effort · frame cost · WebGL:** map (pane build, uses the asset) + visual (shader, material) · S for geometry and values, M for the Shader Graph · N · yes.

### F4 (S1) Nothing in the world can be reflected

- **Player sees:** every glossy surface reflects nothing but lamp highlights: glass, VCT floors, damp carpet, chrome, brass, gloss paint and metal louvers. Glass at grazing angles shows a generic sky inside a windowless office ([23](images/23_window_Office_intact_oblique.png)).
- **Why it reads cheap:** reflections are the main cue that a material is glass, metal or wet. Without them, metal reads as dark plastic and floors read as flat paint.
- **Evidence:**
  - The game scene has no skybox (`Assets/Scenes/FrontRooms3D.unity:29`), and the map clears it again at runtime (`MapWorld.cs:492`).
  - Reflection intensity is 0.3 (`Look.cs:20,30`; scene `:38`).
  - At runtime there are 0 reflection probes, and the default reflection is Unity's "Default-Skybox-Cubemap" at 128 px (05 §A).
  - Box projection and probe blending are both off (`URP.asset:54-55`).
  - `Surface.shader` (used by 83 of the 86 materials in `Assets/Resources/Surfaces`) declares no reflection-probe keywords (`Surface.shader:96-110`), so it cannot box-project probes even if they are turned on.
- **Fix:**
  - Step 0: capture one HDR cubemap per zone type and set it as the custom default reflection, swapped per zone. Raise the intensity to about 0.8.
  - Step 1: spawn a Custom, box-projected probe per room at chunk build, and add the probe keywords to `Surface.shader`.
  - Details: §4.2.
- **Owner · effort · frame cost · WebGL:** visual (capture, Look API, shader keywords) + map (per-room probe spawn) · S (step 0), M (step 1) · N (baked cubes) · yes (baked). Avoid realtime probes on the web.

### F5 (S1) Light has no structure: lamp shadows erased, fill leaks through ceilings

![Level 0 corridor: even wash, contact shadows only from SSAO](images/01_rep_L0.png)

- **Player sees:** an even wash with no readable pools. Wall bases, furniture and the Relay's feet sit on the floor with no contact shadow ([01](images/01_rep_L0.png), [34](images/34_rep_Office.png), [37](images/37_rep_Dark.png)).
- **Why it reads cheap:** AAA interiors read through contrast: a pool under each lamp, falloff up the walls, dark gaps and grounded objects.
- **Evidence:**
  - Map lamps are 162° spots (`MapWorld.cs:1058`).
  - About one lamp in three may cast a shadow (`MapWorld.cs:1069`), and only within 9 m (`MapWorld.cs:1122`; `Level0.asset:49`). At runtime, 9 lights were shadowed (05 §A).
  - URP 17.3 scales spot shadow bias with tan(angle/2) × range. For 162°/10 m that is roughly 9–13 cm of bias, which erases contact shadows (03 §1.8, from `ShadowUtils.cs:390, 414-447` in the package).
  - A directional fill light with only 0.18 shadow strength lights through every ceiling (`Game.cs:267-275`).
  - Indirect light is one flat three-colour ambient for the whole world (`Look.cs:24-29`). The surface shader only samples SH (`Surface.shader:240`).
- **Fix:**
  - Give shadowed lamps a cone of about 115° with a troffer cookie, which cuts the bias to about 3 cm (03 §1.8).
  - Shadow the nearest N lamps instead of using a 1-in-3 hash.
  - Remove the directional fill and its shadow map.
  - Swap the ambient per zone.
  - Use the same lamp shape in the title stream (`FrontRoomsRoomStream.cs:1101,1109`).
- **Owner · effort · frame cost · WebGL:** map (MapWorld lamps, fill light) + visual (stream lamps, cookie, Look API) · S · M for the shadows, partly paid back by removing the main-light shadow pass · yes, with 4 shadowed lamps at 512 px.

### F6 (S1) No camera system

- **Player sees:** a perfectly still camera in every moment: no lean, push-in, shake, FOV change, bob or reaction. The only motion is the climb duck.
- **Why it reads cheap:** every shot Red asked for is camera work, and there is nothing to do it with.
- **Evidence:**
  - Yaw and pitch are written directly every frame (`Game.cs:830-831`).
  - The camera's local position is only written at start and by the climb (`Game.cs:565, 928, 932`).
  - FOV is fixed at 76 (`Game.cs:225`).
  - The only component added to the camera is the hum AudioSource (`Game.cs:1022`).
  - Nothing drives post from gameplay; the post stack only configures the camera (`PostStack.cs:66-73`).
  - The map test walker duplicates the whole E / hold-E loop (`FrontRoomsMapWalker.cs:119-138`).
- **Fix:**
  - Build one camera rig in the map chat. It needs:
    - base look;
    - additive offset, FOV and shake layers;
    - a takeover that blends to an anchor pose;
    - a lock on movement and look, with a look cone;
    - a cancel policy.
  - Add a post "shot" and "pulse" API in the visual chat.
  - Both the game and the map walker use the same rig.
  - Contract: §6.4.
- **Owner · effort · frame cost · WebGL:** map (rig) + visual (post API) · M · N · yes.

### F7 (S1) The builds on disk are not the URP game, and the Mac build menu removes URP

- **Player sees:** anyone running `Builds/Mac` or `Builds/WebGL` sees a pre-URP game: no surface shader, no SSAO and no post.
- **Evidence:**
  - The Mac build was written Oct 1 19:08–19:32 and the WebGL build at 17:49. The URP asset was created at 19:54–20:04 (03 §1.1). The Mac player has no URP runtime DLL (02 §2, 03 §1.1).
  - `BuildMac()` sets `GraphicsSettings.defaultRenderPipeline = null` and `QualitySettings.renderPipeline = null` before building (`Build.cs:61-62`). The second line clears only the active quality level. The Standalone default level (5) still points at URP (`ProjectSettings/QualitySettings.asset:338`). So which pipeline a new Mac player runs is UNVERIFIED (02 and 03 disagree), but it is a trap either way. It also leaves the open editor's active level with no pipeline until rendering setup runs again.
  - The playtest autopilot's look-around and Relay frames are rendered through `Camera.CopyFrom` (`Game.cs:1899, 1924, 1941`), which leaves URP post off. Those frames have no tonemapping or grade (05 frame [36](images/36_rep_Office_b_AUTOPILOT_STYLE_camera.png) against [35](images/35_rep_Office_b.png)).
- **Fix:**
  - Delete the two lines.
  - Fail the build if no render pipeline is set.
  - Rebuild the Mac player.
  - Judge the look only from a fresh URP player or the editor Game view.
  - Fix the autopilot capture to copy the URP camera data.
- **Owner · effort · frame cost · WebGL:** build-script owner. It is unassigned; Red decides, and the map chat is the default. · S · N · yes.

### F8 (S1) Caught is a same-frame hard cut to a white card; the Relay is never framed

- **Player sees:** at 0.7 m the game cuts, in the same frame, to a near-opaque bone-white card reading "CAUGHT". There is no turn to the Relay, no grab and no fall. In the witness frame before the catch, the Relay's capsule torso fills the screen with visible polygon edges ([80](images/80_relay_broken_%2B1000ms.png)).
- **Why it reads cheap:** the moment the whole game builds toward has no picture.
- **Evidence:**
  - `Caught` carries no position (`Hunter.cs:238-242`) and is wired to `End()` (`Game.cs:591, 1568-1574`).
  - The overlay is (.93, .92, .88, .98) (`Game.cs:1452`), with the card text at `Game.cs:1479`.
  - The sound side already hard-cuts to silence and plays `Tinnitus` (`SoundDirector.cs:500-510`).
- **Fix:** a 2 s caught sequence before the card (§3.8). It needs the Relay's position with the event, a lunge pose, and a better Relay model, or at least a silhouette framing until the model lands.
- **Owner · effort · frame cost · WebGL:** map (sequence, event) + visual (Relay model and pose, post hit) + sound (impact timing) · M · N · yes.

### F9 (S1 blocker) Particle and animation modules are not installed

- **Evidence:** `Packages/manifest.json:1-13` and `Packages/packages-lock.json` contain no `com.unity.modules.particlesystem`, `com.unity.modules.animation`, `com.unity.timeline`, `com.unity.cinemachine` or `com.unity.visualeffectgraph`. Physics is installed (`manifest.json:6`).
- **Impact:** shard and glint particles, dust and splinters cannot use Shuriken until the particle module is enabled. Authored hand or key clips cannot play without the animation module. Rigidbody shards and code-driven tweens work today.
- **Fix:**
  - Enable `com.unity.modules.particlesystem` only. This is a one-line manifest change.
  - The recommended camera language (§3) needs no Animator, Timeline or Cinemachine.
  - VFX Graph is out on WebGL2 because it needs compute shaders (02 §6.7, 04 S23).
- **Owner · effort · frame cost · WebGL:** visual, with Red's approval · S · depends on use · yes. The extra WebGL download size is UNVERIFIED.

### F10 (S2) Primitive content in every hero position

![Key from 2 m: a pale yellow brick](images/52_key_2m.png)

- **Player sees:** the key is a 0.32 × 0.12 × 0.12 m emissive yellow box ([52](images/52_key_2m.png)). Doors are plain veneer slabs ([60](images/60_door_key_open_t0250ms.png)). The Relay is capsules and boxes with a floating torso ([70](images/70_relay_break_witness_t1000ms.png), [78](images/78_relay_broken_%2B0250ms.png), older rig). The map troffers are flat white quads ([01](images/01_rep_L0.png)).
- **Evidence:**
  - Key: `MapWorld.cs:731-736`, material `MapWorld.cs:1659`.
  - Door leaf: `MapWorld.cs:879-883`.
  - Map lens: a plain emissive material on a cube (`MapWorld.cs:1633, 1039-1045`), while the textured `Troffer_Lens` exists (02 §3).
  - Relay: driven in code, with no Animator (`FrontRoomsRelayRig.cs:137`).
- **Fix:** in order:
  1. Use the textured lens in the map (hours).
  2. A brass key on a ring with a paper zone tag, no emission.
  3. A door leaf prefab with a lever, a lock cylinder and a kick plate, matching the title doors.
  4. A real Relay model; the rig is already being reworked.
- **Owner · effort · frame cost · WebGL:** visual + map · L in total (lens S, key S, door M, Relay L) · L · yes; add LODs for props.

### F11 (S2) The Relay's door break is visually inert

![Relay break, t = 1.0 s: the door is perfectly still, and the HUD still offers to open it](images/71_relay_break_t1000ms_hud.png)

- **Player sees:**
  - Through 2.5 s of blows, the door does not move, and the HUD still offers "E · OPEN DOOR" ([71](images/71_relay_break_t1000ms_hud.png), [74](images/74_relay_break_t2500ms.png)).
  - Then the intact leaf swings open in about 0.25 s, with no splinters, damage or shake ([75](images/75_relay_broken_%2B0000ms.png) → [78](images/78_relay_broken_%2B0250ms.png)).
  - The hinge sound component plays Handle + Unlatch on the smash.
- **Evidence:**
  - Blows are sound-only events (`Hunter.cs:862-879`, `DoorBlow` at `:868`).
  - `BreakDoor` just swings the door (`MapWorld.cs:1004-1013`), using the 0.18 s broken speed (`MapWorld.cs:1594`).
  - The Handle and Unlatch one-shots fire whenever the leaf leaves the frame (`DoorSound.cs:89-92`).
  - The prompt only hides once the door is already broken (`MapWorld.cs:1510`).
- **Fix:**
  - Each blow jolts the leaf. Damage shows at blows 3 and 4. The break throws the leaf open past the stop, with splinters and a bounce, and the leaf hangs crooked.
  - Hide the prompt while a door is being broken.
  - Suppress Handle and Unlatch for broken doors.
  - Shot: §3.7.
- **Owner · effort · frame cost · WebGL:** map (leaf jolts, state) + visual (damaged leaf variants, splinters) + sound (suppress handle) · M · L for a moment · yes.

### F12 (S2) The six quality levels are one tier; AA is fixed; WebGL limits are unplanned

- **Evidence:**
  - All six levels point at the same URP asset, and the setup script forces that on every run (`RenderSetup.cs:47-54`).
  - Camera AA is forced to None, so 4x MSAA is the only AA (`PostStack.cs:72`). MSAA does not fix specular or texture shimmer (03 §2.7).
  - On WebGL2, URP 17.3 compiles 32 visible lights (03 §1.8). The map can have about 80 lamps live within 16 m.
  - The WebGL template does not cap the device pixel ratio. The cost of that is UNVERIFIED (03 §1.5).
- **Fix:** three tiers (Web / High / Cinematic), each with its own URP asset (§5).
- **Owner · effort · frame cost · WebGL:** visual · M · tier-dependent · the Web tier is the WebGL plan.

### F13 (S2) The window climb has no glass, no plant, no tilt

- **Evidence:** the climb is a 0.6 s lerp with a 0.35 m lift and a 0.55 m duck. No pitch or roll is authored, and it cannot be interrupted (`Game.cs:153, 920-933`). The only sound is FMOD Cloth. There is no glass to crunch, because none is left.
- **Fix:** §3.6.
- **Owner · effort · frame cost · WebGL:** map + sound · S · N · yes.

### F14 (S2) Key pickup is an automatic vacuum of a spinning yellow box

- **Evidence:** the key's collider is removed (`MapWorld.cs:733`). It spins at 90°/s (`MapWorld.cs:1610`) and is collected by walking within 0.9 m (`MapWorld.cs:1612`). There is no prompt or look check, and it is destroyed in one frame ([55](images/55_key_pickup_frame.png), [56](images/56_key_pickup_%2B2f_hud.png)).
- **Fix:** look-and-press pickup with a short presentation (§3.1).
- **Owner · effort · frame cost · WebGL:** map + visual · S · N · yes.

### F15 (S2) The chase is told by HUD text and an exact metre readout

- **Evidence:** the threat panel shows "RELAY / CHASE" and "RELAY nn M" (`Game.cs:1523, 1528`). The camera and post do not react when the Relay sees the player.
- **Fix:**
  - Replace the metre count with a post pulse (vignette, grain and CA rising with the Relay's proximity).
  - Add a small camera tremor while seen, with a motion toggle.
  - Keep the state word only if Red wants it.
- **Owner · effort · frame cost · WebGL:** map (HUD, trigger) + visual (pulse profile) · S · N · yes.

### F16 (S3) Polish and process

- The aimed object has no highlight, and prompts pop on and off with no fade (01 G18).
- Pause does not pause FMOD, and restart is a hard cut (01 G19).
- If FMOD fails, glass plays the door-break clip (`Game.cs:787`), while `FrontRoomsAudio.Glass()` is never called (02 §8.1).
- The key panel always reads "LEVEL 0 KEY", even in Office zones (`Game.cs:1401`).
- `Documentation/LIGHTING_SPEC.md` no longer matches the code (03 §1.13).
- Notes and reading are documented (`Documentation/UI_SYSTEM.md:34`) but not implemented. Whether they are still planned is UNVERIFIED.

---

## 3. Shot designs

### 3.0 One camera language: B, "the object is the actor"

From the three languages in 04 §4, I recommend **B**: the camera pushes in, and the key, lever, bolt, leaf and glass do the acting. There is no hand rig.

Why B:

1. **It is what Red described.** "The camera pushes in to the key opening the door" and "the glass shatters": in B the camera makes the push-in, and the key and the glass carry the action.
2. **It fits the code we have.** Doors, the climb and the Relay rig are already driven by code with no Animator (`MapWorld.cs:1589-1600`, `Game.cs:920-933`, `FrontRoomsRelayRig.cs:137`). B needs no Animation module, Timeline or Cinemachine (F9). Only the particle module is needed, for glints and dust.
3. **Every shot can be cancelled.** The core loop is being hunted by sound, so a shot must abort when the Relay arrives. B shots are short and can do that. Hand clips tend to become "a little cutscene" (04 S26).
4. **It is cheap on WebGL:** transforms, a few rigidbodies and a post volume.
5. **A (hands) stays the upgrade path.** It reads best in a still frame, but it has the highest cost and risk: bad hands look worse than none (04 S15). B's anchors and timings are exactly what a hand clip would hit, so nothing in B is thrown away.
6. **C (camcorder grammar) is the most on-brand, but not now.** Its signal is deliberate analog damage: tears, exposure pumps, focus hunting. Red's complaint today is that the game looks low-level, so C should wait until the clean version reads as high quality. The only thing taken from it is ordinary focus on the lock in the key shot.

One allowed upgrade inside B: if the floating key reads as telekinetic in the test capture, add one **posed** hand mesh holding the key bow. It is a rigid pose moved by the same code, so it still needs no Animator. Red decides after seeing a 10-second capture (§6, item 1.9).

**Rules shared by all shots**

- All beat times live in one shared table in code (for example, a `FrontRoomsShotTimings` class). The map chat reads it for picture and the sound chat for events. Today the 0.35 / 0.70 crack beats are literals in the sound director (`SoundDirector.cs:452-453`), and the 1 s hold is a literal in the map (`MapWorld.cs:1566`).
- The camera moves by position dolly and rotation. FOV changes are kept to ≤ 15° and take ≥ 0.4 s; fast FOV shifts are a listed camera mistake (04 C2, S16).
- Shake is rotation only, in degrees, and decays.
- A "Camera motion" setting (off / 50% / 100%) scales shake, roll, dips and FOV punches (04 S19). Every hold has a tap alternative in settings (04 S20).
- Input notation: **Move** means WASD and sprint; **Look** means the mouse. "Cone ±n°" means look is clamped around the shot direction.
- There is one post profile per shot type, blended by weight: Gaussian DOF on the Web tier, Bokeh on desktop, and no motion blur on the Web tier (03 §6, item 8).
- Existing FMOD events are named as they appear in `SoundIds.cs:15-46`. Names marked **NEW** are proposals for the sound chat, following the same path style.
- All times are ESTIMATES. Tune them on a capture.

### 3.1 Key pickup

**Input lock:** none. **Duration:** 0.95 s.

**Trigger:** the key is aimed within the 2.4 m reach and the prompt reads "E · TAKE KEY". This needs the key's collider back (`MapWorld.cs:733`). The key rests on a surface (desk, cabinet or hook) where furnishing allows, otherwise on the carpet. It does not spin or glow (F10).

| t (s) | Camera | Object / VFX | Sound | Map event |
|---|---|---|---|---|
| 0.00 | Only if the mouse is idle: pitch eases ≤ 6° toward the key (0.2 s, ease-out). Released as soon as the mouse moves. | The key lifts off its surface. | — | `KeyPickupStarted(zone, pos)` NEW |
| 0.00–0.25 | — | The key travels to a held pose 0.35 m ahead, lower right of frame (about 65% across, 70% down), ease-out, and turns so its paper zone tag faces the lens. | — | — |
| 0.25 | — | The key arrives. The tag swings (damped, two swings). | `Foley/Player/KeyPickup` (exists; fires at pickup today, `SoundDirector.cs:474`) | `KeyTaken(zone)` (exists, moved to this beat) |
| 0.25–0.75 | — | The key is held; the brass catches lamp highlights (needs F4). | — | — |
| 0.75–0.95 | — | The key drops out of the bottom of the frame (pocketed), ease-in. | `Foley/Player/Pocket` NEW at 0.85 | — |
| 0.95 | — | A small key glyph with the zone label appears in the HUD. | — | — |

**HUD:** drop the "OPENS THIS ZONE'S DOORS" flash until keys open doors (F1).
**WebGL fallback:** identical.

### 3.2 Unlocking a locked door with the key (Red's example)

**Input lock:** yes. Move is locked from 0.00 to 1.45 s. Look is locked from 0.00 to 1.30 s, then blends back over 0.2 s.
**Duration:** 1.55 s. **Commit point:** 0.86 s. After that the door counts as unlocked even if the shot is cancelled.

**Trigger:** E on a locked door while holding **that door's** zone key.

**Anchor:** the module spec already fixes the lock and handle point at 1.0 m up, 0.08 m in from the latch jamb and 0.03 m proud of each face. It is "the point `DoorUnlocked` reports" (`Documentation/LEVEL_MODULE_SPEC.md:48`), and the constants exist (`Units.cs:58`, `DoorHandleHeight/Inset/Proud`). No code raises `DoorUnlocked` yet (grep at 21:10).

**Framing pose P:** the lock point + 0.45 m along the door normal toward the player + 0.06 m up, looking at the lock.

| t (s) | Camera | Object / VFX | Sound | Map event |
|---|---|---|---|---|
| 0.00 | The shot starts and blends from the eye toward P. Position uses a cubic ease-in-out; rotation slerps to look at the cylinder. Travel takes 0.30 + 0.12 × distance in metres, clamped to 0.35–0.55 s. | The prompt hides. The shot volume goes 0 → 1 over 0.40 s: DOF focused on the cylinder, vignette +0.1, post-exposure +0.15. | `Snapshot/Closeup` NEW (room tone ducked about 3 dB) | `ShotStarted(UnlockDoor)` NEW |
| 0.00–0.45 | FOV 76 → 62 on the same curve. | — | — | — |
| 0.30–0.55 | Arrived; slight hand-held drift of 0.1° (motion setting). | The key enters from lower right and travels to 3 cm in front of the keyway, ease-out, rolling to align. | — | — |
| 0.55–0.68 | — | The key slides 2.5 cm in, with a 30 ms catch at 60% (the pins). | `Mechanism/Lock/KeyInsert` NEW at 0.55 | — |
| 0.68–0.90 | A 0.2° roll follows the turn. | The key turns 90°: the first 10° slow (resistance), then ease-out. | `Mechanism/Lock/KeyTurn` NEW at 0.68 | — |
| 0.86 | 0.3° rotation jolt, 80 ms. | The bolt retracts: the leaf shifts 1.5 mm in the frame. | `Mechanism/Lock/BoltRetract` NEW at 0.86 | `DoorUnlocked(pos, zone)` NEW (commit) |
| 0.90–1.15 | — | The key turns back and withdraws; it is out of frame by 1.15. | tail of KeyTurn | — |
| 1.00–1.25 | — | The leaf pops ajar to 10°, ease-out with a 1° overshoot. | `Mechanism/Door/Handle` + `Unlatch` (exist). `DoorSound.cs:89-92` fires them by itself when the leaf leaves the frame. | `DoorMoved` (exists) |
| 1.15–1.55 | The camera returns to the eye pose with the player's pre-shot yaw and pitch, cubic ease-in-out. FOV 62 → 76. | The shot volume goes 1 → 0. | snapshot released | — |
| 1.30 / 1.45 | Look returns (0.2 s blend), then move. | — | — | `ShotEnded` NEW |

**After:** the door rests ajar at 10°. Walking into it pushes it open (the RE7 "ajar, then push", 04 K3), or E swings it fully. Push speed sets the Relay noise: a fast push slams at 14 m as today (`Game.cs:778`), a slow push creaks at about 5 m. That is a design change for Red (§7).

**Cancel (before 0.86 s):** the Relay enters Chase or comes within 6 m with line of sight, or the player presses S or Esc after 0.2 s. The key withdraws in 0.15 s, the camera returns in 0.25 s, and the door stays locked. After 0.86 s the turn always completes.

**Light:** an optional small, unshadowed "shot light" on the camera at 0.6 intensity during the shot, so the brass reads under a dead lamp. It costs one of the 32 WebGL lights (F12).

**WebGL fallback:** Gaussian DOF (start 0.6 m, end 2.5 m) instead of Bokeh, no motion blur, and the shot light only if under the light cap.

### 3.3 Opening a door normally

**Input lock:** none. **Duration:** 0.75 s.

| t (s) | Camera | Object | Sound | Map event |
|---|---|---|---|---|
| 0.00 | A 0.3° forward pitch impulse (the push), decaying over 0.15 s (motion setting). | The lever rotates down 35° in 0.08 s. | — | — |
| 0.08 | — | The leaf starts: 95° over 0.55 s with ease-out, because a pushed door starts fast and slows. Today it is smoothstep (`MapWorld.cs:1595-1596`). | `Handle` + `Unlatch` (automatic, `DoorSound.cs:89-92`); `Swing` loop driven by angular velocity (exists) | `DoorMoved` (exists) |
| 0.12–0.22 | — | The lever springs back. | — | — |
| 0.63–0.75 | — | A 2° overshoot at the stop, then it settles. | `StopLimit` with Impact from speed (exists, `DoorSound.cs` `EndMotion`) | — |

**Option for Phase 2 (needs Red):** holding E opens slowly with a creak over 1.6 s, at half the noise radius. This is Outlast's two door speeds (04 S29).
**WebGL fallback:** identical.

### 3.4 The locked-door rattle (no key)

**Input lock:** none. **Duration:** 0.40 s.

| t (s) | Camera | Object | Sound | Map event |
|---|---|---|---|---|
| 0.00 | — | The lever goes down 20° and stops hard (0.05 s). | `Mechanism/Door/Locked` (exists), authored as two rattles 0.16 s apart | `DoorLocked` (exists), plus a 6 m Relay noise NEW (design) |
| 0.05 | 0.25° forward impulse. | The leaf jolts 2 mm / 0.3° toward the player against the bolt and springs back in 0.06 s. | — | — |
| 0.16 | 0.25° impulse. | A second jolt. | — | — |
| 0.20–0.40 | — | The lever returns. | — | — |

**Lock state you can see:** a brass deadbolt cylinder with a small zone tag plate beside it. Then the prompt "LOCKED · NEEDS THIS ZONE'S KEY" can shrink to "E · TRY DOOR", followed by "LOCKED" for 1.5 s after a try. Also fix the zone check (F1).
**WebGL fallback:** identical.

### 3.5 Hold to break glass: crack stages and the shatter (Red's example)

Keep the existing 1.0 s hold and its FMOD beats at 0.35, 0.70 and 1.0 (`SoundDirector.cs:452-453`). In B the body is shown through the camera: the hold reads as three shoulder shoves that land on those beats.

**Input lock:** Move is locked while E is held. Look is limited to a cone of ±8° around the hit point; looking off the pane cancels, as it does today.
**Release:** cracks do not heal. The next hold resumes from the stage already reached (02 §8.5).
**Tap mode (setting):** three taps give three stages.

Time = hold progress × 1.0 s. The impact point is the aim ray's hit point, clamped at least 0.2 m from the frame.

| t (s) | Stage | Camera | Glass / VFX | Sound | Map event |
|---|---|---|---|---|---|
| 0.00–0.35 | Push | Lean 5 cm toward the pane; FOV 76 → 73 (sine ease). | A palm smudge fades in at the impact point (smoothness drops locally). The pane bows ≤ 3 mm (vertex offset), so its reflections swim. | `Mechanism/Window/Stress` loop with `Progress` (exists) | `GlassHold(pos, p)` (exists; add the hit point) |
| 0.35 | Crack 1 | Shove: a 4 cm forward jab and back over 0.12 s, plus a 0.4° rotational shake for 120 ms. | The crack mask reveals 5–7 radial cracks reaching 25–35% of the way to the frame, over 60 ms. 3–6 chips fall. | `Mechanism/Window/Crack` (exists) | `GlassCracked(pos, 1, uv)` NEW |
| 0.35–0.70 | Spread | The lean holds. | The cracks creep (the mask threshold follows progress). | the stress loop roughens | — |
| 0.70 | Crack 2 | Shove 2; 0.6° shake. | The radial cracks reach the frame. One or two concentric rings appear 8–20 cm around the impact. Each segment tilts a fraction of a degree, so the reflection breaks into facets (needs F4). | `Crack` (exists) | `GlassCracked(pos, 2, uv)` NEW |
| 0.70–1.00 | Creak | — | The inner pieces shift 1–3 mm away from the player. | stress peaks | — |
| 1.00 | Shatter | Shove 3. Shake 1.5°, decaying over 250 ms. FOV punch 73 → 70 → 76 over 0.3 s. The lean releases over 0.3 s. CA pulse 0.06 → 0.2 → 0.06 over 0.25 s. | Swap to the pre-fractured radial variant that matches the crack seed. Inner pieces fly away from the player at 2–4 m/s with spin; middle pieces drop with a 0–300 ms stagger; edge pieces stay as teeth. 150–250 glint mesh particles and a dust puff. | `Mechanism/Window/Shatter` (exists) | `GlassBroken(info)` (exists; add point, normal, seed and side) |
| +0.35–0.60 | Settle | — | Pieces land (a 1.2 m fall takes about 0.49 s). | `Mechanism/Window/ShardLand` NEW, at the real landing times (or baked into the Shatter tail) | — |
| +1.5 | Rest | — | Rigidbodies sleep and become one static combined mesh: the teeth plus floor glass, about two thirds of it on the far side. | — | — |
| After | — | — | The glass stays on both floors and persists per window across chunk rebuilds. | Footsteps near the window use a glass surface (NEW parameter value) | — |

The numbers come from 02 §8.3, adjusted for B.

**WebGL fallback:** if the particle module is not added, use rigidbody shards only (≤ 24) and no glints. The crack mask is one texture sample and works everywhere. No refraction.
**Desktop extra (optional):** turn on the opaque texture per camera for crack distortion (02 §6.6).

### 3.6 Climbing through the broken window

**Input lock:** Move is locked, as today. Look stays free, but pitch is eased toward the far side.
**Duration:** 0.85 s (0.6 s today). **Trigger:** as today (`TryStartClimb`, `Game.cs:891`).

| t (s) | Camera | Object / VFX | Sound | Event |
|---|---|---|---|---|
| 0.00–0.20 | Duck 0.30 m, pitch down 10° to look at the sill, roll 3° toward the leading side. | — | `Foley/Player/Cloth` (exists) | `PlayerClimbed` (exists, `Game.cs:914`) |
| 0.20 | Plant: a 0.5° jolt as weight goes onto the sill. | The bottom-rail teeth snap off as 3–5 small pieces. | `Foley/Player/ClimbSill` NEW, `Mechanism/Window/ToothSnap` NEW | — |
| 0.20–0.60 | Over the sill: the existing lift arc (0.35 m) and duck (0.55 m at mid-climb). Pitch and roll return to 0. | — | — | — |
| 0.60–0.85 | Landing: dip 6 cm and recover on a critically damped spring. | Floor shards shift. | `Foley/Player/Footstep` with Surface = Glass NEW, at 0.62 and 0.80 | Relay noise 8 m NEW (design) |

**WebGL fallback:** identical.

### 3.7 The Relay breaking a door (seen from the player's side)

**Input lock:** none; the player must be able to run.
**Duration:** 2.5 s of blows (`breakDoorSeconds`, `FrontRoomsHunter.cs:21`), then a 0.4 s break.

| t (s) | Camera (only when the player is within 8 m) | Door / VFX | Sound | Event |
|---|---|---|---|---|
| each blow (every 0.5 s) | Rotation shake from 0.2° rising to 0.6° with the blow count, 150 ms. | The leaf jolts 4–8 mm / 0.6–1.2° toward the player and springs back in 0.12 s. Dust falls from the head. A sliver of far-side light shows at the latch-side gap. | `Mechanism/Door/Blow` with `Damage` (exists, `SoundDirector.cs:476-482`) | `DoorBlow` (exists; add the door and the blow index) |
| blow 3 | — | Damage 1: the veneer splits near the latch (texture or mesh swap). | — | — |
| blow 4 | — | Damage 2: splinters at the latch; the strike plate bends. | — | — |
| 2.5 | Shake 1.0°, decaying over 300 ms. | The leaf is thrown open in 0.12 s past the stop, bounces back to about 80° and hangs 3° crooked (hinge torn). 8–15 splinter mesh particles; the strike plate flies off. | `Door/Break` + `Door/StopLimit` with Impact 1 (exist). Suppress Handle + Unlatch for broken doors (`DoorSound.cs:89-92`). | `DoorBroken` (exists) |
| 2.5–2.8 | — | The Relay holds 0.3 s in the doorway, back-lit by the far room (the reveal). | Relay stinger as today | hunter change NEW |

Also hide the door's prompt while it is being broken (F11).
**WebGL fallback:** splinters are optional; everything else is transforms.

### 3.8 Being caught

**Input lock:** full, from 0.00. **Duration:** 2.0 s, then the card.
**Needs:** `Caught(Vector3 relayHead)`. Today `Caught` carries nothing (`Hunter.cs:241`).

| t (s) | Camera | Relay / screen | Sound | Event |
|---|---|---|---|---|
| 0.00–0.25 | Whip to face the Relay's head: yaw and pitch slerp, ease-out. FOV 76 → 68. | The Relay goes into a lunge pose and moves 0.4 m toward the camera. CA 0.06 → 0.35, vignette 0.26 → 0.5. | `Relay/Lunge` NEW | `Caught(relayPos)` (changed) |
| 0.25 | Impact: the camera is knocked back 0.15 m and rolls 8° over 0.2 s; shake 2.5°, decaying. | A 2-frame exposure flash (+1.5 EV). | Today's hard cut to silence plus `Subjective/Tinnitus` moves to this beat (`SoundDirector.cs:500-510`). | `CaughtImpact` NEW |
| 0.45–1.05 | Fall: the camera drops to 0.3 m height (ease-in) and rolls to 25°, looking up. | The Relay stands over the camera, framed against the troffers as a silhouette. | tinnitus | — |
| 1.00–1.80 | — | Fade to black. | — | — |
| 2.00 | — | The card fades in over 0.4 s, with today's text. | — | `End()` |

R skips the sequence after 0.6 s. Until the new Relay model lands, keep the Relay in silhouette (back-lit, exposure down): the current capsule rig falls apart at close range (frame [80](images/80_relay_broken_%2B1000ms.png)). The card colour (white or black) is Red's call (§7).
**WebGL fallback:** identical.

---

## 4. Glass spec

### 4.1 Pane geometry (map chat)

| Item | Today | Target |
|---|---|---|
| Thickness | 30 mm (`GlassThickness = .03f`, `Units.cs:61`) | 6 mm (real float glass; 02 §5) |
| Glazing stop | none: the frame is two jambs and a head (`MapWorld.cs:860-866`) | A stop on both faces, all four sides, 18 mm wide × 12 mm deep, in the trim material |
| Sill | bare wall block under the opening (`MapWorld.cs:853`); the module spec says "no sill trim" (`LEVEL_MODULE_SPEC.md:49`) | A stool trim 25 mm proud. The spec line needs updating. |
| Edge faces | same material as the face | `Glass_Edge`: near-opaque green, linear (.28, .42, .34), smoothness .6. Real float glass edges look green (02 §4.3). |
| Shadow casting | On (05 runtime dump) | Off on the pane renderer |
| Collider | box | Keep it. It is the aim target and it blocks the Relay's sight (01 §I16). |
| Material | `TransparentGlass` built in code (`MapWorld.cs:1663-1680`) | `Glass_Window` loaded from `Resources/Surfaces`, with today's code as the fallback if it is missing |

### 4.2 Face material: a `FrontRooms/Glass` Shader Graph (visual chat)

Target: URP Lit, Transparent, Alpha blend, Preserve Specular on, ZWrite off, cast shadows off, cull Back on the closed 6 mm box. The values come from 02 §5.2.

| Input | Clean | With grime map | Why |
|---|---|---|---|
| Base colour | linear (.02, .025, .022) | + dust (.42, .40, .34) × dust mask | Glass has no diffuse colour; only dust scatters light. Today's (.75, .85, .88) is the veil in F3. |
| Alpha | 0.08 + 0.55 × Fresnel Effect (power 5) | + 0.25 × dust | About 90% transmission face-on, rising at grazing angles. Today it is a flat 0.28. |
| Metallic | 0 | 0 | Gives the correct F0 of 0.04 automatically. |
| Smoothness | .96 | lerp(.96, .62, smudge) | Smudges blur the reflection. Under room light, that is what makes glass read as glass. |
| Normal | flat plus a 0.02 long-wave roll | + smudge normal at 0.05 | A perfectly flat pane reads as CG. |
| `_Crack`, `_ImpactUV`, `_CrackSeed` | 0 | a 0–1 threshold on a radial crack mask | The crack stages in §3.5 |
| `_Palm` | 0 | a palm smudge at `_ImpactUV` | The push stage in §3.5 |

**Grime maps:** CC0 Fingerprints002, Smear007 and SurfaceImperfections001/007/013/015 are already on disk in `Tools/lookdev/cc0_src/ambientcg/` but not imported. Lay them out like this: dust thickest in the bottom 10–15 cm and in the stop corners, smears at 0.9–1.5 m, and a few prints near the edges.

**The maps are required, not polish.** In 05's experiments, physically clear values made the pane invisible ([08](images/08_window_L0_EXPERIMENT_clear_glass_probe.png), [09](images/09_window_L0_EXPERIMENT_clear_glass_probe_steep.png), [11](images/11_window_L0_EXPERIMENT_clear_glass_probe_1.5m.png)). The full combination (clear values + grime + zone cubemap) has **not been captured yet**. Capture it with 05's harness in a clone before signing it off.

**Prop glass:**
- Prop_Glass and Prop_BottleBlue should move onto the same graph.
- Their generator code asks for SrcAlpha (`RenderSetup.cs:414-415`), but the saved assets are One + premultiply + Preserve Specular (`Assets/Resources/Surfaces/Prop_Glass.mat:15,94,116`). URP's material validation rewrote them (02 §3).
- Make the code write what the assets already hold. 03 §6 item 7 assumed plain alpha; the saved asset shows that is not the case.

**Shards:** `Glass_Shard` is opaque, with a near-black base, smoothness .95 and green edge faces. Opaque shards avoid transparent sorting problems and overdraw (02 §8.4).

### 4.3 Reflection setup

- **Step 0 (visual, S, all tiers).**
  - Capture three 256 px HDR cubemaps in the editor with the fixtures on: a lit Level 0 room, a lit Office room and a dead-lamp room.
  - Add `FrontRoomsLook.SetZoneReflection(kind)`. It sets `RenderSettings.defaultReflectionMode = Custom` and `customReflectionTexture = cube`. The map chat calls it on zone change. 02 §6.1 found both APIs in the WebGL player module.
  - Raise `ReflectionIntensity` from 0.3 to about 0.8, tuned between 0.7 and 1.0 (`Look.cs:20`).
- **Step 1 (visual + map, M, all tiers).**
  - At chunk build, spawn one Custom `ReflectionProbe` per room (or per window cell). Its box is the room on the 3 m grid, box projection is on, and its cubemap is the zone cube.
  - Turn on `m_ReflectionProbeBoxProjection: 1` (`URP.asset:55`). Blending (`:54`) is optional.
  - Add `_REFLECTION_PROBE_BLENDING`, `_REFLECTION_PROBE_BOX_PROJECTION` and `_REFLECTION_PROBE_ATLAS` as `multi_compile_fragment` lines in `Surface.shader` (next to `:99-107`).
  - Each keyword adds shader variants. Unity warns that on the Web "don't include unwanted shader variants because it can lead to unnecessary memory usage" (WebGL2 page, read for this report), so strip them on the Web tier if needed.
  - The map is generated at runtime, so editor-baked per-room probes are not possible (02 §6.2).
- **Step 2 (desktop High/Cinematic only, optional).** When a glass hold starts, render one realtime probe once at that window ("Via Scripting", time-sliced), so the crack facets reflect the actual room.
- **Not planned.** URP 6.3 lists Screen Space Reflections, Planar Reflections and Screen Space Refractions all as "No" (feature comparison page, read for this report). A scripted planar mirror costs about one extra scene render per plane (02 §6.3), which is not viable for windows.

### 4.4 Breakage implementation plan

1. **Map (M):**
   - Replace `brokenWindows` with per-window state {stage 0–3, impact uv, seed, side}.
   - `Hold()` takes the hit point.
   - Stages persist when the player lets go.
   - Raise `GlassCracked` and a richer `GlassBroken`.
   - Swap in the fractured prefab instead of `Kill(window.pane)` (`MapWorld.cs:1571`).
   - On chunk rebuild, rebuild the teeth and the floor glass as static meshes instead of skipping the pane (`MapWorld.cs:900`).
2. **Visual (M):**
   - 3–4 pre-fractured radial variants per pane size, made from a radial point set in the Blender kit (for example with the Cell Fracture extension, 02 §7), with pieces tagged inner, middle and tooth. The pane is 6 mm, so the pieces are flat slabs with green edges.
   - Glint and dust particle prefabs (needs F9).
3. **Sound (S):**
   - Fire cracks from `GlassCracked(stage)` instead of progress thresholds. Today `lastStressProgress` resets to 0 when a new stress loop is created (`SoundDirector.cs:449`), so a resumed hold would replay crack 1.
   - Add the shard-landing tail and a glass footstep surface.
4. **Budget (02 §8.7, ESTIMATE):**
   - ≤ 24 rigidbodies for ≤ 2 s;
   - 150–250 mesh particles for ≤ 2 s;
   - 3–5 extra draws during the break;
   - 1–2 draws per broken window afterwards.
5. **Glass type (Red's call):**
   - Default: an annealed look with big shards and teeth, as an art-direction choice. A pane with a 0.35 m sill is "close to floor level" and would legally be tempered (02 §5.1).
   - Option: tempered granules with no teeth.
   - Wired glass for door lites is P2.

---

## 5. Rendering

### 5.1 What "AAA" can honestly mean here

**Web (WebGL2), the current web target:**
- Unity calls WebGPU "experimental and not recommended for production usage". Compute shaders are listed as a WebGPU feature, not a WebGL2 one (Web graphics page, read for this report).
- The Web "only supports Baked Global Illumination", with non-directional lightmaps only (WebGL2 page, read).
- URP 17.3 compiles 32 visible lights for WebGL2 (03 §1.8, URP `Input.hlsl:17-24`). The map can have about 80 lamps live.
- DBuffer decals do not support OpenGL/GLES (03 §8). That WebGL2 inherits this is UNVERIFIED.
- VFX Graph needs compute shaders (02 §6.7, 04 S23).
- **Realistic bar:** a polished, art-directed indie frame, not AAA. Red should hear this plainly.

**Desktop URP (Metal or DX12):**
- URP 6.3 has no SSR, planar reflections, screen-space refraction, SSGI, contact shadows or volumetric fog, and exposure is "Fixed" only (feature comparison page, read).
- With the §5.4 changes, two custom passes (contact shadows and ray-marched spot scattering) and TAA/STP, the indoor frame can reach a convincing "indie-AAA" level (03 §4).
- Ray-traced GI and reflections, SSR, HDRP volumetrics and subsurface skin stay out of reach without very large custom work.

**HDRP:** it has all of the above natively, but it drops WebGL and means rewriting `FrontRooms/Surface`, the post stack, the lookdev tools and every runtime-built material. Not this semester (03 §4).

**The two shots Red named do not depend on the platform.** They are timing, staging, debris and reflections, and all of these work on WebGL2.

### 5.2 Recommendation on platform and tier

- **Quality bar:** the macOS desktop build at the High tier.
- **Capture tier:** a Cinematic tier for presentation captures.
- **Sharing:** WebGL as a reduced Web tier, judged in a browser on an ordinary laptop, not in the editor.
- The editor's active build target is already StandaloneOSX (03 §1.1; 05 §A).
- **Before any of this, fix F7,** so that what Red judges is actually the URP game.

### 5.3 Tiers (condensed from 03 §5; frame targets are proposals, nothing is measured)

Each tier has one URP asset. The setup script must stop forcing one asset into every quality level (`RenderSetup.cs:47-54`), and camera AA must be chosen per tier (`PostStack.cs:72`).

| Setting | Web (WebGL2, 720p, DPR capped at 1) | High (desktop default) | Cinematic (captures) |
|---|---|---|---|
| AA | MSAA 2x or SMAA | TAA (MSAA off) | STP at 0.77 render scale |
| Lamp light radius | ~12 m (under the 32-light cap) | 16 m | 20 m |
| Shadowed lamps | nearest 4, 512 px | nearest 8–10, 1024 px | nearest 14–16, 1024–2048 px |
| Shadowed cone | ~115° + an unshadowed wide fill | same | same |
| Directional fill | off | off | off |
| Reflections | zone cubemaps | + box-projected room probes | + one realtime probe at a hero window |
| SSAO | downsampled, Low | full res, Medium | full res, High |
| Shafts | depth-faded beam meshes | + quarter-res scattering | half-res scattering with shadows |
| Decals | Screen Space | DBuffer | DBuffer |
| Shot profiles | Gaussian DOF, no motion blur | Bokeh DOF + camera motion blur | Bokeh + object motion blur |
| Target | 30–60 fps on an M1 / Iris Xe laptop | 60 fps on a mid desktop GPU | 30–60 fps |

### 5.4 Ranked rendering changes (03 §6, re-ranked and corrected)

| Rank | Change | Finding | Gain | Cost | Owner | Web |
|---|---|---|---|---|---|---|
| 1 | Rebuild on URP; delete `Build.cs:61-62`; fail the build when no pipeline is set | F7 | very high | < 1 h | build owner (map default) | yes |
| 2 | Zone cubemaps as the custom reflection; intensity ~0.8 | F4 | high | hours | visual | yes |
| 3 | Shadowed lamps at ~115° with a cookie; nearest-N shadows | F5 | high | hours | map + visual | yes (4 casters) |
| 4 | Remove the directional fill; per-zone ambient | F5 | medium-high, and it saves a shadow pass | hours | map + visual | yes |
| 5 | Textured troffer lens in the map; bloom dirt; subtle lens flare | F10 | medium-high (in almost every frame) | hours | map + visual | yes |
| 6 | Glass Shader Graph and the 6 mm pane (§4) | F3 | high on the shot Red named | 1–3 days | visual + map | yes |
| 7 | Shot post profiles and API (§3) | F6 | high for the shots | hours + camera work | visual | yes |
| 8 | Real tiers; TAA on desktop | F12 | medium (no shimmer) | 1 day | visual | Web keeps MSAA |
| 9 | Box-projected room probes and shader keywords | F4 | medium-high | 1–2 days | visual + map | yes |
| 10 | Decals (water damage, scuffs, footprints, notices) | — | medium-high (breaks repetition) | 2–3 days | visual (+ map hooks) | Screen Space only |
| 11 | Visible light: depth-faded beams and dust everywhere; ray-marched scattering on desktop | — | medium / high | hours / 3–5 days | visual | beams yes, scattering no |

Correction carried from the sibling reports: 03 rank 7 said `Prop_Glass` uses plain alpha that dims its reflections. The saved asset is premultiplied with Preserve Specular (§4.2), so that item is a code-consistency fix, not a look fix.

---

## 6. Phased remediation plan

### Phase 1 — this week (quick wins plus the camera skeleton)

| # | Item | Owner | Depends on | Effort |
|---|---|---|---|---|
| 1.1 | Delete `Build.cs:61-62`; fail the build when no pipeline is set; rebuild the Mac player; make the autopilot capture copy the URP camera data (`Game.cs:1899, 1924, 1941`) | build owner (Red decides; map default) | — | S |
| 1.2 | Zone cubemaps as the custom reflection; intensity ~0.8 (§4.3 step 0) | visual | — | S |
| 1.3 | Map pane: 6 mm, stop and sill trim, shadows off, edge material; interim URP Lit values until the graph lands: near-black base, a smudge/dust texture in the base map whose alpha gives 0.06–0.25 coverage, smoothness .96 (05 showed that clear values without surface detail make the pane invisible) | map (geometry) + visual (material) | 1.2 for the look | S |
| 1.4 | Lamps: ~115° shadowed cones with a cookie, nearest-N shadows; remove the directional fill | map + visual | — | S |
| 1.5 | Textured lens in the map | map | — | S |
| 1.6 | Camera rig skeleton (layers, takeover, cancel) and the post shot/pulse API; route the map walker through it | map + visual | — | M |
| 1.7 | Enable `com.unity.modules.particlesystem` | visual | Red's yes | S |
| 1.8 | Small correctness fixes: no Handle/Unlatch on broken doors; hide the prompt on a door being broken; check the door's zone, not the player's; drop the "OPENS THIS ZONE'S DOORS" text | sound + map | — | S |
| 1.9 | A 10 s capture of the key-unlock shot (B, with and without a posed hand) made in a clone with 05's harness, for Red | map + visual | 1.6 | S |

### Phase 2 — next 1–2 weeks (the two shots Red named, and real glass)

| # | Item | Owner | Depends on | Effort |
|---|---|---|---|---|
| 2.1 | `FrontRooms/Glass` Shader Graph; Glass_Window/Edge/Shard; move the prop glass onto it; fix the blend code in `RenderSetup.cs:414-415` | visual | 1.2 | M |
| 2.2 | Window break state, `GlassCracked`, richer `GlassBroken`, fractured swap, static rebuild (§4.4) | map | 1.6, 2.1 | M |
| 2.3 | Fractured pane variants; glint, dust and chip particles | visual | 1.7 | M |
| 2.4 | Crack sounds from stages; shard-landing tail; glass footstep surface | sound | 2.2 | S |
| 2.5 | Door leaf prefab: lever, lock cylinder, deadbolt, zone tag plate, kick plate; damage variants for §3.7 | visual | — | M |
| 2.6 | Door state machine (Locked → Unlocking → Ajar → Open); `DoorUnlocked`, `DoorRattled`, `KeyPickupStarted`; `Use()` holds the door during the shot; the §3.1–3.4 shots; then `doorsNeedKeys: 1` in `Level0.asset:47` | map | 1.6, 2.5 | M |
| 2.7 | Lock and pickup events (KeyInsert, KeyTurn, BoltRetract, Pocket, Snapshot/Closeup) | sound | 2.6 timings | S |
| 2.8 | Climb update (§3.6) | map + sound | 2.2 | S |
| 2.9 | Box-projected room probes and `Surface.shader` probe keywords (§4.3 step 1) | visual + map | 1.2 | M |
| 2.10 | Web / High / Cinematic tiers; TAA on desktop | visual | — | M |

### Phase 3 — after that

| # | Item | Owner | Depends on | Effort |
|---|---|---|---|---|
| 3.1 | Caught sequence (§3.8) | map + sound + visual | 1.6; Relay model or silhouette framing | M |
| 3.2 | Relay door-break damage and reveal (§3.7) | map + visual + sound | 2.5 | M |
| 3.3 | Relay model (rig work is already in progress) | visual | — | L |
| 3.4 | Chase post pulse instead of the metre readout (F15) | map + visual | 1.6 | S |
| 3.5 | Decals | visual (+ map hooks) | — | M |
| 3.6 | Visible light: beams and dust; desktop scattering | visual | 2.10 | M / L |
| 3.7 | Screen-space contact shadows (desktop) | visual | 1.4 | M |
| 3.8 | Hands (language A), only if Red wants them after seeing B; needs the animation module | visual + map | 1.9 decision | L |
| 3.9 | Per-module baked lightmaps (the biggest step toward AAA indoor light; a project, not a tweak) | visual + map | — | L |
| 3.10 | Measure the Web tier on a non-Apple laptop at DPR 1 and 2; GPU-profile the High tier | visual | 2.10 | S |

### 6.4 Contracts between the chats

**Events the map chat raises** (new or changed; existing ones are at `MapWorld.cs:59-71`, `Game.cs:39-43`, `Hunter.cs:126-128`):

| Event | Signature | Who listens |
|---|---|---|
| `KeyPickupStarted` NEW | `(GridCoord zone, Vector3 pos)` | sound |
| `KeyTaken` | unchanged, but fires at the arrival beat (§3.1) | sound, HUD |
| `DoorRattled` NEW (or a reworked `DoorLocked`) | `(Vector3 lockPoint)` | sound, Relay noise |
| `DoorUnlocked` NEW (named in `LEVEL_MODULE_SPEC.md:48`) | `(Vector3 lockPoint, GridCoord zone)` | sound |
| `ShotStarted` / `ShotEnded` NEW | `(ShotKind kind, Vector3 focus)` | sound (snapshots), visual (post) |
| `GlassHold` | add the hit point: `(Vector3 pos, float progress, Vector3 hit)` | sound, visual |
| `GlassCracked` NEW | `(Vector3 pos, int stage, Vector2 uv)` | sound, visual |
| `GlassBroken` | `(GlassBreak info)`: pos, hit, normal, seed, side | sound, visual |
| `DoorBlow` (hunter) | add `(Door door, int blowIndex, float damage01)` | visual, sound |
| `DoorBroken` | add the direction it was broken from | visual |
| `Caught` (hunter) | `(Vector3 relayHead)` | map, sound |
| `CaughtImpact` NEW | `()` at +0.25 s | sound |

**Camera rig (map chat owns it). Sketch, not final:**

```csharp
// One instance on the player camera. UpdateMapPlay writes look through it,
// not straight to the transforms (Game.cs:830-831). FrontRoomsMapWalker uses it too
// (FrontRoomsMapWalker.cs:119-138).
ShotHandle BeginShot(ShotSpec spec);            // blend to an anchor pose
void EndShot(ShotHandle h);                     // blend back
void CancelShot(ShotHandle h, float blendOut = .2f);
void AddTrauma(float degrees, float decaySeconds);   // rotation only; scaled by the motion setting
void PushFov(float delta, float seconds);
void AddOffset(Vector3 local, float seconds);        // lean, jab, dip
bool InShot { get; }                            // movement and look are suspended while true
struct ShotSpec { Transform anchor; Vector3 localOffset; float blendIn, blendOut, fov;
                  bool lockMove, lockLook; float lookCone; CancelPolicy cancel; ShotKind kind; }
```

**The visual chat provides:**
- `FrontRoomsPostStack.PushShot(ShotKind, blendIn, blendOut)` and `Pulse(PulseKind, amount, seconds)`, with one profile per shot (Gaussian DOF on Web, Bokeh on desktop).
- `FrontRoomsLook.SetZoneReflection(ZoneKind)`.
- Assets with fixed names and transforms:
  - the `Glass_Window`, `Glass_Edge` and `Glass_Shard` materials;
  - the door leaf prefab, with `Lever` and `Deadbolt` children, its lock point at the spec's `DoorHandle*` position (`Units.cs:58`), and damage variants;
  - the key prefab with its zone tag;
  - fractured pane prefabs with tagged pieces;
  - glint, dust and splinter particle prefabs.

**The sound chat provides:**
- the events marked NEW in §3;
- cracks fired from stages;
- Handle and Unlatch suppressed for broken doors;
- the caught silence moved to `CaughtImpact`.

**Shared:**
- One timing table (`FrontRoomsShotTimings`), so beats are not duplicated as literals.
- `LEVEL_MODULE_SPEC.md` rows 48–49 (door, window) need updating to describe the glazing stop, the sill trim, the 6 mm pane and the door hardware. The map chat owns that spec.
- Each chat edits only its own files and meets the others through these APIs.

---

## 7. Open questions for Red

1. **Platform.** Is the Mac desktop build the quality bar, with WebGL as a reduced tier (recommended, §5.2)? Or must the web build carry the full look?
2. **Camera language.** B (camera push-ins, objects act, no hands) as the system? After the 10-second capture (1.9): no hand, or one posed hand on the key shot? Full hands (A) later, or never?
3. **Keys.** Should the shipped level lock doors (`doorsNeedKeys` is 0 today)? Does a key open every door in its zone or only one? Is it ever used up?
4. **Doors.** Is it OK to change doors to "ajar, then push", with a slow creak versus a fast slam setting the Relay noise (§3.2, §3.3)? This changes play, not just the picture.
5. **Glass type.** Annealed (big shards, teeth; recommended) or tempered (granules)? Wired glass on door lites later?
6. **Breaking input.** Hold E (today, recommended) with a tap option in settings, or three strikes by default?
7. **Caught.** Show the Relay (it needs the new model), or keep it a silhouette? Should the card stay bone white or go to black after the fade?
8. **Modules.** OK to enable the particle module now (1.7)? The animation module only if hands are chosen.
9. **Camera motion.** On by default with a toggle, or off by default?
10. **Build script.** Who owns `Assets/Editor/FrontRooms3DBuild.cs`? It has no owner today.
11. **Notes and reading.** `UI_SYSTEM.md:34` lists "hold E reads" and "Tab opens notes". Still planned? If so, that is another shot to design.

---

## 8. Sources and method

- **Code:** every `file:line` above was re-read in the real project at about 21:05–21:10 on 2026-10-02 (read only). Lines in `MapWorld.cs` and `Game.cs` move while the map chat works; the named symbol is the anchor.
- **Frames:** all images are 05's captures from the real game camera in a private clone (1920×1080, 4x MSAA, the game's own post stack). Frames 70–80 show the Relay rig as it was at 20:34; the rig has since changed (05 §1).
- **Web pages read for this report (2026-10-02):**
  - Unity 6.3, render pipeline feature comparison (URP: SSR, planar reflections, screen-space refraction, SSGI, contact shadows and volumetric fog all "No"; exposure "Fixed"): https://docs.unity3d.com/6000.3/Documentation/Manual/render-pipelines-feature-comparison.html
  - Unity 6.3, Web graphics APIs (WebGPU "experimental and not recommended for production usage"; compute shaders listed under WebGPU): https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-graphics.html
  - Unity 6.3, WebGL2 (Web "only supports Baked Global Illumination"; the warning about unneeded shader variants): https://docs.unity3d.com/6000.3/Documentation/Manual/WebGL2.html
- **Other web claims** are carried from the sibling reports, which list the URLs their authors read: 02 §10, 03 §8 and 04 §2. They were not re-read for this synthesis. The sibling reports' own UNVERIFIED items still stand, in particular:
  - whether the map pane's shadow is visible (05 §H);
  - the pipeline a Mac player gets after today's `BuildMac`;
  - WebGL DPR, TAA and DBuffer behaviour;
  - all frame-cost estimates;
  - the RE Village key framing and the TLOU2 shard crunch (04 §5);
  - the WebGL size of the particle and animation modules.
