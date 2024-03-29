import bpy
from bpy.types import Operator, PropertyGroup, Scene
from bpy.props import IntProperty, FloatProperty

class BITCAKE_PROPS_lod_configs(PropertyGroup):
    lod_number: IntProperty(name='Number of LODs', default=2, min=0, max=10)

class BITCAKE_OT_lod_maker(Operator):
    bl_idname = "bitcake.lod_maker"
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
        scene_data = bpy.data.objects

        for obj in selection:
            if not obj.get('LOD'):
                obj['LOD'] = 0

            for child_obj in obj.children_recursive:
                if child_obj.get('LOD') is not None:
                    if child_obj.get('LOD') > 0:
                        scene_data.remove(child_obj)

                        if child_obj in selection:
                            selection.remove(child_obj)

        for obj in selection:
            for lod in range(self.lod_number):
                if obj.get('LOD') != 0:
                    continue

                obj_copy = duplicate(obj)
                current_lod = lod + 1

                is_lod = obj_copy.get('LOD')
                if not is_lod:
                    obj_copy['LOD'] = current_lod

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

    if obj.parent is None:
        obj_copy.matrix_parent_inverse = obj.matrix_world.inverted()
    else:
        obj_copy.matrix_world = obj.parent.matrix_world


    for collection in obj.users_collection:
        collection.objects.link(obj_copy)

    return obj_copy


def draw_panel(self, context):
    lod_configs = context.scene.lod_configs

    layout = self.layout

    row = layout.row()
    row.prop(lod_configs, 'lod_number')
    row = layout.row()
    op = row.operator('bitcake.lod_maker', text='Generate LODs')
    op.lod_number = lod_configs.lod_number

    layout.separator()
    obj = context.active_object
    selection = context.selected_objects

    if obj is None:
        return


    displayed_objs = []
    for obj in selection:
        if obj.get('LOD') is not None:
            if obj.get('LOD') > 0 or obj.parent is not None:
                continue
            row = layout.row()
            row.label(text=f'{obj.name} LODs Ratio')

        for child in obj.children_recursive:
            mod = child.modifiers.get('Decimate')
            if mod is not None and child not in displayed_objs:
                row = layout.row()
                row.prop(mod, 'ratio', text=f"{child.name}")
                displayed_objs.append(child)

    return


classes = (BITCAKE_OT_lod_maker,
           BITCAKE_PROPS_lod_configs)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.lod_configs = bpy.props.PointerProperty(type=BITCAKE_PROPS_lod_configs)



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.lod_configs
