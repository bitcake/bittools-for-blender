from posixpath import basename
import bpy
import json
import os
from bpy.types import PropertyGroup, Scene
from bpy.utils import previews
from bpy.props import BoolProperty, EnumProperty, StringProperty
from ..helpers import get_engine_configs_path, get_registered_projects_path

def update_registered_projects(self, context):
    projects_list = []

    projects_file_path = get_registered_projects_path()

    if projects_file_path.is_file():
        with open(str(projects_file_path), 'r') as projects:
            projects_json = json.load(projects)

            for i, project in enumerate(projects_json):
                projects_list.append((project, project, '', i))
    else:
        projects_list = [("NONE", "No Projects Registered", "", 0),]

    return projects_list

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

def check_for_prefixes(self, context):
    exporter_configs = context.scene.exporter_configs
    separator = exporter_configs.separator
    non_batch_filename = exporter_configs.non_batch_filename
    prefix_list = [exporter_configs.static_mesh_prefix , exporter_configs.skeletal_mesh_prefix]

    if prefix_list.__contains__(non_batch_filename.split(separator)[0]):
        exporter_configs.filename_alert = False
    else:
        exporter_configs.filename_alert = True


class BITCAKE_PROPS_exporter_configs(PropertyGroup):
    registered_projects: EnumProperty(items=update_registered_projects,
                                      name='',
                                      description='Register projects here before starting. Current Active project',
                                      )

    engine_configs_list: EnumProperty(items=list_registered_engine_configs,
                                    name='',
                                    description='List all available engine export configurations.',
                                    )

    export_selection_types: EnumProperty(items=[('SELECTED', 'Selected Only', 'Export Selected Objects Only', 'RESTRICT_SELECT_OFF', 0),
                                                ('COLLECTION', 'Entire Active Collection', "Export Objects in the Active Object's Collection", 'OUTLINER_COLLECTION', 1),
                                                ('ALL', 'All', "Export All Objects", 'OUTLINER', 2)], name='', default='ALL')

    export_selected: BoolProperty(name="Selected", description="Only exports selected objects", default=False)
    export_collection: BoolProperty(name="Collection", description="Exports entire collection", default=False)
    export_batch: BoolProperty(name="Batch", description="Exports objects in a separate file", default=False)
    collection_to_folder: BoolProperty(name="Use Collections as Folders", description="Collections are turned into folders on export.", default=True)
    origin_transform: BoolProperty(name="Origin", description="Place objects in origin before exporting", default=False)
    apply_transform: BoolProperty(name="Apply", description="Apply transforms before exporting", default=False)
    export_textures: BoolProperty(name="Embed Textures", description="Embed Textures on FBX or not", default=False)
    export_nla_strips: BoolProperty(name="Export NLA Strips", description="Separate NLA Strips into their own animations when exporting.\nYou'll usually want this turned OFF for Game Engine", default=False)
    filename_alert: BoolProperty(name="Filename Alert", default=True)

    # Prefixes Setup (user changeable)
    separator: StringProperty(name='Separator', default='_')
    static_mesh_prefix: StringProperty(name='Static Mesh', default='SM')
    static_mesh_export: BoolProperty(name="Static Mesh Export", description="Enables or disables exporting of Static Meshes", default=True)
    skeletal_mesh_prefix: StringProperty(name='Skeletal Mesh', default='SK')
    skeletal_mesh_export: BoolProperty(name="Skeletal Mesh Export", description="Enables or disables exporting of Skeletal Meshes (Armatures)", default=True)
    animation_prefix: StringProperty(name='Animation', default='Anim')
    animation_export: BoolProperty(name="Animations Export", description="Enables or disables exporting of Animations", default=True)
    camera_prefix: StringProperty(name='Camera', default='Cam')
    camera_export: BoolProperty(name="Camera Export", description="Enables or disables exporting of Cameras", default=False)

    non_batch_filename: StringProperty(name='Filename', default='', description=f"Name of the exported file. You SHOULD prefix your file with the correct Static Mesh or Skeletal Mesh prefixes! It'll be red until you do so, but won't stop you from exporting the file.", update=check_for_prefixes)
    custom_directory: StringProperty(name='', description='Custom Directory to Export to', subtype='DIR_PATH')




classes = (BITCAKE_PROPS_exporter_configs,)

preview_collections = {}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register Custom Icons
    pcoll = previews.new()
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
        previews.remove(pcoll)
    preview_collections.clear()

    del Scene.exporter_configs