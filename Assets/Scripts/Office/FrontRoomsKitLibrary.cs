using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Loads the Blender-built prop kit (Tools/Blender/frontrooms_kit) from
/// Resources/Props/Models: one FBX per asset plus a JSON sidecar with its
/// bounds, support surfaces, anchors and collider boxes, all in Unity space.
/// The asset's front faces +Z and it stands on y = 0.
/// Submesh materials are named after kit slots ("Prop_WoodCherry"); the
/// importer remaps them to Resources/Surfaces/&lt;slot&gt;.mat, and Spawn
/// repeats that remap at runtime as a safety net.
/// </summary>
public static class FrontRoomsKitLibrary
{
    public const string ModelFolder = "Props/Models/";

    [Serializable]
    public class Support { public string name; public float[] centre; public float[] size; }

    [Serializable]
    public class BoxDef { public float[] centre; public float[] size; }

    [Serializable]
    public class Anchor { public string name; public float[] pos; }

    /// <summary>How the furniture pile may use an asset (kitlib Kit.pile()).</summary>
    [Serializable]
    public class PileDef
    {
        public string cls;          // Seat Table Case Soft Tall Screen Crate Small
        public int mass;            // 0 light .. 3 heavy
        public string[] states;     // Upright Back Front Side Inverted EdgeLean
        public float tolerance;     // max own-volume fraction inside other pieces
        public string palette;      // domestic70s office90s storage hotel
        public bool topper;
    }

    [Serializable]
    public class Info
    {
        public PileDef pile;
        public string name;
        public float[] boundsMin;
        public float[] boundsMax;
        public Support[] supports;
        public BoxDef[] colliders;
        public Anchor[] anchors;
        public string[] tags;
        public string[] slots;
        public int triangles;
        public int trianglesLod1;
        public string frontAxis;          // "+Z": the asset's front faces local +Z
        public float[] footprintCentre;   // physical footprint (colliders), Unity x/z
        public float[] footprintSize;
        public string placement;          // Floor | Wall | DeskTop | Ceiling
        public float service;             // clear depth needed in front (wall units)
        public float minCeiling;          // ceiling height the piece needs

        public Vector3 Min => V(boundsMin);
        public Vector3 Max => V(boundsMax);
        public Vector3 Size => Max - Min;
        /// <summary>The physical footprint (collider union; cables and overhangs excluded) as an x/z rect.</summary>
        public Rect Footprint => footprintSize != null && footprintSize.Length >= 2 && footprintCentre != null && footprintCentre.Length >= 2
            ? new Rect(footprintCentre[0] - footprintSize[0] * .5f, footprintCentre[1] - footprintSize[1] * .5f, footprintSize[0], footprintSize[1])
            : Rect.MinMaxRect(Min.x, Min.z, Max.x, Max.z);

        /// <summary>Footprint half extents about the origin (x, z).</summary>
        public Vector2 HalfFootprint
        {
            get
            {
                var f = Footprint;
                return new Vector2(Mathf.Max(-f.xMin, f.xMax), Mathf.Max(-f.yMin, f.yMax));
            }
        }

        /// <summary>Physical depth (z) of the footprint.</summary>
        public float Depth => Footprint.height;
        public float Height => Max.y;

        public bool TryAnchor(string anchorName, out Vector3 position)
        {
            if (anchors != null)
                foreach (var a in anchors)
                    if (a != null && a.name == anchorName) { position = V(a.pos); return true; }
            position = Vector3.zero;
            return false;
        }

        public bool TrySupport(string supportName, out Vector3 centre, out Vector2 size)
        {
            if (supports != null)
                foreach (var s in supports)
                    if (s != null && (supportName == null || s.name == supportName)) { centre = V(s.centre); size = new Vector2(s.size[0], s.size[1]); return true; }
            centre = Vector3.zero;
            size = Vector2.zero;
            return false;
        }

        public bool HasTag(string tag) => tags != null && Array.IndexOf(tags, tag) >= 0;
        public bool IsPilePiece => pile != null && !string.IsNullOrEmpty(pile.cls);
    }

    static readonly Dictionary<string, GameObject> Models = new Dictionary<string, GameObject>();
    static readonly Dictionary<string, Info> Infos = new Dictionary<string, Info>();
    static readonly Dictionary<string, Material[]> MaterialSets = new Dictionary<string, Material[]>();
    static readonly HashSet<string> Missing = new HashSet<string>();

    static Vector3 V(float[] a) => a == null || a.Length < 3 ? Vector3.zero : new Vector3(a[0], a[1], a[2]);

    public static bool Has(string assetName) => Model(assetName) != null;

    static List<string> allNames;

    /// <summary>
    /// Forget every cached model, sidecar, name list and material. The editor calls
    /// this when a kit FBX/JSON or a surface material is re-imported, so palettes,
    /// footprints and Validate see the new export without a script reload.
    /// </summary>
    public static void ClearCache()
    {
        Models.Clear();
        Infos.Clear();
        MaterialSets.Clear();
        Missing.Clear();
        ProjectMaterials.Clear();
        allNames = null;
    }

