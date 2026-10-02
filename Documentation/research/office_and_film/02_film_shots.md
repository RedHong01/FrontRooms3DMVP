# 02 — Backrooms (A24, 2026) furniture shot catalogue and game landing

Research date: 2026-10-02. Scope: shots/stills/set photos from Kane Parsons' A24 feature *Backrooms* (2026) and its marketing (teaser, trailer, featurettes, press stills, BTS set photography) that contain furniture, furniture piles, distorted / duplicated / embedded furniture, offices, columns and doorways. Purpose: an art-direction catalogue for FrontRooms (Unity 6000.3 / URP 17.3) Office level and `FrontRoomsFurniturePile.Build(...)`.

Rules followed: no image, model or texture was downloaded or saved to disk. Image URLs are recorded only as references. Stills are not to be copied into the project. Status tags per entry:
- **VIEWED** = I looked at the image itself in the in-app browser (viewing only).
- **DESCRIBED** = I only have caption / alt text / article prose ("described, not viewed").
- **UNVERIFIED** = lead from search snippet, not confirmed on the page.

## 0. Status / progress log
- 2026-10-02: catalogue complete for this pass — 0A/0B identified and decomposed, 19 press/BTS entries (F01–F19), 9 trailer entries (T01–T09), 4 teaser entries (TT01–TT04), 8 archetypes, landing rules. Remaining gaps in §6.
- Key discovery: Red's two stills are **BTS photographs of real built sets** (0A = Dezeen/Wendigoon; 0B = Fast Company Brasil scan of the same pile that appears warm-graded in Surface/Galerie/Dwell/Curbed and in the trailer at 0:31).

