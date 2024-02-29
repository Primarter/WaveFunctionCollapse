import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty

class WfcPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    wfc_log_filepath: StringProperty(
        name="Log filepath",
        description="This is passed to bpy.path.abspath, you can use // to reference the Blender file's location",
        subtype='FILE_PATH',
        default="//log.txt"
    )


    wfc_dump_filepath: StringProperty(
        name="Dump data filepath",
        description="This is passed to bpy.path.abspath, you can use // to reference the Blender file's location",
        subtype='FILE_PATH',
        default="//dump.txt"
    )


    wfc_json_filepath: StringProperty(
        name="JSON data filepath",
        description="This is passed to bpy.path.abspath, you can use // to reference the Blender file's location",
        subtype='FILE_PATH',
        default="//data.json"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="WFC Addon filepaths (use // for paths relative to Blender file)")
        layout.prop(self, "log_filepath")
        layout.prop(self, "dump_filepath")
        layout.prop(self, "json_filepath")

def get_preferences(context: bpy.types.Context):
    return context.preferences.addons[__package__].preferences