#! /usr/bin/env bash

set -ex

run_generate() {
    ./wuerth_smt_spacer.py --params "$1"
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done
