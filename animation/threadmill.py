import bpy
from bpy.types import Operator, PropertyGroup, Scene
from bpy.props import IntProperty, BoolProperty, StringProperty, FloatProperty
from ..helpers import delete_hierarchy

def recreate_threadmill():
    bpy.ops.bitcake.threadmill

    return

class BITCAKE_PROPS_threadmill_configs(PropertyGroup):
     steps_number: IntProperty(name='Number of Steps', default=20, min=0)
     steps_spacing: FloatProperty(name='Steps Spacing', default=2, min=1)
     steps_offset: FloatProperty(name='Steps Offset', default=0)
     threadmill_speed: FloatProperty(name='Threadmill Speed (m/s)', default=2, min=0)


class BITCAKE_OT_threadmill(Operator):
    bl_idname = "bitcake.threadmill"
    bl_label = "Threadmill Tool"
    bl_options = {'INTERNAL', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'POSE'

    def execute(self, context):
        threadmill_configs = context.scene.threadmill_configs
        steps_number = threadmill_configs.steps_number
        steps_spacing = threadmill_configs.steps_spacing
        steps_offset = threadmill_configs.steps_offset
        threadmill_speed = threadmill_configs.threadmill_speed

        col = create_threadmill_collection()

        threadmill_group = col.objects.get('Threadmill Mover')
        if threadmill_group:
            delete_hierarchy(threadmill_group.name)
            bpy.ops.object.delete({'selected_objects': [threadmill_group]})

        steps_list = []
        for num, steps in enumerate(range(steps_number)):
            step = create_threadmill_step(col)
            move_amount = (steps_number - 1) * steps_spacing / 2 + steps_offset
            bpy.ops.transform.translate({'selected_objects': [step]}, value=(0, -move_amount + (num*steps_spacing), 0))
            steps_list.append(step)

        threadmill_group = create_threadmill_group(col)

        for steps in steps_list:
            steps.parent = threadmill_group

        threadmill_group.animation_data_create()
        threadmill_action = bpy.data.actions.get('Threadmill')
        if threadmill_action:
            threadmill_group.animation_data.action = threadmill_action

        threadmill_group.keyframe_insert(data_path="location", frame=1)
        threadmill_group.location = (0, threadmill_speed, 0)
        threadmill_group.keyframe_insert(data_path="location", frame=bpy.context.scene.render.fps)
        threadmill_group.location = (0, 0, 0)
        threadmill_group.animation_data.action.name = "Threadmill"

        # Edit only Translation Y curve
        fcurve = threadmill_group.animation_data.action.fcurves[1]
        fcurve.extrapolation = 'LINEAR'
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'

        bpy.context.view_layer.objects.active = threadmill_group

        return {'FINISHED'}


def create_threadmill_collection():
    threadmill_col = bpy.context.scene.collection.children.get('Threadmill')
    if threadmill_col:
        return threadmill_col

    threadmill_col = bpy.context.blend_data.collections.new(name='Threadmill')
    bpy.context.scene.collection.children.link(threadmill_col)

    return threadmill_col

def create_threadmill_step(collection):
        mesh = bpy.data.meshes.new("threadmill_step")
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


def create_threadmill_group(collection):
    # Creates an empty and puts it inside the Threadmill collection correctly
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    threadmill_group = bpy.context.object
    bpy.context.collection.objects.unlink(threadmill_group)
    threadmill_group.name = 'Threadmill Mover'
    collection.objects.link(threadmill_group)

    return threadmill_group


def draw_panel(self, context):
    threadmill_configs = context.scene.threadmill_configs
    layout = self.layout

    layout.separator()
    layout.label(text='Threadmill Tool')
    box = layout.box()
    row = box.row()
    row.prop(threadmill_configs, 'steps_number')
    row = box.row()
    row.prop(threadmill_configs, 'steps_spacing')
    row = box.row()
    row.prop(threadmill_configs, 'steps_offset')
    row = box.row()
    row.prop(threadmill_configs, 'threadmill_speed')
    row = layout.row()
    row.operator('bitcake.threadmill', text="Create Threadmill")


classes = (BITCAKE_OT_threadmill,
           BITCAKE_PROPS_threadmill_configs
           )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.threadmill_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_threadmill_configs)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.threadmill_configs