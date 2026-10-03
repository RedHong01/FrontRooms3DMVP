"""FrontRooms FMOD system: placeholder Foley + the project spec.

    python3 fmod_frontrooms.py render   # synthesize placeholder WAVs + manifest
    python3 fmod_frontrooms.py script   # write build/fmod_build_frontrooms.js from SPEC
    python3 fmod_frontrooms.py all

Then:
    fmodstudiocl -script build/fmod_build_frontrooms.js FMOD/FrontRooms/FrontRooms.fspro

The placeholders are deliberately modular: every physical moment of an object
is its own small asset (handle, unlatch, swing loop, stop, latch strike ...),
so recorded takes can replace them one file at a time without touching the
FMOD event logic or the game code.
"""
import json
import math
import os
import random
import struct
import sys
import wave
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))            # Frontrooms3D
STAGE = os.path.join(ROOT, "AudioSource", "FMOD_Placeholders")    # rendered WAVs
BUILD = os.path.join(HERE, "build")
SR = 48000
TAU = 2 * math.pi
MANIFEST = {}


def seed_of(*parts):
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0xFFFFFFFF


# ----------------------------------------------------------------- primitives
def silence(sec):
    return [0.0] * int(round(sec * SR))


def mix(dst, src, i0=0, gain=1.0):
    for i, v in enumerate(src):
        j = i0 + i
        if 0 <= j < len(dst):
            dst[j] += gain * v
    return dst


def modal(sec, modes, rng, transient=0.003, noise_gain=0.3):
    """Sum of exponentially decaying sinusoids (freq, decay_s, amp) + a click."""
    n = int(sec * SR)
    out = [0.0] * n
    for f, d, a in modes:
        ph = rng.random() * TAU
        w = TAU * f / SR
        k = math.exp(-1.0 / (max(1e-4, d) * SR))
        e = a
        for i in range(n):
            out[i] += e * math.sin(ph + w * i)
            e *= k
            if e < 1e-5:
                break
    m = int(transient * SR)
    for i in range(min(m, n)):
        out[i] += noise_gain * (rng.random() * 2 - 1) * (1 - i / m)
    return out


class Reson:
    def __init__(self, f, q, gain=1.0):
        w = TAU * f / SR
        r = math.exp(-math.pi * (f / q) / SR)
        self.a1, self.a2, self.g = -2 * r * math.cos(w), r * r, (1 - r) * gain
        self.y1 = self.y2 = 0.0

    def __call__(self, x):
        y = self.g * x - self.a1 * self.y1 - self.a2 * self.y2
        self.y2, self.y1 = self.y1, y
        return y


def noise(n, rng):
    return [rng.random() * 2 - 1 for _ in range(n)]


def onepole_lp(sig, fc):
    a = math.exp(-TAU * fc / SR)
    y = 0.0
    out = []
    for x in sig:
        y = (1 - a) * x + a * y
        out.append(y)
    return out


def onepole_hp(sig, fc):
    lp = onepole_lp(sig, fc)
    return [x - l for x, l in zip(sig, lp)]


def band(sig, lo, hi, passes=2):
    for _ in range(passes):
        sig = onepole_hp(sig, lo)
        sig = onepole_lp(sig, hi)
    return sig


def env(sig, attack, decay, hold=0.0):
    out = []
    for i, x in enumerate(sig):
        t = i / SR
        if t < attack:
            g = t / attack if attack > 0 else 1.0
        elif t < attack + hold:
            g = 1.0
        else:
            g = math.exp(-(t - attack - hold) / decay)
        out.append(x * g)
    return out


def fade(sig, fin=0.002, fout=0.01):
    n = len(sig)
    a, b = int(fin * SR), int(fout * SR)
    for i in range(min(a, n)):
        sig[i] *= i / a
    for i in range(min(b, n)):
        sig[n - 1 - i] *= i / b
    return sig


def wrap_loop(sig, xfade_sec):
    """Fold the tail into the head so the file loops without a seam."""
    x = int(xfade_sec * SR)
    body = sig[:-x]
    for i in range(x):
        w = i / x
        body[i] = body[i] * w + sig[len(sig) - x + i] * (1 - w)
    return body


def resonate(sig, resonators):
    out = []
    for x in sig:
        out.append(sum(r(x) for r in resonators))
    return out


def write(rel, sig, peak_db=-3.0):
    path = os.path.join(STAGE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m = max(abs(v) for v in sig) or 1.0
    s = (10 ** (peak_db / 20.0)) / m
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v * s)) * 32767)) for v in sig))
    MANIFEST[rel] = round(len(sig) / SR, 4)


# ----------------------------------------------------------------- ambience
HUM_PARTIALS = {1: 1.0, 2: .55, 3: .42, 4: .30, 5: .22, 6: .20, 7: .12, 8: .10, 9: .08, 10: .05,
                11: .06, 12: .03, 13: .025, 14: .02, 15: .018, 16: .012}


def hum_loop(sec, f0, partials, drive=0.9, seed=1, air=0.0):
    """Seamless ballast hum: every partial completes whole cycles in `sec`."""
    n = int(round(sec * SR))
    f = round(f0 * sec) / sec
    rng = random.Random(seed)
    phases = {h: rng.random() * TAU for h in partials}
    out = []
    am = 2.0 / sec
    for i in range(n):
        t = i / SR
        x = sum(a * math.sin(TAU * h * f * t + phases[h]) for h, a in partials.items())
        out.append(math.tanh(drive * x) * (1 + .05 * math.sin(TAU * am * t)))
    if air:
        tail = int(.3 * SR)
        nz = onepole_lp(noise(n + tail, rng), 900)
        nz = wrap_loop(nz, .3)
        out = [o + air * z for o, z in zip(out, nz)]
    return out


