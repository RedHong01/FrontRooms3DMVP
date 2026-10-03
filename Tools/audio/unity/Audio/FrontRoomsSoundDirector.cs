using System.Collections.Generic;
using FMOD.Studio;
using FMODUnity;
using FrontRooms.Map;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FrontRooms.Audio
{
    /// <summary>
    /// Owns the FMOD side of the game without editing gameplay code:
    /// - starts the room tone (hum + air) and keeps the listener on the camera;
    /// - finds doors, lamps, the player and the Relay rig and attaches sound to them;
    /// - subscribes to the game's events (map run, doors, glass, keys, the Relay);
    /// - drives the global mix parameters (Tension, Zone) and the subjective layer.
    /// While FMOD is ready it mutes the legacy Unity audio; if FMOD is missing or
    /// fails, it stays inert and the legacy audio keeps playing.
    /// </summary>
    public sealed class FrontRoomsSoundDirector : MonoBehaviour
    {
        public static FrontRoomsSoundDirector Instance { get; private set; }

        [SerializeField] bool muteLegacyUnityAudio = true;
        [SerializeField] int fixtureVoices = 4;
        // Every fixture voice plays the same recorded loop. Started in the same frame they stay
        // sample-locked and add up in phase (6 lamps measured +12 dB over one, louder than the
        // player's steps). Starting them a non-multiple of the 4 s loop apart de-phases them.
        const float FixtureStagger = .53f;
        // FrontRoomsRoomStream names its double door's pivots so (read-only to the audio layer).
        const string StreamLeftHinge = "double door left hinge", StreamRightHinge = "double door right hinge";
        [SerializeField] float fixtureRadius = 10f;

        bool started, legacyRestored;
#if UNITY_WEBGL && !UNITY_EDITOR
        bool webUnlocked;
#endif
        float nextDiscover, nextFixtureUpdate, tension;
        EventInstance humBed, airBed, breath, heartbeat, windowStress;
        PARAMETER_ID staminaId, heartProximityId, stressProgressId;
        bool runIdsReady;

        FrontRoomsMapWorld map;
        FrontRoomsMapHunter relay;
        HunterState lastState = HunterState.Dormant;
        bool relayRevealed, caught;
        Transform listener;
        FrontRoomsPlayerFootsteps player;
        FrontRoomsRelaySound relayBody;
        Vector3 lastBlowDoor;
        int blowCount;
        float lastStressProgress;

        readonly HashSet<int> seen = new HashSet<int>();
        readonly List<GameObject> roots = new List<GameObject>(32);
        readonly List<Transform> scan = new List<Transform>(4096);

        // Lamps: discovered Light components, read-only.
        readonly List<Light> lamps = new List<Light>(256);
        readonly List<float> lampMax = new List<float>(256);
        readonly List<float> lampPrev = new List<float>(256);
        readonly List<float> lampNextEvent = new List<float>(256);
        EventInstance[] fixtureVoice;
        int[] fixtureLamp;
        float[] fixtureStartAt;
        bool[] fixtureStarted;
        int[] nearest;
        float[] nearestDistance;
        PARAMETER_ID fixtureLevelId;
        bool fixtureIdReady;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            var tracing = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-audioTrace") >= 0;
            if (Instance != null || (Application.isBatchMode && !tracing)) return;
            FrontRoomsFmod.Tracing = tracing;
            var go = new GameObject("FrontRooms Sound Director");
            DontDestroyOnLoad(go);
            go.AddComponent<FrontRoomsSoundDirector>();
            if (FrontRoomsAudioCapture.Requested) go.AddComponent<FrontRoomsAudioCapture>();
        }

        void Awake()
        {
            Instance = this;
            fixtureVoice = new EventInstance[fixtureVoices];
            fixtureLamp = new int[fixtureVoices];
            fixtureStartAt = new float[fixtureVoices];
            fixtureStarted = new bool[fixtureVoices];
            nearest = new int[fixtureVoices];
            nearestDistance = new float[fixtureVoices];
            for (var i = 0; i < fixtureVoices; i++) fixtureLamp[i] = -1;
        }

        void OnEnable()
        {
            FrontRooms3DGame.MapRunStarted += OnMapRunStarted;
            FrontRooms3DGame.MapRunEnded += OnMapRunEnded;
            FrontRooms3DGame.PlayerClimbed += OnPlayerClimbed;
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        void OnDisable()
        {
            FrontRooms3DGame.MapRunStarted -= OnMapRunStarted;
            FrontRooms3DGame.MapRunEnded -= OnMapRunEnded;
            FrontRooms3DGame.PlayerClimbed -= OnPlayerClimbed;
            SceneManager.sceneLoaded -= OnSceneLoaded;
            OnMapRunEnded();
            StopRoomTone(true);
            for (var i = 0; i < fixtureVoices; i++) FrontRoomsFmod.Stop(ref fixtureVoice[i], true);
            if (muteLegacyUnityAudio) AudioListener.volume = 1f;
            if (FrontRoomsFmod.Tracing)
            {
                var args = System.Environment.GetCommandLineArgs();
                var seed = System.Array.IndexOf(args, "-autopilotSeed");
                var name = seed >= 0 && seed + 1 < args.Length ? "trace_seed" + args[seed + 1] + ".txt" : "trace.txt";
                FrontRoomsFmod.WriteTrace(System.IO.Path.Combine(System.IO.Directory.GetParent(Application.dataPath).FullName,
                    "Verification", "audio", name));
            }
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            seen.Clear();
            lamps.Clear(); lampMax.Clear(); lampPrev.Clear(); lampNextEvent.Clear();
            for (var i = 0; i < fixtureVoices; i++) fixtureLamp[i] = -1;
            listener = null;
            player = null;
            relayBody = null;
            nextDiscover = 0f;
            if (started) StartRoomTone();
        }

        void Update()
        {
            UnlockWebAudio();
            FrontRoomsFmod.EnsureStarted();
            if (FrontRoomsFmod.Failed)
            {
                // FMOD broke mid-session: give the sound back to the legacy Unity audio rather than go silent.
                if (started && muteLegacyUnityAudio && !legacyRestored) { AudioListener.volume = 1f; legacyRestored = true; }
                return;
            }
            var now = Time.unscaledTime;
            if (now >= nextDiscover) { nextDiscover = now + 1f; Discover(); }   // attach to the scene before FMOD is ready
            if (!FrontRoomsFmod.Ready) return;
            if (!started)
            {
                started = true;
                if (muteLegacyUnityAudio) AudioListener.volume = 0f;
                StartRoomTone();
                FrontRoomsFmod.Note("ready");
                Debug.Log("[FrontRoomsAudio] FMOD ready: banks loaded, room tone on, legacy Unity audio muted.");
            }
            EnsureRunVoices();
            // Caught cuts everything to silence: the lamps must not come back under the tinnitus.
            if (!caught && now >= nextFixtureUpdate) { nextFixtureUpdate = now + .2f; UpdateFixtures(); }
            UpdateGlobals(Time.unscaledDeltaTime);
            UpdateSubjective();
        }

        // ------------------------------------------------------------ room tone
        void StartRoomTone()
        {
            if (!humBed.isValid())
            {
                humBed = FrontRoomsFmod.Create2D(SoundIds.HumBed);
                if (humBed.isValid()) humBed.start();
            }
            if (!airBed.isValid()) { airBed = FrontRoomsFmod.Create2D(SoundIds.AirBed); if (airBed.isValid()) airBed.start(); }
        }

        void StopRoomTone(bool immediate)
        {
            FrontRoomsFmod.Stop(ref humBed, immediate);
            FrontRoomsFmod.Stop(ref airBed, immediate);
        }

        // ------------------------------------------------------------ discovery
        void Discover()
        {
            if (listener == null)
            {
                // The ears are the camera. FMOD's setup wizard can replace the scene's Unity
                // AudioListener with a StudioListener, so accept either, and add the FMOD one only if missing.
                var unityListener = FindAnyObjectByType<AudioListener>();
                var fmodListener = FindAnyObjectByType<StudioListener>();
                var ears = unityListener != null ? unityListener.transform : fmodListener != null ? fmodListener.transform : null;
                if (ears != null)
                {
                    listener = ears;
                    if (!FrontRoomsFmod.Failed && listener.GetComponent<StudioListener>() == null)
                        listener.gameObject.AddComponent<StudioListener>();
                }
            }
            // Exactly one FMOD listener: two would make FMOD blend 3D positions between two pairs of ears.
            if (listener != null)
                foreach (var extra in FindObjectsByType<StudioListener>(FindObjectsSortMode.None))
                    if (extra.enabled && extra.transform != listener)
                    {
                        extra.enabled = false;
                        FrontRoomsFmod.Note("disabled extra FMOD listener on " + extra.gameObject.name);
                    }

            if (player == null)
            {
                var body = FindAnyObjectByType<CharacterController>();
                if (body != null)
                {
                    player = body.GetComponent<FrontRoomsPlayerFootsteps>();
                    if (player == null) player = body.gameObject.AddComponent<FrontRoomsPlayerFootsteps>();
                    player.surfaceAt = SurfaceAt;
                    player.dampnessAt = DampnessAt;
                }
            }

            if (relayBody == null)
            {
                var rig = FindAnyObjectByType<FrontRoomsRelayRig>();
                if (rig != null)
                {
                    relayBody = rig.GetComponent<FrontRoomsRelaySound>();
                    if (relayBody == null) relayBody = rig.gameObject.AddComponent<FrontRoomsRelaySound>();
                }
            }
            if (relayBody != null) { relayBody.hunter = relay; relayBody.listener = listener; relayBody.dampnessAt = DampnessAt; }

            // Doors and lamps are built at runtime (chunks, pooled rooms): attach once per new transform.
            var scene = SceneManager.GetActiveScene();
            scene.GetRootGameObjects(roots);
            for (var r = 0; r < roots.Count; r++)
            {
                roots[r].GetComponentsInChildren(true, scan);
                for (var i = 0; i < scan.Count; i++)
                {
                    var t = scan[i];
                    if (!seen.Add(t.GetInstanceID())) continue;
                    var name = t.name;
                    if (name.StartsWith("Door hinge"))
                        Attach(t, FrontRoomsDoorSound.Mode.Manual, 95f);
                    else if (name == StreamLeftHinge || name == StreamRightHinge)
                    {
                        // The stream's double door swings on a script, both leaves at once: one recorded swing
                        // per leaf. The left leaf leads, the right follows (other takes, 28 ms later), so a pair
                        // is two leaves, never one sound doubled.
                        var door = Attach(t, FrontRoomsDoorSound.Mode.Stream, 88f);
                        if (door == null) continue;
                        var left = name == StreamLeftHinge;
                        door.pairedHinge = t.parent != null ? t.parent.Find(left ? StreamRightHinge : StreamLeftHinge) : null;
                        door.leaf = left || door.pairedHinge == null ? SoundIds.Leaf.Lead : SoundIds.Leaf.Follow;
                    }
                    else if (name == "Light" || name.StartsWith("fluorescent light"))
                    {
                        var light = t.GetComponent<Light>();
                        if (light != null) { lamps.Add(light); lampMax.Add(Mathf.Max(.01f, light.intensity)); lampPrev.Add(-1f); lampNextEvent.Add(0f); }
                    }
                }
            }
        }

        static FrontRoomsDoorSound Attach(Transform hinge, FrontRoomsDoorSound.Mode mode, float limit)
        {
            if (hinge.GetComponent<FrontRoomsDoorSound>() != null) return null;
            var door = hinge.gameObject.AddComponent<FrontRoomsDoorSound>();
            door.mode = mode;
            door.openLimit = limit;
            return door;
        }

        SoundIds.Surface SurfaceAt(Vector3 feet)
        {
            if (map == null) return SoundIds.Surface.Carpet;
            var cell = map.CellOf(feet);
            if (map.InStartArea(cell)) return SoundIds.Surface.Carpet;            // the title's stream rooms: Level 0
            var zone = map.ZoneOf(cell);
            return zone.theme == ZoneTheme.Office ? SoundIds.Surface.CarpetTile : SoundIds.Surface.Carpet;
        }

        /// <summary>
        /// How wet the floor is underfoot. The map has no water data yet, so the
        /// zone stands in: low ceilings hold the deep, sticky carpet; offices are
        /// glue-down tile and nearly dry. Puddles would return 0.8-1 here.
        /// </summary>
        float DampnessAt(Vector3 feet)
        {
            if (map == null) return .4f;
            var cell = map.CellOf(feet);
            if (map.InStartArea(cell)) return .4f;
            var zone = map.ZoneOf(cell);
            if (zone.theme == ZoneTheme.Office) return .15f;
            return zone.height == ZoneHeight.Low ? .55f : zone.height == ZoneHeight.Tall ? .3f : .4f;
        }

        // ------------------------------------------------------------ lamps
        void UpdateFixtures()
        {
            if (listener == null) return;
            var origin = listener.position;
            var found = 0;
            var r2 = fixtureRadius * fixtureRadius;
            for (var i = 0; i < lamps.Count; i++)
            {
                var lamp = lamps[i];
                if (lamp == null) continue;
                var d = (lamp.transform.position - origin).sqrMagnitude;
                if (d > r2) continue;
                // insertion into the fixed-size nearest list
                var slot = found < nearest.Length ? found++ : nearest.Length;
                if (slot == nearest.Length)
                {
                    if (d >= nearestDistance[nearest.Length - 1]) continue;
                    slot = nearest.Length - 1;
                }
                while (slot > 0 && nearestDistance[slot - 1] > d)
                {
                    nearest[slot] = nearest[slot - 1];
                    nearestDistance[slot] = nearestDistance[slot - 1];
                    slot--;
                }
                nearest[slot] = i;
                nearestDistance[slot] = d;
            }

            for (var v = 0; v < fixtureVoices; v++)
            {
                if (v >= found) { FrontRoomsFmod.Stop(ref fixtureVoice[v]); fixtureLamp[v] = -1; continue; }
                var index = nearest[v];
                var lamp = lamps[index];
                var on = lamp.enabled && lamp.gameObject.activeInHierarchy;
                var raw = on ? lamp.intensity : 0f;
                if (raw > lampMax[index]) lampMax[index] = raw;
                var level = Mathf.Clamp01(raw / lampMax[index]);
                LampEvents(index, lamp.transform.position, level);
                if (!fixtureVoice[v].isValid())
                {
                    fixtureVoice[v] = FrontRoomsFmod.Create(SoundIds.Fixture, lamp.transform.position);
                    if (!fixtureVoice[v].isValid()) continue;
                    if (!fixtureIdReady) { fixtureLevelId = FrontRoomsFmod.ParameterId(SoundIds.Fixture, SoundIds.Param.Level); fixtureIdReady = true; }
                    fixtureStartAt[v] = Time.unscaledTime + v * FixtureStagger;
                    fixtureStarted[v] = false;
                }
                if (!fixtureStarted[v] && Time.unscaledTime >= fixtureStartAt[v])
                {
                    fixtureVoice[v].start();
                    fixtureStarted[v] = true;
                }
                fixtureLamp[v] = index;
                fixtureVoice[v].setParameterByID(fixtureLevelId, level);
                FrontRoomsFmod.Move(fixtureVoice[v], lamp.transform.position);
            }
        }

        void LampEvents(int index, Vector3 position, float level)
        {
            var previous = lampPrev[index];
            lampPrev[index] = level;
            if (previous < 0f) return;                                  // first sight of this lamp: no event
            var now = Time.time;
            if (now < lampNextEvent[index]) return;
            if (previous < .15f && level > .6f)
            {
                FrontRoomsFmod.OneShot(SoundIds.FixtureEvent, position, SoundIds.Param.FixtureEvent, (float)SoundIds.FixtureKind.Strike);
                lampNextEvent[index] = now + 1.2f;
            }
            else if (previous > .6f && level < .15f)
            {
                FrontRoomsFmod.OneShot(SoundIds.FixtureEvent, position, SoundIds.Param.FixtureEvent, (float)SoundIds.FixtureKind.Tick);
                lampNextEvent[index] = now + .3f;
            }
        }

        // ------------------------------------------------------------ globals
        void UpdateGlobals(float dt)
        {
            var target = .05f;
            if (relay != null && relay.Released && listener != null)
            {
                var proximity = 1f - Mathf.Clamp01(Vector3.Distance(listener.position, relay.Position) / 30f);
                float stateWeight;
                switch (relay.State)
                {
                    case HunterState.Chase: stateWeight = 1f; break;
                    case HunterState.BreakDoor: stateWeight = .8f; break;
                    case HunterState.Search: stateWeight = .55f; break;
                    case HunterState.Hunt: stateWeight = .45f; break;
                    case HunterState.Wander: stateWeight = .2f; break;   // roaming, not tracking you
                    default: stateWeight = .25f; break;
                }
                target = stateWeight * Mathf.Lerp(.5f, 1f, proximity);
            }
            var rate = target > tension ? 2f : .5f;                    // rise fast, settle slowly
            tension = Mathf.MoveTowards(tension, target, rate * dt);
            FrontRoomsFmod.SetGlobal(SoundIds.Param.Tension, tension);

            var zone = SoundIds.Zone.Standard;
            if (map != null && listener != null && !map.InStartArea(map.CellOf(listener.position)))
            {
                var info = map.ZoneOf(map.CellOf(listener.position));
                zone = info.theme == ZoneTheme.Office ? SoundIds.Zone.Office
                    : info.height == ZoneHeight.Low ? SoundIds.Zone.Low
                    : info.height == ZoneHeight.Tall ? SoundIds.Zone.Tall : SoundIds.Zone.Standard;
            }
            FrontRoomsFmod.SetGlobal(SoundIds.Param.Zone, (float)zone);
        }

        void UpdateSubjective()
        {
            if (map == null || caught) return;
            if (breath.isValid() && player != null) breath.setParameterByID(staminaId, player.Stamina01);
            if (relay == null || !relay.Released || listener == null) return;
            if (!heartbeat.isValid())
            {
                heartbeat = FrontRoomsFmod.Create2D(SoundIds.Heartbeat);
                if (heartbeat.isValid()) heartbeat.start();
            }
            var proximity = 1f - Mathf.Clamp01(Vector3.Distance(listener.position, relay.Position) / 20f);
            heartbeat.setParameterByID(heartProximityId, relay.SeesPlayer ? 0f : proximity);
        }

        // ------------------------------------------------------------ game events
        void OnMapRunStarted(FrontRoomsMapWorld world, FrontRoomsMapHunter hunter)
        {
            OnMapRunEnded();
            map = world;
            relay = hunter;
            lastState = HunterState.Dormant;
            relayRevealed = false;
            caught = false;
            FrontRoomsFmod.Note("map run started");
            // Hook the run first: whether FMOD has finished loading must never decide whether a run is heard.
            if (started) StartRoomTone();
            map.GlassHold += OnGlassHold;
            map.GlassHoldReleased += OnGlassHoldReleased;
            map.GlassBroken += OnGlassBroken;
            map.DoorBroken += OnDoorBroken;
            map.DoorLocked += OnDoorLocked;
            map.KeyTaken += OnKeyTaken;
            relay.StateChanged += OnRelayState;
            relay.DoorBlow += OnDoorBlow;
            relay.Caught += OnCaught;
            if (relayBody != null) relayBody.hunter = relay;
        }

        /// <summary>Run voices and parameter ids, created once FMOD is ready (and again after a catch).</summary>
        void EnsureRunVoices()
        {
            if (map == null) return;
            if (!runIdsReady)
            {
                staminaId = FrontRoomsFmod.ParameterId(SoundIds.Breath, SoundIds.Param.Stamina);
                heartProximityId = FrontRoomsFmod.ParameterId(SoundIds.Heartbeat, SoundIds.Param.Proximity);
                stressProgressId = FrontRoomsFmod.ParameterId(SoundIds.WindowStress, SoundIds.Param.Progress);
                runIdsReady = true;
            }
            if (!breath.isValid() && !caught)
            {
                breath = FrontRoomsFmod.Create2D(SoundIds.Breath);
                if (breath.isValid()) breath.start();
            }
        }

        void OnMapRunEnded()
        {
            if (map != null)
            {
                map.GlassHold -= OnGlassHold;
                map.GlassHoldReleased -= OnGlassHoldReleased;
                map.GlassBroken -= OnGlassBroken;
                map.DoorBroken -= OnDoorBroken;
                map.DoorLocked -= OnDoorLocked;
                map.KeyTaken -= OnKeyTaken;
            }
            if (relay != null)
            {
                relay.StateChanged -= OnRelayState;
                relay.DoorBlow -= OnDoorBlow;
                relay.Caught -= OnCaught;
            }
            map = null;
            relay = null;
            FrontRoomsFmod.Stop(ref breath, true);
            FrontRoomsFmod.Stop(ref heartbeat, true);
            FrontRoomsFmod.Stop(ref windowStress, true);
        }

        void OnGlassHold(Vector3 position, float progress)
        {
            if (!windowStress.isValid())
            {
                windowStress = FrontRoomsFmod.Create(SoundIds.WindowStress, position);
                if (windowStress.isValid()) windowStress.start();
                lastStressProgress = 0f;
            }
            if (windowStress.isValid()) windowStress.setParameterByID(stressProgressId, progress);
            if (lastStressProgress < .35f && progress >= .35f) FrontRoomsFmod.OneShot(SoundIds.WindowCrack, position);
            if (lastStressProgress < .7f && progress >= .7f) FrontRoomsFmod.OneShot(SoundIds.WindowCrack, position);
            lastStressProgress = progress;
        }

        void OnGlassHoldReleased(Vector3 position) => FrontRoomsFmod.Stop(ref windowStress);

        void OnGlassBroken(Vector3 position)
        {
            FrontRoomsFmod.Stop(ref windowStress, true);
            FrontRoomsFmod.OneShot(SoundIds.WindowShatter, position);
        }

        void OnDoorBroken(Vector3 position)
        {
            // The leaf is off its hinges now: its motion is the break, not a door being opened.
            FrontRoomsDoorSound.MarkBroken(position);
            FrontRoomsFmod.OneShot(SoundIds.DoorBreak, position);
            FrontRoomsFmod.OneShot(SoundIds.DoorStopLimit, position, SoundIds.Param.Impact, 1f);
            blowCount = 0;
        }

        void OnDoorLocked(Vector3 position) => FrontRoomsFmod.OneShot(SoundIds.DoorLocked, position);

        void OnKeyTaken(GridCoord zone) => FrontRoomsFmod.OneShot2D(SoundIds.KeyPickup);

        void OnDoorBlow(Vector3 position)
        {
            if ((position - lastBlowDoor).sqrMagnitude > .25f) blowCount = 0;
            lastBlowDoor = position;
            blowCount++;
            // The hunter numbers its blows (BlowIndex 0..BlowCount-1, the last one breaks through);
            // BlowCount shrinks at higher tiers, so the strength is the share of the way through.
            var damage = relay != null && relay.BlowIndex >= 0 && relay.BlowCount > 0
                ? (relay.BlowIndex + 1f) / relay.BlowCount
                : Mathf.Clamp01(blowCount / 5f);
            // A struck leaf jolts on its hinge: that is not someone opening the door.
            FrontRoomsDoorSound.Suppress(position, 1f);
            FrontRoomsFmod.OneShot(SoundIds.DoorBlow, position, SoundIds.Param.Damage, damage);
        }

        void OnRelayState(HunterState state)
        {
            var stinger = -1;
            if (state == HunterState.Hunt && lastState != HunterState.Chase) stinger = (int)SoundIds.RelayState.Hunt;
            else if (state == HunterState.Search) stinger = (int)SoundIds.RelayState.Search;
            else if (state == HunterState.Chase && lastState != HunterState.BreakDoor) stinger = (int)SoundIds.RelayState.Chase;
            else if (state == HunterState.Listen && (lastState == HunterState.Search || lastState == HunterState.Chase)) stinger = (int)SoundIds.RelayState.Lost;
            if (stinger >= 0) FrontRoomsFmod.OneShot2D(SoundIds.RelayStinger, SoundIds.Param.RelayState, stinger);
            if (!relayRevealed && state != HunterState.Dormant && relay != null)
            {
                relayRevealed = true;                                   // first move after release: heard before seen
                FrontRoomsFmod.OneShot(SoundIds.RelayClicks, relay.Position + Vector3.up * 2f);
            }
            lastState = state;
        }

        void OnCaught()
        {
            caught = true;
            if (!FrontRoomsFmod.Ready) return;
            // Hard cut to silence, then a single ringing tone.
            StopRoomTone(true);
            for (var i = 0; i < fixtureVoices; i++) { FrontRoomsFmod.Stop(ref fixtureVoice[i], true); fixtureLamp[i] = -1; }
            FrontRoomsFmod.Stop(ref breath, true);
            FrontRoomsFmod.Stop(ref heartbeat, true);
            FrontRoomsFmod.Stop(ref windowStress, true);
            RuntimeManager.GetBus(SoundIds.BusSfx).stopAllEvents(STOP_MODE.IMMEDIATE);
            RuntimeManager.GetBus(SoundIds.BusAmbience).stopAllEvents(STOP_MODE.IMMEDIATE);
            RuntimeManager.GetBus(SoundIds.BusMusic).stopAllEvents(STOP_MODE.IMMEDIATE);
            FrontRoomsFmod.OneShot2D(SoundIds.Tinnitus);
        }

        void OnPlayerClimbed(Vector3 position) => FrontRoomsFmod.OneShot(SoundIds.Cloth, position);

        // ------------------------------------------------------------ web audio
        void UnlockWebAudio()
        {
#if UNITY_WEBGL && !UNITY_EDITOR
            if (webUnlocked || !RuntimeManager.IsInitialized) return;
            if (Input.anyKeyDown || Input.GetMouseButtonDown(0))
            {
                RuntimeManager.CoreSystem.mixerSuspend();
                RuntimeManager.CoreSystem.mixerResume();
                webUnlocked = true;
            }
#endif
        }
    }
}
