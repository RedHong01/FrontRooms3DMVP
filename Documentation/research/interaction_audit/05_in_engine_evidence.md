# 05 — In-engine evidence (frames, material dumps, pipeline state)

Status: DONE (2026-10-02, about 21:15). 81 frames captured; 55 copied here as PNG.

This file is the in-engine part of the interaction audit. It shows, frame by frame, what
the game actually draws when a player breaks a window, finds a key, opens a locked door,
and when the Relay breaks a door. It also records the glass material's real runtime values
and the pipeline state as the game sees it. Code claims cite `file:line` in the real
project as of 21:10. Unity package claims cite the package source in `Library/PackageCache`.
Anything I did not confirm is marked UNVERIFIED.

---

## 0. Short answer

1. **There are no shots.** No interaction moves the camera, plays an animation on a
   hand or key, or spawns any effect. Each one is a state change plus a HUD text line.
   - Glass: holding E for 1 s deletes the pane object in one frame. There are no cracks
     while you hold, no shards, no particles, no decal, and no camera kick
     (frames 14 → 16 → 18 → 20).
   - Key: walking within 0.9 m deletes the floating yellow box. There is no prompt, no
     reach and no hand. The camera does not move (frames 52 → 54 → 55 → 56).
   - Unlocking a door with a key looks exactly like a normal door opening: a 0.55 s hinge
     swing. Nothing touches the lock or the handle, and the door has no handle (frames
     58–62 against 40–43).
2. **In the shipped profile, keys do nothing.** `doorsNeedKeys: 0`
   (`Assets/Levels/FrontRoomsLevel0.asset:47`), so no door is ever locked. I forced it on
   to film the "locked" moment.
3. **The glass reads as a milky teal veil, not as glass.** It is URP/Lit Transparent
   with a light blue-grey base colour at alpha 0.28 (`FrontRoomsMapWorld.cs:1659`). That
   draws a *lit, light-coloured layer* over whatever is behind it. Nothing nearby can be
   reflected: there are **0 reflection probes** at runtime and no skybox, so reflections
   come from Unity's built-in default cube at intensity 0.3 (see §A). At grazing angles
   the panes turn flat pale cyan (frames 04, 23, 25).
4. A local reflection probe alone **does not fix it** (experiment frames 07, 10). A
   clear-glass setting (dark base colour, low alpha) plus a probe makes the pane
   **invisible** instead (frames 08, 09, 11). With this lighting, the pane needs surface
   detail to read as glass. That is my inference from the frames, not a measured result.
5. **The pipeline settings are not the main problem.** The game runs URP Forward+, HDR,
   4x MSAA, render scale 1, SSAO, soft shadows, a 2048/4096 shadow atlas, and a full film
   post stack. The low-end look comes from **content**: primitive-cube keys, doors and
   panes, a primitive-capsule Relay, and no probes, decals or effects. It also comes from
   a 9-shadowed-light budget that leaves most surfaces unshadowed.
6. The playtest autopilot's look-around and Relay shots (`Verification/main-autopilot`)
   are made with `Camera.CopyFrom`. That copy does not carry URP's camera data, so those
   frames have **no tonemapping, grade or grain**. Do not judge the look from them
   (frame 36 against 35).

---

## 1. How the frames were made

- **Where:** a private clone of the project (Assets, Packages, ProjectSettings and Library
  copied at 20:34), opened in Unity 6000.3.10f1 in batch mode. The real project was not
  opened and nothing in it was changed except this folder.
- **Harness:** `harness/FrontRoomsInteractionAudit.cs.txt` (a copy of the clone's
  `Assets/Editor/Audit/FrontRoomsInteractionAudit.cs`). It follows the playtest's pattern:
  enter Play on `Assets/Scenes/FrontRooms3D.unity` and re-attach after the domain reload.
  Then it presses "Space" through the game's own `RequestTitleStart` and drives the
  game's own APIs:
  - `FrontRoomsMapWorld.Hold` and `ReleaseHold` for glass;
  - `FrontRoomsMapWorld.Use` for doors;
  - `CollectKeys`, by moving the player within 0.9 m of the key;
  - `FrontRoomsMapHunter.DebugPlace` and `Noise` for the Relay.

  It moves the player by setting the `playerRoot` position and the game's own `yaw` and
  `pitch` fields, so the game's camera rig places the eye.
