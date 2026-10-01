# FrontRooms level and entity slice

This document turns the public Backrooms references into an original, editable
prototype route. The project uses the atmosphere and spatial ideas as research
input; it does not ship a copied Backrooms character, film model, or protected
film asset.

## What the research changes

The current Backrooms Wiki description of Level 0 treats the space as a yellow,
wet-carpet labyrinth whose layout can shift when it is not directly observed.
It also names arches, blackout zones, red rooms, and layout changes as useful
structural variations, while keeping entity reports uncertain. That supports a
quiet first room in FrontRooms: the player learns to read thresholds before a
creature is confirmed.

The Wiki's Level 1 description moves to concrete, puddles, fog, sectors, and
flicker events where entities become more active. The Level 4 description is a
recognisable abandoned office with a lower entity density. The Hound entry
describes a predator with poor sight and strong hearing. Together these suggest
an escalation based on sound and architectural contrast rather than an enemy
that is visible from the first frame.

The Kane Pixels series and film references reinforce the same design rule:
ordinary office proportions, sickly practical light, buzzing fixtures, and
small architectural errors should carry the tension before the entity appears.
FrontRooms therefore uses original names and a low-cost greybox entity while
keeping the reference qualities in the room, light and sound behaviour.

## Route contract

The streamed route is deterministic for its first pass, then repeats in an
infinite five-profile cycle. The handoff room remains a Lobby threshold; the
first authored profile is revealed immediately after it. A pooled room changes
its profile when it is recycled, so the loop does not run out of geometry or
remain visually locked to Lobby.

| Stream sequence | Profile | Player-facing rule | Exit cue |
| --- | --- | --- | --- |
| 2 | Lobby / Threshold | Walk, watch the first door, learn that a door is the boundary | First door opens after Space/Enter start |
| 3 | Shift / Level 0 | The room beyond the door waits one second, flickers, then rises into light; keep a threshold in view when possible | The next door exposes the office colour temperature |
| 4 | Office / Level 4 | Sparse desks, CRTs, partitions, blackout window and dead vending machine narrow the readable lanes; the threat is only a listening silhouette | Cross the office threshold; sprinting or time in the room wakes it |
| 5 | Run / Level ! | Utility pipes, junction boxes, warning bars and a red service cue turn movement into the decision | Reach the next door while the Relay is closing distance |
| 6 | Exit / Cold threshold | Cyan/metal contrast reads as an apparent exit and briefly releases pressure | Passing the threshold returns to Lobby in the next cycle |

The title uses the same Lobby room pool. Press **Space** or **Enter** to open
the first door; once the camera reaches the next room, **WASD + mouse** takes
control. **Shift** changes to sprint. The room name and threat state are shown
as typography overlays so the player can read the level transition without a
large panel covering the environment.

## Entity contract: The Relay

`The Relay` is an original prototype enemy designed around the game's sound
question. It is a tall, blank-headed, hunched silhouette made from six low-poly
parts in the prototype: capsule body, flattened sphere head, two arms and two
legs. The white head catches a doorway or light pulse without requiring a
high-cost skin shader. It is not a copied Backrooms entity model.

### State and timing

1. **Dormant** — no entity in Lobby or Shift. This keeps the opening readable.
2. **Listening** — when the player enters the first Office sequence (stream
   sequence 4), the Relay appears behind the player, holds for 3.2 seconds,
   and follows a small idle sway. A sprint immediately wakes it.
3. **Chase** — entering Run (sequence 5) always wakes the Relay. Its speed is
   3.72 m/s while the player walks and 4.35 m/s while the player sprints. This
   makes walking unsafe but gives a committed sprint a chance to create space.
4. **Lost** — reaching the player ends the run. The object is disabled before
   the caught state is shown, so the same pooled room can be reused on restart.

The prototype's animation is procedural to stay WebGL-friendly: arm and leg
swings use a gait oscillator while chasing, and the head makes a small off-axis
motion while listening. The production rig target is a 24–36 bone humanoid
rig with root motion disabled and four clips: `Idle_Listen`, `Walk`, `Run`, and
`Stagger`. The state timing above should remain in code so a future FBX can
replace the primitives without changing encounter design.

## Editable implementation

- `Assets/Scripts/FrontRoomsRoomStream.cs` owns the fixed pool, deterministic
  profile sequence, profile materials, office/run/exit props, door threshold,
  light reveal and recycling.
- `Assets/Scripts/FrontRooms3DGame.cs` owns the first-person input, the Relay
  state machine, its procedural motion, Foley footfalls and the minimal HUD.
- The profile arrays are passed from the authored room materials in
  `BuildTitleCorridor`, so changing a material in the serialized editor preview
  changes the streamed profile on the next Play Mode run.
- Recycled rooms are refreshed by rule instead of instantiating new meshes.
  This keeps the first-person WebGL prototype bounded to four room roots.

## Sources

- [The Backrooms Wiki — Level 0 “Threshold”](https://backrooms-wiki.wikidot.com/level-0)
- [The Backrooms Wiki — Level 1 “Habitable Zone”](https://backrooms-wiki.wikidot.com/level-1)
- [The Backrooms Wiki — Level 4 “Abandoned Office”](https://backrooms-wiki.wikidot.com/level-4)
- [The Backrooms Wiki — Entity 8 “Hound”](https://backrooms-wiki.wikidot.com/entity-8)
- [The Backrooms Wiki — collaborative fiction overview](https://backrooms-wiki.wikidot.com/)
- [Associated Press review of the Backrooms film and its 2019 source image](https://apnews.com/article/c7481eab3d0f46436730e88a6ccb9b89)
- [PC Gamer discussion of Backrooms and liminal architecture](https://www.pcgamer.com/movies-tv/backrooms-and-exit-8-make-the-perfect-double-feature-for-videogame-adjacent-horror-movies/)
