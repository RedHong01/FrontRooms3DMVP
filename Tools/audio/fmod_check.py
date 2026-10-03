"""Bank-level checks without Unity, straight through the FMOD runtime library.

    python3 fmod_check.py contract           # every event / parameter / bus the game code uses exists
    python3 fmod_check.py render [outdir]    # non-realtime renders of gameplay moments (default build/renders)

The contract is read from the C# sources (SoundIds + FrontRoomsFmodVerify),
so this stays in step with the Unity-side check. Renders use FMOD's
WAV-writer output: each System update mixes one block, so timing is exact
and the files are what the game would play at the listener.
"""
import ctypes as C
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LIBFILE = os.path.join(ROOT, "Assets", "Plugins", "FMOD", "platforms", "mac", "lib", "fmodstudio.bundle", "Contents",
                       "MacOS", "fmodstudio")
BANKS = os.path.join(ROOT, "FMOD", "FrontRooms", "Build", "Desktop")
VERSION = 0x00020315
OUT_NOSOUND, OUT_WAVWRITER_NRT, SPEAKER_STEREO, STUDIO_SYNC_UPDATE = 2, 5, 3, 0x4

fmod = C.CDLL(LIBFILE)


class Vec(C.Structure):
    _fields_ = [("x", C.c_float), ("y", C.c_float), ("z", C.c_float)]


class Attr(C.Structure):
    _fields_ = [("position", Vec), ("velocity", Vec), ("forward", Vec), ("up", Vec)]


def attr(x=0.0, y=0.0, z=0.0):
    return Attr(Vec(x, y, z), Vec(0, 0, 0), Vec(0, 0, 1), Vec(0, 1, 0))


def ok(result, what):
    if result != 0:
        raise RuntimeError("%s: FMOD_RESULT %d" % (what, result))


