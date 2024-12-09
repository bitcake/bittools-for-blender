import shutil
import bpy
import os
import json
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty
from pathlib import Path
from ..helpers import get_anim_configs_file_path, get_current_engine, get_object_prefixes, get_published_path, select_and_make_active, get_engine_configs_path, get_current_project_assets_path, get_current_project_structure_json, get_collider_prefixes, select_object_hierarchy, select_object_hierarchy_additive, name_prefix
from ..collider_tools.collider_tools import toggle_all_colliders_visibility, get_all_colliders


class BITCAKE_OT_universal_exporter(Operator):
    bl_idname = "bitcake.universal_exporter"
    bl_label = "Send to Engine"
    bl_description = "Quick Export directly to the correct engine folder."
    bl_options = {'INTERNAL', 'UNDO'}

    is_batch: BoolProperty(name='Batch Export', default=False)
    use_custom_dir: BoolProperty(name='Send to Engine', default=False)
    directory: StringProperty(subtype='DIR_PATH')

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'POSE'

    def invoke(self, context, event):
        panel_prefs = context.scene.exporter_configs
        if self.use_custom_dir and panel_prefs.custom_directory == '':
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        return self.execute(context)

    def execute(self, context):
        panel_prefs = context.scene.exporter_configs
        original_context = context.mode

        # If started from Pose mode, let's put in Object so the Operator works then later on, let's revert it.
        if original_context == 'POSE' and context.object is not None:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # Get List of objects to export according to export type (Selected, Collection, All)
        objects_list = make_objects_list(context)

        # Filter List, removing unwanted objects
        objects_list = filter_object_list(objects_list)

        # Verify if there are actual objects to export...
        if len(objects_list) == 0:
            self.report({'ERROR'}, 'No objects to export. Check if Active Object is part of an Ignored Collection')
            return {'CANCELLED'}

        # If file has never been saved...
        if not bpy.data.is_saved:
            self.report({'ERROR'}, 'This file has never been saved, please save this file in an appropriate WIP folder.')
            return {'CANCELLED'}

        # Setup Export Directory, if any error occur during path setup, stop!
        if panel_prefs.custom_directory == '':
             panel_prefs.custom_directory = self.directory
        if self.use_custom_dir:
            custom_directory = bpy.path.abspath(panel_prefs.custom_directory)
            if os.path.isdir(custom_directory):
                export_directory = Path(custom_directory)
            else:
                self.report({'ERROR'}, 'Chosen Directory does not exist or is invalid!')
                return {'CANCELLED'}
        else:
            export_directory = construct_registered_project_export_directory(self)
            if export_directory == {'CANCELLED'}:
                return export_directory

        original_path = Path(bpy.data.filepath)
        # Get current filename, append _backup and save as new file
        backup_filename = original_path.stem + '_backup'
        backup_path = original_path.with_stem(backup_filename)
        # Create a backup and then Save file before messing around!
        bpy.ops.wm.save_mainfile(filepath=str(backup_path))
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        # Perform Animation Cleanup
        actions_cleanup(context)

        # Active Object can be None, so let's fix that.
        if context.active_object is None:
            context.view_layer.objects.active = context.selected_objects[0]

        # Init dict in case we'll need to revert Original Transforms.
        # It's important that 'active_object' is the first key.
        obj_original_info_dict = {'active_object': context.active_object,}

        for obj in objects_list:
            # Add some base obj information before anything else
            obj_original_info_dict[obj] = {
                'name': obj.name,
                'location': obj.location.copy(),
                'rotation_euler': obj.rotation_euler.copy(),
                'scale': obj.scale.copy(),
            }

        collider_prefixes = get_collider_prefixes()

        for obj in objects_list:
            # First let's clean all the unused materials from this object
            if obj.type != 'EMPTY':
                if obj.material_slots:
                    overriden_context = {'active_object': obj}
                    with bpy.context.temp_override(active_object = overriden_context):
                        print(overriden_context)
                        try:
                            bpy.ops.object.material_slot_remove_unused()
                        except RuntimeError:
                            pass
                else:
                    print(f"obj '{obj.name}' has no material slots")

            # Let's save all object's materials to return them back later
            if obj.type == 'MESH':
                obj_original_info_dict[obj]['materials'] = obj.data.materials.items().copy()

            select_and_make_active(context, obj)

            # Save original name and rename current object according to rules
            rename_with_prefix(self, context, obj, obj_original_info_dict)
            rename_if_lod(obj)

            # Use the collider tags to check if object is a collider, and remove its materials
            if name_prefix(obj.name) in collider_prefixes:
                unlink_materials(obj)

            # Create the json object if object has animation events
            markers_json = construct_animation_configs_json(self, context, obj)

            # Only move root objects to 0,0,0 to avoid errors with Custom Pivots.
            if panel_prefs.origin_transform and obj.parent is None:
                obj.location = 0, 0, 0

            # Deal with linked objects (multi user)
            if obj.data is not None and obj.data.users > 1:
                obj_original_info_dict[obj]['linked_mesh'] = obj.data.original
                bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False, obdata_animation=True)

            if panel_prefs.apply_transform:
                if not [armature for armature in obj.modifiers if armature.type == 'ARMATURE'] and obj.data:
                    selected_child_colliders = []
                    for child in bpy.context.selected_objects:
                        if name_prefix(child.name) in collider_prefixes:
                            selected_child_colliders.append(child)
                            child.select_set(False)

                    original_data_name = obj.data.name
                    original_data = obj.data.copy()
                    obj_original_info_dict[obj]['original_data_name'] = original_data_name
                    obj_original_info_dict[obj]['original_data'] = original_data
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True, properties=True)

                    for child in selected_child_colliders:
                        child.select_set(True)


        # Only Select objects inside the list before exporting
        toggle_all_colliders_visibility(True)

        # Process all types of paths then export accordingly
        if self.is_batch:
            batch_process_objs_paths_and_export(self, context, objects_list, export_directory, markers_json)
        else:
            process_objs_paths_and_export(self, obj_original_info_dict, objects_list, export_directory, markers_json)

        # If only apply transform was selected, end Operation
        if panel_prefs.apply_transform and not panel_prefs.origin_transform:
            # Re-hide all colliders for good measure
            toggle_all_colliders_visibility(False)
            # Save! :D
            bpy.ops.wm.save_mainfile(filepath=str(original_path))

            return {'FINISHED'}

        # Return things to original state
        for index, obj in enumerate(obj_original_info_dict):
            # We skip the first item in the dictionary, which was the current active object.
            if index == 0:
                continue

            saved_props = obj_original_info_dict[obj]

            if 'name' in saved_props:
                obj.name = saved_props['name']
            if 'location' in saved_props:
                obj.location = saved_props['location']
            if 'rotation_euler' in saved_props:
                obj.rotation_euler = saved_props['rotation_euler']
            if 'scale' in saved_props:
                obj.scale = saved_props['scale']

            if 'original_data' in saved_props:
                obj.data.name = obj.data.name + '_exported'
                obj.data = saved_props['original_data']
                obj.data.name = saved_props['original_data_name']

            if 'linked_mesh' in saved_props:
                obj.data.user_remap(saved_props['linked_mesh'])

            if 'materials' in saved_props:
                relink_materials(obj, saved_props['materials'])

        # Deletes all data created in the process that has no users to clean the file
        bpy.ops.outliner.orphans_purge()

        # Re-hide all colliders for good measure
        toggle_all_colliders_visibility(False)

        # Go back to Pose Mode if that's what it was
        if original_context == 'POSE':
            bpy.context.view_layer.objects.active = obj_original_info_dict['active_object']
            bpy.ops.object.mode_set(mode='POSE', toggle=False)

        # Save! :D
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        self.report({'INFO'}, "Export Complete!")

        return {'FINISHED'}


