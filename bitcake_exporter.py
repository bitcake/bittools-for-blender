from typing import Collection
import bpy
import json
import addon_utils
from bpy.types           import Operator, Scene
from bpy_extras.io_utils import ImportHelper
from pathlib             import Path


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

        # Save current file
        original_path = Path(bpy.data.filepath)
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        objects_list = make_objects_list(context)

        for obj in range(len(objects_list)):
            try:
                current_object = next(rename_with_prefix(objects_list, generator=True))
                if current_object.parent != None:
                    continue

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

                bpy.ops.export_scene.fbx(
                    filepath=str(path),
                    bake_space_transform=True,
                    axis_forward='-Z',
                    axis_up='Y',
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

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        construct_fbx_path(self, context, bpy.context.active_object)

        return {'FINISHED'}


class BITCAKE_OT_register_project(Operator, ImportHelper):
    bl_idname = "bitcake.register_project"
    bl_label = "Register Project"
    bl_description = "Registers a new project within BitTools. Itá accepts any Unity, Unreal or Cocos Creator project."

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        path = Path(self.filepath)

        if path.suffix != '':
            path = path.parent

        cocos = path / 'project.json'
        unreal = path / 'Content'
        unity = path / 'Assets'
        # print("THIS IS THE CURRENT PATH: {}".format(path))

        if cocos.exists():
            project_definition = project_definitions('Cocos', self.filepath, str(path / 'assets'))
            register_project(project_definition)

        elif unreal.exists():
            project_definition = project_definitions('Unreal', self.filepath, str(path / 'Content'))
            register_project(project_definition)

        elif unity.exists():
            project_definition = project_definitions('Unity', self.filepath, str(path / 'Assets'))
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
        self.report({"ERROR"}, "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment")
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
        pathway.append(col.name)

    # Add parent object as final name
    pathway.append(obj.name + '.fbx')

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"}, "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment/YourFile.blend")
        return {'CANCELLED'}

    current_project_path = Path(get_current_project_assets_path(context))
    constructed_path = current_project_path.joinpath(*pathway)

    return constructed_path

def get_active_object_collection_tree():
    C = bpy.context
    empty_list = []
    collection_tree = get_current_collection_hierarchy(C.collection, empty_list)
    return collection_tree

def get_object_collection_tree(obj):
    # Check if object is in root collection
    if obj.users_collection[0] == bpy.context.scene.collection:
        return []

    empty_list = []
    collection_tree = get_current_collection_hierarchy(obj.users_collection[0], empty_list)

    return collection_tree

def get_current_collection_hierarchy(active_collection, collection_list=[]):
    C = bpy.context

    if active_collection == C.scene.collection:
        return

    parent = find_parent_collection(active_collection)
    get_current_collection_hierarchy(parent, collection_list)
    collection_list.append(active_collection)

    return collection_list

def find_parent_collection(collection):
    D = bpy.data
    C = bpy.context

    # First get a list of ALL collections in the scene
    collections = [c for c in D.collections if C.scene.user_of_id(c)]
    # Then append the master collection because we need to stop this at some point.
    collections.append(C.scene.collection)

    coll = collection
    collection = [c for c in collections if c.user_of_id(coll)]

    return collection[0]

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
    addonPrefs = bpy.context.preferences.addons[__package__].preferences
    collider_prefixes = [addonPrefs.box_collider_prefix,
                         addonPrefs.capsule_collider_prefix,
                         addonPrefs.sphere_collider_prefix,
                         addonPrefs.convex_collider_prefix,
                         addonPrefs.mesh_collider_prefix]

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
        print(children)

    return all_children

def project_definitions(engine, path_string, assets_path):
    # print("THIS IS THE CURRENT ENGINE: {}".format(engine))
    project_name = path_string.split('\\')
    project = {project_name[-2]: {'engine': engine,'path': path_string, 'assets': assets_path,}}

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
    return

def rename_with_prefix(objects_list, generator=False):
    addonPrefs = bpy.context.preferences.addons[__package__].preferences
    # Get needed prefixes
    sm_prefix = addonPrefs.static_mesh_prefix
    sk_prefix = addonPrefs.skeletal_mesh_prefix

    separator = '_'

    # Create list of Collider Prefixes so Collider's don't get renamed
    collider_prefixes = [addonPrefs.box_collider_prefix,
                         addonPrefs.capsule_collider_prefix,
                         addonPrefs.sphere_collider_prefix,
                         addonPrefs.convex_collider_prefix,
                         addonPrefs.mesh_collider_prefix]
    object_prefixes = [sm_prefix, sk_prefix]

    for obj in objects_list:
        split = obj.name.split(separator)

        if collider_prefixes.__contains__(split[0]) or object_prefixes.__contains__(split[0]):
            continue
        if obj.find_armature():
            obj.name = sk_prefix + separator + obj.name
        else:
            obj.name = sm_prefix + separator + obj.name

        if generator:
            yield obj

    return

def toggle_all_colliders_visibility(force_on_off=None):
    all_colliders = get_all_colliders()

    is_hidden = force_on_off

    for col in all_colliders:
        if force_on_off is None:
            is_hidden = col.hide_viewport
        col.hide_set(not is_hidden)
        col.hide_viewport = not is_hidden

    return


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