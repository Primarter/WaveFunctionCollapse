using System.Collections;
using System.Collections.Generic;
using UnityEngine;

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

    public static PrototypeDataWrapper CreateFromJSON(string jsonString)
    {
        return JsonUtility.FromJson<PrototypeDataWrapper>(jsonString);
    }
}