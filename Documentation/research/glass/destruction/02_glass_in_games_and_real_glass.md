# 02 — Breakable glass: how shipped games do it, how a 1990 window really breaks, and why ours reads fake (GD1)

Status: DONE (research only), 2026-10-03. Nothing in Red's project or in any clone was changed. This file is the only thing written.

Red's brief (translated): the glass breaking effect looks fake; breakables are usually built as pre-made stages that are swapped one by one ("may not be fully accurate, research it"). This report covers the glass-specific half of that research. Sibling reports: `01` (conference destruction pipelines in general), `03_micro_cutscene_camera.md` (the shot), `04` (Unity/URP build path), then `10_glass_destruction_plan.md`.

Binding inputs read: `../../interactables/00_map_constraints.md`, `../../interactables/06_period_windows.md` (in progress), `../../interaction_audit/02_glass_and_breakables.md`, `../../interaction_audit/FrontRoomsShotTimings.proposal.cs.txt`, `../10_implementation.md` §3.4, `../11_reflections_and_raytracing.md` (headings), `Documentation/VISUAL_CHAT_TASKS.md` (G1–G14, GD1–GD3), the glass shader in the private clone `proj_glass` (`Assets/Resources/Rendering/FrontRoomsGlass.shader`, read only), and ChatGPT's Metal ray-tracing bridge in Red's project (`NativePlugin/FrontRoomsMetalGlassRT.mm`, `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT*.cs`, `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`, read only).

Source tags like **[G4]** point to §6. "UNVERIFIED" means I could not confirm it from a primary or official source. "ESTIMATE" means my own number or reasoning.

---

## 0. Short answer (for Red)

**What games do.** There are six families of breakable glass in shipped games (§1.1). For the cracked-but-standing pane, most games swap a **texture or material**, not a mesh: Valve's Source engine swaps the whole pane to a cracked texture on the first hit and cuts it into a grid of panels with jagged edge masks [G1]; BeamNG swaps painted damage textures per glass type [G13]; an Unreal tutorial notes that in-game glass hits are usually decals or materials [G12]. **Pre-built stages that are swapped** are real, but they are used for the *pieces*: Capcom fractured a boarded-up window in Maya, simulated it many times and baked it to animation for Resident Evil 7 [G4]; Unreal's Chaos breaks a pre-fractured hierarchy level by level [G12]; Naughty Dog's TLOU2 tool builds the shards from a crack texture, so the crack drawing and the pieces match [G2]. Interactive breaks keep piece counts to a few dozen [G4][G10].

**So Red is half right.** Staged, pre-built geometry is the standard for the break itself, and our pane has none. But a texture crack is not what makes ours fake. Games get away with texture cracks because their panes reflect a room, the crack breaks that reflection, the impact is a crushed crater, and the lines behave like glass (§3).

**What real glass does** (§2). A 1990 office window is most plausibly ¼ in (6 mm) annealed float glass (or ¼ in polished wired glass in a fire-rated wall); a code-correct pane this large and this low would be tempered (§2.1). Annealed glass cracks in **instant pops** (a crack crosses the 1.4 m pane in about 1 ms), not in a slow creep. Radial cracks run out from the impact and **fork** more the harder the hit [P3]; ring cracks are **mostly straight chords between the radials**, and later cracks **stop at earlier ones** [P1]. Each crack is a **6 mm-deep mirror plane inside the glass**: it blazes where it mirrors a lamp and is nearly invisible elsewhere, and at an angle it shows as a doubled line or a thin green band. The pieces tilt a little, so **the reflection breaks into misaligned facets**. That facet breakup is the strongest single cue. A fine glitter also sprays back toward the person who broke it: in an RCMP study, 86% of the backward fragments landed directly below the frame [P2].

**Why ours reads fake** (§3, ranked): (1) the pane reflects almost nothing, so the cracks float in air; (2) smooth curved "hairs" from a glowing hub instead of straight, kinked, forking cracks with T-junctions; (3) every line is the same self-lit cream colour; (4) no depth (no doubled line, no green fracture face); (5) the impact is a glowing star, not a crushed crater; (6) nothing shifts across a crack; (7) the cracks grow smoothly instead of popping on the sound beats.

**For the Metal ray-tracing track** (§4.3): fracture pieces are real geometry with their own triangle normals, so in the RT reflection the cracked pane breaks into facets for free. That works only if the pieces are in the acceleration structure, the tilts are in the vertices (the bridge ignores normal maps and shader tilts), the crack stage is **one combined mesh per pane** (the bridge caps the whole scene at 256 instances), and moving shards update the TLAS every frame (today it rebuilds everything once a second). The crack *lines* must stay a raster-shader feature: a 6 mm fracture face is too thin for one ray per pixel to hit reliably.

---

## 1. How shipped games build breakable glass

### 1.1 The six families

| # | Family | How it works | Verified examples | Strong at | Weak at |
|---|---|---|---|---|---|
| A | **Material swap + panel grid** | First hit swaps the whole pane to a cracked texture. The pane becomes a grid of small panels; hit panels vanish; panels with too little support from their neighbours fall or shatter; the remaining panels draw jagged edge masks; shards are sprite-like particles | Source engine `func_breakable_surf` (Half-Life 2 onward) [G1] | Cheap, partial breaks, persistent holes | Gridded look up close; flat crack texture |
| B | **Decal / damage texture + particles** | Crack or hole textures (often painted with fracture brushes), swapped or blended in by damage state; flying shards are particles | BeamNG vehicle glass [G13]; the usual in-game route per an Unreal tutorial [G12] | Very cheap; art-directable | No facets, no parallax unless the shader adds them |
| C | **Pre-fractured mesh, swapped at the break** | The pane is fractured offline (Voronoi, radial, cluster); the intact mesh is replaced by the pieces, which are simulated live | Unreal Chaos geometry collections (radial tool, multi-level hierarchy) [G12]; RE7's interactive breaks in Havok, held to a few dozen pieces [G4] | Real pieces, real physics | Pattern not centred on the hit unless authored per spot [G11] |
| D | **Baked simulation (staged and swapped)** | Fracture and simulate offline many times, pick the best, bake to animation, play it back as an event | RE7 cinematic breaks: Maya + Pull down it, 256 pieces on a boarded window, baked and played in RE ENGINE [G4] | Fully directed, dramatic, cheap to play back | Same every time; no interaction during playback [G4] |
| E | **Runtime, impact-aligned fracture** | Cut the object around the impact point at runtime, or place an authored fracture pattern at the hit point | Smash Hit (carves a small volume at the hit and cuts it with random planes) [G10]; NVIDIA's VACD method (pattern placed at the impact, partial fracture) [G11]; Rainbow Six Siege RealBlast, procedural and material-driven [G5]; TLOU2's glass tool (shards from a crack texture, a fractal glass shader, Havok) [G2] | Breaks where hit, every time different | Engineering cost; piece-count control |
| F | **Voxels** | Glass is a voxel material that breaks with everything else | Teardown [G14] (glass specifics UNVERIFIED) | Unified with the world | A voxel look; not our style |

