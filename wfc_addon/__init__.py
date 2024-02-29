from __future__ import annotations

bl_info = {
    "name": "Wave Function Collapse Setup",
    "author": "Primarter",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Edit Panel > WFC Setup",
    "description": "Sets up objects to be used in Unity with a Wave Function Collapse algorithm",
    "warning": "",
    "doc_url": "",
    "category": "Setup WFC",
}

import importlib
import bpy

if ("preferences" not in locals()):
    from . import preferences
else:
    preferences = importlib.reload(preferences)

if ("create_weight_operator" not in locals()):
    from . import create_weight_operator
else:
    create_weight_operator = importlib.reload(create_weight_operator)

if ("compute_data_operator" not in locals()):
    from . import compute_data_operator
else:
    compute_data_operator = importlib.reload(compute_data_operator)

if ("dump_data_operator" not in locals()):
    from . import dump_data_operator
else:
    dump_data_operator = importlib.reload(dump_data_operator)

if ("create_json_operator" not in locals()):
    from . import create_json_operator
else:
    create_json_operator = importlib.reload(create_json_operator)

if ("wfc_panel" not in locals()):
    from . import wfc_panel
else:
    wfc_panel = importlib.reload(wfc_panel)

from .preferences import WfcPreferences
from .create_weight_operator import WFC_OT_create_weight
from .compute_data_operator import WFC_OT_compute_data_operator
from .dump_data_operator import WFC_OT_dump_data
from .create_json_operator import WFC_OT_create_json
from .wfc_panel import WFC_PT_wfc_panel

WfcClasses = [
    WfcPreferences,
    WFC_OT_create_weight,
    WFC_OT_compute_data_operator,
    WFC_OT_dump_data,
    WFC_OT_create_json,
    WFC_PT_wfc_panel,
]

def registerProperties():
    bpy.types.Scene.wfc_prototypes_collection = bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection to setup")
    bpy.types.Scene.wfc_log_data = bpy.props.BoolProperty(
        name="Log Data",
        description="Are computing logs going to a file?",
        default=False)

def unregisterProperties():
    del bpy.types.Scene.wfc_prototypes_collection
    del bpy.types.Scene.wfc_log_data

def register():
    for WfcClass in WfcClasses:
        try:
            bpy.utils.register_class(WfcClass)
        except:
            bpy.utils.unregister_class(WfcClass)
            bpy.utils.register_class(WfcClass)

    registerProperties()

    # This prevents data from being lost when reloading, therefore avoiding weird bugs
    bpy.context.preferences.use_preferences_save = True


def unregister():
    for WfcClass in WfcClasses:
        bpy.utils.unregister_class(WfcClass)

    unregisterProperties()


if __name__ == "__main__":
    register()

# TODO add options to panel (paths, debug to file or console, do that by adding properties like the collection)
# add purging data button and data status
# add weight removal button
# Figure out how to work with multi files
# add register everywhere