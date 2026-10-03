# 02 — Period hardware for the interactables kit (1985–1993 US office / store back rooms)

Status: DONE (2026-10-02). Research only. Nothing in the project or the Unity clone was changed.

Binding inputs, read first: `00_map_constraints.md` (this folder), `../office_and_film/22_era_lock.md`, `../interaction_audit/10_audit_report.md` §3–§4, and `../interaction_audit/02_glass_and_breakables.md` §5, §7–§8. The IP rules come from Figma file `0tCbAiVUlrPId3RWd9LRif`, slide HR03 "What the Backrooms teach" (node 2331:873; read as a screenshot) and section IR03 "Set in 1990" (2320:2106; read as metadata).

**How to read this.**
- Every dimension is given in inches as the trade states it, and in metres for the kit (Z up, metres).
- **[read]** means I read the page at the URL in §12.
- **[search]** means the claim came only from a search-engine summary because the page itself refused me (403) or would not parse. Treat it as UNVERIFIED.
- **ESTIMATE** means a designer number with no source behind it. Measure a real object before final modelling.
- **Modern catalogue, timeless form** means the source is a current product sheet for a design family that existed in 1990. The 1990 version is assumed to have the same dimensions. I flag this where it matters.

Who decides what:
- The locked-door type is decided in `05_locked_door_type.md`. §11 here is period input for that decision only.
- Door gap and stop construction belong to the RE8 / door-gap work. §2 and §5 give only the period facts it needs.

---

## 1. Decisions in one table

| Item | Recommendation for FrontRooms | Why (short) | Section |
|---|---|---|---|
| **Free door** (opens directly) | 1-3/4" flush **wood-veneer** door (the existing `Door_Veneer` look). **Passage-function lever** with no keyhole, in brass (US4 satin or US3 bright). No closer. Kick plate optional. | This is the project's own film still F09 (veneer door, brass lever) and IP canon (levers on veneer doors). A lever was the "accessible" choice on public doors before the ADA. "No keyhole" is a close-range cue that the door is free. | 3, 11 |
| **Locked door** (needs a key): period input to 05 | 1-3/4" flush **painted hollow-metal** door in a hollow-metal frame painted the same colour (putty). **Storeroom-function key-in-knob** lockset in US26D satin chrome, with a **knurled** knob and the keyway at the LockPoint (1.0 m). **Engraved room sign** on the wall at the latch side, 1.52 m to centre. Stainless kick plate. | Back-of-house rooms were steel doors with keyed storeroom locks. A knurled knob marked doors to hazardous rooms (UFAS 1984). The sign location is UFAS / ADAAG. Leaf colour, frame and sign read from 6–12 m; knob, keyway and knurl read from 0.5–3 m. | 3, 4, 11 |
| Knob or lever in 1990 | **Both existed.** Knobs still outsold levers about 80:20 at the start of the 1990s **[search]**. Levers were already the accessible standard (ANSI A117.1-1980, UFAS 1984). The ADA required them in new construction only for buildings first occupied after 26 Jan 1993. So a 1990 office plausibly has levers on public and office doors and knobs on service doors. | §3 | 3 |
| Lock height and backset | Keep the game's 1.0 m (real: 38" = 0.965 m to the centre of the lock) and its 0.08 m inset (real backset: 2-3/4" = 0.070 m). | Within about 3.5 cm and 1 cm of real; nobody will see the difference. | 2, 4 |
| Hardware projection | Knob 67 mm and commercial lever 64 mm from the door face. Both fit the map's ≤ 0.07 m per side. | §4 | 4 |
| Hinges | 3 × 4-1/2" × 4-1/2" (114 × 114 mm), 5-knuckle, full mortise, on the "5-10-equal" layout: in game, top 1.859–1.973, middle 1.056–1.171, bottom 0.254–0.368 m. | §5 | 5 |
| Kick plate | 0.050" (1.3 mm) satin stainless, 10" (0.254 m) high, door width less 2" on the push side (less 1-1/2" on the pull side). | §5 | 5 |
| Keys | A generic US 5- or 6-pin pin-tumbler key, about 55–60 mm long. Nickel silver for factory originals; brass for duplicates. Stamped "DO NOT DUPLICATE" plus a keyset/room code. **Use brass for the zone key** (it reads under yellow light, and a brass duplicate is period-true). | §8 | 8 |
| Key tags | Coloured plastic ID tag (zone colour) **or** a 1-1/4" (32 mm) metal-rim paper tag, either on a 1" split ring. | §8 | 8 |
| Key hosts | Wall key cabinet (numbered hooks), hook board, desk top, lock box. Hosted keys **stop spinning**. | §9 | 9 |
| Map window glass | **1/4" (6 mm) annealed float** in the hero window: legacy pre-code glass in an older building, which fits the era lock's second-hand window. It gives crack stages, daggers, teeth, re-breaking and floor glass. Tempered (dice) as a variant. Wired glass for fire-door lites (P2). | Matches Red's "staged fracture → falls → breaks again → stays on floor"; tempered glass does not crack in stages. | 6, 7 |
| Window frame | Hollow-metal borrowed-light frame (2" face, 5/8" stops) or the dark-bronze glazing of `Kit_InteriorWindow`. All of it stays outside the 1.4 × (0.35–2.0) opening. | §6 | 6 |

---

## 2. Doors: leaf, frame, edge, clearances

### 2.1 Leaves

| Property | Period value | Metres | Source |
|---|---|---|---|
| Commercial door thickness | 1-3/4" | 0.0445 | Black Mountain [read]: "1 3/4" thick doors" throughout; the D Series fits 1-3/8"–2" doors as standard [read] |
| Standard single size | 3'0" × 7'0" | 0.914 × 2.134 | SDI 111I example "3′0″ x 7′0″ standard frame" [read]. The game's 1.0 × 2.1 opening is the map's, and it stays. |
| Hollow-metal face sheet | 20 ga (0.032", Level 1 standard duty) or 18 ga (0.042", Level 2 heavy duty) | 0.8 / 1.0 mm | SDI 108-2023 Table 1 [read]. The levels themselves are long-standing; the 2023 edition is the one I read. |
| Hollow-metal core | honeycomb, polystyrene, polyurethane, steel-stiffened or mineral | — | [search] summary of SDI 108 / suppliers |
| Where Level 2 is used | individual offices, storage rooms, closets | — | SDI 108 Table 2 lists Office, Closet, Storage & Utility [read] |
| Wood flush door | solid particleboard or staved core, 1-3/4", veneer faces with a matching hardwood edge band | 0.0445 | ESTIMATE (WDMA standard not read) |
| Bottom undercut, no threshold | 3/4" | 0.019 | SDI 111D note "Doors provided with 3/4″ undercut unless otherwise specified" [read]; Black Mountain cites ANSI A250.10-98 for the same [read] |
| Edge clearance at the hinge edge | 1/8" "design clearance" | 0.0032 | Black Mountain H-1.1 [read] |
| Clearance at jambs and head | 1/8" typical, non-rated | 0.0032 | [search] summary of SDI documents |

