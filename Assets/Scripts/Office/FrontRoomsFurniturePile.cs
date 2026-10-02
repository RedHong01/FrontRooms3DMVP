using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// The film's furniture piles: intact, recognisable pieces copy-pasted into
/// one place. Nothing is broken; it is placed wrong. Pieces rest in legible,
/// quantised states (upright, on the back, on a side, exactly inverted, or
/// leaning 30-52 degrees on an edge against a neighbour), exact duplicates
/// interpenetrate, and the pile rises toward the ceiling as a landmark in an
/// empty hall.
///
/// Deterministic per seed (a chunk rebuilt later gets the same pile), no
/// runtime physics: an analytic solver over oriented boxes from the kit
/// sidecars. Called by the maze (halls of 4x4+ cells) by reflection and by
/// the look-dev hall. See Documentation/OFFICE_LEVEL_FURNITURE_RESEARCH.md
/// (distortion section) for the reasoning behind every rule.
/// </summary>
public static class FrontRoomsFurniturePile
{
    public enum Rest { Upright, Back, Front, Side, Inverted, EdgeLean }
    public enum Tableau { CentreSculpture, CopyPasteRow, CeilingStuck, OfficeCluster, ZeroPile }

    const float CeilingClearance = .06f;
    const float GlobalOverlapBudget = .22f;

    sealed class Piece
    {
        public string asset;
        public FrontRoomsKitLibrary.Info info;
        public string cls;
        public int mass;
        public Rest[] states;
        public float tolerance;
        public string palette;
        public bool topper;
        public Vector3 centre => (info.Min + info.Max) * .5f;
        public Vector3 half => info.Size * .5f;
        public float Volume => Mathf.Max(1e-4f, info.Size.x * info.Size.y * info.Size.z);
        public bool Allows(Rest r) => Array.IndexOf(states, r) >= 0;
    }

    sealed class Placed
    {
        public Piece piece;
        public Vector3 position;     // asset origin, pile-local
        public Quaternion rotation;
        public Rest rest;
        public int copyGroup = -1;   // pieces of one copy-paste run
        public Vector3 obbCentre => position + rotation * piece.centre;
        public Vector3 obbHalf => piece.half;

        public void Corners(Vector3[] into)
        {
            var c = obbCentre; var h = obbHalf; var i = 0;
            for (var x = -1; x <= 1; x += 2)
                for (var y = -1; y <= 1; y += 2)
                    for (var z = -1; z <= 1; z += 2)
                        into[i++] = c + rotation * Vector3.Scale(h, new Vector3(x, y, z));
        }

        public bool Contains(Vector3 p, float pad = 0f)
        {
            var local = Quaternion.Inverse(rotation) * (p - obbCentre);
            var h = obbHalf;
            return Mathf.Abs(local.x) <= h.x + pad && Mathf.Abs(local.y) <= h.y + pad && Mathf.Abs(local.z) <= h.z + pad;
        }
    }

    sealed class Plan
    {
        public Vector3 centre;
        public float radius, ceiling, hMax;
        public readonly List<Placed> placed = new List<Placed>();
        public float totalVolume, overlapVolume;
        public int nextCopyGroup;
    }

    sealed class Rng
    {
        uint state;
        public Rng(int seed) { state = (uint)seed * 747796405u + 2891336453u; if (state == 0) state = 1; }
        public float Next() { state ^= state << 13; state ^= state >> 17; state ^= state << 5; return (state & 0xFFFFFF) / 16777216f; }
        public float Range(float a, float b) => a + (b - a) * Next();
        public int Range(int a, int bExclusive) => a + Mathf.Min(bExclusive - a - 1, (int)(Next() * (bExclusive - a)));
        public bool Chance(float p) => Next() < p;
        public T Pick<T>(IList<T> list) => list[Range(0, list.Count)];
    }

    static List<Piece> library;
    static readonly Vector3[] CornersA = new Vector3[8];

    // ===================================================================== API

    /// <summary>Reflection entry point used by FrontRoomsMapWorld.</summary>
    public static void Build(Transform parent, Vector3 localCenter, float radius, float ceilingHeight, int seed)
    {
        BuildPile(parent, localCenter, radius, ceilingHeight, seed, null);
    }

