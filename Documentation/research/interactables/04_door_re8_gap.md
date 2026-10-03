# 04 — Door gaps: how RE8 builds its doors, and a gap-free door for FrontRooms (R4)

Date: 2026-10-02 (23:00–00:30). Workflow subagent, interactables kit. Status: complete draft.

Scope:
- Red: "in game you can see gaps between the door and its frame, and even see through them into the next room. Research how Resident Evil Village builds its doors and replicate that structure."
- This file is the "R4" that `05_locked_door_type.md` §6 points to. Both door types (free and key) sit on the frame/leaf system defined here.
- Binding rules: `00_map_constraints.md`. Every part below is render-only. The gameplay colliders and names stay exactly as the map builds them.

Evidence:
- In-engine frames come from a private Unity clone (`proj_audit`, synced from the real project at 23:0x). The harness source is `harness/FrontRoomsDoorGapCapture.cs.txt`.
- Logs: `images/door_gap_capture_log.txt`, `images/door_gap_proto_capture_log.txt`, `images/door_gap_shadow_test_log.txt`.
- Code citations are `FrontRoomsMapWorld.cs` as of 23:37 (the map chat is editing it, so line numbers drift).

---

## 0. Summary

1. **Why you can see through the doors.**
   - The visible leaf is the gameplay collider cube: 0.05 × 2.08 × 0.98, hung from a pivot exactly on the jamb line.
   - That leaves a **10 mm slit at each jamb and a 20 mm slit at the head**.
   - Behind the slits there is no stop, rebate or seal: just the bare wall-end faces, 0.20 deep with the trim.
   - Straight rays pass through all three slits from both sides (`door_gap_capture_log.txt`), and the far room shows as a lit line (frames in §1.4).
   - Nothing moves on rebuild. It is purely geometry.
2. **What RE8 does.**
   - Confirmed from pictures I looked at: the door is pushed open by Ethan's hand at the latch stile and swings away from him. The leaf is thick and panelled. It sits in a deep, dark, moulded surround on a threshold board. The perimeter reads as a dark line, never a light one.
   - **Not confirmed:** whether RE8 doors swing away from the player from *both* sides, and whether its frames have true stops. I found no Capcom talk or text source on RE8 door construction; the details are UNVERIFIED (§2.3).
3. **What real doors do.**
   - A single-swing door is gap-free because a **stop** (16 mm in US steel frames) overlaps the 3 mm clearance.
   - A door that swings both ways **has no stop**. It is gap-free in practice because of a radius-cut pivot stile and **brush seals on both stiles**, and it cannot carry a latching lock.
   - FrontRooms' door is geometrically a centre-hung double-acting door (same finding as `01_inventory.md` §1.6 and `02_period_hardware.md` §2.2).
4. **Two fixes, both prototyped in engine (§5, §6).**
   - **Option B** keeps the both-ways swing and needs **nothing from the map chat**. It is a double-acting door: radius hinge stile on the pivot axis, 3 mm gaps, black seal fins on the wall centre plane, a frame "sleeve" that covers the map's trims, and a 12 mm saddle.
     - The see-through lines are gone from both sides in the prototype (§5.4).
     - It swings both ways with no visible clipping at 4°, 14°, 41° and 95°.
   - **Option A** is the RE8-faithful single swing with real 16 mm stops.
     - It works when pushed from the stop side.
     - Pushed from the other side, the leaf passes through the stops. So it needs a fixed swing side, pull handling and Relay changes from the map chat (§6.3).
5. **Two lighting faults make the slits worse. Neither is a slit.**
   - **(a) Thin-leaf shadow leak.** A door-shaped patch of light on the dark side's floor is the shadow leaking through the thin leaf. A 0.14 m shadows-only proxy inside the leaf removes it (tested, §1.5).
   - **(b) Unshadowed lamps.** Two lamps in three cast no shadow and light the next room straight through walls and doors (tested, §1.5). That is audit F5, not a door problem.
6. **Recommendation.**
   - Build **B now**: it fixes Red's complaint with no gameplay change.
   - Offer **A** to Red as the RE8 push/pull grammar.
   - A hybrid for `05`: free doors double-acting (B), key doors single-swing latched with stops (A). It is period-true, because a double-acting door cannot latch, and it adds a long-range difference. Only key doors would need the fixed swing (§7).

---

## 1. What is wrong today

### 1.1 Geometry from the code

All values are hinge-local, as in `01_inventory.md` §1.6:
- X is across the wall (wall faces ±0.08, trim faces ±0.10);
- Z runs along the leaf from the hinge jamb (0) to the latch jamb (1.0);
- Y is up.

