import bpy
import json
from pathlib import Path
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from ..helpers import get_registered_projects_path, get_addon_prefs, get_current_engine


class BITCAKE_OT_register_project(Operator, ImportHelper):
    bl_idname = "bitcake.register_project"
    bl_label = "Register Project"
    bl_description = "Registers a new project within BitTools. It accepts any Unity, Unreal or Cocos Creator project."

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        dir_path = Path(self.filepath)
        if dir_path.is_file() or dir_path.suffix != '':
            dir_path = dir_path.parent

        cocos = dir_path / 'project.json'
        unreal = dir_path / 'Content'
        unity = dir_path / 'Assets'

        if cocos.exists():
            project_definition = project_definitions('Cocos', dir_path, str(dir_path / 'assets'))
            register_project(project_definition)

        elif unreal.exists():
            project_definition = project_definitions('Unreal', dir_path, str(dir_path / 'Content'))
            register_project(project_definition)

        elif unity.exists():
            project_definition = project_definitions('Unity', dir_path, str(dir_path / 'Assets'))
            register_project(project_definition)
        else:
            self.report({"ERROR"},
                        "Folder is not a valid Game Project. Please point to a valid Cocos, Unity or Unreal project folder.")
            return {'CANCELLED'}

        return {'FINISHED'}


class BITCAKE_OT_unregister_project(Operator):
    bl_idname = "bitcake.unregister_project"
    bl_label = "Unregister Project"
    bl_description = "Deletes current project from the Projects list"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        addon_prefs = get_addon_prefs()
        current_project = addon_prefs.registered_projects

        previous_project = get_previous_project(current_project)
        unregister_project(current_project)
        if previous_project is not None:
            addon_prefs.registered_projects = previous_project

        return {'FINISHED'}

def project_definitions(engine, dir_path, assets_path):
    project_name = dir_path.stem
    project = {project_name: {'engine': engine, 'path': str(dir_path), 'assets': assets_path, }}

    return project

def register_project(project):
    """Checks if file exist, if not create it and write details as json"""

    projects_file_path = get_registered_projects_path()

    if projects_file_path.is_file():
        projects_json = json.load(projects_file_path.open())
        projects_json.update(project)

        with open(projects_file_path, 'w') as projects_file:
            json.dump(projects_json, projects_file, indent=4)

    else:
        with open(projects_file_path, 'w') as projects_file:
            json.dump(project, projects_file, indent=4)
    return

def unregister_project(project):
    """Pass a Project string in order to delete it from registered_projects.json"""

    all_projects = Path(get_registered_projects_path())
    all_projects = json.load(all_projects.open())
    all_projects.pop(project)

    file = get_registered_projects_path()

    if not all_projects:
        try:
            file.unlink()
            return
        except FileNotFoundError:
            print("registered_projects.json not found!")
            return

    with open(file, 'w') as projects_file:
        json.dump(all_projects, projects_file, indent=4)

    return

def get_previous_project(current_project):
    registered_projects_file = get_registered_projects_path()
    projects = json.load(registered_projects_file.open())
    projects_list = []
    for project in projects:
        projects_list.append(project)

    previous_project = ''
    for i, project in enumerate(projects_list):
        if project == current_project:
            # Hack so that if current_project is the first index, give me the next instead of previous
            if i == 0:
                i = 2
            try:
                previous_project = projects_list[i - 1]
            except IndexError:
                return None

    return previous_project


def draw_panel(self, context):
    addon_prefs = get_addon_prefs()
    current_engine = get_current_engine()

    layout = self.layout
    row = layout.row()
    row.label(text="Project Configs")
    row = layout.row()
    row.prop(addon_prefs, 'registered_projects')
    row.operator('bitcake.register_project', icon='ADD', text='')

    # If there's no Project Registered, don't draw the rest of the menu below
    if not current_engine:
        return

    row.operator('bitcake.unregister_project', icon='REMOVE', text='')



classes = (BITCAKE_OT_register_project, BITCAKE_OT_unregister_project)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)