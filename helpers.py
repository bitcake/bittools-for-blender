import addon_utils
import json
import bpy
from pathlib import Path
from mathutils import Vector, Quaternion, Euler

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

def get_current_engine():
    exporter_configs = bpy.context.scene.exporter_configs

    return exporter_configs.engine_configs_list

def get_current_project_assets_path():
    """Returns a String Path for the current project Asset folder"""

    addon_prefs = get_addon_prefs()
    active_project = addon_prefs.registered_projects

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    projects_file_path = Path(addon_path.parent / 'configs' / 'registered_projects.json')
    projects_json = json.load(projects_file_path.open())

    return projects_json[active_project]['assets']

def get_current_project_structure_json():
    """Returns the project_structure.json file created by BitPipe as a json Object. Returns None if file not found."""
    asset_path = Path(get_current_project_assets_path())
    json_path = asset_path.joinpath('project_structure.json')

    try:
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

def get_markers_configs_file_path():
    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    engine_configs_path = Path(addon_path.parent / 'configs' / 'anim_events.json')

    return engine_configs_path


def select_and_make_active(context, obj):
    # Deselects everything then selects obj and make it active
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[obj.name].select_set(True)
    context.view_layer.objects.active = obj

    return

def get_collider_prefixes():
    addon_prefs = get_addon_prefs()
    collider_prefixes = [addon_prefs.box_collider_prefix,
                         addon_prefs.capsule_collider_prefix,
                         addon_prefs.sphere_collider_prefix,
                         addon_prefs.convex_collider_prefix,
                         addon_prefs.mesh_collider_prefix]

    return collider_prefixes

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

def get_addon_prefs():
    # Prefs for the BitTools addon instead of the BitTools.exporter module
    return bpy.context.preferences.addons[__package__.split('.')[0]].preferences