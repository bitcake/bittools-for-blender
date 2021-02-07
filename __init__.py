import sys
import importlib


bl_info = {
    "name": "BitCake Tools",
    "author": "Eduardo Lamhut @elamhut",
    "version": (0, 0, 1),
    "blender": (2, 91, 0),
    "location": "3D View > Sidebar > Misc tab",
    "description": "bitcake.studio tools to improve 3D workflow in a game development studio environment",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object",
}


modulesNames = ['AddonConfigs', 'HotkeyChanger', 'HotkeyChooser', 'SideMenu']


modulesFullNames = []

for currentModuleName in modulesNames:
    positionInList = modulesNames.index(currentModuleName)
    modulesFullNames.append('{}.{}'.format(__name__, currentModuleName))

for currentModuleFullName in modulesFullNames:
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(
            currentModuleFullName)
        setattr(globals()[currentModuleFullName],
                'modulesNames', modulesFullNames)


def register():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()


def unregister():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()


if __name__ == "__main__":
    register()