**What this means for the game.**
- The visible leaf should be **0.044–0.045 thick**, within the map's 0.05 limit.
- A real door has a 3 mm gap on the sides and head. It still cannot be seen through, because the **frame stop overlaps it** (§2.2).
- The 19 mm under-door gap is real, and so is the light under a door. Where it shows, it should read as "a lit room behind a shut door", not as a slit.

**Close-range detail a 1990 steel door shows** (ESTIMATE / art):
- a vertical edge seam on both stiles;
- a slight oil-can wave in the face under raking light;
- semi-gloss enamel worn to primer at the latch edge and kick zone;
- a paint line where the hinge leaves meet the edge.

**What a veneer door shows** (ESTIMATE / art):
- veneer leaf seams 150–250 mm apart, book-matched;
- a hardwood edge band;
- finish worn around the lever;
- a darker hand-grime zone at 0.9–1.3 m.

### 2.2 Frames

Hollow-metal (pressed steel) frame, the US commercial standard (SDI 111A-24 standard profiles [read]; idighardware frame terminology [read]):

| Part | Inches | Metres | Note |
|---|---|---|---|
| Face (visible casing width) | 2" | 0.051 | "The standard hollow metal frame face is 2 inches wide" (idighardware [read]) |
| Stop height (how far the stop stands out of the rabbet) | 5/8" | 0.016 | SDI 111A profile drawing [read] |
| Door rabbet (for a 1-3/4" door) | 1-15/16" | 0.049 | The extra 3/16" over the door is for silencers or gasket (SDI 111A; idighardware) [read] |
| Second rabbet (double-rabbet frame) | 1-9/16" or 1-15/16" | 0.040 / 0.049 | idighardware [read] |
| Return (back leg at the wall) | 1/2" (7/16" at 5-3/4" jamb depth) | 0.013 | SDI 111A [read] |
| Gauge | 16 ga interior, 14 ga exterior | ≈1.5 / 1.9 mm | SDI 111A [read] |
| Jamb depth | varies with the wall | the game's 0.20 | SDI 111A "VARIES" [read] |
| Silencers | rubber bumpers on the stop | about 3 mm proud of the stop, ESTIMATE | SDI 111A "Rubber Silencers" detail [read] |

How a single-swing door closes the gap in real life:
- The leaf sits in the rabbet against a 16 mm stop that **overlaps the 3 mm clearance** on the stop side.
- Looking at the push face, you see the stop's edge, then the leaf. Looking at the pull face, you see the frame face, a 3 mm shadow line, then the leaf.
- The gap is never a straight see-through line, because the stop sits in the way.

**Double-acting doors** (doors that swing both ways, like the map's) are framed differently. The frame is a **cased opening with no stop**, and the door hangs on double-acting hinges or pivots:
- Black Mountain H-11.0 [read]: hardware "generally falls into two categories: 1. Hinges 2. Pivot Sets". Doors "will be undersized as needed for operating clearance", and centre-hung or double-acting pivots "may require additional operating clearance at the hinge side", with 1/16"–1/8" (1.6–3.2 mm) clearance for the door corners.
- So a real both-ways door **does** have open side gaps. That is the honest period answer to why the map's doors show slits: they are built like double-acting doors.
- The fix (a visual overlap, or a single swing with a stop) is the door-gap agent's call. The period fact for that call: a stop exists only on single-swing doors.

Wood frames and casings (veneer doors in offices): a jamb with an applied wood stop about 3/8"–1/2" × 1-1/4" (10–13 × 32 mm), and a 2–2-1/2" casing (ESTIMATE). In the project research the doorway is "wood-cased" (`10_synthesis.md` T17) or has a "dark frame" (`02_film_shots.md` F09).

### 2.3 Thresholds

- ADAAG 1991 §4.13.8 [read, access-board.gov]: thresholds at doorways may not exceed 1/2" (13 mm) for interior doors, and raised thresholds must be bevelled no steeper than 1:2.
- Interior office doors on carpet usually had **no threshold**. Where the flooring changed under the door (carpet to VCT), there was a metal or vinyl **transition strip** about 13 mm high or less (ESTIMATE).
- In FrontRooms the two sides of a door can be different themes (Low Level 0 against Standard Office; `01_inventory.md` §1.1). A transition strip under the closed leaf is therefore period-true, and it covers the bottom line. It is render-only and ≤ 13 mm high, so it does not affect the map's collision or the Relay's probe, which starts at 0.4 m.

---

## 3. Locksets: knob or lever in 1990 (ADA)

### 3.1 The timeline

| Date | What happened | Source |
|---|---|---|
| 1923 | Schlage files the bored cylindrical lock patent (US 1,674,841), sold as the "A" series lock. The bored (cylindrical) lock later became the most common commercial lock type. | Wikipedia, Schlage [read]; the "most common" part is from securityparts / qualitydoor [search] |
| 1961 | First ANSI A117.1 accessibility standard | UFAS text [read] |
| 1980 | ANSI A117.1-1980. The 1991 ADAAG says its own text reproduces "the illustrations and text of ANSI A117.1-1980". | ADAAG 1991 §1 [read] |
| 7 Aug 1984 | **UFAS** (federal buildings) published. §4.13.9: hardware on accessible doors must not need "tight grasping, tight pinching, or twisting of the wrist"; "Lever-operated mechanisms, push-type mechanisms, and U-shaped handles are acceptable designs"; mounted no higher than 48". | UFAS [read] |
| 1984 | UFAS §4.29.3: doors to hazardous areas ("loading platforms, boiler rooms, stages") get a **textured, e.g. knurled, handle or knob** so they can be identified by touch. | UFAS [read] |
| 26 Jul 1990 | ADA signed. ADAAG is "for … the Americans with Disabilities Act (ADA) of 1990". | ADAAG §1 [read] |
| 26 Jul 1991 | 1991 ADAAG published as Appendix A to the Title III rule, with the same §4.13.9 lever language. | DOJ letter (TAL 186) [read]; ADAAG §4.13.9 [read] |
| 26 Jan 1992 / 26 Jan 1993 | Alterations after 26 Jan 1992 must comply; new facilities "for first occupancy after January 26, 1993" must comply. | DOJ letter, 21 Sep 1992 [read] |
| early 1990s | "knobs were beating out levers on interior doors 80 to 20" (from Schlage's sales tracking); the lever's rise "began after 1990". | builderonline.com [search]; page 403. Context is mostly residential. |

### 3.2 What a 1990 office most likely had

- The building in the story year is **pre-ADA**. Nothing forced levers, but levers were the published accessible standard for a decade. Federal buildings had to use them (UFAS), and many state codes followed A117.1 (UNVERIFIED which states, and when).
- Knobs were still the majority overall (80:20 [search]).
- A plausible 1990 office mix:
  - levers on newer fit-outs and on public and office doors;
  - knobs on older fit-outs and on service doors (storage, janitor, mechanical), which were not "accessible doors" in the sense of §4.13.9.
- That split is exactly the free / locked split this kit needs, and it is period-true. The project's own evidence leans lever on veneer office doors:
  - `02_film_shots.md` F09: "a plain wood-veneer interior door (brown, dark frame, brass lever)";
  - `03_ip_canon.md` line 187: "lever handles";
  - `10_synthesis.md` T18: the grey hollow-metal side door, flagged unsupported, was given "Lever, closer".

### 3.3 Functions (what the lock does), by the ANSI codes the trade uses

From the Schlage D Series knob catalogue (modern catalogue, timeless functions) [read]:

| Function | ANSI | What it does | Fits |
|---|---|---|---|
| Passage | F75 | "Both knobs always unlocked"; no keyway | **Free door** |
| Storeroom | F86 | "Outside knob is fixed"; "Entrance by key only"; inside always free | **Locked door** (the period-true keyed service door) |
| Office / entry | (D53) | push button or turn button locks the outside | — |
| Classroom | F84 | key locks and unlocks the outside knob | — |

- **Game liberty:** a real storeroom lock is keyed on the outside only. The game's locked door is opened with the key from whichever side the player stands (`LockPoint(door, from)`), so the kit puts a keyway on both faces. Nobody can check this in play.
- The real "keyed both sides" hardware is a **double-cylinder deadbolt** (Yale 112 [read]: "keyed entry on both exterior and interior cylinders"). It belongs at 48" (§4.3), which moves the key off the 1.0 m LockPoint and shrinks the head dip.

---

## 4. Cylinders, keyways, roses, escutcheons, and the key-shot anchors

### 4.1 Cylindrical (bored) lockset: the default for both door types

| Part | Inches | Metres | Source |
|---|---|---|---|
| Backset (door edge to the lock centre) | 2-3/4" standard (2-3/8", 3-3/4", 5" optional) | 0.070 | D Series spec [read]; Black Mountain "widespread availability of bored locks with 2 3/4" backset" [read] |
| Cross bore | 2-1/8" | 0.054 | Black Mountain [read] |
| Latch bolt throw | 1/2" (3/4" for pairs of fire doors) | 0.013 | D Series [read] |
| Latch faceplate | 1-1/8" × 2-1/4", square corner, bevelled | 0.029 × 0.057 | D Series [read] |
| Strike (ANSI curved lip) | 1-1/4" × 4-7/8", lip 13/16" to centre | 0.032 × 0.124 | D Series [read]; Black Mountain "4 7/8" 'universal' strike" [read] |
| Knob rose | Ø 2-9/16" | Ø 0.065 | D Series p. 8 drawing [read]; rendered and checked |
| Ball knob | Ø 2-1/8", projection 2-5/8" from the door face | Ø 0.054, proud 0.067 | D Series "Orbit" [read] |
| Bell knob | Ø 2-1/4", projection 2-9/16" | Ø 0.057, proud 0.065 | D Series "Plymouth" [read] |
| Commercial lever (Grade 1) | 4-3/4" long, rose Ø 3-11/32", projection 2-17/32" | 0.121 long, Ø 0.085, proud 0.064 | Arrow QL product page [read]. The page prints "(4.5mm)" for the projection; 2-17/32" is 64.3 mm. |
| Original keys supplied | "two nickel silver keys per lock" | — | D Series spec [read] |

Both a knob (0.065–0.067) and a commercial lever (0.064) fit the map's limit of about 0.07 m proud per side. Keep the kit's lever at or under 0.065 proud. A lever's return end must not exceed it either.

**The game's numbers against these:**
- `DoorHandleHeight` 1.0 against 38" (0.965). Keep 1.0.
- `DoorHandleInset` 0.08 against a 2-3/4" backset (0.070). Keep 0.08; it reads the same.
- `DoorHandleProud` 0.03 is the LockPoint's distance off the face. A real knob face, where the keyway is, sits at 0.065–0.067. A deadbolt cylinder face sits at about 0.015–0.025 (ESTIMATE).
- **Ask for 05 / the map chat:** the shot should frame the kit's `keyway` anchor, not the 0.03 point. Either `LockPoint` reads the anchor's proud value from the sidecar, or the shot code does. Today's 0.03 is about 4 cm short of a knob's keyway.

### 4.2 Keyways and cylinder faces (what the push-in shot looks at)

- **Pins up.** In the US, pin-tumbler cylinders are fitted with the pins at the top of the keyway, so the key goes in **with its cuts (bitting) uppermost**. Europe is the reverse. (Lockpicking101 forum threads [search]; forum-grade, UNVERIFIED.) The shot should insert the key teeth up.
- **Key-in-knob:** the plug face, about 13 mm across (ESTIMATE), sits at the centre of the knob face, with a vertical warded slot about 2.5 × 8.5 mm (ESTIMATE). The key goes in along the knob axis, which is the door normal. On a storeroom lock the outside knob does not turn ("Outside knob is fixed", D Series [read]). **Turning the key retracts the latch.** That is exactly the audit's §3.2 beat "key turns 90° → bolt retracts → leaf pops ajar".
- **Deadbolt / mortise cylinder** (for reference):
  - a round cylinder face of about Ø 29–35 mm (ESTIMATE) inside a rose of about Ø 2-5/8" (0.067);
  - bolt throw 1" (25 mm), or 1-1/8" on the Yale 112 [read];
  - the commercial deadbolt rose figure of Ø 2-5/8" and 1" throw comes from a [search] summary of current product listings.
- **Insert depth.** The key stops at its shoulder on the cylinder face. Blade length is about 25–30 mm (§8), matching the audit's "slides 2.5 cm in".
- **Turn.** The key turns about 90° to unlock and must return to vertical to come out (common pin-tumbler behaviour; ESTIMATE as a number).
- **Rattle (§3.4) on a storeroom knob.** The fixed outside knob gives a few degrees of play and then stops dead. It does not swing down like a lever. Animate a 3–5° twist and a hard stop on the knob.

### 4.3 Hardware locations (DHI "5-10-equal")

Black Mountain H-1.1 [read] and SDI 111A-24 hardware locations [read]:

| Item | Real | Game (2.10 m opening, metres from floor) |
|---|---|---|
| Lock or latch strike centreline | 38" (SDI: 38–42") | 1.0 (map constant) |
| Deadlock centreline | 48" | 1.22 (only if a deadbolt is ever added) |
| Top hinge | top of hinge 5" below the frame head | 1.859–1.973 |
| Bottom hinge | bottom of hinge 10" above the floor | 0.254–0.368 |
| Middle hinge | equidistant | 1.056–1.171 (centre 1.114) |
| Hinges per leaf | 3 up to a 7'6" opening; 4 above (BM chart) | 3 |
| Vision lite centre | "between 60 and 66 inches" above the floor | 1.52–1.68 (doorwaysplus guide [read]) |
| Room sign on the wall, latch side | UFAS: 54–66"; ADAAG 1991: 60" to centreline | 1.52 |

