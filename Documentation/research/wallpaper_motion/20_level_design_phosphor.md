# Afterglow Blazes: level design proposal for the phosphorescent wallpaper print

Status: proposal only, 2026-10-02. Nothing is implemented. Written by the wallpaper-print chat (a judge-panel workflow: 4 directions, 3 judges per direction, all 4 scored). Most of the build would fall to the map chat (关卡设计), plus some work by the visual chat; see §11.2. Paths are relative to `Frontrooms3D/`. Every gameplay number is marked **SP** (a starting point for playtest). Code facts are given as file:line.

Base design: **Afterglow Blazes (wayfinding)**, which scored highest overall (23 / 30). Grafts taken from the others:
- **threat_intel:** retire the HUD distance readout, permanent BREACH scars, the EAR bloom, and the backlit Relay silhouette.
- **light_economy:** fresh-vs-starved charge physics, a first-dark beat where the lamp dies in view, the drought breaker, and the idea that meaning sits in a world-space mask while narrative owns the glyph substance.
- **anomaly_literacy:** glyph families by silhouette, the physical lie tell, and no strip slips under a readable mark.

---

## 1. Pitch and the player decision it adds

A hidden ZnS:Cu underprint in the Level 0 wallpaper shows only where a cell's own lamp is dead, dying or sagging. Lit walls show nothing, so every lit 3 m module stays identical. In the dark, the paper points:
- **FLOW** (chevrons) lies along the best route to the nearest threshold into a zone you have not visited.
- **HERE** (brackets) frames that door or window.
- **STOP** (bars) marks the mouth of a dead-end pocket.
- **BREACH** (a bracket crossed out) marks a door the Relay broke, which will never shut again.

When the Relay starts a chase, the lamps sag in a wave that runs down the corridors ahead of the player, and the marks in that wave re-point to doors leading away from it.

**The ink knows the building. It does not know the monster.** In calm play it ignores the Relay, so it can lead you straight into a wandering one. Following it also roughly doubles your rate of new thresholds, which speeds up tier escalation.

Decisions it adds:

| When | Decision | Cost of each answer |
|---|---|---|
| Calm | Follow the green to new ground, or go my own way? | Following means faster progress, faster escalation and a blind walk past the Relay. Ignoring it means slower progress and more dead ends. |
| Chase | Which door does the wave point at, and do I spend time reading the end wall? | Reading costs metres at 4.2 m/s. A shut door buys 2.5 s + 0.25 s. |
| Junction | Is that branch a pocket (STOP)? | Entering a pocket during a hunt is the cheapest death in the maze. |
| T4+ (optional) | Is this mark real? It is glowing under a lit lamp. | A forged FLOW leads into a dead end. |

## 2. Rules

1. **Gate.** `G = C × smoothstep(0.55, 0.15, Ls) × weight` (SP).
   - `Ls` is the cell's own lamp level, low-passed with τ 0.35 s (SP). The lamp level is `Fixture.level` (FrontRoomsMapWorld.cs:98), set from `Level()` at :1168.
   - It must never be read from `light.enabled` or `light.intensity`. Those are cut by the distance fade and the start-area hold (:1171-1174), which would make every cell beyond 16 m glow.
   - A lit cell (Ls ≥ 0.55) shows nothing.
2. **Charge physics. This never changes with tier.**
   - Wall light: `W = min(1, L + 0.2 × Σ L of the 4 neighbours)`. Lamps light through walls (FrontRoomsMapWorld.cs:1137-1140).
   - When W > C, C rises toward W with τ 2 s.
   - Otherwise C decays hyperbolically, `C(t) = C₀ / (1 + C₀·t / 8 s)` (SP). This is the second-order recombination shape of real ZnS:Cu afterglow.
   - **Fresh** dark (a lamp that just died) is bright. **Starved** dark (a dead cell among dead neighbours) is faint or blank. Both follow from the physics, so neither looks like a bug.
3. **Carriers.** Only wallpaper carries ink: Level 0 walls and wallpapered columns (LEVEL_MODULE_SPEC.md:57-59). No ink appears on:
   - Office drywall (:58);
   - doors, trim, glass, floors or ceilings;
   - the start area (FrontRoomsMapWorld.cs:389);
   - title stream rooms (10_synthesis.md:217-218).
4. **Messages and glyph families** (the shape is told by silhouette, not detail). Priority is STOP > HERE (or BREACH) > FLOW > GROUND.

   | Message | Family | Meaning | Weight (SP) |
   |---|---|---|---|
   | GROUND | neutral | Plain underprint, no direction | 0.35 |
   | FLOW (dir) | go: open chevrons | The route runs this way along this wall | 1.0 |
   | HERE | threshold: frame brackets | The route leaves through this face's door or window | 1.0 |
   | BREACH (a HERE variant) | stop: bracket with a cross bar | The Relay broke this door. It is passable and will never shut. | 1.0 |
   | STOP | stop: closed horizontal bars | This face is the mouth of a dead-end pocket | 1.0 |
   | Pressure variant (FLOW or HERE) | go or threshold, drawn doubled | Chase routing: a door away from the Relay | 1.0 |

5. **Calm target.** The nearest **new threshold**: a Door or Window edge whose far cell is in a zone not in `zonesVisited` (FrontRooms3DGame.cs:162, 869-877).
   - Unbroken windows cost +4 cells (SP), because breaking glass is heard at 40 × 1.4 = 56 m (FrontRooms3DGame.cs:150; FrontRoomsHunter.cs:32).
   - If `doorsNeedKeys` is on (FrontRoomsLevelProfile.cs:31, false today), the zone's key comes first.
   - Calm routes never read the Relay's position.
6. **Pressure target. By default it is used only while the Relay is in Chase** (this fixes the radar leak).
   - The target is an unbroken, unshut-by-Relay door whose far cell is farther from the Relay (by breadth-first search) than its near cell.
   - Route costs (SP): +6 per cell within 2 steps of the Relay; +2 per cell on its open straight line within 4 cells; +2 for cells it walked through in the last 10 s; −1 per arch edge (arches block sight).
   - Windows and BREACH doors are never pressure targets.
   - Pressure ends when the Relay enters Listen or Wander, or 20 s after the Chase ends (SP).
7. **Only on-route cells point.** The route is a greedy descent of the target field, up to 24 cells (SP). At T0-T1 it also covers cells 1 step off the route. Every other dark cell shows GROUND.
   - Simulation of beacon-seeking walkers, in new zones per 100 cells: when every dark cell points, walkers ping-pong (2.4). On-route only gives 8.0. A random walker scores 5.6.
8. **STOP** marks the mouth cell of each dead-end branch.
   - Branches are found by iterative leaf pruning. Door and window edges count as passable, and the built-area boundary counts as open.
   - The maze has loops (non-tree edges roll Open or Arch at 18-70%, FrontRoomsMap.cs:94-96, 360), so pruning is the exact test. A branch BFS is not.
   - A FLOW route never enters a branch unless its target is inside it.
