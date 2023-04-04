Shader "Custom/Grass_CustomLit"
{
    Properties
    {
        _TipColor("Tip Color", Color) = (1, 1, 1)
        _Color1("Color 1", Color) = (1, 1, 1) // tall grass
        // _Color2("Color 2", Color) = () // small grass
        _AOColor("Ambient Occlusion color", Color) = (1, 1, 1) // color to blend bottom with the ground

        // _FootColor ("Foot Color", Color) = (0.0, 0.15, 0.0, 1.0)
        // _TipColor ("Tip Color", Color) = (0.0, 0.83, 0.0, 1.0)

        _BendDelta ("Bend", Range(0, 1)) = 0.15

        _WindMap("Wind Offset Map", 2D) = "bump" {}
        _WindVelocity("Wind Velocity", Range(0, 1)) = 0.2
        _WindFrequency("Wind Pulse Frequency", Range(0, 1)) = 0.01

        _grassWidth("Grass Width", Range(0.01, 0.3)) = 0.05
        _grassHeight("Grass height", Range(0.1, 5)) = 1.0
        _grassRandomHeight("Grass random height multiplier", Range(0.0, 0.5)) = 0.1
        // _DEBUG("DEBUG", Int) = 0
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

            // #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            #pragma multi_compile _MAIN_LIGHT_SHADOWS
            #pragma multi_compile _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _SHADOWS_SOFT

            // #pragma multi_compile_fog
            // #pragma multi_compile_instancing

            struct GrassBlade {
                float3 position;
                // float4 rot;
            };

            struct Attributes
            {
                float4 vertex   : POSITION;
                float3 normal   : NORMAL;
                float2 uv       : TEXCOORD0;
                uint instanceID : SV_InstanceID;
            };

            struct Varyings
            {
                float4 positionCS  : SV_POSITION;
                float3 positionWS  : TEXCOORD0;
                float2 uv          : TEXCOORD1;
                float3 grassNormal : TEXCOORD2;
                float3 modelNormal : TEXCOORD3;
            };

            CBUFFER_START(UnityPerMaterial)
                float3 _Color1;
                // float3 _Color2;
                float3 _TipColor;
                float3 _AOColor;
                // float4 _TipColor;
                // float4 _FootColor;

                float _BendDelta;

                // int _DEBUG;

                sampler2D _WindMap;
				float4 _WindMap_ST;
				float _WindVelocity;
				float  _WindFrequency;
                float _grassWidth;
                float _grassHeight;
                float _grassRandomHeight;
            CBUFFER_END

            #ifdef SHADER_API_D3D11
                StructuredBuffer<GrassBlade> _grass;
            #endif

            #define PI_2 (PI*2.0)

            Varyings vert(Attributes IN)
            {
                Varyings OUT;

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
                float3x3 globalWindMatrix = angleAxis3x3(PI * noiseValue, windAxis); // to have uvs affect normals calculations

                float3x3 finalMatrix = mul(mul(randBendMatrix, randRotMatrix), windMatrix);
                float3x3 globalFinalMatrix = mul(mul(randBendMatrix, randRotMatrix), globalWindMatrix); // to have uvs affect normals calculations

                pos.x *= _grassWidth;
                pos.y *= _grassHeight - (rd*_grassRandomHeight);

                float2 uv = instance_pos.xz * 0.2;
                pos.y *= (snoise(float3(uv.x, 0, uv.y)) * 0.5 + 0.5) + 1.0;

                pos = mul(pos, finalMatrix);
                pos += instance_pos;

                float3 modelNormal = mul(IN.normal, globalFinalMatrix);
                // float3 modelNormal = mul(rounded(IN.uv.x), globalFinalMatrix);
                // float3 roundedModelNormal = rounded(IN.uv.x);
                float3 grassNormal = float3(0.0, 1.0, 0.0);

                Light light = GetMainLight();
                if (dot(modelNormal, -light.direction) < 0.0) {
                    modelNormal = -modelNormal;
                    // roundedModelNormal.z *= -1.0;
                }

                OUT.positionWS = TransformObjectToWorld(pos);
                OUT.positionCS = TransformObjectToHClip(pos); //TransformWorldToHClip(pos);

                OUT.uv = IN.uv;
                OUT.modelNormal = modelNormal;
                OUT.grassNormal = grassNormal;

                return OUT;
            }

            float4 frag(Varyings IN) : SV_Target
            {
                float noiseHeight = 0.0;
                // float3 grassColor = lerp(_FootColor.xyz, _TipColor.xyz, IN.uv.y);
                float3 grassColor = lerp(_Color1, float3(1,1,1), noiseHeight);
                // float3 grassColor = lerp(_Color1, _TipColor.xyz, noiseHeight);

                float3 ao = lerp(_AOColor, 1.0, IN.uv.y);
                float3 tip = lerp(0.0, _TipColor, IN.uv.y*IN.uv.y);

                grassColor = lerp(grassColor, tip, IN.uv.y);

                Light light = GetMainLight();

                half3 ambiant = half3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w);// * light.color;
                float diff = max(0.0, dot(light.direction, IN.grassNormal));
                float3 diffuse = diff * light.color;

                // specular
                float specularStrength = 1.0;
                float3 viewDir = normalize(_WorldSpaceCameraPos - IN.positionWS);
                float3 reflectDir = reflect(-light.direction, IN.grassNormal);
                float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
                float3 specular = specularStrength * spec * light.color;

                half3 V = _WorldSpaceCameraPos;
                half3 H = normalize(light.direction + V);
                float directSpecular = saturate(dot(IN.modelNormal, H));
                directSpecular *= directSpecular;
                directSpecular *= directSpecular;
                directSpecular *= directSpecular;

                specular *= directSpecular;
                specular *= pow(IN.uv.y, 2.0); // only at the tip of grass blades

                // float3 color = (specular) * grassColor;
                float3 color = (ambiant + diffuse) * (grassColor * ao);
                // float3 color = (ambiant + diffuse) * (grassColor + tip) * ao;
                // float3 color = (ambiant + diffuse + specular) * grassColor;

                #ifdef _MAIN_LIGHT_SHADOWS
                    VertexPositionInputs vertexInput;// = (VertexPositionInputs)0;
                    vertexInput.positionWS = IN.positionWS;

                    float4 shadowCoord = GetShadowCoord(vertexInput);
                    half shadowAttenuation = saturate(MainLightRealtimeShadow(shadowCoord) + 0.25f);
                    float4 shadowColor = lerp(0.0f, 1.0f, shadowAttenuation);
                    color *= shadowColor.xyz;
                #endif

                return float4(color, 1.0);
                // return float4(IN.uv, 0.0, 1.0);
                // return float4(IN.modelNormal, 1.0); // TODO: rounded blade normal
                // return float4(IN.modelNormal*0.5+0.5, 1.0); // TODO: rounded blade normal
            }
            ENDHLSL
        }
    }
}