- **Camera:** the game's own `First-person camera` with its own URP camera data
  (post on, dithering on), rendered to a 1920x1080 sRGB target with **4x MSAA**. With a
  target texture, URP takes the MSAA count from the texture
  (`Library/PackageCache/com.unity.render-pipelines.universal@37e0d4fc2503/Runtime/UniversalRenderPipeline.cs:1409`),
  so 4 samples matches the pipeline's 4x setting.
- **Time:** after the run starts, `Time.captureDeltaTime = 1/60`. Game time then advances
  exactly 1/60 s per frame, and "+0.25 s" means 15 game frames. PNG encoding cannot skip
  animation.
- **Seed:** `Random.InitState(4242)` before Space gives run seed 516574485 every time,
  with the map root at (-576, 0, -576). Four runs reproduced the same map.
- **HUD:** the game's HUD is a Screen Space Overlay canvas (`FrontRooms3DGame.cs:1338`).
  URP does not draw overlay UI into a camera target texture. For the frames marked
  `_hud`, the harness switches that canvas to Screen Space Camera for one render and then
  back. In those frames the post stack (grain, vignette, chromatic aberration) also
  touches the HUD, which the real game does not do.
- **What the harness changed in the game's state (on the clone, at runtime only):**
  1. `hunterTuning.releaseDelaySeconds` set to 1e6, so the Relay stays dormant until §E.
  2. `FrontRoomsMapWorld.doorsNeedKeys` forced **true** for the locked and key-unlock
     frames only. The shipped value is false (§C).
  3. For the mid-hold frame, `Hold(pane, 0.5)` is called once, right before the render.
     The game's `UpdateAim` resets the hold every frame E is not held
     (`FrontRooms3DGame.cs:956-968`), and batch mode has no keyboard. The HUD hold bar in
     frame 14 is set by the harness to the width `UpdateHud` would draw
     (`FrontRooms3DGame.cs:1533`).
  4. Experiments marked **EXPERIMENT** (a reflection probe, a clear-glass material, the
     Prop_Glass material) are not in the game. They show what a change would do.
- **Version note:** after the clone was taken, `FrontRooms3DGame.cs`,
  `FrontRoomsMapWorld.cs` and `FrontRoomsRelayRig.cs` changed in the real project
  (20:37–20:45). I diffed them. The game and map changes touch streaming, the start area
  and furnishing. None of the interaction code cited here changed. The Relay rig did
  change: it gained `DoorBlow` and `Step` hooks and new poses, and is a "squeezed-giant"
  rig work in progress. **The Relay frames in §E show the older rig.**

---

## A. Pipeline state at runtime (as the game sees it in Play)

Full dump: [`images/runtime_dump.txt`](images/runtime_dump.txt).

| Item | Runtime value | Source |
|---|---|---|
| Active build target (Library of the copied project) | StandaloneOSX | runtime `EditorUserBuildSettings.activeBuildTarget` |
| Quality level in editor | 3 "High"; **all six levels use the same `FrontRooms_URP` asset** | runtime `QualitySettings.GetRenderPipelineAssetAt`; `ProjectSettings/QualitySettings.asset` |
| Render path | URP Forward+ | `Assets/Settings/FrontRooms_URP_Renderer.asset:50` |
| HDR | on; colour buffer `_32Bits` (R11G11B10); grading mode HDR, LUT 32 | `FrontRooms_URP.asset:26-27` |
| MSAA / AA | 4x MSAA; camera post-AA None | `FrontRooms_URP.asset:28`; `FrontRoomsPostStack.cs:72` |
| Render scale | 1.0 | `FrontRooms_URP.asset:29` |
| Opaque texture (needed for refraction) | **off** | `FrontRooms_URP.asset:23` |
| Depth texture | on | runtime |
| Shadows | main 2048, additional atlas 4096, distance 40 m, 2 cascades, soft (quality "High") | `FrontRooms_URP.asset:46,50,57` |
| Shadowed lights alive | **9** of 24 enabled lights (1,582 Light components exist; most are switched off by distance) | runtime count |
| Lamp shadows | about one lamp in three, within 9 m (`shadowRadius`) | `FrontRoomsMapWorld.cs:1062,1069`; `FrontRoomsLevelProfile.cs:37` |
| Renderer features | SSAO only (blue noise, depth+normals, intensity 1.6, radius 0.45) | `FrontRooms_URP_Renderer.asset:27,67` |
| Screen-space reflections | none in the renderer feature list | runtime feature list |
| **Reflection probes** | **0** (FindObjectsByType, inactive included) | runtime |
| Probe blending / box projection | both **off** | `FrontRooms_URP.asset:54-55` |
| Skybox | **none**; default reflection = "Default-Skybox-Cubemap" 128², intensity **0.3** | `Assets/Scenes/FrontRooms3D.unity:29,38`; `FrontRoomsLook.cs:20,30` |
| Lightmaps / light probes | 0 / 0 (everything is realtime) | runtime |
| Post (global volume) | ACES; bloom (threshold 1.05, intensity 0.55); white balance; lift-gamma-gain; vignette 0.26; film grain 0.22; chromatic aberration 0.06; lens distortion -0.04 | runtime dump of `Resources/Rendering/FrontRoomsPost` |
| Post (Office) | 44 local volumes in view distance; Office grade (saturation -22, tint -14, thin grain) | runtime dump |
| Camera | FOV 76, near 0.06, far 46 m (streamed sight distance), HDR on, MSAA on | runtime |

