using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Scene light that does not come from a fixture: the ambient bounce and the
/// haze. Kept in one place so the title corridor (RoomStream), the maze
/// (MapWorld) and the shipped scene (FrontRoomsRenderSetup) all match.
/// RenderSettings colours are gamma-space.
/// </summary>
public static class FrontRoomsLook
{
    // The practicals are downward spots, so the ceiling faces down into the
    // ground colour: the warm bounce off a lit beige carpet. Walls take the
    // equator; floors face the sky colour, which is the dim ceiling.
    public static readonly Color AmbientSky = new Color(.22f, .21f, .17f);
    public static readonly Color AmbientEquator = new Color(.34f, .31f, .22f);
    public static readonly Color AmbientGround = new Color(.62f, .56f, .40f);
    public static readonly Color FogColor = new Color(.16f, .15f, .11f);
    public const float FogDensity = .014f;
    public const float ReflectionIntensity = .3f;

    /// <summary>Which reflection cubemap the world uses (glass, VCT, metal): the player's zone,
    /// or DeadLamp when the lamp of the player's cell is dead or off.</summary>
    public enum ReflectionZone { Level0, Office, Tall, DeadLamp }

    /// <summary>
    /// Switch the default reflection to the zone's cubemap, crossfading over blendSeconds.
    /// Safe to call every frame with the same value. The map calls it at run start and
    /// on zone / dead-lamp changes. STUB: no-op until the glass work lands the cubemaps
    /// (Documentation/VISUAL_CHAT_TASKS.md G6); the signature is final.
    /// </summary>
    public static void SetZoneReflection(ReflectionZone zone, float blendSeconds = .5f)
    {
    }

    public static void ApplyAmbient()
    {
        RenderSettings.ambientMode = AmbientMode.Trilight;
        // Set ambientLight first: it aliases the sky colour.
        RenderSettings.ambientLight = AmbientSky;
        RenderSettings.ambientSkyColor = AmbientSky;
        RenderSettings.ambientEquatorColor = AmbientEquator;
        RenderSettings.ambientGroundColor = AmbientGround;
        RenderSettings.reflectionIntensity = ReflectionIntensity;
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.ExponentialSquared;
        RenderSettings.fogColor = FogColor;
        RenderSettings.fogDensity = FogDensity;
        // URP lights with the ambient probe (SH), which is only rebuilt from
        // these colours on a bake or here; without it the change is invisible.
        DynamicGI.UpdateEnvironment();
    }
}
