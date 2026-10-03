"""FrontRooms recorded sound library: real recordings -> modular FMOD assets.

    python3 recorded_library.py ingest    # copy the downloaded originals into AudioSource/Recorded
    python3 recorded_library.py analyze   # onset / band / hum report for every source (build/library_analysis.json)
    python3 recorded_library.py build     # cut, clean, layer and level -> AudioSource/FMOD_Library + manifest
    python3 recorded_library.py credits   # rewrite the recorded-source table in Documentation/AUDIO_LICENSES.md

Originals are never edited. Every processed asset is mono 48 kHz / 24-bit,
starts within 5 ms of its transient, ends on a 20-50 ms fade, peaks at or
below -3 dBFS, and is named <owner>_<module>_<surface>_<gait>_<layer>_<nn>.wav.
"""
import array
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))                 # Frontrooms3D
RAW = os.path.join(ROOT, "AudioSource", "Recorded")                     # untouched originals
LIB = os.path.join(ROOT, "AudioSource", "FMOD_Library")                 # processed, FMOD-ready
BUILD = os.path.join(HERE, "build")
DOWNLOADS = os.path.expanduser("~/Downloads")
SR = 48000

# id, Freesound user, file, licence, folder, what it becomes
CATALOG = [
    (148466, "conleec", "148466__conleec__foley_footsteps_carpet_001.wav", "CC0", "Footsteps",
     "Player carpet body (walk)"),
    (256209, "hannagreen", "256209__hannagreen__foodsteps-sneakers-on-carpet_mono.wav", "CC0", "Footsteps",
     "Player carpet body (sneakers)"),
    (560477, "jeroberts92", "560477__jeroberts92__carpet-dress-shoes.wav", "CC0", "Footsteps",
     "Relay steps (hard sole on carpet)"),
    (575318, "taure", "575318__taure__run-carpet.wav", "CC0", "Footsteps", "Player carpet body (run)"),
    (575321, "taure", "575321__taure__walk-carpet.wav", "CC0", "Footsteps", "Player carpet body (walk)"),
    (187617, "bewagne", "187617__bewagne__wet_soggy_squishy_footsteps.wav", "CC-BY 3.0", "Wet",
     "Waterlogged steps + moisture layer"),
    (583287, "Profispiesser", "583287__profispiesser__fx-sasc-wet-water-rag-movement-squishy-soggy-movement-plants.wav",
     "CC0", "Wet", "Moisture and peel layers"),
    (768656, "Nox_Sound", "768656__nox_sound__foley_door_wood_handle_metal_locked_sequence_stereo.wav", "CC0",
     "Doors", "Handle, locked rattle"),
    (341176, "klangfabrik", "341176__klangfabrik__stairwell-door-panic-bar-and-slam.wav", "CC0", "Doors",
     "Unlatch (panic bar), latch strike, slam"),
    (843829, "thaighaudio", "843829__thaighaudio__doorwood_community-centre-door-a-test_thaighaudio_2026.wav", "CC0",
     "Doors", "Swing, stops, latch"),
    (160213, "qubodup", "160213__qubodup__kickingforcingbreaking-wooden-door.flac", "CC0", "Doors",
     "Relay blow, break"),
    (454098, "kyles", "454098__kyles__neon-tube-fluorescent-light-hum-cu2.flac", "CC0", "Fluorescent",
     "Hum bed, fixture loop"),
    (125064, "EverydaySounds", "125064__everydaysounds__faulty-fluorescent-light-starter-hum.wav", "CC0",
     "Fluorescent", "Fixture strike / starter buzz"),
    (232447, "mmaruska", "232447__mmaruska__lights-flicker-on.wav", "CC0", "Fluorescent", "Fixture strike, tick, pop"),
    (406508, "kyles", "406508__kyles__room-tone-hotel-hallway-quiet-carpeted-light-ventilation-distant-voices-and-"
                      "occasional-elevator-beeps-and-dish-cutlery-gaza-2016.wav", "CC0", "RoomTone",
     "Air bed (carpeted hallway)"),
    (341512, "klankbeeld", "341512__klankbeeld__roomtone-emptymall-indoors-04-160327_00.wav", "CC-BY 4.0",
     "RoomTone", "Air bed (large space)"),
    (376607, "Soundkrampf", "376607__soundkrampf__window-hit-without-breaking.wav", "CC0", "Glass",
     "Window stress, crack"),
    (575283, "TRP", "575283__trp__various-window-breaks-smashes.flac", "CC0", "Glass", "Window shatter"),
    (616835, "TRP", "616835__trp__keys-various-jingle-2012.wav", "CC0", "Keys", "Key pickup"),
    (611276, "xkeril", "611276__xkeril__clothes-rustling-when-running.wav", "CC0", "Cloth",
     "Cloth layer, cloth event"),
]

TITLES = {  # Freesound titles, for attribution
    187617: "wet_soggy_squishy_footsteps.wav",
    341512: "roomtone emptymall indoors 04 160327_00.wav",
}


def url(sid, user):
    return "https://freesound.org/people/%s/sounds/%d/" % (user, sid)


def raw_path(entry):
    return os.path.join(RAW, entry[4], entry[2])


