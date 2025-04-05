#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_Diodes_THT.py
    #./bridge_rectifier.py bridge_rectifier/*.yaml
}

run_generate
