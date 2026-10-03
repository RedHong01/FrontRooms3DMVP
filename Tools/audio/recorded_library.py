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
import wave
import zlib

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


# ================================================================= build
CACHE = os.path.join(BUILD, "lib_cache")
CREAK = os.path.join(ROOT, "Assets", "Resources", "Audio", "door-creak.wav")    # BigSoundBank 3205, CC0
MANIFEST = {}
CHANNEL = {}
TAU = 2 * math.pi

HUM_NOTCH = "equalizer=f=120:t=q:w=6:g=-5,equalizer=f=240:t=q:w=6:g=-4"      # keep bodies off the hum
MAINS_50 = ",".join("equalizer=f=%d:t=q:w=8:g=%d" % fg for fg in ((50, -12), (100, -16), (150, -10), (200, -14),
                                                                   (300, -10)))
BODY_CARPET = "highpass=f=45," + HUM_NOTCH + ",equalizer=f=180:t=q:w=1:g=2,highshelf=f=4500:g=-3,lowpass=f=12000"
BODY_TILE = "highpass=f=60," + HUM_NOTCH + ",equalizer=f=2800:t=q:w=1:g=2.5,lowpass=f=14000"
RELAY_BODY = "highpass=f=35,equalizer=f=90:t=q:w=1:g=3," + HUM_NOTCH + ",lowpass=f=3800,lowpass=f=3800"
THAIG = "highpass=f=50,equalizer=f=560:t=q:w=4:g=-14,afftdn=nr=10:nf=-62:tn=1"
KLANG = "highpass=f=50,afftdn=nr=14:nf=-54:tn=1"


def entry(sid):
    return next(e for e in CATALOG if e[0] == sid)


def src(sid):
    return sid if isinstance(sid, str) else raw_path(entry(sid))


def st(semitones):
    return 2 ** (semitones / 12.0)


def varispeed(ratio):
    """Tape-style speed change: pitch and length move together (the classic Foley weight trick)."""
    return "aresample=%d,asetrate=%d,aresample=%d" % (SR, round(SR * ratio), SR)


def denoise(floor_db, nr=12):
    return "afftdn=nr=%d:nf=%d:tn=1" % (nr, max(-80, min(-20, int(floor_db))))


def channels(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                          "-of", "csv=p=0", path], check=True, capture_output=True, text=True).stdout
    return int(out.strip().split(",")[0])


def best_channel(path):
    """Stereo recordings: keep the channel with the larger peak-to-floor ratio (no comb filtering from a fold-down)."""
    if channels(path) == 1:
        return None
    best, score = 0, -1e9
    for c in range(2):
        lv = sorted(db(v) for v in envelope(decode(path, 16000, channel=c, filters="highpass=f=40"), 16000, 10))
        snr = lv[int(len(lv) * .995)] - lv[int(len(lv) * .2)]
        if snr > score:
            best, score = c, snr
    return best


def prepared(sid, chain=""):
    """The whole source through an ffmpeg chain at 48 kHz mono, cached on disk."""
    path = src(sid)
    if path not in CHANNEL:
        CHANNEL[path] = best_channel(path)
    ch = CHANNEL[path]
    name = sid if isinstance(sid, int) else os.path.splitext(os.path.basename(path))[0]
    f = os.path.join(CACHE, "%s_%s_%08x.f32" % (name, ch, zlib.crc32(chain.encode())))
    if not os.path.exists(f):
        os.makedirs(CACHE, exist_ok=True)
        with open(f, "wb") as fh:
            decode(path, SR, channel=ch, filters=chain or None).tofile(fh)
    a = array.array("f")
    with open(f, "rb") as fh:
        a.frombytes(fh.read())
    return a


# ----------------------------------------------------------------- events and picks
def detect(sig, hop_ms=2.5, merge_ms=110, above_db=14, max_tail=.9):
    """Regions above floor+above_db, merged across short gaps (heel + toe = one step)."""
    env = envelope(sig, SR, hop_ms)
    lv = [db(v) for v in env]
    s = sorted(lv)
    floor = s[int(len(s) * .2)]
    thr = max(floor + above_db, s[-1] - 42)
    regs, i, n = [], 0, len(lv)
    while i < n:
        if lv[i] > thr:
            j = i
            while j < n and lv[j] > thr:
                j += 1
            if regs and (i - regs[-1][1]) * hop_ms <= merge_ms:
                regs[-1][1] = j
            else:
                regs.append([i, j])
            i = j
        else:
            i += 1
    out = []
    for a, b in regs:
        k = a
        while k > 0 and lv[k - 1] > floor + 6 and (a - k) * hop_ms < 40:
            k -= 1
        pk = max(range(a, b), key=lambda x: lv[x])
        e = b
        while e < n and lv[e] > floor + 4 and (e - k) * hop_ms < max_tail * 1000:
            e += 1
        out.append(dict(t=k * hop_ms / 1000, peak=lv[pk], end=e * hop_ms / 1000))
    return out, floor


