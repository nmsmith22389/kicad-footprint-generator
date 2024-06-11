#! /usr/bin/env bash

set -ex

run_generate() {
    ./ipc_gullwing_generator.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done

for file in test_definitions/*.yaml; do
    run_generate "$file"
done