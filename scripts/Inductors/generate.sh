#!/usr/bin/env bash

set -ex

run_generate() {
    ./Choke_Schaffner_RNXXX.py -v
    ./Murata_DEM35xxC.py -v
}

run_generate
