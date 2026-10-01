using UnityEngine;

/// <summary>
/// Lightweight procedural fluorescent ballast. Level 0 has the strongest
/// voltage instability, while offices keep a steadier work-light cadence.
/// This component lives in its own script asset so Unity serializes scene
/// references with a stable GUID in both the editor and player build.
/// </summary>
public sealed class FrontRoomsLightFlicker : MonoBehaviour
{
    public float baseIntensity = 1f;
    public int seed;
    public RoomRule rule;
    Light target;
    float phase;

    void Awake()
    {
        target = GetComponent<Light>();
        phase = seed * .137f;
    }

    void Update()
    {
        if (target == null) return;
        var time = Time.time + phase;
        var amount = rule == RoomRule.Shift ? .20f : rule == RoomRule.Run ? .08f : .045f;
        var noise = Mathf.PerlinNoise(time * (rule == RoomRule.Shift ? 2.8f : 1.2f), phase) - .5f;
        var dropout = 1f;
        if (rule == RoomRule.Shift && Mathf.Sin(time * 1.7f + phase) > .985f) dropout = .12f;
        if (rule == RoomRule.Run) dropout = .84f + .16f * (0.5f + 0.5f * Mathf.Sin(time * 5.5f + phase));
        target.intensity = baseIntensity * dropout * (1f + noise * amount);
    }
}
