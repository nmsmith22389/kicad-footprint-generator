#! /usr/bin/env bash

set -ex

./conn_jst_eh_tht_side.py
./conn_jst_eh_tht_top.py

./conn_jst_J2100_tht_side.py
./conn_jst_J2100_tht_top.py

./conn_jst_JWPF_tht_top.py

./conn_jst_NV_tht_top.py

./conn_jst_ph_tht_side.py
./conn_jst_ph_tht_top.py

./conn_jst_PHD_horizontal.py
./conn_jst_PHD_vertical.py

./conn_jst_PUD_tht_side.py
./conn_jst_PUD_tht_top.py

./conn_jst_VH_tht_side-stabilizer.py
./conn_jst_VH_tht_side.py
./conn_jst_VH_tht_top-shrouded.py
./conn_jst_vh_tht_top.py

./conn_jst_xh_tht_side.py
./conn_jst_xh_tht_top.py

./conn_jst_ze_tht_side.py
./conn_jst_ze_tht_top.py

./conn_jst_zh_tht_top.py

./conn_jst_XA_horizontal.py
./conn_jst_XA_vertical.py
