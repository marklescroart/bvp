import os

bvp_dir = os.path.dirname(__file__)

# Stage for rendering objects w/ cycles
object_stage_cycles = os.path.join(bvp_dir, 'BlendFiles/Object_Stage_Cycles.blend')
# Stage for rendering objects w/ Blender internal renderer
object_stage_blender = os.path.join(bvp_dir, 'BlendFiles/Object_Stage_Blender.blend')
# Entirely empty file
empty_file = os.path.join(bvp_dir, 'BlendFiles/Blank.blend')
