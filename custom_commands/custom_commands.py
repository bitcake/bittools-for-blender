import bpy
import re
from pathlib import Path
from bpy.types import Operator

class BITCAKE_OT_incremental_save(Operator):
    bl_idname = "bitcake.incremental_save"
    bl_label = "BitTools Incremental Save"
    bl_description = "Increases or Adds a number count at the end of the file and saves it!"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        filepath = Path(bpy.data.filepath)
        stem = filepath.stem

        split_stem = stem.split('_')
        if split_stem[-1].isnumeric():
            num = int(split_stem[-1]) + 1
            split_stem.pop()
            split_stem.append(str(num))
            final_name = '_'.join(split_stem)
            print(final_name)

        else:
            pattern = r'[0-9]'

            new_string = re.sub(pattern, "", str(filepath.stem))
            final_name = new_string + "_1"

        filepath = filepath.with_stem(final_name)
        bpy.ops.wm.save_mainfile(filepath=str(filepath))


        self.report(type={'INFO'} , message="Save successful!")

        return {'FINISHED'}

def draw_panel(self, context):
    layout = self.layout

    row = layout.row()
    row.operator('bitcake.incremental_save', text='Test Butten')

    return


classes = (BITCAKE_OT_incremental_save,)
addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(BITCAKE_OT_incremental_save.bl_idname, type='S', value='PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()