#! /usr/bin/env bash

set -ex

run_generate() {
    ./ipc_noLead_generator.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done

for file in size_definitions/qfn/*.yaml; do
    run_generate "$file"
done