import os
import bpy
from bpy.types import Context, Operator
from .SideMenu import BITCAKE_PT_SideMenu, BITCAKE_PT_SideMenuSettings


class BITCAKE_OT_hotkeychanger(Operator):
    bl_idname = "bitcake.hotkeychanger"
    bl_label = ""
    bl_description = "Change your current Hotkeys to Blender's default and back. (This will save your current Custom Hotkeys)"

    addonDir = os.path.dirname(os.path.realpath(__file__))
    customHotkeyDir = addonDir + r"\Keymaps\Custom_Keymap.py"
    blenderHotkeyFile = addonDir + r"\Keymaps\Blender_291_Keymap.py"

    def toggledefaulthotkey(self, context):
        addonPrefs = context.preferences.addons[__package__].preferences
        menu_props = bpy.context.scene.side_menu_props
        print("*" * 40)
        print(menu_props.IsCustomHotkey)
        print("*" * 40)

        if addonPrefs.isDefaultHotkey:
            bpy.ops.preferences.keyconfig_import(
                filepath=self.customHotkeyDir)
            bpy.ops.preferences.keyconfig_activate(
                filepath=self.customHotkeyDir)
            bpy.ops.wm.save_userpref()

            menu_props.IsCustomHotkey = True

            addonPrefs.isDefaultHotkey = False
            print("Voce ta usando Custom Hotkey!")
        else:
            bpy.ops.preferences.keyconfig_export(
                filepath=self.customHotkeyDir)
            bpy.ops.preferences.keyconfig_import(
                filepath=self.blenderHotkeyFile)
            bpy.ops.wm.save_userpref()

            menu_props.IsCustomHotkey = False

            addonPrefs.isDefaultHotkey = True
            print("Voce ta usando Default Hotkey!")

        return {'FINISHED'}

    @ classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        self.toggledefaulthotkey(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(BITCAKE_OT_hotkeychanger)


def unregister():
    bpy.utils.unregister_class(BITCAKE_OT_hotkeychanger)
