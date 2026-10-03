# 06 — Period windows: structure and a window family for FrontRooms (R9)

Status: IN PROGRESS (2026-10-03 00:2x). Research only. Nothing in the real project or the Unity clone has been changed.

Red: "build the window's STRUCTURE too, not just a pane of glass — research what windows made sense in that era."

Binding inputs: `00_map_constraints.md` (obeyed everywhere below), `../office_and_film/22_era_lock.md`, `../interaction_audit/10_audit_report.md` §3.5–3.6 and §4, `02_period_hardware.md` §6–7, `03_readability_placement_shots.md` §3.5, `04_door_re8_gap.md`, `05_locked_door_type.md`, `Documentation/VISUAL_CHAT_TASKS.md` R7, R9, R10, GD1–GD3.

Sections (filled in as the work lands):
0. Decision
1. What the game builds today (code facts)
2. Period research
3. The window family
4. Fit to the map opening: sections, glass, break zones, anchors
5. Asks
6. Open items / UNVERIFIED
7. Sources

---

## 1. What the game builds today (code facts)

Short names as in `05`: `MapWorld` = `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `Map` = `…/FrontRoomsMap.cs`, `Units` = `…/FrontRoomsModuleUnits.cs`, `Stream` = `Assets/Scripts/FrontRoomsRoomStream.cs`. Line numbers are the real project as read on 2026-10-03 00:1x; the map chat is editing `MapWorld`, so they drift.

### 1.1 Map windows

- **Where.** A window is built on any edge where a Tall zone meets a Low or Standard zone (`Map:354`). Tall zones are always the Level 0 theme: only Standard zones can roll Office (`Map:293-295`). So every map window has **a Level 0 tall hall (5.4 m) on one side**, and a Level 0 room (2.4 or 2.9 m) or an Office room (2.9 m) on the other.
- **Opening.** 1.4 wide, centred on the 3 m edge, sill 0.35, head 2.0 (`Units:57`; `MapWorld:903-914`). The wall below 0.35 is a solid block whose top face is bare wallpaper (`MapWorld:914`). Wall 0.16 thick (`Units:41`).
- **Trim.** Two jambs, 0.07 face × 0.20 deep, from the sill to the head, with their inner faces exactly on the opening edges; a head 1.54 × 0.07 × 0.20 from 2.00 to 2.07 (`MapWorld:917-927`). Material `Cove_Base` (`MapWorld:1899`). **No stop, no glazing bead, no bottom member, no stool, no apron.** The trim's inner faces are coplanar with the wall's end faces (the same z-fight `04` §1.1 found at doors).
- **Pane.** A primitive cube `Window pane {a}-{b}`, 1.4 × 1.65 × **0.03**, centred on the wall line, child of the chunk root with no rotation; its scale axes swap with edge direction (`MapWorld:959-969`). Material built in code: URP Lit, transparent, premultiplied, base (.75, .85, .88, .28), smoothness .9 (`MapWorld:1904, 1907-1923`).
- **Break.** At 1.0 s of hold, `Kill(window.pane)` destroys the pane and any children, then `GlassBroken(position)` fires (`MapWorld:1791-1804`). A broken window is simply not rebuilt (`MapWorld:960`). No remnants, no floor glass.
- **No window root.** Nothing unscaled marks the opening. `01` §2.5 proposes a `Window {a}-{b}` root at the opening centre, floor level, local +Z into cell b. This report uses that frame.

### 1.2 `Kit_InteriorWindow` (Office decor)

- `Tools/Blender/frontrooms_kit/assets/interior_window.py:1-33`: a dark-bronze 50 × 85 mm steel frame, 2.40 × 1.22, one undivided 6 mm pane in snap-in glazing beads with black gaskets, a steel sill nose with horns. Wall-mounted, single-sided, no collider. Pane slot `Prop_GlassCRT` (opaque black). Frame slot `Prop_SteelBlack`.
- Placed by `FrontRoomsOfficeKit` (`Assets/Scripts/Office/FrontRoomsOfficeKit.cs:58`), sill 0.90 target (`Documentation/LEVEL_MODULE_SPEC.md:120`).
- The black-slab pane is open task T15 / G5 (`VISUAL_CHAT_TASKS.md`).

### 1.3 Title stream rooms

- `Stream` builds **no windows** (no "window" or "glass" geometry in `FrontRoomsRoomStream.cs`).
- Its doors are flush double doors with brushed-steel bar handles and kick plates on both faces (`Stream:1254-1271`), material "Door / brushed steel" (`Stream:1403`).
- Room rules: Lobby, Shift, Office, Run, Exit (`Assets/Scripts/FrontRoomsRoomRule.cs:5`). Run is "a white hospital corridor, dim except for the red exit signs" (`Stream:1442-1444`); Exit is blue-green paper with cool light (`Documentation/BACKROOMS_VISUAL_SPEC.md:13`).

### 1.4 What this means

- Every live breakable window today is a **Level 0 ↔ Level 0** or **Level 0 ↔ Office** window: "a back room or an office that looks into a tall hall".
- Run and Exit windows do not exist yet. Their family members below are specified so the family is complete, and are lower priority.
- The kit importer remaps any slot name to `Assets/Resources/Surfaces/<slot>.mat` when that material exists (`Assets/Editor/Rendering/FrontRoomsKitImporter.cs:36-43` in the clone). So a window module can use the map's own `Cove_Base` trim, or `Glass_Window` once G3 creates it, by `kitlib.register_slot(...)` with no edit to `kitlib.py` (the mechanism `05` §6.1 uses for `Door_Veneer`).

---

(sections 0, 2–7 in progress)