class Studio:
    def __init__(self, wav=None, rate=48000, block=512):
        self.sys = C.c_void_p()
        ok(fmod.FMOD_Studio_System_Create(C.byref(self.sys), VERSION), "create")
        core = C.c_void_p()
        ok(fmod.FMOD_Studio_System_GetCoreSystem(self.sys, C.byref(core)), "core")
        ok(fmod.FMOD5_System_SetOutput(core, OUT_WAVWRITER_NRT if wav else OUT_NOSOUND), "output")
        ok(fmod.FMOD5_System_SetSoftwareFormat(core, rate, SPEAKER_STEREO, 0), "format")
        ok(fmod.FMOD5_System_SetDSPBufferSize(core, block, 4), "dsp buffer")
        self._wav = C.c_char_p(wav.encode()) if wav else None
        ok(fmod.FMOD_Studio_System_Initialize(self.sys, 256, STUDIO_SYNC_UPDATE, 0, self._wav), "init")
        self.banks = {}
        for name in ("Master.bank", "Master.strings.bank", "Ambience.bank", "SFX.bank", "Music.bank"):
            bank = C.c_void_p()
            ok(fmod.FMOD_Studio_System_LoadBankFile(self.sys, os.path.join(BANKS, name).encode(), 0, C.byref(bank)),
               "load " + name)
            self.banks[name] = bank
        for name, bank in self.banks.items():
            if "strings" not in name:
                fmod.FMOD_Studio_Bank_LoadSampleData(bank)
        ok(fmod.FMOD_Studio_System_FlushSampleLoading(self.sys), "flush sample loading")
        ok(fmod.FMOD_Studio_System_SetListenerAttributes(self.sys, 0, C.byref(attr()), None), "listener")
        self.rate, self.block, self.t, self.live = rate, block, 0.0, []

    def event(self, path):
        desc = C.c_void_p()
        r = fmod.FMOD_Studio_System_GetEvent(self.sys, path.encode(), C.byref(desc))
        return desc if r == 0 else None

    def has_param(self, desc, name):
        buf = C.create_string_buffer(128)
        return fmod.FMOD_Studio_EventDescription_GetParameterDescriptionByName(desc, name.encode(), buf) == 0

    def has_global(self, name):
        buf = C.create_string_buffer(128)
        return fmod.FMOD_Studio_System_GetParameterDescriptionByName(self.sys, name.encode(), buf) == 0

    def has_bus(self, path):
        bus = C.c_void_p()
        return fmod.FMOD_Studio_System_GetBus(self.sys, path.encode(), C.byref(bus)) == 0

    # ---------------------------------------------------------- playback
    def play(self, path, pos=(0, 0, 0), keep=False, **params):
        desc = self.event(path)
        if desc is None:
            raise RuntimeError("no event " + path)
        inst = C.c_void_p()
        ok(fmod.FMOD_Studio_EventDescription_CreateInstance(desc, C.byref(inst)), "instance " + path)
        fmod.FMOD_Studio_EventInstance_Set3DAttributes(inst, C.byref(attr(*pos)))
        for k, v in params.items():
            ok(fmod.FMOD_Studio_EventInstance_SetParameterByName(inst, k.encode(), C.c_float(v), 1), path + " " + k)
        ok(fmod.FMOD_Studio_EventInstance_Start(inst), "start " + path)
        if keep:
            return inst
        fmod.FMOD_Studio_EventInstance_Release(inst)
        return None

    def set(self, inst, **params):
        for k, v in params.items():
            fmod.FMOD_Studio_EventInstance_SetParameterByName(inst, k.encode(), C.c_float(v), 0)

    def move(self, inst, pos):
        fmod.FMOD_Studio_EventInstance_Set3DAttributes(inst, C.byref(attr(*pos)))

    def stop(self, inst, immediate=False):
        fmod.FMOD_Studio_EventInstance_Stop(inst, 1 if immediate else 0)
        fmod.FMOD_Studio_EventInstance_Release(inst)

    def set_global(self, name, value):
        fmod.FMOD_Studio_System_SetParameterByName(self.sys, name.encode(), C.c_float(value), 0)

    def run(self, seconds, script=(), each=None):
        """Advance time block by block; script = [(time, fn)], each(t) runs every block."""
        todo = sorted(script, key=lambda a: a[0])
        end = self.t + seconds
        while self.t < end:
            while todo and todo[0][0] <= self.t:
                todo.pop(0)[1]()
            if each:
                each(self.t)
            ok(fmod.FMOD_Studio_System_Update(self.sys), "update")
            self.t += self.block / self.rate

    def close(self):
        fmod.FMOD_Studio_System_Release(self.sys)


# ----------------------------------------------------------------- contract
def contract():
    ids = open(os.path.join(ROOT, "Assets", "Scripts", "Audio", "FrontRoomsSoundIds.cs")).read()
    consts = dict(re.findall(r'public const string (\w+) = "([^"]+)"', ids.split("class Param")[0]))
    params = dict(re.findall(r'public const string (\w+) = "([^"]+)"', ids.split("class Param")[1]))
    src = open(os.path.join(ROOT, "Assets", "Editor", "Audio", "FrontRoomsFmodVerify.cs")).read()
    entries = re.findall(r'\{ SoundIds\.(\w+), new ?(?:\[\] \{([^}]*)\}|string\[0\]) \}', src)
    globals_ = re.findall(r'SoundIds\.Param\.(\w+)', src.split("Globals =")[1].split(";")[0])
    buses = re.findall(r'SoundIds\.(Bus\w+)', src.split("Buses =")[1].split(";")[0])
    s = Studio()
    fails = []
    for name, plist in entries:
        path = consts[name]
        desc = s.event(path)
        if desc is None:
            fails.append("missing event " + path)
            continue
        for p in re.findall(r'SoundIds\.Param\.(\w+)', plist or ""):
            if not s.has_param(desc, params[p]):
                fails.append("missing parameter %s on %s" % (params[p], path))
    for g in globals_:
        if not s.has_global(params[g]):
            fails.append("missing global " + params[g])
    for b in buses:
        if not s.has_bus(consts[b]):
            fails.append("missing bus " + consts[b])
    s.close()
    if fails:
        print("FMOD contract FAILED:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("FMOD contract OK: %d events, %d globals, %d buses (banks in %s)" % (len(entries), len(globals_), len(buses),
                                                                               os.path.relpath(BANKS, ROOT)))