    /// <summary>Build and return the pile root (null if the kit has too few pieces).</summary>
    public static GameObject BuildPile(Transform parent, Vector3 localCenter, float radius, float ceilingHeight, int seed, Tableau? force)
    {
        var lib = Library();
        if (parent == null || lib.Count == 0 || radius < .6f || ceilingHeight < 1.8f) return null;
        var rng = new Rng(seed);
        var tableau = force ?? ChooseTableau(rng, lib, radius, ceilingHeight);
        var plan = new Plan
        {
            centre = Vector3.zero,
            radius = radius,
            ceiling = ceilingHeight,
            hMax = Mathf.Min(ceilingHeight - CeilingClearance, HeightRatio(tableau, rng) * ceilingHeight),
        };
        switch (tableau)
        {
            case Tableau.CentreSculpture: CentreSculpture(plan, lib, rng); break;
            case Tableau.CopyPasteRow: CopyPasteRow(plan, lib, rng); break;
            case Tableau.CeilingStuck: CeilingStuck(plan, lib, rng); break;
            case Tableau.OfficeCluster: OfficeCluster(plan, lib, rng); break;
            case Tableau.ZeroPile: ZeroPile(plan, lib, rng); break;
        }
        if (plan.placed.Count == 0) return null;
        var root = new GameObject("furniture pile (" + tableau + ")").transform;
        root.SetParent(parent, false);
        root.localPosition = localCenter;
        foreach (var p in plan.placed)
        {
            // Small pieces stay walk-through; everything else blocks.
            var blocks = p.piece.cls != "Small" && p.piece.info.Size.magnitude > .5f;
            FrontRoomsKitLibrary.Spawn(p.piece.asset, root, p.position, p.rotation, null, blocks, p.piece.asset + " / " + p.rest);
        }
        return root.gameObject;
    }

    // ================================================================ library

    static List<Piece> Library()
    {
        if (library != null) return library;
        library = new List<Piece>();
        foreach (var name in FrontRoomsKitLibrary.AllNames())
        {
            var info = FrontRoomsKitLibrary.GetInfo(name);
            if (info == null || !info.IsPilePiece) continue;
            var states = new List<Rest>();
            if (info.pile.states != null)
                foreach (var s in info.pile.states)
                    if (Enum.TryParse(s, out Rest r)) states.Add(r);
            if (states.Count == 0) states.Add(Rest.Upright);
            library.Add(new Piece
            {
                asset = name,
                info = info,
                cls = info.pile.cls,
                mass = info.pile.mass,
                states = states.ToArray(),
                tolerance = info.pile.tolerance > 0f ? info.pile.tolerance : .25f,
                palette = info.pile.palette,
                topper = info.pile.topper,
            });
        }
        return library;
    }

    static List<Piece> Filter(List<Piece> lib, Func<Piece, bool> keep)
    {
        var list = new List<Piece>();
        foreach (var p in lib) if (keep(p)) list.Add(p);
        return list;
    }

    static Tableau ChooseTableau(Rng rng, List<Piece> lib, float radius, float ceiling)
    {
        var heavy = Filter(lib, p => p.mass >= 2).Count;
        var seats = Filter(lib, p => p.cls == "Seat").Count;
        var office = Filter(lib, p => p.palette == "office90s").Count;
        var roll = rng.Next();
        if (ceiling > 4.5f && roll < .12f) return Tableau.ZeroPile;
        if (heavy >= 2 && lib.Count >= 6 && roll < .62f) return Tableau.CentreSculpture;
        if (seats > 0 && roll < .80f) return Tableau.CopyPasteRow;
        if (ceiling < 3.2f && seats > 0 && roll < .90f) return Tableau.CeilingStuck;
        if (office >= 3) return Tableau.OfficeCluster;
        return heavy >= 1 ? Tableau.CentreSculpture : Tableau.CopyPasteRow;
    }

    static float HeightRatio(Tableau t, Rng rng)
    {
        switch (t)
        {
            case Tableau.CentreSculpture: return rng.Range(.82f, .95f);
            case Tableau.CeilingStuck: return 1f;
            case Tableau.CopyPasteRow: return rng.Range(.45f, .8f);
            case Tableau.OfficeCluster: return .72f;
            default: return .6f;
        }
    }

    // =============================================================== tableaux

