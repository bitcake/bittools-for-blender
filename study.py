import bpy

action = bpy.data.actions
i = 0
for animations in action:
    for fcurves in action[i].fcurves:
        print(fcurves.data_path + " channel " + str(fcurves.array_index))
        for keyframe in fcurves.keyframe_points:
            print(keyframe.co) #coordinates x,y
    i += 1

# Primeiro checa se os objetos selecionados possuem animation_data
# animated_objects = []
# for anim in bpy.context.selected_objects:
#     if anim.animation_data:
#         animated_objects.append(anim)
#         print(animated_objects)

# print("*"*40)

selected_bones = [b.name for b in bpy.context.selected_pose_bones]
selected_fcurves = []

for obj in bpy.context.selected_objects:
    if obj.animation_data:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path.split('"')[1] in selected_bones:
                selected_fcurves.append(fcurve)

print(selected_fcurves)


i = 0
for obj in bpy.context.selected_objects:
    for fcurve in obj.animation_data.action.fcurves.values():
        for keyframe in fcurve.keyframe_points:
            print(keyframe.co[0])


for obj in bpy.context.selected_objects:
    if obj is not None:
        for fcurve in obj.animation_data.action.fcurves.values():
            for keyframe in fcurve.keyframe_points:
                print(keyframe.co[0])

# bone_names_list = [b.name for b in selected_bones]
# fcurves = armature.animation_data.action.fcurves
# fcurves_selected = [f for f in fcurves if f.data_path.split('"')[1] in bone_names_list]