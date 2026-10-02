# Office level and furniture piles: research and how it lands

Research and decisions on 2026-10-02 (visual chat). This replaces the earlier
Codex version of this file. The full reports, with every source, are in
[`research/office_and_film/`](research/office_and_film/):

| Report | What it covers |
|---|---|
| [01 film production](research/office_and_film/01_film_production.md) | How A24's *Backrooms* (2026) sourced, built and lit its furniture; 32 sources |
| [02 film shots](research/office_and_film/02_film_shots.md) | 34 shots, including Red's two stills and timestamped trailer frames, clustered into 8 tableau archetypes with game recipes |
| [03 IP canon](research/office_and_film/03_ip_canon.md) | Kane Pixels' series, the wiki's office levels, the 2002 photo, Backrooms games, licensing |
| [04 model sourcing](research/office_and_film/04_model_sourcing.md) | Downloadable models for 31 furniture types, each license checked against the source page |
| [05 texture sourcing](research/office_and_film/05_texture_sourcing.md) | CC0 materials for every furniture surface; what to download vs generate |
| [06 distortion techniques](research/office_and_film/06_distortion_tech.md) | Why Codex's "memory bleed" failed and the design of the pile generator |
| [10 synthesis](research/office_and_film/10_synthesis.md) | The decision document: decomposition, make-vs-download, shot→game plan, layout rules, per-asset spec, lighting and grade, plus critic notes |

## What the research established

- **The film's "copy-paste" furniture is real duplication.** The set decorator
  bought 20 identical sofas and 40+ identical oak slat-back chairs from a hotel
  liquidator. Nothing post-dates the early 1990s. The piles are built around
  many copies of one object, pieces are intact, and they escalate from
  "merely drab" to ceiling-sweeping towers. The idea came from video-game
  clipping. Some pieces were 3D-scanned so VFX could distort them.
- **The film's offices are emptied offices.** They have dividers that go
  nowhere and full-length cabinets. There are no cubicle farms or desk CRTs, so
  Red's target office is FrontRooms' own design. The film's vocabulary becomes
  the anomaly layer.
- **Lighting is practical troffers with flat opal lenses at 4000 K.** The
  lenses are not prismatic or louvred: the Office already uses opal, and Level
  0 is open (question 3). Lenses are 18 mm or wider. The film was shot
  digitally (Venice 2), so grain is a stylistic choice, not a fact about the
  film.
- **Kane Pixels' canon distorts furniture in four ways:** stretching, sinking
  into walls and floors, repeating, and mounding. The founding 2002 photo has no
  furniture at all, and was taken on a Sony Cyber-shot, not a Nikon.
- **Licensing.** We use the concepts only. Wiki text and images are CC BY-SA,
  and the film and Kane's series are all rights reserved, so no stills or wiki
  text are in the project.

## Decisions (Red approved 2026-10-02)

1. **One consistent kit.** Every office and pile piece is modelled by our own
   Blender scripts (`Tools/Blender/frontrooms_kit`) and textured with CC0
   scans. One model was downloaded: Poly Haven *Green Chair 01*, re-slotted onto
   the kit's velvet and walnut as `Kit_BergereChair` (Still A's pink chair).
2. **Downloads.** Red approved 37 CC0 items. 35 were fetched (256 MB, MD5
   checked) into `Tools/lookdev/cc0_src`, which is git-ignored, and logged in
   `cc0_src/SOURCES.txt`. The two cgbookcase sets are hotlink-protected, so they
   were skipped. ambientCG masks cover the same uses. Fetcher:
   `Tools/lookdev/fetch_cc0.py`; packer: `Tools/lookdev/import_cc0_textures.py`.
3. **Columns.** Red: pillars are allowed, but their modular size and placement
   are planned and audited by the level-design chat. That chat's rule v1: a 6 m
   structural lattice, 0.9 m drywall columns plus bulkheads in the Office, and
   0.6 m wallpapered columns in Level 0. The map places them and passes them to
   `Dress` as `obstacles`.
4. **Piles are deterministic analytic solves, not physics.** They use intact
   pieces, rest states quantised to upright, side, back, exact 180° or a 30–52°
   edge-lean, exact copy-paste duplicates, and centred landmarks up to 0.95 × the
   ceiling.
5. **Office look.** Flat frosted lens, 4000 K lamps, and a local Office grade
   volume: cooler, greener and less saturated. Level 0 keeps its warm grade.

## Where it lives in the project

| Piece | File |
|---|---|
| Office layout (pods, wall rows, wall units, keepClear connectivity) | `Assets/Scripts/Office/FrontRoomsOfficeKit.cs` |
| Furniture piles | `Assets/Scripts/Office/FrontRoomsFurniturePile.cs` |
| Kit loader (FBX + sidecar, slot materials, colliders, LOD, shadows) | `Assets/Scripts/Office/FrontRoomsKitLibrary.cs` |
| Import settings, LODGroup heights | `Assets/Editor/Rendering/FrontRoomsKitImporter.cs` |
| Look-dev (office room, pile hall, line-up, per-asset close-ups) | `Assets/Editor/Rendering/FrontRoomsKitLookdev.cs` → `Verification/kit_lookdev` |
| Office zone grade | `FrontRoomsPostStack.EnsureZoneVolume(parent, "Office", bounds)` + `Resources/Rendering/FrontRoomsPost_Office.asset` |
| Prop materials (scanned) | `Resources/Surfaces/Prop_*.mat`, made by `FrontRoomsRenderSetup` |
| Asset sources | `Tools/Blender/frontrooms_kit/assets/*.py` (one module per asset), `ingest_cc0.py` for the downloaded chair |

The unit sizes and the map contract (`Dress` and `Build` signatures,
keepClear, budgets) are in `LEVEL_MODULE_SPEC.md`, which the level-design chat
owns.

## Open questions for Red

From synthesis §7. The ones that remain open:

- **Level 0 lens.** Should Level 0 also switch to the film's flat opal lens?
  The film's behind-the-scenes photos show opal. Level 0 is prismatic today.
- **Camera field of view.** Should it be 72° vertical (about 14 mm, matching
  the film's lens) instead of 76°? The map chat owns the camera.
- **Piles in Office halls.** Should 15% of Office halls get a pile? The film
  never shows cubicles and piles together.
- **Revisits.** When the player re-enters a room, should it keep its layout
  with one prop swapped?
