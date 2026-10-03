# 03 — The Relay (Hunter) redesign: gameplay and tech constraints

Research strand: gameplay-tech. Date: 2026-10-02. Status: COMPLETE.

Scope: the hard numbers the new Hunter model must meet (from the project code and docs), what each behaviour state must show, readability in the two zone grades, the performance budget, animation pipeline options, the name "Relay" as a design hook, and how strong indie horror games keep one enemy readable and scary on a budget. Ends with a constraint checklist and a scoring rubric for the concept round.

Citation rule: project facts cite the file and line. Web claims cite URLs fetched during this pass. Anything not fetched is marked UNVERIFIED. No existing creature design is copied; references are studied for principles only.

## 0. Summary

1. **The current rig is broken, not just spindly.** Measured from `FrontRoomsRelayRig.BuildRig`, it is wrong in four ways (§1.2):
   - The head reaches 3.1 m and goes through the ceiling. It is 2.05 m allowed.
   - About 0.8 m of the legs is under the floor.
   - The torso floats 0.46 m above the thighs.
   - The arms are hanging capsules spread 2.6 m wide.

   The autopilot captures `Verification/main-autopilot/02_relay.png` and `05_play_28s.png` show this. Any new model must be authored to the module spec first.
2. **Hard numbers:**
   - top ≤ 2.00 m at rest and ≤ 2.05 m in motion;
   - face at ~1.6 m, on the sight ray and the player's eye line;
   - body inside a 0.6 m cylinder;
   - visual half-width ≤ 0.5 m at the shoulders, to pass a 1.0 × 2.1 m door;
   - a stoop for broken windows (head 2.0, sill 0.35);
   - clear of 2.4 m ceilings.

   The hunch is therefore functional: a ~2.0 m body with its face at 1.6 m.
3. **States** (§2): Listen is the first silhouette after every relay, so it must be the strongest still pose. Search needs its own pose. BreakDoor is mostly heard; design a reveal frame in the doorway. Stagger has no trigger yet.
4. **Gait speed.** The Hunt walk at 2.6 m/s is above the walk-to-run Froude limit for a human-proportioned 2 m body (Fr ≈ 0.65). Either make the run-speed walk the uncanny trait or lower it to ~2.2 m/s. Long legs would bring back the spindly look.
5. **Readability** (§3): in-game values show the dark body reads on yellow Level 0 paper (4 : 1), but the pale head does not (1.2 : 1). In the planned low-key Office the dark body vanishes (~1 : 1). Keep a two-value split, with a dark frame round the head, a rim term on the body, and no information in hue. The practical limit is the 16 m light radius, not fog.
6. **Budget:**
   - one skinned mesh renderer (today: 16 renderers);
   - 8–12 k triangles (15 k cap);
   - 2–3 materials (4 cap);
   - 24–36 bones, 1–2 influences for rigid parts and at most 4 elsewhere;
   - no blend shapes or cloth.

   WebGL skins on the CPU.
7. **Pipeline** (§5):
   - **Now:** one authored skinned mesh driven by the existing procedural rig, with rigid or semi-rigid segments so mechanical motion looks intended.
   - **Later:** Blender clips through a Generic Animator.
   - **Optional:** 2–3 Animation Rigging constraints.
   - **Mixamo/Humanoid:** reference only. The licence is royalty-free, but raw files cannot be redistributed, so keep them out of a public repo.
8. **"Relay" is the AI's own description** (§6). The word first meant fresh hounds placed along the line of a chase, which is what `Arrive` does. That gives five hooks:
   - a creature that never tires;
   - one unit of many (copy-paste world logic);
   - latched, clicking motion in Listen and Search;
   - a relay-click sound signature;
   - a face read as a contact gap.
9. **Indie horror lessons** (§7): one silhouette, one sound signature and one learnable rule. Ration the body (doorways, flicker, reveals), use a rim light in the dark, share the rig, and use camera reactions. Design inside the collision body from the start.
10. **Tools:** a pass/fail checklist (§8) and a weighted 100-point rubric (§9) for the concept round.

## 1. What the code and docs fix (derived constraints)

### 1.1 Body, clearances and sight (binding numbers)

Source of truth: `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs` line 92 (`RelayRadius = .3f, RelayHeight = 2.05f, RelayEye = 1.6f`), `LEVEL_MODULE_SPEC.md` §2, §3, §7, and `FrontRoomsMapHunter.cs` lines 25–36.

| Constraint | Value | Where it comes from | What it means for the model |
|---|---|---|---|
| Collision body | capsule r 0.30 m, tested from 0.40 to 1.95 m above the feet | `FrontRoomsMapHunter.cs` l.28 (`ProbeBottom = .4f, ProbeTop = 1.95f`) | The navigable body is a 0.6 m cylinder. Anything wider (shoulders, elbows, a coat hem) is visual only and will clip walls and jambs. |
| Height while moving | ≤ 2.05 m (`RelayHeight`) | `ModuleUnits` l.92; spec §7 "≤ 2.05 m tall while walking, or it stoops" | The highest point of the walk and run cycles, including head bob, must stay ≤ 2.05 m. Author the rest pose at ≤ 2.00 m so a 3–5 cm bob still clears. |
| Door opening | 1.00 × 2.10 m, leaf 0.98 × 2.08 × 0.05 | spec §3 | Head and shoulders must pass a 2.10 m head with the body off-centre by up to 0.20 m (1.0 opening − 0.6 body, halved). Visual half-width ≤ 0.50 m at shoulder height is the safe line, so shoulders plus arms ≤ ~0.90 m at the widest pose. |
| Arch (doorless) | 1.1–1.8 m wide, top 2.20 m | spec §3 | Easier than a door; no extra rule. |
| Broken window | 1.4 m wide, sill 0.35 m, head 2.00 m | spec §3; `FrontRoomsMapHunter.cs` l.26–27 comment | The body probe passes, but the visual legs will clip a 0.35 m sill and a 2.05 m head clips a 2.00 m window head. Needs either a stoop/step-over pose or a design where the clip is hidden (checklist G1.6). |
| Ceilings | Low 2.4 m (35 % of the map), Standard 2.9 m (55 %, all Office), Tall 5.4 m (10 %) | spec §2 Heights; `FrontRoomsLevel0.asset` (`lowShare 0.35`, `standardShare 0.55`, `tallShare 0.1`) | In Low zones the head is 0.35 m under the ceiling and about 0.3 m from a downward spot (lamp drop 0.06 m, troffer drop 0.02 m, spec §4): the head will pass through hot top light. |
| Sight | a ray from the Relay's eye at 1.60 m to the player's eye at 1.62 m, range 12 m | `ModuleUnits` l.92; `FrontRoomsMapHunter.Sees` l.729–734; `FrontRoomsHunter.cs` l.22 (`sightRange = 12f`) | The "face" the player reads should sit at or just above 1.60 m. A 2.0 m creature with a face at 1.6 m is hunched by construction: the stoop is the gameplay eye height, not a style choice. |
| Sight blockers | walls, shut doors, columns, colliders with a top ≥ 1.65 m; desks and 1.57 m cubicle panels do not block | spec §7 | Over a 1.57 m panel the player sees the Relay from about the upper chest up. The head and shoulders are the silhouette that must read over furniture. |
| Catch | 0.70 m flat distance while it sees the player | `FrontRoomsHunter.cs` l.24; `FrontRoomsMapHunter.cs` l.195 | The last frame before "caught" is the Relay at 0.7 m (see §2.2 for what fills the screen). |
| Player | capsule 1.75 × r 0.30, eye 1.62, walk 3.2, sprint 5.5 m/s for 5 s, 72–76° vertical FOV | spec §7; synthesis §0 decision 11 | Relay must read as taller than the player by a clear margin (2.0 vs 1.75), but not so tall that its head leaves frame at chase distance. |