# ----------------------------------------------------------------- renders
FEET = (0.0, -1.55, 0.25)


def walk(s, n, interval, start=.3, **params):
    return [(start + i * interval, (lambda: s.play("event:/Foley/Player/Footstep", FEET, **params))) for i in range(n)]


def scenario_steps(out, name, surface, gait, damp, n, interval):
    s = Studio(os.path.join(out, name + ".wav"))
    script = walk(s, n, interval, Surface=surface, Gait=gait, Dampness=damp)
    script.append((.3 + n * interval + .15, lambda: s.play("event:/Foley/Player/Footstep", FEET, Surface=surface, Gait=2,
                                                           Dampness=damp)))
    s.run(.3 + n * interval + 1.2, script)
    s.close()


def scenario_relay(out):
    s = Studio(os.path.join(out, "relay_approach.wav"))
    steps = []
    t, i = .3, 0
    while t < 7.6:
        z = 22 - 19 * (t / 7.6)                                  # 22 m -> 3 m
        occ = .85 if t < 3.5 else max(0.0, .85 - (t - 3.5) * .6)   # turns the corner at 3.5 s
        x = .35 if i % 2 else -.35
        steps.append((t, (lambda z=z, occ=occ, x=x: s.play("event:/Relay/Footstep", (x, -1.6, z), RelayGait=0,
                                                           Occlusion=occ, Dampness=.4))))
        t += .62
        i += 1
    s.run(8.6, steps)
    s.close()


def scenario_door(out):
    s = Studio(os.path.join(out, "door_open_close.wav"))
    door = (0.4, 0.0, 1.6)
    state = {}

    def swing_start():
        state["swing"] = s.play("event:/Mechanism/Door/Swing", door, keep=True, AngularVelocity=0, Openness=0)

    def swing_stop():
        s.stop(state.pop("swing"))

    def each(t):
        inst = state.get("swing")
        if inst is None:
            return
        if t < 1.6:                                              # opening: push, glide, slow into the stop
            u = (t - .35) / 1.25
            vel = math.sin(math.pi * min(1.0, max(0.0, u))) * .7
            s.set(inst, AngularVelocity=vel, Openness=min(1.0, max(0.0, u)))
        else:                                                    # closer pulls it back
            u = (t - 3.0) / 1.1
            vel = math.sin(math.pi * min(1.0, max(0.0, u))) ** .7 * .55
            s.set(inst, AngularVelocity=vel, Openness=1 - min(1.0, max(0.0, u)))

    script = [(.2, lambda: s.play("event:/Mechanism/Door/Handle", door)),
              (.27, lambda: s.play("event:/Mechanism/Door/Unlatch", door)),
              (.35, swing_start), (1.6, swing_stop),
              (1.6, lambda: s.play("event:/Mechanism/Door/StopLimit", door, Impact=.3)),
              (3.0, swing_start), (4.1, swing_stop),
              (4.1, lambda: s.play("event:/Mechanism/Door/LatchStrike", door, Impact=.62))]
    s.run(5.6, script, each)
    s.close()


def scenario_relay_door(out):
    s = Studio(os.path.join(out, "door_relay_break.wav"))
    door = (0.0, 0.0, 3.0)
    script = [(.2 + 1.1 * k, (lambda k=k: s.play("event:/Mechanism/Door/Blow", door, Damage=(k + 1) / 5.0)))
              for k in range(4)]
    script += [(4.7, lambda: s.play("event:/Mechanism/Door/Break", door)),
               (4.75, lambda: s.play("event:/Mechanism/Door/StopLimit", door, Impact=1.0))]
    s.run(6.6, script)
    s.close()


