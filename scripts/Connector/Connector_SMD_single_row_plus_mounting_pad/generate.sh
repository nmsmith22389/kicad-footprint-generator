#! /usr/bin/env bash

set -ex

./smd_single_row_plus_mounting_pad.py conn_hirose.yaml
./smd_single_row_plus_mounting_pad.py conn_jst.yaml
./smd_single_row_plus_mounting_pad.py conn_molex.yaml