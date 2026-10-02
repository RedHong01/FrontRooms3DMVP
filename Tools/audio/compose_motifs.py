"""FrontRooms motif candidates for Logic Pro.

Writes one multitrack Standard MIDI File (one track per instrument, with
markers, tempo, key and GM programs) plus two placeholder audio stems that line
up with it from bar 1: the 120 Hz ballast hum and the door/Foley layer.

Tempo is 92 BPM: one title room (12 m at 1.15 m/s = 10.4348 s) is exactly
four bars, so every room's door lands on a downbeat.

    python3 compose_motifs.py <out_dir>

Layout (bars):
  M1 ATTENTION   1-8 loop, 9 door, 10 key, 12-13 unlocked, 15-16 relay, 18 caught
  M2 ENDLESS    21-28 loop, 29 door, 30 key, 32-33 unlocked, 35-36 relay, 38 caught
  M3 RELAY      41-48 loop, 49 door, 50 key, 52-53 unlocked, 55-56 relay, 58 caught
"""
import math
import os
import random
import struct
import sys
import wave

PPQ = 480
BPM = 92.0
BAR = 4 * PPQ
SEC_PER_BEAT = 60.0 / BPM
TOTAL_BARS = 60
SR = 48000

NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def n(name):
    """'C#4' -> 61 (C4 = 60)."""
    pc = NAMES[name[0]]
    i = 1
    while i < len(name) and name[i] in "#b":
        pc += 1 if name[i] == "#" else -1
        i += 1
    return pc + 12 * (int(name[i:]) + 1)


def tick(bar, beat=1.0):
    return int(round(((bar - 1) * 4 + (beat - 1)) * PPQ))


class Track:
    def __init__(self, name, channel, program=None, humanize=0, seed=0):
        self.name, self.ch, self.program = name, channel, program
        self.events = []          # (tick, order, bytes)
        self.rng = random.Random(seed)
        self.hum = humanize

    def note(self, bar, beat, beats, pitch, vel, jitter=True):
        p = n(pitch) if isinstance(pitch, str) else pitch
        t = tick(bar, beat)
        if jitter and self.hum:
            t = max(0, t + self.rng.randint(-self.hum, self.hum))
            vel = max(1, min(127, vel + self.rng.randint(-4, 4)))
        end = t + max(10, int(beats * PPQ))
        self.events.append((t, 1, bytes([0x90 | self.ch, p, vel])))
        self.events.append((end, 0, bytes([0x80 | self.ch, p, 0])))

    def chord(self, bar, beat, beats, pitches, vel, strum=0):
        for i, p in enumerate(pitches):
            self.note(bar, beat + i * strum / PPQ, beats, p, vel - i)

    def cc(self, bar, beat, num, val):
        self.events.append((tick(bar, beat), 0, bytes([0xB0 | self.ch, num, val])))

    def bend(self, bar, beat, semis):
        """Pitch bend, assuming the default +/-2 semitone range."""
        v = max(0, min(16383, int(8192 + semis / 2.0 * 8191)))
        self.events.append((tick(bar, beat), 0, bytes([0xE0 | self.ch, v & 0x7F, v >> 7])))

    def bend_ramp(self, bar, beat, beats, frm, to, steps=24):
        for i in range(steps + 1):
            u = i / steps
            self.bend(bar, beat + beats * u, frm + (to - frm) * u * u)


def vlq(x):
    out = [x & 0x7F]
    x >>= 7
    while x:
        out.append((x & 0x7F) | 0x80)
        x >>= 7
    return bytes(reversed(out))


def meta(kind, data):
    return bytes([0xFF, kind]) + vlq(len(data)) + data


def chunk(events, name, program=None, ch=0):
    body = bytearray(vlq(0) + meta(0x03, name.encode("ascii")))
    if program is not None:
        body += vlq(0) + bytes([0xC0 | ch, program])
    last = 0
    for t, _, data in sorted(events, key=lambda e: (e[0], e[1])):
        body += vlq(t - last) + data
        last = t
    body += vlq(0) + meta(0x2F, b"")
    return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)


# --------------------------------------------------------------------------
# Tracks
T = {}


def track(key, name, ch, program, humanize=6, seed=1):
    T[key] = Track(name, ch, program, humanize, seed)
    return T[key]


