# 01 — Inventory: interactables and placeholder objects in code

2026-10-02, from the code. This covers every interactable or gameplay-visible object built from primitives or placeholders, what depends on its collider or name, how it moves, and the exact frame a model would attach to.

**Method.**
- Line numbers are from the real project, `Assets/Scripts/...`. File names are shortened: `MapWorld` = `FrontRoomsMap/FrontRoomsMapWorld.cs`, `Map` = `FrontRoomsMap/FrontRoomsMap.cs`, `Hunter` = `FrontRoomsMap/FrontRoomsMapHunter.cs`, `Game` = `FrontRooms3DGame.cs`, `Stream` = `FrontRoomsRoomStream.cs`, `Units` = `FrontRoomsMap/FrontRoomsModuleUnits.cs`, `SoundDirector` = `Audio/FrontRoomsSoundDirector.cs`, `DoorSound` = `Audio/FrontRoomsDoorSound.cs`.
- `diff -rq` of `Assets/Scripts` between the project and the private clone `proj_int` came back empty, so the clone has the same code.
- Nothing here was run in Unity. Statements about how things look are computed from code and material files and are marked UNVERIFIED where a capture is needed.
- `00_map_constraints.md` is binding. Where this inventory finds a number that reads differently, it says so and leaves the call to the map chat (§9 F8).

---

## 0. Summary table

| Object | Built at | Placeholder today | Gameplay collider | Who depends on it | Motion |
|---|---|---|---|---|---|
| Map door leaf | `MapWorld:921-949` | Unity cube, 0.05 × 2.08 × 0.98, `Door_Veneer` | the cube's BoxCollider | `doorByCollider` (Describe/Use/IsOpenDoorLeaf/IsArchitecture), the E ray, the Relay's sight ray and nav probes, tests | hinge `localRotation`, 95° both ways, 0.55 s (0.18 s broken) |
| Map door pivot | `MapWorld:927-930` | empty `Door hinge {a}-{b}` | none | sound (`SoundDirector:212` by name; `DoorSound` reads its rotation), `Door.hinge`, tests | rotates |
| Map door frame | `MapWorld:910-919` | 2 jambs and a head, boxes merged into the chunk shell, `Cove_Base` | none (render-only) | nothing | static |
| Map window pane | `MapWorld:950-962` | Unity cube, 1.4 × 1.65 × 0.03, code-built transparent Lit | the cube's BoxCollider | `windowByCollider` (Describe/Hold/IsArchitecture), the E ray, the Relay's sight ray and nav probes | none; `Kill(pane)` on break |
| Map window frame | `MapWorld:910-919` | 2 jambs and a head, as for doors; no sill trim | none | nothing | static |
| Zone key | `MapWorld:781-791` | Unity cube, 0.32 × 0.12 × 0.12, emissive yellow | none (removed) | `CollectKeys` by horizontal distance ≤ 0.9 m | spins 90°/s about world Y |
| Troffer lens ("panel") | `MapWorld:1092-1101` | Unity cube, 0.6 × 0.025 × 1.2 | none (removed) | the fixture flicker (`MapWorld:1178-1180`) | none |
| Stream double door (incl. terminal door) | `Stream:1209-1299` | 2 planar boxes 1.12 × 2.62 × 0.08, bar handles, kick plates | BoxColliders on leaves, handles **and** kick plates | proximity opener, `IsDoorPassable`, sound (by name, `SoundDirector:214`) | pivots ±88°, 0.9 s |

There is **no exit, goal or terminal object in the generated map**. A run ends only when the Relay catches the player (`Game:598`, `Game:1585-1592`). The only "terminal" door is the title stream's last shut door, which leads into the map (§6).

---

## 1. Map doors

### 1.1 Where they appear

- An edge is a Door only where a **Low** zone meets a **Standard** zone. Where either side is **Tall**, the edge is a Window (`Map:348-356`).
- A border edge becomes an opening only if it is the chunk border's required gate, or if a 0.15 roll (`borderOpening`) hits (`Map:337-346`, `FrontRoomsLevel0.asset:38`). Otherwise it is a wall.
- Every door therefore has a 2.4 m ceiling on one side and 2.9 m on the other. The wall above the door is built to 2.9 (`MapWorld:733-734`), so the Low side sees 0.3 m of wall above the head trim.
- A door's two sides can be different themes (Low Level 0 against Standard Office). The wall is then split into two half-thickness skins, each in its own paper (`MapWorld:871-879`).
- Room modules cannot place doors or windows. `ModuleEdge` is only Wall/Open/Arch (`FrontRoomsRoomModuleData.cs:7-11`). Where a module meets another height, the map's rule stands (`FrontRoomsRoomModuleStamp.cs:13-16`).

### 1.2 What is built (`MapWorld.BuildEdge`, 855-963)

Edge geometry, in metres along the 3 m edge from its start corner (`start`, chunk-local, y = 0 at floor):

