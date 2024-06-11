#! /usr/bin/env bash

set -ex

run_generate() {
    ./dip_generator.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done
