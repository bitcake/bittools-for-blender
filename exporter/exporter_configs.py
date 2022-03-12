import bpy
from bpy.types import PropertyGroup, Scene
from bpy.props import BoolProperty

class BITCAKE_PROPS_exporter_configs(PropertyGroup):
    export_selected: BoolProperty(name="Selected", description="Only exports selected objects", default=False)
    export_collection: BoolProperty(name="Collection", description="Exports entire collection", default=False)
    export_batch: BoolProperty(name="Batch", description="Exports objects in a separate file", default=False)
    origin_transform: BoolProperty(name="Origin", description="Place objects in origin before exporting", default=False)
    apply_transform: BoolProperty(name="Apply", description="Apply transforms before exporting", default=False)
    export_nla_strips: BoolProperty(name="Export NLA Strips", description="Separate NLA Strips into their own animations when exporting.\nYou'll usually want this turned OFF for Game Engine", default=False)


classes = (BITCAKE_PROPS_exporter_configs,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.exporter_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_exporter_configs)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.exporter_configs