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
        // Volumetric light only adds energy. Additive blending prevents the
        // transparent proxy from tinting the room dark when it intersects a
        // doorway or when Unity's scene fog is dense.
        Blend One One
        Cull Off
        ZWrite Off
        ZTest LEqual

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
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
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
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
                // The mesh only carries front/back soft sheets. Fade fully at
                // their boundaries so the sheet never reads as a rectangle in
                // the room or across a doorway.
                half edgeFade = 1.0h - smoothstep(0.30h, 0.96h, edgeDistance);
                half softVariation = 0.90h + 0.10h * sin((i.uv.x + i.uv.y * 1.7h) * 18.0h);
                half alpha = saturate(_Density * _DiffuseCoefficient * heightFade * edgeFade * softVariation);
                fixed4 color = _Color * alpha;
                color.a = alpha;
                return color;
            }
            ENDCG
        }
    }
    FallBack Off
}
