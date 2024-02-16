#!/usr/bin/env python3
#functions for working with human chromosomes or 
# organisms with fewer chromosomes than humans

from types import IntType, StringType


def stringify(chromint, ishuman):
  assert type(chromint) is IntType, 'need to pass integer to stringify(int)'
  chromstring = str(chromint)
  if ishuman:
    assert (chromint >= 1 and chromint <= 25), 'valid human chromosomes are from 1..25'
    if chromint == 23:
      chromstring = 'X'
    elif chromint == 24:
      chromstring = 'Y'
    elif chromint == 25:
      chromstring = 'MT'
  return chromstring

def intify(chromstring, ishuman):
  assert type(chromstring) is StringType, 'need to pass string to intify(string)'
  chromint = None
  if ishuman:
    if chromstring == 'X':
      chromint = 23
    elif chromstring == 'Y':
      chromint = 24
    elif chromstring.startswith('M'):
      chromint = 25
  if not chromint:
    #throws ValueError if invalid
    chromint = int(chromstring)
  return chromint
