# 20 — G10 in-engine verification: glass and zone reflections, BEFORE vs AFTER

Status: DONE (2026-10-03, about 10:30). Two capture runs on the private clone `proj_glass`: run 1 at 00:23 and run 2 at
10:04. Run 2 is the one reported here. Nothing in `Frontrooms3D` changed except this folder (`images/g10_*`,
`logs/g10_*`, `g10_harness/`). The real project was not opened in Unity.

---

## 0. Short answer

1. **The veil is gone.** The far room now shows its true colour and contrast through the pane, instead of the
   cyan-grey haze. BEFORE changes the view behind the pane by **26–41 /255** on average. AFTER changes it by
   **2.4–3.5 /255**. The noise floor (the same frame rendered twice) is 0.4–1.2 /255. This fixes the audit's F3.
2. **In the game, the AFTER pane does not read as glass at 1.5 m, at 50° or at 61°, in Level 0 or in Office.** It
   reads as an empty opening, which is the failure the audit warned about (audit 05 frames 08, 09 and 11). Three
   things show that a pane is there:
   - the grime over the dark jamb reveal along the side edges,
   - a faint dust strip above the sill at 0.7 m,
   - small bright specks and short streaks across the pane at 1:1.

   At 1.5 m the specks look like marks on the floor behind the glass, not marks on the glass.
3. **The zone cube makes almost no visible difference on glass.** The glass-only reflection floor
   (`_ReflectionMin` 0.6) adds about +1 /255. Pushing it to the full captured light (1.0) adds only +2–4 /255 in
   total. In these evenly lit rooms a dielectric reflects about 4 % face-on, and the reflected room is about as
   bright as the room behind the pane. Cube reflections cannot make this pane visible. The only term that lifts it
   above the noise is the grime scatter (`_Scatter` 3, worth about +4 /255).
4. **On walls and floors the zone cube makes no measurable change** at intensity 0.5 (0.214 linear). In frames 01,
   34, 35 and 37, BEFORE → AFTER-glass is 0.4–1.2 /255, the same as the noise floor. That makes the frozen-print
   caveat moot at this level, but it also means the cube buys nothing visible here yet.
5. **`ApplyAmbient()` is the biggest visible change, and it is not glass.** It doubles the ambient probe (SH0 red
   0.064 → 0.127) and brightens every frame by about 6–7 /255 on average, mostly the shadows and ceilings. The map
   chat will call it at run start. **Red should sign it off on its own.**
6. **Props:**

   | Prop | AFTER result |
   |---|---|
   | Water-cooler bottle | Still reads as a blue bottle, slightly clearer. |
   | Vending front | Clearer and darker, but shows no reflection at 53°. |
   | Hutch and display cabinet (staged) | **Now read as solid dark doors.** The hutch's arched glass panes and the cabinet's glass shelves disappear. |
   | Desk glassware (staged stand-ins) | Almost vanishes at 1.25 m. |

   BEFORE was physically wrong (milky plastic), but it read as glass. AFTER is closer to physics but reads as
   *nothing* for case goods and small glassware.
7. **It is not ready for sign-off as "AAA glass".** It is a correct transmission base. What is missing is the set of
   cues that make real interior glass visible: a glazing stop and edge, sharp lamp reflections at an angle, and
   soft directional smears that catch the lamps. §9 ranks what the fix pass should try. The Metal RT track (G14)
   helps only some of those (§10).

---

## 1. Method

- **Harness:** `g10_harness/FrontRoomsGlassG10Capture.cs.txt`, a copy of the clone's
  `Assets/Editor/Audit/FrontRoomsGlassG10Capture.cs`. It is built from the audit harness
  (`../interaction_audit/harness/FrontRoomsInteractionAudit.cs.txt`; method in `../interaction_audit/05_in_engine_evidence.md` §1):
  - same scene `Assets/Scenes/FrontRooms3D.unity`, seed `Random.InitState(4242)` before Space, giving run seed
    516574485 and map root (-576, 0, -576), as in the audit;
  - same title handoff;
  - same game camera: 1920x1080 sRGB target, 4x MSAA, post on;
  - same target search.

  The camera positions for 01, 04, 23, 34, 35 and 37 match the audit's `frames.txt` to the centimetre.
