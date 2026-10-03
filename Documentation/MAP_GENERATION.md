# FrontRooms map generation

The design plan replaces the straight train of rooms with an endless Level 0
maze. The generator produces it as data (cells, edges, zones, keys);
`FrontRoomsMapWorld` builds it as geometry around the player. The main game
(`FrontRooms3D.unity`) plays in it: the title is still the looping room
stream, and pressing Space hands the player control in the stream room they
are watching. The maze lies behind that corridor's next shut door.

## Main game flow

1. **Title.** `FrontRoomsRoomStream` loops the Lobby corridor with the logo, unchanged.
2. **Space.** No glide and no white-out: the player takes over where the camera is.
   - **Stream:** it ends at its first door that is still shut (`FrontRoomsRoomStream.EndStreamAt`). Rooms past that door are put away, and nothing recycles or rebases any more.
   - **Placement:** `FrontRoomsMapWorld.CreateEmbedded` attaches the maze behind that door.
     - Its root is the nearest multiple of 192 m where the door opens onto a cell (the title runs at x 256.5 = a cell centre, z 0 = room ends on cell lines).
     - The five cells across the door are Standard-height Level 0, matching the stream room's 2.9 m ceiling and paper.
     - The cell ahead is open and leads on for 150+ cells.
   - **Start area:** the stream rooms are the map's start area (`SetStartArea`). The map builds nothing there and walls it off on three sides. The stream room's end wall, carried out by two facade strips, forms the fourth side with the door in it. `IsBuilt` and `PassageBetween` treat it as no map.
   - **Streaming:** the maze streams in at the normal per-frame budget round the door (`StreamFocus`, `Begin(player, false)`). Map lamps whose light would reach through the stream walls are held dark (`StartLampsNorth/South`).
   - **The door:** it opens once everything in sight through it is built and furnished (`ReadyAround(BuildRadius)`, at most 3 s after Space).
3. **Leaving the start rooms.**
   - Once the player is 4 m into the maze, the door swings shut and stays shut.
   - The stream's lamps fade out, and the maze's lamps beside the rooms fade in.
   - The rooms behind it are destroyed one per frame. The last room goes, and the start area is handed back to the map, once every chunk round it has been dropped.
4. **Play.**
   - WASD and mouse to move and look. Shift sprints on 5 s of stamina, which refills after 1 s.
   - E opens or shuts a door (it swings away from you); holding E for 1 s breaks glass, and walking into the broken frame climbs through it.
   - Keys are collected by walking over them. With `doorsNeedKeys` off in the level profile (the default) they are shown but not required.
   - With `doorsNeedKeys` on, a shut door needs the key of the zone you stand in (`DoorLocked` otherwise). The first time a key opens a door, the map raises `DoorUnlocked(door, zone, lock point)` (the lock: 1.0 m up, 0.08 m in from the latch jamb, on your side) and the leaf swings after `UnlockSwingDelay` (0 by default; the key push-in sets it). From then on that door is unlocked from both sides.
   - Esc (or losing focus) pauses; `FrontRooms3DGame.Paused(bool)` reports it, for the sound layer.
   - The HUD shows the zone name and meta line, the prompt and hold bar, and the stamina segments under the crosshair. The hint card is timed: the first-run hint, then only flashes. The Relay's state and distance are an assist, off by default (Red, 2026-10-03): Esc → O (display settings) → T turns them on, remembered across runs (`FrontRooms.Assist.RelayReadout`).
