using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TerrainCreator : MonoBehaviour
{
    public GameObject prototypesAsset;
    public TextAsset prototypesDataFile;
    public Vector3Int mapSize = new Vector3Int(20, 1, 20);

    private GameObject prototypePrefab;
    private Prototype[] prototypes;
    private GameObject[,,] terrainGrid;

    private void Awake() {
        prototypePrefab = Resources.Load<GameObject>("WFC/Prototype");
    }

    private void Start() {
        if (mapSize.x <= 0 || mapSize.y <= 0 || prototypesAsset == null || prototypesDataFile == null) {
            Debug.LogError("Terrain sizes can't be negative or null");
            this.enabled = false;
            return;
        }

        // Getting labelling data from JSON and attaching meshes to it.
        prototypes = PrototypeDataWrapper.CreateFromJSON(prototypesDataFile.ToString()).data;
        for (int i = 0; i < prototypes.Length; i++) {
            foreach(Transform t in prototypesAsset.transform) {
                if (t.name == prototypes[i].name) {
                    prototypes[i].mesh = t.GetComponent<MeshFilter>().sharedMesh;
                }
            }
        }

        // Setting up grid for prototype placement
        terrainGrid = new GameObject[mapSize.x, mapSize.y, mapSize.z];

        // Grid filling test
        for (int x = 0; x < terrainGrid.GetLength(0); x++) {
            for (int y = 0; y < terrainGrid.GetLength(1); y++) {
                for (int z = 0; z < terrainGrid.GetLength(2); z++) {
                    terrainGrid[x,y,z] = Instantiate<GameObject>(prototypePrefab, this.transform);
                    terrainGrid[x,y,z].transform.position = new Vector3(x,y,z);
                    terrainGrid[x,y,z].GetComponent<MeshFilter>().mesh = prototypes[1].mesh;
                }
            }
        }
    }
}
