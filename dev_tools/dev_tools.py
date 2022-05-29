import time
import bpy
from bpy.types import Operator

class BITCAKE_OT_dev_operator(Operator):
    bl_idname = "bitcake.dev_operator"
    bl_label = "Test Stuff"
    bl_description = "Test stuuuuff"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        clear_weights_on_opposite_side(context)

        return {'FINISHED'}

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
