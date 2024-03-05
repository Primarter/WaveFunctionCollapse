using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.Events;
using Unity.Collections;

namespace Wfc {

public struct Superposition
{
    public List<Prototype> possibilites;
    public GameObject collapsedGameObj;
    public Prototype collapsedPrototype;
}

// TODO:
// Find a solution for verticality
// Add custom rules (every collapse, call a custom function)
// Add starting and ending rules (edit grid before and after generation)
public class WfcGenerator : MonoBehaviour
{
    public GameObject prototypePrefab;
    public GameObject prototypesAsset;
    public TextAsset prototypesDataFile;
    public Vector3Int mapSize = new(20, 1, 20);
    public UnityEvent startRules;
    public UnityEvent endRules;
    public bool drawGizmos = true;
    public bool emptyBorders = true;

    // private Prototype[] prototypes;
    private Dictionary<int, Prototype> prototypes;
    private Superposition[,,] terrainGrid;
    private int uncollapsedCellsCount;
    private float minEntropy;
    private float maxEntropy;
    private Vector3Int minEntropyPoint;
    private List<Vector3Int> minEntropyPoints = new();

    // Start and Update are uncommented when debugging step by step
    private void Start() {
        // SetupWfc();
    }
    private void Update() {
        // if (Input.GetKeyDown(KeyCode.Space) && uncollapsedCellsCount > 0) {
        // if (uncollapsedCellsCount > 0) {
        //     CollapseStep();
        // }
        // }
    }

