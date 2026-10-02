# FrontRooms map generation

The design plan replaces the straight train of rooms with an endless Level 0
maze. The generator produces it as data (cells, edges, zones, keys);
`FrontRoomsMapWorld` builds it as geometry around the player. The main game
(`FrontRooms3D.unity`) plays in it: the title is still the looping room
stream, and pressing Space noclips the player into the maze.

## Main game flow

1. **Title.** `FrontRoomsRoomStream` loops the Lobby corridor with the logo, unchanged.
2. **Space.** The first door opens as before. When the camera is through it, a 0.22 s white-out covers the screen, the corridor is destroyed, and `FrontRoomsMapWorld.CreateEmbedded` builds the 5 × 5 chunks around the spawn (cell (4, 4) of chunk (0, 0)). The camera moves onto a `CharacterController` player, and the maze fades in over 0.8 s.
3. **Play.**
   - WASD and mouse to move and look. Shift sprints on 5 s of stamina, which refills after 1 s.
   - E opens or shuts a door (it swings away from you); holding E for 1 s breaks glass, and walking into the broken frame climbs through it.
   - Keys are collected by walking over them. With `doorsNeedKeys` off in the level profile (the default) they are shown but not required.
   - The HUD shows the zone name and meta line, the Relay state and distance, the prompt and hold bar, and the stamina segments under the crosshair. The hint card is timed: the first-run hint, then only flashes.
4. **Relay** (`FrontRoomsMapHunter`, the same `HunterTuning` as before):
   - **Release:** 3 s after the noclip, in a built cell 9–15 cells of walking away that the player cannot see, preferably behind them.
   - **States:** Listen → Hunt (breadth-first route through built cells) → Search, and Chase on sight. Sight is a 12 m ray at eye height; walls, shut doors and pillars block it.
   - **Doors and glass:** it breaks shut doors (2.5 s of blows) and cannot pass unbroken glass.
   - **Noise:** it walks to sprint steps (26 m), door moves (14 m) and breaking glass (40 m).
   - **Leash:** if it ends up off the built map or more than 30 cells behind, it relays itself closer, out of sight.
   - **Catch:** under 0.7 m while it sees the player.
   - **Body:** r 0.3 m, tested from 0.4 to 1.95 m. It walks straight while the body fits and otherwise plans a detour on a 0.25 m grid round furniture, columns and open door leaves. With no way round furniture it passes through it on a route that still keeps out of walls. A hunt that ends inside furniture stops beside it. A door it breaks swings away from it.
5. **Caught.** The result shows time, zones crossed, keys taken and doors it broke. R restarts: same title, new maze (or the same one if `runSeed` is set).

## Level profile

Every tunable number of the level is one asset, `Assets/Levels/FrontRoomsLevel0.asset` (`FrontRoomsLevelProfile`; **FrontRooms → Map → Select level profile**). The `FrontRooms 3D` object's `Level Profile` field points at it; the test scene, the debug window and the 100-seed check resolve the same asset.

- `generation`: zone shares, maze and room grammar, exits, pillars, Office share (`MapSettings`). Its seed is the preview seed for the tools.
- Run: `runSeed` (0 = new maze each run), `buildRadius` (1–3), `chunksPerFrame`, `shiftAfterSeconds`, `doorsNeedKeys`.
- Light budget: `lightRadius`, `shadowRadius`.
- Dressing: `dressOffices`, `pileChance`.

Edits made in Play mode are kept (it is an asset) and apply from the next run; a running map works on a copy. With no asset assigned the code defaults apply. The fixed geometry (cell, wall, openings, troffer, bodies) is `ModuleUnits`, documented in `LEVEL_MODULE_SPEC.md`.

## Grid

- A **cell** is a 3 m square, one corridor wide. Cell `(x, y)` covers world X `[3x, 3x+3)` and Z `[3y, 3y+3)`.
- A **chunk** is 8 × 8 cells (24 m) and is the unit that is built and dropped around the player.
- Every edge between two neighbouring cells has one **kind**: `Open`, `Arch` (a doorless doorway: blocks sight, not movement), `Wall`, `Door`, `Window`.

## Level 0 grammar

The Backrooms are walls and doorways, not columns. Each chunk is carved in two passes:

1. **Maze.** A random depth-first spanning tree over the 64 cells. Its edges are never walls, so every cell stays reachable, and its long branches read as corridors. Some tree edges become doorways (standard 30 %, low 25 %, tall 10 %), the rest stay open corridor.
2. **Rooms.** Rectangles carved on top of the maze, with every edge inside them open: standard zones get two rooms of 2–4 cells, low zones two of 2–3, tall zones one hall of 5–7.

