#!/usr/bin/env python2
# Script to evaluate the chromosome positional overlap between two BED files.
# Will use this to find out which lncRNAs have overlapping expression probe data.
#
# Note: ability to compare BED format files already exists in Galaxy Toolshed, 
#  unfortunately only returns a BED file of the overlap (incl. only first file in output).
#


import csv
from collections import defaultdict
import datetime
import getopt
import math
import operator
import os
import re
import sys
import shutil

#local
import arraytools
from beans import ChromFeature, Nestable
import downloader
import constants as c


#non object oriented version, to try to speed up performance.
#summary:
#1. open all the file handles.
#2. go through the input files line by line checking for overlap
#  and immediately writing out overlap if present.
#3. hope the file handle buffering in python is good.
#this approach should be faster if the performance hit is due to allocating
# objects to memory
def writeOverlap(inputA, inputB, outputA, outputB, output, chunksize):
  #remove old output files if present
  print 'deleting file %s if present...' % outputA
  downloader.remove(outputA)
  print 'deleting file %s if present...' % outputB
  downloader.remove(outputB)
  print 'deleting file %s if present...' % output
  downloader.remove(output)
  #read in the two input files
  colNames = ['chrom', 'start', 'stop', 'name', 'value', 'strand']
  usedCols = [x for x in range(0, 6)]
  print 'reading in file B (%s) to dataframe @ %s' % (inputB, str(datetime.datetime.now()))
  with open(inputB, 'rb') as inB:
    dataB = pd.read_csv(inB, header=None, sep='\t',
        names=colNames, usecols=usedCols)
  print 'reading in file A (%s) to dataframe @ %s' % (inputA, str(datetime.datetime.now()))
  with open(inputA, 'rb') as inA:
    #get number of chunks in file first
    numChunks = 0
    readerA = pd.read_csv(inA, header=None, sep='\t',
        usecols=[0], chunksize=chunksize)
    for chunkA in readerA:
      numChunks += 1
    #now read chunk by chunk and get overlap below
    inA.seek(0)
    readerA = pd.read_csv(inA, header=None, sep='\t',
        names=colNames, usecols=usedCols, chunksize=chunksize)
    chunkCount = 0
    for chunkA in readerA:
      chunkCount += 1
      print 'finding overlap for file A chunk %s/%s... @ %s' % (chunkCount, numChunks, str(datetime.datetime.now()))
      #group the input data by chromosome & strand and then search each chromosome 
      # & strand for overlap separately
      groupedA = chunkA.groupby(['chrom', 'strand'])
      groupedB = dataB.groupby(['chrom', 'strand'])
      #iterate through all the chromosomes & strands
      for (chrom, strand), subA in groupedA:
        subB = groupedB.get_group((chrom, strand))
        #sort the chromosome/strand group by start position, stop position
        a = subA.sort_values(by=['start', 'stop'], ascending=[True, True])
        b = subB.sort_values(by=['start', 'stop'], ascending=[True, True])
        #now compare the data to find overlap in start/stop position

        #4 different match cases. any case can be true for a match.
        #if ((startA < startB and startB < stopA) or   #1 i
        #    (startB < startA and startA < stopB) or   #1 ii
        #    (startA < stopB and stopB < stopA) or     #2 i
        #    (startB < stopA and stopA < startB)):     #2 ii
        #how to do this line-wise (lines in B) in pandas:
        #for index, row in b.itertuples():
        #  startB = ...
        #  stopB = ...
        #
        #  filt1 = a[(a.start < startB) & (startB < a.stop)]
        #  filt2 = a[(startB < a.start) & (a.start < stopB)]
        #  filt3 = a[(a.start < stopB) & (stopB < a.stop)]
        #  filt4 = a[(startB < a.stop) & (a.stop < startB)]
        #
        #  ... do more stuff ...
        #want to do a fully array-wise approach ideally...
        #SQL equivalent
        #select * from a join b on
        #  (a.start < b.start and b.start < a.stop) or
        #  (b.start < a.start and a.start < b.stop) or
        #  (a.start < b.stop and b.stop < a.stop) or 
        #  (b.start < a.stop and a.stop < b.stop)
        #using numpy which saves memory for at least the a < c single 
        # comparison by only getting cartesian product of a and c elements not 
        # entire dataframes (df_a and df_b)
        #ia, ib = np.where(np.less.outer(df_a.a, df_b.c))
        #pd.concat((df_a.take(ia).reset_index(drop=True), 
        #                 df_b.take(ib).reset_index(drop=True)), axis=1)

        #outer product less than comparison to compare each A to all of B.
        #NOTE need to always have A elements first to keep consistency for 
        # when we join together the different outer product boolean operations.
        startA_lt_startB = np.less.outer(a.start, b.start)
        #startB_lt_startA = np.greater.outer(a.start, b.start)  #basically redundant with 1
        startB_lt_startA = np.logical_not(startA_lt_startB)
        stopA_lt_stopB = np.less.outer(a.stop, b.stop)
        #stopB_lt_stopA = np.greater.outer(a.stop, b.stop)  #basically redundant with 3
        stopB_lt_stopA = np.logical_not(stopA_lt_stopB)
        startA_lt_stopB = np.less.outer(a.start, b.stop)
        startB_lt_stopA = np.greater.outer(a.stop, b.start)
        #create arrays of test result for each criterion
        crit1 = np.logical_and(startA_lt_startB, startB_lt_stopA)
        crit2 = np.logical_and(startB_lt_startA, startA_lt_stopB)
        crit3 = np.logical_and(startA_lt_stopB, stopB_lt_stopA)
        crit4 = np.logical_and(startB_lt_stopA, stopA_lt_stopB)
        or1 = np.logical_or(crit1, crit2)
        or2 = np.logical_or(crit3, crit4)
        matches = np.logical_or(or1, or2)
        #get indices of matches, one for first array column and one for second array column
        ia, ib = np.where(matches)
        #need to rename columns of a and b since pandas.concat doesn't do it.
        colNamesA = {}
        colNamesB = {}
        for colName in colNames:
          newNameA = '%s_x' % colName
          newNameB = '%s_y' % colName
          colNamesA[colName] = newNameA
          colNamesB[colName] = newNameB
        overlap = pd.concat((
          a.take(ia).rename(columns=colNamesA, inplace=False).reset_index(drop=True), 
          b.take(ib).rename(columns=colNamesB, inplace=False).reset_index(drop=True)), axis=1)

        #gets indices of where condition true
        #ia1, ib1 = np.where(np.less.outer(a.start, b.start))
        #ia2, ib2 = np.where(np.less.outer(b.start, a.start))  #basically redundant with 1
        #ia3, ib3 = np.where(np.less.outer(a.stop, b.stop))
        #ia4, ib4 = np.where(np.less.outer(b.stop, a.stop))  #basically redundant with 3
        #ia5, ib5 = np.where(np.less.outer(a.start, b.stop))
        #ia6, ib6 = np.where(np.less.outer(b.start, a.stop))
        #match criteria
        #(1 & 6) | (2 & 5) | (5 & 4) | (6 & 3)
        #alternatively
        #(1 & 6) | (!1 & 5) | (5 & !3) | (6 & 3)

        #using pandas filtering (NOTE much slower than above!)
        #first rename b columns to avoid collision (overwriting)
        #b.rename(columns={'old': 'new', 'old2': 'new2'}, inplace=True)
        #--> not necessary. first array is a_x, b_x, etc and second is a_y, b_y, etc.
        #df_a['ones'] = np.ones(len(df_a.index))  #df_a has an a column
        #df_b['ones'] = np.ones(len(df_b.index))  #df_b has a c column
        #cartesian = pd.merge(df_a, df_b, left_on='ones', right_on='ones')
        #cartesian[(cartesian.c > cartesian.a) & (other cond)]
        
        #add a column of ones to the dataframes
