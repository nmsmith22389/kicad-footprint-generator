#! /usr/bin/env bash

SUBDIRS=(
    Connector
    Inductor_SMD
    Packages/Package_BGA
    Packages/Package_DIP
    Packages/Package_Gullwing__QFP_SOIC_SO
    Packages/Package_NoLead__DFN_QFN_LGA_SON
    Packages/Package_PLCC
)

for dir in ${SUBDIRS[@]}; do
    pushd $dir
    ./generate.sh
    popd
done
