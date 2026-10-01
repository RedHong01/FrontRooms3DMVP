using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Small, shared film-surface mesh kit used by the streamed rooms. It keeps the
/// gameplay's analytical collision model intact while replacing Unity's sharp
/// default cubes with a low-poly chamfered box. The mesh is cached by dimensions
/// so the five-room pool does not allocate a new mesh for every prop instance.
/// UVs are expressed in metres and projected from the thinnest axis, which keeps
/// wall paper, floor weave, and furniture surfaces at a stable texel density.
/// </summary>
public static class FrontRoomsFilmMesh
{
    static readonly Dictionary<string, Mesh> Cache = new Dictionary<string, Mesh>();

    public static Mesh GetBeveledBox(Vector3 size, float requestedBevel)
    {
        size.x = Mathf.Max(.01f, size.x);
        size.y = Mathf.Max(.01f, size.y);
        size.z = Mathf.Max(.01f, size.z);
        var minimum = Mathf.Min(size.x, Mathf.Min(size.y, size.z));
        var bevel = Mathf.Clamp(requestedBevel, .0015f, minimum * .32f);
        var key = string.Format("{0:0.000}|{1:0.000}|{2:0.000}|{3:0.000}", size.x, size.y, size.z, bevel);
        if (Cache.TryGetValue(key, out var cached) && cached != null) return cached;

        var mesh = Build(size, bevel);
        mesh.name = "Film beveled box " + key;
        mesh.hideFlags = HideFlags.DontSave;
        Cache[key] = mesh;
        return mesh;
    }

    static Mesh Build(Vector3 size, float bevel)
    {
        var hx = size.x * .5f;
        var hy = size.y * .5f;
        var hz = size.z * .5f;
        var outer = Ring(hx, hy, bevel, hz);
        var inner = Ring(Mathf.Max(.001f, hx - bevel), Mathf.Max(.001f, hy - bevel), Mathf.Max(.0008f, bevel * .45f), Mathf.Max(.0008f, hz - bevel));
        var innerBack = Ring(Mathf.Max(.001f, hx - bevel), Mathf.Max(.001f, hy - bevel), Mathf.Max(.0008f, bevel * .45f), -Mathf.Max(.0008f, hz - bevel));
        var outerBack = Ring(hx, hy, bevel, -hz);
        var vertices = new List<Vector3>(34);
        vertices.AddRange(outer); vertices.AddRange(inner); vertices.AddRange(innerBack); vertices.AddRange(outerBack);
        // Front and back cap centres close the octagonal rings.
        vertices.Add(new Vector3(0f, 0f, hz - bevel));
        vertices.Add(new Vector3(0f, 0f, -hz + bevel));
        var triangles = new List<int>(120);
        var uvs = new List<Vector2>(vertices.Count);
        for (var i = 0; i < vertices.Count; i++) uvs.Add(ProjectUv(vertices[i], size));

        for (var i = 0; i < 8; i++)
        {
            var next = (i + 1) % 8;
            AddQuad(triangles, i, next, 8 + next, 8 + i);
            AddQuad(triangles, 8 + i, 8 + next, 16 + next, 16 + i);
            AddQuad(triangles, 16 + i, 16 + next, 24 + next, 24 + i);
            // Winding is reversed on the back cap.
            triangles.Add(32); triangles.Add(8 + next); triangles.Add(8 + i);
            triangles.Add(33); triangles.Add(24 + i); triangles.Add(24 + next);
        }

        var mesh = new Mesh();
        mesh.indexFormat = vertices.Count > 65535 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
        mesh.SetVertices(vertices);
        mesh.SetTriangles(triangles, 0);
        mesh.SetUVs(0, uvs);
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        try { mesh.RecalculateTangents(); } catch (Exception) { /* older importers may omit tangents */ }
        return mesh;
    }

    static Vector3[] Ring(float hx, float hy, float corner, float z)
    {
        corner = Mathf.Clamp(corner, .0005f, Mathf.Min(hx, hy) * .9f);
        return new[]
        {
            new Vector3(-hx + corner, -hy, z), new Vector3(hx - corner, -hy, z),
            new Vector3(hx, -hy + corner, z), new Vector3(hx, hy - corner, z),
            new Vector3(hx - corner, hy, z), new Vector3(-hx + corner, hy, z),
            new Vector3(-hx, hy - corner, z), new Vector3(-hx, -hy + corner, z),
        };
    }

    static void AddQuad(List<int> triangles, int a, int b, int c, int d)
    {
        triangles.Add(a); triangles.Add(b); triangles.Add(c);
        triangles.Add(a); triangles.Add(c); triangles.Add(d);
    }

    static Vector2 ProjectUv(Vector3 p, Vector3 size)
    {
        // Thin Y is a floor/ceiling slab. Thin X/Z is a wall or trim strip.
        if (size.y <= Mathf.Min(size.x, size.z) * 1.25f) return new Vector2(p.x, p.z);
        if (size.x <= size.z) return new Vector2(p.z, p.y);
        return new Vector2(p.x, p.y);
    }
}
