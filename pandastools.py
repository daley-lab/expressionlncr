#!/usr/bin/env python3
# Convenience functions for working with pandas.
#

import pandas as pd


def mask(dataframe, key, value):
  return dataframe[dataframe[key] == value]

#this recursive function is because comparing columns to a list of values as 
# below doesn't work in pandas:
#    df[df.key in [some, values, here]]
#
#df = DataFrame, a pandas data type.
#values = [] of acceptable values to OR filter on.
def maskValues(df, key, values):
  while len(values) > 0:
    value = values.pop()
    df = df.mask(key, value)
  return df

pd.DataFrame.mask = mask
