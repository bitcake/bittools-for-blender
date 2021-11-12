bl_info = {
    "name": "bitcake.studio Blender Tools",
    "author": "Eduardo Lamhut",
    "version": (0, 0, 1),
    "blender": (2, 93, 0),
    "location": "3D View > Properties> Auto-Rig Pro",
    "description": "Automatic rig generation based on reference bones and various tools",
    "tracker_url": "www.bitcakestudio.com",
    "doc_url": "www.bitcakestudio.com",
    "category": "Animation",
}

from . import menu_prefs
from . import menu_side
from . import hotkey_manager
from . import anim_tools


def register():
    menu_prefs.register()
    menu_side.register()
    hotkey_manager.register()
    anim_tools.register()


def unregister():
    menu_prefs.unregister()
    menu_side.unregister()
    hotkey_manager.unregister()
    anim_tools.unregister()


# bpy.ops.bitcake.addon_prefs_setup('EXEC_DEFAULT')