    private void OnDrawGizmos() {
        if (drawGizmos) {
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
    }

    public void ResetGrid() {
        terrainGrid = null;
    }

    private void SetupGrid() {
        terrainGrid = new Superposition[mapSize.x, mapSize.y, mapSize.z];

        // Filling superposition grid
        for (int x = 0; x < mapSize.x; x++) {
            for (int y = 0; y < mapSize.y; y++) {
                for (int z = 0; z < mapSize.z; z++) {
                    terrainGrid[x,y,z].possibilites = new List<Prototype>(prototypes.Values);
                    terrainGrid[x,y,z].collapsedGameObj = null;
                }
            }
        }

        uncollapsedCellsCount = mapSize.x * mapSize.y * mapSize.z;
        maxEntropy = prototypes.Count;
        minEntropy = maxEntropy;
    }

    public bool SetupWfc() {
        if (prototypePrefab == null) {
            Debug.Log("Using default prototype from Resources/WFC/Prototype");
            prototypePrefab = Resources.Load<GameObject>("WFC/Prototype");
        }
        if (mapSize.x <= 0 || mapSize.y <= 0 || mapSize.z <= 0 || prototypesAsset == null || prototypesDataFile == null) {
            Debug.LogError("Terrain sizes can't be negative or null");
            this.enabled = false;
            return false;
        }
        // Getting labelling data from JSON and attaching meshes to it.
        prototypes = PrototypeDataWrapper.CreateFromJSON(prototypesDataFile.ToString());
        for (int i = 0; i < prototypes.Count; i++) {
            foreach(Transform t in prototypesAsset.transform) {
                if (t.name == prototypes[i].name) {
                    prototypes[i].mesh = t.GetComponent<MeshFilter>().sharedMesh;
                }
            }
        }

        // Setting up grid for prototype placement
        SetupGrid();

        if (emptyBorders)
            CollapseBorders();
        else
            minEntropyPoints.Add(mapSize/2);

        return true;
    }

    public void ExecuteWfc() {
        if (!SetupWfc())
            return;
        while (uncollapsedCellsCount > 0) {
            CollapseStep();
        }
        endRules.Invoke();

        minEntropy = maxEntropy;
    }

    private void CollapseStep() {
        // Setting entropy point, either from list of entropy points or researching the whole grid
        if (minEntropyPoints.Count == 0) {
            ResetEntropy();
        }
        int chosenEntropy = UnityEngine.Random.Range(0, minEntropyPoints.Count);
        minEntropyPoint = minEntropyPoints[chosenEntropy];
        minEntropyPoints.RemoveAt(chosenEntropy);

        CollapseCell(minEntropyPoint);

        PropagateFromPosition(minEntropyPoint);
    }

    private void CollapseCell(Vector3Int pos) {
        // Create prefab
        if (terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj) {
            Debug.Log(("ALREADY COLLAPSED", pos));
        }
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj = Instantiate(prototypePrefab, this.transform); // Set prefab
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.transform.position = new Vector3(pos.x, pos.y, pos.z); // Set position of prefab

        if (terrainGrid[pos.x, pos.y, pos.z].possibilites.Count == 0) {
            InstantiateEmpty(pos.x, pos.y, pos.z);
            return;
        }

        // Choose random prototype in possibilities
        Prototype chosenPrototype = ChooseRandomPrototype(terrainGrid[pos.x, pos.y, pos.z].possibilites);
        if (chosenPrototype == null) {
            chosenPrototype = prototypes[0];
            Debug.LogError("Random prototype choice returned null (this shouldn't happen)");
        }

        // Set mesh and rotation of prefab from prototype
        var meshFilter = terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.GetComponent<MeshFilter>();
        meshFilter.mesh = chosenPrototype.mesh; // Assign mesh
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.transform.rotation = Quaternion.Euler(0, 90 * chosenPrototype.rotation, 0); // Set rotation of prefab
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.GetComponent<MeshCollider>().sharedMesh = meshFilter.sharedMesh; // Assign mesh

        // Setup possibilities to propagate properly later
        terrainGrid[pos.x, pos.y, pos.z].possibilites.Clear();
        terrainGrid[pos.x, pos.y, pos.z].possibilites.Add(chosenPrototype);

        uncollapsedCellsCount -= 1;
    }

    public void CollapseCell(Vector3Int pos, Prototype chosenPrototype) {
        if (terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj)
            Debug.Log(("ALREADY COLLAPSED", pos));
        // Create prefab
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj = Instantiate(prototypePrefab, this.transform); // Set prefab
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.transform.position = new Vector3(pos.x, pos.y, pos.z); // Set position of prefab

        if (terrainGrid[pos.x, pos.y, pos.z].possibilites.Count == 0) {
            InstantiateEmpty(pos.x, pos.y, pos.z);
            return;
        }

        // Choose random prototype in possibilities
        if (chosenPrototype == null) {
            chosenPrototype = prototypes[0];
            Debug.LogError("Chosen prototype is null");
        }

        // Set mesh and rotation of prefab from prototype
        var meshFilter = terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.GetComponent<MeshFilter>();
        meshFilter.mesh = chosenPrototype.mesh; // Assign mesh
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.transform.rotation = Quaternion.Euler(0, 90 * chosenPrototype.rotation, 0); // Set rotation of prefab
        terrainGrid[pos.x, pos.y, pos.z].collapsedGameObj.GetComponent<MeshCollider>().sharedMesh = meshFilter.sharedMesh; // Assign mesh

        // Setup possibilities to propagate properly later
        terrainGrid[pos.x, pos.y, pos.z].possibilites.Clear();
        terrainGrid[pos.x, pos.y, pos.z].possibilites.Add(chosenPrototype);

        uncollapsedCellsCount -= 1;
    }

    private void PropagateSingle(Stack<Vector3Int> stack) {
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
        List<(Vector3Int, int)> validNbCoords = new();
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
                foreach (int id in potNeighIdces) {
                    possibleNeighbours.Add(prototypes[id]);
                    // possibleNeighbours.Add(Array.Find(prototypes, (proto) => proto.id == nb));
                }
            }

            // Getting Superposition to update
            Superposition other = terrainGrid[otherCoords.x, otherCoords.y, otherCoords.z];

            // Removing invalid possibilities from Superposition by checking possibleNeighbours List
            bool change = false;
            for (int idx = other.possibilites.Count - 1; idx >= 0; idx--) {
                var otherProto = other.possibilites[idx];
                if (!possibleNeighbours.Exists(nb => nb.id == otherProto.id)) {
                    other.possibilites.RemoveAt(idx);
                    UpdateEntropy(other.possibilites, otherCoords);
                    change = true;
                    if (other.possibilites.Count == 0) {
                        other.possibilites.Add(prototypes[0]);
                        break;
                    }
                }
            }
            if (change && !stack.Contains(otherCoords))
                stack.Push(otherCoords);
        }
    }