def scenario_locked(out):
    s = Studio(os.path.join(out, "door_locked.wav"))
    s.run(2.8, [(.2, lambda: s.play("event:/Mechanism/Door/Locked", (.3, 0, 1.0))),
                (1.4, lambda: s.play("event:/Mechanism/Door/Locked", (.3, 0, 1.0)))])
    s.close()


def scenario_room(out):
    """The room tone the player lives in: hum + air + one close fixture, Tension rising."""
    s = Studio(os.path.join(out, "room_tension.wav"))
    s.set_global("Zone", 1)
    s.set_global("Tension", 0)
    keep = [s.play("event:/Ambience/HumBed", keep=True), s.play("event:/Ambience/AirBed", keep=True),
            s.play("event:/Ambience/Fixture", (1.2, 1.1, 2.0), keep=True, Level=1.0)]

    def each(t):
        s.set_global("Tension", min(1.0, max(0.0, (t - 5.0) / 6.0)))

    s.run(14.0, (), each)
    for k in keep:
        s.stop(k)
    s.close()


def scenario_zones(out):
    s = Studio(os.path.join(out, "air_zones.wav"))
    s.set_global("Zone", 1)
    air = s.play("event:/Ambience/AirBed", keep=True)
    s.run(12.0, [(6.0, lambda: s.set_global("Zone", 2))])
    s.stop(air)
    s.close()


def scenario_window(out):
    s = Studio(os.path.join(out, "window_break.wav"))
    pane = (0.0, .2, 1.2)
    state = {}

    def hold():
        state["stress"] = s.play("event:/Mechanism/Window/Stress", pane, keep=True, Progress=0)

    def each(t):
        if "stress" in state:
            s.set(state["stress"], Progress=min(1.0, max(0.0, (t - .3) / 3.0)))

    def release():
        s.stop(state.pop("stress"))

    s.run(5.5, [(.3, hold), (1.35, lambda: s.play("event:/Mechanism/Window/Crack", pane)),
                (2.4, lambda: s.play("event:/Mechanism/Window/Crack", pane)), (3.3, release),
                (3.3, lambda: s.play("event:/Mechanism/Window/Shatter", pane))], each)
    s.close()


def scenario_lamp(out):
    s = Studio(os.path.join(out, "fixture_strike.wav"))
    lamp = (0.6, 1.2, 1.5)
    state = {}

    def on():
        state["hum"] = s.play("event:/Ambience/Fixture", lamp, keep=True, Level=0.0)

    def each(t):
        if "hum" in state:
            s.set(state["hum"], Level=min(1.0, max(0.0, (t - .5) / .4)))

    s.run(4.0, [(.2, lambda: s.play("event:/Ambience/FixtureEvent", lamp, FixtureEvent=0)), (.25, on),
                (2.4, lambda: s.play("event:/Ambience/FixtureEvent", lamp, FixtureEvent=1))], each)
    s.stop(state["hum"])
    s.close()


def scenario_keys(out):
    s = Studio(os.path.join(out, "key_pickup.wav"))
    s.run(1.6, [(.2, lambda: s.play("event:/Foley/Player/KeyPickup"))])
    s.close()


def render(out):
    os.makedirs(out, exist_ok=True)
    scenario_steps(out, "steps_walk_dry", 0, 0, 0.0, 8, .55)
    scenario_steps(out, "steps_walk_damp", 0, 0, .4, 8, .55)
    scenario_steps(out, "steps_walk_soaked", 0, 0, .9, 8, .55)
    scenario_steps(out, "steps_run_damp", 0, 1, .4, 12, .34)
    scenario_steps(out, "steps_tile_walk", 1, 0, .15, 8, .55)
    scenario_relay(out)
    scenario_door(out)
    scenario_relay_door(out)
    scenario_locked(out)
    scenario_room(out)
    scenario_zones(out)
    scenario_window(out)
    scenario_lamp(out)
    scenario_keys(out)
    print("rendered into", out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "contract"
    if cmd == "contract":
        contract()
    elif cmd == "render":
        render(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "build", "renders"))
