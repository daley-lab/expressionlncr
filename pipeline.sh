#!/bin/bash
# ExpressionLncr example pipeline steps.
# Note: recommended to *not* run all at once the first time on a machine;
#  instead make sure things work correctly at each step.
STARTTIME=`date`
echo "Started ExpressionLncr pipeline @ $STARTTIME..."
./get_lncrna.py
./get_ensembl_probes.py
./find_overlap.py
# -k flag is short for --skip-series-info.
# speeds up step by not downloading info on series matrix file sizes.
# note: use -s flag to include all GEO Series not just DataSets.
./find_geo_dataseries.py -k
./get_geo_dataseries.py
./parse_geo_dataseries.py
ENDTIME=`date`
echo "Done @ $ENDTIME"
