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
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Blend SrcAlpha OneMinusSrcAlpha
        Cull Off
        ZWrite Off
        ZTest LEqual

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "UnityCG.cginc"

            fixed4 _Color;
            half _Density;
            half _DiffuseCoefficient;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_FOG_COORDS(1)
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                UNITY_TRANSFER_FOG(o, o.vertex);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                // The frustum carries a simple height coordinate. Fade at the
                // ceiling and floor, then soften each side so the volume never
                // produces a hard polygon or an exposed diagonal edge.
                half heightFade = smoothstep(0.015h, 0.20h, i.uv.y)
                    * (1.0h - smoothstep(0.78h, 1.0h, i.uv.y));
                half edgeDistance = abs(i.uv.x * 2.0h - 1.0h);
                // Side faces use a constant U at their outer edge. Keep a
                // soft residual there so the frustum remains visible when
                // viewed obliquely, while the front/back faces still fade at
                // their broad edges.
                half edgeFade = lerp(0.62h, 1.0h, 1.0h - smoothstep(0.52h, 1.0h, edgeDistance));
                half softVariation = 0.90h + 0.10h * sin((i.uv.x + i.uv.y * 1.7h) * 18.0h);
                half alpha = saturate(_Density * _DiffuseCoefficient * heightFade * edgeFade * softVariation);
                fixed4 color = _Color;
                color.a *= alpha;
                UNITY_APPLY_FOG(i.fogCoord, color);
                return color;
            }
            ENDCG
        }
    }
    FallBack Off
}
