# 00 — Gameplay constraints from the map chat (binding)

Source: the map chat (关卡设计), 2026-10-02. It owns `FrontRoomsMapWorld.cs`, `FrontRooms3DGame.cs` and `FrontRoomsMapHunter.cs`. Every model in the interactables kit must obey these rules.

## The rule underneath everything: every collider counts

- The Relay's sight ray (`FrontRoomsMapHunter.Visible`) and the player's E aim ray (`FrontRooms3DGame`, `Physics.Raycast` on all layers, non-trigger) both stop at the **first collider** they hit.
- The Relay's nav probe (radius 0.3, 0.4–1.95 m) treats colliders as obstacles.
- **Therefore hardware, hinges, frames, glazing bars, glass remnants and key hosts are render-only, with no colliders.** Build them with `kit.no_collider()`.
  - A handle collider in front of the leaf would steal the E ray, and the door could no longer be used.
  - A frame or shard collider in a window opening would block the climb and the Relay.

## Doors

- **Opening:** 1.0 × 2.1, centred on the edge. Nothing collides inside it.
- **Map trim:** the map's jambs and head trim are render-only today, with a 0.07 face. The jamb is 0.20 deep: wall 0.16, plus 0.02 proud on each side.
- **Pivot:** the transform `Door hinge {a}-{b}` is the pivot (声音 finds it by name). It sits on the low-coordinate jamb, on the wall centre line, with the leaf along its local **+Z**. It swings 95° about Y, away from the opener, in 0.55 s (0.18 s when broken).
  - **A leaf model must be a child of that hinge.**
- **Leaf collider (keep exactly):** BoxCollider 0.05 × 2.08 × 0.98 (DoorLeafThickness × (2.1 − 0.02) × (1.0 − 0.02)), centred 0.49 along the hinge's +Z. `doorByCollider` maps it (Use, the Relay's door breaking, `IsOpenDoorLeaf`). A model may replace only the **renderer**.
- **Visible leaf ≤ 0.05 m thick.** Near the hinge, the open leaf passes inside the jamb with no rebate.
- **Hardware depth:** at 95° the leaf's latch end stands about 0.09 m off the wall face. **Everything proud of the leaf face must stay within about 0.07 m per side**, or it clips the wall when the door is open.
- **Lockset:** placed exactly at `ModuleUnits.DoorHandleHeight` 1.0, `DoorHandleInset` 0.08 (from the latch edge), `DoorHandleProud` 0.03. `MapWorld.LockPoint(door, from)` and `DoorUnlocked`'s point both use the handle/lock spot on the opener's face.

## Windows

- **Opening:** 1.4 wide, sill 0.35, head 2.0.
- **Sill:** the wall below 0.35 is collision. The Relay's probe starts at 0.4, and the climb lifts 0.35 over the sill.
- **Pane collider (keep exactly):** a box 1.4 × 1.65 × 0.03 (GlassThickness), centred on the wall line. It blocks the Relay and its sight until it breaks. `windowByCollider` maps it, and `Hold` breaks it.
- **Glazing and frame are render-only.** Once the pane is gone, they must stay **outside the 1.4 × (0.35–2.0) opening**.
- **Remnants after the break are render-only too,** and the opening must stay clear for the climb. The player enters the frame from ≤ 0.95 m; the climb lasts 0.6 s with a 0.55 m duck.

## Keys

