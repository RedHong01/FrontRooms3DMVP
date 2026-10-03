"""Click-to-play previews for the sound research slides (Figma Slides).

    python3 make_previews.py [chart.png]

Each MP4 is the slot's spectrogram with a playhead (or a highlight box walking
through rows / takes) over the sound itself, so the poster frame matches the
static design and pressing play shows what you are hearing. Output goes to
Research/week02/assets/sound-previews/ with slots.json for the Slides mapping.
`chart.png` is a 2x screenshot of the SR07 frame (needed for the door story).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))                       # Frontrooms3D
OUT = os.path.abspath(os.path.join(ROOT, "..", "Research", "week02", "assets", "sound-previews"))
TMP = os.path.join(HERE, "build", "previews_work")
LIB = os.path.join(ROOT, "AudioSource", "FMOD_Library")
PH = os.path.join(ROOT, "AudioSource", "FMOD_Placeholders")
REN = os.path.join(HERE, "build", "renders")
FMOD_LATENCY = .093                     # measured: NRT renders start ~93 ms late
YELLOW = "0xF4DF3B"


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + list(args), check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def tile_png(audio, png, w, h, gain_db=0.0, window=None):
    """Yellow waveform over a fire spectrogram, the deck's media style. `window` fixes the time span."""
    wh = h * 3 // 10
    sh = h - wh
    d = window or duration(audio)
    ff("-t", "%.3f" % d, "-i", audio, "-filter_complex",
       "[0:a]aformat=channel_layouts=mono,volume=%sdB,apad=whole_dur=%.3f,asplit[a][b];"
       "[a]showwavespic=s=%dx%d:colors=%s:scale=sqrt[w];color=c=black:s=%dx%d[bg];[bg][w]overlay=format=auto,format=rgb24[wv];"
       "[b]showspectrumpic=s=%dx%d:legend=0:color=fire:scale=log:fscale=log:start=40:stop=16000:gain=2,format=rgb24[sp];"
       "[wv][sp]vstack" % (gain_db, d, w, wh, YELLOW, w, wh, w, sh), "-frames:v", "1", png)


def clip(src, dst, start=0.0, dur=None, gain_db=0.0, fade_out=.04):
    args = ["-ss", "%.3f" % start]
    if dur:
        args += ["-t", "%.3f" % dur]
    af = "volume=%sdB,aformat=sample_rates=48000:channel_layouts=stereo" % gain_db
    if dur and fade_out:
        af += ",afade=t=out:st=%.3f:d=%.3f" % (dur - fade_out, fade_out)
    ff(*(args + ["-i", src, "-af", af, dst]))


def sequence(parts, dst, total):
    """parts: [(wav, at_seconds, gain_db)] mixed onto one stereo timeline."""
    args, fc = [], ""
    for i, (wav, at, g) in enumerate(parts):
        args += ["-i", wav]
        ms = int(at * 1000)
        fc += "[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=%sdB,adelay=%d|%d[s%d];" % (i, g, ms, ms, i)
    fc += "".join("[s%d]" % i for i in range(len(parts)))
    fc += "amix=inputs=%d:normalize=0,apad=pad_dur=%.3f,atrim=0:%.3f" % (len(parts), total, total)
    ff(*(args + ["-filter_complex", fc, dst]))


def onset(path, after=0.0, frac=.08):
    import array
    d = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    a = array.array("f")
    a.frombytes(d)
    th = max(abs(x) for x in a) * frac
    return next(i for i in range(int(after * 8000), len(a)) if abs(a[i]) >= th) / 8000.0


def mp4(name, png, audio, boxes=None, playhead=True):
    """Still image + audio; a playhead sweeps the width, or boxes light up in turn."""
    d = duration(audio)
    vf = "[0:v]format=rgb24"
    chain = vf
    if boxes:
        for (x, y, w, h, t0, t1) in boxes:
            chain += ",drawbox=x=%d:y=%d:w=%d:h=%d:color=%s@1.0:t=6:enable='between(t,%.3f,%.3f)'" % (x, y, w, h, YELLOW, t0, t1)
        chain += "[v]"
    if playhead:
        chain += "[bg];color=c=white@0.9:s=4x2160:r=30[ph];[bg][ph]overlay=x='(W-4)*t/%.4f':y=0:eval=frame:shortest=1[v]" % d
    path = os.path.join(OUT, name + ".mp4")
    ff("-loop", "1", "-framerate", "30", "-t", "%.3f" % d, "-i", png, "-i", audio, "-filter_complex", chain,
       "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
       "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", "%.3f" % d, "-movflags", "+faststart", path)
    poster = os.path.join(OUT, name + ".png")
    ff("-i", path, "-frames:v", "1", poster)
    return path, d