| Part | Built at | Size / place | Code |
|---|---|---|---|
| Opening | edge centre, c = 1.5 m | 1.00 wide × 2.10 high; wall pieces stop at Z 0 and Z 1.0 | `FrontRoomsMapWorld.cs:898-903, 911-913` |
| Jamb trims | Z −0.07…0 and 1.0…1.07 | boxes 0.07 face × 0.20 deep (wall 0.16 + 0.02 proud each side), Y 0–2.10, render-only | `:918-926` (`TrimFace` .07, `TrimProud` .02, `FrontRoomsModuleUnits.cs:64`) |
| Head trim | Y 2.10–2.17 | 1.14 × 0.20, render-only | `:927` |
| Hinge (pivot) | Z 0, X 0 (wall centre line) | `Door hinge {a}-{b}` | `:935-938` |
| Leaf | centre (0, 1.04, 0.50) | cube 0.05 × 2.08 × 0.98: spans Z 0.01–0.99, Y 0–2.08. **The renderer is the collider** | `:939-943`; `DoorLeafGap` .02, `FrontRoomsModuleUnits.cs:56` |
| Swing | about Y, 95°, away from the opener, both ways; 0.55 s smoothstep (0.18 s broken) | `SwingAway :1771-1781`, `TickDoors :1822-1844` (`:1838, :1840`) |

- **Measured** (`door_gap_capture_log.txt`): leaf renderer bounds Z 31.010–31.990 and Y 0.000–2.080, with the hinge at Z 31.000 and the latch line at Z 32.000.
  - So the slits are **10 mm (hinge), 10 mm (latch), 20 mm (head), 0 mm (floor)**.
  - The task brief's "whole 2 cm at the latch" is wrong: the leaf is centred, so the 2 cm is split 1 + 1. The map chat's numbers in `00` are right.
- **Reveal z-fight (by construction, not captured).**
  - `MeshBuilder.Box` emits all six faces (`:153-161`). So the wall piece's end face and the jamb trim's inner face are coplanar at Z 0 and Z 1.0, and they fight in depth: wallpaper against trim colour.
  - The same is true at the head soffit (wall piece bottom face against trim bottom face at Y 2.10).

### 1.2 Section through a jamb (plan, today)

```
 room A (−X)                      wall centre                       room B (+X)
                 trim  wall end face (Z=0, |X|≤0.08)  trim
   X = −0.10 ─┐  ┌──────────────────────────────────┐  ┌─ X = +0.10
              │  │            JAMB (solid)           │  │
   Z = 0 ─────┴──┴──────────────────────────────────┴──┴──── reveal plane
                     ·  ·  ·  10 mm slit  ·  ·  ·             ← nothing behind it
   Z = 0.01 ............┌────────────┐.......................
                        │ LEAF 50 mm │  (|X| ≤ 0.025)
                        │  = collider│
```

A ray crossing the wall plane between Z 0 and 0.01 meets nothing at all, from either room.

### 1.3 When the far room shows (computed, then checked)

| Slit | Channel | Straight see-through only within | Visible aperture |
|---|---|---|---|
| Jamb (hinge or latch), any height | 10 mm wide; leaf 50 mm deep inside a 200 mm reveal | ±4.6° of the wall normal in plan (atan 10/125) | 10 − 125·tan φ mm |
| Head | 20 mm; leaf 50 mm under a 200 mm soffit | ≤ 9.1° above horizontal (atan 20/125) | 20 − 125·tan θ mm |

- **Jamb slits.** Standing roughly in line with a jamb, the slit is a full-height, 3–7 px bright line at 1.2 m (1080p, FOV 76°; 14 px per degree).
- **Head slit.**
  - Eye height 1.62 against the head at 2.09 means you must be ≥ 2.9 m away to see through it at all.
  - At 3 m the aperture is 0.4 mm, which is invisible. That is confirmed: frames 03 and 12 show no line at 2.6 and 3 m.
  - From 5–15 m it is computed at about 1–1.4 px: a thin line that will shimmer. Not captured, because the test room was too short.
- **Physics.** The wall colliders are 0.16 deep, so a straight ray passes the jamb slits within ±5.4° and the head within ±10.8°.
  - The Relay's sight ray (eye to eye) could in principle pass a slit when both bodies stand nearly on a jamb line, on opposite sides.
  - Render-only fixes do not change this. Computed only; UNVERIFIED in play (§8).

### 1.4 In-engine frames (`images/`)

Door (276,202)→(277,202): side A is Level 0 Low, side B is Level 0 Standard; seed 516574485. "darknear" means the near room's lamps are at 8% and a shadowed spot is added 1.5 m into the far room (a harness light).

