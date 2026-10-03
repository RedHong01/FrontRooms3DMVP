using System;
using System.Collections.Generic;
using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// A room module as an asset (Assets/Levels/Modules): what a level designer
/// authors in the Level Designer. The data itself is RoomModuleData, so the
/// stamp and its checks run without Unity; see LEVEL_DESIGNER.md.
/// </summary>
[CreateAssetMenu(menuName = "FrontRooms/Room module", fileName = "RoomModule")]
public sealed class FrontRoomsRoomModule : ScriptableObject
{
    public const string Folder = "Assets/Levels/Modules";

    [TextArea(2, 5)] public string notes;
    public RoomModuleData data = new RoomModuleData();

    /// <summary>Raised after any edit (inspector, plan view, undo), so the preview rebuilds.</summary>
    public static event Action<FrontRoomsRoomModule> Changed;

    public static void NotifyChanged(FrontRoomsRoomModule module) => Changed?.Invoke(module);

    void OnValidate()
    {
        if (data == null) data = new RoomModuleData();
        data.Normalize();
        Changed?.Invoke(this);
    }

    /// <summary>Errors and warnings for the designer, using the kit library's real footprints.</summary>
    public void Validate(List<string> errors, List<string> warnings) => data.Validate(errors, warnings, FrontRoomsMapWorld.KitFootprint);
}
