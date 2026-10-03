using FMODUnity;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Points FMOD for Unity at the FrontRooms FMOD Studio project and loads its
/// banks. The project lives outside Assets (Frontrooms3D/FMOD/FrontRooms);
/// banks are built there by fmodstudiocl and copied to StreamingAssets/FMOD
/// by FMOD for Unity on play and build.
///
/// Batch: Unity -batchmode -projectPath &lt;project&gt; -executeMethod FrontRoomsFmodSetup.RunBatch -quit
/// </summary>
public static class FrontRoomsFmodSetup
{
    const string StudioProject = "FMOD/FrontRooms/FrontRooms.fspro";

    [MenuItem("FrontRooms/Audio/Configure FMOD (FrontRooms project)")]
    public static void Configure()
    {
        // Fresh installs ship the editor's logging library (fmodstudioL) in a staging
        // folder; the setup wizard normally moves it, which batch mode never shows.
        StagingSystem.Startup();
        AssetDatabase.Refresh();

        var settings = Settings.Instance;
        settings.HasSourceProject = true;
        settings.SourceProjectPath = StudioProject;
        settings.ImportType = ImportType.StreamingAssets;
        settings.TargetSubFolder = "FMOD";
        settings.BankLoadType = BankLoadType.All;
        settings.AutomaticEventLoading = true;
        settings.AutomaticSampleLoading = false;
        EditorUtility.SetDirty(settings);
        AssetDatabase.SaveAssets();
        EventManager.RefreshBanks();
        Debug.Log("[FrontRoomsAudio] FMOD for Unity now reads " + StudioProject);
    }

    public static void RunBatch()
    {
        Configure();
        EditorApplication.Exit(0);
    }
}
