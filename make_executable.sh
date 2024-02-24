#!/bin/sh
# Build the ExpressionLncr standalone GUI executable and bundle into release archive.
#
# Setup and run:
#  python3.11 -m venv .venv
#  source .venv/bin/activate
#  pip install -r requirements.txt
#  pip install -r requirements.dev.txt
#  bash make_executable.sh 0.0.0
#
# Note: pyinstaller only makes executables for the platform it's run on.
#  I.e. you need to run it on Windows to build a Windows executable.
#
version="$1"
pyinstaller --paths .venv/lib/python3.11/site-packages --add-data="*.py:." --onefile --windowed --name expressionlncr --icon=expressionlncr.png gui.py
cd dist
release="expressionlncr-${version}"
mkdir "${release}"
sha256sum expressionlncr > expressionlncr.sha256
mv expressionlncr.sha256 "${release}"
mv expressionlncr "${release}"
cp ../*.py "${release}"
tar -cvzf "${release}.tar.gz" "${release}"
sha256sum "${release}.tar.gz" > "${release}.tar.gz.sha256"
cd ..