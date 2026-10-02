"""Download the CC0 sources Red approved on 2026-10-02 (research/10_synthesis.md §2.3).

  python3 Tools/lookdev/fetch_cc0.py [dest]   (default Tools/lookdev/cc0_src)

Poly Haven files are resolved through api.polyhaven.com (URLs + md5 checked);
ambientCG zips come from ambientcg.com/get. Everything is CC0 1.0. Raw files
stay outside Assets/ (git-ignored); importers write the packed maps.
"""
import hashlib, json, os, sys, urllib.request

DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "cc0_src")
UA = {"User-Agent": "FrontRooms-asset-fetch/1.0 (student project)"}

PH_TEXTURES = {  # id -> maps (2K JPG)
    "teak_veneer": ["Diffuse", "nor_gl", "arm"],
    "lacquered_cherry_wood": ["Diffuse", "nor_gl", "arm"],
    "dark_wood": ["Diffuse", "nor_gl", "arm"],
    "red_oak_veneer": ["Diffuse", "nor_gl", "arm"],
    "walnut_veneer": ["Diffuse", "nor_gl", "arm"],
    "plywood": ["Diffuse", "nor_gl", "arm"],
    "poly_wool_herringbone": ["Diffuse", "nor_gl", "arm"],
    "rough_linen": ["Diffuse", "nor_gl", "arm"],
    "velour_velvet": ["Diffuse", "nor_gl", "arm"],
    "floral_jacquard": ["Diffuse", "nor_gl", "arm", "Displacement"],
    "dirty_carpet": ["nor_gl", "arm"],
    "beige_wall_001": ["Diffuse", "nor_gl", "arm"],
    "polystyrene": ["nor_gl", "arm"],
}
PH_MODELS = ["GreenChair_01"]
AMBIENTCG = [
    "Chipboard004_1K", "Plastic013B_1K", "Plastic018B_1K", "Plastic012B_1K", "Metal028_1K", "Metal016_1K",
    "Metal050C_1K", "Leather027_1K", "Planks021_1K", "Wood096_1K", "Tape005_1K", "CardboardSet001_2K",
    "SurfaceImperfections013_1K", "SurfaceImperfections001_1K", "SurfaceImperfections007_1K",
    "SurfaceImperfections015_1K", "Leaking001_1K", "Leaking006_1K", "Scratches005_1K", "Fingerprints002_1K",
    "Smear007_1K",
]


def get(url, path, md5=None):
    if os.path.exists(path) and (md5 is None or hashlib.md5(open(path, "rb").read()).hexdigest() == md5):
        return os.path.getsize(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        data = r.read()
    if md5 and hashlib.md5(data).hexdigest() != md5:
        raise RuntimeError("md5 mismatch for " + url)
    open(path, "wb").write(data)
    return len(data)


def api(id_):
    with urllib.request.urlopen(urllib.request.Request("https://api.polyhaven.com/files/" + id_, headers=UA), timeout=60) as r:
        return json.load(r)


total = 0
log = []
for id_, maps in PH_TEXTURES.items():
    files = api(id_)
    for m in maps:
        f = files[m]["2k"]["jpg"]
        n = get(f["url"], os.path.join(DEST, "polyhaven", id_, os.path.basename(f["url"])), f.get("md5"))
        total += n
    log.append("polyhaven/%s  CC0  https://polyhaven.com/a/%s" % (id_, id_))
    print("ok", id_, flush=True)
for id_ in PH_MODELS:
    g = api(id_)["gltf"]["2k"]["gltf"]
    base = os.path.join(DEST, "polyhaven", id_)
    total += get(g["url"], os.path.join(base, os.path.basename(g["url"])), g.get("md5"))
    for rel, inc in g.get("include", {}).items():
        total += get(inc["url"], os.path.join(base, rel), inc.get("md5"))
    log.append("polyhaven/%s (model)  CC0  https://polyhaven.com/a/%s" % (id_, id_))
    print("ok", id_, flush=True)
for name in AMBIENTCG:
    asset = name.rsplit("_", 1)[0]
    total += get("https://ambientcg.com/get?file=%s-JPG.zip" % name, os.path.join(DEST, "ambientcg", asset, name + "-JPG.zip"))
    log.append("ambientcg/%s  CC0  https://ambientcg.com/a/%s" % (asset, asset))
    print("ok", name, flush=True)
open(os.path.join(DEST, "SOURCES.txt"), "w").write(
    "CC0 1.0 sources approved by Red on 2026-10-02 (no attribution required; credited as courtesy).\n" + "\n".join(log) + "\n")
print("total MB %.1f" % (total / 1e6))
