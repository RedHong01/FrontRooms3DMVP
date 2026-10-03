# FrontRooms 3D — First-person MVP

This is a first-person experiment built from the FrontRooms functional question: how much information is worth the seconds it costs to collect? It is a 3D greybox prototype inspired by the first-person pressure of Dark Deception and Escape the Backrooms.

## Run

Open `Builds/Mac/FrontRooms3D.app` and press **Space**. The build was compiled with Unity **6000.3.10f1** as a macOS universal player. The working project is this folder. An editable copy is also included at the sibling Frontrooms3D/ folder in the assignment directory.

**WASD** moves, mouse looks, **Shift** runs, and **hold E** reads a note or breaks glass. Walk over the key, then hold E while aiming at the yellow door. **Esc** pauses; **Tab** opens the note journal; **R** retries after a result.

The title opens on an empty corridor: the camera pushes forward, the brand mark fades in, and a fixed pool of room copies is recycled ahead of it. Press **Space** or **Return** and the camera continues to the next physical door; that door opens, the next copy connects, and control is handed to the player two metres inside that same room. The stream never creates more than three room copies and rebases its coordinates during long runs. The HUD only shows the current room, hunter distance, crosshair and one context prompt once play begins.

## Scope

This MVP tests first-person readability and pressure through room rules, notes, keys, doors, windows and noise. It is a short route, not the deck's final 8–12 minute experience. It uses placeholder geometry and procedural audio; no final art or human playtest claim is attached.

The original design guidance is the [FrontRooms deck](https://www.figma.com/deck/NmYGRYKlhfX6H4rbJ7QcSN). The former 2D MVP was retired; this project is the active local source.

## Edit the Unity project

Open this folder in Unity Hub with Unity 6000.3.10f1 and open Assets/Scenes/FrontRooms3D.unity. The scene contains a bootstrap object and a serialized, editable greybox preview, so walls, lights and materials are visible in the Scene view. The title stream is runtime-only and does not replace that playable layout. Edit Assets/Scripts/FrontRoomsLevel.cs to change rooms, openings, keys and exits; edit Assets/Scripts/FrontRooms3DGame.cs for first-person/HUD behavior; and edit Assets/Scripts/FrontRoomsRoomStream.cs or assign its optional room template to tune the streamed title/arrival rooms. Build commands preserve an existing scene, so editor changes survive a build. The assignment-folder copy contains the same source plus LEVEL_DESIGN_GUIDE.md.

## WebGL build

Use **FrontRooms 3D → Build WebGL** or run `FrontRooms3DBuild.BuildWebGL` in batch mode. The browser output is written to `Builds/WebGL/`; Brotli compression, hashed files, data caching, no-thread WebAssembly, and decompression fallback are configured for static hosting such as GitHub Pages. See [Documentation/WEBGL_BUILD.md](Documentation/WEBGL_BUILD.md) for the exact command and hosting requirements.
