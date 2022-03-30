import shutil
import bpy
import os
import json
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty
from pathlib import Path
from ..helpers import get_current_engine, select_and_make_active, get_engine_configs_path, get_markers_configs_file_path, get_addon_prefs, get_current_project_assets_path, get_current_project_structure_json, get_all_child_of_child, get_collider_prefixes, select_object_hierarchy
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
        return context.mode == 'OBJECT'

    def invoke(self, context, event):
        panel_prefs = context.scene.exporter_configs
        if self.use_custom_dir and panel_prefs.custom_directory == '':
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        return self.execute(context)

    def execute(self, context):
        panel_prefs = context.scene.exporter_configs

        # Get List of objects to export according to export type (Selected, Collection, All)
        objects_list = make_objects_list(context, panel_prefs)

        # Verify if there are actual objects to export...
        if len(objects_list) == 0:
            self.report({'ERROR'}, 'No objects to export. Check if Active Object is part of an Ignored Collection')
            return {'CANCELLED'}

        # If file has never been saved...
        if bpy.data.filepath == '':
            self.report({'ERROR'}, 'Please Save the file once before running the export.')
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

        # Init empty dict in case we'll need to revert Origin Transforms
        obj_original_info_dict = {'active_object': context.active_object,}
        for obj in objects_list:
            # Create dict entry so we can revert things later
            obj_original_info_dict[obj] = {'name': obj.name,
                                           'location': obj.location.copy(),
                                           'materials': obj.data.materials.items().copy(),
                                           }

            select_and_make_active(context, obj)

            # Save original name and rename current object according to rules
            rename_with_prefix(context, obj)

            # Create the json object if object has animation events
            markers_json = construct_animation_events_json(self, context, obj)

            if panel_prefs.origin_transform:
                obj.location = 0, 0, 0

            if not panel_prefs.export_textures:
                unlink_materials(obj)

            if panel_prefs.apply_transform:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Only Select objects inside the list before exporting
        toggle_all_colliders_visibility(True)

        # Process all types of paths then export accordingly
        if self.use_custom_dir and not self.is_batch:
            process_objs_paths_and_export(self, obj_original_info_dict, objects_list, export_directory, markers_json, panel_prefs)

        elif self.use_custom_dir and self.is_batch:
            batch_process_objs_paths_and_export(self, context, objects_list, export_directory, markers_json, panel_prefs)

        elif not self.use_custom_dir and self.is_batch:
            batch_process_objs_paths_and_export(self, context, objects_list, export_directory, markers_json, panel_prefs)
        else:
            process_objs_paths_and_export(self, obj_original_info_dict, objects_list, export_directory, markers_json, panel_prefs)

        # If only apply transform was selected, end Operation
        if panel_prefs.apply_transform and not panel_prefs.origin_transform:
            # Re-hide all colliders for good measure
            toggle_all_colliders_visibility(False)
            # Save! :D
            bpy.ops.wm.save_mainfile(filepath=str(original_path))

            return {'FINISHED'}

        # Return things to original state
        for index, obj in enumerate(obj_original_info_dict):
            # We skip the first item in the dictionary, which is the current active object.
            if index == 0:
                continue

            obj.name = obj_original_info_dict[obj]['name']
            obj.location = obj_original_info_dict[obj]['location']
            relink_materials(obj, obj_original_info_dict[obj]['materials'])

        # Re-hide all colliders for good measure
        toggle_all_colliders_visibility(False)

        # Save! :D
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        return {'FINISHED'}


def make_objects_list(context, panel_prefs):

    objects_list = []
    if panel_prefs.export_selected:
        selected_objects = context.selected_objects
        selected_objects = append_child_colliders(selected_objects)
        objects_list = selected_objects

    elif panel_prefs.export_collection:
        change_active_collection(context)
        collection_objects = context.active_object.users_collection[0].all_objects
        collection_objects = append_child_colliders([obj for obj in collection_objects])
        objects_list = collection_objects

    else:
        bpy.ops.object.select_all(action='DESELECT')
        toggle_all_colliders_visibility(True)
        bpy.ops.object.select_all()
        objects_list = context.selected_objects

    return filter_object_list(objects_list)

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

def change_active_collection(context=bpy.context):
    active_collection = context.active_object.users_collection[0].name
    layer_collections = context.view_layer.layer_collection.children

    for i in layer_collections:
        if i.name == active_collection:
            context.view_layer.active_layer_collection = i

    return


def filter_object_list(object_list):
    '''Removes all objects that are inside an Ignored Collection or are Linked inside one'''

    list_copy = object_list.copy()

    for obj in list_copy:
        for col in obj.users_collection:
            if col.get('Ignore'):
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
            pathway.append(split_part[-1])
        if part.__contains__('_WIP'):
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

def construct_registered_project_published_export_directory(self):
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    # Search the .blend Path for BitCake's folder structure
    # Change _WIP folder to Art then construct the rest of the path
    for part in blend_path.parts:
        pathway.append(part)
        if part.__contains__('02_WIP'):
            wip = True
            pathway.pop()
            pathway.append('03_Published')

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment")
        return {'CANCELLED'}

    # Construct final directory and return it
    constructed_directory = Path().joinpath(*pathway) # Unpacks the list as arguments

    return constructed_directory

def rename_with_prefix(context, obj):
    """Renames current obj and all its children."""

    if obj.parent is None:
        all_children = get_all_child_of_child(obj)

        for child in all_children:
            prefix = get_correct_prefix(context, child)
            # Checks if object already has correct prefix in name
            if not check_object_name_for_prefix(context, prefix, child):
                child.name = prefix + child.name

    prefix = get_correct_prefix(context, obj)
    # Checks if object already has correct prefix in name
    if not check_object_name_for_prefix(context, prefix, obj):
        obj.name = prefix + obj.name

