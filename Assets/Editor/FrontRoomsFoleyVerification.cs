using System;
using UnityEditor;
using UnityEngine;

/// <summary>Smoke test for the data-driven Foley banks and door layer set.</summary>
public static class FrontRoomsFoleyVerification
{
    [MenuItem("FrontRooms/Audio/Verify Foley banks")]
    public static void Run()
    {
        var hinge = Resources.Load<AudioClip>("Audio/door-creak");
        var foley = new FrontRoomsFoley(hinge);
        var pass = foley.Doors != null && foley.Doors.latch != null && foley.Doors.hinge != null
            && foley.Doors.travel != null && foley.Doors.slam != null && foley.Doors.breakImpact != null;
        var count = 0;
        foreach (FrontRoomsFoleyActor actor in Enum.GetValues(typeof(FrontRoomsFoleyActor)))
        foreach (FrontRoomsFoleySurface surface in Enum.GetValues(typeof(FrontRoomsFoleySurface)))
        for (var running = 0; running <= 1; running++)
        for (var i = 0; i < 4; i++)
        {
            var step = foley.PickStep(actor, surface, running == 1);
            pass &= step != null && step.impact != null && step.texture != null && step.cloth != null;
            count++;
        }
        Debug.Log("[FrontRoomsFoley] " + (pass ? "PASS" : "FAIL") + " · checked " + count + " surface/state selections and 5 door layers");
        if (Application.isBatchMode) EditorApplication.Exit(pass ? 0 : 1);
    }
}
