# FrontRooms 3D lighting specification

The first-person prototype uses contrast and distance to make the rooms feel occupied by real fluorescent fixtures. The editor scene stores the generated lights, so each object can be tuned without changing the gameplay script.

## Lighting stack

- **Trilight ambient**: cool ceiling bounce (`#5B5E5A`), warm equator bounce (`#26221B`), and a dark ground bounce (`#0F0D0A`). This keeps unlit wall faces visible while preserving corner occlusion.
- **Soft ambient direction**: a low-intensity cool directional light (`0.10`) with soft shadows. It is a fill, not the room's main source.
- **Room light**: three point lights per room, each with soft shadows and a short range. Their inverse-square falloff produces visible pools below the fixtures.
- **Atmosphere**: Exponential Squared fog (`#1B1A17`, density `0.024`) separates distant doorways and prevents the long corridor from reading as a flat plane.
- **Camera**: HDR and MSAA are enabled; the near clip remains low enough for the first-person scale.

## Room temperature profiles

| Room | Light color | Intensity | Range | Read |
| --- | --- | ---: | ---: | --- |
| Lobby | warm fluorescent `#E6D5A7` | 0.98 | 6.4 | familiar yellow, stable pool |
| Shift | desaturated green-grey `#B9B694` | 0.78 | 5.7 | weaker pool, blackout can fall away |
| Office | warm white `#FFE1B1` | 1.25 | 6.8 | readable work-light |
| Red Run | red `#D8493D` | 1.15 | 6.2 | threat colour with deeper shadows |
| Exit | cool cyan `#A9D7D0` | 0.98 | 6.4 | cold contrast at the end |

`FrontRoomsLightFlicker` retains the authored voltage behaviour on top of these base values. In the editor, select a `Room light` under `EDITOR_PREVIEW / FrontRooms3D` to tune intensity, range, colour, shadow strength, or the flicker seed; the serialized scene is used in Play Mode as well.

## Streamed title rooms

The first title room starts at its authored intensity. When a connecting door finishes opening, the room beyond it stays dark for one second, gives its ballast one short flicker, then rises with a 1.8-second SmoothStep fade. Recycled rooms reset to the dark state before receiving their next sequence number, so the cue repeats without allocating new lights or changing the fixed three-room pool.
