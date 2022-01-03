import bpy
import blf
import time
from bpy import context
from bpy.types import Operator


class BITCAKE_OT_hotkeychanger(Operator):
    import sys
    import pathlib

    bl_idname = "bitcake.hotkeychanger"
    bl_label = ""
    bl_description = "Change your current Hotkeys to Blender's default and back. (This will save your current Custom Hotkeys)"

    # Find Python's Path inside Blender Install
    pure = pathlib.PurePath(sys.executable)
    # Go down to the version directory
    pure = pure.parents[2]
    # Get Blender's Default Keymap
    default_keymap_path = "scripts/presets/keyconfig/Blender.py"
    default_keymap_path = str(pathlib.PurePath(pure, default_keymap_path))

    addonDir = bpy.utils.user_resource('SCRIPTS')
    custom_keymap_dir = addonDir + "\\addons\\BitCakeTools\\custom_keymap.py"

    def toggledefaulthotkey(self, context):
        addonPrefs = context.preferences.addons[__package__].preferences
        scene = context.scene
        mytool = scene.my_tool

        if addonPrefs.isDefaultKeymaps:
            bpy.ops.preferences.keyconfig_import(filepath=self.custom_keymap_dir)
            bpy.ops.preferences.keyconfig_activate(filepath=self.custom_keymap_dir)
            addonPrefs.isDefaultKeymaps = False
            bpy.ops.wm.save_userpref()
        else:
            bpy.ops.preferences.keyconfig_export(filepath=self.custom_keymap_dir)
            bpy.ops.preferences.keyconfig_activate(filepath=self.default_keymap_path)
            addonPrefs.isDefaultKeymaps = True
            bpy.ops.wm.save_userpref()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.area.type == 'VIEW_3D'

    def execute(self, context):
        self.toggledefaulthotkey(context)

        context.area.tag_redraw()
        return {'FINISHED'}


#####################################


def create_font(id, size):
    blf.size(id, size, 72)

def draw_text(text, x, y, font_id):
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)

class Draw_Input:
    def __init__(self):
        self.key = ''
        self.timestamp = time.time()

    def input(self, event):
        self.key = event.type
        self.timestamp = time.time()

    def __str__(self):
        result = []

        if(self.key != ''):
            result.append(self.key)

        if(len(result) > 0):
            return ' | '.join(result)

        return ''


class DRAW_OT_view(Operator):
    bl_idname = "bitcake.draw_input"
    bl_label = "Draw Input"
    bl_description = "This will draw your input in the Viewport"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def __init(self):
        self.draw_handle = None
        self.draw_event = None

    def invoke(self, context, event):
        args = (self, context)

        self.key_input = Draw_Input()

        if(context.window_manager.BUTTON_pressed is False):
            context.window_manager.BUTTON_pressed = True

            self.register_handlers(args, context)

            context.window_manager.modal_handler_add(self)
            return("RUNNING_MODAL")
        else:
            context.window_manager.BUTTON_pressed = False
            return("CANCELLED")

    def register_handlers(self, args, context):
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, "WINDOW", "POST_PIXEL")
        self.draw_event = context.window_manager.event_timer_add(0.1, context.window)

    def unregister_handlers(self, context):
        context.window_manager.event_timer_remove(self.draw_event)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")

        self.draw_handle = None
        self.draw_event = None

    def modal(self, context, event):
        context.area.tag_redraw()

        self.detect_keyboard(event)

        if not context.window_manager.BUTTON_pressed:
            self.unregister_handlers(context)

            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def detect_keyboard(self, event):
        if(event.value == 'PRESS'):
            self.key_input(event)

    def cancel(self, context):
        if context.window_manager.BUTTON_pressed:
            self.unregister_handlers(context)
            return {"CANCELLED"}

    def finish(self):
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_px(tmp, self, context):
        region = context.region
        current_time = time.time()
        time_diff_keys = current_time - self.key_input.timestamp

        if(time_diff_keys < 4.0):
            xt = int(region.width / 2.0)
            font_id = 0
            create_font(font_id,30)
            text = str(self.key_input)
            draw_text(text, 40, 30, font_id)

classes = (BITCAKE_OT_hotkeychanger, DRAW_OT_view)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)