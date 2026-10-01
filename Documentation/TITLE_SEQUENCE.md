# 3D title sequence

The 3D title starts in an empty FrontRooms corridor. There are no room labels, instructions, hunter, keys, notes, or gameplay panels on this screen. The brand logo is centered and fades in after a short hold in the empty room.

The title camera moves forward at a constant speed. Its corridor is divided into room segments. New segments are generated ahead of the camera and segments that have passed behind it are destroyed, keeping the number of title rooms bounded instead of growing for the duration of the title screen.

Press **Space** or **Return** to stop the sequence and enter the playable five-room slice. The normal serialized scene is reused when gameplay starts, so level edits made in the Unity Editor remain the playable layout.

The title corridor is runtime-only and lives outside the authored greybox. It uses the same wallpaper, carpet, ceiling, trim, and fluorescent-light materials resolved from the serialized scene.
