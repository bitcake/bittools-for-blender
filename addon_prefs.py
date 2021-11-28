import bpy
import os
import addon_utils
from pathlib   import Path
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty, EnumProperty

def update_registered_projects(self, context):
    import json
    projects_list = []

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')

    if projects_file_path.is_file():
        with open('registered_projects.json', 'r') as projects:
            projects_json = json.load(projects)
            for i, project in enumerate(projects_json):
                projects_list.append((project, project, '', i))

    return projects_list


class BitCakeToolsPreferences(AddonPreferences):
    bl_idname = __package__

    isDefaultKeymaps: BoolProperty(
        name="Using Blender Default Keymaps",
        default=False,
    )

    registered_projects: EnumProperty(items=update_registered_projects, name='')

    # Prefixes Setup (user changeable)
    static_mesh_prefix: StringProperty(name='Static Mesh Prefix', default='SM_')
    skeletal_mesh_prefix: StringProperty(name='Skeletal Mesh Prefix', default='SK_')
    animation_prefix: StringProperty(name='Animation Prefix', default='Anim_')
    pose_prefix: StringProperty(name='Pose Prefix', default='Pose_')
    camera_prefix: StringProperty(name='Camera Prefix', default='Cam_')

    # Folder Paths (not user changeable)
    static_mesh_path: StringProperty(name='Static Mesh Path', default='/Art/StaticMeshes/',)
    skeletal_mesh_path: StringProperty(name='Skeletal Mesh Path', default='/Art/SkeletalMeshes/')
    animation_path: StringProperty(name='Animation Path', default='/Art/Animations/')
    pose_path: StringProperty(name='Pose Path', default='/Art/Poses/')
    camera_path: StringProperty(name='Camera Path', default='/Art/Camera/')

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
        column2.prop(self, "static_mesh_path")
        column2.prop(self, "skeletal_mesh_path")




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
