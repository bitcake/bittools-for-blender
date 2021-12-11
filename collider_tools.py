import logging
import bpy
from bpy.types import Operator
from mathutils import Vector
import mathutils


class BITCAKE_OT_add_box_collider(Operator):
    bl_idname = "bitcake.add_box_collider"
    bl_label = "Add Box Collider"
    bl_description = "Add a box collider to selected object and rename it according to naming convention"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'EDIT_MESH'

    def execute(self, context):
        if found_issues_during_checking(self, context):
            return {'CANCELLED'}

        if context.mode == 'EDIT_MESH':
            bound_box = create_bound_box_from_selected_vertices()
            if not bound_box:
                self.report({"ERROR"}, "No vertices selected! Please select some vertices and try again.")
                return {'CANCELLED'}
        else:
            create_bound_box_from_selected_objects()

        return {'FINISHED'}


class BITCAKE_OT_add_sphere_collider(Operator):
    bl_idname = "bitcake.add_sphere_collider"
    bl_label = "Add Sphere Collider"
    bl_description = "Add a sphere collider to selected object and rename it according to naming convention"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'EDIT_MESH'

    def execute(self, context):
        if found_issues_during_checking(self, context):
            return {'CANCELLED'}

        if context.mode == 'EDIT_MESH':
            sphere = create_sphere_from_selected_vertices()
            if not sphere:
                self.report({"ERROR"}, "No vertices selected! Please select some vertices and try again.")
                return {'CANCELLED'}
        else:
            logging.info(context.mode)
            create_sphere_from_selected_objects()

        return {'FINISHED'}


class BITCAKE_OT_add_convex_collider(Operator):
    bl_idname = "bitcake.add_convex_collider"
    bl_label = "Add Convex Collider"
    bl_description = "Add a convex collider to selected object based on the Object's shape and rename it according to naming convention"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'EDIT_MESH'

    def execute(self, context):
        if found_issues_during_checking(self, context):
            return {'CANCELLED'}

        if context.mode == 'EDIT_MESH':
            hull = create_convex_hull_from_selected_vertices(self, context)
            if not hull:
                self.report({"ERROR"}, "No vertices selected! Please select some vertices and try again.")
                return {'CANCELLED'}
        else:
            create_convex_hull_from_selected_objects(self, context)

        return {'FINISHED'}


def found_issues_during_checking(self, context):
    """Checks for issues before running any Collider operator."""

    # User cannot operate in Edit Mode if he has more than 1 object selected
    if len(context.selected_objects) > 1 and context.mode == 'EDIT_MESH':
        self.report({"ERROR"}, "More than one object is selected, please only select one object at a time.")
        return True

    # Check the contents of all the user's selection
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            self.report({"ERROR"}, "The selected object is not a Mesh.")
            return True
        # Check if object is inside an Armature Hierachy, if so, cancel Operator.
        elif obj.parent is not None:
            has_armature = check_hierarchy_for_armature(self, context, obj)
            if has_armature:
                self.report({"ERROR"},
                            "The selected object is part of an Armature Hierarchy.\n Please remove it from the Armature and try again.")
                return True


def check_hierarchy_for_armature(self, context, obj):
    """Checks parental hierarchy for an Armature, returns True if there's one."""

    # Go up the hierarchy until parent because there could be an object inside an object
    please = False
    while please is False:
        parent = obj.parent

        # Unhide parent in case it's hidden
        original_hide_status = parent.hide_get()
        if parent.hide_get():
            parent.hide_set(not parent.hide_get())
            parent.hide_viewport = not parent.hide_get()

        if obj.type == 'ARMATURE' or parent.type == 'ARMATURE':
            # In case we unhid object, hide it again
            if original_hide_status:
                parent.hide_set(not parent.hide_get())
                parent.hide_viewport = not parent.hide_get()
            return True
        else:
            # In case we unhid object, hide it again
            if original_hide_status:
                parent.hide_set(not parent.hide_get())
                parent.hide_viewport = not parent.hide_get()

            obj = obj.parent
            please = True

    return False

