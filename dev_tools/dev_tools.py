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
        obj = context.object

        collider_material = None
        for mat_name, material in bpy.data.materials.items():
            if mat_name == "BitTools_Collider_Material":
                collider_material = material

        if collider_material is None:
            mat = bpy.data.materials.new(name='BitTools_Collider_Material')
            mat.blend_method = 'BLEND'
            mat.use_nodes = True
            principled = mat.node_tree.nodes['Principled BSDF']
            principled.inputs['Base Color'].default_value = (0.19, 0.22, 0.8, 1)
            principled.inputs['Alpha'].default_value = 0.35
            collider_material = mat

        if len(obj.material_slots) < 1:
            obj.data.materials.append(collider_material)
        else:
            obj.material_slots[0].material = collider_material

        return {'FINISHED'}

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
