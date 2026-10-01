# FrontRooms 3D — First-person MVP

This is a separate first-person experiment built from the FrontRooms functional question: how much information is worth the seconds it costs to collect? It is a 3D greybox comparison for the 2D prototype in `/Users/redwang/Developer/ThresholdRoomsMVP`, inspired by the first-person pressure of Dark Deception and Escape the Backrooms.

## Run

Open `Builds/Mac/FrontRooms3D.app` and press **Space**. The build was compiled with Unity **6000.3.10f1** as a macOS universal player. The working project is this folder. An editable copy is also included at the sibling FrontRooms3DMVP/ folder in the assignment directory.

**WASD** moves, mouse looks, **Shift** runs, and **hold E** reads a note or breaks glass. Walk over the key, then hold E while aiming at the yellow door. **Esc** pauses; **Tab** opens the note journal; **R** retries after a result.

The title opens on an empty corridor: the camera pushes forward, the brand mark fades in, and passed corridor segments are destroyed while new ones are generated ahead. Press **Space** or **Return** to enter the playable slice: Lobby → Level 0 → Level 4 / Office → Level ! / Run → Exit. The HUD only shows the current room, hunter distance, crosshair and one context prompt.

## Scope

This MVP tests first-person readability and pressure against the same room rule, note, key, door, window and noise systems as the 2D slice. It is a short route, not the deck's final 8–12 minute experience. It uses placeholder geometry and procedural audio; no final art or human playtest claim is attached.

The original design guidance is the [FrontRooms deck](https://www.figma.com/deck/NmYGRYKlhfX6H4rbJ7QcSN). The 2D source and assignment documentation remain in `/Users/redwang/Developer/ThresholdRoomsMVP/Documentation/PROTOTYPE_BRIEF.md`.

## Edit the Unity project

Open this folder in Unity Hub with Unity 6000.3.10f1 and open Assets/Scenes/FrontRooms3D.unity. The scene contains a bootstrap object and a serialized, editable greybox preview, so walls, lights and materials are visible in the Scene view. The title corridor is runtime-only and does not replace that playable layout. Edit Assets/Scripts/FrontRoomsLevel.cs to change rooms, openings, keys and exits, and edit Assets/Scripts/FrontRooms3DGame.cs to change the first-person geometry and title tuning. The assignment-folder copy contains the same source plus LEVEL_DESIGN_GUIDE.md.

## WebGL build

Use **FrontRooms 3D → Build WebGL** or run `FrontRooms3DBuild.BuildWebGL` in batch mode. The browser output is written to `Builds/WebGL/`; Brotli compression, hashed files, data caching, no-thread WebAssembly, and decompression fallback are configured for static hosting such as GitHub Pages. See [Documentation/WEBGL_BUILD.md](Documentation/WEBGL_BUILD.md) for the exact command and hosting requirements.
