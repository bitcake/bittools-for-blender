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
        if len(context.selected_objects) > 1 and context.mode == 'EDIT_MESH':
            self.report({"ERROR"}, "More than one object is selected, please only select one object at a time.")
            return {'CANCELLED'}
        elif context.active_object.type != 'MESH':
            self.report({"ERROR"}, "The selected object is not a Mesh.")
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
        active_object = bpy.context.active_object
        bounding_box = active_object.bound_box
        bounding_box_center = find_bounding_box_center()

        # Put the cursor in the middle just to check if its working
        cursor = bpy.context.scene.cursor
        cursor.location = bounding_box_center

        bounds_limit = mathutils.Vector((bounding_box[0][0], bounding_box[0][1], bounding_box[0][2]))
        radius = bounds_limit - bounding_box_center
        print(radius.length)

        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=32, radius=radius.length, enter_editmode=False, align='WORLD', location=bounding_box_center, scale=(1, 1, 1))

        return {'FINISHED'}


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

    return bounding_box


def get_vertices_from_selection():
    bpy.ops.object.mode_set(mode='OBJECT')
    verts = [vert for vert in bpy.context.object.data.vertices if vert.select]

    return verts

def get_bounds(vertex_list):
    """Found this super fast and handy function in the web, thanks.\n
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
                (max_bounds[0], min_bounds[1], max_bounds[2]),]

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
                 (0, 3, 7, 4),]

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


def find_bounding_box_center():
    o = bpy.context.active_object
    local_bbox_center = 0.125 * sum((Vector(b) for b in o.bound_box), Vector())
    global_bbox_center = o.matrix_world @ local_bbox_center

    return global_bbox_center


classes = (BITCAKE_OT_add_box_collider,
           BITCAKE_OT_add_sphere_collider,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
