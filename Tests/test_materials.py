
import bvp

dbi = bvp.DBInterface()
fname = '/home/mark/pomsync/mark/Projects/BioMotion/Stimuli/TextureMovies/tex_sz00512_ver00001.mp4'

mat = bvp.Material.from_media(fname, 'matmat')