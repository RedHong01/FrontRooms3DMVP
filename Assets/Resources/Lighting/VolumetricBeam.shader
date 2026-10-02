Shader "FrontRooms/VolumetricBeam"
{
    Properties
    {
        _Color ("Beam color", Color) = (1, 0.93, 0.74, 1)
        _Density ("Density", Range(0, 1)) = 0.13
        _DiffuseCoefficient ("Diffuse coefficient", Range(0, 1)) = 0.82
    }
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        // Volumetric light only adds energy. Additive blending prevents the
        // transparent proxy from tinting the room dark when it intersects a
        // doorway or when the scene fog is dense.
        Blend One One
        Cull Off
        ZWrite Off
        ZTest LEqual

        Pass
        {
            Name "VolumetricBeam"
            Tags { "LightMode" = "UniversalForward" }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _Density;
                half _DiffuseCoefficient;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                half fog : TEXCOORD1;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes input)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                o.uv = input.uv;
                o.fog = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                // The frustum carries a simple height coordinate. Fade at the
                // ceiling and floor, then soften each side so the volume never
                // produces a hard polygon or an exposed diagonal edge.
                half heightFade = smoothstep(0.015h, 0.20h, i.uv.y)
                    * (1.0h - smoothstep(0.78h, 1.0h, i.uv.y));
                half edgeDistance = abs(i.uv.x * 2.0h - 1.0h);
                half edgeFade = 1.0h - smoothstep(0.30h, 0.96h, edgeDistance);
                half softVariation = 0.90h + 0.10h * sin((i.uv.x + i.uv.y * 1.7h) * 18.0h);
                half alpha = saturate(_Density * _DiffuseCoefficient * heightFade * edgeFade * softVariation);
                half3 color = _Color.rgb * alpha;
                // Additive light fades toward black (no added energy) in fog.
                color = MixFogColor(color, half3(0, 0, 0), i.fog);
                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
