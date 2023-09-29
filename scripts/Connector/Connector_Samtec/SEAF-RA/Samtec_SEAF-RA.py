#!/usr/bin/env python3

import math
import os
import sys
import argparse
import yaml

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..","..", "..", ".."))

from KicadModTree import *  # NOQA
from KicadModTree.nodes.base.Pad import Pad  # NOQA
sys.path.append(os.path.join(sys.path[0], "..","..", "..", "tools"))  # load parent path of tools

from KicadModTree import *
import itertools
from string import ascii_uppercase

def generateFootprint(config, fpParams, fpId):
    # Common parameters for all types
    size_source = "http://suddendocs.samtec.com/prints/seaf-xx-xx.x-xx-xx-x-ra-xx-footprint.pdf"
    pitchX = 1.27
    pitchY = pitchX
    pitchString = str(pitchX) + "x" + str(pitchY)
    # The paste mask is bigger than the copper and stop-mask
    # For this type of connector it is a must to do so.
    pad_size_x = 0.32 + 0.2 + 0.32
    pad_size_y = 0.64
    pad_stencil_size_x = 0.44 + 0.1 + 0.44 
    pad_stencil_size_y = 0.89    
    mask_margin = 0.0
    paste_margin = 0.0
    paste_ratio = 0.0
    npth_drill_AlignmentHole = 1.27
    # Holes use paste in hole technology .. therefore the THT-via size is same as drill
    # resulting in a THT with no copper pad
    # But this is not a practical real world design.
    # PCB manufacturers need a annular restring anyway, at least according IPC2221 of 50 um.
    # To avoid problems in manufacturing process,
    # assume a Minimum Annular Ring of 200 um or a Pad to Hole Ratio of 1,5 . what ever is suitable.
    pth_drill = 1.14
    if ((pth_drill * 1.5) < (pth_drill + (2 * 0.2))):
        pth_pad = pth_drill + (2 * 0.2)
    else:
        pth_pad = pth_drill * 1.5
    
    pth_distance = 2.97
        
    
    
    # Check if given parameters are correct according catalogue ordering guideline
    # checking-clause
    # (Latchpost 06 row 40 positions only)
    if ((fpParams["option"] == "LP") and 
        (fpParams["no_pins_of_row"] != 40) and
        (fpParams["no_of_rows"] != 6)):
        print('Skipping {0} => This connector is not orderable.'.format(fpId))
        sys.exit()
    else:
        print('Building footprint for parameter set: {}'.format(fpId))    
    
    
    # Read the number of positions (a.k.a. number of pins of an row )
    num_positions = fpParams["no_pins_of_row"]
    # Read the number of rows
    num_rows = fpParams["no_of_rows"]
    # define the correct pin-order here according datasheet
    # tlbr = top left to bottom right
    # trbl = top right to bottom left
    # bltr = bottom left to top right
    # brtl = bottom right to top left
    pin_order = "tlbr"
    # Parameters for SEAF-RA used from datasheet
    tab_DIM_A = [[20, 30, 40, 50],                          # number of positions per row
                 [24.13, 36.83, 49.53, 62.23]]  # dimension values for the number of positions per row
    tab_DIM_B = [[4, 6, 8, 10],
                 [13.77, 16.31, 18.85, 21.39]]
    tab_DIM_C = [[4, 6, 8, 10],
                 [8.00, 10.54, 10.54, 10.54]]
    tab_DIM_D = [[20, 30, 40, 50],
                 [19, 29, 39, 49]]
    tab_DIM_E = [[20, 30, 40, 50],
                 [30.73, 43.43, 56.13, 68.83]]
    tab_DIM_F = [[20, 30, 40, 50],
                 [32.77, 45.47, 58.17, 70.87]]
    tab_DIM_G_w_GP = [[20, 30, 40, 50],
                      ["NA", "NA", "NA", "NA"]]
    tab_DIM_G_wo_GP = [[20, 30, 40, 50],
                      ["NA", "NA", "NA", "NA"]]
    tab_DIM_G_LP = [[20, 30, 40, 50],
                    [45.47, 58.17, 70.87, 83.57]]
    tab_DIM_H_w_GP = [[20, 30, 40, 50],
                      [34.80, 47.50, 60.20, 72.90]]
    tab_DIM_H_wo_GP = [[20, 30, 40, 50],
                       [34.80, 47.50, 60.20, 72.90]]
    tab_DIM_H_LP = [[20, 30, 40, 50],
                    [50.80, 63.50, 76.20, 88.90]]
    tab_DIM_J = [[4, 6, 8, 10],
                 [2, 4, 6, 8]]
    tab_DIM_K = [[4, 6, 8, 10],
                 [2.54, 5.08, 7.62, 10.16]]
    tab_DIM_M = [[20, 30, 40, 50],
                 [33.27, 45.97, 58.67, 71.37]]
    tab_DIM_N = [[4, 6, 8, 10],
                 [1.27, 2.08, 2.08, 2.08]]
    # Original table entries from datasheet. There is an error for 10 row-types
    #tab_DIM_P = [[4, 6, 8, 10],
    #             [13.77, 12.75, 16.31, 18.85]]
    # Corrected table entries, measured in 3D and on a physical part itself
    tab_DIM_P = [[4, 6, 8, 10],
                 [13.77, 12.75, 16.31, 16.31]]
    tab_DIM_Q_w_GP = [[20, 30, 40, 50],
                      [44.96, 57.66, 70.36, 83.06]]
    tab_DIM_Q_wo_GP = [[20, 30, 40, 50],
                       ["NA", "NA", "NA", "NA"]]
    tab_DIM_Q_LP = [[20, 30, 40, 50],
                 ["NA", "NA", "NA", "NA"]]
    
    len_REF_A = 5.84 # Length from PCB-Edge-Marker-Line to first pin row, see datasheet page 1
    len_REF_B = 2.15 # Length from PCB Edge-Marker-Line to top left corner ofhousing, see datasheet page 1
    len_REF_C = 2.16 # Distance from first pin row to second pin row, see dataheet page 1
    len_REF_D = 4.38 # Distance from first pin row to left upper fixature hole 
    len_REF_E = 2.97 # Distance first pad A1 from Alignement Hole DIM "E", see datasheet page 1
    len_REF_F = 3.63 # Distance last pad Ax to Alignement Hole right side (use  DIM "E" ?), see datasheet page 1
    len_REF_N = 1.51 # Length not noted in datasheet, measured from 3D-Model . Counterpart to DIM "N" but also a fixed value for all
    
    pkg_DIM_A = getTableEntry(tab_DIM_A, num_positions)
    if pkg_DIM_A == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_A-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_B = getTableEntry(tab_DIM_B, num_rows)
    if pkg_DIM_B == -1:
        print('Error, no_of_rows = {} does not exist in tab_DIM_B-list'.format(fpParams["no_of_rows"]))
        sys.exit()
    pkg_DIM_C = getTableEntry(tab_DIM_C, num_rows)
    if pkg_DIM_C == -1:
        print('Error, no_of_rows = {} does not exist in tab_DIM_C-list'.format(fpParams["no_of_rows"]))
        sys.exit()
    pkg_DIM_D = getTableEntry(tab_DIM_D, num_positions)
    if pkg_DIM_D == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_D-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_E = getTableEntry(tab_DIM_E, num_positions)
    if pkg_DIM_E == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_E-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_F = getTableEntry(tab_DIM_F, num_positions)
    if pkg_DIM_F == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_F-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    
    pkg_DIM_G_w_GP = getTableEntry(tab_DIM_G_w_GP, num_positions)
    if pkg_DIM_G_w_GP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_G_w_GP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_G_wo_GP = getTableEntry(tab_DIM_G_wo_GP, num_positions)
    if pkg_DIM_G_wo_GP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_G_wo_GP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_G_LP = getTableEntry(tab_DIM_G_LP, num_positions)
    if pkg_DIM_G_LP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_G_LP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    
    pkg_DIM_H_w_GP = getTableEntry(tab_DIM_H_w_GP, num_positions)
    if pkg_DIM_H_w_GP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_H_w_GP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_H_wo_GP = getTableEntry(tab_DIM_H_wo_GP, num_positions)
    if pkg_DIM_H_wo_GP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_H_wo_GP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_H_LP = getTableEntry(tab_DIM_H_LP, num_positions)
    if pkg_DIM_H_LP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_H_LP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
        
    pkg_DIM_J = getTableEntry(tab_DIM_J, num_rows)
    if pkg_DIM_J == -1:
        print('Error, no_of_rows = {} does not exist in tab_DIM_J-list'.format(fpParams["no_of_rows"]))
        sys.exit()
    pkg_DIM_K = getTableEntry(tab_DIM_K, num_rows)
    if pkg_DIM_K == -1:
        print('Error, no_of_rows = {} does not exist in tab_DIM_K-list'.format(fpParams["no_of_rows"]))
        sys.exit()
    pkg_DIM_M = getTableEntry(tab_DIM_M, num_positions)
    if pkg_DIM_M == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_M-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_N = getTableEntry(tab_DIM_N, num_rows)
    if pkg_DIM_N == -1:
        print('Error, no_of_rows = {} does not exist in tab_DIM_N-list'.format(fpParams["no_of_rows"]))
        sys.exit()
    pkg_DIM_P = getTableEntry(tab_DIM_P, num_rows)
    if pkg_DIM_P == -1:
        print('Error, no_of_rows = {} does not exist in tab_DIM_P-list'.format(fpParams["no_of_rows"]))
        sys.exit()
    
    pkg_DIM_Q_w_GP = getTableEntry(tab_DIM_Q_w_GP, num_positions)
    if pkg_DIM_Q_w_GP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_w_GP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_Q_wo_GP = getTableEntry(tab_DIM_Q_wo_GP, num_positions)
    if pkg_DIM_Q_wo_GP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_wo_GP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
    pkg_DIM_Q_LP = getTableEntry(tab_DIM_Q_LP, num_positions)
    if pkg_DIM_Q_LP == -1:
        print('Error, no_pins_of_row = {} does not exist in tab_DIM_LP-list'.format(fpParams["no_pins_of_row"]))
        sys.exit()
        
    
    #num_positions = fpParams["layout_x"]
    #num_rows = fpParams["layout_y"]
    
    if "additional_tags" in fpParams:
        additionalTag = " " + fpParams["additional_tags"]
    else:
        additionalTag = ""
    
    if "row_names" in fpParams:
        row_names = fpParams["row_names"]
    else:
        row_names = config['row_names']
    
    if "row_skips" in fpParams:
        row_skips = fpParams["row_skips"]
    else:
        row_skips = []


    f = Footprint(fpId)
    f.setAttribute("smd")
    f.setMaskMargin(mask_margin)
    f.setPasteMargin(paste_margin)
    f.setPasteMarginRatio(paste_ratio)

    s1 = [1.0, 1.0]
    s2 = [min(1.0, round(pkg_DIM_M / 4.3, 2))] * 2

    t1 = 0.15 * s1[0]
    t2 = 0.15 * s2[0]

    padShape = Pad.SHAPE_OVAL
    
    silkOffset = config['silk_fab_offset']
    crtYdOffset = config['courtyard_offset']['connector']
    
    
    # Horizonal center line is not really specified in dataheet
    # Note:
    # Alignment Holes define together with the first row of pins the horizontal centerline
    X_Center = 0.0
    Y_Center = 0.0
    
    ########################### Front Edge of PCB - Marker #################################
    if (fpParams["option"] == "NONE"):
        P1_X_FrontEdgeMarker = X_Center - (pkg_DIM_H_wo_GP / 2.0)
        P1_Y_FrontEdgeMarker = Y_Center - len_REF_A
        P2_X_FrontEdgeMarker = X_Center + (pkg_DIM_H_wo_GP / 2.0)
        P2_Y_FrontEdgeMarker = P1_Y_FrontEdgeMarker
    elif (fpParams["option"] == "GP"):
        P1_X_FrontEdgeMarker = X_Center - (pkg_DIM_Q_w_GP / 2.0)
        P1_Y_FrontEdgeMarker = Y_Center - len_REF_A
        P2_X_FrontEdgeMarker = X_Center + (pkg_DIM_Q_w_GP / 2.0)
        P2_Y_FrontEdgeMarker = P1_Y_FrontEdgeMarker
    elif (fpParams["option"] == "LP"):
        P1_X_FrontEdgeMarker = X_Center - (pkg_DIM_H_LP / 2.0)
        P1_Y_FrontEdgeMarker = Y_Center - len_REF_A
        P2_X_FrontEdgeMarker = X_Center + (pkg_DIM_H_LP / 2.0)
        P2_Y_FrontEdgeMarker = P1_Y_FrontEdgeMarker       
    else:
        print('Error, this type of option={} is not defined for Front Edge of PCB-Marker'.format(fpParams["option"]))
        sys.exit()
        
    f.append(Line(start=[P1_X_FrontEdgeMarker, P1_Y_FrontEdgeMarker],
                      end=[P2_X_FrontEdgeMarker, P2_Y_FrontEdgeMarker],
                      layer="Dwgs.User",
                      width=0.05))
    
    ########################### Fabrication, Courtyard and Silk  #################################
    # Since the Silk layer would be outbounded of the PCB-edge we need to stop it 0.25 before
    # PCB edge to avoid failures in production fab
    silkEdgeOffset = 0.25
    
    if (fpParams["option"] == "NONE"): # This is the without GP-option or LP-option
        # Generating Points for the "Fab"-layer (fabrication)
        P1_X_Fabrication = X_Center - (pkg_DIM_M / 2.0)
        P1_Y_Fabrication = Y_Center - (len_REF_A + len_REF_B)
        P2_X_Fabrication = X_Center + (pkg_DIM_M / 2.0)
        P2_Y_Fabrication = P1_Y_Fabrication
        P3_X_Fabrication = P2_X_Fabrication
        P3_Y_Fabrication = P2_Y_Fabrication + len_REF_N
        P4_X_Fabrication = X_Center + (pkg_DIM_H_wo_GP / 2.0)
        P4_Y_Fabrication = P3_Y_Fabrication
        P5_X_Fabrication = P4_X_Fabrication
        P5_Y_Fabrication = P2_Y_Fabrication + pkg_DIM_B
        P6_X_Fabrication = P3_X_Fabrication
        P6_Y_Fabrication = P5_Y_Fabrication
        P7_X_Fabrication = P6_X_Fabrication
        P7_Y_Fabrication = P6_Y_Fabrication + pkg_DIM_N
        P8_X_Fabrication = P1_X_Fabrication
        P8_Y_Fabrication = P7_Y_Fabrication
        P9_X_Fabrication = P8_X_Fabrication
        P9_Y_Fabrication = P6_Y_Fabrication
        P10_X_Fabrication = X_Center - (pkg_DIM_H_wo_GP / 2.0)
        P10_Y_Fabrication = P9_Y_Fabrication
        P11_X_Fabrication = P10_X_Fabrication
        P11_Y_Fabrication = P3_Y_Fabrication
        P12_X_Fabrication = P1_X_Fabrication
        P12_Y_Fabrication = P11_Y_Fabrication
        # Generating Points for the "crtYd"-layer (courty yard)
        P1_X_Courtyard = crtYdRound(P11_X_Fabrication - crtYdOffset)
        P1_Y_Courtyard = crtYdRound(P1_Y_Fabrication - crtYdOffset)
        P2_X_Courtyard = crtYdRound(P4_X_Fabrication + crtYdOffset)
        P2_Y_Courtyard = crtYdRound(P1_Y_Fabrication - crtYdOffset)
        P3_X_Courtyard = crtYdRound(P4_X_Fabrication + crtYdOffset)
        P3_Y_Courtyard = crtYdRound(P7_Y_Fabrication + crtYdOffset)
        P4_X_Courtyard = crtYdRound(P11_X_Fabrication - crtYdOffset)
        P4_Y_Courtyard = crtYdRound(P7_Y_Fabrication + crtYdOffset)
        # Generating Points for the "Silk"-layer (silkscreen)
        # Silklayer starts in top left corner and is drawn counter-clock-wise here
        P1_X_Silk = P1_X_FrontEdgeMarker - silkOffset
        P1_Y_Silk = P1_Y_FrontEdgeMarker + silkEdgeOffset
        P2_X_Silk = P10_X_Fabrication - silkOffset
        P2_Y_Silk = P10_Y_Fabrication + silkOffset
        P3_X_Silk = P9_X_Fabrication - silkOffset
        P3_Y_Silk = P9_Y_Fabrication + silkOffset 
        P4_X_Silk = P8_X_Fabrication - silkOffset
        P4_Y_Silk = P7_Y_Fabrication + silkOffset
        P5_X_Silk = P7_X_Fabrication + silkOffset
        P5_Y_Silk = P7_Y_Fabrication + silkOffset  
        P6_X_Silk = P6_X_Fabrication + silkOffset
        P6_Y_Silk = P6_Y_Fabrication + silkOffset
        P7_X_Silk = P5_X_Fabrication + silkOffset
        P7_Y_Silk = P5_Y_Fabrication + silkOffset                
        P8_X_Silk = P2_X_FrontEdgeMarker + silkOffset
        P8_Y_Silk = P2_Y_FrontEdgeMarker + silkEdgeOffset        
        # Define the position of pads to be placed
        #Pad_X_Left = X_Center - pitchX * ((num_positions - 1) / 2.0)
        #Pad_X_Right = X_Center + pitchX * ((num_positions - 1) / 2.0)
        #Pad_Y_Top = Y_Center - pitchY * ((num_rows - 1) / 2.0)
        #Pad_Y_Bottom = Y_Center + pitchY * ((num_rows - 1) / 2.0)
        Pad_X_Left_First_Row = X_Center - ((pkg_DIM_E / 2.0) - len_REF_E)
        #Pad_X_Right = X_Center + pitchX * ((num_positions - 1) / 2.0)
        Pad_Y_Top_First_Row = Y_Center
        #Pad_Y_Bottom = Y_Center + pitchY * ((num_rows - 1) / 2.0)
        Pad_X_Left_Second_Row = Pad_X_Left_First_Row
        Pad_Y_Top_Second_Row = Pad_Y_Top_First_Row + len_REF_C
        # Define the position of the REF** in silkscreen
        Ref_X_Silk = X_Center
        Ref_Y_Silk = P1_Y_Courtyard - 2.0
        # Define the position of the REF** in fabrication
        Ref_X_Fab = X_Center
        Ref_Y_Fab = Y_Center
        # Define the position of the VALUE in fabrication
        Value_X_Fabrication = X_Center
        Value_Y_Fabrication = P4_Y_Courtyard + 2.0
        # Setting the correct line width for fabrication, courtyard and silk layers
        width_Line_Fabrication = configuration['fab_line_width']
        width_Line_Courtyard = configuration['courtyard_line_width']
        width_line_Silk = configuration['silk_line_width']
        # Place the Text
        f.append(Text(type="reference",
                      text="REF**",
                      at=[Ref_X_Silk, Ref_Y_Silk],
                      layer="F.SilkS",
                      size=s1,
                      thickness=t1))
    
        f.append(Text(type="value",
                      text=fpId,
                      at=[Value_X_Fabrication, Value_Y_Fabrication],
                      layer="F.Fab",
                      size=s1,
                      thickness=t1))
    
        f.append(Text(type="user",
                      text="%R",
                      at=[Ref_X_Fab, Ref_Y_Fab],
                      layer="F.Fab",
                      size=s2,
                      thickness=t2))
        # Place the fabrication layer line
        f.append(PolygoneLine(polygone=[[P1_X_Fabrication, P1_Y_Fabrication],
                                        [P2_X_Fabrication, P2_Y_Fabrication],
                                        [P3_X_Fabrication, P3_Y_Fabrication],
                                        [P4_X_Fabrication, P4_Y_Fabrication],
                                        [P5_X_Fabrication, P5_Y_Fabrication],
                                        [P6_X_Fabrication, P6_Y_Fabrication],
                                        [P7_X_Fabrication, P7_Y_Fabrication],
                                        [P8_X_Fabrication, P8_Y_Fabrication],
                                        [P9_X_Fabrication, P9_Y_Fabrication],
                                        [P10_X_Fabrication, P10_Y_Fabrication],
                                        [P11_X_Fabrication, P11_Y_Fabrication],
                                        [P12_X_Fabrication, P12_Y_Fabrication],
                                        [P1_X_Fabrication, P1_Y_Fabrication]],
                              layer="F.Fab",
                              width=width_Line_Fabrication))
    
        # Place the courtyard layer line
        f.append(RectLine(start=[P1_X_Courtyard, P1_Y_Courtyard],
                          end=[P3_X_Courtyard, P3_Y_Courtyard],
                          layer="F.CrtYd",
                          width=width_Line_Courtyard))
        # Place the silk layer line
        f.append(PolygoneLine(polygone=[[P1_X_Silk, P1_Y_Silk],
                                        [P2_X_Silk, P2_Y_Silk],
                                        [P3_X_Silk, P3_Y_Silk],
                                        [P4_X_Silk, P4_Y_Silk],
                                        [P5_X_Silk, P5_Y_Silk],
                                        [P6_X_Silk, P6_Y_Silk],
                                        [P7_X_Silk, P7_Y_Silk],
                                        [P8_X_Silk, P8_Y_Silk]],
                              layer="F.SilkS",
                              width=width_line_Silk))
    elif (fpParams["option"] == "GP"):
        # Generating Points for the "Fab"-layer (fabrication)
        P1_X_Fabrication = X_Center - (pkg_DIM_M / 2.0)
        P1_Y_Fabrication = Y_Center - len_REF_A - len_REF_B
        P2_X_Fabrication = X_Center + (pkg_DIM_M / 2.0)
        P2_Y_Fabrication = P1_Y_Fabrication
        P3_X_Fabrication = P2_X_Fabrication
        P3_Y_Fabrication = P2_Y_Fabrication + len_REF_N
        P4_X_Fabrication = X_Center + (pkg_DIM_Q_w_GP / 2.0)
        P4_Y_Fabrication = P3_Y_Fabrication
        P5_X_Fabrication = P4_X_Fabrication
        P5_Y_Fabrication = P2_Y_Fabrication + pkg_DIM_P
        P6_X_Fabrication = X_Center + (pkg_DIM_H_w_GP / 2.0)
        P6_Y_Fabrication = P5_Y_Fabrication
        P7_X_Fabrication = P6_X_Fabrication
        P7_Y_Fabrication = P2_Y_Fabrication + pkg_DIM_B
        P8_X_Fabrication = X_Center + (pkg_DIM_M / 2.0)
        P8_Y_Fabrication = P7_Y_Fabrication
        P9_X_Fabrication = P8_X_Fabrication
        P9_Y_Fabrication = P8_Y_Fabrication + pkg_DIM_N
        P10_X_Fabrication = X_Center - (pkg_DIM_M / 2.0)
        P10_Y_Fabrication = P9_Y_Fabrication
        P11_X_Fabrication = P10_X_Fabrication
        P11_Y_Fabrication = P8_Y_Fabrication
        P12_X_Fabrication = X_Center - (pkg_DIM_H_w_GP / 2.0)
        P12_Y_Fabrication = P11_Y_Fabrication
        P13_X_Fabrication = X_Center - (pkg_DIM_H_w_GP / 2.0)
        P13_Y_Fabrication = P6_Y_Fabrication
        P14_X_Fabrication = X_Center - (pkg_DIM_Q_w_GP / 2.0)
        P14_Y_Fabrication = P13_Y_Fabrication
        P15_X_Fabrication = P14_X_Fabrication
        P15_Y_Fabrication = P4_Y_Fabrication
        P16_X_Fabrication = P1_X_Fabrication
        P16_Y_Fabrication = P15_Y_Fabrication
        # Generating Points for the "crtYd"-layer (courty yard)
        P1_X_Courtyard = crtYdRound(P15_X_Fabrication - crtYdOffset)
        P1_Y_Courtyard = crtYdRound(P1_Y_Fabrication - crtYdOffset)
        P2_X_Courtyard = crtYdRound(P4_X_Fabrication + crtYdOffset)
        P2_Y_Courtyard = crtYdRound(P2_Y_Fabrication - crtYdOffset)
        P3_X_Courtyard = crtYdRound(P4_X_Fabrication + crtYdOffset)
        P3_Y_Courtyard = crtYdRound(P9_Y_Fabrication + crtYdOffset)
        P4_X_Courtyard = crtYdRound(P14_X_Fabrication - crtYdOffset)
        P4_Y_Courtyard = crtYdRound(P10_Y_Fabrication + crtYdOffset)
        # Generating Points for the "Silk"-layer (silkscreen)
        # Silklayer starts in top left corner and is drawn counter-clock-wise here
        P1_X_Silk = P1_X_FrontEdgeMarker - silkOffset
        P1_Y_Silk = P1_Y_FrontEdgeMarker + silkEdgeOffset
        P2_X_Silk = P14_X_Fabrication - silkOffset
        P2_Y_Silk = P14_Y_Fabrication + silkOffset
        P3_X_Silk = P13_X_Fabrication - silkOffset
        P3_Y_Silk = P13_Y_Fabrication + silkOffset
        P4_X_Silk = P12_X_Fabrication - silkOffset
        P4_Y_Silk = P12_Y_Fabrication + silkOffset
        P5_X_Silk = P11_X_Fabrication - silkOffset
        P5_Y_Silk = P11_Y_Fabrication + silkOffset
        P6_X_Silk = P10_X_Fabrication - silkOffset
        P6_Y_Silk = P10_Y_Fabrication + silkOffset
        P7_X_Silk = P9_X_Fabrication + silkOffset
        P7_Y_Silk = P9_Y_Fabrication + silkOffset
        P8_X_Silk = P8_X_Fabrication + silkOffset
        P8_Y_Silk = P7_Y_Fabrication + silkOffset
        P9_X_Silk = P7_X_Fabrication + silkOffset
        P9_Y_Silk = P7_Y_Fabrication + silkOffset 
        P10_X_Silk = P6_X_Fabrication + silkOffset
        P10_Y_Silk = P6_Y_Fabrication + silkOffset 
        P11_X_Silk = P5_X_Fabrication + silkOffset
        P11_Y_Silk = P5_Y_Fabrication + silkOffset
        P12_X_Silk = P2_X_FrontEdgeMarker + silkOffset
        P12_Y_Silk = P2_Y_FrontEdgeMarker + silkEdgeOffset
        # Define the position of pads to be placed
        #Pad_X_Left = X_Center - pitchX * ((num_positions - 1) / 2.0)
        #Pad_X_Right = X_Center + pitchX * ((num_positions - 1) / 2.0)
        #Pad_Y_Top = Y_Center - pitchY * ((num_rows - 1) / 2.0)
        #Pad_Y_Bottom = Y_Center + pitchY * ((num_rows - 1) / 2.0)
        Pad_X_Left_First_Row = X_Center - ((pkg_DIM_E / 2.0) - len_REF_E)
        #Pad_X_Right = X_Center + pitchX * ((num_positions - 1) / 2.0)
        Pad_Y_Top_First_Row = Y_Center
        #Pad_Y_Bottom = Y_Center + pitchY * ((num_rows - 1) / 2.0)
        Pad_X_Left_Second_Row = Pad_X_Left_First_Row
        Pad_Y_Top_Second_Row = Pad_Y_Top_First_Row + len_REF_C
        # Define the position of the REF** in silkscreen
        Ref_X_Silk = X_Center
        Ref_Y_Silk = P1_Y_Courtyard - 2.0
        # Define the position of the REF** in fabrication
        Ref_X_Fab = X_Center
        Ref_Y_Fab = Y_Center
        # Define the position of the VALUE in fabrication
        Value_X_Fabrication = X_Center
        Value_Y_Fabrication = P4_Y_Courtyard + 2.0
        # Setting the correct line width for fabrication, courtyard and silk layers
        width_Line_Fabrication = configuration['fab_line_width']
        width_Line_Courtyard = configuration['courtyard_line_width']
        width_line_Silk = configuration['silk_line_width']
        # Place the Text
        f.append(Text(type="reference",
                      text="REF**",
                      at=[Ref_X_Silk, Ref_Y_Silk],
                      layer="F.SilkS",
                      size=s1,
                      thickness=t1))
    
        f.append(Text(type="value",
                      text=fpId,
                      at=[Value_X_Fabrication, Value_Y_Fabrication],
                      layer="F.Fab",
                      size=s1,
                      thickness=t1))
    
        f.append(Text(type="user",
                      text="%R",
                      at=[Ref_X_Fab, Ref_Y_Fab],
                      layer="F.Fab",
                      size=s2,
                      thickness=t2))
        # Place the fabrication layer line
        f.append(PolygoneLine(polygone=[[P1_X_Fabrication, P1_Y_Fabrication],
                                        [P2_X_Fabrication, P2_Y_Fabrication],
                                        [P3_X_Fabrication, P3_Y_Fabrication],
                                        [P4_X_Fabrication, P4_Y_Fabrication],
                                        [P5_X_Fabrication, P5_Y_Fabrication],
                                        [P6_X_Fabrication, P6_Y_Fabrication],
                                        [P7_X_Fabrication, P7_Y_Fabrication],
                                        [P8_X_Fabrication, P8_Y_Fabrication],
                                        [P9_X_Fabrication, P9_Y_Fabrication],
                                        [P10_X_Fabrication, P10_Y_Fabrication],
                                        [P11_X_Fabrication, P11_Y_Fabrication],
                                        [P12_X_Fabrication, P12_Y_Fabrication],
                                        [P13_X_Fabrication, P13_Y_Fabrication],
                                        [P14_X_Fabrication, P14_Y_Fabrication],
                                        [P15_X_Fabrication, P15_Y_Fabrication],
                                        [P16_X_Fabrication, P16_Y_Fabrication],
                                        [P1_X_Fabrication, P1_Y_Fabrication]],
                              layer="F.Fab",
                              width=width_Line_Fabrication))
    
        # Place the courtyard layer line
        f.append(RectLine(start=[P1_X_Courtyard, P1_Y_Courtyard],
                          end=[P3_X_Courtyard, P3_Y_Courtyard],
                          layer="F.CrtYd",
                          width=width_Line_Courtyard))
        # Place the silk layer line
        f.append(PolygoneLine(polygone=[[P1_X_Silk, P1_Y_Silk],
                                        [P2_X_Silk, P2_Y_Silk],
                                        [P3_X_Silk, P3_Y_Silk],
                                        [P4_X_Silk, P4_Y_Silk],
                                        [P5_X_Silk, P5_Y_Silk],
                                        [P6_X_Silk, P6_Y_Silk],
                                        [P7_X_Silk, P7_Y_Silk],
                                        [P8_X_Silk, P8_Y_Silk],
                                        [P9_X_Silk, P9_Y_Silk],
                                        [P10_X_Silk, P10_Y_Silk],
                                        [P11_X_Silk, P11_Y_Silk],
                                        [P12_X_Silk, P12_Y_Silk]],
                              layer="F.SilkS",
                              width=width_line_Silk))
    elif (fpParams["option"] == "LP"): # This is the without GP-option or LP-option
        # Generating Points for the "Fab"-layer (fabrication)
        P1_X_Fabrication = X_Center - (pkg_DIM_M / 2.0)
        P1_Y_Fabrication = Y_Center - (len_REF_A + len_REF_B)
        P2_X_Fabrication = X_Center + (pkg_DIM_M / 2.0)
        P2_Y_Fabrication = P1_Y_Fabrication
        P3_X_Fabrication = P2_X_Fabrication
        P3_Y_Fabrication = P2_Y_Fabrication + len_REF_N
        P4_X_Fabrication = X_Center + (pkg_DIM_H_LP / 2.0)
        P4_Y_Fabrication = P3_Y_Fabrication
        P5_X_Fabrication = P4_X_Fabrication
        P5_Y_Fabrication = P2_Y_Fabrication + pkg_DIM_B
        P6_X_Fabrication = P3_X_Fabrication
        P6_Y_Fabrication = P5_Y_Fabrication
        P7_X_Fabrication = P6_X_Fabrication
        P7_Y_Fabrication = P6_Y_Fabrication + pkg_DIM_N
        P8_X_Fabrication = P1_X_Fabrication
        P8_Y_Fabrication = P7_Y_Fabrication
        P9_X_Fabrication = P8_X_Fabrication
        P9_Y_Fabrication = P6_Y_Fabrication
        P10_X_Fabrication = X_Center - (pkg_DIM_H_LP / 2.0)
        P10_Y_Fabrication = P9_Y_Fabrication
        P11_X_Fabrication = P10_X_Fabrication
        P11_Y_Fabrication = P3_Y_Fabrication
        P12_X_Fabrication = P1_X_Fabrication
        P12_Y_Fabrication = P11_Y_Fabrication
        # Generating Points for the "crtYd"-layer (courty yard)
        P1_X_Courtyard = crtYdRound(P11_X_Fabrication - crtYdOffset)
        P1_Y_Courtyard = crtYdRound(P1_Y_Fabrication - crtYdOffset)
        P2_X_Courtyard = crtYdRound(P4_X_Fabrication + crtYdOffset)
        P2_Y_Courtyard = crtYdRound(P1_Y_Fabrication - crtYdOffset)
        P3_X_Courtyard = crtYdRound(P4_X_Fabrication + crtYdOffset)
        P3_Y_Courtyard = crtYdRound(P7_Y_Fabrication + crtYdOffset)
        P4_X_Courtyard = crtYdRound(P11_X_Fabrication - crtYdOffset)
        P4_Y_Courtyard = crtYdRound(P7_Y_Fabrication + crtYdOffset)
        # Generating Points for the "Silk"-layer (silkscreen)
        # Silklayer starts in top left corner and is drawn counter-clock-wise here
        P1_X_Silk = P1_X_FrontEdgeMarker - silkOffset
        P1_Y_Silk = P1_Y_FrontEdgeMarker + silkEdgeOffset
        P2_X_Silk = P10_X_Fabrication - silkOffset
        P2_Y_Silk = P10_Y_Fabrication + silkOffset
        P3_X_Silk = P9_X_Fabrication - silkOffset
        P3_Y_Silk = P9_Y_Fabrication + silkOffset
        P4_X_Silk = P8_X_Fabrication - silkOffset
        P4_Y_Silk = P7_Y_Fabrication + silkOffset 
        P5_X_Silk = P7_X_Fabrication + silkOffset
        P5_Y_Silk = P7_Y_Fabrication + silkOffset 
        P6_X_Silk = P6_X_Fabrication + silkOffset
        P6_Y_Silk = P6_Y_Fabrication + silkOffset
        P7_X_Silk = P5_X_Fabrication + silkOffset
        P7_Y_Silk = P5_Y_Fabrication + silkOffset
        P8_X_Silk = P2_X_FrontEdgeMarker + silkOffset
        P8_Y_Silk = P2_Y_FrontEdgeMarker + silkEdgeOffset
        # Define the position of pads to be placed
        #Pad_X_Left = X_Center - pitchX * ((num_positions - 1) / 2.0)
        #Pad_X_Right = X_Center + pitchX * ((num_positions - 1) / 2.0)
        #Pad_Y_Top = Y_Center - pitchY * ((num_rows - 1) / 2.0)
        #Pad_Y_Bottom = Y_Center + pitchY * ((num_rows - 1) / 2.0)
        Pad_X_Left_First_Row = X_Center - ((pkg_DIM_E / 2.0) - len_REF_E)
        #Pad_X_Right = X_Center + pitchX * ((num_positions - 1) / 2.0)
        Pad_Y_Top_First_Row = Y_Center
        #Pad_Y_Bottom = Y_Center + pitchY * ((num_rows - 1) / 2.0)
        Pad_X_Left_Second_Row = Pad_X_Left_First_Row
        Pad_Y_Top_Second_Row = Pad_Y_Top_First_Row + len_REF_C
        # Define the position of the REF** in silkscreen
        Ref_X_Silk = X_Center
        Ref_Y_Silk = P1_Y_Courtyard - 2.0
        # Define the position of the REF** in fabrication
        Ref_X_Fab = X_Center
        Ref_Y_Fab = Y_Center
        # Define the position of the VALUE in fabrication
        Value_X_Fabrication = X_Center
        Value_Y_Fabrication = P4_Y_Courtyard + 2.0
        # Setting the correct line width for fabrication, courtyard and silk layers
        width_Line_Fabrication = configuration['fab_line_width']
        width_Line_Courtyard = configuration['courtyard_line_width']
        width_line_Silk = configuration['silk_line_width']
        # Place the Text
        f.append(Text(type="reference",
                      text="REF**",
                      at=[Ref_X_Silk, Ref_Y_Silk],
                      layer="F.SilkS",
                      size=s1,
                      thickness=t1))
    
        f.append(Text(type="value",
                      text=fpId,
                      at=[Value_X_Fabrication, Value_Y_Fabrication],
                      layer="F.Fab",
                      size=s1,
                      thickness=t1))
    
        f.append(Text(type="user",
                      text="%R",
                      at=[Ref_X_Fab, Ref_Y_Fab],
                      layer="F.Fab",
                      size=s2,
                      thickness=t2))
        # Place the fabrication layer line
        f.append(PolygoneLine(polygone=[[P1_X_Fabrication, P1_Y_Fabrication],
                                        [P2_X_Fabrication, P2_Y_Fabrication],
                                        [P3_X_Fabrication, P3_Y_Fabrication],
                                        [P4_X_Fabrication, P4_Y_Fabrication],
                                        [P5_X_Fabrication, P5_Y_Fabrication],
                                        [P6_X_Fabrication, P6_Y_Fabrication],
                                        [P7_X_Fabrication, P7_Y_Fabrication],
                                        [P8_X_Fabrication, P8_Y_Fabrication],
                                        [P9_X_Fabrication, P9_Y_Fabrication],
                                        [P10_X_Fabrication, P10_Y_Fabrication],
                                        [P11_X_Fabrication, P11_Y_Fabrication],
                                        [P12_X_Fabrication, P12_Y_Fabrication],
                                        [P1_X_Fabrication, P1_Y_Fabrication]],
                              layer="F.Fab",
                              width=width_Line_Fabrication))
    
        # Place the courtyard layer line
        f.append(RectLine(start=[P1_X_Courtyard, P1_Y_Courtyard],
                          end=[P3_X_Courtyard, P3_Y_Courtyard],
                          layer="F.CrtYd",
                          width=width_Line_Courtyard))
        # Place the silk layer line
        f.append(PolygoneLine(polygone=[[P1_X_Silk, P1_Y_Silk],
                                        [P2_X_Silk, P2_Y_Silk],
                                        [P3_X_Silk, P3_Y_Silk],
                                        [P4_X_Silk, P4_Y_Silk],
                                        [P5_X_Silk, P5_Y_Silk],
                                        [P6_X_Silk, P6_Y_Silk],
                                        [P7_X_Silk, P7_Y_Silk],
                                        [P8_X_Silk, P8_Y_Silk]],
                              layer="F.SilkS",
                              width=width_line_Silk))
    else:
        print('Error, this type of option={} is not defined in general'.format(fpParams["option"]))
        sys.exit()        
    
    ########################### Pin 1 - Marker #################################
    markerOffset = 0.4
    markerLength = pad_size_x
    
    PM1_X_Pin1Marker = Pad_X_Left_First_Row
    PM1_Y_Pin1Marker = P1_Y_Silk + markerOffset + markerLength
    
    PM2_X_Pin1Marker = PM1_X_Pin1Marker - (markerLength / 2)
    PM2_Y_Pin1Marker = PM1_Y_Pin1Marker - (markerLength / sqrt(2))
    
    PM3_X_Pin1Marker = PM2_X_Pin1Marker + markerLength
    PM3_Y_Pin1Marker = PM2_Y_Pin1Marker
    
    # Silk
    f.append(PolygoneLine(polygone=[[PM1_X_Pin1Marker, PM1_Y_Pin1Marker],
                                    [PM2_X_Pin1Marker, PM2_Y_Pin1Marker],
                                    [PM3_X_Pin1Marker, PM3_Y_Pin1Marker],
                                    [PM1_X_Pin1Marker, PM1_Y_Pin1Marker]],
                          layer="F.SilkS",
                          width=width_line_Silk))
    
    ########################### Pads Generation ###################
    # Pads generated according pin_order
    # tlbr = top left to bottom right
    # trbl = top right to bottom left
    # bltr = bottom left to top right
    # brtl = bottom right to top left
    pad_array_size = num_positions * num_rows
    if row_skips == []:
        for _ in range(num_rows):
            row_skips.append([])
    for row_num, row in zip(range(num_rows), row_names):
        row_set = set(range(1, num_positions + 1))
        for item in row_skips[row_num]:
            try:
                # If item is a range, remove that range
                row_set -= set(range(*item))
                pad_array_size -= item[1] - item[0]
            except TypeError:
                # If item is an int, remove that int
                row_set -= {item}
                pad_array_size -= 1
        for col in row_set:
            if pin_order == "tlbr":
                if (row_num == 0):
                    # Apply the pad itself without a solder paste mask            
                    f.append(Pad(number="{}{}".format(row, col),
                                 type=Pad.TYPE_SMT,
                                 shape=padShape,
                                 at=[Pad_X_Left_First_Row + (col-1) * pitchX, Pad_Y_Top_First_Row + row_num * pitchY],
                                 size=[pad_size_x, pad_size_y],
                                 #layers=Pad.LAYERS_SMT,
                                 layers=['F.Cu', 'F.Mask'], 
                                 radius_ratio=config['round_rect_radius_ratio']))
                    # Apply the solder paste mask 
                    f.append(Pad(number="{}{}".format(row, col),
                                 type=Pad.TYPE_SMT,
                                 shape=padShape,
                                 at=[Pad_X_Left_First_Row + (col-1) * pitchX, Pad_Y_Top_First_Row + row_num * pitchY],
                                 size=[pad_stencil_size_x, pad_stencil_size_y],
                                 #layers=Pad.LAYERS_SMT,
                                 layers=['F.Paste'],
                                 radius_ratio=config['round_rect_radius_ratio']))
                else:
                    ## Apply the pad itself without a solder paste mask 
                    f.append(Pad(number="{}{}".format(row, col),
                                 type=Pad.TYPE_SMT,
                                 shape=padShape,
                                 at=[Pad_X_Left_Second_Row + (col-1) * pitchX, Pad_Y_Top_Second_Row + ((row_num - 1) * pitchY)],
                                 size=[pad_size_x, pad_size_y],
                                 #layers=Pad.LAYERS_SMT,
                                 layers=['F.Cu', 'F.Mask'],
                                 radius_ratio=config['round_rect_radius_ratio']))
                    # Apply the solder paste mask
                    f.append(Pad(number="{}{}".format(row, col),
                                 type=Pad.TYPE_SMT,
                                 shape=padShape,
                                 at=[Pad_X_Left_Second_Row + (col-1) * pitchX, Pad_Y_Top_Second_Row + ((row_num - 1) * pitchY)],
                                 size=[pad_stencil_size_x, pad_stencil_size_y],
                                 #layers=Pad.LAYERS_SMT,
                                 layers=['F.Paste'],
                                 radius_ratio=config['round_rect_radius_ratio']))
            elif pin_order == "trbl":
                f.append(Pad(number="{}{}".format(row, col),
                             type=Pad.TYPE_SMT,
                             shape=padShape,
                             at=[Pad_X_Right - (col-1) * pitchX, Pad_Y_Top + row_num * pitchY],
                             size=[pad_size_x, pad_size_y],
                             layers=Pad.LAYERS_SMT, 
                             radius_ratio=config['round_rect_radius_ratio']))
            elif pin_order == "bltr":
                f.append(Pad(number="{}{}".format(row, col),
                             type=Pad.TYPE_SMT,
                             shape=padShape,
                             at=[Pad_X_Left + (col-1) * pitchX, Pad_Y_Bottom - row_num * pitchY],
                             size=[pad_size_x, pad_size_y],
                             layers=Pad.LAYERS_SMT, 
                             radius_ratio=config['round_rect_radius_ratio']))
            elif pin_order == "brtl":
                f.append(Pad(number="{}{}".format(row, col),
                             type=Pad.TYPE_SMT,
                             shape=padShape,
                             at=[Pad_X_Right - (col-1) * pitchX, Pad_Y_Bottom - row_num * pitchY],
                             size=[pad_size_x, pad_size_y],
                             layers=Pad.LAYERS_SMT, 
                             radius_ratio=config['round_rect_radius_ratio']))
            else:
                print('Error, pin_order = {} does not exist.'.format(pin_order))
                sys.exit()
                
    ##################  Alignment Holes NPTH  ########################
    # Those are all the same for "NONE", "GP" or "LP"
    PAH1_X_AlignmentHole = X_Center - (pkg_DIM_E / 2.0)
    PAH1_Y_AlignmentHole = Y_Center
    
    f.append(Pad(at=[PAH1_X_AlignmentHole, PAH1_Y_AlignmentHole],
                 number="",
                 type=Pad.TYPE_NPTH,
                 shape=Pad.SHAPE_CIRCLE,
                 size=npth_drill_AlignmentHole,
                 drill=npth_drill_AlignmentHole,
                 layers=Pad.LAYERS_NPTH))

    PAH2_X_AlignmentHole = X_Center + (pkg_DIM_E / 2.0)
    PAH2_Y_AlignmentHole = Y_Center

    f.append(Pad(at=[PAH2_X_AlignmentHole, PAH2_Y_AlignmentHole],
                 number="",
                 type=Pad.TYPE_NPTH,
                 shape=Pad.SHAPE_CIRCLE,
                 size=npth_drill_AlignmentHole,
                 drill=npth_drill_AlignmentHole,
                 layers=Pad.LAYERS_NPTH))
    
    ##################  Latch Post Holes PTH  ########################    
    # Latch post holes PTH for "NONE" or "GP" version
    if ((fpParams["option"] == "NONE") or (fpParams["option"] == "GP")):
        PAH1_X_LatchPostHole = X_Center - (pkg_DIM_F / 2.0)
        PAH1_Y_LatchPostHole = Y_Center - len_REF_D
        PAH2_X_LatchPostHole = X_Center + (pkg_DIM_F / 2.0)
        PAH2_Y_LatchPostHole = PAH1_Y_LatchPostHole
        PAH3_X_LatchPostHole = PAH1_X_LatchPostHole
        PAH3_Y_LatchPostHole = PAH1_Y_LatchPostHole + pkg_DIM_C
        PAH4_X_LatchPostHole = PAH2_X_LatchPostHole
        PAH4_Y_LatchPostHole = PAH3_Y_LatchPostHole
        
        f.append(Pad(at=[PAH1_X_LatchPostHole, PAH1_Y_LatchPostHole],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH2_X_LatchPostHole, PAH2_Y_LatchPostHole],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH3_X_LatchPostHole, PAH3_Y_LatchPostHole],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH4_X_LatchPostHole, PAH4_Y_LatchPostHole],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
    elif (fpParams["option"] == "LP"):
        PAH1_X_LatchPostHoleLeftSide = X_Center - (pkg_DIM_G_LP / 2.0)
        PAH1_Y_LatchPostHoleLeftSide = Y_Center - len_REF_D
        PAH2_X_LatchPostHoleLeftSide = X_Center - (pkg_DIM_F / 2.0)
        PAH2_Y_LatchPostHoleLeftSide = PAH1_Y_LatchPostHoleLeftSide
        PAH3_X_LatchPostHoleLeftSide = PAH1_X_LatchPostHoleLeftSide
        PAH3_Y_LatchPostHoleLeftSide = PAH1_Y_LatchPostHoleLeftSide + pkg_DIM_C
        PAH4_X_LatchPostHoleLeftSide = PAH2_X_LatchPostHoleLeftSide
        PAH4_Y_LatchPostHoleLeftSide = PAH3_Y_LatchPostHoleLeftSide
        
        f.append(Pad(at=[PAH1_X_LatchPostHoleLeftSide, PAH1_Y_LatchPostHoleLeftSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH2_X_LatchPostHoleLeftSide, PAH2_Y_LatchPostHoleLeftSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH3_X_LatchPostHoleLeftSide, PAH3_Y_LatchPostHoleLeftSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH4_X_LatchPostHoleLeftSide, PAH4_Y_LatchPostHoleLeftSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        PAH1_X_LatchPostHoleRightSide = X_Center + (pkg_DIM_G_LP / 2.0)
        PAH1_Y_LatchPostHoleRightSide = Y_Center - len_REF_D
        PAH2_X_LatchPostHoleRightSide = X_Center + (pkg_DIM_F / 2.0)
        PAH2_Y_LatchPostHoleRightSide = PAH1_Y_LatchPostHoleRightSide
        PAH3_X_LatchPostHoleRightSide = PAH1_X_LatchPostHoleRightSide
        PAH3_Y_LatchPostHoleRightSide = PAH1_Y_LatchPostHoleRightSide + pkg_DIM_C
        PAH4_X_LatchPostHoleRightSide = PAH2_X_LatchPostHoleRightSide
        PAH4_Y_LatchPostHoleRightSide = PAH3_Y_LatchPostHoleRightSide
        
        f.append(Pad(at=[PAH1_X_LatchPostHoleRightSide, PAH1_Y_LatchPostHoleRightSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH2_X_LatchPostHoleRightSide, PAH2_Y_LatchPostHoleRightSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH3_X_LatchPostHoleRightSide, PAH3_Y_LatchPostHoleRightSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
        
        f.append(Pad(at=[PAH4_X_LatchPostHoleRightSide, PAH4_Y_LatchPostHoleRightSide],
                     number="",
                     type=Pad.TYPE_THT,
                     shape=Pad.SHAPE_CIRCLE,
                     size=pth_pad,
                     drill= pth_drill,
                     layers=Pad.LAYERS_THT))
    else:
        print('Error, this type of option={} is not defined for Latch Post Holes'.format(fpParams["option"]))
        sys.exit()   
        
    ##################  Gereration of File-Name, Description and Tags  ########################
    # Prepare name variables for footprint folder, footprint name, etc.
    familiyType = fpParams['family']
    packageType = fpId

    f.append(Model(filename="{}Connector_Samtec_{}.3dshapes/{}.wrl".format(
                  config['3d_model_prefix'], familiyType, fpId)))

    f.setDescription("{0}, {1}x{2}mm, {3} Ball, {4}x{5} Layout, {6}mm Pitch, {7}".format(
                     fpId,
                     pkg_DIM_M,
                     (pkg_DIM_B + pkg_DIM_N),
                     pad_array_size,
                     num_positions,
                     num_rows,
                     pitchString,
                     size_source))
    f.setTags("{} {} {}{}".format(
              packageType,
              pad_array_size,
              pitchString,
              additionalTag))

    outputDir = 'Connector_Samtec_{lib_name:s}.pretty/'.format(lib_name=familiyType)
    if not os.path.isdir(outputDir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(outputDir)
    filename = '{outdir:s}{fpId:s}.kicad_mod'.format(outdir=outputDir, fpId=fpId)
    
    file_handler = KicadFileHandler(f)
    file_handler.writeFile(filename)

def crtYdRound(x):
        # Round away from zero for proper courtyard calculation
        neg = x < 0
        if neg:
            x = -x
        x = math.ceil(x * 100) / 100.0
        if neg:
            x = -x
        return x
    
def rowNameGenerator(seq):
    for n in itertools.count(1):
        for s in itertools.product(seq, repeat = n):
            yield ''.join(s)

def getTableEntry(table, number):
    pkg_val = -1
    for i in range(len(table[0])):
        #print('{}'.format(table[0][i]))
        if table[0][i] == number:
            pkg_val = table[1][i]
            break; # quit the for-loop when a correct match is made to reduce script duration time
    return pkg_val
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../../tools/global_config_files/config_KLCv3.0.yaml')
    # parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../package_config_KLCv3.yaml')

    args = parser.parse_args()
    
    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    # with open(args.series_config, 'r') as config_stream:
        # try:
            # configuration.update(yaml.safe_load(config_stream))
        # except yaml.YAMLError as exc:
            # print(exc)
    
    # generate dict of A, B .. Y, Z, AA, AB .. CY less easily-confused letters
    rowNamesList = [x for x in ascii_uppercase if x not in ["I", "O", "Q", "S", "X", "Z"]]
    configuration.update({'row_names': list(itertools.islice(rowNameGenerator(rowNamesList), 80))})

    for filepath in args.files:
        with open(filepath, 'r') as command_stream:
            try:
                cmd_file = yaml.safe_load(command_stream)
            except yaml.YAMLError as exc:
                print(exc)
        for pkg in cmd_file:
            generateFootprint(configuration, cmd_file[pkg], pkg)