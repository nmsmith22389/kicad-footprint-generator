#! /usr/bin/env bash

set -ex

run_generate() {
    ./Converter_DCDC.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done
