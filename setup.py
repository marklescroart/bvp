#! /usr/bin/env python
#
# Copyright (C) 2016 Mark Lescroart
# <mark.lescroart@gmail.com>
#
# Adapted from MNE-Python

import os
import sys
import setuptools
#from numpy.distutils.core import setup

if len(set(('develop', 'bdist_egg', 'bdist_rpm', 'bdist', 'bdist_dumb',
            'bdist_wininst', 'install_egg_info', 'egg_info', 'easy_install',
            'test',
            )).intersection(sys.argv)) > 0:
    # This formulation is taken from nibabel.
    # "setup_egg imports setuptools setup, thus monkeypatching distutils."
    # Turns out, this patching needs to happen before disutils.core.Extension
    # is imported in order to use cythonize()...
    from setuptools import setup
else:
    # Use standard
    from distutils.core import setup

from distutils.command.install import install
from distutils.core import Extension

version = "0.1"
with open(os.path.join('bvp', '__init__.py'), 'r') as fid:
    for line in (line.strip() for line in fid):
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('\'')
            break
if version is None:
    raise RuntimeError('Could not determine version')


descr = """A set of tools for rendering stimuli for vision experiments using Blender."""

DISTNAME = 'bvp'
DESCRIPTION = descr
MAINTAINER = 'Mark Lescroart'
MAINTAINER_EMAIL = 'mark.lescroart@gmail.com'
URL = 'https://github.com/marklescroart/bvp'
LICENSE = 'Regents of the University of California'
DOWNLOAD_URL = 'https://github.com/marklescroart/bvp'
VERSION = version

if __name__ == "__main__":
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    setup(name=DISTNAME,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          license=LICENSE,
          url=URL,
          version=VERSION,
          download_url=DOWNLOAD_URL,
          long_description=open('README.md').read(),
          zip_safe=False,  # the package can run out of an .egg file
          classifiers=['Intended Audience :: Science/Research',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved',
                       'Programming Language :: Python',
                       'Topic :: Software Development',
                       'Topic :: Scientific/Engineering',
                       'Operating System :: OSX'],
          platforms='any',
          packages=['bvp', 
                    'bvp.utils',
                    'bvp.Classes'],
          requires=['numpy', 'couchdb',],
          package_data={'bvp':[ 
                            'defaults.cfg',
                            ],
                        },
          include_package_data=True,
          scripts=[])
