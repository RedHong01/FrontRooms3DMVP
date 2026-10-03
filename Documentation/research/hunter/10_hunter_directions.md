# 10 — Hunter (The Relay) redesign: concept directions and blockout specs

Status: COMPLETE (2026-10-02), with an adversarial critic pass applied the same day (see "Critic notes" at the end; every change it made is listed there in C6). Synthesis of reports 01–04 in this folder: design pillars, four concept directions (A Floor Sample, B Night Shift, C Duplicate, D Delivery), Blender blockout specs checked in a headless build, rubric scores and a recommendation. All four directions stay open for Red's choice.

## 0. How to read this

- **Inputs.** All four reports in this folder were read in full: `01_ip_entities.md` (IP grammar and what not to copy), `02_creature_craft.md` (craft levers L1–L12, seeds S1–S6), `03_gameplay_tech.md` (hard numbers, gates G1–G5, rubric), `04_period_wardrobe.md` (garments, period objects, measured palettes). Also read in the project: `RELAY_MODEL_RIG_RESEARCH.md`, `LEVELS_AND_ENTITIES.md`, `LEVEL_MODULE_SPEC.md` §1–§8, `VISUAL_RESEARCH_LOOKDEV.md`, `research/office_and_film/10_synthesis.md` (§0, §5.2 slot table), `FrontRoomsMapHunter.cs`, `FrontRoomsHunter.cs` (tuning), `FrontRoomsRelayRig.cs`, `FrontRoomsModuleUnits.cs` l.92, and the kit's `kitlib.py` (`SLOTS`) and `creature_lib.py` / `build_creature.py` (the Skin-modifier blockout pipeline a parallel session added at 18:30–18:36 today).
- **Citations.** "(02 §2.4)" means the claim is sourced in that report, which carries the URL. URLs given inline here were fetched for this synthesis on 2026-10-02. **UNVERIFIED** marks anything not confirmed on a fetched page. Interpretations are marked "Reading:" or are design proposals, which need no source.
- **Originality.** The four directions below are new combinations built from principles. Each has a "Resemblance risk" line that names the nearest existing design and how the direction steers away from it. Nothing is traced from or modelled on another work's creature.
- **The blockout specs (§7)** use the joint names and the data format of `Tools/Blender/frontrooms_kit/creature_lib.py`, so a modeller can type them in by hand or a script can paste them into a `creatures/<name>.py` module. Every spec was built headless in Blender from a copy in the session scratchpad to check its envelope (§7.0). Nothing was written into `Tools/` or `Assets/`.
- **Language.** Directions are named A–D. "Walking height" is the highest point of the figure in the render pose (the stalking pose it moves in); "standing height" is how tall it would be fully upright, which it never is while moving.

## 1. Design pillars: what the research says the Hunter must be

