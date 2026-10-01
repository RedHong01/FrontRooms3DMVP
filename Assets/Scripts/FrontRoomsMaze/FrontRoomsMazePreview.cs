using System.Collections.Generic;
using UnityEngine;
using FrontRooms.Maze;

/// <summary>
/// Low-cost editor preview for the generated Level 0 labyrinth. It is an
/// authored, inspectable scene object; gameplay streaming can consume the same
/// FrontRoomsMazeSpec later without changing the seed or route constraints.
/// </summary>
[ExecuteAlways]
public sealed class FrontRoomsMazePreview : MonoBehaviour
{
    public int seed = 20261001;
    [Range(3, 31)] public int width = 9;
    [Range(3, 31)] public int height = 7;
    [Range(.05f, .35f)] public float loopRatio = .18f;
    public float cellSize = 7.5f;
    public float roomHeight = 3.2f;
    public bool buildCeiling = true;
    public Vector3 previewOffset = new Vector3(78f, 0f, 0f);

    public FrontRoomsMazeSpec spec;
    public Material wallMaterial;
    public Material floorMaterial;
    public Material ceilingMaterial;
    public Material trimMaterial;
    public Material threatMaterial;
    public Material landmarkMaterial;

    public void Rebuild()
    {
        spec = FrontRoomsMazeGenerator.Generate(seed, width, height, loopRatio);
        ClearChildren();
        EnsureMaterials();
        transform.localPosition = previewOffset;
        gameObject.name = "EDITOR_PREVIEW / Level 0 maze / seed " + seed;

        var open = new HashSet<EdgeKey>();
        foreach (var c in spec.connections) open.Add(new EdgeKey(c.from, c.to));
        for (var y = 0; y < spec.height; y++)
            for (var x = 0; x < spec.width; x++)
            {
                var id = y * spec.width + x;
                var cell = spec.cells[id];
                var center = new Vector3(x * cellSize, 0f, y * cellSize);
                var floorMat = MaterialFor(cell.type, floorMaterial);
                Box("Room " + id.ToString("00") + " / floor / " + cell.type, center + Vector3.down * .10f, new Vector3(cellSize, .20f, cellSize), floorMat);
                if (buildCeiling) Box("Room " + id.ToString("00") + " / ceiling", center + Vector3.up * (roomHeight + .10f), new Vector3(cellSize, .20f, cellSize), ceilingMaterial);
                if (x == 0 || !open.Contains(new EdgeKey(id, id - 1))) Wall("west", center + Vector3.left * cellSize * .5f, new Vector3(.20f, roomHeight, cellSize + .2f));
                if (x == spec.width - 1 || !open.Contains(new EdgeKey(id, id + 1))) Wall("east", center + Vector3.right * cellSize * .5f, new Vector3(.20f, roomHeight, cellSize + .2f));
                if (y == 0 || !open.Contains(new EdgeKey(id, id - spec.width))) Wall("south", center + Vector3.back * cellSize * .5f, new Vector3(cellSize + .2f, roomHeight, .20f));
                if (y == spec.height - 1 || !open.Contains(new EdgeKey(id, id + spec.width))) Wall("north", center + Vector3.forward * cellSize * .5f, new Vector3(cellSize + .2f, roomHeight, .20f));
                if (cell.type == MazeRoomType.Threat) Box("Threat marker", center + Vector3.up * .025f, new Vector3(cellSize * .22f, .05f, cellSize * .22f), threatMaterial);
                if (cell.type == MazeRoomType.Landmark) Box("Landmark marker", center + Vector3.up * .04f, new Vector3(cellSize * .32f, .08f, cellSize * .32f), landmarkMaterial);
            }
        CreateLightRig();
    }

    struct EdgeKey
    {
        public int a, b;
        public EdgeKey(int first, int second) { a = Mathf.Min(first, second); b = Mathf.Max(first, second); }
        public override int GetHashCode() { return (a * 397) ^ b; }
        public override bool Equals(object o) { return o is EdgeKey && ((EdgeKey)o).a == a && ((EdgeKey)o).b == b; }
    }

    void EnsureMaterials()
    {
        if (wallMaterial == null) wallMaterial = Make("Maze / aged yellow wall", new Color(.57f, .50f, .30f));
        if (floorMaterial == null) floorMaterial = Make("Maze / worn carpet", new Color(.22f, .19f, .13f));
        if (ceilingMaterial == null) ceilingMaterial = Make("Maze / ceiling tile", new Color(.29f, .28f, .24f));
        if (trimMaterial == null) trimMaterial = Make("Maze / dark trim", new Color(.18f, .15f, .11f));
        if (threatMaterial == null) threatMaterial = Make("Maze / threat marker", new Color(.52f, .09f, .07f));
        if (landmarkMaterial == null) landmarkMaterial = Make("Maze / landmark marker", new Color(.08f, .38f, .35f));
    }

    Material MaterialFor(MazeRoomType type, Material fallback)
    {
        return type == MazeRoomType.Threat ? threatMaterial : type == MazeRoomType.Landmark ? landmarkMaterial : fallback;
    }

    Material Make(string name, Color color)
    {
        var shader = Shader.Find("Standard") ?? Shader.Find("UI/Default");
        var material = new Material(shader) { name = name, color = color };
        material.SetFloat("_Glossiness", .08f);
        return material;
    }

    void Wall(string suffix, Vector3 localPosition, Vector3 scale)
    {
        Box("Wall / " + suffix, localPosition + Vector3.up * (roomHeight * .5f), scale, wallMaterial);
    }

    void CreateLightRig()
    {
        for (var y = 1; y < height; y += 2)
            for (var x = 1; x < width; x += 2)
            {
                var light = new GameObject("Maze fluorescent / " + x + " / " + y);
                light.transform.SetParent(transform, false);
                light.transform.localPosition = new Vector3(x * cellSize, roomHeight - .22f, y * cellSize);
                var point = light.AddComponent<Light>();
                point.type = LightType.Point; point.range = cellSize * 1.35f; point.intensity = 1.35f; point.color = new Color(1f, .90f, .68f);
                point.shadows = LightShadows.None;
            }
    }

    GameObject Box(string name, Vector3 localPosition, Vector3 scale, Material material)
    {
        var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = name; box.transform.SetParent(transform, false); box.transform.localPosition = localPosition; box.transform.localScale = scale;
        var renderer = box.GetComponent<Renderer>(); if (renderer != null) renderer.sharedMaterial = material;
        var collider = box.GetComponent<Collider>(); if (collider != null) Remove(collider);
        return box;
    }

    void ClearChildren()
    {
        for (var i = transform.childCount - 1; i >= 0; i--) Remove(transform.GetChild(i).gameObject);
    }

    static void Remove(Object target)
    {
        if (Application.isPlaying) Destroy(target); else DestroyImmediate(target);
    }

    void OnDrawGizmosSelected()
    {
        if (spec == null) return;
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireCube(transform.position + new Vector3((spec.width - 1) * cellSize * .5f, roomHeight * .5f, (spec.height - 1) * cellSize * .5f), new Vector3(spec.width * cellSize, roomHeight, spec.height * cellSize));
    }
}
