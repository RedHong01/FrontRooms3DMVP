# 3D title sequence

The 3D title starts in an empty FrontRooms corridor. There are no room labels, instructions, hunter, keys, notes, or gameplay panels on this screen. The brand logo is centered and fades in after a short hold in the empty room.

The title camera moves forward at a constant speed. Its corridor is divided into room copies, each with a real frame, double door, rear seal, entry transform and fluorescent fixture. The stream keeps a fixed pool of three copies: the oldest copy is repositioned ahead after it is safely behind the camera, so the run can continue without allocating an unbounded number of meshes or lights. Coordinates are rebased every 256 metres to keep WebGL floating-point precision stable.

Press **Space** or **Return** to request the handoff. The camera does not cut to the authored map. It finishes the approach to the next door, animates the two leaves open, connects the next room copy and eases to its `Entry / 2m inside` anchor. Only then does WASD/mouse control become active. The player can move within the streamed room with the same room bounds and door threshold; the gameplay HUD appears at handoff. The normal serialized scene remains available for editing and for the separate authored five-room slice.

The title corridor is runtime-only and lives outside the authored greybox. It uses the same wallpaper, carpet, ceiling, trim, and fluorescent-light materials resolved from the serialized scene. `FrontRoomsRoomStream` exposes `RoomCount`, `RecycledCount`, `RebaseCount`, `PendingAnchorPosition`, and `HasControl` for debugging or a future telemetry overlay. An optional `roomTemplate` can be assigned to author the repeated room in the Inspector; when it is empty, the component builds the editable placeholder walls, floor, ceiling, frame, and doors procedurally.

The title logo uses the supplied SVG/PNG artwork with a white UI shader. The two offset S forms are split into a second image layer so the Inspector field `Logo Motion Variation` can compare two treatments: `Slide Then Fade` moves the S mark in from the left and fades the main lockup, while `Full Lockup` makes the same slide but keeps the complete wordmark visible.