9. **Truth.** Before T4 the ink never lies. It never points into a dead end, through a BREACH on the pressure route, or at the Relay's cell.
   - From T4 (optional, see §6), a **forged FLOW** may appear. It is the only mark that glows under a lit lamp, and only FLOW is ever forged.
10. **Commit gate.** A cell's message may change only when at least one of these holds:
    - (a) the cell has been unseen for ≥ 0.5 s;
    - (b) its own Ls ≥ 0.8, so the ink is invisible;
    - (c) a sag or wave front is at that cell (a deliberate beat).

    Each cell changes at most once per 2 s (SP). The glow *brightness* may change in view (that is physics). The *message* may not.
11. **Shape is procedural; substance is in B.**
    - The message shape is computed in the shader from world position plus the cell's message code.
    - The print's B channel holds the ink *substance*, which narrative authors per print slice. What you see is the shape drawn in that substance.
    - Print jumps can change the substance (read up close). They can never change the message.
    - Cells with a non-GROUND message take no lamp-dropout strip slips; their print changes only while unseen.
12. **Delivery channels.**
    - Natural dark cells (always on).
    - The first-dark beat (once per run).
    - Calm power sags (periodic, local).
    - The chase wave (rare).
    - The drought breaker (a safety net).
    - The EAR bloom (when the Relay accepts a noise).
13. **Dark is never cover, and tall halls are not refuges.**
    - The Relay's sight is a 12 m ray with no light term (FrontRoomsMapHunter.cs:926-931; FrontRoomsHunter.cs:26).
    - Its speeds have no ceiling-height term.
    - Nothing in the ink or its fiction may imply either.
14. **The HUD stops giving it away.** Today `RELAY nn M` renders every frame (FrontRooms3DGame.cs:1544), and the state text shows HUNT/SEARCH (:1539).
    - Ship with the state text shown only for CHASE and BREAKING DOOR.
    - Move the distance readout behind an accessibility assist.
15. **Photosafe by construction.**
    - Stutter-mode cells are forced to G = 0.
    - Ls is low-passed.
    - Each message changes at most once per 2 s.
    - Sags and waves are single dips with ramps ≥ 0.3 s.
    - Any lamp death in view dips at ≤ 2 Hz.
16. **Deterministic.** All choices are hashed from (seed, cell & 63, event counters). No `UnityEngine.Random`, no `_Time`. The same seed and inputs give the same ink timeline (synthesis P3 gate).

## 3. Placement and generation per zone and tier

Nothing is hand-placed. Every message is derived per cell from:
- **map data that does not change with revision:** zones, border edges and keys (MAP_GENERATION.md:97);
- **the lamp temperament hash:** `Hash(seed, cell, 211)`, rolled at FrontRoomsMapWorld.cs:1087 and 1127-1128. It is known even for unbuilt cells.

Routes are recomputed whenever a chunk is rebuilt. Rebuilds happen ≥ 24 m away (:612-616).

**Beacon sources, measured in a Python port of the generator (12-16 seeds; it skips modules, columns and the start area):**
- **Lamp temperaments:** 62.3% steady, 20.1% stutter, 9.5% failing, 5.0% dead, 3.1% dim.
- **Effective beacon cells** (failing, dead or dim): 17.6%.
  - The nearest beacon is a mean of 1.84 cells from any cell (p90 is 4).
  - On walked routes, a readable beacon comes every ~6 cells (18 m).
- **Thresholds are plentiful:** a cell is a mean 3.1 cells from a door or window. The nearest *new* threshold is typically 3-7 cells away.
- **Dead-end branches:** 31 per 1,000 cells, 70% of them 1-cell alcoves. That is about 50 in a 5×5-chunk area, about 15 of them with depth ≥ 2.

**Hint strength (150-cell walks, 16 seeds):**

| Walker | New zones / 100 cells | New thresholds / 100 cells |
|---|---|---|
| Random | 5.6 | 3.1 |
| On-route ink | 8.0 | 6.1 |
| Perfect knowledge | 15.1 | 12.5 |
| Continuous 3-cell route dimming (rejected: a GPS) | 14.7 | not measured |

**Per zone** (shares from FrontRoomsMap.cs:82-84, 117):

| Zone | Share of zones | Ink | Notes |
|---|---|---|---|
| Standard Level 0, 2.9 m | ~38% | Full | Long corridors. Decisions are read on end walls at T-junctions. |
| Low, 2.4 m | ~35% | Full | Short sightlines and many facing walls: the best near-read zone. Doors sit on its borders. |
| Tall hall, 5.4 m | ~10% | Full, glow band 0.8-2.0 m | Exits are windows only, so calm HERE marks windows. Lamps run ×1.6 with range 12, so neighbour spill is high: dead cells read bright, and lookdev must check the paper contrast. |
| Office, 2.9 m | ~17% of zones (13.6% of cells) | None (drywall) | Deliberate blind stretches. Routes add +1 per Office cell (SP), so the ink prefers paper. |

**Room modules.** Level Designer modules can author ModuleLamp Dead/Failing/Off per cell (FrontRoomsRoomModuleData.cs:30; applied at FrontRoomsMapWorld.cs:1130).
- Recommended: at most 1 dark "reading room" per 4 chunks (SP).
- Off cells have L = 0 for good, so they are starved and show no ink.

**Optional "border dusk" lever.** Cells beside door or window edges roll failing 25% / dead 10% instead of 10% / 5%.
- Use it only if playtest shows HERE is too rare: naturally only 14% of exit-adjacent cells are dark themselves.
- It needs visual-chat sign-off, because flicker odds are their numbers (LEVEL_MODULE_SPEC.md:76).

**Storage.**
- 64×64 toroidal arrays indexed `(x & 63) + 64·(y & 63)`, with a 192 m period (10_synthesis.md:131).
- The built window is 40×40 (56×56 at buildRadius 3, FrontRoomsLevelProfile.cs:25), so there is no aliasing.
- A chunk's texels are cleared on build and on drop.
- Persistent per-cell sets survive chunk drops, like `brokenDoors` (FrontRoomsMapWorld.cs:205). They hold: killed lamps (first-dark beat, drought breaker) and BREACH edges.

Tier effects on placement are in §6.

## 4. Triggers, charge/decay and timing

**Per frame, per built cell (CPU).** Compute L, Ls, W, C and G as in R1-R2.

On chunk build, C starts at its steady state (SP):

| Temperament | Initial C |
|---|---|
| Steady | 1.0 |
| Stutter | 1.0 |
| Failing | 0.75 |
| Dim | 0.5 |
| Dead | W (spill equilibrium) |
| Off | 0 |

Visibility thresholds (SP):
- **Beacon:** G ≥ 0.08, a green patch visible from about 20 m.
- **Legible:** G ≥ 0.25, the shape reads at 12-20 m head-on.

