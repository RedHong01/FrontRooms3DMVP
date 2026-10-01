using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Data-driven Foley banks for the prototype. A step is assembled from an
/// impact, a surface texture and a quiet body/cloth layer. Banks are selected
/// by actor, movement state and surface, then sampled without immediate repeats.
/// The short clips are generated once at startup so the WebGL build has no
/// streaming callback or file lookup on the movement hot path.
/// </summary>
public enum FrontRoomsFoleyActor
{
    Player,
    Hunter
}

public enum FrontRoomsFoleySurface
{
    Carpet,
    Tile,
    Concrete,
    Metal
}

public sealed class FrontRoomsFoley
{
    public sealed class StepSelection
    {
        public AudioClip impact;
        public AudioClip texture;
        public AudioClip cloth;
        public float pitch;
    }

    public sealed class DoorSet
    {
        public AudioClip latch;
        public AudioClip hinge;
        public AudioClip travel;
        public AudioClip slam;
        public AudioClip breakImpact;
    }

    const int Rate = 44100;
    const int StepVariations = 6;
    readonly Dictionary<int, AudioClip[]> impactBanks = new Dictionary<int, AudioClip[]>();
    readonly Dictionary<int, AudioClip[]> textureBanks = new Dictionary<int, AudioClip[]>();
    readonly Dictionary<int, AudioClip[]> clothBanks = new Dictionary<int, AudioClip[]>();
    readonly Dictionary<int, int> lastChoices = new Dictionary<int, int>();
    readonly System.Random random = new System.Random(20261001);

    public DoorSet Doors { get; private set; }

    public FrontRoomsFoley(AudioClip recordedHinge)
    {
        Doors = new DoorSet
        {
            latch = DoorLatch(),
            hinge = recordedHinge != null ? recordedHinge : DoorHinge(),
            travel = DoorTravel(),
            slam = DoorSlam(),
            breakImpact = DoorBreak()
        };
        BuildStepBanks();
    }

    public StepSelection PickStep(FrontRoomsFoleyActor actor, FrontRoomsFoleySurface surface, bool running)
    {
        var key = BankKey(actor, surface, running);
        if (!impactBanks.TryGetValue(key, out var impact))
        {
            surface = FrontRoomsFoleySurface.Carpet;
            key = BankKey(actor, surface, running);
            impact = impactBanks[key];
        }

        var index = NextIndex(key, impact.Length);
        var pitch = actor == FrontRoomsFoleyActor.Hunter
            ? Mathf.Lerp(.94f, 1.02f, (float)random.NextDouble())
            : Mathf.Lerp(.97f, 1.04f, (float)random.NextDouble());
        return new StepSelection
        {
            impact = impact[index],
            texture = textureBanks[key][index],
            cloth = clothBanks[key][index],
            pitch = pitch
        };
    }

    void BuildStepBanks()
    {
        foreach (FrontRoomsFoleyActor actor in Enum.GetValues(typeof(FrontRoomsFoleyActor)))
        foreach (FrontRoomsFoleySurface surface in Enum.GetValues(typeof(FrontRoomsFoleySurface)))
        for (var running = 0; running <= 1; running++)
        {
            var isRunning = running == 1;
            var key = BankKey(actor, surface, isRunning);
            var impacts = new AudioClip[StepVariations];
            var textures = new AudioClip[StepVariations];
            var cloth = new AudioClip[StepVariations];
            for (var i = 0; i < StepVariations; i++)
            {
                var seed = 1000 + key * 31 + i * 97;
                impacts[i] = StepImpact(actor, surface, isRunning, seed);
                textures[i] = StepTexture(actor, surface, isRunning, seed + 7);
                cloth[i] = StepCloth(actor, isRunning, seed + 13);
            }
            impactBanks[key] = impacts;
            textureBanks[key] = textures;
            clothBanks[key] = cloth;
            lastChoices[key] = -1;
        }
    }

