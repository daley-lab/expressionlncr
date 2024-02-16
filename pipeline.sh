#!/bin/bash
# ExpressionLncr example pipeline steps.
# Note: recommended to *not* run all at once the first time on a machine;
#  instead make sure things work correctly at each step.
STARTTIME=`date`
echo "Started ExpressionLncr pipeline @ $STARTTIME..."
./get_lncrna.py
./get_ensembl_probes.py
mv data/lncrnas.bed data/lncrnas.unsorted.bed
mv data/probes.bed data/probes.unsorted.bed
# sort the bed files to speed up the next step.
sort -k1,1 -k2,2n data/lncrnas.unsorted.bed > data/lncrnas.bed
sort -k1,1 -k2,2n data/probes.unsorted.bed > data/probes.bed
# -d flag is short for --input-sorted.
# speeds up step by assuming the input bed files are sorted.
./find_overlap.py -d
# -k flag is short for --skip-series-info.
# speeds up step by not downloading info on series matrix file sizes.
# note: use -s flag to include all GEO Series not just DataSets.
./find_geo_dataseries.py -k
./get_geo_dataseries.py
./parse_geo_dataseries.py
ENDTIME=`date`
echo "Done @ $ENDTIME"
