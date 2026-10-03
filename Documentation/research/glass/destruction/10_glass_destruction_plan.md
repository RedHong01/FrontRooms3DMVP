# 10 — Glass destruction plan for FrontRooms (GD1 → GD3, plus the ray-traced glass track G14)

Status: PLAN, 2026-10-03. Planner output of the glass-destruction-research workflow. Nothing in Red's project or any clone was changed; this file is the only output.

Built from the four research reports in this folder, read in full:
- `01_conference_destruction.md` (how shipped games build destruction) = **[01]**
- `02_glass_in_games_and_real_glass.md` (glass in games, real 1990 glass) = **[02]**
- `03_micro_cutscene_camera.md` (the shot) = **[03]**
- `04_unity_implementation.md` (Unity/URP build path, Blender prototype) = **[04]**

Also read: `../../interactables/00_map_constraints.md` (binding), `../../interactables/06_period_windows.md` = **[06w]**, `../../interactables/03_readability_placement_shots.md` §3.5 = **[03i]**, `../../interaction_audit/FrontRoomsShotTimings.proposal.cs.txt`, `../20_verification.md` (G10), `Documentation/VISUAL_CHAT_TASKS.md` (G8, G9, G12, G14, GD1–GD3, W8), the RT bridge code, and the running G14 track's first probe and benchmark output in the session scratchpad (**PRELIMINARY**: that workflow has not reported yet).

Tags: **MEASURED** = measured on this Mac. **ESTIMATE** = arithmetic or judgement. **UNVERIFIED** = not confirmed from a source. Short source tags like **[Kihl10]** resolve in §8.

---

## 0. Short answer for Red

