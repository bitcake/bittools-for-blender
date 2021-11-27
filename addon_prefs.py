from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty


class BitCakeToolsPreferences(AddonPreferences):
    bl_idname = __package__

    isDefaultKeymaps: BoolProperty(
        name="Using Blender Default Keymaps",
        default=False,
    )

    static_mesh_prefix: StringProperty(name='Static Mesh Prefix', default='SM_')
    skeletal_mesh_prefix: StringProperty(name='Skeletal Mesh Prefix', default='SK_')
    animation_prefix: StringProperty(name='Animation Prefix', default='Anim_')
    pose_prefix: StringProperty(name='Pose Prefix', default='Pose_')
    camera_prefix: StringProperty(name='Camera Prefix', default='Cam_')


    def draw(self, context):
        layout = self.layout
        layout.label(text="HotkeyChanger")
        layout.prop(self, "isDefaultKeymaps")

        box = layout.box().column_flow(columns=2)
        column = box.column()
        column2 = box.column()

        column.label(text="Prefixes")
        column.prop(self, "static_mesh_prefix")
        column.prop(self, "skeletal_mesh_prefix")
        column.prop(self, "animation_prefix")
        column.prop(self, "pose_prefix")
        column.prop(self, "camera_prefix")

        column2.label(text='Paths')




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