    static void CentreSculpture(Plan plan, List<Piece> lib, Rng rng)
    {
        var bases = Filter(lib, p => p.mass >= 2);
        var mids = Filter(lib, p => p.cls != "Small" && p.cls != "Tall");
        var seatsTables = Filter(lib, p => p.cls == "Seat" || p.cls == "Table");
        var cases = Filter(lib, p => p.Allows(Rest.EdgeLean));
        var talls = Filter(lib, p => p.cls == "Tall");
        var toppers = Filter(lib, p => p.topper);
        var smalls = Filter(lib, p => p.cls == "Small");

        // Counts scale with the radius: the film's piles are a dense mass of
        // furniture, not a few objects (R 3.2 → ~4 bases, ~10 stacked pieces).
        var r = plan.radius;
        Repeat(Mathf.Clamp(Mathf.RoundToInt(r * 1.3f), 2, 5), () => TryBase(plan, bases.Count > 0 ? bases : mids, rng));
        Repeat(Mathf.Clamp(Mathf.RoundToInt(r * .8f), 1, 3), () => TryEdgeLean(plan, cases, rng));
        Repeat(Mathf.Clamp(Mathf.RoundToInt(r * 3.2f), 4, 12), () => TryStack(plan, mids, rng, null, highest: rng.Chance(.45f)));
        Repeat(rng.Range(2, 5), () => TryStack(plan, seatsTables, rng, Rest.Inverted, highest: rng.Chance(.3f)));
        if (seatsTables.Count > 0) TryCopyPasteRun(plan, seatsTables, rng, rng.Range(3, 6));
        Repeat(Mathf.Clamp(Mathf.RoundToInt(r * 1.5f), 2, 5), () => TryStack(plan, mids, rng, null, highest: true));
        if (talls.Count > 0) TrySpike(plan, talls, rng);
        if (toppers.Count > 0) TryStack(plan, toppers, rng, null, highest: true);
        if (smalls.Count > 0) Repeat(rng.Range(4, 8), () => TrySatellite(plan, smalls, rng));
    }

    static void CopyPasteRow(Plan plan, List<Piece> lib, Rng rng)
    {
        var seats = Filter(lib, p => p.cls == "Seat" || p.cls == "Soft" || p.cls == "Table");
        if (seats.Count == 0) seats = Filter(lib, p => p.cls != "Small");
        if (seats.Count == 0) return;
        var piece = rng.Pick(seats);
        var yaw = rng.Pick(new[] { 0f, 90f, 180f, 270f });
        var count = Mathf.Clamp(Mathf.RoundToInt(plan.radius * 2f / Mathf.Max(.25f, piece.info.Size.x * .55f)), 5, 14);
        var step = piece.info.Size.x * rng.Range(.3f, .5f);
        var yawStep = rng.Pick(new[] { 0f, 3f, 7f });
        var start = -step * (count - 1) * .5f;
        var axis = Quaternion.Euler(0f, yaw, 0f) * Vector3.right;
        var group = plan.nextCopyGroup++;
        for (var i = 0; i < count; i++)
        {
            var rot = Quaternion.Euler(0f, yaw + yawStep * i, 0f);
            var pos = axis * (start + step * i);
            var placed = Make(piece, Rest.Upright, rot, pos, 0f);
            placed.copyGroup = group;
            TryCommit(plan, placed, ignoreOverlapWithGroup: true);
        }
        // A second, inverted row pasted on top when it fits.
        if (piece.Allows(Rest.Inverted) && rng.Chance(.5f))
            for (var i = 0; i < count; i += 2)
            {
                var rot = Quaternion.Euler(0f, yaw + yawStep * i + 180f, 0f);
                var pos = axis * (start + step * i);
                var top = TopAt(plan, pos);
                var placed = Make(piece, Rest.Inverted, rot, pos, top);
                placed.copyGroup = group;
                TryCommit(plan, placed, ignoreOverlapWithGroup: true);
            }
    }

