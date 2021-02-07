import os
import bpy


def BackupHotkeys(self, context):
    addonDir = os.path.dirname(os.path.realpath(__file__))
    originalHotkeyDir = addonDir + r"\Keymaps\Original_Keymap.py"
    bitcakeHotkeyDir = addonDir + r"\Keymaps\BitCake_Keymap.py"

    addonPrefs = context.preferences.addons[__package__].preferences

    if os.path.isfile(originalHotkeyDir):
        print("Original_Keymap.py file already exists!")
    else:
        bpy.ops.preferences.keyconfig_export(filepath=originalHotkeyDir)
        print("Original_Keymap.py backup file created")

    if addonPrefs.boolean:
        bpy.ops.preferences.keyconfig_import(filepath=bitcakeHotkeyDir)
        bpy.ops.preferences.keyconfig_activate(filepath=bitcakeHotkeyDir)
        bpy.ops.wm.save_userpref()
        print("Using BitCake Hotkey!")
    else:
        bpy.ops.preferences.keyconfig_import(filepath=originalHotkeyDir)
        bpy.ops.preferences.keyconfig_activate(filepath=originalHotkeyDir)
        bpy.ops.wm.save_userpref()
        print("Using Custom Hotkey!")
