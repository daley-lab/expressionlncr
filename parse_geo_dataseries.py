#!/usr/bin/env python2
#
# Script to parse expression at probes
#  given a folder of gzipped GEO data series matrix files.
#
# Input:
# -directory with series data matrix files. file names like GSE*_series_matrix.tar.gz
# -directory for output files (lncRNA w/ overlap w/ expr, lncRNA w/ overlap w/o expr, 
#  lncRNA w/ overlap n/a expr, lncRNA w/o overlap)
# -XML file with mapping of overlap from lncRNA to probe(s)
# -funcgen organism - for mapping probe platform to GPL id in results
# -original lncRNA source file - for finding difference of lncRNAs w/ and w/o overlap
#
# Output: 
# -lncRNAs with probe expression
# -lncRNAs with probe overlap but no relevant expression data
# -lncRNAs with no overlap with Ensembl funcgen probes
#
# Algorithm for finding expressed probes:
#
# -read each zipped series data matrix file from a folder into memory one at a time
# -for the !series_matrix_table_begin/!series_matrix_table_end rows
#    ignoring the "ID_REF" "GSM...." "GSM...." ... header row
#    store !Series_platform_id "GPL...." ->
#            !Series_geo_accession "GSE...." ->
#              probe name ->
#                max {probe expression value} (among all samples)
# -read in the XML file of lncRNA -> probe overlap
# -note probes read in as probe platform -> probe set -> probe name
# -use org_array_gpl.py ORG_TO_ARRAY_TO_GPL map and organism input variable 
#   to map the GPL id to probe platform name
# -iterate through the overlapping probes, looking for expression
#   in the map of GPL -> GSE -> probe name -> max value
# -finally, combines the results from all the series matrix files into one 
#   expressed lncRNAs output file
#
# Folder structure:
# /path/given/to/data/GDSnnn_series_matrix.txt.gz
# where nnn is each GEO series accession number
#
# Ex. series matrix table format:
# ...
# !series_matrix_table_begin
# "ID_REF"  "GSM1376183"  "GSM1376184"  "GSM1376185"  ...
# "1415670_at"  9.398088024 9.202949651 9.590200486 ...
# "1415671_at"  10.31231611 10.22683466 10.40513719 ...
# ...
# !series_matrix_table_end
# ...
#


import csv
import datetime
import getopt
import gzip
import operator
import os
import re
from sets import Set
import sys
import xml.etree.cElementTree as cet

#local
from beans import ChromFeature, Probe, ProbeExpression
import constants as c
import downloader
import find_geo_platforms as plat


#one file per line
def parseFileNames(completedFilesFile):
  fileNames = Set()
  with open(completedFilesFile, 'rb') as f:
    for line in f:
      fileNames.add(line.strip())
  return fileNames

