# 03 — Interactables: readability, key placement and shot support

Status: DRAFT 1 COMPLETE (2026-10-02, 23:3x). Research only; nothing in the project was changed.
Owner: visual chat, interactables workflow (readability / placement / shots agent).

Binding inputs, read first:
- [00_map_constraints.md](00_map_constraints.md) (map chat; every rule below obeys it);
- [01_inventory.md](01_inventory.md) (attach frames I reuse: hinge-local §1.6, window root §2.5, key §3.4);
- `../interaction_audit/10_audit_report.md` §3 (shot designs) and §4 (glass spec);
- `../office_and_film/22_era_lock.md` (1990; newest design 1993; oldest ~1955; nothing printed after 1990);
- Figma file `0tCbAiVUlrPId3RWd9LRif`: HR03 "What the Backrooms teach" (2331:873) and IR04 "Yellow by accident" (2320:2141), read with `get_screenshot`.

Sibling reports: period hardware and key/tag dimensions are `02_period_hardware.md`'s call; the locked-door type is `05_locked_door_type.md`'s call. This report gives the distance tests those choices must pass (§1.7) and the anchors they must carry (§3).

Code citations are `file:line` in the real project (read only). `MapWorld` = `Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs`, `Map` = `Assets/Scripts/FrontRoomsMap/FrontRoomsMap.cs`, `Game` = `Assets/Scripts/FrontRooms3DGame.cs`, `Units` = `Assets/Scripts/FrontRoomsMap/FrontRoomsModuleUnits.cs`.

---

## 0. Decisions in one table

| Question | Answer | Where |
|---|---|---|
| What makes a key findable at 6–12 m? | Its **host**, not the key. A key is a 60 mm object, which is recognisable only to about 5 m at 1080p. A 0.30 m dark key board is recognisable past 20 m. | §1.1, §1.4 P1 |
| What replaces the emissive yellow cube? | A brass key on a steel ring with a large plastic fob (zone tag), **no emission, no spin**, hung on a dark host, in a cell whose lamp is forced Steady. | §1.4, §2 |
| Glint? | Only the real one: bevelled brass edges whose lamp highlight crosses the bloom threshold (1.05). No sprite, no pulse. An opt-in "Item glint" accessibility setting is Red's call. | §1.4 P5 |
| Key colour vs Level 0 | Brass and manila are the wallpaper's own hue (IR04: "Put the yellow in the walls"). The read must come from **value** (light key and fob on a dark board) and from **non-yellow fob colours**. | §1.2, §1.4 P3 |
| Host anchor convention | `Key · zone {id}` (an unscaled empty, map change) sits **at the host's `key_hook` or `key_rest` anchor**. The key assembly hangs or lies from that point. The pickup reference is that point. | §2.2 |
| Do hosted keys spin? | **No.** | §2.2 |
| Hosts | v1: three new wall hosts the map spawns at chunk build (`Interact_KeyBoard`, `Interact_KeyCabinet`, `Interact_KeyHook`), render-only. v2: keys on existing kit furniture through the Office dresser. | §2.3 |
| Heights | Hook 1.40–1.55 m; fob hangs to 1.20–1.40 m. That is 0.1–0.4 m below the 1.62 m eye, in central vision from 2–8 m. | §2.2 |
| Zone identity | **Number + shape + colour** on the fob (never colour alone). The same number plate is on that zone's locked doors. Numbers read only at ≤ 1 m; shape and colour at 3–8 m. | §2.5 |
| Separable parts | Key, ring and fob are three assets. The lever, cylinder, thumbturn, bolt and strike are their own assets. Fracture pieces are one asset per variant with a per-vertex piece id, plus a `pieces` list in the sidecar. | §3 |
| Axis convention | The kit has point anchors only (`kitlib.py:498-499`). An axis is `<name>` plus `<name>_dir` at +0.10 m along the axis; roll is `<name>_up` at +0.10 m. | §3.1 |
| Blockers for the map chat | Unscaled `Key · zone`, `Window` root and `Door leaf`; the key cell's lamp forced Steady; key-cell choice needs a wall; host keep-clear handed to the dresser; spin off for hosted keys. | §2.6, §3.7 |

---

## 1. How interactables read in first person, 1–12 m

### 1.1 Viewing geometry: how many pixels a thing gets