### 1.2 The current rig breaks these numbers (measured)

I evaluated the rest pose that `FrontRoomsRelayRig.BuildRig` (l.146–190) and `TickAnimation` (Idle: spine −9°, chest −4°, upper arms ±7° roll, forearms 12°) produce, using Unity primitive sizes (capsule 2 × r 0.5, sphere ⌀ 1, cube 1). The scene serialises the same offsets (`Scenes/FrontRooms3D.unity`, `bodyScale: 1`, Hunter scale 1).

| Part | World height (feet at y = 0) | Problem |
|---|---|---|
| Head sphere | 2.31 – 3.11 m | 1.06 m over the 2.05 m limit; pierces a 2.4 m and a 2.9 m ceiling; cannot pass a 2.1 m door head |
| Head bone (visual "eye") | 2.71 m | 1.11 m above the gameplay eye (1.60 m) |
| Torso capsule | 1.07 – 2.70 m | floats: 0.46 m gap above the thigh tops (0.61 m) |
| Thigh / shin / foot | thigh −0.47 – 0.61, shin −1.06 – 0.02, foot −0.94 – −0.80 m | leg chain is 1.71 m (0.55 + 0.60 + 0.56) under a pelvis at 0.92 m, so 0.8 m of leg is below the floor; only the thighs show |
| Arms | bones laid out horizontally (T-pose offsets along X) with vertical capsules hanging off each bone | arm span ±1.32 m (2.6 m wide): three separate hanging "sausages" per side, wider than any door |
| Spine lean | spine −9° and chest −4° about X | with the rig facing +Z (`FrontRooms3DGame.UpdateRelayRig` l.750–751), a negative X rotation leans the torso back, away from the player (head 0.24 m behind the pelvis). The "hunch" reads as a recline. (Derived from Unity's Euler convention; check in the Scene view.) |

The autopilot capture `Verification/main-autopilot/02_relay.png` shows exactly this: in an Office doorway the torso hangs from the ceiling with a yellow hand block at the ceiling line, and two thigh capsules stick out of the floor below it. This is most of why Red reads the current Relay as "spindly/odd": it is not a proportion problem alone, the parts are not connected and the figure is 3.1 m tall with its legs buried.

Rule for the redesign: the model is authored in metres, feet on y = 0, in the module spec's conventions (spec §1: Y up, front +Z, pivot at floor centre), and checked against §1.1 before any look work.

### 1.3 Behaviour states and timing

From `FrontRoomsHunter.cs` (enum l.5, tuning l.9–27, values serialised in `Scenes/FrontRooms3D.unity` l.1016–1020) and `FrontRoomsMapHunter.cs`:

| State | Speed | Duration / timing | Enters when | Rig state today (`FrontRooms3DGame.cs` l.755–759) |
|---|---|---|---|---|
| Dormant | 0 | `releaseDelaySeconds` 3 s | game start | hidden |
| Listen | 0 | `listenSeconds` 2 s, then hunts a random cell within 3 cells of the player | every release and every relay (`Arrive`, l.121, l.135); end of Search | IdleListen |
| Hunt | `huntSpeed` 2.6 m/s | until it reaches the noise or stalls 3 s | a noise within radius (sprint 26 m, door 14 m), or Listen timeout | Walk |
| Search | 0 | `searchSeconds` 2.5 s | reached the hunt goal, or stalled | IdleListen (no separate pose) |
| Chase | `chaseSpeed` 4.2 m/s (task brief allows tuning to 5.4; player sprint is 5.5) | replans every 0.35 s; gives up 1.5 s after losing sight | the sight ray hits the player within 12 m | Run (playback ×1.15) |
| BreakDoor | 0 | stands 0.45 m before the crossing line; a blow every 0.5 s (`DoorBlow` event, l.716); door breaks at 2.5 s, leaf swings 95° in 0.18 s, waits 0.25 s, resumes | a shut door on its path | BreakDoor |
| Relay (not a state) | teleport | leash check every 1 s; triggers when more than 30 cells behind outside Chase/BreakDoor | re-arrives 9–15 cells of walking away, out of the player's sight, preferably behind them, then Listen | — |
| Ghosting (flag) | moving | while it passes through furniture it found no way round | `Ghosting` property, l.93 | — |
| Stagger | — | no `HunterState` drives it | — | rig only, unused |

Footstep audio cadence (`FrontRooms3DGame.cs` l.761–764): one step every 0.44 s in Hunt and 0.29 s in Chase. Procedural gait (`FrontRoomsRelayRig.TickAnimation` l.104–116): walk 7.2 rad/s gives a 0.87 s cycle, 0.44 s per step, which matches; run 11.5 rad/s × 1.15 gives 0.24 s per step, which does not match the 0.29 s audio. A new run cycle should be timed to the audio, or the audio to it. The sound research reached the same conclusion: it measured the legs about 18 % ahead of the footsteps (`SOUND_FOLEY_MOTIF_RESEARCH.md` l.31).

Step lengths the animation must plant without sliding (root motion is off; the brain moves the body):

| | Speed | Step interval | Step length | Stride (2 steps) |
|---|---|---|---|---|
| Hunt walk | 2.6 m/s | 0.44 s | 1.14 m | 2.29 m |
| Chase at 4.2 | 4.2 m/s | 0.29 s | 1.22 m | 2.44 m |
| Chase at 5.4 | 5.4 m/s | 0.29 s (if unchanged) | 1.57 m | 3.13 m |

(sections 2 onward appended below)

### 1.4 Gait physics: the Hunt walk is a run-speed walk

The Froude number for walking is Fr = v² / (g · l), with l the leg (hip) length, and bipeds usually switch from walking to running near Fr ≈ 0.5 ([Wikipedia, Froude number](https://en.wikipedia.org/wiki/Froude_number)).

| Hip height l | Fr at Hunt 2.6 m/s | Reading |
|---|---|---|
| 1.00 m (a 1.9–2.0 m figure with human leg proportions; the ratio is approximate, UNVERIFIED) | 0.69 | a human this size would be running |
| 1.06 m | 0.65 | same |
| 1.38 m | 0.50 | the hip height needed to walk at 2.6 m/s comfortably: legs about 69 % of a 2.0 m body, which is the stilt-legged "spindly" look Red dislikes |

So there are three honest options:
1. **Keep 2.6 m/s and make the wrong gait the point.** It walks at a speed where a person would run, with long, level, unhurried steps. Mori's uncanny valley notes that movement amplifies the effect ([Wikipedia, Uncanny valley](https://en.wikipedia.org/wiki/Uncanny_valley)). This fits a creature that never tires (§6).
2. **Lower `huntSpeed` to about 2.2 m/s** (Fr ≈ 0.47 at l = 1.06) so a human-proportioned walk looks natural. That is a tuning change for the map chat.
3. **Long legs.** Rejected: it brings back the spindly read and pushes the hip, head and eye heights against the 2.05 m limit.

Chase at 4.2 m/s is a normal run for any of these leg lengths. At 5.4 m/s, steps of 1.57 m every 0.29 s need a long, low, forward-pitched stride. If the chase speed is raised, the footstep interval should drop to about 0.25 s.

## 2. What each state must show

The brain stays authoritative and the rig only shows it (`RELAY_MODEL_RIG_RESEARCH.md`, "Motion state contract"). Unity's own animation optimisation guide recommends the same split: an AI layer controls the Animator, with state tags to align the two state machines ([Unity Manual, Mecanim performance and optimization](https://docs.unity3d.com/6000.0/Documentation/Manual/MecanimPeformanceandOptimization.html)).

### 2.1 Per-state brief

| State | The player must be able to tell | Pose and motion requirement | Sound partner (existing Foley or new) | Notes from code |
|---|---|---|---|---|
| **Listen** (2 s, after every release and relay) | "It has not found me. It is listening." | Frozen, weight settled, the head turned off-axis and held. Small, slow, irregular motion only. Face at ~1.6 m. This is the pose most often seen first, so it carries the strongest silhouette of all. | none, or a slow relay tick (§6) | Today it shares IdleListen with Search. The brain does not expose the noise point; add a read-only `ListenTarget` for a head aim (§5.4). |
| **Search** (2.5 s at the end of a hunt) | "It lost the trail. It is looking around here." | Different from Listen: the torso turns, the head sweeps in steps, and it may take one or two shuffling steps in place. | a scanning click pattern | Currently identical to Listen. A distinct pose is cheap and tells the player "keep still". |
| **Hunt** (2.6 m/s walk) | "It is coming toward a sound, not toward me." | A level, purposeful walk, head forward and tilted to listen, arms held (not swinging freely). Steps of 1.14 m every 0.44 s with no foot sliding. | heavy carpet step every 0.44 s (exists) | See §1.4 on gait speed. |
| **Chase** (4.2, up to 5.4 m/s) | "It sees me. Run." | An unmistakable change in shape: the torso pitches forward, the head drops and faces the player, the stride lengthens, and the arms open or reach. Readable from behind at 12 m and through a doorway. | faster, heavier steps every 0.29 s (exists) | The rig faces the player while it sees them (`FrontRooms3DGame.cs` l.751), so the front of the model is what a chased player sees. |
| **BreakDoor** (5 blows at 0.5 s, door gives at 2.5 s) | From the player's side: "something is hitting that door" (sound and leaf shake). Then the reveal. | A 0.5 s strike loop with contact on the `DoorBlow` event. It stands with its body axis 0.45 m from the crossing line, so the front of the 0.3 m body is about 0.13 m from the leaf: hands or forearms must reach ~0.45 m forward of the spine, at 1.0–1.8 m high. The leaf swings away from it in 0.18 s and it holds for 0.25 s, so design a **reveal frame**: the Relay framed by the 1.0 × 2.1 m doorway, head near the head jamb, arms still forward. | door blow, break impact (exist) | Mostly heard, not seen: the Relay is behind a shut door for 2.5 s. |
| **Stagger** | "It was hurt or knocked off balance" (future hook) | A short, unstable recovery that breaks the silhouette's symmetry for under 1 s. | — | No `HunterState` triggers it today. Keep one pose so a later mechanic (thrown object, door slam) can use it. |
| **Relay** (teleport while unseen) | Nothing visual by definition; at most "it moved". | No animation. Arrival is followed by Listen, so the arrival pose is the Listen pose. | a single spatial relay click or clunk at the arrival point would tell the player it moved without showing it (§6) | Pop-in risk: `Arrive` tests visibility of the eye point only (centre + 1.6 m, l.243). A head or shoulders above 1.6 m could show over a 1.65 m panel the eye test calls hidden. Ask the map chat to test the head top too, or keep the head ≤ 1.65 m in Listen. |
| **Ghosting** (passes through furniture it cannot route round) | ideally nothing: today it visibly clips desks and piles | Either hide it (it happens far from the player) or turn it into a feature: a brief "signal drop" (dither or flicker of the model) while `Ghosting` is true. | a relay chatter burst | The flag is public (`FrontRoomsMapHunter.Ghosting`, l.93). |

### 2.2 How big it is on screen

Vertical FOV is 72° in the plan (synthesis §0 decision 11; 76° in the game today), so at 1080 p one metre at distance d covers about 743 / d pixels.

| Distance | Why this distance matters | 2.0 m body | 0.30 m head | 0.10 m detail |
|---|---|---|---|---|
| 0.7 m | catch distance; the frame shows only 1.11–2.13 m of the body (waist to just over the head), with the player's eye line at 1.62 | fills the screen | ~320 px | ~106 px |
| 3 m | one cell; a doorway reveal | ~500 px (half the screen) | ~74 px | ~25 px |
| 12 m | `sightRange`; the chase starts here | ~125 px | ~19 px | ~6 px |
| 16 m | lamps are fully off beyond this (`FrontRoomsMapWorld.cs` l.841: fade from 13 to 16 m) | ~93 px | ~14 px | ~5 px |
| 20 m | a long Level 0 sightline | ~74 px | ~11 px | ~4 px |

Consequences:
- Anything smaller than about 0.15 m is invisible at chase distance. The readable vocabulary is head, shoulder line, arm length and posture.
- A face at 1.60 m sits on the player's eye line (1.62 m) at every distance: it is always on the screen's horizon line, looking straight back. At the catch it is dead centre. This is free composition and a reason to keep the face low in the hunch.
- At the catch the legs are out of frame, so a costly lower-body silhouette buys nothing at the scariest moment. Spend detail above the waist.

## 3. Readability in the two zone grades

### 3.1 Measured values

Relative luminance (sRGB to linear, Rec. 709 weights) averaged over regions of existing captures; contrast ratio = (L_bright + 0.05) / (L_dark + 0.05). These are in-game pixels, not albedo. The map test scene may lack the full post stack, so treat them as indicative.

| Sample | Source | sRGB | Rel. luminance |
|---|---|---|---|
| Level 0 near wall (lit paper) | `Verification/map-test-north.png` | #A8914D | 0.29 |
| Level 0 far wall | same | #85723B | 0.17 |
| Level 0 carpet | same | #9C8555 | 0.24 |
| Office near wall (drywall, lit) | `Verification/main-autopilot/03_play_10s.png` | #928869 | 0.25 |
| Office far wall | same | #71694C | 0.14 |
| Office carpet tile | same | #606353 | 0.12 |
| Office ceiling between lenses | same | #3A351F | 0.04 |
| Relay body (charcoal, in game) | `Verification/main-autopilot/05_play_28s.png` | #383524 | 0.035 |
| Relay head (in game) | same | #A39D7F | 0.34 |
| Relay hand block (yellow detail) | same | #B19B43 | 0.33 |
| Office target wall (the low-key goal) | `10_synthesis.md` §6.9 | #3C392C | 0.041 |
| Office target cubicle fabric | same | #2E2F28 | 0.028 |
| Office target under-desk shadow | same | #212019 | 0.014 |
| Office target far haze | same | #4C4B3C | 0.069 |

| Pairing | Ratio | Read |
|---|---|---|
| Dark body vs lit Level 0 wall | 4.0 : 1 | strong |
| Dark body vs far Level 0 wall | 2.6 : 1 | fair |
| Pale head vs lit Level 0 wall | 1.2 : 1 | **the head disappears into the yellow paper** (it reads by hue only) |
| Dark body vs lit Office wall today | 3.5 : 1 | strong |
| Pale head vs lit Office wall today | 1.3 : 1 | weak |
| Pale head vs Office ceiling | 4.6 : 1 | strong |
| Dark body vs Office ceiling or the target's walls, fabric and corners | ~1.0–1.3 : 1 | **the body disappears** |

### 3.2 What this means

- Level 0 is a mid-to-light, warm, high-key background: the dark body carries the read, and the pale head does not.
- The Office target (synthesis §6.9) is low key: walls at L 0.15–0.25 (HSL), fabric and corners near black. Once that grade lands, the charcoal body vanishes and only light values read.
- So the two-value split (dark body, pale head) is right in principle: in every zone one of the two has contrast. But each needs a **guaranteed edge**:
  - The pale head needs a dark frame (a dark collar, hood edge or the shoulder mass behind it) so it reads against yellow paper.
  - The dark body needs one light accent or a rim response at the shoulder line so it reads against the Office's dark fabric and corners.
- The silhouette must survive with no lighting cues at all. Valve's Team Fortress 2 work states this goal directly: "distinct silhouettes that can be easily identified even with no lighting cues" ([Team Fortress Wiki, Art style](https://wiki.teamfortress.com/wiki/Artstyle)). Its published approach put the highest value contrast at chest level and a dark-to-light gradient from feet to chest (Valve's NPAR 2007 paper, per search summary; the PDF was not opened: UNVERIFIED).
- Frictional added a rim-light term to Amnesia's monster so its outline lit up in dark areas and players got a glimpse of a silhouette in the distance ([Game Developer, Birth of a monster part 2](https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-2-)). A view-dependent rim (fresnel) term in the Relay's body shader is the cheap equivalent and solves the Office problem.

### 3.3 Light, fog and flicker

| Factor | Value | Effect on the Relay |
|---|---|---|
| Lamps | downward spots at the lens centre, 162°/96°, range 10 m (12 m Tall); full within 13 m of the player, off beyond 16 m | Top light. Shoulders and the head crown catch it; the face (pointing down in the hunch) falls into shadow, which suits a face void. In Low zones the head passes within ~0.3 m of a lamp and will flare: the pale head must not blow out (keep its albedo ≤ ~0.75 sRGB). |
| Shadows | 1 lamp in 3 casts soft shadows within 9 m | Its shadow pools under it and on near walls. A cheap tell; keep the silhouette clean so the shadow reads too. |
| Fog | exp² 0.014 today (`FrontRoomsLook.cs` l.19); synthesis proposes 0.018 Office and 0.024 Level 0 | At 12 m: 3 %, 5 % and 8 % fog. At 20 m: 8 %, 12 % and 21 %. Fog barely matters inside sight range. The practical readability limit is the light radius (16 m), not fog. |
| Flicker | per fixture: Level 0 Shift 10 % dead / 32 % failing; Office 3 % / 6 % (proposed 25 % dead off the spine) | A failing lamp over the Relay is the strongest staging tool in the game: the silhouette appears and goes. The design should read in a single 2–3 frame flash, so it needs one simple, unmistakable shape. |
| Grade | Level 0: WB +9 / tint −7, saturation −8, grain 0.22. Office (planned): WB +1 / tint −14, saturation −22, grain 0.18 | Muted yellow detail (#A99E78 albedo) survives the Level 0 grade as warm; in the Office grade it shifts toward olive. Colour accents are weak in both grades. Rely on value, not hue. |

Rules for the concepts:
1. Two values at least 3 : 1 apart inside the figure (body and head), plus a rim response.
2. One readable shape that survives a 2–3 frame flash at 12 m: the head-and-shoulder block, seen from the front and from behind.
3. No important information in hue. Test each concept as a greyscale thumbnail on a yellow mid-value field and on a near-black olive field.

## 4. Performance budget (one skinned character, Mac laptop and WebGL)

Project context: Unity 6000.3, URP Forward+, 4× MSAA. Macs ship a universal player and the WebGL build targets GitHub Pages (`README.md`, `WEBGL_BUILD.md`). Acceptance is the autopilot: average ≥ 55 fps and p99 ≤ 33 ms, with an Office room budget of ≤ 120 k LOD0 triangles (spec §8).

| Item | Budget | Basis |
|---|---|---|
| Skinned mesh renderers | **1** | Unity: use only one skinned mesh renderer per character; two "could roughly double the rendering time" ([Unity Manual, Modeling characters for optimal performance](https://docs.unity3d.com/6000.0/Documentation/Manual/ModelingOptimizedCharacters.html)). Today's rig is 16 separate primitive renderers. |
| LOD0 triangles | **≤ 15 k cap, aim for 8–12 k** | Brief. 15 k is ~12 % of one Office room's budget. The silhouette vocabulary at 3–12 m (§2.2) needs far less; spend the remainder on the head and hands, which the catch frame shows. |
| LOD1 | optional, ~45 % at > 10 m | Matches the prop rule (spec §8). Low priority: it is one character. |
| Materials | **≤ 4, aim for 2–3** | Unity: keep materials per model as low as possible and use more than one only for different shaders ([same page](https://docs.unity3d.com/6000.0/Documentation/Manual/ModelingOptimizedCharacters.html)). Suggested: body (with rim term), head/face (matte pale), detail (muted yellow), optional emissive or dither for a "signal" effect. |
| Deform bones | **24–36** | Brief and `RELAY_MODEL_RIG_RESEARCH.md`. Unity: "The fewer bones you use, the better" ([same page](https://docs.unity3d.com/6000.0/Documentation/Manual/ModelingOptimizedCharacters.html)). Today: 18 transforms. |
| Influences per vertex | **≤ 4; 1–2 for rigid-segment designs** | Unity recommends linear blend skinning with at most four influences ([same page](https://docs.unity3d.com/6000.0/Documentation/Manual/ModelingOptimizedCharacters.html)), and setting the count on import rather than with a runtime cap ([Unity Manual, Skinned Mesh Renderer](https://docs.unity3d.com/6000.0/Documentation/Manual/class-SkinnedMeshRenderer.html)). |
| Skinning path | Mac: GPU (Batched) by default. WebGL2: CPU | `PlayerSettings.meshDeformation` defaults to GPUBatched, which uses compute shaders ([Unity Script Reference](https://docs.unity3d.com/ScriptReference/PlayerSettings-meshDeformation.html)). WebGL2 lists compute shaders as "Not natively supported" ([Unity 6.7 Manual, Web graphics APIs](https://docs.unity3d.com/6000.7/Documentation/Manual/web-graphics-apis-intro.html)), so the browser build skins on the CPU (an inference from the two pages). Low bone and vertex counts matter most for WebGL. |
| Blend shapes, cloth, hair, physics | **none** | Each active blend shape is its own GPU dispatch ([Unity Script Reference](https://docs.unity3d.com/ScriptReference/PlayerSettings-meshDeformation.html)); the prototype already rules out cloth and physics (`RELAY_MODEL_RIG_RESEARCH.md`). |
| Animator settings (when one exists) | Culling Mode "Cull Completely"; no root motion; no scale curves; hashed parameters | [Unity Manual, Mecanim performance and optimization](https://docs.unity3d.com/6000.0/Documentation/Manual/MecanimPeformanceandOptimization.html): root motion and scale curves cost more; Update When Offscreen stays off. |
| Bounds | set the renderer's local bounds to cover the widest pose (BreakDoor reach, run) | With Update When Offscreen off, Unity does not recompute bounds each frame ([Skinned Mesh Renderer](https://docs.unity3d.com/6000.0/Documentation/Manual/class-SkinnedMeshRenderer.html)); bounds that are too small cull the creature while it is on screen. |
| Colliders on the rig | none | The brain ignores rig colliders for its own casts (`FrontRoomsMapHunter.Ignored`, l.707), but they would still block the player's raycasts and the sight test from other systems. The current rig already strips them. |
| Textures | one 2048 set or two 1024 sets (albedo, normal, mask), head and hands get the largest UV share | At the catch, 1 m of the upper body covers ~1060 px of a 1080 p screen. |
| First render | prewarm the Relay's shader variants before release | The spec records an editor shader-compile spike when the Relay first renders at 3 s (spec §8). |

## 5. Animation pipeline options

### 5.1 The options

| Option | What it is | Pros | Cons | Fit |
|---|---|---|---|---|
| **A. Procedural rig, authored mesh (now)** | Keep `FrontRoomsRelayRig.TickAnimation` as the only driver. Replace the 16 primitives with one skinned mesh from Blender whose bones are the transforms the rig already rotates. | No Animator or clips. The state contract and timing stay in code. Editable in the Scene. Works on WebGL today. | Procedural walk and run cycles look mechanical. Soft-skinned shoulders and hips deform badly under raw rotations. The bone offsets in `BuildRig` must come from the imported armature, not hard-coded numbers. | **Best now**, if the design has rigid or semi-rigid segments (hard joints, plates, a stiff garment) so mechanical motion reads as intended. A "relay" creature makes this a style, not a limitation (§6). |
| **B. Blender keyframed clips + Animator (Generic rig)** | 6–7 in-place clips: `Listen`, `Search`, `Walk`, `Run`, `BreakDoor_Strike` (0.5 s loop, contact frame on the blow), `Stagger`, optionally `Reveal_Hold`. An Animator Controller selects them from `HunterState`; the playback rate is speed ÷ authored speed so the feet do not slide. | Real weight and timing. Clips are reviewable in Blender. Generic keeps the authored hunch (no humanoid retargeting to straighten it). | Needs animation time (several days for an animation student). The Animator must stay a view of the brain, not a second authority. | **Next step**, after the model is approved. |
| **C. Mixamo / Unity Humanoid retarget** | Auto-rig in Mixamo and retarget human clips through a Unity Humanoid avatar. | Fast; large library; free. | Mixamo's auto-rigger expects a bipedal humanoid in a neutral T- or A-pose and struggles with extra limbs, large clothing or asymmetric poses ([Cinevva guide, citing Adobe's FAQ](https://app.cinevva.com/guides/automatic-rigging-explained); Adobe's page returned 403: direct quote UNVERIFIED). Unity's Humanoid needs at least 15 bones loosely matching a human skeleton, in T-pose ([Unity Manual, Configuring the Avatar](https://docs.unity3d.com/6000.0/Documentation/Manual/ConfiguringtheAvatar.html)). Retargeted human motion makes it move like a person and straightens the hunch. | **Reference or blocking only**, unless a concept is deliberately human-proportioned (e.g., "an office worker that is wrong"). |
| **D. Unity Animation Rigging layer** | Runtime constraints on top of A or B: Multi-Aim (head toward the noise or the player), Damped Transform (lag on forearms and hands), Two Bone IK (hand contact on the door leaf), Override Transform (an extra stoop under a low head), Twist Correction. All are built on the Animation Jobs API ([Unity, Constraint components](https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/ConstraintComponents.html)). | Cheap secondary motion and gaze. The Listen head-turn becomes a real look at the sound. Compatible with Unity 2023.2+ ([Unity, Animation Rigging](https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/index.html)). | The Rig Builder evaluates inside the Animator's graph, so it needs an Animator component even with option A (from working knowledge: UNVERIFIED). Extra cost per constraint. | **Optional** with B; use two or three constraints, not a full rig. |

### 5.2 Mixamo licence (if used at all)

- Adobe's community FAQ says the content can be used "for unlimited commercial or non commercial use" in games and school projects, and that the only thing you cannot do is distribute the raw character and animation files ([Adobe Community, Mixamo FAQ](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/m-p/13234775)).
- Risk for this project: the WebGL build is set up for GitHub Pages. If the repository is public, committing raw Mixamo FBX files could count as distributing raw files (my reading, UNVERIFIED). Keep raw Mixamo files out of any public repo; ship them only inside builds.

### 5.3 Blender → Unity export for a skinned character

The kit exporter (`Tools/Blender/frontrooms_kit/kitlib.py` l.756–768) already sets `apply_unit_scale`, `FBX_SCALE_ALL`, forward −Z / up Y, `bake_space_transform`, `add_leaf_bones=False`. For the Relay it needs two changes:
1. `object_types` must include `ARMATURE` (today it is `{"MESH"}`).
2. Turn on animation baking per action (Key All Bones, NLA strips or All Actions, Force Start/End Keying) if clips are authored.

That matches the general checklist: leaf bones off, deform bones only, one Action per clip, Generic for non-humanoid rigs ([Cinevva, Blender to Unity export checklist](https://app.cinevva.com/guides/blender-to-unity-export-checklist)). Blender's own FBX manual page did not load (404 and an index-only page): UNVERIFIED there.

A hand-built 24–36 bone armature is simpler than Rigify for this budget. Rigify's control rig needs a deform-only export, and users report unwanted bones in that export (search summary of [Blender devtalk](https://devtalk.blender.org/t/rigify-parent-bones-of-some-def-bones/14745), not opened: UNVERIFIED).

### 5.4 Proposed skeleton (26 deform bones; 10 spare for concept-specific parts)

`root → pelvis → spine_01 → spine_02 → chest → neck → head (→ face_plate optional)`; `chest → clavicle_L/R → upperarm → forearm → hand → finger_grp`; `pelvis → thigh_L/R → shin → foot → toe`.

That is 26 bones with the face plate. The 10 spare bones can go to a second neck segment (a stoop that bends the neck, not the spine), garment panels, cords, or whatever a concept's "relay" part is. Bone names should stay compatible with the rig's serialized fields (`pelvis`, `spine`, `chest`, `neck`, `head`, `upper arm L` …) or the fields get remapped once.

Small code hooks the model will want (map-chat owners):
- `FrontRoomsMapHunter.ListenTarget` (read-only): the noise point it is hunting, for the head aim.
- A separate rig state for `Search`.
- Distinguishing the last `DoorBlow` from the others, for the reveal frame.
- Audio cadence and gait rate taken from one number (§1.3).

## 6. "Relay" as a design hook

### 6.1 What the word carries (sources)

| Sense | Fact | Source |
|---|---|---|
| Origin: the hunt | The noun (late 14c.) comes from Old French *relais*: fresh hounds or horses placed along the line of a chase to take over from tired ones. The verb was revived in electromagnetics for passing on telephone signals (1878). The relay-race sense dates from 1898. | [Etymonline, relay](https://www.etymonline.com/word/relay) |
| Electromechanical relay | A coil magnetises an iron core, which pulls a movable armature that makes or breaks contacts. A spring returns it when power drops. Switching under load arcs and wears the contacts. Latching relays hold their position without power. | [Wikipedia, Relay](https://en.wikipedia.org/wiki/Relay) |
| Telephone exchanges (era fit) | Crossbar switches used select and hold electromagnets moving horizontal and vertical bars, coordinated by a "marker". They dominated from the 1930s to the 1980s, and some remained in service into the 1990s. | [Wikipedia, Crossbar switch](https://en.wikipedia.org/wiki/Crossbar_switch) |
| Step-by-step switching | A Strowger switch's arm steps vertically to a row, then rotates to a contact, one step per dial pulse. | [Wikipedia, Strowger switch](https://en.wikipedia.org/wiki/Strowger_switch) |
| Relay race | The incoming runner hands the baton to an outgoing runner who has already started running (the blind handoff). | [Wikipedia, Relay race](https://en.wikipedia.org/wiki/Relay_race) |

### 6.2 The hook, read against the code

**The etymology already describes the AI.** "Fresh hounds placed along the line of a chase" is what `Arrive` does: when the chase leaves the Relay 30 cells behind, it re-enters 9–15 cells away, unseen, and listens (§1.3). The name is a gameplay description, not a label. Design consequences:

1. **It never tires.** The Hunt walk is level and unhurried even at a speed where a person would run (§1.4). Chase is relentless rather than fast: a sprinting player (5.5 m/s for 5 s) outruns it, then it gains 1 m/s on a walker. The body language should say "a fresh one every time".
2. **It is one of a series.** The game's world already runs on copy-paste: the film's furniture piles are "the same catalogue pasted again", with exact duplicates (`10_synthesis.md` §0 decision 3). A Relay that reads as one unit of many (a unit number, an equipment tag, a stencil) ties the creature to the world logic for the cost of one decal. Each relay can imply a different unit arrived.
3. **Its motion latches.** Relays and stepping switches move in discrete pulls and holds. In Listen and Search the head and torso snap between held poses, and a stepping head moves up, then across, in clicks. That is uncanny (it moves wrong, not just looks wrong; [Uncanny valley](https://en.wikipedia.org/wiki/Uncanny_valley)). It is also the cheapest motion to make procedurally (stepped interpolation, option A). The walk and run stay continuous, so the change from latched to fluid is itself a state cue.
4. **Its sound is a click.** A relay click is percussive and sits apart from the 120 Hz ballast hum, so it reads through walls. The project's motif research already gives the Relay a relay-click signature on the accents of a 3-3-2 rhythm (`SOUND_FOLEY_MOTIF_RESEARCH.md`, around l.200–206). Suggested uses:
   - one spatial click at the arrival point when it relays (the only sign that it moved);
   - a slow tick in Listen;
   - clicks locked to footfalls in Hunt;
   - dense chatter in Chase;
   - a hard "pull-in" clunk on the final door blow.
5. **Its face is a contact gap.** The current narrow dark face void reads naturally as an open contact or a slot. Keep that read, but make it at least 0.10–0.15 m tall so it survives at 12 m (§2.2); 0.08 m today is ~5 px at sight range.
6. **Period materials, not robotics.** For the late-1980s to early-1990s setting, use bakelite-brown and beige plastics, aged brass contacts, cloth-wrapped wire and coiled handset cord. Used as small detail on a body, these give "relay" without turning the creature into a robot. The muted yellow detail slot can be the brass.

What to avoid: a literal robot or switchboard-man (it becomes a costume), visible arcs or sparks as a constant effect (cost, and they light the creature too well), and any wire- or cable-built body. The sibling report `01_ip_entities.md` §0 flags a cable-built humanoid as the Backrooms monster shape already taken by fan games.

## 7. How strong indie horror keeps one enemy readable and scary on a budget

| Game | What it does | Source | Translation for the Relay |
|---|---|---|---|
| Amnesia: The Dark Descent (Frictional, small team) | Designed a humanoid that is not a zombie cliché. It had to walk upright to fit a cylindrical collision body, and stay simple enough to keep the schedule. The aim was uncertainty: "true terror really emerges" when the player cannot predict or make sense of it. | [Game Developer, Birth of a monster part 1](https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-1-) | Our capsule (r 0.3, ≤ 2.05 m) is the same kind of constraint. Design inside it from the start rather than squeezing a concept in later. One or two unreadable features beat many. |
| Amnesia (part 2) | Asymmetric modelling with no mirroring; detail concentrated where needed; the **rig shared with another character**; a **rim-light** term so the outline lit up in the dark and players glimpsed a silhouette in the distance. | [Game Developer, Birth of a monster part 2](https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-2-) | Use asymmetry (already in the Relay's brief: uneven shoulders). Put detail above the waist (§2.2). Add a fresnel rim to the body material for the Office (§3.2). Keep the skeleton generic enough to reuse. |
| Amnesia (the water monster) | A monster never shown, only its splashes. | search summary only (the USgamer interview returned 503): UNVERIFIED | Door blows, footsteps and clicks carry the Relay most of the time. The body is the payoff, not the constant. |
| Alien: Isolation (Creative Assembly) | A "director" tracks a menace gauge and sends the alien away (into vents) when pressure peaks. The alien finds the player only through its own senses, and lucky timing produces "psychopathic serendipity". | [Game Developer, The perfect organism](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation) | The Relay's leash and relay are a crude director. The enemy needs clear **arrival** and **withdrawal** tells (§2.1, §6.2.4), because they are when the player re-evaluates. |
| SCP – Containment Breach (one developer, free, open source) | SCP-173 moves only when the player is not looking; a blink meter forces looking away. | [Wikipedia, SCP – Containment Breach](https://en.wikipedia.org/wiki/SCP_%E2%80%93_Containment_Breach) | The Relay relays only when unseen. A "freeze on first sight" (the Listen hold after an arrival) makes that rule feel deliberate. The rule needs a still, statue-strong Listen pose. |
| Slender: The Eight Pages (one developer, Unity, ~4 months) | The model was crude, but the player is punished for looking at it, so it is never scrutinised. Proximity shows as audio cues and TV-noise distortion. | [Wikipedia, Slender: The Eight Pages](https://en.wikipedia.org/wiki/Slender:_The_Eight_Pages) | The camera can react to the Relay: a short grain or chromatic-aberration spike on first sight through the existing post stack (grain 0.22, CA 0.06). It fits a "signal" creature and is nearly free. |
| Lethal Company (one developer) | Coil-Head: a mannequin-like body on a spring neck that moves only when unobserved. Bracken: brief eye contact makes it flee, a long stare makes it aggressive. | [GGRecon guide](https://ggrecon.com/guides/all-lethal-company-monsters-and-how-to-avoid) (secondary source) | One mechanical oddity (a spring, a latch) plus a clear look rule is enough identity for a cheap model. Also a warning: a spring- or coil-necked mannequin is already taken, so the Relay's "coil" must not be a spring neck. |
| Dark Deception (Glowstick, Red's primary reference) | First-person maze chase, "No hiding in lockers": each level's monsters have distinct AI that needs a different tactic. | [Steam, Dark Deception](https://store.steampowered.com/app/332950/Dark_Deception/) | In a maze, the enemy must read at the junction and down the corridor. The Relay's silhouette and gait must differ from the player's own shadow and the furniture at 12 m. |
| Team Fortress 2 (Valve; AAA, but the standard reference on readability) | Silhouettes that read "even with no lighting cues". | [Team Fortress Wiki, Art style](https://wiki.teamfortress.com/wiki/Artstyle) | The silhouette test in §3.3 rule 3. |

Common thread: one enemy, one strong silhouette, one sound signature, one rule the player can learn. The body is rationed and staged (doorways, flicker, a reveal), and the low budget is hidden by design, not by polish.

## 8. Constraint checklist (pass/fail gates for every concept)

A concept that fails a gate is revised before it is scored.

### G1 Fit (from code)

- [ ] **G1.1** Authored in metres, feet on y = 0, pivot at the floor centre, front +Z (spec §1).
- [ ] **G1.2** Rest-pose top ≤ 2.00 m. Peak of the walk and run cycles ≤ 2.05 m (`RelayHeight`).
- [ ] **G1.3** Face or sensing feature centred at 1.55–1.75 m in Listen and Hunt. The sight ray is at 1.60 m; the face sits on the player's eye line.
- [ ] **G1.4** Hips and torso inside the 0.6 m cylinder between 0.4 and 1.95 m. Anything outside is visual only and ≤ 0.50 m from the body axis at shoulder height.
- [ ] **G1.5** Door crossing: the widest moving pose is ≤ 0.9 m across between 1.0 and 2.05 m, or the arms tuck while crossing. Passes the 2.10 m head.
- [ ] **G1.6** Broken-window crossing (sill 0.35, head 2.00): a defined stoop or step-over pose, or a design where the clip is not visible.
- [ ] **G1.7** No part touches a 2.4 m ceiling in any moving pose. Optional: a stationary rear-up in Tall halls only, never above 2.05 m while moving.
- [ ] **G1.8** Arrival pop-in: the Listen pose's head top is ≤ 1.65 m, or the map chat adds a head-top visibility test to `Arrive`.

### G2 Behaviour

- [ ] **G2.1** Seven poses or loops that read differently in silhouette: Listen, Search, Hunt walk, Chase run, BreakDoor strike, Reveal hold, Stagger.
- [ ] **G2.2** Listen is the strongest still silhouette (it is the first thing seen after every release and relay).
- [ ] **G2.3** Steps plant at 1.14 m every 0.44 s (Hunt) and 1.22–1.57 m every 0.29 s (Chase), or the footstep audio is generated from the gait phase (`SOUND_FOLEY_MOTIF_RESEARCH.md` l.145).
- [ ] **G2.4** Strike reach ≥ 0.45 m in front of the spine at 1.0–1.8 m height, on a 0.5 s loop.

### G3 Readability

- [ ] **G3.1** Two values inside the figure at least 3 : 1 apart.
- [ ] **G3.2** The greyscale thumbnail reads on a yellow mid-value field (rel. luminance ~0.2–0.3) and on a near-black olive field (~0.02–0.04).
- [ ] **G3.3** The head-and-shoulder block is identifiable as a ~125 px tall figure (12 m) in a 2–3 frame flash.
- [ ] **G3.4** Defining features are ≥ 0.10–0.15 m. Nothing important is carried by hue alone.
- [ ] **G3.5** Reads in the Office's low key: a rim response, a light accent or a light value on the upper body.

### G4 Production

- [ ] **G4.1** One skinned mesh renderer, LOD0 ≤ 15 k triangles (aim 8–12 k), ≤ 4 materials (aim 2–3).
- [ ] **G4.2** 24–36 deform bones, ≤ 4 influences per vertex. No blend shapes, cloth, hair or physics.
- [ ] **G4.3** Animates convincingly with the procedural driver (option A), so either rigid or semi-rigid segmentation, or soft areas kept away from the shoulders and hips.
- [ ] **G4.4** Exports through the kit pipeline with an armature (§5.3).

### G5 Originality and era

- [ ] **G5.1** Not a copy or close imitation of an existing creature. Per `01_ip_entities.md`, it is not:
  - wire- or cable-built;
  - a mascot or costume figure;
  - a spring-necked mannequin;
  - a dark, featureless, long-armed grey humanoid.
- [ ] **G5.2** Materials and details are no newer than the early 1990s.

## 9. Scoring rubric (for concepts that pass the gates)

Score each criterion 1–5. Total = Σ (score × weight) ÷ 5, out of 100: all 5s = 100, all 3s = 60. In the sheet, enter score × weight in each cell and divide the sum by 5.

| # | Criterion | Weight | 1 (weak) | 3 (adequate) | 5 (strong) |
|---|---|---|---|---|---|
| 1 | **Silhouette, mass and value** | 20 | reads only up close or in one zone; spindly | reads in both zones in greyscale; one clear block | identifiable in a single flash at 12 m in both grades; mass in the upper body; asymmetric |
| 2 | **State legibility** | 15 | Listen, Hunt and Chase look alike | Chase is clearly different | every state including Search and the reveal reads from the silhouette alone; latched versus fluid motion is itself a cue |
| 3 | **Fear: uncertainty and wrongness** | 15 | a familiar monster type | one disturbing feature | human-but-wrong, one feature the player cannot make sense of, and a gait that is wrong (e.g., the run-speed walk) |
| 4 | **"Relay" hook** | 10 | the name is a label | one element (a sound or a part) | shape, motion and sound all grow from the name (fresh unit, latch, click, contact gap) without becoming a robot or costume |
| 5 | **World and era fit** | 10 | generic fantasy or modern | fits one zone | belongs in both Level 0 and the Office, period-correct, and follows the copy-paste world logic |
| 6 | **Production cost for Red** | 15 | needs mocap, cloth or a soft-skinned deformation pass | buildable in about 2 weeks with clips | buildable in about 1 week with the procedural driver (option A); clips optional later |
| 7 | **Technical margin** | 10 | passes the gates only with hacks (shrinking, clipping) | passes with small poses | eye height, door, window and ceiling clearances are solved by the design itself (e.g., the hunch puts the face at 1.6 m) |
| 8 | **Distance from existing IP** | 5 | needs explaining | clearly different on inspection | nobody would name another creature on first sight |

Scoring sheet:

| Concept | 1 Silh. ×20 | 2 States ×15 | 3 Fear ×15 | 4 Relay ×10 | 5 World ×10 | 6 Cost ×15 | 7 Margin ×10 | 8 IP ×5 | Total /100 | Gate notes |
|---|---|---|---|---|---|---|---|---|---|---|
| A | | | | | | | | | | |
| B | | | | | | | | | | |
| C | | | | | | | | | | |

Tie-breakers, in order: criterion 1, then 6, then 2.

## 10. Open questions and hand-offs

For Red:
1. **Hunt walk speed.** Keep 2.6 m/s and make the run-speed walk a deliberate uncanny trait, or lower it to ~2.2 m/s for a natural walk (§1.4)?
2. **Chase top speed.** If it goes toward 5.4 m/s, the footstep interval should drop to ~0.25 s and the run needs a long, low stride (§1.4).
3. **Ghosting.** Show the pass-through as a "signal drop" effect, or keep hiding it?
4. **First-sight camera reaction** (a grain or CA spike): wanted, or too close to Slender's static?

For the map chat (owner of `FrontRoomsMap/*` and `FrontRooms3DGame.cs`):
1. Expose `ListenTarget` (the noise point).
2. Give Search its own rig state.
3. Mark the final `DoorBlow`.
4. Drive the Relay's footstep audio from the gait phase (§1.3, and `SOUND_FOLEY_MOTIF_RESEARCH.md`).
5. Head-top visibility in `Arrive` (G1.8).
6. If a rig ever exceeds 2.05 m in a Tall hall while stationary, confirm that it never starts moving in that pose.

For the visual chat:
1. Rebuild `FrontRoomsRelayRig` so its bone offsets come from the imported armature.
2. Collapse the 16 renderers to one skinned mesh.
3. Add a rim term to the body material.
4. Prewarm its shaders.

## Sources

Project files (read 2026-10-02):
- `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs`
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs`
- `Assets/Scripts/FrontRoomsHunter.cs`
- `Assets/Scripts/FrontRoomsRelayRig.cs`
- `Assets/Scripts/FrontRooms3DGame.cs`
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`
- `Assets/Scripts/Rendering/FrontRoomsLook.cs`
- `Assets/Scenes/FrontRooms3D.unity`
- `Assets/Levels/FrontRoomsLevel0.asset`
- `Tools/Blender/frontrooms_kit/kitlib.py`
- `Documentation/LEVEL_MODULE_SPEC.md`
- `Documentation/RELAY_MODEL_RIG_RESEARCH.md`
- `Documentation/LEVELS_AND_ENTITIES.md`
- `Documentation/VISUAL_RESEARCH_LOOKDEV.md`
- `Documentation/research/office_and_film/10_synthesis.md`
- `Documentation/SOUND_FOLEY_MOTIF_RESEARCH.md`
- `Documentation/FOLEY_SYSTEM.md`
- `Documentation/research/hunter/01_ip_entities.md`
- captures in `Verification/main-autopilot/` (02, 03, 05) and `Verification/map-test-north.png`

Web (fetched 2026-10-02):
- Wikipedia, Froude number — https://en.wikipedia.org/wiki/Froude_number
- Wikipedia, Uncanny valley — https://en.wikipedia.org/wiki/Uncanny_valley
- Unity Manual, Mecanim performance and optimization — https://docs.unity3d.com/6000.0/Documentation/Manual/MecanimPeformanceandOptimization.html
- Unity Manual, Modeling characters for optimal performance — https://docs.unity3d.com/6000.0/Documentation/Manual/ModelingOptimizedCharacters.html
- Unity Manual, Skinned Mesh Renderer — https://docs.unity3d.com/6000.0/Documentation/Manual/class-SkinnedMeshRenderer.html
- Unity Script Reference, PlayerSettings.meshDeformation — https://docs.unity3d.com/ScriptReference/PlayerSettings-meshDeformation.html
- Unity 6.7 Manual, Web graphics APIs — https://docs.unity3d.com/6000.7/Documentation/Manual/web-graphics-apis-intro.html
- Unity Manual, Configuring the Avatar — https://docs.unity3d.com/6000.0/Documentation/Manual/ConfiguringtheAvatar.html
- Unity Animation Rigging 1.3, manual — https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/index.html
- Unity Animation Rigging 1.3, constraint components — https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/ConstraintComponents.html
- Adobe Community, Mixamo FAQ (licensing) — https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/m-p/13234775
- Cinevva, Automatic rigging explained (cites Mixamo's FAQ) — https://app.cinevva.com/guides/automatic-rigging-explained
- Cinevva, Blender to Unity export checklist — https://app.cinevva.com/guides/blender-to-unity-export-checklist
- Etymonline, relay — https://www.etymonline.com/word/relay
- Wikipedia, Relay — https://en.wikipedia.org/wiki/Relay
- Wikipedia, Crossbar switch — https://en.wikipedia.org/wiki/Crossbar_switch
- Wikipedia, Strowger switch — https://en.wikipedia.org/wiki/Strowger_switch
- Wikipedia, Relay race — https://en.wikipedia.org/wiki/Relay_race
- Game Developer, Amnesia: Birth of a monster part 1 — https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-1-
- Game Developer, Amnesia: Birth of a monster part 2 — https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-2-
- Game Developer, The perfect organism: the AI of Alien: Isolation — https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation
- Wikipedia, SCP – Containment Breach — https://en.wikipedia.org/wiki/SCP_%E2%80%93_Containment_Breach
- Wikipedia, Slender: The Eight Pages — https://en.wikipedia.org/wiki/Slender:_The_Eight_Pages
- GGRecon, Lethal Company monsters — https://ggrecon.com/guides/all-lethal-company-monsters-and-how-to-avoid
- Steam, Dark Deception — https://store.steampowered.com/app/332950/Dark_Deception/
- Team Fortress Wiki, Art style — https://wiki.teamfortress.com/wiki/Artstyle

Not fetched or failed (claims marked UNVERIFIED where used):
- Adobe Mixamo FAQ on helpx (403)
- Blender manual FBX page (404 or index-only)
- Rigify manual (404)
- USgamer Kaernk interview (503)
- Valve NPAR 2007 PDF (not opened)
- Blender devtalk Rigify thread (search summary only)
