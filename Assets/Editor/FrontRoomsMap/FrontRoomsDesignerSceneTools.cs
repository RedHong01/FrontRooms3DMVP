using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// The Level Designer's Scene view tools, while the designer scene is the
/// active scene and its preview shows a module:
/// - a kit dragged from the palette onto the floor becomes a prop there;
/// - a prop moved or turned with the usual tools (or its Transform fields)
///   writes its new x, z and yaw back to the module as it goes; the preview
///   rebuilds once nothing has moved for 0.3 s with no handle held and no
///   field being typed in, and the rebuilt prop is selected again;
/// - Delete on selected props removes them from the module, Duplicate adds
///   copies of them to it;
/// - the room's outline and openings are drawn on the floor.
/// Clicking a prop selects the whole kit, not a mesh inside it, and props
/// stay selected across every rebuild.
///
/// Moves are seen through Undo.postprocessModifications, which Unity calls
/// for the preview's DontSave props as for any scene object. The module is
/// written on the next editor update, not inside that callback, because an
/// Undo record made there is lost; the write joins the move's undo step.
/// FrontRoomsLevelDesignerTests checks both.
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
    // Transforms of tagged props that Undo saw change, and the undo group of the first, until Sync writes them back.
    static readonly HashSet<Transform> touched = new HashSet<Transform>();
    static int touchedGroup;
    // The preview whose props moved, waiting for its rebuild, and when they last moved.
    static FrontRoomsModulePreview moved;
    static double lastMove;
    // Props to select after the next rebuild, when an edit knows better than the current selection (a drop, a new prop).
    static int[] reselect;
    static (string kit, Vector2 at)? ghost;
    static GUIStyle label;

    static FrontRoomsDesignerSceneTools()
    {
        SceneView.duringSceneGui += OnSceneGUI;
        Undo.postprocessModifications += OnModifications;
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
    /// inside the kit), if the preview's own stamp placed that prop in its
    /// current map and the module has not changed since (same props, same kits).
    /// </summary>
    static FrontRoomsModulePropTag TagOf(GameObject go, FrontRoomsModulePreview preview)
    {
        var tag = go != null ? go.GetComponentInParent<FrontRoomsModulePropTag>(true) : null;
        if (tag == null || preview.module == null || tag.module == null || tag.module != preview.Stamped) return null;
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

    /// <summary>
    /// Select the props with these indices in the Scene view: after the
    /// rebuild on its way if the map is older than the module (a prop added,
    /// removed or swapped), else now. Props the map left out (blocking an
    /// opening, a kit without a model) have nothing to select.
    /// </summary>
    public static void SelectProps(FrontRoomsModulePreview preview, int[] indices) => SelectProps(preview, indices, false);

    static void SelectProps(FrontRoomsModulePreview preview, int[] indices, bool rebuilt)
    {
        if (preview == null || preview.World == null || preview.module == null) return;
        if (!rebuilt && Stale(preview))
        {
            reselect = indices;
            return;
        }
        // Applied: an older request must not override it at the next rebuild.
        reselect = null;
        var tags = preview.World.GetComponentsInChildren<FrontRoomsModulePropTag>(true).Where(t => TagOf(t.gameObject, preview) == t && indices.Contains(t.index));
        Selection.objects = tags.Select(t => (Object)t.gameObject).ToArray();
    }

    /// <summary>The map was stamped from other props than the module has now (their number or kits), so its tags no longer match.</summary>
    static bool Stale(FrontRoomsModulePreview preview)
    {
        var stamped = preview.Stamped;
        var props = preview.module.data.props;
        if (stamped == null || stamped.props.Length != props.Length) return true;
        for (var k = 0; k < props.Length; k++)
            if (stamped.props[k].kit != props[k].kit) return true;
        return false;
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
        if (moved == preview) moved = null;
        if (indices != null && indices.Length > 0) SelectProps(preview, indices, true);
    }

    // ---------- Moving props in the Scene ----------

    /// <summary>Note every tagged prop whose transform Undo saw change (the Move and Rotate tools, the Transform fields).</summary>
    static UndoPropertyModification[] OnModifications(UndoPropertyModification[] modifications)
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return modifications;
        foreach (var modification in modifications)
        {
            if (!(modification.currentValue?.target is Transform t) || t.GetComponentInParent<FrontRoomsModulePropTag>(true) == null) continue;
            if (touched.Count == 0) touchedGroup = Undo.GetCurrentGroup();
            touched.Add(t);
            lastMove = EditorApplication.timeSinceStartup;
        }
        return modifications;
    }

    static void Update()
    {
        Sync();
        // Rebuilding while a handle is held, or a Transform field is typed in, would destroy the object being edited.
        if (moved != null && GUIUtility.hotControl == 0 && !EditorGUIUtility.editingTextField && EditorApplication.timeSinceStartup - lastMove >= Settle) Commit(moved);
    }

    /// <summary>
    /// Write the props Undo saw move back to their modules, as one undo step
    /// with the move. The editor runs it every update; the tests call it
    /// straight after a recorded move.
    /// </summary>
    public static void Sync()
    {
        if (touched.Count == 0) return;
        var wrote = false;
        foreach (var t in touched)
        {
            var tag = t != null ? t.GetComponentInParent<FrontRoomsModulePropTag>(true) : null;
            var preview = tag != null ? tag.GetComponentInParent<FrontRoomsModulePreview>(true) : null;
            if (preview == null || TagOf(tag.gameObject, preview) != tag) continue;
            var module = preview.module;
            var before = module.data.props[tag.index];
            // A mesh moved inside the kit has nothing to write, but the rebuild puts it back.
            if (WriteBack(preview, tag) || t != tag.transform) moved = preview;
            wrote |= !module.data.props[tag.index].Equals(before);
        }
        touched.Clear();
        if (!wrote) return;
        Undo.FlushUndoRecordObjects();
        Undo.CollapseUndoOperations(touchedGroup);
    }

    /// <summary>
    /// If a tagged prop is away from where its module prop puts it, write its
    /// new place back to the module asset: x and z (0.05 m snap, inside the
    /// room) for the axes it moved along, yaw (whole degrees) if it turned.
    /// Recorded for Undo on the asset; the preview is not rebuilt here. Height
    /// stays the panel's (a lifted prop drops back at the rebuild). Returns
    /// whether the prop is away from its module place (scaled counts: the
    /// rebuild sets it right).
    /// </summary>
    static bool WriteBack(FrontRoomsModulePreview preview, FrontRoomsModulePropTag tag)
    {
        var module = preview.module;
        var m = module.data;
        var p = m.props[tag.index];
        var t = tag.transform;
        var turned = Quaternion.Angle(t.rotation, preview.ModuleToWorldRotation(p.yaw)) > MovedDegrees;
        var scaled = (t.localScale - Vector3.one).sqrMagnitude > 1e-6f;
        if ((t.position - preview.ModuleToWorld(new Vector2(p.x, p.z), p.y)).magnitude < MovedMetres && !turned) return scaled;
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

    /// <summary>Props have moved and the preview has not been rebuilt from the module since.</summary>
    public static bool RebuildPending => moved != null;

    /// <summary>The move is over: rebuild the preview from the module (the moved props stay selected).</summary>
    public static void Commit(FrontRoomsModulePreview preview)
    {
        moved = null;
        if (preview == null || preview.module == null) return;
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

    /// <summary>Add copies of the selected props to the module (Duplicate in the Scene view), one undo step; they are selected after the rebuild. False if none is selected.</summary>
    public static bool DuplicateSelected(FrontRoomsModulePreview preview)
    {
        // All indices first: once a copy is added, the map no longer matches the module and no tag counts.
        var indices = SelectedTags(preview).Select(t => t.index).OrderBy(i => i).ToArray();
        if (indices.Length == 0) return false;
        var group = Undo.GetCurrentGroup();
        reselect = indices.Select(i => FrontRoomsModuleEditing.DuplicateProp(preview.module, i)).ToArray();
        Undo.CollapseUndoOperations(group);
        return true;
    }

    // ---------- Dropping kits ----------

    /// <summary>
    /// The module point (unturned metres) where a dropped kit lands, if it is
    /// in or next to the room: where the ray meets the floor or, for a
    /// desk-top kit, the first prop top it crosses on the way (seen at a
    /// slant, the floor behind a desk lies well past the desk).
    /// </summary>
    public static bool FloorPoint(FrontRoomsModulePreview preview, Ray ray, string kit, out Vector2 at)
    {
        at = default;
        if (!preview.FloorPlane.Raycast(ray, out var distance)) return false;
        at = preview.WorldToModule(ray.GetPoint(distance));
        var m = preview.module.data;
        if (FrontRoomsModuleEditing.Placement(kit) == "DeskTop")
            foreach (var p in m.props)
            {
                var top = FrontRoomsModuleEditing.TopHeight(p);
                if (top == null) continue;
                var plane = new Plane(preview.transform.up, preview.transform.TransformPoint(Vector3.up * top.Value));
                if (!plane.Raycast(ray, out var d) || d >= distance) continue;
                var q = preview.WorldToModule(ray.GetPoint(d));
                if (!FrontRoomsModuleEditing.OnTop(p, q, out _)) continue;
                distance = d;
                at = q;
            }
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
        // Prefab Mode keeps the designer scene active: the tools belong to the main stage only.
        if (StageUtility.GetCurrentStageHandle() != StageUtility.GetMainStageHandle()) return;
        var preview = ActivePreview();
        if (preview == null) return;
        var e = Event.current;

        var kit = FrontRoomsModuleEditing.DraggedKit();
        if (kit != null && (e.type == EventType.DragUpdated || e.type == EventType.DragPerform))
        {
            var onFloor = FloorPoint(preview, HandleUtility.GUIPointToWorldRay(e.mousePosition), kit, out var at);
            DragAndDrop.visualMode = onFloor ? DragAndDropVisualMode.Copy : DragAndDropVisualMode.Rejected;
            ghost = onFloor ? (kit, at) : ((string, Vector2)?)null;
            if (onFloor && e.type == EventType.DragPerform)
            {
                DragAndDrop.AcceptDrag();
                FrontRoomsModuleEditing.DragDone();
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
        // Duplicate: the copies join the module (Unity's own would go at the next rebuild).
        if ((e.type == EventType.ValidateCommand || e.type == EventType.ExecuteCommand) && e.commandName == "Duplicate" && SelectedTags(preview).Count > 0)
        {
            if (e.type == EventType.ExecuteCommand) DuplicateSelected(preview);
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