## 1. Sources checked (with verification status)
| Source | Status | What it gave |
|---|---|---|
| [Dezeen 2026-05-29](https://www.dezeen.com/2026/05/29/backrooms-production-design-danny-vermette-interview/) | Read + images VIEWED in browser (WebFetch 403) | **STILL A source** (col_10, BTS by Wendigoon), raked floor, store BTS, quotes on sinking furniture / doorways halfway up walls / Async HQ |
| [Surface 2026-06-16](https://www.surfacemag.com/articles/a24-backrooms-production-design/) | WebFetch + 5 images VIEWED | pile F01, showroom F04, corridor F05 (trailer 0:43), F06 (film 00:37:55), mannequins F07; "thirty-nine of the same chair" |
| [Fast Company Brasil 2026-06-05](https://fastcompanybrasil.com/design/backrooms-como-a-a24-deu-vida-ao-lugar-mais-assustador-da-internet/) | images VIEWED (text from prior run, not re-fetched) | **STILL B source** (TB_Scans_00108), raked floor KV-40 |
| [Galerie 2026-06-15](https://galeriemagazine.com/how-horror-hit-backrooms-terrorizes-viewers-with-design/) | WebFetch + browser; 4 images VIEWED | pile credit (Moutsokapas), throne/shoes hatch shot, Mary's office, Sears-catalogue quote |
| [Curbed 2026-05-28](https://www.curbed.com/article/backrooms-kane-pixels-a24-set-production-design-interview.html) | Full text read in browser (WebFetch blocked); 7 images VIEWED | sourcing, 350 troffers, cut shoes / tipping throne, captions |
| [Dwell](https://www.dwell.com/article/backrooms-a24-production-design-5cc5d402) | Text read in browser (WebFetch 502); 3 images VIEWED | La-Z-Boys, maple sets, "delicate piles", awkward columns |
| [W Magazine 2026-06-12](https://www.wmagazine.com/culture/backrooms-a24-movie-set-design-details-interview) | WebFetch | palette shift greys/blues → beige; mint '90s furniture |
| [Man of Many](https://manofmany.com/entertainment/movies-tv/backrooms-trailer-a24-explained) | WebFetch + 5 images VIEWED | F17 camcorder pile frame, F18 armchair, trailer ID |
| [Official Trailer](https://www.youtube.com/watch?v=0HjdiohVOik) | Scrubbed in browser, ~70 frames VIEWED | T01–T09 with timestamps |
| [Official Teaser](https://www.youtube.com/watch?v=tKGhxMi50y8) | Scrubbed in browser, ~30 frames VIEWED | TT01–TT04 |
| [The Credits / motionpictures.org](https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/) | prior-run extraction only — UNVERIFIED this run | still filenames with film timecodes (00:36:24, 01:28:15, 00:15:54), platforms/slopes quote |
| [Moria Reviews](https://moriareviews.com/sciencefiction/backrooms-2026.htm) | prior-run extraction only — UNVERIFIED this run | list of embedded-furniture rooms |
| IMDb gallery, Letterboxd backdrops, FilmGrab, ShotDeck stills, A24 Instagram, Kane Parsons socials, ASC article, A24 Notes interview, Blu-ray featurettes | NOT CHECKED this run (budget) | see §6 |

## 2. What production says about the furniture (verified facts that shape the archetypes)

Verified on-page (all quotes < 15 words):

- **Furniture came from real 1990s stock, mint condition, colour-curated.** Vermette had "almost a spectrum of furniture colors" in mind; buyer Eric Cairns sourced on Facebook Marketplace and found "a lot of red couches" at a local hotel liquidator; 1990s lamps were wanted "in pairs with intact shades"; sofas for Dr. Kline's office/living room were chosen for soft pastels and wood-trim detailing. Source: [Curbed, Adriane Quinlan, 2026-05-28](https://www.curbed.com/article/backrooms-kane-pixels-a24-set-production-design-interview.html) (read in-browser; WebFetch is blocked for curbed.com).
- **Embedded/cut props were hand-made.** Vermette: "I was cutting shoes in half"; the hard part of half-objects is making them balance, e.g. an oversize throne tipping over; he built a flamingo for the pool room himself. Same Curbed page. → In-game: half-meshes (cut at the wall/floor plane) are an authentic film technique, not a cheat.
- **Repeated identical chairs are the backbone of the piles.** Surface: "thirty-nine of the same chair" found in one haul and reused "as oddities, barriers, and the bones of nonsensical creations"; towers of furniture act as landmarks; sourcing from estate sales, clearance spots, hotel liquidators and Facebook Marketplace. Source: [Surface, Abigail Saldana, 2026-06-16](https://www.surfacemag.com/articles/a24-backrooms-production-design/).
- **Lighting is a built grid of 350 custom troffers.** Vermette: two LED tubes suspended ~3 ft above a lens on each troffer, all built from scratch, "350 of them", grid built before walls. Source: Curbed (above). Visual check (F12/F13): the lenses read as **flat opal/frosted white**, not prismatic — this contradicts the "prismatic K12" note in our `VISUAL_RESEARCH_LOOKDEV.md`; for the film look use a flat diffuse lens with a soft falloff to the frame edge.
- **Budget/scale:** under $1M build, 30,000 sq ft over four soundstages vs. ~100,000 sq ft in Parsons' Blender plan; the showroom basement was the largest continuous set. Source: Curbed.
- **The real showroom location had its black ceiling painted white** (Vancouver suburb). Source: Curbed caption + text.
- **Era/fabrics:** "mint condition '90s" furniture, nostalgia via fabrics and patterns in neutral tones; palette moves from the sad greys and blues upstairs to near-neutral beige below. Source: [W Magazine, 2026-06-12](https://www.wmagazine.com/culture/backrooms-a24-movie-set-design-details-interview).
- **Sears-catalogue logic:** Vermette likened the look to a Sears catalog with page after page of couches; Eric Cairns sourced "vintage finds in mint condition" for Clark's showroom and Mary's office/home. Source: [Galerie, Mandi Bierly, 2026-06-15](https://galeriemagazine.com/how-horror-hit-backrooms-terrorizes-viewers-with-design/).
- **Platforms and slopes:** sets on platforms "going down slopes and weird angles"; separate wall portals for talent and camera. Source: [The Credits / motionpictures.org](https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/) (per prior run's extraction; UNVERIFIED this run). Surface mentions sets on 15-foot risers connected by ramps (prior-run extraction; UNVERIFIED this run).
- **Embedded furniture exists in the cut:** a review lists "rooms with couches and furniture buried in the midst of floors and walls", shoes "standing upright embedded in the carpet", wall cabinets running the length of a hall, rooms of low-hanging chandeliers, a reversed stop sign, doors in ceilings and wedge alcoves with tiny doors. Source: [Moria Reviews](https://moriareviews.com/sciencefiction/backrooms-2026.htm) (prior-run extraction; UNVERIFIED this run).
- **Dwell (read in-browser; WebFetch returned 502):** the store has bulging La-Z-Boy recliners, maple bedroom and dining sets, hand-painted EVERYTHING MUST GO signage, "awkward columns and too-bright fluorescent lighting"; the backrooms' large rooms host remnants such as "piled furniture, a lit-up Christmas tree, a rotting swimming pool"; furniture exists only "to be amassed and arranged in delicate piles"; a photo caption says furniture in the backrooms serves no purpose other than visual stimuli. Source: [Dwell, Anjulie Rao](https://www.dwell.com/article/backrooms-a24-production-design-5cc5d402). → In-game: piles should look *arranged* (delicate balance), not dumped.
- **Dezeen (read in-browser; WebFetch 403):** sets include "doorways halfway up the wall", raked floors, and "an incongruous piece of furniture sinking into the carpet"; finite sets on 20-foot risers with real slopes (squeezing through crevasses, crawling tunnels); set decorator **Trevor Johnston** assembled the 1990s "most unaesthetic fabrics, fashions and furniture" for the store and Mary's office; the store has "floating furniture and chaotic sale signs"; the **Async HQ is inspired by 90s data centres and their drab beige-ness**. Source: [Dezeen, 2026-05-29](https://www.dezeen.com/2026/05/29/backrooms-production-design-danny-vermette-interview/).

## 3. Shot catalogue

### 0A — Red's STILL A (warm hall, centre pile, blue-tape doorway) — SOURCE FOUND + VIEWED
- **Source identified:** [Dezeen, Rima Sabina Aouf, "Architects will 'cringe a bit' at design horrors in Backrooms", 2026-05-29](https://www.dezeen.com/2026/05/29/backrooms-production-design-danny-vermette-interview/) (WebFetch gets 403; read in the in-app browser). Image: `https://static.dezeen.com/uploads/2026/05/backrooms-danny-vermette-interview-behind-the-scenes-design_dezeen_2364_col_10-852x564.jpg`. Alt text: behind-the-scenes photo of the set with furniture piled up in the middle of a room. Caption: about the effort on carpet and wallpaper, **"Behind-the-scenes photo by Wendigoon"** (the YouTuber visited the set). So STILL A is a BTS photograph of a real built set, shot on film — not a VFX frame.
- **Room shell:** very large open hall (>15 m deep), 2'x2' lay-in ceiling with 2'x4' flat-lens troffers on a regular ~2.4 m grid (every second tile row, staggered 2 columns); ceiling ~2.7 m. Warm yellow wallpaper with faint vertical pinstripe / small motif; a **dark wood chair rail at ~0.9 m** running along the left wall and continuing on a free-standing wall section; a **square column/pilaster** at left (~0.6 m) that the chair rail wraps; pale beige cut-pile carpet, seamless.
- **Pile decomposition (left → right), every piece intact, nothing broken:**
  1. **Two-tier turned-leg side/serving table on casters** (dark walnut, 4 bobbin-turned legs, lower shelf) — upright, standing 1 m in front of the pile, the "escapee".
  2. **Cherry/mahogany pedestal desk** (veneer, 3 drawers facing camera) — upright, the left anchor; a **sideboard/credenza** behind it, also upright.
  3. **Queen-Anne / French bergère-style armchair** — pale pink/blush velvet, exposed walnut frame, cabriole legs — tipped back ~15–20° onto the desk edge.
  4. **Dark (near-black lacquer/ebonised) hutch or armoire** leaning ~45° with its back panel toward camera, forming the dark triangular peak of the pile — the silhouette anchor.
  5. **Two-drawer nightstand** (orange-brown grain, brass ring pulls) rotated ~90° on its side in the centre-front, wedged under the hutch.
  6. **Brown ceramic urn / bulb vase** lying on its side in the middle.
  7. **Pleated-shade table lamp** (cream drum shade, brass/ceramic base) sitting upright on top, lamp off.
  8. **Tall 5-drawer chest of drawers** (honey/orange oak or teak grain) **tipped ~40° onto its front corner**, leaning on the pile — the biggest diagonal.
  9. **Low cherry chest / dresser** behind it, and a **beige-grey 2-drawer steel filing cabinet** half-hidden at the back right.
  10. **Wooden bar stool** (4-leg, rungs) standing alone at the far right.
  11. **Small rolling cabinet / mini-bar on casters** (veneer cube with a door) standing alone at right.
- **Doorway (right wall):** a door-sized opening framed with **exposed vertical wood studs** (unfinished framing, ~0.9 x 2.1 m) and a **blue strip at floor level** (blue painter's tape / blue protection — reads as the blue tape Red described). This is a set under construction or a deliberate "unfinished" wall.
- **Distortion type:** tilted (chest 40°, hutch 45°, nightstand 90°), interlocked/wedged (pieces bear on each other with no visible support), sprawling low pile (height ~1.7 m, width ~5 m, depth ~2.5 m — wide, not tall), with 3 satellites (side table, stool, rolling cabinet) separated by 0.8–1.5 m.
- **Materials/era:** 1970s–90s American case goods — cherry and oak veneer, ebonised lacquer, brass hardware, blush velvet, steel office file. Palette: warm browns + one pink + one black + one grey-steel accent.
- **Composition:** eye-level ~1.5 m, ~35 mm equivalent (mild perspective), pile slightly left of centre, lower 45% of frame is empty carpet, horizon in the upper third; ceiling grid gives the perspective; doorway as a secondary focal point at right third.
- **Lighting/grade:** flat top light from troffers, no key; soft contact shadows; film grain + slight halation on the troffers; warm yellow, lifted blacks.
- **GAME LANDING (Level 0 / Lobby variant of `FrontRoomsFurniturePile.Build`, "sprawl" mode):**
  - Kit: `Desk_Pedestal_Cherry`, `Credenza_Cherry`, `Armchair_QueenAnne_Blush`, `Hutch_Ebonised`, `Chest5_Oak`, `Nightstand2_Oak`, `FileCabinet2_Steel`, `SideTable2Tier_Turned`, `BarStool_Wood`, `RollingCabinet_Veneer`, `Lamp_Table_Pleated`, `Urn_Ceramic`. Shared trim-sheet wood material (3 tints via MaterialPropertyBlock), one fabric material (tint per piece), one painted steel.
  - Placement: radius 2.5 m, height cap 0.6 x ceiling. 2 upright anchors on floor at the back; 2–3 big case goods rotated 35–50° about a horizontal axis, pivot on a floor corner, so one edge touches the floor and one face leans on an anchor; 1–2 small pieces rotated 90° and wedged; 1 lamp upright on the highest flat surface; 2–3 satellites 0.8–1.5 m out at different headings.
  - Doorway: pair it with a `Doorway_UnfinishedStuds` wall module (studs at 400 mm centres, a header, no casing, blue tape decal outlining the opening and a blue strip on the floor) placed on a wall 4–8 m away so both read in one frame.
  - Camera moment: player enters from the opposite side; the pile is low enough that the troffer grid and the stud doorway are visible over it — it is a "sculpture in a hall", not a wall.
  - Gameplay: low cover (crouch-hide behind the desk/credenza); not a chase blocker — the chaser can be seen over it.

### 0B — Red's STILL B (cool grey-green room, tall ceiling-touching pile) — SOURCE FOUND + VIEWED
- **Source identified:** it is entry **F02** (Fast Company Brasil, `TB_Scans_00108.webp`, a film-scan unit photo of the same pile seen warm-graded in F01/F10, credited Asterios Moutsokapas on Galerie/Curbed for the F01 angle). See F02 for the frame-level notes.
- **Room shell:** 2'x2' lay-in grid, 2'x4' flat opal troffers every ~3 tiles; square drywall column (left, ~0.6 m, wallpapered); grey-green cut-pile carpet; olive/khaki pinstripe wallpaper with a darker base band on the back wall; dark doorway at back left. The cool cast is the film scan's colour, the same set reads yellow in the digital stills (F01) — **identical geometry, different grade**.
- **Pile decomposition (bottom → top):**
  1. Base: **plywood crate on a wooden pallet** (stencilled lettering, reads like a fragile/glass shipping mark), **plywood/MDF cabinets**, a **glass-door display cabinet** (lower centre-right), a low dark cabinet at back left.
  2. Mid: **beige/oatmeal upholstered armchair** rolled onto its back (seat facing the camera); a **ladder-back step-stool / small library ladder** leaning across its front at ~50°; a **charcoal sofa back**; an **open oak bookshelf** on its side; **ladder-back wooden dining chairs** (same model repeated 4–5x) upright at the front-left, sideways, and upside-down on top.
  3. Top: a **beige floral/striped sofa** lying on top as a slab; a **black 1990s CRT TV** on top facing the camera; a **halogen torchiere floor lamp** (black pole, white bowl) sticking up ~20° off vertical — the highest point (~2.4 m); a navy cushion/pouf.
  4. Satellite: **teal fabric club armchair** parked upright ~1 m to the right.
- **Distortion type:** tall stacked pile (~0.85–0.9 x ceiling), duplicated chair model, tilted/upside-down, interpenetration at contacts (legs sink into upholstery; sofa passes into bookcase). Feels "pasted" rather than "fallen" because every piece is pristine and plausible-looking but physically unstable.
- **Composition:** low camera (~1.1 m), near-frontal, ~28–32 mm; the ceiling grid fills the top third and converges; pile mass sits on the horizon line so its silhouette is backed by wall, not ceiling.
- **GAME LANDING (Office variant of `FrontRoomsFurniturePile.Build`, "tower" mode):** kit = crate+pallet, plywood cabinet, glass-door cabinet, upholstered armchair, sofa (x2 fabrics), ladder-back chair (x5 instances, one mesh), step ladder, open bookcase, CRT TV, torchiere, teal club armchair. Radius 1.5–1.8 m, height 0.8–0.9 x ceiling (2.3–2.6 m in a 2.9 m room; in a 2.4 m zone clamp to 2.1 m and drop the torchiere). Collision: one convex hull/box for the base (crate+cabinets) and a capsule for the mass; everything above 1.2 m is visual only. Gameplay: line-of-sight blocker and loopable obstacle in the middle of an open-plan office; also the best "landmark" because the CRT faces the entrance.

### Film / marketing / BTS entries

#### F01 — Hall pile with man walking past (production still, warm) — VIEWED
- Page: [Surface, "A24's 'Backrooms' Designs Horror From Indifference" (Abigail Saldana, 2026-06-16)](https://www.surfacemag.com/articles/a24-backrooms-production-design/) (also reachable as https://www.surfacemag.com/?p=207316). Image: `https://www.surfacemag.com/app/uploads/2026/06/TB_11703_R3.jpg` (1250x833, "Courtesy of A24"). Filename prefix `TB_` = unit/BTS photography series (same series as the Asterios Moutsokapas set photos credited on motionpictures.org), so this is a set still, not a frame grab.
- In frame: a free-standing island pile in the middle of a vast open yellow room. Readable pieces: at least 4 identical **ladder-back wooden dining chairs** (one upright on the floor in front, one lying diagonally across the front with its legs out, one perched on top left, one at the top right tilted ~30°) — the repeat of one chair model is the film's "thirty-nine of the same chair" device; a **beige/oatmeal upholstered armchair** rolled onto its back so its seat faces the camera; a **charcoal sofa or loveseat** standing on end behind it; a **plywood shipping crate on a wooden pallet**; an **open-front pine bookcase/hutch carcass** on its side at right; a **beige CRT TV/monitor** at the summit; a **black halogen torchiere floor lamp** stabbing up out of the top at ~20° off vertical; a low wooden **bar stool**; cardboard/plywood sheets; a dark wood cabinet wedged at back-left. Separate from the pile, ~1 m to the right: a **sea-green club armchair** sitting normally, as if it "rolled off".
- Distortion type: stacked pile + repeated array (same chair model x4+) + tilted/upside-down + partially interpenetrating (chair legs pass behind/into the crate). Nothing is broken; every piece is intact and recognisable.
- Scale: actor ~1.8 m; pile top (lamp head) ~2.4 m, mass ~2.1 m tall, footprint ~3.0 x 2.0 m. Ceiling ~2.7 m (2'x2' mineral-fibre grid with 2'x4' flat-lens troffers in a regular grid, ~2 tiles apart).
- Composition: ~24–28 mm equivalent, camera ~1.4 m (slightly below eye), three-quarter view of the pile; pile is placed right-of-centre with the actor at left third walking "past" it, leaving a large empty floor plane in the foreground (~40% of frame). Far back: square column/wall return, a second room through a wide opening.
- Lighting/grade: flat overhead troffer light only, no visible key; soft contact shadows under the pile; warm yellow-cream grade (walls and carpet same value), black stays lifted.
- GAME LANDING: this is the canonical `FrontRoomsFurniturePile.Build` look. Kit = ladder-back chair (one mesh, 4–6 instances), upholstered armchair, sofa, plywood crate + pallet, open bookcase carcass, CRT TV, torchiere lamp, bar stool, 2–3 plywood sheets. Placement rule: one "anchor" (crate/bookcase, upright, on floor) + one "mass" (sofa on end) + 2–3 "rollers" (armchair on back, chair on side) + 3–5 "spikes" on top (chairs at 20–40°, lamp, TV) + one "escapee" (a single normal chair/armchair 0.8–1.5 m away). Radius 1.5 m, height 0.75–0.85 x ceiling. Camera moment: player enters the room through a door and sees it three-quarter with the far wall behind; never centre-frame on entry. Gameplay: landmark + circular chase obstacle (loop around it), solid box/capsule colliders on anchor+mass only, top pieces non-colliding.


#### F02 — Same pile, film-scan colour (this IS Red's STILL B) — VIEWED
- Page: [Fast Company Brasil, "Backrooms: como a A24 deu vida ao lugar mais assustador da internet" (Grace Snelling, 2026-06-05)](https://fastcompanybrasil.com/design/backrooms-como-a-a24-deu-vida-ao-lugar-mais-assustador-da-internet/). Image: `https://fastcompanybrasil.com/wp-content/uploads/2026/06/TB_Scans_00108.webp` (1024x819). Caption (pt) paraphrased: a pile of furniture and electronics in an empty Backrooms space built for the film. Credit on page: Asterios Moutsokapas (per the earlier run's page extraction; re-check credit before citing in a deck).
- Identification: the beige floral/striped sofa slab near the top, black CRT TV, torchiere lamp, plywood cabinets + crate on pallet, glass-door cabinet (lower centre-right), teal club armchair parked at right, ladder-back chairs and a wooden ladder-stool leaning on the beige armchair match Red's STILL B exactly. It is the **same physical pile as F01**, shot from a lower, more frontal angle on film (scan), so STILL B is a BTS/unit film photograph, not a frame from the movie. The cool grey-green colour is the film stock + set's real light colour; F01 is the same set graded/printed warm. Conclusion for us: the pile works in BOTH warm (Level 0) and cool (Office) grades, so one pile recipe can serve two zones.
- In frame (additional to F01): ceiling = 2'x2' lay-in tiles with 2'x4' troffers with flat opal lenses, every ~3 tiles, regular grid; a square drywall column at far left (~0.6 m) with wallpaper; olive/khaki pinstripe wallpaper at the back with a low dark band; grey-green carpet occupying the bottom 40% of frame; an open doorway at far back left.
- Distortion: stacked pile, tilted 20–90°, upside-down chair on top, repeated chair model (x4–5), wooden step-stool/ladder as diagonal brace, objects pass "through" each other at contact points (sofa back intersects bookcase; chair legs sink into the armchair).
- Composition: camera ~1.1 m, near-frontal, pile centred slightly right; ~28–32 mm; huge foreground carpet; ceiling occupies the top third with troffers converging — the ceiling grid is the perspective device.
- Lighting/grade: only overhead troffers; even top-light with soft occlusion at the pile base; cyan-green cast, low contrast, visible film grain.
- GAME LANDING: use as the Office-zone variant of the pile: same kit, swap grade by zone (the Office post-volume's green-grey). Target height ~0.85 x ceiling (2.4–2.5 m in a 2.9 m room). Put one CRT TV in the top 30% facing the player's likely approach (the screen is the "face" of the pile); add the torchiere as the highest vertical spike. Escapee armchair must be a different upholstery colour (teal) from the pile's beige mass. Chase role: loopable island obstacle; hide spot behind it (enemy LOS blocker).

#### F03 — Slanted "tilted room" (BTS / key art scan) — VIEWED
- Page: Fast Company Brasil (above). Image: `https://fastcompanybrasil.com/wp-content/uploads/2026/06/KV-40.jpg` (1600x900). Caption (pt) paraphrased: crew members walking through an inclined set built to represent the Backrooms. Two people on a floor that rises steeply to the right while the ceiling stays level; yellow wallpaper; a tiny dark doorway at the far upper right.
- Furniture: none — but it is the spatial-distortion reference (a floor that ramps up to meet the ceiling, shrinking clearance). Matches the risers/ramps statements in Surface and The Credits.
- GAME LANDING: not a furniture pile but a "squeeze" room: a ramp mesh rising from 0 to ~1.8 m over 8–10 m inside a 2.9 m room, ceiling kept flat so clearance shrinks to ~1.1 m (crouch). Use in the maze as a chase choke; place a single normal office chair half-way up the slope (it reads instantly as "wrong").

#### F04 — Cap'n Clark's showroom, rows of recliners (BTS film scan) — VIEWED
- Page: Surface (F01). Image: `https://www.surfacemag.com/app/uploads/2026/06/TB_Scans_00103.jpg`.
- In frame: big-box store interior: a pirate mannequin at a ship's wheel centre-frame; flanking **rows of 1990s overstuffed recliners/club chairs** in powder-blue, teal, mauve and sage velour, all facing the camera like an audience; patio umbrellas, table lamps with pleated shades, side tables, a wicker set behind; open-web steel joists and long fluorescent strip fixtures; hanging "EVERYTHING MUST GO" / "ON SALE" signs.
- Distortion type: none in-world, but this is the **source catalogue** of the backrooms piles: the same recliner/club-chair families and lamp shades reappear in the piles. Composition: perfectly symmetrical, one-point, camera ~1.2 m, ~28 mm.
- GAME LANDING: "copy-paste row" archetype source: 4–6 instances of one armchair mesh in a straight row, identical yaw, 0.9 m pitch, facing the doorway. In the Office, the same trick with task chairs facing a blank wall. Colour palette for upholstery materials: powder blue #8EA3B8, teal #4E7F7C, mauve #8C6B74, sage #9AA38C (sampled by eye from the viewed image; approximate).

#### F05 — Endless yellow corridor (trailer frame) — VIEWED
- Page: Surface (F01); same frame on [The Credits / motionpictures.org](https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/). Image: `https://www.surfacemag.com/app/uploads/2026/06/A24_BACKROOMS_DTR1_NO_GREENBAND_1920x1080_TEXTLESS_SPLITS_PRHQ.00_00_43_20.Still005_R2.jpg`. The filename encodes **trailer "DTR1" (domestic trailer 1) at 00:00:43:20** — i.e. ~0:43 into the first full trailer.
- In frame: Clark walks away down a long straight corridor (~2.4 m wide), yellow fine-patterned wallpaper, cream carpet, 2'x2' tile ceiling with a single centred line of 2'x4' troffers receding; a second figure far down the hall. No furniture.
- GAME LANDING: the corridor rhythm for the Office's "doorway into a long corridor" (target image): troffer pitch 2 tiles, centred; corridor width 2.4 m; no props for >10 m so a single chair at the far end becomes a landmark.

#### F06 — Clark at the wall, empty room with column and chair rail (film frame ~00:37:55) — VIEWED
- Page: Surface (F01). Image: `https://www.surfacemag.com/app/uploads/2026/06/EFG_LOCK-R5Changes_Clean_A24_20260326.00_37_55_22.Still016_CropR.jpg` — filename = final locked cut, **film timecode 00:37:55**.
- In frame: Clark's hand on a wall that appears to be **wood-grain veneer/yellow**, background: empty hall with a square column, a thin **dark wood chair rail/bumper at ~0.9 m** on the far wall, 2'x4' troffers. Very shallow staging, camera ~1.5 m, ~35 mm.
- GAME LANDING: confirms the chair-rail + square-column vocabulary of Red's STILL A. Kit pieces: `ChairRail_DarkWood` strip (0.9 m height, 7 cm tall, 2 cm proud), `Column_600` square drywall column with wallpaper wrap.

#### F07 — Mannequin group between free-standing half-walls (production still) — VIEWED
- Page: Surface (F01). Image: `https://www.surfacemag.com/app/uploads/2026/06/cRgSaEBw.jpg` (1250x977).
- In frame: three grey mannequins (one with a red mark at the hip) standing in a room of free-standing **1.4 m and 1.0 m wallpapered partial walls capped with dark wood**, a dropped soffit beam, square pier, pale grey concrete-ish carpet, two 2'x4' troffers.
- Furniture: none, but the **wood-capped half-wall** is a furniture-scale divider (like a cubicle panel built in drywall) — directly applicable to Office cubicle "islands that go nowhere".
- GAME LANDING: `HalfWall_Capped` (1.0/1.4 m high, 0.15 m thick, dark wood cap 5 cm) placed as L-shapes that enclose nothing; good low-cover for hiding in chase.


#### F08 — Clark at a wall hatch; huge empty room with one purple chair and shoes on the carpet (film still) — VIEWED
- Page: [Galerie, "How Horror Blockbuster Backrooms Terrorizes Viewers with Design" (Mandi Bierly, 2026-06-15)](https://galeriemagazine.com/how-horror-hit-backrooms-terrorizes-viewers-with-design/). Image: `https://cdn.galeriemagazine.com/wp-content/uploads/2026/06/BackroomsClark.jpg` (1825x1027, "Photo: Courtesy of A24"). Alt text: man in beige room with scattered shoes and a purple chair.
- In frame: camera looks through a deep square wall opening (a ~0.6 m thick "hatch", framed like a picture box) into a vast empty yellow-cream room. Clark's head and shoulders in the hatch. Far back-right: a **single purple/violet upholstered side chair** standing alone; on the carpet mid-ground: **4–5 dark shoes standing upright** (embedded — compare Mutant Reviewers/Moria's "shoes standing upright embedded in the carpet", https://moriareviews.com/sciencefiction/backrooms-2026.htm). Ceiling: 2'x4' troffers, regular grid, converging to a vanishing point. Zero other furniture.
- **Identified via Curbed** (same frame, `Still023-CropR`, https://pyxis.nymag.com/v1/imgs/d29/108/e43904f3fe736995e424db292a59150e92-Still023-CropR.rhorizontal.w700.jpg): Curbed's caption calls it a leaning throne and embedded shoes in the background, and Vermette describes cutting shoes in half and balancing an oversize throne that is tipping over ([Curbed, 2026-05-28](https://www.curbed.com/article/backrooms-kane-pixels-a24-set-production-design-interview.html)). So the purple chair is an **oversized, leaning throne** (scaled wrong + tilted) and the shoes are **half-shoes embedded in the carpet**.
- Distortion type: scaled wrong (oversize throne) + tilted (leaning, balanced) + embedded (half-shoes rooted in carpet) + isolation in an over-large room.
- Composition: frame-within-frame (the hatch = 70% of image as a dark yellow border), one-point perspective, camera ~1.5 m, ~28 mm, symmetrical.
- Grade: warm yellow, low contrast, soft top light.
- GAME LANDING: "Lone chair in a void" archetype. In a big zone (5.4 m ceiling) or a merged 3x3-cell room: one office chair or upholstered side chair (unique colour, e.g. violet #6A4C7A fabric) placed at 70–80% depth, slightly off-axis; 3–6 shoe meshes as small floor "plugs" (sunk 3–5 cm into carpet, no collider). Camera moment: present it through a thick wall opening or a doorway (frame-within-frame). Gameplay: landmark/bait — the chair is where a pickup/note sits; walking to it pulls the player into the open (exposed to the chaser).

#### F09 — Mary walking through a lone door in an empty yellow room (film still) — VIEWED
- Page: Galerie (F08). Image: `https://cdn.galeriemagazine.com/wp-content/uploads/2026/06/BackroomsRoomMary-1174x660.jpg` ("Courtesy of A24").
- In frame: a plain wood-veneer interior door (brown, dark frame, brass lever) standing open in a long yellow wallpapered wall; through it a deeper lit space. Pale concrete-grey carpet. No furniture.
- GAME LANDING: door kit for Office/Level 0 boundaries: slab door 0.9 x 2.1 m, medium-brown wood veneer, dark casing, lever handle; open 70–80°. The target office image's "wood-framed doorway into a long corridor" can use this exact door family.

#### F10 — Pile, wide three-quarter (same set photo as F01, credited) — VIEWED
- Page: Galerie (F08). Image: `https://cdn.galeriemagazine.com/wp-content/uploads/2026/06/BackroomsPile-1174x783.jpg`. Caption credit **"Photo: Asterios Moutsokapas"** and alt text "large pile of stacked furniture including chairs, tables, and couches". Same frame as F01 — this confirms F01/F02 are unit photography by Asterios Moutsokapas.
- Use: cite this one (clear credit) in decks; the GAME LANDING is in F01/F02.

#### F11 — Mary's therapist office ("real world" 1990s office, film still) — VIEWED
- Page: Galerie (F08). Image: `https://cdn.galeriemagazine.com/wp-content/uploads/2026/06/BackroomsMaryOffice-1174x660.jpg` ("Courtesy of A24"); alt text: person in an office chair in a warmly lit study with bookshelves.
- In frame: **tan/cognac tufted leather swivel executive chair** with black lacquered arms on a 5-star base; built-in **oak open shelving** with books, a globe, a plant; a **wood-top desk with a grey/greige front modesty panel** under the window; plaid/check drapes in brown-tan-black with a matching valance; sheer white curtains; framed diploma on greige wall; beige carpet. Galerie says buyer Eric Cairns dressed "Mary's office" from Facebook Marketplace finds (see §2).
- Distortion: none — this is the "upstairs" reference palette (Vermette's sad greys and blues per W Magazine, §2).
- GAME LANDING: material/era calibration for Office props: leather (cognac, crazed, 0.45 roughness), lacquered oak (0.35 roughness), greige laminate panel. One "executive" chair mesh variant for the boss office/landmark; the drapes + valance are a cheap window dressing for the target image's big interior window.


#### F12 — Showroom ceiling: long fluorescent strip runs under open-web joists (film still) — VIEWED
- Page: Curbed (§2). Image: `https://pyxis.nymag.com/v1/imgs/3ba/2de/675f8b1ea7f685a45ec28097b16cf13fc3-Still012-CropR.2x.rhorizontal.w700.jpg`; caption: the white ceilings are new (location ceiling painted white).
- In frame: Clark (store T-shirt) under a white-painted steel joist deck with continuous rows of 8 ft fluorescent strips, a hanging sale sign at left, a dark blue fascia wall, a pendant brass lamp. No backrooms furniture.
- GAME LANDING: the "upstairs"/showroom ceiling, if FrontRooms ever has a store-front lobby; continuous strip rows (not troffers) separate the real world from the backrooms grid.

#### F13 — Custom troffers above a store employee (BTS, Sela Shiloni) — VIEWED
- Page: Curbed. Image: `https://pyxis.nymag.com/v1/imgs/3d4/3d9/da69220c2b74ec42298f839aeb52fa429d--H4A8444.rvertical.w570.jpg`; caption: custom-made troffers above actor Lukita Maxwell (photo: Sela Shiloni).
- In frame: 2'x2' lay-in tile ceiling with two 2'x4' troffers with **flat, evenly glowing opal lenses** (no visible prisms, no visible lamps) and a thin white frame; a photo-mural of a tropical beach on the wall.
- GAME LANDING: troffer material = flat emissive opal lens (emission ~ uniform, slight 5–8% falloff to edges), thin 2 cm white steel frame flush with the T-bar. Use this for Office troffers instead of a prismatic grid texture (the current Office frame shows a 4x8 egg-crate/prismatic look that does not match the film).


#### F14 — Cap'n Clark's store lobby: floating sofa/armchair vignettes (film still) — VIEWED
- Page: Dezeen (§2). Image: `https://static.dezeen.com/uploads/2026/05/backrooms-danny-vermette-interview-behind-the-scenes-design_dezeen_2364_col_8-852x479.jpg`; caption: the store also has echoes of the liminal space aesthetic.
- In frame: two employees in the entrance zone; behind them on white-grey vinyl tile: a **camel/oatmeal overstuffed sofa**, a **charcoal sofa**, a **tan armchair**, a **wood armoire/wardrobe** against the wall, a **black torchiere** and table lamps with pleated shades, all grouped as "rooms" with no walls; a navy fascia band above greige walls; a storefront glazing wall with steel mullions.
- Distortion: none, but the vignette grouping (sofa + armchair + lamp + side table floating in a void) is the "living-room island" that the backrooms later mutates.
- GAME LANDING: a "vignette island" generator — 1 sofa + 1–2 armchairs + 1 side table + 1 lamp, arranged on an implicit 3x3 m rug footprint, facing a non-existent TV. In the Office, swap to "cubicle island" (see archetypes). Good as a hiding spot (crouch behind sofa back).

#### F15 — Showroom BTS (Asterios Moutsokapas), symmetric rows of recliners — VIEWED (duplicate of F04, different crop)
- Page: Dezeen; image `...dezeen_2364_col_15-852x650.jpg`; caption credits Asterios Moutsokapas and says the store set was also designed to be unnerving. Same frame as F04 (Surface `TB_Scans_00103.jpg`). Use F04 for notes; this gives the photographer credit.

#### F16 — Raked floor to a shrinking space (BTS, Asterios Moutsokapas) — VIEWED (same frame as F03)
- Page: Dezeen; image `...dezeen_2364_col_17-852x568.jpg`; alt text: director Kane Parsons climbing up a raked floor into a shrinking space; caption: sets were built to encourage awkward interactions. This identifies the person in F03 as Parsons and the photographer as Moutsokapas.


#### F17 — Camcorder POV through tilted case-goods pile, figure in column hall (trailer frame) — VIEWED
- Page: [Man of Many, "Inside the Backrooms Trailer..."](https://manofmany.com/entertainment/movies-tv/backrooms-trailer-a24-explained) (embeds the official trailer https://www.youtube.com/watch?v=0HjdiohVOik). Image: `https://manofmany.com/wp-content/uploads/2026/04/Backrooms-A24-2026-2.jpg` (1200x900, 4:3 — camcorder/VHS aspect). Exact trailer timestamp: UNVERIFIED (not stated on the page).
- In frame: 4:3 low-res video look (soft, smeared highlights, interlace-like softness). Foreground lower-left: a jumble of **1970s–80s wood case goods** — a light-oak **dresser/hutch with Chinoiserie fretwork side panels** tipped ~30° and stacked on another dresser, a **dark hutch top** leaning, drawers half-out, all cropped by frame edge. Background: a vast pale-yellow hall with **square columns** (~0.6 m) on a ~6 m grid, 2'x4' troffers, a person in a dark jacket mid-ground.
- Distortion: stacked + tilted + cropped "foreground pile" — the pile is used as a **foreground frame**, not a subject.
- Composition: handheld, ~1.2 m height, wide (~24 mm), pile occupies lower-left 40% as a dark diagonal mass; columns give depth rhythm.
- Grade: washed-out, low-contrast, yellow-cream highlights clipping, no deep blacks — the VHS look.
- GAME LANDING: "foreground pile at a doorway / column" — place a low case-goods pile (dresser + hutch top tipped 25–35°) **immediately beside a doorway or a column on the player's entry side**, so the first view into a big column-hall is framed by it. Also use the 4:3 camcorder post profile (if FrontRooms has a camcorder item) — soft, lifted blacks, chroma bleed.

#### F18 — Lone floral armchair low in a basement under a bare bulb (trailer frame) — VIEWED
- Page: Man of Many (F17). Image: `https://manofmany.com/wp-content/uploads/2026/04/Backrooms-A24-2026-3.jpg` (4:3). Man of Many alt/caption lists an image as "Empty room with armchair". **Provenance resolved:** this is the opening of the official teaser (see TT01, https://www.youtube.com/watch?v=tKGhxMi50y8, ~0:15–0:21).
- In frame: low basement room, 2'x2' tile ceiling with one ceiling-mounted bulb fixture, small hopper windows high on the left wall, a wooden step-ladder/shelf at left, dark doorway at right; centre-back against the wall: a **grey-cream floral upholstered armchair** whose legs are not visible — it sits **sunk into the floor to the seat line** (reads like Dezeen's "incongruous piece of furniture sinking into the carpet").
- Distortion: embedded-in-floor.
- Composition: ~1.4 m camera, frontal, ~28 mm; chair centred, room empty.
- Grade: warm sodium-tungsten from one bulb, deep vignette, dark corners — the opposite of troffer flatness.
- GAME LANDING: "Sunk furniture" archetype: armchair mesh lowered by 0.25–0.4 m into the floor; requires a floor decal (dark crease ring + carpet pile pushed up) and a cut mesh variant or a stencil/clip so the buried part never shows through the floor's underside (rooms are recycled — the floor is a thin plane). Lighting: a single point light (warm 2700 K) makes it a "story room". Gameplay: landmark / jump-scare spot (chaser can spawn behind the doorway at right).

#### F19 — Kane-Pixels-style empty column rooms with low half-wall (trailer/series frame) — VIEWED
- Page: Man of Many (F17). Image: `https://manofmany.com/wp-content/uploads/2026/04/Backrooms-A24-2026-8.jpg` (4:3). Caption on page: "Empty room with armchair" may refer to F18 instead; this frame shows no furniture. Provenance UNVERIFIED (looks like CG from Kane Pixels' 2022 series).
- In frame: saturated orange-yellow walls, a free-standing **~1 m half-wall** (pony wall) in front of an opening into a dark room, a square pier, a big 2'x4' troffer in the foreground, a thin dark chair-rail strip on the far wall.
- GAME LANDING: confirms the pony-wall/half-wall vocabulary (see F07) and the chair-rail strip. Use as low cover in the maze.


#### Trailer pass — method
I scrubbed the official trailer [A24, Backrooms | Official Trailer HD](https://www.youtube.com/watch?v=0HjdiohVOik) (2:17.8 long, 49M views at time of viewing) in the in-app browser by seeking the paused player and drawing frames to an on-page canvas for viewing (nothing saved). Sampled every 1.5–2 s, then looked at key frames at 640x360. Timestamps below are trailer time (m:ss), accurate to about ±0.5 s.

#### T01 — 0:05–0:09 Cap'n Clark's store at night: recliner rows under strip lights — VIEWED
- In frame: same showroom as F04 but dark/after hours: rows of recliners and club chairs, dining sets, hanging sale signs, joists with continuous strip fixtures. 0:09 is near-black with only the sign and a few chairs lit.
- GAME LANDING: a "dark showroom" variant of the copy-paste row: same row of identical armchairs, with only every third light on (stepped darkness = chase tension).

#### T02 — 0:31–0:33 The F01/F02 pile as a foreground wall, Clark far behind — VIEWED
- In frame: the tall pile (ladder-back chairs on top, torchiere, crate, cabinets, a wood dresser front, armchair) fills the **left 40% of frame in the foreground**, cut by the frame edge; Clark small (1/6 frame height) at ~12 m, mid-right; empty yellow hall, square column at right edge, troffer grid converging. Camera ~1.3 m, wide (~20–24 mm), slow push.
- Distortion: same pile (stacked/tilted/repeated chairs) used as a **foreground occluder**.
- GAME LANDING: proves the pile works as a *reveal device*: place `FurniturePile` 1.5–3 m to one side of the doorway the player enters through, so the first frame is "pile in left/right foreground, empty hall + column + far doorway beyond". Collision: blocks the side, keeps the door axis clear.

#### T03 — 0:53 Two lone wooden chairs in a column hall — VIEWED
- In frame: Clark in the foreground (eye-level, ~28 mm), behind him a very large low hall with square columns and a dense troffer grid; at far right two **wooden side chairs** standing apart, at different yaw (~40° apart), nothing else in ~20 m.
- Distortion: isolation / random yaw (the "39 identical chairs" used singly).
- GAME LANDING: `LoneChairs` scatter: 1–3 instances of one wooden chair mesh at 60–90% room depth, random yaw from (0, 35, 90, 180)°, never aligned to anything. Cheapest landmark in the kit (one mesh, one material).

#### T04 — 1:05 Camcorder (4:3) in the store: bedroom-set dressers and a lamp — VIEWED
- In frame: VHS-look 4:3; a store employee in the foreground; behind her dark **cherry/mahogany dressers with mirrors**, a chest-on-chest, a floor lamp, a white plastic stool; white walls, grey carpet.
- GAME LANDING: the "real" versions of the case goods that reappear tilted in 0A — the kit should include the upright, un-distorted dresser-with-mirror so the player first sees it normal (lobby/store) and later sees its copy tilted in a pile.

#### T05 — 1:25.5 Mary's living room: pastel blue floral sofa with wood-trim, pleated lamp — VIEWED
- In frame: a pale blue/white **floral-print 3-seat sofa** with rolled arms and an exposed wood base trim, a cherry end table with a **pleated-shade brass table lamp** (warm, lit), a framed watercolour above; a second lamp at right. Matches Eric Cairns' brief for "soft pastels and wood-trim detailing" (Curbed, §2).
- GAME LANDING: upholstery reference for the pile's "floral sofa slab" (STILL B top): pastel floral fabric material (tiling 0.5 m, roughness 0.85, sheen via URP Lit "clear coat off" + fabric-ish normal). One sofa mesh, three fabric tints: pastel-blue floral, oatmeal stripe, charcoal plain.

#### T06 — 1:32 Long yellow corridor with a **drift of identical wooden chairs** — VIEWED
- In frame: a ~3 m wide, very long corridor, yellow wallpaper both sides, centred troffer line; from ~15 m to the vanishing point **10+ wooden side chairs** stand along the left wall and cluster in the far distance (some facing the wall, some facing the camera, some toppled?). Single tone, flat light, faint haze.
- Distortion: repeated array (one chair model many times) with random yaw → it reads as a crowd. This is the clearest on-screen use of the "thirty-nine of the same chair" haul (Surface, §2).
- GAME LANDING: "Chair drift" archetype: N (8–20) GPU-instanced copies of one chair along a corridor wall, density increasing with distance (Poisson spacing 0.6–1.5 m), yaw jitter ±25° with 15% of instances at 180°, 5% tipped on their back. No colliders beyond 5 m from the player path; at the near end, 1–2 chairs with colliders as soft obstacles. Excellent for the streamed room train corridors (cheap draw calls).

#### T07 — 1:47 Dark furnished room inside the backrooms (dining set, torchiere, stair banister) — VIEWED
- In frame: low-lit, warm room seen past a white-painted **stair banister** (left); a **round dining table with a white cloth** and 4 bentwood/ladder chairs, a sofa, a lit **torchiere** and table lamps (only light sources), a whiteboard/frame on a stand, small objects hanging from the ceiling on strings, a figure standing still at the back. Ceiling: 2'x2' grid, no lit troffers.
- Distortion: domestic furniture set up "as if lived in" in the wrong place (house interior inside an office grid); hanging objects.
- GAME LANDING: "Lamp-lit domestic island" — lights off in the troffers of a room, then 2–3 warm lamps (torchiere 3000 K, table lamps 2700 K) on a dining/sofa vignette. Strong contrast with the flat office; good safe-room/story beat, or a trap.

#### T08 — 1:50 Coat-rack silhouette in the foreground, dark hall with chairs — VIEWED
- In frame: black bentwood **coat rack/hat stand** silhouette filling the right foreground; a doorway with a figure; behind, a dim room with a dining table, chairs, a floor spotlight on a stand. 
- GAME LANDING: a single tall foreground prop (coat rack, torchiere) placed 0.5–1 m from a doorframe on the player's side gives depth layers in dark rooms; non-colliding.

#### T09 — 2:06.5 Pool room with plastic patio chairs on the deck — VIEWED
- In frame: tiled room (grey-beige wall tile, dark floor tile), a raised long pool/basin with a chrome ladder, **white plastic patio chairs** in a row on the deck, a figure seated on the ledge; low warm-green light. Dwell mentions a rotting swimming pool (§2).
- GAME LANDING: out of scope for Office, but the "row of identical plastic chairs" is the same copy-paste row archetype in a new material (white ABS, roughness 0.4).


#### Teaser pass — [A24, Backrooms | Official Teaser HD](https://www.youtube.com/watch?v=tKGhxMi50y8) (1:00.7; also listed: a second teaser `BjRndcTYqJo`, a promo `2z6a6NUFlsU` and a clip `Pb8KqfkLe24`, not reviewed)

#### TT01 — 0:01–0:15 Basement with a lone floral armchair, sun through hopper windows — VIEWED
- In frame: a low basement (~2.3 m), painted block/drywall, 2'x2' tile ceiling, one flush-mount dome light, a strip of small hopper windows high on the back wall throwing **hard sun patches with prismatic rainbow edges** across the floor; a dark panelled door at right; a small dark cabinet at left; centre-back: a **grey-cream floral wingback/club armchair** standing normally (0:09–0:13). Slow static/locked frames with light patches moving (time-lapse).
- Distortion: none yet — this is the "normal" state.
- GAME LANDING: a pre-distortion beat — show an ordinary armchair in an ordinary room first; reuse the same mesh later sunk or stacked (TT02, F02).

#### TT02 — 0:19–0:21 Same armchair, now lower, arms splayed on the floor — VIEWED
- In frame: from a new angle (camera nearer the wall ladder/shelving), the same armchair now sits **noticeably lower, seat almost at floor level, arms flat on the carpet** — reads as sunk into the floor or melted (my reading; the film's intent is UNVERIFIED). Light changed from sun to only the dome light.
- Distortion: embedded-in-floor / progressive (changes between visits).
- GAME LANDING: "Revisit change" rule: when the player re-enters a recycled room, swap the armchair to its sunk variant (-0.3 m, slight pitch 5°, crease decal). Cheap, memorable, fits the RoomStream recycling (same seed + visit counter).

#### TT03 — 0:23–0:36 Empty rooms; wedge-shaped alcove with a tiny dark doorway; arched dwarf door — VIEWED
- In frame: rooms with a pin-board/poster cluster and one small object on the floor (0:23–0:25), then plain walls narrowing to a **tiny dark doorway** (0:33–0:35) and a **small arched doorway** (0:36.6). Matches Moria Reviews' "alcoves that narrow in a wedge shape to reach tiny dwarf doors" (prior-run extraction, §2).
- GAME LANDING: doorway kit variant `Doorway_Dwarf` (0.6 x 1.1 m, arched or square) at the end of a tapering alcove — a non-traversable landmark or a crouch-only shortcut for the player that the chaser cannot follow.

#### TT04 — 0:38–0:47 Yellow open office of half-height counters and partitions — VIEWED
- In frame: classic yellow backrooms, but filled with **free-standing ~1.1 m counters/pony walls** (reception-desk-like L-shapes, wallpapered, with thin caps), recessed bays with darker lighting at the back right, troffers on a regular grid, square piers. The title card overlays it.
- Distortion: "dividers that go nowhere" (Moria's phrase for endless offices empty of people; §2).
- GAME LANDING: the Office's cubicle islands should borrow this: partitions laid out by a rule that produces **enclosures with no entrance or with entrances facing walls** in 1 of 4 islands; height 1.1–1.5 m so the player can see the chaser over them when standing and hide when crouched.

## 4. Tableau archetypes (5–8) with recipes

Eight archetypes cover every furniture shot above. Shared rules from the film (§2): every piece is **intact, clean, period-correct 1970s–90s** (nothing broken, no debris); repetition of **one** model is the strongest signal; piles are **"delicate", arranged, balanced** rather than dumped; light stays the flat troffer grid (no special light on the pile). Perf rules for all: one shared mesh per furniture type, GPU instancing / SRP Batcher-compatible materials, tints via MaterialPropertyBlock, 2 LODs, colliders only on the lower 1.2 m.

### A1 — Centre-hall tower pile ("tower") — sources: 0B, F01, F02, F10, T02
- Silhouette: roughly conical, 0.8–0.9 x ceiling height, footprint 3 x 2 m, with 1–2 thin spikes (torchiere, chair legs) breaking the top; one escapee armchair 1 m away.
- Kit (10–14 pieces): crate+pallet, plywood cabinet, glass-door cabinet, upholstered armchair, sofa x2 fabrics, ladder-back chair x4–6 (same mesh), step ladder, open bookcase, CRT TV, torchiere, bar stool, club armchair (escapee).
- Placement: layer 0 (floor, upright): 2–3 boxy anchors touching; layer 1: 2 soft/large pieces leaning 20–90° on anchors; layer 2: 3–5 light pieces (chairs, ladder, TV) on top surfaces at 20–40°, at least one upside-down; spike: torchiere at 10–25° off vertical, top ≤ ceiling - 0.25 m. Allow ≤ 10 cm interpenetration at contacts (film look), never visible floating gaps > 2 cm.
- Camera moment: reveal from a doorway 6–10 m away, three-quarter, with the pile off-centre (F01) or as a foreground side wall (T02).
- Gameplay: landmark + loopable chase obstacle + LOS blocker; base collider = 1 box + 1 capsule.

### A2 — Sprawl of tilted case goods with satellites ("sprawl") — sources: 0A, F17, T04
- Silhouette: low and wide (height ≤ 0.6 x ceiling, ~1.7 m), 4–5 m wide, one dark triangular peak (leaning hutch) and one big diagonal (chest of drawers at 40°), plus 2–3 satellites at 0.8–1.5 m.
- Kit: pedestal desk, credenza, hutch (ebonised), 5-drawer chest, 2-drawer nightstand, steel 2-drawer file, Queen-Anne armchair (blush velvet), 2-tier turned side table, bar stool, rolling cabinet, pleated table lamp, urn.
- Placement: anchors at the back upright; tilt big case goods about their floor edge (pivot at a bottom corner, 35–50°); rotate one small piece 90°; lamp upright on the highest flat top; satellites at distinct headings.
- Pair with A7 doorway (stud doorway + blue tape) 4–8 m away.
- Gameplay: crouch cover; does not block sight lines when standing.

### A3 — Copy-paste row / chair drift — sources: F04, F15, T01, T03, T06, T09
- Row variant: 4–8 identical seats (recliner / armchair / plastic chair / task chair) in a straight line, identical yaw, 0.9–1.0 m pitch, facing a door or a blank wall.
- Drift variant: 8–20 identical wooden chairs along a corridor wall with density rising toward the far end; yaw jitter ±25°, 15% reversed, 5% on their backs.
- Implementation: one mesh, `Graphics.RenderMeshInstanced` or static-batched instances; colliders only on the 2 nearest to the player path.
- Gameplay: rhythm/landmark in long streamed corridors; near-end chairs = soft obstacles in a chase.

### A4 — Sunk / embedded / half-object — sources: F08 (half-shoes), F18/TT02 (sunk armchair), Dezeen "furniture sinking into the carpet", Moria "couches ... buried in floors and walls" (prior-run)
- Method (film-authentic, Curbed §2: props were literally cut in half): pre-cut meshes in Blender with a **capped cut face** (so recycled thin floors/walls never show internals): `Armchair_Sunk30` (cut 0.3 m above the floor plane), `Sofa_WallHalf` (cut by a wall plane at 40% depth), `Cabinet_CeilingHalf`, `Shoe_Half`. Add a crease/contact decal (dark ring + pushed-up carpet pile) via URP Decal Projector.
- Placement: snap cut face to the wall/floor surface ±1 cm; never at a door's swing; one per room max.
- Gameplay: uncanny landmark; revisit-change trigger (TT02).

### A5 — Scaled-wrong lone object in a void — sources: F08 (oversize leaning throne), T03 (two lone chairs)
- One object, unique colour, 1.3–2.0x scale (throne) or normal scale but isolated (chairs), tilted 5–12°, placed at 70–80% of the room depth in an oversized room (merged cells or the 5.4 m zone).
- Present through a frame (hatch, doorway, window) — F08 composition.
- Gameplay: bait/pickup location; exposes the player in open floor.

### A6 — Dividers that go nowhere (cubicle island) — sources: TT04, F07, F19 and the target office image
- Cubicle panels 1.1–1.5 m (fabric blue-grey in Office; wallpapered + dark wood cap in Level 0), L/U shapes on the 3 m grid; 1 in 4 islands has no opening or its opening faces a wall; desks/CRTs inside some, empty in others.
- Gameplay: hide when crouched, see over when standing; chaser path-finding needs NavMesh carving per island.

### A7 — Threshold under construction / wrong doorway — sources: 0A (exposed studs + blue tape), TT03 (dwarf doors), F09 (lone door), Dezeen "doorways halfway up the wall"
- Kit: `Doorway_UnfinishedStuds` (studs at 400 mm, header, blue tape decal on the opening edge, blue strip on floor), `Doorway_Dwarf` (0.6 x 1.1 m), `Door_Slab_Veneer` (0.9 x 2.1 m), `Doorway_HighWall` (sill at 1.2–1.6 m).
- Gameplay: path choice and readability — unfinished = passable, dwarf = crouch-only, high = unreachable landmark.

### A8 — Lamp-lit domestic island — sources: T07, T08, T05, F14, F11
- Troffers off in the room; 2–3 warm practicals (torchiere 3000 K, pleated table lamps 2700 K) on a sofa + armchair + dining set vignette; one tall foreground silhouette (coat rack/torchiere) beside the entry door.
- Gameplay: safe-room/story beat or ambush. Costs 2–3 real-time lights → bake or use 1 shadowed + 2 unshadowed point lights.

## 5. Landing rules for `FrontRoomsFurniturePile.Build` and `FrontRoomsOfficeKit.Dress`

`FrontRoomsFurniturePile.Build(Transform parent, Vector3 localCenter, float radius, float ceilingHeight, int seed)`
1. **Mode by space:** `radius <= 1.9 && ceilingHeight >= 2.6` → A1 tower; `radius >= 2.2` → A2 sprawl; `ceilingHeight < 2.6` (2.4 m zone) → sprawl only, height cap 1.6 m; `ceilingHeight >= 5` → tower cap 3.6 m or A5 throne (seed % 4 == 0).
2. **Authored poses, not runtime physics.** The film piles are impossible balances (Curbed: balance was the hard part). Author 6–10 pile "recipes" in Blender/Unity editor as lists of `(slot sizeClass, localPos, localRot, scale)`; at runtime the seed picks recipe, mirror (x-flip), yaw (0/90/180/270 + ±10°) and **substitutes pieces within the same size class** (any chair in a chair slot, any case good in a case slot). This gives "copy-paste recombination" variety, deterministic per seed, zero physics cost, no floating.
3. **Repetition rule:** in each pile, one chair model fills all chair slots (the 39-same-chairs device); one "odd colour" item (teal, blush, violet) per pile.
4. **Height clamp:** top of highest bounds ≤ `ceilingHeight - 0.25`; spikes may reach `ceilingHeight - 0.1`; never intersect the ceiling (troffer grid must read uninterrupted — it is the film's perspective device).
5. **Colliders:** `BoxCollider` around layer 0 + one `CapsuleCollider` for the mass; nothing above 1.2 m; NavMeshObstacle (carve) with the base footprint so the chaser loops around.
6. **Escapee:** 1 satellite at `radius + 0.8..1.5 m`, upright, facing the pile at ±30°.
7. **Materials:** 3 shared materials (wood trim-sheet with 3 tints, fabric with 5 tints + 1 floral, painted steel/plastic) → SRP Batcher friendly; CRT screen gets a slight emissive grey only if powered (rare).

`FrontRoomsOfficeKit.Dress(Transform parent, Rect localFloorXZ, float ceilingHeight, int seed, Rect[] keepClear)`
1. Reserve `keepClear` + 1.2 m margins (doors, chase spine). The target image's central aisle stays empty.
2. Perimeter first: copier, water cooler, vending machine, filing cabinets, interior window — against walls, never in corners that the chaser needs.
3. Cubicle islands (A6) on the 3 m grid, 1–4 per room by area; 25% "go nowhere".
4. One landmark per room chosen by seed: none (50%), lone chair (A5-lite, 20%), chair row (A3, 15%), sunk object (A4, 10%), pile (A1/A2, 5% — rarer in Office than in Level 0 so it stays special).
5. Corridors from the room train: chair drift (A3) at 1 in 5 corridors.
6. Revisit change (TT02): store a visit counter per seed; on the second visit swap one prop to its distorted twin (tilted, sunk, duplicated).

Shot-to-camera checklist for every placed tableau: visible from the entry door within the first 2 s; off-centre (rule of thirds) unless symmetry is the point (A3 row); troffer grid visible above; foreground empty floor ≥ 30% of the frame at eye height 1.6 m with the game's wide FOV (the film used 18 mm or wider per Sony/ShotDeck, cited in VISUAL_RESEARCH_LOOKDEV.md).

Quality-bar note (calibration from `Verification/lookdev/2_Office_forward.png` and `ref_office_target.png`): the current Office frame has a 4x6 egg-crate/prismatic troffer, plain white bench boxes and no columns, cubicles or desks reading; the target and the film both use **flat opal lenses**, square columns, cubicle islands and real 1990s pieces with bevels and fabric. The pile kit must hit the same material fidelity as the target's desks/CRTs (bevelled edges, veneer grain, fabric weave normal, macro wear), otherwise piles will read as "boxy, flat-coloured" — the exact complaint about the previous Codex models.

## 6. Open questions / what still needs eyes-on verification
- The film itself (and the Blu-ray extras "Building the Backrooms" / prop walkthrough listed by A24's shop per the Codex doc) were not viewed; the furniture-in-wall / buried-couch shots described by Moria Reviews have **no still found yet**. Next: IMDb media gallery, Letterboxd backdrops, ShotDeck (requires account — skip if gated), FilmGrab once it posts the film.
- Second teaser `BjRndcTYqJo`, promo `2z6a6NUFlsU` and clip `Pb8KqfkLe24` not scrubbed.
- F17 (camcorder pile with fretwork dresser) timestamp in the trailer not located in my 2 s sampling — it may come from the second teaser/promo. UNVERIFIED.
- TT02 "sunk armchair" is my visual reading of a lower seat line; intent UNVERIFIED.
- Throne scale in F08: Curbed says "oversize"; actual scale factor unknown (estimate 1.3–2x).
- Photo credits: confirm Fast Company Brasil's credit line for `TB_Scans_00108` (prior run says Asterios Moutsokapas) before using it in a deck. No still may be copied into the Unity project or shipped; use these only as private reference.
- Troffer lens: film = flat opal (F13 viewed) vs. our doc's "prismatic K12" — Red should decide per zone (Level 0 photo-faithful prismatic vs. film-faithful opal). The Office target image also shows flat frosted panels.
