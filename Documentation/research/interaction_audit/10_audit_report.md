# 10 — Interaction, glass and render-quality audit (for Red)

Date: 2026-10-02. Status: COMPLETE (synthesis of 01–05; about 21:15), revised at about 21:50 after three
reviews (code, feasibility, completeness). Every correction was re-checked against the code first; see §9.
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
`Game.cs` 21:02), and again for the review at about 21:40 (no cited file had changed). The map chat is still editing those files, so the symbol named next to each line
is the stable anchor. Line numbers in the sibling reports are a few lines older in places.

Tags: **UNVERIFIED** = not confirmed in code, in engine or on a page that was read.
**ESTIMATE** = engineering judgement, not a measurement.

---

## 1. Verdict

Red is right on all three counts, and each has a specific cause.

1. **No interaction has a shot.** Every interaction is "press E, the world changes in one frame, a HUD line explains it". Keys do nothing in the shipped level (`doorsNeedKeys: 0`), and a keyed door opens with the same 0.55 s swing as any other door. Glass is deleted, not broken. There is also nothing to stage a shot with: the camera only moves during the window climb, and there are no hands.
2. **The glass is a lit, pale veil on a 30 mm box, and there is nothing in the world for it to reflect.** There is no reflection probe, no skybox, and reflection intensity is 0.3 (all three come from the scene file; the code in `FrontRoomsLook` that sets them never runs in the game, F4). That same gap makes every metal and gloss surface in the game look like plastic.
3. **URP has the features we need. Several settings are wrong for this content (probes, AA, a single tier, the shadow setup), but the bigger cause is what we feed it.** The game already runs Forward+, HDR, 4x MSAA, SSAO and a full film post stack at about 14–18 ms per 1080p render in the editor (median of three runs; one render plus a forced GPU readback on an M3 Max; not GPU frame time and not a player, 05 §G). It reads as "low level" because of primitive cubes for keys, doors and panes, a capsule Relay, lamp shadows erased by a 162° cone, a fill light leaking through every ceiling, unshadowed lamps lighting through walls, and no reflections. Also, every build on disk was made before URP was added, the last player Red ran was one of them (`../Builds/FrontRooms3D_Mac`, Player.log, Oct 1 21:14), and that player's saved display setting is SDR (F7). Don't use them to judge the look.
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
| F1 | S1 | Using a key has no shot, and keys do nothing in the shipped level | map + visual + sound | L |
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
| F17 | S2 | No captions or visual sound cues, while the plan removes HUD threat text | map + sound | S |

### F1 (S1) Using a key has no shot, and keys do nothing in the shipped level

![Key door at 0.25 s: the same swing as any door](images/60_door_key_open_t0250ms.png)

- **Player sees:** with a key held, E on a door gives the same 0.55 s swing as a door that never needed one, frame for frame. Compare frames [59](images/59_door_key_open_t0000ms.png)–[62](images/62_door_key_open_t0750ms.png) with [40](images/40_door_normal_t0000ms.png)–[43](images/43_door_normal_t0750ms.png). The key object never appears again after pickup; only a HUD glyph shows (`Game.cs:1394-1401, 1548`; frames 56, 58). The door has no lock, lever or handle to put a key into. In the shipped level no door is ever locked, so the pickup text "KEY / OPENS THIS ZONE'S DOORS" is a promise the game does not keep. When locks are forced on, a locked press changes nothing on screen ([48](images/48_door_locked_before_hud.png), [50](images/50_door_locked_after_use_hud.png), [51](images/51_door_locked_0.5s.png)).
- **Why it reads cheap:** the most important beat in a key-and-door game is told only by a prompt string. There is no object, no camera, and no change of state you can see.
- **Evidence:**
  - `Use()` checks for the key and then runs the same `SwingAway` + `SetDoor` as any door (`MapWorld.cs:1523-1533`). There is no key-use or unlock event; the full event list is `MapWorld.cs:59-71`.
  - Locks are off in the shipped level: `doorsNeedKeys: 0` (`Level0.asset:47`), and the default is also false (`FrontRoomsLevelProfile.cs:31`).
  - The door leaf is a `CreatePrimitive(Cube)` with no hardware (`MapWorld.cs:879-883`). The title doors have handles and kick plates (`FrontRoomsRoomStream.cs:1254-1271`).
  - The key check uses the zone the player stands in (`HasKeyHere`, `MapWorld.cs:1583`). Every map door joins two zones, because doors only stand where cell heights differ (`FrontRoomsMap.cs:350-355`; `Units.cs:54`), so a door can need a different key depending on which side the player is on. The UI text matches this rule (`MapWorld.cs:1513`; `Game.cs:796`). Which side's key opens a door is a design decision (§7 Q3), not a bug.
  - The locked feedback is a prompt (`MapWorld.cs:1513`) plus an FMOD one-shot (`SoundDirector.cs:472`).
- **Fix:**
  - Add a door state machine: Locked → Unlocking (shot) → Ajar → Open. Use the `DoorUnlocked(Door, GridCoord, Vector3)` already planned in `Documentation/AUDIO_CONTRACT.md:28`, plus `DoorRattled`.
  - `Use()` must hold the door while the shot plays.
  - Ajar needs an explicit Relay rule and a push mechanism (§3.2 "After"); this is AI work, not only picture.
  - Keep lock state across chunk rebuilds and shifts (§4.4 item 1).
  - Visual chat ships a door leaf with a lever, a lock cylinder and a `LockAnchor` transform; the map exposes it as `FrontRoomsMapWorld.LockPoint` (named at `Units.cs:57`, not yet in code).
  - Apply Red's answer to §7 Q3 (which side's key) in `HasKeyHere` and in the `DoorUnlocked` zone argument.
  - Turn `doorsNeedKeys` on only once the shot exists.
  - Shot designs: §3.2 and §3.4.
- **Owner · effort · frame cost · WebGL:** map + visual + sound · L (the Ajar AI rule and state persistence push the map share from M to L) · N · picture yes; sound UNVERIFIED on WebGL (F9).

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
- **Owner · effort · frame cost · WebGL:** visual (shader, fracture assets) + map (break state, events) + sound (stage-driven cracks, shard tail) · M · L for about 2 s during a break, N after (≤ 24 rigidbody shards, each its own renderer with a unique mesh, plus particles: about 25–35 extra draws during the break, with shadow casting off on moving shards and particles; ESTIMATE, UNVERIFIED until profiled) · yes, with fewer particles.

### F3 (S1) The window pane is a lit pale veil on a 30 mm box

![Level 0 window, intact, 1.5 m: a grey-teal haze](images/02_window_L0_intact_1.5m.png)

- **Player sees:** a cool grey-teal haze over the far room, lighter than the same view with the pane gone (compare [02](images/02_window_L0_intact_1.5m.png) with [16](images/16_window_L0_break_next_frame.png)). At grazing angles the panes turn flat pale cyan ([04](images/04_window_L0_intact_oblique.png), [23](images/23_window_Office_intact_oblique.png), [25](images/25_window_Office_intact_steep.png)). There are no smudges, no edge, and nothing holding the glass in the frame.
- **Why it reads cheap:** clear glass has almost no diffuse colour. Here 28% of a pale, lit colour is painted over the view, so the pane looks like plastic film that brightens and darkens with the lamps.
- **Evidence:**
  - The material is built in code as URP Lit Transparent, base (.75, .85, .88, **.28**), smoothness .9 (`MapWorld.cs:1660`, `TransparentGlass` at `:1663-1680`).
  - The pane is a primitive cube (`MapWorld.cs:901-905`), 30 mm thick (`GlassThickness = .03f`, `Units.cs:61`).
  - The frame is two jambs and a head, with no glazing stop or sill trim (`MapWorld.cs:858-867`).
  - The pane's material keeps the ShadowCaster pass (`MapWorld.cs:1663-1680`; `images/runtime_dump.txt:239`) and its renderer keeps `shadowCastingMode` On (`MapWorld.cs:901-906`; `runtime_dump.txt:274`), unlike `Prop_Glass` (`Prop_Glass.mat:27`). Whether that throws a visible solid shadow is UNVERIFIED (05 §H).
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
  - The scene has no skybox (`Assets/Scenes/FrontRooms3D.unity:29`) and the camera clears to a solid colour (scene camera `m_ClearFlags: 2`, `FrontRooms3D.unity:296`). `MapWorld.cs:492` clears the skybox only in the standalone map test scene and in edit-mode captures (`MapWorld.cs:241-242, 415`); the game embeds the map with `standalone = false` (`MapWorld.cs:257`).
  - Reflection intensity is 0.3, and the game takes it, and the ambient colours, from the scene file (`FrontRooms3D.unity:23-27, 38`; `images/runtime_dump.txt:211`). `FrontRoomsLook.ApplyAmbient()` (`Look.cs:22-38`) never runs on the game's runtime path. Its callers are the editor's Create Scene (`Game.cs:266`, called from `Build.cs:25`), the standalone map scene and edit-mode captures (`MapWorld.cs:491`), and editor tools (`RenderSetup.cs:543`, `FrontRoomsKitLookdev.cs:59`, `FrontRoomsLookdevCapture.cs:39`). The game's `Awake` only calls `DynamicGI.UpdateEnvironment()` (`Game.cs:301`). The runtime ambient (.20/.19/.15, .26/.24/.17, .40/.36/.24) is not Look's (`Look.cs:15-17`). So editing `Look.cs:20` changes nothing in the game, and the comment at `RenderSetup.cs:541-542` ("applied at runtime by FrontRoomsLook") is wrong for the game.
  - At runtime there are 0 reflection probes, and the default reflection is Unity's "Default-Skybox-Cubemap" at 128 px (05 §A).
  - Box projection and probe blending are both off (`URP.asset:54-55`).
  - `Surface.shader` (used by 83 of the 86 materials in `Assets/Resources/Surfaces`) declares no reflection-probe keywords (`Surface.shader:96-110`), so it cannot box-project probes even if they are turned on.
