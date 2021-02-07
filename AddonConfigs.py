import bpy
from .HotkeyChooser import BackupHotkeys
from bpy.types import AddonPreferences
from bpy.props import BoolProperty


class BITCAKE_PT_preferences(AddonPreferences):
    bl_idname = __package__

    boolean: BoolProperty(
        name="Use BitCake's Maya-like Hotkey",
        description="The first time you press this button it'll create a backup of your current hotkeys and you'll be able to revert back. Warning: If you changed keys after creating the backup you will lose them when reverting!",
        default=False,
        update=BackupHotkeys,
    )
    isDefaultHotkey: BoolProperty(
        name="User is using Default Hotkey",
        default=False,
    )

    def __init__(self):
        self.layout = None

    def draw(self, context):
        layout = self.layout
        layout.label(text="Set your preferences")
        layout.prop(self, "boolean")


def register():
    bpy.utils.register_class(BITCAKE_PT_preferences)


def unregister():
    bpy.utils.unregister_class(BITCAKE_PT_preferences)
