# 05 · Texture & material sourcing for the Office level and the furniture piles

Status: COMPLETE for this pass (2026-10-02). Nothing has been downloaded; every entry is a URL for Red to approve.

Legend: **V** = verified this run by fetching the page or the site's API (date 2026-10-02). **U** = UNVERIFIED (lead only). Recommendation: **USE** / **MAYBE** / **REJECT** / **GEN** (generate procedurally in `gen_surfaces.py` instead).

## 0. TL;DR

1. **Licences are not the problem.** ambientCG and Poly Haven are plain CC0 (verified); 3DTextures.me and TextureCan are CC0; cgbookcase states CC0 1.0. ShareTextures is "custom CC0" (no redistribution outside a built product, keep raw files out of a public repo). FreePBR is non-commercial unless paid; textures.com is proprietary: avoid both.
2. **Download the furniture materials, keep generating the room shell.** The flat look Red dislikes comes from Codex's 512-px value-noise wood/metal/vinyl. Poly Haven's 2026 veneer series (teak, lacquered cherry, dark wood, red oak, walnut, plywood), its 2025 fabric series (poly-wool herringbone, rough linen, velour velvet, floral jacquard), and ambientCG plastics/metals/leather (Plastic013B/018B/012B, Metal028/016/050C, Leather027) cover every piece in both film stills and the target office. Tier-1 list = 19 assets, ≈255 MB published (≈160 MB if Poly Haven maps are fetched individually).
3. **Room shells: generate or hybridise.** No CC0 source has a ≥2K 2'x2' fissured tile without baked lights, a scanned 24" carpet tile, a plain almond laminate, a pinstripe wallpaper, blue painter's tape or ceiling stain clouds. Keep `gen_surfaces.py` for those and bake two scanned micro-maps into it (Poly Haven `dirty_carpet` for the pile, `polystyrene` for tile pits). Swap the drywall for Poly Haven `beige_wall_001` if A/B looks better.
4. **Decals**: ambientCG Leaking / SurfaceImperfections / Fingerprints / Smear / Scratches and cgbookcase Liquid Stains + Dust Wipes, at 1K. The URP renderer has no Decal feature yet; prefer baking stains into masks, projectors only for hero spots.
5. **Landing**: the shader is metre-based (`_TileSize`), GL normals, mask R = smoothness, G = cavity. Convert with a small `import_cc0.py` (1 − roughness, AO → G, regrade albedo), unwrap props at 1 UV = 1 m in Blender, and set `_TileSize` to each asset's published physical size. Room-shell repeats must divide 256 m.

## 1. How a downloaded material has to land in FrontRooms

Read from the project, not assumed:

- **Shader** `Assets/Resources/Rendering/FrontRoomsSurface.shader` (`FrontRooms/Surface`) samples `_BaseMap` (albedo), `_BumpMap` (tangent normal, `UnpackNormalScale`, i.e. Unity / OpenGL Y+ convention), `_MaskMap` (**R = smoothness, G = cavity/AO**, B = wet, A = 1), optional `_EmissionMap`, plus the shared `MacroWear_M` macro map (R tone, G dirt, B damp, A streaks) and procedural water-stain / floor-grime / ceiling-streak terms.
- **Coordinates:** by default the shader builds UVs from **world position in metres** (`PlanarFrame`), then divides by `_TileSize` (metres). With the `_FR_MESH_UV` keyword it reads mesh UVs, also in metres. So a downloaded material lands correctly if `_TileSize` is set to the **physical size the source publishes** (Poly Haven `dimensions`, ambientCG `dimensionX/Y`). That is why physical size is recorded for every candidate below.
- **The 256-m rule** (`gen_surfaces.py` header): world-projected repeats must divide 256 m so the stream's floating-origin rebase never shifts a pattern. 1.0 m, 0.5 m, 0.8 m (=256/320), 2.0 m pass; 0.6, 1.4, 1.83 m do not, so for room shells (floor / wall / ceiling) set `_TileSize` to the nearest 256/n (e.g. 1.40 → 256/183 = 1.3989 m, a 0.08 % stretch nobody can see). Props using `_FR_MESH_UV` move with their mesh and are exempt.
- **Map conversion** (both CC0 libraries ship everything needed): albedo = `Diffuse`/`Color` (sRGB); normal = **`nor_gl` (Poly Haven) / `NormalGL` (ambientCG)**, never the DX version; mask = R `1 − Roughness`, G `AO` (Poly Haven `arm` already packs AO/Rough/Metal in R/G/B, so R←1−arm.G, G←arm.R). Height/displacement is not used by the shader; keep it only to bake cavity where AO is missing (ambientCG wood sets ship no AO).
- **Resolution budget:** the current kit ships 2048 px for big surfaces and 1024 px for props (VISUAL_RESEARCH_LOOKDEV.md). Download **2K JPG** for case goods, fabrics and anything mapped onto the floor; **1K** for small props (plastics, metals, leather) and decals; then let Unity compress (ASTC 6x6 on Apple Silicon, BC7 on Intel Macs). 4K is only worth it for a scanned detail layer baked into the floor, which fills half of every frame. Every 2K figure below is the zip/map total published by the site; what lands in the project after packing is roughly a third of that.
- **Already generated in-house** (`Assets/Resources/Surfaces/Textures/`): `Office_CarpetTile`, `Office_Ceiling2x2`, `Office_Drywall`, `Office_CubicleFabric`, `Office_Louver`, `PaintedMetal`, `DoorVeneer`, `MacroWear_M`, and Codex's 512-px `OfficeFurniture_Wood/Metal/Vinyl` (from `Tools/lookdev/gen_office_furniture_textures.py`, stdlib only, value-noise based; this is part of why the furniture reads flat).

Calibration against the frames: the current `Verification/lookdev/2_Office_forward.png` already has the right grade and a believable ceiling/carpet, but the props are untextured-looking slabs and the carpet tile reads as one flat value with no stain map. Red's target (`ref_office_target.png`) gets its realism from (a) scanned-looking ceiling-tile fissures plus **large brown water-stain clouds**, (b) carpet tiles with **per-tile tone shift and dark blotches**, (c) beige walls with near-invisible texture, and (d) props that read because of **edge wear, plastic sheen and correct values**, not because of texture detail. The download list below follows that: buy realism on the furniture materials and decals; keep room shells procedural.

## 2. Source licences (verified)

All checked 2026-10-02 by fetching the licence page text.

