import bpy
from pathlib import Path
from bpy.types import Operator
from ..helpers import get_current_project_assets_path, get_current_project_structure_json

class BITCAKE_OT_dev_operator(Operator):
    bl_idname = "bitcake.dev_operator"
    bl_label = "Test Stuff"
    bl_description = "Test stuuuuff"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        print(construct_export_directory(self))

        return {'FINISHED'}


def construct_export_directory(self):
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    # Get the current project's project_structure.json object to get its folder structure
    structure_json = get_current_project_structure_json()
    if not structure_json:
        self.report({"ERROR"},
                    "No project_structure.json found! Please use BitPipe to create one for your project!")
        return {'CANCELLED'}

    # First, add the parent folder where all assets in the project reside
    pathway.append(structure_json['folderName'])

    # Search the .blend Path for BitCake's folder structure
    # Change _WIP folder to Art then construct the rest of the path
    for part in blend_path.parts:
        if wip is True:
            split_part = part.split('_')
            pathway.append(split_part[-1])
        if part.__contains__('_WIP'):
            pathway.append('Art')
            wip = True

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment")
        return {'CANCELLED'}

    # Construct final directory and return it
    current_project_path = Path(get_current_project_assets_path())
    constructed_directory = current_project_path.joinpath(*pathway) # Unpacks the list as arguments

    return constructed_directory

def draw_panel(self, context):
    layout = self.layout

    row = layout.row()
    row.operator('bitcake.dev_operator', text='Test Butten')

    return


classes = (BITCAKE_OT_dev_operator,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