### 4.4 Mortise locks and escutcheons (not recommended here)

- Mortise locks (a lock body in a pocket in the door edge, with separate trim and a separate keyed cylinder) remained "widely installed in industrial, commercial, and institutional environments" (Wikipedia, Mortise lock [read]).
- A full escutcheon plate (a tall rectangle about 2-1/4" × 8–10"; ESTIMATE) with the cylinder above the lever would read further away than a round rose.
- Not recommended:
  - it moves the keyway above 1.0 m;
  - a bored storeroom knob is the cheaper and more typical 1990 office lock (cylindrical "most common lock type … office rooms, storage closets": securityparts/qualitydoor, [search]).
- Keep it as an alternative for 05.

---

## 5. Hinges, strikes, closers, kick plates

### 5.1 Hinges

| Property | Value | Metres | Source |
|---|---|---|---|
| Size for 1-3/4" doors up to 36" wide | 4-1/2" × 4-1/2", full mortise | 0.114 × 0.114 (both leaves open) | Black Mountain "4-1/2" Standard and Heavy Weight Hinge Preparation" [read]; hinge size guide [search] |
| Leaf thickness | standard weight .134"; heavy weight .180" | 3.4 / 4.6 mm | Black Mountain H-6.0 table [read]; Hager BB1279 ".134" gauge [search] |
| Knuckles | 5, with a non-rising removable pin and button tips | — | Hager BB1279 listing [search] |
| Ball bearings | 2, on doors with closers or heavy use | — | same |
| Knuckle (barrel) diameter | about 16–19 mm | ESTIMATE | not found |
| Backset on the frame | 5/16"–11/32" | ≈ 0.008 | Black Mountain [read] |

