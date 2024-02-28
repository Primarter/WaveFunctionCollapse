import bpy

class WFC_OT_create_weight(bpy.types.Operator):
    '''Create custom property Weight on current object'''
    bl_idname = "wfc.create_weight"
    bl_label = "Create Weight"

    def execute(self, context):
        context.object['Weight'] = float(1.0)
        return {'FINISHED'}