chime = track("chime", "M1 PA Chime", 0, 14, 0)
rhodes = track("rhodes", "M1 Lobby Rhodes", 1, 4, 8, 2)
bass1 = track("bass1", "M1 Lobby Bass", 2, 33, 5, 3)
vibes = track("vibes", "M1 Vibes Lead", 3, 10, 6, 4)
pad1 = track("pad1", "M1 Strings Pad", 4, 50, 0)
kit1 = track("kit1", "M1 Lounge Kit", 9, None, 4, 5)
piano = track("piano", "M2 Felt Piano", 5, 0, 7, 6)
str2 = track("str2", "M2 Synth Strings", 6, 92, 0)
riser = track("riser", "M2 Endless Air", 7, 97, 0)
pulse2 = track("pulse2", "M2 Pulse", 8, 38, 0)
glass = track("glass", "M2 Glass Bells", 10, 5, 3, 7)
arp = track("arp", "M3 Relay Arp", 11, 82, 0)
bass3 = track("bass3", "M3 Bass Pulse", 12, 38, 0)
lead3 = track("lead3", "M3 Lead", 13, 83, 0)
pad3 = track("pad3", "M3 Dark Pad", 14, 89, 0)
kit3 = track("kit3", "M3 Drums", 9, None, 3, 8)

KICK, SIDE, SNARE, CLAP, HH, PHH, OHH, RIDE = 36, 37, 38, 39, 42, 44, 46, 51
DOORS, KEYS, RELAYS, CAUGHTS = [], [], [], []
MARKERS = []

# ==========================================================================
# M1 ATTENTION — the building's PA chime over lobby muzak (B major).
# Four bells ask 1-5-3-2; the door answers on the downbeat where the
# tonic should be. Every other room the last bell is a semitone flat.
# ==========================================================================
B0 = 0
MARKERS += [(1, "M1 ATTENTION - title loop bars 1-8"), (10, "M1 cue KEY"), (12, "M1 cue UNLOCKED"),
            (15, "M1 cue RELAY"), (18, "M1 cue CAUGHT")]

CH1 = {  # rootless lounge voicings, voice-led
    1: ["D#3", "F#3", "A#3", "C#4"],   # Bmaj9
    2: ["D#3", "F#3", "A#3", "B3"],    # G#m9
    3: ["D#3", "F#3", "G#3", "B3"],    # Emaj9
    4: ["E3", "G#3", "B3", "D#4"],     # F#13sus4  (chime)
    5: ["D#3", "F#3", "A#3", "C#4"],   # Bmaj9
    6: ["D3", "F#3", "A3", "B3"],      # Gmaj9  (bVI: the room slips)
    7: ["D3", "F#3", "G3", "B3"],      # Em9    (iv minor)
    8: ["E3", "A#3", "C4", "D#4"],     # F#13#11 (wrong chime)
}
BASS1 = {1: ("B1", "F#2"), 2: ("G#1", "D#2"), 3: ("E2", "B1"), 4: ("F#1", None),
         5: ("B1", "F#2"), 6: ("G1", "D2"), 7: ("E2", "B1"), 8: ("F#1", "C2")}

for bar in range(1, 9):
    v = CH1[bar]
    if bar in (4, 8):
        rhodes.chord(bar, 1, 3.8, v, 46, strum=10)
    else:
        rhodes.chord(bar, 1, 1.4, v, 60, strum=8)
        rhodes.chord(bar, 2.5, 2.3, v, 54, strum=8)
    root, fifth = BASS1[bar]
    if fifth:
        bass1.note(bar, 1, 1.9, root, 78)
        bass1.note(bar, 3, 1.9, fifth, 70)
    else:
        bass1.note(bar, 1, 3.9, root, 74)
    if bar in (4, 8):
        kit1.note(bar, 2, .25, PHH, 34)
        kit1.note(bar, 4, .25, PHH, 34)
    else:
        for e in range(8):
            kit1.note(bar, 1 + e * .5, .25, HH, 40 if e % 2 == 0 else 27)
        kit1.note(bar, 1, .5, KICK, 58)
        kit1.note(bar, 3, .5, KICK, 44)
        kit1.note(bar, 2, .25, SIDE, 40)
        kit1.note(bar, 4, .25, SIDE, 52)

