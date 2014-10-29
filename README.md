bvp
===

bvp (B.lender V.ision P.roject) is a module of functions and classes for creating visual 
stimuli within Blender. bvp functions are intended to allow creation of arbitrary scenes 
using libraries of "scene elements" (objects, backgrounds, skies/lighting setups, shadows,
and cameras). 

Scene elements are all managed by classes that wrap functionality of native Blender 
objects and store meta-data about each element (for example, the semantic category or
size of an object). Each individual scene element is stored in a archival .blend files, 
and managed by a database system based on mongodb (http://www.mongodb.com/).

Scene elements can be combined using a bvpScene class, which has methods to populate a 
given scene with objects in random locations, render the scene, and more.

All relevant information for a set of scenes is stored in the bvpSceneList 
class, which has* methods for permanent storage* / write-out of stimulus lists to 
archival hf5 files*. 

*Still to come 2014.10.23



Installation notes
==================

## Dependencies - non python:
mongodb server (binaries avialable for unix, osx, and windows at http://docs.mongodb.org/manual/installation/)

## Dependencies - python 3.X (X depends on your version of blender):
numpy 
matplotlib 
scipy
pymongo

0) * Get Mark to add you as a collaborator on github repo * 

1) Get BVP from github: git clone https://github.com/marklescroart/bvp <your_bvp_path>
	cd <your_bvp_path>
	#POSSIBLY check out some working branch:
	git fetch 
	git checkout <branchname>
	# Make sure <your_bvp_path> is on your PYTHONPATH in your .bashrc file

2) Install mongodb server. 
	See http://docs.mongodb.org/manual/installation/
	Recommended location is ~/mongodb/

) Download whatever Blender version you want to use. 
	Standard site for stable versions: http://www.blender.org/
	Bleeding edge new stuff available at: http://graphicall.org/
	# MacOS:
	delete <path_to_blender_app>/Blender.app/
	# NOTE: capitalization of words in that path may vary with operating system / Blender version

) Make sure you have python3.X environment on your computer somewhere
	Find it; add the following line to your ~/.bashrc or ~/.bash_profile file:
	export BLENDER_SYSTEM_PYTHON="<my_python3.X_path>"

) Recommended: Set a blender alias 

) Set settings in <your_bvp_path>/Settings/Settings.json

) Run mongod server with the command: 
	mongod --dbpath /

) Party. Ready to go.


Links: 
WTF is a .bashrc file?
WTF is the difference between .bashrc and .bash_profile?
WTF is a PYTHONPATH?
Where the hell do I find my system python?
Why is this all so DAMN COMPLICATED?
Where can I find some Blender tutorials that are worth a damn? 
Using anaconda to simplify your python life


Contributing models to BVP
==========================
First: I love you for even reading this! 

If you have models in non-Blender form (3DS max, Sketchup, .off, whatever), and don't want to be bothered, EMAIL ME and we can talk. I love more models. I always want more models. 

If you are willing to actually putting them in BVP format, GREAT, we have tools for that. 


