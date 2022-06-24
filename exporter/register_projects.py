from ntpath import join
import os
import bpy
import json
from pathlib import Path
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from ..exporter.exporter_configs import check_project_for_settings
from ..helpers import get_current_project_assets_path, get_exporter_configs, get_generic_project_structure_json, get_registered_projects_path


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

        check_project_for_settings(self, context)

        return {'FINISHED'}


class BITCAKE_OT_create_project_structure_from_main_folder(Operator, ImportHelper):
    bl_idname = "bitcake.create_project_structure_from_main_folder"
    bl_label = "Project Structure from Folder"
    bl_description = "Creates a projects_settings.json with the correct folder paths in it.\
    Please select the Internal folder inside the /Content/ or /Assets/ folder where your FBXs will live in (usually a folder named _Internal)"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        exporter_configs = get_exporter_configs()

        dir_path = Path(self.filepath)
        if dir_path.is_file() or dir_path.suffix != '':
            dir_path = dir_path.parent

        current_asset = Path(get_current_project_assets_path())
        is_relative = dir_path.is_relative_to(current_asset)

        if not is_relative or dir_path == current_asset:
            self.report({'ERROR'}, message=f"This folder must be inside the current Project's /{current_asset.parts[-1]}/ folder and CANNOT be the /{current_asset.parts[-1]}/ itself!")
            return {'CANCELLED'}

        structure_json = get_generic_project_structure_json()
        structure_json['folderName'] = str(dir_path.relative_to(current_asset))
        created_json_path = current_asset / 'project_structure.json'

        with open(created_json_path, 'w') as json_dump:
            json.dump(structure_json, json_dump, indent=4)

        exporter_configs.project_has_settings = True

        return {'FINISHED'}


class BITCAKE_OT_create_project_structure(Operator):
    bl_idname = "bitcake.create_project_structure"
    bl_label = "I AGREE THIS WILL CREATE EMPTY FOLDERS INSIDE MY PROJECT!"
    bl_description = f"**WARNING** Creates an entire Folder Structure inside your Project's /Assets/ or /Content/ folder! \
    This Folder Structure follows BitCake's folder structure convention"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        exporter_configs = get_exporter_configs()

        current_asset = Path(get_current_project_assets_path())

        structure_json = get_generic_project_structure_json()

        build_folder_paths(structure_json, current_asset)

        exporter_configs.project_has_settings = True

        return {'FINISHED'}


class BITCAKE_OT_unregister_project(Operator):
    bl_idname = "bitcake.unregister_project"
    bl_label = "Unregister Project"
    bl_description = "Deletes current project from the Projects list"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        exporter_configs = context.scene.exporter_configs
        current_project = exporter_configs.registered_projects

        previous_project = get_previous_project(current_project)
        unregister_project(current_project)
        if previous_project is not None:
            exporter_configs.registered_projects = previous_project

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

def build_folder_paths(project_structure, folder_path):
    joined_path = folder_path.joinpath(project_structure['folderName'])
    os.makedirs(joined_path)

    for child_folder in project_structure['childFolders']:
        build_folder_paths(child_folder, joined_path)


def draw_panel(self, context):
    exporter_configs = get_exporter_configs()

    layout = self.layout
    row = layout.row()
    row.label(text="Project Configs")
    row = layout.row()
    row.prop(exporter_configs, 'registered_projects')
    row.operator('bitcake.register_project', icon='ADD', text='')

    if not exporter_configs.registered_projects == 'NONE':
        row.operator('bitcake.unregister_project', icon='REMOVE', text='')

    row = layout.row()
    row.prop(exporter_configs, 'engine_configs_list')

    if exporter_configs.project_has_settings == False:
        box = layout.box()
        box.alert = True
        box.label(text=f"No {exporter_configs.engine_configs_list} Engine project_structure.json found!", icon='ERROR')
        row = box.row()
        row.scale_y = 1.2
        row.operator('bitcake.create_project_structure_from_main_folder', text='Select Internal Folder' ,icon='RESTRICT_SELECT_ON')
        row.operator('bitcake.create_project_structure', text='Create Folder Structure', icon='OUTLINER')

classes = (BITCAKE_OT_register_project,
           BITCAKE_OT_create_project_structure_from_main_folder,
           BITCAKE_OT_create_project_structure,
           BITCAKE_OT_unregister_project)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)