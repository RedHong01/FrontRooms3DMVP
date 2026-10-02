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
