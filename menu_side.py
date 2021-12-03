import bpy
import os
import addon_utils
import json
import bpy.utils.previews
from pathlib   import Path
from bpy.types import Panel, PropertyGroup, Scene
from bpy.props import StringProperty, BoolProperty


class PanelProperties(PropertyGroup):
    custom_keymap: StringProperty(name="CurrentKeymapLabel", default="Custom Keymap")
    default_keymap: StringProperty(name="KeymapLabel", default="Default Keymap")
    export_selected: BoolProperty(name="Selected", description="Only exports selected objects", default=False)
    export_collection: BoolProperty(name="Collection", description="Exports entire collection", default=False)
    export_batch: BoolProperty(name="Batch Export", description="Exports objects in a separate file", default=False)

class BITCAKE_PT_menu(Panel):
    bl_idname = "BITCAKE_PT_menu"
    bl_label = "Hotkey Changer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"

    def draw(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props

        addonPrefs = context.preferences.addons[__package__].preferences

        if not addonPrefs.isDefaultKeymaps:
            button_label = panel_prefs.default_keymap
            current_label = panel_prefs.custom_keymap
        else:
            button_label = panel_prefs.custom_keymap
            current_label = panel_prefs.default_keymap

        layout = self.layout
        row = layout.row()
        row.label(text="Hotkey Changer")
        row = layout.row()
        row.label(text='Current Keymap: ' + current_label)
        row = layout.row()
        row.operator('bitcake.hotkeychanger',text=button_label)

class BITCAKE_PT_send_to_engine(Panel):
    bl_idname = "BITCAKE_PT_send_to_engine"
    bl_label = "BitCake Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"

    def draw(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props

        addonPrefs = context.preferences.addons[__package__].preferences

        pcoll = preview_collections["main"]
        unity_logo = pcoll["unity"]
        unreal_logo = pcoll["unreal"]
        cocos_logo = pcoll["cocos"]

        registered_projects_path = get_registered_projects_path()

        current_engine = None
        if registered_projects_path.is_file():
            projects_json = json.load(registered_projects_path.open())
            current_engine = projects_json[addonPrefs.registered_projects]['engine']


        layout = self.layout
        row = layout.row()
        row.label(text="Send to Project")
        row = layout.row()
        row.prop(addonPrefs, 'registered_projects')
        row.operator('bitcake.register_project', icon='ADD', text='')

        # If there's no Project Registered, don't draw the rest of the menu
        if not current_engine:
            return

        row = layout.row()
        row.prop(panel_prefs, 'export_batch', toggle=1, icon_value=1, icon='FILE_NEW')

        if current_engine == 'Unity':
            row = layout.row()
            if not panel_prefs.export_batch:
                row.operator('bitcake.send_to_engine', text='Send to Unity', icon_value=unity_logo.icon_id)
            else:
                row.operator('bitcake.batch_send_to_engine', text='Batch Send to Unity', icon_value=unity_logo.icon_id)

        elif current_engine == 'Unreal':
            row = layout.row()
            if not panel_prefs.export_batch:
                row.operator('bitcake.send_to_engine', text='Send to Unreal', icon_value=unreal_logo.icon_id)
            else:
                row.operator('bitcake.batch_send_to_engine', text='Batch Send to Unreal', icon_value=unreal_logo.icon_id)

        elif current_engine == 'Cocos':
            row = layout.row()
            if not panel_prefs.export_batch:
                row.operator('bitcake.send_to_engine', text='Send to Cocos', icon_value=cocos_logo.icon_id)
            else:
                row.operator('bitcake.batch_send_to_engine', text='Batch Send to Cocos', icon_value=cocos_logo.icon_id)

        row = layout.row()
        row.prop(panel_prefs, 'export_selected')
        row.prop(panel_prefs, 'export_collection')
        row = layout.row()
        row = layout.row()
        row.operator('bitcake.toggle_all_colliders_visibility', text='Toggle Colliders Visibility', icon='HIDE_OFF')
        row = layout.row()
        row.operator('bitcake.custom_butten', text='Custom Butten')

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


def get_registered_projects_path():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')

    return projects_file_path


classes = (PanelProperties, BITCAKE_PT_menu, BITCAKE_PT_send_to_engine, BITCAKE_PT_animtools)
preview_collections = {}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


    # Register Custom Icons
    pcoll = bpy.utils.previews.new()
    bittools_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("unity", os.path.join(bittools_icons_dir, "unity_logo.png"), 'IMAGE')
    pcoll.load("unreal", os.path.join(bittools_icons_dir, "unreal_logo.png"), 'IMAGE')
    pcoll.load("cocos", os.path.join(bittools_icons_dir, "cocos_logo.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    Scene.menu_props = bpy.props.PointerProperty(type=PanelProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # UnRegister Custom Icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    del Scene.menu_props