def tilt(sig, i0, i1):
    """Brightness of the transient: first-difference energy over energy, in dB."""
    s = d = 0.0
    prev = sig[i0]
    for x in sig[i0 + 1:i1]:
        s += x * x
        d += (x - prev) * (x - prev)
        prev = x
    return db(math.sqrt(d / max(s, 1e-12)))


def refine(sig, t, length, max_delay=.12, min_snr=30.0, hop_ms=2.5):
    """One event per slice: the main hit early, the slice ends before the next onset, and the noise
    floor inside it is at least min_snr below the hit. Returns the usable length or None."""
    i0, i1 = int(t * SR), int((t + length) * SR)
    lv = [db(v) for v in envelope(sig[i0:i1], SR, hop_ms)]
    if len(lv) < 8:
        return None
    pk = max(range(len(lv)), key=lambda k: lv[k])
    if pk * hop_ms / 1000 > max_delay:
        return None
    start = pk + int(.12 / (hop_ms / 1000))               # look for a second contact after the first settles
    for k in range(start, len(lv)):
        recent = min(lv[max(0, k - 12):k])
        if lv[k] - recent >= 9 and lv[k] >= lv[pk] - 10:
            length = (k - 4) * hop_ms / 1000                # stop ~10 ms before it
            lv = lv[:k - 4]
            break
    w = int(20 / hop_ms)
    quiet = min(sum(lv[k:k + w]) / w for k in range(0, max(1, len(lv) - w)))
    if lv[pk] - quiet < min_snr:
        return None
    return length


