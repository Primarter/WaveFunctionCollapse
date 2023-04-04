using System.Collections;
using System.Collections.Generic;
using UnityEngine;

struct GrassBlade {
    public Vector3 position; // 4*3 bytes
    // public Quaternion rot; // 4*4 bytes
}

public class GrassManager : MonoBehaviour
{
    [SerializeField] Material material;
    Mesh mesh;

    // float grassBladeWidth = 0.05f;
    float grassBladeHeight = 1.0f;

    // const int res = 128;
    // const float chunck_size = 10f;
    const int res = 128 * 4;
    const float chunck_size = 10f * 4;


    const float step = chunck_size / res;
    ComputeBuffer grass_buffer;
    int bladeCount = -1;

    void Start()
    {
        print("Start Grass!");
        Init();
    }

    void Init()
    {
        print("Initialize grass!");

        mesh = CreateMesh();

        // grass_buffer = new ComputeBuffer(res*res, (4*3 + 4*4) );
        grass_buffer = new ComputeBuffer(res*res, (4*3) );

        // GrassBlade[] blades = new GrassBlade[res*res];
        var blades = new List<GrassBlade>();

        // TODO: use raycast to find position and normal of grass blade and use texture mask to find if grass is needed
        LayerMask defaultMask = LayerMask.NameToLayer("Default");
        RaycastHit hit;

        for (int z = 0 ; z < res ; ++z) {
            for (int x = 0 ; x < res ; ++x) {
                int i = z * res + x;

                Vector3 pos = new Vector3((float)x * step, 0f, (float)z * step);

                bool didHit = Physics.Raycast(pos + new Vector3(0f, 10f, 0f), Vector3.down, out hit, Mathf.Infinity);
                if (didHit == false)
                    continue;

                print("HIT !!!");

                GrassBlade blade;
                blade.position = pos;
                // blades[i].position.y = Terrain.activeTerrain.SampleHeight(new Vector3(x, 0f, z) * step);

                // center mesh to origin ! (Mesh.bounds center change the model matrix of the mesh when rendering)
                blade.position += new Vector3(-chunck_size/2f, -grassBladeHeight/2f, -chunck_size/2f);

                Vector2 offset = Random.insideUnitCircle * step*0.5f;
                blade.position.x += offset.x;
                blade.position.z += offset.y;

                // blades[i].rot = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);
            }
        }

        print(blades.Count);
        // grass_buffer.SetData(blades);
        bladeCount = blades.Count;
        grass_buffer.SetData(blades, 0, 0, blades.Count);
        material.SetBuffer("_grass", grass_buffer);
    }

    Mesh CreateMesh()
    {
        Mesh mesh = new Mesh();

        Vector3[] vertices = {
            new Vector3(-0.5f, 0f, 0f),
            new Vector3(0.5f, 0f, 0f),
            new Vector3(0f, 1f, 0f),
        };

        Vector2[] uvs = {
            new Vector2(0.0f, 0.0f),
            new Vector2(1.0f, 0.0f),
            new Vector2(0.5f, 1.0f)
        };

        // Vector3[] normals = { // Upward pointing normals
        //     new Vector3(0.0f, -0.7f, 1.0f).normalized,
        //     new Vector3(0.7f, 0.0f, 1.0f).normalized,
        //     new Vector3(0.0f, 0.0f, 1.0f).normalized
        // };

        int[] triangles = {
            0, 1, 2
        };

        mesh.vertices = vertices;
        mesh.triangles = triangles;
        // mesh.normals = normals;
        mesh.uv = uvs;

        mesh.RecalculateNormals();
        mesh.RecalculateTangents();

        // set bounds manually because the geometry doesn't represent the entire mesh
        // var bounds = new Bounds(Vector3.zero, new Vector3(chunck_size, grassBladeHeight, chunck_size)); // centered bounding box
        var bounds = new Bounds();
        bounds.SetMinMax(new Vector3(0f, 0f, 0f), new Vector3(chunck_size, grassBladeHeight, chunck_size)); // could increase bounds a bit so grass that get out of bounds with wind don't get culled
        mesh.bounds = bounds;

        return mesh;
    }

    void Update()
    {
        Graphics.DrawMeshInstancedProcedural(
            mesh,
            0,
            material,
            mesh.bounds, //new Bounds(Vector3.zero, Vector3.one * 100000f),
            // res*res
            bladeCount
        );
    }

    void OnDestroy()
    {
        grass_buffer.Release();
    }
}
