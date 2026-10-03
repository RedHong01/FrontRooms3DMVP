using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// The Relay's states. Wander was added last so the others keep their values:
/// it roams without knowing where the player is; only seeing the player starts a Chase.
/// </summary>
public enum HunterState { Dormant, Listen, Hunt, Search, Chase, BreakDoor, Wander }

/// <summary>Designer-facing numbers for the Relay. Edit them on the FrontRooms 3D object.</summary>
[Serializable]
public sealed class FrontRoomsHunterTuning
{
    [Tooltip("Seconds the player must spend in the first furnished room before the Relay is released behind them.")]
    public float releaseDelaySeconds = 3f;
    [Tooltip("How many rooms the Relay may fall behind before it relays forward, out of sight, to that distance.")]
    public int trailRooms = 2;
    public float listenSeconds = 2f;
    public float searchSeconds = 2.5f;
    public float breakDoorSeconds = 2.5f;
    [Tooltip("Walk speed while hunting a noise or the next room. Player walk is 3.2 m/s.")]
    public float huntSpeed = 2.6f;
    [Tooltip("Speed while it can see the player. Faster than a walk, slower than a sprint (5.5 m/s).")]
    public float chaseSpeed = 4.2f;
    public float sightRange = 12f;
    public float lostSightSeconds = 1.5f;
    public float catchDistance = .7f;
    public float sprintNoiseRadius = 26f;
    public float doorNoiseRadius = 14f;
    [Range(.5f, 3f), Tooltip("How far it hears, as a multiple of every noise radius (sprint, door, glass). 1.4: sprint 36 m, door 20 m, glass 56 m. The level profile's tiers raise it.")]
    public float hearing = 1.4f;
    [Tooltip("Searching a room (the map Relay): seconds it stands and listens at each spot.")]
    public float searchLookSeconds = 1.1f;
    [Tooltip("Searching a room (the map Relay): it gives up after this long.")]
    public float searchMaxSeconds = 15f;

    /// <summary>Copy every number from another tuning, in place (the running Relay keeps its one tuning object).</summary>
    public void CopyFrom(FrontRoomsHunterTuning o)
    {
        releaseDelaySeconds = o.releaseDelaySeconds;
        trailRooms = o.trailRooms;
        listenSeconds = o.listenSeconds;
        searchSeconds = o.searchSeconds;
        breakDoorSeconds = o.breakDoorSeconds;
        huntSpeed = o.huntSpeed;
        chaseSpeed = o.chaseSpeed;
        sightRange = o.sightRange;
        lostSightSeconds = o.lostSightSeconds;
        catchDistance = o.catchDistance;
        sprintNoiseRadius = o.sprintNoiseRadius;
        doorNoiseRadius = o.doorNoiseRadius;
        hearing = o.hearing;
        searchLookSeconds = o.searchLookSeconds;
        searchMaxSeconds = o.searchMaxSeconds;
    }
}

/// <summary>
/// The Relay's Listen → Hunt → Search → Chase → BreakDoor state machine, kept
/// from the authored-grid hunter and re-expressed for the linear room stream:
/// rooms are 12 m slices along +Z, every room ends in a door, and doors behind
/// the player are shut unless the Relay has broken them. Positions are world
/// X/Z, so the caller only has to keep the rig in sync.
/// </summary>
public sealed class FrontRoomsHunterBrain
{
    const float DoorApproach = .35f;
    const float BlowInterval = .5f;

    readonly FrontRoomsRoomStream stream;
    readonly FrontRoomsHunterTuning tuning;
    // Doors the Relay broke after their room was recycled away.
    readonly HashSet<int> brokenUnloadedDoors = new HashSet<int>();
    Vector2 position, target, lastSeen;
    float lostTime, blowTime, releaseTimer, appliedRebaseShift;
    int breakingDoor = -1;
    int alarmedRoom = int.MinValue;
    bool caught;

