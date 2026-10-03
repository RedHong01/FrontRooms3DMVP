# 11 — Squeezed giant: Red's direction for the Hunter (2026-10-02)

> Red: "我希望怪物能够像是巨大的身躯挤在小小的这个空间里" — the monster should read as a **huge body crammed into this small space**.

This supersedes pillar 1 of `10_hunter_directions.md` ("built to the door, not to a scale"). The four directions (A Floor Sample, B Night Shift, C Duplicate, D Delivery) keep their anchor, costume, head treatment and tell. What changes is their scale and posture: each becomes a giant that never fits the rooms it hunts in.

## Rules

1. **A true giant, heavy and not thin.**
   - Full standing height is 3.1–3.3 m, about 1.75 × a 1.80 m person.
   - Body parts scale with it:
     - head about 0.36–0.42 m tall;
     - hands about 0.32 m;
     - shoes about 0.45 m;
     - shoulders 0.80–0.95 m across the clothing.
   - Proportions are a heavy adult's, scaled up. **Not** elongated or thin. Thin, dark, long-armed giants are Kane's Lifeform and its fan-game clones (01 §6).
   - When it stands, the fingertips reach mid-thigh, not the floor.
2. **It never fits.**
   - In every room it is compressed against the ceiling: the back of the shoulders (or the hood, or the load) is within 2–5 cm of the ceiling tiles.
   - Its legs fold, its spine bends, and its neck cranes down, so the face comes down near the player's eye line.
   - Elbows splay out. Clothing strains: creases across the back, sleeves bunched at the elbow, a collar pushed up.
   - The read is pressure: a body that would be bigger if the room let it.
3. **Its true size is shown once.** In a 5.4 m Tall zone it straightens up. That pose is the reveal.
4. **Navigation is unchanged.** The probe stays a capsule of r 0.30 tested at 0.40–1.95 m, and the sight ray stays at 1.60 m. The extra size is visual. The map only moves position and yaw and calls `TickAnimation`; a production rig would read the ceiling height and blend between the poses below.

## Poses (one creature module, four poses)

Each pose's limits are checked on export. They are given to `build_creature.py` through the module's `POSES` dict.

| Pose | Where | Top of the figure | Face centre | Half-width | Notes |
|---|---|---|---|---|---|
| `low` | under the 2.4 m Low ceiling | ≤ 2.37 (touching) | 1.30–1.65 | ≤ 0.80 | Deepest fold: knees high, one hand or knuckles may rest on the floor, head hung low under the shoulders |
| `std` | under the 2.9 m Standard / Office ceiling | 2.80–2.86 (touching) | 1.55–1.80 | ≤ 0.80 | The main hunting pose. The shoulders/back press the tiles and the head hangs forward and down to eye height |
| `door` | squeezing through the 1.0 × 2.1 m door | everything within \|y\| < 0.15 of the door plane (y = 0) must be ≤ 2.08 high and within \|x\| ≤ 0.48 | 1.2–1.7 | — | Half through the doorway: the head and leading shoulder are on the −Y side, the rest behind on +Y. It turns 60–90° sideways and leads with one shoulder, head ducked, one hand gripping the jamb (the grip can sit beyond \|y\| 0.15) |
| `tall` | a 5.4 m Tall zone | 3.10–3.30 | 2.8–3.1 | ≤ 0.85 | Nearly upright, a slight stoop: the reveal |

- **Silhouettes** use the same 400 px per metre on a 2.4 × 3.6 m canvas (`SIL_FRAME = (2.4, 3.6)`), so a Figma line-up stays at true scale beside the human-scale ones.
- **Budget for these concept meshes:** ≤ 18 k triangles per pose and ≤ 6 material slots. Production would use one rig and these poses as targets.

## Why this works for FrontRooms

- **The rooms do the acting.** A body pressed under ceiling tiles makes the fixed 2.4 / 2.9 m Backrooms ceilings feel low and close: the space itself becomes the threat.
- **It uses the level's own variation.** The Low (35 %), Standard (55 %) and Tall (10 %) ceilings each give a different silhouette for free.
- **The door becomes an event.** Watching it fold through a 1.0 m doorway is the IP's doorway reveal (01 §5 rule 6), stretched over several seconds.
- **The IP's hunters are 2.3–3.4 m tall** (Pirate Clark's performer is 7'7"; the Lifeform is presumed 11 ft; 01 §7). FrontRooms' Hunter now matches that scale but keeps the period-person anchor.