| Image | What it shows |
|---|---|
| `door_gap_00_sideA_front_1.5m_game.jpg`, `door_gap_09_sideB_front_1.5m_game.jpg` | Straight on, game lighting: the jambs read as thin pale lines |
| `door_gap_02_sideA_front_1.5m_darknear.jpg`, `door_gap_11_sideB_front_1.5m_darknear.jpg`, `door_gap_02_crop_hinge_reveal_2x.jpg` | Dark near room: the far-side half of the reveal glows through the slit along the jamb |
| `door_gap_06_sideA_latch_dead_inline_darknear.jpg` + `door_gap_06_crop_latch_slit_2x.jpg` | Eye on the latch jamb line: a full-height lit line into room B |
| `door_gap_16_sideB_hinge_inline_darknear.jpg` + `door_gap_16_crop_hinge_slit_2x.jpg` | Eye on the hinge jamb line from B: the lit line, with the **far room's ceiling troffer** visible through it (white dash) |
| `door_gap_03_crop_head_3m_3x.jpg`, `door_gap_12_crop_head_2.6m_3x.jpg` | Head at 3 m / 2.6 m: no line, as computed |
| `door_gap_19…23_open_*` | Open 95° both ways: the leaf stands nearly square to the wall, its hinge end buried in the jamb |

### 1.5 The two lighting faults (tested)

`door_gap_shadow_leak_sideA.jpg` and `door_gap_shadow_leak_sideB.jpg` show three panels each, on the Option B prototype (no gaps left):
- **Left:** dark near room, shadowed far lamp. A door-shaped patch of light lies on the floor at the threshold.
- **Middle:** the same, plus a **0.14 m-thick shadows-only box** inside the leaf. The patch is gone. So the patch is the far lamp's shadow leaking through the thin leaf (light shadow bias 0.05, normal bias 0.4), not a gap.
- **Right:** the same far lamp with shadows off, as two lamps in three are (`:1124, :1132`). The whole near room lights up through the wall.

So:
- (a) Every door leaf needs a thick shadow caster (§4.5).
- (b) "Light from the next room" through walls is the unshadowed-lamp budget, audit F5, and no door model can fix it. The map also turns shadows on only within `shadowRadius` (`:1201`).

---

## 2. Resident Evil Village: how its doors are built and presented

### 2.1 What I could confirm (sources I actually looked at)

