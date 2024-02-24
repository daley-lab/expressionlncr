#!/usr/bin/env python3
# Grabs bulk download of Ensembl Funcgen database flat files for an organism 
# and searches for probe features (matched probe locations against reference genome).
# This method limits us to the platforms in Ensembl but eliminates the 
# expensive BLAST/BLAT step, in addition to some data cleaning / sanity checks.


#TODO Get length of chromosomes from Ensembl to convert '-' strand
# -> Current implementation for calculating overlap only compares + to + and - 
# to - strand.


import csv
import datetime
import getopt
import operator
import os
import re
import sys

#local
import arraytools
import beans
import downloader
import ziptools
import constants as c
import get_ensembl_funcgen_organisms as org


#downloads the funcgen database dump files (flat text) for the specified organism from ensembl.
#@return a map of file type to location
def getFuncgenFiles(orgString, destDir, fileTypes, cleanUp):
  downloader.createPathToFile(destDir)
  # Note: to use current Ensembl release would need to rework for changes to database schema
  # https://useast.ensembl.org/info/docs/api/core/core_schema.html
  # https://useast.ensembl.org/info/docs/api/funcgen/funcgen_schema.html
  #baseUrl = 'ftp://ftp.ensembl.org/pub/current/mysql'
  baseUrl = f'ftp://ftp.ensembl.org/pub/release-{c.PROBE_ENSEMBL_VERSION}/mysql'
  fileNameToLocation = {}
  funcgenUrlString = orgString
  #coreUrlString = orgString.replace('funcgen', 'core')
  for f in fileTypes:
    print('get funcgen files - downloading %s ...' % f)
    #schemaString = coreUrlString if f in ['coord_system', 'seq_region'] else funcgenUrlString
    schemaString = funcgenUrlString
    url = baseUrl + '/' + schemaString + '/' + f + '.txt.gz'
    if not destDir.endswith('/'):
      destDir += '/'
    output = destDir + f + '.txt'
    zippedOutput = output + '.gz'
    downloader.simpleDownload(url, zippedOutput)
    ziptools.gunzip(zippedOutput, output)
    fileNameToLocation[f] = output
    if cleanUp:
      os.remove(zippedOutput)
  return fileNameToLocation

#convenience function for later retrieving data in these files
def getFuncgenFilenames(destDir):
  fileNameToLocation = {}
  fileTypes = c.GET_ENSEMBL_PROBES_DEFAULTS['fileTypes']
  for f in fileTypes:
    output = destDir + '/' + f + '.txt'
    fileNameToLocation[f] = output
  return fileNameToLocation

#takes the coordinate system file unzipped, and the schema build to filter on from the 
# organism name, and whether to force returning the latest schema or fail
def getCoordSystemId(coordSystemFile, schemaBuild, forceCurrentSchema):
  coordSystemId = None
  coordSystemIdCol = 0
  nameCol = 1
  schemaBuildCol = 5
  isCurrentCol = 8
  delim = '\t'
  #note that version can be null therefore need to split on only single tab
  with open(coordSystemFile, 'r') as csf:
    reader = csv.reader(csf, delimiter=delim)
    for cols in reader:
      coordSystemId = cols[coordSystemIdCol]
      name = cols[nameCol]
      currentSchemaBuild = cols[schemaBuildCol]
      if name == 'chromosome' and currentSchemaBuild == schemaBuild:
        if forceCurrentSchema:
          isCurrent = cols[isCurrentCol]
          if not isCurrent:
            print('Schema build passed to get_ensembl_probes.py is not current. Aborting...', file=sys.stderr)
            sys.exit(2)
        break
  return coordSystemId

