using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

namespace Wfc {

[CustomEditor(typeof(WfcGenerator))]
public class WfcCustomEditor : Editor
{
    public override void OnInspectorGUI()
    {
        WfcGenerator generator = (WfcGenerator)target;
        DrawDefaultInspector();

        if (GUILayout.Button("Setup W.F.C.")) {
            Debug.Log("Setting up...");
            generator.SetupWfc();
            Debug.Log("Done!");
        }

        if (GUILayout.Button("Execute W.F.C.")) {
            Debug.Log("Collapsing...");
            generator.ExecuteWfc();
            Debug.Log("Done!");
        }

        if (GUILayout.Button("Clear Generator")) {
            Debug.Log("Destroying...");
            for (int i = generator.transform.childCount; i > 0; --i)
                DestroyImmediate(generator.transform.GetChild(0).gameObject);
                generator.ResetGrid();
            Debug.Log("Done!");
        }
    }
}

}