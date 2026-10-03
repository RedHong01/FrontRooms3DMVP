# 05 — Locked-door type: how a key door reads differently from a free door

Status: DONE (2026-10-02, 23:5x). Research plus an in-engine mock-up test in the private clone. Nothing in the real project was changed.
Owner: visual chat, interactables workflow (locked-door type agent).

Binding input: [00_map_constraints.md](00_map_constraints.md).
Sibling reports this one builds on:
- [02_period_hardware.md](02_period_hardware.md) (period hardware, dimensions, functions, §11 input to this report);
- [03_readability_placement_shots.md](03_readability_placement_shots.md) (pixel budgets §1.1, the door distance test §1.7, zone identity §2.5, anchors §3.3).

Other inputs:
- era: `../office_and_film/22_era_lock.md`;
- shots: `../interaction_audit/10_audit_report.md` §3.2 (unlock, head dip) and §3.4 (rattle);
- Figma file `0tCbAiVUlrPId3RWd9LRif`, page 2099:76. Read with `get_metadata` and `get_screenshot`: IP RESEARCH 2312:852 (IR01–IR06), PROP KIT · THREE-VIEW + ERA 2324:852 (K00, K16), PROP KIT · REAL vs MODEL 2349:852 (R44), HUNTER 2331:852 (HR03).

Code is cited as `file:line` in the real project (read only). Short names:
- `MapWorld` = `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`
- `Map` = `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs`
- `Units` = `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs`
- `Game` = `Assets/Scripts/FrontRooms3DGame.cs`
- `Stream` = `Assets/Scripts/FrontRoomsRoomStream.cs`

Web claims carry the URL I read, or say UNVERIFIED.

---

## 1. Decision

**Free door (opens directly):** the stained wood-veneer office door, which is what the map draws today (`Door_Veneer`).
- It has a dark wood casing in the building's trim colour.
- It has a brass passage lever with no keyhole.
- It has no sign and no kick plate.

**Key door (needs a key):** a painted hollow-metal back-of-house door, a "storeroom" door:
- an **almond-white enamel leaf**, lighter than the wallpaper. This needs a new surface, `Door_Enamel`. The kit's `Prop_SteelPutty` is too dark (§5.3);
- a **dark bronze 2-inch steel frame** in the building's dark trim value;
- a **10-inch kick plate** on both faces;
- a **dark engraved "EMPLOYEES ONLY" plate** centred on the leaf at 60 in (1.524 m), on both faces;
- a satin-chrome **storeroom key-in-knob lockset** on both faces. The keyway sits at the lock point, 1.0 m;
- the zone **number plate** from 03 §2.5 beside the knob.

Option for later (Red decides): a 4 × 25 in **wired-glass vision lite** on the latch side. It is the strongest mark at 20 m, but it is a see-through hole (§6.4).

Why this pairing:
1. **It reads at 6, 12 and 20 m in all three lights I tested**, by value:
   - Level 0 lit and dim, and the Office grade, all measured in engine (§5);
   - the key door's leaf is 2.1–3.3× the veneer's luminance;
   - it is 4.5–6.6 stops brighter than an open doorway into a dark room;
   - the dark frame outlines it against pale walls.
2. **It is never a dark rectangle.** HR03 rule 03 needs the 1.0 × 2.1 m doorway to be the Relay's dark picture frame at 12 m. A dark locked door competes with that.
   - The dark-bronze candidate measured only +0.3 stops above an open dark doorway in a dim Level 0 cell.
   - It was also only 0.8 stops below the veneer door there (§5.2).
3. **It is the IP's own door.** "Backrooms" are a store's back rooms.
   - In the A24 film, the way in is found in the store's utility space, "while checking the breaker box".
   - The free/locked split is the ordinary 1990 split between occupied rooms (veneer) and service rooms (painted steel, keyed storeroom lock). 02 §11 shows this.
4. **It is era-exact**, and nothing in it is later than 1990 (§4).
   - The storeroom function, the 1-3/4 in hollow-metal door and 2 in frame, and the kick plate all predate 1990.
   - The door-mounted engraved plate without Braille is pre-ADAAG (ADAAG was published 1991).
   - Wired glass in rated door lites was legal from 1977 to 2003/2006.
5. **It gives Red's head-dip shot a single, obvious keyway at 1.0 m.** That is the height where the dip reads strongest (03 §3.3: about 39° down at 1.0 m, against 21° at 1.2 m).
6. **It is cheap.**
   - One leaf mesh with four slots, one frame profile and one knob asset.
   - The text is one texture cell, plus the shared number atlas from 03.
   - No lights; render-only.

Where I differ from the siblings, on evidence:
- 02 §11 suggested putty paint and a frame in the same paint. In engine:
  - `Prop_SteelPutty` renders at almost the wallpaper's value (−0.1 stop) and drops to 1.4× the veneer in dim light;
  - a frame in the same paint loses the door's outline against the pale Office wall at 12–20 m (§5.3).
- 03 §1.7 leaned towards a dark steel door, as "the safer side". The measurements say dark is the risky side in dim cells (§5.2), and dim cells are common (audit frames 39 and 48).

---

## 2. What the game does today (code facts)