    static void CeilingStuck(Plan plan, List<Piece> lib, Rng rng)
    {
        var stackable = Filter(lib, p => (p.cls == "Seat" || p.cls == "Crate" || p.cls == "Table") && p.info.Height < plan.ceiling * .45f);
        if (stackable.Count == 0) { CentreSculpture(plan, lib, rng); return; }
        var piece = rng.Pick(stackable);
        var group = plan.nextCopyGroup++;
        var y = 0f;
        var yaw = rng.Range(0f, 360f);
        for (var i = 0; i < 12; i++)
        {
            var rest = i % 2 == 0 || !piece.Allows(Rest.Inverted) ? Rest.Upright : Rest.Inverted;
            var rot = Quaternion.Euler(0f, yaw + rng.Range(-9f, 9f), 0f);
            var pos = new Vector3(rng.Range(-.06f, .06f), 0f, rng.Range(-.06f, .06f));
            // The column touches the ceiling: the last piece may sink into it.
            var placed = Make(piece, rest, rot, pos, y);
            placed.copyGroup = group;
            var top = Top(placed);
            if (top > plan.ceiling + .12f) break;
            plan.hMax = plan.ceiling + .12f;
            if (!TryCommit(plan, placed, ignoreOverlapWithGroup: true)) break;
            // Interlock a little: the next copy sits 12% into this one.
            y = top - (top - y) * .12f;
        }
        var bases = Filter(lib, p => p.mass >= 2);
        if (bases.Count > 0) Repeat(2, () => TryBase(plan, bases, rng, minR: .45f));
    }

    static void OfficeCluster(Plan plan, List<Piece> lib, Rng rng)
    {
        var office = Filter(lib, p => p.palette == "office90s" && p.cls != "Small");
        if (office.Count == 0) { CentreSculpture(plan, lib, rng); return; }
        Repeat(2, () => TryBase(plan, Filter(office, p => p.mass >= 1), rng));
        Repeat(2, () => TryEdgeLean(plan, Filter(office, p => p.Allows(Rest.EdgeLean)), rng));
        Repeat(3, () => TryStack(plan, office, rng, rng.Chance(.5f) ? Rest.Side : (Rest?)null));
        TryCopyPasteRun(plan, office, rng, rng.Range(2, 4));
    }

    static void ZeroPile(Plan plan, List<Piece> lib, Rng rng)
    {
        var seats = Filter(lib, p => p.cls == "Seat");
        if (seats.Count == 0) seats = Filter(lib, p => p.cls != "Small");
        if (seats.Count == 0) return;
        TryCommit(plan, Make(rng.Pick(seats), Rest.Upright, Quaternion.identity, Vector3.zero, 0f));
    }

    // ============================================================= operators

    static void Repeat(int n, Func<bool> op)
    {
        for (var i = 0; i < n; i++) op();
    }

    static bool TryBase(Plan plan, List<Piece> pool, Rng rng, float minR = 0f)
    {
        if (pool.Count == 0) return false;
        for (var attempt = 0; attempt < 10; attempt++)
        {
            var piece = rng.Pick(pool);
            var rest = piece.Allows(Rest.Back) && rng.Chance(.3f) ? Rest.Back : Rest.Upright;
            var r = Mathf.Lerp(minR, .55f, rng.Next()) * plan.radius;
            var a = rng.Range(0f, Mathf.PI * 2f);
            var yaw = rng.Pick(new[] { 0f, 90f, 180f, 270f }) + rng.Range(-12f, 12f);
            var placed = Make(piece, rest, Quaternion.Euler(0f, yaw, 0f), new Vector3(Mathf.Cos(a) * r, 0f, Mathf.Sin(a) * r), 0f);
            if (TryCommit(plan, placed)) return true;
        }
        return false;
    }

