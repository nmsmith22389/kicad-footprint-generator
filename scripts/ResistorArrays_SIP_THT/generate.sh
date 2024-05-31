s#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_Resistor_array_SIP.py -v
}

run_generate
