#! /usr/bin/env bash

run_generate() {
    ./ipc_noLead_generator.py size_definitions/$1
}

for file in size_definitions/*.yaml; do
    run_generate $(basename $file)
done