- **States per view.** Each view is one frozen moment (`Time.timeScale` 0, `FrontRoomsGlassG10Capture.cs:543`), so
  lamp flicker is the same in every state.
  - **A BEFORE.** What the game draws today:
    - the map's runtime `TransparentGlass` 30 mm cube with shadows on. Main still builds this at
      `FrontRoomsMapWorld.cs:2070-2087` (read 10:20) with `GlassThickness = .03f` (`FrontRoomsModuleUnits.cs:61`);
    - the scene's ambient;
    - Unity's default sky cube at 0.3;
    - copies of the shipped URP/Lit `Prop_Glass` and `Prop_BottleBlue` (`Assets/Editor/Audit/G10/G10Before_*.mat`).
  - **B AFTER-glass.** Every built pane gets `Glass_Window`, is thinned to 6 mm and has shadows turned off
    (`:307-335`; the map contract). The zone cube is set through `FrontRoomsZoneReflection.SetImmediate` (`:356-367`).
    The props get the new materials. The scene's ambient is left alone.
  - **C AFTER.** B plus `FrontRoomsLook.ApplyAmbient()`. This is what the game will draw once the map chat makes
    both calls.
  - **N no pane.** Window views only: the pane is hidden, with C's lighting. It is the reference for "is the pane
    visible".
- **`FrontRoomsMapWorld.cs` was not edited.** Panes are swapped at runtime by the harness and swapped back. The
  restore check renders A again at the end of every view. It differs from the first A by 0.4–1.2 /255 on average
  (max 4–11). That is the noise floor. Film grain is the likely cause (UNVERIFIED).
- **Zone rule (harness only; the map chat may choose differently):**
  - DeadLamp if the camera cell's own lamp is mode 3 or disabled;
  - else Office for the Office theme;
  - else Tall for Tall height;
  - else Level0.

  Code: `:382`.
- **Metrics.** Inside the pane's screen quad (inset 6 %), each state is compared with N:
  - mean luminance change ΔY (Rec.709 on sRGB bytes, /255);
  - mean |ΔRGB|;
  - "contrast kept" = σ(with pane) / σ(no pane).

  Full numbers: `logs/g10_metrics.txt`. Per-view camera, cell, zone and lamp state: `logs/g10_frames.txt`. Run log:
  `logs/g10_log.txt`.
- **Run 2 additions over run 1:**
  - **Diagnostics** (`:515`). Four single-knob variants of `Glass_Window` on a temporary material copy, plus a
    ×6 difference image.
  - **A real dead-lamp window** (`:987`). Run 1's dead-lamp frame was a duplicate of 37.
  - **Better prop framing** (`:1124`). The camera aims at the glass sub-mesh.
  - **Two STAGED set-ups** (`:1172`, `:1214`), because the built map near the start has no glass on any desk and no
    hutch or cabinet:
    - glass on a real `Kit_OfficeDesk`;
    - a `Kit_Hutch` and a `Kit_DisplayCabinet`.
- **What the AFTER pane still lacks.** The map-chat geometry from audit §4.1: the glazing stop (18 × 12 mm) and the
  stool trim. AFTER therefore has no frame cue at the pane edge. A stop would add one (UNVERIFIED until the map
  chat builds it).

## 2. Images (all JPEG q85, in `images/`)

