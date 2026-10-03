# 06 — Period windows: structure and a window family for FrontRooms (R9)

Status: DONE (2026-10-03 10:2x), resumed from the 00:2x pass that stopped after §1. Research and spec only; no kit module was written and nothing was rendered. Nothing in the real project or any Unity clone was changed by this report.

Red: "build the window's STRUCTURE too, not just a pane of glass — research what windows made sense in that era."
Red (relayed, 2026-10-03): ChatGPT built an independent ray-traced glass path; understand it and add it as a task. §5 covers what it means for windows and gives the task row.

Binding inputs: `00_map_constraints.md` (obeyed everywhere below), `../office_and_film/22_era_lock.md`, `../interaction_audit/10_audit_report.md` §3.5–3.6 and §4, `02_period_hardware.md` §6–7 and §10, `03_readability_placement_shots.md` §3.5, `04_door_re8_gap.md` §4, `05_locked_door_type.md` §1 and §6, `../glass/10_implementation.md` §8, `Documentation/VISUAL_CHAT_TASKS.md` rows R7, R9, R10, G5, G8–G13, GD1–GD3.

Tags: **[read]** = I read the page or file (this pass, or the 00:2x pass whose downloads are in `scratchpad/win06/` and which I re-read now). **[search]** = only a search-engine summary; treat as UNVERIFIED. **ESTIMATE** = a designer number with no source. **Modern catalogue, timeless form** = a current product sheet for a design that existed in 1990.

---

## 0. Decision

**One window family, four members, one per level. Every member uses the door kit's frame grammar** (`04` §4.1 sleeve, `05` §6): the same casing/face band round the opening, a 2 mm lining over the bare reveal, and real 16 mm stops. The members differ by material, which is also how the doors differ.

| Member | Where | What it is (period alibi) | Frame | Glass | Extra |
|---|---|---|---|---|---|
| **W-L0 "back-office light"** | Level 0 / Lobby / Shift rooms, so every map window whose non-tall side is Level 0 | A fixed interior window in the store's older back rooms (built 1955–85, still there in 1990). Same trim as the free veneer door | Stained dark wood: jamb liner, casing on both faces, **through-stool with horns and an apron on both faces**, wood glazing stops | 1/4" (6 mm) clear float, annealed look | Option: hammered obscure glass (§3.1) |
| **W-OF "office borrowed light"** | Office rooms, so every map window whose non-tall side is Office; also the target look for `Kit_InteriorWindow` | A 4-sided pressed-steel borrowed-light frame, SDI profile, same frame and paint as the key door | **Dark-bronze painted steel**, 4 sides, integral stop on the hall face, **screw-fixed removable stop on the office face** (30 oval-head screws) | 1/4" clear float, annealed look | Optional **raised 1" aluminium mini-blind** on the office face (§3.2) |
| **W-RN "corridor wire light"** | Run (Level !, white hospital corridor). No map windows yet | The same steel frame in institutional white enamel | W-OF mesh, slot swap only | **1/4" polished wired glass** (Georgian square mesh) or, v1, plain clear | Wired glass changes the break: Red's call (§3.3) |
| **W-EX "aluminium office front"** | Exit. No map windows yet | Clear-anodised aluminium that wraps the wall, snap-in bevelled beads, black vinyl gaskets | **Clear anodised aluminium** | 1/4" clear | — |

How it fits the opening (§4):
- The gameplay opening stays 1.4 × (0.35–2.0) and the pane collider stays 1.4 × 1.65 × 0.03 on the wall line. Everything here is render-only (`kit.no_collider()`).
- **The one thing I need from the map chat is a rule clarification:** real stops must stand 16 mm into the opening, because the wall cut *is* the opening and the reveal behind it is solid wall. I ask for a render-only 16 mm stop band round the opening (§4.1). Without it, the frame can only show a flat lined reveal with a dark slot, which loses the "structure" Red asked for.
- The visible glass is a separate 6 mm slab, 1.391 × 1.642, held 12 mm behind the stops. It sits wholly inside the gameplay pane box. The map spawns it as a render-only child of the pane (§4.3), so it dies with the pane on break, carries `Glass_Window`, and carries the ray-tracing target (§5).
- Teeth: the glass pocket behind the stops is the tooth socket. Teeth may show past the stop line only if the map chat accepts `03`'s tooth band (≤ 0.10 m from the opening edge at jambs and head, ≤ 0.04 m at the sill, §4.4).

What this report does **not** do:
- It does not build the fracture meshes. `VISUAL_CHAT_TASKS.md` G8 moved remnants to the glass-destruction plan (GD1/GD3). §4.4 gives GD3 the exact pocket, slab and tooth-band numbers.
- It does not write kit modules. §3 gives the profiles in kit terms for the build stage.

---

## 1. What the game builds today (code facts)