- **Fix:**
  - Make the look code actually run in the game: the map chat calls `FrontRoomsLook.ApplyAmbient()` and the new `SetZoneReflection` at run start (`Game.cs` `Awake`, near `:299-301`) and on zone change, or the scene's Lighting settings are changed. A scene edit needs Red, because he has the scene open.
  - Step 0: capture one HDR cubemap per zone type and set it as the custom default reflection, swapped per zone. Prove in a clone first that a runtime swap reaches URP (UNVERIFIED, §4.3). Keep intensity ≤ 0.5 until step 1, and crossfade on zone change.
  - Step 1: per-room box-projected probes. They need probe blending on (§4.3).
  - Details: §4.3.
- **Owner · effort · frame cost · WebGL:** visual (capture, Look API, shader) + map (runtime call, probe spawn) · S (step 0), M (step 1) · N (step 0); L–M per pixel plus atlas memory for step 1 (UNVERIFIED) · step 0 yes; step 1 desktop only. Avoid realtime probes on the web.

### F5 (S1) Light has no structure: lamp shadows erased, fill leaks through ceilings

![Level 0 corridor: even wash, contact shadows only from SSAO](images/01_rep_L0.png)

- **Player sees:** an even wash with no readable pools. Wall bases, furniture and the Relay's feet sit on the floor with no contact shadow ([01](images/01_rep_L0.png), [34](images/34_rep_Office.png), [37](images/37_rep_Dark.png)).
- **Why it reads cheap:** AAA interiors read through contrast: a pool under each lamp, falloff up the walls, dark gaps and grounded objects.
- **Evidence:**
  - Map lamps are 162° spots (`MapWorld.cs:1058`).
  - About one lamp in three may cast a shadow (`MapWorld.cs:1069`), and only within 9 m (`MapWorld.cs:1122`; `Level0.asset:49`). At runtime, 9 lights were shadowed (05 §A).
  - URP 17.3 scales spot shadow bias with tan(angle/2) × range. For 162°/10 m that is roughly 9–13 cm of bias, which erases contact shadows (03 §1.8, from `ShadowUtils.cs:390, 414-447` in the package).
  - The runtime fill is the scene object "Soft ambient direction" (`FrontRooms3D.unity:2200`; intensity 0.16, soft shadows at strength 0.18; `runtime_dump.txt:215`). At 0.18 shadow strength it lights through every ceiling. `Game.cs:267-275` creates the same light (at 0.22) only for the editor's Create Scene.
  - Unshadowed lamps light the next rooms through walls; the code says so itself (`MapWorld.cs:1083-1085`). Two lamps in three never cast (`:1069`), every lamp beyond 9 m is unshadowed (`:1122`), yet lamps stay lit to 16 m (`:1118-1120`). Light layers are off (`URP.asset:76`). Shadows also switch on and off at the 9 m line with no fade (`:1122`), which pops.
  - Indirect light is one flat three-colour ambient for the whole world, from the scene file (`FrontRooms3D.unity:23-27`; F4). The surface shader only samples SH (`Surface.shader:240`).
- **Fix:**
  - Give every lamp the same cone of about 115° with a troffer cookie, and no extra fill lights. Range is the other half of the bias (`ShadowUtils.cs:390`: tan(angle/2) × range): try about 6 m (8 m in Tall) instead of 10/12 m (`MapWorld.cs:1061`) and retune intensity. Both cut the bias and shrink light volumes (ESTIMATE; 03 §1.8 gives about 3 cm for the cone change alone).
  - Shadow the nearest N lamps instead of the 1-in-3 hash, and fade `shadowStrength` over about 0.5 s when a lamp joins or leaves the set, instead of toggling at `shadowRadius`.
  - Stop the leak with per-room rendering layers (`m_SupportsLightLayers: 1`, `URP.asset:76`) or shorter unshadowed ranges.
  - Remove the directional fill in two steps: delete it from the scene (a scene edit Red must coordinate, since he has the scene open), and delete it from `ApplySceneLighting` (`Game.cs:267-275`) so Create Scene does not bring it back.
  - Ambient per zone only works once the look code runs in the game (F4).
  - Use the same lamp shape in the title stream (`FrontRoomsRoomStream.cs:1101,1109`).
- **Owner · effort · frame cost · WebGL:** map (MapWorld lamps, fill light in scene and code) + visual (stream lamps, cookie, Look API) · S · M for the shadows, partly paid back by removing the main-light shadow pass · yes, with 4 shadowed lamps at 512 px.

### F6 (S1) No camera system

- **Player sees:** a perfectly still camera in every moment: no lean, push-in, shake, FOV change, bob or reaction. The only motion is the climb duck.
- **Why it reads cheap:** every shot Red asked for is camera work, and there is nothing to do it with.
- **Evidence:**
  - Yaw and pitch are written directly every frame (`Game.cs:830-831`).
  - The camera's local position is only written at start and by the climb (`Game.cs:565, 928, 932`).
  - FOV 76 is serialized in the scene (`FrontRooms3D.unity:320`). `Game.cs:225` sets it only for Create Scene or when no camera is found (`Game.cs:303-304`).
  - Nothing is parented to the camera, and it has no camera-motion or viewmodel component. Apart from the Camera, the AudioListener (`FrontRooms3D.unity:279`), URP camera data (`PostStack.cs:69`) and FMOD's StudioListener (added at runtime, `SoundDirector.cs:173-174`), the only component added is the hum AudioSource (`Game.cs:1022`).
  - Post is static: one global volume plus position-blended Office zone volumes (`PostStack.cs:15-62`; spawned per chunk at `MapWorld.cs:1386-1420`; 44 local volumes at runtime, 05 §A). No script changes post weights or values in response to game events, and there is no pulse or shot API.
  - Gameplay reads the camera transform directly: the aim ray (`Game.cs:942`) and the Relay's view of the player's eye (`Game.cs:879`; sight at `FrontRoomsMapHunter.cs:175`). Any camera offset would move both.
  - The map test walker duplicates the whole E / hold-E loop (`FrontRoomsMapWalker.cs:119-138`).
- **Fix:**
  - Build one camera rig in the map chat. It needs:
    - base look;
    - additive offset, FOV and shake layers;
    - a takeover that blends to an anchor pose;
    - a lock on movement and look, with a look cone;
    - a cancel policy;
    - a `BaseEye` (body + 1.62 m, base yaw and pitch, no offsets or shake) that the aim ray and `relay.Tick` use instead of the rendered camera pose;
    - a world clamp (a short spherecast) on every camera offset.
  - Add a post "shot" and "pulse" API in the visual chat.
  - Both the game and the map walker use the same rig.
  - Contract: §6.4.
- **Owner · effort · frame cost · WebGL:** map (rig) + visual (post API) · M · N · yes.

### F7 (S1) The builds on disk are not the URP game, and the Mac build menu removes URP

- **Player sees:** anyone running `Builds/Mac` or `Builds/WebGL` sees a pre-URP game: no surface shader, no SSAO and no post.
- **Evidence:**
  - The Mac build was written Oct 1 19:08–19:32 and the WebGL build at 17:49. The URP asset was created at 19:54–20:04 (03 §1.1). The Mac player has no URP runtime DLL (02 §2, 03 §1.1).
  - `BuildMac()` sets `GraphicsSettings.defaultRenderPipeline = null` and `QualitySettings.renderPipeline = null` before building (`Build.cs:61-62`). The second line clears only the active quality level. The Standalone default level (5) still points at URP (`ProjectSettings/QualitySettings.asset:338`). So which pipeline a new Mac player runs is UNVERIFIED (02 and 03 disagree), but it is a trap either way. It also leaves the open editor's active level with no pipeline until rendering setup runs again.
  - The last player run was `../Builds/FrontRooms3D_Mac/Frontrooms3D.app` (`~/Library/Logs/Red Wang/FrontRooms3D/Player.log`, Oct 1 21:14). `../Builds/` (outside `Frontrooms3D/`) holds 14 build folders, 12 Mac and 2 WebGL, none with a URP runtime (Mac assemblies dated Oct 1 17:46–19:32).
  - That player's saved display preference is SDR: `FrontRooms.Display.HDR = 0` in `~/Library/Preferences/com.redwang.frontrooms3d.plist` (written Oct 1 21:12; key read at `Game.cs:86, 310`, applied at `Game.cs:1235-1247`). PlayerPrefs survive a rebuild with the same bundle id (`Build.cs:64`), so a rebuilt player would also start in SDR. How much SDR shaped Red's impression is UNVERIFIED.
  - The playtest autopilot's look-at, look-around and Relay frames are rendered through `Camera.CopyFrom` (`Game.cs:1899, 1924, 1941`), which leaves URP post off. Those frames have no tonemapping or grade (05 frame [36](images/36_rep_Office_b_AUTOPILOT_STYLE_camera.png) against [35](images/35_rep_Office_b.png)).