SLOTS = []


def add(slide, slot, name, png, audio, w, h, **kw):
    path, d = mp4(name, png, audio, **kw)
    SLOTS.append(dict(slide=slide, slot=slot, mp4=os.path.basename(path), poster=name + ".png", seconds=round(d, 2),
                      size=[w, h]))
    print("  %-26s %5.2f s  %s" % (name, d, slot))


def wav(name):
    return os.path.join(TMP, name + ".wav")


def png(name):
    return os.path.join(TMP, name + ".png")


def main(chart=None):
    os.makedirs(TMP, exist_ok=True)
    legacy = os.path.join(ROOT, "Verification", "audio", "player-walk.wav")
    creak = os.path.join(ROOT, "Assets", "Resources", "Audio", "door-creak.wav")

    # SR01: what we had
    sequence([(legacy, 0, 0), (legacy, .55, 0), (legacy, 1.1, 0)], wav("legacy_steps"), 1.75)
    clip(creak, wav("creak"), 0, 3.2)
    clip(os.path.join(PH, "Ambience", "amb_hum_bed_loop.wav"), wav("hum_generated"), 0, 4.0)
    sequence([(os.path.join(PH, "Foley", "step_carpet_walk_%02d.wav" % (i + 1)), .55 * i, -6) for i in range(3)],
             wav("placeholder_steps"), 1.75)
    for slot, n in (("01 player step", "legacy_steps"), ("02 the one recording", "creak"),
                    ("03 the hum", "hum_generated"), ("04 FMOD placeholder", "placeholder_steps")):
        tile_png(wav(n), png("sr01_" + n), 852, 454)
        add("SR01", slot, "sr01_" + n, png("sr01_" + n), wav(n), 426, 227)

    # SR02: dry / damp / soaked, six steps each
    for k in ("dry", "damp", "soaked"):
        src = os.path.join(REN, "steps_walk_%s.wav" % k)
        clip(src, wav("walk_" + k), max(0.0, onset(src) - .02), 3.3)
        tile_png(wav("walk_" + k), png("sr02_" + k), 1152, 320, 6)
        add("SR02", k, "sr02_" + k, png("sr02_" + k), wav("walk_" + k), 576, 160)

    # SR03: together, then each layer alone, its row lit while it plays
    soaked = os.path.join(REN, "steps_walk_soaked.wav")
    clip(soaked, wav("together"), max(0.0, onset(soaked, 1.45) - .015), .5, 6)
    layers = [wav("together"), os.path.join(LIB, "Foley", "plr_step_carpet_walk_body_01.wav"),
              os.path.join(LIB, "Foley", "plr_step_damp_any_moist_03.wav"),
              os.path.join(LIB, "Foley", "plr_step_damp_any_peel_02.wav"),
              os.path.join(LIB, "Foley", "plr_step_soaked_any_squish_02.wav"),
              os.path.join(LIB, "Foley", "plr_step_any_run_cloth_03.wav")]
    gains = [0, -8, -8, -5, -8, -8]
    at = [.3 + k * .9 for k in range(6)]
    sequence([(l, t, g) for l, t, g in zip(layers, at, gains)], wav("layers"), at[-1] + .9)
    rows = []
    for k, l in enumerate(layers):                       # common 0-500 ms axis, as in the design frame
        tile_png(l, png("row%d" % k), 3072, 160, 6 if k == 0 else 0, window=.5)
        rows.append(png("row%d" % k))
    anatomy = png("sr03_anatomy")
    ff(*sum([["-i", r] for r in rows], []), "-filter_complex",
       "".join("[%d]pad=3072:176:0:0:white[p%d];" % (i, i) for i in range(5)) +
       "".join("[p%d]" % i for i in range(5)) + "[5]vstack=inputs=6", anatomy)
    add("SR03", "anatomy", "sr03_layers", anatomy, wav("layers"), 1536, 520, playhead=False,
        boxes=[(3, k * 176 + 3, 3066, 154, t - .05, t + .8) for k, t in enumerate(at)])

    # SR04: the ten takes, one after another
    takes = [os.path.join(LIB, "Foley", "plr_step_carpet_walk_body_%02d.wav" % (i + 1)) for i in range(10)]
    at = [.3 + k * .6 for k in range(10)]
    sequence([(t, a, -3) for t, a in zip(takes, at)], wav("takes"), at[-1] + .7)
    tiles = []
    for i, t in enumerate(takes):
        tile_png(t, png("take%d" % i), 326, 720, window=.42)
        tiles.append(png("take%d" % i))
    ff(*sum([["-i", t] for t in tiles], []), "-filter_complex",
       "".join("[%d]pad=358:720:0:0:white[q%d];" % (i, i) for i in range(9)) +
       "".join("[q%d]" % i for i in range(9)) + "[9]hstack=inputs=10", png("sr04_takes"))
    add("SR04", "ten takes", "sr04_takes", png("sr04_takes"), wav("takes"), 1774, 360, playhead=False,
        boxes=[(k * 358 + 3, 3, 320, 714, t - .05, t + .55) for k, t in enumerate(at)])

    # SR05: one click per source family
    fam = [("steps", os.path.join(LIB, "Foley", "plr_step_carpet_walk_body_01.wav"), 0, 2.0),
           ("wet", os.path.join(LIB, "Foley", "plr_step_soaked_any_squish_02.wav"), 0, 2.0),
           ("doors", os.path.join(LIB, "Door", "door_latch_slam_01.wav"), 0, 2.0),
           ("hum", os.path.join(LIB, "Ambience", "amb_hum_bed_loop.wav"), 2, 4.0),
           ("air", os.path.join(LIB, "Ambience", "amb_air_hall_loop.wav"), 4, 5.0),
           ("glass", os.path.join(LIB, "Window", "win_shatter_01.wav"), 0, 2.0),
           ("keys", os.path.join(LIB, "Foley", "plr_key_pickup_01.wav"), 0, 1.2),
           ("cloth", os.path.join(LIB, "Foley", "plr_cloth_move_01.wav"), 0, 1.2)]
    D, F, W = (os.path.join(LIB, x) for x in ("Door", "Foley", "Window"))
    seqs = {  # short stories, so a click plays more than a blip
        "doors": ([(os.path.join(D, "door_handle_press_01.wav"), 0, 0), (os.path.join(D, "door_unlatch_bolt_01.wav"), .1, -4),
                   (os.path.join(D, "door_latch_slam_01.wav"), 1.0, 0)], 2.0),
        "glass": ([(os.path.join(W, "win_crack_hit_01.wav"), 0, -3), (os.path.join(W, "win_shatter_01.wav"), .9, 0)], 2.6),
        "keys": ([(os.path.join(F, "plr_key_pickup_01.wav"), 0, 0), (os.path.join(F, "plr_key_pickup_03.wav"), 1.0, 0)], 1.9),
        "cloth": ([(os.path.join(F, "plr_cloth_move_%02d.wav" % (i + 1)), .55 * i, 0) for i in range(3)], 1.7),
    }
    for k, src, s0, d in fam:
        if k in ("steps", "wet"):                       # a few takes in a row, so it reads as walking
            n = sorted(f for f in os.listdir(os.path.dirname(src)) if f.startswith(os.path.basename(src)[:-7]))[:3]
            sequence([(os.path.join(os.path.dirname(src), f), .55 * i, -3) for i, f in enumerate(n)], wav("fam_" + k), d)
        elif k in seqs:
            sequence(seqs[k][0], wav("fam_" + k), seqs[k][1])
        else:
            clip(src, wav("fam_" + k), s0, d, 0 if k not in ("hum", "air") else 6)
        tile_png(wav("fam_" + k), png("sr05_" + k), 852, 400)
        add("SR05", k, "sr05_" + k, png("sr05_" + k), wav("fam_" + k), 426, 200)

    # SR07: the door chart, sounding as the playhead crosses each marker
    if chart:
        story = os.path.join(REN, "door_story.wav")
        clip(story, wav("door_story"), FMOD_LATENCY, 14.0, 0, .3)
        k = int(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0", chart],
                               capture_output=True, text=True, check=True).stdout.strip()) // 1920
        ff("-i", chart, "-vf", "crop=%d:%d:%d:%d,format=rgb24" % (1776 * k, 470 * k, 72 * k, 340 * k), png("sr07_chart"))
        add("SR07", "door chart", "sr07_door_story", png("sr07_chart"), wav("door_story"), 1776, 470)

    # SR08: before / after, same cadence and loudness
    sequence([(os.path.join(PH, "Foley", "step_carpet_walk_%02d.wav" % (i + 1)), .55 * i, -6) for i in range(3)],
             wav("before"), 1.75)
    walk = os.path.join(REN, "steps_walk_damp.wav")
    clip(walk, wav("after"), max(0.0, onset(walk) - .02), 1.75, 0, .2)
    for k in ("before", "after"):
        tile_png(wav(k), png("sr08_" + k), 1728, 480, 6)
        add("SR08", k, "sr08_" + k, png("sr08_" + k), wav(k), 864, 240)

    for slot in SLOTS:
        k = slot["mp4"][:-4]
        slot["layer"] = "media:" + k
        slot["slides_slide"], slot["slides_node"] = SLIDES_NODES[k]
        slot["sources"] = SOURCES[k]
    with open(os.path.join(OUT, "slots.json"), "w") as f:
        json.dump(dict(slides_file_key="NmYGRYKlhfX6H4rbJ7QcSN", design_file_key="0tCbAiVUlrPId3RWd9LRif",
                       playback="click to play, sound on, no autoplay, no loop", slots=SLOTS), f, indent=1)
    write_ledger()
    write_instructions()
    print(len(SLOTS), "previews in", OUT)


