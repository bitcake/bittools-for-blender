import bpy
import os
import bpy.utils.previews
from bpy.types import Panel, PropertyGroup, Scene
from bpy.props import StringProperty, BoolProperty
from .helpers import get_addon_prefs, get_current_engine


class PanelProperties(PropertyGroup):
    export_selected: BoolProperty(name="Selected", description="Only exports selected objects", default=False)
    export_collection: BoolProperty(name="Collection", description="Exports entire collection", default=False)
    export_batch: BoolProperty(name="Batch", description="Exports objects in a separate file", default=False)
    origin_transform: BoolProperty(name="Origin", description="Place objects in origin before exporting", default=False)
    apply_transform: BoolProperty(name="Apply", description="Apply transforms before exporting", default=False)
    export_nla_strips: BoolProperty(name="Export NLA Strips", description="Separate NLA Strips into their own animations when exporting.\nYou'll usually want this turned OFF for Game Engine", default=False)


class BITCAKE_PT_send_to_engine(Panel):
    bl_idname = "BITCAKE_PT_send_to_engine"
    bl_label = "BitCake Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"

    def draw(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props

        addon_prefs = get_addon_prefs()

        current_engine = get_current_engine()

        layout = self.layout
        row = layout.row()
        row.label(text="Send to Project")
        row = layout.row()
        row.prop(addon_prefs, 'registered_projects')
        row.operator('bitcake.register_project', icon='ADD', text='')

        # If there's no Project Registered, don't draw the rest of the menu below
        if not current_engine:
            return

        row.operator('bitcake.unregister_project', icon='REMOVE', text='')

        row = layout.row(align=True)
        row.prop(panel_prefs, 'origin_transform', toggle=1, icon_value=1, icon='OBJECT_ORIGIN')
        row.prop(panel_prefs, 'apply_transform', toggle=1, icon_value=1, icon='CHECKMARK')
        row.prop(panel_prefs, 'export_batch', toggle=1, icon_value=1, icon='FILE_NEW')

        row = layout.row(align=True)
        row.prop(panel_prefs, 'export_nla_strips', toggle=1, icon_value=1, icon='NLA')

        row = layout.row(align=True)
        row.prop(panel_prefs, 'export_selected', toggle=1, icon='RESTRICT_SELECT_OFF')
        row.prop(panel_prefs, 'export_collection', toggle=1, icon='OUTLINER_COLLECTION')
        row = layout.row()
        row.operator('bitcake.toggle_all_colliders_visibility', text='Toggle Colliders Visibility', icon='HIDE_OFF')

        layout.separator()
        layout.label(text='Export')
        send_to_engine_button(self, context)
        send_to_custom(self, context)

        layout.separator()
        layout.separator()
        layout.label(text='Test Stuff')
        row = layout.row()
        row.operator('bitcake.custom_butten', text='Test Butten')


def send_to_engine_button(self, context):
    panel_prefs = context.scene.menu_props
    layout = self.layout

    pcoll = preview_collections["main"]
    unity_logo = pcoll["unity"]
    unreal_logo = pcoll["unreal"]
    cocos_logo = pcoll["cocos"]

    current_engine = get_current_engine()

    if current_engine == 'Unity':
        row = layout.row()
        if not panel_prefs.export_batch:
            row.operator('bitcake.send_to_engine', text='Send to Unity Project', icon_value=unity_logo.icon_id)
        else:
            row.operator('bitcake.batch_send_to_engine', text='Batch Send to Unity', icon_value=unity_logo.icon_id)

    elif current_engine == 'Unreal':
        row = layout.row()
        if not panel_prefs.export_batch:
            row.operator('bitcake.send_to_engine', text='Send to Unreal Project', icon_value=unreal_logo.icon_id)
        else:
            row.operator('bitcake.batch_send_to_engine', text='Batch Send to Unreal',
                            icon_value=unreal_logo.icon_id)

    elif current_engine == 'Cocos':
        row = layout.row()
        if not panel_prefs.export_batch:
            row.operator('bitcake.send_to_engine', text='Send to Cocos Project', icon_value=cocos_logo.icon_id)
        else:
            row.operator('bitcake.batch_send_to_engine', text='Batch Send to Cocos', icon_value=cocos_logo.icon_id)


def send_to_custom(self, context):
    panel_prefs = context.scene.menu_props
    layout = self.layout

    row = layout.row()
    if not panel_prefs.export_batch:
        op = row.operator('bitcake.send_to_engine', text='Send to Custom Folder', icon='EXPORT')
        op.sending_to_engine = False
    else:
        row.operator('bitcake.batch_send_to_engine', text='Batch Send to Custom Folder', icon='EXPORT')

class BITCAKE_PT_collider_tools(Panel):
    bl_idname = "BITCAKE_PT_collider_tools"
    bl_label = "Collider Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"

    def draw(self, context):
        properties = context.scene.menu_props
        animtool_props = context.scene.animtool_props

        addon_prefs = get_addon_prefs()
        pcol = [addon_prefs.box_collider_prefix,
                addon_prefs.capsule_collider_prefix,
                addon_prefs.sphere_collider_prefix,
                addon_prefs.convex_collider_prefix,
                addon_prefs.mesh_collider_prefix]

        current_engine = get_current_engine()

        layout = self.layout
        row = layout.row()
        row.operator('bitcake.add_box_collider', text=f'Add Box Collider ({pcol[0]})', icon='CUBE')
        row = layout.row()
        row.operator('bitcake.add_sphere_collider', text=f'Add Sphere Collider ({pcol[2]})', icon='SPHERE')
        row = layout.row()
        row.operator('bitcake.add_convex_collider', text=f'Add Convex Collider ({pcol[3]})', icon='MESH_ICOSPHERE')

        if current_engine == 'Unity':
            row = layout.row()
            row.operator('bitcake.add_mesh_collider', text=f'Add Mesh Collider ({pcol[4]})', icon='MESH_MONKEY')


class BITCAKE_PT_rigging_tools(Panel):
    bl_idname = "BITCAKE_PT_rigging_tools"
    bl_label = "Rigging Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BitTools"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('bitcake.set_deform_bones', text='Set Deform Bones', icon='BONE_DATA')
        row = layout.row()
        row.operator('bitcake.shape_keys_to_custom_props', text='Shape Keys to Props', icon='CON_ACTION')


classes = (PanelProperties,
           BITCAKE_PT_send_to_engine,
           BITCAKE_PT_collider_tools,
           BITCAKE_PT_rigging_tools)

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