def parseData(dataDir, outDir, overlapFile, lncrnaFile, organism, completedFilesFile):
  print 'Parsing data started @ %s...' % str(datetime.datetime.now())
  #read in overlap file and make map of lncrna -> probe
  print 'Reading in lncrna/probe overlap file %s ...' % overlapFile
  overlapMap = parseOverlapFile(overlapFile)
  if not overlapMap:
    print 'Error: could not parse overlap file %s' % overlapFile 
    return
  print 'Reading in data series matrix files @ %s/GSE*_series_matrix.txt.gz ...' % dataDir
  #make sure data dir exists
  if not os.path.exists(dataDir):
    print >> sys.stderr, 'No data directory at: %s' % dataDir
    raise err
  #create output dir if doesn't exist already
  downloader.createPathToFile(outDir + '/')
  #create sub dir for output of expressed lncrnas files for each GEO series
  expressedLncrnasDir = '%s/expressed_series' % outDir
  downloader.createPathToFile(expressedLncrnasDir + '/')
  #read in zipped series data matrices one file at a time
  matrixFileNames = ['%s/%s' % (dataDir, f) for f in os.listdir(dataDir) if (
                      #only files
                      os.path.isfile(os.path.join(dataDir, f)) and
                      #ending with _series_matrix.txt.gz
                      os.path.basename(f).lower().endswith('_series_matrix.txt.gz') and
                      #starting with GSE
                      os.path.basename(f).lower().startswith('gse')
                    )]
  #check which series have already been parsed
  completedFiles = Set()
  try:
    completedFiles = parseFileNames(completedFilesFile)
  except IOError as ioe:
    #no existing file, create
    print 'No completed files file %s, creating ...' % completedFilesFile
    with open(completedFilesFile, 'wb') as cff:
      cff.write('')
  if len(completedFiles) > 0:
    print 'Skipping parsing for following files (already complete): %s ...' % (','.join(completedFiles))
  #parse all files that haven't been already
  filesToParse = Set(matrixFileNames).difference(completedFiles)
  with open(completedFilesFile, 'ab') as completeFile:
    count = 0
    numFiles = len(filesToParse)
    #for each file create a map of expression in that file then write out 
    # any lncrna/expression results to file
    for fileName in sorted(filesToParse):
      count += 1
      print ' > parsing file (%s/%s): %s @ %s' % (count, numFiles, fileName, str(datetime.datetime.now()))
      try:
        #create map of GPL -> probeSet -> probeName -> list(tuple(max probe val among samples, GSE))
        with gzip.open(fileName, 'rb') as matrixFile:
          expressionMap = parseSeriesDataMatrix(matrixFile)
        #write lncrna expression to file
        lncrnaExpressionMap = getLncrnaExpressionMap(overlapMap, expressionMap, organism)
        seriesExpressedLncrnasFile = '%s/%s.expressed.lncrnas.txt' % ( \
            expressedLncrnasDir, os.path.basename(fileName))
        writeExpressedLncrnas(lncrnaExpressionMap, seriesExpressedLncrnasFile)
      except Exception as err:
        print >> sys.stderr, err
        print >> sys.stderr, 'Could not parse series matrix data file: %s' % fileName
      completeFile.write('%s\n' % fileName)
  #once all the expressed lncrna files for each GEO series are written, 
  # then merge them all  into one expressed lncrna file that the user expects.
  #write header line of expressed lncrnas file once only
  expressedLncrnasFile = '%s/expressed.lncrnas.txt' % outDir
  print '> Expressed lncRNAs file will be written to: %s' % expressedLncrnasFile
  expressedLncrnas = mergeExpressedLncrnaFiles(expressedLncrnasDir, expressedLncrnasFile)
  #create output file of lncrnas with overlap but missing expression data
  # (i.e. not in expressedLncrnas list but in overlapMap)
  try:
    noExpressionDataLncrnasFile = '%s/noexpressiondata.lncrnas.txt' % outDir
    print '> No expression data lncRNAs file: %s ... @ %s' % ( \
        noExpressionDataLncrnasFile, str(datetime.datetime.now()))
    with open(noExpressionDataLncrnasFile, 'wb') as nedlf:
      noDataList = []
      for (lncrnaName, lncrnaProbeList) in overlapMap.iteritems():
        if lncrnaName.upper() not in expressedLncrnas:
          noDataList.append(lncrnaProbeList)
      header = '#lncRNA\toverlapping Ensembl probe(s), comma delimited\n'
      nedlf.write(header)
      #sort the list of tuples on the first element's name.
      #it's a tuple of ChromFeature.
      for lncrnaProbeList in sorted(noDataList, key=lambda x: x[0].name):
        lncrna = lncrnaProbeList[0]
        if lncrna is None:
          continue
        line = '%s\t' % lncrna.name
        for probe in lncrnaProbeList[1:]:
          if probe is None:
            continue
          line += '%s,' % probe.name
        #trim off last comma
        line = line[:-1]
        line += '\n'
        nedlf.write(line)
  except Exception as err:
    print >> sys.stderr, err
    print >> sys.stderr, 'Error writing no expression data lncRNAs'
  #use original lncrna file with all lncrnas to make output file of lncrnas #
  # w/ no overlap.
  try:
    print '> Parsing all lncRNAs from original input %s ...' % lncrnaFile
    lncrnaList = parseLncrnasFromBed(lncrnaFile)
    nonOverlappingLncrnas = getNonOverlappingLncnras(lncrnaList, overlapMap)
    nonOverlappingLncrnasFile = '%s/nonoverlapping.lncrnas.txt' % outDir
    print '> Non-overlapping lncRNAs file: %s ... @ %s' % ( \
        noExpressionDataLncrnasFile, str(datetime.datetime.now()))
    with open(nonOverlappingLncrnasFile, 'wb') as nolf:
      header = '#lncRNAs from lncRNA source not overlapping Ensembl probe(s)\n'
      nolf.write(header)
      for lncrna in sorted(nonOverlappingLncrnas):
        line = '%s\n' % lncrna
        nolf.write(line)
  except Exception as err:
    print >> sys.stderr, err
    print >> sys.stderr, 'Error writing non-overlapping lncRNAs'
  print 'Finished parsing data @ %s' % str(datetime.datetime.now())

