import bpy
import logging
from compute_data_operator import WFC_OT_compute_data_operator
from wfc_utils import DUMP_DATA_PATH

log = logging.getLogger("wfc_addon.dump_data_operator")

class WFC_OT_dump_data(bpy.types.Operator):
    '''Dump data to a text file (useful to debug)'''
    bl_idname = "wfc.dump_data"
    bl_label = "Dump WFC data to text file"

    def execute(self, context):
        prototypes = WFC_OT_compute_data_operator.prototypes
        file = open(DUMP_DATA_PATH, 'a')
        file.write('\n### DATA ###\n\n')

        # for fp, ori, ofp in known_face_profiles:
        #     file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

        # file.write('\n')

        # for fp, ori, ofp in known_vertical_face_profiles:
        #     file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

        # file.write('\n')

        for proto in prototypes:
            file.write(proto.name + ' ' + str(proto.id) + '\n')
            for fp in proto.face_profiles:
                file.write(str(fp) + '\n')
                # file.write(str(fp.potential_neighbours) + '\n')
            file.write('\n')
        log.info("Dumped debug data to log.txt")
        return {'FINISHED'}