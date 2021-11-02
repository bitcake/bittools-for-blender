import bpy

def translate(v):
    bpy.ops.transform.translate(value=v, constraint_axis=(True, True, True))

def location(v):
    bpy.context.object.location = v

def scale(objName, v):
    bpy.data.objects[objName].scale = v