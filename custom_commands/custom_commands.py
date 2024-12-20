import bpy
import re
import os
from pathlib import Path
from ..helpers import get_addon_prefs, get_published_path, is_inside_published
from bpy.types import Operator

class BITCAKE_OT_incremental_save(Operator):
    bl_idname = "bitcake.incremental_save"
    bl_label = "Incremental Save"
    bl_description = "Increases or Adds a number count at the end of the file and saves it!"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        filepath = bpy.data.filepath

        # If file has never been saved or there aren't any changes don't run
        if not bpy.data.is_saved or not bpy.data.is_dirty:
            return {'CANCELLED'}

        filepath = Path(filepath)
        if is_inside_published(filepath.parent):
            return {'CANCELLED'}

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
        filepath = bpy.data.filepath

        # If file has never been saved or there aren't any changes don't run
        if not bpy.data.is_saved or not bpy.data.is_dirty:
            return {'CANCELLED'}

        filepath = Path(filepath)
        if is_inside_published(filepath.parent):
            return {'CANCELLED'}

        published_path = get_published_path()

        incremental_name = increment_filename(filepath)
        incremental_path = filepath.with_stem(incremental_name)
        master_name = master_filename(incremental_name)
        master_path = published_path.with_stem(master_name)

        os.makedirs(published_path.parent, exist_ok=True)

        bpy.ops.wm.save_mainfile(filepath=str(master_path))
        bpy.ops.wm.save_mainfile(filepath=str(incremental_path))

        self.report(type={'INFO'} , message="Save successful!")

        return {'FINISHED'}


class BITCAKE_OT_deduplicate_materials(Operator):
    bl_idname = "bitcake.deduplicate_materials"
    bl_label = "Deduplicate Materials"
    bl_description = "Remove all materials that have the same name as another (except by the .NNN suffix). Will also delete the duplicates"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        pattern = re.compile(r"(.*)\.\d{3}$")
        duplicate_to_base_material = {} # iterate over all materials in the project
        for material in bpy.data.materials:
            match = pattern.match(material.name)
            if match:
                base_name = match.group(1)
                base_material = bpy.data.materials.get(base_name)
                duplicate_to_base_material[material] = base_material

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                mesh = obj.data
                for i, slot in enumerate(mesh.materials):
                    original_material = duplicate_to_base_material.get(slot)
                    if original_material:
                        mesh.materials[i] = original_material

        duplicate_count = len(duplicate_to_base_material)

        for duplicate in duplicate_to_base_material:
            if duplicate.users == 0:
                bpy.data.materials.remove(duplicate)

        self.report(type={'INFO'} , message=f"Removed {duplicate_count} duplicated materials")
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


def auto_incremental_save():
    addon_prefs = get_addon_prefs()

    if addon_prefs.auto_save:
        bpy.ops.bitcake.incremental_save()

    return addon_prefs.auto_save_time * 60


def draw_panel(self, context):
    layout = self.layout

    row = layout.row()
    row.operator('bitcake.incremental_save', text='Incremental Save')
    row = layout.row()
    row.operator('bitcake.increment_and_master_save', text='Incremental Save and Send to Published')
    row = layout.row()
    row.operator('bitcake.deduplicate_materials', text='Deduplicate Materials')

    return


classes = (
    BITCAKE_OT_incremental_save,
    BITCAKE_OT_increment_and_master_save,
    BITCAKE_OT_deduplicate_materials,
)

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.timers.register(auto_incremental_save)

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
    try:
        bpy.app.timers.unregister(auto_incremental_save)
    except ValueError:
        pass

    for cls in classes:
        bpy.utils.unregister_class(cls)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
