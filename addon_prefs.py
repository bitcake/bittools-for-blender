import json
import addon_utils
from pathlib   import Path
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty
from .helpers import get_registered_projects_path

from . import scene_setup


def update_registered_projects(self, context):
    projects_list = []

    projects_file_path = get_registered_projects_path()

    if projects_file_path.is_file():
        with open(str(projects_file_path), 'r') as projects:
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

    registered_projects: EnumProperty(items=update_registered_projects,
                                      name='',
                                      description='Register projects here before starting. Current Active project',
                                      )

    separator: StringProperty(name='Characater that separates naming', default='_')

    # Prefixes Setup (user changeable)
    static_mesh_prefix: StringProperty(name='Static Mesh Prefix', default='SM')
    skeletal_mesh_prefix: StringProperty(name='Skeletal Mesh Prefix', default='SK')
    animation_prefix: StringProperty(name='Animation Prefix', default='Anim')
    pose_prefix: StringProperty(name='Pose Prefix', default='Pose')
    camera_prefix: StringProperty(name='Camera Prefix', default='Cam')

    # Collider Prefixes Setup (user changeable)
    box_collider_prefix: StringProperty(name='Box Collider Prefix', default='UBX')
    capsule_collider_prefix: StringProperty(name='Capsule Collider Prefix', default='UCP')
    sphere_collider_prefix: StringProperty(name='Sphere Collider Prefix', default='USP')
    convex_collider_prefix: StringProperty(name='Convex Collider Prefix', default='UCX')
    mesh_collider_prefix: StringProperty(name='Mesh Collider Prefix', default='UME')

    # Folder Paths (not user changeable)
    static_mesh_path: StringProperty(name='Static Mesh Path', default='/Art/StaticMeshes/',)
    skeletal_mesh_path: StringProperty(name='Skeletal Mesh Path', default='/Art/SkeletalMeshes/')
    animation_path: StringProperty(name='Animation Path', default='/Art/Animations/')
    pose_path: StringProperty(name='Pose Path', default='/Art/Poses/')
    camera_path: StringProperty(name='Camera Path', default='/Art/Camera/')

    #Scene Setup
    fps: IntProperty(name='Scene FPS', default=30, min=24, max=120, update=scene_setup.update_scene_fps)

    def draw(self, context):
        layout = self.layout

        box = layout.box().column_flow(columns=2)
        column = box.column()
        column2 = box.column()

        column.label(text="Prefixes")
        column.prop(self, "static_mesh_prefix")
        column.prop(self, "skeletal_mesh_prefix")
        column.prop(self, "animation_prefix")
        column.prop(self, "pose_prefix")
        column.prop(self, "camera_prefix")

        column2.label(text='Scene Configs')
        column2.prop(self, "fps")


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
