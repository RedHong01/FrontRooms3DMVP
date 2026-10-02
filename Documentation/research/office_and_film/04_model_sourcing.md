# 04 — Ready-made 3D model sourcing for the Office level and film-style furniture piles

Status: COMPLETE (2026-10-02). Report path: scratchpad/research/04_model_sourcing.md
Date of research: 2026-10-02. No asset files were downloaded; every entry is a URL to be approved and downloaded later by Red.

Legend: **verified** = the asset page or the source's official API record was fetched during this run (2026-10-02) and existence + license were confirmed. **UNVERIFIED** = lead only (search result, or from the earlier interrupted run and not re-fetched).
Recommendation: **use** = drop-in candidate (after Unity import check), **maybe** = usable with rework (retexture, decimate, re-UV, scale), **reject** = do not use (license, style, polycount, era).

## 0. Executive summary

- **Ready-made coverage is good for the film-style household piles, weak for the specific 1990s office.** Of 31 asset types, 22 have at least one verified **use** candidate (the desk only as a secondary desk type); 4 are hard gaps and 7 are soft gaps (download exists but needs as much rework as modelling).
- **Best sources:** Poly Haven (CC0, real PBR, 1K–8K, 0.2–30k tris, verified via its public API) for TVs, bar stool, two-tier side table, bookshelves, steel shelves, wall clock, notepads, a tanker-style metal desk and a glass-front cabinet; **Sketchfab CC-BY** for the explicitly 1990s office items (MadeByYeshe "90s Retro Office Pack" + "Retro CRT Computer", fizyman CRT monitor, tboiston water cooler, ahmagh2e filing cabinet, artvolodskikh task chair) and for the household pile (lena-wachs plaid sofa, MaX3Dd club armchair and pallet, 3DCraftsman velvet wingback, ladder-back chairs, Soviet/Victorian glass cabinets, sideboards/hutch).
- **Not useful:** Kenney and Quaternius (CC0 but stylised/untextured → greybox only), ambientCG (no furniture models; use it for materials), OpenGameArt (diffuse-only low-poly), Smithsonian CC0 (18th-century scans, 100k+ faces), Unity Asset Store / itch.io packs found (paid, HDRP-only, PSX or contemporary). TurboSquid, Free3D, Fab and BlenderKit licence pages could not be fetched (403 / odd redirect) → nothing from them is marked verified.
- **Rejected for licence reasons:** a Sketchfab re-upload of a Quixel Megascans cabinet labelled CC-BY, a "Poppy Playtime" snack machine (game-IP derivative), branded Sony/Nortel electronics (trademarks), and any NC/ND/Editorial/Personal-use item.
- **Must be modelled in Blender:** the target beige-laminate/brown-steel desk, cubicle fabric panels, plywood crate with original stencil, halogen torchiere; likely also photocopier, beige PC case, 1970s veneer chest of drawers, small rolling wooden cabinet, pleated lamp shade, vending-machine snack rows. All are low-complexity shapes whose quality depends on materials (texture report 03), which is exactly where the earlier boxy, flat-coloured Codex models failed.
- **Pipeline:** ingest everything through Blender (scale, decimate, ≤2 materials, ARM → URP mask map), 1K/2K textures, shared SRP-Batcher materials with a few colour variants, box colliders; the pile builder reuses ~10–14 meshes with seeded tilt/interpenetration to get the film's "duplicated and pasted" look cheaply. CC-BY credit lines are ready in Section 5.
- **Before downloading:** visually check the rows marked "silhouette/colour UNVERIFIED" (thumbnails were not viewed), and get Red's approval for each download (none were downloaded).

## 1. Licensing notes per source

Summary rule for FrontRooms (student game, possibly published free or paid on itch/Steam): **CC0 and CC-BY 4.0 are safe**; CC-BY needs a credits entry (author, title, link, licence, "modified" note). Royalty-Free store licences (CGTrader, TurboSquid, Unity Asset Store, Fab Standard) are fine **inside a built game** but forbid redistributing raw files — so never commit their source files to a public Git repo. Reject NC, ND, Editorial, "Personal use only", UE-only, and anything re-uploaded from another store or ripped from a game.

### 1.1 Poly Haven (CC0)
- Verified 2026-10-02 at https://polyhaven.com/license : all assets CC0; commercial use allowed; attribution not required. Quote: "You can use our assets for any purpose, including commercial work."
- Metadata for every Poly Haven candidate was read from the official public API (`api.polyhaven.com/info/<id>` and `/files/<id>`), see Appendix A. Downloads offered as Blend / glTF / FBX / USD at 1K–8K with Diffuse, ARM (AO-Rough-Metal), nor_gl, nor_dx maps → maps directly onto URP Lit (pack ARM → URP mask map: R=Metal, G=AO, A=Smoothness=1-Rough; use nor_gl).
- 521 models total; ~85 furniture. Strongest source for the household-pile items (TVs, bar stool, side table, bookshelf, shelves, desk, clock, notepads). Weakness: few 1990s office items (no CRT monitor, copier, vending machine, cubicle, task chair).

### 1.2 Kenney (CC0)
- Verified https://kenney.nl/assets/furniture-kit : CC0, 140 files, low-poly stylised, v1.0 2018. Item list not shown on page (UNVERIFIED which office items it contains).
- Verdict: **blockout only** (flat-colour stylised; violates the "not stylised" rule). Useful for greyboxing pile composition in Blender quickly.

### 1.3 Quaternius (CC0)
- Verified https://quaternius.com/packs/ultimatehomeinterior.html : CC0 ("free to use in personal and commercial projects"), 123 models, FBX/OBJ/Blend, **not textured** (flat colour). Ultimate Furniture Pack (20 models) likewise untextured (prior-run fetch of https://quaternius.com/packs/ultimatefurniture.html, UNVERIFIED this run).
- Verdict: **reject for final art**, blockout only.

