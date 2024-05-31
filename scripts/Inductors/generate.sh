#!/usr/bin/env bash

set -ex

run_generate() {
    ./bourns-srn.py -v
    ./Choke_Schaffner_RNXXX.py -v
    ./Murata_DEM35xxC.py -v
    ./vishay_IHSM.py -v
    ./we-hci.py -v
    ./we-hcm.py -v
    ./we-mapi.py -v
}

run_generate