    private void PropagateFromPosition(Vector3Int pos)
    {
        Stack<Vector3Int> stack = new(); // cells to update
        stack.Push(pos);

        while (stack.Count > 0) { // While not fully propagated
            PropagateSingle(stack);
        }

        terrainGrid[pos.x, pos.y, pos.z].possibilites.Clear();
    }

    // Could use that rather than random to select lowest entropy point, don't know how useful it would be though
    private float ComputeCellEntropy(List<Prototype> possibilites) {
        float mean = 0f;
        foreach (var p in possibilites) {
            mean += p.weight;
        }
        mean /= possibilites.Count;
        float stdDev = 0;
        foreach (var p in possibilites) {
            stdDev += Mathf.Pow(p.weight - mean, 2);
        }
        stdDev /= possibilites.Count;
        float cellEntropy = 1f/Mathf.Sqrt(stdDev);

        return cellEntropy;
    }
    
    private void UpdateEntropy(List<Prototype> possibilites, Vector3Int cellCoords) {
        // float newCellEntropy = ComputeCellEntropy(possibilites);
        float newCellEntropy = possibilites.Count;

        if (newCellEntropy < minEntropy) {
            minEntropyPoints.Clear();
            minEntropyPoints.Add(cellCoords);
            minEntropy = newCellEntropy;
        } else if (newCellEntropy == minEntropy) {
            minEntropyPoints.Add(cellCoords);
        }
    }

    private void ResetEntropy() {
        minEntropy = maxEntropy;
        for (int x = 0; x < mapSize.x; x++)
            for (int y = 0; y < mapSize.y; y++)
                for (int z = 0; z < mapSize.z; z++)
                    if (terrainGrid[x,y,z].collapsedGameObj == null
                    && terrainGrid[x,y,z].possibilites.Count > 0
                    && terrainGrid[x,y,z].possibilites.Count < minEntropy) {
                        UpdateEntropy(terrainGrid[x,y,z].possibilites, new Vector3Int(x,y,z));
                    }
    }

    private void InstantiateEmpty(int x, int y, int z) {
        // Set mesh and rotation of prefab from prototype
        terrainGrid[x,y,z].collapsedGameObj = Instantiate(prototypePrefab, this.transform); // Set prefab
        terrainGrid[x,y,z].collapsedGameObj.transform.position = new Vector3(x,y,z); // Set position of prefab
        terrainGrid[x,y,z].collapsedPrototype = prototypes[0];
        terrainGrid[x,y,z].possibilites.Clear();
        terrainGrid[x,y,z].possibilites.Add(prototypes[0]);

        uncollapsedCellsCount -= 1;
    }

    private Prototype ChooseRandomPrototype(List<Prototype> possibilities) {
        if (possibilities.Count == 0) {
            Debug.LogWarning("Can't select random from an empty list");
            return null;
        }

        float totalWeight = 0;
        foreach (var proto in possibilities) {
            totalWeight += proto.weight;
        }

        Prototype selectedPrototype = null;
        float randomNumber = UnityEngine.Random.Range(0, totalWeight);
        foreach (var proto in possibilities)
        {
            if (randomNumber < proto.weight)
            {
                selectedPrototype = proto;
                break;
            }
            randomNumber -= proto.weight;
        }

        selectedPrototype ??= possibilities[0];

        return selectedPrototype;
    }

    private void CollapseBorders() {
        if (mapSize.x < 3 || mapSize.z < 3) {
            return;
        }

        for(int x = 0; x < mapSize.x; x++) {
            Vector3Int pos = new(x, 0, mapSize.z - 1);
            CollapseCell(pos, prototypes[0]);
            PropagateFromPosition(pos);
            pos.z = 0;
            CollapseCell(pos, prototypes[0]);
            PropagateFromPosition(pos);
        }

        for(int z = 1; z < mapSize.z - 1; z++) {
            Vector3Int pos = new(mapSize.x - 1, 0, z);
            CollapseCell(pos, prototypes[0]);
            PropagateFromPosition(pos);
            pos.x = 0;
            CollapseCell(pos, prototypes[0]);
            PropagateFromPosition(pos);
        }
        ResetEntropy();
    }

}

}