Every other edge inside a zone is a wall, a doorway or open: standard 82 / 10 / 8 % (the maze), low 50 / 20 / 30 % (it leaks), tall 30 / 10 / 60 % (halls). Doorways get a random width (1.1–1.8 m) and an off-centre position from the edge hash, so no two line up.

Columns stand on the world 6 m grid (cell corners with both indices even), only inside rooms that are one open space, at least 3 × 3 cells, never in Low zones. A qualifying room rolls once (Level 0 25 %, Office 75 %, Tall hall 70 %) and then fills every grid corner inside it: 0.6 m columns in Level 0, 0.9 m in Offices (with bulkheads between them) and tall halls. See `LEVEL_MODULE_SPEC.md` §3.

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

`Assets/Scenes/FrontRoomsMapTest.unity` (**FrontRooms → Map → Open walkable test scene**) holds one standalone `FrontRoomsMapWorld` with its own walker and debug HUD. Both modes:

- keep the 5 × 5 chunks around the player built, adding one new chunk per frame (nearest first), and drop the rest;
- build walls, doorways, doors, windows, ceilings at zone height and one troffer per cell. These go into 6 m mesh blocks, with one collision mesh per chunk. Office-zone cells use the Office surfaces;
- run every lamp on its own: steady, occasional stutter, failing ballast, dead with rare blinks, or dim. Each is a downward 162° spot of intensity 5, and one lamp in three casts shadows within 9 m;
- use the shared ambient and haze (`FrontRoomsLook.ApplyAmbient`). The camera's far plane stops 2 m short of the first unbuilt chunk;
- furnish Office rooms through `FrontRoomsOfficeKit.Dress` (with the room's columns as obstacles), and sometimes halls of at least 4 × 4 cells through `FrontRoomsFurniturePile.Build`, one room per frame after the chunk is built. Only rooms that are one open space are dressed. Both kits are found by reflection and skipped while they don't exist.

Controls: click to look, WASD, Shift sprints on about 5 s of stamina, E opens and shuts doors, hold E breaks glass, Esc frees the cursor. Doors open without a key by default (`doorsNeedKeys` in the level profile), so a test walk never gets stuck.

## Editor tools

- **FrontRooms → Map → Debug map**: top-down view with a preview seed, area, chunk grid, hover info and *Shift hovered chunk*. *Settings* picks the level profile and edits its generation numbers (with Undo).
- **FrontRooms → Map → Select level profile** / **Assign level profile to main scene** (batch: `-executeMethod FrontRoomsLevelProfiles.SetupBatch -quit`).
- **FrontRooms → Map → Verify 100 seeds**: checks 100 seeds of the level profile's generation numbers over 8 × 8 chunks each and writes `Verification/map-verification-latest.json`.
- **FrontRooms → Map → Capture test views**: builds the area around the spawn in edit mode and renders four views to `Verification/map-test-*.png`.
- **FrontRooms → Map → Play main scene on autopilot**: plays `FrontRooms3D.unity` unattended. It presses Space, noclips, then walks breadth-first routes for 75 s, opening doors and sprinting once. Frames and `report.json` go to `Verification/main-autopilot`. Batch: `-executeMethod FrontRoomsMainScenePlaytest.RunBatch`, with no `-quit`; it exits 0 on PASS.
- **FrontRooms → Map → Test Relay navigation**: builds the map around the spawn, scatters test furniture and sends the Relay on 60 hunts; writes `Verification/relay-nav-test.json`.
- Headless: `-executeMethod FrontRoomsMapVerification.RunBatch`, `FrontRoomsMapTestScene.CreateBatch`, `FrontRoomsMapTestScene.CaptureBatch`, `FrontRoomsRelayNavTest.RunBatch`.

## Code

- `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs`: types, `MapSettings`, `FrontRoomsMapGenerator`, `FrontRoomsMapCache`. Plain C#, no UnityEngine dependency.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapValidator.cs`: the checks above.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs`: the modular unit spec in code. `FrontRoomsLevelProfile.cs`: the level profile asset type.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`: the level builder, both embedded in the game and standalone in the test scene. `FrontRoomsMapWalker.cs` is the test scene's player.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs`: the Relay on the map.
- `Assets/Scripts/FrontRooms3DGame.cs`: title, noclip, map play, HUD, and the editor-only autopilot.
- `Assets/Editor/FrontRoomsMap/`: debug window, verification, test scene menu and captures.

The older `FrontRoomsMaze` (finite 9 × 7 maze) and `FrontRoomsRace` (route graph) generators are superseded by this layer and can be removed once the test scene is approved.