    public HunterState State { get; private set; } = HunterState.Dormant;
    public float StateTime { get; private set; }
    public Vector2 Position => position;
    public bool Moving { get; private set; }
    public bool Released => State != HunterState.Dormant;
    public bool SeesPlayer { get; private set; }
    public int DoorsBroken { get; private set; }
    public int Relays { get; private set; }

    public event Action<HunterState> StateChanged;
    public event Action<Vector2> DoorBlow;
    public event Action<int> DoorBroken;
    /// <summary>Raised when the Run room's alarm brings the Relay up behind the player.</summary>
    public event Action<int> Alarmed;
    public event Action Caught;

    public FrontRoomsHunterBrain(FrontRoomsRoomStream stream, FrontRoomsHunterTuning tuning)
    {
        this.stream = stream;
        this.tuning = tuning ?? new FrontRoomsHunterTuning();
        appliedRebaseShift = stream.TotalRebaseShift;
        // Every door the player opens is a sound the Relay may hear.
        stream.DoorOpeningStarted += (door, point) => Noise(new Vector2(point.x, point.z), this.tuning.doorNoiseRadius);
    }

    /// <summary>
    /// Advance the Relay one frame. Call after the stream has ticked and the
    /// player has moved, with the player's world X/Z.
    /// </summary>
    public void Tick(float dt, Vector2 player)
    {
        if (caught || stream == null) return;
        // Stay attached to the rooms when the stream rebases its origin.
        var shift = stream.TotalRebaseShift - appliedRebaseShift;
        if (shift != 0f)
        {
            position.y -= shift;
            target.y -= shift;
            lastSeen.y -= shift;
            appliedRebaseShift = stream.TotalRebaseShift;
        }
        var playerRoom = stream.SequenceAtZ(player.y);
        if (alarmedRoom != playerRoom && stream.IsPlayable && stream.RuleAt(playerRoom) == RoomRule.Run && TryAlarm(player, playerRoom))
        {
            alarmedRoom = playerRoom;
            Alarmed?.Invoke(playerRoom);
        }
        if (State == HunterState.Dormant)
        {
            TickRelease(dt, playerRoom);
            return;
        }

        StateTime += dt;
        if (State != HunterState.Chase && RoomOf(position) < playerRoom - tuning.trailRooms)
            RelayTo(playerRoom - tuning.trailRooms, HunterState.Listen);

        SeesPlayer = Sees(player);
        if (SeesPlayer)
        {
            lastSeen = player;
            lostTime = 0f;
            if (State != HunterState.Chase && State != HunterState.BreakDoor)
            {
                target = player;
                SetState(HunterState.Chase);
            }
        }

        var before = position;
        switch (State)
        {
            case HunterState.Listen:
                if (StateTime > tuning.listenSeconds)
                {
                    target = RoomCenter(RoomOf(position) + 1);
                    SetState(HunterState.Hunt);
                }
                break;
            case HunterState.Hunt:
                if (Follow(tuning.huntSpeed, dt)) SetState(HunterState.Search);
                break;
            case HunterState.Search:
                if (StateTime > tuning.searchSeconds) SetState(HunterState.Listen);
                break;
            case HunterState.Chase:
                target = SeesPlayer ? player : lastSeen;
                Follow(tuning.chaseSpeed, dt);
                if (!SeesPlayer)
                {
                    lostTime += dt;
                    if (lostTime > tuning.lostSightSeconds)
                    {
                        target = lastSeen;
                        SetState(HunterState.Hunt);
                    }
                }
                break;
            case HunterState.BreakDoor:
                TickBreak(dt);
                break;
        }
        Moving = (position - before).sqrMagnitude > 1e-6f;

        if (SeesPlayer && Vector2.Distance(position, player) < tuning.catchDistance)
        {
            caught = true;
            Caught?.Invoke();
        }
    }

    /// <summary>A sound the player made. The Relay walks to the last one it heard.</summary>
    public void Noise(Vector2 source, float radius)
    {
        if (!Released || State == HunterState.Chase) return;
        if (Vector2.Distance(position, source) > radius) return;
        target = source;
        if (State != HunterState.BreakDoor) SetState(HunterState.Hunt);
    }

