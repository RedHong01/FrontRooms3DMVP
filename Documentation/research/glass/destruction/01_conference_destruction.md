# 01 — How shipped games build destructible environments (conference research, GD1)

Date: 2026-10-03. Status: COMPLETE. Research only. Nothing in the real project or in any clone was changed; this file is the only output.

Task: `Documentation/VISUAL_CHAT_TASKS.md` row **GD1** (Red: "the glass breaking looks fake … breakables are usually built as stage models and swapped stage by stage … research how destructible scenes are made, across developer conferences"). Also folded in, as Red asked: **ChatGPT's native Metal ray-tracing glass bridge** (what it does, and what fracture assets need from it), §7.

How to read the source tags:

| Tag | Meaning |
|---|---|
| **[SLIDES]** | I extracted and read the text of the speaker's own slide deck. |
| **[DOC]** | Official engine or vendor documentation. |
| **[TALK-DESC]** | Only the official session title and abstract were readable (GDC Vault page). Claims beyond the abstract are not made. |
| **[REPORT]** | A secondary write-up of a talk, or an interview with the developers (80 Level, Game Developer, CGWorld, fxguide, SideFX). |
| **[SURVEY]** | A survey by a non-developer (Game Maker's Toolkit). Used only as corroboration. |
| **UNVERIFIED** | I could not confirm it from a source I read. |

Full source list with URLs: §9.

---

## 0. Short answer (for Red)

1. **You are mostly right.** The most common shipped technique is: **break the object offline into pieces ("pre-fracture"), keep the intact version on screen, and swap to the broken version when damage crosses a threshold.** Battlefield: Bad Company 2, Control, Uncharted 4, Unreal's Chaos (its "root proxy" mesh is literally "render this intact mesh until the collection breaks"), NVIDIA APEX/Blast and The Finals all start from pre-fractured pieces made in a DCC tool (Houdini, Maya, PhysXLab).
2. **"One model per stage, swapped in order" is incomplete in four ways.**
   - **The stages are usually one hierarchy, not separate models.** The broken version is a tree of pieces glued by a connection graph. Damage releases pieces or clusters a few at a time (Chaos clusters and per-level damage thresholds, Blast bonds, Siege's leaf graph, The Finals' structural graph, Control's constraint-bonded hierarchies). A "stage" is which bonds have broken, not a different file.
   - **Early damage is mostly surface, not geometry.** Frostbite paints a destruction mask, Control uses decals for dents and cracks, Siege adds "decorations" (decal-like meshes) on cut edges. Geometry changes only when something actually comes apart.
   - **Every swap is dressed and covered.** Frostbite's recipe is four layers: remove the piece, add detail meshes around the hole, paint the mask, then add particles and mesh debris. Control fills the scale range from big rigid chunks down to dust. Red Faction managed camera shake and sound so big events did not drown. The swap itself is never what the player is meant to notice.
   - **Some games fracture at runtime, and set pieces are baked.** Siege cuts walls procedurally at runtime, and Smash Hit cuts glass where the ball lands. Teardown edits voxels. Big scripted moments are baked offline and played back: Uncharted 4 as joint animation, Halo 5 as geometry caches, Quantum Break as DMM playback, and many games as Vertex Animation Textures.
3. **Why our crack reads fake** (against these practices, §5): it is only a drawing on an unbroken plane. Nothing about the glass changes except thin bright lines. The reflection stays one perfect mirror across the cracks. No edge catches light, the impact point does not crush, and no piece moves. Then at 1.0 s the pane simply vanishes (`Kill(window.pane)`), with no shards, no teeth left in the stop, no floor glass and no dust. Shipped games do the opposite: the cracks are where real piece boundaries are, and the break leaves debris.
4. **Our window is a "choreographed hero break", not systemic destruction.** It is one pane, close to the camera, broken by a scripted 1 s hold with three fixed sound beats. The shipped analogue is the Uncharted / Control hero prop. That means a **pre-fractured hierarchy authored offline**, revealed in three beats (0.35 / 0.70 / 1.0 s), with edge detail, dust and glints, real falling pieces, teeth and floor glass, all synced with camera and sound. Runtime fracture is not needed for a first build. Siege's 2D planar cutter is the upgrade path if impact-point variety matters (§6).
5. **Geometry stages are also what ray tracing needs.** With ChatGPT's Metal bridge, a pre-fractured pane whose pieces tilt by fractions of a degree breaks its traced reflection into facets for free. A shader-only crack never can. §7 lists what the fracture asset needs for that: rigid pieces as separate instances, a BLAS built once per piece, and a TLAS rebuilt every frame. It also lists six defects I found by reading the bridge code, which should be fixed before production.

---

## 1. The approaches, in one table

| Approach | How pieces are made | How damage "stages" exist | Shipped examples (sources in §2) |
|---|---|---|---|
| **A. Pre-fracture + swap** | Offline in a DCC tool (Voronoi or hand cuts) | Intact mesh until a threshold, then the broken mesh | Bad Company 2, Control, Uncharted 4, UE root proxy |
| **B. Pre-fracture hierarchy + connection graph** | Offline, nested levels (chunks of chunks) | Bonds or clusters break one by one: strain or impulse vs threshold per level | Unreal Chaos, NVIDIA Blast/APEX, Siege (pre-fragmented part), The Finals, Red Faction: Guerrilla (stress) |
| **C. Surface masks / decals / decorations** | Textures or decal meshes, no new geometry | Mask or decal grows with damage | Frostbite destruction masking, Control decals, Siege decorations |
| **D. Runtime fracture** | Cut at runtime around the impact | Each hit cuts new pieces | Rainbow Six Siege (surface cutter), Smash Hit (glass), NVIDIA VACD research, The Division (press) |
| **E. Baked playback** | Simulated offline, played back | A timeline: frames, not states | Uncharted 4 (joint animation), Halo 5 (geometry cache), Quantum Break (DMM playback), VAT (Houdini Labs) |
| **F. Voxels** | The world is voxels | Voxels removed; disconnected islands become new bodies | Teardown |

Most shipped games mix these. Frostbite is A + C + debris. Siege is B for objects and D for walls, with pre-made debris. Control is A/B + C + particles. Uncharted is A + E.

---

## 2. Talk by talk

### 2.1 Frostbite: Bad Company, Battlefield 1943, Bad Company 2 → Frostbite 2 (DICE)

Source: *Destruction Masking in Frostbite 2 using Volume Distance Fields*, Robert Kihl (DICE), SIGGRAPH 2010 "Advances in Real-Time Rendering" course. **[SLIDES]**

- **The recipe, in order.** Destroying part of a house means:
  1. remove that piece of geometry;
  2. add detail meshes around the destroyed section;
  3. add the destruction mask (a texture effect on the surrounding surface);
  4. add particle effects and mesh debris.

  The same steps repeat for every further part the player breaks.
- **Stages.** The building is split into destructible *parts*. Each part's loss is the stage change; the mask is what makes the edge look broken.
- **Frostbite 1** (Bad Company, 1943, BC2) needed a hand-made UV map per destructible part for the mask. That was too slow, so Frostbite 2 moved the mask into a **volume distance field**. Artists place spheres where holes are; the distance field is low resolution (about 2 m per texel, typically 8×8×8 texels); a projected detail texture breaks up its shape.
- **Cost control.** The mask is drawn as a **deferred decal**, so only pixels inside its volume pay. On PS3 the triangles were pre-sorted on the SPUs into inside/outside index buffers instead of branching in the shader.
- **What made it read real:** the detail meshes and projected detail textures around the hole, and a second detail normal map on ceiling edges "to make them pop".

Corroboration **[SURVEY]**: Game Maker's Toolkit describes Bad Company 2 buildings as many prefabricated pieces, each with an intact and a destroyed version, swapped once damage is high enough. A fan wiki says a BC2 building plays its collapse once about 26 parts are broken (**UNVERIFIED**, fan source).

Later Battlefields: *Battlefield 4: Creating a More Dynamic Battlefield*, Linnea Harrison (DICE), GDC 2014, covers "destruction, levolution and dynamic weather" **[TALK-DESC]**. Press describes Levolution events (the Shanghai skyscraper) as scripted set pieces the player triggers (**UNVERIFIED** from a primary source). In 2011 DICE said it deliberately reduced full-building destruction in BF3, because long matches ground maps flat and hurt defenders **[REPORT, mp1st]**. I found no technical talk on Battlefield 1 / V destruction (**UNVERIFIED**; press only).

### 2.2 Rainbow Six Siege: RealBlast (Ubisoft Montreal)

Source: *The Art of Destruction in Rainbow Six: Siege*, Julien L'Heureux (Ubisoft), GDC 2016. **[SLIDES]**, plus the Ubisoft interview (2016) **[REPORT]**.

- **Definitions used in the talk.** *Procedural* destruction is a state change generated at runtime with a unique outcome. *Pre-fragmented* destruction is pre-determined, with a fixed outcome. RealBlast does both. It first shipped in Assassin's Creed IV: Black Flag.
- **Model.** Objects are split by physical material: separate drywall, wood and so on, which the talk says should drive how assets are modelled. Pieces sit in a **hierarchical decomposition** with a **connection-based leaf graph**. The game acts on connections, and the graph tracks state. A leaf can be flagged procedural, so it can be cut further at runtime.
- **Surface cutter (Siege only).** A wall layer is projected to 2D. A cut pattern is generated from the impact position and the material's "cutter" (random ellipse, spline, Voronoi, or a texture-defined motif; **glass is one of the cutter classes**, and a "procedural glass prototype" is shown). The pattern is clipped against the surface polygons, ear-clipped, then extruded back to 3D.
- **Making it look real.** Instead of GPU decals, Siege uses **decorations**: actual geometry. "Cut decorations" are decal-like planar meshes cut along with the surface. "Feature-bound decorations" sit on edges and vertices, can stick out, and disappear when their feature is gone.
- **Debris (the important budget choice):** no procedurally cut dynamic fragments at all. Debris are **well-placed pre-made replacements**, instanced and **recycled aggressively**, with fragments vaporised in explosions and box-only collision.
- **Budgets.** About 6 ms per wall (two procedural layers plus pre-fragmented parts), 25 MB GPU memory, 200 MB data plus 150 MB engine RAM. Example PC timings: one bullet hole 0.33 ms; an explosion through 2 drywall + 2 wood layers 8.1 ms (about 19–20 ms on PS4/XB1).
- **Hiding the cost.** Destruction runs **asynchronously and time-sliced**. The "pre-destruction" trick computes the destruction in advance and reveals it at the end of an animation. The RNG is seeded by impact position, for determinism across the network.

### 2.3 THE FINALS (Embark Studios)

Sources: *Engineering Mayhem: Technical Deep-Dive into Environmental Destruction in THE FINALS*, Måns Isaksson (Embark), GDC 2024 **[SLIDES; some slides are image-only]**. *Making the Procedural Buildings of THE FINALS using Houdini*, Adrian Björkerud (Embark), SideFX, 2026 **[REPORT]**.

- **Authoring.** Buildings are assembled from modular Houdini "Feature Nodes", then **pre-fractured in Houdini**. The input must be watertight so interior faces generate cleanly. Iteration takes about 4–6 minutes from blockout to fractured asset. Collision hulls come automatically from a 2D convex decomposition. 100+ buildings shipped this way.
- **Connections.** A tool generates the connection graph (parts "standing on supportive ground") and shows every connection in the level editor.
- **Structural analysis.** Embark's own rigid-body solver is a sparse direct solver (incremental Cholesky). Each connection's force is split into tension/compression, shearing and bending, each scaled by a per-material multiplier. A connection breaks when the combined impulse exceeds its baseline plus an offset. The talk credits Bad Company and Red Faction: Guerrilla as its models.
- **Network and rendering.** A large destruction event averaged about 400 kbit/s of transforms. Quantisation plus delta compression brought the peak to about 175 kbit/s. Rendering uses a **GPU transform pool** for the many moving parts, with separate sections on lighting, **edge meshes** and VFX (those slides are images; details **UNVERIFIED**).

### 2.4 Control (Remedy, Northlight)

Source: *Destructible Environments in CONTROL: Lessons in Procedural Destruction*, Johannes Richter (Remedy), GDC Summer 2020 **[TALK-DESC + REPORT]**. Details from the CGWorld (Japan) write-up and the Game Developer write-up. I did not read the slides.

- **Granularity is the principle.** Nature is a continuum from huge objects down to dust and smoke, so the effect covers every scale:
  - large: rigid-body chunks and props;
  - middle: mesh particles, rigid-body hierarchies and decals;
  - fine: sparks, dust, splinters and smoke as sprites and particles.
- **Material-driven, rule-based.** Every object carries metadata saying what it is made of. Rules decide what it spawns: concrete breaks into concrete bits plus dust. A small VFX team could not hand-make hundreds of breakables, so a single Houdini HDA processed them all; it was updated about 20 times over two years. Pre-fractured fragments are bonded by constraints into object hierarchies.
- **Budgets.** At most about 200 active rigid bodies on screen. Off-screen debris is removed immediately. Large blasts get collision delays and temporary deactivation, and pieces bounce less than in reality. Particles and decals carry the visual density instead of physics.
- **Stages and covering the swap [SURVEY].** Game Maker's Toolkit describes Control as holding an intact and a broken version, swapping on attack, and playing a particle effect to cover the swap. That fits the CGWorld account.
- **What made it read real:** the full scale range, material-specific responses, and hand-made extras on top of the system (sparking computers, spinning whiteboards).

### 2.5 Red Faction: Guerrilla (Volition, GeoMod 2.0)

Sources: *Destruction of Design*, Luke Schneider (Volition), GDC 2009, reported by Game Developer **[REPORT]**. Eric Arnold (Volition) Q&A, CBS News 2009 **[REPORT]**. Game Maker's Toolkit 2025 **[SURVEY]**. **I could not find the GDC 2010 Guerrilla talk named in the brief (UNVERIFIED).** GDC Vault lists *Multiplayer Level Design in Red Faction Guerrilla* (Luke Schneider) and an audio talk for Armageddon.

- **Stress, not CSG.** The first Red Faction carved terrain with real-time booleans (Erwin Coumans' overview, §2.13). In Guerrilla, buildings are made of destructible parts with mass and strength. When the support under a load fails, the parts above become physics objects **[SURVEY]**. Schneider's line was "stress is stressful": without good stress maths, collapses look wrong.
- **What made it read real:** creaks as weight shifts, floors buckling before collapse, rendered insides of walls, and **rebar added late in development** because concrete looked fake without it. The team also visited a hotel demolition **[REPORT, Arnold]**.
- **Hiding and dosing.** The team worked hard on sound and camera shake during destruction. They switched sounds and camera movement **off** when the engine would otherwise fire too many at once **[REPORT, Schneider]**.

### 2.6 Unreal Engine: Chaos Destruction (Epic)

Sources: *State of Unreal*, GDC 2019 (Chaos demo in the Robo Recall world) **[REPORT]**. *Causing Chaos: Physics and Destruction in Unreal Engine*, Michael Lentine and Jim Van Allen, SIGGRAPH 2019 Real-Time Live! **[TALK-DESC]**. *Dynamic Destruction in UE5 with the Chaos Destruction System*, Jim Van Allen and Cedric Caillaud (Epic), GDC 2025 **[TALK-DESC]**. Epic's destruction overview and the GeometryCollection Python API **[DOC]**.

- **Pieces.** A **Geometry Collection** is made from static or skeletal meshes, then fractured (for example uniform Voronoi) in Fracture Mode. The source must be watertight and non-intersecting. Each material is duplicated so interior (cut) faces get their own material.
- **Stages = cluster levels.** Pieces are grouped into a cluster tree. A **connection graph** of nearest neighbours carries strain values. A connection breaks when collision or a field applies more impulse than its limit. The **damage threshold is an array, one value per cluster level**, optionally size-specific instead. `max_cluster_level` limits how deep breaking goes.
- **The intact stage is a separate mesh.** `root_proxy_data` is a static mesh rendered *until the collection is broken*. That is Red's "stage model" exactly, built into the engine.
- **Hiding and lifetimes.** Niagara and audio hook into break events. Fields (anchor, strain, disable, sleep) script the result. `remove_on_max_sleep` dissolves pieces after a set sleep time, `removal_duration` sets how long that takes, and `scale_on_removal` shrinks them on the way out (on by default). A **cache system** replays heavy simulations at runtime.
- **GDC 2025** adds break and shock propagation and Niagara Data Channels for gameplay **[TALK-DESC]**.

### 2.7 NVIDIA APEX Destruction and Blast

Sources: *NVIDIA APEX: From Mirror's Edge to Pervasive Cinematic Destruction*, Anders Caspersson (DICE) with Monier Maher and Jean Pierre Bordes (NVIDIA), GDC 2009 **[SLIDES]**. *Authoring Physically Simulated Destruction with NVIDIA APEX*, Bryan Galdrikian and Dane Johnston, GDC 2010 **[SLIDES]**. NVIDIA Blast SDK documentation **[DOC]**.

- APEX authoring was offline: mesh plus fracture map into PhysXLab. It covered "chippables" (cutout fracturing), slicing, and a Batman: Arkham Asylum workflow in Unreal Engine 3.
- **Mirror's Edge PC** added its PhysX glass destruction in about 5 weeks as **mesh and sprite particles** with full physical interaction. Each asset was lit individually so it matched the static lighting.
- **Blast** (the successor) has chunk hierarchies: a fractured chunk spawns its children. Any chunks can be tagged "support". **Bonds** (centroid, normal, area) join support chunks, and user "damage shader" functions weaken bonds. Hierarchy depth is the stage system.

### 2.8 Naughty Dog: Uncharted 4, The Last of Us Part II

Sources: *FX Adventures in Uncharted 4*, interview with Neilan Naicker and Raymond Popka, SideFX / 80 Level, June 2016 **[REPORT]**. *How Naughty Dog Created the Immersive World of The Last of Us Part II*, 80 Level, December 2020 **[REPORT]**. *Technical Art Techniques of Naughty Dog: Vertex Shaders and Beyond*, Andrew Maximov, GDC 2017 **[TALK-DESC]**.

- **Two kinds of fracture.** Near the camera, or where pieces must match the texture, pieces were **cut by hand in Maya**. For larger or more distant work, a Houdini HDA did clustered fracture and added edge detail efficiently.
- **Baked playback.** Most hero destruction was simulated in Houdini and **exported as joint animation** through Maya.
- **Hand-off.** A rope-bridge collapse switches from baked animation to real-time physics halfway. The bake had to end on exact poses and velocities.
- **TLOU2 breakable glass** was a small team effort:
  - an initial glass tool;
  - a process that builds **shards from textures**;
  - a **fractal glass shader**;
  - Havok tuning;
  - one authoring tool that wrapped them all.

  Glass breaks differently by weapon, and broken glass crunches underfoot.

### 2.9 Baked playback: Quantum Break, Halo 5, Vertex Animation Textures

- **Quantum Break** (Remedy). *Time for destruction: the tech of Quantum Break*, fxguide, April 2016, interviewing Remedy staff **[REPORT]**.
  - Soft deformation was **DMM**: finite-element simulations baked offline and played back, forwards, backwards and stuttering.
  - Rigid destruction was Thinking Particles (the train crash was about 5,000 objects). Real-time physics was Havok.
  - Geometry was pre-fractured only where needed, to keep the debris count finite.
- **Halo 5.** *Geometry Caching Optimizations*, Zabir Hoque and Ben Laidlaw (343 / Microsoft / Epic), GDC 2017 **[TALK-DESC]**. The abstract compares geometry caches to motion capture for environments: complex destruction is baked into a playable format.
- **VAT.** SideFX Labs *Vertex Animation Textures 3.0* **[DOC]** has Soft, **Rigid**, Fluid and Sprite modes. Rigid mode stores each piece's pivot and rotation per frame in textures, and a vertex shader moves the pieces. It ships shader packages for Unity and Unreal. The CPU sees a static mesh, so it is very cheap. Game Developer's 2023 VAT article (Oleksandr Horiuk) shows it on the game Gord **[REPORT]**.
- **Houdini cleanup for real-time** (Paul Ambrosiussen, SideFX tutorial, 2017) **[REPORT]**: merging constrained islands and freezing still pieces cut one example from 2,000 to 59 packed pieces (97%).
- *Visual Effects Bootcamp: Sorting Through the Rubble*, Fred Hooper (NVIDIA), GDC 2019 **[TALK-DESC]**, frames the range from **choreographed event destruction** to dynamic real-time destruction. Our window sits at the choreographed end.

### 2.10 Runtime fracture: Smash Hit (glass), NVIDIA VACD, The Division

- **Smash Hit** (Mediocre). Dennis Gustafsson (later the Teardown author) spoke on the Smash Hit fracture algorithm at GDC 2015, inside the *Physics for Game Programmers* tutorial **[REPORT, his blog]**. His 2014 post *Cracking destruction* gives the details.
  - Pre-made breaks that look the same every time were not enough for the game.
  - Objects always break **where they are hit**. Around the impact, slightly randomised planes carve out a small volume, which splits into several new dynamic pieces.
  - Breaking happens **inside** the physics step with capped impulses (up to three passes), so pieces keep some of the motion.
  - Vertex normals are carried through the splits to keep the glass shading soft.
- **NVIDIA VACD.** *Real Time Dynamic Fracture with Volumetric Approximate Convex Decompositions*, Müller, Chentanez and Kim, SIGGRAPH 2013 (ACM TOG). Also shown at SIGGRAPH 2013 Real-Time Live! as *Massive Destruction in Real Time* **[DOC/REPORT]**. Impact-dependent fracture patterns are applied at runtime. The demo split a 1M-vertex arena into 20,000 pieces at over 30 fps, including dust and rendering. The RTL description sets it explicitly against the pre-fracturing then common in games.
- **The Division** (Massive, Snowdrop). Massive told the press its destruction is procedural and not pre-baked **[PRESS; no technical talk found, UNVERIFIED]**.

### 2.11 Voxels: Teardown (Tuxedo Labs)

Source: *Teardown Frame Teardown*, Steven Wittens (acko.net), January 2023 **[REPORT, frame analysis]**. Game Maker's Toolkit 2025 **[SURVEY]**.

- Each object is a 3D volume texture: one byte per voxel, with a 256-entry palette. It is drawn by ray-marching inside its bounding box.
- Destruction removes voxels. **Disconnected chunks become new objects**, recursively.
- Transparency (glass) is drawn screen-door style with blue noise.
- Everything is breakable at one granularity. Gustafsson's design remark (via GMTK): full destructibility is great for players and a nightmare for designers.

### 2.12 Source engine: staged glass (Valve)

Source: Valve Developer Wiki, `func_breakable_surf` **[DOC; the page returned 403 to my fetcher, so this is from the indexed summary: UNVERIFIED in detail]**.

- A planar glass or tile surface that breaks into **increasingly smaller fragments as it takes damage**. By contrast, `func_breakable` breaks all at once.
- It is the classic **staged** pane: progressive partial breakage, driven by special breakable glass materials on four-sided faces.

### 2.13 Overviews

- *Opinion: Destruction*, Erwin Coumans (AMD; author of Bullet), Game Developer, 2011 **[REPORT]**.
  - Offline preparation: Voronoi, tetrahedralisation, booleans, hand cuts.
  - Runtime: real-time booleans (Red Faction's original GeoMod), finite elements (DMM in Star Wars), composite rigid bodies glued with breakable links (union-find to detect separated parts), and breakable fixed constraints.
- *How Games Do Destruction*, Mark Brown (Game Maker's Toolkit), October 2025 **[SURVEY]**. Swap-based (Bad Company 2, Control), slicing (Siege, Astro Bot), soft body (BeamNG), grids (Far Cry 2 fire), voxels (Minecraft, Teardown), stress (Red Faction: Guerrilla, The Finals).

### 2.14 Searched, nothing verifiable found

- Insomniac destruction talk.
- Digital Dragons, Nordic Game and Unite sessions on destruction.
- A technical talk on Battlefield 1 / V destruction.
- A primary source for Levolution's internals.
- The "GDC 2010 Red Faction: Guerrilla" talk.

All **UNVERIFIED / not found**. I did not substitute guesses.

---

## 3. Cross-cutting: stages, hiding, debris, budgets, realism

| Game / system | Stages represented by | Swap hidden by | Debris | Budgets and lifetimes (as stated) | What sold it |
|---|---|---|---|---|---|
| Frostbite 1/2 | Destructible parts removed; mask grows | Detail meshes at the hole, mask, particles, mesh debris | Mesh debris + particles | Low-res distance field (~2 m/texel, 8³); deferred decal only where needed | Detail meshes and projected detail textures at broken edges |
| Siege | Leaf graph + runtime cuts per layer | Async + time-slicing; pre-destruction revealed at animation end | **No** cut debris: pre-made replacements, instanced, recycled, box collision | ~6 ms/wall; 25 MB GPU; 0.33 ms per bullet hole (PC) | Material layers; cut and edge "decorations" |
| The Finals | Connection graph + structural analysis | Edge meshes, VFX, lighting (slides image-only) | Fully simulated server-side; GPU transform pool | ~175 kbit/s peak after compression | Believable structural failure; debris that reshapes play |
| Control | Pre-fractured hierarchies bonded by constraints; intact→broken swap | Particles at the swap; decals | Big chunks as rigid bodies; mid-size as mesh particles; fine as sprites | ≤ ~200 active rigid bodies; off-screen removal; fewer bounces | Granularity across all scales; material rules |
| Red Faction: Guerrilla | Parts + stress | Creaks; managed shake and sound | Physics chunks | Separate large and small destruction calculations (Schneider) | Stress, creaks, rebar, wall interiors |
| Unreal Chaos | Cluster levels; per-level damage thresholds; root proxy until broken | Niagara + audio events; fields | Rigid pieces; cache playback | Remove-on-sleep timer; removal duration; shrink-on-removal | Strain and connection graph |
| Uncharted 4 | Baked sims (joints); hand-off to physics | Choreography | Baked, then real-time | (not stated) | Hand-cut pieces matching the texture near camera; edge detail |
| Quantum Break | Baked DMM + Thinking Particles playback | Choreography | Baked | Finite debris; DMM avoided where tetra counts hit memory | Large-scale sims played back |
| Smash Hit | Runtime cuts at each impact | Breaks inside the physics step, keeping motion | Every cut piece is dynamic | Capped impulses, ≤ 3 passes | Breaks exactly where hit |
| Teardown | Voxel removal | n/a | Disconnected chunks become bodies | (not stated) | Everything breaks the same way |
| Source glass | Progressive partial breakage of a pane | — | Fragments | — | Gets smaller with each hit |

**Patterns that hold across almost all of them:**
1. Pieces are authored offline wherever the shot can be art-directed.
2. Damage state lives in a graph of bonds, not in a list of models.
3. Small-scale damage is surface work: mask, decal or decoration.
4. Edges get extra detail.
5. Debris is pooled, capped, put to sleep and removed or frozen.
6. Particles and sound cover the instant of change.
7. Camera and sound are rationed so big events stay readable.

---

## 4. Red's hypothesis, answered directly

> "Breakables are usually made by building the different stages as models in advance and swapping stage by stage."

| Part of the hypothesis | Verdict | Evidence |
|---|---|---|
| Broken pieces are built in advance (offline) | **Right**, for most shipped games | Frostbite parts; Control HDA; Uncharted hand cuts and Houdini; The Finals Houdini pre-fracture; Chaos Geometry Collections; APEX/Blast; Siege's pre-fragmented objects and debris |
| The intact look is a separate model, swapped on the break | **Right** | Chaos `root_proxy_data` (intact mesh until broken); Bad Company 2 and Control intact/destroyed pairs [SURVEY] |
| Several stage models swapped in sequence | **Incomplete.** The usual form is *one* fractured hierarchy whose bonds or clusters release progressively. "Stage n" is a cluster level or a set of broken bonds, not a new file | Chaos per-level damage thresholds; Blast bonds and support chunks; Siege leaf graph; The Finals graph; Control constraint hierarchies; Source glass breaking into smaller fragments per hit |
| Early stages are geometry | **Usually not.** Cracks, dents and scorches are masks, decals or decal meshes until something actually separates | Frostbite mask; Control decals; Siege cut decorations |
| The swap alone makes it believable | **No.** Every source dresses the swap: edge or detail meshes, interior faces, particles, debris, sound, camera | Frostbite four-step recipe; Control granularity; Siege decorations; Red Faction rebar, creaks and managed shake; Uncharted edge detail; The Finals edge meshes |
| It is the *only* way | **No.** Runtime fracture (Siege walls, Smash Hit glass, VACD), voxels (Teardown) and baked playback (Uncharted, Halo 5, Quantum Break, VAT) all shipped | §2.2, §2.9–2.11 |

**One line for Red:** yes, pre-built and swapped, but as a *hierarchy of pieces* that comes apart in steps. The early steps are drawn on the surface, and every step is covered by edge detail, debris, particles, sound and camera.

---

## 5. Why the current FrontRooms crack reads fake, against these practices

Read from the glass shader in `proj_glass` (`Assets/Resources/Rendering/FrontRoomsGlass.shader:24-27, 219-264, 319-342`), the images `glass/images/03_*`/`04_*`, and `interactables/06_period_windows.md` §1.1.

| What the game does now | What shipped games do |
|---|---|
| `_Crack` grows radial lines and three ring sets continuously from `_ImpactUV`. Lines are bright and uniform in width (03/04 images). | Cracks are boundaries between real pieces. They show because light catches fracture edges and reflections jump across them, not as painted lines (Siege decorations on edges; Uncharted edge detail; Frostbite detail meshes). |
| The pane stays one plane. The per-wedge `tilt` (at most about ±0.03, `h * 0.06` with `h` in ±0.5) only nudges the shader normal, so a planar or RT reflection stays one unbroken mirror. | Pieces are separate geometry with their own normals. Tiny tilts break reflections into facets (§7). |
| The crush zone is a smoothstep disc of the same lines. | Impact crushing is either a decal/mask layer (Frostbite, Control) or a cluster of tiny pieces (Smash Hit carves a small volume at the hit). |
| At 1.0 s, `Kill(window.pane)` deletes the pane: no shards, teeth, floor glass or dust (06 §1.1). | Debris, remnants and dust are what make the event (all sources). The pane's perimeter normally stays in the stop as "teeth". |
| Continuous growth driven by hold progress. | Stages are discrete events (bond breaks), each tied to a sound and VFX hit (Frostbite, Control, Red Faction). Our three sound beats are exactly the right skeleton. |

---

## 6. What this means for the FrontRooms window (input for `10_glass_destruction_plan.md`)

These are **proposals** derived from §2–4, not decisions. Numbers marked PROPOSAL are mine, not from a source.

**6.1 Pick the shipped pattern that matches the shot.** Use the choreographed hero break (Uncharted / Control prop) built on a pre-fracture hierarchy (Chaos/Blast style): an intact proxy, then one fractured pane whose pieces release in steps.

**6.2 Map the stages to the beats that already exist.**

| Beat | Stage (PROPOSAL) | Representation | Cover |
|---|---|---|---|
| 0–0.35 s hold | S0 intact | Intact pane (root proxy) + palm smudge (existing `_Palm`) | Lean / FOV push (camera chat) |
| **Crack1 0.35 s** | S1 first cracks | Swap the intact proxy for the fractured pane, all pieces still in place. Reveal **level-1 piece edges** (radial wedges from the impact) as edge rendering. Per-piece tilt ≤ ~0.3° so reflections split. A crush decal or tiny-piece cluster at the hit | Crack1 sound, small shake, a puff of glass dust and glints at the hit |
| **Crack2 0.70 s** | S2 rings | Reveal **level-2 edges** (concentric breaks); tilts grow; 2–6 chips fall from the crush zone (pooled) | Crack2 sound, shake, glints |
| **Shatter 1.0 s** | S3 break | Release the inner clusters: pieces fall away from the push. Perimeter teeth stay in the glazing stop; a few drop late (0.2–0.8 s, PROPOSAL). Floor glass lands; dust | Shatter sound, FOV punch, dust and glints |
| After | S4 settled | Pieces freeze when still (the proposal's `SettleToStatic` 1.5 s) and stay as floor glass. Freeze, don't shrink: the window stays broken | — |

**6.3 Authoring (Blender; no Houdini on this Mac).** `mdfind` finds no Houdini install; Blender 4.3 is at `/Applications/Blender.app`, and the Cell Fracture add-on is **not** installed (it became an extension in 4.2+). Options:
- a scripted Voronoi or plane-cut fracture in `kitlib` (bmesh bisect per cell), with cells graded fine near the impact and coarse at the edges;
- hand-tuned cuts for the hero variant, as Naughty Dog did near camera.

Either way, each piece carries:
- its **level** (1 radial, 2 ring, 3 crush);
- **teeth vs free**;
- **edge-face** marking, for the edge shader.

Use impact-zone variants (for example a 3×3 grid × 2 seeds, PROPOSAL), chosen from the E-ray hit on the pane.

**6.4 Upgrade path: a Siege-style runtime planar cutter.** The pane is a flat surface, exactly what Siege's 2D cutter was built for. Glass was one of its cutter classes. Using Siege's "pre-destruction" idea, the cut can be computed while the player holds E (the impact point is known at hold start) and revealed at Crack1. Leave this for later; offline variants are more art-directable and match Red's intuition.

**6.5 Budgets (PROPOSAL, from Siege, Control and Chaos practice).**
- 60–120 pieces per pane variant.
- At most about 64 dynamic pieces at once per window; chips and dust come from a pool, Siege-style.
- Pieces freeze to static after landing.
- No physics collider that the E ray, the Relay's sight ray or its nav probe can hit. Pieces either have no collider or a collider on Ignore Raycast that only touches the floor. Report 04 owns the Unity details.
- The opening (1.4 × 0.35–2.0) must be clear after the break. Teeth must stay inside the stop's rebate, or fall when the climb starts.

**6.6 Cross-check for report 02 (period glass): this matters for the stages.** The FrontRooms pane meets every condition of today's "hazardous location" safety-glazing rule:
- bottom edge 0.35 m (< 18 in);
- pane area 2.31 m² (> 9 ft²);
- top edge 2.0 m (> 36 in);
- a walking surface on both sides.

Federal safety-glazing rules (CPSC 16 CFR 1201) date from 1977. So a code-compliant 1990 pane might have been **tempered** (dices all at once into small cubes, with no radial-crack stages), **laminated** (cracks into a web but stays in one sagging sheet) or **wired** (cracks but hangs on the wire). Ordinary annealed glass gives the long shards and radial plus concentric cracks that our three beats imply.

The exact 1990 model-code wording, and whether interior relites fell under it, are **UNVERIFIED** here. This is a design choice Red should see in report 02 or the plan: "period by code" vs "reads best for a 3-beat hold".

---

## 7. ChatGPT's Metal ray-tracing glass bridge: what it does and what fracture needs

**Files read** (real project, read-only):
- `NativePlugin/FrontRoomsMetalGlassRT.mm` (763 lines) and `NativePlugin/build_frontrooms_metal_glass_rt.sh`;
- `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs` (394);
- `Assets/Scripts/Rendering/FrontRoomsMetalGlassRTRendererFeature.cs` (34);
- `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`;
- the hooks in `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:346-347, 1043-1049`.

The built `Assets/Plugins/macOS/libFrontRoomsMetalGlassRT.dylib` exists (75 KB, 2026-10-03 01:11).

**Nothing was run.** Everything below is from reading the code.

### 7.1 What it does (plain English)

- **Why it can exist at all.** Report 11 measured that *Unity* reports no ray tracing on Metal. But the M3 family GPU has hardware ray tracing (Apple, Oct 2023), so the bridge skips Unity's API. It asks Metal directly (`MTLDevice.supportsRaytracing`) and builds Metal acceleration structures itself, from Unity's own vertex and index buffers (`GetNativeVertexBufferPtr`). That is a real way past report 11's "not possible", on Macs with M3 or newer only.
- **Scene registration** (`.cs:117-227`). Once a second (`rescanSeconds = 1`), the controller:
  1. finds the nearest pane tagged `FrontRoomsMetalGlassTarget`;
  2. collects every enabled `MeshRenderer` within 18 m of it, plus every tagged pane anywhere, up to 256;
  3. **clears the native scene** (`FRGlassRT_Reset`);
  4. builds **one BLAS per unique mesh** and **one TLAS instance per renderer**, with a material record per material. Bit 0 = glass, set when the renderer has the tag.
- **Per frame** (`.cs:229-246`, `.mm:245-303`), a compute kernel:
  1. traces a **primary ray per pixel from the camera into its own TLAS**;
  2. if the first hit is flagged glass, reflects once and traces again;
  3. shades the second hit with a flat colour, a fixed "sun" and a sky gradient;
  4. applies a Fresnel term;
  5. writes RGBA (non-glass pixels get alpha 0).

  A URP renderer feature then blends that texture over the frame after post-processing.
- **Fallbacks.** It runs only on macOS editor or player (`.cs:76-78`), and only where the standalone map scene creates it (`MapWorld:346-347`). Without the dylib or RT support it stays inert, and the URP glass shows as before.

### 7.2 What fractured glass needs from it

| Need | Why | What the asset or bridge must do |
|---|---|---|
| **Pieces are separate rigid instances** | The kernel takes per-triangle *geometric* normals from the BLAS (`.mm:214-221, 282`). A piece that tilts 0.3° reflects a different part of the room, so the reflection breaks into facets for free. A shader-only crack never changes the traced normal | Each moving piece is its own renderer (one TLAS instance). Teeth that never move can be merged into one mesh per window after the break |
| **BLAS: build once, never refit for rigid pieces** | Apple's guidance (WWDC22, WWDC23): build primitive structures at load, **refit only deforming meshes**, rebuild the **instance** structure every frame (cheap at a few thousand instances). Rigid motion is only a transform change | Build the BLAS for every piece of a fracture variant once, when the variant is first used; pool it. Per frame, rebuild the TLAS with new transforms only. Refit is needed only for bent or deformed pieces: compute writes positions, then refit |
| **No VAT for traced pieces** | The BLAS reads the mesh's static vertex buffer. VAT moves vertices in the vertex shader, which the ray tracer never sees, so traced reflections would show pieces at rest | Move traced pieces by transforms (rigid bodies or baked transform curves). VAT is fine for untraced dust and chips |
| **Per-frame transforms** | Today transforms are captured only at the 1 s rescan (`.cs:201-209`). Anything that moves — a falling shard, an opening door, the Relay — is traced up to 1 s out of date | Add a light per-frame path: update instance transforms and rebuild the TLAS each frame. Keep BLAS across frames instead of `Reset` + rebuild |
| **Piece count vs cap** | One cap of 256 covers meshes *and* instances (`kMaxInstances`, `.mm:32, 693, 731`), shared with the whole room within 18 m. The selection loop stops at 256 in InstanceID order (`.cs:145-157`), so a window's pieces can be **silently dropped** | Register the active window's pieces first. Cap traced pieces at about 64 per window (PROPOSAL); dust, chips and floor glass are URP-only. Raise the cap or use the instance mask (WWDC23) to keep small debris out of reflection rays |
| **Glass flag per piece** | The flag is per *material*, set by whichever renderer registers that material first (`.cs:192-199`) | Give every piece the `FrontRoomsMetalGlassTarget` tag, and give pieces a dedicated shard material that nothing else uses |
| **Mesh format** | Only Float32×3 positions and triangle topology are accepted (`.cs:176-179`), and **only submesh 0** is registered (`.cs:186-187`) | No vertex compression on piece meshes. Put face and edge triangles in one submesh, and mark edges by vertex colour or UV for the raster shader, or extend the bridge to several geometry descriptors |
| **Closed 6 mm pieces** | The kernel flips normals to face the ray and offsets 2 mm (`.mm:283-288`) | Pieces are closed slabs (two faces + edge strip), flat-shaded normals |

### 7.3 Defects found by reading the code (fix before production)

1. **Wrong field of view in the traced rays.** The managed side writes `camera.fieldOfView` in radians into the field the kernel reads as `tanFovY` (`.cs:378` → `.mm:75, 264-265`). It should be `tan(fov/2)`. At 60° that is 1.047 instead of 0.577, so traced rays fan out about 1.8× wider than the raster image, and the RT glass would not line up with the raster glass. (The vertical orientation of the result also needs checking in a capture.)
2. **One blank frame every second.** Each rescan sets `reset`, and the kernel then writes zeros and returns (`.cs:218, 242-244`; `.mm:258`). The traced reflection would blink off for one frame per second.
3. **Glass pixels are overwritten, not added to.** The kernel writes alpha 1, and the composite blends `SrcAlpha OneMinusSrcAlpha` with alpha = strength (1). Each glass pixel is *replaced* by a dim reflection, so whatever is seen through the glass disappears. A reflection term should be added on top of the glass (or the glass shader should read it). The pass also runs **after post-processing** (`RendererFeature:17`), so the reflection skips tonemapping and bloom.
4. **"Is this pixel glass?" is decided by the ray tracer's own scene, not by what was drawn.** Anything not in the TLAS (skinned meshes, objects beyond 18 m) or out of date (moved within the last second) can be painted over by the reflection. That includes the Relay standing in front of a window. Production should start reflection rays from the raster's glass pixels and depth (a glass mask plus the depth buffer), or at least depth-test the composite.
5. **Stalls.** Every second, every BLAS is rebuilt synchronously with `waitUntilCompleted` (`.mm:401-408, 706`). The call comes from `Update` on the main thread, through Unity's Metal command queue, although the comment says render thread (`.mm:726-727`). Expect a hitch each second and a thread-safety risk.
6. **The look is a placeholder.** Hits are flat base colour lit by a hard-coded sun and sky (`.mm:223-243`). There is no wallpaper texture and no FrontRooms lamps, which is wrong for a windowless interior. The composite shader is loaded with `Shader.Find` and is not in Always Included Shaders (its GUID does not appear in `ProjectSettings/GraphicsSettings.asset`), so a Mac player build may strip it (**UNVERIFIED** until a build is tried).

### 7.4 Proposed task row (text only; not filed)

> **G13b — Metal RT glass to production (desktop, M3+ only).** Fix 7.3 (1)–(5) first: FOV, reset blink, additive composite before post, raster-driven glass mask + depth, BLAS cache + per-frame TLAS with pieces prioritised. Then shade hits with real textures and lamps (or probe lookup). Fracture contract from 7.2: rigid pieces = instances, BLAS once per piece, TLAS per frame, no VAT on traced pieces, ≤ 64 traced pieces per window, tag + dedicated shard material, Float32 positions, single submesh. WebGL and Windows untouched (Windows DX12 could reuse the same contract later). Verify against the planar reflection from report 11 at the same frames.

---

## 8. Open items / UNVERIFIED

- The GDC 2010 Red Faction: Guerrilla talk named in the brief was not found. Guerrilla's details here come from a GDC 2009 report, a 2009 interview and a 2025 survey.
- Control: I did not read Richter's slides or video. Details come from CGWorld (Japanese) and Game Developer write-ups, plus GMTK for the intact/broken swap.
- The Finals: the lighting, edge-mesh and VFX slides are images; their content is not described here.
- Battlefield 1 / V destruction internals and Levolution internals: press only.
- Bad Company 2 "26 parts → collapse": fan wiki.
- Valve `func_breakable_surf`: summary from the search index; the page itself returned 403.
- 1990 code status of safety glazing in interior windows (§6.6): not checked; belongs to report 02.
- §7 is code reading only. Nothing was compiled or run. Defects 7.3 (1)–(4) are certain from the code. Their visual size, and the vertical orientation, need a capture.
- No talk found for Insomniac, Digital Dragons, Nordic Game or Unite on destruction.

---

## 9. Sources

Format: title — speaker / studio — venue, year — URL.

**Talks and slide decks**
1. Destruction Masking in Frostbite 2 using Volume Distance Fields — Robert Kihl / DICE — SIGGRAPH 2010, Advances in Real-Time Rendering course — https://www.advances.realtimerendering.com/s2010/Kihl-Destruction%20in%20Frostbite(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
2. The Art of Destruction in Rainbow Six: Siege — Julien L'Heureux / Ubisoft Montreal — GDC 2016 — https://gdcvault.com/play/1023003/The-Art-of-Destruction-in ; slides https://media.gdcvault.com/gdc2016/Presentations/LHeureux_Julien_Art_Of_Destruction.pdf
3. Engineering Mayhem: Technical Deep-Dive into Environmental Destruction in THE FINALS — Måns Isaksson / Embark Studios — GDC 2024 — https://gdcvault.com/play/1034280/Engineering-Mayhem-Technical-Deep-Dive ; slides https://media.gdcvault.com/gdc2024/Slides/GDC+slide+presentations/Isaksson_Mans_Engineering+Mayham+Technical.pdf
4. Destructible Environments in CONTROL: Lessons in Procedural Destruction — Johannes Richter / Remedy — GDC Summer 2020 — https://gdcvault.com/play/1030643/Destructible-Environments-in-Control-Lessons
5. Destruction of Design (Red Faction: Guerrilla) — Luke Schneider / Volition — GDC 2009, as reported — https://www.gamedeveloper.com/design/gdc-2009---day-5-4---those-who-seek-destruction-find-luke
6. Multiplayer Level Design in Red Faction Guerrilla — Luke Schneider — GDC (Vault) — https://gdcvault.com/play/1012330/Multiplayer-Level-Design-in-Red
7. Battlefield 4: Creating a More Dynamic Battlefield — Linnea Harrison / EA DICE — GDC 2014 — https://gdcvault.com/play/1021272/Battlefield-4-Creating-a-More
8. Dynamic Destruction in UE5 with the Chaos Destruction System — Jim Van Allen, Cedric Caillaud / Epic Games — GDC 2025 — https://www.gdcvault.com/play/1035357/Dynamic-Destruction-in-UE5-with
9. Causing Chaos: Physics and Destruction in Unreal Engine — Michael Lentine, Jim Van Allen / Epic Games — SIGGRAPH 2019 Real-Time Live! — https://history.siggraph.org/?p=69750
10. NVIDIA APEX: From Mirror's Edge to Pervasive Cinematic Destruction — Anders Caspersson (DICE), Monier Maher, Jean Pierre Bordes (NVIDIA) — GDC 2009 — https://developer.download.nvidia.com/presentations/2009/GDC/APEX_Destruction%20_and_MirrorsEdge_GDC09.pdf
11. Authoring Physically Simulated Destruction with NVIDIA APEX — Bryan Galdrikian, Dane Johnston / NVIDIA — GDC 2010 — https://gdcvault.com/play/1012418/Authoring-Physically-Simulated-Destruction-with ; slides https://developer.download.nvidia.com/presentations/2010/gdc/Authoring_Physically_Simulated_Destruction_with_NVIDIA_APEX.pdf
12. Technical Art Techniques of Naughty Dog: Vertex Shaders and Beyond — Andrew Maximov / Naughty Dog — GDC 2017 — https://gdcvault.com/play/1024103/Technical-Art-Techniques-of-Naughty
13. Geometry Caching Optimizations — Zabir Hoque, Ben Laidlaw / 343 Industries, Microsoft, Epic — GDC 2017 — https://www.gdcvault.com/play/1024577/
14. Visual Effects Bootcamp: Sorting Through the Rubble: A Review of Destruction Techniques — Fred Hooper / NVIDIA — GDC 2019 — https://gdcvault.com/play/1026329/Visual-Effects-Bootcamp-Sorting-Through
15. Physics for Game Programmers tutorial (Smash Hit fracture segment) — Dennis Gustafsson / Mediocre — GDC 2015 — announcement https://blog.voxagon.se/2015/02/20/physics-tutorial-at-gdc-2015.html ; tutorial session page https://gdcvault.com/play/1022194/Physics-for-Game-Programmers-Robust
16. Real Time Dynamic Fracture with Volumetric Approximate Convex Decompositions — Matthias Müller, Nuttapong Chentanez, Tae-Yong Kim / NVIDIA — SIGGRAPH 2013 (ACM TOG 32(4) art. 115) — https://history.siggraph.org/?p=108389
17. Massive Destruction in Real Time — Müller-Fischer, Chentanez, Kim, Galdrikian / NVIDIA — SIGGRAPH 2013 Real-Time Live! — https://history.siggraph.org/experience/massive-destruction-in-real-time-by-muller-fischer-chentanez-kim-and-galdrikian
18. Maximize your Metal ray tracing performance — Apple — WWDC 2022 — https://developer.apple.com/videos/play/wwdc2022/10105/
19. Your guide to Metal ray tracing — Apple — WWDC 2023 — https://developer.apple.com/videos/play/wwdc2023/10128/

**Official documentation**
20. Chaos Destruction overview — Epic Games — UE5 docs — https://dev.epicgames.com/documentation/en-us/unreal-engine/destruction-overview
21. GeometryCollection (Python API: damage_threshold, root_proxy_data, remove_on_max_sleep, removal_duration, scale_on_removal, max_cluster_level) — Epic Games — UE 5.8 docs — https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/GeometryCollection
22. Geometry Collections user guide — Epic Games — https://dev.epicgames.com/documentation/en-us/unreal-engine/geometry-collections-user-guide
23. NVIDIA Blast SDK documentation — NVIDIA — https://docs.nvidia.com/gameworks/content/gameworkslibrary/blast/1.1/api_docs/files/pageintroduction.html
24. Labs Vertex Animation Textures 3.0 — SideFX — Houdini docs — https://www.sidefx.com/docs/houdini/nodes/out/labs--vertex_animation_textures-3.0.html
25. func_breakable_surf — Valve — Valve Developer Wiki — https://developer.valvesoftware.com/wiki/Func_breakable_surf (403 to my fetcher; summary only)
26. Apple unveils M3, M3 Pro and M3 Max (hardware-accelerated ray tracing on Mac) — Apple Newsroom, 30 Oct 2023 — https://www.apple.com/newsroom/2023/10/apple-unveils-m3-m3-pro-and-m3-max-the-most-advanced-chips-for-a-personal-computer/
27. Safety Standard for Architectural Glazing Materials (16 CFR 1201; history from 1977) — CPSC — Federal Register, 23 Mar 2016 — https://www.govinfo.gov/content/pkg/FR-2016-03-23/html/2016-06523.htm
28. Safety Glazing handout (hazardous-location criteria) — City of Dublin, CA — https://dublin.ca.gov/DocumentCenter/View/14839/Safety-Glazing

**Interviews and write-ups**
29. The Art of Destruction in Rainbow Six Siege: An Interview with Julien L'Heureux — Ubisoft News, March 2016 — https://news.ubisoft.com/en-us/article/4GHX2yepSaKkflLjLAlpwO/the-art-of-destruction-in-rainbow-six-siege-an-interview-with-julien-lheureux
30. Dev Blog: Explosions & Shrapnel in Y5S1 — Ubisoft — https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/1QkezaGoRkDWqcQ6duGvtk/dev-blog-explosions-shrapnel-in-y5s1
31. Making the Procedural Buildings of THE FINALS using Houdini — Adrian Björkerud / Embark — SideFX, Feb 2026 — https://www.sidefx.com/community/making-the-procedural-buildings-of-the-finals-using-houdini/
32. GDC Summer Control destruction write-up — CGWorld (Japan), Aug 2020 — https://cgworld.jp/feature/202008-gdccontrol.html
33. Using procedural destruction to unleash chaos in Control — Game Developer, 2020 — https://www.gamedeveloper.com/production/using-procedural-destruction-to-unleash-chaos-in-i-control-i-
34. "Red Faction: Guerrilla" Q&A — Eric Arnold / Volition — CBS News, 30 Jun 2009 — https://www.cbsnews.com/news/red-faction-guerrilla-q-a/
35. FX Adventures in Uncharted 4: A Thief's End — Neilan Naicker, Raymond Popka / Naughty Dog — SideFX, 1 Jun 2016 — https://www.sidefx.com/community/fx-adventures-in-uncharted-4-a-thiefs-end/ (also 80 Level: https://80.lv/articles/uncharted-4-building-vfx-with-houdini)
36. How Naughty Dog Created the Immersive World of The Last of Us Part II — 80 Level, 8 Dec 2020 — https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/
37. Time for destruction: the tech of Quantum Break — fxguide, 21 Apr 2016 — https://www.fxguide.com/?p=185607
38. Optimizing destruction simulations for real-time solutions — Paul Ambrosiussen / SideFX, Apr 2017 — https://www.sidefx.com/tutorials/optimizing-destruction-simulations-for-real-time-solutions/
39. Using Vertex Animation Texture for Complex Visual Effects — Oleksandr Horiuk — Game Developer, 8 Dec 2023 — https://www.gamedeveloper.com/art/using-vertex-animation-texture-for-complex-visual-effects
40. Destruction Simulations for Games — Magnus Larsson — 80 Level, 27 Aug 2018 — https://80.lv/articles/destruction-simulations-for-games/
41. Cracking destruction (Smash Hit) — Dennis Gustafsson — blog, 13 May 2014 — https://blog.voxagon.se/2014/05/13/cracking-destruction.html
42. Teardown Frame Teardown — Steven Wittens — acko.net, 24 Jan 2023 — https://acko.net/blog/teardown-frame-teardown/
43. Opinion: Destruction — Erwin Coumans — Game Developer, 6 Sep 2011 — https://www.gamedeveloper.com/programming/opinion-destruction
44. Less Destructible Environments in Battlefield 3? DICE Explains — mp1st, 5 Sep 2011 — https://mp1st.com/news/less-destructible-environments-in-battlefield-3-dice-explains
45. How Games Do Destruction — Mark Brown / Game Maker's Toolkit — Substack, 2 Oct 2025 — https://gmtk.substack.com/p/how-games-do-destruction
46. Chaos demo coverage, GDC 2019 State of Unreal — CG Channel — https://www.cgchannel.com/?p=102426
47. The Division's Snowdrop engine destruction (press) — GamingBolt — https://gamingbolt.com/the-divisions-snowdrop-engine-allows-for-dynamic-destruction-designed-for-next-gen
48. Battlefield 4 Levolution (press) — PCGamesN — https://pcgamesn.com/battlefield/battlefield-4-s-levolution-lets-you-flood-cities-block-alleys-shoot-out-power

**Project files read**
- Real project (read-only): `NativePlugin/FrontRoomsMetalGlassRT.mm`, `NativePlugin/build_frontrooms_metal_glass_rt.sh`, `Assets/Scripts/Rendering/FrontRoomsMetalGlassRT.cs`, `Assets/Scripts/Rendering/FrontRoomsMetalGlassRTRendererFeature.cs`, `Assets/Shaders/FrontRoomsMetalGlassRTComposite.shader`, `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `Documentation/research/interactables/00_map_constraints.md`, `06_period_windows.md`, `Documentation/research/interaction_audit/FrontRoomsShotTimings.proposal.cs.txt`, `Documentation/research/glass/11_reflections_and_raytracing.md`, `Documentation/VISUAL_CHAT_TASKS.md`, `glass/images/03_*.jpg`, `04_*.jpg`.
- Private clone (read-only): `proj_glass/Assets/Resources/Rendering/FrontRoomsGlass.shader`.