### 1.2 Per game (what I could verify)

Rows marked UNVERIFIED have no official technical source that I could find. The described behaviour is what to check in footage, not a finding.

| Game / engine | Before the break | How the cracked pane is drawn | Left in the frame | Falling shards | Floor | Reflections | Status |
|---|---|---|---|---|---|---|---|
| **Half-Life 2 and Source games** (`func_breakable_surf`) [G1] | None: the first bullet or club hit already breaks | The whole pane swaps to its `$crackmaterial` (a cracked texture). It is cut into panels of 12 Hammer units, at most 16 × 16 (bigger panes get bigger panels). Each surviving panel picks one of 4 edge types × 3 styles of jagged masks (`glassbroken_01a`…`03d`) multiplied over the cracked texture. The SDK also ships a `ShatteredGlass` shader whose env-map variant adds a reflection masked by the base texture (which materials use it is not confirmed) | Panels connected to the frame. Support is recomputed per think from the neighbours (below 1.25; sides, above and lower diagonals 1.0; upper diagonals 0.25), normalised by 6.75; a panel under 0.2 × `fragility`/100 either drops whole as a spinning pane model or shatters (50/50) | Temp-entity particles on a grid of 4-unit shards, life 2–5 s, random spin up to ±400 per second | No persistent glass | Env map (cubemap) | **VERIFIED from Valve's SDK code** |
| **The Last of Us Part II** (Naughty Dog) [G2] | (UNVERIFIED) | Shards are built from a texture; a fractal glass shader; Havok tweaks; packaged as a level-design tool | (UNVERIFIED) | Havok rigid bodies | Crunch when walked on (press coverage [G18]) | (UNVERIFIED) | Tool **VERIFIED** (80.lv interview, Michael Fadollone); visuals UNVERIFIED |
| **Uncharted 4** (Naughty Dog) [G3] | — | SIGGRAPH 2016 talk lists "Glass Shading"; I could not read the slides (13 MB PDF) | — | — | — | — | UNVERIFIED content |
| **Resident Evil 7** (Capcom, RE ENGINE) [G4] | — | Scripted breaks are baked; interactive breaks use Havok with pre-fractured pieces held to a few dozen | Pieces marked as unbreakable stay | Baked: 256 pieces, enlarged fist capsule for punch; interactive: Havok | Baked into the event | — | **VERIFIED** (CEDEC 2017 report) — the example is a boarded *wooden* window, not glass |
| **Rainbow Six Siege** (Ubisoft, RealBlast) [G5] | (UNVERIFIED) | Procedural, material-driven destruction; glass specifics not in the interview | (UNVERIFIED) | (UNVERIFIED) | (UNVERIFIED) | — | Approach **VERIFIED**; glass UNVERIFIED |
| **Mirror's Edge** PC (DICE, PhysX) [G6] | — | — | — | Without PhysX the fragments are particles; with GPU PhysX they are smaller, more numerous and persist as physical objects | Persistent with PhysX | — | Secondary press only; partly read through search snippets |
| **Control** (Remedy, Northlight) [G7] | (UNVERIFIED) | Procedural destruction, Houdini workflow (GDC Summer 2020 talk, Johannes Richter; not watched) | (UNVERIFIED) | (UNVERIFIED) | (UNVERIFIED) | **Ray-traced reflections on transparent surfaces** (windows), presented by NVIDIA as a world first | RT **VERIFIED** (NVIDIA guide); glass break UNVERIFIED |
| **Battlefield 6** (DICE, Frostbite) [G8] | Health transitions that a game team can customise (swap state, spawn assets) | Part-based destruction; seam and surface emitters choose VFX by visual material; one parameter set drives VFX and audio | — | — | — | — | Approach **VERIFIED**; glass specifics UNVERIFIED |
| **Frostbite 2** (DICE) [G9] | Destruction masks from spheres placed on geometry, turned into a distance field in a volume texture | — | — | — | — | — | Read via summary; mask technique, not glass-specific |
| **Smash Hit** (Mediocre) [G10] | — | Everything breakable is solid glass. At a hit, a small volume around the point is carved and cut by five random planes into convex pieces; vertex normals are preserved through the cuts for soft gradients | The rest of the object | Live rigid bodies | — | — | **VERIFIED** (author's blog) |
| **Unreal Engine 5, Chaos** [G12] | Cluster levels break off as strain is applied | Fracture Mode: Uniform, Cluster, **Radial** (centre, normal, radius, angular and radial steps, angle offset, variability), Planar, Slice, Brick, Mesh | Anchored pieces | Geometry collection rigid bodies; caches for cinematics | — | — | Tools **VERIFIED** (Epic docs) |
| **BeamNG.drive** [G13] | Intact or broken per deform group | Painted damage textures: windshield (laminated) with sparse fracture cracks, kept restrained on purpose; side windows (tempered) with dense cracks and a jagged hole | Edges of the hole | — | — | — | **VERIFIED** (official modding docs) |
| **Teardown** [G14] | Voxel damage | Glass is a voxel material | Voxels | Voxel debris | — | Ray-traced voxels | Glass details UNVERIFIED |
| **Call of Duty** (IW / Treyarch) [G17] | — | A Vancouver SIGGRAPH chapter talk on "Visual Effects and Destruction in Call of Duty: Ghosts" (2014) exists; page unreachable | — | — | — | — | UNVERIFIED |
| **Max Payne 3** (Rockstar, RAGE) [G16] | — | Rockstar's "Design and Technology Series: Visual Effects" video (2012) covers VFX; not watched | — | — | — | — | UNVERIFIED |
| **F.E.A.R.** (Monolith, Jupiter EX) [G15] | — | Semi-destructible environment and a detailed particle system; nothing glass-specific found | — | — | — | — | UNVERIFIED |
| **Hitman (Glacier 2), Receiver 2, Ready or Not** | — | No official technical source found | — | — | — | — | UNVERIFIED |

Footage worth pulling for the reference board (UNVERIFIED until someone watches it): TLOU2 window breaks by melee, brick and gunfire; a Source-engine window shot many times (the panel grid shows); RE2/RE3 remake zombies coming through boarded and glazed windows; Control with RT reflections on, shooting office glass; Ready or Not shooting a glazed door.

### 1.3 Talks and papers on glass and fracture

| Talk / paper | Speaker, studio | Venue, year | What it gives us |
|---|---|---|---|
| 壊れ物への取り組み いかにベイクを美しく魅せるか (Approach to breakables: how to show bakes beautifully) [G4] | 滝 崇海 (romanisation UNVERIFIED), Capcom | CEDEC 2017 | Baked vs real-time; repeat the sim until it is right; enlarge the striking capsule to sell the impact; fill and unwrap the cut faces; piece counts; polygon count about triples after a break |
| The Art of Destruction in Rainbow Six: Siege [G5] | Julien L'Heureux, Ubisoft Montréal | GDC 2016 | Procedural, material-driven destruction (glass details not confirmed) |
| Destructible Environments in CONTROL: Lessons in Procedural Destruction [G7] | Johannes Richter, Remedy | GDC Summer 2020 | Houdini-based procedural destruction (not watched) |
| The Technical Art of Uncharted 4 [G3] | Waylon Brinck, Andrew Maximov, Naughty Dog | SIGGRAPH 2016 | Includes a glass-shading section (not read) |
| Destruction Masking in Frostbite 2 using Volume Distance Fields [G9] | Robert Kihl, DICE | SIGGRAPH 2010, Advances in Real-Time Rendering | Damage masks from spheres → distance field; no per-asset UV work |
| Real Time Dynamic Fracture with Volumetric Approximate Convex Decompositions [G11] | Matthias Müller, Nuttapong Chentanez, Tae-Yong Kim, NVIDIA | SIGGRAPH 2013 | Names the flaw of pre-fracture (the pattern ignores where the hit was) and fixes it by placing an authored pattern at the impact |
| Cracking destruction (blog) and the GDC 2015 physics tutorial [G10] | Dennis Gustafsson, Mediocre | Blog 2014; GDC 2015 | Impact-centred convex cutting for an all-glass game |
| The Future of Destruction in Unreal (Chaos reveal) [G19] | Matthias Worch, Jim Van Allen, Michael Lentine, Epic | GDC 2019 | Chaos fracture tools (read via 80.lv summary only) |

No GDC, SIGGRAPH or Digital Dragons talk dedicated to *window glass* came up in my searches. I am not claiming one exists.

### 1.4 What the games agree on

1. **Breaks happen where the player hit.** Source breaks the hit panel and its neighbours [G1]. Smash Hit's author puts it as "objects always break where they get hit" [G10]. Müller et al. built a method because plain pre-fracture does not line up with the impact [G11]. Our impact point is the crosshair hit, so the fracture must be centred there.
2. **Interactive breaks keep piece counts low; cinematic breaks bake.** RE7 holds interactive pieces to a few dozen and bakes the 256-piece set pieces [G4]. Smash Hit keeps a few dozen convex shapes per body [G10]. Our break is a scripted micro-cutscene with a known start, so it can be baked.
3. **The crack drawing and the pieces come from one source.** TLOU2 builds its shards from the crack texture [G2]. Source's edge masks match the panel grid [G1]. If the cracks on the pane and the pieces that fall do not match, it reads wrong.
4. **The frame keeps its edges.** Source keeps every supported panel and draws jagged edges on it [G1]; Chaos anchors pieces [G12].
5. **Glass is an ensemble.** Naughty Dog says destruction needs sound, lighting and FX together [G2]; DICE drives VFX and audio from one parameter set [G8].
6. **Reflections are part of the glass.** Source draws its cracked glass with an env map [G1]; Control made ray-traced reflections on windows a headline feature [G7].

---

## 2. Real glass: what a 1990 office window is and how it breaks

### 2.1 What glass the window would be

Our pane: 1.4 × 1.65 m = 2.31 m² (24.9 sq ft), bottom edge 0.35 m (13.8 in) above the floor, top edge 2.0 m (78.7 in), floor on both sides (`00_map_constraints.md`).

| Glass | In a 1990 US office | How it breaks | Fit for FrontRooms |
|---|---|---|---|
| **Annealed clear float, ¼ in (6 mm)** | The default flat glass. Float glass went into commercial production in 1960, spread worldwide that decade, and is now the most widely produced form [P10 Float glass]. Allowed wherever the code did not demand safety glazing | Radial and ring cracks; large, sharp, irregular pieces [P10 Tempered glass] | **Recommended look** (as the audit chose). It is the only common type with visible crack stages *and* teeth. Art-directed: the Backrooms is not code-compliant |
| **Tempered (fully toughened)** | Required by today's codes for large panes near the floor (see below); safety glazing has been required in doors since the 1977 federal rule [P6] | No crack stages: the whole pane fails at once into small rounded chunks [P10 Tempered glass]. EN 12150 requires at least 40 pieces in a 50 × 50 mm square [P12], so pieces are about 8 mm (ESTIMATE from that count). A broken tempered pane can stay in its frame as a crazed sheet (Commons "Broken Meat Case Window", not viewed; how long it holds is UNVERIFIED) | Variant only. It would need a different hold: dull flex thumps, no cracks, then the whole pane collapses |
| **Polished wired glass, ¼ in** | The only fire-rated glass for most of the century [P9]; exempt from the 1977 federal impact rule when used in fire-rated assemblies [P6]; effectively banned by the 2006 IBC [P10 Wired glass] | Cracks like annealed glass but the wire holds the pieces; the wire makes the breaks more irregular [P10 Wired glass] | Correct for door vision lites and fire-rated corridor walls. **Our 1.4 × 1.65 m lite is too big for wired glass**: NFPA 80 limits a 45-minute wired lite to 1296 sq in with no side over 54 in [P8], and ours is 3581 sq in, 55 × 65 in. A wired version needs mullions (for example 2 × 2 lites of about 0.66 × 0.79 m). Tell `06_period_windows.md` |
| **Laminated** | Rare for interior office windows in 1990 (UNVERIFIED) | Cracks in a spiderweb, stays in the frame, sags | Not recommended |

**Code status of our window.** The federal rule of 1977 (16 CFR 1201) covers doors, storm doors, sliding doors and bath and shower enclosures, not fixed windows [P6]. Today's codes call a window a hazardous location (safety glazing required) when all four hold: pane larger than 9 sq ft, bottom edge below 18 in, top edge above 36 in, walking surface within 36 in [P7]. Ours meets all four. Whether the 1988-era model codes (UBC, BOCA, SBC) had the same rule is **UNVERIFIED**. A careful 1990 architect would probably have used tempered glass here (ESTIMATE). Annealed stays an art-direction choice, as the audit already said.

### 2.2 How annealed glass breaks under a blunt load

**Cracks are instant.** In soda-lime glass a running crack reaches roughly 1.2–1.5 km/s (high-speed photography work reports cracks jumping to about 1200 m/s, near the terminal speed [P4]; the figure and its attribution came from a search summary and are UNVERIFIED). That is about 1 ms to cross our 1.4 m pane. To the eye and to a 60 fps camera, a crack appears in one frame. There is no visible creeping.

**More energy, more branches.** A running crack becomes unstable above about 0.4 of the Rayleigh wave speed and starts to micro-branch [P3]. In practice, a pane that fails at low stress breaks into a few long cracks and a few big pieces (Commons photo "Broken glas.JPG": a window broken in two parts). A hard, fast hit gives a dense star. The amount of branching tells the eye how hard the hit was.

**Hard hit (stone, hammer, tool, bullet).** It leaves a cone or crater. When the object goes through, the exit hole is larger than the entry [P1]. Around the impact there is a crushed, white, powdery zone with flakes missing. Radial cracks run out from the impact. If the pane is held on all sides, concentric cracks form around it; SWGMAT describes them as mostly straight segments that end on an existing radial crack [P1]. Cracks from a later impact end at the earlier cracks [P1]. Forensic examiners read the blow's direction from the ridges (Wallner lines) on a radial crack's face, which meet the face away from the blow at right angles (the 4R or 3R rule) [P1][P10 Forensic glass analysis].

**Soft hit (shoulder, body, palm).** There is no cone. The pane bends like a plate and fails from a surface flaw on the face that goes into tension. Code impact tests simulate a person with a 100 lb (45 kg) bag swung from 18 in and 48 in [P6]. I found no source describing the soft-body crack pattern; my reading is a few long cracks from one origin and large pieces (ESTIMATE). Sibling report `03` reaches the same conclusion from the camera side: a palm shove rarely breaks 6 mm annealed glass, so a strike reads better.

**Holding for one second vs several blows.** Glass is weaker under long loads ("static fatigue"): ASTM E1300 rates annealed glass at a load factor of 1.0 for 3 s and 0.43 for 30 days [P13]. Over one second this changes nothing you can see. While the load is held, the only visible change is the pane **bowing**, which makes the reflection swim. Failure is then sudden. **A series of blows** is what produces visible stages: each blow adds a new set of cracks that end on the old ones [P1]. Our three sound beats (Crack1 0.35 s, Crack2 0.70 s, Shatter 1.0 s) therefore read as **three blows**, not one steady push. This matches design 2 in `03`.

**Edge cracks** (not our break, but useful set dressing). Thermal cracks start at an edge flaw, run at about 90° to the edge, are curved and smooth, and show no impact point [P1][P5]. One old thermal crack in an intact pane says "this building is old" without breaking anything.

### 2.3 Shards: shapes, sizes, where they go

- **Shapes.** Annealed glass gives irregular, sharp pieces [P10 Tempered glass]: long daggers and wedges between radials, polygons between the radials and the ring chords, and tiny fragments near the impact. In an impact break the small particles can clear the opening and hide the pattern [P5].
- **Teeth.** The pieces held by the glazing stop (or putty) stay in the frame. The audit already plans them as kinematic render-only teeth. A sloping tooth at the head can fall a moment later (UNVERIFIED; I ran out of searches to source this).
- **Back toward the breaker.** In an RCMP study of backward fragmentation, 86% of the recovered fragments were directly below the frame. About 90% of the fragments in the first grid row were 0.15–0.85 mm, the count fell four- to five-fold every 45 cm away from the wall, and most were found on the two subjects' shirts and jackets [P2] (abstract only; the full paper was not read). **For us:** a fine glitter on the player's side, packed against the wall base, plus a puff toward the camera on the shatter. The bulk of the glass goes to the far side (the forward share is UNVERIFIED; see Pounds and Smalldon 1978, cited in [P1]).
- **Falling time.** t = √(2h/g). From the head (2.0 m): 0.64 s. From mid-pane (1.18 m): 0.49 s. From the sill (0.35 m): 0.27 s. This agrees with the shot proposal's `ShardLandMin/Max` 0.35–0.60.
- **Our floors are carpet** on both sides (loop-pile in Level 0, carpet tiles in Office; `FrontRoomsMapWorld.cs` theme floors and `Assets/Resources/Surfaces/*_Carpet.mat`). Shards landing on carpet mostly nest in the pile and do not shatter again; the landing sound is muffled (ESTIMATE, physical reasoning). The "second-level fracture on hitting the floor" in G12 is right for hard floors (the Run corridor) and should be rare on carpet.

### 2.4 How cracks catch light

| Cue | Physics | What to see |
|---|---|---|
| **Cracks are mirrors** | A crack is a thin air gap inside the glass. Light inside the glass that meets it beyond the critical angle (asin(1/1.5) = 41.8°) is totally reflected [P11] | Each crack segment is a small vertical mirror 6 mm deep. It is **bright where it mirrors a lamp or a lit wall toward the eye**, and dark or nearly invisible elsewhere. Brightness changes segment by segment and moves as the camera moves |
| **Rough zones scatter** | Fracture faces go from a smooth mirror near the origin to mist and hackle further out [P1][P15]; striations and rib marks follow the crack [P1][P16] | The crushed origin and rough segments read whitish from every angle. Smooth segments read only when they mirror something |
| **Depth and double lines** | The crack plane runs through the full 6 mm thickness | At an angle θ from face-on, the crack face shows as a band 6 mm × sin θ wide, edged by two lines (front and back surface). At 45° from 1 m that is about 4 mm, or 3 px at our 76° FOV in 1080p (ESTIMATE). It is visible at the hold distance |
| **Green** | Iron (Fe²⁺) tints float glass green, more so along long paths [P10 Float glass] | The fracture faces, edge-on shards and teeth look green; face-on the glass looks clear |
| **Iridescence** | A crack that is nearly closed is a thin air film, so it shows thin-film interference colours, as in Newton's rings [P10 Thin-film interference, Newton's rings] | Small rainbow fringes on some cracks (how often this shows on window cracks is UNVERIFIED) |
| **Facets** | Pieces tilt slightly once cracked | The reflection is offset at every crack. A tilt of 0.5° moves the reflection of an object 3 m away by about 5 cm (2 × 0.5° = 1°; 3 m × tan 1°; ESTIMATE), which is clearly visible. The view *through* the glass shifts much less (6 mm slab) |
| **Glints** | Tiny chips along the crack edges | Sparkles that switch on and off as the camera moves |

