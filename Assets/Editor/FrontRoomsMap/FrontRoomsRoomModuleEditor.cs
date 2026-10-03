using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The Inspector of a room module: a plan of the room (north up) where clicks
/// edit it, the props and their placement, the gameplay markers, the
/// module's settings, and its checks. The Level Designer window (FrontRooms → Level Designer → Window)
/// draws the same plan and sections (FrontRoomsModulePlanView,
/// FrontRoomsModuleGUI) beside its module list and kit palette; the preview
/// scene rebuilds after every edit made in either.
/// </summary>
[CustomEditor(typeof(FrontRoomsRoomModule))]
public sealed class FrontRoomsRoomModuleEditor : Editor
{
    FrontRoomsModulePlanView plan;
    int addKit;
    bool showGenerator;
    RoomModuleData resizeFrom;

    FrontRoomsRoomModule Module => (FrontRoomsRoomModule)target;

    void OnEnable()
    {
        plan = new FrontRoomsModulePlanView(Repaint);
        FrontRoomsRoomModule.Changed += OnModuleChanged;
    }

    void OnDisable()
    {
        FrontRoomsRoomModule.Changed -= OnModuleChanged;
        // A drag ended outside the Inspector: let the preview catch up.
        plan?.EndDrag();
        FrontRoomsModuleGUI.Release(true);
    }

    // Edits made in the window or the Scene view show here at once.
    void OnModuleChanged(FrontRoomsRoomModule changed)
    {
        if (changed == target) Repaint();
    }

    public override void OnInspectorGUI()
    {
        var module = Module;
        var m = module.data ?? (module.data = new RoomModuleData());
        m.Normalize();

        using (new EditorGUILayout.HorizontalScope())
        using (new EditorGUI.DisabledScope(EditorApplication.isPlayingOrWillChangePlaymode))
        {
            // Scene changes and save prompts must not run inside the Inspector's GUI pass.
            if (GUILayout.Button("Open in Level Designer")) EditorApplication.delayCall += () => FrontRoomsLevelDesigner.Open(module);
            if (GUILayout.Button("Frame preview", GUILayout.Width(110))) FrontRoomsLevelDesigner.FramePreview();
        }
        EditorGUILayout.Space(4);

        FrontRoomsModuleGUI.Notes(module);
        FrontRoomsModuleGUI.Room(module, ref resizeFrom);

        // ---------- Plan ----------
        EditorGUILayout.Space(6);
        EditorGUILayout.LabelField("Plan (north up)", EditorStyles.boldLabel);
        plan.Draw(module, EditorGUIUtility.currentViewWidth - 40f);
        EditorGUILayout.LabelField(plan.Help, EditorStyles.wordWrappedMiniLabel);

        // ---------- Props ----------
        EditorGUILayout.Space(6);
        EditorGUILayout.LabelField("Props (" + m.props.Length + ")", EditorStyles.boldLabel);
        var names = FrontRoomsModuleEditing.Kits();
        using (new EditorGUILayout.HorizontalScope())
        {
            addKit = names.Length == 0 ? 0 : EditorGUILayout.Popup(Mathf.Clamp(addKit, 0, names.Length - 1), names);
            using (new EditorGUI.DisabledScope(names.Length == 0))
                if (GUILayout.Button("Add", GUILayout.Width(50)))
                    plan.Select(FrontRoomsModuleEditing.AddKit(module, names[addKit], new Vector2(m.WidthMetres * .5f, m.DepthMetres * .5f)));
        }
        FrontRoomsModuleGUI.SelectedProp(module, plan);

        // ---------- Markers ----------
        EditorGUILayout.Space(6);
        EditorGUILayout.LabelField("Markers (" + m.markers.Length + ")", EditorStyles.boldLabel);
        FrontRoomsModuleGUI.Markers(module, plan);

        // ---------- Generator ----------
        EditorGUILayout.Space(6);
        showGenerator = EditorGUILayout.Foldout(showGenerator, "Where the generator may use it", true);
        if (showGenerator)
        {
            FrontRoomsModuleGUI.GeneratorFields(module);
            FrontRoomsModuleGUI.Fit(module, FrontRoomsLevelProfiles.Resolve());
        }

        // ---------- Checks ----------
        EditorGUILayout.Space(6);
        FrontRoomsModuleGUI.Checks(module);
        FrontRoomsModuleGUI.Release();
    }
}
