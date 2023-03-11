import bpy
from bpy.types import Operator, PropertyGroup, Scene
from bpy.props import IntProperty, FloatProperty

class BITCAKE_PROPS_lod_configs(PropertyGroup):
    lod_number: IntProperty(name='Number of LODs', default=2, min=0, max=10)

class BITCAKE_OT_dev_operator(Operator):
    bl_idname = "bitcake.dev_operator"
    bl_label = "Test Stuff"
    bl_description = "Test stuuuuff"
    bl_options = {'INTERNAL', 'UNDO'}

    lod_number: IntProperty(default=0)
    lod_ratio: FloatProperty(default=1)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.active_object
        selection = context.selected_objects

        for obj in selection:
            if not obj.get('LOD'):
                obj['LOD'] = 0

        scene_data = bpy.data.objects
        for child in obj.children_recursive:
            if child.get('LOD'):
                scene_data.remove(child)

        for lod in range(self.lod_number):
            if obj.get('LOD') is not 0:
                continue

            obj_copy = duplicate(obj)
            current_lod = lod + 1

            is_lod = obj_copy.get('LOD')
            if not is_lod:
                obj_copy['LOD'] = current_lod

            print(obj_copy.name)
            obj_name = obj_copy.name.split('.')
            obj_copy.name = obj_name[0] + '_LOD' + str(current_lod)

            decimate = obj_copy.modifiers.get('Decimate')
            if not decimate:
                decimate = obj_copy.modifiers.new('Decimate', 'DECIMATE')

            self.lod_ratio = self.lod_ratio / 2
            decimate.ratio = self.lod_ratio

        self.lod_ratio = 1


        return {'FINISHED'}


def duplicate(obj, data=True, actions=True, parent=True):
    obj_copy = obj.copy()
    if data:
        obj_copy.data = obj_copy.data.copy()
    if actions and obj_copy.animation_data:
        obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
    if parent:
        obj_copy.parent = obj

    obj_copy.matrix_parent_inverse = obj.matrix_world.inverted()

    for collection in obj.users_collection:
        collection.objects.link(obj_copy)

    return obj_copy


def draw_panel(self, context):
    lod_configs = context.scene.lod_configs

    layout = self.layout

    row = layout.row()
    row.prop(lod_configs, 'lod_number')
    row = layout.row()
    op = row.operator('bitcake.dev_operator', text='Generate LODs')
    op.lod_number = lod_configs.lod_number

    layout.separator()
    obj = context.active_object

    if obj is None:
        return

    mod = obj.modifiers.get('Decimate')
    if mod is not None:
        row = layout.row()
        row.prop(mod, 'ratio', text=f"LOD{str(obj.get('LOD'))}")

    for child in obj.children_recursive:
        mod = child.modifiers.get('Decimate')
        if mod is not None:
            row = layout.row()
            row.prop(mod, 'ratio', text=f"LOD{str(child.get('LOD'))}")

    return


classes = (BITCAKE_OT_dev_operator,
           BITCAKE_PROPS_lod_configs)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.lod_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_lod_configs)



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.lod_configs
