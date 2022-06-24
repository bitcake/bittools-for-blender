import bpy
from bpy.types import Operator

class BITCAKE_OT_mirror_weights_all_vertex_groups(Operator):
    bl_idname = "bitcake.mirror_weights_all"
    bl_label = "Mirror Goddamn Weights Properly (All Vertex Groups)"
    bl_description = "Copies the default Maya Mirroring behavior! Works for all Vertex Groups in this mesh, needs correct naming scheme!"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        return context.mode == 'OBJECT' or context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        configs = context.scene.rigging_configs
        left_to_right = configs.left_to_right
        active_vg_name = context.object.vertex_groups.active.name

        if left_to_right:
            side_to_mirror = configs.left_side
        else:
            side_to_mirror = configs.right_side

        vertex_groups = context.object.vertex_groups.items().copy()
        for vertex_group in vertex_groups:
            current_side = get_mirror_side(vertex_group[0])
            if current_side is None:
                self.report({'ERROR'}, f"Bone named {vertex_group[0]} cannot be mirror'd. Make sure its naming has the correct Side Keywords that are separated by the correct separator.")
            elif configs.mirror_middle and current_side == configs.middle:
                clear_weights_on_opposite_side(context, vertex_group[1])
                mirror_vertex_group_middle(context, vertex_group[1])
            elif current_side == side_to_mirror:
                mirror_vertex_group_sides(context, vertex_group[1])

        context.object.vertex_groups.active = context.object.vertex_groups.get(active_vg_name)

        return {'FINISHED'}


class BITCAKE_OT_mirror_weights_active_vertex_group(Operator):
    bl_idname = "bitcake.mirror_weights_active"
    bl_label = "Mirror Goddamn Weights Properly (Active)"
    bl_description = "Copies the default Maya Mirroring behavior! Works for only the active Vertex Group of this mesh, needs correct naming scheme!"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        return context.mode == 'OBJECT' or context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        configs = context.scene.rigging_configs
        active_vg = context.object.vertex_groups.active

        side_to_mirror = get_mirror_side(active_vg.name)
        if side_to_mirror is None:
            self.report({'ERROR'}, "Bone cannot be mirror'd. Make sure its naming has the correct Side Keywords that are separated by the correct separator.")
            return {'CANCELED'}
        elif side_to_mirror == configs.middle:
            clear_weights_on_opposite_side(context, active_vg)
            mirror_vertex_group_middle(context, active_vg)
        else:
            mirror_vertex_group_sides(context, active_vg)

        context.object.vertex_groups.active = context.object.vertex_groups.get(active_vg.name)

        return {'FINISHED'}

def get_mirror_side(name_to_mirror):
    configs = bpy.context.scene.rigging_configs
    split_name = name_to_mirror.split(configs.separator)

    for item in split_name:
        if item == configs.left_side:
            return configs.left_side
        elif item == configs.right_side:
            return configs.right_side
        elif item == configs.middle:
            return configs.middle

    return None

def clear_weights_on_opposite_side(context, vertex_group):
    context.object.vertex_groups.active = context.object.vertex_groups.get(vertex_group.name)
    vertices = context.object.data.vertices
    active_vertex_group = context.object.vertex_groups.active
    left_to_right = context.scene.rigging_configs.left_to_right

    for verts in vertices.items():
        if left_to_right:
            if verts[1].co[0] < -0.0001:
                active_vertex_group.remove([verts[0]])
        else:
            if verts[1].co[0] > 0.0001:
                active_vertex_group.remove([verts[0]])

        if  0.0001 >= verts[1].co[0] >= -0.0001:
            verts[1].select = True
            try:
                new_weight = active_vertex_group.weight(verts[0]) / 2
                active_vertex_group.add([verts[0]], new_weight, 'REPLACE')
            except RuntimeError:
                continue

    return

def mirror_vertex_group_middle(context, vertex_group):
    context.object.vertex_groups.active = context.object.vertex_groups.get(vertex_group.name)
    vertex_a = vertex_group.name

    bpy.ops.object.vertex_group_copy()
    context.object.data.use_paint_mask = False
    context.object.data.use_paint_mask_vertex = False
    bpy.ops.object.vertex_group_mirror(use_topology=False)

    vertex_b = context.object.vertex_groups.active.name

    modifier_name = "VertexWeightMix"
    mix_modifier = context.object.modifiers.new(name=modifier_name, type='VERTEX_WEIGHT_MIX')
    mix_modifier.vertex_group_a = vertex_a
    mix_modifier.vertex_group_b = vertex_b
    mix_modifier.mix_set = 'OR'
    mix_modifier.mix_mode = 'ADD'

    bpy.ops.object.modifier_apply(modifier=modifier_name)

    context.object.vertex_groups.remove(context.object.vertex_groups.get(vertex_b))

    return

def mirror_vertex_group_sides(context, vertex_group):
    context.object.vertex_groups.active = context.object.vertex_groups.get(vertex_group.name)
    new_name = mirror_naming(vertex_group.name)

    # Duplicate Active Vertex Group and Mirror it
    bpy.ops.object.vertex_group_copy()
    context.object.data.use_paint_mask = False
    context.object.data.use_paint_mask_vertex = False
    bpy.ops.object.vertex_group_mirror(use_topology=False)

    vertex_group_to_delete = context.object.vertex_groups.get(new_name)
    if vertex_group_to_delete is not None:
        context.object.vertex_groups.remove(vertex_group_to_delete)

    # Renames duplicated Vertex Group so there's no suffix added
    context.object.vertex_groups.active.name = new_name

    return

def mirror_naming(name_to_mirror):
    configs = bpy.context.scene.rigging_configs
    split_name = name_to_mirror.split(configs.separator)
    new_name = split_name.copy()

    for index, item in enumerate(split_name):
        if item == configs.left_side:
            new_name.pop(index)
            new_name.insert(index, configs.right_side)
            new_name = configs.separator.join(new_name)
        elif item == configs.right_side:
            new_name.pop(index)
            new_name.insert(index, configs.left_side)
            new_name = configs.separator.join(new_name)
        elif item == configs.middle:
            new_name = configs.separator.join(new_name)

    return new_name

def draw_panel(self, context):
    configs = context.scene.rigging_configs
    layout = self.layout

    if configs.left_to_right:
        label_text = 'Mirror All Left to Right'
    else:
        label_text = 'Mirror All Right to Left'

    layout.separator()
    layout.label(text='Mirror Skin Weights Tool')
    column = layout.column(align=True)
    row = column.row(align=True)
    row.prop(configs, 'left_to_right', text='L -> R or R -> L', toggle=1)
    row.prop(configs, 'mirror_middle', text='Mirror Middle Bones', toggle=1)
    row = column.row()
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