#only a subset of arrays in the funcgen schema are expression arrays.
#find out which from unzipped database array.txt and array_chip.txt file dumps.
#@return a set of array chip ids that are expression arrays.
#array chip ids needed not array ids, because array chip ids are used in the probe table.
#keys of set are integer ids, values are the human readable array name.
def getExpressionArrays(arrayFile, arrayChipFile):
  arrayIdToChipId = {}
  expressionArrayChipIds = {}
  delim = '\t'
  #array.txt file:
  arrayFileFormat = {'arrayIdCol': 0, 'arrayName': 1, 'formatCol': 2}
  #array_chip.txt file:
  arrayChipFileFormat = {'arrayChipIdCol': 0, 'arrayIdCol': 2}
  #build map of array_id to array_chip_id
  with open(arrayChipFile, 'r') as acf:
    arrayChipReader = csv.reader(acf, delimiter=delim)
    for arrayChipCols in arrayChipReader:
      arrayChipId = arrayChipCols[arrayChipFileFormat['arrayChipIdCol']]
      arrayId = arrayChipCols[arrayChipFileFormat['arrayIdCol']]
      arrayIdToChipId[arrayId] = arrayChipId
  #get the array chip id for each array that is format "EXPRESSION"
  with open(arrayFile, 'r') as af:
    arrayReader = csv.reader(af, delimiter=delim)
    for arrayCols in arrayReader:
      if arrayCols[arrayFileFormat['formatCol']] == 'EXPRESSION':
        arrayId = arrayCols[arrayFileFormat['arrayIdCol']]
        if arrayId in list(arrayIdToChipId.keys()):
          arrayChipId = arrayIdToChipId[arrayId]
          arrayName = arrayCols[arrayFileFormat['arrayName']]
          expressionArrayChipIds[arrayChipId] = arrayName
        else:
          print('get_ensembl_probes.getExpressionArrays(): array_chip_id missing for array: ' \
              + arrayId, file=sys.stderr)
  return expressionArrayChipIds

#need to use probe file in order to get the name of probes, 
# whether they are in a probe set,
# and whether they are expression probes (via the array chip id).
#@return a map of expression probes
def getExpressionProbes(probeFile, probeSetFile, expressionArrayChipIds,
      chunksize=100, keysOnly=False):
  print('Start get probes @ %s' % datetime.datetime.now())
  delim = '\t'
  nullChar = '\\N'  #i.e. '\N' is null in the probe file
  expressionProbes = {}
  probeIdCol = 0
  probeSetIdCol = 1  #nullable
  nameCol = 2
  arrayChipIdCol = 4
  probeSets = {}  #id to name
  probeSetProbeSetIdCol = 0
  probeSetProbeSetNameCol = 1
  print('get probes - probeset file @ %s' % datetime.datetime.now())
  with open(probeSetFile, 'r') as psf:
    probeSetReader = csv.reader(psf, delimiter=delim)
    for chunk in arraytools.getChunks(probeSetReader, chunksize=chunksize):
      for psr in chunk:
        probeSets[psr[probeSetProbeSetIdCol]] = psr[probeSetProbeSetNameCol]
  print('get probes - probe file @ %s' % datetime.datetime.now())
  with open(probeFile, 'r') as pf:
    probeReader = csv.reader(pf, delimiter=delim)
    for chunk in arraytools.getChunks(probeReader, chunksize=chunksize):
      for pr in chunk:
        #only store the probe if it corresponds to a probe expression array (and not a methylation array for ex.)
        arrayChipId = pr[arrayChipIdCol]
        if arrayChipId in expressionArrayChipIds:
          probeId = pr[probeIdCol]
          probe = None
          if not keysOnly:
            probeSetId = pr[probeSetIdCol]
            if probeSetId != nullChar and probeSetId != '' and probeSetId in probeSets:
              probeSetName = probeSets[probeSetId]
            else:
              probeSetName = None
            probeName = pr[nameCol]
            arrayName = expressionArrayChipIds[arrayChipId]
            probe = beans.Probe(probeId, probeSetName, probeName, arrayChipId, arrayName)
          expressionProbes[probeId] = probe
  return expressionProbes