- **Visible read.** On a single-swing door the knuckles show only on the pull face. The push face sees the stop.
- On a both-ways door the knuckles of a butt hinge are on one face only, so a **double-acting spring hinge** (barrels on both faces) or **pivots** (nothing visible but a pivot cap at the head and foot) would be the honest hardware. Mortise, half-surface and clamp-flange double-acting hinges and pivot sets are described in Black Mountain H-11.0 [read].
- Recommendation: model 5-knuckle butt hinges on the hinge-jamb face the knuckles would face. Accept the one-sided read unless the door-gap work picks Option A (single swing), which makes it fully correct.

### 5.2 Strikes

- ANSI curved-lip strike, 1-1/4" × 4-7/8" (0.032 × 0.124), on the latch jamb at the lock height (§4.1), in the lock's finish.
- Render-only, about 1.5 mm proud of the frame (ESTIMATE).
- The audit's §3.7 "strike plate bends / flies off" needs it as a **separate mesh part**, named `strike`.

### 5.3 Closers (only with a single swing)

- Surface closers were standard on commercial doors. LCN's heavy-duty 4010/4110 series dates from 1958 [search: LCN "100 Years" brochure, too large to fetch].
- ADAAG 1991 §4.13.10: if a door has a closer, it must take at least 3 s from 70° open to 3" from the latch [read].
- A surface closer cannot work on a door that swings both ways.
- Model one (body about 300 × 65 × 50 mm on the push-side head or the top rail, plus a two-link arm; ESTIMATE) **only** if the map adopts Option A (single swing). It is then the strongest silhouette cue at the head for a back-of-house door. Otherwise leave it out.

### 5.4 Kick plates

| Property | Value | Metres | Source |
|---|---|---|---|
| Thickness | .050" | 0.00127 | Rockwood K1050 listing [read] |
| Height | 10" (8" also stocked) | 0.254 | same [read] |
| Width | door width less 2" on the push side, less 1-1/2" on the pull side | collider leaf: 0.929; a 1.02 visual leaf: 0.969 | [search] summary of Rockwood sizing |
| Finish | US32D satin stainless (630), or US3 / US4 brass | — | same [read] |
| Fixing | bevelled edges, #6 × 5/8" screws | — | same [read] |
| Accessible doors with closers | up to 16" (406 mm) high, width less about 2" | 0.406 | UFAS A4.13.9 and ADAAG A4.13.9 [read] |

The title-corridor stream doors already carry 0.25-tall, 4 mm-thick kick plates and 0.055 × 0.18 × 0.045 bar pulls at 1.22 m on both faces (`FrontRoomsRoomStream.cs:1258-1270`). A 0.254 kick plate on the map's locked door matches that language.

---

## 6. Vision lites, borrowed lights, glazing stops

### 6.1 Door vision lites (option for 05; gameplay consequence noted)

- Two-piece steel lite kit that sandwiches the door face from both sides; 1/4" glass. Typical visible sizes 5" × 20" (narrow lite) and 10" × 10" ([search] summary of lite-kit retailers). The centre sits 60–66" above the floor (doorwaysplus [read]).
- Glass in a door:
  - **non-rated door: tempered** (the 1977 CPSC standard covers "Doors", 16 CFR 1201.1 [read]);
  - **fire-rated door: wired glass**, which is exempt: "Wired glass used in doors or other assemblies to retard the passage of fire …" (16 CFR 1201.1 [read]).
- **Gameplay flag.** A lite is a deliberate see-through hole. The Relay's sight ray stops at the leaf collider, so the player could see the Relay through a lite but the Relay could not see the player. That is a design call for the map chat and Red, not a default.

