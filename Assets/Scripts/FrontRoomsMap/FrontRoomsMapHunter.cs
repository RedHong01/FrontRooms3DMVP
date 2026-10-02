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
/// - if the chase leaves it too far behind, it relays itself closer, unseen;
/// - it has a body (<see cref="ModuleUnits.RelayRadius"/>): it walks straight
///   while the way is clear and plans a detour on a 0.25 m grid around the
///   cell it is in and the next one when furniture, a column or an open door
///   leaf is in the way. With no way round furniture it passes through it,
///   still on a route that keeps out of walls.
/// Positions are world space; the caller drives the rig.
/// </summary>
public sealed class FrontRoomsMapHunter
{
    const float EyeHeight = ModuleUnits.RelayEye;
    // The body as it is tested: between knee and head height, so it fits a
    // broken window (sill 0.35, head 2.0) and a door (head 2.1).
    const float Radius = ModuleUnits.RelayRadius, ProbeBottom = .4f, ProbeTop = 1.95f;
    const float NodeStep = .25f, StraightRecheck = .25f;
    const int NodesPerCell = 12, MaxRegionCells = 4, MaxRegionNodes = NodesPerCell * NodesPerCell * MaxRegionCells * MaxRegionCells;
    const float BlowInterval = .5f;
    // After the last blow it waits for the leaf to fall open (it swings in 0.18 s).
    const float DoorFallSeconds = .25f;
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
    readonly RaycastHit[] bodyHits = new RaycastHit[16];
    readonly Collider[] overlaps = new Collider[16];
    // Detour planning scratch: a region of at most 4 x 4 cells at 0.25 m.
    readonly List<Vector3> detour = new List<Vector3>();
    readonly List<int> nodePath = new List<int>();
    readonly List<int> heapNode = new List<int>();
    readonly List<float> heapKey = new List<float>();
    readonly sbyte[] nodeFree = new sbyte[MaxRegionNodes];
    readonly float[] nodeCost = new float[MaxRegionNodes];
    readonly int[] nodeParent = new int[MaxRegionNodes];
    readonly bool[] nodeClosed = new bool[MaxRegionNodes];
    Vector3 position, lastSeen, goal;
    int pathIndex;
    float releaseTimer, lostTime, blowTime, replanTimer, leashTimer;
    // Steering: the aim the current plan was made for, the detour toward it
    // (empty = straight), and whether the detour ends short of the aim.
    Vector3 planTarget = new Vector3(float.MaxValue, 0f, 0f);
    int detourIndex;
    bool detourShort, unreachable, ghosting;
    // The cell a crossing leg started from: a detour may cut through a
    // neighbouring cell, and that must not count as leaving the route.
    GridCoord legFrom, legTo;
    bool hasLeg;
    float straightCheck;
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
    /// <summary>True while it passes through furniture it found no way round, until its body is clear again.</summary>
    public bool Ghosting => ghosting;
    /// <summary>Tools: the route and steering state, for test reports.</summary>
    public string DebugSteering => "path " + pathIndex + "/" + path.Count + (pathIndex < path.Count ? " next " + path[pathIndex] : "") + " detour " + detourIndex + "/" + detour.Count
        + (detourIndex < detour.Count ? " aim " + detour[detourIndex].ToString("F2") : "") + (ghosting ? " ghosting" : "") + (detourShort ? " short" : "") + " plan " + planTarget.ToString("F2");
    /// <summary>Tools: what the body touched or the straight leg hit when it last chose to pass through.</summary>
    public string DebugBlocker { get; private set; } = "";
    /// <summary>Times it found no way round furniture and passed through it.</summary>
    public int Ghosts { get; private set; }

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

