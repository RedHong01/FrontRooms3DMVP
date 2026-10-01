using System;
using UnityEngine;

/// <summary>
/// A bounded, first-person room stream for the FrontRooms title and arrival.
/// The component owns three reusable room roots. It does not replace the
/// authored gameplay map: a caller can keep the camera and use the stream as a
/// title/arrival layer, then read HasControl and take over at PendingAnchorPosition.
/// </summary>
public sealed class FrontRoomsRoomStream : MonoBehaviour
{
    public const int MaxRooms = 3;
    public const float RoomWidth = 11.5f;
    public const float RoomHeight = 2.9f;
    public const float RoomLength = 12f;
    const float DoorWidth = 2.4f;
    const float WallThickness = .26f;
    const float BoundaryMargin = .34f;
    const float TitleSpeed = 1.15f;
    const float TransitionSpeed = 2.25f;
    const float DoorOpenSeconds = .9f;
    const float RecycleDistance = 8f;
    const float RebaseThreshold = 256f;
    const float LogoDelay = .7f;
    const float LogoFadeSeconds = 2.2f;
    const float LogoExitSeconds = .55f;

    [Tooltip("Optional room authoring template. A copy is placed inside each streamed room root.")]
    public GameObject roomTemplate;

    sealed class RoomSlot
    {
        public GameObject root;
        public Transform entry;
        public Transform leftDoor;
        public Transform rightDoor;
        public GameObject rearSeal;
        public int sequence;
        public float startZ;
        public float endZ;
        public float doorProgress;
        public bool doorOpening;
        public bool doorOpen;
        public bool connected;
    }

    Camera streamCamera;
    Material wallMaterial;
    Material floorMaterial;
    Material ceilingMaterial;
    Material trimMaterial;
    Material fixtureMaterial;
    Material doorMaterial;
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
    int recycledCount;
    int rebaseCount;
    float maxExposure;
    bool initialized;
    bool startRequested;
    bool hasControl;
    bool isEntering;

    public bool HasControl => hasControl;
    public bool IsEntering => isEntering;
    public float LogoVisibility => logoVisibility;
    public int RoomCount => initialized ? MaxRooms : 0;
    public int RecycledCount => recycledCount;
    public int RebaseCount => rebaseCount;
    public int CurrentRoomNumber => currentSequence;
    public float CameraZ => streamCamera == null ? 0f : streamCamera.transform.position.z;
    public Vector3 PendingAnchorPosition { get; private set; }
    public float MaxExposure => maxExposure;
    public float MaxExposureDistance => RoomLength * MaxRooms;
    public int MaxExposedRooms => MaxRooms;

    /// <summary>Build the fixed room pool around the camera's current position.</summary>
    public void Initialize(Camera camera, Material wall, Material floor, Material ceiling,
        Material trim, Material fixture, Material door)
    {
        streamCamera = camera;
        wallMaterial = wall;
        floorMaterial = floor;
        ceilingMaterial = ceiling;
        trimMaterial = trim;
        fixtureMaterial = fixture;
        doorMaterial = door;
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

        var cameraZ = streamCamera == null ? 0f : streamCamera.transform.position.z;
        centerX = streamCamera == null ? 0f : streamCamera.transform.position.x;
        var firstStart = cameraZ - RoomLength * .5f;
        for (var i = 0; i < MaxRooms; i++)
        {
            var room = new RoomSlot();
            room.sequence = i;
            room.startZ = firstStart + i * RoomLength;
            room.endZ = room.startZ + RoomLength;
            room.root = new GameObject("Stream room / " + i.ToString("000"));
            room.root.transform.SetParent(transform, false);
            room.root.transform.position = new Vector3(centerX, 0f, room.startZ);
            BuildRoom(room, i);
            pool[i] = room;
        }
        currentPoolIndex = 0;
        currentSequence = 0;
        maxExposure = MaxRooms;
        initialized = true;
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
        pendingTargetZ = next.startZ + 2f;
        PendingAnchorPosition = new Vector3(streamCamera.transform.position.x, streamCamera.transform.position.y, pendingTargetZ);
        next.connected = false;
        next.doorOpening = true;
        current.doorOpening = true;
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
        if (candidate.z > room.endZ - BoundaryMargin && !room.doorOpen)
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
            source.doorOpening = true;
            source.doorProgress = Mathf.MoveTowards(source.doorProgress, 1f, dt / DoorOpenSeconds);
            ApplyDoorPose(source);
            if (source.doorProgress >= 1f)
            {
                source.doorOpen = true;
                target.connected = true;
                if (target.rearSeal != null) target.rearSeal.SetActive(false);
            }
            return;
        }

