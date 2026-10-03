# 10 — Hunter (The Relay) redesign: concept directions and blockout specs

Status: IN PROGRESS (2026-10-02). Synthesis of reports 01–04 in this folder. Written incrementally.

## 0. How to read this

- **Inputs.** All four reports in this folder were read in full: `01_ip_entities.md` (IP grammar and what not to copy), `02_creature_craft.md` (craft levers L1–L12, seeds S1–S6), `03_gameplay_tech.md` (hard numbers, gates G1–G5, rubric), `04_period_wardrobe.md` (garments, period objects, measured palettes). Also read in the project: `RELAY_MODEL_RIG_RESEARCH.md`, `LEVELS_AND_ENTITIES.md`, `LEVEL_MODULE_SPEC.md` §1–§8, `VISUAL_RESEARCH_LOOKDEV.md`, `research/office_and_film/10_synthesis.md` (§0, §5.2 slot table), `FrontRoomsMapHunter.cs`, `FrontRoomsHunter.cs` (tuning), `FrontRoomsRelayRig.cs`, `FrontRoomsModuleUnits.cs` l.92, and the kit's `kitlib.py` (`SLOTS`) and `creature_lib.py` / `build_creature.py` (the Skin-modifier blockout pipeline a parallel session added at 18:30–18:36 today).
- **Citations.** "(02 §2.4)" means the claim is sourced in that report, which carries the URL. URLs given inline here were fetched for this synthesis on 2026-10-02. **UNVERIFIED** marks anything not confirmed on a fetched page. Interpretations are marked "Reading:" or are design proposals, which need no source.
- **Originality.** The four directions below are new combinations built from principles. Each has a "Resemblance risk" line that names the nearest existing design and how the direction steers away from it. Nothing is traced from or modelled on another work's creature.
- **The blockout specs (§7)** use the joint names and the data format of `Tools/Blender/frontrooms_kit/creature_lib.py`, so a modeller can type them in by hand or a script can paste them into a `creatures/<name>.py` module. Every spec was built headless in Blender from a copy in the session scratchpad to check its envelope (§7.0). Nothing was written into `Tools/` or `Assets/`.
- **Language.** Directions are named A–D. "Walking height" is the highest point of the figure in the render pose (the stalking pose it moves in); "standing height" is how tall it would be fully upright, which it never is while moving.

## 1. Design pillars: what the research says the Hunter must be

1. **Built to the door, not to a scale.** Rest-pose top ≤ 2.00 m, moving top ≤ 2.05 m, face centred at 1.55–1.70 m on the 1.60 m sight ray (03 §1.1, G1.2–G1.3). The hunch is how a ~2 m body gets its face to 1.6 m, so it is the gameplay eye height and not a style choice (03 §1.1). The head sits at or below the shoulder line, which no person does (02 L1). The same rule keeps the face inside the frame at the 0.7 m catch, where only the band 1.11–2.13 m is visible (02 §1). It reads "too big for the room" through shoulders that nearly fill a 1.0 m door and a mass that nearly reaches its 2.1 m head, not through raw height (01 §7.1).
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
| Eye | 1.60 m (player 1.62 m) | Face or sensing feature centred at 1.55–1.70 m in Hunt; it then sits on the screen's horizon at every distance (03 §2.2). |
| Front reach | the face ≤ ~0.36 m in front of the axis while walking | In BreakDoor it stands with its axis 0.45 m from the crossing line, so the leaf face is ~0.425 m away. The strike (hands, forearms or load) must reach 0.42–0.45 m at 1.0–1.8 m, and the head must not pass the leaf (G2.4). |
| Speeds | Hunt 2.6 m/s, Chase 4.2 m/s (`chaseSpeed`; the 5.4 m/s in the brief is not in code or the level asset); player walk 3.2, sprint 5.5 for 5 s | Steps plant 1.14 m every 0.44 s in Hunt and 1.22 m every 0.29 s in Chase (03 §1.3). At 2.6 m/s a human-proportioned 2 m body is above the walk-to-run Froude limit (03 §1.4): each direction says how it makes that look intended. |
| States | Dormant → Listen 2 s → Hunt → Search 2.5 s → Chase → BreakDoor (5 blows, 2.5 s) → resume; Relay = an unseen re-arrival followed by Listen; Stagger is rig-only | Seven poses or loops (G2.1). Listen is the most-seen still pose (G2.2). |
| Screen | 72° vertical FOV planned: 2.0 m figure ≈ 125 px at 12 m, ≈ 74 px at 20 m; 0.30 m head ≈ 19 px at 12 m (03 §2.2) | Features under ~0.15 m vanish at chase distance. |
| Light/fog | lamps on within 13 m, off past 16 m; fog exp² 0.018 (Office) / 0.024 (Level 0) proposed: 5–8 % at 12 m, 12–21 % at 20 m (03 §3.3) | At 20 m the limit is lamp radius, not fog: a figure there is a shape against whatever lit room or doorway is behind it. |
| Values (albedo, 04 §9) | Level 0 paper #D2C27C, carpet #9A8558, ceiling #D9D2BF; Office drywall #BDB6A4, carpet #5B636B, cubicle #4A535C; lit Office target walls #3C392C | Dark body 7–9 : 1 against Level 0 paper; ~1.5 : 1 against lit Office panels. Pale head ~1.2 : 1 against Level 0 paper, ~4.5 : 1 against the lens-lit Office ceiling. Mid tones (#A99E78 detail, khaki, mauve) fail everywhere. |
| Budget | 1 skinned renderer, 8–12 k tris, 2–3 materials, 24–36 bones, ≤ 4 influences | The production skeleton is 03 §5.4's 26 bones plus the extras each direction lists. |

## 3. Direction A

(to be written)

## 4. Direction B

(to be written)

## 5. Direction C

(to be written)

## 6. Direction D

(to be written)

## 7. Blockout specs (Blender, Skin-modifier)

(to be written)

## 8. Scoring against the gameplay-tech rubric, and a recommendation

(to be written)

## 9. Open questions and hand-offs

(to be written)

## Sources

(to be written)