#@input a probe file and probeset file, and a list of valid expression arrays to filter on
#@return pandas dataframe of expression probes
#dataframe columns (not in order):
# probeSetId, probeSetName, probeId, probeName, arrayChipId
def getExpressionProbeDataFrame(probeFile, probeSetFile, expressionArrayChipIds,
      keysOnly=False):
  import pandas as pd
  print('Start get probes @ %s' % datetime.datetime.now())
  #pidgeon-hole the expressionArrayChipIds dictionary of chip id -> chip name
  # into a dataframe object. could go back and re-write function creating the dict.
  expressionArrayChipIdFrame = pd.DataFrame(data={
      'arrayChipId': list(expressionArrayChipIds.keys()),
      'arrayChipName': list(expressionArrayChipIds.values())
  })
  #some constants regarding the files
  delim = '\t'
  nullChar = '\\N'  #i.e. '\N' is null in the probe file
  probeSetCols = [0, 1]
  probeSetColNames = ['probeSetId', 'probeSetName']
  #data types must all be string due to presence of NA values for probesetid in probe file
  probeSetDataTypes = {'probeSetId': str, 'probeSetName': str}
  probeCols = [0, 1, 2, 4]  #probesetid can be nullable
  probeColNames = ['probeId', 'probeSetId', 'probeName', 'arrayChipId']
  probeDataTypes = {'probeId': str, 'probeSetId': str, 
      'probeName': str, 'arrayChipId': str}
  #read in the probe set file
  print('get probes - probeset file @ %s' % datetime.datetime.now())
  probeSetFrame = pd.read_csv(
      probeSetFile,
      usecols=probeSetCols,
      sep=delim,
      header=None,
      dtype=probeSetDataTypes,
      low_memory=False,
      engine='c',
      names=probeSetColNames
  )
  #read in the probe file
  print('get probes - probe file @ %s' % datetime.datetime.now())
  probeFrame = pd.read_csv(
      probeFile,
      usecols=probeCols,
      sep=delim,
      header=None,
      dtype=probeDataTypes,
      na_values=[nullChar],
      low_memory=False,
      engine='c',
      names=probeColNames
  )
  print('get probes - merging @ %s' % datetime.datetime.now())
  #merge the probeset file probesetname into the probe file info.
  # probesetid can be null therefore left join.
  mergedOnProbeSetIdFrame = pd.merge(probeFrame, probeSetFrame, on='probeSetId', how='left')
  #now, merged frame cols (not in order):
  # probeid, probesetid, probesetname, probename, arraychipid
  #filter resulting dataframe for only probes that are in expression arrays we want
  # i.e. arraychipid in expressionArrayChipIds.
  # must have valid arraychipid therefore inner join.
  filteredOnArrayFrame = pd.merge(mergedOnProbeSetIdFrame, expressionArrayChipIdFrame, 
      on='arrayChipId', how='inner')
  return filteredOnArrayFrame

#takes an organism string like homo_sapiens_funcgen_84_38 and returns 84_38
def getSchemaBuildFromOrganism(organism):
  #get schema build from organism parameter (retrieved in earlier script and put as option 
  # [prettified] into galaxy interface)
  m = re.search(org.FUNCGEN_ORG_REGEX_PATTERN, organism)
  if m:
    schemaBuild = m.group(2) + '_' + m.group(3)
  else: 
    print('Invalid value for parameter organism: ' + organism, file=sys.stderr)
    sys.exit(2)
  return schemaBuild

#takes unzipped sequence region file, coordinate system id, and schema build.
#returns dictionary of sequence region ids to chomosome name.
def getSequenceRegionIds(seqRegionFile, coordSystemId, schemaBuild):
  seqRegionIdMap = {}
  seqRegionIdCol = 0
  nameCol = 1
  coordSystemIdCol = 2
  schemaBuildCol = 4
  delim = '\t'
  with open(seqRegionFile, 'r') as f:
    reader = csv.reader(f, delimiter=delim)
    for cols in reader:
      seqRegionId = cols[seqRegionIdCol]
      name = cols[nameCol]
      currentCoordSystemId = cols[coordSystemIdCol]
      currentSchemaBuild = cols[schemaBuildCol]
      if currentCoordSystemId == coordSystemId and currentSchemaBuild == schemaBuild:
        #NOTE in Ensembl flat files mitochondrial is denoted as chrMT.
        # we convert this to chrM here.
        if name == 'MT':
          name = 'M'
        #every sequence region we're interested in is a chromosome and we're outputting to 
        # bed file later so prepend with 'chr'
        seqRegionIdMap[seqRegionId] = 'chr%s' % name
  return seqRegionIdMap

