using System;
using System.Collections.Generic;
using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// The Relay on the generated map. It keeps the Listen → Hunt → Search →
/// Chase → BreakDoor states of the stream hunter, re-expressed for an open
/// grid:
/// - it is released after a short grace period, in a built cell 9–15 cells of
///   walking away that the player cannot see, preferably behind them;
/// - it paths through built cells with a breadth-first search, breaks shut
///   doors, and cannot pass unbroken glass;
/// - it sees with a ray at eye height and walks to the last noise it heard;
/// - if the chase leaves it too far behind, it relays itself closer, unseen.
/// Positions are world space; the caller drives the rig.
/// </summary>
public sealed class FrontRoomsMapHunter
{
    const float EyeHeight = 1.6f;
    const float BlowInterval = .5f;
    const float ReplanSeconds = .35f;
    const float LeashCheckSeconds = 1f;
    const int SpawnMinCells = 9, SpawnMaxCells = 15, LeashCells = 30, SearchRadiusCells = 3;

    static readonly GridCoord[] Steps = { new GridCoord(1, 0), new GridCoord(-1, 0), new GridCoord(0, 1), new GridCoord(0, -1) };

    readonly FrontRoomsMapWorld world;
    readonly FrontRoomsHunterTuning tuning;
    readonly Collider playerCollider;
    readonly Transform rig;
    readonly List<GridCoord> path = new List<GridCoord>();
    readonly Dictionary<GridCoord, GridCoord> cameFrom = new Dictionary<GridCoord, GridCoord>();
    readonly Dictionary<GridCoord, int> depth = new Dictionary<GridCoord, int>();
    readonly Queue<GridCoord> frontier = new Queue<GridCoord>();
    readonly List<GridCoord> candidates = new List<GridCoord>();
    readonly RaycastHit[] hits = new RaycastHit[16];
    Vector3 position, lastSeen, goal;
    int pathIndex;
    float releaseTimer, lostTime, blowTime, replanTimer, leashTimer;
    FrontRoomsMapWorld.Door breakingDoor;
    HunterState resumeState;
    bool caught;
    uint rng;

    public HunterState State { get; private set; } = HunterState.Dormant;
    public float StateTime { get; private set; }
    public Vector3 Position => position;
    public Vector3 Heading { get; private set; } = Vector3.forward;
    public bool Moving { get; private set; }
    public bool Released => State != HunterState.Dormant;
    public bool SeesPlayer { get; private set; }
    public int DoorsBroken { get; private set; }
    public int Relays { get; private set; }

    public event Action<HunterState> StateChanged;
    public event Action<Vector3> DoorBlow;
    public event Action Caught;

    public FrontRoomsMapHunter(FrontRoomsMapWorld world, FrontRoomsHunterTuning tuning, Collider playerCollider, Transform rig, int seed)
    {
        this.world = world;
        this.tuning = tuning ?? new FrontRoomsHunterTuning();
        this.playerCollider = playerCollider;
        this.rig = rig;
        rng = (uint)seed | 1u;
    }

