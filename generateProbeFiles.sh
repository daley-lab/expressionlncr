#!/bin/bash
#generate M files of N random lines from input file

numlines=( 10 100 1000 10000 )
repeats=3

#numlines=( 100000 )
#repeats=1

for N in "${numlines[@]}"; do
  for M in `seq 1 $repeats`; do
    echo "$N lines, file $M"
    shuf -n $N "data/probeFiles/probes.bed" > "data/probeFiles/${N}_lines_${M}_iter.out.bed"
  done
done
