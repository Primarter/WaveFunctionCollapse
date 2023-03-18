using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TerrainCreator : MonoBehaviour
{
    public GameObject prototypesAsset;
    public TextAsset prototypesDataFile;
    public Vector2Int mapSize = new Vector2Int(20, 20);

    private Prototype[] prototypes;

    private void Start() {
        if (mapSize.x <= 0 || mapSize.y <= 0 || prototypesAsset == null || prototypesDataFile == null) {
            Debug.LogError("Terrain sizes can't be negative or null");
            this.enabled = false;
            return;
        }
        Debug.Log(prototypesAsset.transform.childCount);
        foreach (Transform t in prototypesAsset.transform) {
            Debug.Log(t.name);
        }
        prototypes = PrototypeDataWrapper.CreateFromJSON(prototypesDataFile.ToString()).data;
        for (int i = 0; i < prototypes.Length; i++) {
            foreach(Transform t in prototypesAsset.transform) {
                if (t.name == prototypes[i].name)
                    prototypes[i].mesh = t.GetComponent<MeshFilter>().sharedMesh;
            }
        }
    }
}
