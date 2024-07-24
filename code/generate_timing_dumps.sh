#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <session_dir>"
  exit 1
fi

# Set SESSION_DIR to the first command-line argument
SESSION_DIR=$1
OUT_DIR=$SESSION_DIR/timing-dumps
LOG_LEVEL=DEBUG

echo "Generating timing dumps for session: $SESSION_DIR"
echo "Timing dumps will be saved to: $OUT_DIR"

# Create the out directory if it does not exist
if [ ! -d "$OUT_DIR" ]; then
  mkdir -p "$OUT_DIR"
  echo "Created directory: $OUT_DIR"
fi

# Generate DICOMs dump
echo "Generating DICOMs dumps..."
./dump_dicoms.py --log-level $LOG_LEVEL $SESSION_DIR >$OUT_DIR/dump_dicoms.jsonl 2>$OUT_DIR/dump_dicoms.log
echo "dump_dicoms.py exit code: $?"

# Generate QR dump
echo "Generating QR info dumps..."
./dump_qrinfo.py --log-level $LOG_LEVEL $SESSION_DIR >$OUT_DIR/dump_qrinfo.jsonl 2>$OUT_DIR/dump_qrinfo.log
echo "dump_qrinfo.py exit code: $?"

# Generate BIRCH dump
echo "Generating birch dumps..."
./dump_birch.py --log-level $LOG_LEVEL $SESSION_DIR >$OUT_DIR/dump_birch.jsonl 2>$OUT_DIR/dump_birch.log
echo "dump_birch.py exit code: $?"

# Generate psychopy dump
echo "Generating psychopy dumps..."
./dump_psychopy.py --log-level $LOG_LEVEL $SESSION_DIR >$OUT_DIR/dump_psychopy.jsonl 2>$OUT_DIR/dump_psychopy.log
echo "dump_psychopy.py exit code: $?"
