Shader "Custom/Grass_CustomLit_BAD"
{
    Properties
    {
        _FootColor ("Foot Color", Color) = (0.0, 0.15, 0.0, 1.0)
        _TipColor ("Tip Color", Color) = (0.0, 1.0, 0.0, 1.0)

        _BendDelta ("Bend", Range(0, 1)) = 0.15

        _WindMap("Wind Offset Map", 2D) = "bump" {}
        _WindVelocity("Wind Velocity", Range(0, 1)) = 0.2
        _WindFrequency("Wind Pulse Frequency", Range(0, 1)) = 0.01

        // [Space(20)]
        // [Toggle(_SPECULAR_SETUP)] _MetallicSpecToggle ("Workflow, Specular (if on), Metallic (if off)", Float) = 0
        // [Toggle(_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A)] _SmoothnessSource ("Smoothness Source, Albedo Alpha (if on) vs Metallic (if off)", Float) = 0
        // _Metallic("Metallic", Range(0.0, 1.0)) = 0
        // _Smoothness("Smoothness", Range(0.0, 1.0)) = 0.5
        // _SpecColor("Specular Color", Color) = (0.5, 0.5, 0.5, 0.5)
        // [Toggle(_METALLICSPECGLOSSMAP)] _MetallicSpecGlossMapToggle ("Use Metallic/Specular Gloss Map", Float) = 0
        // _MetallicSpecGlossMap("Specular or Metallic Map", 2D) = "black" {}
        // // Usually this is split into _SpecGlossMap and _MetallicGlossMap, but I find
        // // that a bit annoying as I'm not using a custom ShaderGUI to show/hide them.

        // [Space(20)]
        // [Toggle(_NORMALMAP)] _NormalMapToggle ("Use Normal Map", Float) = 0
        // [NoScaleOffset] _BumpMap("Normal Map", 2D) = "bump" {}
        // _BumpScale("Bump Scale", Float) = 1

        // // Not including Height (parallax) map in this example/template

        // [Space(20)]
        // [Toggle(_OCCLUSIONMAP)] _OcclusionToggle ("Use Occlusion Map", Float) = 0
        // [NoScaleOffset] _OcclusionMap("Occlusion Map", 2D) = "bump" {}
        // _OcclusionStrength("Occlusion Strength", Range(0.0, 1.0)) = 1.0

        // [Space(20)]
        // [Toggle(_EMISSION)] _Emission ("Emission", Float) = 0
        // [HDR] _EmissionColor("Emission Color", Color) = (0,0,0)
        // [NoScaleOffset]_EmissionMap("Emission Map", 2D) = "black" {}

        // [Space(20)]
        // [Toggle(_SPECULARHIGHLIGHTS_OFF)] _SpecularHighlights("Turn Specular Highlights Off", Float) = 0
        // [Toggle(_ENVIRONMENTREFLECTIONS_OFF)] _EnvironmentalReflections("Turn Environmental Reflections Off", Float) = 0
    }

    SubShader
    {
        Tags {
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
            "RenderPipeline" = "UniversalPipeline"
        }

        HLSLINCLUDE
		#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        CBUFFER_START(UnityPerMaterial)
            float4 _FootColor;
            float4 _TipColor;
            float _BendDelta;

            sampler2D _WindMap;
            float4 _WindMap_ST;
            float _WindVelocity;
            float  _WindFrequency;

            // PBR //
            // float4 _BaseMap_ST;
            // float4 _BaseColor;
            // float4 _EmissionColor;
            // float4 _SpecColor;
            // float _Metallic;
            // float _Smoothness;
            // float _OcclusionStrength;
            // float _Cutoff;
            // float _BumpScale;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Off // disable face culling

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag


            // ---------------------------------------------------------------------------
            // Keywords
            // ---------------------------------------------------------------------------

            // Material Keywords
            #pragma shader_feature_local _NORMALMAP
            #pragma shader_feature_local_fragment _ALPHATEST_ON
            #pragma shader_feature_local_fragment _ALPHAPREMULTIPLY_ON
            #pragma shader_feature_local_fragment _EMISSION
            #pragma shader_feature_local_fragment _METALLICSPECGLOSSMAP
            #pragma shader_feature_local_fragment _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A
            #pragma shader_feature_local_fragment _OCCLUSIONMAP

            #pragma shader_feature_local_fragment _SPECULARHIGHLIGHTS_OFF
            #pragma shader_feature_local_fragment _ENVIRONMENTREFLECTIONS_OFF
            #pragma shader_feature_local_fragment _SPECULAR_SETUP
            #pragma shader_feature_local _RECEIVE_SHADOWS_OFF

            // URP Keywords
            // #pragma multi_compile _ _MAIN_LIGHT_SHADOWS
            // #pragma multi_compile _ _MAIN_LIGHT_SHADOWS_CASCADE
            // Note, v11 changes these to :
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN

            // #pragma multi_compile _MAIN_LIGHT_SHADOWS
            // #pragma multi_compile _MAIN_LIGHT_SHADOWS_CASCADE
            // #pragma multi_compile _SHADOWS_SOFT
            // #pragma multi_compile _ _MAIN_LIGHT_SHADOWS
            // #pragma multi_compile _ _MAIN_LIGHT_SHADOWS_CASCADE
            // #pragma multi_compile _ _SHADOWS_SOFT

            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION // v10+ only (for SSAO support)
            #pragma multi_compile _ LIGHTMAP_SHADOW_MIXING // v10+ only, renamed from "_MIXED_LIGHTING_SUBTRACTIVE"
            #pragma multi_compile _ SHADOWS_SHADOWMASK // v10+ only

            // Unity Keywords
            #pragma multi_compile _ LIGHTMAP_ON
            #pragma multi_compile _ DIRLIGHTMAP_COMBINED
            #pragma multi_compile_fog

            // #pragma multi_compile_instancing

            #include "utils.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"


            struct GrassBlade {
                float3 position;
                // float4 rot;
            };

            struct Attributes
            {
                float4 positionOS	: POSITION;
                #ifdef _NORMALMAP
                    float4 tangentOS 	: TANGENT;
                #endif
                float4 normalOS		: NORMAL;
                float2 uv		    : TEXCOORD0;
                float2 lightmapUV	: TEXCOORD1;
                float4 color		: COLOR;

                uint instanceID : SV_InstanceID;
            };

            struct Varyings
            {
                float4 positionCS 					: SV_POSITION;
                // float2 uv		    				: TEXCOORD0;
                // DECLARE_LIGHTMAP_OR_SH(lightmapUV, vertexSH, 1);
                // float3 positionWS					: TEXCOORD2;

                // #ifdef _NORMALMAP
                //     half4 normalWS					: TEXCOORD3;    // xyz: normal, w: viewDir.x
                //     half4 tangentWS					: TEXCOORD4;    // xyz: tangent, w: viewDir.y
                //     half4 bitangentWS				: TEXCOORD5;    // xyz: bitangent, w: viewDir.z
                // #else
                //     half3 normalWS					: TEXCOORD3;
                // #endif

                // #ifdef _ADDITIONAL_LIGHTS_VERTEX
                //     half4 fogFactorAndVertexLight	: TEXCOORD6; // x: fogFactor, yzw: vertex light
                // #else
                //     half  fogFactor					: TEXCOORD6;
                // #endif

                // #if defined(REQUIRES_VERTEX_SHADOW_COORD_INTERPOLATOR)
                //     float4 shadowCoord 				: TEXCOORD7;
                // #endif

                float4 color						: COLOR;
                //UNITY_VERTEX_INPUT_INSTANCE_ID
                //UNITY_VERTEX_OUTPUT_STEREO
            };

            #ifdef SHADER_API_D3D11
                StructuredBuffer<GrassBlade> _grass;
            #endif

            #define PI_2 (PI*2.0)

            // #include "PBRSurface.hlsl"
            // #include "PBRInput.hlsl"

            half3 ApplySingleDirectLight(Light light, half3 N, half3 V, half3 albedo, half positionOSY)
            {
                half3 H = normalize(light.direction + V);

                //direct diffuse
                half directDiffuse = dot(N, light.direction) * 0.5 + 0.5; //half lambert, to fake grass SSS

                //direct specular
                float directSpecular = saturate(dot(N,H));
                //pow(directSpecular,8)
                directSpecular *= directSpecular;
                directSpecular *= directSpecular;
                directSpecular *= directSpecular;
                //directSpecular *= directSpecular; //enable this line = change to pow(directSpecular,16)

                //add direct directSpecular to result
                directSpecular *= 0.1 * positionOSY;//only apply directSpecular to grass's top area, to simulate grass AO

                half3 lighting = light.color * (light.shadowAttenuation * light.distanceAttenuation);
                half3 result = (albedo * directDiffuse + directSpecular) * lighting;
                return result;
            }

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                // UNITY_SETUP_INSTANCE_ID(IN);

                // -- //
                    float3 instance_pos = _grass[IN.instanceID].position;
                    float3 pos = IN.positionOS.xyz;

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
                    pos += instance_pos;
                // -- //

                // float3 cameraTransformRightWS = UNITY_MATRIX_V[0].xyz;//UNITY_MATRIX_V[0].xyz == world space camera Right unit vector
                // float3 cameraTransformUpWS = UNITY_MATRIX_V[1].xyz;//UNITY_MATRIX_V[1].xyz == world space camera Up unit vector
                // float3 cameraTransformForwardWS = -UNITY_MATRIX_V[2].xyz;//UNITY_MATRIX_V[2].xyz == -1 * world space camera Forward unit vector

                float3 cameraDir = UNITY_MATRIX_IT_MV[2].xyz;

                // float3 perGrassPivotPosWS = float3(rd * _BendDelta * PI * 0.5f, 0.0, rd*PI_2);
                // float3 randomAddToN = (0.15 * sin(perGrassPivotPosWS.x * 82.32523 + perGrassPivotPosWS.z)) * cameraTransformRightWS;//random normal per grass
                // float3 N = normalize(float3(0, 1, 0) + randomAddToN - cameraTransformForwardWS*0.5);

                float3 N = float3(0.0, 1.0, 0.0);
                // float3 N = mul(float3(0.0, 1.0, 0.0), finalMatrix);

                // float3 vd = pos - _WorldSpaceCameraPos;
                float3 vd = _WorldSpaceCameraPos - pos;

                // invert normal if looking away from light source //
                // float3 cameraDir = UNITY_MATRIX_IT_MV[2].xyz;
                // if (dot(normalInputs.normalWS, GetMainLight().direction.xyz) < 0) {
                //     normalInputs.normalWS = -normalInputs.normalWS;
                // }

                float4 positionCS = TransformObjectToHClip(pos);
                float3 positionWS = TransformObjectToWorld(pos);

                OUT.positionCS = positionCS;
                // OUT.positionWS = positionWS;

                //lighting data
                Light mainLight;
                #if _MAIN_LIGHT_SHADOWS
                    mainLight = GetMainLight(TransformWorldToShadowCoord(positionWS));
                #else
                    mainLight = GetMainLight();
                #endif


                half3 V = cameraDir;//viewWS / ViewWSLength;

                // half3 baseColor = tex2Dlod(_BaseColorTexture, float4(TRANSFORM_TEX(positionWS.xz,_BaseColorTexture),0,0)) * _BaseColor;//sample mip 0 only
                half3 albedo = lerp(_FootColor.xyz, _TipColor.xyz, IN.uv.y);

                //indirect
                half3 lightingResult = SampleSH(0) * albedo;

                //main direct light
                lightingResult += ApplySingleDirectLight(mainLight, N, vd, albedo, IN.positionOS.y); //or IN.uv.y
                // lightingResult += ApplySingleDirectLight(mainLight, N, V, albedo, IN.uv.y); //or IN.uv.y


                // OUT.uv = IN.uv;
                OUT.color = float4(lightingResult, 1.0);

                return OUT;
            }

            float4 frag(Varyings IN) : SV_Target
            {
                float4 color = IN.color;

                return color;
            }
            ENDHLSL
        }
    }
}
