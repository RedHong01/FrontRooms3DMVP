// FrontRooms FMOD builder. Interprets SPEC (prepended by fmod_frontrooms.py).
// Idempotent: deletes what it generated last time, then rebuilds and saves
// only if every step succeeded.

var ws = studio.project.workspace;
var errors = [], warnings = [];
var GP = {}, BUS = {}, BANK = {}, ASSET = {};

function log(m) { console.log("FR> " + m); }
function attempt(label, fn, optional) {
    try { return fn(); } catch (e) {
        (optional ? warnings : errors).push(label + ": " + e);
        log((optional ? "WARN " : "ERROR ") + label + ": " + e);
        return null;
    }
}

// ------------------------------------------------------------------ cleanup
function cleanup() {
    SPEC.eventRoots.forEach(function (name) {
        var f = ws.masterEventFolder.getItem(name);
        if (f) studio.project.deleteObject(f);
    });
    Object.keys(SPEC.params).forEach(function (name) {
        var p = studio.project.lookup("parameter:/" + name);
        if (p) studio.project.deleteObject(p);
    });
    Object.keys(SPEC.vcas).forEach(function (name) {
        var v = studio.project.lookup("vca:/" + name);
        if (v) studio.project.deleteObject(v);
    });
    var r = studio.project.lookup("bus:/" + SPEC.reverb.name);
    if (r) studio.project.deleteObject(r);
    var stock = studio.project.lookup("bus:/Reverb");          // unused return from the new-project template
    if (stock && stock.isOfType("MixerReturn")) studio.project.deleteObject(stock);
    SPEC.buses.slice().reverse().forEach(function (b) {
        var path = b.parent ? (b.parent + "/" + b.name) : b.name;
        var o = studio.project.lookup("bus:/" + path);
        if (o) studio.project.deleteObject(o);
    });
    SPEC.banks.forEach(function (name) {
        var o = studio.project.lookup("bank:/" + name);
        if (o) studio.project.deleteObject(o);
    });
}

// ------------------------------------------------------------------ project objects
function makeParams() {
    var T = studio.project.parameterType;
    Object.keys(SPEC.params).forEach(function (name) {
        var d = SPEC.params[name];
        var def = { name: name, type: T.User, min: d.min, max: d.max };
        if (d.labels) { def.type = T.UserEnumeration; def.min = 0; def.max = d.labels.length - 1; def.enumerationLabels = d.labels; }
        else if (d.discrete) { def.type = T.UserDiscrete; }
        var gp = ws.addGameParameter(def);
        if (d.isGlobal) gp.isGlobal = true;
        if (d.initial !== undefined) gp.initialValue = d.initial;
        GP[name] = gp;
    });
    log("parameters: " + Object.keys(GP).length);
}

function makeMixer() {
    SPEC.buses.forEach(function (b) {
        var g = studio.project.create("MixerGroup");
        g.name = b.name;
        g.output = b.parent ? BUS[b.parent] : ws.mixer.masterBus;
        if (b.volume !== undefined) g.volume = b.volume;
        BUS[b.name] = g;
    });
    var rv = SPEC.reverb;
    var ret = studio.project.create("MixerReturn");
    ret.name = rv.name;
    ret.output = ws.mixer.masterBus;
    var fx = ret.effectChain.addEffect("SFXReverbEffect");
    fx.highCut = 5000;
    fx.dryLevel = -80;
    // 3 m carpeted cells: first reflections arrive within ~10 ms, so no 20/40 ms default pre-delay (3D-14).
    attempt("reverb timing", function () { fx.earlyDelay = 1; fx.lateDelay = 7; fx.hfDecayRatio = 40; }, true);
    automate(fx, { prop: "decayTime", param: "Zone", points: rv.decay });
    automate(fx, { prop: "wetLevel", param: "Zone", points: rv.wet });
    Object.keys(rv.sends).forEach(function (busName) {
        attempt("send " + busName, function () {
            var send = studio.project.create("MixerSend");
            send.mixerReturn = ret;
            send.level = rv.sends[busName];
            BUS[busName].effectChain.relationships.effects.add(send);
        }, true);
    });
    Object.keys(SPEC.vcas).forEach(function (name) {
        attempt("vca " + name, function () {
            var v = studio.project.create("MixerVCA");
            v.name = name;
            v.mixer = ws.mixer;
            SPEC.vcas[name].forEach(function (busName) { v.relationships.slaves.add(BUS[busName]); });
        }, true);
    });
    log("buses: " + Object.keys(BUS).length + ", reverb return + sends, vcas: " + Object.keys(SPEC.vcas).length);
}