def make_objects_list(context):
    panel_prefs = bpy.context.scene.exporter_configs
    objects_list = []

    if panel_prefs.export_selection_types == 'SELECTED':
        selected_objects = context.selected_objects
        selected_objects = append_child_colliders(selected_objects)
        objects_list = selected_objects

    elif panel_prefs.export_selection_types == 'COLLECTION':
        change_active_collection(context)
        collection_objects = context.active_object.users_collection[0].all_objects
        collection_objects = append_child_colliders([obj for obj in collection_objects])
        objects_list = collection_objects

    else:
        bpy.ops.object.select_all(action='DESELECT')
        toggle_all_colliders_visibility(True)
        bpy.ops.object.select_all()
        objects_list = context.selected_objects

    return objects_list

def append_child_colliders(obj_list):
    all_colliders = get_all_colliders()
    for obj in obj_list:
        for child in obj.children_recursive:
            # If collider is already in the list, ignore it
            if child in obj_list:
                continue

            if child in all_colliders:
                # If object has collider, unhide it, select it, add it to list
                child.hide_set(False)
                child.hide_viewport = False
                child.select_set(True)
                obj_list.append(child)

    return obj_list

def change_active_collection(context=bpy.context):
    active_collection = context.active_object.users_collection[0].name
    layer_collections = context.view_layer.layer_collection.children

    for i in layer_collections:
        if i.name == active_collection:
            context.view_layer.active_layer_collection = i

    return


