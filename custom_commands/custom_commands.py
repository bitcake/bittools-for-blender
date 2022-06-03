import bpy
import re
from pathlib import Path
from ..helpers import get_addon_prefs, get_published_path, is_wip_in_path
from bpy.types import Operator

class BITCAKE_OT_incremental_save(Operator):
    bl_idname = "bitcake.incremental_save"
    bl_label = "Incremental Save"
    bl_description = "Increases or Adds a number count at the end of the file and saves it!"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        filepath = Path(bpy.data.filepath)

        incremental_name = increment_filename(filepath)

        filepath = filepath.with_stem(incremental_name)
        bpy.ops.wm.save_mainfile(filepath=str(filepath))

        self.report(type={'INFO'} , message="Save successful!")

        return {'FINISHED'}


class BITCAKE_OT_increment_and_master_save(Operator):
    bl_idname = "bitcake.increment_and_master_save"
    bl_label = "Incremental Save and Send to Published"
    bl_description = "Increases or Adds a number count at the end of the file and saves it!"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        filepath = Path(bpy.data.filepath)
        published_path = get_published_path()

        incremental_name = increment_filename(filepath)
        incremental_path = filepath.with_stem(incremental_name)
        master_name = master_filename(incremental_name)
        master_path = published_path.with_stem(master_name)

        bpy.ops.wm.save_mainfile(filepath=str(master_path))
        bpy.ops.wm.save_mainfile(filepath=str(incremental_path))

        self.report(type={'INFO'} , message="Save successful!")

        return {'FINISHED'}


def increment_filename(path):
    addon_prefs = get_addon_prefs()
    sep = addon_prefs.separator
    stem = path.stem

    split_stem = stem.split(sep)
    if split_stem[-1].isnumeric():
        num = int(split_stem[-1]) + 1
        split_stem.pop()
        split_stem.append(str(num))
        incremental_name = sep.join(split_stem)
        print(incremental_name)

    else:
        addon_prefs = get_addon_prefs()
        pattern = r'[0-9]'

        new_string = re.sub(pattern, "", str(path.stem))
        incremental_name = new_string + addon_prefs.separator + "1"

    return incremental_name


def master_filename(filename):
    addon_prefs = get_addon_prefs()
    sep = addon_prefs.separator
    master = filename.split(sep)

    master.pop()
    master.append('Master')
    master_name = sep.join(master)

    return master_name


def draw_panel(self, context):
    layout = self.layout

    row = layout.row()
    row.operator('bitcake.incremental_save', text='Incremental Save')
    row = layout.row()
    row.operator('bitcake.increment_and_master_save', text='Incremental Save and Send to Published')

    return


classes = (BITCAKE_OT_incremental_save,
           BITCAKE_OT_increment_and_master_save,)
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

        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(BITCAKE_OT_increment_and_master_save.bl_idname, type='S', value='PRESS', ctrl=True, alt=True, shift=True)
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()