Two notes from the build script, not tested in a build (UNVERIFIED effect):
- `BuildMac()` sets `GraphicsSettings.defaultRenderPipeline = null` and
  `QualitySettings.renderPipeline = null` before building
  (`Assets/Editor/FrontRooms3DBuild.cs:61-62`). The per-level assets still point at URP,
  so the player probably still runs URP. Someone should check this in a built player.
- `BuildWebGL()` forces quality level 3 (`FrontRooms3DBuild.cs:146`). All levels share one
  URP asset, so this does not lower any setting. The WebGL build in `Builds/WebGL` is from
  Oct 1, 17:49, older than today's code.

---

## B. Glass

### B1. What the glass is, at runtime

The map's pane is a **primitive cube** of 1.40 x 1.65 x 0.03 m
(`FrontRoomsMapWorld.cs:900-905`, runtime scale (1.40, 1.65, 0.03), mesh "Cube", 24 verts).
It has a BoxCollider, `shadowCastingMode On` and `reflectionProbeUsage BlendProbes`.
Its material is built in code (`FrontRoomsMapWorld.cs:1659`, `1662-1678`). Runtime dump:

| Property | Map glass "Map test / glass" | Project `Prop_Glass` (props) |
|---|---|---|
| Shader | URP/Lit, Transparent, queue 3000 | URP/Lit, Transparent, queue 3000 |
| `_BaseColor` | (0.75, 0.85, 0.88, **0.28**) | (0.82, 0.88, 0.88, **0.16**) |
| `_Smoothness` / `_Metallic` | 0.90 / 0 | 0.92 / 0 |
| Blend | `_SrcBlend` 1 (One), `_DstBlend` 10 (OneMinusSrcAlpha), keyword `_ALPHAPREMULTIPLY_ON`, `_BlendModePreserveSpecular` 1 | the same (the saved asset was re-validated to this; `Assets/Resources/Surfaces/Prop_Glass.mat:15-16,116`), although `EnsureGlassMaterials` writes SrcAlpha (`FrontRoomsRenderSetup.cs:414`) |
| Passes | ShadowCaster **on**, DepthOnly on | ShadowCaster **off**, DepthOnly off (`Prop_Glass.mat:26-27`) |
| Textures (normal, smudge, roughness) | none | none |
| Environment reflections | on, but no probe exists (§A) | same |

The blend state is URP's standard "Alpha, Preserve Specular" setup
(`.../Editor/ShaderGUI/BaseShaderGUI.cs:1058-1063,1098-1102,1114`; default on,
`.../Shaders/Lit.shader:57`). So **the blend is not wrong**. What is wrong is what gets
blended. A light blue-grey diffuse colour at 28 % alpha is lit by the troffers and laid
over the far room as a pale veil. Real clear glass has almost no diffuse colour; it shows
reflections and a slight darkening. Meanwhile the only reflection source is a generic sky
cube at 0.3, so the pane shows no reflection of the room, the lamps or the player's side.

### B2. Level 0 window, before / during / after (camera on the Low side, looking into a Tall hall)