def filter_object_list(object_list):
    '''Removes all objects that are:
    - Inside an Ignored Collection or are Linked inside one'''

    panel_prefs = bpy.context.scene.exporter_configs
    sm = panel_prefs.static_mesh_export
    sk = panel_prefs.skeletal_mesh_export
    cam = panel_prefs.camera_export

    list_copy = object_list.copy()

    for obj in list_copy:
        for col in obj.users_collection:
            if col.get('Ignore'):
                object_list.remove(obj)
        if sm is False and obj.type == 'MESH':
            object_list.remove(obj)
        if sk is False and obj.type == 'ARMATURE':
            object_list.remove(obj)
        if cam is False and obj.type == 'CAMERA':
            object_list.remove(obj)

    return object_list


def construct_registered_project_export_directory(self):
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    # Get the current project's project_structure.json object to get its folder structure
    structure_json = get_current_project_structure_json()
    if not structure_json:
        self.report({"ERROR"},
                    "No project_structure.json found! Please use BitPipe to create one for your project!")
        return {'CANCELLED'}

    # First, add the parent folder where all assets in the project reside
    pathway.append(structure_json['folderName'])

    # Search the .blend Path for BitCake's folder structure
    # Change _WIP folder to Art then construct the rest of the path
    for part in blend_path.parts:

        if wip is True:
            split_part = part.split('_')
            # If folder name starts with a number, remove it, otherwise join again.
            if split_part[0].isnumeric():
                split_part.pop(0)
                pathway.append('_'.join(split_part))
            else:
                pathway.append('_'.join(split_part))

        if part.__contains__('WIP'):
            pathway.append('Art')
            wip = True

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment")
        return {'CANCELLED'}

    # Construct final directory and return it
    current_project_path = Path(get_current_project_assets_path())
    constructed_directory = current_project_path.joinpath(*pathway) # Unpacks the list as arguments

    return constructed_directory

def rename_object(self, obj, target_name):
    original_name = obj.name
    obj.name = target_name
    if obj.name != target_name:
        self.report({"ERROR"}, f"Failed to rename object '{original_name}' to '{target_name}' for export")


def rename_with_prefix(self, context, obj, obj_original_info_dict):
    """Renames parent obj and all its children."""

    if obj.parent:
        return

    panel_prefs = context.scene.exporter_configs
    separator = panel_prefs.separator

    prefix = get_correct_prefix(context, obj)
    if not object_has_correct_prefix(context, prefix, obj):
        rename_object(self, obj, f"{prefix}{separator}{obj.name}")

    collider_prefixes = get_collider_prefixes()

    collider_index = 0
    for child in obj.children_recursive:
        prefix = get_correct_prefix(context, child)

        if not child in obj_original_info_dict:
            obj_original_info_dict[child] = {'name': child.name}

        prefix_split = prefix.split(separator)

        if prefix_split[0] in collider_prefixes:
            if child.parent in obj_original_info_dict:
                rename_object(self, child, f"{prefix}{separator}{obj_original_info_dict[child.parent]['name']}{separator}{str(collider_index).zfill(2)}")
            else:
                rename_object(self, child, f"{prefix}{separator}{obj_original_info_dict[obj]['name']}{separator}{str(collider_index).zfill(2)}")
            collider_index += 1
        else:
            # Checks if object already has correct prefix in name
            if not object_has_correct_prefix(context, prefix, child):
                rename_object(self, child, f"{prefix}{separator}{child.name}")


def rename_if_lod(obj):
    """Renames obj if it's the LOD0."""

    if obj.get('LOD') == 0:
        obj.name = obj.name + '_LOD0'

    return

