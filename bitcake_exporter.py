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
        # This is a Generator because I use it on the batch exporter to properly export things.
        for obj in rename_with_prefix(objects_list):
            construct_animation_events_json(self, constructed_path, obj)
            continue

        if panel_prefs.origin_transform:
            for obj in objects_list:
                obj.location = 0, 0, 0

        if panel_prefs.apply_transform:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Get current file path, append _bkp and save as new file
        filename = original_path.stem + '_bkp'
        new_path = original_path.with_stem(filename)
        bpy.ops.wm.save_mainfile(filepath=str(new_path))

        # Builds the parameters and exports scene
        exporter(constructed_path, panel_prefs)

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
        configs = get_engine_configs()

        # Save current file
        original_path = Path(bpy.data.filepath)
        bpy.ops.wm.save_mainfile(filepath=str(original_path))

        objects_list = make_objects_list(context)

        # I just wanted to use generators to see how they worked. Please don't judge.
        for obj in rename_with_prefix(objects_list):
            if obj.parent != None:
                continue

            print(f'THIS IS THE CURRENT OBJECT BEING EXPORTED {obj}')
            # If object is root object, construct its file path
            path = construct_fbx_path(self, context, obj)

            # If folder doesn't exist, create it
            path.parent.mkdir(parents=True, exist_ok=True)

            # Create .json file with all animation events
            construct_animation_events_json(self, path, obj)

            # Get all children objects and select ONLY them and the parent, also making it the active obj
            children = get_all_child_of_child(obj)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            for child in children:
                child.select_set(True)

            if panel_prefs.origin_transform:
                obj.location = 0, 0, 0

            if panel_prefs.apply_transform:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            # Builds the parameters and exports scene
            exporter(path, panel_prefs, batch=True)

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
        obj = context.object

        if obj.type != 'ARMATURE':
            self.report({"ERROR"}, "Not an armature")
            return {'CANCELLED'}

        # If object is root object, construct its file path
        path = construct_fbx_path(self, context, obj)

        # If folder doesn't exist, create it
        path.parent.mkdir(parents=True, exist_ok=True)

        markers_json = Path(get_markers_configs_file_path())
        markers_json = json.load(markers_json.open())

        fps = bpy.context.scene.render.fps
        markers_json['FPS'] = fps
        if fps % 30 != 0:
            self.report({"ERROR"}, "Scene is not currently at 30 or 60FPS! Please FIX!")

        markers_json['Character'] = obj.name

        for mrks in bpy.context.scene.timeline_markers:
            markers_json['TimelineMarkers'][mrks.name] = mrks.frame

        for action in bpy.data.actions:
            markers_json['ActionsMarkers'][action.name] = {}
            for marker in action.pose_markers:
                markers_json['ActionsMarkers'][action.name][marker.name] = marker.frame

        path = path.with_stem(path.stem + '_events')
        path = path.with_suffix('.json')
        print(path)

        with open(path, 'w') as jfile:
            json.dump(markers_json, jfile, indent=4)

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


class BITCAKE_OT_ignore_on_export(bpy.types.Operator):
    """Right click entry test"""
    bl_idname = "bitcake.ignore_on_export"
    bl_label = "Ignore on Export"

    def execute(self, context):
        collection = context.collection

        if not collection.get('Ignore'):
            collection['Ignore'] = True
        elif collection['Ignore']:
            collection['Ignore'] = not collection['Ignore']

        if collection['Ignore']:
            collection.name = collection.name + '_[IGNORED]'
            bpy.ops.outliner.collection_color_tag_set(color='COLOR_01')
        else:
            collection.name = collection.name.replace('_[IGNORED]', '')
            bpy.ops.outliner.collection_color_tag_set(color='NONE')

        return {'FINISHED'}


def collection_outliner_context_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.label(text='BitCake Tools')
    layout.operator("bitcake.ignore_on_export", text="Ignore on Export")


