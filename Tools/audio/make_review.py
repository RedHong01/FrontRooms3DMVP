"""Sound review sheet: every sound the game can play, one short click-to-play clip each.

    python3 make_review.py

Groups: A recorded (real rooms and objects, lightly cleaned), B reshaped (recorded but
pitched or layered), C synthesized (FMOD placeholders still in the banks), D the old Unity
audio (what plays whenever FMOD is off). `funny` is my guess, from how each sound is made,
of what may read as cartoonish; Red listens and picks. Output:
Research/week02/assets/sound-review/ (MP4 + poster per card, review.json).
"""
import json
import os
import shutil

import make_previews as M

OUT = os.path.abspath(os.path.join(M.ROOT, "..", "Research", "week02", "assets", "sound-review"))
TMP = os.path.join(M.HERE, "build", "review_work")
LEG = os.path.join(M.HERE, "build", "legacy_audio")
L = lambda *p: os.path.join(M.LIB, *p)
PH = lambda *p: os.path.join(M.PH, *p)
R = lambda *p: os.path.join(M.REN, *p)


def lib_seq(folder, prefix, n, gap, gain=0, start=1):
    return [(L(folder, "%s_%02d.wav" % (prefix, start + i)), gap * i, gain) for i in range(n)]


def ph_seq(folder, prefix, n, gap, gain=0):
    return [(PH(folder, "%s_%02d.wav" % (prefix, i + 1)), gap * i, gain) for i in range(n)]