- **Opening:** width `DoorWidth` 1.0, centred at `c = 1.5`, height `DoorHeight` 2.1 (`MapWorld:890-895`). Wall pieces stand at [0, 1.0] and [2.0, 3.0] full height, plus a header [1.0, 2.0] from 2.1 to the ceiling (`MapWorld:903-905`). These are solid: they go into the render mesh **and** the chunk collision mesh (`MapWorld:703-707`).
- **Frame (render-only):** two jambs and a head, added to the block mesh in the `trim` material, `FrontRoomsSurfaces.CoveBase` (`MapWorld:910-919, 1785`). They are not in the collision mesh, because `get()` is used, not `solid()`.
  - Jamb: 0.07 along the wall (`TrimFace`), 0.20 across (wall 0.16 plus `TrimProud` 0.02 each side), floor to 2.1. Centred at `c ± (0.5 + 0.035)`, so the jamb's inner face is exactly on the opening edge.
  - Head: 1.14 along, 0.20 across, 2.10–2.17.
  - No stop, no rebate, no threshold.
  - **Coplanar faces (UNVERIFIED in a capture):** the wall piece's end face (`MapWorld:903`, it ends at `c − 0.5`) and the jamb's inner face are both at `c − 0.5`, in two materials, as are the header's underside and the head trim's underside at y = 2.1. This is a likely z-fighting band on the reveal.
- **Pivot:** `new GameObject("Door hinge " + a + "-" + b)` (`MapWorld:927`). `GridCoord.ToString` is `"(x, y)"` (`Map:42`), so a real name is `Door hinge (3, 4)-(4, 4)`.
  - Parent: the chunk root. It is world-aligned and unscaled at the chunk origin; the map root has identity rotation in the game (`Game:541`).
  - `localPosition = start + along * (c − 0.5)`: the low-coordinate jamb, on the wall centre line, at floor level (`MapWorld:929`).
  - `localRotation = LookRotation(along, up)` (`MapWorld:930`), stored as `Door.closed`.
- **Leaf:** `GameObject.CreatePrimitive(Cube)`, named `"Door leaf"`, a child of the hinge (`MapWorld:931-936`).
  - `localPosition (0, 1.04, 0.50)`, `localScale (0.05, 2.08, 0.98)`.
  - So it spans hinge-local X ±0.025, Y 0–2.08, Z 0.01–0.99.
  - Material: `FrontRoomsSurfaces.DoorVeneer`, or a fallback Lit (.72, .66, .50) (`MapWorld:1786`).
  - The primitive's default renderer settings apply: it casts shadows.
- No handle, lock, hinge knuckles, kick plate, stop, threshold or panel detail exists.

### 1.3 Collider and everything that depends on it

The leaf's BoxCollider, the primitive's unit box under the 0.05 × 2.08 × 0.98 scale, is the only door collider.

| Consumer | How | Where |
|---|---|---|
| `doorByCollider[leaf] = door` | maps the collider to its `Door`. Removed on chunk drop. | `MapWorld:947, 640` |
| `Describe` | prompt text: "E · OPEN DOOR" / "E · SHUT DOOR" / "LOCKED · NEEDS THIS ZONE'S KEY"; null when broken | `MapWorld:1589-1597` |
| `Use` | open, shut, locked, unlock | `MapWorld:1607-1620` |
| Player E ray | `Physics.Raycast` from the camera, `Reach` 2.4, all layers, ignores triggers, first hit wins | `Game:949-951` (`Reach` at `Game:150`) |
| Test-scene walker E ray | the same | `FrontRoomsMapWalker.cs:114-116` |
| `IsArchitecture` | doors count as architecture for the Relay's furniture-blind probes | `MapWorld:548`, `Hunter:881-882` |
| `IsOpenDoorLeaf` | public; no caller found in `Assets/` | `MapWorld:555` |
| Relay sight | `RaycastNonAlloc`; the nearest non-rig hit blocks | `Hunter:937-951` |
| Relay nav probes | capsule casts and overlaps, r 0.3, 0.4–1.95 m | `Hunter:838-879` |
| Editor tests | call `world.Use(door.leaf)` and read `door.hinge.parent.rotation * door.closed` | `Editor/FrontRoomsMap/FrontRoomsMapInteractionTests.cs:240-287` |