| Frame | What it shows | What is missing |
|---|---|---|
| ![](images/02_window_L0_intact_1.5m.png) `02` intact, 1.5 m, straight on | The far hall seen through a cool grey-teal haze, visibly lighter and cooler than the same view with the pane gone (frame 18). Frame, sill and reveal are clean boxes. | No reflection of this room or the troffer behind the camera. No smudge or dust. No visible pane edge or thickness. No mullion, sticker or wired glass. |
| ![](images/03_window_L0_intact_1.5m_hud.png) `03` same, with HUD | Prompt `HOLD E · BREAK GLASS`. | — |
| ![](images/04_window_L0_intact_oblique.png) `04` intact, ~50° | The veil gets lighter and greyer. Other windows down the hall read as flat cyan rectangles. A small lamp glint shows at the top-right corner of the frame. | Still no image of the room in the glass. |
| ![](images/06_window_L0_intact_steep.png) `06` intact, ~60° | A pale milky sheet over the far wall. | Same. |
| ![](images/05_window_L0_intact_0.7m.png) `05` intact, 0.7 m | The same flat veil up close. No surface texture at any distance. | Smudges or prints are what would sell glass at this distance. |
| ![](images/14_window_L0_hold_0.5s_hud.png) `14` mid hold (0.5 s), HUD | The world image is pixel-for-pixel the intact frame. Only the HUD hold bar is half full. | No crack growth, no strain, no shake. Nothing tells the player the glass is about to go except a 120 px bar. |
| ![](images/16_window_L0_break_next_frame.png) `16` first frame after the break | The pane is simply gone (the object is destroyed in `Hold`, `FrontRoomsMapWorld.cs:1570`). | No shards, no burst, no dust, no flash of light, no camera kick. |
| ![](images/17_window_L0_break_next_frame_hud.png) `17` same, HUD | Flash card: `GLASS BROKEN / WALK INTO THE FRAME TO CLIMB THROUGH` (`FrontRooms3DGame.cs:785`). | The text explains what the picture fails to show. |
| ![](images/18_window_L0_break_%2B0.25s.png) `18` +0.25 s | A clean empty frame. | No falling pieces. |
| ![](images/19_window_L0_after_1s.png) `19` +1 s | Identical to 18. | No shards on the sill or floor, no jagged remains in the frame. |
| ![](images/20_window_L0_after_1s_oblique.png) `20` +1 s, oblique | The sill and the floor below are clean. Other windows in the hall still read as flat cyan. | Nothing persists. Runtime check: 0 ParticleSystems and 0 DecalProjectors in the scene. Within 1.5 m there is only the shell collider, a zone-volume trigger and the player. |

### B3. Office window (camera on the Office side, looking into a Level 0 Tall hall)

| Frame | What it shows |
|---|---|
| ![](images/21_window_Office_intact_1.5m.png) `21` intact, 1.5 m | Under the Office grade, the far hall turns cyan-green. The pane adds the same pale veil. |
| ![](images/23_window_Office_intact_oblique.png) `23` ~50° | The windows on the far wall show as **flat pale-cyan rectangles**. That is the default sky cube reflected at a steep angle: a sky inside a windowless office. |
| ![](images/25_window_Office_intact_steep.png) `25` ~60° | The same: a uniform pale sheet. Nothing of the office is reflected. |
| ![](images/27_window_Office_hold_0.5s_hud.png) `27` mid hold, HUD | Only the bar changes. |
| ![](images/29_window_Office_break_next_frame.png) `29` next frame | The pane is gone, with no debris. |
| ![](images/33_window_Office_after_1s_oblique.png) `33` +1 s, oblique | An empty frame, clean sill. |

### B4. Experiments (not in the game; Level 0 window, same view as 04 or 06)

| Frame | Change | Result |
|---|---|---|
| ![](images/07_window_L0_EXPERIMENT_with_probe.png) `07` | + one realtime ReflectionProbe (256 px) at the window | Almost no visible change from 04: at 50° a dielectric reflects only a few percent. |
| ![](images/10_window_L0_EXPERIMENT_game_glass_probe_steep.png) `10` | game glass + probe, ~60° | Close to 06. The veil still dominates. |
| ![](images/08_window_L0_EXPERIMENT_clear_glass_probe.png) `08` / ![](images/09_window_L0_EXPERIMENT_clear_glass_probe_steep.png) `09` / ![](images/11_window_L0_EXPERIMENT_clear_glass_probe_1.5m.png) `11` | Same shader and blend, base colour (0.02, 0.025, 0.025, 0.12), smoothness 0.96, + probe | The veil is gone and the far room shows its true colour. But the pane is now **invisible**, even at 60°: it reads as an empty opening. |
| ![](images/12_window_L0_EXPERIMENT_prop_glass.png) `12` | The pane drawn with the project's `Prop_Glass` | A thinner veil (alpha 0.16). Same problem, less of it. |

