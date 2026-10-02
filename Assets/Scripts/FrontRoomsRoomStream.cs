using System;
using UnityEngine;

/// <summary>
/// The bounded, first-person room stream: the title corridor and the whole
/// playable level. The component owns five reusable room roots: the rooms
/// behind the player, the current room and at least two dressed rooms waiting
/// behind closed doors. The oldest room is recycled to the front only once the
/// door behind the player has shut.
/// </summary>
public sealed class FrontRoomsRoomStream : MonoBehaviour
{
    // Up to two rooms behind, the current room, and two or three prepared
    // rooms ahead. A room only changes profile while it is out of sight.
    public const int MaxRooms = 5;
    public const float RoomWidth = 11.5f;
    public const float RoomHeight = 2.9f;
    public const float RoomLength = 12f;
    const float DoorWidth = 2.4f;
    // Leave a small jamb clearance for the closed leaves and for the hinge
    // side of the slab while it swings open. The opening remains 2.4m wide,
    // while the ordinary double door occupies 2.24m of it.
    const float DoorLeafWidth = 1.12f;
    const float DoorLeafPivotX = 1.12f;
    // Keep the threshold return almost flush with the door plane. A deep
    // return leaves a dark inner side visible when the leaf is open, which
    // reads as looking into a hollow model instead of a normal doorway.
    const float DoorWallDepth = .04f;
    const float DoorLeafDepth = .08f;
    // Keep a small construction tolerance below the 2.66m header bottom.
    // A full-height 2.88m leaf visibly intersected the header slab.
    const float DoorHeaderHeight = .24f;
    const float DoorLeafHeight = RoomHeight - DoorHeaderHeight - .04f;
    const float WallThickness = .26f;
    // The rear seal belongs to the room behind a threshold. Keep it just
    // inside the next room so it cannot sit on the same plane as the door
    // leaves when a pooled room is recycled onto that threshold.
    const float RearSealOffset = .24f;
    const float BoundaryMargin = .34f;
    const float TitleSpeed = 1.15f;
    // The title crawl is intentionally slow, but the start trigger should
    // feel like a handoff into play rather than another title beat. Accelerate
    // over a short ramp, then settle precisely on the next room's authored
    // Entry / 2m inside anchor.
    const float TransitionSpeed = 6.2f;
    const float TransitionFinalSpeed = 1.2f;
    const float TransitionAccelerationSeconds = .36f;
    const float DoorOpenSeconds = .9f;
    const float RecycleDistance = 8f;
    const float RebaseThreshold = 256f;
    const float LogoDelay = .7f;
    const float LogoFadeSeconds = 4f;
    const float LogoExitSeconds = .55f;
    // Drop-ceiling grid in world space: 2' across X, 4' along Z. Both divide
    // the 256 m rebase, so fixtures stay in their grid cells after a rebase.
    const float GridX = 256f / 420f;
    const float GridZ = 256f / 210f;
    const float TrofferWidth = GridX;
    const float TrofferLength = GridZ;
    static readonly float[] FixtureZ = { 1.7f, 4.55f, 7.4f, 10.25f };
    // Room-stream lights use a deterministic variation per sequence rather
    // than one global flash cue. The sequence is hashed, so recycling a pool
    // slot never repeats the same behaviour simply because it is the same
    // GameObject.
    const int LightRandomSeed = 24017;

    [Tooltip("Optional room authoring template. A copy is placed inside each streamed room root.")]
    public GameObject roomTemplate;

    [SerializeField, Tooltip("Keep the title and arrival stream on authored Level 0 Lobby replicas. Player control is handed off separately after arrival.")]
    bool lobbyOnlyTitle = true;

    [SerializeField, Tooltip("Empty Lobby rooms after the handoff room before the first furnished profile.")]
    int emptyLeadRooms = 2;

    [Header("Practical light response")]
    [SerializeField, Range(0f, 1f), Tooltip("Scales the diffuse contribution of each fluorescent practical. The same coefficient drives point-light output, bounceIntensity and the beam material.")]
    float diffuseCoefficient = .82f;

    [SerializeField, Range(0f, 1f), Tooltip("Density of the lightweight built-in-renderer volumetric shafts below each fluorescent fixture.")]
    float volumetricDensity = .012f;

    [SerializeField, Range(.8f, 2.0f), Tooltip("Downward length of each volumetric shaft in metres.")]
    float volumetricRange = 1.0f;

    sealed class RoomSlot
    {
        public GameObject root;
        public Transform entry;
        public Transform leftDoor;
        public Transform rightDoor;
        // The analytical mover normally avoids physics queries. Keep the
        // doorway colliders explicitly so a player cannot step into a swung
        // leaf or the thin wall returns and then see their internal faces.
        public BoxCollider[] doorwayColliders;
        public GameObject rearSeal;
        public int sequence;
        public RoomRule rule;
        public float startZ;
        public float endZ;
        public float doorProgress;
        public bool doorOpening;
        public bool doorOpen;
        // Broken by the Relay: the door stays open and never auto-closes.
        public bool doorBroken;
        public bool connected;
        public bool doorSoundPlayed;
        public AudioSource doorAudio;
        public Light[] roomLights;
        public float[] lightBaseIntensity;
        public bool[] lightWasEnabled;
        // Every fixture is its own ballast: it strikes after its own delay,
        // flickers its own count, rises at its own rate, and may be failing
        // (sways forever) or dead (never lights). Nothing waits for the room.
        public LampState[] lampState;
        public float[] lampDelay;
        public int[] lampFlickerCount;
        public float[] lampFlickerElapsed;
        public float[] lampFlickerPeriod;
        public float[] lampFlickerOnFraction;
        public float[] lampFlickerPhase;
        public float[] lampRevealSeconds;
        public float[] lampRevealProgress;
        public float[] lampRiseFrom;
        public bool[] lampUnstable;
        public bool[] lampDead;
        public float[] lampUnstableElapsed;
        public float[] lampNoisePhase;
        public Transform[] fixtures;
        public Renderer[] lightDiffusers;
        public Renderer[] volumetricRenderers;
        public MaterialPropertyBlock[] lightDiffuserBlocks;
        public MaterialPropertyBlock[] volumetricBlocks;
        public float[] lightOutputLevel;
        public bool[] lightOutputEnabled;
        public GameObject[] profileVariants;
    }

    enum LampState { Off, Waiting, Striking, Rising, Steady, Unstable, Dead }

    Camera streamCamera;
    Material wallMaterial;
    Material floorMaterial;
    Material ceilingMaterial;
    Material trimMaterial;
    Material fixtureMaterial;
    Material doorMaterial;
    Material[] profileWallMaterials;
    Material[] profileFloorMaterials;
    Material[] profileCeilingMaterials;
    Material officeDeskMaterial;
    Material officeMetalMaterial;
    Material officePaperMaterial;
    Material officeGlassMaterial;
    Material officeDarkMaterial;
    Material runChromeMaterial;
    Material runVinylMaterial;
    Material runBedMaterial;
    Material runRailMaterial;
    Material outletMaterial;
    Material doorHardwareMaterial;
    Material volumetricLightMaterial;
    AudioClip doorCreakClip;
    AudioClip doorLatchClip;
    AudioClip doorTravelClip;
    readonly RoomSlot[] pool = new RoomSlot[MaxRooms];
    readonly Vector3[] movementScratch = new Vector3[1];
    int currentPoolIndex;
    int currentSequence;
    int transitionPoolIndex = -1;
    float centerX;
    float titleElapsed;
    float transitionElapsed;
    float transitionStartZ;
    float pendingTargetZ;
    float logoVisibility;
    float firstDoorMotionProgress;
    int recycledCount;
    int rebaseCount;
    float maxExposure;
    bool initialized;
    bool startRequested;
    bool hasControl;
    bool isEntering;
    int firstPlayableSequence = -1;

    /// <summary>Raised once per door, when its latch first releases.</summary>
    public event Action<int, Vector3> DoorOpeningStarted;

    public bool HasControl => hasControl;
    public bool IsEntering => isEntering;
    public float LogoVisibility => logoVisibility;
    /// <summary>
    /// Progress of the first visible door. The title mark uses this as its
    /// motion clock, so the two trailing S forms move only when the physical
    /// door begins to open instead of after an arbitrary title delay.
    /// </summary>
    public float FirstDoorProgress => firstDoorMotionProgress;
    public int RoomCount => initialized ? MaxRooms : 0;
    public int RecycledCount => recycledCount;
    public int RebaseCount => rebaseCount;
    public int CurrentRoomNumber => currentSequence;
    public bool LobbyOnlyTitle => lobbyOnlyTitle;
    public RoomRule CurrentRule
    {
        get
        {
            var current = FindSequence(currentSequence);
            return current == null ? RoomRule.Lobby : current.rule;
        }
    }
    public float CameraZ => streamCamera == null ? 0f : streamCamera.transform.position.z;
    public Vector3 PendingAnchorPosition { get; private set; }
    public float MaxExposure => maxExposure;
    public float MaxExposureDistance => RoomLength * MaxRooms;
    public int MaxExposedRooms => MaxRooms;
    public float CenterX => centerX;
    /// <summary>Sum of every floating-origin shift, so callers can move their own world positions with the rooms.</summary>
    public float TotalRebaseShift { get; private set; }
    public bool IsPlayable => !lobbyOnlyTitle && firstPlayableSequence >= 0;
    /// <summary>Sequence of the first furnished room after the empty lead rooms, or -1 before the handoff.</summary>
    public int FirstProfileSequence => IsPlayable ? firstPlayableSequence + LeadRooms + 1 : -1;
    int LeadRooms => Mathf.Max(0, emptyLeadRooms);

    void EnsureVolumetricLightMaterial()
    {
        if (volumetricLightMaterial != null) return;
        var shader = Resources.Load<Shader>("Lighting/VolumetricBeam");
        if (shader == null)
        {
            Debug.LogWarning("[FrontRooms3D] VolumetricBeam shader is unavailable; fluorescent shafts will stay disabled.");
            return;
        }
        volumetricLightMaterial = new Material(shader)
        {
            name = "FrontRooms / volumetric fluorescent beam",
            renderQueue = 3000
        };
    }

