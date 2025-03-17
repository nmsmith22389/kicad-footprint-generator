#! /usr/bin/env bash

set -ex

./hsec8_dv_pcbedge.py
./mecf_connector.py
./mecf_socket.py
./conn_samtec_LSHM_smd_top.py
./conn_samtec_hle.py
