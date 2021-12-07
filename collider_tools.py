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
        get_box_vertices()

        return {'FINISHED'}


def get_box_vertices():
    cursor = bpy.context.scene.cursor
    active_object = bpy.context.active_object

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

    new_mesh = bpy.data.meshes.new('new_mesh')
    new_mesh.from_pydata(vertices, edges, faces)
    new_mesh.update()
    new_object = bpy.data.objects.new('new_object', new_mesh)

    master_collection = bpy.context.scene.collection
    master_collection.objects.link(new_object)
    new_object.select_set(True)
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)



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
