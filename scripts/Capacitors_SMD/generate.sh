#! /usr/bin/env bash

set -ex

# NOTE: This generator needs a rework
# preferrably when the CI auto-checks generation
./C_Elec_round.py size_definitions/C_Elec_round.yaml
./CP_Elec_round.py size_definitions/CP_Elec_round.yaml
./C_Trimmer_make.py # TODO rework to take YAML as arg