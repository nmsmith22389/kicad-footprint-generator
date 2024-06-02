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
# (C) 2019 by Carsten Presser, <c@rstenpresser.de>

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

manufacturer = "Amphenol-FCI"
conn_category = "FFC-FPC"

lib_by_conn_category = True

variants = ["1ST", "2ST"]
pincounts = range(4, 35)

def generate_one_footprint(pincount, variant, configuration):
    footprint_name = 'Amphenol-FCI_SFV{pns}R-{var}_1x{pc:02g}-1MP_P0.5mm_Horizontal'\
        .format(pns=str(pincount), pc=pincount, var=variant)
    print('Building {:s}'.format(footprint_name))

    # calculate working values
    pitch = 0.5
    pad_y = -2
    pad_width = 0.3
    pad_height = 1.4
    pad_x_span = pitch * (pincount - 1) # C
    pad1_x = pad_x_span / 2.0

    tab_width = 2.65
    tab_height = 2.3
    tab_x = pad1_x + 3.1 - tab_width / 2.0
    tab_y = pad_y + pad_height / 2.0 + tab_height / 2.0 - 0.6

    body_y1 = tab_y - tab_height / 2.0 + 0.2
    half_body_width = pad_x_span / 2.0 + 2.20 # B
    actuator_y1 = body_y1 + 4.2
    actuator_y2 = actuator_y1 + 1.5
    half_actuator_width = pad_x_span / 2.0 + 3 # A
    ear_height = 1.4

    body_edge = {
        'left': -half_body_width,
        'right': half_body_width,
        'top': body_y1,
        'bottom': actuator_y1
    }

    silk_clearance = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    marker_y = 1.8
    nudge = configuration['silk_fab_offset']

    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = roundToBase(tab_x + tab_width / 2.0 + courtyard_clearance, courtyard_precision)
    courtyard_y1 = roundToBase(pad_y - pad_height / 2.0 - courtyard_clearance, courtyard_precision)
    courtyard_y2 = roundToBase(actuator_y2 + courtyard_clearance, courtyard_precision)

    label_y_offset = 0.7

    # select correct datasheet URL depending on part number
    if variant == "1ST":
        side = "bottom"
    elif variant == "2ST":
        side = "top"
    datasheet = "https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/sfv12b_hlf.pdf"

    # initialise footprint
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription('Amphenol-FCI FPC connector, {pc:02g} {side}-side contacts, 0.5mm pitch, 1.8mm height, SMT, {ds}'.format(pc=pincount, side=side, ds=datasheet))
    kicad_mod.setTags('fci amphenol fpc {:s}'.format(variant))
    kicad_mod.setAttribute('smd')


    # create pads
    kicad_mod.append(PadArray(pincount=pincount, x_spacing=pitch, center=[0,pad_y],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[pad_width, pad_height], layers=Pad.LAYERS_SMT))

    # create tab (smt mounting) pads
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
        at=[-tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[tab_width, tab_height], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
        at=[tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[tab_width, tab_height], layers=Pad.LAYERS_SMT))

    # create fab outline and pin 1 marker
    kicad_mod.append(PolygoneLine(
        polygone=[
            [-half_body_width, body_y1],
            [half_body_width, body_y1],
            [half_body_width, actuator_y1-ear_height],
            [half_actuator_width, actuator_y1-ear_height],
            [half_actuator_width, actuator_y1],
            [-half_actuator_width, actuator_y1],
            [-half_actuator_width, actuator_y1-ear_height],
            [-half_body_width, actuator_y1-ear_height],
            [-half_body_width, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            [-pad1_x-0.25, body_y1],
            [-pad1_x, body_y1+0.5],
            [-pad1_x+0.25, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create open actuator outline
    kicad_mod.append(PolygoneLine(
        polygone=[
            [half_body_width, actuator_y1],
            [half_body_width, actuator_y2-ear_height],
            [half_actuator_width, actuator_y2-ear_height],
            [half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2],
            [-half_actuator_width, actuator_y2-ear_height],
            [-half_body_width, actuator_y2-ear_height],
            [-half_body_width, actuator_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create silkscreen outline and pin 1 marker
    kicad_mod.append(PolygoneLine(
        polygone=[
            [half_body_width+nudge, tab_y+tab_height/2.0+silk_clearance],
            [half_body_width+nudge, actuator_y1-ear_height-nudge],
            [half_actuator_width+nudge, actuator_y1-ear_height-nudge],
            [half_actuator_width+nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1+nudge],
            [-half_actuator_width-nudge, actuator_y1-ear_height-nudge],
            [-half_body_width-nudge, actuator_y1-ear_height-nudge],
            [-half_body_width-nudge, tab_y+tab_height/2.0+silk_clearance]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            [-pad1_x-pad_width/2.0-silk_clearance, tab_y-tab_height/2.0-silk_clearance],
            [-pad1_x-pad_width/2.0-silk_clearance, pad_y-pad_height/2.0]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # create courtyard
    kicad_mod.append(RectLine(start=[-courtyard_x, courtyard_y1], end=[courtyard_x, courtyard_y2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
    # kicad_mod.append(Text(type='reference', text='REF**', size=[1,1], at=[0, courtyard_y1 - label_y_offset], layer='F.SilkS'))
    # kicad_mod.append(Text(type='user', text='%R', size=[1,1], at=[0, tab_y], layer='F.Fab'))
    # kicad_mod.append(Text(type='value', text=footprint_name, at=[0, courtyard_y2 + label_y_offset], layer='F.Fab'))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':courtyard_y1, 'bottom':courtyard_y2}, fp_name=footprint_name, text_y_inside_position=[0, tab_y])

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

    # with pincount(s) and variant(s) to be generated, build them all in a nested loop
    for variant in variants:
        for pincount in pincounts:
            generate_one_footprint(pincount, variant, configuration)
