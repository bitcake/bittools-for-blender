import bpy
import os
import json
import addon_utils
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty
from pathlib import Path
from ..helpers import get_current_engine, select_and_make_active, get_registered_projects_path, get_engine_configs_path, get_markers_configs_file_path, get_addon_prefs

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
        if self.use_custom_dir:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        panel_prefs = scene.menu_props

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


        original_path = Path(bpy.data.filepath)
        # Get current filename, append _backup and save as new file
        backup_filename = original_path.stem + '_backup'
        new_path = original_path.with_stem(backup_filename)
        # Create a backup and then Save file before messing around!
        bpy.ops.wm.save_mainfile(filepath=str(new_path))
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        # Perform Animation Cleanup
        actions_cleanup(context)

        # Init empty dict in case we'll need to revert Origin Transforms
        obj_location_dict = {}
        for obj in objects_list:
            select_and_make_active(context, obj)

            # Rename current object according to rules
            rename_with_prefix(obj)

            # Create the json object if object has animation events
            markers_json = construct_animation_events_json(self, context, obj)

            if panel_prefs.origin_transform:
                obj_location_dict[obj] = obj.location.copy()
                obj.location = 0, 0, 0


            if panel_prefs.apply_transform:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Only Select objects inside the list before exporting
        toggle_all_colliders_visibility(True)

        if self.use_custom_dir and not self.is_batch:
            select_objects_in_list(objects_list)
            filename = Path(bpy.data.filepath).stem + '.fbx'
            constructed_path = Path(self.directory + filename)
            # If folder doesn't exist, create it
            constructed_path.parent.mkdir(parents=True, exist_ok=True)
            create_animation_markers_json_file(constructed_path, markers_json)
            exporter(constructed_path, panel_prefs)

        elif self.use_custom_dir and self.is_batch:
            for obj in objects_list:
                select_and_make_active(context, obj)
                collection_hierarchy = get_collection_hierarchy_list_as_path(context, obj)
                constructed_path = Path(self.directory).joinpath(*collection_hierarchy)
                # If folder doesn't exist, create it
                constructed_path.parent.mkdir(parents=True, exist_ok=True)
                create_animation_markers_json_file(constructed_path, markers_json)
                exporter(constructed_path, panel_prefs)

        elif self.is_batch:
            pass
        else:
            pass

        if panel_prefs.origin_transform:
            for obj in obj_location_dict:
                print(f'AQUI É {obj} CUJO VETOR DE LOCATION É {obj_location_dict[obj]}')
                obj.location = obj_location_dict[obj]


        # Re-hide all colliders for good measure
        toggle_all_colliders_visibility(False)

        return {'FINISHED'}
        # # Checks and constructs the path for the exported file
        # if self.use_custom_dir:
        # else:
        #     constructed_path = construct_export_directory(self, context)




        # # Builds the parameters and exports scene
        # exporter(constructed_path, panel_prefs)

        # # Save _bkp file and reopen original
        # bpy.ops.wm.save_mainfile(filepath=str(new_path))
        # bpy.ops.wm.open_mainfile(filepath=str(original_path))

        # # Deselect everything because Blender 3.0 now saves selection
        # bpy.ops.object.select_all(action='DESELECT')




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

def toggle_all_colliders_visibility(force_on_off=None):
    all_colliders = get_all_colliders()

    is_hidden = force_on_off

    for col in all_colliders:
        if force_on_off is None:
            is_hidden = col.hide_viewport
        col.hide_set(not is_hidden)
        col.hide_viewport = not is_hidden

    return

def filter_object_list(object_list):
    '''Removes all objects that are inside an Ignored Collection or are Linked inside one'''

    list_copy = object_list.copy()

    for obj in list_copy:
        for col in obj.users_collection:
            if col.get('Ignore'):
                object_list.remove(obj)

    return object_list

def get_all_child_of_child(obj):
    children = list(obj.children)
    all_children = []

    while len(children):
        child = children.pop()
        all_children.append(child)
        children.extend(child.children)

    return all_children

