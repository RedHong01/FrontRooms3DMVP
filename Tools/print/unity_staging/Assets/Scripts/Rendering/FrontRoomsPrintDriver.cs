using System;
using UnityEngine;

/// <summary>
/// Drives the moving layer of the "sandwich" wallpaper (Documentation/research/
/// wallpaper_motion). The print is ink only: FrontRooms/Surface multiplies it into
/// the albedo, and the paper layer alone supplies normal, smoothness and cavity, so
/// light and reflections never see the motion. This component only writes globals:
///   _FR_Print       Texture2DArray, one 0.75 x 1.125 m roll tile per slice
///                   (R ink density, G cream, B phosphor glow ink; linear)
///   _FR_PrintClock  x frame position [0, n), y n, z per-roll phase (frames), w live mix
///   _FR_PrintWarp   x amplitude (m), y phase (rad, [0, 2pi)), z wavelength (m), w enable
/// With w = 0 (edit mode, look-dev captures, before the array is bound) the shader
/// shows the material's static frame 0, so a wall is never blank.
///
/// Motion (Red, 2026-10-02): discrete jumps by default (long holds, then a short
/// blend to the next keyframe); slow continuous crawl only for scripted beats. Both
/// are IMotion modules, so later modes plug in without touching the binding.
/// All clocks are doubles wrapped on the CPU; the shader never reads _Time.
/// </summary>
public sealed class FrontRoomsPrintDriver : MonoBehaviour
{
    /// <summary>Resources path of the packed print (Tools/print/print_tool.py pack).</summary>
    public const string DefaultPrint = "Print/FR_Print_HardEdge";
    const string ReduceMotionKey = "FrontRooms.ReduceWallMotion";
    const double Tau = Math.PI * 2.0;

    static readonly int PrintId = Shader.PropertyToID("_FR_Print");
    static readonly int ClockId = Shader.PropertyToID("_FR_PrintClock");
    static readonly int WarpId = Shader.PropertyToID("_FR_PrintWarp");

    public static FrontRoomsPrintDriver Instance { get; private set; }

    static int reduceMotion = -1;

    /// <summary>Accessibility: freezes the print (no jumps, no crawl). Persisted in PlayerPrefs.</summary>
    public static bool ReduceMotion
    {
        get
        {
            if (reduceMotion < 0) reduceMotion = PlayerPrefs.GetInt(ReduceMotionKey, 0);
            return reduceMotion == 1;
        }
        set
        {
            reduceMotion = value ? 1 : 0;
            PlayerPrefs.SetInt(ReduceMotionKey, reduceMotion);
            PlayerPrefs.Save();
        }
    }

    /// <summary>Everything the print shows, in CPU doubles. Modules edit it; the driver sends it.</summary>
    public struct State
    {
        public double Frame;          // keyframe position, [0, Count)
        public int Count;             // slices in the array
        public double WarpPhase;      // radians, [0, 2pi)
        public float WarpAmplitude;   // metres
        public float WarpWavelength;  // metres
        public float WarpEnable;      // 0..1
    }

    /// <summary>A way for the print to move. Return false when a one-shot beat has finished.</summary>
    public interface IMotion
    {
        bool Tick(ref State s, double dt);
    }

    [Serializable]
    public struct Drift
    {
        [Tooltip("Displacement in metres. Subliminal: 0.002-0.006.")] public float amplitude;
        [Tooltip("Wavelength in metres; rounded to whole cycles per 3 m in the shader.")] public float wavelength;
        [Tooltip("Phase speed in rad/s. Subliminal: 0.05-0.3.")] public float phaseRate;
    }

    [SerializeField] Texture2DArray printArray;
    [SerializeField] HoldAndJump jumps = new HoldAndJump();
    [Tooltip("Always-on drift. Beats scale its amplitude and speed but keep its wavelength.")]
    [SerializeField] Drift subliminal = new Drift { amplitude = 0.004f, wavelength = 1.5f, phaseRate = 0.15f };
    [Tooltip("Frames of phase between neighbouring rolls (hashed per strip & 3). 0 keeps every roll in step; a non-zero value leaves rolls part-way between keyframes during holds.")]
    [SerializeField] float rollPhaseFrames = 0f;

    /// <summary>Stops all print time (e.g. on Caught or pause).</summary>
    public bool Frozen { get; set; }

    State state;
    IMotion beat;   // a scripted beat (e.g. Crawl) runs on top of the jumps until it finishes