def render_ambience():
    write("Ambience/amb_hum_bed_loop.wav", hum_loop(7.3, 120.0, HUM_PARTIALS, seed=11, air=.25), -9)
    write("Ambience/amb_hum_beat_loop.wav", hum_loop(7.3, 118.5, HUM_PARTIALS, seed=12), -9)
    rng = random.Random(21)
    n = int(11.1 * SR)
    a = onepole_lp(noise(n + int(.5 * SR), rng), 420)
    b = band(noise(n + int(.5 * SR), rng), 900, 3200)
    air = wrap_loop([x + .25 * y for x, y in zip(a, b)], .5)
    write("Ambience/amb_air_loop.wav", air, -12)
    bright = dict(HUM_PARTIALS)
    for h in range(17, 26):
        bright[h] = .02 if h % 2 else .012
    write("Ambience/amb_fixture_loop.wav", hum_loop(2.0, 120.0, bright, drive=1.4, seed=13, air=.08), -9)
    for v in range(3):
        rng = random.Random(100 + v)
        sig = silence(.7)
        mix(sig, modal(.08, [(2400 + 300 * v, .02, .6), (4100, .012, .4)], rng, noise_gain=.5))
        buzz = hum_loop(.5, 120.0, bright, drive=2.2, seed=200 + v)
        gate = []
        for i in range(len(buzz)):
            t = i / SR
            on = 1.0 if math.sin(TAU * (9 + 4 * v) * t + v) > -.2 else .15
            gate.append(buzz[i] * on * math.exp(-t / .35))
        mix(sig, gate, int(.03 * SR), .6)
        write("Ambience/amb_fixture_strike_%02d.wav" % (v + 1), fade(sig), -4)
    for v in range(3):
        rng = random.Random(300 + v)
        write("Ambience/amb_fixture_tick_%02d.wav" % (v + 1),
              fade(modal(.06, [(3000 + 500 * v, .008, .7), (5200, .005, .4), (900, .02, .3)], rng, noise_gain=.4)), -8)
    for v in range(2):
        rng = random.Random(400 + v)
        sig = modal(.5, [(70 + 10 * v, .09, .8), (190, .05, .3), (6200, .03, .25)], rng, transient=.006, noise_gain=.6)
        write("Ambience/amb_fixture_pop_%02d.wav" % (v + 1), fade(sig), -4)


# ----------------------------------------------------------------- doors
def door_body(level, rng):
    """Laminate slab on a steel frame: low body modes + panel modes."""
    return [(78 * (1 + .03 * rng.random()), .09 + .05 * level, .9),
            (156, .06, .45), (310, .04, .3), (620 + 60 * rng.random(), .025, .18 * (1 + level)),
            (1250, .015, .1 * (1 + 2 * level))]


def hardware_rattle(sec, rng, hits=5, gain=.3):
    sig = silence(sec)
    t = .0
    for h in range(hits):
        t += rng.uniform(.012, .045)
        mix(sig, modal(.05, [(rng.uniform(2200, 4800), .01, 1.0), (rng.uniform(5000, 7500), .006, .5)], rng,
                       noise_gain=.2), int(t * SR), gain * (1 - h / (hits + 1)))
    return sig


