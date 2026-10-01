using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class FrontRooms3DBuild
{
    const string Scene = "Assets/Scenes/FrontRooms3D.unity";
    [MenuItem("FrontRooms 3D/Create Scene")]
    public static void CreateScene()
    {
        Directory.CreateDirectory("Assets/Scenes");
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var root = new GameObject("FrontRooms 3D");
        var game = root.AddComponent<FrontRooms3DGame>();
        game.EnsureEditorPreview();
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene, Scene);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(Scene, true) };
    }
    [MenuItem("FrontRooms 3D/Build macOS")]
    public static void BuildMac()
    {
        FrontRoomsVerification.Run();
        GraphicsSettings.defaultRenderPipeline = null;
        QualitySettings.renderPipeline = null;
        PlayerSettings.productName = "FrontRooms3D"; PlayerSettings.companyName = "Red Wang";
        PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Standalone, "com.redwang.frontrooms3d");
        PlayerSettings.bundleVersion = "0.1.0"; PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
        // Match the Canvas reference resolution so the title and HUD are not downsampled on launch.
        PlayerSettings.defaultScreenWidth = 1920; PlayerSettings.defaultScreenHeight = 1080;
        PlayerSettings.resizableWindow = true; PlayerSettings.runInBackground = true;
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
        CreateScene();
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions { scenes = new[] {Scene}, locationPathName = "Builds/Mac/FrontRooms3D.app", target = BuildTarget.StandaloneOSX, options = BuildOptions.None });
        Debug.Log("[FrontRooms3DBuild] " + report.summary.result + " errors=" + report.summary.totalErrors + " bytes=" + report.summary.totalSize);
        if (report.summary.result != BuildResult.Succeeded) throw new Exception("3D build failed");
    }

    /// <summary>
    /// Build a browser-ready WebGL player. This deliberately avoids threads and
    /// server-only compression headers so the output can be hosted on GitHub
    /// Pages or any static file server without additional configuration.
    /// </summary>
    [MenuItem("FrontRooms 3D/Build WebGL")]
    public static void BuildWebGL()
    {
        FrontRoomsVerification.Run();
        var webglGroup = BuildPipeline.GetBuildTargetGroup(BuildTarget.WebGL);
        EditorUserBuildSettings.SwitchActiveBuildTarget(webglGroup, BuildTarget.WebGL);
        ApplyWebGLSettings();
        CreateScene();

        const string output = "Builds/WebGL";
        Directory.CreateDirectory(output);
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { Scene },
            locationPathName = output,
            target = BuildTarget.WebGL,
            options = BuildOptions.None
        });
        Debug.Log("[FrontRooms3DBuild] WebGL " + report.summary.result +
                  " errors=" + report.summary.totalErrors +
                  " warnings=" + report.summary.totalWarnings +
                  " bytes=" + report.summary.totalSize);
        if (report.summary.result != BuildResult.Succeeded) throw new Exception("3D WebGL build failed");
    }

    static void ApplyWebGLSettings()
    {
        PlayerSettings.productName = "FrontRooms3D";
        PlayerSettings.companyName = "Red Wang";
        PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.WebGL, "com.redwang.frontrooms3d");
        PlayerSettings.bundleVersion = "0.1.0";
        PlayerSettings.defaultScreenWidth = 1280;
        PlayerSettings.defaultScreenHeight = 720;
        PlayerSettings.runInBackground = true;
        PlayerSettings.resizableWindow = true;
        PlayerSettings.WebGL.template = "APPLICATION:Default";
        PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Brotli;
        PlayerSettings.WebGL.decompressionFallback = true;
        PlayerSettings.WebGL.dataCaching = true;
        PlayerSettings.WebGL.nameFilesAsHashes = true;
        PlayerSettings.WebGL.showDiagnostics = false;
        PlayerSettings.WebGL.debugSymbolMode = WebGLDebugSymbolMode.Off;
        PlayerSettings.WebGL.analyzeBuildSize = false;
        PlayerSettings.WebGL.useEmbeddedResources = false;
        PlayerSettings.WebGL.linkerTarget = WebGLLinkerTarget.Wasm;
        PlayerSettings.WebGL.wasm2023 = true;
        PlayerSettings.WebGL.threadsSupport = false;
        PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.None;
        PlayerSettings.WebGL.wasmArithmeticExceptions = WebGLWasmArithmeticExceptions.Ignore;
        PlayerSettings.WebGL.initialMemorySize = 128;
        PlayerSettings.WebGL.maximumMemorySize = 1024;
        PlayerSettings.WebGL.memoryGrowthMode = WebGLMemoryGrowthMode.Geometric;
        PlayerSettings.WebGL.geometricMemoryGrowthStep = 0.2f;
        PlayerSettings.WebGL.memoryGeometricGrowthCap = 64;
        PlayerSettings.WebGL.linearMemoryGrowthStep = 16;
        PlayerSettings.WebGL.powerPreference = WebGLPowerPreference.HighPerformance;
        PlayerSettings.WebGL.webAssemblyTable = false;
        PlayerSettings.WebGL.webAssemblyBigInt = false;
        PlayerSettings.WebGL.closeOnQuit = false;
        PlayerSettings.SetManagedStrippingLevel(UnityEditor.Build.NamedBuildTarget.WebGL, ManagedStrippingLevel.High);
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.WebGL, ScriptingImplementation.IL2CPP);
        EditorUserBuildSettings.webGLBuildSubtarget = WebGLTextureSubtarget.Generic;
        EditorUserBuildSettings.development = false;
        EditorUserBuildSettings.allowDebugging = false;
        EditorUserBuildSettings.connectProfiler = false;
        QualitySettings.SetQualityLevel(3, true); // High: preserve the readable material/lighting slice.
    }
}