    int BankKey(FrontRoomsFoleyActor actor, FrontRoomsFoleySurface surface, bool running)
    {
        return (((int)actor * 4) + (int)surface) * 2 + (running ? 1 : 0);
    }

    int NextIndex(int key, int count)
    {
        if (count <= 1) return 0;
        var previous = lastChoices.TryGetValue(key, out var last) ? last : -1;
        var next = random.Next(count - 1);
        if (next >= previous) next++;
        lastChoices[key] = next;
        return next;
    }

    static float SurfaceBody(FrontRoomsFoleySurface surface)
    {
        switch (surface)
        {
            case FrontRoomsFoleySurface.Tile: return 1.18f;
            case FrontRoomsFoleySurface.Concrete: return 1.05f;
            case FrontRoomsFoleySurface.Metal: return 1.28f;
            default: return .72f;
        }
    }

    static float SurfaceRing(FrontRoomsFoleySurface surface)
    {
        switch (surface)
        {
            case FrontRoomsFoleySurface.Tile: return .16f;
            case FrontRoomsFoleySurface.Concrete: return .10f;
            case FrontRoomsFoleySurface.Metal: return .28f;
            default: return .035f;
        }
    }

    AudioClip StepImpact(FrontRoomsFoleyActor actor, FrontRoomsFoleySurface surface, bool running, int seed)
    {
        var hunter = actor == FrontRoomsFoleyActor.Hunter;
        var seconds = hunter ? .22f : (running ? .12f : .15f);
        var bodyHz = hunter ? 62f : (running ? 116f : 142f);
        var amplitude = (hunter ? .50f : (running ? .31f : .23f)) * SurfaceBody(surface);
        var ring = SurfaceRing(surface);
        var noise = NoiseBuffer(seconds, seed);
        var phase = (seed % 29) * .17f;
        return Make("foley-" + actor + "-" + surface + (running ? "-run" : "-walk") + "-impact-" + seed, seconds, t =>
        {
            var attack = Mathf.Exp(-t * (running ? 78f : 62f));
            var body = Mathf.Sin(2f * Mathf.PI * bodyHz * t + phase) * attack;
            var heel = Mathf.Sin(2f * Mathf.PI * (bodyHz * 1.93f) * t + phase * .7f) * Mathf.Exp(-t * 94f);
            var texture = noise[SampleIndex(t, noise.Length)] * Mathf.Exp(-t * (hunter ? 14f : 38f));
            var resonance = ring * Mathf.Sin(2f * Mathf.PI * (bodyHz * 4.2f) * t) * Mathf.Exp(-t * 20f);
            return amplitude * (.70f * body + .18f * heel + .18f * texture) + resonance;
        });
    }

    AudioClip StepTexture(FrontRoomsFoleyActor actor, FrontRoomsFoleySurface surface, bool running, int seed)
    {
        var hunter = actor == FrontRoomsFoleyActor.Hunter;
        var seconds = hunter ? .25f : .18f;
        var noise = NoiseBuffer(seconds, seed);
        var high = surface == FrontRoomsFoleySurface.Carpet ? 0f : surface == FrontRoomsFoleySurface.Metal ? .16f : .08f;
        var amount = hunter ? .16f : (running ? .12f : .09f);
        return Make("foley-" + actor + "-" + surface + "-texture-" + seed, seconds, t =>
        {
            var env = Mathf.Exp(-t * (hunter ? 13f : 28f));
            var grit = noise[SampleIndex(t, noise.Length)] * env;
            var scrape = Mathf.Sin(2f * Mathf.PI * (180f + seed % 80) * t) * Mathf.Exp(-t * 22f);
            return amount * (grit + high * scrape);
        });
    }

