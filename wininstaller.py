#!/usr/bin/env python2
#Build windows executable

from distutils.core import setup
import py2exe
from glob import glob

data_files = [("Microsoft.VC90.CRT", glob(r'msvc*.dll'))]

setup(console=['gui.py'], data_files=data_files)