    /// <summary>Tools and tests: stand released at a point (searching), with no plan.</summary>
    public void DebugPlace(Vector3 feet)
    {
        position = feet;
        path.Clear();
        pathIndex = 0;
        breakingDoor = null;
        ResetSteering();
        SetState(HunterState.Search);
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
            if (!BodyFits(center) || Visible(playerEye, center + Vector3.up * EyeHeight)) continue;
            if (!haveFallback) { fallback = pair.Key; haveFallback = true; }
            if (Vector3.Dot(Flat(center - playerFeet), Flat(playerForward)) < 0f) candidates.Add(pair.Key);
        }
        GridCoord chosen;
        if (candidates.Count > 0) chosen = candidates[(int)(Next() % (uint)candidates.Count)];
        else if (haveFallback) chosen = fallback;
        else return false;
        position = world.CellCenter(chosen);
        ResetSteering();
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
        if (pathIndex >= path.Count) return MoveDirect(goal, speed, dt, true);
        var here = world.CellOf(position);
        var next = path[pathIndex];
        if (here == next)
        {
            pathIndex++;
            return pathIndex >= path.Count && MoveDirect(goal, speed, dt, true);
        }
        if (hasLeg && legTo == next && detourIndex < detour.Count) here = legFrom;
        else
        {
            legFrom = here;
            legTo = next;
            hasLeg = true;
        }
        if (Mathf.Abs(here.x - next.x) + Mathf.Abs(here.y - next.y) != 1)
        {
            // A detour or a pass-through left it off its path: plan again from where it stands.
            Plan(here, path[path.Count - 1], goal);
            return false;
        }
        var passage = world.PassageBetween(here, next);
        if (passage == FrontRoomsMapWorld.Passage.ClosedDoor)
        {
            // Walk up to the door on this side, then break it down.
            var door = world.DoorBetween(here, next);
            var face = world.CrossingPoint(here, next) - Flat(world.CellCenter(next) - world.CellCenter(here)).normalized * .45f;
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
        // Cross at the opening itself (doorways sit off-centre), aiming a
        // little past the edge so the next step starts inside the next cell.
        MoveDirect(world.CrossingPoint(here, next) + Flat(world.CellCenter(next) - world.CellCenter(here)).normalized * .35f, speed, dt, false, next);
        return false;
    }

    /// <summary>
    /// Walk toward a point. Returns true on arrival. With <paramref name="enter"/>
    /// the leg's purpose is to step into that cell (a crossing), so a detour
    /// may end anywhere inside it. A <paramref name="final"/> point that
    /// furniture covers counts as reached once it stands as close as it can,
    /// so it searches beside a desk rather than inside it.
    /// </summary>
    bool MoveDirect(Vector3 target, float speed, float dt, bool final = false, GridCoord? enter = null)
    {
        target.y = position.y;
        if (Flat(target - planTarget).sqrMagnitude > .25f) Steer(target, final, enter);
        else if (detour.Count == 0 && (straightCheck -= dt) <= 0f) Steer(target, final, enter);
        if (unreachable)
        {
            // Nothing free near a final point: stop here, the hunt is over.
            unreachable = false;
            return true;
        }
        var onDetour = detourIndex < detour.Count;
        var aim = onDetour ? detour[detourIndex] : target;
        aim.y = position.y;
        // Doors swing and the player moves: keep checking the leg it is on.
        if (onDetour && (straightCheck -= dt) <= 0f)
        {
            straightCheck = StraightRecheck;
            if (!PathClear(position, aim, !ghosting))
            {
                Steer(target, final, enter);
                onDetour = detourIndex < detour.Count;
                aim = onDetour ? detour[detourIndex] : target;
                aim.y = position.y;
            }
        }
        position = Vector3.MoveTowards(position, aim, speed * dt);
        if (onDetour && Flat(position - aim).sqrMagnitude < .0004f && ++detourIndex >= detour.Count)
        {
            detour.Clear();
            detourIndex = 0;
            straightCheck = 0f;
            if (ghosting && BodyFits(position, true)) ghosting = false;
            if (detourShort && final) return true;
        }
        return Flat(position - target).sqrMagnitude < .04f * .04f;
    }

    void ResetSteering()
    {
        detour.Clear();
        detourIndex = 0;
        detourShort = unreachable = ghosting = hasLeg = false;
        planTarget = new Vector3(float.MaxValue, 0f, 0f);
        straightCheck = 0f;
    }

    /// <summary>
    /// Decide how to reach the aim: straight if the body fits the whole way,
    /// else a detour round the furniture, else through the furniture on a
    /// route that still keeps out of walls. Standing inside furniture (after
    /// passing through, or when a door swings into it) also means passing through.
    /// </summary>
    void Steer(Vector3 target, bool final, GridCoord? enter)
    {
        planTarget = target;
        detour.Clear();
        detourIndex = 0;
        detourShort = false;
        straightCheck = StraightRecheck;
        var inside = !BodyFits(position, true);
        if (!inside)
        {
            ghosting = false;
            if (Flat(target - position).sqrMagnitude < .0004f || PathClear(position, target, true)) return;
            if (PlanDetour(target, enter, true)) return;
            if (final)
            {
                unreachable = true;
                return;
            }
            Ghosts++;
            DebugBlocker = Blocker(position, target);
        }
        ghosting = true;
        if (!PathClear(position, target, false)) PlanDetour(target, enter, false);
    }