| Fact | Where | What it means for the door type |
|---|---|---|
| Locks are all-or-nothing. `LockedHere` = `doorsNeedKeys && !unlockedDoors.Contains(edge) && !HasKeyHere()`. With keys on, **every** door is locked. | `MapWorld:1701`; profile default off, `FrontRoomsLevelProfile.cs:31` | "Locked doors look different" needs a per-door flag. The map chat proposes `lockedDoorShare` ≈ 0.35 from an edge hash (`Documentation/VISUAL_CHAT_TASKS.md` W5). Red picks the rule. |
| Doors exist only where a Low zone meets a Standard zone. | `Map:350-355`; `Units:54` | Every door has at least one Level 0 face. |
| Low zones are never Office. | `Map:294-295` | The other face is Level 0 or Office, so the type must read under both grades. |
| The leaf is the collider cube, using the `Door_Veneer` surface. The trim is `CoveBase`. | `MapWorld:931-936`, `MapWorld:1785-1786` | Today's look is the free door. `Door_Veneer` albedo averages sRGB (157, 109, 59), linear luminance 0.19. The L0 wallpaper and Office drywall are both 0.43. (Measured from `Assets/Resources/Surfaces/Textures/*_A.png`.) |
| The lock point is at `DoorHandleHeight` 1.0, `DoorHandleInset` 0.08 and `DoorHandleProud` 0.03, on the opener's face. | `MapWorld:1640-1648`, `Units:58` | The keyway goes here. A knob's keyway sits at 0.067 proud, not 0.03 (§7). |
| The global post grade: temperature +9, tint −7, saturation −8, contrast −6, exposure +0.15. The Office zone grade: temperature +1, tint −14, saturation −22, contrast +4, colour filter (.95, .99, .97). | `Assets/Resources/Rendering/FrontRoomsPost.asset:191-226`, `FrontRoomsPost_Office.asset:16-127` | The Office grade strips colour. **Value is the cue that survives both grades.** A hue-only difference (teal, red, slate) will not hold at 12 m in the Office. |
| The camera has a 76° vertical FOV, with the eye at 1.62 m. | `Game:227`; `Units:92` | Pixels per metre at 1080p = 1080 / (2·d·tan 38°) = **691 / d**: 115 at 6 m, 58 at 12 m, 35 at 20 m. |
| In dim cells today's veneer door has the same value as the wall: luminance 0.016 against 0.015. | audit frames `interaction_audit/images/39_door_normal_before_hud.png`, `48_door_locked_before_hud.png`, sampled by me | The free door is already hard to read in the dark. The key door must not also be dark. |
| The title-corridor doors have 0.25 m kick plates and bar pulls on both faces. | `Stream:1255-1271` | A 0.254 m kick plate on the key door matches the language the game already uses. |

**Pixel budget, so we know what can carry the read** (leaf 0.98 × 2.08 m):

| Feature | 6 m | 12 m | 20 m |
|---|---|---|---|
| The whole leaf | 113 × 240 px | 56 × 120 | 34 × 72 |
| A 0.254 × 0.076 sign plate | 29 × 9 | 15 × 4 | 9 × 3 |
| A 0.254 m kick plate band | 29 px tall | 15 | 9 |
| A 0.10 × 0.64 lite | 12 × 74 | 6 × 37 | 3.5 × 22 |
| A 54–65 mm knob or rose | 6–7 px | 3–4 | 2 |
| 19 mm sign letters | 2 px | 1 | <1 |

So:
- beyond about 6 m, only the leaf's value, the frame outline, and large marks (plate, kick band, lite) carry the type;
- hardware is a 0–5 m confirmation;
- text is a ≤ 1.5 m flavour detail.

This matches 03 §1.1 and §1.7.

---

## 3. What the project research says (Figma and office_and_film)

| Source | What it says | What it implies for the key door |
|---|---|---|
| HR03 "What the Backrooms teach" (2331:873), rule 02 FROM 1990 | "A half-remembered ordinary thing from the set's own year. Not a costume." | Nothing invented: no glowing panel, no chains, no boarded door, no red paint code. Use an ordinary 1990 building difference. |
| HR03, rule 03 DOORWAY FIRST | The 1.0 × 2.1 m door is the Relay's picture frame and "has to read there as a dark shape at 12 m". | The key door must **not** be a dark slab, or it reads as an open dark doorway or a Relay in a doorway. A pale door also improves the Relay read: a dark figure in front of a pale door is a stronger silhouette. |
| HR03, "Not ours to use" | Other artists' monsters and designs are out. | No borrowed iconography (no RE-style emblem doors, no film signage). |
| IR01 "One bad photo" (2320:2056) | "It began as a photo of a real room, so it has to look real." The room is a furniture store under renovation. | The door must be real commercial hardware, correctly sized. |
| IR04 "Yellow by accident" (2320:2141) | "Keep the light neutral. Put the yellow in the walls." | Under neutral light, an off-white enamel reads as off-white against yellow paper. The door can carry its own value. |
| IR05 "Copy, paste, pile" (2320:2170) | "Our kit is a catalogue: few models, many copies." | One key-door model and one sign text, copied. Zone identity comes from a plate cell (03 §2.5), not from new models. |
| IR06 "The games" (2320:2195) | "They add monsters. We add a choice at every exit." The FrontRooms run-zone frame shows an EXIT sign over a door. | Free vs locked is that choice, so it must read before the player walks to the door. |
| K00 (2324:853), 22_era_lock §3 | The kit is 44 models from 1950–2000. **There is no door in the kit yet.** | The two door types are new kit entries and must be dated in the era table (§4). |
| R44 "Stud doorway" (2350:1286); `01_film_production.md:86, 204` | Blue painter's tape marks the film's boundary and opening. `Kit_DoorwayStuds` already uses it. | **Blue is the IP's "opening" colour. Do not spend it on "locked"**, or the two signals fight. |
| `02_film_shots.md:147-150` (F09) | "a plain wood-veneer interior door (brown, dark frame, brass lever)" | The free door is the IP's door, which is today's map door. |
| `03_ip_canon.md:187` | Doors: "wood-veneer frames, solid-core doors · mid oak / walnut · worn kick zone, lever handles". | Same. |
| `01_film_production.md:108` (Sony, S11) | The film's sets had "strange hallways and ill-fitting doors". | A real door that is slightly wrong is on brand (see the "both faces say EMPLOYEES ONLY" note in §6.2). |
| Wikipedia, *Backrooms* (film) [read] | Clark "notices a glowing slit in a wall" "while checking the breaker box". | The way in is in the store's back-of-house utility space. Back-of-house is the IP's threshold. |