// Safety ceiling on the master bus (added once; the builder never removes it).
function masterLimiter() {
    var master = ws.mixer.masterBus;
    if (findEffect(master, "LimiterEffect")) return;
    var lim = master.effectChain.addEffect("LimiterEffect");
    attempt("limiter ceiling", function () { lim.ceiling = -1; }, true);
    log("master limiter added");
}

function makeBanks() {
    BANK["Master Bank"] = studio.project.lookup("bank:/Master Bank") || studio.project.lookup("bank:/Master");
    SPEC.banks.forEach(function (name) {
        var b = studio.project.create("Bank");
        b.name = name;
        b.folder = ws.masterBankFolder;
        BANK[name] = b;
    });
}

// ------------------------------------------------------------------ assets
function asset(rel) {
    if (ASSET[rel]) return ASSET[rel];
    var a = ws.masterAssetFolder.getAsset(rel);
    if (!a) {
        a = studio.project.importAudioFile(SPEC.sources[rel]);
        if (!a) throw new Error("import failed " + rel);
        if (a.getAssetPath() !== rel) a.setAssetPath(rel);
    }
    ASSET[rel] = a;
    return a;
}

// ------------------------------------------------------------------ events
function folderFor(parts) {
    var parent = ws.masterEventFolder;
    parts.forEach(function (name) {
        var f = parent.getItem(name);
        if (!f) {
            f = studio.project.create("EventFolder");
            f.name = name;
            f.folder = parent;
        }
        parent = f;
    });
    return parent;
}

function findEffect(mixerGroup, entity) {
    var fx = mixerGroup.effectChain.effects;
    for (var i = 0; i < fx.length; i++) if (fx[i].isOfType(entity)) return fx[i];
    return null;
}

function automate(obj, a) {
    var au = obj.addAutomator(a.prop);
    var c = au.addAutomationCurve(GP[a.param]);
    a.points.forEach(function (p) { c.addAutomationPoint(p[0], p[1]); });
}

// Loop length of the event being built: every looping instrument is stretched to it and the event
// gets a loop region over it, so loops never stop on their own (3D audit 3D-03: an async loop with
// no region plays one pass and the event goes STOPPED with its handle still valid).
var CUR_LOOP = 0;

function addSound(ev, track, s) {
    var len = 0;
    s.files.forEach(function (f) { len = Math.max(len, SPEC.durations[f]); });
    if (s.loop && CUR_LOOP) len = CUR_LOOP - (s.start || 0);
    var snd;
    if (s.files.length === 1) {
        snd = track.addSound(ev.timeline, "SingleSound", s.start || 0, len);
        snd.audioFile = asset(s.files[0]);
    } else {
        snd = track.addSound(ev.timeline, "MultiSound", s.start || 0, len);
        s.files.forEach(function (f) {
            var c = studio.project.create("SingleSound");
            c.audioFile = asset(f);
            c.owner = snd;
        });
    }
    snd.isAsync = true;
    if (s.loop) snd.looping = true;
    if (s.volume !== undefined) snd.volume = s.volume;
    if (s.pitch !== undefined) snd.pitch = s.pitch;
    (s.cond || []).forEach(function (c) {
        var gp = GP[c[0]];
        if (typeof c[1] !== "string") { snd.addParameterCondition(gp, c[1], c[2]); return; }
        try { snd.addParameterCondition(gp.presetOwner, c[1]); }
        catch (e1) {
            var idx = SPEC.params[c[0]].labels.indexOf(c[1]);
            snd.addParameterCondition(gp, idx, idx);
        }
    });
    if (s.randPitch) snd.addModulator("RandomizerModulator", "pitch").amount = s.randPitch;
    if (s.randVol) snd.addModulator("RandomizerModulator", "volume").amount = s.randVol;
    (s.auto || []).forEach(function (a) { automate(snd, a); });
    return snd;
}

