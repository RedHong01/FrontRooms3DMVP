# Door Foley segments: wooden doors, open and close

FrontRooms doors are passive wooden doors, not electric ones. This document breaks each door sound into its segments. For each segment it says what makes the sound, when it plays, how loud it is, what recording we already have, and what is still missing.

Scope:
- **Title double door.** Two flush solid-core leaves, about 1.12 x 2.2 m, with pull bars and no lever. They swing 0 to 88 degrees in 0.9 s on a smoothstep curve. One door per run swings shut on the reverse curve and is then locked.
- **Map single door.** A 1 m leaf with a lever, swung 95 degrees in 0.55 s on a smoothstep curve. The player opens it with E. Some doors are locked and need a key.

Units:
- **Levels** are in dB relative to the map door's normal-tier close compound heard at 1 m (0 dB). These are working estimates from Foley practice, not measurements.
- **Times** are in ms from motion start, the first frame the leaf moves.
- **"1–4 m"** means audible at that distance in a quiet carpeted office with about 35 dBA of background noise.

---

## 1. Answer first

| Sound | Segments | Latch or catch click on close? | Why |
|---|---|---|---|
| Title double door, open | **3:** release, swing bed, next-room reveal. Nothing at 88°. | n/a | The curve ends at zero speed and nothing touches the leaf, so the open has no end hit. |
| Title door, close and lock | **4 beats:** swing bed, seat, silence, lock. Three of them make sound. | **No latch click at the seat.** The only metal sound is the deadbolt, heard through the door 0.4–0.8 s later. | The doors have pull bars and no lever, so there is no spring latch. Keeping the seat soft and the lock metal makes the lock the story beat. |
| Map door, open | **3:** handle (press, latch pull-back and spring return in one asset), breakaway, swing bed. Nothing at 95°. Locked door: 1 compound. Unlock: 1 key compound, then breakaway and swing bed. | n/a | The lever has to pull the latch in before the leaf can move, so the handle leads. |
| Map door, close | **2 at runtime:** swing bed and close compound. The compound holds **4 parts you can hear:** strike-lip scrape, stop thud, latch click, backlash knock. | **Yes, a spring-latch click, and it is the defining "shut" cue.** It is only physically valid if the door is single-acting (see the decision below). | The scrape followed by the click is what makes a door sound shut rather than just bumped. |

**Hinges are not a separate segment.**
- A 1990 office door hangs on ball-bearing hinges, which are nearly silent.
- The hinge sound lives inside the swing bed as faint grain and stick-slip ticks.
- Stick-slip only happens at low speed. So the ticks belong in the slow first and last part of each swing, not at peak speed.
- The long creak is the haunted-house cliché. At most, use one short, dry groan on about 1 run in 5.

**Decided by Red (2026-10-02): single-acting (Option A).** It is the same choice as the visual chat's door option A. The map chat implements a fixed swing side per door, real stops, and a 0.1 s lever-to-swing delay. Background:
- Today `SwingAway` (FrontRoomsMapWorld.cs:1655) swings the leaf away from the player from either side, which makes it a double-acting door.
- A bevelled spring latch and a stop bead only work from one side.
- **Option A, single-acting (recommended).** Keep the lever, the latch click and the stop thud. The door always opens to the same side.
- **Option B, double-acting.** Drop the lever click. The close becomes a soft roller-catch "brr-tk" with no stop thud.

---

## 2. Segment tables

### Curve facts behind the timings

| | Title door (88°, 0.9 s, 1.12 m leaf) | Map door (95°, 0.55 s, ~0.96 m leaf) |
|---|---|---|
| Peak speed | 147 °/s, leaf edge 2.9 m/s, at 450 ms | 259 °/s, leaf edge 4.3 m/s, at 275 ms |
| Slow zones (under 60% of peak speed; hinge ticks go here) | 0–165 ms and 735–900 ms | 0–100 ms and 450–550 ms |
| Open passes 25° | 317 ms (gap at the edge 0.49 m) | 185 ms |
| Close passes 25° / 10° / 5° | 583 / 711 / 770 ms | 365 / 439 / 474 ms |
| Close passes 0.5° from shut (trigger point) | 860 ms, edge 10 mm from shut, 0.48 m/s | 527 ms, edge 8 mm from shut, 0.71 m/s |
| Contact with the silencers (0.25° from shut, ~5 mm) | ~872 ms, 0.35 m/s | ~534 ms, 0.50 m/s |

