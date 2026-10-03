# FrontRooms Level Designer (P1–P3)

Author a room as data, see it in the game's own build next to the editor, and let the generator place it in the real maze. Every number follows `LEVEL_MODULE_SPEC.md`.

## Use it

1. **FrontRooms → Level Designer → Open** (or press *Open in Level Designer* in a room module's Inspector). This opens `Assets/Scenes/FrontRoomsLevelDesigner.unity` on the module and the **Level Designer window**, docked as a tab beside the Inspector (floating if no Inspector is open). **FrontRooms → Level Designer → Window** opens the window alone.
2. **Left: the preview.** The Scene view frames the room; the Game view shows the eye camera standing in its first opening. The room is built by the game's own map code, in a maze whose zones take the room's height and theme, with lamps, columns, the Office kit, piles and the Office grade exactly as in the game (the generator's own modules are left out of the preview, so every tagged prop is this room's). The Scene view is also an editor: see *In the Scene view*.
3. **Right: the window** is the design panel. Every edit rebuilds the preview. A module's own Inspector still edits it with the same plan and sections (no module list, palette or Scene selection sync there).
4. **Play here** (window, Preview section) or Play in the designer scene walks the room (WASD, mouse, Shift, E).

New rooms: **New** in the window or **FrontRooms → Level Designer → New room module** (saved in `Assets/Levels/Modules`). Samples: **Create sample modules** (a Level 0 waiting room, an Office bullpen, a tall pillar hall, a low store room) makes the missing ones and never overwrites; **Reset sample modules** puts them back as shipped (asks first).

## The window

| Section | What it does |
|---|---|
| Modules | every room module asset, with a search field; **New**, **Duplicate**, **Rename**, **Ping**. Picking one shows it in the preview (undoable on the preview) and frames it; the pick survives script reloads and Play. A row says *generator* when the level profile uses the module |
| Room | notes; **Width, Depth** in 3 m cells (1–8); **Theme, Ceiling** Level 0 or Office (Office is Standard height), Low 2.4 / Standard 2.9 / Tall 5.4 m; **Fill** **Auto** as a generated room (Office kit in Offices, sometimes a pile in Level 0 halls ≥ 4 × 4), **None** only your props, **Office** the Office kit fills round your props, **Pile** a furniture pile; **Columns** **Auto** the map's 6 m grid rule (pale squares in the plan: where it can put them), **None**, **Custom** click inner corners (Shift: 0.9 m) |
| Plan | north up. Click an edge: wall → arch (doorway) → open. Right-click a cell: its lamp (Auto, Steady, Stutter, Failing, Dead, Dim, Off). Green strips: floor kept clear inside openings. Props: click to select (again: the one underneath), drag to move (0.05 m snap, Ctrl 0.5 m; the preview rebuilds when you let go), R turns 90°, Delete removes, Esc deselects. The dark band on a prop is its front. With a kit armed, a click places it (Shift-click keeps it armed, Esc stops); a green ghost shows where it will stand |
| Palette | every kit asset with its thumbnail, **All / Floor / Wall / DeskTop** and a search field (hover a tile for its size). Click a kit to arm it (again to disarm), or drag it into the plan or onto the floor in the Scene view. Where it lands: floor kits at the point, snapped to 0.05 m; **wall units** with their back 3 cm off the nearest wall face (the room's walls and inner walls, a cell edge at a time; doorways and openings are not walls), centred where they were put and clear of the walls at the ends; hung pieces (a *hang* anchor: the clock) 2.1 m up; **desk-top items** on the top of the prop under them, turned with it, without a collider (on the floor if there is no top) |
| Props | the module's props in placing order: click a row to select, ▲ ▼ reorder, ✕ removes. Under it the selected prop's fields: kit, X/Z, height above the floor (wall pieces: clock, interior window), yaw, *No collider* for clutter; Turn 90°, Duplicate, Remove |
| Preview | **Seed** and **Turn** (quarter turns clockwise, as the generator may place it) of the preview, **Rebuild**, **Frame**, **Play here** (opens the designer scene on the module if needed and enters Play mode) |
| Generator | **Used by the generator** adds the module to the level profile's *Modules* or takes it out; the level's **module chance** and **module tier** (the profile's generation numbers); the module's weight, may rotate and tier range. Profile edits are undoable and mark `Assets/Levels/FrontRoomsLevel0.asset` dirty (save the project to keep them). It warns when the level's tier is outside the module's range or the weight is 0 |
| Checks | **errors**: no way in, inner walls cutting cells off, a prop in a wall or above the ceiling, props blocking an opening or cutting part of the room off (a 0.25 m walk test with the player's 0.3 m body); **warnings**: a prop in an opening's or an inner doorway's clear strip, a side of 7–8 cells (it meets the chunk border, where the map decides the edges) |

Doors and windows are not in the panel on purpose: the map puts them where a room meets a zone of another height (decision 1). Edges on the outside of a room that meet another height, or the chunk border, stay as the map makes them, and the map may open one of the room's walls to keep the maze connected. A module prop that would stand across such a real opening is left out (with a console warning).

## In the Scene view

While the designer scene is the active scene (not in Play):

- **Drop** a kit from the palette on the floor: it becomes a prop there, placed by the palette's rules (a green footprint shows where while you drag), and is selected once the preview has rebuilt.
- **Move or turn** a prop with the usual Move and Rotate tools, or its Transform fields: the module follows as you go (X and Z snapped to 0.05 m, only along the axes it moved, so a wall unit keeps its exact distance from the wall; yaw in whole degrees). The preview rebuilds 0.3 s after you let go (never while a handle is held: that would destroy the object you are dragging) and the prop is selected again. Height is the panel's and scale is not kept: a lifted or scaled prop goes back at the rebuild. One Undo puts the move back in the module and the Scene.
- **Delete** (Edit → Delete, ⌘⌫) removes the selected props from the module (undoable). Deleting from the Hierarchy only removes the preview's copy, which comes back at the next rebuild.
- Clicking a prop selects the whole kit, not a mesh inside it. A prop selected in the Scene is selected in the window and the other way round, and stays selected across rebuilds.
- The room's outline (orange) and its openings (green, *arch* or *open*) are drawn on the floor.

## How it works

- **`RoomModuleData`** (`FrontRoomsRoomModuleData.cs`, plain C#): the room. **`FrontRoomsRoomModule`**: it as an asset.
- **`RoomModuleStamp.Apply`**: writes a module into a generated chunk. It changes only edges inside the chunk, keeps the map's rule at zone borders, makes the module the chunk's last (fully open) room, places columns, then reopens walls if the room cut the chunk apart (generated walls first). The preview uses it, so the preview is what the game builds.
- **`FrontRoomsMapCache.Place` / `FrontRoomsMapWorld.PlaceModule`**: stamp a module whenever a chunk is generated, again after a revisit shift.
- **`FrontRoomsModulePreview`**: the scene component that rebuilds on every change. It asks the map to tag the module's props (`TagModuleProps`: module, prop index, room origin), keeps the turned data it stamped (`Stamped`, the very object in those tags), raises `Rebuilding` / `Rebuilt`, and converts between module metres and the scene: `ModuleToWorld`, `WorldToModule`, `ModuleToWorldRotation`, `WorldToModuleYaw` (a clockwise quarter turn maps (x, z) to (z, W − x), W the width before the turn, and adds 90° of yaw, as `RoomModuleData.Rotated`).
- **`FrontRoomsLevelDesignerWindow`**: the window. **`FrontRoomsModulePlanView`**: the plan with its selection and drag state, one per panel (window and Inspector). **`FrontRoomsModuleGUI`**: the sections both panels draw. **`FrontRoomsModuleEditing`**: every edit to a module (add a kit by the palette's rules, wall snapping, `AgainstWall` which the samples use too, turn, duplicate, remove, reorder), each undoable and rebuilding the preview. **`FrontRoomsRoomModuleEditor`**: the Inspector.
- **`FrontRoomsDesignerSceneTools`**: the Scene view tools. Moves are seen through `Undo.postprocessModifications`, which Unity calls for the preview's DontSave props as for saved objects; the module is written on the next editor update, because an Undo record made inside that callback is lost (both checked in batch), and the write is collapsed into the move's undo step. Delete is caught as the Scene view's *SoftDelete* command before Unity destroys anything.
- **`FrontRoomsLevelDesigner`**: menus, scene, samples, captures, the profile's module list, chance and tier.

Checks: the stamp is tested outside Unity (400 random rooms: borders unchanged, every cell connected, edges, lamps and columns as authored; rotation four times is identity), plus the 100-seed map check. Headless captures: `-executeMethod FrontRoomsLevelDesigner.CaptureBatch -quit` writes `Verification/designer-<module>-eye.png` and `-plan.png`. The P2 tools: `-executeMethod FrontRoomsLevelDesignerTests.RunBatch -quit` writes `Verification/level-designer-tests.json` (63 checks on a temporary module: palette placement against every wall and both faces of an inner wall, hung and desk-top kits; for every turn, round trips and every built prop against the conversions 26 world periods out; Scene move, turn, drop and delete with Undo; the generator toggle, chance and tier with Undo; the module's checks).

## In the game (P3)

A module the level profile lists (`Assets/Levels/FrontRoomsLevel0.asset` → *Room modules*; the window's *Used by the generator*) is placed by the generator into the real maze:

- Each carved room that is one open space rolls **Module Chance** (`generation.moduleChance`, 0.3). If it hits, a module with the room's height and theme, whose tier range includes **Module Tier** (`generation.moduleTier`, 0), and that fits the room in some allowed quarter turn, is chosen by **weight** (shared between its fitting turns).
- It is stamped at a hashed spot in the room, off the chunk border when the room leaves room for that, so the walls you drew stay yours. Where the map decides an edge (zone and chunk borders, a wall reopened to keep the maze connected), any of your props that would block it is left out with a console warning.
- The same seed always gives the same modules; a revisit shift may bring a different one. The 100-seed check runs with the library and reports how many it placed; the debug map (**FrontRooms → Map → Debug map**) outlines them in orange.
- The four samples are in the library from the start. The preview turns the generator's modules off around the room you edit, so only yours is there.

## Next

- **P4** live tuning in Play mode, gameplay markers (key spot, Relay entry), tiers from DP08 (module tier and the Relay's hearing per tier).