### 2.5 Sound to picture

- Glass-break detectors listen for a **low-frequency positive pressure wave** (the inward flex of the pane, around 50–100 Hz) within the first ~10 ms, followed by **high-frequency breaking sound** (around 6.5 kHz) between about 10 and 77 ms [P14]. In picture terms: on each blow, the reflection jolts (flex) and the cracks appear in the same frame as the bright transient.
- Since cracks are instant (§2.2), the crack frame and the crack sound transient must coincide within a frame (16 ms).
- After `Shatter`, landing sounds follow the falling times in §2.3 (0.27–0.64 s), muffled on carpet. The sound chat's beats (0.35, 0.70, 1.0 s) stay; the picture lands on them.

---

## 3. Diagnosis: why our prototype reads fake

### 3.1 What the prototype is

`CrackMask` in `FrontRoomsGlass.shader` (clone `proj_glass`, read only) draws 9–14 radial lines from `_ImpactUV`. They wander with two sines of the distance (`0.05·sin(9r) + 0.02·sin(31r)`), and their reach grows with `_Crack`. Three ring arcs at radii of about 5, 16 and 33 cm appear at `_Crack` 0.30, 0.55 and 0.80, each segment kept or dropped at random. A crush disc sits at the impact. Each wedge between two rays tilts the normal by up to ±0.03 (about ±1.7°). Crack pixels get albedo (0.70, 0.73, 0.71), alpha +0.55, smoothness 0.35, and an emission term of `3 × crack × dust colour × 0.5 × ambient` gathered from both sides (2× for the crush disc). A radial line is a 1.6 mm core (0.8 mm either side of its centre line) plus one pixel of anti-aliasing; a ring line is 0.8 mm. Frames: `../images/04_crack_palm_hooks.jpg` (left `_Crack` 0.55 seed 3, right `_Palm` 1 + `_Crack` 0.2). In `../images/02_window_old_vs_new.jpg` the new pane is almost invisible head-on, because the Level 0 room gives it almost nothing to reflect.