#creates bed file out of probe features.
#formats the output as a BED-6 file: chrom, chromStart, chromEnd, name, score (0), strand. note
# here that name = (internal database) probe id.
#organism just for bed file header line (not implemented atm).
def createBedFile(probeFeatureFile, seqRegionIdMap, expressionProbes, 
    outputFile, organism, chunksize):
  delim = '\t'
  #probeFeatureIdCol = 0
  seqRegionIdCol = 1
  seqRegionStartCol = 2
  seqRegionEndCol = 3
  seqRegionStrandCol = 4
  probeIdCol = 5
  #analysisIdCol = 6
  #mismatchesCol = 7
  #cigarLineCol = 8
  #PROBE_SET_NAME = 0
  #PROBE_NAME = 1
  #ARRAY_CHIP_ID = 2
  #ARRAY_NAME = 3
  print('create bed - # seq region keys: ' + str(len(list(seqRegionIdMap.keys()))))
  print('create bed - # expression probes: ' + str(len(expressionProbes)))
  #ensure directories to output file are created
  print('create bed - creating path to ' + outputFile + '...')
  downloader.createPathToFile(outputFile)
  #delete file at output if already present. open(f, 'w') should erase it for us but it's 
  # appending for some strange reason.
  print('create bed - removing ' + outputFile + ' if present...')
  downloader.remove(outputFile)
  #output: chrom, chromStart, chromEnd, name, score (0), strand.
  print('create bed - using probe feature file %s' % probeFeatureFile)
  print('create bed - start writing output...')
  with open(outputFile, 'w') as output:
    #header = 'track name=probeFeatures ' + \
    #    'description="Ensembl microarray probe features from database ' + \
    #    organism + '" useScore=0\n'
    with open(probeFeatureFile, 'r') as pff:
      probeFeatureReader = csv.reader(pff, delimiter=delim)
        #TODO add header back in and later logic dealing with it
      #output.write(header)
      for chunk in arraytools.getChunks(probeFeatureReader, chunksize):
        for cols in chunk:
          try:
            #this will fail with KeyError if the probe feature doesn't correspond to a probe
            # we are interested in
            probe = expressionProbes[cols[probeIdCol]]
            #convert the requence region id to chromosome
            chrom = seqRegionIdMap[cols[seqRegionIdCol]]
            #NOTE in Ensembl flat files mitochondrial is denoted as chrMT.
            # we convert this to chrM before outputting to BED file.
            if chrom == 'MT':
              chrom = 'M'
            #for probes with a probe set name, format their id column in the BED file as 
            # array/probe_set:probe else use array/probe
            probeDesc = '%s/%s:%s' % (probe.arrayName, probe.probeSetName, probe.name) \
                if (probe.probeSetName) \
                else '%s/%s' % (probe.arrayName, probe.name)
            line = '%s\t%s\t%s\t%s\t%s\t%s\n' % (
                chrom,
                cols[seqRegionStartCol],
                cols[seqRegionEndCol],
                probeDesc,
                0,
                '+' if (cols[seqRegionStrandCol] == '1') else '-'
              )
            output.write(line)
          except KeyError:
            #this wasn't a probe feature with a relevant probe
            continue
  print('create bed - done writing output @ time: ' + str(datetime.datetime.now()))

#@input dataframe row with probe array, probe set, probe name
#@return probe description formatted for a bed file
def getProbeDesc(row):
  import numpy as np
  #for probes with a probe set name, format their id column in the BED file as 
  # array/probe_set:probe else use array/probe
  if (row['probeSetName'] and row['probeSetName'] != 'NaN' and row['probeSetName'] != np.nan):
    probeDesc = '%s/%s:%s' % (row['arrayChipName'], row['probeSetName'], row['probeName'])
  else:
    probeDesc = '%s/%s' % (row['arrayName'], row['probeName'])
  return probeDesc