# Slides 15-22 in NmYGRYKlhfX6H4rbJ7QcSN: slot layer per preview (slide, node)
SLIDES_NODES = {
    "sr01_legacy_steps": ("15", "174:626"), "sr01_creak": ("15", "174:629"), "sr01_hum_generated": ("15", "174:632"),
    "sr01_placeholder_steps": ("15", "174:635"), "sr02_dry": ("16", "176:636"), "sr02_damp": ("16", "176:639"),
    "sr02_soaked": ("16", "176:642"), "sr03_layers": ("17", "174:691"), "sr04_takes": ("18", "175:629"),
    "sr05_steps": ("19", "175:651"), "sr05_wet": ("19", "175:653"), "sr05_doors": ("19", "175:655"),
    "sr05_hum": ("19", "175:657"), "sr05_air": ("19", "175:659"), "sr05_glass": ("19", "175:661"),
    "sr05_keys": ("19", "175:663"), "sr05_cloth": ("19", "175:665"), "sr07_door_story": ("21", "175:801"),
    "sr08_before": ("22", "175:842"), "sr08_after": ("22", "175:844")}

FS = "Freesound %s (%s, %s)"
STEPS = [FS % ("575321", "taure", "CC0"), FS % ("256209", "hannagreen", "CC0")]
DAMP = [FS % ("583287", "Profispiesser", "CC0"), FS % ("187617", "bewagne", "CC-BY 3.0")]
DOORS = [FS % ("768656", "Nox_Sound", "CC0"), FS % ("843829", "thaighaudio", "CC0"), FS % ("341176", "klangfabrik", "CC0"),
         FS % ("160213", "qubodup", "CC0"), "BigSoundBank 3205 Creaking Door #2 (CC0)"]