Short names as in `05`: `MapWorld` = `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `Map` = `…/FrontRoomsMap.cs`, `Units` = `…/FrontRoomsModuleUnits.cs`, `Stream` = `Assets/Scripts/FrontRoomsRoomStream.cs`. Line numbers are the real project as read on 2026-10-03 09:5x. The map chat keeps editing `MapWorld` (it has uncommitted changes now), so they drift.

### 1.1 Map windows

- **Where.** A window is built on any edge where a Tall zone meets a Low or Standard zone (`Map:366`). Only Standard zones can roll the Office theme (`Map:306-307`), so tall halls are always Level 0. Every map window therefore has **a Level 0 tall hall (5.4 m) on one side**, and a Level 0 room (2.4 or 2.9 m) or an Office room (2.9 m) on the other. The theme of each side is known when the edge is built.
- **Opening.** 1.4 wide, centred on the 3 m edge, sill 0.35, head 2.0 (`Units:61`; `MapWorld:986-995`). The wall below the sill is a solid wall piece; its top face is bare wallpaper (`MapWorld:996`). Wall 0.16 thick (`Units:41`).
- **Trim.** Two jambs, 0.07 face × 0.20 deep, from the sill to the head, with their inner faces exactly on the opening edges; a head 1.54 × 0.07 × 0.20 from 2.00 to 2.07 (`MapWorld:999-1009`; `TrimFace .07`, `TrimProud .02`, `Units:64`). Material `Cove_Base` (`MapWorld:2067`). All trims of a 6 m block are merged into one renderer, so the kit cannot hide one window's trims. **No stop, no glazing bead, no bottom member, no stool, no apron.** The trims' inner faces are coplanar with the wall's end faces (the z-fight `04` §1.1 found at doors).
- **Pane.** A primitive cube `Window pane {a}-{b}`, 1.4 × 1.65 × **0.03**, centred on the wall line, a child of the chunk root with no rotation; its scale axes swap with the edge direction (`MapWorld:1042-1052`). Material built in code: URP Lit, transparent, premultiplied, base (.75, .85, .88, .28), smoothness .9 (`MapWorld:2070, 2073-2088`). Since 01:42 today it also gets `FrontRoomsMetalGlassTarget` (`MapWorld:1049`, §5).
- **Break.** At 1.0 s of hold, `Kill(window.pane)` destroys the pane and its children, then `GlassBroken(position)` fires (`MapWorld:1891-1904`). A broken window's pane is not rebuilt (`MapWorld:1042`); the trims still are, because they are built before that return. No remnants, no floor glass.
- **No window root.** Nothing unscaled marks the opening. `01` §2.5 proposes a `Window {a}-{b}` root at the opening centre, on the wall line, at floor level, local +Z into cell b. This report uses that frame: opening X ±0.70, Y 0.35–2.00; wall faces Z ±0.08; map trim faces Z ±0.10.

### 1.2 `Kit_InteriorWindow` (Office decor)

- `Tools/Blender/frontrooms_kit/assets/interior_window.py:1-33`: a dark-bronze 50 × 85 mm steel frame, 2.40 × 1.22, one undivided 6 mm pane in snap-in glazing beads with black gaskets, a steel sill nose with horns. Wall-mounted, single-sided, no collider. Pane slot `Prop_GlassCRT` (opaque black). Frame slot `Prop_SteelBlack`.
- Placed by `FrontRoomsOfficeKit` (`Assets/Scripts/Office/FrontRoomsOfficeKit.cs:58`), sill 0.90 target (`Documentation/LEVEL_MODULE_SPEC.md:120`).
- The black-slab pane is open task T15 / G5 (`VISUAL_CHAT_TASKS.md`).

### 1.3 Title stream rooms

- `Stream` builds **no windows** (no window or glass geometry in `FrontRoomsRoomStream.cs`).
- Its doors are flush double doors with brushed-steel bar handles and kick plates on both faces (`Stream:1254-1271`), material "Door / brushed steel" (`Stream:1403`).
- Room rules: Lobby, Shift, Office, Run, Exit (`Assets/Scripts/FrontRoomsRoomRule.cs:5`). Run is "Level !: a white hospital corridor, dim except for the red" exit signs (`Stream:1442`). The older `Documentation/BACKROOMS_VISUAL_SPEC.md:12` still says red paper; the code is newer, so I follow the code. Exit is blue-green paper with cool light (`BACKROOMS_VISUAL_SPEC.md:13`; `Stream:1358`).

### 1.4 What this means

- Every live breakable window today is a **Level 0 ↔ Level 0** or **Level 0 ↔ Office** window: a back room or an office that looks into a tall hall.
- Run and Exit windows do not exist yet. Their members are specified so the family is complete, at lower priority.
- The kit importer remaps any slot name to `Assets/Resources/Surfaces/<slot>.mat` when that material exists (`Assets/Editor/Rendering/FrontRoomsKitImporter.cs:36-43` in the clone). So a window module can use `Cove_Base`, `Door_Veneer`, `Painted_Metal` (all in `Assets/Resources/Surfaces/` today) or `Door_Enamel` once it exists, through `kitlib.register_slot(...)` (`kitlib.py:132`), with no edit to `kitlib.py`. This is the mechanism `05` §6.1 uses for `Door_Veneer`.

---

## 2. Period research (US commercial interiors, 1985–1993, with older stock back to 1955)

### 2.1 What an interior window was, and where a 1990 building had one

- The trade name is **borrowed light** (or relite / vision light): "a glazed opening frame installed in an interior partition prepared for field installation of stationary (fixed) glazing" ([search], Allegion knowledge base summary). Fixed glass, no sash, no hardware.
- Older office buildings had them on purpose: "In offices, the corridor doors and sometimes internal openings contained glazing, which also transferred natural lighting from the office to the hallway" (NPS ITS 31 [read]). The same note records the fire-code fate of such glass: it may be kept "if set in a metal frame with wireglass" (NPS ITS 31 [read]).
- In 1980s fit-outs they came in three construction families, which map onto FrontRooms' existing door split:

| Family | Period evidence | Who in FrontRooms |
|---|---|---|
| **Wood**: jamb liner, casing, stool and apron, wood stops | Older buildings; NPS ITS 31 describes corridors "distinguished by mahogany trim around openings" with "interior sidelight windows" [read]. Stool, apron, casing and horns are standard carpentry (This Old House [read]) | W-L0 (matches the free veneer door's wood casing, `05` §6.1) |
| **Hollow metal (pressed steel)**: a frame that wraps the wall, integral stop on one side, screw-applied removable stop on the other | SDI 111A standard profiles [read]; the UH master spec [read]; a 1998 Steelcraft-based spec references ANSI/SDI 100 [read]. Form unchanged since well before 1990 (timeless form) | W-OF and W-RN (matches the key door's 2" steel frame, `05` §6.2) |
| **Aluminium**: extruded frames and snap-in beads with elastomeric splines, in partitions | US Gypsum patent US4463535, filed 1982, granted 1984: a demountable glass stop "for installation in interior partition walls with borrowed lights or side lights", for "full or cornice height partitions" and "partially glazed bank rails", glazing tempered glass with an elastomeric spline [read]. US4443984 (filed 1981, granted 1984): aluminium casing extrusions that wrap drywall partitions at doors and windows, with a flat web "masking the margin" of the opening [read]. Kawneer's TRIFAB 450 storefront framing: trademark filed 1969 [search]; today 1-3/4" sightline × 4-1/2" depth, glass front, centre or back set [read, modern catalogue] | W-EX; also the existing `Kit_InteriorWindow` |

### 2.2 Hollow-metal frames: the numbers

From SDI 111A-24 "Standard Profiles" (page render read in `scratchpad/win06/sdi111/p05.png`) [read]:
- **2" (51 mm) face**; **5/8" (16 mm) stop**; **1/2" (13 mm) return** typical; "7/16" Return Typical for 5-3/4" Jamb Depth" (so the face stands about 11 mm proud of a 4-7/8" wall); "16 gauge steel is typical for interior"; an optional **4" face** for heads; a **cased open** profile with no stop.
- The 2" face and 5/8" stop agree with `02` §2.2 and §6.2.

From the University of Houston master spec 08 11 13 (2014; modern spec, timeless form) [read]:
- Borrowed-light frames: "Fire Rated, Borrowed Light Assemblies: Complying with NFPA 80"; frames of "0.042 inch" (18 ga) minimum steel; exposed finish "Prime" (field-painted).
- Stops: "Single Glazed Lites: Provide fixed stops and moldings welded on secure side of hollow metal work"; "Provide loose stops and moldings on inside of hollow metal work"; "Form corners of stops and moldings with [butted] [or] [mitered] hairline joints".
- Fasteners: "Secure stops with countersunk flat or oval head machine screws spaced uniformly not more than 9 inches o.c. and not more than 2 inches o.c. from each corner."
- Mullions and transom bars: "closed tubular members with no visible face seams or joints".
- Glass size: "Glass Cutting Size (GCS) is determined by adding 1 1/4" to Exposed Glass Size (EGS)" ([search], Allegion summary), i.e. about 5/8" of glass hidden behind each stop.

**What the game takes from this:** a pressed-steel sleeve with crisp 1.5 mm bends and no moulding; a 16 mm stop on both faces; the screw-fixed stop on the "secure" (room) side and a plain welded stop on the hall side; 30 visible oval-head screws on the room face at ≤ 229 mm (9") centres, ≤ 51 mm (2") from the corners; glass about 12–16 mm into the pocket.

### 2.3 Aluminium and its finishes

- **Integral-colour bronze anodising** (Alcoa "Duranodic") was introduced "in the early 1960's" and "was commonly used in the coloring of aluminum storefront systems"; the current 2-step electrolytic colouring arrived "in the early 1970's" (SAF [read]). So clear and bronze anodised aluminium were both ordinary by 1990.
- Today's standard architectural colours: clear, champagne, light, medium and dark bronze, black; Class II (thinner) "generally is suited for interior applications" (Alumicor [read], modern).
- Kawneer 1988 patent US4841700: conventional thermal storefront framing then had "typical face dimensions … of 2.25 and 2.50 inches", and the goal was a smaller "sight line" [read].
- Kawneer's own bevelled stops: "Standard 1/4" beveled glass stops" ([search], Kawneer summary).

### 2.4 Glass

| Glass | 1990 status | How it breaks | Source |
|---|---|---|---|
| **1/4" (6 mm) clear float, annealed** | The ordinary glass. Float replaced plate glass in the 1960s ("Full scale profitable sales of float glass were first achieved in 1960") | Long irregular shards; edge pieces stay in the stops as teeth | Wikipedia, Float glass [read]; `02` §7 |
| **Tempered** | Required in doors (16 CFR 1201, 1977) and in code "hazardous locations"; the 1982 USG partition patent glazes interior borrowed lights with tempered glass | All at once, into ~1 cm granules; no crack stages | `02` §7.1; US4463535 [read] |
| **Polished wired glass, 1/4"** (Georgian square or diamond mesh) | Fire-rated walls and doors; also sold as "non-rated decorative glazing". By 1992 no longer made in the US: "Wired glass is no longer produced in the United States" (UFGS 08 81 00 note on a 17 March 1992 ruling) | Cracks like annealed glass, but "the broken pieces are retained by the wire mesh and do not fall out"; "Wired glass cannot be tempered" | General Glass [read]; UFGS 08 81 00 [read]; Designing Buildings, Wired glass [read]: "grid size of around 12.5mm" |
| **Patterned (obscure) glass** | "normally provided for windows of toilet rooms … borrowed light sash at entrances"; "When used for interior partitions, place the patterned surface in same direction in all openings" | Like annealed; the texture hides the crack lines at a distance | UFGS 08 81 00 [read] |

Edge colour: "Ordinary float glass is green in thicker sheets due to Fe2+ impurities" (Wikipedia [read]); `Glass_Edge` already uses that (`../glass/10_implementation.md` §3).

**Size limits for rated glass** (only matters for W-RN): NFPA 80 "limits the maximum size of each glass light to 1296 square inches with no dimension exceeding 54 inches" (idighardware [read], quoting a modern edition; the 1990 edition's value is UNVERIFIED). The map pane is 1.4 × 1.65 m = 3,580 sq in and 55" wide, so **a fire-rated version would need a mullion**, which cannot sit in the climb opening (`00`). W-RN is therefore a *non-rated* wired light (§3.3).

**Legality of the annealed look.** `02` §7.1 already showed that a 1.4 × 1.65 pane with a 0.35 m sill meets today's four-part hazardous-location test, so a code-built pane would be tempered. Whether the late-1980s model codes had the same test is still UNVERIFIED (the building-code forum thread that discusses it returned 403 to me). The annealed look stays what `02` and the audit called it: an art-direction choice with a period alibi (glass in an older building, pre-code).

### 2.5 Hardware and window coverings

- Borrowed lights are **fixed**: no latches or handles. The only "hardware" a 1990 person would see is the stop screws on the room side (§2.2).
- **Horizontal 1" aluminium mini-blinds were the default window covering by 1990.**
  - "The '70s began the era of the mini-blind … In 1981, mini-blinds were 70 to 80 percent of the U.S. market in window coverings" (Wikipedia, Mini blind [read]; Encyclopedia.com gives the same 70–80 % [read]).
  - In October 1984 the trend piece was already about the next step, the half-inch "micro-mini", "since the introduction of one-inch-wide mini blinds some years ago" (Christian Science Monitor, 19 Oct 1984 [read]).
  - The 1993 Sears Annual Home Catalog (the source of Figma's REAL vs MODEL pages) sells "Levolor 1-inch aluminum mini-blinds" with "baked-on enamel finish", "Steel headrail; bottom rail has plastic sill guards", in colours including Almond, Alabaster, Winter white and "Polished bright aluminum" [read, Internet Archive full text, local copy `scratchpad/win06/sears1993_djvu.txt`].
  - 平面视觉's binding era note for the kit names "1-inch aluminium mini-blinds" (`VISUAL_CHAT_TASKS.md` R10).
  - Dimensions (Levolor Riviera commercial guide; modern catalogue, timeless form) [read]: slat 1" × 0.008" gauge; headrail 1-3/8" × 1-3/8" (35 × 35 mm); bottom rail 1-1/2" × 1-1/8"; ladder spacing 22 mm; outside-mount return 1-3/4" (44 mm); **stacking height** 4-5/8" for a 60" blind and 5" for a 72" blind; wand 30" for a 37–52" blind, 40" for 52–67", 50" for 67–82".

### 2.6 What the IP adds

- Canon windows are "dead": blacked out, black mirrors, rain on fog, or absent; "un-blacked windows are framed as a hazard" (`../office_and_film/03_ip_canon.md:75, 122`).
  - The map's windows are exactly that hazard: breaking one is the loudest noise in the game (`10_audit_report.md` §3.6).
  - The Office decor window stays dark (`03_ip_canon.md:242`, T15).
- HR03's rules (as quoted in `05` §1): "a half-remembered ordinary thing from the set's own year" and countable wrongness. The 1" mini-blind is the most "1990" object a window can carry, and one identical bent slat in every Office blind is a countable wrongness. Both are suggestions, not decisions.

---

## 3. The window family

### 3.0 Shared grammar (what windows take from the doors)

| Element | Doors (`04`, `05`) | Windows (this report) |
|---|---|---|
| Frame sleeve | Casing 0.075 face, 0.025 proud, encloses the map trims; 2 mm linings over the bare reveal, set 0.5 mm into the opening to kill the z-fight (`04` §4.1) | **The same sleeve section**, run round the window: jambs and head always; the sill is per member |
| Stop | Option A: 16 mm SDI stop (`04` §6.1, Red chose A, `VISUAL_CHAT_TASKS.md` W6) | 16 mm glazing stops on **both** faces, all four sides |
| Wood member | Free door: veneer leaf, wood casing in the dark trim value, brass lever (`05` §6.1) | W-L0: same casing profile and slot; stool and apron |
| Steel member | Key door: 2" pressed-steel frame, **dark bronze** (`Prop_SteelBrown`), square returns, no moulding (`05` §6.2) | W-OF: same steel profile and slot; the screw-fixed stop is the window's "hardware read" |
| Asymmetry | The key door's sign and knob face both rooms | Face A (kit −Y, Unity +Z) = the room side, with the screws and the blind; face B = the tall-hall side. The map rotates the asset so face A looks into the non-tall cell |

**Sleeve mode vs true mode.**
- **Sleeve mode (v1, no map change):** every member's face band is 0.0755 wide and stands 0.025 proud, so it encloses the map's 0.07 × 0.02 trims (`MapWorld:999-1009`). A real steel face is 2" (0.051) and 7/16" (0.011) proud, so in sleeve mode the steel member is a bit heavy. That is the same compromise `04` made for doors.
- **True mode (after the optional map change in §6):** the map stops building trims on window edges, and the steel member uses the real 0.051 face / 0.011 return, the wood member a real 11/16" casing.

All numbers below are metres in the window root frame (§1.1): X along the wall (opening ±0.70), Y up, Z across (+Z = face A after rotation). Sleeve mode unless stated.

### 3.1 W-L0 "back-office light" (Level 0, Lobby, Shift)

**Alibi.** A fixed interior window in the store's older back rooms: a wood-cased opening with a stool, built in the second-hand era (1955–85, `22_era_lock.md` §2) and still in use in 1990. It wears the same wood trim as the free veneer door, so a player learns "wood = the building's own rooms".

| Part | Spec (sleeve mode) | Note |
|---|---|---|
| Jamb liner and head liner | 19 mm stock. Visible inner face at \|X\| = 0.6995 (head Y 1.9995), spanning Z ±0.1005 | Covers the bare wall ends and the map trims' inner faces |
| Casing (both faces) | Section 0.0755 wide (X 0.6995→0.775) × 0.025 proud (Z 0.080→0.105). Ranch-style back-bevel: front at Z 0.105 over the outer 25 mm, falling to Z 0.1005 at the inner edge; 1.5 mm eased arrises; mitred at the head corners. Jambs Y 0.3505→2.075; head X ±0.775, Y 1.9995→2.075 | Must stay ≥ Z 0.1005 over X 0.70–0.77 to hide the trim face. This is the free door's casing (`05` §6.1); if the door spec fixes a different profile, use that one |
| **Through-stool** (one board, both faces) | X ±0.800 (horns 25 mm beyond the casing, "add … 2 inches total for horn projection", This Old House [read]); Z ±0.121 (16 mm beyond the casing face); Y 0.3255→0.3505 (25 mm). Half-round nosing on both long edges | Its top **is** the sill: it replaces the bare wallpaper top of the wall piece (`MapWorld:996`), 0.5 mm high to avoid the z-fight. Jamb casings land on it |
| Apron (both faces) | Casing profile, X ±0.775, Y 0.250→0.3255, Z 0.080→0.105, ends returned | Under the stool nose |
| Glazing stops (both faces) | 16 × 16 mm square bead with a 3 mm ovolo on the exposed arris; Z ±(0.006→0.022); stop line \|X\| 0.6835, Y 0.3665 / 1.9835; mitred | §4.1 |
| Glass | §4.3 slab, 6 mm clear, annealed look | Option: hammered obscure glass, patterned face toward the tall hall on every window ("same direction in all openings", UFGS [read]). It turns the hall and the Relay into blurs. **Red's call**: it changes what the player can see through the window |
| Slot | One: the free door's casing slot (`Prop_WoodWalnut`, or `Cove_Base` via `register_slot` if the door spec keeps the map trim colour) | 1 renderer, 1 draw |
| LOD0 detail (0.3 m hero) | Grain runs along each piece and turns at the mitres; stain pooled in the bevel; dust on the stool top and in the stop corners; one stop bead with a split end (ESTIMATE, texture) | |
| Budget (ESTIMATE) | LOD0 ~1,400 tris, LOD1 ~550 (drop ovolo and nosing segments), LOD2 ~150 (boxes) | |

### 3.2 W-OF "office borrowed light" (Office)

**Alibi.** The office fit-out's steel: a 4-sided SDI borrowed-light frame, dark bronze like the key door's frame and the existing `Kit_InteriorWindow`. Screws on the office side, because the removable stop goes on the "secure side" (§2.2).

| Part | Spec (sleeve mode) | True mode |
|---|---|---|
| Frame | One pressed-steel section run round all four sides: face band X 0.6995→0.775 on both wall faces at Z ±0.105; outer return (backbend) at X 0.775 from Z 0.105 back to the wall at 0.080; soffit at \|X\| 0.6995 (sill Y 0.3505, head Y 1.9995) spanning Z ±0.105; all bends 1.5 mm inside radius. Sill band Y 0.2745→0.3505 and head band Y 1.9995→2.075 on both faces. Mitred corners with hairline joints | Face 0.051 (X 0.6995→0.7505), return 0.011 (Z 0.080→0.091) |
| Integral stop (face B, hall side) | A formed rib: Z −0.022→−0.006, 16 mm proud of the soffit, same bend radii, continuous round the corners | same |
| Removable stop (face A, office side) | A 16 × 16 mm channel bead, Z 0.006→0.022, mitred hairline corners | same |
| **Screws** (face A) | Countersunk oval heads, Ø 7 mm, 1.5 mm dome, slotted, on the bead's inner face. Jambs: 8 each, first and last 0.051 from the stop-line corners (Y 0.4175 and 1.9325), 0.2164 apart. Head and sill: 7 each, X ±0.6325, 0.2108 apart. **30 in all** (UH spec: ≤ 9" o.c., ≤ 2" from corners [read]) | same |
| Glazing tape | A 1.5 mm black line where glass meets each stop, both faces | `Prop_Rubber` (2nd slot) |
| Glass | §4.3 slab | |
| Slots | `Prop_SteelBrown` (the key door frame's slot, `05` §6.2; renders in the map trim's value) + `Prop_Rubber` | 1 renderer, 2 submeshes |
| LOD0 detail | Orange-peel enamel normal; paint worn to grey primer on the sill soffit and the stop corners; a paint-filled screw slot here and there; hairline mitre seams | |
| Budget (ESTIMATE) | LOD0 ~1,800 tris (30 screws ≈ 700), LOD1 ~600 (screws dropped), LOD2 ~150 | |

**Raised mini-blind (optional, face A only): `Interact_MiniBlindRaised`.**
- A separate render-only asset the map places on the office face of Office windows (share by edge hash, e.g. 0.6; ESTIMATE).
- Head rail 0.035 × 0.035 × 1.55 (X ±0.775), outside mount on box brackets with spacer blocks (the Riviera guide's "Spacer Blocks … to clear obstructions, such as window moldings" [read]): **Y 2.160→2.195**, Z 0.110→0.145. It needs a ceiling ≥ 2.2; Low zones are 2.4.
- Raised stack of 1" slats, 0.025 deep, Z 0.115→0.140, **Y 2.035→2.160** (≈ 5" for this ≈ 70" drop, from the Riviera table); bottom rail 0.038 × 0.029 at **Y 2.006→2.035**. So the lowest part stays above the head line at 2.0, and the whole blind stays in front of the head band (Z ≤ 0.105).
- Tilt wand Ø 8 mm hex, clear, from the rail at X +0.72 (over the face band, outside the opening's X range) down 1.02 m (40" wand) to Y 1.14. Lift cords and tassel at X +0.74 down to Y 1.20.
- Ladder strings visible at 22 mm pitch at the stack ends.
- Slots: slats and rails `Prop_SteelAlmond` (baked enamel on aluminium, "Almond" from the Sears 1993 colour list) + wand/cords `Prop_PlasticWhite`. About 1,200 tris LOD0 (the stack as ~12 grouped slabs with a slat normal map), LOD1 ~300.
- One deliberately bent slat at the same index in every blind (HR03 countable wrongness, §2.6); Red's call.
- **Never lowered on a breakable map window**: a lowered blind would hang in the opening and over the break. A lowered and half-tilted variant is fine on `Kit_InteriorWindow`, which is decor.

**`Kit_InteriorWindow` alignment (decor, G5).** Its section is already an aluminium/steel office front. To make it read as the same family:
- add a `VARIANTS` entry `Kit_InteriorWindow_Bronze` that swaps `Prop_SteelBlack` → `Prop_SteelBrown` (no new mesh);
- give it the lowered mini-blind variant;
- G5 moves its pane onto `FrontRooms/Glass`.

### 3.3 W-RN "corridor wire light" (Run)

- **Frame:** the W-OF mesh with one slot swapped through `VARIANTS`: `Prop_SteelBrown` → institutional white enamel (`Door_Enamel` once the visual chat creates it, `05` §6.2; fallback `Painted_Metal`, which exists). No blind (none of the period sources puts a blind in a hospital corridor; ESTIMATE).
- **Glass:** 1/4" polished wired glass, square mesh at about 12.5 mm (Designing Buildings [read]; `02` §7.3 had it as UNVERIFIED 1/2", which matches). It needs a `Glass_Wired` material: the `Glass_Window` shader plus a wire grid in the albedo, normal and a little roughness. That is a new material for the visual chat to make, not a kit slot.
- **It cannot be a legal rated window** at this size without a mullion (§2.4). The alibi is a non-rated wire light. General Glass sells wire glass as "non-rated decorative glazing" [read].
- **The break is the problem.** Wired glass does not fall out. The physically right sequence is:
  1. the hold cracks it through all stages;
  2. the "shatter" leaves the sheet sagging on the wire;
  3. a second hold, or the Relay, tears the sheet out, leaving wire stubs in the stops.
  That is a gameplay change (a two-stage break) for Red and the map chat.
- **v1 recommendation:** ship W-RN with plain clear glass and the annealed break, and keep wired glass as Red's option. This is moot until Run has map windows.

### 3.4 W-EX "aluminium office front" (Exit)

- **Frame:** a clear-anodised aluminium wrap casing in the US4443984 manner [read]: a flat web masking the opening margin on both faces, same sleeve envelope (X 0.6995→0.775, Z ±0.105). Extrusion read: crisp 0.5 mm edges, and a 6 mm shadow groove in the face band 0.040 from the opening edge. Four-sided, the sill band like the head band.
- **Stops:** snap-in aluminium beads on both faces, 16 × 16 mm, with a 45° bevelled top (Kawneer "1/4" beveled glass stops" [search]), and a black vinyl gasket wedge showing 3 mm against the glass on both faces (USG 1982 elastomeric spline [read]).
- **Glass:** 1/4" clear (tempered in the real thing; annealed look in game for one consistent break). Tempered granules would be a cheap way to make the true exit's glass behave differently, if Red wants a tell.
- **Slots:** `Prop_Aluminium` (metallic, roughness 0.35, reads as clear anodised) + `Prop_Rubber`. Under the Exit's cool light (`Stream:1358`) it reads silver-cyan, distinct from every other member.
- **Budget:** LOD0 ~1,500 tris, LOD1 ~500.

### 3.5 Proposed asset names (final names belong to the kit spec)

| Asset | Module file | Members |
|---|---|---|
| `Interact_WindowFrameWood` | `assets/interact_window_frame_wood.py` | W-L0 |
| `Interact_WindowFrameSteel` + `VARIANTS` `Interact_WindowFrameSteel_Enamel` | `assets/interact_window_frame_steel.py` | W-OF, W-RN |
| `Interact_WindowFrameAlu` | `assets/interact_window_frame_alu.py` | W-EX |
| `Interact_MiniBlindRaised` (+ `_Lowered` for decor) | `assets/interact_mini_blind.py` | W-OF option; `Kit_InteriorWindow` |

- `03` §3.5 used a single `Interact_WindowFrame`. These are its per-level split.
- Origin for all frames: the window root (opening centre, wall centre line, floor). In Blender the wall plane is XZ at y = 0, the wall runs ±0.08 in y, and **face A is −y** (Unity +Z, `kitlib.py` export maps (x, y, z) → (−x, z, −y), `05` §6.3).
- Tags in the sidecar: `window`, `frame_wood` / `frame_steel` / `frame_alu`. The sound chat can key `ClimbSill` and `ToothSnap` on these if it wants a wood/steel difference (`10_audit_report.md` §3.6).

---

## 4. Fit to the map opening: sections, glass, break zones, anchors

### 4.1 The stop problem, and three ways to solve it

The map cuts the wall exactly to the 1.4 × 1.65 opening (`MapWorld:993-996`). The reveal behind that edge is solid wall. A real borrowed light hides the glass edge behind stops that stand **into** the clear opening, so with this wall cut:
- either the stops stand 16 mm into the opening,
- or the stops are not visible at all.

| Option | What it looks like | Map work | Gameplay effect |
|---|---|---|---|
| **S1: a 16 mm render-only stop band (recommended)** | Real stops on both faces; exposed glass 1.367 × 1.617 (Y 0.3665–1.9835) | None. A rule clarification: "render-only frame parts may occupy a 16 mm band inside the opening edge" | None. Nothing collides; the climb camera and the Relay's 0.3 m body stay far from the edges. The pane collider and the climb trigger are unchanged |
| S0: flush, no intrusion | Lined reveal with a dark 12 mm "gasket" strip where the glass meets it; no stops | None | None, but it loses the structure Red asked for, and from an angle the glass appears to die into the wallpaper line |
| S2: map widens the wall cut by 16 mm per side | Real stops, with the exposed glass exactly 1.4 × 1.65 | Wall cut 1.432 × (0.334–2.016); the pane collider must grow to match, or 16 mm see-through slits open round it for the Relay's sight ray and the E ray | Breaks "keep the pane collider exactly". Not recommended |

`03` §3.5 already asks for a render-only tooth band (≤ 0.10 m at jambs and head, ≤ 0.04 m at the sill). The S1 stop band is inside that band. The map chat can approve both at once.

### 4.2 Section summary (S1, sleeve mode, all members)

| Item | Jambs (X) | Head (Y) | Sill (Y) | Across (Z) |
|---|---|---|---|---|
| Opening edge (wall cut) | ±0.700 | 2.000 | 0.350 | wall ±0.080 |
| Lining / soffit visible face | ±0.6995 | 1.9995 | 0.3505 (stool top on W-L0) | ±0.1005 (wood) / ±0.105 (steel, alu) |
| Glass edge (in the pocket) | ±0.6955 | 1.996 | 0.354 (on 3.5 mm setting blocks) | glass ±0.003 |
| Stop line (exposed glass edge) | ±0.6835 | 1.9835 | 0.3665 | stops ±(0.006→0.022) |
| Face band / casing | 0.6995→0.775 | 1.9995→2.075 | W-L0: stool + apron; others: 0.2745→0.3505 | 0.080→0.105 |
| Glass bite | 12 mm | 12.5 mm | 12.5 mm | — |

Checks:
- The map trims (X 0.70–0.77, Y to 2.07, Z ±0.10) lie wholly inside the sleeve envelope.
- Nothing visible sits inside X ±0.6835 × Y 0.3665–1.9835 except the glass.
- The 2 mm-class skins are 0.5 mm inside the opening, as on the doors (`04` §4.1).

### 4.3 The visible glass

- **A render-only 6 mm slab, 1.391 × 1.642, centred (0, 1.175, 0).** It sits wholly inside the 1.4 × 1.65 × 0.03 gameplay box, so nothing visible is outside the collider.
- **Spawned by the map as a child of `Window pane {a}-{b}`**: a primitive cube with its `BoxCollider` destroyed. Local scale is the slab over the pane size on each axis: (0.99357, 0.99515, 0.2) when the pane's long axis is local x, or (0.2, 0.99515, 0.99357) when the edge runs along z (the pane's scale axes swap, `MapWorld:1047`). Local position 0.
  - `01` §2.5 says a *model* cannot be a child of the pane. The slab is the exception on purpose: it is a unit cube, which is exactly what the glass shader expects ("Keep the pane a scaled unit cube with no rotation, or set `_PaneSize`", `../glass/10_implementation.md` §8). And `Kill(window.pane)` should destroy it.
- The pane's own `MeshRenderer` is **disabled, not destroyed**; `windowByCollider` keys on its collider (`01` §2.5).
- Material `Glass_Window` (`FrontRoomsGlassPane.Window`), with today's `TransparentGlass` as the fallback; shadows off on the slab.
- `ImpactUV` and `SetCrack` take the **slab's** transform and renderer. Its UV frame is the slab, so the crack mask covers the hidden bite too, as in real glass.
- `FrontRoomsMetalGlassTarget` moves from the pane cube to the slab. The RT controller only registers *enabled* renderers that carry the component (`Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs:149-153`). Left on the disabled pane, the RT path would silently ignore every window (§5).
- `Kit_InteriorWindow` keeps its own pane quad (decor; G5).

### 4.4 Break zones (the interface for GD1/GD3)

| Zone | Where (window root) | What lives there |
|---|---|---|
| **Pocket** (hidden) | between the stops: \|X\| 0.6835→0.6955, Y 0.354→0.3665 and 1.9835→1.996, Z ±0.003 | Every tooth's root. A tooth outline must include its hidden root, so it reads as held by the stop |
| **Tooth band** (visible, needs the `03` exception) | jambs \|X\| 0.600→0.6835; head Y 1.9835→1.900 ("guillotine" teeth); sill Y 0.3665→0.390 | Tooth tips. Largest at the corners, where radial cracks run out (ESTIMATE). Sill teeth carry `edge = bottom` and snap at the climb plant (`03` §3.6) |
| Clear zone | \|X\| < 0.600, Y 0.390→1.900 | Nothing after the break |
| Floor glass | `floor_pz` / `floor_nz` at (0, 0, ±0.45) (`03` §3.5) | GD3's floor scatters, about two thirds on the far side |

- Without the map's OK on the tooth band, teeth are clipped at the stop line, and the break reads as tempered (`03` §3.5).
- Per member:
  - **W-L0:** a wood stop bead knocked loose and hanging by one nail is a good second-level detail (ESTIMATE; render-only; GD3).
  - **W-OF / W-EX:** stops stay put.
  - **W-RN wired:** wire stubs (12.5 mm grid) continue out of the pocket by 5–30 mm all round, with glass crumbs on them (only if Red picks the wired break, §3.3).
- Slab size for the fracture generator: **1.391 × 1.642 × 0.006**, impact centres as `03` §3.5 (X ∈ {−0.40, 0, +0.40}, Y ∈ {0.90, 1.30, 1.65}); all ≥ 0.2 m from the stop line.

### 4.5 Anchors (add to `03` §3.5's list)

| Anchor | Value (window root) | Used by |
|---|---|---|
| `glass_slab` | centre (0, 1.175, 0), size in `meta` (1.391, 1.642, 0.006) | the map's slab spawn; GD3 |
| `stop_l`, `stop_r`, `stop_t`, `stop_b` | mid-points of the stop line: (∓0.6835, 1.175, 0), (0, 1.9835, 0), (0, 0.3665, 0) | crack UV clamp; tooth clip |
| `pocket_l` … `pocket_b` | glass-edge mid-points: (∓0.6955, 1.175, 0), (0, 1.996, 0), (0, 0.354, 0) | tooth roots |
| `tooth_band_l` … `_b` | (∓0.600, 1.175, 0), (0, 1.900, 0), (0, 0.390, 0) | tooth tips (if approved) |
| `face_a` | (0, 1.175, +0.105); in Blender (0, −0.105, 1.175) | which way the map rotates the frame |
| `blind_rail` | top centre of the rail: (0, 2.195), Z 0.110…0.145 on face A | `Interact_MiniBlindRaised` placement |
| `sill_plant_pz`, `sill_plant_nz` | (0, 0.3505, ±0.05) | `03` §3.6; on W-L0 this is the stool top |

### 4.6 Render-only and cheap

- Every part uses `kit.no_collider()`. No lights.
- **Draws per window:** frame 1 renderer (1–2 submeshes) + slab 1 (transparent) + blind 0–1. Frames reuse one mesh per member, so the SRP Batcher and static batching treat them like any other kit prop.
- **Shadows:** frame and blind cast; the slab does not (G1 shader has no shadow caster).
- **LOD:** LOD0/LOD1/LOD2 per Red's highest-spec order (`VISUAL_CHAT_TASKS.md` standing order). The WebGL tier's LOD bias belongs to the WebGL track and must not change the desktop path (`00`; `webgl-changes-webgl-only` rule).
- **The map spawns the frame before the `brokenWindows` early return** (`MapWorld:1042`), next to the trims, so a broken window keeps its frame across rebuilds.

---

## 5. The independent ray-traced glass track (ChatGPT/Codex): what it does, and what windows need from it

Read-only code reading, 2026-10-03 09:5x. I did not run it. The scratchpad holds a `proj_rt` clone and `rt_baseline_hashes.txt` (both 10:02), so another stage appears to be testing it. This section covers what it is and what it means for the window kit.

### 5.1 What it is

- **Files** (committed in `edfbc92`, 2026-10-03 01:42, message "1"; plus an uncommitted follow-up in the `.cs` that adds error checks and a capability log line):
  - `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs`: `FrontRoomsMetalGlassTarget` (marker), `FrontRoomsMetalGlassRTController`, the RenderGraph pass, and the P/Invoke bindings;
  - `Assets/Scripts/Rendering/FrontRoomsMetalGlassRTRendererFeature.cs`;
  - `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`;
  - `NativePlugin/FrontRoomsMetalGlassRT.mm` + `build_frontrooms_metal_glass_rt.sh` → `Assets/Plugins/macOS/libFrontRoomsMetalGlassRT.dylib` (arm64);
  - the feature added, active, to `Assets/Settings/FrontRooms_URP_Renderer.asset`;
  - `MapWorld:345-347` calls `FrontRoomsMetalGlassRTController.Ensure()` in standalone play; `MapWorld:1049` tags each pane.
- **Approach.** It bypasses Unity: a native Metal plugin builds its own acceleration structures and uses Metal's hardware ray intersector.
  - The visual chat's G11 found that Unity reports no hardware ray tracing on Metal (`../glass/11_reflections_and_raytracing.md`); G13 planned software rays through Unity's UnifiedRayTracing.
  - This track is a third route, and the only one that could use the M3 Max's RT hardware.
- **Scene upload** (`FrontRoomsMetalGlassRT.cs:117-226`):
  - every 1 s, on the main thread, it finds the glass target nearest the camera;
  - it registers every enabled `MeshRenderer` within 18 m of that target, plus all targets (cap 256);
  - it builds one BLAS per mesh straight from Unity's Metal vertex and index buffers, then a TLAS;
  - materials pass `_BaseColor`, metallic, smoothness, and a glass flag.
- **Per frame** (the kernel at `FrontRoomsMetalGlassRT.mm:245-303`):
  - one primary ray per pixel at full resolution;
  - if the first hit is a glass-flagged instance, one reflection ray;
  - a hit is shaded as `_BaseColor` × a fixed "sun" Lambert, direction (0.35, 0.82, 0.28), plus a small ambient term;
  - a miss returns a blue sky gradient;
  - the result is scaled by Schlick fresnel and written with **alpha 1**.
- **Composite:** a full-screen pass at `AfterRenderingPostProcessing` that blends it with `SrcAlpha, OneMinusSrcAlpha` (`FrontRoomsMetalGlassRTRendererFeature.cs:17`; composite shader `Frag`).
- **Gating:**
  - Mac only (`.cs:76-78`). WebGL and Windows stay inert, which respects the WebGL separate-track rule.
  - The capability test is `device.supportsRaytracing` (`.mm:652`). Its comment claims this means "M3-class hardware", but Apple staff say hardware RT must be tested with `supportsFamily(MTLGPUFamilyApple9)`. `supportsRaytracing` is true on M1/M2 too, where Metal RT runs in software (Apple Developer Forums thread 744941 [read]).

### 5.2 Defects that matter for windows (from the code; UNVERIFIED in a run)

1. **It makes windows opaque.** Alpha 1 with `SrcAlpha/OneMinusSrcAlpha` replaces every glass pixel with the dimmed reflection. The room behind, and the URP glass's grime, cracks and palm, disappear. At normal incidence the result is about 0.18 × the hit's flat lit colour (`mix(0.15, 1, F)` with F = 0.04 at normal incidence, `.mm:298-301`): a dark mirror.
   Fix: add the reflection (`Blend One One`) with alpha 0, or premultiply by fresnel.
2. **The field of view is wrong.** The managed side writes `fovRadians` at byte offset 64 (`.cs:378`), where the native struct reads `tanFovY` (`.mm:75, 142`). At 60° that fans the rays about 1.8× too wide, so the traced glass mask does not line up with the rasterised pane.
   Fix: write tan(fov/2).
3. **It composites after post-processing, with ZTest Always.**
   - Linear HDR values land in the graded, display-referred image, skipping exposure, bloom and grain.
   - Anything the BLAS lacks is painted over when it stands in front of a window: skinned meshes, objects beyond 18 m or the 256 cap, submeshes other than 0.
   Fix: composite before post, and depth-test the RT first hit against the camera depth.
4. **Flat shading.** No textures, no scene lamps, no shadows; misses show a sky that does not exist in FrontRooms.
   Fix: use the zone reflection cube (`FrontRoomsLook.SetZoneReflection`, G6) for misses, and the lamp list or the probe for hit colour.
5. **Main-thread rebuilds every second.** `FindObjectsByType` plus BLAS and TLAS rebuilds that block on `waitUntilCompleted` (`.mm:408, 490`) will hitch. Moving doors and the Relay are up to 1 s stale in both the reflection and the glass mask. The native comment expects these calls "from the render thread" (`.mm:727`), but `Update` makes them on the main thread (`.cs:117-122`).
   - **It also blinks once a second.** Each rebuild sets `reset` (`.cs:218`), and on a reset frame the kernel writes zeros and returns (`.mm:257-258`). Combined with defect 1, every window flips from dark mirror to clear glass for one frame per second.
6. **It may be inert in builds.** The composite shader is found by `Shader.Find` (`FrontRoomsMetalGlassRTRendererFeature.cs:13`), and nothing references it (no `Always Included` entry found in `ProjectSettings`), so player builds probably strip it (UNVERIFIED). The plugin `.meta` has no platform settings (2 lines).
7. **Cracks are ignored.** The reflection ray ignores `_Crack`, `_Palm` and smudge roughness, so a cracked pane would still reflect like a perfect mirror.
   Fix: pass the crack stage per instance, or fade RT out from crack stage 1.

### 5.3 What the window kit does for it (contract)

- The **visible slab** carries `FrontRoomsMetalGlassTarget`, not the disabled pane cube (§4.3).
- Frames, blinds and teeth are ordinary `MeshRenderer`s, so they enter the BLAS automatically within 18 m. Until defect 4 is fixed they are shaded by `_BaseColor` alone. So the Unity materials behind `Prop_SteelBrown`, the wood slot and `Prop_Aluminium` must carry a representative `_BaseColor`, not white with all colour in a texture. Each member is one mesh, so its BLAS is built once (`meshIndices`, `.cs:173`).
- Teeth and shards use `Glass_Shard` (opaque URP Lit) and are **not** targets.

### 5.4 Task row to add to `VISUAL_CHAT_TASKS.md` (for the visual chat; this workflow may not edit that file)

| # | Task | Owner | Status |
|---|---|---|---|
| G14 | **ChatGPT's native Metal RT glass track** (`FrontRoomsMetalGlassRT*`, `NativePlugin/`, committed `edfbc92`). A native Metal plugin with its own BLAS/TLAS and a one-bounce reflection, composited over URP; Mac only, inert on WebGL and Windows. Steps: (1) verify in a private clone: capture frames and frame time on the M3 Max, and check behaviour on an M1/M2 (software RT); (2) fix §5.2 defects 1–7 (additive composite before post with a depth test, tan(fov/2), Apple9 hardware gate, zone-cube misses and real hit colour, render-thread or async BLAS updates with per-instance transform refits, the shader kept in builds, crack fade); (3) move the target to the visible slab with the window kit (`interactables/06` §4.3); (4) decide it against G13 (UnifiedRayTracing) and the planar/probe path, since all three answer Red's "highest spec glass". Desktop only; WebGL untouched | visual (+ map: `MapWorld:345-347, 1049`) | QUEUED (analysis RUNNING in another stage: `proj_rt`) |

---

## 6. Asks

**Map chat**
1. Approve the **16 mm render-only stop band** (S1, §4.1), together with `03`'s tooth band.
2. Per window edge, spawn the frame asset at the `Window {a}-{b}` root (`01` §2.5):
   - pick the member by the non-tall side's theme (`Map:306-307`): Level 0 → `Interact_WindowFrameWood`, Office → `Interact_WindowFrameSteel`;
   - rotate it so face A looks into the non-tall cell;
   - build it next to the trims, before the `brokenWindows` return (`MapWorld:1042`).
3. Spawn the **visible slab** as a render-only child of the pane (§4.3): collider removed, `Glass_Window`, shadows off, `FrontRoomsMetalGlassTarget` moved onto it. Disable the pane's renderer. Feed `ImpactUV`/`SetCrack` from the slab.
4. Optional, for true profiles: skip the jamb and head trims on window edges when a kit frame spawns (`MapWorld:999-1009`). They are render-only, so there is no gameplay effect.
5. Optional: place `Interact_MiniBlindRaised` on face A of Office windows by edge hash.
6. Later, if Run gets map windows with wired glass: a two-stage break (§3.3).

**Visual chat / glass destruction (GD1, GD3)**
- Fracture sets for a **1.391 × 1.642 × 0.006** slab; pocket and tooth bands as §4.4.
- `Glass_Wired` only if Red picks wired glass.
- `Kit_InteriorWindow_Bronze` variant plus the lowered blind, with G5.
- G14 (§5.4).

**Sound (声音)**
- Frame tags `frame_wood` / `frame_steel` / `frame_alu` are available for `ClimbSill` and `ToothSnap`, if a material difference is wanted.

**Red**
1. The family split: wood in Level 0, dark-bronze steel in Office, white steel in Run, clear aluminium at the Exit.
2. Mini-blinds on Office windows (raised only), and the "same bent slat" detail.
3. Hammered obscure glass for some Level 0 windows (it hides the hall and the Relay).
4. Run: wired glass with a two-stage break, or plain glass.
5. The Exit: a different break (tempered granules) as a tell, or the same.

---

## 7. Open items / UNVERIFIED

- The 1980s model-code test for large low glazing (UBC/BOCA) is unconfirmed; it decides only whether "annealed" is legal or an alibi (§2.4).
- NFPA 80's 1,296 sq in / 54" limit is quoted from a page about a modern edition; the 1990 value is unconfirmed.
- TRIFAB 450's 1969 trademark date and Kawneer's "1/4" beveled glass stops" are search summaries only.
- The Allegion glass-cutting rule (EGS + 1-1/4") is a search summary only. The 12 mm bite is an ESTIMATE that fits it.
- All triangle budgets, the blind share, the corner-tooth sizes and the loose-bead detail are ESTIMATES.
- Hammered glass in mid-century office partitions: only a weak source (UNVERIFIED); UFGS confirms patterned glass in borrowed-light sash, not the style.
- §5: all seven RT defects come from reading code; none was run. Whether the composite shader is stripped in player builds needs a build.
- The map's line numbers will move: `MapWorld` has uncommitted edits (`git status`, 2026-10-03 09:5x).
- Not done here: Figma three-view sheets (R10's last stage), and an in-engine render of the frames (the build stage).

---

## 8. Sources

**Project files (read 2026-10-03):** `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs` (lines cited above), `FrontRoomsMap.cs:306-307, 366`, `FrontRoomsModuleUnits.cs:41, 61, 64`, `Assets/Scripts/FrontRoomsRoomStream.cs:1254-1271, 1358, 1403, 1442`, `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs`, `FrontRoomsMetalGlassRTRendererFeature.cs`, `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`, `NativePlugin/FrontRoomsMetalGlassRT.mm`, `NativePlugin/build_frontrooms_metal_glass_rt.sh`, `Assets/Settings/FrontRooms_URP_Renderer.asset`, `Tools/Blender/frontrooms_kit/kitlib.py:1-140`, `assets/interior_window.py`, `Documentation/VISUAL_CHAT_TASKS.md`, `research/glass/10_implementation.md`, `research/interactables/00–05`, `research/interaction_audit/10_audit_report.md`, `research/office_and_film/03_ip_canon.md`, `22_era_lock.md`; `git show --stat edfbc92`, `git diff` of the RT controller.

**Web (read):**
- Steel Door Institute, SDI 111 (111A-24 Standard Profiles, p. 3): https://steeldoor.org/wp-content/uploads/2020/02/SDI_111.pdf
- University of Houston, Master Spec 08 11 13 Hollow Metal Doors and Frames (rev. 2014): https://www.uh.edu/facilities-services/departments/fpc/master-specs/08-11-13-hollow-metal-doors-and-frames.pdf
- WBDG, UFGS-08 81 00 Glazing (May 2019): https://www.wbdg.org/FFC/DOD/UFGS/UFGS%2008%2081%2000.pdf
- NPS, ITS 31 Retaining Distinctive Corridor Features: https://www.nps.gov/orgs/1739/upload/its-31-retaining-corridor-features.pdf
- US4463535A, Glass stop assembly (USG, 1982/1984): https://patents.google.com/patent/US4463535A/en
- US4443984A, Door, window, and partition casing arrangement for dry wall partitions (1981/1984): https://patents.google.com/patent/US4443984
- US4841700A, Narrow flush glazed thermal framing (Kawneer, 1988/1989): https://patents.google.com/patent/US4841700
- Kawneer, Trifab VersaGlaze 450 (1-3/4" × 4-1/2"): https://www.kawneer.com/products/storefront-framing/trifab-versaglaze-450-framing-system-1-3-4-sightline/
- SAF, Aluminum Sheet: Anodizing – Integral Color (Duranodic): https://www.saf.com/how-to-specify/aluminum-sheet-anodizing-integral-color-duranodic/
- Alumicor, Anodized advantage: https://alumicor.com/2024/02/anodized-advantage-understanding-the-benefits-and-options/
- Wikipedia, Float glass: https://en.wikipedia.org/wiki/Float_glass
- Designing Buildings, Wired glass: https://www.designingbuildings.co.uk/wiki/Wired_glass
- General Glass International, Wire Glass Features & Benefits (PDF, generalglass.com; local copy `scratchpad/win06/ggi_wire.pdf`)
- idighardware, glass in fire doors (NFPA 80 limits): https://idighardware.com/?p=26463
- This Old House, How to trim an interior window: https://www.thisoldhouse.com/windows/how-to-trim-an-interior-window
- Wikipedia, Mini blind: https://en.wikipedia.org/wiki/Mini_blind ; Window blind: https://en.wikipedia.org/wiki/Window_blind
- Encyclopedia.com, Blinds & Shades: https://www.encyclopedia.com/manufacturing/encyclopedias-almanacs-transcripts-and-maps/blinds-shades
- Christian Science Monitor, "Take a look at the latest blinds – 'micro-minis'" (19 Oct 1984): https://www.csmonitor.com/1984/1019/101955.html
- Levolor, Riviera Commercial Horizontal Aluminum Blinds, Product Information Guide (PDF; local copy `scratchpad/win06/hd_alum.pdf`)
- Sears Annual Home Catalog 1993, Internet Archive full text (local copy `scratchpad/win06/sears1993_djvu.txt`; the source behind Figma REAL vs MODEL slide 45)
- Apple Developer Forums, "How do I check programmatically if a device supports hardware Raytracing?": https://developer.apple.com/forums/thread/744941

**Web (search summaries only, UNVERIFIED):** Allegion knowledge base on borrowed lights and glass cutting size (403 to direct reads); Kawneer bevelled stops; the TRIFAB 450 trademark date; the building-code forum thread on hazardous-location history (403).
