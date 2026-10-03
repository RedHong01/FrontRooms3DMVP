using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>URP RenderGraph pass that composites the native RT texture.</summary>
public sealed class FrontRoomsMetalGlassRTRendererFeature : ScriptableRendererFeature
{
    FrontRoomsMetalGlassRTPass pass;
    Material material;

    public override void Create()
    {
        var shader = Shader.Find("Hidden/FrontRooms/MetalGlassRTComposite");
        if (shader != null) material = CoreUtils.CreateEngineMaterial(shader);
        pass = new FrontRoomsMetalGlassRTPass(material)
        {
            renderPassEvent = RenderPassEvent.AfterRenderingPostProcessing
        };
    }

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        var controller = FrontRoomsMetalGlassRTController.Instance;
        if (controller == null || !controller.IsReady || material == null) return;
        pass.Controller = controller;
        renderer.EnqueuePass(pass);
    }

    protected override void Dispose(bool disposing)
    {
        CoreUtils.Destroy(material);
        material = null;
    }
}