### 6.2 Interior windows / borrowed lights

There are two period systems. Both are render-only and stay outside the 1.4 × (0.35–2.0) opening.

| System | Profile | Glass | Where | Kit slot |
|---|---|---|---|---|
| **Hollow-metal borrowed light** | same family as the door frame: 2" (0.051) face; 5/8" (0.016) glazing stops on both faces (a fixed integral stop on one side, a screw-applied removable stop on the other; Allegion "glazing bead for hollow metal frames" [search]). Glass bite about 10–13 mm, ESTIMATE. | 1/4" | corridors, service areas, rated walls (wired) | painted like the door frame |
| **Office-front glazing** (aluminium or steel) | about 50 mm face, snap-in glazing beads, black vinyl gaskets | 1/4" | offices facing the open plan | `Prop_SteelBlack` dark bronze, exactly as `Kit_InteriorWindow` builds it (`Tools/Blender/frontrooms_kit/assets/interior_window.py:1-30`) |

- The audit's glass spec asks for "a stop on both faces, all four sides, 18 mm wide × 12 mm deep" (`10_audit_report.md` §4.1). That matches the 5/8" hollow-metal stop.
- **Recommendation:** use the hollow-metal profile on map windows next to painted-steel locked doors, and the dark-bronze office front elsewhere. The choice belongs to the kit spec.

---

## 7. Glass types and how they break

### 7.1 What a 1990 building had, and what the law said

| Glass | 1990 use | Break behaviour | Source |
|---|---|---|---|
| **Annealed float, 1/4"** | ordinary interior glass. In older buildings, everywhere: the federal impact rule (16 CFR 1201, 6 Jan 1977) covered doors and similar products, not most other hazardous locations. | "breaks into irregular and sharp pieces". Edges stay in the stops. | Wikipedia, Tempered glass [read]; 16 CFR 1201.1 [read]; history note [search] |
| **Tempered, 1/4"** | doors, sidelights and code "hazardous locations" in new work | "shatter[s] into small granular chunks"; "the entire unit usually breaks"; about 4× stronger than annealed; cannot be cut after tempering | Wikipedia, Tempered glass [read] |
| **Wired, 1/4" polished** (square "Georgian" or diamond mesh) | fire-rated doors and walls; 20–45 min ratings | "The wire prevents the glass from falling out of the frame even if it cracks"; it is weaker than plain glass; the US IBC "effectively banned" it in 2006 | Wikipedia, Wired glass [read]; General Glass Georgian [read]: 1/4" (6.8 mm), square mesh, "20-45-minute", "not designed for impact-rated safety glazing"; idighardware 2009 on the 2003/2006 IBC [read] |
| Laminated | rare in 1990 office interiors (ESTIMATE) | cracks; the interlayer holds the sheet | — |

