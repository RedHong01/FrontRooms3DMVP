# Unity editor workflow

The scene is now an authored, editable greybox rather than an empty bootstrap scene.

- Open `Assets/Scenes/FrontRooms3D.unity`.
- Expand `FrontRooms 3D` and then `EDITOR_PREVIEW / FrontRooms3D` in the Hierarchy.
- Edit the child objects directly: continuous wallpaper slabs, floors, ceilings, lights, openings, the first-person camera, and Hunter are ordinary scene objects.
- Play Mode uses this serialized preview as its world, so material, light, camera, and Transform edits are visible in the next run.

The room topology and interaction rules still come from `Assets/Scripts/FrontRoomsLevel.cs`. After changing the authored room grid or opening list, use **FrontRooms 3D → Create Scene** to regenerate the preview. Visual tuning can be done directly in the scene without regenerating it.

The retired 2D MVP is no longer part of the assignment. Continue editing and validating the 3D project from `Assets/Scenes/FrontRooms3D.unity`.