def pick(sig, n, min_len, max_len, stops=False, region=None, window=(-6, 5), tilt_tol=5.0, merge_ms=110,
         above_db=14, loudest=False, max_delay=.12, min_snr=30.0):
    """Choose n clean, isolated, typical events. stops=True keeps only last steps before a pause."""
    ev, _ = detect(sig, merge_ms=merge_ms, above_db=above_db)
    total = len(sig) / SR
    cands = []
    for i, e in enumerate(ev):
        if region and not region[0] <= e["t"] <= region[1]:
            continue
        prev_end = ev[i - 1]["end"] if i else -1.0
        nxt = ev[i + 1]["t"] if i + 1 < len(ev) else total
        if e["t"] - prev_end < .03:
            continue
        gap = nxt - e["t"]
        if stops and gap < .95:
            continue
        length = min(max_len, gap - .015, max(min_len, e["end"] - e["t"] + .05))
        length = refine(sig, e["t"], length, max_delay, min_snr)
        if length is None or length < min_len:
            continue
        i0 = int(e["t"] * SR)
        cands.append(dict(t=e["t"], len=length, peak=e["peak"], tilt=tilt(sig, i0, i0 + int(.12 * SR))))
    if not cands:
        return []
    levels = sorted(c["peak"] for c in cands)
    ref = levels[int(len(levels) * .65)]
    tref = sorted(c["tilt"] for c in cands)[len(cands) // 2]
    good = [c for c in cands if window[0] <= c["peak"] - ref <= window[1] and abs(c["tilt"] - tref) <= tilt_tol]
    if loudest:
        good.sort(key=lambda c: -c["peak"])
    else:
        good.sort(key=lambda c: abs(c["peak"] - ref) + .5 * abs(c["tilt"] - tref))
    return sorted(good[:n], key=lambda c: c["t"])


# ----------------------------------------------------------------- sample ops
def cut(sig, t, length, pre=.004, fin=.0015, fout=.03, lead=0.0):
    """Slice with a short pre-roll (transient within 5 ms of the start) and a cosine tail fade."""
    i0 = max(0, int((t - pre) * SR))
    i1 = min(len(sig), int((t + length) * SR))
    out = [0.0] * int(lead * SR) + list(sig[i0:i1])
    a, b = int(fin * SR), min(int(fout * SR), (i1 - i0) // 2)
    head = int(lead * SR)
    for k in range(min(a, i1 - i0)):
        out[head + k] *= k / a
    for k in range(b):
        out[-1 - k] *= .5 - .5 * math.cos(math.pi * k / b)
    return out


def mix(*layers):
    """layers: (samples, offset_s, gain_db)."""
    n = max(int(o * SR) + len(x) for x, o, _ in layers)
    out = [0.0] * n
    for x, o, g in layers:
        k, j0 = 10 ** (g / 20), int(o * SR)
        for i, v in enumerate(x):
            out[j0 + i] += v * k
    return out


def peak_db(x):
    return db(max(abs(v) for v in x) if x else 0.0)


def rms_db(x):
    return db(math.sqrt(sum(v * v for v in x) / max(1, len(x))))


def loudness(x):
    """Short-term level: loudest 50 ms RMS after a 100 Hz high-pass (a rough K-weighting)."""
    a = math.exp(-TAU * 100 / SR)
    lp, hp = 0.0, []
    for v in x:
        lp = (1 - a) * v + a * lp
        hp.append(v - lp)
    w, best = int(.05 * SR), 0.0
    for i in range(0, max(1, len(hp) - w), int(.01 * SR)):
        seg = hp[i:i + w]
        best = max(best, sum(v * v for v in seg) / max(1, len(seg)))
    return db(math.sqrt(best))


def level_set(items, peak=-3.0):
    """Equal short-term loudness across a set, then the set's typical peak at `peak`, no file above -1 dBFS."""
    L = [loudness(x) for x in items]
    P = [peak_db(x) for x in items]
    med = sorted(L)[len(L) // 2]
    gains = [med - l for l in L]
    tops = sorted(p + g for p, g in zip(P, gains))
    shift = peak - tops[int(.8 * (len(tops) - 1))]
    out = []
    for x, p, g in zip(items, P, gains):
        total = min(g + shift, -1.0 - p)
        k = 10 ** (total / 20)
        out.append([v * k for v in x])
    return out


def level_rms(x, target, peak=-3.0):
    g = min(target - rms_db(x), peak - peak_db(x))
    k = 10 ** (g / 20)
    return [v * k for v in x]


def write24(rel, x):
    path = os.path.join(LIB, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    buf = bytearray()
    for v in x:
        buf += int(round(max(-1.0, min(1.0, v)) * 8388607)).to_bytes(3, "little", signed=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(bytes(buf))


def tighten(x, below=30.0, pre=.004, fin=.0015):
    """Drop dead air so the first sample within `below` dB of the peak sits `pre` s from the start."""
    pk = max(abs(v) for v in x) or 1.0
    thr = pk * 10 ** (-below / 20)
    i = next(k for k, v in enumerate(x) if abs(v) >= thr)
    y = x[max(0, i - int(pre * SR)):]
    a = int(fin * SR)
    for k in range(min(a, len(y))):
        y[k] *= k / a
    return y


def emit(prefix, items, sources, note, level=True, peak=-3.0, tight=True):
    if tight:
        items = [tighten(x) for x in items]
    if level:
        items = level_set(items, peak)
    names = []
    for k, (x, s) in enumerate(zip(items, sources)):
        rel = "%s_%02d.wav" % (prefix, k + 1)
        write24(rel, x)
        MANIFEST[rel] = dict(seconds=round(len(x) / SR, 4), source=s, note=note)
        names.append(rel)
    print("  %-48s %2d  %s" % (prefix, len(names), note))
    return names


def emit_one(rel, x, source, note):
    write24(rel, x)
    MANIFEST[rel] = dict(seconds=round(len(x) / SR, 4), source=source, note=note)
    print("  %-48s  1  %s" % (rel, note))


def ref(sid, t):
    return "%s@%.2fs" % (sid if isinstance(sid, int) else os.path.basename(sid), t)


# ----------------------------------------------------------------- loops
def best_lag(sig, i0, lag0, search, probe=2400):
    """Loop length near lag0 whose seam is in phase (max normalised correlation)."""
    refw = sig[i0:i0 + probe]
    e0 = sum(a * a for a in refw)
    best, bestc = lag0, -2.0
    for lag in range(lag0 - search, lag0 + search + 1):
        seg = sig[i0 + lag:i0 + lag + probe]
        num = sum(a * b for a, b in zip(refw, seg))
        den = math.sqrt(e0 * sum(b * b for b in seg)) or 1.0
        if num / den > bestc:
            best, bestc = lag, num / den
    return best, bestc


def loop_from(sig, t0, seconds, xfade, f0=None, power=False):
    i0, L, X = int(t0 * SR), int(seconds * SR), int(xfade * SR)
    corr = None
    if f0:
        L, corr = best_lag(sig, i0, L, int(SR / f0) + 2)
    seg = sig[i0:i0 + L + X]
    y = list(seg[:L])
    for n in range(X):
        w = n / X
        a, b = (math.sqrt(w), math.sqrt(1 - w)) if power else (w, 1 - w)
        y[n] = seg[n] * a + seg[L + n] * b
    return y, corr


def calmest(path, seconds, chain="highpass=f=300,lowpass=f=3000"):
    """Start of the window with the smallest level spike above its median (no voices, beeps or bumps)."""
    lv = [db(v) for v in envelope(decode(path, 16000, channel=CHANNEL.get(path), filters=chain), 16000, 100)]
    w = int(seconds / .1)
    best, bi = 1e9, 0
    for i in range(10, len(lv) - w - 10, 5):
        s = sorted(lv[i:i + w])
        score = s[-1] - s[len(s) // 2]
        if score < best:
            best, bi = score, i
    return bi * .1, best


def hum_f0(sig, t0, dur=4.0):
    """Fundamental of the 120 Hz ballast family from its strongest partial near 240 Hz."""
    x = sig[int(t0 * SR):int((t0 + dur) * SR):4]                 # 12 kHz is plenty for 240 Hz
    best, bf = -1, 240.0
    f = 236.0
    while f <= 244.0:
        v = goertzel(x, SR / 4, f)
        if v > best:
            best, bf = v, f
        f += .02
    return bf / 2


# ----------------------------------------------------------------- the library
def build_steps():
    print("player steps")
    tw = prepared(575321, BODY_CARPET)
    hg = prepared(256209, "highpass=f=45,volume=30dB," + denoise(-48) + "," + BODY_CARPET.split(",", 1)[1])
    hgp = pick(hg, 4, .26, .42)
    walk = [(tw, 575321, p) for p in pick(tw, 10 - len(hgp), .26, .42)] + [(hg, 256209, p) for p in hgp]
    emit("Foley/plr_step_carpet_walk_body", [cut(s, p["t"], p["len"]) for s, _, p in walk],
         [ref(i, p["t"]) for _, i, p in walk], "padded damp carpet, walk (sneakers)")
    tr = prepared(575318, BODY_CARPET)
    runs = pick(tr, 10, .2, .34, merge_ms=60)
    emit("Foley/plr_step_carpet_run_body", [cut(tr, p["t"], p["len"]) for p in runs],
         [ref(575318, p["t"]) for p in runs], "padded damp carpet, run")
    hgs = pick(hg, 2, .3, .5, stops=True, window=(-9, 4))
    stops = [(tw, 575321, p) for p in pick(tw, 5 - len(hgs), .3, .5, stops=True, window=(-9, 4))] + \
            [(hg, 256209, p) for p in hgs]
    emit("Foley/plr_step_carpet_stop_body", [cut(s, p["t"], p["len"], fout=.06) for s, _, p in stops],
         [ref(i, p["t"]) for _, i, p in stops], "last step before standing still")

    cl = prepared(148466, BODY_TILE)
    tile = pick(cl, 10, .26, .42, window=(-8, 5), tilt_tol=4)
    emit("Foley/plr_step_tile_walk_body", [cut(cl, p["t"], p["len"]) for p in tile],
         [ref(148466, p["t"]) for p in tile], "glue-down carpet tile, walk")
    trt = prepared(575318, BODY_TILE)
    used = [p["t"] for p in runs]
    tile_runs = [p for p in pick(trt, 18, .2, .34, merge_ms=60) if all(abs(p["t"] - u) > .05 for u in used)][:8]
    emit("Foley/plr_step_tile_run_body", [cut(trt, p["t"], p["len"]) for p in tile_runs],
         [ref(575318, p["t"]) for p in tile_runs], "glue-down carpet tile, run (brighter EQ, other takes)")
    twt = prepared(575321, BODY_TILE)
    cs = pick(cl, 4, .3, .5, stops=True, window=(-9, 4))
    tstops = [(cl, 148466, p) for p in cs] + [(twt, 575321, p) for p in pick(twt, 4 - len(cs), .3, .5, stops=True,
                                                                             window=(-9, 4))]
    emit("Foley/plr_step_tile_stop_body", [cut(x, p["t"], p["len"], fout=.06) for x, _, p in tstops],
         [ref(i, p["t"]) for _, i, p in tstops], "last step before standing still")

    print("damp layers")
    rag_lo = prepared(583287, "highpass=f=280,highpass=f=280,lowpass=f=2200,lowpass=f=2200," + denoise(-66, 10))
    moist = pick(rag_lo, 8, .1, .24, above_db=12, window=(-10, 8), tilt_tol=8, max_delay=.15, min_snr=18)
    emit("Foley/plr_step_damp_any_moist", [cut(rag_lo, p["t"], p["len"], fout=.05) for p in moist],
         [ref(583287, p["t"]) for p in moist], "wet pile compressing, 300 Hz-2 kHz (Dampness)")
    rag_hi = prepared(583287, "highpass=f=1800,highpass=f=1800,lowpass=f=6000," + denoise(-64, 8))
    peel = pick(rag_hi, 8, .05, .14, above_db=12, merge_ms=40, window=(-10, 8), tilt_tol=8, max_delay=.06, min_snr=18)
    leads = [.06, .11, .08, .14, .07, .12, .09, .13]                # sole lifts 50-150 ms after the heel
    emit("Foley/plr_step_damp_any_peel", [[0.0] * int(d * SR) + tighten(cut(rag_hi, p["t"], p["len"], fout=.03))
                                          for p, d in zip(peel, leads)],
         [ref(583287, p["t"]) for p in peel], "sticky release 2-5 kHz, delayed 50-150 ms (Dampness)",
         peak=-6.0, tight=False)
    sq = prepared(187617, "highpass=f=110,lowpass=f=7500," + denoise(-68, 10))
    squish = pick(sq, 6, .14, .32, above_db=12, window=(-8, 12), tilt_tol=8, loudest=True, max_delay=.15, min_snr=18)
    emit("Foley/plr_step_soaked_any_squish", [cut(sq, p["t"], p["len"], fout=.06) for p in squish],
         [ref(187617, p["t"]) for p in squish], "waterlogged shoe (Dampness > .75 only); CC-BY bewagne")

    print("cloth")
    cloth = prepared(611276, "highpass=f=220,lowpass=f=9500")
    crun = pick(cloth, 8, .16, .3, region=(25, 40.2), above_db=8, window=(-4, 8), max_delay=.1, min_snr=14)
    emit("Foley/plr_step_any_run_cloth", [cut(cloth, p["t"], p["len"], fout=.05) for p in crun],
         [ref(611276, p["t"]) for p in crun], "jacket swish per stride")
    cmove = pick(cloth, 6, .35, .6, region=(0, 25), above_db=8, window=(-5, 8), merge_ms=200, max_delay=.3, min_snr=12)
    emit("Foley/plr_cloth_move", [cut(cloth, p["t"], p["len"], fout=.12) for p in cmove],
         [ref(611276, p["t"]) for p in cmove], "body movement")


def build_relay():
    print("relay")
    rw = prepared(560477, varispeed(st(-3)) + "," + RELAY_BODY)
    walk = pick(rw, 10, .3, .55)
    emit("Relay/rly_step_carpet_walk_body", [cut(rw, p["t"], p["len"], fout=.06) for p in walk],
         [ref(560477, p["t"] * st(-3)) for p in walk], "hard soles on damp carpet, -3 st")
    rr = prepared(560477, varispeed(st(-2)) + "," + RELAY_BODY.replace("lowpass=f=3800,lowpass=f=3800", "lowpass=f=5000"))
    run = pick(rr, 8, .22, .38, window=(-2, 8), loudest=True, merge_ms=70)
    emit("Relay/rly_step_carpet_run_body", [cut(rr, p["t"], p["len"], fout=.05) for p in run],
         [ref(560477, p["t"] * st(-2)) for p in run], "hard soles, forceful, -2 st")
    rd = prepared(560477, varispeed(st(-4)) + "," + RELAY_BODY)
    drag_steps = pick(rd, 4, .3, .5)
    rub = prepared(611276, varispeed(st(-7)) + ",highpass=f=120,lowpass=f=1200")
    rubs = pick(rub, 4, .45, .7, above_db=8, window=(-4, 8), merge_ms=200, max_delay=.4, min_snr=12)
    drags = [mix((cut(rd, a["t"], a["len"]), 0, 0), (cut(rub, b["t"], b["len"], fout=.15), .08, -4))
             for a, b in zip(drag_steps, rubs)]
    emit("Relay/rly_step_carpet_drag_body", drags,
         ["%s + %s" % (ref(560477, a["t"] * st(-4)), ref(611276, b["t"] * st(-7))) for a, b in zip(drag_steps, rubs)],
         "slow step + dragged cloth on carpet")


def nox_pairs(sig):
    ev, _ = detect(sig, merge_ms=60, above_db=12)
    starts = [0.0, 1.37, 2.96, 4.37, 5.66, 6.99, 8.30, 9.85]
    out = []
    for s in starts:
        first = min(ev, key=lambda e: abs(e["t"] - s))["t"]
        later = [e for e in ev if first + .25 < e["t"] < first + .85]
        second = later[0] if later else None
        out.append((first, second["t"] if second else first + .5, second["end"] if second else first + .9))
    return out


def build_doors():
    print("doors")
    nox = prepared(768656, "highpass=f=60")
    pairs = nox_pairs(nox)
    emit("Door/door_handle_press", [cut(nox, a, min(.34, b - a - .02), fout=.05) for a, b, _ in pairs],
         [ref(768656, a) for a, _, _ in pairs], "lever handle pressed")
    emit("Door/door_locked_rattle", [cut(nox, a, min(1.05, max(e, b + .3) - a), fout=.08) for a, b, e in pairs],
         [ref(768656, a) for a, _, _ in pairs], "handle against a locked bolt, press + release")
    emit("Door/door_blow_rattle", [cut(nox, b, .3, fout=.08) for _, b, _ in pairs[1:3]],
         [ref(768656, b) for _, b, _ in pairs[1:3]], "hardware rattle after a blow")

    th = prepared(843829, THAIG)
    t_un = [.74, .96, 1.19, 1.55, 1.68]
    emit("Door/door_unlatch_bolt", [cut(th, t, .2, fout=.05) for t in t_un], [ref(843829, t) for t in t_un],
         "latch bolt and spring")
    t_soft = [19.50, 23.80]
    emit("Door/door_latch_soft", [cut(th, t, .45, fout=.12) for t in t_soft], [ref(843829, t) for t in t_soft],
         "door eased shut")
    body = prepared(843829, THAIG + ",lowpass=f=900")
    norms = [(19.50, 13.44), (23.80, 28.93), (19.50, 28.93)]
    emit("Door/door_latch_norm", [mix((cut(th, a, .45, fout=.12), 0, 0), (cut(body, b, .55, fout=.2), .002, -9))
                                  for a, b in norms],
         ["%s + %s" % (ref(843829, a), ref(843829, b)) for a, b in norms], "latch click over a softened body")
    kl = prepared(341176, KLANG)
    emit("Door/door_latch_slam", [cut(th, 13.44, .95, fout=.3), cut(th, 28.93, .95, fout=.3), cut(kl, .11, .8, fout=.35)],
         [ref(843829, 13.44), ref(843829, 28.93), ref(341176, .11)], "slammed shut (stairwell tail trimmed)")
    cr = prepared(CREAK, "highpass=f=50")
    emit("Door/door_stop_soft", [cut(th, 12.82, .35, fout=.1), cut(th, 28.30, .35, fout=.1), cut(cr, 1.80, .45, fout=.12)],
         [ref(843829, 12.82), ref(843829, 28.30), ref(CREAK, 1.80)], "leaf bumps the stop")
    thm = prepared(843829, varispeed(st(-2)) + "," + THAIG + ",lowpass=f=1800")
    emit("Door/door_stop_med", [cut(thm, 13.44 / st(-2), .45, fout=.15), cut(thm, 28.93 / st(-2), .45, fout=.15)],
         [ref(843829, 13.44), ref(843829, 28.93)], "leaf hits the stop, -2 st")
    thh = prepared(843829, varispeed(st(-1)) + "," + THAIG)
    emit("Door/door_stop_hard", [cut(kl, .11, .7, fout=.3), cut(kl, 6.21, .7, fout=.3), cut(thh, 13.44 / st(-1), .7, fout=.3)],
         [ref(341176, .11), ref(341176, 6.21), ref(843829, 13.44)], "leaf slams into the wall")
    t_mid = [18.68, .96, 1.19]
    emit("Door/door_stopmid_settle", [cut(th, t, .15, fout=.05) for t in t_mid], [ref(843829, t) for t in t_mid],
         "comes to rest mid-swing")
    tb = prepared(843829, varispeed(st(-5)) + "," + THAIG + ",lowpass=f=2200")
    kb = prepared(341176, varispeed(st(-4)) + "," + KLANG + ",lowpass=f=2600")
    emit("Door/door_blow_hit", [cut(tb, 13.44 / st(-5), 1.0, fout=.35), cut(tb, 28.93 / st(-5), 1.0, fout=.35),
                                cut(kb, .11 / st(-4), .9, fout=.35)],
         [ref(843829, 13.44), ref(843829, 28.93), ref(341176, .11)], "the Relay strikes the door, -4/-5 st")
    qb = prepared(160213, "highpass=f=200")
    emit("Door/door_blow_split", [cut(qb, .15, .4, fout=.1), cut(qb, .45, .5, fout=.15)],
         [ref(160213, .15), ref(160213, .45)], "wood splitting")
    qf = prepared(160213, "highpass=f=40")
    ql = prepared(160213, varispeed(st(-1)) + ",highpass=f=40")
    emit("Door/door_break_rip", [mix((cut(qf, .03, .97, fout=.25), 0, 0), (cut(th, 13.44, .9, fout=.3), .01, -6)),
                                 mix((cut(ql, .03 / st(-1), 1.0, fout=.25), 0, 0), (cut(th, 28.93, .9, fout=.3), .01, -6))],
         [ref(160213, .03) + " + " + ref(843829, 13.44), ref(160213, .03) + " + " + ref(843829, 28.93)],
         "door forced through")
    creak = prepared(CREAK, "highpass=f=180,lowpass=f=7000")
    loop, _ = loop_from(creak, .30, .95, .2, power=True)
    emit_one("Door/door_swing_creak_loop.wav", level_rms(loop, -20), ref(CREAK, .30), "hinge stick-slip, looped")


def build_ambience():
    print("ambience")
    hum = prepared(454098, "highpass=f=40,lowpass=f=7000")
    t0, spike = calmest(src(454098), 12, chain="highpass=f=60")
    f0 = hum_f0(hum, t0 + 1)
    loop, corr = loop_from(hum, t0 + 1, 9.6, .4, f0=f0)
    emit_one("Ambience/amb_hum_bed_loop.wav", level_rms(loop, -20), ref(454098, t0 + 1),
             "60 Hz-mains tube hum, 120/240/360 Hz family (f0 %.2f, seam corr %.3f)" % (f0, corr))
    beat = prepared(454098, varispeed(118.5 / 120) + ",highpass=f=40,lowpass=f=7000")
    tb = (t0 + 1) / (118.5 / 120)
    loop, corr = loop_from(beat, tb, 9.6, .4, f0=f0 * 118.5 / 120)
    emit_one("Ambience/amb_hum_beat_loop.wav", level_rms(loop, -20), ref(454098, t0 + 1),
             "same hum detuned to 118.5 Hz: beats against the bed (Tension)")
    fx = prepared(454098, "highpass=f=60")
    tf = (t0 + 20) % 60 + 5
    loop, corr = loop_from(fx, tf, 4.0, .25, f0=hum_f0(fx, tf))
    emit_one("Ambience/amb_fixture_close_loop.wav", level_rms(loop, -18), ref(454098, tf), "one fixture up close")

    st1 = prepared(125064, varispeed(1.2) + ",highpass=f=60")          # 50 Hz mains (100 Hz) -> 120 Hz
    mm = prepared(232447, "highpass=f=60")
    emit("Ambience/amb_fixture_strike", [cut(st1, .27 / 1.2, 1.3, fout=.2), cut(mm, .85, 1.9, fout=.3)],
         [ref(125064, .27) + " x1.2 speed", ref(232447, .85)], "starter flicker into hum")
    t_tick = [.91, 1.60, 10.09]
    emit("Ambience/amb_fixture_tick", [cut(mm, t, .08, fout=.03) for t in t_tick], [ref(232447, t) for t in t_tick],
         "starter / ballast tick")

    for sid, name, note in ((406508, "hall", "carpeted hallway air, 50 Hz mains notched"),
                            (341512, "mall", "large empty interior, 50 Hz mains notched; CC-BY klankbeeld")):
        sig = prepared(sid, "highpass=f=30," + MAINS_50 + ",lowpass=f=9000")
        t, spike = calmest(src(sid), 24)
        loop, _ = loop_from(sig, t + 1, 20.0, 1.5, power=True)
        emit_one("Ambience/amb_air_%s_loop.wav" % name, level_rms(loop, -30), ref(sid, t + 1),
                 note + " (window spike %.1f dB)" % spike)


def build_glass_keys():
    print("glass, keys")
    sk = prepared(376607, "highpass=f=90")
    trp_hi = prepared(575283, "highpass=f=900")
    emit("Window/win_crack_hit", [cut(sk, .07, .9, fout=.3), cut(sk, 4.09, .9, fout=.3), cut(trp_hi, 50.38, .2, fout=.08)],
         [ref(376607, .07), ref(376607, 4.09), ref(575283, 50.38)], "pane flexes and cracks")
    trp = prepared(575283, "highpass=f=60")
    t_sh = [40.18, 43.26, 50.38]
    emit("Window/win_shatter", [cut(trp, t, 1.6, fout=.45) for t in t_sh], [ref(575283, t) for t in t_sh],
         "pane gives way", peak=-1.0)
    keys = prepared(616835, "highpass=f=250")
    t_k = [.54, 1.94, 9.76, 25.49, 27.20]
    emit("Foley/plr_key_pickup", [cut(keys, t, .8, fout=.25) for t in t_k], [ref(616835, t) for t in t_k],
         "key ring lifted")


def build():
    if os.path.isdir(LIB):
        shutil.rmtree(LIB)
    build_steps()
    build_relay()
    build_doors()
    build_ambience()
    build_glass_keys()
    os.makedirs(BUILD, exist_ok=True)
    for path in (os.path.join(BUILD, "library_manifest.json"), os.path.join(LIB, "LIBRARY.json")):
        with open(path, "w") as f:
            json.dump(MANIFEST, f, indent=1, sort_keys=True)
    print("built", len(MANIFEST), "assets into", LIB)


# ----------------------------------------------------------------- credits
def credits():
    path = os.path.join(ROOT, "Documentation", "AUDIO_LICENSES.md")
    text = open(path).read()
    marker = "\n## Recorded library (Freesound)\n"
    if marker in text:
        text = text[:text.index(marker)]
    lines = [marker.rstrip("\n"), "",
             "Originals live untouched in `AudioSource/Recorded/<folder>/`; processed FMOD assets are in "
             "`AudioSource/FMOD_Library/` (`LIBRARY.json` maps every asset to its source and second). "
             "Regenerate with `python3 Tools/audio/recorded_library.py build`.", "",
             "### Attribution required (ship these lines in the game credits)", ""]
    for e in CATALOG:
        if e[3].startswith("CC-BY"):
            lines.append('- "%s" by %s, %s, licensed under %s (https://creativecommons.org/licenses/by/%s/). '
                         'Cut, filtered, denoised and level-matched for FrontRooms.' %
                         (TITLES[e[0]], e[1], url(e[0], e[1]), e[3], e[3].split()[-1]))
    lines += ["", "### All sources", "", "| Freesound ID | Author | Licence | Folder | Used for |", "| --- | --- | --- | --- | --- |"]
    for e in CATALOG:
        lines.append("| [%d](%s) | %s | %s | %s | %s |" % (e[0], url(e[0], e[1]), e[1], e[3], e[4], e[5]))
    lines += ["", "CC0 sources need no credit; they are listed for provenance. Nothing here is from the BBC "
                  "Sound Effects library (non-commercial licence), the A24 film, or any game.", ""]
    with open(path, "w") as f:
        f.write(text.rstrip("\n") + "\n" + "\n".join(lines))
    print("updated", path)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"ingest": ingest, "analyze": analyze, "build": build, "credits": credits}[cmd]()