#        print 'adding columns of ones to A @ %s' % str(datetime.datetime.now())
#        a['ones'] = np.ones(len(a.index))
#        print 'adding columns of ones to B @ %s' % str(datetime.datetime.now())
#        b['ones'] = np.ones(len(b.index))
        #take the cartesian product of the arrays (every row joined on all the 
        # other rows). this will be quite large!
        # for ex. chr1/+ human: 1182840 * 8540 rows =  1M * 10k = 10B
        #FIXME currently throws memory error
#        print 'creating cartesian product of A and B @ %s' % str(datetime.datetime.now())
#        c = pd.merge(a, b, left_on='ones', right_on='ones')
#        print 'finding overlap of A and B @ %s' % str(datetime.datetime.now())
#        overlap = c[
#          ((c.start_x < c.start_y) & (c.start_y < c.stop_x)) |
#          ((c.start_y < c.start_x) & (c.start_x < c.stop_y)) |
#          ((c.start_x < c.stop_y) & (c.stop_y < c.stop_x)) |
#          ((c.start_y < c.stop_x) & (c.stop_x < c.stop_y))
#        ]
        #once we have dataframe with all the matches, write out the info
        colsA = ['%s_x' % name for name in colNames]
        colsB = ['%s_y' % name for name in colNames]
        overlap.to_csv(outputA, columns=colsA, sep='\t', header=False, mode='ab', index=False)
        overlap.to_csv(outputB, columns=colsB, sep='\t', header=False, mode='ab', index=False)
        overlap.to_csv(output, sep='\t', header=False, mode='ab', index=False)