# The chime: bar 4 asks, bar 8 asks with the wrong last bell.
for bar, last in ((4, "C#5"), (8, "C5")):
    for i, (p, vel) in enumerate((("B4", 86), ("F#5", 82), ("D#5", 84), (last, 92))):
        chime.note(bar, 1 + i, 2.6 if i == 3 else 1.9, p, vel)

# Vibes: a lounge line; room two sings the chime in augmentation.
for bar, beat, dur, p, vel in [
        (1, 3, .9, "F#4", 60), (1, 4, .9, "A#4", 62),
        (2, 1, 2.9, "B4", 66), (2, 4, .9, "A#4", 58),
        (3, 1, 1.9, "G#4", 62), (3, 3, .9, "F#4", 58), (3, 4, .9, "D#4", 56),
        (5, 1, 1.9, "B4", 66), (5, 3, 1.9, "F#5", 68),
        (6, 1, 1.9, "D5", 66), (6, 3, 1.9, "C#5", 62),
        (7, 1, 2.9, "B4", 62), (7, 4, .9, "G4", 58)]:
    vibes.note(bar, beat, dur, p, vel)

for bar, notes in ((5, ["D#4", "A#4"]), (6, ["D4", "A4"]), (7, ["D4", "G4"]), (8, ["C4", "E4"])):
    pad1.chord(bar, 1, 3.95, notes, 52 + (bar - 5) * 4)

DOORS += [(1, "auto"), (5, "auto"), (9, "auto")]

# Cue KEY (bar 10): the first two bells only, small and high. The rest is withheld.
chime.note(10, 1, 1.2, "B5", 74)
chime.note(10, 1.5, 1.8, "F#6", 80)
KEYS.append(10)

# Cue UNLOCKED (bars 12-13): the chime finally resolves and the door opens on the tonic.
for i, p in enumerate(("B4", "F#5", "D#5", "C#5")):
    chime.note(12, 1 + i, 1.9, p, 84)
chime.chord(13, 1, 3.9, ["B4", "B5"], 96)
rhodes.chord(13, 1, 3.9, CH1[1], 58, strum=10)
bass1.note(13, 1, 3.9, "B1", 74)
DOORS.append((13, "player"))

# Cue RELAY (bars 15-16): the chime played wrong, low and slow, sagging like tape.
for i, (p, beat) in enumerate((("B3", 1), ("F#4", 3))):
    chime.note(15, beat, 1.9, p, 70)
    chime.bend_ramp(15, beat, 1.9, 0, -.6)
for i, (p, beat) in enumerate((("D4", 1), ("C4", 3))):
    chime.note(16, beat, 1.9, p, 72)
    chime.bend_ramp(16, beat, 1.9, 0, -.6)
chime.bend(17, 1, 0)
bass1.note(15, 1, 7.9, "C2", 52)
pad1.chord(15, 1, 7.9, ["B3", "C4"], 44)
RELAYS.append(15)

# Cue CAUGHT (bar 18): every bell at once, falling.
chime.chord(18, 1, 1.6, ["B3", "B4", "C5", "D5", "F#5"], 118)
chime.bend_ramp(18, 1, 1.5, 0, -2, steps=30)
chime.bend(19, 1, 0)
rhodes.chord(18, 1, 1.5, ["B2", "C3", "F3", "B3"], 96)
CAUGHTS.append(18)

# ==========================================================================
# M2 ENDLESS — felt piano over the hum's B pedal (B minor).
# 5 up a minor sixth to 3, sigh down to 2. Each half-room the top climbs a
# step; the bass never moves. The loop drops back to where it started.
# ==========================================================================
B0 = 20
MARKERS += [(21, "M2 ENDLESS - title loop bars 21-28"), (30, "M2 cue KEY"), (32, "M2 cue UNLOCKED"),
            (35, "M2 cue RELAY"), (38, "M2 cue CAUGHT")]