def get_correct_prefix(context, obj):
    panel_prefs = context.scene.exporter_configs
    separator = panel_prefs.separator

    # Create list of Collider Prefixes to use so that Colliders don't get renamed
    collider_prefixes = get_collider_prefixes()

    # Get user-defined object prefixes
    object_prefixes = get_object_prefixes()

    # If object is correctly named, return its prefix
    split_name = obj.name.split(separator)
    prefixes = collider_prefixes + object_prefixes
    col_prefix = ['','']
    for prefix in prefixes:
        if split_name[0] == prefix:
            col_prefix[0] = prefix
        if len(split_name) > 1:
            if split_name[1] == prefix:
                col_prefix[1] = prefix
    if col_prefix[0]:
        prefix = col_prefix[0]
        if col_prefix[1]:
            prefix = prefix + separator + col_prefix[1]
        return prefix

    # Return correct prefix for each case
    # Check get_object_prefixes for each index, this is bad, should be a dict instead?
    if obj.type == 'ARMATURE':
        return object_prefixes[1]
    if obj.type == 'CAMERA':
        return object_prefixes[2]
    else:
        return object_prefixes[0]

def object_has_correct_prefix(context, prefix, obj):
    panel_prefs = context.scene.exporter_configs
    separator = panel_prefs.separator

    split_name = obj.name.split(separator)
    if split_name[0] == prefix:
        return True

    return False

def actions_cleanup(context):
    actions = context.blend_data.actions
    for action in actions:
        # If Action doesn't contain any keyframes, delete it
        if action.fcurves.items() == []:
            bpy.data.actions.remove(bpy.data.actions[action.name])
        # Make sure all actions with keyframes Use Fake User so they don't get deleted on export
        elif not action.use_fake_user:
            action.use_fake_user = True

def construct_animation_configs_json(self, context, obj):
    if obj.type != 'ARMATURE':
        return

    if bpy.data.actions.items() == []:
        return

    markers_json = Path(get_anim_configs_file_path())
    markers_json = json.load(markers_json.open())

    fps = context.scene.render.fps
    markers_json['FPS'] = fps
    if fps % 30 != 0:
        self.report({"ERROR"}, "Scene is not currently at 30 or 60FPS! Please FIX and re-export!")

    markers_json['Character'] = obj.name

    markers_json['TimelineMarkers'] = []
    for mrks in context.scene.timeline_markers:
        dictionary = {"Name": mrks.name, "Frame": mrks.frame}
        markers_json['TimelineMarkers'].append(dictionary)

    markers_json['ActionsData'] = []
    for action in bpy.data.actions:
        action_marker = {"Name": action.name,
                         "Markers": [],
                         "StartEndFrames": [],
                         "Speed": None,
                         "Loop": action.use_cyclic}

        for marker in action.pose_markers:
            marker_dict = {"Name": marker.name, "Frame": marker.frame}
            action_marker['Markers'].append(marker_dict)

        if action.use_frame_range:
            action_marker['StartEndFrames'].append(int(action.frame_start))
            action_marker['StartEndFrames'].append(int(action.frame_end))
        else:
            action_marker['StartEndFrames'].append(int(action.curve_frame_range[0]))
            action_marker['StartEndFrames'].append(int(action.curve_frame_range[1]))

        speed = action.get('treadmill_speed')
        if speed:
            action_marker['Speed'] = speed

        markers_json['ActionsData'].append(action_marker)

    return markers_json

def unlink_materials(obj):
    if obj.override_library is not None and obj.type != 'EMPTY':
        obj.data.override_create(remap_local_usages=True)

    try:
        bpy.ops.object.material_slot_remove_unused()

    except RuntimeError:
        pass

    finally:
        for index, material in enumerate(obj.material_slots):
            obj.material_slots[index].material = None

    return

def create_fake_materials(obj):
    for index, material in enumerate(obj.material_slots):
        mat = bpy.data.materials.new(name=f'{obj.name}_{material.name}_{index}')
        obj.material_slots[index].material = mat

def relink_materials(obj, materials):
    if materials == []:
        return

    for index, slot in enumerate(obj.material_slots):
        if slot.material is None:
            slot.material = materials[index][1]

    return

def create_animation_markers_json_file(path, markers_json):
    if markers_json is None:
        return

    path = path.with_stem(path.stem + '_configs')
    path = path.with_suffix('.json')

    with open(path, 'w') as json_file:
        json.dump(markers_json, json_file, indent=4)

    return

