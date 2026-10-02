// FrontRooms surface: URP physically based shading with the room materials
// projected in world metres. Walls, floors and ceilings take their UVs from the
// world position and the face normal, so a pattern runs continuously across
// every slab and keeps the same printed scale everywhere. Tile sizes are chosen
// to divide the room stream's 256 m origin rebase, so a rebase never shifts a
// pattern. Large-scale wear (discolouration, damp carpet, water streaks under
// the ceiling, dirt along the floor) is sampled at 8 m and 12.8 m in world
// space on top of the tile, which hides the tile repeat.
Shader "FrontRooms/Surface"
{
    Properties
    {
        [MainTexture] _BaseMap ("Albedo", 2D) = "white" {}
        [MainColor] _BaseColor ("Tint", Color) = (1, 1, 1, 1)
        [Normal] _BumpMap ("Normal", 2D) = "bump" {}
        _BumpScale ("Normal strength", Range(0, 2)) = 1
        _MaskMap ("Mask (R smoothness, G cavity)", 2D) = "white" {}
        _Smoothness ("Smoothness scale", Range(0, 2)) = 1
        _Metallic ("Metallic", Range(0, 1)) = 0
        _OcclusionStrength ("Cavity strength", Range(0, 1)) = 0.8
        _TileSize ("Tile size in metres (xy)", Vector) = (1, 1, 0, 0)
        [Toggle(_FR_MESH_UV)] _MeshUV ("Use mesh UVs (metres) instead of world projection", Float) = 0

        _MacroMap ("Macro wear (R tone, G dirt, B damp, A streaks)", 2D) = "gray" {}
        _MacroTone ("Macro discolouration", Range(0, 1)) = 0.35
        _MacroDirt ("Macro dirt", Range(0, 1)) = 0.25
        _StainColor ("Stain colour", Color) = (0.42, 0.31, 0.16, 1)
        _StainStrength ("Water stains", Range(0, 1)) = 0
        _WetStrength ("Damp patches (floors)", Range(0, 1)) = 0
        _FloorGrime ("Grime along the floor (walls)", Range(0, 1)) = 0
        _FloorGrimeHeight ("Floor grime height (m)", Float) = 0.35
        _CeilingGrime ("Streaks under the ceiling (walls)", Range(0, 1)) = 0
        _CeilingHeight ("Ceiling height (m)", Float) = 2.9

        [Toggle(_EMISSION)] _UseEmission ("Emission", Float) = 0
        _EmissionMap ("Emission", 2D) = "white" {}
        [HDR] _EmissionColor ("Emission colour", Color) = (0, 0, 0, 1)

        // Required by URP's shadow/depth passes.
        _Cutoff ("Alpha cutoff", Range(0, 1)) = 0.5
        [HideInInspector] _Cull ("__cull", Float) = 2
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "UniversalMaterialType" = "Lit" "Queue" = "Geometry" }
        LOD 300

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _BumpScale;
            half _Smoothness;
            half _Metallic;
            half _OcclusionStrength;
            float4 _TileSize;
            half _MacroTone;
            half _MacroDirt;
            half4 _StainColor;
            half _StainStrength;
            half _WetStrength;
            half _FloorGrime;
            float _FloorGrimeHeight;
            half _CeilingGrime;
            float _CeilingHeight;
            half4 _EmissionColor;
            half _Cutoff;
        CBUFFER_END

        // _BaseMap, _BumpMap and _EmissionMap come from URP's SurfaceInput,
        // which the shadow and depth passes below also rely on.
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/SurfaceInput.hlsl"
        TEXTURE2D(_MaskMap);      SAMPLER(sampler_MaskMap);
        TEXTURE2D(_MacroMap);     SAMPLER(sampler_MacroMap);
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull [_Cull]
            ZWrite On

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex Vert
            #pragma fragment Frag

            #pragma shader_feature_local _FR_MESH_UV
            #pragma shader_feature_local_fragment _EMISSION

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ EVALUATE_SH_MIXED EVALUATE_SH_VERTEX
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile _ _LIGHT_LAYERS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Fog.hlsl"
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float4 tangentOS  : TANGENT;
                float2 uv         : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                float4 tangentWS  : TEXCOORD2;
                float2 uv         : TEXCOORD3;
                half4 fogAndVertexLight : TEXCOORD4;
                DECLARE_LIGHTMAP_OR_SH(staticLightmapUV, vertexSH, 5);
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_TRANSFER_INSTANCE_ID(input, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                VertexPositionInputs p = GetVertexPositionInputs(input.positionOS.xyz);
                VertexNormalInputs n = GetVertexNormalInputs(input.normalOS, input.tangentOS);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = n.normalWS;
                o.tangentWS = float4(n.tangentWS, input.tangentOS.w * GetOddNegativeScale());
                o.uv = input.uv;
                half fog = ComputeFogFactor(p.positionCS.z);
                o.fogAndVertexLight = half4(fog, VertexLighting(p.positionWS, n.normalWS));
                OUTPUT_SH(o.normalWS, o.vertexSH);
                return o;
            }

            // World-planar frame: floors/ceilings use X/Z, walls run along the
            // wall with V up. B = cross(N, T) keeps the normal map unmirrored.
            void PlanarFrame(float3 positionWS, float3 n, out float2 uvMetres, out float3 t, out float3 b)
            {
                t = abs(n.y) > 0.5 ? float3(1, 0, 0) : normalize(cross(float3(0, 1, 0), n));
                b = cross(n, t);
                uvMetres = float2(dot(positionWS, t), dot(positionWS, b));
            }

            void Frag(Varyings input, out half4 outColor : SV_Target0
            #ifdef _WRITE_RENDERING_LAYERS
                , out uint outRenderingLayers : SV_Target1
            #endif
            )
            {
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float3 nGeo = normalize(input.normalWS);
                float2 metres;
                float3 t, b;
            #if defined(_FR_MESH_UV)
                metres = input.uv;
                t = normalize(input.tangentWS.xyz);
                b = input.tangentWS.w * cross(nGeo, t);
            #else
                PlanarFrame(input.positionWS, nGeo, metres, t, b);
            #endif
                float2 uv = metres / max(_TileSize.xy, 1e-3) * _BaseMap_ST.xy + _BaseMap_ST.zw;

                half4 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv) * _BaseColor;
                half4 mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, uv);
                half3 nTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, uv), _BumpScale);

                // Large-scale wear in world space (two scales, the second turned
                // 90 degrees). Both periods divide 256 m.
                float2 wearUV;
                float3 wt, wb;
                PlanarFrame(input.positionWS, nGeo, wearUV, wt, wb);
                half4 m1 = SAMPLE_TEXTURE2D(_MacroMap, sampler_MacroMap, wearUV / 8.0);
                half4 m2 = SAMPLE_TEXTURE2D(_MacroMap, sampler_MacroMap, float2(wearUV.y, -wearUV.x) / 12.8);
                half tone = lerp(1.0h, 0.84h + 0.30h * m1.r * m2.r, _MacroTone);
                half dirt = 1.0h - _MacroDirt * smoothstep(0.55h, 0.95h, m1.g * 0.6h + m2.g * 0.4h);
                albedo.rgb *= tone * dirt;

                // Water stains: soft tide-mark rings where the broad wear field crosses a band.
                // Only the top of the broad field stains, so tide marks are
                // occasional patches, not a ceiling-wide wash.
                half ring = smoothstep(0.70h, 0.73h, m2.r) * (1.0h - smoothstep(0.73h, 0.80h, m2.r));
                half pool = smoothstep(0.74h, 0.88h, m2.r);
                albedo.rgb = lerp(albedo.rgb, albedo.rgb * _StainColor.rgb * 1.6h, saturate((ring * 0.9h + pool * 0.35h) * _StainStrength));

                half smoothness = mask.r * _Smoothness;
                half cavity = lerp(1.0h, mask.g, _OcclusionStrength);

                // Damp carpet: darker, flatter, glossier.
                half wet = smoothstep(0.35h, 0.85h, m1.b * 0.7h + m2.b * 0.5h) * _WetStrength;
                albedo.rgb *= 1.0h - 0.32h * wet;
                smoothness = lerp(smoothness, 0.62h, wet);
                nTS = normalize(lerp(nTS, half3(0, 0, 1), wet * 0.7h));

                // Walls: dirt picked up along the floor, streaks from the ceiling grid.
                half wall = 1.0h - saturate(abs(nGeo.y) * 2.0h);
                half y = (half)input.positionWS.y;
                half floorBand = 1.0h - smoothstep(0.0h, (half)_FloorGrimeHeight, y);
                half ceilBand = smoothstep((half)_CeilingHeight - 1.6h, (half)_CeilingHeight, y);
                half streak = m1.a * ceilBand;
                albedo.rgb *= 1.0h - wall * (_FloorGrime * 0.35h * floorBand * (0.6h + 0.4h * m1.g));
                albedo.rgb = lerp(albedo.rgb, albedo.rgb * _StainColor.rgb * 1.5h, wall * saturate(_CeilingGrime * (streak * 0.8h + ceilBand * 0.15h)));

                InputData inputData = (InputData)0;
                inputData.positionWS = input.positionWS;
                inputData.positionCS = input.positionCS;
                half3x3 tbn = half3x3(t, b, nGeo);
                inputData.normalWS = NormalizeNormalPerPixel(TransformTangentToWorld(nTS, tbn));
                inputData.tangentToWorld = tbn;
                inputData.viewDirectionWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
            #if defined(MAIN_LIGHT_CALCULATE_SHADOWS)
                inputData.shadowCoord = TransformWorldToShadowCoord(input.positionWS);
            #else
                inputData.shadowCoord = float4(0, 0, 0, 0);
            #endif
                inputData.fogCoord = InitializeInputDataFog(float4(input.positionWS, 1.0), input.fogAndVertexLight.x);
                inputData.vertexLighting = input.fogAndVertexLight.yzw;
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                inputData.bakedGI = SampleSH(inputData.normalWS);
                inputData.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo.rgb;
                s.metallic = _Metallic;
                s.specular = half3(0, 0, 0);
                s.smoothness = saturate(smoothness);
                s.normalTS = nTS;
                s.occlusion = cavity;
                s.alpha = 1;
            #if defined(_EMISSION)
                s.emission = SAMPLE_TEXTURE2D(_EmissionMap, sampler_EmissionMap, uv).rgb * _EmissionColor.rgb;
            #endif

                half4 color = UniversalFragmentPBR(inputData, s);
                color.rgb = MixFog(color.rgb, inputData.fogCoord);
                color.a = 1;
                outColor = color;
            #ifdef _WRITE_RENDERING_LAYERS
                outRenderingLayers = EncodeMeshRenderingLayer();
            #endif
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex ShadowPassVertex
            #pragma fragment ShadowPassFragment
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/Shaders/ShadowCasterPass.hlsl"
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex DepthOnlyVertex
            #pragma fragment DepthOnlyFragment
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/Shaders/DepthOnlyPass.hlsl"
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            ZWrite On
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex DepthNormalsVertex
            #pragma fragment DepthNormalsFragment
            #pragma multi_compile_instancing
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/DepthNormalsPass.hlsl"
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
