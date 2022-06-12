import bpy
from bpy.types import Operator, PropertyGroup, Scene
from bpy.props import IntProperty, FloatProperty
from ..helpers import delete_hierarchy

def update_treadmill(self, context):
    treadmill_configs = context.scene.treadmill_configs

    bpy.ops.bitcake.treadmill(steps_number=treadmill_configs.steps_number,
                              steps_spacing=treadmill_configs.steps_spacing,
                              steps_offset=treadmill_configs.steps_offset,
                              treadmill_speed=treadmill_configs.treadmill_speed
                              )

    return


class BITCAKE_PROPS_treadmill_configs(PropertyGroup):
     steps_number: IntProperty(name='Number of Steps', default=20, min=0, update=update_treadmill)
     steps_spacing: FloatProperty(name='Steps Spacing', default=2, min=1, update=update_treadmill)
     steps_offset: FloatProperty(name='Steps Offset', default=0, update=update_treadmill)
     treadmill_speed: FloatProperty(name='treadmill Speed (m/s)', default=2, min=0, update=update_treadmill)


class BITCAKE_OT_treadmill(Operator):
    bl_idname = "bitcake.treadmill"
    bl_label = "Treadmill Tool"
    bl_options = {'UNDO'}

    steps_number: IntProperty(name='Number of Steps', default=20, min=0)
    steps_spacing: FloatProperty(name='Steps Spacing', default=2, min=1)
    steps_offset: FloatProperty(name='Steps Offset', default=0)
    treadmill_speed: FloatProperty(name='treadmill Speed (m/s)', default=2, min=0)


    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj and obj.animation_data.action is not None:
            return True
        else:
            return False

    def execute(self, context):
        obj = context.object
        active_action = obj.animation_data.action if obj.animation_data else False

        active_action['HasTreadmill'] = True
        active_action['steps_number'] = self.steps_number
        active_action['steps_spacing'] = self.steps_spacing
        active_action['steps_offset'] = self.steps_offset
        active_action['treadmill_speed'] = self.treadmill_speed

        col = create_treadmill_collection()

        treadmill_group = col.objects.get('Treadmill Mover')
        if treadmill_group:
            delete_hierarchy(treadmill_group.name)
            bpy.ops.object.delete({'selected_objects': [treadmill_group]})

        steps_list = []
        for num, steps in enumerate(range(self.steps_number)):
            step = create_treadmill_step(col)
            move_amount = (self.steps_number - 1) * self.steps_spacing / 2 + self.steps_offset
            step.location = (0, -move_amount + (num*self.steps_spacing), 0)
            steps_list.append(step)

        treadmill_group = create_treadmill_group(col)

        for steps in steps_list:
            steps.parent = treadmill_group

        context.view_layer.objects.active = treadmill_group

        if treadmill_group.animation_data is None:
            treadmill_group.animation_data_create()

        treadmill_action = bpy.data.actions.get('Treadmill')
        if treadmill_action:
            bpy.data.actions.remove(treadmill_action)

        treadmill_action = bpy.data.actions.new('Treadmill')
        treadmill_group.animation_data.action = treadmill_action

        fc = treadmill_action.fcurves.find('location', index=1)
        if fc is None:
            fc = treadmill_action.fcurves.new('location', index=1, action_group='Treadmill')

        fc.extrapolation = 'LINEAR'
        key = fc.keyframe_points.insert(0, 0)
        key.interpolation = 'LINEAR'
        key = fc.keyframe_points.insert(context.scene.render.fps, self.treadmill_speed)
        key.interpolation = 'LINEAR'

        bpy.context.view_layer.objects.active = obj
        obj.animation_data.action = active_action

        return {'FINISHED'}


