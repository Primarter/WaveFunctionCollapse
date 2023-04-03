using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public struct FaceProfile
{
    public int id;
    public bool vertical;
    public bool rotating;
    public bool flipping;
    public int rotation;
    public bool flipped;
    public int[] potential_neighbours;
}

[System.Serializable]
public class Prototype
{
    public int id;
    public string name;
    public float weight;
    public FaceProfile[] face_profiles;
    public int rotation;
    public Mesh mesh;
}

[System.Serializable]
public struct PrototypeDataWrapper
{
    public Prototype[] data;

    public static Dictionary<int, Prototype> CreateFromJSON(string jsonString) {
        var data = JsonUtility.FromJson<PrototypeDataWrapper>(jsonString).data;
        Dictionary<int, Prototype> res = new Dictionary<int, Prototype>();
        foreach (var p in data) {
            res.Add(p.id, p);
        }
        return res;
    }
}