#! /usr/bin/env bash

set -ex


for file in size_definitions/*.yaml; do
    ./ipc_gullwing_generator.py "$file" -v
done

for file in test_definitions/*.yaml; do
   ./ipc_gullwing_generator.py "$file" -v --output-dir "test_output"
done
