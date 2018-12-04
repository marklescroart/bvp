import bvp
import bpy

for scn in bpy.data.scenes:
	bvp.utils.blender.set_scene(scn.name)
	for o in scn.objects:
		bvp.utils.blender.grab_only(o)
		try:
			bpy.ops.object.transform_apply(scale=True)
		except:
			print("Failed for object %s"%o.name)

bpy.ops.wm.save_as_mainfile(f)
