#!/bin/bash
#generate M files of N random lines from input file

#numlines=( 10 100 1000 10000 )
#repeats=3

numlines=( 100000 )
repeats=1

echo 'start'
for N in "${numlines[@]}"; do
  for M in `seq 1 $repeats`; do
    date
    echo "finding overlap for: $N lines, file ${M}..."
    python find_overlap.py -a "data/probeFiles/${N}_lines_${M}_iter.out.bed" -b data/lncrnas.bed -A "data/probeFiles/${N}_lines_${M}_iter.probes.overlap.bed" -B "data/probeFiles/${N}_lines_${M}_iter.lncrnas.overlap.bed" "data/probeFiles/${N}_lines_${M}_iter.overlap.xml"
  done
done
date
echo 'done'
