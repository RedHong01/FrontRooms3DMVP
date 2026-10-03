# Narrative: the alarm that sends it

Status: proposal, revision 2, 2026-10-03. Written by the narrative chat ("Design the narrative of the phosphor wallpaper print") for the Relay pursuit redesign.
- The main document is `Documentation/RELAY_PURSUIT_REDESIGN.md`, owned by the systems chat (系统设计, formerly 怪物追捕机制设计审计).
- This file is fiction only: no state, timing or code change.
- The fiction follows EGRESS, which **Red chose** for the glow ink on 2026-10-03 (`research/wallpaper_motion/30_narrative_phosphor.md` §4). B/C/D stay as alternates in §3.
- **Revision 2 follows Red's staged warning.** The lamps no longer dim where the Relay is: the player's own room flickers, then footsteps are heard, then a lock-on cue sounds (§5). The old herald brown-out around the Relay is withdrawn.

## 1. Premise (EGRESS)

The building has a fire-alarm system. The Relay is the stage of it that trips: the thing the building sends to clear a zone.
- When it is absent, it is not hiding; the panel is on standby.
- It comes when a device in a zone trips.
- It leaves when the zone is reset.

The glow ink is the same building's exit plan, so the two systems belong together:
- the plan shows occupants the way out;
- the alarm sends something to sweep them out.

## 2. State ↔ fiction (EGRESS)

| State | Fire-alarm reading | What the player sees and hears |
|---|---|---|
| AWAY | Standby, normal condition | Lamps keep their own temperaments (steady, stutter, failing, dead). No herald |
| CALLED | An initiating device trips in a zone: breaking glass, an alarmed door, a detector. Accumulated noise = the panel counting confirmations | Nothing yet, or the annunciator: if EAR is enabled, the GROUND glow round the source swells (LD §4, P2) |
| ARRIVE | The alarm relay pulls in somewhere out of sight, and the responder enters the floor | Nothing at its position. The player learns only through the staged warning (§5) |
| INVESTIGATE | Alarm verification: the panel re-checks the zone before full alarm | It walks the tripped zone and listens, with error. Stage 1 and stage 2 warnings when it is near (§5) |
| CHASE | Full alarm, locked to your compartment | Stage 3 lock-on cue, then LD's chase wave from its cell (Chase only, Q3); the ink switches to ALARM ROUTE (doors you can shut) |
| SEARCH | Room-by-room sweep, as a fire warden checks every room | It searches nearby rooms, then gives up |
| WITHDRAW | Reset / restoral | Your room's lamps settle back to their own temperaments; it leaves the way it came |
| Caught | The occupant is accounted for | Optional Caught line: `OCCUPANT ACCOUNTED FOR` (map chat's HUD) |

What EGRESS fixes is the Relay's **role** (the alarm's responder), not its body. The best match among the open looks is hunter direction B "Night Shift" (the electrician with a lens face, `research/hunter/10` §4), but the fiction works with all four.

## 3. Alternates

**B SUB-PATTERN:** it is what puts people into the paper.

| State | Reading |
|---|---|
| AWAY | It stays behind the paper, out of reach of our side |
| CALLED | The pattern is wounded: torn paper, broken glass |
| Near (stage 1–2) | The kept in your room's paper press forward in fear: your lamps falter and the ground glow stirs beside you |
| WITHDRAW | Back behind the paper once it has fed |
| Caught | You join the sub-pattern |

**C BLAZES:** it is "IT" in the wanderers' notes. There is no explanation, only rules they learned.

| State | Reading |
|---|---|
| AWAY | `IT LEAVES WHEN THE LIGHTS COME BACK` |
| CALLED | `IT COMES FOR GLASS` |
| Near (stage 1–2) | `WHEN YOUR LIGHTS GO IT'S CLOSE` · `THEN YOU HEAR IT WALK` |
| WITHDRAW | The lights come back |
| Caught | A new set of initials, maybe |

**D DRAG LINE:** it is the hunt's hound. This fixes its role, not its look.

| State | Reading |
|---|---|
| AWAY | Kennelled |
| CALLED | The huntsman puts hounds into cover (*draw a covert*, to verify); glass is the cry of the find (*view halloo*, to verify) |
| Near (stage 1–2) | The hunt drawing your covert; then the hound on the line, heard before seen |
| SEARCH | A **check**, after losing the line (verified) |
| WITHDRAW | Taken home (*blowing for home*, to verify) |
| Caught | A run ended |

## 4. Trigger rooms

**Rules:**
1. **Readable before entry.** Every trigger room has one 1990 object visible from outside it, or a sound heard before entry.
2. **The ink never marks a trigger room.** There is no new glyph, because that would turn the ink into radar.
3. **Inner-zone trigger rooms (TO CONFIRM with the level-design chat).** Doors and windows exist only on zone borders, so a trigger room inside a zone must be read through an arch or open-edge sightline.

