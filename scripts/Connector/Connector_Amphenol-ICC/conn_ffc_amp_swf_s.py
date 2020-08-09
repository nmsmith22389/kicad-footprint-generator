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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

"""

The SFW series of flex connectors was originally developed by FCI, which was acquired 
2016 by Amphenol. The SFW is designed for connecting flat flex cables (FFC), flexible
printed circuits (FPC) and conductive ink circuits (CIC) with pitch 1.0mm through 
surface mount technology (SMT). The series has vertical ("straight") and horizontal 
("right angle") mounting options for up to 30 positions and is available in lead-free 
matte tin and gold-flash plating options. The right-angled versions are available with 
the contacts orientated in either lower or upper position.

This script works for the straight version only and will generate codes for the 
FFC/FPC versions only. Variations include the presence of a mounting plate, which
provides more mechanical robustness ("STM" variants) and without ("ST" variants). 
The final LF in the product codes stands for lead-free and is default.

Example product code (spaces to be ignored):
SFW 8 S - 2 ST E1 LF
|   | |   | |   |  + lead free
|   | |   | |   + package style
|   | |   | + ST: without mounting plate
|   | |   + 2: for FPC/FFC
|   | + S: straight type
|   + number of contact
+ name of the series

Product Specification:
https://cdn.amphenol-icc.com/media/wysiwyg/files/documentation/sc-sfws03.pdf

Drawing:
https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/sfw_s-2st_e1lf.pdf

"""

import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import sqrt, floor
import argparse
import yaml
from helpers import *
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

manufacturer = "Amphenol-ICC"
conn_category = "FFC-FPC"

lib_by_conn_category = True

variants = ['ST', 'STM']
pincounts = range(4, 30)

def generate_one_footprint(pincount, variant, configuration):
    footprint_name = 'Amphenol-ICC_SFW{pc}S-2{v}E1LF_1x{pc}_P1.0mm_Vertical'.format(pc=str(pincount), v=variant)
    print('Building ', footprint_name)

    # calculate working values
    pitch = 1
    pad_inner_distance = 2 # pads alternate around centerline
    pad_width = 0.6
    pad_height = 1.85
    pad_span = pitch * (pincount - 1)

    even = floor(pincount/2)
    odd = pincount - even

    pad1_y = -pad_span/2

    tab_width = pad_width
    tab_height = pad_inner_distance + 2 * pad_height
    tab_y = pad1_y - pitch
    tab_x = 0

    half_body_height = 3.6/2
    half_body_width = (pad_span + 10.4 - 3)/2

    body_edge = {
        'left': -half_body_width,
        'right': half_body_width,
        'top': -half_body_height,
        'bottom': half_body_height
    }

    if variant=='STM':
        conduct_y = (pad1_y - pitch - half_body_width)/2
    else:    
        conduct_y = (pad1_y - half_body_width)/2
    conduct_side = 1

    silk_clearance = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    marker_x = 1.8
    nudge = configuration['silk_fab_offset']

    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = roundToBase(pad_inner_distance/2+ pad_height + courtyard_clearance, courtyard_precision)
    courtyard_y = roundToBase(half_body_width + courtyard_clearance, courtyard_precision)
    
    label_x_offset = 0.7

    datasheet = "https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/sfw_s-2st_e1lf.pdf"

    # initialise footprint
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription('Amphenol-ICC 1.00mm Flex Connector, SFW series, {pc} position, top entry, 5.3mm height, SMT, {ds}'.format(pc=pincount, ds=datasheet))
    kicad_mod.setTags('amphenol icc fci flex fcc fpc zif')
    kicad_mod.setAttribute('smd')

    # create even pads
    kicad_mod.append(PadArray(pincount=even, y_spacing=2*pitch, start=[(pad_inner_distance + pad_height)/2, pad1_y + pitch],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_height, pad_width], layers=Pad.LAYERS_SMT,
        initial=2, increment=2))

    # create odd pads
    kicad_mod.append(PadArray(pincount=odd, y_spacing=2*pitch, start=[-(pad_inner_distance + pad_height)/2, pad1_y],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_height, pad_width], layers=Pad.LAYERS_SMT,
        initial=1, increment=2))

    # create tab (smt mounting) pads
    if variant=='STM':
        kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
            at=[tab_x, -tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
            size=[tab_height, tab_width], layers=Pad.LAYERS_SMT))

        kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
            at=[tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
            size=[tab_height, tab_width], layers=Pad.LAYERS_SMT))

    # create fab outline and pin 1 marker
    kicad_mod.append(RectLine(
        start=[-half_body_height, -half_body_width],
        end=[half_body_height, half_body_width],
        layer='F.Fab', width=configuration['fab_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            [-half_body_height-silk_clearance, pad1_y-pad_width/2.0-silk_clearance],
            [-pad_inner_distance/2 - pad_height, pad1_y-pad_width/2.0-silk_clearance]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create silkscreen outline, pin 1 marker and conductor side marker
    kicad_mod.append(RectLine(
        start=[-half_body_height-silk_clearance, -half_body_width-silk_clearance],
        end=[half_body_height+silk_clearance, half_body_width+silk_clearance],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            [-half_body_height-silk_clearance, pad1_y-pad_width/2.0-silk_clearance],
            [-pad_inner_distance/2 - pad_height, pad1_y-pad_width/2.0-silk_clearance]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            [-half_body_height + silk_clearance, conduct_y-conduct_side/2],
            [-half_body_height + silk_clearance, conduct_y+conduct_side/2],
            [-half_body_height + silk_clearance + conduct_side*.866, conduct_y],
            [-half_body_height + silk_clearance, conduct_y-conduct_side/2]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # create courtyard
    kicad_mod.append(RectLine(start=[-courtyard_x, -courtyard_y], end=[courtyard_x, courtyard_y],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
    # kicad_mod.append(Text(type='reference', text='REF**', size=[1,1], at=[0, courtyard_y1 - label_x_offset], layer='F.SilkS'))
    # kicad_mod.append(Text(type='user', text='%R', size=[1,1], at=[0, tab_x], layer='F.Fab'))
    # kicad_mod.append(Text(type='value', text=footprint_name, at=[0, courtyard_y2 + label_x_offset], layer='F.Fab'))


    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':-courtyard_y, 'bottom':courtyard_y}, fp_name=footprint_name, text_y_inside_position=[0, tab_x])

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

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

    # with pincount(s) and mounting plate variants (s) to be generated, build them all in a nested loop
    for variant in variants:
        for pincount in pincounts:
            generate_one_footprint(pincount, variant, configuration)
