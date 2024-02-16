#!/usr/bin/env python2
#
# find NCBI GEO platforms, specifically platform accession numbers (GPLXXX)
# from Ensembl Funcgen database array_chip.txt and array.txt flat files which contain
# information on expression arrays used in the Ensembl database.
#
# this requires searching using NCBI E-Utils to find matches of array name 
# (like "HG-U133A") to NCBI GPL. note that this mapping is 1 to many; 
# have not found any exact method of 1 to 1 correlation of array name to GPL.
#
# update: for best results, a class with the Ensembl arrays to GPL platform accessions was 
# curated manually and is called. see org_array_gpl.py.
#


#local
import get_ensembl_probes
import org_array_gpl


def getEnsemblArraysFromFile(dataDir):
  #array of filenames
  funcgenFiles = get_ensembl_probes.getFuncgenFilenames(dataDir)
  #map of id to name
  expressionArrayChipIds = get_ensembl_probes.getExpressionArrays(
      funcgenFiles['array'], funcgenFiles['array_chip'])
  return expressionArrayChipIds

#TODO dynamic searching will require some complicated logic/exceptions due to how 
# GEO search currently ignores certain characters in title (for ex. [, ], _, '). the main problem
# is that entirely incorrect arrays can be returned from search given a correct and fully 
# specific search term. for ex. searching for "[HG-U133A]" also returns "HG-U133A_2" in the title.
# in addition, the title is inconsistent between arrays and not all arrays have [] around the 
# array name. another, more minor issue, is that multiple variants of arrays can be returned--
# there's several GPLs for each array name.
#
#note that this search searches for GEO datasets ('gds[entry type') but grabs only the 
# data series accession for each dataset
def searchForPlatforms(organism, title, esearchFile, esummaryFile):
  database = 'gds'
  accessionType = 'GPL'  #corresponds to the <GPL> tag in XML output not [Entry Type] in search
  entryType = 'gpl'
  filterType = 'title'
  filterValue = '[HG-U133A]'  #TODO dynamic. here as an example only.
  terms = '%s[organism]+AND+%s[entry type]+AND+%s[title]' % (organism, entryType, title)
  seriesIds = ncbitools.getAccessionsFromSearch(database, accessionType, \
      terms, esearchFile, esummaryFile, filterType, filterValue)
  return platformIds

#organism - the ensembl funcgen organism name like homo_sapiens_funcgen_84_38
#dataDir - the directory with the downloaded Ensembl funcgen files, particularly array.txt.gz
# and array_chip.txt.gz
def getGplsFromEnsemblOrganismData(organism, dataDir):
  arrayChipMap = getEnsemblArraysFromFile(dataDir)
  gpls = []
  for (id_, array) in arrayChipMap.items():
    arrayGpls = getGplsFromEnsemblArrayName(organism, array)
    #where multiple GPLs correspond to an array returned as 'GPL123,GPL234'.
    # can be split for our purposes here.
    if arrayGpls:
      for gpl in arrayGpls.split(','):
        gpls.append(gpl)
  return gpls

#get gpl from manual curation stored in class.
#note gpls returned in format 'GPL123' or 'GPL123,GPL456'.
#returns [] if failed.
#expects organism to be like 'homo_sapiens_funcgen_85_38' or 'homo_sapiens_funcgen'
def getGplsFromEnsemblArrayName(organism, array):
  #cut off version number from the for ex. "homo_sapiens_funcgen_85_38" string
  # bc the keys are version independent (homo_sapiens_funcgen) in the map.
  keyword = 'funcgen'
  keywordIndex = organism.find(keyword)
  if keywordIndex >= 0:
    organismKey = organism[:keywordIndex+len(keyword)]
  else:
    organismKey = organism
  #could fail on a key not found exception if an organism 
  # or array is expected to be curated but the curations aren't updated.
  try:
    gplString = org_array_gpl.ORG_TO_ARRAY_TO_GPL[organismKey][array]
    if not gplString or gplString == '':
      raise
    gpls = gplString.split(',')
  except:
    #print 'Warning: no GPLs found for organism %s, array %s' % (organismKey, array)
    #exit gracefully and don't print any warning. many arrays currently 
    # don't have any GPL in the manually curated map.
    gpls = []
  return gpls
