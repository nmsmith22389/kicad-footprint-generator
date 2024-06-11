#! /usr/bin/env bash

set -ex

run_generate() {
    ./rotary_coded_switch.py "$1" -v
}

for file in size_definitions/*.yaml; do
    run_generate "$file"
done

# Run make_DIPSwitches.py which does not take any parameter
./make_DIPSwitches.py -v