def select_objects_in_list(objects_list):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None

    for obj in objects_list:
        obj.select_set(True)

    return

def get_object_collection_hierarchy(context, parent_collection, collection_list=[]):

    if parent_collection == context.scene.collection:
        return []

    parent = find_parent_collection(context, parent_collection)
    get_object_collection_hierarchy(context, parent, collection_list)
    collection_list.append(parent_collection)

    return collection_list


def find_parent_collection(context, collection):
    data = bpy.data

    # First get a list of ALL collections in the scene
    collections = [c for c in data.collections if context.scene.user_of_id(c)]
    # Then append the master collection because we need to stop this at some point.
    collections.append(context.scene.collection)

    coll = collection
    collection = [c for c in collections if c.user_of_id(coll)]

    return collection[0]

def get_collection_hierarchy_list_as_path(context, obj):
    parent_collection = obj.users_collection[0]
    # Initializing an empty list otherwise it wouldn't reset properly
    collection_hierarchy = []
    collection_hierarchy = get_object_collection_hierarchy(context, parent_collection, collection_hierarchy)
    collection_hierarchy = [c.name for c in collection_hierarchy]

    return collection_hierarchy

def exporter(self, path):
    panel_prefs = bpy.context.scene.exporter_configs
    configs = get_engine_configs(panel_prefs)

    export_nla = panel_prefs.export_nla_strips

    # remember what textures each material uses
    node_to_texture = {}
    for material in bpy.data.materials:
        if material and material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    node_to_texture[node] = node.image
                    node.image = None

    # Export file
    try:
        teste = bpy.ops.export_scene.fbx(
            filepath=str(path),
            apply_scale_options=configs['apply_scale'],
            use_space_transform=configs['space_transform'],
            bake_space_transform=False,
            use_mesh_modifiers=True,
            use_armature_deform_only=True,
            use_custom_props=True,
            add_leaf_bones=configs['add_leaf_bones'],
            primary_bone_axis=configs['primary_bone'],
            secondary_bone_axis=configs['secondary_bone'],
            bake_anim=panel_prefs.animation_export,
            bake_anim_use_nla_strips=export_nla,
            bake_anim_step=configs['anim_sampling'],
            bake_anim_simplify_factor=configs['anim_simplify'],
            bake_anim_force_startend_keying=True,
            use_selection=True,
            use_active_collection=False,
            path_mode='COPY',
            embed_textures=False,
            axis_forward=configs['forward_axis'],
            axis_up=configs['up_axis'],
        )
    except err:
        self.report({"ERROR"}, f"error while exporting: '{err}'")

    # restore all materials textures
    for node in node_to_texture:
        texture = node_to_texture[node]
        if texture:
            node.image = texture
        else:
            self.report({"ERROR"}, f"node '{node}' lost reference to its texture")

    return


def process_objs_paths_and_export(self, original_info_dict, objects_list, export_directory, markers_json):
    panel_prefs = bpy.context.scene.exporter_configs

    select_objects_in_list(objects_list)

    for object in objects_list:
        select_object_hierarchy_additive(object)

    # Create the filename based on this .blend name
    filename = panel_prefs.non_batch_filename + '.fbx'
    if filename == '':
        filename = original_info_dict['active_object'].name + '.fbx'
    # Constructs final path
    constructed_path = export_directory.joinpath(filename)
    # If folder doesn't exist, create it
    constructed_path.parent.mkdir(parents=True, exist_ok=True)
    # Pass the Json Dict and dump it to create the actual file in the directory
    create_animation_markers_json_file(constructed_path, markers_json)
    # Finally, export the file
    exporter(self, constructed_path)

    # Copy the created FBX to its published folder
    if not self.use_custom_dir:
        published_dir = get_published_path().parent
        published_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(constructed_path, published_dir)

    return

def obj_ancestor_in_objects_set(objects_set, obj):
    result = False
    obj = obj.parent
    while obj:
        result = obj in objects_set
        if result:
            break
        obj = obj.parent
    return result

