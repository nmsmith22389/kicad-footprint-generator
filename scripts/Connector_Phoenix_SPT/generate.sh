#! /usr/bin/env bash

set -ex

run_generate() {
    python3 phoenixcontact_terminal_block_spt_tht.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done