def create_convex_hull_from_selected_vertices(self, context):
    verts = get_vertices_from_selection()
    if not verts:
        return

    obj = context.object

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[1]
    data = bpy.context.active_object.data

    for v in data.vertices:
        v.select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.convex_hull()

    current_obj = bpy.context.active_object
    prefix = get_collider_prefixes()['convex']
    current_obj.name = prefix + '_' + obj.name
    current_obj.parent = obj
    current_obj.matrix_parent_inverse = obj.matrix_world.inverted()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    current_obj.select_set(True)

    return current_obj


def create_convex_hull_from_selected_objects(self, context):
    selected_objects = context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')

    for obj in selected_objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.duplicate()
        current_obj = bpy.context.object
        data = bpy.context.object.data

        for v in data.vertices:
            v.select = True

        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.convex_hull()
        prefix = get_collider_prefixes()['convex']
        current_obj.name = prefix + '_' + obj.name
        current_obj.parent = obj
        current_obj.matrix_parent_inverse = obj.matrix_world.inverted()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    return


def create_sphere_from_selected_vertices():
    active_object = bpy.context.active_object
    collection = bpy.context.active_object.users_collection[0]

    verts = get_vertices_from_selection()
    if not verts:
        return

    bounds = get_bounds(verts)
    bounding_box = define_bounding_box_from_bounds(bounds)
    bounding_box_center = find_center_from_vertices(bounding_box[0], active_object)

    bounds_limit = mathutils.Vector(bounding_box[0][0])
    bounds_limit = (bounds_limit + active_object.location)
    radius = bounds_limit - bounding_box_center

    cursor = bpy.context.scene.cursor
    cursor.location = bounding_box_center

    # Create the sphere using the vector length so that it has measurements in meters.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=32, radius=radius.length, enter_editmode=False,
                                         align='WORLD', location=bounding_box_center, scale=(1, 1, 1))

    # Organize everything, placing it under the correct collection and parent, then rename the sphere
    sphere = bpy.context.active_object
    master_collection = bpy.context.collection
    master_collection.objects.unlink(sphere)
    collection.objects.link(sphere)
    sphere.parent = active_object
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

    prefix = get_collider_prefixes()['sphere']
    sphere.name = prefix + '_' + active_object.name

    return sphere


def create_sphere_from_selected_objects():
    master_collection = bpy.context.collection

    sphere = None
    for obj in bpy.context.selected_objects:
        active_object = obj
        bounding_box = active_object.bound_box
        collection = obj.users_collection[0]
        cursor = bpy.context.scene.cursor

        # Applies transform so that we can properly do The Math®
        apply_transform_reverse_hierarchy(obj)
        bounding_box_center = find_bounding_box_center_from_obj(active_object)
        cursor.location = bounding_box_center

        # Get any point in th bounding box and find the radius using it
        # (Radius = The distance between the center of the bbox and any bbox point)
        bounds_limit = mathutils.Vector(bounding_box[0])
        bounds_limit = (bounds_limit + active_object.location)
        cursor.location = bounding_box_center
        radius = bounds_limit - bounding_box_center

        # Create the sphere using the vector length so that it has measurements in meters.
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=32, radius=radius.length, enter_editmode=False,
                                             align='WORLD', location=bounding_box_center, scale=(1, 1, 1))

        # Organize everything, placing it under the correct collection and parent, then rename the sphere
        sphere = bpy.context.active_object

        if sphere.users_collection[0] == master_collection:
            master_collection.objects.unlink(sphere)

        collection.objects.link(sphere)
        sphere.parent = active_object
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

        prefix = get_collider_prefixes()['sphere']
        sphere.name = prefix + '_' + active_object.name

    return sphere


def apply_transform_reverse_hierarchy(obj):
    # Go up the hierarchy until parent because there could be an object inside an object
    current_object = obj
    please = False
    while please is False:
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        if current_object.parent is not None:
            current_object.parent.select_set(True)
            bpy.context.view_layer.objects.active = current_object.parent
            current_object = current_object.parent
            continue
        else:
            bpy.context.view_layer.objects.active = obj
            please = True

    # Restore Original Selection

    return


def create_bound_box_from_selected_vertices():
    verts = get_vertices_from_selection()
    if not verts:
        return

    bounds = get_bounds(verts)
    bounding_box = define_bounding_box_from_bounds(bounds)

    active_object = bpy.context.active_object
    prefix = get_collider_prefixes()['box']
    name = prefix + '_' + active_object.name

    bounding_box = create_mesh(name, (bounding_box[0], bounding_box[1], bounding_box[2]), active_object)

    cursor = bpy.context.scene.cursor
    cursor.location = active_object.location
    bounding_box.select_set(True)
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
    bounding_box.select_set(False)

    return bounding_box


