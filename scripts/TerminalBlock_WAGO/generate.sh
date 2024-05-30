#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_TerminalBlock_WAGO.py -v
}

run_generate
