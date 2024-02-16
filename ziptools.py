#!/usr/bin/env python

import gzip
import os
import zipfile
import tarfile


#untar/untar+gunzip file from a tar archive to outputFilename. expects 
# single file archive (ignores files in TAR after first).
def untargz(sourceFilename, outputFilename):
    with tarfile.open(sourceFilename) as zipped:
        firstMember = zipped.next()
        if firstMember:
            firstFileHandle = zipped.extractfile(firstMember)
            data = firstFileHandle.read()
            with open(outputFilename, 'wb') as plain:
                plain.write(data)

#bulk whole file into memory unzipping method. expects single file archive.
def gunzip(sourceFilename, outputFilename):
	with gzip.open(sourceFilename, 'rb') as zipped:
		data = zipped.read()
	with open(outputFilename, 'wb') as plain:
		plain.write(data)

#line-wise unzipping method. expects single file archive.
def gunzip2(sourceFilename, outputFilename):
	with gzip.open(sourceFilename, 'rb') as zipped:
		with open(outputFilename, 'wb') as plain:
			for line in zipped:
				plain.write(line)

#unzip only any file labelled FILENAME in FILENAME.gz or other zipped archive
def unzipOne(sourceFilename, destDir):
	#basename with no extension. eg. /path/to/file.bed.gz -> file.bed
	basenameNoExt = ''.join(os.path.basename(sourceFilename).split('.').pop())
	with zipfile.ZipFile(sourceFilename) as zipped:
		for member in zipped.infolist():
			if member.filename == baseNameNoExt:
				zipped.extract(member, destDir)

#create python unzip function protecting against bad archive.
# old versions of python (> 1-2 years ago) vulnerable in ZipFile.extractall
def unzipAll(sourceFilename, destDir):
	with zipfile.ZipFile(sourceFilename) as zipped:
		for member in zipped.infolist():
			words = member.filename.split('/')
			path = destDir
			for word in words[:-1]:
				drive, word = os.path.splitdrive(word)	
				head, word = os.path.split(word)
				if word in (os.curdir, os.pardir, ''): continue
				path = os.path.join(path, word)
			zipped.extract(member, path)