LH = {
    1: ["B2", "F#3", "D4", "F#3", "B3", "F#3", "D4", "F#3"],
    2: ["B2", "F#3", "C#4", "F#3", "B3", "F#3", "C#4", "F#3"],
    3: ["B2", "G3", "D4", "G3", "B3", "G3", "D4", "G3"],
    4: ["B2", "G3", "E4", "G3", "B3", "G3", "D4", "G3"],
    5: ["B2", "G3", "E4", "G3", "B3", "G3", "E4", "G3"],
    6: ["B2", "G3", "F#4", "G3", "B3", "G3", "E4", "G3"],
    7: ["B2", "E3", "C#4", "E3", "B3", "E3", "C#4", "E3"],
    8: ["B2", "E3", "A#3", "C#4", "E4", "C#4", "A#3", "E3"],
}
RH = {  # (beat, beats, pitch, vel)
    1: [(1, 1, "F#4", 50), (2, 3, "D5", 60)],
    2: [(1, 4, "C#5", 54)],
    3: [(1, 1, "F#4", 52), (2, 3, "E5", 63)],
    4: [(1, 4, "D5", 56)],
    5: [(1, 1, "F#4", 54), (2, 3, "F#5", 66)],
    6: [(1, 4, "E5", 58)],
    7: [(1, 1, "F#4", 56), (2, 3, "G5", 70)],
    8: [(1, 2, "F#5", 60), (3, 2, "A#4", 50)],
}
STR2 = {1: ["B3", "D4", "F#4"], 2: ["B3", "D4", "F#4"], 3: ["B3", "D4", "G4"], 4: ["B3", "D4", "G4"],
        5: ["B3", "E4", "G4"], 6: ["B3", "E4", "G4"], 7: ["B3", "C#4", "E4", "F#4"], 8: ["A#3", "E4", "F#4"]}

for r in range(1, 9):
    bar = B0 + r
    for e, p in enumerate(LH[r]):
        piano.note(bar, 1 + e * .5, .55, p, 46 if e == 0 else 36)
    for beat, beats, p, vel in RH[r]:
        piano.note(bar, beat, beats - .05, p, vel)
    piano.cc(bar, 1.06, 64, 127)
    piano.cc(bar, 4.95, 64, 0)
    str2.chord(bar, 1, 3.98, STR2[r], 40 + r * 3)
    if r >= 3:
        for q in range(4):
            pulse2.note(bar, 1 + q, .3, "B1", 62 if q == 0 else 42)
for r, p in ((5, "B5"), (6, "B5"), (7, "A#5"), (8, "A#5")):
    str2.note(B0 + r, 1, 3.98, p, 44 + r * 2)
riser.note(B0 + 1, 1, 31.9, "B3", 72)
for r, p in ((2, "C#6"), (4, "D6"), (6, "E6"), (8, "F#6")):
    glass.note(B0 + r, 3, 2, p, 46 + r)
DOORS += [(21, "auto"), (25, "auto"), (29, "auto")]

# Cue KEY (bar 30): only the leap, high.
piano.note(30, 1, .5, "F#5", 58)
piano.note(30, 1.5, 2, "D6", 64)
glass.note(30, 1.5, 2.5, "D7", 50)
KEYS.append(30)

# Cue UNLOCKED (bars 32-33): the sigh finally reaches the tonic.
for beat, beats, p, vel in ((1, 1, "F#4", 52), (2, 2, "D5", 62), (4, 1, "C#5", 58)):
    piano.note(32, beat, beats - .05, p, vel)
piano.chord(33, 1, 3.9, ["B2", "F#3", "B3", "D4", "B4"], 58)
piano.cc(32, 1.05, 64, 127)
piano.cc(33, 4.9, 64, 0)
str2.chord(33, 1, 3.95, ["B3", "D4", "F#4", "B4"], 52)
DOORS.append((33, "player"))

# Cue RELAY (bars 35-36): the motif inverted, low: down a minor sixth, up a half step.
str2.note(35, 1, 1.95, "F#3", 64)
str2.note(35, 3, 1.95, "A#2", 66)
str2.note(36, 1, 3.95, "B2", 68)
str2.chord(35, 1, 7.9, ["B1", "C2"], 50)
piano.chord(35, 1, 7.5, ["B0", "C1"], 44)
piano.cc(35, 1.02, 64, 127)
piano.cc(36, 4.9, 64, 0)
RELAYS.append(35)

