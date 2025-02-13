#! /usr/bin/env bash

set -ex

# these generators don't output to libraries yet, so make the dirs here
# and we can remove this when they're ported
mkdir -p Potentiometer_THT.pretty
mkdir -p Potentiometer_SMD.pretty

cd Potentiometer_THT.pretty
../slide_Potentiometer.py ../slide_Potentiometer.yaml
../make_Potentiometer_THT.py

cd ../Potentiometer_SMD.pretty
../make_Potentiometer_SMD.py