| # | Source | What it shows |
|---|---|---|
| V1 | Official Steam screenshot of the Castle Dimitrescu main hall, viewed full size ([store page](https://store.steampowered.com/app/1196590/); [image](https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1196590/ss_363d9c05ee0a974b766938610a3352e7a89b9c92.1920x1080.jpg)) | A pair of tall leaves, each with a glazed or painted upper panel and a raised lower panel, and visible rails and stiles. Brass levers sit at the meeting stiles. Three decorative hinge plates are on each outer stile. The doors stand in a deep surround: pilasters on both sides, an entablature and overdoor above. The centre seam and perimeter read as **dark** lines. |
| V2 | MKIceAndFire, full-game walkthrough, frames at 1:36:37.5, 1:36:38.9, 1:36:39.6, 1:36:40.4 ([video](https://www.youtube.com/watch?v=nuShOR4IC8w)). The video uses a **third-person camera**, not the default first-person view. | A castle single door. **Shut:** a pale panelled leaf inside a darker moulded architrave, set back in a reveal between fluted pilasters, standing on a darker threshold board. The outline reads as a dark line; no light shows through it. **Opening:** Ethan's hand pushes at the latch stile and the leaf swings **away from him**, into the next room. The leaf's edge shows real thickness, and its face has raised, moulded panels. |
| V3 | Same video, 0:10:45 (prologue, Winters house) | A modern interior doorway with a moulded casing; the leaf is open inward. |
| V4 | Fawcett, "Resident Evil Village and first-person video game immersion", The Conversation ([link](https://theconversation.com/resident-evil-village-and-first-person-video-game-immersion-why-hands-create-intense-connection-161566)) | Ethan's hands are shown in "his interaction with doors, ladders and gates". |
| V5 | RE7, the same engine family: press to unlatch; the door creaks and stays ajar; walk into it to push it open. Read by the audit in the browser pane (`interaction_audit/04_aaa_references.md` S25, Twinfinite). I could not re-open it (HTTP 403). | The "ajar, then push" grammar |
| V6 | Quixel/Capcom interview ([befores & afters mirror](https://beforesandafters.com/2021/09/23/megascans-infests-resident-evil-village/)) | Scanned wood was used "for the outside walls of the houses … floorings and pillars". Nothing on doors. |
| V7 | The Level Design Book, "Doors" ([link](https://book.leveldesignbook.com/process/scripting/doors)) | The common game convention it recommends: rotating doors "double-hinged and open in both directions, outwards / away from the character". Context only; not RE8. |

### 2.2 Principles taken from RE8 (what to replicate; no asset copying)

1. **The leaf is framed by a contrasting, deeper surround**: casing or architrave, reveal, and a threshold board. The perimeter reads as a **dark shadow line**, never a lit line (V1, V2).
2. **The leaf has real thickness and relief.** The edge shows when it opens, and panels catch the light (V2). FrontRooms' 1990 office equivalent is a 44 mm flush veneer or steel leaf with a visible edge band (`02` §2.1).
3. **There is a threshold under the leaf** (V2).
4. **Hardware sits at the latch stile at hand height, and the hand pushes there.** The leaf swings away from the actor (V2, V4), and the door can be left ajar and then pushed (V5).
5. **Nothing behind the gap is open.** Whatever the construction, a gap is backed by solid frame. This is inferred from V1 and V2, where no light line shows. The mechanism (a stop, an overlap or a seal) is UNVERIFIED (§2.3).

### 2.3 What I could not confirm (UNVERIFIED)

- Whether RE8 doors swing away from the player **from both sides**, or have a fixed swing with a pull animation. My memory is that many RE Engine doors swing away from the player from either side; that is not verified by any source here.
- Whether RE8 door frames have true **stops or rebates**, or hide the gap by overlapping geometry. V2 does not resolve it at video resolution.
- How double doors open: one leaf or both, and whether the player pushes both.
- Leaf dimensions in metres.
- **Research limits.**
  - The RE Fandom wiki sits behind a Cloudflare check, which I did not try to pass.
  - The castle-only walkthrough on YouTube is age-gated (sign-in required), and I did not sign in.
  - No CEDEC or RE Engine talk on doors turned up in English or Japanese searches.
  - So RE8's construction is inferred from picture evidence only.

---

## 3. Real-world door construction (comparison)

### 3.1 Single-swing door: the stop does the work

| Fact | Value | Source |
|---|---|---|
| Rebate / stop | The "L-shaped shoulder the leaf comes to rest against". The stop bead is the "short upstand"; rebate width ≈ 12–15 mm for an internal door | [studiomatrx, door frame rebate](https://www.studiomatrx.org/guides/door-frame-rebate-india) |
| US steel frame | Standard 2" face and 5/8" (16 mm) stops | [4specs forum, citing SDI](https://forum.4specs.com/t/hollow-metal-frame-1-inch-face-width/3139); also `02` §2.2 (SDI 111A, read there) |
| Rabbet for a 1-3/4" door | 1-15/16"; the extra 3/16" is for silencers or gasketing so the door still closes flush | [Beacon, frame profiles](https://beaconcdl.com/blogs/news/4-common-hollow-metal-frame-profiles) |
| Terms | Stop: the profile element that receives the door. Soffit: between stop and face. Cased opening: "a frame without a stop and soffit". Astragal: covers the edge clearance at meeting stiles | [SDI glossary](https://steeldoor.org/glossary/) |
| Clearances | Head, jambs and meeting stiles: 1/8" (3.2 mm) ±1/16"; bottom ≤ 3/4" (19 mm) | NFPA 80 (2022) via [idighardware](https://idighardware.com/2022/07/decoded-allowable-clearances-for-fire-door-assemblies/) |
| Threshold | ≤ 1/2" (13 mm), bevelled 1:2 max above 1/4" | [US Access Board, ADA guide ch. 4, §404.2.5](https://www.access-board.gov/ada/guides/chapter-4-entrances-doors-and-gates/); `02` §2.3 has the 1991 ADAAG |

**Why it is gap-free.** The 16 mm stop overlaps the 3 mm clearance. The only path through is L-shaped: through the 3 mm gap, then 90° along the 3 mm silencer gap. No straight line can follow it.

### 3.2 Double-acting door (swings both ways): no stop, so seals and radii

| Fact | Source |
|---|---|
| Hung on a "center-hung pivot system"; double-acting doors "generally cannot carry a traditional latching lockset" (push-pull or no latch); kick plates on **both** faces | [Doorways Plus, double-acting hardware](https://www.doorwaysplus.com/blog/our-blog-1/specifying-double-acting-door-hardware-sets-what-changes-when-the-door-swings-both-ways-453) |
| The pivot edge is radius-cut so the door swings without binding: R9 with a 4 mm gap on a 44 mm door; R15 with 3 mm on fire doors. **Brush strips on both the locking and hinge stiles** "for privacy" | [Royde & Tucker double-action pivot set listing](https://www.independent4life.co.uk/royde-tucker-double-action-pivot-door-set-80kg-centre-pivot-hinge-brushed-stainless-steel) |
| Frame is a cased opening with no stop; doors undersized for operating clearance | `02` §2.2 (Black Mountain H-11.0, read there) |

What this means for FrontRooms:
- The map's door (pivot on the leaf's centre plane, exactly at the jamb, 95° either way) **is** a double-acting door.
- The honest way to make it gap-free while it still swings both ways is the double-acting construction: a radius stile on the pivot, small even gaps, and **seals filling the centre plane**.
- A stop is honest only once the door swings one way.

---

## 4. The common kit: frame sleeve, leaf, saddle, shadow proxy

This is shared by A and B. Hinge-local metres as in §1.1. Which room is +X depends on the edge direction (`01` §1.6 table), so every part is symmetric in X unless stated otherwise. Blender export maps (x, y, z) to Unity (−x, z, −y) (`01` §1.6).

### 4.1 Frame sleeve (static; a sibling under the chunk root at the hinge's closed pose, per `05` §6)

Its job:
- replace the look of the map's jamb and head trims;
- **fully enclose** them, so the map needs no change;
- cover the coplanar reveal faces (the §1.1 z-fight) with a 2 mm skin.

| Part | X | Z | Y | Note |
|---|---|---|---|---|
| Casing, hinge side (each face) | 0.0795…0.105 (and mirrored) | −0.075…0.002 | 0…2.175 | 0.075 face, 0.025 proud of the wall. It encloses the map trim (0.07 face, 0.02 proud, top 2.17) |
| Casing, latch side | same | 0.998…1.075 | 0…2.175 | |
| Casing, head | same | −0.075…1.075 | 2.098…2.175 | |
| Lining, hinge jamb | \|X\| ≤ 0.0795 (B: slot \|X\| < 0.025) | −0.0005…0.002 | 0…2.098 | 2 mm skin over the wall end and trim faces |
| Lining, latch jamb | \|X\| ≤ 0.0795 | 0.998…1.0005 | 0…2.098 | |
| Lining, head | \|X\| ≤ 0.0795 | −0.0005…1.0005 | 2.098…2.1005 | |
| Saddle (threshold) | \|X\| ≤ 0.10 | 0.002…0.998 | 0…0.012 | 12 mm (ADA ≤ 13 mm). Bevel both long edges 1:2 (top flat about 0.152). Metal or vinyl transition strip (`02` §2.3) |

- If the map chat later stops building door trims (an optional one-line change, §8), the casing can drop to the true profile:
  - 0.07 wood casing on the free door (`05` §6.1);
  - 0.051 steel face on the key door (`05` §6.2).
- One slot for the frame (`05` §6 budget). No collider (`kit.no_collider()`).

### 4.2 Leaf (child of `Door hinge {a}-{b}`, next to `Door leaf`; never a child of the scaled cube)

| Item | Value | Why |
|---|---|---|
| Thickness | 0.044 (X ±0.022) | 1-3/4" commercial door (`02` §2.1); within the ≤ 0.05 rule (`00`). The prototype used 0.045. |
| Bottom | Y 0.011 | 1 mm into the 12 mm saddle: the floor line is closed |
| Top | Y 2.095 | 3 mm under the head lining (NFPA 80 1/8") |
| Edges | 1.5 mm × 45° arris chamfers on both faces; a 6 mm hardwood or seam band on the stiles | The chamfer plus the 3 mm gap reads as a dark line (RE8 principle 1); the band shows thickness (principle 2) |
| Jamb edges | per option (§5.1, §6.1) | |
| Gameplay collider | unchanged: the map's `Door leaf` cube | Its renderer is disabled; the model replaces only the renderer (`00`) |

### 4.3 Hardware anchors

- **Lock / handle point:** (±0.055, 1.00, 0.92), the opener's face, = `LockPoint` (`01` §1.6, `FrontRoomsMapWorld.cs:1756`).
- Nothing is more than 0.065 proud.
- The ≤ 0.07 rule is conservative everywhere except within about 0.10 m of the hinge, where the open leaf lies inside the jamb (`01` §1.6 F8, and my frames 19–23).

### 4.4 Gap test (both options)

- The rule: **the wall centre plane (X = 0) must be closed by something solid at every point of the opening's perimeter.**
- A straight sightline from one room to the other must cross X = 0. If every point on the perimeter is covered there (by the leaf, a seal, a stop or the jamb), nothing can be seen through, at any angle, from either side.

### 4.5 Shadow proxy (fixes the floor leak, §1.5)

- A **shadows-only** box, 0.10–0.14 × 2.08 × 0.96, centred (0, 1.05, 0.50), child of the hinge.
- Either a second renderer with `ShadowCastingMode.ShadowsOnly`, or a shadow-only submesh the importer flags.
- Render-only: it never draws, has no collider and adds about 12 triangles.
- When the door is open, its shadow is up to 0.14 wide instead of 0.044. Use 0.10 if that shows.

---

## 5. Option B: gap-free, keeps the both-ways swing (recommended now; no map change)

### 5.1 Construction (a commercial double-acting door)

| Part | Spec | Gap test at X = 0 |
|---|---|---|
| Hinge stile | **Radiused about the pivot axis.** The leaf's hinge edge is a half-cylinder R = 0.022 centred on (X 0, Z 0), so the leaf reaches Z −0.022 inside the jamb. The lining has a slot \|X\| < 0.025 (3 mm each side). A black seal sits in the slot: \|X\| ≤ 0.025, Z 0…0.0015. | Closed: the leaf runs into the solid jamb |
| Latch stile | An **arc about the pivot axis**, r = 0.995. A flat end at Z 0.995 is within 0.25 mm of it, so it can be modelled flat. 3 mm gap to the latch lining (0.998). **Black seal fin** on the centre plane: \|X\| ≤ 0.004, Z 0.994…0.998 (1 mm into the leaf end), Y 0.011…2.098 | Closed by the fin |
| Head | Leaf top 2.095, 3 mm gap. **Head seal fin**: \|X\| ≤ 0.004, Y 2.093…2.098 (2 mm into the leaf top), Z 0…0.998 | Closed by the fin |
| Floor | Leaf bottom 0.011 on the 0.012 saddle | Closed |
| Seals | Black nylon brush or rubber (`Prop_PlasticBlack`), render-only. They are the real "brush strips on both stiles" of §3.2 | — |

### 5.2 Why it does not clip either way (checked)

- **Latch.** Every leaf point stays within r ≤ 0.995 of the axis, so the latch end never enters the latch lining (0.998) or the casing. The fin touches the leaf end by 1 mm only while shut.
- **Hinge.** The hinge stile is round about the axis, so it is identical at every angle: the "radius-cut pivot edge" of §3.2. Its seal ends up inside the leaf as the leaf turns.
- **Head.** The head fin overlaps the leaf top by 2 mm. Once the leaf moves, the fin crosses the leaf only within a few centimetres of the pivot, inside the leaf.
- **At 95°.** The first ~0.10 m from the pivot still lies inside the jamb on the swing side. That is unchanged from today (spec `LEVEL_MODULE_SPEC.md:48`); the casing hides the junction.

### 5.3 Hardware that fits B

- **Honest version:**
  - a push plate on both faces, about 0.10 × 0.40 at Y 0.9–1.3, near the latch (prototype at Z 0.80–0.90);
  - a kick plate on both faces (`02` §5);
  - pivots, which show only as a cap at the head and the floor: "nothing visible but a pivot cap" (`02` §5).
- This matches the title stream doors, which already use bar handles and kick plates on both faces (`FrontRoomsRoomStream.cs:1254-1270`).
- If Red and `05` keep a lever or knob on a both-ways door, that is a game liberty: a real double-acting door "generally cannot carry a traditional latching lockset" (§3.2). The gap fix does not depend on it.

### 5.4 Prototype evidence (render-only prototype in the clone, same door, same views)

| Image | Result |
|---|---|
| `door_gap_proto_cmp_hinge_inline_sideA.jpg`, `…_sideB.jpg` | Panels left to right: today / B / A. The lit line at the hinge jamb (with the far troffer in it) is gone in B and A, from both sides |
| `door_gap_proto_cmp_latch_inline_sideA.jpg`, `…_sideB.jpg` | Same at the latch jamb |
| `door_gap_proto_B_sideA_front_game.jpg`, `…_sideB_front_game.jpg`, `…_B_sideA_front_darknear.jpg` | The closed B door: casing, dark perimeter line, push plate, kick plate, saddle |
| `door_gap_proto_swing_B_pushA_4deg.jpg`, `…_B_pushA_14deg.jpg`, `…_B_pushB_4deg.jpg` | Early swing, pushed from A and from B, seen from both sides at the latch and hinge jambs: no part enters the frame |
| `door_gap_proto_swing_B_95deg.jpg` | 95° both ways, hinge jamb from both sides: clean; no seal or fin clipping visible |

- The prototype frames show the shapes, not final materials: the frame uses the map trim material, and the seals are a black copy of the veneer.
- Full frame list: `images/door_gap_proto_frames.txt`. The prototype log confirms the gameplay collider stays 0.050 × 2.080 × 0.980, untouched; only the cube's renderer is switched off.

### 5.5 Cost

- No map change, no gameplay change, and the sound chat's names are unaffected.
- **Frame:** about 14 boxes, about 170 triangles, 1–2 slots (frame, seal).
- **Leaf:** slab plus half-cylinder plus plates, about 150–250 triangles, 2–3 slots.
- No lights, no LOD1 needed.

---

## 6. Option A: RE8-faithful single swing with stops (needs the map chat)

### 6.1 Construction

| Part | Spec |
|---|---|
| Swing | One fixed side per door, S. Stops are on the other face, P (the push side) |
| Stops | On the P face at the hinge jamb, latch jamb and head. **16 mm projection** (SDI 5/8") from the lining: Z 0.002…0.018 / 0.982…0.998; head Y 2.082…2.098. 35 mm wide: X from −(0.022 + 0.003) to −0.0605 when S = +X. 3 mm silencer gap to the leaf's P face |
| Leaf | 0.044, centred on the pivot (A1). Flat, square stiles at Z 0.005…0.995 (3 mm to each lining), Y 0.011…2.095 |
| Gap test | Closed by the stops, which overlap the 3 mm gaps by 13 mm. The path is L-shaped (§3.1) |
| Hardware | Lever or knob both faces, ≤ 0.065 proud (`02` §3–4). Strike on the latch jamb. A closer is allowed (`02` §5.3) |
| Hinges | **A1 (pivot stays on the centre line):** no honest butt-hinge knuckles. A knuckle has to sit on the axis, and here the axis is inside the leaf, so knuckles would orbit and bury themselves. Use plain hinge leaves or pivot caps. **A2 (map moves the pivot, §6.3 item 5):** three 4-1/2" butts with knuckles on the S face at `02`'s heights. This is the RE8 "hinge read" (V1). |

### 6.2 Prototype evidence

| Image | Result |
|---|---|
| `door_gap_proto_cmp_*` (right-hand panel) | No see-through, from both sides |
| `door_gap_proto_A_sideA_front_game.jpg`, `…_sideB_front_game.jpg` | The closed A door with its lever |
| `door_gap_proto_swing_A_pushA_4deg.jpg`, `…_A_pushA_14_95.jpg` | Pushed from the stop side: clean, through to 95° |
| `door_gap_proto_swing_A_wrong_14deg.jpg`, `…_A_95_right_vs_wrong.jpg` | **Pushed from the wrong side** (today's rule): the leaf passes through the stops |

How bad the wrong-side clip is:
- At the latch it lasts the first ~5° (about 2 frames).
- The head stop cuts the top of the leaf near the hinge for most of the swing, by geometry.
- At 1–1.5 m it is subtle in the frames, but it is physically wrong. **A is not acceptable with the both-ways rule.**

### 6.3 What the map must change (the map chat's own estimate: about an evening plus the takeover, `00`)

1. **A fixed swing side per door.**
   - Suggestion: the leaf **opens into the Standard-height room**. Doors exist only on Low ↔ Standard borders (`LEVEL_MODULE_SPEC.md:48`), so this is deterministic, needs no hash, and puts the 1.0 m sweep in the bigger room.
   - Or use the map chat's edge hash.
2. **Pulls.**
   - From the swing side the leaf comes toward the player across a 1.0 m radius. The keep-clear strip is already 1.2 m (`FrontRoomsModuleUnits.cs:71`).
   - Handle the player standing in the sweep with a short takeover: step back about 0.45 m in ≤ 0.35 s, spherecast-clamped. If the space behind is blocked, open to about 60°.
   - Add a `DoorPulled` event for the visual and sound chats.
   - RE8's own pull animation is UNVERIFIED (§2.3).
3. **The Relay.**
   - From the stop side it bursts the leaf into the far room, and the stop or strike splinters.
   - From the pull side it rips the leaf toward itself.
   - Nav is unchanged (`00`).
4. **Shots.**
   - The key shot (audit §3.2) ends with the door popping ajar. From the pull side that is toward the camera, so the pose must back off by the ajar angle (10° moves the latch edge 0.17 m).
   - The audit §3.3 push stays as it is for the push side.
5. **(A2, optional) Move the pivot to the S face.** This gives true butt hinges and removes the leaf's burial in the jamb at 95°:
   - hinge local position += X_S × 0.028 (6 mm proud of the leaf face);
   - the leaf collider's local centre −= X_S × 0.028, so **the collider does not move when shut**;
   - `LockPoint` is unaffected: it is computed from the opening centre (`:1756`).
6. Tests and docs (`LEVEL_MODULE_SPEC.md:48` swing text, keep-clear notes).

Gameplay consequences for Red:
- Pulling is slower than pushing, so fleeing through a door from its swing side costs time. That is a new tension beat, but it can feel unfair during a chase. Mitigations: the takeover, or a push-only rule.
- Doors gain a readable front and back, since hinges and stops show on one face only.

---

## 7. Recommendation

1. **Build Option B now** (§4 + §5 + the §4.5 shadow proxy).
   - It removes every see-through slit from both sides at all angles, swings both ways cleanly, and changes no gameplay.
   - It also gives the RE8 read: dark perimeter, deep frame, threshold, a thick leaf with edge band.
2. **Put Option A to Red** as the RE8 push/pull grammar, with §6.3's costs.
   - The frame sleeve, saddle, leaf slab and shadow proxy are shared.
   - Only the stile profiles, the seals-versus-stops choice and the hinges differ, so switching later is cheap.
3. **Hybrid, for `05_locked_door_type.md` to weigh:**
   - **free doors double-acting (B):** push plates, pivots, seals, no latch;
   - **key doors single-swing (A):** stops, visible hinges, a latching lockset and keyway.
   - It is period-true, because a double-acting door "generally cannot carry a traditional latching lockset" (§3.2).
   - It gives a hardware difference readable at 3–6 m: plate against knob or lever, and hinge knuckles on one face. That adds to `05`'s colour read.
   - Only key doors would need §6.3's fixed swing and pull handling. Unlocking already has its own camera shot, so the pull can live inside that shot.
4. **Lighting.**
   - The shadow proxy is part of the door kit.
   - Light through walls from unshadowed lamps stays with the visual and map chats (audit F5). Until it is addressed, a lit room next door will still glow through walls, even with perfect doors.

---

## 8. Asks to the other chats

- **Visual chat (kit).**
  - Build `interact_door_frame_*` (sleeve, saddle, and B's seals or A's stops) and `interact_door_leaf_*` (B: radius hinge stile; A: flat stiles), following §4–§6. Final names belong to the kit spec.
  - Add the shadow proxy (§4.5).
  - Anchors: `lock_px`/`lock_nx` at (±0.055, 1.00, 0.92), as in `05` §7.
- **Map chat.**
  - B needs nothing.
  - Optional for B: stop building door trims once the kit frame is placed (`:918-927` for doors only). That removes hidden overdraw and the coplanar reveal faces.
  - For A: §6.3.
  - Note: the Relay can in principle see through the 10 mm collider slits within ±5.4° of a jamb line (§1.3). Render-only fixes cannot close that; the map decides whether it matters.
- **Sound chat.**
  - B has no latch, so `Handle`/`Unlatch` on a free door are not honest; a push-plate thump would be.
  - A adds a pull event.

## 9. Open items and UNVERIFIED

- RE8 both-sides behaviour, stops versus overlap, double-door behaviour, pull animation (§2.3).
- The head slit's 1–1.4 px line at 5–15 m is computed, not captured.
- The Relay seeing through collider slits is computed, not observed.
- The prototype is boxes plus a cylinder in the clone. Final meshes, materials and the seal look are not yet built or captured.
- The hinge-location layout ("5-10-equal") is `02`'s. I could not open Allegion's page (HTTP 403).

## 10. Sources and method

- **Code:** `FrontRoomsMapWorld.cs` (lines as of 23:37), `FrontRoomsModuleUnits.cs`, `FrontRoomsRoomStream.cs`, `LEVEL_MODULE_SPEC.md`.
- **In-engine:** three batch runs in the private clone, all on the same door (the run's seed is deterministic):
  - before;
  - before / B / A with swings;
  - the shadow test.
- **Web, read:**
  - The Level Design Book (doors);
  - The Conversation (Fawcett);
  - befores & afters / Quixel (RE Village);
  - Doorways Plus (double-acting hardware);
  - Royde & Tucker listing (independent4life);
  - studiomatrx (rebate);
  - 4specs forum (SDI 2"/5/8");
  - Beacon (rabbets);
  - SDI glossary;
  - idighardware (NFPA 80 clearances);
  - US Access Board ADA guide ch. 4.
- **Viewed in the browser pane:** the Steam store screenshots (V1) and YouTube frames (V2, V3).
- **Not reachable:**
  - the RE Fandom wiki (Cloudflare check, not attempted);
  - an age-gated castle walkthrough (sign-in, not attempted);
  - Twinfinite and unbox.ph RE7 previews (403);
  - Allegion KB (403);
  - the Quixel blog (redirected; the page carried no article text).
