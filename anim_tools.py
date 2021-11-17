import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from bpy.types import Operator, PropertyGroup, Scene
from bpy.app.handlers import frame_change_post
from bpy.app import driver_namespace


# This here below is so that the Handler frame_change_post do not end up with
# many version of the same function runing inside it. If this is not here
# every time you save and update the scene, a new handler will be added and various
# versions of the same function will be playing when the callback is called
# Just print out the list frame_change_post to check if everything is correct

breakdowner_handler_key = 'BREAKDOWNER_HANDLER'

if breakdowner_handler_key in driver_namespace:
    if driver_namespace[breakdowner_handler_key] in frame_change_post:
        frame_change_post.remove(driver_namespace[breakdowner_handler_key])
    del driver_namespace[breakdowner_handler_key]


def reset_breakdowner(self, context):
    animtool_props = bpy.context.scene.animtool_props
    animtool_props.breakdowner_bool = False
    update_property_value(0.5)
    animtool_props.breakdowner_bool = True

def update_breakdowner(self, context):
    animtool_props = bpy.context.scene.animtool_props
    if animtool_props.breakdowner_bool:
        animtool_props = context.scene.animtool_props
        selected_bones_fcurves = get_fcurves_from_selected_bones()
        nearest_frames = get_nearest_frames_from_current_frame(selected_bones_fcurves)
        if nearest_frames[0] == None or nearest_frames[1] == None:
            return
        bpy.ops.pose.breakdown(factor=animtool_props.breakdowner, prev_frame=nearest_frames[0], next_frame=nearest_frames[1])

def update_property_value(value):
    animtool_props = bpy.context.scene.animtool_props
    animtool_props.breakdowner = value

def get_fcurves_from_selected_bones():
    selected_bones = [b.name for b in bpy.context.selected_pose_bones]
    selected_fcurves = []

    for obj in bpy.context.selected_objects:
        # Check if selected object is animated (check for null)
        if obj.animation_data:
            for fcurve in obj.animation_data.action.fcurves:
                # Check the name of the bone that owns that fcurve. If it's inside
                # the selected_bones list, add the fcurve to the selected_fcurves list
                if fcurve.data_path.split('"')[1] in selected_bones:
                    selected_fcurves.append(fcurve)

    return selected_fcurves

def get_nearest_frames_from_current_frame(fcurves):
    min = None
    max = None
    for fcurve in fcurves:
        for keyframes in fcurve.keyframe_points.values():
            check = keyframes.co[0] - bpy.context.scene.frame_current

            if min == None and check < 0:
                min = keyframes.co[0]
            if check < 0 and keyframes.co[0] >= min:
                min = keyframes.co[0]

            if max == None and check > 0:
                max = keyframes.co[0]
            if check > 0 and keyframes.co[0] <= max:
                max = keyframes.co[0]

    return (min, max)


frame_change_post.append(reset_breakdowner)
driver_namespace[breakdowner_handler_key] = reset_breakdowner

class AnimToolProperties(PropertyGroup):
        breakdowner: FloatProperty(
        name="Lean Percentage",
        description="Set breakdown value towards either the last frame or the next, in percentage",
        min=0.0, max=1.0,
        default=0.5,
        update=update_breakdowner,
        )

        breakdowner_bool: BoolProperty(default=True)

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
        # This execute method just changes the value of the float. The float itself then calls
        # its update function to run the breakdowner code.
        properties = context.scene.animtool_props
        properties.breakdowner = self.breakdown_value
        return {'FINISHED'}


# Keyframes live in fcurves and each fcurve has a bunch of keyframe_points
# You can iterate fcurves's keyframe_points to find all keyframes in that curve
# Keep in mind each object might have a lot of fcurves, for instance each Translation axis
# is an fcurve, so there's 3 FCurves there + Quaternion + Scale + Custom Attrs.
# Here is an example on how to acess a specific keyframe inside an FCurve:
# bpy.data.actions[1].fcurves[1].keyframe_points[0].co
# Function to iterate over fcurves and find all keyframe on all channels:

# action = bpy.data.actions[0]
# for fcu in action.fcurves:
#     print(fcu.data_path + " channel " + str(fcu.array_index))
#     for keyframe in fcu.keyframe_points:
#         print(keyframe.co) #coordinates x,y



classes = (BITCAKE_OT_breakdowner, AnimToolProperties)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.animtool_props = bpy.props.PointerProperty(type=AnimToolProperties)



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.animtool_props