#given a map of lncrna/probe overlap, and lncrna expression, returns
# a map of lncrna -> probe expression.
def getLncrnaExpressionMap(overlapMap, expressionMap, organism):
  #map the expression map probe name to the overlap file's expression probe name (-> lncrna).
  # then construct map of lncrna -> expression.
  lncrnaExpressionMap = {}
  for (lncrnaName, lncrnaProbeList) in overlapMap.iteritems():
    #if there's probes matched to this lncrna
    if len(lncrnaProbeList) > 1:
      #initialise map where we'll store expressed probes for this lncrna
      lncrna = lncrnaProbeList[0]
      lncrnaExpressionMap[lncrna] = []
      #for each probe
      for probeChromFeat in lncrnaProbeList[1:]:
        #grab the ensembl probe array name from the probe name.
        #note: probe name like HG-U133_Plus_2/200012_x_at:1135:649;
        slashSplit = probeChromFeat.name.split('/', 1)
        array = slashSplit[0]
        #while we're at it grab the probe set name and probe name, too
        colonSplit = slashSplit[1].split(':')
        if len(colonSplit) > 2:
          probeSet = colonSplit[0].strip()
          probeName = colonSplit[1].strip()
        else:
          probeSet = 'NoSet'
          probeName = colonSplit[0].strip()
        gpls = plat.getGplsFromEnsemblArrayName(organism, array)
        #we can now check for probe expression in the expression map using the GPL(s)
        # and the probe name.
        #the value for the probe key is a list of tuple(gse, max val among samples in gse)
        for gpl in gpls:
          try:
            probeSeriesMaxVals = expressionMap[gpl.upper()][probeSet.upper()][probeName.upper()]
            for (gse, maxVal) in probeSeriesMaxVals:
              probe = Probe(
                probeId=None,
                probeSetName=probeSet,
                name=probeName,
                arrayChipId=None,
                arrayName=array
              )
              probeExpression = ProbeExpression(
                probe=probe,
                probeChromFeat=probeChromFeat,
                gpl=gpl,
                gse=gse,
                maxVal=maxVal
              )
              lncrnaExpressionMap[lncrna].append(probeExpression)
          except KeyError as ke:
            #print 'Found no probe data for: gpl %s, probeSet %s, probeName %s' % (gpl, probeSet, probeName)
            continue
  return lncrnaExpressionMap