| File | What |
|---|---|
| [g10_01_representative.jpg](images/g10_01_representative.jpg) | Audit frames 01, 34, 35, 37: BEFORE \| AFTER-glass (scene ambient) \| AFTER |
| [g10_02_window_L0.jpg](images/g10_02_window_L0.jpg) | Level 0 window (282,206): 1.5 m, ~50° (**audit 04**), 0.7 m, 61°: BEFORE \| AFTER \| no pane |
| [g10_03_window_Office.jpg](images/g10_03_window_Office.jpg) | Office window (281,206): 1.5 m, ~50° (**audit 23**), 0.7 m, 61° |
| [g10_04_window_crops_1to1.jpg](images/g10_04_window_crops_1to1.jpg) | 1:1 pixel crops at the pane centre, both zones, 1.5 m and 0.7 m |
| [g10_05_diagnostics_L0.jpg](images/g10_05_diagnostics_L0.jpg) | Level 0 1.5 m / 0.7 m / 50°: no pane, AFTER, ×6 difference, `_ReflectionMin` 1.0, `_ReflectionMin` 0, `_Scatter` 0, grime off, BEFORE |
| [g10_05b_diagnostics_Office_deadlamp.jpg](images/g10_05b_diagnostics_Office_deadlamp.jpg) | The same for Office 1.5 m and the two dead-lamp windows |
| [g10_06_deadlamp_windows.jpg](images/g10_06_deadlamp_windows.jpg) | Window (304,207)↔(305,207) seen from under a dead lamp (38) and from the lit side (39) |
| [g10_07_props.jpg](images/g10_07_props.jpg) | Water-cooler bottle; vending front at 22° and 53°; STAGED desk glass; STAGED hutch + display cabinet |
| `g10_full_*` | Full-resolution A / C (and N for two views) of 01, 04, 23, 34, 35, 37, 38, the Level 0 window at 1.5 m and 0.7 m, the Office window at 1.5 m, the desk and the hutch |

The ×6 difference images and every variant are in the clone at `proj_glass/Verification/glass_g10/` (`*_D_diff_x6.jpg`,
`*_V??.jpg`).

---

## 3. Windows: what reads as glass and what does not

### 3.1 Numbers (pane quad vs the same view with no pane; noise floor 0.4–1.2)

| View | BEFORE mean\|ΔRGB\| / ΔY / contrast kept | AFTER mean\|ΔRGB\| / ΔY / contrast kept |
|---|---|---|
| Level 0, 1.5 m | 35.8 / +34.1 / 0.71 | 3.4 / +2.7 / 0.88 |
| Level 0, ~50° (audit 04) | 29.0 / +25.1 / 0.86 | 2.4 / +1.0 / 0.92 |
| Level 0, 0.7 m | 41.3 / +40.0 / 0.75 | 3.2 / +2.8 / 0.89 |
| Level 0, 61° | 27.3 / +24.0 / 1.24 | 2.7 / +1.3 / 0.95 |
| Office, 1.5 m | 34.1 / +32.7 / 0.76 | 2.9 / +2.0 / 0.86 |
| Office, ~50° (audit 23) | 29.0 / +28.0 / 0.78 | 3.1 / +1.4 / 0.88 |
| Office, 0.7 m | 33.4 / +32.8 / 0.56 | 3.5 / +2.4 / 0.88 |
| Office, 61° | 30.3 / +29.4 / 1.01 | 3.5 / +2.0 / 0.92 |
| Under a dead lamp, 1.5 m (38) | 10.4 / +4.7 / 0.69 | 2.7 / −0.6 / 0.91 |
| Under a dead lamp, ~50° (38) | 9.8 / +3.7 / 0.83 | 2.8 / −1.5 / 0.94 |
| Lit side, dead lamp beyond, 1.5 m (39) | 29.7 / +27.0 / 0.46 | 2.7 / +1.8 / 0.89 |

### 3.2 What reads

- **The view through the pane is now correct.** Level 0 behind an Office window is yellow, not cyan
  ([g10_03](images/g10_03_window_Office.jpg)). The far troffers and the far wall keep their contrast. In frame 23
  the far-wall windows show the pale Office room behind them, the same as with no pane. The audit's flat
  "sky in a windowless office" rectangles are gone.
