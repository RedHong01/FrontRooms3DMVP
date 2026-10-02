using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// The film look as a global URP volume (Resources/Rendering/FrontRoomsPost):
/// ACES tonemapping, halation on the tubes, a green-yellow white balance,
/// lifted blacks for the CRT haze, fine grain and a slight wide-lens falloff.
/// The profile is an asset, so every value is tuned in the Inspector.
/// </summary>
public static class FrontRoomsPostStack
{
    const string VolumeName = "Post / FrontRooms film look";

    public static Volume Ensure(Transform parent)
    {
        var profile = Resources.Load<VolumeProfile>("Rendering/FrontRoomsPost");
        if (profile == null)
        {
            Debug.LogWarning("[FrontRooms3D] Post profile is missing. Run FrontRooms → Rendering → Set up URP, post and surfaces.");
            return null;
        }
        var existing = parent == null ? GameObject.Find(VolumeName) : parent.Find(VolumeName)?.gameObject;
        var go = existing != null ? existing : new GameObject(VolumeName);
        if (parent != null && go.transform.parent != parent) go.transform.SetParent(parent, false);
        var volume = go.GetComponent<Volume>() ?? go.AddComponent<Volume>();
        volume.isGlobal = true;
        volume.priority = 0f;
        volume.sharedProfile = profile;
        return volume;
    }

    public static void ConfigureCamera(Camera camera)
    {
        if (camera == null) return;
        camera.allowHDR = true;
        camera.allowMSAA = true;
        var data = camera.GetUniversalAdditionalCameraData();
        data.renderPostProcessing = true;
        data.renderShadows = true;
        data.antialiasing = AntialiasingMode.None; // the pipeline's 4x MSAA keeps the grain sharp
        data.dithering = true;
    }
}