| Source | Licence | Game use / redistribution | Caveat | V | Use? |
|---|---|---|---|---|---|
| [ambientCG](https://docs.ambientcg.com/license/) | CC0 1.0 | Page says raw files may be included in a project "for example a video game"; no credit needed | none | V | **Primary** |
| [Poly Haven](https://polyhaven.com/license) | CC0 | Any purpose incl. commercial; may redistribute, even in a product you sell | none | V | **Primary** |
| [3DTextures.me](https://3dtextures.me/about/) | CC0 | "You can use the textures for any purpose, including commercial" | Free tier is 1024 px only; 4K is a Patreon reward (see [ceiling-drop-tiles-001](https://3dtextures.me/2019/03/27/ceiling-drop-tiles-001/)) | V | Secondary |
| [TextureCan](https://texturecan.com/terms/) | CC0 1.0 | May be redistributed together with your projects | brand/logo content is user's responsibility | V | Secondary |
| [cgbookcase](https://www.cgbookcase.com/textures/) | CC0 1.0 (stated on the /textures/ index; home page says "100% free, no restrictions") | yes | max 4K; **normals are DirectX only** (flip G for Unity); /license and /faq URLs 404; real-world size not shown in page text | V | Secondary |
| [ShareTextures](https://www.sharetextures.com/p/license) | "Custom CC0" with extra rules | Commercial OK | No redistribution as collections/plugins; CC0 only when downloaded directly from their site; no automated downloads. Fine inside a built game, but **do not commit raw files to a public repo** | V | Use with care |
| [FreePBR](https://freepbr.com/about-free-pbr/) | Custom, not CC0 | Free only "as long as you don't use these commercially"; $19 for commercial; no redistribution of the files | A student project is non-commercial, but a portfolio/Steam release would need the fee | V | **Avoid** |
| [textures.com](https://www.textures.com/faq-license) | Proprietary | Games allowed incl. free accounts; no open-source release, no resale as textures (per search summary) | Page body did not render for the fetcher; free account has daily credit limits | U | **Avoid** |
| Fab / Megascans | Fab Standard License | Usable in any engine per [CG Channel 2024](https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/); most Megascans paid since 2025 | Requires Epic account; not CC0 | U | Only if a specific item is free |
| Adobe Substance 3D Assets | Adobe licence; usable in a "Larger Work" like a game | needs subscription to download | Search summary only | U | Skip |

## 3. Candidates by material

Metadata for every ambientCG row comes from the public JSON API `https://ambientcg.com/api/v2/full_json?id=<ID>&include=downloadData,mapData,dimensionsData` and for every Poly Haven row from `https://api.polyhaven.com/info/<id>` + `/files/<id>` (both fetched 2026-10-02). "2K" = total of all 2K JPG maps as published (Poly Haven: Diffuse+nor_gl+Rough+AO+Displacement+arm; ambientCG: the 2K-JPG zip incl. both DX and GL normals). Physical size is what goes into `_TileSize`. Poly Haven assets all ship Diffuse, nor_gl, nor_dx, Rough, AO, Displacement, arm (and .blend/.gltf). ambientCG wood/plastic/leather sets ship Color, NormalGL/DX, Roughness, Displacement and **no AO** unless stated.

### 3.1 Wood: cherry, oak, walnut, orange 70s teak, laminate woodgrain, plywood, particle board

Poly Haven published a large veneer series on 2026-08-11 (API `date_published`; 1 m x 1 m, up to 8K, all maps). "photo" in the Method column means a Poly Haven capture: the API does not state the capture method per asset, so treat it as UNVERIFIED (ambientCG's API does state it: `PBRPhotogrammetry`, `PBRApproximated` = from photo, `PBRProcedural` = procedurally generated). It is the best free wood source for this job; ambientCG's older woods are mostly procedurally generated (`PBRProcedural`) and read more synthetic.

| Need (pile / office) | Candidate | URL | Size | Max | 2K | Method | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|---|
| Orange-grain 70s chest of drawers (Still A) | Teak Veneer | https://polyhaven.com/a/teak_veneer | 100x100 cm | 8K | 14.0 MB | photo | warm brown, fine grain, subtle knots, low sheen; push hue to orange in albedo grade | V | **USE** |
| same, alternative | Wood 092 (ambientCG) | https://ambientcg.com/a/Wood092 | 80x80 cm | 8K | 18.2 MB | photogrammetry (2024) | tagged orange/fine/smooth; one of the few ambientCG woods captured by photogrammetry (Planks021 is another) | V | **USE** (second orange) |
| Cherry desk + sideboard (Still A), hutch | Lacquered Cherry Wood | https://polyhaven.com/a/lacquered_cherry_wood | 100x100 cm | 16K | 11.5 MB | photo | glossy, reflective, subtle scratches: exactly the 80s/90s lacquered case-good look | V | **USE** |
| Dark wood cabinet/hutch leaning 45° (Still A) | Dark Wood | https://polyhaven.com/a/dark_wood | 200x200 cm | 8K | 13.8 MB | photo | dark cherry/mahogany, satin | V | **USE** |
| alt. red-brown varnished top | Wood Table 001 | https://polyhaven.com/a/wood_table_001 | 150x150 cm | 16K | 5.3 MB | photo | stained red-brown table, varnished glossy | V | MAYBE |
| Cherry, raw/blonde | Cherry Veneer | https://polyhaven.com/a/cherry_veneer | 100x100 cm | 8K | 9.8 MB | photo | blonde, unlacquered; too pale for 70s cherry unless graded | V | MAYBE |
| Open oak bookshelf, ladder-back chairs (Still B) | Red Oak Veneer | https://polyhaven.com/a/red_oak_veneer | 100x100 cm | 8K | 14.2 MB | photo | light oak, visible pores, the classic 80s "golden oak" when tinted | V | **USE** |
| oak, larger repeat | Oak Veneer 01 | https://polyhaven.com/a/oak_veneer_01 | 183x183 cm | 16K | 15.7 MB | photo | fine vertical grain, lightly glossy; bigger repeat hides tiling on long panels | V | MAYBE |
| Walnut (bar stools, dark furniture) | Walnut Veneer | https://polyhaven.com/a/walnut_veneer | 180x180 cm | 16K | 12.1 MB | photo | warm walnut, large repeat | V | **USE** |
| alt. walnut | American Walnut Veneer / Smoked Walnut Veneer | https://polyhaven.com/a/american_walnut_veneer , https://polyhaven.com/a/smoked_walnut_veneer | 100x100 cm | 8K | 13.4 / 10.0 MB | photo | grey-walnut / warm satin | V | MAYBE |
| Sapele / mahogany (sideboards) | Sapele Veneer 02 | https://polyhaven.com/a/sapele_veneer_02 | 100x100 cm | 8K | 11.0 MB | photo | reddish-brown fine stripe grain, typical of 80s office case goods | V | MAYBE |
| Plywood cabinets (Still B), unfinished doorway framing | Plywood | https://polyhaven.com/a/plywood | 50x50 cm | 8K | 19.5 MB | photo | light, low-sheen raw face. Plywood **edges** (ply stripes) are not in it | V | **USE** |
| Plywood edge strips | Wood 087 / 088 / 089 (ambientCG, tag "plywood, side") | https://ambientcg.com/a/Wood087 , https://ambientcg.com/a/Wood088 , https://ambientcg.com/a/Wood089 | not published | 8K | ~28 MB | procedural | ply laminations for cut edges; tile along U only | V | MAYBE (or GEN: 6 stripes is trivial) |
| Particle board (raw backs, shelf undersides, broken edges) | Chipboard 001-003 (with AO) / 004-008 | https://ambientcg.com/a/Chipboard001 … https://ambientcg.com/a/Chipboard008 | not published (assume ~1 m) | 8K | 28-33 MB | procedural | the only CC0 chipboard set; 001-003 ship AO | V | **USE** one (Chipboard004 as default) |
| OSB (pallet crate, back panels) | Oriented Strand Board | https://polyhaven.com/a/oriented_strand_board | 251x251 cm | 8K | 21.3 MB | photo | lacquered OSB; for the Still B crate on a pallet | V | MAYBE |
| Woodgrain laminate (cheap desks, filing-cabinet tops) | Laminate Floor 02 | https://polyhaven.com/a/laminate_floor_02 | 170x170 cm | 8K | 14.9 MB | photo | printed woodgrain with fine seams; seams are wrong for a desk top | V | REJECT → use a veneer albedo with laminate smoothness (0.55-0.65) and no pores in the normal |
| Pine (ladder-back chairs, cheap shelving) | Coated Pine / Stained Pine | https://polyhaven.com/a/coated_pine , https://polyhaven.com/a/stained_pine | 74 / 90 cm | 16K | 14.7 / 10.0 MB | photo | knotty varnished pine, plank seams in stained_pine | V | MAYBE |
| ambientCG procedural woods (Wood048-052, Wood021-030) | e.g. Wood049 (oak furniture), Wood051 (espresso), Wood052 (orange) | https://ambientcg.com/a/Wood049 , https://ambientcg.com/a/Wood051 , https://ambientcg.com/a/Wood052 | 80x80 cm (048-052) | 8K | 23-25 MB | procedural | usable, but the Poly Haven veneers beat them; keep only as fallback | V | REJECT (superseded) |

Fit notes: the furniture pile is lit by flat overhead troffers and viewed from 3-15 m, so grain direction and **sheen (smoothness)** matter more than micro detail; 1K is enough for small parts (stool legs, chair spindles), 2K for case goods. Every wood here is a flat face texture: end grain on cut edges should come from a separate small end-grain map or simply a darker tint on edge faces in the mesh.

### 3.2 Beige laminate desk tops

Office desk tops in the target image are **almond/putty high-pressure laminate** with a fine suede stipple and a dark T-mould or self-edge, not woodgrain. No CC0 library publishes a plain laminate (ambientCG search `laminate` → 0 results; Poly Haven has only laminate *floor*). Two routes:

| Candidate | URL | Note | V | Rec |
|---|---|---|---|---|
| Generate (`gen_surfaces.py`) | n/a | flat #CDBF9F-ish colour, 0.3 mm stipple normal (band noise), smoothness 0.35-0.45, plus macro wear for hand-polish patches at the user's seat. 30 lines of numpy on the existing helpers | n/a | **GEN** |
| Borrow the stipple from a plastic | Plastic 018A (ambientCG) | https://ambientcg.com/a/Plastic018A | grey plastic grain normal+roughness, tint albedo to almond; physical size not published | V | MAYBE |

### 3.3 Plastics: aged beige ABS (computer casing), black textured plastic

ambientCG is the only CC0 library with a plastic series (32 assets, nearly all Substance-procedural 2023 sets). Poly Haven has no plastic category.

| Need | Candidate | URL | Size | Max | 2K | Maps | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|---|
| Beige CRT/PC case (yellowed ABS) | Plastic 013B (white, scratched) | https://ambientcg.com/a/Plastic013B | n/p | 8K | 26.4 MB | Color, Normal, Rough, Disp | take normal+roughness; regrade albedo to #D8CFB8 → #C9BC97 yellowing (UV-yellowing is stronger on top faces: drive it with the world-up term in the shader or bake in Blender) | V | **USE** (normal/rough only) |
| Same, dirty variant | Plastic 018B (gray, dirty, scratched) | https://ambientcg.com/a/Plastic018B | n/p | 8K | 27.8 MB | same | grime already in the albedo, good for the photocopier and water cooler body | V | **USE** |
| Black textured plastic (keyboard, monitor bezel back, chair base, TV) | Plastic 012A / 012B (black / black scratched) | https://ambientcg.com/a/Plastic012A , https://ambientcg.com/a/Plastic012B | n/p | 8K | 26.7 / 26.8 MB | same | 012B for chair bases and the CRT TV; 012A for keyboards | V | **USE** 012B |
| Brown/light rough plastic (old casings) | Plastic 004 | https://ambientcg.com/a/Plastic004 | n/p | 4K | 24.9 MB | same | 2018 set, 4K max | V | MAYBE |

Fit note: casings are small (≤0.5 m), so 1K is enough; the readability comes from **roughness 0.45-0.6 with a slightly brighter edge** (handled by SSAO + a bevelled mesh), not the texture.

### 3.4 Metals: painted steel (putty / beige-grey), brushed aluminium

| Need | Candidate | URL | Size | Max | 2K | Maps | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|---|
| Painted steel: filing cabinets, desk frames, pedestals (putty/beige-grey, dark brown frames) | Metal 016 ("light, painted, rough, scratched, steel, white") | https://ambientcg.com/a/Metal016 | n/p | 8K | 24.7 MB | Color, Normal, Rough, Metalness, Disp | light painted scratched steel: tint albedo to putty #BDB6A2 or dark brown #3B2E25; scratches expose metal in the metalness map (good for the 5-star base and drawer pulls) | V | **USE** |
| Powder-coat black steel (chair columns, frames) | Metal 027 / 028 / 029 (black powder-covered painted steel) | https://ambientcg.com/a/Metal027 … /Metal029 | n/p | 8K | 25-27 MB | + Metalness | powder-coat orange peel normal is the right micro-surface for office steel of any colour | V | **USE** Metal028 (tint for any colour) |
| Old painted steel with rust (pile, basement) | Painted Metal 012 / 014 / 010 | https://ambientcg.com/a/PaintedMetal012 , /PaintedMetal014 , /PaintedMetal010 | n/p | 8K | 24-33 MB | + AO, Metalness | rust is wrong for a dry office; useful only for the pallet/crate corner | V | REJECT for office |
| Brushed aluminium (lamp poles, chair arms, torchiere, trims) | Metal 050A (clean aluminium) / 050C (rough scratched) | https://ambientcg.com/a/Metal050A , https://ambientcg.com/a/Metal050C | n/p | 8K | 6.8 / 10.7 MB | + Metalness | 2024 sets, small download | V | **USE** 050C |
| Painted steel, scratched (cgbookcase) | Painted Metal 01-03 / Scratched Painted Metal 01 | https://www.cgbookcase.com/textures/painted-metal-01 , https://www.cgbookcase.com/textures/scratched-painted-metal-01 | n/s | 4K | n/c | AO, Base Color, Height, Metallic, Normal (DX), Roughness (+ORM) | alternative to Metal016; DX normal | V | MAYBE |
| Brushed steel (linear) | Metal 009 / 011 / 012 (brushed, bumpy, scratches) | https://ambientcg.com/a/Metal009 | n/p | 8K | 16.7 MB | + Metalness | linear brushing; needs a mesh UV aligned to the brush direction | V | MAYBE |
| Circular brushed aluminium (knobs, lamp bases) | Metal 051A/B/C | https://ambientcg.com/a/Metal051A | n/p | 8K | 9.1 MB | + Metalness | radial brushing for round parts | V | MAYBE |
| Painted steel plate with scuffs | Blue Metal Plate (Poly Haven) | https://polyhaven.com/a/blue_metal_plate | 250x250 cm | 16K | 5.9 MB | all | blue paint; scuffs and seams are good, colour needs full regrade | V | MAYBE |

The in-house `PaintedMetal` (1024 px, scratch lines on noise) is acceptable for troffer pans but too clean for furniture.

### 3.5 Textiles: cubicle fabric, upholstery (pink velvet, teal woven, beige floral), leather / vinyl

Poly Haven published a fabric series on 2025-09-05 (capture method not stated in the API) (all ~27x27 cm, 8K+, all maps). Physical size is small, so for a sofa the repeat is visible unless the macro map breaks it up.

| Need | Candidate | URL | Size | Max | 2K | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|
| Cubicle panel fabric (blue-grey woven, Still/target) | Poly Wool Herringbone | https://polyhaven.com/a/poly_wool_herringbone | 27x28 cm | 8K | 22.7 MB | grey poly-wool, rough woven: the closest scanned match to Guilford-of-Maine style panel fabric; tint to #5F6B78 | V | **USE** |
| alt. | Rough Linen | https://polyhaven.com/a/rough_linen | 27x27 cm | 8K | 24.2 MB | rough blue linen crosshatch; already blue | V | **USE** (second cubicle colour) |
| alt. (ambientCG) | Fabric 031 ("grey, large, weave, wool, woven") / Fabric 030 (grey cloth, ships AO) | https://ambientcg.com/a/Fabric031 , https://ambientcg.com/a/Fabric030 | n/p | 4K | 32.5 / 38.0 MB | approximated from photos (2019); coarser weave than panel fabric | V | MAYBE |
| Pink velvet Queen-Anne armchair (Still A) | Velour Velvet | https://polyhaven.com/a/velour_velvet | 28x27 cm | 8K | 18.4 MB | red plush velour with patchy nap highlights; regrade hue to dusty pink; velvet needs a sheen/fresnel term the shader lacks (fake with lower smoothness + brighter grazing albedo) | V | **USE** |
| Teal woven club armchair (Still B) | Scuba Suede (turquoise) / Curly Teddy Checkered (teal) / Rough Linen (blue, regrade) | https://polyhaven.com/a/scuba_suede , https://polyhaven.com/a/curly_teddy_checkered | 29x28 / 56x47 cm | 8K / 14K | 22.8 / 15.2 MB | a 70s/80s club chair is a tight tweed or nubby woven; best = **Rough Linen or Poly Wool Herringbone regraded to teal**; teddy is too shaggy; suede is too smooth | V | **USE** rough_linen (regrade) |
| Beige floral jacquard/chenille sofa (Still B) | Floral Jacquard | https://polyhaven.com/a/floral_jacquard | 25x38 cm | 12K | 34.3 MB | black embossed floral jacquard: the **normal/height** is exactly a floral jacquard relief; the albedo is black, so rebuild the albedo from its height (beige ground, slightly darker motif, pastel print) | V | **USE** (normal + regraded albedo) |
| alt. | Quatrefoil Jacquard Fabric | https://polyhaven.com/a/quatrefoil_jacquard_fabric | 28x28 cm | 8K | 17.9 MB | burgundy brocade; strong pattern, read as "grandma sofa" | V | MAYBE |
| Nubby chenille/bouclé | Wool Boucle | https://polyhaven.com/a/wool_boucle | 31x39 cm | 12K | 26.2 MB | looped fibres, checker weave | V | MAYBE |
| Beige plain upholstery (chair seats) | Terlenka / Cotton Jersey | https://polyhaven.com/a/terlenka , https://polyhaven.com/a/cotton_jersey | 27 / 26 cm | 8K | 22.9 / 21.5 MB | beige fine weave | V | MAYBE |
| Ribbed corduroy (80s armchair variant) | Ribbed Corduroy | https://polyhaven.com/a/ribbed_corduroy | 27x27 cm | 8K | 22.9 MB | green wales | V | MAYBE |
| Black office-chair vinyl/leatherette | Leather 026 / 027 (black, smooth) | https://ambientcg.com/a/Leather026 , https://ambientcg.com/a/Leather027 | n/p | 8K | 24.0 / 23.0 MB | procedural black smooth leather grain; right for 90s task-chair vinyl | V | **USE** Leather027 |
| alt. black leather (cgbookcase) | Black Leather 01 / 02 | https://www.cgbookcase.com/textures/black-leather-01 | n/s | 4K | n/c | Base Color, Height, Normal (DX), Roughness | V | MAYBE |
| alt. scratched black | Leather 032 / 031 | https://ambientcg.com/a/Leather032 | 45x45 cm | 8K | 26.1 MB | black, scratched; physical size published | V | MAYBE |
| Brown aged leather (club chair, executive chair) | Fabric Leather 01 / Brown Leather | https://polyhaven.com/a/fabric_leather_01 , https://polyhaven.com/a/brown_leather | 40x40 cm | 8K | 12.3 / 12.4 MB | aged chestnut upholstery with stitching / matte vintage brown | V | MAYBE |
| Worn vinyl (scratched, scuffed) | Leather 014 (brown, old, scratches, scuffs, used, vintage) | https://ambientcg.com/a/Leather014 | n/p | 8K | 25.8 MB | approximated from photo | V | MAYBE |

### 3.6 Floor: blue-grey loop-pile carpet tiles

The target floor is 24" (0.6096 m) carpet tiles, quarter-turned, blue-grey, with per-tile tone shift and dark blotches. No CC0 library has a scanned *office carpet tile*. The in-house `office_carpet()` already models the quarter-turn striation, seams and flecks; what it lacks is a scanned pile micro-normal and believable soiling.

| Candidate | URL | Size | Max | 2K | Method | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|
| In-house `Office_CarpetTile` (gen_surfaces.py `office_carpet`) | local | 256/210 m tile pair | 2K | n/a | numpy | correct layout, repeat obeys the 256 rule; too uniform in value | n/a | **GEN (keep, improve)** |
| Blue Office Carpet Texture, TextureCan Fabric 0009 | https://texturecan.com/details/66 | not stated | 4K + SBSAR | n/c | Substance Designer | page text: parallel threads on each tile (i.e. quarter-turn tiles), dirt and worn areas; all maps incl. AO. Closest ready-made match to the target; tile size unknown, so measure the tile count in the image and set `_TileSize` accordingly | V | **USE** (A/B test against in-house) |
| Dirty Carpet (Poly Haven) | https://polyhaven.com/a/dirty_carpet | 60x60 cm | 8K | 21.1 MB | photo | scanned flattened, faded pile with grime; colour is olive-brown, so take **normal + roughness + AO** as the pile micro-detail and multiply the in-house blue-grey albedo by its luminance | V | **USE** (detail layer) |
| Carpet 012 (ambientCG, blue dark plain) | https://ambientcg.com/a/Carpet012 | n/p | 8K | 36.6 MB | procedural | plain dark-blue cut pile with AO; fallback micro-normal | V | MAYBE |
| Basic Carpet 01 (cgbookcase) | https://www.cgbookcase.com/textures/basic-carpet-01 | n/s | 4K | n/c | n/s | Base Color, Height, Normal (DX), Roughness; colour not readable from page text | V (page) | MAYBE |
| Carpet 006 (ambientCG, blue checker square) | https://ambientcg.com/a/Carpet006 | n/p | 8K | 41.3 MB | procedural | checker squares read as tiles but too graphic | V | REJECT |
| Fabric 022 / 023 (ambientCG, dark blue carpet) | https://ambientcg.com/a/Fabric022 , https://ambientcg.com/a/Fabric023 | n/p | 8K | 30-32 MB | procedural (from FabricSubstance006) | woven, too regular | V | REJECT |
| Carpet Floor 6 / Tiling 72 (ShareTextures) | https://sharetextures.com/textures/floor/carpet-floor-6 | n/c | 4K | n/c | "Approximated" (page data) | page is JS-rendered; colour/pattern could not be read | U | MAYBE (look in a browser first) |
| SummerEngine "carpet normal map", "office carpet albedo" (CC0) | https://www.summerengine.com/asset-store/carpet-normal-map-b8688475 | n/c | 4K | n/c | listing text reads like an image-generation prompt | provenance unclear, single maps only | U | REJECT |

### 3.7 Ceiling: 2'x2' mineral-fibre tiles and water stains

| Candidate | URL | Size | Max | 2K | Method | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|
| In-house `Office_Ceiling2x2` + shader water stains (`_StainStrength`, ring + pool from the macro map) | local | 256/210 m | 2K | n/a | numpy | right grid and repeat; the target's large **brown stain clouds** need a stronger, lower-frequency stain mask (macro map B/R at 8-12 m) | n/a | **GEN (keep, improve)** |
| Office Ceiling 001-006 (ambientCG) | https://ambientcg.com/a/OfficeCeiling001 … https://ambientcg.com/a/OfficeCeiling006 | 385 / 515 / 1000 / 1300 cm | 8K | 13-27 MB | procedural (API `creationMethod` = PBRProcedural) | whole ceilings with **lights baked in** (they ship an emission map); fixed light layout fights the game's own troffers and gives only ~530 px/m at 2K over 3.85 m. Use only as a look reference or to lift the T-bar/tile albedo | V | REJECT for direct use |
| Ceiling Drop Tiles 001 (3DTextures.me) | https://3dtextures.me/2019/03/27/ceiling-drop-tiles-001/ | n/s | 1K free (4K Patreon) | n/c | n/s | Diffuse, Normal, Displacement, Roughness, AO; 1K is below the in-house 2K | V | REJECT (resolution) |
| Ceiling Gypsum 001 (3DTextures.me) | https://3dtextures.me/2019/01/29/ceiling-gypsum-001/ | n/s | 1K free | n/c | n/s | gypsum, not mineral fibre | V | REJECT |
| False Ceiling SBSAR (ShareTextures) | https://www.sharetextures.com/textures/sbsar/false_ceiling_sbsar | n/c | SBSAR | n/c | Substance | needs Substance runtime to bake; ShareTextures licence restrictions | U | MAYBE |
| Polystyrene (Poly Haven) | https://polyhaven.com/a/polystyrene | 150x150 cm | 8K | 16.7 MB | photo | pitted, bead-like, discoloured white: a usable **scanned micro-normal for the tile face** (pinhole/fissure feel), not a tile layout | V | MAYBE (detail layer) |
| SummerEngine "Backrooms Ceiling - Damaged Acoustic Tiles" (CC0) | https://www.summerengine.com/asset-store/backrooms-ceiling-damaged-acoustic-tiles-05e7f307 | n/s | "4K" | n/c | listing text is an image prompt ("photorealistic, flat even diffuse lighting…"), 0 downloads | baked perspective/lighting risk, albedo only | V (page) | REJECT |
| Lightbeans "acoustic ceiling system" | https://lightbeans.com/en/textures/acoustic_ceiling_system | n/c | n/c | n/c | scanned (search snippet) | site returned HTTP 429 to the fetcher; licence not read | U | check in a browser |

Water stains: there is no CC0 *ceiling* tide-mark decal set; ambientCG `Leaking*` decals are vertical wall streaks. Keep stains procedural in the shader (they already exist) and add 4-6 hand-shaped stain-cloud masks to `gen_surfaces.py`.

### 3.8 Walls: drywall / knockdown paint, pinstripe wallpaper

| Candidate | URL | Size | Max | 2K | Method | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|
| Beige Wall 001 (Poly Haven) | https://polyhaven.com/a/beige_wall_001 | 300x300 cm | 16K | 3.2 MB (as listed) | photo | smooth beige painted plaster, soft colour variation and blemishes: this is the "near-invisible" wall of the target. 300 cm violates the 256 rule → `_TileSize` 256/85 = 3.0118 m | V | **USE** |
| Beige Wall 002 (Poly Haven) | https://polyhaven.com/a/beige_wall_002 | 300x300 cm | 32K | 1.1 MB (as listed) | photo | rough granular bumps: an orange-peel/knockdown stand-in | V | MAYBE |
| Painted Plaster 017 (ambientCG) | https://ambientcg.com/a/PaintedPlaster017 | n/p | 16K | 14.9 MB | photogrammetry | white painted plaster, tint to greige | V | MAYBE |
| White Stucco (Poly Haven) | https://polyhaven.com/a/white_stucco | 200x200 cm | 8K | 13.0 MB | photo | too coarse for office drywall | V | REJECT |
| In-house `Office_Drywall` (knockdown splatter) | local | 256/210 m | 1K | n/a | numpy | correct idea; 1K and low contrast | n/a | **GEN** (or replace by beige_wall_001) |
| Pinstripe wallpaper (Still A warm yellow, Still B olive) | none found: ambientCG wallpaper = woodchip only (Wallpaper001A/002A, https://ambientcg.com/a/Wallpaper001A); Poly Haven = `decrepit_wallpaper` (peeling) | – | – | – | – | – | V (absence) | **GEN** with the existing `wallpaper()` pipeline (vertical stripe ink instead of chevron) |

### 3.9 Frosted acrylic lens, glass with dust / smudges

| Need | Candidate | URL | Fit | V | Rec |
|---|---|---|---|---|---|
| Flat frosted 2'x4' lens (target) | none on the CC0 sites (ambientCG `glass` = facades only) | https://ambientcg.com/list?q=glass | the existing `lens()` already makes prismatic K12; a flat frosted lens is just albedo #EEEDE8 + soft emission falloff to the frame | V (absence) | **GEN** |
| Dust/smudge on glass, CRT screens, vending-machine front, interior window | Fingerprints 001-009, Smear 001-008, SurfaceImperfections 001/003/013 (ambientCG; ship Color + Normal + Roughness or Opacity) | https://ambientcg.com/a/Fingerprints002 , https://ambientcg.com/a/Smear007 , https://ambientcg.com/a/SurfaceImperfections013 | use as a **roughness modulation** on glass (dust raises roughness, fingerprints add streaks); 1K is enough. Fingerprints002 = 17.5 MB 2K, 4K max | V | **USE** 2-3 |
| Dust layer | SurfaceImperfections 014/015/016 ("dust") | https://ambientcg.com/a/SurfaceImperfections015 | 65x65 cm, ships opacity; for top-face dust on cabinets in the pile | V | **USE** 015 |

### 3.10 Cardboard, paper, blue painter's tape

| Need | Candidate | URL | Size | Max | 2K | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|
| Boxes, crate on pallet (Still B) | Cardboard Set 001 (atlas, photogrammetry 2024; pieces, tape, torn) | https://ambientcg.com/a/CardboardSet001 | 150x150 cm | 16K | 11.4 MB | scanned pieces with tape and AO + opacity; atlas, so UV boxes onto its regions | V | **USE** |
| Clean corrugated faces | Cardboard 002 / 004 | https://ambientcg.com/a/Cardboard002 | n/p | 8K | 23.3 MB | procedural, clean | V | **USE** one |
| Torn/broken | Cardboard 001 / 003 | https://ambientcg.com/a/Cardboard001 | n/p | 8K | 24.6 MB | | V | MAYBE |
| Paper stacks, loose sheets | Paper 001 (white) / Paper 003 (creased white) | https://ambientcg.com/a/Paper001 , https://ambientcg.com/a/Paper003 | n/p | 4K / 8K | 16.2 / 7.7 MB | stacks read by their **edge lines**, which are geometry/procedural; a creased sheet normal helps loose sheets only | V | MAYBE (Paper003) |
| Manila folders, envelopes | Paper 006 (beige-brown) | https://ambientcg.com/a/Paper006 | n/p | 8K | 17.9 MB | | V | MAYBE |
| **Blue painter's tape** (doorway outline, Still A) | none in blue. Closest: Tape 005 (light brown, rough packaging tape atlas, ships opacity) / Tape 004 | https://ambientcg.com/a/Tape005 | n/p | 8K | 12.2 MB | take Tape005's crepe normal + opacity edge, regrade albedo to painter's-tape blue (#2E86C1-ish); Tape003 is blue *police* tape with print → wrong | V | **GEN** (recolour Tape005) |

### 3.11 Raw pine studs / 2x4 lumber

| Candidate | URL | Size | Max | 2K | Method | Fit | V | Rec |
|---|---|---|---|---|---|---|---|---|
| Wood 096 (ambientCG; beige, knots, light, natural, softwood) | https://ambientcg.com/a/Wood096 | 50x50 cm | 8K | 19.6 MB | approximated (released 2026-09-30) | light softwood with knots = SPF stud lumber | V | **USE** |
| Planks 021 (ambientCG; raw, rough, yellow) | https://ambientcg.com/a/Planks021 | 140x140 cm | 8K | 24.3 MB | photogrammetry, with AO | rough-sawn yellow planks; good for the pallet | V | **USE** (pallet) |
| Coated Pine (Poly Haven) | https://polyhaven.com/a/coated_pine | 74x74 cm | 16K | 14.7 MB | photo | glossy varnished: wrong for raw studs, right for pine furniture | V | REJECT for studs |
| Hinoki / Japanese cedar planks (Poly Haven) | https://polyhaven.com/a/hinoki_planks | 189 cm | 16K | n/c | photo | pale raw wood, plank layout | V | MAYBE |

Studs are 38x89 mm, so the texture only needs ~1 m of grain along the length; the end grain and the grade stamp ("SPF S-DRY") are better as a tiny generated decal.

### 3.12 Decals: scuffs, water stains, dust, grime, leaks

ambientCG has 127 assets of type `Decal` (API `type=Decal`): Leaking (39), RoadLines (69), ManholeCover (11), ChewingGum, Door, AsphaltDamage, PavingEdge, TireTracks. Indoor-useful ones, plus the "imperfection" materials that ship an opacity map:

| Need | Candidate | URL | Maps | 2K | Fit | V | Rec |
|---|---|---|---|---|---|---|---|
| Wall streaks under the ceiling / interior window (Run & Office) | Leaking 001-006 (moisture streaks, smudge) | https://ambientcg.com/a/Leaking001 , https://ambientcg.com/a/Leaking006 | Color, Normal, Rough, Disp, Opacity | 11.4 / 5.1 MB | URP Decal Projector; 2-3 variants are enough | V | **USE** 2 |
| Floor / carpet stains | SurfaceImperfections 001 (water stains) / 013 (stains) | https://ambientcg.com/a/SurfaceImperfections001 , https://ambientcg.com/a/SurfaceImperfections013 | Color, Normal, Opacity | 18.1 / 23.1 MB | atlas of blotches; cut 6-8 stains into a decal atlas | V | **USE** |
| Dirt / grime overlay | SurfaceImperfections 008 (dirt, rough smear) / 017-020 (dirt overlay) | https://ambientcg.com/a/SurfaceImperfections008 | Color, Normal, Opacity | 20.6 MB | | V | MAYBE |
| Scratches / scuffs on desks, steel, plastic | Scratches 005 / 003 | https://ambientcg.com/a/Scratches005 | Color, Normal, Opacity | 22.9 MB | use as a mask into roughness+albedo, not as projected decals | V | **USE** |
| Coffee rings on desks | SurfaceImperfections 007 (coffee, cup, mug, rings, stains) | https://ambientcg.com/a/SurfaceImperfections007 | Color, Normal, Opacity | 8.0 MB | the one cliché worth having on the target's desks | V | **USE** |
| Chewing gum on carpet | ChewingGum 001/002 | https://ambientcg.com/a/ChewingGum001 | Color, Disp, Normal, Rough, Opacity, AO | 5.7 MB | floor gum; a few on the carpet near the vending machine is a nice touch, otherwise skip | V | MAYBE |
| Liquid stains, dust wipes, dirt dust, smudges (cgbookcase) | Liquid Stains 01-03, Dust Wipes 01, Dirt Dust 01, Smudges 01, Fingerprints 01-07 | https://www.cgbookcase.com/textures/liquid-stains-01 , https://www.cgbookcase.com/textures/dust-wipes-01 , https://www.cgbookcase.com/textures/dirt-dust-01 , https://www.cgbookcase.com/textures/smudges-01 | up to 4K (Dust Wipes 3K) | n/c | Liquid Stains = carpet/desk spill masks; Dust Wipes = wiped-dust pattern for desk tops and CRT screens | V | **USE** Liquid Stains 01 + Dust Wipes 01 |

URP note: `Assets/Settings/FrontRooms_URP_Renderer.asset` currently has only the Screen Space Ambient Occlusion feature, so the URP **Decal Renderer Feature** must be added before any Decal Projector renders. Per the [URP decal manual](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-feature-decal.html) decals bypass the SRP Batcher (material property blocks; use GPU instancing and atlases) and the projection does not work on transparent surfaces, so glass smudges must live in the glass material, not in a projector. Cheaper: bake stains into the existing `MacroWear_M` / per-surface masks and keep projectors for a few hero spots.

## 4. Download vs generate: decision matrix

What `gen_surfaces.py` can and cannot do (read 2026-10-02): it composes spectral (1/f) noise, band-limited noise, Gaussian blur, PIL line drawing with wrap-around, Lanczos resize, a duotone remap of a CC0 reference image (the chevron wallpaper), and height→normal. Outputs are `_A` (albedo), `_N` (GL normal), `_S` (R smoothness, G cavity, B wet) and `_E`. It is very good at **dimensioned man-made layouts** (tile grids, seams, T-bars, prism lenses, printed repeats) and at **soft wear**. It has no model of wood figure, weave interlacing, fibre nap or leather grain; those come out as noise, which is exactly why Codex's 512-px `OfficeFurniture_Wood/Vinyl` (value noise, stdlib only) reads flat.

Rule used below:
- **Download** when the read is a natural micro-structure that noise fakes badly (wood figure and pores, woven/jacquard relief, velvet nap, leather grain, powder-coat orange peel, scanned plaster), and the surface is a prop with mesh UVs (no 256-m constraint).
- **Generate** when the read is a layout tied to real dimensions (24" tiles, 2'x2' grid, wallpaper roll width, lens prisms), when it must obey the 256-m repeat rule, when the colour must be art-directed per room, or when no CC0 source exists.
- **Hybrid** = bake a downloaded CC0 micro-map into the procedural layout inside `gen_surfaces.py` (the wallpaper function already does this with a CC0 image), so the shader stays one-normal-map and nothing changes at runtime.

| Material | Decision | Why |
|---|---|---|
| Teak / cherry / oak / walnut / dark wood / sapele case goods | **Download** (Poly Haven veneers) | real wood figure + pores; furniture is mesh-UV'd |
| Woodgrain laminate | **Download + regrade** (veneer albedo, smoothness 0.55-0.65, pores removed from normal) | printed laminate is a photo of wood under a flat clear coat |
| Plywood face / particle board / OSB | **Download** | chip and veneer structure is irregular |
| Plywood edge stripes | **Generate** | 5-7 straight laminations; trivial |
| Beige laminate desk top | **Generate** | no CC0 source; flat colour + stipple + hand-polish wear |
| Aged beige ABS | **Hybrid** (ambientCG plastic normal/roughness + generated yellowing albedo) | yellowing must be art-directed, grain must look moulded |
| Black textured plastic | **Download** (Plastic012B) | |
| Painted steel (putty, dark brown) | **Download + tint** (Metal028 powder-coat / Metal016) | orange-peel and scratch-to-metal are hard to fake |
| Brushed aluminium | **Download** (Metal050C) | anisotropic look is in the normal/roughness |
| Cubicle fabric | **Download + tint** (poly_wool_herringbone / rough_linen) — replaces in-house `Office_CubicleFabric` | the current sin()-weave reads like a grid |
| Pink velvet, teal woven, floral jacquard sofa | **Download + regrade**; floral sofa = **Hybrid** (jacquard height → new beige albedo) | |
| Office-chair vinyl, leather | **Download** (Leather027) | |
| Carpet tiles | **Hybrid**: keep in-house quarter-turn layout and 256/420 m tile, multiply in `dirty_carpet` normal/roughness/AO, add per-tile tone and blotches; A/B against TextureCan Blue Office Carpet | layout must stay on the world grid |
| 2'x2' ceiling tiles | **Generate** (keep) + optional `polystyrene` pits as micro-normal; stain clouds stay procedural | ambientCG ceilings bake lights; no CC0 tile scan at ≥2K |
| Drywall | **Download** `beige_wall_001` (or keep `Office_Drywall`) | scanned paint blemish beats noise; set `_TileSize` 3.0118 m |
| Pinstripe wallpaper (Stills A/B) | **Generate** (`wallpaper()` with stripe ink) | no CC0 source; must match roll width and the 256 rule |
| Frosted flat lens | **Generate** (variant of `lens()`) | trivial; emission must match the ballast logic |
| Glass dust/smudges | **Download** (Fingerprints002, Smear007, Dust Wipes 01) as roughness masks | |
| Cardboard, crates | **Download** (CardboardSet001, Cardboard002) | |
| Paper stacks | **Generate** (edge lines + flat white) | a stack is read by its edges |
| Blue painter's tape | **Hybrid** (Tape005 crepe normal + opacity, blue albedo) | no blue CC0 tape |
| Raw pine studs / pallet | **Download** (Wood096, Planks021) | knots and sawn grain |
| Stain / leak / scuff decals | **Download** (ambientCG Leaking, SurfaceImperfections, Scratches; cgbookcase Liquid Stains) | real stain edges (tide lines) are hard to fake; ceiling stain clouds stay procedural |
| Macro wear | **Generate** (keep `MacroWear_M`) | world-space, already wired into the shader |

Copy-paste piles: because `MacroWear_M` and the stain terms are sampled in world space, two copies of the same chest of drawers at different positions already receive different discolouration. Add only 2-3 tint variants per wood material (not per-renderer MaterialPropertyBlocks, which break SRP batching) to sell "different pieces from the same catalogue".

## 5. Import / conversion recipe (Blender headless + numpy, no manual steps)

1. **Download** (after Red approves): ambientCG zips come from the API field `downloadFolders…downloads[].downloadLink`, e.g. `https://ambientcg.com/get?file=Wood092_2K-JPG.zip`; Poly Haven per-map JPGs come from `https://api.polyhaven.com/files/<id>` → `[map][2k][jpg].url`, e.g. `https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/teak_veneer/teak_veneer_nor_gl_2k.jpg` (verified in the API, not downloaded). For Poly Haven fetch only `Diffuse`, `nor_gl`, `arm` (teak: 2.5 + 1.9 + 3.4 MB = 7.9 MB at 2K, about half of the full set). Put raw files outside `Assets/` (e.g. `Tools/lookdev/cc0_src/<source>/<id>/`) so Unity never imports them twice.
2. **Pack** with a new `Tools/lookdev/import_cc0.py` that reuses `gen_common.py`:
   - `_A` = Diffuse/Color, optionally regraded to a target hex in linear space (`srgb_to_lin` → match mean/hue → `lin_to_srgb`), resized to 1K (small props) or 2K (case goods, fabrics, floor);
   - `_N` = `nor_gl` / `NormalGL` as is; cgbookcase normals are DirectX → invert G;
   - `_S` = R `1 − roughness` (Poly Haven: `1 − arm.G`), G = AO (`arm.R`; ambientCG sets without AO → cavity from `blur(height) − height`, the same trick `gen_surfaces.py` uses), B = 0, A = 1;
   - append one line per asset to `Tools/lookdev/ref/LICENSE.txt` (name, URL, licence, date).
3. **Materials**: one `FrontRooms/Surface` material per packed set with `_FR_MESH_UV` on and `_TileSize` = the published physical size (Poly Haven veneers 1.0 m, walnut_veneer 1.8 m, velour 0.28 m, poly_wool_herringbone 0.27 m, Wood092 0.8 m, CardboardSet001 1.5 m, Wood096 0.5 m). For ambientCG assets with no published size, use 1.0 m and adjust by eye once.
4. **Blender (headless, 4.3)**: unwrap props so **1 UV unit = 1 m** (Cube Projection, cube size 1.0, "Scale to Bounds" off, "Correct Aspect" on), grain direction along the long axis of each board, so the shader's metre-based tiling is right with no per-mesh fiddling. Export FBX with tangents.
5. **Unity import**: albedo sRGB; `_N` as Normal Map; `_S` linear (sRGB off); Max Size 1024/2048; ASTC 6x6 (Apple Silicon) or BC7; mipmaps on with "Preserve Coverage" off.

## 6. Shopping list (approve once, download once)

All CC0 (ambientCG, Poly Haven) unless noted. Sizes are the published 2K totals (ambientCG zip / Poly Haven all maps); Poly Haven three-map downloads are about half.

**Tier 1 – furniture (makes the props stop looking boxy and flat-coloured)**

| # | Asset | Source / URL | Res | Size |
|---|---|---|---|---|
| 1 | teak_veneer | https://polyhaven.com/a/teak_veneer | 2K | 14.0 MB |
| 2 | lacquered_cherry_wood | https://polyhaven.com/a/lacquered_cherry_wood | 2K | 11.5 MB |
| 3 | dark_wood | https://polyhaven.com/a/dark_wood | 2K | 13.8 MB |
| 4 | red_oak_veneer | https://polyhaven.com/a/red_oak_veneer | 2K | 14.2 MB |
| 5 | walnut_veneer | https://polyhaven.com/a/walnut_veneer | 2K | 12.1 MB |
| 6 | plywood | https://polyhaven.com/a/plywood | 2K | 19.5 MB |
| 7 | Wood092 (orange) | https://ambientcg.com/a/Wood092 | 2K | 18.2 MB |
| 8 | Chipboard004 | https://ambientcg.com/a/Chipboard004 | 1K | 8.0 MB |
| 9 | Plastic013B (beige ABS base) | https://ambientcg.com/a/Plastic013B | 1K | 6.5 MB |
| 10 | Plastic018B (dirty grey) | https://ambientcg.com/a/Plastic018B | 1K | 6.8 MB |
| 11 | Plastic012B (black) | https://ambientcg.com/a/Plastic012B | 1K | 6.5 MB |
| 12 | Metal028 (powder-coat) | https://ambientcg.com/a/Metal028 | 1K | 7.0 MB |
| 13 | Metal016 (light painted scratched steel) | https://ambientcg.com/a/Metal016 | 1K | 7.3 MB |
| 14 | Metal050C (aluminium) | https://ambientcg.com/a/Metal050C | 1K | 3.6 MB |
| 15 | poly_wool_herringbone | https://polyhaven.com/a/poly_wool_herringbone | 2K | 22.7 MB |
| 16 | rough_linen | https://polyhaven.com/a/rough_linen | 2K | 24.2 MB |
| 17 | velour_velvet | https://polyhaven.com/a/velour_velvet | 2K | 18.4 MB |
| 18 | floral_jacquard | https://polyhaven.com/a/floral_jacquard | 2K | 34.3 MB |
| 19 | Leather027 | https://ambientcg.com/a/Leather027 | 1K | 6.6 MB |
| | **Tier 1 total** | | | **≈ 255 MB** (≈ 160 MB with Poly Haven three-map downloads) |

**Tier 2 – room shell detail, pile extras, decals (decals at 1K)**

| # | Asset | Source / URL | Res | Size |
|---|---|---|---|---|
| 20 | dirty_carpet (pile detail layer) | https://polyhaven.com/a/dirty_carpet | 2K | 21.1 MB |
| 21 | Blue Office Carpet (A/B test) | https://texturecan.com/details/66 (CC0) | 2K | not published |
| 22 | beige_wall_001 | https://polyhaven.com/a/beige_wall_001 | 2K | 3.2 MB (as listed by API) |
| 23 | polystyrene (ceiling pits) | https://polyhaven.com/a/polystyrene | 2K | 16.7 MB |
| 24 | CardboardSet001 | https://ambientcg.com/a/CardboardSet001 | 2K | 11.4 MB |
| 25 | Cardboard002 | https://ambientcg.com/a/Cardboard002 | 1K | 6.0 MB |
| 26 | Wood096 (studs) | https://ambientcg.com/a/Wood096 | 1K | 5.4 MB |
| 27 | Planks021 (pallet) | https://ambientcg.com/a/Planks021 | 1K | 7.1 MB |
| 28 | Tape005 (→ blue tape) | https://ambientcg.com/a/Tape005 | 1K | 3.9 MB |
| 29 | Leaking001, Leaking006 | https://ambientcg.com/a/Leaking001 , https://ambientcg.com/a/Leaking006 | 1K | 3.9 + 2.2 MB |
| 30 | SurfaceImperfections001, 013, 007, 015 | https://ambientcg.com/a/SurfaceImperfections013 (etc.) | 1K | 4.8 + 7.0 + 3.4 + 8.2 MB |
| 31 | Fingerprints002, Smear007 | https://ambientcg.com/a/Fingerprints002 , https://ambientcg.com/a/Smear007 | 1K | 5.2 + 8.4 MB |
| 32 | Scratches005 | https://ambientcg.com/a/Scratches005 | 1K | 6.4 MB |
| 33 | Liquid Stains 01, Dust Wipes 01 (cgbookcase, CC0) | https://www.cgbookcase.com/textures/liquid-stains-01 , https://www.cgbookcase.com/textures/dust-wipes-01 | 1K | not published |
| | **Tier 2 total (known sizes)** | | | **≈ 124 MB** |

**Tier 3 – optional variety** (only if a pile piece needs it): sapele_veneer_02, oak_veneer_01, american_walnut_veneer, coated_pine, oriented_strand_board, wool_boucle, quatrefoil_jacquard_fabric, terlenka, fabric_leather_01, Leather014, beige_wall_002, PaintedPlaster017, Metal051A, Paper003, Paper006 (URLs in §3).

## 7. Gaps (nothing acceptable to download; must be generated or modelled)

- **Beige/almond plain laminate** for desk tops (no CC0 plain laminate anywhere checked).
- **2'x2' fissured mineral-fibre ceiling tile at ≥2K** with no baked lights (ambientCG ceilings bake lights; 3DTextures.me is 1K free; others unverified or AI-generated).
- **Ceiling water-stain clouds / tide marks** as a CC0 decal set (only vertical wall leaks exist).
- **Office 24" carpet tile** as a scan (only Substance-made TextureCan and generic carpets).
- **Pinstripe vinyl wallpaper** (warm yellow / olive) for the film-style halls.
- **Flat frosted acrylic troffer lens** (trivial to generate).
- **Blue painter's tape** (recolour Tape005).
- **Velvet sheen**: the texture exists, but the shader has no sheen lobe; fake it or add a fresnel-tinted albedo term to `FrontRooms/Surface` later.
- **Plywood edge laminations, stud grade stamps, paper-stack edges, CRT screen phosphor/curvature, vending-machine snack labels** (labels must be invented, never copied from real brands).

## 8. Sources

Licences: https://docs.ambientcg.com/license/ · https://polyhaven.com/license · https://3dtextures.me/about/ · https://texturecan.com/terms/ · https://www.cgbookcase.com/ and https://www.cgbookcase.com/textures/ · https://www.sharetextures.com/p/license · https://freepbr.com/about-free-pbr/ · https://www.textures.com/faq-license (did not render; UNVERIFIED) · https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/ (Megascans pricing, UNVERIFIED in this run).

APIs used for metadata (read-only JSON, nothing downloaded): https://ambientcg.com/api/v2/full_json (queries `q=`, `id=`, `type=Decal`, `include=downloadData,mapData,dimensionsData,tagData`) · https://api.polyhaven.com/assets?t=textures · https://api.polyhaven.com/info/<id> · https://api.polyhaven.com/files/<id>.

Asset pages: every URL in §3 and §6. Other pages read: https://texturecan.com/details/66 · https://3dtextures.me/2019/03/27/ceiling-drop-tiles-001/ · https://3dtextures.me/2019/01/29/ceiling-gypsum-001/ · https://3dtextures.me/?s=fabric · https://www.cgbookcase.com/textures/basic-carpet-01 (and the other cgbookcase pages in §3) · https://www.summerengine.com/asset-store/backrooms-ceiling-damaged-acoustic-tiles-05e7f307 · https://www.sharetextures.com/textures/sbsar/false_ceiling_sbsar · https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-feature-decal.html.

Project files read: `Frontrooms3D/Tools/lookdev/gen_surfaces.py`, `gen_common.py`, `gen_office_furniture_textures.py`, `Assets/Resources/Rendering/FrontRoomsSurface.shader`, `Assets/Settings/FrontRooms_URP_Renderer.asset`, `Documentation/VISUAL_RESEARCH_LOOKDEV.md`, `Documentation/OFFICE_LEVEL_FURNITURE_RESEARCH.md`, `Verification/lookdev/2_Office_forward.png`, `scratchpad/research/ref_office_target.png`.
