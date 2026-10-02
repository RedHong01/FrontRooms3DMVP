# FrontRooms map generation (week 2 · data layer)

The design plan replaces the straight train of rooms with an endless field of
open zones. This layer is the data only: cells, edges, zones, pillars and keys.
It is not yet connected to `FrontRoomsRoomStream`; the week 3 work builds
geometry from it and replaces the door train.

## Grid

- A **cell** is a 6 m square. Cell `(x, y)` covers world X `[6x, 6x+6)` and Z `[6y, 6y+6)`.
- A **chunk** is 4 × 4 cells (24 m) and is the unit that is built and dropped around the player.
- Every edge between two neighbouring cells has one **kind**: `Open`, `Arch` (wall with a gap: blocks sight, not movement), `Wall`, `Door`, `Window`.

## Zones and heights

Each chunk owns one random site. A cell belongs to the zone of the nearest site,
so zones are irregular and cross chunk borders. Each zone rolls a ceiling class:
`Low` 2.4 m, `Standard` 2.9 m, `Tall` 5.4 m (shares 35 / 55 / 10 %).

- Inside a zone, and between two zones of the same height, edges are `Open`, `Arch` or `Wall`. Low zones are mostly open, standard zones office-like (more arches and walls), tall zones open halls.
- Where the height changes, an edge is a `Wall` unless it opens as an exit, and the taller side decides the exit: **Door** between low and standard, **Window** whenever one side is tall.
- Every low or standard zone has one **key**, in its cell nearest the site. Tall zones are left through windows and have no key.
- **Pillars** stand on cell corners where all four cells share a height (low 30 %, standard 8 %, tall 55 %).

## Guarantees

- **Reachable:** each chunk lays a random spanning tree over its 16 cells, and tree edges are never walls. Each chunk border has one required opening. So every cell connects to every other (doors and windows count as passable).
- **Borders agree:** zones, heights, border edges and border pillars are pure functions of the seed and world coordinates, so neighbouring chunks agree whichever is built first.
- **Shift without seams:** `Generate(chunk, revision)` with a higher revision reshuffles only that chunk's interior walls and pillars. Borders and zones stay the same. This is what decision 2 ("a dropped chunk comes back shifted") would use; the default build always uses revision 0.

## Editor tools

- **FrontRooms → Map → Debug map** opens a top-down view: seed, area, chunk grid, generation settings, hover info and *Shift hovered chunk*.
- **FrontRooms → Map → Verify 100 seeds** checks 100 seeds over 8 × 8 chunks each and writes `Verification/map-verification-latest.json`.
- Headless: `Unity -batchmode -projectPath <project> -executeMethod FrontRoomsMapVerification.RunBatch -quit`.

## Code

- `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs`: types, `MapSettings`, `FrontRoomsMapGenerator`, `FrontRoomsMapCache`. Plain C#, no UnityEngine dependency.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapValidator.cs`: the checks above.
- `Assets/Editor/FrontRoomsMap/`: debug window and verification menu.

The older `FrontRoomsMaze` (finite 9 × 7 maze) and `FrontRoomsRace` (route graph) generators are superseded by this layer and can be removed once week 3 lands.