---

## 4. Period practice, 1985–1993 US commercial (only what this decision needs; 02 has the rest)

| Element | 1990 practice | Source | Use |
|---|---|---|---|
| Which rooms get which door | Hollow-metal doors go "in stairwells, back entries, corridors, and anywhere security is a concern". Wood doors are "more common inside offices and administrative spaces". | cdfdistributors.com [read]: a modern description of a long-standing practice. SDI 108 lists Storage & Utility, Closet and Mechanical (02 §2.1 [read there]). | Free = veneer office door. Key = steel service door. |
| Storeroom function | F86 (bored): "Dead locking latch bolt operated by key in outside lever [or knob], or by operating inside lever. Outside lever is always inoperable." F07 is the mortise version. | beaconcdl.com [read]; Schlage D Series "Outside knob is fixed", "Entrance by key only" (02 §3.3 [read there]) | The real lock that is always locked from outside and opens only with a key. This is exactly the gameplay. |
| Knob or lever in 1990 | Both. Levers were the accessible standard on public doors (ANSI A117.1-1980, UFAS 1984). Knobs stayed on service doors. Knurled knobs marked doors to hazardous rooms (UFAS 1984 §4.29.3). | 02 §3.1–3.2 [read there] | Lever on the free door, knob on the key door: a 2–5 m silhouette cue (bar against dot). |
| Lock height | "Standard height for horizontal centerline is 39-15/16″ above finished floor" (1.014 m) on a commercial mortise lock. SDI gives the lock strike centreline at 38–42 in and the **deadlock strike at 48 in**. | Yale 8800 instructions [read]; SDI 111A-24 hardware locations [read] | The game's 1.0 m is real. A separate deadbolt would sit at 1.22 m and weaken the head dip. |
| Steel frame | A 2 in face, 5/8 in stop, double rabbet, 16 ga for interiors. | SDI 111A-24 [read] (2024 edition; the profile is long-standing; the 1990 edition was not read) | Frame spec, §6.2. |
| Kick plate | Accessible doors with closers: "cover the door width, less approximately 2 in (51 mm), up to a height of 16 in". Stock height is 10 in. | ADAAG appendix A4.13.9 [read]; 02 §5.4 [read there] | 0.254 m plate, both faces. |
| Sign rules | ADAAG 4.30.6 (1991): **room identification** signs go "on the wall adjacent to the latch side", with the centreline at 60 in. 4.30.5: light characters on a dark ground, or the reverse, non-glare. | access-board.gov ADAAG [read] | "EMPLOYEES ONLY" is not a room identification sign, and 1990 predates ADAAG. A door-mounted plate with no Braille is right for 1990. Keep the 60 in height and the contrast rule. |
| Wired glass | Exempt from the CPSC impact standard from 1977 when used in fire doors. The exemption was removed for schools in 2003 and everywhere by 2006. | safti.com [read]; 16 CFR 1201.1 (02 §6.1 [read there]) | A wired lite in a rated steel door is period-normal in 1990. It also explains why that glass does not break like a window. |
| ADA | Signed 26 Jul 1990. ADAAG was published 26 Jul 1991. New buildings had to comply only from 26 Jan 1993. | 02 §3.1 [read there] | A 1990 back room is pre-ADA: knobs and no Braille are allowed. |

**Era table entries** (to add to `22_era_lock.md` §3 when the models land):

| Asset | Type | Made | Fit |
|---|---|---|---|
| Veneer office door | Flush solid-core wood-veneer door, brass passage lever | 1960–2000 | timeless |
| Storeroom door | Painted hollow-metal flush door, 2 in steel frame, storeroom knob, kick plate, engraved plate | 1960–2000 (door); plate pre-1991 style | timeless; the plate is "current" in 1990 |
| Wired lite (option) | 4 × 25 in polished wired glass, steel lite kit | 1977–2003 for this use | current |

Nothing printed carries a date. There is no maker's name on any rose, knob or plate.

---

## 5. The readability test (in engine, private clone)

### 5.1 Method

