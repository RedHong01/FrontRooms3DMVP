# FrontRooms map generation

The design plan replaces the straight train of rooms with an endless Level 0
maze. This layer generates it as data (cells, edges, zones, keys) and a
separate walkable test scene builds it as greybox geometry. The main game scene
still runs on `FrontRoomsRoomStream` until the test scene is approved.

## Grid

- A **cell** is a 3 m square, one corridor wide. Cell `(x, y)` covers world X `[3x, 3x+3)` and Z `[3y, 3y+3)`.
- A **chunk** is 8 × 8 cells (24 m) and is the unit that is built and dropped around the player.
- Every edge between two neighbouring cells has one **kind**: `Open`, `Arch` (a doorless doorway: blocks sight, not movement), `Wall`, `Door`, `Window`.

## Level 0 grammar

The Backrooms are walls and doorways, not columns. Each chunk is carved in two passes:

1. **Maze.** A random depth-first spanning tree over the 64 cells. Its edges are never walls, so every cell stays reachable, and its long branches read as corridors. Some tree edges become doorways (standard 30 %, low 25 %, tall 10 %), the rest stay open corridor.
2. **Rooms.** Rectangles carved on top of the maze, with every edge inside them open: standard zones get two rooms of 2–4 cells, low zones two of 2–3, tall zones one hall of 5–7.

Every other edge inside a zone is a wall, a doorway or open: standard 82 / 10 / 8 % (the maze), low 50 / 20 / 30 % (it leaks), tall 30 / 10 / 60 % (halls). Doorways get a random width (1.1–1.8 m) and an off-centre position from the edge hash, so no two line up.

Pillars appear only in tall halls (6 % of corners).

## Zones and heights

Each chunk owns one random site. A cell belongs to the zone of the nearest site,
so zones are irregular and cross chunk borders. Each zone rolls a ceiling class:
`Low` 2.4 m, `Standard` 2.9 m, `Tall` 5.4 m (shares 35 / 55 / 10 %).

- Where the height changes, an edge is a `Wall` unless it opens as an exit, and the taller side decides the exit: **Door** between low and standard, **Window** whenever one side is tall.
- Every low or standard zone has one **key**, in its cell nearest the site. Tall zones are left through windows and have no key.

## Guarantees

- **Reachable:** the maze tree connects every cell of a chunk, and each chunk border has one required opening, so every cell connects to every other (doors and windows count as passable).
- **Borders agree:** zones, heights, border edges and border corners are pure functions of the seed and world coordinates, so neighbouring chunks agree whichever is built first.
- **Revisits shift (decision 2):** a chunk the player has been away from for at least 30 s is rebuilt with a new revision when they come back. The maze, rooms and interior walls change. Borders, zones and keys stay the same. It is always at least 24 m away and inside the fog when it is rebuilt, so the change is never seen.

## Walkable test scene

`Assets/Scenes/FrontRoomsMapTest.unity` (**FrontRooms → Map → Open walkable test scene**) holds one `FrontRoomsMapWorld`. On Play it:

- keeps the 3 × 3 chunks around the player built and drops the rest;
- builds walls, doorways, doors, windows, ceilings at zone height, and one fluorescent fixture per cell, as 6 m mesh blocks with one collision mesh per chunk;
- runs every fixture on its own: steady, occasional stutter, failing ballast, dead with rare blinks, or dim, rolled per lamp from the seed and its cell;
- hides everything past 20 m in fog, under the 24 m distance to the first unbuilt chunk.

Controls: click to look, WASD, Shift sprints on about 5 s of stamina, E opens and shuts doors, hold E breaks glass, Esc frees the cursor. Doors open without a key by default (`Doors Need Keys` on the component), so a test walk never gets stuck. The wallpaper is a placeholder print until the reference pattern is supplied.

## Editor tools

- **FrontRooms → Map → Debug map**: top-down view with seed, area, chunk grid, generation settings, hover info and *Shift hovered chunk*.
- **FrontRooms → Map → Verify 100 seeds**: checks 100 seeds over 8 × 8 chunks each and writes `Verification/map-verification-latest.json`.
- **FrontRooms → Map → Capture test views**: builds the area around the spawn in edit mode and renders four views to `Verification/map-test-*.png`.
- Headless: `-executeMethod FrontRoomsMapVerification.RunBatch`, `FrontRoomsMapTestScene.CreateBatch`, `FrontRoomsMapTestScene.CaptureBatch`.

## Code

- `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs`: types, `MapSettings`, `FrontRoomsMapGenerator`, `FrontRoomsMapCache`. Plain C#, no UnityEngine dependency.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapValidator.cs`: the checks above.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `FrontRoomsMapWalker.cs`: the test scene's level builder and player.
- `Assets/Editor/FrontRoomsMap/`: debug window, verification, test scene menu and captures.

The older `FrontRoomsMaze` (finite 9 × 7 maze) and `FrontRoomsRace` (route graph) generators are superseded by this layer and can be removed once the test scene is approved.