# ----------------------------------------------------------------- ingest
def ingest():
    copied = 0
    for e in CATALOG:
        dst = raw_path(e)
        if os.path.exists(dst):
            continue
        src = os.path.join(DOWNLOADS, e[2])
        if not os.path.exists(src):
            print("MISSING", e[2])
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    with open(os.path.join(RAW, "SOURCES.json"), "w") as f:
        json.dump([dict(id=e[0], user=e[1], file=os.path.join(e[4], e[2]), license=e[3], url=url(e[0], e[1]),
                        use=e[5]) for e in CATALOG], f, indent=1)
    print("ingested", copied, "new;", len(CATALOG), "catalogued in", RAW)


# ----------------------------------------------------------------- decode helpers
def decode(path, rate=SR, channel=None, start=None, dur=None, filters=None):
    """Decode to mono float list via ffmpeg (optionally one channel, a window, a filter chain)."""
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None:
        cmd += ["-ss", "%.4f" % start]
    if dur is not None:
        cmd += ["-t", "%.4f" % dur]
    cmd += ["-i", path]
    af = []
    if channel is not None:
        af.append("pan=mono|c0=c%d" % channel)
    if filters:
        af.append(filters)
    if af:
        cmd += ["-af", ",".join(af)]
    cmd += ["-ac", "1", "-ar", str(rate), "-f", "f32le", "-"]
    data = subprocess.run(cmd, check=True, capture_output=True).stdout
    a = array.array("f")
    a.frombytes(data)
    return a


def envelope(sig, rate, hop_ms=5.0):
    hop = max(1, int(rate * hop_ms / 1000))
    out = []
    for i in range(0, len(sig) - hop + 1, hop):
        s = 0.0
        for v in sig[i:i + hop]:
            s += v * v
        out.append(math.sqrt(s / hop))
    return out


def db(x):
    return 20 * math.log10(max(x, 1e-9))


def onsets(env, hop_ms=5.0, rise_db=9.0, floor_db=-55.0, min_gap_ms=120.0):
    """Energy-rise onsets: frame level jumps rise_db above the recent minimum."""
    gap = int(min_gap_ms / hop_ms)
    found, last = [], -10 ** 9
    lv = [db(v) for v in env]
    for i in range(4, len(lv)):
        recent = min(lv[max(0, i - 12):i - 1])
        if lv[i] > floor_db and lv[i] - recent >= rise_db and i - last >= gap:
            j = i                                         # walk to the local peak
            while j + 1 < len(lv) and lv[j + 1] >= lv[j]:
                j += 1
            found.append(dict(t=round((i - 1) * hop_ms / 1000, 3), peak_t=round(j * hop_ms / 1000, 3),
                              peak_db=round(lv[j], 1)))
            last = i
    return found


def goertzel(sig, rate, f):
    w = 2 * math.pi * f / rate
    c = 2 * math.cos(w)
    s1 = s2 = 0.0
    for x in sig:
        s0 = x + c * s1 - s2
        s2, s1 = s1, s0
    p = s1 * s1 + s2 * s2 - c * s1 * s2
    return math.sqrt(max(p, 0.0)) / len(sig)


# ----------------------------------------------------------------- analyze
def analyze():
    report = {}
    for e in CATALOG:
        path = raw_path(e)
        info = dict(use=e[5])
        rate = 16000
        sig = decode(path, rate)
        info["seconds"] = round(len(sig) / rate, 2)
        env = envelope(sig, rate)
        lv = sorted(db(v) for v in env)
        info["floor_db"] = round(lv[int(len(lv) * .1)], 1)
        info["median_db"] = round(lv[len(lv) // 2], 1)
        info["peak_db"] = round(lv[-1], 1)
        info["onsets"] = onsets(env)
        low = envelope(decode(path, rate, filters="lowpass=f=250,lowpass=f=250"), rate, 20)
        high = envelope(decode(path, rate, filters="highpass=f=1500,highpass=f=1500"), rate, 20)
        info["low_vs_high_db"] = round(db(sum(low) / len(low)) - db(sum(high) / len(high)), 1)
        if e[4] in ("Fluorescent", "RoomTone"):
            hs = decode(path, 4000, start=2.0, dur=8.0)
            cand = {}
            for f in (50, 60, 100, 120, 150, 180, 200, 240, 300, 360):
                cand[str(f)] = round(db(goertzel(hs, 4000, f)), 1)
            info["hum_db"] = cand
            best, bestv = None, -1
            for f10 in range(900, 2600, 2):                # 90-260 Hz in 0.2 Hz steps
                v = goertzel(hs, 4000, f10 / 10)
                if v > bestv:
                    best, bestv = f10 / 10, v
            info["strongest_90_260_hz"] = best
        report[str(e[0])] = info
        print(e[0], e[1], info["seconds"], "s floor", info["floor_db"], "median", info["median_db"], "peak",
              info["peak_db"], "onsets", len(info["onsets"]), "low-high", info["low_vs_high_db"],
              ("hum %s best %s" % (info.get("hum_db"), info.get("strongest_90_260_hz"))) if "hum_db" in info else "")
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "library_analysis.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"ingest": ingest, "analyze": analyze}[cmd]()