    /// <summary>Build the fixed room pool around the camera's current position.</summary>
    public void Initialize(Camera camera, Material wall, Material floor, Material ceiling,
        Material trim, Material fixture, Material door, AudioClip doorCreak = null,
        AudioClip doorLatch = null, AudioClip doorTravel = null,
        Material[] profileWalls = null, Material[] profileFloors = null, Material[] profileCeilings = null)
    {
        streamCamera = camera;
        wallMaterial = wall;
        floorMaterial = floor;
        ceilingMaterial = ceiling;
        trimMaterial = trim;
        fixtureMaterial = fixture;
        doorMaterial = door;
        profileWallMaterials = profileWalls;
        profileFloorMaterials = profileFloors;
        profileCeilingMaterials = profileCeilings;
        doorCreakClip = doorCreak;
        doorLatchClip = doorLatch;
        doorTravelClip = doorTravel;
        initialized = false;
        startRequested = false;
        hasControl = false;
        isEntering = false;
        titleElapsed = 0f;
        transitionElapsed = 0f;
        transitionPoolIndex = -1;
        recycledCount = 0;
        rebaseCount = 0;
        maxExposure = 0f;
        logoVisibility = 0f;
        firstDoorMotionProgress = 0f;
        lobbyOnlyTitle = true;
        firstPlayableSequence = -1;
        TotalRebaseShift = 0f;

        EnsureVolumetricLightMaterial();

        var cameraZ = streamCamera == null ? 0f : streamCamera.transform.position.z;
        centerX = streamCamera == null ? 0f : streamCamera.transform.position.x;
        var firstStart = cameraZ - RoomLength * .5f;
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = new RoomSlot();
            room.sequence = i;
            room.rule = RuleForStreamSequence(i);
            room.startZ = firstStart + i * RoomLength;
            room.endZ = room.startZ + RoomLength;
            room.root = new GameObject("Stream room / " + i.ToString("000"));
            room.root.transform.SetParent(transform, false);
            room.root.transform.position = new Vector3(centerX, 0f, room.startZ);
            BuildRoom(room, i);
            pool[i] = room;
        }
        // The first title room is already occupied when the sequence begins.
        // Subsequent rooms receive their light cue from the door that connects
        // them, so the corridor can fall away into darkness beyond the first
        // threshold.
        ActivateRoomLightImmediately(pool[0]);
        currentPoolIndex = 0;
        currentSequence = 0;
        maxExposure = MaxRooms;
        initialized = true;
    }

    /// <summary>
    /// Edit-mode reference: one room per profile laid end to end with doors
    /// open and lights on, built by the same code as the runtime pool. It is
    /// a view of the generator, not a pool — nothing here ticks or recycles.
    /// </summary>
    public void BuildEditorPreview(Material wall, Material floor, Material ceiling,
        Material trim, Material fixture, Material door,
        Material[] profileWalls, Material[] profileFloors, Material[] profileCeilings)
    {
        EnsureVolumetricLightMaterial();
        wallMaterial = wall;
        floorMaterial = floor;
        ceilingMaterial = ceiling;
        trimMaterial = trim;
        fixtureMaterial = fixture;
        doorMaterial = door;
        profileWallMaterials = profileWalls;
        profileFloorMaterials = profileFloors;
        profileCeilingMaterials = profileCeilings;
        centerX = 0f;
        var profiles = (RoomRule[])Enum.GetValues(typeof(RoomRule));
        for (var i = 0; i < profiles.Length; i++)
        {
            var room = new RoomSlot { sequence = i, rule = profiles[i], startZ = i * RoomLength };
            room.endZ = room.startZ + RoomLength;
            room.root = new GameObject("Profile " + i + " / " + profiles[i]);
            room.root.transform.SetParent(transform, false);
            room.root.transform.localPosition = new Vector3(0f, 0f, room.startZ);
            BuildRoom(room, i);
            room.doorProgress = 1f;
            ApplyDoorPose(room);
            ActivateRoomLightImmediately(room);
        }
    }

    /// <summary>
    /// The playable cycle, counted from the first furnished room: Shift,
    /// Office, Run, Exit, then a Lobby breather. Later cycles repeat the same
    /// semantic beats while the light profile and door timing continue to vary
    /// by sequence number.
    /// </summary>
    public static RoomRule RuleForProfileIndex(int profileIndex)
    {
        switch (((profileIndex % 5) + 5) % 5)
        {
            case 0: return RoomRule.Shift;
            case 1: return RoomRule.Office;
            case 2: return RoomRule.Run;
            case 3: return RoomRule.Exit;
            default: return RoomRule.Lobby;
        }
    }

    RoomRule RuleForStreamSequence(int sequence)
    {
        // The title corridor and the first rooms after the handoff are empty
        // Lobby replicas. Furnished profiles start only beyond the rooms that
        // already exist at the handoff, so nothing is re-dressed in view.
        if (!IsPlayable) return RoomRule.Lobby;
        var profileIndex = sequence - FirstProfileSequence;
        return profileIndex < 0 ? RoomRule.Lobby : RuleForProfileIndex(profileIndex);
    }

    /// <summary>The profile of any sequence, loaded or not.</summary>
    public RoomRule RuleAt(int sequence)
    {
        var room = FindSequence(sequence);
        return room == null ? RuleForStreamSequence(sequence) : room.rule;
    }

    /// <summary>
    /// Advance the title, arrival transition, door animation and bounded pool.
    /// No room or mesh is allocated in this method after Initialize returns.
    /// </summary>
    public void Tick(float dt)
    {
        if (!initialized || streamCamera == null) return;
        dt = Mathf.Clamp(dt, 0f, .1f);
        titleElapsed += dt;
        if (!startRequested)
        {
            logoVisibility = Mathf.Clamp01(Mathf.Max(0f, titleElapsed - LogoDelay) / LogoFadeSeconds);
            MoveTitleCamera(dt);
        }
        else if (isEntering)
        {
            logoVisibility = Mathf.MoveTowards(logoVisibility, 0f, dt / LogoExitSeconds);
            TickArrival(dt);
        }
        TickNearbyDoors(dt);
        TickRoomLights(dt);
        var firstDoor = FindSequence(0);
        if (firstDoor != null) firstDoorMotionProgress = Mathf.Max(firstDoorMotionProgress, firstDoor.doorProgress);
        else firstDoorMotionProgress = 1f;
        MaintainPool();
        RebaseIfNeeded();
    }

    /// <summary>
    /// Begin the next-door handoff. Repeated calls are intentionally harmless.
    /// </summary>
    public void RequestStart()
    {
        if (!initialized || hasControl || startRequested) return;
        var current = FindCurrentRoom();
        var next = FindSequence(current.sequence + 1);
        if (next == null) return;
        startRequested = true;
        isEntering = true;
        transitionPoolIndex = PoolIndex(next);
        transitionElapsed = 0f;
        transitionStartZ = streamCamera.transform.position.z;
        var targetAnchor = next.entry == null
            ? new Vector3(centerX, streamCamera.transform.position.y, next.startZ + 2f)
            : next.entry.position;
        pendingTargetZ = targetAnchor.z;
        PendingAnchorPosition = new Vector3(targetAnchor.x, streamCamera.transform.position.y, targetAnchor.z);
        next.connected = false;
        // The next room stays closed until it reaches the normal proximity
        // trigger. Opening its animation here would make a distant door play
        // its creak before the player can see or hear the hinge move.
        next.doorOpening = false;
        BeginDoorOpening(current);
    }

    /// <summary>
    /// Start counting the playable sequence from the room the player was just
    /// handed. The handoff room and the empty lead rooms keep their Lobby
    /// dressing. Rooms already prepared ahead are re-dressed only while they
    /// are still sealed behind the handoff room's closed door, so no room ever
    /// changes while it can be seen.
    /// </summary>
    public void BeginPlayableSequence()
    {
        if (!initialized || IsPlayable) return;
        lobbyOnlyTitle = false;
        firstPlayableSequence = currentSequence;
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = pool[i];
            if (room == null || room.connected || room.sequence <= currentSequence) continue;
            var rule = RuleForStreamSequence(room.sequence);
            if (rule == room.rule) continue;
            room.rule = rule;
            ResetRoomLights(room);
            RefreshRoomMaterials(room);
        }
    }

    /// <summary>
    /// Move the camera after handoff. The analytical bounds keep the stream
    /// editable without requiring physics colliders on every generated mesh.
    /// </summary>
    public Vector3 Move(Vector2 worldXZDelta)
    {
        if (!initialized || streamCamera == null) return streamCamera == null ? Vector3.zero : streamCamera.transform.position;
        if (!hasControl) return streamCamera.transform.position;
        var current = streamCamera.transform.position;
        var candidate = current + new Vector3(worldXZDelta.x, 0f, worldXZDelta.y);
        var room = FindCurrentRoom();
        var half = RoomWidth * .5f - BoundaryMargin;
        candidate.x = Mathf.Clamp(candidate.x, centerX - half, centerX + half);
        var rear = room.startZ + BoundaryMargin;
        if (candidate.z < rear) candidate.z = rear;
        // Tick opens a door whenever the camera is within 4 m of it, and a frame
        // step is at most 0.55 m, so the hinge always animates. Let the player
        // through once the leaves are most of the way open.
        var passable = room.doorOpen || (room.doorOpening && room.doorProgress > .65f);
        if (candidate.z > room.endZ - BoundaryMargin && !passable)
            candidate.z = room.endZ - BoundaryMargin;
        ResolveDoorwayOverlap(room, passable, ref candidate);
        streamCamera.transform.position = candidate;
        movementScratch[0] = candidate;
        return movementScratch[0];
    }

    public Transform EntryTransform(int poolIndex)
    {
        if (!initialized || poolIndex < 0 || poolIndex >= MaxRooms || pool[poolIndex] == null) return null;
        return pool[poolIndex].entry;
    }

    void MoveTitleCamera(float dt)
    {
        var current = streamCamera.transform.position;
        current.z += TitleSpeed * dt;
        streamCamera.transform.position = current;
    }

    void TickArrival(float dt)
    {
        var source = FindSequence(currentSequence);
        var target = transitionPoolIndex < 0 ? null : pool[transitionPoolIndex];
        if (source == null || target == null) return;

        if (source.doorProgress < 1f)
        {
            BeginDoorOpening(source);
            source.doorProgress = Mathf.MoveTowards(source.doorProgress, 1f, dt / DoorOpenSeconds);
            ApplyDoorPose(source);
            if (source.doorProgress >= 1f)
            {
                // Stop treating the hinge as an active animation once it has
                // reached its target. Leaving this flag set makes the pool
                // revisit the finished door every frame and can make the
                // final frame look like a small hitch when the next room is
                // connected.
                source.doorOpening = false;
                source.doorOpen = true;
                target.connected = true;
                if (target.rearSeal != null) target.rearSeal.SetActive(false);
                ScheduleRoomLight(target);
            }
            return;
        }

        var currentPosition = streamCamera.transform.position;
        var remaining = pendingTargetZ - currentPosition.z;
        if (remaining > .001f)
        {
            // Accelerate after the start trigger, then ease only inside the
            // final metre and clamp the step. This keeps the handoff quick
            // without ever overshooting the authored anchor.
            var normalized = Mathf.Clamp01(remaining / 1f);
            transitionElapsed += dt;
            var acceleration = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(transitionElapsed / TransitionAccelerationSeconds));
            var cruiseSpeed = Mathf.Lerp(TitleSpeed, TransitionSpeed, acceleration);
            var speed = Mathf.Lerp(TransitionFinalSpeed, cruiseSpeed, normalized);
            currentPosition.z += Mathf.Min(remaining, speed * dt);
            streamCamera.transform.position = currentPosition;
            return;
        }

        currentPosition.x = PendingAnchorPosition.x;
        currentPosition.z = PendingAnchorPosition.z;
        streamCamera.transform.position = currentPosition;
        hasControl = true;
        isEntering = false;
        currentSequence = target.sequence;
        currentPoolIndex = transitionPoolIndex;
        transitionPoolIndex = -1;
        PendingAnchorPosition = currentPosition;
    }

    void TickNearbyDoors(float dt)
    {
        var cameraZ = streamCamera.transform.position.z;
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = pool[i];
            if (room == null) continue;
            var distance = room.endZ - cameraZ;
            if (!room.doorOpen && distance < 4f && distance > -1f)
                BeginDoorOpening(room);
            if (room.doorOpening && room.doorProgress < 1f)
            {
                room.doorProgress = Mathf.MoveTowards(room.doorProgress, 1f, dt / DoorOpenSeconds);
                ApplyDoorPose(room);
                if (room.doorProgress >= 1f)
                {
                    room.doorOpening = false;
                    room.doorOpen = true;
                    var next = FindSequence(room.sequence + 1);
                    if (next != null)
                    {
                        next.connected = true;
                        if (next.rearSeal != null) next.rearSeal.SetActive(false);
                        ScheduleRoomLight(next);
                    }
                }
            }
            if (room.doorOpen && !room.doorBroken && distance < -4f && room.sequence < currentSequence)
            {
                room.doorOpen = false;
                room.doorOpening = false;
                room.doorProgress = 0f;
                room.doorSoundPlayed = false;
                if (room.doorAudio != null) room.doorAudio.Stop();
                ApplyDoorPose(room);
            }
        }
    }

    /// <summary>
    /// A door opening cues the room beyond it, but every fixture answers on its
    /// own: each ballast strikes after its own delay, flickers its own count,
    /// rises at its own rate and may keep failing or never light at all. The
    /// odds come from the room profile (Shift fails more, Run is mostly dark
    /// under its exit signs). The pool is fixed, so this stays allocation-free.
    /// </summary>
    void TickRoomLights(float dt)
    {
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = pool[i];
            if (room == null || room.lampState == null) continue;
            for (var lamp = 0; lamp < room.lampState.Length; lamp++)
                TickLamp(room, lamp, dt);
        }
    }

    void TickLamp(RoomSlot room, int lamp, float dt)
    {
        switch (room.lampState[lamp])
        {
            case LampState.Waiting:
                room.lampDelay[lamp] -= dt;
                if (room.lampDelay[lamp] > 0f) return;
                if (room.lampDead[lamp])
                {
                    room.lampState[lamp] = LampState.Dead;
                    SetFixtureOutput(room, lamp, 0f, false);
                    return;
                }
                room.lampFlickerElapsed[lamp] = 0f;
                room.lampRevealProgress[lamp] = 0f;
                room.lampRiseFrom[lamp] = 0f;
                room.lampState[lamp] = room.lampFlickerCount[lamp] > 0 ? LampState.Striking : LampState.Rising;
                return;
            case LampState.Striking:
            {
                room.lampFlickerElapsed[lamp] += dt;
                var period = room.lampFlickerPeriod[lamp];
                if (room.lampFlickerElapsed[lamp] < room.lampFlickerCount[lamp] * period)
                {
                    var pulse = (room.lampFlickerElapsed[lamp] + room.lampFlickerPhase[lamp]) % period;
                    SetFixtureOutput(room, lamp, pulse < period * room.lampFlickerOnFraction[lamp] ? .92f : .035f, true);
                    return;
                }
                // A struck tube comes up from a dim warm-up glow, not from black.
                room.lampRiseFrom[lamp] = .35f;
                room.lampRevealProgress[lamp] = 0f;
                room.lampState[lamp] = LampState.Rising;
                return;
            }
            case LampState.Rising:
            {
                var progress = Mathf.MoveTowards(room.lampRevealProgress[lamp], 1f, dt / room.lampRevealSeconds[lamp]);
                room.lampRevealProgress[lamp] = progress;
                var eased = progress * progress * (3f - 2f * progress);
                var level = Mathf.Lerp(room.lampRiseFrom[lamp], 1f, eased);
                // A failing ballast never reaches full output.
                if (room.lampUnstable[lamp]) level *= Mathf.Lerp(.72f, .30f, progress);
                SetFixtureOutput(room, lamp, level, true);
                if (progress >= 1f) room.lampState[lamp] = room.lampUnstable[lamp] ? LampState.Unstable : LampState.Steady;
                return;
            }
            case LampState.Unstable:
                TickUnstableLamp(room, lamp, dt);
                return;
        }
    }

    void ScheduleRoomLight(RoomSlot room)
    {
        if (room == null || room.lampState == null) return;
        // Only dark lamps are cued; a lamp that is already on keeps its clock.
        for (var lamp = 0; lamp < room.lampState.Length; lamp++)
            if (room.lampState[lamp] == LampState.Off) room.lampState[lamp] = LampState.Waiting;
    }

    void TickUnstableLamp(RoomSlot room, int lamp, float dt)
    {
        room.lampUnstableElapsed[lamp] += dt;
        var t = room.lampUnstableElapsed[lamp] + room.lampNoisePhase[lamp];
        // Two incommensurate waves sway the ballast; Perlin dropouts cut it out
        // for a moment. Each lamp has its own phase, so no two drop together.
        var wave = .5f + .5f * Mathf.Sin(t * 3.7f) * (.68f + .32f * Mathf.Sin(t * 1.13f));
        var dropout = Mathf.PerlinNoise(t * .92f, room.lampNoisePhase[lamp] + lamp * 1.73f) > .77f ? .06f : 1f;
        SetFixtureOutput(room, lamp, (.16f + .30f * Mathf.Clamp01(wave)) * dropout, true);
    }

    void MaintainPool()
    {
        // The camera is allowed to move more than one floating-point frame
        // across a threshold. Looking only at FindCurrentRoom() here can skip
        // the exact endZ sample (for example 5.98 -> 6.10), leaving
        // currentSequence one room behind forever. Once that happens the pool
        // refuses to recycle and the title eventually runs past its last room.
        // Advance through every already-connected room whose boundary has been
        // crossed; the loop is bounded by the fixed pool size and performs no
        // allocation.
        AdvanceCurrentSequence();

        var oldest = FindOldestRoom();
        if (oldest == null || oldest.sequence >= currentSequence - 1) return;
        if (streamCamera.transform.position.z - oldest.endZ < RecycleDistance) return;
        // The room that becomes the last one behind the player gets its rear
        // sealed below. Wait until the player can no longer look into it
        // through the door they just used, unless the Relay broke that door.
        var behind = FindSequence(oldest.sequence + 1);
        if (behind != null && behind.doorOpen && !behind.doorBroken) return;
        var newest = FindNewestRoom();
        if (newest == null) return;
        var nextSequence = newest.sequence + 1;
        oldest.sequence = nextSequence;
        oldest.rule = RuleForStreamSequence(nextSequence);
        oldest.startZ = newest.endZ;
        oldest.endZ = oldest.startZ + RoomLength;
        oldest.root.transform.position = new Vector3(centerX, 0f, oldest.startZ);
        AlignFixtures(oldest);
        oldest.doorProgress = 0f;
        oldest.doorOpening = false;
        oldest.doorOpen = false;
        oldest.doorBroken = false;
        oldest.connected = false;
        oldest.doorSoundPlayed = false;
        if (oldest.doorAudio != null) oldest.doorAudio.Stop();
        if (oldest.rearSeal != null) oldest.rearSeal.SetActive(true);
        if (behind != null && behind.rearSeal != null) behind.rearSeal.SetActive(true);
        ResetRoomLights(oldest);
        RefreshRoomMaterials(oldest);
        ApplyDoorPose(oldest);
        recycledCount++;
    }

    void AdvanceCurrentSequence()
    {
        var room = FindSequence(currentSequence);
        if (room == null) return;

        var cameraZ = streamCamera.transform.position.z;
        while (cameraZ >= room.endZ)
        {
            var next = FindSequence(room.sequence + 1);
            if (next == null || !next.connected) break;
            room = next;
            currentSequence = room.sequence;
        }
    }

    void RebaseIfNeeded()
    {
        var z = streamCamera.transform.position.z;
        if (Mathf.Abs(z) <= RebaseThreshold) return;
        var shift = Mathf.Floor(z / RebaseThreshold) * RebaseThreshold;
        if (Mathf.Abs(shift) < .01f) return;
        var cameraPosition = streamCamera.transform.position;
        cameraPosition.z -= shift;
        streamCamera.transform.position = cameraPosition;
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = pool[i];
            if (room == null) continue;
            room.startZ -= shift;
            room.endZ -= shift;
            var root = room.root.transform.position;
            root.z -= shift;
            room.root.transform.position = root;
        }
        var anchor = PendingAnchorPosition;
        anchor.z -= shift;
        PendingAnchorPosition = anchor;
        pendingTargetZ -= shift;
        transitionStartZ -= shift;
        TotalRebaseShift += shift;
        rebaseCount++;
    }

    /// <summary>Start Z of any sequence; rooms are contiguous, so unloaded ones are extrapolated.</summary>
    public float RoomStartZ(int sequence)
    {
        var reference = FindSequence(currentSequence) ?? pool[0];
        return reference.startZ + (sequence - reference.sequence) * RoomLength;
    }

    public int SequenceAtZ(float z)
    {
        var reference = FindSequence(currentSequence) ?? pool[0];
        return reference.sequence + Mathf.FloorToInt((z - reference.startZ) / RoomLength);
    }

    public bool IsLoaded(int sequence) => FindSequence(sequence) != null;

    /// <summary>
    /// Whether the door at the end of a room can be walked through. Doors of
    /// rooms that are no longer loaded are behind the player and therefore shut.
    /// </summary>
    public bool IsDoorPassable(int sequence)
    {
        var room = FindSequence(sequence);
        if (room == null) return false;
        return room.doorBroken || room.doorOpen || (room.doorOpening && room.doorProgress > .65f);
    }

    /// <summary>
    /// Force a door open from the hunter's side. Returns false when the room is
    /// not loaded, so the caller can remember the breach itself.
    /// </summary>
    public bool BreakDoor(int sequence)
    {
        var room = FindSequence(sequence);
        if (room == null) return false;
        room.doorBroken = true;
        room.doorOpening = false;
        room.doorOpen = true;
        room.doorProgress = 1f;
        room.doorSoundPlayed = true;
        ApplyDoorPose(room);
        var next = FindSequence(sequence + 1);
        if (next != null)
        {
            next.connected = true;
            if (next.rearSeal != null) next.rearSeal.SetActive(false);
            ScheduleRoomLight(next);
        }
        return true;
    }

    RoomSlot FindCurrentRoom()
    {
        var z = streamCamera.transform.position.z;
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = pool[i];
            if (room != null && z >= room.startZ && z <= room.endZ) return room;
        }
        return FindSequence(currentSequence) ?? pool[currentPoolIndex];
    }

    RoomSlot FindSequence(int sequence)
    {
        for (var i = 0; i < MaxRooms; i++)
            if (pool[i] != null && pool[i].sequence == sequence) return pool[i];
        return null;
    }

    int PoolIndex(RoomSlot target)
    {
        for (var i = 0; i < MaxRooms; i++) if (pool[i] == target) return i;
        return -1;
    }

    RoomSlot FindOldestRoom()
    {
        var oldest = pool[0];
        for (var i = 1; i < MaxRooms; i++) if (pool[i] != null && pool[i].sequence < oldest.sequence) oldest = pool[i];
        return oldest;
    }

    RoomSlot FindNewestRoom()
    {
        var newest = pool[0];
        for (var i = 1; i < MaxRooms; i++) if (pool[i] != null && pool[i].sequence > newest.sequence) newest = pool[i];
        return newest;
    }

    void BuildRoom(RoomSlot room, int index)
    {
        if (roomTemplate != null)
        {
            var copy = Instantiate(roomTemplate, room.root.transform);
            copy.name = "Editable room template";
            copy.transform.localPosition = Vector3.zero;
            room.entry = copy.transform.Find("Entry") ?? CreateEntry(room.root.transform);
        }
        else
        {
            var roomWall = ProfileMaterial(profileWallMaterials, room.rule, wallMaterial);
            var roomFloor = ProfileMaterial(profileFloorMaterials, room.rule, floorMaterial);
            var roomCeiling = ProfileMaterial(profileCeilingMaterials, room.rule, ceilingMaterial);
            Box(room.root.transform, "carpet floor", new Vector3(0f, -.12f, RoomLength * .5f), new Vector3(RoomWidth, .24f, RoomLength + .04f), roomFloor);
            Box(room.root.transform, "ceiling", new Vector3(0f, RoomHeight + .1f, RoomLength * .5f), new Vector3(RoomWidth, .2f, RoomLength + .04f), roomCeiling);
            Box(room.root.transform, "left wallpaper wall", new Vector3(-RoomWidth * .5f, RoomHeight * .5f, RoomLength * .5f), new Vector3(WallThickness, RoomHeight, RoomLength), roomWall);
            Box(room.root.transform, "right wallpaper wall", new Vector3(RoomWidth * .5f, RoomHeight * .5f, RoomLength * .5f), new Vector3(WallThickness, RoomHeight, RoomLength), roomWall);
            Box(room.root.transform, "left baseboard", new Vector3(-RoomWidth * .5f + .15f, .18f, RoomLength * .5f), new Vector3(.08f, .16f, RoomLength), trimMaterial ?? roomWall);
            Box(room.root.transform, "right baseboard", new Vector3(RoomWidth * .5f - .15f, .18f, RoomLength * .5f), new Vector3(.08f, .16f, RoomLength), trimMaterial ?? roomWall);
            // The printed texture carries the paper drops and the ceiling grid
            // (FrontRooms/Surface projects both in world metres), so no seam or
            // T-bar geometry is modelled: long raised strips read as wireframe
            // in a first-person corridor.
            // 2'x4' troffers: a painted-steel pan with the lens inset, one grid
            // cell each, grouped per lamp so a fixture, its light and its beam
            // move together when AlignFixtures snaps them to the world grid.
            room.fixtures = new Transform[FixtureZ.Length];
            for (var fixtureIndex = 0; fixtureIndex < FixtureZ.Length; fixtureIndex++)
            {
                var fixture = new GameObject("fluorescent fixture " + fixtureIndex).transform;
                fixture.SetParent(room.root.transform, false);
                room.fixtures[fixtureIndex] = fixture;
                Box(fixture, "fluorescent recessed pan " + fixtureIndex, new Vector3(0f, RoomHeight - .015f, 0f), new Vector3(TrofferWidth - .012f, .03f, TrofferLength - .012f), FrontRoomsSurfaces.PaintedMetal);
                Box(fixture, "fluorescent diffuser " + fixtureIndex, new Vector3(0f, RoomHeight - .033f, 0f), new Vector3(TrofferWidth - .06f, .006f, TrofferLength - .06f), fixtureMaterial ?? roomCeiling);
                BuildVolumetricBeam(fixture, fixtureIndex, ProfileLightColor(room.rule));
                var lightObject = new GameObject("fluorescent light " + fixtureIndex);
                lightObject.transform.SetParent(fixture, false);
                // A troffer only throws light downward: a wide spot at the lens
                // leaves the surrounding tiles to the floor bounce (ambient), so
                // the lit lens reads against the ceiling instead of blowing it out.
                lightObject.transform.localPosition = new Vector3(0f, RoomHeight - .05f, 0f);
                lightObject.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
                var light = lightObject.AddComponent<Light>();
                light.type = LightType.Spot;
                light.spotAngle = 162f;
                light.innerSpotAngle = 96f;
                light.range = ProfileLightRange(room.rule);
                light.intensity = ProfileLightIntensity(room.rule);
                light.color = ProfileLightColor(room.rule);
                // URP renders soft point-light shadows for every practical.
                // Contact darkness under furniture, behind door leaves and in
                // the corners is what sells a room lit only by its fixtures.
                light.shadows = LightShadows.Soft;
                light.shadowStrength = .92f;
                light.shadowNearPlane = .1f;
                light.bounceIntensity = diffuseCoefficient;
            }
            AlignFixtures(room);
            room.entry = CreateEntry(room.root.transform);
        }

        CacheRoomLights(room);
        CacheRoomLightVisuals(room);
        ResetRoomLights(room);

        room.rearSeal = Box(room.root.transform, "opaque rear boundary seal", new Vector3(0f, RoomHeight * .5f, RearSealOffset), new Vector3(RoomWidth, RoomHeight, .18f), ProfileMaterial(profileWallMaterials, room.rule, wallMaterial));
        room.rearSeal.SetActive(index == 0);
        BuildDoor(room);
        BuildProfileProps(room);
        RefreshRoomMaterials(room);
    }

    Transform CreateEntry(Transform parent)
    {
        var entry = new GameObject("Entry / 2m inside").transform;
        entry.SetParent(parent, false);
        entry.localPosition = new Vector3(0f, 0f, 2f);
        return entry;
    }

    /// <summary>
    /// Put each troffer in the centre of a world grid cell, just right of the
    /// room's centreline. The ceiling texture is projected in world space, so
    /// this is what makes the fixtures sit inside the printed T-bar grid.
    /// </summary>
    void AlignFixtures(RoomSlot room)
    {
        if (room?.fixtures == null || room.root == null) return;
        var origin = room.root.transform.position;
        var cellX = (Mathf.Floor((origin.x + GridX * .5f) / GridX) + .5f) * GridX;
        for (var i = 0; i < room.fixtures.Length; i++)
        {
            if (room.fixtures[i] == null) continue;
            var cellZ = (Mathf.Floor((origin.z + FixtureZ[i]) / GridZ) + .5f) * GridZ;
            room.fixtures[i].localPosition = new Vector3(cellX - origin.x, 0f, cellZ - origin.z);
        }
    }

    GameObject BuildVolumetricBeam(Transform fixture, int fixtureIndex, Color color)
    {
        var beam = new GameObject("volumetric fluorescent beam " + fixtureIndex);
        beam.transform.SetParent(fixture, false);
        // The mesh is a short, tapered frustum below the diffuser. Keeping it
        // as one low-poly surface avoids the crossed-quad edge lines that read
        // like a wireframe in the first-person camera.
        beam.transform.localPosition = new Vector3(0f, RoomHeight - .04f, 0f);
        var meshFilter = beam.AddComponent<MeshFilter>();
        var renderer = beam.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = volumetricLightMaterial;
        renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        renderer.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
        renderer.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
        meshFilter.sharedMesh = CreateVolumetricFrustumMesh(volumetricRange);
        if (volumetricLightMaterial != null)
        {
            renderer.enabled = true;
            renderer.sharedMaterial.SetColor("_Color", color);
        }
        else renderer.enabled = false;
        return beam;
    }

    static Mesh CreateVolumetricFrustumMesh(float range)
    {
        var topX = .18f;
        var topZ = .03f;
        var bottomX = .28f;
        var bottomZ = .06f;
        var mesh = new Mesh { name = "Fluorescent volumetric frustum" };
        mesh.SetVertices(new[]
        {
            new Vector3(-topX, 0f, -topZ), new Vector3(topX, 0f, -topZ),
            new Vector3(topX, 0f, topZ), new Vector3(-topX, 0f, topZ),
            new Vector3(-bottomX, -range, -bottomZ), new Vector3(bottomX, -range, -bottomZ),
            new Vector3(bottomX, -range, bottomZ), new Vector3(-bottomX, -range, bottomZ)
        });
        mesh.SetUVs(0, new[]
        {
            new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(0f, 1f),
            new Vector2(0f, 0f), new Vector2(1f, 0f), new Vector2(1f, 0f), new Vector2(0f, 0f)
        });
        mesh.SetTriangles(new[]
        {
            0, 4, 5, 0, 5, 1, // front
            2, 6, 7, 2, 7, 3  // back
        }, 0);
        mesh.RecalculateBounds();
        return mesh;
    }

    void BuildDoor(RoomSlot room)
    {
        EnsurePropMaterials();
        var frameMaterial = doorHardwareMaterial;
        // The threshold is cut into the end wall. Filling the two side spans
        // keeps the door connected to the room instead of reading as a free
        // standing prop in the distance.
        var sideWallWidth = (RoomWidth - DoorWidth) * .5f;
        var sideWallOffset = DoorWidth * .5f + sideWallWidth * .5f;
        var roomWall = ProfileMaterial(profileWallMaterials, room.rule, wallMaterial);
        // Keep the threshold return nearly flush with the paper plane. A deep
        // return exposes its unlit inner side when the door opens, which reads
        // as looking into a hollow model instead of a normal doorway.
        var leftReturn = Box(room.root.transform, "door wall return left", new Vector3(-sideWallOffset, RoomHeight * .5f, RoomLength), new Vector3(sideWallWidth, RoomHeight, DoorWallDepth), roomWall);
        var rightReturn = Box(room.root.transform, "door wall return right", new Vector3(sideWallOffset, RoomHeight * .5f, RoomLength), new Vector3(sideWallWidth, RoomHeight, DoorWallDepth), roomWall);
        Box(room.root.transform, "door wall above", new Vector3(0f, RoomHeight - DoorHeaderHeight * .5f, RoomLength), new Vector3(DoorWidth, DoorHeaderHeight, DoorWallDepth), roomWall);
        // The return's inner X-facing sides are almost unlit at the threshold
        // and can read as a black hollow shell from a close camera angle.
        // Add a deliberately front-facing paper plane one millimetre forward
        // of the return. It preserves the wallpaper and removes the apparent
        // X/inside lines without making the doorway a layered portal.
        var revealZ = RoomLength - DoorWallDepth * .5f - .002f;
        var outsideRevealZ = RoomLength + DoorWallDepth * .5f + .002f;
        var leftRevealSize = new Vector2(sideWallWidth, RoomHeight);
        var rightRevealSize = leftRevealSize;
        var headerRevealSize = new Vector2(DoorWidth, DoorHeaderHeight);
        InteriorReveal(room.root.transform, "door reveal left", new Vector3(-sideWallOffset, RoomHeight * .5f, revealZ), leftRevealSize, roomWall, true);
        InteriorReveal(room.root.transform, "door reveal right", new Vector3(sideWallOffset, RoomHeight * .5f, revealZ), rightRevealSize, roomWall, true);
        InteriorReveal(room.root.transform, "door reveal header", new Vector3(0f, RoomHeight - DoorHeaderHeight * .5f, revealZ), headerRevealSize, roomWall, true);
        // The stream can be viewed from either side after a handoff or a
        // Relay door break. A matching outward-facing cap prevents the far
        // side from becoming an apparent X-ray when the player looks back.
        InteriorReveal(room.root.transform, "door reveal left / far side", new Vector3(-sideWallOffset, RoomHeight * .5f, outsideRevealZ), leftRevealSize, roomWall, false);
        InteriorReveal(room.root.transform, "door reveal right / far side", new Vector3(sideWallOffset, RoomHeight * .5f, outsideRevealZ), rightRevealSize, roomWall, false);
        InteriorReveal(room.root.transform, "door reveal header / far side", new Vector3(0f, RoomHeight - DoorHeaderHeight * .5f, outsideRevealZ), headerRevealSize, roomWall, false);
        // The source-room door is an ordinary, flush double door. Avoid the
        // layered jamb/reveal/header pieces from the prototype; their exposed
        // edges made the threshold look like a sci-fi portal.
        var leftPivot = new GameObject("double door left hinge").transform;
        var doorPlaneZ = RoomLength - DoorWallDepth * .5f - .005f;
        leftPivot.SetParent(room.root.transform, false); leftPivot.localPosition = new Vector3(-DoorLeafPivotX, 0f, doorPlaneZ);
        var rightPivot = new GameObject("double door right hinge").transform;
        rightPivot.SetParent(room.root.transform, false); rightPivot.localPosition = new Vector3(DoorLeafPivotX, 0f, doorPlaneZ);
        var left = Box(leftPivot, "double door left", new Vector3(DoorLeafWidth * .5f, DoorLeafHeight * .5f, 0f), new Vector3(DoorLeafWidth, DoorLeafHeight, DoorLeafDepth), doorMaterial ?? wallMaterial);
        var right = Box(rightPivot, "double door right", new Vector3(-DoorLeafWidth * .5f, DoorLeafHeight * .5f, 0f), new Vector3(DoorLeafWidth, DoorLeafHeight, DoorLeafDepth), doorMaterial ?? wallMaterial);
        // Mount a shallow bar just outside each leaf face. The old single
        // handle sat on only the camera-facing side, so looking back through
        // a threshold made it appear to intersect the slab. A matching rear
        // bar keeps the hardware attached from either side of the doorway.
        const float handleDepth = .045f;
        var handleOffset = DoorLeafDepth * .5f + handleDepth * .5f + .006f;
        Box(leftPivot, "left door handle / near", new Vector3(1.02f, 1.22f, -handleOffset), new Vector3(.055f, .18f, handleDepth), frameMaterial);
        Box(leftPivot, "left door handle / far", new Vector3(1.02f, 1.22f, handleOffset), new Vector3(.055f, .18f, handleDepth), frameMaterial);
        Box(rightPivot, "right door handle / near", new Vector3(-1.02f, 1.22f, -handleOffset), new Vector3(.055f, .18f, handleDepth), frameMaterial);
        Box(rightPivot, "right door handle / far", new Vector3(-1.02f, 1.22f, handleOffset), new Vector3(.055f, .18f, handleDepth), frameMaterial);
        // Brushed kick plates on both faces: the scuffed lower band of a real
        // commercial door, and a bright edge that catches the practicals.
        var plateOffset = DoorLeafDepth * .5f + .003f;
        foreach (var side in new[] { -1f, 1f })
        {
            Box(leftPivot, "left door kick plate " + (side < 0 ? "/ near" : "/ far"), new Vector3(DoorLeafWidth * .5f, .14f, side * plateOffset), new Vector3(DoorLeafWidth - .05f, .25f, .004f), frameMaterial);
            Box(rightPivot, "right door kick plate " + (side < 0 ? "/ near" : "/ far"), new Vector3(-DoorLeafWidth * .5f, .14f, side * plateOffset), new Vector3(DoorLeafWidth - .05f, .25f, .004f), frameMaterial);
        }
        // The leaf itself supplies the dark reveal. The former full-height
        // gasket strips read as exposed wireframe when the door is closed, so
        // keep the visual seam implicit in the leaf and retain only the small
        // handles.
        room.leftDoor = leftPivot; room.rightDoor = rightPivot;
        room.doorwayColliders = new[]
        {
            leftReturn.GetComponent<BoxCollider>(),
            rightReturn.GetComponent<BoxCollider>(),
            left.GetComponent<BoxCollider>(),
            right.GetComponent<BoxCollider>()
        };
        var audioObject = new GameObject("door creak / spatial");
        audioObject.transform.SetParent(room.root.transform, false);
        audioObject.transform.localPosition = new Vector3(0f, RoomHeight * .42f, RoomLength);
        var audio = audioObject.AddComponent<AudioSource>();
        audio.clip = doorCreakClip;
        audio.playOnAwake = false;
        audio.loop = false;
        audio.spatialBlend = 1f;
        audio.minDistance = 2.5f;
        audio.maxDistance = 20f;
        audio.rolloffMode = AudioRolloffMode.Logarithmic;
        audio.dopplerLevel = .08f;
        audio.priority = 72;
        room.doorAudio = audio;
        room.doorProgress = 0f; room.doorOpening = false; room.doorOpen = false; room.doorSoundPlayed = false;
        ApplyDoorPose(room);
    }

    void ResolveDoorwayOverlap(RoomSlot room, bool doorPassable, ref Vector3 candidate)
    {
        if (room == null || room.doorwayColliders == null) return;
        const float playerRadius = .18f;
        var leafOpen = room.leftDoor != null
            && Quaternion.Angle(room.leftDoor.localRotation, Quaternion.identity) > 1f;
        // Only swung leaves need a transform sync; the return colliders are
        // static and their cached bounds remain valid between door motions.
        if (leafOpen) Physics.SyncTransforms();
        for (var i = 0; i < room.doorwayColliders.Length; i++)
        {
            // A closed leaf is already handled by the threshold clamp above.
            // Applying its AABB while closed would overlap the two leaves at
            // the centre seam and incorrectly block a straight-on approach.
            if (i >= 2 && (!doorPassable || !leafOpen)) continue;
            var collider = room.doorwayColliders[i];
            if (collider == null || !collider.enabled || !collider.gameObject.activeInHierarchy) continue;
            var bounds = collider.bounds;
            var minX = bounds.min.x - playerRadius;
            var maxX = bounds.max.x + playerRadius;
            var minZ = bounds.min.z - playerRadius;
            var maxZ = bounds.max.z + playerRadius;
            if (candidate.x <= minX || candidate.x >= maxX || candidate.z <= minZ || candidate.z >= maxZ) continue;

            // Resolve along the shallowest penetration. This keeps the
            // doorway aperture usable while stopping the camera from entering
            // a leaf or a return and revealing its interior faces.
            var pushLeft = candidate.x - minX;
            var pushRight = maxX - candidate.x;
            var pushBack = candidate.z - minZ;
            var pushForward = maxZ - candidate.z;
            var smallest = Mathf.Min(Mathf.Min(pushLeft, pushRight), Mathf.Min(pushBack, pushForward));
            if (smallest == pushLeft) candidate.x = minX;
            else if (smallest == pushRight) candidate.x = maxX;
            else if (smallest == pushBack) candidate.z = minZ;
            else candidate.z = maxZ;
        }
    }

    static Material ProfileMaterial(Material[] materials, RoomRule rule, Material fallback)
    {
        var index = (int)rule;
        return materials != null && index >= 0 && index < materials.Length && materials[index] != null ? materials[index] : fallback;
    }

    // Tube colour per profile. The yellow of Level 0 comes from the paper and
    // the camera's white balance (post stack), not from the lamps, so the
    // tubes stay near cool-white; Shift's ballasts drift green, the Office is
    // a cooler 90s cool-white, Run's few working tubes are dim and neutral.
    static Color ProfileLightColor(RoomRule rule)
    {
        switch (rule)
        {
            case RoomRule.Shift: return new Color(.86f, .93f, .78f);
            case RoomRule.Office: return new Color(.93f, .96f, 1f);
            case RoomRule.Run: return new Color(.88f, .92f, .94f);
            case RoomRule.Exit: return new Color(.62f, .92f, .90f);
            default: return new Color(1f, .96f, .88f);
        }
    }

    // URP point lights fall off with the inverse square of distance, so these
    // are physical-ish lamp outputs, not the built-in renderer's 0..1 values.
    static float ProfileLightIntensity(RoomRule rule)
    {
        switch (rule)
        {
            case RoomRule.Shift: return 4.2f;
            case RoomRule.Office: return 6.0f;
            case RoomRule.Run: return .6f;
            case RoomRule.Exit: return 4.4f;
            default: return 5.2f;
        }
    }

    static float ProfileLightRange(RoomRule rule) => rule == RoomRule.Run ? 6.5f : 10f;

    // Per-lamp odds that a ballast is dead (never lights) or failing (sways
    // and drops out forever). Level ! is mostly dark under its exit signs.
    static void LampOdds(RoomRule rule, out float dead, out float unstable)
    {
        switch (rule)
        {
            case RoomRule.Shift: dead = .10f; unstable = .32f; break;
            case RoomRule.Office: dead = .03f; unstable = .06f; break;
            case RoomRule.Run: dead = .70f; unstable = .45f; break;
            case RoomRule.Exit: dead = 0f; unstable = .05f; break;
            default: dead = .02f; unstable = .10f; break;
        }
    }

    void EnsurePropMaterials()
    {
        if (officeDeskMaterial != null) return;
        officeDeskMaterial = FrontRoomsSurfaces.Lit("Office / laminate desk", new Color(.40f, .36f, .30f), .38f);
        officeMetalMaterial = FrontRoomsSurfaces.Lit("Office / putty steel", new Color(.56f, .54f, .50f), .45f, .55f);
        officePaperMaterial = FrontRoomsSurfaces.Lit("Office / paper", new Color(.86f, .84f, .78f), .1f);
        officeGlassMaterial = FrontRoomsSurfaces.Lit("Office / cooler bottle", new Color(.40f, .60f, .66f), .92f, 0f, new Color(.04f, .08f, .09f));
        officeDarkMaterial = FrontRoomsSurfaces.BlackedGlass;
        runChromeMaterial = FrontRoomsSurfaces.Lit("Run / chrome", new Color(.70f, .70f, .68f), .78f, .9f);
        runVinylMaterial = FrontRoomsSurfaces.Lit("Run / teal vinyl seat", new Color(.20f, .36f, .35f), .42f);
        runBedMaterial = FrontRoomsSurfaces.Lit("Run / mattress", new Color(.72f, .80f, .77f), .25f);
        runRailMaterial = FrontRoomsSurfaces.Lit("Run / vinyl handrail", new Color(.72f, .68f, .58f), .48f);
        outletMaterial = FrontRoomsSurfaces.Lit("Level 0 / outlet plate", new Color(.82f, .78f, .66f), .35f);
        doorHardwareMaterial = FrontRoomsSurfaces.Lit("Door / brushed steel", new Color(.64f, .63f, .60f), .62f, .9f);
    }

    void BuildProfileProps(RoomSlot room)
    {
        EnsurePropMaterials();
        room.profileVariants = new GameObject[5];
        for (var ruleIndex = 0; ruleIndex < room.profileVariants.Length; ruleIndex++)
        {
            var rule = (RoomRule)ruleIndex;
            var props = new GameObject("Profile props / " + rule);
            props.transform.SetParent(room.root.transform, false);
            room.profileVariants[ruleIndex] = props;
            props.SetActive(rule == room.rule);
            var roomWall = ProfileMaterial(profileWallMaterials, rule, wallMaterial);
            if (rule == RoomRule.Lobby || rule == RoomRule.Shift || rule == RoomRule.Exit)
            {
                // Level 0's scattered electrical outlets, low on the paper.
                var wallFace = RoomWidth * .5f - WallThickness * .5f - .006f;
                foreach (var (x, z) in new[] { (-wallFace, 2.3f), (wallFace, 5.8f), (-wallFace, 9.1f) })
                {
                    var outlet = Box(props.transform, "outlet plate", new Vector3(x, .32f, z), new Vector3(.012f, .115f, .07f), outletMaterial);
                    outlet.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                }
            }
            else if (rule == RoomRule.Office)
            {
                // Level 4: ordinary, low-density office objects. The centre
                // lane remains open for threshold reading and pursuit.
                for (var i = -1; i <= 1; i++)
                {
                    var x = i * 2.45f + (i == 1 ? .22f : 0f);
                    var z = 6.65f;
                    Box(props.transform, "office desk surface", new Vector3(x, .72f, z), new Vector3(1.75f, .12f, .72f), officeDeskMaterial);
                    Box(props.transform, "office desk leg left", new Vector3(x - .67f, .35f, z), new Vector3(.12f, .62f, .45f), officeMetalMaterial);
                    Box(props.transform, "office desk leg right", new Vector3(x + .67f, .35f, z), new Vector3(.12f, .62f, .45f), officeMetalMaterial);
                    Box(props.transform, "office CRT monitor", new Vector3(x, 1.08f, z + .18f), new Vector3(.48f, .34f, .08f), officeMetalMaterial);
                    Box(props.transform, "office monitor stand", new Vector3(x, .88f, z + .1f), new Vector3(.08f, .18f, .08f), officeMetalMaterial);
                    Box(props.transform, "office paper stack", new Vector3(x - .42f, .82f, z - .16f), new Vector3(.22f, .03f, .28f), officePaperMaterial);
                    Box(props.transform, "office cubicle panel", new Vector3(x, 1.2f, z + .82f), new Vector3(1.45f, 1.0f, .09f), FrontRoomsSurfaces.CubicleFabric);
                }
                Box(props.transform, "office water cooler body", new Vector3(4.25f, .9f, 3.8f), new Vector3(.48f, .9f, .48f), officeMetalMaterial);
                Box(props.transform, "office water cooler bottle", new Vector3(4.25f, 1.58f, 3.8f), new Vector3(.31f, .42f, .31f), officeGlassMaterial);
                Box(props.transform, "office filing cabinet", new Vector3(-4.25f, .78f, 8.15f), new Vector3(.56f, .78f, .52f), officeMetalMaterial);
                Box(props.transform, "office cabinet handle", new Vector3(-4.25f, 1.02f, 7.87f), new Vector3(.22f, .035f, .035f), officePaperMaterial);
                // Level 4's windows are usually blacked out. This shallow
                // panel reads as a sealed window at the edge of the room,
                // while the central sightline stays clear for pursuit.
                Box(props.transform, "office blacked-out window", new Vector3(-5.28f, 1.68f, 3.15f), new Vector3(.06f, 1.42f, 2.15f), officeDarkMaterial);
                Box(props.transform, "office window frame top", new Vector3(-5.22f, 2.42f, 3.15f), new Vector3(.10f, .08f, 2.25f), officeMetalMaterial);
                Box(props.transform, "office window frame bottom", new Vector3(-5.22f, .94f, 3.15f), new Vector3(.10f, .08f, 2.25f), officeMetalMaterial);
                // A dead vending machine is a recognizable 90s office relic;
                // it is deliberately unlit so it cannot compete with the
                // fluorescent room reveal.
                Box(props.transform, "office vending machine", new Vector3(4.88f, 1.12f, 9.35f), new Vector3(.46f, 1.12f, .72f), officeMetalMaterial);
                Box(props.transform, "office vending machine display", new Vector3(4.62f, 1.62f, 9.35f), new Vector3(.025f, .30f, .48f), officeDarkMaterial);
            }
            else if (rule == RoomRule.Run)
            {
                // Level !: a white hospital corridor, dim except for the red
                // exit signs hanging from the ceiling. Chairs and a gurney are
                // the obstacles the player has to run around.
                var rail = RoomWidth * .5f - WallThickness * .5f - .05f;
                Box(props.transform, "run handrail left", new Vector3(-rail, .92f, RoomLength * .5f), new Vector3(.07f, .11f, RoomLength - 1.2f), runRailMaterial);
                Box(props.transform, "run handrail right", new Vector3(rail, .92f, RoomLength * .5f), new Vector3(.07f, .11f, RoomLength - 1.2f), runRailMaterial);
                for (var c = 0; c < 3; c++)
                {
                    var cz = 2.6f + c * .62f;
                    var cx = -RoomWidth * .5f + .55f;
                    Box(props.transform, "run waiting chair seat", new Vector3(cx, .45f, cz), new Vector3(.48f, .07f, .5f), runVinylMaterial);
                    Box(props.transform, "run waiting chair back", new Vector3(cx - .22f, .74f, cz), new Vector3(.06f, .48f, .5f), runVinylMaterial);
                    Box(props.transform, "run waiting chair leg", new Vector3(cx + .17f, .21f, cz), new Vector3(.03f, .42f, .44f), runChromeMaterial);
                }
                var bed = new GameObject("run gurney").transform;
                bed.SetParent(props.transform, false);
                bed.localPosition = new Vector3(3.4f, 0f, 7.3f);
                bed.localRotation = Quaternion.Euler(0f, -14f, 0f);
                Box(bed, "run gurney frame", new Vector3(0f, .56f, 0f), new Vector3(.82f, .07f, 2.02f), runChromeMaterial);
                Box(bed, "run gurney mattress", new Vector3(0f, .66f, 0f), new Vector3(.78f, .13f, 1.94f), runBedMaterial);
                Box(bed, "run gurney rail left", new Vector3(-.43f, .80f, 0f), new Vector3(.025f, .16f, 1.4f), runChromeMaterial);
                Box(bed, "run gurney rail right", new Vector3(.43f, .80f, 0f), new Vector3(.025f, .16f, 1.4f), runChromeMaterial);
                foreach (var (wx, wz) in new[] { (-.34f, -.9f), (.34f, -.9f), (-.34f, .9f), (.34f, .9f) })
                {
                    Box(bed, "run gurney post", new Vector3(wx, .30f, wz), new Vector3(.035f, .5f, .035f), runChromeMaterial);
                    Box(bed, "run gurney wheel", new Vector3(wx, .06f, wz), new Vector3(.04f, .11f, .11f), officeDarkMaterial);
                }
                Cylinder(props.transform, "run IV pole", new Vector3(4.3f, .95f, 8.6f), new Vector3(.03f, .95f, .03f), runChromeMaterial, Vector3.zero);
                // Hanging exit signs: battery fixtures that stay lit when the
                // ballasts fail, and the red source of the whole level.
                foreach (var sz in new[] { 3.4f, 9.2f })
                {
                    var sign = new GameObject("run exit sign").transform;
                    sign.SetParent(props.transform, false);
                    sign.localPosition = new Vector3(0f, 2.36f, sz);
                    Box(sign, "run exit sign housing", Vector3.zero, new Vector3(.40f, .21f, .05f), officeDarkMaterial);
                    SignFace(sign, "run exit sign face / near", new Vector3(0f, 0f, -.027f), new Vector2(.36f, .18f), FrontRoomsSurfaces.ExitSign, true);
                    SignFace(sign, "run exit sign face / far", new Vector3(0f, 0f, .027f), new Vector2(.36f, .18f), FrontRoomsSurfaces.ExitSign, false);
                    Box(sign, "run exit sign rod left", new Vector3(-.15f, .32f, 0f), new Vector3(.012f, .43f, .012f), runChromeMaterial);
                    Box(sign, "run exit sign rod right", new Vector3(.15f, .32f, 0f), new Vector3(.012f, .43f, .012f), runChromeMaterial);
                    var red = new GameObject("run exit sign light").AddComponent<Light>();
                    red.transform.SetParent(sign, false);
                    red.transform.localPosition = new Vector3(0f, -.40f, 0f);
                    red.type = LightType.Point;
                    red.color = new Color(1f, .10f, .06f);
                    red.intensity = 3.6f;
                    red.range = 9.5f;
                    red.shadows = LightShadows.Soft;
                    red.shadowStrength = .85f;
                }
            }
            else if (rule == RoomRule.Exit)
            {
                Box(props.transform, "exit threshold marker", new Vector3(0f, .04f, 5.9f), new Vector3(2.8f, .03f, .12f), roomWall);
            }
        }
    }

    void RefreshRoomMaterials(RoomSlot room)
    {
        if (room == null || room.root == null) return;
        var wall = ProfileMaterial(profileWallMaterials, room.rule, wallMaterial);
        var floor = ProfileMaterial(profileFloorMaterials, room.rule, floorMaterial);
        var ceiling = ProfileMaterial(profileCeilingMaterials, room.rule, ceilingMaterial);
        var renderers = room.root.GetComponentsInChildren<Renderer>(true);
        for (var i = 0; i < renderers.Length; i++)
        {
            var renderer = renderers[i];
            if (renderer == null) continue;
            var name = renderer.gameObject.name.ToLowerInvariant();
            if (name.Contains("floor") || name.Contains("carpet")) renderer.sharedMaterial = floor;
            else if (name.Contains("ceiling")) renderer.sharedMaterial = ceiling;
            else if (name.Contains("wall") || name.Contains("seal") || name.Contains("partition") || name.Contains("threshold marker")) renderer.sharedMaterial = wall;
        }
        if (room.roomLights != null)
        {
            for (var i = 0; i < room.roomLights.Length; i++)
            {
                var light = room.roomLights[i];
                if (light == null) continue;
                light.color = ProfileLightColor(room.rule);
                if (light.gameObject.name.Contains("fluorescent"))
                {
                    room.lightBaseIntensity[i] = ProfileLightIntensity(room.rule);
                    light.range = ProfileLightRange(room.rule);
                    light.bounceIntensity = diffuseCoefficient;
                }
            }
        }
        // A door's far-side reveal is seen from the next room, so it wears that
        // room's paper; this room's wall also faces back into the previous one.
        var next = FindSequence(room.sequence + 1);
        SetFarSideReveals(room, next != null ? ProfileMaterial(profileWallMaterials, next.rule, wall) : wall);
        var previous = FindSequence(room.sequence - 1);
        if (previous != null) SetFarSideReveals(previous, wall);
        // Prismatic lenses in Level 0 and Run; parabolic louvers in the Office.
        var lens = room.rule == RoomRule.Office ? FrontRoomsSurfaces.OfficeLouver : (fixtureMaterial ?? FrontRoomsSurfaces.TrofferLens);
        if (room.lightDiffusers != null)
            for (var i = 0; i < room.lightDiffusers.Length; i++)
                if (room.lightDiffusers[i] != null) room.lightDiffusers[i].sharedMaterial = lens;
        if (room.lightOutputLevel != null)
            for (var i = 0; i < room.lightOutputLevel.Length; i++)
                ApplyFixtureVisual(room, i, room.lightOutputLevel[i], room.lightOutputEnabled != null && i < room.lightOutputEnabled.Length && room.lightOutputEnabled[i]);
        if (room.profileVariants != null)
            for (var i = 0; i < room.profileVariants.Length; i++)
                if (room.profileVariants[i] != null) room.profileVariants[i].SetActive(i == (int)room.rule);
    }

    static void SetFarSideReveals(RoomSlot room, Material material)
    {
        if (room?.root == null || material == null) return;
        foreach (var renderer in room.root.GetComponentsInChildren<Renderer>(true))
            if (renderer.gameObject.name.EndsWith("/ far side", StringComparison.Ordinal)) renderer.sharedMaterial = material;
    }

    void CacheRoomLights(RoomSlot room)
    {
        room.roomLights = room.root.GetComponentsInChildren<Light>(true);
        room.lightBaseIntensity = new float[room.roomLights.Length];
        room.lightWasEnabled = new bool[room.roomLights.Length];
        for (var i = 0; i < room.roomLights.Length; i++)
        {
            var light = room.roomLights[i];
            room.lightBaseIntensity[i] = light == null ? 0f : light.intensity;
            room.lightWasEnabled[i] = light != null && light.enabled && room.lightBaseIntensity[i] > 0f;
        }
    }

    void CacheRoomLightVisuals(RoomSlot room)
    {
        var count = room.roomLights == null ? 0 : room.roomLights.Length;
        room.lightDiffusers = new Renderer[count];
        room.volumetricRenderers = new Renderer[count];
        room.lightDiffuserBlocks = new MaterialPropertyBlock[count];
        room.volumetricBlocks = new MaterialPropertyBlock[count];
        room.lightOutputLevel = new float[count];
        room.lightOutputEnabled = new bool[count];
        var renderers = room.root.GetComponentsInChildren<Renderer>(true);
        for (var i = 0; i < renderers.Length; i++)
        {
            var renderer = renderers[i];
            if (renderer == null) continue;
            var name = renderer.gameObject.name;
            var marker = name.IndexOf("fluorescent diffuser ", StringComparison.OrdinalIgnoreCase);
            var isBeam = name.IndexOf("volumetric fluorescent beam ", StringComparison.OrdinalIgnoreCase) >= 0;
            if (marker < 0 && !isBeam) continue;
            var start = marker >= 0 ? marker + "fluorescent diffuser ".Length : name.IndexOf("volumetric fluorescent beam ", StringComparison.OrdinalIgnoreCase) + "volumetric fluorescent beam ".Length;
            if (!int.TryParse(name.Substring(start), out var fixtureIndex) || fixtureIndex < 0 || fixtureIndex >= count) continue;
            if (isBeam)
            {
                room.volumetricRenderers[fixtureIndex] = renderer;
                room.volumetricBlocks[fixtureIndex] = new MaterialPropertyBlock();
                renderer.sharedMaterial = volumetricLightMaterial;
            }
            else
            {
                room.lightDiffusers[fixtureIndex] = renderer;
                room.lightDiffuserBlocks[fixtureIndex] = new MaterialPropertyBlock();
            }
        }
    }

    void ResetRoomLights(RoomSlot room)
    {
        ConfigureLightProfile(room);
        if (room.roomLights == null) return;
        for (var i = 0; i < room.roomLights.Length; i++)
            if (room.roomLights[i] != null) SetFixtureOutput(room, i, 0f, false);
    }

    /// <summary>
    /// Deal each fixture its own ballast from the room's sequence number and
    /// the lamp index: strike delay, flicker count/period/duty, rise time, and
    /// whether it is failing or dead (odds per profile, see LampOdds). Hashing
    /// by sequence means a recycled pool slot never repeats its old pattern.
    /// </summary>
    void ConfigureLightProfile(RoomSlot room)
    {
        if (room == null) return;
        var count = room.roomLights == null ? 0 : room.roomLights.Length;
        if (room.lampState == null || room.lampState.Length != count)
        {
            room.lampState = new LampState[count];
            room.lampDelay = new float[count];
            room.lampFlickerCount = new int[count];
            room.lampFlickerElapsed = new float[count];
            room.lampFlickerPeriod = new float[count];
            room.lampFlickerOnFraction = new float[count];
            room.lampFlickerPhase = new float[count];
            room.lampRevealSeconds = new float[count];
            room.lampRevealProgress = new float[count];
            room.lampRiseFrom = new float[count];
            room.lampUnstable = new bool[count];
            room.lampDead = new bool[count];
            room.lampUnstableElapsed = new float[count];
            room.lampNoisePhase = new float[count];
        }
        LampOdds(room.rule, out var deadChance, out var unstableChance);
        var sequence = Mathf.Max(0, room.sequence);
        for (var lamp = 0; lamp < count; lamp++)
        {
            var key = sequence * 16 + lamp;
            var band = Hash01(key, 11);
            room.lampFlickerCount[lamp] = band < .27f ? 0
                : band < .58f ? 1
                : band < .87f ? 2 + Mathf.FloorToInt(Hash01(key, 23) * 3f)
                : 2 + Mathf.FloorToInt(Hash01(key, 29) * 4f);
            room.lampFlickerPeriod[lamp] = Mathf.Lerp(.13f, .34f, Hash01(key, 37));
            room.lampFlickerOnFraction[lamp] = Mathf.Lerp(.20f, .50f, Hash01(key, 41));
            room.lampFlickerPhase[lamp] = Hash01(key, 73) * room.lampFlickerPeriod[lamp];
            room.lampRevealSeconds[lamp] = Mathf.Lerp(.45f, 1.6f, Hash01(key, 47));
            room.lampNoisePhase[lamp] = Hash01(key, 53) * 19f;
            // Ballasts strike on their own: 0.4 to 2.2 s after the door opens.
            room.lampDelay[lamp] = Mathf.Lerp(.4f, 2.2f, Hash01(key, 59));
            room.lampDead[lamp] = Hash01(key, 79) < deadChance;
            room.lampUnstable[lamp] = !room.lampDead[lamp] && Hash01(key, 83) < unstableChance;
            room.lampState[lamp] = LampState.Off;
            room.lampFlickerElapsed[lamp] = 0f;
            room.lampRevealProgress[lamp] = 0f;
            room.lampRiseFrom[lamp] = 0f;
            room.lampUnstableElapsed[lamp] = 0f;
        }
    }

    static float Hash01(int sequence, int salt)
    {
        unchecked
        {
            uint x = (uint)(sequence * 92821 + salt * 68917 + LightRandomSeed);
            x ^= x >> 16;
            x *= 2246822519u;
            x ^= x >> 13;
            x *= 3266489917u;
            x ^= x >> 16;
            return (x & 0x00ffffffu) / 16777215f;
        }
    }

    void ActivateRoomLightImmediately(RoomSlot room)
    {
        if (room == null || room.lampState == null) return;
        for (var lamp = 0; lamp < room.lampState.Length; lamp++)
        {
            if (room.lampDead[lamp])
            {
                room.lampState[lamp] = LampState.Dead;
                SetFixtureOutput(room, lamp, 0f, false);
            }
            else if (room.lampUnstable[lamp])
            {
                room.lampState[lamp] = LampState.Unstable;
                SetFixtureOutput(room, lamp, .4f, true);
            }
            else
            {
                room.lampState[lamp] = LampState.Steady;
                SetFixtureOutput(room, lamp, 1f, true);
            }
        }
    }

    void SetFixtureOutput(RoomSlot room, int fixtureIndex, float normalizedIntensity, bool enabled)
    {
        if (room == null || room.roomLights == null || fixtureIndex < 0 || fixtureIndex >= room.roomLights.Length) return;
        var light = room.roomLights[fixtureIndex];
        if (light == null || room.lightWasEnabled == null || fixtureIndex >= room.lightWasEnabled.Length || !room.lightWasEnabled[fixtureIndex]) return;
        normalizedIntensity = Mathf.Clamp01(normalizedIntensity);
        var active = enabled && normalizedIntensity > .0005f;
        // Built-in realtime GI is intentionally disabled in this project, so
        // bounceIntensity alone is not a visible diffuse control. Scale the
        // direct practical output as well, while keeping a useful floor when
        // the coefficient is tuned down for a darker grade.
        var diffuseScale = Mathf.Lerp(.45f, 1f, Mathf.Clamp01(diffuseCoefficient));
        light.bounceIntensity = Mathf.Clamp01(diffuseCoefficient);
        light.enabled = active;
        light.intensity = room.lightBaseIntensity[fixtureIndex] * normalizedIntensity * diffuseScale;
        if (room.lightOutputLevel != null && fixtureIndex < room.lightOutputLevel.Length)
            room.lightOutputLevel[fixtureIndex] = normalizedIntensity;
        if (room.lightOutputEnabled != null && fixtureIndex < room.lightOutputEnabled.Length)
            room.lightOutputEnabled[fixtureIndex] = active;
        ApplyFixtureVisual(room, fixtureIndex, normalizedIntensity, active);
    }

    void ApplyFixtureVisual(RoomSlot room, int fixtureIndex, float level, bool enabled)
    {
        var color = ProfileLightColor(room.rule);
        if (room.lightDiffusers != null && fixtureIndex < room.lightDiffusers.Length && room.lightDiffusers[fixtureIndex] != null)
        {
            var renderer = room.lightDiffusers[fixtureIndex];
            var block = room.lightDiffuserBlocks[fixtureIndex] ?? (room.lightDiffuserBlocks[fixtureIndex] = new MaterialPropertyBlock());
            renderer.GetPropertyBlock(block);
            var emission = color * Mathf.Lerp(.02f, 2.6f, enabled ? level : 0f);
            block.SetColor("_EmissionColor", emission);
            block.SetColor("_Color", Color.Lerp(new Color(.045f, .042f, .035f), Color.white, enabled ? level : 0f));
            renderer.SetPropertyBlock(block);
        }
        if (room.volumetricRenderers == null || fixtureIndex >= room.volumetricRenderers.Length || room.volumetricRenderers[fixtureIndex] == null) return;
        var volume = room.volumetricRenderers[fixtureIndex];
        var volumeBlock = room.volumetricBlocks[fixtureIndex] ?? (room.volumetricBlocks[fixtureIndex] = new MaterialPropertyBlock());
        volume.GetPropertyBlock(volumeBlock);
        volumeBlock.SetColor("_Color", color);
        volumeBlock.SetFloat("_Density", enabled ? volumetricDensity * level : 0f);
        volumeBlock.SetFloat("_DiffuseCoefficient", Mathf.Clamp01(diffuseCoefficient));
        volume.enabled = enabled && volumetricDensity > .0005f;
        volume.SetPropertyBlock(volumeBlock);
    }

    void BeginDoorOpening(RoomSlot room)
    {
        if (room == null) return;
        room.doorOpening = true;
        if (room.doorSoundPlayed) return;
        room.doorSoundPlayed = true;
        DoorOpeningStarted?.Invoke(room.sequence, new Vector3(centerX, RoomHeight * .42f, room.endZ));
        if (room.doorAudio == null || (doorCreakClip == null && doorLatchClip == null && doorTravelClip == null)) return;
        // A very small deterministic pitch variation keeps repeated streamed
        // doors from sounding phase-locked while preserving the same source.
        room.doorAudio.pitch = .97f + Mathf.Abs(room.sequence % 7) * .01f;
        if (doorLatchClip != null) room.doorAudio.PlayOneShot(doorLatchClip, .42f);
        if (doorCreakClip != null) room.doorAudio.PlayOneShot(doorCreakClip, .78f);
        if (doorTravelClip != null) room.doorAudio.PlayOneShot(doorTravelClip, .42f);
    }

    void ApplyDoorPose(RoomSlot room)
    {
        if (room.leftDoor == null || room.rightDoor == null) return;
        // A hinge does not stop with a hard linear snap. Smoothstep eases the
        // last few degrees to zero velocity, removing the visible end-of-open
        // hitch while preserving the same 0.9 s motion clock used by the
        // stream and title mark.
        var t = Mathf.Clamp01(room.doorProgress);
        t = t * t * (3f - 2f * t);
        // Stop just shy of a right angle. This keeps a small construction
        // margin for the thin slab and avoids any floating-point sweep into
        // the side return while still reading fully open.
        var angle = 88f * t;
        room.leftDoor.localRotation = Quaternion.Euler(0f, -angle, 0f);
        room.rightDoor.localRotation = Quaternion.Euler(0f, angle, 0f);
    }

    GameObject Box(Transform parent, string name, Vector3 localPosition, Vector3 scale, Material material)
    {
        var box = new GameObject(name);
        box.name = name;
        box.transform.SetParent(parent, false);
        box.transform.localPosition = localPosition;
        box.transform.localScale = Vector3.one;
        var meshFilter = box.AddComponent<MeshFilter>();
        var meshRenderer = box.AddComponent<MeshRenderer>();
        // Every box is planar. The bevelled box's front cap is a fan around one
        // centre vertex with smoothed normals, which shaded large flat faces
        // (cubicle panels, desks) with a visible diagonal X under URP lighting.
        meshFilter.sharedMesh = FrontRoomsFilmMesh.GetPlanarBox(scale);
        meshRenderer.sharedMaterial = material;
        var collider = box.AddComponent<BoxCollider>();
        collider.size = scale;
        return box;
    }

    GameObject InteriorReveal(Transform parent, string name, Vector3 localPosition, Vector2 size, Material material, bool faceBack)
    {
        var reveal = new GameObject(name);
        reveal.transform.SetParent(parent, false);
        reveal.transform.localPosition = localPosition;
        var meshFilter = reveal.AddComponent<MeshFilter>();
        var meshRenderer = reveal.AddComponent<MeshRenderer>();
        var hx = size.x * .5f;
        var hy = size.y * .5f;
        var mesh = new Mesh { name = "Doorway interior reveal" };
        mesh.SetVertices(faceBack
            ? new[]
            {
                new Vector3(hx, -hy, 0f), new Vector3(-hx, -hy, 0f),
                new Vector3(-hx, hy, 0f), new Vector3(hx, hy, 0f)
            }
            : new[]
            {
                new Vector3(-hx, -hy, 0f), new Vector3(hx, -hy, 0f),
                new Vector3(hx, hy, 0f), new Vector3(-hx, hy, 0f)
            });
        var normal = faceBack ? Vector3.back : Vector3.forward;
        mesh.SetNormals(new[] { normal, normal, normal, normal });
        mesh.SetUVs(0, new[]
        {
            new Vector2(0f, 0f), new Vector2(size.x, 0f),
            new Vector2(size.x, size.y), new Vector2(0f, size.y)
        });
        mesh.SetTriangles(new[] { 0, 1, 2, 0, 2, 3 }, 0);
        mesh.RecalculateBounds();
        meshRenderer.sharedMaterial = material;
        meshRenderer.receiveShadows = false;
        meshRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        meshFilter.sharedMesh = mesh;
        return reveal;
    }

    void SignFace(Transform parent, string name, Vector3 localPosition, Vector2 size, Material material, bool faceBack)
    {
        var face = InteriorReveal(parent, name, localPosition, size, material, faceBack);
        var renderer = face.GetComponent<Renderer>();
        renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
    }

    GameObject Cylinder(Transform parent, string name, Vector3 localPosition, Vector3 scale, Material material, Vector3 eulerAngles)
    {
        var cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        cylinder.name = name;
        cylinder.transform.SetParent(parent, false);
        cylinder.transform.localPosition = localPosition;
        cylinder.transform.localScale = scale;
        cylinder.transform.localRotation = Quaternion.Euler(eulerAngles);
        var renderer = cylinder.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = material;
        return cylinder;
    }
}
