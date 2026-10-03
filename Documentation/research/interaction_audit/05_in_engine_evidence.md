# 05 — In-engine evidence (frames, material dumps, pipeline state)

Status: IN PROGRESS (2026-10-02). This file is updated as captures land.

Method (planned): a private clone of the project (Assets/Packages/ProjectSettings copied
2026-10-02 20:34) is opened in Unity 6000.3.10f1 in batch mode. A new editor script
(clone only: Assets/Editor/Audit/FrontRoomsInteractionAudit.cs) enters Play on
Assets/Scenes/FrontRooms3D.unity, starts a run through the game's own title handoff, then
drives the game's own APIs (FrontRoomsMapWorld.Hold / Use / TryOpenDoor, the Relay's
Noise / DebugPlace) and renders the game's first-person camera (its own URP camera data,
post volume and grade) to 1920x1080 PNGs. Nothing in the real project was changed.

## Code facts checked before capture

- Shipped profile has keys switched off: `doorsNeedKeys: 0` in
  Assets/Levels/FrontRoomsLevel0.asset:47 (default `false`,
  Assets/Scripts/FrontRoomsMap/FrontRoomsLevelProfile.cs:31). In the shipped game a door
  is never locked, so the "LOCKED · NEEDS THIS ZONE'S KEY" prompt
  (Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:1498) and the DoorLocked event
  (FrontRoomsMapWorld.cs:1511-1514) never fire. Keys are still placed and collected.
- Glass breaking: FrontRoomsMapWorld.cs:1546-1559 — hold progress accumulates; at 1 s the
  pane GameObject is destroyed (`Kill(window.pane)`, line 1556) and GlassBroken is raised.
  No crack stage, no shards, no particles, no decal, no camera reaction in that code path.
- Key pickup: FrontRoomsMapWorld.cs:1587-1603 — a key within 0.9 m (XZ) is destroyed and
  KeyTaken raised; no input, no animation, no camera move. The key is a primitive cube
  0.32 x 0.12 x 0.12 m floating at 1.05 m and spinning (lines 720-729).
- Door open with or without key: FrontRoomsMapWorld.cs:1508-1518 → SetDoor; the leaf
  rotates about its hinge over 0.55 s (TickDoors, lines 1573-1585). Nothing differs when
  a key is used.

(Capture results follow below once the run completes.)
