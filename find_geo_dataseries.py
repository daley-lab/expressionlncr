#!/usr/bin/env python3
#
# script to grab NCBI GEO data series from FTP server given search parameters.
# IDs and sizes of the series NOT the data itself is retrieved.
# sizes retrieved are of the series matrix files.
#
# input:
# -geo search terms
# -ensembl funcgen organism string
# -data directory that ensembl funcgen files have been downloaded to
# output:
# -eSearch results
# -eSummary results
# -file with summary statistics on data series in search results, namely:
#   > series matrix file name
#   > series matrix file size
#   > aggregate file count and size

import csv
import datetime
import getopt
import operator
import sys
import urllib.request
import urllib.error
import urllib.parse

#local
import downloader
import geotools
import ncbitools
import constants as c
import find_geo_platforms as plat


#get the array names only from a BED file consisting of overlapping probes.
# array names will be the FOO in FOO/bar:baz, which is the name field of the BED file.
#@return arrays - a set of array names
def getArraysFromProbeOverlapBed(probeOverlapFile):
  arrays = set()
  delim = '\t'
  nameCol = 3
  try:
    with open(probeOverlapFile, 'r') as pof:
      reader = csv.reader(pof, delimiter=delim)
      for cols in reader:
        try:
          if len(cols) > nameCol + 1:
            name = cols[nameCol]
            array = name.strip().split('/')[0]
            arrays.add(array)
        except Exception:
          pass
  except Exception as e:
    print(e, file=sys.stderr)
    print('Error: could not get arrays from %s' % probeOverlapFile)
  return arrays

#get sizes of all series matrix files present on FTP server
def getSeriesMatrixFileInfo(seriesIds, ftp):
  info = {}
  count = 0
  numSeries = len(seriesIds)
  for series in seriesIds:
    count += 1
    print('downloading info for series %s (%s/%s) @ %s ...' % (
        series, count, numSeries, str(datetime.datetime.now())
    ))
    #update our map of all matrix files -> size with this folder's contents
    seriesDir = geotools.getSeriesDirFromGSE(series)  #ex GSE10nnn
    ftpFolder = '%s/%s/GSE%s/matrix/' % (ftp, seriesDir, series)
    try:
      folderInfo = downloader.getFolderInfo(ftpFolder)
      for (k, v) in folderInfo.items():
        if k.endswith('series_matrix.txt.gz'):
          info[k] = v
    except urllib.error.URLError as ue:
      print(ue, file=sys.stderr)
      print('Error: could not download info for %s' % ftpFolder)
  return info

#find curated GEO DataSet's GEO Data Series belonging to platforms 
# we have Ensembl information on (Ensembl funcgen database flat files 
# specified by dataDir).
#
#example term:
#term=gds[Entry+Type]+AND+Homo+sapiens[Organism]+AND+(%s[GEO+Accession]+OR+%s[GEO+Accession]+OR+%s[GEO+Accession])
#
#NOTE don't have to worry about URL length due to limited number of platforms.
# human has most and is well below usual ~ 4000 character limit to URL length.
# (at about ~ 1000 characters.)
def searchForSeriesInPlatforms(organism, platforms, searchTerms, esearchFile, esummaryFile, gdsOnly=True):
  seriesIds = []
  if not platforms:
    return seriesIds
  #convert organism name like 'homo_sapiens_funcgen_85_38' to 'Homo sapiens'
  try:
    keyword = 'funcgen'
    splat = organism.split('_')
    #capitalise the first word
    splat[0] = '%s%s' % (splat[0][0].upper(), splat[0][1:])
    keywordIndex = splat.index(keyword)
    #make the searchable organism out of the words before the keyword
    searchableOrg = ' '.join(splat[:keywordIndex])
  except Exception:
    searchableOrg = organism
  #now construct the search term
  database = 'gds'
  accessionType = 'GSE'  #corresponds to the <GSE> tag in XML output not [Entry Type] in search
  #n.b.: entryType is not gse if we want to restrict retrieved series to only ones in datasets
  entryType = 'gds' if gdsOnly else 'gse'
  terms = '%s[organism] AND %s[entry type]' % (searchableOrg, entryType)
  #if no user-specified search terms then don't add
  if searchTerms != '':
    terms += ' AND %s' % searchTerms
  #add the GPLs to the search terms. we want a match on any of these.
  terms += ' AND ('
  orTerm = ' OR '
  for gpl in platforms:
    terms += '%s[GEO Accession]%s' % (gpl, orTerm)
  #trim off the final OR
  terms = terms[:-len(orTerm)]
  terms += ')'
  #print 'constructed search terms %s' % terms
  seriesIds = ncbitools.getAccessionsFromSearch(database, accessionType, \
      terms, esearchFile, esummaryFile)
  return seriesIds

#note that this search searches for GEO datasets ('gds[entry type') but grabs only the 
# data series accession for each dataset
def searchForAllDataSetSeries(organism, searchTerms, esearchFile, esummaryFile):
  database = 'gds'
  accessionType = 'GSE'  #corresponds to the <GSE> tag in XML output not [Entry Type] in search
  entryType = 'gds'  #*NOT* gse! a trick to restrict retrieved series to only ones in datasets
  terms = '%s[organism] AND %s[entry type] AND %s' % (organism, entryType, searchTerms)
  seriesIds = ncbitools.getAccessionsFromSearch(database, accessionType, \
      terms, esearchFile, esummaryFile)
  return seriesIds