    /// <summary>Stand a case next to a committed piece and tip it onto it about
    /// its bottom edge until first contact, then jam it a few degrees.</summary>
    static bool TryEdgeLean(Plan plan, List<Piece> pool, Rng rng)
    {
        if (pool.Count == 0 || plan.placed.Count == 0) return false;
        for (var attempt = 0; attempt < 12; attempt++)
        {
            var piece = rng.Pick(pool);
            var target = plan.placed[rng.Range(0, plan.placed.Count)];
            if (target.rest == Rest.EdgeLean) continue;
            var a = rng.Range(0f, Mathf.PI * 2f);
            var dir = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
            // Face the piece's front or back toward the target so it tips forward/back.
            var yaw = Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg + (rng.Chance(.5f) ? 0f : 180f);
            var upright = Quaternion.Euler(0f, yaw, 0f);
            var targetExtent = Extent(target, dir);
            var depthHalf = piece.half.z;
            var origin = target.obbCentre;
            origin.y = 0f;
            var pos = origin + dir * (targetExtent + depthHalf + .03f);
            var stand = Make(piece, Rest.Upright, upright, pos, 0f);
            // Pivot: the stand's bottom edge on the target's side.
            var pivot = stand.obbCentre - dir * depthHalf;
            pivot.y = 0f;
            var axis = Vector3.Cross(Vector3.up, -dir).normalized;
            float contact = -1f;
            for (var deg = 6f; deg <= 58f; deg += 2f)
            {
                var q = Quaternion.AngleAxis(deg, axis);
                var trial = new Placed { piece = piece, rest = Rest.EdgeLean, rotation = q * stand.rotation, position = pivot + q * (stand.position - pivot) };
                if (OverlapFraction(trial, target) > .004f) { contact = deg; break; }
            }
            if (contact < 0f) continue;
            var angle = contact + rng.Range(2f, 6f);
            if (angle < 30f || angle > 52f) continue;
            var rot = Quaternion.AngleAxis(angle, axis);
            var lean = new Placed { piece = piece, rest = Rest.EdgeLean, rotation = rot * stand.rotation, position = pivot + rot * (stand.position - pivot) };
            // Keep the hinge edge on the floor.
            Ground(lean, 0f);
            if (TryCommit(plan, lean)) return true;
        }
        return false;
    }

    /// <summary>Rest a piece on top of a committed piece (or the floor).</summary>
    static bool TryStack(Plan plan, List<Piece> pool, Rng rng, Rest? want, bool highest = false)
    {
        if (pool.Count == 0) return false;
        for (var attempt = 0; attempt < 12; attempt++)
        {
            var piece = rng.Pick(pool);
            var rest = want.HasValue && piece.Allows(want.Value) ? want.Value : PickRest(piece, rng);
            var yaw = rng.Pick(new[] { 0f, 90f, 180f, 270f }) + rng.Range(-20f, 20f);
            Placed support = null;
            if (plan.placed.Count > 0)
            {
                support = highest ? Highest(plan) : plan.placed[rng.Range(0, plan.placed.Count)];
                if (support.rest == Rest.EdgeLean || (support.rest == Rest.Inverted && (support.piece.cls == "Seat" || support.piece.cls == "Table"))) support = null;
            }
            Vector3 pos;
            float y;
            if (support != null)
            {
                var c = support.obbCentre;
                var spread = Mathf.Min(Extent(support, Vector3.right), Extent(support, Vector3.forward)) * .5f;
                pos = new Vector3(c.x + rng.Range(-spread, spread), 0f, c.z + rng.Range(-spread, spread));
                y = TopAt(plan, pos);
            }
            else
            {
                var r = rng.Range(0f, .55f) * plan.radius;
                var a = rng.Range(0f, Mathf.PI * 2f);
                pos = new Vector3(Mathf.Cos(a) * r, 0f, Mathf.Sin(a) * r);
                y = TopAt(plan, pos);
            }
            var placed = Make(piece, rest, Quaternion.Euler(0f, yaw, 0f), pos, y);
            if (TryCommit(plan, placed)) return true;
        }
        return false;
    }

    /// <summary>Paste exact copies of one piece with a rigid offset; they interpenetrate.</summary>
    static bool TryCopyPasteRun(Plan plan, List<Piece> pool, Rng rng, int copies)
    {
        if (pool.Count == 0) return false;
        Placed source = null;
        for (var i = plan.placed.Count - 1; i >= 0 && source == null; i--)
            if (pool.Contains(plan.placed[i].piece) && plan.placed[i].rest != Rest.EdgeLean) source = plan.placed[i];
        if (source == null)
        {
            if (!TryStack(plan, pool, rng, null)) return false;
            source = plan.placed[plan.placed.Count - 1];
        }
        var group = source.copyGroup >= 0 ? source.copyGroup : (source.copyGroup = plan.nextCopyGroup++);
        var localAxis = rng.Pick(new[] { Vector3.right, Vector3.forward });
        var size = Vector3.Scale(source.piece.info.Size, localAxis).magnitude;
        var step = size * rng.Range(.15f, .45f);
        var yawStep = rng.Pick(new[] { 3f, 7f, 15f, 90f });
        var prev = source;
        var any = false;
        for (var i = 0; i < copies; i++)
        {
            var dir = prev.rotation * localAxis;
            dir.y = 0f;
            var pos = prev.position + dir.normalized * step;
            var rot = Quaternion.Euler(0f, yawStep, 0f) * prev.rotation;
            var copy = new Placed { piece = source.piece, rest = source.rest, rotation = rot, position = pos, copyGroup = group };
            // Copies on the floor stay on it; raised copies settle on whatever is below.
            Ground(copy, prev.position.y < .01f ? 0f : TopAt(plan, pos, copy));
            if (!TryCommit(plan, copy, ignoreOverlapWithGroup: true)) break;
            prev = copy;
            any = true;
        }
        return any;
    }

