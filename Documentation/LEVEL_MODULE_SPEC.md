# FrontRooms modular unit spec

The contract between the level (map chat: generator, `FrontRoomsMapWorld`, Relay, future Level Designer) and the art (visual chat: surfaces, lamps, Office kit, furniture pile, Relay rig). Every architectural piece, prop and future room module is measured against it. In code it is `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs` (`ModuleUnits`); the level's tunable numbers live in `Assets/Levels/FrontRoomsLevel0.asset` (`FrontRoomsLevelProfile`).

Status: P0 of the level-design modularization (2026-10-02), reviewed against the code. Sections marked **P0b** are agreed directions that change the picture and land as a joint step.

## 1. Conventions (every unit)

| Rule | Value |
|---|---|
| Units | metres, scale 1 (Blender metric, FBX `apply_unit_scale`) |
| Axes | Y up; a unit's **front faces +Z** (Blender −Y) |
| Pivot | floor centre: stands on y = 0, centred on x = 0 and z = 0. Depth must be centred too: kits place by `depth / 2`, and `HalfFootprint` is symmetric about the pivot, so trailing parts (cables) inflate the footprint. `Kit_CRTMonitor` is not depth-centred yet (z −0.311..0.213) |
| Name | `Kit_<PascalCase>` (props), `Prop_<Material>` (slots) |
| Randomness | seeded per room, never `UnityEngine.Random`, no static state. Same seed, same room: a chunk can be dropped and rebuilt at any time |
| Parent | everything under the `parent` the map passes; nothing outside the floor rect |

## 2. Grid

| Unit | Value | Why |
|---|---|---|
| Cell | **3.0 m** square, one corridor wide | every wall, doorway, door and window spans exactly one cell edge |
| Chunk | 8 × 8 cells = 24 m | built and dropped around the player |
| Fine module | **0.6 m** (5 per cell, 40 per chunk) | metric ceiling grid, carpet tiles, fixture footprints |
| Structural grid | **6 m** (every other cell line) | columns (§3) |
| Wall | 0.16 m thick, **centred on the cell line** | each side loses 0.08 m |
| Clear span | `n × 3 − 0.16` | 2 cells 5.84, 3 cells 8.84, 4 cells 11.84, 7 cells 20.84 |

Cell (x, y) covers world X [3x, 3x+3) and Z [3y, 3y+3) in map space. A wall piece that reaches a cell corner runs 0.08 m (`WallHalf`) past it, so a full wall edge is 3.16 m long: two walls in a line overlap by 0.16 m and an L or T junction is a shared 0.16 × 0.16 m square (butt overlap, no mitre). A piece that ends at an opening is not extended. Where two themes meet a wall is two 0.08 m skins, each in its own room's paper.

### Heights

| Zone | Ceiling | Shares |
|---|---|---|
| Low | 2.4 m | 35 % |
| Standard | 2.9 m | 55 % (Office is a theme of Standard only) |
| Tall | 5.4 m | 10 % |

Floor slab 0.20 below y = 0; ceiling slab 0.16 above the ceiling. An edge wall takes the taller side's height. Props keep **0.05 m** under the ceiling (`CeilingClearance`), except the pile's ceiling-stuck tableau (§6).

## 3. Architecture (map-owned sizes)

The map builds these; the visual chat owns their materials and finish. Sizes change only by agreement: the Relay's crossings, the player capsule and the key rule depend on them.

| Piece | Where | Size | Notes |
|---|---|---|---|
| Arch (doorless doorway) | edges inside a zone (and Open/Arch room edges) | 1.1–1.8 m wide, top 2.2 m (0.2 m under a lower ceiling) | off-centre from the edge hash, ≥ 0.2 m of wall to each corner; no trim |
| Door | Low ↔ Standard borders only | opening 1.0 × 2.1 m, centred | leaf 0.98 × 2.08 × 0.05, hinge on the edge's low-coordinate jamb (south jamb of an east edge, west jamb of a north edge), pivot on the wall centre line, leaf centred in the wall. It opens 95° **away from whoever opens or breaks it** (a pushed door) and stays that way across rebuilds. Trim 0.07 face; the jamb stands 0.02 proud of each wall face; the open leaf's first ~0.1 m passes inside the 0.20 m jamb, so no stop or rebate near the hinge |
| Window (breakable glass) | any border with a Tall side | 1.4 m wide, sill 0.35, top 2.0, centred | glass 0.03; same trim, no sill trim. Hold E to break; **walk into the broken frame to climb through** (0.6 s, the view ducks under the head) |
| Column | see below | 0.6 or 0.9 m square, full height | faced in the room's wall material, on a 0.10 m `CoveBase` cove 6 mm proud |
| Bulkhead (Office) | between two Office columns on the same grid line, inside the room | as wide as the column, 0.35 deep under the ceiling | no collision (above every head) |