- **Grime over a dark background.** Along the side edges the pane overlaps the dark jamb reveal. There the dust and
  prints show as a mottled light band ([g10_05](images/g10_05_diagnostics_L0.jpg), the ×6 difference: the brightest
  part of the pane is its border). This is the strongest "there is glass" cue in every view.
- **At 0.7 m, at 1:1** ([g10_04](images/g10_04_window_crops_1to1.jpg)): small bright specks and short horizontal
  smear streaks, most visible in the Office crop. A faint lighter dust strip sits above the sill.
- **A lamp glint at the head of the frame at ~50°.** It is visible in BEFORE as well, so it is not new.

### 3.3 What does not read

- **Face-on, 1.5 m, both zones:** the pane is invisible except for the edge band. A player would try to walk through
  it.
- **The specks read as marks on the floor behind the pane.** They are small, bright, high-frequency and evenly
  spread, so at 1.5 m and beyond they sit "on" whatever is behind them. Real smudges read because they are soft,
  directional (wipe arcs, hand height) and catch a lamp's specular. These catch ambient only.
- **No reflection of anything is visible** at any angle: not the near wall, not the troffer behind the camera, not
  the player's side. That holds in Level 0, in Office and under the dead lamp.
- **50° and 61° are no better than face-on** (ΔY +1.0 to +2.0). The Fresnel rise (alpha .08 + .55·F⁵) reflects a
  cube that is as bright as the room behind, so it cancels out.
- **No edge or thickness cue.** The 6 mm green edge faces (`_AutoEdge`) are about 2–3 px at these distances (my
  estimate: 1 px ≈ 2.2 mm at 1.5 m with a 76° FOV) and are lost against the dark frame. Without the glazing stop the pane has no outline.

## 4. Which knob does what (diagnostics, state C, ΔY vs no pane)

| View | AFTER | `_ReflectionMin` 0 | `_Scatter` 0 | grime off | `_ReflectionMin` 1.0 |
|---|---|---|---|---|---|
| Level 0, 1.5 m | +2.7 | +1.4 | −1.3 | −1.5 | +4.1 |
| Level 0, ~50° | +1.0 | +0.0 | −2.5 | −2.4 | +1.9 |
| Level 0, 0.7 m | +2.8 | +1.6 | −1.3 | −1.7 | +4.0 |
| Level 0, 61° | +1.3 | −0.1 | −1.8 | −1.9 | +2.7 |
| Office, 1.5 m | +2.0 | +0.5 | −2.1 | −2.1 | +3.4 |
| Office, ~50° | +1.4 | +0.1 | −2.4 | −2.3 | +2.8 |
| Office, 0.7 m | +2.4 | +1.0 | −1.9 | −1.9 | +3.8 |
| Office, 61° | +2.0 | +0.3 | −1.5 | −1.6 | +3.7 |
| Dead lamp, 1.5 m | −0.6 | −1.6 | −3.8 | −2.9 | +0.4 |
| Lit side, 1.5 m | +1.8 | +0.7 | −2.1 | −2.1 | +3.0 |

How to read it:

- **The reflection floor is worth about +1 /255.** Going from 0.6 to 1.0 linear adds about +1.3 more. The
  arithmetic agrees. Face-on, F0 is 0.04, so the pane reflects about 0.04 × 0.6 ≈ 2.4 % of the cube and transmits
  about 92 % of the room behind. When both rooms are equally bright, the sum lands within a few percent of the
  no-pane image (my inference; the measurements match it).
- **`_Scatter` 3 is the largest term, about +3.5 to +4.5.** With scatter off, the grime maps only darken: "scatter
  off" and "grime off" give nearly the same mean. So everything the grime maps show today comes through the
  scatter term.
- **Clear glass on its own (grime off)** darkens the view by about 2 /255 and keeps 93–96 % of the contrast:
  transparent and invisible.

## 5. The rest of the frame: zone cube and `ApplyAmbient`

Whole-frame mean /255 (noise floor in brackets):

