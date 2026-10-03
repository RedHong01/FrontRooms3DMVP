using System;
using System.Collections.Generic;
using System.IO;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// The WebGL lamp tick (FrontRoomsMapWorld.TickFixturesNearOnly) against the
/// desktop lamp formula, checked without playing the game: every lamp's Light
/// and lens are read back from the components after ticking and compared with
/// what the desktop path would have set (lit within lightRadius, at
/// baseIntensity × level × fade, soft shadows within shadowRadius when it
/// casts, the lens at the current glow; otherwise off, the lens within 5% of
/// the glow). The player stands still, crosses chunk borders, walks far and
/// comes back; the clocks run long enough for stutters, dropouts and blinks.
/// The desktop path is checked the same way, so the checker itself is proven.
/// Writes Verification/fixture-tick-tests.json.
/// Headless: -executeMethod FrontRoomsFixtureTickTests.RunBatch -quit (throws on FAIL).
/// </summary>
public static class FrontRoomsFixtureTickTests
{
    const float Dt = 1f / 60f;

    [Serializable]
    sealed class Report
    {
        public string verdict;
        public int passed, failed;
        public List<string> checks = new List<string>();
    }

    static Report report;

    static void Check(bool ok, string what)
    {
        if (ok) report.passed++; else report.failed++;
        report.checks.Add((ok ? "ok   " : "FAIL ") + what);
    }

    [MenuItem("FrontRooms/Map/Test lamp tick (WebGL near-only)")]
    public static void Run() => Execute(false);

    public static void RunBatch() => Execute(true);

    static void Execute(bool throwOnFail)
    {
        report = new Report();
        var ambientMode = RenderSettings.ambientMode;
        var sky = RenderSettings.ambientSkyColor;
        var equator = RenderSettings.ambientEquatorColor;
        var ground = RenderSettings.ambientGroundColor;
        var reflection = RenderSettings.reflectionIntensity;
        var fog = RenderSettings.fog;
        var fogMode = RenderSettings.fogMode;
        var fogColor = RenderSettings.fogColor;
        var fogDensity = RenderSettings.fogDensity;
        var skybox = RenderSettings.skybox;
        var nearOnly = FrontRoomsMapWorld.TickFixturesNearOnly;
        var roots = new List<GameObject>();
        try
        {
            Walk(roots, true, -41f, "WebGL near-only");
            Walk(roots, false, -43f, "desktop");
        }
        catch (Exception e)
        {
            Check(false, "exception: " + e.GetType().Name + " " + e.Message + "\n" + e.StackTrace);
        }
        finally
        {
            FrontRoomsMapWorld.TickFixturesNearOnly = nearOnly;
            foreach (var r in roots)
            {
                if (r == null) continue;
                var w = r.GetComponent<FrontRoomsMapWorld>();
                if (w != null) w.Release();
                UnityEngine.Object.DestroyImmediate(r);
            }
            RenderSettings.ambientMode = ambientMode;
            RenderSettings.ambientSkyColor = sky;
            RenderSettings.ambientEquatorColor = equator;
            RenderSettings.ambientGroundColor = ground;
            RenderSettings.reflectionIntensity = reflection;
            RenderSettings.fog = fog;
            RenderSettings.fogMode = fogMode;
            RenderSettings.fogColor = fogColor;
            RenderSettings.fogDensity = fogDensity;
            RenderSettings.skybox = skybox;
            DynamicGI.UpdateEnvironment();
        }

        var pass = report.failed == 0 && report.passed > 0;
        report.verdict = (pass ? "PASS" : "FAIL") + ": " + report.passed + " passed, " + report.failed + " failed";
        var path = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "fixture-tick-tests.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        File.WriteAllText(path, JsonUtility.ToJson(report, true));
        var text = "[FixtureTickTests] " + report.verdict + "\n" + string.Join("\n", report.checks);
        if (pass) Debug.Log(text); else Debug.LogError(text);
        if (throwOnFail && !pass) throw new Exception(report.verdict);
    }

    /// <summary>Build the Level 0 map round its spawn, then tick the lamps while the eye stands, moves and returns.</summary>
    static void Walk(List<GameObject> roots, bool nearOnly, float period, string label)
    {
        FrontRoomsMapWorld.TickFixturesNearOnly = nearOnly;
        var root = new GameObject("FIXTURE TICK TEST / " + label) { hideFlags = HideFlags.DontSave };
        roots.Add(root);
        // Far from the open scene, on whole world periods so surfaces stay on the lattice.
        root.transform.position = new Vector3(period * ModuleUnits.WorldPeriod, 0f, -27f * ModuleUnits.WorldPeriod);
        var world = root.AddComponent<FrontRoomsMapWorld>();
        world.Profile = FrontRoomsLevelProfiles.Resolve();
        world.BuildForCapture();
        // Transform.Find reads "/" as a path separator, so match the child by name.
        Transform eye = null;
        foreach (Transform child in world.transform) if (child.name == "CAPTURE / eye") eye = child;
        if (eye == null) { Check(false, label + ": BuildForCapture left no eye"); return; }
        var start = eye.position;
        var problems = new List<string>();

        void Verify(string where, int frames)
        {
            for (var i = 0; i < frames; i++) world.TickFixturesForTools(Dt);
            problems.Clear();
            var mismatches = world.CheckLampStatesForTools(out var lit, out var total, problems);
            Check(total > 0, label + " · " + where + ": " + total + " lamps built");
            Check(mismatches == 0, label + " · " + where + ": " + lit + " lit of " + total + ", " + mismatches + " disagree with the lamp formula" + (problems.Count > 0 ? "\n      " + string.Join("\n      ", problems) : ""));
        }

        Verify("at the spawn, first frame", 1);
        Verify("at the spawn, 6 s", 360);
        eye.position = start + new Vector3(MapGrid.ChunkSize, 0f, 0f);
        Verify("one chunk east", 30);
        eye.position = start + new Vector3(MapGrid.ChunkSize * 2f, 0f, MapGrid.ChunkSize * 2f);
        Verify("two chunks north-east", 30);
        eye.position = start + new Vector3(MapGrid.ChunkSize * 1.5f, 0f, -MapGrid.ChunkSize * .5f);
        Verify("on a chunk border", 240);
        eye.position = start;
        Verify("back at the spawn", 30);
        eye.position = start;
        Verify("back at the spawn, 10 s", 600);
    }
}
