import bpy

from create_weight_operator import WFC_OT_create_weight
from compute_data_operator import WFC_OT_compute_data_operator
from dump_data_operator import WFC_OT_dump_data
from create_json_operator import WFC_OT_create_json

class WFC_PT_wfc_panel(bpy.types.Panel):
    '''This panel is used to setup the data needed for the Wave Function Collapse algorithm'''
    bl_label = "WFC Setup"
    bl_idname = "WFC_PT_wfc_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Collection to setup:")
        layout.prop(context.scene, "WFC_prototypes_collection", text="")
        layout.separator()
        col = layout.column()
        if (len(context.selected_objects) > 0 and context.selected_objects[0].get('Weight') is not None):
            col.label(text=context.selected_objects[0].name)
            col.prop(context.object, '["Weight"]')
        else:
            enabled = len(context.selected_objects) > 0
            col.label(text=context.selected_objects[0].name if enabled else "No object selected")
            col.operator(WFC_OT_create_weight.bl_idname, text="Create Weight prop")
            col.enabled = enabled
        layout.separator()
        layout.prop(context.scene, "WFC_log_data", text="Computing Log")
        layout.operator(WFC_OT_compute_data_operator.bl_idname, text="Compute Data")
        layout.operator(WFC_OT_dump_data.bl_idname, text="Dump Data")
        layout.operator(WFC_OT_create_json.bl_idname, text="Create JSON File")