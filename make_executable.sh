#!/bin/sh
#Short script to build the ExpressionLncr standalone GUI executable.
#Requires python, pyinstaller.
#PIP to install pyinstaller is optional, for ex: pip install pyinstaller
#Note that pyinstaller only makes executables for the platform it 
# is run on. I.e. you need to run it on Windows to build a Windows executable.
pyinstaller --onefile --windowed --name expressionlncr --icon=expressionlncr.png gui.py
