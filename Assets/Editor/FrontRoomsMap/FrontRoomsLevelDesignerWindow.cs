using System.Collections.Generic;
using System.Linq;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The Level Designer's panel (P2), docked beside the Inspector with the
/// Scene or Game view on the left: the room modules, the selected one's plan,
/// a palette of kit assets, its props and settings, the preview's seed and
/// turn, and whether the generator may use it. Kits are placed by clicking
/// one to arm it and then clicking in the plan, or by dragging one into the
/// plan or onto the floor in the Scene view (FrontRoomsDesignerSceneTools).
/// FrontRooms → Level Designer → Window, or Open.
/// </summary>
public sealed class FrontRoomsLevelDesignerWindow : EditorWindow
{
    static readonly string[] Filters = { "All", "Floor", "Wall", "DeskTop" };
    static readonly Color RowSelected = new Color(.24f, .48f, .90f, .45f), Armed = new Color(1f, .6f, .2f, .55f), Tile = new Color(0f, 0f, 0f, .18f);
    const float TileWidth = 76f, Thumb = 64f, TileHeight = Thumb + 16f;

    [SerializeField] FrontRoomsRoomModule module;
    [SerializeField] string search = "";
    [SerializeField] string paletteSearch = "";
    [SerializeField] int paletteFilter;
    [SerializeField] Vector2 scroll, listScroll, propsScroll;
    [SerializeField] bool showRoom = true, showPalette = true, showProps = true, showPreview = true, showGenerator = true, showChecks = true;

    static FrontRoomsLevelDesignerWindow open;
    static GUIStyle tileLabel, rowNote;

    FrontRoomsModulePlanView plan;
    RoomModuleData resizeFrom;
    // Every module asset, found again when the project changes.
    List<FrontRoomsRoomModule> modules;
    // The new name while renaming, else null.
    string renaming;
    // A palette tile under a held mouse button, until it becomes a click (arm) or a drag.
    string pressedKit;
    Vector2 pressedAt;

    [MenuItem("FrontRooms/Level Designer/Window", priority = 1)]
    public static void OpenWindow() => ShowFor(null);

    /// <summary>Open or focus the window, docked beside the Inspector when one is open, on <paramref name="target"/> (null: the one it had).</summary>
    public static FrontRoomsLevelDesignerWindow ShowFor(FrontRoomsRoomModule target)
    {
        var inspector = typeof(Editor).Assembly.GetType("UnityEditor.InspectorWindow");
        var window = inspector != null
            ? GetWindow<FrontRoomsLevelDesignerWindow>("Level Designer", true, inspector)
            : GetWindow<FrontRoomsLevelDesignerWindow>("Level Designer", true);
        if (target != null && target != window.module)
        {
            window.module = target;
            window.plan.Select(-1, false);
        }
        window.Repaint();
        return window;
    }

    /// <summary>Repaint the window if it is open (props moved in the Scene view).</summary>
    public static void RepaintOpen()
    {
        if (open != null) open.Repaint();
    }

    void OnEnable()
    {
        open = this;
        titleContent = new GUIContent("Level Designer");
        // The plan follows the mouse with an armed kit's ghost, and drops it when the mouse leaves.
        wantsMouseMove = true;
        wantsMouseEnterLeaveWindow = true;
        plan = new FrontRoomsModulePlanView(Repaint);
        plan.SelectionChanged += OnPlanSelection;
        FrontRoomsRoomModule.Changed += OnModuleChanged;
        Undo.undoRedoPerformed += Repaint;
        EditorApplication.projectChanged += OnProjectChanged;
        // Enough room for every kit's thumbnail.
        AssetPreview.SetPreviewTextureCacheSize(256);
    }

    void OnDisable()
    {
        if (open == this) open = null;
        plan.EndDrag();
        FrontRoomsRoomModule.Changed -= OnModuleChanged;
        Undo.undoRedoPerformed -= Repaint;
        EditorApplication.projectChanged -= OnProjectChanged;
    }

    void OnModuleChanged(FrontRoomsRoomModule changed)
    {
        if (changed == module) Repaint();
    }

    void OnProjectChanged()
    {
        modules = null;
        Repaint();
    }

    void OnFocus()
    {
        modules = null;
        Repaint();
    }

    /// <summary>A prop selected in the Scene view is selected here too.</summary>
    void OnSelectionChange()
    {
        var preview = FrontRoomsDesignerSceneTools.ScenePreview();
        if (preview == null || preview.module != module) return;
        var index = FrontRoomsDesignerSceneTools.SelectedIndex(preview);
        if (index >= 0) plan.Select(index, false);
    }

