using System.IO;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Imports packed wallpaper prints under Assets/Resources/Print as Texture2DArrays.
/// Columns and rows come from the <name>.print.json that Tools/print/print_tool.py
/// writes next to the sheet. A print is ink data, not colour: linear, mipmapped,
/// repeat-wrapped, trilinear with aniso 16, set on the array itself because WebGL2
/// couples samplers to textures. Kept apart from Resources/Surfaces, whose rule caps
/// textures at 4096 px.
/// </summary>
sealed class FrontRoomsPrintImporter : AssetPostprocessor
{
    const string Folder = "Assets/Resources/Print/";

    [System.Serializable]
    sealed class Meta
    {
        public int columns = 1;
        public int rows = 1;
    }

    void OnPreprocessTexture()
    {
        if (!assetPath.StartsWith(Folder) || !assetPath.EndsWith(".png")) return;
        string json = assetPath.Substring(0, assetPath.Length - 4) + ".print.json";
        if (!File.Exists(json))
        {
            Debug.LogWarning($"[Print] {assetPath} has no {Path.GetFileName(json)}; pack it with Tools/print/print_tool.py.");
            return;
        }
        var meta = JsonUtility.FromJson<Meta>(File.ReadAllText(json));
        var ti = (TextureImporter)assetImporter;
        ti.textureType = TextureImporterType.Default;
        ti.textureShape = TextureImporterShape.Texture2DArray;
        var s = new TextureImporterSettings();
        ti.ReadTextureSettings(s);
        s.flipbookColumns = Mathf.Max(1, meta.columns);
        s.flipbookRows = Mathf.Max(1, meta.rows);
        ti.SetTextureSettings(s);
        ti.sRGBTexture = false;
        ti.alphaSource = TextureImporterAlphaSource.None;
        ti.mipmapEnabled = true;
        ti.streamingMipmaps = false;
        ti.npotScale = TextureImporterNPOTScale.None;
        ti.wrapMode = TextureWrapMode.Repeat;
        ti.filterMode = FilterMode.Trilinear;
        ti.anisoLevel = 16;
        ti.maxTextureSize = 8192;
        ti.textureCompression = TextureImporterCompression.CompressedHQ;
    }
}