# Cue CAUGHT (bar 38): a low cluster under the pedal, then nothing.
piano.chord(38, 1, 2.5, ["B1", "C2", "F2", "B2", "C3"], 112)
piano.cc(38, 1.01, 64, 127)
piano.cc(38, 3.5, 64, 0)
CAUGHTS.append(38)

# ==========================================================================
# M3 RELAY — an analogue ostinato in 3+3+2 whose accents spell B - C - A
# (1, flat 2, flat 7); the lead leans 5 - flat 6 - 5, then falls 3 - flat 2 - 1.
# ==========================================================================
B0 = 40
MARKERS += [(41, "M3 RELAY - title loop bars 41-48"), (50, "M3 cue KEY"), (52, "M3 cue UNLOCKED"),
            (55, "M3 cue RELAY"), (58, "M3 cue CAUGHT")]

ARP_A = ["B3", "F#3", "B2", "C4", "F#3", "B2", "A3", "F#3"]
ARP_B = ["B3", "F#3", "B2", "C4", "F#3", "B2", "D4", "C#4"]
ARP_7 = ["B3", "G3", "B2", "C4", "G3", "B2", "A3", "G3"]
ACC = {0, 3, 6}
for r in range(1, 9):
    bar = B0 + r
    pat = ARP_B if r in (4, 8) else ARP_7 if r == 7 else ARP_A
    for e, p in enumerate(pat):
        arp.note(bar, 1 + e * .5, .4, p, 98 if e in ACC else 66)
        bass3.note(bar, 1 + e * .5, .42, "C2" if r == 7 else "B1", 92 if e in ACC else 70)
        kit3.note(bar, 1 + e * .5, .2, HH, 84 if e in ACC else 46)
    kit3.note(bar, 1, .5, KICK, 104)
    if r >= 3:
        kit3.note(bar, 2.5, .5, KICK, 86)
        kit3.note(bar, 3, .5, CLAP, 92)
    pad3.chord(bar, 1, 3.98, ["C3", "G3", "C4", "E4"] if r == 7 else ["B2", "F#3", "B3", "D4"], 54 + r * 2)
for i in range(4):
    kit3.note(B0 + 8, 4 + i * .25, .2, SNARE, 60 + i * 12)
for r, beat, beats, p in ((3, 1, 7.9, "F#4"), (5, 1, 3.9, "G4"), (6, 1, 3.9, "F#4"),
                          (7, 1, 1.9, "D4"), (7, 3, 1.9, "C4"), (8, 1, 3.9, "B3")):
    lead3.note(B0 + r, beat, beats, p, 86)
DOORS += [(41, "auto"), (45, "auto"), (49, "auto")]

# Cue KEY (bar 50): the first two accents, B - C, as a quick high pluck.
arp.note(50, 1, .4, "B5", 92)
arp.note(50, 1.25, 1.2, "C6", 96)
KEYS.append(50)

# Cue UNLOCKED (bars 52-53): 5 - flat 6 - 5 finally rises to the tonic.
for beat, beats, p in ((1, 1.9, "F#4"), (3, .9, "G4"), (4, .9, "F#4")):
    lead3.note(52, beat, beats, p, 88)
lead3.note(53, 1, 3.9, "B4", 96)
pad3.chord(53, 1, 3.95, ["B2", "F#3", "B3", "D4"], 66)
bass3.note(53, 1, 3.9, "B1", 92)
DOORS.append((53, "player"))

