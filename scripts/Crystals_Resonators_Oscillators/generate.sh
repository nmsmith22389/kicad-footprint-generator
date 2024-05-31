#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_crystal.py -v
}

run_generate
