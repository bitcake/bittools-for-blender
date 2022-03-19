import json
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
    else:
        projects_list = [("NONE", "No Projects Registered", "", 0),]

    return projects_list


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

    toggle_dev_tools: BoolProperty(
        name="Development Tools",
        default=True,
    )

    registered_projects: EnumProperty(items=update_registered_projects,
                                      name='',
                                      description='Register projects here before starting. Current Active project',
                                      )

    separator: StringProperty(name='Characater that separates naming', default='_')

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

    def draw(self, context):
        layout = self.layout

        box = layout.box().column_flow(columns=1)
        column = box.column()
        column.label(text="Menu Configs")
        column.prop(self, "toggle_animation_tools")
        column.prop(self, "toggle_collider_tools")
        column.prop(self, "toggle_rigging_tools")
        column.prop(self, "toggle_dev_tools")


        box = layout.box().column_flow(columns=2)
        column = box.column()
        column2 = box.column()

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
