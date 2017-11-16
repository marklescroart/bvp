The files in this directory are "under-the-hood" files for BVP - i.e., they are
generally called by other functions, and you probably shouldn't mess with them. 

All the files in this folder are meant to be called within a .blend file - meaning, 
in a particular instance of Blender, with a file open. Other functions (e.g. the 
methods of bvpLibrary) will do this for you, but you can call them individually by
opening the script in Blender's text editor and running them inside Blender, or by 
calling Blender at the command line in the form: 
blender -b blend_file.blend -P script_name.py
... or by calling RunScriptForAllFiles.py

The scripts (generally) make some modification to that file, or they save some 
information about that file to a pickle (.pik) file. 

But really, you should just leave them alone.