**Columns (rule v1, map-owned).** Columns stand on cell corners of the world **6 m grid** (both corner indices even), so columns in neighbouring rooms line up like a real building. Only inside carved rooms that are one open space (no later room cuts into them, every cell the same height and theme), at least 3 cells on both sides, never in Low zones, maze corridors or 2-cell rooms. A room that qualifies rolls once per revision (`MapSettings`: Level 0 25 %, Office 75 %, Tall hall 70 %); if it hits, every grid corner inside it gets a column: 3 × 3 → 1, 3 × 4 → 1–2, 4 × 4 → 1–4, Tall 5 × 5 → 4, 5 × 7 → 6, 7 × 7 → 9.

| Room | Column | Finish (visual chat) |
|---|---|---|
| Level 0 Standard | 0.6 m | the room's wallpaper + cove (a chair rail would run round it if the walls ever get one) |
| Office | 0.9 m + bulkheads | drywall (`Office_Wall`, world-projected so it lines up with the walls) + cove; bulkhead `Office_Wall`, no cove; no chair rail |
| Tall hall | 0.9 m, 5.4 m tall | wallpaper + cove |

Guarantees from the geometry: a column face is ≥ 2.47 m from any wall face or opening and ≥ 1.27 m from every keep-clear strip, and ≥ 1.06 m from every cell-to-cell crossing line (0.75 m is needed), so routes are never blocked. Columns are architecture: they block sight.

Real-world check: a commercial 3070 leaf is 0.914 × 2.134 m in a frame ≈ 1.02 m wide (SDI 111); a two-layer metal-stud wall is ≈ 0.156 m. Our door and wall read true.

## 4. Ceiling, fixtures and light

Done jointly on 2026-10-02 (P0b, metric grid):

| Rule | Value |
|---|---|
| Ceiling grid | **0.6 m tile pitch anchored at world (0, 0)**; every sheet repeats at 1.2 m (Level 0 2'×4' print, Office 2'×2') |
| Troffer | one per cell: 0.6 (X) × 1.2 (Z) × 0.025 lens filling whole tiles, X [1.2, 1.8] and Z [1.2, 2.4] of the cell (centre +0.3 m Z, `TrofferOffsetZ`), its centre 0.02 below the ceiling (`TrofferDrop`); a real 2×4 troffer in the grid with one cross tee left out |
| Lamp | downward spot at the lens centre, 0.06 below the ceiling (`LampDrop`), 162°/96°, colour (1, .96, .88), range 10 (12 tall), intensity 5 / Office 5.5 / ×1.6 tall |
| Budget | lights on within `lightRadius` 16 m (3 m fade); 1 lamp in 3 may cast Soft shadows within `shadowRadius` 9 m; both in the level profile |

Lamp intensity, colour, flicker odds and lens materials are the visual chat's numbers. The map chat owns placement, count and the budget radii. Office troffers keep clear of bulkheads (the lens is ≥ 0.15 m from any bulkhead).

## 5. Surfaces (world-projected tile sizes)

Room surfaces are world-projected (`FrontRooms/Surface`), so the map's mesh-UV repeats only reach fallback materials. Every number here is the material's **world repeat** (`_TileSize`), which may hold several physical tiles: `Office_CarpetTile`, `Office_Ceiling2x2` and `Ceiling_Fissured` hold 2 tiles across one repeat today.

