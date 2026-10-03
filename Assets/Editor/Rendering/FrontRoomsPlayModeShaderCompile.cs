using UnityEditor;

/// <summary>
/// Play Mode compiles shader variants synchronously, so a frame never shows
/// Unity's cyan placeholder while a variant compiles. This mattered for the
/// URP/Lit lens and glass materials the map makes at runtime: after a URP
/// keyword change, every new lighting combination (a Tall hall, a dead lamp)
/// drew them cyan until the compile finished. The cost is a one-off hitch the
/// first time a variant is drawn, as in a player build; the variant is then
/// cached in Library/ShaderCache. Edit mode keeps asynchronous compilation.
/// Editor only: player builds (Mac, Win, WebGL) are unaffected.
/// </summary>
[InitializeOnLoad]
static class FrontRoomsPlayModeShaderCompile
{
    const string PreviousKey = "FrontRooms.PlayModeShaderCompile.PreviousAsync";

    static FrontRoomsPlayModeShaderCompile()
    {
        EditorApplication.playModeStateChanged += OnPlayModeChanged;
        // A domain reload while playing would otherwise leave the default back on.
        if (EditorApplication.isPlaying) ShaderUtil.allowAsyncCompilation = false;
    }

    static void OnPlayModeChanged(PlayModeStateChange change)
    {
        if (change == PlayModeStateChange.ExitingEditMode)
        {
            SessionState.SetBool(PreviousKey, ShaderUtil.allowAsyncCompilation);
            ShaderUtil.allowAsyncCompilation = false;
        }
        else if (change == PlayModeStateChange.EnteredEditMode)
        {
            ShaderUtil.allowAsyncCompilation = SessionState.GetBool(PreviousKey, true);
        }
    }
}