Reading the experiments (my inference): the material values are only half the story. In
these dim, evenly lit rooms, physically clear glass is nearly invisible. Glass becomes
legible through surface detail that catches light: smudges, dust and roughness variation,
a visible edge, the frame's shadow, and bright lamp reflections. It also needs something
to reflect: a local probe (box projection is off in the asset) or a screen-space
reflection, which URP does not have here. Section 02 (`02_glass_and_breakables.md`)
should give the reference-backed answer. This section only shows that neither "tint
more" nor "add a probe" works by itself.

---

## C. Doors

### C1. A door opened normally (doorsNeedKeys false, as shipped)

Door between (274, 189) and (273, 189): Level 0 Standard to Low. The leaf is a primitive
cube of 0.05 x 2.08 x 0.98 m (`FrontRoomsMapWorld.cs:878`) in `Door_Veneer`. It has no
handle, no lock and no hinge hardware.

| t | Frame | door.progress / hinge |
|---|---|---|
| before | ![](images/39_door_normal_before_hud.png) `39` prompt `E · OPEN DOOR` | 0 |
| 0.00 s | ![](images/40_door_normal_t0000ms.png) `40` the press frame: nothing moves yet | 0 |
| 0.25 s | ![](images/41_door_normal_t0250ms.png) `41` | 0.455 (about 44°) |
| 0.50 s | ![](images/42_door_normal_t0500ms.png) `42` | 0.909 |
| 0.75 s | ![](images/43_door_normal_t0750ms.png) `43` fully open (95°); 1.0–1.5 s identical | 1.0 |

The swing is a smoothstep over 0.55 s (`FrontRoomsMapWorld.cs:1587-1597`). The camera
does not move, nothing appears in view, and there is no push.

### C2. The locked door and the "needs key" moment (doorsNeedKeys forced on)

Door between (273, 188) and (273, 189), in key zone (34, 23).

| Frame | What it shows |
|---|---|
| ![](images/48_door_locked_before_hud.png) `48` | Prompt `LOCKED · NEEDS THIS ZONE'S KEY` (`FrontRoomsMapWorld.cs:1512`). The door looks the same as an unlocked one: no lock, no chain, no sign. |
| ![](images/50_door_locked_after_use_hud.png) `50` the frame after pressing E | Nothing changes. `DoorLocked` is raised (`FrontRoomsMapWorld.cs:1527`). Only the sound layer listens to it (`Assets/Scripts/Audio/FrontRoomsSoundDirector.cs:393,472`). There is no rattle, no handle jiggle, no camera nudge, and no HUD flash. |
| ![](images/51_door_locked_0.5s.png) `51` +0.5 s | Unchanged. |

In the shipped game this state never happens (`FrontRoomsLevel0.asset:47`).

### C3. Unlocking and opening with the key (key for zone (34, 23) held)

| t | Frame | progress |
|---|---|---|
| before | ![](images/58_door_key_before_hud.png) `58` prompt `E · OPEN DOOR`; key panel `LEVEL 0 KEY` bottom left | 0 |
| 0.00 s | ![](images/59_door_key_open_t0000ms.png) `59` | 0 |
| 0.25 s | ![](images/60_door_key_open_t0250ms.png) `60` | 0.455 |
| 0.50 s | ![](images/61_door_key_open_t0500ms.png) `61` | 0.909 |
| 0.75 s | ![](images/62_door_key_open_t0750ms.png) `62` open; 1.0–1.5 s identical | 1.0 |

**This is the same animation as C1, frame for frame.** `Use` only checks `HasKeyHere()`
and calls the same `SetDoor` (`FrontRoomsMapWorld.cs:1522-1531`). The key is not
consumed or shown, there is no keyhole, and the camera does not push in. The shot Red
describes (camera moves to the lock, the key turns, the door opens) does not exist in any
form.

---

## D. Key on the floor, and pickup