- **Ceiling grid pitch must divide 3 m** (0.3, 0.5, 0.6, 0.75, 1.0, 1.5, 3.0): it is **0.6**. A 2-tile sheet at 1.2 m keeps a 0.6 m line on every cell line; its pattern shifts by one tile from cell to cell, which reads as a real ceiling.
- **Live tile sizes (visual chat, 2026-10-02):** ceiling sheets 1.2 (0.6 tiles); wallpaper roll 0.75, repeat 0.75 × 1.125; Office carpet 0.6 tiles in a 1.2 sheet; Office wall and Run VCT 1.2 (0.3 VCT tiles); Level 0 carpet 1.0.
- **Free:** vertical repeats (the paper is cut at the ceiling, as real paper is), prop materials (mesh UV).
- **Roots on a 192 m multiple:** surfaces are projected from world (0, 0), so a map root, capture root or origin shift must sit on a multiple of 192 m (`ModuleUnits.WorldPeriod`, the least common multiple of every world period: 0.6 / 1.2, 0.75, 1, 8, 12.8 and 24 m). The game's map root is at the origin; captures and tests use 4992 m.
- **Title stream rebase: 192 m.** `RebaseIfNeeded` shifts the world in Z by whole multiples of it, so it must be a multiple of every world-projected period along Z: the tiles above, the 24 m chunk and the shader's macro-wear periods (8 m and 12.8 m).
- **Ceiling grime:** the shader grimes the 1.6 m under `_CeilingHeight`, the absolute world height of the renderer's ceiling plane. The map builds its shell renderers per 6 m block **and ceiling height** and sets `_CeilingHeight` = chunk floor Y + 2.4 / 2.9 / 5.4 on each with a `MaterialPropertyBlock` (shell only, never props). A wall between two heights takes the taller one.

## 6. Rooms and the dressing contract

The generator carves rooms (`CellRect`) on top of the maze: Low 2 × 2–3 cells, Standard 2 × 2–4, Tall 1 × 5–7. A later room wins where two overlap, and the earlier rect keeps maze edges (walls, arches) along the overlap. **Only rooms that are one open space are dressed**: no later room cuts into them (`MapChunk.RoomIntact`) and every cell has the same height and theme (`FrontRoomsMapGenerator.Uniform`). Office rooms are Standard height only, so 6, 9 or 12 m a side. Rooms are dressed one per frame, after their chunk's geometry, since chunks build ≥ 24 m away.

`FrontRoomsOfficeKit.Dress(Transform parent, Rect floorXZ, float ceilingHeight, int seed, Rect[] keepClear, Rect[] obstacles)` (the map binds this one by parameter types, else the 5-argument one):

- `floorXZ` is the **clear floor** in chunk-local metres: the room's cells inset by 0.08 m (`WallHalf`) on every side, so its edges are the wall faces (n·3 − 0.16 a side). Wall units sit `depth / 2 + 0.03` from those edges.
- `keepClear` holds one strip per passable boundary edge (open, doorway, door, window), along the inside of that cell edge, spanning the full 3 m: **1.0 m** deep from the wall face, **1.2 m** at doors whichever way the leaf swings. The spawn room of chunk (0, 0) also gets a 2 × 2 m strip round the spawn point. Boundary stretches that no strip touches are wall.
- `obstacles` are the room's columns (footprints in chunk-local metres): occupied, with the kit's own 0.45 m reserved halo. The 6-argument path never places columns itself.
- Dress keeps every strip connected to every other through aisles **≥ 1.0 m** (`MinAisle`; player capsule 0.6). The design target between pods is the 1.6 m chase lane (kit to enforce pod-to-pod spacing, not only halos).
- Nothing taller than `ceilingHeight − 0.05`. Nothing on a strip, with or without a collider.

`FrontRoomsFurniturePile.Build(Transform parent, Vector3 centerLocal, float radius, float ceilingHeight, int seed)`: halls of at least 4 × 4 cells; chance 0.35 (≥ 0.6 in Tall). The centre is the room centre, or with columns the centre of the 6 m bay nearest it; the radius is `min(3.2, 0.22 × shorter side)` and shrinks so the pile plus a 0.6 m ring stays off columns and walls and the pile stays off every keep-clear strip (no pile under 1.2 m). Upright pieces keep under `min(0.95 H, H − 0.06)`; the ceiling-stuck tableau deliberately sinks up to 0.12 m into the 0.16 m ceiling slab.

### What fits (aisle 1.6 m, the Office chase lane)

Footprints from the visual chat's Blender kit (2026-10-02), with real catalog sizes for reference:

| Unit | Footprint W × D × H | Real reference |
|---|---|---|
| Desk worksurface | 1.524 × 0.762, top 0.74 | 30 × 60 in, 28.5–30 in high (BIFMA G1 / ANSI-HFES) |
| Pedestal | 0.38 × 0.56 × 0.71 | |
| Cubicle panel | `Kit_CubiclePanel` 1.524 W and `Kit_CubiclePanelShort` 0.762 W (narrow, not low), both 0.065 thick × 1.57 H | 53–54 in = 1.35 (low), 65 in = 1.65 (standard). Proposed: a 1.65 m variant, which would block the Relay's sight (§7) |
| Station | 1.524 × 1.70 (desk + 0.9 chair zone) | chair pull-back 0.91 min |
| Pod 2 × 2 back-to-back | 3.10 × 3.45 | |
| Task chair | 0.66 base, seat 0.45, back 0.95 | 26–28 in base, seat 15–22 in |
| Vertical file (4 drawer) | 0.38 × 0.66 × 1.32 | HON 310: 0.381 × 0.673 × 1.321 |
| Lateral file (planned, no `Kit_` id yet) | 0.91 × 0.46 × 1.32 | HON Brigade: 0.914 × 0.457 × 1.334 |
| Vending | 0.90 × 0.90 × 1.83 | |
| Water cooler | 0.32 × 0.32 × 1.37 (bottle top) | |
| Copier | 0.62 × 0.68 × 1.15 | |
| Interior window (decor) | 2.44 × 1.22, sill 0.90 target (code places 0.95), no collider | |

| Room side | Clear | Single row on a wall (1.70 + 1.6) | Back-to-back pod free-standing (1.6 + 3.45 + 1.6) | Pod with one long side on a wall | Two-column pod across (3.10) |
|---|---|---|---|---|---|
| 2 cells | 5.84 | ✓ | ✗ (6.65) | ✓ (5.05) | end on a wall (4.70) |
| 3 cells | 8.84 | ✓ | ✓ | ✓ | ✓ free-standing (6.30) |
| 4 cells | 11.84 | ✓ | ✓ | ✓ | ✓ |

Wall units need a 0.5 m service zone in front. The decor window stays inside one cell edge (never across a corner junction) and only on wall stretches no strip touches.

## 7. Collision, navigation and sight

- Props: authored **box colliders** per prop (sidecar `colliders[]`); no mesh colliders; desk-top items none.
- Player: `CharacterController` 1.75 × r 0.3, step 0.3, eye 1.62. Walk 3.2, run 5.5 m/s for 5 s.
- Relay: a body of r 0.3, tested between 0.4 and 1.95 m (it fits a door and a broken window). It routes cell to cell on the map; inside a leg it walks straight while the body fits the whole way and otherwise plans a detour on a 0.25 m grid over the cells around it (furniture, columns, open door leaves). With no way round furniture it passes through it, still on a route that keeps out of walls, and walks round again once clear. A hunt whose end is covered stops beside it; a hunt held in place for 3 s gives up and searches. After breaking a door it waits for the leaf to fall. It never spawns overlapping anything. Checked by **FrontRooms → Map → Test Relay navigation** (60 hunts among random boxes). **The rig must fit a 1.0 × 2.1 m door and a 2.4 m ceiling** (≤ 2.05 m tall while walking, or it stoops).
- Sight is a ray between eyes at 1.60 (Relay) and 1.62 (player). Desks and the current 1.57 m panels don't block it; walls, shut doors, columns and anything with a collider top ≥ 1.65 m do.

## 8. Streaming and performance

The map builds one chunk per frame, nearest first, and furnishes one room per frame after that. Budgets per dressed room:

| | Office rooms | Other rooms |
|---|---|---|
| LOD0 triangles | ≤ 120 k (LOD1 ≈ 45 % from ~8 m) | ≤ 60 k |
| Renderers / colliders | ≤ 120 / ≤ 40 | ≤ 120 / ≤ 40 |
| Dress time | ≤ 3 ms | ≤ 3 ms |

Props ≤ 0.3 m cast no shadows. Acceptance is the autopilot (`FrontRoomsMainScenePlaytest`, with `-autopilotSeed N` for a fixed maze; seeds 2554 and 20388 spawn in an Office zone): average ≥ 55 fps and `p99FrameMs` ≤ 33 after the first 2 s. `frameSpikes` lists every frame over 50 ms with its time and zone; one-off editor shader compiles (e.g. when the Relay first renders at 3 s) are not counted against the budget. Baseline with only `Kit_CRTMonitor`: 59 fps, p99 ≈ 18 ms.

## 9. Room modules (Level Designer, P1–P3)

Built (`RoomModuleData`, `FrontRoomsRoomModule` assets in `Assets/Levels/Modules`; the editor is in `LEVEL_DESIGNER.md`). A module is authored in these units:

