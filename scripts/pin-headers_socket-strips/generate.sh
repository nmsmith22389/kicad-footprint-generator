#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_idc_headers.py -v
    ./make_pin_headers.py -v
    ./make_socket_strips.py -v
}

run_generate
