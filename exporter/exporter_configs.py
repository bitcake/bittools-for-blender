import bpy
import json
import os
from bpy.types import PropertyGroup, Scene
from bpy.props import BoolProperty, EnumProperty, StringProperty
from ..helpers import get_engine_configs_path

def list_registered_engine_configs(self, context):
    pcoll = preview_collections["main"]
    engine_list = []

    projects_file_path = get_engine_configs_path()

    if projects_file_path.is_file():
        with open(str(projects_file_path), 'r') as projects:
            projects_json = json.load(projects)

            for i, engine in enumerate(projects_json):
                engine_logo = pcoll[engine]
                engine_list.append((engine, engine, '', engine_logo.icon_id, i))

    return engine_list

class BITCAKE_PROPS_exporter_configs(PropertyGroup):
    engine_configs_list: EnumProperty(items=list_registered_engine_configs,
                                    name='',
                                    description='List all available engine export configurations.',
                                    )

    export_selected: BoolProperty(name="Selected", description="Only exports selected objects", default=False)
    export_collection: BoolProperty(name="Collection", description="Exports entire collection", default=False)
    export_batch: BoolProperty(name="Batch", description="Exports objects in a separate file", default=False)
    collection_to_folder: BoolProperty(name="Use Collections as Folders", description="Collections are turned into folders on export.", default=True)
    origin_transform: BoolProperty(name="Origin", description="Place objects in origin before exporting", default=False)
    apply_transform: BoolProperty(name="Apply", description="Apply transforms before exporting", default=False)
    export_textures: BoolProperty(name="Embed Textures", description="Embed Textures on FBX or not", default=False)
    export_nla_strips: BoolProperty(name="Export NLA Strips", description="Separate NLA Strips into their own animations when exporting.\nYou'll usually want this turned OFF for Game Engine", default=False)

    # Prefixes Setup (user changeable)
    separator: StringProperty(name='Separator', default='_')
    static_mesh_prefix: StringProperty(name='Static Mesh', default='SM')
    skeletal_mesh_prefix: StringProperty(name='Skeletal Mesh', default='SK')
    animation_prefix: StringProperty(name='Animation', default='Anim')
    pose_prefix: StringProperty(name='Pose', default='Pose')
    camera_prefix: StringProperty(name='Camera', default='Cam')

    custom_directory: StringProperty(name='', description='Custom Directory to Export to', subtype='DIR_PATH')


classes = (BITCAKE_PROPS_exporter_configs,)

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

    Scene.exporter_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_exporter_configs)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # UnRegister Custom Icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    del Scene.exporter_configs