import bpy
from bpy.types import Panel
from ..helpers import get_addon_prefs

modules = [
    'custom_commands',
]

from .. import import_or_reload_modules
modules = import_or_reload_modules(modules, __name__)

class BITCAKE_PT_custom_commands(Panel):
    bl_idname = "BITCAKE_PT_custom_commands"
    bl_label = "Custom Commands"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"

    draw_funcs = []

    @classmethod
    def poll(cls, context):
        addon_prefs = get_addon_prefs()
        return addon_prefs.toggle_custom_commands

    def draw(self, context):
        for draw_func in __class__.draw_funcs:
            draw_func(self, context)


classes = (BITCAKE_PT_custom_commands,)

def register():
    for module in modules:
        if hasattr(module, 'register'):
            module.register()
        if hasattr(module, 'draw_panel'):
            BITCAKE_PT_custom_commands.draw_funcs.append(module.draw_panel)

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    BITCAKE_PT_custom_commands.draw_funcs.clear()

    for module in modules:
        if hasattr(module, 'unregister'):
            module.unregister()
