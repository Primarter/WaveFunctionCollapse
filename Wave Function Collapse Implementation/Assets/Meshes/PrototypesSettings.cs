using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "Settings", menuName = "ScriptableObjects/PrototypesSettings", order = 1)]
public class PrototypesSettings : ScriptableObject
{
    public Object prototypesAsset;
    public TextAsset prototypesData;
}