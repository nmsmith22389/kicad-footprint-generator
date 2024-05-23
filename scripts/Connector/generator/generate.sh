#! /usr/bin/env bash

run_generate() {
    python3 ./connector_generator.py $1
}

for file in size_definitions/*.yaml; do
    # Later, this can set an output directory
    # (when the generator supports it)
    run_generate $file
done

for file in test_definitions/*.yaml; do
    run_generate $file
done
