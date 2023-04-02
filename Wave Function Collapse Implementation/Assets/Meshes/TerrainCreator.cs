using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Profiling;

public struct Superposition
{
    public List<Prototype> possibilites;
    public GameObject collapsedGameObj;
    public Prototype collapsedPrototype;
}

// TODO:
// Add weights to prototype choices
// See with Paul for plants
// Add vertical orientation to prototypes (two collections in Blender for easy solution, then a single one with normal computations)
// Check verticality: if upwards block is placed, either the column upwards is empty or the next block encountered is downwards
public class TerrainCreator : MonoBehaviour
{
    public GameObject prototypesAsset;
    public TextAsset prototypesDataFile;
    public Vector3Int mapSize = new Vector3Int(20, 1, 20);

    private GameObject prototypePrefab;
    private Prototype[] prototypes;
    private Superposition[,,] terrainGrid;
    private int uncollapsedCellsCount;
    private int minEntropy;
    private Vector3Int minEntropyPoint;
    private List<Vector3Int> minEntropyPoints = new List<Vector3Int>();

    private void Awake() {
        prototypePrefab = Resources.Load<GameObject>("WFC/Prototype");
    }

    private void Start() {
        if (mapSize.x <= 0 || mapSize.y <= 0 || mapSize.z <= 0 || prototypesAsset == null || prototypesDataFile == null) {
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
        terrainGrid = new Superposition[mapSize.x, mapSize.y, mapSize.z];

        // Filling superposition grid
        for (int x = 0; x < mapSize.x; x++) {
            for (int y = 0; y < mapSize.y; y++) {
                for (int z = 0; z < mapSize.z; z++) {
                    terrainGrid[x,y,z].possibilites = new List<Prototype>(prototypes);
                    terrainGrid[x,y,z].collapsedGameObj = null;
                }
            }
        }

        uncollapsedCellsCount = mapSize.x * mapSize.y * mapSize.z;
        // minEntropyPoint = mapSize/2;
        minEntropyPoints.Add(mapSize/2);
        minEntropy = prototypes.Length;

        // Profiler.BeginSample("Wave Function Collapse");
        // while (uncollapsedCellsCount > 0) {
        //     CollapseStep();
        // }
        // Profiler.EndSample();
    }

    private void Update() {
        // if (Input.GetKeyDown(KeyCode.Space) && uncollapsedCellsCount > 0) {
        if (uncollapsedCellsCount > 0) {
            CollapseStep();
        }
    }

    private void OnDrawGizmos() {
        Gizmos.color = Color.red;

        for (int x = 0; x < mapSize.x; x++) {
            for (int y = 0; y < mapSize.y; y++) {
                for (int z = 0; z < mapSize.z; z++) {
                    if (terrainGrid != null) {
                        #if UNITY_EDITOR
                        UnityEditor.Handles.color = Color.green;
                        UnityEditor.Handles.Label(new Vector3(x, y, z), terrainGrid[x,y,z].possibilites.Count.ToString());
                        #endif
                    }
                    Gizmos.DrawWireCube(new Vector3(x, y, z), Vector3.one);
                }
            }
        }
    }

    private void CollapseStep() {
        // TODO: Implement backtracking or restart algorithm
        // if (terrainGrid[minEntropyPoint.x, minEntropyPoint.y, minEntropyPoint.z].possibilites.Count == 0) {
        //     uncollapsedCellsCount -= 1;
        //     Debug.Log(("Error in propagation", minEntropyPoint));
        //     return;
        // }

        // Setting entropy point, either from list of entropy points or researching the whole grid
        if (minEntropyPoints.Count == 0) {
            ResetEntropy();
        }
        int chosenEntropy = UnityEngine.Random.Range(0, minEntropyPoints.Count);
        minEntropyPoint = minEntropyPoints[chosenEntropy];
        minEntropyPoints.RemoveAt(chosenEntropy);

        (int x, int y, int z) = (minEntropyPoint.x, minEntropyPoint.y, minEntropyPoint.z);

        CollapseCell(x,y,z);

        // Propagate collapse
        Stack<Vector3Int> stack = new Stack<Vector3Int>(); // cells to update
        stack.Push(minEntropyPoint);

        while (stack.Count > 0) { // While not fully propagated
            Propagate(stack);
        }

        terrainGrid[x,y,z].possibilites.Clear();
    }

    private void CollapseCell(int x, int y, int z) {
        // Create prefab
        terrainGrid[x,y,z].collapsedGameObj = Instantiate<GameObject>(prototypePrefab, this.transform); // Set prefab
        terrainGrid[x,y,z].collapsedGameObj.transform.position = new Vector3(x,y,z); // Set position of prefab

        if (terrainGrid[x,y,z].possibilites.Count == 0) {
            InstantiateEmpty(x,y,z);
            return;
        }

        // Choose random prototype in possibilities
        int chosenPossibilityIdx = UnityEngine.Random.Range(0, terrainGrid[x,y,z].possibilites.Count);
        Prototype chosenPrototype = terrainGrid[x,y,z].possibilites[chosenPossibilityIdx];

        if (y - 1 >= 0
            && terrainGrid[x, y - 1, z].collapsedPrototype != null
            && terrainGrid[x, y - 1, z].collapsedPrototype.face_profiles[5].id == -1) // Need to fix this so that it actually prevents overlapping blocks
        {
            chosenPrototype = prototypes[0];
        }

        // Set mesh and rotation of prefab from prototype
        terrainGrid[x,y,z].collapsedGameObj.GetComponent<MeshFilter>().mesh = chosenPrototype.mesh; // Assign mesh
        terrainGrid[x,y,z].collapsedGameObj.transform.rotation = Quaternion.Euler(0, 90 * chosenPrototype.rotation, 0); // Set rotation of prefab

        // Setup possibilities to propagate properly later
        terrainGrid[x,y,z].possibilites.Clear();
        terrainGrid[x,y,z].possibilites.Add(chosenPrototype);

        uncollapsedCellsCount -= 1;
    }

    private void Propagate(Stack<Vector3Int> stack) {
        Vector3Int coords = stack.Pop();
        Superposition current = terrainGrid[coords.x, coords.y, coords.z];

        // Get all neighbour directions to check
        Vector3Int[] dirs = { // Indices of these are setup to mirror index setup from Blender script but with Unity coord system
            coords + new Vector3Int (1, 0, 0),  // RIGHT
            coords + new Vector3Int (0, 0, 1),  // FORWARD
            coords + new Vector3Int (-1, 0, 0), // LEFT
            coords + new Vector3Int (0, 0, -1), // BACKWARDS
            coords + new Vector3Int (0, -1, 0), // DOWN
            coords + new Vector3Int (0, 1, 0)   // UP
        };
        // Handedness and up vectors are a pain

        // Get only valid neighbour directions to check
        List<(Vector3Int, int)> validNbCoords = new List<(Vector3Int, int)>();
        for (int i = 0; i < dirs.Length; i++) {
            if (dirs[i].x < mapSize.x && dirs[i].x >= 0
                && dirs[i].y < mapSize.y && dirs[i].y >= 0
                && dirs[i].z < mapSize.z && dirs[i].z >= 0) // if inside grid
            {
                if (terrainGrid[dirs[i].x, dirs[i].y, dirs[i].z].collapsedGameObj == null) {
                    validNbCoords.Add((dirs[i], i));
                }
            }
        }

        // Propagating through each direction
        foreach ((Vector3Int otherCoords, int dirIdx) in validNbCoords) { // dirIdx == direction's face profile's idx

            // Creating potential neighbour list for direction by compiling potential neighbours or each possibility
            List<Prototype> possibleNeighbours = new List<Prototype>();
            foreach (Prototype proto in current.possibilites) {
                int[] potNeighIdces = proto.face_profiles[dirIdx].potential_neighbours;
                foreach (int nb in potNeighIdces) {
                    possibleNeighbours.Add(Array.Find(prototypes, (proto) => proto.id == nb));
                }
            }

            // Getting Superposition to update
            Superposition other = terrainGrid[otherCoords.x, otherCoords.y, otherCoords.z];

            // Removing invalid possibilities from Superposition by checking possibleNeighbours List
            bool change = false;
            for (int idx = other.possibilites.Count - 1; idx >= 0; idx--) {
                var otherProto = other.possibilites[idx];
                if (!(possibleNeighbours.Exists(nb => nb.id == otherProto.id))) {
                    other.possibilites.RemoveAt(idx);
                    UpdateEntropy(other.possibilites.Count, otherCoords);
                    change = true;
                    if (other.possibilites.Count == 0) {
                        other.possibilites.Add(prototypes[0]);
                        break;
                    }
                }
            }
            if (change && !stack.Contains(otherCoords)) stack.Push(otherCoords);
        }
    }

    private void UpdateEntropy(int newCellEntropy, Vector3Int cellCoords) {
        if (newCellEntropy < minEntropy) {
            minEntropyPoints.Clear();
            minEntropyPoints.Add(cellCoords);
            minEntropy = newCellEntropy;
        } else if (newCellEntropy == minEntropy) {
            minEntropyPoints.Add(cellCoords);
        }
    }

    private void ResetEntropy() {
        minEntropy = prototypes.Length;
        for (int x = 0; x < mapSize.x; x++)
            for (int y = 0; y < mapSize.y; y++)
                for (int z = 0; z < mapSize.z; z++)
                    if (terrainGrid[x,y,z].collapsedGameObj == null
                    && terrainGrid[x,y,z].possibilites.Count > 0
                    && terrainGrid[x,y,z].possibilites.Count < minEntropy) {
                        UpdateEntropy(terrainGrid[x,y,z].possibilites.Count, new Vector3Int(x,y,z));
                    }
    }

    private void InstantiateEmpty(int x, int y, int z) {
        // Set mesh and rotation of prefab from prototype
        terrainGrid[x,y,z].collapsedGameObj = Instantiate<GameObject>(prototypePrefab, this.transform); // Set prefab
        terrainGrid[x,y,z].collapsedGameObj.transform.position = new Vector3(x,y,z); // Set position of prefab
        terrainGrid[x,y,z].collapsedPrototype = prototypes[0];
        terrainGrid[x,y,z].possibilites.Clear();
        terrainGrid[x,y,z].possibilites.Add(prototypes[0]);

        uncollapsedCellsCount -= 1;
    }

}
