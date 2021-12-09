# Get Addon Preferences
addonPrefs = context.preferences.addons[__package__].preferences
# Active Object Collection
bpy.context.active_object.users_collection[0].name
# Get Master Collection
bpy.context.collection
# Change currenct active object
bpy.context.view_layer.objects.active = ob
# Get a Specific Object in scene via name
bpy.data.objects['Sphere.017']