def render_doors():
    for v in range(3):                                   # lever handle: spring + tick
        rng = random.Random(1000 + v)
        sig = silence(.25)
        spring = env(band(noise(int(.07 * SR), rng), 1800, 4200), .004, .025)
        mix(sig, spring, 0, .5)
        mix(sig, modal(.08, [(2800 + 200 * v, .012, .8), (4600, .008, .5)], rng, noise_gain=.3), int(.05 * SR))
        mix(sig, modal(.1, [(620, .02, .4), (1300, .01, .2)], rng, noise_gain=.1), int(.09 * SR), .6)
        write("Door/door_handle_%02d.wav" % (v + 1), fade(sig), -4)
    for v in range(4):                                   # latch bolt retracts
        rng = random.Random(1100 + v)
        sig = modal(.18, [(1900 + 150 * v, .014, .9), (3100, .01, .6), (5200, .006, .3), (140, .04, .5)], rng,
                    noise_gain=.5)
        mix(sig, hardware_rattle(.18, rng, 2, .2), int(.01 * SR))
        write("Door/door_unlatch_%02d.wav" % (v + 1), fade(sig), -3)
    rng = random.Random(1200)                            # hydraulic closer + air (loop)
    n = int(2.3 * SR)
    hiss = band(noise(n, rng), 800, 2600)
    oil = onepole_lp(noise(n, rng), 260)
    write("Door/door_closer_loop.wav", wrap_loop([.7 * a + .5 * b for a, b in zip(hiss, oil)], .3), -6)
    rng = random.Random(1300)                            # stick-slip hinge creak (loop)
    n = int(2.3 * SR)
    imp = [0.0] * n
    ph = 0.0
    for i in range(n):
        rate = 160 * (1 + .06 * math.sin(TAU * .7 * i / SR)) * (1 + rng.uniform(-.05, .05))
        ph += rate / SR
        if ph >= 1:
            ph -= 1
            imp[i] = .6 + .6 * rng.random()
    creak = resonate(imp, [Reson(1650, 14), Reson(2870, 11, .6), Reson(640, 6, .8), Reson(4300, 18, .25)])
    write("Door/door_creak_loop.wav", wrap_loop(creak, .3), -6)
    for name, level, count in (("soft", .15, 2), ("med", .5, 2), ("hard", 1.0, 3)):   # hits the open stop
        for v in range(count):
            rng = random.Random(1400 + int(level * 100) + v)
            sig = modal(.6 + .3 * level, door_body(level, rng), rng, transient=.004, noise_gain=.3 + .5 * level)
            if level > .4:
                mix(sig, hardware_rattle(.4, rng, 3 + int(4 * level), .25 * level), int(.02 * SR))
            if level < .3:
                sig = onepole_lp(sig, 1800)
            write("Door/door_stop_%s_%02d.wav" % (name, v + 1), fade(sig), -3)
    for v in range(2):                                   # comes to rest mid-swing
        rng = random.Random(1500 + v)
        write("Door/door_stopmid_%02d.wav" % (v + 1),
              fade(modal(.07, [(3400 + 300 * v, .01, .6), (1700, .015, .3)], rng, noise_gain=.15)), -14)
    for name, level, count in (("soft", .2, 3), ("norm", .55, 3), ("slam", 1.0, 3)):   # latch strike
        for v in range(count):
            rng = random.Random(1600 + int(level * 100) + v)
            sig = silence(.9)
            mix(sig, modal(.12, [(2200 + 120 * v, .012, .9), (3800, .008, .6), (6100, .005, .3)], rng,
                           noise_gain=.4))
            mix(sig, modal(.8, door_body(level, rng), rng, transient=.005, noise_gain=.4 + .4 * level),
                int(.004 * SR), .4 + .8 * level)
            if level > .8:
                mix(sig, hardware_rattle(.5, rng, 7, .35), int(.03 * SR))
            write("Door/door_latch_%s_%02d.wav" % (name, v + 1), fade(sig), -3)
    for v in range(2):                                   # pressure "whump" on a fast close
        rng = random.Random(1700 + v)
        sig = env(onepole_lp(noise(int(.35 * SR), rng), 120), .01, .09)
        write("Door/door_air_whump_%02d.wav" % (v + 1), fade(sig), -6)
    for v in range(3):                                   # locked: handle rattles against the bolt
        rng = random.Random(1800 + v)
        sig = silence(.5)
        for h in range(3):
            mix(sig, modal(.12, [(2600 + 200 * h, .012, .8), (900, .02, .4), (180, .03, .5)], rng,
                           noise_gain=.4), int((.02 + .09 * h + .01 * v) * SR), 1 - .2 * h)
        write("Door/door_locked_%02d.wav" % (v + 1), fade(sig), -4)
    for v in range(3):                                   # the Relay hits the door
        rng = random.Random(1900 + v)
        sig = modal(.9, [(58 + 6 * v, .14, 1.0), (118, .09, .6), (240, .06, .4), (470, .04, .25), (930, .02, .15)],
                    rng, transient=.008, noise_gain=.8)
        write("Door/door_blow_%02d.wav" % (v + 1), fade(sig), -2)
    for v in range(2):
        rng = random.Random(2000 + v)
        write("Door/door_rattle_%02d.wav" % (v + 1), fade(hardware_rattle(.7, rng, 9, .5)), -6)
    for v in range(2):                                   # laminate / frame splitting
        rng = random.Random(2100 + v)
        sig = silence(.6)
        t = 0.0
        for h in range(14):
            t += rng.uniform(.005, .04)
            burst = env(band(noise(int(.03 * SR), rng), 1200, 7000), .0005, .006)
            mix(sig, burst, int(t * SR), rng.uniform(.4, 1.0))
        mix(sig, modal(.4, [(300, .05, .5), (780, .03, .3)], rng, noise_gain=.2), 0, .5)
        write("Door/door_split_%02d.wav" % (v + 1), fade(sig), -4)
    for v in range(2):                                   # latch rips out
        rng = random.Random(2200 + v)
        sig = silence(1.4)
        scrape = env(band(noise(int(.25 * SR), rng), 1500, 6000), .005, .08)
        mix(sig, scrape, 0, .7)
        mix(sig, modal(1.2, door_body(1.0, rng), rng, transient=.01, noise_gain=1.0), int(.03 * SR))
        mix(sig, hardware_rattle(.9, rng, 11, .5), int(.05 * SR))
        write("Door/door_break_%02d.wav" % (v + 1), fade(sig), -2)
    for v in range(2):                                   # automatic operator: relay click + motor
        rng = random.Random(2300 + v)
        sig = silence(1.25)
        mix(sig, modal(.06, [(2200, .01, .9), (110, .02, .5)], rng, noise_gain=.6))
        motor = []
        m = int(1.0 * SR)
        ph = 0.0
        for i in range(m):
            t = i / SR
            f = 110 + 60 * min(1.0, t / .3)
            ph += TAU * f / SR
            x = sum(math.sin(k * ph) / k for k in range(1, 9))
            g = min(1.0, t / .08) * min(1.0, (1.0 - t) / .2)
            motor.append(.25 * x * g)
        mix(sig, onepole_lp(motor, 1600), int(.06 * SR))
        mix(sig, modal(.06, [(1900, .01, .6), (95, .02, .4)], rng, noise_gain=.4), int(1.1 * SR), .7)
        write("Door/door_auto_operator_%02d.wav" % (v + 1), fade(sig), -4)


