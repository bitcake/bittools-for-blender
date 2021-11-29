import bpy
import json
import addon_utils
from bpy.types           import Operator
from bpy_extras.io_utils import ImportHelper
from pathlib             import Path


class BITCAKE_OT_send_to_unity(Operator):
    bl_idname = "bitcake.send_to_unity"
    bl_label = "Send to Unity"
    bl_description = "Quick export with settings aimed at Unity Game Engine"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props

        if panel_prefs.export_collection:
            change_active_collection()

        path = 'D:\\GitProjects\\Bitstrap\\Assets\\DoNotVersionControlThis\\macaco.fbx'
        bpy.ops.export_scene.fbx(
            filepath=path,
            bake_space_transform=True,
            axis_forward='-Z',
            axis_up='Y',
            use_selection=panel_prefs.export_selected,
            use_active_collection=panel_prefs.export_collection,
            )
        return {'FINISHED'}


class BITCAKE_OT_custom_butten(Operator):
    bl_idname = "bitcake.custom_butten"
    bl_label = "Do test stuff"
    bl_description = "Just test stuff"


    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        addonPrefs = context.preferences.addons[__package__].preferences
        print(addonPrefs.registered_projects)
        return {'FINISHED'}


class BITCAKE_OT_register_project(Operator, ImportHelper):
    bl_idname = "bitcake.register_project"
    bl_label = "Register Project"
    bl_description = "Register a new project within blender to work with using BitCake Exporter"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        path = Path(self.filepath)
        cocos = path / 'project.json'
        unreal = path / 'Content'
        unity = path / 'Assets'
        # print("THIS IS THE CURRENT PATH: {}".format(path))

        if cocos.exists():
            project_definition = project_definitions(self.filepath, 'Cocos')
            register_project(project_definition)

        elif unreal.exists():
            project_definition = project_definitions(self.filepath, 'Unreal')
            register_project(project_definition)

        elif unity.exists():
            project_definition = project_definitions(self.filepath, 'Unity')
            register_project(project_definition)
        else:
            self.report({"ERROR"}, "Folder is not a valid Game Project. Please point to a valid Cocos, Unity or Unreal project folder.")
            return {'CANCELLED'}

        return {'FINISHED'}


class BITCAKE_OT_unregister_project(Operator):
    bl_idname = "bitcake.unregister_project"
    bl_label = "Register Project"
    bl_description = "Register a new project within blender to work with using BitCake Exporter"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        self.report({"ERROR"}, "Button Not Implemented.")
        return {'FINISHED'}


def change_active_collection():
    active_collection = bpy.context.active_object.users_collection[0].name
    layer_collections = bpy.context.view_layer.layer_collection.children

    for i in layer_collections:
        if i.name == active_collection:
            bpy.context.view_layer.active_layer_collection = i

def project_definitions(path_string, engine):
    # print("THIS IS THE CURRENT ENGINE: {}".format(engine))
    project_name = path_string.split('\\')
    project = {project_name[-2]: {'engine': engine,'path': path_string,}}
    return project

def register_project(project):
    """Checks if file exist, if not create it and write details as json"""

    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')

    if projects_file_path.is_file():
        projects_json = json.load(projects_file_path.open())
        projects_json.update(project)

        with open(projects_file_path, 'w') as projects_file:
            json.dump(projects_json, projects_file, indent=4)

    else:
        with open(projects_file_path, 'w') as projects_file:
            json.dump(project, projects_file, indent=4)


classes = (BITCAKE_OT_send_to_unity, BITCAKE_OT_register_project, BITCAKE_OT_unregister_project, BITCAKE_OT_custom_butten)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)