    static bool TrySpike(Plan plan, List<Piece> pool, Rng rng)
    {
        if (pool.Count == 0 || plan.placed.Count == 0) return false;
        for (var attempt = 0; attempt < 8; attempt++)
        {
            var piece = rng.Pick(pool);
            var support = Highest(plan);
            var c = support.obbCentre;
            var pos = new Vector3(c.x + rng.Range(-.15f, .15f), 0f, c.z + rng.Range(-.15f, .15f));
            var tilt = Quaternion.Euler(rng.Range(-8f, 8f), rng.Range(0f, 360f), rng.Range(-8f, 8f));
            var placed = Make(piece, Rest.Upright, tilt, pos, TopAt(plan, pos));
            if (TryCommit(plan, placed)) return true;
        }
        return false;
    }

    static bool TrySatellite(Plan plan, List<Piece> pool, Rng rng)
    {
        if (pool.Count == 0) return false;
        for (var attempt = 0; attempt < 6; attempt++)
        {
            var piece = rng.Pick(pool);
            var r = rng.Range(.7f, .95f) * plan.radius;
            var a = rng.Range(0f, Mathf.PI * 2f);
            var rest = piece.Allows(Rest.Side) && rng.Chance(.3f) ? Rest.Side : Rest.Upright;
            var placed = Make(piece, rest, Quaternion.Euler(0f, rng.Range(0f, 360f), 0f), new Vector3(Mathf.Cos(a) * r, 0f, Mathf.Sin(a) * r), 0f);
            if (TryCommit(plan, placed)) return true;
        }
        return false;
    }

    // ================================================================ geometry

    static Rest PickRest(Piece piece, Rng rng)
    {
        var options = new List<Rest>();
        foreach (var s in piece.states) if (s != Rest.EdgeLean) options.Add(s);
        if (options.Count == 0) return Rest.Upright;
        // Upright is the most common reading; the rest are deliberate.
        return rng.Chance(.4f) && options.Contains(Rest.Upright) ? Rest.Upright : rng.Pick(options);
    }

    static Quaternion RestRotation(Rest rest, Rng rng = null)
    {
        switch (rest)
        {
            case Rest.Back: return Quaternion.Euler(-90f, 0f, 0f);      // back face down, front up
            case Rest.Front: return Quaternion.Euler(90f, 0f, 0f);
            case Rest.Side: return Quaternion.Euler(0f, 0f, 90f);
            case Rest.Inverted: return Quaternion.Euler(180f, 0f, 0f);
            default: return Quaternion.identity;
        }
    }

    static Placed Make(Piece piece, Rest rest, Quaternion yaw, Vector3 position, float floorY)
    {
        var placed = new Placed { piece = piece, rest = rest, rotation = yaw * RestRotation(rest), position = position };
        Ground(placed, floorY);
        return placed;
    }

    /// <summary>Move vertically so the lowest corner sits at y.</summary>
    static void Ground(Placed p, float y)
    {
        p.Corners(CornersA);
        var min = float.MaxValue;
        foreach (var c in CornersA) min = Mathf.Min(min, c.y);
        p.position += Vector3.up * (y - min);
    }

    static float Top(Placed p)
    {
        p.Corners(CornersA);
        var max = float.MinValue;
        foreach (var c in CornersA) max = Mathf.Max(max, c.y);
        return max;
    }

    static float Extent(Placed p, Vector3 dir)
    {
        var h = p.obbHalf;
        var r = p.rotation;
        return Mathf.Abs(Vector3.Dot(r * Vector3.right, dir)) * h.x + Mathf.Abs(Vector3.Dot(r * Vector3.up, dir)) * h.y + Mathf.Abs(Vector3.Dot(r * Vector3.forward, dir)) * h.z;
    }