#write out the expression map for each series matrix file to file.
# file format is of expressed lncrna file type, minus the header.
#expressed lncrna file type:
#header = '#lncRNA(name)\tlncRNA(chrom)\tlncRNA(start)\tlncRNA(stop)\tlncRNA(strand)\t' + \
#    'probe(array)\tprobe(set)\tprobe(name)\tprobe(gpl)\tprobe(gse)\t' + \
#    'probe(max gse value)\tprobe2(array)\tprobe2(set)\t...etc...\n'
def writeExpressedLncrnas(lncrnaExpressionMap, expressedLncrnasFile):
  #create output file of lncrnas with expressed values and zero expression
  try:
    with open(expressedLncrnasFile, 'wb') as elf:
      #for each set of probe expressions for a lncrna find out if any are expression > 0.
      #write out to appropriate output file.
      #note: lncrna is a ChromFeature bean
      for (lncrnaBean, probeExpressions) in sorted(lncrnaExpressionMap.iteritems()):
        #we have new expression
        if probeExpressions and len(probeExpressions) > 0:
          probeColString = ''
          for probeExpression in probeExpressions:
            p = probeExpression
            probeSetName = p.probe.probeSetName if (p.probe.probeSetName.upper() != 'NoSet'.upper()) else ''
            #note that we add onto the previous probe columns
            probeColString += '\t' + '\t'.join((
                p.probe.arrayName,
                probeSetName,
                p.probe.name,
                p.gpl,
                p.gse,
                p.maxVal
            ))
          #construct output line of lncrna and overlapping probe data
          lncrnaCols = '\t'.join((
              lncrnaBean.name,
              lncrnaBean.chrom,
              lncrnaBean.start,
              lncrnaBean.stop, 
              lncrnaBean.strand
          ))
          line = lncrnaCols + probeColString + '\n'  #note: probeColString starts with a tab
          elf.write(line)
        else:
          #by changing the pipeline to parse one matrix file at a time and writing 
          # out the expressed lncrnas, the error message below will be trigger by most lncrnas
          # for each matrix file and is no longer useful.
          pass
          #no expression data? this is unexpected so warn, but continue.
          #possible cases (#3 is most likely, use option -s in find_geo_dataseries.py to workaround, 
          # caveats being: much more data to download, series might be less likely to have series matrix 
          # summary results file)
          #1. user uses an overlap.xml that contains more than the subset of downloaded information
          #2. an Ensembl funcgen database expression array has no GPL mapped in org_array_gpl.py
          #3. there are no GEO DataSets corresponding to the expression array in GEO, only GEO Series
          #4. there is a mismatch between Ensembl funcgen database probe names and the GEO Series matrix summary file
          #print >> sys.stderr, 'Warning: Expected expression data for lncRNA ' + \
          #    '%s but none found. Check the "no expression data" lncRNAs file for a full list.' % lncrnaBean.name
  except Exception as err:
    print >> sys.stderr, err
    print >> sys.stderr, 'Error writing expressed lncRNAs file %s' % expressedLncrnasFile

#join all the files of lncrna/expression probes into one file.
# returns list of expressed lncRNA names (strings).
def mergeExpressedLncrnaFiles(dataDir, outputFile):
  #first read in existing lncrna -> probe(s) expression files and create a map.
  #
  #note: this is a map of
  #   lncrna name -> file columns (lncrna, chrom, start, stop, strand, probe array, probeset, 
  #  probe name, probe gpl, etc etc....
  #see file header written below for more info.
  lncrnaHeaderCols = ['lncRNA(name)', 'lncRNA(chrom)', 'lncRNA(start)', 'lncRNA(stop)', 'lncRNA(strand)']
  numLncrnaCols = len(lncrnaHeaderCols)
  header = '#' + '\t'.join(lncrnaHeaderCols) + '\t' + \
    'probe(array)\tprobe(set)\tprobe(name)\tprobe(gpl)\tprobe(gse)\t' + \
    'probe(max gse value)\tprobe2(array)\tprobe2(set)\t...etc...\n'
  lncrnaExpressionMap = {}
  fileNames = ['%s/%s' % (dataDir, f) for f in os.listdir(dataDir) if (
                      #only files
                      os.path.isfile(os.path.join(dataDir, f)) and
                      #ending with .expressed.lncrnas.txt
                      os.path.basename(f).lower().endswith('.expressed.lncrnas.txt') and
                      #starting with GSE
                      os.path.basename(f).lower().startswith('gse')
                    )]
  numFiles = len(fileNames)
  count = 1
  for fileName in sorted(fileNames):
    #read in series specific lncrna expression map
    print ' > merging file (%s/%s): %s @ %s' % (count, numFiles, fileName, str(datetime.datetime.now()))
    count += 1
    fileExpressionMap = {}
    with open(fileName, 'rb') as f:
      reader = csv.reader(f, delimiter='\t')
      for cols in reader:
        lncrna = cols[0].upper()
        #upper-case all lncrna name keys in the maps, because different series might 
        # have upper/lower-case in the series matrix file.
        fileExpressionMap[lncrna.upper()] = cols
    #merge the series specific map with the global map
    for lncrna in fileExpressionMap:
      if lncrna in lncrnaExpressionMap:
        #merge
        existingCols = lncrnaExpressionMap[lncrna]
        newProbeCols = fileExpressionMap[lncrna][numLncrnaCols:]
        for col in newProbeCols:
          existingCols.append(col)
        lncrnaExpressionMap[lncrna] = existingCols
      else:
        #add new
        lncrnaExpressionMap[lncrna] = fileExpressionMap[lncrna]
  #write out the final expresssed lncrnas file
  with open(outputFile, 'wb') as out:
    #write the file header
    out.write(header)
    #write out the expression map
    for lncrna in sorted(lncrnaExpressionMap):
      line = '\t'.join(lncrnaExpressionMap[lncrna]) + '\n'
      out.write(line)
  return lncrnaExpressionMap.keys()

