using System;
using System.IO;
using FrontRooms.Map;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Data-level checks of the map generator for 100 seeds, using the level
/// profile's generation numbers (FrontRoomsLevelProfiles.Resolve): neighbouring chunks
/// agree on every shared edge, every cell is reachable, doors and windows sit
/// only where the ceiling height changes, every key zone has its key, rebuilds
/// are identical, and a shifted chunk keeps its borders. It does not build
/// geometry or load a scene.
/// Run with -executeMethod FrontRoomsMapVerification.RunBatch; failures throw after the JSON report is saved.
/// </summary>
public static class FrontRoomsMapVerification
{
    const int FirstSeed = 20261001;
    const int SeedCount = 100;
    const int RadiusChunks = 4;

    [MenuItem("FrontRooms/Map/Verify 100 seeds")]
    public static void Verify() => Run(false);

    public static void RunBatch() => Run(true);

    public static string Run(bool throwOnFailure)
    {
        var profile = FrontRoomsLevelProfiles.Resolve();
        var report = FrontRoomsMapValidator.Run(profile.generation, FirstSeed, SeedCount, RadiusChunks);
        var path = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Verification", "map-verification-latest.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        File.WriteAllText(path, JsonUtility.ToJson(report, true));
        var summary = "[FrontRoomsMap] " + (report.failed == 0 ? "PASS" : "FAIL") + " · " + report.passed + "/" + report.seedCount
            + " seeds · " + (RadiusChunks * 2) + "×" + (RadiusChunks * 2) + " chunks each · profile " + (AssetDatabase.GetAssetPath(profile) is string p && p.Length > 0 ? p : "code defaults") + " · " + path;
        if (report.failed == 0) Debug.Log(summary);
        else
        {
            foreach (var seed in report.seeds)
                if (!seed.passed) { Debug.LogError("[FrontRoomsMap] seed " + seed.seed + ": " + string.Join(" | ", seed.errors)); break; }
            Debug.LogError(summary);
        }
        if (throwOnFailure && report.failed > 0) throw new Exception(summary);
        return summary;
    }
}