- **Harness:** `FrontRoomsLockedDoorReadability`, an editor script in the private clone `proj_int` only. A copy is at [harness/05_FrontRoomsLockedDoorReadability.cs.txt](harness/05_FrontRoomsLockedDoorReadability.cs.txt), and the analysis script is at [harness/05_analyze_readability.py.txt](harness/05_analyze_readability.py.txt).
- **Room:** built with the game's own look-dev room builder (`Assets/Editor/Rendering/FrontRoomsKitLookdev.cs`), with the game's surfaces, troffers, ambient and post stack:
  - an 8 × 22 m room, 2.9 m ceiling, end wall 16 cm thick;
  - three 1.0 × 2.1 openings at −2, 0 and +2 m: **left** the free veneer door, **centre** the candidate, **right** an open doorway into black (an unlit room).
- **Three conditions:**
  - Level 0 lit;
  - Level 0 dim, where the troffers within 6 m of the end wall are removed (like audit frames 39 and 48);
  - Office, with the Office zone grade volume.
- **Camera:** the game's eye (1.62 m) and FOV (76° vertical), at 6, 12 and 20 m, plus a close look at 2.4 m.
- **Doors:** primitive mock-ups at real sizes:
  - leaf 1.0 × 2.1 × 0.045;
  - steel frame face 0.051; wood casing 0.07;
  - kick plate 0.254;
  - sign 0.254 × 0.076 at 1.524 m;
  - knob, rose and lever as in 02 §4.1.
  - These are not the kit models. There is no reflection probe, so every metal reads dark, as it does in the game today (audit F4).
- **Measured:** mean linear luminance (from the PNGs) of fixed regions: the lower leaf of each door, the upper leaf of the candidate, the open doorway, and the wall between the doors.
- **Control:** P1 uses the same veneer as the free door. Its leaf therefore measures the centre slot's lighting bias: +0.26–0.30 stops lit, +0.01 dim, +0.32–0.39 Office. Subtract it when comparing.
- **Unity runs:** three batch runs, all exit 0 (logs in the scratchpad).

### 5.2 Candidates and results

Every pairing uses the same free door: today's veneer leaf, dark casing and brass passage lever.

| Pairing | Key door |
|---|---|
| **P1** hardware only | the same veneer door, plus a brass deadbolt at 48 in (1.22 m) and a small brass tag plate |
| **P2** back-of-house steel | almond-white enamel (sRGB 205, 197, 176) leaf and frame in the same paint, kick plate, dark sign, storeroom lever |
| **P2b** | P2 plus a 4 × 25 in dark wired lite |
| **P2c** | P2 with a dark bronze frame |
| **P2d** | P2c plus the lite |
| **P2p** | P2 in the kit's existing `Prop_SteelPutty` |
| **P3** dark steel | dark bronze enamel leaf and frame (sRGB 59, 46, 37), light sign |
| **P4** office half-lite | veneer door with an obscure-glass upper lite (0.62 × 0.85) and gold-leaf lettering ("PRIVATE"-style) |
| **REC** (final) | P2c with the storeroom **knob** and the zone number plate. REC-lite adds the lite |

Measured at 12 m. The 6 m and 20 m values are within ±0.1 stop of these (all values: `images/05_r1_metrics.json`, `05_r2_metrics.json`, `05_r3_metrics.json`). The first column is bias-corrected.

| Key door | vs free door, stops (lit / dim / Office) | vs wall, stops (lit / dim / Office) | vs open dark doorway, stops (lit / dim / Office) | Read |
|---|---|---|---|---|
| P1 veneer + deadbolt | 0.0 / 0.0 / 0.0 | −0.9 / −0.7 / −1.1 | +3.6 / +1.2 / +4.9 | **Fails.** It is the same door. The deadbolt is 7 px at 6 m and gone at 12 m. |
| P2 / P2c / REC almond steel | **+1.5 / +1.05 / +1.7** | +0.6 / +0.35 / +0.64 | **+5.1 / +2.25 / +6.6** | **Passes** in all lights at 6, 12 and 20 m. In the Office it needs the dark frame (P2c, REC) to keep its outline. |
| P2p kit putty | +0.8 / +0.5 / +1.0 | −0.1 / −0.2 / −0.1 | +4.4 / +1.7 / +5.9 | **Weak.** It melts into the Office wall at 20 m and into the dim L0 wall at 12 m. |
| P3 dark bronze steel | −2.0 / **−0.8** / −2.6 | −2.9 / −1.6 / −3.7 | +1.6 / **+0.3** / +2.3 | **Fails dim.** In a dim cell it is within 0.3 stops of an open dark doorway: a dark rectangle among dark rectangles. |
| P4 half-lite (upper panel only) | +1.4 / +1.0 / +1.9 | −0.9 / −0.7 / −1.1 (lower leaf) | +3.6 / +1.2 / +4.9 | It reads at 12–20 m as a pale square on a brown door. The lower half is the free door. |
| P2b / P2d / REC-lite | as P2, plus a dark slot | — | — | The strongest mark at 20 m: the lite is a vertical dark slot of 3.5 × 22 px. |