# id, group, title, note, funny (None = not flagged), parts [(wav, at, gainDb)], length s
CARDS = [
    ("A01", "A", "Carpet step · walk", "Sneakers on padded carpet", None, lib_seq("Foley", "plr_step_carpet_walk_body", 4, .55), 2.4),
    ("A02", "A", "Carpet step · run", "Running on the same carpet", None, lib_seq("Foley", "plr_step_carpet_run_body", 5, .34), 2.0),
    ("A03", "A", "Carpet tile step", "Office glue-down tiles", None, lib_seq("Foley", "plr_step_tile_walk_body", 4, .55), 2.4),
    ("A04", "A", "Wet pile", "Damp layer under each step", None, lib_seq("Foley", "plr_step_damp_any_moist", 3, .55), 1.9),
    ("A05", "A", "Sole peel", "Sticky lift after the heel", None, lib_seq("Foley", "plr_step_damp_any_peel", 4, .45), 2.0),
    ("A06", "A", "Soaked squish", "Waterlogged shoe, wet zones", "Squelch may read cartoonish", lib_seq("Foley", "plr_step_soaked_any_squish", 3, .55), 1.9),
    ("A07", "A", "Jacket swish", "Cloth on every run stride", None, lib_seq("Foley", "plr_step_any_run_cloth", 4, .34), 1.7),
    ("A08", "A", "Key pickup", "Key ring lifted", None, [(L("Foley", "plr_key_pickup_01.wav"), 0, 0), (L("Foley", "plr_key_pickup_03.wav"), 1.0, 0)], 2.0),
    ("A09", "A", "Door handle + bolt", "Lever down, latch draws", None,
     [(L("Door", "door_handle_press_01.wav"), 0, 0), (L("Door", "door_unlatch_bolt_01.wav"), .1, -4),
      (L("Door", "door_handle_press_02.wav"), 1.0, 0), (L("Door", "door_unlatch_bolt_02.wav"), 1.1, -4)], 1.8),
    ("A10", "A", "Locked door", "Handle rattles on the bolt", None, lib_seq("Door", "door_locked_rattle", 2, 1.1), 2.3),
    ("A11", "A", "Door shuts · soft to slam", "Latch hits, three strengths", None,
     [(L("Door", "door_latch_soft_01.wav"), 0, -6), (L("Door", "door_latch_norm_01.wav"), .9, -3), (L("Door", "door_latch_slam_01.wav"), 1.8, 0)], 3.0),
    ("A12", "A", "Door hits its stop", "Soft, medium, hard", None,
     [(L("Door", "door_stop_soft_01.wav"), 0, -6), (L("Door", "door_stop_med_01.wav"), .8, -3), (L("Door", "door_stop_hard_01.wav"), 1.6, 0)], 2.6),
    ("A13", "A", "Hinge creak", "Only on slow swings", "Horror-cliché creak", [(L("Door", "door_swing_creak_loop.wav"), 0, 0), (L("Door", "door_swing_creak_loop.wav"), .95, 0)], 1.9),
    ("A14", "A", "Window crack", "Glass flexes as you hold E", None, lib_seq("Window", "win_crack_hit", 2, 1.0), 2.0),
    ("A15", "A", "Window shatter", "The pane gives way", None, [(L("Window", "win_shatter_01.wav"), 0, 0)], 1.7),
    ("A16", "A", "Tube hum", "Room hum, beats with tension", None,
     [(L("Ambience", "amb_hum_bed_loop.wav"), 0, 6), (L("Ambience", "amb_hum_beat_loop.wav"), 2.0, 6)], 4.0),
    ("A17", "A", "One lamp up close", "Hum of the nearest fixture", None, [(L("Ambience", "amb_fixture_close_loop.wav"), 0, 3)], 3.0),
    ("A18", "A", "Lamp starts and ticks", "Starter flicker, ballast ticks", "Sped-up starter, may buzz",
     [(L("Ambience", "amb_fixture_strike_01.wav"), 0, 0), (L("Ambience", "amb_fixture_tick_01.wav"), 1.6, 0), (L("Ambience", "amb_fixture_tick_02.wav"), 2.0, 0)], 2.4),
    ("A19", "A", "Room tone", "Hall air, then tall-room air", None,
     [(L("Ambience", "amb_air_hall_loop.wav"), 0, 14), (L("Ambience", "amb_air_mall_loop.wav"), 2.5, 12)], 5.0),
    ("B01", "B", "Relay walk", "Dress shoes, 3 semitones down", "Slowed tape, may sound slow-mo", lib_seq("Relay", "rly_step_carpet_walk_body", 4, .62), 2.6),
    ("B02", "B", "Relay run", "Same shoes, 2 semitones down", None, lib_seq("Relay", "rly_step_carpet_run_body", 5, .4), 2.2),
    ("B03", "B", "Relay drag", "Step + cloth, 7 semitones down", "Monster-movie rumble", lib_seq("Relay", "rly_step_carpet_drag_body", 2, .9), 1.8),
    ("B04", "B", "Relay hits a door", "Door slams pitched down", None, lib_seq("Door", "door_blow_hit", 3, .55), 2.4),
    ("B05", "B", "Door forced through", "Wood break + slam layered", None, [(L("Door", "door_break_rip_01.wav"), 0, 0)], 1.2),
    ("B06", "B", "Wood splitting", "Under the later blows", None, lib_seq("Door", "door_blow_split", 2, .7), 1.4),
    ("B07", "B", "Relay on soaked carpet", "Its steps plus the wet layers", "Low squelch can turn comic", [(R("relay_wet_steps.wav"), 0, 4)], 3.4),
    ("C01", "C", "Metal floor step", "Threshold strips", "Toy-like ping", ph_seq("Foley", "step_metal_walk", 4, .55), 2.4),
    ("C02", "C", "Door closer hiss", "Under a swinging door", None, [(PH("Door", "door_closer_loop.wav"), 0, 0)], 2.2),
    ("C03", "C", "Fast-close air thump", "A door slammed fast", None, ph_seq("Door", "door_air_whump", 2, .6), 1.2),
    ("C04", "C", "Automatic door motor", "Title-stream doors", "Buzzy sci-fi motor", [(PH("Door", "door_auto_operator_01.wav"), 0, 0)], 1.4),
    ("C05", "C", "Glass under stress", "While you hold E on a window", "Ringing digital tone", [(PH("Window", "window_stress_loop.wav"), 0, 0)], 2.3),
    ("C06", "C", "Lamp pop", "A tube failing", None, ph_seq("Ambience", "amb_fixture_pop", 2, .7), 1.4),
    ("C07", "C", "Relay presence", "Low drone near the Relay", None, [(PH("Relay", "relay_presence_loop.wav"), 0, 4)], 3.0),
    ("C08", "C", "Relay clicks", "First sign it's awake", None, ph_seq("Relay", "relay_clicks", 2, .8), 1.5),
    ("C09", "C", "Relay stingers", "Hunt, search, chase, lost", "Sine swells, slide-whistle",
     [(PH("Relay", "relay_sting_hunt.wav"), 0, 0), (PH("Relay", "relay_sting_search.wav"), 2.6, 0),
      (PH("Relay", "relay_sting_chase.wav"), 4.4, 0), (PH("Relay", "relay_sting_lost.wav"), 6.6, 0)], 8.6),
    ("C10", "C", "Breath", "Calm, then out of stamina", "Robotic wheeze",
     [(PH("Subjective", "breath_calm_loop.wav"), 0, 6), (PH("Subjective", "breath_heavy_loop.wav"), 4.0, 0)], 6.6),
    ("C11", "C", "Heartbeat", "Relay close but unseen", "Sine thumps, not a heart", [(PH("Subjective", "heartbeat_slow_loop.wav"), 0, 0), (PH("Subjective", "heartbeat_fast_loop.wav"), 2.0, 0)], 3.0),
    ("C12", "C", "Tinnitus", "After you're caught", None, [(PH("Subjective", "tinnitus.wav"), 0, 6)], 3.0),
    ("D01", "D", "Player step", "Synth thump + noise", "A beep, not a shoe",
     [(os.path.join(LEG, "player_step_%s_%d.wav" % (k, i)), .5 * i, 0) for i in range(3) for k in ("impact", "texture", "cloth")], 1.6),
    ("D02", "D", "Relay step", "Same synth, darker", "Synthetic thud",
     [(os.path.join(LEG, "hunter_step_%s_%d.wav" % (k, i)), .55 * i, 0) for i in range(3) for k in ("impact", "texture", "cloth")], 1.8),
    ("D03", "D", "Hum", "2 s loop, never changes", "Pure buzz, never changes", [(os.path.join(LEG, "hum.wav"), 0, 0), (os.path.join(LEG, "hum.wav"), 2.0, 0)], 4.0),
    ("D04", "D", "Door", "One creak for open and shut", "Haunted-house creak",
     [(os.path.join(M.ROOT, "Assets", "Resources", "Audio", "door-creak.wav"), 0, 0)], 3.2),
    ("D05", "D", "Title-stream door", "Synth latch, creak, travel", "Same creak as the door",
     [(os.path.join(LEG, "door_latch.wav"), 0, -2), (os.path.join(M.ROOT, "Assets", "Resources", "Audio", "door-creak.wav"), 0, -4),
      (os.path.join(LEG, "door_travel.wav"), 0, -2)], 3.2),
    ("D06", "D", "Break and glass", "One synth crash for both", "Glass sounds like a door",
     [(os.path.join(LEG, "door_break.wav"), 0, 0), (os.path.join(LEG, "door_break.wav"), .7, 0)], 1.2),
    ("D07", "D", "Caught", "Synth sting when caught", "Arcade game-over", [(os.path.join(LEG, "caught.wav"), 0, 0)], 1.7),
]
GROUPS = {"A": "Recorded", "B": "Reshaped", "C": "Synthesized", "D": "Old Unity audio"}


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    os.makedirs(TMP, exist_ok=True)
    M.TMP = TMP
    M.OUT = OUT
    M.SLOTS.clear()
    cards = []
    for cid, g, title, note, funny, parts, length in CARDS:
        wav = os.path.join(TMP, cid + ".wav")
        M.sequence(parts, wav, length)
        png = os.path.join(TMP, cid + ".png")
        M.tile_png(wav, png, 384, 216, 0)
        path, d = M.mp4("rv_" + cid, png, wav)
        cards.append(dict(id=cid, group=g, group_name=GROUPS[g], title=title, note=note, funny=funny,
                          mp4=os.path.basename(path), poster="rv_%s.png" % cid, seconds=round(d, 2),
                          layer="media:rv_" + cid))
        print("  %s %-26s %4.1fs %s" % (cid, title, d, ("FUNNY? " + funny) if funny else ""))
    with open(os.path.join(OUT, "review.json"), "w") as f:
        json.dump(dict(slides_file_key="NmYGRYKlhfX6H4rbJ7QcSN", cards=cards), f, indent=1, ensure_ascii=False)
    print(len(cards), "cards ->", OUT)


if __name__ == "__main__":
    main()