class BITCAKE_OT_remove_treadmill(Operator):
    bl_idname = "bitcake.remove_treadmill"
    bl_label = "Remove Treadmill"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj and obj.animation_data.action is not None:
            return True
        else:
            return False

    def execute(self, context):
        obj = context.object
        active_action = obj.animation_data.action

        treadmill_col = context.scene.collection.children.get('Treadmill')
        if treadmill_col:
            treadmill_group = treadmill_col.objects.get('Treadmill Mover')
            if treadmill_group:
                delete_hierarchy(treadmill_group.name)
                bpy.ops.object.delete({'selected_objects': [treadmill_group]})

            bpy.data.collections.remove(treadmill_col)

        treadmill_action = bpy.data.actions.get('Treadmill')
        if treadmill_action:
            bpy.data.actions.remove(treadmill_action)

        active_action['HasTreadmill'] = False

        return {'FINISHED'}


def create_treadmill_collection():
    treadmill_col = bpy.context.scene.collection.children.get('Treadmill')
    if treadmill_col:
        treadmill_col.hide_viewport = False # Turn on View
        return treadmill_col

    treadmill_col = bpy.context.blend_data.collections.new(name='Treadmill')
    bpy.context.scene.collection.children.link(treadmill_col)

    return treadmill_col

def create_treadmill_step(collection):
        mesh = bpy.data.meshes.new("treadmill_step")
        obj = bpy.data.objects.new(mesh.name, mesh)
        collection.objects.link(obj)

        verts = [
                # Up Face
                ( 1.0,  1.0,  0.0),
                ( 1.0,  0.0,  0.0),
                (-1.0,  0.0,  0.0),
                (-1.0,  1.0,  0.0),
                # Down Face
                ( 1.0,  1.0,  -0.5),
                ( 1.0,  0.0,  -0.5),
                (-1.0,  0.0,  -0.5),
                (-1.0,  1.0,  -0.5),
                ]

        edges = []

        faces = [
                [0, 3, 2, 1],
                [4, 5, 6, 7],
                [1, 2, 6, 5],
                [2, 3, 7, 6],
                [3, 0, 4, 7],
                [0, 1, 5, 4]
                ]

        mesh.from_pydata(verts, edges, faces)

        return obj


def create_treadmill_group(collection):
    # Creates an empty and puts it inside the treadmill collection correctly
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    treadmill_group = bpy.context.object
    bpy.context.collection.objects.unlink(treadmill_group)
    treadmill_group.name = 'Treadmill Mover'
    collection.objects.link(treadmill_group)

    return treadmill_group


def draw_panel(self, context):
    if not bpy.data.actions.items():
        return

    treadmill_configs = context.scene.treadmill_configs
    obj = context.object
    treadmill_col = context.scene.collection.children.get('Treadmill')

    if obj is None:
        return

    layout = self.layout
    layout.separator()
    box = layout.box()
    row = box.row(align=True)

    active_action = obj.animation_data.action if obj.animation_data else None
    treadmill = active_action.get('HasTreadmill')

    row.label(text='Treadmill Tool', icon='MOD_ARRAY')
    if not treadmill:
        row.operator('bitcake.treadmill', icon='ADD', text="")

    else:
        row = row.row()
        if treadmill_col:
            row.prop(treadmill_col, 'hide_viewport', icon='HIDE_OFF', text="")
        row.operator('bitcake.remove_treadmill', icon='REMOVE', text="")

    if not treadmill:
        return

    print(f'{treadmill_configs.steps_number}')
    row = box.row()
    row.prop(treadmill_configs, 'steps_number')
    row = box.row()
    row.prop(treadmill_configs, 'steps_spacing')
    row = box.row()
    row.prop(treadmill_configs, 'steps_offset')
    row = box.row()
    row.prop(treadmill_configs, 'treadmill_speed')

    bpy.ops.outliner.orphans_purge()

    return


classes = (BITCAKE_OT_treadmill,
           BITCAKE_PROPS_treadmill_configs,
           BITCAKE_OT_remove_treadmill
           )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.treadmill_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_treadmill_configs)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.treadmill_configs