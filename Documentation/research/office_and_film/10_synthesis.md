# 10 — Synthesis: FrontRooms Office level and furniture piles (decision document)

Status: COMPLETE, 2026-10-02. Lead-TA synthesis of reports 01–06. **Critic pass applied at about 15:45 the same day.** Corrections are inline and tagged **[critic]**. Items that could not be verified are tagged **[UNVERIFIED]**. Open gaps are listed in "Critic notes" at the end.

**Read this first [critic].** `Frontrooms3D/Documentation/LEVEL_MODULE_SPEC.md` (map chat, 15:35) is now the binding contract for sizes, clearances and budgets. Where this document disagrees with it, the spec wins until both chats agree on a change. The disagreements are marked inline and collected in Critic notes C1. The most important ones:
- Office rooms are Standard height (2.9 m) only, 6, 9 or 12 m a side.
- Each dressed room is capped at **≤ 60k tris, ≤ 120 renderers, ≤ 40 colliders and ≤ 3 ms**.
- Office columns are 0.61 m, with at most 1 in a 9 m room and 4 in a 12 m room.
- Props keep 0.05 m under the ceiling.

**Inputs.** All six reports were present and read in full:

| Report | File | Size |
|---|---|---|
| Film production | `01_film_production.md` | 51 KB |
| Film shots | `02_film_shots.md` | 62 KB |
| IP canon | `03_ip_canon.md` | 52 KB |
| Model sourcing | `04_model_sourcing.md` | 129 KB; the raw API appendices were skimmed |
| Texture sourcing | `05_texture_sourcing.md` | 52 KB |
| Distortion tech | `06_distortion_tech.md` | 74 KB |

No researcher failed. The `prior/` folder holds the interrupted run. It was not used, because every report already re-verified or flagged its claims.

**Calibration.**
- Viewed `ref_office_target.png`. Region colours were sampled numerically (§6.9).
- Viewed the look-dev frames `2_Office_forward.png` and `2_Office_back.png`, plus the old Codex hero crop.
- Viewed the parallel kit session's first asset: `Kit_CRTMonitor` in Cycles and in-engine (`kitprev/`, `kl_crt.jpg`, `kl_lineup.jpg`).

**Project state, checked in code on 2026-10-02 at about 15:15.**
- A Blender kit pipeline exists: `Tools/Blender/frontrooms_kit/kitlib.py` plus one Python module per asset. It exports FBX plus a JSON sidecar, with one material slot per submesh named `Prop_*`, and metre UVs.
- One asset is exported so far: `Kit_CRTMonitor`.
- `FrontRoomsOfficeKit.Dress(...)` (338 lines) and `FrontRoomsFurniturePile.Build(...)` (621 lines) are already written by the parallel session. `Dress` uses `Aisle = 1.6f` and 16 named `Kit_*` assets. `Build` has the tableaux `CentreSculpture`, `CopyPasteRow`, `CeilingStuck`, `OfficeCluster` and `ZeroPile`, with the rest states `Upright`, `Back`, `Front`, `Side`, `Inverted` and `EdgeLean`.
- `FrontRoomsMapWorld.Furnish` calls both generators by reflection.

**[critic] Re-checked at about 15:40. The code moved after the 15:15 snapshot.**
- `FrontRoomsOfficeKit.cs` is now 597 lines and declares 17 `Kit_*` names, not 16.
  - It reserves keepClear strips expanded by **0.25 m**, not 0.35.
  - Columns are 0.61 m, with 1–4 per room.
  - Its header records Red's direction: "a maze of walls, not a pillar hall".
- **18 kit modules now exist** in `Tools/Blender/frontrooms_kit/assets/` and are exported in the private copy (`scratchpad/proj/Assets/Resources/Props/Models`). Only `Kit_CRTMonitor` is promoted into the real project.
  - The live names differ from this document: **`Kit_Dresser70s`** (this doc: `Kit_Chest5`) and **`Kit_TableLampPleated`** (this doc: `Kit_LampPleated`).
  - `Kit_Crate` is also built, ahead of its Day 2 slot in §5.5, at 0.90 × 0.60 × 0.70 against the 1.00 × 0.80 × 0.75 spec.
  - The live meshes exceed this document's triangle budgets by up to 13× (only the CRT is on budget) and its ≤ 4-slot rule (§5.3, Critic notes C3).
- `Tools/Blender/frontrooms_kit/ingest_cc0.py` (288 lines, 15:25) already exists. It imports Poly Haven models and **keeps their own textures and UVs**: it writes `PH_<asset>_*` maps and appends to `materials_manifest.json`. This conflicts with decision 1 ("re-UV onto kit slots") and replaces the proposed `import_cc0.py` (§2.3).
- `FrontRoomsMapHunter` (15:31) **no longer walks through props**.
  - It capsule-casts and slides along props.
  - After 0.5 s blocked it sidesteps. After 1.4 s it ghosts through furniture (never walls) for 0.8 s.
  - R1 and decision 7 are rewritten below.
- `FrontRoomsSurfaces.OfficeLouver` (15:24) now returns `Troffer_Lens`, the Level 0 lens. That lens is still the **prismatic** `lens()` with tube stripes from `gen_surfaces.py`, despite the code comment saying "opal". The flat opal lens of decision 4 is still not built.
- **This document targets that code and those asset names.** It does not propose a parallel system. Per the project memory, check the parallel session's and Codex's activity before editing any of these files.

---

## 0. Decisions on one page

1. **One kit, built in Blender by our own scripts (kitlib), textured with downloaded CC0 scans.**
   - 45 of 46 assets are modelled in kitlib (one of them, the CRT, is already done). Only **one model is downloaded**: Poly Haven `GreenChair_01` (CC0), which stands in for the Queen-Anne/bergère chair. Its geometry is re-UV'd onto kit slots.
   - Every material is a shared `Prop_*` slot fed by **CC0 textures** from Poly Haven and ambientCG.
   - Sketchfab CC-BY models are **fallbacks only**. They are downloaded only if a quality gate fails (§2.3-F).
   - Why: the pile's whole effect is "the same catalogue pasted again". A patchwork of six authors' texturing styles breaks that. kitlib already gives correct dimensions, sidecars, colliders and pile metadata for free (proven on the CRT).
   - **[critic] Conflict with the live pipeline.** `ingest_cc0.py` keeps a downloaded model's own UVs and textures, and its docstring example ingests `ArmChair_01`. So the kit session is preparing more than one download and is not re-slotting it.
     - Red or the kit session must pick one rule: re-slot onto `Prop_*`, or keep the Poly Haven materials.
     - Keeping them is acceptable for Poly Haven-only pieces, which share one capture style. It is not acceptable for the copy-paste chair, which must share the pile's slots.
   - **[critic] 04 rated `GreenChair_01` only "maybe"** (it "reads gothic up close"). 04's "use" pick was the CC-BY 3DCraftsman wingback (F1). Choosing the CC0 chair is a defensible licence and consistency call, but it overrides 04 (see Q2).
2. **Office = FrontRooms' own 1990s office, not "film-accurate".** The film documents emptied offices: dividers that go nowhere, full-length cabinets, random furniture. It does not document cubicle farms or desk CRTs (01, 03). Red's target is built as specified. The film's office vocabulary becomes the anomaly layer (§4.8).
3. **Piles: authored tableau templates plus a seeded analytic solver, with no runtime physics.**
   - These are the code's existing approach (06 §7).
   - Repetition rule: one chair mesh, `Kit_LadderBackChair`, fills every chair slot in a pile. Duplicates are exact (same mesh, same material).
   - Orientations are quantised: upright, 90°, 180°, or a 30–52° edge-lean.
   - Nothing is ever broken.
4. **Troffer lens: flat frosted opal in the Office**, replacing the parabolic louvre. The film (02 F13), Red's target and the BPA real-office baseline agree. Level 0 keeps prismatic for now; this is open question Q3.
5. **Office light = 4000 K tubes. The green-grey comes from an Office-only post volume, not from tinting the lights.** Absolute values are in §6.4. Office fog becomes lighter and greener, exp² 0.018, #3B3F35.
6. **Pile placement:** at the room centroid, unless both main openings sit on an axis through the centroid. In that case, shift it 0.2 × room width off the axis. It stays a landmark, and the entry view stays off-centre and keeps the chase lane clear.
   - **[critic] The shift must be clamped.** The spec keeps a clear ring of R + 0.6. In a 12 m hall (clear 11.84, R = 2.64), an unclamped 2.4 m shift puts the ring's edge 5.64 m from the centre. The keepClear strip begins at 4.92. Clamp to `shift ≤ halfClear − stripDepth − (R + 0.6)`, which is about 1.7 m on a side with a strip.
   - **[critic] API gap.** `Build(parent, centre, radius, H, seed)` does not receive the openings, so it cannot know the door axis. Either `Furnish` (map-chat file) computes the offset, or this needs the 6-argument overload that passes `KeepClear(...)`, which A4 also needs.
7. **Collision and Hunter.**
   - Piles get 2–4 blocker boxes, 1.8–2.0 m tall, around the dense core. Upper pieces are visual only.
   - **`Dress` and `Build` must return their occupied footprints.** `FrontRoomsMapWorld` then marks those 3 m cells as impassable to the Hunter.
   - ~~This is the biggest integration bug: the Hunter walks through anything.~~ **[critic] Superseded at 15:31.**
     - The Hunter now collides with prop colliders. It slides along them, sidesteps after 0.5 s and ghosts through furniture after 1.4 s (spec §7).
     - The remaining problem is path quality. BFS still routes through pod and pile cells, so the Hunter either ghosts visibly through a pile or snags on it mid-chase.
     - Returning footprints is still the right fix, but it is no longer a walk-through bug. `MapGrid.Passable` is edge-based, so a per-cell blocked flag is a map-chat change (06 §9).
