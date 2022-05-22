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
        return context.mode == 'OBJECT'

    def execute(self, context):
        mesh = context.object.data
        selected_verts = [v for v in mesh.vertices if v.select]

        print(selected_verts[0].groups.items())
        print(selected_verts[0].groups.items()[2][1].weight)


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