# Sad reminder to do research properly before jumping into the first solution
# Blender 2.92 had introduced a better way to export to Unity, this is the OLD way of doing things
def unity_animation_setup(context, obj_list):
    c = context.copy()

    for obj in obj_list:
        if obj.type == 'ARMATURE':
            # Context Override so the methods below only works on select objects
            c['selected_objects'] = [obj]
            c['selected_editable_objects'] = [obj]
            bpy.ops.transform.rotate(c, value=-1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SPHERE', proportional_size=0.13513, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)
            bpy.ops.object.transform_apply(c, location=False, rotation=True, scale=False)
            bpy.ops.transform.rotate(c, value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SPHERE', proportional_size=0.13513, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)

            for child in obj.children:
                if child.type == 'MESH':
                    c['selected_editable_objects'] = [child]
                    bpy.ops.object.transform_apply(c, location=False, rotation=True, scale=False)

    return


def exporter(path, panel_preferences, batch=False):
    configs = get_engine_configs()

    use_selection = panel_preferences.export_selected
    use_collection = panel_preferences.export_collection

    if batch:
        use_selection = True
        use_collection = False

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
        bake_anim_step=configs['anim_sampling'],
        bake_anim_simplify_factor=configs['anim_simplify'],
        use_selection=use_selection,
        use_active_collection=use_collection,
        axis_forward=configs['forward_axis'],
        axis_up=configs['up_axis'],
    )

def construct_animation_events_json(self, path, obj):
        if obj.type != 'ARMATURE':
            return

        # Verify if file has markers, if not, don't build .json
        has_markers = False
        for action in bpy.data.actions:
            for marker in action.pose_markers:
                has_markers = True

        for mrks in bpy.context.scene.timeline_markers:
            has_markers = True

        if not has_markers:
            return

        markers_json = Path(get_markers_configs_file_path())
        markers_json = json.load(markers_json.open())

        fps = bpy.context.scene.render.fps
        markers_json['FPS'] = fps
        if fps % 30 != 0:
            self.report({"ERROR"}, "Scene is not currently at 30 or 60FPS! Please FIX!")

        markers_json['Character'] = obj.name

        markers_json['TimelineMarkers'] = []
        for mrks in bpy.context.scene.timeline_markers:
            dictionary = {"Name": mrks.name, "Frame": mrks.frame}
            markers_json['TimelineMarkers'].append(dictionary)

        markers_json['ActionsMarkers'] = []
        for action in bpy.data.actions:
            action_marker = {"Name": action.name, "Markers": []}
            for marker in action.pose_markers:
                marker_dict = {"Name": marker.name, "Frame": marker.frame}
                action_marker['Markers'].append(marker_dict)
            markers_json['ActionsMarkers'].append(action_marker)

        path = path.with_stem(path.stem + '_events')
        path = path.with_suffix('.json')

        with open(path, 'w') as jfile:
            json.dump(markers_json, jfile, indent=4)

        return

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


def get_engine_configs():
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
            pathway.append(split_part[-1])
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
            pathway.append(split_part[-1])
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

    objects_list = []
    if panel_prefs.export_selected:
        selected_objects = bpy.context.selected_objects
        selected_objects = append_child_colliders(selected_objects)
        objects_list = selected_objects

    elif panel_prefs.export_collection:
        change_active_collection()
        collection_objects = bpy.context.active_object.users_collection[0].all_objects
        collection_objects = append_child_colliders([obj for obj in collection_objects])
        objects_list = collection_objects

    else:
        bpy.ops.object.select_all(action='DESELECT')
        toggle_all_colliders_visibility(True)
        bpy.ops.object.select_all()
        objects_list = bpy.context.selected_objects

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


def filter_object_list(object_list):
    '''Removes all objects that are inside an Ignored Collection or are Linked inside one'''

    for obj in object_list:
        for col in obj.users_collection:
            if col.get('Ignore'):
                print(obj.name + " TA IGNORADO dentro da " + col.name)
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


def get_markers_configs_file_path():
    # Gets Addon Path (__init__.py)
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == __package__:
            addon_path = Path(mod.__file__)

    engine_configs_path = Path(addon_path.parent / 'anim_events.json')

    return engine_configs_path


def rename_with_prefix(obj_list):
    """Renames current obj and all its children. If Generator is true it'll yield the current object being renamed."""

    for obj in obj_list:
        if obj.parent is None:
            all_children = get_all_child_of_child(obj)
            for child in all_children:
                print(child)
                prefix = get_correct_prefix(child)
                if prefix:
                    child.name = prefix + child.name
        prefix = get_correct_prefix(obj)
        if prefix:
            obj.name = prefix + obj.name

        yield obj


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

    # If object is correctly named, ignore it and return its prefix
    if collider_prefixes.__contains__(split_name[0]) or object_prefixes.__contains__(split_name[0]):
        return

    # Return correct prefix for each case
    if obj.type == 'ARMATURE':
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
           BITCAKE_OT_toggle_all_colliders_visibility,
           BITCAKE_OT_ignore_on_export)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.OUTLINER_MT_collection.append(collection_outliner_context_draw)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.OUTLINER_MT_collection.remove(collection_outliner_context_draw)
