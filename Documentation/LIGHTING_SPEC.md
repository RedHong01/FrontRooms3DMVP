# FrontRooms 3D lighting specification

The first-person prototype uses contrast and distance to make the rooms feel occupied by real fluorescent fixtures. The editor scene stores the generated lights, so each object can be tuned without changing the gameplay script.

## Lighting stack

- **Trilight ambient**: warm ceiling bounce (`#8D8E78`), ochre equator bounce (`#4A4231`), and a dark ground bounce (`#252016`). This keeps unlit wallpaper readable while preserving corner occlusion.
- **Soft ambient direction**: a low-intensity warm directional light (`0.22`) with soft shadows. It is a fill, not the room's main source.
- **Room light**: four independent point lights per 12 m room, each inside a rectangular housing/diffuser. Alternating lamps cast soft shadows; the others retain point falloff and emissive diffuser output for a predictable WebGL cost.
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

`FrontRoomsRoomStream` retains the authored voltage behaviour on top of these base values. Each lamp receives its own deterministic phase, pulse count, period and dropout noise. In the editor, select a `fluorescent light` under the generated room preview to tune intensity, range, colour, shadow strength, or the room seed.

## Streamed title rooms

The first title room starts at its authored intensity. When a connecting door finishes opening, the room beyond it stays dark for one second, then each ballast runs its own short flicker before the room rises with a 1.8-second SmoothStep fade. Recycled rooms reset all lamp phases before receiving their next sequence number, so the cue repeats without allocating new lights or changing the fixed five-room pool.
