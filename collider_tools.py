import bpy
from bpy.types import Operator
from mathutils import Vector


class BITCAKE_OT_add_box_collider(Operator):
    bl_idname = "bitcake.add_box_collider"
    bl_label = "Add Box Collider"
    bl_description = "Add a box collider to selected object and rename it according to naming convention"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        find_bounding_box_center()
        create_box_mesh_from_bounding_box()

        return {'FINISHED'}


def create_box_mesh_from_bounding_box():
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
        new_mesh = bpy.data.meshes.new(prefix + '_' + active_object.name)
        new_mesh.from_pydata(vertices, edges, faces)
        new_mesh.update()

        new_object = bpy.data.objects.new(prefix + '_' + active_object.name, new_mesh)
        new_object.parent = active_object

        master_collection = active_object_collection
        master_collection.objects.link(new_object)
        new_object.select_set(True)
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

    return


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
    o = bpy.context.object
    local_bbox_center = 0.125 * sum((Vector(b) for b in o.bound_box), Vector())
    global_bbox_center = o.matrix_world @ local_bbox_center

    print(global_bbox_center)
    return global_bbox_center


classes = (BITCAKE_OT_add_box_collider,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
