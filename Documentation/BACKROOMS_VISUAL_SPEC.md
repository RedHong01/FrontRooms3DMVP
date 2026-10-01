# FrontRooms visual language / 3D prototype

The prototype now treats each room as a visual-and-audio landmark instead of a
single yellow box. The palette keeps the existing deck system (ink, paper,
yellow accent) while moving the world toward the Backrooms reference:

| Room role | Wall treatment | Floor / ceiling | Light behaviour |
| --- | --- | --- | --- |
| Lobby | faded yellow vertical arrow/chevron paper with drop seams | warm tan woven carpet / warm grey acoustic ceiling | warm, steady fluorescent ballast |
| Level 0 / Shift | ochre arrow/chevron paper with stronger seam contrast | worn tan carpet / low grey acoustic ceiling | irregular per-lamp ballast flicker and occasional dropout |
| Level 4 / Office | beige paper with fine diamond repeat | office carpet / warmer ceiling | stable warm office light |
| Level ! / Run | red paper and dark carpet | dark red ceiling | red warning light with a slow pulse |
| Exit | blue-green paper | cool dark carpet | readable cool exit contrast |

All wallpaper and carpet textures are generated at runtime. Their 256px sources
are paired with derived micro-normal maps, metre-space UVs, and mipmaps, so the
shared five-room pool gets a stable physical scale without a large texture pack.
The 3D script also adds chamfered surfaces, thin baseboards, paper drop seams,
and an acoustic ceiling grid to preserve construction scale when the player is
close to a wall. Wall cells are merged into continuous slabs, with breaks only
at openings or room-material changes; this prevents the old one-cube-per-tile
pillar effect.

The visual rules are grounded in the Backrooms references: Level 0's repeated
labyrinth and buzzing light, Level 1's landmark-led navigation, Level 2's
utility corridor turns, Level 3's room-specific danger, and Level 4's office
landmarks. See the sources in the assignment research document.

## Lighting target

The Figma references `2127:68` (Escape the Backrooms) and `2127:56` (The Exit
8) establish the target for the realtime pass: a small number of visible
fixtures should create local pools of light, while corners, door reveals and
the ceiling recesses fall off naturally. The prototype now uses Trilight
ambient colors, a low warm directional fill, and four rectangular practicals
per 12 m room. Each practical has a housing, diffuser, end caps, and its own
point light. Lobby and Office use warm ballast light; Shift has a shorter range
and can drop out; Run uses a red warning pulse; Exit uses a cool blue-green
contrast. HDR is enabled on the first-person camera so the diffuser can bloom
against the darker room without lifting every wall equally.

In the editor, the main controls are the objects named `Room light` and `Soft
ambient direction` under `EDITOR_PREVIEW / FrontRooms3D`. Their intensity,
range, color, shadow strength and bias are serialized in the scene, so a room
can be art-directed without rewriting the generator.

## Validation boundary

The changes only run during the streamed room build; room dimensions,
collisions, openings, hunter logic, and HUD layout are unchanged. Flicker is
stored per fixture in `FrontRoomsRoomStream`: each lamp gets its own deterministic
phase, pulse count, period and dropout noise, so a room reads as several aging
ballasts rather than one synchronized light multiplied four times.