#@input dataframe row, strand int is 0/1 strand integer
#@return -/+ strand symbol
def getStrandSymbol(row):
  if (str(row['seqRegionStrand']) == '1'):
    symbol = '+'
  else:
    symbol = '-'
  return symbol

#create bed file of all relevant probe features.
# use probe feature file and previously generated sequence region id map and 
# data frame of all relevant expression probes.
def createBedFileFromDataFrame(probeFeatureFile, seqRegionIdMap, expressionProbeFrame, 
    outputFile, organism):
  import pandas as pd
  #some constants defining the files
  delim = '\t'
  #probeFeatureIdCol = 0
  #seqRegionIdCol = 1
  #seqRegionStartCol = 2
  #seqRegionEndCol = 3
  #seqRegionStrandCol = 4
  #probeIdCol = 5
  #analysisIdCol = 6
  #mismatchesCol = 7
  #cigarLineCol = 8
  #PROBE_SET_NAME = 0
  #PROBE_NAME = 1
  #ARRAY_CHIP_ID = 2
  #ARRAY_NAME = 3
  probeFeatureCols = [1, 2, 3, 4, 5]
  probeFeatureColNames = ['seqRegionId', 'seqRegionStart', 'seqRegionEnd',
      'seqRegionStrand', 'probeId']
  probeFeatureDataTypes = str
  print('create bed - # seq region keys: ' + str(len(seqRegionIdMap)))
  print('create bed - # expression probes: ' + str(len(expressionProbeFrame)))
  #ensure directories to output file are created
  print('create bed - creating path to ' + outputFile + '...')
  downloader.createPathToFile(outputFile)
  #delete file at output if already present. open(f, 'w') should erase it for us but it's 
  # appending for some strange reason.
  print('create bed - removing ' + outputFile + ' if present...')
  downloader.remove(outputFile)
  #output: chrom, chromStart, chromEnd, name, score (0), strand.
  print('create bed - using probe feature file %s' % probeFeatureFile)
  #read probe feature file into dataframe
  print('create bed - get probe feature file @ %s' % datetime.datetime.now())
  probeFeatureFrame = pd.read_csv(
      probeFeatureFile,
      usecols=probeFeatureCols,
      sep=delim,
      header=None,
      dtype=probeFeatureDataTypes,
      names=probeFeatureColNames
  )
  #pidgeon-hole the sequence region id dictionary of sequence region id -> chromosome
  # into a dataframe object. could go back and re-write function creating the dict.
  seqRegionIdFrame = pd.DataFrame(data={
      'seqRegionId': list(seqRegionIdMap.keys()),
      'seqRegionName': list(seqRegionIdMap.values())
  })
  #merge in the sequence region names (i.e. chromosomes) needed for chromosome column
  withSeqRegionName = pd.merge(probeFeatureFrame, seqRegionIdFrame, on='seqRegionId', how='inner')
  #free up memory
  seqRegionIdFrame = None
  probeFeatureFrame = None
  #merge in the probe information needed to generate the probe description column.
  #columns in expression probe frame:
  # probeSetId, probeSetName, probeId, probeName, arrayChipId
  withProbeInfo = pd.merge(withSeqRegionName, expressionProbeFrame, on='probeId', how='inner')
  #free up memory
  withSeqRegionName = None
  #resulting dataframe columns:
  # seqRegionId, seqRegionStart, seqRegionEnd, seqRegionStrand, probeId
  # seqRegionName,
  # probeSetId, probeSetName, probeName, arrayChipId, arrayChipName
  #we want to create a dataframe with exactly the following columns:
  # chromosome, start, end, probeDesc, '0', strand
  #i.e.
  # seqRegionName, seqRegionStart, seqRegionEnd,
  # getProbeDesc(arrayChipName, probeSetName, probeName),
  # '0',
  # getStrandSymbol(seqRegionStrand)
  #clone first three columns from existing data
  bedFrame = withProbeInfo[['seqRegionName', 'seqRegionStart', 'seqRegionEnd']].copy()
  #create column of zeroes
  bedFrame['zeroes'] = '0'  #or instead of .copy() above use here: bedFrame.loc[:,'zeroes'] = '0'
  #FIXME thread dies somewhere after this point??
  #get probe description column from arrayChipName, probeSetName, and probeName
  print('create bed - creating probe description column @ %s' % datetime.datetime.now())
  bedFrame['probeDesc'] = withProbeInfo.apply(getProbeDesc, axis='columns')
  #get strand symbol from stand integer column
  print('create bed - creating strand symbol column @ %s' % datetime.datetime.now())
  bedFrame['seqRegionStrandSymb'] = withProbeInfo.apply(getStrandSymbol, axis='columns')
  #free up memory
  withProbeInfo = None
  #write out our bed data frame to file
  print('create bed - start writing output @ %s' % datetime.datetime.now())
  header = ['track name=probeFeatures ' + \
      'description="Ensembl microarray probe features from database ' + \
      organism + '" useScore=0\n']
  columnsToWrite = ['seqRegionName', 'seqRegionStart', 'seqRegionEnd',
      'probeDesc', 'zeroes', 'seqRegionStrandSymb']
  #add some empty columns to write to the header. needed to fool pandas
  # into writing an arbitrary header as it expects a string of aliases for each column.
  for i in range(0, len(columnsToWrite)):
    header.append('')
  bedFrame.to_csv(
      path_or_buf=outputFile,
      sep=delim,
      index=False,
      columns=columnsToWrite,
      header=header,
  )
  print('create bed - done writing output @ time: ' + str(datetime.datetime.now()))

