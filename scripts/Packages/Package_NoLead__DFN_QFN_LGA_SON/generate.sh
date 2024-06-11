#! /usr/bin/env bash

run_generate() {
    ./ipc_noLead_generator.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done