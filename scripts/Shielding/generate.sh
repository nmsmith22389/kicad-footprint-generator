#! /usr/bin/env bash

set -ex

run_generate() {
    ./smd_shielding.py "$1"
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done
