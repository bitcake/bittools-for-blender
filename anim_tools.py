import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator, PropertyGroup, Scene
from bpy.app.handlers import persistent

breakdowner_status = True


@persistent
def reset_breakdowner(self, context):
    boolean = bpy.context.scene.animtool_props
    boolean.bool_prop = False
    boolean.c += 1
    print("Chamou? {}".format(boolean.c))
    update_property_value(0.5)
    print("Foi agora?{}".format(boolean.c))
    boolean.c -= 1
    boolean.bool_prop = True

def update_breakdowner(self, context):
    properties = bpy.context.scene.animtool_props
    if properties.bool_prop:
        properties = context.scene.animtool_props
        print("Update Real {} c = {}".format(properties.breakdowner, properties.c))

def update_property_value(value):
    properties = bpy.context.scene.animtool_props
    properties.breakdowner = value


# bpy.ops.pose.breakdown(factor=self.breakdown_value, prev_frame=0, next_frame=30)
class AnimToolProperties(PropertyGroup):
        breakdowner: FloatProperty(
        name="Lean Percentage",
        description="Set breakdown value towards either the last frame or the next, in percentage",
        min=0.0, max=1.0,
        default=0.5,
        update=update_breakdowner,
        )

        bool_prop: BoolProperty(default=True)

        c: IntProperty()

class BITCAKE_OT_breakdowner(Operator):
    bl_idname = "bitcake.breakdowner"
    bl_label = "Breakdowner"
    bl_description = "Changes Breakdowner lean percentage value"
    # bl_options = {'INTERNAL'}

    breakdown_value: FloatProperty(name='Lean Percentage')

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'


    def execute(self, context):
        properties = context.scene.animtool_props
        properties.breakdowner = self.breakdown_value
        bpy.ops.pose.breakdown(factor=self.breakdown_value, prev_frame=0, next_frame=30)
        return {'FINISHED'}

bpy.app.handlers.frame_change_post.append(reset_breakdowner)

# bpy.msgbus.subscribe_rna(
#      key=(bpy.types.LayerObjects, "active"),
#      owner=object(),
#      args=tuple(),
#      notify=textTry,
# )

classes = (BITCAKE_OT_breakdowner, AnimToolProperties)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.animtool_props = bpy.props.PointerProperty(type=AnimToolProperties)



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.animtool_props
