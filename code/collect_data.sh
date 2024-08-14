#!/bin/bash

set -eu

mdate=${1:-`date +"20%y%m%d"`}


Y=${mdate:0:4}
M=${mdate:4:2}
D=${mdate:6:2}
ISODATE=$Y-$M-$D

echo "Collecting data for mdate=$mdate (AKA $ISODATE)"

mkdir -p "ses-$mdate"
cd "ses-$mdate"

mkdir -p {DICOMS,birch,psychopy,reproevents,reprostim-videos}

rsync -a bids@rolando.cns.dartmouth.edu:/inbox/DICOM/$Y/$M/$D/birchtest/* DICOMS/
rsync -a /home/yoh/proj/repronim/reprostim/Examples/exp-alpha/code/{${mdate}*log,qr_code_flips.py} psychopy/
ssh birch "grep -h '\<${ISODATE}T' /mnt/td/*" >| birch/out.jsonl
if [ ! -s "birch/out.jsonl" ]; then
    echo "ERROR: nothing from birch!"
fi

# figure out which file has it first and then grep from all files records
ssh reprostim@reproiner "cd reprostim/Events/data && grep -l '\<${ISODATE}T' *.csv | head -n 1 | xargs head -n 1 && grep '\<${ISODATE}T' *.csv" > reproevents/events.csv

# only those for which we fetch data, we get them
cp --reflink=auto `find ~/proj/repronim/reprostim-reproiner/Videos/$Y/$M -size +100 -iname "$Y.$M.$D.*"` reprostim-videos/