# 06 — Distorted / copy-paste furniture: techniques and the `FrontRoomsFurniturePile.Build` design

Status: COMPLETE (2026-10-02). Every factual claim carries a URL. "UNVERIFIED" marks anything that could not be confirmed against a fetched page; "(prior run)" marks pages fetched by the interrupted earlier run and not re-fetched now. Quotes are kept under 15 words. No assets, stills or images were downloaded.

## 0. TL;DR (read this first)

1. **The film's "copy-paste" furniture is literal duplication of intact real pieces** — the set decorator bought 20 identical sofas and 40+ identical oak chairs from a hotel liquidator for the Backrooms; some pieces were 3D-scanned so VFX could distort them; Vermette's stated inspiration is video-game clipping, escalating to "ceiling-sweeping piles". In Unity terms: **same mesh + same material, many instances, interpenetrating at legible angles**. That is also the cheapest thing to render.
2. **Codex's `BuildMemoryBleed` fails because it is timid**: 5 same-material office boxes, 3–12° tilts, non-uniform scale under rotated children (shear), parked dark against a side wall, no colliders, max ~1.9 m. It reads as broken/invisible, not as "pasted".
3. **Rules for "nothing broken, just wrong"**: intact pieces; quantised orientations (upright / 90° / 180° / 35–50° edge-lean); exact duplicates; ≥4 material families; centred landmark with a clear floor ring and its own light; height up to ~0.9 × ceiling; at most one escalation axis per room.
4. **Technique choice**: authored *tableau templates* (constraint slots) + a **seeded analytic solver** (OBB stacking, edge-tip bisection, copy-paste offsets, overlap budget) at runtime; **no runtime physics**. Blender 4.3 rigid-body bake (operators verified locally) only for 1–2 hero piles.
5. **Rendering on Mac**: SRP Batcher is on → share materials, no MaterialPropertyBlocks; GPU Resident Drawer (Forward+, compute, not WebGL) is the ideal path for many identical copies but is currently off → make it a Mac quality option; default = per-pile `StaticBatchingUtility.Combine`. Grounding = existing SSAO (radius 0.45) + a Decal feature (Screen Space for WebGL) + blob-shadow fallback. Avoid coplanar contacts instead of using depth bias.
6. **Integration bug to pre-empt**: the map Hunter walks along BFS cell centres with `MoveTowards` and ignores colliders, so a centred pile would be walked through. `Build` should return its footprint so `FrontRoomsMapWorld` marks those cells impassable; blocker colliders then also make the pile a real **line-of-sight breaker** (Hunter LOS is a raycast).
7. **Tableaux**: Centre sculpture (40 %), Wall-embedded (20 %), Copy-paste row (15 %), Ceiling-stuck (10 %), Tilted office cluster (10 %, office only), Zero pile (5 %); intensity rises with maze depth.

## 1. What the film actually did (practical production facts)

Verified facts (each re-fetched in this run unless marked):

