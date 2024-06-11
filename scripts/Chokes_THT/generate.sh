#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_Chokes_THT.py -v
}

run_generate