### 1.4 ambientCG (CC0)
- Verified https://docs.ambientcg.com/license/ : CC0 1.0; commercial use without permission; attribution appreciated not required.
- 3D-model section contains food, sticks, stumps, "Cardboard Set", "Screw Set" etc. — **no furniture** (prior-run fetch of https://ambientcg.com/list?type=3DModel ; UNVERIFIED this run). ambientCG matters for **materials** (wood veneer, plywood, fabric, laminate) used to retexture/model the gap items, not for models.

### 1.5 Sketchfab (CC0 / CC-BY downloadables)
- Licence per model is read from the official API field `license.label` (Appendix B). CC-BY 4.0 terms verified at https://creativecommons.org/licenses/by/4.0/ : commercial use and adaptation allowed; must give credit, link the licence and indicate changes.
- https://sketchfab.com/licenses did not render via WebFetch (JS page) → licence semantics taken from the CC deed above.
- Sketchfab CC0 content is dominated by museum photogrammetry (Smithsonian, Cleveland Museum of Art, Virtual Museums of Małopolska): 100k–3M faces, mostly 18th-century pieces → useful only as decimated hero items.
- Red flags found and rejected: re-uploads of Quixel Megascans assets labelled CC-BY (e.g. 9196fe561ed64777ba4f9ca3350c87eb), fan models of commercial game IP labelled CC-BY (Poppy Playtime snack machine), branded electronics (Sony PVM/Trinitron, Nortel) — trademark exposure.
- Licence conflict case: "[CC0] Newspaper Stack" (c4311a0b918643af97904e10c7a34efc) says CC0 in its description but the licence field is CC-BY → follow the stricter CC-BY.
- Downloading from Sketchfab requires a free account (not a paid one) — acceptable under the task rules.

### 1.6 Smithsonian Open Access 3D (CC0)
- https://3d.si.edu/ and https://www.si.edu/openaccess both returned HTTP 403 to WebFetch (UNVERIFIED directly).
- The Smithsonian's own Sketchfab uploads carry `license = CC0 Public Domain` in the Sketchfab API, and each description states the file is in the public domain (verified for "Armchair With Slip Seat" c6c4a65abf90401abab62f238f13a640, "Side Chair" 9c7f1f712edc4b3196e8dcca39a9a537, "Chair (England) 1750-60" 40688b848b6044f6af306ecdf2b8b105 — Cooper Hewitt collection scans, 100k–150k faces).
- Verdict: only relevant for a hero Queen Anne / Georgian chair; needs retopology. Not era-typical of a 1990s household.

### 1.7 OpenGameArt (per-file licence)
- Verified https://opengameart.org/content/office-desk-and-chair-set : CC0, by gamekorp, 2015, OfficeSetcc0.zip 8.8 MB, 1024 px diffuse + AO, "pretty low poly". → **reject** (diffuse-only, 2015 low-poly, wooden office set; below the PBR bar). Other OGA furniture packs found are Quaternius low-poly mirrors.
- Rule: OGA licence is per submission and sometimes per file; always read the licence box on the exact page.

### 1.8 BlenderKit (free assets, Royalty Free licence, add-on)
- Official Blender manual (https://docs.blender.org/manual/en/2.93/addons/3d_view/blenderkit.html, via search result) states both BlenderKit licences (Royalty Free and CC0) allow commercial use. The BlenderKit licence page redirected to an unexpected domain (blendkit.com) and was **not followed**; exact Royalty-Free terms for export to Unity are therefore **UNVERIFIED**.
- Practical notes: assets are fetched through the BlenderKit add-on inside Blender with a (free) account; free tier exists, many assets are paid ("Full plan"). Recommend only the **CC0-tagged** BlenderKit models if Red wants to use it, and record the asset page URL per model.

### 1.9 Fab.com (Standard Licence / CC licences)
- https://www.fab.com/eula returned 403. Verified via Epic's documentation https://dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab : licence types = CC-BY (free), Standard (free or paid; Personal tier for buyers under USD 100,000 gross revenue in the last 12 months; Professional above), and legacy UE Marketplace licence.
- Secondary sources (CG Channel 2024-10-22, https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/ ; search summary) state the Standard Licence allows use "in any game engine or tool" — i.e. **Unity is allowed** for Standard-licensed listings, **except listings marked "UE-Only"** (legacy Unreal Marketplace content), which may only ship with Unreal Engine code (Unreal forum / Epic EULA, search result). Megascans were free only until end-2024.
- Verdict: usable in principle (check each listing shows "Standard" or "CC-BY", not "UE-Only"), but Fab requires an Epic account and its pages could not be fetched here → **no Fab candidate is marked verified**. Do not use the Sketchfab re-uploads of Megascans.

### 1.10 Unity Asset Store (Standard Unity Asset Store EULA)
- Verified https://unity.com/legal/as-terms : non-exclusive perpetual licence to incorporate the asset into an application and monetise it there; raw-asset redistribution forbidden. Fine for FrontRooms.
- Pipeline caveat: many free office packs ship Built-in RP materials → run Edit ▸ Rendering ▸ Materials ▸ Convert to URP, or rebuild with the project's `FrontRooms/Surface` shader. The only 1990s-office Asset Store pack surfaced ("90s Office - HDRP") is paid and not URP-compatible → rejected (Section 2.32).

### 1.11 CGTrader free (Royalty Free)
- Verified https://www.cgtrader.com/pages/terms-and-conditions : Royalty Free products may be used inside a game "if the Product is contained inside a proprietary format and displays inside the game during play"; standalone resale/redistribution prohibited; **Editorial** items are restricted to journalistic use → reject any model marked Editorial (common for branded copiers, vending machines and PCs).

### 1.12 TurboSquid free
- https://www.turbosquid.com/licensing returned 403. Search-result summary of that page: models are royalty-free unless otherwise noted and games are an allowed use. Editorial-marked models are excluded. **UNVERIFIED** at source; treat as maybe.

### 1.13 Free3D
- https://free3d.com/terms returned 403. Free3D mixes "Personal Use Only" and "Royalty Free" per model; Personal Use Only forbids any commercial use (search summary). → Per-model check mandatory; **no Free3D candidate verified**; default **reject** unless the model page says Royalty Free.

### 1.14 itch.io asset packs
- Licence is whatever the creator writes on the pack page (CC0 common for PSX packs). Searched results skew to PSX/low-poly packs (wrong look). No itch.io pack met the PBR/era bar in this run.

## 2. Candidates per asset type

Column key: **Tris** = triangles/faces reported by the source API. **Tex** = max texture resolution in the source download. **DL** = download size (Poly Haven: glTF 2K incl. textures; Sketchfab: auto-converted GLB archive incl. textures). Sketchfab page URL pattern `https://sketchfab.com/3d-models/<uid>`; every Sketchfab row marked "yes" was confirmed `isDownloadable=true` with licence CC Attribution 4.0 (or CC0 where stated) via `api.sketchfab.com/v3/models/<uid>` or the search API on 2026-10-02. "yes (listing)" = confirmed from the search API record only (licence, faces, archive), description not read.

### 2.1 Office desk (1990s laminate top, metal/wood frame, drawer pedestal)

Target: beige laminate top, dark-brown steel frame, beige 3-drawer pedestal (ref_office_target.png).

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Metal Office Desk (Ulan Cabanilla) | Poly Haven https://polyhaven.com/a/metal_office_desk | CC0 | 6,898 | 8K (use 2K) | 5.2 MB glTF-2K / 6.0 MB FBX-2K | Good: worn grey steel double-pedestal "tanker" desk, 2000 x 947 x 788 mm; common 1950s–90s | yes | **use** (desk variant B) | Best-quality CC0 desk found. Not the beige-laminate desk of the ref → use as second desk type (supervisor desk, pile item). Full PBR (Diffuse, ARM, nor_gl). |
| Office Desk (inside "90s Retro Office Pack", MadeByYeshe) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY 4.0 | pack total 44,155 | 4K (160 textures in pack) | 56.5 MB GLB (whole pack) | Excellent (explicit 1990s office pack) | yes | maybe | Author says it was a first Substance Painter project, tagged "lowpoly"; quality unproven at hero distance. Extract desk, re-bake to project texel density. |
| Office Desk 140x60 (AleixoAlonso) | Sketchfab 9262f311271c4c4390341e526d3fe103 | CC-BY | 7,100 | 4K | 23.2 MB | Modern | UNVERIFIED (prior-run listing) | reject | Modern desk. |
| School Desk 01 | Poly Haven https://polyhaven.com/a/SchoolDesk_01 | CC0 | 4,162 | 4K | 1.1 MB | School | yes | reject | Wrong typology. |
| **Gap** | — | — | — | — | — | — | — | — | Exact target desk (beige laminate + brown steel C-frame + beige pedestal) has no downloadable equivalent → **model in Blender** (≈1.5–3k tris, bevelled edges, laminate edge banding; drawer fronts as a separate sub-mesh so piles can reuse them). |

### 2.2 Cubicle / partition fabric panels

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Cubicle Separator (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | 56.5 MB pack | Excellent | yes | maybe | One panel size only; Red needs ~1.5 m blue-grey fabric panels in several widths + posts. |
| Low Poly 90s Office Cubicle (NobleCrowDev) | Sketchfab 4912ac8a39e546e39524badcca7b240f | CC-BY | 4,206 | 512 px | 2.9 MB | 90s but PSX-styled | yes | reject | PSX look; author says it was "more for fun". |
| Room Partition 5175-5 (iDivide) | Sketchfab 0f244a4985134d38ae4dec414499ccee | CC-BY | 12,066 | 512 px | 0.9 MB | Modern translucent twinwall | yes | reject | Manufacturer product model. |
| **Gap** | — | — | — | — | — | — | — | — | **Model in Blender**: parametric panel (aluminium frame + fabric face + top cap + connector post); quality comes from the fabric material (texture report 03). Widths 0.6/0.9/1.2 m, heights 1.37/1.6 m. |

### 2.3 Beige CRT computer monitor

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| CRT Computer Monitor (fizyman) | Sketchfab f2ff0013f86e4cd0a2aee183a23bdfee | CC-BY | 3,742 | 4K (Color, Rough, Metal, Normal-GL, AO; separate shell + glass materials) | 47.4 MB GLB | Good generic CRT (shell colour UNVERIFIED — thumbnail not viewed) | yes | **use** | Game-ready, non-overlapping UVs (author). Downscale to 2K/1K. Separate glass material → drive an emissive screen. |
| Retro CRT Computer (1990s Desktop PC) (MadeByYeshe) | Sketchfab ea9faf1298d24497b916c27a4ea38636 | CC-BY | 2,416 (monitor+keyboard+mouse) | 1K PBR | 2.6 MB | Excellent (explicit 1990s office PC) | yes | **use** | Very cheap → ideal for many instanced desks. Tags include psx/ps1: confirm textures are not posterised before committing. |
| 3x Retro PC (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | Three variants; whether a tower/desktop case is included is UNVERIFIED. |
| CRT Monitor (Oliver Triplett) | Sketchfab 140738b1308446679c763a3d3d86a873 | CC-BY | 2,347 | 2K | 7.2 MB | Retro-futurist (Alien: Isolation style per author) | yes | reject | Wrong design language. |

### 2.4 Beige PC tower / desktop case

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Old Pc (newarcov) | Sketchfab 4d237a57b18a42d9a56c0d9a7ed0371a | CC-BY | 11,692 | 4K | 34.3 MB | 90s, dirty/damaged | yes | maybe | Author: not fully optimised for games → decimate. |
| 90s Retro Office Pack PCs | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | See 2.3. |
| Retro Monitor & PC Tower, PSX Style (410prod) | Sketchfab 36b9d8a6018c493282916df39e149365 | CC-BY | 126 | 256 px | 0.03 MB | PSX | yes (listing) | reject | Blockout only. |
| **Gap (partial)** | — | — | — | — | — | — | — | — | Beige tower/desktop case = bevelled box + bezel decal → **model in Blender** (≤600 tris), share the CRT's beige ABS material. |

### 2.5 Keyboard and 2.6 Mouse

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Keyboard + mouse inside Retro CRT Computer (MadeByYeshe) | Sketchfab ea9faf1298d24497b916c27a4ea38636 | CC-BY | in 2,416 | 1K | 2.6 MB | Excellent | yes | **use** | Split into separate meshes in Blender so each desk can offset them. |
| 90s Retro Office Pack (keyboard/mouse tags) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | Alternate set. |
| Retro Computer With Mouse And Keyboard (jampakdd) | Sketchfab b0a0b822b3be444ab751414c657658c8 | CC-BY | 1,540 | none | 0.2 MB | Generic | yes (listing) | reject | Untextured. |

### 2.7 Office swivel chair (5-star base)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Office Chair (artvolodskikh), "Bureaukrat" reference | Sketchfab a7fefb5dde954c84896949246dde5be6 | CC-BY | 5,488 | 4K | 28.5 MB | Generic task chair (silhouette UNVERIFIED) | yes | **use** (if silhouette reads 90s) | Game-ready, Substance-textured, low tris: best budget/quality ratio found. |
| Office chair (inven2000 / AK STUDIO) | Sketchfab af2f07d06f6349158c1d24d87f5ceb95 | CC-BY | 28,768 | 2K | 10.1 MB | Generic | yes | maybe | Decimate to ~8k for instancing. |
| Office Chair (nokillnando) | Sketchfab b228a29fa84544c2be501c295653ffe7 | CC-BY | 9,454 | 2K | 35.1 MB | Generic | yes | maybe | Same author as the MFP printer (2.9). |
| Worn Leather Office Chair (FordVFX) | Sketchfab 003b00c7cdd348888296b85c40275a50 | CC-BY | 27,270 | 2K | 41.7 MB | Executive/study chair (wood + leather) | yes | maybe | Manager office / pile item, not the cubicle task chair. |
| Leather Chair (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | |
| High-Poly PBR Office Chair (kilicarslan) | Sketchfab fa2d5243f916407a93db7efcaae75e0d | CC-BY | 23,334 | 4K | 17.8 MB | Probably modern | yes | reject | Modern look. |

### 2.8 Water cooler with bottle

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Water cooler (tboiston) | Sketchfab 4b88c4c4e94c497ca39f831f374e89fc | CC-BY | 2,188 | 4K | 16.3 MB | Classic floor cooler + bottle (uni project) | yes | **use** | Check that the bottle is a separate mesh so a blue transparent URP material can be assigned. |
| Water Cooler_8MB (Mehdi Shahsavan / ahmagh2e) | Sketchfab 9aef3e2a5d00481eb2864550bc781e7c | CC-BY | 12,886 | 2K | 6.5 MB | Generic | yes | maybe | 12 MB variant: fea47b4738774f238b2914b8852c7bb1. |
| Water Cooler (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | |
| Old Water Cooler (alii.maghami) | Sketchfab 10a08e3ea4ff4055b913add41b016050 | CC-BY | 145,874 | 8K | 19.8 MB | ? | UNVERIFIED (prior listing) | reject | Too heavy. |

### 2.9 Photocopier

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Copier (ykykykk) | Sketchfab 9eebb4e8b77944159892df30d8b44de5 | CC-BY | 1,782 | 4K | 4.8 MB | Unknown (not viewed) | yes (listing) | maybe | Only textured low-poly copier found; ref needs beige floor copier with paper drawers. |
| MFP Office Printer (nokillnando) | Sketchfab d55f6fca7c3d45c883bbff770672970d | CC-BY | 7,685 | 2K (28 textures) | 41.6 MB | Multi-function printer (probably 2000s+) | yes (listing) | maybe | 650 likes = solid craft; re-tint beige, hide the touch panel. |
| Old Copier (sookendestroy1) | Sketchfab 3d9bd04e9e8e497c9bb51d5d326f1cbe | CC-BY | 1,646 | none | 0.1 MB | ? | yes | reject | Untextured (2015). |
| IMPRIMANTE (nando59) / Low Poly Office Copy Machine (JeremyGrayson) | Sketchfab 6722b414a72b4aa4a275135bd7f3a3cd / f6d56154ad87402e899f8a2df4b114d9 | CC-BY | 132k / 394 | none | — | — | yes (listing) | reject | Untextured. |
| **Gap (likely)** | — | — | — | — | — | — | — | — | If neither "maybe" matches the ref: **model in Blender** (beige body + 3 paper drawers + platen lid + panel decal ≈ 1–2k tris). |

### 2.10 Vending machine (snack)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Vending Machine (AtTheSpeedOf) | Sketchfab af792a359ab24c6eaf1e8d98640f05a8 | CC-BY | 13,326 | 2K | 7.3 MB | Worn; author: "Empty Vending Machine" | yes | maybe | Good shell; interior empty → add instanced snack rows (coil + packet quads) ourselves. |
| Vending Machine (RackRibs) | Sketchfab d62a741a00e04d84bc45b6ccb039cf8a | CC-BY | 1,626 | 1K | 1.7 MB | Japanese snacks (off-locale) | yes | maybe | Cheap; replace snack texture. |
| Soda Vending Machine (RasenDan) / Retro Vending Machine (Ebethrone) | Sketchfab f753a659faae499282e882d63972d4c2 / 2390b6696cde4fc9bb999e0bb923a785 | CC-BY | 247k / 8k | 1K / 2K | 19 / 7.6 MB | Soda machines | UNVERIFIED (prior listing) | reject | Soda, not snack; first one far too heavy. |
| "Poppy Playtime Chapter 3: Snack Machine" | Sketchfab 492f8601f9c54c839cbed430ee6cd8cf | labelled CC-BY | 6,474 | 2K | 13.9 MB | — | yes (listing) | **reject** | Derived from a commercial game IP; uploader's CC-BY label is not trustworthy. |

### 2.11 Steel filing cabinet

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Filing Cabinet - 6MB (Mehdi Shahsavan / ahmagh2e) | Sketchfab d217a4bbdfa2426eb32ebf3b1007a8c3 | CC-BY | 6,806 | 2K | 5.3 MB | Generic vertical steel cabinet | yes | **use** | 16 MB variant: ac5d883bec4549508aa579f792d59954 (16,246 tris). |
| Filing Cabinet (matthijs001) | Sketchfab adb93fd3a2d84d3ea6f002cd4f1ea7a8 | CC-BY | 1,072 | 4K | 72.3 MB | 3-drawer, corroded metal | yes | maybe | Very low tris + heavy textures → downscale to 2K. |
| Filing Cabinets (TooManyDemons) | Sketchfab 7ef1ca295ff14af2abcbe0ae0168a241 | CC-BY | 7,351 | 2K | 19.7 MB | Made for a Unity sci-fi scene; drawers pulled out | yes | maybe | Pulled-out drawers suit the "disheveled" pile. |
| Metal Cabinet (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | |
| Vintage Wooden Drawer 01 (6-drawer wooden filing cabinet) | Poly Haven https://polyhaven.com/a/vintage_wooden_drawer_01 | CC0 | 5,184 | 8K | 2.0 MB glTF-2K | Pre-war wooden office | yes | maybe | Not steel, but CC0 + high quality → pile item. |
| Rusty Metal Cabinet - "3D scan Quixel Megascans" (Guay0) | Sketchfab 9196fe561ed64777ba4f9ca3350c87eb | labelled CC-BY | 22,978 | 2K | 12.4 MB | — | yes | **reject** | Re-upload of a Quixel Megascans asset (author field says Quixel); uploader cannot relicense it as CC-BY. |

### 2.12 Bookshelf / open shelf

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Wooden Bookshelf Worn (Ulan Cabanilla) | Poly Haven https://polyhaven.com/a/wooden_bookshelf_worn | CC0 | 10,106 | 4K | 10.3 MB glTF-2K | Good: worn plywood-edged bookcase 1374 x 581 x 2063 mm | yes | **use** | Matches the "open oak bookshelf" of Still B once the albedo is warmed/darkened. |
| Shelf 01 (Gabriel Radić) | Poly Haven https://polyhaven.com/a/Shelf_01 | CC0 | 182 | 4K | 2.5 MB | Distressed painted tall shelf | yes | **use** | Extremely cheap; ideal for many pile copies. |
| Steel Frame Shelves 01 (James Ray Cock) | Poly Haven https://polyhaven.com/a/steel_frame_shelves_01 | CC0 | 4,348 | 8K | 5.6 MB | Steel frame + planks; office storeroom | yes | **use** | Office back rooms. `_02` is an identical-tri variant. |
| Worn Metal Rack (Luca B) | Poly Haven https://polyhaven.com/a/worn_metal_rack | CC0 | 6,372 | 8K | 6.8 MB | Green painted steel rack | yes | maybe | Storeroom only. |
| Painted Wooden Cabinet 02 (bookcase, blue paint) | Poly Haven https://polyhaven.com/a/painted_wooden_cabinet_02 | CC0 | 966 | 4K | 6.2 MB | Rustic farmhouse | yes | maybe | Household pile variety. |
| Wooden Display Shelves 01 | Poly Haven https://polyhaven.com/a/wooden_display_shelves_01 | CC0 | 3,174 | 8K | 1.4 MB | Modern pine cubbies | yes | reject | Too contemporary (IKEA-like). |

### 2.13 Chest of drawers / dresser (Still A: orange-grain chest tipped on a corner)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Old dresser (Vladyslav Holhanov / vladicom08) | Sketchfab d235f91eee0a484d95283afccc83931d | CC-BY | 2,638 | 2K | 8.3 MB | Generic old bureau/commode | yes | maybe | Cheap; grain colour UNVERIFIED → retint toward orange 1970s veneer. |
| Old Dresser (slls666) | Sketchfab 3ee2cb9b3d9d441ea2e99e6c801ee0b8 | CC-BY | 39,383 | 4K | 42.0 MB | Antique/vintage | yes | maybe | Textures come from ambientCG (CC0) per author; decimate to ≤10k. |
| Painted Wooden Cabinet (2 drawers + doors) | Poly Haven https://polyhaven.com/a/painted_wooden_cabinet | CC0 | 2,227 | 4K | 6.8 MB | Farmhouse painted | yes | maybe | CC0 alternative; wrong finish (paint, not veneer). |
| Gothic Commode 01 | Poly Haven https://polyhaven.com/a/GothicCommode_01 | CC0 | 3,897 | 4K | 1.7 MB | Carved gothic | yes | reject | Wrong era. |
| Drawer Cabinet (modern) | Poly Haven https://polyhaven.com/a/drawer_cabinet | CC0 | 26,406 | 4K | 2.1 MB | Modern black frame | yes | reject | Wrong era. |
| **Gap (partial)** | — | — | — | — | — | — | — | — | A 1970s flat-front veneer chest is the most-repeated pile element; **model in Blender** (carcass + 4–6 drawer fronts + plinth + pulls ≈ 800–1,500 tris) and texture with a CC0 wood-veneer set (texture report 03). Sharing one veneer material across chest/sideboard/desk keeps draw calls low. |

### 2.14 Wooden cabinet / hutch / sideboard

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Sideboard (tony chopper / choppar) | Sketchfab 1492a0e14568490bb5c3a20e903622ac | CC-BY | 980 | 2K | 9.8 MB | "vintage" low-poly sideboard | yes | **use** | Cheap, game-ready per tags. |
| Mid Century Teak Sideboard Credenza (calebkung) | Sketchfab 3028ba44d1f245b886c12eadc934f722 | CC-BY | 21,794 | 1K | 1.7 MB | 1960s–70s teak credenza, 1350 x 360 x 635 mm | yes | maybe | Made for close-up renders; decimate. |
| Old Hutch (raeganmaddox) | Sketchfab c6d26a7ab43249ceb408a7cde32cb166 | CC-BY | 38,876 | 2K | 46.0 MB | Weathered hutch | yes | maybe | Exactly the "dark wood hutch leaning 45°" typology; decimate to ~10k. |
| Wooden Back Bar Cabinet (mark-peters) | Sketchfab a1961b9e5a7043fb9a70b855e947e27f | CC-BY | 23,213 | 4K | 53.6 MB | Bar back cabinet | yes (listing) | maybe | |
| Painted Wooden Cabinet | Poly Haven https://polyhaven.com/a/painted_wooden_cabinet | CC0 | 2,227 | 4K | 6.8 MB | Farmhouse | yes | maybe | See 2.13. |

### 2.15 Queen Anne armchair (Still A: pink velvet, cabriole legs)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Antique Wing Back Chair lowpoly (3DCraftsman / diapant95) | Sketchfab 49e21ea4c0bf469387471934dd8bf0fa | CC-BY | 2,478 | 2K | 10.7 MB | Author: "Velvet armchair with wooden legs"; tags victorian/antique/velvet (Queen Anne wingbacks are this family) | yes | **use** | Cheapest on-brief option; retint the velvet albedo to dusty pink. Leg shape (cabriole vs turned) UNVERIFIED. |
| Green Chair 01 (Kirill Sannikov) | Poly Haven https://polyhaven.com/a/GreenChair_01 | CC0 | 4,213 | 4K | 2.0 MB | Carved wooden armchair, green fabric, curved legs | yes | maybe | CC0 fallback; retint fabric pink. Reads "gothic" up close. |
| Arm Chair 01 (Kirill Sannikov) | Poly Haven https://polyhaven.com/a/ArmChair_01 | CC0 | 5,626 | 4K | 2.8 MB | Victorian carved armchair | yes | maybe | |
| Classic Victorian Wooden Armchair – Red Velvet (khalandarthameem97) | Sketchfab 045a190f982b40f28b62eb7f503f3948 | CC-BY | 40,000 | 2K | 3.6 MB | Victorian velvet | yes (listing) | maybe | Decimate. |
| Antique white armchair (klava88) | Sketchfab 148a621c978e4c2fb9ecb6c41b852c1d | CC-BY | 39,954 | 2K | 3.0 MB | Antique French | yes (listing) | maybe | 331 likes. |
| Armchair With Slip Seat (Smithsonian / Cooper Hewitt) | Sketchfab c6c4a65abf90401abab62f238f13a640 | **CC0** | 150,000 | (scan) | n/a | 18th-c. museum piece (photogrammetry) | yes | maybe | Authentic cabriole-leg form; needs retopo/decimate + re-UV — only worth it if Red wants a hero chair. |
| Vintage Wingback Armchair (pranavranjan2212) | Sketchfab d606a3eb868d4122855bc7a82d2889a9 | CC-BY | 102,937 | 4K | 44.2 MB | Leather wingback | yes | reject | Too heavy for instanced piles. |

### 2.16 Fabric sofa (floral / plaid, 1970s–90s)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Old Plaid Sofa (lena-wachs) | Sketchfab 9feaf83034ca4382a099c18cec5aecb3 | CC-BY | 8,668 | 2 x 2K | 42.8 MB | 1970s plaid sofa ("70's" tag) | yes | **use** | Game-ready. For Still B's beige floral sofa, swap the albedo for a floral upholstery texture (same UVs). |
| Old Couch (oisougabo) | Sketchfab 443d9bb95e944afe8ebc4ff489e2886c | CC-BY | 7,964 | 2K | 13.7 MB | Worn, muddy couch made for horror scenes | yes | **use** | Good second sofa; clean up mud via albedo tint if needed. |
| Old Sofa (FREE) (RenderRum Filip Rumin) | Sketchfab 90be7242f24749c3a8e0b0a69c616fc1 | CC-BY | 57,306 | 4K | 44.5 MB | Old leather sofa | yes | maybe | Decimate; leather not fabric. |
| Old Sofa (glezova) | Sketchfab 3fe7ed15c42e48b8820792e8cef64f93 | CC-BY | 6,894 | 4K (21 textures) | 282.6 MB | — | yes (listing) | reject | Archive far too large. |
| Sofa 01 / Sofa 02 / Sofa 03 | Poly Haven Sofa_01, sofa_02, sofa_03 | CC0 | 4,101 / 2,728 / 8,004 | 4K–8K | 2–10 MB | Victorian / tufted leather | yes (prior API) | reject | Wrong era. |
| Floral sofas found (Modenese "Duchess", CMBC "...Bloom..." series) | Sketchfab 4cae2f4486964f3f87f513911eb7513b etc. | CC-BY | 230k–700k | none/2K | — | Baroque / art pieces | yes (listing) | reject | Untextured or sculptural, very heavy. |

### 2.17 Club armchair (Still B: teal fabric)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Old Armchair (MaX3Dd) | Sketchfab c20f084f29bd440197a18b4c750f69eb | CC-BY | 2,588 | 4K (1 PBR set) | 35.3 MB | Worn leather club chair | yes | **use** | Swap leather for teal fabric material (same UVs). |
| Club Chair (Saandy) | Sketchfab da25d54972b04a8e9fa64048c7bcb89c | CC-BY | 10,696 | 2K | 9.0 MB | Leather club chair (Comedy Store reference) | yes | maybe | |
| Club chair (alban) | Sketchfab 0edad579dcd9431e9b91c1fff4b84700 | CC-BY | 36,177 | 4K | 7.0 MB | 3D scan (2014) | yes | maybe | Scan → decimate. |
| Mid Century Lounge Chair | Poly Haven https://polyhaven.com/a/mid_century_lounge_chair | CC0 | 6,148 | 8K | 7.7 MB | Eames-like lounge | yes | reject | Wrong silhouette. |

### 2.18 Ladder-back wooden chair

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Low-poly Ladder Back Chair (Average3DmodelEnjoyer) | Sketchfab 8a922e83386843028527e796e880d7b0 | CC-BY | 758 | 4K | 22.0 MB | Classic ladder-back | yes | **use** | Very cheap; author warns topology may be rough → check normals. |
| French Ladder Back Chair (same author) | Sketchfab 39a05a5dd79f4d34b42e89b59033dd12 | CC-BY | 10,166 | 4K | 48.4 MB | Ladder-back with cushion | yes | maybe | Hero variant. |
| Painted Wooden Chair 01 (Kuutti Siitonen) | Poly Haven https://polyhaven.com/a/painted_wooden_chair_01 | CC0 | 724 | 8K | 1.5 MB | White farmhouse chair (splat back) | yes | maybe | CC0 alternative, not ladder-back. |
| Painted Wooden Chair 02 (Kirill Sannikov) | Poly Haven https://polyhaven.com/a/painted_wooden_chair_02 | CC0 | 1,246 | 4K | 9.4 MB | Farmhouse dining chair | yes | maybe | |

### 2.19 Wooden bar stool

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Bar Chair Round 01 (Dairon Sanchez) | Poly Haven https://polyhaven.com/a/bar_chair_round_01 | CC0 | 14,373 | 4K | 7.2 MB | Vintage wooden bar stool, round seat, footrest ring, 751 mm high | yes | **use** | Best match; decimate to ~6k for pile copies. |
| Wooden Stool 01 (Kuutti Siitonen) | Poly Haven https://polyhaven.com/a/wooden_stool_01 | CC0 | 10,946 | 8K | 3.2 MB | Turned-leg low stool (437 mm) | yes | maybe | Low stool, not bar height. |
| Bar Stool (raeganmaddox) | Sketchfab 382d65cea3e84bb68b81fd318b10d12c | CC-BY | 4,690 | 1K | 2.0 MB | Leather + wood bar stool | yes | maybe | |
| Painted Wooden Stool | Poly Haven https://polyhaven.com/a/painted_wooden_stool | CC0 | 676 | 4K | 6.7 MB | Farmhouse | yes | maybe | |

### 2.20 Side table with turned legs (Still A: two-tier, on casters)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Side Table Tall 01 (James Ray Cock) | Poly Haven https://polyhaven.com/a/side_table_tall_01 | CC0 | 6,408 | 8K | 1.4 MB | Tall vintage side table, curved legs, lower shelf | yes | **use** | Two-tier already; add 4 small casters in Blender. |
| Small Wooden Table 01 (Ulan Cabanilla) | Poly Haven https://polyhaven.com/a/small_wooden_table_01 | CC0 | 3,410 | 4K | 1.4 MB | Vintage, rounded legs, double stretchers | yes | maybe | |
| Classic Nightstand 01 | Poly Haven https://polyhaven.com/a/ClassicNightstand_01 | CC0 | 2,002 | 4K | 1.4 MB | Cabriole legs, open shelf (Victorian) | yes | maybe | |
| Side Table 01 | Poly Haven https://polyhaven.com/a/side_table_01 | CC0 | 2,756 | 8K | 1.6 MB | Minimalist modern | yes | reject | |

### 2.21 Rolling cart / cabinet on casters

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Industrial Storage Cart (Jule Bielitz) | Poly Haven https://polyhaven.com/a/industrial_storage_cart | CC0 | 18,902 | 8K | 8.1 MB | Riveted steel cart, trays, double-door cabinet, casters; rusty | yes | maybe | Office/storeroom cart after de-rusting the albedo; heavy-ish. |
| Tool Cart (Savva Zakharov) | Poly Haven https://polyhaven.com/a/tool_cart | CC0 | 29,394 | 8K | 9.8 MB | Green metal tool cart | yes | maybe | Over the 30k-ish budget edge; decimate. |
| [Free] Drawer Tool Cart (Used) (Robert Prispilović) | Sketchfab da8955e5c8c448e58b013951f48148a0 | CC-BY | 850 | 2K | 7.9 MB | Generic drawer tool cart | yes | maybe | Cheap stand-in for the "small rolling cabinet". |
| **Gap (partial)** | — | — | — | — | — | — | — | — | The small wooden/laminate rolling cabinet of Still A (TV/AV cart look) → **model in Blender** (box + door + 4 casters ≈ 600 tris) sharing the veneer material. |

### 2.22 Table lamp with pleated shade

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Classic table lamp (AndreiVNK) | Sketchfab 1a3292317bb342b4b33431081338a5c3 | CC-BY | 14,548 | 4K | 28.8 MB | Classic fabric-shade table lamp | yes | maybe | Shade is probably smooth, not pleated (UNVERIFIED). |
| Old Table Lamp V02 (MAR.COS.) | Sketchfab 70659923adc74413ba983516139e222d | CC-BY | 2,686 | 2K | 5.5 MB | Victorian / art-deco | yes | maybe | DirectX normal map → flip G in Unity import (Unity expects OpenGL-style). |
| 1920s Table Lamps (Mad_Lobster_Workshop) | Sketchfab fb7475ef551c46f9b4b2b28d96d31dfc | CC-BY | 66,992 | 4K | 193 MB | 1920s | yes (listing) | reject | Too heavy. |
| **Gap (partial)** | — | — | — | — | — | — | — | — | Pleated shade = lathe + sine-displaced pleats in Blender (≈1k tris) on a ceramic/brass base; cheap and exactly on-brief. |

### 2.23 Halogen torchiere floor lamp (Still B)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Floor_lamp (Uragan27) — tagged "torchere" | Sketchfab 1ea7bb08894243f5b1f1200ee35fb40a | CC-BY | 2,152 | 2K | 6.6 MB | Torchiere tag; 1990s halogen bowl UNVERIFIED | yes | maybe | Check silhouette (thin pole + shallow uplight bowl). |
| Vintage Floor Lamp 70s Freebie (Geug) | Sketchfab 36c21f6b4c4e4b1d94401c287f902362 | CC-BY | 23,984 | 4K | 97.3 MB | 1970s design lamp | yes | reject | Not a torchiere; heavy. |
| **Gap (likely)** | — | — | — | — | — | — | — | — | Trivial lathe model (weighted base disc, 1.8 m pole, black metal bowl, emissive inner disc) ≈ 300 tris. |

### 2.24 Black CRT TV

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Television 02 (Benny Weimer) | Poly Haven https://polyhaven.com/a/television_02 | CC0 | 2,310 | 8K | 3.9 MB glTF-2K | Chunky retro CRT, plastic bezel, push buttons, 400 x 350 x 411 mm | yes | **use** | Closest CC0 match to the black 1990s set; recolour bezel black if needed. |
| Television 01 (Gabriel Radić) | Poly Haven https://polyhaven.com/a/Television_01 | CC0 | 1,918 | 4K | 1.6 MB | 1970s wood-cased tabletop CRT | yes | **use** (household variant) | Great for the household piles. |
| Small CRT TV (rhcreations) | Sketchfab 890c6ce1f6124c02b0cad54db0fdcb52 | CC-BY | 2,304 | 1K | 9.5 MB | Small CRT | yes | maybe | |
| Vintage TV Free (donnichols) | Sketchfab ed92cac6b8d64ea48ea4f91ce9bf350b | CC-BY | 3,326 | 1K | 3.0 MB | 1970s/80s analog TV | yes | maybe | Free low-res version of a paid HD model. |
| Retro CRT TV (meipal / ashabbugaev12) | Sketchfab 6bc462b233ce4c78904dfcadf5123e29 | CC-BY | 1,708 | 2K | 16.5 MB | Stylised cyberpunk stickers | yes | reject | Stylised. |
| Sony PVM / Trinitron models | Sketchfab 5f80311f1a4646ef9673f20ee6dc6245, 9de7c78e35824eff94bb77acf47b250d | CC-BY | 240k / 44k | 4K | 117 / 115 MB | Branded | yes (listing) | reject | Heavy + visible trademarks. |

### 2.25 Glass display cabinet (Still B)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Soviet Vintage Kitchen Cabinet (PBR Lowpoly) (Vitalii.Sandula) | Sketchfab 154bb3f924b64cdd935f2e196fa8a1e8 | CC-BY | 2,704 | 2K | 7.4 MB | 1950s–70s lacquered wood + glass doors | yes | **use** | Cheap, glass doors, plausible in a US household pile once the lattice reads as generic. |
| victorian Cabinet (lagesnpiet) | Sketchfab 81291e282b854934a6f1b9f53a900f5f | CC-BY | 2,876 | 4K | 42.2 MB | Victorian china cabinet, glass | yes | **use** | Game-ready, clean UVs per author. |
| Vintage Cabinet 01 (Rico Cilliers) | Poly Haven https://polyhaven.com/a/vintage_cabinet_01 | CC0 | 61,096 | 8K | 5.0 MB glTF-2K (FBX 2K 72.9 MB) | Dark-wood cabinet, glass-front upper doors, 2022 x 670 x 2235 mm | yes | maybe | Best CC0 quality but 61k tris → decimate to ~15k or use once per pile. |
| Victorian Display Cabinet (Jonny Crabb) | Sketchfab 9b11556cd24f4a16b4e451ade7946e53 | CC-BY | 930 | 2K | 1.6 MB | Gilded mahogany vitrine | yes | maybe | |

### 2.26 Wooden pallet

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Wooden Pallet Low-poly (MaX3Dd) | Sketchfab 2f1abd705d4f4118b4c8d0b275441505 | CC-BY | 1,372 | 2K PBR | 8.7 MB | Standard pallet | yes | **use** | |
| Wooden Pallets (YadroGames) | Sketchfab dba5c00928cd400796d9f6fffdd724b3 | CC-BY | 384 | 2K (baked) | 6.8 MB | Standard pallet(s) | yes | **use** | Unity-compatible per author. |
| Wooden Pallet (torricane) / Wood Pallet (commonspence) | Sketchfab e1b107ddf32f4a3981557b4ba0e63063 / 63252e96e64a4c32ba876786e2da4f82 | CC-BY | 816 / 250 | 2K | 12.4 / 11.0 MB | Standard | yes (listing, prior run) | maybe | |

### 2.27 Plywood crate ("fragile glass" stencil in Still B)

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Wooden Boxes (MaX3Dd) | Sketchfab ddecbe4586594bddb4822a90c0cba222 | CC-BY | 4,097 | 2K | 16.3 MB | Plank shipping boxes | yes | maybe | Plank, not plywood. |
| Wooden Military Crate (Prabhjinder Singh) | Poly Haven https://polyhaven.com/a/wooden_military_crate | CC0 | 22,986 | 4K | 10.2 MB | Stencilled wooden crate | yes | maybe | Heavy for a box; stencil workflow is a good model to copy. |
| Wooden Crate 01 / 02 (James Ray Cock) | Poly Haven https://polyhaven.com/a/wooden_crate_01 , /wooden_crate_02 | CC0 | 6,576 / 5,176 | 8K | 8.3 / 8.2 MB | Colonial/maritime chests | yes | reject | Wrong typology (rope handles, brass). |
| **Gap** | — | — | — | — | — | — | — | — | Plywood crate = bevelled box + batten frame (≈200–400 tris) with a CC0 plywood texture and an original "FRAGILE / GLASS" stencil decal (do not copy the film's lettering). **Model in Blender.** |

### 2.28 Desk phone

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 90s LandLine (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | **use** | |
| Office Phone (maxdragonn) | Sketchfab 4176a01b6d0b4d13ad165c0df278a6b5 | CC-BY | 4,786 | 512 px | 0.4 MB | Generic office phone | yes | maybe | Low-res texture is acceptable for a tiny prop. |
| Telephone (Office) (retroststem10710) | Sketchfab 6abe79fcf1a34e2e8b2acca44e266289 | CC-BY | 24,388 | 2K | 1.8 MB | RealityScan photogrammetry | yes | maybe | Decimate; real 90s phone scan. |
| Nortel Vista 200 Corded Landline (JordanF) | Sketchfab aa47a7474cdd4e1cbf21b2ceceeabf47 | CC-BY | 63,517 | 4K | 15.2 MB | Branded 1990s phone | UNVERIFIED (prior listing) | reject | Heavy + trademark. |

### 2.29 Paper stacks / binders

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Office Notepads (Ulan Cabanilla) | Poly Haven https://polyhaven.com/a/office_notepads | CC0 | 666 | 4K | 5.7 MB | Legal pads, index cards, sticky notes | yes | **use** | |
| Papers (oparaskos) | Sketchfab f858428c790f43f8ba9a3aa2996b88b0 | CC-BY | 619 | 2K | 5.8 MB | Paper pile + sticky notes | yes | **use** | |
| Document File Folder (Kami Rapacz / kuroderuta) | Sketchfab 11390179bba7462484d344e2fe22c703 | CC-BY | 1,505 | 4K | 51.5 MB | A4 folder, yellowed pages | yes | **use** | Author explicitly asks for credit. Downscale textures. |
| 3x Binder + 12 paper variants (90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | **use** | |
| [CC0] Newspaper Stack (karlwirbelwind) | Sketchfab c4311a0b918643af97904e10c7a34efc | Sketchfab field = CC-BY; description claims CC0 | 2,132 | 2K | 9.6 MB | Newspapers | yes | maybe | Licence conflict → treat as CC-BY (stricter) and credit. |
| Clipboard (ProgrammerOnCoffee) | Poly Haven https://polyhaven.com/a/clipboard | CC0 | 6,176 | 8K | 6.8 MB | Masonite clipboard | yes | maybe | |
| Binder Notebook | Poly Haven https://polyhaven.com/a/binder_notebook | CC0 | 18,077 | 8K | 5.1 MB | Leather personal binder | yes | reject | Not an office ring binder. |

### 2.30 Trash bin

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Metal Bin (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | **use** | |
| Waste Bin (Household Props 24, Daniel O'Neil / doneil) | Sketchfab bb24dc82165346f7a2a64bf2c378504c | CC-BY | 270 | 512 px | 0.3 MB | Household wastebasket (2018) | yes | maybe | Author calls it deliberately simple; fine as a background prop. |
| Trash basket (DevFaisal) | Sketchfab c9bf9a2b04f44fea82c38344cc5ec8f4 | CC-BY | 11,316 | none | 0.5 MB | Generic | yes | reject | Untextured. |
| Metal Trash Can | Poly Haven https://polyhaven.com/a/metal_trash_can | CC0 | 13,960 | 8K | 17.5 MB | Outdoor rusty ribbed can | yes | reject | Street bin, not office. |
| **Fallback** | — | — | — | — | — | — | — | — | Office wastebasket is a tapered cylinder → model in Blender (≈200 tris) if the pack bin fails. |

### 2.31 Wall clock

| Candidate | Source / page | Licence | Tris | Tex | DL | Era fit | Verified | Rec. | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Wall Clock (PierreB3D) | Poly Haven https://polyhaven.com/a/wall_clock | CC0 | 3,658 | 4K | 4.9 MB | Office wall clock, tags include "office" and "90s" | yes | **use** | Has separate glass maps (alpha/rough) → URP transparent glass. |
| Wall Clock (FelipeMSX) | Sketchfab 2e964ac0242e4b1789adfd9549c653dc | CC-BY | 798 | 2K | 3.7 MB | Simple, Roman numerals | yes | maybe | Numerals baked from high-poly. |
| Old wall clock (AndreiVNK) | Sketchfab 8e920e8b129842718099a3f772cec024 | CC-BY | 1,538 | 2K | 11.3 MB | Old domestic clock | yes | maybe | Household piles. |
| Clock (in 90s Retro Office Pack) | Sketchfab dadca97505214b9481d35e22c48e18df | CC-BY | in 44k | 4K | pack | Excellent | yes | maybe | |

### 2.32 Other stores checked (no row-level candidate)

| Item | Page | Licence / price | Verified | Rec. | Why |
|---|---|---|---|---|---|
| 90s Office - HDRP (Robot Skeleton), Unity Asset Store | https://assetstore.unity.com/packages/3d/props/interior/90s-office-hdrp-217427 | Standard Unity EULA, **paid USD 9.89**, HDRP + Built-in only (page says URP not compatible), 219.8 MB, v1.0 2022 | yes | reject | Paid and not URP; the only 1990s-office Asset Store pack surfaced. |
| Office Furniture and More (3D Models - SCA), itch.io | https://3dmodels-sca.itch.io/office-furniture-and-more | CC-BY 4.0 but **paid USD 8.99**; 52 meshes, 2K PBR/ORM, UE + FBX | yes | reject | Paid; contemporary office. |
| Backrooms Asset Pack [FREE] (NaiveGoblin), itch.io | https://naivegoblin.itch.io/cc0-backrooms-asset-pack | Free/PWYW; page wording mixes "CC-BY 4.0" and "CC0" (treat as CC-BY); 2K, GLB, 103 MB | yes | reject (for props) | Modular Level-0 walls/floors/ceilings only — no furniture. Also overlaps the project's own environment kit. |
| Retro Office (bitsoft), itch.io / Fab | https://bitsoft.itch.io/retro-office | Paid (search summary) | UNVERIFIED | reject | PS1/PS2/N64 style. |
| Office Desk and Chair Set (gamekorp), OpenGameArt | https://opengameart.org/content/office-desk-and-chair-set | CC0, 8.8 MB, 1K diffuse + AO, 2015 | yes | reject | Diffuse-only low-poly. |
| Kenney Furniture Kit | https://kenney.nl/assets/furniture-kit | CC0, 140 files, stylised | yes | reject (blockout only) | Stylised flat colour. |
| Quaternius Ultimate House Interior | https://quaternius.com/packs/ultimatehomeinterior.html | CC0, 123 models, untextured | yes | reject (blockout only) | Stylised flat colour. |
| CGTrader "Photocopier Machine 14" | https://www.cgtrader.com/3d-models/interior/office-interior/photocopier-machine-14 | Royalty Free, paid USD 36 (search summary) | UNVERIFIED | reject | Paid. |
| Coohom "realistic low polygon copier" | https://www.coohom.com/3d-models/Printer/realistic-low-polygon-copier-3d-model-mdtl~3FO428HN1I1K | "free use" claim, licence text not seen | UNVERIFIED | reject | Unclear licence. |

## 3. Gaps (no acceptable download — model in Blender)

Hard gaps (nothing downloadable meets era + quality + licence):
1. **Target office desk** — beige laminate top + dark-brown steel C-frame + beige 3-drawer pedestal. (Poly Haven Metal Office Desk is a good *second* desk type, not this one.)
2. **Cubicle fabric partition panels** (several widths/heights, posts, top caps).
3. **Plywood crate** with an original "FRAGILE / GLASS" stencil decal.
4. **Halogen torchiere floor lamp** (one CC-BY "torchere" lamp exists but its silhouette is unverified; modelling is ~30 min).

Soft gaps (a download exists but needs so much rework that modelling is as fast; decide after a visual check of the "maybe" rows):
5. **Photocopier** (only Copier by ykykykk 1.8k tris / MFP printer by nokillnando — both era-uncertain).
6. **Beige PC tower / desktop case** (Old Pc by newarcov is heavy; others PSX).
7. **1970s flat-front veneer chest of drawers** (Old dresser by vladicom08 is a fallback).
8. **Small rolling wooden cabinet on casters** (only metal tool/storage carts exist).
9. **Pleated-shade table lamp** (found lamps have smooth or unknown shades).
10. **Snack-row interior for the vending machine** (shell from AtTheSpeedOf; snack rows = instanced quads).
11. **Office wastebasket** only if the 90s Retro Office Pack bin is unusable.

Everything else has at least one verified **use** candidate (Section 2): CRT monitor + keyboard + mouse, task chair, water cooler, filing cabinet, bookshelf/shelves, sideboard/hutch, Queen Anne-type velvet wingback, plaid sofa (retexture → floral), club armchair (retexture → teal fabric), ladder-back chair, wooden bar stool, two-tier side table, black/wood CRT TVs, glass display cabinet, pallet, desk phone, paper/notepads/folders, wall clock.

## 4. Import / pipeline notes for Unity 6 URP (instancing, LOD, texel density)

- **Single ingest path through Blender 4.3 (headless OK):** import FBX/glTF → apply transforms and real-world scale (check against the Poly Haven `dimensions` in Appendix A; Sketchfab models often use arbitrary units) → decimate to budget → merge to ≤2 materials → export FBX into the project. This also avoids adding a glTF importer package to Unity for Sketchfab GLB files.
- **Tri budgets (Mac laptop GPU, rooms recycled):** small desk props ≤2k, chairs ≤6k, case goods ≤8k, hero items ≤12k; add LOD1 (~40%) for anything >3k; cull at ~3% screen height. Decimation targets for the heavy picks: bar_chair_round_01 14k→6k, Old Hutch 39k→10k, vintage_cabinet_01 61k→15k, Old Dresser 39k→8k, Office chair (inven2000) 29k→8k.
- **Textures:** ship 1K for desk-top props and 2K for furniture (most sources offer 4K–8K; downscale in the importer). Target ≈ 256–512 px/m so props sit with the project's world-projected 2K surfaces without looking sharper or blurrier than the walls.
- **URP Lit mask map:** R = Metallic, G = Occlusion, B = detail mask, A = Smoothness. Poly Haven ARM = (R AO, G Rough, B Metal) → repack to (B, R, 0, 1−G). Use `nor_gl` maps. DirectX-normal sources (e.g. Old Table Lamp V02) need the green channel flipped (repack in Blender during ingest).
- **Batching for recycled rooms and piles:** keep materials shared and SRP-Batcher-compatible; express colour variety with 3–4 material variants (e.g. velvet pink / teal / beige), not MaterialPropertyBlocks (MPBs break the SRP Batcher). The film-pile look is "the same object pasted again", so `FrontRoomsFurniturePile.Build` can draw from a library of ~10–14 meshes with seeded tilt (20–50°), yaw, ±10% scale and deliberate interpenetration — every copy is a shared mesh + shared material, so draw calls stay low. A mirrored copy (negative scale) is cheap in URP but should stay rare, because mixed-handedness objects cannot be batched together.
- **Collision:** 1–3 box colliders per prop (no mesh colliders); for piles, one compound collider of 3–6 boxes around the mass.
- **Glass:** separate transparent submeshes only where the source already splits them (fizyman CRT glass, Poly Haven wall_clock glass maps, display cabinet doors). Opaque dark glass is cheaper for distant copies.
- **Licence hygiene:** keep a `CREDITS.md` + in-game credits entry for every CC-BY mesh (Section 5); record the source URL and download date next to each imported prefab; do not commit raw Royalty-Free (CGTrader/Asset Store/Fab) source files to a public repo.

## 5. CC-BY attribution text (copy into Credits)

Format required by CC BY 4.0 (credit + licence link + changes). Only items marked **use** or **maybe** are listed; delete lines for anything not finally imported.

```
3D models used under Creative Commons Attribution 4.0 (https://creativecommons.org/licenses/by/4.0/).
All were modified for FrontRooms (rescaled, decimated, re-textured/re-materialed, and arranged/duplicated).

Office
- "90s Retro Office Pack" by MadeByYeshe — https://sketchfab.com/3d-models/90s-retro-office-pack-dadca97505214b9481d35e22c48e18df
- "Retro CRT Computer (1990s Desktop PC)" by MadeByYeshe — https://sketchfab.com/3d-models/retro-crt-computer-1990s-desktop-pc-ea9faf1298d24497b916c27a4ea38636
- "CRT Computer Monitor" by fizyman — https://sketchfab.com/3d-models/crt-computer-monitor-f2ff0013f86e4cd0a2aee183a23bdfee
- "Old Pc" by newarcov (gamesinside) — https://sketchfab.com/3d-models/old-pc-4d237a57b18a42d9a56c0d9a7ed0371a
- "Office Chair" by artvolodskikh — https://sketchfab.com/3d-models/office-chair-a7fefb5dde954c84896949246dde5be6
- "Office chair" by AK STUDIO (inven2000) — https://sketchfab.com/3d-models/office-chair-af2f07d06f6349158c1d24d87f5ceb95
- "Office Chair" by Red Fox / nokillnando — https://sketchfab.com/3d-models/office-chair-b228a29fa84544c2be501c295653ffe7
- "Worn Leather Office Chair" by FordVFX — https://sketchfab.com/3d-models/worn-leather-office-chair-003b00c7cdd348888296b85c40275a50
- "Water cooler" by tboiston — https://sketchfab.com/3d-models/water-cooler-4b88c4c4e94c497ca39f831f374e89fc
- "Water Cooler_8MB" by Mehdi Shahsavan (ahmagh2e) — https://sketchfab.com/3d-models/water-cooler-8mb-9aef3e2a5d00481eb2864550bc781e7c
- "Copier" by ykykykk — https://sketchfab.com/3d-models/copier-9eebb4e8b77944159892df30d8b44de5
- "MFP Office Printer" by Red Fox / nokillnando — https://sketchfab.com/3d-models/mfp-office-printer-d55f6fca7c3d45c883bbff770672970d
- "Vending Machine" by AtTheSpeedOf — https://sketchfab.com/3d-models/vending-machine-af792a359ab24c6eaf1e8d98640f05a8
- "Vending Machine" by RackRibs — https://sketchfab.com/3d-models/vending-machine-d62a741a00e04d84bc45b6ccb039cf8a
- "Filing Cabinet - 6MB" by Mehdi Shahsavan (ahmagh2e) — https://sketchfab.com/3d-models/filing-cabinet-6mb-d217a4bbdfa2426eb32ebf3b1007a8c3
- "Filing Cabinet" by matthijs001 — https://sketchfab.com/3d-models/filing-cabinet-adb93fd3a2d84d3ea6f002cd4f1ea7a8
- "Filing Cabinets" by TooManyDemons — https://sketchfab.com/3d-models/filing-cabinets-7ef1ca295ff14af2abcbe0ae0168a241
- "Office Phone" by maxdragonn — https://sketchfab.com/3d-models/office-phone-4176a01b6d0b4d13ad165c0df278a6b5
- "Telephone (Office)" by retroststem10710 — https://sketchfab.com/3d-models/telephone-office-6abe79fcf1a34e2e8b2acca44e266289
- "Papers" by oparaskos — https://sketchfab.com/3d-models/papers-f858428c790f43f8ba9a3aa2996b88b0
- "Document File Folder" by Kami Rapacz (kuroderuta) — https://sketchfab.com/3d-models/document-file-folder-11390179bba7462484d344e2fe22c703
- "[CC0] Newspaper Stack - Ready to Unity HDRP" by karlwirbelwind — https://sketchfab.com/3d-models/c4311a0b918643af97904e10c7a34efc
- "Waste Bin (Animation): Household Props 24" by Daniel O'Neil (doneil) — https://sketchfab.com/3d-models/bb24dc82165346f7a2a64bf2c378504c
- "Wall Clock" by FelipeMSX (felipeprodev) — https://sketchfab.com/3d-models/wall-clock-2e964ac0242e4b1789adfd9549c653dc
- "Old wall clock" by AndreiVNK — https://sketchfab.com/3d-models/old-wall-clock-8e920e8b129842718099a3f772cec024

Furniture piles
- "Old dresser" by Vladyslav Holhanov (vladicom08) — https://sketchfab.com/3d-models/old-dresser-d235f91eee0a484d95283afccc83931d
- "Old Dresser" by slls666 — https://sketchfab.com/3d-models/old-dresser-3ee2cb9b3d9d441ea2e99e6c801ee0b8
- "Sideboard" by tony chopper (choppar) — https://sketchfab.com/3d-models/sideboard-1492a0e14568490bb5c3a20e903622ac
- "Mid Century Teak Sideboard Credenza" by calebkung — https://sketchfab.com/3d-models/mid-century-teak-sideboard-credenza-3028ba44d1f245b886c12eadc934f722
- "Old Hutch" by raeganmaddox — https://sketchfab.com/3d-models/old-hutch-c6d26a7ab43249ceb408a7cde32cb166
- "Wooden Back Bar Cabinet - 4096px²" by mark-peters — https://sketchfab.com/3d-models/a1961b9e5a7043fb9a70b855e947e27f
- "Antique Wing Back Chair lowpoly" by 3DCraftsman (diapant95) — https://sketchfab.com/3d-models/49e21ea4c0bf469387471934dd8bf0fa
- "Classic Victorian Wooden Armchair – Red Velvet" by khalandarthameem97 — https://sketchfab.com/3d-models/045a190f982b40f28b62eb7f503f3948
- "Antique white armchair" by klava88 — https://sketchfab.com/3d-models/148a621c978e4c2fb9ecb6c41b852c1d
- "Old Plaid Sofa" by lena-wachs — https://sketchfab.com/3d-models/old-plaid-sofa-9feaf83034ca4382a099c18cec5aecb3
- "Old Couch" by oisougabo — https://sketchfab.com/3d-models/old-couch-443d9bb95e944afe8ebc4ff489e2886c
- "Old Sofa (FREE)" by RenderRum Filip Rumin — https://sketchfab.com/3d-models/old-sofa-free-90be7242f24749c3a8e0b0a69c616fc1
- "Old Armchair" by MaX3Dd — https://sketchfab.com/3d-models/old-armchair-c20f084f29bd440197a18b4c750f69eb
- "Club Chair" by Saandy — https://sketchfab.com/3d-models/club-chair-da25d54972b04a8e9fa64048c7bcb89c
- "Club chair" by alban — https://sketchfab.com/3d-models/club-chair-0edad579dcd9431e9b91c1fff4b84700
- "Low-poly Ladder Back Chair" by Average3DmodelEnjoyer — https://sketchfab.com/3d-models/low-poly-ladder-back-chair-8a922e83386843028527e796e880d7b0
- "French Ladder Back Chair" by Average3DmodelEnjoyer — https://sketchfab.com/3d-models/french-ladder-back-chair-39a05a5dd79f4d34b42e89b59033dd12
- "Bar Stool" by raeganmaddox — https://sketchfab.com/3d-models/bar-stool-382d65cea3e84bb68b81fd318b10d12c
- "[Free] Drawer Tool Cart (Used)" by Robert Prispilović (rprispil) — https://sketchfab.com/3d-models/da8955e5c8c448e58b013951f48148a0
- "Classic table lamp" by AndreiVNK — https://sketchfab.com/3d-models/classic-table-lamp-1a3292317bb342b4b33431081338a5c3
- "Old Table Lamp V02" by MAR.COS. — https://sketchfab.com/3d-models/old-table-lamp-v02-70659923adc74413ba983516139e222d
- "Floor_lamp" by Uragan27 — https://sketchfab.com/3d-models/floor-lamp-1ea7bb08894243f5b1f1200ee35fb40a
- "Small CRT TV" by rhcreations — https://sketchfab.com/3d-models/small-crt-tv-890c6ce1f6124c02b0cad54db0fdcb52
- "Vintage TV Free" by donnichols — https://sketchfab.com/3d-models/vintage-tv-free-ed92cac6b8d64ea48ea4f91ce9bf350b
- "Soviet Vintage Kitchen Cabinet (PBR Lowpoly)" by Vitalii.Sandula — https://sketchfab.com/3d-models/soviet-vintage-kitchen-cabinet-pbr-lowpoly-154bb3f924b64cdd935f2e196fa8a1e8
- "victorian Cabinet" by lagesnpiet — https://sketchfab.com/3d-models/victorian-cabinet-81291e282b854934a6f1b9f53a900f5f
- "Victorian Display Cabinet" by Jonny Crabb (JonathanCrabb) — https://sketchfab.com/3d-models/victorian-display-cabinet-9b11556cd24f4a16b4e451ade7946e53
- "Wooden Pallet Low-poly" by MaX3Dd — https://sketchfab.com/3d-models/2f1abd705d4f4118b4c8d0b275441505
- "Wooden Pallets" by YadroGames — https://sketchfab.com/3d-models/dba5c00928cd400796d9f6fffdd724b3
- "Wooden Boxes" by MaX3Dd — https://sketchfab.com/3d-models/ddecbe4586594bddb4822a90c0cba222

CC0 (no attribution required; credit as courtesy): Poly Haven (https://polyhaven.com) — Metal Office Desk, Vintage Wooden Drawer 01,
Wooden Bookshelf Worn, Shelf 01, Steel Frame Shelves 01, Worn Metal Rack, Painted Wooden Cabinet / 02, Green Chair 01, Arm Chair 01,
Painted Wooden Chair 01/02, Bar Chair Round 01, Wooden Stool 01, Painted Wooden Stool, Side Table Tall 01, Small Wooden Table 01,
Classic Nightstand 01, Industrial Storage Cart, Tool Cart, Television 01/02, Vintage Cabinet 01, Wooden Military Crate, Office Notepads,
Clipboard, Wall Clock (authors listed in Appendix A). Smithsonian / Cooper Hewitt scans via Sketchfab (CC0).
```

## 6. Sources consulted

Verified this run (fetched 2026-10-02):
- Poly Haven licence https://polyhaven.com/license ; Poly Haven public API https://api.polyhaven.com/assets?t=models , /info/<id>, /files/<id> (Appendix A)
- Sketchfab public API https://api.sketchfab.com/v3/search and /v3/models/<uid> (Appendix B)
- CC BY 4.0 deed https://creativecommons.org/licenses/by/4.0/
- Kenney Furniture Kit https://kenney.nl/assets/furniture-kit
- Quaternius Ultimate House Interior https://quaternius.com/packs/ultimatehomeinterior.html
- ambientCG licence https://docs.ambientcg.com/license/
- OpenGameArt Office Desk and Chair Set https://opengameart.org/content/office-desk-and-chair-set
- Unity Asset Store EULA https://unity.com/legal/as-terms ; 90s Office - HDRP https://assetstore.unity.com/packages/3d/props/interior/90s-office-hdrp-217427
- CGTrader terms https://www.cgtrader.com/pages/terms-and-conditions
- Fab licences doc (Epic) https://dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab
- itch.io: https://3dmodels-sca.itch.io/office-furniture-and-more , https://naivegoblin.itch.io/cc0-backrooms-asset-pack

Blocked / secondary only (UNVERIFIED at source): https://www.fab.com/eula (403), https://www.turbosquid.com/licensing (403), https://free3d.com/terms (403), https://3d.si.edu/ and https://www.si.edu/openaccess (403), https://sketchfab.com/licenses (JS page), BlenderKit licence page (redirected to an unexpected domain, not followed); CG Channel Fab/Megascans article https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/ (search summary); Blender manual BlenderKit page https://docs.blender.org/manual/en/2.93/addons/3d_view/blenderkit.html (search summary).

Project context read: Documentation/OFFICE_LEVEL_FURNITURE_RESEARCH.md (previous Codex pass — it listed only Poly Haven desk/shelves, an OGA set and Kenney; this report adds verified per-item candidates with polycounts, texture sizes, download sizes and licence checks), Verification/lookdev/2_Office_forward.png, scratchpad ref_office_target.png.

## Appendix A — Poly Haven API records fetched 2026-10-02 (raw, verified)

Source: `https://api.polyhaven.com/info/<id>` and `https://api.polyhaven.com/files/<id>` (official Poly Haven public API; page URL = `https://polyhaven.com/a/<id>`). "tris" = the API `polycount` field, which the asset page labels as triangles. Sizes = model + its textures for that resolution.

```
## metal_office_desk | Metal Office Desk | tris/poly=6898 | dims_mm=[2000, 947, 788] | maxres=[8192, 8192] | authors=['Ulan Cabanilla']
   desc: Free 8k metal office desk model with worn grey finish, dual pedestal drawers, chrome handles and tapered legs - sturdy industrial mid-century look.
   sizes: gltf1k=1.6MB gltf2k=5.2MB gltf4k=19.1MB fbx1k=1.9MB fbx2k=6.0MB fbx4k=20.7MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## SchoolDesk_01 | School Desk 01 | tris/poly=4162 | dims_mm=[712, 546, 883] | maxres=[4096, 4096] | authors=['Ethan Place']
   desc: Free 4K model of a classic single-seat school desk with a wood top, gray metal storage shelf and adjustable tubular metal legs with worn finish.
   sizes: gltf1k=0.4MB gltf2k=1.1MB gltf4k=4.1MB fbx1k=1.1MB fbx2k=4.4MB fbx4k=16.1MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## television_02 | Television 02 | tris/poly=2310 | dims_mm=[400, 350, 411] | maxres=[8192, 8192] | authors=['Benny Weimer']
   desc: Free 8K model of a chunky retro CRT TV with scuffed glass, plastic bezel, push buttons, and vented metal speaker panel with sunburst decal and worn edges.
   sizes: gltf1k=1.2MB gltf2k=3.9MB gltf4k=12.6MB fbx1k=1.5MB fbx2k=4.4MB fbx4k=13.5MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## Television_01 | Television 01 | tris/poly=1918 | dims_mm=[600, 471, 457] | maxres=[4096, 4096] | authors=['Gabriel Radić']
   desc: Free 4K model of a vintage tabletop CRT TV with wood casing, scratched metal bezel, worn knobs and speaker grille, smudged glass and realistic weathering.
   sizes: gltf1k=0.5MB gltf2k=1.6MB gltf4k=5.1MB fbx1k=1.5MB fbx2k=4.8MB fbx4k=14.9MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## wall_clock | Wall Clock | tris/poly=3658 | dims_mm=[320, 47, 320] | maxres=[4096, 4096] | authors=['PierreB3D']
   desc: Free 4K model of a modern wall clock with a worn metal bezel, clear glass, bold numerals, gray hour/minute hands, and a slim red second hand on a clean dial.
   sizes: gltf1k=1.6MB gltf2k=4.9MB gltf4k=17.1MB fbx1k=2.7MB fbx2k=7.4MB fbx4k=21.1MB | maps: AO,arm,Diffuse,glass_alpha,glass_arm,glass_rough,Metal,nor_dx,nor_gl,Rough
## metal_trash_can | Metal Trash Can | tris/poly=13960 | dims_mm=[1847, 556, 906] | maxres=[8192, 8192] | authors=['GurJas Studios']
   desc: Free 8K model of a weathered metal trash can with removable lid, ribbed cylindrical body, dents, heavy rust, grime and realistic industrial wear.
   sizes: gltf1k=5.0MB gltf2k=17.5MB gltf4k=63.3MB fbx1k=18.6MB fbx2k=67.6MB fbx4k=239.6MB | maps: Diffuse,nor_dx,rust_arm,Metal,rust_diff,rust_nor_gl,rust_metal,Rough,rust_rough,nor_gl,rust_nor_dx,arm
## industrial_storage_cart | Industrial Storage Cart | tris/poly=18902 | dims_mm=[1603, 1103, 1377] | maxres=[8192, 8192] | authors=['Jule Bielitz']
   desc: Free 8K model of a weathered industrial storage cart with riveted steel frame, two trays, lower double-door cabinet, rolling casters, chipped paint and rust.
   sizes: gltf1k=2.6MB gltf2k=8.1MB gltf4k=28.0MB fbx1k=4.0MB fbx2k=13.3MB fbx4k=45.2MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## tool_cart | Tool Cart | tris/poly=29394 | dims_mm=[1273, 754, 965] | maxres=[8192, 8192] | authors=['Savva Zakharov']
   desc: Free 8K model of a worn green metal tool cart with raised-lip top, lower shelf, two side drawers, riveted frame, chipped paint, rust, and casters.
   sizes: gltf1k=3.2MB gltf2k=9.8MB gltf4k=36.5MB fbx1k=4.6MB fbx2k=15.3MB fbx4k=57.3MB | maps: AO,arm,Diffuse,Displacement,Metal,nor_dx,nor_gl,Rough
## vintage_wooden_drawer_01 | Vintage Wooden Drawer 01 | tris/poly=5184 | dims_mm=[858, 457, 545] | maxres=[8192, 8192] | authors=['James Ray Cock']
   desc: Free 8K model of a vintage wooden six-drawer filing cabinet with worn patina and brass label handles - ideal for period office, study, or furniture scenes.
   sizes: gltf1k=0.8MB gltf2k=2.0MB gltf4k=6.4MB fbx1k=1.8MB fbx2k=5.8MB fbx4k=19.4MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## drawer_cabinet | Drawer Cabinet | tris/poly=26406 | dims_mm=[1141, 488, 1881] | maxres=[4096, 4096] | authors=['Ulan Cabanilla']
   desc: Free 4K modern drawer cabinet featuring warm wood drawers and shelves, slim black metal frame, four horizontal drawers, and open shelving.
   sizes: gltf1k=1.1MB gltf2k=2.1MB gltf4k=5.7MB fbx1k=1.8MB fbx2k=4.9MB fbx4k=16.5MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## painted_wooden_cabinet | Painted Wooden Cabinet | tris/poly=2227 | dims_mm=[1195, 617, 1182] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model: a weathered painted wooden cabinet with chipped farmhouse paint, colonial details, two drawers and double-door storage - rustic, antique character.
   sizes: gltf1k=1.9MB gltf2k=6.8MB gltf4k=25.5MB fbx1k=2.4MB fbx2k=8.9MB fbx4k=32.7MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,AO,Rough
## painted_wooden_cabinet_02 | Painted Wooden Cabinet 02 | tris/poly=966 | dims_mm=[997, 729, 2569] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model of a painted wooden cabinet: rustic, vintage bookcase with worn blue paint, aged wood, shelves, drawer and lower cupboard.
   sizes: gltf1k=1.6MB gltf2k=6.2MB gltf4k=25.2MB fbx1k=2.2MB fbx2k=9.3MB fbx4k=36.5MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,AO,Rough
## painted_wooden_nightstand | Painted Wooden Nightstand | tris/poly=470 | dims_mm=[505, 509, 616] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model of a painted wooden nightstand with worn blue paint, single drawer and tapered legs - vintage, aged bedside table for authentic bedroom scenes.
   sizes: gltf1k=2.2MB gltf2k=8.2MB gltf4k=29.8MB fbx1k=3.1MB fbx2k=11.6MB fbx4k=39.0MB | maps: Diffuse,nor_dx,nor_gl,arm,AO,Rough
## steel_frame_shelves_01 | Steel Frame Shelves 01 | tris/poly=4348 | dims_mm=[1097, 502, 2141] | maxres=[8192, 8192] | authors=['James Ray Cock']
   desc: Free 8K model of a modern industrial steel-frame shelf with five wooden planks, sturdy metal frame and clean lines, ideal for commercial or home interiors.
   sizes: gltf1k=1.6MB gltf2k=5.6MB gltf4k=20.3MB fbx1k=2.3MB fbx2k=8.2MB fbx4k=29.7MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## wooden_bookshelf_worn | Wooden Bookshelf Worn | tris/poly=10106 | dims_mm=[1374, 581, 2063] | maxres=[4096, 4096] | authors=['Ulan Cabanilla']
   desc: Free 4K model of a worn wooden bookshelf with multiple shelves, distressed weathered grain, layered plywood edges, visible nail holes and rustic vintage finish.
   sizes: gltf1k=2.8MB gltf2k=10.3MB gltf4k=42.0MB fbx1k=4.3MB fbx2k=15.5MB fbx4k=59.3MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## worn_metal_rack | Worn Metal Rack | tris/poly=6372 | dims_mm=[915, 600, 1900] | maxres=[8192, 8192] | authors=['Luca B']
   desc: Free 8K model: aged metal rack with green painted frame and four dusty shelves. Realistic rust, chips and dents, with faint labels for a gritty look.
   sizes: gltf1k=2.0MB gltf2k=6.8MB gltf4k=24.6MB fbx1k=3.3MB fbx2k=11.8MB fbx4k=43.7MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## Shelf_01 | Shelf 01 | tris/poly=182 | dims_mm=[1003, 257, 2080] | maxres=[4096, 4096] | authors=['Gabriel Radić']
   desc: Free 4K wooden shelf model with weathered, distressed paint and aged, dirty finish; a simple tall bookcase with multiple shallow display shelves.
   sizes: gltf1k=0.6MB gltf2k=2.5MB gltf4k=9.6MB fbx1k=2.4MB fbx2k=10.0MB fbx4k=34.8MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## wooden_display_shelves_01 | Wooden Display Shelves 01 | tris/poly=3174 | dims_mm=[1078, 372, 1556] | maxres=[8192, 8192] | authors=['James Ray Cock']
   desc: Free 8K model - modern pine display shelf with nine square cubbies and three lower bins; clean, minimalist bookshelf for home or retail displays.
   sizes: gltf1k=0.5MB gltf2k=1.4MB gltf4k=4.8MB fbx1k=1.1MB fbx2k=4.0MB fbx4k=16.5MB | maps: mask01,Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## ArmChair_01 | Arm Chair 01 | tris/poly=5626 | dims_mm=[848, 766, 1065] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free (CC0) vintage Victorian armchair 3D model - varnished carved wood frame, upholstered seat; gothic/classic styling ideal for interiors, period scenes, and renders.
   sizes: gltf1k=0.8MB gltf2k=2.8MB gltf4k=10.8MB fbx1k=2.6MB fbx2k=10.2MB fbx4k=37.7MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## GreenChair_01 | Green Chair 01 | tris/poly=4213 | dims_mm=[673, 664, 1059] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model of a vintage Gothic wooden armchair with carved decorative details, green fabric upholstery and elegant curved legs; ideal for period interiors.
   sizes: gltf1k=0.6MB gltf2k=2.0MB gltf4k=7.7MB fbx1k=1.9MB fbx2k=6.6MB fbx4k=24.0MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## Sofa_01 | Sofa 01 | tris/poly=4101 | dims_mm=[1571, 658, 797] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K vintage Victorian wooden sofa - decorative gothic-style upholstered couch with carved frame, elegant seating prop for period interiors.
   sizes: gltf1k=0.5MB gltf2k=2.2MB gltf4k=10.0MB fbx1k=1.9MB fbx2k=8.1MB fbx4k=32.1MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## mid_century_lounge_chair | Mid Century Lounge Chair | tris/poly=6148 | dims_mm=[1009, 1190, 1169] | maxres=[8192, 8192] | authors=['Kuutti Siitonen']
   desc: Free 8K mid-century lounge chair: wooden shell, worn brown leather cushions, swivel recliner base - stylish, comfy retro seating for modern interiors.
   sizes: gltf1k=2.1MB gltf2k=7.7MB gltf4k=31.6MB fbx1k=3.1MB fbx2k=11.3MB fbx4k=46.4MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## painted_wooden_chair_01 | Painted Wooden Chair 01 | tris/poly=724 | dims_mm=[432, 540, 956] | maxres=[8192, 8192] | authors=['Kuutti Siitonen']
   desc: Free 8K painted wooden chair, distressed white farmhouse piece with slatted seat, decorative back splat, square legs and simple stretchers.
   sizes: gltf1k=0.5MB gltf2k=1.5MB gltf4k=5.1MB fbx1k=1.3MB fbx2k=4.8MB fbx4k=17.4MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,AO,Rough
## painted_wooden_chair_02 | Painted Wooden Chair 02 | tris/poly=1246 | dims_mm=[639, 662, 1264] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model of a painted wooden dining chair with distressed vintage farmhouse charm, worn paint and realistic wood grain - ideal for antique interiors.
   sizes: gltf1k=2.4MB gltf2k=9.4MB gltf4k=35.8MB fbx1k=3.5MB fbx2k=13.6MB fbx4k=50.1MB | maps: Diffuse,nor_dx,nor_gl,arm,AO,Rough
## painted_wooden_stool | Painted Wooden Stool | tris/poly=676 | dims_mm=[385, 406, 579] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model - painted wooden stool with chipped paint, worn edges and rustic farmhouse charm; simple antique carpentry.
   sizes: gltf1k=1.9MB gltf2k=6.7MB gltf4k=25.8MB fbx1k=2.3MB fbx2k=7.8MB fbx4k=29.4MB | maps: Diffuse,emissive,nor_dx,Metal,AO,Rough,nor_gl,Alpha,arm
## bar_chair_round_01 | Bar Chair Round 01 | tris/poly=14373 | dims_mm=[483, 486, 751] | maxres=[4096, 4096] | authors=['Dairon Sanchez']
   desc: Free 4K model, vintage wooden bar stool with round seat, carved beaded trim, hexagonal legs, circular footrest and worn finish.
   sizes: gltf1k=2.8MB gltf2k=7.2MB gltf4k=19.7MB fbx1k=3.0MB fbx2k=8.3MB fbx4k=22.7MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,AO,Rough
## wooden_stool_01 | Wooden Stool 01 | tris/poly=10946 | dims_mm=[425, 442, 437] | maxres=[8192, 8192] | authors=['Kuutti Siitonen']
   desc: Free 8K model of an old, worn wooden stool with a cracked round seat, turned legs and weathered grain, dusty finish and workshop-aged patina.
   sizes: gltf1k=1.0MB gltf2k=3.2MB gltf4k=11.7MB fbx1k=2.8MB fbx2k=10.4MB fbx4k=40.2MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,AO,Rough
## side_table_tall_01 | Side Table Tall 01 | tris/poly=6408 | dims_mm=[384, 384, 761] | maxres=[8192, 8192] | authors=['James Ray Cock']
   desc: Free 8K model of a tall vintage wooden side table with slender curved legs, lower shelf and brass medallions - worn patina perfect for antique interiors.
   sizes: gltf1k=0.6MB gltf2k=1.4MB gltf4k=4.5MB fbx1k=1.2MB fbx2k=3.6MB fbx4k=13.0MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## side_table_01 | Side Table 01 | tris/poly=2756 | dims_mm=[550, 450, 551] | maxres=[8192, 8192] | authors=['James Ray Cock']
   desc: Free 8K model of a minimalist wooden side table with two shelves, clean lines and warm oak finish - perfect for modern living room or bedroom interiors.
   sizes: gltf1k=0.5MB gltf2k=1.6MB gltf4k=5.8MB fbx1k=1.0MB fbx2k=3.3MB fbx4k=11.9MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## small_wooden_table_01 | Small Wooden Table 01 | tris/poly=3410 | dims_mm=[916, 440, 533] | maxres=[4096, 4096] | authors=['Ulan Cabanilla']
   desc: Free 4K model of a small vintage wooden table with rounded legs, double stretchers and a worn warm-brown finish, showing subtle scratches and aged varnish.
   sizes: gltf1k=0.4MB gltf2k=1.4MB gltf4k=5.5MB fbx1k=0.8MB fbx2k=3.1MB fbx4k=14.1MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough,AO
## ClassicNightstand_01 | Classic Nightstand 01 | tris/poly=2002 | dims_mm=[568, 424, 700] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model of a vintage Victorian Gothic wooden nightstand - ornate carved details, cabriole legs and open shelf; perfect decorative table/furniture prop.
   sizes: gltf1k=0.4MB gltf2k=1.4MB gltf4k=5.1MB fbx1k=1.5MB fbx2k=5.3MB fbx4k=18.5MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## vintage_cabinet_01 | Vintage Cabinet 01 | tris/poly=61096 | dims_mm=[2022, 670, 2235] | maxres=[8192, 8192] | authors=['Rico Cilliers']
   desc: Free 8K model: varnished dark-wood vintage cabinet with carved detailing, glass-front upper doors, paneled lower cupboards and brass knobs.
   sizes: gltf1k=2.9MB gltf2k=5.0MB gltf4k=13.0MB fbx1k=21.1MB fbx2k=72.9MB fbx4k=251.2MB | maps: a_ao,a_metal,a_alpha,b_rough,b_diff,b_ao,a_nor_dx,a_rough,a_diff,b_arm,b_nor_dx,b_nor_gl,a_nor_gl,a_arm
## GothicCommode_01 | Gothic Commode 01 | tris/poly=3897 | dims_mm=[1201, 581, 1212] | maxres=[4096, 4096] | authors=['Kirill Sannikov']
   desc: Free 4K model: vintage Gothic wooden commode with carved arches, three drawers and decorative trim.
   sizes: gltf1k=0.6MB gltf2k=1.7MB gltf4k=5.2MB fbx1k=1.4MB fbx2k=4.6MB fbx4k=14.9MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,Rough
## wooden_crate_01 | Wooden Crate 01 | tris/poly=6576 | dims_mm=[825, 409, 350] | maxres=[8192, 8192] | authors=['James Ray Cock']
   desc: Free 8K model of a vintage wooden crate - weathered colonial chest with rope handles, metal rivets and latch; ideal as maritime, farmhouse or prop container.
   sizes: gltf1k=2.3MB gltf2k=8.3MB gltf4k=31.7MB fbx1k=3.0MB fbx2k=11.6MB fbx4k=45.7MB | maps: Diffuse,mask01,nor_dx,nor_gl,Metal,arm,AO,Rough
## wooden_crate_02 | Wooden Crate 02 | tris/poly=5176 | dims_mm=[1166, 529, 464] | maxres=[8192, 8192] | authors=['James Ray Cock', 'Jurita Burger']
   desc: Free 8K model of a vintage wooden crate with worn planks, dovetail joins, brass corner plates and rope handles - ideal for maritime, colonial or farmhouse props.
   sizes: gltf1k=2.2MB gltf2k=8.2MB gltf4k=31.3MB fbx1k=3.3MB fbx2k=12.7MB fbx4k=49.8MB | maps: Diffuse,nor_dx,nor_gl,Mask,Metal,arm,AO,Rough
## wooden_military_crate | Wooden Military Crate | tris/poly=22986 | dims_mm=[1242, 520, 465] | maxres=[4096, 4096] | authors=['Prabhjinder Singh']
   desc: Free 4K model of a rugged wooden military crate with hinged lid, metal straps and latches, side handles, and stenciled, weathered paint and scratches.
   sizes: gltf1k=3.0MB gltf2k=10.2MB gltf4k=41.1MB fbx1k=4.1MB fbx2k=14.5MB fbx4k=58.2MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## office_notepads | Office Notepads | tris/poly=666 | dims_mm=[1103, 660, 22] | maxres=[4096, 4096] | authors=['Ulan Cabanilla']
   desc: Free 4K model of assorted office notepads: blank sheets, lined legal pads with red glue, index cards, and sticky notes. Realistic paper grain and crisp edges.
   sizes: gltf1k=1.3MB gltf2k=5.7MB gltf4k=25.4MB fbx1k=1.8MB fbx2k=8.6MB fbx4k=39.7MB | maps: arm,Diffuse,nor_dx,nor_gl,Rough
## binder_notebook | Binder Notebook | tris/poly=18077 | dims_mm=[584, 200, 25] | maxres=[8192, 8192] | authors=['DaDrood']
   desc: Free 8K leather binder notebook with worn patina, brass rings, stitched pockets, snap strap and pen, embossed logo, realistic paper stack and metal details.
   sizes: gltf1k=1.9MB gltf2k=5.1MB gltf4k=14.2MB fbx1k=2.3MB fbx2k=6.5MB fbx4k=16.6MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## clipboard | Clipboard | tris/poly=6176 | dims_mm=[229, 337, 42] | maxres=[8192, 8192] | authors=['ProgrammerOnCoffee']
   desc: Free 8K model of a worn masonite clipboard with a shiny chrome clip, engraved logo, rounded corners, scuffs and edge wear, showing a lived-in look.
   sizes: gltf1k=1.8MB gltf2k=6.8MB gltf4k=28.3MB fbx1k=2.4MB fbx2k=9.8MB fbx4k=40.8MB | maps: AO,arm,Diffuse,Metal,nor_dx,nor_gl,Rough
## cardboard_box_01 | Cardboard Box 01 | tris/poly=16952 | dims_mm=[387, 516, 342] | maxres=[4096, 4096] | authors=['Rahul Chaudhary']
   desc: Free 4K model of a worn, creased cardboard box with torn flaps, taped seams and a weathered strap - aged, dented paper texture and realistic damage.
   sizes: gltf1k=2.2MB gltf2k=6.7MB gltf4k=22.8MB fbx1k=3.6MB fbx2k=11.2MB fbx4k=37.0MB | maps: Diffuse,nor_dx,nor_gl,arm,AO,Rough
## plastic_bottle_gallon | Plastic Bottle Gallon | tris/poly=13728 | dims_mm=[166, 126, 274] | maxres=[8192, 8192] | authors=['Rahul Chaudhary']
   desc: Free 8K model of a weathered off-white plastic gallon jug with integrated handle, scuffs, dirt and rusty stains, scratched, dented and worn neck threads.
   sizes: gltf1k=1.4MB gltf2k=4.4MB gltf4k=16.3MB fbx1k=2.4MB fbx2k=8.8MB fbx4k=32.2MB | maps: Diffuse,nor_dx,nor_gl,Metal,arm,AO,Rough
## stationery_supplies | Stationery Supplies | tris/poly=4412 | dims_mm=[302, 84, 164] | maxres=[4096, 4096] | authors=['Mateusz Sadek']
   desc: Free 4k model of assorted stationery: scuffed pens, colored and graphite pencils with worn paint, pink eraser and engraved metal cup, realistic and finely detailed props.
   sizes: gltf1k=2.0MB gltf2k=7.3MB gltf4k=28.9MB fbx1k=2.8MB fbx2k=9.8MB fbx4k=37.9MB | maps: AO,arm,Diffuse,Displacement,Metal,nor_dx,nor_gl,Rough
```

## Appendix B — Sketchfab search API results fetched 2026-10-02 (raw, verified listing; downloadable=true; CC-BY unless noted)

Source: `https://api.sketchfab.com/v3/search?type=models&q=<q>&downloadable=true&license=by|cc0&sort_by=-likeCount` (official public API). Columns: name | uid (page = https://sketchfab.com/3d-models/<uid>) | author | licence | faces | GLB archive size / texture count / max texture px | likes.

```
## q="beige computer" lic=by n=16
  CT Derived Human Skeleton | 7235c83248574ce986dd9e8b35159afa | terrielsimmons | CC Attribution | faces=568776 | glb=16.3MB tex=0 max=0 | likes=103
  Retro Monitor & PC Tower | PSX Style | 36b9d8a6018c493282916df39e149365 | 410prod | CC Attribution | faces=126 | glb=0.0MB tex=1 max=256 | likes=98
  Retro PC With Pixel Terrarium Screen | 24c533e85ff64307bd9a4485db129223 | s8819296 | CC Attribution | faces=1000663 | glb=52.8MB tex=3 max=2048 | likes=67
  Low Poly Computer with Devices | 721d8c3c3c9a493bb8f7da6d9ac197d1 | vadzaecc | CC Attribution | faces=1742 | glb=0.2MB tex=1 max=1024 | likes=57
  LP old computer low poly cartoon | 6afe35f1a1274af5861d34409bd392b0 | Quantum-Bit | CC Attribution | faces=364 | glb=0.0MB tex=1 max=32 | likes=57
  YPM ANT.057502 | d88abc10c94b4c0dbe98f3de034c4dcd | yalepeabodymuseum | CC Attribution | faces=1800000 | glb=87.6MB tex=1 max=8192 | likes=12
  Jesse-D-SPRUE-FullColorLineup.png | 40cef68e2d924936a151a8615b35d149 | daysjesse | CC Attribution | faces=37788 | glb=1.3MB tex=0 max=0 | likes=6
  Software Engineer S.P.R.U.E Set | 45be9ce8fc8d45dfaa726a04c833e11f | daysjesse | CC Attribution | faces=30600 | glb=0.9MB tex=0 max=0 | likes=5
  Vintage Macintosh Moniter | 981813d75bc24f0eb7099751d383e72f | josh3Dmodel | CC Attribution | faces=1597 | glb=0.2MB tex=1 max=2048 | likes=5
  Modern Multi-Screen Workstation Design | fcac8f29abea4e4a85a24ed0149a868a | miftaholnafi810 | CC Attribution | faces=3954 | glb=0.2MB tex=0 max=0 | likes=4
## q="crt monitor" lic=by n=24
  90s Retro Office Pack | dadca97505214b9481d35e22c48e18df | MadeByYeshe | CC Attribution | faces=44155 | glb=56.5MB tex=160 max=4096 | likes=1116
  Sony PVM-1341 || Sony Playstation | 5f80311f1a4646ef9673f20ee6dc6245 | dark_igorek | CC Attribution | faces=240414 | glb=116.7MB tex=25 max=4096 | likes=824
  Medical Console | 89065e109790417191467cfececf2c7c | OliverTriplett | CC Attribution | faces=3312 | glb=7.1MB tex=4 max=2048 | likes=556
  Retro CRT TV | 6bc462b233ce4c78904dfcadf5123e29 | ashabbugaev12 | CC Attribution | faces=1708 | glb=16.5MB tex=6 max=2048 | likes=425
  office is old abandoned FREE | 3977a108b2304b85a698f3dda1777015 | dasy444 | CC Attribution | faces=59782 | glb=42.4MB tex=23 max=4096 | likes=313
  CRT Computer Monitor | f2ff0013f86e4cd0a2aee183a23bdfee | fizyman | CC Attribution | faces=3742 | glb=47.4MB tex=5 max=4096 | likes=265
  Retro CRT Computer (1990s Desktop PC) | ea9faf1298d24497b916c27a4ea38636 | MadeByYeshe | CC Attribution | faces=2416 | glb=2.6MB tex=20 max=1024 | likes=256
  PSX CRT TV | 14c4034011ff4faebd99de03c7ab1635 | Tomitos_ | CC Attribution | faces=84 | glb=0.1MB tex=1 max=256 | likes=235
  Low Poly Computer Desk | 646ed84ecd9d40089c31d94f79334ca5 | Nyangire | CC Attribution | faces=5486 | glb=0.5MB tex=2 max=128 | likes=234
  CRT Monitor | 140738b1308446679c763a3d3d86a873 | OliverTriplett | CC Attribution | faces=2347 | glb=7.2MB tex=4 max=2048 | likes=195
## q="keyboard mouse retro" lic=by n=15
  90s Retro Office Pack | dadca97505214b9481d35e22c48e18df | MadeByYeshe | CC Attribution | faces=44155 | glb=56.5MB tex=160 max=4096 | likes=1116
  PSX Retro Computer | 7e7f8a9dfa1f4b34abde94bb02b9f46c | Tomitos_ | CC Attribution | faces=194 | glb=0.2MB tex=4 max=256 | likes=486
  Retro CRT Computer (1990s Desktop PC) | ea9faf1298d24497b916c27a4ea38636 | MadeByYeshe | CC Attribution | faces=2416 | glb=2.6MB tex=20 max=1024 | likes=256
  old computer | 8183647717084f008969c22b7fcd1b8a | ivsn | CC Attribution | faces=102968 | glb=15.9MB tex=12 max=2048 | likes=60
  Retro Computer | 78bedd5bc4aa422296181fc28042426b | FishyBusiness | CC Attribution | faces=60 | glb=0.0MB tex=10 max=16 | likes=56
  Retro Computer With Mouse And Keyboard | b0a0b822b3be444ab751414c657658c8 | jampakdd | CC Attribution | faces=1540 | glb=0.2MB tex=0 max=0 | likes=41
  Free Voxel Retro Computer | Ретро Компьютер | d93b923c8e284281891203bf4362e83c | crusadjor | CC Attribution | faces=21836 | glb=0.9MB tex=0 max=0 | likes=30
  PSX - Smartphone | 100758c720a74ae2ab5dbf86443f8be8 | Kasugay | CC Attribution | faces=12 | glb=0.0MB tex=1 max=256 | likes=26
  Desk Mess | 074deab6e0e04cd696a0c9143b850dd6 | renviros | CC Attribution | faces=17659 | glb=55.8MB tex=31 max=2048 | likes=26
  Terminal-styled Computer (Dumb Terminal) | ccfb7a137ecd451f8fd5760fa463976a | public_access | CC Attribution | faces=58973 | glb=4.4MB tex=8 max=1024 | likes=7
## q="office chair" lic=by n=24
  Office - Assets | 16c1a779bb0a4055a26367741d39e059 | EvanPetrov | CC Attribution | faces=30368 | glb=133.2MB tex=42 max=4096 | likes=2142
  90s Retro Office Pack | dadca97505214b9481d35e22c48e18df | MadeByYeshe | CC Attribution | faces=44155 | glb=56.5MB tex=160 max=4096 | likes=1116
  Minimalistic Modern Office | 5540183da1c7452f810f8de33734879a | dylanheyes | CC Attribution | faces=133674 | glb=39.2MB tex=8 max=4096 | likes=984
  Living room - Furniture, Chairs, Sofa and Props | 567712976c5148099b91abe5c580ba9e | marinojofre99 | CC Attribution | faces=1005535 | glb=325.8MB tex=8 max=8192 | likes=869
  chesterfield-sofa | 66ba4225efaa4de59d9a9b7086363199 | leaguestudio | CC Attribution | faces=146524 | glb=24.5MB tex=6 max=4096 | likes=818
  Victorian Chairs | a12b3c2a6f9c4b99ad618242e86e12fe | mtcollings | CC Attribution | faces=19772 | glb=67.1MB tex=4 max=4096 | likes=700
  Office Chair Modern | 675f34f7304e4d92812a41e9750539aa | thethieme | CC Attribution | faces=1234 | glb=7.3MB tex=3 max=2048 | likes=627
  Small Office | 393a8fec31bf41a99a49a57bbcf02ac8 | dylanheyes | CC Attribution | faces=101699 | glb=32.9MB tex=23 max=2048 | likes=611
  Art Drafting Desk | e57096564d9c411dabb3184bb3fef325 | Raffey | CC Attribution | faces=52194 | glb=43.5MB tex=19 max=2048 | likes=509
  Modular office Interior assets (Post Apoc) | 5150e7fcc98b44e1bc087e9ba206135a | JordiKruk | CC Attribution | faces=5554 | glb=4.6MB tex=1 max=4096 | likes=493
## q="water cooler" lic=by n=24
  90s Retro Office Pack | dadca97505214b9481d35e22c48e18df | MadeByYeshe | CC Attribution | faces=44155 | glb=56.5MB tex=160 max=4096 | likes=1116
  Water cooler | 4b88c4c4e94c497ca39f831f374e89fc | tboiston | CC Attribution | faces=2188 | glb=16.3MB tex=4 max=4096 | likes=414
  Water Cooler_12_MB | fea47b4738774f238b2914b8852c7bb1 | ahmagh2e | CC Attribution | faces=11314 | glb=10.1MB tex=6 max=2048 | likes=178
  Water Cooler_8MB | 9aef3e2a5d00481eb2864550bc781e7c | ahmagh2e | CC Attribution | faces=12886 | glb=6.5MB tex=4 max=2048 | likes=132
  Northern Stone Crab | f95f438fdce44232a3c147e21686dd18 | wattinstitution | CC Attribution | faces=1803880 | glb=55.8MB tex=0 max=0 | likes=52
  Water Dispenser | 457cd4e59d634c4cafc67d32b8212032 | dmytronikonov | CC Attribution | faces=15189 | glb=41.9MB tex=6 max=4096 | likes=43
  liquid-cooler | 1c60872e45144239aadb4e188c43bce3 | snrnsrk5 | CC Attribution | faces=7768 | glb=0.4MB tex=1 max=256 | likes=37
  Orient Air Cooler | b24f633dee1a42289ae3d09a7a406b5c | yadavashish3210 | CC Attribution | faces=43192 | glb=7.2MB tex=7 max=4096 | likes=36
  GAME READY BACKROOMS ASSET PACK VOL. 2 | 4d0ee1ba795140b69288819764db10e8 | oxygen3d | CC Attribution | faces=27206 | glb=4.5MB tex=1 max=2048 | likes=23
  Office Props Lowpoly | 36b97aeac9fc46499262c036eea265f3 | lakawaka | CC Attribution | faces=37190 | glb=2.4MB tex=1 max=512 | likes=23
## q="photocopier" lic=by n=3
  IMPRIMANTE | 6722b414a72b4aa4a275135bd7f3a3cd | nando59 | CC Attribution | faces=132212 | glb=5.2MB tex=0 max=0 | likes=14
  witch_stuff | 7fbfb7ff766145b58dc50ce75cdccc63 | aleksandarpopovic2 | CC Attribution | faces=58728 | glb=3.1MB tex=0 max=0 | likes=3
  Old Copier | 3d9bd04e9e8e497c9bb51d5d326f1cbe | sookendestroy1 | CC Attribution | faces=1646 | glb=0.1MB tex=0 max=0 | likes=0
## q="snack vending machine" lic=by n=24
  Realistic Vending Machine | 3D Model | f32a7ba4f73448a3837fd37d90d9b130 | nandana.sethu.10 | CC Attribution | faces=1559324 | glb=116.9MB tex=103 max=512 | likes=303
  Vending Machine | d62a741a00e04d84bc45b6ccb039cf8a | RackRibs | CC Attribution | faces=1626 | glb=1.7MB tex=1 max=1024 | likes=286
  Poppy Playtime Chapter 3: Snack Machine | 492f8601f9c54c839cbed430ee6cd8cf | Unkown_ | CC Attribution | faces=6474 | glb=13.9MB tex=4 max=2048 | likes=129
  Japanese Inspired Vending Machines | 2b3638c2c2a64633a3e11d473152c909 | spookyghostboo | CC Attribution | faces=14006 | glb=5.6MB tex=6 max=2048 | likes=100
  PSX - Vending Machine | aff31f282155471d8222287596c7ac59 | Kasugay | CC Attribution | faces=92 | glb=0.3MB tex=2 max=512 | likes=99
  Vending Machine 2 LOWPOLY | 7fa48e74cde4415892b4ab87006abb8c | evan4129 | CC Attribution | faces=168 | glb=9.5MB tex=4 max=2048 | likes=54
  Vending Machine | af792a359ab24c6eaf1e8d98640f05a8 | AtTheSpeedOf | CC Attribution | faces=13326 | glb=7.3MB tex=7 max=2048 | likes=49
  Vending Machine 1 LOWPOLY | 18a9a263bab64de08879f7f9543966c3 | evan4129 | CC Attribution | faces=156 | glb=8.8MB tex=4 max=2048 | likes=36
  Turtle Tears Vending Machine | 991be573153243818c9e6c977f022174 | evan4129 | CC Attribution | faces=2208 | glb=16.1MB tex=5 max=4096 | likes=35
  Vending Machine | d248162f0c9a465a8d2cdf868ea7aa12 | mkhawasawala.21 | CC Attribution | faces=505738 | glb=60.2MB tex=38 max=2048 | likes=32
## q="filing cabinet metal" lic=by n=9
  Small Kitchen with Oven | e783d6d64f8c453ab534bdde715b210d | AleixoAlonso | CC Attribution | faces=20924 | glb=36.3MB tex=5 max=4096 | likes=467
  Office workspace | 2cd8b1fa627245e7bf319347c00c4cd7 | Juty | CC Attribution | faces=848028 | glb=27.5MB tex=0 max=0 | likes=43
  Filing Cabinet | adb93fd3a2d84d3ea6f002cd4f1ea7a8 | matthijs001 | CC Attribution | faces=1072 | glb=72.3MB tex=6 max=4096 | likes=30
  Metal Cabinets [Low Polygon] | ac38bdc890714640a29657e5e1386208 | jamyzgenius | CC Attribution | faces=1400 | glb=3.0MB tex=3 max=2048 | likes=19
  Rusty Metal Cabinet - 3D scan Quixel Megascans | 9196fe561ed64777ba4f9ca3350c87eb | Guay0 | CC Attribution | faces=22978 | glb=12.4MB tex=3 max=2048 | likes=8
  Sideboard Design | aa85db9b82054ddfb6aaf63e6fe221b1 | home3dmodel | CC Attribution | faces=21937 | glb=6.1MB tex=10 max=2048 | likes=6
  Cherry Wood Bench | ed1caa52e8c94368acbbc5f14602106a | nickvarts | CC Attribution | faces=29696 | glb=24.7MB tex=6 max=4096 | likes=6
  Carbon dioxide fire extinguisher - 灭火器 CO2 | 061870daa4c14a3382e3b0ea11582e5c | mrdt.club | CC Attribution | faces=6488 | glb=0.3MB tex=0 max=0 | likes=5
## q="office cubicle partition" lic=by n=2
  Room Partition Model 5175-5 | 0f244a4985134d38ae4dec414499ccee | iDivide | CC Attribution | faces=12066 | glb=0.9MB tex=5 max=512 | likes=18
  Name Tag Furniture | 577e799a81ee4722902eeeac4485cb90 | afroartstudios | CC Attribution | faces=6456 | glb=3.3MB tex=3 max=1024 | likes=6
## q="office desk 90s" lic=by n=6
  90s Retro Office Pack | dadca97505214b9481d35e22c48e18df | MadeByYeshe | CC Attribution | faces=44155 | glb=56.5MB tex=160 max=4096 | likes=1116
  Low Poly Computer Desk | 646ed84ecd9d40089c31d94f79334ca5 | Nyangire | CC Attribution | faces=5486 | glb=0.5MB tex=2 max=128 | likes=234
  Scandi Modern Office Desk PSX Style | f6915f34677546dd8dce914f32d892e8 | adamsite | CC Attribution | faces=72 | glb=0.1MB tex=1 max=256 | likes=33
  90s Stylized Office | 6dce10aa9372427daa06e3bd730cb8b3 | ilyagum | CC Attribution | faces=3234 | glb=0.3MB tex=6 max=256 | likes=23
  Old Pc | 4d237a57b18a42d9a56c0d9a7ed0371a | newarcov | CC Attribution | faces=11692 | glb=34.3MB tex=3 max=4096 | likes=6
  Retro Cigarette Pack | b4ff052db8d14f448d86a068418cf9ae | nadedasel | CC Attribution | faces=26 | glb=0.1MB tex=1 max=512 | likes=3
## q="dresser vintage" lic=by n=13
  Simple Drape Victorian Dress Test | 0e2f55763d8244cf93ecdeffb5976532 | persnip | CC Attribution | faces=25626 | glb=0.7MB tex=0 max=0 | likes=79
  Old Dresser | 3ee2cb9b3d9d441ea2e99e6c801ee0b8 | slls666 | CC Attribution | faces=39383 | glb=42.0MB tex=3 max=4096 | likes=49
  Shoe Cabinet | d4205cbd80f4459c80a0257b97ab95a2 | 3dwalkabout | CC Attribution | faces=14930 | glb=2.3MB tex=1 max=2048 | likes=40
  Vintage ABBA 8-Track Tape (low-poly) | 70d23233d5c64f948d047923db1f867a | TampaJoey | CC Attribution | faces=1790 | glb=1.2MB tex=3 max=1024 | likes=39
  room with TV table chair | Detailed draft XYZ | bd4f92fab2f248478b9fe0621a2fe06e | milapixia | CC Attribution | faces=132232 | glb=5.9MB tex=0 max=0 | likes=30
  Bettina Blaze, retro varsity comic sweetheart | 1d4f2f3edfc44c2ca686a197a45b89ab | pinckneyb | CC Attribution | faces=204623 | glb=17.8MB tex=1 max=4096 | likes=24
  Art Deco Dresser With Mirror ( Raw Scan ) | 81fdeca9aa0c4cbe9908f62ebf7f42a7 | JordanF | CC Attribution | faces=825724 | glb=73.4MB tex=3 max=8192 | likes=11
  Emma - Little Classic Movie Star | d1f9128ced034b0a9dbbd8e90718e154 | wanderingnote_jp | CC Attribution | faces=273709 | glb=27.9MB tex=4 max=2048 | likes=7
## q="hutch cabinet" lic=by n=6
  Wooden Back Bar Cabinet - 4096px² | a1961b9e5a7043fb9a70b855e947e27f | mark-peters | CC Attribution | faces=23213 | glb=53.6MB tex=3 max=4096 | likes=170
  Cabinet Storage | 3597a7a470ac4f81b1b362eea66f4d6f | jimbogies | CC Attribution | faces=19750 | glb=13.0MB tex=6 max=2048 | likes=62
  Old Hutch | c6d26a7ab43249ceb408a7cde32cb166 | raeganmaddox | CC Attribution | faces=38876 | glb=46.0MB tex=14 max=2048 | likes=43
  Horror Props | 7783c4f885324f21807842fe5b0db2be | lamills | CC Attribution | faces=22714 | glb=30.5MB tex=31 max=2048 | likes=34
  Antique Oak Cabinet | 9d56172d033c40d4a83fcdeafc5b749e | Azura_SQ | CC Attribution | faces=950831 | glb=59.9MB tex=3 max=2048 | likes=4
  Dining Room Hutch | 15090a6f9a314ebfaa9455e5e4b3f0db | shirlanne | CC Attribution | faces=2296 | glb=0.3MB tex=3 max=512 | likes=2
## q="cabriole leg armchair" lic=by n=3
  Flor de Calavera Armchair - chair | 494585b8e4534354979cc780cdb08248 | CMBC | CC Attribution | faces=601265 | glb=23.9MB tex=1 max=2048 | likes=5
  Silla del Recuerdo - chair | c83477189ef94bc5a59ea915bbb51eb7 | CMBC | CC Attribution | faces=560926 | glb=20.4MB tex=1 max=2048 | likes=3
  Venetian Gold Armchair by Modenese | 55210dd9da5e4f7bb3e21199cd7e3f09 | modeneseinteriors | CC Attribution | faces=333264 | glb=10.6MB tex=0 max=0 | likes=2
## q="plaid sofa" lic=by n=2
  Old Plaid Sofa | 9feaf83034ca4382a099c18cec5aecb3 | lena-wachs | CC Attribution | faces=8668 | glb=42.8MB tex=6 max=4096 | likes=199
  Мodern sofa | dfed5023ec614799a68d392a6a4199ed | avilov | CC Attribution | faces=100657 | glb=6.1MB tex=2 max=2048 | likes=13
## q="old sofa" lic=by n=24
  Futuristic Room | a60be41028b049b6a488f5c6effcb6f8 | denis_cliofas | CC Attribution | faces=221366 | glb=587.4MB tex=83 max=4096 | likes=2227
  Old Sofa | 3fe7ed15c42e48b8820792e8cef64f93 | glezova | CC Attribution | faces=6894 | glb=282.6MB tex=21 max=4096 | likes=847
  Old Sofa (FREE) | 90be7242f24749c3a8e0b0a69c616fc1 | RendeRum | CC Attribution | faces=57306 | glb=44.5MB tex=5 max=4096 | likes=654
  Modern apartment interior | 400c9069181a4342a7142433dfa3466e | Katydid. | CC Attribution | faces=60084 | glb=10.1MB tex=46 max=1024 | likes=583
  Luxurious royal sofa with pillows, two seats. | a54b2ac109d146fb80cfc37c9da26cfb | klava88 | CC Attribution | faces=39988 | glb=3.1MB tex=1 max=2048 | likes=532
  Dormitory - Assets | 6f8d7eda19364c79aeeedbb65d6073d1 | EvanPetrov | CC Attribution | faces=22379 | glb=64.9MB tex=15 max=4096 | likes=528
  Old Sofa's | 64c9a2ecb01f46c2bd39133955d753b5 | Badboy17Aiden | CC Attribution | faces=1816 | glb=13.3MB tex=3 max=2048 | likes=502
  Old Couch | 443d9bb95e944afe8ebc4ff489e2886c | oisougabo | CC Attribution | faces=7964 | glb=13.7MB tex=3 max=2048 | likes=479
## q="armchair fabric vintage" lic=by n=11
  Swizza | d47d0ca538e44295af3f0244474d7e67 | topfrank2013 | CC Attribution | faces=73092 | glb=106.5MB tex=6 max=8192 | likes=128
  Sofa 4 | 3DX | ee680e0210694e0496c69c78b9aba494 | snowvy | CC Attribution | faces=5936 | glb=0.5MB tex=0 max=0 | likes=40
  Sofa 3 | 3DX | 1d09094be7fc4e809841992d8801f217 | snowvy | CC Attribution | faces=131056 | glb=4.0MB tex=2 max=1024 | likes=32
  Vintage Wingback Armchair | d606a3eb868d4122855bc7a82d2889a9 | pranavranjan2212 | CC Attribution | faces=102937 | glb=44.2MB tex=3 max=4096 | likes=28
  Sofa 2 | 3DX | 2e625caf1f8a444aa03b763859759d83 | snowvy | CC Attribution | faces=204928 | glb=21.6MB tex=2 max=1024 | likes=22
  Sofa 1 | 3DX | 6e0045e2b6a142658d561797d9f63669 | snowvy | CC Attribution | faces=58238 | glb=1.4MB tex=0 max=0 | likes=15
## q="ladder back chair" lic=by n=4
  Vintage Rustic Wooden Chair | e7729870223446e189e8c30c5604c600 | apelsinka29070 | CC Attribution | faces=500000 | glb=52.0MB tex=3 max=4096 | likes=1
  French Ladder Back Chair | 39a05a5dd79f4d34b42e89b59033dd12 | Average3DmodelEnjoyer | CC Attribution | faces=10166 | glb=48.4MB tex=7 max=4096 | likes=1
  Low-poly Ladder Back Chair | 8a922e83386843028527e796e880d7b0 | Average3DmodelEnjoyer | CC Attribution | faces=758 | glb=22.0MB tex=3 max=4096 | likes=1
  Heirloom Chair | bc3d4bc5742541e5af374b46b81c5419 | Average3DmodelEnjoyer | CC Attribution | faces=11720 | glb=44.5MB tex=6 max=4096 | likes=1
## q="bar stool wood" lic=by n=24
  Bar bar | 818254b878dd46dda5566d2ae88f84da | anDDDres | CC Attribution | faces=227718 | glb=11.3MB tex=31 max=1024 | likes=599
  Bar Stool - 4096px² | 6351e81f25064477a96ce3eb6d7269df | mark-peters | CC Attribution | faces=88008 | glb=40.2MB tex=3 max=4096 | likes=77
  Pub Bar Rose Gold Metal Stool / Wood Top | 67d88c3a9b1c4075aaf3feaeabde4fa1 | artsandmaterials | CC Attribution | faces=1128 | glb=13.3MB tex=6 max=2048 | likes=70
  Metal Industrial Bar Stool | f5e340ffca03407c9f72f6675f83c51d | berilbaska | CC Attribution | faces=8318 | glb=8.4MB tex=3 max=2048 | likes=44
  Tall Kitchen Table | e51d10faae3e4448ae95432d294eb950 | AleixoAlonso | CC Attribution | faces=8278 | glb=26.3MB tex=3 max=4096 | likes=38
  Bar Stool | 382d65cea3e84bb68b81fd318b10d12c | raeganmaddox | CC Attribution | faces=4690 | glb=2.0MB tex=4 max=1024 | likes=27
## q="tea cart" lic=by n=4
  Indian street food cart | 9c1be296bf1842fe8f604c50849ed6e5 | sunita.gupta198011 | CC Attribution | faces=515532 | glb=22.2MB tex=1 max=2048 | likes=17
  Tea Cart | 81aa0a84f54545378d4d14d5823fa563 | ashnovember | CC Attribution | faces=76324 | glb=21.2MB tex=1 max=8192 | likes=9
  Simple Transport Cart | b6363189e4744853b250f07cbf40a533 | Lukymas | CC Attribution | faces=1077556 | glb=36.9MB tex=4 max=1024 | likes=6
  Cinderella Cart | bea38e7323ce4cf9a1313f791114a147 | VeinSyct | CC Attribution | faces=85470 | glb=6.5MB tex=5 max=1024 | likes=0
## q="torchiere" lic=by n=24
  "Selfie?" in Orsay Museum, Paris | f0fcdbc7ad614f97b43c71e2233f0b3e | HoangHiepVu | CC Attribution | faces=554718 | glb=42.1MB tex=2 max=8192 | likes=116
  Floor_lamp | 1ea7bb08894243f5b1f1200ee35fb40a | Uragan27 | CC Attribution | faces=2152 | glb=6.6MB tex=3 max=2048 | likes=47
  Asset Lights | b34bbce2451f4b06ba6b19dd487475ff | burunduk | CC Attribution | faces=1338 | glb=0.1MB tex=0 max=0 | likes=33
  737707_ Corinto_ Lightstar | d7b65bb5a9754d24829e55ce0b362790 | LIGHT_STAR_GROUP | CC Attribution | faces=9912 | glb=0.3MB tex=0 max=0 | likes=19
  738687_ Undine_ Lightstar | 46ba3f57c4e547ba9b4adb627e23f1ba | LIGHT_STAR_GROUP | CC Attribution | faces=5312 | glb=0.2MB tex=0 max=0 | likes=10
  574_747_748_ Tubo_ Lightstar | 8f4d071eee9b4c52bd70b5e8983addb3 | LIGHT_STAR_GROUP | CC Attribution | faces=1663264 | glb=91.5MB tex=0 max=0 | likes=9
## q="china cabinet" lic=by n=13
  victorian Cabinet | 81291e282b854934a6f1b9f53a900f5f | lagesnpiet | CC Attribution | faces=2876 | glb=42.2MB tex=3 max=4096 | likes=260
  Chinese Food Box | 31036f1e89c8483a8100c6f0e8784416 | JYModels | CC Attribution | faces=3304 | glb=0.5MB tex=2 max=1024 | likes=39
  Classic Solid Wood Showcase | 5ae39cc797324eaa81b7cdfc29d11129 | modeneseinteriors | CC Attribution | faces=1308412 | glb=35.2MB tex=0 max=0 | likes=26
  Low Poly China Cabinet | df702c25881e4e31a431bce54b197f0f | LortDigital | CC Attribution | faces=4416 | glb=0.1MB tex=0 max=0 | likes=12
  Triple-Section Cabinet | 4a45e5eb21804ac38dfb0821da704392 | Azura_SQ | CC Attribution | faces=1115180 | glb=84.3MB tex=4 max=2048 | likes=4
  Red Lacquered Chinese Temple Cabinet | 4399b2690a8a4c388021a45794f8598f | leolei34 | CC Attribution | faces=1784514 | glb=112.4MB tex=3 max=2048 | likes=3
## q="glass cabinet vintage" lic=by n=5
  Soviet Vintage Kitchen Cabinet (PBR Lowpoly) | 154bb3f924b64cdd935f2e196fa8a1e8 | Vitalii.Sandula | CC Attribution | faces=2704 | glb=7.4MB tex=3 max=2048 | likes=69
  Cursed Porcelain Doll - Antique Horror Prop | 288cb2cc88204a339257f221881dbef1 | s8819296 | CC Attribution | faces=1961576 | glb=129.0MB tex=3 max=4096 | likes=45
  Cabinet 2 | 0477a29f70a845d4b698f6093eb13a37 | tejay21 | CC Attribution | faces=555062 | glb=118.5MB tex=9 max=4096 | likes=33
  Love potion bottle | 8ace79a068684fe68c6a93274211871f | Allfie | CC Attribution | faces=22496 | glb=2.2MB tex=1 max=1024 | likes=7
  vintage showcase | 60d9fd8654bd4bb6af4dd803d89e0c2d | kavlumert | CC Attribution | faces=26470 | glb=1.3MB tex=0 max=0 | likes=1
## q="crt tv" lic=by n=24
  Sony PVM-1341 || Sony Playstation | 5f80311f1a4646ef9673f20ee6dc6245 | dark_igorek | CC Attribution | faces=240414 | glb=116.7MB tex=25 max=4096 | likes=824
  Sony PVM-14L2 CRT TV | ab19c2419c2647299ce96d027b3e7f5e | poring | CC Attribution | faces=12516 | glb=70.6MB tex=9 max=4096 | likes=625
  Retro CRT TV | 6bc462b233ce4c78904dfcadf5123e29 | ashabbugaev12 | CC Attribution | faces=1708 | glb=16.5MB tex=6 max=2048 | likes=425
  Nintendo Entertainment System - 85' Scene | cfd6dcb544fa4401b3dac20061d7fefb | theauditor | CC Attribution | faces=68024 | glb=72.6MB tex=38 max=4096 | likes=265
  Vintage TV Free | ed92cac6b8d64ea48ea4f91ce9bf350b | donnichols | CC Attribution | faces=3326 | glb=3.0MB tex=6 max=1024 | likes=258
  PSX CRT TV | 14c4034011ff4faebd99de03c7ab1635 | Tomitos_ | CC Attribution | faces=84 | glb=0.1MB tex=1 max=256 | likes=235
## q="wooden pallet" lic=by n=24
  Wooden Box - Pallet. Game Asset | 2a4411c6956f4adeb7877f03436bb742 | sergei_8888 | CC Attribution | faces=14052 | glb=3.5MB tex=3 max=1024 | likes=396
  Industrial Asset Pack | 0edba07309ef4ff98e5bb4d0b858952c | vmatthew | CC Attribution | faces=22658 | glb=204.0MB tex=159 max=2048 | likes=395
  Wooden Pallets | dba5c00928cd400796d9f6fffdd724b3 | yadrogames | CC Attribution | faces=384 | glb=6.8MB tex=6 max=2048 | likes=366
  Military Container Stage Props | 7056a14fb830432188a09b44d3fa61b9 | neslihancakmak | CC Attribution | faces=1003364 | glb=111.9MB tex=128 max=1024 | likes=340
  Pile of Wooden Pallets [FREE] | 2ccafd822f494dbe89348eeca1908aa2 | realMrAnderson | CC Attribution | faces=990000 | glb=72.7MB tex=1 max=8192 | likes=321
  Wooden Crate | e12fde1101b84b6da40056336a7b309d | yadrogames | CC Attribution | faces=324 | glb=6.2MB tex=6 max=2048 | likes=308
## q="plywood box" lic=by n=18
  LCVP Higgins boat (1945) | 92b2ec48991545f7baea8b0954489be8 | RedC130 | CC Attribution | faces=170108 | glb=9.3MB tex=6 max=1024 | likes=33
  '26 FREEDOM FLIGHT XL - 5ft x7ft | 2e81ad23367f4e2ab555d1f3f5a91d34 | dwe | CC Attribution | faces=1106864 | glb=48.6MB tex=4 max=4096 | likes=12
  '25 FREEDOM FLIGHT XL - 5ft x7ft ULTRA LIGHT | 3dcbff82465e4a7aaa123915164b4bf4 | dwe | CC Attribution | faces=1134452 | glb=48.6MB tex=4 max=4096 | likes=11
  ERS76 | 2bc7174dba934270816928b5f319274c | EvolutionFasteners2 | CC Attribution | faces=10958 | glb=0.4MB tex=0 max=0 | likes=8
  Crate | 6587efa32615464099b0736f92336506 | JackiiM | CC Attribution | faces=396 | glb=0.9MB tex=3 max=1024 | likes=4
  Bow | 491c0e1bfc834bfb98c1f119a4e50b48 | Lockstar64 | CC Attribution | faces=1200 | glb=26.8MB tex=2 max=4096 | likes=3
## q="wooden crate" lic=by n=24
  Crates And Barrels | 5ae3c72285474862a89d69c2f2ad2246 | jeandiz | CC Attribution | faces=7509 | glb=56.3MB tex=12 max=2048 | likes=916
  Issum, The town on Capital Isle | e433923a64d549fabb2d30635d643ab6 | Olee | CC Attribution | faces=193968 | glb=19.3MB tex=44 max=1024 | likes=866
  Wooden Boxes | ddecbe4586594bddb4822a90c0cba222 | MaX3Dd | CC Attribution | faces=4097 | glb=16.3MB tex=3 max=2048 | likes=686
  Rifle Box (Low Poly) | aaa6d521741944359a6b5a6b67a0bee7 | berkgedik | CC Attribution | faces=928 | glb=11.3MB tex=3 max=2048 | likes=680
  Low-Poly Fruit Box Assets | 9c66e47273b14057a1c6a646336cffda | Bowen154 | CC Attribution | faces=1996 | glb=18.7MB tex=3 max=2048 | likes=664
  Asset-Map Type Battlefield V | 60bff01e7fd349749f312bb3ab986e20 | Max-7215 | CC Attribution | faces=29848 | glb=223.1MB tex=18 max=4096 | likes=438
## q="desk phone" lic=by n=24
  Office Desk | b7a7bf47bdb241d1ba52acd7ecf2f0e8 | saeedkhalili.ir | CC Attribution | faces=311645 | glb=9.9MB tex=0 max=0 | likes=413
  Office Phone | 4176a01b6d0b4d13ad165c0df278a6b5 | maxdragon | CC Attribution | faces=4786 | glb=0.4MB tex=1 max=512 | likes=352
  Antique L.M. Ericsson Phone | 74281535466a4b32bb073ba3fe152cf8 | Ro_mulus | CC Attribution | faces=48684 | glb=51.6MB tex=3 max=4096 | likes=349
  6 Props | ff2e9985c03a4d789ea5ca4a5e3dd181 | Korpselene | CC Attribution | faces=12550 | glb=49.1MB tex=18 max=2048 | likes=274
  Lesson 20 Eiffel Tower Paramount Telephone | 7351366cae2a4361aa3318f9d2fcb03a | n.tendetnik | CC Attribution | faces=10966 | glb=58.3MB tex=3 max=4096 | likes=251
  Retro Office Props | 65e47619f5114df89fd26db1fa7f9d7f | YJ_ | CC Attribution | faces=108236 | glb=164.6MB tex=58 max=2048 | likes=130
## q="binder" lic=by n=24
  90s Retro Office Pack | dadca97505214b9481d35e22c48e18df | MadeByYeshe | CC Attribution | faces=44155 | glb=56.5MB tex=160 max=4096 | likes=1116
  Document File Folder | 11390179bba7462484d344e2fe22c703 | kuroderuta | CC Attribution | faces=1505 | glb=51.5MB tex=6 max=4096 | likes=1007
  Single spiral notepad | 80299283fefc44649ae00bf4992b7ba2 | sousinho | CC Attribution | faces=30342 | glb=4.4MB tex=3 max=2048 | likes=340
  Modulair Office assets (extra) (Post Apoc) | 2dd7f5d512ba4510b8423fee904dbe36 | JordiKruk | CC Attribution | faces=1333 | glb=7.3MB tex=1 max=4096 | likes=289
  Document Ring Binder | c91efa31b18749bdab2605fde1571856 | kuroderuta | CC Attribution | faces=198796 | glb=75.9MB tex=10 max=4096 | likes=282
  Mei Posed 001 - Female Walking Business Model | 07f308b81bc045c8917104a72ce2ffe4 | renderpeople | CC Attribution | faces=100008 | glb=13.8MB tex=1 max=8192 | likes=259
## q="paper stack" lic=by n=24
  [CC0] Newspaper Stack - Ready to Unity HDRP | c4311a0b918643af97904e10c7a34efc | karlwirbelwind | CC Attribution | faces=2132 | glb=9.6MB tex=3 max=2048 | likes=1288
  Book Stack | 90944ea5739248f6b707d6c2b0955c3b | paubr | CC Attribution | faces=1620 | glb=29.4MB tex=6 max=4096 | likes=705
  Medieval Book Stack | 0ea43f7fdcb7411cb1123b987f297d41 | GetDeadEntertainment | CC Attribution | faces=2968 | glb=11.1MB tex=3 max=2048 | likes=678
  Paper Stack | e8b337d31a5a44eaa7265c2dbc63fc1c | vivifyproductions.co | CC Attribution | faces=18792 | glb=0.9MB tex=3 max=1024 | likes=141
  Papers | f858428c790f43f8ba9a3aa2996b88b0 | oparaskos | CC Attribution | faces=619 | glb=5.8MB tex=2 max=2048 | likes=115
  Human Epidermal Cell | bd685c57fc904f3e891a21b25e659d3f | terrielsimmons | CC Attribution | faces=0 | glb=12.2MB tex=0 max=0 | likes=64
## q="office trash can" lic=by n=18
  Trash Alley - Wigan Street | 36576ecb1b3648f7b74d5e71d3ba3f0c | z3d.nz | CC Attribution | faces=84004 | glb=21.8MB tex=3 max=8192 | likes=139
  Modern chair and table (Post-apocalypse) | ad669f19d20b41039404b8aa8d61cd7a | kurmanin | CC Attribution | faces=7029 | glb=38.5MB tex=12 max=2048 | likes=52
  Office Props Pack | 7bae180618f0443b8bfd397e348d941b | noorani.hasnain3 | CC Attribution | faces=189063 | glb=82.1MB tex=76 max=2048 | likes=47
  Trash basket | c9bf9a2b04f44fea82c38344cc5ec8f4 | DevFaisal | CC Attribution | faces=11316 | glb=0.5MB tex=0 max=0 | likes=46
  Futuristic Trash Can | 626389bbefe342289b7214a5186cefb0 | kennyt | CC Attribution | faces=646 | glb=1.1MB tex=4 max=1024 | likes=29
  GAME READY BACKROOMS ASSET PACK VOL. 2 | 4d0ee1ba795140b69288819764db10e8 | oxygen3d | CC Attribution | faces=27206 | glb=4.5MB tex=1 max=2048 | likes=23
## q="wastebasket" lic=by n=9
  Trash | 8ae03cc7b4044b1fbbf3df649f46dd4b | local.yany | CC Attribution | faces=37999 | glb=15.5MB tex=4 max=4096 | likes=188
  Bathroom Assets | 865e8aca42584db190d50c280f670e13 | Narutonic | CC Attribution | faces=1718 | glb=0.7MB tex=3 max=512 | likes=39
  Wooden garbage container - damaged | bffedbdce5a945f7a2abca0bfca85478 | DEJVDOU | CC Attribution | faces=553406 | glb=44.8MB tex=2 max=4096 | likes=14
  Waste Bin (Animation): Household Props 24 | bb24dc82165346f7a2a64bf2c378504c | doneil | CC Attribution | faces=270 | glb=0.3MB tex=2 max=512 | likes=11
  garbage can | ab484b97568949b891d83480d0cb2e0b | ree27703 | CC Attribution | faces=8960 | glb=0.4MB tex=0 max=0 | likes=3
  Wastebasket | 3c6afba702c64906b5a850051b6888bc | dianawahyuni | CC Attribution | faces=3135 | glb=0.2MB tex=1 max=128 | likes=3
## q="wall clock" lic=by n=24
  Old wall clock | 8e920e8b129842718099a3f772cec024 | AndreiVNK | CC Attribution | faces=1538 | glb=11.3MB tex=4 max=2048 | likes=412
  Antique Wall Clock | 174a3fc826414bfc9693d9b00f43fe57 | 3DGunsmith | CC Attribution | faces=1970 | glb=2.4MB tex=3 max=1024 | likes=272
  Wall Clock | 2e964ac0242e4b1789adfd9549c653dc | felipeprodev | CC Attribution | faces=798 | glb=3.7MB tex=2 max=2048 | likes=205
  PSX-Style Vintage Wall Clocks | 9dc475ad89874ccc9d2b199d0ec00806 | vanillao03 | CC Attribution | faces=1228 | glb=0.4MB tex=2 max=512 | likes=201
  Wall clock old | 07859442442f4d24995ab93e1533106f | Artem.Goyko | CC Attribution | faces=1941 | glb=12.4MB tex=51 max=1024 | likes=199
  Vintage wall Clock | 634a04c45ef04bc68c5240ae265f8537 | sousinho | CC Attribution | faces=9300 | glb=59.4MB tex=9 max=4096 | likes=192
## q="club chair" lic=by n=23
  Literary Club Chair - Preview | d94bd85f39944eb299e467de21733966 | IUI-UniversityLibrary | CC Attribution | faces=74384 | glb=8.7MB tex=1 max=2048 | likes=285
  Club chair | 0edad579dcd9431e9b91c1fff4b84700 | alban | CC Attribution | faces=36177 | glb=7.0MB tex=2 max=4096 | likes=144
  Literary Club Chair | 76e27215f5324cc580c39499431ed54c | IUI-UniversityLibrary | CC Attribution | faces=757357 | glb=31.6MB tex=1 max=4096 | likes=111
  Club Chair | fe97624ba34d4334933e9f7830eb04b0 | juang3d | CC Attribution | faces=93824 | glb=2.4MB tex=0 max=0 | likes=82
  Wassily DFA 24 | 1c4d14c0e90b49018475c335aebc425b | greshnovk | CC Attribution | faces=5004 | glb=4.0MB tex=4 max=2048 | likes=79
  Club Chair | da25d54972b04a8e9fa64048c7bcb89c | Saandy | CC Attribution | faces=10696 | glb=9.0MB tex=3 max=2048 | likes=61
## q="chest of drawers" lic=by n=24
  Furniture set | 09b8b458fbad4986b6fd44698f5bc6dc | Peter.Nox | CC Attribution | faces=18512 | glb=15.8MB tex=3 max=4096 | likes=458
  Nintendo Entertainment System - 85' Scene | cfd6dcb544fa4401b3dac20061d7fefb | theauditor | CC Attribution | faces=68024 | glb=72.6MB tex=38 max=4096 | likes=265
  Office Table | 80130830a9814e9298f11920ad0b7275 | Agha.Najam | CC Attribution | faces=61738 | glb=11.9MB tex=6 max=4096 | likes=190
  [Free] Drawer Tool Cart (Used) | da8955e5c8c448e58b013951f48148a0 | rprispil | CC Attribution | faces=850 | glb=7.9MB tex=3 max=2048 | likes=181
  Medieval Drawer | 4f1e62dcea4a4c2588bc80b0b8c034f3 | Zambur | CC Attribution | faces=3448 | glb=33.9MB tex=3 max=4096 | likes=175
  Tool Cart | 16ceecf05f3e453e96c050f4c43f86b5 | jimbogies | CC Attribution | faces=80238 | glb=12.0MB tex=6 max=2048 | likes=159
## q="sideboard" lic=by n=24
  modern scandinavian kitchen island | a9738f4e651b4779acdddcfbb89516f6 | QuarizonStudio | CC Attribution | faces=65974 | glb=20.1MB tex=19 max=4096 | likes=368
  European style dining cabinet | c8717576f2244716b3abf321065f2b9a | D.art | CC Attribution | faces=51303 | glb=35.6MB tex=7 max=4096 | likes=318
  Wooden Back Bar Cabinet - 4096px² | a1961b9e5a7043fb9a70b855e947e27f | mark-peters | CC Attribution | faces=23213 | glb=53.6MB tex=3 max=4096 | likes=170
  [Free] Dining Set Scandinavian Style | 61275205fe084208887d74876919aac6 | AllQuad | CC Attribution | faces=66694 | glb=26.6MB tex=32 max=2048 | likes=124
  Mid Century Teak Sideboard Credenza | 3028ba44d1f245b886c12eadc934f722 | calebkung | CC Attribution | faces=21794 | glb=1.7MB tex=2 max=1024 | likes=80
  Sideboard | 1492a0e14568490bb5c3a20e903622ac | choppar | CC Attribution | faces=980 | glb=9.8MB tex=3 max=2048 | likes=78
## q="side table vintage" lic=by n=10
  New Family Desk | f832b6dc57774c0f8fb380b21bbccd65 | IUI-UniversityLibrary | CC Attribution | faces=2069998 | glb=96.5MB tex=1 max=8192 | likes=103
  Coffee Tables Three Legs with Rattan I Low-Poly | c434f22ec51846cc8142e95f7f2495eb | pascal.garten | CC Attribution | faces=6088 | glb=21.6MB tex=5 max=4096 | likes=80
  Dining Room Side Table | ec99fad1fc9643f59859850265073782 | IUI-UniversityLibrary | CC Attribution | faces=2710826 | glb=330.5MB tex=1 max=8192 | likes=64
  Timeless wavy side table by Modenese | 29c888d41a2f415783bb2c7402cb1f5c | modeneseinteriors | CC Attribution | faces=85752 | glb=3.8MB tex=0 max=0 | likes=27
  Weathered Round Table  Metal Top & Wooden Legs | 6cd4d2509f2b4e4ea97d8f6a93c94c43 | Nikoleta.Zhecheva | CC Attribution | faces=574 | glb=77.0MB tex=9 max=4096 | likes=19
  Vintage Side table | fc510dbff15e4106bba4c1ab3bd3bc19 | kingdome | CC Attribution | faces=116188 | glb=5.7MB tex=0 max=0 | likes=10
## q="table lamp vintage" lic=by n=24
  Office - Assets | 16c1a779bb0a4055a26367741d39e059 | EvanPetrov | CC Attribution | faces=30368 | glb=133.2MB tex=42 max=4096 | likes=2142
  Leather armchair/ Coffee table/ Floorlamp | fcce92a09de84456a071ea6117b57cbc | YJ_ | CC Attribution | faces=7821 | glb=51.2MB tex=4 max=4096 | likes=1252
  Old Table Lamp V02 | 70659923adc74413ba983516139e222d | mar.cos. | CC Attribution | faces=2686 | glb=5.5MB tex=4 max=2048 | likes=259
  Classic table lamp | 1a3292317bb342b4b33431081338a5c3 | AndreiVNK | CC Attribution | faces=14548 | glb=28.8MB tex=3 max=4096 | likes=224
  1920s Table Lamps Type A | fb7475ef551c46f9b4b2b28d96d31dfc | Mad_Lobster_Workshop | CC Attribution | faces=66992 | glb=193.2MB tex=9 max=4096 | likes=211
  LAMP | a2adb536e2354db2ab422072a5537547 | twilightfox | CC Attribution | faces=4146 | glb=22.4MB tex=3 max=4096 | likes=204
## q="floor lamp vintage" lic=by n=9
  1920s Standing Floor Lamps Type A | ca1cf1c435ec4012b9b6d5128333ad83 | Mad_Lobster_Workshop | CC Attribution | faces=59406 | glb=192.7MB tex=9 max=4096 | likes=226
  1920s Table Lamps Type A | fb7475ef551c46f9b4b2b28d96d31dfc | Mad_Lobster_Workshop | CC Attribution | faces=66992 | glb=193.2MB tex=9 max=4096 | likes=211
  Vintage Floor Lamp 70s Freebie | 36c21f6b4c4e4b1d94401c287f902362 | Geug | CC Attribution | faces=23984 | glb=97.3MB tex=10 max=4096 | likes=105
  Interior Decor Props Collection Vol. 1 | 985bfb95e1794254b3ce62b8eac51b49 | Nicholas01 | CC Attribution | faces=4 | glb=1.0MB tex=1 max=1024 | likes=25
  lamp | 1d8b4c2708a14a32a29b1b040b80ecfc | snowvy | CC Attribution | faces=4640 | glb=0.1MB tex=0 max=0 | likes=12
  Floor Lamp | 055ecc09440b4a40b3c27caf8e0ff768 | mattpoast | CC Attribution | faces=12528 | glb=13.8MB tex=17 max=2048 | likes=11
```

### Appendix B2 — Sketchfab CC0 (license=cc0) searches
```
## q="computer" lic=cc0 n=24
  Creel Basket | c4142764f11b4640b5951b37c2c4d1a5 | cineg | CC0 Public Domain | faces=687902 | glb=39.5MB tex=4 max=4096 | likes=89
  Skull showing treponemal disease (syphilis) | 2692cc377baf4031b288aeaa58154bba | cineg | CC0 Public Domain | faces=900352 | glb=46.7MB tex=4 max=4096 | likes=56
  Human Humerus Bone | 12744d7c36be47d8ad94f620a22d649c | cineg | CC0 Public Domain | faces=345646 | glb=25.1MB tex=4 max=4096 | likes=31
  Seven Half Hull Models | 891afcef8be54f4f9eae626800d5f7b6 | ScottishMaritimeMuseum | CC0 Public Domain | faces=258171 | glb=102.3MB tex=16 max=4096 | likes=30
  Qube | 026aa846da8d4fc98cd05a72a3d2edab | thecablecenter | CC0 Public Domain | faces=795206 | glb=34.3MB tex=1 max=4096 | likes=26
## q="monitor" lic=cc0 n=2
  Silent Monitor | a8078c7542b747e5aca777e970ac0105 | ScottishMaritimeMuseum | CC0 Public Domain | faces=272414 | glb=31.5MB tex=2 max=4096 | likes=25
  V-GIS | 7183c4fcd01942008304269169dd37f4 | thecablecenter | CC0 Public Domain | faces=50000 | glb=23.0MB tex=1 max=4096 | likes=5
## q="office chair" lic=cc0 n=2
  Side Chair | 9c7f1f712edc4b3196e8dcca39a9a537 | Smithsonian | CC0 Public Domain | faces=100142 | glb=26.7MB tex=3 max=4096 | likes=347
  Chair (England) 1750-60 | 40688b848b6044f6af306ecdf2b8b105 | Smithsonian | CC0 Public Domain | faces=150000 | glb=21.0MB tex=2 max=4096 | likes=76
## q="desk" lic=cc0 n=0
## q="cabinet" lic=cc0 n=4
  Doctor Walerian Klecki’s first aid kit | 472419b814f54fbda74d4e63c262e389 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=1739776 | glb=72.8MB tex=2 max=4096 | likes=147
  Panel for a Cabinet Door | 1288a8b5aa694579a4f73ce2aeab70e3 | Smithsonian | CC0 Public Domain | faces=150000 | glb=34.4MB tex=3 max=4096 | likes=132
  Augsburg table cabinet, c. 1560-1570 CE | 2f2086b17f52471496f2aa2c7dda4197 | artsmia | CC0 Public Domain | faces=33992 | glb=69.8MB tex=29 max=2048 | likes=87
  Viererkopf "Memento Mori" | 29e8ed82994f4f66a193129319ec3bf8 | mkghamburg | CC0 Public Domain | faces=2000000 | glb=99.0MB tex=2 max=8192 | likes=20
## q="chair" lic=cc0 n=12
  Side Chair | 9c7f1f712edc4b3196e8dcca39a9a537 | Smithsonian | CC0 Public Domain | faces=100142 | glb=26.7MB tex=3 max=4096 | likes=347
  Zakopane style chair | 3f3e54908994487bb94f6358d52e75cf | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=141569 | glb=18.4MB tex=2 max=4096 | likes=162
  Chair (England) 1750-60 | 40688b848b6044f6af306ecdf2b8b105 | Smithsonian | CC0 Public Domain | faces=150000 | glb=21.0MB tex=2 max=4096 | likes=76
  2024.140 Ceremonial Chair or Throne | d72f5cf4c8e24daca0de504f342b8cf1 | clevelandart | CC0 Public Domain | faces=255386 | glb=178.9MB tex=3 max=8192 | likes=61
  1983.33 Prestige Chair | 03d10a0ccb254061a8ec77b8cc14b40c | clevelandart | CC0 Public Domain | faces=90000 | glb=89.2MB tex=3 max=8192 | likes=41
## q="armchair" lic=cc0 n=3
  Armchair | 36bc06f43e3f485093a56842d36077ea | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=249682 | glb=40.8MB tex=3 max=4096 | likes=186
  Johann Wolfgang von Goethe COVID-19 | 99d6b24e3ccb40c8a86111f4f2acf855 | www.noe-3d.at | CC0 Public Domain | faces=473404 | glb=71.6MB tex=1 max=8192 | likes=69
  Armchair With Slip Seat | c6c4a65abf90401abab62f238f13a640 | Smithsonian | CC0 Public Domain | faces=150000 | glb=14.7MB tex=2 max=4096 | likes=53
## q="sofa" lic=cc0 n=0
## q="lamp" lic=cc0 n=24
  2018.281 Peacock Table Lamp | a24bcb6b7a2e448fad661004f403ae12 | clevelandart | CC0 Public Domain | faces=59408 | glb=444.3MB tex=18 max=8192 | likes=419
  Locomotive Headlamp | f4f2e2d5cbda44ae8f059a267b459269 | ScottishMaritimeMuseum | CC0 Public Domain | faces=23594 | glb=23.6MB tex=3 max=4096 | likes=143
  Safety Flame Lamp from the Shale Oil Museum | 643da293172e4d84b504d3d99f8e0df8 | ScottishMaritimeMuseum | CC0 Public Domain | faces=25514 | glb=25.9MB tex=2 max=4096 | likes=85
  2023.104 Oil Lamp | 1946d782b9d949848f75b6b69efcedf7 | clevelandart | CC0 Public Domain | faces=119864 | glb=152.9MB tex=3 max=8192 | likes=75
  Mitscherlich polarimeter with gas lamp | d997668759cb45449264d7d25045cbad | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=166288 | glb=178.3MB tex=6 max=8192 | likes=65
## q="television" lic=cc0 n=18
  ESPN Hat | 1317f928db1747489a0b19c755c8ab3a | thecablecenter | CC0 Public Domain | faces=49999 | glb=15.0MB tex=1 max=4096 | likes=72
  Jerrold Cable TV Set-top Box | 6a5993c79d1743bdb7bf58b5df29e51c | thecablecenter | CC0 Public Domain | faces=100000 | glb=6.9MB tex=1 max=2048 | likes=44
  Jerrold Model 704 Strength Meter | f520e93aedf64e3b8b82f9617cc2b6b5 | thecablecenter | CC0 Public Domain | faces=3515291 | glb=127.7MB tex=1 max=4096 | likes=42
  Time Warner SA Remote | 4e0993560f6e4e7cb08b321902d279c9 | thecablecenter | CC0 Public Domain | faces=268940 | glb=8.6MB tex=1 max=1024 | likes=42
  Mr T Chia Box | 1fdbaff8813f4b15a2206b0609ae7bcb | thecablecenter | CC0 Public Domain | faces=246382 | glb=11.7MB tex=1 max=2048 | likes=39
## q="stool" lic=cc0 n=2
  Chieftain’s stool from Cameroon | bf643415e76440d88c9208e357f99691 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=259384 | glb=22.9MB tex=2 max=4096 | likes=145
  2006.138 Prestige Stool (Kuo fo) | 5722f792fa484993bc06ca6f0c0244fb | clevelandart | CC0 Public Domain | faces=69710 | glb=122.8MB tex=3 max=8192 | likes=29
## q="dresser" lic=cc0 n=14
  12th C CE Water-Moon Guanyin - point cloud | 996ce4d6401445ac9c26f927770df851 | artsmia | CC0 Public Domain | faces=0 | glb=237.8MB tex=0 max=0 | likes=149
  St. Stanislaus (St. Martin of Tours?) | b558c99bb6c442dfb1cf23419d45a73c | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=999886 | glb=210.0MB tex=9 max=4096 | likes=75
  Hl. Ulrich von Augsburg | 7060550e6640460aa1b525f411acee7e | www.noe-3d.at | CC0 Public Domain | faces=582886 | glb=71.3MB tex=1 max=8192 | likes=68
  Kore dressed in chiton and cape (epiblema) | 185f351f4d1249749b4c88b0d2c27511 | smkmuseum | CC0 Public Domain | faces=288766 | glb=8.2MB tex=0 max=0 | likes=62
  Hl. Servatius | c8a2cb0958e84e38a64c03ad57947185 | www.noe-3d.at | CC0 Public Domain | faces=492602 | glb=87.7MB tex=1 max=8192 | likes=51
## q="table" lic=cc0 n=24
  1924.859 Table Fountain | c03c9b6836aa42328803baeef085be40 | clevelandart | CC0 Public Domain | faces=506761 | glb=212.1MB tex=6 max=8192 | likes=487
  2018.281 Peacock Table Lamp | a24bcb6b7a2e448fad661004f403ae12 | clevelandart | CC0 Public Domain | faces=59408 | glb=444.3MB tex=18 max=8192 | likes=419
  Tabletop clock (1670) | c5d25a4967894a1683afeb3533658d5b | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=2910528 | glb=113.5MB tex=4 max=4096 | likes=343
  1991.45 Table and Tea Service | 475426f525de4a55a4ba5540ea0fbdd1 | clevelandart | CC0 Public Domain | faces=178251 | glb=151.2MB tex=8 max=8192 | likes=260
  Porcelain plate from the Flora Danica service | 3862e607231c46729f91b3bbb32412b8 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=849680 | glb=99.6MB tex=3 max=8192 | likes=210
## q="crate" lic=cc0 n=0
## q="pallet" lic=cc0 n=0
## q="telephone" lic=cc0 n=4
  Telephone | e2389b65271f4a57906fe194dbd0e56a | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=52468 | glb=49.7MB tex=3 max=4096 | likes=343
  Morse-Vail Telegraph Key | a5b108e3132d46b696c36310c2314ed8 | Smithsonian | CC0 Public Domain | faces=150000 | glb=18.3MB tex=3 max=4096 | likes=124
  Chester Telegraph Relay | 1b464109b4df435a959fd2cae00da1e4 | Smithsonian | CC0 Public Domain | faces=150000 | glb=23.1MB tex=3 max=4096 | likes=31
  Badge of the telephone unit | 8e63be1aa78d4e68b1b231f8e1e2f048 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=42844 | glb=20.8MB tex=2 max=4096 | likes=18
## q="clock" lic=cc0 n=18
  Astronomical monstrance clock | ec83c5935b7341788775f856f268ac61 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=588882 | glb=45.1MB tex=2 max=8192 | likes=684
  Tabletop clock (1670) | c5d25a4967894a1683afeb3533658d5b | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=2910528 | glb=113.5MB tex=4 max=4096 | likes=343
  Equatorial sundial | 98b148ffdc574b1a8e1eaab01b4821ce | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=545848 | glb=204.2MB tex=6 max=8192 | likes=295
  Pocket watch | f5f6785f33234709bc297ee27725d5d0 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=300612 | glb=105.6MB tex=3 max=8192 | likes=140
  Pocket chronometer watch | 943e853db20f46f7a413be424b6158bc | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=517603 | glb=45.3MB tex=5 max=4096 | likes=138
## q="cart" lic=cc0 n=8
  Ehrengrab Müller u. Pettenkofen | 27d936ffbccf47b392026becea3d5a3d | www.noe-3d.at | CC0 Public Domain | faces=628398 | glb=94.7MB tex=1 max=8192 | likes=109
  Egg Carton From Muslim Farms | 34718f6a4bac43cbae72ad80d135c68e | Smithsonian | CC0 Public Domain | faces=150000 | glb=17.6MB tex=3 max=4096 | likes=98
  Aset-iri-khet-es mummy sarcophagus & cartonnage | 9ad64e4cc1de4b719a669ef7caf6e329 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=308796 | glb=29.4MB tex=5 max=4096 | likes=73
  Wooden toy — “A cart pulled by horses” | 9980a3ad87f74540a1273f30f49fa9c0 | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=64000 | glb=62.0MB tex=3 max=8192 | likes=72
  “On the way” | 3dfbf09b8adb437aa79c6912d620f96b | WirtualneMuzeaMalopolski | CC0 Public Domain | faces=962782 | glb=93.1MB tex=2 max=8192 | likes=63
## q="shelf" lic=cc0 n=4
  Antarctic Meteorite Sample LAR 12326,32 | 9518395c58084c6f883d903daa886460 | Astromaterials3D | CC0 Public Domain | faces=194346 | glb=14.6MB tex=1 max=4096 | likes=19
  Great Departure of the Buddha | 229b2f23987c4fe48643a622c5bea542 | danielpett | CC0 Public Domain | faces=558370 | glb=22.3MB tex=1 max=4096 | likes=15
  Antarctic Meteorite Sample MIL 090036,35 | fac3f65895d74752a507a151ea56a7e8 | Astromaterials3D | CC0 Public Domain | faces=99862 | glb=12.8MB tex=1 max=4096 | likes=13
  TN004-010032 - Cross Slab | 9f625c246386442da9b2d65a458d69bc | Tipperary3D | CC0 Public Domain | faces=180827 | glb=23.5MB tex=1 max=8192 | likes=0
## q="vending machine" lic=cc0 n=0
## q="water cooler" lic=cc0 n=0
```
