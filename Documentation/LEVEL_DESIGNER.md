# FrontRooms Level Designer (P1)

Author a room as data, see it in the game's own build next to the editor, then (P3) let the generator use it. Every number follows `LEVEL_MODULE_SPEC.md`.

## Use it

1. **FrontRooms → Level Designer → Open** (or select a room module and press *Open in Level Designer*). This opens `Assets/Scenes/FrontRoomsLevelDesigner.unity` and selects the module.
2. **Left: the preview.** The Scene view frames the room; the Game view shows the eye camera standing in its first opening. The room is built by the game's own map code, in a maze whose zones take the room's height and theme, with lamps, columns, the Office kit, piles and the Office grade exactly as in the game.
3. **Right: the Inspector** of the room module is the design panel. Every edit rebuilds the preview.
4. **Play** in the designer scene to walk the room (WASD, mouse, Shift, E).

New rooms: **FrontRooms → Level Designer → New room module** (saved in `Assets/Levels/Modules`). Samples: **Create sample modules** (a Level 0 waiting room, an Office bullpen, a tall pillar hall, a low store room) makes the missing ones and never overwrites; **Reset sample modules** puts them back as shipped (asks first).

## The panel

| Section | What it sets |
|---|---|
| Notes | free text for the team |
| Width, Depth | footprint in 3 m cells (1–8 each) |
| Theme, Ceiling | Level 0 or Office (Office is Standard height); Low 2.4 / Standard 2.9 / Tall 5.4 m |
| Fill | **Auto** as a generated room (Office kit in Offices, sometimes a pile in Level 0 halls ≥ 4 × 4), **None** only your props, **Office** the Office kit fills round your props, **Pile** a furniture pile |
| Columns | **Auto** the map's 6 m grid rule (pale squares in the plan: where it can put them), **None**, **Custom** click inner corners (Shift: 0.9 m) |
| Plan | north up. Click an edge: wall → arch (doorway) → open. Right-click a cell: its lamp (Auto, Steady, Stutter, Failing, Dead, Dim, Off). Green strips: floor kept clear inside openings |
| Props | pick a kit asset and *Add*. In the plan: click to select (click again for the prop underneath), drag to move (0.05 m snap, Ctrl 0.5 m; the preview rebuilds when you let go), R turns 90°, Delete removes, Esc deselects. Fields: kit, X/Z, height above the floor (wall pieces: clock, interior window), yaw, *No collider* for clutter. The dark band on a prop is its front |
| Where the generator may use it | weight, may rotate, tier range (used from P3) |
| Checks | **errors**: no way in, inner walls cutting cells off, a prop in a wall or above the ceiling, props blocking an opening or cutting part of the room off (a 0.25 m walk test with the player's 0.3 m body); **warnings**: a prop in an opening's or an inner doorway's clear strip, a side of 7–8 cells (it meets the chunk border, where the map decides the edges) |

Doors and windows are not in the panel on purpose: the map puts them where a room meets a zone of another height (decision 1). Edges on the outside of a room that meet another height, or the chunk border, stay as the map makes them, and the map may open one of the room's walls to keep the maze connected. A module prop that would stand across such a real opening is left out (with a console warning).

## How it works

- **`RoomModuleData`** (`FrontRoomsRoomModuleData.cs`, plain C#): the room. **`FrontRoomsRoomModule`**: it as an asset.
- **`RoomModuleStamp.Apply`**: writes a module into a generated chunk. It changes only edges inside the chunk, keeps the map's rule at zone borders, makes the module the chunk's last (fully open) room, places columns, then reopens walls if the room cut the chunk apart (generated walls first). The preview uses it now and the generator will in P3, so the preview is what the game builds.
- **`FrontRoomsMapCache.Place` / `FrontRoomsMapWorld.PlaceModule`**: stamp a module whenever a chunk is generated, again after a revisit shift.
- **`FrontRoomsModulePreview`**: the scene component that rebuilds on every change.
- **`FrontRoomsRoomModuleEditor`**: the panel. **`FrontRoomsLevelDesigner`**: menus, scene, samples, captures.

Checks: the stamp is tested outside Unity (400 random rooms: borders unchanged, every cell connected, edges, lamps and columns as authored; rotation four times is identity), plus the 100-seed map check. Headless captures: `-executeMethod FrontRoomsLevelDesigner.CaptureBatch -quit` writes `Verification/designer-<module>-eye.png` and `-plan.png`.

## Next

- **P2** a dedicated docked window (module list, palette, drag from the palette into the Scene view, two-way sync with props moved in the Scene).
- **P3** the generator picks modules by weight, height, theme, tier and rotation into rooms that fit, with the 100-seed check extended to stamped maps.
- **P4** live tuning in Play mode, gameplay markers (key spot, Relay entry), tiers from DP08.