        var currentPosition = streamCamera.transform.position;
        var remaining = pendingTargetZ - currentPosition.z;
        if (remaining > .001f)
        {
            // Ease only inside the final metre and clamp the step. This keeps
            // the handoff C1-smooth without ever overshooting the anchor.
            var normalized = Mathf.Clamp01(remaining / 1f);
            var speed = Mathf.Lerp(.62f, TransitionSpeed, normalized);
            currentPosition.z += Mathf.Min(remaining, speed * dt);
            streamCamera.transform.position = currentPosition;
            transitionElapsed += dt;
            return;
        }

        currentPosition.z = pendingTargetZ;
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
                room.doorOpening = true;
            if (room.doorOpening && room.doorProgress < 1f)
            {
                room.doorProgress = Mathf.MoveTowards(room.doorProgress, 1f, dt / DoorOpenSeconds);
                ApplyDoorPose(room);
                if (room.doorProgress >= 1f)
                {
                    room.doorOpen = true;
                    var next = FindSequence(room.sequence + 1);
                    if (next != null)
                    {
                        next.connected = true;
                        if (next.rearSeal != null) next.rearSeal.SetActive(false);
                    }
                }
            }
            if (room.doorOpen && distance < -4f && room.sequence < currentSequence)
            {
                room.doorOpen = false;
                room.doorOpening = false;
                room.doorProgress = 0f;
                ApplyDoorPose(room);
            }
        }
    }

    void MaintainPool()
    {
        var room = FindCurrentRoom();
        if (room != null && streamCamera.transform.position.z >= room.endZ)
        {
            var next = FindSequence(room.sequence + 1);
            if (next != null && next.connected) currentSequence = next.sequence;
        }
        var oldest = FindOldestRoom();
        if (oldest == null || oldest.sequence >= currentSequence - 1) return;
        if (streamCamera.transform.position.z - oldest.endZ < RecycleDistance) return;
        if (oldest.doorOpening || oldest.doorOpen) return;
        var newest = FindNewestRoom();
        if (newest == null) return;
        var nextSequence = newest.sequence + 1;
        oldest.sequence = nextSequence;
        oldest.startZ = newest.endZ;
        oldest.endZ = oldest.startZ + RoomLength;
        oldest.root.transform.position = new Vector3(centerX, 0f, oldest.startZ);
        oldest.doorProgress = 0f;
        oldest.doorOpening = false;
        oldest.doorOpen = false;
        oldest.connected = false;
        if (oldest.rearSeal != null) oldest.rearSeal.SetActive(true);
        ApplyDoorPose(oldest);
        recycledCount++;
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
        rebaseCount++;
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
            Box(room.root.transform, "carpet floor", new Vector3(0f, -.12f, RoomLength * .5f), new Vector3(RoomWidth, .24f, RoomLength + .04f), floorMaterial);
            Box(room.root.transform, "ceiling", new Vector3(0f, RoomHeight + .1f, RoomLength * .5f), new Vector3(RoomWidth, .2f, RoomLength + .04f), ceilingMaterial);
            Box(room.root.transform, "left wallpaper wall", new Vector3(-RoomWidth * .5f, RoomHeight * .5f, RoomLength * .5f), new Vector3(WallThickness, RoomHeight, RoomLength), wallMaterial);
            Box(room.root.transform, "right wallpaper wall", new Vector3(RoomWidth * .5f, RoomHeight * .5f, RoomLength * .5f), new Vector3(WallThickness, RoomHeight, RoomLength), wallMaterial);
            Box(room.root.transform, "left baseboard", new Vector3(-RoomWidth * .5f + .15f, .18f, RoomLength * .5f), new Vector3(.08f, .16f, RoomLength), trimMaterial ?? wallMaterial);
            Box(room.root.transform, "right baseboard", new Vector3(RoomWidth * .5f - .15f, .18f, RoomLength * .5f), new Vector3(.08f, .16f, RoomLength), trimMaterial ?? wallMaterial);
            Box(room.root.transform, "fluorescent fixture", new Vector3(0f, RoomHeight - .08f, RoomLength * .5f), new Vector3(2.05f, .1f, .38f), fixtureMaterial ?? ceilingMaterial);
            var lightObject = new GameObject("fluorescent light");
            lightObject.transform.SetParent(room.root.transform, false);
            lightObject.transform.localPosition = new Vector3(0f, RoomHeight - .38f, RoomLength * .5f);
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Point; light.range = 7.5f; light.intensity = .9f; light.color = new Color(.9f, .84f, .66f);
            room.entry = CreateEntry(room.root.transform);
        }

        room.rearSeal = Box(room.root.transform, "opaque rear boundary seal", new Vector3(0f, RoomHeight * .5f, 0f), new Vector3(RoomWidth, RoomHeight, .18f), wallMaterial);
        room.rearSeal.SetActive(index == 0);
        BuildDoor(room);
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
        Box(room.root.transform, "door wall return left", new Vector3(-sideWallOffset, RoomHeight * .5f, RoomLength), new Vector3(sideWallWidth, RoomHeight, WallThickness), wallMaterial);
        Box(room.root.transform, "door wall return right", new Vector3(sideWallOffset, RoomHeight * .5f, RoomLength), new Vector3(sideWallWidth, RoomHeight, WallThickness), wallMaterial);
        Box(room.root.transform, "door wall above", new Vector3(0f, RoomHeight - .12f, RoomLength), new Vector3(DoorWidth, .24f, WallThickness), wallMaterial);
        Box(room.root.transform, "door frame left", new Vector3(-1.45f, RoomHeight * .5f, RoomLength), new Vector3(.22f, RoomHeight, .22f), frameMaterial);
        Box(room.root.transform, "door frame right", new Vector3(1.45f, RoomHeight * .5f, RoomLength), new Vector3(.22f, RoomHeight, .22f), frameMaterial);
        Box(room.root.transform, "door frame header", new Vector3(0f, RoomHeight - .12f, RoomLength), new Vector3(3.12f, .24f, .22f), frameMaterial);
        var leftPivot = new GameObject("double door left hinge").transform;
        leftPivot.SetParent(room.root.transform, false); leftPivot.localPosition = new Vector3(-1.2f, 0f, RoomLength);
        var rightPivot = new GameObject("double door right hinge").transform;
        rightPivot.SetParent(room.root.transform, false); rightPivot.localPosition = new Vector3(1.2f, 0f, RoomLength);
        var left = Box(leftPivot, "double door left", new Vector3(.6f, 1.2f, 0f), new Vector3(1.2f, 2.4f, .14f), doorMaterial ?? wallMaterial);
        var right = Box(rightPivot, "double door right", new Vector3(-.6f, 1.2f, 0f), new Vector3(1.2f, 2.4f, .14f), doorMaterial ?? wallMaterial);
        room.leftDoor = leftPivot; room.rightDoor = rightPivot;
        room.doorProgress = 0f; room.doorOpening = false; room.doorOpen = false;
        ApplyDoorPose(room);
    }

    void ApplyDoorPose(RoomSlot room)
    {
        if (room.leftDoor == null || room.rightDoor == null) return;
        var angle = 94f * room.doorProgress;
        room.leftDoor.localRotation = Quaternion.Euler(0f, -angle, 0f);
        room.rightDoor.localRotation = Quaternion.Euler(0f, angle, 0f);
    }

    GameObject Box(Transform parent, string name, Vector3 localPosition, Vector3 scale, Material material)
    {
        var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = name;
        box.transform.SetParent(parent, false);
        box.transform.localPosition = localPosition;
        box.transform.localScale = scale;
        var renderer = box.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = material;
        return box;
    }
}
