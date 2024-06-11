#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_LEDs_THT.py -v
}

run_generate
