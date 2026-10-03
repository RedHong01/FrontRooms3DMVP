using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// The Level Designer's Scene view tools, while the designer scene is the
/// active scene and its preview shows a module:
/// - a kit dragged from the palette onto the floor becomes a prop there;
/// - a prop moved or turned with the usual tools (or its Transform fields)
///   writes its new x, z and yaw back to the module as it goes; the preview
///   rebuilds once nothing has moved for 0.3 s with no handle held, and the
///   rebuilt prop is selected again;
/// - Delete on selected props removes them from the module;
/// - the room's outline and openings are drawn on the floor.
/// Clicking a prop selects the whole kit, not a mesh inside it, and props
/// stay selected across every rebuild.
///
/// Write-back polls the selected props each editor update rather than
/// listening to Undo.postprocessModifications or ObjectChangeEvents: the
/// preview's objects are DontSave, and polling catches every way of moving
/// them whether or not Undo records it (see LEVEL_DESIGNER.md).
/// </summary>
[InitializeOnLoad]
public static class FrontRoomsDesignerSceneTools
{
    /// <summary>How long the selected props must stay still, with no handle held, before the preview rebuilds.</summary>
    const double Settle = .3;
    /// <summary>A prop this far (m) or this many degrees from its module place has been moved; well above float error 5 km out, well under the 0.05 m snap.</summary>
    const float MovedMetres = .004f, MovedDegrees = .05f;
    static readonly Color OutlineColor = new Color(1f, .6f, .2f, .9f), OpeningColor = new Color(.3f, .9f, .4f, .9f), GhostFill = new Color(.4f, 1f, .5f, .25f);

    static FrontRoomsModulePreview cached;
    // Moved props waiting for the rebuild: when they last moved, and where they were then.
    static bool moved;
    static double lastMove;
    static int lastPose;
    // Props to select after the next rebuild, when an edit knows better than the current selection (a drop, a new prop).
    static int[] reselect;
    static (string kit, Vector2 at)? ghost;
    static GUIStyle label;

    static FrontRoomsDesignerSceneTools()
    {
        SceneView.duringSceneGui += OnSceneGUI;
        EditorApplication.update += Update;
        Selection.selectionChanged += OnSelectionChanged;
        FrontRoomsModulePreview.Rebuilding += OnRebuilding;
        FrontRoomsModulePreview.Rebuilt += OnRebuilt;
    }