5. **Relay** (`FrontRoomsMapHunter`, the same `HunterTuning` as before):
   - **Release:** 3 s after the door to the stream rooms has shut behind the player, in a built cell 9–15 cells of walking away that the player cannot see, preferably behind them.
   - **States:** it does not know where the player is. Listen → **Wander** to a random place 6–14 cells away (at 80 % of hunt speed, keeping to shut doors) → Listen … It **chases only once it sees the player**: a 12 m ray at eye height that walls, shut doors and columns block. A noise sends it walking to that spot (Hunt), without running, even mid-search. Losing sight in a chase, it goes where it last saw the player; if it was right behind them as they went through a door, it follows into the room behind that door instead. Either way it then **searches that room** (up to 3 spots, listening 1.1 s at each, at 70 % of hunt speed; a carved room's cells, or the cells within 2 steps that need no door) and gives up, back to wandering. It does not follow the player further unless it hears or sees them again.
   - **Doors and glass:** it breaks shut doors and cannot pass unbroken glass. Blows land 0.5, 1.0, 1.5 and 2.0 s into BreakDoor and the last one at 2.4 s; the door gives at 2.5 s (`breakDoorSeconds`), and it waits 0.25 s for the leaf to fall. `DoorBlow` fires at each blow with `BlowIndex` (0–4) and `BlowCount` (5) set.
   - **Rig hooks** (the visual chat's `FrontRoomsRelayRig`, set each frame by `FrontRooms3DGame.UpdateRelayRig`): the motion state (Search when it stands searching), the listen target (`ListenPoint`, the last noise it heard, in Listen and Search; cleared when it sees the player or relays), `DoorBlow(index, count)`, the ceiling height of its cell, and `DoorSqueeze` (1 on the line of an open or broken door it is in, 0 from 0.6 m out). Its footsteps come from the rig's `Step` under FMOD; the old timed steps play only when FMOD is not ready.
   - **Noise:** it walks to sprint steps (26 m), door moves (14 m) and breaking glass (40 m).
   - **Arrival spots:** release and relays prefer a designer's Relay entry (a module marker) behind the player, then a cell behind them, then an entry anywhere, then the nearest cell; all under the same rules (9–15 cells of walking, body fits, unseen). Every arrival raises `Arrived(feet, tag)` with the entry's tag ("vent", "doorway", …) or null.
   - **Leash:** if it ends up off the built map it relays at once; if it is more than 30 cells away and has neither seen nor heard the player for 45 s, it relays itself closer, out of sight.
   - **Catch:** under 0.7 m while it sees the player.
   - **Body:** r 0.3 m, tested from 0.4 to 1.95 m. It walks straight while the body fits and otherwise plans a detour on a 0.25 m grid round furniture, columns and open door leaves. With no way round furniture it passes through it on a route that still keeps out of walls. A hunt that ends inside furniture stops beside it. A door it breaks swings away from it.
6. **Difficulty tiers** (DP08 proposal; level profile *Difficulty tiers*). The run starts at tier 1 and rises every 4 new zones (zones 5–8 are tier 2, and so on), or after 120 s without a new zone, up to 5. `FrontRooms3DGame.TierChanged(int)` reports each rise; the HUD meta line and the Caught stats show the tier.
   - **The Relay** runs on a copy of the base tuning (the FrontRooms 3D object) scaled by the tier's row, rebuilt every frame: tier 5 is chase × 1.29 (5.4 m/s), hearing × 1.6, break time × 0.52 (1.3 s, so 3 blows instead of 5), search × 1.6. A break keeps the length it started with.
   - **The map:** a chunk takes the run's tier when it is first generated and keeps it, so rebuilding it is identical; a revisit shift takes the tier of its time. The tier raises the chunk's module tier (`moduleTier + tier − 1`) and shifts its Auto lamps toward failing and dead (tier 1: 62 % steady, 20 stutter, 10 failing, 5 dead, 3 dim; tier 5: 40 / 25 / 18 / 12 / 5). Zone heights, tall shares and key distance are not tiered: zones span many chunks, so a tier there would make neighbours disagree.
7. **Caught.** The result shows time, tier, zones crossed, keys taken and doors it broke. R restarts: same title, new maze (or the same one if `runSeed` is set).

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

## Room modules (Level Designer)

Rooms authored in the Level Designer (`LEVEL_DESIGNER.md`) can replace carved rooms. The level profile's `modules` list is the library; `generation.moduleChance` (0.3) and `moduleTier` set how often and which.

1. After the maze, the rooms and the columns, each generated room that is one open space (no later room cuts into it, every cell the same height and theme) rolls `moduleChance`.
2. If it hits, the candidates are the modules with the room's height and theme whose tier range includes `moduleTier`, in every quarter turn they allow (`allowRotate`) that fits the room. One is chosen by weight (a module's weight is shared between its fitting turns).
3. It is stamped (`RoomModuleStamp`) at a hashed spot inside the room: inner and perimeter edges inside the chunk as authored, the map's rule at zone borders and on the chunk border, columns per the module, walls reopened if the chunk was cut apart.
4. **Markers.** A module's **key spot** takes its zone's key when the key's cell (the cell holding the zone's site) lies in the module's room and the spot's cell is in the same zone: the key lies there, still, turned as the marker says (on a revisit shift it may move within its room). Its **Relay entries** are where the Relay prefers to appear (see the Relay above). The Office kit and piles keep a metre round the key and 0.8 m round each entry clear.
5. When it is built, a module prop is left out (with a console warning) if it would block a real opening, stands in a column, or stands on a prop left out (a desk-top item goes with its desk). A fill (Office kit, pile) sees the module's inner walls as obstacles and keeps its inner doorways clear.