Other consumers:
- The `Door` fields other code reads (`MapWorld:103-116`) are `hinge`, `closed`, `leaf`, `a`, `b`, `edge`, `position`, `open`, `broken`, `progress` and `swing`. `Door.position` is the **opening centre at floor level** (`MapWorld:922`), not at handle height.
- **Sound** finds the pivot by name. `SoundDirector` scans every transform in the scene each pass. Any transform whose name **starts with** `"Door hinge"` gets a `FrontRoomsDoorSound` in Manual mode, 95° (`SoundDirector:200-218, 225-231`). `DoorSound` reads `Quaternion.Angle(closed, transform.localRotation)` every LateUpdate (`DoorSound:38-75`): handle and unlatch when the leaf leaves closed, a swing loop by angular velocity, and a stop or latch strike at rest.
  - Consequence: **no child of a door model may have a name starting with "Door hinge"**, or it gets its own door sound. The same scan also takes any transform named exactly `"Light"` or starting with `"fluorescent light"` as a lamp, and `"double door left hinge"` / `"double door right hinge"` as automatic doors (`SoundDirector:212-217`).
  - `FrontRoomsKitLibrary.Spawn` renames the instance to its `label` argument, or else the asset name (`Office/FrontRoomsKitLibrary.cs:195-201`), so pass a safe label.

### 1.4 How it moves

- **Open or shut:** `SetDoor` flags the door and queues it (`MapWorld:1667-1673`). `TickDoors` moves `progress` 0 to 1 linearly over 0.55 s, or 0.18 s if broken. The angle is smoothstepped: `hinge.localRotation = closed * Euler(0, −95 · swing · e, 0)` (`MapWorld:1718-1727`). Only the hinge rotates. The leaf transform never moves relative to the hinge.
- **Swing direction:** `SwingAway` picks the side away from the opener and remembers it per edge in `doorSwing`. It survives rebuilds (`MapWorld:1655-1665, 207, 938`). It only re-picks when the leaf is fully shut (`progress == 0`). Doors therefore swing **both ways**.
- **Rebuilt open:** a door whose edge is in `openDoors` or `brokenDoors` is built already at 95° (`MapWorld:939-945`).
  - Side effect: `DoorSound.Start` records the current rotation as "closed" (`DoorSound:38-43`), so a door rebuilt open reads its open pose as closed. That is the sound chat's issue, noted only because it touches the hinge.
- **Relay break:**
  - It walks to 0.45 m in front of the crossing point (`Hunter:513-533`).
  - Blows every 0.5 s (`Hunter:884-905`).
  - Then `BreakDoor` swings the leaf away from the Relay in 0.18 s and marks it broken and open for good (`MapWorld:1056-1065`).
  - A broken door can never be shut again (`MapWorld:1609`).
  - No damage state, splinters or leaf detachment exist.
- **Passage for the AI:** a door counts as Open when it is in `openDoors` or `brokenDoors`, or when it is opening past `progress` 0.6 (`MapWorld:1041-1044`).
- **Key delay:** `UnlockSwingDelay` holds the leaf after `DoorUnlocked` (`MapWorld:79-80, 1629-1637, 1708-1717`). Nothing in the game sets it (default 0), and nothing subscribes to `DoorUnlocked` outside the map's tests (grep of `Assets/`).

### 1.5 Locks: what the code actually does

- `doorsNeedKeys` is **false** in the code default and in the shipped profile (`FrontRoomsLevelProfile.cs:31`, `Levels/FrontRoomsLevel0.asset:47`). Today no door is ever locked, and keys do nothing but count.
- When it is on, `LockedHere(door)` = keys on, AND this edge not yet in `unlockedDoors`, AND the player holds no key for **the zone the player stands in** (`MapWorld:1698-1701`).
  - So **no door is intrinsically locked or free.** Every shut door is locked to a player without the current zone's key, and free to one with it.
  - The same door can be locked from one side and free from the other.
  - Once a key opens a door, the edge stays unlocked for the run (`MapWorld:1631`).
- **Consequence for Red's "locked doors must look different" (a):** there is no per-door locked flag to drive a different model. The map chat would have to add one (for example an edge-hash subset, or "doors on the key zone's border"), store it in `Door`, and make `LockedHere` read it. Until then a "locked door type" has nothing to bind to.
- `DoorUnlocked(door, zone, LockPoint(door, from))` reports the **player's** zone, not a zone of the door (`MapWorld:1632-1633`).
- `LockPoint` (`MapWorld:1640-1648`) = opening centre + along · (0.5 − `DoorHandleInset` 0.08) + up · `DoorHandleHeight` 1.0 + across · side · (0.025 + `DoorHandleProud` 0.03). Side is the opener's side of `closed * right`. It uses the **closed** rotation, so it is the lock's rest position, not where the moving leaf is.

### 1.6 Attach frame for a door model (hinge-local)

Model this frame, and mount the model as a **child of the hinge** next to `Door leaf`. Do not make it a child of the leaf: the leaf carries a non-uniform 0.05 / 2.08 / 0.98 scale that any child would inherit.