The key for zone (34, 23) is at (256.5, 1.05, -19.5). It is a primitive cube of
0.32 x 0.12 x 0.12 m with no collider, at 1.05 m height in the middle of a cell, spinning
at 90°/s (`FrontRoomsMapWorld.cs:730-737,1609`). Its material is URP/Lit, base
(0.96, 0.87, 0.23), smoothness 0.4, emission (0.77, 0.70, 0.18)
(`FrontRoomsMapWorld.cs:1658`). One key object stood at that spot, so there were no
duplicates.

| Frame | What it shows | What is missing |
|---|---|---|
| ![](images/52_key_2m.png) `52` from 2 m | A pale yellow brick hanging in an empty room. With no shadow below it, it reads as lying on the floor. The emission washes it toward cream after ACES. | It does not look like a key: no bow, no blade, no ring or tag. It does not sit on furniture, it has no glint, and nothing draws the eye to it. |
| ![](images/54_key_1.0m.png) `54` from 1.0 m (closest a player gets; pickup radius 0.9 m) | The same brick, larger, still unlit-looking. | — |
| ![](images/55_key_pickup_frame.png) `55` pickup frame | The key is gone. | No reach, hand, or move-to-camera; no sound-sync visual. |
| ![](images/56_key_pickup_%2B2f_hud.png) `56` +2 frames, HUD | Flash card `KEY / OPENS THIS ZONE'S DOORS` and the `LEVEL 0 KEY` panel (`FrontRooms3DGame.cs:789-793`). The HUD updates one frame after the `KeyTaken` event. | The pickup is automatic, by walking near it (`FrontRoomsMapWorld.cs:1611`). There is no "E · take key" prompt. |

---

## E. The Relay breaks a door

Setup (harness): the Relay is placed released, in the cell beyond a closed door, with
`DebugPlace`, then given a `Noise` at the player. The player stands 2.2 m back on the
other side. The Relay walked to the door and entered `BreakDoor` 0.6 s later. It struck
for `breakDoorSeconds` 2.5 (`Assets/Scripts/FrontRoomsHunter.cs:21`; `TickBreak` at
`Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs:862-879`), then `BreakDoor` swung the leaf open at 0.18 s speed
(`FrontRoomsMapWorld.cs:1003,1593`). These frames show the **older rig** (see §1).