# ----------------------------------------------------------------- window
def render_window():
    rng = random.Random(3000)
    n = int(2.3 * SR)
    imp = [0.0] * n
    for i in range(n):
        if rng.random() < 40.0 / SR:
            imp[i] = rng.uniform(.3, 1.0)
    groan = resonate(imp, [Reson(2500, 40), Reson(3700, 35, .7), Reson(5100, 30, .5)])
    low = onepole_lp(noise(n, rng), 180)
    write("Window/window_stress_loop.wav", wrap_loop([g + .6 * l for g, l in zip(groan, low)], .3), -6)
    for v in range(3):
        rng = random.Random(3100 + v)
        sig = modal(.4, [(5200 + 400 * v, .05, .9), (7400, .03, .6), (3100, .06, .4), (9100, .02, .3)], rng,
                    transient=.002, noise_gain=1.0)
        write("Window/window_crack_%02d.wav" % (v + 1), fade(sig), -3)
    for v in range(2):
        rng = random.Random(3200 + v)
        sig = silence(2.2)
        mix(sig, env(noise(int(.5 * SR), rng), .001, .06), 0, .9)
        mix(sig, modal(.3, [(90, .06, .6), (200, .04, .3)], rng, noise_gain=.2))
        for _ in range(60):
            t = .02 + rng.random() ** 1.7 * 1.9
            mix(sig, modal(.06, [(rng.uniform(2800, 9000), rng.uniform(.006, .03), 1.0)], rng, noise_gain=.1),
                int(t * SR), rng.uniform(.05, .35))
        write("Window/window_shatter_%02d.wav" % (v + 1), fade(sig, fout=.2), -1)


# ----------------------------------------------------------------- foley
SURFACES = {
    # carpet: dull, low, damp fibre; tile: thinner pile, a little heel; metal: aluminium threshold strip
    "carpet": dict(lp=1100, click=.08, ring=[], fibre=.5),
    "tile": dict(lp=2600, click=.25, ring=[], fibre=.3),
    "metal": dict(lp=5000, click=.35, ring=[(2900, .05, .5), (4700, .04, .35), (6800, .025, .2)], fibre=.15),
}


def footstep(surface, gait, rng, heavy=False):
    s = SURFACES[surface]
    run = gait == "run"
    sec = .45 if heavy else .3
    sig = silence(sec)
    body_f = (55 if heavy else 120) * rng.uniform(.93, 1.07)
    heel = modal(sec, [(body_f, .05 if heavy else .03, 1.0), (body_f * 2.1, .02, .4),
                       (700, .01, s["click"]), (1600, .006, s["click"] * .6)], rng,
                 transient=.003, noise_gain=.3 + s["click"])
    mix(sig, heel, 0, 1.0 if run else .8)
    toe_t = .05 if run else .09
    mix(sig, modal(.15, [(body_f * 1.4, .02, .5), (900, .008, s["click"] * .7)], rng, noise_gain=.2),
        int(toe_t * SR), .45)
    fibre = env(onepole_lp(noise(int(.2 * SR), rng), s["lp"]), .002, .03 if not heavy else .06)
    mix(sig, fibre, int(.004 * SR), s["fibre"])
    for f, d, a in s["ring"]:
        mix(sig, modal(.15, [(f * rng.uniform(.98, 1.02), d, a)], rng, noise_gain=0), int(.002 * SR), .6)
    cloth = env(band(noise(int(.15 * SR), rng), 1800, 6000), .01, .04)
    mix(sig, cloth, int(.01 * SR), .06 if not heavy else .1)
    if heavy:
        sig = onepole_lp(sig, 2400)
    return fade(sig)


def scuff(surface, rng):
    s = SURFACES[surface]
    sig = env(band(noise(int(.25 * SR), rng), 300, s["lp"]), .02, .06)
    return fade(sig)


def render_foley():
    for surface in SURFACES:
        for gait in ("walk", "run"):
            for v in range(6):
                rng = random.Random(seed_of(surface, gait, v))
                write("Foley/step_%s_%s_%02d.wav" % (surface, gait, v + 1), footstep(surface, gait, rng), -3)
        for v in range(3):
            rng = random.Random(seed_of(surface, "stop", v))
            write("Foley/step_%s_stop_%02d.wav" % (surface, v + 1), scuff(surface, rng), -6)
    for v in range(4):
        rng = random.Random(4000 + v)
        sig = env(band(noise(int(.35 * SR), rng), 1500, 7000), .03, .09)
        write("Foley/cloth_%02d.wav" % (v + 1), fade(sig), -10)
    for v in range(4):
        rng = random.Random(4100 + v)
        sig = silence(.5)
        t = 0.0
        for h in range(5 + v % 2):
            t += rng.uniform(.02, .06)
            mix(sig, modal(.18, [(rng.uniform(2300, 6200), rng.uniform(.03, .07), 1.0) for _ in range(4)], rng,
                           noise_gain=.1), int(t * SR), .8 - h * .1)
        write("Foley/key_jingle_%02d.wav" % (v + 1), fade(sig), -4)


