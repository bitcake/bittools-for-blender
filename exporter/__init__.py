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
    bl_category = "BitTools"

    draw_funcs = []

    def draw(self, context):
        for draw_func in __class__.draw_funcs:
            draw_func(self, context)


class BITCAKE_PT_nomenclature(Panel):
    bl_idname = "BITCAKE_PT_nomenclature"
    bl_label = "Export Nomenclature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"
    bl_parent_id = "BITCAKE_PT_universal_exporter"

    def draw(self, context):
        exporter_configs = context.scene.exporter_configs
        layout = self.layout

        layout.label(text='Prefixes')

        # row = layout.row(align=True)
        # row.prop(exporter_configs, 'separator')
        row = layout.row(align=True)
        row.prop(exporter_configs, 'static_mesh_prefix')
        row = layout.row(align=True)
        row.prop(exporter_configs, 'skeletal_mesh_prefix')
        row = layout.row(align=True)
        row.prop(exporter_configs, 'animation_prefix')
        row = layout.row(align=True)
        row.prop(exporter_configs, 'pose_prefix')
        row = layout.row(align=True)
        row.prop(exporter_configs, 'camera_prefix')

        return

classes = (BITCAKE_PT_universal_exporter, BITCAKE_PT_nomenclature,)

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
