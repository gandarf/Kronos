#!/bin/bash

# Check if both arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: ./run_lump_backtest.sh <symbol> <capital>"
  exit 1
fi

SYMBOL="$1"
CAPITAL="$2"

python3 run_backtest.py --mode lump --symbol "$SYMBOL" --start-date 2021-12-27 --end-date 2022-12-27 --capital "$CAPITAL"
