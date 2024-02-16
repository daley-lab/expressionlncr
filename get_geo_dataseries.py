#!/usr/bin/env python3
#
# script to grab NCBI GEO data series matrix files from FTP server 
# given the GEO data series IDs.
# may take a long time depending on download rate and series given to tool.
#
# path to series matrix like:
# ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE30nnn/GSE30000/matrix/GSE30000_series_matrix.txt.gz
#
# or for multiple platforms per data series like:
# ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE10nnn/GSE10000/matrix/GSE10000-GPL1261_series_matrix.txt.gz
# ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE10nnn/GSE10000/matrix/GSE10000-GPL8321_series_matrix.txt.gz


import datetime
import getopt
import operator
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

#local
import downloader
import geotools
import constants as c


#downloads each data series matrix file if present from the FTP server.
#ex urls:
# (A) single platform per series
# ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE30nnn/GSE30000/matrix/GSE30000_series_matrix.txt.gz
# (B) multiple platforms per series
# ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE10nnn/GSE10000/matrix/GSE10000-GPL1261_series_matrix.txt.gz
#
#NOTE this function doesn't have an option to skip retrieving folder info if a GSE1234_series_matrix.txt.gz
# file already exists because several GEO Series have multiple series matrix files. However, for each 
# matrix file retrieved by the query for FTP folder info, if the file already exists at the output path
# the actual file download is skipped.
#
# As downloads are made, completed and skipped series are written out to files 
# so that progress is saved if interrupted. Again, cannot infer that just because some file
# GSE1234_series_matrix.txt.gz exists in our matrices/ folder that we have completed downloads for that
# series because several GEO Series have multiple series matrix files.
#
def downloadSeriesMatrixFiles(seriesIds, outputDir, ftp, skippedSeriesFile, completedSeriesFile):
  #create path to output directory if it doesn't exist.
  # add trailing slash to make sure recognised as directory.
  downloader.createPathToFile('%s/' % outputDir)
  print('Downloading series matrix files to: %s ...' % outputDir)
  print('Started downloads @ %s' % str(datetime.datetime.now()))
  #check which series passed have already been downloaded
  completedSeries = set()
  try:
    completedSeries = geotools.parseSeriesIdFile(completedSeriesFile)
  except IOError:
    #no existing file, create
    print('No completed series file %s, creating ...' % completedSeriesFile)
    with open(completedSeriesFile, 'w') as csf:
      csf.write('')
  if len(completedSeries) > 0:
    print('Skipping downloads for following series (already complete): %s ...' % (','.join(completedSeries)))
  #check which series have already been skipped. read into a set so we don't write
  # multiple of the same series to the skipped file if the download is resumed.
  skippedSeries = set()
  try:
    skippedSeries = geotools.parseSeriesIdFile(skippedSeriesFile)
  except IOError:
    #no existing file, create
    print('No skipped series file %s, creating ...' % skippedSeriesFile)
    with open(skippedSeriesFile, 'w') as ssf:
      ssf.write('')
  #download all matrix files for series that haven't been downloaded already
  seriesToDownload = set(seriesIds).difference(completedSeries)
  with open(completedSeriesFile, 'ab') as completeFile:
    with open(skippedSeriesFile, 'ab') as skipFile:
      count = 0
      numSeries = len(seriesToDownload)
      for series in sorted(seriesToDownload):
        count += 1
        print('downloading data for series %s (%s/%s) @ %s ...' % (
            series, count, numSeries, str(datetime.datetime.now())
        ))
        seriesDir = geotools.getSeriesDirFromGSE(series)  #ex GSE10nnn
        ftpFolder = '%s/%s/GSE%s/matrix/' % (ftp, seriesDir, series)
        matrixFiles = []
        downloadError = None
        try:
          #get a map of all files -> size in the matrix/ folder for this data series.
          #NOTE pass folder with slash at end to this method.
          folderInfo = downloader.getFolderInfo(ftpFolder)
          #restrict to only series matrix files
          for f in list(folderInfo.keys()):
            if f.endswith('series_matrix.txt.gz'):
              matrixFiles.append(f)
          for matrixFile in matrixFiles:
            url = '%s/%s' % (ftpFolder, matrixFile)
            output = '%s/%s' % (outputDir, matrixFile)
            #don't download again if file already at location
            if not os.path.isfile(output):
              try:
                downloader.simpleDownload(url, output)
                print('%s > %s' % (url, output))
              except urllib.error.URLError as ue:
                #matrix file not present for the series
                print('Error: Could not download series matrix file %s for GSE%s' % (url, series))
                downloadError = ue
            else:
              print('skipped (already exists) %s > %s' % (url, output))
          if downloadError:
            raise downloadError
          completeFile.write('%s\n' % series)
        except urllib.error.URLError as ue:
          #we couldn't get folder info at all for the series
          print(ue, file=sys.stderr)
          print('Error: Could not download series matrix file(s) for GSE%s, skipping...' % series)
          if series not in skippedSeries:
            skippedSeries.add(series)
            skipFile.write('%s\n' % series)
      print('Finished downloads @ %s' % str(datetime.datetime.now()))

def usage(defaults):
  print('Usage: ' + sys.argv[0] + \
      ' (-i, --input <INPUT> | -s, --series X,Y,Z) -o, --output <OUTPUT> -k, --skipped-series <SKIPPED>')
  print('Example: ' + sys.argv[0] + ' -i data/matrices/series.txt -s GSE10000,GSE20000 -o data/matrices')
  print('Defaults:')
  for key, val in sorted(iter(defaults.items()), key=operator.itemgetter(0)):
    print(str(key) + ' - ' + str(val))

def __main__():
  shortOpts = 'hf:i:o:s:k:c:'
  longOpts = ['help', 'ftp=', 'input=', 'output=', 'series=', 'skipped-series-file=', 'completed-series-file=']
  defaults = c.GET_GEO_DATASERIES_DEFAULTS
  ftp = defaults['ftp']
  inputFile = defaults['input']
  skippedSeriesFile = defaults['skippedSeriesFile']
  completedSeriesFile = defaults['completedSeriesFile']
  output = defaults['output']
  series = defaults['series']
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
    elif opt in ('-i', '--input'):
      inputFile = arg
    elif opt in ('-o', '--output'):
      output = arg
    elif opt in ('-s', '--series'):
      series = arg
    elif opt in ('-k', '--skipped-series-file'):
      skippedSeriesFile = arg
    elif opt in ('-c', '--completed-series-file'):
      completedSeriesFile = arg
  seriesIds = geotools.getSeriesIds(inputFile, series)
  if not seriesIds:
    print('No GEO series IDs passed to download. Nothing to do, quitting...', file=sys.stderr)
    sys.exit(2)
  downloadSeriesMatrixFiles(seriesIds, output, ftp, skippedSeriesFile, completedSeriesFile)

if __name__ == '__main__':
  __main__()
