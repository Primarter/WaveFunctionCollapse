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
        for (int x = 0; x < terrainGrid.GetLength(0); x++) {
            for (int y = 0; y < terrainGrid.GetLength(1); y++) {
                for (int z = 0; z < terrainGrid.GetLength(2); z++) {
                    terrainGrid[x,y,z].possibilites = new List<Prototype>(prototypes);
                    terrainGrid[x,y,z].collapsedValue = null;
                }
            }
        }

        uncollapsedCellsCount = mapSize.x * mapSize.y * mapSize.z; // TODO: Decrease when a cell collapses
        minEntropyPoint = mapSize/2; // TODO: Change when propagating, randomise if tie
        minEntropy = prototypes.Length;

        while (uncollapsedCellsCount > 0) {
            (int x, int y, int z) = (minEntropyPoint.x, minEntropyPoint.y, minEntropyPoint.z);

            // Collapse minEntropyPoint
            terrainGrid[x,y,z].collapsedValue = Instantiate<GameObject>(prototypePrefab, this.transform); // Set prefab
            terrainGrid[x,y,z].collapsedValue.transform.position = new Vector3(x,y,z); // Set position of prefab
            int chosenPossibilityIdx = Random.Range(0, terrainGrid[x,y,z].possibilites.Count); // Choose random possibility
            terrainGrid[x,y,z].collapsedValue.GetComponent<MeshFilter>().mesh = terrainGrid[x,y,z].possibilites[chosenPossibilityIdx].mesh; // Assign mesh
            terrainGrid[x,y,z].possibilites.Clear();
            uncollapsedCellsCount -= 1;

            // TODO: Propagate collapse
            /* pseudo code
            stack = []
            stack.push(minEntropyPoint)

            while stack !empty
                coords = stack.pop
                current = terrainGrid[coords]

                enum DirectionIndices // for face profiles
                    LEFT
                    BACKWARDS
                    RIGHT
                    FORWARD
                    DOWN
                    UP
                Vector3Int[] dirs = [
                    coords + new Vector3Int (-1, 0, 0)   // LEFT
                    coords + new Vector3Int (0, 0, -1)   // BACKWARDS
                    coords + new Vector3Int (1, 0, 0)    // RIGHT
                    coords + new Vector3Int (0, 0, 1)    // FORWARD
                    coords + new Vector3Int (0, -1, 0)   // DOWN
                    coords + new Vector3Int (0, 1, 0)    // UP
                ]
                List<(Vector3Int, fpIdx)> validDirs = []
                for (int i = 0; i < dirs.Length; i++)
                    if ((dirs[i].x < terrainGrid.GetLength(0)
                        && dirs[i].y < terrainGrid.GetLength(1)
                        && dirs[i].z < terrainGrid.GetLength(2))
                    && (terrainGrid[dirs[i].x, dirs[i].y, dirs[i].z].possibilites.Count > 0))
                        validDirs.append(dirs[i], i)

                for dir in validDirs
                    Prototype[] possibleNeighbours = []
                    for proto in current.possibilites
                        possibleNeighbours.append(proto.face_profiles[dir].potential_neighbours)
                    other = terrainGrid[coords + dir]
                    bool change = false
                    for proto in other.possibilities
                        if not proto in possibleNeighbours
                            other.possibilities.remove(proto)
                            change = true
                    if change stack.push(other)
            */
        }
    }
}
