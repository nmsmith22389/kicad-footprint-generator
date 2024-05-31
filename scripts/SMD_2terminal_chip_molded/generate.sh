#! /usr/bin/env bash

set -ex

run_generate() {
    # NOTE: Does not support --verbose argument yet
    # NOTE: Currently, it needs to be run on the top-level YAML
    ./ipc_2terminal_chip_molded_generator.py part_definitions.yaml
}

run_generate