def usage(defaults):
  print('Usage: ' + sys.argv[0] + \
      ' -d, --data-dir <CREATED_DIR> -f, --force-current-schema ' + \
      '-c, --chunksize <FILE_LINES_READ_AT_ONCE> ' + \
      '-o, --organism <ORGANISM> <BED_OUTPUT>')
  print('Example: ' + sys.argv[0] + \
      ' --organism homo_sapiens_funcgen_85_38 data/ensembl_probe_features.bed')
  print('Defaults:')
  for key, val in sorted(iter(defaults.items()), key=operator.itemgetter(0)):
    print(str(key) + ' - ' + str(val))

def __main__():
  shortOpts = 'hc:d:o:fnp'
  longOpts = ['help', 'chunksize=', 'data-dir=', 'organism=', \
      'force-current-schema', 'no-download']  #, 'file-types']
  defaults = c.GET_ENSEMBL_PROBES_DEFAULTS
  chunksize = defaults['chunksize']
  dataDir = defaults['dataDir']
  organism = defaults['organism']
  output = defaults['output']
  forceCurrentSchema = defaults['forceCurrentSchema']
  fileTypes = defaults['fileTypes']
  noDownload = defaults['noDownload']
  pandasPipeline = defaults['pandasPipeline']
  cleanUp = defaults['cleanUp']
  try:
    opts, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
  except getopt.GetoptError as err:
    print(str(err))
    usage(defaults)
    sys.exit(2)
  for opt, arg in opts:
    if opt in ('-h', '--help'):
      usage(defaults)
      sys.exit()
    elif opt in ('-c', '--chunksize'):
      chunksize = arg
    elif opt in ('-d', '--data-dir'):
      dataDir = arg
    elif opt in ('-f', '--force-current-schema'):
      forceCurrentSchema = True
    elif opt in ('-o', '--organism'):
      organism = arg
    elif opt in ('-n', '--no-download'):
      noDownload = True
    elif opt in ('-p', '--pandas-pipeline'):
      pandasPipeline = not pandasPipeline
    elif opt in ('-l', '--cleanup'):
      cleanUp = True