# ----------------------------------------------------------------- relay
def render_relay():
    for gait in ("walk", "run"):
        for v in range(6):
            rng = random.Random(seed_of("relay", gait, v))
            write("Relay/relay_step_%s_%02d.wav" % (gait, v + 1), footstep("carpet", gait, rng, heavy=True), -2)
    for v in range(4):
        rng = random.Random(5000 + v)
        sig = silence(.8)
        mix(sig, footstep("carpet", "walk", rng, heavy=True), 0, .8)
        drag = env(band(noise(int(.55 * SR), rng), 250, 1400), .06, .2)
        wob = [d * (1 + .5 * math.sin(TAU * 11 * i / SR)) for i, d in enumerate(drag)]
        mix(sig, wob, int(.1 * SR), .6)
        write("Relay/relay_drag_%02d.wav" % (v + 1), fade(sig), -3)
    sec = 4.0
    n = int(sec * SR)
    rng = random.Random(5100)
    out = []
    pairs = [(60.0, 1.0), (61.25, .9), (120.0, .5), (121.75, .45), (183.0, .2)]
    pairs = [(round(f * sec) / sec, a) for f, a in pairs]
    for i in range(n):
        t = i / SR
        out.append(sum(a * math.sin(TAU * f * t) for f, a in pairs))
    nz = wrap_loop(onepole_lp(noise(n + int(.3 * SR), rng), 300), .3)
    write("Relay/relay_presence_loop.wav", [o + .3 * z for o, z in zip(out, nz)], -8)
    for v in range(4):
        rng = random.Random(5200 + v)
        sig = silence(.6)
        for k, dt in enumerate((0, .21, .29)[: 2 + v % 2]):
            mix(sig, modal(.06, [(2100 + 80 * k, .01, .9), (70, .02, .5)], rng, noise_gain=.6),
                int((dt + .01 * v) * SR))
        write("Relay/relay_clicks_%02d.wav" % (v + 1), fade(sig), -4)
    rng = random.Random(5300)
    sw = silence(2.4)                                     # hunt: low swell
    for f, a in ((61.7, 1.0), (92.5, .6), (123.5, .4)):
        mix(sw, [a * math.sin(TAU * f * i / SR) * min(1.0, i / (1.6 * SR)) * min(1.0, (len(sw) - i) / (.3 * SR))
                 for i in range(len(sw))])
    write("Relay/relay_sting_hunt.wav", fade(sw), -4)
    se = silence(1.6)                                     # search: two dull pulses + a ping
    for k in range(2):
        mix(se, modal(.5, [(55, .1, 1.0), (110, .05, .4)], rng, noise_gain=.2), int(k * .45 * SR))
    mix(se, modal(1.0, [(1568, .4, .3)], rng, noise_gain=0), int(.9 * SR), .5)
    write("Relay/relay_sting_search.wav", fade(se), -4)
    ch = silence(2.0)                                     # chase: hit + metal + rise
    mix(ch, modal(1.2, [(45, .25, 1.0), (90, .15, .6), (2400, .2, .3), (3700, .15, .2)], rng, transient=.01,
                  noise_gain=1.0))
    rise = [math.sin(TAU * (200 + 400 * (i / SR) ** 2) * i / SR) * (i / (1.4 * SR)) * .3
            for i in range(int(1.4 * SR))]
    mix(ch, rise, int(.5 * SR))
    write("Relay/relay_sting_chase.wav", fade(ch, fout=.1), -1)
    lo = []                                               # lost: falling release
    m = int(1.8 * SR)
    ph = 0.0
    for i in range(m):
        t = i / SR
        f = 300 * (80 / 300) ** (t / 1.8)
        ph += TAU * f / SR
        lo.append(math.sin(ph) * math.exp(-t / .9))
    write("Relay/relay_sting_lost.wav", fade(lo), -6)


# ----------------------------------------------------------------- subjective
def breath(sec, cycles, rng, heavy=False):
    n = int(sec * SR)
    base = noise(n, rng)
    formants = [Reson(600, 6), Reson(1400, 7, .7), Reson(2600, 8, .4)] if heavy else \
        [Reson(500, 5), Reson(1500, 6, .6), Reson(2800, 8, .3)]
    shaped = resonate(base, formants)
    out = []
    period = sec / cycles
    for i in range(n):
        t = (i / SR) % period
        u = t / period
        inhale = .38
        if u < inhale:
            g = math.sin(math.pi * u / inhale) * (.7 if heavy else .5)
        else:
            g = math.sin(math.pi * (u - inhale) / (1 - inhale)) * (1.0 if heavy else .8)
        out.append(shaped[i] * g)
    return out


def heart(sec, bpm, rng):
    n = int(sec * SR)
    sig = [0.0] * n
    beat = 60.0 / bpm
    t = 0.0
    while t < sec - .01:
        mix(sig, modal(.25, [(48, .05, 1.0), (96, .03, .3)], rng, noise_gain=.05), int(t * SR))
        mix(sig, modal(.25, [(56, .04, .7), (112, .025, .2)], rng, noise_gain=.05), int((t + .28) * SR))
        t += beat
    return sig


def render_subjective():
    rng = random.Random(6000)
    write("Subjective/breath_calm_loop.wav", breath(4.0, 1, rng), -14)
    write("Subjective/breath_heavy_loop.wav", breath(2.6, 2, rng, heavy=True), -6)
    write("Subjective/heartbeat_slow_loop.wav", heart(2.0, 60, rng), -4)
    write("Subjective/heartbeat_fast_loop.wav", heart(1.0, 120, rng), -4)
    tin = [math.sin(TAU * 4186 * i / SR) * min(1.0, i / (.4 * SR)) * math.exp(-(i / SR) / 1.6)
           for i in range(int(4.0 * SR))]
    write("Subjective/tinnitus.wav", fade(tin, fout=.3), -16)


def render():
    render_ambience()
    render_doors()
    render_window()
    render_foley()
    render_relay()
    render_subjective()
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "placeholder_manifest.json"), "w") as f:
        json.dump(MANIFEST, f, indent=1, sort_keys=True)
    print("rendered", len(MANIFEST), "files to", STAGE)


# ================================================================= SPEC
def files(prefix, count, start=1):
    return ["%s_%02d.wav" % (prefix, i) for i in range(start, start + count)]


DOOR3D = dict(spatial=True, min=1.0, max=26.0, bus="Mechanism", bank="SFX")

