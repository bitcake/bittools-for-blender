import imp
import addon_utils
import json
import bpy
import os

from pathlib import Path
from mathutils import Vector, Quaternion, Euler
from . import bl_info

# Some of those helpers are from the GRET Plugin, check it out.

# Collected keys with `sorted(set(chain.from_iterable(pb.keys() for pb in C.object.pose.bones)))`
arp_default_pose_values = {
    'auto_eyelid': 0.1,
    'auto_stretch': 0.0,
    'autolips': None,  # Different values
    'bend_all': 0.0,
    'elbow_pin': 0.0,
    'eye_target': 1.0,
    'fingers_grasp': 0.0,
    'fix_roll': 0.0,
    'head_free': 0,
    'ik_fk_switch': 0.0,
    'leg_pin': 0.0,
    'lips_retain': 0.0,
    'lips_stretch': 1.0,
    'pole_parent': 1,
    'stretch_length': 1.0,
    'stretch_mode': 1,  # Bone original
    'volume_variation': 0.0,
    'y_scale': 2,  # Bone original
}
default_pose_values = {}

def panel_category_name():
    name = bl_info["name"]
    version = bl_info["version"]
    v_maj = version[0]
    v_min = version[1]
    v_pch = version[2]
    return f'{name} {v_maj}.{v_min}.{v_pch}'

def is_wip_in_path():
    """Receives a Path object and checks if there's a WIP folder in one of the parent folders"""
    filepath = Path(bpy.data.filepath)
    addon_prefs = get_addon_prefs()
    parts = filepath.parts

    for part in parts:
        split_parts = part.split(addon_prefs.separator)
        for split_part in split_parts:
            if split_part == addon_prefs.wip:
                return True

    return False

def get_published_path():
    if not is_wip_in_path():
        return None

    addon_prefs = get_addon_prefs()
    filepath = Path(bpy.data.filepath)
    parts = filepath.parts

    # How many folders in Path until WIP folder?
    walk = 0
    for part in parts:
        wip = False
        split_parts = part.split(addon_prefs.separator)
        for split_part in split_parts:
            if split_part == addon_prefs.wip:
                wip = True
        if wip == True:
            walk += 1
            break

        walk += 1

    # Now we do the reverse so we can Path walk until the WIP's parent
    folders_to_walk = len(parts) - walk

    project_root = filepath.parents[folders_to_walk]
    relative_parents = parts[-folders_to_walk:]

    published = get_published_folder_name_inside_a_dir(project_root)
    published_path = project_root.joinpath(published).joinpath(*relative_parents)

    return published_path

def get_published_folder_name_inside_a_dir(directory):
    """Finds wether or not a Published folder exists inside a directory and returns it. In case none found, creates a mirror Path inside the Published folder returns it."""
    addon_prefs = get_addon_prefs()
    sep = addon_prefs.separator
    pub = addon_prefs.published
    wip = addon_prefs.wip
    root, dirs, files = next(os.walk(directory))

    wip_folder = None
    published_folder = None
    for folder in dirs:
        split_parts = folder.split(sep)

        for part in split_parts:
            if part == pub:
                published_folder = folder
            if part == wip:
                wip_folder = folder

    if published_folder:
        return published_folder

    else:
        split_wip = wip_folder.split(sep)
        if split_wip[0].isnumeric():
            zsize = len(split_wip[0])
            num = int(split_wip[0]) + 1
            split_wip.pop(0)
            split_wip.insert(0, str(num).zfill(zsize))
            split_wip[1] = pub
            published_folder = sep.join(split_wip)

            return published_folder

        else:
            return pub


def is_inside_published(directory):
    """Finds wether or not a Published folder exists inside a Path and returns True. In case none found returns false."""
    addon_prefs = get_addon_prefs()
    sep = addon_prefs.separator
    pub = addon_prefs.published
    dirs = directory.parts

    for folder in dirs:
        split_parts = folder.split(sep)

        for part in split_parts:
            if part == pub:
                return True

    return False


def is_collider(obj):
    collider_prefixes = get_collider_prefixes()
    obj_prefix = obj.name.split("_")
    if obj_prefix[0] in collider_prefixes:
        return True

    return False


def is_object_arp(obj):
    """Returns whether the object is an Auto-Rig Pro armature."""
    return obj and obj.type == 'ARMATURE' and "c_pos" in obj.data.bones

