# Relay pursuit: audit and redesign

Status: proposal, 2026-10-03. Nothing is implemented. Every number marked **SP** is a starting point for playtest.

Written by the chat 怪物追捕机制设计审计 (systems), with:
- **关卡设计** (map / Relay code owner): level design, feasibility. See §9.
- **Design the narrative of the phosphor wallpaper print** (narrative): fiction. See §10 and `research/relay_pursuit/30_narrative.md`.

Figma: design file `0tCbAiVUlrPId3RWd9LRif`, page 2099:76, section `FRONTROOMS · RELAY PURSUIT · AUDIT + REDESIGN` (2441:3804) at x 7897, y 26369, frames RP01–RP10 (2441:3805 … 2441:3883). Diagram data: real generator output (Python port of the `FrontRoomsMap` edge rules) and autopilot reports; scripts and SVGs in `research/relay_pursuit/sim/`.

**Red's brief (2026-10-03).** Right now the player has no room to explore the Backrooms and has to keep running. Pursuit should follow a logic:
- the Relay starts tracking the player's sound only after something calls it, such as entering certain rooms or breaking glass;
- when it comes, the lamps where it is start to flicker irregularly.

**Red's follow-up, the same day.** Given in the wallpaper chat and relayed to this one; it replaces the second point.
- Make it a **staged warning**. The lights do **not** dim where the monster is.
  1. When it is fairly close, the lamps in the **player's** room flicker.
  2. Closer still, the player hears **muffled footsteps**.
  3. When it **sees** the player, a clear, recognisable but non-jarring sound says "you are targeted". Then the chase formally begins.
- All Relay state text stays off the HUD (assist only).
- The chase wave fires on CHASE only.
- Narrative: **EGRESS**.

---

## 0. Summary

1. **Why the player always runs.** The Relay is never away.
   - It is released 3 s after the start door shuts.
   - It appears a median 24 m (straight line) from the player.
   - It hears a sprint step through any wall within 36 m. That covers about 465 cells, and 98.5 % of its possible spawn cells.
   - It sees 360° at 12 m with no reaction time.
   - When it loses contact for 45 s, it is teleported back.
   - The HUD shows its distance at all times.
   - Every verb the game teaches (sprint, open a door) calls it, and nothing sends it away.
2. **The new rule is one sentence the player can learn.** *Noise calls it. It warns you three times. It leaves when it finds nothing.*
3. **The loop:** AWAY → (called) ARRIVE → INVESTIGATE → SEARCH or CHASE → WITHDRAW → grace → AWAY. Three new states, appended to `HunterState`: Away 7, Arrive 8, Withdraw 9.
4. **What calls it:**
   - The building's alarm "panel": a run-wide **Attention** meter. Sprinting and doors fill it; walking does not.
   - **Instant triggers:** glass, alarm doors, ringing phones and other trigger rooms you can read before you enter.