ROOM = [FS % ("454098", "kyles", "CC0"), FS % ("406508", "kyles", "CC0"), FS % ("341512", "klankbeeld", "CC-BY 4.0")]
MADE = "made in the project (synthesized placeholder)"
RENDER = "rendered through the built FMOD banks (Tools/audio/fmod_check.py render)"
SOURCES = {
    "sr01_legacy_steps": ["Frontrooms3D/Verification/audio/player-walk.wav: the old procedural step, " + MADE],
    "sr01_creak": ["BigSoundBank 3205 Creaking Door #2 (CC0), the build's only recording"],
    "sr01_hum_generated": ["AudioSource/FMOD_Placeholders/Ambience/amb_hum_bed_loop.wav, " + MADE],
    "sr01_placeholder_steps": ["AudioSource/FMOD_Placeholders/Foley/step_carpet_walk_01-03.wav, " + MADE],
    "sr02_dry": ["Footstep event at Dampness 0, " + RENDER] + STEPS,
    "sr02_damp": ["Footstep event at Dampness 0.4, " + RENDER] + STEPS + DAMP,
    "sr02_soaked": ["Footstep event at Dampness 0.9, " + RENDER] + STEPS + DAMP,
    "sr03_layers": ["one soaked step, " + RENDER, "then each layer file from AudioSource/FMOD_Library"] + STEPS + DAMP
                   + [FS % ("611276", "xkeril", "CC0")],
    "sr04_takes": ["plr_step_carpet_walk_body_01-10 (LIBRARY.json lists each take's source second)"] + STEPS,
    "sr05_steps": STEPS, "sr05_wet": [FS % ("187617", "bewagne", "CC-BY 3.0")], "sr05_doors": DOORS[:3],
    "sr05_hum": [FS % ("454098", "kyles", "CC0")], "sr05_air": [FS % ("406508", "kyles", "CC0")],
    "sr05_glass": [FS % ("376607", "Soundkrampf", "CC0"), FS % ("575283", "TRP", "CC0")],
    "sr05_keys": [FS % ("616835", "TRP", "CC0")], "sr05_cloth": [FS % ("611276", "xkeril", "CC0")],
    "sr07_door_story": ["door events + room tone, " + RENDER, "timed to the SR07 chart markers (scenario_door_story)"] + DOORS + ROOM[:2],
    "sr08_before": ["AudioSource/FMOD_Placeholders/Foley/step_carpet_walk_01-03.wav, " + MADE],
    "sr08_after": ["Footstep event at Dampness 0.4, " + RENDER] + STEPS + DAMP,
}


