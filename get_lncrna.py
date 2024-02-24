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
def getLncipedia(version, highconf, output):
  # Examples:
  #  https://lncipedia.org/downloads/lncipedia_5_2/full-database/lncipedia_5_2_hg38.bed
  #  https://lncipedia.org/downloads/lncipedia_5_2/high-confidence-set/lncipedia_5_2_hc_hg38.bed
  baseurl = 'https://lncipedia.org/downloads/'
  versionString = version.replace('.', '_')  #e.g. 3.1 changes to 3_1
  lncipediaString = 'lncipedia_' + versionString
  url = baseurl + lncipediaString
  if highconf:
    url += '/high-confidence-set/' + lncipediaString + '_hc'
  else:
    url += '/full-database/' + lncipediaString
  url += '_hg38.bed'
  print('Getting BED file from LNCipedia @ ' + url + ' ...')
  downloader.simpleDownload(url, output)

#gets a gzipped BED file from noncode.org and decompresses it.
def getNoncode(organism, versionString, output):
  baseurl = 'http://www.noncode.org/datadownload/NONCODE' + versionString + '_'
  url = baseurl + organism + '.lncAndGene.bed.gz'
  print('Getting BED file from NONCODE @ ' + url + ' ...')
  zippedOutput = output + '.gz'
  downloader.simpleDownload(url, zippedOutput)
  print('Unzipping %s to %s ...' % (zippedOutput, output))
  ziptools.gunzip(zippedOutput, output)

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
  lncipediaVersion = defaults['lncipediaVersion']  #lncipedia.org version
  noncodeVersion = defaults['noncodeVersion']  #noncode.org version
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
  print('Called with these args:\nmode=%s\norganism=%s\noutput=%s\nhighconf=%s\nlncipediaVersion=%s\nnoncodeVersion=%s\nbedInput=%s' % \
        (mode, organism, output, highconf, lncipediaVersion, noncodeVersion, bedInput))
  if mode == 'lncipedia':
    getLncipedia(lncipediaVersion, highconf, output)
  elif mode == 'noncode':
    getNoncode(organism, noncodeVersion, output)
  else:
    shutil.copy(bedInput, output)
  print('If you wish to sort the BED file by chromosome and start pos, try running:\n')
  print('\tsort -k1,1 -k2,2n %s > data/lncrna.sorted.bed\n' % output)

if __name__ == '__main__':
  __main__()