    /// <summary>
    /// A* on a 0.25 m grid over the cell the body is in and the aim's cell (or
    /// <paramref name="enter"/>), with one cell of margin round them. A node
    /// is free when the body fits there; with <paramref name="furniture"/>
    /// off only walls, columns, doors and glass count. The result is
    /// string-pulled into a few straight legs.
    /// </summary>
    bool PlanDetour(Vector3 target, GridCoord? enter, bool furniture)
    {
        var from = world.CellOf(position);
        var to = enter ?? world.CellOf(target);
        if (Mathf.Abs(from.x - to.x) > 1 || Mathf.Abs(from.y - to.y) > 1) to = from;
        var minCell = new GridCoord(Mathf.Min(from.x, to.x) - 1, Mathf.Min(from.y, to.y) - 1);
        var maxCell = new GridCoord(Mathf.Max(from.x, to.x) + 1, Mathf.Max(from.y, to.y) + 1);
        var cols = (maxCell.x - minCell.x + 1) * NodesPerCell;
        var rows = (maxCell.y - minCell.y + 1) * NodesPerCell;
        var count = cols * rows;
        var corner = world.CellCenter(minCell) - new Vector3(MapGrid.CellSize * .5f, 0f, MapGrid.CellSize * .5f);
        corner.y = position.y;
        Vector3 Node(int k) => corner + new Vector3((k % cols + .5f) * NodeStep, 0f, (k / cols + .5f) * NodeStep);
        bool Free(int k)
        {
            if (nodeFree[k] == 0)
            {
                var p = Node(k);
                nodeFree[k] = (sbyte)(world.IsBuilt(world.CellOf(p)) && BodyFits(p, furniture) ? 1 : -1);
            }
            return nodeFree[k] > 0;
        }
        bool Goal(int k)
        {
            if (enter.HasValue) return world.CellOf(Node(k)) == enter.Value;
            return Flat(Node(k) - target).sqrMagnitude <= .3f * .3f;
        }
        for (var k = 0; k < count; k++)
        {
            nodeFree[k] = 0;
            nodeCost[k] = float.MaxValue;
            nodeParent[k] = -1;
            nodeClosed[k] = false;
        }

        // Start from the free node nearest the body.
        var local = position - corner;
        int sx = Mathf.Clamp(Mathf.FloorToInt(local.x / NodeStep), 0, cols - 1), sz = Mathf.Clamp(Mathf.FloorToInt(local.z / NodeStep), 0, rows - 1);
        var start = -1;
        var startDistance = float.MaxValue;
        for (var dz = -3; dz <= 3; dz++)
        for (var dx = -3; dx <= 3; dx++)
        {
            int x = sx + dx, z = sz + dz;
            if (x < 0 || z < 0 || x >= cols || z >= rows) continue;
            var k = x + z * cols;
            var d = Flat(Node(k) - position).sqrMagnitude;
            if (d < startDistance && Free(k)) { start = k; startDistance = d; }
        }
        if (start < 0) return false;

        heapNode.Clear();
        heapKey.Clear();
        nodeCost[start] = 0f;
        Push(start, Flat(Node(start) - target).magnitude);
        var reached = -1;
        var best = start;
        var bestDistance = float.MaxValue;
        while (heapNode.Count > 0)
        {
            var k = Pop();
            if (nodeClosed[k]) continue;
            nodeClosed[k] = true;
            var distance = Flat(Node(k) - target).magnitude;
            if (distance < bestDistance) { bestDistance = distance; best = k; }
            if (Goal(k)) { reached = k; break; }
            int x = k % cols, z = k / cols;
            for (var dz = -1; dz <= 1; dz++)
            for (var dx = -1; dx <= 1; dx++)
            {
                if (dx == 0 && dz == 0) continue;
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= cols || nz >= rows) continue;
                var n = nx + nz * cols;
                if (nodeClosed[n] || !Free(n)) continue;
                // No cutting a corner past a blocked node.
                if (dx != 0 && dz != 0 && (!Free(nx + z * cols) || !Free(x + nz * cols))) continue;
                var cost = nodeCost[k] + (dx != 0 && dz != 0 ? NodeStep * 1.4142f : NodeStep);
                if (cost >= nodeCost[n]) continue;
                nodeCost[n] = cost;
                nodeParent[n] = k;
                Push(n, cost + Flat(Node(n) - target).magnitude);
            }
        }
        // A final aim that no node reaches: settle for the closest free spot.
        if (reached < 0)
        {
            if (enter.HasValue || best == start) return false;
            reached = best;
            detourShort = true;
        }