def write_ledger():
    rows = ["# Sources for the sound previews", "",
            "Every preview is either a project render or a cut from a licensed recording. Freesound pages: "
            "https://freesound.org/s/<id>/. Full licence notes and CC-BY credit lines: "
            "Frontrooms3D/Documentation/AUDIO_LICENSES.md. Exact source seconds per asset: "
            "Frontrooms3D/AudioSource/FMOD_Library/LIBRARY.json.", "",
            "The two canon images on slide 16 / SR02 come from Research/week02/ip-research (see its SOURCES.md): "
            "the Level 0 photo (Wikimedia Commons, EXIF 2002-06-12, \"copyrighted free use\") and Kane Pixels, "
            "\"The Backrooms (Found Footage)\", youtube.com/watch?v=H4dGpz6cnHo at 0:48.", "",
            "| Preview | Slide | Sources |", "|---|---|---|"]
    for slot in SLOTS:
        rows.append("| `%s` | %s | %s |" % (slot["mp4"], slot["slides_slide"], "<br>".join(slot["sources"])))
    with open(os.path.join(OUT, "SOURCES.md"), "w") as f:
        f.write("\n".join(rows) + "\n")



def write_instructions():
    rows = ["| %d | %s (%s) | %s | `%s` | `%s` | %s | %.1f s |" % (i, s["slides_slide"], s["slide"], s["slot"], s["mp4"],
                                                               s["layer"], s["slides_node"], s["seconds"])
            for i, s in enumerate(SLOTS, 1)]
    doc = """# Insert the sound previews into the FrontRooms sound slides (Slides 15-22)

For whoever does the insertion (Red, or an agent driving the Figma desktop app).
The Figma MCP upload accepts images only, so each MP4 has to go in through the Figma editor.
Every slot already shows its poster (the video's first frame), so the deck reads correctly before any video is in.

## File

Slides file `NmYGRYKlhfX6H4rbJ7QcSN` (the Project 1 deck), slides **15-22** at the end of the row.
They mirror the design frames SR01-SR08 in section "FRONTROOMS · SOUND RESEARCH" (design file `0tCbAiVUlrPId3RWd9LRif`, node 2339:858).
To jump to a slot: https://www.figma.com/slides/NmYGRYKlhfX6H4rbJ7QcSN?node-id=<node with - instead of :>

## Steps for each row

1. Select the slot layer (it is named `media:<clip>`; Edit > Find works with the exact name).
2. Fill > click the image swatch > **Video** > **Upload from computer** > pick the MP4 from this folder. Keep the fit mode on **Fill**.
3. In the Slides video options set **Autoplay off, Loop off, Sound on**: these are click-to-play previews
   (the week-1 deck's clips are the opposite: muted autoplay loops).
4. Don't rename, move or resize the layer.

Each video shows the spectrogram of exactly the audio it plays, with a white playhead; on slides 17 and 18 a yellow box
walks through the layers / takes instead. On slide 21 the playhead crosses each marker on the door chart at the moment
that sound fires (audio rendered through the built FMOD banks). Sources for every clip: SOURCES.md.

## Slot map (%d slots)

| # | Slide | Slot | MP4 | Layer | Slides node | Length |
|---|---|---|---|---|---|---|
%s

Regenerate everything with `python3 Frontrooms3D/Tools/audio/make_previews.py <screenshot of SR07>`
(the audio renders come from `fmod_check.py render`).
""" % (len(SLOTS), "\n".join(rows))
    with open(os.path.join(OUT, "INSERT_VIDEOS_INSTRUCTIONS.md"), "w") as f:
        f.write(doc)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
