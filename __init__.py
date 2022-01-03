bl_info = {
    "name": "BitTools",
    "author": "Eduardo Lamhut",
    "version": (0, 0, 1),
    "blender": (3, 0, 0),
    "location": "3D View > Properties> Auto-Rig Pro",
    "description": "Automatic rig generation based on reference bones and various tools",
    "tracker_url": "www.bitcakestudio.com",
    "doc_url": "www.bitcakestudio.com",
    "category": "Animation",
}

from . import addon_prefs
from . import menu_side
from . import hotkey_manager
from . import anim_tools
from . import bitcake_exporter
from . import collider_tools
from . import scene_setup
from . import rigging_tools

def register():
    addon_prefs.register()
    menu_side.register()
    hotkey_manager.register()
    anim_tools.register()
    bitcake_exporter.register()
    collider_tools.register()
    scene_setup.register()
    rigging_tools.register()

def unregister():
    addon_prefs.unregister()
    menu_side.unregister()
    hotkey_manager.unregister()
    anim_tools.unregister()
    bitcake_exporter.unregister()
    collider_tools.unregister()
    scene_setup.unregister()
    rigging_tools.unregister()


# bpy.ops.bitcake.addon_prefs_setup('EXEC_DEFAULT')
