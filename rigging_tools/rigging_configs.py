import bpy
from bpy.types import PropertyGroup, Scene
from bpy.props import BoolProperty, StringProperty

class BITCAKE_PROPS_rigging_configs(PropertyGroup):
    left_to_right: BoolProperty(name="Left to Right", description="Mirror Left to Right", default=True)
    mirror_middle: BoolProperty(name="Mirror Middle Bones", description="Should the operator work on Bones that are located in the 0 axis?", default=False)

    # Prefixes Setup (user changeable)
    separator: StringProperty(name='Separator', default='.')
    left_side: StringProperty(name='Left Side', default='l')
    middle: StringProperty(name='Middle', default='x')
    right_side: StringProperty(name='Right Side', default='r')


classes = (BITCAKE_PROPS_rigging_configs,)

preview_collections = {}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.rigging_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_rigging_configs)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.rigging_configs