**What each temperament does** (from `Level()`, FrontRoomsMapWorld.cs:1184-1214):

| Temperament | Lamp level | Ink |
|---|---|---|
| Steady (:1213-1214) | 0.98 | Nothing. A full battery for its neighbours. |
| Stutter (:1188-1196) | 0.95/0.05 bursts on Perlin(t·23) | Forced G = 0, so it never flickers ink. |
| Failing (:1198-1202) | 0.25-0.70 at ~0.49 Hz, Perlin dropouts | Breathes: about 1 s readable every ~2 s. Full reads during dropouts. |
| Dead (:1203-1210) | 0, with 0.8 blinks every 8-28 s | Spill-charged steady glow. With 2 lit neighbours, C ≈ 0.39 (legible). In a dark cluster it is starved (blank). |
| Dim (:1211-1212) | 0.42 | G ≈ 0.2, legible within ~5 m |

**Fields and route.**
- The target field and the STOP pruning are rebuilt on any of:
  - `ZoneEntered`, `KeyTaken`, `DoorMoved`, `DoorBroken`, `GlassBroken` (FrontRoomsMapWorld.cs:58-64);
  - `relay.StateChanged` (FrontRoomsMapHunter.cs:141);
  - `ChunkBuilt` / `ChunkDropped`;
  - a mode switch.
- Rebuilds are rate-limited to 2 Hz (SP) and never run in a chunk-build frame (deferred one frame).
- The route is re-descended whenever the player changes cell (~0.94 s at the 3.2 m/s walk).
- Target stickiness: keep the current threshold until it is reached, or until it is ≥ 6 cells worse than the best alternative (SP).

**First-dark beat** (once per run; replaces the pre-dead cell).
- Trigger: after the start door shuts (MAP_GENERATION.md:23-24) and within 45 s.
- Cell: the 3rd-5th cell ahead on the guaranteed open walk-in line (MAP_GENERATION.md:17-19) whose target is ≤ 6 cells beyond it.
- Its message commits while it is still lit (R10b).
- When the player is 6-9 m away and facing it, the lamp dies over 1.5 s: three dips at ≤ 2 Hz, then off. It stays Dead for the run (persistent set).
- C = 1, so it blooms bright, then settles to its spill glow.

**Power sag** (calm pacing pulse).
- Frequency: every 75-120 s at T0 (SP).
- Never within 30 s of a wave (10_synthesis.md:167). Never while the player stands in an Office zone.
- Shape: breadth-first search, radius 4 cells (12 m) around the player. Lamps dip to 0.35× with attack 0.6 s, hold 4 s, release 1.5 s.
- All messages in the radius commit at dip start. It is a snapshot, never a trail.