Evidence images, native 1080p crops (left: free door, centre: candidate, right: open doorway; columns 6 / 12 / 20 m):
- round 1, all candidates: [L0 lit](images/05_r1_sheet_L0lit.jpg), [L0 dim](images/05_r1_sheet_L0dim.jpg), [Office](images/05_r1_sheet_Office.jpg);
- round 2, frame colour and the kit putty: [L0 lit](images/05_r2_sheet_L0lit.jpg), [L0 dim](images/05_r2_sheet_L0dim.jpg), [Office](images/05_r2_sheet_Office.jpg);
- round 3, the recommended door with and without the lite, all three lights: [sheet](images/05_r3_sheet_recommended.jpg);
- close looks: [L0 lit](images/05_r3_close_L0lit_recommended.jpg), [Office with lite](images/05_r3_close_Office_recommended_lite.jpg);
- the dark-steel failure: [P3 in L0 dim at 20 m](images/05_L0dim_P3_bronze_20m.jpg).

### 5.3 What the test settles

1. **Value beats hue and hardware.**
   - P1 proves hardware cannot carry the read past about 6 m.
   - The Office grade (saturation −22) removes hue cues.
2. **Light, not dark.**
   - The almond leaf separates from the veneer by 2.1–3.3× in every light.
   - Dark bronze separates from the veneer in good light, but in a dim cell it collapses onto the veneer (1.7×) and onto the open doorway (1.2×).
   - That collision with HR03 rule 03 is the deciding fault.
3. **The leaf paint must be lighter than the kit's putty.**
   - `Prop_SteelPutty` renders at luminance 0.345. That is 0.1 stop *below* the wallpaper and only 1.4× the veneer in dim light.
   - The enamel needs an albedo luminance of **≥ 0.50**. The tested almond is 0.56; `Painted_Metal`, the troffer-pan white, is 0.61.
4. **The frame must be dark.**
   - The leaf is only +0.35–0.65 stops above the walls.
   - A same-colour frame lets it bleed into the pale Office wall at 12–20 m; compare rows 1 and 2 in [r2 Office](images/05_r2_sheet_Office.jpg).
   - A dark bronze frame draws the 1.0 × 2.1 outline. It also matches the dark trim every other opening in the map already has (`MapWorld:1785`).
5. **The kick plate reads as a dark foot band in today's renderer.** Metal with no probe renders dark. That is a usable 6–12 m cue now. When reflection probes land (audit F4) it will turn bright. It is still distinct either way, because the free door has no plate.

---

## 6. Recommended pairing: exact visual specs

All parts are render-only (`kit.no_collider()`, per 00).
- The leaf model is a child of `Door hinge {a}-{b}`, with the leaf along hinge +Z (00).
- The gameplay leaf collider stays 0.05 × 2.08 × 0.98.
- The frame is a sibling under the chunk root, so it does not swing (03 §3.3).
- Both types sit on the same gap-free frame/leaf system from the door-gap work (R4), whichever option Red picks there.

### 6.1 Free door: "office door"