A smoothstep close does **not** reach the frame at zero speed. Near the end, speed falls only with the square root of the angle that is left. The leaf meets the silencers at about hand-guided speed, so a soft seat and a latch click are both physically real. Trigger the hit at the 0.5° crossing. At 60 fps the sound then lands in the next 0–17 ms, which is right at contact.

### 2.1 Title double door, open (3 segments)

| # | Segment | What makes the sound | When (ms) | Length | Level | 1–4 m |
|---|---|---|---|---|---|---|
| T-O1 | Release | Both leaves pull off the rubber silencers at the meeting stiles, giving one soft "thup/tk". If there is a catch, it lets go at the same instant, so it is not a separate sound. | 0 (0–10 ms pre-roll is fine) | 40–120 ms | −20 | **Keep.** At 4 m this is the "nobody touched it" cue, so mix it slightly forward. |
| T-O2 | Swing bed, one per leaf at the hinge | The leaf body moving air: a low swish under 300 Hz that peaks at 450 ms. Faint ball-bearing grain and stick-slip ticks in the slow zones, 0–165 and 735–900 ms. Ends in silence. | 0–900 | 0.9 s, cut to the curve | body −24 at peak, grain −32; rare creak −20 | **Keep** at 1–2 m. At 4 m it is mostly inaudible, which is correct. |
| T-O3 | Next-room reveal (a mix parameter, not a sample) | As the gap opens, the next room's tone loses its muffle. `Aperture` breakpoints: 0°→0, 5°→0.25, 10°→0.45, 25°→0.8, 45°→0.97, 88°→1 (about 1−(1−θ/88)^4.8). | 0–450; 80% by 317 ms | – | Next-room tone low-pass goes from about 600 Hz to fully open (8 kHz and up), +4–6 dB | **Keep.** This is the biggest audible change at 4 m. |
| – | End stop at 88° | Nothing. The leaf stops at zero speed and touches nothing. | – | – | – | **Skip.** Leave it silent. |
| opt | Worn-hinge knuckle tick | Play in a worn pin takes up when the acceleration reverses. | 450 | 10–20 ms | −30 | Optional, on at most 1 run in 8. |

### 2.2 Title door, close and lock (4 beats)

| # | Segment | What makes the sound | When (ms) | Length | Level | 1–4 m |
|---|---|---|---|---|---|---|
| T-C1 | Closing swing bed, one per leaf | Same layers as T-O2, cut from **closing** recordings (never reversed audio). Ticks sit in 0–165 and 735–872. | 0–872 | ~0.87 s | body −24, grain −32 | **Keep** at 1–2 m. |
| T-C2 | Next-room muffle (parameter) | `Aperture` goes 1→0 on the same breakpoints. It crosses 0.8 at 583 ms, 0.45 at 711 and 0.25 at 770, and reaches 0 at contact. | 583–872 | – | the reverse of T-O3 | **Keep.** It is the main "shut" cue at 3–4 m. |
| T-C3 | Seat | Both solid-core leaves meet the rubber silencers at 0.35 m/s, giving a muffled, dense "thup" (body at 100–400 Hz, little above 2 kHz). Add a short frame ring only if the frame is hollow metal. **No latch click.** Leaf B lands 5–20 ms after leaf A, never before it. | Trigger at the 0.5° crossing (860); lands 860–877 | 80–200 ms (5–15 ms hit plus ring) | −6 (soft tier, two leaves) | **Keep.** The loudest moment of the close. |
| T-C4 | Silence | Nothing plays. This pause carries the scare. | seat + 0 to seat + 400–800 | 0.4–0.8 s, randomized | – | **Keep.** This silence is designed. |
| T-C5 | Lock from the far side | Thumb-turn detent and ratchet (150–250 ms) plus the deadbolt throwing with a "chunk", as one 200–350 ms compound. Optionally one leaf knock as the bolt seats. Heard **through** the leaf: low-passed at 1.5–2.5 kHz, mostly the thunk. Emitter at the meeting stiles, on the far side. | seat + 400–800 (about 1270–1670) | 200–350 ms | −10 | **Keep.** This is the story beat. It must stay audible at 4 m, so raise its level before you raise its brightness. |

### 2.3 Map door, open (3 segments, assuming Option A)

The E press is at −100 ms. The code should delay the leaf 80–120 ms after E. If it does not, put the handle at the head of the asset and accept that it overlaps the start of the swing.

