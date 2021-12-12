import logging

import bpy
import json
import addon_utils
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from pathlib import Path


class BITCAKE_OT_send_to_engine(Operator):
    bl_idname = "bitcake.send_to_engine"
    bl_label = "Send to Unity"
    bl_description = "Quick Export directly to the correct engine folder."

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props

        # Save current file
        original_path = Path(bpy.data.filepath)
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        # Checks and constructs the path for the exported file
        constructed_path = construct_file_path(self, context)

        # If folder doesn't exist, create it
        constructed_path.parent.mkdir(parents=True, exist_ok=True)

        # Get List of objects according to export type (Selected, Collection, All)
        objects_list = make_objects_list(context)

        # Rename everything in the list
        rename_with_prefix(objects_list)

        # Get current file path, append _bkp and save as new file
        filename = original_path.stem + '_bkp'
        new_path = original_path.with_stem(filename)
        bpy.ops.wm.save_mainfile(filepath=str(new_path))

        # Export file
        bpy.ops.export_scene.fbx(
            filepath=str(constructed_path),
            bake_space_transform=True,
            axis_forward='-Z',
            axis_up='Y',
            use_selection=panel_prefs.export_selected,
            use_active_collection=panel_prefs.export_collection,
        )

        # Save _bkp file and reopen original
        bpy.ops.wm.save_mainfile(filepath=str(new_path))
        bpy.ops.wm.open_mainfile(filepath=str(original_path))

        # Re-hide all colliders for good measure
        toggle_all_colliders_visibility(False)

        return {'FINISHED'}


class BITCAKE_OT_batch_send_to_engine(Operator):
    bl_idname = "bitcake.batch_send_to_engine"
    bl_label = "Batch Send to Engine"
    bl_description = "Exports each object into its own separate FBX alongside any Child objects."

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props
        configs = get_engine_settings()

        # Save current file
        original_path = Path(bpy.data.filepath)
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        objects_list = make_objects_list(context)
        print(f'CURRENT OBJECTS LIST IS: {objects_list}')

        # I just wanted to use generators to see how they worked. Please don't judge.
        for obj in range(len(objects_list)):
            try:
                current_object = next(rename_with_prefix(objects_list, generator=True))
                if current_object.parent != None:
                    continue

                print(f'THIS IS THE CURRENT OBJECT BEING EXPORTED {current_object}')
                # If object is root object, construct its file path
                path = construct_fbx_path(self, context, current_object)

                # If folder doesn't exist, create it
                path.parent.mkdir(parents=True, exist_ok=True)

                # Get all children objects and select ONLY them and the parent, also making it the active obj
                children = get_all_child_of_child(current_object)
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = current_object
                current_object.select_set(True)

                for child in children:
                    child.select_set(True)

                if panel_prefs.origin_transform:
                    bpy.context.object.location = 0, 0, 0

                if panel_prefs.apply_transform:
                    print("AE DOIDERA, APLIQUEI OS TRANSFORM TUDO")
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                bpy.ops.export_scene.fbx(
                    filepath=str(path),
                    bake_space_transform=True,
                    axis_forward=configs['forward_axis'],
                    axis_up=configs['up_axis'],
                    use_selection=True,
                )

            # Ver se isso vai dar problema no futuro (Algum arquivo não vai ser exportado, sei la...)
            except StopIteration:
                print("Generator Iteration Stopped")
                break

        bpy.ops.wm.open_mainfile(filepath=str(original_path))
        bpy.ops.object.select_all(action='DESELECT')
        toggle_all_colliders_visibility(False)

        return {'FINISHED'}


class BITCAKE_OT_toggle_all_colliders_visibility(Operator):
    bl_idname = "bitcake.toggle_all_colliders_visibility"
    bl_label = "Toggles Colliders Visibility"
    bl_description = "Colliders must be prefixed by UBX_, UCX_, USP_, UCP_ or UMX_"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        toggle_all_colliders_visibility()

        return {'FINISHED'}


class BITCAKE_OT_custom_butten(Operator):
    bl_idname = "bitcake.custom_butten"
    bl_label = "Do test stuff"
    bl_description = "Just test stuff"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        get_engine_settings()

        return {'FINISHED'}


class BITCAKE_OT_register_project(Operator, ImportHelper):
    bl_idname = "bitcake.register_project"
    bl_label = "Register Project"
    bl_description = "Registers a new project within BitTools. Itá accepts any Unity, Unreal or Cocos Creator project."

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
        addon_prefs = context.preferences.addons[__package__].preferences
        current_project = addon_prefs.registered_projects

        previous_project = get_previous_project(current_project)
        unregister_project(current_project)
        if previous_project is not None:
            addon_prefs.registered_projects = previous_project

        return {'FINISHED'}


