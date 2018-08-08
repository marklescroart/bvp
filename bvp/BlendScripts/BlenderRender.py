"""
Script to render via Blender using SLURM / other parallel computing. 

This file is called by the Render() and RenderSlurm() commands in SceneList 
class. In order to render many files, multiple instances of Blender need to be
opened, and each one needs to call this script (or, a modified version of this
script). 

Useful info for command-line Blender can be found at: 
http://wiki.blender.org/index.php/Doc:Manual/Render/Command_Line_Options
"""

import bvp,os,sys,copy,subprocess,math,time,random

### --- REPLACE 1 --- ###
TempFile = os.path.join(bvp.__path__[0],'Scripts','CurrentRender.pik')
### --- To here --- ###

# Jitter read time to avoid stupid NFS bugs:
time.sleep(random.random())
if bvp.Verbosity_Level > 3: print('Attempting to load: %s'%TempFile)
SL = bvp.utils.basics.load_pik(TempFile)

### --- REPLACE 2 --- ###
ScnToRender = range(len(SL.ScnList))
### --- To here --- ###

# Set memory saving mode
bvp.utils.blender.SetNoMemoryMode(nThreads=2,nPartsXY=4)

# Specify type of render *(??) This should be specified by SL.RenderOptions.
#fpath = copy.copy(SL.RenderOptions.filepath)
for ii in ScnToRender:
    Scn = SL.ScnList[ii]
    # Create scene in Blender (load all objects)
    Scn.Create(SL.RenderOptions)
    ## include scene number in file path
    #SL.RenderOptions.filepath = fpath%Scn.fpath
    # Render (animate)
    Scn.Render(SL.RenderOptions)
    # Clear all objects to prep for next render
    Scn.Clear()

# Remove temp files?
#if ii==len(SL.ScnList):
#   os.remove(TempFile)
# Display final info? Log time taken, etc?
#print('Finished rendering!') 