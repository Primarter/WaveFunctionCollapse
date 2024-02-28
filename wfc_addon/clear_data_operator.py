import bpy

class WFC_OT_clear_data(bpy.types.Operator):
    '''Clear setup data'''
    bl_idname = "wfc.clear_data"
    bl_label = "Clear WFC data"

    def execute(self, context):
        print(context.scene.WFC_prototypes_collection)
        return {'FINISHED'}