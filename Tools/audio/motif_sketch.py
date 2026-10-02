"""FrontRooms motif sketches. Pure standard library (no numpy).

Every pitched element is a partial of the 120 Hz ballast hum, so the motif
lives inside the hum instead of on top of it.  Tempo: 92 BPM, which is exactly
one title room (12 m / 1.15 m/s = 10.4348 s = 16 beats).
"""
import math, random, struct, sys, wave, os

SR = 44100
BPM = 92.0
BEAT = 60.0 / BPM
ROOM = 16 * BEAT
HUM = 120.0
P = lambda n, base=HUM / 2: n * base          # harmonic n of 60 Hz grid (8 -> 480 Hz)


class Buf:
    def __init__(self, seconds, wrap=False):
        self.n = int(round(seconds * SR))
        self.d = [0.0] * self.n
        self.wrap = wrap

    def add(self, i, v):
        if self.wrap:
            self.d[i % self.n] += v
        elif 0 <= i < self.n:
            self.d[i] += v


def resonator(freq, q):
    w = 2 * math.pi * freq / SR
    r = math.exp(-math.pi * (freq / q) / SR)
    a1, a2 = -2 * r * math.cos(w), r * r
    state = [0.0, 0.0]

    def step(x):
        y = (1 - r) * x - a1 * state[0] - a2 * state[1]
        state[1], state[0] = state[0], y
        return y
    return step


# ---------------------------------------------------------------- beds
def hum(buf, gain, env=lambda t: 1.0, loop=False):
    T = 2048
    amps = {1: 1.0, 2: .55, 3: .42, 4: .30, 5: .22, 6: .20, 7: .12, 8: .10, 9: .08,
            10: .05, 11: .06, 12: .03, 13: .025, 14: .02, 15: .018, 16: .012}
    table = []
    for k in range(T):
        x = sum(a * math.sin(2 * math.pi * h * k / T + h * .7) for h, a in amps.items())
        table.append(math.tanh(.9 * x))
    m = max(abs(v) for v in table)
    table = [v / m for v in table]
    L = buf.n / SR
    if loop:
        c = round(HUM * L)
        freqs = [c / L, (c + 1) / L, (c - 2) / L]
        am = 2 / L
    else:
        freqs = [HUM, HUM + .05, HUM - .09]
        am = .1
    gains, phases = [1.0, .6, .45], [0.0, .33, .71]
    for i in range(buf.n):
        t = i / SR
        v = 0.0
        for f, g, p in zip(freqs, gains, phases):
            pos = ((f * t + p) % 1.0) * T
            j = int(pos)
            fr = pos - j
            a = table[j]
            v += g * (a + (table[(j + 1) % T] - a) * fr)
        buf.d[i] += gain * env(t) * v * (1 + .06 * math.sin(2 * math.pi * am * t)) / 2.05


def air(buf, gain, cut=600, loop=False, seed=3):
    rnd = random.Random(seed)
    a = math.exp(-2 * math.pi * cut / SR)
    extra = int(.5 * SR) if loop else 0
    n = buf.n + extra
    y1 = y2 = 0.0
    out = [0.0] * n
    for i in range(n):
        y1 = (1 - a) * rnd.uniform(-1, 1) + a * y1
        y2 = (1 - a) * y1 + a * y2
        out[i] = y2
    rms = math.sqrt(sum(v * v for v in out) / n) or 1
    if loop:
        for k in range(extra):
            w = k / extra
            out[k] = out[k] * w + out[buf.n + k] * (1 - w)
    for i in range(buf.n):
        buf.d[i] += gain * out[i] / rms


# ---------------------------------------------------------------- voices
def tone(buf, t0, f, dur, gain, attack=.04, decay=1.4, ripple=.3, detune=0.0, glide_to=None, glide_time=0):
    i0 = int(t0 * SR)
    n = int(dur * SR)
    ph = ph2 = 0.0
    for k in range(n):
        t = k / SR
        ff = f
        if glide_to:
            u = min(1.0, t / glide_time)
            ff = f * (glide_to / f) ** (u * u)
        ph += 2 * math.pi * ff / SR
        ph2 += 2 * math.pi * (ff + detune) / SR
        env = min(1.0, t / attack) * math.exp(-t / decay)
        if k > n - 2205:
            env *= (n - k) / 2205
        # 120 Hz ripple: the note is "made of" the mains, it buzzes like the hum
        env *= 1 - ripple * (.5 + .5 * math.cos(2 * math.pi * HUM * t))
        s = math.sin(ph) + .16 * math.sin(2 * ph + .3) + .05 * math.sin(3 * ph)
        if detune:
            s = .55 * s + .45 * math.sin(ph2)
        buf.add(i0 + k, gain * env * s)