        nodePath.Clear();
        for (var k = reached; k >= 0; k = nodeParent[k]) nodePath.Add(k);
        nodePath.Reverse();
        // String-pull: from where it stands, jump to the farthest node it can walk to straight.
        var at = position;
        var i0 = 0;
        while (i0 < nodePath.Count - 1)
        {
            var next = i0 + 1;
            for (var j = nodePath.Count - 1; j > i0 + 1; j--)
                if (PathClear(at, Node(nodePath[j]), furniture)) { next = j; break; }
            at = Node(nodePath[next]);
            detour.Add(at);
            i0 = next;
        }
        if (detour.Count == 0) detour.Add(Node(reached));
        if (!detourShort && !enter.HasValue && PathClear(at, target, furniture)) detour.Add(target);
        return true;
    }

    void Push(int node, float key)
    {
        heapNode.Add(node);
        heapKey.Add(key);
        var i = heapNode.Count - 1;
        while (i > 0)
        {
            var parent = (i - 1) / 2;
            if (heapKey[parent] <= heapKey[i]) break;
            Swap(i, parent);
            i = parent;
        }
    }

    int Pop()
    {
        var top = heapNode[0];
        var last = heapNode.Count - 1;
        Swap(0, last);
        heapNode.RemoveAt(last);
        heapKey.RemoveAt(last);
        var i = 0;
        while (true)
        {
            int l = i * 2 + 1, r = l + 1, m = i;
            if (l < heapNode.Count && heapKey[l] < heapKey[m]) m = l;
            if (r < heapNode.Count && heapKey[r] < heapKey[m]) m = r;
            if (m == i) break;
            Swap(i, m);
            i = m;
        }
        return top;
    }

    void Swap(int a, int b)
    {
        (heapNode[a], heapNode[b]) = (heapNode[b], heapNode[a]);
        (heapKey[a], heapKey[b]) = (heapKey[b], heapKey[a]);
    }

    /// <summary>
    /// True when the body can walk straight from a to b without touching
    /// anything but the player or its rig (with <paramref name="furniture"/>
    /// off, only walls, columns, doors and glass count).
    /// </summary>
    bool PathClear(Vector3 a, Vector3 b, bool furniture)
    {
        var dir = Flat(b - a);
        var distance = dir.magnitude;
        if (distance < 1e-4f) return true;
        dir /= distance;
        var count = Physics.CapsuleCastNonAlloc(a + Vector3.up * (ProbeBottom + Radius), a + Vector3.up * (ProbeTop - Radius), Radius, dir, bodyHits, distance, ~0, QueryTriggerInteraction.Ignore);
        for (var i = 0; i < count; i++)
        {
            var c = bodyHits[i].collider;
            if (Ignored(c, furniture)) continue;
            // A collider it already stands in (distance 0) does not stop it walking out.
            if (bodyHits[i].distance <= 0f) continue;
            return false;
        }
        return true;
    }

    /// <summary>True when the body standing here would touch nothing but the player or its own rig.</summary>
    bool BodyFits(Vector3 feet, bool furniture = true)
    {
        var count = Physics.OverlapCapsuleNonAlloc(feet + Vector3.up * (ProbeBottom + Radius), feet + Vector3.up * (ProbeTop - Radius), Radius, overlaps, ~0, QueryTriggerInteraction.Ignore);
        for (var i = 0; i < count; i++)
            if (!Ignored(overlaps[i], furniture)) return false;
        return true;
    }

    /// <summary>Tools: names what the straight leg hits, for reports.</summary>
    string Blocker(Vector3 a, Vector3 b)
    {
        var dir = Flat(b - a);
        var distance = dir.magnitude;
        if (distance < 1e-4f) return "";
        var count = Physics.CapsuleCastNonAlloc(a + Vector3.up * (ProbeBottom + Radius), a + Vector3.up * (ProbeTop - Radius), Radius, dir / distance, bodyHits, distance, ~0, QueryTriggerInteraction.Ignore);
        var names = "";
        for (var i = 0; i < count; i++)
            if (!Ignored(bodyHits[i].collider, true) && bodyHits[i].distance > 0f)
                names += bodyHits[i].collider.name + (bodyHits[i].collider.transform.parent != null ? "<" + bodyHits[i].collider.transform.parent.name : "") + "@" + bodyHits[i].distance.ToString("F2") + " ";
        return names;
    }

    bool Ignored(Collider c, bool furniture) =>
        c == null || c == playerCollider || (rig != null && c.transform.IsChildOf(rig)) || (!furniture && !world.IsArchitecture(c));

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
            world.BreakDoor(breakingDoor, position);
            DoorsBroken++;
            breakingDoor = null;
        }
        if (StateTime < tuning.breakDoorSeconds + DoorFallSeconds) return;
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