- **footprint** 1–8 × 1–8 cells (a room never crosses a chunk); ceiling class (§2); theme Level 0 or Office (Office is Standard height);
- **edges**: perimeter and inner, each Wall / Arch / Open. An arch is §3's arch. Doors and windows are not authored: where the room meets another height, or the chunk border, the map's rule stands (§3), and the map may reopen one of the module's walls to keep the chunk connected (generated walls first, then the module's perimeter, its inside last);
- **columns**: Auto (§3's rule on the world 6 m grid; never on a corner where an inner wall or arch meets), None, or Custom (inner corners, 0.6 or 0.9 m);
- **props** by kit asset name at (x, z) metres from the room's south-west corner, snapped to 0.05 m, any yaw (the plan turns in 90° steps; the Scene view keeps whole degrees), a height for wall pieces, and *no collider* for clutter. Placement comes from the kit's sidecar: `footprint`, `placement` (Floor / Wall / DeskTop / Ceiling), the `top` support and the `hang` anchor;
- **fill** None / Auto (as a generated room) / Office (the kit fills round the props) / Pile; **lamps** per cell (Auto rolls them as the map does).

**Checks** (`Validate`). These are errors:
- no way in;
- cells cut off;
- a prop in a wall or above the ceiling less §4's 0.05 m;
- a prop with a collider in an opening's 1.0 m clear strip (§6; the map leaves it out of the build);
- a prop that blocks a walk between openings (0.25 m grid, player radius 0.3 m).

These are warnings:
- a *No collider* prop in an opening's clear strip, or any prop at an inner doorway;
- a prop where a column stands or may stand in any turn the generator can use;
- a side of 7–8 cells (it meets the chunk border);
- Office, Pile or Auto fill with inner walls (the fill furnishes the room as one space).

**Placement by the generator** (P3): each intact uniform carved room rolls `moduleChance` (0.3). A module of the room's height and theme whose tier range holds `moduleTier`, and that fits in an allowed quarter turn, is picked by `weight` (capped at 1000; it is shared between the module's fitting turns). The spot is hashed, kept off the chunk border when the room allows. An Auto-column module lands on the 6 m grid phase of its turned footprint centred in a chunk, which is what the Level Designer preview shows for that turn. With an odd side, the columns move to the other corners in odd turns. The same seed gives the same modules; a revisit shift may give others. The map leaves out, with a console warning, a module prop that would stand across an opening the map made.

## 10. Ownership and changes## 10. Ownership and changes

| Area | Owner | Files |
|---|---|---|
| Grid, openings, columns and bulkheads, room carving, keep-clear, dressing order, budgets, Relay body and navigation | map chat | `FrontRoomsMap/*`, `FrontRooms3DGame.cs`, `Editor/FrontRoomsMap/*`, `Assets/Levels/*`, this spec |
| Surfaces, tile sizes, lamp look, lens, finishes, Office kit, pile, Relay rig, title stream | visual chat | `Rendering/*`, `Office/*`, `FrontRoomsRoomStream.cs`, `Tools/Blender`, `Tools/lookdev` |

A change to a number in §2–§4 or §6–§7 is agreed in both chats first, then `ModuleUnits` and this file change together.

## 11. Known gaps (2026-10-02)

- In the main project only `Kit_CRTMonitor` is built so far; the Office kit (~29 assets) is in the visual chat's copy, in review.
- Two office kits exist: the title stream still uses `FrontRoomsOfficeFurniture` (fronts face −Z, different sizes). The map uses `FrontRoomsOfficeKit` only.
- Stale docs: `LIGHTING_SPEC.md`, `BACKROOMS_VISUAL_SPEC.md`, `WALLPAPER_UV.md`, `LEVELS_AND_ENTITIES.md`, `FRONTROOMS_MAZE_LEVEL_DESIGN.md` describe the title stream or older prototypes. This spec and `MAP_GENERATION.md` describe the game.

Sources for real-world sizes: Armstrong Cortega and Rockfon T24 data sheets (ceiling grid), Lithonia 2GTL4 / BLT (troffers), SDI 111 (door frames), US Access Board ADA ch. 4 (clear widths), UW EHS ergonomics guide citing BIFMA G1 and ANSI/HFES 100 (desks, chairs), HON catalog (files), officefurniture2go guides (panels, aisles).
