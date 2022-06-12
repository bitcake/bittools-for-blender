import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ..helpers import clear_pose

# Most of this code comes from the amazing GRET plugin, check it out
# I have permission from the author to copy parts of her plugin :)

class BITCAKE_OT_actions_set(Operator):
    bl_idname = "bitcake.actions_set"
    bl_label = "Set Action"
    bl_options = {'INTERNAL', 'UNDO'}

    name: bpy.props.StringProperty(options={'HIDDEN'})
    new_name: bpy.props.StringProperty(name="New name", default="")
    play: bpy.props.BoolProperty(options={'HIDDEN'}, default=False)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'POSE' and context.object.animation_data

    def execute(self, context):
        obj = context.object
        if not self.name:
            obj.animation_data.action = None
            return {'FINISHED'}

        action = bpy.data.actions.get(self.name, None)
        if action:
            # Always save it, just in case
            action.use_fake_user = True

            if self.new_name:
                # Rename
                action.name = self.new_name
            elif not self.play and obj.animation_data.action == action:
                # Action was already active, stop editing
                obj.animation_data.action = None
            else:
                clear_pose(obj)
                obj.animation_data.action = action

                # Set preview range. Use start and end markers if they exist
                if action.use_frame_range:
                    context.scene.frame_preview_start = int(action.frame_start)
                    context.scene.frame_preview_end = int(action.frame_end)
                else:
                    context.scene.frame_preview_start = int(action.curve_frame_range[0])
                    context.scene.frame_preview_end = int(action.curve_frame_range[1])

                context.scene.use_preview_range = True

                if self.play:
                    context.scene.frame_current = int(action.curve_frame_range[0])
                    bpy.ops.screen.animation_cancel(restore_frame=False)
                    bpy.ops.screen.animation_play()

            treadmill_col = context.scene.collection.children.get('Treadmill')
            treadmill = action.get('HasTreadmill')

            if treadmill_col is not None and treadmill:
                treadmill_col.hide_viewport = False
            elif treadmill_col is not None and not treadmill:
                treadmill_col.hide_viewport = True

            temp_steps_number = action.get('steps_number')
            temp_steps_spacing = action.get('steps_spacing')
            temp_steps_offset = action.get('steps_offset')
            temp_treadmill_speed = action.get('treadmill_speed')

            treadmill_configs = context.scene.treadmill_configs

            if treadmill:
                if treadmill_configs.steps_number != temp_steps_number:
                    treadmill_configs.steps_number = temp_steps_number

                if treadmill_configs.steps_spacing != temp_steps_spacing:
                    treadmill_configs.steps_spacing = temp_steps_spacing

                if treadmill_configs.steps_offset != temp_steps_offset:
                    treadmill_configs.steps_offset = temp_steps_offset

                if treadmill_configs.treadmill_speed != temp_treadmill_speed:
                    treadmill_configs.treadmill_speed = temp_treadmill_speed

            elif treadmill == False:
                treadmill_configs.ui_lock = True
                treadmill_configs.steps_number = temp_steps_number
                treadmill_configs.steps_spacing = temp_steps_spacing
                treadmill_configs.steps_offset = temp_steps_offset
                treadmill_configs.treadmill_speed = temp_treadmill_speed
                treadmill_configs.ui_lock = False

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.ctrl:
            # Rename
            self.new_name = self.name
            return context.window_manager.invoke_props_dialog(self)
        else:
            self.new_name = ""
            return self.execute(context)


class BITCAKE_OT_action_add(Operator):
    """Add a new action"""

    bl_idname = 'bitcake.action_add'
    bl_label = "Add Action"
    bl_options = {'INTERNAL', 'UNDO'}

    name: bpy.props.StringProperty(default="New action")

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        obj = context.object

        if not obj.animation_data:
            obj.animation_data_create()
        new_action = bpy.data.actions.new(self.name)
        new_action.use_fake_user = True
        clear_pose(obj)
        obj.animation_data.action = new_action

        return {'FINISHED'}

class BITCAKE_OT_action_remove(Operator):
    """Delete the action"""

    bl_idname = 'bitcake.action_remove'
    bl_label = "Remove Action"
    bl_options = {'INTERNAL', 'UNDO'}

    name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object and context.object.animation_data

    def execute(self, context):
        obj = context.object
        action = bpy.data.actions.get(self.name, None)
        if not action:
            return {'CANCELLED'}

        bpy.data.actions.remove(action)

        return {'FINISHED'}

class BITCAKE_OT_action_duplicate(Operator):
    """Duplicate this action"""

    bl_idname = 'bitcake.action_duplicate'
    bl_label = "Duplicate Action"
    bl_options = {'INTERNAL', 'UNDO'}

    name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        obj = context.object
        action = bpy.data.actions.get(self.name, None)
        if not action:
            return {'CANCELLED'}

        new_action = action.copy()
        new_action.use_fake_user = True

        return {'FINISHED'}


class BITCAKE_OT_set_manual_frame_range(bpy.types.Operator):
    #tooltip - Made an operator so it doesn't light up on the panel due to boolean
    """Set Manual Frame Range for Action"""

    bl_idname = 'bitcake.set_manual_frame_range'
    bl_label = "Set Manual Frame Range"
    bl_options = {'INTERNAL', 'UNDO'}

    name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        obj = context.object
        action = bpy.data.actions.get(self.name, None)
        if not action:
            return {'CANCELLED'}

        action.use_frame_range = not action.use_frame_range

        return {'FINISHED'}


def get_unlinked_action_list():
    action_list = []
    for action in bpy.data.actions:
        if action.library:
            continue
        else:
            action_list.append(action)

    return action_list


def draw_panel(self, context):
    if not bpy.data.actions.items():
        return

    obj = context.object
    layout = self.layout
    box = layout.box()
    row = box.row(align=True)

    row.label(text='Available Actions', icon='NLA')
    row.operator('bitcake.action_add', icon='ADD', text="")

    col = box.column(align=True)

    if obj is None:
        return

    active_action = obj.animation_data.action if obj.animation_data else None
    if active_action is None:
        row = box.row()
        row.alert = True
        row.label(text='Select a valid Object with an Action')
        return

    for action in get_unlinked_action_list():
        row = col.row(align=True)
        selected = action == active_action

        if selected and context.screen.is_animation_playing:
            op = row.operator('screen.animation_cancel', icon='PAUSE', text='', emboss=False)
            op.restore_frame = False
        else:
            icon = 'PLAY' if action == active_action else 'TRIA_RIGHT'
            op = row.operator('bitcake.actions_set', icon=icon, text='', emboss=False)
            op.name = action.name
            op.play = True

        op = row.operator('bitcake.actions_set', text=action.name)
        op.name = action.name
        op.play = False

        if action.use_frame_range:
            range_icon = 'KEYFRAME_HLT'
        else:
            range_icon = 'KEYFRAME'

        row.operator('bitcake.set_manual_frame_range', icon=range_icon, text="").name = action.name
        row.operator('bitcake.action_duplicate', icon='DUPLICATE', text='').name = action.name
        row.operator('bitcake.action_remove', icon='TRASH', text='').name = action.name

    if active_action and active_action.use_frame_range:
        row = layout.row(align=True)
        row.prop(active_action, 'frame_start')
        row.prop(active_action, 'frame_end')
        row.prop(active_action, 'use_cyclic', icon='FILE_REFRESH', text="")

classes = (BITCAKE_OT_actions_set,
           BITCAKE_OT_action_add,
           BITCAKE_OT_action_duplicate,
           BITCAKE_OT_action_remove,
           BITCAKE_OT_set_manual_frame_range,
           )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
