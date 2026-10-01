# FrontRooms UI system

This prototype uses a world-first horror HUD. The room and the player's read of it stay visually dominant; the HUD gives only the next useful signal.

## Type use

- HUD meta: IBM Plex Mono, 13 px, 16 px leading. Use for room metadata, distance, controls, and event-like labels.
- UI label: Bayon, 20 px, 20 px leading. Use for state, prompt, and section labels.
- Screen title: Bayon, 88 px, 80 px leading. Use for title, start, pause, and result moments.
- Room name: Source Serif 4, 50 px, 42 px leading. Use for the current location.
- Context: Source Serif 4, 24 px, 26 px leading. Use for a clue, note, or consequence.

The runtime loads the matching font files from `Assets/Resources/Fonts` and keeps Unity's built-in font as a safe fallback if a platform cannot import the variable Source Serif file. The files are distributed under the included OFL license.

## Grid use

- Reference viewport: 1920 x 1080.
- Outer margin: 72 px.
- Columns: 12 columns, 126 px each, 24 px gutters.
- Rows: 6 rows, 136 px each, 24 px gutters.
- Gameplay comparison: two 6-column panels with a 24 px gap.
- Result states: three 4-column cards sharing the same baseline.
- Internal rhythm: 24 px. Keep panels and prompts on that rhythm.

## Information layers

- Persistent: current room, current state, and one threat signal (hunter distance / chase state).
- Contextual: one prompt, one clue, or the note/map view when the player is close enough or asks for it.
- Secondary: notes/map and pause controls are opened with `Tab` or `Esc`; they are not permanently stacked onto the play view.

## Runtime mapping

- 2D: WASD or arrows move, `Shift` runs, hold `Q` to read, hold `E` to break glass, `Tab` opens the map, `Esc` pauses, `R` retries.
- 3D: WASD moves, mouse looks, `Shift` runs, hold `E` reads/breaks, `E` opens a keyed door, `Tab` opens notes, `Esc` pauses, `R` retries.
- `Space` or `Return` starts from the title card.

## Runtime HUD mapping

- Room and threat information are direct typography overlays aligned to the 72 px screen margin. They have no persistent card background.
- The room name is a single 50 px line with a no-wrap overflow policy so long names such as `LEVEL 4 / OFFICE` never bleed into the scene.
- A 4 px yellow rule is the only persistent threat accent. Context and Notes retain dark containers because they temporarily replace the play view.
- The title, pause, and result states remain full-screen overlays; they are state changes rather than persistent HUD windows.