| Trigger (EGRESS) | Read before entering | 1990 basis |
|---|---|---|
| Alarmed exit door | Push-bar door with `EMERGENCY EXIT ONLY — ALARM WILL SOUND` | Panic-bar door alarms (to verify) |
| Detector room | A ceiling smoke detector with a blinking red LED, visible from the doorway | Smoke detectors common by the 1980s (to verify) |
| Electrical room | `ELECTRICAL ROOM — AUTHORIZED PERSONNEL ONLY`, panelboards, transformer hum | The building's wiring |
| Paging room | A wall intercom/PA handset, speaker hiss | Office paging |
| Any window | The glass itself: breaking it trips glass-break detection | Acoustic glass-break detectors in 1980s security (to verify) |

**Alternates:**
- **B:**
  - a room with the wallpaper torn off in strips (Gilman's narrator tears the paper);
  - an older, yellower paper visible from the door;
  - a water-stained room (the 2002 founding photo shows water damage);
  - windows.
- **C:**
  - an abandoned wanderers' camp (sleeping bag, cans, dead flashlight);
  - a door frame covered in tallies;
  - a tin-can tripwire across a doorway: their own alarm, which calls it;
  - a copier room whose machine warms up and whirs as you enter;
  - a phone off the hook, beeping.
- **D:**
  - furniture-pile rooms (cover);
  - Office cubicle islands;
  - Tall halls (open country, in view the moment you enter);
  - windows.

## 5. Staged warning (EGRESS)

Red's design (systems doc): the lamps never dim where the Relay is. The warnings happen around **you**.

| Stage | Game | Fire-alarm reading |
|---|---|---|
| 1 | Within about 30 m of walking, your room's lamps flicker irregularly as a group | Pre-alarm: the panel moves your compartment to emergency power and tests it before verification. The building is saying "something is in your zone", not sounding the alarm |
| 2 | Within about 15 m, muffled footsteps, more muffled through walls | The sweep is on your floor: a warden checking rooms |
| 3 | It sees you: a clear, non-jarring cue of about 0.6 s, then Chase | Alarm verified. Full alarm locked to your compartment; LD's chase wave follows (Chase only) |

**The ink at stage 1.**
- The paper beside you gasps green: GROUND only, no message (LD R5). It is the annunciator lighting *your* zone, a local warning and not radar.
- It shows only if the flicker is a smooth sag under 3 Hz, because stutter cells force the ink to 0 (LD R15). That is the photosafety rule anyway.
- None of the three stages is a stealth rule. The dark of stage 1 hides no one (LD R13).

**Lock-on cue: period references for the sound chat (all 待核):**
- **Magnetic door-holder release.** Fire doors are held open by electromagnets and let go on alarm, with a soft, low clunk. This is the recommended base: it says "the building just acted" and ties the cue to doors.
- **A single strike of a coded fire-alarm chime.** Hospitals used chimes instead of bells.
- **A PA pre-announcement chime**, the two-tone sound before a page.
- **A panel's trouble or supervisory buzzer.** It is a short, steady piezo tone, not a bell.
- **Relay pull-in click.** It is already in the sound chat's motif (§4.3–4.4) and could sit under any of the above.

**The three layers** (each tells one thing only):
- **Your room's lamps** = it is near you.
- **The print** = where it just walked (Relay wake reprint, `wallpaper_motion/10_synthesis.md` §5).
- **The ink** = where to go.

## 6. Writing rules

1. **Dark is never cover (LD R13).** No line, sign or prop may say or imply that darkness hides you or it. Its sight has no light term. Your lamps flicker because the panel is testing your zone, not to hide anything.
2. **The staged warning is a warning, never a stealth rule.** All Relay state text is hidden from the HUD (assist toggle only), so these three stages are the player's only proximity tells. They stay local and honest.
3. **Silent alarm.** No bell. Sound is the sound chat's call; the relay click is optional (`SOUND_FOLEY_MOTIF_RESEARCH.md` §4.3–4.4).
4. **Period.** 1990 hardware, US English caps on signs, no real brands, printed dates ≤ 1990.
5. **The fiction lives in objects and signs.** The HUD never names the system.

## 7. Terms to verify (待核)

- **Fire alarm** (general knowledge, not yet sourced):
  - *initiating device* and *notification appliance*;
  - *alarm verification*, where a panel re-checks a detector before full alarm;
  - break-glass call points (UK) and glass-rod pull stations (US);
  - acoustic glass-break detectors in 1980s security;
  - panic-bar door alarms reading `ALARM WILL SOUND`, common by 1990;
  - smoke detectors common by the 1980s;
  - the fire-warden "sweep";
  - *pre-alarm*, *trouble* and *supervisory* signals, and whether 1990 panels had a pre-alarm stage;
  - magnetic door holders releasing on alarm;
  - coded chimes in hospitals;
  - PA pre-announcement chimes.
- **Hunting:** *draw a covert*, *view halloo*, hound *music* and *blowing for home* still need sources.
  - Verified: a **check** is when hounds lose the scent; the fox **goes to ground** (https://en.wikipedia.org/wiki/Fox_hunting).
  - Drag hunting, an artificially laid scent line: https://en.wikipedia.org/wiki/Drag_hunting.
- **Emergency-lighting tests:** monthly 30 s and annual 1.5 h under NFPA 101 §7.9.3, current edition. The 1990 wording is not verified (https://www.inspectpoint.com/resources/articles/emergency-lighting-and-exit-sign-testing-requirements).
