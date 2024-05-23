#! /usr/bin/env bash

SUBDIRS=(
    Connector
    Packages/Package_NoLead__DFN_QFN_LGA_SON
)

for dir in ${SUBDIRS[@]}; do
    pushd $dir
    ./generate.sh
    popd
done