- The player camera has a vertical FOV of 76° (`Game:227`). The eye is 1.62 m above the floor (`Units:92`). The E reach is 2.4 m (`Game:150`, ray at `Game:949`).
- At 1080p, one metre at distance *d* covers 1080 / (2 · *d* · tan 38°) ≈ **691 / *d* pixels**.
- Johnson's criteria give the line pairs needed across a target's critical dimension, at 50% probability: detection 1.0, recognition 4, identification 6.4. With 2 px per line pair, that is **2 px to detect, 8 px to recognise, ~13 px to identify** (https://en.wikipedia.org/wiki/Johnson%27s_criteria). These are lower bounds: they assume the target contrasts with its background.

Pixels across each feature (1080p, FOV 76°):

| Feature (critical size) | 1 m | 2 m | 3 m | 6 m | 9 m | 12 m | Recognised to | Identified to |
|---|---|---|---|---|---|---|---|---|
| Key, bow + blade (0.060 m) | 41 | 21 | 14 | 7 | 5 | 3.5 | 5.2 m | 3.2 m |
| Key bow (0.025 m) | 17 | 9 | 6 | 3 | 2 | 1.4 | 2.2 m | 1.3 m |
| Round rim tag (0.040 m) | 28 | 14 | 9 | 5 | 3 | 2.3 | 3.5 m | 2.1 m |
| Motel-style fob (0.10 m long) | 69 | 35 | 23 | 12 | 8 | 6 | 8.6 m | 5.3 m |
| Digit on a fob (0.012 m tall) | 8 | 4 | 3 | 1.4 | 0.9 | 0.7 | 1.0 m | 0.6 m |
| Key board (0.30 m wide) | 207 | 104 | 69 | 35 | 23 | 17 | 26 m | 16 m |
| Key cabinet (0.36 m wide) | 249 | 124 | 83 | 41 | 28 | 21 | 31 m | 19 m |
| Lock rose or deadbolt (0.06 m) | 41 | 21 | 14 | 7 | 5 | 3.5 | 5.2 m | 3.2 m |
| Lever (0.12 m) | 83 | 41 | 28 | 14 | 9 | 7 | 10 m | 6.4 m |
| Door sign or number plate (0.25 m) | 173 | 86 | 58 | 29 | 19 | 14 | 22 m | 13 m |
| Door leaf (0.98 m) | 677 | 339 | 226 | 113 | 75 | 56 | — | — |

What the table says:
1. **Beyond about 5 m the key itself cannot be recognised**, whatever its material. Only the host, and a big fob, carry the read from 6 to 12 m.
2. **Numbers are close-up information.** A digit on a fob is identifiable only at about 0.6 m. That is fine for the pickup presentation (held 0.35 m from the lens, audit §3.1, ≈ 24 px per digit), but not at a distance.
3. **Lock hardware alone cannot tell a locked door from a free door beyond ~5 m** (§1.7).

### 1.2 The light they read under (measured from the project files)

| | Level 0 zones | Office zones |
|---|---|---|
| Walls | `L0_Wallpaper` (`Wallpaper_Chevron_A.png`): mean sRGB (192, 173, 102), linear luminance **0.43**, a saturated yellow | `Office_Wall` (`Office_Drywall_A.png`): mean sRGB (181, 174, 157), luminance **0.43**, neutral greige |
| Floor | `Carpet_LoopPile_A.png`: sRGB (137, 121, 83), luminance 0.20 | `Office_CarpetTile_A.png`: sRGB (83, 91, 98), luminance 0.10, blue-grey |
| Lamp | One spot per cell, 162° outer / 96° inner, colour (1, .96, .88), range 10 m (12 m tall), intensity 5 (`MapWorld:1110-1119`, `:1768`) | Same, intensity 5.5 (`MapWorld:1777`) |
| Shadows | About one lamp in three may cast shadows, and only near the player (`MapWorld:1122`) | Same |
| Lamp failures | Rolled per lamp: 62% steady, 20% stutter, 10% failing, 5% dead with rare blinks, 3% dim (`MapWorld:1125-1128`). A module can force a mode (`MapWorld:1129-1130`; `ModuleLamp` in `FrontRoomsRoomModuleData.cs:30`) | Same |
| Grade | Global profile; bloom threshold **1.05** (`Assets/Resources/Rendering/FrontRoomsPost.asset:47-49`) | Adds an Office volume: contrast +4, saturation **−22**, a cool colour filter (.95, .99, .97) (`FrontRoomsPost_Office.asset:113-127`) |
| Reflections | Nothing in the world is reflected yet (audit F4). Metals show only the direct highlights of lamps | Same |

Means and luminance were computed from the textures on disk (64 × 64 downsample, sRGB-to-linear, Rec. 709 weights).

Three consequences:
- **Brass is camouflaged in Level 0.** `Prop_Brass` is metallic 1, smoothness 0.6, base (0.69, 0.54, 0.29) (`Assets/Resources/Surfaces/Prop_Brass.mat:59-66`). With no reflection environment it renders dark brown except at highlights. With a zone cubemap (audit §4.3) it reflects the yellow room at about the wall's own value. Either way, a brass key on yellow wallpaper has no hue contrast and little value contrast. Today's key (.96, .87, .23) is the same hue as the wall (`MapWorld:1787`).
- **About 8% of cells are dead or dim.** A key in such a cell is invisible without emission. Never place a key there (§2.4).
- **The Office grade removes 22% of saturation.** Colour codes must survive desaturation, so value and shape carry the code and hue is the backup.

The project's own rule (IR04, Figma 2320:2141): "Keep the light neutral. Put the yellow in the walls." A yellow key, a manila tag or an amber glow fights that rule.

### 1.3 What goes wrong with today's key

- It is an **emissive** yellow box 0.32 × 0.12 × 0.12 m, spinning at 90°/s, at 1.05 m in the middle of a cell (`MapWorld:783-789`, `:1738`). Audit frame `images/52_key_2m.png` shows it from 2 m.
- Emission makes it the only self-lit object in the scene that is not a lamp. It reads as a game token, not a key.
- The spin is a UI gesture; nothing real in a 1990 room spins.
- Its hue is the wallpaper's hue, so what reads is the glow. Remove the glow and nothing is left.
- It floats in mid-air, and can float inside furniture (01 §3.1, F10).

### 1.4 Principles (from the references, adapted to FrontRooms)

**P1. The host is the landmark; the key is the reward.**
- The distance table (§1.1) decides it: at 6–12 m the player can find a dark board or cabinet on a wall, not a key.
- Silent Hill 2 (remake): producer Motoi Okamoto said the remake avoids yellow paint and that "item placement and lighting will be designed to help the player guess where an item may be located". The team balances hidden items with obvious ones so the game does not become a "shelf searching game", and uses cues like knocked-over trash cans (Automaton, 2024-06-06, from a Famitsu interview: https://automaton-media.com/en/news/silent-hill-2-remake-will-not-use-yellow-paint-and-the-like-producer-assures/). The original game turned James's head toward nearby items (same article).
- Game Developer, "Level design tricks of the trade" (Jonathon Wilson, 2018-07-20): "people tend to be drawn to the brightest point on the screen"; landmarks grab attention; consistent colour meanings; overdoing brightness reads as hand-holding (https://www.gamedeveloper.com/design/level-design-tricks-of-the-trade).
- For FrontRooms: one family of hosts (a key board, a key cabinet, a lone hook), always on a wall, always at the same height, always under a working lamp. After the first key, the player knows what to scan walls for.

**P2. Light the spot, not the object.**
- The Level Design Book: lighting sets hierarchy ("Big important exits should have more important looking lighting"), and "a strong spotlight draws attention" (https://book.leveldesignbook.com/process/lighting).
- For FrontRooms: the key cell's lamp is forced Steady (mode 0). It is never dead, dim or failing. No extra light is added (00 forbids lights on these props).
- Optional, map chat: if the key cell's lamp is one of the shadow casters (`MapWorld:1122`), the hung fob throws a crisp shadow on the board, which helps. Do not force shadows (budget).

**P3. Value before hue.**
- Level 0: a **dark** host (board luminance ~0.05–0.15) on the 0.43 wallpaper, with a light or saturated fob on it. That gives contrast at the host (3–8:1) and again at the key (fob against board).
- Office: the wall is neutral 0.43. A putty or grey steel cabinet with a **light** interior and a dark key and coloured fob works, or the dark board as in Level 0.
- Fob colours: never yellow, orange, tan or manila in Level 0. The palette is in §2.5.

**P4. Silhouette: hang it flat to the viewer.**
- A key is recognised by its ring bow plus the toothed blade outline. Hung on a hook, the key and fob face the room flat, at full size.
- Lying flat on a desk, a 60 mm key seen from 4 m at a 13° grazing angle projects to about 0.014 m (≈ 2 px). Flat placements need a vertical element: the fob hangs over the front edge (§2.3, "over-edge" pose).

**P5. A restrained glint, and only a physical one.**
- Make the real lamp highlight do the work:
  - bevel the bow and blade edges at least 1 mm, so the highlight has area;
  - keep `Prop_Brass` smoothness 0.55–0.7, so the lobe is wide enough to catch the player at several angles;
  - add a light wear normal map on the key (the 1024² key texture the audit asks for, §6.4).
- The cell's lamp is above and in front of a wall host. A small specular highlight on brass from a 5-intensity lamp should cross the 1.05 bloom threshold for a few frames as the player moves. That is a natural glint, and nothing else in the room does it. **ESTIMATE: verify in a capture** (05's harness) that the highlight blooms and is not too strong.
- No sparkle sprite, no periodic flash, no rim light, no outline.
  - Survival horror's common item glints are UI by another name. They also fight HR03 rule 04, "Heard, then seen".
  - TLOU Part II shows how to offer the strong version as an opt-in: its High Contrast Display "mutes environment colors and adds distinct contrast coloring to allies, enemies, items, and interactive objects" (Naughty Dog, 2020-06-09: https://naughtydog.com/blog/THE_LAST_OF_US_PART_II_ACCESSIBILITY_FEATURES_DETAILED).
- Option for Red: an "Item glint" setting, off by default, in the settings panel planned as audit Phase 1.10. It adds a small sparkle on keys within 8 m and in view, at most once every 3 s.
- Until audit F4 step 0 (zone cubemaps) lands, brass will read too dark between highlights. Do **not** fix that with emission. If needed, lower metallic to ~0.85 on the key material only, so some diffuse brass shows (ESTIMATE; check in the capture).

**P6. Still things in a still room.**
- No spin, no bob. A hung key may sway once, for about 1 s, if a door within 3 m slams. That is cheap transform code driven by the existing `DoorMoved` event. It is optional, and it is "heard, then seen" for keys.
- Sound-chat option: a faint key jingle on that sway (a NEW event, sound chat's call).

**P7. One grammar, applied the same way every time.**
- Keys always hang on the same three host types, at the same height band, under a steady lamp.
- HR03 rule 01, "One error", can be applied to the host. Every hook on the board is empty except one, or every hook carries the same number. One wrong thing you can count.

**P8. Never colour alone.**
- Game Accessibility Guidelines, basic level: "Ensure no essential information is conveyed by a fixed colour alone" (https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-colour-alone/). About 8–10% of males have red–green difficulty (same page).
- So zone identity is number + shape + colour (§2.5).

### 1.5 Distance bands: what carries the read

| Distance | What the player must get | What carries it |
|---|---|---|
| 6–12 m | "There is something on that wall" | The host: a dark 0.30 × 0.40 m board or cabinet under a working lamp, at eye level |
| 3–6 m | "It is a key, and it is this zone's kind" | The fob's shape and colour (0.10 m fob, recognised to 8.6 m) plus the hanging silhouette |
| 1–3 m | "It is brass, it is real" | The key silhouette (identified to 3.2 m), the bevel glint, the ring |
| ≤ 0.9 m (horizontal) | Pickup | Today: automatic (`MapWorld:1740`). With the audit §3.1 shot: E · TAKE KEY |
| 0.35 m (held pose) | "This is zone 14's key" | The number on the fob, ≈ 24 px per digit at 1080p |

### 1.6 Other interactables in the same light

- **Windows.** A pane must read as glass at 3–12 m. That needs the stop, sill and grime in audit §4.1–4.2; clear values alone made the pane invisible (audit §4.2, 05 frames 08–11). Readability needs nothing extra from this report; the shot anchors are in §3.5.
- **Doors.** "Doorway first": "The 1.0 × 2.1 m door is its picture frame. It has to read there as a dark shape at 12 m." (HR03, Figma 2331:873). That rule is written for the hunter, but it sets the project's 12 m standard. I use it for the locked-door test below.

### 1.7 Locked vs free doors: the distance test the door type must pass

05 chooses the locked type. Whatever it picks must pass these tests (numbers from §1.1).

| Distance | What must differ | Features that can carry it | Features that cannot |
|---|---|---|---|
| 8–12 m | The door **type**, as a whole shape or value | The leaf's material and value over the whole 0.98 × 2.08 m; the frame type (a pressed steel frame vs a wood casing, 0.05–0.10 m faces along 2.1 m); a sign or number plate ≥ 0.20 m wide; a vision lite present or absent (≥ 0.10 m wide) | The cylinder, the rose, the hinge type, a kick plate in the same metal as the free door |
| 3–8 m | Confirmation | Two hardware points (deadbolt above lever) vs one; the lever vs a push plate; a 0.25 m plate's text block | Digits, keyways |
| ≤ 3 m | Zone and state | The number plate's digits (identified to ~2.7 m at 0.05 m high); the cylinder; a thumbturn's orientation on the inside face | — |

Value check against today's materials:
- The veneer leaf is luminance **0.19** (`DoorVeneer_A.png`, sRGB 157, 109, 59). The walls are 0.43.
- A locked type at a similar value but a different hue (for example a mid-grey painted steel) will **not** separate at 12 m under Office's −22 saturation.
- Aim for a value step of at least 2:1 from the veneer: a dark painted steel leaf (luminance ≤ 0.09) or a light one (≥ 0.38). The light option merges with the walls in both zones, so **dark is the safer side**. This is a recommendation to 05, not a decision.

Both faces must carry the type, because a door is approached from both sides. 00 says a locked door that has been unlocked keeps the locked model. The only distant state cue is then whether the door stands ajar (audit §3.2 "ajar, then push"). Up close, a locked-type door that is no longer locked does not rattle (§3.4 of the audit). Flag for Red: is "locked-type but already opened" allowed to be ambiguous from a distance once shut again?

---

## 2. Key placement

### 2.1 What the code does today

- One key per zone, none in Tall zones. The validator fails a Low or Standard zone without one (`Assets/Scripts/FrontRoomsMap/FrontRoomsMapValidator.cs:196-201`).
- `keyCell` is the zone cell whose centre is nearest the zone's site (`Map:627-651`). It can be a corridor, a room's middle or a module room (01 §3.1).
- The key is built with the chunk, at `keyCell` centre, 1.05 m up (`MapWorld:781-790`).
- Furnishing happens **later and asynchronously**: rooms are queued and dressed one per frame (`MapWorld:1258-1282`). Office rooms get the Office dresser through reflection (`MapWorld:1333-1342`); large halls sometimes get a pile (`MapWorld:1344-1356`). `KeepClear` covers only openings (`MapWorld:1565`).
- Consequence: **the key cannot wait for furniture.** v1 hosts must be spawned by the map, with the key, at chunk build. Furniture hosts (v2) need a contract with the dresser (§2.3 B).

### 2.2 Host anchor convention (the answer 00 asks for)

1. Every host asset has one or more anchors named **`key_hook`** (a hung key: the point where the ring touches the hook) or **`key_rest`** (a key lying on a surface: the contact centre). These are in the host sidecar, Unity space, like every kit anchor (`kitlib.py:498-499, 806`).
2. The map makes `Key · zone {id}` an **unscaled empty** (01 F2; today it is the scaled cube, `MapWorld:783-788`). It places that empty **at the host anchor's world position**. Its rotation equals the host's (local +Z = the host's front, facing the room).
3. The key model goes in as children of that empty, posed for the anchor type (§3.2):
   - `key_hook`: the ring hangs from the origin, the key and fob hang below it, flats facing +Z (the room);
   - `key_rest`: the key lies on the surface at the origin;
   - `key_rest` + `edge`: the key lies just behind the front edge, and the ring and fob hang over that edge down the front face.
4. **The pickup reference stays the empty's position.** For a hung key that is the hook point, 0.03–0.06 m off the wall face. The player's centre can get to 0.30 m from the face (radius 0.3, `Units:92`), so the horizontal distance is ≤ 0.36 m, well inside 0.9 m. Rule for every host: **`key_hook` / `key_rest` must lie within 0.55 m horizontally of floor a 0.3 m capsule can stand on.** That leaves 0.35 m of margin under the 0.9 m pickup.
5. **Hosted keys do not spin** (00's open question). `CollectKeys` skips the rotate for any key the map placed on a host (map change, `MapWorld:1738`). A host-less fallback key (§2.4, last resort) also stops: it lies on the floor.
6. **Heights.** `key_hook` at **1.40–1.55 m** above the floor:
   - the key and fob hang to about 1.20–1.40 m;
   - from 2–8 m that is about 2–12° below the eye line, in central vision;
   - it is above desk tops (0.74–0.76 m) but below the tops of cubicle panels (1.52–1.65 m), so in Office rooms the host goes on a perimeter wall, never behind a pod (§2.4);
   - the eye-to-hook distance from the nearest standing spot is ≈ 0.40 m, well inside the 2.4 m aim reach if pickup becomes aim-and-press (audit §3.1).
   - `key_rest` on furniture: 0.60–1.32 m (the kit supports listed in §2.3 B). Below 0.6 m (low tables, the floor) a key is found only by someone already searching that spot.
7. **Proud limit.** Wall hosts stand ≤ 0.10 m off the wall face. The camera never comes closer than 0.30 m to a wall face (player radius), so a render-only host this thin never clips the near plane (0.06 m, `Game:227`). Shot offsets are clamped by the rig's 0.1 m spherecast (audit §6.4).

### 2.3 Host catalogue

#### A. New hosts (v1). All render-only (`kit.no_collider()`, 00), wall-mounted, spawned by the map with the key

Shared convention for all three (proposal; the modules do not exist yet):
- origin on the **wall face plane**, centred horizontally, at **floor level** (y = 0);
- front (Blender −Y) faces the room (Unity +Z); the back is flush with the wall face;
- heights are baked into the asset, so the map needs only a wall-face point at floor level and a facing;
- sidecar `placement` = Wall via the tag `wall_decor` (`kitlib.py:820`).
- File names: `assets/interact_key_board.py`, `assets/interact_key_cabinet.py`, `assets/interact_key_hook.py`.

| Asset | What it is (era) | Size, proud | Slots (existing only) | Anchors | Zones |
|---|---|---|---|---|---|
| `Interact_KeyBoard` | A plain key board: a dark painted or stained board with two rows of brass cup hooks and a painted number under each. The kind of thing that hangs in a store's back office. Timeless (1950–2000) | 0.30 W × 0.40 H × 0.018 board; hooks to 0.05 proud; top at 1.65 m | `Prop_Hardboard` or `Prop_WoodDark` (board), `Prop_Brass` (hooks), `Prop_Paper` (number strip) | `hook_0`–`hook_7` (rows at 1.42 and 1.54 m), `key_hook` (= one of them, chosen per seed by the map) | Level 0 (first choice); Office (second) |
| `Interact_KeyCabinet` | A wall key cabinet in painted steel, with numbered hooks on a light back panel. Its door is swung fully open and flat to the wall (≈ 175°), so nothing sticks out. Numbered-tag cabinets were sold for decades; Telkee has made them since at least 1965 (https://architectureanddesign.com.au/suppliers/telkee-key-cabinets; Australian maker, so US-period confirmation is for 02 §9) | 0.36 W × 0.46 H × 0.08 D; door 0.36 × 0.46 × 0.02 beside it; ≤ 0.10 proud; top at 1.70 m | `Prop_SteelPutty` or `Prop_SteelAlmond` (body, door), `Prop_PlasticWhite` (back panel), `Prop_Chrome` (hooks), `Prop_Label` (index card, existing atlas cell) | `hook_r{0..3}_c{0..5}`, `key_hook`, `door_hinge` | Office (first choice) |
| `Interact_KeyHook` | A single brass cup hook, or a nail, in the wall. The emptiest host: one key in an empty yellow room | hook ≈ 0.03; at 1.48 m | `Prop_Brass` | `key_hook` | Level 0 (rare: at most 1 in 4 keys, and only when the key's fob is a dark colour, because there is no board behind it, §1.4 P3) |

The one-error touch (optional, P7): on the board and the cabinet, every hook is empty except the zone key's.

#### B. Existing kit props as hosts (v2: needs the dresser to cooperate)

Anchors here are computed by the map or the dresser from the sidecar `supports` and `anchors` (values from `Assets/Resources/Props/Models/*.json`), so **no existing asset module has to change**. Rule for surfaces: `key_rest` = the support's front edge minus 0.05 m (front = +Z in Unity), with the fob over the edge, unless stated.

| Prop | Spot (Unity, metres) | Height | Read at distance | Era | Notes |
|---|---|---|---|---|---|
| `Kit_FilingCabinet` | `lock` anchor (−0.128, 1.279, 0.332): **the key left in the cabinet's own lock**, fob hanging down the drawer face | 1.28 | Very good: vertical fob on a putty face at chest height | timeless | Best Office furniture host. The key "in a lock" also previews the unlock shot |
| `Kit_Copier` | `cover` support, y 1.126 | 1.13 | Good with the fob over the front edge | current | Office |
| `Kit_Bookcase` | shelf 4 front, y 1.455 (or shelf 3, 1.115) | 1.12–1.46 | Good: the fob hangs over the shelf lip, in a dark shelf cavity | current | Level 0 piles, home rooms |
| `Kit_Hutch` / `_Cherry` | `buffet ledge`, y 0.80 | 0.80 | Fair | current | |
| `Kit_Dresser70s` | `top`, y 1.22 | 1.22 | Good | second-hand | |
| `Kit_PlyCabinet` | `top`, y 1.20 | 1.20 | Good | timeless | |
| `Kit_StepStool` | `top`, y 1.00 | 1.00 | Fair | second-hand | Floor host in an empty hall (needs collider policy, below) |
| `Kit_HatStand` | pegs ≈ 1.65–1.75 (no peg anchors yet; the visual chat adds `peg_0..n`) | ~1.7 | Very good silhouette in an empty Level 0 hall: a key ring on a coat stand | timeless | Needs peg anchors added to `hat_stand.py` (visual chat, a later pass) |
| `Kit_OfficeDesk` / `Kit_DeskPedestal` / `Kit_Credenza` | `top`, y 0.74–0.76, near the front edge | 0.74–0.76 | Poor beyond 3 m unless over-edge | current | SH2's "obviously placed" balance: use sometimes, not always |
| `Kit_CRTMonitor` on a desk | `top`, y 0.407 + 0.74 ≈ 1.15 | 1.15 | Good (a classic office spot) | current | Desk-top stack only |
| `Kit_SideTableTurned`, `Kit_Nightstand2`, `Kit_RollingCabinet`, `Kit_DresserLow` | `top`, 0.60–0.78 | 0.60–0.78 | Fair | mixed | Home rooms |
| Excluded | `Kit_VendingMachine` top (1.83: above the eye, cannot be seen), `Kit_TrashBin` and `Kit_Urn` mouths (0.38, inside), seats (sitting surfaces read wrong) | | | | |

Collider policy for floor hosts (flag for the map chat): 00 says key hosts are render-only. That fits wall hosts. A floor host from the kit (a step stool, a hat stand) is furniture. It should keep its kit collider, as the dresser's furniture does, or the player walks through it. With a collider, the key's horizontal-distance pickup still works (key on top; the player stands at the collider's edge, 0.3 m + half the footprint ≤ 0.55 m for every prop above except the desks, whose `key_rest` must then be within 0.25 m of the front edge).

#### C. Pose assets for the key on hosts

The key assembly is posed by code from three parts (§3.2), so there is no separate "hung key" mesh. The three poses: **hung**, **flat**, **over-edge**.

### 2.4 Rules per zone type

**Which cell.** Map change: `PlaceKey` (`Map:627-651`) prefers, among zone cells near the site, one that has a **usable wall stretch**:
- at least 0.60 m of plain wall face;
- not inside a keep-clear strip;
- at least 0.35 m from any opening's edge (clear of the trim and of a leaf that overlaps the frame);
- not in the start area.
Then choose the stretch facing the cell's main way in (an Open, Arch or Door edge opposite or beside it), so the host is in view on entry. If no cell within the search has one, fall back to the nearest cell and put the key **flat on the carpet under the lamp** with its fob up (last resort; no host).

**Lamp.** The key cell's lamp is forced Steady (mode 0), whatever the roll (`MapWorld:1125-1130`). If a module fixes a lamp mode, a module room with a key keeps Steady.

**Level 0 (Low 2.4 m, Standard 2.9 m; empty rooms; piles in big halls):**
1. `Interact_KeyBoard` (dark board) on the chosen stretch. Default.
2. `Interact_KeyHook` instead, at most 1 key in 4, and only with a dark fob (red or blue, §2.5).
3. Never a yellow, orange, tan or manila fob or board.
4. v2: if the key cell lies in a pile hall, the pile may carry the key on a `Kit_Bookcase` shelf or a `Kit_HatStand` peg, but only when the pile places that piece upright and within 0.55 m of standable floor. Piles are deterministic per seed, so the map can ask after dressing; otherwise keep the wall host.

**Office (Standard ceilings; dressed rooms):**
1. `Interact_KeyCabinet` on a **perimeter wall** stretch of the key cell, preferably near the room's door. Cubicle panels are 1.52–1.65 m tall (`Kit_CubiclePanel*`), so a host behind a pod is hidden.
2. `Interact_KeyBoard` second.
3. The map passes the host's footprint plus an approach strip, **(host width + 0.6 m) × 1.0 m deep**, to the Office dresser as a keep-clear rect. `Dress` already passes keep-clear rects to the dresser (`MapWorld:1340`), so the dresser keeps vending machines, copiers and panels out of the way. This is a map-side change: add the rect to `clear` in `Dress` (`MapWorld:1293`).
4. v2: the dresser may host the key itself, in the `Kit_FilingCabinet` lock first. Contract: `Dress(..., keyCellRect)` returns the chosen `key_rest` world point; the map then moves `Key · zone {id}` there and skips the wall host. The key exists before dressing (the queue runs over later frames), so it may move once, within a few frames of the room being dressed and usually before the player is near (UNVERIFIED: dress order vs player distance).

**Tall zones:** no key (validator, above).
**Module rooms (Level Designer):** a module may place a host prop tagged `key_host`. The map then uses that prop's `key_hook` / `key_rest` instead of choosing a wall (proposal for the map chat; the module data already carries props, `FrontRoomsRoomModuleData.cs:32-40`).

### 2.5 Per-zone key identity (era-safe and readable)

Three channels, so no information rides on colour alone (P8):

| Channel | Values | Read at | Era evidence |
|---|---|---|---|
| **Number** | Two digits, `00`–`99`, from a hash of the zone id. Hand-stamped or embossed on the fob | ≤ 1 m (held pose: yes) | Motel fobs printed room numbers (The Henry Ford, Tivoli Motel key, 1955–1980, fob 1.5625 in wide, green and white plastic, "DROP IN ANY MAIL BOX / WE GUARANTEE POSTAGE": https://www.thehenryford.org/collections/explore/artifact/365287). Dymo embossing labelers date from 1958 (https://en.wikipedia.org/wiki/Dymo_Corporation) |
| **Shape** | Diamond motel fob (0.04 × 0.10 m), rectangular cabinet tag (0.03 × 0.06 m), round rim tag (0.04 m) | Diamond 3–8 m; the others 2–4 m | Rim tags: metal-rimmed paper tags go back to the 19th century (Dennison, search result only, UNVERIFIED). Cabinet tags: numbered plastic tags ship with key cabinets (Telkee page above) |
| **Colour** | Red `Prop_PlasticRed`, blue `Prop_PlasticBlue`, white `Prop_PlasticWhite`, and optionally green (needs a new slot, §3.8) | 3–8 m when the fob is the diamond | — |

- 3 shapes × 3 colours = 9 identities with existing slots (12 with green).
- The map picks the shape and colour so that **two zones that share a door never share both**. It knows the adjacency through its door edges. The number makes every key unique up close.
- **No yellow, orange or manila fobs** (§1.2). White fobs read best on the dark board; red and blue read on the cabinet's light back panel and on the board.
- **The door carries the same identity.** Each face of a locked-type door gets a small engraved number plate (about 0.10 × 0.05 m, digits 0.035–0.05 m) in the fob's colour and shape family, beside the cylinder. The number is identified from about 2–2.7 m. With today's key rule (the key of the zone the player stands in, 00), each face shows the zone on its own side. If Red changes the rule (audit §7 Q3), the plate follows it.
- **HUD:** the key panel label shows the same number ("KEY 14") instead of "LEVEL 0 KEY" (`Game:1408-1415`; audit F16).
- **Digits need a texture.** The `Prop_Label` atlas is full (16 cells in use, `Tools/lookdev/gen_props.py:244-305`). Proposal: a new slot `Prop_KeyTagNo`, a 10 × 10 atlas of "00"–"99" stamped numbers, one quad per fob, with the cell chosen per renderer through a material property block (UV offset). **Not added**: kitlib.py must not be edited by this workflow, so this is reported in §3.8.

### 2.6 Asks to the map chat (placement)

1. `Key · zone {id}` as an unscaled empty; keep its name. The model and the host go in as children (01 F2).
2. No spin for hosted keys (`MapWorld:1738`).
3. `PlaceKey` prefers a cell with a usable wall stretch; the host goes on the stretch facing the way in (§2.4).
4. The key cell's lamp forced Steady.
5. Host keep-clear rect handed to the Office dresser (§2.4 Office 3).
6. Fob shape and colour per zone, distinct across shared doors; number from the zone hash; the same values on the locked doors' plates.
7. v2: the dresser-hosted key contract (§2.4 Office 4) and pile hosts (§2.4 Level 0, item 4).

---

## 3. Shot support: anchors and separable parts

### 3.1 Conventions

- **Anchors are points.** `kit.anchor(name, pos)` stores a position, exported to Unity space as (−x, z, −y) (`kitlib.py:498-499, 789-806`). There is no orientation.
- **Axes:** an axis is a pair: `<name>` and `<name>_dir`, placed 0.10 m along the axis. Direction = normalise(`_dir` − `<name>`). It survives the handedness change because both points convert the same way.
- **Roll:** `<name>_up`, 0.10 m along the reference "up" (for example the key's bitting edge).
- **Moving parts are separate assets.** One asset is one joined mesh (`kitlib.py:632-667`), so anything that moves on its own (key, ring, fob, lever, cylinder, thumbturn, bolt, strike plate, fracture pieces) is either its own asset, with its origin at its pivot, or encoded inside one asset (fracture, §3.5).
- **Assembly** happens in Unity: the parent's `<part>_pivot` anchor plus `<part>_pivot_dir` give the child's position and axis.
- **Naming:** `Interact_<Thing>[_<Part>]` for assets; the anchors below; parts in the hierarchy keep the asset name. Avoid the hazard names in 01 F6 (`Door hinge*`, `Light`, `fluorescent light*`, `double door * hinge`).
- **Frames reused from 01:**
  - **Door:** hinge-local (01 §1.6). Origin on the hinge jamb's edge, wall centre line, floor. +Z toward the latch (0 → 1.0), +Y up, ±X the wall normal. LockPoint in this frame is **(±0.055, 1.00, 0.92)**; the sign is the opener's side.
  - **Window:** a proposed unscaled root `Window {a}-{b}` at the opening centre, on the wall line, at floor level. Local +Z into cell b. The opening is X ±0.70, Y 0.35–2.00 (01 §2.5).
  - **Key:** the `Key · zone {id}` empty (§2.2).
- **Face suffixes on doors:** `_px` = the face on hinge-local +X, `_nx` = the face on −X. This is the `side` sign `LockPoint` uses (`MapWorld:1640-1648`).

### 3.2 Key (audit §3.1 pickup, §3.2 unlock)

Three assets, so the fob can swing and the key can turn while the ring and fob hang (§3.1 "the tag swings, damped, two swings"; §3.2 "the key turns 90°"):

| Asset | Origin and axes (Unity, part-local) | Anchors | Material | Notes |
|---|---|---|---|---|
| `Interact_Key` | Origin = **bow centre on the key's turning axis** (01 §3.4). +Z = insertion direction (bow → tip). +Y = bitting edge (teeth up). ±X = the flats | `tip` (0, 0, L), `shoulder` (where the blade meets the bow; at full insertion it sits on the cylinder face), `grip` (where a thumb and finger pinch the bow; for the optional posed hand, audit §3.0), `ring_hole` + `ring_hole_dir` (along X) | `Prop_Brass` | Real size (02 owns the numbers; ESTIMATE ≈ 0.058 m long, blade ≈ 0.028 m). ≥ 1 mm bevels; a 1024² texture with a wear normal (audit §6.4). Under ~600 tris, so no LOD1 (`kitlib.py:23-25`) |
| `Interact_KeyRing` | Origin = the ring's **top inner point** (where it hangs on a hook) | `key_contact`, `tag_contact` (bottom inner points, 8 mm apart) | `Prop_Chrome` | Split steel ring, ≈ 25–30 mm |
| `Interact_KeyTag_{Diamond, Rect, Round}` | Origin = the fob's **hole** (its swing pivot). It hangs along −Y. Front face +Z | `face` (centre), `number` (centre of the number quad) | `Prop_PlasticRed/Blue/White` via `VARIANTS` (`kitlib.py:27`), plus `Prop_KeyTagNo` for the number (new slot, §3.8) | Diamond 0.04 × 0.10 m (motel style); rectangle 0.03 × 0.06; round 0.04 |

Shot use:
- **Pickup (§3.1):** the held pose centres on the midpoint of `grip` and the fob's `face`, 0.35 m ahead of the lens. The fob turns its `face` to the lens. The fob swings about its origin. The number is readable here (§1.1).
- **Unlock (§3.2):**
  - Align key +Z to the lock's `keyhole_*_dir` and key +Y to `keyhole_*_up`.
  - Start with `tip` 3 cm in front of `keyhole_*`.
  - Slide in until `shoulder` = `keyhole_*` (the slide is the blade length, ≈ the audit's 2.5 cm; 02 sets it).
  - Turn 90° about key +Z. Unlock turns the top of the key toward the hinge edge (convention for the picture; the real direction depends on the lock's handing, UNVERIFIED).
  - The ring and fob hang from `ring_hole` and swing under gravity while the key turns (transform code, no physics needed).
- **Hosted (§2.2):** hung = ring origin at the empty, key from `key_contact` with tip down and flats to +Z, fob from `tag_contact` with its face to +Z.

### 3.3 Locked-door hardware (audit §3.2 unlock with the head dip, §3.4 rattle, §3.7 Relay break)

The leaf model is a child of `Door hinge {a}-{b}` in hinge-local space (00, 01 §1.6). If the jolts in audit §3.4 and §3.7 go on `Door leaf` (they must, or `DoorSound` hears a door opening, audit F11), the visual leaf must ride with them. So: either the map makes `Door leaf` unscaled and the model goes under it, or the jolt code moves the model too. Map chat's call (§3.7).

Anchors the **leaf** asset must carry (both faces, unless 05 chooses a one-sided lock):

| Anchor | Where (hinge-local; t = visible leaf thickness ≤ 0.05) | Used by |
|---|---|---|
| `keyhole_px` / `keyhole_nx` | On the cylinder's face at the keyway centre. Default: the LockPoint spot (±0.055, 1.00, 0.92). If 05 puts a separate deadbolt above the lever, this moves up (say 1.15–1.20 m) and the map should move `LockPoint` to it, so `DoorUnlocked` and the sound come from the keyhole | §3.2 framing pose P, key alignment |
| `keyhole_px_dir` / `_nx_dir` | 0.10 m **into** the leaf (∓X) | key insertion axis |
| `keyhole_px_up` / `_nx_up` | +Y (pins on top; US pin-tumbler keys go in teeth up. The convention is UNVERIFIED for every lock; 02 confirms) | key roll |
| `lever_px_pivot` / `_nx_pivot` + `_dir` | The rose centre on the spindle; `_dir` = outward normal (±X) | §3.3 lever down 35°, §3.4 down 20° and stop |
| `lever_px_tip` / `_nx_tip` | The grip end; the lever points toward the hinge side | sanity check for the clip rule |
| `tagplate_px` / `_nx` | Centre of the zone number plate (§2.5) | identity; framing |
| `thumbturn_nx` (or `_px`) | Only with a single-cylinder deadbolt: the inside turn piece | turns 90° with the key (both faces show state) |
| `latchbolt`, `deadbolt` + `_dir` | On the latch edge face (z ≈ 0.99 or the visual leaf's edge), at bolt height; `_dir` = +Z (throw) | open-door read of a thrown bolt; §3.7 |
| `pivot_top`, `pivot_floor` | On the hinge axis (x 0, z 0) at y 2.10 and 0 | 01 F9: the map's pivot is centre-hung double-acting. Any visible pivot or hinge must sit on this axis, or the leaf visibly orbits the wrong point. §3.7 hang-crooked rotates about `pivot_floor` (top pivot torn) |
| `hinge_top`, `hinge_mid`, `hinge_bottom` | Only if Red takes 00's Option A (single swing with butt hinges). Same axis rule | Option A |
| `damage_latch` | Centre of the splinter zone on the latch edge, y ≈ 1.0–1.2 | §3.7 damage 1 and 2, splinter emitter |
| `kick_px` / `_nx` | Kick plate centre, if any | — |

Separable parts (own assets, origin at the pivot):

| Part | Pivot and motion | Why separate |
|---|---|---|
| `Interact_Lever` (one per face) | Spindle axis (±X); rotates −35° (open), −20° then hard stop (rattle) | §3.3, §3.4 |
| `Interact_LockCylinder` | Static; carries its own `keyhole` anchors, merged into the leaf's anchors by the prefab builder | different metal, close-up texel density (audit §6.4: ≥ 1,600 px/m at the framing distance, 2,048 to be safe) |
| `Interact_Thumbturn` | Spindle axis; 90° | shows the lock state on the inside |
| `Interact_Bolt` (deadbolt) | Translates 25 mm along −Z (into the leaf) | §3.2 bolt retract beat; open-door read |
| `Interact_StrikePlate` (on the frame asset) | Free; flies off on the break | §3.7 "the strike plate flies off" |
| Leaf damage variants `_Dmg1`, `_Dmg2` | Same origin as the leaf | §3.7 at 50% and 80% of `breakDoorSeconds` |

Anchors the **frame** asset must carry (a sibling under the chunk root, not under the hinge; it does not swing):
- `strike_latch`, `strike_deadbolt` on the latch jamb's stop face;
- `head_dust_a`, `head_dust_b` (the ends of the head soffit line, for dust on blows, §3.7);
- `threshold` (centre).

**Head-dip shot (Red's "lowering your head to unlock").** What the models must allow:
1. **The keyhole height sets how much the head dips.** Framing pose P is 0.45 m out along the face normal, with the eye dropped by at most 0.25 m (audit §3.2):
   - keyhole at 1.00 m: the camera at ≈ 1.37 m looks down ≈ 39° at it. A clear head dip;
   - keyhole at 1.20 m: ≈ 21° down. A milder dip;
   - below 0.9 m the camera must crouch; above 1.3 m no dip reads.
   - So 1.0–1.2 m is the band where Red's shot reads (1.0 for the strongest dip).
2. **Clear view cone.** Nothing on the face may block a 20° half-angle cone from P to `keyhole_*`. The lever below or beside the cylinder is fine. The number plate goes beside the cylinder, never above it. The hanging ring and fob of the key fall below the keyhole.
3. **Clip rule.** Everything proud of the leaf face stays ≤ 0.07 m per side (00). 01 F8 shows the real clip zone is the first ~0.10 m from the pivot; the latch-side lock is safe.
4. **Detail.** The audit's close-up spec (≥ 1,600 px/m at ≈ 0.57 m, FOV 62, §6.4) applies to the cylinder, the rose, the plate and the leaf around them: a detail map or a lock-plate mesh.
5. **Both faces.** With both-ways doors and "the key of the zone you stand in", a locked door is unlocked from either side. So either both faces carry a keyed cylinder (a double-cylinder deadbolt or a keyed lever on each side), or the map chooses one locked face. 05's call.

### 3.4 Free door (audit §3.3 open, shut)

Same leaf frame and the same `lever_*`, `latchbolt`, `pivot_*` anchors. No `keyhole_*`, `thumbturn_*` or `tagplate_*`. The Relay-break anchors are shared (§3.3). This keeps the two door variants on the same gap-free frame, as 00 asks.

### 3.5 Window (audit §3.5 hold and shatter, §3.6 climb, §4.4)

All window assets share the proposed **`Window {a}-{b}` root** (01 §2.5): origin at the opening centre on the wall line at floor level, local +Z into cell b, opening X ±0.70, Y 0.35–2.00, gameplay pane Z ±0.015. The frame and stops stay outside the opening (00).

**Frame and glazing asset** (`Interact_WindowFrame`, render-only):

| Anchor | Value (window root) | Used by |
|---|---|---|
| `pane_bl`, `pane_br`, `pane_tl`, `pane_tr` | (∓0.70, 0.35, 0), (∓0.70, 2.00, 0) | crack UV frame; fracture alignment |
| `rebate_l`, `rebate_r`, `rebate_t`, `rebate_b` | Midpoints of the glass edge lines inside the rebate (the glass bite beyond the opening, set by 02; audit §4.1 suggests stops 18 mm wide × 12 mm deep) | teeth sockets; where the glass edge hides |
| `impact_00` … `impact_22` | The 3 × 3 authored impact centres: X ∈ {−0.40, 0, +0.40}; Y ∈ {0.90, 1.30, 1.65} (world height; each ≥ 0.2 m from the frame, audit §3.5). A player facing the pane aims at about 1.62 m, so the top row gets most hits | snap the hit point; pick the fracture variant |
| `sill_plant_pz`, `sill_plant_nz` | Sill top centre, 0.05 m toward each side | §3.6 the plant at 0.15 s |
| `floor_pz`, `floor_nz` | (0, 0, ±0.45): floor-glass patch centres | §3.5 settle and rest; §3.6 landing footsteps |
| `palm` | Default smudge point, (0, 1.30, ±0.015) | §3.5 push stage when no hit point is passed |

The pane's UV0 must map the opening exactly: u = (x + 0.70) / 1.40, v = (y − 0.35) / 1.65. Then `GlassCracked(pos, stage, uv)` (audit §6.4) and the crack mask share one frame.

**Fracture variants** (Red's requirement c; audit §4.4 item 2):
- `Interact_PaneFrac_{r}{c}{v}`: r, c ∈ 0..2 (the impact centres), v ∈ a, b. 18 assets.
- Each piece is tagged **inner** (flies away from the player at 2–4 m/s), **middle** (drops with a 0–300 ms stagger) or **tooth** (stays in the rebate).
- **Breaking again on the floor:** every inner or middle piece larger than about 0.10 × 0.10 m is pre-split into 2–4 sub-pieces that share its outline. At its first floor contact faster than about 1.5 m/s (ESTIMATE), Unity swaps the piece for its sub-pieces with a small outward impulse. Sub-pieces under about 4 cm do not split again; after about 1.5 s they sleep and merge into the static floor-glass mesh (audit §3.5 "Rest").
- **Encoding, within today's pipeline:** one joined mesh per variant, with a per-vertex piece id written by the asset module before `finish()` joins the parts (a colour attribute or a second UV channel). The module also adds a `pieces` list to `kit.meta`: `export()` copies `self.meta` into the sidecar (`kitlib.py:797`), so a custom key passes through. Each entry: id, class, parent id (for sub-pieces), centroid (converted to Unity space in the module), area, and edge side for teeth. Unity splits the mesh by id once at load and caches it. **Verify first** with a small probe module, like `axis_probe.py`, that the attribute survives the FBX export and Unity import (UNVERIFIED).
- **Crack masks:** one per variant, baked from the variant's own fracture edges (audit §4.4): stage 1 = the radial edges out to 25–35%, stage 2 = radials to the frame plus 1–2 rings, shatter = all edges.
- **Floor glass:** `Interact_FloorGlass_{a..d}`, flat scatters of small shards in 0.6 × 0.9 m patches, origin at the patch centre on the floor. About 2/3 of the glass goes to the far side (audit §3.5). They are placed at `floor_pz` / `floor_nz` and rebuilt per window across chunk rebuilds (map, audit §4.4 item 1).
- **Teeth vs 00.** 00 says remnants stay outside the opening. The audit's teeth are pieces that stick into it. Proposal for the map chat: allow render-only teeth to reach at most 0.10 m into the opening at the jambs and head, and 0.04 m above the sill. The climb camera and the 0.3 m body stay near the opening's middle, so they never touch them. The bottom teeth snap off at the §3.6 plant anyway. If the map chat says no, the teeth are cut flush at the stop line and the break reads as tempered glass (audit §4.4 item 5).

### 3.6 Climb (audit §3.6)

- `sill_plant_*`: the camera's plant jolt and the bottom-teeth snap at 0.15 s.
- Bottom tooth pieces carry the `tooth` class with edge = bottom, so the map can drop exactly those 3–5 pieces.
- Floor-glass patches give the landing footsteps their surface (sound chat's NEW Glass value).

### 3.7 Asks to the map chat (shots)

1. Unscaled parents (01 F2): `Key · zone {id}` and a `Window {a}-{b}` root; `Door leaf` too, if the jolts are to carry the visual leaf (§3.3).
2. The frame and remnant models are not children of `Window pane`, because `Kill(window.pane)` (`MapWorld:1686`) would destroy them. Disable the pane renderer and keep its collider (01 §2.5).
3. If the locked type's keyhole is not at LockPoint, move `LockPoint` to the model's `keyhole_*` anchor.
4. Approve or refuse the 0.10 m tooth exception (§3.5).
5. Event points are at floor level today (01 F4). Shots need the hit point (`Hold(hit)`, audit §6.4) and the keyhole point.

### 3.8 New material slots needed (reported, not added; kitlib.py is not edited by this workflow)

| Proposed slot | Why | Fallback with existing slots |
|---|---|---|
| `Prop_KeyTagNo` | 10 × 10 atlas of stamped numbers "00"–"99" for fobs and door plates (§2.5) | Typed cards in the `Prop_Label` atlas (no per-zone numbers) |
| `Prop_PlasticGreen` | 4th fob colour | 9 identities with red, blue and white |
| `Prop_GlassShard` (opaque near-black, smoothness .95) and `Prop_GlassEdge` (near-opaque green) | Audit §4.2 shard and edge looks for fracture pieces, teeth and floor glass | `Prop_GlassCRT` (opaque, near-black, roughness .08) for faces; no green edge |

---

## 4. Out of scope here, pointers only

- **Window reflection material and ray tracing** (Red's 23:0x message). URP 6.3 lists ray-traced reflections as "No" and HDRP as "Yes" (https://docs.unity3d.com/6000.3/Documentation/Manual/render-pipelines-feature-comparison.html). The URP plan is the audit's cubemap and probe route (§4.3). The glass material is audit §4.2. Neither is decided here.
- **The locked-door type**: 05. **Period dimensions, keyways, tag and cabinet history**: 02. **RE8 door construction and the gap fix**: the door construction report (not in this folder at the time of writing).

---

## 5. Open items and UNVERIFIED

1. The bevel glint crossing the 1.05 bloom threshold (P5): ESTIMATE; capture it.
2. Brass before zone cubemaps: may read too dark; the metallic 0.85 fallback is an ESTIMATE.
3. Dress order vs player distance, for v2 dresser-hosted keys: UNVERIFIED.
4. FBX export of a per-vertex piece id (colour attribute or UV2) through `kitlib.export()`: UNVERIFIED; probe first.
5. Key turn direction and the "teeth up" convention: UNVERIFIED for every lock; 02.
6. Metal-rimmed paper tags in the 19th century (Dennison): from a search result, not a page read.
7. Telkee's 1965 date is for an Australian maker; US key cabinets in 1990 are 02 §9's to source.
8. The pixel thresholds assume 1080p and contrast; at 1440p or 4K every distance in §1.1 scales up by 1.33× or 2×. Under dim or failing lamps they shrink.

## 6. Sources read for this report (2026-10-02)

- Johnson's criteria: https://en.wikipedia.org/wiki/Johnson%27s_criteria
- Silent Hill 2 remake, producer on yellow paint, item placement and lighting (Automaton, 2024-06-06): https://automaton-media.com/en/news/silent-hill-2-remake-will-not-use-yellow-paint-and-the-like-producer-assures/
- Yellow paint debate (overview, arguments, the Kotaku summary): https://en.wikipedia.org/wiki/Yellow_paint_debate
- Jonathon Wilson, "Level design tricks of the trade", Game Developer, 2018-07-20: https://www.gamedeveloper.com/design/level-design-tricks-of-the-trade
- The Level Design Book, Lighting: https://book.leveldesignbook.com/process/lighting
- Naughty Dog, The Last of Us Part II accessibility features, 2020-06-09: https://naughtydog.com/blog/THE_LAST_OF_US_PART_II_ACCESSIBILITY_FEATURES_DETAILED
- Game Accessibility Guidelines, colour alone: https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-colour-alone/
- The Henry Ford, Tivoli Motel key, 1955–1980: https://www.thehenryford.org/collections/explore/artifact/365287
- Dymo Corporation: https://en.wikipedia.org/wiki/Dymo_Corporation
- Telkee key cabinets: https://architectureanddesign.com.au/suppliers/telkee-key-cabinets
- Unity 6.3 render pipeline feature comparison: https://docs.unity3d.com/6000.3/Documentation/Manual/render-pipelines-feature-comparison.html
- Figma `0tCbAiVUlrPId3RWd9LRif`: HR03 (2331:873), IR04 (2320:2141), screenshots read 2026-10-02.
- Project files: as cited inline. Texture means were computed from `Assets/Resources/Surfaces/Textures/*.png`.