    /// <summary>
    /// The Run room's alarm. Once the door behind the player has shut, the
    /// Relay arrives on the far side of it and starts breaking it at once, so
    /// the player hears it right behind them and has to keep moving. Returns
    /// false while that door is still open, so the jump is never seen.
    /// </summary>
    bool TryAlarm(Vector2 player, int playerRoom)
    {
        var behind = playerRoom - 1;
        if (DoorPassable(behind)) return false;
        target = player;
        if (State == HunterState.Chase || RoomOf(position) > behind) return true;
        position = DoorPoint(behind, -DoorApproach);
        breakingDoor = behind;
        blowTime = BlowInterval;
        Relays++;
        SetState(HunterState.BreakDoor);
        return true;
    }

    void TickRelease(float dt, int playerRoom)
    {
        if (!stream.IsPlayable || playerRoom < stream.FirstProfileSequence) return;
        releaseTimer += dt;
        if (releaseTimer < tuning.releaseDelaySeconds) return;
        RelayTo(playerRoom - tuning.trailRooms, HunterState.Listen);
    }

    void RelayTo(int room, HunterState state)
    {
        // Arrive at the rear of that room, behind its seal or a shut door.
        position = new Vector2(stream.CenterX, stream.RoomStartZ(room) + .6f);
        target = position;
        breakingDoor = -1;
        Relays++;
        SetState(state);
    }

    void TickBreak(float dt)
    {
        blowTime += dt;
        if (blowTime >= BlowInterval)
        {
            blowTime = 0f;
            DoorBlow?.Invoke(DoorPoint(breakingDoor, 0f));
        }
        if (StateTime < tuning.breakDoorSeconds) return;
        if (!stream.BreakDoor(breakingDoor)) brokenUnloadedDoors.Add(breakingDoor);
        DoorsBroken++;
        DoorBroken?.Invoke(breakingDoor);
        breakingDoor = -1;
        SetState(HunterState.Hunt);
    }

    /// <summary>Walk toward the target, through doors. True once it is reached.</summary>
    bool Follow(float speed, float dt)
    {
        var room = RoomOf(position);
        var targetRoom = RoomOf(target);
        Vector2 waypoint;
        if (targetRoom > room)
        {
            var approach = DoorPoint(room, -DoorApproach);
            if (!DoorPassable(room))
            {
                if (Vector2.Distance(position, approach) < .05f)
                {
                    breakingDoor = room;
                    blowTime = BlowInterval;
                    SetState(HunterState.BreakDoor);
                    return false;
                }
                waypoint = approach;
            }
            else waypoint = DoorPoint(room, DoorApproach);
        }
        else waypoint = target;
        position = Vector2.MoveTowards(position, waypoint, speed * dt);
        return targetRoom <= room && Vector2.Distance(position, target) < .05f;
    }

    bool Sees(Vector2 player)
    {
        if (Vector2.Distance(position, player) > tuning.sightRange) return false;
        var from = Mathf.Min(RoomOf(position), RoomOf(player));
        var to = Mathf.Max(RoomOf(position), RoomOf(player));
        for (var room = from; room < to; room++)
            if (!DoorPassable(room)) return false;
        return true;
    }

    bool DoorPassable(int room) => stream.IsDoorPassable(room) || brokenUnloadedDoors.Contains(room);
    int RoomOf(Vector2 point) => stream.SequenceAtZ(point.y);
    Vector2 RoomCenter(int room) => new Vector2(stream.CenterX, stream.RoomStartZ(room) + FrontRoomsRoomStream.RoomLength * .5f);
    Vector2 DoorPoint(int room, float offset) => new Vector2(stream.CenterX, stream.RoomStartZ(room + 1) + offset);

    void SetState(HunterState next)
    {
        if (next == State) { StateTime = 0f; return; }
        State = next;
        StateTime = 0f;
        StateChanged?.Invoke(next);
    }
}
