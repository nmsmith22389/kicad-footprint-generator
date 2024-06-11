#!/usr/bin/env bash

set -ex

run_generate() {
    ./make_Capacitors_THT.py -v
}

run_generate