5. **Its own ears:** sound travels the map (walking distance plus door penalties), not straight lines. A sprint step is heard over about 30 cells instead of 465, and from a distance the Relay hears roughly where you were, not exactly.
6. **Three warnings** (Red's staging, §7), each measured as walking distance from the Relay to the player:
   1. **Lights:** within 30 m, the lamps in *your* room flicker together in irregular bursts. The bursts come more often as it nears. The lamps settle when it goes.
   2. **Steps:** within 15 m, its footsteps become audible, muffled through walls.
   3. **Lock-on:** when it sees you (±70° cone, about half a second to notice), a clear but quiet lock-on cue plays. The chase starts when the cue ends.
   - No lamp changes more than 3 times a second, and there is a Reduce Flashing option (§7.4).
7. **It leaves.** A failed search ends in WITHDRAW, followed by a grace window. That window is the exploration time Red asked for.
8. **Tiers stretch the hunt, not the panic:**
   - the call threshold falls, grace shortens, and from tier 3 it patrols before leaving;
   - the "stall 120 s → tier up" rule is removed.

---

## 1. Audit: why the player always runs

### 1.1 What the code does now

Sources: `FrontRoomsMapHunter.cs`, `FrontRooms3DGame.cs`, `FrontRoomsHunterTuning` in `FrontRoomsHunter.cs`, scene values in `FrontRooms3D.unity`, and `FrontRoomsLevelProfile.cs`.

| # | Fact | Where | Effect on the player |
|---|---|---|---|
| A1 | Released `releaseDelaySeconds` 3 s after the start door shuts behind the player. In autopilot runs that is 6.6–11.8 s into play | `UpdateMapPlay` (`streamFade >= 0`), `Tick` Dormant | There is no calm opening. |
| A2 | `Arrive` places it 9–15 cells of walking from the player, out of sight, preferably behind | `Arrive`, `SpawnMinCells/MaxCells` | Measured straight-line distance: median 24 m (p10 17 m, p90 32 m). It always starts inside hearing range. |
| A3 | `Noise(source, radius)` tests flat straight-line distance only. Walls, doors and floors don't count. Walking is silent. Door and glass noises come from the door or window, not from the player. Noise is ignored in Dormant, Chase and BreakDoor | `Noise` (l.291–295) | Tier 1: sprint step 26 × 1.4 = **36.4 m** (every 0.3 s); door open *or* shut 14 × 1.4 = **19.6 m**; glass 40 × 1.4 = **56 m**. The tier hearing multiplier (up to 1.6) takes these to **58 / 31 / 90 m** at tier 5. |
| A4 | A heard noise sends it to the *exact* source point | `HuntToward(world.CellOf(source), source)` | Sound works as GPS. A sprint step gives your exact feet. |
| A5 | Sight is a ray from its 1.6 m eye to the player's camera within 12 m, in every direction. No reaction time and no light term; any non-player collider blocks it. A door it is breaking is finished first | `Sees`, `Tick` | No "almost seen" moment. Any line of sight while it wanders becomes a chase that same frame. |
| A6 | Wander picks random cells 6–14 cells from *itself*, never through shut doors | `Wander` | It wanders around where it spawned, which is near you. |
| A7 | Leash: after 45 s with no contact, if it is more than 30 cells of walking away, it re-`Arrive`s 9–15 cells from you | `Tick` leash | Getting away doesn't last. |
| A8 | No state ever takes it off the map | state machine | No exploration window can exist. |
| A9 | Tier rises every 4 new zones **or** after 120 s with no new zone. Zones are small (median about 63 cells), and same-height zones join through arches | `UpdateMapPlay`, `FrontRoomsTierRules.stallSeconds` | Lingering to explore is punished, and walking on is too: the autopilot reached tier 3 at 60–74 s (关卡设计, 20 seeds). |
| A10 | Lamps flicker at random by tier odds (tier 1: 62 % steady, 20 % stutter, 10 % failing, 5 % dead, 3 % dim). They have no link to the Relay | `FrontRoomsMapWorld.Level`, `FrontRoomsTier.LampMode` | The world gives no honest tell, so a Relay flicker must be a distinct signature, not just more flicker. |
| A11 | HUD shows `RELAY nn M` and its state (WANDER/HUNT…) whenever it is released. Red has already decided to make this an assist, off by default | `FrontRooms3DGame` HUD | The threat is on screen all the time, even while it wanders far away. |
| A12 | The only listed escape verb is sprint: 5.5 m/s for 5 s against chase 4.2 m/s. The hint card says "it hears every step" | `CalmHint`, stamina | The escape verb is also the beacon. |

### 1.2 Measurements

**Hearing.** Measured on the generated map: 366 random positions, Python port of the `FrontRoomsMap` edge rules, modules ignored.
- **465 cells** lie inside the 36.4 m sprint radius. 90 % are reachable on foot, at a median walking distance of 39 m (p90 57 m).
- Walking distance is 1.55× the straight line (median) and 2.33× (p90). Through walls, the Relay hears places that are a long walk away.
- **98.5 %** of the cells the Relay can spawn in (9–15 cells of walking) are within hearing of the player's next sprint step. The minimum over all trials was 85 %.

**Autopilot: a trace of the system, not difficulty data.** 17 distinct main-scene runs after Wander landed, each up to 75 s.
- **Caveats (关卡设计):**
  - Only the last report is kept in the repo; the rest come from other sessions' private copies.
  - The route RNG is unseeded (`FrontRooms3DGame.cs:1982`), so a seed does not replay a run.
  - The autopilot is not a player model: it doesn't know where the Relay is, never hides or shuts doors, and sprints once at 16–22 s.
- The Relay's released time:

  | State | Share |
  |---|---|
  | Wander | 59 % |
  | Listen | 18 % |
  | Hunt | 13 % |
  | Search | 8 % |
  | BreakDoor | 1.5 % |
  | Chase | 0.5 % |

  **No run has a gap:** once released, it never leaves the map.
- 9 of 17 runs started a hunt 13–19 s into play (one at 51 s). The early ones (13–14 s) were the autopilot opening a door, heard about 20 m away; the later ones were its sprint.
- 3 of 17 runs ended caught.

**Reading.** Even when it isn't hunting, it is never far, and the player is told so. A human player sprints and uses doors, because those are the game's verbs, and each use costs them. So the safe strategy is to keep moving, which is what Red felt.

### 1.3 What already works and is kept

- The Relay body, A* detours, door breaking (blows at 0.5 s steps) and `CrossingPoint` routing: nav test 60/60.
- Search: three spots, listening at each, give-up time (`searchLookSeconds`, `searchMaxSeconds`).
- LoseTrack following through the door you just used.
- The rig hooks: `SetListenTarget`, `DoorBlow`, `Step`, `DoorSqueeze`, `CeilingHeight`.
- The audio contract events: `StateChanged`, `DoorBlow`, `Caught`, `Arrived`.

---

## 2. Design goals

| Goal | Test (SP) |
|---|---|
| G1 **Room to explore.** Most of a tier-1 run is calm | Relay AWAY or withdrawing for ≥ 60 % of run time at tier 1, ≥ 35 % at tier 5 |
| G2 **Cause → effect.** The player can always say why it came | Every call is logged with its cause. In playtest, ≥ 8/10 players name the cause after a chase |
| G3 **Readable approach.** Warnings come in order before every encounter | Every CHASE is preceded by warning stage 1 or 2 for ≥ 3 s, and always by the stage 3 cue (autopilot check) |
| G4 **Sound is an estimate.** Distance blurs it | Hunt target error grows with distance (§5) |
| G5 **Escape is a decision.** Breaking line of sight, shutting a door and going quiet each work | A quiet walker who breaks line of sight escapes ≥ 50 % of tier-1 chases |
| G6 **It leaves, and you can tell** | Every failed search ends in WITHDRAW. Your room's lamps settle once it is beyond 36 m |
| G7 **No new contracts broken** | `HunterState` append-only; sound through events; lamp look stays with the visual chat; WebGL cuts platform-gated |

---

## 3. The new loop

```
            noise fills Attention / instant trigger
  AWAY ───────────────────────────────────────────▶ ARRIVE (entry 10–16 cells from the call point;
   ▲                                                 │        steps in after the arrive delay)
   │ grace (40 s at T1)                              ▼
  WITHDRAW ◀── search fails ── SEARCH ◀── reaches ── INVESTIGATE (walks to the estimate)
   ▲                            ▲          estimate   │
   │                  loses you │                     │ spotting meter full → lock-on cue (stage 3)
   └─ T3+: patrol first ────────┴──── CHASE ◀─────────┘

  Warnings run beside the states, by walking distance to the player:
  ≤ 30 m: stage 1 (your room's lamps)   ≤ 15 m: stage 2 (its steps)   seen: stage 3 (lock-on)
```

| State | New? | What it does | Speed | Warning (§7) |
|---|---|---|---|---|
| **Away** | **new, appended (7)** | Off the map. Attention runs; grace may hold calls | — | none |
| **Arrive** | **new, appended (8)** | The call picks an entry 10–16 cells from the call point. After `arriveDelay` (3 s at T1) `Arrived(pos, tag)` fires (P4 hook) and it walks in. Nothing changes at the entry itself | — | by distance |
| Hunt (= INVESTIGATE) | kept | Walks to the noise *estimate*; new noise it hears updates the target | `huntSpeed` 2.6 (research suggests 2.2) | by distance |
| Search | kept | Three spots, listens at each | 0.7 × hunt | by distance |
| Chase | kept | Begins when the lock-on cue ends; runs, replans every 0.35 s, loses you after 1.5 s | `chaseSpeed` 4.2 | stage 3, then the LD chase wave |
| BreakDoor | kept | 5 blows over 2.5 s | 0 | by distance |
| Wander (= PATROL) | kept, repurposed | From tier 3 only: patrols before withdrawing | 0.8 × hunt | by distance |
| **Withdraw** | **new, appended (9)** | Walks to a Relay entry far from you, reachable without a door, and leaves | hunt | fades as it goes; your lamps settle |
| Listen | kept | The pause after it arrives | 0 | by distance |
| Dormant | kept | Before the first call of the run | — | none |

Contract notes (关卡设计):
- `HunterState` is append-only: Away 7, Arrive 8, Withdraw 9. Ping 声音设计 first.
- `Released` changes to "not Dormant and not Away". The HUD, rig visibility, autopilot PASS and the sound contract all read it.
- `TickBreak` must resume into Arrive, Withdraw and Wander as well as Chase and Hunt.

The leash teleport (A7) is replaced by the **handoff** (§8.2): when the call point is far, it leaves where it stands and arrives near the call, out of your sight.

---

## 4. What calls it

Two channels, matching the fire-alarm fiction (§10): the **panel** hears the whole building roughly; the **Relay's own ears** hear nearby exactly.

### 4.1 Attention (the panel)

Attention is a run-wide number from 0 to 100, kept in the hunter (关卡设计's preference: the state rules and the tier hearing multiplier live there).
- The game only labels each disturbance: `Disturb(kind, point)`.
- Glass and trigger rooms call `Summon(source)`.
- **While Away**, a disturbance adds its full gain: the panel hears the whole building.
- **While the Relay is on the map**, gains fall off with walking distance (§5).
- The tier table gets its own `attentionGain` column, separate from `hearing`, so the two never multiply.

| Source | Attention (SP) | Note |
|---|---|---|
| Walking, turning, looking | 0 | Quiet is free |
| Sprint step (one per 0.3 s) | +3 (≈ +10 per second) | A full 5 s sprint ≈ 50 |
| A door opens or shuts | +6 | today's `DoorMoved`, both ways |
| A door shut while sprinting ("slam") | +15 | new: `DoorMoved` + sprinting |
| Window broken | **call now** | `GlassBroken` |
| Trigger room / alarm door / ringing phone | **call now**, or per ring | §4.2 |

**Decay.** −2 per second after 4 s without a gain.

**Call.** When Attention reaches the tier's threshold (60 at tier 1), the panel calls the Relay to the **estimated** noise centre: the centroid of the last 10 s of noises, with an error radius:

| Noise | Error radius |
|---|---|
| sprint | 3 m |
| door | 1.5 m |
| glass, alarm | 0 |

**While it is on the map** a new call is a *re-dispatch*: its hunt target moves to the new estimate. When Attention passes the threshold during INVESTIGATE or SEARCH, the panel updates the zone.

**Grace.**
- The run's first 45 s in the map: Attention may not call. Instant triggers still do.
- After a WITHDRAW: grace lasts `graceSeconds` (40 s at tier 1). During grace, Attention gains are halved and instant triggers still call.

### 4.2 Instant triggers ("you went in there")

This is Red's "entering certain rooms". The full list is in §9 (level design) and §10 (fiction). The rule:
- every trigger is readable **before** the player commits: a sign, a fixture or a sound at the doorway;
- every trigger offers something in return: a shortcut, a key, or a new zone.

| Trigger (EGRESS set) | Read from outside | Fires on | Reward that makes it a choice |
|---|---|---|---|
| Window (every tall zone) | the glass itself | glass broken | the only way into a tall zone |
| Alarm door | push bar: "EMERGENCY EXIT ONLY — ALARM WILL SOUND" | opening it | a shortcut over a zone border, no key |
| Detector room | ceiling smoke detector, red LED blinking, seen through the arch | stepping 1.5 m inside | the quick way through |
| Electrical room | "ELECTRICAL ROOM — AUTHORIZED PERSONNEL ONLY", transformer hum | stepping 1.5 m inside | the zone key, from tier 3 |
| Glass floor (`Loud`) | glass across the first 1.2 m of the doorway | stepping past the strip | the shorter route |
| Paging room (optional) | wall handset, speaker hiss | stepping 1.5 m inside | a key or desk |

---|---|---|
| Window (all tall zones) | glass broken | the only way into a tall zone; fast |
| Alarm door: push bar reading "EMERGENCY EXIT ONLY — ALARM WILL SOUND" | opening it | a shortcut across a zone border, no key needed |
| Ringing phone (Office) | entering the room. The phone rings every 3 s (+8 each ring) until E picks it up | the room's key or desk; pick it up to silence it |
| Smoke-detector room (red LED blinking, visible from the door) | entering it | a short cut through |
| Electrical room ("AUTHORIZED PERSONNEL ONLY", transformer hum) | entering it | the zone key at higher tiers |

---

## 5. Hearing on the map (the Relay's own ears)

This applies while the Relay is on the map (Hunt, Search, Patrol, Listen).

- **Propagation.** Shortest path over the cell graph from the noise's cell:
  - 3 m per cell;
  - open / arch / open door +0;
  - Ajar door +4 m (door state machine);
  - shut door +9 m;
  - intact window +9 m;
  - walls block.
- **Cost.** A Dijkstra in whole metres reusing the hunter's BFS scratch, at most about 300–700 cells (glass at tier 5 covers the 5 × 5 chunks). Sprint steps arrive every 0.3 s, so the field is cached, **rooted at the player's cell** and refreshed only when the player changes cell (关卡设计). Sprint noise starts at the player anyway, and the same field gives the warning distances (§7). The Relay's cell is read from it each frame. This matters on WebGL, which is CPU-bound. Door and glass noises come from the door or window; they use a one-off field from that cell.
- **Loudness**, in metres of travel (SP): sprint step 15, door 12, slam 20, glass 60. Multiplied by the tier's `hearing` (1.0 → 1.6). The base `hearing` becomes 1.0 instead of today's 1.4.
- **Heard area.** A sprint step is heard over a median of **30 cells** (p90 42), instead of today's 465. Glass is heard over about 430 cells.
- **Estimate.** The target is a random cell within k cells of the source, where k grows with the share of the hearing radius used (up to 2 cells, about 6 m). Far sounds are vague. A second noise within 4 s replaces the estimate, with error based on its own distance.
- **The head turns** to the estimate during Listen and Search (`ListenPoint`, unchanged).

---

## 6. Sight: seen, then chased

| Rule | Today | Proposed (SP) |
|---|---|---|
| Field | 360° | ±70° cone round the rig's head direction (the `SetListenTarget` clamp) while calm, hunting or searching; 360° in chase |
| Range | 12 m | 12 m (tier ×1.0–1.15) |
| Touch | — | 360° within 2.0 m ("it feels you") |
| Reaction | 0 s | a **spotting meter** fills in `T(d) = 0.25 + 0.035·d` s (12 m: 0.67 s; 6 m: 0.46 s; 3 m: 0.36 s) and drains at 1/s out of sight |
| Light | no term | still no term: **dark is never cover** (LD R13) |

**While the meter fills,** the head turns toward you (`SetListenTarget`) and nothing else happens. That is the "almost seen" beat: about half a second to break line of sight.

**When it fills,** warning stage 3 fires:
- `TargetAcquired(pos)` is raised and the lock-on cue plays (§7.3);
- the Relay stays at walking pace and squares up to you during the cue (`lockOnSeconds`, 0.6 s SP);
- chase speed begins when the cue ends.

From the first sight line to chase speed takes about 0.9–1.3 s.

**In chase** sight is 360° and the cue doesn't repeat. If it loses you and later sees you again within the same encounter, a short version of the cue plays.

New read-only property: `Spotting` (0–1), for the rig and the sound layer.

---

## 7. Three warnings

Red's staging. Distances are **walking distance** from the Relay's cell to the player's cell, read from a path field cached at the player's cell and refreshed when the player changes cell (关卡设计's suggestion; the same field serves sprint hearing). The field is reused, never recomputed per frame.

Nothing ever changes at the Relay's own position. All three warnings are about **you**: your room, your ears, your being seen.

| Stage | Fires when (SP) | What you get | Off when |
|---|---|---|---|
| 0 | Away, or farther than 36 m | nothing; every lamp keeps its own temperament | — |
| **1 · Lights** | Relay on the map and ≤ 30 m of walking (10 cells) | The lamps of **your room** flicker together in irregular bursts | > 36 m (hysteresis), or it withdraws |
| **2 · Steps** | ≤ 15 m of walking (5 cells) | Its footsteps become audible: muffled through walls, clear in line. Stage 1 keeps going | > 18 m |
| **3 · Lock-on** | The spotting meter fills (§6) | One clear, quiet lock-on cue (0.6 s); its head squares up to you; the chase begins when the cue ends. Your room's flicker stops: it has found you | the encounter ends |

### 7.1 Stage 1: your room's lamps

- **Your room** (关卡设计's definition):
  1. If you stand in an intact carved room or module room (the topmost in `MapChunk.rooms`), it is all of that room's cells.
  2. Otherwise (corridor, maze cell, cut room) it is a BFS from your cell over same-zone cells joined by **Open** edges only, depth ≤ 2 and at most 9 cells. Arches and doors count as walls, so the burst stops at the doorway and never leaks next door.
  3. The stream start rooms are excluded: they have no map lamps.
  4. The set is recomputed only when you change cell.
- **The burst** (new preset `LampFx.Warn`):
  - every lamp in the set dips together, with a deterministic ±40 ms jitter per lamp from its cell hash;
  - 2–4 dips over 0.8–1.4 s, multiplier 0.3–0.65, attack 0.08 s, release 0.2 s, dips ≥ 0.34 s apart.
- **Irregular, and closer means more:** the gap between bursts is random. It runs 5–8 s at 30 m and shrinks linearly to 2–3 s at 15 m.
- **How it reads against ambient lamps:** a failing lamp fails alone and keeps its own rhythm. In a warning burst the whole room, steady lamps included, stutters together, and the bursts gather pace. Value and timing only, never hue (hunter research §3.3).
- **Sound:** each dip raises `LampDipped(cell, pos)`, so the fixtures buzz or tick with the light (声音设计).
- **All clear:** when it is beyond 36 m or gone, the bursts stop and the room stays steady.

### 7.2 Stage 2: its steps

- Today the Relay's steps play at any distance, attenuated in 3D. Under staging, the Relay sound layer gates its steps on `WarnStage ≥ 2`. Within that, the existing wall occlusion (`FrontRoomsRelaySound`: 1 wall = 0.55, 2+ = 0.85) gives the **muffled** read through walls and the clear read in line.
- The presence drone, which today plays within 30 m, should follow the stages too: silent at stage 0, faint at 1, present at 2. The sound chat decides.

### 7.3 Stage 3: the lock-on cue

Red's terms: clear and recognisable, never jarring, never immersion-breaking.
- **Recognisable:** one signature, always the same, used for nothing else. Candidate: the relay's pull-in "clack" followed by a low two-note figure from the motif.
- **Not jarring:** no stinger, no volume spike, no frequency sweep. It sits just above the room tone and the Relay's own steps.
- **Diegetic in EGRESS:** the panel locking the alarm to your zone (narrative chat to supply the exact reading and a 1990 reference).
- **Timing:** `TargetAcquired(pos)` at the meter's fill. The cue lasts `lockOnSeconds` 0.6 s, then CHASE. After a lost sight line, a re-acquisition in the same encounter plays a short version.
- **HUD:** nothing (Red: every Relay state stays off the HUD).

### 7.4 Safety and accessibility rules (binding; also cover the LD chase wave)

- No lamp changes level more than **3 times per second**. No full-field flash.
- **Reduce Flashing / Reduce Motion** is one setting shared with the wallpaper print. When it is on:
  - a warning burst becomes a single slow dim to 0.6 over 0.6 s and back;
  - every attack and release is ≥ 0.5 s;
  - the chase wave becomes a static sag.
- The warnings are honest: stage 1 never fires without the Relay within 30 m of walking, and never fires at all while it is Away.

### 7.4b Lamp override interface v1

Agreed on 2026-10-03 by this chat, the wallpaper/phosphor chat (动画和动态图形模型技术) and 关卡设计, which builds it in `FrontRoomsMapWorld`. It is folded into both `TickFixtures` and `TickFixturesNear`, and is bit-identical when idle.
- `LampLevel(cell)` and `LampBaseLevel(cell)`: the logical level only, never read back from the Light.
- `LampModeOf(cell)`: pure, so it is valid for unbuilt cells too.
- `SetLampMode(cell, mode)`: persistent; survives a chunk drop.
- `SetLampOverride(cell, LampFx, multiplier, hold, env?)` and `RemoveLampOverride`.
  - `LampFx { Dip, Sag, Warn }`, with a per-kind envelope table.
  - The Relay-centred `Omen`, `Herald`, `Restrike` and `SetLampField` were dropped after Red's staging.
- **Stacking:** effective = base × MIN of all active multipliers.
- **Events:**
  - `FixtureChanged(cell, level)` on crossings of 0.15 / 0.55 / 0.8;
  - `LampDipped(cell, pos)`.
- **Hunter side:**
  - `WarnStage` (0–3) and `WarnStageChanged(int)`;
  - `PathDistanceToPlayer`;
  - `TargetAcquired(Vector3)`.

### 7.5 With the phosphor ink and the moving print

- **Lamps** = how close it is to *you*.
- **Print** (Relay wake reprint) = where it just walked.
- **Ink** = where to go.

A stage-1 burst briefly drops your cell below the ink's 0.55 gate, so the paper next to you gasps. The wallpaper chat adopts this as an intended beat: "when the lights flicker around you, the walls point". It is local to you, so it is not a position readout. The chase wave stays the LD's, on CHASE only.

---

## 8. Leaving

### 8.1 Withdraw

- A Search that runs out (`searchMaxSeconds`) with no contact ends in **Withdraw**. From tier 3 it first patrols for `patrolSeconds`.
- It walks at hunt speed to a Relay entry far from the player (preferring one it can reach without a door), out of sight, or to any unseen cell when there is no entry. It leaves the map there.
- As it passes 36 m of walking, your room's lamps stop flickering: the all-clear.
- Attention resets to 20 and grace starts.
- Sound: a release "drop-out" clunk where it leaves (new event `Withdrew`).

### 8.2 Handoff (replaces the leash teleport)

- During INVESTIGATE, when the new estimate is > 20 cells of walking from it, it **hands off**:
  - it leaves where it stands, out of the player's sight;
  - it arrives at an entry 10–16 cells from the estimate, unseen by the player, after the arrive delay.
- Never during CHASE or BREAKDOOR.
- This is the name made literal: a fresh hound placed along the line (hunter research §6).

---

## 9. Level design (关卡设计)

Full chapter: `research/relay_pursuit/20_level_design.md` (written by the 关卡设计 chat). Key points from its reply, 2026-10-03, measured on 20 seeds and 46k cells:

**The geometry already allows escape. The problem is the AI.**

| Measure | Value |
|---|---|
| Cells on dead-end branches | 7 % (Standard 10 %, Low 3 %, Tall 6 %) |
| Independent loops inside a zone | median 16 (p10 6; 1 % of zones have none) |
| Exits per zone | median 22 passable border edges, 7 of them doors |
| Whole map, per 100 cells | 39 loops, 6.2 doors, 3 windows |

No new loops are needed. What is needed is to make **shutting a door** a real escape verb:
- single-acting doors (Red's decision);
- the Relay's break time;
- the Ajar state from the door state machine. For the Relay an Ajar door counts as open: it pushes through in +0.4 s, and the push is audible.

**Trigger rooms are a room-level field, not a marker.**
- `ModuleTrigger { None, Alarm, Loud }` (append-only), with noise radius, one-shot or cooldown, and an arming delay. An optional device marker places the phone or pull station.
- MapWorld registers trigger rectangles per built chunk. It checks only the current chunk when the player changes cell, fires once per room instance, and raises `RoomTriggered(kind, source, tag)`; the game forwards it to `relay.Summon`.
- A deterministic `triggerChance` pass (new MapHash salt, by tier and height) can make generated rooms into triggers too.
- `Loud` (glass-strewn floor) is one flag per cell. `Alarm` needs a wall spot without an opening for its device.
- The visual chat must supply the readable props (ringing phone, pull station, copier, glass floor). Without them, "readable before entry" fails.

**Placement rules:**
- **Trigger rooms:**
  - one per 2–3 zones;
  - ≥ 15 cells from the start door, none in the first zone;
  - never in a dead-end branch, unless the branch has a door you can shut (a risk-for-reward choice);
  - the device in sight from the doorway, outside the entrance passage.
- **Relay entries:**
  - ≥ 2 per zone;
  - preferably at dead-end branches and corridor ends (vents);
  - ≥ 9 cells from any trigger room, so the warnings have time to build as it walks in.
  - Only two sample modules have entries today, so the generator should add them in dead ends automatically.

**Readable before entry, enforced rather than assumed.** This confirms the narrative chat's TO CONFIRM, with a correction. Arches are 1.1–1.8 m wide and 2.2 m high, so sight through them is narrow.
1. A trigger room needs at least one arch or open entrance from its own zone. A room reached only through another zone's doors is never a trigger: a shut door is opaque.
2. The device must be visible from 2 m outside such an entrance, at 1.6 m eye height. Module Validate gets a 2D ray check, and generated triggers place devices only on walls an entrance can see.
3. Loud floors show their glass in the first 1.2 m inside each opening, as a decal with no collider.
4. The trigger arms only ≥ 1.5 m inside, past that strip. Looking in, or stepping into the doorway, is safe.

**Office cover.** Today's 1.57 m panels don't block sight. The 1.65 m panel (visual chat) would.

**Effort (关卡设计 estimate):**

| Piece | Days |
|---|---|
| Loop and states | 2–3 |
| Attention and noise kinds | 1.5 |
| Trigger rooms | 2.5 + props |
| Lamp override | 1 |
| Tier by explored cells | 0.5 |
| Auto entries | 0.5 |
| Tests | 1.5 |

Total about **9–11 working days**, after the door state machine (single-acting doors, Locked → Unlocking → Ajar → Open), once Red approves.

---

## 10. Narrative (Design the narrative of the phosphor wallpaper print)

Full chapter: `research/relay_pursuit/30_narrative.md` (written by the narrative chat). **Red chose EGRESS (2026-10-03):** the Relay is the relay a fire-alarm panel pulls in. Its states match the panel's sequence one for one:

| Loop | Fire alarm (EGRESS) |
|---|---|
| Away | Panel on standby |
| Called | An initiating device trips: pull station, smoke detector, door alarm, glass-break detector |
| Arrive | The relay pulls in. Nothing changes at its position |
| Investigate | Alarm verification (the panel re-checks the device before full alarm) |
| Chase | Full alarm |
| Search | Floor sweep, room by room |
| Withdraw | Reset to normal |
| Caught | Accounted for. Optional Caught line "OCCUPANT ACCOUNTED FOR", not yet approved by Red |

**The staged warning in EGRESS** (chapter §5):

| Stage | Reading |
|---|---|
| 1 · lights | **Pre-alarm:** the panel moves your compartment to emergency power and pre-checks it before verification. "Something is in your zone"; not yet the alarm |
| 2 · steps | The sweep has reached your floor |
| 3 · lock-on | Verification: the full alarm locks to your zone. Then the chase, and the LD chase wave on CHASE only |

- In a stage-1 burst the ink gasps GROUND next to you: the annunciator lighting *your* zone. This needs the burst to be a smooth sag under 3 Hz (§7.4), because LD R15 zeroes ink in strobe cells.
- **Lock-on cue directions for 声音设计** (all marked 待核, unverified):
  - preferred: the low "thunk" of a magnetic door hold-open releasing on alarm. The building just acted, and it is a door sound;
  - a single strike of a hospital coded fire chime;
  - a two-tone paging pre-chime;
  - a short steady supervisory/trouble buzzer tone;
  - the relay pull-in can sit under any of these (`SOUND_FOLEY_MOTIF_RESEARCH.md` §4.3–4.4).

B (SUB-PATTERN), C (BLAZES) and D (DRAG LINE) remain alternates; see the chapter. Hunting terms marked 待核 (unverified) there are not used here.

Rules the fiction adds:
- Every trigger room is readable before entry from one 1990 object or sound. The ink never marks one, or it would become radar.
- Dark is never cover: the lamps dim because it draws power.
- The building-wide alarm is silent.
  - A device's own local sound (a door horn chirp, a phone ring) is the player's feedback for what they did.
  - Whether it plays is the sound chat's call (open question Q6).

---

## 11. Pacing and tiers

| Tier | Call threshold | Decay /s | Grace s | Arrive delay s | Patrol s | Hearing × | Chase m/s | Spot time at 12 m |
|---|---|---|---|---|---|---|---|---|
| 1 | 60 | 2.0 | 40 | 3.0 | 0 | 1.0 | 4.2 | 0.67 s |
| 2 | 55 | 1.8 | 35 | 2.75 | 0 | 1.15 | 4.5 | 0.60 s |
| 3 | 50 | 1.6 | 30 | 2.5 | 20 | 1.3 | 4.8 | 0.55 s |
| 4 | 45 | 1.4 | 25 | 2.25 | 40 | 1.45 | 5.1 | 0.50 s |
| 5 | 40 | 1.2 | 20 | 2.0 | 60 | 1.6 | 5.4 | 0.45 s |

Tier rules (关卡设计's measurements and proposal):
- **The tier counts new cells explored: one tier per 150 new cells.** Zones are small (median about 63 cells), so counting zones escalates too fast.
- **Stalling no longer raises the tier.** It shortens grace instead: it comes back sooner, not stronger (open question Q3).
- The tier's Relay multipliers (chase, door-break time, search time) and lamp odds follow DP08 as today.

One tier-1 cycle, roughly:
- calm 45–90 s;
- arrive delay 3 s;
- the walk in (10–16 cells at 2.6 m/s, about 12–18 s; stage 1 starts as it comes within 30 m);
- investigate and search 15–25 s, or a lock-on and a chase of 5–15 s;
- withdraw 8–12 s;
- grace 40 s.

Warning distances stay fixed across tiers: the tiers make the Relay better, never the warnings shorter. The player who makes noise and then moves on is never caught. The player who keeps making noise is.

---

## 12. Implementation map (for the owners; nothing is built)

| Piece | Owner | Contract |
|---|---|---|
| Attention, grace, calls, re-dispatch: `Disturb(kind, point)`, `Summon(source)` in the hunter; tier columns `attentionGain`, grace, arrive delay, patrol | map chat | new tuning fields must go into `CopyFrom` (relayTuning is rebuilt every frame) |
| `HunterState.Away` (7), `Arrive` (8), `Withdraw` (9) | map chat | **append-only**; ping 声音 before landing; `Released` = not Dormant and not Away |
| `FrontRoomsMapHunter`: path field cached at the player's cell (hearing + warnings), cell-quantised estimate error, ±70° cone + `Spotting`, lock-on, Withdraw, handoff | map chat | about 350–450 lines + 200 lines of tests; door-rule tests need a facing |
| Staged warnings: `WarnStage` (0–3), `WarnStageChanged(int)`, `PathDistanceToPlayer`, `TargetAcquired(Vector3)`, `lockOnSeconds`; your-room set (§7.1) | map chat | stage thresholds 30 / 15 m with hysteresis 36 / 18 m (SP) |
| Lamp override v1 (shared with the phosphor ink): `SetLampOverride`, `LampFx { Dip, Sag, Warn }`, MIN stacking, `LampLevel`, `SetLampMode`, `FixtureChanged`, `LampDipped`; one `f.level *= f.mod` in both TickFixtures branches | map chat (logic), **游戏视觉** (look of the Warn burst) | bit-identical with no override, so the WebGL fixture tests hold |
| Trigger rooms: `ModuleTrigger` room field, device marker, `RoomTriggered` event, `triggerChance` pass, Level Designer type picker | map chat; props from 游戏视觉 | §9 |
| Sound events: `WarnStageChanged`, `LampDipped`, `TargetAcquired`, `Arrived`, `Withdrew`, `RoomTriggered`; `Spotting` property | map chat → **声音设计** | AUDIO_CONTRACT: events only, no new AudioSources. 声音设计 was not running on 2026-10-03, so this list is its hand-off |
| Sounds: fixture buzz/tick on warning dips; Relay steps gated to stage ≥ 2 (occlusion = muffled); presence drone by stage; **the lock-on cue**; device sounds (door-alarm chirp, phone ring) | 声音设计 | new FMOD events or parameters |
| HUD: every Relay state off by default (assist only) | map chat | Red's decision, landed for distance/state on 2026-10-03; CHASE and BREAKING DOOR text too |
| **Step 0: a baseline before any change.** A seeded route RNG and an **evading bot** (hides, shuts doors, sprints when chased), plus **quiet** (never sprints) and **noisy** modes. Report: state shares, time to first call, calls per minute with cause, chases per encounter, warning stage before each chase | map chat (offered; waits for Red) | `FrontRoomsMainScenePlaytest` report; run before and after |

---

## 13. Acceptance (autopilot + playtest)

- **Quiet walker, tier 1, 5 min:** at most 1 call, and only from an instant trigger the route took.
- **Noisy walker:** first call within 20 s of the first full sprint.
- Every CHASE is preceded by stage 1 or 2 for ≥ 3 s, and always by the lock-on cue.
- Stage 1 never fires while the Relay is Away or farther than 36 m.
- Calm share ≥ 60 % at tier 1.
- Nav test 60/60 and map 100/100 unchanged; fps budget unchanged (a warning burst touches ≤ 20 fixtures).
- **Playtest, 10 players:**
  - ≥ 8 name why it came;
  - ≥ 7 read a room burst as "it is near" without being told;
  - ≥ 8 recognise the lock-on cue on its second play, and none call it a jump scare.

---

## 14. Open questions for Red

**Answered on 2026-10-03:**
- EGRESS is the fiction.
- The chase wave fires on CHASE only.
- All Relay state stays off the HUD.
- The warning is staged and centred on the player. That replaces the old Q7 about an ink halo round the Relay.

**Still open:**
1. **Calm share:** is about 60 % calm at tier 1 the right amount of room?
2. **Attention vs. pure triggers:** keep the panel meter (sprints and doors add up), or let only instant triggers call it?
3. **Stall rule:** stalling shortens grace instead of raising the tier, and tiers count 150 new cells. Agreed?
4. **Spotting time:** about 0.5 s of "almost seen" plus the 0.6 s lock-on cue before the chase. Too generous?
5. **Trigger set:** which of the alarm door, phone, smoke detector and electrical room go in first?
6. **Device sounds:** with a silent building alarm, may a device's own local sound (door-alarm chirp, phone ring) still play?
7. **Warning distances:** 30 m (lights) and 15 m (steps) of walking. Fixed for every tier?
8. **Baseline first:** may the map chat add the seeded evading bot (no gameplay change) to measure today's pursuit before anything changes?
