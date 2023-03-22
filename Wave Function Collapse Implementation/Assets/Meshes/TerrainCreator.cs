using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public struct Superposition
{
    public List<Prototype> possibilites;
    public GameObject collapsedValue;
}

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

    // private enum DirectionIndex { // for face profiles
    //     LEFT = 0,
    //     BACKWARDS = 1,
    //     RIGHT = 2,
    //     FORWARD = 3,
    //     DOWN = 4,
    //     UP = 5
    // };

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
                    // terrainGrid[x,y,z] = new Superposition();
                    terrainGrid[x,y,z].possibilites = new List<Prototype>(prototypes);
                    terrainGrid[x,y,z].collapsedValue = null;
                    // Debug.Log(("Init", terrainGrid[x,y,z].possibilites.Count));
                }
            }
        }
        // Debug.Log(terrainGrid[10,0,11]);

        uncollapsedCellsCount = mapSize.x * mapSize.y * mapSize.z; // TODO: Decrease when a cell collapses
        minEntropyPoint = mapSize/2; // TODO: Change when propagating, randomise if tie
        minEntropy = prototypes.Length;

        while (uncollapsedCellsCount > 0) {
            (int x, int y, int z) = (minEntropyPoint.x, minEntropyPoint.y, minEntropyPoint.z);
            // Debug.Log(minEntropyPoint);

            if (terrainGrid[x,y,z].possibilites.Count == 0) {
                Debug.Log(("error", minEntropyPoint));
                break;
            }
            // Collapse minEntropyPoint
            terrainGrid[x,y,z].collapsedValue = Instantiate<GameObject>(prototypePrefab, this.transform); // Set prefab
            terrainGrid[x,y,z].collapsedValue.transform.position = new Vector3(x,y,z); // Set position of prefab
            int chosenPossibilityIdx = UnityEngine.Random.Range(0, terrainGrid[x,y,z].possibilites.Count); // Choose random possibility
            // Debug.Log((terrainGrid[x,y,z].possibilites.Count, chosenPossibilityIdx));
            Prototype chosenPrototype = terrainGrid[x,y,z].possibilites[chosenPossibilityIdx];
            terrainGrid[x,y,z].collapsedValue.GetComponent<MeshFilter>().mesh = terrainGrid[x,y,z].possibilites[chosenPossibilityIdx].mesh; // Assign mesh
            terrainGrid[x,y,z].possibilites.Clear();
            terrainGrid[x,y,z].possibilites.Add(chosenPrototype);
            uncollapsedCellsCount -= 1;

            // Propagate collapse
            Stack<Vector3Int> stack = new Stack<Vector3Int>(); // Contains all cells to update
            stack.Push(minEntropyPoint); // adding starting point

            int block = 0;
            while (stack.Count > 0) { // While not fully propagated
                block += 1;
                if (stack.Count > 401 && block > 5000) {
                    Debug.Log(("Cucked", stack.Count));
                    return;
                }
                Vector3Int coords = stack.Pop();
                Superposition current = terrainGrid[coords.x, coords.y, coords.z];

                // Get all neighbour directions to check
                Vector3Int[] dirs = { // Indices of these are setup to mirror index setup from Blender script but with Unity coord system
                    coords + new Vector3Int (-1, 0, 0), // LEFT
                    coords + new Vector3Int (0, 0, -1), // BACKWARDS
                    coords + new Vector3Int (1, 0, 0),  // RIGHT
                    coords + new Vector3Int (0, 0, 1),  // FORWARD
                    coords + new Vector3Int (0, -1, 0), // DOWN
                    coords + new Vector3Int (0, 1, 0)   // UP
                }; // Handedness and up vectors are a pain

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

                    // Creating potential neighbour list for direction
                    List<Prototype> possibleNeighbours = new List<Prototype>();
                    // Debug.Log(("current", current.possibilites.Count));
                    foreach (Prototype proto in current.possibilites) {
                        var potNeighIdces = proto.face_profiles[dirIdx].potential_neighbours;
                        foreach (int nb in potNeighIdces) {
                            possibleNeighbours.Add(Array.Find(prototypes, (proto) => proto.id == nb));
                        }
                    }

                    // Getting Superposition to update
                    Superposition other = terrainGrid[otherCoords.x, otherCoords.y, otherCoords.z];

                    // Removing invalid neighbours from Superposition by checking possibleNeighbours List
                    bool change = false;
                    // Debug.Log(possibleNeighbours.Count);
                    for (int idx = other.possibilites.Count - 1; idx >= 0; idx--) {
                        var otherProto = other.possibilites[idx];
                        if (!(possibleNeighbours.Exists(nb => nb.id == otherProto.id))) {
                            other.possibilites.RemoveAt(idx);
                            change = true;
                            if (other.possibilites.Count <= minEntropy) {
                                minEntropy = other.possibilites.Count;
                                minEntropyPoint = otherCoords;
                                // Debug.Log(("Entropy", minEntropy, minEntropyPoint));
                            }
                        }
                    }
                    Debug.Log(otherCoords);
                    if (change && !stack.Contains(otherCoords)) stack.Push(otherCoords);
                }
            }
            Debug.Log(("MIN ENTROPY POINT########################################", minEntropyPoint));
            terrainGrid[x,y,z].possibilites.Clear();
        }
    }
}
