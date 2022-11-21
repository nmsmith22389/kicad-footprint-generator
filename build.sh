#!/bin/bash
set -e

ROOT="$(pwd)"
SCRIPTS="$ROOT/scripts"
OUT="$ROOT/out"

rm -r "$OUT"
mkdir -p "$OUT"

enter() {
    mkdir -p "$OUT/$1"
    cd "$OUT/$1"
}

enter_root_out() {
    cd "$OUT"
}

# Used for scripts that are reasonably well formed and emit their footprints into a subdirectory.
output_subdir() {
    mkdir -p "$OUT/$1.pretty"
    mv ./$1.pretty/* "$OUT/$1.pretty/"
    rm -r "./$1.pretty"
    echo "= Wrote footprints to $1.pretty"
}

# Used for scripts that are a bit less well behaved and spit their footprints into the same directory
# as the script itself.
output_currdir() {
    mkdir -p "$OUT/$1.pretty"
    mv ./*.kicad_mod "$OUT/$1.pretty"
    echo "= Wrote footprints to $1.pretty"
}

assert_outputed() {
    if compgen -G "*.pretty/*" > /dev/null; then
        echo "ERROR: Items not outputed from scripts:"
        ls -lh ./*.pretty/*
        echo ""
        echo "Exiting."
        exit 1
    fi

    if compgen -G "*.kicad_mod" > /dev/null; then
        echo "ERROR: Items not outputed from scripts:"
        ls -lh ./*.kicad_mod
        echo ""
        echo "Exiting."
        exit 1
    fi
}

enter "Battery.pretty"
python3 "$SCRIPTS/Battery/BatteryHolder.py" "$SCRIPTS/Battery/BatteryHolder.yml"

# TODO separate libs for SMD and THT
# enter "Test.pretty"
# python3 "$SCRIPTS/Buttons_Switches/rotary_coded_switch.py" "$SCRIPTS/Buttons_Switches/rotary_coded_switch.yml"

enter "Buzzer_Beeper.pretty"
python3 "$SCRIPTS/Buzzers_Beepers/buzzer_round_tht.py" "$SCRIPTS/Buzzers_Beepers/buzzer_round_tht_star_mictronics.csv"

# === BEGIN Capacitor_SMD.pretty ===
cd "$SCRIPTS/Capacitors_SMD"

python3 "C_Elec_round.py" "--global_config" "$SCRIPTS/tools/global_config_files/config_KLCv3.0.yaml" "--series_config" "$SCRIPTS/SMD_2terminal_chip_molded/package_config_KLCv3.0.yaml" "--ipc_definition" "$SCRIPTS/Capacitors_SMD/ipc7351B_capae_crystal.yaml" "$SCRIPTS/Capacitors_SMD/C_Elec_round.yaml"
output_subdir "Capacitor_SMD"
assert_outputed

# TODO this script errors non-trivially
#python3 "$SCRIPTS/Capacitors_SMD/CP_Elec_round.py" "--global_config" "$SCRIPTS/tools/global_config_files/config_KLCv3.0.yaml" "$SCRIPTS/Capacitors_SMD/CP_Elec_round.yaml"

python3 "C_Trimmer_make.py"
output_currdir "Capacitor_SMD"
assert_outputed
# === END Capacitor_SMD.pretty ===

# === BEGIN Capacitor_THT.pretty ===
cd "$SCRIPTS/Capacitors_THT"
python3 "make_Capacitors_THT.py"
output_currdir "Capacitor_THT"
assert_outputed
# === END Capacitor_THT.pretty ===

# === BEGIN Chokes_THT.pretty ===
cd "$SCRIPTS/Chokes_THT"
python3 "make_Chokes_THT.py"
output_currdir "Chokes_THT"
assert_outputed
# === END Chokes_THT.pretty ===

# === BEGIN Connector_Harwin.pretty ===
cd "$SCRIPTS/Connector/Connector_Harwin"
python3 "conn_harwin_m20-781xx45_smd_top_dual_row.py"
output_subdir "Connector_Harwin"
assert_outputed
# === END Connector_Harwin.pretty ===

# === BEGIN Connector_Hirose ===
cd "$SCRIPTS/Connector/Connector_Hirose"
python3 "conn_ffc_hirose_fh12_smd_side.py"
python3 "conn_hirose_df11_tht_top.py"
python3 "conn_hirose_df12c_ds_smd_top.py"
python3 "conn_hirose_df12e_dp_smd_top.py"
python3 "conn_hirose_df13_tht_side.py"
python3 "conn_hirose_df13_tht_top.py"
python3 "conn_hirose_df13c_smd_top.py"
python3 "conn_hirose_df63_tht_top.py"

output_subdir "Connector_FFC-FPC"
output_subdir "Connector_Hirose"
assert_outputed
# === END Connector_Hirose ===

# === BEGIN Connector_IEC_DIN ===
cd "$SCRIPTS/Connector/Connector_IEC_DIN"
python3 "generate_din41612.py"
output_subdir "Connector_DIN"
assert_outputed
# === END Connector_IEC_DIN ===

# === BEGIN Connector_JAE ===
cd "$SCRIPTS/Connector/Connector_JAE"
python3 "conn_ffc_jae_ff08.py"
python3 "conn_jae_LY20_tht_side.py"
python3 "conn_jae_LY20_tht_top.py"

output_subdir "Connector_FFC-FPC"
output_subdir "Connector_JAE"
assert_outputed
# === END Connector_JAE ===

# === BEGIN Connector_JST ===
cd "$SCRIPTS/Connector/Connector_JST"
python3 "conn_jst_eh_tht_side.py"
python3 "conn_jst_eh_tht_top.py"
python3 "conn_jst_J2100_tht_side.py"
python3 "conn_jst_J2100_tht_top.py"
python3 "conn_jst_JWPF_tht_top.py"
python3 "conn_jst_NV_tht_top.py"
python3 "conn_jst_ph_tht_side.py"
python3 "conn_jst_ph_tht_top.py"
python3 "conn_jst_PHD_horizontal.py"
python3 "conn_jst_PHD_vertical.py"
python3 "conn_jst_PUD_tht_side.py"
python3 "conn_jst_PUD_tht_top.py"
python3 "conn_jst_VH_tht_side-stabilizer.py"
python3 "conn_jst_VH_tht_side.py"
python3 "conn_jst_VH_tht_top-shrouded.py"
python3 "conn_jst_vh_tht_top.py"
python3 "conn_jst_xh_tht_side.py"
python3 "conn_jst_xh_tht_top.py"
python3 "conn_jst_ze_tht_side.py"
python3 "conn_jst_ze_tht_top.py"

output_subdir "Connector_JST"
assert_outputed
# === END Connector_JST ===

# === BEGIN Connector_Molex ===
cd "$SCRIPTS/Connector/Connector_Molex"
python3 "conn_molex_micro-clasp_tht_top.py"
python3 "conn_molex_mini-fit-sr_tht_top.py"
python3 "conn_molex_mini-fit-sr_tht_top_dual.py"
python3 "conn_molex_mini-fit_Jr_tht_side_dual-row.py"
python3 "conn_molex_mini-fit_Jr_tht_top_dual-row.py"
python3 "conn_molex_nano-fit_tht_side.py"
python3 "conn_molex_nano-fit_tht_top.py"
python3 "conn_molex_picoblade_tht_side.py"
python3 "conn_molex_picoblade_tht_top.py"
python3 "conn_molex_picoflex_smd_top.py"
python3 "conn_molex_picoflex_tht_top.py"
python3 "conn_molex_sabre_tht_side.py"
python3 "conn_molex_sabre_tht_top.py"
python3 "conn_ffc_molex_200528.py"
python3 "conn_ffc_molex_502250.py"
python3 "conn_molex_kk_254_tht_top.py"
python3 "conn_molex_kk_396_tht_top.py"
python3 "conn_molex_mega-fit_tht_side_dual-row.py"
python3 "conn_molex_mega-fit_tht_top_dual_row.py"
python3 "conn_molex_micro-clasp_tht_side.py"
python3 "conn_molex_micro-fit-3.0_smd_side_dual_row.py"
python3 "conn_molex_micro-fit-3.0_smd_top_dual_row.py"
python3 "conn_molex_micro-fit-3.0_tht_side_dual_row.py"
python3 "conn_molex_micro-fit-3.0_tht_side_single_row.py"
python3 "conn_molex_micro-fit-3.0_tht_top_dual_row.py"
python3 "conn_molex_micro-fit-3.0_tht_top_single_row.py"
python3 "conn_molex_micro-latch_tht_side.py"
python3 "conn_molex_micro-latch_tht_top.py"
python3 "conn_molex_mini-fit-sr_tht_side.py"
python3 "conn_molex_slimstack-52991.py"
python3 "conn_molex_slimstack-53748.py"
python3 "conn_molex_slimstack-54722.py"
python3 "conn_molex_slimstack-55560.py"
python3 "conn_molex_slimstack-501920.py"
python3 "conn_molex_slimstack-502426.py"
python3 "conn_molex_slimstack-502430.py"
python3 "conn_molex_SPOX_tht_side.py"
python3 "conn_molex_SPOX_tht_top.py"
python3 "conn_molex_stackable-linear_tht_top.py"

output_subdir "Connector_FFC-FPC"
output_subdir "Connector_Molex"
assert_outputed
# === END Connector_Molex ===

# === BEGIN Connector_PCBEdge ===
cd "$SCRIPTS/Connector/Connector_PCBEdge"
python3 "molex_EDGELOCK.py"

output_currdir "Connector_PCBEdge"
assert_outputed
# === END Connector_PCBEdge ===

# === BEGIN Connector_PhoenixContact ===
cd "$SCRIPTS/Connector/Connector_PhoenixContact"
python3 mc.py
python3 mstb.py

output_subdir "Connector_Phoenix_GMSTB"
output_subdir "Connector_Phoenix_MC_HighVoltage"
output_subdir "Connector_Phoenix_MC"
output_subdir "Connector_Phoenix_MSTB"
assert_outputed
# === END Connector_PhoenixContact ===

# === BEGIN Connector_Samtec ===
cd "$SCRIPTS/Connector/Connector_Samtec"

# TODO these error out
#python3 conn_samtec_LSHM_smd_top.py
#python3 mecf_connector.py

python3 mecf_socket.py
python3 conn_samtec_hle.py

output_subdir "Connector_PCBEdge"
output_subdir "Connector_Samtec_HLE_SMD"
output_subdir "Connector_Samtec_HLE_THT"
assert_outputed
# === END Connector_Samtec ===

# === BEGIN Connector_SMD_single_row_plus_mounting_pad ===
cd "$SCRIPTS/Connector/Connector_SMD_single_row_plus_mounting_pad"
python3 smd_single_row_plus_mounting_pad.py conn_jst.yaml
python3 smd_single_row_plus_mounting_pad.py conn_molex.yaml
python3 smd_single_row_plus_mounting_pad.py conn_hirose.yaml

output_subdir "Connector_Molex"
output_subdir "Connector_JST"
output_subdir "Connector_Hirose"
assert_outputed
# === END Connector_SMD_single_row_plus_mounting_pad ===

# === BEGIN Connector_Stocko ===
cd "$SCRIPTS/Connector/Connector_Stocko"
python3 conn_Stocko_MKS_16xx.py

output_subdir "Connector_Stocko"
assert_outputed
# === END Connector_Stocko ===

# === BEGIN Connector_TE-Connectivity ===
cd "$SCRIPTS/Connector/Connector_TE-Connectivity"
python3 conn_ffc_te_84952-84953.py
python3 conn_fpc_te_1734839.py
python3 conn_te_826576.py
python3 conn_te_mate-n-lock_tht_side.py
python3 conn_te_mate-n-lock_tht_top.py

output_subdir "Connector_FFC-FPC"
output_subdir "Connector_TE-Connectivity"
assert_outputed
# === END Connector_TE-Connectivity ===

# === BEGIN Connector_Wago ===
cd "$SCRIPTS/Connector/Connector_Wago"
python3 conn_wago_734_horizontal.py
python3 conn_wago_734_vertical.py

output_subdir "Connector_Wago"
assert_outputed
# === END Connector_Wago ===

# === BEGIN Connector_Wire ===
cd "$SCRIPTS/Connector/Connector_Wire"
python3 solder_wire_tht.py wire_MC_Flexivolt.yaml

output_subdir "Connector_Wire"
assert_outputed
# === END Connector_Wago ===

# === BEGIN Connector_Wuerth ===
cd "$SCRIPTS/Connector/Connector_Wuerth"
python3 wuerth_6480xx11622.py

output_subdir "Connector_Wuerth"
assert_outputed
# === END Connector_Wago ===

# === BEGIN Connector_Audio ===
cd "$SCRIPTS/Connector/Connector_Audio"
python3 Jack_3.5mm_Switronic_ST-005-G_horizontal.py

output_currdir "Connector_Audio"
assert_outputed
# === END Connector_Wago ===

# === BEGIN Connector_PinSocket ===
cd "$SCRIPTS/Connector_PinSocket"
python3 main_generator.py

output_subdir "Connector_PinSocket_1.00mm"
output_subdir "Connector_PinSocket_1.27mm"
output_subdir "Connector_PinSocket_2.00mm"
output_subdir "Connector_PinSocket_2.54mm"
assert_outputed
# === END Connector_PinSocket ===

# === BEGIN Connector_DSub ===
cd "$SCRIPTS/Connectors_DSub"
python3 make_dsubs.py

# Yes, the casing here is different. This follows the current name in the library.
output_currdir "Connector_Dsub"
assert_outputed
# === END Connector_DSub ===

# === BEGIN Connector_DCDC ===
cd "$SCRIPTS/Converter_DCDC"
python3 Converter_DCDC.py Converter_DCDC.yml
python3 XP_Power_SF_THT.py

output_currdir "Converter_DCDC"
output_subdir "Converter_DCDC"
assert_outputed
# === END Connector_DCDC ===

cd "$SCRIPTS/Crystals_Resonators_SMD"
python3 make_crystal_smd.py
output_currdir "Crystal"
assert_outputed

cd "$SCRIPTS/Crystals_Resonators_THT"
python3 make_crystal.py
output_currdir "Crystal"
assert_outputed

cd "$SCRIPTS/Diodes_THT"
python3 make_Diodes_THT.py
output_currdir "Diode_THT"
assert_outputed

cd "$SCRIPTS/Fuse"
python3 ptc-fuse-tht.py ptc-fuse-tht.yaml
output_currdir "Fuse"
assert_outputed

# TODO is scripts/general still relevant?

cd "$SCRIPTS/Inductor_SMD"
python3 Inductor_SMD.py Inductor_SMD.yml
output_currdir "Inductor_SMD"
assert_outputed

cd "$SCRIPTS/Inductors"

python3 Choke_Schaffner_RNXXX.py
output_currdir "Inductor_THT"
assert_outputed

python3 Murata_DEM35xxC.py
output_currdir "Inductor_SMD"
assert_outputed

# TODO broken
#python3 vishay_IHSM.py
#assert_outputed

# TODO broken
#python3 we-hci.py
#assert_outputed

# TODO broken
#python3 we-hcm.py
#assert_outputed

# TODO broken
#python3 we-mapi.py
#assert_outputed

# TODO broken
#python3 bourns-srn.py
#assert_outputed

cd "$SCRIPTS/LEDs_SMD"

python3 plcc4.py plcc4.yml
output_currdir "LED_SMD"
assert_outputed

# TODO broken
#python3 plcc4.py smlvn6.yml
#assert_outputed

cd "$SCRIPTS/LEDs_THT"
python3 make_LEDs_THT.py
output_currdir "LED_THT"
assert_outputed

cd "$SCRIPTS/Mounting_Hardware"
python3 wuerth_smt_spacer.py
# TODO broken? correct file? why is this in sibling directory?
#python3 mounting_hole.py ../Mounting_Holes/mounting_hole_long.yaml
output_subdir "Mounting_Wuerth"
assert_outputed

# TODO broken
#cd "$SCRIPTS/Multicomp"
#bash create_connectors_multicomp.sh
#assert_outputed

cd "$SCRIPTS/Oscillators_SMD"
python3 make_oscillators.py
output_currdir "Oscillator"
assert_outputed

cd "$SCRIPTS/Packages/Package_BGA"
python3 ipc_bga_generator.py bga.yaml
python3 ipc_bga_generator.py csp.yaml
python3 ipc_bga_generator.py ipc_7351b_bga_land_patterns.yaml
python3 ipc_bga_generator.py bga_xilinx.yaml
output_subdir "Package_BGA"
output_subdir "Package_CSP"
assert_outputed

cd "$SCRIPTS/Packages/Package_DIP"
python3 make_DIP_footprints.py
output_currdir "Package_DIP"
assert_outputed

cd "$SCRIPTS/Packages/Package_Gullwing__QFP_SOIC_SO"
python3 ipc_gullwing_generator.py size_definitions/*
output_subdir "Package_SO"
output_subdir "Package_QFP"
output_subdir "Package_TO_SOT_SMD"
assert_outputed

cd "$SCRIPTS/Packages/Package_NoLead__DFN_QFN_LGA_SON"
python3 ipc_noLead_generator.py size_definitions/**.yaml
output_subdir "Package_SON"
output_subdir "Package_LGA"
output_subdir "Package_DFN_QFN"
output_subdir "Package_CSP"
output_subdir "OptoDevice"
output_subdir "Oscillator"
output_subdir "RF_Converter"
assert_outputed

cd "$SCRIPTS/Packages/Package_PLCC"
python3 ipc_plcc_jLead_generator.py plcc_jLead_definitions.yaml
output_subdir "Package_LCC"
assert_outputed

cd "$SCRIPTS/Packages/TO_SOT_Packages_SMD"
python3 make_DPAK.py
output_currdir "Package_TO_SOT_SMD"
assert_outputed

cd "$SCRIPTS/Packages/TO_SOT_THT"
python3 TO_SOT_THT_generate.py
output_currdir "Package_TO_SOT_THT"
assert_outputed
 
# TODO params?
# cd "$SCRIPTS/PadGenerator"
# python3 RingPad.py
# assert_outputed

cd "$SCRIPTS/pin-headers_socket-strips"
python3 make_pin_headers.py
# TODO broken
#python3 make_socket_strips.py
python3 make_idc_headers.py
output_subdir "Pin_Headers"
#output_subdir "Socket_Strips"
output_subdir "Connector_IDC"
assert_outputed

cd "$SCRIPTS/Potentiometers"
# TODO really broken
#python3 make_Potentiometer_THT.py
# TODO really broken
#python3 make_Potentiometer_SMD.py
python3 slide_Potentiometer.py slide_Potentiometer.yaml
output_currdir "Potentiometer_THT"
assert_outputed

cd "$SCRIPTS/Recom_DCDC"
python3 Recom_SIP.py
output_currdir "Converter_DCDC"
assert_outputed

cd "$SCRIPTS/Resistor_THT"
python3 make_Resistors_THT.py
output_currdir "Resistor_THT"
assert_outputed

cd "$SCRIPTS/ResistorArrays_SIP_THT"
python3 make_Resistor_array_SIP.py
output_currdir "Resistor_THT"
assert_outputed

cd "$SCRIPTS/Shielding"
python3 smd_shielding.py wuerth_smd_shielding.kicad_mod.yaml
python3 smd_shielding.py laird_technologies_smd_shielding.kicad_mod.yaml
python3 wuerth_electronic_smd_shielding.py
python3 wuerth_electronic_tht_shielding.py
output_currdir "RF_Shielding"
assert_outputed

cd "$SCRIPTS/SMD_2terminal_chip_molded"
python3 ipc_2terminal_chip_molded_generator.py --series_config package_config_KLCv3.0.yaml --ipc_definition ipc7351_2terminal.yaml part_definitions.yaml
output_subdir "Capacitor_SMD"
output_subdir "Resistor_SMD"
output_subdir "LED_SMD"
output_subdir "Inductor_SMD"
output_subdir "Fuse"
output_subdir "Diode_SMD"
output_subdir "Capacitor_Tantalum_SMD"
assert_outputed

cd "$SCRIPTS/Socket"
python3 3M_Textool.py 3M_Textool.yaml
output_currdir "Socket"
assert_outputed

cd "$SCRIPTS/TerminalBlock_4Ucon"
# TODO this one probably has quadratic behavior somewhere, fix
python3 make_TerminalBlock_4Ucon.py
output_subdir "TerminalBlock_4Ucon"
assert_outputed

cd "$SCRIPTS/TerminalBlock_Altech"
python3 Altech.py Altech.yml
output_currdir "TerminalBlock_Altech"
assert_outputed

cd "$SCRIPTS/TerminalBlock_MetzConnect"
python3 make_TerminalBlock_MetzConnect.py
python3 make_SingleTerminalBlock_MetzConnect.py
output_subdir "TerminalBlock_MetzConnect"
assert_outputed

cd "$SCRIPTS/TerminalBlock_Philmore"
python3 make_TerminalBlock_Philmore.py
output_subdir "TerminalBlock_Philmore"
assert_outputed

cd "$SCRIPTS/TerminalBlock_Phoenix"
# TODO this one probably has quadratic behavior somewhere, fix
python3 make_TerminalBlock_Phoenix.py
output_subdir "TerminalBlock_Phoenix"
assert_outputed

cd "$SCRIPTS/TerminalBlock_RND"
# TODO this one probably has quadratic behavior somewhere, fix
python3 make_TerminalBlock_RND.py
output_subdir "TerminalBlock_RND"
assert_outputed

cd "$SCRIPTS/TerminalBlock_TE-Connectivity"
python3 make_TerminalBlock_TE-Connectivity.py
output_subdir "TerminalBlock_TE-Connectivity"
assert_outputed

cd "$SCRIPTS/TerminalBlock_WAGO"
python3 make_TerminalBlock_WAGO.py
output_subdir "TerminalBlock_WAGO"
assert_outputed

# cd "$SCRIPTS/Vigortronix"
# TODO broken
# python3 vigotronix.py
# assert_outputed
