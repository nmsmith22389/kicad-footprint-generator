#! /usr/bin/env bash

set -ex

run_generate() {
    ./gen_inductor.py "$1" -v
}

for file in ../../data/Inductor_SMD/*.yaml; do
    run_generate "$file"
done


# The old StandardBox-based def (port me!)
./Inductor_SMD.py -v Inductor_SMD.yaml
