import bpy

class WFC_OT_clear_data(bpy.types.Operator):
    '''Clear setup data'''
    bl_idname = "wfc.clear_data"
    bl_label = "Clear WFC data"

    def execute(self, context):
        print(context.scene.wfc_prototypes_collection)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(WFC_OT_clear_data)

def unregister():
    bpy.utils.unregister_class(WFC_OT_clear_data)