def parseSeriesDataMatrix(matrixFile):
  #map of GPL -> probe set -> probe name -> list(tuple(GSE, probe max value)).
  #note: probe set == 'NoSet' where probe has no defined probe set name.
  expressionMap = {}
  readTableHeader = False
  readTableRow = False
  gse = None
  gpl = None
  for line in matrixFile:
    #get the GSE, series accession
    if line.startswith('!Series_geo_accession'):
      gse = line.replace('"', '').split('\t')[1].strip().upper()
      print ' > got %s' % gse
    #get the GPL, series platform accession
    if line.startswith('!Series_platform_id'):
      gpl = line.replace('"', '').split('\t')[1].strip().upper()
      print ' > got %s' % gpl
    if readTableRow:
      #read in a row of the table. (probeSet/)probeName\tsample1Val\tsample2Val ...
      cols = line.replace('"', '').split('\t')
      slashSplit = cols[0].split('/', 1)
      if len(slashSplit) > 1:
        probeSet = slashSplit[0].upper().strip()
        probeName = slashSplit[1].upper().strip()
      else:
        probeSet = 'NoSet'.upper().strip()
        probeName = slashSplit[0].upper().strip()
      #get maximum expression at this probe among all samples in this series
      maxVal = -1
      for val in cols[1:]:
        stripped = val.strip()
        if stripped > maxVal:
          maxVal = stripped
      #set the expression map for this probe.
      #initialise keys as necessary.
      try:
        expressionMap[gpl]
      except KeyError as ke:
        expressionMap[gpl] = {}
      try:
        expressionMap[gpl][probeSet]
      except KeyError as ke:
        expressionMap[gpl][probeSet] = {}
      try:
        #add to probe's list of tuple(gse, maxval)
        probeSeriesMaxVals = expressionMap[gpl][probeSet][probeName]
        if not probeSeriesMaxVals:
          probeSeriesMaxVals = []
        probeSeriesMaxVals.append((gse, maxVal))
        expressionMap[gpl][probeSet][probeName] = probeSeriesMaxVals
      except KeyError as ke:
        expressionMap[gpl][probeSet][probeName] = [(gse, maxVal)]
    if readTableHeader:
      #ignore the header line for now. queue up read table row on next row.
      readTableRow = True
      continue
    if line.startswith('!series_matrix_table_begin'):
      #double-check that we got both the gse and gpl which are to be keys 
      # for probe expression map
      if not gse or not gpl:
        print >> sys.stderr, 'Malformed series data matrix file: %s' % fileName
        break
      readTableHeader = True
      continue
    if line.startswith('!series_matrix_table_end'):
      readTableRow = False
      continue
  return expressionMap

#make a map of ChromFeature type a/b to ChromFeature type b/a.
# map is a/b.name -> (a/b, b/a, b/a, ...) list of ChromFeature.
# note XML maps a -> children b. reverse makes overlapMap of b -> a.
def parseOverlapFile(overlapFile, reverse=False):
  print 'Parsing overlap file %s @ %s ...' % (overlapFile, str(datetime.datetime.now()))
  xml = open(overlapFile, 'rb')
  tree = cet.parse(xml)
  root = tree.getroot()
  overlapMap = {}
  for a in root.findall('a'):
    afeat = getChromFeature(a)
    for b in a.findall('b'):
      bfeat = getChromFeature(b)
      #define which feature is the key in the map and which is mapped
      if reverse:
        keyfeat = bfeat
        mappedfeat = afeat
      else:
        keyfeat = afeat
        mappedfeat = bfeat
      if not keyfeat or not mappedfeat:
        #probably indicates a malformed overlap XML file.
        # warn but continue parsing
        print 'Warning: likely malformed overlap file %s' % overlapFile
        print '\t> Missing child <B> elements for <A> elements'
        continue
      try:
        feats = overlapMap[keyfeat.name]
      except KeyError as ke:
        #no entry yet for key so initialise
        overlapMap[keyfeat.name] = [keyfeat]
        feats = overlapMap[keyfeat.name]
      if not feats:
        feats = [keyfeat]
      feats.append(mappedfeat)
      overlapMap[keyfeat.name] = feats
  return overlapMap