def usage(defaults):
  print('Usage: ' + sys.argv[0] + \
      ' -o, --organism <STRING> -d, --data-dir <DIRECTORY> -t, --search-terms <STRING> -p, --get-platforms-from-overlap <PROBE_OVERLAP_FILE> --esearch <ESEARCH_OUTPUT> --esummary <ESUMMARY_OUTPUT> --series-output <SERIES_IDS_OUTPUT> --info-output <SUMMARY_INFO_OUTPUT>')
  print('Example: ' + sys.argv[0] + ' -o homo_sapiens_funcgen -t "asthma"')
  print('Defaults:')
  for key, val in sorted(iter(defaults.items()), key=operator.itemgetter(0)):
    print(str(key) + ' - ' + str(val))

def __main__():
  shortOpts = 'hgksd:e:f:i:o:p:t:'
  longOpts = ['help', 'ftp=', 'organism=', 'data-dir=', 'search-terms=', 
      'esearch=', 'esummary=', 'series-output=', 'info-output=',
      'get-all-platforms', 'get-platforms-from-overlap=', 
      'skip-series-info', 'allow-data-series']
  defaults = c.FIND_GEO_DATASERIES_DEFAULTS
  ftp = defaults['ftp']
  organism = defaults['organism']
  dataDir = defaults['dataDir']
  searchTerms = defaults['searchTerms']
  esearch = defaults['esearch']
  esummary = defaults['esummary']
  seriesOutput = defaults['seriesOutput']
  infoOutput = defaults['infoOutput']
  getAllPlatforms = defaults['getAllPlatforms']
  getPlatformsFromOverlap = defaults['getPlatformsFromOverlap']
  skipSeriesInfo = defaults['skipSeriesInfo']
  gdsOnly = defaults['gdsOnly']
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
    elif opt in ('-f', '--ftp'):
      ftp = arg
    elif opt in ('-o', '--organism'):
      organism = arg
    elif opt in ('-d', '--data-dir'):
      dataDir = arg
    elif opt in ('--esearch'):
      esearch = arg
    elif opt in ('--esummary'):
      esummary = arg
    elif opt in ('-t', '--search-terms'):
      searchTerms = arg
    elif opt in ('-e', '--series-output'):
      seriesOutput = arg
    elif opt in ('-i', '--info-output'):
      infoOutput = arg
    elif opt in ('-k', '--skip-series-info'):
      skipSeriesInfo = True
    elif opt in ('-g', '--get-all-platforms'):
      getAllPlatforms = True
    elif opt in ('-p', '--get-platforms-from-overlap'):
      getAllPlatforms = False
      getPlatformsFromOverlap = arg
    elif opt in ('-s', '--allow-data-series'):
      gdsOnly = False
  #get relevant GEO platforms
  if getAllPlatforms:
    #significantly slower, this gets all GEO platforms related to Ensembl arrays
    print('Getting all GEO platforms ...')
    platforms = plat.getGplsFromEnsemblOrganismData(organism, dataDir)
  else:
    #this gets only the platforms with arrays in the overlapping probe output file.
    #might be a moot point for large overlap files with most of the Ensembl arrays.
    print('Getting relevant GEO platforms ...')
    probeOverlapFile = getPlatformsFromOverlap
    arrays = getArraysFromProbeOverlapBed(probeOverlapFile)
    platforms = []
    for array in arrays:
      for gpl in plat.getGplsFromEnsemblArrayName(organism, array):
        platforms.append(gpl)
  #search for all geo data series ids corresponding to a set of search terms
  print('Searching GEO for data series with parameters...')
  print(' Organism: %s' % organism)
  print(' Search Terms: %s' % searchTerms)
  print(' eSearch output file: %s' % esearch)
  print(' eSummary output file: %s' % esummary)
  print(' Only curated GEO DataSets: %s' % gdsOnly)
  print('Start searching for GEO data series @ %s' % str(datetime.datetime.now()))
  seriesIds = searchForSeriesInPlatforms(organism, platforms, searchTerms, esearch, esummary, gdsOnly)
  #write out the series ids to file for use in the next pipeline step.
  print('Creating series ids file %s @ %s ...' % (seriesOutput, str(datetime.datetime.now())))
  downloader.createPathToFile(seriesOutput)
  with open(seriesOutput, 'w') as seriesFile:
    #sort as integer since seriesIds are always integers
    for series in sorted(seriesIds, key=lambda x: int(x)):
      line = '%s\n' % series
      seriesFile.write(line)
  print('Finished writing series ids file @ %s' % str(datetime.datetime.now()))
  #create an info file with file name and size for all series data matrices.
  #note the info file (with file sizes) isn't actually used in the next step, we only 
  # generate it for user feedback!
  if not skipSeriesInfo:
    print('Start retrieving series matrix info @ %s' % str(datetime.datetime.now()))
    info = getSeriesMatrixFileInfo(seriesIds, ftp)
    print('Creating series matrix info file: %s @ %s ...' % (infoOutput, str(datetime.datetime.now())))
    downloader.createPathToFile(infoOutput)
    with open(infoOutput, 'w') as infoFile:
      for (key, val) in sorted(info.items()):
        line = '%s\t%s\n' % (key, val)
        infoFile.write(line)
  print('Finished finding GEO data series @ %s' % str(datetime.datetime.now()))

if __name__ == '__main__':
  __main__()