# Cue RELAY (bars 55-56): the ostinato at half speed, an octave down, under a C drone.
for e, p in enumerate(["B2", "F#2", "B1", "C3", "F#2", "B1", "A2", "F#2"]):
    arp.note(55 + e // 4, 1 + (e % 4), .8, p, 74 if e % 4 == 0 else 56)
lead3.note(55, 1, 7.9, "C4", 60)
lead3.bend_ramp(55, 1, 7.5, 0, -.35)
lead3.bend(57, 1, 0)
pad3.chord(55, 1, 7.9, ["B2", "C3"], 56)
RELAYS.append(55)

# Cue CAUGHT (bar 58): the ostinato jams on the flat 2, then a stab and silence.
for i in range(8):
    arp.note(58, 1 + i * .25, .2, "C4", 70 + i * 6)
pad3.chord(58, 3, 1.2, ["B2", "C3", "F3", "C4"], 118)
kit3.note(58, 3, .5, KICK, 120)
kit3.note(58, 3, .5, 49, 110)
CAUGHTS.append(58)


# --------------------------------------------------------------------------
# MIDI file
def write_midi(path):
    conductor = []
    conductor.append((0, 0, meta(0x51, struct.pack(">I", int(round(60_000_000 / BPM)))[1:])))
    conductor.append((0, 0, meta(0x58, bytes([4, 2, 24, 8]))))
    conductor.append((0, 0, meta(0x59, bytes([5, 0]))))                      # B major
    conductor.append((tick(21), 0, meta(0x59, bytes([2, 1]))))               # B minor
    for bar, text in MARKERS:
        conductor.append((tick(bar), 0, meta(0x06, text.encode("ascii"))))
    conductor.append((tick(TOTAL_BARS + 1), 0, meta(0x01, b"end")))
    chunks = []
    for i, t in enumerate(T.values()):
        chunks.append(chunk(t.events + (conductor if i == 0 else []), t.name, t.program, t.ch))
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ))
        for c in chunks:
            f.write(c)
    print("wrote", path, len(chunks), "tracks")


# --------------------------------------------------------------------------
# Audio stems (placeholders for the FMOD events)
def sec(bar, beat=1.0):
    return ((bar - 1) * 4 + (beat - 1)) * SEC_PER_BEAT


def resonator(freq, q):
    w = 2 * math.pi * freq / SR
    r = math.exp(-math.pi * (freq / q) / SR)
    a1, a2 = -2 * r * math.cos(w), r * r
    s = [0.0, 0.0]

    def step(x):
        y = (1 - r) * x - a1 * s[0] - a2 * s[1]
        s[1], s[0] = s[0], y
        return y
    return step


def add_click(buf, t0, gain, f, thunk, seed, length=.08):
    rnd = random.Random(seed)
    i0 = int(t0 * SR)
    for k in range(int(length * SR)):
        t = k / SR
        v = rnd.uniform(-1, 1) * (1 - t / .003) if t < .003 else 0.0
        v += .6 * math.sin(2 * math.pi * f * t) * math.exp(-t / .012)
        v += .5 * math.sin(2 * math.pi * thunk * t) * math.exp(-t / .03)
        if 0 <= i0 + k < len(buf):
            buf[i0 + k] += gain * v


def add_swing(buf, t0, dur, gain, creak_from, creak_to, seed, stop=.35):
    rnd = random.Random(seed)
    i0 = int(t0 * SR)
    count = int(dur * SR)
    rs = [resonator(1650, 14), resonator(2870, 11), resonator(640, 6)]
    prev = lp = phase = 0.0
    for k in range(count + int(.25 * SR)):
        u = k / count
        vel = 6 * u * (1 - u) / 1.5 if u < 1 else 0.0
        x = rnd.uniform(-1, 1)
        hp = x - prev
        prev = x
        lp = .82 * lp + .18 * hp
        out = .5 * vel * lp
        imp = 0.0
        if vel > .3 and u < 1:
            rate = creak_from * (creak_to / creak_from) ** min(1.0, u / .5)
            phase += rate * (1 + rnd.uniform(-.04, .04)) / SR
            if phase >= 1:
                phase -= 1
                imp = (vel - .3) * (.7 + .6 * rnd.random())
        out += 12.0 * (rs[0](imp) + .6 * rs[1](imp) + .8 * rs[2](imp))
        if 0 <= i0 + k < len(buf):
            buf[i0 + k] += gain * out
    add_click(buf, t0 + dur, gain * stop, 420, 68, seed + 1, .12)


def add_tone(buf, t0, f, dur, gain, attack=.01, decay=.4):
    i0 = int(t0 * SR)
    for k in range(int(dur * SR)):
        t = k / SR
        env = min(1.0, t / attack) * math.exp(-t / decay)
        if 0 <= i0 + k < len(buf):
            buf[i0 + k] += gain * env * math.sin(2 * math.pi * f * t)