    AudioClip StepCloth(FrontRoomsFoleyActor actor, bool running, int seed)
    {
        var seconds = running ? .14f : .17f;
        var noise = NoiseBuffer(seconds, seed);
        var amount = actor == FrontRoomsFoleyActor.Hunter ? .085f : .055f;
        return Make("foley-" + actor + "-cloth-" + seed, seconds, t =>
        {
            var env = Mathf.Exp(-t * 30f);
            var rustle = noise[SampleIndex(t, noise.Length)] * env;
            var low = Mathf.Sin(2f * Mathf.PI * 210f * t) * Mathf.Exp(-t * 25f);
            return amount * (rustle + .18f * low);
        });
    }

    AudioClip DoorLatch()
    {
        return Make("foley-door-latch", .13f, t =>
        {
            var click = Mathf.Sin(2f * Mathf.PI * 1060f * t) * Mathf.Exp(-t * 52f);
            var tick = .35f * Mathf.Sin(2f * Mathf.PI * 1780f * t) * Mathf.Exp(-t * 96f);
            return .38f * click + tick;
        });
    }

    AudioClip DoorHinge()
    {
        var noise = NoiseBuffer(.58f, 812);
        return Make("foley-door-hinge-fallback", .58f, t =>
        {
            var body = Mathf.Sin(2f * Mathf.PI * (172f - 56f * t) * t) * Mathf.Exp(-t * 2.8f);
            var scrape = noise[SampleIndex(t, noise.Length)] * Mathf.Exp(-t * 4f);
            return .22f * body + .08f * scrape;
        });
    }

    AudioClip DoorTravel()
    {
        var noise = NoiseBuffer(.72f, 917);
        return Make("foley-door-travel", .72f, t =>
        {
            var start = Mathf.Clamp01((t - .06f) / .12f);
            var movement = start * Mathf.Exp(-t * 2.5f);
            var body = Mathf.Sin(2f * Mathf.PI * (118f - 40f * t) * t) * movement;
            var friction = noise[SampleIndex(t, noise.Length)] * movement * .75f;
            var settle = Mathf.Sin(2f * Mathf.PI * 71f * (t - .58f)) * Mathf.Exp(-(t - .58f) * 24f);
            if (t < .58f) settle = 0f;
            return .16f * body + .07f * friction + .24f * settle;
        });
    }

    AudioClip DoorSlam()
    {
        var noise = NoiseBuffer(.34f, 1017);
        return Make("foley-door-slam", .34f, t =>
            .70f * Mathf.Sin(2f * Mathf.PI * 58f * t) * Mathf.Exp(-t * 17f) +
            .30f * noise[SampleIndex(t, noise.Length)] * Mathf.Exp(-t * 38f));
    }

    AudioClip DoorBreak()
    {
        var noise = NoiseBuffer(.28f, 1117);
        return Make("foley-door-break", .28f, t =>
            .72f * Mathf.Sin(2f * Mathf.PI * 48f * t) * Mathf.Exp(-t * 16f) +
            .42f * noise[SampleIndex(t, noise.Length)] * Mathf.Exp(-t * 28f));
    }

    static int SampleIndex(float t, int length)
    {
        return Mathf.Clamp(Mathf.FloorToInt(t * Rate), 0, Mathf.Max(0, length - 1));
    }

    static float[] NoiseBuffer(float seconds, int seed)
    {
        var random = new System.Random(seed);
        var data = new float[Mathf.CeilToInt(seconds * Rate)];
        for (var i = 0; i < data.Length; i++) data[i] = (float)(random.NextDouble() * 2.0 - 1.0);
        return data;
    }

    static AudioClip Make(string name, float seconds, Func<float, float> sample)
    {
        var count = Mathf.CeilToInt(seconds * Rate);
        var data = new float[count];
        for (var i = 0; i < count; i++) data[i] = Mathf.Clamp(sample(i / (float)Rate), -1f, 1f);
        var clip = AudioClip.Create(name, count, 1, Rate, false);
        clip.SetData(data, 0);
        return clip;
    }
}
