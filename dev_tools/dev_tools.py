from re import I
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
        vertex_a = context.object.vertex_groups.active.name

        bpy.ops.object.vertex_group_copy()
        context.object.data.use_paint_mask = False
        context.object.data.use_paint_mask_vertex = False
        bpy.ops.object.vertex_group_mirror(use_topology=False)

        vertex_b = context.object.vertex_groups.active.name

        modifier_name = "VertexWeightMix"
        mix_modifier = context.object.modifiers.new(name=modifier_name, type='VERTEX_WEIGHT_MIX')
        mix_modifier.vertex_group_a = vertex_a
        mix_modifier.vertex_group_b = vertex_b
        mix_modifier.mix_mode = 'ADD'

        bpy.ops.object.modifier_apply(modifier=modifier_name)

        context.object.vertex_groups.remove(context.object.vertex_groups.get(vertex_b))

        context.object.vertex_groups.active = context.object.vertex_groups.get(vertex_a)


        return {'FINISHED'}



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