#returns ChromFeature for a cElementTree element
def getChromFeature(element):
  chrom = element.find('chr').text
  start = element.find('start').text
  stop = element.find('stop').text
  strand = element.find('strand').text
  name = element.find('name').text
  feat = ChromFeature(chrom, start, stop, strand, name)
  return feat

def parseLncrnasFromBed(lncrnaFile):
  lncrnaList = None
  delim = c.BED_DEFAULTS['delim']
  nameCol = c.BED_DEFAULTS['nameCol']
  try:
    with open(lncrnaFile, 'rb') as lf:
      reader = csv.reader(lf, delimiter=delim)
      lncrnaList = []
      for cols in reader:
        lncrna = cols[nameCol]
        lncrnaList.append(lncrna)
  except Exception as err:
    print >> sys.stderr, 'Error parsing file %s for lncRNAs. Output file of lncRNAs not found to ooverlap with probes will be missing!' % lncrnaFile
  return lncrnaList

def getNonOverlappingLncnras(lncrnaList, overlapMap):
  nonOverlappingLncrnas = []
  #since python doesn't support complex classes as keys in dictionaries (hashmaps)
  # the overlapMap is a bit messy.
  # keys are lncrna.name -> (lncrna, probe1, probe2, ...).
  # note: the probes and lncrnas are ChromFeature type.
  for lncrna in lncrnaList:
    if lncrna not in overlapMap:
      nonOverlappingLncrnas.append(lncrna)
  numLncrnas = len(lncrnaList)
  numOverlapping = len(overlapMap.keys())
  numNonOverlapping = len(nonOverlappingLncrnas)
  print '# lncrnas: %s' % numLncrnas
  print '# overlapping lncrnas: %s' % numOverlapping
  print '# non-overlapping lncrnas: %s' % numNonOverlapping
  if (numOverlapping + numNonOverlapping) != numLncrnas:
    print 'Warning: number of lncRNAs in getNonOverlappingLncrnas did not add up!'
  return nonOverlappingLncrnas

def usage(defaults):
  print 'Usage: ' + sys.argv[0] + \
      ' -d, --data-dir <DIRECTORY> -o, --out-dir <DIRECTORY> -f, --overlap-file <FILE>'
  print 'Example: ' + sys.argv[0] + ' -d data/matrices -o data/results -f data/overlap.xml'
  print 'Defaults:'
  for key, val in sorted(defaults.iteritems(), key=operator.itemgetter(0)):
    print str(key) + ' - ' + str(val)

def __main__():
  shortOpts = 'hf:d:o:l:r:c:'
  longOpts = ['help', 'overlap-file=', 'data-dir=', 'out-dir=', 'lncrna-file=', 'organism=', 'completed-files-file=']
  defaults = c.PARSE_GEO_DATASERIES_DEFAULTS
  overlapFile = defaults['overlapFile']
  dataDir = defaults['dataDir']
  outDir = defaults['outDir']
  lncrnaFile = defaults['lncrnaFile']
  organism = defaults['organism']
  completedFilesFile = defaults['completedFilesFile']
  try:
    opts, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
  except getopt.GetoptError as err:
    print str(err)
    usage(defaults)
    sys.exit(2)
  for opt, arg in opts:
    if opt in ('-h', '--help'):
      usage(defaults)
      sys.exit()
    elif opt in ('-f', '--overlap-file'):
      overlapFile = arg
    elif opt in ('-d', '--data-dir'):
      dataDir = arg
    elif opt in ('-o', '--out-dir'):
      outDir = arg
    elif opt in ('-l', '--lncrna-file'):
      lncrnaFile = arg
    elif opt in ('-r', '--organism'):
      organism = arg
    elif opt in ('-c', '--completed-files-file'):
      completedFilesFile = arg
  parseData(dataDir, outDir, overlapFile, lncrnaFile, organism, completedFilesFile)

if __name__ == '__main__':
  __main__()
