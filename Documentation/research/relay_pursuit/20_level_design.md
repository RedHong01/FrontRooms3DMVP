# Map and Relay: feasibility and level design

*Map/level chat (关卡设计), 2026-10-03. This file is for `RELAY_PURSUIT_REDESIGN.md` §9. The code facts were checked against main after Level Designer P4 landed. The map numbers come from the generator itself: 20 seeds × 8 × 8 chunks, 46,080 inner cells, compiled outside Unity.*

## 1. What the map already gives

| Measure (Level0 profile, 20 seeds) | Value |
|---|---|
| Cells on dead-end branches (outside the 2-core) | 7.3% (Standard 10.3%, Low 3.1%, Tall 5.6%) |
| Cells with a single exit | 4.4% |
| Independent loops per 100 cells | 39 |
| Zone size (whole zones) | median 63 cells (p10 48, p90 78) |
| Loops inside a zone | median 16 (p10 6); only 1% of zones have none |
| Passable border edges per zone | median 22, of which 7 are doors |
| Doors / windows per 100 cells | 6.2 / 3.0 |

**Reading.** Escape geometry is not what is missing. Every zone has many loops and many ways out. The player has no room to explore today because of the Relay (omniscient hearing, instant 360° sight, no away phase), not the maze. The level-side levers that matter are doors as tools (single-acting doors with stops, the Relay's break time, Ajar), sound attenuation through them, and where triggers and entries sit.

## 2. Costs in the map and Relay code

Estimates assume one implementer working on the current code. HunterState stays append-only.

| Item | Where | Size | Notes |
|---|---|---|---|
| States Away=7, Arrive=8, Withdraw=9 | Hunter, tuning | ~300 lines, 2–3 days | The herald is the first seconds of Arrive. `Released` changes to "not Dormant and not Away". The HUD, rig visibility, autopilot PASS (it requires Released) and AUDIO_CONTRACT all read it, so update them in the same change and ping the sound chat first. TickBreak resumes into Arrive, Withdraw or Wander, not only Chase or Hunt. |
| Arrive / Withdraw | Hunter + `RelayEntries` | in the above | Reuses P4's Arrive filters (body fits, unseen, behind preferred) and `Arrived(pos, tag)`. Arrive picks an entry 10–16 cells from the source. Withdraw walks to an entry far from the player, going through no doors if it can. |
| Path-distance hearing | Hunter | ~80 lines | Dijkstra from the Relay's cell in integer metres: cell 3, shut door +9, Ajar +4, open door 0, intact glass +9, no wall leak. Cache it per Relay cell, because sprint fires every 0.3 s. A recompute visits about 300–700 cells, the same order as one existing chase Plan; on WebGL, which is CPU-bound, the cache is required. |
| Error radius | Hunter | ~20 lines | k = floor(errorCells × cost / radius). It searches a random cell within k of the source, quantised to cells. |
| View cone ±70° + 0.3–0.6 s notice | Hunter + rig | ~40 lines | The cone follows the rig's head yaw (same clamp as SetListenTarget). Notice time grows with distance. Tests must give the player a facing or turn the cone off; the door-rule test shows the player for only 0.6 s. |
| Attention (`Disturb(kind, point)`, `Summon(source)`) | Hunter, tuning, tier row | ~150 lines, 1.5 days | While Away, Disturb adds a flat global gain. While the Relay is on the map, it falls off with path distance. Summon beyond 30 cells calls Arrive first. A separate `attentionGain` tier column keeps it from compounding with `hearing`. Every new field goes into `CopyFrom`, because relayTuning is rebuilt every frame and a missing field silently reverts. |
| Trigger rooms | RoomModuleData, stamp, generator, MapWorld, game, Level Designer | ~2.5 days + props | See §3. Needs readable props from the visual chat. |
| Lamp override layer (Omen / Dip / Sag) | MapWorld | ~1 day | Per-chunk cell → fixture index. `SetLampOverride(cell, kind, strength, seconds)`, `LampLevel` / `LampBaseLevel(cell)`, `FixtureChanged`. One `f.level *= f.mod` in both TickFixtures branches (desktop and WebGL near-only). With no override the output is bit-identical, so the WebGL fixture test still holds. `CopyPathAhead(list, max)` on the hunter lets the omen run ahead without touching the RNG. Look numbers (sag curve) belong to the visual chat; reach numbers (radius and cells ahead per state, per tier) to the map. Photosensitivity: no lamp changes more than 3 times a second; the omen is a smooth sag plus a sound rhythm. |
| Tier by explored cells | Game, profile | ~0.5 day | One tier per 150 newly explored cells. A stall no longer raises the tier; it shortens the Away cooldown instead. The rule lives in `FrontRoomsTierRules` and `RaiseTier`. The Relay multipliers per tier stay as they are. |
| Dead-end entries | Generator, MapWorld | ~0.5 day | Auto Relay entries at dead-end tips (degree-1 cells), see §4. |
| Tests | Interaction, nav, designer | ~1.5 days | States and transitions, path hearing with door costs, the cone, attention threshold, Summon, triggers fire once, lamp overrides bit-identical when idle. |

Total: about 9–11 working days after the door state machine (single-acting doors, Locked → Unlocking → Ajar → Open), which comes first. Ajar for the Relay means "open, with a 0.4 s shove that makes a sound".

## 3. Trigger rooms

**Data.** A room-level field on the module, `ModuleTrigger { None, Alarm, Loud }` (append-only), with a noise radius, once or cooldown, and an arm delay. A **device** marker is the point the alarm comes from (a phone or a fire-alarm pull). Point markers stay points: a trigger is an area with state, tested at runtime, so it is not a new marker kind.

**Runtime.** MapWorld registers each built trigger room as an inset cell rectangle plus its device point. On a player cell change it tests only the current chunk and fires `RoomTriggered(kind, source, tag)` once per room instance. The id is (chunk, revision, room), so it survives drop and rebuild. The game forwards it to `relay.Summon` once the Relay has been released.

**Generated rooms.** A deterministic `triggerChance` pass runs after PlaceModules, with its own MapHash salt. It can be tiered.
- Loud (glass on the floor) is a per-cell flag. It is cheap.
- Alarm needs a device on a wall slot with no opening, placed before Dress. That costs about a day more.

**Distribution** (adopted):
- one trigger room per 2–3 zones;
- at least 15 cells from the start door, and none in the first zone;
- never on a dead-end branch, unless the branch has a door the player can shut;
- at least 9 cells from any Relay entry, so the herald has room to travel.

**Readable before entering: confirming the narrative chat's TO CONFIRM, with a correction.** Inside a zone, rooms open through arches (1.1–1.8 m wide, 2.2 m high) and open edges. Sight through an arch is real, but it is narrow. A device on the wall that holds the opening, or beside it, cannot be seen from outside. The rule has to be enforced, not assumed:
1. A trigger room needs at least one arch or open entrance from its own zone. A room reached only through doors from another zone is never a trigger. A shut door is opaque, and reading the room at the moment the door swings is too late.
2. The device must be visible from 2 m outside at least one such entrance, at 1.6 m eye height. Module Validate gets a 2D ray check against walls, inner walls and collider props. The generated-room pass places devices only on walls it can see from an entrance.
3. Loud floors show their glass in the first 1.2 m inside each opening (the keep-clear strip), as a decal with no collider. The floor is visible from the doorway.
4. The trigger arms only past that strip, at least 1.5 m inside the room, so looking in or stepping into the doorway is safe.

## 4. Relay entries

- **Count:** at least 2 per zone footprint. Today only two sample modules carry entries ("vent", "doorway"), and Arrive falls back to unmarked cells.
- **Auto entries:** generate entries at dead-end tips, which are 4.4% of cells and 10% of Standard cells. Use tag `"vent"` in Low and Standard zones and `"doorway"` at Tall hall ends. A dead end is where an arrival or exit reads as natural, and where the player rarely stands.
- **Spacing:** at least 9 cells from trigger rooms. Withdraw prefers the entry farthest from the player and reachable without doors.
- **Choice order:** P4 already prefers entries (behind the player, then any), so Arrive and Withdraw reuse it unchanged.

## 5. Tier counting

Zones are small (median 63 cells), and zones of the same height join through arches. The autopilot crossed 9 zones in 75 s and reached tier 3 by 60–74 s. "Every 4 zones" rises too fast, and the 120 s stall rule punishes careful play.
- **Adopted:** one tier per 150 newly explored cells. At walking pace with backtracking, that is roughly one tier per 2–3 zones of real exploration. The tier stays a pure pressure scale.
- **The stall** shortens the Away cooldown ("it comes back sooner"); it does not make the Relay stronger.

## 6. Merges with P4, the phosphor ink and the door work

- **P4:** RelayEntry markers, `Arrived`, `RelayEntries()` and the tier table (live-editable in Play) carry over unchanged. The HUD Relay readout is already an assist, off by default (Red, 2026-10-03).
- **Phosphor ink:** one lamp override layer serves the omen, the ink's dips and kills, and the chase wave (Q3: the wave fires on Chase only; Hunt and Search show only the local omen, and omen cells show GROUND ink without committing messages). Interface: map chat. Look: visual chat.
- **Doors:** single-acting with stops, a fixed swing side per edge (hashed, stable across rebuilds), pulls with a short step-back, and the Relay breaking toward the swing side. Path hearing costs shut and Ajar doors, so shutting a door becomes an escape tool you can hear.

## 7. Evidence

The autopilot is a system log, not a player model. It never evades, never closes doors, and sprints only once (16–22 s), and its route RNG is unseeded. The first measurement step of the redesign is a seeded fleeing bot (closes doors, breaks line of sight, sprints when seen), run as a baseline before and after.