**Is the map window legal as annealed?**
- Today's codes require safety glazing in a single pane when all four of these hold: more than 9 sq ft, bottom edge under 18", top edge over 36", and a walking surface within 36" (NC OSFM interpretation of R308.4 [read]; IBC 2406 has the same test).
- The map pane is 1.4 × 1.65 = 2.31 m² (24.9 sq ft), its bottom edge is at 0.35 m (13.8"), and its top at 2.0 m. **It meets all four.** A code-built 1990 pane here would be tempered (whether the late-1980s model codes had this exact test is UNVERIFIED).
- Annealed glass is therefore an **art-direction choice with a period alibi**: a borrowed light in an older building, glazed before the rule. That is the era lock's second-hand window (1955–85). This agrees with the audit's "annealed look" default (`10_audit_report.md` §4.4 item 5; `02_glass_and_breakables.md` §5.1, §8.2).

### 7.2 What each type gives Red's staged break (§3.5 of the audit)

| Red's beat | Annealed (recommended) | Tempered (variant) | Wired (P2, door lites) |
|---|---|---|---|
| Crack stages during the hold | Yes: radial cracks from the impact, then concentric rings when the pane is held on all sides; later cracks stop at earlier ones (`02_glass_and_breakables.md` §5.1, Forensic Field) | **No.** Tempered glass holds, then fails all at once. A "pre-crack" stage is not physical; at most a chip at the impact. | Yes: cracks spread like annealed glass |
| The shatter | Inner pieces fall out; daggers drop; edge pieces stay as **teeth** in the stops | The whole pane turns to roughly 1 cm granules and cascades. It may hang crazed for an instant first (UNVERIFIED). | Nothing falls. The centre sags and hangs on the wire, and must be torn out by a second hold or the Relay. |
| Pieces breaking again on the floor | Yes on hard floors (VCT, concrete) from about 1 m. On carpet many large pieces survive whole (ESTIMATE, untested). | Already granules; they scatter and bounce | — |
| Glass left on the floor | Flat angular shards 2–20 cm plus crumbs, mostly within about 1 m of the wall, more on the far side (ESTIMATE) | A heap and spray of granules | A little crumb; the wire stays in the frame |
| Remnants in the frame | Teeth: jagged pieces held by the stops, 2–30 cm deep (ESTIMATE). Head teeth are the "guillotine" ones. | A few granules stuck in the glazing channel | Wire stubs and glass clinging to the wire |

**What this means for the kit's meshes** (all render-only, `kit.no_collider()`):
- intact pane sized to the glass bite;
- crack masks for stages 1–2, or crack-line overlay meshes;
- 3 × 3 authored impact centres × 2 variants of radial pre-fracture (audit §4.4), each piece tagged `inner` / `middle` / `tooth`, as 6 mm slabs with green edges;
- for each large `inner` / `middle` piece, a pre-split child set for its second break on the floor;
- 2–3 static floor-glass scatter meshes per side;
- tempered "dice" particle meshes (2–3 granule shapes) for the variant.

**Teeth versus the map constraint.**
- Real teeth stick **into** the opening. `00_map_constraints.md` asks that remnants stay outside the 1.4 × (0.35–2.0) opening once broken.
- The audit's climb (§3.6) snaps the sill teeth at the plant.
- **Ask for the map chat:** allow render-only teeth to intrude a set depth, for example ≤ 0.12 m at the head and jambs and ≤ 0.04 m at the sill, removed by the climb. The alternative is to accept toothless edges, which loses the danger read.

### 7.3 Glass numbers for the kit

- Thickness 1/4" (6 mm). Edges show green (`02_glass_and_breakables.md` §4.3; the Glas Trösch figures quoted there).
- Wired glass: wire pitch about 1/2" (12.7 mm) square for Georgian. **UNVERIFIED**: General Glass gives "square patterned wire mesh" but no pitch.
- Wired glass is P2. It needs a wire-grid texture or a new slot (§10).

---

## 8. Keys, rings, tags

### 8.1 The key

| Property | Period value | Model value (metres) | Source |
|---|---|---|---|
| Type | US pin-tumbler cylinder key, 5-pin (residential and light commercial) or 6-pin (commercial). D Series ships 6-pin keys. | — | D Series "6-pin" [read]; SC1 "5-pin" listings [search] |
| Parts | bow (grip), shoulder (stops the key at the cylinder face), blade with bitting cuts on top, milled side grooves (keyway profile), tip | named anchors below | key-anatomy summary [search] |
| Overall length | about 2-1/8"–2-3/8" | 0.055–0.060 | ESTIMATE |
| Bow | about 1" wide, rounded "paddle" outline, 2 mm thick, ring hole Ø 4–5 mm | 0.025 × 0.022 × 0.002 | ESTIMATE |
| Blade | about 0.33" tall × 0.08" thick | 0.0085 × 0.002 | ESTIMATE |
| Blade length (shoulder to tip) | about 1.0"–1.2" | 0.026–0.030 | ESTIMATE; matches the audit's 2.5 cm insert |
| Cut spacing / depth step (one maker's spec) | .1562" between cuts; .015" per depth step | 4.0 mm / 0.38 mm | Allegion KB "combinating rule 15" [search]; page 403 |
| Material, factory original | **nickel silver** (silver-white, hard, wears well) | `Prop_Aluminium` (closest satin silver) | D Series "two nickel silver keys per lock" [read]; Allegion KB title "Why are the Schlage commercial keys manufactured from nickel silver?" [search, 403] |
| Material, duplicate | **brass**, often nickel-plated (aftermarket blanks) | `Prop_Brass` | SC1 aftermarket blank listings, "brass … nickel plated" [search] |
| Stamping | "DO NOT DUPLICATE" plus a keyset code (e.g. "AA2", "C14") or room number | Label atlas cell or normal-map stamp | ESTIMATE (common practice, not sourced) |

- **No trademarks.** The bow is a generic paddle outline. Do not copy a maker's bow, logo or keyway name.
- **Zone key recommendation:** brass, read as a hardware-store copy someone cut, which is period-true. It catches lamp highlights in the audit's §3.1. A nickel-silver variant can mark a "facility original", for example a master key if one is ever added.

**Anchors the key model must carry** (for the head-dip shot, audit §3.1–3.2):

| Anchor | Where | Use |
|---|---|---|
| origin = `ring` | centre of the bow's ring hole | the hang point on hooks; the tag's ring passes through it |
| `grip` | centre of the bow | where a posed hand or held pose attaches (audit §3.0) |
| `shoulder` | the stop on the blade's top edge | it meets the cylinder face at full insert |
| `tip` | the blade tip, on the blade centreline | lines up to the keyway 3 cm before insert |
| `insert_axis` | from shoulder toward tip | slide direction, 25–30 mm |
| `cuts_up` | +normal of the bitting edge | US pins-up: cuts go in uppermost |

Keep the blade a separate mesh part from the bow. The shot rolls and slides the whole key, but a later hand pose may need the bow alone.

### 8.2 Rings and tags

| Item | Period form | Size | Kit slot | Source |
|---|---|---|---|---|
| Split ring | flat steel double coil, nickel-plated | Ø 25–32 mm, wire about 1.5 mm | `Prop_Chrome` | ESTIMATE |
| Metal-rim paper tag | round paper disc in a non-tarnish metal rim, with a string or split ring; written by hand | Ø 1-1/4" (0.032) | rim `Prop_Aluminium`, face `Prop_Label` / `Prop_Paper` | Avery metal-rim tag listings, "1-1/4" diameter" [search]. The Dennison company (tags) merged into Avery Dennison in 1990 [search]: the right era, but no brand on the model. |
| Plastic ID tag | coloured plastic tag with a snap-in label window, on a split ring | about 50 × 25 × 3 mm, ESTIMATE | `Prop_PlasticRed` / `Blue` / `White` / `Beige` / `Black` plus `Prop_Label` | Lucky Line Products, "family owned since 1961", plastic key identification tags [search] |
| Stamped numbered tag | aluminium or brass tag stamped with a number that matches a cabinet hook | round Ø 32 mm or oval, 1 mm thick | `Prop_Aluminium` / `Prop_Brass` | Telkee trademark (filed 1928) for "key identification tags, key retainers, and institution key-receiving boards" [search] |
| Janitor's hoop ring | large hinged ring with 10–30 keys | Ø 75–100 mm | `Prop_Chrome` | ESTIMATE (decor only) |

**Zone identity:**
- Use a **plastic tag in the zone colour**, with the zone's room code on a label (`Prop_Label` atlas).
- Repeat the same code on the locked door's room sign (§11).
- A facility key cabinet indexes keys by room number, so "tag code = sign code" is the period system.

---

## 9. How facilities stored keys (hosts)

| Host | Period form | Size / height | Key pose | Kit slot | Source |
|---|---|---|---|---|---|
| **Wall key cabinet** | steel cabinet, hinged locking door, rows of numbered hooks on hook strips, index card in the door | about 0.30–0.40 W × 0.40–0.50 H × 0.08–0.10 D, mounted with its centre at 1.3–1.5 m | hangs from a hook, blade down; door ajar | `Prop_SteelPutty` / `Almond`, hooks `Prop_Chrome`, labels `Prop_Label` | Telkee "institution key-receiving boards" (1928) [search]; sizes ESTIMATE |
| **Hook board** | plywood or pegboard panel with brass cup hooks in a grid; masking-tape labels | 0.60 × 0.40, centre at 1.4 m | hangs | `Prop_Plywood`, `Prop_Brass`, `Prop_TapeBlue` / `Prop_Paper` | ESTIMATE |
| **Desk / cabinet top** | key lying flat by a phone, in a pen tray, under a binder | surface height 0.72–0.76 (desk) | flat, tag beside it | — | ESTIMATE |
| **Lock box / cash box** | small steel box, lid open | about 0.25 × 0.18 × 0.09 | in the open tray | `Prop_SteelBlack` / `Putty` | ESTIMATE |
| **Single nail or hook by a door** | one key on a nail at the latch side | 1.5–1.6 m | hangs | `Prop_SteelBlack` | ESTIMATE |

**Host anchor convention** (proposal to `03_readability_placement_shots.md` and the kit spec):
- Every host carries one or more `key_slot` anchors. The map puts the **key's origin (`ring`) exactly on a `key_slot`** and takes the anchor's rotation.
- On hooks the slot is the hook's contact point. On surfaces it is the resting point of the ring hole, with the key lying flat and its blade along the anchor's +X.
- A hosted key **does not spin or glow**, agreeing with the visual chat and the audit's §3.1.
- Pickup reach: the map's ≤ 0.9 m horizontal pickup is measured from the key transform, which is the ring.
  - A wall cabinet's hooks sit about 0.05–0.08 m off the wall, and the player's capsule radius is 0.3 m, so a player touching the wall is about 0.35–0.40 m away. That is well inside 0.9.
  - Keep any host's slot within 0.6 m of walkable floor, measured horizontally (ESTIMATE margin).

---

## 10. Finishes and slot mapping

BHMA (ANSI A156.18) codes with the older US codes: 605 = US3 bright brass, 606 = US4 satin brass, 613 = US10B oil-rubbed bronze, 626 = US26D satin chrome, 630 = US32D satin stainless (finish guides [search]; the D Series finish chart lists 605/606/609/612/613/625/626/629/630 [read]).

| Part | Free door (veneer) | Locked door (painted steel) | Kit slot |
|---|---|---|---|
| Leaf | stain-grade veneer | semi-gloss enamel, putty | veneer: **no kit slot** (`Door_Veneer` exists only as a Unity surface); `Prop_SteelPutty` for steel |
| Frame / casing | map trim today (`CoveBase`) or stained wood | painted steel, same as the leaf | `Prop_SteelPutty` (or `Prop_SteelBrown`, see §11) |
| Lever / knob / rose / cylinder | US4 or US3 brass lever | US26D satin chrome knurled knob | `Prop_Brass` / `Prop_Chrome` |
| Hinges | US4 brass | US26D (on steel, also sold primed and painted) | `Prop_Brass` / `Prop_Chrome` |
| Strike | matches the lockset | matches the lockset | same |
| Kick plate | none, or US4 brass | US32D satin stainless | `Prop_Brass` / `Prop_Aluminium` |
| Room sign | — | two-colour engraved plastic, white letters on a dark ground, about 0.25 × 0.075 × 0.003 (ESTIMATE) | `Prop_PlasticBlack` + `Prop_Label` atlas cell |
| Transition strip | metal or vinyl | same | `Prop_Aluminium` / `Prop_Rubber` |
| Window frame | dark bronze or painted steel | painted steel | `Prop_SteelBlack` / `Prop_SteelPutty` |
| Intact glass (kit side) | 6 mm | 6 mm | `Prop_Glass` |
| Shards / teeth / floor glass | opaque dark, green edges (audit §4.2 `Glass_Shard`) | same | **no kit slot**: needs `Glass_Shard` |
| Wired glass (P2) | — | wire grid | **no kit slot**: needs a wired-glass texture or slot |

**Slots this kit would need** (report only; `kitlib.py` not edited):
1. a veneer door slot mapped to Unity's `Door_Veneer`, or use `Prop_WoodOak`;
2. `Glass_Shard`;
3. a wired-glass variant (P2);
4. new `Prop_Label` atlas cells for room signs and tag faces. The 4×4 atlas is shared with binders and other props, so free cells must be checked.

---

## 11. Locked versus free: what period practice gives `05_locked_door_type.md`

**The rule in the IP research.** HR03 "What the Backrooms teach" asks for:
- "FROM 1990: A half-remembered ordinary thing from the set's own year";
- "DOORWAY FIRST: The 1.0 × 2.1 m door is its picture frame. It has to read there as a dark shape at 12 m."

So the difference must be an ordinary 1990 building difference, not a game colour code. A **dark** door leaf should be avoided: at 12 m it can read as an open doorway into a dark room, and it competes with the Relay's dark-shape read.

**The ordinary 1990 difference:**
- Occupied rooms (offices, showroom back offices) got **wood-veneer doors**, often with levers.
- Service rooms (storage, stock, janitor, electrical, mechanical) got **painted hollow-metal doors** in steel frames with **keyed storeroom locks**:
  - SDI lists "Storage & Utility", "Closet" and "Mechanical/Storage" among its application rows (SDI 108 Table 2 [read]);
  - the storeroom function is keyed and has a fixed outside knob (D Series F86 [read]);
  - doors to boiler and mechanical rooms got knurled hardware (UFAS 4.29.3 [read]).
- Service rooms are the rooms a facility keeps locked.

**Cues ranked by the distance they read at** (ESTIMATE; to verify in a capture by 03 or 05):

| Distance | Cue on the locked door | Free door |
|---|---|---|
| 10–12 m+ | flat, cool, light **painted steel** leaf and a frame in the same paint | warm, grained **veneer** leaf; darker trim |
| 6–10 m | **dark sign plate** on the wall at the latch side, 1.52 m; bright **kick plate** band (0.254 m) | no sign, no kick plate (or brass) |
| 2–5 m | **knob** (a dot) against a **lever** (a horizontal bar); chrome against brass | brass lever |
| 0.5–2 m | **keyway** in the knob face; **knurl** band; sign text (e.g. "STORAGE 2B" in the zone code) | passage lever, no keyway |
| optional | surface **closer** at the head (only with a single swing, §5.3); no vision lite | — |

**Colour options for the steel door** (art judgement, not sourced):
- **Putty / light grey** (`Prop_SteelPutty`, recommended): lighter and cooler than veneer, and never mistaken for an opening.
- **Dark brown** (`Prop_SteelBrown`): a classic 1980s frame colour, but see the dark-shape warning above.

**What this does to the map today.** Lock state is global: `LockedHere` is `doorsNeedKeys && !unlockedDoors.Contains(edge) && !HasKeyHere()` (`FrontRoomsMapWorld.cs:1701`). A per-door "needs key" flag, so that some doors are free, is a map-chat change that 05 has to ask for.

---

## 12. Open items / UNVERIFIED

1. **Knob vs lever share in 1990.** The 80:20 figure is from a search summary of a 403 page (builderonline.com) and is mostly residential. No commercial-only figure was found.
2. **State adoption of A117.1-1980 lever rules before 1990.** Not checked state by state.
3. **Key dimensions** (length, bow, blade) are ESTIMATES. Measure two real commercial keys before modelling.
4. **The 1990 model-code glazing test** (18" / 9 sq ft / 36"). It is current code; whether the late-1980s UBC / BOCA / SBC had it is UNVERIFIED.
5. **Wired-glass mesh pitch** (about 1/2" square) is UNVERIFIED.
6. **Tempered "hangs crazed then falls"** is UNVERIFIED; annealed re-breaking on carpet versus VCT is an ESTIMATE. A reference video or a test would settle both.
7. **LCN 4010/4110 date (1958)** is from a search summary; the brochure exceeded the fetch limit.
8. **"Pins up" US convention** is from forum threads (search summary).
9. **Hinge knuckle diameter** not found; 16–19 mm is an ESTIMATE.
10. **Asks to other chats** (collected):
    - (a) LockPoint's proud value against the kit's `keyway` anchor (§4.1);
    - (b) a teeth intrusion allowance in the window opening (§7.2);
    - (c) a per-door locked flag (§11);
    - (d) the closer and the honest hinge read depend on the Option A / B swing decision (§2.2, §5.1, §5.3);
    - (e) new slots and atlas cells (§10).

---

## 13. Sources

**Read for this note (2026-10-02):**
- U.S. Access Board, ADAAG 1991 edition as amended through 2002 (§1, 4.13.8–4.13.10, 4.29.3, 4.30.6, A4.13.9): https://www.access-board.gov/adaag-1991-2002.html
- U.S. Access Board, UFAS 1984 (publication 7 Aug 1984; §4.13.9, 4.29.3, 4.30.6, A4.13.9; A117.1 history): https://www.access-board.gov/aba/ufas.html
- U.S. DOJ, Technical Assistance Letter (21 Sep 1992), ADA Title III dates: https://www.justice.gov/crt/foia/readingroom/frequent_requests/ada_tal/tal186.txt
- Schlage D Series cylindrical locks, knob catalogue (knob drawings p. 8, functions pp. 10–13, specifications p. 18). I read the copy in the session scratchpad (`hw/dseries.pdf`, 20 pages). Its download URL was not recorded. The same catalogue (the cover text matches: Orbit and Plymouth in 626) is listed at https://cdn11.bigcommerce.com/s-iqhkw55zf5/content/product-attachments/Schlage_D_Series_Catalog.pdf; that is a search result, not re-read.
- Steel Door Institute, SDI 111 (111A-24 frame profiles and hardware locations, 111D, 111E, 111I): https://steeldoor.org/wp-content/uploads/2020/02/SDI_111.pdf
- Steel Door Institute, SDI 108-2023 (door levels, gauges, applications): https://www.steeldoor.org//wp-content/uploads/2020/02/SDI_108.pdf
- Black Mountain Door, Technical Data — Hardware (H-1.0, H-1.1 5-10-equal locations, H-6.0 hinge preps, H-11.0 double-acting hinges and pivots, H-13.0): https://s3.amazonaws.com/s3-absupply-net/pdf/Black_Mountain_Door_Tech-Data_Hardware.pdf
- idighardware, "OTU: Openings Terminology for the Unenlightened — Frames" (2014): https://idighardware.com/2014/10/otu-openings-terminology-for-the-unenlightened-frames/
- idighardware, wired glass and the IBC (4 Mar 2009): https://idighardware.com/?p=162
- 16 CFR 1201.1 (scope; 42 FR 1426, 6 Jan 1977; wired-glass fire exemption): https://www.law.cornell.edu/cfr/text/16/1201.1
- NC OSFM informal interpretation, R308.4 (2012): https://ncosfm.gov/residential/03084-tempered-glass-windows-9-sq-ft-or-more/open
- Wikipedia, Tempered glass: https://en.wikipedia.org/wiki/Tempered_glass
- Wikipedia, Wired glass: https://en.wikipedia.org/wiki/Wired_glass
- General Glass International, Georgian Polished Wire: https://www.generalglass.com/?p=720
- Wikipedia, Schlage: https://en.wikipedia.org/wiki/Schlage
- Wikipedia, Mortise lock: https://en.wikipedia.org/wiki/Mortise_lock
- Wikipedia, Best Lock Corporation: https://en.wikipedia.org/wiki/Best_Lock_Corporation
- Locksmith Ledger, R. L. Zunkel, "ADA, Older Buildings and the Locksmith" (2005): https://locksmithledger.com/door-hardware/article/10238316/ada-older-buildings-and-the-locksmith
- Rockwood K1050 kick plate listing: https://www.doorwaysplus.com/shop/rockwood-k1050-10-tall-kick-plate-us32d-287
- Arrow QL Grade 1 lever lockset listing: https://www.craftmasterhardware.com/parent-brand/arrow-lock/arql-arrow-ql-series-grade-1-lever-locksets
- Yale / Accentra 112 double-cylinder auxiliary deadbolt listing: https://www.uhs-hardware.com/products/accentra-formerly-yale-112-double-cylinder-auxiliary-deadbolt
- doorwaysplus, field guide to steel-door lite kits: https://www.doorwaysplus.com/blog/our-blog-1/cutting-a-door-window-lite-into-a-steel-door-a-field-guide-for-commercial-installers-54
- Figma `0tCbAiVUlrPId3RWd9LRif`: HR03 (2331:873, screenshot), IR03 (2320:2106, metadata), HUNTER section (2331:852, metadata), IP RESEARCH section (2312:852, metadata)

**Search summaries only (page refused or unparsed; UNVERIFIED):**
- builderonline.com/?p=45667 (knobs vs levers 80:20)
- Allegion KB nickel-silver keys and combinating rule 15
- LCN 100 Years brochure (4010/4110, 1958)
- Hager BB1279 hinge listings
- Rockwood kick-plate width rule
- Lucky Line Products history
- Avery metal-rim tags and Avery Dennison history
- Telkee trademark (1928)
- lockpicking101 "pins up" threads
- commercial deadbolt listings (2-5/8" rose, 1" throw)
- securityparts / qualitydoor on cylindrical vs mortise
- Allegion KB glazing beads
- vision-lite kit retailers

**Project files read:**
- `00_map_constraints.md`, `01_inventory.md` (§0–§1)
- `../office_and_film/22_era_lock.md`, `02_film_shots.md` (F09), `03_ip_canon.md` (line 187), `10_synthesis.md` (T15–T18)
- `../interaction_audit/10_audit_report.md` §3–§4, `02_glass_and_breakables.md` §5, §7–§8
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:781-791, 927-936, 950-962, 1625-1648, 1701`
- `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs:54-71`
- `Assets/Scripts/FrontRoomsRoomStream.cs:1255-1272`
- `Tools/Blender/frontrooms_kit/assets/interior_window.py:1-60`
- `Tools/Blender/frontrooms_kit/kitlib.py` (SLOTS names)
