#!/usr/bin/env python3
# Some complex data types for the scripts

import sys
from dataclasses import dataclass


'''
class Probe(object):
  def __init__(self, probeId=None, probeSetName=None, name=None, arrayChipId=None, arrayName=None):
    self.probeId = probeId
    self.probeSetName = probeSetName
    self.name = name
    self.arrayChipId = arrayChipId
    self.arrayName = arrayName
'''
@dataclass(frozen=True)
class Probe:
  probeId: str = None
  probeSetName: str = None
  name: str = None
  arrayChipId: str = None
  arrayName: str = None


'''
class ChromFeature(object):
  def __init__(self, chrom=None, start=None, stop=None, strand=None, name=None):
    self.chrom = chrom
    self.start = start
    self.stop = stop
    self.strand = strand
    self.name = name

  #equality based on name and type/none-ness only
  def __eq__(self, other):
    if type(other) is type(self):
      if not self and not other:
        return True
      elif self and other and (not self.name and not other.name):
        return True
      elif self and self.name and other and other.name:
        return self.name == other.name
      else:
        return False
    else:
      return False

  def __neq__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash(self.name)

  def toString(self):
    string = '%s\t%s\t%s\t%s\t0\t%s' % (str(self.chrom), str(self.start), \
        str(self.stop), str(self.name), str(self.strand))
    return string
'''
@dataclass(frozen=True)
class ChromFeature:
  chrom: str = None
  start: str = None
  stop: str = None
  strand: str = None
  name: str = None


'''
class ProbeExpression(object):
  def __init__(self, probe=None, probeChromFeat=None, gpl=None, gse=None, maxVal=None):
    self.probe = probe
    self.probeChromFeat = probeChromFeat
    self.gpl = gpl
    self.gse = gse
    self.maxVal = maxVal
'''
@dataclass(frozen=True)
class ProbeExpression:
  probe: str = None
  probeChromFeat: ChromFeature = None
  gpl: str = None
  gse: str = None
  maxVal: float = None


class Nestable(object):
  def __init__(self, parent=None, children=None):
    self.parent = parent
    if children:
      self.children = children
    else:
      self.children = {}


def __main__(argv):
  probeA = Probe()
  probeA.probeId = '1234'
  probeA.name = 'bar_at'
  probeA.arrayChipId = '65'
  probeA.arrayName = 'FooArray-123'
  probeA.probeSetName = ''
  probeB = Probe('0', 'fooset', '1234_at', '23', 'BarArray')
  featA = ChromFeature('chr1', 0, 9999, '+', 'Feat_a12')
  featB = ChromFeature('chr1', 555, 777, '+', 'Feat_b23')
  matchA = Nestable()
  matchA.parent = featA
  matchA.children[featB.name] = featB
  print(probeA)
  print(probeB)
  print(featA)
  print(featB)
  print(matchA.parent)
  print(matchA.children)


if __name__ == '__main__':
  __main__(sys.argv)