**Chase wave** (the synthesis's corridor wave, 10_synthesis.md:143-144, 166).
- Trigger: `StateChanged(Chase)`, if the cooldown has passed (90 s at T0, SP).
- The front runs from the Relay's cell at 8 m/s (0.375 s per cell) along passable edges, with a 0.5 s delay at shut doors. It reaches 10 cells beyond the player (SP).
- Each lamp dips to 0.3× (attack 0.3 s, hold 2.5 s, release 1.2 s). Pressure messages commit as the front arrives.
- The front outruns the 5.5 m/s sprint (FrontRooms3DGame.cs:147), so about 20 m of dim, readable corridor stays ahead of a fleeing player for the 5 s of stamina (:149).
- The same front also carries the visible print reprint.

**Drought breaker.**
- Trigger: no legible sighting for 60 s, and the Relay is not in Hunt or Chase (SP).
- Action: promote one unseen Steady cell 4-8 cells ahead on the current route to Failing (persistent per-cell override). At most once per 90 s (SP).
- In the simulation, natural beacons come every ~6 cells, so this should rarely fire. It exists for Office-heavy and starved seeds.

**EAR bloom** ("it heard you"; P2).
- When `ListenPoint` takes a new value (Noise accepted, FrontRoomsMapHunter.cs:279-286), the dark cells among the source cell and its open neighbours raise their GROUND weight from 0.35 to 1.0 over a 1.5 s ramp. The bloom holds while `ListenPoint` still equals that source, then decays with τ 4 s.
- At most one bloom per 4 s, because sprint steps call `Noise` every 0.3 s (FrontRooms3DGame.cs:861-865).
- It is the only ink change allowed to start in view.
- No EAR occurs during Chase or BreakDoor, because `Noise` is ignored then (:281).

**BREACH.** On `DoorBroken` (FrontRoomsMapWorld.cs:1055-1065), the faces of that door's wall in both cells get the BREACH variant. It is permanent and committed under R10.

**Caught** freezes everything. In the title stream rooms, G = 0.

## 5. Teaching curve

No HUD tutorial by default. Every lesson is a staged beat.

**First 5 minutes:**

| Time | Beat | Lesson | Guaranteed by |
|---|---|---|---|
| 0-3 s | The stream door opens (MAP_GENERATION.md:21). Lamps rise in 0.6 s (FrontRooms3DGame.cs:118, 750). | Lit Level 0 looks normal. | The current start flow |
| ~5-45 s | **First dark:** a lamp dies in view 6-9 m ahead, and chevrons bloom on the side walls with FLOW or HERE on the end wall. The Relay is still dormant (released 3 s after the door shuts, 9-15 cells away: MAP_GENERATION.md:34; FrontRoomsMapHunter.cs:49). | Ink appears where light dies, and green points somewhere. | The first-dark beat |
| ~20-60 s | Following the chevrons ends at a door or window. The ceiling height changes and `ZONE 02` appears (FrontRooms3DGame.cs:1540). | Green leads to new ground. | Target ≤ 6 cells |
| ≤ 2 min | The first natural failing cell, breathing. | Wait for the gasp to read. | Drought breaker |
| 1-2 min | The first STOP at a junction (a 1-cell alcove at T0-T1). | Bars mean a pocket. | Branch density (~50 in range) |
| 75-120 s | The first power sag: every wall within 12 m flares for 4 s. | Sags give a snapshot of the whole neighbourhood. | Sag timer |
| First accepted sprint (P2) | EAR bloom on your own trail. | It heard you; leave quietly. | EAR |
| First chase | The wave runs past the player, and doubled chevrons point to a door. | Under pressure, the walls point to a door you can shut. | Wave (first chase is always past the cooldown) |

**First 3 runs (targets to validate):**
- **Run 1:** green = new ground; STOP = pocket. Notices the dark-only rule.
- **Run 2:** uses the chase wave and shuts doors. Learns that a starved dark cluster is blank (the physics rule) and that Office is blind.
- **Run 3:** scans the ceiling line for dead troffers. Reads end walls at 20 m and side walls within 6-8 m. Starts *choosing against* the ink (it is a lure as well as help). Recognises BREACH as a dead door.
- Lies (T4, about 8+ min in) are expected only after run 3.

**Fallback:** if fewer than 50% of first-time players follow a FLOW within 60 s, add one Flash line written by narrative on the first beacon read (Flash card, FrontRooms3DGame.cs:1546-1548). It names no symbols.

**Optional legend:** one title stream room with a dead lamp and a fixed, authored FLOW and STOP. It needs an exception to the stream-room mask (see §15).

## 6. Escalation over a run

The physics, gate and grammar never change, so what the player learns stays true. Escalation comes from scarcity, pacing, the DP08 lamps and Relay tuning, and an optional late lie.

Tiers follow the unconfirmed DP08 proposal. With no tier system, everything stays at T0.

| Tier | Route beacons | Weight (SP) | Sag every | Wave cooldown | Wave reach ahead | STOP outside waves | Forged FLOW |
|---|---|---|---|---|---|---|---|
| T0 | on-route + 1 off | 1.0 | 75-120 s | 90 s | 10 cells | all branches | none |
| T1 | on-route + 1 off | 1.0 | 90-150 s | 120 s | 10 cells | all branches | none |
| T2 | on-route | 0.9 | 120-180 s | 150 s | 8 cells | depth ≥ 2 | none |
| T3 | on-route | 0.85 | 150-210 s | 180 s | 6 cells | depth ≥ 2 | none |
| T4+ | on-route, within 15 cells of target only | 0.8 | 180-240 s | 240 s | 6 cells | depth ≥ 2 | ≤ 1 per 4 chunks, gated on metrics |

- The weight floor stays at 0.8, so the 20 m head-on read survives at every tier (a brief constraint).
- **DP08 failing lights** add more dark cells (more beacons) but fewer lit neighbours (more starved cells). The result is more hints, each harder to read. This is consistent with R2.
- **Forged FLOW** (T4+, optional):
  - It sits in a lit Steady cell at an unmarked branch mouth and points into the branch.
  - The CPU writes G = 0.8 regardless of Ls, so it glows under full light. That is the tell.
  - Only FLOW is forged. HERE, STOP and BREACH are always true, so the "stop" words stay trustworthy, and a caught lie itself reveals a pocket.
  - It never appears in pressure mode, and never twice on one route.
- **Escalation coupling** (flagged for Red):
  - Following the ink gives about 2× new thresholds per minute, so ink followers tier up faster. This is deliberate: the ink is help and lure at once.
  - DP08's "every 4 zones" counts zone ids, and about 45% of walkable zone crossings are invisible same-height crossings, so zones tick about 3.6 per minute even for a random walker.
  - Suggestion (SP): count tiers by new thresholds, 6 per tier or 2.5 min, whichever comes first.
- **Never escalates:** truth before T4, BREACH permanence, the dark-only rule, R13.

## 7. Interaction with the Relay and the escape verbs

| Fact (code) | Ink behaviour |
|---|---|
| Sight is a 12 m ray with no light term (FrontRoomsMapHunter.cs:926-931) | Darkness, sags and waves change only what the player knows. The wave also darkens the player's own view of the Relay, which is a real cost. The dark body (#2B2928) with its pale head (D8D4C8) (FrontRooms3DGame.cs:255) silhouettes against glowing paper: a free scare, not a stealth rule. |
| Wander never crosses shut doors (FrontRoomsMapHunter.cs:426, 460-463) | Calm routes ignore the Relay, so a shut door the ink led you through also shields you from a wanderer. That is emergent, not promised. |
| Hunt and Chase plan through doors and break them in 2.5 s + 0.25 s (FrontRoomsHunter.cs:21; MAP_GENERATION.md:36) | Pressure routes end at a door away from the Relay (HERE, doubled). After the player passes and shuts it, the next commit points onward. |
| LoseTrack follows through a door the player just used (FrontRoomsMapHunter.cs:294-302) | Pressure costs prefer a door followed by a bend (the +2 sight-line cost), so the player is out of its line when it arrives. |
| Broken doors stay open for good (FrontRoomsMapWorld.cs:1055-1065) | BREACH variant. Pressure routes skip it; calm routes may still pass through it. Over a run the ink becomes a map of dead doors, which matters more as DP08 shortens break time. |
| Unbroken glass blocks its path and sight (FrontRoomsMapHunter.cs:462) | Calm routes may use windows (+4 cost). Pressure routes never do: the 1 s hold costs 4.2 m, and broken glass lets it follow. |
| Sprint: 5.5 vs 4.2 m/s, 5 s stamina, heard at 26 × 1.4 = 36 m (FrontRooms3DGame.cs:147-149, 865) | The wave front at 8 m/s keeps the readable corridor ahead of a sprinting player. EAR (P2) turns a sprint into a visible confession. |
| Shut-door noise 14 × 1.4 = 19.6 m (FrontRooms3DGame.cs:785-790) | It can trigger EAR at the door (P2). |
| Dead ends | STOP marks branch mouths; catches inside branches are a key metric. |
| Leash and relay (FrontRoomsMapHunter.cs:182-187, 390-418) | Unaffected. A future OMEN wave is deferred (§14). |
| Keys glow yellow already (FrontRoomsMapWorld.cs:1730-1745, 1787) | With `doorsNeedKeys` off, a key is just another calm target. With it on, the key comes first. |
| The HUD shows distance and HUNT state (FrontRooms3DGame.cs:1539-1544) | Retired per R14; otherwise the ink adds no tension. |
| Tall halls have no speed term | The ink never treats tall halls as safe. |

## 8. Interaction with the moving visible print

1. **Opposite masking phases.**
   - The visible print changes in the dark: it slips inside its own cell's lamp-dark window (10_synthesis.md:139-142), because ink colour vanishes when unlit.
   - Phosphor messages change in the light (R10b), because the glow is swamped there.
   - A failing lamp gives both systems a legal window every couple of seconds, in opposite phases. A dead cell has no lit phase, so its message changes only when unseen.
2. **Message vs substance** (R11). The shape is procedural and constant across print keyframes, so jumps and crawls never move a message.
   - The B substance belongs to each print slice and may change between a failing lamp's gasps. Narrative may use this, for example writing that rewrites itself up close.
   - Message cells take no lamp-dropout strip slips, so the paper never slides under a readable mark.
3. **Discrete jumps** (the default) use the same unseen set as message commits: one visibility service serves both.
4. **Slow crawl** at scripted beats only uses cells showing GROUND. Moving ink never carries a message.
5. **Chase wave.** One BFS front at 8 m/s carries three things in lockstep: the visible reprint, the lamp dip and the pressure commit.
   - The 192 m rebase caveat (10_synthesis.md:144) does not apply, because the ink is off in the stream rooms.
6. **Relay wake.** Keep the synthesis's visible wake reprint (10_synthesis.md:145). It gives the two-layer deck line "the print shows where it walked; the ink shows where to go". Pressure routes add +2 on wake cells, so the two rarely overlap.
7. **Subliminal drift** (≤ 1-2 mm/s, ±0.3% scale) moves the B substance too. That is imperceptible and fine; the shape mask is world-fixed.
8. **Per-roll phase** `strip & 3` (10_synthesis.md:80, 193): every FLOW wall looks the same in every on-route cell. The deliberate beat is that this cell points, not that it looks unique.

## 9. Readability and accessibility

**Shapes** (procedural, world space, in a glow band 0.8-2.0 m above the floor; player eye 1.62 m, LEVEL_MODULE_SPEC.md:133):

| Shape | Geometry (SP) |
|---|---|
| FLOW | Open chevrons 400 mm tall, stroke ≥ 100 mm, pitch 375 mm (8 per 3 m wall) |
| FLOW, pressure | The same chevron, doubled: 2 × 100 mm strokes with a 60 mm gap |
| HERE | 100 × 900 mm vertical bars on the ~1 m of wall beside a door, ~0.8 m beside a window (LEVEL_MODULE_SPEC.md:48-49) |
| BREACH | HERE plus a 100 mm diagonal bar |
| STOP | 2 horizontal bars, 600 × 120 mm, per 0.75 m roll |
| GROUND | The B substance alone at weight 0.35 |

- **Direction** comes from the world axis (z when |n.x| > 0.5, else x), never the mirrored PlanarFrame u (FrontRoomsSurface.shader:157-161). Arrows therefore point the same world way from both sides of a corridor.
- **B substance rule:** the mean B within any 100 mm square must be ≥ 0.6 inside strokes, so strokes read as solid at 20 m. Fine detail is for reading under 2 m.
- **Print chevrons vs ink chevrons (updated 2026-10-03, after Red chose the WP03 "Hard edge" print and dropped the ghost emboss).** Three cues keep them apart:
  - **Orientation:** the print's chevrons point UP the wall (55° mitred bands, plus the motif arrows), while FLOW chevrons point ALONG the wall toward the route.
  - **Medium:** the print is albedo seen in light; the ink is emission seen only in the dark.
  - **Arm angle:** the narrative chat (30_narrative_phosphor.md §10) asks for FLOW arms of about 30–35°, kept isolated inside the glow band, so that in failing cells, where both show, no ink chevron is ever drawn at the print's 55°.

  The final angle is the visual chat's call.

**Distances** (vertical FOV 76°, FrontRooms3DGame.cs:227, gives ≈ 691/d px per metre at 1080p):
- A 0.40 m chevron is ~14 px at 20 m, with strokes ~3.5 px.
- Side walls read only within 6-8 m, because foreshortening at 20 m down a 3 m corridor is ~0.075. **The decision read is the end wall at a T-junction or turn**; side walls confirm it up close.
- Fog is ExponentialSquared at 0.014 (FrontRoomsLook.cs:19, 32), so ~92.5% of the glow survives at 20 m.

**Luminance, not hue.**
- Glyph-to-paper ratio ≥ 1.3 in a full-charge dead cell with 2 lit neighbours; ≥ 1.15 in a failing cell at Ls 0.3 (SP).
- Emission is capped at ~12% of a lit wall's luminance, so the ink stays faint.
- Colour is about 530 nm (ZnS:Cu). Meaning is carried by shape and luminance, so it is safe for protan and deutan players.
- Screen budget: green covers ≤ 3% of pixels on average and ≤ 8% at p95, so Level 0 stays yellow.

**Photosensitivity.**
- Gate: R15, plus the P2 gate (≤ 3 flashes/s; no reversal above 3 Hz over > 25% of the screen), measured with glow, print, sags, waves and fixtures combined (10_synthesis.md:228).
- The existing stutter mode (FrontRoomsMapWorld.cs:1196) can exceed 3 Hz in bursts on its own. Audit it regardless of the ink.

**Settings:**

| Setting | Effect |
|---|---|
| Reduce wall motion (required, 10_synthesis.md:197-200) | No travelling wave; a static 4 s sag of radius 4 cells at Chase start. Ls τ 1.0 s. Failing cells show a 3 s running mean (a steady, faint read). No crawl. The first-dark beat becomes a single 1.5 s fade. No EAR ramp shorter than 1.5 s. |
| Ink assist | Intensity ×1.5, GROUND off, strokes +30% |
| Threat readout (Off by default) | Off / State / State + distance. Today's HUD moves here. |
| Deaf and hard-of-hearing | EAR and the wave are visual first; sound only reinforces them. |

The ink is never the only signal: doors and windows stay visible as geometry.

## 10. Failure modes and exploits

### 10.1 Judge findings on the base design and how they are resolved

| # | Finding (lens) | Resolution |
|---|---|---|
| 1 | Too reliably helpful; reads as UI, not dread (play) | **Fixed in part.** Calm ink ignores the Relay (it can lure you into it). Following it speeds escalation. Hints are on-route only and about 2× random, not a GPS. Starved cells go blank. Optional physical lies at T4+. HUD distance retired. The residual risk is accepted and measured with the "help, lure or noise" survey. |
| 2 | The HUD distance undercuts tension; calm-to-pressure leaks the Relay (play) | **Fixed:** R14 (distance behind an assist, state text only for CHASE and BREAKING DOOR); R6 pressure is Chase-only by default. |
| 3 | The wave may push chase escape too high (play) | **Fixed:** wave cooldown 90-240 s and reach 10→6 cells by tier; the wave dims the player's view of the Relay; DP08 shortens door breaks. Cap metric: escape ≤ 80% at T0, ≤ 60% at T3+. |
| 4 | Heavy tuning; the invisible mode switch makes one chevron mean two things (play) | **Fixed:** the pressure variant is drawn doubled; pressure commits only at the wave front or unseen. Build order in slices (§11.4). |
| 5 | Office blind zones and dark clusters read as bugs (play) | **Fixed:** the fresh/starved physics (R2) makes blank dark a rule, and narrative explains it. Office stays blind and is accepted as deliberate (+1 route cost; measured). |
| 6 | Largest map-chat surface; LampDip affects lighting and sound (feasibility) | **Accepted and sliced.** LampDip is one multiplier on `f.level`. The sound director already follows `light.intensity` (FrontRoomsSoundDirector.cs:305-310), so the hum dips for free. |
| 7 | `zonesVisited` is private; new events needed (feasibility) | **Accepted:** a read-only `IReadOnlyCollection` plus `ZoneEntered`, owned by the map chat (it owns FrontRooms3DGame.cs, LEVEL_MODULE_SPEC.md §10). |
| 8 | Dijkstra over `PassageBetween` may exceed 0.4 ms (feasibility) | **Fixed:** cached per-chunk adjacency bytes and flat 4096 arrays with a bucket queue; rebuilds deferred out of chunk-build frames and time-sliced if over 0.5 ms. |
| 9 | Per-face shader logic plus 16 glyph slices (feasibility) | **Fixed:** procedural shapes; zero extra slices and no second fetch. |
| 10 | Depends on the unbuilt visibility service (WG2); hard to test (feasibility) | **Mitigated:** slices S1-S3 use a conservative frustum-only test (an occluded cell counts as seen, so the only risk is fewer commits). Commits through the lit path need no visibility at all. Debug overlay and 100-seed audits. |
| 11 | R10 froze the ink against the moving print, weakening the sandwich (fit) | **Fixed:** R11. The substance moves with the print; the message stays fixed. |
| 12 | Omniscient ink softens the dread (fit) | **Accepted as a narrative slot.** It knows the building, never the monster, and it may lie late. Narrative frames it as ambiguous help. |
| 13 | Escalation coupling (fit) | **Accepted and measured:** minutes per tier with ink on vs off; tier counting by thresholds proposed. |
| 14 | Too many numbers for a presentation (fit) | **Accepted:** the deck uses one image (a mute lit corridor beside a dead troffer with chevrons) plus the 3.1 / 6.1 / 12.5 table. |
| 15 | Chevrons echo the removed relief (fit) | **Accepted as deliberate:** different proportions, emission only, and a narrative hook. |

### 10.2 Runtime failure modes

| Failure | Mitigation |
|---|---|
| Beacon ping-pong (every dark cell points) | R7, on-route only (2.4 → 8.0 new zones / 100 cells) |
| GPS creep (continuous route dimming reached 14.7 vs a perfect 15.1) | Sags are snapshots; waves are chase-only with a cooldown; the on/off ratio is tracked |
| Visible message swaps | R10; dead cells commit only unseen; the ink never reuses the print's flicker-mask rule |
| Flow flip-flop | Hash tie-break on (cell & 63), 6-cell stickiness, ≤ 1 commit per 2 s |
| Glow beyond 16 m, or glow through the start door | Use logical `f.level`; ignore the hold and fade (FrontRoomsMapWorld.cs:1171-1174) |
| Invisible same-height borders (~45%) tick ZONE without a threshold | The ink targets thresholds only; tier counting should follow |
| Lure into noise (calm route through glass, heard at 56 m) | +4 window cost; otherwise the intended risk |
| False refuge (dark or tall = safe) | R13; the first contact in a glowing corridor shows it sees you |
| Edge of the world | Built-boundary cells are fallback targets; failed chunks (FrontRoomsMapWorld.cs:672-683) count as walls |
| Interior shift after 30 s away (FrontRoomsLevelProfile.cs:29) | Targets do not change with revision; new routes commit ≥ 24 m away, unseen |
| Aliasing on stream, Office and start walls; jamb faces on cell lines | Ink-eligible mask; clear texels on build and drop; jamb normal bias |
| EAR spam or noise sonar (tapping sprint to probe) | One bloom per 4 s. From T3 the bloom is delayed 2-4 s if telemetry shows sprints under 0.5 s |
| Lure poisoning (players distrust all ink) | Lures only forge FLOW and only at T4+; cut them if the true-FLOW follow rate after the first lure falls below 50% |
| Glyph clipping on 0.6 m columns or between trims | Accepted; or fade where a face is narrower than 0.75 m (visual's call) |
| Starved late game (DP08 darkens the map) | Drought breaker and sags keep a floor |

## 11. Implementation data flow

### 11.1 Pipeline

**Step 1: Lamp API (map chat).**
- Add read-only `LampLevel(cell)` (logical `f.level`) and `LampMode(cell)`, a pure seed hash that also works for unbuilt cells.
- Add a `FixtureChanged` event. The synthesis already requests this (10_synthesis.md:175-178).
- Add `LampDip(cell, depth, attack, hold, release, delay)`, a multiplier applied to `f.level` inside TickFixtures (FrontRoomsMapWorld.cs:1160-1181).
- Add `KillLamp(cell)` / `PromoteLamp(cell, mode)`, with persistent per-cell overrides applied at `BuildFixture` (:1130).

**Step 2: `FrontRoomsWayfinding` (map chat).** A new plain-C# class in `Assets/Scripts/FrontRoomsMap/`, ticked right after TickFixtures (:569). Each frame:
- (a) L, Ls, W, C, G per built cell (≤ 1,600 cells, ~0.05 ms);
- (b) event-driven fields at ≤ 2 Hz: the target field (bucket Dijkstra, costs 0-6), the Relay BFS (pressure only), and leaf pruning for STOP;
- (c) route descent and message assignment;
- (d) the commit gate (R10);
- (e) sag, wave, first-dark, drought and EAR timers;
- (f) packing into `Color32[4096]`.

**Step 3: Visibility (shared).** A BFS over see-through edges from the camera cell plus `TestPlanesAABB` (10_synthesis.md:135-138). It produces one set, used by both print jumps and ink commits.
- Owner: whoever lands WG2 (VISUAL_CHAT_TASKS.md:70); the map chat consumes it.
- Until then, use the frustum-only fallback.

**Step 4: Pack and upload (visual chat driver).** One 64×64 RGBA8 texture, point filter, Repeat wrap, `SetPixelData` + `Apply(false)`, 16 KB per frame. Globals: `_FR_CellState` and `_FR_Ink` (intensity, reduceMotion, assist).

| Channel | Content | Owner |
|---|---|---|
| R | Print state (frame offset or transition) | Visual |
| G | Ink glow G (weight, EAR, forge already applied) × 255 | Map |
| B | Bits 0-1 direction N/E/S/W; bits 2-3 message GROUND/FLOW/HERE/STOP; bit 4 pressure; bit 5 BREACH; bit 6 forged; bit 7 ink-eligible | Map |
| A | Ls × 255, also the print's flicker mask | Map |

The final layout is agreed with the visual chat.

**Step 5: Shader (visual chat).** In FrontRoomsSurface ForwardLit under `_FR_PRINT`: one point load, about 15 ALU, no extra texture fetch. B comes from the existing print fetch.

```hlsl
int2  c    = (int2)floor((positionWS.xz + normalWS.xz * 0.5) / 3.0) & 63;
half4 s    = LOAD_TEXTURE2D(_FR_CellState, c);
uint  code = (uint)(s.b * 255.5);
float along = abs(normalWS.x) > 0.5 ? positionWS.z : positionWS.x;   // world axis, never mirrored u
float sgn   = FaceSign(code & 3, normalWS);       // +1/-1 along this face; 0 means the route crosses it -> GROUND
float m     = InkShape((code >> 2) & 3, code >> 4, along * sgn, heightAboveFloor);  // includes the 0.8-2.0 m band
emission   += _FR_InkColor * s.g * m * print.b * _FR_Ink.x * paperCavity;          // fog applied after
```

- An unset global means G = 0, so edit mode, lookdev and the Level Designer fall back to no ink.
- The ink never writes albedo, normal, smoothness or cavity.

**Step 6: Events in:**
- `DoorMoved`, `DoorBroken`, `GlassBroken`, `KeyTaken` (FrontRoomsMapWorld.cs:58-64);
- `relay.StateChanged` and `ListenPoint` (FrontRoomsMapHunter.cs:114-141);
- new: `ZoneEntered`, the visited set, `ChunkBuilt` / `ChunkDropped`, `Tier`.

The run is reached through `MapRunStarted` (FrontRooms3DGame.cs:608).

**Events out:** `LampDipped(cell)`, `WaveStarted(origin)`, `EarBloom(pos)`, `InkLegible(cell)` for telemetry, and `Event("ink", …)` rows (FrontRooms3DGame.cs:1578).

**Budget (SP):**
- CPU ≤ 0.4 ms on average and ≤ 1.0 ms on rebuild frames.
- GPU ≤ +0.2 ms.
- 16 KB per frame upload; 16 KB of memory.
- Measured against the synthesis perf gate (58.7 fps, p99 19.4 ms; seeds 2554 and 20388 plus a Level 0 flythrough; 10_synthesis.md:230).

### 11.2 Owner asks

| Owner | Must build |
|---|---|
| **Map chat (关卡设计)** | Lamp API and LampDip, KillLamp/PromoteLamp and persistence. `FrontRoomsWayfinding` (fields, pruning, route, messages, commit gate, timers, EAR, BREACH, forged FLOW, packing). Expose `zonesVisited` and `ZoneEntered`. `ChunkBuilt`/`ChunkDropped` events from Stream/Drop (FrontRoomsMapWorld.cs:594-650). A tier index. The HUD change (FrontRooms3DGame.cs:1539-1544) and the threat-readout assist. Freeze on Caught. A debug map overlay (route, messages, branches). Tests: a 100-seed truth audit, 0 commits while seen, determinism, and an ink-follower autopilot policy in FrontRoomsMainScenePlaytest. Update LEVEL_MODULE_SPEC §4 and MAP_GENERATION. |
| **Visual chat (游戏视觉)** | State upload driver. Shader emission with `InkShape`/`FaceSign`, the height band, cavity mask and ink-eligible mask (stream, Office, start). The keyword must survive RenderSetup regeneration (10_synthesis.md:97). The B substance channel in the pack script and seam validator. Ink colour and contrast against the targets. Lookdev captures at 1/6/12/20 m head-on and 6 m grazing, plus tall-hall spill. The combined flash audit. Reduce-motion and ink-assist paths. No strip slips on message cells. Sign-off on lamp overrides (first-dark, drought breaker, optional border dusk; LEVEL_MODULE_SPEC.md:76). The visibility service if WG2 delivers it. |
| **Sound chat (声音设计)** | The ballast sag follows automatically (the hum reads `light.intensity`, FrontRoomsSoundDirector.cs:305-310); tune its pitch dip. A wave stinger aligned to `WaveStarted`. A ballast-death pop for the first-dark beat and the drought breaker. A quiet positional EAR cue, played only when a bloom cell is dark and in view. Never sound an unseen commit. The ink itself is silent; under AUDIO_CONTRACT.md the print never touches audio files. Update the hooks table. |
| **Narrative chat** | The slots in §12 |

### 11.3 Testing hooks

`inkEnabled` editor toggle for A/B testing; tier pinning in tests; `Verify 100 seeds` extended to report beacon spacing, branch counts and target reachability.

### 11.4 Build order (weekly slices)

| Slice | Content | Needs |
|---|---|---|
| S1 | Lamp API; G gate on natural lamps; GROUND only; masks | Map + visual; frustum-only visibility |
| S2 | Calm target field, route, FLOW/HERE, commit gate, debug overlay | Map |
| S3 | STOP via leaf pruning; truth audit | Map |
| S4 | First-dark beat; HUD change | Map, visual sign-off, sound pop |
| S5 | LampDip, chase wave, pressure variant, BREACH | Map, visual (shared wave), sound |
| S6 | Power sags, drought breaker, tier table | Map |
| S7 | WG2 visibility swap-in; EAR (P2) | Visual/WG2, map, sound |
| S8 | Forged FLOW (optional, gated on metrics) | Map, visual lookdev |

## 12. Narrative slots

| Slot | What the mechanic needs |
|---|---|
| What the underprint is and who printed it | Period-plausible ZnS:Cu (1990 era lock; strontium aluminate is too late). Only on wallpaper, never on Office drywall. |
| Why it knows the way to NEW thresholds and never leads back | Knowledge of the building's layout that survives interior shifts. Candidates: a previous wanderer's trail, the building's memory, a printing defect. |
| Why it needs light to charge, and why dark clusters are blank | A rule players can repeat, for example "the paper only remembers what it was shown". |
| Why it reacts to the Relay's chase (wave, doors away from it) | Do the walls fear it, serve it or record it? It must **not** imply the Relay can't see in the dark. |
| Help or herding | Following it speeds escalation; the fiction can frame it as both. |
| What the B substance shows up close (under 2 m) | Any content, including variation per print slice. Stroke-fill rule: mean B ≥ 0.6 inside strokes. |
| The look and naming of FLOW, HERE, STOP, BREACH and the pressure variant | The families must stay go = open, threshold = frame, stop = closed. Any link to the old relief chevrons. |
| What the power sags are | Building electrics, the Relay, or something else. |
| The first-dark beat | Flavour for the ballast pop, plus an optional one-line Flash if playtest needs it. |
| EAR | Is the paper listening, or answering? |
| Forged FLOW (if enabled) | Who forges it, and why a forgery cannot hide under light. Only "go" marks are forged. |
| Optional anchor | The Gilman sub-pattern (10_synthesis.md:238-240). Real ZnS:Cu egress marking (FAA floor-path rules after 1983) as research with original photos and sources. |

## 13. Playtest plan and metrics

**Phases:**
1. **Lookdev stills:** direction call at 6/12/20 m head-on and 6 m grazing, with and without assist, plus a colour-blind filter pass.
2. **Automated audits:** 100 seeds and autopilot.
3. **Class playtest:** an A/B test with ink on and off on the same seeds, with the HUD distance off in both arms.
4. **3-run sessions:** 3 runs per player for the teaching curve.

| Metric | Target (SP) | If missed |
|---|---|---|
| Hint strength: new thresholds per minute, ink on / off | 1.6-2.2× (sim: 2.0) | Above 2.5 it is a GPS: cut sags or T0 adjacency. Below 1.3: raise the weight or enable border dusk. |
| Follow rate: FLOW within 8 m in view ≥ 0.5 s, then the next 3 cells descend the field | 50-75% | Revisit the first-dark beat or the shapes |
| Teaching: first beacon in view → first follow | < 20 s for ≥ 70% of first-time players; ≥ 70% cross their first ink-led threshold within 60 s | Add the Flash line |
| Beacon spacing on routes actually walked | One readable beacon every 5-8 cells (sim 6.2); legible sightings every 20-40 s median | Drought breaker interval; border dusk |
| Chase escape rate, wave vs no wave | Rises, but ≤ 80% at T0 and ≤ 60% at T3+ | Shorten wave reach; lengthen cooldown |
| Doors shut per chase | Rises with the wave | Pressure HERE readability |
| Catches inside leaf-pruned branches | ≥ 50% lower with ink on | STOP depth or weight |
| Office time per run; Office-heavy seeds | Track | +1 → +2 route cost |
| Minutes per tier, ink on vs off | ≤ 1.5× faster with ink | Tier counting by thresholds |
| Comprehension, after run 1 with no text: "what does the green mean?" | ≥ 70% say "way on / new area / door"; ≥ 50% name the dead end; < 15% say "dark hides me" | First-contact beat; fiction |
| Survey: help, lure or noise? | A mix of help and lure; noise < 25% | Weight, spacing |
| Forged FLOW (if on) | 30-50% followed on first exposure, < 20% by the third; true FLOW still followed ≥ 50% afterwards | Cut forgeries |
| EAR (P2) | ≥ 60% leave the bloom cells within 8 s without sprinting by the second exposure | Cue clarity |
| Truth audit (automated) | Every route ends at a valid target; 0 FLOW into branches; 0 pressure routes through windows or BREACH | Bug |
| Change-blindness audit | 0 commits while seen, except at sag, wave or EAR fronts; < 1 flip per cell per 2 s | Bug |
| Flash audit (normal and reduce-motion) | ≤ 3 flashes/s; no > 3 Hz reversal over > 25% of the screen | Lengthen ramps; fix stutter |
| Green screen coverage | Mean ≤ 3%, p95 ≤ 8% | Raise thresholds |
| Perf | CPU ≤ 0.4 ms average, ≤ 1.0 ms on rebuilds; GPU ≤ +0.2 ms; within the synthesis gate | Time-slice the fields |

## 14. Alternatives considered

| Design | Play | Feasibility | Fit | Total |
|---|---|---|---|---|
| **Afterglow Blazes (wayfinding), chosen** | 8 | 7 | 8 | **23** |
| Afterglow Wake (threat_intel) | 7 | 7.5 | 6 | 20.5 |
| Afterglow Ledger (light_economy) | 6 | 6 | 7 | 19 |
| Afterglow Grammar (anomaly_literacy) | 6.5 | 5 | 6.5 | 18 |

**Afterglow Wake (threat_intel), 20.5.** The ink as a ledger of the Relay: wakes that fade with age, knots where it listened, EAR blooms on accepted noise, permanent breaches, and an OMEN wave before each arrival, all read at the cost of standing in the dark.
- Strengths: the best dread, the cheapest core (it polls public hunter API), and the key catch that the HUD distance makes any intel ink pointless.
- Not chosen because: it adds nothing during a chase; its five mark kinds read at range only as "how much"; it fixes the fiction (the Relay writes the ink); and it deletes the synthesis's visible wake reprint.
- Grafted: HUD retirement, BREACH, EAR (P2), the silhouette beat.
- Rejected:
  - **OMEN:** it needs Arrive split into a delayed commit plus a new `HunterState.Arriving`, which touches release timing, sound and AUDIO_CONTRACT. Kept as a possible P3.
  - **The adaptation cost:** it taxes exactly the 20 m end-wall read that carries this design's decisions. Reading cost comes instead from scarcity and failing-lamp breathing.

**Afterglow Ledger (light_economy), 19.** Light as the price of a hint: hyperbolic charge physics, WAY and SHUT signs coded by which wallpaper roll glows, a pull-the-tube verb to buy darkness, a Relay that wanders toward dark, and lamps that only degrade with tier.
- Strengths: the truest phosphor physics, narrative freedom over glyph shape, and a strong first-dark reveal.
- Not chosen because: reads are scarce and fiddly (0.1-0.5 s gasps); there is little in a chase; and it needs a new verb (the lens collider is removed, FrontRoomsMapWorld.cs:~1094), hunter weighting, noise multipliers and runtime changes to flicker odds the visual chat owns.
- Grafted: hyperbolic decay and the fresh/starved rule, constant physics across tiers, meaning in a world-space mask with the substance owned by narrative, the first-dark beat, the drought breaker.
- Pull-the-tube stays a stretch goal, used only if playtests show beacon drought.

**Afterglow Grammar (anomaly_literacy), 18.** An 8-word fixed language at branch mouths (THROUGH, BLIND, DOOR, DOOR·BLIND, GLASS, WAKE, HEART, LURE), learned across runs with no save data, with forgeries that glow under lit lamps.
- Strengths: the best fork semantics and the most elegant lie tell.
- Not chosen because:
  - fluency takes 6-10 runs, which student playtests cannot validate;
  - forced reader lamps make troffers the real tell;
  - its "every chunk is a spanning tree" premise is false (non-tree edges are Open or Arch at 18-70%, FrontRoomsMap.cs:94-96), so its dead-end words could lie;
  - tier-dependent planning breaks determinism, and it consumes the whole 32-slice print sheet.
- Grafted: silhouette families, the physical lie tell (T4+, forging FLOW only), and no strip slips under messages.
- DOOR·BLIND ("a door into a closed pocket", a refuge from a wanderer) is held as an optional POCKET variant (§15).

## 15. Open questions for Red

1. **ANSWERED (Red, 2026-10-03): yes.** The RELAY distance and state text are off by default and become an assist option; the map chat lands it after Level Designer P4. Original question: **HUD:** may the map chat retire `RELAY nn M` and the HUNT/SEARCH state text (FrontRooms3DGame.cs:1539-1544) and move them behind an assist? The design depends on it.
2. **Tier counting:** count by new thresholds (6 per tier or 2.5 min), or by DP08's zone ids? Zone ids tick about 3.6 per minute even for a random walker.
3. **Pressure trigger:** Chase only (recommended), or also Hunt and Search within 8 cells (stronger, but it leaks the Relay)?
4. **ANSWERED (Red, 2026-10-03): forged FLOW is ON from T4.** Original question: **Lies:** enable forged FLOW at T4+, or keep the ink truthful forever?
5. **Office blind zones (13.6% of cells):** keep them as deliberate hint-free stretches?
6. **First-dark beat:** use the in-view lamp death (recommended) or the original pre-dead cell? Either one needs visual-chat sign-off on the lamp override.
7. **Lamp overrides:** may the drought breaker and the optional border dusk change lamp temperaments at runtime (LEVEL_MODULE_SPEC.md:76)?
8. **EAR:** in the core at S7, or cut? Should the OMEN arrival wave be scheduled at all (it needs a hunter change)?
9. **POCKET variant** (DOOR·BLIND hide-hole) as a calm secondary message: worth the extra shape?
10. **Legend room** in the title stream (a fixed FLOW and STOP under a dead lamp): it needs an exception to the stream-room mask. Yes or no?
11. **Escalation coupling:** is it acceptable that following the ink makes a run escalate faster?
12. **Deck framing:** use "the print shows where it walked; the ink shows where to go" as the one-line explanation of the sandwich?