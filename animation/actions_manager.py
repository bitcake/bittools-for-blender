import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ..helpers import clear_pose

# Most of this code comes from the amazing GRET plugin, check it out
# I swear I type everything myself so I could learn, tho :P
# I also have permission from the author to copy parts of her plugin :)

class BITCAKE_OT_actions_set(Operator):
    bl_idname = "bitcake.actions_set"
    bl_label = "Set Action"
    bl_options = {'INTERNAL', 'UNDO'}

    new_name: StringProperty(name='New Name', default='')
    action_name: StringProperty(default='', options={'HIDDEN'})
    play: BoolProperty(default=False, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' or context.mode == 'POSE' and context.object.animation_data

    def execute(self, context):
        obj = context.object

        if not self.action_name:
            obj.animation_data.action = None
            return {'FINISHED'}

        action = bpy.data.actions.get(self.action_name)
        if action:
            action.use_fake_user = True

            if self.new_name:
                action.name = self.new_name
            elif not self.play and obj.animation_data.action == action:
                obj.animation_data.action = None
                bpy.ops.screen.animation_cancel(restore_frame=False)
            else:
                clear_pose(obj)
                obj.animation_data.action = action

                context.scene.frame_preview_start = action.frame_range[0]
                context.scene.frame_preview_end = action.frame_range[1]

                for marker in action.pose_markers:
                    if marker.name.lower() == "start":
                        context.scene.frame_preview_start = marker.frame
                    elif marker.name.lower() == "end":
                        context.scene.frame_preview_end = marker.frame

                context.scene.use_preview_range = True

            if self.play:
                context.scene.frame_current = action.frame_range[0]
                bpy.ops.screen.animation_cancel(restore_frame=False)
                bpy.ops.screen.animation_play()

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.ctrl:
            # Rename
            self.new_name = self.action_name
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
        actions_row = col.row(align=True)
        selected = action == active_action

        if selected and context.screen.is_animation_playing:
            op = actions_row.operator('screen.animation_cancel', icon='PAUSE', text='', emboss=False)
            op.restore_frame = False
        else:
            icon = 'PLAY' if action == active_action else 'TRIA_RIGHT'
            op = actions_row.operator('bitcake.actions_set', icon=icon, text='', emboss=False)
            op.action_name = action.name
            op.play = True

        op = actions_row.operator('bitcake.actions_set', text=action.name)
        op.action_name = action.name
        op.play = False

        actions_row.operator('bitcake.action_duplicate', icon='DUPLICATE', text='').name = action.name
        actions_row.operator('bitcake.action_remove', icon='TRASH', text='').name = action.name


classes = (BITCAKE_OT_actions_set,
           BITCAKE_OT_action_add,
           BITCAKE_OT_action_duplicate,
           BITCAKE_OT_action_remove,
           )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
