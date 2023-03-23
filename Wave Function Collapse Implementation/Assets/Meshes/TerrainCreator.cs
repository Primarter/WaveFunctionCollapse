using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public struct Superposition
{
    public List<Prototype> possibilites;
    public GameObject collapsedValue;
}

// TODO:
// Fix verticality by not allowing blocks to be on top of a -1
// Add vertical orientation to prototypes (two collections in Blender for easy solution, then a single one with normal computations)
// Check verticality: if upwards block is placed, either the column upwards is empty or the next block encountered is downwards
// Add weights to prototype choices
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
                    terrainGrid[x,y,z].collapsedValue = null;
                }
            }
        }

        uncollapsedCellsCount = mapSize.x * mapSize.y * mapSize.z;
        minEntropyPoint = mapSize/2;
        // minEntropyPoints.Add(mapSize/2);
        minEntropy = prototypes.Length;

        while (uncollapsedCellsCount > 0) {
            CollapseStep();
        }
    }

    private void Update() {
        if (uncollapsedCellsCount > 0) {
            // Debug.Log(minEntropyPoint);
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

        // Resetting minEntropy by searching through the list
        // optimisation possible by using a list of minEntropyPoints (also allows for randomisation of ties)
        minEntropy = prototypes.Length;
        for (int ix = 0; ix < mapSize.x; ix++) {
            for (int iy = 0; iy < mapSize.y; iy++) {
                for (int iz = 0; iz < mapSize.z; iz++) {
                    if (terrainGrid[ix,iy,iz].collapsedValue == null
                    && terrainGrid[ix,iy,iz].possibilites.Count > 0
                    && terrainGrid[ix,iy,iz].possibilites.Count < minEntropy) {
                        minEntropy = terrainGrid[ix,iy,iz].possibilites.Count;
                        minEntropyPoint = new Vector3Int(ix, iy, iz);
                    }
                }
            }
        }
        // minEntropyPoint = minEntropyPoints[UnityEngine.Random.Range(0, minEntropyPoints.Count)];

        (int x, int y, int z) = (minEntropyPoint.x, minEntropyPoint.y, minEntropyPoint.z);
        Debug.Log(("MIN ENTROPY POINT ", minEntropyPoint, minEntropy));

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
        terrainGrid[x,y,z].collapsedValue = Instantiate<GameObject>(prototypePrefab, this.transform); // Set prefab
        terrainGrid[x,y,z].collapsedValue.transform.position = new Vector3(x,y,z); // Set position of prefab

        // Choose random prototype in possibilities
        int chosenPossibilityIdx = UnityEngine.Random.Range(0, terrainGrid[x,y,z].possibilites.Count);
        Prototype chosenPrototype = terrainGrid[x,y,z].possibilites[chosenPossibilityIdx];

        // Set mesh and rotation of prefab from prototype
        terrainGrid[x,y,z].collapsedValue.GetComponent<MeshFilter>().mesh = terrainGrid[x,y,z].possibilites[chosenPossibilityIdx].mesh; // Assign mesh
        terrainGrid[x,y,z].collapsedValue.transform.rotation = Quaternion.Euler(0, 90 * chosenPrototype.rotation, 0); // Set rotation of prefab

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
                if (terrainGrid[dirs[i].x, dirs[i].y, dirs[i].z].collapsedValue == null) {
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
                    // UpdateEntropy(other.possibilites.Count, otherCoords);
                    change = true;
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

}
