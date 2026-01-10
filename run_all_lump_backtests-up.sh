#!/bin/bash

INPUT_FILE="up-data.csv"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    echo "Please create it with the format: <symbol>,<capital>"
    exit 1
fi

# Print CSV header
echo "symbol,capital,final_equity,total_return_pct,mdd_pct,dividend_income,capital_gain"

# Read the input file line by line
while IFS=',' read -r symbol capital
do
    # Skip empty lines or headers
    if [ -z "$symbol" ] || [ "$symbol" == "symbol" ]; then
        continue
    fi

    # Run the backtest script and capture the output
    output=$(./run_lump_backtest-up.sh "$symbol" "$capital")

    # Parse the output using awk to find the metrics
    final_equity=$(echo "$output" | awk -F': ' '/Final Equity/ {gsub(/,/, "", $2); print $2}')
    total_return=$(echo "$output" | awk -F': ' '/Total Return/ {gsub(/%/, "", $2); print $2}')
    mdd=$(echo "$output" | awk -F': ' '/MDD/ {gsub(/%/, "", $2); print $2}')
    dividend_income=$(echo "$output" | awk -F': ' '/Dividend Income/ {gsub(/,/, "", $2); print $2}')
    capital_gain=$(echo "$output" | awk -F': ' '/Capital Gain/ {gsub(/,/, "", $2); print $2}')

    # Print the results in CSV format
    echo "$symbol,$capital,${final_equity:-"N/A"},${total_return:-"N/A"},${mdd:-"N/A"},${dividend_income:-"N/A"},${capital_gain:-"N/A"}"

done < "$INPUT_FILE"
