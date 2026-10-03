# Sound coverage audit (2026-10-02)

What each game moment plays now, with FMOD running. The review IDs (A01…D07) are the clips on the Slides review page (P1 deck `NmYGRYKlhfX6H4rbJ7QcSN`, slide 22) and in `Research/week02/assets/sound-review/`. When FMOD is off, the old Unity audio (D01–D07) plays instead.

Status key:
- **Recorded** / **Reshaped**: a real recording; reshaped means it is pitched or layered.
- **Synth**: an FMOD placeholder.
- **Partial**: part of the moment has sound and part is missing.
- **Silent**: nothing plays.
- **No gameplay**: the moment doesn't exist in the game yet.

## Player

| Moment | Trigger | Sound now | Status |
|---|---|---|---|
| Walk, run, stop on carpet / office tiles | distance travelled (`FrontRoomsPlayerFootsteps`) | carpet steps + damp layers by zone and shoe wetness (A01–A06) | Recorded |
| Running cloth | run strides | jacket swish (A07) | Recorded |
| Metal threshold strip | `Surface.Metal` | C01 is in the banks, but the map has no metal surface, so it never plays | Unused |
| Climb through a broken window | `PlayerClimbed` | cloth swish only. No hands on the sill, no glass crunch underfoot | Partial |
| Out of stamina | stamina rule mirrored in the footstep component | breath (C10, flagged) | Synth |
| Relay close but unseen | proximity | heartbeat (C11, flagged) | Synth |
| Caught | `Caught` | all buses cut, then tinnitus (C12). No grab or impact | Partial |

## Keys and doors

| Moment | Trigger | Sound now | Status |
|---|---|---|---|
| Pick up a key | `KeyTaken` | key ring (A08); the old audio had nothing | Recorded |
| Try a locked door | `DoorLocked` | handle rattles on the bolt (A10) | Recorded, but doors only lock when a level profile sets `doorsNeedKeys` (default off) |
| **Unlock a door with a key** | none: there is no unlock event | ordinary door Foley only. No key in the lock, no bolt turn | **Silent**, waiting on the `DoorUnlocked` hook (map chat) |
| Open / close a manual door | hinge rotation (`FrontRoomsDoorSound`) | handle, latch, stops, slow-swing creak (A09, A11–A13); closer hiss and fast-close air (C02, C03) | Recorded + Synth |
| Title-stream double doors | hinge rotation (Stream mode) | recorded wooden swing per leaf, release, soft seat + lock on the terminal door (DOOR_FOLEY_SEGMENTS.md); motor and creak removed 2026-10-02 | Recorded (deadbolt still a stand-in) |
| Relay squeezing through a door frame | `FrontRoomsRelayRig.DoorSqueeze` (a value, no event) | nothing | **Silent**, waiting on a rig event (visual chat) |

## Windows

| Moment | Trigger | Sound now | Status |
|---|---|---|---|
| Hold E on a window | `GlassHold` | stress tone (C05, flagged) + cracks at 35 % and 70 % (A14) | Synth + Recorded |
| Let go early | `GlassHoldReleased` | stress tone stops | ok |
| Window breaks | `GlassBroken` | shatter (A15). The old audio reused the door-break clip | Recorded |

## The Relay

| Moment | Trigger | Sound now | Status |
|---|---|---|---|
| Its steps | `FrontRoomsRelayRig.Step` (on the foot plant) | walk / run / drag, wet variant (B01–B03, B07; B01, B03, B07 flagged) | Reshaped |
| It wakes | first state out of Dormant | clicks (C08) | Synth |
| Near you | distance + wall occlusion | presence drone (C07) | Synth |
| Hunt / search / chase / lost | `StateChanged` | stingers (C09, flagged) | Synth |
| Hits and breaks a door | `DoorBlow`, `DoorBroken` | slams pitched down, wood splitting, break (B04–B06) | Reshaped. Blow strength is guessed (count / 5) until `BlowIndex` / `BlowCount` land |
| The giant brushing the ceiling | none | nothing | **Silent**, planned rig event `CeilingBrush` |

## The world

| Moment | Trigger | Sound now | Status |
|---|---|---|---|
| Room hum | always on, Tension global | tube hum with tension beating (A16) | Recorded |
| Air / room tone per zone | Zone global | hall air vs tall-room air (A19) | Recorded |
| Nearest lamp | lamp discovery | fixture hum (A17), 4 voices started 0.53 s apart, −28 dB (was 6 in-phase voices, louder than footsteps) | Recorded |
| Lamp flicker | lamp intensity | starter strike and ballast ticks (A18, flagged) | Recorded |
| A tube failing | none | pop (C06) is in the banks, but nothing triggers it | Unused |

## Game flow

| Moment | Trigger | Sound now | Status |
|---|---|---|---|
| Title screen | none | only the room hum. `Music/Title` exists, but the motif (M1/M2/M3) isn't chosen and nothing starts it | **Silent** (music) |
| Pause | none: there is no pause event | everything keeps playing under the PAUSED screen | **Missing** duck, waiting on the `Paused(bool)` hook (map chat) |
| Menus, display settings, restart | none | nothing | **Silent** (no UI sounds) |
| Escape / win | none: there are no exits yet | the old audio has an unused synth "escape" clip | **No gameplay** |

## What to decide

1. **Review page:** mark the clips you don't want. 19 of 45 are flagged yellow as possibly funny, and 13 of those 19 are synth or old Unity audio. Recording replacements removes most of them.
2. **Motif:** pick M1, M2 or M3. That unlocks title music and the stingers (C09).
3. **Moments with no sound:**
   - Unlock and pause are each blocked on a one-line hook from the map chat.
   - Ceiling brush and door squeeze are blocked on rig events from the visual chat.
   - The window climb, the caught grab, UI and the tube pop are sound-side work I can add next.
