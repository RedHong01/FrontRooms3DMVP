# Afterglow Blazes: level design proposal for the phosphorescent wallpaper print

**Revision 2 (2026-10-03).** The map chat checked 89 claims in §2, §4 and §11 against the code after its P4 changes: 4 wrong, 37 partly right, 30 outdated, 18 correct. This revision fixes all 71 that were not correct:
- Every file:line now points at the post-P4 code. Anything that is not in the code is marked **Proposed:**.
- The four wrong claims: `ZoneEntered` is a new event, not an existing one (§4). The first-dark cell is picked by path distance, because the code guarantees no straight walk-in line (§4). BREACH and the ink shader path are proposals, not code (§4, §11.1 Step 5).
- HUD: the Relay state and distance are now hidden by default behind one assist toggle. Red decided this and the map chat has landed it (R14, §9, §15 Q1). Whether CHASE and BREAKING DOOR should always show is still open.
- Tiers: T0–T4+ in this doc mean **run tiers** 1–5 (`FrontRooms3DGame.TierChanged`), not the per-chunk generation tier. §6 sets out the convention, and each rule says which tier it reads.
- Lamps: the old LampDip/KillLamp/PromoteLamp list is replaced by the shared lamp-override layer. Its interface is still being agreed (§11.1 Step 1, §11.2).
- Ink substance: it no longer lives in print B. It comes from `_FR_InkType` and `_FR_InkSubstance` (spec v1, the visual chat's Q2), and it follows the run tier, not print slices (R11, §8, §9, §11.1 Steps 4–5, §12).
- BREACH: doors become single-acting next, and the map chat is adding a break-direction event beside `DoorBroken` (§4).
- Changed SP values, each marked inline: the R6 arch bonus, the power-sag spacing and the border-dusk odds. Corrected derived figures: the chase-wave lead and the Dim-cell G (§4), and when the late lies arrive (§5). Also new: §15 Q13 (visibility).

Status: proposal only. First written 2026-10-02 and revised 2026-10-03. None of the ink is implemented. Some things it builds on have landed: the P4 run tiers, the Relay-readout assist and the hooks listed as existing in §11.1 Step 6. Written by the wallpaper-print chat (a judge-panel workflow: 4 directions, 3 judges per direction, all 4 scored). Most of the build would fall to the map chat (关卡设计), plus some work by the visual chat; see §11.2. Paths are relative to `Frontrooms3D/`. Every gameplay number is marked **SP** (a starting point for playtest). Code facts are given as file:line, as of the post-P4 code of 2026-10-03.

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

**The ink knows the building. It does not know the monster.** In calm play it ignores the Relay, so it can lead you straight into a wandering one. Following it also roughly doubles your rate of new thresholds, and so of new zones, which speeds up run-tier escalation (the code counts new zones).

Decisions it adds:

| When | Decision | Cost of each answer |
|---|---|---|
| Calm | Follow the green to new ground, or go my own way? | Following means faster progress, faster escalation and a blind walk past the Relay. Ignoring it means slower progress and more dead ends. |
| Chase | Which door does the wave point at, and do I spend time reading the end wall? | Reading costs metres at 4.2 m/s (run tier 1; about 5.4 m/s at tier 5). A shut door buys 2.5 s + 0.25 s at run tier 1; the break shortens to about 1.3 s at tier 5. |
| Junction | Is that branch a pocket (STOP)? | Entering a pocket during a hunt is the cheapest death in the maze. |
| T4+ (run tier 5; on, §15 Q4) | Is this mark real? It is glowing under a lit lamp. | A forged FLOW leads into a dead end. |

## 2. Rules

1. **Gate.** `G = C × smoothstep(0.55, 0.15, Ls) × weight` (SP).
   - `Ls` is the cell's own lamp level, low-passed with τ 0.35 s (SP). The lamp level is the logical `Fixture.level`: a field at FrontRoomsMapWorld.cs:111, in the private class `Fixture` (:98). Every frame it is recomputed as `f.level = Level(f)`, at :1277 in the desktop `TickFixtures` and at :1308 in the WebGL `TickFixturesNear`. `Level()` is at :1384 and switches on `f.mode`. The ink reads it through `LampLevel(cell)` from the lamp-override layer (§11.1 Step 1), so active sags and dips count.
   - It must never be read from `light.enabled`, `light.intensity` or the lens emission. Those are cut by the distance fade and the start-area hold: desktop :1280-1284, WebGL :1309-1319, and the lens factor `f.level × held` at :1288 and :1316.
   - lightRadius is 16 m (FrontRoomsLevelProfile.cs:37). The fade starts at 13 m, and from 16 m the Light is off, so reading the Light would make every cell beyond 16 m glow. On WebGL an off lamp also keeps a stale `light.intensity` (:1319), and far chunks force the fade to 0 (:1310-1311).
   - A lit cell (Ls ≥ 0.55) shows nothing.
2. **Charge physics. This never changes with tier** (run tier or generation tier).
   - Wall light (Proposed, SP): `W = min(1, L + 0.2 × Σ L of the 4 neighbours)`. The code has no per-cell light value and no neighbour sum.
   - The code fact behind it: a lamp without shadows lights straight through walls (comment at FrontRoomsMapWorld.cs:1229-1236). Shadows are None at build (:1207). About 1 lamp in 3 gets `castsShadow` (:1215), and those cast soft shadows only within shadowRadius 9 m (:1285 desktop, :1320 WebGL; FrontRoomsLevelProfile.cs:39).
   - Real lamps reach further than the 4 neighbours: a 162° spot with a range of 10 m, or 12 m under ceilings above 4 m (:1202-1206). The 4-neighbour sum is a deliberate simplification. Building it needs the cell→fixture index of §11.1 Step 1.
   - When W > C, C rises toward W with τ 2 s.
   - Otherwise C decays hyperbolically, `C(t) = C₀ / (1 + C₀·t / 8 s)` (SP). This is the second-order recombination shape of real ZnS:Cu afterglow.
   - **Fresh** dark (a lamp that just died) is bright. **Starved** dark (a dead cell among dead neighbours) is faint or blank. Both follow from the physics, so neither looks like a bug.
3. **Carriers.** Only wallpaper carries ink: Level 0 walls and wallpapered columns (LEVEL_MODULE_SPEC.md:57-59). No ink appears on:
   - Office drywall (:58);
   - doors, trim, glass, floors or ceilings;
   - the start area. The code is at FrontRoomsMapWorld.cs:456-484: `SetStartArea` :467, `InStartArea` :483; floor and ceiling are skipped at :813-814; the boundary walls come from `StartAreaEdge` :919-935.
     - Its west, east and south boundary walls carry the outside zone's wallpaper (:932-933). So the mask must also leave out every edge that touches the start area (`InStartArea` on either side), not only the cells inside it.
     - `ClearStartArea` (:479, called from FrontRooms3DGame.cs:808) hands the area back to the map once the stream rooms are gone. The exclusion therefore holds only while `HasStartArea` is true.
   - the title stream rooms (10_synthesis.md:217-218; line 218 is the mask rule). They share the map's `L0_Wallpaper` material (FrontRoomsSurfaces.cs:28; FrontRooms3DGame.cs:371-376, 401), so a material keyword alone would put ink on them. They need the per-cell ink-eligible bit (§11.1 Step 4) or a stream-only copy of the material. That includes the terminal room's end-wall facade, which faces the map.
4. **Messages and glyph families** (the shape is told by silhouette, not detail). Priority is STOP > HERE (or BREACH) > FLOW > GROUND.

   | Message | Family | Meaning | Weight (SP) |
   |---|---|---|---|
   | GROUND | neutral | Plain underprint, no direction | 0.35 |
   | FLOW (dir) | go: open chevrons | The route runs this way along this wall | 1.0 |
   | HERE | threshold: frame brackets | The route leaves through this face's door or window | 1.0 |
   | BREACH (a HERE variant) | stop: bracket with a cross bar | The Relay broke this door. It is passable and will never shut. | 1.0 |
   | STOP | stop: closed horizontal bars | This face is the mouth of a dead-end pocket | 1.0 |
   | Pressure variant (FLOW or HERE) | go or threshold, drawn doubled | Chase routing: a door away from the Relay | 1.0 |

   BREACH's rule is already code: a door the Relay breaks stays open and passable for the whole run (`BreakDoor`, FrontRoomsMapWorld.cs:1146-1156; `brokenDoors` :229; `PassageBetween` :1134). Only the glyph is proposed.
5. **Calm target.** The nearest **new threshold**: a Door or Window edge whose far cell is in a zone not in `zonesVisited` (FrontRooms3DGame.cs:168; filled at :898-910, cleared at :626).
   - `zonesVisited` is a private `HashSet<GridCoord>` of `ZoneInfo.id`. It is filled only after the player leaves the start rooms, and it has no accessor yet (§11.1 Step 6).
   - Door and Window edges occur only where the zone height changes (FrontRoomsMap.cs:364-367). So a new zone of the same height, reached through an Arch or Open edge, never counts as a new threshold. Widening the rule to "any edge whose far cell's zone id is unvisited" would change that.
   - Unbroken windows cost +4 cells (SP), because breaking glass is loud:
     - At run tier 1 it is heard at 40 × 1.4 = 56 m (`GlassNoiseRadius`, FrontRooms3DGame.cs:156; `hearing`, FrontRoomsHunter.cs:32; applied as `radius × tuning.hearing` at FrontRoomsMapHunter.cs:292).
     - Since P4 the run tier multiplies hearing by 1 / 1.15 / 1.3 / 1.45 / 1.6 (FrontRoomsLevelProfile.cs:139, 164-171; FrontRooms3DGame.cs:1639-1643). That gives 56 / 64.4 / 72.8 / 81.2 / 89.6 m at run tiers 1–5.
     - The distance is straight-line XZ. Noise is ignored while the Relay is unreleased, chasing or breaking a door (FrontRoomsMapHunter.cs:291).
   - If `doorsNeedKeys` is on (FrontRoomsLevelProfile.cs:33; false in code and in FrontRoomsLevel0.asset:47), a Door target comes after the key of the zone the player is standing in. The exception is a door a key has already opened (FrontRoomsMapWorld.cs:1913-1916).
     - Window targets are never key-gated, and tall zones have no key.
     - The map's working flag is private (:39). Read `Profile.doorsNeedKeys` or add a getter.
   - Calm routes never read the Relay's position.
6. **Pressure target. By default it is used only while the Relay is in Chase** (this fixes the radar leak). Proposed: a new system hooked to `relay.StateChanged` (FrontRoomsMapHunter.cs:149; the game already subscribes at FrontRooms3DGame.cs:617).
   - **Target.** An unbroken door, open or player-shut (and not locked when `doorsNeedKeys` is on), whose far cell is farther from the Relay by breadth-first search than its near cell.
     - The Relay never shuts doors. It only breaks them, and a broken door stays open (FrontRoomsMapWorld.cs:1147-1156). Only the player opens or shuts doors (`Use` → `SetDoor`, :1822-1834).
     - The Relay-distance BFS is the ink's own. It runs from `world.CellOf(relay.Position)` over the public `PassageBetween` (:1121), `IsBuilt` (:633) and `DoorBetween` (:1144), because the hunter's own `Search`/`depth` are private (FrontRoomsMapHunter.cs:494-520).
   - **Route costs (SP):**
     - +6 per cell within 2 steps of the Relay;
     - +2 per cell on its open straight line within 4 cells;
     - +2 for cells it walked through in the last 10 s, sampled from `relay.Position` (the hunter keeps no trail);
     - −1 per arch edge, **only when the Relay is not lined up with the arch's gap**. *Changed in Rev 2:* the bonus used to be unconditional, on the wrong premise that arches block sight. An arch narrows the Relay's view, but a ray through the gap passes: the gap is 1.1–1.8 m wide and 2.2 m tall, and both eyes sit at about 1.6 m (FrontRoomsMapWorld.cs:978, 1084-1090; FrontRoomsMapHunter.cs:976-1002). The exact alternative is a raycast from the Relay's eye, as `Visible` does (:987).
     - With a base step cost of 1, an arch step costs 0. A bucket queue handles that.
   - Windows and BREACH doors are never pressure targets.
   - **When pressure ends.** When the Relay enters Listen (Wander only ever follows Listen, FrontRoomsMapHunter.cs:220, 486), or 20 s (SP) after the Chase ends.
     - A Chase that goes into BreakDoor and then resumes Chase (:580-581, :953) has not ended.
     - A lost Chase normally runs Chase → Hunt → Search → Listen (:304, :392, :354).
     - Search alone lasts up to 15 s × the run tier's search factor, 1.0–1.6 (FrontRoomsLevelProfile.cs:141-142, 166-170). So the 20 s timer often ends pressure before Listen does.
7. **Only on-route cells point.** The route is a greedy descent of the target field, up to 24 cells (SP). At T0-T1 (run tiers 1–2) it also covers cells 1 step off the route. Every other dark cell shows GROUND.
   - Simulation of beacon-seeking walkers, in new zones per 100 cells: when every dark cell points, walkers ping-pong (2.4). On-route only gives 8.0. A random walker scores 5.6.
8. **STOP** marks the mouth cell of each dead-end branch.
   - Branches are found by iterative leaf pruning. Door and window edges count as passable, and the built-area boundary counts as open.
   - The maze has loops (non-tree edges roll Open or Arch at 18-70%, FrontRoomsMap.cs:94-96, 360), so pruning is the exact test. A branch BFS is not.
   - A FLOW route never enters a branch unless its target is inside it.
9. **Truth.** Before T4 (run tier 5) the ink never lies. It never points into a dead end, through a BREACH on the pressure route, or at the Relay's cell.
   - From T4 (run tier 5; on, Red §15 Q4; see §6), a **forged FLOW** may appear. It is the only mark that glows under a lit lamp, and only FLOW is ever forged.
10. **Commit gate.** A cell's message may change only when at least one of these holds:
    - (a) the cell has been unseen for ≥ 0.5 s;
    - (b) its own Ls ≥ 0.8, so the ink is invisible;
    - (c) a sag or wave front is at that cell (a deliberate beat).

    Each cell changes at most once per 2 s (SP). The glow *brightness* may change in view (that is physics). The *message* may not.
11. **Shape is procedural; the substance is a tier texture** (Rev 2: it is no longer in the print's B channel).
    - The message shape (`InkShape`) is computed in the shader from the world position plus the cell's message code.
    - The close-up content comes from two global Texture2DArrays. Both are fetched only inside the glow-mask branch. This is spec v1, agreed with the visual chat on 2026-10-03 as its Q2 (Tools/print/README.md, "Planned: glow-ink textures"; VISUAL_CHAT_TASKS.md:127):
      - `_FR_InkType` (1024², BC4, 16 layers) uses glyph-local UV: metres along the wall / 0.75, and (height − 0.8 m) / 0.75. The layer for each message, variant and forged state comes from the CPU lookup `float4 _FR_InkTypeLayer[4]`.
      - `_FR_InkSubstance` (1024×1536, BC4, 5 layers = run tiers 1–5) uses the warped print UV. Its layer is chosen by `_FR_InkTier`, which the wallpaper driver sets on `TierChanged`.
    - What you see is the procedural shape filled with that content. The substance follows the run tier, not print slices, so print jumps never change the substance or the message. Because it is sampled with the warped print UV, it moves with the print's warp and drift.
    - The print's B channel is reserved and always 0. Red chose the WP03 "Hard edge" precise print, whose frames are R density, G cream, B 0.
    - Cells with a non-GROUND message take no lamp-dropout strip slips; their print changes only while unseen.
12. **Delivery channels.**
    - Natural dark cells (always on).
    - The first-dark beat (once per run).
    - Calm power sags (periodic, local).
    - The chase wave (rare).
    - The drought breaker (a safety net).
    - The EAR bloom (when the Relay accepts a noise).
13. **Dark is never cover, and tall halls are not refuges.**
    - The Relay's sight is one 12 m eye-to-eye raycast (`tuning.sightRange`; tiers do not change it), with no light term (`Sees`, FrontRoomsMapHunter.cs:976-981; `Visible`, :987-1002; FrontRoomsHunter.cs:26).
    - Its speeds have no ceiling-height term. Ceiling height drives only the rig's poses and its ceiling-brush sound (FrontRooms3DGame.cs:1044; FrontRoomsRelayRig.cs:44-47, 204-209).
    - Since P4 the chase speed is multiplied by the run tier, ×1.00 to ×1.29, so it runs from 4.2 to about 5.4 m/s (FrontRoomsLevelProfile.cs:136-143, 162-169; FrontRooms3DGame.cs:1639-1643).
    - Nothing in the ink or its fiction may imply that dark hides you or that tall halls are safe.
14. **The HUD stops giving it away.** Done: Red decided this on 2026-10-03 and the map chat has landed it.
    - The Relay state text and the distance readout are hidden by default behind **one** assist toggle, RELAY READOUT. The player turns it on with Esc → O → T (pause screen, display settings). It is saved as `FrontRooms.Assist.RelayReadout` (FrontRooms3DGame.cs:91-94, 333, 1320-1326, 1564).
    - The HUD gate is `showThreat = play && released && relayReadout` (:1598-1600; panel at :1619).
      - With the assist off, nothing shows, CHASE and BREAKING DOOR included.
      - With it on, every state shows (LISTEN, HUNT, SEARCH, WANDER, CHASE, BREAKING DOOR), together with `RELAY nn M`.
    - **Open, a separate call for Red (§15 Q1):** should CHASE and BREAKING DOOR always stay visible, whatever the assist? That is about 5 lines in `UpdateHud`: split the gate into a state gate and a distance gate. It would reverse today's default.
15. **Photosafe by construction.**
    - Stutter-mode cells are forced to G = 0.
    - Ls is low-passed.
    - Each message changes at most once per 2 s.
    - Sags and waves are single dips with ramps ≥ 0.3 s.
    - Any lamp death in view dips at ≤ 2 Hz.
16. **Deterministic.** This is a requirement for the new ink code, not a description of today's code.
    - **Proposed:** every ink choice is hashed from (seed, cell & 63, event counters), with no `UnityEngine.Random` and no `_Time`. That needs the ink's own hash, with `cell & 63` and event-counter salts, layered on `MapHash.Hash(seed, x, y, salt, revision)` (FrontRoomsMap.cs:230-241). Today that hash takes full cell coordinates and no counters.
    - **Today:** map, lamp and Relay choices are hashed or xorshift-drawn from the run seed. Lamps use salt 211 (FrontRoomsMapWorld.cs:1178), and the Relay seeds its own xorshift (FrontRoomsMapHunter.cs:161).
      - No project shader uses `_Time`.
      - `UnityEngine.Random` is used in three places only: it picks the run seed (FrontRooms3DGame.cs:548; FrontRoomsMapWorld.cs:338), varies Foley pitch (FrontRooms3DGame.cs:1137) and picks the editor autopilot's goal (:1982).
    - Two inputs are not a pure function of (seed, cell):
      - Lamp levels run on a per-fixture clock (`f.clock += dt`) that restarts when a chunk is rebuilt.
      - A lamp's temperament depends on its chunk's generation tier (`MapChunk.tier`), which depends on when the player got there (FrontRoomsMapWorld.cs:1219-1221; FrontRooms3DGame.cs:898-917).
    - So the guarantee is: the same seed plus the same input and timing history gives the same ink timeline (synthesis P3 gate). This revision accepts that, because forged FLOW reads the run tier (§6).

## 3. Placement and generation per zone and tier

Nothing is hand-placed. Every message is derived per cell from two sources:
- **Map data that does not change with revision:** zones, border edges and keys (MAP_GENERATION.md:97).
- **The lamp temperament roll.**
  - It starts from `MapHash.Hash(seed, cell.x, cell.y, 211)` (FrontRoomsMapWorld.cs:1178). The odds of the chunk's generation tier turn it into a mode, `tierRules.At(MapChunk.tier).LampMode(roll)` (:1218-1221), unless a room module sets the lamp (:1223).
  - Since P4 it is not known from the seed alone. For an unbuilt cell, `LampModeOf(cell)` (§11.1 Step 1) is exact once the cache has generated the chunk. Before that it is a prediction at the current generation tier.

Routes are recomputed whenever a chunk is rebuilt. Streaming rebuilds a shifted chunk only when it is at least one chunk (24 m) away (FrontRoomsMapWorld.cs:703-710). The Level Designer's live `RebuildChunk`/`ReplaceModule` (:310-331) can rebuild anywhere, but only in the editor.

**Beacon sources, measured in a Python port of the generator (12-16 seeds; it skips modules, columns and the start area).** These were measured with the pre-P4 lamp odds, which are generation tier 1's (62/20/10/5/3). At generation tier 5 the odds are 40/25/18/12/5 (FrontRoomsLevelProfile.cs:164-171), so failing, dead and dim cells rise from about 18% to 35%.
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

**Per zone** (shares from FrontRoomsMap.cs:82-84, 115):

| Zone | Share of zones | Ink | Notes |
|---|---|---|---|
| Standard Level 0, 2.9 m | ~38% | Full | Long corridors. Decisions are read on end walls at T-junctions. |
| Low, 2.4 m | ~35% | Full | Short sightlines and many facing walls: the best near-read zone. Doors sit on its borders. |
| Tall hall, 5.4 m | ~10% | Full, glow band 0.8-2.0 m | Exits are windows only, so calm HERE marks windows. Lamps run ×1.6 with range 12, so neighbour spill is high: dead cells read bright, and lookdev must check the paper contrast. |
| Office, 2.9 m | ~17% of zones (13.6% of cells) | None (drywall) | Deliberate blind stretches. Routes add +1 per Office cell (SP), so the ink prefers paper. |

**Room modules.** Level Designer modules can author ModuleLamp Dead/Failing/Off per cell (FrontRoomsRoomModuleData.cs:30). `BuildFixture` applies the override at FrontRoomsMapWorld.cs:1223, and an Off lamp returns early at :1176.
- Recommended: at most 1 dark "reading room" per 4 chunks (SP).
- Off cells get no fixture at all. L = 0 for good, so they are starved and show no ink.

**Optional "border dusk" lever.** Cells beside door or window edges get higher failing and dead odds.
- *Changed in Rev 2:* this is now an increment on each generation-tier row of `FrontRoomsTier` (SP: failing +15 points, dead +5 points). At generation tier 1 that gives the original 25% / 10% instead of 10% / 5%. The fixed 25% / 10% rested on the single pre-P4 odds table. At generation tiers 4–5 the base dead odds (10%, 12%) already match or beat 10%, so the fixed version would add nothing there, or even lower the dead odds.
- It is a build-time change to the odds at FrontRoomsMapWorld.cs:1221, read by generation tier. It is not a runtime override.
- Use it only if playtest shows HERE is too rare. Naturally, only 14% of exit-adjacent cells are dark themselves (measured at generation tier 1).
- It needs visual-chat sign-off. LEVEL_MODULE_SPEC.md:76 still calls flicker odds the visual chat's numbers, yet P4 already moved them into the level profile's tier table (FrontRoomsLevelProfile.cs:121-125, 164-171) without a recorded sign-off.

**Storage.**
- 64×64 toroidal arrays indexed `(x & 63) + 64·(y & 63)`, with a 192 m period (10_synthesis.md:131).
- The built window is 40×40, or 56×56 at buildRadius 3. buildRadius is `[Range(1,3)]` with a default of 2 (FrontRoomsLevelProfile.cs:26-27), so the window never aliases.
- A chunk's texels are cleared on build and on drop.
- Persistent per-cell sets survive chunk drops, like `brokenDoors` (FrontRoomsMapWorld.cs:229). They hold the persistent lamp modes from `SetLampMode` (the first-dark kill and the drought-breaker promote). BREACH needs no set of its own, because it can be derived from `brokenDoors` at build (§4).

Tier effects on placement are in §6.

## 4. Triggers, charge/decay and timing

**Per frame, per built cell (CPU).** Compute L, Ls, W, C and G as in R1-R2.

On chunk build (the new `ChunkBuilt`, §11.1 Step 6), C starts at its steady state (SP):

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

**What each temperament does.** The levels come from `Level()` (FrontRoomsMapWorld.cs:1384-1416), which both tick paths call (desktop :1277, WebGL :1308). P4 changed only how often each temperament is rolled, set by the chunk's generation tier (`BuildFixture` :1221; odds at FrontRoomsLevelProfile.cs:164-171). The levels themselves did not change.

| Temperament | Lamp level | Ink |
|---|---|---|
| Steady (:1413-1414) | 0.98 (±0.02 shimmer) | Nothing. A full battery for its neighbours. Share: 62% at generation tier 1, 40% at tier 5. |
| Stutter (:1389-1397) | 0.95/0.05 bursts while Perlin(t·23) > 0.45. Each burst lasts 0.15–0.85 s, every 5–20 s; 0.97 ± 0.03 between bursts. | Forced G = 0, so it never flickers ink. Share: 20–25% by generation tier. |
| Failing (:1398-1402) | 0.25-0.70 at ~0.49 Hz (depth set by a ~0.20 Hz envelope), with Perlin dropouts to ~0.01–0.035 | Breathes: about 1 s readable every ~2 s. Full reads during dropouts. Share: 10–18%. |
| Dead (:1403-1410) | 0, with 0.8 blinks of 0.06–0.18 s, the next one 8-28 s after the last (the first 2–16 s after build, :1225) | Spill-charged steady glow. With 2 lit neighbours, C ≈ 0.39 (legible). In a dark cluster it is starved (blank). Share: 5–12%. |
| Dim (:1411-1412) | 0.42 (±0.03 at ~14 Hz; Ls ≈ 0.42 after the low-pass) | The gate is ≈ 0.25, so G ≈ 0.25 × C × weight. For weight-1 messages that is about 0.10 when isolated (C ≈ 0.42), 0.12 at the starting C of 0.5, and up to 0.25 with lit neighbours (C → 1). GROUND stays ≤ 0.087. Above Beacon, at or below Legible: a short-range read (~5 m is a design estimate). Share: 3–5%. |

**Fields and route.**
- The target field and the STOP pruning are rebuilt on any of:
  - `KeyTaken`, `DoorMoved`, `DoorBroken`, `GlassBroken` (FrontRoomsMapWorld.cs:72-78), plus a new `ZoneEntered`. Proposed: a static event on FrontRooms3DGame, which owns zone tracking (§11.1 Step 6);
  - `relay.StateChanged` (FrontRoomsMapHunter.cs:149);
  - `TierChanged` (run tier, FrontRooms3DGame.cs:47), for the per-tier columns of §6;
  - `ChunkBuilt` / `ChunkDropped` (new, §11.1 Step 6);
  - a mode switch. This is the calm ↔ pressure switch inside the wayfinding class, derived from `StateChanged` and the 20 s timer. No map change is needed for it.
- Rebuilds are rate-limited to 2 Hz (SP) and never run in a chunk-build frame (deferred one frame).
  - Events are coalesced with a dirty flag: `RebuildChunk` fires a drop and a build for one chunk in one call, and `Begin` can fire dozens of builds in one frame.
- The route is re-descended whenever the player changes cell (~0.94 s at the 3.2 m/s walk).
- Target stickiness: keep the current threshold until it is reached, or until it is ≥ 6 cells worse than the best alternative (SP).

**First-dark beat.** Proposed. It happens once per run. It replaces the earlier idea of a pre-dead cell, which is not in the code either.
- **Trigger:** after the start door shuts (MAP_GENERATION.md:23-24; FrontRooms3DGame.cs:779-789, `TerminalDoorShut`), and within 45 s (SP; no such timer exists yet).
- **Cell (Rev 2: chosen by path distance).**
  - The code guarantees only two connected cells: the door's cell (`startDoorCell`, cell 1) and the cell beyond it (`ahead`, cell 2). The edge between them can be Open, Arch or a shut Door (FrontRooms3DGame.cs:674-676).
  - `LeadsIntoMaze` (:691-710) proves that 150+ cells are reachable, but not that they lie in a straight line. A wall can stand right after cell 2, so cells 3–5 straight ahead are not guaranteed.
  - So at Space time the beat runs a breadth-first search with parent links over `PassageBetween`, from the cell beyond the start door (`startDoorCell`; depth 1 is `ahead`). It picks a cell at depth 3–5 whose target is ≤ 6 cells beyond it. No generator change is needed.
  - The alternative was to force a straight line in `MapRootFor`. That would shrink the set of candidate roots and need a new 100-seed check.
- **Start-group lamp hold.**
  - Lamps within light range of the start area, at or north of the door line, are `startGroup` 1 (FrontRoomsMapWorld.cs:1241-1251). While the player is in the start rooms they are held dark through `StartLampsNorth` (FrontRooms3DGame.cs:609). They rise with the door swing over 0.6 s (:124, :778) and are forced to 1 once the door is shut (:795).
  - The chosen cell will probably be in that group, so the beat must never fire before the shut. The trigger above guarantees that.
  - The hold sits outside `f.level` (:1280, :1309). The ink's Ls never sees it; only the visible lamp does.
- Its message commits while it is still lit (R10b).
- **The lamp death.** When the player is 6-9 m away and facing it, the lamp dies over 1.5 s: three dips at ≤ 2 Hz (`SetLampOverride(cell, Dip, …)`), then off for the run (`SetLampMode(cell, Off)`, persistent; §11.1 Step 1).
  - It goes "off", not "Dead". In the code, Dead (mode 3) still blinks to 0.8 every 8–28 s (:1403-1410), and `ModuleLamp.Off` exists only at build time (:1176). So the layer needs a new runtime off mode.
- The trigger logic (picking the cell, the distance and facing test, the once-per-run flag) lives in FrontRooms3DGame, which owns the start-door timing (:779-795), or in the wayfinding class.
- C = 1, so it blooms bright, then settles to its spill glow.

**Power sag.** Proposed: a calm pacing pulse. No sag exists in the code.
- **Frequency:** every 75-120 s at T0 (run tier 1) (SP).
- **Spacing from waves.** *Changed in Rev 2:* no sag starts within 30 s after a wave starts. That is the low end of the synthesis's 30–45 s subliminal-only window after a wave (10_synthesis.md:168). The old "never within 30 s of a wave" could not hold before a wave, because the wave fires on an unpredictable Chase. A wave that starts during a sag replaces the sag.
- **Never in Office.** No sag while the player stands in an Office zone. The check is `map.ZoneOf(map.CellOf(playerRoot.position)).theme == ZoneTheme.Office`, already used at FrontRooms3DGame.cs:1876. Also none while `inStartRooms`.
- **Shape:** a breadth-first search over `PassageBetween`, 4 cells around the player. That is up to 12 m of walking distance, not a 12 m circle. Lamps dip through `SetLampOverride(cell, Sag, 0.35, attack 0.6 s, hold 4 s, release 1.5 s)`.
- All messages in the radius commit at dip start. It is a snapshot, never a trail.
- **Needs:** a sag scheduler, a last-wave timestamp, and the per-run-tier intervals of §6.

**Chase wave.** Proposed: the synthesis's corridor wave (10_synthesis.md:143-144, 167). No wave exists in the code.
- **Trigger:** `relay.StateChanged(Chase)` (`event Action<HunterState>`, FrontRoomsMapHunter.cs:149, raised only by `SetState` :1004-1012).
  - It fires only when the previous state was not BreakDoor. The Chase stinger uses the same filter (FrontRoomsSoundDirector.cs:545). Without it, the Chase that resumes after a door break (FrontRoomsMapHunter.cs:953) would start a second wave.
  - It also fires only if the cooldown has passed (90 s at T0 = run tier 1, SP).
  - Subscribe through `FrontRooms3DGame.MapRunStarted` (FrontRooms3DGame.cs:39).
- **The front.** It starts at the Relay's cell (`world.CellOf(relay.Position)`) and runs at 8 m/s (SP), which is 0.375 s per 3 m cell (FrontRoomsMap.cs:52), over built cells (`IsBuilt`). It reaches 10 cells beyond the player (SP).
  - It crosses only edges where `PassageBetween` is Open. Never use `MapGrid.Passable` here, because it lets the front through unbroken glass.
  - It waits 0.5 s (a free tuning value) at a `Passage.ClosedDoor`.
  - That uneven door cost makes it a time-ordered expansion (Dijkstra-style or bucketed), not a plain BFS.
- **Lamps.** Each lamp dips through `SetLampOverride(cell, Dip, 0.3, attack 0.3 s, hold 2.5 s, release 1.2 s)`, called as the front arrives. The old LampDip `delay` argument is gone: the wave schedules the calls itself. Pressure messages commit as the front arrives.
- **Speed.** 8 m/s outruns the 5.5 m/s sprint (FrontRooms3DGame.cs:153) and the run-tier-5 Relay (4.2 × 1.29 ≈ 5.4 m/s).
- **Lead (Rev 2, corrected).** The front gains only 2.5 m/s on a sprinter. After the 5 s of stamina (:155) it is at most about 12.5 m ahead, and less after door delays, because it starts at the Relay's cell behind the player. Rev 1's "about 20 m of dim, readable corridor ahead" did not follow from these numbers.
  - Open (playtest), if 20 m is needed: start the front 7–8 m ahead of the player; raise its speed to about 9.5 m/s; or count the lamps' dim hold (0.3 + 2.5 + 1.2 s) as the readable window.
  - Also open: count the 10-cell reach from the player's current cell, not from their cell at wave start. A sprinter covers 27.5 m in 5 s.
- The same front also carries the visible print reprint, which needs the R2 print layer in main (§11.4).
- A door break takes 2.5 s only at run tier 1. The tier multiplier (1 → 0.52) brings it to about 1.3 s at tier 5 (FrontRoomsHunter.cs:21; FrontRoomsLevelProfile.cs:166-170).

**Drought breaker.** Proposed.
- **Trigger:** no legible sighting for 60 s, and the Relay is not pursuing: `relay.State` (FrontRoomsMapHunter.cs:118) is not Hunt, Chase or BreakDoor (SP).
  - BreakDoor sits inside a Hunt or a Chase (:580-581, :953). Leaving it out would let the breaker fire during a door break.
  - Open: should Search, which follows a lost chase, also block it?
- "Legible sighting" needs a new sighting tracker. It is frustum-only until the visibility class of §11.1 Step 3 exists.
- **Action:** promote one unseen Steady cell, 4-8 cells ahead on the current route, to Failing with the persistent `SetLampMode(cell, Failing)`. At most once per 90 s (SP).
  - Such a cell is always in a built chunk (buildRadius ≥ 1), so the mode must change on the live fixture as well as at build.
  - Never use `RebuildChunk` for this (:319-330). It redresses the whole chunk, causes a frame spike and may be seen.
- In the simulation, natural beacons come every ~6 cells, so this should rarely fire. It exists for Office-heavy and starved seeds. At high generation tiers the lamps are darker, so it will fire even less.

**EAR bloom** ("it heard you"; P2). Proposed.
- **Trigger:** `ListenPoint` takes a new non-null value, which means a Noise was accepted. `Noise` is at FrontRoomsMapHunter.cs:289-296, and :293 is the only place `ListenPoint` gets a value. The guards are at :291 (Dormant, Chase, BreakDoor) and :292 (the hearing radius).
- **Bloom:** the dark cells among the source cell and its open neighbours raise their GROUND weight from 0.35 to 1.0 over a 1.5 s ramp. The bloom holds while `ListenPoint` still equals that source, then decays with τ 4 s.
- **Polling.** The hunter raises no "heard" event, so the bloom polls `relay.ListenPoint` each frame against the last value, the way `UpdateRelayRig` reads it (FrontRooms3DGame.cs:1042).
  - A second accepted noise from exactly the same position does not register. An optional `Heard(Vector3)` event raised at :293 would fix that (about 2 lines).
  - `ListenPoint` is cleared on sight (:204) and in `Appear` (:463), which raises `Arrived` (:465). Either one ends a bloom's hold.
- At most one bloom per 4 s, because sprint steps call `Noise` a little more than every 0.3 s of movement (FrontRooms3DGame.cs:886-894, the call at :893).
- It is the only ink change allowed to start in view.
- No new EAR can start during Chase or BreakDoor, because `Noise` returns early then (:291). A bloom that was already holding when the Relay went from Hunt into BreakDoor may keep holding, since `ListenPoint` is not cleared there (:575-581).

**BREACH.** Proposed. No ink, mark or wall-face code exists.
- When `FrontRoomsMapWorld.DoorBroken` fires (declared at :76, raised in `BreakDoor(Door, Vector3)` at :1146-1156), mark the faces of that door's wall in both cells with the BREACH variant. It is permanent and committed under R10.
- `DoorBroken` carries only the door's position (`Action<Vector3>`). Two map-side changes are coming:
  - Doors become single-acting next (Red's decision).
  - The map chat is adding a break-direction event beside `DoorBroken`.
- BREACH should take the door's edge and cells from the new event if it carries them. Otherwise, read them from `DoorBetween(a, b)` or the `Door` itself (`a`, `b`, `edge`, `broken`; :124-137). Changing `DoorBroken` itself would also mean updating its sound subscriber (FrontRoomsSoundDirector.cs:439).
- Permanence needs no new store. Derive the mark at chunk build from the existing `brokenDoors` set (:229), the way the door rebuild re-applies the broken state (:1029). A public `IsBrokenDoor(a, b)` read accessor would serve the packer (§11.1 Step 4).

**Caught.** Proposed requirement: on Caught the ink must freeze, and in the title stream rooms G = 0.
- **What Caught stops today:** the player, the Relay (FrontRoomsMapHunter.cs:166), the zone and tier clock, and all sound.
- **What keeps running:** `FrontRoomsMapWorld.Update` (:653-670) keeps streaming, flickering lamps (`TickFixtures` :1268) and swinging doors (:1921). The 98%-opaque CAUGHT overlay only hides the world (FrontRooms3DGame.cs:1521-1522).
- So the wayfinding tick needs its own freeze. It subscribes to `relay.Caught` (FrontRoomsMapHunter.cs:151) through `MapRunStarted`, as the sound director does. If the lamp levels that feed Ls and C must freeze too, `TickFixtures` and `TickFixturesNear` need the same gate, or `f.level` is snapshotted at the catch.
- In the stream rooms, G = 0 comes from the R3 mask, not from any code that exists today.

## 5. Teaching curve

No HUD tutorial by default. Every lesson is a staged beat.

**First 5 minutes:**

| Time | Beat | Lesson | Guaranteed by |
|---|---|---|---|
| 0-3 s | The stream door opens (MAP_GENERATION.md:21). The maze lamps by the door rise in 0.6 s (FrontRooms3DGame.cs:124, 778). | Lit Level 0 looks normal. | The current start flow |
| ~5-45 s | **First dark:** a lamp dies in view 6-9 m ahead, and chevrons bloom on the side walls with FLOW or HERE on the end wall. The Relay is still dormant (released 3 s after the door shuts, 9-15 cells away: MAP_GENERATION.md:34; FrontRoomsMapHunter.cs:49). | Ink appears where light dies, and green points somewhere. | The first-dark beat |
| ~20-60 s | Following the chevrons ends at a door or window. The ceiling height changes and `ZONE 02` appears (FrontRooms3DGame.cs:1595). | Green leads to new ground. | Target ≤ 6 cells |
| ≤ 2 min | The first natural failing cell, breathing. | Wait for the gasp to read. | Drought breaker |
| 1-2 min | The first STOP at a junction (a 1-cell alcove at T0-T1, run tiers 1–2). | Bars mean a pocket. | Branch density (~50 in range) |
| 75-120 s | The first power sag: every wall within 12 m of walking flares for 4 s. | Sags give a snapshot of the whole neighbourhood. | Sag timer |
| First accepted sprint (P2) | EAR bloom on your own trail. | It heard you; leave quietly. | EAR |
| First chase | The wave runs past the player, and doubled chevrons point to a door. | Under pressure, the walls point to a door you can shut. | Wave (first chase is always past the cooldown) |

**First 3 runs (targets to validate):**
- **Run 1:** green = new ground; STOP = pocket. Notices the dark-only rule.
- **Run 2:** uses the chase wave and shuts doors. Learns that a starved dark cluster is blank (the physics rule) and that Office is blind.
- **Run 3:** scans the ceiling line for dead troffers. Reads end walls at 20 m and side walls within 6-8 m. Starts *choosing against* the ink (it is a lure as well as help). Recognises BREACH as a dead door.
- Lies (T4 = run tier 5) are expected only after run 3. Under the code's counting, run tier 5 comes at the 17th new zone, or after four 120 s stalls without one (FrontRoomsLevelProfile.cs:183, 160). At the ~3.6 zones per minute a random walker ticks, that is about 5 min in (an estimate), not the 8+ min assumed before Rev 2.

**Fallback:** if fewer than 50% of first-time players follow a FLOW within 60 s, add one Flash line written by narrative on the first beacon read. It names no symbols. `Flash()` is at FrontRooms3DGame.cs:1633, and the line shows in the hint card at :1603.

**Optional legend:** one title stream room with a dead lamp and a fixed, authored FLOW and STOP. It needs an exception to the stream-room mask (see §15).

## 6. Escalation over a run

The physics, gate and grammar never change, so what the player learns stays true. Escalation comes from scarcity, pacing, darker lamps, Relay tuning, and the late lie.

**Tier convention (Rev 2).**
- **Run tier.** Every tier in this doc is the run tier unless it says otherwise: `static FrontRooms3DGame.TierChanged(int)` (FrontRooms3DGame.cs:47), 1–5.
  - It fires 1 at run start (:636) and again on each rise in `RaiseTier` (:1645-1657). It never lowers.
  - T0–T4+ here are run tiers 1–5. The ink tier is the run tier − 1, and T4+ is tier 5 (`MaxTier`).
  - The run tier rises every 4 new zone ids, or by one after 120 s without a new zone (FrontRooms3DGame.cs:898-917; `FrontRoomsTierRules`, FrontRoomsLevelProfile.cs:155-190).
- **Generation tier.** The per-chunk generation tier (`MapChunk.tier`, FrontRoomsMap.cs:158) is stamped from `GenerationTier`/`Cache.Tier` when the cache first generates the chunk. It sets only that chunk's lamp odds and module tier. The ink reads it in two places only: `LampModeOf` and the border-dusk odds (§3).
- The ink columns below become fields on the existing `FrontRoomsTier` rows, read with `FrontRoomsTierRules.At(runTier)` (§11.4 S6).

| Tier (run tier) | Route beacons | Weight (SP) | Sag every | Wave cooldown | Wave reach ahead | STOP outside waves | Forged FLOW |
|---|---|---|---|---|---|---|---|
| T0 (1) | on-route + 1 off | 1.0 | 75-120 s | 90 s | 10 cells | all branches | none |
| T1 (2) | on-route + 1 off | 1.0 | 90-150 s | 120 s | 10 cells | all branches | none |
| T2 (3) | on-route | 0.9 | 120-180 s | 150 s | 8 cells | depth ≥ 2 | none |
| T3 (4) | on-route | 0.85 | 150-210 s | 180 s | 6 cells | depth ≥ 2 | none |
| T4+ (5) | on-route, within 15 cells of target only | 0.8 | 180-240 s | 240 s | 6 cells | depth ≥ 2 | ≤ 1 per 4 chunks; the metrics are a kill switch |

- The weight floor stays at 0.8, so the 20 m head-on read survives at every tier (a brief constraint).
- **Darker lamps by generation tier (P4, landed).** Chunks generated at higher tiers have more failing, dead and dim lamps: 40/25/18/12/5 at tier 5, against 62/20/10/5/3 at tier 1 (FrontRoomsLevelProfile.cs:164-171). That means more beacons but fewer lit neighbours, so more starved cells. The result is more hints, each harder to read. This is consistent with R2.
- **Forged FLOW** (T4+ = run tier 5; on, Red §15 Q4):
  - It reads the run tier (`TierChanged`), not the chunk's generation tier. So once the run reaches tier 5, a chunk generated earlier can still carry a forgery.
  - It sits in a lit Steady cell at an unmarked branch mouth and points into the branch.
  - The CPU writes G = 0.8 regardless of Ls, so it glows under full light. That is the tell.
  - Only FLOW is forged. HERE, STOP and BREACH are always true, so the "stop" words stay trustworthy, and a caught lie itself reveals a pocket.
  - It never appears in pressure mode, and never twice on one route.
- **Escalation coupling** (flagged for Red):
  - Following the ink gives about 2× new thresholds per minute, so ink followers tier up faster. This is deliberate: the ink is help and lure at once.
  - Since P4 the code counts 4 new zone ids per tier (`TierForZones`, FrontRoomsLevelProfile.cs:183). About 45% of walkable zone crossings are invisible same-height crossings, so zones tick about 3.6 per minute even for a random walker.
  - Suggestion (SP): count tiers by new thresholds instead, 6 per tier or 2.5 min, whichever comes first. That would need new code in the zone loop (FrontRooms3DGame.cs:898-917); still open, §15 Q2.
- **Never escalates:** truth before T4, BREACH permanence, the dark-only rule, R13.

## 7. Interaction with the Relay and the escape verbs

| Fact (code) | Ink behaviour |
|---|---|
| Sight is one 12 m ray with no light term, and tiers do not change it (FrontRoomsMapHunter.cs:976-1002) | Darkness, sags and waves change only what the player knows. The wave also darkens the player's own view of the Relay, which is a real cost. The dark body (#2B2928) with its pale head (D8D4C8) (FrontRooms3DGame.cs:276) silhouettes against glowing paper: a free scare, not a stealth rule. |
| Wander never crosses shut doors (FrontRoomsMapHunter.cs:473-487; its search treats doors as closed, :511-512) | Calm routes ignore the Relay, so a shut door the ink led you through also shields you from a wanderer. That is emergent, not promised. |
| Hunt and Chase plan through doors and break them in 2.5 s + 0.25 s at run tier 1, about 1.3 s at tier 5 (FrontRoomsHunter.cs:21; FrontRoomsLevelProfile.cs:166-170; MAP_GENERATION.md:36) | Pressure routes end at a door away from the Relay (HERE, doubled). After the player passes and shuts it, the next commit points onward. |
| LoseTrack follows through a door the player just used (FrontRoomsMapHunter.cs:304-312) | Pressure costs prefer a door followed by a bend (the +2 sight-line cost), so the player is out of its line when it arrives. |
| Broken doors stay open for good (FrontRoomsMapWorld.cs:1146-1156) | BREACH variant. Pressure routes skip it; calm routes may still pass through it. Over a run the ink becomes a map of dead doors, which matters more as run tiers shorten break time. |
| Unbroken glass blocks its path (its search skips Glass, FrontRoomsMapHunter.cs:511) and its sight | Calm routes may use windows (+4 cost). Pressure routes never do: the 1 s hold costs 4.2 m, and broken glass lets it follow. |
| Sprint: 5.5 m/s against a chase of 4.2 m/s (about 5.4 at run tier 5), 5 s of stamina, heard at 26 × 1.4 = 36 m at run tier 1 and about 58 m at tier 5 (FrontRooms3DGame.cs:153-155, 893) | The 8 m/s wave front stays ahead of a sprinting player, but at most about 12.5 m ahead (§4). EAR (P2) turns a sprint into a visible confession. |
| Door noise on any open or shut: 14 × 1.4 = 19.6 m at run tier 1, about 31 m at tier 5 (FrontRooms3DGame.cs:814-819) | It can trigger EAR at the door (P2). |
| Dead ends | STOP marks branch mouths; catches inside branches are a key metric. |
| Leash and relay (FrontRoomsMapHunter.cs:191-199, 396-425) | Unaffected. Relays now raise `Arrived(Vector3, string)` (:153, :465), which ends an EAR hold. A future OMEN wave is deferred (§14). |
| Keys glow yellow already (FrontRoomsMapWorld.cs:1972, 2069) | With `doorsNeedKeys` off, a key is just another calm target. With it on, the key comes first. |
| The HUD shows the Relay's state and distance only with the Relay Readout assist, which is off by default (FrontRooms3DGame.cs:1594-1600, 1619) | Done per R14 (2026-10-03). Without that change the ink would add no tension. |
| Tall halls have no speed term | The ink never treats tall halls as safe. |

## 8. Interaction with the moving visible print

1. **Opposite masking phases.**
   - The visible print changes in the dark: it slips inside its own cell's lamp-dark window (10_synthesis.md:139-142), because ink colour vanishes when unlit.
   - Phosphor messages change in the light (R10b), because the glow is swamped there.
   - A failing lamp gives both systems a legal window every couple of seconds, in opposite phases. A dead cell has no lit phase, so its message changes only when unseen.
2. **Message vs substance** (R11). The shape is procedural and constant across print keyframes, so jumps and crawls never move a message.
   - The substance is one `_FR_InkSubstance` layer per run tier, sampled with the warped print UV. It changes when the run tier rises (`_FR_InkTier`, set on `TierChanged`), never per print slice. Narrative may use the tier step, for example writing that has rewritten itself the next time you look closely.
   - `_FR_InkTier` is a global, so the switch can happen while a glowing wall is in view. It is fine detail, read under 2 m. How it transitions is the visual chat's call.
   - Message cells take no lamp-dropout strip slips, so the paper never slides under a readable mark.
3. **Discrete jumps** (the default) use the same unseen set as message commits: one visibility service serves both.
4. **Slow crawl** at scripted beats only uses cells showing GROUND. Moving ink never carries a message.
5. **Chase wave.** One time-ordered front at 8 m/s carries three things in lockstep: the visible reprint, the lamp dip and the pressure commit.
   - The 192 m rebase caveat (10_synthesis.md:144) does not apply, because the ink is off in the stream rooms.
6. **Relay wake.** Keep the synthesis's visible wake reprint (10_synthesis.md:145). It gives the two-layer deck line "the print shows where it walked; the ink shows where to go". Pressure routes add +2 on wake cells, so the two rarely overlap.
7. **Subliminal drift** (≤ 1-2 mm/s, ±0.3% scale) moves the substance too, because it is sampled with the warped print UV. That is imperceptible and fine; the shape mask is world-fixed.
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
| GROUND | The substance alone (`_FR_InkSubstance` at the current run tier) at weight 0.35 |

- **Direction** comes from the world axis (z when |n.x| > 0.5, else x), never the mirrored PlanarFrame u (FrontRoomsSurface.shader:157-161). Arrows therefore point the same world way from both sides of a corridor.
- **Substance rule:** inside strokes, the `_FR_InkType` and `_FR_InkSubstance` content keeps a mean ≥ 0.6 in any 100 mm square (1.0 is the solid field, about 0.55 is knocked-out type). That way strokes read as solid at 20 m. Fine detail is for reading under 2 m. Print B plays no part (reserved = 0).
- **Print chevrons vs ink chevrons (updated 2026-10-03, after Red chose the WP03 "Hard edge" print and dropped the ghost emboss).** Three cues keep them apart:
  - **Orientation:** the print's chevrons point UP the wall (55° mitred bands, plus the motif arrows), while FLOW chevrons point ALONG the wall toward the route.
  - **Medium:** the print is albedo seen in light; the ink is emission seen only in the dark.
  - **Arm angle:** the narrative chat (30_narrative_phosphor.md §10) asks for FLOW arms of about 30–35°, kept isolated inside the glow band, so that in failing cells, where both show, no ink chevron is ever drawn at the print's 55°.

  The final angle is the visual chat's call.

**Distances** (vertical FOV 76°, FrontRooms3DGame.cs:247, gives ≈ 691/d px per metre at 1080p):
- A 0.40 m chevron is ~14 px at 20 m, with strokes ~3.5 px.
- Side walls read only within 6-8 m, because foreshortening at 20 m down a 3 m corridor is ~0.075. **The decision read is the end wall at a T-junction or turn**; side walls confirm it up close.
- Fog is ExponentialSquared at 0.014 (FrontRoomsLook.cs:19, 46-48), so ~92.5% of the glow survives at 20 m.

**Luminance, not hue.**
- Glyph-to-paper ratio ≥ 1.3 in a full-charge dead cell with 2 lit neighbours; ≥ 1.15 in a failing cell at Ls 0.3 (SP).
- Emission is capped at ~12% of a lit wall's luminance, so the ink stays faint.
- Colour is about 530 nm (ZnS:Cu). Meaning is carried by shape and luminance, so it is safe for protan and deutan players.
- Screen budget: green covers ≤ 3% of pixels on average and ≤ 8% at p95, so Level 0 stays yellow.

**Photosensitivity.**
- Gate: R15, plus the P2 gate (≤ 3 flashes/s; no reversal above 3 Hz over > 25% of the screen), measured with glow, print, sags, waves and fixtures combined (10_synthesis.md:228).
- The existing stutter mode (FrontRoomsMapWorld.cs:1389-1397) can exceed 3 Hz in bursts on its own. Audit it regardless of the ink.

**Settings:**

| Setting | Effect |
|---|---|
| Reduce wall motion (required, 10_synthesis.md:197-200) | No travelling wave; a static 4 s sag of radius 4 cells at Chase start. Ls τ 1.0 s. Failing cells show a 3 s running mean (a steady, faint read). No crawl. The first-dark beat becomes a single 1.5 s fade. No EAR ramp shorter than 1.5 s. |
| Ink assist | Intensity ×1.5, GROUND off, strokes +30% |
| Relay readout (landed 2026-10-03; off by default) | One assist toggle (Esc → O → T) shows the Relay's state and distance together. Rev 1's three-way Off / State / State + distance is dropped under Red's one-toggle decision (R14). |
| Deaf and hard-of-hearing | EAR and the wave are visual first; sound only reinforces them. |

The ink is never the only signal: doors and windows stay visible as geometry.

## 10. Failure modes and exploits

### 10.1 Judge findings on the base design and how they are resolved

| # | Finding (lens) | Resolution |
|---|---|---|
| 1 | Too reliably helpful; reads as UI, not dread (play) | **Fixed in part.** Calm ink ignores the Relay (it can lure you into it). Following it speeds escalation. Hints are on-route only and about 2× random, not a GPS. Starved cells go blank. Physical lies from T4 (run tier 5). HUD distance retired. The residual risk is accepted and measured with the "help, lure or noise" survey. |
| 2 | The HUD distance undercuts tension; calm-to-pressure leaks the Relay (play) | **Fixed:** R14 (the Relay's state and distance sit behind one assist, off by default; landed 2026-10-03); R6 pressure is Chase-only by default. |
| 3 | The wave may push chase escape too high (play) | **Fixed:** wave cooldown 90-240 s and reach 10→6 cells by run tier; the wave dims the player's view of the Relay; run tiers shorten door breaks (2.5 s → about 1.3 s). Cap metric: escape ≤ 80% at T0, ≤ 60% at T3+ (run tiers 1 and 4+). |
| 4 | Heavy tuning; the invisible mode switch makes one chevron mean two things (play) | **Fixed:** the pressure variant is drawn doubled; pressure commits only at the wave front or unseen. Build order in slices (§11.4). |
| 5 | Office blind zones and dark clusters read as bugs (play) | **Fixed:** the fresh/starved physics (R2) makes blank dark a rule, and narrative explains it. Office stays blind and is accepted as deliberate (+1 route cost; measured). |
| 6 | Largest map-chat surface; LampDip affects lighting and sound (feasibility) | **Accepted and sliced.** Rev 2: one shared lamp-override layer (§11.1 Step 1), folded into `f.level` in both tick paths. The hum follows `light.intensity` (FrontRoomsSoundDirector.cs:333) as a volume dip for free. |
| 7 | `zonesVisited` is private; new events needed (feasibility) | **Accepted:** a read-only `IReadOnlyCollection` plus a static `ZoneEntered` on FrontRooms3DGame, owned by the map chat (LEVEL_MODULE_SPEC.md:181 gives it FrontRooms3DGame.cs). |
| 8 | Dijkstra over `PassageBetween` may exceed 0.4 ms (feasibility) | **Fixed:** cached per-chunk adjacency bytes and flat 4096 arrays with a bucket queue (about 13 buckets); every edge read behind `IsBuilt`; rebuilds deferred out of chunk-build frames and time-sliced if over 0.5 ms. |
| 9 | Per-face shader logic plus 16 glyph slices (feasibility) | **Fixed:** procedural shapes and zero extra print slices. Rev 2: the close-up content is now two global arrays (Q2), fetched only inside the glow-mask branch. So glowing pixels pay up to two extra samples, and every wallpaper pixel pays one point load. |
| 10 | Depends on an unbuilt visibility service; hard to test (feasibility) | **Mitigated:** slices S1-S3 use a conservative frustum-only test (an occluded cell counts as seen, so the only risk is fewer commits). Commits through the lit path need no visibility at all. Debug overlay and 100-seed audits. Rev 2: WG2 is WebGL-only, so the ink needs its own desktop class (§11.1 Step 3). |
| 11 | R10 froze the ink against the moving print, weakening the sandwich (fit) | **Fixed:** R11. The substance is sampled with the warped print UV, so it moves with the print; the message stays fixed. Rev 2: the substance changes with the run tier, not per print slice. |
| 12 | Omniscient ink softens the dread (fit) | **Accepted as a narrative slot.** It knows the building, never the monster, and it lies late. Narrative frames it as ambiguous help. |
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
| Glow beyond 16 m, or glow through the start door | Use the logical level (`LampLevel`); ignore the hold and fade (FrontRoomsMapWorld.cs:1280-1284, 1309-1319) |
| Invisible same-height borders (~45%) tick ZONE without a threshold | The ink targets thresholds only; tier counting should follow (§15 Q2) |
| Lure into noise (calm route through glass, heard at 56 m at run tier 1, about 90 m at tier 5) | +4 window cost; otherwise the intended risk |
| False refuge (dark or tall = safe) | R13; the first contact in a glowing corridor shows it sees you |
| Edge of the world | Built-boundary cells are fallback targets; failed chunks (`failedChunks`, the catch in `Build`, FrontRoomsMapWorld.cs:756-770) count as walls |
| Interior shift after 30 s away (`shiftAfterSeconds`, FrontRoomsLevelProfile.cs:31) | Targets do not change with revision; new routes commit ≥ 24 m away, unseen |
| Aliasing on stream, Office and start walls; jamb faces on cell lines | Ink-eligible mask (per-cell bit plus per-surface mask); clear texels on build and drop; jamb normal bias |
| EAR spam or noise sonar (tapping sprint to probe) | One bloom per 4 s. From T3 (run tier 4) the bloom is delayed 2-4 s if telemetry shows sprints under 0.5 s |
| Lure poisoning (players distrust all ink) | Lures only forge FLOW and only at T4+ (run tier 5); cut them if the true-FLOW follow rate after the first lure falls below 50% |
| Glyph clipping on 0.6 m columns or between trims | Accepted; or fade where a face is narrower than 0.75 m (visual's call) |
| Starved late game (high generation tiers darken the map) | Drought breaker and sags keep a floor |

## 11. Implementation data flow

### 11.1 Pipeline

**Step 1: Lamp-override layer (map chat; interface pending agreement).**

This replaces Rev 1's separate asks (`LampLevel`, `LampMode`, `LampDip`, `KillLamp`, `PromoteLamp`) with one shared layer. It is being agreed between three chats: the map chat (关卡设计), the wallpaper-print chat (this doc) and the Relay-pursuit chat (系统设计). The names and types below are a sketch, not final. None of it exists today: the only runtime lamp controls are the global `StartLampsNorth/South` holds (FrontRoomsMapWorld.cs:1238-1239).

| Member | Meaning |
|---|---|
| `SetLampOverride(cell, kind, multiplier, attack, hold, release)` returns a handle | A timed envelope on one lamp. `kind` is Omen (the Relay-pursuit chat), Dip (the first-dark dips and the chase wave) or Sag (the power sag). There is no delay argument: callers schedule the call themselves, and the wave calls it as its front arrives. |
| Stacking | `level = base × MIN(active multipliers)`, so overlapping overrides never multiply down to black. |
| `SetLampMode(cell, mode)` | Persistent kill (a new runtime Off mode) and promote (e.g. Failing). See the rules below the table. |
| `LampModeOf(cell)` | Pure (no side effects) and valid for unbuilt cells. It combines the seed hash (salt 211, :1178; first draw :1219), the odds of the chunk's generation tier (`tierRules.At(MapChunk.tier).LampMode(roll)`, :1221), the module override (`MapChunk.lamp`, :1223; Off at :1176), and then any `SetLampMode`. See the rules below the table. |
| `LampLevel(cell)` / `LampBaseLevel(cell)` | From the logical level only (`f.level`), never `light.*` or the lens. `LampLevel` includes active overrides; `LampBaseLevel` is the level before them. Defined for built cells only, with a sentinel for unbuilt, start-area and Off cells. |
| `FixtureChanged` | Raised on threshold crossings only, never per frame: the lit/dark crossing (`level > .01`, the test at :1282/:1313), mode changes from `SetLampMode`, and lamps appearing at build or disappearing at drop. The wayfinding class polls `LampLevel` every frame and does not need it; it is for listeners such as sound and the Relay-pursuit chat. The synthesis asked for `LampLevel` *or* `FixtureChanged` (10_synthesis.md:175). |
| Tick | Folded into both tick paths: `TickFixtures` (desktop, :1268-1291, `f.level = Level(f)` at :1277) and `TickFixturesNear` (WebGL, :1293-1330, at :1308). See the rules below the table. |

`SetLampMode` rules:
- It is stored in a world-level dictionary next to `brokenDoors` (:229). Drop and rebuild never clear it, so it survives chunk drops.
- It does not go in `MapChunk.lamp`, which `Cache.Shift` regenerates and the validator compares.
- It applies live to a built lamp, and in `BuildFixture` after the module line (:1223). The tier roll (:1219-1221) is still drawn, so later rng draws stay deterministic.
- It wins over the tier roll and the module lamp (to confirm). It does nothing in start-area cells.
- Open: should it survive a revisit shift?

`LampModeOf` rules:
- For a chunk the cache has not generated yet, it predicts at the current `GenerationTier`, with Auto lamps.
- It must never call `Cache.Get`. That would generate and cache the chunk early (FrontRoomsMap.cs:748-760).

Tick rules:
- Multiply right after `Level(f)`. Then the light intensity, the lens emission, the on-test and `CheckLampStatesForTools` (:1350) all stay consistent.
- The start-area hold stays outside `f.level` (:1280, :1309).
- WebGL's `FarEmissionStep` of 0.05 (:1265) lets a 0.3× dip through.

Prerequisites and notes:
- **A cell→Fixture index.** `Fixture` (:98-122) is private and stores no cell. Fixtures live only in each chunk's list (:152; added at :1226). Add a `GridCoord cell` field set in `BuildFixture` (:1173), plus a `Dictionary<GridCoord, Fixture>` cleared in `Unregister` (:728) and `RebuildChunk` (:319).
- **The kill mode must look the same live and after a rebuild:** a dark lens, not a missing troffer.
- **Rough size:** 120–200 lines, plus EditMode tests for persistence across Drop, Shift and RebuildChunk, the envelope, and both tick paths.
- **Sound follows for free, as volume:** the hum reads `light.intensity` (FrontRoomsSoundDirector.cs:333).

**Step 2: `FrontRoomsWayfinding` (map chat).** Proposed: a new plain-C# class in `Assets/Scripts/FrontRoomsMap/`, owned by FrontRoomsMapWorld.
- **Where it ticks:** in `Update`, right after `TickFixtures(Time.deltaTime)` (FrontRoomsMapWorld.cs:663, before `TickDoors` at :664). It is primed once after `TickFixtures(0f)` in `Begin` (:405). Both tick paths keep `f.level` fresh for every built fixture, so it gets the same inputs on desktop and WebGL.
- **When it runs:** only in a real run, after `MapRunStarted`, or only when the world is not standalone. Otherwise the Level Designer's Play mode (`PlayHere` → standalone world, :346-350, 653-663) would show ink.

Each frame:
- (a) L, Ls, W, C, G per built cell. That is ≤ 1,600 cells at the default buildRadius 2 (3,136 at 3), about 0.05 ms with flat arrays.
- (b) Event-driven fields at ≤ 2 Hz:
  - the target field: a bucket Dijkstra. Step costs are 1–6 when calm and 0 to about 12 under pressure, so it needs about 13 buckets;
  - the Relay BFS (pressure only). It is the class's own, or it reads the hunter's chase-replan `depth` through a new read accessor (that dictionary is private);
  - leaf pruning for STOP.

  Every edge read goes through `IsBuilt` or the `MapChunk` edge arrays. `PassageBetween` calls `Cache.Edge`, which generates any chunk that is not yet in the cache (FrontRoomsMap.cs:750-761, 793-802).
- (c) Route descent and message assignment.
- (d) The commit gate (R10).
- (e) Sag, wave, first-dark, drought and EAR timers.
- (f) Packing the map's channels into the shared `Color32[4096]`. The map writes G, B and A; the visual driver writes R (Step 4).

**Step 3: Visibility (shared; owner open).** Proposed. The synthesis's version is a BFS over see-through edges from the camera cell, plus `TestPlanesAABB` (10_synthesis.md:135-138). It produces one set, used by both print jumps and ink commits.
- **What exists:** none of it is in the code. Only the inputs are: `CellOf` (:624), `PassageBetween` (:1121), `DoorBetween`/`Door.progress` (:1144, :134), `IsBuilt` (:633), `CellCenter` (:629) and `ZoneOf` (:636).
- **WG2 cannot supply it.** WG2 (VISUAL_CHAT_TASKS.md:86, still running in a clone) builds `FrontRoomsVisibility` only under `(UNITY_WEBGL && !UNITY_EDITOR) || FRONTROOMS_WEBGL_PREVIEW` (10_webgl_plan.md:151; 02_visibility_portals.md:346). Desktop and the Editor would get nothing.
- **The ink needs its own read-only class.** It must compile on every platform and touch no renderer or light. It could share WG2's 2D portal-walk algorithm. It needs:
  - a see-through predicate that counts a door as open at `Door.progress > 0`, not at the walking threshold of > .6 (:1135);
  - a start-area case: `PassageBetween` returns Wall there (:1129), and `startDoorCell` is private (:247);
  - for the exact walk, the planned `OpeningSpan` hook (`ArchOpening` is private, :1084).
- **Until then, use the frustum-only fallback.** It is conservative: about 355 cells marked seen against about 13 actually visible (02_visibility_portals.md:14). The only cost is fewer commits.
- **Red's call (§15 Q13):** sharing one set between desktop gameplay and WebGL rendering would break the rule that WebGL work never changes desktop or the Editor.

**Step 4: Pack and upload (visual chat driver).** Proposed; none of it exists yet.
- **The texture:** one 64×64 texture, created linear: `new Texture2D(64, 64, TextureFormat.RGBA32, false, linear: true)`. The project renders in Linear colour space, and an sRGB texture would decode G and corrupt the B bitfield.
- **Upload:** `SetPixelData` + `Apply(false)`, 16 KB per frame at worst. A dirty flag skips frames where nothing changed.
- **Reads:** the shader reads it with `LOAD_TEXTURE2D` and wraps with `& 63` itself, so point filter and Repeat wrap are harmless but unused. Bind a black texture at load.
- **Globals:** `_FR_CellState`, `_FR_Ink` (intensity, reduceMotion, assist) and `_FR_InkColor`, plus the Q2 ink globals: `_FR_InkType`, `_FR_InkSubstance`, `float4 _FR_InkTypeLayer[4]` and `_FR_InkTier`.

| Channel | Content | Owner |
|---|---|---|
| R | Print state (frame offset or transition) | Visual |
| G | Ink glow G (weight, EAR, forge already applied) × 255 | Map |
| B | Bits 0-1 direction N/E/S/W; bits 2-3 message GROUND/FLOW/HERE/STOP; bit 4 pressure; bit 5 BREACH; bit 6 forged; bit 7 ink-eligible | Map. For bit 7 the map writes the per-cell bit from `InStartArea` and `ZoneOf(cell).theme`; the shader masks per surface (doors, jambs, Office drywall). |
| A | Ls × 255 (from `LampLevel`, with a fixed default for lampless cells: Off and the start area), also the print's flicker mask | Map |

Where the B bits come from:
- BREACH (bit 5): a public `IsBrokenDoor(a, b)` backed by `brokenDoors` (:229), or the break-direction event.
- Pressure (bit 4): `StateChanged`.
- Forged (bit 6): set at run tier 5 (`TierChanged`).

The final layout is agreed with the visual chat.

**Step 5: Shader (visual chat).** Proposed, for after the R2 print layer reaches main.
- **What exists today.** FrontRoomsSurface (Assets/Resources/Rendering/FrontRoomsSurface.shader) has no `_FR_PRINT` keyword and no print fetch. ForwardLit's only keywords are `_FR_MESH_UV` and `_EMISSION` (:96-97), and albedo is one `_BaseMap` sample (:185). R2 (`_FR_PRINT` + `_PrintTex`) is still in the visual chat's private copy (VISUAL_CHAT_TASKS.md:101).
- **Keyword and globals.** Add `#pragma shader_feature_local_fragment _FR_PRINT` to ForwardLit only, and declare the globals outside `UnityPerMaterial` (:52-71).
- **Where the ink is written.** Into `s.emission`, outside the `#if defined(_EMISSION)` block (:251-253), since the wallpaper materials do not use `_EMISSION`. `MixFog` (:256) then fogs it.
  - Use `nGeo` (:173), `input.positionWS` and `cavity` (:208).
  - The floor is at y = 0, so the height above the floor is `positionWS.y`.
- **Cost:**
  - one point load of `_FR_CellState`. This is a new texture instruction, unless it is shared with a per-cell load the print makes;
  - about 50–80 ALU: cell address and decode, FaceSign, InkShape with fwidth anti-aliasing, the 0.8–2.0 m band, the pressure doubling and the flag tests;
  - up to two array samples, on glowing pixels only.

  The GPU budget (≤ +0.2 ms) is plausible on desktop but must be measured.

```hlsl
int2  c     = (int2)floor((input.positionWS.xz + nGeo.xz * 0.5) / 3.0) & 63;
half4 cs    = LOAD_TEXTURE2D(_FR_CellState, c);                 // the one point load
uint  code  = (uint)(cs.b * 255.5);
float along = abs(nGeo.x) > 0.5 ? input.positionWS.z : input.positionWS.x;   // world axis, never mirrored u
float sgn   = FaceSign(code & 3, nGeo);                         // +1/-1 along this face; 0 means the route crosses it -> GROUND
float h     = input.positionWS.y;                               // floor at y = 0
float glowMask = cs.g * InkShape((code >> 2) & 3, code >> 4, along * sgn, h) * _FR_Ink.x;   // outline + 0.8-2.0 m band
if (glowMask > 0)                                               // the Q2 textures are fetched only here
{
    float2 typeUV = float2(along * sgn / 0.75, (h - 0.8) / 0.75);                  // glyph-local
    half type = SAMPLE_TEXTURE2D_ARRAY(_FR_InkType, sampler_BaseMap, typeUV, InkTypeLayer(code)).r;          // layer via _FR_InkTypeLayer[4]
    half sub  = SAMPLE_TEXTURE2D_ARRAY(_FR_InkSubstance, sampler_BaseMap, PrintUV(input.positionWS, nGeo), _FR_InkTier).r;  // warped print UV
    s.emission += _FR_InkColor.rgb * glowMask * type * sub * cavity;               // how type and substance combine is the visual chat's call
}
```

The print's B channel is never read (it is reserved = 0). `PrintUV` is the P0 helper, with the Q1 warp.

- **Unset globals.** With the globals unset, `_FR_Ink.x` and `_FR_InkColor` read 0, so a fresh edit session and batch lookdev show no ink. Two catches:
  - An unset `_FR_CellState` is not a guaranteed zero. Unity binds a tiny default texture, and an out-of-range load is backend-dependent.
  - Globals set in Play stay set after Play exits.

  So the driver binds its own defaults: an `[ExecuteAlways]` driver, as in 10_synthesis.md:98, sets `Texture2D.blackTexture` and `Vector4.zero` in OnEnable, OnDisable and on `EditorApplication.playModeStateChanged`. And Step 2 runs only in a real run.
- The ink never writes albedo, normal, smoothness or cavity.

**Step 6: Events in.**
- **Existing:**
  - `DoorMoved`, `DoorBroken`, `GlassBroken` (`Action<Vector3>`) and `KeyTaken` (`Action<GridCoord>`) (FrontRoomsMapWorld.cs:72-78);
  - `relay.StateChanged` (`Action<HunterState>`, FrontRoomsMapHunter.cs:149);
  - `ListenPoint` (`Vector3?`, :127; polled);
  - `Arrived(Vector3, string)` (:153).
- **The run tier:** `static FrontRooms3DGame.TierChanged(int)` (FrontRooms3DGame.cs:47). It fires 1 at run start (:636) and again on each rise (:1657). For comparison, the per-chunk generation tier is `MapChunk.tier` (FrontRoomsMap.cs:158), and the map's current one is `GenerationTier` (FrontRoomsMapWorld.cs:50).
- **Exists but private:** the visited set (`FrontRooms3DGame.zonesVisited`, :168). It needs a read-only accessor, e.g. `IReadOnlyCollection<GridCoord> ZonesVisited`.
- **New:**
  - `ZoneEntered`: a static event on FrontRooms3DGame, raised at :903-906 next to the existing `Event("zone")` row, with the zone id and a "first visit" flag.
  - `ChunkBuilt`: raised where `built[coord] = chunk` runs (:884), never on the failed-build path.
  - `ChunkDropped`: raised in `Drop` (:719) and `RebuildChunk` (:319-331), not in the failed-build cleanup (:765). For teardown, use `MapRunEnded` (raised at FrontRooms3DGame.cs:1663).
  - The break-direction event the map chat is adding beside `DoorBroken`.

**How a listener reaches the run.** Through the static `FrontRooms3DGame.MapRunStarted(FrontRoomsMapWorld, FrontRoomsMapHunter)`, declared at FrontRooms3DGame.cs:39 and fired at :634 in `StartRunInPlace`. It fires before `map.GenerationTier = tier` (:635) and before `TierChanged` (:636). So take the tier from `TierChanged`, not from the map inside the handler.

**Events out:** `LampDipped(cell)` (raised by the override layer), `WaveStarted(origin)`, `EarBloom(pos)`, `InkLegible(cell)` for telemetry, and `Event("ink", …)` rows.
- The telemetry sink `Event(string, string)` is private (FrontRooms3DGame.cs:1659). So the game subscribes to the ink's events in its run-start wiring (around :617-634) and forwards them as rows.
- Rows reach disk only in `End()` (:1671), so only runs that end in a catch save them.

**Budget (SP; desktop, buildRadius 2 = 1,600 cells):**
- **CPU:** ≤ 0.4 ms on average and ≤ 1.0 ms on rebuild frames.
  - This needs the cached per-chunk adjacency. A Dijkstra straight over `PassageBetween` would make about 6,400 dictionary-backed calls per rebuild.
  - It excludes the Step 3 visibility test. A per-cell `TestPlanesAABB` fallback costs 0.2–0.5 ms on its own unless it is culled per chunk first.
  - It stacks on the print driver's ~0.1–0.3 ms (10_synthesis.md:133).
  - It roughly doubles at buildRadius 3.
  - WebGL needs its own budget line, at about 4–5× (10_webgl_plan.md:111).
- **GPU:** ≤ +0.2 ms (to be measured; Step 5).
- **Upload:** 16 KB per frame at worst.
- **Memory:** about 32 KB for the texture (the GPU copy plus its readable CPU copy), plus roughly 100–200 KB of CPU-side state (staging, Ls, C, timers, fields, adjacency). Not 16 KB.
- **Perf gate** (10_synthesis.md:230):
  - The 58.7 fps / p99 19.4 ms baseline is a single pre-P4 editor autopilot run of seed 2554 only (Verification/main-autopilot/report.json, M3 Max). Its fps is counted over the whole autopilot clock and capped at 60.
  - The gate's test set is not built: seeds 2554 and 20388 plus a Level 0 corridor flythrough, with FrameTimingManager GPU time. No flythrough harness and no GPU timing exist yet.
  - Re-run the baseline on the P4 code for both seeds, with the run tier pinned or logged (`tierLog`), before using the −1 fps / +1.5 ms p99 budget.
  - The project's own acceptance bar is avg ≥ 55 fps and p99 ≤ 33 ms (LEVEL_MODULE_SPEC.md:147).

### 11.2 Owner asks

| Owner | Must build |
|---|---|
| **Map chat (关卡设计)** | **Lamps:** the lamp-override layer of §11.1 Step 1 (interface pending agreement with the wallpaper-print and Relay-pursuit chats), including the cell→fixture index, the persistent modes and both tick paths. **Wayfinding:** `FrontRoomsWayfinding` (fields, pruning, route, messages, commit gate, timers, EAR, BREACH, forged FLOW, packing of G/B/A). **Events:** expose `zonesVisited` and `ZoneEntered`. Raise `ChunkBuilt`/`ChunkDropped` from `Build` (:756-770; `built[coord] = chunk` at :884) and from `Drop`/`RebuildChunk` (:719-725, :319-331); `Stream` is at :688-717. Add the break-direction event beside `DoorBroken`, and a read accessor for broken doors by edge. **Freeze on Caught.** **Debug overlay** (route, messages, branches): a live-run mode in `FrontRoomsMapDebugWindow`, which today draws only a preview cache. **Tests:** extend the existing chunk determinism check (FrontRoomsMapValidator.cs:204-215) to the wayfinding data. Add a 100-seed route truth audit; the harness (FrontRoomsMapVerification) checks structure only, so the wayfinding must compute from `FrontRoomsMapCache` data to run headless. Add a test for 0 commits while seen (new; needs the commit gate and visibility). Add an ink-follower autopilot policy in FrontRooms3DGame.cs (`AutopilotPlan` :1953, `AutopilotSteer` :1895, editor-only), not in FrontRoomsMainScenePlaytest. Switch it with a SessionState key or command-line argument from that launcher, and add new report fields. Seed the planner, which today picks goals with unseeded `UnityEngine.Random` (:1982). **Docs:** fix LEVEL_MODULE_SPEC §4 now. It omits the tiered temperament odds, and :76 still calls flicker odds the visual chat's numbers; LEVEL_DESIGNER.md:81 still lists tiers as "to come". Document the lamp layer, events and wayfinding once they are built, including that a lamp's mode depends on its chunk's generation tier and that overrides apply in both tick paths. MAP_GENERATION already covers P4. **Done since Rev 1:** the tier index (`TierChanged`, `GenerationTier`, `MapChunk.tier`) and the HUD change (R14). |
| **Visual chat (游戏视觉)** | **Print layer:** promote the P0 print layer (R2) to main. Its `ApplyPrint` in FrontRoomsRenderSetup already keeps `_FR_PRINT` and its values through RenderSetup regeneration (10_synthesis.md:97), in the private copy. **Upload:** the state upload driver (Step 4). **Shader:** emission with `InkShape`/`FaceSign`, the height band, the cavity mask and the per-surface ink-eligible mask (stream, Office, start; the map writes the per-cell bit). Sample `_FR_InkType` and `_FR_InkSubstance` inside the glow-mask branch (Q2). Draw the glyphs for FLOW, HERE, STOP, BREACH, the doubled pressure variant and forged FLOW. No print-B work: print B stays reserved = 0. **Look:** ink colour and contrast against the targets. Lookdev captures at 1/6/12/20 m head-on and 6 m grazing, plus tall-hall spill. The combined flash audit. Reduce-motion and ink-assist paths. No strip slips on message cells. **Sign-offs:** lamp overrides (first-dark, drought breaker, optional border dusk), and the P4 per-tier lamp odds (FrontRoomsLevelProfile.cs:121-125, 164-171), which already changed the numbers LEVEL_MODULE_SPEC.md:76 calls the visual chat's. **Visibility:** not via WG2, which is WebGL-only (§11.1 Step 3). |
| **Wallpaper-print chat (this doc)** | Make the `_FR_InkType` and `_FR_InkSubstance` arrays once Red picks the narrative direction (Tools/print/README.md, spec v1). Check the stroke-fill rule (mean ≥ 0.6 per 100 mm inside strokes) on those sources in Tools/print/print_tool.py, which already carries and seam-checks print B. Set `_FR_InkTier` on `TierChanged` from the wallpaper driver. Agree the lamp-override interface (§11.1 Step 1). |
| **Sound chat (声音设计)** | **What follows for free:** lamp overrides change the hum's volume with no audio code. The hum reads `light.intensity` (FrontRoomsSoundDirector.cs:332-335; lamps registered by name at :255-258) and sends it as the FMOD `Level` parameter (:352). **No pitch dip to tune:** `Level` automates volume only (0 → −60 dB, .05 → −30 dB, 1 → 0 dB). A pitch curve on `Level` would also bend failing and stuttering lamps, so a sag-only pitch dip needs a separate parameter (for example a per-voice `Sag` value from the override layer), sent by FrontRoomsSoundDirector. **Limits:** only the 4 nearest lamps within 10 m have hum voices. A 0.3–0.35× dip never crosses the Tick/Strike thresholds (.15 / .6), so sags and waves make no ballast click. The first-dark kill does cross .6 → .15 and fires the existing Tick; the ballast-death pop can replace or layer it. **New work:** a wave stinger aligned to `WaveStarted` (the Chase stinger already fires on `StateChanged`, :545). A ballast-death pop for the first-dark beat and the drought breaker. A quiet positional EAR cue, played only when a bloom cell is dark and in view. Never sound an unseen commit. The ink itself is silent; under AUDIO_CONTRACT.md the print never touches audio files. Update the hooks table. |
| **Narrative chat** | The slots in §12 |

### 11.3 Testing hooks

- **`inkEnabled` editor toggle** for A/B testing. It is new, and trivial once the ink exists.
- **Tier pinning.**
  - The generation tier can already be pinned: `FrontRoomsMapCache.Tier` (FrontRoomsMap.cs:742), `Generate(coord, revision, tier)` (:558) and `GenerationTier` (FrontRoomsMapWorld.cs:50). The interaction tests already use it.
  - The run tier cannot be pinned. FrontRooms3DGame's `tier` is private (:172), reset at run start (:613), and pushed to the map at :635 and in `RaiseTier` (:1651).
  - Add an editor-only pin read from SessionState (like `AutopilotSeedKey`), applied at :613, with `RaiseTier` skipped while it is pinned. That is about 10–20 lines.
- **`Verify 100 seeds`** (FrontRoomsMapVerification.cs:23-52) reports structure only: edges, zones, keys, pillars, modules, and a walls-only flood fill.
  - Beacon spacing needs `LampModeOf`, with the tier rules passed into the validator. Today the validator runs at generation tier 1 only.
  - Branch counts are a modest new leaf count.
  - Target reachability needs the wayfinding target field.

### 11.4 Build order (weekly slices)

| Slice | Content | Needs |
|---|---|---|
| S1 | Lamp-override layer (§11.1 Step 1: index, `LampLevel`/`LampBaseLevel`, `LampModeOf`, `SetLampOverride`, `SetLampMode`, `FixtureChanged`, both tick paths); `ChunkBuilt`/`ChunkDropped`; G gate on natural lamps (already tiered by generation tier); GROUND only; per-cell ink-eligible bit (`L0_Wallpaper` is shared with the stream rooms) | Map, about one slice. Visual: the `_FR_CellState` upload, the ink path in FrontRoomsSurface and keyword persistence. These are blocked until R2 P0, then Q1, then Q2 land; a constant substance can stand in before Q2. No visibility needed, because nothing commits yet. |
| S2 | Calm target field, route, FLOW/HERE, commit gate, debug overlay. Prerequisite: read-only `zonesVisited` and `ZoneEntered` | Map; frustum-only visibility |
| S3 | STOP via leaf pruning; truth audit | Map |
| S4 | First-dark beat (path-distance cell, after the start-door shut) | Map, visual sign-off, sound pop. Rev 1 also listed the HUD change here; it has landed. |
| S5 | Chase wave (filtered trigger, time-ordered front), pressure variant (Relay trail sampled from `relay.Position`), BREACH | Map: needs the S2–S3 commit gate; the dips come from S1. Visual: the pressure and BREACH glyphs; the shared reprint wave needs R2 in main. Sound: the `WaveStarted` cue. |
| S6 | Power sags, drought breaker, ink columns on the existing `FrontRoomsTier` rows (beacons, weight, sag interval, wave cooldown and reach, STOP depth, forge rate), read by run tier | Map |
| S7 | Desktop visibility class (new; WG2 is WebGL-only); EAR (P2) | Map (+ visual for the shared print/ink set), sound; needs Red's OK (§15 Q13) |
| S8 | Forged FLOW, on from T4 = run tier 5 (Red, §15 Q4); the forgery metrics act only as a kill switch | Map, visual lookdev |

The HUD and the tier backbone have landed, so the map work is now closer to 7 slices. The timeline depends more on the visual chain (R2 → Q1 → Q2) and on the visibility class than on the map chat.

## 12. Narrative slots

| Slot | What the mechanic needs |
|---|---|
| What the underprint is and who printed it | Period-plausible ZnS:Cu (1990 era lock; strontium aluminate is too late). Only on wallpaper, never on Office drywall. |
| Why it knows the way to NEW thresholds and never leads back | Knowledge of the building's layout that survives interior shifts. Candidates: a previous wanderer's trail, the building's memory, a printing defect. |
| Why it needs light to charge, and why dark clusters are blank | A rule players can repeat, for example "the paper only remembers what it was shown". |
| Why it reacts to the Relay's chase (wave, doors away from it) | Do the walls fear it, serve it or record it? It must **not** imply the Relay can't see in the dark. |
| Help or herding | Following it speeds escalation; the fiction can frame it as both. |
| What the ink shows up close (under 2 m) | The content of `_FR_InkType` (per message, variant and forged state) and `_FR_InkSubstance` (one layer per run tier); see 30_narrative_phosphor.md. The content changes with the run tier, not with print slices. Stroke-fill rule: mean ≥ 0.6 inside strokes. |
| The look and naming of FLOW, HERE, STOP, BREACH and the pressure variant | The families must stay go = open, threshold = frame, stop = closed. Any link to the old relief chevrons. |
| What the power sags are | Building electrics, the Relay, or something else. |
| The first-dark beat | Flavour for the ballast pop, plus an optional one-line Flash if playtest needs it. |
| EAR | Is the paper listening, or answering? |
| Forged FLOW (on from T4) | Who forges it, and why a forgery cannot hide under light. Only "go" marks are forged. |
| Optional anchor | The Gilman sub-pattern (10_synthesis.md:238-240). Real ZnS:Cu egress marking (FAA floor-path rules after 1983) as research with original photos and sources. |

## 13. Playtest plan and metrics

**Phases:**
1. **Lookdev stills:** direction call at 6/12/20 m head-on and 6 m grazing, with and without assist, plus a colour-blind filter pass.
2. **Automated audits:** 100 seeds and autopilot.
3. **Class playtest:** an A/B test with ink on and off on the same seeds, with the HUD Relay readout off in both arms (the default since 2026-10-03).
4. **3-run sessions:** 3 runs per player for the teaching curve.

| Metric | Target (SP) | If missed |
|---|---|---|
| Hint strength: new thresholds per minute, ink on / off | 1.6-2.2× (sim: 2.0) | Above 2.5 it is a GPS: cut sags or T0 adjacency. Below 1.3: raise the weight or enable border dusk. |
| Follow rate: FLOW within 8 m in view ≥ 0.5 s, then the next 3 cells descend the field | 50-75% | Revisit the first-dark beat or the shapes |
| Teaching: first beacon in view → first follow | < 20 s for ≥ 70% of first-time players; ≥ 70% cross their first ink-led threshold within 60 s | Add the Flash line |
| Beacon spacing on routes actually walked | One readable beacon every 5-8 cells (sim 6.2); legible sightings every 20-40 s median | Drought breaker interval; border dusk |
| Chase escape rate, wave vs no wave | Rises, but ≤ 80% at T0 and ≤ 60% at T3+ (run tiers 1 and 4+) | Shorten wave reach; lengthen cooldown |
| Doors shut per chase | Rises with the wave | Pressure HERE readability |
| Catches inside leaf-pruned branches | ≥ 50% lower with ink on | STOP depth or weight |
| Office time per run; Office-heavy seeds | Track | +1 → +2 route cost |
| Minutes per tier, ink on vs off | ≤ 1.5× faster with ink | Tier counting by thresholds |
| Comprehension, after run 1 with no text: "what does the green mean?" | ≥ 70% say "way on / new area / door"; ≥ 50% name the dead end; < 15% say "dark hides me" | First-contact beat; fiction |
| Survey: help, lure or noise? | A mix of help and lure; noise < 25% | Weight, spacing |
| Forged FLOW (on from T4) | 30-50% followed on first exposure, < 20% by the third; true FLOW still followed ≥ 50% afterwards | Cut forgeries (the kill switch) |
| EAR (P2) | ≥ 60% leave the bloom cells within 8 s without sprinting by the second exposure | Cue clarity |
| Truth audit (automated) | Every route ends at a valid target; 0 FLOW into branches; 0 pressure routes through windows or BREACH | Bug |
| Change-blindness audit | 0 commits while seen, except at sag, wave or EAR fronts; < 1 flip per cell per 2 s | Bug |
| Flash audit (normal and reduce-motion) | ≤ 3 flashes/s; no > 3 Hz reversal over > 25% of the screen | Lengthen ramps; fix stutter |
| Green screen coverage | Mean ≤ 3%, p95 ≤ 8% | Raise thresholds |
| Perf | CPU ≤ 0.4 ms average, ≤ 1.0 ms on rebuilds; GPU ≤ +0.2 ms; within the synthesis gate, re-baselined on the P4 code (§11.1 Budget) | Time-slice the fields |

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

1. **HUD. ANSWERED and landed (Red, 2026-10-03).**
   - The Relay state text and the distance readout are hidden by default behind ONE assist toggle, RELAY READOUT (Esc → O → T; FrontRooms3DGame.cs:91-94, 333, 1564, 1594-1600, 1619). The map chat has landed it.
   - **Still open, a separate call:** should CHASE and BREAKING DOOR always stay visible, whatever the assist? Today they show only with the assist on. Changing that is about 5 lines in `UpdateHud`.
   - Original question: may the map chat retire `RELAY nn M` and the HUNT/SEARCH state text and move them behind an assist?
2. **Tier counting:** count by new thresholds (6 per tier or 2.5 min), or keep the code's zone ids (4 new zones per tier or a 120 s stall, landed in P4)? Zone ids tick about 3.6 per minute even for a random walker.
3. **Pressure trigger:** Chase only (recommended), or also Hunt and Search within 8 cells (stronger, but it leaks the Relay)?
4. **ANSWERED (Red, 2026-10-03): forged FLOW is ON from T4** (= run tier 5). Original question: **Lies:** enable forged FLOW at T4+, or keep the ink truthful forever?
5. **Office blind zones (13.6% of cells):** keep them as deliberate hint-free stretches?
6. **First-dark beat:** use the in-view lamp death (recommended) or the original pre-dead cell? Either one needs visual-chat sign-off on the lamp override. Rev 2: the cell is now picked by path distance (§4).
7. **Lamp overrides:** may the drought breaker and the optional border dusk change lamp temperaments (LEVEL_MODULE_SPEC.md:76)? P4 already moved the base odds into the tier table, with no recorded sign-off.
8. **EAR:** in the core at S7, or cut? Should the OMEN arrival wave be scheduled at all (it needs a hunter change)?
9. **POCKET variant** (DOOR·BLIND hide-hole) as a calm secondary message: worth the extra shape?
10. **Legend room** in the title stream (a fixed FLOW and STOP under a dead lamp): it needs an exception to the stream-room mask. Yes or no?
11. **Escalation coupling:** is it acceptable that following the ink makes a run escalate faster?
12. **Deck framing:** use "the print shows where it walked; the ink shows where to go" as the one-line explanation of the sandwich?
13. **Visibility (new in Rev 2):** the ink's commit gate needs a desktop visibility class, because WG2 is WebGL-only. May it share one visible-cell set with WebGL rendering? Or must the two stay separate, under the rule that WebGL work never changes desktop or the Editor (§11.1 Step 3)?
