#!/usr/bin/env bash

set -ex

run_generate() {
    python3 make_samtec_tsm.py
}

run_generate