    /// <summary>The designer scene's preview, when that scene is the active one and the editor is not playing.</summary>
    public static FrontRoomsModulePreview ScenePreview()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return null;
        var scene = SceneManager.GetActiveScene();
        if (scene.path != FrontRoomsLevelDesigner.ScenePath) return null;
        if (cached == null || cached.gameObject.scene != scene) cached = Object.FindFirstObjectByType<FrontRoomsModulePreview>();
        return cached;
    }

    /// <summary>The designer scene's preview, if it is built around a module.</summary>
    static FrontRoomsModulePreview ActivePreview()
    {
        var preview = ScenePreview();
        return preview != null && preview.module != null && preview.isActiveAndEnabled && preview.World != null ? preview : null;
    }

    // ---------- Tagged props ----------

    /// <summary>
    /// The tag on the prop an object belongs to (a click often picks a mesh
    /// inside the kit), if that prop is in this preview's current map and the
    /// map was built from the module as it is now (same props, same kits).
    /// </summary>
    static FrontRoomsModulePropTag TagOf(GameObject go, FrontRoomsModulePreview preview)
    {
        var tag = go != null ? go.GetComponentInParent<FrontRoomsModulePropTag>(true) : null;
        if (tag == null || preview.module == null || preview.World == null || !tag.transform.IsChildOf(preview.World.transform) || tag.module == null) return null;
        var props = preview.module.data.props;
        return tag.index < props.Length && tag.module.props.Length == props.Length && tag.module.props[tag.index].kit == props[tag.index].kit ? tag : null;
    }

    static List<FrontRoomsModulePropTag> SelectedTags(FrontRoomsModulePreview preview) =>
        Selection.gameObjects.Select(g => TagOf(g, preview)).Where(t => t != null).Distinct().ToList();

    /// <summary>The module prop index of a selected object, or -1 (the window follows the Scene selection with it).</summary>
    public static int SelectedIndex(FrontRoomsModulePreview preview)
    {
        if (preview == null || preview.module == null) return -1;
        var tag = TagOf(Selection.activeGameObject, preview);
        return tag != null ? tag.index : -1;
    }

    /// <summary>Select the props with these indices in the Scene view, now or, if the map is older than the module, after the rebuild that is on its way.</summary>
    public static void SelectProps(FrontRoomsModulePreview preview, int[] indices)
    {
        if (preview == null || preview.World == null || preview.module == null) return;
        var tags = preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true).Where(t => indices.Contains(t.index)).ToList();
        if (tags.Count < indices.Length || tags.Any(t => TagOf(t.gameObject, preview) == null))
        {
            reselect = indices;
            return;
        }
        Selection.objects = tags.Select(t => (Object)t.gameObject).ToArray();
    }

    /// <summary>Let go of this preview's props in the Scene selection (the preview is about to show another module).</summary>
    public static void Deselect(FrontRoomsModulePreview preview)
    {
        reselect = null;
        if (SelectedTags(preview).Count > 0) Selection.objects = new Object[0];
    }

    static void OnSelectionChanged()
    {
        var preview = ActivePreview();
        if (preview == null) return;
        // A click picks the mesh under the mouse: select the kit it belongs to.
        var objects = Selection.objects;
        var changed = false;
        for (var k = 0; k < objects.Length; k++)
        {
            if (!(objects[k] is GameObject go)) continue;
            var tag = TagOf(go, preview);
            if (tag == null || tag.gameObject == go) continue;
            objects[k] = tag.gameObject;
            changed = true;
        }
        if (changed) Selection.objects = objects.Distinct().ToArray();
    }

    static void OnRebuilding(FrontRoomsModulePreview preview)
    {
        if (reselect == null && preview.module != null) reselect = SelectedTags(preview).Select(t => t.index).ToArray();
    }

    static void OnRebuilt(FrontRoomsModulePreview preview)
    {
        var indices = reselect;
        reselect = null;
        moved = false;
        if (indices != null && indices.Length > 0) SelectProps(preview, indices);
    }

    // ---------- Moving props in the Scene ----------

    static void Update()
    {
        var preview = ActivePreview();
        if (preview == null)
        {
            moved = false;
            return;
        }
        var away = false;
        var pose = 17;
        foreach (var tag in SelectedTags(preview))
        {
            away |= WriteBack(preview, tag);
            pose = pose * 31 + tag.transform.position.GetHashCode();
            pose = pose * 31 + tag.transform.rotation.GetHashCode();
        }
        // Only a change since the last poll counts as a move, so a prop the rebuild cannot put back never rebuilds again and again.
        if (pose != lastPose)
        {
            lastPose = pose;
            lastMove = EditorApplication.timeSinceStartup;
            if (away) moved = true;
        }
        // Rebuilding while a handle is held would destroy the object being dragged.
        if (moved && GUIUtility.hotControl == 0 && EditorApplication.timeSinceStartup - lastMove >= Settle) Commit(preview);
    }

    /// <summary>
    /// If a tagged prop is away from where its module prop puts it, write its
    /// new place back to the module asset: x and z (0.05 m snap, inside the
    /// room) for the axes it moved along, yaw (whole degrees) if it turned.
    /// Recorded for Undo on the asset; the preview is not rebuilt here. Height
    /// stays the panel's (a lifted prop drops back at the rebuild). Returns
    /// whether the prop is away from its module place.
    /// </summary>
    public static bool WriteBack(FrontRoomsModulePreview preview, FrontRoomsModulePropTag tag)
    {
        if (TagOf(tag.gameObject, preview) != tag) return false;
        var module = preview.module;
        var m = module.data;
        var p = m.props[tag.index];
        var t = tag.transform;
        var turned = Quaternion.Angle(t.rotation, preview.ModuleToWorldRotation(p.yaw)) > MovedDegrees;
        if ((t.position - preview.ModuleToWorld(new Vector2(p.x, p.z), p.y)).magnitude < MovedMetres && !turned) return false;
        var at = preview.WorldToModule(t.position);
        var q = p;
        if (Mathf.Abs(at.x - p.x) > MovedMetres) q.x = Mathf.Clamp(FrontRoomsModuleEditing.Snap(at.x), 0f, m.WidthMetres);
        if (Mathf.Abs(at.y - p.z) > MovedMetres) q.z = Mathf.Clamp(FrontRoomsModuleEditing.Snap(at.y), 0f, m.DepthMetres);
        if (turned) q.yaw = Mathf.Repeat(Mathf.Round(preview.WorldToModuleYaw(t.rotation)), 360f);
        if (q.x != p.x || q.z != p.z || q.yaw != p.yaw)
        {
            FrontRoomsModuleEditing.Record(module, "Move prop in Scene");
            m.props[tag.index] = q;
            EditorUtility.SetDirty(module);
            FrontRoomsLevelDesignerWindow.RepaintOpen();
        }
        return true;
    }

    /// <summary>The move is over: rebuild the preview from the module (the moved props stay selected).</summary>
    public static void Commit(FrontRoomsModulePreview preview)
    {
        moved = false;
        // The move's undo step closes here, not with whatever the designer does next.
        Undo.FlushUndoRecordObjects();
        FrontRoomsRoomModule.NotifyChanged(preview.module);
        preview.Rebuild();
    }

    /// <summary>Remove the selected props from the module (Delete in the Scene view). False if none is selected.</summary>
    public static bool RemoveSelected(FrontRoomsModulePreview preview)
    {
        var indices = SelectedTags(preview).Select(t => t.index).ToArray();
        if (indices.Length == 0) return false;
        Selection.objects = new Object[0];
        FrontRoomsModuleEditing.RemoveProps(preview.module, indices);
        return true;
    }

    // ---------- Dropping kits ----------

    /// <summary>The module point (unturned metres) where a ray meets the preview's floor, if it is in or next to the room.</summary>
    public static bool FloorPoint(FrontRoomsModulePreview preview, Ray ray, out Vector2 at)
    {
        at = default;
        if (!preview.FloorPlane.Raycast(ray, out var distance)) return false;
        at = preview.WorldToModule(ray.GetPoint(distance));
        var m = preview.module.data;
        const float reach = .5f;
        return at.x > -reach && at.y > -reach && at.x < m.WidthMetres + reach && at.y < m.DepthMetres + reach;
    }

    /// <summary>Add a kit dropped at a module point; it is selected once the preview has rebuilt. Returns its index.</summary>
    public static int Drop(FrontRoomsModulePreview preview, string kit, Vector2 at)
    {
        var index = FrontRoomsModuleEditing.AddKit(preview.module, kit, at);
        reselect = new[] { index };
        return index;
    }

    // ---------- Scene GUI ----------

    static void OnSceneGUI(SceneView view)
    {
        var preview = ActivePreview();
        if (preview == null) return;
        var e = Event.current;

        var kit = DragAndDrop.GetGenericData(FrontRoomsModuleEditing.DragKey) as string;
        if (kit != null && (e.type == EventType.DragUpdated || e.type == EventType.DragPerform))
        {
            var onFloor = FloorPoint(preview, HandleUtility.GUIPointToWorldRay(e.mousePosition), out var at);
            DragAndDrop.visualMode = onFloor ? DragAndDropVisualMode.Copy : DragAndDropVisualMode.Rejected;
            ghost = onFloor ? (kit, at) : ((string, Vector2)?)null;
            if (onFloor && e.type == EventType.DragPerform)
            {
                DragAndDrop.AcceptDrag();
                Drop(preview, kit, at);
                ghost = null;
            }
            e.Use();
            view.Repaint();
        }
        else if (e.type == EventType.DragExited && ghost != null)
        {
            ghost = null;
            view.Repaint();
        }

        // Delete: the props leave the module (Unity would only destroy the preview's copies).
        if ((e.type == EventType.ValidateCommand || e.type == EventType.ExecuteCommand) && (e.commandName == "SoftDelete" || e.commandName == "Delete")
            && SelectedTags(preview).Count > 0)
        {
            if (e.type == EventType.ExecuteCommand) RemoveSelected(preview);
            e.Use();
        }

        if (e.type == EventType.Repaint) DrawRoom(preview);
    }

    /// <summary>The module's outline just above the floor, its openings in green with their kind, and a dragged kit's footprint.</summary>
    static void DrawRoom(FrontRoomsModulePreview preview)
    {
        var m = preview.module.data;
        var cs = MapGrid.CellSize;
        Vector3 At(float x, float z, float y = .03f) => preview.ModuleToWorld(new Vector2(x, z), y);
        Handles.color = OutlineColor;
        Handles.DrawAAPolyLine(4f, At(0f, 0f), At(m.WidthMetres, 0f), At(m.WidthMetres, m.DepthMetres), At(0f, m.DepthMetres), At(0f, 0f));
        if (label == null) label = new GUIStyle(EditorStyles.miniBoldLabel) { alignment = TextAnchor.MiddleCenter, normal = { textColor = OpeningColor } };
        void Opening(ModuleEdge kind, Vector2 a, Vector2 b)
        {
            if (kind == ModuleEdge.Wall) return;
            Handles.color = OpeningColor;
            Handles.DrawAAPolyLine(6f, At(a.x, a.y), At(b.x, b.y));
            Handles.Label(At((a.x + b.x) * .5f, (a.y + b.y) * .5f) + Vector3.up * .3f, kind == ModuleEdge.Arch ? "arch" : "open", label);
        }
        for (var i = 0; i < m.width; i++)
        {
            Opening(m.south[i], new Vector2(i * cs, 0f), new Vector2((i + 1) * cs, 0f));
            Opening(m.north[i], new Vector2(i * cs, m.DepthMetres), new Vector2((i + 1) * cs, m.DepthMetres));
        }
        for (var j = 0; j < m.depth; j++)
        {
            Opening(m.west[j], new Vector2(0f, j * cs), new Vector2(0f, (j + 1) * cs));
            Opening(m.east[j], new Vector2(m.WidthMetres, j * cs), new Vector2(m.WidthMetres, (j + 1) * cs));
        }
        if (ghost == null) return;
        // Where the dragged kit will stand, wall units already against their wall.
        var p = FrontRoomsModuleEditing.NewProp(m, ghost.Value.kit, ghost.Value.at);
        var f = FrontRoomsModuleEditing.Footprint(p.kit);
        var rad = p.yaw * Mathf.Deg2Rad;
        float c = Mathf.Cos(rad), s = Mathf.Sin(rad);
        Vector3 Corner(float x, float z) => At(p.x + x * c + z * s, p.z - x * s + z * c, p.y + .03f);
        Handles.DrawSolidRectangleWithOutline(new[] { Corner(f[0], f[1]), Corner(f[2], f[1]), Corner(f[2], f[3]), Corner(f[0], f[3]) }, GhostFill, OpeningColor);
    }
}
