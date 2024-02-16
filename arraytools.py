#!/usr/bin/env python
# functions for working with arrays
#


import itertools
import sys


#returns list as chunks of chunksize.
#
#use as:
#for chunk in getChunks(iterable, chunksize=50000):
#  ...
#  del chunk
def getChunks(iterable, chunksize=50000):
  #make an iterator over the iterable
  it = iter(iterable)
  #make sure the chunksize is an integer
  size = int(chunksize)
  while True:
    #get an iterator containing size elements of it.
    #make it a tuple.
    #this is necessary in order to know when the iterator it has been exhausted.
    chunk = tuple(itertools.islice(it, size))
    if not chunk:
      #it exhausted so break out of generator
      break
    #yield next chunk from this generator
    yield chunk

def __main__(argv):
  for chunk in getChunks(list(range(0,100)), chunksize=10):
    for c in chunk:
      print(c)

if __name__ == '__main__':
  __main__(sys.argv)
