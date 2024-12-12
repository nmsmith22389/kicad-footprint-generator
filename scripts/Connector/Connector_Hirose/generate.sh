#! /usr/bin/env bash

set -ex

./conn_ffc_hirose_fh12_smd_side.py
./conn_ffc_hirose_fh26.py

./conn_hirose_df11_tht_top.py
./conn_hirose_df12c_ds_smd_top.py
./conn_hirose_df12e_dp_smd_top.py
./conn_hirose_df13_tht_side.py
./conn_hirose_df13_tht_top.py
./conn_hirose_df13c_smd_top.py
./conn_hirose_df63_tht_top.py