using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// Renders the edit-mode profile preview (one room per profile, lights on)
/// through the full URP + post stack and saves 1920x1080 PNGs to
/// Verification/lookdev. Used to judge materials and light levels without a
/// Play session. Batch: -executeMethod FrontRoomsLookdevCapture.RunBatch
/// (needs graphics, so do not pass -nographics).
/// </summary>
public static class FrontRoomsLookdevCapture
{
    const string ScenePath = "Assets/Scenes/FrontRooms3D.unity";

    [MenuItem("FrontRooms/Rendering/Capture look-dev frames")]
    public static void Capture()
    {
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (scene.path != ScenePath)
        {
            if (!Application.isBatchMode)
            {
                Debug.LogWarning("[FrontRoomsLookdev] Open " + ScenePath + " first.");
                return;
            }
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }
        var game = Object.FindFirstObjectByType<FrontRooms3DGame>();
        if (game == null) { Debug.LogError("[FrontRoomsLookdev] No FrontRooms3DGame in the scene."); return; }
        // Rebuild the preview so it reflects the current surface assets.
        game.enabled = false;
        game.enabled = true;
        // The serialized Relay stands in the preview rooms in edit mode.
        var hunter = game.transform.Find("Hunter");
        var hunterWasActive = hunter != null && hunter.gameObject.activeSelf;
        if (hunter != null) hunter.gameObject.SetActive(false);
        var volume = FrontRoomsPostStack.Ensure(null);
        if (volume != null) volume.gameObject.hideFlags = HideFlags.DontSave;

        var outDir = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "lookdev");
        Directory.CreateDirectory(outDir);
        var cameraObject = new GameObject("LOOKDEV / camera") { hideFlags = HideFlags.DontSave };
        var camera = cameraObject.AddComponent<Camera>();
        camera.fieldOfView = 76f;
        camera.nearClipPlane = .06f;
        camera.farClipPlane = 80f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.13f, .13f, .11f);
        FrontRoomsPostStack.ConfigureCamera(camera);
        var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
        camera.targetTexture = rt;

        var profiles = (RoomRule[])System.Enum.GetValues(typeof(RoomRule));
        var root = game.transform;
        for (var i = 0; i < profiles.Length; i++)
        {
            var z = i * FrontRoomsRoomStream.RoomLength;
            Shot(camera, rt, root.TransformPoint(new Vector3(0f, 1.62f, z + 1.6f)), Quaternion.Euler(4f, 0f, 0f), Path.Combine(outDir, i + "_" + profiles[i] + "_forward.png"));
            Shot(camera, rt, root.TransformPoint(new Vector3(3.6f, 1.62f, z + 10.4f)), Quaternion.Euler(10f, 205f, 0f), Path.Combine(outDir, i + "_" + profiles[i] + "_back.png"));
        }
        camera.targetTexture = null;
        Object.DestroyImmediate(cameraObject);
        rt.Release();
        if (hunter != null) hunter.gameObject.SetActive(hunterWasActive);
        Debug.Log("[FrontRoomsLookdev] Wrote " + profiles.Length * 2 + " frames to " + outDir);
    }

    static void Shot(Camera camera, RenderTexture rt, Vector3 position, Quaternion rotation, string path)
    {
        camera.transform.SetPositionAndRotation(position, rotation);
        // Two renders: the first warms up temporal post effects and shadows.
        camera.Render();
        camera.Render();
        var previous = RenderTexture.active;
        RenderTexture.active = rt;
        var image = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        image.Apply();
        RenderTexture.active = previous;
        File.WriteAllBytes(path, image.EncodeToPNG());
        Object.DestroyImmediate(image);
    }

    public static void RunBatch() => Capture();
}
