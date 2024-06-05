#!/usr/bin/env python3

# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at> (TE connectivity)
# (C) 2024 by Uli Köhler <kicad@techoverflow.net> (JUSHUO)

"""

Family of 1.0mm pitch FFC connectors
https://datasheet.lcsc.com/lcsc/2304140030_JUSHUO-AFA07-S10FCA-00_C262716.pdf

"""

import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import sqrt
import argparse
import yaml
from helpers import *
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

manufacturer = "JUSHUO"
conn_category = "FFC-FPC"

datasheet = "https://datasheet.lcsc.com/lcsc/2304140030_JUSHUO-AFA07-S10FCA-00_C262716.pdf"

lib_by_conn_category = True

pincounts = range(4, 30)

def generate_one_footprint(pincount, configuration):

    footprint_name = f'JUSHUO_AFA07-S{pincount:02g}FCA-00_1x{pincount}-1MP_P1.0mm_Horizontal'
    print(f'Building {footprint_name}')

    # "Global" Y offset, so the part is centered for pick & place
    pad_y = -6.75/2 # Total Y dimension of part with retracted actuator,
    # see graphic below "Section A-A" in the datasheet

    pitch = 1 # Attribute of part family
    
    # Pin pad (1..n) properties
    pad_width = 0.6 # Datasheet, suggested pad layout
    pad_height = 1.8 # Datasheet, suggested pad layout
    pad_x_span = pitch * (pincount - 1)
    pad1_x = pad_x_span / 2.0
    
    marker_y = 0.8*pad_height # How long the pin 1 marker is in vertical direction
    
    # How much further than the body do the pins extend in Y direction?
    pin_protrusion_from_body = 1.45 # Below "Section A-A" in datasheet

    # Mounting pad properties
    mounting_pad_width = 2.6
    mounting_pad_height = 3.0
    tab_x = pad_x_span / 2.0 + 1.05 + mounting_pad_width / 2.0
    # 0.23 Determined by measuring footprint against datasheet recommendation (4.57mm)
    tab_y = pad_y + pad_height / 2.0 + mounting_pad_height / 2.0 - 0.23

    # Compute position of top left corner of body (?)
    body_y1 = pad_y + pad_height / 2.0
    
    # Compute body width
    body_width =  5.05+(pitch*pincount) # Dim "C" in datasheet
    half_body_width = body_width / 2.0
    
    # Compute width of the actuator (in X direction)
    actuator_width = 7+(pitch*pincount) # Dim "D" in datasheet
    half_actuator_width = actuator_width / 2.0
    
    # Actuator position in extended and retracted state
    actuator_y1 = body_y1 + 6.75 - pin_protrusion_from_body # "Section A-A" in datasheet
    actuator_y2 = body_y1 + 8.4 - pin_protrusion_from_body # Below "Section A-A" in datasheet
    
    acutator_height = 1.0 # Extent of actuator part in Y direction. Measured from EasyEDA model.

    body_edge = {
        'left': -half_body_width,
        'right': half_body_width,
        'top': body_y1,
        'bottom': actuator_y1
    }

    silk_clearance = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    nudge = configuration['silk_fab_offset']

    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = roundToBase(half_actuator_width + courtyard_clearance, courtyard_precision)
    courtyard_y1 = roundToBase(pad_y - pad_height / 2.0 - courtyard_clearance, courtyard_precision)
    courtyard_y2 = roundToBase(actuator_y2 + courtyard_clearance, courtyard_precision)

    # initialise footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription(f'JUSHUO FPC connector, {pincount:02g} bottom-side contacts, 1.0mm pitch, 2.5mm height, SMT, {datasheet}')
    kicad_mod.setTags('jushuo lcsc fpc')

    # Create pads (1..n)
    kicad_mod.append(PadArray(pincount=pincount, x_spacing=pitch, center=[0,pad_y],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_width, pad_height], layers=Pad.LAYERS_SMT))

    # Create tab (smt mounting) pads
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
        at=[-tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[mounting_pad_width, mounting_pad_height], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
        at=[tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[mounting_pad_width, mounting_pad_height], layers=Pad.LAYERS_SMT))
    
    # Start of the angled side section of the actuator
    actuator_angle_start_y = actuator_y1-acutator_height - 1.5 # 1.5mm measured from EasyEDA model
    # Where the rectangular (slightly wider) section of the actuator starts
    actuator_rectangular_section_start_y = actuator_angle_start_y - 1 # 1mm measured from EasyEDA model
    actuator_rectangular_section_half_width = half_actuator_width - 0.35 # 0.35: EasyEDA

    # create fab outline and pin 1 marker
    kicad_mod.append(PolygonLine(
        polygon=[
            # Left upper corner
            [-half_body_width, body_y1],
            # Right upper corner
            [half_body_width, body_y1],
            
            # Rectangular section of actuator
            [half_body_width, actuator_rectangular_section_start_y], # Start
            [actuator_rectangular_section_half_width, actuator_rectangular_section_start_y],
            [actuator_rectangular_section_half_width, actuator_angle_start_y], # Down
            
            # Actuator angled section
            [half_actuator_width, actuator_y1-acutator_height],
            
            # Front (cable-facing) section of actuator
            [half_actuator_width, actuator_y1],
            
            # Line from lower right to lower left corner
            [-half_actuator_width, actuator_y1],
            [-half_actuator_width, actuator_y1-acutator_height],
            
            # Actuator angled section
            [-half_actuator_width, actuator_y1-acutator_height],
            
            # Rectangular section of actuator
            [-actuator_rectangular_section_half_width, actuator_angle_start_y], # Up
            [-actuator_rectangular_section_half_width, actuator_rectangular_section_start_y],
            [-half_body_width, actuator_rectangular_section_start_y], # Start

            # End            
            [-half_body_width, body_y1],
            [-half_body_width, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    kicad_mod.append(PolygonLine(
        polygon=[
            [-pad1_x-0.5, body_y1],
            [-pad1_x, body_y1+1],
            [-pad1_x+0.5, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create open actuator outline, only on F.Fab
    kicad_mod.append(PolygonLine(
        polygon=[
            [half_body_width, actuator_y1],
            [half_body_width, actuator_y2-acutator_height],
            [half_actuator_width, actuator_y2-acutator_height],
            [half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2-acutator_height],
            [-half_body_width, actuator_y2-acutator_height],
            [-half_body_width, actuator_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    #
    # create silkscreen outline and pin 1 marker
    #
    
    # Silkscreen outline
    kicad_mod.append(PolygonLine(
        polygon=[
            [actuator_rectangular_section_half_width+nudge,actuator_rectangular_section_start_y-nudge],
            [actuator_rectangular_section_half_width+nudge, actuator_angle_start_y],
            
            [half_actuator_width+nudge, actuator_y1-acutator_height],
            [half_actuator_width+nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1-acutator_height],
            
            [-actuator_rectangular_section_half_width-nudge, actuator_angle_start_y],
            [-actuator_rectangular_section_half_width-nudge,actuator_rectangular_section_start_y-nudge],
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygonLine(
        polygon=[
            [-tab_x+mounting_pad_width/2.0+silk_clearance, body_y1-nudge],
            [-pad1_x-pad_width/2.0-silk_clearance, body_y1-nudge],
            [-pad1_x-pad_width/2.0-silk_clearance, body_y1-nudge-marker_y]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(Line(
        start=[pad1_x+pad_width/2.0+silk_clearance, body_y1-nudge],
        end=[tab_x-mounting_pad_width/2.0-silk_clearance, body_y1-nudge],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # create courtyard
    kicad_mod.append(RectLine(start=[-courtyard_x, courtyard_y1], end=[courtyard_x, courtyard_y2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
    # kicad_mod.append(Text(type='reference', text='REF**', size=[1,1], at=[0, courtyard_y1 - label_y_offset], layer='F.SilkS'))
    # kicad_mod.append(Text(type='user', text='${REFERENCE}', size=[1,1], at=[0, tab_y], layer='F.Fab'))
    # kicad_mod.append(Text(type='value', text=footprint_name, at=[0, courtyard_y2 + label_y_offset], layer='F.Fab'))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':courtyard_y1, 'bottom':courtyard_y2}, fp_name=footprint_name, text_y_inside_position=[0, tab_y])

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KICAD8_3DMODEL_DIR}/')

    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
        lib_name = configuration['lib_name_format_string'].format(man=manufacturer)

    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    # with pincount(s) and partnumber(s) to be generated, build them all in a nested loop
    for pincount in pincounts:
        generate_one_footprint(pincount, configuration)
