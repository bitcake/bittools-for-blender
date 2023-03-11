from pathlib import Path
import bpy
from bpy.types import Operator
from ..helpers import is_wip_in_path

class BITCAKE_OT_dev_operator(Operator):
    bl_idname = "bitcake.dev_operator"
    bl_label = "Test Stuff"
    bl_description = "Test stuuuuff"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.active_object

        print(obj)

        obj_copy = duplicate(obj)
        decimate = obj_copy.modifiers.new('Decimate', 'DECIMATE')
        decimate.ratio = 0.5

        return {'FINISHED'}


def duplicate(obj, data=True, actions=True, parent=True):
    obj_copy = obj.copy()
    if data:
        obj_copy.data = obj_copy.data.copy()
    if actions and obj_copy.animation_data:
        obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
    if parent:
        obj_copy.parent = obj

    obj_copy.matrix_parent_inverse = obj.matrix_world.inverted()

    for collection in obj.users_collection:
        collection.objects.link(obj_copy)

    return obj_copy


def construct_registered_project_published_export_directory(self):
    blend_path = Path(bpy.path.abspath('//'))
    pathway = []

    # If no WIP folder found then fail
    if not is_wip_in_path():
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word 'WIP' like in c:/BitTools/02_WIP/Environment")
        return {'CANCELLED'}

    # Search the .blend Path for BitCake's folder structure
    # Change _WIP folder to Art then construct the rest of the path
    for part in blend_path.parts:
        pathway.append(part)
        if part.__contains__('02_WIP'):
            pathway.pop()
            pathway.append('03_Published')


    # Construct final directory and return it
    constructed_directory = Path().joinpath(*pathway) # Unpacks the list as arguments

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