def render_fx(path):
    buf = [0.0] * int((sec(TOTAL_BARS + 1) + 1) * SR)
    for bar, kind in DOORS:
        t0 = sec(bar)
        if kind == "auto":      # automatic double door: operator relay + maglock, two leaves
            add_click(buf, t0 - .02, .35, 2200, 110, bar * 7)
            add_click(buf, t0 + .03, .45, 900, 60, bar * 7 + 1, .12)
            add_swing(buf, t0 + .08, .9, .22, 270, 300, bar * 7 + 2)
            add_swing(buf, t0 + .11, .9, .16, 272, 303, bar * 7 + 3)
        else:                   # player door: handle, latch, swing
            add_click(buf, t0 - .12, .3, 1500, 95, bar * 11)
            add_click(buf, t0 - .03, .35, 1050, 80, bar * 11 + 1)
            add_swing(buf, t0 + .05, .55, .3, 270, 330, bar * 11 + 2)
    for bar in KEYS:            # key ring
        rnd = random.Random(bar)
        for h in range(5):
            th = sec(bar) + h * rnd.uniform(.025, .06)
            for _ in range(4):
                add_tone(buf, th, rnd.uniform(2300, 6200), .18, .05 * (.8 - h * .12), .001, rnd.uniform(.03, .07))
    for bar in RELAYS:          # the Relay announces itself with relay clicks
        for i, dt in enumerate((0, .21, .29)):
            add_click(buf, sec(bar) + dt, .32, 2100, 70, bar * 13 + i)
    for bar in CAUGHTS:         # tinnitus after the hard cut
        add_tone(buf, sec(bar, 3), 4186.0, 4.5, .02, .4, 1.6)
    write_wav(path, buf, peak=.7)


def render_hum(path):
    total = int((sec(TOTAL_BARS + 1) + 1) * SR)
    table_n = 2048
    amps = {1: 1.0, 2: .55, 3: .42, 4: .30, 5: .22, 6: .20, 7: .12, 8: .10, 9: .08,
            10: .05, 11: .06, 12: .03, 13: .025, 14: .02, 15: .018, 16: .012}
    table = []
    for k in range(table_n):
        x = sum(a * math.sin(2 * math.pi * h * k / table_n + h * .7) for h, a in amps.items())
        table.append(math.tanh(.9 * x))
    m = max(abs(v) for v in table)
    table = [v / m for v in table]
    freqs, gains, phases = [120.0, 120.05, 119.91], [1.0, .6, .45], [0.0, .33, .71]
    cuts = [(sec(b, 2.5), sec(b + 2)) for b in CAUGHTS]
    dips = [sec(b) for b in RELAYS]

    def env(t):
        for a, b in cuts:
            if a <= t < b:
                return 0.0
            if b <= t < b + 2.6:
                return (t - b) / 2.6
        for d in dips:
            if d <= t < d + .35:
                return .2 + .8 * (t - d) / .35
        return 1.0
    buf = [0.0] * total
    rnd = random.Random(5)
    lp1 = lp2 = 0.0
    a = math.exp(-2 * math.pi * 600 / SR)
    for i in range(total):
        t = i / SR
        v = 0.0
        for f, g, p in zip(freqs, gains, phases):
            pos = ((f * t + p) % 1.0) * table_n
            j = int(pos)
            fr = pos - j
            v += g * (table[j] + (table[(j + 1) % table_n] - table[j]) * fr)
        lp1 = (1 - a) * rnd.uniform(-1, 1) + a * lp1
        lp2 = (1 - a) * lp1 + a * lp2
        buf[i] = env(t) * (v / 2.05 * (1 + .06 * math.sin(2 * math.pi * .1 * t)) + 1.6 * lp2)
    write_wav(path, buf, peak=.25)


def write_wav(path, buf, peak):
    m = max(abs(v) for v in buf) or 1
    s = peak / m
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * s)) * 32767)) for v in buf))
    print("wrote", path, round(len(buf) / SR, 2), "s")


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    write_midi(os.path.join(out, "FrontRooms_Motifs.mid"))
    if "--midi-only" not in sys.argv:
        render_fx(os.path.join(out, "FX_Door_Foley_placeholder.wav"))
        render_hum(os.path.join(out, "Hum_120Hz_placeholder.wav"))
