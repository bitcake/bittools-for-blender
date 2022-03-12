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

import importlib
import sys

def import_or_reload_modules(module_names, package_name):
    ensure_starts_with = lambda s, prefix: s if s.startswith(prefix) else prefix + s
    module_names = [ensure_starts_with(name, f'{package_name}.') for name in module_names]
    modules = []
    for module_name in module_names:
        module = sys.modules.get(module_name)
        if module:
            module = importlib.reload(module)
        else:
            module = globals()[module_name] = importlib.import_module(module_name)
        modules.append(module)
    return modules


from . import addon_prefs
from . import menu_side
from . import bitcake_exporter
from . import collider_tools
from . import scene_setup
from . import rigging_tools

module_names = [
    'animation',
    'exporter',
]

modules = import_or_reload_modules(module_names, __name__)

def register():
    addon_prefs.register()
    menu_side.register()
    bitcake_exporter.register()
    collider_tools.register()
    scene_setup.register()
    rigging_tools.register()

    for module in modules:
        if hasattr(module, 'register'):
            module.register()

def unregister():
    addon_prefs.unregister()
    menu_side.unregister()
    bitcake_exporter.unregister()
    collider_tools.unregister()
    scene_setup.unregister()
    rigging_tools.unregister()

    for module in modules:
        if hasattr(module, 'unregister'):
            module.unregister()

# bpy.ops.bitcake.addon_prefs_setup('EXEC_DEFAULT')