SPEC = {
    "eventRoots": ["Ambience", "Mechanism", "Foley", "Relay", "Subjective", "Music"],
    "params": {
        # global
        "Tension": dict(min=0, max=1, isGlobal=True),
        "Zone": dict(labels=["Low", "Standard", "Tall", "Office"], isGlobal=True, initial=1),
        "Tier": dict(min=0, max=4, discrete=True, isGlobal=True),
        # local, reused across events
        "Openness": dict(min=0, max=1),
        "AngularVelocity": dict(min=0, max=1),
        "Impact": dict(min=0, max=1),
        "Damage": dict(min=0, max=1),
        "Progress": dict(min=0, max=1),
        "Level": dict(min=0, max=1, initial=1),
        "Stamina": dict(min=0, max=1, initial=1),
        "Proximity": dict(min=0, max=1),
        "Occlusion": dict(min=0, max=1),
        "Surface": dict(labels=["Carpet", "CarpetTile", "Metal"]),
        "Gait": dict(labels=["Walk", "Run", "Stop"]),
        "RelayGait": dict(labels=["Walk", "Run", "Drag"]),
        "RelayState": dict(labels=["Hunt", "Search", "Chase", "Lost"]),
        "FixtureEvent": dict(labels=["Strike", "Tick", "Pop"]),
    },
    "buses": [
        dict(name="AMB", volume=-2), dict(name="Hum", parent="AMB"), dict(name="Air", parent="AMB", volume=-4),
        dict(name="SFX"), dict(name="Foley", parent="SFX", volume=-2), dict(name="Mechanism", parent="SFX"),
        dict(name="Relay", parent="SFX"), dict(name="Subjective", volume=-2), dict(name="Music", volume=-3),
        dict(name="UI", volume=-6),
    ],
    "reverb": dict(name="Room Reverb", sends={"Foley": -14, "Mechanism": -10, "Relay": -8},
                   # decay (ms) / wet (dB) per Zone label: Low, Standard, Tall, Office
                   decay=[[0, 520], [1, 800], [2, 1650], [3, 380]],
                   wet=[[0, -12], [1, -10], [2, -6], [3, -15]]),
    "vcas": {"VCA Music": ["Music"], "VCA SFX": ["SFX", "Subjective", "UI"], "VCA Ambience": ["AMB"]},
    "banks": ["Ambience", "SFX", "Music"],
    "events": [
        # ---------------------------------------------------------- ambience
        dict(path="Ambience/HumBed", bus="Hum", bank="Ambience", params=["Tension"], ahdsr=[1500, 2000],
             note="Room-tone hum. Global Tension fades in a detuned layer (120 vs 118.5 Hz) whose beating is the danger cue.",
             tracks=[dict(name="Hum", sounds=[dict(files=["Ambience/amb_hum_bed_loop.wav"], loop=True, volume=-10)]),
                     dict(name="Beat", sounds=[dict(files=["Ambience/amb_hum_beat_loop.wav"], loop=True, volume=-10)],
                          auto=[dict(prop="volume", param="Tension", points=[[0, -60], [.35, -20], [1, -1]])])]),
        dict(path="Ambience/AirBed", bus="Air", bank="Ambience", ahdsr=[2000, 2000],
             tracks=[dict(name="Air", sounds=[dict(files=["Ambience/amb_air_loop.wav"], loop=True, volume=-12)])]),
        dict(path="Ambience/Fixture", spatial=True, min=.5, max=9.0, bus="Hum", bank="Ambience", params=["Level"],
             ahdsr=[40, 120], note="One per lit fixture near the listener. Level = the lamp's brightness this frame.",
             tracks=[dict(name="Hum", sounds=[dict(files=["Ambience/amb_fixture_loop.wav"], loop=True, volume=-8)],
                          auto=[dict(prop="volume", param="Level", points=[[0, -60], [.05, -30], [1, 0]])])]),
        dict(path="Ambience/FixtureEvent", spatial=True, min=.5, max=14.0, bus="Hum", bank="Ambience",
             params=["FixtureEvent"],
             tracks=[dict(name="Strike", sounds=[dict(files=files("Ambience/amb_fixture_strike", 3),
                                                      cond=[["FixtureEvent", "Strike"]])]),
                     dict(name="Tick", sounds=[dict(files=files("Ambience/amb_fixture_tick", 3),
                                                    cond=[["FixtureEvent", "Tick"]], volume=-4)]),
                     dict(name="Pop", sounds=[dict(files=files("Ambience/amb_fixture_pop", 2),
                                                   cond=[["FixtureEvent", "Pop"]])])]),
        # ---------------------------------------------------------- door modules
        dict(path="Mechanism/Door/Handle", **DOOR3D, max_=20.0,
             tracks=[dict(name="Handle", sounds=[dict(files=files("Door/door_handle", 3), randPitch=1)])]),
        dict(path="Mechanism/Door/Unlatch", **DOOR3D,
             tracks=[dict(name="Latch", sounds=[dict(files=files("Door/door_unlatch", 4), randPitch=1)])]),
        dict(path="Mechanism/Door/Swing", **DOOR3D, params=["AngularVelocity", "Openness"], ahdsr=[15, 120],
             note="Loop while |angular velocity| > 0. Closer hiss follows speed; the stick-slip creak only "
                  "speaks at low-to-mid speed and rises in pitch with it.",
             tracks=[dict(name="Closer", sounds=[dict(files=["Door/door_closer_loop.wav"], loop=True, volume=-4)],
                          auto=[dict(prop="volume", param="AngularVelocity",
                                     points=[[0, -80], [.04, -36], [.35, -10], [1, 0]])]),
                     dict(name="Creak", sounds=[dict(files=["Door/door_creak_loop.wav"], loop=True, volume=-6,
                                                     auto=[dict(prop="pitch", param="AngularVelocity",
                                                                points=[[0, -3], [1, 2]])])],
                          auto=[dict(prop="volume", param="AngularVelocity",
                                     points=[[0, -80], [.12, -40], [.3, -6], [.6, -4], [.85, -18], [1, -30]])])]),
        dict(path="Mechanism/Door/StopLimit", **DOOR3D, params=["Impact"],
             note="Door reaches its open limit. Impact 0-1 picks soft/medium/hard and adds +4 dB, +3 st across "
                  "the range (BeamNG-style).",
             masterAuto=[dict(prop="volume", param="Impact", points=[[0, -4], [1, 0]])],
             tracks=[dict(name="Soft", sounds=[dict(files=files("Door/door_stop_soft", 2), cond=[["Impact", 0, .33]],
                                                    auto=[dict(prop="pitch", param="Impact", points=[[0, -1.5], [1, 1.5]])])]),
                     dict(name="Medium", sounds=[dict(files=files("Door/door_stop_med", 2), cond=[["Impact", .33, .66]],
                                                      auto=[dict(prop="pitch", param="Impact", points=[[0, -1.5], [1, 1.5]])])]),
                     dict(name="Hard", sounds=[dict(files=files("Door/door_stop_hard", 3), cond=[["Impact", .66, 1]],
                                                    auto=[dict(prop="pitch", param="Impact", points=[[0, -1.5], [1, 1.5]])])])]),
        dict(path="Mechanism/Door/StopMid", **DOOR3D,
             tracks=[dict(name="Settle", sounds=[dict(files=files("Door/door_stopmid", 2), volume=-4)])]),
        dict(path="Mechanism/Door/LatchStrike", **DOOR3D, params=["Impact"],
             masterAuto=[dict(prop="volume", param="Impact", points=[[0, -4], [1, 0]])],
             tracks=[dict(name="Soft", sounds=[dict(files=files("Door/door_latch_soft", 3), cond=[["Impact", 0, .33]])]),
                     dict(name="Normal", sounds=[dict(files=files("Door/door_latch_norm", 3), cond=[["Impact", .33, .66]])]),
                     dict(name="Slam", sounds=[dict(files=files("Door/door_latch_slam", 3), cond=[["Impact", .66, 1]])]),
                     dict(name="Air", sounds=[dict(files=files("Door/door_air_whump", 2), cond=[["Impact", .6, 1]],
                                                   volume=-3)])]),
        dict(path="Mechanism/Door/Locked", **DOOR3D,
             tracks=[dict(name="Rattle", sounds=[dict(files=files("Door/door_locked", 3), randPitch=1)])]),
        dict(path="Mechanism/Door/Blow", spatial=True, min=1.0, max=36.0, bus="Mechanism", bank="SFX",
             params=["Damage"], note="One Relay blow. Damage = blow index / blows needed.",
             tracks=[dict(name="Impact", sounds=[dict(files=files("Door/door_blow", 3), randPitch=1)]),
                     dict(name="Rattle", sounds=[dict(files=files("Door/door_rattle", 2), cond=[["Damage", .3, 1]])]),
                     dict(name="Split", sounds=[dict(files=files("Door/door_split", 2), cond=[["Damage", .6, 1]])])]),
        dict(path="Mechanism/Door/Break", spatial=True, min=1.0, max=40.0, bus="Mechanism", bank="SFX",
             note="Latch rips out. The game also fires StopLimit at Impact 1 when the leaf hits the wall.",
             tracks=[dict(name="Break", sounds=[dict(files=files("Door/door_break", 2))])]),
        dict(path="Mechanism/Door/AutoOperator", **DOOR3D,
             note="Title corridor doors open themselves: operator relay + motor.",
             tracks=[dict(name="Operator", sounds=[dict(files=files("Door/door_auto_operator", 2))])]),
        # ---------------------------------------------------------- window
        dict(path="Mechanism/Window/Stress", spatial=True, min=1.0, max=22.0, bus="Mechanism", bank="SFX",
             params=["Progress"], ahdsr=[50, 150], note="While the player holds E on glass. Progress = hold 0-1.",
             tracks=[dict(name="Stress", sounds=[dict(files=["Window/window_stress_loop.wav"], loop=True, volume=-4,
                                                      auto=[dict(prop="pitch", param="Progress", points=[[0, -2], [1, 3]])])],
                          auto=[dict(prop="volume", param="Progress", points=[[0, -40], [.2, -18], [1, 0]])])]),
        dict(path="Mechanism/Window/Crack", spatial=True, min=1.0, max=28.0, bus="Mechanism", bank="SFX",
             tracks=[dict(name="Crack", sounds=[dict(files=files("Window/window_crack", 3), randPitch=1)])]),
        dict(path="Mechanism/Window/Shatter", spatial=True, min=2.0, max=50.0, bus="Mechanism", bank="SFX",
             note="The loudest noise in the game (Relay hearing radius 40 m).",
             tracks=[dict(name="Shatter", sounds=[dict(files=files("Window/window_shatter", 2))])]),
        # ---------------------------------------------------------- player foley
        dict(path="Foley/Player/Footstep", spatial=True, min=.5, max=16.0, bus="Foley", bank="SFX",
             params=["Surface", "Gait"],
             note="Fire on each foot contact (stride distance), not on a timer.",
             tracks=[dict(name="%s %s" % (s, g), sounds=[dict(
                 files=files("Foley/step_%s_%s" % ({"Carpet": "carpet", "CarpetTile": "tile", "Metal": "metal"}[s],
                                                    g.lower()), 3 if g == "Stop" else 6),
                 cond=[["Surface", s], ["Gait", g]], randPitch=1, randVol=1.5,
                 volume={"Walk": -6, "Run": -2, "Stop": -8}[g])])
                 for s in ("Carpet", "CarpetTile", "Metal") for g in ("Walk", "Run", "Stop")]),
        dict(path="Foley/Player/Cloth", spatial=True, min=.5, max=8.0, bus="Foley", bank="SFX",
             tracks=[dict(name="Cloth", sounds=[dict(files=files("Foley/cloth", 4), volume=-6, randPitch=1)])]),
        dict(path="Foley/Player/KeyPickup", bus="Foley", bank="SFX",
             note="Diegetic key ring. The motif hook (first two notes) gets layered here once the motif is chosen.",
             tracks=[dict(name="Keys", sounds=[dict(files=files("Foley/key_jingle", 4), volume=-3)])]),
        # ---------------------------------------------------------- the Relay
        dict(path="Relay/Footstep", spatial=True, min=1.5, max=42.0, rolloff=3, bus="Relay", bank="SFX",
             params=["RelayGait", "Occlusion"], occlusion=True,
             note="Driven by the rig's foot contacts. Occlusion 0-1 comes from the map path (walls/turns between).",
             tracks=[dict(name="Walk", sounds=[dict(files=files("Relay/relay_step_walk", 6), cond=[["RelayGait", "Walk"]],
                                                    randPitch=1, volume=-2)]),
                     dict(name="Run", sounds=[dict(files=files("Relay/relay_step_run", 6), cond=[["RelayGait", "Run"]],
                                                   randPitch=1)]),
                     dict(name="Drag", sounds=[dict(files=files("Relay/relay_drag", 4), cond=[["RelayGait", "Drag"]],
                                                    volume=-2)])]),
        dict(path="Relay/Presence", spatial=True, min=2.0, max=30.0, bus="Relay", bank="SFX",
             params=["Proximity", "Occlusion"], occlusion=True, ahdsr=[800, 1500],
             tracks=[dict(name="Drone", sounds=[dict(files=["Relay/relay_presence_loop.wav"], loop=True, volume=-6)],
                          auto=[dict(prop="volume", param="Proximity", points=[[0, -50], [.5, -14], [1, 0]])])]),
        dict(path="Relay/Clicks", spatial=True, min=1.0, max=30.0, bus="Relay", bank="SFX",
             tracks=[dict(name="Clicks", sounds=[dict(files=files("Relay/relay_clicks", 4))])]),
        dict(path="Relay/Stinger", bus="Music", bank="SFX", params=["RelayState"],
             note="State-change tells. Placeholders until the motif is chosen (Relay = inverted motif).",
             tracks=[dict(name=s, sounds=[dict(files=["Relay/relay_sting_%s.wav" % s.lower()], cond=[["RelayState", s]])])
                     for s in ("Hunt", "Search", "Chase", "Lost")]),
        # ---------------------------------------------------------- subjective
        dict(path="Subjective/Breath", bus="Subjective", bank="SFX", params=["Stamina"], ahdsr=[300, 600],
             tracks=[dict(name="Calm", sounds=[dict(files=["Subjective/breath_calm_loop.wav"], loop=True, volume=-8)],
                          auto=[dict(prop="volume", param="Stamina", points=[[0, -60], [.5, -18], [1, -8]])]),
                     dict(name="Heavy", sounds=[dict(files=["Subjective/breath_heavy_loop.wav"], loop=True, volume=-4)],
                          auto=[dict(prop="volume", param="Stamina", points=[[0, 0], [.4, -10], [.7, -60], [1, -80]])])]),
        dict(path="Subjective/Heartbeat", bus="Subjective", bank="SFX", params=["Proximity"], ahdsr=[500, 800],
             note="Only while the Relay is close but unseen.",
             tracks=[dict(name="Slow", sounds=[dict(files=["Subjective/heartbeat_slow_loop.wav"], loop=True, volume=-6)],
                          auto=[dict(prop="volume", param="Proximity",
                                     points=[[0, -80], [.3, -18], [.6, -12], [.8, -40], [1, -80]])]),
                     dict(name="Fast", sounds=[dict(files=["Subjective/heartbeat_fast_loop.wav"], loop=True, volume=-4)],
                          auto=[dict(prop="volume", param="Proximity", points=[[0, -80], [.55, -40], [.8, -8], [1, -2]])])]),
        dict(path="Subjective/Tinnitus", bus="Subjective", bank="SFX",
             tracks=[dict(name="Ring", sounds=[dict(files=["Subjective/tinnitus.wav"], volume=-6)])]),
        # ---------------------------------------------------------- music
        dict(path="Music/Title", bus="Music", bank="Music",
             markers=dict(region=[0, 20.8696, "Title loop (2 rooms, 8 bars @ 92 BPM)"],
                          named=[["Room A", 0], ["Room B", 10.4348]], tempo=92),
             note="92 BPM, 4/4, one title room = 4 bars = 10.4348 s. Drop the chosen motif stems "
                  "(AudioSource/Logic) on tracks here; doors land on bar lines."),
    ],
}


def write_script():
    with open(os.path.join(BUILD, "placeholder_manifest.json")) as f:
        manifest = json.load(f)
    for e in SPEC["events"]:                                    # normalise the DOOR3D override helper
        if "max_" in e:
            e["max"] = e.pop("max_")
    spec = dict(SPEC, stage=STAGE.replace("\\", "/") + "/", durations=manifest)
    missing = [fn for e in SPEC["events"] for t in e.get("tracks", []) for s in t["sounds"] for fn in s["files"]
               if fn not in manifest]
    if missing:
        raise SystemExit("spec references files that were not rendered: %s" % missing[:5])
    with open(os.path.join(HERE, "fmod_builder.js")) as f:
        builder = f.read()
    out = os.path.join(BUILD, "fmod_build_frontrooms.js")
    with open(out, "w") as f:
        f.write("// GENERATED by fmod_frontrooms.py - edit SPEC there, not here.\n")
        f.write("var SPEC = " + json.dumps(spec) + ";\n")
        f.write(builder)
    print("wrote", out, "with", len(SPEC["events"]), "events")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("render", "all"):
        render()
    if cmd in ("script", "all"):
        write_script()