def click(buf, t0, gain, f=1800, thunk=90, seed=0, length=.08):
    rnd = random.Random(seed)
    i0 = int(t0 * SR)
    for k in range(int(length * SR)):
        t = k / SR
        v = rnd.uniform(-1, 1) * (1 - t / .003) if t < .003 else 0.0
        v += .6 * math.sin(2 * math.pi * f * t) * math.exp(-t / .012)
        v += .5 * math.sin(2 * math.pi * thunk * t) * math.exp(-t / .03)
        buf.add(i0 + k, gain * v)


def swing(buf, t0, dur, gain, creak_from, creak_to, seed=7, closer=.5, stop=.35):
    """Door swing driven by its own motion curve.

    The door angle follows smoothstep(u); everything here reads the angular
    velocity of that same curve, so the sound cannot outlast the motion.
    Creak = stick-slip: impulses whose rate (the perceived pitch) glides
    from creak_from to creak_to, exciting door-panel resonances.
    """
    rnd = random.Random(seed)
    i0 = int(t0 * SR)
    n = int(dur * SR)
    rs = [resonator(1650, 14), resonator(2870, 11), resonator(640, 6)]
    hp_prev = lp = 0.0
    phase = 0.0
    for k in range(n + int(.25 * SR)):
        u = k / n
        vel = 6 * u * (1 - u) / 1.5 if u < 1 else 0.0     # normalised |dθ/dt|, peak 1
        # hydraulic closer + air: band-limited noise following velocity
        x = rnd.uniform(-1, 1)
        hp = x - hp_prev
        hp_prev = x
        lp = .82 * lp + .18 * hp
        out = closer * vel * lp
        # stick-slip creak
        imp = 0.0
        if vel > .3 and u < 1:
            rate = creak_from * (creak_to / creak_from) ** min(1.0, u / .5)
            phase += rate * (1 + rnd.uniform(-.04, .04)) / SR
            if phase >= 1:
                phase -= 1
                imp = (vel - .3) * (.7 + .6 * rnd.random())
        cr = rs[0](imp) * 1.0 + rs[1](imp) * .6 + rs[2](imp) * .8
        out += 12.0 * cr
        buf.add(i0 + k, gain * out)
    # end stop: soft backcheck (smoothstep arrives at ~zero velocity)
    click(buf, t0 + dur, gain * stop, f=420, thunk=68, seed=seed + 1, length=.12)


def jingle(buf, t0, gain, seed=11):
    rnd = random.Random(seed)
    for h in range(5):
        th = t0 + h * rnd.uniform(.025, .06)
        parts = [rnd.uniform(2300, 6200) for _ in range(4)]
        i0 = int(th * SR)
        for k in range(int(.18 * SR)):
            t = k / SR
            v = sum(math.sin(2 * math.pi * p * t) * math.exp(-t / rnd.uniform(.03, .07)) for p in parts) / 4
            buf.add(i0 + k, gain * (.8 - h * .12) * v)


def glass(buf, t0, gain, seed=21):
    rnd = random.Random(seed)
    i0 = int(t0 * SR)
    for k in range(int(.5 * SR)):
        t = k / SR
        buf.add(i0 + k, gain * rnd.uniform(-1, 1) * math.exp(-t / .07))
    for f in (P(8) * 4, P(9) * 4, P(11) * 4):          # the motif, shattered
        tone(buf, t0, f, 2.2, gain * .22, attack=.002, decay=.5, ripple=0)
    for _ in range(26):                                  # debris
        th = t0 + .05 + rnd.random() ** 1.6 * 1.4
        tone(buf, th, rnd.uniform(3000, 7500), .12, gain * .1 * rnd.random(), attack=.001, decay=.025, ripple=0)


def tick(buf, t0, gain, accent=False):
    click(buf, t0, gain * (1.0 if accent else .6), f=2600 if accent else 3100, thunk=140, length=.04)


# ---------------------------------------------------------------- pieces
def title_door(buf, t0, third, gain=1.0):
    """Automatic double door as the motif's instrument.
    beat 0: operator relay click + note 1 · +1/8: maglock release + note 2,
    swing begins · +1/4: note 3 lands at peak swing velocity."""
    click(buf, t0, .35 * gain, f=2200, thunk=110, seed=31)
    tone(buf, t0, P(8), 3.0, .16 * gain, decay=1.1)
    click(buf, t0 + BEAT / 2, .30 * gain, f=900, thunk=60, seed=32, length=.12)
    tone(buf, t0 + BEAT / 2, P(9), 3.0, .15 * gain, decay=1.1)
    swing(buf, t0 + BEAT / 2, .9, .22 * gain, P(9) / 2, third / 2, seed=33)
    swing(buf, t0 + BEAT / 2 + .03, .9, .16 * gain, P(9) / 2 * 1.01, third / 2 * 1.01, seed=34)  # second leaf
    tone(buf, t0 + BEAT, third, 4.5, .19 * gain, attack=.09, decay=2.2)


