from pathlib import Path
import time
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
        c = bpy.context
        bones = c.object.data.bones

        for bone in bones.items():
            print(f'TAMO ALTERANDO O BONE {bone[1].name} QUE TEM O TIPO DE INHERIT SCALE {bone[1].inherit_scale}')
            bone[1].inherit_scale = 'FULL'
            print(f'{bone[1].name} AGORA TEM O TIPO DE INHERIT SCALE {bone[1].inherit_scale}')


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
    print(constructed_directory)
    return constructed_directory


def clear_weights_on_opposite_side(context):
    start_time = time.time()

    vertices = context.object.data.vertices
    active_vertex_group = context.object.vertex_groups.active
    left_to_right = context.scene.rigging_configs.left_to_right

    for verts in vertices.items():
        if left_to_right:
            if verts[1].co[0] < -0.0001:
                active_vertex_group.remove([verts[0]])
        else:
            if verts[1].co[0] > 0.0001:
                active_vertex_group.remove([verts[0]])

        if  0.0001 >= verts[1].co[0] >= -0.0001:
            verts[1].select = True
            try:
                new_weight = active_vertex_group.weight(verts[0]) / 2
                active_vertex_group.add([verts[0]], new_weight, 'REPLACE')
            except RuntimeError:
                continue

    executionTime = (time.time() - start_time)
    print('Execution time in seconds: ' + str(executionTime))

    return



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
