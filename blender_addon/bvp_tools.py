'''
Copyright (C) 2014 Mark Lescroart
mark.lescroart@berkeley.edu

Created by Mark Lescroart

< SHOULD THIS BE BERKELEY LICENSE?? > 

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy

# see http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Guidelines/Addons
bl_info = {
    "name":        "BVP tools",
    "description": "Tools to help with B.lender V.ision P.roject stimulus creation",
    "author":      "Mark Lescroart",
    "version":     (0, 1, 0),
    "blender":     (2, 7, 0), # (2, 7, 1)?
    "location":    "View 3D > Tool Shelf",
    "warning":     "Alpha",
    "category":    "3D View" # ?? other ??
    # see: http://wiki.blender.org/index.php/Meta:Guides/Writer_Guide
    "wiki_url":    "<docs page on github?>" 
    }

class bvp_tools_panel(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "3D View"
	bl_label = "BVP tools"
	bl_context = "objectmode"
	
	def draw(self, context):
		layout = self.layout
		
		col = layout.column(align = True)
		col.operator("camera_tools.add_rotating_camera")
		col.operator("camera_tools.insert_target_camera")
		
		col = layout.column(align = True)
		col.operator("camera_tools.set_active_camera")
		col.operator("camera_tools.seperate_text")
		col.operator("camera_tools.text_to_name")
		
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