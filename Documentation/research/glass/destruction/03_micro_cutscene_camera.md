# 03 — Micro-cutscene camera for breaking a window (GD2)

Status: DONE (research + three shot designs + a recommendation), 2026-10-03. Research only: nothing in Red's project or in any clone was changed. The camera rig belongs to the map chat, and the sound beats to the sound chat. The values below are the visual chat's proposal for `FrontRoomsShotTimings`.

Red, translated: "When the player tries to break the glass there should be camera feedback, like a micro cutscene." This report answers three questions:

1. What makes a one-second action feel like a cutscene without taking control away for long?
2. How do games do it with a visible arm or tool, and without hands (our language B)?
3. Which shot should FrontRooms use for the 1.0 s hold-to-break?

Read for this report: `interaction_audit/FrontRoomsShotTimings.proposal.cs.txt` (classes `Glass` and `Unlock`), `interaction_audit/10_audit_report.md` §3.0, §3.2 and §3.5–3.6, `interaction_audit/04_aaa_references.md` (its sources S1–S46 are reused here), `interactables/00_map_constraints.md`, `interactables/03_readability_placement_shots.md` §3.5, `interactables/06_period_windows.md` (in progress), `glass/images/03_*` and `04_*`, `Documentation/VISUAL_CHAT_TASKS.md` (G14, GD1, GD2, W8), and the game and RT code listed in §3–§4. I also read the glass track's shader in the private clone (`proj_glass`), read-only.

---

## 0. The answer in one screen

**Why the current glass proposal would not read as a cutscene.** The proposed `Glass` class (lean 5 cm, FOV −3°, three 4 cm jabs, shakes) is a feedback layer on top of the gameplay view. The `Unlock` head dip, which Red liked, reads as a cutscene for a different reason. The camera leaves the gameplay eye for an authored pose, holds there while the object acts, and then returns. The glass needs the same three parts, and it also needs an aftermath beat.

**The recipe (from the research in §2):**

| Ingredient | FrontRooms rule |
|---|---|
| A pose, entered softly | The body plants in front of the glass and braces: the eye drops, the head turns slightly away from the glass, and the horizon tilts toward the striking shoulder. Cubic ease, 0.25 s. |
| Beats with anticipation, contact and reaction | Three strikes land exactly on the sound beats (0.35 / 0.70 / 1.0). Each one has a wind-up, a fast strike, a recoil spring and a rotation-only shake. |
| Stop the object, not the world | On each impact the glass holds for 2–3 frames (33–50 ms) while the camera keeps moving. Never freeze the whole frame: in first person that reads as a hitch. |
| Payoff and a look | At the shatter the camera follows through into the space where the resistance vanished, flinches away, then looks back at the empty frame. This gives you the "cut" without cutting. |
| Release that the player can skip | Hard lock only 0.10 s after the shatter. Any move input then ends the shot. A chase or the Relay's sight ends it at once. |
| Restraint | Shake is rotation only. FOV punch is ≤ 8°, roll ≤ 4°, and there is no sustained fore-aft sway. No letterbox, no depth of field (DOF) on the glass, and no global slow motion. Everything is scaled by one Camera-motion setting. |

**Recommendation: Design 2, "Brace, strike, flinch"** (§5.2). It is the 1.0 s hold plus a 0.65 s aftermath:

- **Hard lock:** while E is held, then 0.10 s after the shatter.
- **Soft lock:** move to 1.30 s, look to 1.40 s. Any move input, a climb, or the Relay ends it early.
- **No hands.** This matches Red's answer in `VISUAL_CHAT_TASKS.md` W8: "a camera head-dip, no hands". A sleeve flash and a reflection-only body are listed as upgrades for Red to choose.

**Ray-traced glass (G14).** ChatGPT's Metal bridge works with these shots, but four things must change for the break to look right (§4):

1. Drop the broken pane from the ray-tracing scene on the same frame it breaks. Otherwise a ghost pane shows for up to 1 s during the aftermath.
2. Update piece transforms every frame while pieces move.
3. Make anything in front of the glass occlude the reflection.
4. Fix the FOV that is passed in radians where the kernel expects tan(FOV/2).

| Design | Reads as | Lock after the shatter (hard / soft) | Motion-sickness risk | Build cost | Verdict |
|---|---|---|---|---|---|
| 1 "Shove" (the existing `Glass`, tightened) | feedback, not a shot | 0 / 0 s | low | low | fallback, and the chase tier |
| **2 "Brace, strike, flinch"** | **a micro-cutscene** | **0.10 / 0.30–0.40 s** | **medium-low** | **medium** | **recommended** |
| 3 "Zoom and slow-mo" | a small film moment | 0.30 / 0.95 s | medium-high | medium-high | too long for a hunted player; keep its zoom for language C |

---

## 1. Where we start

### 1.1 What the game does today (code, read 2026-10-03; line numbers drift because the map chat is editing)

- **Hold.** `UpdateAim` (`FrontRooms3DGame.cs:986`) raycasts from the rendered camera with `Reach = 2.4` (`:156`). While E is held on a pane, `map.Hold()` adds `dt` and fires `GlassHold(pos, progress)`. At 1.0 s the pane is destroyed and `GlassBroken` fires (`FrontRoomsMapWorld.cs:1891-1904`). Releasing E resets the hold to 0 (`:1906-1911`).
- **Noise.** `OnGlassBroken` makes a 40 m noise (`FrontRooms3DGame.cs:820-826`, `GlassNoiseRadius = 40f` at `:156`). With `hearing = 1.4` (`FrontRoomsHunter.cs:32`), the Relay hears the shatter from 56 m. The cracks make no Relay noise.
- **Camera.** There is no camera system: FOV 76 (vertical) and near plane 0.06 (`FrontRooms3DGame.cs:243`). There is no shake, lean or takeover (audit F6).
- **Climb.** You walk into the empty frame: `TryStartClimb`, 0.6 s (`:161`, `:941`).
- **Relay speeds.** Hunt 2.6 m/s, chase 4.2 m/s, catch at 0.7 m (`FrontRoomsHunter.cs:23-28`). So every 0.1 s of locked control lets a chasing Relay close 0.42 m.

### 1.2 The two shots already proposed, side by side

Values are from `FrontRoomsShotTimings.proposal.cs.txt`.

| | `Unlock`: the head dip (Red liked it) | `Glass`: the current proposal |
|---|---|---|
| Authored pose | Eye drops 0.25 m, pitches 38° down, ends 0.57 m from the lock | None: a 5 cm lean |
| Travel into the pose | 0.35–0.55 s, cubic ease-in-out | Sine ease over 0.35 s |
| FOV | −14° on the same curve | −3° push, then a −3° punch at the shatter |
| What acts | The key goes in and turns, the bolt jolts, the door pops ajar | Cracks, then the shatter |
| Payoff | 0.3° bolt jolt, the leaf pops 10° ajar | 1.5° shake, FOV punch, chromatic aberration (CA) pulse |
| Return | 0.40 s cubic | The lean releases in 0.3 s |
| Lock | Look to 1.30 s, move to 1.45 s | Move while E is held; look cone ±8° |
| Post | Shot volume over 0.4 s (far blur, vignette +0.1, exposure +0.15) | CA pulse |

**Why the glass column reads as an effect, not a shot.** Every number in it sits on top of the gameplay view: the camera never goes anywhere, and nothing happens after 1.0 s except a shake. The Unlock shot has a place it goes to, a moment where you watch, and a return. Design 2 below gives the glass the same shape, sized for a violent action at eye height instead of a delicate one at hip height.

---

## 2. Research: how a short physical action becomes a "cutscene"

Source IDs: **M#** are new in this report. **S#** are from `interaction_audit/04_aaa_references.md` and are repeated in §10 so that this file stands alone.

### 2.1 Keep it short, partial and escapable

- **Doom (2016).** id Software kept glory kills to "hundreds of milliseconds". Robert Duffy: "you want to keep the player moving" [M1]. They are chosen by where the player stands, so the takeover is contextual, not a fixed clip [M1].
- **John Nesky's camera talk.** His list of 50 camera mistakes includes "giving the player control over the camera, and then taking it away" (#34) [M3].
- **Half-Life 2** never takes control away (S31).
- **Resident Evil 4 remake.** Capcom dropped quick-time events (QTEs) in favour of a parry, because they felt players would no longer enjoy them [M21]. So no button prompts belong inside a short shot; the hold itself is the input.
- **Dying Light.** Techland tuned "the animation, the physics, and the camera settings" of the dropkick together so it did not feel "like just a video". They kept the enemy in sight and made sure the player's legs never cover the target [M17].
- **God of War (2018) and Hellblade.** Both never cut. The gameplay camera itself becomes the cinematic camera and hands back without a cut (God of War: Dori Arazi [M6]; Hellblade: Ninja Theory dev diary [M7]).