- **Collider:** none.
- **Pickup:** by **horizontal distance ≤ 0.9 m** from the key transform's position, at any height.
- **Placement today:** the cell centre at 1.05 m, **spinning 90°/s about world Y** (`CollectKeys`).
- **Hosts (hooks or surfaces):** the map chat would place the key at a host spot instead of the cell centre. The kit must define:
  1. the **host anchor convention** (where the key's origin goes on each host);
  2. whether a hosted key stops spinning. The visual chat's recommendation is yes: a still key on a hook or surface.
  - Reach: a wall hook at height h puts the key about 0.4 m from where the player can reach it, so the 0.9 m horizontal pickup must still work from the walkable floor in front.

## Names that must survive (the map keeps them on its collider and pivot objects; models go in as children)

- `Door hinge*` (pivot)
- `Door leaf`
- `Window pane {a}-{b}`
- `Key · zone {id}`

## Performance

These spawn per door, window and key in every streamed chunk. Keep them cheap:

- one renderer, or a shared material set, each;
- **no lights**;
- an LOD1 if they're detailed.

## Door slits: exact numbers (map chat, from FrontRoomsMapWorld.BuildEdge, 2026-10-02 23:1x)

- **Side slits:** the leaf cube is 0.98 wide, centred 0.50 along the hinge's +Z, so it spans 0.01–0.99. That leaves a **1 cm slit at the hinge jamb and 1 cm at the latch jamb.**
- **Head slit:** vertically the leaf spans 0–2.08 in a 2.10 opening, so there is **a 2 cm slit at the head.** There is none at the floor: no threshold, and the leaf bottom sits at floor level.
- **Bare reveal:** the jamb and head trims sit *outside* the opening. Their inner faces are at c ± 0.50 and at 2.10, and they are render-only boxes 0.07 face × 0.20 deep. So the reveal is the bare wall-end faces: no stop, no rebate, no threshold, nothing overlapping the leaf.
- **Hinge:** on the low jamb's wall centre line, exactly at the opening edge (c − 0.50).
- **Nothing shifts on rebuild:** the hinge spot is a pure function of the edge, and the swing side is remembered per edge.
- **Aggravating factors:**
  - (a) Two lamps in three cast **no shadows** (budget), so a lit room behind a door throws light through walls and especially through the slits.
  - (b) The head slit sits at eye-line when standing close to a door and looking up.
- **Option B** (a visual leaf and stops that overlap the frame) **needs nothing from the map chat.**
- **Option A** (RE8-style single swing with stops), the map side's cost:
  1. A fixed swing side per door (an edge hash).
  2. Pulls: the leaf sweeps 1.0 m on the pull side, and the keep-clear strip is already 1.2 m. The player in that sweep is handled by a short takeover that steps them back about 0.5 m, or a partial open. Plus a pull event for the visual and sound chats.
  3. The Relay breaks toward the swing side: it bursts into the far room from the stop side and rips toward itself from the pull side. Nav is unaffected.
  4. Tests and docs need updates.
  - Size: about an evening plus the takeover.

## Locked vs free doors: how the map decides (map chat, 2026-10-02 23:1x)

- **Today it's all or nothing.**
  - `doorsNeedKeys` (read once at run start) locks **every** door, and each door needs the key of the zone the player is standing in, so a door needs zone A's key from A's side and B's from B's side.
  - The default is off, so **no** doors are locked.
- **Status only changes one way.** It goes locked → unlocked (by key), and once unlocked a door stays unlocked from both sides. Doors never move; they sit on Low↔Standard borders.
- **The map picks the model at build time** from (lock rule, unlockedDoors). An unlocked locked-door **keeps the locked model**. No hot-swapping on the hinge is needed.
- **Proposed per-door rule (pending Red):** a generation field `lockedDoorShare` (≈ 0.35). A door edge is locked if its hash is under the share; this is deterministic per seed and stable across rebuilds.
  - The key rule stays "the key of the zone you stand in", and every Low/Standard zone has its key reachable inside it, so the maze is always solvable.
  - Tall halls have no key and are never next to a door.
  - Alternatives: lock only the doors that lead deeper, or only doors into Office zones.
- **What the kit must provide:** both variants (free and locked) as separate assets on the same gap-free frame. The map chooses per door.
- **Crack stages:** `GlassHold(Vector3, float progress 0–1)` already fires every frame E is held, so crack stages can follow the hold today. `GlassCracked` / `WindowShattered(window, hitPoint, impulse)` come with the contract; `GlassBroken` keeps firing.
