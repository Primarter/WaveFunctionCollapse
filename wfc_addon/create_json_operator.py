import bpy
import logging
import json
from compute_data_operator import WFC_OT_compute_data_operator
from wfc_utils import JSON_DATA_PATH

log = logging.getLogger("wfc_addon.dump_data_operator")

class WFC_OT_create_json(bpy.types.Operator):
    '''Dump data to a JSON file for transfer to Unity'''
    bl_idname = "wfc.create_json"
    bl_label = "Dump WFC data to JSON file"

    def execute(self, context):
        prototypes = WFC_OT_compute_data_operator.prototypes
        with open(JSON_DATA_PATH, "w") as json_file:
            for p in prototypes:
                p.face_profiles = tuple(fp.__dict__ for fp in p.face_profiles)
            data = [p.__dict__ for p in prototypes]
            data_wrapper = {"data": data}
            json.dump(data_wrapper, json_file, indent=2)
        log.info("Wrote JSON data to data.json")
        return {'FINISHED'}