| # | Segment | What makes the sound | When (ms) | Length | Level | 1–4 m |
|---|---|---|---|---|---|---|
| M-O1 | Handle | The lever is pressed, the return spring winds, the latch tongue pulls in and the lever hits its stop. Then the hand lets go and the spring snaps the lever back. The return is baked into the tail, 150–300 ms after the press. | −100 | 250–400 ms | press −15, return −18 | **Keep.** Audible to about 3 m. |
| M-O2 | Breakaway | The tongue clears the strike and the leaf leaves the silencers: a dry tick or "thup". | 0–20 | 20–60 ms | −20 | **Keep.** Audible at 1–2 m. The player is at about 1 m. |
| M-O3 | Swing bed | With an edge speed of 4.3 m/s right next to the player, the whoosh is real: low and short, peaking at 275 ms. The leaf body adds weight. Bearing grain sits in 0–100 and 450–550. A creak is rare. Ends silent at 95°. | 0–550 | 0.55 s | whoosh −22 at peak, grain −32 | **Keep.** |
| – | Open stop at 95° | Nothing. The leaf arrives at zero speed. | – | – | – | **Skip.** |

| Variant | Segment | What makes the sound | When | Length | Level | 1–4 m |
|---|---|---|---|---|---|---|
| Locked | M-L1 Locked rattle | The lever hits its limit, then the leaf knocks in the latch/bolt clearance. One compound, played at most once per 0.5 s. | at E | 0.3–1.0 s | −12 | Keep |
| Unlock | M-U1 Key compound | Key goes in (pin ratchet), then turns, and the turn pulls the latch back. No "key out": it happens mid-swing and cannot be heard. Then M-O2 and M-O3 play, with no handle. | at key use; the leaf follows 0.5–0.7 s later | 400–700 ms | −14 | Keep |

### 2.4 Map door, close (2 runtime segments)

| # | Segment | What makes the sound | When (ms) | Length | Level | 1–4 m |
|---|---|---|---|---|---|---|
| M-C1 | Closing swing bed | The whoosh peaks at 275 ms. Grain sits in 0–100 and 450–527. Cut from closing recordings. | 0–527 | ~0.53 s | whoosh −22, grain −32 | **Keep.** |
| M-C2 | Close compound | One baked asset holding, in order: the strike-lip scrape (10–30 ms before the thud), the stop/silencer thud (loudest), the latch click 0–15 ms later (3–8 kHz) and a backlash knock 20–80 ms later. Add frame ring if the frame is hollow metal. | Trigger at the 0.5° crossing (527); lands 527–544. Contact speed is 0.5–0.7 m/s. | 120–300 ms | 0 (normal tier) | **Keep.** Audible beyond 4 m. |
| M-C3 | Hand catch (only when E reverses a moving door) | A palm stops the leaf with a dull thud on the face. This is not a hinge tick. | at the reversal | 40–100 ms | −18 | Keep |

Close-compound tiers (4–6 variants each). The tier is chosen from the speed read at the 0.5° crossing.

| Tier | When it is used | Level / pitch | Contents |
|---|---|---|---|
| Soft | Slower close, if the curve is ever changed | −6 dB, darker | Thud and latch click. The scrape is barely there. |
| Normal | Every smoothstep close today (0.5–0.7 m/s) | 0 dB | All four parts |
| Slam | Only if the close curve arrives with speed, or a Relay hit drives the door | +4 dB, +3 semitones (BeamNG-style tiering) | All four parts, plus a settle rattle of 0.6–1.2 s |

---

## 3. Assets per segment

### Recordings we draw from

| ID | Source | Use |
|---|---|---|
| 843829 | thaighaudio, heavy wooden fire door in a hall, CC0 | Main source. About 85% of it is unused. |
| 768656 | Nox_Sound, wooden door with a metal handle, locked, CC0 | Handle source |
| 341176 | klangfabrik, steel stairwell door, CC0 | Wrong material. Sweetener only. |
| BigSoundBank 3205 | `door-creak.wav` | The cliché creak. Do not use it. |

Processing for every 843829 cut:
- High-pass at about 150 Hz for swings and at about 80 Hz for hits.
- De-noise with the room-tone print from 4.5–8.1, 15.6–17.7 or 21.3–23.6 s.
- **Do not use the 560 Hz notch** from the THAIG chain. That band is the leaf/hinge groan itself.