    public Texture2DArray Print => printArray;
    public int Count => state.Count;
    public double Frame => state.Frame;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        // Promoting the packed print into Resources is the switch: no array, no driver.
        if (Instance != null || FindAnyObjectByType<FrontRoomsPrintDriver>() != null) return;
        var tex = Resources.Load<Texture2DArray>(DefaultPrint);
        if (tex == null) return;
        var go = new GameObject("FrontRooms Print");
        DontDestroyOnLoad(go);
        go.AddComponent<FrontRoomsPrintDriver>().Bind(tex);
    }

    /// <summary>Binds a print array and starts at frame 0 (which matches the static _PrintTex).</summary>
    public void Bind(Texture2DArray array)
    {
        printArray = array;
        state = new State { Count = array != null ? array.depth : 0 };
        jumps.Reset();
        if (array != null) Shader.SetGlobalTexture(PrintId, array);
        Push(array != null ? 1f : 0f);
    }

    /// <summary>Blends to the next keyframe now (adjacent slices only, so nothing in between flashes).</summary>
    public void JumpNext()
    {
        if (!ReduceMotion) jumps.BeginBlend(state);
    }

    /// <summary>
    /// Cuts straight to a slice with no blend. Only use while the change is masked
    /// (unseen, or during a lamp dropout): a global cut on visible walls reads as a pop.
    /// </summary>
    public void CutTo(int slice)
    {
        if (state.Count == 0) return;
        state.Frame = Wrap(slice, state.Count);
        jumps.Reset();
    }

    /// <summary>Runs a scripted beat (e.g. a Crawl) over the jumps until it finishes.</summary>
    public void Play(IMotion motion)
    {
        if (!ReduceMotion) beat = motion;
    }

    public void StopBeat() => beat = null;

    void OnEnable()
    {
        Instance = this;
        if (printArray != null && state.Count == 0) Bind(printArray);
    }

    void OnDisable()
    {
        if (Instance == this) Instance = null;
        // Globals outlive play mode in the editor: fall back to the static frame 0.
        Shader.SetGlobalVector(ClockId, Vector4.zero);
        Shader.SetGlobalVector(WarpId, Vector4.zero);
    }

    void Update()
    {
        if (printArray == null || state.Count == 0) return;
        double dt = Frozen ? 0.0 : Time.deltaTime;

        if (ReduceMotion)
        {
            state.WarpEnable = 0f;
        }
        else
        {
            jumps.Tick(ref state, dt);
            state.WarpAmplitude = subliminal.amplitude;
            state.WarpWavelength = subliminal.wavelength;
            state.WarpEnable = 1f;
            state.WarpPhase += subliminal.phaseRate * dt;
            if (beat != null && !beat.Tick(ref state, dt)) beat = null;
        }

        state.Frame = Wrap(state.Frame, state.Count);
        state.WarpPhase = Wrap(state.WarpPhase, Tau);
        Push(1f);
    }

    void Push(float live)
    {
        Shader.SetGlobalVector(ClockId, new Vector4((float)state.Frame, state.Count, rollPhaseFrames, live));
        Shader.SetGlobalVector(WarpId, new Vector4(state.WarpAmplitude, (float)state.WarpPhase,
            Mathf.Max(state.WarpWavelength, 0.05f), state.WarpEnable));
    }

    public static double Wrap(double x, double n) => n <= 0 ? 0 : x - n * Math.Floor(x / n);

    /// <summary>
    /// The default mode: hold a keyframe for a long, random time, then blend to the next
    /// one over a second or so. Blends only go to the adjacent slice, so the packed order
    /// of the keyframes is the story (K00 original, K01 one thing wrong, ...).
    /// </summary>
    [Serializable]
    public sealed class HoldAndJump : IMotion
    {
        [Tooltip("Seconds to hold a keyframe before the next jump (random in range).")]
        public Vector2 holdSeconds = new Vector2(45f, 90f);
        [Tooltip("Seconds a jump takes to blend into the next keyframe.")]
        public float blendSeconds = 1.2f;
        [Tooltip("Off: never jump on its own; the game calls JumpNext or CutTo instead.")]
        public bool automatic = true;
        public int seed = 1990;

        System.Random rng;
        double holdLeft, from, t = -1;

        public void Reset()
        {
            t = -1;
            holdLeft = NextHold();
        }

        public void BeginBlend(State s)
        {
            if (t >= 0 || s.Count < 2) return;
            from = Math.Round(s.Frame);
            t = 0;
        }

        public bool Tick(ref State s, double dt)
        {
            if (s.Count < 2) return true;
            if (t >= 0)
            {
                t = Math.Min(1.0, t + dt / Math.Max(blendSeconds, 0.01f));
                s.Frame = from + t * t * (3.0 - 2.0 * t);   // smoothstep: no snap at either end
                if (t >= 1.0)
                {
                    s.Frame = Wrap(from + 1.0, s.Count);
                    t = -1;
                    holdLeft = NextHold();
                }
                return true;
            }
            if (automatic && (holdLeft -= dt) <= 0) BeginBlend(s);
            return true;
        }

        double NextHold()
        {
            rng ??= new System.Random(seed);
            return holdSeconds.x + rng.NextDouble() * Math.Max(0f, holdSeconds.y - holdSeconds.x);
        }
    }

    /// <summary>
    /// A scripted beat: the print slowly crawls (a divergence-free warp, so the ink keeps
    /// its area and reads as moving, not swelling), fading in and out. It can also drift
    /// the keyframe. Keep the print speed under about 0.12 m/s (amplitude x phase rate x 3).
    /// The beat keeps the driver's drift wavelength: the shader rounds the wavelength to
    /// whole cycles per 3 m, so changing it while the warp is visible makes the print jump.
    /// </summary>
    [Serializable]
    public sealed class Crawl : IMotion
    {
        public float seconds = 8f;
        public float fadeSeconds = 1.5f;
        public float amplitude = 0.02f;
        public float phaseRate = 1.2f;
        [Tooltip("Keyframes per second to drift through during the beat (0 = keep the keyframe).")]
        public float framesPerSecond;

        double time;

        public bool Tick(ref State s, double dt)
        {
            time += dt;
            float fade = Mathf.Max(fadeSeconds, 0.01f);
            float env = Mathf.Clamp01((float)time / fade) * Mathf.Clamp01((seconds - (float)time) / fade);
            // Blend from the subliminal drift the driver already set towards this beat.
            s.WarpAmplitude = Mathf.Lerp(s.WarpAmplitude, amplitude, env);
            s.WarpEnable = 1f;
            s.WarpPhase += phaseRate * env * dt;
            s.Frame += framesPerSecond * env * dt;
            return time < seconds;
        }
    }
}
