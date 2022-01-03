import bpy
from bpy.types import Operator

class BITCAKE_OT_shape_keys_to_custom_props(Operator):
    bl_idname = "bitcake.shape_keys_to_custom_props"
    bl_label = "Shape Keys to Custom Properties"
    bl_description = "Transform all mesh Shape Keys into Custom Properties so animations work in the Action Editor and the Game Engine can pick them up.\n\nMesh with Shape Keys only"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object.type == 'MESH' and context.object.data.shape_keys is not None

    def execute(self, context):
        scene = context.scene
        ctx_object = context.object
        shape_keys = ctx_object.data.shape_keys

        frame = scene.frame_start
        scene.frame_set(frame)

        for key, keyblock in shape_keys.key_blocks.items():
            if keyblock == shape_keys.key_blocks[0]:
                continue

            # create a custom property for the key and update its values
            ctx_object[key] = keyblock.value
            id_props = ctx_object.id_properties_ui(key)
            id_props.update(min=keyblock.slider_min,
                            max=keyblock.slider_max,
                            description="Shape Key %s" % key,
                            soft_min=keyblock.slider_min,
                            soft_max=keyblock.slider_max,
                            )

            # add a driver
            fcurve = shape_keys.driver_add('key_blocks["%s"].value' % key)
            driver = fcurve.driver
            driver.type = 'SCRIPTED'
            driver.expression = "shape"
            var = driver.variables.new()
            var.name = "shape"
            var.type = 'SINGLE_PROP'
            target = var.targets[0]
            target.id_type = "OBJECT"
            target.id = ctx_object.id_data
            target.data_path = '["%s"]' % key

        return {'FINISHED'}


class BITCAKE_OT_set_deform_bones(Operator):
    bl_idname = "bitcake.set_deform_bones"
    bl_label = "Set Deform Bones"
    bl_description = "Correctly sets the Deform property on bones prefixed with DEF- and unchecks it on all others.\n\nArmature Only"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object.type == 'ARMATURE'

    def execute(self, context):
        for bone in context.object.data.bones:
            split_name = bone.name.split('-')
            if split_name[0] == 'DEF':
                bone.use_deform = True
            else:
                bone.use_deform = False

        return {'FINISHED'}


classes = (BITCAKE_OT_shape_keys_to_custom_props,
           BITCAKE_OT_set_deform_bones,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