    /// <summary>Every kit asset name in Resources/Props/Models, sorted (stable for seeding).</summary>
    public static IReadOnlyList<string> AllNames()
    {
        if (allNames != null) return allNames;
        allNames = new List<string>();
        foreach (var model in Resources.LoadAll<GameObject>(ModelFolder.TrimEnd('/')))
            if (model != null && !model.name.StartsWith("Kit_AxisProbe") && !IsSyncCopy(model.name) && !allNames.Contains(model.name)) allNames.Add(model.name);
        allNames.Sort(StringComparer.Ordinal);
        return allNames;
    }

    /// <summary>"Kit_CRTMonitor 2": a file-sync conflict copy (the project sits on an
    /// iCloud Desktop), never a kit. Keeps it out of piles and seeded orders.</summary>
    static bool IsSyncCopy(string name)
    {
        var i = name.LastIndexOf(' ');
        if (i < 0 || i == name.Length - 1) return false;
        for (var k = i + 1; k < name.Length; k++)
            if (!char.IsDigit(name[k])) return false;
        return true;
    }

    public static GameObject Model(string assetName)
    {
        if (string.IsNullOrEmpty(assetName)) return null;
        if (Models.TryGetValue(assetName, out var model)) return model;
        model = Resources.Load<GameObject>(ModelFolder + assetName);
        Models[assetName] = model;
        if (model == null && Missing.Add(assetName))
            Debug.LogWarning("[FrontRoomsKit] Missing model Resources/" + ModelFolder + assetName);
        return model;
    }

    public static Info GetInfo(string assetName)
    {
        if (string.IsNullOrEmpty(assetName)) return null;
        if (Infos.TryGetValue(assetName, out var info)) return info;
        var text = Resources.Load<TextAsset>(ModelFolder + assetName);
        info = text != null ? JsonUtility.FromJson<Info>(text.text) : null;
        if (info == null)
        {
            // No sidecar: derive bounds from the mesh so placement still works.
            var model = Model(assetName);
            var filter = model != null ? model.GetComponentInChildren<MeshFilter>() : null;
            if (filter != null && filter.sharedMesh != null)
            {
                var b = filter.sharedMesh.bounds;
                info = new Info { name = assetName, boundsMin = new[] { b.min.x, b.min.y, b.min.z }, boundsMax = new[] { b.max.x, b.max.y, b.max.z } };
            }
        }
        Infos[assetName] = info;
        return info;
    }

    /// <summary>
    /// Instantiate an asset under <paramref name="parent"/> at a local
    /// position and yaw (degrees, 0 = front faces the parent's +Z).
    /// Scale may be non-uniform (the furniture pile uses it sparingly).
    /// </summary>
    public static GameObject Spawn(string assetName, Transform parent, Vector3 localPosition, float yaw, Vector3? scale = null, bool colliders = true, string label = null)
    {
        return Spawn(assetName, parent, localPosition, Quaternion.Euler(0f, yaw, 0f), scale, colliders, label);
    }

    public static GameObject Spawn(string assetName, Transform parent, Vector3 localPosition, Quaternion localRotation, Vector3? scale = null, bool colliders = true, string label = null)
    {
        var model = Model(assetName);
        if (model == null) return null;
        var instance = UnityEngine.Object.Instantiate(model, parent, false);
        instance.name = label ?? assetName;
        instance.transform.localPosition = localPosition;
        instance.transform.localRotation = localRotation;
        instance.transform.localScale = scale ?? Vector3.one;
        ApplyMaterials(assetName, instance);
        if (colliders) AddColliders(assetName, instance);
        return instance;
    }

    static readonly Dictionary<string, Material> ProjectMaterials = new Dictionary<string, Material>();

    /// <summary>
    /// Remap every renderer (LOD0 and LOD1) to the project slot materials and
    /// keep shadows only on props larger than 0.3 m (LEVEL_MODULE_SPEC §8).
    /// </summary>
    static void ApplyMaterials(string assetName, GameObject instance)
    {
        var info = GetInfo(assetName);
        var castShadows = info == null || Mathf.Max(info.Size.x, Mathf.Max(info.Size.y, info.Size.z)) > .3f;
        foreach (var renderer in instance.GetComponentsInChildren<MeshRenderer>(true))
        {
            if (!MaterialSets.TryGetValue(assetName + "/" + renderer.name, out var set))
            {
                var imported = renderer.sharedMaterials;
                set = new Material[imported.Length];
                for (var i = 0; i < imported.Length; i++)
                {
                    var slot = imported[i] != null ? imported[i].name.Replace(" (Instance)", string.Empty) : null;
                    Material project = null;
                    if (slot != null && !ProjectMaterials.TryGetValue(slot, out project))
                        ProjectMaterials[slot] = project = FrontRoomsSurfaces.TryGet(slot);
                    set[i] = project != null ? project : imported[i];
                }
                MaterialSets[assetName + "/" + renderer.name] = set;
            }
            renderer.sharedMaterials = set;
            renderer.shadowCastingMode = castShadows ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = true;
        }
    }

    static void AddColliders(string assetName, GameObject instance)
    {
        var info = GetInfo(assetName);
        if (info?.colliders == null || info.colliders.Length == 0) return;
        foreach (var box in info.colliders)
        {
            var collider = instance.AddComponent<BoxCollider>();
            collider.center = V(box.centre);
            collider.size = V(box.size);
        }
    }
}
