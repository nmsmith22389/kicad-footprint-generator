#! /usr/bin/env bash

set -ex

run_generate() {
    ./make_TerminalBlock_MetzConnect.py -v
    ./make_SingleTerminalBlock_MetzConnect.py -v
}

run_generate