### 3.1 Title open

| Seg | Have (library) | Cut from an unused part of a source | Still missing: record or search |
|---|---|---|---|
| T-O1 Release | `door_latch_soft_01` = 843829 @ 19.50. This is the take-B leaf pulling off the frame, **mislabelled as a latch**. Relabel it after a listen. | 843829 @ 18.92–19.10 (clicks at 18.925 and 18.995, +30/+40 dB over the floor): 1–2 more | **Gap: 6 takes needed** for shuffle. Record a solid-core door pulled off its rubber silencers with the latch taped back, so there is no metal. Use a close mic at 0.5 m and a second mic at 2–3 m. Search: "door open no latch", "door pull open seal", "door unstick". |
| T-O2 Swing bed, grain | Nothing usable. | 843829 take-A open 1.95–3.60 (groan plus 6 ticks: 2.475, 2.88, 2.92, 3.06, 3.46, 3.555) and take-B open 19.60–21.05 (groan plus 7 ticks, 20.05–20.805). Those swings last about 1.5 s. Shorten them to 0.9 s by tightening the gaps between ticks. Do not time-stretch the ticks. Put the ticks in the slow zones. | – |
| T-O2 Swing bed, air and leaf body | Only the synthetic `door_closer_loop`. | None in our recordings. | **Gap.** Record a solid-core door, or a 2 m plywood panel, swung past a mic at 0.5–1 m with no hardware noise: 6 takes at about 0.9 s and 6 at about 0.55 s (the latter for the map door). Search: "door whoosh", "door swing air", "panel swish", with the CC0 filter. |
| Rare creak | `door_swing_creak_loop` (3205): **remove** | A 150–400 ms dry, low groan from 843829 9.20–10.40 or 24.85–25.80 | – |
| T-O3 Reveal | – | – | No asset. It uses the next room's existing tone event plus the `Aperture` parameter. |

### 3.2 Title close and lock

| Seg | Have (library) | Cut from an unused part of a source | Still missing: record or search |
|---|---|---|---|
| T-C1 Swing bed | Nothing. | 843829 take-A close 9.20–10.40 has 12 ticks about 75 ms apart: **the best hinge texture we own.** Also use 10.85–12.78 (sparse ticks for the slow end zone) and take-B close 24.85–25.80 (8 ticks). **Avoid 26.5–28.2:** it carries a 2.65 kHz closer whistle, and no closer is modelled. | Air/body layer: same gap as T-O2. |
| T-C3 Seat | `door_stop_soft_01/02` = 843829 @ 12.82 and 28.30, the first soft contact before each slam. These are the closest match. About 95% of their energy is below 300 Hz, partly room rumble. High-pass and de-noise them, then listen to confirm there is no metal latch in them. **Drop `door_stop_soft_03`** (from the cliché creak file). | Tail detail: 843829 13.05–13.40 (event at 13.29) and 28.70–28.85 (ticks at 28.72 and 28.795) | **Gap: need at least 4 more.** Record a solid-core door pushed shut by hand onto rubber silencers at about 0.3–0.4 m/s, with the latch taped back so there is no click: 8 takes. Record a pair if you can find one. Search: "door close soft", "door gently closed", "door close no latch". |
| T-C5 Lock | **Nothing.** The only key sound is 616835, a key-ring jingle. The Nox rattle is a handle against a bolt, not the bolt moving. | – | **Gap.** Record a deadbolt thrown by thumb-turn on the far side of a closed solid door, with one mic 1–2 m away on the near side and one close mic to blend: 6 takes of the throw, plus 6 of the retract for later. Search: "deadbolt", "thumb turn lock", "door bolt lock", with the CC0 filter. Choose dry recordings. |

### 3.3 Map door, open

