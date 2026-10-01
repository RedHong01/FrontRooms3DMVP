# FRONTROOMS / Level 0 maze design

## Intent

The room stream should feel like the Backrooms' Level 0: a large patchwork of ordinary office and retail back rooms, not a sequence of showcase rooms. The generated layout keeps the visual grammar familiar (yellowed wallpaper, damp carpet, fluorescent hum) while making orientation unreliable through branches, loops, occluded sightlines and small room shifts.

The reference description for Level 0 treats it as a labyrinth that changes as the player progresses, so this prototype uses a deterministic seed per run rather than pure random noise. A seed gives us reproducible critique builds, replayable race tests and the same map for 2D and 3D.

## Generation recipe

1. **Topology**: generate a 9×7 room grid with a randomized depth-first spanning tree. Every cell is reachable and the tree creates dead ends and long turns.
2. **Loops**: open 18% additional neighbour edges after the tree. This creates alternate routes and re-entry loops without turning the space into a uniform open grid. The validation range is 5–35%.
3. **Critical path**: breadth-first search from the start cell to the exit cell marks one shortest route. Start is always on the west edge; exit is always on the east edge. A keyed door is placed near the middle of that route.
4. **Room grammar**: 70–80% standard lobby language; 18% shifting seams/lighting; 12% office or service variation; roughly 10% threat pressure on the main route; rare landmarks only in branches. Each cell gets a short read cue so 2D and 3D adapters stay aligned.
5. **Playability constraints**: no unreachable cells, one guaranteed start→exit path, one mid-route decision, minimum two traversals between start and exit, and no dead-end branch longer than the encounter budget. The generator emits a validation object and a JSON snapshot for critique.
6. **Streaming**: only the current room plus a two-room exposure window is rendered. Rooms behind the player are pooled and recycled with their sequence seed; the logical graph remains stable for route checks.

## Race and horror pacing

- Opening: 2–3 familiar rooms, stable light and low threat.
- Pressure: a loop or side branch gives a quiet but longer detour; the direct route is faster but louder or keyed.
- Threat: a main-route room can change light temperature, audio bed and sightline length without changing collision topology.
- Reset: a landmark branch or a distinct carpet seam lets the player rebuild a mental map before the next pressure beat.
- Exit: the east-edge cell uses cool contrast and a readable threshold; it is never selected as a random dead end.

## Current implementation

`Assets/Scripts/FrontRoomsMaze/FrontRoomsMazeGenerator.cs` is the shared deterministic data generator. `FrontRoomsMazePreview` and the **FrontRooms → Maze → Build or refresh editor preview** menu create an editable low-poly labyrinth in the Unity scene without generating a build. The same `FrontRoomsMazeSpec` is deliberately renderer-agnostic so the existing 2D prototype can consume it later.
