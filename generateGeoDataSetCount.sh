#!/bin/bash
#

numlines=( 10 100 1000 10000 )
repeats=3

#numlines=( 100000 )
#repeats=1

echo 'start'
for N in "${numlines[@]}"; do
  for M in `seq 1 $repeats`; do
    date
    echo "get number GEO datasets overlap for: $N lines, file ${M}..."
    python find_geo_dataseries.py --esearch "data/matrices/summary.txt.esearch.${N}.${M}" --esummary "data/matrices/summary.txt.esummary.${N}.${M}" --get-platforms-from-overlap "data/probeFiles/${N}_lines_${M}_iter.probes.overlap.bed" --info-output "data/matrices/summary.txt.${N}.${M}" --series-output "data/matrices/series.txt.${N}.${M}"
  done
done
date
echo 'done'