    public void Tick(float dt, Vector3 playerFeet, Vector3 playerEye, Vector3 playerForward)
    {
        if (caught || world == null) return;
        if (State == HunterState.Dormant)
        {
            releaseTimer += dt;
            if (releaseTimer >= tuning.releaseDelaySeconds && Arrive(playerFeet, playerEye, playerForward)) SetState(HunterState.Listen);
            return;
        }

        StateTime += dt;
        var playerCell = world.CellOf(playerFeet);
        var myCell = world.CellOf(position);

        // Never let the chase run off the built map, and never trail so far
        // behind that the player forgets it: relay closer, out of sight.
        leashTimer -= dt;
        if (!world.IsBuilt(myCell) || (State != HunterState.Chase && State != HunterState.BreakDoor && leashTimer <= 0f && Distance(myCell, playerCell, LeashCells + 1) > LeashCells))
        {
            leashTimer = LeashCheckSeconds;
            if (Arrive(playerFeet, playerEye, playerForward)) SetState(HunterState.Listen);
            return;
        }
        if (leashTimer <= 0f) leashTimer = LeashCheckSeconds;

        SeesPlayer = Sees(playerEye);
        if (SeesPlayer)
        {
            lastSeen = playerFeet;
            lostTime = 0f;
            if (State != HunterState.Chase && State != HunterState.BreakDoor)
            {
                replanTimer = 0f;
                SetState(HunterState.Chase);
            }
        }

        var before = position;
        switch (State)
        {
            case HunterState.Listen:
                // It hears the general area, not the exact spot.
                if (StateTime > tuning.listenSeconds) HuntToward(NearCell(playerCell), null);
                break;
            case HunterState.Hunt:
                if (Follow(tuning.huntSpeed, dt)) SetState(HunterState.Search);
                break;
            case HunterState.Search:
                if (StateTime > tuning.searchSeconds) SetState(HunterState.Listen);
                break;
            case HunterState.Chase:
                replanTimer -= dt;
                if (replanTimer <= 0f)
                {
                    replanTimer = ReplanSeconds;
                    Plan(myCell, world.CellOf(lastSeen), lastSeen);
                }
                if (SeesPlayer && myCell == playerCell) MoveDirect(playerFeet, tuning.chaseSpeed, dt);
                else Follow(tuning.chaseSpeed, dt);
                if (!SeesPlayer)
                {
                    lostTime += dt;
                    if (lostTime > tuning.lostSightSeconds) HuntToward(world.CellOf(lastSeen), lastSeen);
                }
                break;
            case HunterState.BreakDoor:
                TickBreak(dt);
                break;
        }
        var step = position - before;
        step.y = 0f;
        Moving = step.sqrMagnitude > 1e-6f;
        if (Moving) Heading = step.normalized;

        if (SeesPlayer && Flat(position - playerFeet).magnitude < tuning.catchDistance)
        {
            caught = true;
            Caught?.Invoke();
        }
    }

    /// <summary>A sound the player made. The Relay walks to the last one it heard.</summary>
    public void Noise(Vector3 source, float radius)
    {
        if (!Released || State == HunterState.Chase || State == HunterState.BreakDoor) return;
        if (Flat(position - source).magnitude > radius) return;
        HuntToward(world.CellOf(source), source);
    }

    void HuntToward(GridCoord cell, Vector3? point)
    {
        Plan(world.CellOf(position), cell, point ?? world.CellCenter(cell));
        SetState(HunterState.Hunt);
    }

    /// <summary>
    /// Arrive in a built cell 9–15 cells of walking away from the player that
    /// the player cannot see, preferring cells behind them. Used for the first
    /// release and for every relay.
    /// </summary>
    bool Arrive(Vector3 playerFeet, Vector3 playerEye, Vector3 playerForward)
    {
        var start = world.CellOf(playerFeet);
        Search(start, SpawnMaxCells, false);
        candidates.Clear();
        GridCoord fallback = start;
        var haveFallback = false;
        foreach (var pair in depth)
        {
            if (pair.Value < SpawnMinCells || pair.Value > SpawnMaxCells || !world.IsBuilt(pair.Key)) continue;
            var center = world.CellCenter(pair.Key);
            if (Visible(playerEye, center + Vector3.up * EyeHeight)) continue;
            if (!haveFallback) { fallback = pair.Key; haveFallback = true; }
            if (Vector3.Dot(Flat(center - playerFeet), Flat(playerForward)) < 0f) candidates.Add(pair.Key);
        }
        GridCoord chosen;
        if (candidates.Count > 0) chosen = candidates[(int)(Next() % (uint)candidates.Count)];
        else if (haveFallback) chosen = fallback;
        else return false;
        position = world.CellCenter(chosen);
        path.Clear();
        pathIndex = 0;
        breakingDoor = null;
        Relays++;
        return true;
    }

    /// <summary>A random reachable cell within a few cells of the given one.</summary>
    GridCoord NearCell(GridCoord around)
    {
        Search(around, SearchRadiusCells, true);
        candidates.Clear();
        foreach (var pair in depth) candidates.Add(pair.Key);
        return candidates.Count == 0 ? around : candidates[(int)(Next() % (uint)candidates.Count)];
    }

    /// <summary>
    /// Breadth-first search over built cells. Doors count as passable (the
    /// Relay breaks them); unbroken glass and walls do not.
    /// </summary>
    void Search(GridCoord start, int maxDepth, bool forRelay)
    {
        cameFrom.Clear();
        depth.Clear();
        frontier.Clear();
        depth[start] = 0;
        frontier.Enqueue(start);
        while (frontier.Count > 0)
        {
            var cell = frontier.Dequeue();
            var d = depth[cell];
            if (d >= maxDepth) continue;
            foreach (var s in Steps)
            {
                var next = cell + s;
                if (depth.ContainsKey(next) || !world.IsBuilt(next)) continue;
                var passage = world.PassageBetween(cell, next);
                if (passage == FrontRoomsMapWorld.Passage.Wall || passage == FrontRoomsMapWorld.Passage.Glass) continue;
                depth[next] = d + 1;
                cameFrom[next] = cell;
                frontier.Enqueue(next);
            }
        }
    }

