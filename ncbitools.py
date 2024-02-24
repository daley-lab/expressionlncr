#!/usr/bin/env python3
#
#functions related to working with NCBI e-utilities
#
#some example queries:
#
#https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=human[organism]+AND+gds[entry type]&usehistory=y&version=2.0&retmax=10
#
#(replace XX and YY as appropriate below from the esearch results above)
#https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&query_key=XX&WebEnv=YY&retmode=xml&version=2.0&retmax=10
#

import sys
import urllib.parse
import xml.etree.cElementTree as cet

#local
import downloader


def getEsearch(database, searchTerms, output, retstart=None, retmax=None, overwrite=False):
  baseurl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
  if retstart and retmax:
    params = urllib.parse.urlencode({
      'db': database,
      'term': searchTerms,
      'retmax': retmax,
      'retstart': retstart,
      'usehistory': 'y',
      'version': '2.0',
      'email': 'genapha@hli.ubc.ca',
      'tool': 'ncbitools.py'
    })
  else:
    params = urllib.parse.urlencode({
      'db': database,
      'term': searchTerms,
      'usehistory': 'y',
      'version': '2.0',
      'email': 'genapha@hli.ubc.ca',
      'tool': 'ncbitools.py'
    })
  url = baseurl + '?%s' % params
  print('Querying NCBI eSearch: ' + url)
  downloader.simpleDownload(url, output, force=overwrite)

def getEsummary(database, queryKey, webEnv, output, retstart=None, retmax=None, overwrite=False):
  baseurl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
  if retstart and retmax:
    params = urllib.parse.urlencode({
      'db': database,
      'query_key': queryKey,
      'WebEnv': webEnv,
      'retmax': retmax,
      'retstart': '0',
      'retmode': 'xml',
      'version': '2.0',
      'email': 'genapha@hli.ubc.ca',
      'tool': 'ncbitools.py'
    })
  else:
    params = urllib.parse.urlencode({
      'db': database,
      'query_key': queryKey,
      'WebEnv': webEnv,
      'retmode': 'xml',
      'version': '2.0',
      'email': 'genapha@hli.ubc.ca',
      'tool': 'ncbitools.py'
    })
  url = baseurl + '?%s' % params
  print('Querying NCBI eSummary: ' + url)
  downloader.simpleDownload(url, output, force=overwrite)

#returns a 2-tuple of (<QueryKey> value, <WebEnv> value)
def parseEsearch(esearchFile):
  xml = open(esearchFile, 'r')
  tree = cet.parse(xml)
  root = tree.getroot()
  #get QueryKey tag. should only be 1 right under the root <eSearchResult> element
  queryKey = root.find('QueryKey')
  if queryKey is None:
    raise Exception('No QueryKey in eSearch results file: %s' % esearchFile)
  queryKeyText = queryKey.text
  #get WebEnv tag. should only be 1 right under the root <eSearchResult> element
  webEnv = root.find('WebEnv')
  if webEnv is None:
    raise Exception('No WebEnv in eSearch results file: %s' % esearchFile)
  webEnvText = webEnv.text
  return (queryKeyText, webEnvText)

#parses the eSummary results xml and returns a set of integer $accessionType id's.
#for ex: $accessionType = 'GPL' ...
# hierarchy: eSummaryResult -> DocumentSummarySet -> DocumentSummary -> GPL.text
# each <DocumentSummary uid="XXXX"> is another GEO DataSet, and contains at least 1
# <GPL>YYYYY</GPL> as a child.
# also note: SOFT format data for this DataSet is in DocumentSummary -> FTPLink.text
#
#filterType - the tag to filter results further on
#filterValue - if the value is within the filter tag the accession will be parsed
def parseEsummary(esummaryFile, accessionType, filterType=None, filterValue=None):
  accessions = set()
  xml = open(esummaryFile, 'r')
  tree = cet.parse(xml)
  root = tree.getroot()
  for docsum in root.findall('./DocumentSummarySet/DocumentSummary'):
    #findall() not find() because potentially >1 accession. for ex. if we look for GSE
    # accession using a GDS query, there's potentially >1 GSE per GDS.
    accns = docsum.findall(accessionType)
    if not accns:
      print('No ID found for %s %s' \
          % (accessionType, docsum.attrib['uid']), file=sys.stderr)
      continue
    if filterType and filterValue:
      #only get the first. shouldn't have more than 1 tag for filter (for ex. <title>).
      filtr = docsum.find(filterType)
      if not filtr or not filtr.text:
        print('No %s filter tag found for %s %s' \
            % (filterType, accessionType, docsum.attrib['uid']), file=sys.stderr)
        continue
      if filterValue not in filtr.text:
        continue
    for acc in accns:
      accessions.add(acc.text)
  return accessions

#enter a database and search terms, and output
# found accessions to a given file
def getAccessionsFromSearch(database, accessionType, terms,
    esearchOutput, esummaryOutput, filterType=None, filterValue=None, overwrite=True):
  accessions = set()
  #saves esearch to file
  getEsearch(database, terms, esearchOutput, overwrite=overwrite)
  #parses params linking to eSummary from esearch file
  try:
    (queryKey, webEnv) = parseEsearch(esearchOutput)
    #saves esummary results xml file
    getEsummary(database, queryKey, webEnv, esummaryOutput, overwrite=overwrite)
    #parses esummary for accession ids and returns them
    accessions = parseEsummary(esummaryOutput, accessionType, filterType, filterValue)
  except Exception:
    print('Error: getAccessionsFromSearch failed, returning empty array')
  return accessions

def __main__(argv):
  esearchOutput = argv[1]
  (queryKey, webEnv) = parseEsearch(esearchOutput)
  print('querykey, webenv : (%s, %s)' % (queryKey, webEnv))

if __name__ == '__main__':
  __main__(sys.argv)
