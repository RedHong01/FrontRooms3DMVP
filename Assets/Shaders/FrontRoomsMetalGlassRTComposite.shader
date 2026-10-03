Shader "Hidden/FrontRooms/MetalGlassRTComposite"
{
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }
        Pass
        {
            Name "Composite"
            ZTest Always
            ZWrite Off
            Cull Off
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_FrontRoomsMetalGlassRT);
            float _FrontRoomsMetalGlassRTStrength;

            struct Attributes
            {
                uint vertexID : SV_VertexID;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.uv = float2((input.vertexID << 1) & 2, input.vertexID & 2);
                output.positionCS = float4(output.uv * 2.0 - 1.0, 0.0, 1.0);
                output.uv.y = 1.0 - output.uv.y;
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                half4 reflection = SAMPLE_TEXTURE2D(_FrontRoomsMetalGlassRT, sampler_LinearClamp, input.uv);
                reflection.a = saturate(reflection.a * _FrontRoomsMetalGlassRTStrength);
                return reflection;
            }
            ENDHLSL
        }
    }
}
