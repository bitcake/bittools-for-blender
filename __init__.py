bl_info = {
    "name": "BitTools",
    "author": "Eduardo Lamhut",
    "version": (0, 3, 8),
    "blender": (3, 0, 0),
    "location": "3D View > Properties > BitTools",
    "description": "Toolset to help BitCake Artists work with various engines",
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
from . import scene_setup

module_names = [
    'animation',
    'custom_commands',
    'collider_tools',
    'exporter',
    'lod_tools',
    'rigging_tools',
    'dev_tools',
]

modules = import_or_reload_modules(module_names, __name__)

def register():
    addon_prefs.register()
    scene_setup.register()

    for module in modules:
        if hasattr(module, 'register'):
            module.register()

def unregister():
    addon_prefs.unregister()
    scene_setup.unregister()

    for module in modules:
        if hasattr(module, 'unregister'):
            module.unregister()