| Frame | BEFORE → AFTER-glass (zone cube on every surface) | AFTER-glass → AFTER (`ApplyAmbient` only) |
|---|---|---|
| 01 Level 0 | 1.18 (1.09) | 6.74 |
| 34 Office | 0.44 (0.39) | 5.97 |
| 35 Office cubicles | 0.44 (0.37) | 6.85 |
| 37 dead lamp | 1.01 (0.99) | 6.92 |

- **Zone cube.** At 0.5 on the slider (0.214 linear), the cube's effect on walls, floors, carpet and the cubicle kit
  is below the noise in all four frames. These frames contain almost no glossy metal and no VCT, so audit §4.3's
  "high gain on VCT and metal" is still UNVERIFIED, not disproved.
- **`ApplyAmbient`.** It replaces the scene's trilight (sky .20/.19/.15, equator .26/.24/.17, ground .40/.36/.24)
  with `FrontRoomsLook`'s (.22/.21/.17, .34/.31/.22, .62/.56/.40) and rebuilds the probe, so SH0 red goes from
  0.064 to 0.127 (`logs/g10_log.txt`). The ceilings, the shadow sides of the columns and the floor under the
  cubicles lift visibly ([g10_01](images/g10_01_representative.jpg), column 3 vs 2). It is a deliberate fix from
  the audit (F4), but it changes the mood of every room. **Red should approve it separately from the glass.**

## 6. Dead lamp

- **Audit frame 37** has no glass in view. The DeadLamp cube changes nothing measurable there (1.01 vs a noise of
  0.99).
- **A window seen from under a dead lamp (38).** The harness searched 80 window edges and found
  (304,207)→(305,207); the camera stands in a Level 0 Tall cell whose own lamp is mode 3.
  - BEFORE was already weak there: +4.7 ΔY, with a blue cast, +17 on the blue channel.
  - AFTER darkens slightly (−0.6) and is invisible.
- **The zone rule is wrong for this cell.** The camera's own lamp is dead, but the Tall hall is lit by its other
  lamps, so a "dead lamp" cube here reflects a darker room than the one the player stands in. It is invisible today,
  so it does not matter yet. If intensity goes up, drive DeadLamp from the local light level, not from one cell's
  lamp. This matters for the map chat's rule.
- **The "lit side, dark beyond" case (39)** is the one where glass should act most like a mirror. It could not be
  shown. The far cell's lamp is dead, but its Tall hall is lit by neighbours, so the far side is not dark (mean Y
  106). No truly dark room behind a window was found near the start at seed 4242.

## 7. Props

Whole-frame BEFORE → AFTER-glass: bottle 0.64, vending front 2.47, vending at 53° 1.81, desk 0.59, hutch 2.17 /255.

- **Water-cooler bottle (`Prop_BottleBlue`, real placement).** It reads as a blue bottle before and after. AFTER is a
  touch clearer, with a slightly crisper rim line. Fine.
- **Vending front (`Prop_Glass`, real placement).** AFTER is clearer and darker, and the products are more
  saturated. It still reads as a glass front, mainly because of the frame and the lit strip behind the glass. No
  room or lamp reflection is visible at 53°.
- **STAGED desk glass (`41`).** Two cylinder stand-ins on the map's one built `Kit_OfficeDesk`: a tumbler with
  `Prop_Glass` and a bottle with `Prop_BottleBlue`. They are not kit assets; no kit asset puts glass on a desk.
  - BEFORE: milky plastic cylinders.
  - AFTER: nearly invisible. A faint outline remains, plus a blue tint and cap on the bottle.
  - A real drinking glass reads from its rim highlight, its thick base and refraction. A closed thin cylinder at
    F0 .04 has none of these. That is a modelling problem as much as a material one.
  - Staging flaw: the tumbler intersects a paper stack.
  - The `Kit_DeskPhone` I added carries no visible glass. The census of glass-material renderers in the built map
    lists only `Kit_VendingMachine` ×10, `Kit_WaterCooler` ×10 and `Kit_WallClock` ×2, and the generator's own
    desk phone is not among them. So the "DeskPhone" in `41`'s note adds nothing to the test.