function makeEvent(e) {
    var parts = e.path.split("/");
    var name = parts.pop();
    var ev = ws.addEvent(name, !!e.spatial);
    ev.folder = folderFor(parts);
    if (e.note) ev.note = e.note;
    if (e.spatial) {
        var sp = findEffect(ev.masterTrack.mixerGroup, "SpatialiserEffect");
        sp.minimumDistance = e.min;
        sp.maximumDistance = e.max;
        // The spatialiser's own min/max are ignored unless it overrides the event range, so set the event's
        // range (3D-01: every event ran at the default 1-20 m). Max first so min never exceeds it.
        attempt("event range " + e.path, function () {
            ev.automatableProperties.maximumDistance = e.max;
            ev.automatableProperties.minimumDistance = e.min;
        }, true);
        // Inverse Tapered unless the SPEC asks otherwise (3D-02: the default Linear Squared barely falls off
        // near and drops off a cliff far). Lamps keep Linear Squared on purpose (a fade by max).
        sp.distanceRolloffType = e.rolloff !== undefined ? e.rolloff : 3;
        // Width (3D-06): with Auto extent and 0 min extent anything 45-90 deg off-centre sat in one ear.
        attempt("extent " + e.path, function () {
            sp.extentMode = 1;                       // User
            sp.soundSize = e.size !== undefined ? e.size : 2 * e.min;
            sp.minimumExtent = e.extent !== undefined ? e.extent : 120;
        }, true);
    }
    ev.mixerInput.output = BUS[e.bus];
    ev.relationships.banks.add(BANK[e.bank]);
    (e.params || []).forEach(function (p) { ev.addGameParameter(GP[p]); });
    var loopLen = 0;
    (e.tracks || []).forEach(function (t) { (t.sounds || []).forEach(function (s) {
        if (s.loop) s.files.forEach(function (f) { loopLen = Math.max(loopLen, (s.start || 0) + SPEC.durations[f]); });
    }); });
    CUR_LOOP = e.markers ? 0 : loopLen;
    (e.tracks || []).forEach(function (t) {
        var track = ev.addGroupTrack(t.name);
        (t.sounds || []).forEach(function (s) { addSound(ev, track, s); });
        (t.auto || []).forEach(function (a) { automate(track.mixerGroup, a); });
    });
    var master = ev.masterTrack.mixerGroup;
    (e.masterAuto || []).forEach(function (a) { automate(master, a); });
    if (e.ahdsr) {
        var m = master.addModulator("ADSRModulator", "volume");
        m.initialValue = -80; m.attackTime = e.ahdsr[0]; m.holdTime = 0; m.decayTime = 0;
        m.peakValue = 0; m.sustainValue = 0; m.releaseTime = e.ahdsr[1]; m.finalValue = -80;
    }
    if (e.occlusion) {
        var eq = master.effectChain.addEffect("MultibandEqEffect");
        eq.filterTypeA = 2;            // low-pass 24 dB
        eq.frequencyA = 22000;
        automate(eq, { prop: "frequencyA", param: "Occlusion", points: [[0, 22000], [.5, 2500], [1, 700]] });
    }
    if (CUR_LOOP) ev.addMarkerTrack().addRegion(0, CUR_LOOP, "loop", studio.project.regionLoopMode.Looping);
    CUR_LOOP = 0;
    if (e.markers) {
        var mt = ev.addMarkerTrack();
        var r = e.markers.region;
        mt.addRegion(r[0], r[1], r[2], studio.project.regionLoopMode.Looping);
        e.markers.named.forEach(function (n) { mt.addNamedMarker(n[0], n[1]); });
        attempt("tempo marker " + e.path, function () {
            var tm = studio.project.create("TempoMarker");
            tm.position = 0;
            tm.tempo = e.markers.tempo;
            tm.timeSignatureNumerator = 4;
            tm.timeSignatureDenominator = 4;
            tm.timeline = ev.timeline;
            mt.relationships.markers.add(tm);
        }, true);
    }
    return ev;
}

// Drop assets no event uses any more (replaced placeholders). Only runs after
// every event rebuilt cleanly, so nothing still referenced can be removed.
function prune() {
    var removed = 0;
    studio.project.model.AudioFile.findInstances().forEach(function (a) {
        if (!SPEC.sources[a.getAssetPath()]) { studio.project.deleteObject(a); removed++; }
    });
    log("pruned " + removed + " unused asset(s)");
}

// ------------------------------------------------------------------ run
log("cleanup");
attempt("cleanup", cleanup);
attempt("params", makeParams);
attempt("mixer", makeMixer);
attempt("master limiter", masterLimiter, true);
attempt("banks", makeBanks);
var made = 0;
SPEC.events.forEach(function (e) {
    if (attempt("event " + e.path, function () { return makeEvent(e); })) made++;
});
log("events built: " + made + " / " + SPEC.events.length);
if (warnings.length) { log(warnings.length + " warning(s):"); warnings.forEach(function (x) { log("  " + x); }); }
if (errors.length) {
    log("NOT SAVED - " + errors.length + " error(s):");
    errors.forEach(function (x) { log("  " + x); });
} else {
    attempt("prune", prune, true);
    studio.project.save();
    log("saved " + studio.project.filePath);
    var ok = studio.project.build();
    log("build " + (ok ? "OK" : "FAILED"));
}
