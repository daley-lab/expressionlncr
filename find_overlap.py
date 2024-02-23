#!/usr/bin/env python3
# Script to evaluate the chromosome positional overlap between two BED files.
# Will use this to find out which lncRNAs have overlapping expression probe data.
#
# Depends on: bedtools, sort
#
# Note: in this tool both input A and input B are normalised, and both A and B have overlap files output.
#  But in the lncRNA + probe overlap workflow, only lncRNAs need to be normalised, and only probes need a 
#  separate overlap file.
#

import datetime
import getopt
import operator
import os
import re
import sys
import subprocess as sub

#local
import constants as c


def usage(defaults):
  print('Usage: ' + sys.argv[0] + \
      ' -a, --input-a <BED_INPUT_A> -b, --input-b <BED_INPUT_B> -A,' + \
      ' --output-a <OVERLAP_A_OUTPUT> -B, --output-b <OVERLAP_B_OUTPUT>' + \
      ' <BED_OUTPUT>\n')
  print('Example: ' + sys.argv[0] + \
      ' -a data/ensembl_probe_features.bed -b data/noncode_lncrnas.bed data/overlap.bed\n')
  print('Defaults:')
  for key, val in sorted(iter(defaults.items()), key=operator.itemgetter(0)):
    print(str(key) + ' - ' + str(val))
  print('IMPORTANT:')
  print('- bedtools and sort must be installed and on your $PATH\n')


def run(cmd: str):
  print(f'Running: {cmd} @ {datetime.datetime.now()} ...')
  sub.run(['sh', '-c', cmd])


def safePath(path: str) -> str:
  return f'{os.path.normpath(os.path.abspath(path))}'


def esc(path: str) -> str:
  return f'"{path}"'


def discardNonStdChrom(bedPath: str) -> str:
  '''
  Discards all lines in BED file where the chromosome string is non-standard i.e. not chr1, chr2, ... chrM, chrX, chrY.
  Needed because bedtools intersect complains about chromosomes with non-standard chars not being sorted lexicographically, even if they are.
  '''
  print(f'Discarding non-standard chromosomes in: {bedPath} @ {datetime.datetime.now()} ...')
  path = safePath(bedPath)
  if not path.endswith('.bed'):
    raise ValueError('Must pass valid .bed file to normalize!')
  out = os.path.splitext(path)[0] + '.stdchr.bed'
  with open(out, 'w') as output:
    with open(path, 'r') as input:
      pattern = re.compile('^chr[0-9A-Z]+$')
      for line in input:
        if not line.startswith('chr'):
          continue
        chr = line.split()[0]
        if not pattern.match(chr):
          continue
        output.write(line)
  return out


def normalizeToBed6(bed6or12path: str) -> str:
  '''
  Normalises bed12 or bed6 file at input path and writes to and returns output bed6 file.
  Requires bedtools to be on path.

  ref: https://bedtools.readthedocs.io/en/latest/content/tools/bed12tobed6.html

  Args:
    bed6or12path (str): Path to input BED file, formatted in BED-6 or BED-12 (column) format.

  Returns:
    str: Path to sorted output BED file.
  '''
  path = safePath(bed6or12path)
  if not path.endswith('.bed'):
    raise ValueError('Must pass valid .bed file to normalize!')
  out = os.path.splitext(path)[0] + '.bed6.bed'
  cmd = f'bedtools bed12tobed6 -i {esc(path)} > {esc(out)}'
  run(cmd)
  return out


def sortBed(bedPath: str) -> str:
  '''
  Sorts a BED file grouping features by chromosome alphabetically, and then by start position numerically.
  Requires unix sort command to be on path.

  Args:
    bedPath (str): Path to input BED file.

  Returns:
    str: Path to sorted output BED file.
  '''
  path = safePath(bedPath)
  if not path.endswith('.bed'):
    raise ValueError('Must pass valid .bed file to normalize!')
  out = os.path.splitext(path)[0] + '.sorted.bed'
  cmd = f'sort -k1,1 -k2,2n {esc(path)} > {esc(out)}'
  run(cmd)
  return out


def getOverlapping(inputA: str, inputB: str, output: str):
  '''
  Gets genomic features in A that overlap positions in B, writing them to output file.
  Only features in A that overlap are written out. No features in B are written to output.

  ref: https://bedtools.readthedocs.io/en/latest/content/tools/intersect.html#u-unique-reporting-the-mere-presence-of-any-overlapping-features

  Args:
    inputA (str): Path to input BED file A.
    inputB (str): Path to input BED file B.
    output (str): Path to output file to write to.
  '''
  cmd = f'bedtools intersect -a {esc(safePath(inputA))} -b {esc(safePath(inputB))} -sorted -u > {esc(safePath(output))}'
  run(cmd)


def getOverlap(inputA: str, inputB: str, output: str):
  '''
  Get overlap of genomic features in sorted BED files A and B and write the overlap out to output BED-like file.
  The output file will have one line for each overlap, first feature A columns then feature B columns.

  Important: files A and B are assumed to be sorted and this will fail if they aren't.

  ref: https://bedtools.readthedocs.io/en/latest/content/tools/intersect.html#wb-reporting-the-original-b-feature

  Args:
    inputA (str): Path to input BED file A.
    inputB (str): Path to input BED file B.
    output (str): Path to output file to write to.
  '''
  cmd = f'bedtools intersect -a {esc(safePath(inputA))} -b {esc(safePath(inputB))} -sorted -wa -wb > {esc(safePath(output))}'
  run(cmd)


def __main__():
  shortOpts = 'ha:b:A:B:o:'
  longOpts = ['help', 'input-a=', 'input-b=', 'output-a=', 'output-b=', 'output=' ]
  defaults = c.FIND_OVERLAP_DEFAULTS
  inputA = defaults['inputA']
  inputB = defaults['inputB']
  outputA = defaults['outputA']
  outputB = defaults['outputB']
  output = defaults['output']
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
    elif opt in ('-a', '--input-a'):
      inputA = arg
    elif opt in ('-b', '--input-b'):
      inputB = arg
    elif opt in ('-A', '--output-a'):
      outputA = arg
    elif opt in ('-B', '--output-b'):
      outputB = arg
    elif opt in ('-o', '--output'):
      output = arg
  if len(args) > 0 and output == defaults['output']:
    # Only assume first argument is output if user didn't specify an --output arg
    output = args[0]
  print('Getting overlap between BED files @ time: ' + str(datetime.datetime.now()))
  stdchrA = discardNonStdChrom(inputA)
  stdchrB = discardNonStdChrom(inputB)
  normalA = normalizeToBed6(stdchrA)
  normalB = normalizeToBed6(stdchrB)
  sortedA = sortBed(normalA)
  sortedB = sortBed(normalB)
  getOverlapping(sortedA, sortedB, outputA)
  getOverlapping(sortedB, sortedA, outputB)
  getOverlap(sortedA, sortedB, output)
  print('Done ' + sys.argv[0] + ' @ time: ' + str(datetime.datetime.now()))


if __name__ == '__main__':
  __main__()
