#!/usr/bin/env python2
# wraps urllib2 functions with a user agent spoof to circumvent anti-crawling behaviour
# of some sites.


import errno
import re
import os
import sys
import urllib.request, urllib.error, urllib.parse


#pass in url to file to download, and the output (optionally including directories 
# to create above file)
def simpleDownload(url, output):
  #download the whole file into memory
  user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0'
  headers = {'User-Agent': user_agent} 
  request = urllib.request.Request(url, None, headers)
  response = urllib.request.urlopen(request)
  data = response.read()
  #create any missing directories in the output path
  createPathToFile(output)
  #write the file to dirname
  with open(output, 'wb') as f:
    f.write(data)

#pass in a file and create the missing directories to the file if any.
#n.b.: directories must have a trailing '/' slash to be recognised.
# else os.path.dirname thinks it's passed a non-existant file.
def createPathToFile(output):
  dirname = os.path.dirname(output)
  if dirname and not os.path.exists(dirname):
    print('Creating directories: ' + dirname + ' ...')
    try:
      os.makedirs(dirname)
    except OSError as err:
      if err.errno != errno.EEXIST:
        print('Could not create directory for file at: ' + dirname, file=sys.stderr)
        raise err

def remove(removefile):
  try:
    os.remove(removefile)
  except OSError as err:
    if err.errno != errno.ENOENT:
      print('Could not remove file at: ' + removefile, file=sys.stderr)
      raise err

#returns content instead of writing to a file
def getUrl(url):
  user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0'
  headers={'User-Agent': user_agent} 
  request = urllib.request.Request(url, None, headers)
  response = urllib.request.urlopen(request)
  data = response.read()
  return data

#returns list of files and file sizes for a folder specified by the url.
#not tested for files with spaces in names.
#format returned from urllib/ftplib is like:
#-r--r--r--   1 ftp      anonymous  1963270 May  7 14:25 GSE10000-GPL1261_series_matrix.txt.gz
def getFolderInfo(url):
  info = {}  #map of name to size
  sizeCol = 4  # file size in bytes @ 5th column
  nameCol = 8  # file name @ column @ 9th column
  data = getUrl(url)
  #reconstruct lines from the retrieved data
  lines = re.split('\n', data)
  for line in lines:
    #ignore empty lines
    if line:
      #split the line contents by whitespace.
      cols = re.split('\s+', line)
      if len(cols) <= nameCol or len(cols) <= sizeCol:
        print('python2 urllib / ftplib returning unexpected FTP ' + \
        'contents format @ downloader.getFolderInfo()', file=sys.stderr)
        print('url: %s' % url, file=sys.stderr)
        err = Exception()
        raise err
      else:
        size = cols[sizeCol]
        name = cols[nameCol]
        info[name] = size
  return info

def __main__():
  ftp = 'ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE10nnn/GSE10000/matrix/'
  info = getFolderInfo(ftp)
  print(info)

if __name__ == '__main__':
  __main__()