- **STAGED `Kit_Hutch` + `Kit_DisplayCabinet` (`42`), free-standing.** The camera stood in the neighbouring Office
  cell, so the Office grade applies.
  - **This is a readability regression.** BEFORE showed the hutch's two arched glass panes and the cabinet's glass
    shelves as light shapes.
  - AFTER, the hutch's upper doors read as solid dark wood and the arches vanish. The cabinet reads as a closed
    wooden cabinet: its glass shelves are almost gone and the side glass is faint.
  - Clear glass over a dark interior looks like the interior. With no reflection strong enough and no scatter
    (props use `_Scatter` 0, `Prop_Glass.mat:132`), nothing marks the glass. The implementation report flagged the
    hutch (`10_implementation.md` §5). This confirms it in the game.

## 8. Other checks

- **Shadows.** The AFTER pane casts none: the harness sets the renderer to Off as the map contract asks, and the
  shader has no ShadowCaster pass.
- **Transparent sorting.** In frame 23 the near pane overlaps the far-wall panes. No sorting artefacts are visible.
  Only one or two panes were ever in view, so this is not a stress test.
- **Cost.** Render plus GPU sync, median of 30, editor, Metal:

  | View | BEFORE | AFTER |
  |---|---|---|
  | 01 | 42.9 ms | 44.5 ms |
  | Level 0 window, 1.5 m | 54.6 ms | 49.8 ms |
  | Level 0 window, 0.7 m | 52.2 ms | 47.1 ms |

  **Not usable.** Three other Unity processes were running: a WebGL build of another session, a perf test on
  `proj_rs`, and Red's editor on `Frontrooms3D` with its import workers. The audit measured 13.9 ms (05 §G). All I can say is that there is no difference outside the noise. Re-measure on a quiet machine.
- **Not tested:** a built player, WebGL (no browser run), the title-stream rooms (they have no cubes yet), the
  crossfade in motion (only the plain swap is captured; the play-mode test in `10_implementation.md` §6.3 covers the
  fade), hold and crack stages, and Glass_Shard.

## 9. What the fix pass should try (ranked; recommendations from these measurements, not tested)

1. **Do not tune the reflection numbers to make the pane visible.** The full captured light (`_ReflectionMin` 1.0)
   adds +2–4 /255. Keep the zone cube for correctness and leave `_ReflectionMin` where it is, or lower it.
2. **Get the edge cue from the map chat (audit §4.1): the glazing stop on both faces, four sides, 18 × 12 mm.** A stop gives
   the pane an outline. Today the only visible part of the AFTER pane is its border band over the reveal. Map-chat
   work, small.