    static Placed Highest(Plan plan)
    {
        Placed best = plan.placed[0];
        var bestTop = Top(best);
        foreach (var p in plan.placed)
        {
            if (p.rest == Rest.EdgeLean) continue;
            var t = Top(p);
            if (t > bestTop) { best = p; bestTop = t; }
        }
        return best;
    }

    /// <summary>Height of the highest committed top surface under (x, z).</summary>
    static float TopAt(Plan plan, Vector3 xz, Placed ignore = null)
    {
        var y = 0f;
        foreach (var p in plan.placed)
        {
            if (p == ignore || p.rest == Rest.EdgeLean) continue;
            var probe = new Vector3(xz.x, p.obbCentre.y, xz.z);
            if (!p.Contains(probe, .02f)) continue;
            y = Mathf.Max(y, Top(p));
        }
        return y;
    }

    /// <summary>Fraction of a's box (4x4x4 samples) that lies inside b's box.</summary>
    static float OverlapFraction(Placed a, Placed b)
    {
        // Cheap reject on bounding spheres.
        if ((a.obbCentre - b.obbCentre).magnitude > a.obbHalf.magnitude + b.obbHalf.magnitude) return 0f;
        var inside = 0;
        var h = a.obbHalf;
        for (var i = 0; i < 4; i++)
            for (var j = 0; j < 4; j++)
                for (var k = 0; k < 4; k++)
                {
                    var local = new Vector3((i + .5f) / 4f * 2f - 1f, (j + .5f) / 4f * 2f - 1f, (k + .5f) / 4f * 2f - 1f);
                    var p = a.obbCentre + a.rotation * Vector3.Scale(h, local);
                    if (b.Contains(p)) inside++;
                }
        return inside / 64f;
    }

    static bool TryCommit(Plan plan, Placed p, bool ignoreOverlapWithGroup = false)
    {
        p.Corners(CornersA);
        foreach (var c in CornersA)
        {
            if (new Vector2(c.x, c.z).magnitude > plan.radius) return false;
            if (c.y > plan.hMax) return false;
            if (c.y < -.02f) return false;
        }
        var own = 0f;
        var added = 0f;
        foreach (var q in plan.placed)
        {
            var f = OverlapFraction(p, q);
            if (f <= 0f) continue;
            var sameGroup = p.copyGroup >= 0 && p.copyGroup == q.copyGroup;
            if (f > .8f) return false;                                  // never swallow a piece
            if (sameGroup && ignoreOverlapWithGroup) { if (f > .45f) return false; continue; }
            if (AlmostCoplanar(p, q)) return false;                     // z-fighting guard
            own += f;
            added += f * p.piece.Volume;
        }
        if (own > p.piece.tolerance) return false;
        var total = plan.totalVolume + p.piece.Volume;
        if (plan.overlapVolume + added > GlobalOverlapBudget * total) return false;
        plan.placed.Add(p);
        plan.totalVolume = total;
        plan.overlapVolume += added;
        return true;
    }

    /// <summary>Parallel faces closer than 3 mm with overlapping projections flicker; reject them.</summary>
    static bool AlmostCoplanar(Placed a, Placed b)
    {
        var axesA = new[] { a.rotation * Vector3.right, a.rotation * Vector3.up, a.rotation * Vector3.forward };
        var axesB = new[] { b.rotation * Vector3.right, b.rotation * Vector3.up, b.rotation * Vector3.forward };
        var ha = new[] { a.obbHalf.x, a.obbHalf.y, a.obbHalf.z };
        var hb = new[] { b.obbHalf.x, b.obbHalf.y, b.obbHalf.z };
        for (var i = 0; i < 3; i++)
            for (var j = 0; j < 3; j++)
            {
                var d = Vector3.Dot(axesA[i], axesB[j]);
                if (Mathf.Abs(d) < .9994f) continue; // > 2 degrees apart
                var n = axesA[i];
                var ca = Vector3.Dot(a.obbCentre, n);
                var cb = Vector3.Dot(b.obbCentre, n);
                for (var sa = -1; sa <= 1; sa += 2)
                    for (var sb = -1; sb <= 1; sb += 2)
                        if (Mathf.Abs((ca + sa * ha[i]) - (cb + sb * hb[j])) < .003f) return true;
            }
        return false;
    }
}
