from bpy.types import AddonPreferences
from bpy.props import BoolProperty, IntProperty, StringProperty

from . import scene_setup


class BitCakeToolsPreferences(AddonPreferences):
    bl_idname = __package__

    toggle_animation_tools: BoolProperty(
        name="Animation Tools",
        default=True,
    )

    toggle_collider_tools: BoolProperty(
        name="Collider Tools",
        default=True,
    )

    toggle_rigging_tools: BoolProperty(
        name="Rigging Tools",
        default=True,
    )

    toggle_custom_commands: BoolProperty(
        name="Custom Commands Menu",
        default=True,
    )

    toggle_dev_tools: BoolProperty(
        name="Development Tools",
        default=True,
    )

    separator: StringProperty(name='Characater that separates naming', default='_')
    wip: StringProperty(name='WIP Folder name', default='WIP')
    published: StringProperty(name='Published Folder name', default='Published')
    art: StringProperty(name='In-Engine Art Folder name', default='Art')

    # Collider Prefixes Setup (NOT user changeable)
    box_collider_prefix: StringProperty(name='Box Collider Prefix', default='UBX')
    capsule_collider_prefix: StringProperty(name='Capsule Collider Prefix', default='UCP')
    sphere_collider_prefix: StringProperty(name='Sphere Collider Prefix', default='USP')
    convex_collider_prefix: StringProperty(name='Convex Collider Prefix', default='UCX')
    mesh_collider_prefix: StringProperty(name='Mesh Collider Prefix', default='UME')

    # Folder Paths (NOT user changeable)
    static_mesh_path: StringProperty(name='Static Mesh Path', default='/Art/StaticMeshes/',)
    skeletal_mesh_path: StringProperty(name='Skeletal Mesh Path', default='/Art/SkeletalMeshes/')
    animation_path: StringProperty(name='Animation Path', default='/Art/Animations/')
    pose_path: StringProperty(name='Pose Path', default='/Art/Poses/')
    camera_path: StringProperty(name='Camera Path', default='/Art/Camera/')

    #Scene Setup
    fps: IntProperty(name='Scene FPS', default=30, min=24, max=120, update=scene_setup.update_scene_fps)
    auto_save: BoolProperty(name="Auto Incremental-Save", default=True, description='Turn on or off auto incremental saving')
    auto_save_time: IntProperty(name="Auto Save Timer (Minutes)", default=30, min=10, description='Set the time for auto-saving')


    def draw(self, context):
        layout = self.layout

        box = layout.box().column_flow(columns=1)
        column = box.column()
        column.label(text="Menu Configs")
        column.prop(self, "toggle_animation_tools")
        column.prop(self, "toggle_collider_tools")
        column.prop(self, "toggle_custom_commands")
        column.prop(self, "toggle_rigging_tools")
        column.prop(self, "toggle_dev_tools")


        box = layout.box().column_flow(columns=2)
        column = box.column()
        column2 = box.column()

        column2.label(text='Scene Configs')
        column2.prop(self, "fps")
        row = column2.row(align=True)
        row.prop(self, "auto_save", text='Auto Save', icon='FILE_NEW')
        row.prop(self, "auto_save_time", text='Timer (mins)')


classes = (BitCakeToolsPreferences,)

# Registration
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