def clear_pose(obj, clear_armature_properties=True, clear_bone_properties=True):
    """Resets the given armature."""

    if not obj or obj.type != 'ARMATURE':
        return

    if clear_armature_properties:
        for prop_name, prop_value in obj.items():
            if isinstance(prop_value, float):
                obj[prop_name] = 0.0

    is_arp = is_object_arp(obj)
    for pose_bone in obj.pose.bones:
        if clear_bone_properties:
            for prop_name, prop_value in pose_bone.items():
                if is_arp and prop_name in arp_default_pose_values:
                    value = arp_default_pose_values[prop_name]
                    if value is not None:
                        pose_bone[prop_name] = value
                elif prop_name in default_pose_values:
                    value = default_pose_values[prop_name]
                    if value is not None:
                        pose_bone[prop_name] = value
                elif prop_name.startswith("_"):
                    continue
                else:
                    try:
                        pose_bone[prop_name] = type(prop_value)()
                    except TypeError:
                        pass
        pose_bone.location = Vector()
        pose_bone.rotation_quaternion = Quaternion()
        pose_bone.rotation_euler = Euler()
        pose_bone.rotation_axis_angle = [0.0, 0.0, 1.0, 0.0]
        pose_bone.scale = Vector((1.0, 1.0, 1.0))


def get_current_project_assets_path():
    """Returns a String Path for the current project Asset folder"""

    active_project = get_exporter_configs().registered_projects

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'configs' / 'registered_projects.json')
    projects_json = json.load(projects_file_path.open())

    return projects_json[active_project]['assets']

def get_generic_project_structure_json_path():
    """Returns the Path to the json Object of the BitTools generic project_structure.json"""
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    project_structure_json_path = Path(addon_path.parent / 'configs' / 'project_structure.json')

    return project_structure_json_path

def get_generic_project_structure_json():
    """Returns a json Object from the BitTools generic project_structure.json file"""
    project_structure_json_path = get_generic_project_structure_json_path()
    project_structure_json = json.load(project_structure_json_path.open())

    return project_structure_json

def get_current_project_structure_json():
    """Returns the project_structure.json file created by BitPipe as a json Object. Returns None if file not found."""
    try:
        asset_path = Path(get_current_project_assets_path())
        json_path = asset_path.joinpath('project_structure.json')

        json_file = json.load(json_path.open())
    except FileNotFoundError:
        return None

    return json_file

def get_registered_projects_path():
    addon_path = None
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'configs' / 'registered_projects.json')

    return projects_file_path

def get_engine_configs_path():
    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    engine_configs_path = Path(addon_path.parent / 'configs' / 'engine_configs.json')

    return engine_configs_path

def get_anim_configs_file_path():
    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    engine_configs_path = Path(addon_path.parent / 'configs' / 'anim_configs.json')

    return engine_configs_path


def select_and_make_active(context, obj):
    # Deselects everything then selects obj and make it active
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[obj.name].select_set(True)
    context.view_layer.objects.active = obj

def get_collider_prefixes():
    exporter_configs = get_addon_prefs()
    collider_prefixes = [exporter_configs.box_collider_prefix,
                         exporter_configs.capsule_collider_prefix,
                         exporter_configs.sphere_collider_prefix,
                         exporter_configs.convex_collider_prefix,
                         exporter_configs.mesh_collider_prefix]

    return collider_prefixes

def get_object_prefixes():
    context = bpy.context
    exporter_configs = context.scene.exporter_configs

    objects_prefixes = [exporter_configs.static_mesh_prefix,
                        exporter_configs.skeletal_mesh_prefix,
                        exporter_configs.camera_prefix]

    return objects_prefixes

def get_all_child_of_child(obj):
    children = list(obj.children)
    all_children = []

    while len(children):
        child = children.pop()
        all_children.append(child)
        children.extend(child.children)

    return all_children

def select_object_hierarchy(obj):
    children = get_all_child_of_child(obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    for child in children:
        child.select_set(True)

    return


def set_correct_child_matrix(parentObj, childObj):
    if parentObj.parent is None:
        childObj.matrix_parent_inverse = parentObj.matrix_world.inverted()
    else:
        childObj.matrix_world = parentObj.parent.matrix_world
        childObj.matrix_local.identity()

    return


def delete_hierarchy(parent_obj_name):
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects.get(parent_obj_name)
    obj.animation_data_clear()
    names = []

    def get_child_names(obj):
        for child in obj.children:
            names.append(child.name)
            if child.children:
                get_child_names(child)

    get_child_names(obj)

    objects = bpy.data.objects
    for n in names:
        n = objects[n]
        n.select_set(True)

    # Remove the animation from the all the child objects
    for child_name in names:
        bpy.data.objects[child_name].animation_data_clear()

    bpy.ops.object.delete()


def get_addon_prefs():
    # Prefs for the BitTools addon instead of the BitTools.exporter module
    return bpy.context.preferences.addons[__package__.split('.')[0]].preferences

def get_exporter_configs():
    # Prefs for the BitTools addon instead of the BitTools.exporter module
    return bpy.context.scene.exporter_configs

def get_current_project():
    # Gets the current active registered project
    return bpy.context.scene.exporter_configs.registered_projects

def get_current_engine():
    return get_exporter_configs().engine_configs_list