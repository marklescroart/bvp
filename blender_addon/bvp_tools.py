import bpy

bl_info = dict(
	name='Next Scene',
	category='Scene',
	author='Mark Lescroart'
	created='2014.07.06'
	)

class NextScene(bpy.types.operator):
	"""Skip to the next scene"""
	bl_idname = "scene.next"
	bl_label = "Skip to next scene"
	bl_options = {'REGISTER','UNDO'}
	
	def execute(self,context):
		ScnList = list(bpy.data.scenes)
		ScnIdx = ScnList.index(context.scene)
		if ScnIdx<len(ScnList)-1:
			context.screen.scene = ScnList[ScnIdx+1]
		return {"FINISHED"}

def register():
	bpy.utils.register_class(NextScene)

def unregister():
	bpy.utils.unregister_class(NextScene)

if __name__=="__main__":
	register()