    int Distance(GridCoord from, GridCoord to, int cap)
    {
        Search(from, cap, true);
        return depth.TryGetValue(to, out var d) ? d : int.MaxValue;
    }

    void Plan(GridCoord from, GridCoord to, Vector3 finalPoint)
    {
        goal = finalPoint;
        path.Clear();
        pathIndex = 0;
        if (from == to) return;
        Search(from, 64, true);
        if (!depth.ContainsKey(to)) return;
        for (var c = to; c != from; c = cameFrom[c]) path.Add(c);
        path.Reverse();
    }

    /// <summary>Walk the planned path. Returns true once the goal is reached.</summary>
    bool Follow(float speed, float dt)
    {
        if (pathIndex >= path.Count) return MoveDirect(goal, speed, dt);
        var here = world.CellOf(position);
        var next = path[pathIndex];
        if (here == next)
        {
            pathIndex++;
            return pathIndex >= path.Count && MoveDirect(goal, speed, dt);
        }
        var passage = world.PassageBetween(here, next);
        if (passage == FrontRoomsMapWorld.Passage.ClosedDoor)
        {
            // Walk up to the door on this side, then break it down.
            var door = world.DoorBetween(here, next);
            var face = world.CellCenter(here) + Flat(world.CellCenter(next) - world.CellCenter(here)) * .38f;
            if (MoveDirect(face, speed, dt) && door != null)
            {
                breakingDoor = door;
                blowTime = BlowInterval;
                resumeState = State;
                SetState(HunterState.BreakDoor);
            }
            return false;
        }
        if (passage != FrontRoomsMapWorld.Passage.Open)
        {
            // The map changed under the path (a wall where a door was): plan again.
            Plan(here, path[path.Count - 1], goal);
            return false;
        }
        // Through doorways the line between cell centres is always clear.
        MoveDirect(world.CellCenter(next), speed, dt);
        return false;
    }

    bool MoveDirect(Vector3 target, float speed, float dt)
    {
        target.y = position.y;
        position = Vector3.MoveTowards(position, target, speed * dt);
        return Flat(position - target).sqrMagnitude < .04f * .04f;
    }

    void TickBreak(float dt)
    {
        blowTime += dt;
        if (blowTime >= BlowInterval)
        {
            blowTime = 0f;
            if (breakingDoor != null) DoorBlow?.Invoke(breakingDoor.position);
        }
        if (StateTime < tuning.breakDoorSeconds) return;
        if (breakingDoor != null)
        {
            world.BreakDoor(breakingDoor);
            DoorsBroken++;
        }
        breakingDoor = null;
        SetState(resumeState == HunterState.Chase ? HunterState.Chase : HunterState.Hunt);
    }

    bool Sees(Vector3 playerEye)
    {
        var eye = position + Vector3.up * EyeHeight;
        if ((playerEye - eye).magnitude > tuning.sightRange) return false;
        return Visible(eye, playerEye);
    }

    /// <summary>
    /// True when nothing but the player (or nothing at all) lies between the
    /// two points. Hits on the Relay's own rig are ignored.
    /// </summary>
    bool Visible(Vector3 from, Vector3 to)
    {
        var dir = to - from;
        var distance = dir.magnitude;
        if (distance < .01f) return true;
        var count = Physics.RaycastNonAlloc(from, dir / distance, hits, distance, ~0, QueryTriggerInteraction.Ignore);
        var nearest = float.MaxValue;
        Collider blocker = null;
        for (var i = 0; i < count; i++)
        {
            var c = hits[i].collider;
            if (c == null || (rig != null && c.transform.IsChildOf(rig))) continue;
            if (hits[i].distance < nearest) { nearest = hits[i].distance; blocker = c; }
        }
        return blocker == null || blocker == playerCollider;
    }

    void SetState(HunterState next)
    {
        if (next == State) { StateTime = 0f; return; }
        State = next;
        StateTime = 0f;
        StateChanged?.Invoke(next);
    }

    uint Next()
    {
        rng ^= rng << 13;
        rng ^= rng >> 17;
        rng ^= rng << 5;
        return rng;
    }

    static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0f, v.z);
}
