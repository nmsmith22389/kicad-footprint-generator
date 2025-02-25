#! /usr/bin/env bash

set -ex

./slide_Potentiometer.py slide_Potentiometer.yaml
./make_Potentiometer_THT.py
./make_Potentiometer_SMD.py
