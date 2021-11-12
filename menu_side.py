import bpy
from bpy.types import Panel, PropertyGroup, Scene


class PanelProperties(PropertyGroup):
    custom_keymap: bpy.props.StringProperty(name="CurrentKeymapLabel", default="Custom Keymap")
    default_keymap: bpy.props.StringProperty(name="KeymapLabel", default="Default Keymap")


class BITCAKE_PT_menu(Panel):
    bl_idname = "BITCAKE_PT_menu"
    bl_label = "BitCake Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitCake Tools"

    def draw(self, context):
        scene = context.scene
        mytool = scene.menu_props

        addonPrefs = context.preferences.addons[__package__].preferences

        if not addonPrefs.isDefaultKeymaps:
            button_label = mytool.default_keymap
            current_label = mytool.custom_keymap
        else:
            button_label = mytool.custom_keymap
            current_label = mytool.default_keymap

        layout = self.layout
        row = layout.row()
        row.label(text="Hotkey Changer")
        row = layout.row()
        row.label(text='Current Keymap: ' + current_label)
        row = layout.row()
        row.operator('bitcake.hotkeychanger',text=button_label)

class BITCAKE_PT_animtools(Panel):
    bl_idname = "BITCAKE_PT_animtools"
    bl_label = "Anim Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "posemode"
    bl_category = "Item"

    def draw(self, context):
        properties = context.scene.menu_props
        animtool_props = context.scene.animtool_props

        addonPrefs = context.preferences.addons[__package__].preferences

        layout = self.layout
        layout.label(text='Breakdowner')
        row = layout.row()
        row.prop(animtool_props, 'breakdowner', slider=True)
        row = layout.row()
        row.operator('bitcake.breakdowner', text='0').breakdown_value=0.0
        row.operator('bitcake.breakdowner', text='25').breakdown_value=0.25
        row.operator('bitcake.breakdowner', text='50').breakdown_value=0.5
        row.operator('bitcake.breakdowner', text='75').breakdown_value=0.75
        row.operator('bitcake.breakdowner', text='100').breakdown_value=1.0


# bpy.ops.pose.breakdown(factor=0.733291, prev_frame=0, next_frame=30)

classes = (PanelProperties, BITCAKE_PT_menu, BITCAKE_PT_animtools)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.menu_props = bpy.props.PointerProperty(type=PanelProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.menu_props