- **Fix:**
  - Delete the two lines.
  - Fail the build if no render pipeline is set.
  - Rebuild the Mac player, then turn HDR back on (Esc → O → H) or delete that preference key before judging.
  - WebGL is equally pre-URP. `BuildWebGL` forces the default template (`Build.cs:116`), so the DPR cap (Unity: set `devicePixelRatio=1` in the template's page, https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-canvas-size.html) needs a project template; it forces quality level 3 (`Build.cs:146`), so a Web tier asset would never be picked; and it switches the active target to WebGL (`Build.cs:86`), which reimports the editor Red has open. Rebuild WebGL only from a clone in batch mode.
  - Judge the look only from a fresh URP player or the editor Game view.
  - Fix the autopilot capture to copy the URP camera data.
- **Owner · effort · frame cost · WebGL:** build-script owner. It is unassigned; Red decides, and the map chat is the default. · S · N · yes.

### F8 (S1) Caught is a same-frame hard cut to a white card; the Relay is never framed

- **Player sees:** at 0.7 m the game cuts, in the same frame, to a near-opaque bone-white card reading "CAUGHT". There is no turn to the Relay, no grab and no fall. In the player-view frame at the moment of the catch ([80](images/80_relay_broken_%2B1000ms.png)), the capsule torso fills the screen with visible polygon edges.
- **Why it reads cheap:** the moment the whole game builds toward has no picture.
- **Evidence:**
  - `Caught` carries no position (`Hunter.cs:238-242`) and is wired to `End()` (`Game.cs:591, 1568-1574`).
  - The overlay is (.93, .92, .88, .98) (`Game.cs:1452`), with the card text at `Game.cs:1479`.
  - The sound side already hard-cuts to silence and plays `Tinnitus` (`SoundDirector.cs:500-514`).
  - `caught` stops the hunter's tick (`FrontRoomsMapHunter.cs:141`), and `End()` switches straight to `Phase.Caught` (`Game.cs:1568-1571`), where R restarts at once (`Game.cs:1496`). Nothing can run between the catch and the card today.
- **Fix:** a 2 s caught sequence before the card (§3.8), in a new `Phase.Dying` that keeps the rig and camera running before `End()`. It needs the Relay's position with the event, a lunge pose, and a better Relay model, or at least a silhouette framing until the model lands.
- **Owner · effort · frame cost · WebGL:** map (sequence, event) + visual (Relay model and pose, post hit) + sound (impact timing) · M · N · yes.

### F9 (S1 blocker) Particle and animation modules are not installed

- **Evidence:** `Packages/manifest.json:1-13` and `Packages/packages-lock.json` contain no `com.unity.modules.particlesystem`, `com.unity.modules.animation`, `com.unity.timeline`, `com.unity.cinemachine`, `com.unity.visualeffectgraph` or `com.unity.modules.unitywebrequest`. Physics is installed (`manifest.json:6`).
- **FMOD has never been in a build.** `Assets/Plugins/FMOD` was created Oct 2 18:44, after every build on disk. On WebGL, FMOD loads banks with `UnityWebRequest` (`Assets/Plugins/FMOD/src/RuntimeManager.cs:943-965`), whose module is not installed, so a WebGL build may not compile (UNVERIFIED). If FMOD then fails at runtime, the legacy fallback has no sound for any new shot event.
- **Impact:** shard and glint particles, dust and splinters cannot use Shuriken until the particle module is enabled. Authored hand or key clips cannot play without the animation module. Rigidbody shards and code-driven tweens work today.
- **Fix:**
  - Enable `com.unity.modules.particlesystem`, and `com.unity.modules.unitywebrequest` for FMOD on WebGL. Each is a one-line manifest change.
  - Switch a clone to WebGL, compile, and run one build with FMOD banks before promising any shot's sound on the web.
  - The recommended camera language (§3) needs no Animator, Timeline or Cinemachine.
  - VFX Graph is out on WebGL2 because it needs compute shaders (02 §6.7, 04 S23).
- **Owner · effort · frame cost · WebGL:** visual, with Red's approval · S · depends on use · yes. The extra WebGL download size is UNVERIFIED.

### F10 (S2) Primitive content in every hero position

![Key from 2 m: a pale yellow brick](images/52_key_2m.png)

- **Player sees:** the key is a 0.32 × 0.12 × 0.12 m emissive yellow box ([52](images/52_key_2m.png)). Doors are plain veneer slabs ([60](images/60_door_key_open_t0250ms.png)). The Relay is capsules and boxes with a floating torso ([70](images/70_relay_break_witness_t1000ms.png), [78](images/78_relay_broken_%2B0250ms.png), older rig), and its facing snaps instantly. In Level 0 zones the map troffers are flat bright slabs ([01](images/01_rep_L0.png)).
- **Evidence:**
  - Key: `MapWorld.cs:731-736`, material `MapWorld.cs:1659`.
  - Door leaf: `MapWorld.cs:879-883`.
  - Map lens: Level 0-zone lenses use a plain emissive Lit material on a thin primitive cube, 0.6 × 0.025 × 1.2 m (`MapWorld.cs:1633, 1639, 1038-1045`). Office zones already use the textured `Troffer_Lens` (`MapWorld.cs:1642-1648`; `FrontRoomsSurfaces.cs:47-48`; emission set at `Troffer_Lens.mat:68`).
  - Relay: driven in code, with no Animator (`FrontRoomsRelayRig.cs:137`). Its facing is written directly every frame (`Game.cs:981-982`).
- **Fix:** in order:
  1. Set the Level 0 lens to `FrontRoomsSurfaces.TrofferLens` (`MapWorld.cs:1633/1639`), a one-line change for the map chat. Slerp the Relay's facing at a capped turn rate (about 360°/s, ESTIMATE; map).
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
  - Blows are sound-only events (`Hunter.cs:862-879`, `DoorBlow` at `:868`). The rig's blow impulse, `FrontRoomsRelayRig.DoorBlow(int, int)` (`FrontRoomsRelayRig.cs:38-43`, a chest snap at `:172-177`), exists but nothing calls it; the rig only holds a static BreakDoor pose (`Game.cs:986-990`).
  - `BreakDoor` just swings the door (`MapWorld.cs:1004-1013`), using the 0.18 s broken speed (`MapWorld.cs:1594`).
  - The Handle and Unlatch one-shots fire whenever the leaf leaves the frame (`DoorSound.cs:89-92`).
  - The prompt only hides once the door is already broken (`MapWorld.cs:1510`).
- **Fix:**
  - Wire `MapHunter.DoorBlow` (`Hunter.cs:868`) to `hunterRig.DoorBlow` with the blow index (map, about an hour), using the `BlowIndex`/`BlowCount` already planned in `AUDIO_CONTRACT.md:29`.
  - Each blow jolts the leaf. The jolt goes on the "Door leaf" child (`MapWorld.cs:879-884`), not the hinge: `FrontRoomsDoorSound` reads the hinge's rotation every frame and would fire Handle + Unlatch + Swing on every jolt (`DoorSound.cs:20-23, 49-61, 89-101`). Damage shows at 50% and 80% of `breakDoorSeconds`. The break throws the leaf open past the stop, with splinters and a bounce, and the leaf hangs crooked.
  - Hide the prompt while a door is being broken.
  - Suppress Handle and Unlatch for broken doors.
  - Shot: §3.7.
- **Owner · effort · frame cost · WebGL:** map (leaf jolts, state) + visual (damaged leaf variants, splinters) + sound (suppress handle) · M · L for a moment · yes.

### F12 (S2) The six quality levels are one tier; AA is fixed; WebGL limits are unplanned

- **Evidence:**
  - All six levels point at the same URP asset, and the setup script forces that on every run (`RenderSetup.cs:47-54`).
  - Camera AA is forced to None, so 4x MSAA is the only AA (`PostStack.cs:72`). MSAA does not fix specular or texture shimmer (03 §2.7).
  - On WebGL2, URP 17.3 compiles 32 visible lights (03 §1.8), and in Forward+ that count includes the main light (Unity, "Troubleshooting the Forward+ rendering path", https://docs.unity3d.com/6000.3/Documentation/Manual/urp/rendering/forward-plus-rendering-path-limitations.html). Measured: 24 enabled lights, 9 shadowed, at 05's capture point (`runtime_dump.txt:214`). Upper bound by geometry: about 89 cells within 16 m, one lamp per cell (03 §1.8; `MapWorld.cs:707`). The cap is exceeded only in dense spots; count lights per frame in a WebGL build.
  - Bright HDR lens edges stair-step (05 frame 34; cause UNVERIFIED). Crack lines and .96-smooth glass will alias the same way.
  - The WebGL template does not cap the device pixel ratio. The cost of that is UNVERIFIED (03 §1.5). The build script blocks the fix (F7).
- **Fix:** three tiers (Web / High / Cinematic), each with its own URP asset (§5). Trade-off to note: TAA would fix shimmer but ghosts on exactly the shots Red named (§5.3), so High keeps MSAA.
- **Owner · effort · frame cost · WebGL:** visual · M · tier-dependent · the Web tier is the WebGL plan.

### F13 (S2) The window climb has no glass, no plant, no tilt

- **Evidence:** the climb is a 0.6 s lerp with a 0.35 m lift and a 0.55 m duck. No pitch or roll is authored, and it cannot be interrupted (`Game.cs:153, 920-933`). The only climb-specific sound is FMOD Cloth (`SoundDirector.cs:516`). Whether FMOD footsteps fire during the climb is UNVERIFIED (`FrontRoomsPlayerFootsteps.cs:60-79` tracks body motion, and the climb writes the body position every frame, `Game.cs:925-927`). There is no glass to crunch, because none is left.
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
  - Keep the state word only if Red wants it, and always when captions are on (F17).
  - First sighting: a one-time post pulse (01 I14).
- **Owner · effort · frame cost · WebGL:** map (HUD, trigger) + visual (pulse profile) · S · N · yes.

### F16 (S3) Polish and process

- The aimed object has no highlight, and prompts pop on and off with no fade (01 G18).
- Pause does not pause FMOD, and restart is a hard cut (01 G19). Use the `static event Action<bool> Paused` already planned in `AUDIO_CONTRACT.md:27`; it moves to Phase 1 because shots must freeze on pause (§3.0).
- The start door shuts behind the player with no cue or shot (01 G17).
- A 1,440 ms hitch when 25 chunks built (03 §1.12). Profile it; shots must not start while chunk builds are queued.
- If FMOD fails, glass plays the door-break clip (`Game.cs:787`), while `FrontRoomsAudio.Glass()` is never called (02 §8.1).
- The key panel always reads "LEVEL 0 KEY", even in Office zones (`Game.cs:1401`).
- `Documentation/LIGHTING_SPEC.md` no longer matches the code (03 §1.13).
- Notes and reading are documented (`Documentation/UI_SYSTEM.md:34`) but not implemented. Whether they are still planned is UNVERIFIED.

### F17 (S2) No captions or visual sound cues

- **Evidence:** the game is hunted by sound, and no caption or visual sound indicator exists in `Assets/Scripts` or `Documentation` (grep). F15 removes the metre readout and maybe the state word, and §3.4 shrinks the LOCKED text, so deaf and hard-of-hearing players would lose the last non-audio threat cues.
- **Fix:** optional captions and direction markers for threat sounds ([RELAY CLICKS · LEFT], [DOOR BLOWS], [GLASS CRACKS]), driven by the same FMOD event IDs (`SoundIds.cs:15-46`). Off by default; part of the settings panel (Phase 1.10).
- **Owner · effort · frame cost · WebGL:** map (HUD) + sound (event hooks) · S · N · yes.

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
- The camera moves by position dolly and rotation. FOV changes are deltas from the player's FOV (not absolute), kept to ≤ 15°, and take ≥ 0.4 s; fast FOV shifts are a listed camera mistake (04 C2, S16). The one exception is a punch of ≤ 8° in ≤ 0.3 s, used only inside a takeover and scaled by the Camera motion setting (the §3.5 push and shatter, the §3.8 whip).
- Shake is rotation only, in degrees, and decays.
- **Gameplay never reads the rendered camera.** The aim ray and the Relay's view of the player use the rig's `BaseEye` (body + 1.62 m, base yaw and pitch). Shake, lean, jab and shot poses are picture only (§6.4). Every camera offset is clamped against the world with a short spherecast.
- A "Camera motion" setting (off / 50% / 100%) scales shake, roll, dips and FOV punches (04 S19). At Off, every takeover plays in place: no dolly, drop or roll, and look stays free; the key, lock and glass still animate. A "Reduce flashing" setting removes exposure flashes and the CA pulse and slows lamp stutter (`MapWorld.cs:1135-1155`). Every hold has a tap alternative in settings (04 S20); a tap never makes the action faster than the hold. (04 S19/S20 were not re-read for the review; UNVERIFIED here.)
- **Input and priority.** Shots and their sound beats advance only in `Phase.Playing` (or the new `Phase.Dying`, §3.8). Esc during a shot pauses and freezes it; it never cancels (Esc is pause, `Game.cs:1495`). Cancel is S (move back) or a second E. While `InShot`, E and mouse deltas are consumed and discarded, not accumulated (`Game.cs:815-816` adds them every frame today). One E press in the last 0.2 s of a door shot is buffered as "push open". A glass hold starts only on a fresh E-down on the pane (today `GetKey` at `Game.cs:959` lets an E held from a door press start breaking a pane). Priority: Caught > Cancel > Shot; Caught cancels the shot and §3.8 starts from the current camera pose.
- **HUD and listener.** During a takeover, fade all HUD except captions over 0.15 s and restore it on `ShotEnded`. The FMOD listener stays on the camera on purpose (`SoundDirector.cs:173-174`), so shot moves also move the listener; the sound chat tunes for that.
- No shot starts while chunk builds are queued (the 1.44 s hitch, F16).
- Input notation: **Move** means WASD and sprint; **Look** means the mouse. "Cone ±n°" means look is clamped around the shot direction.
- There is one post profile per shot type, blended by weight: a mild Gaussian far blur on every tier, no DOF at all in the glass shot (the pane writes no depth, `MapWorld.cs:1671`, so DOF would blur its cracks as background), and no motion blur on the Web tier.
- **Era check.** Every lens effect must pass a found-footage tone check: a 1990s small-CCD camcorder shows vertical smear on bright lamps, halation and deep depth of field, not anamorphic flare streaks, lens dirt or shallow bokeh (art judgement, UNVERIFIED by a source).
- Haptics: none; keyboard and mouse only (`Game.cs:815-828`). If a gamepad is added, rumble fires on the shake beats from `FrontRoomsShotTimings`.
- Existing FMOD events are named as they appear in `SoundIds.cs:15-46`. Names marked **NEW** are proposals for the sound chat, following the same path style.
- All times are ESTIMATES. Tune them on a capture.

### 3.1 Key pickup

**Input lock:** none. **Duration:** 0.95 s.

**Trigger:** the key is aimed within the 2.4 m reach and the prompt reads "E · TAKE KEY". This needs the key's collider back (`MapWorld.cs:733`). The key rests on a surface (desk, cabinet or hook) where furnishing allows, otherwise on the carpet. It does not spin or glow (F10).

| t (s) | Camera | Object / VFX | Sound | Map event |
|---|---|---|---|---|
| 0.00 | Only if the mouse is idle: pitch eases ≤ 6° toward the key (0.2 s, ease-out). Released as soon as the mouse moves. | The key lifts off its surface. | — | `KeyPickupStarted(zone, pos)` NEW |
| 0.00–0.25 | — | The key travels to a held pose 0.35 m ahead, lower right of frame (about 65% across, 70% down), ease-out, and turns so its paper zone tag faces the lens. The player's radius is 0.3 m (`Units.cs:92`), so facing a wall this pose is inside it: draw held objects on their own layer through a Render Objects pass with a depth override, or clamp the pose with a spherecast. | — | — |
| 0.25 | — | The key arrives. The tag swings (damped, two swings). | `Foley/Player/KeyPickup` (exists; fires at pickup today, `SoundDirector.cs:474`) | `KeyTaken(zone)` (exists, moved to this beat) |
| 0.25–0.75 | — | The key is held; the brass catches lamp highlights (needs F4). | — | — |
| 0.75–0.95 | — | The key drops out of the bottom of the frame (pocketed), ease-in. | `Foley/Player/Pocket` NEW at 0.85 | — |
| 0.95 | — | The existing key panel (`Game.cs:1394-1401`) fades in, with its label changed to the zone name (F16). | — | — |

**HUD:** drop the "OPENS THIS ZONE'S DOORS" flash until keys open doors (F1).
**WebGL fallback:** picture identical; sound UNVERIFIED until a WebGL build with FMOD banks has run (F9). This applies to every shot below.

### 3.2 Unlocking a locked door with the key (Red's example)

**Input lock:** yes. Move is locked from 0.00 to 1.45 s. Look is locked from 0.00 to 1.30 s, then blends back over 0.2 s.
**Duration:** 1.55 s. **Commit point:** 0.86 s. After that the door counts as unlocked even if the shot is cancelled.
**After the commit point the player is not trapped.** Chase is 4.2 m/s and the catch is 0.7 m (`FrontRoomsHunter.cs:25, 28`), so 0.59 s of lock lets a Relay 2.5 m away reach the player. If the Relay enters Chase or gains sight after 0.86 s, movement and look return at once, the camera snaps back in ≤ 0.15 s, and the key and bolt finish off camera. The door is already unlocked, so nothing is lost.

**Trigger:** E on a locked door while holding the key that §7 Q3 decides (today: the zone the player stands in).

**Anchor:** the module spec already fixes the lock and handle point at 1.0 m up, 0.08 m in from the latch jamb and 0.03 m proud of each face. It is "the point `DoorUnlocked` reports" (`Documentation/LEVEL_MODULE_SPEC.md:48`), and the constants exist (`Units.cs:58`, `DoorHandleHeight/Inset/Proud`). The API is named `FrontRoomsMapWorld.LockPoint` (`Units.cs:57`) but does not exist yet. No code raises `DoorUnlocked` yet (grep at 21:10).

**Framing pose P:** 0.45 m from the lock along the door normal toward the player, with the eye dropped by at most about 0.25 m (to about 1.35 m; the eye is 1.62 m, `Units.cs:92`, and the lock 1.0 m), pitched down 25–30° to the lock. The drop is scaled by the Camera motion setting. A full drop to lock height would be a 0.56 m crouch plus a 14° FOV change in under 0.55 s, the biggest camera move in the game.

| t (s) | Camera | Object / VFX | Sound | Map event |
|---|---|---|---|---|
| 0.00 | The shot starts and blends from the eye toward P. Position uses a cubic ease-in-out; rotation slerps to look at the cylinder. Travel takes 0.30 + 0.12 × distance in metres, clamped to 0.35–0.55 s. | The prompt hides. The shot volume goes 0 → 1 over 0.40 s: DOF focused on the cylinder, vignette +0.1, post-exposure +0.15. | `Snapshot/Closeup` NEW (room tone ducked about 3 dB) | `ShotStarted(UnlockDoor)` NEW |
| 0.00–0.45 | FOV 76 → 62 on the same curve. | — | — | — |
| 0.30–0.55 | Arrived; slight hand-held drift of 0.1° (motion setting). | The key enters from lower right and travels to 3 cm in front of the keyway, ease-out, rolling to align. | — | — |
| 0.55–0.68 | — | The key slides 2.5 cm in, with a 30 ms catch at 60% (the pins). | `Mechanism/Lock/KeyInsert` NEW at 0.55 | — |
| 0.68–0.90 | A 0.2° roll follows the turn. | The key turns 90°: the first 10° slow (resistance), then ease-out. | `Mechanism/Lock/KeyTurn` NEW at 0.68 | — |
| 0.86 | 0.3° rotation jolt, 80 ms. | The bolt retracts: the leaf shifts 1.5 mm in the frame. | `Mechanism/Lock/BoltRetract` NEW at 0.86 | `DoorUnlocked(door, zone, lockPoint)` (planned in `AUDIO_CONTRACT.md:28`; commit) |
| 0.90–1.15 | — | The key turns back and withdraws; it is out of frame by 1.15. | tail of KeyTurn | — |
| 1.00–1.25 | — | The leaf pops ajar to 10°, ease-out with a 1° overshoot. | `Mechanism/Door/Handle` + `Unlatch` (exist). `DoorSound.cs:89-92` fires them by itself when the leaf leaves the frame. | `DoorMoved` (exists) |
| 1.15–1.55 | The camera returns to the eye pose with the player's pre-shot yaw and pitch, cubic ease-in-out. FOV 62 → 76. | The shot volume goes 1 → 0. | snapshot released | — |
| 1.30 / 1.45 | Look returns (0.2 s blend), then move. | — | — | `ShotEnded` NEW |

**After:** the door rests ajar at 10°. Walking into it pushes it open (the RE7 "ajar, then push", 04 K3), or E swings it fully. Push speed sets the Relay noise: a fast push slams at 14 m as today (`Game.cs:781`, in `OnDoorMoved`), a slow push creaks at about 5 m. That is a design change for Red (§7 Q4), and it needs AI and physics work:
- Ajar must be its own value in `Door` and `PassageBetween`. Today `SetDoor` marks any opened door Open at once (`MapWorld.cs:991, 1555`), so the Relay would path into a leaf still standing at 10°; if ajar were stored as closed, the Relay would break it down (`FrontRoomsMapHunter.cs:493-511`). The Relay should treat ajar as Open with a shove.
- Doors are transform-animated colliders (`MapWorld.cs:1590-1600`); a CharacterController cannot push them. The push needs `OnControllerColliderHit` or a trigger that advances `door.progress`.
- If the Relay starts breaking the same door from the far side (`DoorBlow` on that door), cancel the shot.

**Cancel (before 0.86 s):** the Relay enters Chase or comes within 6 m with line of sight, or the player presses S or a second E after 0.2 s (not Esc, which pauses; §3.0). The key withdraws in 0.15 s, the camera returns in 0.25 s, and the door stays locked. After 0.86 s the turn completes, but a Chase or sight trigger frees the player at once (above).

**Light:** an optional small, unshadowed "shot light" on the camera at 0.6 intensity during the shot, so the brass reads under a dead lamp. It costs one of the 32 WebGL lights (F12).

**Close-up detail:** at 0.45 m and FOV 62 (Unity FOV is vertical) the frame is about 0.54 m tall, about 2,000 px/m at 1080p. `DoorVeneer_A.png` is 1024 × 2048 over a 1.12 × 2.62 m tile (`Door_Veneer.mat:69`), about 780–910 px/m, so the leaf near the lock would be magnified about 2.2–2.6× and look soft (ESTIMATE). The lock plate needs its own mesh or a detail map (§6.4).

**WebGL fallback:** Gaussian far blur instead of Bokeh, no motion blur, and the shot light only if under the light cap.

### 3.3 Opening a door normally

**Input lock:** none. **Duration:** 0.75 s.

| t (s) | Camera | Object | Sound | Map event |
|---|---|---|---|---|
| 0.00 | A 0.3° forward pitch impulse (the push), decaying over 0.15 s (motion setting). | The lever rotates down 35° in 0.08 s. | — | — |
| 0.08 | — | The leaf starts: 95° over 0.55 s with ease-out, because a pushed door starts fast and slows. Today it is smoothstep (`MapWorld.cs:1595-1596`). | `Handle` + `Unlatch` (automatic, `DoorSound.cs:89-92`); `Swing` loop driven by angular velocity (exists) | `DoorMoved` (exists) |
| 0.12–0.22 | — | The lever springs back. | — | — |
| 0.63–0.75 | — | A 2° overshoot at the stop, then it settles. | `StopLimit` with Impact from speed (exists, `DoorSound.cs` `EndMotion`) | — |

**Option for Phase 2 (needs Red):** holding E opens slowly with a creak over 1.6 s, at half the noise radius. This is Outlast's two door speeds (04 S29).

**Shutting a door ("E · SHUT DOOR", `MapWorld.cs:1511`)** is the player's main defence, because the Relay must break a shut door (`FrontRoomsMapHunter.cs:493-511`). Give it the same grammar: the leaf closes on the existing curve, `LatchStrike` fires from `DoorSound` at the close (`DoorSound.cs:118-121`), a 0.3° camera impulse lands on the latch, and the existing Relay noise stays (`Game.cs:781`).

### 3.4 The locked-door rattle (no key)

**Input lock:** none. **Duration:** 0.40 s.

| t (s) | Camera | Object | Sound | Map event |
|---|---|---|---|---|
| 0.00 | — | The lever goes down 20° and stops hard (0.05 s). | `Mechanism/Door/Locked` (exists), authored as two rattles 0.16 s apart | `DoorLocked` (exists), plus a 6 m Relay noise NEW (design) |
| 0.05 | 0.25° forward impulse. | The leaf jolts 2 mm / 0.3° toward the player against the bolt and springs back in 0.06 s. The jolt goes on the "Door leaf" child, not the hinge, or `DoorSound` would play a full door opening (F11). | — | — |
| 0.16 | 0.25° impulse. | A second jolt. | — | — |
| 0.20–0.40 | — | The lever returns. | — | — |

**Lock state you can see:** a brass deadbolt cylinder with a small zone tag plate beside it. Then the prompt "LOCKED · NEEDS THIS ZONE'S KEY" can shrink to "E · TRY DOOR", followed by "LOCKED" for 1.5 s after a try (keep the longer text when captions are on, F17).

### 3.5 Hold to break glass: crack stages and the shatter (Red's example)

Keep the existing 1.0 s hold and its FMOD beats at 0.35, 0.70 and 1.0 (`SoundDirector.cs:452-453`). In B the body is shown through the camera: the hold reads as three shoulder shoves that land on those beats.

**Input lock:** Move is locked while E is held; today the player can walk away mid-hold (01 I9), so this is a change to play (§7 Q6). Look is clamped to ±8° around the hit point, so looking away no longer cancels. Cancel = release E, or the Relay gaining sight.
**Release:** cracks do not heal. The next hold resumes from the stage already reached (02 §8.5).
**Tap mode (setting):** each tap adds 0.35 s of progress, with a ≥ 0.3 s cooldown, so the total stays ≥ 1 s. Noise and Relay risk are identical to the hold, and the FMOD beats still fire on progress (`SoundDirector.cs:452-453`).

Time = hold progress × 1.0 s. The impact point is the aim ray's hit point, clamped at least 0.2 m from the frame.

| t (s) | Stage | Camera | Glass / VFX | Sound | Map event |
|---|---|---|---|---|---|
| 0.00–0.35 | Push | Lean 5 cm toward the pane; FOV −3° (sine ease). | A palm smudge fades in at the impact point (smoothness drops locally). The pane appears to bow through a normal-map perturbation in the glass shader (the primitive cube has 4 vertices per face, so a vertex bow is impossible), so its reflections swim. | `Mechanism/Window/Stress` loop with `Progress` (exists) | `GlassHold(pos, p)` (exists; add the hit point) |
| 0.35 | Crack 1 | Shove: a 4 cm forward jab and back over 0.12 s, plus a 0.4° rotational shake for 120 ms. | The crack mask reveals 5–7 radial cracks reaching 25–35% of the way to the frame, over 60 ms. 3–6 chips fall. | `Mechanism/Window/Crack` (exists) | `GlassCracked(pos, 1, uv)` NEW |
| 0.35–0.70 | Spread | The lean holds. | The cracks creep (the mask threshold follows progress). | the stress loop roughens | — |
| 0.70 | Crack 2 | Shove 2; 0.6° shake. | The radial cracks reach the frame. One or two concentric rings appear 8–20 cm around the impact. Each segment's normal tilts a fraction of a degree (per-cell normals in the crack mask), so the reflection breaks into facets (needs F4). | `Crack` (exists) | `GlassCracked(pos, 2, uv)` NEW |
| 0.70–1.00 | Creak | — | No geometry change (a 1–3 mm shift is 1–2 px at 1 m and impossible before the fracture swap). | stress peaks | — |
| 1.00 | Shatter | Shove 3. Shake 1.5°, decaying over 250 ms. FOV punch −3° and back over 0.3 s (the §3.0 exception). The lean releases over 0.3 s. CA pulse 0.06 → 0.2 → 0.06 over 0.25 s (off with Reduce flashing). | Swap to the pre-fractured variant whose centre the impact was snapped to (§4.4 item 2). Inner pieces fly away from the player at 2–4 m/s with spin; middle pieces drop with a 0–300 ms stagger; edge pieces stay as teeth. 150–250 glint mesh particles and a dust puff. | `Mechanism/Window/Shatter` (exists) | `GlassBroken(info)` (exists; add point, normal, seed and side) |
| +0.35–0.60 | Settle | — | Pieces land (a 1.2 m fall takes about 0.49 s). | `Mechanism/Window/ShardLand` NEW, at the real landing times (or baked into the Shatter tail) | — |
| +1.5 | Rest | — | Rigidbodies sleep and become one static combined mesh: the teeth plus floor glass, about two thirds of it on the far side. | — | — |
| After | — | — | The glass stays on both floors and persists per window across chunk rebuilds, keyed by edge and chunk revision (§4.4). When the Relay crosses the broken window (it is `Passage.Open` to it, `MapWorld.cs:994`), it snaps the remaining bottom teeth and fires `ToothSnap`. | Footsteps near the window use a glass surface (NEW parameter value) | — |

The numbers come from 02 §8.3, adjusted for B.

**WebGL fallback:** if the particle module is not added, use rigidbody shards only (≤ 24) and no glints. The crack mask is one texture sample and works everywhere. No refraction.
**Desktop extra (optional):** turn on the opaque texture per camera for crack distortion (02 §6.6).

### 3.6 Climbing through the broken window

**Input lock:** Move is locked, as today. Look stays free, but pitch is eased toward the far side.
**Duration:** 0.6 s, as today, with the plant and the landing fitted inside it. The draft's 0.85 s would add 0.25 s of lock (about 1 m of Relay closing at 4.2 m/s) right after the loudest noise in the game (glass, 40 m × hearing 1.4 = 56 m; `Game.cs:148`, `FrontRoomsHunter.cs:32`). A longer climb is a balance change for Red (§7). **Trigger:** as today (`TryStartClimb`, `Game.cs:891`).

| t (s) | Camera | Object / VFX | Sound | Event |
|---|---|---|---|---|
| 0.00–0.15 | Duck 0.30 m, pitch down 10° to look at the sill, roll 3° toward the leading side. | — | `Foley/Player/Cloth` (exists) | `PlayerClimbed` (exists, `Game.cs:914`) |
| 0.15 | Plant: a 0.5° jolt as weight goes onto the sill. | The bottom-rail teeth snap off as 3–5 small pieces. | `Foley/Player/ClimbSill` NEW, `Mechanism/Window/ToothSnap` NEW | — |
| 0.15–0.45 | Over the sill: the existing lift arc (0.35 m) and duck (0.55 m at mid-climb). Pitch and roll return to 0. | — | — | — |
| 0.45–0.60 | Landing: dip 6 cm and recover on a critically damped spring (the recovery may run on after control returns). | Floor shards shift. | `Foley/Player/Footstep` with Surface = Glass NEW, at 0.47 and 0.58 | Relay noise 8 m NEW (design) |

### 3.7 The Relay breaking a door (seen from the player's side)

**Input lock:** none; the player must be able to run.
**Duration:** 2.5 s of blows (`breakDoorSeconds`, `FrontRoomsHunter.cs:21`), then a 0.12 s throw, a bounce, and a 0.3 s reveal. `breakDoorSeconds` is a tuning field that the planned tiers change (`FrontRoomsHunter.cs:31`), and blows are every 0.5 s (`FrontRoomsMapHunter.cs:38`), so damage is tied to fractions of it, not blow numbers.

| t (s) | Camera (only when the player is within 8 m) | Door / VFX | Sound | Event |
|---|---|---|---|---|
| each blow (every 0.5 s) | Rotation shake from 0.2° rising to 0.6° with the blow count, 150 ms. | The leaf jolts 4–8 mm / 0.6–1.2° toward the player and springs back in 0.12 s (on the "Door leaf" child, not the hinge; F11). The Relay rig's chest snaps (`hunterRig.DoorBlow`, F11). Dust falls from the head. A sliver of far-side light shows at the latch-side gap. | `Mechanism/Door/Blow` with `Damage` (exists, `SoundDirector.cs:476-482`) | `DoorBlow(Vector3)` (exists) plus hunter `BlowIndex`/`BlowCount` (planned, `AUDIO_CONTRACT.md:29`) |
| 50% of `breakDoorSeconds` | — | Damage 1: the veneer splits near the latch (texture or mesh swap). | — | — |
| 80% | — | Damage 2: splinters at the latch; the strike plate bends. | — | — |
| 2.5 | Shake 1.0°, decaying over 300 ms. | The leaf is thrown open in 0.12 s past the stop, bounces back to about 80° and hangs 3° crooked (hinge torn). 8–15 splinter mesh particles; the strike plate flies off. | `Door/Break` + `Door/StopLimit` with Impact 1 (exist). Suppress Handle + Unlatch for broken doors (`DoorSound.cs:89-92`). | `DoorBroken` (exists) |
| 2.5–2.8 | — | The Relay holds 0.3 s in the doorway, back-lit by the far room (the reveal). | Relay stinger as today | hunter change NEW |

Also hide the door's prompt while it is being broken (F11).
**WebGL fallback:** splinters are optional; everything else is transforms.

### 3.8 Being caught

**Input lock:** full, from 0.00. **Duration:** 2.0 s, then the card. It runs in a new `Phase.Dying` that keeps the rig and camera running; `End()` and `Phase.Caught` come at 2.0 s (today `caught` stops the hunter tick, `FrontRoomsMapHunter.cs:141`, and `End()` jumps straight to `Phase.Caught`, `Game.cs:1568-1571`).
**Needs:** `Caught(Vector3 relayHead)`. Today `Caught` carries nothing (`Hunter.cs:241`). Drive the lunge on the rig directly.

| t (s) | Camera | Relay / screen | Sound | Event |
|---|---|---|---|---|
| 0.00–0.25 | Whip to face the Relay's head: yaw and pitch slerp, ease-out. FOV −8° (the §3.0 exception). | The Relay goes into a lunge pose and moves ≤ 0.15 m toward the camera (the catch is at 0.7 m and the Relay's radius 0.3 m, `FrontRoomsHunter.cs:28`, `Units.cs:94`; a 0.4 m lunge would put the 0.06 m near plane inside it). CA 0.06 → 0.35, vignette 0.26 → 0.5. | `Relay/Lunge` NEW | `Caught(relayPos)` (changed) |
| 0.25 | Impact: the camera is knocked back 0.15 m (world-clamped) and rolls 8° over 0.2 s; shake 2.5°, decaying. | A 2-frame exposure flash (+1.5 EV; off with Reduce flashing). | Today's hard cut to silence plus `Subjective/Tinnitus` moves to this beat (`SoundDirector.cs:500-514`). | `CaughtImpact` NEW |
| 0.45–1.05 | Fall: the camera drops to 0.3 m height (ease-in, world-clamped) and rolls to 25°, looking up. | The Relay stands over the camera, framed against the troffers as a silhouette. | tinnitus | — |
| 1.00–1.80 | — | Fade to black. | — | — |
| 2.00 | — | The card fades in over 0.4 s, with today's text. | — | `End()` |

In `Phase.Dying`, R is ignored until 0.6 s, then jumps to the card (today R restarts the scene in any phase but Playing and Title, `Game.cs:1496`). Until the new Relay model lands, keep the Relay in silhouette (back-lit, exposure down): the current capsule rig falls apart at close range (frame [80](images/80_relay_broken_%2B1000ms.png)). The card colour (white or black) is Red's call (§7).

---

## 4. Glass spec

### 4.1 Pane geometry (map chat)

| Item | Today | Target |
|---|---|---|
| Thickness | 30 mm (`GlassThickness = .03f`, `Units.cs:61`) | 6 mm (real float glass; 02 §5) |
| Glazing stop | none: the frame is two jambs and a head (`MapWorld.cs:858-867`) | A stop on both faces, all four sides, 18 mm wide × 12 mm deep, in the trim material |
| Sill | bare wall block under the opening (`MapWorld.cs:854`); the module spec says "no sill trim" (`LEVEL_MODULE_SPEC.md:49`) | A stool trim 25 mm proud. The spec line needs updating. |
| Edge faces | same material as the face | `Glass_Edge`: near-opaque green, linear (.28, .42, .34), smoothness .6. Real float glass edges look green (02 §4.3). |
| Shadow casting | On: the material keeps its ShadowCaster pass and the renderer is On (`MapWorld.cs:901-906, 1663-1680`; `runtime_dump.txt:239, 274`) | Off on the pane renderer |
| Collider | box | Keep it. It is the aim target and it blocks the Relay's sight (01 §I16). Once the glass reads as clear, the player sees through it but the Relay cannot (§7 Q15). |
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
- `Kit_InteriorWindow` is placed in half of the Office rooms with a ceiling of at least 2.6 m (`FrontRoomsOfficeKit.cs:405`). Its pane is opaque `Prop_GlassCRT`, which its own asset script says reads as a black slab (`Tools/Blender/frontrooms_kit/assets/interior_window.py:28-31`; 02 §3). Move it onto the `FrontRooms/Glass` graph with an interior-mapping back layer (02 §5.2, V5). Visual, M (Phase 3.12).

**Shards:** `Glass_Shard` is opaque, with a near-black base, smoothness .95 and green edge faces. Opaque shards avoid transparent sorting problems and overdraw (02 §8.4). Moving shards and particles cast no shadows; only the settled teeth and floor-glass mesh may. Shards, key and door leaf use URP Lit or Shader Graph materials, which have a MotionVectors pass, not `FrontRooms/Surface` (it has none, `Surface.shader:80-83, 266-269, 285-288, 302-305`), so they stay correct if TAA is ever turned on.

### 4.3 Reflection setup

- **Step 0 (visual + map, S, all tiers).**
  - The reflection and ambient the game uses come from the scene file, not from `FrontRoomsLook` (F4). First make the look code run in the game: the map chat calls `ApplyAmbient()` and `SetZoneReflection` at run start (`Game.cs` `Awake`, near `:299-301`) and on zone change, or Red changes the scene's Lighting settings.
  - Capture three 256 px HDR cubemaps in the editor with the fixtures on: a lit Level 0 room, a lit Office room and a dead-lamp room. Add cubes for the title-stream rooms (Lobby, Shift, Office, Run in red, Exit in cyan; `BACKROOMS_VISUAL_SPEC.md`), owner visual (RoomStream).
  - Add `FrontRoomsLook.SetZoneReflection(kind)`. It sets `RenderSettings.defaultReflectionMode = Custom` and `customReflectionTexture = cube`. 02 §6.1 found both APIs in the WebGL player module, but that a runtime change reaches URP's bound default cube (`UniversalRenderPipeline.cs:2201`), with or without `DynamicGI.UpdateEnvironment()`, is UNVERIFIED. Prove it with a short play-mode test in a clone.
  - Risks: a lit-room cube makes glossy floors glow in dead-lamp corridors (lamp temperaments, `MapWorld.cs:1074`; 05 frame 37), and every glossy surface changes at once on a zone crossing, including panes that sit on zone borders. So keep intensity ≤ 0.5 until step 1 lands (or drive it from the nearest lamp's state), use the dead-lamp cube where the lamp is dead or dim, and crossfade over about 0.5 s.
  - Then tune intensity toward 0.7–1.0. Before ranking it, capture the cube alone with 05's harness (seed 4242, frames 01, 04, 23, 34, 35, and a dead-lamp frame). 05 frame 07 showed a realtime probe barely changes glass at 50°, so the expected gain is high on VCT and metal, low on glass (UNVERIFIED until captured).
- **Step 1 (visual + map, M, desktop tiers).**
  - At chunk build, spawn one Custom `ReflectionProbe` per room (or per window cell). Its box is the room on the 3 m grid, box projection is on, and its cubemap is the zone cube.
  - **Probe blending is required** (`URP.asset:54` = 1). The shell is merged into one renderer per 6 m block × ceiling class × material (`MapWorld.cs:22, 636-649`). With blending off, Forward+ gives each renderer one probe on the CPU (`UniversalRenderPipeline.cs:2092-2098`; `GlobalIllumination.hlsl:425`), so a per-room box would be wrong in most of a block. With blending on, URP sets the probe keywords and uses the per-pixel cluster path (`ForwardLights.cs:538-540`). The atlas is already on (`URP.asset:56`). The alternative is to split shell renderers per room.
  - Turn on `m_ReflectionProbeBoxProjection: 1` (`URP.asset:55`).
  - Shader: if every tier that uses probes has blending and box projection on, add `#define _REFLECTION_PROBE_BLENDING 1` and `#define _REFLECTION_PROBE_BOX_PROJECTION 1` before the URP includes in `Surface.shader` (no new variants; `GlobalIllumination.hlsl:33-39`). If a tier turns blending off, declare only `multi_compile_fragment _ _REFLECTION_PROBE_BLENDING`. Never declare `_REFLECTION_PROBE_ATLAS`: undeclared, the cluster loop already includes probes (`Clustering.hlsl:9`). Unity warns that on the Web "don't include unwanted shader variants" (https://docs.unity3d.com/6000.3/Documentation/Manual/web-graphics-apis-intro.html).
  - Cost: L–M per pixel plus atlas memory, not N. The atlas is keyed per probe instance (`ReflectionProbeManager.cs:162`), a probe unseen for more than a frame is evicted and re-blitted (`:120`), visible probes are capped at min(light cap, 64) (`UniversalRenderPipeline.cs:172`; 32 on WebGL2), and probes count as items in the Forward+ tiles (`ForwardLights.cs:245`). ESTIMATE: about 5 MB per 256 px probe. So use 64–128 px room cubes, enable probes only for the nearest 8–12 rooms (or one per 6 m block), and measure the "URP Reflection Probe Atlas" in the Memory Profiler before committing.
  - Web tier: step 0 only.
  - The map is generated at runtime, so editor-baked per-room probes are not possible (02 §6.2).
- **Step 2 (desktop High/Cinematic only, optional).** When a glass hold starts, render one realtime probe once at that window ("Via Scripting", time-sliced), so the crack facets reflect the actual room.
- **Not planned.** URP 6.3 lists Screen Space Reflections, Planar Reflections and Screen Space Refractions all as "No" (feature comparison page, read for this report). A scripted planar mirror costs about one extra scene render per plane (02 §6.3), which is not viable for windows.

### 4.4 Breakage implementation plan

1. **Map (M):**
   - Replace the edge-keyed sets (`MapWorld.cs:192-194`) with one per-edge record that survives rebuilds: {lockState, angle01, breakStage 0–3, impact uv, seed, side}. A chunk the player left comes back through `Cache.Shift`, which bumps its revision and changes its interior (`MapWorld.cs:591-593`; `FrontRoomsMap.cs:706-711`). On a shift, keep the record only if the edge is still a door or window; otherwise drop it with its floor glass. Today no unlocked-door set exists, so an unlocked door that is shut would relock after a rebuild (§7 Q3b).
   - `Hold()` takes the hit point.
   - Stages persist when the player lets go.
   - Raise `GlassCracked` and a richer `GlassBroken`.
   - Swap in the fractured prefab instead of `Kill(window.pane)` (`MapWorld.cs:1571`).
   - On chunk rebuild, rebuild the teeth and the floor glass as static meshes instead of skipping the pane (`MapWorld.cs:900`).
2. **Visual (M):**
   - Fracture variants that line up with the cracks. The impact point is wherever the aim hits, and there is one pane size (1.40 × 1.65 m, `Units.cs:61`), so a few fixed-centre variants would not match the crack mask. Recommended: snap the impact to the nearest authored centre (for example 3 × 3 centres × 2 variants = 18 meshes, from a radial point set in the Blender kit, e.g. Cell Fracture, 02 §7) and bake each variant's crack mask from its own fracture edges. Alternative: a 2-D radial fracture of the 6 mm slab at runtime, with the crack mask drawn from the same data; profile it on WebGL's single thread (`Build.cs:127`). Pieces are tagged inner, middle and tooth; they are flat slabs with green edges.
   - Glint and dust particle prefabs (needs F9).
3. **Sound (S):**
   - Fire cracks from `GlassCracked(stage)` instead of progress thresholds. Today `lastStressProgress` resets to 0 when a new stress loop is created (`SoundDirector.cs:449`), so a resumed hold would replay crack 1.
   - Add the shard-landing tail and a glass footstep surface.
4. **Budget (ESTIMATE; UNVERIFIED until profiled):**
   - ≤ 24 rigidbodies for ≤ 2 s; each is its own renderer with a unique mesh, so no instancing or static batching;
   - 150–250 mesh particles for ≤ 2 s;
   - about 25–35 extra draws during the break (02 §8.7's 3–5 was too low), with shadow casting off on moving shards and particles (otherwise every shadowed lamp in range redraws every shard);
   - 1–2 draws per broken window afterwards.
5. **Glass type (Red's call):**
   - Default: an annealed look with big shards and teeth, as an art-direction choice. A pane with a 0.35 m sill is "close to floor level" and would legally be tempered (02 §5.1).
   - Option: tempered granules with no teeth.
   - Wired glass for door lites is P2.

---

## 5. Rendering

### 5.1 What "AAA" can honestly mean here

**Web (WebGL2), the current web target:**
- Unity calls WebGPU "experimental and not recommended for production usage". Compute shaders are listed as a WebGPU feature, not a WebGL2 one (Web graphics page).
- The Web "only supports Baked Global Illumination", with non-directional lightmaps only (Web graphics APIs intro page, https://docs.unity3d.com/6000.3/Documentation/Manual/web-graphics-apis-intro.html).
- URP 17.3 compiles 32 visible lights for WebGL2, including the main light in Forward+ (03 §1.8, URP `Input.hlsl:17-24`). 24 were enabled at 05's capture point; the geometric upper bound within 16 m is about 89 (F12).
- FMOD on WebGL is unproven (F9).
- DBuffer decals do not support OpenGL/GLES (03 §8). That WebGL2 inherits this is UNVERIFIED.
- VFX Graph needs compute shaders (02 §6.7, 04 S23).
- **Realistic bar:** a polished, art-directed indie frame, not AAA. Red should hear this plainly.

**Desktop URP (Metal or DX12):**
- URP 6.3 has no SSR, planar reflections, screen-space refraction, SSGI, contact shadows or volumetric fog, and exposure is "Fixed" only (feature comparison page, read).
- With the §5.4 changes and two custom passes (contact shadows and ray-marched spot scattering), the indoor frame can reach a convincing "indie-AAA" level (03 §4). That is an UNVERIFIED goal: nothing was GPU-profiled, and the only timing is 05's editor render plus readback (14–18 ms). URP 17.3 compiles the non-Render-Graph path only under `URP_COMPATIBILITY_MODE`, which this project does not define (`ProjectSettings/ProjectSettings.asset:826-844`), so both custom passes must be written with the Render Graph API (https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-introduction.html); that makes each L.
- Ray-traced GI and reflections, SSR, HDRP volumetrics and subsurface skin stay out of reach without very large custom work.

**HDRP:** it has all of the above natively, but it drops WebGL and means rewriting `FrontRooms/Surface`, the post stack, the lookdev tools and every runtime-built material. Not this semester (03 §4).

**The two shots Red named do not depend on the platform.** They are timing, staging, debris and reflections, and all of these work on WebGL2 (picture; sound UNVERIFIED, F9).

**Against the project's own target.** The lighting target in `Documentation/BACKROOMS_VISUAL_SPEC.md:31-33` names Figma refs `2127:68` (Escape the Backrooms) and `2127:56` (The Exit 8): a few visible fixtures making local pools, with corners and reveals falling off. Frames 01, 34 and 35 show the opposite (an even wash, F5). The AAA references in 03 and 04 (RE Village, RE7, TLOU2, Alien) were chosen by the auditors, not by Red; §7 Q13 asks which he meant. Claims about those games' tech remain as sourced in 03/04.

### 5.2 Recommendation on platform and tier

- **Quality bar:** the macOS desktop build at the High tier.
- **Capture tier:** a Cinematic tier for presentation captures.
- **Sharing:** WebGL as a reduced Web tier, judged in a browser on an ordinary laptop, not in the editor. 02 §6.7 recommended the opposite (judge the design in WebGL). This report chooses desktop because Red's complaint is about quality, and the Web limits (32 lights, no realtime GI, no compute) would cap the answer before the content is fixed. `WEBGL_BUILD.md:17` chose the Generic texture subtarget for "broad desktop and mobile browser compatibility"; whether mobile browsers are in scope is §7 Q14.
- The editor's active build target is already StandaloneOSX (03 §1.1; 05 §A).
- **Before any of this, fix F7,** so that what Red judges is actually the URP game.

### 5.3 Tiers (condensed from 03 §5; frame targets are proposals, nothing is measured)

Each tier has one URP asset. The setup script must stop forcing one asset into every quality level (`RenderSetup.cs:47-54`), and camera AA must be chosen per tier (`PostStack.cs:72`).

| Setting | Web (WebGL2, 720p, DPR capped at 1) | High (desktop default) | Cinematic (captures) |
|---|---|---|---|
| AA | MSAA 2x or SMAA | MSAA 4x (as today, `PostStack.cs:72`); add SMAA if shimmer is a concern. TAA only after a harness capture of §3.5 and §3.7 shows no smear | STP or TAA at render scale ≥ 1.0 |
| Lamp light radius | about 9.5 m by area for 32 lights (ESTIMATE); set it after counting visible lights in a Web build | 16 m | 20 m |
| Shadowed lamps | nearest 4, 512 px | nearest 8–10, 1024 px | nearest 14–16, 1024–2048 px |
| Lamp cone and range | every lamp ~115°, range ~6 m (8 m Tall), no extra fill lights; shadow strength fades over ~0.5 s on joining or leaving the set | same | same |
| Directional fill | off | off | off |
| Reflections | zone cubemaps | + box-projected room probes | + one realtime probe at a hero window |
| SSAO | downsampled, Low | full res, Medium | full res, High |
| Shafts | depth-faded beam meshes | + quarter-res scattering | half-res scattering with shadows |
| Decals | Screen Space | DBuffer | DBuffer |
| Textures | WebGL override 1024–2048, mip streaming (03 §5) | full | full |
| Shot profiles | mild Gaussian far blur, no motion blur; no DOF in the glass shot | same + camera motion blur | same + optional object motion blur (only with TAA and motion vectors) |
| Download | today about 7.7 MB (the four files `Builds/WebGL/index.html` loads, measured); measure each addition in a clone build | — | — |
| Target (UNVERIFIED goals) | 30–60 fps on an M1 / Iris Xe laptop | 60 fps on a mid desktop GPU | 30–60 fps |

Why not TAA on High: TAA "uses motion vectors", ghosts when an object "moves quickly in front of a surface that contrasts with it", and cannot be combined with MSAA (Unity 6.3, https://docs.unity3d.com/6000.3/Documentation/Manual/urp/anti-aliasing.html). `FrontRooms/Surface` has no MotionVectors pass (`Surface.shader:80-83, 266-269, 285-288, 302-305`) and the door veneer uses it (`Door_Veneer.mat:11`), so a swinging or thrown leaf would ghost; the pane writes no depth (`MapWorld.cs:1671`), so its cracks would smear under camera shake (UNVERIFIED in a capture); and 150–250 fast shards are the documented ghosting case. If TAA is adopted, add a MotionVectors pass to FR Surface first.

### 5.4 Ranked rendering changes (03 §6, re-ranked and corrected)

| Rank | Change | Finding | Gain | Cost | Owner | Web |
|---|---|---|---|---|---|---|
| 1 | Rebuild on URP; delete `Build.cs:61-62`; fail the build when no pipeline is set | F7 | very high | < 1 h | build owner (map default) | yes |
| 2 | Make the look code run in the game; zone cubemaps as the custom reflection, intensity ≤ 0.5 at first | F4 | expected high on VCT and metal, low on glass (05 frame 07); UNVERIFIED until captured | hours | map (runtime call) + visual | yes |
| 3 | Every lamp ~115° with a cookie, shorter range; nearest-N shadows with a fade; stop the unshadowed leak | F5 | high | hours | map + visual | yes (4 casters) |
| 4 | Remove the directional fill (scene and code); per-zone ambient (needs rank 2's runtime call) | F5 | medium-high, and it saves a shadow pass | hours | map (scene edit with Red) + visual | yes |
| 5 | Textured troffer lens in Level 0 zones (one line); a vertical-smear and halation pass on troffers instead of lens dirt and flare streaks (era check, §3.0) | F10 | medium-high (in almost every frame) | hours | map + visual | yes |
| 6 | Glass Shader Graph and the 6 mm pane (§4) | F3 | high on the shot Red named | 1–3 days | visual + map | yes |
| 7 | Shot post profiles and API (§3) | F6 | high for the shots | hours + camera work | visual | yes |
| 8 | Real tiers (MSAA on High; TAA only after a smear test) | F12 | medium | 1 day | visual + build owner | Web keeps MSAA |
| 9 | Box-projected room probes with blending, shader defines | F4 | medium-high; L–M per pixel plus atlas memory | 1–2 days | visual + map | no (Web: step 0 only) |
| 10 | Decals (water damage, scuffs, footprints, notices) | — | medium-high (breaks repetition) | 2–3 days | visual (+ map hooks) | Screen Space only |
| 11 | Visible light: depth-faded beams and dust everywhere; ray-marched scattering on desktop (Render Graph) | — | medium / high | hours / L | visual | beams yes, scattering no |

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
