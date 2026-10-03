using System.IO;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Import settings for the Blender prop kit (Assets/Resources/Props/Models):
/// metres at unit scale, imported normals with MikkTSpace tangents, no
/// cameras/lights/animation, and each kit slot ("Prop_WoodCherry") remapped
/// to the project material Resources/Surfaces/&lt;slot&gt;.mat when it exists.
/// The slot list comes from the asset's JSON sidecar.
/// </summary>
sealed class FrontRoomsKitImporter : AssetPostprocessor
{
    const string Folder = "Assets/Resources/Props/Models/";
    const string CreatureFolder = "Assets/Resources/Creatures/";
    const string SurfaceFolder = "Assets/Resources/Surfaces/";

    void OnPreprocessModel()
    {
        if (!assetPath.StartsWith(Folder) && !assetPath.StartsWith(CreatureFolder)) return;
        var importer = (ModelImporter)assetImporter;
        importer.globalScale = 1f;
        importer.useFileScale = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.importVisibility = false;
        importer.importBlendShapes = false;
        importer.animationType = ModelImporterAnimationType.None;
        importer.importAnimation = false;
        importer.importNormals = ModelImporterNormals.Import;
        importer.importTangents = ModelImporterTangents.CalculateMikk;
        importer.meshCompression = ModelImporterMeshCompression.Off;
        importer.isReadable = false;
        importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;

        var sidecar = Path.ChangeExtension(assetPath, ".json");
        if (!File.Exists(sidecar)) return;
        var info = JsonUtility.FromJson<FrontRoomsKitLibrary.Info>(File.ReadAllText(sidecar));
        if (info?.slots == null) return;
        foreach (var slot in info.slots)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(SurfaceFolder + slot + ".mat");
            var id = new AssetImporter.SourceAssetIdentifier(typeof(Material), slot);
            if (material != null) importer.AddRemap(id, material);
            else importer.RemoveRemap(id);
        }
    }

    /// <summary>
    /// Kit FBX files with _LOD0/_LOD1 children get a LODGroup from Unity;
    /// set the switch heights from the research spec: LOD1 below 10 % of the
    /// screen, culled below 2 % (large pieces) or 3 % (desk props).
    /// </summary>
    /// <summary>A re-exported kit model or sidecar (or a surface material) invalidates
    /// FrontRoomsKitLibrary's caches in the editor.</summary>
    static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
    {
        foreach (var list in new[] { imported, deleted, moved, movedFrom })
            foreach (var path in list)
                if (path.StartsWith(Folder) || path.StartsWith("Assets/Resources/Surfaces/"))
                {
                    FrontRoomsKitLibrary.ClearCache();
                    return;
                }
    }

    void OnPostprocessModel(GameObject root)
    {
        if (!assetPath.StartsWith(Folder) && !assetPath.StartsWith(CreatureFolder)) return;
        var group = root.GetComponent<LODGroup>();
        if (group == null) return;
        var lods = group.GetLODs();
        if (lods.Length < 2) return;
        var size = group.size;
        lods[0].screenRelativeTransitionHeight = .10f;
        lods[1].screenRelativeTransitionHeight = size < .6f ? .03f : .02f;
        group.SetLODs(lods);
        group.fadeMode = LODFadeMode.None;
    }
}