3. **Change the grime from specks to smears.**
   - Use fewer and larger, low-frequency wipe arcs and hand-height smears, with soft edges. Keep the fine specks
     for 0.7 m and closer only.
   - Let the smudge roughness (.96 → .62) catch the **troffer specular**, not only ambient. My hypothesis (UNVERIFIED; check it against
     `../interaction_audit/02_glass_and_breakables.md`'s references): a smudge that lights up when it lines up with a
     lamp is the cue that sells glass.

   Today the scatter term adds ambient SH from both sides (`FrontRoomsGlass.shader:379-380`), which is uniform, so
   the grime reads as a flat speckle.
4. **Prop glass needs its own answer:**
   - Case goods (hutch, cabinet, vending): a light dust scatter (`_Scatter` > 0 on `Prop_Glass`), a slightly higher
     `_AlphaFresnel`, or both. Then re-check the hutch arches and the cabinet's glass shelves.
   - Small glassware: geometry (rim, thick base). The material alone will not carry it.
5. **Lamp reflections at an angle** are the one reflection cue strong enough to see: a troffer lens is far brighter
   than the room. The cube holds the lenses, but a 256 px cube seen in a 1.4 m pane at 50° gives a soft, low-detail
   glint. Two ways to make it sharp:
   - the audit's step 2: one time-sliced realtime probe at the window being held, desktop only;
   - the RT track (§10).
6. **Approve or re-tune `ApplyAmbient` separately** (§5). It changes every frame more than the glass does.

## 10. What this means for the Metal ray-traced glass track (G14)

- Red had ChatGPT build a separate hardware RT path. Its files are in main, not in this clone:
  - `NativePlugin/FrontRoomsMetalGlassRT.mm` → `Assets/Plugins/macOS/libFrontRoomsMetalGlassRT.dylib`;
  - `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs` and `FrontRoomsMetalGlassRTRendererFeature.cs`;
  - in main's `FrontRoomsMapWorld.cs`: `FrontRoomsMetalGlassRTController.Ensure()` at `:347` and
    `pane.AddComponent<FrontRoomsMetalGlassTarget>()` at `:1049` (read 10:20).
- What it does: the controller registers renderers within 18 m (`registrationRadius`, up to 256 instances). The
  plugin traces the camera ray to the first glass hit, reflects it once through the nearby scene, and writes RGBA
  where the first hit is marked glass. URP composites that after post (class summary in `FrontRoomsMetalGlassRT.cs`).
  The task row is `VISUAL_CHAT_TASKS.md` G14.
- **None of the G10 frames include it.** The clone predates it.
- **What the measurements here predict for it (inference).**
  - The G1 hook contract feeds RT radiance through the same Fresnel and grime (`_FR_GlassRTReflection` /
    `_FR_GlassRTWeight`). A perfect reflection of these evenly lit rooms still adds only about +2–4 /255 face-on,
    the same as the full-cube test in §4.
  - RT will **not** make face-on panes visible.
  - RT can win where a cube cannot:
    - sharp lamp-lens reflections at 40–70°;
    - things that move or that the cube does not hold: the Relay, the player's light, opened doors;
    - a dark room behind a lit window.
  - So G14's acceptance frames should be oblique and dark-beyond views, not these face-on ones. No truly dark room
    behind a window exists near the start at seed 4242 (§6), so G14 needs a staged one.
- **Two notes for the RT track:**
  - It composites after post. That is why G1 asked for the hook before transparents, so that RT gets tonemapped,
    graded and bloomed with the scene.
  - Any harness that swaps pane materials must keep the `FrontRoomsMetalGlassTarget` component.

## 11. Limits

- Seed 4242 near the start only (25 chunks). One Level 0 window and one Office window, the same ones as the audit.
- The AFTER pane is 6 mm and has shadows off, but it has no glazing stop or stool trim (§1).
- The props in `41` and `42` are staged by the harness at runtime. The rest are real placements.
- Metrics are on 8-bit sRGB output after post (grain, vignette, chromatic aberration), not on HDR radiance.
- The capture tool reads private `FrontRoomsMapWorld` and `FrontRooms3DGame` members by reflection: `built`,
  `windows`, `pane`, `windowByCollider`, `fixtures`, `mode`, `phase`, `playerRoot`, `yaw`, `pitch` and others. I
  checked at 10:20 that main still has them. A rename breaks the tool, not the game.

## 12. Reproduce

In a clone with the glass work (never in the real project):

1. Copy `g10_harness/FrontRoomsGlassG10Capture.cs.txt` to `Assets/Editor/Audit/FrontRoomsGlassG10Capture.cs`, and
   `g10_harness/G10Before_*.mat.txt` (copies of the shipped prop materials) to `Assets/Editor/Audit/G10/*.mat`.
2. Run `Unity -batchmode -projectPath <clone> -executeMethod FrontRoomsGlassG10Capture.RunBatch -logFile <log>`.
   The run takes about 3 minutes after compile and writes to `Verification/glass_g10/`.
   `g10_harness/run_unity.sh.txt` waits while another process has the clone open.
3. Build the sheets with `/usr/bin/python3 g10_harness/g10_sheets.py <clone>/Verification/glass_g10 <out>` (needs
   Pillow).