#count up number of lines in a file
def getNumLinesInFile(filename):
  with open(filename, 'rb') as f:
    print 'counting number of lines in file %s @ %s' % (filename, datetime.datetime.now())
    total = 0
    for row in f:
      total += 1
    print ' > %s lines in file %s' % (total, filename)
    return total
  return -1
  #remember to reset file handle position if passing file handle
  #f.seek(0)

#gets positional (chromosomal) overlap of 2 bed files.
#does not consider positional overlap across strands,
# only overlap between strands is returned.
#this simple version does not have heuristics but does not rely on sorting of BED files.
def getOverlap(inputA, inputB, swap, chunksize, chromfilter, inputSorted):
  overlap = defaultdict(Nestable)
  matches = 0
  delim = c.BED_DEFAULTS['delim']
  chromCol = c.BED_DEFAULTS['chromCol']
  startCol = c.BED_DEFAULTS['startCol']
  stopCol = c.BED_DEFAULTS['stopCol']
  nameCol = c.BED_DEFAULTS['nameCol']
  strandCol = c.BED_DEFAULTS['strandCol']  #last column
  ##read all lines in file b into memory. no need to read all lines in a into memory use iterable.
  print 'counting files @ %s ...' % datetime.datetime.now()
  totalA = getNumLinesInFile(inputA)
  totalB = getNumLinesInFile(inputB)
  with open(inputA, 'rb') as a:
    with open(inputB, 'rb') as b:
      readerA = csv.reader(a, delimiter=delim)
      readerB = csv.reader(b, delimiter=delim)
      #load file B into memory
      print 'reading file B into memory @ time: %s ...' % datetime.datetime.now() 
      if chromfilter:
        print ' > including only chromosome %s' % chromfilter
      blines = {}
      try:
        for bcols in readerB:
          chrom = bcols[chromCol]
          strand = bcols[strandCol]
          if chromfilter and chrom != chromfilter:
            #this speeds up the operation significantly by loading a smaller file into memory
            continue
          #parse all the integer columns in file B at once now rather than again 
          # and again in loop over A lines below
          start = int(bcols[startCol])
          stop = int(bcols[stopCol])
          #NOTE hardcoded implementation for speed rather than a flexible implementation.
          # the BED file format is fixed and do not really expect columns to change, 
          # the variables are currently only for convenience in coding.
          newcols = [bcols[0], start, stop, bcols[3], bcols[4], bcols[5]]
          try:
            chromStrandLines = blines[chrom][strand]
          except KeyError:
            #might also not have chrom key
            try:
              blines[chrom]
            except KeyError:
              blines[chrom] = {}
            chromStrandLines = []
            blines[chrom][strand] = chromStrandLines
          finally:
            chromStrandLines.append(newcols)
      except ValueError as ve:
        #unfortunately no skipping of bad lines in this method. abort.
        print 'Error: Malformed BED file - Could not convert value to integer'
        return overlap
      #finally loop over A file lines and compute overlap for each B line.
      print 'computing overlap of file A w/ b @ time: %s ...' % datetime.datetime.now() 
      chunkCount = 1
      numChunks = int(math.ceil(totalA/float(chunksize)))
      for chunk in arraytools.getChunks(readerA, chunksize=chunksize):
        print 'processing file A, chunk %s/%s (matches so far: %s) @ %s ...' \
            % (chunkCount, numChunks, matches, datetime.datetime.now())
        chunkCount = chunkCount + 1
        for acols in chunk:
          #if acols[0][0:5] == 'track':  #to skip header line in BED file
          #  continue
          if chromfilter and chromfilter != acols[chromCol]:
            continue
          chromA = acols[chromCol]
          startA = int(acols[startCol])
          stopA = int(acols[stopCol])
          strandA = acols[strandCol]
          nameA = acols[nameCol]
          #iterate through all lines in file B to find matches. do not exploit positional sorting.
          #declare some variables more locally for possible improved performance in below for loop
          inputSortedLocal = inputSorted
          swapLocal = swap
          try:
            for bcols in blines[chromA][strandA]:
              #input B file is sorted
              if inputSortedLocal:  #TODO possibly force sorting to remove this if statement
                #test if B elements start after A, if so break to next A
                if stopA < bcols[1]:
                  break
              #test if position of B is completely before/after A, if so then skip.
              #runs 2 more logical operations for matched values but 6 fewer for unmatched.
              if (bcols[2] < startA) or (stopA < bcols[1]):
                continue
              #test if strand matches
              #if strandA == strandB
              #test for positional overlap:
              #case 1. one of the element starts is within the other
              #     i) startB is within A
              #    ii) startA is withpin B
              #case 2. one of the element stops is within the other
              #     i) stopB is within A
              #    ii) stopA is within B
              #note: we don't care to distinguish b/w completely and 
              # partially contained elements, currently.
              if ((startA < bcols[1] and bcols[1] < stopA) or   #1 i
                  (bcols[1] < startA and startA < bcols[2]) or   #1 ii
                  (startA < bcols[2] and bcols[2] < stopA) or     #2 i
                  (bcols[1] < stopA and stopA < bcols[2])):     #2 ii
                matches += 1
                #we have a match
                #create feature A
                featureA = ChromFeature(chrom=chromA, start=startA, stop=stopA, \
                    strand=strandA, name=nameA)
                #create feature B
                chromB = bcols[0]
                startB = bcols[1]
                stopB = bcols[2]
                nameB = bcols[3]
                strandB = bcols[5]
                featureB = ChromFeature(chrom=chromB, start=startB, stop=stopB, \
                    strand=strandB, name=nameB)
                #design appropriate element as key feature
                keyFeature = featureA if swapLocal else featureB
                keyFeatureName = keyFeature.name
                childFeature = featureB if swapLocal else featureA
                #try speeding up creation of new match and adding to dictionary.
                #use a defaultdict with a local Nestable() factory.
                #might be faster than try/except.
                match = overlap[keyFeatureName]
                if not match.parent:
                  match.parent = keyFeature
                #try dict for performance
                match.children[nameB] = childFeature
          except KeyError:
            continue
  return overlap