| Seg | Have (library) | Cut from an unused part of a source | Still missing: record or search |
|---|---|---|---|
| M-O1 Handle | `door_handle_press`, 8 takes from 768656 (Nox). Clean and close, but these are **locked-door** takes: the leaf clunks on the bolt at about +0.18 s. Trim each one before 0.17 s. `door_unlatch_bolt`, 5 takes from 843829 take A, all cut from one gesture, so they are thin variety. | 843829 take B **18.15–18.33 press plus 18.38–18.55 release** gives one full press-and-return compound, the strongest handle in the file. Optional pre-touch from 17.75–18.10. Spring returns from Nox release-only cuts: 0.33–0.60, 1.90–2.16, 3.51–3.75, 4.69–5.00, 6.14–6.42, 7.32–7.66, 8.78–9.25 and 10.37–10.70 s. Each has a snap followed by a leaf knock 0–30 ms later; high-pass it to isolate the snap. Build 6 compounds of trimmed Nox press, a 150–300 ms gap and a Nox return. | Nice to have: an **unlocked** lever on a solid-core door, press, hold and release, 8 takes, so the press does not sound locked. |
| M-O2 Breakaway | Same pool as T-O1. | Same as T-O1 | Same as T-O1. For this door, also record the tongue clearing the strike. |
| M-O3 Swing bed | – | Grain: same 843829 cuts as T-O2, tightened to 0.55 s | Whoosh: same gap as T-O2 (the 0.55 s takes). |
| M-L1 Locked | `door_locked_rattle`, 8 Nox takes: **keep.** | – | – |
| M-U1 Unlock | **Nothing.** | – | **Gap.** Record a key going into a cylinder (pin ratchet) and turning to pull the latch back, as one take: 4–6 takes. Search: "key unlock door", "key insert turn lock". Jingle 616835 can sit in front as a pocket layer. It is not part of the door. |

### 3.4 Map door, close

| Seg | Have (library) | Cut from an unused part of a source | Still missing: record or search |
|---|---|---|---|
| M-C1 Swing bed | – | Same 843829 closing cuts as T-C1 | Whoosh: same gap |
| M-C2 Slam tier | `door_latch_slam_01/02` = 843829 @ 13.44 and 28.93. Real, and they include the tongue hitting the strike lip 40 ms before the impact. **Drop `_03`** (341176, a steel door). | Settle rattle: **843829 14.20–15.45**, 10 hits about 0.12 s apart decaying from −40 to −58 dB, almost all unused | Slam takes 3–4 for shuffle. Search: "wooden door slam latch". |
| M-C2 Normal tier | `door_latch_norm` is a muffled slam: its body is 11–15 dB over the click and it is very dull. **Replace it.** | – | **Gap: the most important recording to get.** A hand close of a lever-latch solid-core door at 0.5–0.8 m/s, so the tongue rides the strike lip and clicks in: 6 takes, with a close mic and a mic at 2–3 m. Search: "door close latch click", "interior door close". |
| M-C2 Soft tier | `door_latch_soft` is mislabelled. Remove it from LatchStrike. | – | **Gap.** The same session at 0.3–0.4 m/s: 4 takes. |
| M-C3 Hand catch | Nothing. | – | **Gap.** Record a palm stopping a moving solid door: 4 takes. Search: "hand stops door", "palm on door". |

### 3.5 Placeholders and misused assets that must go

| Asset or path | Problem | Action |
|---|---|---|
| `door_auto_operator` (2 files, synthetic motor), fired by `FrontRoomsSoundDirector.cs:215` | It is an electric door. Red rejected it. | Remove the event and its calls. |
| `door_closer_loop` (synthetic hiss) | No closer is modelled, and a healthy closer is silent. | Remove. |
| `door_air_whump` (2 files, synthetic) | Level 0 is open plan, so closing builds no pressure. | Remove. |
| `door_swing_creak_loop` (BigSoundBank 3205); `FrontRooms3DGame.cs:1028` also loads `door-creak` | The horror cliché | Remove from the bed. Rare creaks come from 843829. |
| 5 synthetic files in `FMOD_Placeholders/Door` that the SPEC in `fmod_frontrooms.py` still points to, plus 38 superseded synthetic door files | Placeholders | Repoint the SPEC to recorded files and delete the placeholders. |
| Legacy AudioSource clips in `FrontRoomsRoomStream.BeginDoorOpening` (lines 1760–1762: latch at 0.42, creak at 0.78, travel at 0.42) | Doubles the FMOD path and breaks AUDIO_CONTRACT (FMOD events only) | Remove. |
| StopLimit firing at 88° with Impact ≈ 0.02, which plays `stop_soft` on the open | An impact where none exists | Do not fire a stop when the leaf eases to rest. |
| `door_stopmid_settle` | These are handle clicks; _02 and _03 duplicate `unlatch_bolt` | Remove. Replace with M-C3. |
| `door_stop_med`, `door_stop_hard` | Closing slams used for an open stop our doors never hit | Remove from the door events. Relay blows can keep their own copies. |
| One-slam reuse: 843829 13.44 and 28.93 feed 12 of the 49 one-shots | The same transient is recognisable across events | Keep them for the slam tier and Relay hits only. |

