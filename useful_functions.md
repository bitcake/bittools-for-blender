### Get Addon Preferences
addonPrefs = context.preferences.addons[__package__].preferences
### Active Object Collection
bpy.context.active_object.users_collection[0].name
### Get Master Collection
bpy.context.collection
### Change currenct active object
bpy.context.view_layer.objects.active = ob
### Get a Specific Object in scene via name
bpy.data.objects['Sphere.017']
### Map a bounding box float array to vectors
list(map(Vector, C.active_object.bound_box))
### Deselect Everything
bpy.ops.object.select_all(action='DESELECT')

-----------

If the child object moves after setting the parent, use the following to move it back:

### After both parent and child have been link()ed to the scene:
```python
childObject.parent = parentObject
childObject.matrix_parent_inverse = parentObject.matrix_world.inverted()
```
### To unparent and keep the child object location (without using operators):
```python
parented_wm = childObject.matrix_world.copy()
childObject.parent = None
childObject.matrix_world = parented_wm
```
As mentioned in the comments, the matrices need to be up to date, which can be done with:
`bpy.context.scene.update()`
