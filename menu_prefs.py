from bpy.types import AddonPreferences
from bpy.props import BoolProperty


class BitCakeToolsPreferences(AddonPreferences):
    bl_idname = __package__

    isDefaultKeymaps: BoolProperty(
        name="Using Blender Default Keymaps",
        default=False,
    )


    def draw(self, context):
        layout = self.layout
        layout.label(text="This is a preferences view for our add-on")
        layout.prop(self, "isDefaultKeymaps")

classes = (BitCakeToolsPreferences,)

# Registration
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