**For FrontRooms:**
- Lock the body, keep a little look, never cut, and keep the struck point in frame.
- After the impact, give control back on the first move input.
- A chase overrides everything.

### 2.2 The structure: pose, beats, payoff, look, release

- **Motivated camera.** God of War's no-cut camera follows documentary rules: "the camera always be motivated by something in order to move". Lens changes are hidden under character movement (24 mm to 120 mm in one example) [M6]. For FrontRooms, every camera move is caused either by the body (brace, wind-up, strike, flinch) or by the glass (resistance vanishing at the shatter). FOV changes ride under those moves.
- **Additive layers.** In Uncharted 3, camera shake is "a separate layer of additive cameras keyed off of player animations", and the game also has authored animated cameras [M5]. For FrontRooms, the shot is a set of additive layers on top of `BaseEye`, keyed off hold progress. Gameplay rays read `BaseEye` and never see them (audit §3.0).
- **Anticipation, action, follow-through.** These classic animation principles (Thomas & Johnston, *The Illusion of Life*, 1981; general reference, not re-read) map onto each strike: wind-up, fast strike, recoil. They also map onto the shatter, where the body follows through into the space where the resistance vanished.
- **The Unlock head dip** (Red's favourite) already has pose, hold and return. Design 2 adds the two parts a violent action needs: beats, and a look at the result.

### 2.3 Impact: stop the object, not the world (hit-stop)

- **Vlambeer.** Nuclear Throne freezes "about 10–20 milliseconds whenever you hit something" (Jan Willem Nijman in a Rock Paper Shotgun interview, 2013, as summarised in [M10]).
- **Masahiro Sakurai** recommends freezing the action for impactful moments. His tips include "keep the attacker moving just a little", "gradually lessen the shake", and scaling the shake with camera distance [M11].
- **First-person caveat (my judgement).** A whole-frame freeze in first person looks like a frame hitch, and FrontRooms already has a 1.44 s chunk-build hitch (audit F16). So the hit-stop goes on the glass only:
  - the crack reveal and the chips hold for 2–3 frames at 60 fps (33–50 ms);
  - at the shatter, every piece holds in place with the full crack network visible for 50 ms, then flies;
  - the camera keeps moving through all of it (Sakurai's attacker).

### 2.4 Time dilation

- **Call of Duty: Modern Warfare 2 (2009).** Its "breach and clear" rooms play in slow motion as the door blows [M23].
- **Mirror's Edge** has a charged slow-motion "reaction time" [M15].
- **Dying Light** deliberately "slowed down gravity" so the player feels the dropkick's impact [M17]. That is a local time dilation of physics, not the whole world.
- **Academic framing.** A Games and Culture article separates "cinematic slow motion" (spectacle) from "bullet time" (slow motion the player controls for an advantage) [M29].

**For FrontRooms:**
- **Never global.** Changing `Time.timeScale` would slow the Relay, the hunter tick and every timer, and it reads as a bullet-time power.
- **Local only.** Only the shards and the dust get a slower clock. With pre-simulated pieces this is just a playback rate. With rigidbodies, scale velocity by s, gravity by s² and angular velocity by s, then restore.
- **Never during a chase.**
- **Era check (judgement).** A 1990 consumer camcorder could not shoot slow motion, so it is a film device, not a found-footage one. Design 2 keeps it as a subtle A/B switch (0.6× for 0.15 s), off by default. Design 3 uses it fully.

### 2.5 Framing tools: push-in, FOV, focus, letterbox

- **Push-in and FOV.**
  - Nesky lists "using a too small field-of-view" (#41), "rapidly shifting field-of-view" (#42) and "rapidly transitioning to a new camera position" (#46) as mistakes [M3].
  - XAG 117 asks for adjustable FOV, because narrow and wide FOVs affect sickness differently [M12].
  - God of War hides lens changes under movement [M6].
  - Rule kept from the audit: FOV deltas ≤ 15°, changes over ≥ 0.4 s, and punches ≤ 8° only inside a takeover and under a body move.
- **Depth of field: no.**
  - The new `FrontRooms/Glass` shader is `ZWrite Off` (`proj_glass/Assets/Resources/Rendering/FrontRoomsGlass.shader:7, 82`). DOF would therefore read the depth of the room behind the pane and blur the cracks, the same problem the audit found with the old pane (§3.0).
  - Uncharted 3 does use DOF with its cameras [M5]. But the era rule for FrontRooms is a camcorder's deep focus (audit §3.0).
  - Instead, focus comes from framing, a vignette and sound.
- **Letterbox: no.** Four reasons:
  1. Bars say "you are not in control" while the player is still holding E and can cancel.
  2. Bars sliding in and out within one second are a large edge motion.
  3. 1990 video was 4:3 SD (S41), and permanent letterbox is film language (*The Order: 1886*, S40).
  4. Bars hide the edges of the frame exactly when the player needs them to watch for the Relay.
  
  Instead, use the existing 0.15 s HUD fade, a +0.08 vignette, and the `Snapshot/Closeup` sound duck proposed for the Unlock shot.

### 2.6 Shake and sound sync

- **Squirrel Eiserloh's camera talk** covers types of shake and smooth follow [M4]. Two common takeaways are reported by secondary summaries, not checked against the video: use only rotational shake in 3D, and drive shake by a decaying "trauma" value with smooth noise rather than random jitter.
- Nesky lists "excessively shaking the camera" (#43) [M3].
- **Steve Swink** defines polish as the "harmony of animation, sounds, and effects with input-driven motion" [M8].
- **Naughty Dog's glass** in The Last of Us Part II: "sound, lighting, and FX are essential to complete the quartet" (Michael Fadollone) [M22].
- **For FrontRooms:**
  - Shake is rotation only.
  - Translation is reserved for motivated body moves (brace, strike, recoil, flinch).
  - One beat table drives the picture and the FMOD event on the same frame.
  - The sound chat's beats stay exactly where they are: Crack1 0.35, Crack2 0.70, Shatter 1.0.

### 2.7 With an arm or tool, or without hands

| What is shown | Games (sources) | What it buys | What it costs |
|---|---|---|---|
| Full body, camera on the rig | Mirror's Edge [M15, S12, S13]; Battlefield 3: the camera "now actually sits on the animation rig" [M16] | Weight, landings, a body in the world | Full first-person body animation; hand-keyed camera (mocapped head failed, S13) |
| Hands and feet at contact points | Outlast (S28, S6); Dying Light (S14, M17); RE7 hands on walls (S26); RE Village hands at "doors, ladders and gates" [M19]; Firewatch torso and legs [M28, partly UNVERIFIED] | Unmistakable agency; embodiment (RE uses hands to carry pain [M19]) | A rig and clips per interaction, IK to each target, and the risk that elaborate hand animations become "a little cutscene" (S26) |
| First-person takeover with arms | Doom glory kills [M1]; Dishonored kill animations, which "would have to be adjusted for VR" [M25] | Spectacle in a few hundred ms | Lots of camera motion; comfort cost |
| Device or object framed | Alien: Isolation tools (S4 forum report); its team chose first person because it made it "feel like Alien" (Alistair Hope, GDC 2015) [M27] | Focus on the object | A framing anchor per device |
| Hands only, no arms | Half-Life: Alyx. Robin Walker: when you play "you don't notice that at all ... your brain edits those out" [M18] | Players don't miss arms | — |
| No hands; the object does the work | Amnesia/SOMA physics grab (S8, S9, S27); Amnesia: The Bunker, where bricks and a sledgehammer break wooden doors and guns break locks [M26] | Cheap, no animation risk | Can feel telekinetic (S27) |
| Third person (staging only) | The Last of Us Part II: glass breaks differently depending on what hits it; break it for supplies and risk being heard [M22] | Reads at a glance | Not available in first person |

**For FrontRooms (language B):**
- Valve's observation [M18] is the best evidence that players will not miss arms in first person.
- The risk is the opposite one: a camera that jolts with no cause reads as an earthquake.
- Design 2 solves that with anticipation. The wind-up before each strike is what makes the jolt read as "I hit it".
- Arms remain an optional upgrade for each design (§5). Costs in FrontRooms specifically:
  - the Animation module is not installed (audit F9);
  - Red's standing order needs a hero LOD0 that holds up at 0.3 m;
  - the Metal ray-tracing bridge only sees `MeshRenderer`s, so a skinned arm would currently get the glass reflection painted over it (§4).

### 2.8 Motion sickness and settings

- **Game Accessibility Guidelines.** They list "camera shakes or tilting, or changing where the character is looking without the player's input" as problems, and ask for an option to turn them off [M13].
- **XAG 117:** avoid camera shake, bobbing and motion blur, or offer to turn them off; provide adjustable FOV; let players disable automatic camera movement. Its examples include Cyberpunk 2077's "additive camera motions" setting and Halo Infinite's per-effect sliders [M12]. FrontRooms' Camera-motion setting (Off / 50% / 100%) is the same idea.
- **Diels and Howarth (2013).** Visually induced sickness from fore-aft oscillation peaks at 0.2–0.4 Hz, and they recommend avoiding that band [M14]. A lean or flinch is a one-off move, but any slow forward-and-back sway with a 2.5–5 s period is ruled out.
- **VR shows the limit.**
  - RE7 VR made the camera never move on its own and turned in "set angles which the camera will cut to" [M20].
  - Arkane said Dishonored's animated kills would have to be adjusted for VR [M25].
  - Flat-screen takeovers are tolerated because they are short and small, so keep them that way.
- **Mirror's Edge** removed head bob ("viewing the game from your eyes and not your head") and added a centre dot to fix the gaze [M15].

**FrontRooms limits for this shot:**
- shake is rotation only, ≤ 1.5°, decaying within 0.3 s;
- roll ≤ 4°, yaw ≤ 12°, pitch ≤ 8° (except the head-dip-class tilts of Design 3);
- translation ≤ 0.16 m from `BaseEye`, world-clamped;
- FOV ≤ −10° (Design 3) or ≤ −8° (Design 2);
- no sustained oscillation below 1 Hz.

### 2.9 Index of every reference Red's brief named

| Reference | What it does (verified part) | Lesson for the glass shot | Status |
|---|---|---|---|
| Resident Evil 7 | Doors creak open and stay ajar until you walk into them (S25); hands press on walls (S26); VR: the camera never moves on its own [M20] | Hand the end of the action back to the player | Verified (press, interviews) |
| Resident Evil Village | Hands at doors, ladders and gates carry Ethan's damage [M19] | Hands as embodiment; not needed for B | Verified (essay) |
| Resident Evil 4 remake | QTEs removed for a parry [M21]; third person | No prompts inside a shot | Verified; first-person contextual moves N/A (third person) |
| Alien: Isolation | First person chosen to make it "feel like Alien" [M27]; device moments frame the tool (S4) | Frame the object | Framing details UNVERIFIED (forum) |
| Outlast 1/2/Trials | Hands and feet so you are not a floating camera (S28); doors smashed loudly or opened slowly (S29) | Speed and noise as choice | Outlast 1 verified; 2/Trials not researched |
| Amnesia: Rebirth / The Bunker | The Bunker: bricks or a sledgehammer break wooden doors; guns break locks [M26] | The object does the work; no takeover | Rebirth hands UNVERIFIED |
| SOMA | Grabbed doors lag the cursor for weight (S27) | Weight without a body | Verified (press) |
| Dying Light | Dropkick tuned so it doesn't feel "like just a video"; gravity slowed [M17] | Tune camera and physics together; local time dilation | Verified (interview) |
| Mirror's Edge | Camera from the eyes, no head bob, centre dot, slow-motion "reaction time" [M15]; camera on the rig (BF3) [M16] | Body awareness; restraint | Verified |
| Call of Duty | MW2 breach-and-clear slow motion [M23]; MW2019 doors: use, sprint-bash (heard), aim + use to crack open [M24] | Slow motion at the breach; speed and noise | A CoD window-break interaction was not found: UNVERIFIED |
| The Last of Us Part II | Glass breaks by what hits it; noise vs supplies; "the quartet" [M22] | Sound, light and FX sell it as much as the mesh | Verified (80.lv, interview) |
| Half-Life: Alyx | Hands only, no arms [M18] | Players don't miss arms | Verified |
| Firewatch | Torso and legs visible; exaggerated proportions seen only from the camera [M28] | First-person bodies are built for the lens | Article body unreadable: details UNVERIFIED |
| Hellblade | Camera never cuts, even for cutscenes [M7] | No-cut takeovers | Verified (summary of dev diary) |
| Doom (2016) glory kills | Hundreds of milliseconds, chosen by position [M1] | Short, contextual takeover | Invulnerability during glory kills UNVERIFIED |
| Dishonored | Animated first-person kills are camera-heavy; would need rework for VR [M25] | Takeover motion has a comfort cost | Verified (UploadVR); the "throw up" quote is UNVERIFIED |
| GDC: Eiserloh 2016 | Shake types, smooth follow [M4] | Rotation-only shake, trauma decay | Takeaways from secondary summaries |
| GDC: Nesky 2014 | 50 mistakes: #34, #41, #42, #43, #46 [M3] | Don't take control away, don't snap FOV or shake hard | List via a transcription |
| GDC: Mirror's Edge (Dahl, Lagre) | First-person full-body movement (S12); hand-keyed camera won (S13) | Author the camera by hand | Verified (Vault page) |
| Naughty Dog / Santa Monica | Uncharted 3 cameras: additive shake keyed off animation, DOF [M5]; God of War no-cut camera [M6] | Additive layers; motivated moves | Verified (Vault page, press) |
| Swink, *Game Feel* | Polish = harmony of animation, sound and effects with input-driven motion [M8] | Sync every layer to the beat | Verified (book summary, article) |
| Accessibility (XAG, GAG, APX) | Toggles for shake, bob, auto camera, FOV [M12, M13] | Camera-motion setting, Reduce flashing | APX has no camera-comfort card in its list (accessible.games/apx) |

---

## 3. FrontRooms facts the shot must fit

| Fact | Value | Source |
|---|---|---|
| Eye height, player radius | 1.62 m, 0.3 m | `FrontRoomsModuleUnits.cs:92` |
| FOV (vertical), near plane | 76°, 0.06 m | `FrontRooms3DGame.cs:243` |
| Window opening | 1.4 wide, sill 0.35, head 2.0; pane collider 1.4 × 1.65 × 0.03 on the wall line | `FrontRoomsModuleUnits.cs:61`; `00_map_constraints.md` |
| Aim reach (all interactables) | 2.4 m | `FrontRooms3DGame.cs:156` |
| Authored impact centres | 3 × 3 grid: x ∈ {−0.40, 0, +0.40}, height ∈ {0.90, 1.30, 1.65} | `interactables/03_readability_placement_shots.md` §3.5 |
| Glass noise heard from | 40 m × hearing 1.4 = 56 m | `FrontRooms3DGame.cs:156, 820-826`; `FrontRoomsHunter.cs:32` |
| Relay closing per 0.1 s of lock | 0.42 m in chase, 0.26 m in hunt | `FrontRoomsHunter.cs:23-25` |
| Frame height at the pane | 0.78 m at 0.55 m with FOV 71°; 1.87 m at 1.2 m with FOV 76° | geometry: 2·d·tan(FOV/2) |
| Shard fall time to the floor | 0.49 s from the pane centre (1.175 m), 0.58 s from 1.65 m | √(2h/g) |
| Glass depth | `ZWrite Off` | `FrontRoomsGlass.shader:7, 82` (clone) |
| Camera rules already agreed | Gameplay reads `BaseEye`; every offset is world-clamped (0.1 m spherecast); HUD fades in 0.15 s; Caught > Cancel > Shot | proposal file; audit §3.0 |

Two consequences shape all three designs:

1. **Distance.**
   - You can start breaking a pane from 2.4 m today. A body cannot strike glass from there, and at 1.2 m the window is a small part of the frame.
   - Designs 2 and 3 therefore add a **step-in**: in the first 0.20 s the body (not the camera) moves to stand 0.55 m from the pane, in front of the impact centre. It moves at most 0.65 m forward and 0.25 m sideways, at walking speed, and the move is swept.
   - They also propose a **1.2 m glass prompt range**. That is a map-chat change for Red to approve.
   - At 0.55 m the 1.4 m pane fills the frame width.
2. **Impact snapping.**
   - The authored 3 × 3 centres can sit up to about 0.27 m from where the player aimed. At 0.55 m that is up to 26° off the crosshair.
   - The camera may rotate at most 6° yaw and 8° pitch toward the snapped centre, and the step-in absorbs the lateral part. Anything larger is left alone.
   - The fracture reports (01/02/04 in this folder) should either:
     - offer more centres (≤ 0.10 m error would be ideal for the camera), or
     - start the stage-1 and stage-2 cracks at the true aim point.
   - Either way, the variant should be chosen at E-down, not at 1.0 s, so the camera knows the centre from the first frame.

---

## 4. The ray-traced glass (G14) and the shot

Red asked the team to understand what ChatGPT built. This section covers what matters for the camera; the glass-rt-track workflow (G14) owns the production design.

**What the bridge does** (read from code, not run):

- `FrontRoomsMetalGlassTarget` marks a pane (the map adds it at `FrontRoomsMapWorld.cs:1049`).
- Every 1 s (`rescanSeconds = 1f`, `FrontRoomsMetalGlassRT.cs:35, 117-121`) the controller rebuilds the native scene:
  - every enabled `MeshRenderer` within 18 m of the nearest pane, up to 256 instances (`:33-34, 124-160`);
  - a BLAS per mesh and one TLAS, with transforms captured at that moment (`:201`).
- Each frame, a Metal kernel re-traces the primary ray from the camera's transform and FOV. Where the first hit is a glass instance, it traces one reflected ray, shades it flat (fake sun, sky on a miss) and writes colour with alpha 1. Elsewhere it writes zero (`FrontRoomsMetalGlassRT.mm:245-302`). There is no frame history.
- A URP pass composites the result **after post-processing**, with `ZTest Always` (`FrontRoomsMetalGlassRTRendererFeature.cs:17`; `FrontRoomsMetalGlassRTComposite.shader:9, 12`).

**What that means for the micro-cutscene:**

| # | Issue | Effect on the shot | Fix (G14's track) |
|---|---|---|---|
| R1 | The broken pane stays in the TLAS until the next 1 s rescan | During the aftermath (1.0–1.65 s) the kernel still hits a pane that no longer exists, and the composite paints its reflection over the empty frame: a ghost pane in the payoff shot | On `WindowShattered`, remove the pane and add the pieces on the same frame |
| R2 | Transforms are captured only at rescan | Flying pieces, and any shot prop such as a sleeve, show reflections at stale positions, jumping once per second | Per-frame instance transforms while anything moves (TLAS rebuild or refit only, BLAS once per piece mesh); cost UNVERIFIED, measure |
| R3 | No depth test, composite after post, alpha 1 at strength 1 | (a) Anything in front of the glass that is not in the TLAS gets painted over: a skinned arm, particles. (b) The shot's vignette, CA pulse and exposure don't reach the reflection. (c) At strength 1 the reflection replaces the view through the pane. | G14's plan to feed `_FR_GlassRTReflection` into the glass shader, before transparents, fixes all three |
| R4 | FOV is passed in radians where the kernel reads tan(FOV/2) (`FrontRoomsMetalGlassRT.cs:240, 369-377` writes `fovRadians` at byte 64; `.mm:68-84` reads it as `tanFovY`) | At FOV 76° it writes 1.33 instead of 0.78, so the traced pane is about 1.7× too small and pulled toward the centre. The FOV punch makes the misregistration pulse. | Pass tan(FOV/2) (G14 already lists this as suspected; the code read confirms it) |
| R5 | No frame history | Shake and punches cannot ghost in the reflection | Nothing to fix (good) |

**Highest-spec option: a reflection-only body.**
- At 0.55 m from a pane, a real window shows your own silhouette, especially when the far side is darker. In language B there is no body, so the traced reflection shows the room behind the player with no one in it.
- The bridge registers every enabled `MeshRenderer`, including ones on a layer the main camera does not draw. So a simple 1990 office-worker silhouette could exist only for the reflection:
  - 4 rigid parts (torso, head, upper arm, forearm), posed by code on the same beats;
  - no collider, no Animator.
- Then the glass would show the player's own coil and strike, and the stage-2 cracks would break that reflection into facets.
- This is desktop ray tracing only. The probe and planar fallbacks don't include the player. It is Red's call (§8).

---

## 5. Three shot designs

### 5.0 Shared rules (all designs)

**Conventions**
- **Time.** Up to the shatter, time = hold progress × 1.0 s, so the beats stay locked to the sound chat. After the shatter, time is real. Pose blends (in, out, cancel) run in real time.
- **Offsets.** Additive to `BaseEye`, in the camera's yaw frame:
  - **fwd** = toward the pane, **drop** = down, in metres;
  - **yaw +** = turning away from the striking side;
  - **roll +** = tilting toward the striking shoulder;
  - **pitch +** = looking down.
  - The striking side is the right.
  - Values in tables are **targets**, not deltas.

**Easing**
- Wind-ups: smoothstep.
- Strikes: ease-in quad (accelerating into contact).
- Recoil: critically damped spring, ω = 40 rad/s (settles to 5% in about 0.12 s).
- Flinch: ease-out cubic.
- Pose in and out: cubic ease-in-out.

**Shake**
- Rotation only: amplitude = max × trauma², with trauma decaying linearly over the stated time, on about 16 Hz smooth noise.
- The trauma recipe follows [M4]'s secondary summaries; the numbers are ESTIMATES.

**Object stop.** The glass holds 33 / 40 / 50 ms on Crack1 / Crack2 / Shatter. The camera never stops.

**Post and sound**
- No letterbox, no DOF, no motion blur.
- HUD fades out over 0.15 s (captions stay).
- Vignette +0.08.
- CA pulse at the shatter, off with Reduce flashing.
- `Snapshot/Closeup` (proposed for the Unlock shot) ducks room tone about 3 dB during the shot.
- Beats are unchanged: Crack1 0.35, Crack2 0.70, Shatter 1.0, and `GlassBroken` still fires at 1.0.

**Input and cancel**

*During the hold*
- Move is locked while E is held; look is free inside a cone.
- Releasing E before 1.0 cancels: offsets return in 0.20 s, cracks persist, and the next hold resumes from the stage reached (audit §3.5).

*Chase and sight*
- **Change from the audit.** The Relay's sight no longer cancels the hold. A window is an escape route, so a chase **demotes the camera, not the action**.
  - **Before the shatter:** the shot drops to Design 1 values at 50%, with no step-in and no yaw-away. The hold continues while E is held.
  - **At or after the shatter:** the aftermath is skipped, offsets return in 0.12 s, and control is immediate.
- The trigger is the Unlock rule: the Relay is in Chase, or within 6 m with sight.

*After the shatter*
- Climbing (walking into the frame) ends the shot at once and hands over to the climb camera in 0.1 s.
- Caught overrides everything.

**Tap mode** (accessibility, S20)
- One tap = one strike: the strike and impact play at once, with no wind-up delay.
- Each tap adds 0.35 of progress, with a ≥ 0.3 s cooldown.

**Camera-motion setting**
- **Off:** no step-in, no pose, no lean, roll, shake or FOV change. Look is free, and control returns at 1.0. The glass, the object stop and the sound still play.
- **50%:** every amplitude is halved (metres, degrees, FOV); timings stay the same.
- **100%:** as written.

**WebGL.** The camera values are the same, because they are only transforms. The ray-tracing items in §4 are desktop only, and WebGL keeps its own shard budget (separate track).

### 5.1 Design 1 — "Shove" (the existing `Glass`, tightened)

**What the player sees.** The view leans 5 cm toward the pane and narrows slightly. Three shoves land on the cracks with small rotational jolts. At 1.0 s the view punches in and shakes as the glass bursts outward, then it is immediately the player's again.

| t (s) | Camera | Glass | Sound |
|---|---|---|---|
| 0.00–0.35 | Lean fwd 0.05, FOV −3° (sine) | Pane bows (normal perturbation) | `Mechanism/Window/Stress` |
| 0.35 | Jab +0.04 and back over 0.12 s; shake 0.4° / 0.12 s | Stage 1 cracks; **object stop 33 ms**; 3–6 chips | Crack (exists) |
| 0.70 | Jab; shake 0.6° / 0.15 s | Stage 2; **object stop 40 ms** | Crack |
| 1.00 | Jab; shake 1.5° / 0.25 s; FOV punch −3° over 0.3 s; CA pulse; the lean releases over 0.3 s (additive, control already back) | Swap to fracture; **object stop 50 ms**; pieces fly | Shatter (exists) |
| 1.35–1.60 | — | Pieces land (`ShardLandMin/Max` 0.35/0.60 after the shatter) | ShardLand NEW |

- **Lock:** move while E is held; look cone ±8°. There is no lock after 1.0 s.
- **Chase:** nothing to demote. Shake is halved.
- **Arm/tool option.** A forearm and palm flat on the glass during the lean; the existing `_Palm` smudge appears under it.
  - Adds: a cause for the smudge, and scale.
  - Costs: a hero hand LOD0 at about 0.4 m; a rigid pose moved by code; per-frame ray-tracing registration (R2/R3).
  - Physically, a palm shove rarely breaks 6 mm annealed glass, so it reads weaker than a strike.
- **Motion sickness:** low. Every move is small and one-off.
- **Verdict:** honest feedback, but not a cutscene. Keep it as the Camera-motion 50% / chase tier of Design 2.

### 5.2 Design 2 — "Brace, strike, flinch" (recommended)

**What the player sees:**

1. On E-down the body steps up to the glass and plants. The view lowers a few centimetres, turns a little away from the pane (the face protected), and the horizon tilts toward the right shoulder. The pane fills the frame.
2. On each beat the head coils back, then snaps forward into the glass. A crack bursts from the impact and the glass holds for an instant while the view recoils.
3. The third strike goes through: the view lunges forward into the space where the glass was, then flinches away as the pane explodes outward.
4. A beat later the head turns back. The player is looking at the empty frame, glass still raining onto the sill, with the far side open.
5. Control returns. The first step forward starts the climb.

| t (s) | Phase | Camera targets (fwd m, drop m, yaw °, roll °, pitch °; FOV) | Body / glass | Sound (beats unchanged) |
|---|---|---|---|---|
| 0.00–0.25 | **Plant and brace** | Pose in (cubic, 0.25 s): fwd +0.03, drop 0.06, yaw +6, roll +2, look-at toward the impact centre (≤ 6° yaw, ≤ 8° pitch). FOV −5° over 0.40 s. HUD out over 0.15 s; vignette +0.08 over 0.3 s | Step-in over 0–0.20 s: stand 0.55 m from the pane, in front of the impact centre (≤ 0.65 m fwd, ≤ 0.25 m lateral, walk speed, swept) | `Snapshot/Closeup` NEW (shared with Unlock); stress loop |
| 0.20–0.29 | Wind-up 1 | fwd 0.00, yaw +8, roll +3, pitch −1 (chin up) | — | `Foley/Player/StrikeWindup` NEW, optional (cloth) |
| 0.29–0.35 | Strike 1 | fwd +0.08, yaw +3, roll +1, pitch 0 (ease-in) | — | — |
| **0.35** | **Impact 1** | Recoil 0.025 m (spring); shake 0.5° / 0.15 s | Stage 1 cracks at the centre; **object stop 33 ms**; chips | **Crack1** (exists) |
| 0.35–0.49 | Recover | Back to the brace pose | Cracks creep with progress | stress roughens |
| 0.49–0.64 | Wind-up 2 | fwd −0.01, yaw +9, roll +3.5, pitch −1.5 | — | windup (opt.) |
| 0.64–0.70 | Strike 2 | fwd +0.10, yaw +4, roll +1 | — | — |
| **0.70** | **Impact 2** | Recoil 0.03 m; shake 0.7° / 0.18 s | Stage 2: radials to the frame plus rings; **object stop 40 ms**; the reflection breaks into facets (§4) | **Crack2** (exists) |
| 0.70–0.84 | Recover | Brace, with drop deepening to 0.08 | — | stress peaks |
| 0.84–0.94 | Wind-up 3 | fwd −0.02, yaw +10, roll +4, pitch −2 | — | windup (opt.) |
| 0.94–1.00 | Strike 3 | fwd +0.12, yaw +3, roll +0.5 | — | — |
| **1.00** | **Shatter** | Follow-through to fwd +0.16 in 0.05 s (no resistance left). FOV punch −3° (to −8°) in 0.05 s. Shake 1.5° / 0.30 s. CA pulse 0.06 → 0.16 → 0.06 over 0.25 s | Full crack network lit; **object stop 50 ms**; then inner pieces fly outward (2–4 m/s), middle pieces drop with a 0–300 ms stagger, teeth stay (audit §3.5) | **Shatter** (exists); `GlassBroken` + `WindowShattered` |
| 1.05–1.17 | **Flinch** | fwd +0.06, drop 0.08, yaw +12, roll +1, pitch +5 (ease-out, startle) | Pieces in flight | `Foley/Player/Flinch` NEW, optional (breath) |
| 1.17–1.40 | **Look** | fwd 0.00, drop 0.04, yaw 0, roll 0, pitch +6 (on the sill and teeth); FOV back to −5° | Shards land about 1.35–1.65 (real contacts) | ShardLand NEW |
| 1.40–1.65 | **Release** | Every offset to 0, FOV to the player's, vignette out (cubic) | Settle | snapshot released at 1.30 |

**Input lock and the chase**

| Window | Move | Look | Ends early when |
|---|---|---|---|
| 0.00 → release of E or 1.00 | locked (the hold) | free in a ±5° additive cone | E released (cancel); Relay chase or sight demotes the shot (§5.0) |
| 1.00–1.10 (hard) | locked | locked | Player input cannot end it. Chase, sight or Caught can: a chase or sight skips straight to release (0.12 s) |
| 1.10–1.30 (soft) | soft-locked: any WASD ends the shot (offsets out in 0.15 s) | soft-locked: mouse beyond 3° ends it | climb start (0.1 s hand-off); chase or sight |
| 1.30 / 1.40 | move returns | look returns (0.15 s blend) | — |

- **Lock budget after the shatter:** 0.10 s that player input cannot end. That is 0.26 m of approach by a Relay still hunting toward the noise; a chase or sight ends it at once. The soft 0.20–0.30 s only plays for a player who is not moving and not being chased.
- **Slow-motion switch (A/B, default OFF).** Shards and dust at 0.6× for 0.15 s, ramping to 1× by +0.45 s. Landing moves from about 1.49 s to about 1.61 s. It never runs during a chase.

**Arm/tool option: a "sleeve flash"**
- **What it is.** A rigid forearm and elbow in a 1990 shirt sleeve enters lower right for 4–6 frames on each strike (about 0.29–0.45, 0.64–0.80 and 0.94–1.10 s).
- **What it adds:**
  - "I hit it" is unmistakable;
  - scale;
  - with ray tracing, the sleeve also appears in the glass.
- **What it costs:**
  - a hero LOD0 that holds up at 0.3 m (standing order);
  - 3 strike poses and 1 flinch pose (rigid, code-moved, no Animator), lit to match the room;
  - a viewmodel layer through a Render Objects pass so it never clips (S44);
  - per-frame ray-tracing registration and a depth-tested composite (R2/R3).
- **Risk.** A rigid arm can look like a mannequin. Valve's experience says players don't miss arms [M18].
- **Better highest-spec route.** The reflection-only body (§4), which shows the body only where a real window would.

**Motion sickness: medium-low**
- **Peak rates.** The strikes rotate about 80°/s for 60 ms; the shatter shake is 1.5°.
- **Fore-aft motion.** It is three strikes at about 2.9 Hz, well above the 0.2–0.4 Hz band [M14], plus one flinch.
- **Roll.** It stays ≤ 4° and is held for under 1 s.
- **Setting scaling:**
  - **Off:** no step-in and no pose; the shot plays in place, with object stop and sound only. Control returns at 1.0.
  - **50%:** the step-in still happens (it is the same as walking), and every angle, offset and FOV value is halved.
  - **Reduce flashing:** the CA and vignette pulses are off.

### 5.3 Design 3 — "Zoom and slow-mo" (the most cinematic)

**What the player sees:**

1. The body steps up square to the pane; nothing turns away.
2. Over the hold the view zooms in steadily, like a camcorder's zoom rocker, and smaller strikes land on the beats.
3. At the shatter the glass hangs for a beat, then falls in slow motion while the view zooms back out and tilts down to follow the shards to the sill and floor.
4. It then tilts up through the empty frame to the hall beyond, and returns control at 2.25 s.

| t (s) | Camera | Glass / time | Sound |
|---|---|---|---|
| 0.00–0.20 | Step-in as in Design 2; drop 0.05; square to the pane (yaw 0, roll 0) | — | snapshot |
| 0.10–1.00 | Power zoom: FOV −10° at a constant rate after a 0.15 s ease-in. Jabs fwd +0.05 / +0.06 / +0.08 on the beats; shakes 0.4° / 0.6° | Stage 1 and 2 cracks; object stops 33 / 40 ms | Crack1, Crack2 |
| 1.00 | Shake 1.2° / 0.3 s; no FOV punch (the zoom-out replaces it) | **Object stop 70 ms**; shards and dust run at **0.35× for 0.30 s**, ramping to 1× by 1.80 s (ease-in) | Shatter; room tone −6 dB 1.00–1.80 (the sound chat may soften the tail) |
| 1.05–1.55 | Zoom out: FOV −10° → −2° (ease-out); tilt down to pitch +12° following the shards | Shards land about 1.85–1.95 s | ShardLand at real contacts |
| 1.55–1.95 | Tilt up to pitch −2°, fwd +0.05: looking through the empty frame at the far side | Settle | — |
| 1.95–2.25 | Release (cubic) | — | snapshot out |

- **Lock:**
  - move: hard to 1.30, then soft to 1.95;
  - look: locked to 1.95 (cone ±3°), then a 0.20 s blend.
- **Chase and sight:** as in Design 2. Slow motion and the tilt are skipped, and control returns in 0.12 s.
- **Lock budget:** 0.30 s after the shatter that player input cannot end (0.78 m of a hunting Relay's approach; a chase or sight still ends it at once). The soft lock lasts up to 0.95 s.
- **Arm/tool option.** Swing a wall-mounted fire extinguisher, the period-correct way to break an office window.
  - Adds: a physically convincing break.
  - Costs: a pickup and hold system, a two-handed swing clip (needs the Animation module), extinguishers placed near windows, and a new verb. It breaks language B.
- **Motion sickness: medium-high.** There is a forced look of nearly 1 s, a 12° tilt down and back (one slow pitch cycle), a 10° zoom, and slow motion that disconnects the image from the player's rhythm.
  - **Off:** no zoom and no tilt. Slow motion stays, because it is object-only.
  - **50%:** zoom −5°, tilt 6°.
- **Era fit:** mixed. The power zoom is something a 1990 camcorder could do (my judgement; worth keeping for language C). Slow motion is a film device.

---

## 6. Comparison and recommendation

| | `Unlock` (reference) | `Glass` (current) | 1 Shove | **2 Brace, strike, flinch** | 3 Zoom and slow-mo |
|---|---|---|---|---|---|
| Authored pose | Dip 0.25 m, pitch 38° | none | none | Step-in plus brace (drop 0.06–0.08, yaw 6–10° away, roll 2–4°) | Step-in plus square framing |
| Beats | Key, turn, bolt | 3 shoves | 3 shoves plus object stop | 3 coiled strikes plus object stop | 3 jabs under a zoom |
| FOV | −14° over ≥ 0.35 s | −3° / −3° punch | same | −5° pose / −3° punch | −10° zoom, out to −2° |
| Payoff | Bolt jolt, ajar 10° | Shake 1.5° | Shake 1.5° | Follow-through, flinch, look | Hang, slow-mo fall, tilt, reveal |
| Duration | 1.55 s | 1.0 s (+0.3 s additive) | 1.0 s (+0.3 s) | **1.65 s** | 2.25 s |
| Lock after the payoff (hard / soft) | 0.59 s move, 0.44 s look (after the 0.86 s commit) | 0 | 0 | **0.10 / 0.30–0.40 s** | 0.30 / 0.95 s |
| Chase rule | Frees the player after the commit | Relay sight cancels | Hold continues | Demote, or skip the aftermath | Demote, or skip |
| Reads as a cutscene | yes | no | no | **yes** | most |
| Sickness risk | medium | low | low | **medium-low** | medium-high |
| Era fit (1990 found footage) | good | good | good | **good** | mixed |
| Build | Map rig plus anchors | Map rig | Map rig | **Map rig plus step-in plus soft lock** | plus local slow-mo, zoom, tilt |

**Recommendation: Design 2.** Reasons:

1. It has the shape Red already approved in the head dip (pose, object acts, payoff, return), sized for a violent action at eye height.
2. Every move is motivated by the body or the glass (§2.2), so it reads as a body acting, not as shake. That answers "looks fake" from the camera side.
3. It costs a hunted player only 0.10 s after the loudest noise in the game. The rest is skippable, and a chase removes it entirely.
4. It needs no hands, no Animator and no new verbs.
5. It shows off the real fracture: the object stop shows the crack network, and the follow-through and look frame the pieces and teeth. With ray tracing it also shows the faceted reflection.

Design 3's slow motion becomes Design 2's A/B switch, and its power zoom is parked for language C.

---

## 7. Proposed values for the map chat's `FrontRoomsShotTimings`

This replaces `Glass`. All values are ESTIMATES to tune on a capture; the beats are the sound chat's and are unchanged.

```csharp
// ---- 3.5 Hold to break glass: "Brace, strike, flinch" (replaces Glass). Visual chat proposal, 2026-10-03.
// Offsets are additive to BaseEye and are TARGETS: fwd/drop in metres; yaw + = away from the striking (right) side,
// roll + = toward the striking shoulder, pitch + = down. Hold progress drives t up to Shatter; real time after.
public static class GlassBreak
{
    public const float HoldSeconds = 1.0f, Crack1 = .35f, Crack2 = .70f, Shatter = 1.0f; // sound chat's beats
    public const float Reach = 1.2f;                       // pane prompt range (was the shared 2.4 m) -- needs Red
    public const float StandDistance = .55f, StepInMaxForward = .65f, StepInMaxLateral = .25f, StepInSeconds = .20f;
    public const float PoseIn = .25f, PoseFovDeg = -5f, PoseFov = .40f, LookCone = 5f, LookAtMaxYaw = 6f, LookAtMaxPitch = 8f;
    public const float BraceFwd = .03f, BraceDrop = .06f, BraceDropAfterCrack2 = .08f, BraceYaw = 6f, BraceRoll = 2f;
    public static readonly float[] WindupStart = { .20f, .49f, .84f }, StrikeStart = { .29f, .64f, .94f };
    public static readonly float[] WindupFwd = { 0f, -.01f, -.02f }, WindupYaw = { 8f, 9f, 10f },
                                   WindupRoll = { 3f, 3.5f, 4f }, WindupPitch = { -1f, -1.5f, -2f };
    public static readonly float[] StrikeFwd = { .08f, .10f, .12f }, StrikeYaw = { 3f, 4f, 3f }, StrikeRoll = { 1f, 1f, .5f };
    public static readonly float[] Recoil = { .025f, .03f, 0f }, ShakeDeg = { .5f, .7f, 1.5f }, ShakeDecay = { .15f, .18f, .30f };
    public static readonly float[] ObjectStop = { .033f, .040f, .050f }; // glass only; the camera never stops
    public const float RecoilOmega = 40f, ShakeNoiseHz = 16f;
    public const float FollowThroughFwd = .16f, FollowThrough = .05f, ShatterFovPunchDeg = -3f, ShatterFovPunch = .05f;
    public const float FlinchStart = 1.05f, FlinchEnd = 1.17f, FlinchFwd = .06f, FlinchDrop = .08f, FlinchYaw = 12f, FlinchRoll = 1f, FlinchPitch = 5f;
    public const float LookEnd = 1.40f, LookDrop = .04f, LookPitch = 6f, ReleaseEnd = 1.65f;
    public const float HardLockEnd = 1.10f, MoveSoftLockEnd = 1.30f, LookSoftLockEnd = 1.40f, LookBlendBack = .15f, SoftBreakLookDeg = 3f;
    public const float CancelBlend = .20f, ChaseSkipBlend = .12f, ChaseDemoteScale = .5f, ClimbHandOff = .10f, CancelRelayDistance = 6f;
    public const float Vignette = .08f, CaPulsePeak = .16f, CaPulse = .25f;               // CA off with Reduce flashing
    public const float ImpactMinFromFrame = .2f;
    public const float ShardSlowMoScale = .6f, ShardSlowMo = .15f, ShardSlowMoRampEnd = .45f; // A/B switch, default OFF
    public const float TapProgress = .35f, TapCooldown = .3f;  // tap mode: one tap = one strike, no wind-up delay
    public const float ShardLandMin = .35f, ShardLandMax = .60f, SettleToStatic = 1.5f;    // unchanged from Glass
}
```

---

## 8. Asks

**Red (decisions)**

1. Design 2 as the glass shot, or Design 3? Optionally A/B Design 2's slow-motion switch on a capture.
2. Hands or not. The default follows the W8 answer: no hands. The upgrades are the sleeve flash (§5.2) or the reflection-only body (§4, desktop ray tracing only).
3. Change the pane prompt range from 2.4 m to 1.2 m, and add a step-in of at most 0.65 m.
4. The Relay's sight or a chase no longer cancels the hold; it only demotes the camera. Today's audit text says sight cancels.

**Map chat (camera rig owner)**

1. Rig features:
   - a swept body step-in toward a stand point;
   - a soft lock (any move input or a 3° mouse move ends the shot);
   - a demote tier (Design 1 values at 50%);
   - an instant hand-off to the climb camera.
2. Choose the fracture variant / impact centre at E-down, and pass it with the hold. Either add `GlassHoldStarted(window, impactCentre, seed)` or add the centre to `GlassHold`.
3. `GlassBreak` replaces `Glass` in `FrontRoomsShotTimings`.
4. Keep `GlassBroken` at 1.0 s, and add `WindowShattered` (already proposed).

**Sound chat**
- The beats are unchanged.
- Optional NEW events: `Foley/Player/StrikeWindup` at 0.20 / 0.49 / 0.84 and `Foley/Player/Flinch` at 1.05.
- Share `Snapshot/Closeup` with the Unlock shot.
- If the slow-motion switch is adopted, `ShardLand` should follow real contacts (it does if it is contact-driven).

**Visual chat (glass and G14)**

1. The fracture player supports the object stop: pieces spawn held, release after the stop, and a playback rate is available for slow motion.
2. Fix R1–R4 in the ray-tracing production pass. R1 is the one that would break this shot visibly.
3. Prototype the reflection-only body, if Red wants it.
4. Shot post: a vignette and CA pulse API (audit F6).

**Fracture reports 01/02/04**
- Impact-centre error ≤ 0.10 m from the aim point. Alternatively, start the stage cracks at the true aim point; the 3 × 3 grid alone allows up to about 0.27 m.

---

## 9. Open items and UNVERIFIED

**Talks and references not fully checked**
- **Eiserloh's rotational-only and trauma recipe** come from secondary summaries. The GDC video [M4] was not watched.
- **Nesky's numbered list** comes from a transcription [M3]. Only the title and description were read on the Vault and Game Developer pages.
- **Embracing Push Forward Combat in DOOM** (Loudy and Campbell, GDC 2018) [M2]: only the title and speakers are verified. Glory-kill invulnerability is UNVERIFIED.
- **Missing sources:**
  - a Call of Duty window-break interaction;
  - Outlast 2 / Trials door or window takeovers;
  - Amnesia: Rebirth hand animations;
  - the "Art of Screenshake" talk by Jan Willem Nijman. Its hit-stop number is from an RPS interview summary [M10].
- **Partly read:**
  - Firewatch body details [M28];
  - the Alien: Isolation quote [M27], via a search summary because the article body was unreadable;
  - Dishonored's "throw up" quote, seen only in a search snippet [M25].
- **Games and Culture slow-motion article** [M29]: the title and authors were not seen (paywall). Only the abstract framing comes from a search summary.

**Design numbers and judgement calls**
- **Every timing, angle and distance** in §5 and §7 is an ESTIMATE, to tune on a 10-second capture per design.
- **Three judgement calls:**
  - a 1990 camcorder cannot do slow motion but can power-zoom;
  - a first-person whole-frame freeze reads as a hitch;
  - a flinch reads as natural rather than weak.

**Code and performance**
- **The §4 ray-tracing findings** are from reading code, not running it. G14's runtime probe should confirm R1–R4.
- **Cost of per-frame TLAS updates** for ≤ 256 instances on the M3 Max is not measured.
- **Line numbers** in `FrontRooms3DGame.cs` and `FrontRoomsMapWorld.cs` were read on 2026-10-03 and drift while the map chat edits.

---

## 10. Sources

New in this report (M):

- **M1** — "The Guts and Gore of DOOM Glory Kills", Bethesda.net (Robert Duffy, Marty Stratton, id Software), 2016 (date not shown in the text read). https://bethesda.net/ja-JP/news/the-guts-and-gore-of-doom-glory-kills
- **M2** — "Embracing Push Forward Combat in DOOM", Kurt Loudy and Jake Campbell (id Software), GDC 2018. https://gdcvault.com/play/1024940/Embracing-Push-Forward-Combat-in (title and speakers only)
- **M3** — "50 Game Camera Mistakes", John Nesky (thatgamecompany), GDC 2014. Vault: https://gdcvault.com/play/1020460/50-Camera ; video: https://www.youtube.com/watch?v=C7307qRmlMI ; Game Developer page (2015-11-17): https://gamedeveloper.com/design/video-50-common-game-camera-mistakes----and-how-to-fix-them ; numbered list via a transcription: https://t.me/s/disdoc/71
- **M4** — "Math for Game Programmers: Juicing Your Cameras With Math", Squirrel Eiserloh (SMU Guildhall), GDC 2016. Video: https://www.youtube.com/watch?v=tu-Qe66AvtY ; Game Developer summary: https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math ; secondary trauma/noise implementation that credits the talk: https://discourse.threejs.org/t/camera-shake-or-much-damage-such-wow/8963
- **M5** — "The Cameras of Uncharted 3", Travis McIntosh (Naughty Dog), GDC 2012. https://gdcvault.com/play/1015514/The-Cameras-of-Uncharted (session description)
- **M6** — "How God of War's cinematography went beyond its no-cut camera", Michael Leri, GameRevolution, 2019-04-17 (Dori Arazi, Santa Monica Studio). https://www.gamerevolution.com/features/525735-god-of-war-cinematography-explained ; Arazi's GDC 2019 cinematography talk is noted at https://www.gameanim.com/2021/08/17/creating-a-deeper-emotional-connection-the-cinematography-of-god-of-war/
- **M7** — "Hellblade development diary 6: Camera, controls, and hardcore combat", Digitally Downloaded, 2014-11 (Ninja Theory dev diary). https://www.digitallydownloaded.net/2014/11/hellblade-development-diary-6-camera.html
- **M8** — Steve Swink, *Game Feel: A Game Designer's Guide to Virtual Sensation*, Morgan Kaufmann 2008. "Game Feel: The Secret Ingredient", Gamasutra/Game Developer, 2007: https://www.gamedeveloper.com/design/game-feel-the-secret-ingredient ; polish definition as quoted at https://en.wikipedia.org/wiki/Game_feel
- **M9** — "Juice It or Lose It", Martin Jonasson and Petri Purho, GDC Europe 2012 (search summary only). https://www.gamedeveloper.com/design/video-is-your-game-juicy-enough-
- **M10** — "Making Game 'Feel'", infovore.org, summarising Graham Smith's Rock Paper Shotgun interview with Jan Willem Nijman (Vlambeer), October 2013. https://infovore.org/?p=5275
- **M11** — "Eight Hit Stop Techniques", Masahiro Sakurai on Creating Games (YouTube), December 2022, as summarised in "This Week in Sakurai", Nintendo Wire, 2022-12-12. https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/
- **M12** — Xbox Accessibility Guideline 117, "Visual distractions and motion settings", Microsoft Learn (page dated 2022-05-09). https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/117
- **M13** — Game Accessibility Guidelines, "Avoid (or provide option to disable) any difference between controller movement and camera movement". https://gameaccessibilityguidelines.com/avoid-or-provide-option-to-disable-any-difference-between-controller-movement-and-camera-movement/ (= S19)
- **M14** — C. Diels and P. Howarth, "Frequency Characteristics of Visually Induced Motion Sickness", *Human Factors* 55(3):595–604, 2013. https://repository.lboro.ac.uk/articles/journal_contribution/Frequency_characteristics_of_visually_induced_motion_sickness/9346865
- **M15** — "How Mirror's Edge fights simulation sickness", Ross Miller, Engadget/Joystiq, 2008-07-17 (DICE). https://www.engadget.com/2008/07/17/how-mirrors-edge-fights-simulation-sickness/
- **M16** — "How Mirror's Edge gave legs (and more) to Battlefield 3", Ben Gilbert, Engadget, 2012-08-13 (Karl Magnus Troedsson, DICE, GDC Europe 2012). https://www.engadget.com/2012-08-13-how-mirrors-edge-gave-legs-and-more-to-battlefield-3.html
- **M17** — "Developing Dying Light's Iconic Dropkick Move", 80 Level, 2023-03-16 (Bartosz Kulon, Techland). https://80.lv/articles/developing-dying-light-s-iconic-dropkick-move
- **M18** — "Valve Talks Half-Life: Alyx And Why Arms Don't Work In VR", Game Informer, 2020-03-23 (Robin Walker). https://www.gameinformer.com/index.php/interview/2020/03/23/valve-talks-half-life-alyx-and-why-arms-dont-work-in-vr (= S15)
- **M19** — "Resident Evil Village and first-person video game immersion: why hands create intense connection", Christina Fawcett (University of Winnipeg), The Conversation, 2021. https://theconversation.com/resident-evil-village-and-first-person-video-game-immersion-why-hands-create-intense-connection-161566
- **M20** — "Capcom Trying To Make Sure Resident Evil 7 VR Won't Make You Sick", Jamie Feltham, UploadVR, 2016-08-23 (Masachika Kawata, Capcom). https://uploadvr.com/capcom-trying-make-sure-resident-evil-7-vr-wont-make-sick/
- **M21** — "Resident Evil 4 Remake Gameplay Changes Include New Parry Mechanic to Replace QTEs…", Salman Haider Zaidi, MP1st, 2023-02-28 (Kazunori Kadoi, Yasuhiro Ampo, Capcom). https://mp1st.com/news/resident-evil-4-remake-gameplay-changes-include-new-parry-mechanic-to-replace-qtes-quick-dodge-stealth-rework-more
- **M22** — The Last of Us Part II glass:
  - "How Naughty Dog Created the Immersive World of The Last of Us Part II", 80 Level, 2020-12-08 (Michael Fadollone, Neilan Naicker). https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/ (= S34)
  - Anthony Newman interview, Chris Garcia, One More Game, 2020-06-01. https://onemoregame.ph/?p=70076
  - "The Last of Us Part 2 – 20 Tiny But Amazing Details", Shubhankar Parijat, GamingBolt, 2020-06-25. https://gamingbolt.com/the-last-of-us-part-2-20-tiny-but-amazing-details-you-may-have-missed/3
- **M23** — "Modern Warfare 2" review, FutureFive NZ, 2010-01-01 (breach-and-clear slow motion). https://futurefive.co.nz/story/modern-warfare-2
- **M24** — "Call of Duty: Modern Warfare Executions, 'Realism' Option, Door Breaching & More Detailed", Alex Co, MP1st, 2019-08-07. https://mp1st.com/news/call-of-duty-modern-warfare-executions-realism-option-door-breaching-more-detailed
- **M25** — "Dishonored VR? Arkane is thinking about it", UploadVR, 2016-10-18 (Christophe Carrier, Arkane, via GamesRadar). https://www.uploadvr.com/dishonored-vr-arkane/
- **M26** — "Amnesia: The Bunker shows another gameplay encouraging creative problem solving", Juan Camilo Arroyave Guevara, LevelUp, 2022-12-29: https://www.levelup.com/en/news/717905/Amnesia-The-Bunker-shows-another-gameplay-encouraging-creative-problem-solving ; Wikipedia, "Amnesia: The Bunker": https://en.wikipedia.org/wiki/Amnesia:_The_Bunker
- **M27** — Alistair Hope (Creative Assembly), "Building Fear in Alien: Isolation", GDC 2015, as reported by GamesRadar, "Here's why Alien: Isolation's third-person mode was scrapped" (search summary; article body unreadable). https://gamesradar.com/alien-isolation-third-person
- **M28** — "Firewatch is a freak of nature in third-person", GamesRadar (Olly Moss, Campo Santo; search summary only). https://gamesradar.com/firewatch-third-person
- **M29** — Article on slow motion in videogames ("cinematic slow motion" vs "bullet time"), *Games and Culture*, 2022, DOI 10.1177/15554120221090974 (title and author UNVERIFIED; abstract via search). https://journals.sagepub.com/doi/10.1177/15554120221090974

Reused from `interaction_audit/04_aaa_references.md` (S):

- **S4** — Steam forum thread on Alien: Isolation's maintenance-jack animation. https://steamcommunity.com/app/214490/discussions/0/600766503721133225
- **S6** — Dread Central, Outlast review, Gareth Jones, 2013-09-10. https://www.dreadcentral.com/reviews/47973/outlast-video-game/
- **S8, S9** — Wikipedia, Amnesia: The Dark Descent / Penumbra: Overture. https://en.wikipedia.org/wiki/Amnesia:_The_Dark_Descent ; https://en.wikipedia.org/wiki/Penumbra:_Overture
- **S12** — "Creating First Person Movement for Mirror's Edge", Tobias Dahl and Mikael Lagre (DICE), GDC Vault (2009). https://gdcvault.com/play/1012171/Creating-First-Person-Movement-for
- **S13** — Game Anim blog on the Mirror's Edge talk, 2010-11-05. https://www.gameanim.com/?p=2058
- **S14** — "The vaulting dead", MCV/Develop, 2016-05-18 (Binkowski, Kulon, Techland). https://www.mcvuk.com/development-news/the-vaulting-dead-implementing-first-person-parkour-in-dying-light/
- **S20** — Game Accessibility Guidelines, holding buttons. https://gameaccessibilityguidelines.com/avoid-provide-alternatives-to-requiring-buttons-to-be-held-down/
- **S25** — Twinfinite, E3 2016 Resident Evil 7 preview, Zhiqing Wan, 2016-06-19. https://twinfinite.net/features/e3-2016-resident-evil-7-preview/
- **S26** — PC Gamer, "Why I love watching my hands in first-person games", Tom Senior, 2017-01-25. https://www.pcgamer.com/why-i-love-watching-my-hands-in-first-person-games/
- **S27** — PC Gamer, "The weighty doors and switches of Soma", Tom Senior, 2015-10-07. https://www.pcgamer.com/the-weighty-doors-and-switches-of-soma/
- **S28** — PC Gamer, Outlast preview, Cassandra Khaw, 2013-03-29. https://www.pcgamer.com/outlast-preview/
- **S29** — Geek Culture, Outlast PS4 review, 2014-02-15. https://geekculture.co/geek-review-outlast-playstation-4
- **S31** — BFI, "Half-Life 2: 20 years", Jacob Heayes, 2024-11-15. https://www.bfi.org.uk/features/half-life-2-20-years-valve-shooter
- **S40** — Wikipedia, The Order: 1886. https://en.wikipedia.org/wiki/The_Order:_1886
- **S41** — Wikipedia, Standard-definition television. https://en.wikipedia.org/wiki/Standard-definition_television
- **S44** — Unity manual, Render Objects renderer feature. https://docs.unity3d.com/Manual/urp/renderer-features/renderer-feature-render-objects.html

General reference (not re-read): Frank Thomas and Ollie Johnston, *The Illusion of Life: Disney Animation*, 1981 (anticipation, follow-through).

Project files read (not edited):
- `Assets/Scripts/FrontRooms3DGame.cs`, `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs`, `Assets/Scripts/FrontRoomsHunter.cs`
- `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs`, `Assets/Scripts/Rendering/FrontRoomsMetalGlassRTRendererFeature.cs`, `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`, `NativePlugin/FrontRoomsMetalGlassRT.mm`
- From the clone `proj_glass`: `Assets/Resources/Rendering/FrontRoomsGlass.shader` and `Assets/Scripts/Rendering/FrontRoomsGlassPane.cs`
