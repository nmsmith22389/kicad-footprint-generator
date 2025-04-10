#! /usr/bin/env bash

set -ex

./wuerth_smt_spacer.py --params size_definitions/wuerth_smt_spacer.yaml
./mountinghole.py size_definitions/hole_sizes.yaml