    /// <summary>A prop picked in the plan or the list is selected in the Scene view, ready for the Move tool.</summary>
    void OnPlanSelection(int index)
    {
        var preview = FrontRoomsDesignerSceneTools.ScenePreview();
        if (preview == null || preview.module != module) return;
        if (index >= 0) FrontRoomsDesignerSceneTools.SelectProps(preview, new[] { index });
        else if (FrontRoomsDesignerSceneTools.SelectedIndex(preview) >= 0) Selection.objects = new Object[0];
    }

    /// <summary>Show a module here and in the preview (undoable on the preview).</summary>
    void SetModule(FrontRoomsRoomModule target)
    {
        module = target;
        modules = null;
        renaming = null;
        plan.Select(-1, false);
        var preview = FrontRoomsDesignerSceneTools.ScenePreview();
        if (preview == null || target == null || preview.module == target) return;
        // The selected props belong to the module that is leaving.
        FrontRoomsDesignerSceneTools.Deselect(preview);
        Undo.RecordObject(preview, "Preview module");
        preview.module = target;
        EditorUtility.SetDirty(preview);
        preview.Rebuild();
        FrontRoomsLevelDesigner.FramePreview();
    }

    void OnGUI()
    {
        ModuleList();
        if (module == null)
        {
            EditorGUILayout.HelpBox("Pick a room module above, or press New.", MessageType.Info);
            return;
        }
        module.data.Normalize();
        var preview = FrontRoomsDesignerSceneTools.ScenePreview();

        scroll = EditorGUILayout.BeginScrollView(scroll);
        if (preview == null || preview.module != module)
        {
            EditorGUILayout.HelpBox(preview == null ? "The designer scene is not open: the Scene view tools and the preview controls need it." : "The preview shows another module.", MessageType.Info);
            using (new EditorGUI.DisabledScope(EditorApplication.isPlayingOrWillChangePlaymode))
                if (GUILayout.Button(preview == null ? "Open the designer scene on this module" : "Preview this module"))
                {
                    // Scene changes and save prompts must not run inside a GUI pass.
                    var target = module;
                    EditorApplication.delayCall += () => FrontRoomsLevelDesigner.Open(target);
                }
        }

        showRoom = Section(showRoom, "Room");
        if (showRoom)
        {
            FrontRoomsModuleGUI.Notes(module);
            FrontRoomsModuleGUI.Room(module, ref resizeFrom);
        }

        EditorGUILayout.Space(4);
        EditorGUILayout.LabelField("Plan (north up)", EditorStyles.boldLabel);
        plan.Draw(module, position.width - 40f);
        EditorGUILayout.LabelField(plan.ArmedKit != null
            ? "Click to place " + plan.ArmedKit + " (Shift: keep placing). Esc stops."
            : "Click a prop to select (again: the one under it), drag to move, R turns, Delete removes, Esc deselects. Click an edge: wall → arch → open. Right-click a cell: lamp.", EditorStyles.wordWrappedMiniLabel);

        showPalette = Section(showPalette, "Palette");
        if (showPalette) Palette();

        showProps = Section(showProps, "Props (" + module.data.props.Length + ")");
        if (showProps)
        {
            PropList();
            FrontRoomsModuleGUI.SelectedProp(module, plan);
        }

        showPreview = Section(showPreview, "Preview");
        if (showPreview) PreviewControls(preview);

        showGenerator = Section(showGenerator, "Generator");
        if (showGenerator) Generator();

        showChecks = Section(showChecks, "Checks");
        if (showChecks) FrontRoomsModuleGUI.Checks(module);
        EditorGUILayout.EndScrollView();
    }

    /// <summary>A section header that folds (a plain foldout: header groups break when a control exits the GUI pass inside them).</summary>
    static bool Section(bool show, string title) => EditorGUILayout.Foldout(show, title, true, EditorStyles.foldoutHeader);

    // ---------- Modules ----------

