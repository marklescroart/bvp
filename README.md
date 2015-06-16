bvp
===

The B.lender V.ision P.roject (bvp) is a framework for creating visual stimuli within Blender. 

bvp consists of a library of python classes and functions, as well as a library of "scene 
elements" (objects, backgrounds, skies/lighting setups, shadows, and cameras) stored in 
.blend files and accessible through a database.

Scene elements are all managed by classes that wrap functionality of native Blender 
objects and store meta-data about each element (for example, the semantic category or
size of an object). Each individual scene element is stored in a archival .blend files, 
and managed by a database system based on mongodb (http://www.mongodb.com/).

Scene elements can be combined using a bvpScene class, which has methods to populate a 
given scene with objects in random locations, render the scene, and more.

All relevant information for a set of scenes is stored in the bvpSceneList 
class, which has* methods for permanent storage* / write-out of stimulus lists to 
archival hdf5 files*. 

*Still to come 2014.10.23



Installation
============

The INTENT with all this is to package all this code / all these dependencies as pip / conda packages. 

## Dependencies - non python:
mongodb server (binaries avialable for unix, osx, and windows at http://docs.mongodb.org/manual/installation/)

## Dependencies - python 3.X (X depends on your version of blender):
numpy 
matplotlib 
scipy
pymongo

1) Download whatever Blender version you want to use. -*-?
	Standard site for stable versions: http://www.blender.org/
	Bleeding edge new stuff available at: http://graphicall.org/
	# MacOS:
	delete <path_to_blender_app>/blender.app/Contents/Resources/2.72/python
	... and all its sub-folders.
	# NOTE: capitalization of words in that path may vary with operating system / Blender version

2.a) * Get Mark to add you as a collaborator on github repo * -*-

2.b) Get BVP from github: git clone https://github.com/marklescroart/bvp <your_bvp_path>
	# <your_bvp_path> should be something like ~/Code/bvp, or wherever you like keeping code
	cd <your_bvp_path>
	#POSSIBLY check out some working branch:
	git fetch origin <branchname>
	git checkout <branchname>
	# Make sure the folder above <your_bvp_path> is on your PYTHONPATH in your .bashrc file, so you can successfully import bvp from a python session
	# (the path requirement will go away once bvp is properly packaged...) -*-
	#For example, include the following line in your .bashrc file:
	# (if you already have a PYTHONPATH environment variable set:)
	export PYTHONPATH=$PYTHONPATH":/Users/mark/Code/" 
	# (if not:)
	export PYTHONPATH=":/Users/mark/Code/"

3) Make sure you have python3.X environment on your computer somewhere. Currently (2015.01) this should be 3.4. 
	I recommend you install this (and all your python packages) via anaconda:
	sudo conda create -n py34 python=3.4 anaconda  # creates python 3.4 environment with standard anaconda packages (numpy, scipy, matplotlib, more)
	sudo conda install -n py34 pymongo # install pymongo wrapper for mongodb
	Once you have a python 3.4 environment somewhere (if you follow the above recommendations,
	it will be in ) add the following line to your ~/.bashrc or ~/.bash_profile file:
	export BLENDER_SYSTEM_PYTHON="<my_python3.X_path>"
	For me (OSX version 10.10), it's: 
	export BLENDER_SYSTEM_PYTHON="/Users/mark/anaconda/envs/py34/"

4) Set settings in <your_bvp_path>/Settings/Settings.json
	Copy the file <your_bvp_path>/Settings/Example.json to <your_bvp_path>/Settings/Settings.json
	Relace the obvious bits of the following lines: 
	"RenderDir": "/path/to/which/to/render/by/default", 
    "BlenderCmd": "/path/to/your/blender/installation/executable/file", 
    "LibDir": "/path/to/your/Library" 

== At this point, BVP should* be functional, but you won't have the ability to access / store things in a database without mongod installed & running ==

5) Install mongodb server. 
	See http://docs.mongodb.org/manual/installation/
	Recommended install location is ~/mongodb/

(Before each use of database)
6) Run mongod server with the command: 
	mongod --dbpath <path_to_your_BVPdb> --port 9194
	The port is just a convention, flout it if you wish. 
	path_to_your_BVPdb is the path to which you have saved the whole directory of BVP .blend files and database headers. 

7) Party. Ready to go.

Installation - Recommended
==========================
) Set a blender alias -*-
	add the following line to your ~/.bashrc or ~/.bash_profile file:
	alias blender="<path_to_blender>"
	Note that path_to_blender should be a path to the actual executable file, INSIDE the blender.app bundle, e.g.:
	alias blender="/Applications/blender.app/Contents/MacOS/blender" # or wherever you installed blender.

) Use the blender settings provided in bvp/blendfiles/<blah>.blend (This currently DOES NOT WORK SO WELL (OR AT ALL))


Contributing models to BVP
==========================
First: I love you for even reading this! 

If you have models in non-Blender form (3DS max, Sketchup, .off, whatever), and don't want to be bothered, EMAIL ME and we can talk. I love more models. I always want more models. 

If you are willing to actually putting them in BVP format, GREAT, we have tools for that. 


Adding labels
=============

) The objects in the database are already labeled with semantic categories from the WordNet hierarchy. To add additional labels through the BVP blender addon GUI, you will need to make sure your system has the WordNet corpus downloaded for nltk (the Natural Language ToolKit for python) ==

Links: 
WTF is a .bashrc file?
WTF is the difference between .bashrc and .bash_profile?
WTF is a PYTHONPATH?
Where the hell do I find my system python?
Why is this all so DAMN COMPLICATED?
Where can I find some Blender tutorials that are worth a damn? 
Using anaconda to simplify your python life