1. **What the industry does.** Most shipped games break the object into pieces *before* the moment of breaking, keep the intact model on screen, and swap to the pieces when damage crosses a threshold. Battlefield: Bad Company 2, Control, Uncharted 4, Resident Evil 7 and Unreal's Chaos all work this way [Kihl10][Richter20][ND-U4][RE7-CEDEC17][Chaos].
2. **Your "stage models swapped" idea is mostly right, with two corrections.**
   - The stages are usually **one set of pieces that comes apart step by step**, not a separate model per stage (Chaos cluster levels, Siege's piece graph) [Chaos][LHeureux16].
   - **The swap alone never sells it.** Every studio hides it with edge detail, debris, particles, sound and camera. Frostbite's recipe is: remove the piece, add detail around the hole, paint a damage mask, add debris [Kihl10]. Early cracks are often only a texture, and that works only when the cues around it are right [02 §3.3].
3. **Why ours looks fake.** It is a drawing on one unbroken plane: same-width, glowing, curved lines around a glowing star. The reflection never breaks, nothing moves, nothing crushes. At 1.0 s the pane simply vanishes, with no shards, no teeth in the frame and no glass on the floor.
4. **What we will build: three stages of real geometry, on the three sound beats we already have.**
   - **0.35 s:** crack faces appear inside the pane, plus a crushed white spot and falling chips.
   - **0.70 s:** the pane is swapped, in place, for its own ~150 pieces, each tilted by less than 1°, so reflections split into misaligned facets.
   - **1.00 s:** the pieces fall as real physics. Teeth stay in the frame, and glass stays on the carpet.
5. **The pieces are built when you press E, around the exact point you aimed.** The pattern is radial cracks plus ring cracks (what impacted glass really does), not the "cobblestone" Voronoi that most tools make. This is still "built in advance and swapped stage by stage", just 0.35–1.0 s ahead, and every break is different. A baked set of 18 variants per glass type stays as a fallback.
6. **Glass: 6 mm (1/4 in) annealed float glass.** It is the only common 1990 glass that cracks in stages and leaves teeth. Today's codes would demand tempered glass for a pane this large and this low, and tempered glass dices all at once with no stages. Whether 1990 codes did the same is UNVERIFIED, so annealed is an art-direction choice with a period alibi (an older building) [02 §2.1][06w §2.4].
7. **The micro-cutscene: "Brace, strike, flinch" (1.65 s, no hands).**
   - The body steps up to the glass and braces.
   - Three wound-up strikes land exactly on the sound beats. On each hit the glass freezes for 2–3 frames while the camera keeps moving.
   - At the shatter the view lunges through, flinches away, then looks back at the empty frame.
   - You get control back 0.10 s after the shatter. Any movement skips the rest, and a chase skips it all.
8. **ChatGPT's ray-traced glass is added as a task (G14), and the fracture is designed for it.** It is real hardware ray tracing on your M3 Max, done by a native Metal plugin that goes around Unity (Unity itself reports "no ray tracing"). It is still a prototype: it does not run in the game yet, its field of view is wrong, it paints over the glass instead of adding a reflection, and it stalls once a second. We fix that first (G14 P0/P1), then feed it the fracture pieces (G14 P4). Real tilted pieces give broken, faceted reflections for free.
9. **WebGL is a separate, cheaper tier** with the same beats: about 60 pieces, simple scripted falling, no ray tracing. Desktop is never reduced for it.

---

## 1. Why the current crack reads fake (ranked)

Frames: `../images/04_crack_palm_hooks.jpg`, `../images/03_window_close_masks.jpg`. Shader: the glass track's `FrontRoomsGlass.shader` in the private clone `proj_glass` (read only).

| Rank | What real cracked glass shows | What ours does | Fixed by |
|---|---|---|---|
| 1 | **The pane actually breaks.** Pieces shift slightly, so the reflection and the view jump across each crack | One flat box. The "facets" are only a shader normal tilt of up to about ±0.03 (`:249`), which the Metal ray tracer cannot see (it uses triangle normals) | Real pieces, tilts baked into the geometry (§2.3 S2) |
| 2 | **Crack shapes.** Near-straight radials that kink and fork outward; ring cracks are straight chords that end on the radials; later cracks end on earlier ones [SWGMAT04] | 9–14 sine-wobbled spokes from one hub; ring arcs float free; no forks, no T-ends | The crack-graph generator (§2.6) |
| 3 | **Light.** A crack is a 6 mm-deep mirror inside the glass: it blazes where it mirrors a lamp and is dark elsewhere [02 §2.4] | Every line is the same self-lit cream, from an emission term of 3 × crack (`:379-380`), even in a dead-lamp room | Crack faces as geometry, no emission (§2.4) |
| 4 | **Depth.** A doubled line or a green band at an angle; anti-aliased edges | A painted 0.8 mm line with no MSAA, so it shimmers in motion | Crack fins and bevelled piece faces (4× MSAA works on them) |
| 5 | **The impact.** A small, crushed, frosted crater with chips missing | A glowing star | Crater mesh ≤ 1.5 cm, crush mask, chips |
| 6 | **Timing.** A crack crosses the pane in about 1 ms, so cracks appear in one frame, in pops [02 §2.2] | `_Crack` grows smoothly (plus a 60 ms `CrackReveal`) | Stage index on the beat frame, no growth between beats |
| 7 | **The ending.** Shards, teeth left in the stop, glass on the floor, dust | `Kill(window.pane)` deletes the pane | Stages S3–S4 |
| 8 | Small cues: the pane bows under load, glints, chips on every pop, fine glitter falling back toward the breaker (86% of backward fragments land directly below the frame [RCMP91]) | None | Bow, particles (§2.3) |

**One trap to plan around.** Our rooms are evenly lit, so a pane reflects very little face-on: G10 measured +2–4 /255 even with a perfect reflection (`../20_verification.md` §0). Broken facets (cue 1) therefore read mainly **at an angle, against a lamp, or with a dark room beyond**. Face-on, the crack faces, crater, chips and gaps between pieces must carry the read. Verification (§5) uses all three kinds of view.

---

## 2. The breakage design

### 2.1 Glass type and fracture pattern

| Window member [06w §0] | Where | Glass | How it breaks | In this plan |
|---|---|---|---|---|
| W-L0 back-office light | Level 0 (every live map window has a Level 0 side) | 1/4 in (6 mm) clear annealed float | Radial + ring cracks, long daggers, teeth stay | **BUILD** (profile `Annealed6`) |
| W-OF office borrowed light | Office | same | same | **BUILD** (same profile) |
| W-RN corridor wire light | Run (no map windows yet) | 1/4 in polished wired glass | Cracks, then hangs on the wire; needs a two-stage break (a gameplay change) | PARK: profile `Wired6` as data only |
| Tempered option | e.g. the Exit, as a tell | 6 mm tempered | No crack stages; the whole pane dices into ~1 cm granules at 1.0 s; no teeth | PARK: profile `Tempered6` as data only |

The physics the annealed pattern is built to:
- Radial cracks come first. Ring cracks form between them when the pane is held on all sides, as mostly straight chords ending on a radial; later cracks end at earlier ones [SWGMAT04].
- Branching grows with the energy of the hit [FM99]. A hard hit leaves a crushed, whitish crater [SWGMAT04].
- Holding a load for one second changes nothing visible except the pane bowing; failure is then sudden [02 §2.2]. **Three blows** are what produce visible stages, so the shot uses strikes, not a push (§3).
- The code question: today's safety-glazing rule [IRC-R308] calls our pane a hazardous location (larger than 9 sq ft, bottom edge below 18 in, top edge above 36 in, floor on both sides). The federal rule of 1977 [CPSC1201] covers doors, not fixed windows. The late-1980s model-code wording is UNVERIFIED.

### 2.2 Where the glass sits (window root frame, metres) [06w §4]

| Item | Value |
|---|---|
| Window root `Window {a}-{b}` | Unscaled. Opening centre, on the wall line, at floor level; +Z into cell b |
| Visible glass slab | 1.391 × 1.642 × 0.006, centred (0, 1.175, 0); 12 mm of it hidden behind 16 mm stops on both faces |
| Exposed glass | 1.367 × 1.617 (X ±0.6835, Y 0.3665–1.9835) |
| Clear zone after the break | X ±0.600, Y 0.390–1.900: nothing remains here |
| Tooth band (needs the map chat's OK) | Jambs X ±0.600–0.6835; head Y 1.900–1.9835; sill Y 0.3665–0.390. Tooth roots continue into the hidden pocket behind the stop |
| Gameplay collider (map chat, unchanged) | `Window pane {a}-{b}`, box 1.4 × 1.65 × 0.03 |

So visible teeth are at most about 8 cm deep at the jambs and head, and about 2 cm at the sill. That is smaller than the 6–24 cm teeth in the [04] prototype; the generator clips them to this band. If the map chat refuses the band, teeth are clipped at the stop line, and the break reads more like tempered glass [03i §3.5].

### 2.3 The stages, mapped onto the hold

Hold time `t` = E-hold progress × 1.0 s up to the shatter, real time after it. Camera beats are from §3.

| t (s) | Beat (sound / camera) | What is on screen | How it is represented | Ray tracing (desktop Mac) |
|---|---|---|---|---|
| **E-down** | Step-in starts | Intact pane | Generator runs on {seed, true aim point, rotation}. Meshes are built in slices over about 10 frames. Piece objects are created disabled | Nothing yet |
| **0.00–0.35 S0 Push** | Stress loop / brace and wind-up 1 | A palm smudge fades in at the impact. The pane bows up to 3 mm toward the far side, so the reflection swims. Dust drifts from the stop | Shader masks (`_Palm`) + an analytic bow normal | Bow as an analytic normal (no acceleration-structure change). Fins + crater registered in slices |
| **0.35 S1 Impact** (one frame) | **Crack1** / strike 1 lands, shake 0.5° | 5–8 radial cracks reach 25–35% of the way to the frame. Each is a hairline face-on and a silver ribbon at an angle. A whitish crushed spot ≤ 1.5 cm. 6–12 chips fall; a puff of powder. The glass holds still for 33 ms | **Geometry:** crack fins (thin quads through the 6 mm, ≤ 400 tris) and a crater (≤ 200 tris) inside the still-intact slab. Crush mask. Mesh-particle chips | Fins/crater instance switched in on the beat. Stage-2 acceleration structure built between 0.35 and 0.70 |
| 0.35–0.70 | Stress / recover, wind-up 2 | **No crack growth.** Only the bow and falling chips move | — | — |
| **0.70 S2 Spiderweb** (one frame) | **Crack2** / strike 2 lands, shake 0.7° | Radials reach the frame; 1–3 rings of chords appear. **Reflections split into facets.** Thin dark and bright gaps between pieces. The crushed core falls out. 10–20 chips; glitter on the sill. The glass holds 40 ms | **Geometry:** one combined stage-2 mesh of all pieces at their final pose. Tilt 0.2–0.8° and push 0.5–3 mm toward the far side, both falling off as e^(−r / 0.35 m). 0.6 mm bevelled crack faces with the green edge | Slab + fins out, stage-2 instance in, same frame. Piece acceleration structures built 0.70–1.0 |
| **1.00 S3 Shatter** | **Shatter** / strike 3 follows through, FOV punch, shake 1.5° | The whole crack network is lit and holds still for 50 ms. Then: inner pieces fly outward at 2–4 m/s (× e^(−r / 0.25 m)); middle bands go at 30–120 ms; outer non-tooth pieces tip out of the stop at 120–300 ms and drop. Teeth stay. 200–400 glints and crumbs, a dust puff, a little glitter toward the camera | Piece renderers enabled at exactly the stage-2 poses. **Rigid bodies in a separate physics scene** (desktop) / scripted motion (WebGL). Particles | Stage-2 instance removed on this frame (no ghost pane); the ≤ 64 largest pieces in as instances; TLAS rebuilt every frame |
| **~1.3–2.0 S4 Land** | ShardImpact sounds at real contacts | Pieces land 0.27–0.64 s after release (from √(2h/g)); about two thirds on the far side. On carpet they mostly stay whole. Large pieces (> 60 cm²) re-break only on hard floors above 2 m/s | Physics | Per-frame TLAS |
| **≤ 2.5 Settle** | — | Each piece freezes after 0.3 s below 0.05 m/s; everything freezes at 2.5 s at the latest | Floor glass merged into one static mesh, teeth into another | Pieces unregistered; 2 static instances |
| Later | Climb plant | Bottom teeth snap off as the player climbs (particles + `TeethSnap` sound). Optional horror beat: one head tooth drops 1–3 s later (off by default) | `PlayerClimbed` event (exists) | — |

### 2.4 Mask, mesh or simulation: one line per element

| Element | Representation | Why |
|---|---|---|
| Palm smudge, grime, dust, crush whiteness | Glass-shader masks in pane-space UVs | URP decals do not project onto transparent surfaces [URP-Decal] |
| Stage-1 cracks | Fin geometry inside the intact slab | Real normals, MSAA, visible to ray tracing |
| Stage-2 cracks and facets | One combined pre-fractured mesh; tilts baked into vertex positions | The ray tracer reads triangle normals only |
| Falling shards | Rigid bodies in a separate physics scene (desktop); scripted motion + one skinned mesh (WebGL) | Gameplay rays never see them (§4.3). **Not** vertex-animation textures: the ray tracer would see VAT shards at rest, a ghost pane |
| Chips, powder, glints, dust | Built-in Particle System (VFX Graph is not installed) | Cheap; covers each swap |
| Teeth, floor glass | Static merged meshes | 2 draws per broken window, persistent |
| Today's `CrackMask` lines and crack emission | **Removed** | They are the fake part |

### 2.5 How the swaps are hidden

1. **On the beat frame.** Every swap happens on the same frame as the sound one-shot and the camera impact. All three key off `GlassCracked` / `WindowShattered` (interim: identical progress thresholds from the shot timings) [04 §4].
2. **Same root, shader, material and pane-space UVs**, so smudges and dust do not jump. The shader reads pane metres from UV0 and the per-pane random value from UV1 instead of the object's transform (`_PaneFromUV`).
3. **Exact tiling.** Stage-2 pieces tile the slab exactly (validated to ±0.05% of the area), so the silhouette never changes. Stage-3 pieces start at exactly the stage-2 poses.
4. **Chips on the new cracks** in the swap frame, the cover Frostbite and Control use [Kihl10][Richter20].
5. **Glass-only hit-stop** of 33 / 40 / 50 ms; the camera never stops (a whole-frame freeze reads as a hitch in first person) [03 §2.3].
6. **No springy settle** on the facets: real glass releases within the crack time.
7. **Ray tracing:** acceleration structures are built before the beat; on the beat only TLAS instances switch.

### 2.6 The pattern generator (one source of truth)

`FrontRoomsGlassFracturePattern.Generate(profile, seed, impactUV, slabSize, rotation)`: pure C#, deterministic, the same on desktop and WebGL [04 §3.3].

- **Rings:** first radius about 3 cm, ×1.55 per ring, nodes jittered ±12%.
- **Radial tracks:** 8–12 at jittered angles; about 2° of wander per ring, kept in order; from ring 2, wedges wider than 0.3 rad fork with probability 0.3 (28–39 tracks measured).
- **Ring chords:** present with probability 0.97 near the centre, falling to 0.45 at the edge. Missing chords make the long daggers.
- **Crush core:** 1.2 cm, which becomes powder, crumbs and the crater, not bodies.
- **Clip** to the slab (Sutherland–Hodgman), **teeth** cut to the tooth band (§2.2), **hierarchy** per piece: band, cluster (release order), primary (shown at 0.35), level-2 sub-cells for pieces over 60 cm².
- **Impact:** the true base-eye aim point, clamped at least 0.2 m from the stop line.
- **Persistence:** `{stage, seed, impactUV, rotation, side}` per window edge.
- **Validation on every build** (also an edit-mode test): area sum ±0.05%, no crossing tracks, every piece convex, no piece under 1 cm² outside the crush core, the same seed gives byte-identical output.

Prototype (Blender 4.3 headless, **MEASURED** [04 §3.2]): 125–171 pieces (25–36 teeth), 6.6k–9.0k triangles with a 0.6 mm bevel, 7.5–35 ms in plain Python. See `images/04_b_crack_graph_eye_centre.png` and `images/04_d_crack_graph_low_right.png`; plain Voronoi for comparison in `images/04_a_plain_voronoi.png`. Four fixes before production: tracks could cross; daggers longer than about 1 m need a secondary crack; teeth must be a subset clipped to the band; one run left a 39 cm² hole that validation must catch.

---

## 3. The micro-cutscene

### 3.1 The recommendation

**Design 2, "Brace, strike, flinch"** [03 §5.2]. The current `Glass` proposal (5 cm lean, −3° FOV, three 4 cm jabs) is shake on top of the normal view, so it reads as feedback, not a shot. The Unlock head dip, which Red liked, reads as a cutscene because the camera goes to an authored pose, holds while the object acts, and returns. The glass gets the same shape, plus beats and a look at the result:

- The camera never cuts; every move is caused by the body or the glass [Arazi19].
- Shake is an additive, rotation-only layer on top of the view [McIntosh12].
- The takeover is a few hundred milliseconds [Duffy16]; control is never taken away for long [Nesky14].
- Only the object stops on impact; the "attacker" keeps moving [Sakurai22].

The implied action: an off-screen elbow or forearm strike from the right, face turned away from the glass (yaw away, roll toward the striking shoulder).

### 3.2 Beat by beat (all values ESTIMATES, to tune on a capture)

Offsets are additive to `BaseEye`: fwd = toward the pane, drop = down (m); yaw + = away from the striking side, roll + = toward the striking shoulder, pitch + = down (°). Values are targets.

| t (s) | Phase | Camera | Glass | Sound (beats unchanged) |
|---|---|---|---|---|
| 0.00–0.25 | Plant and brace | Body step-in over 0–0.20 s to stand 0.55 m from the pane (≤ 0.65 m forward, ≤ 0.25 m sideways, swept). Pose (cubic, 0.25 s): fwd +0.03, drop 0.06, yaw +6, roll +2; look-at toward the impact ≤ 6° yaw, ≤ 8° pitch. FOV −5° over 0.40 s. HUD out (0.15 s), vignette +0.08 | S0 | `Snapshot/Closeup` (new, shared with Unlock); stress loop |
| 0.20–0.29 | Wind-up 1 | fwd 0, yaw +8, roll +3, pitch −1 | — | `StrikeWindup` (optional) |
| 0.29–0.35 | Strike 1 | fwd +0.08, yaw +3, roll +1 (ease-in) | — | — |
| **0.35** | **Impact 1** | Recoil 0.025 m (spring, ω 40 rad/s); shake 0.5° / 0.15 s | **S1 pops; holds 33 ms** | **Crack1** |
| 0.49–0.64 | Wind-up 2 | fwd −0.01, yaw +9, roll +3.5, pitch −1.5 | — | — |
| 0.64–0.70 | Strike 2 | fwd +0.10, yaw +4, roll +1 | — | — |
| **0.70** | **Impact 2** | Recoil 0.03 m; shake 0.7° / 0.18 s; brace drop deepens to 0.08 | **S2 swap; holds 40 ms; facets** | **Crack2** |
| 0.84–0.94 | Wind-up 3 | fwd −0.02, yaw +10, roll +4, pitch −2 | — | — |
| 0.94–1.00 | Strike 3 | fwd +0.12, yaw +3, roll +0.5 | — | — |
| **1.00** | **Shatter** | Follow-through to fwd +0.16 in 0.05 s. FOV punch −3° (total −8°) in 0.05 s. Shake 1.5° / 0.30 s. CA pulse 0.06 → 0.16 → 0.06 over 0.25 s | **S3: holds 50 ms, then release waves** | **Shatter**; `GlassBroken` + `WindowShattered` |
| 1.05–1.17 | Flinch | fwd +0.06, drop 0.08, yaw +12, roll +1, pitch +5 (ease-out) | Pieces in flight | `Flinch` (optional) |
| 1.17–1.40 | Look | fwd 0, drop 0.04, yaw 0, roll 0, pitch +6 (at the sill and teeth); FOV back to −5° | First landings ≈ 1.3 s | `ShardImpact` at contacts |
| 1.40–1.65 | Release | Every offset to 0, FOV to the player's, vignette out (cubic) | Settling | Snapshot released at 1.30 |

Rules that hold throughout:
- **No letterbox, no depth of field, no global slow motion.** The glass shader is `ZWrite Off`, so depth of field would blur the cracks [03 §2.5]. `Time.timeScale` would slow the Relay. An optional shard-only slow motion (0.6× for 0.15 s) is an A/B switch, **off** by default.
- **Comfort limits:** shake rotation only, roll ≤ 4°, FOV punch ≤ 8°, translation ≤ 0.16 m, no sustained sway below 1 Hz (sickness peaks at 0.2–0.4 Hz [Diels13]).
- **Camera-motion setting** (Off / 50% / 100%), as XAG 117 and the Game Accessibility Guidelines ask [XAG117][GAG]. Off = no step-in, no pose; the glass, hit-stop and sound still play.
- **Tap mode:** one tap = one strike (0.35 progress, 0.3 s cooldown).

### 3.3 Locks and the chase

| Window | Move | Look | Ends early when |
|---|---|---|---|
| E held (0 → 1.00) | Locked (the hold) | Free in a ±5° cone | E released (cancel: offsets back in 0.20 s, cracks persist, the next hold resumes from the stage reached). A chase or the Relay's sight **demotes** the shot to Design 1 values at 50% |
| 1.00–1.10 (hard) | Locked | Locked | Only a chase, sight or Caught: skip to release in 0.12 s |
| 1.10–1.30 / 1.40 (soft) | Any move key ends the shot | A mouse move over 3° ends it | Climb start (0.10 s hand-off), chase, sight |

Cost to a hunted player: 0.10 s after the loudest noise in the game, which is 0.26 m of a hunting Relay's approach. A chase removes even that [03 §5.2].

### 3.4 Hands or not

**Default: no hands.** Reasons:
- It matches Red's answer to the audit (W8: "a camera head-dip, no hands").
- Valve found that players do not notice missing arms in first person [Walker20].
- The wind-up before each strike is what makes a camera jolt read as "I hit it" instead of an earthquake [03 §2.7].
- Arms would need the Animation module (not installed), a hero model that holds up at 0.3 m, and a ray-tracing fix first (today the bridge would paint the glass reflection over a skinned arm).

**Alternatives for Red to pick:**
- **(a) Sleeve flash:** a rigid 1990 shirt-sleeve forearm enters lower right for 4–6 frames on each strike. "I hit it" becomes unmistakable. Risk: a rigid arm can look like a mannequin.
- **(b) Reflection-only body (desktop ray tracing only):** a simple 4-part office-worker silhouette that exists only in the glass reflection, posed on the same beats. The stage-2 cracks then break *your own reflection* into facets. Highest spec, and it shows the body only where a real window would.
- **(c) Design 3, "Zoom and slow-mo"** (2.25 s): a camcorder power zoom, shards falling slowly, tilt down then up. The most cinematic, but 0.30 s hard lock plus up to 0.95 s soft lock is long for a hunted player. Parked for camera language C.

### 3.5 Proposed replacement for `FrontRoomsShotTimings.Glass`

The values are [03 §7] with two changes: cracks pop in one frame, and the fracture is centred on the true aim point.

```csharp
// ---- 3.5 Hold to break glass: "Brace, strike, flinch" (replaces Glass). Visual chat proposal, 2026-10-03.
// Offsets are additive to BaseEye and are TARGETS: fwd/drop in metres; yaw + = away from the striking (right) side,
// roll + = toward the striking shoulder, pitch + = down. Hold progress drives t up to Shatter; real time after.
// Gameplay rays read BaseEye only, never the shot camera.
public static class GlassBreak
{
    public const float HoldSeconds = 1.0f, Crack1 = .35f, Crack2 = .70f, Shatter = 1.0f; // sound chat's beats, unchanged
    public const int   CrackRevealFrames = 1;                // cracks pop on the beat frame (replaces CrackReveal .06 s)
    public const bool  ImpactFromAim = true;                 // fracture centred on the base-eye hit, chosen at E-down
    public const float ImpactMinFromFrame = .2f;             // metres from the stop line
    public const float Reach = 1.2f;                         // pane prompt range (was the shared 2.4 m) -- needs Red
    public const float StandDistance = .55f, StepInMaxForward = .65f, StepInMaxLateral = .25f, StepInSeconds = .20f;
    public const float PoseIn = .25f, PoseFovDeg = -5f, PoseFov = .40f, LookCone = 5f, LookAtMaxYaw = 6f, LookAtMaxPitch = 8f;
    public const float BraceFwd = .03f, BraceDrop = .06f, BraceDropAfterCrack2 = .08f, BraceYaw = 6f, BraceRoll = 2f;
    public static readonly float[] WindupStart = { .20f, .49f, .84f }, StrikeStart = { .29f, .64f, .94f };
    public static readonly float[] WindupFwd = { 0f, -.01f, -.02f }, WindupYaw = { 8f, 9f, 10f },
                                   WindupRoll = { 3f, 3.5f, 4f }, WindupPitch = { -1f, -1.5f, -2f };
    public static readonly float[] StrikeFwd = { .08f, .10f, .12f }, StrikeYaw = { 3f, 4f, 3f }, StrikeRoll = { 1f, 1f, .5f };
    public static readonly float[] Recoil = { .025f, .03f, 0f }, ShakeDeg = { .5f, .7f, 1.5f }, ShakeDecay = { .15f, .18f, .30f };
    public static readonly float[] ObjectStop = { .033f, .040f, .050f }; // glass only; the camera never stops
    public const float RecoilOmega = 40f, ShakeNoiseHz = 16f;
    public const float FollowThroughFwd = .16f, FollowThrough = .05f, ShatterFovPunchDeg = -3f, ShatterFovPunch = .05f;
    public const float FlinchStart = 1.05f, FlinchEnd = 1.17f, FlinchFwd = .06f, FlinchDrop = .08f, FlinchYaw = 12f, FlinchRoll = 1f, FlinchPitch = 5f;
    public const float LookEnd = 1.40f, LookDrop = .04f, LookPitch = 6f, ReleaseEnd = 1.65f;
    public const float HardLockEnd = 1.10f, MoveSoftLockEnd = 1.30f, LookSoftLockEnd = 1.40f, LookBlendBack = .15f, SoftBreakLookDeg = 3f;
    public const float CancelBlend = .20f, ChaseSkipBlend = .12f, ChaseDemoteScale = .5f, ClimbHandOff = .10f, CancelRelayDistance = 6f;
    public const float Vignette = .08f, CaPulsePeak = .16f, CaPulse = .25f;                 // CA off with Reduce flashing
    public const float ShardSlowMoScale = .6f, ShardSlowMo = .15f, ShardSlowMoRampEnd = .45f; // A/B switch, default OFF
    public const float TapProgress = .35f, TapCooldown = .3f;                                 // tap mode: one tap = one strike
    public const float ShardLandMin = .35f, ShardLandMax = .60f, SettleToStatic = 1.5f;       // unchanged from Glass
}
```

### 3.6 What the map chat must change for the shot

1. Replace `Glass` with `GlassBreak` in `FrontRoomsShotTimings`.
2. Rig features: a swept **body step-in** to a stand point; a **soft lock** (any move key, or a mouse move over 3°, ends the shot); a **demote tier** (Design 1 values at 50%); a **chase skip** (0.12 s); an instant hand-off to the climb camera (0.10 s).
3. A **1.2 m prompt range for panes** (the 2.4 m shared reach stays for everything else). Needs Red (§6, decision 3).
4. **The Relay's sight or a chase demotes the camera instead of cancelling the hold** (today's audit text says sight cancels). Needs Red (§6, decision 3).
5. **On E release, keep the stage reached:** progress resumes from 0 / 0.35 / 0.70, not from 0 (cracks do not heal).
6. **Look-at target:** the impact point the visual side publishes at E-down (§4.4).

---

## 4. Asset and code list

### 4.1 Blender (kit pipeline, `Tools/Blender/frontrooms_kit/`, written in the clone)

No Houdini is installed, and Blender 4.3 has no Cell Fracture add-on; neither is needed [04 §1.5]. The kit's `finish()` joins everything into one mesh, which is right for props and wrong for fracture, so fracture gets its own scripts.

| Script (new) | Output | Notes |
|---|---|---|
| `glass/crack_graph_ref.py` | The Python reference generator (from `04_proto/web_proto_crack_graph.py`) + JSON + 20 golden seeds | For Red's sign-off renders before Unity work, and the test oracle for the C# port |
| `glass/glass_lookdev.py` | Cycles look-dev frames of S1, S2, S4 from generator JSON: a lamp in the reflection, a dark room beyond, views at 0.55 m face-on and 1.5 m at 45° | 6 samples per profile (3 impact spots × 2 seeds) |
| `assets/glass_crumbs.py` | 8 crumb and sliver meshes (6–30 tris each) + 2 crater meshes (≤ 200 tris), render-only (`kit.no_collider()`) | Normal kit asset |
| `glass/glass_bakes.py` | Fracture-face normal map 256² tileable (hackle and Wallner ripples), crush mask 128², glint sprite 64², dust sprite 128² | Baked with `kitlib` decal UVs |

**Fracture variants:**
- **Runtime:** every break is unique (seed × aim point × rotation).
- **Baked fallback:** the editor menu `FrontRooms/Glass/Bake Fracture Variants` writes 3 × 3 impact centres × 2 seeds = **18 per profile per tier**. Ship them only if the WebGL build-time measurement fails.
- **Look-dev sign-off set:** 6 per profile.

### 4.2 Materials and shaders

| Item | Change | Tier |
|---|---|---|
| `FrontRooms/Glass` (glass track's shader) | Remove `CrackMask` lines, wedge tilt and the crack emission. Add `_PaneFromUV` (UV0 pane metres, UV1 = pane hash, band, kind), an edge mask from vertex colour R (green edge, fracture-face normal map, glints), fin shading as an internal glass-to-air face (Fresnel near 1 at grazing), the crush mask, bow parameters `_BowCentre` / `_BowAmp`. Keep `_Palm`, `_ImpactUV`, grime, the base glass look. Consume the RT hook `_FR_GlassRTReflection` / `_FR_GlassRTWeight` (proposed under G1; not yet in the clone's shader). **No new keywords**: uniform branches only, to protect the WebGL variant budget | all |
| `FrontRooms/GlassShard` | Opaque: dark, smooth, green rim | WebGL moving shards |
| `Glass_Window`, `Glass_Edge`, `Glass_Shard` | Exist in the clone (`FrontRoomsGlassPane.cs:12-14`). Add a dedicated `Glass_Fracture` instance for pieces, so the ray tracer's per-material glass flag cannot be lost | all |
| Floor glass | `Glass_Shard` + a sparkle term | all |

### 4.3 Unity components (visual chat unless noted)

| Component | Kind | Role |
|---|---|---|
| `FrontRoomsGlassTypeProfile` | ScriptableObject | Generator numbers per glass type and tier (`Annealed6`, `Wired6`, `Tempered6`) |
| `FrontRoomsGlassFracturePattern` | Static C# | Deterministic crack graph → pieces, teeth, primaries, clusters, level-2 sub-cells |
| `FrontRoomsGlassFractureMeshes` | Time-sliced builder | Slab, fins, crater, stage-2 combined mesh, piece meshes, teeth mesh |
| `FrontRoomsGlassBreakable` | MonoBehaviour on the `Window {a}-{b}` root | Stage machine S0→S4; owns the visible slab and every stage mesh; listens to map events; restores from the break record; publishes the impact point |
| `FrontRoomsGlassDebrisWorld` | Singleton | Desktop: a separate physics scene (`LocalPhysicsMode.Physics3D`, stepped with `PhysicsScene.Simulate`) with proxy floor, wall and nearby-prop boxes. WebGL: a scripted integrator. Release waves, re-break, settle; one shattering window at a time |
| `FrontRoomsGlassFloorGlass` | Per window | Merged teeth and floor mesh, LOD1, settled-pose registry, `IsGlassAt(pos)` |
| `FrontRoomsGlassVfx` | Prefab set | Chips, powder, glints, dust (counts per tier) |
| `FrontRoomsGlassRefractionFeature` | URP renderer feature, desktop asset only | Requests the opaque texture only while cracked glass or shards are on screen |
| `FrontRoomsMetalGlassRT*` | Native + C# (G14) | Production pass + the fracture API (§4.7) |
| `FrontRoomsShotTimings.GlassBreak` + shot rig | **Map chat** | §3 |

Why a separate physics scene: every gameplay query in this project passes the layer mask `~0`, which **includes** Ignore Raycast (the E ray `FrontRooms3DGame.cs:987`; the Relay's sight and nav casts `FrontRoomsMapHunter.cs:894, 911, 923, 992`), and the collision matrix is all ones [04 §1.2]. So the brief's "Ignore Raycast layer" idea would not keep shards out of the E ray, the Relay's sight or its nav probe. A separate physics scene keeps them out of every query with no change to the map chat's code or the layer settings [Unity-MultiScene] (to be confirmed by a play-mode test, §5 step 6).

### 4.4 Events needed from the map chat (contract)

| Event / call | Exists? | Payload | Used for |
|---|---|---|---|
| `Window {a}-{b}` root | New ([03i]) | Unscaled; opening centre, floor level, +Z into cell b | Parent of the frame, slab and every stage mesh |
| Pane renderer | Change | Disable the pane cube's renderer, keep its collider (`windowByCollider` keys on it) | The visible slab is ours |
| On break | Change | Remove **only** the collider object; never destroy the root | Stage meshes survive |
| `Hold(collider, hitPoint, dt, out progress)` | Change | + `hitPoint` from the base-eye ray | Impact point |
| `GlassHoldStarted(window, hitPoint, seed)` | New | At E-down; seed from the edge hash | Generator start; shot look-at |
| `GlassHold(…, progress)` | Exists | + window id | Bow, palm |
| `GlassHoldReleased` | Exists | — | Stop bow; keep the stage |
| `GlassCracked(window, stage 1/2)` | New (G9) | — | S1, S2; the sound chat's cracks |
| `WindowShattered(window, hitPoint, impulse)` | New (G9) | Impulse = base-eye forward × 2–4 m/s | S3 |
| `GlassBroken(pos)` | Exists, **keep** | — | The sound chat's Shatter |
| Break record per edge | New (G9) | `{stage, seed, impactUV, rotation, side}` | Persistence |
| `WindowBuilt(window, record)` / chunk-drop notice | New | — | Restore and clean up |
| `PlayerClimbed(center)` | Exists | — | Bottom-teeth snap |
| Rule clarifications | New | Approve the 16 mm render-only stop band [06w §4.1] and the tooth band (§2.2) | Frame and teeth |
| RT lines ChatGPT added in `MapWorld` (`:344-347` `Ensure()`, `:1049` the target tag) | Move | To the visual side's render setup; the target goes on the visible slab, not the disabled pane [06w §4.3] | G14 |

### 4.5 Sound events for the sound chat

| Event | Status | Note |
|---|---|---|
| Crack1 0.35, Crack2 0.70, Shatter 1.0 | **Keep** | Fire the cracks from `GlassCracked`, so a resumed hold does not replay a crack. Each crack transient must land on the swap frame (± 1 frame): a real break has a low-frequency flex in the first ~10 ms, then the high-frequency break [Patent5192931] |
| `ShardImpact(pos, mass, speed)` | New (visual → sound) | Landing tinkles at real contacts, muffled on carpet |
| `TeethSnap(pos)` | New | On the climb plant |
| `FrontRoomsGlassDebris.IsGlassAt(pos)` | New | Glass footsteps |
| `Foley/Player/StrikeWindup` (0.20 / 0.49 / 0.84), `Foley/Player/Flinch` (1.05) | Optional | Cloth and breath |
| `Snapshot/Closeup` | New, shared with Unlock | Room tone down about 3 dB during the shot |

### 4.6 Budgets (ESTIMATES unless marked)

| Item | Desktop Cinematic | Desktop High (default) | WebGL |
|---|---|---|---|
| Pieces per pane | ≤ 170 | ≤ 150 | ≈ 60, no bevel |
| Stage-2 mesh | ≤ 10k tris (MEASURED 6.6–9.0k) | same | ≤ 1.5k |
| Fins + crater | ≤ 400 + 200 | same | ≤ 150 + 60 |
| Teeth | ≤ 2k (MEASURED 1.3–1.8k) | same | ≤ 400 |
| Floor glass (merged) | ≤ 9k, LOD1 ≤ 2k | same | ≤ 1.5k, shared with the teeth |
| Moving bodies | ≤ 170, floor re-break on | ≤ 150 | ≤ 40, scripted, one skinned draw |
| Particles at the shatter | 400 | 250 | ≤ 60, floor plane only |
| Extra draws during the hold | +2–3 | +2–3 | +2–3 |
| Extra draws for ≤ 2.5 s after the shatter | +150–180 (≈ 0.4 ms) | same | +4 |
| Persistent draws per broken window | 2 | 2 | 1 |
| CPU: building the meshes at E-down | 1–5 ms total over ~10 frames | same | 3–10 ms over ~20 frames |
| CPU: physics | 0.3–1 ms per step, for ≤ 2.5 s | same | ≤ 0.1 ms |
| Memory per broken window | 1–1.5 MB | same | 0.3 MB |
| Ray tracing (Mac M3+) | See §4.7 | same | none |

### 4.7 What the fracture needs from ChatGPT's ray-tracing bridge (G14)

**What it is, in one paragraph.** A native Metal plugin (`NativePlugin/FrontRoomsMetalGlassRT.mm` → `Assets/Plugins/macOS/libFrontRoomsMetalGlassRT.dylib`), a controller and render pass (`Assets/Scripts/Rendering/FrontRoomsMetalGlassRT*.cs`) and a composite shader. Every second it collects the glass panes plus mesh renderers within 18 m (cap 256), builds one BLAS per mesh and one TLAS from Unity's own vertex buffers, and every frame traces one ray per pixel; where the first hit is glass, it traces one reflection and blends the result over the finished frame. The G14 probe confirmed on the M3 Max that Unity reports no ray tracing while the plugin's Metal device does (**PRELIMINARY** [G14-probe]).

**Defects to fix first (G14 P0/P1)**, from [01 §7.3][03 §4][04 §1.3][06w §5.2], with the probe's first numbers:

| # | Defect | Evidence |
|---|---|---|
| RT1 | Runs only in the map test scene, not the game (`MapWorld:346-347`, standalone only) | Probe: "RT controller after the run started = NONE" in the game path [G14-probe] |
| RT2 | FOV passed in radians where the kernel reads tan(FOV/2) (`.cs:378` → `.mm:75`) | Probe: 1.326 sent vs 0.781 correct (×1.70); the traced pane covers ~35% of the real pane's pixels [G14-probe] |
| RT3 | Composite after post-processing with alpha 1 and `ZTest Always`: the reflection replaces the view through the pane, skips tonemapping, and paints over anything not in its scene | Code reading |
| RT4 | Full scene rebuild every second on the main thread with `waitUntilCompleted`; a blank frame on each reset | Probe (editor): 95–1,071 ms main-thread stall per rescan (median 289 ms over 9 logged rescans); in a 200-frame free run, frames with a rescan took a median 202 ms vs 61 ms overall [G14-probe] |
| RT5 | 256 objects in InstanceID order, not by distance | Probe: none of the 252 renderers within 18 m of the probed pane, and none of the 654 in view, were in the ray-traced scene [G14-probe] |
| RT6 | No `useResource` for referenced structures and buffers [WWDC23] | Code reading |
| RT7 | MeshRenderers and submesh 0 only; flat colour, fixed sun and blue sky; composite shader may be stripped from builds; unguarded `DllImport`s (WebGL link risk); hardware check uses `supportsRaytracing`, which is also true on M1/M2 where RT runs in software [AppleForum744941] | Code reading. Correction to [02]/[04]: the probe found the Relay rig is 16 MeshRenderers (registered 0/16 because of RT5), so it is rigid, not skinned [G14-probe] |

**The fracture contract (G14 P4):**

| Need | Rule | Why |
|---|---|---|
| Where reflection rays start | From the **raster** glass pixels (the glass pass writes normal and depth), not from re-traced primary rays | Facets then come from the stage meshes' own triangle normals; things in front occlude correctly; RT2 and the ghost cases disappear [04 §7.8] |
| Piece count limits | Per window: S1 = 1 instance (fins + crater); S2 = 1 (combined mesh); S3 = the **≤ 64 largest pieces** as instances; smaller pieces stay out of reflection rays via the instance mask (they still get a reflection on their own pixels from the raster-driven rays); after settle = 2 (teeth, floor). Bridge capacity ≥ 1,024 instances, glass and pieces first, then nearest | Today every piece would need its own instance, and 150 pieces cannot fit in a 256 cap shared with the room |
| BLAS: build, refit or rebuild? | Rigid pieces: **build once, never refit, never rebuild**. Build all piece BLASes in one batched encoder from index ranges of one buffer (`FRGlassRT_AddMeshRanges`), during 0.70–1.0 s, never on a beat frame. **Refit only deforming meshes** (none in this plan: the bow is an analytic normal; a wired-glass sag would need it) | Apple: refit for deformation, rebuild the instance structure for moving content [WWDC22][WWDC23]. G14 bench on the M3 Max: a 12-tri BLAS built on its own costs 0.16 ms; a 20k-tri BLAS builds in 0.63 ms and refits in 0.17 ms [G14-bench] |
| TLAS | Rebuild every frame while anything moves; static after settle | G14 bench: 0.18 ms for 256 instances, 0.25 ms for 1,024, 0.52 ms for 4,096 [G14-bench] |
| Glass flag per piece | Per material: bit 0 glass, bit 1 fracture edge (from vertex colour R), bit 2 shard (instance mask); window id in the instance user id; pieces use the dedicated `Glass_Fracture` material. Until per-material flags land, every piece renderer carries `FrontRoomsMetalGlassTarget` | Today the glass bit is set by whichever renderer registers a material first |
| Mesh format | Single submesh; Float32 × 3 positions in stream 0; 16-bit indices; closed 6 mm slabs with flat normals | The bridge accepts only these (`.cs:176-187`); project vertex compression already keeps positions Float32 |
| No VAT on traced pieces | Move pieces by transforms only | The ray tracer reads the static vertex buffer, so VAT pieces would be traced at rest: a ghost pane |
| Lifetime | Swap the slab instance out on the 0.70 frame and the stage-2 instance out on the shatter frame, never at the next rescan; unregister pieces before the floor-glass merge | Otherwise a ghost pane reflects for up to 1 s [03 §4 R1] |
| Crack lines | Stay a raster-shader feature | A 6 mm crack face is too thin for one ray per pixel, and the bridge has no transmission [02 §4.3] |
| Cost in the shot | The pane fills the frame at 0.55 m, the worst case for tracing | G14 bench: 1.5–1.9 ms at 1080p with glass on 100% of pixels, 0.3–0.8 ms at 25% (standalone, outside Unity) [G14-bench]. 150 one-at-a-time BLAS builds at ~0.16 ms each would be ~24 ms (ESTIMATE from the bench), hence the batched build |

### 4.8 Desktop (highest spec) vs WebGL

- **Desktop Mac/Win is the reference.** Full piece counts, bevels, the separate physics scene, refraction along edges, 250–400 particles. Ray-traced reflections on Mac M3+ (G14). Windows keeps report 11's planar reflection for the held pane, with facets offsetting the planar UV.
- **WebGL is its own path**, gated by `#if UNITY_WEBGL`, the WebGL quality level and the WebGL URP asset. Same generator code, beats, events, stage logic and camera values. Different: ≈ 60 pieces, no bevel, opaque moving shards, a scripted integrator, all moving shards in one skinned draw, ≤ 60 particles, no refraction, no ray tracing, no floor re-break.
- **Never** change a desktop value to save WebGL cost. Step 10 of §5 checks that desktop captures are byte-identical before and after the WebGL work.

---

## 5. Build plan for the next workflow (GD3 + G14 P4)

### 5.1 Verification protocol (used by every step)

- **Lab scene** in a private clone: `GlassBreakLab`. One W-L0 window (Level 0 on both sides) and one W-OF window (Level 0 hall ↔ Office). A lit ceiling lamp in the player's room that appears in the reflection. A dark room behind the second window. A fixed seed (the audit harness's 4242). Three fixed hit points: eye-height centre, low right, near a jamb.
- **Cameras:** C1 = the shot camera (Design 2 driver, 0.55 m); C2 = fixed, 45°, 1.5 m, lamp in the reflection; C3 = fixed, face-on, 1.2 m, dark room beyond; C4 = the far side, 2 m, looking at the floor.
- **Frames:** hold t = 0.00, 0.30, 0.34, **0.35**, 0.36, 0.69, **0.70**, 0.71, 0.99, **1.00**, 1.033, 1.05, 1.10, 1.20, 1.40, 1.65, 2.50 s, then settled, then after a chunk rebuild. Fixed 1/60 s step; the frame index of every sound event is logged next to each capture.
- **Side-by-side sheet:** our frame, the real-glass description it must match (checklist below), and a reference photo URL (Commons list in [02 §6]).
- **Real-glass checklist** (pass or fail per frame):

| # | Check | Real-glass basis |
|---|---|---|
| V1 | Cracks appear in one frame, on the beat frame (± 0 frames vs the sound event) | Cracks cross the pane in about 1 ms [02 §2.2] |
| V2 | Radials near-straight, kinked, forking outward; ring cracks are chords ending in T's on radials | [SWGMAT04] |
| V3 | Crack brightness varies along each crack and with the view; nothing glows in a dead-lamp room | Cracks are internal mirrors [02 §2.4] |
| V4 | At 45° (C2): a doubled line or silver ribbon, green on fracture faces and teeth | 6 mm deep crack plane; iron-green float glass [02 §2.4] |
| V5 | Crushed whitish spot ≤ 1.5 cm, no star | [SWGMAT04] |
| V6 | S2 in C2: the lamp's reflection steps across cracks by ≥ 1 cm at 1 m | 0.5° tilt → 1.7 cm at 1 m (arithmetic, [04 §5]) |
| V7 | Grime continuous across every swap: pixel difference outside crack pixels ≤ the 1.2 /255 noise floor | Swap rule 2 |
| V8 | First landings 0.27–0.64 s after release; about two thirds of the glass on the far side | √(2h/g); [02 §2.3] |
| V9 | Teeth only inside the tooth band; nothing in the clear zone | §2.2, [00] |
| V10 | Fine glitter at the wall base on the player's side | [RCMP91] |

### 5.2 Steps

| # | Step | Where | Verify | Waits for |
|---|---|---|---|---|
| 1 | Clone Red's project into the scratchpad, merge the glass track's shader from `proj_glass`, build `GlassBreakLab` and the capture harness (reuse `g10_harness` and the audit harness) | Unity clone | A "before" capture of today's glass at every §5.1 frame | — |
| 2 | Pattern sign-off in Blender: `crack_graph_ref.py` with the four prototype fixes and tooth-band clipping; `glass_lookdev.py` renders 6 samples of S1/S2/S4 | Blender 4.3 | Validation suite (area ±0.05%, no crossings, convex, ≥ 1 cm², determinism); V2 against the reference photos; a review sheet for Red | Red's look approval (steps 3–7 continue on the default) |
| 3 | C# generator, profiles, edit-mode tests | Clone | Golden match to the Python reference on 20 seeds (vertices within 0.1 mm); generation time per slice ≤ 1 ms in the editor | — |
| 4 | Shader changes (§4.2) in the clone's copy of the glass shader, coordinated with the glass track's owner | Clone | S0 frames match the step-1 baseline except palm and bow; WebGL shader-variant count unchanged | — |
| 5 | Stage meshes and `FrontRoomsGlassBreakable` (S0–S2), driven by stub events on progress thresholds | Clone | §5.1 frames 0.00–0.71 in C1–C3: V1, V3–V7 | — |
| 6 | Debris world, release waves, teeth, floor glass, settle and merge (S3–S4) | Clone | Frames 1.00–2.50: V8–V10. Play-mode tests: the E ray, the Relay's sight ray and nav capsule pass through the opening while debris moves in it; the E ray hits the pane collider at every stage before the shatter; no default-scene collider inside X ±0.70 × Y 0.35–2.00 afterwards; physics ≤ 1 ms per step | — |
| 7 | Particles and sound-hook stubs (`ShardImpact`, `TeethSnap`, `IsGlassAt`) | Clone | Chips spawn on the swap frame; particle counts per tier | — |
| 8 | Shot prototype: a visual-side driver in the clone, for captures only (the real rig is the map chat's) | Clone | A 10-second capture per design (D1, D2, optional D3) with Camera-motion Off / 50 / 100; logged peaks within the comfort limits (§3.2) | Red's shot decision before hand-off |
| 9 | Persistence and climb: break record, chunk rebuild, bottom-teeth snap | Clone | After a rebuild the C1 frame is pixel-identical; teeth snap on `PlayerClimbed` | — |
| 10 | WebGL tier, behind the WebGL gates only | Clone + browser | Build time and frame time per stage in a browser; ≤ +4 draws; desktop captures byte-identical before and after this step | — |
| 11 | **G14 P0/P1: ray-tracing production pass** (RT1–RT7 in §4.7): controller out of `MapWorld`, tan(FOV/2) then raster-driven reflection rays, reflection fed into the glass shader before post, BLAS cache + per-frame TLAS on the render thread, ≥ 1,024 prioritised instances, `useResource`, real hit shading (albedo, lamps, zone cube on a miss), Apple9 hardware check, `#if` guards | G14's own workflow (`proj_rt`) | G14's acceptance: oblique and dark-beyond frames, no rescan stall, the traced glass mask matches the raster mask within 1 px | — (already running) |
| 12 | **G14 P4: fracture hookup** (§4.7 contract) | Clone with steps 5–6 + step 11 | C1/C2 frames, RT on vs off, at 0.70–1.65 s: V6 in the traced reflection; no ghost pane after 1.0 s; traced pieces not stale (traced vs raster mask ≤ 1 px on every captured frame); frame time with the pane filling the view ≤ +2 ms at 1080p | Step 11 |
| 13 | Hand-off pack: §4.4 contract to the map chat, §4.5 to the sound chat, the review sheet and captures to Red | — | — | — |

### 5.3 What must wait

- **Red:** the four decisions in §6. Steps 2–7 and 9–10 can run on the defaults; step 8's hand-off and the map contract need decisions 2 and 3.
- **The map chat:** the window root, the events in §4.4, the stop and tooth bands, the reach and the rig. Until then steps 5–9 run on stub events in the clone, and nothing reaches the real game.
- **The sound chat:** cracks fired from `GlassCracked` and the new hooks (§4.5).
- **The G14 workflow:** step 11 before step 12. The fracture design works without ray tracing, so GD3 does not wait for it.
- **Task rows** (for the visual chat to file; this workflow does not edit `VISUAL_CHAT_TASKS.md`): GD3a generator + profiles + tests; GD3b stage meshes + shader; GD3c debris world; GD3d floor glass, teeth, persistence, climb; GD3e particles + sound hooks; GD3f WebGL tier; **G14 keeps its filed row** and adds "P4 = the §4.7 fracture contract"; G8 becomes "baked variants only as the generator's fallback output"; G12 is superseded by GD3.

---

## 6. Decisions for Red

| # | Decision | Recommended default | Alternatives |
|---|---|---|---|
| 1 | **Glass type** for all live map windows | **6 mm annealed** float: staged cracks and teeth; an art-direction choice with a period alibi | Tempered, as a strict modern code reading requires (no crack stages; the whole pane dices at once); or a mix per zone (wired in Run, tempered at the Exit as a tell) |
| 2 | **The shot, and hands** | **Design 2 "Brace, strike, flinch", no hands** (matches your head-dip choice and "no hands" answer) | Add the sleeve flash; add the reflection-only body (desktop ray tracing only, highest spec); or Design 3 "Zoom and slow-mo" |
| 3 | **Gameplay rules for the shot** | **Yes to both:** panes break from 1.2 m (not 2.4 m) with a body step-in of up to 0.65 m; the Relay's sight or a chase **demotes** the camera instead of cancelling the hold (a window is an escape route) | Keep 2.4 m without step-in (the window is small in frame and the shot loses its pose); keep "sight cancels the hold" |
| 4 | **How the pieces are made** | **Built at E-press around your aim point** (every break unique, crack exactly where you hit) | A fixed set of 18 baked variants per glass type (the crack can land up to ~24 cm from your aim, and players see repeats within a few breaks) |

The ray-traced glass (G14) is not on this list: you asked for it to be added, and the plan schedules it (steps 11–12). The fracture works with or without it.

---

## 7. Where the reports disagreed, and what this plan picks

| Topic | Reports said | This plan | Why |
|---|---|---|---|
| Stage 1 representation | [01]: swap to the fractured pane at 0.35 with tilts ≤ 0.3°. [04]: fins inside the intact slab | Fins in the intact slab | Radials alone barely displace a pane held on all sides; one swap fewer; the facet cue is saved for 0.70 |
| Crack growth between beats | [03]/[04]: cracks creep 2–6 cm. [02]: no growth | No growth | Real cracks run in about 1 ms; pops sell it |
| Variants | [01]/[02]/[03i]: 3 × 3 × 2 baked. [04]: built at E-press | Built at E-press, baked as fallback | Exact impact, no repeats, and the camera's look-at needs no snapping |
| Tooth size | [04]: cut 6–24 cm in. [03i]/[06w]: band ≤ 0.10 m (jambs, head), ≤ 0.04 m (sill) | The band | Binding opening rule; needs the map chat's OK |
| Who owns the visible slab | [06w]: a child of the pane, killed with it. [04]: under the window root | Under the window root, owned by `FrontRoomsGlassBreakable` | Stage swaps start before the pane dies; interim fallback is [06w]'s child slab |
| Traced pieces per window | [01]: ≤ 64. [02]: ≤ 24. [04]: one per moving piece (≤ 150) | ≤ 64 largest, the rest masked | Possible once rays start from raster pixels (RT step 11) |
| The Relay in ray tracing | [02]/[04]: skinned, never traced | Rigid MeshRenderers (16), missing only because of the cap order | [G14-probe], PRELIMINARY |
| Shard colliders | Brief: Ignore Raycast layer | A separate physics scene | Every gameplay query uses `~0`, which includes Ignore Raycast [04 §1.2] |

Still UNVERIFIED (carried from the reports): the 1990 model-code safety-glazing rule; that static `Physics.*` queries ignore a local physics scene (test in step 6); every cost estimate; every shot value (tune on a capture); the G14 numbers until that workflow reports; the crack-speed figure (1.2–1.5 km/s, from search summaries).

---

## 8. Sources

Format: title — speaker / studio — venue, year — URL. Full lists are in [01] §9, [02] §6, [03] §10, [04] §14.

**Talks, papers and write-ups**
- [Kihl10] Destruction Masking in Frostbite 2 using Volume Distance Fields — Robert Kihl / DICE — SIGGRAPH 2010, Advances in Real-Time Rendering — https://www.advances.realtimerendering.com/s2010/Kihl-Destruction%20in%20Frostbite(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
- [LHeureux16] The Art of Destruction in Rainbow Six: Siege — Julien L'Heureux / Ubisoft Montreal — GDC 2016 — https://gdcvault.com/play/1023003/The-Art-of-Destruction-in ; slides https://media.gdcvault.com/gdc2016/Presentations/LHeureux_Julien_Art_Of_Destruction.pdf
- [Richter20] Destructible Environments in CONTROL: Lessons in Procedural Destruction — Johannes Richter / Remedy — GDC Summer 2020 — https://gdcvault.com/play/1030643/Destructible-Environments-in-Control-Lessons (read via CGWorld https://cgworld.jp/feature/202008-gdccontrol.html and Game Developer https://www.gamedeveloper.com/production/using-procedural-destruction-to-unleash-chaos-in-i-control-i- ; slides not read)
- [ND-U4] FX Adventures in Uncharted 4: A Thief's End — Neilan Naicker, Raymond Popka / Naughty Dog — SideFX interview, 2016 — https://www.sidefx.com/community/fx-adventures-in-uncharted-4-a-thiefs-end/
- [TLOU2] How Naughty Dog Created the Immersive World of The Last of Us Part II — Michael Fadollone et al. / Naughty Dog — 80 Level, 2020 — https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/
- [RE7-CEDEC17] 壊れ物への取り組み いかにベイクを美しく魅せるか (Approach to breakables) — Capcom (Resident Evil 7) — CEDEC 2017, CGWorld report — https://cgworld.jp/feature/201709-cedec2017-capcom.html
- [Gustafsson14] Cracking destruction (Smash Hit) — Dennis Gustafsson / Mediocre — blog, 2014 (fracture also covered in the GDC 2015 Physics for Game Programmers tutorial) — https://blog.voxagon.se/2014/05/13/cracking-destruction.html
- [VACD13] Real Time Dynamic Fracture with Volumetric Approximate Convex Decompositions — Müller, Chentanez, Kim / NVIDIA — SIGGRAPH 2013 — https://history.siggraph.org/?p=108389
- [Nesky14] 50 Game Camera Mistakes — John Nesky / thatgamecompany — GDC 2014 — https://gdcvault.com/play/1020460/50-Camera (numbered list via a transcription)
- [McIntosh12] The Cameras of Uncharted 3 — Travis McIntosh / Naughty Dog — GDC 2012 — https://gdcvault.com/play/1015514/The-Cameras-of-Uncharted
- [Arazi19] How God of War's cinematography went beyond its no-cut camera (Dori Arazi, Santa Monica Studio) — GameRevolution, 2019 — https://www.gamerevolution.com/features/525735-god-of-war-cinematography-explained
- [Duffy16] The Guts and Gore of DOOM Glory Kills (Robert Duffy, id Software) — Bethesda.net, 2016 — https://bethesda.net/ja-JP/news/the-guts-and-gore-of-doom-glory-kills
- [Sakurai22] Eight Hit Stop Techniques — Masahiro Sakurai — Masahiro Sakurai on Creating Games, 2022, as summarised by Nintendo Wire — https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/
- [Walker20] Valve Talks Half-Life: Alyx And Why Arms Don't Work In VR (Robin Walker) — Game Informer, 2020 — https://www.gameinformer.com/index.php/interview/2020/03/23/valve-talks-half-life-alyx-and-why-arms-dont-work-in-vr
- [Diels13] Frequency Characteristics of Visually Induced Motion Sickness — C. Diels, P. Howarth — Human Factors 55(3), 2013 — https://repository.lboro.ac.uk/articles/journal_contribution/Frequency_characteristics_of_visually_induced_motion_sickness/9346865
- [WWDC22] Maximize your Metal ray tracing performance — Apple — WWDC 2022, session 10105 — https://developer.apple.com/videos/play/wwdc2022/10105/
- [WWDC23] Your guide to Metal ray tracing — Apple — WWDC 2023, session 10128 — https://developer.apple.com/videos/play/wwdc2023/10128/

**Documentation and standards**
- [Chaos] GeometryCollection (`root_proxy_data`, `damage_threshold`) — Epic Games — UE5 Python API docs — https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/GeometryCollection ; Chaos Destruction overview — https://dev.epicgames.com/documentation/en-us/unreal-engine/destruction-overview
- [Valve-SDK] `func_breakablesurf` — Valve — Source SDK 2013 source code — https://github.com/ValveSoftware/source-sdk-2013
- [AppleForum744941] How do I check programmatically if a device supports hardware Raytracing? — Apple Developer Forums — https://developer.apple.com/forums/thread/744941
- [Unity-MultiScene] Multi-scene physics — Unity 6000.3 Manual (`physics-multi-scene.html`, `PhysicsScene.Simulate`) — https://docs.unity3d.com/6000.3/Documentation/Manual/physics-multi-scene.html
- [URP-Decal] Decal renderer feature ("does not work on transparent surfaces") — Unity URP 17 Manual — https://docs.unity3d.com/6000.3/Documentation/Manual/urp/renderer-feature-decal.html
- [XAG117] Xbox Accessibility Guideline 117: Visual distractions and motion settings — Microsoft — https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/117
- [GAG] Game Accessibility Guidelines: option to disable camera movement the player did not cause — https://gameaccessibilityguidelines.com/avoid-or-provide-option-to-disable-any-difference-between-controller-movement-and-camera-movement/
- [CPSC1201] Safety Standard for Architectural Glazing Materials, 16 CFR 1201 (1977) — US CPSC — Federal Register, 2016 — https://www.govinfo.gov/content/pkg/FR-2016-03-23/html/2016-06523.htm
- [IRC-R308] 2021 International Residential Code R308.4.3 (hazardous locations), via the City of Aberdeen tip sheet — https://www.aberdeenwa.gov/DocumentCenter/View/1964/Safety-Glazing-PDF

**Glass physics and forensics**
- [SWGMAT04] Glass Fractures — Scientific Working Group for Materials Analysis — 2004 (hosted by NIST) — https://www.nist.gov/document/glassfracturespdf
- [RCMP91] A study on the backward fragmentation of window glass… — Luce, Buckle, McInnis / RCMP — Can. Soc. Forensic Sci. J. 24(2), 1991 (abstract only) — https://www.ncjrs.gov/App/Publications/abstract.aspx?ID=132202
- [FM99] Instability in dynamic fracture — J. Fineberg, M. Marder — Physics Reports 313, 1999 — https://jay-fineberg.huji.ac.il/node/3202996
- [Patent5192931] Dual channel glass break detector — R. A. Smith, C. A. Bernhardt / Sentrol — US 5,192,931, 1993 — https://patents.google.com/patent/US5192931A/en

**Project data (read only)**
- [G14-probe] The running G14 track's runtime probe, editor, M3 Max: session scratchpad `rtprobe/run1.log`, 2026-10-03 10:31. PRELIMINARY: that workflow has not reported, and its trace output was 0 px in this run, so its ghost-pane test is inconclusive.
- [G14-bench] The running G14 track's standalone Metal benchmark on the M3 Max (outside Unity): scratchpad `rt_research/bench_run1.txt` and `bench_run2.txt`, 2026-10-03 10:33–10:34. PRELIMINARY.
- Code: `NativePlugin/FrontRoomsMetalGlassRT.mm`, `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs` (`maxInstances = 256` `:34`, `rescanSeconds = 1` `:35`, FOV written `:378`), `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:347, 1049`; clone `proj_glass`: `Assets/Resources/Rendering/FrontRoomsGlass.shader`, `Assets/Scripts/Rendering/FrontRoomsGlassPane.cs`.