Looking at a 2× crop of frame 04: cream lines of even width and brightness; gentle S-curves; a glowing star at the hub; ring pieces as short loose arcs that do not meet the radials; the room behind continuous across every line; the palm a faint white ghost.

### 3.2 Cues real cracked glass has and ours lacks, ranked by how much each sells

| Rank | Real cue | Ours | Sells | Lives in |
|---|---|---|---|---|
| 1 | **The reflection breaks into misaligned facets** (§2.4). This is how the eye knows a surface cracked | The wedge tilt exists, but the pane reflects almost nothing, so the lines float in air like scratches on a lens | Very high | Reflection content (zone cubes, probe, or the Metal RT bridge) **plus** real per-piece tilt |
| 2 | **Crack shapes**: radials as near-straight runs with kinks and forks (my description, UNVERIFIED until checked on the photos in §6; branching grows with energy [P3]); ring cracks as straight chords between radials; every later crack ends in a T on an earlier one [P1] | Smooth curved hairs from one hub; no forks; ring pieces float free; lines never end on other lines | Very high | The crack graph (one 2D graph per variant, §4.2) |
| 3 | **Brightness depends on view and light**: a few segments blaze, most are dark (§2.4) | Every pixel of every line has the same self-lit cream colour, even in a dead-lamp room (the emission term) | High | Shader: light each segment as a vertical mirror with its own direction |
| 4 | **Depth**: a 6 mm deep plane, so a doubled line or a green band at an angle, with parallax as the head moves | A 2D line painted on the surface | High at 0.6–0.95 m (the hold distance) | Shader (parallax offset along the crack normal) or real fracture-face geometry |
| 5 | **The impact**: a crushed, frosted crater, flakes missing, a cone on a hard hit; irregular | A perfect glowing star | High: it is the centre of the micro-cutscene | Geometry (a small hole and chips) plus a frosted crush mask |
| 6 | **Displacement**: pieces sit slightly out of plane; small chips missing near the impact; the room behind steps across some cracks | The background and reflection are continuous across every line | Medium-high | Geometry (per-piece offsets of 0.2–1 mm, tilts of 0.2–1°; ESTIMATE) |
| 7 | **Timing**: cracks appear in one frame, in pops on the blows (§2.2) | `_Crack` grows continuously; the proposal reveals each stage over 60 ms (`CrackReveal`) and lets cracks "creep" between beats | Medium-high (motion is what the eye catches) | Driver: stage index, not a 0–1 reach; reveal ≤ 1–2 frames |
| 8 | **Debris at each pop**: chips and powder fall from the impact; glitter on the sill and at the wall base on the player's side (§2.3) | None until the pane is deleted | Medium | Mesh particles, render-only |
| 9 | **Flex**: the pane bows on each blow, so the reflection wobbles | Rigid | Medium (needs a reflection to show) | Vertex offset (and a BLAS refit for RT, §4.3) |
| 10 | **Glints** along rough crack edges | None | Medium-low | Shader sparkle mask along the crack graph |
| 11 | **Green** on fracture faces and teeth at an angle | None in the crack stage (the green edge exists only on the pane's outer edges) | Low-medium | Shader / fracture-face material |
| 12 | **Iridescence** on a few cracks | None | Low | Shader, optional |
| 13 | **Hand marks** where the pane was pushed | `_Palm` exists but barely reads | Low (and the shot may show no hands) | Shader |

**Things ours has that real glass does not:** a glowing hub; lines that glow in the dark; curves with a steady wave; ring arcs floating in the wedges; cracks that stop in mid-glass on a smooth taper everywhere (real radials mostly run to the frame or into another crack once the energy is high).

### 3.3 Red's theory, checked

Red suspected the fakeness comes from not using pre-built stages. The research says:

- **Right about the pieces.** Every verified game with real breaking (RE7, TLOU2, Chaos, Smash Hit) uses real geometry for the pieces, and RE7 bakes the hero breaks [G2][G4][G10][G12]. Cues 1, 4, 5 and 6 above are geometric, and a single flat shader pane cannot give them convincingly.
- **Not the whole story for the cracks.** Games often draw the pre-break cracks as textures [G1][G12][G13]. They work because the cues in §3.2 are there. Our cracks fail on shape, lighting and the missing reflection more than on being procedural.
- **So the answer is a hybrid** (for `10_glass_destruction_plan.md` to decide): pre-fractured, impact-centred pane geometry for each stage, swapped on the beats, **and** crack lines drawn by the shader from the *same* crack graph, the way TLOU2 builds shards from its crack texture [G2].

---

## 4. What the fracture assets need

### 4.1 Stages (proposal for the plan; numbers are ESTIMATES)

| Stage | When | Geometry | Shader / particles |
|---|---|---|---|
| S0 intact | Before the hold | Today's pane (or a 16 × 16 grid pane if it must bow under RT) | Glass shader, no crack |
| S1 first blow | 0.35 s | Pane cut along a short star of 4–6 radials, 10–25 cm long, around a small crushed hole; pieces tilted 0.1–0.4° | Crack lines from the graph, crush mask, chip burst (10–20 mesh chips), powder |
| S2 second blow | 0.70 s | Radials reach the frame; 1–2 rings of chords; 30–80 pieces; tilts 0.2–1°, offsets 0.2–1 mm; a few centre pieces missing | Lines, glints, more chips; glitter on the sill |
| S3 shatter | 1.0 s | The inner pieces leave (baked sim or live rigid bodies on a render-only layer), ≤ 24 moving bodies plus mesh particles; teeth stay | Shatter burst, backward glitter toward the camera |
| S4 aftermath | +0.3–0.7 s | Teeth (one combined mesh, outside the 1.4 × 0.35–2.0 opening) + floor glass (one combined mesh per side, most of it on the far side) | Static; glint decals on the carpet |

Rules:
- **Impact-centred.** Either author variants per impact zone (for example a 3 × 3 grid of zones × 2 seeds, picked by the hit and mirrored), or place one authored 2D crack graph at the hit point and clip it to the pane rectangle at runtime, then extrude it to 6 mm. Because the pane is flat, the clip is a 2D polygon clip, which is cheap (ESTIMATE). That is the idea of Müller et al. [G11] reduced to 2.5D.
- **One crack graph per variant** drives the S1/S2 piece boundaries, the shader's crack lines (as a distance-to-crack channel or a vertex attribute), the S3 pieces and the S4 teeth, so lines and pieces always match [G2].
- **Each piece is a 6 mm slab** with its face triangles (Glass_Window) and fracture-face triangles (green, smooth, the "mirror" material).
- **Render-only.** No colliders that the E ray, the Relay's sight ray or its nav probe could hit (`00_map_constraints.md`). Live shards, if any, need colliders on a layer outside `Physics.DefaultRaycastLayers` (the Ignore Raycast layer is excluded by default [M4]) and must also not collide with the player's controller, or they can block the climb. Teeth stay outside the opening.
- **Persistence.** The map stores stage, impact and seed per window (G9), so a rebuilt chunk shows the same S2 or S4.

### 4.2 Shot and sound alignment

- One stage swap per sound beat, in the same frame. No growth between beats; between beats the only motion is flex (reflection wobble) and falling chips.
- Three blows (design 2 in `03`) match the physics better than a steady press (§2.2).

### 4.3 What the Metal ray-tracing bridge needs from fracture assets

Reading of ChatGPT's bridge as it is today (prototype; G14 takes it to production). Line numbers are Red's project, 2026-10-03.

**What it does.** Every second (`rescanSeconds` 1, `FrontRoomsMetalGlassRT.cs:35`) it finds every `FrontRoomsMetalGlassTarget` (the map adds one to each pane, `FrontRoomsMapWorld.cs:1049`), plus every `MeshRenderer` within 18 m of the nearest one (`:33`, `:145–155`), resets the native scene and builds one BLAS per mesh and one TLAS (`:162`, `:216`). Each frame a Metal compute kernel traces a primary ray per pixel. Where the first hit is a glass material, it reflects once off the **geometric triangle normal** (`.mm:214`, `:282`) and shades the second hit with a flat base colour and a fixed sun (`.mm:230–242`), or a sky gradient on a miss (`.mm:223`). A full-screen pass blends the result after post-processing (`FrontRoomsMetalGlassRTRendererFeature.cs:17`).

| Need | Why (code) | What the fracture assets must do |
|---|---|---|
| **Piece count** | The whole scene shares 256 meshes and 256 instances (`kMaxInstances`, `.mm:32`; `maxInstances`, `.cs:34`). Every glass target is registered whatever its distance, and when the cap is hit the loop stops (`.cs:152–155`), so nearby walls can drop out | S1/S2: **one combined mesh per pane** (all pieces, 1–3 k triangles, ESTIMATE). S3: ≤ 24 moving piece instances for ≤ 2 s; mesh particles stay out of RT (only `MeshRenderer` is scanned, `.cs:145`). S4: one teeth mesh and one floor mesh per window, or leave the floor glass out |
| **Facet tilt in the vertices** | Normals are per-triangle geometric normals; vertex normals, normal maps and shader tilt (`CrackMask`) are invisible to RT | Bake the 0.2–1° tilts and sub-millimetre offsets into each stage mesh (or into per-piece transforms) |
| **BLAS: build once, rebuild never for rigid pieces** | Today every rescan resets and rebuilds every BLAS synchronously (`waitUntilCompleted`, `.mm:408`, `:490`), and moving objects are frozen in the reflection for up to 1 s | Rigid shards never change shape, so their BLAS can be built once when the chunk (or the variant) loads. Only the **TLAS** changes as they move: rebuild it every frame (Apple recommends a full instance rebuild when objects move a lot [M2]). That needs G14's production rework (per-mesh BLAS cache, per-frame TLAS on the GPU, no CPU wait) |
| **BLAS refit only for deforming meshes** | Metal refit is much faster than a rebuild but cannot add or remove geometry, and quality drops as the shape changes [M1] | The pane bowing during the hold (if it should show in RT), a wired-glass sag, and the Relay's skinned mesh (via `SkinnedMeshRenderer.GetVertexBuffer` [M3]) need a refit-enabled BLAS. The Relay is not in the reflection today (skinned meshes are not scanned) |
| **Glass flag per piece** | The glass bit is per material, but it is set by whichever renderer first registers that material (`.cs:193–197`); a shared `Glass_Shard` on an untagged renderer loses the bit | Production: flag by material (Glass_Window, Glass_Edge, Glass_Shard, fracture-face) and put the window ID in the instance user ID. Until then, every piece renderer carries `FrontRoomsMetalGlassTarget` |
| **Submesh 0, Float32 positions** | Only submesh 0 is traced (`.cs:186`); meshes without Float32 positions are skipped (`.cs:176`) | Put faces and fracture faces in submesh 0 (or separate meshes); turn off position compression for these meshes |
| **Crack lines stay raster** | A fracture face is 6 mm deep and edge-on face-on; one ray per pixel (about 1.5 mm per pixel at 1 m, ESTIMATE) hits it unreliably and will shimmer. The bridge also has no transmission, so the total-internal-reflection look of a crack cannot come from RT | The glass shader draws the lines (§3.2 ranks 2–4, 10–12); RT supplies the facet reflections and per-shard reflections |
| **Compositing** | The prototype writes alpha 1 on glass pixels and blends after post (`.mm:302`, composite shader), which replaces the pixel, including the raster crack lines and the view through the glass | G14's planned path (the glass shader reads `_FR_GlassRTReflection` before transparents) is required before cracked glass can be judged in RT |

---

## 5. Open items / UNVERIFIED

- Glass-specific behaviour in Call of Duty, Battlefield, Max Payne 3, Rainbow Six Siege, Control, Hitman, F.E.A.R., Receiver 2, Ready or Not and Teardown: no official technical source found. The rows in §1.2 say what to check in footage.
- The glass-shading section of "The Technical Art of Uncharted 4" was not read (PDF over 10 MB).
- Whether the 1988-era UBC/BOCA hazardous-location rule (> 9 sq ft, < 18 in, > 36 in, walking surface within 36 in) already existed.
- The exact terminal crack speed in soda-lime glass (1.2 vs 1.5 km/s).
- The split between forward and backward glass when a window breaks; only the backward study's abstract was read.
- How often window cracks show iridescence; whether head teeth fall late.
- The soft-body crack pattern (§2.2) and the carpet behaviour (§2.3) are physical reasoning, not sourced.
- The NFPA 80 wired-glass size limit came from secondary sources (I Dig Hardware, Syracuse Glass via search results).
- The Commons photos below were identified from their metadata and were not viewed.
- My web search budget for this session ran out near the end. A few points (head teeth falling late, high-speed footage of window breaks) could not be sourced.

---

## 6. Sources

### Games, talks, official tech (read 2026-10-03 unless noted)

- **[G1]** Valve, Source SDK 2013: `src/game/server/func_breakablesurf.cpp` (+ `.h`), `src/game/client/c_func_breakablesurf.cpp`, `src/game/client/c_te_glassshatter.cpp`, `src/materialsystem/stdshaders/ShatteredGlass_EnvMap.psh`. https://github.com/ValveSoftware/source-sdk-2013 (read through the GitHub API into the scratchpad; summarised, not copied). The Valve Developer Community page https://developer.valvesoftware.com/wiki/Func_breakable_surf returned 403.
- **[G2]** 80.lv, "How Naughty Dog Created the Immersive World of The Last of Us Part II" (interview; glass tool told by technical artist Michael Fadollone, with Christophe Desse, Charlotte Francis, Jaroslav Sinecky, Neilan Naicker), 2020-12-08. https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/
- **[G3]** Waylon Brinck, Andrew Maximov (Naughty Dog), "The Technical Art of Uncharted 4", SIGGRAPH 2016. https://advances.realtimerendering.com/other/2016/naughty_dog (slides not read)
- **[G4]** Kenji Ono (CGWORLD), report on the CEDEC 2017 session 「壊れ物への取り組み いかにベイクを美しく魅せるか」, speaker 滝 崇海 (Capcom technical artist, Resident Evil 7). https://cgworld.jp/feature/201709-cedec2017-capcom.html and pages -2, -3, -4
- **[G5]** Ubisoft News, "The Art of Destruction in Rainbow Six Siege: an interview with Julien L'Heureux", 2016-03-11. https://news.ubisoft.com/en-us/article/4GHX2yepSaKkflLjLAlpwO/the-art-of-destruction-in-rainbow-six-siege-an-interview-with-julien-lheureux ; GDC 2016 session "The Art of Destruction in Rainbow Six: Siege", GDC Vault https://gdcvault.com/play/1023003/The-Art-of-Destruction-in (not watched)
- **[G6]** Rob Williams, "Mirror's Edge PC Version to Support PhysX", Techgage, 2008-11-19. https://techgage.com/news/mirrors_edge_pc_version_to_support_physx/ ; AnandTech, "Mirror's Edge: Do we have a winner?", 2009. https://www.anandtech.com/show/2745/12 (site unreachable; search summary only)
- **[G7]** Andrew Burnes, "Control Graphics and Performance Guide", NVIDIA, 2019-08-27. https://www.nvidia.com/en-gb/geforce/guides/control-graphics-and-performance-guide ; Johannes Richter (Remedy), "Destructible Environments in CONTROL: Lessons in Procedural Destruction", GDC Summer 2020 (80.lv announcement https://80.lv/articles/gdc-talk-destructible-environments-in-control ; schedule https://schedule.gdconf.com/session/destructible-environments-in-control-lessons-in-procedural-destruction/875640; not watched)
- **[G8]** EA / DICE, "How Battlefield 6 redefined destruction" (Rickard Antroia, Talan Le Geyt, Johan Leijon), 2025-11-10. https://www.ea.com/en/news/how-battlefield-6-redefined-destruction
- **[G9]** Robert Kihl (DICE), "Destruction Masking in Frostbite 2 using Volume Distance Fields", SIGGRAPH 2010 Advances in Real-Time Rendering. https://advances.realtimerendering.com/s2010/Kihl-Destruction%20in%20Frostbite(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf (search summary only)
- **[G10]** Dennis Gustafsson (Mediocre), "Cracking destruction", 2014-05-13. https://blog.voxagon.se/2014/05/13/cracking-destruction.html ; "Physics tutorial at GDC 2015" https://blog.voxagon.se/2015/02/20/physics-tutorial-at-gdc-2015.html (not read)
- **[G11]** Matthias Müller, Nuttapong Chentanez, Tae-Yong Kim (NVIDIA), "Real Time Dynamic Fracture with Volumetric Approximate Convex Decompositions", SIGGRAPH 2013. https://discmaster.textfiles.com/file/16678/SIGGRAPH%202013%20-%20Disc%203.iso/content/papers/115-0151.pdf (abstract via search)
- **[G12]** Epic Games, "Fracturing Geometry Collections User Guide" https://dev.epicgames.com/documentation/en-us/unreal-engine/fracturing-geometry-collections-user-guide ; "Destruction Quick Start" https://dev.epicgames.com/documentation/unreal-engine/destruction-quick-start ; John_CTS, "Chaos Destruction for Beginners – Realistic Fractures: Bullet Holes", Unreal Engine forums, 2026-08-17 (community) https://forums.unrealengine.com/t/community-tutorial-unreal-engine-5-8-1-chaos-destruction-for-beginners-realistic-fractures-bullet-holes/2744389
- **[G13]** BeamNG, "Glass Damage Textures" (modding docs). https://documentation.beamng.com/modding/vehicle/vehicle-art/texturing/glass-damage-textures/
- **[G14]** Teardown: https://en.wikipedia.org/wiki/Teardown_(video_game) ; community modding docs https://get-teardown.readthedocs.io/en/latest/mods/creating-your-own-assets.html (search summary)
- **[G15]** F.E.A.R.: https://en.wikipedia.org/wiki/F.E.A.R._(video_game)
- **[G16]** Rockstar, "Max Payne 3 Design and Technology Series: Visual Effects and Cinematics", 2012, via Gaming Nexus https://gamingnexus.com/News/25914/Max-Payne-3-shows-off-its-fancy-visual-effects-and-cinematics (not watched)
- **[G17]** "Visual Effects and Destruction in Call of Duty: Ghosts" (Infinity Ward), Vancouver ACM SIGGRAPH chapter, 2014-01-23. http://vancouver.siggraph.org/2014/01/02/visual-effects-and-destruction-in-call-of-duty-ghosts/ (unreachable; title and date from search)
- **[G18]** GamingBolt, "The Last of Us Part 2 – 20 Tiny But Amazing Details You May Have Missed". https://gamingbolt.com/the-last-of-us-part-2-20-tiny-but-amazing-details-you-may-have-missed/3 (search summary)
- **[G19]** 80.lv, "The Future of Destruction in Unreal" (GDC 2019; Matthias Worch, Jim Van Allen, Michael Lentine). https://80.lv/articles/the-future-of-destruction-in-unreal/ (search summary)

### Real glass: physics, standards, forensics

- **[P1]** Scientific Working Group for Materials Analysis (SWGMAT), "Glass Fractures", July 2004 (hosted by NIST). https://www.nist.gov/document/glassfracturespdf
- **[P2]** R. J. W. Luce, J. L. Buckle, I. McInnis (RCMP), "A study on the backward fragmentation of window glass and the transfer of glass fragments to individual's clothing", Can. Soc. Forensic Sci. J. 24(2):79–89, 1991. Abstract: https://www.ncjrs.gov/App/Publications/abstract.aspx?ID=132202 ; catalogue: https://britglass.org.uk/knowledge-base/digital-library-and-information-services/study-backward-fragmentation-window-glass
- **[P3]** J. Fineberg, M. Marder, "Instability in dynamic fracture", Physics Reports 313 (1999) 1–108. https://jay-fineberg.huji.ac.il/node/3202996
- **[P4]** University of Cambridge repository, high-speed photography of crack initiation and propagation in glasses. https://www.repository.cam.ac.uk/handle/1810/246968 (search summary; ~1200 m/s)
- **[P5]** Cardinal IG, Technical Service Bulletin IG24 "Insulating Glass Breakage", 12/2020. https://www.cardinalcorp.com/wp-content/uploads/2023/01/IG24_12-2020.pdf
- **[P6]** US CPSC, 16 CFR 1201 Safety Standard for Architectural Glazing Materials (1977), as summarised in Federal Register 81(56), 2016-03-23. https://www.govinfo.gov/content/pkg/FR-2016-03-23/html/2016-06523.htm
- **[P7]** 2021 International Residential Code R308.4.3, as reproduced by the City of Aberdeen (WA) safety-glazing tip sheet. https://www.aberdeenwa.gov/DocumentCenter/View/1964/Safety-Glazing-PDF
- **[P8]** NFPA 80 wired-glass lite limits (1296 sq in, 54 in): I Dig Hardware https://idighardware.com/?p=26463 ; Syracuse Glass, Polished Wired Glass product info https://syracuseglass.com/E-DOCS/Fire%20Rated%20Glass/EDOCS/Polished%20Wired%20Glass%20Product%20Info.pdf (both via search summaries)
- **[P9]** SAFTI FIRST, "Wired glass still a misunderstood product". https://safti.com/articles/wired-glass-still-a-misunderstood-product/ (search summary)
- **[P10]** Wikipedia: Wired glass https://en.wikipedia.org/wiki/Wired_glass ; Tempered glass https://en.wikipedia.org/wiki/Tempered_glass ; Float glass https://en.wikipedia.org/wiki/Float_glass ; Forensic glass analysis https://en.wikipedia.org/wiki/Forensic_glass_analysis ; Thin-film interference https://en.wikipedia.org/wiki/Thin-film_interference ; Newton's rings https://en.wikipedia.org/wiki/Newton%27s_rings
- **[P11]** LibreTexts, "Total internal reflection". https://phys.libretexts.org/Workbench/PhysClips_Light/02%3A_Geometrical_Optics/2.08%3A_Appendix/2.8.05%3A_Total_internal_reflection ; ScienceABC (popular science), "If glass is transparent, then why are its cracks opaque?" https://www.scienceabc.com/eyeopeners/if-glass-is-transparent-then-why-are-its-cracks-opaque.html
- **[P12]** EN 12150-1 fragmentation count (≥ 40 particles in 50 × 50 mm), via Glass Canada https://www.glasscanadamag.com/robot-counting-counting-the-fragments-in-tempered-glass-strength-tests/ (search summary)
- **[P13]** ASTM E1300 load duration (3 s; annealed load factor 1.0 at 3 s, 0.43 at 30 days), via Cardinal IG bulletin IG03 https://cardinalcorp.com/wp-content/uploads/2025/03/IG03_03-2025.pdf (search summary)
- **[P14]** R. A. Smith, C. A. Bernhardt (Sentrol), US 5,192,931 "Dual channel glass break detector", 1993. https://patents.google.com/patent/US5192931A/en
- **[P15]** G. Quinn, NIST Recommended Practice Guide: Fractography of Ceramics and Glasses (SP 960-16). https://www.nist.gov/publications/nist-recommended-practice-guide-fractography-ceramics-and-glasses-4th-edition (not read in full)
- **[P16]** Glass Technology Services, "6 glass breakage patterns and how to identify them". https://www.glass-ts.com/news/6-glass-breakage-patterns-and-how-to-identify-them/

### Metal and Unity

- **[M1]** Apple, `MTLAccelerationStructureCommandEncoder.refit(...)`. https://developer.apple.com/documentation/metal/mtlaccelerationstructurecommandencoder/refit(sourceaccelerationstructure:descriptor:destinationaccelerationstructure:scratchbuffer:scratchbufferoffset:options:)
- **[M2]** Apple, WWDC22 session 10105 "Maximize your Metal ray tracing performance". https://developer.apple.com/videos/play/wwdc2022/10105/ (transcript via https://nonstrict.eu/wwdcindex/wwdc2022/10105)
- **[M3]** Unity, `SkinnedMeshRenderer.GetVertexBuffer` (6000.3). https://docs.unity3d.com/6000.3/Documentation/ScriptReference/SkinnedMeshRenderer.GetVertexBuffer.html
- **[M4]** Unity, `Physics.DefaultRaycastLayers` (legacy 5.4 page; I assume the behaviour is unchanged in 6000.3). https://docs.unity3d.com/540/Documentation/ScriptReference/Physics.DefaultRaycastLayers.html

### Reference photos (Wikimedia Commons; licences from the file pages; not viewed, identified from metadata)

- Forensic radial and concentric fractures: https://commons.wikimedia.org/wiki/File:Glass_fracture_radial_concentric.jpg
- Broken house window (West Midlands Police, CC BY-SA 2.0): https://commons.wikimedia.org/wiki/File:Day_195_-_Shut_the_burglar_out_(9293361460).jpg
- Broken window (Helgi Halldórsson, CC BY-SA 2.0): https://commons.wikimedia.org/wiki/File:Broken_Window_(3512969871).jpg
- A window broken in two parts, a low-energy break (P.J.L. Laurens, CC BY-SA 3.0): https://commons.wikimedia.org/wiki/File:Broken_glas.JPG
- Broken window, Heimaey (Hannes Grobe, CC BY-SA 4.0): https://commons.wikimedia.org/wiki/File:Broek-window-on-heimaey_hg.jpg
- Cracked pane above an altar (geograph): https://commons.wikimedia.org/wiki/File:Cracked_pane_of_glass_above_the_altar_-_geograph.org.uk_-_7461197.jpg
- Tempered pane crazed in its frame (CC BY-SA 3.0): https://commons.wikimedia.org/wiki/File:Broken_Meat_Case_Window.JPG
- Tempered fragments (CC BY-SA 3.0): https://commons.wikimedia.org/wiki/File:Tempered_Glass.jpg
- Conchoidal fracture surface, obsidian (CC BY-SA 3.0): https://commons.wikimedia.org/wiki/File:Conchoidal.JPG
- Green colour of float glass: https://commons.wikimedia.org/wiki/File:Green_color_of_float_glass.jpg
- Period wired-glass styles, Pittsburgh Plate Glass catalogue: https://commons.wikimedia.org/wiki/File:Various_styles_of_wire_glass,_from_Glass_Paints_(p._141).jpg

### Project files read

Red's project (read only): `Documentation/research/interactables/00_map_constraints.md`, `06_period_windows.md`; `Documentation/research/interaction_audit/02_glass_and_breakables.md`, `FrontRoomsShotTimings.proposal.cs.txt`; `Documentation/research/glass/10_implementation.md`, `11_reflections_and_raytracing.md`, `20_verification.md`, `images/02_window_old_vs_new.jpg`, `images/03_window_close_masks.jpg`, `images/04_crack_palm_hooks.jpg`; `Documentation/research/glass/destruction/03_micro_cutscene_camera.md` (headings); `Documentation/VISUAL_CHAT_TASKS.md`; `NativePlugin/FrontRoomsMetalGlassRT.mm`, `build_frontrooms_metal_glass_rt.sh`; `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs`, `FrontRoomsMetalGlassRTRendererFeature.cs`; `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`; `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs` (pane build, RT hook, floor materials). Clone `proj_glass` (read only): `Assets/Resources/Rendering/FrontRoomsGlass.shader`. Tools on this Mac: Blender 4.3, Maya 2023/2025 (with Bifrost); no Houdini found in `/Applications`.