def batch_process_objs_paths_and_export(self, context, objects_list, export_directory, markers_json):
    """Process each object in the list, constructs each path, creates Animation Markers Json and Exports Files"""
    panel_prefs = bpy.context.scene.exporter_configs

    objects_set = {}

    for obj in objects_list:
        objects_set[obj] = True

    for obj in objects_list:
        if obj_ancestor_in_objects_set(objects_set, obj):
            continue

        # Selects the object and all its hierachy
        select_object_hierarchy(obj)

        if panel_prefs.collection_to_folder:
            # Gets object Collection Hierarchy as a path in string list format
            collection_hierarchy = get_collection_hierarchy_list_as_path(context, obj)
            # Constructs the export Path without filename
            constructed_path = export_directory.joinpath(*collection_hierarchy)
        else:
            constructed_path = export_directory

        constructed_path = constructed_path.joinpath(obj.name + '.fbx')
        # Create dir if not found
        constructed_path.parent.mkdir(parents=True, exist_ok=True)
        # Pass the Json Dict and dump it to create the actual file in the directory
        create_animation_markers_json_file(constructed_path, markers_json)
        # Finally, export the file
        exporter(self, constructed_path)

        # Copy the created FBX to its published folder
        if not self.use_custom_dir:
            published_dir = get_published_path().parent
            if panel_prefs.collection_to_folder:
                published_dir = published_dir.joinpath(*collection_hierarchy)
            published_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(constructed_path, published_dir)

    return

def construct_dummy_export_directory():
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    # Get the current project's project_structure.json object to get its folder structure
    structure_json = get_current_project_structure_json()
    if structure_json is None:
        return "project_structure.json not found"

    # First, add the parent folder where all assets in the project reside
    pathway.append(structure_json['folderName'])

    # Search the .blend Path for BitCake's folder structure
    # Change _WIP folder to Art then construct the rest of the path
    for part in blend_path.parts:

        if wip is True:
            split_part = part.split('_')
            # If folder name starts with a number, remove it, otherwise join again.
            if split_part[0].isnumeric():
                split_part.pop(0)
                pathway.append('_'.join(split_part))
            else:
                pathway.append('_'.join(split_part))

        if part.__contains__('WIP'):
            pathway.append('Art')
            wip = True

    # Construct final directory and return it
    current_project_path = Path(get_current_project_assets_path())
    constructed_directory = current_project_path.joinpath(*pathway) # Unpacks the list as arguments

    return constructed_directory


def get_engine_configs(panel_prefs):
    engine_configs_file = get_engine_configs_path()
    configs = json.load(engine_configs_file.open())

    current_engine = panel_prefs.engine_configs_list
    current_config = configs[current_engine]

    return current_config


def draw_panel(self, context):
    configs = context.scene.exporter_configs
    pcoll = preview_collections["main"]

    batch = ""
    if configs.export_batch:
        batch = "Batch "

    current_engine = get_current_engine()
    if current_engine is None:
        return

    engine_logo = pcoll[current_engine]

    layout = self.layout
    layout.separator()
    layout.label(text='Export')

    if not configs.export_batch:
        row = layout.row(align=True)
        row.alert = configs.filename_alert
        row.prop(configs, 'non_batch_filename', toggle=1)

    # box = layout.box()
    # box.label(text='Current Export Directory:')
    # directory = construct_dummy_export_directory()
    # box.label(text=f'{directory}')

    row = layout.row()
    op = row.operator('bitcake.universal_exporter', text=f'{batch}Send to {current_engine} Project', icon_value=engine_logo.icon_id)
    op.is_batch = configs.export_batch

    row = layout.row()
    row.separator()
    row = layout.row()
    row.prop(configs, 'custom_directory')

    row = layout.row()
    op = row.operator('bitcake.universal_exporter', text=f'{batch}Send to Custom Directory', icon='EXPORT')
    op.use_custom_dir = True
    op.is_batch = configs.export_batch

classes = (BITCAKE_OT_universal_exporter,)

preview_collections = {}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register Custom Icons
    pcoll = bpy.utils.previews.new()
    bittools_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("Unity", os.path.join(bittools_icons_dir, "unity_logo.png"), 'IMAGE')
    pcoll.load("Unreal", os.path.join(bittools_icons_dir, "unreal_logo.png"), 'IMAGE')
    pcoll.load("Cocos", os.path.join(bittools_icons_dir, "cocos_logo.png"), 'IMAGE')
    preview_collections["main"] = pcoll


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # UnRegister Custom Icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()