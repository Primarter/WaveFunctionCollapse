using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public struct Neighbour
{
    public int id;
    public int rotation;
}

[System.Serializable]
public struct FaceProfile
{
    public int id;
    public bool vertical;
    public bool rotating;
    public bool flipping;
    public int rotation;
    public bool flipped;
    public Neighbour[] potential_neighbours;
}

[System.Serializable]
public class Prototype
{
    public int id;
    public string name;
    public Mesh mesh;
    public FaceProfile[] face_profiles;
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