def get_collider_prefixes():
    addon_prefs = get_addon_prefs()
    collider_prefixes = [addon_prefs.box_collider_prefix,
                         addon_prefs.capsule_collider_prefix,
                         addon_prefs.sphere_collider_prefix,
                         addon_prefs.convex_collider_prefix,
                         addon_prefs.mesh_collider_prefix]

    return collider_prefixes


def get_all_colliders():
    collider_prefixes = get_collider_prefixes()

    all_objects = bpy.context.scene.objects

    all_colliders_list = []
    for obj in all_objects:
        split = obj.name.split('_')
        if collider_prefixes.__contains__(split[0]):
            all_colliders_list.append(obj)

    return all_colliders_list


# TODO: CHANGE THIS ACCORDING TO TALK WITH DANI
def construct_export_directory(self, context, custom_directory, using_custom=False, ):
    blend_path = Path(bpy.path.abspath('//'))
    wip = False
    pathway = []

    for part in blend_path.parts:
        if wip is True:
            split_part = part.split('_')
            pathway.append(split_part[-1])
        if part.__contains__('_WIP'):
            pathway.append('Art')
            wip = True

    # Add .blend filename and correct extension to the pathway list (if filename is dani.blend then export will be dani.fbx)
    filename = Path(bpy.data.filepath).stem
    pathway.append(filename + '.fbx')

    # If no WIP folder found then fail
    if wip is False:
        self.report({"ERROR"},
                    "The .blend path is not contained inside a proper BitCake Pipeline hierarchy, please make sure your hierarchy's root folder contains the word '_WIP' like in c:/BitTools/02_WIP/Environment")
        return {'CANCELLED'}

def rename_with_prefix(obj):
    """Renames current obj and all its children."""

    if obj.parent is None:
        all_children = get_all_child_of_child(obj)

        for child in all_children:
            prefix = get_correct_prefix(child)
            # Checks if object already has correct prefix in name
            if not check_object_name_for_prefix(prefix, child):
                child.name = prefix + child.name

    prefix = get_correct_prefix(obj)
    # Checks if object already has correct prefix in name
    if not check_object_name_for_prefix(prefix, obj):
        obj.name = prefix + obj.name

def get_correct_prefix(obj):
    # Create list of Collider Prefixes to use so that Colliders don't get renamed
    collider_prefixes = get_collider_prefixes()

    # Get user-defined prefixes
    addon_prefs = get_addon_prefs()
    separator = addon_prefs.separator
    sm_prefix = addon_prefs.static_mesh_prefix
    sk_prefix = addon_prefs.skeletal_mesh_prefix

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

def check_object_name_for_prefix(prefix, obj):
    addon_prefs = get_addon_prefs()
    separator = addon_prefs.separator

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

def create_animation_markers_json_file(path, markers_json):
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
        return None

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
    collection_hierarchy.append(obj.name + '.fbx')

    return collection_hierarchy

def exporter(path, panel_preferences):
    configs = get_engine_configs()

    export_nla = panel_preferences.export_nla_strips

    # Export file
    bpy.ops.export_scene.fbx(
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
        axis_forward=configs['forward_axis'],
        axis_up=configs['up_axis'],
    )

    return

def get_engine_configs():
    registered_projects_file = get_registered_projects_path()
    projects = json.load(registered_projects_file.open())
    engine_configs_file = get_engine_configs_path()
    configs = json.load(engine_configs_file.open())

    addon_prefs = get_addon_prefs()
    current_project = projects[addon_prefs.registered_projects]
    current_config = configs[current_project['engine']]

    return current_config


def draw_panel(self, context):
    pcoll = preview_collections["main"]
    current_engine = get_current_engine(context)
    engine_logo = pcoll[current_engine]


    layout = self.layout
    row = layout.row()
    op = row.operator('bitcake.universal_exporter', text=f'Send to {current_engine} Project', icon_value=engine_logo.icon_id)
    op.use_custom_dir = True
    op.is_batch = True

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