def get_correct_prefix(context, obj):
    # Create list of Collider Prefixes to use so that Colliders don't get renamed
    collider_prefixes = get_collider_prefixes()

    # Get user-defined prefixes
    panel_prefs = context.scene.exporter_configs
    separator = panel_prefs.separator
    sm_prefix = panel_prefs.static_mesh_prefix
    sk_prefix = panel_prefs.skeletal_mesh_prefix

    # If object is correctly named, return its prefix
    split_name = obj.name.split(separator)
    prefixes = collider_prefixes + [sm_prefix, sk_prefix]
    for prefix in prefixes:
        if split_name[0] == prefix:
            return prefix

    # Return correct prefix for each case
    if obj.type == 'ARMATURE':
        return sk_prefix + separator
    else:
        return sm_prefix + separator

def check_object_name_for_prefix(context, prefix, obj):
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

def construct_animation_events_json(self, context, obj):
    if obj.type != 'ARMATURE':
        return

    # Verify if file has markers, if not, don't build .json
    has_markers = False
    for action in bpy.data.actions:
        for marker in action.pose_markers:
            has_markers = True

    for mrks in context.scene.timeline_markers:
        has_markers = True

    if not has_markers:
        return

    markers_json = Path(get_markers_configs_file_path())
    markers_json = json.load(markers_json.open())

    fps = context.scene.render.fps
    markers_json['FPS'] = fps
    if fps % 30 != 0:
        self.report({"ERROR"}, "Scene is not currently at 30 or 60FPS! Please FIX!")

    markers_json['Character'] = obj.name

    markers_json['TimelineMarkers'] = []
    for mrks in context.scene.timeline_markers:
        dictionary = {"Name": mrks.name, "Frame": mrks.frame}
        markers_json['TimelineMarkers'].append(dictionary)

    markers_json['ActionsMarkers'] = []
    for action in bpy.data.actions:
        action_marker = {"Name": action.name, "Markers": []}
        for marker in action.pose_markers:
            marker_dict = {"Name": marker.name, "Frame": marker.frame}
            action_marker['Markers'].append(marker_dict)
        markers_json['ActionsMarkers'].append(action_marker)

    return markers_json

def unlink_materials(obj):
    for index, material in enumerate(obj.material_slots):
        obj.material_slots[index].material = None

    return

def relink_materials(obj, materials):
    if materials == []:
        return

    for index, slot in enumerate(obj.material_slots):
        slot.material = materials[index][1]

    return

def create_animation_markers_json_file(path, markers_json):
    if markers_json is None:
        return

    path = path.with_stem(path.stem + '_events')
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

def exporter(path, panel_preferences):
    configs = get_engine_configs(panel_preferences)

    export_nla = panel_preferences.export_nla_strips

    # Export file
    teste = bpy.ops.export_scene.fbx(
        filepath=str(path),
        apply_scale_options=configs['apply_scale'],
        use_space_transform=configs['space_transform'],
        bake_space_transform=False,
        use_armature_deform_only=True,
        use_custom_props=True,
        add_leaf_bones=configs['add_leaf_bones'],
        primary_bone_axis=configs['primary_bone'],
        secondary_bone_axis=configs['secondary_bone'],
        bake_anim_use_nla_strips=export_nla,
        bake_anim_step=configs['anim_sampling'],
        bake_anim_simplify_factor=configs['anim_simplify'],
        use_selection=True,
        use_active_collection=False,
        path_mode='COPY',
        embed_textures=False,
        axis_forward=configs['forward_axis'],
        axis_up=configs['up_axis'],
    )

    return


def process_objs_paths_and_export(self, original_info_dict, objects_list, export_directory, markers_json, panel_prefs):
    select_objects_in_list(objects_list)
    # Create the filename based on this .blend name
    print(f'O OBJETO ATIVO ORIGINAL ERA: {original_info_dict}')
    filename = original_info_dict['active_object'].name + '.fbx'
    # Constructs final path
    constructed_path = export_directory.joinpath(filename)
    # If folder doesn't exist, create it
    constructed_path.parent.mkdir(parents=True, exist_ok=True)
    # Pass the Json Dict and dump it to create the actual file in the directory
    create_animation_markers_json_file(constructed_path, markers_json)
    # Finally, export the file
    exporter(constructed_path, panel_prefs)

    # Copy the created FBX to its published folder
    if not self.use_custom_dir:
        published_dir = construct_registered_project_published_export_directory(self)
        published_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(constructed_path, published_dir)

    return

def batch_process_objs_paths_and_export(self, context, objects_list, export_directory, markers_json, panel_prefs):
    """Process each object in the list, constructs each path, creates Animation Markers Json and Exports Files"""
    for obj in objects_list:
        if obj.parent is not None:
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
        exporter(constructed_path, panel_prefs)

        # Copy the created FBX to its published folder
        if not self.use_custom_dir:
            published_dir = construct_registered_project_published_export_directory(self)
            if panel_prefs.collection_to_folder:
                published_dir = published_dir.joinpath(*collection_hierarchy)
            published_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(constructed_path, published_dir)

    return


def get_engine_configs(panel_preferences):
    engine_configs_file = get_engine_configs_path()
    configs = json.load(engine_configs_file.open())

    current_engine = panel_preferences.engine_configs_list
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