| Hinge-local axis | Meaning |
|---|---|
| origin | hinge jamb edge of the opening, on the wall centre line, at floor level (y = 0) |
| +Z | across the opening, from the hinge jamb (Z 0) to the latch jamb (Z 1.0). The leaf spans 0.01–0.99 |
| +Y | up. Opening to 2.10, leaf to 2.08; head trim 2.10–2.17 |
| ±X | the wall normal. The wall's faces are at X ±0.08, the trim faces at ±0.10. **Which room +X faces depends on the edge's direction (table below)**, so a model must be the same on both faces, or the map must tell it which face is which |

| Edge | `along` (chunk-local) | Hinge at (chunk-local, cell (i, j) = a) | Hinge +Z | Hinge +X | swing +1 sends the leaf into |
|---|---|---|---|---|---|
| East edge, a = (x, y), b = (x+1, y) | +Z | ((i+1)·3, 0, j·3 + 1.0) | north (+Z) | east (+X), toward **b** | a (west) |
| North edge, a = (x, y), b = (x, y+1) | +X | (i·3 + 1.0, 0, (j+1)·3) | east (+X) | south (−Z), toward **a** | b (north) |

(Local +X for the north edge follows from Unity's `LookRotation(+X, up)`: right = up × forward = −Z.)

- **Swing rule in hinge terms:** `swing` = the sign of the opener's hinge-local X. The leaf turns by −95° · swing about +Y, so it travels toward −swing · X, away from the opener. This holds for both edge directions (`MapWorld:1655-1665` with the table above).
- **Latch side:** always hinge-local +Z (Z = 1.0). The hinge side is Z = 0.
- **Lock / handle anchor (closed pose):** hinge-local **(±0.055, 1.00, 0.92)**. The sign is the opener's side. This is exactly `LockPoint` minus the hinge. The key's insertion axis is hinge-local ∓X, into the leaf face.
- **Blender to Unity:** the kit exports Blender (x, y, z) as Unity (−x, z, −y) (`Tools/Blender/frontrooms_kit/kitlib.py:789-794`). So in Blender:
  - the leaf runs from the origin along **−Y** to −1.0, with height on +Z;
  - the lock anchor is (∓0.055, −0.92, 1.00);
  - the hinge's +X is Blender −X.
- **Slits when shut** (matches 00): 1 cm at each jamb, 2 cm at the head, none at the floor. The reveal is the bare wall-end faces (wallpaper).
- **Open-pose geometry (computed, 95°):**
  - The leaf's latch end sits at hinge-local about (∓0.99, —, −0.086 to −0.111). It is 5° past square, about 0.09 m behind the hinge line, and about 0.83 m from the nearest wall face (the pier face at X = ∓0.08).
  - The only solid or visible thing the open leaf meets is at the **hinge end**. For the first ~0.10 m from the pivot, the leaf's pier-side face lies inside the jamb trim and the end of the wall pier, up to 0.034 m deep (face at Z −0.026 to −0.034 while the trim reaches Z −0.07 and the wall pier is solid for Z < 0, |X| ≤ 0.08).
  - So the clip that matters for hardware is near the hinge edge: knuckles, pivots or a hinge-side stile proud of the face. At the latch end, a lever or cylinder proud of the face has nothing to hit when open.
  - 00 says "at 95° the leaf's latch end stands about 0.09 m off the wall face". The 0.09 m matches how far the latch end passes the hinge line (0.99 · cos 95° = 0.086), not a distance to a wall face. The ≤ 0.07 m-per-side rule is safe, but it is conservative everywhere except within ~0.1 m of the hinge. **Flag for the map chat to confirm (§9 F8).**
- **What the pivot geometry corresponds to:** the pivot sits on the leaf's centre plane, exactly at the opening edge, and the leaf swings both ways. That is the geometry of a **centre-hung, double-acting pivot door** (top and floor pivot), not of butt hinges. Butt-hinge knuckles at the edge would sit inside the wall end when shut. This bears on the hinge "read" for the RE8 brief. Period plausibility is for `02_period_hardware.md` to source; it is UNVERIFIED here.

### 1.7 Leaf material and UVs (computed; UNVERIFIED in a capture)

- `Door_Veneer` uses `FrontRooms/Surface` with `_FR_MESH_UV` on, `_TileSize` 1.12 × 2.62 (`Resources/Surfaces/Door_Veneer.mat:14-15, 58, 69`). The shader then reads **mesh UVs in metres** (`Resources/Rendering/FrontRoomsSurface.shader:21, 176-183`).
  - The stream leaves are planar boxes with metre UVs (`FrontRoomsFilmMesh.cs:24-60`), so their veneer maps 1:1.
  - The map leaf is a Unity cube with 0–1 UVs per face. Its 0.98 × 2.08 m face shows 1 × 1 "metres" of texture, so **the veneer is stretched about 2.08× vertically**. The 0.05 m edges show a full 1 m of texture squeezed.
  - A kit leaf with metre UVs (kitlib's convention) fixes this.
- The shader's macro wear is always world-planar (`FrontRoomsSurface.shader:191-197`), so on a swinging leaf it slides slightly (8 m and 12.8 m periods).

---

## 2. Map windows

### 2.1 Where they appear

Any edge where a **Tall** zone (5.4 m) meets Low or Standard (`Map:354`), with the same gate and 0.15 roll as doors. Tall zones have no key (`Map:636`), so a Tall zone is "left through windows" (`Editor/FrontRoomsMap/FrontRoomsMapDebugWindow.cs:256`).

### 2.2 What is built (`MapWorld:896-962`)

- **Opening:** 1.4 wide centred at c = 1.5, sill 0.35, head 2.0.
  - Wall pieces: left and right full height, the header above 2.0, and a **solid sill block 0–0.35** (`MapWorld:903-906`). The sill's top face is bare wall material: no stool, no sill trim.
- **Frame (render-only, shell mesh, `Cove_Base`):** jambs 0.07 × 0.20, from 0.35 to 2.0, inner faces on the opening edges; head 1.54 × 0.20, 2.00–2.07 (`MapWorld:910-919`). There is no glazing stop and no bottom member. The same coplanar-reveal risk applies as for doors.
- **Pane:** `CreatePrimitive(Cube)` named `"Window pane " + a + "-" + b`, for example `Window pane (3, 4)-(3, 5)` (`MapWorld:953-958`).
  - A child of the chunk root, **with no rotation**.
  - `localPosition = start + along·1.5 + up·1.175`: the wall centre line, mid-opening.
  - `localScale = Abs(along·1.4 + across·0.03 + up·1.65)`. That is (0.03, 1.65, 1.4) on east edges and (1.4, 1.65, 0.03) on north edges, so **the scale and the long axis change with edge direction**.
  - Material: `TransparentGlass("Map test / glass", (.75, .85, .88, .28))`, built in code: URP Lit, transparent, premultiplied, ZWrite off, smoothness .9 (`MapWorld:1788, 1791-1807`). The renderer keeps the primitive's shadow casting (On).
- `Window` class: `pane`, `edge`, `position`, `hold` (`MapWorld:118-124`). **`Window.position` is the opening centre at floor level** (`MapWorld:922, 959`). The pane's centre is 1.175 m above it. `GlassHold`, `GlassBroken` and the sound events all use the floor point (`SoundDirector:443-462`).

### 2.3 Collider and dependents

- The cube's BoxCollider, 1.4 × 1.65 × 0.03 on the wall line.
- `windowByCollider[pane collider] = window` (`MapWorld:961`), used by:
  - `Describe` → "HOLD E · BREAK GLASS", `holdToUse` (`MapWorld:1599-1603`);
  - `Hold` (`MapWorld:1676-1689`) and `ReleaseHold` (`1691-1696`);
  - `IsArchitecture` (`548`).
- The E ray (`Game:949-978`; walker `FrontRoomsMapWalker.cs:107-140`) hits it first.
- It blocks the Relay's sight (`Hunter:937-951`) and nav probes. `PassageBetween` returns Glass until it breaks (`MapWorld:1045-1046`), and the Relay plans around Glass (`Hunter:461-462`).

### 2.4 How it changes

- **Hold:** `window.hold += dt`; `progress = hold / 1.0`. `GlassHold(position, progress)` fires every frame (`MapWorld:1680-1682`). Release resets `hold` to 0 (`MapWorld:1695`): cracks "heal" today.
- **Sound beats:** crack one-shots at progress 0.35 and 0.70 are literals in the sound layer (`SoundDirector:452-453`).
- **No visual change at all during the hold.**
- **Break at 1.0 s:**
  - `brokenWindows.Add(edge)` and `windowByCollider.Remove`.
  - **`Kill(window.pane)` destroys the whole GameObject, including any children**, then `GlassBroken(position)` fires (`MapWorld:1683-1688`).
- **Rebuild:** a broken window's pane is simply not built (`MapWorld:952`). Nothing marks the opening afterwards: no remnants, no floor glass.
- `WindowShattered` does not exist yet (grep: no match in `Assets/`).
- **Climb (main game only):** walking into a broken window's frame from ≤ 0.95 m in front, ≤ 0.45 m lateral, moving toward it, starts a 0.6 s scripted climb.
  - Lift 0.35, duck 0.55, landing 0.75 m past the wall line (`Game:897-940`, constants `Game:155`).
  - The CharacterController is disabled during the climb (`Game:932-934`), so remnant meshes cannot block it physically, but they must not occupy the opening visually. 00 already requires them to stay outside the opening.
  - The **test-scene walker has no climb** and a 0.3 step offset, so it cannot get over the 0.35 sill (`FrontRoomsMapWalker.cs:42`).

### 2.5 Attach frame for a window model (proposal: the map has no unscaled window frame today)

- A model **cannot** be a child of `Window pane …`, for two reasons: it inherits the non-uniform scale, and it is destroyed with the pane on break.
- The map needs an unscaled window root. A proposal for the map chat:
  - a sibling `Window {a}-{b}` at the opening centre, on the wall line, at floor level (= `Window.position`);
  - `localRotation = LookRotation(across, up)`, so local +Z points into cell b and local ±X runs along the wall.
- In that frame:
  - the clear opening is X ±0.70, Y 0.35–2.00, at Z 0;
  - the gameplay pane is the box X ±0.70, Y 0.35–2.00, Z ±0.015;
  - the jambs' inner faces are at X ±0.70 and the head at Y 2.00;
  - the wall faces are at Z ±0.08, the trim faces at Z ±0.10.
- The frame, glazing and post-break remnants must stay outside X ±0.70 × Y 0.35–2.00 (00).
- Kit axes: the kit's front (Blender −Y) becomes local +Z, facing b.
- As with doors, local +X runs along +along on north edges and −along on east edges (`LookRotation` right = up × forward). Keep the window symmetric, or let the shatter code pass a side.
- The pane renderer can then be disabled, with its collider kept. Disable it rather than destroy it, since `windowByCollider` keys on that collider.

---

## 3. Zone keys

### 3.1 How many and where

- **One key per zone, and none in Tall zones** (`Map:632-652`). The validator fails a Low or Standard zone without one, and a Tall zone with one (`FrontRoomsMapValidator.cs:196-201`).
- Every chunk owns exactly one zone site (`Map:129-139, 280-299`), so there is **at most one key per chunk**. About 90 % of chunks qualify (Low .35 + Standard .55, `FrontRoomsLevel0.asset:17-19`).
- **`keyCell`** = the cell of that zone whose centre is nearest the zone's site (`Map:632-652`). The site lies 0.15–0.85 of the way across its chunk (`Map:285-287`), so in practice the key is in or beside the cell holding the site. That can be a corridor, a room's middle, or a module room.
- **Placement** (`MapWorld:781-791`):
  - built with the chunk that owns the zone, parented to that chunk's root;
  - `localPosition = keyCell centre at y 1.05` (chunk-local, floor 0);
  - skipped if the player already holds that zone's key, or if the cell is in the start area.
- Nothing reserves the key's cell when rooms are dressed:
  - `KeepClear` covers only openings (`MapWorld:1565-1585`);
  - the pile centre is the room or bay centre (`MapWorld:1537-1556`);
  - module props ignore keys.
  - So a key can float inside a desk, a cubicle run or a furniture pile. **UNVERIFIED in a capture**, but nothing in code prevents it. A host convention (00, "Keys") would have to choose hosts that avoid this.

### 3.2 What is built

- `CreatePrimitive(Cube)` named `"Key · zone " + ownZone.id`, for example `Key · zone (2, -1)`. Its **collider is destroyed** (`MapWorld:783-785`).
- `localScale (0.32, 0.12, 0.12)`: the long axis is local X, horizontal.
- Material `keyGlow` = Lit "Map test / key", (.96, .87, .23), smoothness .4, emission × 0.8 (`MapWorld:1787`). It casts shadows (primitive default).

### 3.3 How it behaves

- `CollectKeys` runs every Update (`MapWorld:571, 1730-1746`):
  - it rotates the key **90°/s about world Y** (`Space.World`);
  - the key is taken when the **horizontal** distance from the player root (feet) to the key's transform position is ≤ 0.9 m, at any height;
  - it then adds the zone to `keysHeld`, destroys the key and raises `KeyTaken(zone)`.
- No E press, no aim, no prompt (§3.1 of the audit wants E · TAKE KEY, which would need a collider back; 00 says none for now).
- Subscribers to `KeyTaken`:
  - the game's flash "KEY / OPENS THIS ZONE'S DOORS" and counter (`Game:584, 800-805`);
  - the sound one-shot `KeyPickup` (`SoundDirector:474`).
- The HUD key panel uses a 40 × 22 px glyph `Resources/UI/HUD_KeyGlyph.png` (a ring bow on the left and a toothed blade to the right) and the label "LEVEL 0 KEY" (`Game:1408-1415`). A 3-D key should read as the same object.
- The test scene collects keys the same way, with the walker as `player`.

### 3.4 Attach frame for a key model

- The pickup point is **the key transform's position**. A model must keep the key's logical origin where the map puts it. The model's own origin should be the key's natural point, the bow or grip centre, with an anchor for the tip and the insertion axis (the audit's §3.2 shot).
- `Key · zone {id}` carries the scaled cube, so a model **cannot** be its child. Proposal for the map chat: build the key as an unscaled empty with that name, with the model (or the cube) as a child.
- Spinning is a `transform.Rotate` on that object. A hosted key that stops spinning needs `CollectKeys` to skip the rotate for hosted keys (map change). The visual chat recommends this in 00.

---

## 4. Other map placeholders

- **Troffer lens** (the "panel" at `MapWorld:1092`):
  - a cube, `"Lens"`, 0.6 × 0.025 × 1.2, collider removed, `theme.lens`, shadows off;
  - under `"Fixture (x, y)"`, beside a spot light named **`"Light"`** (`MapWorld:1088-1110`). The sound director picks up that name as a lamp.
  - Not interactable. Listed because the task named it. A kit troffer would have to keep the `Light` child's name, and keep `fixture.panel`, which is used for emission flicker through a MaterialPropertyBlock (`MapWorld:1178-1180`).
- **Arches (doorless doorways):**
  - 1.1–1.8 m wide, off-centre, top 2.2 m or 0.2 m under the ceiling (`MapWorld:885-889, 993-999`). They have no trim at all (`MapWorld:908`).
  - `Kit_DoorwayStuds` / `140` / `180` exist as dressing for them but are not wired (`Tools/Blender/frontrooms_kit/assets/doorway_studs.py:1-30`).
  - Not interactable.
- **Columns / cove / bulkheads:** shell boxes, not interactable (`MapWorld:973-986`).

---

## 5. The Relay, ray and probe rules that bind every model (summary)

- **E ray:** the camera ray, 2.4 m, `~0` layers, ignores triggers, **first collider wins** (`Game:949`, walker `:114`). A non-trigger collider on any hardware in front of the leaf or pane would steal the ray and make the door or window unusable.
- **Relay sight:** `RaycastNonAlloc` over all layers; the nearest hit that is not the player or the rig blocks (`Hunter:937-951`).
- **Relay body:** capsule r 0.3, 0.4–1.95 m (`Hunter:35, 838-879`). With `furniture = false` only architecture counts (`Hunter:881-882`). Any new collider in a door or window opening would block the Relay or make it plan wrongly.
- So everything a model adds is **render-only**: kit `no_collider()`, or `FrontRoomsKitLibrary.Spawn(..., colliders: false, label)` (`FrontRoomsKitLibrary.cs:190-206`).

---

## 6. Title stream doors (`FrontRoomsRoomStream.cs`)

- **Build** (`Stream:1209-1299`): every stream room ends in a 2.4 m opening in a thin end wall (`DoorWallDepth` 0.04).
  - The wall returns and the header (0.24) are boxes with colliders.
  - Paper "reveal" quads on both sides hide the returns' inner faces (`Stream:1230-1243`).
- **Leaves:** two leaves, `"double door left"` and `"double door right"`, each a planar box 1.12 × 2.62 × 0.08 with metre UVs, in `doorMaterial` = `FrontRoomsSurfaces.DoorVeneer` (`Game:359, 379`).
  - They hang from `"double door left hinge"` / `"double door right hinge"` at x = ∓1.12 on the door plane (`Stream:1247-1253`).
  - Gaps: 8 cm between each pivot and its return (opening half-width 1.20), none at the meeting stiles, 4 cm at the head (leaf top 2.62, header underside 2.66), none at the floor (`Stream:19-33`).
- **Hardware (the language to match):**
  - **bar handles** 0.055 × 0.18 × 0.045 at pivot-local (±1.02, 1.22, ±0.0725), on both faces, i.e. 0.10 m in from the meeting stile, centred at 1.22 m;
  - **kick plates** 1.07 × 0.25 × 0.004 centred at y 0.14, on both faces;
  - all in "Door / brushed steel" Lit (.64, .63, .60), smoothness .62, metallic .9 (`Stream:1255-1270, 1403`).
  - All are made with `Box()`, which **adds a BoxCollider to every piece, handles and kick plates included** (`Stream:1782-1799`). That breaks the map's render-only rule. It is harmless here only because stream doors are not E-used and `Describe` returns null for them.
- **Motion** (`Stream:722-784, 1765-1780`):
  - proximity-opened (camera within 4 m), 0.9 s, smoothstep, to **88°**;
  - both leaves turn by `doorSwing`: +1 opens away from the camera, −1 when an ended stream's door is approached from its far side (`Stream:741`);
  - the sound director attaches Automatic-mode door sound to the two pivots by name (`SoundDirector:214-215`).
  - The Relay's stream break poses the leaves open instantly (`Stream:998-1012`).
- **Terminal door** (the only door into the map):
  - At Space, the game ends the stream at the first shut door (`Stream:483-489, 503-538`; `Game:517-551`).
  - That door stays held while the map builds: opened when `ReadyAround`, or after a 3 s limit (`Game:733-746`).
  - It shuts for good once the player is 4 m into the map (`Game:118, 749-753`; `Stream:575-585`).
  - It is a 2.4 m double door: it is not the map door type and is not keyed.

---

## 7. Level Designer modules

- Modules hold edges (Wall/Open/Arch), columns, props, lamps and fill (`FrontRoomsRoomModuleData.cs:7-84`). They hold **no doors, windows or keys**.
- Props are kit assets spawned through `FrontRoomsKitLibrary.Spawn`, with colliders unless `noCollider` (`MapWorld:1433`).
- The preview (`FrontRoomsModulePreview.cs:180-218`):
  - builds a real map in which **every zone has the module's height and theme**, so it contains **no door or window edges at all**;
  - still places keys in Low and Standard zones;
  - builds in edit mode through `BuildForCapture`, where `Update` (and so `CollectKeys` and the door tick) does not run.
- Models therefore need to work in edit mode (no reliance on `Start`), but door and window models will not show up in the Designer until the map chat adds a door/window preview.

---

## 8. Other primitives (not interactables, for completeness)

- `FrontRoomsRelayRig.cs:292-300`: the Relay's primitive body parts.
- `Office/FrontRoomsOfficeKit.cs:711-724`: office column boxes (drywall plus a cove without a collider).
- `FrontRoomsOfficeFurniture.cs:424-439`: a cylinder helper; the class has no callers in `Assets/`.
- `FrontRoomsMaze/FrontRoomsMazePreview.cs:112`: an old editor preview.
- `Stream:1845-1856`: a cylinder helper.
- Editor test boxes: `Editor/FrontRoomsMap/FrontRoomsRelayNavTest.cs:101, 144` and `Editor/Rendering/FrontRoomsKitLookdev.cs:269`.

---

## 9. Findings for the kit spec and the map chat

- **F1. No intrinsic locked or free door.** Locking depends on the player's zone and held keys, and keys are off in the shipped profile (§1.5). Red's "locked doors look different from far away" needs a per-door `locked` flag from the map chat before any locked-door model can be bound.
- **F2. Three of the four map objects carry non-uniform scale on the very object whose name and collider must survive:** the leaf (0.05 / 2.08 / 0.98), the pane (axis-swapped per edge) and the key (0.32 / 0.12 / 0.12).
  - Door models can go under the existing unscaled hinge.
  - Windows and keys need a map change: an unscaled root, then disabling the primitive's renderer but keeping its collider (§2.5, §3.4).
- **F3. Window break destroys the pane object, and rebuild skips it.**
  - Remnants, teeth and floor glass cannot live under the pane.
  - The map must swap or keep a separate window root, and rebuild remnants for edges in `brokenWindows` (`MapWorld:952, 1686`).
  - Release resets the hold, so there are no persistent crack stages yet (`MapWorld:1695`).
- **F4. Event points are at floor level.** `Door.position`, `Window.position`, `DoorMoved`, `GlassHold` and `GlassBroken` all report the opening centre at y = 0 (`MapWorld:922`). Only `LockPoint` and `DoorUnlocked` give a handle-height point. Shots and VFX must add the height (pane centre +1.175), or the map must add a hit point (the audit's `Hold(hit)`).
- **F5. The map leaf's veneer is stretched** about 2.08× vertically by 0–1 cube UVs on a metre-UV material (§1.7). A kit leaf fixes it.
- **F6. Name hazards for model children:**
  - any name starting `Door hinge`;
  - exactly `Light`;
  - starting `fluorescent light`;
  - `double door left hinge` / `double door right hinge` (sound auto-attach, `SoundDirector:212-217`).
  - `KitLibrary.Spawn` names the instance after `label` or the asset.
- **F7. Likely z-fighting on reveals** where the wall end face and the trim's inner face, and the header soffit and the head trim's underside, are coplanar (`MapWorld:903-919`). UNVERIFIED; check in a capture. A kit frame that wraps the reveal would hide it.
- **F8. Open-leaf clearance.** Computed at 95°: the hinge end is the only clip zone. The pier-side face is up to 0.034 m inside the jamb trim and wall end for the first ~0.10 m. The latch end is about 0.83 m clear of any wall face; it passes the hinge line by about 0.09 m.
  - 00's wording "0.09 m off the wall face" seems to describe that pass-by.
  - Map chat: please confirm whether the ≤ 0.07 m proud limit was meant for the hinge end or for the whole leaf.
- **F9. The pivot is a centre-hung, double-acting pivot** (on the leaf's centre plane, at the opening edge, swinging both ways). Butt-hinge knuckles would intersect the wall end when shut. The hinge hardware read must fit this pivot, or Option A in 00 (single swing with a stop) has to be taken.
- **F10. Keys can sit inside furniture**, since nothing keeps `keyCell` clear (§3.1). They spin about world Y, and a host convention needs `CollectKeys` to skip the spin for hosted keys.
- **F11. Stream door hardware has colliders** on handles and kick plates (`Stream:1782-1799`). If its language is reused in the map kit, those pieces must be render-only there.
- **F12. Nothing listens to `DoorUnlocked`, and `UnlockSwingDelay` is never set.** The key shot (head dip, key turning) has its map hooks (`LockPoint`, the delay) but no consumer yet.