| Frame | What it shows | What is missing |
|---|---|---|
| ![](images/66_relay_break_t0000ms.png) `66` BreakDoor t=0 (player view) | A closed door. | — |
| ![](images/71_relay_break_t1000ms_hud.png) `71` t=1.0 s, HUD | The door is perfectly still. The HUD shows `RELAY 3 M` and still offers `E · OPEN DOOR` on the door being broken. | No leaf jolt, no frame shake, no dust or splinters, no light leaking through. The blows exist only as sound (`DoorBlow` → `FoleyDoorBreak`, `FrontRooms3DGame.cs:590`). |
| ![](images/74_relay_break_t2500ms.png) `74` t=2.5 s | Unchanged. | — |
| ![](images/70_relay_break_witness_t1000ms.png) `70` NON-PLAYER witness view, t=1.0 s | The rig is primitive capsules and boxes (`FrontRoomsRelayRig.cs:234-264` in today's file). In the break pose the torso floats above the leg pieces with a visible gap. The yellow hand boxes do not touch the door. | Contact, impact poses and readable anatomy. |
| ![](images/75_relay_broken_%2B0000ms.png) `75` → ![](images/76_relay_broken_%2B0100ms.png) `76` → ![](images/78_relay_broken_%2B0250ms.png) `78` | Over 0.25 s the intact leaf swings fully open (progress 0.09 → 0.65 → 1.0) and the Relay is in the doorway. | No splintering, no broken hinge, no leaf on the floor, no debris, no camera shake. The "broken" door is just an open door that will not close. |
| ![](images/77_relay_broken_witness.png) `77` witness | The leaf swung away on its hinge. | — |
| ![](images/80_relay_broken_%2B1000ms.png) `80` +1.0 s | Caught: the capsule torso fills the screen and its polygon edges are visible. | — |

---

## F. Representative frames for the render-quality review

| Frame | Notes |
|---|---|
| ![](images/00_start_room_view.png) `00` title stream room right after Space | This is the strongest-looking space: authored doors with handles, a lens on the ceiling. |
| ![](images/01_rep_L0.png) `01` Level 0 corridor (cell 264,200) | The chevron paper and carpet hold up. The geometry is boxes: no baseboard wear, outlets, vents, sprinkler heads or fixture housings. Only the troffer lens is a flat bright quad. Walls have no contact shadows except SSAO. |
| ![](images/34_rep_Office.png) `34` Office corridor | Even, flat light. The Office grade makes everything cyan-green. On the lens edges there is visible stair-stepping (UNVERIFIED cause: possibly MSAA resolving very bright HDR edges before tonemapping). |
| ![](images/35_rep_Office_b.png) `35` Office cubicles | The prop kit is the most detailed content in the game. |
| ![](images/36_rep_Office_b_AUTOPILOT_STYLE_camera.png) `36` same view through `Camera.CopyFrom` | This is how `AutopilotLookAround` and `AutopilotCaptureRelay` render (`FrontRooms3DGame.cs:1895,1920,1937`). A new camera's URP data defaults to `renderPostProcessing = false` (`.../Runtime/UniversalAdditionalCameraData.cs:466`), so there is no ACES, grade or grain, and the picture is warmer and brighter. The autopilot also renders at 1600x900 with no MSAA (`FrontRooms3DGame.cs:1959`). |
| ![](images/37_rep_Dark.png) `37` darkest corridor nearby (dead lamps) | The nearest lamp is dead, so the foreground drops to dark olive, but the black level stays lifted (grade lift, `FrontRoomsPost`). The lit cells beyond are flat and evenly lit. Fog (exp², 0.014) fades the distance. |

---

## G. Frame time

Measured on the clone in the editor, Apple M3 Max, Metal:
- Game camera, 1920x1080, 4x MSAA, full post. Each sample is one render plus a 1-pixel
  readback, which forces a GPU sync. Run 4: **median 13.9 ms** (min 13.0, max 21.8,
  20 samples). Run 2: 15.4 ms. Run 1: 18.1 ms.
- The player loop in batch mode has a median of 16.69 ms. That is only the
  `targetFrameRate 60` / vSync cap (`FrontRooms3DGame.cs:291`), not a cost. Batch mode
  draws no game view.
- Not measured: a built player, WebGL, or GPU-only time. Inference, UNVERIFIED: about
  14 ms on an M3 Max at 1080p leaves little headroom for a WebGL build on ordinary
  laptops. More effects should be budgeted against the Mac build, or the WebGL target
  should get its own lower URP asset.

---

## H. What could not be captured, and limits

- **The real start door opening.** In batch mode the stream's terminal door did not open
  within 8 s, because the player was not walking to it. Frame 00 is the stream room at
  handoff, not the door.
- **An ~80° grazing view of the glass.** The pane sits in the middle of the wall
  thickness, so at very low angles the reveal hides it. Two attempts filmed wallpaper.
  The steepest usable view is about 60° (frames 06, 25).
- **Glass shadows.** The pane is set to cast shadows (ShadowCaster pass on, renderer
  `shadowCastingMode On`). I did not find a frame that shows whether it darkens the
  floor (UNVERIFIED).
- **The HUD** in `_hud` frames is the real HUD, drawn through the camera (see §1), so it
  carries grain and vignette that the overlay does not have in the game.
- **The hold-to-break bar** in frames 14 and 27 is drawn by the harness at the game's
  width. With a real key held, `UpdateHud` draws it.
- **The Relay frames use the 20:34 rig.** The real project's rig changed at 20:39.
- **Frame counts:** 81 PNGs are in the clone at
  `/private/tmp/claude-501/.../scratchpad/proj_audit/Verification/interaction_audit/`
  (temporary). The 55 most useful are copied to `images/` (about 124 MB). The full log
  is [`images/audit_log.txt`](images/audit_log.txt), and the per-frame camera
  position, HUD text and notes are in [`images/frames.txt`](images/frames.txt).

## I. Reproduce

Copy `harness/FrontRoomsInteractionAudit.cs.txt` to `Assets/Editor/Audit/FrontRoomsInteractionAudit.cs`
**in a clone, never in the real project**. Then run:

```
/Applications/Unity/Hub/Editor/6000.3.10f1/Unity.app/Contents/MacOS/Unity -batchmode \
  -projectPath <clone> -executeMethod FrontRoomsInteractionAudit.RunBatch -logFile <log>
```

It writes `Verification/interaction_audit/*.png`, `frames.txt`, `runtime_dump.txt` and
`audit_log.txt`, then quits (about 2.5 minutes after compile).