---

## 4. Realism rules

### Avoid

- **Electric sounds.** No motor whine, solenoid clunk, pneumatic hiss, beeps or closer hiss. A door that moves by itself and makes only passive sounds is creepier.
- **The long horror creak.** Ball-bearing hinges are almost silent. Allow at most one 150–400 ms dry, low groan, on about 1 run in 5, placed in a slow zone (start or end of the swing).
- **Hinge ticks at peak speed.** Stick-slip dies out at high speed. Put the ticks in the slow zones and let the air and leaf body carry the middle.
- **Identical doubled leaves.** Never use the same sample on both leaves. Give each leaf its own shuffled pick and its own pitch roll. Delay leaf B, and never play it early:
  - **Hits:** 5–20 ms, so they read as one thicker hit. A 30–80 ms gap reads as a double hit the eye does not see.
  - **Swing beds:** 15–40 ms.
- **An impact when the leaf eases to rest.** There is no sound at 88° or 95° on the open.
- **Reversed audio for a close.** Closing swings come from closing recordings.
- **A slam on every close.** The title close is soft, and the map door's normal tier is a hand close.
- **Baked hall reverb.** Keep assets dry and add the space in game. Cut 843829 tails before the hall builds up.
- **Clutter nobody hears at 1–4 m.** No air whump. The carpet sweep is off: commercial doors are undercut and a correct sweep does not touch the floor. Use it only as a rare "wrongness" variant. No flush bolts or coordinator: the leaves move in sync.
- **Separate runtime events for parts that happen within 150 ms.** Scrape, thud, click and knock are layered when editing and baked into one asset.

### Randomization (FMOD)

| Segment | Variants | Pitch | Volume | Other |
|---|---|---|---|---|
| Release | 6 | ±40 cents | ±1.5 dB | Leaf flam 0–20 ms |
| Swing bed (per direction) | 6 | ±60 cents | ±2 dB | Leaf B +15–40 ms; creak layer about 20% of the time |
| Seat | 6 | ±40 cents | ±1.5 dB | Leaf B +5–20 ms |
| Lock | 4–6 | ±30 cents | ±1 dB | Delay after the seat 400–800 ms |
| Handle | 6 | ±50 cents | ±1.5 dB | – |
| Close compound | 3 tiers x 4–6 | ±40 cents | ±1.5 dB | Tier from contact speed; slam is +4 dB, +3 semitones |
| Locked rattle | 8 | ±50 cents | ±1.5 dB | At most once per 0.5 s |
| Unlock | 4–6 | ±30 cents | ±1 dB | – |

FMOD notes:
- **Shuffle** only avoids repeats when a playlist has 3 or more entries and no play percentages. Every pool above has at least 4.
- **Cooldown** applies to the whole event. If both leaves share one event with a cooldown, leaf B is silently dropped. Use one instance per leaf, or no cooldown.
- **Swings are pre-edited one-shots, not velocity loops.** Both curves are fixed, so the edit can follow them exactly. An Amnesia-style loop would spend half the 0.55 s swing fading in and out.

### Emitters, distance, occlusion

- **Title door.** Release, seat and lock sit at the meeting stiles in the centre. The lock is on the far side and occluded. Each swing bed sits at its own hinge.
- **Map door.** Handle, breakaway and close compound sit at the latch edge: 1.0 m high, 0.08 m in from the latch jamb. The swing bed sits at the hinge.
- **Distance.** Spatialize in FMOD and low-pass small transients more as distance grows. Swing beds should drop out by about 3 m, which is correct. Mix as if heard from 2–3 m, not from a close mic.
- **Doorway.** Treat it as a portal: the `Aperture` curve in 2.1 on the open, the same curve in reverse on the close.

### Timing fixes the sound needs from code (for the sound session to raise; not edited here)

- Trigger the seat or close compound at the **0.5° crossing**, and read the contact speed there. `EndMotion` today uses the last speed above 2 °/s, which is about 0, and it fires about 80 ms after contact.
- Map door: delay the leaf 80–120 ms after E, so the handle comes before the swing.
- Set `UnlockSwingDelay` to 0.5–0.7 s. It is 0 today, so the key turn plays over the swing.
- Red's decision on single-acting versus double-acting (section 1).

---

## 5. Sources