def get_previous_project(current_project):
    registered_projects_file = get_registered_projects_file_path()
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


def get_engine_settings():
    registered_projects_file = get_registered_projects_file_path()
    projects = json.load(registered_projects_file.open())
    engine_configs_file = get_engine_configs_file_path()
    configs = json.load(engine_configs_file.open())

    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    current_project = projects[addon_prefs.registered_projects]
    current_config = configs[current_project['engine']]

    return current_config


def change_active_collection():
    active_collection = bpy.context.active_object.users_collection[0].name
    layer_collections = bpy.context.view_layer.layer_collection.children

    for i in layer_collections:
        if i.name == active_collection:
            bpy.context.view_layer.active_layer_collection = i

    return


def construct_file_path(self, context):
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    for part in blend_path.parts:
        if wip is True:
            split_part = part.split('_')
            pathway.append(split_part[1])
        if part.__contains__('_WIP'):
            pathway.append('Art')
            wip = True

    # Add .blend filename and correct extension to the pathway list
    filename = Path(bpy.data.filepath).stem
    pathway.append(filename + '.fbx')

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment")
        return {'CANCELLED'}

    current_project_path = Path(get_current_project_assets_path(context))
    constructed_path = current_project_path.joinpath(*pathway)

    return constructed_path


def construct_fbx_path(self, context, obj):
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    for part in blend_path.parts:
        if wip is True:
            split_part = part.split('_')
            pathway.append(split_part[1])
        if part.__contains__('_WIP'):
            pathway.append('Art')
            wip = True

    collection_tree = get_object_collection_tree(obj)
    for col in collection_tree:
        nospc = col.name.replace(" ", "")
        pathway.append(nospc)

    # Add parent object as final name, remove whitespaces for good measure
    pathway.append(obj.name.replace(" ", "") + '.fbx')

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment/YourFile.blend")
        return {'CANCELLED'}

    current_project_path = Path(get_current_project_assets_path(context))
    constructed_path = current_project_path.joinpath(*pathway)

    return constructed_path


def get_active_object_collection_tree():
    context = bpy.context
    empty_list = []
    collection_tree = get_current_collection_hierarchy(context.collection, empty_list)
    return collection_tree


def get_object_collection_tree(obj):
    # Check if object is in root collection
    if obj.users_collection[0] == bpy.context.scene.collection:
        return []

    empty_list = []
    collection_tree = get_current_collection_hierarchy(obj.users_collection[0], empty_list)

    return collection_tree


def get_current_collection_hierarchy(active_collection, collection_list=[]):
    context = bpy.context

    if active_collection == context.scene.collection:
        return

    parent = find_parent_collection(active_collection)
    get_current_collection_hierarchy(parent, collection_list)
    collection_list.append(active_collection)

    return collection_list


def find_parent_collection(collection):
    data = bpy.data
    context = bpy.context

    # First get a list of ALL collections in the scene
    collections = [c for c in data.collections if context.scene.user_of_id(c)]
    # Then append the master collection because we need to stop this at some point.
    collections.append(context.scene.collection)

    coll = collection
    collection = [c for c in collections if c.user_of_id(coll)]

    return collection[0]


def get_all_registered_projects():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')
    projects_json = json.load(projects_file_path.open())

    return projects_json


def get_current_project_assets_path(context):
    addonPrefs = context.preferences.addons[__package__].preferences
    active_project = addonPrefs.registered_projects

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')
    projects_json = json.load(projects_file_path.open())

    return projects_json[active_project]['assets']


def get_current_project_path(context):
    addonPrefs = context.preferences.addons[__package__].preferences
    active_project = addonPrefs.registered_projects

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')
    projects_json = json.load(projects_file_path.open())

    return projects_json[active_project]['path']


def get_all_colliders():
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    collider_prefixes = [addon_prefs.box_collider_prefix,
                         addon_prefs.capsule_collider_prefix,
                         addon_prefs.sphere_collider_prefix,
                         addon_prefs.convex_collider_prefix,
                         addon_prefs.mesh_collider_prefix]

    all_objects = bpy.context.scene.objects

    all_colliders_list = []
    for obj in all_objects:
        split = obj.name.split('_')
        if collider_prefixes.__contains__(split[0]):
            all_colliders_list.append(obj)

    return all_colliders_list


