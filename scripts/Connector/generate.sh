#! /usr/bin/env bash

set -ex

dir_list=(
    generator
    Connector_Audio
    Connector_Harting
    Connector_Harwin
    Connector_Hirose
    Connector_IEC_DIN
    Connector_JAE
    Connector_JST
    Connector_JUSHUO
    Connector_Molex
    Connector_PCBEdge
    Connector_PhoenixContact
    Connector_Samtec
    Connector_SMD_single_row_plus_mounting_pad
    Connector_Stocko
    Connector_TE-Connectivity
    Connector_Wago
    Connector_Wire
    Connector_Wuerth
)

for dir in ${dir_list[@]}; do
    pushd $dir
    ./generate.sh
    popd
done