Recordings (Freesound, CC0):
- 843829 thaighaudio, heavy wooden fire door: https://freesound.org/s/843829/
- 768656 Nox_Sound, wooden door with metal handle, locked: https://freesound.org/s/768656/
- 341176 klangfabrik, stairwell door: https://freesound.org/s/341176/
- 160213 qubodup, wooden door kick/break: https://freesound.org/s/160213/
- 616835, key ring: https://freesound.org/s/616835/

Door mechanics:
- Hinge squeak as stick-slip (Purdue): https://www.purdue.edu/newsroom/archive/releases/2016/Q2/pesky-squeaks-and-squeals-caused-by-3-types-of-stick-slip-behavior.html
- Ball-bearing vs plain-bearing hinges: https://www.doorwaysplus.com/blog/our-blog-1/plain-bearing-vs-ball-bearing-hinges-on-standard-commercial-doors-when-the-cheaper-option-creates-the-bigger-problem-394 and https://www.hunker.com/13403332/ball-bearing-vs-standard-hinge/
- Door silencers and bump stops: https://www.doorwaysplus.com/blog/our-blog-1/door-silencer-adhesive-vs-press-fit-choosing-the-right-bump-stop-for-the-frame-you-have-498
- A sweep should not touch the floor: https://www.beaconcdl.com/door-sweeps-vs-auto-door-bottoms-whats-the-difference/
- Closer control zones (no hiss; latch speed can be set faster or slower): https://www.beaconcdl.com/4-control-zones-of-door-closers/ and https://doorhub.com/blog/how-to-adjust-your-commercial-door-closer
- Hollow metal frames amplify latch and deadbolt impact noise: https://patents.google.com/patent/US10724286
- Lever return spring mechanism: https://patents.google.com/patent/US5718468
- Four latch impact events; a faster close is louder (car-door study): https://doi.org/10.1177/1077546320932009
- Roller latches: https://www.iveshardware.com/en/products/latches-catches-and-bolts/roller-latches.html
- Flush bolts and coordinators (why they do not fit here): https://idighardware.com/2015/04/flush-bolts-and-coordinators/

Game audio practice:
- Amnesia hinge loop and limit sounds: https://github.com/FrictionalGames/AmnesiaTheDarkDescent/blob/master/HPL2/core/sources/physics/PhysicsJoint.cpp
- Amnesia door events (`CloseOff` on grab, `CloseOn`, lock): https://github.com/FrictionalGames/AmnesiaTheDarkDescent/blob/master/amnesia/src/game/LuxProp_SwingDoor.cpp
- Source `prop_door_rotating` move/open/close slots: https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/props.cpp
- BeamNG latch tiers and variants: https://beamng.com/game/news/blog/latch-audio-system
- Physics door sounds in Unreal: https://forums.unrealengine.com/t/how-do-i-give-a-physically-opened-door-opening-and-closing-sounds/453319
- Farnell, Designing Sound (procedural door creak): https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/8375/designing_sound.zip/practical09.html
- RE7 dry door recording: https://blog.native-instruments.com/engineering-the-sound-of-fear/
- Uncharted 4, sound through the next rooms: https://www.dualshockers.com/uncharted-4-is-currently-being-tested-by-about-40-people-dev-talks-sound-effects-that-feel-right/
- Wwise repetition avoidance: https://www.audiokinetic.com/qa/8949/how-can-i-avoid-repetition-from-different-containers
- Audio/video sync tolerance (late audio is tolerated more than early): https://en.wikipedia.org/wiki/Audio-to-video_synchronization
- Comb filtering: https://en.wikipedia.org/wiki/Comb_filter
- FMOD Studio 2.03 manual (Instrument, Modulator, Parameters references), bundled with FMOD Studio

Checked but not relied on, because they do not support the claims first attributed to them:
- https://italdoors.com/home-design-blog/solid-core-vs-hollow-core-interior-doors-privacy-sound-and-durability-compared/ covers sound privacy (STC), not door tone.
- https://asoundeffect.com/sound-library/daily-doors is a store page with no mixing advice.
- https://postaudiotips.beehiiv.com/p/doors-are-a-pain is about matching reverb to the space, not about handle, latch and hinge layering.
- https://morphic.com/resources/sounds/creaking-door-sound-effects is vendor copy. It is cited only as an example of the cliché.
- https://www.hometips.com/repair-fix/how-to-stop-a-door-from-rattling.html could not be checked (TLS error).