def get_vertices_from_selection():
    bpy.ops.object.mode_set(mode='OBJECT')
    verts = [vert for vert in bpy.context.object.data.vertices if vert.select]

    return verts


def get_bounds(vertex_list):
    """Found this super-fast and handy function in the web, thanks.\n
    Returns a list of tuples containing the min and max values of each axis in the bounds of a vertex list."""
    points = [points.co for points in vertex_list]
    x_co, y_co, z_co = zip(*points)

    return [(min(x_co), min(y_co), min(z_co)), (max(x_co), max(y_co), max(z_co))]


def define_bounding_box_from_bounds(bounds):
    min_bounds = bounds[0]
    max_bounds = bounds[1]
    vertices = [(min_bounds[0], min_bounds[1], min_bounds[2]),
                (min_bounds[0], max_bounds[1], min_bounds[2]),
                (max_bounds[0], max_bounds[1], min_bounds[2]),
                (max_bounds[0], min_bounds[1], min_bounds[2]),
                (min_bounds[0], min_bounds[1], max_bounds[2]),
                (min_bounds[0], max_bounds[1], max_bounds[2]),
                (max_bounds[0], max_bounds[1], max_bounds[2]),
                (max_bounds[0], min_bounds[1], max_bounds[2]), ]

    edges = []
    faces = [(0, 1, 2, 3),
             (4, 5, 1, 0),
             (5, 4, 7, 6),
             (3, 2, 6, 7),
             (0, 3, 7, 4),
             (5, 6, 2, 1)]

    return (vertices, edges, faces)


def create_bound_box_from_selected_objects():
    cursor = bpy.context.scene.cursor
    selection = bpy.context.selected_objects

    for obj in selection:
        if obj.type != 'MESH':
            continue

        active_object = obj
        active_object_collection = obj.users_collection[0]
        cursor.location = active_object.location
        bpy.ops.object.select_all(action='DESELECT')

        # I had to check each vertice by hand to figure out which one was which
        # Then I build that faces array by drawing and plotting each loop
        vertices = active_object.bound_box
        edges = []
        faces = [(0, 1, 2, 3),
                 (0, 4, 5, 1),
                 (4, 7, 6, 5),
                 (7, 3, 2, 6),
                 (1, 5, 6, 2),
                 (0, 3, 7, 4), ]

        prefix = get_collider_prefixes()['box']
        name = prefix + '_' + active_object.name

        new_object = create_mesh(name, (vertices, edges, faces), active_object)

        new_object.select_set(True)
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

    return


def create_mesh(name, pydata, parent=None):
    """Function takes in a name string, a tuple of (vertices, edges, faces) and optionally a Parent object."""
    new_mesh = bpy.data.meshes.new(name)
    new_mesh.from_pydata(pydata[0], pydata[1], pydata[2])
    new_mesh.update()

    new_object = bpy.data.objects.new(name, new_mesh)

    collection = bpy.context.collection

    if parent:
        collection = parent.users_collection[0]
        new_object.parent = parent

    collection.objects.link(new_object)

    return new_object


def get_collider_prefixes():
    """Returns a dictionary containing all prefixes, access them with the strings:
    'box', 'capsule', 'sphere', 'convex', 'mesh' WARNING: Does not contain separator"""

    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    collider_prefixes = {'box': addon_prefs.box_collider_prefix,
                         'capsule': addon_prefs.capsule_collider_prefix,
                         'sphere': addon_prefs.sphere_collider_prefix,
                         'convex': addon_prefs.convex_collider_prefix,
                         'mesh': addon_prefs.mesh_collider_prefix}

    return collider_prefixes


def find_bounding_box_center_from_obj(obj):
    local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center

    return global_bbox_center


def find_center_from_vertices(vertices, obj):
    local_bbox_center = sum((Vector(b) for b in vertices), Vector()) / len(vertices)
    global_bbox_center = obj.matrix_world @ local_bbox_center

    return global_bbox_center


classes = (BITCAKE_OT_add_box_collider,
           BITCAKE_OT_add_sphere_collider,
           BITCAKE_OT_add_convex_collider)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