1. **Built to the door, not to a scale.** Rest-pose top ≤ 2.00 m, moving top ≤ 2.05 m, face centred at 1.55–1.75 m (G1.3; ideally 1.58–1.66), on or near the 1.60 m sight ray (03 §1.1, G1.2). The hunch is how a ~2 m body gets its face to 1.6 m, so it is the gameplay eye height and not a style choice (03 §1.1). Lever L1 puts the head at or below the shoulder line, which no person does (02 L1). A and D take this literally; B and C push the head forward and down to the same face height instead. The same rule keeps the face inside the frame at the 0.7 m catch, where only the band 1.11–2.13 m is visible (02 §1). It reads "too big for the room" through shoulders that nearly fill a 1.0 m door and a mass that nearly reaches its 2.1 m head, not through raw height (01 §7.1).
2. **Mass up top, never thin everywhere.** Red's "spindly" note and the IP research point the same way. The thin, dark, long-armed humanoid is the most crowded family in the Backrooms: Kane's Lifeform, the wiki's Dullers, and the fan games' clones of the Lifeform (01 §3.2, §4, §6). Each direction puts one heavy block above the waist (shoulders, chest, a load, a hood), keeps the limbs thinner, and stretches at most one segment by 15–30 % (02 L2, L3). Part of the "odd" read was construction, not style: a 3.1 m head, a floating torso, buried legs and T-posed pillar arms (02 §1, 03 §1.2). Every spec here is measured against the door first.
3. **A misremembered ordinary thing from FrontRooms' own building, 1985–1993.** The IP's strongest entities are wrong copies of ordinary people or things from the set's own era. Their errors are countable (a length, a count, a missing feature), not gore (01 §5 rules 1–2). FrontRooms' building has three trades: the furniture store (the Backrooms photo was taken in a former furniture store, 04 §3.1), the 1990s office, and building services. Each direction takes one **anchor** that belongs there and adds one **tell** that is discovered, not announced (02 §2.3). Excluded: mascots and costumes, hazmat suits, a peg-leg or other asymmetric wooden step, a person fused to furniture (01 §6).
4. **Value before colour.** The dark mass must have an sRGB value ≤ #3B. One light element above 1.5 m faces up into the troffers. Each needs a guaranteed edge: a dark frame round the light, and a light accent or rim on the dark (03 §3.2, 04 §9.3). Level 0 reads the dark mass (dark body against paper 4 : 1 in game); the Office reads the light element above the 1.57 m panel line (the body falls to about 1 : 1 there) (03 §3.1). No information is carried by hue. The silhouette must survive a 2–3-frame lamp flash at 12 m (≈ 125 px) and read as a cut-out in a lit 1.0 × 2.1 m door (03 G3.3, 02 L4).
5. **Heard first, then lit.** One signature footstep that no other actor makes, not wooden and not asymmetric (that is the film's peg-leg cue, 01 §2.2, §6). One audible signature per state, low-passed through walls as now, and troffers that react within about a cell (02 L10–L11). The body must explain its own Foley: what are its feet, what rattles on it (02 §2.8).
6. **Deliberate, not twitchy.** Weight and planted feet; the wrongness lives in one joint or one timing beat (01 rule 8). Listen and Search use **latched** motion (held poses, snapped steps); Hunt and Chase stay fluid. The switch from latched to fluid is itself a state cue (03 §6.2). Chase changes the gait's category, not just its speed (02 L8). It changes pose only when unseen, which is where "relay" already lives in the code (02 L9).
7. **The name is the AI.** A *relay* was first the fresh hounds placed along a chase. Etymonline glosses the root as leaving the tired dogs behind to take fresh ones (https://www.etymonline.com/word/relay). That is what `Arrive` does when the Relay trails by more than 30 cells. So the creature never tires, is one unit of many (exact copy-paste duplicates, as in the furniture piles), and clicks (03 §6.2, 04 §8.1).
8. **Cheap by construction.** One skinned mesh renderer, 8–12 k triangles (15 k cap), 2–3 materials (4 cap), 24–36 bones, no cloth, hair, blend shapes or physics (03 §4). Rigid or semi-rigid segments make the existing procedural driver (`FrontRoomsRelayRig.TickAnimation`, option A) look intended (03 §5.1). Detail goes above the waist, because the catch frame never shows the legs (03 §2.2).

## 2. Shared numbers every direction obeys

From `FrontRoomsModuleUnits.cs` l.92 (`RelayRadius .3, RelayHeight 2.05, RelayEye 1.6`), `FrontRoomsMapHunter.cs` (probe 0.4–1.95 m, blows every 0.5 s, door falls in 0.25 s, leash 30 cells, re-arrival 9–15 cells), `FrontRoomsHunter.cs` (tuning) and `LEVEL_MODULE_SPEC.md` §3, §7. Checked in code for this synthesis.

| Number | Value | Consequence for every direction |
|---|---|---|
| Body (nav) | capsule r 0.30, probed 0.40–1.95 m | Hips and torso stay inside a 0.6 m cylinder; shoulders, hood, load and arms are visual only and ≤ 0.50 m from the axis (G1.4). Anything behind the axis beyond ~0.38 m clips walls when it turns in a corner. |
| Height | ≤ 2.00 m in the render (rest) pose; ≤ 2.05 m at the peak of the walk/run bob | Door head 2.10, window head 2.00 (needs a deeper stoop or a hidden clip, G1.6), Low ceiling 2.40. |
| Eye | 1.60 m (player 1.62 m) | Face or sensing feature centred at 1.55–1.75 m in Listen and Hunt (G1.3); it then sits on the screen's horizon at every distance (03 §2.2). |
| Front reach | the face ≤ ~0.36 m in front of the axis while walking | In BreakDoor it stands with its axis 0.45 m from the crossing line, so the leaf face is ~0.425 m away. The strike (hands, forearms or load) must reach 0.42–0.45 m at 1.0–1.8 m, and the head must not pass the leaf (G2.4). |
| Speeds | Hunt 2.6 m/s, Chase 4.2 m/s (`chaseSpeed`; the 5.4 m/s in the brief is not in code or the level asset); player walk 3.2, sprint 5.5 for 5 s | Steps plant 1.14 m every 0.44 s in Hunt and 1.22 m every 0.29 s in Chase (03 §1.3). At 2.6 m/s a human-proportioned 2 m body is above the walk-to-run Froude limit (03 §1.4): each direction says how it makes that look intended. |
| States | Dormant → Listen 2 s → Hunt → Search 2.5 s → Chase → BreakDoor (5 blows, 2.5 s) → resume; Relay = an unseen re-arrival followed by Listen; Stagger is rig-only | Seven poses or loops (G2.1). Listen is the most-seen still pose (G2.2). |
| Screen | 72° vertical FOV planned: 2.0 m figure ≈ 125 px at 12 m, ≈ 74 px at 20 m; 0.30 m head ≈ 19 px at 12 m (03 §2.2) | Features under ~0.15 m vanish at chase distance. |
| Light/fog | lamps on within 13 m, off past 16 m; fog exp² 0.018 (Office) / 0.024 (Level 0) proposed: 5–8 % at 12 m, 12–21 % at 20 m (03 §3.3) | At 20 m the limit is lamp radius, not fog: a figure there is a shape against whatever lit room or doorway is behind it. |
| Values (albedo, 04 §9) | Level 0 paper #D2C27C, carpet #9A8558, ceiling #D9D2BF; Office drywall #BDB6A4, carpet #5B636B, cubicle #4A535C; lit Office target walls #3C392C | Dark body 7–9 : 1 against Level 0 paper; ~1.5 : 1 against lit Office panels. Pale head ~1.2 : 1 against Level 0 paper, ~4.5 : 1 against the lens-lit Office ceiling. Mid tones (#A99E78 detail, khaki, mauve) fail everywhere. |
| Budget | 1 skinned renderer, 8–12 k tris, 2–3 materials, 24–36 bones, ≤ 4 influences | The production skeleton is 03 §5.4's 26 bones plus the extras each direction lists. |

## 3. Direction A — "Floor Sample"

**Pitch.** The furniture store's display figure, dressed in last decade's power suit, walks the stockrooms in plain sight; when it relays, the store has set it up again somewhere else.

*(Critic: the first pitch, "posed somewhere new every time you look back", is the moves-only-when-unwatched premise of SCP-173, Lethal Company's Coil-head and Dark Deception's own Gold Watchers. A keeps the sight-chase AI: it moves openly while watched, and the only unseen change is the re-arrival that `Arrive` already hides.)*

**Story tie.** The Backrooms photo was taken in the back rooms of a former furniture store (04 §3.1; `VISUAL_RESEARCH_LOOKDEV.md` §1). The A24 film also pulls store stock into the place (04 §3.1, citing synthesis §0.3). A 1990s furniture floor is room-sets under troffers, and 1990s display figures were abstract and faceless, usually painted white, black or grey (04 §6.1). A "floor sample" is the display piece sold as-is. *Relay*: it is re-staged, not resurrected. Each re-arrival is the figure set up in a new spot, in a new display pose, with the same stock number on the same swing tag (the furniture-pile rule of exact duplicates, 04 §10.3 rule 4).

**Silhouette.**
- *Front.* A hard **T**. A level, padded yoke 0.84 m wide forms the top line at 1.91–1.92 m. The pale head hangs **below** that line (crown ≈ 1.77, face ≈ 1.58), bowed into a white collar. The waist is narrow (≈ 0.33 m), and the trousers fall straight onto oversized black shoes. In Hunt the hands are clasped low in front, so the arms make two closed loops with clear negative space between elbow and body. At 12 m it reads as a square-shouldered, almost headless man.
- *Side.* The torso is near-upright and the yoke runs flat. The neck juts forward and down 45°, so the head centre sits 0.24 m in front of the body axis and under the yoke's front edge. The clasped hands sit about 0.2 m in front of the belly.
- *Tell (countable).* The head is lower than the shoulders, and the joints have seams at the neck and wrists. Each re-arrival is a different display pose (02 S1, S2; L1, L9). It never freezes while watched and never moves only while unwatched.

| Measure | Value |
|---|---|
| Walking height (render pose, after flooring) | **1.92 m** (yoke top, its raised left end); + bob ≤ 0.04 → ≤ 1.96 |
| Standing height (head lifted upright, never while moving) | ≈ 2.05 m |
| Face centre (CRT glass) | 1.58 m |
| Shoulder width (yoke) | 0.84 m (half 0.42) |
| Upper arm / forearm / hand | 0.35 / 0.36 / ≈ 0.20 m (forearm about 10 % long) |
| Hip / thigh / shin | hip 0.99, thigh 0.47, shin 0.45 m |
| Head (shell) | 0.20 W × 0.23 D × 0.27 H m, pitched 22° down, rolled 6° |
| Torso, pelvis to chest-top | 0.71 m |

**Key features.**
- *Head and face.* A satin fibreglass egg, crown-yellowed like the kit's ABS tops. Where the face should be is an oval of **glossy CRT glass**, 0.12 × 0.15 m, slightly convex: a period object, not a slot or a blank (04 §8.2). Under the troffers it carries moving streaks of the lamps, so the "face" is the room reflected. The current narrow face void becomes this glass.
- *Hands.* Satin shell, the same material as the head, so the two light elements are hands and head. They are mannequin hands: fingers together, no nails, a seam at the wrist. In Hunt they are clasped; in Chase they open flat.
- *Feet.* Oversized black shoes (0.33 m), hard heels. No display-stand rod or base plate on a leg: that would make an asymmetric limb with a metal step, too close to the film's peg-leg cue (01 §6).
- *Costume.* A late-1980s power suit cut as one stiff shell, with a padded yoke (04 §1.1, §1.4). The white collar, shirt front and cuffs are the Office light accents. A blank white badge hangs on a navy lanyard (no tie, to steer away from Slender Man, 04 §10.4). A manila swing tag on the left wrist carries the stock number.

| Part | Slot (kit or new) | sRGB | Smoothness | Note |
|---|---|---|---|---|
| Suit, yoke, trousers | `Prop_FabricNavy` (kit #23304A; tune to 04's faded navy **#262C3A**) | #262C3A | 0.15–0.22, elbows/seat 0.30 | 7.8 : 1 against Level 0 paper (04 §9.2) |
| Head, neck, hands | **new `Creature_ShellSatin`** | #DAD5C9 → crown #C8B98F | 0.45–0.55 | Top-face yellowing mask as `Prop_PlasticBeige`; 9.5 : 1 against the suit |
| Face | `Prop_GlassCRT` (kit) | #0F1412 | 0.80–0.88 | 12.7 : 1 against the shell |
| Collar, shirt front, cuffs, badge | `Prop_PlasticWhite` (kit #D9D5C8; 04's #E2DFD6) | #E2DFD6 | 0.25 | 10.5 : 1 against the navy |
| Shoes | `Prop_PlasticBlack` | #1A1A1A | 0.40 | — |
| Swing tag | `Prop_Paper` / atlas | #D8C9A0 with #1D1D1C print | 0.15 | Same number on every Relay |

Production materials: 3. (1) Cloth: navy suit and black shoes by mask. (2) Shell atlas: head, hands, collar, cuffs, badge, tag. (3) CRT glass.

**Motion signature.**

| State | What it does | Reads as |
|---|---|---|
| Listen (2 s) | A **display pose**: weight on one leg, hands clasped at the belt, head turned 20° off-axis. Fully still except one latched head step (a 12° snap) about 1.2 s in. | A figure set up on a showroom floor. The still pose is the arrival pose after every relay (G2.2). |
| Search (2.5 s) | The torso turns in three latched 30° steps with the head fixed to the torso, like a figure re-angled on its stand. The feet do not move. | "Keep still": it is looking around here. Different from Listen (03 §2.1). |
| Hunt (2.6 m/s) | A level, metronome **showroom walk** with the hands still clasped and **no arm swing**. Steps are 1.14 m every 0.44 s (03 §1.3). The head stays locked level on the last noise. At hip 0.99 m, Fr ≈ 0.70: a person would be running. The unhurried long step at that speed is the uncanny trait (03 §1.4, option 1). | Walking too fast without hurrying. |
| Chase (4.2 m/s) | The hands **unclasp**. The arms swing in full, stiff arcs (rigid segments, no elbow lag). The torso pitches to 30° and the yoke rocks with the stride. | A category change (02 L8), visible from behind at 12 m. |
| BreakDoor (0.5 s loop) | Flat-palmed double shove at 1.25 m, both palms together, **identical every blow** (copy-paste, 02 §2.6). Reveal frame: arms still forward, head lifted so the CRT glass catches the lit room. | The T framed by the 1.0 × 2.1 door, yoke near the head jamb. |
| Relay re-arrival | No animation. It appears in one of 4 seeded display poses (hands clasped, one hand raised to the lapel, arms at its sides, turned three-quarters). Optional: a 1–2 s phosphor ghost of the head where it vanished, tinted with the kit CRT `_On` emission #5E7380 (04 §8.2). | Found again in a different pose (L9). |
| Stagger | The only loose motion: the yoke tips 10° and one arm swings free from its shoulder seam. The head stays rigid on the neck (a head bobbing loose on a long neck is the Coil-head's spring). | — |

**How it reads.**
- *Level 0 (warm, high key).* The navy mass is the read: 7.8 : 1 against paper, 9.3 : 1 against the ceiling. The pale head and collar are weak against paper (1.2–1.3 : 1), but the navy yoke frames them and the CRT glass puts a dark mark in the middle of the head. The read is a dark T with a pale, dark-centred oval hanging under it.
- *Office (cool, low key).* The navy body falls to about 1.8 : 1 against cubicle fabric (04 §9.2), and the lit-wall model is lower still. Above the 1.57 m panel line the read is the pale head, collar and shirt-front V: 4.2–5.9 : 1 against the panels and carpet, about 4.5 : 1 against the lens-lit ceiling (04 §9.2–9.3). That is exactly the band seen over a cubicle.
- *20 m in fog.* ≈ 74 px tall (03 §2.2); fog adds 12 % (Office) to 21 % (Level 0) at 20 m (03 §3.3). The T outline and the pale dot of the head survive as a cut-out against any lit room or doorway behind it. Past the 16 m lamp radius it is visible only as that cut-out.

**Sound.** Hard leather heels through carpet give one dull, even "tock" per step, with the badge clip ticking on each step (not wooden, not asymmetric). The latched pose snaps in Listen and Search make a dry fibreglass knock: this is the **relay click** (03 §6.2.4). Chase adds a padded-jacket "whump" per stride. BreakDoor is a doubled flat slap. Troffers within 3 m hum louder as it passes (L11).

**Risks.**
- *Slender Man* (suit plus a pale featureless head) is the nearest existing design (04 §10.1). Mitigation: faded navy, never black; a wide square yoke and a hunch, never thin; a CRT-glass face, not a blank one; no tie; normal-length limbs; the retail markers (swing tag, seams, blank badge).
- *Living shop mannequins* are an existing premise (Doctor Who's Autons, 04 §10.1). Use the figure as material and period only. Never stage a window display that comes alive.
- *Lethal Company's Coil-head* (mannequin on a spring neck that freezes when watched, 02 §3). No spring, no loose head, and no "freezes while watched" rule: the sight-chase AI stays.
- *Dark Deception's Gold Watchers*, from Red's primary reference: enemies that move only when Doug is not looking at them (search summary of the Dark Deception fan wiki, which returns HTTP 402 to WebFetch; a fetched Steam thread confirms that looking toward them stops them: https://steamcommunity.com/app/332950/discussions/0/2996548763043799353). A mannequin re-posed "every time you look back" would be read as this monster in Red's own genre. The pitch was rewritten for that reason.
- *Dark Deception's Malak* wears a formal suit under a non-human head (https://gamepretty.com/dark-deception-monsters-mortals-monsters-guide/, fetched), like Slender Man. The suit is shared, so the separation has to come from the hunch, the yoke and the shell head, never from the suit.
- *The A24 film's monster is also a furniture-store figure*: Pirate Clark copies the store owner in the store's mascot costume (01 §2.1). A shares the store, not the figure. Keep the store link to the swing tag and the display poses. No store branding, mascot, uniform or costume.
- *A blank face reads as Facelings* (01 §6). The CRT glass gives it a specific object instead.
- *Readability.* The clasped hands close the arm loops in Hunt; keep the elbows out so negative space remains (L4).
- *Taste.* "Mannequin in a suit" is the most familiar idea of the four (fear score 3).

**Production cost.** Lowest. The seams make rigid segments natural, so the existing procedural driver (option A) looks intended (03 §5.1).
- Bones: 26 base (03 §5.4) + tag dangle ×2 + badge ×1 = **29**. The yoke is one piece across both shoulders, so it is weighted 100 % to `chest` (one influence) and the clavicles move under it. Weighting each half to its own clavicle would tear it at the middle whenever the shoulders move apart, which Chase does on every stride.
- Size: blockout 10.0 k tris (Skin + Subsurf 2), so production 8–10 k is realistic.
- Time: about **5–6 working days** from blockout to a skinned FBX on the procedural driver.

## 4. Direction B — "Night Shift"

**Pitch.** The building's night electrician went up into the ceiling and came back down wearing it: his face is a fluorescent lens, the only light in the Backrooms that moves.

**Story tie.** Troffers, tiles and ballasts are the anatomy of this space (`VISUAL_RESEARCH_LOOKDEV.md` §1, the Async framing), and FrontRooms already runs one ballast per fixture with dead and failing lamps (`VISUAL_RESEARCH_LOOKDEV.md` §2). Building services wore laundered 65/35 rental coveralls, which fade flat and grey (04 §2.1). A preheat fluorescent's glow-switch starter heats the filaments and pulses until the lamp strikes, and with a failing tube it keeps cycling (https://en.wikipedia.org/wiki/Fluorescent_lamp, "Preheating"). *Relay*: the starter is a switch that keeps trying. When the Relay re-arrives, a dead troffer near the arrival point clicks, cycles and strikes: the place re-lit itself, and it is there (03 §6.2.4; L11). This is the strongest version of 02's S3 seed, reworked to avoid a box head (see Risks).

**Silhouette.**
- *Front.* A rounded **shrug**. The coverall's shoulders ride up into the hood (trapezius joints at 1.84), so the top line is one rounded curve up to the hood crown (≈ 1.87) with no visible neck. In the middle of the dark hood sits a narrow lit panel, 0.13 × 0.26 m, in the 1 : 2 ratio of the ceiling's own 0.6 × 1.2 m lens. It has no rim: the hood is drawn tight round its edge, so the dark twill is the frame. (Critic: the first version's 0.21 × 0.28 m panel in a white enamel rim had a screen's proportions and a bezel, and read as a TV-head in the line-up.) Long forearms hang the gloved hands to mid-thigh, which is ordinary human reach for a figure this size: fingertips at about 0.38 of standing height. A tool belt with a pouch on one hip makes the figure asymmetric.
- *Side.* The torso pitches forward about 15°, the hood leans ahead of the chest, and the lens faces forward and down 18°, like a head bowed to read a meter.
- *Tell.* Its face is a light. Behind the opal you can just see the shadow of one tube and a strip of a face pressed against the diffuser from inside (02 S3): the narrow lens shows only part of it.

| Measure | Value |
|---|---|
| Walking height (render pose) | **1.87 m** (hood crown); + bob ≤ 0.04 → ≤ 1.91 |
| Standing height (upright) | ≈ 2.00 m |
| Face centre (lens) | 1.64 m |
| Shoulder width | 0.85 m (half 0.425) |
| Upper arm / forearm / hand | 0.35 / **0.41** / ≈ 0.22 m (the one long segment: forearm 1.17 × upper arm) |
| Hip / thigh / shin | hip 0.99, thigh 0.48, shin 0.42 m |
| Head (hood) | 0.235 W × 0.25 D × 0.29 H m; lens 0.13 × 0.26 m, no rim |
| Torso, pelvis to chest-top | 0.68 m |

**Key features.**
- *Head and face.* A dark twill hood, drawn tight round a **flat opal lens**. In production the hood front is cut flat and the lens sits 1–2 cm inside it; the blockout's flat panel stands a little proud of the curved hood. It is a strip of the Office's opal troffer, not a screen: no image, no bezel, no rim, no landscape or 3 : 4 proportions, no box behind it. Its emission is the creature's state light (below). Its emission map carries one tube shadow and the pressed strip of face. At the catch, that shadow is what fills the frame.
- *Hands.* Black canvas work gloves. Silver duct-tape bands at the wrists and ankles are the light marks that sell the gait in the dark Office (04 §4.3).
- *Feet.* Rubber-soled work boots.
- *Costume.* An oversized action-back coverall in laundered spruce, with shine at the knees and seat (04 §2.1, §2.3). A blank oval name patch (the same blank on every Relay). A tool belt with a pouch, and a brass key ring that is mainly a sound.
- *Ethics.* No skin shows and nothing codes the wearer's identity, which keeps the cues institutional, per 04 §2.2's caution about the period's real night cleaners.

| Part | Slot | sRGB | Smoothness | Note |
|---|---|---|---|---|
| Coverall, hood | **new `Creature_TwillSpruce`** (04's alternative body colour) | #2E3B33 | 0.15; knees and seat 0.35 | 6.6 : 1 against Level 0 paper; belongs to the Office's green-grey grade (04 §9.3) |
| Lens | **new `Creature_LensOpal`** (emissive), or reuse the Office opal lens material when it exists (synthesis decision 4) | #E8E4D8 albedo; emission 4000 K-ish, at most about 0.6 × the troffer lens | 0.3 | The light element by definition |
| Name patch | `Prop_Paper` (light atlas) | #DCD8CC | 0.45 | 8.2 : 1 against the coverall. The lens itself is 9.2 : 1 against the coverall by albedo alone, before emission |
| Tape cuffs | **new `Creature_TapeSilver`** (04's `Prop_Aluminium` value, dielectric) | #B8B8B4 | 0.50 | 5.9 : 1 against the coverall |
| Gloves | `Prop_FabricChair` | #1C1C1E | 0.15 | — |
| Boots, belt, pouch | `Prop_Vinyl` | #151413 | 0.40 | — |
| Key ring | `Prop_Brass` | #B08A4A | metallic | Mostly audio |

Production materials: 3. (1) Twill, with gloves, boots and belt by mask. (2) Lens (emissive). (3) A small light atlas: tape, patch.

**Motion signature: the light is the state.** The lens emission is driven by `HunterState`, which the rig already receives.

| State | Body | Lens |
|---|---|---|
| Listen (2 s) | Frozen, shoulders up, head tilted 15° toward the sound; latched, no idle sway. | **Off**, with a faint afterglow fading over 1 s (phosphor). An unlit opal lens is still pale plastic (#E8E4D8 albedo), so under a lit cell the arrival pose shows a pale panel in a dark hood. Only in a dead cell is it a dark shape. Its face is therefore never blank, which keeps B out of the dark, featureless humanoid family (G5.1). |
| Search (2.5 s) | The head sweeps in 3 latched steps; one shuffle step in place. | **Starter cycling**: 2–3 dim pulses with clicks, a failing tube trying to strike (Fluorescent lamp, above). |
| Hunt (2.6 m/s) | A heavy, level, bent-knee stride (Fr ≈ 0.70 at hip 0.99, the deliberate run-speed walk). Long forearms hang and barely swing; the head is locked on the last noise. | **Dim, steady** (about 25 %): a moving pale rectangle at 1.64 m, the 12 m read in a dead cell. |
| Chase (4.2 m/s) | The torso drops to 35°, the long arms swing wide with open hands, and the lens stays level on the player (head-lock, 02 §2.6). | **Strikes to full**, plus one unshadowed point light (range 3 m) that lights its own shoulders and the carpet ahead. |
| BreakDoor (0.5 s loop) | Forearm hammer blows at 1.4 m, identical each time. | **Flashes on each blow.** From the player's side, light leaks around the door gap in the 0.5 s rhythm before the door gives. Reveal: lit face framed in the doorway. |
| Relay re-arrival | No animation. | A dead troffer within one cell of the arrival point clicks, cycles and strikes. The lens itself stays off (Listen). |
| Stagger | The hood jerks; arms loose. | Drops out for 0.3 s, then flickers back. |

**How it reads.**
- *Level 0.* The spruce mass reads at 6.6 : 1 against paper. The lens reads by emission everywhere. The dark hood round it is the "dark frame round the light" that 03 §3.2 asks for. Unlit, the lens is only 1.4 : 1 against Level 0 paper, so the hood frame matters.
- *Office.* The body drops to about 1.5 : 1 against the panels, but the lens is self-lit. It is the only Office element that reads without any lamp, above the 1.57 m panel line, and the tape cuffs mark the hands.
- *20 m in fog.* B is the only direction readable **beyond the 16 m lamp radius**: a small lit slot at eye height (≈ 5 × 10 px at 20 m) moving in the dark. That is an honest telegraph, and a design choice: it trades some mystery for the readable, uncatchable-but-avoidable feel of Red's reference, *Dark Deception* (02 §3). Listen keeps it dark, so arrivals stay ambushes.

**Sound.** It is a light, so it hums.
- The **ballast hum** is its voice. It is quiet in Listen, steady in Hunt, and rises in pitch and level in Chase. It sits inside the game's own hum bed, so the player hears the room get louder before seeing anything.
- The **starter click-and-cycle** is its relay click (Search, arrival). Rubber boot thuds with a slight scuff; keys jingle on the belt in a metronome rhythm in Hunt.
- Nearby troffers buzz up as it passes (L11).

**Risks.**
- *Object-for-a-head trope.* Skibidi Toilet (from 2023) has humanoids with CCTV cameras, speakers and televisions for heads (https://en.wikipedia.org/wiki/Skibidi_Toilet). Trevor Henderson's everyday-object anatomy (Siren Head) is the principle (02 §3).
  - The first blockout used a box-shaped fixture head and read as a TV-head in the line-up. It was replaced with the hood plus a flat lens.
  - The hood-plus-lens version still read as a screen in the critic's look at the line-up, because of its 3 : 4 panel and white bezel. The critic pass narrowed the lens to the troffer's 1 : 2 ratio and removed the rim (§7.3).
  - Keep it that way: no box, no bezel or rim, no screen image or screen proportions, no suit (do **not** combine B's face with A's suit), no speaker.
  - No humanoid with a fluorescent lamp for a head turned up in one web search (2026-10-02). The nearest wiki hit was "Lamp-Reys", lamprey-like and not humanoid (search result only, UNVERIFIED). That is not proof that none exists.
- *Silhouette at 20 m.* With the lens dark, B's cut-out is the plainest of the four: a rounded, headless block on legs (C4). Its identity at range is the light. Optional test for panel 2: a 1.2 m carton of 4-ft tubes carried upright in one hand, a period relamper's load that makes the outline asymmetric. Check it against the 0.45 m half-width first.
- *A glowing face as a default.* 02 §2.4 warns against glowing eyes. This is a period diffuser with a job: its light is its state.
- *Hazmat read (Async).* A hood with a face shield could read as a protective suit (01 §1.4, §6). Use dark twill, not white Tyvek, with no respirator, tank or mask hardware.
- *Gameplay.* A self-lit enemy is easier to see in the dark. Mitigation: the lens is off in Listen and dim in Hunt.
- *Look-dev.* The emission must stay under the troffer lens's own brightness so bloom does not turn the face into a white blob (03 §3.3 keeps the pale head at ≤ 0.75 sRGB for the same reason). Budget one extra realtime light, Chase only.

**Production cost.** Low to medium.
- Bones: 26 base + key-ring dangle ×1 + optional hood-pitch bone ×1 = **27–28**. The hood is rigid on the head bone.
- Size: blockout 8.9 k tris.
- Extra work: an emissive lens texture (tube and face shadows), a state-to-emission hook in `FrontRoomsRelayRig` (it already receives the state), the Chase point light, and the "strike a troffer near the arrival" call into the existing per-fixture flicker (map-chat owned).
- Time: about **6–8 working days**.

## 5. Direction C — "Duplicate"

**Pitch.** A bad photocopy of an employee: a flat toner-print face, a body stretched where the page slipped on the glass, and identical copies of him standing in every office.

**Story tie.**
- *The copier is a period object.* Xerographic copiers spread through offices from the 1960s to the 1980s, and toner sticks only to the charged, dark areas of the image (https://en.wikipedia.org/wiki/Photocopier). The game's Office kit already has a copier (`Kit_Copier`).
- *Copies of copies degrade.* Each generation of photocopy distorts and degrades the image (https://en.wikipedia.org/wiki/Generation_loss).
- *Relay.* A relay was first a signal repeater on telegraph lines (04 §8.1, citing Wikipedia "Relay"). This Relay is a repeater: each re-arrival is the **next-generation copy**. The public `Relays` counter (`FrontRoomsMapHunter.Relays`) drives a material parameter, so the print gets harsher, darker and noisier each time.
- *Copy-paste.* This is the furniture piles' rule (exact duplicates, synthesis decision 3) applied to a person. It would also make Red's Office-target "dark figure-like shape about 25 m down the corridor" intentional (02 S6; synthesis T24, Q12).

**Silhouette.**
- *Front.* The **inverted value scheme** of the four, and **monochrome like a copy**: only toner black and paper white, no hue. A pale long-sleeved shirt block runs from the belt (0.95) to the shoulders (1.61), with a black tie down the middle and black trousers below. Only the hands are bare. The head is toner-black with a flat pale face set into it.
- *Side.* A long, forward-curving trunk with a paunch: the trunk is about as long as the legs (0.78 vs 0.85 m). Measured the same way, pelvis-to-neck against hip height is 0.85 / 0.82 ≈ 1.0 for C and 0.57 / 0.92 ≈ 0.6 for the pipeline's own `Ref_Human180`. The legs are short (hip 0.82). The head pushes forward of the chest. In profile **the face has no relief**: it is a flat plane, and that is the tell at 3–6 m.
- *Tell (countable).* (1) A flat face with a dark copy border. (2) A trunk stretched to leg length, "where the page slipped". (3) It is one of several identical copies.

| Measure | Value |
|---|---|
| Walking height (render pose) | **1.79 m** (crown) — the smallest of the four; its menace is number and wrongness, not size |
| Listen pose height (straightens up) | ≈ 1.98 m: in Listen it stands to full height, face at about 1.75 |
| Face centre (print) | 1.64 m |
| Shoulder width | 0.68 m (half 0.34) |
| Upper arm / forearm / hand | 0.29 / 0.30 / ≈ 0.22 m (human length; they hang to mid-thigh because the legs are short) |
| Hip / thigh / shin | hip 0.82, thigh 0.39, shin 0.36 m |
| Head | 0.19 W × 0.21 D × 0.25 H m; face plane 0.155 × 0.20 m |
| Trunk, pelvis to chest-top | **0.78 m** |

**Key features.**
- *Head and face.* The skull and hair mass are toner-black, the large flat dark area a copier makes of hair and shadow. Set into it is a flat paper plane printed with an **invented** high-contrast face (made from a sculpt rendered in Blender and thresholded, never a real person's photo): black eye sockets, nostrils, mouth line and brows on white, with a neutral, faintly sad expression (01 rule 9, pitiable not snarling). The black head is the dark frame the pale face needs (03 §3.2). Across the face run toner streaks along the "scan" direction, from vertical drum marks rather than a smeared face (01 §6 rules out smeared faces).
- *Hands.* Bare, paper-pale, toner-shaded in the creases.
- *Feet.* Soft-soled black office shoes.
- *Costume.* A long-sleeved white shirt buttoned at the cuff, a toner-black tie, toner-black trousers, belt and shoes. No jacket, briefcase or phone. The shirt is "printed": its up-facing planes stay white, but folds and flanks go **toner-grey**, a baked darkening toward the silhouette edge. The figure therefore draws its own dark outline, which makes it readable against yellow paper. (Critic: the first version, a white short-sleeved shirt, oxblood tie and navy trousers with "no jacket and no briefcase", did not separate C from The Exit 8's man, who wears work clothes and carries a briefcase. Fetched: https://en.wikipedia.org/wiki/The_Exit_8. Search summaries put him in a white shirt and dress pants, UNVERIFIED on a fetched page. The separation now rests on the black-and-white print, the flat face, the toner head and the stretched trunk. See Risks.)
- *The copies.* 2–3 static duplicates stand in Office rooms in the **upright Listen pose** (§7.4 second pose). Stage them as a print run, not as passers-by. They all face the same way, spaced exactly one cell apart against a wall or among desks. None ever stands in a corridor or walks toward the player. They are baked static meshes: a skinned mesh does not batch, so bake the pose. They share one mesh and the two materials, so the SRP Batcher handles them. They still cost triangles: each is about 8.5 k, so three copies add about 26 k to an Office room's 120 k LOD0 budget (spec §8). Give them an LOD1 at about 45 % beyond 8 m, and cap them at 3 per room. The live one is the copy whose head turns.

| Part | Slot | sRGB | Note |
|---|---|---|---|
| Shirt, collar, face plane, hands, neck | `Prop_Paper` (kit) | #DCD8CC; folds and edges toner-grey (baked, or a darkening term) | 11.8 : 1 against the toner trousers |
| Head (skull/hair), print ink, tie, trousers, belt, shoes | **new `Creature_Toner`** (= 04's mannequin black) | #1D1D1C | 11.8 : 1 against the paper face; 9.4 : 1 against Level 0 paper |

Production materials: 2. (1) Paper: shirt, hands and face via an atlas, with a `_Generation` parameter and the toner-edge term. (2) Toner: head, print, tie, trousers, belt and shoes, with cloth detail in the normal map. No hue anywhere: the figure is a black-and-white copy in a coloured room. (Critic: this replaces the first version's oxblood tie, navy trousers and `Creature_SkinPale` arms. It is cheaper by one material and drops the `Creature_TieOxblood` slot.)

**Motion signature.**

| State | What it does |
|---|---|
| Listen (2 s) | It **straightens to full height** (≈ 1.98 m), arms at its sides, in exactly the copies' pose, then turns its head toward the noise in two latched steps. In a room of copies, the head turn is the only difference. |
| Search (2.5 s) | It folds back into the slump and sweeps the head in latched steps. The body does not turn: the face plane swings flat across the room like a page being read. |
| Hunt (2.6 m/s) | Short legs (hip 0.82, Fr ≈ 0.84) cannot sell a 1.14 m step, so it **shuffles**: quick, short, level steps (about 0.76 m every 0.29 s) with no vertical bob. It slides like a sheet across a desk (the "glide" wrongness, 02 §2.6). This needs the footstep audio driven from the gait phase (03 §1.3 hand-off), not the fixed 0.44 s timer. |
| Chase (4.2 m/s) | The long trunk folds to 40°, the arms pump, and the **head stays level and locked on the player**: the flat face always faces you while the body labours (head-lock, 02 §2.6). |
| BreakDoor (0.5 s loop) | Both forearms come down together like a copier lid, identical every blow. The reveal shows the flat face framed in the door. |
| Relay re-arrival | No animation. It arrives in the frozen copy pose, one generation darker. Optional: one horizontal light sweep across the face plane (the scan bar) on its first sighting. |
| Stagger | The head jerks sideways 15° and **the face plane does not follow** for 0.2 s. It is a print on the front of the head, so the misregistration shows as a bug. |

**How it reads.**
- *Level 0.* The shirt is weak against paper (1.3 : 1), so the read comes from the toner head, tie and trousers (9.4 : 1 each) and the toner-grey shirt edges. At 12 m it is a dark head floating over dark legs with an outlined pale trunk between them.
- *Office.* This is C's home. The white shirt and face give 4.3–5.5 : 1 against the carpet and panels, and above the panel line the pale trunk and face are the strongest read of all four directions.
- *20 m in fog.* A pale vertical block with a dark head. In the Office it can be confused with a copy at that distance, which is intended.

**Sound.**
- Feet: a quick double shuffle of soft soles.
- Paper rustle when it moves in Listen and Search.
- Relay: a copier scan sweep and paper-feed whirr at the arrival point.
- Chase: fast, flat slaps.
- BreakDoor: a lid-slam.

None of these is a footstep any other actor makes.

**Risks.**
- *Doppelgänger horror* (the Mandela Catalogue's replaced familiar people, 02 §3). Keep it about copies of a stranger: no smile, no broadcast.
- *The IP's own Still Life idea* (the place's failed copies of people, 01 §2.1). The principle is free, but the execution must stay photocopy-specific. No stuffing, no duplicated eyes, no smear (01 §6).
- ***The Exit 8* is C's closest neighbour, and the overlap is more than the costume.** Fetched (https://en.wikipedia.org/wiki/The_Exit_8): its only other person is a middle-aged man in work clothes with a briefcase. The player's whole task is to spot anomalies in a repeating corridor, and some loops give the man "proportion differences" or make him walk quickly at you. C first shared four things with it: the office-man costume, a repeating copy-paste space, spot-the-changed-one, and a proportion error as the tell. The critic pass changes what it can:
  - a black-and-white printed figure instead of a commuter (§5 Costume);
  - copies staged as a still print run in Office rooms, never as a passer-by in a corridor (§5 The copies);
  - the stretched trunk is the same in every copy, so it is a fixed trait, not a variation to spot;
  - only the live copy moves, so no pass/fail spot-the-difference rule is built on it.

  What remains is the premise: an ordinary office man, repeated. Panel 1 must show that the flat face and the print read first. If Red's first word on seeing it is "Exit 8", drop C's body and keep only its mechanics (the generation counter, the scan-bar arrival), which §8.3 already offers to any direction.
- *The wiki's ordinary-looking Stalkers* (01 §3.2) and Facelings (ordinary office clothes, a wrong face): C keeps a face, a printed one, and is never shown keeping its distance.
- *Gameplay: decoys.* The live one must be learnable: only it turns its head.
- *Gameplay: two code changes.* The copies need placement (map chat). The shuffle needs gait-driven audio.
- *Budget.* The copies are extra triangles in the densest rooms: about 8.5 k each. Use the LOD1 and the cap of 3 per room (§5 The copies).
- *Silhouette.* It is the smallest and least massive of the four, so it gets the weakest silhouette score. It also needs the toner-edge shading to pass Level 0.

**Production cost.** Medium to high.
- Bones: 26 base + a third spine bone (the long C-curve) + tie ×1 = **28**. The long soft trunk under procedural rotations needs careful weights (G4.3).
- Size: blockout 8.5 k tris.
- Extra work: invented face art, the generation parameter, copy placement, the gait-audio coupling.
- Time: about **10–12 working days**.

## 6. Direction D — "Delivery"

**Pitch.** The delivery nobody signed for: a mover bent under a padded load that has become his back. Every time it relays, a fresh carrier arrives with the same load.

**Story tie.**
- *Movers' kit.* Movers use dollies, furniture pads and cargo belts (https://en.wikipedia.org/wiki/Moving_company).
- *Store stock.* The furniture piles are delivered store stock (04 §3.2, synthesis §0.3).
- *Relay.* This direction takes the word most literally. The Pony Express (1860–61) kept 157 relay stations (about 190 stations in all), where riders changed tired horses for fresh ones and the same mail pouch (the *mochila*) moved from saddle to saddle (https://en.wikipedia.org/wiki/Pony_Express; the critic's re-fetch corrected "about 190 relay stations"). The root sense of *relay* is to leave the tired dogs behind and take fresh ones (https://www.etymonline.com/word/relay). So the Relay is a courier relay: it never tires because each re-arrival is a **fresh carrier with the same load**, and the load's shipping label never changes.

**Silhouette.**
- *Front.* A **tilted slab**. A quilted, strapped bundle 0.72 m wide and 0.50 m tall rides high on the back to 1.95 m. It is rolled 11° down to its right and sits 3 cm toward its left shoulder, so the top line is a slanted, square-cornered block, plainly a load. (Critic: the first version's rounder 0.76 × 0.62 m mound with soft corners read from the front at 20 m as one huge round head, a mascot-head silhouette; see C4.) Under its front lip the head hangs low (face ≈ 1.60) in a dark knit watch cap whose ecru cuff is turned up at the brow. The face below is in the load's shadow. Cargo straps cross the chest in an X with a chrome buckle. The arms hang forward with big pale work gloves at knee-to-thigh height. Bent knees, heavy boots.
- *Side.* The torso is pitched about 26° with bent knees: the carry posture. The load sits on the back, up to 0.34 m behind the axis. The head is under the front lip, so top light cannot reach the face.
- *Tell.* It never sets the load down, and the straps run *into* the shoulders. Its face is never lit: it does not need to see.

| Measure | Value |
|---|---|
| Walking height (render pose) | **1.95 m** (load top) — "just fits" the 2.1 m door head |
| Standing height (if it stood up under the load; it never does) | ≈ 2.10 m |
| Face centre (eyes, in shadow) | 1.60 m; the ecru cap cuff, the face's light band, is at 1.65 m |
| Width | 0.80 m across at 1.0–2.1 m, asymmetric: +0.43 m on its left, −0.37 m on its right; shoulders 0.70 m |
| Upper arm / forearm / hand | 0.33 / 0.31 / ≈ 0.22 m (gloves oversized: 0.12 × 0.15 m) |
| Hip / thigh / shin | hip 0.86 (knees bent), thigh 0.44, shin 0.39 m |
| Head | 0.18 W × 0.21 D × 0.235 H m in the cap |
| Load | 0.72 × 0.42 × 0.50 m soft box (corner radius 0.05), pitched 20°, rolled −11° (right side down), centre 3 cm left of the axis |

**Key features.**
- *Head and face.* A charcoal knit watch cap with its ecru cuff turned up at the brow. Below it, the face is modelled only in big planes with a dark neutral albedo and sits under the load's lip, where the top light never reaches (02 §2.4 option 1, the face the light erases). It codes no identity (04 §2.2's caution). The cuff is the face's light band in a dark frame: 8.0 : 1 against the cap, with the load's lip above it and the shadowed face below. At the catch it sits at 1.65 m, the centre of the frame. (Critic: the first version taped the eyes and mouth with silver tape. A gagged, blindfolded man reads as a hostage, not a hunter, and taped-over eyes on a hunched sound-hunter sat close to the Janitor of *Little Nightmares*; see Risks.)
- *Hands.* Pale cotton work gloves, oversized. These are its "reveal" detail: in the doorway and at the door leaf, the player sees two white hands.
- *Feet.* Steel-toe work boots, the heaviest Foley of the four.
- *Costume.* A brown duck-canvas work jacket, charcoal work trousers, and black cargo straps with a chrome buckle.
- *The load.* A **quilted moving pad** in faded navy with a pale binding along its top-front edge. That binding is the light rim that outlines the load against dark walls. A white shipping label on the top faces up into the troffers and forward toward the player in Chase. The bundle stays unidentifiable: no chair legs or upholstery poke out (see Risks).

| Part | Slot | sRGB | Note |
|---|---|---|---|
| Load (quilted pad) | **new `Creature_PadNavy`** (quilting by normal map) | #262C3A | 7.8 : 1 against Level 0 paper, 9.8 : 1 against the Office ceiling |
| Jacket | **new `Creature_CanvasBrown`** | #3A2E24 | 7.4 : 1 against Level 0 paper |
| Trousers, cap, neck, face (dark neutral) | `Prop_FabricCharcoal` (kit) | #3A3A3C | — |
| Gloves, cap cuff, binding, label | `Prop_Paper` / light atlas | #DCD8CC | 9.2 : 1 against the jacket; 8.0 : 1 (cuff) against the cap; 4.3–5.5 : 1 against Office carpet and panels |
| Straps, boots | `Prop_FabricChair`, `Prop_Vinyl` | #1C1C1E, #151413 | — |
| Buckle | `Prop_Chrome` | #D8D8D8 metallic | — |

Production materials: 3. (1) Pad. (2) Clothing atlas: jacket, trousers, cap, boots, straps. (3) Light atlas: gloves, cap cuff, binding, label, buckle.

**Motion signature.**

| State | What it does |
|---|---|
| Listen (2 s) | It stands still with the load settled. The only movement is **one slow breath under the load** (the mound sinks 2 cm over 1.5 s and rises), while the capped head tilts toward the sound in one latched step. |
| Search (2.5 s) | It turns in place the way a man with a load turns: the whole mound pivots in two heavy steps, and the head follows late. |
| Hunt (2.6 m/s) | A heavy, wide, bent-knee **plod** (hip 0.86, Fr ≈ 0.80). The steps are long and low, as if pushing under weight; 2.6 m/s with a load is the wrongness. On the fixed 0.44 s footstep timer each step must be 1.14 m, which is 1.3 × the bent leg's length and reads as a lunge. Drive the footsteps from the gait phase (§9) and plod at about 0.9 m every 0.35 s instead. The load sways with damped lag (2 bones), arms hang, gloves swing slightly. |
| Chase (4.2 m/s) | It drops lower and drives the load forward like a ram. The arms reach ahead and the mound pitches down over the head. Each stride thuds the load against its back. |
| BreakDoor (0.5 s loop) | A **shoulder ram**: it turns 30° and drives the load's front corner into the leaf at 1.5–1.8 m, identical every blow. The pad muffles the blows: a deadened thud, unlike any other door sound in the game. Reveal: the load fills the doorway up to 0.15 m below the head jamb, gloves on the frame. |
| Relay re-arrival | No animation. A single heavy padded **set-down thud** sounds at the arrival point, then it is in Listen. The same label, the same stock (L12). |
| Stagger | The load slews sideways 10° and the figure takes two catching steps. It is the only time the load looks heavy *for* it. |

**How it reads.**
- *Level 0.* The strongest read of the four: a 0.80 × 0.6 m dark mass at head height, 7.4–7.8 : 1 against paper, from any angle.
- *Office.* The pad and jacket sink against the panels (≈ 1.8 : 1), but the mound rises above the 1.57 m panel line against the haze and lit ceiling (≈ 9.8 : 1 against the ceiling tile). The pale binding, label and gloves pick it out.
- *20 m in fog.* A tilted block on legs from the front, a hump in profile. It is the shape least likely to be mistaken for a person or for furniture at distance, which is good for the chase.

**Sound.** The heaviest set in the game:
- steel-toe boot plod plus a strap-buckle clink on each step;
- a padded load thump on each Chase stride;
- one exhale in Listen;
- the muffled ram on doors;
- the set-down thud on relay.

**Risks.**
- *Hunchback cartoon.* The Amnesia team rejected a cartoony hunchback concept as too childlike (02 §2.3). Keep the load an object, with straps, quilting and a label, and keep the posture a real carry.
- *"Person fused to furniture"* is a film Still Life trait (01 §6). The load must never show furniture parts (no chair legs or upholstery). It stays a padded bundle.
- *Gameplay: the load's back.* The load reaches 0.34 m behind the axis, outside the 0.30 m probe, so it can clip walls in tight turns. Keep turns wide, or accept a visual clip (G1.4).
- *Gameplay: width.* 0.80 m across, but 0.43 m on its left side. With the body up to 0.20 m off the door's centre, that side passes the jamb only when the body is centred or off to its right. Any wider or more offset load fails G1.5.
- *Gameplay: the face.* The face is hidden most of the time, so the catch portrait is under the load's lip: the ecru cuff, the dark face below, the buckle lower down. It is less legible than A or B.
- ***Little Nightmares*' Janitor** is blind, hunts by touch, smell and sound, and is known for his long arms (https://www.gamerevolution.com/features/14122-little-nightmares-story-explained-a-look-at-its-monsters-and-ending, fetched). Search summaries add bandaged eyes and a hunch (UNVERIFIED). A hunched sound-hunter with taped-over eyes sat near him. D keeps normal arm length, a load instead of a hunch, and a face hidden by light, not bound.
- *Hostage imagery.* Tape over the eyes and mouth codes a bound victim. That is the wrong register for the hunter and a needless taste risk in a student showcase. It was removed.
- *Fear.* Pitiable more than frightening (fear 3); the scare must come from mass and the ram.
- *Production.* The bent-knee loaded walk needs hand tuning to avoid comedy, and the straps over the shoulders are a soft-skin zone (G4.3).

**Production cost.** Medium.
- Bones: 26 base + load root + load sway ×2 (damped) = **29**.
- Size: blockout 8.1 k tris.
- Extra work: a quilting normal map, the load-sway damping, a hand-tuned procedural crouch.
- Time: about **8–10 working days**.

## 7. Blockout specs (Blender, Skin-modifier)

### 7.0 Conventions, format and how the specs were checked

**Axes and units.** Metres; Blender **Z up**; the figure **faces −Y** (Unity +Z after the kit's FBX export); its **left is +X**; feet on z = 0; the body axis is x = y = 0 (the nav capsule's centre line). Rotations are degrees XYZ (Blender Euler). **X pitches**: a positive X rotation pitches a part's front face **down** (−Y toward −Z). **Y rolls** (tilts side to side as seen from the front): a positive Y rotation lowers the part's left (+X) end. **Z yaws** (turns left or right). This is the convention of `kitlib.py` and `creature_lib.py`. (Critic: the first specs wrote every "roll" in the Z slot, which is a yaw. A's head and yoke, C's head and D's load were turned instead of tilted, so the yoke's "left end 1 cm high" and the load's lean did not exist in the build. The tables below put roll in Y.)

**Format** (the one `creature_lib.py` already uses):
- **Joints**: name → (x, y, z), radius. The radius is a Skin-modifier vertex radius: one number, or (rx, ry) for an oval section (rx ≈ across the body, ry ≈ front-to-back on vertical chains).
- **Skin parts**: each part is one Skin-modifier object over a set of joint pairs, so each garment can carry its own material slot. Run it with `creature_lib.skin_body(kit, joints, bones, slot, subdiv=2)`, or by hand: an edges-only mesh, a Skin modifier (branch smoothing 0.6, one root per connected chain), then Subdivision Surface level 2, then apply.
- **Legs are two separate chains**, each starting at a root joint hidden inside the torso garment (`seat_l/_r`, or `waist_l/_r` for C), as `creature_lib.LEG_BONES` does. A single pelvis joint shared by both legs makes the Skin modifier fold a flat sheet at the crotch; the library's own comment says so. In the first check build that fold showed as a pale flap at A's and D's hips. C's three-way waist, pelvis and hip node collapsed into an arch of trouser legs that floated 6 cm under the shirt, the "floating torso" fault that 02 §1 diagnosed in the current rig. The critic pass rebuilt all four with separate chains (C5).
- **Derived joints** (sleeve ends, cuffs, "inside the cuff" starts, shins) are linear interpolations along a limb, given so that tube ends tuck inside the neighbouring garment (the same trick as `creature_lib`'s `cuff`, `neck_base` and `shin`). Their coordinates are listed too.
- **Rigid parts**: `kitlib.Kit` primitives. `box`, `soft_box` (superellipsoid; `radius` softens the corners, `puff` bows the faces) and `ellipsoid` (= `creature_lib.ellipsoid`, a `soft_box` with radius 0.6 × its largest size) take `size` (x, y, z), centred at `loc`. `cylinder` is Z-aligned, and `frame` and `bulged_panel` face −Y. `tube` takes a polyline.
- **Slots**: kit `Prop_*` slots where one fits. Otherwise **new `Creature_*` slots** with the hex given in §3–§6. As of 19:02 on 2026-10-02 these are already in `kitlib.SLOTS` (added by the visual chat, together with `Troffer_Lens` and `Creature_LensDim`). `FrontRoomsRenderSetup` does not have them yet.

**Flooring.** Skin radii leave the soles about 1–2 cm above z = 0. Finish with `creature_lib.floor_parts(kit)`, which drops every part so the lowest vertex sits on z = 0. Rigid parts placed through `Kit._place` have a stale `matrix_world` until the depsgraph updates, so `floor_parts` must call `bpy.context.view_layer.update()` first, or it reads them at the origin. The first check build was shifted up by 0.13–0.31 m because of this. **That fix has landed**: `creature_lib.floor_parts` calls the update itself (file modified 19:02 on 2026-10-02). The coordinates below are **before** flooring; the envelope table gives the values **after** it.

**How they were checked.** All four specs were typed into a data file in the session scratchpad and built headless with Blender 4.3 through the project's own `creature_lib` and `kitlib` (imported read-only; nothing written to `Tools/` or `Assets/`). Each was then measured the way `build_creature.envelope` measures, and rendered as an orthographic front and side line-up beside a 1.0 × 2.1 m door, the 2.05 m and 1.60 m lines and a 1.80 m reference. The first pass caught the B box-head problem (§4 Risks) and a D load 0.95 m wide (over the 0.9 m door guideline, G1.5); both are fixed below. **Critic rebuild:** the critic pass rebuilt all four the same way from a corrected copy of the data file (separate leg chains, roll in Y, B's narrower rimless lens, C's long sleeves and monochrome, D's new load and face). It also rendered alpha cut-outs from the front, back and side and scaled them to the 20 m screen size (C4). The tables in §7.2–§7.5 and the envelope in §7.1 are from that rebuild.

### 7.1 Envelope of the built blockouts (after flooring)

| | A Floor Sample | B Night Shift | C Duplicate | D Delivery | Limit |
|---|---|---|---|---|---|
| Top of the render pose | 1.92 | 1.87 | 1.79 | 1.95 | ≤ 2.00 rest, ≤ 2.05 moving (G1.2) |
| Face / sensing centre | 1.58 | 1.64 | 1.64 | 1.60 | 1.55–1.75 (G1.3) |
| Half-width at 1.0–2.1 m | 0.42 | 0.425 | 0.34 | 0.43 left / 0.37 right | ≤ 0.45 (≤ 0.9 m across, G1.5); ≤ 0.50 hard |
| Furthest point forward, above 1 m | 0.37 | 0.36 | 0.35 | 0.37 | ≲ 0.38 walking; the BreakDoor pose must stop at ~0.42 |
| Furthest point back, 0.4–1.95 m | 0.28 | 0.28 | 0.29 | **0.34** (load) | probe r 0.30; beyond is visual only and may clip walls in tight turns |
| Window head 2.00 while walking (top + 0.04 bob) | 1.96 ✓ | 1.91 ✓ | 1.83 ✓ | 1.99 ✓ (tight: the plod's bob must stay ≤ 0.05) | the 0.35 m sill still needs a step-over pose (G1.6) |
| Listen-pose head top ≤ 1.65 (G1.8) | ✗ (crown 1.77) | ✗ (1.87) | ✗ (1.95 upright) | ✗ (load 1.95) | none of the four meets it; ask the map chat to test the head top (or the renderer bounds) in `Arrive` (§9) |
| Blockout triangles (Skin + Subsurf 2) | 10.0 k | 8.9 k | 8.5 k | 8.1 k | production 8–12 k (G4.1); these blockouts are not retopologised |

### 7.2 A — Floor Sample

**Render pose: "showroom walk" (the Hunt stalk).** Mid-stride, left foot forward (toe at y −0.37), right heel lifted 2 cm. Hands clasped low in front (left over right, z ≈ 1.04), elbows out so the arm loops stay open. Torso near-upright (pelvis-to-chest-top pitch ≈ 13°). Neck jutting forward and down 45°. Head pitched 22° down and rolled 6° toward its right shoulder (rot Y −6). The yoke rolled 1.5° so its left end is about 1 cm high (rot Y −1.5; the asymmetry of the current brief, `RELAY_MODEL_RIG_RESEARCH.md`). The trousers hang from `seat_l/_r` inside the jacket skirt.

Second pose for the doorway panel (BreakDoor reveal), changing only these joints: elbows (±0.355, −0.218, 1.437), wrists (±0.14, −0.385, 1.206), hands (±0.14, −0.395, 1.35), fingers up and the palms flat toward −Y on the leaf plane (0.425 m in front of the axis). Recompute the derived sleeve, cuff and wrist-in joints along the new elbow→wrist line with the same fractions. Head pitch 5° (lifted, so the CRT glass faces the lit room). Leave everything else as below. (Critic: the first version's elbows (±0.30, −0.33, 1.38), wrists (±0.16, −0.42, 1.27) and hands (±0.10, −0.44, 1.25) stretched the upper arm from 0.35 to 0.44 m and shrank the forearm from 0.36 to 0.20 m, which no rig can reach. It also put the hands 2 cm past the leaf. The pose above keeps the left side's bone lengths: 0.348, 0.357 and 0.144 m.)

##### A joints

| Joint | Left / centre: (x, y, z) | r | Right: (x, y, z) | r | Note |
|---|---|---|---|---|---|
| pelvis | (0, 0.04, 1.04) | (0.18, 0.13) | | | |
| belly | (0, 0, 1.24) | (0.165, 0.125) | | | |
| chest | (0, -0.07, 1.49) | (0.235, 0.16) | | | |
| chest_top | (0, -0.12, 1.73) | (0.22, 0.135) | | | |
| shoulder_l / _r | (0.3, -0.1, 1.76) | 0.095 | (-0.3, -0.1, 1.745) | 0.095 |  |
| elbow_l / _r | (0.32, -0.17, 1.42) | 0.075 | (-0.31, -0.15, 1.41) | 0.075 |  |
| wrist_l / _r | (0.12, -0.29, 1.15) | 0.042 | (-0.12, -0.27, 1.17) | 0.042 |  |
| hand_l / _r | (0.03, -0.31, 1.04) | (0.042, 0.058) | (-0.04, -0.29, 1.06) | (0.042, 0.058) |  |
| neck_base | (0, -0.17, 1.76) | 0.065 | | | |
| neck | (0, -0.21, 1.72) | 0.058 | | | |
| hip_l / _r | (0.11, 0.05, 0.99) | 0.12 | (-0.11, 0.07, 0.99) | 0.12 |  |
| knee_l / _r | (0.12, -0.11, 0.545) | 0.088 | (-0.12, 0.18, 0.545) | 0.088 |  |
| ankle_l / _r | (0.12, -0.15, 0.1) | 0.075 | (-0.12, 0.27, 0.12) | 0.075 |  |
| toe_l / _r | (0.12, -0.37, 0.05) | (0.066, 0.05) | (-0.12, 0.08, 0.05) | (0.066, 0.05) |  |
| sleeve_l / _r | (0.16, -0.266, 1.204) | 0.056 | (-0.158, -0.246, 1.218) | 0.056 | derived: elbow→wrist 0.80 |
| cuffa_l / _r | (0.168, -0.261, 1.215) | 0.05 | (-0.166, -0.241, 1.228) | 0.05 | derived: elbow→wrist 0.76 |
| cuffb_l / _r | (0.14, -0.278, 1.177) | 0.047 | (-0.139, -0.258, 1.194) | 0.047 | derived: elbow→wrist 0.90 |
| wristin_l / _r | (0.156, -0.268, 1.199) | 0.036 | (-0.154, -0.248, 1.213) | 0.036 | derived: elbow→wrist 0.82 |
| shin_l / _r | (0.12, -0.139, 0.225) | 0.05 | (-0.12, 0.245, 0.239) | 0.05 | derived: knee→ankle 0.72 |
| shoe_l / _r | (0.12, -0.15, 0.1) | 0.06 | (-0.12, 0.27, 0.12) | 0.06 | derived: = ankle |
| seat_l / _r | (0.08, 0.05, 1.07) | 0.11 | (-0.08, 0.06, 1.07) | 0.11 | leg-chain root, inside the jacket (one chain per leg) |

##### A skin parts (one Skin-modifier object each)

| Part | Slot | Bones (joint pairs) |
|---|---|---|
| jacket | `Prop_FabricNavy` | pelvis–belly, belly–chest, chest–chest_top, chest_top–shoulder_l, shoulder_l–elbow_l, elbow_l–sleeve_l, chest_top–shoulder_r, shoulder_r–elbow_r, elbow_r–sleeve_r |
| trousers | `Prop_FabricNavy` | seat_l–hip_l, hip_l–knee_l, knee_l–ankle_l, seat_r–hip_r, hip_r–knee_r, knee_r–ankle_r |
| neck | `Creature_ShellSatin` | neck_base–neck |
| cuff_l | `Prop_PlasticWhite` | cuffa_l–cuffb_l |
| cuff_r | `Prop_PlasticWhite` | cuffa_r–cuffb_r |
| hand_l | `Creature_ShellSatin` | wristin_l–wrist_l, wrist_l–hand_l |
| hand_r | `Creature_ShellSatin` | wristin_r–wrist_r, wrist_r–hand_r |
| shoe_l | `Prop_PlasticBlack` | shin_l–shoe_l, shoe_l–toe_l |
| shoe_r | `Prop_PlasticBlack` | shin_r–shoe_r, shoe_r–toe_r |

##### A rigid parts (kitlib primitives; loc = centre; rot = degrees XYZ)

| Part | Primitive | Size | loc | rot | Slot |
|---|---|---|---|---|---|
| head shell | ellipsoid | (0.2, 0.23, 0.27) | (0.01, -0.235, 1.645) | (22, -6, 0) | `Creature_ShellSatin` |
| face glass (CRT) | bulged_panel | 0.12 × 0.15, bulge 0.012 | (0.01, -0.337, 1.598) | (22, -6, 0) | `Prop_GlassCRT` |
| padded yoke (one piece) | soft_box | (0.84, 0.27, 0.15), radius 0.045 | (0, -0.09, 1.845) | (8, -1.5, 0) | `Prop_FabricNavy` |
| jacket skirt | soft_box | (0.4, 0.29, 0.24), radius 0.08 | (0, 0.03, 1.03) | (0, 0, 0) | `Prop_FabricNavy` |
| shirt front | box | (0.13, 0.02, 0.22) | (0, -0.255, 1.62) | (6, 0, 0) | `Prop_PlasticWhite` |
| collar | cylinder | r 0.078, depth 0.05 | (0, -0.175, 1.755) | (-45, 0, 0) | `Prop_PlasticWhite` |
| badge (blank) | box | (0.055, 0.006, 0.085) | (0.1, -0.238, 1.43) | (6, 0, 0) | `Prop_PlasticWhite` |
| swing tag | box | (0.07, 0.004, 0.11) | (0.06, -0.33, 0.94) | (0, 0, 8) | `Prop_Paper` |

### 7.3 B — Night Shift

**Render pose: "shrugged stalk" (Hunt).** Left foot forward, knees soft. Shoulders shrugged so the trapezius joints (1.84) sit above the deltoids (1.76): no visible neck. The long forearms hang forward, gloves at mid-thigh (z ≈ 0.84), fingers slightly curled. Hood pitched 18° down, so the lens faces forward and down. Tool pouch on the right hip, key ring on the left.

Second pose for the "light is the state" panel: render the same pose twice, lens emission 0 (Listen) and full (Chase, plus a 3 m point light 0.25 m in front of the lens). Add a third render from behind a shut door with only the light leaking round the 0.98 × 2.08 leaf (BreakDoor).

##### B joints

| Joint | Left / centre: (x, y, z) | r | Right: (x, y, z) | r | Note |
|---|---|---|---|---|---|
| pelvis | (0, 0.05, 1.03) | (0.19, 0.145) | | | |
| belly | (0, 0.01, 1.24) | (0.205, 0.155) | | | |
| chest | (0, -0.07, 1.48) | (0.24, 0.165) | | | |
| chest_top | (0, -0.12, 1.69) | (0.21, 0.15) | | | |
| trap_l / _r | (0.15, -0.08, 1.845) | 0.095 | (-0.15, -0.08, 1.835) | 0.095 |  |
| shoulder_l / _r | (0.3, -0.11, 1.76) | 0.105 | (-0.3, -0.11, 1.75) | 0.105 |  |
| elbow_l / _r | (0.35, -0.19, 1.42) | 0.085 | (-0.35, -0.17, 1.41) | 0.085 |  |
| wrist_l / _r | (0.33, -0.3, 1.03) | 0.055 | (-0.34, -0.27, 1.04) | 0.055 |  |
| hand_l / _r | (0.32, -0.33, 0.84) | (0.052, 0.066) | (-0.33, -0.3, 0.85) | (0.052, 0.066) |  |
| neck_base | (0, -0.15, 1.72) | 0.075 | | | |
| neck | (0, -0.18, 1.71) | 0.07 | | | |
| hip_l / _r | (0.115, 0.06, 0.99) | 0.13 | (-0.115, 0.08, 0.99) | 0.13 |  |
| knee_l / _r | (0.13, -0.11, 0.545) | 0.095 | (-0.13, 0.17, 0.53) | 0.095 |  |
| ankle_l / _r | (0.13, -0.13, 0.13) | 0.085 | (-0.13, 0.26, 0.14) | 0.085 |  |
| toe_l / _r | (0.13, -0.33, 0.055) | (0.072, 0.06) | (-0.13, 0.06, 0.055) | (0.072, 0.06) |  |
| sleeve_l / _r | (0.333, -0.285, 1.085) | 0.066 | (-0.341, -0.256, 1.092) | 0.066 | derived: elbow→wrist 0.86 |
| tapea_l / _r | (0.334, -0.278, 1.108) | 0.064 | (-0.342, -0.25, 1.114) | 0.064 | derived: elbow→wrist 0.80 |
| tapeb_l / _r | (0.332, -0.291, 1.061) | 0.062 | (-0.341, -0.262, 1.07) | 0.062 | derived: elbow→wrist 0.92 |
| wristin_l / _r | (0.333, -0.282, 1.092) | 0.046 | (-0.342, -0.254, 1.099) | 0.046 | derived: elbow→wrist 0.84 |
| hema_l / _r | (0.13, -0.126, 0.213) | 0.094 | (-0.13, 0.242, 0.218) | 0.094 | derived: knee→ankle 0.80 |
| hemb_l / _r | (0.13, -0.129, 0.142) | 0.092 | (-0.13, 0.257, 0.152) | 0.092 | derived: knee→ankle 0.97 |
| shin_l / _r | (0.13, -0.124, 0.255) | 0.06 | (-0.13, 0.233, 0.257) | 0.06 | derived: knee→ankle 0.70 |
| boot_l / _r | (0.13, -0.13, 0.13) | 0.07 | (-0.13, 0.26, 0.14) | 0.07 | derived: = ankle |

##### B skin parts (one Skin-modifier object each)

| Part | Slot | Bones (joint pairs) |
|---|---|---|
| coverall | `Creature_TwillSpruce` | pelvis–belly, belly–chest, chest–chest_top, chest_top–trap_l, trap_l–shoulder_l, shoulder_l–elbow_l, elbow_l–sleeve_l, chest_top–trap_r, trap_r–shoulder_r, shoulder_r–elbow_r, elbow_r–sleeve_r, pelvis–hip_l, hip_l–knee_l, knee_l–ankle_l, pelvis–hip_r, hip_r–knee_r, knee_r–ankle_r |
| neck (hood) | `Creature_TwillSpruce` | neck_base–neck |
| tape wrist l | `Creature_TapeSilver` | tapea_l–tapeb_l |
| tape wrist r | `Creature_TapeSilver` | tapea_r–tapeb_r |
| tape ankle l | `Creature_TapeSilver` | hema_l–hemb_l |
| tape ankle r | `Creature_TapeSilver` | hema_r–hemb_r |
| glove l | `Prop_FabricChair` | wristin_l–wrist_l, wrist_l–hand_l |
| glove r | `Prop_FabricChair` | wristin_r–wrist_r, wrist_r–hand_r |
| boot l | `Prop_Vinyl` | shin_l–boot_l, boot_l–toe_l |
| boot r | `Prop_Vinyl` | shin_r–boot_r, boot_r–toe_r |

##### B rigid parts (kitlib primitives; loc = centre; rot = degrees XYZ)

| Part | Primitive | Size | loc | rot | Slot |
|---|---|---|---|---|---|
| hood (twill, drawn tight) | ellipsoid | (0.235, 0.25, 0.29) | (0, -0.2, 1.7) | (18, 0, 0) | `Creature_TwillSpruce` |
| opal lens face (emissive) | bulged_panel | 0.13 × 0.26, bulge 0.01 | (0, -0.318, 1.658) | (18, 0, 0) | `Creature_LensOpal` |
| tool belt | soft_box | (0.46, 0.35, 0.07), radius 0.03 | (0, 0.02, 1.09) | (0, 0, 0) | `Prop_Vinyl` |
| tool pouch | box | (0.13, 0.08, 0.17) | (-0.23, -0.02, 1.01) | (0, 0, -15) | `Prop_Vinyl` |
| key ring | cylinder | r 0.03, depth 0.008 | (0.22, -0.03, 0.99) | (90, 0, 0) | `Prop_Brass` |
| name patch (blank) | box | (0.09, 0.006, 0.05) | (0.11, -0.226, 1.44) | (4, 0, 0) | `Prop_Paper` |

### 7.4 C — Duplicate

**Render pose: "the copy's step" (the Hunt slump it moves in).** Short mid-stride, left foot forward, right heel raised 4 cm. The long trunk is curved forward (waist y +0.07 to chest-top y −0.13). Long paper-white sleeves to the wrist; the legs hang from `waist_l/_r` under the belt. Paunch forward. Arms hanging straight, hands at mid-thigh. Head pushed forward and pitched 8° down, rolled 4° (rot Y 4). The flat face plane is vertical within 8°.

Second pose (Listen, "stands to full height"): chest_top (0, −0.02, 1.68), chest (0, 0.02, 1.44), belly (0, 0.05, 1.16). Knees straightened, hips at 0.84. Head centre (0, −0.08, 1.84) pitched 25° down (face ≈ 1.74, crown ≈ 1.95). Arms straight at the sides. This is the pose that must be indistinguishable from a copy until the head turns.

##### C joints

| Joint | Left / centre: (x, y, z) | r | Right: (x, y, z) | r | Note |
|---|---|---|---|---|---|
| waist | (0, 0.07, 0.95) | (0.18, 0.14) | | | |
| belly | (0, 0.01, 1.12) | (0.225, 0.19) | | | |
| chest | (0, -0.07, 1.4) | (0.215, 0.155) | | | |
| chest_top | (0, -0.13, 1.61) | (0.19, 0.13) | | | |
| shoulder_l / _r | (0.25, -0.12, 1.61) | 0.085 | (-0.25, -0.12, 1.6) | 0.085 |  |
| elbow_l / _r | (0.29, -0.13, 1.32) | 0.055 | (-0.29, -0.11, 1.31) | 0.055 |  |
| wrist_l / _r | (0.29, -0.2, 1.03) | 0.042 | (-0.3, -0.17, 1.02) | 0.042 |  |
| hand_l / _r | (0.29, -0.22, 0.85) | (0.04, 0.056) | (-0.3, -0.19, 0.84) | (0.04, 0.056) |  |
| neck_base | (0, -0.17, 1.63) | 0.065 | | | |
| neck | (0, -0.21, 1.655) | 0.06 | | | |
| hip_l / _r | (0.105, 0.1, 0.82) | 0.115 | (-0.105, 0.12, 0.82) | 0.115 |  |
| knee_l / _r | (0.11, -0.05, 0.46) | 0.08 | (-0.11, 0.21, 0.45) | 0.08 |  |
| ankle_l / _r | (0.11, -0.1, 0.1) | 0.062 | (-0.11, 0.31, 0.12) | 0.062 |  |
| toe_l / _r | (0.11, -0.29, 0.045) | (0.052, 0.045) | (-0.11, 0.13, 0.045) | (0.052, 0.045) |  |
| sleeve_l / _r | (0.29, -0.19, 1.071) | 0.05 | (-0.299, -0.162, 1.061) | 0.05 | derived: elbow→wrist 0.86 |
| shin_l / _r | (0.11, -0.086, 0.201) | 0.045 | (-0.11, 0.282, 0.212) | 0.045 | derived: knee→ankle 0.72 |
| shoe_l / _r | (0.11, -0.1, 0.1) | 0.052 | (-0.11, 0.31, 0.12) | 0.052 | derived: = ankle |
| waist_l / _r | (0.09, 0.08, 0.93) | 0.115 | (-0.09, 0.09, 0.93) | 0.115 | leg-chain root, under the belt (one chain per leg) |
| handin_l / _r | (0.29, -0.189, 1.076) | 0.036 | (-0.298, -0.16, 1.066) | 0.036 | derived: elbow→wrist 0.84 |

##### C skin parts (one Skin-modifier object each)

| Part | Slot | Bones (joint pairs) |
|---|---|---|
| shirt | `Prop_Paper` | waist–belly, belly–chest, chest–chest_top, chest_top–shoulder_l, shoulder_l–elbow_l, elbow_l–sleeve_l, chest_top–shoulder_r, shoulder_r–elbow_r, elbow_r–sleeve_r |
| trousers | `Creature_Toner` | waist_l–hip_l, hip_l–knee_l, knee_l–ankle_l, waist_r–hip_r, hip_r–knee_r, knee_r–ankle_r |
| neck | `Prop_Paper` | neck_base–neck |
| hand_l | `Prop_Paper` | handin_l–wrist_l, wrist_l–hand_l |
| hand_r | `Prop_Paper` | handin_r–wrist_r, wrist_r–hand_r |
| shoe_l | `Creature_Toner` | shin_l–shoe_l, shoe_l–toe_l |
| shoe_r | `Creature_Toner` | shin_r–shoe_r, shoe_r–toe_r |

##### C rigid parts (kitlib primitives; loc = centre; rot = degrees XYZ)

| Part | Primitive | Size | loc | rot | Slot |
|---|---|---|---|---|---|
| head (toner black) | ellipsoid | (0.19, 0.21, 0.25) | (0, -0.235, 1.68) | (8, 4, 0) | `Creature_Toner` |
| printed face (flat) | box | (0.155, 0.012, 0.2) | (0, -0.333, 1.656) | (8, 4, 0) | `Prop_Paper` |
| tie | box | (0.075, 0.015, 0.38) | (0, -0.232, 1.42) | (8, 0, 0) | `Creature_Toner` |
| belt | soft_box | (0.39, 0.31, 0.045), radius 0.02 | (0, 0.06, 0.95) | (0, 0, 0) | `Creature_Toner` |
| collar | cylinder | r 0.078, depth 0.045 | (0, -0.175, 1.635) | (-60, 0, 0) | `Prop_Paper` |

### 7.5 D — Delivery

**Render pose: "carry" (Hunt plod).** Left foot forward with both knees bent (hips 0.86). Torso pitched about 26°. The load sits on the upper back, pitched 20° with the torso, rolled −11° (rot Y −11, its right side lower) and shifted 3 cm toward its left shoulder. The trousers hang from `seat_l/_r` inside the jacket. Head hangs under the load's front lip, pitched 30° down. Arms hang forward, gloves at z 0.70 (left) and 0.74 (right), the right hand slightly behind (asymmetry).

Second pose (BreakDoor ram): rotate the whole upper body (chest and above, including the load) 30° about Z so the load's front-left corner leads, **and pitch it about 8° further forward from the hips**. Drop the pelvis 4 cm. The load's leading top corner then reaches y ≈ −0.43 at z ≈ 1.7, the leaf plane when it stands 0.45 m from the crossing line (§2). Gloves come up to the leaf at z ≈ 1.2. (Critic: the turn alone stops the corner at about 0.34 m in front of the axis with this load, and at about 0.37 m with the first one, short of the leaf. Checked by transforming the load's corners.)

##### D joints

| Joint | Left / centre: (x, y, z) | r | Right: (x, y, z) | r | Note |
|---|---|---|---|---|---|
| pelvis | (0, 0.14, 0.9) | (0.18, 0.14) | | | |
| belly | (0, 0.06, 1.1) | (0.19, 0.15) | | | |
| chest | (0, -0.04, 1.3) | (0.22, 0.16) | | | |
| chest_top | (0, -0.13, 1.46) | (0.2, 0.14) | | | |
| shoulder_l / _r | (0.25, -0.11, 1.46) | 0.1 | (-0.25, -0.11, 1.45) | 0.1 |  |
| elbow_l / _r | (0.3, -0.24, 1.16) | 0.075 | (-0.3, -0.22, 1.17) | 0.075 |  |
| wrist_l / _r | (0.27, -0.33, 0.86) | 0.055 | (-0.27, -0.29, 0.89) | 0.055 |  |
| hand_l / _r | (0.25, -0.36, 0.7) | (0.058, 0.075) | (-0.25, -0.31, 0.74) | (0.058, 0.075) |  |
| neck_base | (0, -0.17, 1.5) | 0.068 | | | |
| neck | (0, -0.21, 1.54) | 0.062 | | | |
| hip_l / _r | (0.11, 0.16, 0.86) | 0.12 | (-0.11, 0.18, 0.86) | 0.12 |  |
| knee_l / _r | (0.13, -0.1, 0.5) | 0.09 | (-0.13, 0.12, 0.48) | 0.09 |  |
| ankle_l / _r | (0.13, -0.08, 0.11) | 0.075 | (-0.13, 0.32, 0.13) | 0.075 |  |
| toe_l / _r | (0.13, -0.29, 0.055) | (0.078, 0.065) | (-0.13, 0.12, 0.055) | (0.078, 0.065) |  |
| sleeve_l / _r | (0.275, -0.317, 0.905) | 0.065 | (-0.275, -0.28, 0.932) | 0.065 | derived: elbow→wrist 0.85 |
| wristin_l / _r | (0.276, -0.312, 0.92) | 0.052 | (-0.276, -0.276, 0.946) | 0.052 | derived: elbow→wrist 0.80 |
| shin_l / _r | (0.13, -0.086, 0.227) | 0.065 | (-0.13, 0.26, 0.235) | 0.065 | derived: knee→ankle 0.70 |
| boot_l / _r | (0.13, -0.08, 0.11) | 0.075 | (-0.13, 0.32, 0.13) | 0.075 | derived: = ankle |
| seat_l / _r | (0.08, 0.15, 0.93) | 0.11 | (-0.08, 0.16, 0.93) | 0.11 | leg-chain root, inside the jacket (one chain per leg) |

##### D skin parts (one Skin-modifier object each)

| Part | Slot | Bones (joint pairs) |
|---|---|---|
| jacket | `Creature_CanvasBrown` | pelvis–belly, belly–chest, chest–chest_top, chest_top–shoulder_l, shoulder_l–elbow_l, elbow_l–sleeve_l, chest_top–shoulder_r, shoulder_r–elbow_r, elbow_r–sleeve_r |
| trousers | `Prop_FabricCharcoal` | seat_l–hip_l, hip_l–knee_l, knee_l–ankle_l, seat_r–hip_r, hip_r–knee_r, knee_r–ankle_r |
| neck | `Prop_FabricCharcoal` | neck_base–neck |
| glove l | `Prop_Paper` | wristin_l–wrist_l, wrist_l–hand_l |
| glove r | `Prop_Paper` | wristin_r–wrist_r, wrist_r–hand_r |
| boot l | `Prop_Vinyl` | shin_l–boot_l, boot_l–toe_l |
| boot r | `Prop_Vinyl` | shin_r–boot_r, boot_r–toe_r |

##### D rigid parts (kitlib primitives; loc = centre; rot = degrees XYZ)

| Part | Primitive | Size | loc | rot | Slot |
|---|---|---|---|---|---|
| head in knit watch cap | ellipsoid | (0.18, 0.21, 0.235) | (0, -0.235, 1.615) | (30, 0, 0) | `Prop_FabricCharcoal` |
| load (quilted pad bundle) | soft_box | (0.72, 0.42, 0.5), radius 0.05, puff 0.04 | (0.03, 0.06, 1.62) | (20, -11, 0) | `Creature_PadNavy` |
| binding top-front | box | (0.62, 0.035, 0.035) | (0.005, -0.215, 1.746) | (20, -11, 0) | `Prop_Paper` |
| shipping label | box | (0.2, 0.26, 0.006) | (0.067, -0.061, 1.848) | (20, -11, 0) | `Prop_Paper` |
| strap L | tube | r 0.02 through (0.164, -0.022, 1.876) → (0.205, -0.178, 1.664) → (0.16, -0.27, 1.46) → (0, -0.24, 1.28) → (-0.17, -0.12, 1.1) | — | — | `Prop_FabricChair` |
| strap R | tube | r 0.02 through (-0.19, -0.022, 1.807) → (-0.148, -0.178, 1.595) → (-0.15, -0.27, 1.45) → (0, -0.24, 1.26) → (0.17, -0.12, 1.08) | — | — | `Prop_FabricChair` |
| buckle | box | (0.06, 0.02, 0.05) | (0, -0.255, 1.27) | (0, 0, 0) | `Prop_Chrome` |
| cap cuff (ecru, turned up at the brow) | ellipsoid | (0.2, 0.23, 0.065) | (0, -0.268, 1.648) | (30, 0, 0) | `Prop_Paper` |

### 7.6 Pre-render brief for the Figma round (same five panels for every direction)

02 §5 proposed the panel set. These are the numbers that make the comparison fair. Render each direction from its blockout, in its render pose unless a panel says otherwise.

| Panel | Camera | Set | What Red should judge |
|---|---|---|---|
| 1 Proportion sheet | Orthographic front and side | 1.0 × 2.1 m door; 2.05 m, 1.60 m and 2.40 m lines; the `Ref_Human180` module (1.80 m) beside it | Fit, mass, the "too big for the room" read, the tell |
| 2 12 m silhouette | Perspective, **72° vertical FOV**, eye 1.62 m, figure 12 m away in a 3 m-wide corridor | One troffer per 3 m cell: 0.6 × 1.2 m lens, spot 162°/96°, colour (1, 0.96, 0.88); the figure under a lit cell, the next cell dead | Is it identifiable at ≈ 125 px? Render a black-cut-out version too (G3.3), and a strip of all four cut-outs at the 20 m size (≈ 74 px) from the front, back and side (C4) |
| 3 Doorway | Same camera, 3 m from a 1.0 × 2.1 m door; the room behind lit, the near side dim | The second (BreakDoor reveal) pose for A and D; the lit lens for B; the Listen copy pose for C | The hero shot: silhouette in a lightbox (02 §2.7.4) |
| 4 Catch portrait | Same camera, **0.7 m** away, top light only | Frame band 1.11–2.13 m (02 §1) | What fills the screen when it catches you |
| 5 Value check | Panel 2's camera | (a) Level 0: paper #D2C27C, carpet #9A8558, ceiling #D9D2BF, grade WB +9 / tint −7, sat −8, grain 0.22. (b) Office: drywall #BDB6A4, carpet #5B636B, cubicle #4A535C, ceiling #DCD8CC, Office grade (WB +1 / tint −14, sat −22, grain 0.18), fog exp² 0.018 #3B3F35 (03 §3.3; synthesis decision 5) | Greyscale thumbnails on both (G3.2); which element carries each zone |

For B, add the Listen-dark vs Chase-lit pair and the door-gap leak (§7.3). For C, add one panel with three copies and the live one with its head turned, staged as a print run in an Office room, not in a corridor. Show panel 1 of C to Red cold, before the pitch: if his first read is *The Exit 8*, C fails its originality test (§5 Risks). Label every panel with the direction letter and name only. Put the pitch and the rubric score (§8) in the frame's header, not on the image.

## 8. Scoring against the gameplay-tech rubric, and a recommendation

### 8.1 Gates (03 §8)

All four pass the gates that can be judged on paper. The table lists only exceptions and items still to prove.

| Gate | A | B | C | D |
|---|---|---|---|---|
| G1.1–G1.5, G1.7 fit | ✓ (§7.1) | ✓ | ✓ | ✓; the load extends 0.34 m behind the axis and 0.43 m to its left (visual only) |
| G1.6 window sill | step-over pose needed | same | same | same, and the load top is 1.99 with bob under a 2.00 window head: tight |
| G1.8 Listen head ≤ 1.65 | ✗: map-chat test (§9) | ✗ | ✗ | ✗ |
| G3.1 two values ≥ 3 : 1 | 9.5 : 1 shell/suit | 9.2 : 1 lens/coverall by albedo, and the lens is self-lit | 11.8 : 1 shirt/trousers | 9.2 : 1 gloves/jacket; 8.0 : 1 cap cuff/cap |
| G3.4 features ≥ 0.10–0.15 m | CRT glass 0.12 × 0.15 ✓ | lens 0.13 × 0.26 ✓ | face 0.155 × 0.20 ✓ | the cap cuff is 6.5 cm tall (close range only; the read is the load) |
| G4.3 procedural-friendly | ✓ rigid seams | ✓ | ⚠ long soft trunk | ⚠ straps over the shoulders |
| G5.1 originality | ✓ after the critic's pitch change (watch Slender Man, Coil-head and Dark Deception's Gold Watchers, §3) | ✓ after the rim and proportion change (watch object-heads, §4) | ⚠ *The Exit 8* overlap reduced, not removed; panel 1 decides (§5) | ✓ after the face change (watch the furniture-fusion line and the *Little Nightmares* Janitor, §6) |

### 8.2 Rubric (03 §9: score 1–5 × weight, total ÷ 5, out of 100)

| Direction | 1 Silh. ×20 | 2 States ×15 | 3 Fear ×15 | 4 Relay ×10 | 5 World ×10 | 6 Cost ×15 | 7 Margin ×10 | 8 IP ×5 | **Total /100** |
|---|---|---|---|---|---|---|---|---|---|
| A Floor Sample | 4 → 80 | 4 → 60 | 3 → 45 | 4 → 40 | 5 → 50 | 5 → 75 | 5 → 50 | 3 → 15 | **83** |
| B Night Shift | 4 → 80 | 5 → 75 | 4 → 60 | 4 → 40 | 5 → 50 | 4 → 60 | 5 → 50 | 3 → 15 | **86** |
| C Duplicate | 3 → 60 | 4 → 60 | 5 → 75 | 5 → 50 | 4 → 40 | 3 → 45 | 3 → 30 | 2 → 10 | **74** |
| D Delivery | 5 → 100 | 4 → 60 | 3 → 45 | 4 → 40 | 4 → 40 | 3 → 45 | 3 → 30 | 4 → 20 | **76** |

Why each score:
- **Silhouette.**
  - A: the T reads in a flash and the head-below-shoulders is unmistakable, but the Office read depends on the small pale head and collar.
  - B: the shrug plus a self-lit face reads anywhere, even in the dark, but the body itself is the plainest mass.
  - C: the smallest and least massive; the Level 0 read depends on the toner edge.
  - D: the boldest, most massive and asymmetric shape; it cures "spindly" outright. It keeps its 5 only with the critic's square-cornered, tilted load: the first, rounder mound read from the front at 20 m as an oversized head (C4).
- **States.**
  - B gets 5 because its light makes every state visible, even through a shut door.
  - A (clasped versus open hands, latched versus fluid), C (frozen copy versus head-turn versus head-locked chase) and D (breath, plod, ram) each change category clearly but only in the body.
- **Fear.**
  - C gets 5: which copy is live, and a face with no relief.
  - B gets 4: a face pressed behind a lit lens.
  - A and D get 3: familiar types (a mannequin; a burdened man), so menace must come from behaviour.
- **Relay.**
  - C: generation loss and the repeater.
  - A: re-staging and the same stock tag.
  - B: the starter that keeps trying and the troffer that strikes on arrival.
  - D: the courier relay, a fresh carrier with the same load.
  - All four make the name visible. C's is also mechanical (the generation counter).
- **World.**
  - A (the store is the Backrooms' own origin) and B (the troffer is its anatomy) belong in both zones.
  - C is Office-first.
  - D is store-and-stockroom-first.
- **Cost.** A is about 1 week. B adds an emissive state hook. C needs face art, copies and gait audio. D needs load-sway tuning (§3–§6).
- **Margin.**
  - A and B solve eye height, door and ceiling by construction.
  - C needs the gait-audio change and a Listen pose that stands to 1.95.
  - D sits at the width and window limits and extends past the probe at the back.
- **IP distance.**
  - D has no close neighbour once the taped eyes are gone (they put it near the *Little Nightmares* Janitor).
  - A (Slender Man, mannequins, Dark Deception's Gold Watchers and Malak) and B (object-heads) each need the steering in their Risks lines.
  - C drops from 3 to 2 (critic): an office man in a white shirt, repeated in a copy-paste space with one changed copy to spot, is *The Exit 8*'s premise as well as the IP's own copies-of-people principle. The flat printed face separates it only on inspection.

### 8.3 Recommendation (all four stay on the table for Red)

1. **Lead the Figma round with B, "Night Shift" (86).** It is the only direction that could exist only in FrontRooms: it is made of the game's own light system. It turns the AI state into something seen (through a door, across a dead cell, over a cubicle panel) without UI. That is the "visible state change" lesson taken from *Dark Deception* (02 §3). Its open risk is visual: panel 3 (doorway at 3 m) must prove that the hood plus flat lens does **not** read as a TV-head. The critic pass already removed the bezel and the screen proportions (§4). If it still does, drop to A. Its second weakness is that, with the lens dark, its outline is the plainest of the four at 20 m (C4).
2. **A, "Floor Sample" (83), is the safe pick.** It is the cheapest and fits every number by construction, and it is closest to the current pale-head language and to 04's recommendation. It is also the fallback if B fails panel 3. Its weakness is familiarity.
3. **Keep D, "Delivery" (76), as the anti-spindly extreme.** It has the best silhouette and door moment, and the weakest face.
4. **Keep C, "Duplicate" (74), as the strongest idea for fear and for the name**, but it is the most expensive and carries the highest IP risk (*The Exit 8*). Its copy and generation-loss mechanics can be borrowed by any direction later.

**Traits that carry over whatever Red picks** (system-level, not tied to a body):
- the same stock number or label on every re-arrival;
- a relay click at the arrival point;
- troffers that buzz up or strike within a cell;
- latched Listen/Search versus fluid Hunt/Chase;
- footstep audio driven from the gait phase;
- retiring the mid-tone #A99E78 detail colour (04 §9.3).

**One combination to avoid:** B's lens face on A's suit. A suited figure with an object for a head is exactly the object-headed humanoid read (§4 Risks).

## 9. Open questions and hand-offs

**For Red.**
1. Which directions to pre-render. Suggested: all four in the five panels of §7.6, with B and A first.
2. B: is it acceptable that the Relay can be seen in the dark by its own light (lens off in Listen, dim in Hunt, full in Chase)?
3. C: are static copies wanted? They need placement code in the map.
4. Hunt speed: keep 2.6 m/s and make the run-speed walk the uncanny trait (A, B and D are designed for it), or lower it to about 2.2 m/s (03 §10)? C shuffles either way.
5. A first-sight camera reaction (a short grain or chromatic-aberration spike): wanted, or too close to Slender's static (03 §10)?
6. C: look at panel 1 before reading the pitch. Does it read first as *The Exit 8*'s man? If yes, keep C's mechanics and drop its body (§5 Risks, §8.3).

**For the map chat** (`FrontRoomsMap/*`, `FrontRooms3DGame.cs`):
1. `Arrive` tests only the eye point. Every direction's Listen head top is 1.77–1.95 m, above the 1.65 m cubicle line (G1.8), so test the head top or the renderer bounds too.
2. 03 §5.4's hooks:
   - expose `ListenTarget`;
   - give Search its own rig state;
   - mark the final `DoorBlow`;
   - drive the footstep audio from the gait phase (C needs this; D needs it for a plod that is not a lunge, §6).
3. B only: a call that strikes a dead troffer within one cell of the arrival point (the per-fixture flicker already exists).
4. C only: a way to place 2–3 static copies in Office rooms (at most 3 per room, as a print run against a wall or among desks, never in a corridor; §5).
5. Window crossing (G1.6): a flag the rig can read while the body is inside a broken window, for a step-over pose.

**For the visual chat and the creature-pipeline owner** (`Tools/Blender/frontrooms_kit/creature_lib.py`, `build_creature.py`, added at 18:30–18:36 today):
1. ~~Add `bpy.context.view_layer.update()` at the top of `creature_lib.floor_parts`.~~ Done: the update call is in `floor_parts` as of 19:02 (§7.0).
2. Add the new slots to `FrontRoomsRenderSetup`. They are already in `kitlib.SLOTS` as of 19:02. After the critic pass, `Creature_TieOxblood` is no longer used by any spec, and D no longer uses `Creature_TapeSilver` (B still does):
   - `Creature_ShellSatin` #DAD5C9
   - `Creature_TwillSpruce` #2E3B33
   - `Creature_TapeSilver` #B8B8B4
   - `Creature_LensOpal` #E8E4D8 (emissive)
   - `Creature_Toner` #1D1D1C
   - `Creature_TieOxblood` #5B2A2A
   - `Creature_PadNavy` #262C3A
   - `Creature_CanvasBrown` #3A2E24
3. The FBX export needs `ARMATURE` in `object_types` (03 §5.3).
4. Rebuild `FrontRoomsRelayRig` so bone offsets come from the imported armature. Collapse the 16 renderers to 1 skinned mesh. Add a rim term and prewarm the shader (03 §10).
5. The §7 specs are in `creature_lib`'s own format; a `creatures/hunter_a.py` … `hunter_d.py` module per direction can paste them directly. The first checked copy (data file, runner, line-up renders, `envelopes.json`) is in this session's scratchpad under `hunter_specs/`. The critic's corrected copy is under `critic_hunter/`: `specs_fix.py`, `run_check.py`, `specs_fix_front.png`, `specs_fix_side.png`, and the 20 m cut-outs `cut20_specs_orig.png` and `cut20_specs_fix.png`. Neither is in the project.
6. The §7 joints are a posed sculpt, not an armature. Left and right bone lengths differ by up to 8 % (A forearm; D upper arm, forearm and hand) and 13 % (D thigh). Build the production armature from the left side and mirror it, then pose it.

## Sources

**Fetched for this synthesis (WebFetch, 2026-10-02):**
- Wikipedia, Fluorescent lamp ("Preheating": a glow-switch starter cycles until the lamp strikes; a failing tube cycles repeatedly) — https://en.wikipedia.org/wiki/Fluorescent_lamp
- Wikipedia, Generation loss (successive photocopies distort and degrade) — https://en.wikipedia.org/wiki/Generation_loss
- Wikipedia, Photocopier (xerography spread through offices in the 1960s–1980s; toner sticks to the charged dark areas) — https://en.wikipedia.org/wiki/Photocopier
- Wikipedia, Mannequin (fibreglass and plastic as today's materials; the page does **not** mention detachable limbs, stands or 1980s–90s history, so the seam positions stay UNVERIFIED as in 04 §6.2) — https://en.wikipedia.org/wiki/Mannequin
- Wikipedia, Skibidi Toilet (humanoids with cameras, speakers and televisions for heads; series from 7 February 2023) — https://en.wikipedia.org/wiki/Skibidi_Toilet
- Wikipedia, Moving company (furniture pads, dollies and cargo belts as moving equipment) — https://en.wikipedia.org/wiki/Moving_company
- Wikipedia, Pony Express (157 relay stations and about 190 stations in all, fresh horses, the *mochila* moved from saddle to saddle; 1860–61; the first version said "about 190 relay stations", corrected in the critic pass) — https://en.wikipedia.org/wiki/Pony_Express
- Etymonline, relay (from Old French *relais*, hounds placed along a line of chase; "to leave (dogs) behind (in order to take fresh ones)") — https://www.etymonline.com/word/relay
- Tried, not used: https://en.wikipedia.org/wiki/Moving_blanket (HTTP 404).

**Cited through the research reports** (each report carries its own fetched URLs): `01_ip_entities.md`, `02_creature_craft.md`, `03_gameplay_tech.md`, `04_period_wardrobe.md` in this folder.

**Project files read:** `Documentation/RELAY_MODEL_RIG_RESEARCH.md`, `LEVELS_AND_ENTITIES.md`, `LEVEL_MODULE_SPEC.md`, `VISUAL_RESEARCH_LOOKDEV.md`, `research/office_and_film/10_synthesis.md` (§0, §1a T24, §5.2, Q12), `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs`, `FrontRoomsMap/FrontRoomsModuleUnits.cs` (l.92), `Assets/Scripts/FrontRoomsHunter.cs` (tuning), `Assets/Scripts/FrontRoomsRelayRig.cs`, `Assets/Scripts/Office/FrontRoomsOfficeKit.cs` (`Kit_Copier`), `Tools/Blender/frontrooms_kit/kitlib.py`, `creature_lib.py`, `build_creature.py`, `creatures/ref_human.py`.

**UNVERIFIED in this synthesis:**
- The audible "click" of a glow-switch starter. The fetched page describes the cycling, not the sound; the click is common experience.
- Mannequin seams at fixed joints (04 §6.2; not on the fetched Mannequin page).
- That a loaded carrier walks with bent knees. This is used only as a design choice for D, not as a fact.
- "Standing height" figures in §3–§6 are estimates for an upright pose that was not built. Only the render poses were built and measured (§7.1).

## Critic notes (adversarial review, 2026-10-02)

Status: COMPLETE. This is an adversarial pass over this file and reports 01–04. It checked five things: originality, gameplay constraints, evidence, 20 m silhouettes and blockout buildability. Fixes were made in place above and are marked "(Critic: …)" where the reason matters to a reader. C6 lists every change. The critic rebuilt all four blockouts headless (Blender 4.3.0, the project's `creature_lib` and `kitlib` imported read-only) from a corrected copy of the data file in the session scratchpad (`critic_hunter/`). Nothing was written to `Tools/` or `Assets/`.

### C1. Originality

The question for each direction: does it resemble an existing creature too closely, and if so, how was it pushed away?

| Direction | Nearest existing design found | Problem | What changed |
|---|---|---|---|
| A Floor Sample | SCP-173, Coil-head, Weeping Angels, and **Dark Deception's Gold Watchers**, which only move while Doug is not looking at them. Red's primary reference has them. The fan wiki is HTTP 402 to WebFetch; search summary, plus a fetched Steam thread: https://steamcommunity.com/app/332950/discussions/0/2996548763043799353 | The pitch "posed somewhere new every time you look back" *is* the moves-only-when-unwatched premise | Pitch and tell rewritten. It moves openly while watched; only the re-arrival, already hidden by `Arrive`, is unseen. |
| A | Coil-head's spring neck | Stagger had the head "loll on the neck seam", a loose head bobbing on a long neck | The head stays rigid; the yoke tips and one arm swings instead. |
| A | Slender Man (fetched: black suit and tie, white featureless face, created 10 June 2009) and Dark Deception's Malak (a formal suit under a non-human head; fetched GamePretty guide) | A suit with a non-human head is shared by both | Risk lines added. The suit cannot separate A; the hunch, the yoke and the shell head must. |
| A | Pirate Clark (01 §2.1): the film's monster is also a furniture-store figure | Shared origin | Keep the store to the swing tag and display poses. No mascot, branding, uniform or costume. |
| B Night Shift | Object-for-a-head humanoids: Skibidi Toilet's TV Men (fetched: "televisions in place of their heads"), Siren Head's principle | In the line-up the 0.21 × 0.28 m panel in a white rim still read as a screen: 3 : 4 proportions plus a bezel | Lens narrowed to the troffer's 1 : 2 ratio (0.13 × 0.26 m), rim removed, hood edge as frame. |
| B | The dark, featureless, long-armed family (Dullers, the Lifeform; G5.1) | The text said the Listen pose is "a dark shape", and its arms are "long" | An unlit opal lens is still pale by albedo, so the face is never blank in a lit cell. Its fingertips at mid-thigh are ordinary human reach for its size (≈ 0.38 of standing height). Clarified in §4. |
| B | — | One search found no humanoid with a fluorescent lamp for a head (the nearest wiki hit, "Lamp-Reys", is lamprey-like: search result only, UNVERIFIED) | No change; this is not proof that none exists. |
| C Duplicate | ***The Exit 8*'s man.** Fetched (https://en.wikipedia.org/wiki/The_Exit_8): a middle-aged man in work clothes with a briefcase, in a repeating corridor where the player spots anomalies, including the man's "proportion differences". Search summaries put him in a white shirt and dress pants (UNVERIFIED on a fetched page). | Four overlaps: office-man costume, repeating copy-paste space, spot-the-changed-one, a proportion error as the tell. "No jacket, no briefcase" separated nothing. | Black-and-white printed costume (long sleeves, toner tie and trousers). Copies staged as a still print run in Office rooms, never in corridors. The trunk stretch is a fixed trait, not a variation to spot. IP score 3 → 2. Panel 1 is a pass/fail test (§7.6, §9 Q6). **This overlap is reduced, not removed.** |
| C | Kane's and the film's Still Lifes; the wiki's Facelings and Stalkers; the Mandela Catalogue | Copies of a person, an ordinary person with a wrong face | Already steered in §5; the face is printed, not blank, smeared or smiling. No change. |
| D Delivery | A **mascot head**: the round 0.76 × 0.62 m mound, seen from the front at 20 m, reads as one oversized round head (C4). Mascots are excluded (pillar 3) and are Pirate Clark's register. | Front silhouette | Load made square-cornered (radius 0.05), 0.72 × 0.50 m, rolled 11° and offset toward one shoulder. It now reads as a carried slab. |
| D | ***Little Nightmares*' Janitor**: blind, hunts by touch, smell and sound, long arms (fetched: https://www.gamerevolution.com/features/14122-little-nightmares-story-explained-a-look-at-its-monsters-and-ending). Search summaries add bandaged eyes and a hunch (UNVERIFIED). | Taped-over eyes on a hunched sound-hunter. Tape over the eyes *and* mouth also reads as a bound hostage. | Tape removed. An ecru cap cuff at the brow is the light band; the face is hidden by the load's shadow (02 §2.4 option 1). |

Also checked, no issue: SCP-096 (no direction uses the pale, emaciated, long-armed body or a face trigger); Kane's Lifeform and fan-game clones (none of the four is thin, dark and wire-built); the wiki's Smilers, Hounds, Partygoers and Skin-Stealers (no shared feature).

### C2. Gameplay constraints

| Check | Result after the critic rebuild |
|---|---|
| Walking height ≤ 2.05 (rest ≤ 2.00) | A 1.92, B 1.87, C 1.79, D 1.95 (render pose, after flooring). With a 0.04 m bob all stay ≤ 1.99; door head clearance 0.15–0.31 m. C's Listen pose stands to ≈ 1.95–1.98 but is stationary. ✓ |
| 1.0 × 2.1 m door | Half-width A 0.42, B 0.425, C 0.34; D 0.43 on its left and 0.37 on its right (0.80 m across). D's offset side is the one to watch at an off-centre crossing. ✓ |
| Window (head 2.00) | D is 1.99 with the bob: its plod's bob must stay ≤ 0.05. All four still need the step-over pose (G1.6). |
| Sight ray 1.60 | Face centres 1.58–1.64 ✓ (D's light band at 1.65, eyes ≈ 1.60). |
| Probe r 0.30 | D's load reaches 0.34 m behind the axis (was 0.38): visual only. |
| BreakDoor reach (leaf ≈ 0.425 m ahead; standoff 0.45 m verified at `FrontRoomsMapHunter.cs` l.351) | **A's second pose was not reachable**: the upper arm stretched 0.35 → 0.44 m and the forearm shrank 0.36 → 0.20 m. Replaced with an IK-solved pose keeping the bone lengths. **D's ram fell short** (load corner ≈ 0.34 m with the turn alone; ≈ 0.37 m with the first load). Added an 8° forward pitch, which reaches ≈ 0.43 m at z ≈ 1.7. |
| Gait vs footstep timer (0.44 s Hunt) | D's 1.14 m Hunt step is 1.3 × its bent leg and reads as a lunge. It needs the gait-phase audio hook (already needed by C) and a shorter plod (~0.9 m every 0.35 s). |
| Readable states | All four give Listen, Search, Hunt, Chase, BreakDoor and Stagger distinct poses (G2.1). One clarification for B: its "off" lens is pale in lit cells. G1.8 (Listen head ≤ 1.65) still fails for all four; it remains a map-chat test in `Arrive`. |
| Performance | Blockouts 8.1–10.0 k tris; 27–29 bones; 2–3 materials (C now 2). **C's copies** were called cheap because they "batch". Skinned meshes do not batch, and each copy is ≈ 8.5 k tris, so three copies are ≈ 21 % of an Office room's 120 k LOD0 budget. Now: baked static meshes, LOD1 at ≈ 45 % beyond 8 m, at most 3 per room. **A's yoke** was weighted to both clavicles; as one piece it would tear when the shoulders part, so it is now on `chest`. |
| Speeds | `chaseSpeed` 4.2 is the serialised value (`Scenes/FrontRooms3D.unity` l.1018). The brief's 5.4 is not in code. ✓ as stated in §2. |

### C3. Evidence spot-check

Twelve URLs were fetched with WebFetch on 2026-10-02: eight of this file's own and four from the reports it relies on.

| URL | Claim in the docs | Result |
|---|---|---|
| https://www.etymonline.com/word/relay | relay = hounds placed along a chase; "to leave (dogs) behind (in order to take fresh ones)" | ✓ confirmed |
| https://en.wikipedia.org/wiki/Fluorescent_lamp | a glow-switch starter cycles until the lamp strikes; a failing tube cycles repeatedly | ✓ confirmed. No click is mentioned, so the click correctly stays UNVERIFIED. |
| https://en.wikipedia.org/wiki/Pony_Express | "about 190 relay stations" | ✗ **corrected**: the page gives 157 relay stations, and 184, 186 or 190 stations in all in different sentences. The *mochila* moving saddle to saddle and 1860–61 are ✓. |
| https://en.wikipedia.org/wiki/Skibidi_Toilet | humanoids with CCTV cameras, speakers and TVs for heads; from 7 Feb 2023 | ✓ confirmed |
| https://en.wikipedia.org/wiki/Moving_company | dollies, furniture pads, cargo belts | ✓ confirmed |
| https://en.wikipedia.org/wiki/Photocopier | xerography spread 1960s–1980s; toner sticks to the charged dark areas | ✓ confirmed |
| https://en.wikipedia.org/wiki/Generation_loss | successive photocopies distort and degrade | ✓ confirmed |
| https://en.wikipedia.org/wiki/Mannequin | fibreglass and plastic; no seams, stands or 1980s–90s history on the page | ✓ confirmed, including the absences |
| https://en.wikipedia.org/wiki/The_Exit_8 (02) | a middle-aged man in work clothes with a briefcase; anomalies include wrong proportions and walking quickly | ✓ confirmed. The same page's anomaly-spotting loop is what makes C's overlap serious (C1). |
| https://en.wikipedia.org/wiki/Slender_Man (02, 04) | created by Eric Knudsen on Something Awful, 10 June 2009; black suit and tie; white, featureless face | ✓ confirmed |
| https://gamepretty.com/dark-deception-monsters-mortals-monsters-guide/ (02) | Dark Deception's monsters are themed costumes plus one wrong feature | ✓ the monster list matches (Killer Monkeys, Agatha, Golden Watchers, Ugly Ducklings, Gremlin Clowns, Malak). The enraged-recolour claim was not re-checked. |
| https://80.lv/articles/the-internet-finds-the-original-backrooms-location (04) | the Backrooms photo building was Rohner's Furniture, Oshkosh | ✓ confirmed. It gives the address as 811 Oregon Street, while `VISUAL_RESEARCH_LOOKDEV.md` l.11 says 807. That file is not this one; flagged only. |

Also fetched, for C1: the Steam thread on the Gold Watchers (✓), the GameRevolution page on the Janitor (✓), and Siliconera, Nintendo Life, Joysauce and Adrian Hon's Substack on *The Exit 8* (none states the shirt; hence UNVERIFIED). Failed: the Dark Deception fan wiki (HTTP 402), TV Tropes (HTTP 403), and the Automaton article (truncated). Project facts were re-checked in code: `ModuleUnits` l.92, `ProbeBottom/ProbeTop`, `BlowInterval` 0.5, `DoorFallSeconds` 0.25, `SpawnMin/MaxCells` 9/15, `LeashCells` 30, and the 0.45 m standoff. All ✓.

### C4. Silhouettes at 20 m

**Method.** Alpha-only renders of each blockout from the front, back and left side, orthographic. Each was scaled to the 20 m screen size of 03 §2.2 (37 px per metre, so a 2.0 m figure is about 74 px tall) and thresholded into a black cut-out. Pairs were compared by overlap (intersection over union, IoU, with the figures aligned on their body axis and feet). An IoU around 0.6 or above means two cut-outs are hard to tell apart; around 0.4 means clearly different. The images are `cut20_specs_orig.png` and `cut20_specs_fix.png` in the scratchpad's `critic_hunter/`.

| Pair | Front, before → after | Back, before → after | Side, before → after |
|---|---|---|---|
| A–B | 0.58 → 0.58 | 0.59 → 0.59 | 0.64 → 0.65 |
| A–C | 0.39 → 0.41 | 0.39 → 0.41 | 0.50 → 0.52 |
| A–D | 0.48 → 0.47 | 0.45 → 0.44 | 0.43 → 0.41 |
| B–C | 0.50 → 0.52 | 0.50 → 0.53 | 0.64 → 0.65 |
| B–D | 0.52 → 0.52 | 0.49 → 0.49 | 0.52 → 0.51 |
| C–D | 0.51 → 0.54 | 0.49 → 0.52 | 0.42 → 0.44 |

**Reading.**
- **From the front and back, three shapes are genuinely distinct.** A is a T, or a vase: a flat bar on top, a notch where the head hangs, a narrow waist. D is a load on legs. B and C share the third shape: a plain humanoid outline.
- **B and C differ mainly in width**: 0.85 against 0.68 m, about 31 against 25 px. They do not differ in shape. B is a wide, headless block (the hood merges into the shrug); C is narrow with a small head. At 20 m, B is identified by its lit lens and C by its pale shirt, so both depend on light and value, not on outline.
- **In profile only D is distinct.** A, B and C converge (IoU 0.64–0.65 for A–B and B–C): three walking people.
- **D's first front read was a giant round head.** The fix made it a tilted, square-cornered slab. The overlap barely moves, because overlap measures area, but the shape now reads as a carried load. Look at the cut-outs, not only the numbers.
- **Not fixed, by design:** B's and C's plain outlines are their concepts (a worker, a copy of a worker). The optional test for B is a 1.2 m tube carton carried in one hand (§4 Risks). For C, accept the weakest silhouette score (3), as §8 already does.

### C5. Blockout buildability

- **Units and joints.** Metres, Z up, facing −Y, feet on z = 0: ✓. Every bone in every skin part names a defined joint; all four built without error, before and after the fixes. Flooring moves the figures only 1.2–2.2 cm. ✓
- **Rotation convention (fixed).** Every "roll" was written in the Euler Z slot, which is a yaw. §7.0 now defines X = pitch, Y = roll, Z = yaw, and the tables put roll in Y. A's head and yoke, C's head and D's load changed.
- **Leg chains (fixed).** All three trousers parts hung both legs from one pelvis joint, which the library's own comment warns against. In the first line-up this left a flat flap at A's and D's hips. In C it left an arch of trouser legs floating 6 cm under the shirt, the "floating torso" fault 02 §1 found in the current rig. Now each leg is its own chain from `seat_l/_r`, or `waist_l/_r` for C. The rebuild shows clean hips on all four.
- **Second poses.** A's BreakDoor pose was not reachable by any rig; it is IK-solved now (C2). D's ram is fixed (C2). C's Listen pose is given as joint moves and is plausible. B's second pose is a lighting change only.
- **Armature.** The joints are a posed sculpt: left and right bones differ by up to 8 % (A forearm; D arm) and 13 % (D thigh). Build the armature from the left side and mirror it (§9).
- **Pipeline hand-offs already landed.** As of 19:02, `creature_lib.floor_parts` calls `view_layer.update()` itself, and `kitlib.SLOTS` has all eight new `Creature_*` slots, plus `Troffer_Lens` and `Creature_LensDim` from the visual chat. `FrontRoomsRenderSetup` has none of them yet. §7.0 and §9 were updated.
- **No value check exists yet.** The first run's `values_L0paper.png` and `values_officeDark.png` are byte-identical (same MD5): the background swap did not apply. This file never cites them, but panel 5 (§7.6) is the first real greyscale check.
- **B's lens in the blockout** is a flat panel on a curved hood, so its top and bottom stand a few centimetres proud. Production cuts the hood front flat (§4).

### C6. What changed in this file

1. Status line: notes the critic pass.
2. §3 A: pitch and tell rewritten (no moves-when-unwatched); Stagger keeps the head rigid; Risks add the Gold Watchers, Malak and Pirate Clark's store origin; yoke weighted to `chest`; tris 10.0 k.
3. §4 B: lens 0.13 × 0.26 m, no rim (silhouette, measures, key features, materials, 20 m read, Risks); unlit-lens note in Listen; tell narrowed to one tube shadow; name patch moved to the chest (1.44 m) and to `Prop_Paper`; tris 8.9 k.
4. §5 C: monochrome costume with long sleeves; materials 3 → 2 (`Creature_TieOxblood` and `Creature_SkinPale` dropped); copy staging, baking, LOD and cap; *Exit 8* risk rewritten with sources; budget risk added; tris 8.5 k.
5. §6 D: Pony Express count corrected; load 0.72 × 0.42 × 0.50 m, square-cornered, rolled −11°, offset 3 cm, with the binding, label and straps re-seated on it (the first binding sat inside the pad); tape removed for an ecru cap cuff and a shadowed face; neck and face to `Prop_FabricCharcoal`; width, back and top figures; plod note; Janitor and hostage-imagery risks; tris 8.1 k.
6. §7.0: rotation axes defined; separate leg chains required; `floor_parts` fix and kit slots marked as landed; critic rebuild described.
7. §7.1 envelope and §7.2–§7.5 tables regenerated from the corrected build. A's BreakDoor pose IK-solved; D's ram pose adds an 8° pitch; C's and D's render-pose text updated.
8. §7.6: 20 m cut-out strip added to panel 2; C staging and a cold-read test for panel 1.
9. §8: gates updated (D width and window, B and C contrast, feature sizes, G5.1 notes); C's IP 3 → 2, total 75 → 74; D's silhouette score now conditional on the new load; recommendation text updated. The ranking is unchanged: B 86, A 83, D 76, C 74.
10. §9: Red Q6 (the C cold-read); D added to the gait-audio hook; C copies capped at 3; pipeline items 1–2 marked done or narrowed; item 6 (mirror the armature) added; scratchpad paths for the corrected copy.
11. Sources: Pony Express line corrected.
