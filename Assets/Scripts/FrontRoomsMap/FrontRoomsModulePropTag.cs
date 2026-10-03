using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// On a prop that a room module placed: which module and which of its props,
/// and where the module's south-west corner is (chunk-local metres), so the
/// Level Designer can map edits made in the Scene view back to the module.
/// Added only when the map is asked to (FrontRoomsMapWorld.TagModuleProps).
/// </summary>
public sealed class FrontRoomsModulePropTag : MonoBehaviour
{
    // The stamped module data (a copy the map works on), not serialized.
    [System.NonSerialized] public RoomModuleData module;
    public int index;
    public Vector3 roomOrigin;
}
