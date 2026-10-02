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
        if (!go.TryGetComponent<Volume>(out var volume)) volume = go.AddComponent<Volume>();
        volume.isGlobal = true;
        volume.priority = 0f;
        volume.sharedProfile = profile;
        return volume;
    }

    /// <summary>
    /// A local grade for one zone (e.g. "Office" → Resources/Rendering/
    /// FrontRoomsPost_Office): a trigger box over <paramref name="localBounds"/>
    /// in the parent's space that blends in over <paramref name="blendDistance"/>
    /// metres as the camera walks in. Overrides only what the zone changes
    /// (white balance, saturation, contrast, grain); the global film look
    /// supplies the rest. Destroyed with its parent (a map chunk).
    /// </summary>
    public static Volume EnsureZoneVolume(Transform parent, string zone, Bounds localBounds, float blendDistance = 2.5f)
    {
        if (parent == null || string.IsNullOrEmpty(zone)) return null;
        var profile = Resources.Load<VolumeProfile>("Rendering/FrontRoomsPost_" + zone);
        if (profile == null) return null;
        var name = "Post / zone " + zone;
        var existing = parent.Find(name);
        var go = existing != null ? existing.gameObject : new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = Vector3.zero;
        go.transform.localRotation = Quaternion.identity;
        if (!go.TryGetComponent<BoxCollider>(out var box)) box = go.AddComponent<BoxCollider>();
        box.isTrigger = true;
        box.center = localBounds.center;
        box.size = localBounds.size;
        if (!go.TryGetComponent<Volume>(out var volume)) volume = go.AddComponent<Volume>();
        volume.isGlobal = false;
        volume.priority = 1f;
        volume.blendDistance = blendDistance;
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
