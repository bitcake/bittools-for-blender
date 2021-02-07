import bpy
from bpy.types import Panel


class BITCAKE_PT_SideMenuSettings(bpy.types.PropertyGroup):
    IsCustomHotkey = bpy.props.BoolProperty(
        name='IsCustomHotkey',
        default=True
    )


class BITCAKE_PT_SideMenu(Panel):
    bl_idname = "BITCAKE_PT_SideMenu"
    bl_label = "BitCake Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitCake Tools"

    # buttonLabel: bpy.props.StringProperty(name="ButtonName")
    # buttonLabel = "Custom Hotkeys"

    def draw(self, context):
        hotkeyButtonLabel = "Custom Hotkeys"
        layout = self.layout
        props = context.scene.side_menu_props

        row = layout.row()
        row.label(text="Hotkey Changer")
        row = layout.row()
        # row.operator('bitcake.hotkeychanger', text=hotkeyButtonLabel)

        if props.IsCustomHotkey:
            row.operator('bitcake.hotkeychanger', text="Custom Hotkeys")
        else:
            row.operator('bitcake.hotkeychanger', text="Default Hotkeys")
        row = layout.row()
        row.prop(props, "IsCustomHotkey")


classes = (
    BITCAKE_PT_SideMenu,
    BITCAKE_PT_SideMenuSettings
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.side_menu_props = bpy.props.PointerProperty(
        type=BITCAKE_PT_SideMenuSettings)


def unregister():
    del bpy.types.Scene.side_menu_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