#output file format - 
#XML:
#<a>
# <chr>String -> chr1, chrY, ...</chr>
# <start>Integer</start>
# <stop>Integer</stop>
# <name>String -> e.g. probe if not swap, lncRNA if swap</name>
# <b>
#  <chr>String -> chr1, chrY, ...</chr>
#  <start>Integer</start>
#  <stop>Integer</stop>
#  <name>String -> e.g. lncrna if not swap, probe if swap (array/probeset:probe)</name>
# </b>
# <b>...</b>
# ...
#</a>
#<a>...</a>
#...
#
def createOverlapOutput(overlap, outputName, swap):
  delim = '\t'
  #ensure directories to output file are created
  print 'creating path to file ' + outputName + ' @ time: ' + str(datetime.datetime.now())
  downloader.createPathToFile(outputName)
  #delete file at output if already present. open(f, 'wb') should erase it for us but it's 
  # appending for some strange reason.
  print 'removing ' + outputName + ' if present...'
  downloader.remove(outputName)
  print 'start writing output time: ' + str(datetime.datetime.now())
  with open(outputName, 'wb') as output:
    header = '<!DOCTYPE overlapResult>\n<overlap>\n'
    output.write(header)
    #for consistency later on in the pipeline just always have <a><b></b></a>
    # regardless of swap
    parentTag = 'a'
    childTag = 'b'
    for (key, match) in overlap.iteritems():
      par = match.parent
      startPar = '<%s>\n\t<chr>%s</chr>\n\t<start>%s</start>\n\t<stop>%s</stop>\n\t<strand>%s</strand>\n\t<name>%s</name>\n' % (
          parentTag, par.chrom, par.start, par.stop, par.strand, par.name
        )
      output.write(startPar)
      for (name, child) in match.children.iteritems():
        childString = '\t<%s>\n\t\t<chr>%s</chr>\n\t\t<start>%s</start>\n\t\t<stop>%s</stop>\n\t\t<strand>%s</strand>\n\t\t<name>%s</name>\n\t</%s>\n' % (
            childTag, child.chrom, child.start, child.stop, child.strand, child.name, childTag
          )
        output.write(childString)
      endPar = '</%s>\n' % parentTag
      output.write(endPar)
    footer = '</overlap>'
    output.write(footer)
  print 'done writing output @ time: ' + str(datetime.datetime.now())

