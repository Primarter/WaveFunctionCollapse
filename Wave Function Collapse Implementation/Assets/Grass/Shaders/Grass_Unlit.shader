Shader "Custom/Grass_Unlit"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (0.0, 0.15, 0.0, 1.0)
        _TipColor ("Tip Color", Color) = (0.0, 1.0, 0.0, 1.0)

        _BendDelta ("Bend", Range(0, 1)) = 0.15

        _WindMap("Wind Offset Map", 2D) = "bump" {}
        _WindVelocity("Wind Velocity", Range(0, 1)) = 0.2
        _WindFrequency("Wind Pulse Frequency", Range(0, 1)) = 0.01
    }

    SubShader
    {
        Tags {
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
            "RenderPipeline" = "UniversalPipeline"
        }

        Pass
        {
            Cull Off // disable face culling

            HLSLPROGRAM

            #pragma vertex vert
            #pragma fragment frag

            #include "utils.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            #pragma multi_compile _MAIN_LIGHT_SHADOWS
            #pragma multi_compile _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _SHADOWS_SOFT
            // #pragma multi_compile _ _MAIN_LIGHT_SHADOWS
            // #pragma multi_compile _ _MAIN_LIGHT_SHADOWS_CASCADE
            // #pragma multi_compile _ _SHADOWS_SOFT

            // #pragma multi_compile_fog
            #pragma multi_compile_instancing

            struct GrassBlade {
                float3 position;
                // float4 rot;
            };

            struct VertexInput
            {
                float4 vertex   : POSITION;
                float3 normal   : NORMAL;
                float2 uv       : TEXCOORD0;
                uint instanceID : SV_InstanceID;
            };

            struct VertexOutput
            {
                float4 positionHCS  : SV_POSITION;
                float3 positionWS   : TEXCOORD0;
                // float3 normal       : TEXCOORD1;
                float2 uv           : TEXCOORD1;
            };

            CBUFFER_START(UnityPerMaterial)
                float4 _Color;
                float4 _BaseColor;
                float4 _TipColor;
                float _BendDelta;

                sampler2D _WindMap;
				float4 _WindMap_ST;
				float _WindVelocity;
				float  _WindFrequency;
            CBUFFER_END

            #ifdef SHADER_API_D3D11
                StructuredBuffer<GrassBlade> _grass;
            #endif

            #define PI_2 (PI*2.0)

            VertexOutput vert(VertexInput IN)
            {
                VertexOutput OUT;

                float3 instance_pos = _grass[IN.instanceID].position;
                float3 pos = IN.vertex.xyz;

                float rd = rand(instance_pos.xz);

                float3x3 randRotMatrix = angleAxis3x3(rd * PI_2, float3(0, 1, 0));
                float3x3 randBendMatrix = angleAxis3x3(rd * _BendDelta * PI * 0.5f, float3(-1.0f, 0, 0));

                float2 windUV = instance_pos.xz * _WindMap_ST.xy + _WindFrequency * _Time.y;

                // using texture (BUG)
                // float2 windSample = (tex2Dlod(_WindMap, float4(windUV, 0, 0)).xy * 2 - 1) * _WindVelocity;
                // float3 windAxis = float3(windSample.x, windSample.y, 0);
                // float3x3 windMatrix = angleAxis3x3(PI * windSample, windAxis);

                // using simplex noise
                float noiseValue = snoise(float3(windUV, 1.0)) * _WindVelocity;
                float2 windSample = float2(cos(noiseValue), sin(noiseValue));
                float3 windAxis = normalize(float3(windSample.x, windSample.y, 0));
                float3x3 windMatrix = angleAxis3x3(PI * noiseValue * IN.uv.y, windAxis);


                float3x3 finalMatrix = mul(mul(randBendMatrix, randRotMatrix), windMatrix);

                pos = mul(pos, finalMatrix);

                // float3 cameraDir = UNITY_MATRIX_V[2].xyz = mul((float3x3)UNITY_MATRIX_V,float3(0,0,1));
                float3 cameraDir = UNITY_MATRIX_IT_MV[2].xyz;

                float3 normal = mul(IN.normal, finalMatrix);
                float viewNormalDelta = abs(dot(normal, cameraDir));

                if (viewNormalDelta < 0.2) { // if almost orthogonal to view vector

                }

                pos += instance_pos;

                OUT.positionWS = TransformObjectToWorld(pos);
                OUT.positionHCS = TransformObjectToHClip(pos);
                // OUT.positionHCS = TransformWorldToHClip(pos);

                OUT.uv = IN.uv;
                // OUT.normal = mul(IN.normal, finalMatrix);

                return OUT;
            }

            float4 frag(VertexOutput IN) : SV_Target
            {
                float4 color = lerp(_BaseColor, _TipColor, IN.uv.y);
                // float4 color = float4(IN.uv, 0.0, 1.0);

                // float3 lightDir = GetMainLight().direction;

                #ifdef _MAIN_LIGHT_SHADOWS
                    VertexPositionInputs vertexInput;// = (VertexPositionInputs)0;
                    vertexInput.positionWS = IN.positionWS;

                    float4 shadowCoord = GetShadowCoord(vertexInput);
                    half shadowAttenuation = saturate(MainLightRealtimeShadow(shadowCoord) + 0.25f);
                    float4 shadowColor = lerp(0.0f, 1.0f, shadowAttenuation);
                    color *= shadowColor;
                #endif

                return color;
            }
            ENDHLSL
        }
    }
}
