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

Drawing:
https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/f32q-f32t.pdf

"""

import sys
import os

sys.path.append(os.path.join(sys.path[0], '..', '..', '..'))  # load parent path of KicadModTree
import argparse
import yaml
from helpers import *
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], '..', '..', 'tools'))  # load parent path of tools
from footprint_text_fields import addTextFields

manufacturer = 'Amphenol'
conn_category = 'FFC-FPC'

lib_by_conn_category = True

families = ({'name': 'F32Q', 'side': 'top'},
            {'name': 'F32R', 'side': 'bottom'})
pincounts = range(4, 61)

def generate_one_footprint(family, pincount, configuration):

    footprint_name = '{mfg:s}_{family:s}-1A7x1-110{pc:02g}_1x{pc:02g}-1MP_P0.5mm_Horizontal'\
        .format(mfg=manufacturer, family=family['name'], pc=pincount)

    print('Building {:s}'.format(footprint_name))

    datasheet = 'https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/f32q-f32t.pdf'

    # calculate working values
    pitch = 0.5
    pad_width = 0.3
    pad_height = 1.1
    pad_y = -(5.50 - 1.0)/2 -1.2 + pad_height/2  # So that middle of body in fab layer is at (0,0)
    pad_x_span = pitch * (pincount - 1)
    pad1_x = -pad_x_span / 2

    tab_width = 2.10
    tab_height = 1.95
    tab_x = pad_x_span/2 + 3.30 - tab_width/2
    tab_y = pad_y - pad_height/2 + (1.2 - 0.5) + tab_height/2

    body_y1 = pad_y - pad_height/2 + 1.2
    half_body_width = pad_x_span/2 + 2.65
    actuator_y1 = body_y1 + 5.5 - 1.0
    half_actuator_width = half_body_width + 1.25
    ear_height = 1.5  # Measured on STEP model

    body_edge = {
        'left': -half_body_width,
        'right': half_body_width,
        'top': body_y1,
        'bottom': actuator_y1
    }

    silk_clearance = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    courtyard_precision = configuration['courtyard_grid']
    courtyard_clearance = configuration['courtyard_offset']['connector']
    courtyard_x = roundToBase(half_actuator_width + courtyard_clearance, courtyard_precision)
    courtyard_y1 = roundToBase(pad_y - pad_height/2 - courtyard_clearance, courtyard_precision)
    courtyard_y2 = roundToBase(actuator_y1 + courtyard_clearance, courtyard_precision)
    
    # initialise footprint
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription('{mfg} FPC connector, {pc:g} {side}-side contacts, 0.5mm pitch, SMT, {ds}'.format(mfg=manufacturer, pc=pincount, side=family['side'], ds=datasheet))
    kicad_mod.setTags('{mfg} fpc {family:s}'.format(mfg=manufacturer, family=family['name']))
    kicad_mod.setAttribute('smd')

    # create pads
    kicad_mod.append(PadArray(pincount=pincount, x_spacing=pitch, center=[0,pad_y],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
        size=[pad_width, pad_height], layers=Pad.LAYERS_SMT))

    # create tab (smt mounting) pads
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
        at=[tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
        size=[1, 1], layers=Pad.LAYERS_SMT, primitives=[Polygon(nodes=[
            (-tab_width/2, -tab_height/2),
            (-tab_width/2, tab_height/2),
            (tab_width/2 - 0.8, tab_height/2),
            (tab_width/2 - 0.8, tab_height/2 - 0.35),
            (tab_width/2, tab_height/2 - 0.35),
            (tab_width/2, -tab_height/2),
            (-tab_width/2, -tab_height/2)
            ])]))
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'],
        at=[-tab_x, tab_y], type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
        size=[1, 1], layers=Pad.LAYERS_SMT, primitives=[Polygon(nodes=[
            (-tab_width/2, -tab_height/2),
            (-tab_width/2, tab_height/2),
            (tab_width/2 - 0.8, tab_height/2),
            (tab_width/2 - 0.8, tab_height/2 - 0.35),
            (tab_width/2, tab_height/2 - 0.35),
            (tab_width/2, -tab_height/2),
            (-tab_width/2, -tab_height/2)
            ], x_mirror=0)]))

    # create fab outline
    kicad_mod.append(PolygoneLine(
        polygone=[
            (-half_body_width, body_y1),
            (half_body_width, body_y1),
            (half_body_width, actuator_y1-ear_height),
            (half_actuator_width, actuator_y1-ear_height),
            (half_actuator_width, actuator_y1),
            (-half_actuator_width, actuator_y1),
            (-half_actuator_width, actuator_y1-ear_height),
            (-half_body_width, actuator_y1-ear_height),
            (-half_body_width, body_y1)],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create fab pin 1 marker
    kicad_mod.append(PolygoneLine(
        polygone=[
            [pad1_x-0.4, body_y1],
            [pad1_x, body_y1+0.8],
            [pad1_x+0.4, body_y1]],
        layer='F.Fab', width=configuration['fab_line_width']))

    # create silkscreen outline
    kicad_mod.append(PolygoneLine(
        polygone=[
            (pad1_x + pad_x_span + pad_width/2 + silk_clearance, tab_y - tab_height/2 - silk_clearance),
            (tab_x + tab_width/2 + silk_clearance, tab_y - tab_height/2 - silk_clearance),
            (tab_x + tab_width/2 + silk_clearance, actuator_y1 - ear_height - configuration['silk_line_width']/2),
            (half_actuator_width + configuration['silk_line_width']/2, actuator_y1 - ear_height - configuration['silk_line_width']/2),
            (half_actuator_width + configuration['silk_line_width']/2, actuator_y1 + configuration['silk_line_width']/2),
            (-half_actuator_width - configuration['silk_line_width']/2, actuator_y1 + configuration['silk_line_width']/2),
            (-half_actuator_width - configuration['silk_line_width']/2, actuator_y1 - ear_height - configuration['silk_line_width']/2),
            (-tab_x - tab_width/2 - silk_clearance, actuator_y1 - ear_height - configuration['silk_line_width']/2),
            (-tab_x - tab_width/2 - silk_clearance, tab_y - tab_height/2 - silk_clearance),
            (pad1_x - pad_width/2 - silk_clearance, tab_y - tab_height/2 - silk_clearance),
            (pad1_x - pad_width/2 - silk_clearance, pad_y - pad_height/2 + configuration['silk_line_width']/2)],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # create courtyard
    kicad_mod.append(RectLine(start=[-courtyard_x, courtyard_y1], end=[courtyard_x, courtyard_y2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

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

    # with pincount(s) and family(es) to be generated, build them all in a nested loop
    for family in families:
        for pincount in pincounts:
            generate_one_footprint(family, pincount, configuration)