#output BED file from ChromFeature array
def createBedFromChromFeatures(chromFeatures, outputName, delim='\t', writeHeader=False):
  #create output directory
  print 'creating path to file ' + outputName + ' @ time: ' + str(datetime.datetime.now())
  downloader.createPathToFile(outputName)
  #and remove output file if already present
  print 'removing ' + outputName + ' if present...'
  downloader.remove(outputName)
  #write out the file
  print 'start writing features file @ time: ' + str(datetime.datetime.now())
  with open(outputName, 'wb') as output:
    if writeHeader:
      header = '#Chromosome%sStart%sStop%sName%sScore%sStrand\n' % \
          (delim, delim, delim, delim, delim)
      output.write(header)
    for f in chromFeatures:
      line = '%s%s%s%s%s%s%s%s0%s%s\n' % (
          f.chrom, delim, f.start, delim, f.stop, delim, f.name, delim, delim, f.strand
      )
      output.write(line)
  print 'done writing features file @ time: ' + str(datetime.datetime.now())

def usage(defaults):
  print 'Usage: ' + sys.argv[0] + \
      ' -a, --input-a <BED_INPUT_A> -b, --input-b <BED_INPUT_B> -A,' + \
      ' --output-a <OVERLAP_A_OUTPUT> -B, --output-b <OVERLAP_B_OUTPUT>' + \
      ' -d, --input-sorted ' + \
      ' -c, --chr <CHROMOSOME> -s, --swap <XML_OUTPUT>\n'
  print 'Example: ' + sys.argv[0] + \
      ' -a data/ensembl_probe_features.bed -b data/noncode_lncrnas.bed data/overlap.xml\n'
  print 'Defaults:'
  for key, val in sorted(defaults.iteritems(), key=operator.itemgetter(0)):
    print str(key) + ' - ' + str(val)
  print '\nOptions:\n'
  print '-s, --swap\n\tSwap the XML hierarchy of the output overlap XML file. ' + \
    'Default, unswapped, is elements like <B><A></A></B>.\n'
  print '-d, --input-sorted\n\tSpecify that input B file is sorted by chromosome, ' + \
    'then start position. Program will assuming sorting to speed up algorithm. ' + \
    'Can be done using: sort -k1,1 -k2,2n <INPUT> > <OUTPUT>. ' + \
    'Defaults to unsorted.\n'
  print 'IMPORTANT:'
  print '-There *must* be enough system memory to load file B into memory'
  print '-This implies you should specify the larger file as file A\n'

