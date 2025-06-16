#!/bin/bash

python proxy/subscheck.py

# Find and kill subs-check process
PROCESS_ID=$(pgrep -f "subs-check")
if [ ! -z "$PROCESS_ID" ]; then
  echo "Found subs-check process with ID: $PROCESS_ID, killing it..."
  kill $PROCESS_ID
else
  echo "subs-check process not found."
fi
