#! /usr/bin/env bash

set -ex

# NOTE: Currently this automatically determines the YAML filename
run_generate() {
    python3 main_generator.py
}

run_generate