1. **Real furniture, really duplicated.** Set decorator Trevor Johnston bought from a hotel liquidator "20 identical … upholstered sofas" and 40+ identical oak slat-back dining chairs, specifically to populate the Backrooms, which in the story "creates duplicates of real-world items". Sourcing rule: nothing newer than the early 1990s; channels were Facebook Marketplace and BC estate sales. — [The Set Set, Eve Crosbie, interview with Trevor Johnston](https://thesetset.com/articles/backrooms-set-decorator-trevor-johnston-interview)
   - **Implication for the game:** the "copy-paste" look is achieved with *identical* real objects, not with mutated ones. In engine terms: the same mesh, instanced many times, is the authentic technique — it is also the cheapest one.
2. **Distortion was partly VFX on scanned props.** The same Set Set article says pieces were 3D-scanned so the VFX department could distort them digitally in post, supporting the "no-clipping" game concept. — [The Set Set](https://thesetset.com/articles/backrooms-set-decorator-trevor-johnston-interview)
   - **Implication:** the film itself mixes intact practical piles with digital interpenetration. A game can do both natively (interpenetration is free in a renderer).
3. **The stated design source is video-game clipping.** Production designer Danny Vermette took the furniture idea from game "clipping", where objects "appear spliced at odd angles" when pushed through no-clip barriers; the furniture escalates from drab to "ceiling-sweeping piles of Frankensteined ottomans and chairs" deeper in the maze; "as much practical as we could". — [ELLE Decor via AOL, Dorothy Scarborough](https://www.aol.com/articles/meaning-behind-surreal-sets-a24-195154000.html)
4. **Escalation is a structure, not a one-off.** Same source: furniture starts merely drab and escalates with depth. → Use `pileIntensity` as a function of maze depth / run progress (§7.4).
5. **Kane's own framing.** Kane Parsons designed all sets in Blender 1:1 with the final film and used it to shot-list; he describes the concept as the feeling of "glitching and getting stuck in a video game". Built as ~30,000 sq ft of practical sets on Vancouver soundstages. — [A24 Notes, "Thirty Thousand Square Feet with Kane Parsons & James Wan"](https://a24films.com/notes/2026/05/thirty-thousand-square-feet-with-kane-parsons-james-wan)
   - Location conflict: ELLE Decor says "Toronto area" soundstages; A24 and Wikipedia say Vancouver. A24 is the primary source → Vancouver. ([Wikipedia](https://en.wikipedia.org/wiki/Backrooms_(film)) — fetched by prior run, not re-fetched.)
6. **The pile room is the first Backrooms space.** The furniture-pile room is the first room after the Null Zone in the store basement: classic yellow wallpaper corridors, then a heap of domestic objects in the centre; contents listed as restaurant chairs, TVs, cabinets, sofas, shelving, dressers, lamps, hatstands. — [Film and Furniture](https://filmandfurniture.com/2026/06/backrooms-the-furniture-film-of-the-year/) (fetched by prior run; not re-fetched).
7. **Other furniture anomalies in the film (reviews):** ladder-back chairs clipping through floors ([Film and Furniture](https://filmandfurniture.com/2026/06/backrooms-the-furniture-film-of-the-year/), prior run); couches and furniture "buried in the midst of floors and walls", shoes upright in carpet, wall cabinets running a whole hall ([Moria Reviews](https://moriareviews.com/sciencefiction/backrooms-2026.htm), prior run); "some melding with the floor or walls, some piled up like obstacle courses or a bonfire-in-waiting" ([BFI Sight and Sound](https://www.bfi.org.uk/sight-and-sound/reviews/backrooms-kane-parsons-turns-internet-mythology-into-unsettling-inventive-horror), prior run); "art installation versions of office space" ([KQED](https://www.kqed.org/arts/13990220/backrooms-movie-review-a24-liminal-space-horror), prior run).
8. **Physical set grammar.** Sets on platforms with slopes and odd angles, crawl spaces and ramps to make actors uncomfortable. — [The Credits / MPA, Vermette interview](https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/) (prior run).
9. **Not found:** no fetched source says *how* the piles were physically fixed (screws, armature, glue). Mark "how the pile was secured" as UNVERIFIED; the A24 Blu-ray lists a prop walkthrough and VFX breakdowns that would answer it (Codex's doc cites [shop.a24films.com](https://shop.a24films.com/products/backrooms-blu-ray) — not re-verified). Fast Company, Dezeen, IndieWire, Curbed and GoldDerby all blocked fetching (403/402/blocked) in this or the prior run.

### What Still A and Still B tell us (from Red's descriptions; no stills copied)

| Observation | Engine rule |
|---|---|
| Pile sits dead-centre of an empty hall, shot symmetrical at eye level. | Pile = landmark at room centroid or on a long sightline; keep 2–3 m empty floor ring. |
| Every piece is intact and recognisable (dresser, hutch, armchair, side table, lamp, stool, filing cabinet / sofa, ladder-back chairs, CRT, torchiere, crate on pallet, display cabinet, club chair, bookshelf). | No fracture, no melting, no random scale. Recognition first. |
| Orientations are decisive: ~40° tipped on a corner, ~45° lean, upside-down, sideways. | Orientation states are quantised (§6.3). |
| Mixed eras and rooms (living room + office + warehouse). | Library mixes domestic + office + storage pieces; `OfficeKit` pieces are only ~30–40 % of a pile. |
| Still B reaches ~2.5 m, nearly touching the ceiling; a torchiere "pokes up". | Height budget = 0.85–0.97 × ceiling; one vertical "spike" piece on top. |
| Pieces interpenetrate yet the read is "pasted", not "crashed". | Interpenetration happens *at joints and volumes*, never as thin surfaces coplanar with each other (z-fighting), and never as debris. |
| Repeated identical chairs (Still B ladder-backs; Set Set's 40 identical chairs). | "Copy-paste" operator duplicates one piece with a rigid offset (§6.3). |

## 2. Art references (installations that solve the same visual problem)

Each artist below contributes one *operator* to the generator. That is the useful takeaway; the art is research only, never copied.

| Artist / work | What it physically is (verified) | Operator it gives the generator |
|---|---|---|
| **Doris Salcedo – *Unland* (1995–98)** | Two mismatched domestic tables (different height, width, wood) with legs cut off at one end, crudely joined into one long table; the join is left uneven. "Like the mutated remains of an accident." — [Tate Papers 01](https://tate.org.uk/research/tate-papers/01/unland-the-place-of-testimony) | **Splice**: two *different* pieces of the same class joined end-to-end at one shared face (desk + sideboard → one long surface). Hide the seam inside the overlap, never as two coplanar tops. |
| **Doris Salcedo – *Untitled* furniture (from 1989)** | Wardrobes, chairs, doors filled with concrete; fragments of *other* furniture visible inside; furniture hybridised. — [Tate Papers 01](https://tate.org.uk/research/tate-papers/01/unland-the-place-of-testimony); [Guggenheim Bilbao](https://guggenheim-bilbao.eus/en/exhibition/doris-salcedo) (prior run) | **Nest/inside**: a chair passing through a wardrobe's open front, a chair leg emerging from a cabinet side. Interpenetration as *containment*. |
| **Doris Salcedo – Istanbul project (2003, 8th Istanbul Biennial)** | Hundreds of wooden chairs heaped in a narrow vacant lot between two apartment buildings, to the height of a small building. — [Istanbul Modern](https://www.istanbulmodern.org/en/collection/istanbul-project-i). Count reported as ~1,550 by [Public Delivery](https://publicdelivery.org/doris-salcedo-chairs/) and ~1,500 by [Wikipedia](https://en.wikipedia.org/wiki/Doris_Salcedo) (both prior run). | **Wall-to-wall fill**: one repeated piece type packed between two planes (corridor choke). Use for the *Copy-paste row* / corridor-plug tableau. |
| **Michael Johansson – "real-life tetris"** | Found objects (suitcases, TVs, cabinets, boxes) packed to fill a gap exactly; he hunts flea markets for "duplicate or nearly identical objects". — [Museum Voorlinden](https://www.voorlinden.nl/exhibition/michael-johansson/?lang=en); method detail in [Inhabitat](https://inhabitat.com/michael-johanssons-precisely-stacked-sculptures-give-found-objects-the-tetris-treatment/) (prior run) | **Pack/fit**: axis-aligned bin-packing of boxy pieces into a doorway or alcove; *no* interpenetration — the uncanny comes from perfect fit + doubles. A good *contrast* tableau (orderly wrongness). |
| **Ai Weiwei – *Grapes* (2010)** | Qing-dynasty wooden stools joined with traditional joinery into one cluster, 193 × 202 × 191 cm. — [De Pont Museum](https://www.depont.nl/en/collection/artists/weiwei-ai/grapes) | **Radial array**: N copies of one small piece, each rotated about a common centre, legs pushed into neighbours' seats. Exactly the "array of the same chair" rule. |
| **Tadashi Kawamata – *Avalanche* (Paris, 21 Sep – 5 Oct 2024)** | Hundreds of wooden chairs spilling out of a window into a courtyard "like a large wave". — [designboom](https://www.designboom.com/art/avalanche-tadashi-kawamata-phileo-dover-street-market-paris-10-07-2024/). *Chairs for Abu Dhabi* (2012) was a ~6 m stacked chair edifice — [Islamic Arts Magazine](https://islamicartsmagazine.com/magazine/view/an_art_work_of_hundreds_of_chairs_begins_creation_this_week_for_abu_dh/) (search snippet only, prior run, UNVERIFIED by fetch). | **Flow/spill**: a pile with a direction — densest at a wall opening or ceiling hole, thinning across the floor. This is the *Wall-embedded* and *Ceiling-stuck* tableau logic. |
| **Sarah Sze** | Room-scale accumulations of everyday objects; "organizes space as if it is a remnant of human behaviour discovered by accident"; deliberate scale shifts. — [Victoria Miro](https://victoria-miro.com/exhibitions/380) (prior run, not re-fetched) | **Scatter at the base**: small satellites (paper, a lamp, a single shoe, a cable) around the pile foot make the heap feel like a *remnant of behaviour* rather than a placed asset. Cheap: 4–10 small props. |

Design synthesis: the film's pile = **Kawamata spill + Ai Weiwei array + Salcedo nest**, made from **Johansson-style doubles**. Keep each operator explicit in code so a tableau can turn them on/off.

## 3. Kane Pixels (Async / VHS series) furniture anomalies

- **Why there is furniture at all (in-universe):** the Async Research Institute's project was pitched as a fix for "the growing housing and storage crisis" — i.e. the Backrooms were to be used as storage. — [Wikipedia, Backrooms (web series)](https://en.wikipedia.org/wiki/Backrooms_(web_series)). Game use: piles can read as *stored* stock that the place has re-arranged (crates on pallets, stencilled boxes in Still B fit this).
- **Fan-wiki lore (secondary, low confidence):** furniture "no-clipped" in from Earth and entities later moved it around without understanding its function. — search snippet of the Kane Pixels fandom wiki (page fetch returned 402) → UNVERIFIED.
- **Objects fused into architecture (episode 21 "Static Dead End", per a fan explainer):** objects "half-fused into the floor and walls"; a carpet hill with one plastic chair on top; a room that mirrors Room 14D "but wrong". Episode 19 contains an embedded domestic house. — [Taylor Holmes explainer, eps 18–22](https://taylorholmes.com/2026/06/02/explaining-the-backrooms-youtube-episodes-18-22/) (secondary source; episode content not checked against the videos → treat as UNVERIFIED-secondary).
- **Episode 25 furniture-store room** with "EVERYTHING MUST GO" sale signage. — [Wikipedia, web series](https://en.wikipedia.org/wiki/Backrooms_(web_series)).
- **VHS look:** Kane cites flash-on, gross lighting, off white balance as the found-footage signature (same Wikipedia page). For our pile this means: *no* bespoke "glitch shader" on the furniture; the wrongness lives in placement; any VHS treatment is a camera/post effect that applies to the whole frame (the project already has film grain, CA and lens distortion).

**Takeaway:** in Kane's canon the anomaly is *spatial* (copied, merged, misplaced), never a material/shader effect on the object. That directly argues against dithering, wobble vertex shaders, or texture glitches on pile pieces.

## 4. Liminal-space games and how they handle furniture anomalies

| Game | What it does with furniture / anomalies (verified where linked) | Lesson for FrontRooms |
|---|---|---|
| **The Exit 8** (Kotake Create) | Rule loop: "If you find anomalies, turn back immediately" ([Steam](https://store.steampowered.com/app/2653790/The_Exit_8/), prior run). A notoriously hard anomaly is posters that are slightly *larger* than normal; players filed it as a "no anomaly" bug ([Automaton search snippet](https://automaton-media.com/en/news/20231208-23845/) — page fetch truncated, so UNVERIFIED-by-fetch). | Small scale changes read as *bugs*, not as intent. If an anomaly must be subtle, the game must *teach* the player to look (Exit 8 does). FrontRooms is a chase game → anomalies must be **loud** (180°, 90°, ceiling-touching), not 5 %. |
| **POOLS** (Tensori) | No enemies; "numerous chairs you occasionally come across" that serve no purpose. — [GameSpew review](https://www.gamespew.com/2024/04/pools-review-a-liminal-hidden-gem/) | Purposeless, *ordinary* furniture placed with care is itself uncanny. Some rooms should have **one** perfect chair in a huge space — the "zero-pile" tableau. |
| **Escape the Backrooms** | Level 5 "Abandoned Office": count book stacks, water dispensers, tables, chairs, enter counts into vending machines; Levels 6/14 hide under beds/closets. — [gameplay.tips guide](https://gameplay.tips/guides/escape-the-backrooms-all-levels-guide.html) | Furniture *types* can carry gameplay information (counts, landmarks). A pile with a deterministic, countable composition can be a navigation clue. |
| **Inside the Backrooms** | 4-player co-op; hiding in lockers to escape the first level's monster. — [search summary of the Steam page](https://store.steampowered.com/app/1987080/) (not fetched → UNVERIFIED-by-fetch) | Hiding spots should be explicit, readable volumes. A pile may expose one **hollow** (under an inverted table/desk) as a hide spot with a defined trigger volume. |
| **The Backrooms 1998** (Steelkrill) | Found-footage survival horror; mic input detects voice/breathing; spray paint to mark the path. — [TechRadar search summary](https://www.techradar.com/news/best-backrooms-games-no-clipping-has-never-been-more-fun-or-terrifying) (prior run, search snippet only → UNVERIFIED-by-fetch) | Players in mazes need landmarks; spray marks exist because rooms repeat. **Unique piles are the landmark system** that makes the FrontRooms maze navigable without UI. |
| **Anemoiapolis** | Liminal mall/pool spaces with hidden procedural elements designed to make players more lost. — search summary of [TechRaptor review](https://techraptor.net/gaming/reviews/anemoiapolis-chapter-1-review) (fetch 403 → UNVERIFIED-by-fetch) | Procedural disorientation works *only* if some things stay stable. Pile composition must be deterministic per room seed, so a returning player recognises "the sofa-on-top pile". |

No source found for a specific "furniture pile" mechanic in these games — the film is ahead of the games here, which is an opportunity for FrontRooms.

## 5. Why the existing Codex attempt (`BuildMemoryBleed`) fails — what not to do

Source read: `Frontrooms3D/Assets/Scripts/FrontRoomsOfficeFurniture.cs` lines 142–218 (`Build` + `BuildMemoryBleed`), helpers at 395–452; rendered result checked in `Verification/lookdev/2_Office_back.png` (the cluster is the dark heap at frame-left, against the side wall).

| # | What the code does | Why it reads wrong | Rule for the new generator |
|---|---|---|---|
| 1 | Cluster is parked at `(±3.55, 0, 10.1)` — side wall, rear third, behind the workstations ("the memory bleed lives to the sides"). | In the look-dev frame it is a dark, unreadable lump at the edge of frame. The film stills put the pile **in the centre of an empty hall, on the eye-line axis** — it is the subject of the shot, not clutter. | Pile is a *landmark*: place it on a sightline axis with ≥2 m clear floor around it and its own light pool. Clutter belongs to `OfficeKit.Dress`, not to the pile. |
| 2 | Tilts of 3–12° (`Euler(6,17,3)`, `-12`, `8`…) and non-uniform scale `0.72–1.18`. | Small angles read as a placement *bug* or bad modelling, i.e. "broken". The film's pieces are decisive: ~40–45° leans, clean 90° side-lays, clean 180° inversions. | Quantise orientations to a small set of *legible* states (upright, 90° on side/back, 180° inverted, 35–50° lean on an edge). Never 3–12° unless it is a deliberate "almost right" anomaly. |
| 3 | Non-uniform `localScale` on container GameObjects whose children are themselves rotated (chair casters in a loop, CRT yaw). | Unity cannot represent a rotated child under a non-uniformly scaled parent without shear, so bevels, casters and screens skew (Unity Transform manual, cited in §6.3). It also stretches texel density on mesh-UV materials. | Uniform scale only (and only from a whitelist like 1.0 / 0.97 / 1.03), or authored "squashed" mesh variants baked in Blender. Mirroring = scale `(-1,1,1)` on the *leaf* renderer only. |
| 4 | 5 pieces, all from the same office kit (desk, filing cabinet, chair, shelf, CRT), same 1–2 materials. | No silhouette or material contrast; the pile becomes one grey mass. Still A/B work because an orange-grain dresser, pink velvet armchair, teal club chair, black CRT and beige steel cabinet are instantly separable. | 12–30 pieces per pile from ≥4 material families (warm wood, upholstery, painted steel, black plastic) and ≥3 silhouette classes (box, open frame, soft). |
| 5 | Max height ≈1.9 m. | Film piles are "ceiling-sweeping" (verified, §1). | Target 75–95 % of `ceilingHeight` for the hero variant; one piece may touch or pierce the ceiling. |
| 6 | Hand-typed positions (`y = .58`, `y = .18`…), no support test. | Pieces float or sink arbitrarily: a desk hovering 0.58 m up with nothing under it reads as a physics bug. | Every piece must rest on a *support* (floor, another piece's top face, or an edge contact), or be explicitly flagged as an "embedded" anomaly with ≥30 % of its volume buried. |
| 7 | Upside-down chair at 156–168°. | Reads as "tumbling/fallen" (broken), not "pasted". | Use exact 180° (± 2°) for inversions. |
| 8 | Fallback pieces are built with `Box(..., collider:false)` and `Cylinder` with its collider destroyed; no pile collider. | Player walks through the pile — the opposite of "solid but wrong". | One compound collider set per pile (§6.7) + `NavMeshObstacle`/maze-cell blocking. |
| 9 | Each piece is 10–40 separate GameObjects (`Bevel`/`Box`/`CreatePrimitive`), built per recycled room. | Many renderers and GC per room spawn on a Mac laptop. | Shared prefab meshes (one `MeshFilter` per material) instanced via SRP Batcher/GPU Resident Drawer, or combined per pile (§6.8). |
| 10 | Variation = `Hash(sequence,41) % 3` → three hard-coded layouts. | Repetition is noticed within a few rooms. | Seeded solver with a library and tableau templates; seed derived from room coordinates (§6.9). |
| 11 | Imported FBX roots need `scale * 100f`. | Fragile: every downstream scale multiplies a hidden 100× and non-uniform tweaks compound. | Fix at import (Blender export "Apply Transform"/unit scale or Unity "Convert Units"), so prefab root scale = 1 — UNVERIFIED which option the current Codex export used. |

**Bottom line:** the Codex cluster tries to be "subtle" and ends up *invisible + broken-looking*. The film's piles are the opposite: loud, centred, tall, made of intact, recognisable, high-contrast pieces in legible orientations.

## 6. Technique menu (Unity 6 URP, Mac laptop)

**Project facts this section is calibrated against (read from the repo, 2026-10-02):**
- `Assets/Settings/FrontRooms_URP.asset`: SRP Batcher **on** (`m_UseSRPBatcher: 1`), dynamic batching off, **GPU Resident Drawer off** (`m_GPUResidentDrawerMode: 0`), additional-light shadows on, soft shadows on.
- `FrontRooms_URP_Renderer.asset`: rendering mode 2 (= Forward+), SSAO feature active: Source = Depth Normals, Radius 0.45, Intensity 1.6, Direct Lighting Strength 0.35, Falloff 40, no downsample. **No Decal renderer feature** present.
- `ProjectSettings.asset`: static batching on for Standalone, **off for WebGL** (there is a `Documentation/WEBGL_BUILD.md`, so WebGL is a target too).
- Movement: player is a `CharacterController`; the map Hunter (`FrontRoomsMap/FrontRoomsMapHunter.cs`) path-finds by BFS over 3 m grid cells and moves with `Vector3.MoveTowards` between cell centres (line 293) — it does **not** collide with props; its line-of-sight is a `Physics.RaycastNonAlloc` against all non-trigger colliders (line 331). No NavMesh anywhere.
- Integration hook already exists: `FrontRoomsMapWorld.Furnish` (lines ~781–820) reflects for `FrontRoomsFurniturePile.Build(Transform, Vector3, float, float, int)` and calls it for non-office rooms with min side ≥ 4 cells, `radius = min(3.2, minSide·3·0.22)` (→ 2.64 m for 4-cell rooms, 3.2 m for ≥5), chance 0.35 (≥0.6 in Tall zones), seed = `MapHash.Hash(seed, chunk.x*16+r, chunk.y, 307, revision)`.
- A new prop loader `Assets/Scripts/Office/FrontRoomsKitLibrary.cs` (created 2026-10-02 15:00, presumably by the parallel build agent) loads `Resources/Props/Models/<name>` FBX + a JSON sidecar with `boundsMin/Max`, `supports[] {name, centre, size}`, `colliders[] {centre,size}` (boxes), `anchors[]`, `tags[]`, `slots[]`, `triangles`, and offers `Spawn(name, parent, pos, rot, scale, colliders)`. **The pile generator should consume exactly this sidecar**; §7.1 only adds pile-specific fields.

### 6.1 Authored compositions vs seeded procedural stacking

| | Authored tableau (Blender or Unity editor) | Seeded procedural solver (runtime) |
|---|---|---|
| Look | Best silhouettes; can match Still A/B intent exactly | Good if operators are curated; bad if "random rotate everything" |
| Variety | N templates (6–12 is enough for landmarks) | Unlimited |
| Determinism | Perfect (it is data) | Needs a seeded RNG + no physics at runtime |
| Cost to make | Artist time per template | Engineering once |
| Risk | Repetition across a large maze | Implausible floating/stacking, unreadable mass |

**Recommendation: hybrid.** Author 6–8 *tableau templates* as **relative constraint lists** ("dresser tipped onto corner, leaning on hutch; armchair inverted on top"), not as fixed transforms, and let the seeded solver choose the concrete pieces from the library that satisfy each slot's tags and size range, then resolve contacts. This gives authored composition with procedural variety. Fixed-transform "baked" tableaux (from Blender physics, §6.2) are the fallback for the 1–2 hero piles that must look perfect (e.g. the first pile the player ever sees, mirroring the film's first Backrooms room).

### 6.2 Offline physics settle vs runtime

- **Unity:** `Physics.Simulate(step)` runs the simulation manually when `Physics.simulationMode` is `Script`; steps > 0.03 s "likely to produce inaccurate results"; determinism requires a fixed step. — [Unity ScriptReference: Physics.Simulate](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Physics.Simulate.html). Whether this works in **Edit mode** is *not stated* in the 6000.0 docs (UNVERIFIED in docs); community editor tools that rely on it exist (e.g. [TCS-PhysicsDropper](https://github.com/unitycoder/TCS-PhysicsDropper), [Unity Discussions thread](https://discussions.unity.com/t/physics-in-scene-editor-mode/27215) — search results from prior run, not fetched). Test before relying on it.
- **Blender 4.3 (verified locally by running `Blender -b --python` on this Mac):** `bpy.ops.rigidbody.objects_add(type)`, `rigidbody.shape_change(type)` with shapes `BOX, SPHERE, CAPSULE, CYLINDER, CONE, CONVEX_HULL, MESH, COMPOUND`, `rigidbody.mass_calculate(material, density)`, `rigidbody.bake_to_keyframes(frame_start, frame_end, step)`, `object.visual_transform_apply` ("Apply the object's visual transformation to its data"), `ptcache.bake_all`; world exposes `substeps_per_frame`, `solver_iterations`, `use_split_impulse`. So a headless script can drop pieces, bake, apply visual transforms and export the resting transforms as JSON.
- **Why NOT runtime physics:** rooms are recycled and must reproduce exactly; PhysX settle depends on step order and timing; settling 20 bodies on room spawn costs frames on a laptop and risks pieces sliding into the door path. Unity itself only promises determinism with a fixed step (doc above), not across hardware.
- **Why physics settle is still useful offline:** it produces *believable* contacts (a dresser genuinely resting on its corner against a hutch). But physics never produces the film's look on its own — real physics would make pieces *slide apart*, not jam. Use it only for "gravity polish" of an authored tableau: author interpenetrations first, mark those pieces kinematic/passive, then let 2–4 "free" pieces settle onto them.
- **Runtime solver = analytic.** Use support-face stacking + box-overlap tests (`Physics.ComputePenetration` works on colliders that are not even enabled and "has no side effects on the Scene" — [Unity ScriptReference](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Physics.ComputePenetration.html)). Simpler still: do the overlap maths on the sidecar's oriented boxes in pure C# (OBB–OBB SAT), which avoids touching PhysX at all and is deterministic.

### 6.3 Rule-based "copy-paste" placement operators

Each operator takes the current pile state + RNG and appends 1–N pieces. All operators keep pieces **intact** and choose orientations from a quantised set.

| Operator | Rule | Reference |
|---|---|---|
| `Base` | Place 1–3 heavy, wide pieces (sofa, dresser, desk, sideboard, pallet+crate) upright or on their back, footprint inside 0.6·radius. | Still A/B bases |
| `StackOnSupport` | Pick a support face (sidecar `supports[]`) of an existing piece; place a new piece whose footprint centre lies on it; allow up to 25 % overhang. | Still B sofa on top |
| `TipOnEdge` | Rotate a box-like piece 35–50° about one bottom edge; its high corner rests on a neighbour (contact found by OBB test). | Still A dresser ~40°, hutch 45° |
| `Invert` | Exactly 180° about X or Z (±2°), resting on a support face. Best for chairs, tables, stools (legs up = instantly readable). | Still B ladder-backs |
| `SideLay` | Exactly 90° about X or Z. | Still B chairs sideways |
| `CopyPaste` | Duplicate the *last placed* piece (same mesh, same material) with a rigid offset of 10–45 % of its size and a yaw step of 0/15/90°; the copies interpenetrate. Run 2–5 times. | Set Set: 40 identical chairs; Ai Weiwei *Grapes* |
| `Splice` | Place a second piece of the same class end-to-end so their volumes overlap by 15–40 % of the shorter one (two desks become one long one). | Salcedo *Unland* |
| `Nest` | A small piece's volume 40–70 % inside a big piece's open volume (chair inside wardrobe, stool through shelf bay). | Salcedo *Untitled* |
| `Spike` | One tall thin piece (torchiere, hatstand, floor lamp) on top, near-vertical (≤10° tilt), to break the silhouette upward. | Still B torchiere |
| `Satellite` | 4–10 small props at the foot (paper stacks, a shoe, a single cassette, a cable). Mostly decals + 1–2 meshes. | Sarah Sze |
| `Pierce` | A piece passes through a wall/ceiling plane (see §6.6). | ELLE Decor "no clip" |
| `Mirror` | `localScale.x = -1` on the leaf renderer; use only for asymmetric pieces where the mirroring is subtle (a hutch with its handle on the wrong side). | Exit 8-style subtle anomaly |

Non-uniform scale: the Unity Transform manual warns that a rotated child under a non-uniformly scaled parent "might appear skewed or 'sheared'" and that skewed Box Colliders no longer match the mesh — [Unity Manual: Transform](https://docs.unity3d.com/6000.0/Documentation/Manual/class-Transform.html). `FrontRoomsKitLibrary.Spawn` puts the scale on the instance root of a single-renderer model, so it will not shear, but **the pile must never parent pieces under a scaled group**, and should restrict scale to uniform 0.97–1.03 (or one deliberate *Exit-8 style* 1.12 "too big" copy per pile at most).

### 6.4 Interpenetration without z-fighting

Z-fighting happens only where two surfaces are (nearly) **coplanar and overlapping**. Interpenetration at an angle is free. Rules:

1. **Reject coplanar contacts in the solver:** after placing a piece, for each pair of overlapping OBBs, compare face normals; if any pair of faces is parallel within 2° **and** their plane distance is < 3 mm, nudge the newcomer by +8–15 mm along that normal or rotate 3–5° about the vertical axis. (`CopyPaste` with a pure translation along a face is the main offender — e.g. two identical desks offset sideways share top planes.)
2. **Copy-paste offsets always include a vertical component** ≥ 1 cm, or a yaw ≥ 3°.
3. **Shader depth bias is a last resort.** ShaderLab `Offset factor, units` sets GPU depth bias ([Unity Manual: Offset](https://docs.unity3d.com/6000.0/Documentation/Manual/SL-Offset.html), prior run) but on a shared URP Lit material it would bias every instance; and it breaks SRP-batch grouping if done as a material variant. Prefer geometric nudges.
4. **Hide seams**: where the solver intentionally buries a piece in another ≥ 30 % (Nest/Splice), the cut line is inside the host's volume and is never seen — only if the host is closed. For open hosts (a shelf bay), accept the visible intersection; it is the point.
5. Thin pieces (paper, table tops < 2 cm) never copy-paste coplanar — scatter them at different heights.

### 6.5 Contact grounding: SSAO, decals, blob shadows

- **SSAO (already on):** URP SSAO settings and costs — Radius has a "High" performance impact (smaller is cheaper); Samples 4→8 doubles cost; Blur Bilateral is the most expensive; Downsample has a "Very high" impact (big saving, less detail); After Opaque helps when Source = Depth — [Unity Manual: SSAO renderer feature reference](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/ssao-renderer-feature-reference.html) (re-verified). Current Radius 0.45 m is right for furniture contact. SSAO alone gives *crease* darkening where pieces interpenetrate — this is exactly what sells "jammed together". Keep `Direct Lighting Strength` 0.3–0.5 so occlusion also shows under the lit troffer pool.
- **URP has no built-in contact shadows** (HDRP-only feature; no URP setting found in this or the prior run → UNVERIFIED negative). Rely on SSAO + shadow maps + decals.
- **Decals (not yet enabled in the renderer):** URP Decal renderer feature projects decal materials; "does not work on transparent surfaces"; decals use material property blocks so they **don't use the SRP Batcher**, but share-material decals can be GPU-instanced; atlas decal textures — [Unity Manual: Decal renderer feature](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-feature-decal.html) (prior run). Technique: **DBuffer** needs a DepthNormal prepass and "does not support the OpenGL and OpenGL ES API"; **Screen Space** avoids the prepass unless Rendering Layers are used — [Unity Manual: Decal reference](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-feature-decal-reference.html) (re-verified). Because SSAO already requests Depth Normals, DBuffer's prepass is partly paid for on Metal; **for the WebGL build choose Screen Space** (WebGL = OpenGL ES).
  - Use 1–3 decals per pile: a **carpet crush/dust ring** (soft dark ellipse 1.2× footprint, 15–25 % opacity), and **drag scuffs** from tipped pieces. No dirt *on* furniture — "nothing broken".
- **Blob shadow fallback** (cheap, WebGL-safe): one quad with a radial gradient, multiply-blended, under the pile — same mesh/material for all piles.
- **Lighting:** give the pile its own troffer pool. The film's Still A/B piles sit under the regular grid; in-game, ensure the pile centre is within ~1 m of a lit fixture so its silhouette reads against darker walls (this also answers the look-dev problem in `2_Office_back.png`).

### 6.6 Piercing walls / ceilings (geometry vs stencil vs clip planes)

Three options, cheapest first:

1. **Plain geometric interpenetration (recommended).** Just let the piece pass through the wall/ceiling mesh. Walls/ceilings are opaque and closed, so the part "inside" is hidden by depth. Requirements: the hidden part must not poke out the *other side* into a neighbour room — clamp penetration depth to `wallThickness − 2 cm` (map world `WallThickness = .16f`), or check that the other side is solid void. For the ceiling, the drop-ceiling plenum is not modelled → cap penetration at 10–15 cm *or* add a short "cut ring" (ceiling-tile trim) mesh around the entry.
2. **Clip plane in the shader** (when the piece must not appear on the far side): a Shader Graph variant of the furniture material with world-space plane `(n, d)` per instance, alpha-clip when `dot(n, posWS) > d`. Costs: alpha-clip disables early-Z benefits for that draw; per-instance plane data needs MaterialPropertyBlock (breaks SRP batching) or DOTS-instanced property (GRD). Use only for 1–2 hero pieces.
3. **Stencil portal** (piece visible "through" a wall only from one side): URP Render Objects renderer feature with layer mask, event, depth-test/stencil overrides — [Unity Manual: Render Objects](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-features/how-to-custom-effect-render-objects.html) (prior run). Overkill for furniture; keep for actual no-clip portal VFX.

The film did its wall-clipping as practical half-pieces plus VFX on scanned props (§1). In a game, option 1 *is* the half-piece.

### 6.7 Colliders and navigation

- **Player:** one `BoxCollider` per piece from the sidecar `colliders[]` (already supported by `FrontRoomsKitLibrary.AddColliders`). Then **merge**: compute the pile's convex XZ footprint and add 2–4 big axis-aligned blocker boxes (height ≥ 1.8 m) so the player cannot wedge into gaps between interpenetrating boxes; disable per-piece colliders below 0.4 m height that sit inside a blocker (fewer contact pairs).
- **Mesh colliders:** convex mesh colliders "are limited to 255 triangles" ([Unity Manual: Mesh Collider](https://docs.unity3d.com/6000.0/Documentation/Manual/class-MeshCollider.html), prior run quote); concave mesh colliders can only be static/kinematic ([Unity Manual: Mesh colliders intro](https://docs.unity3d.com/6000.0/Documentation/Manual/mesh-colliders-introduction.html), prior run). For a static pile a *single non-convex MeshCollider built from the combined low-poly collision proxy* is legal and cheap for raycasts, but box compounds are simpler and never snag the CharacterController on tiny edges → **boxes**.
- **Hunter (critical integration bug to avoid):** the map Hunter moves along BFS cell centres with `MoveTowards`, ignoring colliders. A pile centred in a 4×4-cell room covers parts of the four central cells (radius 2.64 m around a cell corner), so the Hunter would **walk through the pile**. Fix options: (a) `Build` returns/registers the occupied cell rect so `FrontRoomsMapWorld` marks those cells impassable for the Hunter BFS (`MapGrid.Passable`), keeping a 1-cell ring free; or (b) the Hunter does a capsule-cast step and slides. (a) is consistent with the existing grid design. NavMesh is not used in the project; `NavMeshObstacle` (Box/Capsule, optional carve — [AI Navigation manual](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshObstacle.html)) only matters if a NavMesh is introduced later.
- **Line of sight:** the Hunter's `Visible()` raycasts against all non-trigger colliders, so pile blocker boxes automatically make the pile a **LOS breaker** — a real chase tool. Make blocker height ≥ eye height (1.7 m) on at least one side.
- **Hide spot:** if a tableau has a hollow (inverted desk/table, sofa on its back against a cabinet), add a trigger volume tagged `HideSpot`; keep the hollow ≥ 0.7 m high and with one open side facing away from the room's main door.

### 6.8 Rendering cost: SRP Batcher, GPU Resident Drawer, instancing, static batching, mesh combine, LOD

- **SRP Batcher (on):** keeps material data resident on the GPU and reduces render-state changes between draws — [Unity Manual: SRP Batcher](https://docs.unity3d.com/6000.0/Documentation/Manual/SRPBatcher.html) (prior run). It works best when many renderers share **shader variants**, not necessarily materials. Implication: give all pile pieces the same `FrontRooms/Surface` shader and a small set of materials (one per kit slot), and **never use MaterialPropertyBlock** for per-piece tint: Unity says in an SRP project "don't use a MaterialPropertyBlock because they remove SRP Batcher compatibility" and to use different materials instead — [Unity Manual: batching properties](https://docs.unity3d.com/6/Documentation/Manual/DrawCallBatching-Properties.html). Do colour variation via 2–3 material variants per slot. (Copy-paste duplicates *should* share the exact material anyway — §6.10 rule 6.)
- **GPU instancing:** in URP, GPU instancing on custom shaders works only if the SRP Batcher is disabled or the shader is SRP-incompatible — [Unity Manual: GPU instancing](https://docs.unity3d.com/6000.0/Documentation/Manual/GPUInstancing.html) (re-verified). So classic instancing is *not* the path here.
- **GPU Resident Drawer (currently off):** requires Forward+ (the project uses it), compute-shader platforms except OpenGL ES, Mesh Renderer GameObjects; falls back to non-instanced drawing otherwise; longer builds (all BRG variants); "most effective" when many GameObjects share the same mesh; updates when GameObjects are created/changed — [Unity Manual: GPU Resident Drawer](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html). This *exactly* matches "copy-paste" piles (40 identical chairs) on Metal. **Not available on WebGL** (no compute) → it must stay an optional quality setting. Test on the Mac: enable GRD + disable static batching in Player settings as Unity suggests, compare frame time in the pile room.
- **Static batching at runtime:** `StaticBatchingUtility.Combine(root)` combines non-moving meshes; children cannot move afterwards, but the root can — [Unity ScriptReference](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/StaticBatchingUtility.Combine.html) (prior run). Requires readable meshes (Read/Write enabled) — costs CPU memory per combined copy. With recycled rooms, combine **once per built pile** (root = pile root) and destroy with the room. Not compatible with GRD (GRD wants it off).
- **Mesh.CombineMeshes:** merge by material (`mergeSubMeshes=true` per material) into one mesh per material per pile — [Unity ScriptReference](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh.CombineMeshes.html) (prior run). 16-bit index meshes support up to 65,535 vertices; 32-bit indices are not guaranteed on all GPUs — [Unity ScriptReference: Mesh.indexFormat](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh-indexFormat.html). A 25-piece pile at ~3–8 k tris per piece will exceed 65 k verts → set `IndexFormat.UInt32` (fine on Apple GPUs and WebGL2) or split by material.
- **Decision for this project:** default path = **shared prefab meshes + SRP Batcher + per-pile `StaticBatchingUtility.Combine`** (works on Mac and WebGL). Quality path on Mac = **GRD on, static batching off**. Avoid runtime `CombineMeshes` unless profiling shows CPU-bound draw submission; it doubles memory per pile and kills culling granularity.
- **LOD:** `LODGroup` swaps meshes by screen size; each LOD is a separate renderer GameObject — [Unity Manual: LOD](https://docs.unity3d.com/6000.0/Documentation/Manual/LevelOfDetail.html) (prior run). Rooms are ≤ 12–36 m deep and the pile is a landmark seen from far; budget LOD0 ≤ 8 k tris per piece, LOD1 ~35 %, cull small satellites at 5 % screen height. Shadows: set pile satellites to `ShadowCastingMode.Off`; point/spot shadow casting is expensive because casters may render into every cubemap face — [Unity Manual: shadow mapping](https://docs.unity3d.com/2022.1/Documentation/Manual/shadow-mapping.html) (prior run, 2022.1 page).

### 6.9 Deterministic seeding for recycled rooms

- `UnityEngine.Random` "is a static class, and so its state is globally shared" — [Unity ScriptReference: Random](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Random.html) (prior run). Any other system calling it between rooms changes the pile → **never use it in generators**.
- `System.Random`: Microsoft warns seeded sequences "may produce different sequences … on different versions of .NET" — [Microsoft Learn: System.Random](https://learn.microsoft.com/en-us/dotnet/api/system.random) (prior run). Unity's Mono vs IL2CPP/WebGL builds may differ → avoid for saved/shared seeds.
- **Use `Unity.Mathematics.Random`** (package 1.3.2 is already in `Packages/packages-lock.json`): xorshift, 32-bit state, seed must be non-zero, `CreateFromIndex(uint)` hashes an index — [Unity Mathematics API](https://docs.unity3d.com/Packages/com.unity.mathematics@1.3/api/Unity.Mathematics.Random.html). Or reuse the project's `MapHash.Hash/Unit` (integer hash in `FrontRoomsMap.cs` line 163–192) for a counter-based RNG.
- **Sub-streams:** derive independent seeds per decision (`tableau`, `piece choice`, `orientation`, `satellites`) as `Hash(seed, stepIndex, salt)` so adding a satellite does not reshuffle the whole pile. Never iterate a `Dictionary`/`HashSet` during generation (order is unspecified); iterate arrays sorted by stable keys.
- **Float determinism:** the solver uses only +, −, ×, comparisons and `Quaternion.Euler` of quantised angles; avoid accumulating transforms through `Transform` hierarchy reads (`TransformPoint`) mid-solve — keep pile-space maths in plain structs, assign transforms at the end.
- **Test:** build the same seed twice in EditMode tests and hash all resulting `localPosition/localRotation` rounded to 1 mm / 0.1° — must match; run on Mac Editor and a WebGL build.

### 6.10 Readability: "nothing broken, just wrong"

Rules distilled from §1–4:
1. **Intact pieces only.** No fractures, no missing legs, no melted meshes, no dirt *on* the furniture beyond its normal wear. The wrongness is in arrangement, count and location.
2. **Recognition before distortion.** At least 60 % of each piece's silhouette must be visible from the main approach. Hidden pieces are wasted triangles.
3. **Quantised, legible orientations** (upright, 90°, 180°, 35–50° edge-lean). Avoid 3–15° "drunk" tilts (they read as bugs — cf. Exit 8 poster).
4. **Upright reading of the whole:** the pile's centre of mass sits over its footprint; it looks *stable*, as if pasted, not about to fall. No piece's centre of mass may hang outside its support polygon by more than 25 % of its width unless it is jammed by another piece (contact on both sides).
5. **Material contrast:** ≥ 4 material families and ≥ 2 value groups (dark wood/black CRT vs pale upholstery/beige steel) so pieces separate under flat overhead light.
6. **Duplicates must be *exact*.** Same mesh, same material, same wear. (Set Set: identical hotel stock.) A copy with a different tint reads as "another chair", not as a paste.
7. **One escalation axis per room**: count (copy-paste rows), height (ceiling-sweeping), or embedding (wall/ceiling) — not all three at once, except in the deepest zone.
8. **Clean surroundings:** a ring of empty floor and normal room dressing keeps the pile the only wrong thing — "just wrong".

### 6.11 Gameplay roles

| Role | Mechanism | Generator parameter |
|---|---|---|
| **Landmark for navigation** | Unique, deterministic composition per room seed; distinctive top silhouette (sofa, torchiere, CRT) visible over cubicle height (1.5 m). | `spikePiece`, `topPiece` chosen from a per-zone palette so each zone has a "signature" topper. |
| **Line-of-sight blocker in chases** | Blocker boxes ≥ 1.7 m; Hunter `Visible()` raycast blocked. Player can circle the pile to break pursuit. | `losBlock = true` → guarantee one 2.2 m-wide opaque face. |
| **Hiding spot** | Hollow under inverted desk/table or behind a sofa on its back; trigger volume. | `hideSlot` template slot; only in ≤ 30 % of piles so it stays a discovery. |
| **Obstacle course / choke** | *Copy-paste row* or *Wall-embedded* tableau narrows a corridor to 0.9–1.2 m. | Must never fully block: verify a 0.8 m capsule path between all `keepClear` doors. |
| **Escalation clock** | Pile intensity rises with depth/time (ELLE Decor's drab → ceiling-sweeping). | `intensity = f(zone depth)` → piece count, height ratio, operator mix. |
| **Diegetic clue** | Countable composition (Escape the Backrooms Level 5 idea): e.g. number of inverted chairs = number of the correct exit. | Optional; data-only. |

## 7. Generator design: `FrontRoomsFurniturePile.Build(parent, localCenter, radius, ceilingHeight, seed)`

Design goals (from §1–6): intact recognisable pieces · quantised legible orientations · exact duplicates · centred landmark with a clear ring · height up to ~0.9 × ceiling · analytic deterministic solver (no runtime physics) · shared meshes/materials · blocker colliders + Hunter cell blocking · decal grounding.

### 7.1 Piece library schema

Reuse the sidecar that `FrontRoomsKitLibrary.Info` already parses (`boundsMin/Max`, `supports[]`, `colliders[]`, `anchors[]`, `tags[]`, `slots[]`, `triangles`; front = +Z, stands on y = 0). Add an optional `pile` block in the same JSON (written by `kitlib.py`), with defaults derived from tags when absent:

```jsonc
"pile": {
  "class": "Case",            // Seat | Table | Case | Soft | Tall | Screen | Crate | Small
  "mass": 2,                  // 0 light .. 3 heavy  → base vs top choice
  "states": ["Upright","Back","EdgeLean"],   // allowed rest states (quantised)
  "pierceable": true,         // may be embedded in wall/ceiling/floor
  "tolerance": 0.25,          // max fraction of own volume allowed inside others
  "cavities": [ { "centre":[0,0.45,0.05], "size":[0.8,0.6,0.4] } ],  // Nest targets (shelf bays, under-desk)
  "palette": "domestic70s",   // domestic70s | office90s | storage | hotel
  "topper": false             // good silhouette for the top of a landmark (sofa, CRT, torchiere)
}
```

Defaults by class (tune by eye):

| class | examples (Still A/B + office) | states | tolerance | mass |
|---|---|---|---|---|
| Seat | ladder-back chair, bar stool, task chair, Queen-Anne armchair | Upright, Inverted, Side, Back | 0.45 (open frames hide intersections) | 0–1 |
| Table | side table, desk, coffee table | Upright, Inverted, Side | 0.35 | 1–2 |
| Case | dresser, hutch, filing cabinet, sideboard, bookshelf, display cabinet | Upright, Back, Side, EdgeLean | 0.20 | 2–3 |
| Soft | sofa, club chair | Upright, Back, Side | 0.30 | 2 |
| Tall | torchiere, table lamp, hatstand | Upright only (Spike) | 0.30 | 0 |
| Screen | CRT TV, monitor | Upright, Side, Front | 0.15 | 1 |
| Crate | crate, pallet, boxes | Upright, Side | 0.20 | 1–2 |
| Small | paper stack, shoe, cassette, phone | any | 0.5 | 0 |

Rest pose per state is computed, not authored: `Upright` = identity; `Back` = −90° about X (rests on its back face); `Front` = +90° X; `Side` = ±90° about Z; `Inverted` = 180° about X; `EdgeLean` = solved angle 30–52° about a bottom edge (§7.2). After rotation, re-ground using the rotated bounds' min y.

Minimum library to look like Still A/B (≥ 14 meshes): 2 chairs (ladder-back, bar stool), 1 upholstered armchair, 1 club chair, 1 sofa, 1 dresser, 1 hutch/cabinet, 1 filing cabinet, 1 bookshelf, 1 side table, 1 desk, 1 CRT TV, 1 torchiere, 1 table lamp, 1 crate + pallet. Sourcing of these is covered by the model-sourcing report; the pile code must degrade gracefully if only office pieces exist.

### 7.2 Placement solver (pseudo-code)

```csharp
public static class FrontRoomsFurniturePile
{
    // Signature required by FrontRoomsMapWorld (reflection matches on name + parameter types;
    // the return type is free, so returning the footprint is compatible).
    public static Bounds Build(Transform parent, Vector3 localCenter, float radius, float ceilingHeight, int seed)
        => Build(parent, localCenter, radius, ceilingHeight, seed, PileContext.Probe(parent, localCenter, radius));

    public static Bounds Build(Transform parent, Vector3 c, float R, float H, int seed, PileContext ctx)
    {
        var rng   = new PileRng((uint)seed);                      // counter-based: rng.U(stream, i, j)
        var lib   = PileLibrary.Available();                      // cached Info list, sorted by name (stable order)
        if (lib.Count < 4) return Bounds.zero;                    // never throw inside Furnish

        var t     = Tableaux.Choose(rng, R, H, ctx);              // §7.3, weighted by ctx.zoneTheme / depth / wall presence
        var plan  = new PilePlan(c, R, H, t, ctx) {
            Hmax        = Mathf.Min(H - t.ceilingClearance, t.heightRatio * H),   // e.g. 0.92·H, clearance .06 m
            volBudget   = t.globalOverlap,                         // e.g. 0.20 of summed piece volume
            ringClear   = t.ringClear                              // empty floor ring beyond R (decal only)
        };

        for (int s = 0; s < t.slots.Length; s++)                   // slots ordered base → mid → top → spike → satellites
        {
            var slot = t.slots[s];
            for (int k = 0; k < slot.count.Pick(rng, s); k++)
            for (int attempt = 0; attempt < 10; attempt++)
            {
                var piece = lib.Pick(slot.filter, rng.U(1, s*64+k, attempt));       // tags, class, size range, palette
                var state = slot.states.Intersect(piece.States).Pick(rng.U(2, s*64+k, attempt));
                if (!Ops.TryPlace(slot.op, piece, state, plan, rng.Sub(3, s*64+k, attempt), out Pose pose)) continue;
                if (!Validate(piece, pose, plan)) continue;
                plan.Commit(piece, pose, slot);
                if (slot.copyPaste.count > 0) Ops.CopyPaste(plan, plan.Last, slot.copyPaste, rng.Sub(4, s*64+k));
                break;                                              // slot satisfied
            }
        }

        Ops.ResolveCoplanar(plan);          // §6.4: nudge 8–15 mm / rotate 3–5° where faces are parallel & touching
        Ops.EnsureStable(plan);             // drop pieces whose COM hangs > 25 % outside support without a second contact
        var root = Emit(parent, plan);      // FrontRoomsKitLibrary.Spawn(..., colliders:false) for each committed pose
        Colliders.BuildBlockers(root, plan);// 2–4 BoxColliders from convex XZ hull, height ≥ 1.8 m; keep piece boxes > 0.4 m
        Grounding.AddDecals(root, plan);    // dust ring 1.2× footprint + scuffs under EdgeLean pieces; blob quad fallback
        if (t.hideSpot) Gameplay.AddHideTrigger(root, plan);
        if (PileSettings.StaticCombine) StaticBatchingUtility.Combine(root);       // Standalone default; GRD mode skips
        return plan.FootprintBoundsLocal();  // caller marks Hunter cells impassable (FrontRoomsMapWorld)
    }

    static bool Validate(PieceInfo p, Pose pose, PilePlan plan)
    {
        var obb = p.WorldObb(pose);
        if (!plan.InsideRadius(obb, p.cls == Small ? 1.0f : 0.92f)) return false;   // XZ corners ≤ R
        if (obb.MaxY > plan.Hmax && !plan.t.allowCeilingPierce) return false;
        if (obb.MinY < -0.02f && !plan.slotAllowsFloorSink) return false;
        if (plan.ctx.KeepClearHit(obb.FootprintXZ)) return false;                   // doors / chase lanes
        if (!plan.Supported(obb, pose.state)) return false;                          // rest face on floor/support (≤ 1 cm) or 2 contacts for EdgeLean
        float own = 0f;
        foreach (var q in plan.Committed)
        {
            float f = ObbOverlapFraction(obb, q.obb);             // SAT reject, then clipped-AABB volume estimate
            if (f > 0.80f && !plan.IsNestPair(p, q)) return false; // never fully swallow a piece
            if (!plan.IsCopyPair(p, q)) own += f;                 // copy-paste pairs have their own budget
        }
        if (own > p.tolerance) return false;
        return plan.GlobalOverlapAfter(obb) <= plan.volBudget;
    }
}
```

Key operator details (`Ops.TryPlace`):

```text
Base          : pos = c + polar(r = U·0.35R, θ = U·360°); yaw = {0,90,180,270}[i] + U(−12°,12°); state Upright|Back.
StackOnSupport: choose committed q with an up-facing support (normal·up > 0.86) whose height + p.height ≤ Hmax;
                point = random inside support rect shrunk by 0.15·p.width; allow ≤ 25 % overhang; yaw quantised ± 20°.
TipOnEdge     : stand p next to neighbour q (gap 2 cm), hinge = p's bottom edge nearest q;
                bisection on θ ∈ [25°, 55°] for first contact with q (OBB SAT), then θ += U(2°, 6°) "jam";
                reject if θ ∉ [30°, 52°]  →  reads as deliberate, never as 'drunk'.
Invert        : state Inverted (180° X ± 2°), place on floor or a support exactly like StackOnSupport.
SideLay       : state Side (±90° Z), on floor or support.
CopyPaste(n)  : axis a = one local axis of the source (chosen once), step d = size_a · U(0.12, 0.45);
                each copy_i = copy_{i−1} ⊕ (d·a + up·U(0.01, 0.04)), yawStep ∈ {0°, 0°, 7°, 15°, 90°} chosen once.
                Same mesh + same material. Copies may overlap the source up to 0.45; Validate() skips own-copy pairs.
Splice        : same class, different asset, end-to-end along the long axis, overlap 15–40 % of the shorter;
                top-height mismatch 2–8 cm on purpose (Salcedo seam; also prevents coplanar tops).
Nest          : pick a cavity of q; place small p (Seat/Screen/Small) with centre inside the cavity, any allowed state.
Spike         : highest stable support; Tall piece Upright, tilt ≤ 8°; top ≤ Hmax (or ≤ H + 0.12 if ceiling-pierce tableau).
Pierce        : requires ctx.wall (plane n,d) or ceiling; embed depth ∈ [0.25, 0.6]·depth_of_piece but ≤ wallThickness − 0.02
                (FrontRoomsMapWorld WallThickness = 0.16 m) so nothing appears in the next room; ceiling embed ≤ 0.12 m.
Satellite     : 4–10 Small pieces on the floor ring [0.7R, 1.0R], Upright/Side, no colliders, shadows off.
```

Interpenetration budget summary: per piece `tolerance` (by class), copy-paste pairs ≤ 0.45, nest pairs ≤ 0.70, nothing > 0.80 swallowed, global ≤ 0.20 of summed volume. OBB–OBB tests use the 15-axis separating-axis test from the OBBTree literature ([Gottschalk et al. 1996, OBBTree](https://www.cs.cornell.edu/courses/cs667/2005sp/readings/gottschalk96.pdf) — search result, not fetched; the 15-axis SAT is standard).

`PileContext.Probe` (used by the 5-arg overload): cast 8 horizontal rays from `c + up·1.2` up to `R + 1.5 m` to find a wall plane for Pierce tableaux, and read zone height class from `ceilingHeight` (≈2.4/2.9/5.4). Raycasts against colliders created earlier in the same frame may need `Physics.SyncTransforms()` first (UNVERIFIED for this project's spawn order) — the cleaner fix is a 6-arg overload where `FrontRoomsMapWorld` passes walls + `KeepClear(...)` rects (it already computes them for `Dress`).

### 7.3 Tableau variants

Each tableau = ordered slot list + parameters. Counts scale with `R` (2.64–3.2 m from the map) and the zone's ceiling.

| Tableau | Intent / reference | Slots (op × count) | Height | Placement & gameplay | Weight |
|---|---|---|---|---|---|
| **Centre sculpture** | Still A/B; film's first Backrooms room; Kawamata + Salcedo | Base×2–3 (Case/Soft/Crate, mass ≥ 2) · TipOnEdge×2 (Case) · StackOnSupport×4–6 (mixed) · Invert×2–3 (Seat/Table) · CopyPaste run 3–4 of one Seat · Nest×1 · Spike×1 (Tall) · Topper×1 (Soft/Screen) · Satellite×6 | 0.88–0.95·H (2.9 m zone ≈ 2.6 m, like Still B) | Room centroid; ring of 2–3 m empty floor; landmark + LOS blocker; 30 % chance of hide hollow | 40 % |
| **Wall-embedded** | ELLE Decor "no clip"; Moria "furniture buried in walls"; Kawamata *Avalanche* spill | Pierce×2–3 (Case/Soft into wall) · StackOnSupport×3 · CopyPaste run 2–3 · Satellite×4 · density falls off with distance from wall | 0.6–0.8·H | Needs `ctx.wall`; footprint = half-disc of R against the wall; never on a wall with a door/window within 1.5 m | 20 % |
| **Copy-paste row** | Set Set's 40 identical chairs / 20 sofas; Ai Weiwei *Grapes*; Salcedo Istanbul | Base×1 (one asset) · CopyPaste run 6–14 along a line or arc (step 0.25–0.45·width, yawStep 0/7°) · optional second row Inverted on top | 0.4–0.8·H | Along a wall, or across a corridor leaving ≥ 1.0 m gap (choke). One mesh → cheapest tableau (GRD/instancing friendly) | 15 % |
| **Ceiling-stuck** | Still B "nearly touching the ceiling"; gravity-wrong but intact | Column: CopyPaste of one Seat/Crate stacked floor→ceiling (6–10, each Invert/Upright alternating) · 1–2 Invert pieces embedded ≤ 0.12 m into the ceiling grid + ceiling-tile cut-ring trim mesh | H (touches) | Best in 2.4 m zones where the ceiling is in view; avoid 5.4 m halls (pieces too far up to read) | 10 % |
| **Tilted office cluster** | Replaces Codex's memory bleed; office reading of the same rule | One full workstation (desk + CRT + task chair + cubicle panel) copy-pasted 2–3×, each copy rotated 90° (SideLay) or EdgeLean 35–45° onto the previous; papers as satellites | ≤ 2.0 m | Office zones only, outside `Dress` keepClear; never in the chase lane; reads as "the workstation was pasted three times" | 10 % (office only) |
| *Zero pile* (bonus) | POOLS: one perfect chair in a huge room | 1 Seat Upright, centred, exact axis-aligned; satellite: none | — | Tall 5.4 m halls; cheap; makes the next real pile hit harder | 5 % |

Escalation: `intensity ∈ [0,1]` from maze depth or run time multiplies slot counts (0.6× → 1.3×), `heightRatio` (0.6 → 0.95) and unlocks Wall-embedded/Ceiling-stuck only above 0.5 — mirroring ELLE Decor's "begins as merely drab, but culminates" structure.

### 7.4 Integration with the maze / room train

- **Map (`FrontRoomsMapWorld.Furnish`)**: keep the reflection call, but (1) consume the returned `Bounds` and mark the overlapped 3 m cells impassable for `FrontRoomsMapHunter` BFS — otherwise the Hunter's `MoveTowards` walks straight through the pile (§6.7); (2) pass `KeepClear(data, room)` to the pile as well (currently only `Dress` gets it); (3) prefer piles in rooms whose centroid is on a line between two openings (landmark visibility).
- **Room train (11.5 × 12 × 2.9 m)**: radius 2.4–2.6 m, centre at the room centroid leaves ≥ 3.1 m on each side for the chase lane; or offset to one third and use Wall-embedded. Seed = stream sequence hash (the existing `Hash(sequence, salt)` pattern) so recycled rooms reproduce.
- **Office level**: `FrontRoomsOfficeKit.Dress` owns normal workstations; it may call `FrontRoomsFurniturePile.Build` with the *Tilted office cluster* tableau for at most one cluster per room, outside `keepClear`.
- **Offline hero piles**: `Tools/Blender/frontrooms_kit/pile_bake.py` (proposed) builds 1–2 hand-composed tableaux, runs a short rigid-body settle on 2–4 free pieces (operators verified in §6.2), applies visual transforms and exports `Resources/Props/Piles/<name>.json` (asset name + local pose per piece). `Build` treats a baked tableau as a template with fixed poses; the seed only picks yaw (0/90/180/270), mirror and material variant of the whole pile.
- **Recycling**: build per room, destroy with the room; `Info`, materials and decals are cached statically; no per-pile materials, no MaterialPropertyBlocks.

### 7.5 Acceptance tests

1. **Determinism** (EditMode test): `Build` twice with the same seed into two roots → identical list of (asset, pos rounded 1 mm, euler rounded 0.1°). Also run in a WebGL build once.
2. **Bounds**: 1,000 seeds × {R 2.4, 2.64, 3.2} × {H 2.4, 2.9, 5.4}: every OBB inside R (XZ) and ≤ Hmax (except pierce tableaux), nothing below floor unless FloorSink.
3. **Stability/readability**: every committed piece supported; ≥ 60 % of pieces have their centre visible (raycast) from at least one of the room's door positions at 1.6 m eye height.
4. **Path**: a 0.8 m capsule path exists between all room openings (0.25 m occupancy grid BFS) and the Hunter cell mask matches the footprint.
5. **Z-fight lint**: no pair of committed boxes with parallel faces (< 2°) closer than 3 mm with overlapping projections.
6. **Performance (Mac Editor + build)**: pile build ≤ 5 ms; ≤ 60 SRP batches added per pile; ≤ 200 k triangles per pile at LOD0 (targets are proposals — UNVERIFIED until profiled).
7. **Look-dev capture**: add `Verification/lookdev/pile_<tableau>_<seed>.png` frames from the door at eye level, judged against Still A/B descriptions and the target office image for grade/lighting.

## 8. Sources

**Film production (re-verified this run)**
- The Set Set — Trevor Johnston interview: https://thesetset.com/articles/backrooms-set-decorator-trevor-johnston-interview
- ELLE Decor via AOL — "The Meaning Behind the Surreal Sets of A24's Backrooms": https://www.aol.com/articles/meaning-behind-surreal-sets-a24-195154000.html
- A24 Notes — Thirty Thousand Square Feet with Kane Parsons & James Wan: https://a24films.com/notes/2026/05/thirty-thousand-square-feet-with-kane-parsons-james-wan
- Wikipedia — Backrooms (web series): https://en.wikipedia.org/wiki/Backrooms_(web_series)

**Film production / reviews (prior run, not re-fetched)**
- Film and Furniture: https://filmandfurniture.com/2026/06/backrooms-the-furniture-film-of-the-year/
- Wikipedia — Backrooms (film): https://en.wikipedia.org/wiki/Backrooms_(film)
- The Credits (MPA) — Vermette interview: https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/
- Moria Reviews: https://moriareviews.com/sciencefiction/backrooms-2026.htm
- BFI Sight and Sound: https://www.bfi.org.uk/sight-and-sound/reviews/backrooms-kane-parsons-turns-internet-mythology-into-unsettling-inventive-horror
- KQED: https://www.kqed.org/arts/13990220/backrooms-movie-review-a24-liminal-space-horror
- Taylor Holmes explainer eps 18–22 (secondary, re-fetched): https://taylorholmes.com/2026/06/02/explaining-the-backrooms-youtube-episodes-18-22/
- Blocked/unfetchable: Fast Company, Dezeen, IndieWire, Curbed, GoldDerby VFX interview (https://www.goldderby.com/film/2026/backrooms-vfx-explainer-interview-trickiest-shots-easter-eggs/), VIEW Conference abstract (https://www.viewconference.it/article/1256/from-youtube-to-hollywood-the-vfx-of-a24s-backrooms?amphtml=1 — fetched, abstract only).

**Art references**
- Tate Papers 01 (Salcedo, *Unland*/*Untitled*) — re-verified: https://tate.org.uk/research/tate-papers/01/unland-the-place-of-testimony
- Istanbul Modern (Salcedo Istanbul project) — re-verified: https://www.istanbulmodern.org/en/collection/istanbul-project-i
- Museum Voorlinden (Michael Johansson) — re-verified: https://www.voorlinden.nl/exhibition/michael-johansson/?lang=en
- De Pont Museum (Ai Weiwei *Grapes*) — re-verified: https://www.depont.nl/en/collection/artists/weiwei-ai/grapes
- designboom (Kawamata *Avalanche*) — re-verified: https://www.designboom.com/art/avalanche-tadashi-kawamata-phileo-dover-street-market-paris-10-07-2024/
- Prior run: Guggenheim Bilbao (Salcedo) https://guggenheim-bilbao.eus/en/exhibition/doris-salcedo · Public Delivery https://publicdelivery.org/doris-salcedo-chairs/ · Inhabitat (Johansson) https://inhabitat.com/michael-johanssons-precisely-stacked-sculptures-give-found-objects-the-tetris-treatment/ · Victoria Miro (Sze) https://victoria-miro.com/exhibitions/380 · Islamic Arts Magazine (Kawamata Abu Dhabi, snippet only) https://islamicartsmagazine.com/magazine/view/an_art_work_of_hundreds_of_chairs_begins_creation_this_week_for_abu_dh/

**Games**
- GameSpew POOLS review — re-verified: https://www.gamespew.com/2024/04/pools-review-a-liminal-hidden-gem/
- gameplay.tips Escape the Backrooms levels — re-verified: https://gameplay.tips/guides/escape-the-backrooms-all-levels-guide.html
- Steam The Exit 8 (prior run): https://store.steampowered.com/app/2653790/The_Exit_8/
- Automaton (Exit 8 poster anomaly; fetch truncated): https://automaton-media.com/en/news/20231208-23845/
- Steam Inside the Backrooms (search summary): https://store.steampowered.com/app/1987080/
- TechRadar Backrooms games (search summary): https://www.techradar.com/news/best-backrooms-games-no-clipping-has-never-been-more-fun-or-terrifying
- TechRaptor Anemoiapolis (403): https://techraptor.net/gaming/reviews/anemoiapolis-chapter-1-review

**Unity / Blender / maths (re-verified this run unless noted)**
- Physics.Simulate: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Physics.Simulate.html
- Physics.ComputePenetration: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Physics.ComputePenetration.html
- Transform (non-uniform scale shear): https://docs.unity3d.com/6000.0/Documentation/Manual/class-Transform.html
- GPU Resident Drawer: https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html
- GPU instancing vs SRP Batcher: https://docs.unity3d.com/6000.0/Documentation/Manual/GPUInstancing.html
- MaterialPropertyBlock vs SRP Batcher: https://docs.unity3d.com/6/Documentation/Manual/DrawCallBatching-Properties.html
- Mesh.indexFormat: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh-indexFormat.html
- SSAO reference: https://docs.unity3d.com/6000.0/Documentation/Manual/urp/ssao-renderer-feature-reference.html
- Decal reference: https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-feature-decal-reference.html
- NavMesh Obstacle (AI Navigation 2.0): https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshObstacle.html
- Unity.Mathematics.Random: https://docs.unity3d.com/Packages/com.unity.mathematics@1.3/api/Unity.Mathematics.Random.html
- Prior run: SRP Batcher https://docs.unity3d.com/6000.0/Documentation/Manual/SRPBatcher.html · StaticBatchingUtility.Combine https://docs.unity3d.com/6000.0/Documentation/ScriptReference/StaticBatchingUtility.Combine.html · Mesh.CombineMeshes https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh.CombineMeshes.html · Mesh Collider https://docs.unity3d.com/6000.0/Documentation/Manual/class-MeshCollider.html · Mesh colliders intro https://docs.unity3d.com/6000.0/Documentation/Manual/mesh-colliders-introduction.html · Decal feature https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-feature-decal.html · Render Objects https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-features/how-to-custom-effect-render-objects.html · ShaderLab Offset https://docs.unity3d.com/6000.0/Documentation/Manual/SL-Offset.html · LOD https://docs.unity3d.com/6000.0/Documentation/Manual/LevelOfDetail.html · Random https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Random.html · shadow mapping (2022.1) https://docs.unity3d.com/2022.1/Documentation/Manual/shadow-mapping.html · System.Random https://learn.microsoft.com/en-us/dotnet/api/system.random
- Blender 4.3 rigid-body operators: verified locally with `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python` (probe script in the session scratchpad, `blender_probe.py`), Blender 4.3.0 hash 2b18cad88b13.
- Gottschalk et al. 1996, OBBTree (search result): https://www.cs.cornell.edu/courses/cs667/2005sp/readings/gottschalk96.pdf

**Repository files read**
- `Frontrooms3D/Assets/Scripts/FrontRoomsOfficeFurniture.cs` (BuildMemoryBleed, lines 142–218)
- `Frontrooms3D/Assets/Scripts/Office/FrontRoomsKitLibrary.cs` (sidecar schema; new, 2026-10-02 15:00)
- `Frontrooms3D/Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs` (Furnish / KeepClear, lines ~759–850)
- `Frontrooms3D/Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs` (BFS + MoveTowards line 293; Visible() raycast line 331)
- `Frontrooms3D/Assets/Settings/FrontRooms_URP.asset`, `FrontRooms_URP_Renderer.asset`, `ProjectSettings/ProjectSettings.asset`, `Packages/packages-lock.json`
- `Frontrooms3D/Documentation/OFFICE_LEVEL_FURNITURE_RESEARCH.md`, `Verification/lookdev/2_Office_forward.png`, `2_Office_back.png`

## 9. Open questions / UNVERIFIED items

- **How the film's piles were physically secured** (screws, armatures, glue) — no fetched source says; the A24 Blu-ray "prop walkthrough" / "Building the Backrooms" extras would answer it (UNVERIFIED).
- **Which film shots were VFX-distorted vs practical** — Set Set says some scanned props were digitally distorted; no shot list found.
- **Edit-mode `Physics.Simulate`** is not documented in 6000.0 docs; test before building an editor settle tool (Blender bake is the verified alternative).
- **URP contact shadows**: none found in URP docs (negative claim, UNVERIFIED).
- **Exit 8 poster anomaly / Inside the Backrooms / Backrooms 1998 / Anemoiapolis** details rest on search summaries, not fetched pages.
- **Does `FrontRoomsMapWorld` build walls/colliders before `Furnish`?** Needed for `PileContext.Probe` raycasts; prefer passing walls/keepClear explicitly.
- **Hunter cell blocking API**: `MapGrid.Passable` is edge-based; marking pile cells requires a new per-cell "blocked" flag — design decision for whoever owns the map code (check Codex activity first).
- **Performance targets** in §7.5 are proposals; profile on Red's Mac (GRD on/off, static combine on/off) in the pile room.
- **Library availability**: the Blender kit (`Tools/Blender/frontrooms_kit`) is mid-construction (only `axis_probe.py` in `assets/` at time of reading); the pile needs ≥14 meshes across 8 classes to match Still A/B — depends on the model-sourcing report.
- **FBX root scale**: Codex's office FBX need `scale * 100f`; confirm the new kit exports at unit scale (`FrontRoomsKitLibrary.Spawn` assumes `Vector3.one`).