    void ModuleList()
    {
        using (new EditorGUILayout.HorizontalScope(EditorStyles.toolbar))
        {
            search = GUILayout.TextField(search, EditorStyles.toolbarSearchField, GUILayout.MinWidth(80f));
            // Asset changes wait for the end of the GUI pass.
            if (GUILayout.Button(new GUIContent("New", "A 3 × 3 room in " + FrontRoomsRoomModule.Folder), EditorStyles.toolbarButton, GUILayout.Width(40f)))
                EditorApplication.delayCall += () => SetModule(FrontRoomsLevelDesigner.CreateModule());
            using (new EditorGUI.DisabledScope(module == null))
            {
                var current = module;
                if (GUILayout.Button("Duplicate", EditorStyles.toolbarButton, GUILayout.Width(64f)))
                    EditorApplication.delayCall += () => SetModule(FrontRoomsLevelDesigner.DuplicateModule(current));
                if (GUILayout.Button("Rename", EditorStyles.toolbarButton, GUILayout.Width(56f))) renaming = module.name;
                if (GUILayout.Button("Ping", EditorStyles.toolbarButton, GUILayout.Width(36f))) EditorGUIUtility.PingObject(module);
            }
        }
        if (renaming != null && module != null)
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                // Read before the field, which may take the key itself.
                var enter = Event.current.type == EventType.KeyDown && (Event.current.keyCode == KeyCode.Return || Event.current.keyCode == KeyCode.KeypadEnter) && GUI.GetNameOfFocusedControl() == "rename";
                GUI.SetNextControlName("rename");
                renaming = EditorGUILayout.TextField(renaming);
                if (GUILayout.Button("OK", GUILayout.Width(40f)) || enter)
                {
                    var target = module;
                    var name = renaming.Trim();
                    renaming = null;
                    EditorApplication.delayCall += () =>
                    {
                        var error = AssetDatabase.RenameAsset(AssetDatabase.GetAssetPath(target), name);
                        if (!string.IsNullOrEmpty(error)) Debug.LogWarning("[FrontRoomsLevelDesigner] " + error);
                        modules = null;
                        Repaint();
                    };
                    if (enter) Event.current.Use();
                }
                if (GUILayout.Button("Cancel", GUILayout.Width(56f))) renaming = null;
            }
        }

        var profile = FrontRoomsLevelProfiles.Resolve();
        if (modules == null) modules = FrontRoomsLevelDesigner.Modules().ToList();
        var shown = modules.Where(m => m != null && (string.IsNullOrEmpty(search) || m.name.IndexOf(search, System.StringComparison.OrdinalIgnoreCase) >= 0)).ToList();
        var rows = Mathf.Clamp(shown.Count, 1, 6);
        if (rowNote == null) rowNote = new GUIStyle(EditorStyles.miniLabel) { alignment = TextAnchor.MiddleRight };
        listScroll = EditorGUILayout.BeginScrollView(listScroll, GUILayout.Height(rows * EditorGUIUtility.singleLineHeight + 6f));
        foreach (var m in shown)
        {
            var r = GUILayoutUtility.GetRect(new GUIContent(m.name), EditorStyles.label);
            var e = Event.current;
            if (e.type == EventType.Repaint && m == module) EditorGUI.DrawRect(r, RowSelected);
            var used = profile.modules != null && profile.modules.Contains(m);
            var d = m.data;
            var size = d != null ? d.width + " × " + d.depth + " · " + d.height + (d.theme == ZoneTheme.Office ? " Office" : "") : "";
            GUI.Label(r, new GUIContent(m.name, m.notes), EditorStyles.label);
            GUI.Label(r, (used ? "generator · " : "") + size, rowNote);
            if (e.type == EventType.MouseDown && e.button == 0 && r.Contains(e.mousePosition))
            {
                if (m != module) SetModule(m);
                e.Use();
            }
        }
        if (shown.Count == 0) EditorGUILayout.LabelField("No room modules" + (string.IsNullOrEmpty(search) ? "." : " match."), EditorStyles.miniLabel);
        EditorGUILayout.EndScrollView();
    }

    // ---------- Palette ----------

    void Palette()
    {
        using (new EditorGUILayout.HorizontalScope())
        {
            paletteFilter = GUILayout.Toolbar(paletteFilter, Filters, EditorStyles.miniButton);
            paletteSearch = GUILayout.TextField(paletteSearch, EditorStyles.toolbarSearchField, GUILayout.MinWidth(60f));
        }
        var kits = FrontRoomsModuleEditing.PaletteKits(Filters[paletteFilter], paletteSearch);
        var columns = Mathf.Max(1, Mathf.FloorToInt((position.width - 30f) / TileWidth));
        var rows = Mathf.CeilToInt(kits.Count / (float)columns);
        var area = GUILayoutUtility.GetRect(columns * TileWidth, rows * TileHeight, GUILayout.ExpandWidth(false));
        var id = GUIUtility.GetControlID(FocusType.Passive);
        var e = Event.current;
        if (tileLabel == null) tileLabel = new GUIStyle(EditorStyles.miniLabel) { alignment = TextAnchor.UpperCenter, clipping = TextClipping.Clip };

        for (var k = 0; k < kits.Count; k++)
        {
            var kit = kits[k];
            var r = new Rect(area.x + k % columns * TileWidth, area.y + k / columns * TileHeight, TileWidth - 4f, TileHeight - 2f);
            if (e.type == EventType.Repaint)
            {
                EditorGUI.DrawRect(r, kit == plan.ArmedKit ? Armed : Tile);
                var model = FrontRoomsKitLibrary.Model(kit);
                // Previews load in the background; until then the model's icon stands in.
                var texture = model != null ? AssetPreview.GetAssetPreview(model) ?? AssetPreview.GetMiniThumbnail(model) : null;
                if (texture != null) GUI.DrawTexture(new Rect(r.x + (r.width - Thumb) * .5f, r.y + 1f, Thumb, Thumb), texture, ScaleMode.ScaleToFit);
                var f = FrontRoomsModuleEditing.Footprint(kit);
                var tip = kit + " · " + FrontRoomsModuleEditing.Placement(kit) + " · " + (f[2] - f[0]).ToString("0.00") + " × " + (f[3] - f[1]).ToString("0.00") + " m, " + f[4].ToString("0.00") + " m high";
                GUI.Label(new Rect(r.x, r.y + Thumb + 1f, r.width, 14f), new GUIContent(FrontRoomsModuleEditing.Short(kit), tip), tileLabel);
            }
            else if (e.type == EventType.MouseDown && e.button == 0 && r.Contains(e.mousePosition))
            {
                pressedKit = kit;
                pressedAt = e.mousePosition;
                GUIUtility.hotControl = id;
                // Out of the search fields, so Esc in the plan reaches the armed kit.
                GUIUtility.keyboardControl = 0;
                e.Use();
            }
        }
        if (GUIUtility.hotControl == id)
        {
            var type = e.GetTypeForControl(id);
            if (type == EventType.MouseDrag && pressedKit != null && (e.mousePosition - pressedAt).magnitude > 4f)
            {
                // Into the plan or onto the Scene view's floor.
                GUIUtility.hotControl = 0;
                DragAndDrop.PrepareStartDrag();
                DragAndDrop.SetGenericData(FrontRoomsModuleEditing.DragKey, pressedKit);
                DragAndDrop.objectReferences = new Object[0];
                DragAndDrop.StartDrag(pressedKit);
                pressedKit = null;
                e.Use();
            }
            else if (type == EventType.MouseUp)
            {
                // A click arms the kit for the plan; a second click disarms it.
                GUIUtility.hotControl = 0;
                if (pressedKit != null) plan.ArmedKit = plan.ArmedKit == pressedKit ? null : pressedKit;
                pressedKit = null;
                e.Use();
                Repaint();
            }
        }
        if (e.type == EventType.Repaint && AssetPreview.IsLoadingAssetPreviews()) Repaint();
        if (kits.Count == 0) EditorGUILayout.LabelField("No kits match.", EditorStyles.miniLabel);
        else EditorGUILayout.LabelField("Click a kit, then click in the plan; or drag it into the plan or onto the floor in the Scene view. Wall units go against the nearest wall, desk-top items onto the desk under them.", EditorStyles.wordWrappedMiniLabel);
    }

    // ---------- Props ----------

    void PropList()
    {
        var props = module.data.props;
        if (props.Length == 0)
        {
            EditorGUILayout.LabelField("No props yet: place some from the palette.", EditorStyles.miniLabel);
            return;
        }
        propsScroll = EditorGUILayout.BeginScrollView(propsScroll, GUILayout.Height(Mathf.Min(props.Length, 8) * (EditorGUIUtility.singleLineHeight + 2f) + 6f));
        for (var k = 0; k < props.Length; k++)
        {
            var p = props[k];
            using (new EditorGUILayout.HorizontalScope())
            {
                var r = GUILayoutUtility.GetRect(GUIContent.none, EditorStyles.label, GUILayout.ExpandWidth(true));
                var e = Event.current;
                if (e.type == EventType.Repaint && k == plan.Selected) EditorGUI.DrawRect(r, RowSelected);
                GUI.Label(r, (k + 1) + "  " + FrontRoomsModuleEditing.Short(p.kit) + "   (" + p.x.ToString("0.00") + ", " + p.z.ToString("0.00") + ")" + (p.y > 0f ? " ↑" + p.y.ToString("0.00") : "") + "  " + p.yaw.ToString("0") + "°");
                if (e.type == EventType.MouseDown && e.button == 0 && r.Contains(e.mousePosition))
                {
                    plan.Select(k);
                    e.Use();
                }
                using (new EditorGUI.DisabledScope(k == 0))
                    if (GUILayout.Button("▲", EditorStyles.miniButtonLeft, GUILayout.Width(22f))) plan.Select(FrontRoomsModuleEditing.ReorderProp(module, k, k - 1));
                using (new EditorGUI.DisabledScope(k == props.Length - 1))
                    if (GUILayout.Button("▼", EditorStyles.miniButtonMid, GUILayout.Width(22f))) plan.Select(FrontRoomsModuleEditing.ReorderProp(module, k, k + 1));
                if (GUILayout.Button("✕", EditorStyles.miniButtonRight, GUILayout.Width(22f)))
                {
                    var selected = plan.Selected;
                    FrontRoomsModuleEditing.RemoveProps(module, new[] { k });
                    // The selection stays on the same prop; the removed one leaves none.
                    plan.Select(selected == k ? -1 : selected > k ? selected - 1 : selected);
                }
            }
        }
        EditorGUILayout.EndScrollView();
    }

    // ---------- Preview ----------

    void PreviewControls(FrontRoomsModulePreview preview)
    {
        using (new EditorGUI.DisabledScope(preview == null || preview.module != module || EditorApplication.isPlayingOrWillChangePlaymode))
        {
            EditorGUI.BeginChangeCheck();
            var seed = EditorGUILayout.DelayedIntField(new GUIContent("Seed", "The maze around the room, the lamps' temperaments and the kits' rolls"), preview != null ? preview.seed : 0);
            var rotation = EditorGUILayout.IntSlider(new GUIContent("Turn (quarter turns)", "Clockwise, as the generator may place it"), preview != null ? preview.rotation : 0, 0, 3);
            if (EditorGUI.EndChangeCheck() && preview != null)
            {
                Undo.RecordObject(preview, "Preview seed and turn");
                preview.seed = seed;
                preview.rotation = rotation;
                EditorUtility.SetDirty(preview);
                preview.Rebuild();
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Rebuild")) preview.Rebuild();
                if (GUILayout.Button("Frame")) FrontRoomsLevelDesigner.FramePreview();
            }
        }
        using (new EditorGUI.DisabledScope(EditorApplication.isPlayingOrWillChangePlaymode))
            if (GUILayout.Button(new GUIContent("Play here", "Opens the designer scene on this module if needed and enters Play mode: walk the room (WASD, mouse, Shift, E).")))
            {
                var target = module;
                EditorApplication.delayCall += () => FrontRoomsLevelDesigner.PlayHere(target);
            }
    }

    // ---------- Generator ----------

    void Generator()
    {
        var profile = FrontRoomsLevelProfiles.Resolve();
        if (!EditorUtility.IsPersistent(profile))
        {
            EditorGUILayout.HelpBox("No level profile asset yet: FrontRooms → Map → Select level profile creates one.", MessageType.Info);
            return;
        }
        using (new EditorGUI.DisabledScope(true))
            EditorGUILayout.ObjectField("Level profile", profile, typeof(FrontRoomsLevelProfile), false);
        var used = profile.modules != null && profile.modules.Contains(module);
        var want = EditorGUILayout.ToggleLeft(new GUIContent("Used by the generator", "In the level profile's module library: the generator may put it into carved rooms it fits"), used);
        if (want != used) FrontRoomsLevelDesigner.SetUsedByGenerator(profile, module, want);

        var g = profile.generation;
        EditorGUI.BeginChangeCheck();
        var chance = EditorGUILayout.Slider(new GUIContent("Module chance (level)", "The chance that a carved room some module fits is replaced by one"), g.moduleChance, 0f, 1f);
        var tier = EditorGUILayout.IntSlider(new GUIContent("Module tier (level)", "Modules whose tier range holds it may be used"), g.moduleTier, 0, 9);
        if (EditorGUI.EndChangeCheck()) FrontRoomsLevelDesigner.SetModuleGeneration(profile, chance, tier);

        EditorGUILayout.Space(2);
        EditorGUILayout.LabelField("This module", EditorStyles.miniBoldLabel);
        FrontRoomsModuleGUI.GeneratorFields(module);
        var m = module.data;
        if (used && (g.moduleTier < m.minTier || g.moduleTier > m.maxTier))
            EditorGUILayout.HelpBox("The level's module tier (" + g.moduleTier + ") is outside this module's range (" + m.minTier + "–" + m.maxTier + "): the generator will not use it.", MessageType.Warning);
        if (used && m.weight <= 0f) EditorGUILayout.HelpBox("Weight 0: the generator will never pick it.", MessageType.Warning);
    }
}
