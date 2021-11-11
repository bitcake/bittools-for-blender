import bpy
from bpy.types import Panel, PropertyGroup, Scene
from bpy.props import FloatProperty



class PanelProperties(PropertyGroup):
    custom_keymap: bpy.props.StringProperty(name="CurrentKeymapLabel", default="Custom Keymap")
    default_keymap: bpy.props.StringProperty(name="KeymapLabel", default="Default Keymap")
    Breakdowner: FloatProperty(
        name="Breakdowner",
        description="Set breakdown value towards either the last frame or the next, in percentage",
        min=0.0, max=1.0,
        default=0.5,
        )

class BITCAKE_PT_menu(Panel):
    bl_idname = "BITCAKE_PT_menu"
    bl_label = "BitCake Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitCake Tools"

    def draw(self, context):
        scene = context.scene
        mytool = scene.my_tool

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
    bl_label = "Test Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"



    def draw(self, context):
        scene = context.scene
        mytool = scene.my_tool
        slider = mytool.Breakdowner

        print(slider)
        addonPrefs = context.preferences.addons[__package__].preferences

        layout = self.layout
        row = layout.row()
        row.prop(mytool, 'slider', slider=True)
        row = layout.row()
        row.operator('pose.breakdown', text='0')
        row.operator('pose.breakdown', text='25')
        row.operator('pose.breakdown', text='50')
        row.operator('pose.breakdown', text='75')
        row.operator('pose.breakdown', text='100')

# bpy.ops.pose.breakdown(factor=0.733291, prev_frame=0, next_frame=30)

classes = (PanelProperties, BITCAKE_PT_menu, BITCAKE_PT_animtools)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.my_tool = bpy.props.PointerProperty(type=PanelProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.my_tool