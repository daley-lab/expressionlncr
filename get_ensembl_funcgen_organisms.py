#!/usr/bin/env python3
# Curls the Ensembl FTP server for a listing of available organisms with the funcgen
# database information and returns it.
#
#1. curl ftp://ftp.ensembl.org/pub/current_mysql/ > curl_index.txt
#2. parse into columns via space delimiting merging multiple delimiters (not tab sep)
#3. column 9 (last) should be the directory (organism) name
#4.
# only some organisms will have funcgen database/schema.
# others just look like: ailuropoda_melanoleuca_core_84_1
# need to regex for: ([a-z_]+)_funcgen_([0-9]+)_([0-9]+)
# where group 1 = organism name, group 2 = major version, group 3 = minor version.
# format organism name to pretty format by converting '_' to ' ' and uppercasing the first word:
# "canis_familiaris" -> "Canis familiaris"


import getopt
import operator
import sys
import re

#local
import downloader
import constants as c
import ziptools


#gets the index at FTP url and parses it for Ensembl organisms with the funcgen database.
# returns a map of database name to prettified name for user selection.
# e.g. homo_sapiens_funcgen_84_38 -> Homo sapiens v84.38
def parseFtpIndexForOrganisms(url, output, prettify, arrayFiles, dataDir):
  #1. curl ftp://ftp.ensembl.org/pub/current_mysql/ > output
  #note that urllib works for FTP too, not just HTTP. same output as curl.
  data = downloader.getUrl(url)
  #create path to output file
  downloader.createPathToFile(output)
  #2. parse into columns via space delimiting merging multiple delimiters (not tab sep)
  #3. column 9 (last) should be the directory (organism) name
  organisms = {}
  curlDirectoryColumn = 8
  with open(output, 'w') as outputFile:
    for line in data.splitlines():
      cols = re.split('\s+', line)
      #last line in the file blank, possibly others in future. so skip these lines
      if len(cols) > curlDirectoryColumn:
        org = cols[curlDirectoryColumn]
        m = re.search('([a-z_]+)_funcgen_([0-9]+)_([0-9]+)', org)
        if m:
          pretty = prettifyOrganism(org)
          organisms[org] = pretty
          if prettify:
            outputFile.write(pretty + '\n')
          else:
            outputFile.write(org + '\n')
  #if requested download the array info files for these funcgen databases to a directory
  if arrayFiles and dataDir: 
    downloader.createPathToFile(dataDir)
    for (org, pretty) in organisms.items():
      arrayFileUrl = '%s%s/array.txt.gz' % (url, org)
      arrayFileUnzip = '%s/array.%s.txt' % (dataDir, org)
      arrayFileOut = '%s.gz' % (arrayFileUnzip)
      print('downloading %s to %s' % (arrayFileUrl, arrayFileOut))
      downloader.simpleDownload(arrayFileUrl, arrayFileOut)
      ziptools.gunzip(arrayFileOut, arrayFileUnzip)
      downloader.remove(arrayFileOut)
  return organisms
    
#4.
# format organism name to pretty format by converting '_' to ' ' and uppercasing the first word:
# "canis_familiaris_XX_YY" -> "Canis familiaris vXX.YY"
def prettifyOrganism(organism):
  pattern = '([a-z_]+)_[a-z_]+_([0-9]+)_([0-9]+)'
  m = re.search(pattern, organism)
  if m:
    name = m.group(1)
    major = m.group(2)
    minor = m.group(3)
    pretty = (name[0].upper() + name[1:]).replace('_', ' ') + ' v' + major + '.' + minor
  else:
    pretty = organism
  return pretty

def usage(defaults):
  print('Usage: ' + sys.argv[0] + ' -u, --url <ENSEMBL_FTP> -o, --output <OUTPUT>')
  print('Example: ' + sys.argv[0] + ' --output available_organisms.txt')
  print('Defaults:')
  for key, val in sorted(iter(defaults.items()), key=operator.itemgetter(0)):
    print(str(key) + ' - ' + str(val))

def __main__():
  shortOpts = 'ho:u:p:'
  longOpts = ['help', 'output=', 'url=', 'pretty=', 'data-dir=', 'array-files']
  defaults = c.GET_ENSEMBL_FUNCGEN_ORGANISMS_DEFAULTS
  output = defaults['output']
  url = defaults['url']
  prettify = defaults['pretty']
  arrayFiles = defaults['arrayFiles']
  dataDir = defaults['dataDir']
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
    elif opt in ('-o', '--output'):
      output = arg
    elif opt in ('-u', '--url'):
      url = arg
    elif opt in ('-p', '--pretty'):
      prettify = True
    elif opt in ('--array-files'):
      arrayFiles = True
    elif opt in ('--data-dir'):
      dataDir = arg
  organisms = parseFtpIndexForOrganisms(url, output, prettify, arrayFiles, dataDir)

if __name__ == '__main__':
  __main__()
