from __future__ import annotations

if "bpy" in locals():
    import importlib
    importlib.reload(create_weight_operator)
    importlib.reload(compute_data_operator)
    importlib.reload(dump_data_operator)
    importlib.reload(create_json_operator)
    importlib.reload(wfc_panel)
else:
    from . import create_weight_operator
    from . import compute_data_operator
    from . import dump_data_operator
    from . import create_json_operator
    from . import wfc_panel

import bpy

from create_weight_operator import WFC_OT_create_weight
from compute_data_operator import WFC_OT_compute_data_operator
from dump_data_operator import WFC_OT_dump_data
from create_json_operator import WFC_OT_create_json
from wfc_panel import WFC_PT_wfc_panel

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

def register():
    bpy.types.Scene.WFC_prototypes_collection = bpy.props.PointerProperty(type=bpy.types.Collection, name="Collection to setup")
    bpy.types.Scene.WFC_log_data = bpy.props.BoolProperty(name="Log Data", description="Are computing logs going to a file?", default=False)
    bpy.utils.register_class(WFC_OT_create_weight)
    bpy.utils.register_class(WFC_OT_compute_data_operator)
    bpy.utils.register_class(WFC_OT_dump_data)
    bpy.utils.register_class(WFC_OT_create_json)
    bpy.utils.register_class(WFC_PT_wfc_panel)


def unregister():
    bpy.utils.unregister_class(WFC_PT_wfc_panel)
    bpy.utils.unregister_class(WFC_OT_create_json)
    bpy.utils.unregister_class(WFC_OT_dump_data)
    bpy.utils.unregister_class(WFC_OT_compute_data_operator)
    bpy.utils.unregister_class(WFC_OT_create_weight)
    del bpy.types.Scene.WFC_prototypes_collection


if __name__ == "__main__":
    register()

# TODO add options to panel (paths, debug to file or console, do that by adding properties like the collection)
# add purging data button and data status
# add weight removal button