def __main__():
  shortOpts = 'ha:b:A:B:o:c:z:sdp'
  longOpts = ['help', 'input-a=', 'input-b=', \
      'output-a=', 'output-b=', 'output=', 'chromosome=', \
      'chunksize=', 'swap', 'input-sorted', 'pandas-pipeline']
  defaults = c.FIND_OVERLAP_DEFAULTS
  chunksize = defaults['chunksize']
  chromosome = defaults['chromosome']
  inputA = defaults['inputA']
  inputB = defaults['inputB']
  outputA = defaults['outputA']
  outputB = defaults['outputB']
  output = defaults['output']
  swap = defaults['swap']
  inputSorted = defaults['inputSorted']
  pandasPipeline = defaults['pandasPipeline']
  try:
    opts, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
  except getopt.GetoptError as err:
    print str(err)
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
    elif opt in ('-z', '--chunksize'):
      chunksize = int(arg)
    elif opt in ('-c', '--chromosome'):
      chromosome = arg
    elif opt in ('-s', '--swap'):
      swap = not swap
    elif opt in ('-d', '--input-sorted'):
      inputSorted = not inputSorted
    elif opt in ('-p', '--pandas-pipeline'):
      pandasPipeline = not pandasPipeline
  if len(args) > 0 and output == defaults['output']:
    #only assume first argument is output if user didn't specify an --output arg
    output = args[0]
  print 'getting overlap b/w BED files @ time: ' + str(datetime.datetime.now())
  if pandasPipeline:
    import pandas as pd
    import numpy as np
    print 'using pandas pipeline'
    #a non-object oriented pipeline in pandas. unfortunately, much slower atm.
    writeOverlap(inputA, inputB, outputA, outputB, output, chunksize)
  else:
    #pipeline
    overlap = getOverlap(inputA, inputB, swap, chunksize, chromosome, inputSorted)
    print 'found %s elements in file A with matches in file B' % len(overlap.keys())
    print 'creating overlap output file @ time: ' + str(datetime.datetime.now())
    createOverlapOutput(overlap, output, swap)
    print 'creating chrom feature A output file @ time: ' + str(datetime.datetime.now())
    #if swap:
    # -parent features are of element A
    # -child features are of element B
    #else:
    # -the reverse
    parentFeatures = [match.parent for (key, match) in overlap.iteritems()]
    createBedFromChromFeatures(parentFeatures, outputA if swap else outputB)
    print 'creating chrom feature B output file @ time: ' + str(datetime.datetime.now())
    childFeatures = []
    for (key, match) in overlap.iteritems():
      for (name, child) in match.children.iteritems():
        childFeatures.append(child)
    createBedFromChromFeatures(childFeatures, outputB if swap else outputA)
    print 'done ' + sys.argv[0] + ' @ time: ' + str(datetime.datetime.now())

if __name__ == '__main__':
  __main__()
