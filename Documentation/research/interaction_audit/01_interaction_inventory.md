# 01 — Interaction inventory (from code)

Date: 2026-10-02. Status: COMPLETE (code read; nothing was run in Unity).

Scope: every player-facing interaction and moment in FrontRooms, what each channel does today, and
the gaps against a AAA first-person horror bar, including Red's two examples (a key-use close-up and
a glass shatter).

Citation rule: `file:line`. Paths are relative to `Frontrooms3D/Assets/Scripts/` unless they start
with `Assets/`, `ProjectSettings/` or `Packages/`. "FMOD" means the sound layer in `Audio/`. "Legacy"
means the Unity AudioSource sounds made in `FrontRooms3DGame.cs`.

---

## 0. Verdict

Every interaction in the game is "press or hold E, then the world changes state in one frame". No
interaction has a shot. Specifically:

- **There is no first-person body.** Nothing is parented to the camera except the hum AudioSource
  (`FrontRooms3DGame.cs:1013`). No hands, no viewmodel, no held key.
- **The camera has no language.** Its local position is fixed at eye height and is only changed by
  the window climb (`FrontRooms3DGame.cs:561, 919, 923`). FOV is a constant 76
  (`FrontRooms3DGame.cs:226`). No head-bob, sprint FOV, shake, impulse or scripted shot exists
  anywhere in `Assets/Scripts`.
- **Key use has no code path at all.** With a key, a door opens exactly like a door without one
  (`FrontRoomsMap/FrontRoomsMapWorld.cs:1513-1523`). The shipped level profile has
  `doorsNeedKeys: 0` (`Assets/Levels/FrontRoomsLevel0.asset:47`), so in the real game no door is
  ever locked and keys do nothing.
- **Glass does not break. It is deleted.** After a 1 s hold the pane object is destroyed in one
  frame (`FrontRoomsMap/FrontRoomsMapWorld.cs:1559-1562`). No crack, shards, physics, particles or
  decal follow.
- **The project cannot currently make particles or play animation clips.** The particle-system,
  animation, Timeline, Cinemachine and VFX Graph packages are not installed
  (`Packages/manifest.json`, `Packages/packages-lock.json`, section 3).
- **Sound is ahead of picture.** The FMOD layer already has events for glass stress, cracks,
  shatter, key pickup, locked door, door blows and break, the caught moment and the climb
  (`Audio/FrontRoomsSoundDirector.cs:421-493`). For some moments the sound now describes
  something the screen does not show (section 4).

---

## 1. Global facts (true for every interaction)