8. **Colour variety comes from material variants, never MaterialPropertyBlocks**, because MPBs break the SRP Batcher (04, 05, 06; 02's MPB suggestion is overruled).
   - kitlib gains an export option, `variants`, that writes the same mesh several times with remapped slots. Example: `Kit_Sofa3_Floral`, `_Oatmeal` and `_Charcoal`.
9. **Pile frequency per eligible room.**

   | Zone | Pile chance |
   |---|---|
   | Level 0 halls (4×4 cells or larger) | 35% (unchanged) |
   | Tall zones | 60% |
   | Low zones | 25% |
   | Office halls | 15% |
   | Office workrooms | 0% (the anomaly layer is used instead) |
   | Corridor chair drift | 1 in 5 corridors |

   Chances scale with the difficulty tier.

   **[critic] Several rows cannot fire under the current room carving** (spec §6; `Furnish` requires min side ≥ 4 cells):
   - **Low zones.** Low rooms are 2 × 2–3 cells, so they are never eligible.
   - **Office halls.** Office rooms are 2–4 cells a side, and `Furnish` sends every Office room to `Dress` only. So "Office halls 15%" means `Dress` calls `Build` internally, and only in 4 × 4 rooms (11.84 m clear). There, a pile plus a 2 m ring leaves about 2.4 m per side: room for wall rows, but not pods. Treat 15% as "replaces pods in that room".
   - **Corridors.** `Furnish` iterates rooms only. Corridor chair drift needs a new map-side hook, which belongs to the map chat.
10. **Height caps.**

    | Case | Cap |
    |---|---|
    | Tower mass | H − 0.25 m |
    | Tower spike | H − 0.10 m |
    | Sprawl | 0.6 × H |
    | Tall zones | 3.6 m absolute |

    Only `CeilingStuck` touches or pierces the ceiling (by 0.12 m or less), and only in 2.4 m and 2.9 m zones.

    **[critic] This conflicts with the spec.** The spec says the pile keeps under `min(0.95 H, H − 0.06)`, and props keep 0.05 m under the ceiling.
    - Piercing needs agreement with the map chat first.
    - Since Low rooms never qualify (decision 9), CeilingStuck effectively runs only in 2.9 m 4 × 4 halls.
    - The code's `CeilingStuck` height ratio is `1f`. Check it against the spec's cap.
11. **Camera FOV: 72° vertical** in both `FrontRooms3DGame` (76° today) and `FrontRoomsMapWalker` (72° today). At 16:9 that is about 14 mm full-frame, the film's "a 14mm looks normal" (01 S11).
12. **Grain and halation are a stylistic choice, not film fact** (01: the film was digital on Venice 2). Keep the grain subtle. Do not attribute "warm green-yellow" or "CRT haze" to Cox.
13. **Downloads: 37 CC0 items, about 270 MB raw** (§2.3), all on pages verified by 04 and 05 on 2026-10-02. **Nothing is downloaded until Red approves.**

### 0.1 Conflicts between the reports and how they are resolved

| Topic | Positions | Decision |
|---|---|---|
| Troffer count | 01: ASC gives 180 fixtures × 2 tubes. 02: Curbed, read in the browser, gives "350 custom troffers". | Irrelevant to the game. Both describe a flat, evenly glowing lens, so use flat opal. Do not cite either number in the deck without the source. |
| Lens type | `VISUAL_RESEARCH_LOOKDEV.md` says prismatic K12 (Level 0) and parabolic louvre (Office). 02 F13 and the target show flat opal. | Office uses flat opal. Level 0 is Red's call (Q3). |
| Colour variety | 02 suggests MaterialPropertyBlock tints. 04, 05 and 06 say no MPB. | Material variants per slot, exported as separate `Kit_*` assets. |
| Navigation | 01 and 02 say NavMeshObstacle. 06 says the project has no NavMesh. | Hunter cell mask from returned footprints (§3.4, §4.10). |
| Pile position | 01 and 02: off-axis, never centre-frame. 06: centred landmark. | Centroid, shifted 0.2 × W off a straight door axis (decision 6). |
| Collider height | 02: nothing above 1.2 m. 06: blockers at least 1.8 m so they break line of sight. | 06. Blockers 1.8–2.0 m let the pile break the Hunter's raycast LOS; pieces above stay non-colliding. |
| Scale outliers | 01: 0.85×/1.2× "wrong copies". 06: uniform 0.97–1.03, with at most one 1.12×. | Uniform scale only. At most one 1.15× copy per pile, only when intensity ≥ 0.6. Never non-uniform scale under a rotated child (shear). |
| Mirroring | 02: mirror is fine. 04: negative scale splits batches. | At most one mirrored leaf per pile, used as the "copy is slightly wrong" beat (01 S24). |
| Office share of a pile | 01: a minority. 06: 30–40%. | Level 0 piles ≤ 20% office pieces. Office-zone piles 35–40%. |
| Pile height | 06: 0.88–0.95 × H everywhere. 02: cap 3.6 m in 5.4 m zones. | 02's cap in Tall zones. 25 intact pieces cannot read at 5 m. |

### 0.2 Corrections to project docs (do these when next editing them)

`Documentation/VISUAL_RESEARCH_LOOKDEV.md`:
- The 2002 photo was taken on a **Sony Cyber-shot**, not a Nikon Coolpix (03).
- "Warm green-yellow" and "CRT haze" are **not** in the re-fetched Cox interviews (01). Relabel them as FrontRooms' stylistic choice.
- The Office fixture is a **flat opal lens**, not a parabolic louvre.

Codex doc's Curbed claims:
- "350 troffers" is now confirmed in-browser by 02.
- "Pastels with wood trim" is confirmed by 02 for Mary's office/living-room sofas only, not for the backrooms.

`Documentation/LIGHTING_SPEC.md`: the Office row reads "warm white #FFE1B1". Update it to the §6.3 values.
- **[critic]** The same row gives intensity 1.25 and range **6.8**. LEVEL_MODULE_SPEC §11 lists `LIGHTING_SPEC.md` as stale, describing the title stream. The map uses range 10 m (12 m in Tall zones) and Office intensity 5.5 (`FrontRoomsMapWorld` lines 713 and 1009). §6.3 is corrected to match.

### 0.3 What the research established (brief, with sources) [critic: added]

This was the brief's first item. Before this pass it was only implicit in the decisions. One line per finding, each with its primary URL. Details are in 01 and 03.

**Film (A24 *Backrooms*, 2026)**

| Finding | Source |
|---|---|
| The copy-paste furniture was real duplicates. The set decorator bought 20 identical sofas and 40+ identical oak slat-back chairs from a hotel liquidator. Nothing post-dates the early 1990s. | The Set Set (Trevor Johnston): https://thesetset.com/articles/backrooms-set-decorator-trevor-johnston-interview |
| Some sourced pieces were 3D-scanned so VFX could distort them. Which shots used this is unknown. | same |
| "Thirty-nine of the same chair" from one haul. Furniture towers are landmarks for characters and viewers. | Surface (re-fetched in this critic pass): https://www.surfacemag.com/articles/a24-backrooms-production-design/ |
| The furniture idea comes from video-game clipping. It escalates from drab to piles that reach the ceiling. | Elle Decor via Yahoo: https://www.yahoo.com/entertainment/movies/articles/meaning-behind-surreal-sets-a24-195154619.html |
| Store stock and Clark's throne were pulled into the backrooms on purpose. | IndieWire via Yahoo: https://www.yahoo.com/entertainment/movies/articles/backrooms-production-design-ultimate-game-200000184.html |
| Vermette cut shoes in half and balanced an oversize throne, so half-objects are practical props. | Curbed, read in a browser by 02: https://www.curbed.com/article/backrooms-kane-pixels-a24-set-production-design-interview.html |
| Lighting: 180 fixtures × 2 Astera Titan tubes at 4000 K, camera WB 4300 K, Venice 2. No grain, halation or film emulation is mentioned; only the found footage went to VHS. | ASC (re-fetched in this critic pass): https://theasc.com/article/backrooms-cinematography-cox/ |
| Lenses: 18 mm or wider inside, where "a 14mm looks normal". The sets include a wide-open office space with random furniture. | Sony Cinematography (re-fetched in this critic pass): https://sony-cinematography.com/dp-jeremy-cox-and-venice-2-ground-the-extradimensional-reality-of-backrooms/ |
| Offices in the cut are emptied offices with "dividers that go nowhere" and full-length wall cabinets. Couches are buried in floors and walls. | Moria: https://moriareviews.com/sciencefiction/backrooms-2026.htm (01 re-fetched it; 02 marked its own copy as prior-run) |

**IP canon outside the film**

| Finding | Source |
|---|---|
| wikidot Level 4 is an empty office with water coolers, vending machines and blacked-out windows. | https://backrooms-wiki.wikidot.com/level-4 |
| Fandom Level 4 has carpet indents where furniture stood, many dead lights, and furniture only in small rooms. Level 153 is late-1980s to mid-1990s workstations. | https://backrooms.fandom.com/wiki/Level_4 , https://backrooms.fandom.com/wiki/Level_153 (read in a browser by 03) |
| Kane Pixels' series distorts furniture by stretching it (Found Footage #2) and phasing it into walls and floors (Static Dead End). Everything Must Go repeats objects in a line that phases into the floor; those objects are signs, not furniture. No source describes a broken object; "nothing is broken" is 03's inference. | https://en.wikipedia.org/wiki/Backrooms_(web_series) |
| The founding photo (2002, Sony Cyber-shot) shows an emptied furniture-store upper floor with no furniture. | https://en.wikipedia.org/wiki/The_Backrooms |
| Wiki text and images are CC BY-SA 3.0, and share-alike applies if copied. Concepts are free. Kane's series and the film are all rights reserved. | https://backrooms-wiki.wikidot.com/licensing-guide |

**Net reading.** Red's target office is FrontRooms' own (decision 2). The pile grammar (identical intact pieces, decisive orientations, landmark placement) is documented by the film. The stretch, sink and repeat verbs are documented by Kane's canon.

---

## 1. Decomposition

Dimensions are W × D × H in metres. Real-world references name a type only. **No asset may carry a brand, logo or real label.**

**Texture-set shorthand.** PH = Poly Haven, aCG = ambientCG, GEN = generated in `gen_surfaces.py`, followed by the kit slot that receives it (§5.2).

### 1a. Red's office target (`ref_office_target.png`)

Measured read of the frame (§6.9): a low-key, olive-green-grey image (hue 45–70°, saturation 0.08–0.2). The carpet is lighter than the walls under downlight. The lenses clip to #EEEADA.

**[critic] What this table rests on.**
- The critic re-viewed the frame with brightened crops and re-sampled the colours. Lens #EEEADA, foreground carpet #595E5A, far corridor #4C4C3F and fabric #2D2D27 reproduce.
- The "Real-world reference" and "Dims" columns are **designer estimates and trade-typical sizes**. The reports cite only panel heights, the desk worksurface and file sizes (03; LEVEL_MODULE_SPEC §6 catalogue). The other dimensions are uncited.
- Brand-type labels (Steelcase/Haworth, National Vendors/AP) are uncited style pointers [UNVERIFIED].
- Where the spec's catalogue gives a size, the spec size is binding and is noted in the row.

| # | Element | Real-world reference | Dims (m) | Materials → texture sets | Sells it at 2–4 m | Wear |
|---|---|---|---|---|---|---|
| T1 | Lay-in ceiling | 2'×2' fine-fissured mineral-fibre tile on 15/16" exposed white T-bar, 1970s–90s | tile 0.61 × 0.61, T-bar 0.024 wide | GEN `Office_Ceiling2x2` (keep), plus PH `polystyrene` micro-normal baked in | Tee grid as a perspective device; slight tile-to-tile value shifts; 1 in 40 tiles sagging 5 mm | **Big brown tide-ring stain clouds** 0.6–2.5 m, in clusters near fixtures and corners; dust at tee edges |
| T2 | Troffer | 2'×4' recessed lensed troffer, 2-lamp T8/T12 type | 0.61 × 1.22, flange 0.02 | GEN opal lens + `Painted_Metal` flange | **Flat even glow, no visible tubes**, 6–8% edge falloff; thin white flange flush with the T-bar | Lens slightly yellowed; dead units show 2 faint grey tube shadows through the opal |
| T3 | Walls | Painted gypsum, eggshell beige; dark vinyl cove base | base 0.10 h | PH `beige_wall_001` (A/B against GEN `Office_Drywall`); cove = existing `Cove_Base` | Near-invisible texture; value change at the cove line | Scuffs at 0.7–0.9 m (chair-back height); grime around switch plates |
| T4 | Square columns + bulkhead | Drywall-wrapped structural column with a soffit beam between column pairs. **[critic]** The target's columns measure about 0.9–1.2 m against the 1.52 m desks beside them. The spec and live code use **0.61 m**, at most 1–4 per room, because Red rejected pillar halls. Open conflict: Q11. The target's soffit also carries its own small surface fixtures (far left and far right of the frame). | column 0.9 × 0.9 (target) vs 0.61 (spec) × to ceiling; bulkhead 0.9 wide × 0.35 deep | Wall material; corner bead as a 25 mm bevel | **Crisp bevelled corners catching the lens light**; the bulkhead breaks the ceiling plane | Chipped corners at 0.3–1.0 m |
| T5 | Carpet | 24" loop-pile modular tile, quarter-turned, slate blue-grey, 1990s | 0.61 module | GEN `Office_CarpetTile` layout + PH `dirty_carpet` normal/rough/AO; A/B with TextureCan Blue Office Carpet | Per-tile tone shift and pile direction; seams | **Dark blotches** (aCG SurfaceImperfections013/001); traffic darkening on the spine; coffee spill near the cooler |
| T6 | Cubicle panel | 1990s systems panel (Steelcase 9000 / Haworth type): fabric-faced, tackable | 1.52 W × 0.064 × 1.52 H; end panel 0.76 W. **[critic]** Live mesh: 1.524 × 0.068 × **1.57**; spec heights 1.32 / 1.57, suggested 1.35 / 1.65. Under the spec a 1.57 panel does not block the Hunter's 1.6 m sight ray; only panels ≥ 1.65 do. | PH `poly_wool_herringbone` tinted slate → `Prop_FabricCubicle`; trims `Prop_SteelPutty` | **Light putty edge trim and top cap (20 mm) against the dark fabric** (the strongest read in the crop); dark base rail; connector post | Fabric slightly faded on top; dust on the cap; 1–2 pinned papers |
| T7 | Desk | Panel-frame office desk: almond HPL top on dark-brown steel C-frame, hanging beige pedestal. **[critic]** In the foreground desk the beige block reads as a full-depth pedestal or modesty panel between the right-hand legs, ending just above the floor. | 1.524 × 0.762 × 0.74 (spec); top 0.032 thick; legs 0.038 square tube with a lower stretcher; pedestal 0.38 × 0.66 × 0.56 at 0.10 off the floor (this doc) vs **0.38 × 0.56 × 0.71 (spec)**. Reconcile. | GEN almond laminate stipple → `Prop_LaminateBeige`; aCG Metal028 tinted brown → `Prop_SteelBrown`; pedestal `Prop_SteelPutty` | **Visible top thickness with a self-edge**; dark frame rectangle (leg, apron, stretcher); pedestal floating above the carpet | Edge chips at the user's front corners; cup rings (aCG SurfaceImperfections007); polished patch at the user position |
| T8 | CRT monitor | 14–15" beige CRT, c. 1994–97 | 0.37 × 0.41 × 0.41 (built) | aCG Plastic013B normal/rough + yellowed albedo → `Prop_PlasticBeige`; `Prop_ScreenCRT` | Thick chin with buttons; tapered tube; screen darker than the bezel with a faint reflection | **UV yellowing stronger on top faces**; dust on the glass (aCG Fingerprints002) |
| T9 | Keyboard + mouse | 101-key beige keyboard; 2-button beige mouse with cord. **[critic]** The foreground desk also has a flat pale rectangle right of the mouse, reading as a mouse pad or notepad. It is not yet in the kit. | kb 0.46 × 0.19 × 0.035; mouse 0.06 × 0.11 × 0.035 | `Prop_PlasticBeige`, `Prop_KeyboardKeys` (atlas) | Key-field relief and legends at 2 m; cord to the monitor | Shiny worn keys (WASD/space) |
| T10 | Paper stack / binders | Letter paper, manila folders, 3" ring binders | stack 0.22 × 0.28 × 0.02–0.08; binder 0.29 × 0.06 × 0.32 | GEN paper edges → `Prop_Paper`; binder vinyl → `Prop_Vinyl` | Readable **edge lines**; slightly fanned | 1 in 6 stations has a sheet on the carpet |
| T11 | Task chair | 1990s fabric task chair, 5-star black base on casters, gas lift | base Ø 0.64; seat 0.46 h; back top 0.92 (this doc) vs **base 0.66, seat 0.45, back 0.95 (spec; the live mesh is 0.95)** | Black weave (PH `rough_linen` → charcoal) → `Prop_FabricChair`; aCG Plastic012B → `Prop_PlasticBlack`; `Prop_Chrome` gas lift | Separate seat and back cushions with a back bar; 5 casters | **Never aligned**: pushed out 0.2–0.6 m, yawed ±35°; seat front worn shiny |
| T12 | Desktop PC case | Beige horizontal desktop case under the monitor. **[critic] Not visible in the target.** Both legible stations have the CRT on its own tilt-swivel foot, directly on the desk. Keep the asset as optional variety (§4.6 already limits it to under 40% of CRTs). Do not cite the target for it. | 0.42 × 0.42 × 0.14 (live mesh: 0.42 × 0.49 × 0.12) | `Prop_PlasticBeige` + atlas (drive bays) | Floppy slot and power LED | Yellowed |
| T13 | Water cooler | Bottled floor cooler, enamelled almond cabinet, 5-gal blue PC bottle | cabinet 0.32 × 0.33 × 0.98; bottle Ø 0.27 × 0.49; total 1.32 (this doc) vs **0.32 × 0.32 × 1.35 (spec)**. The live mesh is 0.41 × 0.38 × 1.365, wider than the spec. | aCG Plastic018B → `Prop_PlasticWhite`/`Prop_SteelPutty`; `Prop_BottleBlue` (transparent) | **Blue bottle read** (the only cool colour accent); hot/cold taps; cup dispenser | Drip-tray stain; water line half-full |
| T14 | Photocopier | Floor-standing mid-volume copier with paper deck, late 1980s–90s. **[critic]** It stands on casters, against a free-standing dark cubicle panel set in front of the wall, not against the bare wall. | 0.62 × 0.66 × 1.05 (this doc) vs **0.62 × 0.68 × 1.15 (spec; the live mesh is 0.63 × 0.69 × 1.14)** | `Prop_PlasticBeige` body; `Prop_PlasticGrey` platen cover and panel; atlas `Prop_CopierPanel` | **3–4 paper-drawer seams with handles**; dark top cover; side output tray | Lid slightly open; a sheet on the tray |
| T15 | Interior window | Aluminium-framed interior borrowed light. **[critic] Not blacked out in the target.** It looks into a **dim adjoining room** with one lit ceiling fixture and a door frame. The spec makes it decor with no collider on a wall stretch, so the room behind needs a fake interior: an interior-mapping shader or a shallow back box with one emissive lens. That fake interior is unspecified. | 2.40 × 0.10 × 1.05; sill 1.00, head 2.05 (this doc) vs **2.44 × 1.22, sill 0.90, no collider (spec)**; frame 0.05 | Dark-bronze anodised → `Prop_SteelBlack`; `Prop_Glass` (transparent, dark tint) | **Dark glass with a dim room and one lit fixture beyond**; deep frame shadow | Dust on the sill |
| T16 | Vending machine | 1990s glass-front snack machine (type label uncited) | 0.94 × 0.89 × 1.83 (this doc) vs **0.90 × 0.90 × 1.83 (spec)** | `Prop_SteelBlack` cabinet; `Prop_Glass`; atlas `Prop_VendingFront` (invented snack art); warm emissive interior | **Lit interior; the target shows 4 trays × 4 packets** (corrected from "5 trays × 4–6 coils"); keypad at right; dark pickup door; small feet | One dead tray light; coin-slot wear |
| T17 | Main doorway | Wood-cased opening into a long corridor. **[critic]** The map owns openings: an arch is 1.1–1.8 m wide, top 2.2 m, **no trim**; a door is 1.0 × 2.1 m with a 0.07 trim, on Low ↔ Standard borders only (spec §3). The target's cased opening needs the map chat to allow trim on arches | 1.80 × 2.10 opening, casing 0.07 | Existing `Door_Veneer` / DoorVeneer | **Depth through repetition**: a lit corridor with a troffer line beyond | Worn kick zone |
| T18 | Side door | Flush hollow-metal door, painted grey, closed. **[critic] Not found in the target.** The grey rectangles at the right are cubicle panels; the only door frame on that side is seen through T15. The map owns doors anyway: 1.0 × 2.1 m, only on Low ↔ Standard borders (spec §3). Treat T18 as unsupported. | 0.91 × 2.13 | `Painted_Metal` tinted | Lever, closer | Scuffs at the bottom |
| T19 | Wall details | Light switch, thermostat, a notice. **[critic]** The target shows two small round plaques flanking the doorway at about 1.2–1.4 m, plus a small sign above the casing. | 0.07 × 0.12 plates | atlas | Small near-door detail at 1.2–1.4 m | Yellowed notice |
| T20 | Haze | Distance haze; corridor fades to grey | — | Fog (§6.5) | 3rd–4th room down the axis falls to #4C4B3C | — |
| T21 | Contact grounding | — | — | SSAO + dust/blob decals | Dark contact under desk frames and pedestals | — |
| T22 [critic: added] | Narrow dark object leaning on the column beside the cooler | Unidentified: a folded easel or flip-chart stand, a closed coat rack, or a mop. About 1.3 m tall | ≈ 0.25 × 0.05 × 1.3 [UNVERIFIED] | `Prop_SteelBlack` or `Prop_WoodDark` | A thin diagonal breaking the column face | — |
| T23 [critic: added] | Free-standing panel ends and "returns" | A dark panel behind the cooler and another behind the copier, with a small side table abutting the centre-left desk | Panel as T6; return 0.6 × 0.6 × 0.74 [UNVERIFIED] | As T6 and T7 | Wall units placed against panel ends, not bare walls (supports §4.4) | — |
| T24 [critic: added] | Dark figure-like shape at the far end of the corridor | Possibly a person or entity silhouette (or a chair) about 25 m down the axis | — | — | A gameplay or narrative beat, not furniture. Ask Red whether it is intended (Q12) | — |

### 1b. Still A — warm hall, low "sprawl" pile, blue-tape stud doorway

Source: Dezeen BTS photo by Wendigoon, 02 §0A. The geometry follows 02. Every piece is intact.

**[critic]** Red's two stills are not on disk, and the critic could not view them. This table and §1c were checked item by item against 02's viewed decompositions (0A, 0B, F01, F02, T02), not against the images.
- Still A is fully covered except for one item: the **free-standing wall section that carries the chair rail** (02 §0A), which is not itemised. Add it to A1 as a half-height wall module.
- The ceiling grid and troffers of both stills are covered by T1/T2.

| # | Element | Real-world reference | Dims (m) | Materials → texture sets | Sells it at 2–4 m | Wear / state in pile |
|---|---|---|---|---|---|---|
| A1 | Shell: wallpaper, chair rail, column, carpet | Warm yellow vertical pinstripe vinyl paper; dark-wood chair rail; square column; pale beige cut pile | rail at 0.90, 0.07 h, 0.02 proud; column 0.6 | GEN `wallpaper()` stripe variant; rail `Prop_WoodDark`; GEN beige carpet | Rail line continuing across the column | — |
| A2 | Unfinished doorway | Rough opening in 2×4 SPF studs at 16" centres, double header, no casing; blue painter's tape | opening 0.91 × 2.10; studs 0.038 × 0.089 at 0.406 c/c; tape 0.048 | aCG Wood096 → `Prop_Studs`; aCG Tape005 recoloured blue → `Prop_TapeBlue` decal | **Raw stud rhythm plus a saturated blue tape line on the floor** | Grade stamp decal on 1 stud |
| A3 | Two-tier side table on casters | 1970s–80s bobbin-turned walnut serving table | 0.46 × 0.46 × 0.66; legs Ø 0.035 | PH `walnut_veneer` → `Prop_WoodWalnut`; `Prop_Brass` casters | Turned-leg profile; lower shelf | Upright "escapee", 1 m out |
| A4 | Pedestal desk | Single-pedestal cherry desk, 3 drawers, brass bail pulls | 1.37 × 0.71 × 0.76 | PH `lacquered_cherry_wood` → `Prop_WoodCherry`; `Prop_Brass` | **Glossy lacquer highlight**; drawer reveals | Upright anchor |
| A5 | Credenza / sideboard | Cherry sideboard | 1.52 × 0.46 × 0.76 | `Prop_WoodCherry` | Door and drawer grid | Upright, behind the desk |
| A6 | Bergère / Queen-Anne armchair | Blush velvet, exposed walnut frame, cabriole legs | 0.68 × 0.70 × 0.98, seat 0.45 | PH `velour_velvet` hue-shifted → `Prop_VelvetPink` (with sheen, §5.1); `Prop_WoodWalnut` | **The only pink in the pile**; curved legs | Tipped back 15–20° onto the desk edge |
| A7 | Hutch / armoire | Ebonised (black-lacquer) 2-door armoire with cornice | 1.00 × 0.50 × 1.90 | PH `dark_wood` regraded near-black → `Prop_WoodEbony` | **Dark triangular silhouette peak** | EdgeLean 45°, back toward the camera |
| A8 | Nightstand | 2-drawer orange-brown oak, brass ring pulls | 0.50 × 0.40 × 0.60 | PH `red_oak_veneer` (orange regrade) → `Prop_WoodOak`; `Prop_Brass` | Ring pulls | On its side (90°), wedged |
| A9 | Urn / bulb vase | Brown glazed ceramic | Ø 0.28 × 0.38 | GEN glaze → `Prop_Ceramic` | Glossy highlight | Lying on its side |
| A10 | Pleated table lamp | Cream pleated drum shade, brass/ceramic base | total 0.68; shade Ø 0.40 → 0.28 × 0.26 | GEN pleat normal → `Prop_LampShade`; `Prop_Brass` | **Pleat relief** | Upright on the highest flat top, off |
| A11 | Tall chest of drawers | 5-drawer honey/orange teak or oak, 1970s | 0.86 × 0.46 × 1.22 | PH `teak_veneer` (orange) → `Prop_WoodTeak` | **Biggest diagonal**; drawer-reveal shadows | EdgeLean 40° on its front corner |
| A12 | Low dresser | 6-drawer cherry dresser | 1.40 × 0.48 × 0.78 | `Prop_WoodCherry` | Drawer grid | Upright, at the back |
| A13 | 2-drawer steel file | Beige-grey vertical file | 0.38 × 0.66 × 0.72 | aCG Metal028 tinted putty → `Prop_SteelPutty` | Label holders and handles | Half-hidden at the back right |
| A14 | Wooden bar stool | 4-leg wooden stool with rung ring | Ø 0.38 seat × 0.76 | `Prop_WoodWalnut` | Rung ring | Standing alone, far right |
| A15 | Rolling cabinet | Veneer cube on casters with a door (TV/mini-bar cart) | 0.50 × 0.45 × 0.55 + casters | `Prop_WoodCherry`, `Prop_Rubber` | Casters | Standing alone, right |
| A16 | Light / grade | Flat troffer top light, no key | — | — | Soft contact shadows only | — |

### 1c. Still B — cool room, tall "tower" pile

Source: Fast Company Brasil `TB_Scans_00108` film scan. It is the same physical pile as Surface's warm `TB_11703_R3` and appears in trailer frames 0:31–0:33 (02 F01, F02, T02).

| # | Element | Real-world reference | Dims (m) | Materials → texture sets | Sells it at 2–4 m | Wear / state in pile |
|---|---|---|---|---|---|---|
| B1 | Shell | Olive pinstripe paper with a darker base band; wallpapered square column; grey-green carpet; flat-lens troffers every 3 tiles | band 0–0.9 m; column 0.6 | GEN stripe paper (olive) + band; GEN carpet (green-grey) | Ceiling grid fills the top third | — |
| B2 | Pallet | 48"×40" stringer pallet | 1.22 × 1.02 × 0.14 | aCG Planks021 → `Prop_PinePallet` | Slat gaps | Base, upright |
| B3 | Plywood crate | Battened 18 mm ply shipping crate, invented "FRAGILE / GLASS" stencil | 1.00 × 0.80 × 0.75 | PH `plywood` → `Prop_Plywood`; stencil atlas decal | **Ply edge laminations**; stencil | Upright on the pallet |
| B4 | Plywood cabinets | Raw ply / MDF carcass | 0.90 × 0.45 × 1.20 | `Prop_Plywood`; aCG Chipboard004 backs → `Prop_Chipboard` | Raw backs | Base |
| B5 | Glass display cabinet | 1980s–90s oak curio cabinet, 2 glass doors, glass shelves | 0.90 × 0.40 × 1.80 | `Prop_WoodOak`; `Prop_Glass` | **Glass reflection plus shelf lines** | Lower centre-right, upright |
| B6 | Low dark cabinet | Dark-wood 2-door cabinet | 0.80 × 0.45 × 0.75 | `Prop_WoodDark` | — | Back left |
| B7 | Upholstered armchair | Oatmeal woven club chair | 0.85 × 0.85 × 0.82 | PH `poly_wool_herringbone` → oatmeal `Prop_FabricBeige` | **Seat facing the camera** | Rolled onto its back |
| B8 | Step stool / library ladder | Oak 3-step ladder stool | 0.45 × 0.50 × 1.00 | `Prop_WoodOak` | Strong diagonal | EdgeLean 50° across the armchair |
| B9 | Charcoal sofa | Plain charcoal loveseat or sofa | (sofa mesh) | PH `rough_linen` → charcoal `Prop_FabricCharcoal` | Back panel mass | Standing on end |
| B10 | Open bookcase | Golden-oak open bookcase | 0.90 × 0.30 × 1.80 | `Prop_WoodOak` | Shelf rhythm | On its side |
| B11 | **Ladder-back dining chair ×4–5 (same mesh)** | Oak slat-back hotel dining chair: the 39–40 identical chairs (01 S1/S2) | 0.45 × 0.50 × 0.98, seat 0.46 | PH `red_oak_veneer` golden → `Prop_WoodOak` | **Identical silhouette repeated: the device itself** | Upright, sideways, upside-down on top |
| B12 | Floral sofa (top slab) | 1980s–90s beige floral jacquard 3-seat, rolled arms, wood base trim (T05) | 2.00 × 0.90 × 0.82 | PH `floral_jacquard` normal + rebuilt beige albedo → `Prop_FabricFloral`; `Prop_WoodOak` trim | Pattern readable at 3 m; loose cushions | Lying flat on top |
| B13 | Black CRT TV | 20" black CRT TV, 1990s | 0.52 × 0.48 × 0.48 | aCG Plastic012B → `Prop_PlasticBlack`; `Prop_ScreenCRT` | **The pile's "face"**: screen toward the approach | Upright, near the top |
| B14 | Halogen torchiere | Black pole, shallow uplight bowl, 300 W halogen type | base Ø 0.28; pole 1.80; bowl Ø 0.35; total 1.83 | `Prop_SteelBlack`; GEN bowl inside | **The highest thin spike** | 10–20° off vertical |
| B15 | Navy cushion / pouf | Navy pouf | Ø 0.50 × 0.40 | PH `rough_linen` → navy `Prop_FabricNavy` | Colour accent | On the top surface |
| B16 | Teal club armchair (satellite) | 1980s teal tweed club chair | 0.85 × 0.85 × 0.82 | `rough_linen` regraded teal → `Prop_FabricTeal` | **An odd colour, sitting normally** | Upright, 1 m out ("rolled off") |
| B17 [critic: added] | Wooden bar stool | Same as A14 | as A14 | `Prop_WoodWalnut` | Small vertical at the base | Seen in the warm F01 angle of the same pile (02 F01) |
| B18 [critic: added] | Plywood and cardboard sheets | Loose 4' × 8' ply offcuts and flattened cartons leaning at the base | ≈ 1.2 × 0.01 × 0.9 [UNVERIFIED] | `Prop_Plywood`, `Prop_Cardboard`. This is the only consumer of download **C6 CardboardSet001** | Flat diagonal planes at the base | Leaning (02 F01) |
| B19 [critic: added] | Wood dresser front in the pile | A case good showing its drawer face (same family as A11/A12) | as A12 | `Prop_WoodCherry` / `Prop_WoodTeak` | Drawer grid | Seen when the pile is used as a foreground wall (02 T02) |

**[critic] Conflict inside 02.** F01 (warm angle) calls the summit screen a "beige CRT TV/monitor", while 0B/F02 calls it a "black 1990s CRT TV". B13 follows 0B. Either colour works with existing slots; this needs eyes-on before it goes into a deck.

---

## 2. Make vs download

### 2.1 Principle

**One consistent kit at cinematic quality beats a patchwork.**

The case for kitlib:
- The kitlib CRT already reads correctly in-engine. It has correct dimensions, bevels and its sidecar with supports, colliders and pile metadata, and it costs about an hour per asset.
- Every downloaded model would need a rescale, decimation, slot remap, re-UV to metres and a hand-written sidecar. That is about the same work as modelling a boxy piece, and it brings a foreign texturing style.

**Rule.**
- Model every hard-surface, lathed or boxy piece in kitlib.
- Download geometry only where it is organic, a correct-era CC0 candidate exists, and modelling it in Python would take much longer. Only the bergère chair qualifies.
- Download **textures** for everything natural: wood figure, weave, velvet nap, leather grain, powder-coat orange peel, plaster. This is the real fix for the old flat look (05).
- **Generate** dimensioned layouts: carpet tiles, ceiling grid, stripe paper, lens, laminate, labels.

Upholstery (sofa, club chair) is the main quality risk of modelling. kitlib gains a `cushion()` helper:
- a box with 4–6 bevel segments;
- subdivision level 1;
- a 3–6 mm cloud-noise Displace;
- a 6 mm piping bead along seams.

90s mass-market upholstery was taut and mint (01 S1, S6), so this is era-correct. The gate in §5.4 decides whether the Sketchfab fallbacks are needed.

### 2.2 Decision per element

Most rows are modelled in kitlib and share kit slots. A row only names a download or a fallback where one applies.

**Office kit** (asset names as in `FrontRoomsOfficeKit`)

| Asset | Covers | Decision | Reason |
|---|---|---|---|
| `Kit_OfficeDesk` | T7 | Model (kitlib) | No download matches (04 hard gap) |
| `Kit_CubiclePanel`, `Kit_CubiclePanelShort`, new `Kit_PanelPost` | T6 | Model | 04 hard gap. Parametric widths 0.76 / 1.52 and heights 1.37 / 1.52 / 1.65 are export variants |
| `Kit_CRTMonitor` | T8 | **Done** (kitlib) | Keep. Add a yellowed-top albedo variant and an `_On` screen variant |
| `Kit_PCDesktop` | T12 | Model | Bevelled box (04 soft gap) |
| `Kit_Keyboard`, new `Kit_Mouse` | T9 | Model | Consistency. MadeByYeshe's (CC-BY) is unnecessary |
| `Kit_TaskChair` | T11 | Model | Blocky 90s form suits kitlib. Fallback: artvolodskikh Office Chair (CC-BY, 5.5k tris, 28.5 MB), §2.3-F |
| `Kit_DeskPhone` | — | Model | Trivial |
| `Kit_PaperStack`, `Kit_Binders` | T10 | Model + GEN edges | A stack reads by its edges (05) |
| `Kit_TrashBin` | — | Model (lathe) | 04 fallback rule |
| `Kit_VendingMachine` | T16 | Model + invented snack atlas | The download shell is empty anyway (04); no real brands |
| `Kit_WaterCooler` | T13 | Model (lathe bottle) | tboiston (CC-BY) not needed. The bottle must be its own transparent submesh, which is guaranteed if we build it |
| `Kit_Copier` | T14 | Model | Both downloads are era-uncertain (04 soft gap) |
| `Kit_FilingCabinet` (4-drawer) + `Kit_FilingCabinet2` | T13 office, A13 | Model | Shared by the office and the pile (dual use) |
| `Kit_InteriorWindow` | T15 | Model | Trivial |
| Columns, bulkheads, cove, troffer | T1–T4 | Code (map / room stream) + GEN materials | Already procedural |
| New `Kit_HatStand` | A, B, office | Model (lathe) | Dual use: the "hatstand" in the film pile inventory (01 S13) and an office coat rack |
| `Kit_WallClock` (optional) | — | Model (lathe + decal), **or download** | **[critic] Corrected.** 04 rates Poly Haven `wall_clock` (PierreB3D, CC0, 3,658 tris) as **use**, with tags "office" and "90s". The "modern" label had no support. Modelling is still fine for kit consistency, but the CC0 download is a valid zero-effort option (add it to list E) |

**Pile kit** (new names; `pile()` metadata required)

| Asset | Covers | Decision | Reason |
|---|---|---|---|
| `Kit_LadderBackChair` | B11 | Model. **Highest priority, hero quality** | 30–45% of pile instances; must be perfect. The 758-tri download "may be rough" (04) |
| `Kit_Sofa3` → `_Floral`, `_Oatmeal`, `_Charcoal` | B12, B9 | Model with `cushion()`; variants by slot remap | Floral tiling needs metre UVs, which a downloaded sofa would need a bake to get. Fallback: oisougabo Old Couch (CC-BY) |
| `Kit_ClubChair` → `_Teal`, `_Oatmeal` | B16, B7 | Model; same family as the sofa | "Same catalogue" coherence. Fallback: MaX3Dd Old Armchair (CC-BY) |
| `Kit_BergereChair` | A6 | **Download** Poly Haven `GreenChair_01` (CC0, 4,213 tris, 2.0 MB glTF 2K; API re-checked by the critic: 673 × 664 × **1,059** mm, tags include "gothic") → re-UV to metres → slots `Prop_VelvetPink` + `Prop_WoodWalnut` | Exposed carved frame, curved legs and an upholstered seat match a bergère. Cabriole legs are the one shape not worth scripting. Gate: if the gothic carving reads wrong at 3 m, fall back to 3DCraftsman wingback (CC-BY) |
| `Kit_Chest5` → **live name `Kit_Dresser70s`** [critic] | A11 | Model (**built**: 0.90 × 0.45 × 1.10, 7,518 tris, 6 slots) | 04 soft gap; simplest box family |
| `Kit_Nightstand2` | A8 | Model; shared "case" module | — |
| `Kit_DeskPedestal` | A4 | Model; shared module | — |
| `Kit_Credenza` | A5 | Model | — |
| `Kit_DresserLow` | A12 | Model | — |
| `Kit_Hutch` → `_Ebony`, `_Cherry` | A7 | Model. Old Hutch (CC-BY, 39k) rejected | Too heavy; variants by slot |
| `Kit_SideTableTurned` | A3 | Model (lathe legs) | Bobbin profile shared with the chair's turned posts. PH `side_table_tall_01` has curved legs, the wrong form |
| `Kit_BarStool` | A14 | Model (lathe) | PH `bar_chair_round_01` is 14k tris. **[critic]** 04 rated it **"use: best match"** (a vintage wooden bar stool with a round seat and footrest ring, 751 mm). "Beading" and "wrong form" are unsupported [UNVERIFIED]. Modelling wins only on the triangle budget; keep the download as the fallback |
| `Kit_RollingCabinet` | A15 | Model | 04 soft gap |
| `Kit_LampPleated` → **live name `Kit_TableLampPleated`** [critic] | A10 | Model (lathe + sine pleats) (**built**: 3,670 tris) | 04 soft gap |
| `Kit_Urn` | A9 | Model (lathe) | — |
| `Kit_CRTTV` | B13 | Model; reuses the CRT monitor module | Same screen material as the office, which is a deliberate rhyme |
| `Kit_Torchiere` | B14 | Model (lathe) | 04 hard gap |
| `Kit_DisplayCabinet` | B5 | Model | The downloads are Soviet/Victorian (wrong locale) or 61k tris |
| `Kit_Bookcase` | B10 | Model | PH `wooden_bookshelf_worn` is "worn", which contradicts mint condition |
| `Kit_PlyCabinet` | B4 | Model | — |
| `Kit_Crate` | B3 | Model + invented stencil | 04 hard gap |
| `Kit_Pallet` | B2 | Model | 384 tris either way; texture from Planks021 |
| `Kit_StepStool` | B8 | Model | — |
| `Kit_Pouf` | B15 | Model with `cushion()` | — |
| `Kit_ShoeHalf` (P2) | A4 archetype | Model (loft) | Only for the sunk / half-object archetype |
| `Kit_DoorwayStuds` (P1) | A2 | Model (arch kit) | Pairs with the sprawl pile |

**Optional variety, Tier E** (approve separately; not needed for the target or the stills):
- Poly Haven `Television_01` (wood-cased CRT, CC0, 1.6 MB).
- Poly Haven `metal_office_desk` (grey tanker desk, CC0, 5.2 MB) as a supervisor-office desk.

Both are Poly Haven quality, so they will not clash. Re-slot them onto kit materials anyway.

### 2.3 DOWNLOAD LIST — for Red to approve (nothing has been downloaded)

All pages and licences were verified on 2026-10-02:
- Poly Haven via `api.polyhaven.com/info|files`; licence: polyhaven.com/license.
- ambientCG via `ambientcg.com/api/v2/full_json`; licence: docs.ambientcg.com/license.
- cgbookcase: CC0 1.0 stated on its texture index.
- TextureCan: CC0 1.0 on its terms page.

**Poly Haven texture files** are fetched per map at 2K JPG: `<id>_diff_2k.jpg`, `<id>_nor_gl_2k.jpg` and `<id>_arm_2k.jpg` (arm = AO/rough/metal). URL pattern, from 05: `https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/<id>/<id>_<map>_2k.jpg`. "≈" sizes are about 56% of 05's all-maps totals; teak measured 7.9 MB of 14.0.

**ambientCG files** are zips named `<ID>_1K-JPG.zip` or `<ID>_2K-JPG.zip` from `https://ambientcg.com/get?file=<ID>_<res>-JPG.zip`, with sizes as published.

**Land raw files in `Frontrooms3D/Tools/lookdev/cc0_src/<source>/<id>/`, outside `Assets/`.** Pack them with a new `import_cc0.py`: albedo regraded, normal kept as `nor_gl`/NormalGL, mask R = 1 − rough, G = AO. Log every asset to `Tools/lookdev/ref/LICENSE.txt`.

**[critic] `ingest_cc0.py` already exists.**
- It is the model path: it handles Poly Haven glTF/.blend/.fbx and writes `_A/_N/_S` maps plus `materials_manifest.json`.
- Extend it, or add a texture-only mode, rather than writing a second `import_cc0.py`.
- It writes its outputs into `Assets/Resources/Surfaces/Textures`. Confirm the raw sources still stay outside `Assets/`.

**[critic] Spot-check of this list, 2026-10-02 ~15:45.** Every page below **exists**, and the licence matches:
- Poly Haven API `GreenChair_01` (4,213 tris, CC0 via polyhaven.com/license);
- Poly Haven API `floral_jacquard` (252.95 × 383.6 mm, published 2025-09-05);
- ambientCG `Plastic013B` (CC0; 1K-JPG listed at 6 MB);
- ambientCG API `Wood096` (50 × 50 cm, released 2026-09-30, 1K zip 5,358,165 B), `SurfaceImperfections007` (3,371,661 B) and `Tape005` (3,949,151 B);
- TextureCan 66 ("Blue Office Carpet Texture (Fabric 0009)"; the page shows 1K/2K/4K and SBSAR, but the licence text was not visible in the fetch; 05 verified the CC0 terms page);
- cgbookcase Liquid Stains 01 (1K–4K; CC0 only in alt text on the page; 05 verified the index);
- Sketchfab API F1 (CC Attribution, downloadable, 2,478 faces).

Sizes agree with the table to within rounding (MB here are decimal).

**A. Model (required, 1 item)**

| # | Asset | Files | Source page | Licence | Size | Lands as |
|---|---|---|---|---|---|---|
| A1 | Green Chair 01 (Kirill Sannikov) | `GreenChair_01_2k.gltf` + `.bin` + 2K textures (textures kept for reference only) | https://polyhaven.com/a/GreenChair_01 | CC0 | 2.0 MB | `Kit_BergereChair` |

**B. Furniture textures (required, Tier 1: 19 items)**

| # | Asset | Files | Source page | Licence | Size | → slot |
|---|---|---|---|---|---|---|
| B1 | teak_veneer | diff, nor_gl, arm 2K | https://polyhaven.com/a/teak_veneer | CC0 | ≈ 7.9 MB | `Prop_WoodTeak` (TileSize 1.0) |
| B2 | lacquered_cherry_wood | diff, nor_gl, arm 2K | https://polyhaven.com/a/lacquered_cherry_wood | CC0 | ≈ 6.4 MB | `Prop_WoodCherry` (1.0) |
| B3 | dark_wood | diff, nor_gl, arm 2K | https://polyhaven.com/a/dark_wood | CC0 | ≈ 7.7 MB | `Prop_WoodDark`, `Prop_WoodEbony` (2.0) |
| B4 | red_oak_veneer | diff, nor_gl, arm 2K | https://polyhaven.com/a/red_oak_veneer | CC0 | ≈ 8.0 MB | `Prop_WoodOak`; also the `Prop_WoodLaminate` source (1.0) |
| B5 | walnut_veneer | diff, nor_gl, arm 2K | https://polyhaven.com/a/walnut_veneer | CC0 | ≈ 6.8 MB | `Prop_WoodWalnut` (1.8) |
| B6 | plywood | diff, nor_gl, arm 2K | https://polyhaven.com/a/plywood | CC0 | ≈ 10.9 MB | `Prop_Plywood` (0.5) |
| B7 | Chipboard004 | `Chipboard004_1K-JPG.zip` | https://ambientcg.com/a/Chipboard004 | CC0 | 8.0 MB | `Prop_Chipboard` (1.0) |
| B8 | Plastic013B | `Plastic013B_1K-JPG.zip` | https://ambientcg.com/a/Plastic013B | CC0 | 6.5 MB | `Prop_PlasticBeige`, `Prop_PlasticWhite` (normal + rough; albedo GEN) |
| B9 | Plastic018B | `Plastic018B_1K-JPG.zip` | https://ambientcg.com/a/Plastic018B | CC0 | 6.8 MB | `Prop_PlasticGrey` |
| B10 | Plastic012B | `Plastic012B_1K-JPG.zip` | https://ambientcg.com/a/Plastic012B | CC0 | 6.5 MB | `Prop_PlasticBlack` |
| B11 | Metal028 | `Metal028_1K-JPG.zip` | https://ambientcg.com/a/Metal028 | CC0 | 7.0 MB | `Prop_SteelPutty`, `Prop_SteelBrown`, `Prop_SteelBlack` (tints) |
| B12 | Metal016 | `Metal016_1K-JPG.zip` | https://ambientcg.com/a/Metal016 | CC0 | 7.3 MB | Scratch / metalness mask for steel slots |
| B13 | Metal050C | `Metal050C_1K-JPG.zip` | https://ambientcg.com/a/Metal050C | CC0 | 3.6 MB | `Prop_Aluminium` |
| B14 | poly_wool_herringbone | diff, nor_gl, arm 2K | https://polyhaven.com/a/poly_wool_herringbone | CC0 | ≈ 12.7 MB | `Prop_FabricCubicle` (slate), `Prop_FabricBeige` (oatmeal) (0.27) |
| B15 | rough_linen | diff, nor_gl, arm 2K | https://polyhaven.com/a/rough_linen | CC0 | ≈ 13.6 MB | `Prop_FabricTeal`, `Prop_FabricChair`, `Prop_FabricCharcoal`, `Prop_FabricNavy` (0.27) |
| B16 | velour_velvet | diff, nor_gl, arm 2K | https://polyhaven.com/a/velour_velvet | CC0 | ≈ 10.3 MB | `Prop_VelvetPink` (0.28) |
| B17 | floral_jacquard | diff, nor_gl, arm **+ disp** 2K (the albedo is rebuilt from the height) | https://polyhaven.com/a/floral_jacquard | CC0 | ≈ 24 MB | `Prop_FabricFloral` (0.25 × 0.38) |
| B18 | Leather027 | `Leather027_1K-JPG.zip` | https://ambientcg.com/a/Leather027 | CC0 | 6.6 MB | `Prop_Vinyl` |
| B19 | Planks021 | `Planks021_1K-JPG.zip` | https://ambientcg.com/a/Planks021 | CC0 | 7.1 MB | `Prop_PinePallet` (1.4) |

**C. Room and arch detail (required: 6)**

| # | Asset | Files | Source page | Licence | Size | Use |
|---|---|---|---|---|---|---|
| C1 | dirty_carpet | nor_gl, arm 2K (no diff) | https://polyhaven.com/a/dirty_carpet | CC0 | ≈ 8 MB | Pile micro-layer baked into `Office_CarpetTile` |
| C2 | beige_wall_001 | diff, nor_gl, arm 2K | https://polyhaven.com/a/beige_wall_001 | CC0 | 3.2 MB (API listing) | A/B for `Office_Wall`; TileSize 3.0118 (256/85) |
| C3 | polystyrene | nor_gl, arm 2K | https://polyhaven.com/a/polystyrene | CC0 | ≈ 7 MB | Tile-face pits baked into `Office_Ceiling2x2` |
| C4 | Wood096 | `Wood096_1K-JPG.zip` | https://ambientcg.com/a/Wood096 | CC0 | 5.4 MB | `Prop_Studs` (0.5) |
| C5 | Tape005 | `Tape005_1K-JPG.zip` | https://ambientcg.com/a/Tape005 | CC0 | 3.9 MB | `Prop_TapeBlue` (recoloured) |
| C6 | CardboardSet001 | `CardboardSet001_2K-JPG.zip` | https://ambientcg.com/a/CardboardSet001 | CC0 | 11.4 MB | `Prop_Cardboard` (1.5). **[critic]** No §5.3 asset used this slot until B18 was added. The live `Kit_PaperStack` also uses `Prop_Cardboard`. Keep it only if B18 or boxes are built |

**D. Decal / mask sources (required: 11, all at 1K)**

These are baked into masks, or used in URP Decal projectors once that feature is added (§6.7).

| # | Asset | Files | Source page | Licence | Size | Use |
|---|---|---|---|---|---|---|
| D1 | SurfaceImperfections013 | `_1K-JPG.zip` | https://ambientcg.com/a/SurfaceImperfections013 | CC0 | 7.0 MB | Carpet blotches |
| D2 | SurfaceImperfections001 | `_1K-JPG.zip` | https://ambientcg.com/a/SurfaceImperfections001 | CC0 | 4.8 MB | Water stains |
| D3 | SurfaceImperfections007 | `_1K-JPG.zip` | https://ambientcg.com/a/SurfaceImperfections007 | CC0 | 3.4 MB | Desk cup rings |
| D4 | SurfaceImperfections015 | `_1K-JPG.zip` | https://ambientcg.com/a/SurfaceImperfections015 | CC0 | 8.2 MB | Top-face dust |
| D5 | Leaking001 | `_1K-JPG.zip` | https://ambientcg.com/a/Leaking001 | CC0 | 3.9 MB | Wall streaks under the window and soffit |
| D6 | Leaking006 | `_1K-JPG.zip` | https://ambientcg.com/a/Leaking006 | CC0 | 2.2 MB | Same |
| D7 | Scratches005 | `_1K-JPG.zip` | https://ambientcg.com/a/Scratches005 | CC0 | 6.4 MB | Desk/steel/plastic scuff masks |
| D8 | Fingerprints002 | `_1K-JPG.zip` | https://ambientcg.com/a/Fingerprints002 | CC0 | 5.2 MB | CRT / vending / window roughness |
| D9 | Smear007 | `_1K-JPG.zip` | https://ambientcg.com/a/Smear007 | CC0 | 8.4 MB | Same |
| D10 | Liquid Stains 01 | 1K set (DirectX normal: flip G) | https://www.cgbookcase.com/textures/liquid-stains-01 | CC0 1.0 | not published (est. 3–6 MB) | Carpet and desk spills |
| D11 | Dust Wipes 01 | 1K set | https://www.cgbookcase.com/textures/dust-wipes-01 | CC0 1.0 | not published (est. 3–6 MB) | Wiped dust on CRT screens and desk tops |

**E. Optional A/B tests and variety** (approve separately)

| # | Asset | Source page | Licence | Size | Why |
|---|---|---|---|---|---|
| E1 | Blue Office Carpet Texture (Fabric 0009), 2K | https://texturecan.com/details/66 | CC0 | not published | A/B against the in-house carpet tile |
| E2 | Wood092 (orange), 2K | https://ambientcg.com/a/Wood092 | CC0 | 18.2 MB | Second orange wood if teak won't regrade |
| E3 | Television_01, glTF 2K | https://polyhaven.com/a/Television_01 | CC0 | 1.6 MB | Wood-cased domestic TV variant |
| E4 | metal_office_desk, glTF 2K | https://polyhaven.com/a/metal_office_desk | CC0 | 5.2 MB | Supervisor-office desk |
| E5 [critic: added] | wall_clock, glTF 2K | https://polyhaven.com/a/wall_clock | CC0 | 4.9 MB (04) | 04 "use": office and 90s tags. A zero-effort alternative to modelling `Kit_WallClock` |
| E6 [critic: added] | bar_chair_round_01, glTF 2K | https://polyhaven.com/a/bar_chair_round_01 | CC0 | 7.2 MB (04) | 04 "best match" for A14. Decimate 14k → about 6k |

**F. Fallbacks.** Download these only if a §5.4 quality gate fails. They are CC-BY 4.0, so each needs a credit line (04 §5 has the text).

| # | Asset | Source page | Licence | Size | Replaces |
|---|---|---|---|---|---|
| F1 | Antique Wing Back Chair lowpoly (3DCraftsman) | https://sketchfab.com/3d-models/49e21ea4c0bf469387471934dd8bf0fa | CC-BY 4.0 | 10.7 MB | `Kit_BergereChair` |
| F2 | Old Couch (oisougabo) | https://sketchfab.com/3d-models/old-couch-443d9bb95e944afe8ebc4ff489e2886c | CC-BY 4.0 | 13.7 MB | `Kit_Sofa3` |
| F3 | Old Armchair (MaX3Dd) | https://sketchfab.com/3d-models/old-armchair-c20f084f29bd440197a18b4c750f69eb | CC-BY 4.0 | 35.3 MB | `Kit_ClubChair` |
| F4 | Office Chair (artvolodskikh) | https://sketchfab.com/3d-models/office-chair-a7fefb5dde954c84896949246dde5be6 | CC-BY 4.0 | 28.5 MB | `Kit_TaskChair` |

Sketchfab downloads need a free account. A sofa or chair fallback also needs a Cycles bake of our tiling fabric into its UVs.

**Totals.**
- Required A–D: 37 items, about 270 MB of raw downloads.
  - A: 2 MB.
  - B: about 168 MB.
  - C: about 39 MB.
  - D: about 50 MB, plus about 6–12 MB from cgbookcase.
- Packed into `Assets/` (albedo, normal, mask at 1K–2K): about 80–100 MB of source PNG. Builds are much smaller after ASTC/BC compression.
- **No attribution obligations** for A–D (all CC0). Add a courtesy credit line anyway (§2.5).

### 2.4 Explicitly not downloading

| Rejected | Reason |
|---|---|
| Kenney and Quaternius kits | Stylised; blockout only |
| OpenGameArt office set | Diffuse-only |
| 90s Office HDRP | Paid; not URP |
| MadeByYeshe 90s Retro Office Pack (CC-BY, 56.5 MB) | Patchwork risk and a "first Substance project"; everything in it is covered by kitlib |
| Megascans re-uploads, the Poppy Playtime machine, Sony/Nortel branded models | Licence or trademark problems |
| Poly Haven Victorian/gothic sofas, school desk, modern cabinets | Wrong era |
| ambientCG OfficeCeiling sets | Lights baked in |
| FreePBR, textures.com, ShareTextures | Licence terms |
| SummerEngine "CC0" listings | AI-prompt provenance |

### 2.5 Licence hygiene

- **Concept-only use of the IP.** No wiki text, wiki images or named wiki inventions; that triggers CC BY-SA 3.0 (03). No film or Kane stills in the project (02).
- Courtesy credit line: "Inspired by the Backrooms creepypasta and the Backrooms Wiki community (CC BY-SA 3.0). Textures and models from Poly Haven and ambientCG (CC0)."
- Record source URL and download date per asset in `LICENSE.txt`, and per prefab in its sidecar `tags`, e.g. `src:polyhaven/GreenChair_01`.

---

## 3. Film shot → game landing plan

### 3.0 Shot index [critic: added so this document stands alone]

**Counts.** 02 catalogues 34 entries: 0A, 0B, F01–F19, T01–T09 and TT01–TT04. Four are duplicate frames (0B = F02, F10 = F01, F15 = F04, F16 = F03), which leaves **30 distinct real frames**.
- **23** show furniture or office-type dividers.
- **13** show the distorted, repeated or embedded furniture the brief asked for: 0A, 0B, F01, F04, F08, F17, F18, T01, T02, T03, T06, T09 and TT02.

**Status.** "Viewed" means 02 looked at the image in a browser. Nothing was downloaded, and no still is in the project or the scratchpad (the critic checked the scratchpad). Trailer and teaser times are ±0.5 s.

**Trailer** = https://www.youtube.com/watch?v=0HjdiohVOik. **Teaser** = https://www.youtube.com/watch?v=tKGhxMi50y8.

**Stills and set photos**

| ID | What it shows (distortion) | Source page | Status | Archetype |
|---|---|---|---|---|
| 0A | Red's Still A: low sprawl of tilted case goods, satellites, stud doorway with blue tape | https://www.dezeen.com/2026/05/29/backrooms-production-design-danny-vermette-interview/ (BTS photo by Wendigoon) | Viewed | A2, A7 |
| 0B / F02 | Red's Still B: tall pile, repeated ladder-backs, sofa slab, CRT, torchiere (film-scan colour) | https://fastcompanybrasil.com/design/backrooms-como-a-a24-deu-vida-ao-lugar-mais-assustador-da-internet/ | Viewed; photographer credit [UNVERIFIED this run] | A1 |
| F01 / F10 | Same pile, warm, man walking past; ≥ 4 identical ladder-backs; teal escapee chair | Surface https://www.surfacemag.com/articles/a24-backrooms-production-design/ ; Galerie https://galeriemagazine.com/how-horror-hit-backrooms-terrorizes-viewers-with-design/ (credit Asterios Moutsokapas) | Viewed; Surface image list re-confirmed by the critic | A1 |
| F03 / F16 | Raked floor rising to a shrinking space (no furniture) | Fast Company Brasil; Dezeen | Viewed | Squeeze room (not a pile) |
| F04 / F15 | Showroom: symmetric rows of identical recliners | Surface; Dezeen | Viewed | A3 row |
| F05 | Endless corridor, trailer DTR1 00:00:43 (no furniture) | Surface | Viewed | Corridor rhythm |
| F06 | Wall, column, chair rail, film 00:37:55 | Surface | Viewed | Shell vocabulary |
| F07 | Mannequins between wood-capped half-walls | Surface | Viewed | A6 |
| F08 | Hatch view: lone oversize leaning throne, half-shoes in the carpet | Galerie; the Curbed caption confirms throne and shoes | Viewed | A4, A5 |
| F09 | Lone veneer door in an empty room | Galerie | Viewed | A7 |
| F11 | Mary's 1990s office (undistorted) | Galerie | Viewed | Era and material calibration |
| F12 | Showroom strip-light ceiling | Curbed | Viewed | — |
| F13 | Custom troffers with flat opal lenses (BTS, Sela Shiloni) | Curbed | Viewed | Lens (§6.1) |
| F14 | Store vignettes: floating sofa and armchair islands | Dezeen | Viewed | A8 |
| F17 | Camcorder 4:3: tilted fretwork dresser and hutch as a foreground frame, column hall | https://manofmany.com/entertainment/movies-tv/backrooms-trailer-a24-explained | Viewed; trailer time [UNVERIFIED] | A2 foreground |
| F18 | Floral armchair sunk to the seat line, basement | Man of Many (= teaser opening) | Viewed | A4 |
| F19 | Pony wall, square pier, chair rail (no furniture) | Man of Many | Viewed; provenance [UNVERIFIED] | A6 |

**Trailer and teaser frames**

| ID | What it shows (distortion) | Source | Status | Archetype |
|---|---|---|---|---|
| T01 | Dark showroom, recliner rows | Trailer 0:05–0:09 | Viewed | A3 |
| T02 | The F01 pile as a foreground wall | Trailer 0:31–0:33 | Viewed | A1 reveal |
| T03 | Two lone wooden chairs, random yaw, column hall | Trailer 0:53 | Viewed | A5 |
| T04 | Camcorder: upright dressers (the "normal" copy) | Trailer 1:05 | Viewed | A2 source |
| T05 | Pastel floral sofa, pleated lamp | Trailer 1:25.5 | Viewed | B12 reference |
| T06 | Corridor drift of 10+ identical wooden chairs | Trailer 1:32 | Viewed | A3 drift |
| T07 | Lamp-lit dining island inside the grid | Trailer 1:47 | Viewed | A8 |
| T08 | Hat-stand silhouette in the foreground | Trailer 1:50 | Viewed | A8 |
| T09 | Row of white plastic patio chairs at the pool | Trailer 2:06.5 | Viewed | A3 |
| TT01 | Basement armchair, normal state | Teaser 0:01–0:15 | Viewed | A4 setup |
| TT02 | Same armchair lower, arms on the floor | Teaser 0:19–0:21 | Viewed; "sunk" is 02's reading [UNVERIFIED] | A4, revisit change |
| TT03 | Wedge alcove to a dwarf door | Teaser 0:23–0:36 | Viewed | A7 |
| TT04 | Open office of pony-wall counters | Teaser 0:38–0:47 | Viewed | A6 |

**Gaps (02 §6).**
- No still was found for the "couches buried in walls" that Moria describes.
- The second teaser (`BjRndcTYqJo`), the promo (`2z6a6NUFlsU`) and the clip (`Pb8KqfkLe24`) were not scrubbed.
- The IMDb, Letterboxd, ShotDeck and FilmGrab galleries were not checked.

### 3.1 Archetypes

Shot IDs are from 02. "Code" is the `FrontRoomsFurniturePile.Tableau` value, or another owner.

**A1 — Tower pile** (shots 0B, F01, F02, F10, T02)
- Code: `CentreSculpture`, tower mode.
- Recipe:
  - Base: 2–3 heavy uprights (crate+pallet, ply cabinet, display cabinet).
  - Lean: 2 soft or large pieces (sofa on end, armchair on its back), plus 1 `TipOnEdge` (step stool or bookcase).
  - Stack: 3–5 light pieces, ≥ 1 exactly inverted.
  - CopyPaste: one run of 3–4 ladder-backs.
  - Topper: the floral sofa slab, plus the CRT TV facing the approach.
  - Spike: torchiere, ≤ 8° tilt.
  - Escapee: the teal club chair at R + 0.8–1.5 m.
  - 12–20 pieces; mass ≤ H − 0.25.
- Gameplay: landmark, loop obstacle, LOS breaker. Hide hollow in ≤ 30%.
- Camera reveal: from a doorway 6–10 m away, three-quarter view, pile off-centre. Or as a **foreground side wall** 1.5–3 m beside the entry (T02).

**A2 — Sprawl pile** (shots 0A, F17, T04)
- Code: `CentreSculpture`, sprawl mode. Add a `Tableau.Sprawl` value or a mode flag.
- Recipe:
  - 2 upright anchors (pedestal desk, credenza).
  - 2–3 case goods in `EdgeLean` 35–50° (chest at 40°, hutch at 45°).
  - 1 small piece `Side` (nightstand); the urn lying down; the pleated lamp upright on the highest top.
  - The bergère tipped back.
  - 2–3 satellites at 0.8–1.5 m (side table, bar stool, rolling cabinet).
  - Height ≤ 0.6 × H, width ≤ 2R.
- Gameplay: crouch cover. Does not block standing LOS.
- Camera reveal: low enough that the troffer grid and a far doorway read over it. Pair with A7 (stud doorway) 4–8 m away.

**A3 — Copy-paste row / chair drift** (F04, F15, T01, T03, T06, T09)
- Code: `CopyPasteRow`, plus a new corridor drift mode.
- Recipe:
  - Row: 4–8 identical seats, same yaw, 0.9–1.0 m pitch, facing a door or blank wall. The Office version uses task chairs facing a wall.
  - Drift: 8–20 ladder-backs along a corridor wall, densest at the far end; yaw ±25°, 15% reversed, 5% on their backs.
  - Colliders only on the 2 nearest chairs.
- Gameplay: rhythm and landmark in corridors; soft obstacle near the player.
- Camera reveal: down a long axis; it reads as a crowd.

**A4 — Sunk / embedded / half-object** (F08 half-shoes, F18/TT02 sunk armchair; Dezeen; Moria)
- Code: **new** `Embedded` (P2). Needs the 6-argument `Build` overload, which passes wall planes and `keepClear`.
- Recipe:
  - Pre-cut, capped meshes: `Kit_ClubChair_Sunk30` (cut 0.30 m above the floor plane), `Kit_Sofa3_WallHalf` (wall plane at 40% depth), `Kit_ShoeHalf`.
  - Crease/dust ring decal.
  - Wall embed ≤ wall thickness − 0.02 (0.14 m in the map) unless the back is solid void.
- Gameplay: uncanny landmark; the trigger for revisit changes.
- Camera reveal: through a frame-within-frame (hatch, doorway).

**A5 — Lone object in a void** (F08 oversized throne; T03 two lone chairs; POOLS)
- Code: `ZeroPile` (+ oversize option).
- Recipe: one seat at 70–80% room depth, axis-aligned or yawed 0/35/90°. Optionally a 1.3–1.5× uniform-scale "throne" (bergère) tilted 5–12°, **only in Tall zones**.
- Gameplay: bait. Put the zone key or a note here, so the player is pulled into open floor.
- Camera reveal: through a doorway or interior window.

**A6 — Dividers that go nowhere** (TT04, F07, F19, Moria)
- Code: **`OfficeKit.Dress` anomaly layer**, not the pile (§4.8).
- Recipe: a panel run continues 1.5–3 m past its pod and dead-ends at a column or nothing; or a closed pod with no opening; or an opening facing the wall.
- Gameplay: hide when crouched, see over when standing.
- Camera reveal: reads from the spine.

**A7 — Wrong doorway** (0A stud doorway, TT03 dwarf door, F09, Dezeen "halfway up the wall")
- Code: map arch kit (`Kit_DoorwayStuds`, a dwarf door 0.6 × 1.1, a high door with sill 1.2–1.6).
- Recipe: studs at 406 mm centres plus a blue tape outline and floor strip.
- Gameplay: path choice. Unfinished = passable; dwarf = crouch-only, a shortcut the Hunter can't take; high = an unreachable landmark.
- Camera reveal: secondary focal point in the A2 frame.

**A8 — Lamp-lit domestic island** (T07, T08, T05, F14, F11)
- Code: new room dressing (P3), not a pile.
- Recipe: troffers off; sofa + club chair + side table + pleated lamp (2700 K) + torchiere (3000 K); a tall foreground silhouette (hat stand) beside the entry.
- Gameplay: safe-room or ambush beat.
- Camera reveal: entering out of a lit hall.
- Cost: 1 shadowed and 2 unshadowed point lights.

**Ceiling-stuck** (0B "nearly touching"; Elle "ceiling-sweeping")
- Code: `CeilingStuck` (exists).
- Recipe: a column of 6–10 alternating upright/inverted copies of one seat or crate, floor to ceiling; the last piece sinks ≤ 0.12 m into the grid, with a tile cut-ring trim.
- Gameplay: landmark in Low zones.
- Camera reveal: the ceiling is in view in 2.4 m rooms.

**Office cluster** (06; replaces Codex's memory bleed)
- Code: `OfficeCluster` (exists).
- Recipe: one full workstation (desk + CRT + task chair + panel) pasted 2–3×, each `SideLay` or `EdgeLean` 35–45° onto the previous; papers as satellites. ≤ 2.0 m.
- Gameplay: the "the workstation was pasted three times" beat in Office halls.
- Camera reveal: off the spine, visible from the entry.

### 3.2 Where each appears (per eligible room; chances × tier factor in §3.3)

| Space | Eligibility | Chance | Mix | Notes |
|---|---|---|---|---|
| Level 0 normal hall (2.9 m) | non-Office room, min side ≥ 4 cells (the current `Furnish` rule) | 35% (`pileChance`) | Tower 45% · Sprawl 25% · Row 15% · CeilingStuck 5% · ZeroPile 5% · Embedded 5% (P2) | Domestic palette; office pieces ≤ 20% |
| Tall zone (5.4 m) | same | 60% (current rule) | Tower (cap 3.6 m) 40% · ZeroPile / oversized throne 35% · Row 25% | Never CeilingStuck; pieces can't read near a 5.4 m ceiling |
| Low zone (2.4 m) | same | 25% | CeilingStuck 40% · Sprawl (cap 1.5 m) 40% · Row 20% | No tower: no room for a spike |
| Office hall (≥ 4×4 cells) | Office theme | **15%** (new; called from `Dress` after pods) | OfficeCluster 50% · Tower (office mix 35–40%) 35% · task-chair Row 15% | Outside the spine and pods, with a ≥ 2 m clear ring |
| Office workroom (< 4×4) | Office theme | 0% | — | The §4.8 anomaly layer instead |
| Corridor (1-cell-wide run ≥ 4 cells) | any theme | 20% | Chair drift (A3) | Cheapest landmark; 1 mesh |
| Streamed Office room (11.5 × 12 × 2.9 m) | room train, if still used | 0% pile | `Dress` preset §4.11 + revisit change | Keeps the train cheap |
| **First pile of a run** | first eligible Level 0 hall after the Relay release | **100%, forced** | Hero tower: offline-baked template (06 §7.4), seed only picks yaw / mirror | The film's first Backrooms room and Clark's "proof object" (01 S16) |

**[critic] Reachability of these rows under the spec and the current `Furnish`.**
- **Low zone row.** Unreachable: Low rooms are 2 × 2–3 cells, below the 4-cell minimum.
- **Office rows.** Office rooms max out at 4 × 4. The pile happens only if `Dress` calls `Build` itself (06 §7.4), and then it displaces pods (decision 9).
- **Corridor row.** Needs a new map hook; `Furnish` iterates `data.rooms` only.
- **Streamed Office room.** Legacy only. The game now runs on `FrontRoomsMapWorld`; the stream is the title corridor and the lookdev preview (spec §11; project memory).
- **First pile of a run.** `Furnish` is a pure function of chunk coordinates and seed and has no run order. "First" must be defined spatially (for example, the nearest eligible hall to the spawn chunk) or it breaks the rebuild-identical rule (spec §1).
- **Level 0 normal hall row.** Fires only in 4 × 4 Standard rooms (11.84 m clear).
- **Tall zone row.** Fires in 5–7-cell Tall rooms.
- **Pillar collision.** The spec's known gap applies: Tall-hall pillars are not yet kept out of the pile disc.

### 3.3 Escalation

Use the DP08 tier proposal (tiers 1–5) as `intensity` = 0.2 / 0.4 / 0.6 / 0.8 / 1.0.

| Intensity drives | Range |
|---|---|
| Pile chance factor | 0.6× → 1.4× |
| Piece count | 0.6× → 1.3× |
| Height ratio | 0.6 → 0.95 of the cap |
| Unlocks | Embedded and CeilingStuck from 0.5 up; the 1.15× "too big" copy and the mirrored leaf from 0.6 up |

This mirrors "begins as merely drab … culminates in ceiling-sweeping piles" (01 S3), and "the more times it remembers something, the less it does" (01 S17): later copies drift further from right.

### 3.4 Consolidated pile build rules (for `FrontRoomsFurniturePile`)

1. **Exact duplicates.** One chair mesh per pile (`Kit_LadderBackChair`). One sofa variant per pile. One odd-colour piece per pile (teal, blush or violet).
2. **Orientations are quantised:** Upright, Back, Front, Side (exactly 90°), Inverted (180° ± 2°), EdgeLean 30–52° found by bisection to first contact plus a 2–6° jam. Never 3–15° "drunk" tilts.
3. **Support or embed.** Every piece rests on the floor or a support face within 1 cm, has two contacts (EdgeLean), or is ≥ 30% buried as a deliberate embed.
4. **Overlap budgets** (06): per class `tolerance` (Seat 0.45, Table 0.35, Case 0.20, Soft 0.30, Screen 0.15); copy pairs ≤ 0.45; nest pairs ≤ 0.70; nothing swallowed > 0.80; global ≤ 0.22 (the code already uses 0.22).
5. **No z-fighting.** Reject faces parallel within 2° and closer than 3 mm. Nudge by 8–15 mm, or rotate 3–5°. Every copy-paste offset gets ≥ 1 cm vertical or ≥ 3° yaw.
6. **Readability.** ≥ 60% of each piece's silhouette is visible from an entry. ≥ 4 material families and 2 value groups.
7. **Collision.**
   - Per-piece colliders off.
   - 2–4 blocker boxes on the convex XZ hull, 1.8–2.0 m tall. Small satellites are walk-through.
   - **Return the footprint** (`Bounds` is allowed by the reflection lookup).
   - `Furnish` marks every 3 m cell whose centre is within 0.75 m of the footprint as Hunter-impassable.
   - The validator then re-checks entry-to-entry connectivity. If it fails, rebuild with seed + 1 (at most 3 tries), then skip the pile.
8. **Rendering.**
   - Shared `Prop_*` materials, no MPBs.
   - Satellites: `ShadowCastingMode.Off`.
   - `StaticBatchingUtility.Combine(pileRoot)` on Standalone. WebGL has static batching off, so it relies on the SRP Batcher only.
   - A GPU Resident Drawer quality option on Mac (off by default; profile first).
9. **Grounding.** SSAO (existing). A blob/dust-ring quad, 1.2× the footprint at 15–25% opacity, the same mesh for all piles. Scuff decals under EdgeLean pieces once the URP Decal feature exists (Screen Space technique for WebGL).
10. **Light.** The pile centre is within 1 m of a **lit** fixture (force that fixture to stay alive). No special light on the pile; the film used only the ceiling grid (01 S10/S12).
11. **Determinism.**
    - Counter-based hash RNG with sub-streams per decision, as the code already does.
    - Stable sorted library order; no `UnityEngine.Random`; no dictionary iteration.
    - **Layout seed excludes `data.revision`.** Revision feeds only the revisit-change stream (risk R2).

### 3.5 Camera-reveal checklist (per placed tableau, as an EditMode capture test)

1. Visible from at least one entry within the first 2 s of walking in, at 1.6 m eye height and 72° vertical FOV.
2. Off-centre, on a third, unless symmetry is the point (A3 row).
3. The troffer grid is visible above it.
4. ≥ 30% empty floor in the lower frame.
5. Capture `Verification/lookdev/pile_<tableau>_<seed>.png` from each entry and judge it against Stills A and B (02 §5).

---

## 4. Office layout rules — `FrontRoomsOfficeKit.Dress(Transform parent, Rect floorXZ, float ceilingHeight, int seed, Rect[] keepClear)`

These rules keep the existing contract: parent-local metres, edges are walls except where a keepClear strip touches them, a pure function of the seed. They extend the existing order (columns → wall units → pods). The only API change is a return value: the occupied footprints, as `Rect[]` or a cell mask.

**[critic] Binding numbers from LEVEL_MODULE_SPEC §6 that this section must respect.**
- **Room sizes.** Office rooms are 2–4 cells a side (clear 5.84 / 8.84 / 11.84 m) at H = 2.9 only.
- **keepClear strips.** 1.0 m deep (1.2 m at doors), spanning the full 3 m cell edge.
- **Aisles.** Every strip stays connected through aisles ≥ 1.0 m (`MinAisle`); the pod chase lane is 1.6 m (`Aisle`).
- **Wall units.** They sit `depth/2 + 0.03` from the wall **face**, which is 0.08 m inside the rect edge, and keep a 0.5 m service zone.
- **Height.** Nothing taller than H − 0.05.
- **Room budget.** ≤ 3 ms, ≤ 120 renderers, ≤ 40 colliders, ≤ 60k tris.

So every rule below that mentions 2.4 m or 5.4 m Office zones, rooms larger than 4 × 4, or short sides ≥ 15 m is **moot** under the current generator. Those rules are kept only in case the map chat widens Office carving.

### 4.0 Grid

Everything snaps to a **0.6 m module** from the room's world origin. The 3 m map cell is 5 modules, which matches the 2'×2' tile and the 24" carpet tile (03 R1).

Asset widths follow the module:

| Item | Width (m) |
|---|---|
| Panel | 1.52 or 0.76 |
| Desk | 1.52 |
| Pod pitch | 1.80 |

The carpet tile is 0.6096 m, but its world TileSize stays 256/420 m to satisfy the 256 m rebase rule (05). The 0.0096 m drift is invisible.

**[critic] Superseded by spec §4–5 (P0b, agreed direction).**
- The ceiling grid becomes 0.6 × 0.6 anchored at world (0, 0), and the Office carpet tile becomes 0.6 m.
- The title-stream rebase moves from 256 m to **240 m**.
- The 2'×4' lens fills tiles X [1.2, 1.8], Z [1.2, 2.4] of each cell, so its long axis runs along **world Z**, not "the room's long axis" (§6.1).
- Imperial asset widths (1.524 desk and panel) do **not** follow the 0.6 module. Only placement origins snap to it.

### 4.1 Room classes (seeded mix, 03 R2)

Size is in 3 m cells.

| Class | Size | Share when the size allows | Content |
|---|---|---|---|
| **Small office** | ≤ 2×2 cells (≤ 36 m²) | special, 15% of Office rooms | One of: manager office (`Kit_OfficeDesk` + chair + CRT + 2 filing + window); copy room (copier + 2–4 filing + bin + paper); break room (2 vending + cooler + 2 task chairs facing the wall) |
| **Workroom** | 2×3 to 4×4 cells | 40% | 1–3 pods + 1–3 wall units + columns if ≥ 9 × 9 m |
| **Open hall** | > 4×4 cells, or ≥ 150 m² (**[critic] unreachable: the largest Office room is 4×4, 140 m² clear. Use 4×4 rooms as the open hall**) | 45% | Columns (spec: ≤ 4 in a 12 m room, 0.61 m), a 2.4 m spine, 2–4 pods only beside the spine (the target composition), 3–5 wall units, 1 interior window, carpet ghosts; ≥ 40% of the floor left empty |

### 4.2 Reservation (before anything is placed)

1. Take every `keepClear` rect expanded by 0.35 m (the existing code). **[critic]** The code at 15:40 expands by **0.25 m** (`FrontRoomsOfficeKit.cs` line 235).
2. **Chase spine.** Connect the centres of the entry strips with straight or L-shaped lanes. Width: **≥ 1.6 m** (`Aisle`) everywhere; **2.4 m** in halls; **3.0 m** when the room's short side is ≥ 15 m. In single-entry rooms, run the spine from the entry to the far wall.
3. **Side aisles** between pods: ≥ 1.6 m when the aisle connects two lanes. Dead-end pockets inside or behind a pod may be 0.9–1.1 m, but they never lie between two entries.
4. **Hunter lanes.** After placement, compute the 3 m cells whose centres are covered (±0.75 m) by pods, wall units deeper than 0.5 m, or piles. Return them to `Furnish`. The validator requires every pair of entries to stay connected through unblocked cells. If they don't, drop the last pod placed and retry, at most 3 times.

### 4.3 Structure

1. **Columns** only at **map cell corners**, every 2nd corner in each direction (6 m bay), in rooms ≥ 9 × 9 m.
   - **[critic] Spec override.** At most **1 in a 9 m room and 4 in a 12 m room**, none in 2-cell rooms, **0.61 m** square. Red rejected pillar-heavy spaces (project memory; spec §6; code header).
   - The target's columns read about 0.9–1.2 m; that is open question Q11.
   - Drywall-wrapped, **0.9 × 0.9 m** (see the override above), 25 mm bevel (corner bead), cove base.
   - **Skip** a corner where the map already placed a pillar (`data.pillar`) or that falls inside a reserved lane. Drop it rather than move it, so the bay rhythm is kept.
2. **Bulkhead** (target): between column pairs along the room's long axis, 0.9 wide × 0.35 deep, only when H ≥ 2.9. Troffers skip bulkhead cells.
3. In 5.4 m Office zones, add a **lowered soffit ring** 0.6 m from the walls at 3.0 m. Panels alone look like dollhouse props under a 5.4 m ceiling (03 R9). **[critic] Moot:** Office is Standard (2.9 m) only.

### 4.4 Perimeter (wall units), on walls not touched by keepClear

Clearances:
- Back 0.05–0.08 m from the wall. **[critic] Spec:** `depth/2 + 0.03` from the wall **face**, which is 0.08 m inside the rect edge.
- Yaw jitter ±1.5°.
- Never within 1.2 m of a corner the spine turns through.
- 0.9 m of clear floor in front of the copier and vending machine. This is stricter than the spec's 0.5 m service zone, which is the minimum.

| Unit | Frequency | Placement rule |
|---|---|---|
| Vending machine | 1 per room ≥ 6 × 6 m; ≤ 1 per 150 m² | Against a wall, ideally visible from the main entry (it is a colour accent) |
| Water cooler | 1 per ~100 m² | Beside a column face or a pod end-panel (target), never in a corner |
| Copier | 1 per 150 m² | Against a wall or a free panel end |
| Filing cabinets | Runs of 2–6 identical units; 1 in 6 rooms runs the **full wall length** (A6 anomaly, Moria) | Butted edge to edge |
| Interior window | ≤ 1 per room | Centred in a 3 m cell on a wall with no keepClear within 1.5 m. **[critic]** Spec: 2.44 × 1.22, sill 0.90, no collider. The target shows a dim room beyond, not black (T15) |
| Wall details | 0–2 | Clock at 2.1 m; switch plate at 1.2 m beside entries; notice board |

### 4.5 Pods (cubicle islands)

**Station:** desk 1.52 × 0.76 against a panel, plus a 0.9 m chair zone. Station footprint: 1.80 × 1.70 m. **[critic] Spec and code:** the station is **1.524 × 1.70**, and a 2 × 2 back-to-back pod is **3.10 × 3.45**. The 1.80 figure is not used anywhere in the code.

**Pod types:**

| Type | Footprint (incl. chair zones) | Use |
|---|---|---|
| P1 single L | 1.8 × 1.8 m (1 station + end panel) | Small rooms and hall edges |
| R2×N back-to-back rows, N = 1–3 | 1.8N + 0.06 × 3.5 m. **[critic]** Use (1.524N + 0.06) × 3.45 m | Default workroom pod |
| P4 pinwheel | 3.6 × 3.6 m (4 stations around a cross spine). **[critic]** Not in the spec or the code; a proposal | Halls; reads as an "island" from every side |

**[critic] Fit check** (spec §6 table; aisles 1.6 m).
- A free-standing back-to-back pod needs 6.65 m, so it fits only rooms of 3 cells or more.
- 2-cell rooms (5.84 m) take a single wall row, or a pod with one long side on a wall.

**Panel height:**

| Zone | Height |
|---|---|
| 2.4 m zones | 1.37 m (**[critic] moot**: Office is 2.9 m only) |
| Default (the target) | 1.52 m (**[critic]** the live mesh is 1.57) |
| 10% of pods | 1.65 m. This is the only height that blocks the Hunter's 1.6 m sight ray (spec §7) |
| 5.4 m zones | 1.65 m, plus the soffit ring (**[critic] moot**) |

Panels sit 0.02 m above the floor on a dark base rail.

**Orientation:** each pod's open side faces the spine, so desks and CRTs are visible from the aisle (target).

**Spacing:** ≥ 1.6 m between pods and between a pod and a column, wall or wall unit wherever that gap is a lane; ≥ 0.9 m otherwise.

**Count:**
- Workroom: `round(freeArea / 45 m²)`, clamped to 1–3.
- Hall: `round(freeArea / 80 m²)`, clamped to 2–4, and only in the bays beside the spine.
- **[critic]** The live code uses `round(area / 24)`, clamped to 1–8, so it is much denser. Whatever count is chosen must also fit the 60k-tri room budget (§5.3). The live LOD0 cost per station is about 34–42k tris: desk 6,870 + 1–2 panels at 3,892 + CRT 3,032 + task chair 11,684 + paper 1,754 + bin 2,428, plus a PC at 8,460 where present. So the budget holds 1–1.5 stations today.

### 4.6 Station dressing (all seeded per station)

| Item | Rule |
|---|---|
| CRT | 80% of desks, set back 0.15 m. **1 in 6 on**, a dim blue-grey `_On` variant |
| PC desktop | Under 40% of CRTs |
| Keyboard | In front of the CRT, ±3 cm, yaw ±4° |
| Mouse | 80% |
| Phone | 50% |
| Paper / binders | 1–3 items per desk (03 R10: at most 3) |
| Bin | 60%, under the desk end |
| Task chair | 75% of stations, pushed out 0.2–0.6 m, yaw ±35°, 10% turned away |
| Paper on the floor | 1 in 6 stations |

### 4.7 Floor and wall traces

- **Carpet ghosts** (Fandom L4 "indents"): in empty hall floor, 2–6 decals or baked mask stamps. Rectangles 1.52 × 0.76 for removed desks; 4-dot chair marks; 0.9 m panel lines.
- Blotches near the cooler and vending machine.
- Traffic darkening along the spine (macro mask).
- Wall scuffs at 0.7–0.9 m behind stations.

### 4.8 Anomaly layer (at most 1 per room, seeded; 0 in the first Office room of a run)

| Anomaly | Chance | Source |
|---|---|---|
| None | 50% | — |
| Divider that goes nowhere (panel run continues 1.5–3 m into nothing, or a closed pod) | 15% | Moria; TT04 |
| Full-length filing-cabinet wall | 10% | Moria |
| Identical task chairs crowding one station (6–12, copy-paste row) | 10% | 01 implication 11c |
| Every CRT at the identical angle and identically "on" | 5% | 01 S24 "remembers wrong" |
| Mirrored sign or label on 1 in N labels | 5% | 01 S24 |
| Domestic piece leaking into the office (one ladder-back or bergère at a desk) | 5% | 01 S5, "store stock pulled in" |

### 4.9 Density by room size

| Room (cells) | Area | Pods | Wall units | Columns | Window | Ghosts | Pile (via §3.2) |
|---|---|---|---|---|---|---|---|
| 1×N corridor | — | 0 | 0–1 filing | 0 | 0 | 0 | Chair drift 20% |
| 2×2 | 36 m² | 0–1 (small office) | 2–3 | 0 | 0–1 | 0 | 0 |
| 2×3 / 3×3 | 54–81 m² | 1–2 | 2–3 | 0 (≥ 9 m: 1–4) | 0–1 | 0–1 | 0 |
| 3×4 / 4×4 | 108–144 m² | 2–3 | 3–4 | 2–4 | 1 | 1–2 | 0 |
| ≥ 4×5 | ≥ 180 m² | 2–4 (bays only) | 3–5 | 4–9 | 1 | 3–6 | 15% |

**[critic] Corrections to this table under the spec.**
- The **1×N corridor** and **≥ 4×5** rows cannot occur for Office: `Dress` receives rooms only, and they are at most 4 × 4.
- **Columns** must read: 2×2 → 0; 3×3 → ≤ 1; 3×4 / 4×4 → ≤ 4 (only 4×4 is guaranteed up to 4).
- The 2×2 row is the smallest Office room (5.84 m clear).
- The Pile column applies only to 4×4 rooms (decision 9).

### 4.10 Determinism and validation

1. **Sub-streams per phase**: `Rng(Hash(seed, phaseSalt))` for columns, wall units, pods, dressing and anomaly. Adding a phase must not reshuffle the others. Today there is one shared `Rng`; split it.
2. No `UnityEngine.Random`, no physics, no dictionary or hash-set iteration, and no `Transform` reads mid-solve.
3. Layout uses a seed **without** `data.revision`. Revision drives only the revisit-change stream: on revision > 0, one prop swaps to its twin (sunk, inverted or duplicated) — TT02, 02.
4. EditMode tests:
   - Same seed twice → identical (asset, position rounded to 1 mm, yaw rounded to 0.1°) list.
   - 500 seeds × {6×6, 9×12, 12×12, 18×24} × {2.4, 2.9, 5.4}.
   - Nothing outside `floorXZ`, nothing in keepClear, nothing taller than H − 0.05.
   - A 0.8 m capsule path exists between all entries (0.25 m grid BFS).
   - The Hunter cell mask keeps all entries connected.

### 4.11 Streamed Office room preset (11.5 × 12 × 2.9 m, if the room train is still used)

**[critic]** The game no longer plays through the room train. The stream is only the title corridor and the edit-mode lookdev (spec §11; project memory, 2026-10-02), so this preset is for lookdev captures only. Its composition maps onto a 4 × 4 map room (11.84 m clear).

- A 2.5 m spine on the door axis.
- One P4 pinwheel or R2×2 on each side.
- A wall run on one side: copier + cooler + 2 filing.
- The interior window on the other side; vending machine near the exit door.
- 0 piles.
- Revisit change on the 2nd visit to the same sequence.

This is exactly the target's composition (03 R11).

---

## 5. Production spec for every asset we model

### 5.1 Global rules (kitlib)

- **Units and axes.** Metres, Z up in Blender, front −Y, standing on z = 0, centred. kitlib exports to Unity as +Z front, root scale 1 (never the old ×100 FBX root).
- **Bevels.** Every visible hard edge gets a bevel. Nothing ships with a raw box edge visible at 2 m. Add a `WeightedNormal` modifier (face-area, keep sharp) after the bevel in `finish()` so flat faces shade flat.

  | Material class | Bevel width | Segments |
  |---|---|---|
  | Case goods / wood | 3–5 mm | 2 |
  | Laminate tops | self-edge 2 mm | 2 |
  | Painted steel | 1.5–3 mm | 1–2 |
  | ABS plastics | 8–15 mm | 3 |
  | Upholstery | 25–60 mm, with `cushion()` (subdivision 1 + 3–6 mm displace + 6 mm piping) | 4–6 |
  | Turned parts | — | lathe, 16–24 sides |

- **Material slots.** ≤ 4 per asset; each slot is a submesh and a draw. Shared `Prop_*` slot materials only.
  - **[critic] The live kit already breaks this.** Copier 10, WaterCooler 10, PCDesktop 8, RollingCabinet 8, OfficeDesk 7, Dresser70s 6, TaskChair 6, Torchiere 6, FilingCabinet 6, PaperStack 5, Crate 5.
  - Under the 120-renderer room cap and the SRP Batcher this is a batch cost, not a correctness bug.
  - Either relax the rule to ≤ 6 with tiny parts merged into `Prop_Atlas`, or collapse slots in kitlib `finish()`. Decide before more assets are built.
  - Add these slots to `kitlib.SLOTS`: `Prop_WoodWalnut`, `Prop_WoodEbony`, `Prop_Chipboard`, `Prop_Studs`, `Prop_TapeBlue`, `Prop_FabricCharcoal`, `Prop_FabricNavy`, `Prop_Ceramic`, `Prop_Atlas`.
  - **Fix**: painted and powder-coated steel is **dielectric**. `Prop_SteelPutty`, `Prop_SteelBrown` and `Prop_SteelBlack` should be metallic 0 (`SLOTS` previews 0.6). Metalness comes only from the Metal016 scratch mask.
- **UVs and texel density.**
  - Tiled slots use `uv="metres"` (1 UV = 1 m) with grain along each board's long axis. Effective density = texture px ÷ the slot's TileSize:
    - wood and steel ≥ 1,024 px/m;
    - fabric ≥ 2,048 px/m (packed at 1K over 0.27 m ≈ 3,800 px/m);
    - plastics ≥ 1,024 px/m.
  - Unique art uses `uv="decal"` into **one shared `Prop_Atlas`** (2048², FrontRooms/Surface, `_FR_MESH_UV`, TileSize 1):

    | Atlas region | Density |
    |---|---|
    | CRT screen states: off / on / dusty | 1,024 px/m (hero) |
    | Vending front, snack art (invented) | 1,024 px/m |
    | Copier panel | 1,024 px/m |
    | Keyboard legends | 1,024 px/m |
    | Labels, filing label holders, crate stencil, stud grade stamp, switch plates | 512 px/m |

  - The atlas replaces the separate `Prop_Label`, `Prop_VendingFront`, `Prop_CopierPanel` and `Prop_KeyboardKeys` slots: one material, fewer state changes.
- **Trim strategy.** Case goods share the veneer slot for carcass and fronts. Drawer reveals are geometry (4–6 mm gaps, 3 mm deep), not texture, because the light is flat top-light and only real reveals cast lines. Edge banding on laminate is a 2 mm bevel in the same slot. Ply edges are a 6-stripe GEN strip mapped by U on `Prop_Plywood`'s second tile region.
- **LOD.** kitlib exports `<Name>_LOD1` (bevel segments → 1, planar decimate at 5°, 40–50% of LOD0). Unity `LODGroup` thresholds:
  - LOD0 ≥ 10% screen height;
  - LOD1 ≥ 2% (large pieces) or 3% (desk props);
  - culled below.
  - Desk props under 600 tris get no LOD1, culled at 2.5%.
- **Colliders.** 1–3 sidecar boxes per asset. Small desk props have none. Pile pieces' boxes are disabled by the pile (blockers instead). Chairs are static, not pushable.
- **Shader.**
  - All opaque props use `FrontRooms/Surface` with `_FR_MESH_UV`. This matches the room shells, gets the cavity mask and stays on one SRP-Batcher variant.
  - Only `Prop_Glass` and `Prop_BottleBlue` use **URP Lit Transparent** (2 materials). CRT glass stays opaque.
  - Add to `FrontRooms/Surface` (inside the UnityPerMaterial CBUFFER; default 0 = no change for existing materials):
    - `_SheenColor` and `_SheenPower`: a fresnel-tinted albedo for velvet and chenille;
    - `_MacroStrength`: set ≤ 0.3 on props, so world-space macro wear does not make copy-paste duplicates visibly different (rule 1 of §3.4).
- **Import.** Albedo sRGB; `_N` as Normal Map; mask linear. Max size: 2048 for case goods; 1024 for fabrics, plastics, steel and the atlas. ASTC 6×6 on Mac; DXT/BC fallback for WebGL. Mipmaps on.

### 5.2 Slot material table (the look lives here)

Albedo targets are in sRGB, after regrade. Smoothness is the range in the mask's R channel.

| Slot | Source | TileSize (m) | Albedo target | Smoothness | Notes |
|---|---|---|---|---|---|
| `Prop_WoodCherry` | PH lacquered_cherry_wood | 1.0 | #5A2A18 | 0.65–0.75 | Lacquer highlight |
| `Prop_WoodOak` | PH red_oak_veneer (golden) | 1.0 | #9A6A3A | 0.50–0.58 | Chairs, bookcase, curio |
| `Prop_WoodTeak` | PH teak_veneer (orange) | 1.0 | #A0582A | 0.48–0.55 | Chest of drawers |
| `Prop_WoodDark` | PH dark_wood | 2.0 | #2E1C14 | 0.55–0.62 | — |
| `Prop_WoodEbony` | PH dark_wood, darkened | 2.0 | #1C1410 | 0.62–0.70 | Hutch |
| `Prop_WoodWalnut` | PH walnut_veneer | 1.8 | #4A3020 | 0.48–0.55 | — |
| `Prop_WoodLaminate` | PH red_oak, pores removed | 1.0 | #8E6E4C | 0.58–0.64 | Woodgrain laminate |
| `Prop_LaminateBeige` | GEN stipple | 0.5 | #C9BEA0 | 0.40–0.46 | Desk tops |
| `Prop_Plywood` | PH plywood + GEN edge strip | 0.5 | #B8936A | 0.25–0.32 | — |
| `Prop_Chipboard` | aCG Chipboard004 | 1.0 | #9C8466 | 0.20–0.28 | Backs |
| `Prop_PinePallet` | aCG Planks021 | 1.4 | #A88A62 | 0.15–0.22 | — |
| `Prop_Studs` | aCG Wood096 | 0.5 | #C9AE84 | 0.18–0.25 | — |
| `Prop_PlasticBeige` | aCG Plastic013B normal/rough + GEN albedo | 1.0 | #D3C9AE sides; **#C8B98F tops** (yellowing, top-face mask) | 0.45–0.55 | — |
| `Prop_PlasticBlack` | aCG Plastic012B | 1.0 | #1A1A1A | 0.40–0.48 | — |
| `Prop_PlasticGrey` | aCG Plastic018B | 1.0 | #5E5E5A | 0.40–0.48 | — |
| `Prop_PlasticWhite` | aCG Plastic013B | 1.0 | #D9D5C8 | 0.45–0.55 | Cooler |
| `Prop_SteelPutty` | aCG Metal028 + Metal016 mask | 1.0 | #A8A08A | 0.38–0.48, metallic 0 | Panel trim, pedestals, files |
| `Prop_SteelBrown` | Metal028 | 1.0 | #3B2E25 | 0.38–0.48, metallic 0 | Desk frames |
| `Prop_SteelBlack` | Metal028 | 1.0 | #1E1E1E | 0.38–0.48, metallic 0 | Vending, torchiere, window frame |
| `Prop_Aluminium` | aCG Metal050C | 1.0 | #B8B8B4 | 0.50–0.60, metallic 1 | — |
| `Prop_Chrome` | GEN | — | #D8D8D8 | 0.85, metallic 1 | — |
| `Prop_Brass` | GEN | — | #B08A4A | 0.55–0.65, metallic 1 | — |
| `Prop_FabricCubicle` | PH poly_wool_herringbone | 0.27 | **#4A535C slate** | 0.10–0.18 | — |
| `Prop_FabricChair` | PH rough_linen | 0.27 | #1C1C1E | 0.12–0.18 | — |
| `Prop_FabricTeal` | rough_linen | 0.27 | #2F6B6A | 0.12–0.20 | — |
| `Prop_FabricBeige` | poly_wool_herringbone | 0.27 | #B9A88A | 0.10–0.18 | Oatmeal |
| `Prop_FabricCharcoal` | rough_linen | 0.27 | #3A3A3C | 0.12–0.18 | — |
| `Prop_FabricNavy` | rough_linen | 0.27 | #23304A | 0.12–0.18 | — |
| `Prop_FabricFloral` | PH floral_jacquard height → GEN albedo | 0.25 × 0.38 | ground #CDBFA3, motif #A89679, dusty-rose/sage accents | 0.10–0.16 | — |
| `Prop_VelvetPink` | PH velour_velvet | 0.28 | #B88986 | 0.20–0.30 | Sheen #E6C8C4, power 4 |
| `Prop_Vinyl` | aCG Leather027 | 1.0 | #151413 | 0.35–0.45 | — |
| `Prop_LampShade` | GEN pleats | — | #E2D8C0 | 0.10 | Thin; transmission faked with emission 0.05 when on |
| `Prop_Ceramic` | GEN | — | #5A3A24 | 0.75–0.85 | — |
| `Prop_Cardboard` | aCG CardboardSet001 | 1.5 | #A07E55 | 0.15–0.22 | — |
| `Prop_Paper` | GEN | — | #DCD8CC | 0.20–0.28 | — |
| `Prop_ScreenCRT` / `Prop_GlassCRT` | GEN + Fingerprints002 / Dust Wipes mask | — | #0F1412 | 0.80–0.88 | Opaque; `_On`: emission #5E7380 × 0.6 |
| `Prop_Glass` | — | — | #0E1210, α 0.22 | 0.90 | URP Lit Transparent |
| `Prop_BottleBlue` | — | — | #6E9CC4, α 0.45 | 0.92 | URP Lit Transparent |
| `Prop_TapeBlue` | aCG Tape005 recoloured | — | #2E86C1 | 0.30 | Opacity edge |
| `Prop_Atlas` | GEN unique art | 1 | — | per region | — |

Reflectance sanity (BPA, 03): ceiling tile albedo ≈ 0.8 (#E4E2D8), walls ≈ 0.5 (#BAB39E), carpet ≈ 0.2 (#6E767C blue-grey). Nothing in the kit may exceed sRGB #E6 or go below #10 in albedo.

### 5.3 Per-asset spec (LOD0 / LOD1 triangles are budgets, not estimates)

Priority (P column):
- **P0** = needed for the target office frame and the Still B tower.
- **P1** = Still A sprawl plus the arch pieces.
- **P2** = archetype extras.

The **Collider boxes** column gives the sidecar box(es); "none" = no collider. The **Pile** column gives `class, mass, states`. States: U = Upright, B = Back, F = Front, S = Side, I = Inverted, E = EdgeLean. "+top" marks a topper (a piece that crowns the pile).

**Office kit** (all P0)

| Asset | Dims (m) | LOD0 / LOD1 | Slots | Unique (atlas) | Collider boxes | Pile |
|---|---|---|---|---|---|---|
| `Kit_OfficeDesk` | 1.52 × 0.76 × 0.74 | 2,200 / 900 | LaminateBeige, SteelBrown, SteelPutty | — | 1 (full footprint × 0.74) | Table 2; U, I, S |
| `Kit_CubiclePanel` (+ 1.37 / 1.65 variants) | 1.52 × 0.064 × 1.52 | 600 / 250 | FabricCubicle, SteelPutty, PlasticBlack | — | 1 | Case 1; U, S, B (OfficeCluster only) |
| `Kit_CubiclePanelShort` | 0.76 × 0.064 × 1.52 | 450 / 200 | same | — | 1 | — |
| `Kit_PanelPost` | 0.064 × 0.064 × 1.52 | 120 / — | SteelPutty | — | none | — |
| `Kit_CRTMonitor` (done; add `_On`) | 0.37 × 0.41 × 0.41 | ≈ 3,000 / 1,200 | PlasticBeige, PlasticGrey, PlasticBlack, ScreenCRT | screen | 1 | Screen 1; +top |
| `Kit_PCDesktop` | 0.42 × 0.42 × 0.14 | 900 / 350 | PlasticBeige, Atlas | bays, LED | 1 | Small 1 |
| `Kit_Keyboard` | 0.46 × 0.19 × 0.035 | 1,200 / 120 | PlasticBeige, Atlas | legends | none | Small 0 |
| `Kit_Mouse` | 0.06 × 0.11 × 0.035 | 300 / — | PlasticBeige, PlasticBlack | — | none | — |
| `Kit_DeskPhone` | 0.20 × 0.22 × 0.09 | 900 / 300 | PlasticGrey, Atlas | keypad | none | Small 0 |
| `Kit_PaperStack`, `Kit_Binders` | 0.22 × 0.28 × 0.02–0.08; 0.29 × 0.06 × 0.32 | 200; 400 / — | Paper, Vinyl, Atlas | spine labels | none | Small 0 |
| `Kit_TrashBin` | 0.36 × 0.26 × 0.38 | 400 / — | PlasticGrey | — | none | Small 0 |
| `Kit_TaskChair` | Ø 0.64, H 0.92 (**[critic]** spec 0.66 / H 0.95) | 4,500 / 1,800 | FabricChair, PlasticBlack, Chrome | — | 1 (0.6 × 0.6 × 0.95) | Seat 1; U, I, S, B |
| `Kit_WaterCooler` | 0.32 × 0.33 × 1.32 (**[critic]** spec 0.32 × 0.32 × 1.35) | 2,500 / 1,000 | PlasticWhite, SteelPutty, BottleBlue, PlasticBlack | — | 1 | Tall 1; U, S |
| `Kit_Copier` | 0.62 × 0.66 × 1.05 (**[critic]** spec 0.62 × 0.68 × 1.15) | 2,500 / 1,000 | PlasticBeige, PlasticGrey, Atlas | panel | 1 | Case 2; U, S, B |
| `Kit_VendingMachine` | 0.94 × 0.89 × 1.83 (**[critic]** spec 0.90 × 0.90 × 1.83; 4 trays × 4 in the target) | 4,000 + 2,000 snack quads / 2,200 | SteelBlack, Glass, Atlas, PlasticBlack | front, snacks | 1 | Case 3; U, B (rare) |
| `Kit_FilingCabinet` / `_2` | 0.38 × 0.66 × 1.32 / 0.72 | 1,400 / 600; 900 / 400 | SteelPutty, Chrome, Atlas | labels | 1 | Case 2; U, B, S, E |
| `Kit_InteriorWindow` | 2.40 × 0.10 × 1.05 (**[critic]** spec: 2.44 × 1.22, sill 0.90) | 300 / — (+ fake back room, T15) | SteelBlack, Glass | — | 1 (glass plane) (**[critic]** spec: **none**) | — |

**Shared office / pile**

| Asset | P | Dims (m) | LOD0 / LOD1 | Slots | Unique (atlas) | Collider boxes | Pile |
|---|---|---|---|---|---|---|---|
| `Kit_HatStand` | P1 | Ø 0.45 × 1.80 | 900 / 350 | WoodDark | — | 1 | Tall 0; spike |
| `Kit_WallClock` | P2 | Ø 0.32 × 0.05 | 600 / — | PlasticBlack, Atlas | face | none | — |

**Pile kit**

| Asset | P | Dims (m) | LOD0 / LOD1 | Slots | Unique (atlas) | Collider boxes | Pile |
|---|---|---|---|---|---|---|---|
| **`Kit_LadderBackChair`** | **P0** | 0.45 × 0.50 × 0.98 | **1,800 / 700** | WoodOak | — | 1 | Seat 0; U, I, S, B |
| `Kit_Sofa3` (_Floral, _Oatmeal, _Charcoal) | P0 | 2.00 × 0.90 × 0.82 | 6,000 / 2,400 | Fabric*, WoodOak | — | 2 | Soft 2; U, B, S, +top |
| `Kit_ClubChair` (_Teal, _Oatmeal) | P0 | 0.85 × 0.85 × 0.82 | 4,000 / 1,600 | Fabric*, WoodDark | — | 1 | Soft 2; U, B, S, I |
| `Kit_CRTTV` | P0 | 0.52 × 0.48 × 0.48 | 2,200 / 900 | PlasticBlack, ScreenCRT, Atlas | grille, buttons | 1 | Screen 1; +top |
| `Kit_Torchiere` | P0 | Ø 0.35 × 1.83 | 500 / 200 | SteelBlack, Aluminium | — | none | Tall 0; spike |
| `Kit_DisplayCabinet` | P0 | 0.90 × 0.40 × 1.80 | 1,800 / 700 | WoodOak, Glass | — | 1 | Case 2; U, B, S, E |
| `Kit_Bookcase` | P0 | 0.90 × 0.30 × 1.80 | 700 / 300 | WoodOak | — | 1 | Case 2; U, B, S, E (nest cavities) |
| `Kit_PlyCabinet` | P0 | 0.90 × 0.45 × 1.20 | 500 / 200 | Plywood, Chipboard | — | 1 | Case 2; U, S, B |
| `Kit_Crate` (**live**: 0.90 × 0.60 × 0.70) | P0 | 1.00 × 0.80 × 0.75 | 600 / 250 | Plywood, Atlas | stencil | 1 | Crate 2; U, S |
| `Kit_Pallet` | P0 | 1.22 × 1.02 × 0.14 | 900 / 400 | PinePallet | — | 1 | Crate 2; U |
| `Kit_StepStool` | P0 | 0.45 × 0.50 × 1.00 | 800 / 300 | WoodOak | — | 1 | Seat 0; U, E, S |
| `Kit_Pouf` | P0 | Ø 0.50 × 0.40 | 800 / 300 | FabricNavy | — | none | Small 0 |
| `Kit_Chest5` (**live: `Kit_Dresser70s`**, 0.90 × 0.45 × 1.10) | P1 | 0.86 × 0.46 × 1.22 | 1,500 / 600 | WoodTeak, Brass | — | 1 | Case 3; U, B, F, S, E |
| `Kit_Nightstand2` | P1 | 0.50 × 0.40 × 0.60 | 900 / 400 | WoodOak, Brass | — | 1 | Case 1; U, S, I |
| `Kit_DeskPedestal` | P1 | 1.37 × 0.71 × 0.76 | 1,800 / 700 | WoodCherry, Brass | — | 1 | Table 3; U, B |
| `Kit_Credenza` | P1 | 1.52 × 0.46 × 0.76 | 1,600 / 650 | WoodCherry, Brass | — | 1 | Case 3; U, B |
| `Kit_DresserLow` | P1 | 1.40 × 0.48 × 0.78 | 2,000 / 800 | WoodCherry, Brass | — | 1 | Case 3; U, B, E |
| `Kit_Hutch` (_Ebony, _Cherry) | P1 | 1.00 × 0.50 × 1.90 | 2,000 / 800 | WoodEbony / WoodCherry, Brass | — | 1 | Case 3; U, B, E |
| `Kit_BergereChair` (DL) | P1 | 0.68 × 0.70 × 0.98 | 4,200 / 1,700 | VelvetPink, WoodWalnut | — | 1 | Seat 1; U, B, E |
| `Kit_SideTableTurned` | P1 | 0.46 × 0.46 × 0.66 | 2,200 / 900 | WoodWalnut, Brass | — | 1 | Table 1; U, I |
| `Kit_BarStool` | P1 | Ø 0.38 × 0.76 | 1,600 / 700 | WoodWalnut | — | 1 | Seat 0; U, I, S |
| `Kit_RollingCabinet` | P1 | 0.50 × 0.45 × 0.62 | 900 / 400 | WoodCherry, Rubber | — | 1 | Case 1; U, S |
| `Kit_LampPleated` (**live: `Kit_TableLampPleated`**, H 0.62) | P1 | Ø 0.40 × 0.68 | 1,600 / 500 | LampShade, Brass, Ceramic | — | none | Tall 0; spike / top |
| `Kit_Urn` | P1 | Ø 0.28 × 0.38 | 600 / 250 | Ceramic | — | none | Small 0 |
| `Kit_DoorwayStuds` | P1 | 1.2 × 0.14 × 2.4 module | 800 / 300 | Studs, TapeBlue, Atlas | grade stamp | per stud | — (arch) |
| `Kit_ShoeHalf`, `Kit_ClubChair_Sunk30`, `Kit_Sofa3_WallHalf` | P2 | — | 400; = parent | as parent | — | none / parent | Embedded only (capped cut faces) |

**Budgets.**

| Scope | Budget | Notes |
|---|---|---|
| Office room 12 × 12 m, LOD0 | ~~≤ 150k tris~~ **≤ 60k tris, ≤ 120 renderers, ≤ 40 colliders, Dress ≤ 3 ms** [critic: spec §8 is binding] | The old figure assumed 8 stations × 15k. At the spec cap, even this document's own budgets (about 15k per station) allow only 3 stations plus wall units |
| Pile, LOD0 | ~~≤ 80k~~ **≤ 60k tris** [critic] | A pile room is a dressed room under the same cap. 06 had proposed 200k |
| Pile, SRP batches added | ≤ 60 | — |
| Pile build time | ≤ 5 ms (**[critic]** spec caps room dressing at 3 ms; use ≤ 3 ms) | 06 targets, unverified until profiled on Red's Mac |

**[critic] Live kit against this table** (sidecars in `scratchpad/proj/Assets/Resources/Props/Models`, about 15:35; LOD0 only, no LOD1 exported yet). Dimensions are W × D × H in metres.

| Asset | Budget LOD0 | Live tris | Live dims | Live slots | Live colliders |
|---|---|---|---|---|---|
| OfficeDesk | 2,200 | 6,870 | 1.52 × 0.76 × 0.74 | 7 | 1 |
| CubiclePanel (and Short) | 600 / 450 | 3,892 each | 1.52 × 0.07 × 1.57 | 4 | 1 |
| CRTMonitor | ≈ 3,000 | 3,032 | 0.37 × 0.52 × 0.41 | 4 | 1 |
| PCDesktop | 900 | 8,460 | 0.42 × 0.49 × 0.12 | 8 | 1 |
| TaskChair | 4,500 | 11,684 | 0.62 × 0.65 × 0.95 | 6 | 4 |
| WaterCooler | 2,500 | 9,708 | 0.41 × 0.38 × 1.37 | 10 | 2 |
| Copier | 2,500 | 6,020 | 0.63 × 0.69 × 1.14 | 10 | 2 |
| FilingCabinet | 1,400 | 4,890 | 0.38 × 0.66 × 1.32 | 6 | 1 |
| PaperStack | 200 | 1,754 | 0.35 × 0.37 × 0.10 | 5 | 1 (spec: desk-top items get none) |
| TrashBin | 400 | 2,428 | 0.28 × 0.20 × 0.30 | 2 | 1 |
| Dresser70s (Chest5) | 1,500 | 7,518 | 0.90 × 0.45 × 1.10 | 6 | 2 |
| SideTableTurned | 2,200 | 8,968 | 0.62 × 0.40 × 0.64 | 4 | 2 |
| RollingCabinet | 900 | 5,394 | 0.45 × 0.43 × 0.62 | 8 | 2 |
| TableLampPleated | 1,600 | 3,670 | 0.38 × 0.43 × 0.62 | 4 | 2 (budget: none) |
| Torchiere | 500 | 6,514 | 0.37 × 0.51 × 1.85 | 6 | 3 (budget: none) |
| Crate | 600 | 4,212 | 0.90 × 0.60 × 0.70 (budget 1.00 × 0.80 × 0.75) | 5 | 2 |
| Pallet | 900 | 2,100 | 1.21 × 1.01 × 0.15 | 2 | 1 |

**Reading.** Except for the CRT, the tri budgets in §5.3 are 2–13× under what is being built. Either:
- the budgets were unrealistic for "no raw edge at 2 m", and LOD1 plus fewer stations must carry the 60k cap; or
- the kit needs a decimation pass. Bevel segments 2 → 1 on hidden edges would help, and so would dropping per-key and per-caster geometry.

This is Red's or the kit session's call (Critic notes C3).

### 5.4 Quality gate (per asset, before it enters the generators)

1. **kitlib preview**: Cycles `_a` and `_b` stills.
2. **In-engine lineup shot**, as `kl_lineup` / `kl_crt` do today, at **2 m and 4 m**, under the Office grade.
3. **Pass criteria:**
   - Silhouette and era readable at 4 m.
   - Every material family distinguishable under flat top-light.
   - No raw edges at 2 m; no shading artefacts.
   - Dimensions within ±3% of §1.
   - Albedo within the §5.2 targets (sample in-engine).
4. Upholstery (sofa, club chair, pouf) additionally: cushions read soft at 3 m, not as mattress blocks. **Fail → the §2.3-F fallback.**
5. A pile is accepted only after its §3.5 captures, judged against Stills A and B.

### 5.5 Build order

1. **Day 1, P0 office:** desk, panels and post, task chair, keyboard and mouse, PC, filing cabinets, cooler, copier, vending machine, window. Then Office lens and grade (§6). Capture against the target.
2. **Day 2, P0 tower:** ladder-back (hero), sofa (3 variants), club chair (2), CRT TV, torchiere, display cabinet, bookcase, ply cabinet, crate, pallet, step stool, pouf. Then Hunter footprint integration (R1). Capture the tower in Level 0 and the Office grade.
3. **Day 3, P1:** chest, nightstand, pedestal desk, credenza, dresser, hutch, bergère (the download), side table, bar stool, rolling cabinet, pleated lamp, urn, hat stand, stud doorway. Then the Sprawl mode. Capture the sprawl.
4. **Later, P2/P3:** Embedded cut meshes, chair drift, the oversized throne, the lamp-lit island, the decal feature, a GRD test.

**[critic] Status at about 15:40.** The kit session had already built most of Day 1 in the private copy: desk, panels, task chair, PC, filing cabinet, cooler, copier, paper and bin. It also built parts of Day 2 and Day 3: pallet, crate, torchiere, dresser, side table, rolling cabinet and pleated lamp.
- **Not built yet:** Keyboard, Mouse, DeskPhone, Binders, VendingMachine, InteriorWindow, PanelPost, and the whole upholstery and seat family (ladder-back, sofa, club chair, bergère).
- **Next.** The priority now is the §5.4 gate, LOD1 and the budget reconciliation (C3), before more modelling. The ladder-back stays the top pile priority.

---

## 6. Lighting and grade for the Office

### 6.1 Fixture

**Replace `Office_Louver` with `Office_LensOpal`.**
- Generate it with a new `lens(style="opal")` in `gen_surfaces.py`:
  - albedo #EEEDE8;
  - emission flat, with a **6–8% falloff into a 20 mm frame band**;
  - no prisms, no cells.
- Dead or off state: albedo #D9D6CC with two faint 25 mm grey tube shadows through the opal.
- Housing: the existing painted-steel pan; flange 20 mm white, flush with the T-bar.
- Size 0.61 × 1.22, **long axis along the room's long axis**, matching the target's central run.
  - **[critic]** The map owns fixture placement. Today the lens is 1.2 (X) × 0.6 (Z) at each cell centre. The agreed P0b direction is 0.6 (X) × 1.2 (Z) filling whole tiles, so the long axis is world Z in every room, not per room (spec §4).
  - Per-room orientation would need the map chat's agreement.
- Applies to `FrontRoomsMapWorld.BuildMaterials` (`officeLens`) and `FrontRoomsRoomStream` (`room.rule == Office`).
  - **[critic]** `officeLens` now resolves to `Troffer_Lens` (15:24), which is still the prismatic, tube-striped `lens()`. So adding `Office_LensOpal` means a new material plus repointing `FrontRoomsSurfaces.OfficeLens`. `BuildMaterials` stays as it is.

Rationale:
- The film's custom troffers have flat opal lenses with no visible tubes (02 F13).
- Cox moved the tubes so they would not read through the diffuser (01 S12).
- The target shows flat frosted panels (03 Q7).

### 6.2 Grid and lit pattern

- One fixture per 3 m cell, centred: about 9 m² per fixture, close to the real 8'×10' (7.4 m², about 38 fc, BPA).
- Skip cells under a bulkhead.
- **Lit fraction:**
  - Spine fixtures **never dead**: the "lit runway" that keeps the chase readable.
  - Halls: 40% of the remaining fixtures lit.
  - Workrooms: 70%.
  - Small offices: 100%. Canon: big rooms dark, small rooms lit (03 L1).
- Office dead/failing odds: 3% / 6% today → **25% dead (off the spine), 6% failing**, plus 1 flicker per ~3 rooms.
- Dead fixtures concentrate over pods and corners, so islands sit in falloff (target, 03 L5).
- The fixture nearest a pile centre is forced alive (§3.4.10).

### 6.3 Colour temperature and light values

- Tubes are 4000 K, film-accurate (01 S10).
- Set the Office lamp colour to **#FFF1E0**, not #FFE1B1. That is 4000 K as seen by a camera balanced near 4300 K: very slightly warm.
  - **[critic]** This value is a design derivation, not sourced. The map's current lamp colour is (1, .96, .88), about #FFF5E0 (spec §4), which is already close.
- Keep `lampIntensity` 5.5 and range about 6.8 m. **[critic] Corrected:** the map's range is **10 m** (12 m in Tall), per `FrontRoomsMapWorld` line 713 and spec §4. The 6.8 m figure came from the stale title-stream `LIGHTING_SPEC.md`. Re-check exposure after the grade (§6.4) so that:

  | Surface | Target sRGB (measured in the target, §6.9) |
  |---|---|
  | Lit lens | clips at ≈ #EEEADA |
  | Ceiling next to a lens | ≈ #B3B19F |
  | Carpet under a fixture | ≈ #585B55 |
  | Walls | ≈ #3C392C |
  | Corners | ≈ #2A271C |

- The CRT `_On`, the vending interior and exit signs are the only colour accents (03 L6). Do not tint the troffers green; the green-grey is a grade.

### 6.4 Office grade (new `Resources/Rendering/FrontRoomsPost_Office.asset`)

**Mechanism.** A local volume:
- priority 1;
- weight blended 0 → 1 over 1.5 s by `FrontRoomsMapWorld` when the player's zone theme is Office.

The Office volume is not additive: it overrides each parameter it enables. So these are **absolute** values. The global Level 0 profile stays as it is (WB +9 / −7, contrast −6, saturation −8, grain 0.22, vignette 0.26, CA 0.06, distortion −0.04).

| Override | Office value | Why |
|---|---|---|
| White Balance | temperature **+1**, tint **−14** | Cooler than Level 0, pushed green: the target's olive-green-grey (hue 45–70°, measured) |
| Color Adjustments | post-exposure −0.15; contrast +4; saturation **−22**; colour filter #F2F5EE | Low saturation 0.08–0.2 measured; deeper corners than Level 0 |
| Shadows / Midtones / Highlights | shadows (0.97, 1.01, 1.00, −0.03); midtones neutral; highlights (1.02, 1.00, 0.97, 0) | Teal-green shadows, warm lens highlights |
| Lift Gamma Gain | lift (1.00, 1.02, 1.00, +0.015) | Small lift only: the target's shadows are deep (#212019 under desks) |
| Bloom | threshold 1.1; intensity 0.25; scatter 0.55; tint #FFF3E0 | Soft lens glow. No strong halation: not a film fact (01) |
| Film grain | Medium3, 0.18 | Subtle, a stylistic choice |
| Vignette | 0.22 | — |
| Chromatic aberration | 0.03 | The film avoided anything glossy or cinematic (01 S12) |
| Lens distortion | −0.03 | — |

### 6.5 Haze

URP fog is global `RenderSettings`. Lerp fog colour and density by the player's zone over 1.5 s, in the same driver as §6.4.

| Zone | Mode | Colour | Density |
|---|---|---|---|
| Office | Exponential squared | **#3B3F35** (from the target's far-corridor haze, #4C4B3C, after the grade) | **0.018** (≈ 40% fog at 40 m) |
| Level 0 | Exponential squared | #1B1A17 | 0.024 |

The 3rd–4th room down an axis should fall off, not black out (03 L4).

### 6.6 Practicals

- **CRT `_On`**: emission #5E7380 × 0.6 on 1 in 6 monitors; no real light.
- **Vending interior**: warm emission 3000 K plus **one** unshadowed point light (intensity 0.6, range 2 m) per machine.
- Exit signs: as the existing system.
- Lamp-lit island (A8, later): 1 shadowed and 2 unshadowed point lights at 2700–3000 K, with the troffers off.

### 6.7 Shadows, AO and decals

- **SSAO.** Keep Depth Normals, radius 0.45, intensity 1.6. Raise **Direct Lighting Strength 0.35 → 0.45** in the Office profile, so desk frames and pods ground under lit pools.
- **Shadows.** 1–2 shadow-casting fixture lights per room. Small props: `ShadowCastingMode.Off`.
- **Decals.**
  - Add the **URP Decal renderer feature** with the **Screen Space** technique: DBuffer does not support OpenGL ES/WebGL (06).
  - Until then, bake stains and ghosts into masks, and use a blob quad under piles.
  - URP decals don't work on transparent surfaces, so glass smudges go into the glass material's roughness.

### 6.8 Camera

- **72° vertical FOV** in both camera paths (≈ 14 mm full-frame at 16:9; the film used 18 mm or wider inside, 01 S11).
- No depth of field.
- Eye height 1.6 m.

### 6.9 Measured target values (sRGB averages from `ref_office_target.png`, 1672 × 941)

| Region | Value | Hue / L / S |
|---|---|---|
| Lens (near) | #EEEADA | clipped warm white |
| Ceiling beside the lit lens | #B3B19F | 54° / 0.66 |
| Ceiling far corner | #2A271C | 47° / 0.14 |
| Back wall (lit) | #3C392C | 49° / 0.20 |
| Column | #433F2E | 49° / 0.22 |
| Carpet, foreground | #595E5A | ≈135° / 0.36 / 0.03 (neutral blue-grey-green) |
| Carpet, mid | #585B55 | — |
| Cubicle fabric face | #2E2F28 | 69° / 0.17 / 0.08 |
| Shadow under desk | #212019 | — |
| Far corridor haze | #4C4B3C | 57° / 0.27 |
| Ceiling stain | #626053 | 52° / 0.35 |

The reading: **low key**. Floor and lenses carry the light; walls and fabric sit at L 0.15–0.25, all in a desaturated olive. The current `2_Office_forward.png` is too yellow-brown on the ceiling, too flat on the props, and uses an egg-crate lens.

---

## 7. Risks and open questions for Red

### Risks (with mitigations)

**R1 — The Hunter's paths run through furniture.** **[critic] Restated.**
- The original claim was that `FrontRoomsMapHunter` ignores colliders (06, line 293). That was true of the file 06 read. As of 15:31 the Hunter capsule-casts, slides along props, sidesteps after 0.5 s and ghosts through furniture after 1.4 s (spec §7).
- The remaining risk: BFS still plans through pod and pile cells, so chases show the Hunter snagging on or ghosting through a pile.
- Office pods and piles both cover cell centres.
- Fix before shipping furniture in the map:
  - `Dress` and `Build` return footprints;
  - `Furnish` marks cells;
  - the validator re-checks connectivity.
- **This touches the map session's files: coordinate with that owner.**

**R2 — Revisits re-roll the whole room.**
- `roomSeed` hashes `data.revision`, so a re-built chunk re-rolls everything instead of "one thing changed".
- Split the seed: layout without revision, anomaly with revision.
- This depends on Red's open decision about returning to a dropped chunk.

**R3 — Procedural upholstery may read as blocks.**
- Mitigated by the `cushion()` helper and the §5.4 gate, with CC-BY fallbacks F2–F4.
- A fallback sofa needs a Cycles bake of the floral fabric into its UVs: about half a day.

**R4 — Shader change risk.**
- Adding `_SheenColor`, `_SheenPower` and `_MacroStrength` to `FrontRooms/Surface` touches every surface material.
- Keep the defaults neutral (0 / 1).
- Verify that the SRP Batcher is still compatible: the properties go in the UnityPerMaterial CBUFFER.

**R5 — WebGL.**
- No static batching, no GRD, and the Screen Space decal technique only.
- A 25-piece pile is about 25–60 draws on WebGL.
- Profile the pile room on WebGL; if needed, reduce pieces on WebGL by 30%.

**R6 — Performance numbers are proposals.**
- 150k tris per office room, 80k per pile, ≤ 5 ms pile build.
- Profile on Red's Mac before locking them.

**R7 — Parallel ownership.**
- `kitlib.py`, `FrontRoomsOfficeKit.cs` and `FrontRoomsFurniturePile.cs` belong to the parallel kit session. Map files belong to the map session.
- This doc's changes should be handed to those sessions, not written over their in-progress edits.
- Check Codex and session activity first (project memory rule).

**R8 — Double columns.**
- `Dress` adds columns on its own 6 m grid. The map already places `data.pillar` at cell corners.
- Fix: columns only at corners, and skip existing pillars (§4.3).

**R9 — Copy-pastes stop looking identical.**
- World-space macro wear makes them drift apart.
- Use `_MacroStrength` ≤ 0.3 on props.

**R10 — Kit slot previews mislead.**
- Painted-steel slots preview as metallic 0.6. The Unity materials must be metallic 0.

**R11 — Brand and IP exposure.**
- Vending snack art, labels, stencils and the copier panel must be invented.
- No film stills, wiki images or wiki text in the project or build.
- The 2002 photo is all rights reserved.

**R12 — Unverified source claims.**
Do not state these as fact in the deck:
- how the film's piles were physically secured (Blu-ray extras, 01);
- the "two chairs melded" proof chair and the five-legged stool;
- the TT02 sunk-armchair reading;
- the F17 trailer timestamp;
- 180 versus 350 troffers.

**R13 — This document disagrees with LEVEL_MODULE_SPEC [critic].**
- Room sizes and heights, column size and count, window size and collider, wall-unit offset, station and pod sizes, the ceiling-clearance cap and the per-room budgets all disagree in places.
- The spec is the agreed contract, so changing any of those numbers needs both chats (spec §10). Details are in Critic notes C1.

**R14 — The live kit is over budget [critic].**
- The live meshes run at 2–13× this document's LOD0 budgets (the CRT is the exception) and up to 10 slots each.
- One live station costs about 34–42k tris against a 60k room cap.
- No LOD1 is exported yet, so the target's 6–8 visible stations cannot be dressed at the current cost (C3).

### Questions for Red

**Q1 — Approve the download list?**
- §2.3 A–D: 37 CC0 items, about 270 MB, no attribution required.
- Separately: E (optional A/B and variety).
- F (CC-BY fallbacks) only if a gate fails.

**Q2 — The bergère chair.**
- Use Poly Haven `GreenChair_01` (carved, gothic-leaning, CC0)?
- Or accept the CC-BY wingback (F1)?
- Or a simpler modelled armchair with turned legs, which loses the cabriole?

**Q3 — Level 0 lens.**
- Keep the prismatic K12 lens (2002-photo signature, Kane's tile survey)?
- Or switch to the film's flat opal too? (Office is decided: opal.)

**Q4 — A separate Office grade?**
- Cool green-grey through a local volume plus a fog lerp, versus one global look for every zone.
- The target needs the separate grade.

**Q5 — FOV.**
- 76° → 72° vertical in the main game camera. This changes the chase feel slightly; confirm.

**Q6 — Piles in Office zones?**
- Proposed: 15% of Office halls.
- Note: the film never shows office cubicles or piles together; that pairing is FrontRooms' own.

**Q7 — Revisit change.**
- Should a re-entered room keep its layout and swap one prop (the film-like "remembers it less" beat)?
- This needs the R2 seed split.

**Q8 — Piles as gameplay.**
- OK to put hide hollows in ≤ 30% of towers?
- OK to put the zone key on A5 lone chairs as bait?
- Should piles ever block a door fully? Proposed: never. A 0.8 m path always remains.

**Q9 — Priority.**
- Is the target office frame first (Day 1), or the Still B tower first?
- The build order in §5.5 assumes the office first.

**Q10 — Corridor chair drift.**
- Wanted in Office corridors too, using task chairs? Or only ladder-backs in Level 0?

**Q11 — Columns [critic].**
- The target shows big columns (about 0.9–1.2 m, at least 4 in view) flanking the spine. Red earlier rejected pillar-heavy spaces, and the spec allows 0.61 m and at most 4 in a 12 m room.
- Which wins for the Office: the target's look or the "maze of walls" rule?

**Q12 — The figure at the corridor's end [critic].**
- The target has a dark figure-like shape about 25 m down the doorway axis. Is that intended (a Relay or entity tease), or noise?

**Q13 — Downloaded models: re-slot or keep [critic].**
- `ingest_cc0.py` keeps Poly Haven textures and UVs. This document re-slots them onto `Prop_*`.
- Pick one rule before the first download.

---

## Critic notes (completeness pass, 2026-10-02 about 15:45)

### C0. What was checked

**Reports.** All six reports and this document were read in full. The exception is 04's raw API appendices, which were spot-read.

**Target image.** `ref_office_target.png` was re-viewed in full and in five brightened crops: left foreground, left middle, centre doorway, right middle and right far.
- Colours were re-sampled from a BMP conversion. Lens #EEEADA, carpet #595E5A, haze #4C4C3F and fabric #2D2D27 reproduce §6.9.

**Project code and docs**, re-read at about 15:40:
- `FrontRoomsOfficeKit.cs`, `FrontRoomsFurniturePile.cs`;
- `FrontRoomsMapWorld.Furnish` and `BuildMaterials`;
- `FrontRoomsMapHunter.MoveDirect`, `Slide` and `Cast`;
- `FrontRoomsSurfaces.cs`, `kitlib.SLOTS`, `ingest_cc0.py`;
- the 18 kit sidecars in the private copy;
- `Documentation/LEVEL_MODULE_SPEC.md`, `LIGHTING_SPEC.md` and `VISUAL_RESEARCH_LOOKDEV.md`;
- the post profile in `FrontRoomsRenderSetup.cs` (WB +9 / −7, contrast −6, saturation −8 confirmed);
- the camera FOVs (76° and 72° confirmed).

**URLs spot-checked with WebFetch.** 11 assets on 10 URLs (ambientCG's API returned three in one call). All exist, and every claim checked matched.

| # | URL | Result |
|---|---|---|
| 1 | api.polyhaven.com/info/GreenChair_01 | 4,213 tris, Kirill Sannikov. **Height 1,059 mm**, not the doc's 0.98 (fixed in §2.2). Tagged "gothic" |
| 2 | api.polyhaven.com/info/floral_jacquard | 252.95 × 383.6 mm; published 2025-09-05 |
| 3 | ambientcg.com/a/Plastic013B | CC0; 1K-JPG 6 MB |
| 4 | ambientCG API `Wood096`, `SurfaceImperfections007`, `Tape005` | Sizes match §2.3; Wood096 released 2026-09-30, 50 × 50 cm |
| 5 | texturecan.com/details/66 | Title and 1K/2K/4K/SBSAR confirmed; the licence text was not in the fetch (05 verified the terms page) |
| 6 | cgbookcase.com/textures/liquid-stains-01 | Exists, 1K–4K; CC0 shown only in alt text |
| 7 | api.sketchfab.com/v3/models/49e21ea4… (F1) | CC Attribution, downloadable, 2,478 faces, "velvet armchair with wooden legs" |
| 8 | surfacemag.com …/a24-backrooms-production-design/ | "Thirty-nine of the same chair", towers as landmarks; all five image filenames cited by 02 present |
| 9 | theasc.com/article/backrooms-cinematography-cox/ | 180 fixtures × 2 Titan tubes (360) + 50 Helios, 4000 K, camera 4300 K, Venice 2, Supreme Primes; no grain or halation mentioned |
| 10 | sony-cinematography.com …/venice-2… | 18 mm or wider inside, 25/28 mm and up outside, the 14 mm remark, an open office set with random furniture |

**Copyright.** No film still is in the scratchpad or the project; only Red's target and our own renders are there. Source quotes in this document are fragments under 15 words. Where one source is quoted twice, it is the same phrase ("a 14mm looks normal"; Elle's "ceiling-sweeping").

### C1. Disagreements with LEVEL_MODULE_SPEC (the spec is binding until both chats agree)

| Topic | This document | Spec / live code | Action |
|---|---|---|---|
| Office room sizes | Open hall > 4×4; 2.4 m and 5.4 m Office zones | 2–4 cells a side; Standard 2.9 m only | Rules marked moot (§4) |
| Columns | 0.9 m on a 6 m bay; 4–9 in big rooms | 0.61 m; ≤ 1 per 9 m room, ≤ 4 per 12 m room; Red: "maze of walls" | Q11 |
| Interior window | 2.40 × 1.05, sill 1.00, glass collider | 2.44 × 1.22, sill 0.90, **no collider** | §1a T15, §4.4, §5.3 corrected |
| Wall-unit offset | 0.05–0.08 m from the wall | `depth/2 + 0.03` from the face; 0.5 m service zone | §4.4 corrected |
| Station / pod | 1.80 × 1.70; R2×N 1.8N × 3.5 | 1.524 × 1.70; 2×2 pod 3.10 × 3.45 | §4.5 corrected |
| Pedestal, chair, cooler, copier, vending | see §1a | spec catalogue (§6) | Spec values added per row |
| Ceiling cap | CeilingStuck pierces ≤ 0.12 m | Props stay 0.05 m under; pile under `min(0.95H, H − 0.06)` | Needs agreement (decision 10) |
| Pile placement shift | 0.2 × W | Ring of R + 0.6 must stay clear | Clamp (decision 6) |
| Room budget | 150k tris per room; pile 80k | ≤ 60k tris, ≤ 120 renderers, ≤ 40 colliders, ≤ 3 ms | §5.3 corrected |
| Carpet / grid / rebase | 256/420 m tile, 256 m rebase | 0.6 m tile, 0.6 × 0.6 grid, 240 m rebase (P0b) | §4.0 marked superseded |
| Lens orientation | Along the room's long axis | World Z in every cell (P0b) | §6.1 marked |
| Lamp range | 6.8 m | 10 m (12 m Tall) | §6.3 corrected |
| keepClear expansion | 0.35 m | 0.25 m in the code | §4.2 corrected |

### C2. The brief, item by item

| Brief item | Where | Verdict |
|---|---|---|
| Research the Backrooms IP **first** | 03; now summarised with sources in §0.3 | Covered. The Kane Pixels Fandom wiki was unreachable, so Async interior details are thin (03 Q1) |
| Research the Backrooms **film** | 01, 02; §0.3 | Covered from press, BTS and the trailer/teaser. The film itself and the Blu-ray extras were not viewed. How the piles were built and which shots are VFX remain unknown |
| Decompose / analyse the furniture | §1a (target, now with T22–T24), §1b, §1c (now B17–B19) | Covered. The film stills were checked against 02's viewing, **not re-viewed by the critic** (they are not on disk) |
| Can ready-made assets be downloaded and dropped in? | §2, from 04 and 05 | Covered: 37 CC0 items with verified pages and licences, 4 CC-BY fallbacks. The CC-BY fallback silhouettes were never viewed (04: thumbnails not viewed) |
| Collect shots of distorted / copy-paste furniture | §3.0 (added), from 02 | Covered: 30 distinct real frames, 13 of distorted, repeated or embedded furniture, all with source pages. Gaps: buried-couch shots, the second teaser, promo and clip |
| How to land them in the game | §3.1–3.5 | Covered as archetypes and rules. Several rows are unreachable under the current room carving (decision 9, §3.2) |
| Redo models, textures and materials at URP cinematic level | §5, §6 | The spec is concrete enough to model from. It is now contradicted by the live kit's budgets (C3) |

### C3. Live kit against the budgets (the largest open problem)

- 18 kit meshes plus a test probe are built. Every one except the CRT is 2–13× over its LOD0 budget, and 11 exceed the ≤ 4-slot rule.
- No LOD1 is exported. kitlib has no LOD, `cushion()`, `variants` or `WeightedNormal` code yet; those are proposals in §2.1, §5.1 and decision 8.
- **Arithmetic.** One live station costs about 34–42k tris. The target composition (6–8 stations plus appliances in a 12 m room) needs about 250–300k at LOD0, against a 60k cap.
- **Options (Red or the kit session decides):**
  1. Decimate the kit to roughly this document's budgets.
  2. Export LOD1 and cap stations per room at 3–4.
  3. Ask the map chat to raise the cap for Office rooms after profiling.

### C4. Claims found unsupported or wrong, and how each is now marked

1. **T12, PC case under the monitor.** Not in the target; the CRTs sit on their own feet.
2. **T18, grey side door.** Not in the target. The map owns doors anyway.
3. **T15, window "blacked out, near-black".** The target shows a dim lit room beyond. A fake interior is needed, and it is unspecified.
4. **T16, "5 trays × 4–6 coils".** The target shows 4 × 4.
5. **§2.2, PH `wall_clock` "modern".** 04 rates it "use" (office and 90s tags). Added to E5.
6. **§2.2, `bar_chair_round_01` "beading, wrong form".** 04 rates it "best match". Added to E6.
7. **Decision 7 and R1, "the Hunter walks through anything".** Stale since 15:31.
8. **§6.3, range 6.8 m.** That is the stale stream spec; the map uses 10 m.
9. **Project-state counts.** "338 lines", "16 Kit names" and "0.35 m" were stale. Asset names `Kit_Chest5` and `Kit_LampPleated` differ from the live `Kit_Dresser70s` and `Kit_TableLampPleated`.
10. **Uncited type labels and sizes.** Brand-type labels (Steelcase/Haworth, National Vendors/AP), "300 W", "101-key", the CRT size and most §1 dimensions are designer estimates. They are now labelled as such.
11. **#FFF1E0.** A derivation, not a source.
12. **"Office halls 15%" and the Low-zone pile rows.** Unreachable with current carving.
13. **"First pile of a run".** Undefined in a coordinate-seeded map.
14. **Bergère pick.** Overrides 04's recommendation; now stated.
15. **Download C6 (CardboardSet001).** It had no consumer until B18 was added.

### C5. Still missing after this pass

1. **Eyes on Red's Still A and Still B.** They are not on disk. Have Red drop them in the scratchpad, or re-view the Dezeen col_10 and Fast Company `TB_Scans_00108` in a browser, viewing only. Confirm B13's CRT colour (black or beige, an internal conflict in 02) and B17–B19.
2. **Film coverage gaps.** Not checked: the second teaser `BjRndcTYqJo`, promo `2z6a6NUFlsU`, clip `Pb8KqfkLe24`, the IMDb, Letterboxd, ShotDeck and FilmGrab galleries, and the Blu-ray extras ("Building the Backrooms", the prop walkthrough). No frame was found of furniture buried in walls. How the piles were fixed and which shots were VFX-distorted remain unknown.
3. **Visual check of every download before approval.** No one has looked at the GreenChair_01 silhouette (bergère gate), the F1–F4 Sketchfab thumbnails, or the TextureCan carpet in a browser.
4. **Spec reconciliation (C1).** The column size and count (Q11), ceiling piercing, window, budgets and per-asset dimensions need a joint decision between the map chat and the kit session.
5. **Budget plan (C3).** Per-asset LOD0 and LOD1 targets that sum to ≤ 60k per room, and a station cap. LOD export in kitlib.
6. **Map-side hooks (map chat).**
   - A per-cell Hunter block flag fed by footprints returned from `Dress` and `Build`.
   - A 6-argument `Build` that passes keepClear and walls.
   - A corridor-dressing hook for chair drift.
   - A spatial definition of "first pile".
7. **Unspecified pieces.**
   - The interior window's fake back room (interior mapping or a back box).
   - T22, the leaning object, still unidentified.
   - T24, the figure at the corridor's end (Q12).
   - A mouse pad or notepad desk prop.
   - Soffit-mounted fixtures at the frame edges.
8. **Pipeline decision Q13** (re-slot or keep Poly Haven materials) before any download. Extend `ingest_cc0.py`; do not write a second importer.
9. **Not yet implemented, and not verified to work:**
   - the shader additions (`_SheenColor`, `_SheenPower`, `_MacroStrength`);
   - the URP Decal feature;
   - the Office post volume and fog lerp;
   - the opal lens.

   §6 values are proposals until captured against the target.
10. **Escalation.** The DP08 tiers (§3.3) are an unconfirmed proposal in project memory.