#    elif opt in ('--file-types'):
#      fileTypes = arg
  if len(args) > 0:
    output = args[0]
  #add trailing slash to directory so recognised as such
  if not dataDir.endswith('/'):
    dataDir += '/'
  print('Start get_ensembl_probes @ time: ' + str(datetime.datetime.now()))
  #get available funcgen organisms if we don't already have a file with the available 
  # organisms in it
  if not noDownload:
    #check if we already have the file
    funcgenOrgDefaults = c.GET_ENSEMBL_FUNCGEN_ORGANISMS_DEFAULTS
    if dataDir:
      availableOrganismsFileName = '%s/availableOrganisms.txt' % dataDir
    else:
      availableOrganismsFileName = funcgenOrgDefaults['output']
    availableOrganismsFileName = os.path.normpath(availableOrganismsFileName)
    #array of available organisms is a dictionary like: 
    if os.path.isfile(availableOrganismsFileName):
      #retrieve from file
      availableOrganisms = []
      with open(availableOrganismsFileName, 'r') as orgFile:
        for line in orgFile:
          availableOrganisms.append(line.strip())
    else:
      #download the available organisms
      availableOrganismsDict = org.parseFtpIndexForOrganisms(funcgenOrgDefaults['url'], availableOrganismsFileName, None, None, None)
      #turn dict like: homo_sapiens_funcgen_84_38 -> Homo sapiens v84.38
      # into array of keys
      availableOrganisms = list(availableOrganismsDict.keys())
    #match the default or user-passed organism against the up-to-date one
    newOrganism = None
    for availOrg in availableOrganisms:
      if availOrg.lower().startswith(organism.lower().split('_funcgen')[0]):
        newOrganism = availOrg
        break
    if newOrganism:
      oldOrganism = organism
      organism = newOrganism
      print('Updated Ensembl organism %s to %s' % (oldOrganism, organism))
    else:
      print('No matching new Ensembl organism for %s, download from Ensembl may fail' % organism, file=sys.stderr)
  #get schema build from organism name string
  print('Getting schema build from organism %s ...' % organism)
  schemaBuild = getSchemaBuildFromOrganism(organism)
  #pipeline:
  #grab funcgen database flat files for ensembl organism.
  #store file name to location in a map.
  #keys are fixed: array, array_chip, coord_system, probe, probe_set, probe_feature, seq_region
  if not noDownload:
    print('Downloading Ensembl Funcgen files to %s ...' % dataDir)
    funcgenFiles = getFuncgenFiles(organism, dataDir, fileTypes, cleanUp)
  else:
    print('Skipping download of Ensembl Funcgen files ...')
  #get current coordinate system id corresponding to chromosomes
  print('Start coord system time: ' + str(datetime.datetime.now()))
  coordSystemId = getCoordSystemId(funcgenFiles['coord_system'], schemaBuild, forceCurrentSchema)
  print('Coordinate system id: %s' % coordSystemId)
  #get all sequence region ids for those chromosomes. note # ids = # chromosomes in the organism.
  print('Start sequence regions time: ' + str(datetime.datetime.now()))
  seqRegionIdMap = getSequenceRegionIds(funcgenFiles['seq_region'], coordSystemId, schemaBuild)
  print('Number of sequence region ids: %s' % len(seqRegionIdMap))
  #get array and probe data to be able to filter out the non-expression array probe features
  print('Start expression arrays time: ' + str(datetime.datetime.now()))
  expressionArrayChipIds = getExpressionArrays(funcgenFiles['array'], funcgenFiles['array_chip'])
  #below takes a little while -> TODO optimise
  print('Start expression probes time: ' + str(datetime.datetime.now()))
  if not pandasPipeline:
    expressionProbes = getExpressionProbes(funcgenFiles['probe'], funcgenFiles['probe_set'],
        expressionArrayChipIds, chunksize=chunksize)
  else:
    expressionProbeFrame = getExpressionProbeDataFrame(funcgenFiles['probe'], funcgenFiles['probe_set'],
        expressionArrayChipIds)
  print('Start create bed time: ' + str(datetime.datetime.now()))
  if not pandasPipeline:
    createBedFile(funcgenFiles['probe_feature'], seqRegionIdMap, expressionProbes,
        output, organism, chunksize)
  else:
    createBedFileFromDataFrame(funcgenFiles['probe_feature'], seqRegionIdMap, expressionProbeFrame,
        output, organism)
  print('Done get_ensembl_probes @ time: ' + str(datetime.datetime.now()))
  print('If you wish to sort the BED file by chromosome and start pos, try running:\n')
  print('\tsort -k1,1 -k2,2n %s > data/probes.sorted.bed\n' % output)

if __name__ == '__main__':
  __main__()
