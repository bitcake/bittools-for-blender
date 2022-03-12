import bpy
from bpy.types import Panel

modules = [
    'exporter_configs',
    'register_projects',
    'exporter_configs_drawer',
    'exporter',
]

from .. import import_or_reload_modules
modules = import_or_reload_modules(modules, __name__)

class BITCAKE_PT_universal_exporter(Panel):
    bl_idname = "BITCAKE_PT_universal_exporter"
    bl_label = "Universal Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools 2.0"

    draw_funcs = []

    def draw(self, context):
        for draw_func in __class__.draw_funcs:
            draw_func(self, context)


classes = (BITCAKE_PT_universal_exporter,)

def register():
    for module in modules:
        if hasattr(module, 'register'):
            module.register()
        if hasattr(module, 'draw_panel'):
            BITCAKE_PT_universal_exporter.draw_funcs.append(module.draw_panel)

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    BITCAKE_PT_universal_exporter.draw_funcs.clear()

    for module in modules:
        if hasattr(module, 'unregister'):
            module.unregister()