| Part | Spec | Slot |
|---|---|---|
| Leaf | Flush, solid-core, 1-3/4 in (0.044 visible thickness), stained veneer. Size and overlap per R4. Close-range detail per 02 §2.1: book-matched seams, a hardwood edge band, grime at 0.9–1.3 m. | `Door_Veneer` (an existing Unity surface; the module registers the slot name with `kitlib.register_slot`, `kitlib.py:132`; the importer maps it to `Resources/Surfaces/Door_Veneer.mat`, `FrontRoomsKitImporter.cs:39-45` in the clone) |
| Frame | Wood jamb and casing: 0.07 face (today's `TrimFace`, `Units:64`) and 0.20 deep. Dark trim value. | `CoveBase` today, or `Prop_WoodWalnut` |
| Lockset | Passage lever, **no keyhole**: rose Ø 0.065–0.085, lever 0.12 long pointing at the hinge, ≤ 0.065 proud. At 1.0 m, 0.08 in from the latch edge, both faces. | `Prop_Brass` |
| Hinges | Per R4: three 4-1/2 in butts at 02 §4.3's heights with Option A, or pivots on the hinge axis with Option B | `Prop_Brass` |
| Not on it | No kick plate, no sign, no number plate, no lite | — |

### 6.2 Key door: "storeroom door"

| Part | Spec | Slot |
|---|---|---|
| Leaf | Flush hollow-metal, 1-3/4 in (0.044 visible), square edges with a 1.5 mm bevel, a faint vertical edge seam on both stiles. Size and overlap per R4. **Almond-white semi-gloss enamel**, sRGB ≈ (205, 197, 176) ±5 %: albedo luminance ≥ 0.50, smoothness 0.45–0.55, metallic 0. Faint orange-peel normal. Hand grime on the latch side at 0.85–1.25 m; scuffs to grey primer just above the kick plate (02 §2.1). | **new surface `Door_Enamel`** (the visual chat creates it next to `Door_Veneer`). Fallback today: the existing `Painted_Metal` surface (luminance 0.61). **Not** `Prop_SteelPutty`/`Prop_SteelAlmond` (both render at 0.34, §5.3). |
| Frame | Pressed steel: 2 in (0.051) face, wrapping the 0.20 jamb depth. Option A: a 5/8 in (0.016) stop. Option B: a cased opening with no stop, per R4. Square 90° returns and no moulding: this is the close-range difference from the wood casing. **Dark bronze** paint. | `Prop_SteelBrown` (existing; renders at luminance 0.03, in the map trim's value) |
| Kick plate | Satin stainless, 0.254 high × (visual leaf width − 0.051), 0.0013 thick, 3 mm above the leaf bottom, **both faces** (the door swings both ways). Part of the leaf mesh. | `Prop_Aluminium` |
| Lockset | **Storeroom key-in-knob, both faces** (game liberty; a real F86 is keyed outside only, 02 §3.3). Rose Ø 0.065 × 0.010; ball knob Ø 0.054 with its face **0.067 proud** (inside the 0.07 limit); knurled band on the outer half of the knob (UFAS hazardous-door knurl, 02 §3.1). Plug face Ø 0.013 at the knob centre; vertical keyway about 2.5 × 8.5 mm (ESTIMATE, 02 §4.2), pins up. Centre at 1.0 m, 0.08 in from the latch edge. A separate asset, so the rattle can twist it. | `Prop_Chrome` (US26D satin chrome); plug face `Prop_Brass` |
| Zone number plate | Per 03 §2.5: 0.10 × 0.05 × 0.003, beside the knob **toward the hinge** (centre 0.13 m from the knob axis, at 1.0 m), never above the knob. Both faces. Each face shows the zone whose key opens it from that side (today's rule, `MapWorld:1698`). The fob's colour and shape family. | `Prop_PlasticRed/Blue/White` plus 03's proposed `Prop_KeyTagNo` digits |
| Sign | A two-ply engraved plastic plate, 10 × 3 in (0.254 × 0.076 × 0.003), with 4 screw dots, centred on the leaf width, **centre at 1.524 m (60 in)**, **both faces**. Dark brown face, sRGB ≈ (48, 36, 30), with ivory core letters (02 §10; ADAAG 4.30.5 contrast). Text: **EMPLOYEES ONLY**, one line, all caps, TeX Gyre Heros Bold (the Helvetica stand-in, `Documentation/FONTS_PERIOD_1990.md`), cap height 19 mm, tracking +40, centred. No Braille (pre-ADAAG), no date, no logo. | **new slot `Prop_SignEngraved`** (one texture cell, which can later hold other engraved plates). Fallback: the plate in `Prop_PlasticBlack` with no text; the far read does not need the text. |
| Hinges | Per R4, in satin chrome or primed and painted to match the leaf | `Prop_Chrome` or the leaf slot |
| Not on it | No closer under Option B (a surface closer cannot work on a double-acting door, 02 §5.3). No padlock, chain, boards, red paint, indicator light or blue tape (§3). | — |

**One sign text everywhere, on both faces.** Per IR05, the copies are the point: the player learns one plate. Both faces of the same door say EMPLOYEES ONLY, so whichever side you stand on, you are the outsider. That is the kind of countable wrongness HR03 rule 01 asks for. It is cheap, because one leaf mesh is mirrored.

**Budget:**
- Leaf asset: 4 slots (`Door_Enamel`, `Prop_Aluminium`, `Prop_SignEngraved`, `Prop_KeyTagNo`), within the kit's ≤ 4 rule (`kitlib.py:30-32`). Flat geometry, about 300–600 triangles, no LOD1.
- Knob asset: 2 slots, about 400 triangles, with an LOD1.
- Frame: 1 slot.
- No lights.

### 6.3 Proposed asset names (final names belong to the kit spec)

Following 03 §3.1 (`Interact_<Thing>[_<Part>]`):

| Door | Leaf | Lockset | Frame | Variant |
|---|---|---|---|---|
| Free | `Interact_DoorOffice` | `Interact_LeverPassage` | `Interact_FrameWood` | — |
| Key | `Interact_DoorStoreroom` | `Interact_KnobStoreroom` | `Interact_FrameSteel` | `Interact_DoorStoreroom_Lite` |

Module files: `assets/interact_door_office.py`, `assets/interact_door_storeroom.py`, and so on.

**Origin convention:**
- Leaf origin on the hinge axis at the floor (hinge-local, 01 §1.6 and 03 §3.1).
- In Blender the leaf runs along **−Y**, so it lands on Unity +Z, with its faces on ±X. The kit exports Blender (x, y, z) as Unity (−x, z, −y) (`kitlib.py:789-794`).

### 6.4 The lite option (`_Lite`), for Red

- **Geometry:** 4 × 25 in visible glass (0.102 × 0.635), in a steel lite kit with a 0.019 face in the leaf paint. The centre is at 1.55–1.60 m (60–66 in, 02 §4.3), on the latch side, 0.24 m from the latch edge. It stays clear of the sign and the knob.
- **Glass:** 1/4 in polished wired glass, square mesh about 1/2 in (pitch UNVERIFIED, 02 §12). It needs a wired-glass slot (02 §10).
- **For:**
  - the strongest 20 m mark (§5.2);
  - a real period detail;
  - a horror beat: the Relay's shape through wired glass.
- **Against:**
  - a hole in the leaf that shows the next room;
  - the Relay's sight ray stops at the leaf collider, so the player sees it but it cannot see the player (02 §6.1);
  - light leaks through it;
  - it needs one more slot.
- **Recommendation:** ship v1 without the lite. Add it only if Red wants the peek, and the map chat agrees on what sight through it means.

---

## 7. Head-dip shot support (Red: "lowering your head to unlock")

**What the model gives the shot** (anchor names per 03 §3.3; hinge-local, t = 0.044 visible leaf):

| Anchor | Value | Note |
|---|---|---|
| `keyhole_px` / `keyhole_nx` | (±(t/2 + 0.067), 1.00, 0.92) = **(±0.089, 1.00, 0.92)** | On the knob face, at the keyway centre |
| `keyhole_*_dir` | 0.10 m into the leaf (∓X) | The key goes in along the knob axis, which is the door normal |
| `keyhole_*_up` | +Y | Pins up, teeth up (02 §4.2; the US convention is UNVERIFIED there) |
| `knob_px_pivot` / `_nx_pivot` + `_dir` | The rose centre on the spindle; `_dir` = outward normal | The rattle twists the knob 3–5° and stops dead. It replaces the lever's "down 20°" in audit §3.4 (02 §4.2). |
| `tagplate_px` / `_nx` | (±(t/2 + 0.003), 1.00, 0.79) | Identity in the close-up |
| `sign_px` / `_nx` | (±(t/2 + 0.003), 1.524, leaf centre) | Above and away from the view cone |
| `kick_px` / `_nx`, `latchbolt` + `_dir`, `pivot_top`, `pivot_floor` | per 03 §3.3 | Shared with the free door |

**Framing check (rendered):**
- Pose P from audit §3.2: 0.45 m out from the keyhole along the normal, eye dropped to 1.35 m, FOV 62. That puts the camera about 0.57 m from the keyhole, looking down about 38°.
- In P, the keyway, knob and number plate sit in the frame centre. The sign (0.52 m higher, 0.43 m toward the hinge) and the kick plate are far outside the 20° view cone.
- Strips, start → mid → P → key in → key turned: [L0](images/05_r3_headdip_strip_L0lit.jpg), [Office](images/05_r3_headdip_strip_Office.jpg); single frame at P with the key in: [P](images/05_r3_headdip_P_key_in_L0lit.jpg).
- The mock key and fob turn as one block. In the real shot the ring and fob hang under gravity (03 §3.2).

**Why the knob at 1.0 m is the right shot:**
1. One keyway on each face. The player's eye knows where the key goes before the camera moves.
2. At 1.0 m the dip is the strongest that still reads as a person lowering their head, not crouching: about 39° down, with the eye at about 1.37 m (03 §3.3).
3. The key enters straight along the door normal into a round face. The 90° turn reads as a rotation of the bow in the frame centre.
4. The storeroom function makes the story literal: the key turns, the latch retracts, the leaf pops ajar (audit §3.2 beats 0.68–1.25 s). Nothing else has to move.

---

## 8. Asks to the other chats

**Map chat (关卡设计)**
1. **A per-door lock flag**, stable per edge across rebuilds: W5, `lockedDoorShare` or the rule Red picks.
   - Spawn `Interact_DoorStoreroom` on locked edges and `Interact_DoorOffice` everywhere else.
   - Keep the names `Door hinge*` and `Door leaf`, and keep the collider (00).
2. **An unlocked key door keeps its storeroom model** (00, 03 §1.7). From a distance, the only "now open" cue is the leaf standing ajar after the unlock (audit §3.2). Please do not auto-close it.
   - If the player shuts it again, it looks locked but opens on E. Red decides whether that is acceptable.
3. **`LockPoint` should read `keyhole_*`.** That is ±0.089 off the leaf centre plane, against today's ±0.055 (`MapWorld:1640-1648`). Then `DoorUnlocked`'s point and the sound come from the keyway (03 §3.3, 02 §4.1).
4. **The Relay breaking a steel door.** Steel dents and the frame tears; it does not splinter. Each type needs its own damage variants (audit §3.7).
   - Optional design lever for Red: steel doors could take longer to break. Default: the same time.

**Visual chat: R4 door gaps and the R3 kit**

5. Build both types on the same gap-free frame/leaf system:
   - the steel frame (`Prop_SteelBrown`, 2 in face) for the key door;
   - the wood casing for the free door.
6. Create the `Door_Enamel` surface (§6.2), and register the `Prop_SignEngraved` slot. Fallbacks: `Painted_Metal`, and `Prop_PlasticBlack` without text.
7. Shot spec: the key-door rattle becomes a knob twist and hard stop (3–5°), not a lever drop. The free door keeps the lever beats (audit §3.3).

**平面视觉 (graphic-visual)**

8. Make the EMPLOYEES ONLY plate artwork in TeX Gyre Heros Bold: dark brown face, ivory engraved letters, 19 mm caps, slight engraving wear. Share the number-plate digits with 03's `Prop_KeyTagNo` atlas.

**声音 (sound)**

9. Steel-door variants of the door events, through a `doorType` parameter on the existing `Mechanism/Door/*` events or new ones:
   - a hollow-metal boom on the stop or slam;
   - a fixed-knob rattle with no lever spring;
   - the storeroom latch drawn by the key.

**Red**

10. Decisions needed:
    - which doors are locked (W5);
    - the lite option (§6.4);
    - whether a shut, already-unlocked storeroom door may look locked (§8 item 2);
    - Option A or B on the door gaps, which decides the frame stop and whether a closer is allowed (02 §5.3).

---

## 9. Open items and UNVERIFIED

1. **Mock-ups, not models.** The test used primitive boxes in the look-dev room, not the map.
   - Lamp spacing and intensity come from `FrontRoomsKitLookdev.Troffers`, not the map's fixtures.
   - Re-run 03 §1.7's test with the real kit models in a real map seed before signing off.
2. **Lighting bias.** The candidate slot sat under more light than the free-door slot: +0.26–0.39 stops, lit and Office. The corrected numbers are given in §5.2. The conclusions do not depend on the bias.
3. **No reflection probe.** Every metal rendered dark: the kick plate, knob and lever (audit F4). When probes land, the kick plate turns bright. Re-check the "dark foot band" cue then.
4. **Two-tone paint (light leaf, dark frame)** as common 1990 practice is art judgement, UNVERIFIED by a dated source. The game reason is the measured outline (§5.3) and the map's existing dark trim.
5. **Door-mounted "EMPLOYEES ONLY" plates** are period-plausible, but UNVERIFIED by a dated catalogue. ADAAG's wall-mounting rule applies to permanent room identification (4.30.6 [read]), and ADAAG postdates 1990 in any case.
6. **SDI 111A** was read in the 2024 edition. That the dimensions match 1990 is assumed (the profile is long-standing).
7. **Resident Evil 2 (2019)** marks its four key doors with card-suit symbols matching the keys. That they are four door types matched to four keys is from gameshedge.com [read]. That the symbols are on the doors comes from search summaries only (UNVERIFIED). It is cited as genre precedent for "door and key share a mark" (our number plate). We do not copy the symbols (HR03 "Not ours to use").
8. **Keyway size, knurl pattern, wired-glass pitch and key dimensions** are ESTIMATES (02 §12). Measure real hardware before final modelling.
9. **Hinge handing and key-turn direction** follow 03 §3.2's picture convention: the top of the key turns toward the hinge edge. The real direction depends on handing (UNVERIFIED).

---

## 10. Sources

**Project files (read):**
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs` (lines 931-936, 1597-1648, 1698-1701, 1785-1788)
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs` (lines 291-295, 350-355)
- `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs` (lines 54-64)
- `Assets/Scripts/FrontRoomsMap/FrontRoomsLevelProfile.cs:31`
- `Assets/Scripts/FrontRooms3DGame.cs:227`
- `Assets/Scripts/FrontRoomsRoomStream.cs` (lines 1209-1275)
- `Assets/Resources/Rendering/FrontRoomsPost.asset`, `FrontRoomsPost_Office.asset`
- `Assets/Resources/Surfaces/*.mat` and `Textures/*_A.png` (albedos measured)
- `Tools/Blender/frontrooms_kit/kitlib.py` (SLOTS, `register_slot`, export axes)
- clone: `Assets/Editor/Rendering/FrontRoomsKitLookdev.cs`, `FrontRoomsHunterLookdev.cs`, `FrontRoomsKitImporter.cs`
- `Documentation/VISUAL_CHAT_TASKS.md` (R4–R6, W5, W6)
- `Documentation/FONTS_PERIOD_1990.md`
- `Documentation/research/office_and_film/22_era_lock.md`, `02_film_shots.md`, `03_ip_canon.md`, `01_film_production.md`
- `Documentation/research/interaction_audit/10_audit_report.md` (§3, F1, §7)
- `04_aaa_references.md`
- audit frames 01, 34, 39, 48

**Figma** (`0tCbAiVUlrPId3RWd9LRif`, read with get_metadata / get_screenshot):
- 2312:852: IR01 2320:2056, IR03 2320:2106, IR04 2320:2141, IR05 2320:2170, IR06 2320:2195
- 2324:852: K00 2324:853, K16 2326:984; frame list
- 2349:852: R44 2350:1286; frame list
- 2331:852: HR03 2331:873

**Web (read):**
- Storeroom function F86/F07: https://www.beaconcdl.com/what-is-a-storeroom-lock/
- SDI 111 (111A-24 hardware locations and frame profiles): https://steeldoor.org/wp-content/uploads/2020/02/SDI_111.pdf
- Yale 8800 mortise lock instructions ("Standard height for horizontal centerline is 39-15/16″"): https://accesshardware.com/wp-content/uploads/2014/08/Yale-8800-Series-Mortise-Lock-is.pdf
- ADAAG 1991 (4.13.9, A4.13.9 kick plates, 4.30.5, 4.30.6, 4.1.1(3) employee work areas): https://www.access-board.gov/adaag-1991-2002.html
- Wired-glass exemption 1977 and its removal in 2003/2006: https://safti.com/was-wired-glass-affected-by-the-new-codes/
- Hollow metal vs wood doors by use: https://www.cdfdistributors.com/blog/post/what-are-the-most-common-types-of-doors-used-in-commercial-buildings
- *Backrooms* (2026 film) plot, the breaker box: https://en.wikipedia.org/wiki/Backrooms_(film)
- RE2 (2019) four key-door types: https://www.gameshedge.com/resident-evil-2-remake-unlock-doors-guide/

**Through the siblings** (read there, not re-read here): UFAS 1984, ADA dates, Schlage D Series functions and sizes, kick plate stock sizes, 16 CFR 1201.1. See 02 §13.

**Evidence produced for this report:**
- [images/](images/) `05_*.jpg` and `05_r*_metrics.json`
- [harness/](harness/) `05_*`
- Unity batch logs: `scratchpad/locked_door/unity_run{1,2,3}.log` (exit 0)
