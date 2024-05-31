#! /usr/bin/env bash

set -ex

run_generate() {
    ./smlvn6.py -v
    ./plcc4.py size_definitions/plcc4.yml -v
}

run_generate