| Topic | What the code does | Cite |
|---|---|---|
| Player body | A `CharacterController` is created at runtime when the run starts: height 1.75, radius 0.3, step 0.3. The camera is parented to it at (0, 1.62, 0). | `FrontRooms3DGame.cs:551-562`; `FrontRoomsMap/FrontRoomsModuleUnits.cs:90` |
| Look | Raw mouse × 2.1, pitch clamped to ±75°. No smoothing or acceleration. Yaw goes on the body and pitch on the camera, both written **every frame**. | `FrontRooms3DGame.cs:806-807, 821-822` |
| Move | Walk 3.2 m/s and run 5.5 m/s, applied instantly (no acceleration curve). Gravity is applied, with no landing response. | `FrontRooms3DGame.cs:146, 836-839` |
| Camera lens | FOV 76, near 0.06, far 80 (the far plane is later the map's sight distance). HDR and MSAA on. Post on, with camera AA off. | `FrontRooms3DGame.cs:226-229, 712`; `Rendering/FrontRoomsPostStack.cs:64-74`; scene `Assets/Scenes/FrontRooms3D.unity:320` |
| Camera motion | No head-bob, sway, lean, shake, FOV change or recoil. The only camera offset is the climb duck. | `FrontRooms3DGame.cs:919, 923` (only writers of `cam.transform.localPosition` in play) |
| Hands/body | None. The only thing on the camera is the hum AudioSource. The FMOD director also adds a StudioListener to the AudioListener object. | `FrontRooms3DGame.cs:1013`; `Audio/FrontRoomsSoundDirector.cs:157-164` |
| Interaction ray | One ray from the camera, 2.4 m long. The prompt comes from `MapWorld.Describe`. | `FrontRooms3DGame.cs:149, 933-936`; `FrontRoomsMap/FrontRoomsMapWorld.cs:1494-1511` |
| Aim feedback | Prompt text (20 px) 44 px below the crosshair, plus a 120×4 px hold bar. The aimed object gets no outline or highlight, and the crosshair sprite never changes. | `FrontRooms3DGame.cs:1367-1378, 1524-1529` |
| Post | One static global volume (Resources/Rendering/FrontRoomsPost), plus static Office zone volumes with a 2.5 m blend. **Nothing drives post from gameplay.** No API for pulses exists. | `Rendering/FrontRoomsPostStack.cs:15-62`; `FrontRoomsMap/FrontRoomsMapWorld.cs:1413` |
| VFX | No ParticleSystem, VisualEffect, DecalProjector, Rigidbody, AddForce, Animator, Timeline or Cinemachine use in `Assets/Scripts` (grep returned nothing). | grep over `Assets/Scripts` |
| Audio routing | When FMOD is ready, the director sets `AudioListener.volume = 0`. That **mutes every legacy Unity sound**: the legacy door hinge, the glass break, the caught clip and the title door clips. If FMOD fails, the legacy sounds play and the FMOD layer goes silent. | `Audio/FrontRoomsSoundDirector.cs:127-133`; `Audio/FrontRoomsFmod.cs:43-56` |
| Hunter tuning (scene) | Release 3 s, hunt 2.6 m/s, chase 4.2 m/s, sight 12 m, catch 0.7 m, break-door 2.5 s, sprint noise 26 m, door noise 14 m. Hearing ×1.4 is the code default (not serialized). | `Assets/Scenes/FrontRooms3D.unity:1011-1023`; `FrontRoomsHunter.cs:16-32` |
| Duplicate controller | The map test scene's walker duplicates the whole E / hold-E loop (with FOV 72). Any shot system has to be shared, or it will drift between the two. | `FrontRoomsMap/FrontRoomsMapWalker.cs:50, 119-138` |

---

## 2. Interaction tables

Each table uses the same rows. "—" means nothing happens on that channel.

### I1. Title sequence (watching, before Space)

| Channel | Today |
|---|---|
| Trigger | Scene start. `Phase.Title`. `FrontRooms3DGame.cs:319` |
| Camera | Crawls forward at 1.15 m/s on +Z. No rotation. `FrontRoomsRoomStream.cs:41, 661-666` |
| Body/hands | — (there is no body yet) |
| Object | The streamed rooms' double doors open by proximity (within 4 m) over 0.9 s with smoothstep, to 88°. The doors have bar handles and kick plates. `FrontRoomsRoomStream.cs:49, 737-765, 1261-1271, 1766-1781` |
| VFX | Volumetric beam meshes under the fixtures. Lamps strike and flicker per fixture. `FrontRoomsRoomStream.cs:269-283, 794-803` |
| Post | Static film look. |
| SFX | FMOD: Automatic-mode door sound (AutoOperator, swing loop, stop) on the "double door … hinge" transforms, plus room tone. Legacy (muted under FMOD): latch .42, creak .78 and travel .42 one-shots. `Audio/FrontRoomsSoundDirector.cs:203-204`; `Audio/FrontRoomsDoorSound.cs:84-89`; `FrontRoomsRoomStream.cs:1750-1764` |
| UI | The vector wordmark fades in from 0.7 s over 4 s. The two trailing S forms slide, keyed to the first door's progress. `FrontRoomsRoomStream.cs:52-53, 434`; `FrontRooms3DGame.cs:412-460` |
| Input lock | Only Space or Return does anything. `FrontRooms3DGame.cs:1482` |
| Timing | Loops forever until Space. |

### I2. Title → play handoff (Space)

The code comments still say "noclip" (`FrontRoomsMap/FrontRoomsMapWorld.cs:10-11`), but no noclip
or fall exists. The player takes over in place.

| Channel | Today |
|---|---|
| Trigger | Space or Return. `StartRunInPlace`. `FrontRooms3DGame.cs:488-599` |
| Camera | Re-parented to a new player body at the same spot, with rotation reset to identity (pitch and yaw 0). The title's forward drift becomes a "glide" that eases to 0 over 0.6 s. Mouse input is ignored for 2 frames. `FrontRooms3DGame.cs:549-570, 840` |
| Body/hands | A body capsule is created, with no visible body. |
| Object | The stream ends at the first shut door. The map is built behind it. `FrontRooms3DGame.cs:516-544` |
| VFX/Post | — |
| SFX | — (no handoff cue) |
| UI | The wordmark fades out over 0.55 s. The gameplay HUD fades in over 0.9 s. A calm hint shows for 9 s: "Shift to sprint. About 5 seconds, and it hears every step." `FrontRooms3DGame.cs:102, 140-142, 405-410, 1506, 1522` |
| Input lock | None after 2 frames. |
| Timing | Instant takeover. The HUD is fully visible at 0.9 s. |

### I3. Start door (stream → maze), and "the way back shuts"

| Channel | Today |
|---|---|
| Trigger | Proximity, within 4 m from either side. **Not E.** It is held shut until the map round it is built, for at most 3 s after Space. `FrontRooms3DGame.cs:716-728`; `FrontRoomsRoomStream.cs:733-747` |
| Camera | — |
| Object | Double doors open over 0.9 s. When the player is out of the start area and ≥4 m from the door, it swings shut over 0.9 s and never opens again. `FrontRooms3DGame.cs:733-734`; `FrontRoomsRoomStream.cs:575-585, 778-783` |
| VFX | The maze lamps by the door rise over 0.6 s. After the door shuts, the stream lamps fade over 1.2 s and are then destroyed. `FrontRooms3DGame.cs:117, 732, 740-758` |
| SFX | FMOD Automatic door sound (open and close). Legacy clips (muted). |
| UI | — (no cue that the way back is gone) |
| Input lock | — |
| Timing | 0.9 s open, 0.9 s close, 1.2 s lamp fade. The Relay's release clock starts once the door has shut. `FrontRooms3DGame.cs:869-870` |

Note: this door is automatic, while every map door needs E. The two door types also look
different (I5).

### I4. Look / aim prompt

| Channel | Today |
|---|---|
| Trigger | The crosshair ray hits a map door or a window pane within 2.4 m. `FrontRooms3DGame.cs:927-937` |
| Camera / body / object / VFX / post / SFX | — |
| UI | Text: "E · OPEN DOOR", "E · SHUT DOOR", "LOCKED · NEEDS THIS ZONE'S KEY" (only when doorsNeedKeys is on), or "HOLD E · BREAK GLASS". A broken door gives no prompt. Keys never prompt (they are auto-collected, I7). `FrontRoomsMap/FrontRoomsMapWorld.cs:1494-1511` |
| Timing | Instant on and off. No fade. `FrontRooms3DGame.cs:1524` |

### I5. Map door open / close (E)

| Channel | Today |
|---|---|
| Trigger | E (key down) on the leaf. `FrontRooms3DGame.cs:944-948` → `MapWorld.Use` `FrontRoomsMap/FrontRoomsMapWorld.cs:1513-1523` |
| Camera | — |
| Body/hands | — (no hand on the handle, because there is no handle) |
| Object | The leaf is a **Unity primitive cube**: 1 × 2.1 m opening, 0.05 m thick, DoorVeneer material, no handle, lock, hinge or frame hardware (a trim box frame only). It rotates 95° over 0.55 s with smoothstep, away from the player. It is not physical: it does not push the player and has no momentum. `FrontRoomsMap/FrontRoomsMapWorld.cs:854-893, 1530-1548, 1578-1590`; `FrontRoomsMap/FrontRoomsModuleUnits.cs:55-56` |
| VFX/Post | — |
| SFX | FMOD, driven by the hinge's real rotation: Handle + Unlatch on leaving the frame, a Swing loop (AngularVelocity, Openness), then StopLimit, StopMid or LatchStrike at rest. Legacy (muted): one hinge clip at .8. `Audio/FrontRoomsDoorSound.cs:44-125`; `FrontRooms3DGame.cs:769-774` |
| Gameplay | The Relay hears it within 14 m × 1.4. `FrontRooms3DGame.cs:772` |
| UI | The prompt flips OPEN/SHUT. |
| Input lock | None. The player can walk and look throughout. |
| Timing | 0.55 s. |

### I6. Locked door (only when doorsNeedKeys is on, which it is not in the shipped profile)

| Channel | Today |
|---|---|
| Trigger | E on a shut door without the key of **the zone the player stands in** (not the door's zone). `FrontRoomsMap/FrontRoomsMapWorld.cs:1516-1520, 1573` |
| Camera / body / object / VFX / post | — (no handle rattle, no leaf jiggle, no camera nudge) |
| SFX | FMOD `Mechanism/Door/Locked` one-shot. Nothing in the game code subscribes to `DoorLocked`. `Audio/FrontRoomsSoundDirector.cs:387, 450` |
| UI | The prompt already says "LOCKED · NEEDS THIS ZONE'S KEY". No flash text. |
| Status | Not reachable in the real game: `doorsNeedKeys: 0` in `Assets/Levels/FrontRoomsLevel0.asset:47`. The default is also false (`FrontRoomsMap/FrontRoomsLevelProfile.cs:30-31`). |

### I7. Key pickup

| Channel | Today |
|---|---|
| Trigger | **Automatic.** The player's flat distance to the key is under 0.9 m. No E press and no look check. `FrontRoomsMap/FrontRoomsMapWorld.cs:1592-1608` |
| Camera | — |
| Body/hands | — |
| Object | The key is a **primitive cube** 0.32 × 0.12 × 0.12 m at 1.05 m height, with its collider removed. It uses the emissive yellow "Map test / key" material (smoothness .4, emission .8× base). It spins at 90°/s. On pickup it is destroyed in one frame. `FrontRoomsMap/FrontRoomsMapWorld.cs:725-735, 1600, 1604, 1649` |
| VFX/Post | — |
| SFX | FMOD `Foley/Player/KeyPickup`, 2D. Legacy: none. The procedural `FrontRoomsAudio.Key()` exists but nothing calls it. `Audio/FrontRoomsSoundDirector.cs:452`; `FrontRoomsAudio.cs:68` |
| UI | 3 s flash in the bottom card: "KEY / OPENS THIS ZONE'S DOORS". In that zone the HUD then shows a key glyph and the fixed text "LEVEL 0 KEY" (also in Office zones). `FrontRooms3DGame.cs:784-789, 1385-1394, 1539, 1552` |
| Input lock | — |
| Timing | 1 frame, then 3 s of text. |
| Placement | One key per non-Tall zone, in the zone cell nearest the zone's site. `FrontRoomsMap/FrontRoomsMap.cs:630-651` |

### I8. Key use on a locked door (Red's example 1)

| Channel | Today |
|---|---|
| Trigger | — **There is no key-use action.** `Use()` checks `HasKeyHere()` and then calls the same `SwingAway` + `SetDoor` as any door. No `KeyUsed` or `DoorUnlocked` event exists. `FrontRoomsMap/FrontRoomsMapWorld.cs:1502, 1513-1523, 58-71` |
| Camera | — (no push-in, no framing, no input lock) |
| Body/hands | — (no hand, no key mesh in hand) |
| Object | Same 0.55 s swing as I5. The key is not consumed and no lock animates. |
| VFX/Post | — |
| SFX | Same as I5 (Handle/Unlatch/Swing). No key-in-lock or turn sound is defined in `Audio/FrontRoomsSoundIds.cs:15-35`. |
| UI | Prompt "E · OPEN DOOR" (`FrontRoomsMap/FrontRoomsMapWorld.cs:1502`). |
| Status | With `doorsNeedKeys: 0`, a held key changes nothing at a door. The pickup text "OPENS THIS ZONE'S DOORS" promises something the game does not do. |

### I9. Glass: hold E to break (the stress phase)

| Channel | Today |
|---|---|
| Trigger | Hold E with the crosshair on a pane. 1.0 s to break. Letting go, or looking off the pane, resets progress to 0. `FrontRooms3DGame.cs:938, 950-962`; `FrontRoomsMap/FrontRoomsMapWorld.cs:1551-1571` |
| Camera | — (no lean-in, no shake, no strain) |
| Body/hands | — (no hand or elbow on the glass) |
| Object | **No change.** The pane stays pristine until the frame it is destroyed. |
| VFX/Post | — |
| SFX | FMOD: a `Window/Stress` loop with `Progress` 0–1, plus two `Window/Crack` one-shots at 35% and 70%. On release the stress loop fades out. Legacy: none. `Audio/FrontRoomsSoundDirector.cs:421-435` |
| UI | Hold bar 120 × 4 px, yellow fill. `FrontRooms3DGame.cs:1376-1378, 1525-1529` |
| Input lock | None. The player can walk away mid-hold. |
| Timing | 1.0 s. |

### I10. Glass break (Red's example 2)

| Channel | Today |
|---|---|
| Trigger | Hold reaches 1.0 s. `FrontRoomsMap/FrontRoomsMapWorld.cs:1558` |
| Camera | — |
| Body/hands | — |
| Object | `Kill(window.pane)`: the primitive-cube pane is **destroyed in one frame**. No crack stage, no shards, no falling pieces, no physics, no frame residue, no glass on the floor. When the chunk is rebuilt, broken windows get no pane at all. `FrontRoomsMap/FrontRoomsMapWorld.cs:1559-1562, 896` |
| VFX | — (no particles. The particle module is not even installed, section 3.) |
| Post | — (no flash or CA pulse) |
| SFX | FMOD `Window/Shatter` one-shot at the window. Legacy (muted under FMOD): the **door-break impact clip**, reused for glass. The procedural `FrontRoomsAudio.Glass()` is never called. `Audio/FrontRoomsSoundDirector.cs:437-441`; `FrontRooms3DGame.cs:776-782, 1055-1074`; `FrontRoomsAudio.cs:84` |
| Gameplay | The Relay hears it within 40 m × 1.4 = 56 m, the loudest noise in the game. `FrontRooms3DGame.cs:149, 779` |
| UI | 3 s flash: "GLASS BROKEN / WALK INTO THE FRAME TO CLIMB THROUGH". `FrontRooms3DGame.cs:780` |
| Timing | 1 frame. |

Glass material in the maze (context for Red's "material and reflection are wrong"): the pane uses
`TransparentGlass("Map test / glass", (.75,.85,.88,.28))`. It is built in code with URP/Lit,
smoothness .9, `_Blend` 0 but SrcBlend One with `_ALPHAPREMULTIPLY_ON`, and ZWrite off
(`FrontRoomsMap/FrontRoomsMapWorld.cs:1650, 1653-1669`). It is not the project's glass from
`FrontRoomsRenderSetup.EnsureGlassMaterials`, which uses SrcAlpha/OneMinusSrcAlpha and turns off the
DepthOnly pass (`Assets/Editor/Rendering/FrontRoomsRenderSetup.cs:398-424`). The maze has no
reflection probe: the only `ReflectionProbe` reference in the scripts turns probes off in the stream
(`FrontRoomsRoomStream.cs:1171`). Global reflection intensity is .3 with no skybox
(`Rendering/FrontRoomsLook.cs:20, 30`; `FrontRoomsMap/FrontRoomsMapWorld.cs:490`). A smoothness .9
surface therefore has almost nothing to reflect. The pane renderer's shadow mode is left at the
primitive default (`FrontRoomsMap/FrontRoomsMapWorld.cs:897-902`). Whether the transparent pane
casts a solid shadow under the shadow-casting lamps is UNVERIFIED and needs an editor check. The
rendering audit should own the detail.

### I11. Climb through a broken window

| Channel | Today |
|---|---|
| Trigger | Automatic: walking toward a broken window from within 0.95 m, lateral offset under 0.45 m, input within 60° of the crossing. The sill is 0.35 m and the head is 2.0 m. `FrontRooms3DGame.cs:882-909`; `FrontRoomsMap/FrontRoomsModuleUnits.cs:59` |
| Camera | Over 0.6 s the body lerps (smoothstep) 0.75 m past the opening and lifts 0.35 m on a sine arc. The camera ducks 0.55 m at mid-climb. No pitch, roll or head turn is authored. `FrontRooms3DGame.cs:154, 911-924` |
| Body/hands | — (no hands on the sill) |
| Object | The CharacterController is disabled during each position write, so the frame is passed through. `FrontRooms3DGame.cs:916-918` |
| VFX/Post | — |
| SFX | FMOD `Foley/Player/Cloth` at the opening. Legacy (muted): one carpet footstep at .3. No glass crunch, because no glass is left. `Audio/FrontRoomsSoundDirector.cs:493`; `FrontRooms3DGame.cs:904-905` |
| UI | — |
| Input lock | Movement is locked for 0.6 s. Look stays free. |
| Timing | 0.6 s. It cannot fail or be interrupted. |

### I12. Sprint, stamina and footsteps

| Channel | Today |
|---|---|
| Trigger | Shift held while moving with stamina > 0. 5 s of stamina. Refill starts 1 s after the sprint ends, at 1 per s. `FrontRooms3DGame.cs:146-148, 825-835` |
| Camera | — (no FOV kick, no bob, no sway, no exhaustion effect at 0 stamina) |
| Body/hands | — |
| Post | — |
| SFX | FMOD footsteps are triggered by distance travelled (stride 1.45–1.72 m), with Surface, Gait and Dampness parameters. A Breath event is driven by mirrored stamina. Legacy (muted): a timer step every 0.5 s walking or 0.3 s sprinting. `Audio/FrontRoomsPlayerFootsteps.cs:39-96`; `Audio/FrontRoomsSoundDirector.cs:355, 392-393`; `FrontRooms3DGame.cs:842-851` |
| Gameplay | Each sprint step is a 26 m × 1.4 noise for the Relay. `FrontRooms3DGame.cs:849` |
| UI | 5 stamina segments under the crosshair, shown only while stamina is below full. `FrontRooms3DGame.cs:1379-1383, 1530-1536` |

### I13. Zone change (Level 0 low/standard/tall, Office)

| Channel | Today |
|---|---|
| Camera/body/object | — |
| Post | Office cells get a local volume (Resources/Rendering/FrontRoomsPost_Office) with a 2.5 m blend. `FrontRoomsMap/FrontRoomsMapWorld.cs:1379-1418` |
| SFX | FMOD global `Zone` parameter. Footstep surface is CarpetTile in the Office. `Audio/FrontRoomsSoundDirector.cs:222-229, 341-349` |
| UI | The top-left typography switches instantly ("LEVEL 0 / THE MAZE", "LEVEL 4 / OFFICE", etc.) along with the zone counter and ceiling height. `FrontRooms3DGame.cs:992-1001, 1512-1516` |

### I14. Relay release and first reveal

| Channel | Today |
|---|---|
| Trigger | 3 s after the start door has shut. The Relay is placed in a cell 9–15 cells away that the player cannot see, preferring cells behind them. `FrontRooms3DGame.cs:869-870`; `FrontRoomsMap/FrontRoomsMapHunter.cs:142-146, 370-397` |
| Object | The rig GameObject is switched on. The rig is 16 Unity primitives (6 cubes, 1 sphere, 9 capsules) with code-driven bone swing and no Animator. `FrontRooms3DGame.cs:968`; `FrontRoomsRelayRig.cs:100-145, 147-191`; `Assets/Scenes/FrontRooms3D.unity` (16 built-in mesh refs) |
| SFX | FMOD `Relay/Clicks` at the Relay + 2 m on its first state change, a `Relay/Presence` loop (Proximity, Occlusion), and a `Heartbeat` 2D loop (Proximity, forced to 0 while it sees the player). `Audio/FrontRoomsSoundDirector.cs:356-364, 470-474`; `Audio/FrontRoomsRelaySound.cs:112-132` |
| UI | The top-right threat panel appears: "RELAY / LISTEN", etc., plus "RELAY nn M", the exact distance in metres. `FrontRooms3DGame.cs:1513-1519` |
| Camera/post | — |

### I15. Relay heard: hunt, search, wander

| Channel | Today |
|---|---|
| Trigger | Player noises: door (I5), sprint (I12), glass (I10). `FrontRoomsMap/FrontRoomsMapHunter.cs:260-266` |
| Object | Rig Walk or IdleListen pose. Facing snaps instantly to its heading. `FrontRooms3DGame.cs:972-981` |
| SFX | FMOD stingers on Hunt, Search and Lost. Tension rises at 2/s and falls at 0.5/s. Footsteps come from the rig's leg contacts. Legacy (muted): a timer step every 0.44 s. `Audio/FrontRoomsSoundDirector.cs:319-339, 462-469`; `Audio/FrontRoomsRelaySound.cs:65-89`; `FrontRooms3DGame.cs:983-989` |
| UI | Threat text shows the state name in capitals. `FrontRooms3DGame.cs:1514` |
| Camera/post | — |

### I16. Being seen and chased

| Channel | Today |
|---|---|
| Trigger | A ray from the Relay's eye at 1.6 m to the player's eye, within 12 m, not blocked. Glass panes block it (they have box colliders). `FrontRoomsMap/FrontRoomsMapHunter.cs:175-186, 881-907` |
| Camera | — (no shake, FOV, breathing sway or forced look) |
| Object | The rig switches to Run at 1.15× speed and turns its facing straight to the player (instant snap). `FrontRooms3DGame.cs:972-981` |
| Post | — (no vignette, CA or grain pulse) |
| SFX | FMOD Chase stinger, tension towards 1, heartbeat set to 0 while seen (a design choice to confirm with the sound chat). `Audio/FrontRoomsSoundDirector.cs:328, 363, 467` |
| UI | "RELAY / CHASE" in yellow plus the exact distance in metres. `FrontRooms3DGame.cs:1514-1519` |
| Timing | Sight is lost after 1.5 s unseen. `FrontRoomsHunter.cs:27` |

### I17. Relay breaks a door

| Channel | Today |
|---|---|
| Trigger | The Relay's path meets a shut door. It walks to 0.45 m from the face and enters BreakDoor. `FrontRoomsMap/FrontRoomsMapHunter.cs:493-511` |
| Camera | — (no shake, even when the player is behind that door) |
| Object | Rig BreakDoor pose: crouch .13, forearms -42°. **The leaf does not react to the blows.** At 2.5 s, `BreakDoor()` swings it open in 0.18 s and it stays open, intact: no splinters, no damage state, no hinge failure. `FrontRoomsRelayRig.cs:111-133`; `FrontRoomsMap/FrontRoomsMapHunter.cs:862-879`; `FrontRoomsMap/FrontRoomsMapWorld.cs:1000-1009, 1584` |
| VFX/Post | — |
| SFX | FMOD `Door/Blow` every 0.5 s with Damage rising over 5 blows, then `Door/Break` + `Door/StopLimit` (Impact 1). The hinge's DoorSound also hears the 0.18 s swing and plays Handle + Unlatch + Swing + a second StopLimit. A handle sound on a smashed door is a desync. Legacy (muted): the door-break impact on every blow. `Audio/FrontRoomsSoundDirector.cs:443-460`; `Audio/FrontRoomsDoorSound.cs:90-94, 119-120`; `FrontRooms3DGame.cs:586` |
| UI | "RELAY / BREAKING DOOR". `FrontRooms3DGame.cs:1514` |
| Timing | 2.5 s of blows, plus 0.25 s fall. |

### I18. Caught (death)

| Channel | Today |
|---|---|
| Trigger | The Relay sees the player and is within 0.7 m (flat). `FrontRoomsMap/FrontRoomsMapHunter.cs:238-242` → `End()` `FrontRooms3DGame.cs:1559-1566` |
| Camera | — (**no turn to the Relay, no grab, no shake, no fall**). The game loop stops, so the camera freezes. `FrontRooms3DGame.cs:1494` |
| Body/hands | — |
| Object | The Relay stops (`caught` blocks Tick). `FrontRoomsMap/FrontRoomsMapHunter.cs:141` |
| VFX/Post | — |
| SFX | FMOD cuts room tone, fixtures, breath, heartbeat, stress and the SFX/AMB/Music buses to silence immediately, then plays one `Tinnitus`. Legacy (muted): a 1.6 s caught clip. `Audio/FrontRoomsSoundDirector.cs:478-491`; `FrontRooms3DGame.cs:1562` |
| UI | **A hard cut to a full-screen bone-white card** (.93, .92, .88, alpha .98) with "CAUGHT" in 88 px and the stats line, "R TRY AGAIN". The cursor unlocks. `FrontRooms3DGame.cs:1442-1443, 1461, 1469-1470` |
| Timing | 0 s. Same frame. |

### I19. Restart

| Channel | Today |
|---|---|
| Trigger | R while Caught or Paused. `FrontRooms3DGame.cs:1487` |
| Everything | Scene reload. The restart flag starts the run in the first stream room right away, skipping the title. Hard cut, no fade. `FrontRooms3DGame.cs:320-324, 494-502` |

### I20. Pause, display settings and focus loss

| Channel | Today |
|---|---|
| Trigger | Esc toggles pause. O opens display settings, where H toggles HDR. Losing focus pauses. `FrontRooms3DGame.cs:1472-1486` |
| UI | The same bone-white card with "PAUSED" and the key list. The list does not mention keys. `FrontRooms3DGame.cs:1468` |
| SFX | Nothing pauses the FMOD layer. The director runs on unscaled time and has no pause hook. `Audio/FrontRoomsSoundDirector.cs:124-139` |
| Note | `Time.timeScale` stays 1. The game loop is gated by phase. `FrontRooms3DGame.cs:295, 1494` |

### I21. Exits and level transitions

None. `Phase` is Title, Playing, Paused or Caught, with no Escaped or Win state
(`FrontRooms3DGame.cs:31`). The `FrontRoomsAudio.Escape()` clip exists but nothing calls it
(`FrontRoomsAudio.cs:116`). "LEVEL 4 / OFFICE" is a HUD label for an Office zone inside the same map,
not a transition (`FrontRooms3DGame.cs:994`). Tall zones are "left through windows"
(`FrontRoomsMap/FrontRoomsMap.cs:9-11, 170-171`), which is a zone border, not an exit.

### I22. Ambient moments (no player action)

- Lamp temperaments: steady, stutter, failing, dead-blink or dim, per fixture
  (`FrontRoomsMap/FrontRoomsMapWorld.cs:1067-1072, 1126-1158`). FMOD Strike and Tick one-shots
  on large level changes (`Audio/FrontRoomsSoundDirector.cs:299-316`).
- Chunk shift: a chunk left for 30 s comes back rearranged, always out of sight
  (`FrontRoomsMap/FrontRoomsMapWorld.cs:586-593`; `Assets/Levels/FrontRoomsLevel0.asset:46`).

### Documented but not implemented

`Documentation/UI_SYSTEM.md:34` lists "hold `E` reads" and "`Tab` opens notes" for 3D. The game has
no notes, reading or Tab handler (`FrontRooms3DGame.cs:1479-1501`). Whether this is still planned is
UNVERIFIED.

---

## 3. Platform and package constraints on any fix

- **Missing packages.** The resolved package list has no `com.unity.modules.particlesystem`,
  `com.unity.modules.animation`, `com.unity.timeline`, `com.unity.cinemachine` or
  `com.unity.visualeffectgraph` (`Packages/manifest.json`; `Packages/packages-lock.json`, entries at
  lines 3-188). Unity's manual says that using a disabled built-in package's scripting APIs gives
  "compiler errors" (https://docs.unity3d.com/6000.0/Documentation/Manual/upm-ui-disable.html).
  The ParticleSystem is a built-in package
  (https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.modules.particlesystem.html).
  So a glass shatter cannot use particles until that module is enabled, and an authored key/hand
  clip cannot play until the animation module is enabled. Physics is installed, so mesh shards
  with Rigidbody work today.
- **Who writes the camera.** `UpdateMapPlay` writes yaw and pitch every frame
  (`FrontRooms3DGame.cs:821-822`). A scripted shot (key push-in, caught) needs a state that
  suspends that write and the movement, as `Climb` does for movement only
  (`FrontRooms3DGame.cs:838`). This seam belongs to the map chat.
- **Event seams that already exist:** `DoorMoved`, `GlassHold(position, progress)`,
  `GlassHoldReleased`, `GlassBroken(position)`, `DoorBroken`, `KeyTaken(zone)`, `DoorLocked`
  (`FrontRoomsMap/FrontRoomsMapWorld.cs:58-71`), `PlayerClimbed`, `MapRunStarted/Ended`
  (`FrontRooms3DGame.cs:39-43`), and Relay `StateChanged`, `DoorBlow`, `Caught`
  (`FrontRoomsMap/FrontRoomsMapHunter.cs:126-128`).
- **Seams that are missing:** `KeyUsed/DoorUnlocked`, a glass-break impact direction or point, the
  Relay position or direction passed with `Caught`, and any camera-director or post-pulse API.
- **Quality.** Default quality is High (index 3) for WebGL and Ultra (index 5) for Standalone. The
  editor's current level is 3 (`ProjectSettings/QualitySettings.asset:7, 169, 275, 338-339`). The
  active build target lives in a binary Library file and was not read: UNVERIFIED here, left to
  the rendering audit.
- **Cost on WebGL (author's judgment, not measured).** Both requested shots are cheap. A camera
  push-in with a hand/key mesh and lock-turn animation costs a few draw calls. A shatter of about
  20–40 shard meshes on Rigidbodies for a second or two, plus a frame residue mesh, is small. Unlike
  screen-space reflections or ray tracing, neither depends on a high-end platform.

---

## 4. Cross-channel desyncs (sound describes what the picture does not)

1. **Glass hold.** FMOD plays two cracks at 35% and 70% (`Audio/FrontRoomsSoundDirector.cs:430-431`)
   while the pane stays untouched (`FrontRoomsMap/FrontRoomsMapWorld.cs:1551-1558`).
2. **Glass break.** FMOD plays a shatter, but the picture shows the pane vanishing in one frame
   (`FrontRoomsMap/FrontRoomsMapWorld.cs:1561`). The legacy fallback plays the door-break clip
   (`FrontRooms3DGame.cs:778`).
3. **Relay door break.** Blow sounds rise in damage while the leaf never moves. Then Handle and
   Unlatch play as the "broken" door swings open intact (`Audio/FrontRoomsDoorSound.cs:90-94`).
4. **Caught.** Sound does a deliberate hard cut to tinnitus. Picture does an unrelated hard cut to
   a white menu card, and the Relay is never framed.
5. **Key pickup.** A pickup sound and a promise ("OPENS THIS ZONE'S DOORS") with no function
   behind it while `doorsNeedKeys` is 0.

---

## 5. Gaps list

Severity: **S1** breaks immersion. **S2** noticeably cheap. **S3** polish.
Owner: **map** (FrontRooms3DGame.cs, FrontRoomsMap/*), **visual** (Rendering/*, Editor/Rendering/*,
props and Blender kit, RoomStream), **sound** (Audio/*). Where two chats are listed, the first one
leads.

The bar used here is the author's judgment of current first-person horror practice, not a cited
standard. A held object or hand is on screen for every scripted interaction. The camera reacts to
exertion, impacts and threat. Breakables break in stages that you can see. The death moment frames
the killer.

| # | Gap | Sev | Owner | Evidence |
|---|---|---|---|---|
| G1 | **Key use has no shot and no code path.** It needs an input-locked, framed push-in to the lock with a hand and key mesh, a key insert and turn, the latch releasing, then control returning. Today a key changes nothing: the same 0.55 s swing plays, there is no unlock event, and `doorsNeedKeys` is 0 so keys are inert. | S1 | map (flow, camera state, event, profile flag) + visual (hand/key/lock assets, close-up lighting) + sound (key-in-lock, turn) | I8; `FrontRoomsMap/FrontRoomsMapWorld.cs:1513-1523`; `Assets/Levels/FrontRoomsLevel0.asset:47` |
| G2 | **Glass break is deletion, not shatter.** It needs a crack stage (decal or texture swap tied to `GlassHold` progress), a break into shards with physics and an outward impulse from the player, a jagged frame residue that stays, and floor glass that crunches. Today the pane is destroyed in one frame. | S1 | visual (shard meshes, crack texture, residue, material) + map (spawn hook in `Hold`, residue persistence across chunk rebuilds, `brokenWindows`) + sound (glass-underfoot surface) | I9, I10; `FrontRoomsMap/FrontRoomsMapWorld.cs:1559-1562, 896` |
| G3 | **No first-person body or hands.** This is the precondition for G1, the glass hold, the climb and door use. Nothing is attached to the camera. | S1 | visual (rigged arms, near-clip safe) + map (viewmodel mount, per-interaction poses) | `FrontRooms3DGame.cs:1013`; section 1 |
| G4 | **The caught moment is a cut to a white menu card.** There is no turn to the Relay, no grab or lunge framing and no fall or fade. The Relay is never seen at the moment that matters. | S1 | map (camera take-over, Relay pose trigger, timed fade before the card) + visual (Relay lunge pose, post hit) | I18; `FrontRooms3DGame.cs:1442-1443, 1559-1566` |
| G5 | **The project cannot make particles or play animation clips.** The particle, animation, Timeline and Cinemachine modules are absent. Any plan for G1, G2 or G4 must start by enabling what it needs, or by using code-driven tweens and Rigidbody shards only. | S1 (blocker) | visual (enable modules, the VFX budget for WebGL) + map (agree on the approach) | section 3; `Packages/packages-lock.json` |
| G6 | **The glass hold is invisible.** FMOD cracks at 35% and 70% while the pane is pristine. There is no hand on the glass and no camera strain. Only a 4 px bar shows progress. | S2 | visual (crack stages) + map (drive them from progress) | I9; `Audio/FrontRoomsSoundDirector.cs:430-431` |
| G7 | **The maze glass material is a code-built test material.** "Map test / glass": premultiplied, smoothness .9, no reflection source in the maze (no probe, reflection intensity .3, no skybox). Its shadow behaviour is UNVERIFIED. It differs from the project's `EnsureGlassMaterials`. | S2 | visual (one shared glass asset, probe or planar reflection decision) + map (use that asset instead of `TransparentGlass`) | I10 note; `FrontRoomsMap/FrontRoomsMapWorld.cs:1650-1669`; `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs:398-424` |
| G8 | **No camera language system.** No head-bob or footstep sway, sprint FOV, exhaustion at 0 stamina, impact shake (glass break, nearby door break), chase shake or climb tilt. The camera is perfectly still in every moment. | S2 | map (camera rig with offset and FOV layers) + visual (tuning to the film look) | section 1; I12, I16, I17 |
| G9 | **The Relay's door break is visually inert.** The leaf ignores 5 blows, then swings open intact in 0.18 s. There are no splinters, no damage state and no hinge or latch failure. A handle and unlatch sound plays on the smash. | S2 | map (per-blow leaf jolt, broken state) + visual (damaged leaf, debris) + sound (suppress Handle/Unlatch when `broken`) | I17; `FrontRoomsMap/FrontRoomsMapHunter.cs:862-879`; `Audio/FrontRoomsDoorSound.cs:90-94` |
| G10 | **Map doors are primitive slabs with no hardware**, unlike the title doors, which have bar handles and kick plates. There is nothing to grab, nothing for a key to go into, and the two door types do not match. | S2 | visual (door leaf asset with lever and lock cylinder) + map (use it in `BuildEdge`) | I5; `FrontRoomsMap/FrontRoomsMapWorld.cs:875-880`; `FrontRoomsRoomStream.cs:1261-1271` |
| G11 | **Being seen and chased is told by HUD text**, "RELAY / CHASE" and an exact metre count, with no post or camera response. The metre readout reads as debug UI and drains tension. | S2 | map (HUD content) + visual (threat post pulse: vignette, CA, grain) | I14, I16; `FrontRooms3DGame.cs:1514-1519` |
| G12 | **The key pickup is an automatic vacuum of a spinning yellow emissive cube.** There is no E, no inspect and no hand, and the mesh is a primitive. | S2 | visual (key model and material) + map (look-and-press pickup, optional inspect) | I7; `FrontRoomsMap/FrontRoomsMapWorld.cs:725-735, 1592-1608` |
| G13 | **The climb is a 0.6 s lerp with a camera duck.** There are no hands on the sill, no head tilt and no glass crunch, and it cannot be interrupted. | S2 | map (camera path and tilt) + visual (hands) + sound (glass crunch) | I11; `FrontRooms3DGame.cs:911-924` |
| G14 | **The locked-door feedback, when enabled, is only a prompt and an FMOD one-shot.** There is no handle rattle or leaf jiggle, and the game ignores `DoorLocked`. It also checks the player's zone, not the door's. | S2 | map | I6; `FrontRoomsMap/FrontRoomsMapWorld.cs:1516-1520, 1573` |
| G15 | **No exit, goal or level transition exists**, so there is no end-of-run moment to shoot. The Escape clip is unused. | S2 (design) | map | I21; `FrontRooms3DGame.cs:31` |
| G16 | **The Relay's facing snaps instantly**, and the creature is 16 primitives. Every encounter frames a placeholder. | S2 | visual (rig and mesh) + map (turn smoothing) | `FrontRooms3DGame.cs:972-973`; `FrontRoomsRelayRig.cs:3-8` |
| G17 | **The start door's "way back is gone" beat has no shot.** It is automatic, with no E and no cue. It also behaves differently from map doors (proximity versus E). | S3 | map | I3; `FrontRooms3DGame.cs:733-734` |
| G18 | **The aimed object has no highlight or rim**, and the crosshair has no state change. Prompts pop on and off with no fade. | S3 | map (UI) + visual (outline or rim shader if wanted) | I4; `FrontRooms3DGame.cs:1520, 1524` |
| G19 | **Pause does not pause FMOD**, and restart is a hard cut with no fade. | S3 | sound (pause snapshot) + map (fade) | I19, I20 |
| G20 | **Legacy fallback gaps.** Glass uses the door-break clip, and the key has no legacy sound. This only matters if FMOD is not ready (for example, banks missing on a platform). | S3 | sound | `FrontRooms3DGame.cs:778`; `FrontRoomsAudio.cs:68, 84` |
| G21 | **Key HUD text is fixed at "LEVEL 0 KEY"**, also in Office zones, and the pickup text promises doors it does not open. | S3 | map | `FrontRooms3DGame.cs:787, 1392` |
| G22 | **The map test walker duplicates the interaction loop**, so any shot or viewmodel logic has to be shared or the test scene will drift. | S3 | map | `FrontRoomsMap/FrontRoomsMapWalker.cs:119-138` |

### Top 10 (ranked)

1. **G1.** Key use has no shot or code path, and keys are inert (`doorsNeedKeys: 0`). S1. map + visual + sound.
2. **G2.** Glass is deleted in one frame: no crack, shards, physics or residue. S1. visual + map.
3. **G3.** No first-person hands or body, which both requested shots need. S1. visual + map.
4. **G4.** Caught is a hard cut to a white card, and the Relay is never framed. S1. map + visual.
5. **G5.** The particle, animation, Timeline and Cinemachine modules are not installed, which blocks G1, G2 and G4. S1 blocker. visual + map.
6. **G7.** The maze glass is a code-built test material with nothing to reflect. S2. visual + map.
7. **G6.** The glass hold is invisible while FMOD plays cracks. S2. visual + map.
8. **G8.** No camera language (bob, FOV, shake, exhaustion, impacts). S2. map.
9. **G9.** The Relay's door break is inert: the leaf ignores blows and swings open intact. S2. map + visual + sound.
10. **G10.** Map doors are primitive slabs with no hardware, so a key has no lock to go into. G1 depends on this. S2. visual + map.

Next after the top 10: G11 (the chase is told by HUD text and a metre readout instead of picture), then G12 (key pickup).

---

## 6. Sources (web pages actually read)

- Unity Manual, disabling a built-in package (scripting APIs give "compiler errors"):
  https://docs.unity3d.com/6000.0/Documentation/Manual/upm-ui-disable.html
- Unity Manual, ParticleSystem built-in package:
  https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.modules.particlesystem.html
- Unity Manual, URP Lit shader (no per-material cast-shadow toggle documented there, so the glass
  shadow question stays UNVERIFIED): https://docs.unity3d.com/6000.0/Documentation/Manual/urp/lit-shader.html

Everything else in this file comes from the code and assets cited inline.
