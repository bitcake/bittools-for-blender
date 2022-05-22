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
        string_test = 'Penis.01'
        print(string_test[:-1])

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
