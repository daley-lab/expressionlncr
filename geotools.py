#!/usr/bin/env python2
#
#functions related to working with NCBI GEO FTP server
#


import csv
from sets import Set
import sys


#for GEO platform ids and series ids there is a subdirectory in between
# platforms/series and GPL1234/GSE1234. we need to generate this 
# directory name based on the GPL or GSE id, here 1234.
#
#here's the expected output:
#GPL123:
# 123 -> GPLnnn
# 1234 -> GPL1nnn
# 12345 -> GPL12nnn
#GSE123:
# 123 -> GSEnnn
# 1234 -> GSE1nnn
# 12345 -> GSE12nnn
#
#NOTE no geo accessions greater than 5 digits currently exist, but 
# going to assume for 6 digits it looks like:
# 123456 -> GSE123nnn
#
#the url that's ultimately constructed looks like this:
# ftp://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL10nnn/GPL10000
def getDirFromGeoAccession(accessionType, accession):
  dirName = accessionType
  accessionStr = str(accession)
  #get first (length-3) digits of accession
  numDigits = len(accessionStr)-3 if len(accessionStr) > 3 else 0
  accessionDigits = accessionStr[:numDigits]
  dirName += accessionDigits + 'nnn'
  return dirName

def getPlatformDirFromGPL(gpl):
  return getDirFromGeoAccession('GPL', gpl)

def getSeriesDirFromGSE(gse):
  return getDirFromGeoAccession('GSE', gse)

def removeGPL(idString):
  return removePrefix(idString, 'GPL')

def removeGSE(idString):
  return removePrefix(idString, 'GSE')

def removePrefix(idString, prefix):
  if idString.lower().startswith(prefix):
    return idString[len(prefix):]
  else:
    return idString

def printAccession(accessionType, accession):
  line = 'accn: %s, type: %s, result: %s' % (accession, accessionType, getDirFromGeoAccession(accessionType, accession))
  print(line)

#get series ids from either input file and/or argument.
#argument should look like: 1,2,3,4
#input file can have any combination of tab delimited cols of ids
# or lines of ids.
#ids can be string 'GSE1234' or numeric '1234' style.
def getSeriesIds(seriesFile=None, seriesArg=None):
  ids = []
  if seriesArg and seriesArg != '':
    #parse arguments delimited by commas
    cols = re.split(',', seriesArg)
    for col in cols:
      ids.append(removeGSE(col))
      if col.lower().startswith('GSE'):
        ids.append(col[3:])
      else:
        ids.append(col)
  if seriesFile:
    try:
      with open(seriesFile, 'rb') as s:
        #parse all ids in each line delimited by tabs, and all lines
        reader = csv.reader(s, delimiter='\t')
        for cols in reader:
          for col in cols:
            ids.append(removeGSE(col))
    except IOError:
      print('Warning: No series id file: %s' % seriesFile)
  return ids

#file format is whitespace delim rows &/ cols of GSE identifiers, numbers only
def parseSeriesIdFile(seriesFileName):
  seriesSet = Set()
  with open(seriesFileName, 'rb') as seriesFile:
    for line in seriesFile:
      cols = line.strip().split()
      for series in cols:
        if series:  #not empty string
          seriesSet.add(series)
  return seriesSet

def __main__(argv):
  accessionTypes = ['GPL', 'GSE']
  intAccessions = [1, 12, 123, 1234, 12345, 123456]
  accessions = [str(x) for x in intAccessions]
  for accessionType in accessionTypes:
    for accession in accessions:
      printAccession(accessionType, accession)
    for accession in intAccessions:
      printAccession(accessionType, accession)

if __name__ == '__main__':
  __main__(sys.argv)

