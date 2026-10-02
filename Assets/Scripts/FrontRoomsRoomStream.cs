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
    // Leave only a small construction tolerance below the header. The old
    // 2.4m leaf stopped 0.26m below the 2.66m header bottom.
    const float DoorHeaderHeight = .24f;
    const float DoorLeafHeight = RoomHeight - .02f;
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
    const float LightRevealDelaySeconds = 1f;
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

    sealed class RoomSlot
    {
        public GameObject root;
        public Transform entry;
        public Transform leftDoor;
        public Transform rightDoor;
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
        public float lightRevealProgress;
        public bool lightRevealStarted;
        public bool lightTriggerScheduled;
        public float lightDelayRemaining;
        public float lightFlickerElapsed;
        public int lightFlickerCount;
        public float lightFlickerPeriod;
        public float lightFlickerOnFraction;
        public int[] lightFixtureFlickerCount;
        public float[] lightFixtureFlickerElapsed;
        public float[] lightFixtureFlickerPeriod;
        public float[] lightFixtureFlickerOnFraction;
        public float[] lightFixtureFlickerPhase;
        public float lightRevealSeconds;
        public bool lightNeverSettles;
        public float lightUnstableElapsed;
        public float lightNoisePhase;
        public GameObject[] profileVariants;
    }

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
    Material runMetalMaterial;
    Material runCableMaterial;
    Material runHazardMaterial;
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
            SetRoomLightIntensity(room, 1f, true);
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
    /// A door opening cues the room beyond it. Every streamed sequence owns a
    /// deterministic light profile: some rooms rise cleanly, some ballast
    /// once or several times, and a few never settle into a constant output.
    /// The pool is fixed, so this remains allocation-free while rooms recycle.
    /// </summary>
    void TickRoomLights(float dt)
    {
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = pool[i];
            if (room == null || room.roomLights == null || room.roomLights.Length == 0) continue;
            if (room.lightRevealStarted && room.lightRevealProgress >= 1f)
            {
                if (room.lightNeverSettles) TickUnstableRoomLight(room, dt);
                continue;
            }
            if (!room.lightTriggerScheduled && !room.lightRevealStarted) continue;

            if (room.lightTriggerScheduled)
            {
                room.lightDelayRemaining -= dt;
                if (room.lightDelayRemaining > 0f) continue;
                room.lightFlickerElapsed += dt;
                var anyFixtureFlickering = false;
                for (var lightIndex = 0; lightIndex < room.roomLights.Length; lightIndex++)
                {
                    if (!room.lightWasEnabled[lightIndex]) continue;
                    var fixtureCount = room.lightFixtureFlickerCount == null ? 0 : room.lightFixtureFlickerCount[lightIndex];
                    if (fixtureCount <= 0)
                    {
                        room.roomLights[lightIndex].enabled = true;
                        room.roomLights[lightIndex].intensity = room.lightBaseIntensity[lightIndex] * .92f;
                        continue;
                    }
                    room.lightFixtureFlickerElapsed[lightIndex] += dt;
                    var totalFlickerSeconds = fixtureCount * room.lightFixtureFlickerPeriod[lightIndex];
                    if (room.lightFixtureFlickerElapsed[lightIndex] < totalFlickerSeconds)
                    {
                        anyFixtureFlickering = true;
                        var pulseTime = (room.lightFixtureFlickerElapsed[lightIndex] + room.lightFixtureFlickerPhase[lightIndex]) % room.lightFixtureFlickerPeriod[lightIndex];
                        var flickerLevel = pulseTime < room.lightFixtureFlickerPeriod[lightIndex] * room.lightFixtureFlickerOnFraction[lightIndex] ? .92f : .035f;
                        room.roomLights[lightIndex].enabled = true;
                        room.roomLights[lightIndex].intensity = room.lightBaseIntensity[lightIndex] * flickerLevel;
                    }
                    else
                    {
                        room.roomLights[lightIndex].enabled = true;
                        room.roomLights[lightIndex].intensity = room.lightBaseIntensity[lightIndex] * .92f;
                    }
                }
                if (anyFixtureFlickering) continue;
                room.lightTriggerScheduled = false;
                room.lightRevealStarted = true;
                room.lightRevealProgress = 0f;
            }
            if (!room.lightRevealStarted || room.lightRevealProgress >= 1f) continue;

            room.lightRevealProgress = Mathf.MoveTowards(room.lightRevealProgress, 1f, dt / room.lightRevealSeconds);
            var eased = room.lightRevealProgress * room.lightRevealProgress * (3f - 2f * room.lightRevealProgress);
            if (room.lightNeverSettles)
            {
                // Keep this room in a readable low-output state after the
                // startup flashes. It must never become a steady lamp.
                eased *= Mathf.Lerp(.72f, .18f, room.lightRevealProgress);
            }
            SetRoomLightIntensity(room, eased, true);
        }
    }

    void ScheduleRoomLight(RoomSlot room)
    {
        if (room == null || room.roomLights == null || room.roomLights.Length == 0) return;
        if (room.lightTriggerScheduled || room.lightRevealStarted) return;
        room.lightTriggerScheduled = true;
        room.lightDelayRemaining = LightRevealDelaySeconds;
        room.lightFlickerElapsed = 0f;
        room.lightUnstableElapsed = 0f;
    }

    void TickUnstableRoomLight(RoomSlot room, float dt)
    {
        room.lightUnstableElapsed += dt;
        var t = room.lightUnstableElapsed + room.lightNoisePhase;
        // Two incommensurate waves create an independent ballast sway for each
        // fixture. The ceiling never reaches the normal steady-state level, but
        // no two lamps share the same dropout frame or phase.
        for (var lightIndex = 0; lightIndex < room.roomLights.Length; lightIndex++)
        {
            var phase = room.lightFixtureFlickerPhase == null ? 0f : room.lightFixtureFlickerPhase[lightIndex];
            var lampT = t + phase;
            var wave = .5f + .5f * Mathf.Sin(lampT * 3.7f) * (.68f + .32f * Mathf.Sin(lampT * 1.13f));
            var dropout = Mathf.PerlinNoise(lampT * .92f, room.lightNoisePhase + lightIndex * 1.73f) > .77f ? .06f : 1f;
            var level = (.12f + .28f * Mathf.Clamp01(wave)) * dropout;
            var light = room.roomLights[lightIndex];
            if (light == null || !room.lightWasEnabled[lightIndex]) continue;
            light.enabled = true;
            light.intensity = room.lightBaseIntensity[lightIndex] * level;
        }
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
            // Paper-drop variation is carried by the printed texture. Raised
            // seam strips created another family of overlapping edge lines in
            // the first-person view, so keep the wall face continuous here.
            // Do not model the acoustic-tile seams as raised boxes. In a
            // first-person corridor those long X/Y lines converge toward the
            // vanishing point and read as exposed wireframe. The planar
            // ceiling and the fixture housings retain the tile impression;
            // micro variation stays in the ceiling material instead.
            // Four simple recessed fluorescent panels create the practical
            // rhythm from the reference. Keep the edge profile closed and
            // shallow: the old housing/end-cap stack exposed overlapping
            // strips that read as a wireframe at the first-person angle.
            var fixtureZ = new[] { 1.7f, 4.55f, 7.4f, 10.25f };
            for (var fixtureIndex = 0; fixtureIndex < fixtureZ.Length; fixtureIndex++)
            {
                var fixtureZPosition = fixtureZ[fixtureIndex];
                Box(room.root.transform, "fluorescent recessed pan " + fixtureIndex, new Vector3(0f, RoomHeight - .042f, fixtureZPosition), new Vector3(1.94f, .07f, .40f), darkMatOr(roomCeiling));
                Box(room.root.transform, "fluorescent diffuser " + fixtureIndex, new Vector3(0f, RoomHeight - .083f, fixtureZPosition), new Vector3(1.70f, .026f, .25f), fixtureMaterial ?? roomCeiling);
                var lightObject = new GameObject("fluorescent light " + fixtureIndex);
                lightObject.transform.SetParent(room.root.transform, false);
                lightObject.transform.localPosition = new Vector3(0f, RoomHeight - .38f, fixtureZ[fixtureIndex]);
                var light = lightObject.AddComponent<Light>();
                // Reach the side walls and the next threshold so the wallpaper
                // and embedded doorway remain readable without a large shadow
                // atlas cost.
                light.type = LightType.Point; light.range = room.rule == RoomRule.Run ? 7.1f : room.rule == RoomRule.Office ? 8.4f : 8.2f;
                light.intensity = room.rule == RoomRule.Run ? .56f : room.rule == RoomRule.Office ? .68f : .64f;
                light.color = ProfileLightColor(room.rule);
                // Keep practicals shadowless. Point-light cube shadow seams
                // can project long diagonal boundaries across the planar
                // ceiling in the built-in renderer; the directional fill and
                // the physical fixture housings supply depth without that
                // wireframe-looking artifact.
                light.shadows = LightShadows.None;
                light.shadowStrength = 0f;
                light.bounceIntensity = .28f;
            }
            room.entry = CreateEntry(room.root.transform);
        }

        CacheRoomLights(room);

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

    void BuildDoor(RoomSlot room)
    {
        var frameMaterial = trimMaterial ?? wallMaterial;
        // The threshold is cut into the end wall. Filling the two side spans
        // keeps the door connected to the room instead of reading as a free
        // standing prop in the distance.
        var sideWallWidth = (RoomWidth - DoorWidth) * .5f;
        var sideWallOffset = DoorWidth * .5f + sideWallWidth * .5f;
        var roomWall = ProfileMaterial(profileWallMaterials, room.rule, wallMaterial);
        // Keep the threshold nearly flush with the paper plane. A full wall
        // thickness at the opening exposes dark side faces when the player is
        // close, which reads as a portal frame instead of the ordinary door in
        // the source room.
        const float doorWallDepth = .08f;
        Box(room.root.transform, "door wall return left", new Vector3(-sideWallOffset, RoomHeight * .5f, RoomLength), new Vector3(sideWallWidth, RoomHeight, doorWallDepth), roomWall);
        Box(room.root.transform, "door wall return right", new Vector3(sideWallOffset, RoomHeight * .5f, RoomLength), new Vector3(sideWallWidth, RoomHeight, doorWallDepth), roomWall);
        Box(room.root.transform, "door wall above", new Vector3(0f, RoomHeight - DoorHeaderHeight * .5f, RoomLength), new Vector3(DoorWidth, DoorHeaderHeight, doorWallDepth), roomWall);
        // The source-room door is an ordinary, flush double door. Avoid the
        // layered jamb/reveal/header pieces from the prototype; their exposed
        // edges made the threshold look like a sci-fi portal.
        var leftPivot = new GameObject("double door left hinge").transform;
        leftPivot.SetParent(room.root.transform, false); leftPivot.localPosition = new Vector3(-1.2f, 0f, RoomLength - .08f);
        var rightPivot = new GameObject("double door right hinge").transform;
        rightPivot.SetParent(room.root.transform, false); rightPivot.localPosition = new Vector3(1.2f, 0f, RoomLength - .08f);
        var left = Box(leftPivot, "double door left", new Vector3(.6f, DoorLeafHeight * .5f, 0f), new Vector3(1.2f, DoorLeafHeight, .14f), doorMaterial ?? wallMaterial);
        var right = Box(rightPivot, "double door right", new Vector3(-.6f, DoorLeafHeight * .5f, 0f), new Vector3(1.2f, DoorLeafHeight, .14f), doorMaterial ?? wallMaterial);
        Box(leftPivot, "left door handle", new Vector3(1.02f, 1.22f, -.10f), new Vector3(.055f, .18f, .08f), frameMaterial);
        Box(rightPivot, "right door handle", new Vector3(-1.02f, 1.22f, -.10f), new Vector3(.055f, .18f, .08f), frameMaterial);
        // The leaf itself supplies the dark reveal. The former full-height
        // gasket strips read as exposed wireframe when the door is closed, so
        // keep the visual seam implicit in the leaf and retain only the
        // handles and jamb geometry.
        room.leftDoor = leftPivot; room.rightDoor = rightPivot;
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

    static Material ProfileMaterial(Material[] materials, RoomRule rule, Material fallback)
    {
        var index = (int)rule;
        return materials != null && index >= 0 && index < materials.Length && materials[index] != null ? materials[index] : fallback;
    }

    static Color ProfileLightColor(RoomRule rule)
    {
        switch (rule)
        {
            case RoomRule.Shift: return new Color(.73f, .74f, .65f);
            case RoomRule.Office: return new Color(.94f, .87f, .76f);
            // The utility run is cooler and flatter; reserve red for the
            // localized warning props instead of tinting the whole room.
            case RoomRule.Run: return new Color(.76f, .80f, .78f);
            case RoomRule.Exit: return new Color(.45f, .88f, .82f);
            default: return new Color(1f, .93f, .74f);
        }
    }

    Material PropMaterial(string name, Color color, bool emission = false)
    {
        var shader = Shader.Find("Standard");
        if (shader == null) shader = Shader.Find("UI/Default");
        var material = new Material(shader);
        material.name = name;
        material.color = color;
        material.SetFloat("_Glossiness", .16f);
        if (emission)
        {
            material.EnableKeyword("_EMISSION");
            material.SetColor("_EmissionColor", color * .72f);
        }
        return material;
    }

    void EnsurePropMaterials()
    {
        if (officeDeskMaterial != null) return;
        officeDeskMaterial = PropMaterial("Office / stained laminate", new Color(.30f, .29f, .27f));
        officeMetalMaterial = PropMaterial("Office / oxidized steel", new Color(.40f, .39f, .36f));
        officePaperMaterial = PropMaterial("Office / paper", new Color(.78f, .75f, .66f));
        officeGlassMaterial = PropMaterial("Office / cooler bottle", new Color(.48f, .68f, .70f), true);
        officeDarkMaterial = PropMaterial("Office / blacked-out glass", new Color(.018f, .021f, .022f));
        runMetalMaterial = PropMaterial("Run / galvanized cabinet", new Color(.36f, .35f, .33f));
        runCableMaterial = PropMaterial("Run / rubber cable", new Color(.08f, .075f, .07f));
        runHazardMaterial = PropMaterial("Run / emergency warning", new Color(.71f, .20f, .13f), true);
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
            if (rule == RoomRule.Office)
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
                    Box(props.transform, "office low partition", new Vector3(x, 1.2f, z + .82f), new Vector3(1.45f, 1.0f, .09f), roomWall);
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
                // Run: chalky utility walls, equipment silhouettes and a red
                // warning layer concentrated near the next threshold.
                Box(props.transform, "run utility cabinet left", new Vector3(-3.6f, 1.0f, 4.1f), new Vector3(.7f, 1.0f, 1.0f), runMetalMaterial);
                Box(props.transform, "run utility cabinet right", new Vector3(3.1f, 1.0f, 7.7f), new Vector3(.7f, 1.0f, 1.0f), runMetalMaterial);
                Box(props.transform, "run cable tray", new Vector3(0f, 2.48f, 7.0f), new Vector3(4.2f, .12f, .18f), runCableMaterial);
                // Utility Level 2 language: exposed conduits, junction boxes,
                // and a low ceiling run that makes the room feel serviced
                // rather than decorated. Cylinders are kept to four per room
                // so the streamed pool remains inexpensive in WebGL.
                Cylinder(props.transform, "run conduit left", new Vector3(-4.35f, 2.22f, 6.0f), new Vector3(.07f, 2.6f, .07f), runMetalMaterial, new Vector3(90f, 0f, 0f));
                Cylinder(props.transform, "run conduit right", new Vector3(4.12f, 2.03f, 8.1f), new Vector3(.06f, 2.1f, .06f), runMetalMaterial, new Vector3(90f, 0f, 0f));
                Box(props.transform, "run junction box left", new Vector3(-4.26f, 1.88f, 6.05f), new Vector3(.42f, .34f, .18f), runMetalMaterial);
                Box(props.transform, "run junction box right", new Vector3(4.06f, 1.70f, 8.12f), new Vector3(.42f, .34f, .18f), runMetalMaterial);
                Box(props.transform, "run hazard marker left", new Vector3(-4.85f, 1.2f, 9.5f), new Vector3(.08f, 1.25f, 1.1f), runHazardMaterial);
                Box(props.transform, "run hazard marker right", new Vector3(4.85f, 1.2f, 9.5f), new Vector3(.08f, 1.25f, 1.1f), runHazardMaterial);
                Box(props.transform, "run service cart", new Vector3(3.15f, .52f, 3.8f), new Vector3(.72f, .12f, .48f), runMetalMaterial);
                Box(props.transform, "run cart handle", new Vector3(3.15f, .95f, 4.12f), new Vector3(.62f, .08f, .08f), runCableMaterial);
                Box(props.transform, "run red door cue", new Vector3(0f, 2.25f, 10.7f), new Vector3(2.1f, .12f, .08f), runHazardMaterial);
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
                    room.lightBaseIntensity[i] = room.rule == RoomRule.Run ? .56f : room.rule == RoomRule.Office ? .68f : .64f;
                    light.range = room.rule == RoomRule.Run ? 7.1f : room.rule == RoomRule.Office ? 8.4f : 8.2f;
                }
            }
        }
        if (room.profileVariants != null)
            for (var i = 0; i < room.profileVariants.Length; i++)
                if (room.profileVariants[i] != null) room.profileVariants[i].SetActive(i == (int)room.rule);
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
        ResetRoomLights(room);
    }

    void ResetRoomLights(RoomSlot room)
    {
        ConfigureLightProfile(room);
        room.lightRevealProgress = 0f;
        room.lightRevealStarted = false;
        room.lightTriggerScheduled = false;
        room.lightDelayRemaining = 0f;
        room.lightFlickerElapsed = 0f;
        room.lightUnstableElapsed = 0f;
        if (room.roomLights == null) return;
        for (var i = 0; i < room.roomLights.Length; i++)
        {
            var light = room.roomLights[i];
            if (light == null) continue;
            light.intensity = 0f;
            light.enabled = false;
        }
    }

    void ConfigureLightProfile(RoomSlot room)
    {
        if (room == null) return;
        var sequence = Mathf.Max(0, room.sequence);
        var profile = Hash01(sequence, 11);
        // The weighted bands intentionally leave a useful minority of rooms
        // completely clean while reserving a smaller tail for lights that
        // continue misbehaving after their initial cue.
        if (profile < .27f)
        {
            room.lightFlickerCount = 0;
            room.lightNeverSettles = false;
        }
        else if (profile < .58f)
        {
            room.lightFlickerCount = 1;
            room.lightNeverSettles = false;
        }
        else if (profile < .87f)
        {
            room.lightFlickerCount = 2 + Mathf.FloorToInt(Hash01(sequence, 23) * 3f);
            room.lightNeverSettles = false;
        }
        else
        {
            room.lightFlickerCount = 2 + Mathf.FloorToInt(Hash01(sequence, 29) * 4f);
            room.lightNeverSettles = true;
        }

        room.lightFlickerPeriod = Mathf.Lerp(.17f, .31f, Hash01(sequence, 37));
        room.lightFlickerOnFraction = Mathf.Lerp(.23f, .48f, Hash01(sequence, 41));
        room.lightRevealSeconds = Mathf.Lerp(1.35f, 2.35f, Hash01(sequence, 47));
        room.lightNoisePhase = Hash01(sequence, 53) * 19f;
        var lampCount = room.roomLights == null ? 4 : room.roomLights.Length;
        room.lightFixtureFlickerCount = new int[lampCount];
        room.lightFixtureFlickerElapsed = new float[lampCount];
        room.lightFixtureFlickerPeriod = new float[lampCount];
        room.lightFixtureFlickerOnFraction = new float[lampCount];
        room.lightFixtureFlickerPhase = new float[lampCount];
        for (var i = 0; i < lampCount; i++)
        {
            var lampSeed = Hash01(sequence + i * 17, 61);
            room.lightFixtureFlickerCount[i] = room.lightFlickerCount <= 0 ? 0 : Mathf.Max(1, room.lightFlickerCount + Mathf.RoundToInt(Mathf.Lerp(-1f, 1f, lampSeed)));
            room.lightFixtureFlickerPeriod[i] = room.lightFlickerPeriod * Mathf.Lerp(.78f, 1.22f, Hash01(sequence + i * 23, 67));
            room.lightFixtureFlickerOnFraction[i] = Mathf.Clamp01(room.lightFlickerOnFraction + Mathf.Lerp(-.08f, .08f, Hash01(sequence + i * 29, 71)));
            room.lightFixtureFlickerPhase[i] = Hash01(sequence + i * 31, 73) * room.lightFixtureFlickerPeriod[i];
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
        if (room == null || room.roomLights == null) return;
        room.lightTriggerScheduled = false;
        room.lightRevealStarted = true;
        room.lightRevealProgress = 1f;
        SetRoomLightIntensity(room, 1f, true);
    }

    void SetRoomLightIntensity(RoomSlot room, float normalizedIntensity, bool enabled)
    {
        if (room == null || room.roomLights == null) return;
        normalizedIntensity = Mathf.Clamp01(normalizedIntensity);
        for (var i = 0; i < room.roomLights.Length; i++)
        {
            var light = room.roomLights[i];
            if (light == null || !room.lightWasEnabled[i]) continue;
            light.enabled = enabled;
            light.intensity = room.lightBaseIntensity[i] * normalizedIntensity;
        }
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
        var angle = 94f * t;
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
        var structural = name.IndexOf("wall", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("ceiling", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("carpet floor", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("rear boundary", StringComparison.OrdinalIgnoreCase) >= 0
            || name.IndexOf("fluorescent", StringComparison.OrdinalIgnoreCase) >= 0;
        meshFilter.sharedMesh = structural
            ? FrontRoomsFilmMesh.GetPlanarBox(scale)
            : FrontRoomsFilmMesh.GetBeveledBox(scale, Mathf.Min(.035f, Mathf.Min(scale.x, Mathf.Min(scale.y, scale.z)) * .16f));
        meshRenderer.sharedMaterial = material;
        var collider = box.AddComponent<BoxCollider>();
        collider.size = scale;
        return box;
    }

    Material darkMatOr(Material fallback)
    {
        // The dark door/furniture material is the fixture housing when one is
        // supplied by the game; fallback keeps editor previews self-contained.
        return doorMaterial != null ? doorMaterial : (trimMaterial != null ? trimMaterial : fallback);
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
