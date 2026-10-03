# 3D level design handoff

## Scene

Open Assets/Scenes/FrontRooms3D.unity. This is the first-person greybox scene. It contains the FrontRooms 3D bootstrap object; the floor, walls, ceiling, lights, notes, key, openings and hunter are generated when the scene starts.

## Change the route

Edit Assets/Scripts/FrontRoomsLevel.cs. The current 3D version uses a five-room data model that was also used by the retired 2D prototype:

- AddRoom(...) defines the room name, height, rule, note and key.
- AddOpening(...) defines hall, door and window boundaries.
- PlayerStart, HunterStart and ExitTiles define the run.
- CellW and CellH control the room dimensions.

The 3D presentation is generated in Assets/Scripts/FrontRooms3DGame.cs, inside BuildWorld(). Edit that method to replace greybox cubes with prefabs, move furniture, add lights or change the first-person camera. The Walk, Run and Radius constants near the top tune the prototype feel.

## Reset and build

Use FrontRooms 3D → Create Scene to regenerate a clean bootstrap scene. Press Play and then Space to enter the first-person run. Use FrontRooms 3D → Build macOS to export a new player.

This MVP is deliberately code-authored so a route can be changed quickly. A later pass can move the room data into a ScriptableObject or prefab scene once the 2D/3D comparison answers the current design question.