def make_objects_list(context):
    panel_prefs = context.scene.menu_props

    if panel_prefs.export_selected:
        selected_objects = bpy.context.selected_objects
        selected_objects = append_child_colliders(selected_objects)
        return selected_objects

    elif panel_prefs.export_collection:
        change_active_collection()
        collection_objects = bpy.context.active_object.users_collection[0].all_objects
        collection_objects = append_child_colliders([obj for obj in collection_objects])
        return collection_objects

    else:
        bpy.ops.object.select_all(action='DESELECT')
        toggle_all_colliders_visibility(True)
        bpy.ops.object.select_all()
        return bpy.context.selected_objects


def append_child_colliders(obj_list):
    for obj in obj_list:
        children = get_all_child_of_child(obj)
        for child in children:
            if get_all_colliders().__contains__(child):
                # If object has collider, unhide it, select it, add it to list
                child.hide_set(False)
                child.hide_viewport = False
                child.select_set(True)
                obj_list.append(child)

    return obj_list


def get_all_child_of_child(obj):
    children = list(obj.children)
    all_children = []

    while len(children):
        child = children.pop()
        all_children.append(child)
        children.extend(child.children)

    return all_children


def project_definitions(engine, dir_path, assets_path):
    project_name = dir_path.stem
    project = {project_name: {'engine': engine, 'path': str(dir_path), 'assets': assets_path, }}

    return project


def register_project(project):
    """Checks if file exist, if not create it and write details as json"""

    projects_file_path = get_registered_projects_file_path()

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

    all_projects = get_all_registered_projects()
    all_projects.pop(project)

    file = get_registered_projects_file_path()

    if not all_projects:
        try:
            file.unlink()
            return
        except FileNotFoundError:
            print("registered_projects.json not found!")
            return

    with open(file, 'w') as projects_file:
        json.dump(all_projects, projects_file, indent=4)


def get_registered_projects_file_path():
    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'registered_projects.json')

    return projects_file_path


def get_engine_configs_file_path():
    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    engine_configs_path = Path(addon_path.parent / 'engine_configs.json')

    return engine_configs_path


def rename_with_prefix(objects_list, generator=False):
    """Renames current obj and all its children. If Generator is true it'll yield the current object being renamed."""

    for obj in objects_list:
        print(f'THIS IS THE CURRENT LIST OF OBJECTS TO RENAME {objects_list}')
        print(f'THIS IS THE CURRENT OBJECT BEING RENAMED {obj}')

        if obj.parent is None:
            all_children = get_all_child_of_child(obj)
            for child in all_children:
                prefix = get_correct_prefix(child)
                child.name = prefix + child.name
        prefix = get_correct_prefix(obj)
        if prefix:
            obj.name = prefix + obj.name

        print(f'THIS IS THE NEW OBJECT NAME {obj.name}')
        if generator:
            yield obj

    return


def get_correct_prefix(obj):
    # Create tuple of Collider Prefixes so Collider's don't get renamed
    addonPrefs = bpy.context.preferences.addons[__package__].preferences
    collider_prefixes = (addonPrefs.box_collider_prefix,
                         addonPrefs.capsule_collider_prefix,
                         addonPrefs.sphere_collider_prefix,
                         addonPrefs.convex_collider_prefix,
                         addonPrefs.mesh_collider_prefix)

    # Get user-defined prefixes
    sm_prefix = addonPrefs.static_mesh_prefix
    sk_prefix = addonPrefs.skeletal_mesh_prefix
    object_prefixes = (sm_prefix, sk_prefix)

    separator = '_'

    split_name = obj.name.split('_')

    # If object is correctly named, ignore it
    if collider_prefixes.__contains__(split_name[0]) or object_prefixes.__contains__(split_name[0]):
        return

    # Return correct prefix for each case
    if obj.find_armature():
        return sk_prefix + separator
    else:
        return sm_prefix + separator


def toggle_all_colliders_visibility(force_on_off=None):
    all_colliders = get_all_colliders()

    is_hidden = force_on_off

    for col in all_colliders:
        if force_on_off is None:
            is_hidden = col.hide_viewport
        col.hide_set(not is_hidden)
        col.hide_viewport = not is_hidden

    return


def zero_transforms(obj_list):
    for obj in obj_list:
        bpy.context.object.location = 0, 0 ,0


classes = (BITCAKE_OT_send_to_engine,
           BITCAKE_OT_batch_send_to_engine,
           BITCAKE_OT_register_project,
           BITCAKE_OT_unregister_project,
           BITCAKE_OT_custom_butten,
           BITCAKE_OT_toggle_all_colliders_visibility)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