def loop_a(path):
    buf = Buf(2 * ROOM, wrap=True)
    hum(buf, .22, loop=True)
    air(buf, .035, loop=True)
    first = 2 * BEAT
    for bar in range(8):
        for b in (0, 2):
            tick(buf, bar * 4 * BEAT + b * BEAT, .05, accent=(b == 0))
    title_door(buf, first, P(11))                 # statement: rises into the gap between notes
    title_door(buf, first + ROOM, P(7))           # answer: falls to the natural seventh
    write(buf, path)


def loop_b(path):
    """Alternative: no melody. The motif is a rhythm (3-3-2) that the
    failing ballast plays by gating the hum, with relay ticks on the hits."""
    pattern = [0, 3, 6]                            # eighth-note hits in each bar
    hits = []
    for bar in range(8):
        for e in pattern:
            hits.append(bar * 4 * BEAT + e * BEAT / 2)

    n = int(round(2 * ROOM * SR))
    gate_arr = [1.0] * n
    for h in hits:
        i0 = int(h * SR)
        for k in range(int(.09 * SR)):
            i = (i0 + k) % n
            gate_arr[i] = min(gate_arr[i], .25 + .75 * k / (.09 * SR))
    gate = lambda t: gate_arr[min(n - 1, int(t * SR))]
    buf = Buf(2 * ROOM, wrap=True)
    hum(buf, .24, env=gate, loop=True)
    air(buf, .035, loop=True)
    for i, h in enumerate(hits):
        tick(buf, h, .07, accent=(i % 3 == 0))
    for r in range(2):
        t0 = 2 * BEAT + r * ROOM
        click(buf, t0, .3, f=900, thunk=60, seed=40 + r, length=.12)
        swing(buf, t0 + .04, .9, .22, 300, 300 * 1.12, seed=50 + r)
    write(buf, path)


def family(path):
    dur = 21.5
    cut = 16.35

    def env(t):
        if t >= cut:
            return 0.0
        if 8.0 <= t < 8.35:
            return .25 + .75 * (t - 8.0) / .35
        return 1.0
    buf = Buf(dur)
    hum(buf, .16, env=env)
    air(buf, .025)
    # 1. player door: handle, latch, 0.55 s swing; the creak glides 9 -> 11
    click(buf, .6, .3, f=1500, thunk=95, seed=1)
    click(buf, .7, .35, f=1050, thunk=80, seed=2)
    swing(buf, .78, .55, .3, P(9) / 2, P(11) / 2, seed=3)
    # 2. key pickup: notes 1-2 only, the third is withheld
    jingle(buf, 3.0, .18)
    tone(buf, 3.02, P(8) * 2, 1.4, .09, attack=.004, decay=.5, ripple=.1)
    tone(buf, 3.02 + BEAT / 2, P(9) * 2, 1.6, .09, attack=.004, decay=.6, ripple=.1)
    # 3. door you hold the key for: the third note lands at peak swing
    click(buf, 5.0, .3, f=1500, thunk=95, seed=4)
    click(buf, 5.1, .35, f=1050, thunk=80, seed=5)
    swing(buf, 5.18, .55, .3, P(9) / 2, P(11) / 2, seed=6)
    tone(buf, 5.18 + .27, P(11), 3.0, .17, attack=.06, decay=1.6)
    # 4. the Relay: hum drops out, relay clicks, inverted motif low and beating
    for i, dt in enumerate((0, .21, .29)):
        click(buf, 8.0 + dt, .28, f=2100, thunk=70, seed=60 + i)
    tone(buf, 8.35, P(11) / 2, 1.3, .2, attack=.2, decay=1.4, detune=1.4)
    tone(buf, 8.35 + BEAT, P(9) / 2, 1.3, .2, attack=.2, decay=1.4, detune=1.4)
    tone(buf, 8.35 + 2 * BEAT, P(8) / 2, 2.6, .22, attack=.2, decay=1.8, detune=1.4)
    # 5. glass: the motif shattered into glass partials
    glass(buf, 12.4, .5)
    # 6. caught: all three notes collapse into the hum, hard cut, then tinnitus
    for f in (P(8), P(9), P(11)):
        tone(buf, 15.4, f, cut - 15.4, .14, attack=.15, decay=5, glide_to=HUM, glide_time=.9, detune=.8)
    for i in range(int(cut * SR), buf.n):          # hard cut: everything, beds included
        buf.d[i] = 0.0
    tone(buf, cut + .9, 4186.0, 3.0, .012, attack=.4, decay=1.4, ripple=0)
    write(buf, path)


def write(buf, path):
    peak = max(abs(v) for v in buf.d) or 1
    scale = .89 / peak
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * scale)) * 32767)) for v in buf.d))
    print("wrote", path, round(buf.n / SR, 3), "s")


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    if which in ("all", "a"):
        loop_a(os.path.join(out, "01_title_loop_A_threshold_motif.wav"))
    if which in ("all", "f"):
        family(os.path.join(out, "02_motif_family_in_foley.wav"))
    if which in ("all", "b"):
        loop_b(os.path.join(out, "03_title_loop_B_rhythm_only.wav"))
