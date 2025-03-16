#!/usr/bin/env bash

set -ex

run_generate() {
    ./Choke_Schaffner_RNXXX.py -v
    ./Murata_DEM35xxC.py -v
    ./vishay_IHSM.py -v
    ./we-hci.py -v
    ./we-hcm.py -v
}

run_generate
