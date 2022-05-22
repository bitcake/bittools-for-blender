import bpy
from bpy.types import Operator

class BITCAKE_OT_mirror_weights_all_vertex_groups(Operator):
    bl_idname = "bitcake.mirror_weights_all"
    bl_label = "Mirror Goddamn Weights Properly (All Vertex Groups)"
    bl_description = "Does what this software should do out of the box: MIRROR MY WEIGHTS! Works for all Vertex Groups in this mesh, needs naming scheme ending with .r or .l"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        return context.mode == 'OBJECT' or context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        configs = context.scene.rigging_configs
        left_to_right = configs.left_to_right

        if left_to_right:
            side_to_mirror = configs.left_side
            side_to_delete = configs.right_side
        else:
            side_to_mirror = configs.right_side
            side_to_delete = configs.left_side

        active_vg = context.object.vertex_groups.active.name

        vgs_to_mirror = []
        for vertex_group in context.object.vertex_groups.items():
            vg_split = vertex_group[0].split(configs.separator)

            if vg_split[-1] == side_to_delete:
                context.object.vertex_groups.remove(vertex_group[1])

            if vg_split[-1] == side_to_mirror:
                vgs_to_mirror.append(vertex_group[1])

        for vertex_group in vgs_to_mirror:
            context.object.vertex_groups.active = vertex_group
            bpy.ops.object.vertex_group_copy()
            context.object.data.use_paint_mask = False
            context.object.data.use_paint_mask_vertex = False
            bpy.ops.object.vertex_group_mirror(use_topology=False)
            context.object.vertex_groups.active.name = vertex_group.name[:-1] + side_to_delete

        # In case you were selecting a Vertex Group that gets deleted midway we do this to pick the new one
        context.object.vertex_groups.active = context.object.vertex_groups.get(active_vg)

        return {'FINISHED'}


class BITCAKE_OT_mirror_weights_active_vertex_group(Operator):
    bl_idname = "bitcake.mirror_weights_active"
    bl_label = "Mirror Goddamn Weights Properly (Active)"
    bl_description = "Does what this software should do out of the box. MIRROR MY WEIGHTS! Works for only the active Vertex Group of this mesh, needs naming scheme ending with .r or .l"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        return context.mode == 'OBJECT' or context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        configs = context.scene.rigging_configs
        active_vg = context.object.vertex_groups.active

        side_to_mirror = active_vg.name.split(configs.separator)[-1]
        if side_to_mirror == configs.left_side:
            side_to_delete = configs.right_side
        elif side_to_mirror == configs.right_side:
            side_to_delete = configs.left_side
        else:
            self.report({'ERROR'}, 'Active Vertex Group is not mirroable! Make sure its name ends with a .r or .l !')
            return {'CANCELLED'}

        # Duplicate Active Vertex Group and Mirror it
        bpy.ops.object.vertex_group_copy()
        context.object.data.use_paint_mask = False
        context.object.data.use_paint_mask_vertex = False
        bpy.ops.object.vertex_group_mirror(use_topology=False)

        vertex_group_to_delete = bpy.context.object.vertex_groups.get(active_vg.name[:-1] + side_to_delete)
        if vertex_group_to_delete is not None:
            bpy.context.object.vertex_groups.remove(vertex_group_to_delete)

        # Renames duplicated Vertex Group so there's no suffix added
        context.object.vertex_groups.active.name = active_vg.name[:-1] + side_to_delete

        return {'FINISHED'}


def draw_panel(self, context):
    configs = context.scene.rigging_configs
    layout = self.layout

    if configs.left_to_right:
        label_text = 'Mirror All Left to Right'
    else:
        label_text = 'Mirror All Right to Left'

    layout.separator()
    layout.label(text='Mirror Tool')
    row = layout.row()
    row.prop(configs, 'left_to_right', text='Switch L->R or R->L', toggle=1, icon='RESTRICT_SELECT_OFF')
    row = layout.row()
    row.operator('bitcake.mirror_weights_all', text=label_text, icon='MOD_MIRROR')
    row = layout.row()
    row.operator('bitcake.mirror_weights_active', text='Mirror Active Vertex Group', icon='MOD_MIRROR')

    return


classes = (BITCAKE_OT_mirror_weights_all_vertex_groups,
           BITCAKE_OT_mirror_weights_active_vertex_group,
           )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
