#! /usr/bin/env bash

set -ex

run_generate() {
    ./buzzer_round_tht.py "$1" -v
}

# NOTE: This would be correct as the generator also supports YAML,
# but we dont have any YAML files at the moment
# for file in size_definitions/*.{yaml,csv}; do
for file in size_definitions/*.csv; do
    run_generate "$file"
done