All of it is a function of the seed, the chunk and its revision, with the library in a stable order (by asset name), so neighbours agree, rebuilds are identical and a revisit shift may bring a different module. The 100-seed check runs with the profile's library and reports how many modules it placed; outside Unity it was also run with 14 random modules at chance 0.7 (3,806 placed, 100/100). The debug map outlines placed modules in orange.

## Zones and heights

Each chunk owns one random site. A cell belongs to the zone of the nearest site,
so zones are irregular and cross chunk borders. Each zone rolls a ceiling class:
`Low` 2.4 m, `Standard` 2.9 m, `Tall` 5.4 m (shares 35 / 55 / 10 %).

- Where the height changes, an edge is a `Wall` unless it opens as an exit, and the taller side decides the exit: **Door** between low and standard, **Window** whenever one side is tall.
- Every low or standard zone has one **key**, in its cell nearest the site. Tall zones are left through windows and have no key.

## Guarantees

- **Reachable:** the maze tree connects every cell of a chunk, and each chunk border has one required opening, so every cell connects to every other (doors and windows count as passable).
- **Borders agree:** zones, heights, border edges and border corners are pure functions of the seed and world coordinates, so neighbouring chunks agree whichever is built first.
- **A chunk that fails to build** (an exception in `Build`) is undone, logged once and left out until it leaves the build radius, then tried once more; `ReadyAround` and `Settled` count it as done.
- **Revisits shift (decision 2):** a chunk the player has been away from for at least 30 s is rebuilt with a new revision when they come back. The maze, rooms and interior walls change. Borders, zones and keys stay the same. It is always at least 24 m away and inside the fog when it is rebuilt, so the change is never seen.

## Walkable test scene

`Assets/Scenes/FrontRoomsMapTest.unity` (**FrontRooms → Map → Open walkable test scene**) holds one standalone `FrontRoomsMapWorld` with its own walker and debug HUD. Both modes:

- keep the 5 × 5 chunks around the player built, adding one new chunk per frame (nearest first), and drop the rest;
- build walls, doorways, doors, windows, ceilings at zone height and one troffer per cell (a 0.6 × 1.2 m lens filling whole 0.6 m ceiling tiles). These go into 6 m mesh blocks split by ceiling height, each with its own `_CeilingHeight`, with one collision mesh per chunk. Office-zone cells use the Office surfaces;
- run every lamp on its own: steady, occasional stutter, failing ballast, dead with rare blinks, or dim. Each is a downward 162° spot of intensity 5, and one lamp in three casts shadows within 9 m;
- use the shared ambient and haze (`FrontRoomsLook.ApplyAmbient`). The camera's far plane stops 2 m short of the first unbuilt chunk;
- furnish Office rooms through `FrontRoomsOfficeKit.Dress` (with the room's columns as obstacles), and sometimes halls of at least 4 × 4 cells through `FrontRoomsFurniturePile.Build`, one room per frame after the chunk is built. Only rooms that are one open space are dressed. Both kits are found by reflection and skipped while they don't exist.

Controls: click to look, WASD, Shift sprints on about 5 s of stamina, E opens and shuts doors, hold E breaks glass, Esc frees the cursor. Doors open without a key by default (`doorsNeedKeys` in the level profile), so a test walk never gets stuck.

## Live tuning (Play)

- **Level profile:** edits during Play apply at once to the running map: build radius and chunks per frame (the far plane follows), shift delay, light and shadow radius, keys, Office dressing and pile chance (for rooms furnished from then on), and the tier table (on the next frame). Generation numbers and the module list apply on the next run: changing them under a running map would move what the player has seen.
- **Relay tuning** (FrontRooms 3D object): the base, read every frame through the tier.
- **Level Designer preview:** in Play, a module edit rebuilds only the room's chunk and keeps the walker where it stands (`FrontRoomsMapWorld.ReplaceModule`); a new size, height, theme or seed rebuilds everything.

## Editor tools

- **FrontRooms → Map → Debug map**: top-down view with a preview seed, area, chunk grid, hover info and *Shift hovered chunk*. *Settings* picks the level profile and edits its generation numbers (with Undo).
- **FrontRooms → Map → Select level profile** / **Assign level profile to main scene** (batch: `-executeMethod FrontRoomsLevelProfiles.SetupBatch -quit`).
- **FrontRooms → Map → Verify 100 seeds**: checks 100 seeds of the level profile's generation numbers over 8 × 8 chunks each and writes `Verification/map-verification-latest.json`.
- **FrontRooms → Map → Capture test views**: builds the area around the spawn in edit mode and renders four views to `Verification/map-test-*.png`.
- **FrontRooms → Map → Play main scene on autopilot**: plays `FrontRooms3D.unity` unattended. It presses Space (at 1.8 s, or `-autopilotSpaceAt N`; 1.0 starts with the door still shut 4.85 m ahead), walks out of the stream room into the maze, then walks breadth-first routes for 75 s, opening doors and sprinting once. The report adds the handoff: the slowest frames after Space and what the map built in them, when the map was ready, how long the player waited at the held door, and when the door opened and shut and the stream was removed. Frames and `report.json` go to `Verification/main-autopilot`. Batch: `-executeMethod FrontRoomsMainScenePlaytest.RunBatch`, with no `-quit`; it exits 0 on PASS.
- Headless `-executeMethod FrontRoomsMapTestScene.CaptureColumnsBatch -captureSeed N`: renders the first Level 0, Office and tall-hall column near the spawn and the ceiling straight above the spawn (troffer vs printed grid) to `Verification/map-columns-*.png` and `map-ceiling.png`.
- **FrontRooms → Map → Test Relay navigation**: builds the map around the spawn, scatters test furniture and sends the Relay on 60 hunts; writes `Verification/relay-nav-test.json`.
- **FrontRooms → Map → Test map interactions**: the Relay's blow timing, `DoorSqueeze` and `ListenPoint`; `DoorUnlocked` with and without the swing delay, from both sides, and with keys off; module props on columns (and what stands on them); the Office kit round a module's inner walls; the guard round a failing chunk build. Writes `Verification/map-interaction-tests.json`; batch `-executeMethod FrontRoomsMapInteractionTests.RunBatch -quit`.
- Headless: `-executeMethod FrontRoomsMapVerification.RunBatch`, `FrontRoomsMapTestScene.CreateBatch`, `FrontRoomsMapTestScene.CaptureBatch`, `FrontRoomsRelayNavTest.RunBatch`, `FrontRoomsMapInteractionTests.RunBatch`.

## Code

- `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs`: types, `MapSettings`, `FrontRoomsMapGenerator`, `FrontRoomsMapCache`. Plain C#, no UnityEngine dependency.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapValidator.cs`: the checks above.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs`: the modular unit spec in code. `FrontRoomsLevelProfile.cs`: the level profile asset type.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`: the level builder, both embedded in the game and standalone in the test scene. `FrontRoomsMapWalker.cs` is the test scene's player.
- `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs`: the Relay on the map.
- `Assets/Scripts/FrontRooms3DGame.cs`: title, the in-place handoff to the maze, map play, HUD, and the editor-only autopilot.
- `Assets/Editor/FrontRoomsMap/`: debug window, verification, test scene menu and captures.

The older `FrontRoomsMaze` (finite 9 × 7 maze) and `FrontRoomsRace` (route graph) generators are superseded by this layer and can be removed once the test scene is approved.
