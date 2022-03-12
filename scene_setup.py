import bpy
from bpy.app.handlers import persistent
from .helpers import get_addon_prefs

@persistent
def scene_setup(scene):
    """Put any code that you want to run every time a Scene is loaded up here"""
    addon_prefs = get_addon_prefs()

    # Make sure Scene is being animated at 30, 60 or 120 FPS.
    bpy.context.scene.render.fps = addon_prefs.fps


def update_scene_fps(self, context):
    addon_prefs = get_addon_prefs()
    bpy.context.scene.render.fps = addon_prefs.fps


def register():
    bpy.app.handlers.load_pre.append(scene_setup)
    bpy.app.handlers.load_factory_startup_post.append(scene_setup)


def unregister():
    bpy.app.handlers.load_factory_startup_post.remove(scene_setup)