# 3D title sequence

The 3D title starts in an empty FrontRooms corridor. There are no room labels, instructions, hunter, keys, notes, or gameplay panels on this screen. The brand logo is centered and fades in after a short hold in the empty room.

The title camera moves forward at a constant speed. Its corridor is divided into room copies, each with a real frame, double door, rear seal, entry transform and fluorescent fixture. The stream keeps a fixed pool of three copies: the oldest copy is repositioned ahead after it is safely behind the camera, so the run can continue without allocating an unbounded number of meshes or lights. Coordinates are rebased every 256 metres to keep WebGL floating-point precision stable. If the player does nothing, this loop continues and the title remains visible indefinitely.

Press **Space** or **Return** to request the handoff. The camera does not cut to the authored map. It finishes the approach to the next door, animates the two leaves open, connects the next room copy and eases to its `Entry / 2m inside` anchor. Only then does WASD/mouse control become active. The player can move within the streamed room with the same room bounds and door threshold; the gameplay HUD appears at handoff. The normal serialized scene remains available for editing and for the separate authored five-room slice.

The title corridor is runtime-only and lives outside the authored greybox. It uses the same wallpaper, carpet, ceiling, trim, and fluorescent-light materials resolved from the serialized scene. `FrontRoomsRoomStream` exposes `RoomCount`, `RecycledCount`, `RebaseCount`, `PendingAnchorPosition`, and `HasControl` for debugging or a future telemetry overlay. An optional `roomTemplate` can be assigned to author the repeated room in the Inspector; when it is empty, the component builds the editable placeholder walls, floor, ceiling, frame, and doors procedurally.

The title logo uses native SVG `VectorImage` artwork. The complete wordmark includes the solid final S; the two offset S paths are separate vector assets that begin on top of that S and move outward in sequence. Their motion clock is `FrontRoomsRoomStream.FirstDoorProgress`, so the movement starts exactly when the first corridor door begins opening. The complete mark stays visible after the motion finishes and only fades during the requested Space/Return handoff. The PNG and shader path remain as an older-platform fallback.

### Continuous-pool boundary recovery

The title camera can cross a room boundary between two rendered frames. The stream now advances `currentSequence` through every already-connected room whose `endZ` has been crossed, instead of requiring one frame to land exactly on the boundary. This keeps the fixed three-room pool eligible for recycling after every cycle; the loop is bounded by the pool size and does not allocate during playback.
