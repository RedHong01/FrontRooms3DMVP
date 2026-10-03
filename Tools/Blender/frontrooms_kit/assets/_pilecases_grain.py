"""Grain-aware metre UVs for the pilecases group (helper, NOT an asset module).

STATUS 2026-10-02: kitlib._uv_metres now reads fr_grain / fr_uv_offset
itself, so install() is a no-op (kept for older kitlib copies). The wood
albedos are seamless CC0 scans now: callers pass tile = the slot's TileSize
(Teak / Cherry 1.0, Walnut 1.8, PinePallet 1.4, Plywood 0.5) so each part
just lands on its own patch; the seam logic below only matters for parts
longer than a tile. The text below describes the original DoorVeneer setup.

Used by dresser_70s, rolling_cabinet, side_table_turned, pallet and crate.

Why: every wood slot (Prop_WoodTeak / Cherry / Dark / Plywood / PinePallet) is
rendered in Unity with the DoorVeneer texture, whose grain runs along V.
kitlib._uv_metres puts V on world Z for faces pointing +-X / +-Y and on world Y
for faces pointing +-Z, so a 0.84 m drawer front, a face rail or a pallet
stringer gets vertical (cross) grain and a 0.90 m top gets front-to-back grain.

What install(kit) does: on THIS Kit instance only (kitlib.py is not edited), the
metre projection of wood parts is replaced by one that puts V along the
part's grain axis whenever that axis lies in the face's plane:

* grain axis = obj["fr_grain"] ("x" / "y" / "z") if set, else per face the
  longer of the part's two in-plane world extents (so a board's long faces,
  edges and a mitred plinth ring all run along the board; a tall side panel
  stays vertical; end-grain faces fall back to the longer in-plane edge);
* obj["fr_uv_offset"] = (du, dv) shifts that part's UVs, so neighbouring
  boards / drawer fronts do not share one continuous sheet of grain
  (scatter_offsets() sets it from a seed);
* non-wood slots keep kitlib's mapping exactly.

Texel density stays 1 UV unit per metre, as in kitlib. If kitlib's own
_uv_metres later learns fr_grain, install() does nothing and kitlib's version
(which reads the same properties) takes over; this file can then be deleted.
"""

import inspect
import random

import bmesh

import kitlib

WOOD_SLOTS = ("Prop_WoodCherry", "Prop_WoodOak", "Prop_WoodTeak", "Prop_WoodDark",
              "Prop_WoodLaminate", "Prop_Plywood", "Prop_PinePallet")


def _kitlib_has_grain():
    try:
        return "fr_grain" in inspect.getsource(kitlib.Kit._uv_metres)
    except (OSError, TypeError):
        return False


def _slot_of(obj):
    mats = obj.data.materials
    return mats[0].name if len(mats) and mats[0] is not None else ""


def _uv_metres_grain(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.loops.layers.uv.verify()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    wood = _slot_of(obj).split(".")[0] in WOOD_SLOTS
    forced = obj.get("fr_grain")
    forced = "xyz".index(forced) if forced in ("x", "y", "z") else None
    pts = [mw @ v.co for v in bm.verts]
    ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)] if pts else [1, 1, 1]
    off = obj.get("fr_uv_offset")
    du, dv = (float(off[0]), float(off[1])) if off is not None else (0.0, 0.0)
    for face in bm.faces:
        n = (rot @ face.normal).normalized()
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        if az >= ax and az >= ay:
            axis, s, plane = 2, (1 if n.z >= 0 else -1), (0, 1)
        elif ax >= ay:
            axis, s, plane = 0, (1 if n.x >= 0 else -1), (1, 2)
        else:
            axis, s, plane = 1, (1 if n.y >= 0 else -1), (0, 2)
        g = None
        if wood:
            if forced is not None and forced in plane:
                g = forced
            else:
                g = plane[0] if ext[plane[0]] > ext[plane[1]] else plane[1]
        for loop in face.loops:
            p = mw @ loop.vert.co
            # kitlib's default mapping (V = world Y on +-Z faces, world Z otherwise)
            if axis == 2:
                u, v = p.x * s, p.y
            elif axis == 0:
                u, v = -p.y * s, p.z
            else:
                u, v = -p.x * s, p.z
            if g is not None:
                if axis == 2 and g == 0:      # top / bottom, grain along X
                    u, v = -p.y * s, p.x
                elif axis == 0 and g == 1:    # end face, grain along Y
                    u, v = -p.z * s, p.y
                elif axis == 1 and g == 0:    # front / back, grain along X
                    u, v = p.z * s, p.x
            loop[layer].uv = (u + du, v + dv)
    bm.to_mesh(mesh)
    bm.free()


def install(kit):
    """Use the grain-aware projection for this Kit instance's metre UVs."""
    if not _kitlib_has_grain():
        kit._uv_metres = _uv_metres_grain


def scatter_offsets(kit, seed, slots=WOOD_SLOTS, tile=(0.6, 1.2), skip=(), margin=0.03, seam_at=None):
    """Give every part on `slots` its own UV offset.

    The DoorVeneer albedo is not seamless along V (its top rows are ~15 %
    brighter than its bottom rows), so where a part is shorter than one tile
    along its grain the V offset is chosen to keep the whole part inside one
    tile: no seam across a drawer front or a rail. A part too long for that
    (pallet boards, lid cleats) gets its seam placed at world coordinate
    `seam_at` along its grain, if given (e.g. over a stringer / mid cleat),
    else at random. U is random in one tile.
    """
    rng = random.Random(seed)
    tu, tv = tile
    for obj in kit.parts:
        if _slot_of(obj).split(".")[0] not in slots or obj.name.split(".")[0] in skip:
            continue
        m = obj.matrix_basis
        pts = [m @ v.co for v in obj.data.vertices]
        ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
        forced = obj.get("fr_grain")
        g = "xyz".index(forced) if forced in ("x", "y", "z") else max(range(3), key=lambda i: ext[i])
        lo, length = min(p[g] for p in pts), ext[g]
        du = rng.uniform(0.0, tu)
        if length + 2 * margin < tv:
            dv = rng.uniform(margin, tv - length - margin) - lo
        elif seam_at is not None:
            dv = (-seam_at) % tv
        else:
            dv = rng.uniform(0.0, tv)
        obj["fr_uv_offset"] = (round(du, 4), round(dv, 4))
