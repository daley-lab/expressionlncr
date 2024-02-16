#!/usr/bin/env python3
# Grabs lncRNA BED file annotated with chrloc etc. from an online datasource.

import getopt
import operator
import sys
import shutil

#local
import downloader
import ziptools
import constants as c

#gets the BED file from lncipedia.org
def getLncipedia(organism, version, highconf, output):
  baseurl = 'http://lncipedia.org/downloads/lncipedia_'
  url = baseurl + version.replace('.', '_')  #e.g. 3.1 changes to 3_1
  if highconf:
    url += '_hc'
  url += '.bed'
  print('Getting BED file from LNCipedia @ ' + url + ' ...')
  downloader.simpleDownload(url, output)

#gets a gzipped BED file from noncode.org and decompresses it.
def getNoncode(organism, year, output):
  baseurl = 'http://www.noncode.org/datadownload/NONCODE' + year + '_'
  url = baseurl + organism + '.lncAndGene.bed.tgz'
  print('Getting BED file from NONCODE @ ' + url + ' ...')
  zippedOutput = output + '.tgz'
  downloader.simpleDownload(url, zippedOutput)
  print('Unzipping %s to %s ...' % (zippedOutput, output))
  ziptools.untargz(zippedOutput, output)

def usage(defaults):
  print('Usage: ' + sys.argv[0] + ' [-l, --lncipedia | -n, --noncode | -c, --custom-bed <BED_INPUT>] (--high-conf) -o, --organism <ORGANISM> <BED_OUTPUT>')
  print('Example: ' + sys.argv[0] + ' --noncode --organism hg38 noncode_lncrnas.bed')
  print('Defaults:')
  for (key, val) in sorted(iter(defaults.items()), key=operator.itemgetter(0)):
    print('%s - %s' % (str(key), str(val)))

def __main__():
  shortOpts = 'hlnc:o:'
  longOpts = ['help', 'lncipedia', 'noncode', 'custom-bed=', 'organism=', 'high-conf']
  defaults = c.GET_LNCRNA_DEFAULTS
  mode = defaults['mode']
  organism = defaults['organism']
  output = defaults['output']
  highconf = defaults['highconf']
  version = defaults['version']  #lncipedia.org version
  year = defaults['year']  #noncode.org yearly bulk download version
  bedInput = None
  try:
    opts, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
  except getopt.GetoptError as err:
    print(str(err), file=sys.stderr)
    usage(defaults)
    sys.exit(2)
  for opt, arg in opts:
    if opt in ('-h', '--help'):
      usage(defaults)
      sys.exit()
    elif opt in ('-l', '--lncipedia'):
      mode = 'lncipedia'
    elif opt in ('-n', '--noncode'):
      mode = 'noncode'
    elif opt in ('-c', '--custom-bed'):
      mode = 'custom'
      bedInput = arg
    elif opt in ('-o', '--organism'):
      organism = arg
    elif opt in ('--high-conf'):
      highconf = True
  if len(args) > 0:
    output = args[0]
  print('Called with these args: %s, %s, %s, %s, %s, %s, %s' % (mode, organism, output, highconf, version, year, bedInput))
  if mode == 'lncipedia':
    getLncipedia(organism, version, highconf, output)
  elif mode == 'noncode':
    getNoncode(organism, year, output)
  else:
    shutil.copy(bedInput, output)

if __name__ == '__main__':
  __main__()
