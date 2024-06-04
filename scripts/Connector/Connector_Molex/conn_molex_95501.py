#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
import sys
import os
from collections import defaultdict
from math import sqrt, ceil, floor

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


def build_base_footprint(args, config):
    # expand the orientation based on the KLC config
    args['entry'] = config['entry_direction'][args['orientation']]
    args['orientation'] = config['orientation_options'][args['orientation']]

    name = config['fp_name_format_string']
    args['footprint_name'] = name.format(**defaultdict(str, args)).replace("__", '_')

    kicad_mod = Footprint(args['footprint_name'])
    kicad_mod.setDescription(config['descr_format_string'].format(**args))
    kicad_mod.setTags(config['keyword_fp_string'].format(**args))

    return kicad_mod

def add_keepout(kicad_mod, center, x, y):
    return addRectangularKeepout(kicad_mod, center, (x,y))


def generate_one_footprint(config, **kwargs):
    args = dict(        man = 'Molex',
                        mpn = '{}P{}C'.format(kwargs['positions'], kwargs['connected']),
                     series = '95501',
                orientation = 'V',
                   lib_name = 'Connector_RJ',
                  datasheet = 'http://www.molex.com/pdm_docs/sd/955012441_sd.pdf'
                )
    args.update(kwargs)


    config['keyword_fp_string']     = 'connector {man} {series} {mpn} Cat.3 right angle side entry'
    config['fp_name_format_string'] = '{man}_{series}_{variant}_{mpn}'
    config['descr_format_string']   = '{series} Cat.3 modular connector, right angle, {datasheet}'


    kicad_mod = build_base_footprint(args, config)
    if args['variant'] == 'SMT':
        kicad_mod.setAttribute('smd')
    else:
        kicad_mod.setAttribute('through_hole')

    ref = Point (0, 0)  # move the ref to any point

    if args['variant'] == 'THT':
        pitch_x = 1.27
        pitch_y = 2.54

        ref = Point (config['B'] / 2, 8.89)

        # for the 6pins, pin 1 is on the top
        if (args['connected'] != 6):
            ref = ref - (0, pitch_y)

        pad_settings = dict(layers=Pad.LAYERS_THT,
                            drill=0.90,
                            size=(2, 2))
        pad_type = Pad.TYPE_THT
        pad_shape = Pad.SHAPE_RECT
        for i in range(1, args['connected']+1):
            y = 0
            if i % 2 == 0:
                if args['connected'] / 2 % 2 == 0:
                    y = -pitch_y
                else:
                    y = pitch_y
            position = Point ((i-1) * pitch_x, y)
            kicad_mod.append(Pad(number=i, at=position, shape=pad_shape,
                type=pad_type, **pad_settings))

            pad_shape = Pad.SHAPE_CIRCLE

    else: # SMT

        pitch_x = 1.27
        pitch_y = 0

        pad_settings = dict( layers = Pad.LAYERS_SMT, size = (0.76, 6.35) )
        pad_type = Pad.TYPE_SMT
        pad_shape = Pad.SHAPE_RECT
        pad_pos = Point (-config['B'] / 2, -13.4 + (pad_settings['size'][1]/2) )


        for i in range(0, args['connected']):
            position = ref + pad_pos + ((i) * pitch_x, 0)
            kicad_mod.append(Pad(number=i+1, at=position, shape=pad_shape,
                             type=pad_type, **pad_settings))

    # center now content the offset to add to Pin 1
    # this thing will allways violate F6.2

    # the two centering holes
    mounting_hole_position = ref - (config['C']/2, 0)
    kicad_mod.append(Pad(at=mounting_hole_position, shape=Pad.SHAPE_CIRCLE,
        type=Pad.TYPE_NPTH, drill=3.25, size=3.25, layers=Pad.LAYERS_NPTH))

    kicad_mod.append(Pad(at=mounting_hole_position + (config['C'], 0),
        shape=Pad.SHAPE_CIRCLE,
        type=Pad.TYPE_NPTH, drill=3.25, size=3.25, layers=Pad.LAYERS_NPTH))


    # introduce the shift between the body and centering holes
    ref = ref - Point (0,  18.10/2 - 7.80)

    housing_size = Point(config['A'], 18.10)
    kicad_mod.append(RectLine(start = ref - housing_size/2,
                                end = ref + housing_size/2, layer='F.Fab',
                              width = config['fab_line_width']))


    # SilkScreen
    nudge = configuration['silk_fab_offset']
    if args['variant'] == 'THT':
        kicad_mod.append(RectLine(start = ref - housing_size/2 - nudge,
                                    end = ref + housing_size/2 + nudge, layer='F.SilkS',
                                  width = config['silk_line_width']))
        # Triangle pin1
        tSize = 0.5
        points = [
                   ((ref - housing_size/2 - nudge).x       , 0        ),
                   ((ref - housing_size/2 - nudge).x -tSize, 0 - tSize),
                   ((ref - housing_size/2 - nudge).x -tSize, 0 + tSize),
                   ((ref - housing_size/2 - nudge).x       , 0        )
                ]
        kicad_mod.append(PolygoneLine(polygone=points, layer='F.SilkS', width=config['silk_line_width']))
    else:
        # SMD, Silk can not print on Pad (Pad Size = 6.35*0.76)
        silk_pad_stop_xLeft = ref.x + pad_pos.x - pad_settings['size'][0]/2 - config['silk_pad_clearance']
        silk_pad_stop_xRigh = silk_pad_stop_xLeft + args['connected'] * pitch_x
        points = [
                (+silk_pad_stop_xLeft - nudge, (ref -housing_size / 2).y - (pad_settings['size'][1]/2)),
                (+silk_pad_stop_xLeft - nudge, (ref -housing_size / 2).y - nudge),
                ref - housing_size / 2 - (+nudge, +nudge) ,
                ref - housing_size / 2 + (-nudge , housing_size.y + nudge),
                ref + housing_size / 2 + (+nudge,  +nudge),
                ref + housing_size / 2 - (-nudge, housing_size.y + nudge),
                (silk_pad_stop_xRigh   + nudge, (ref -housing_size / 2).y - nudge),
                ]
        kicad_mod.append(PolygoneLine(polygone=points, layer='F.SilkS', width=config['silk_line_width']))

    body_edges = dict( top = (ref - housing_size/2).y,
                      left = (ref - housing_size/2).x,
                    bottom = (ref + housing_size/2).y,
                     right = (ref + housing_size/2).x  )


    # Forn SMT, the top courtyard is above the Pad
    if args['variant'] == 'SMT':
        body_edges['top'] -=  pad_settings['size'][1] / 2

    cx1 = roundToBase( body_edges['left']   -config['courtyard_offset']['connector'], config['courtyard_grid'] )
    cy1 = roundToBase( body_edges['top']    -config['courtyard_offset']['connector'], config['courtyard_grid'] )

    cx2 = roundToBase( body_edges['right']  +config['courtyard_offset']['connector'], config['courtyard_grid'] )
    cy2 = roundToBase( body_edges['bottom'] +config['courtyard_offset']['connector'], config['courtyard_grid'] )

    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod, config, body_edges=body_edges,
            courtyard={'top':cy1, 'bottom':cy2}, fp_name=args['footprint_name'])

    ##################### Output and 3d model ############################
    args['model3d_path_prefix'] = configuration.get('3d_model_prefix','${KICAD6_3DMODEL_DIR}/')

    lib_name = configuration['lib_name_format_string'].format(**args)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{footprint_name:s}.wrl'.format(**args)
    kicad_mod.append(Model(filename=model_name))

    config['outdir'] = '{lib_name:s}.pretty/'.format(**args)
    if not os.path.isdir(config['outdir']):
        os.makedirs(config['outdir'])
    filename = '{outdir:s}{footprint_name:s}.kicad_mod'.format(**config, **args)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    parser.add_argument('--kicad4_compatible', action='store_true', help='Create footprints kicad 4 compatible')
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

    configuration['kicad4_compatible'] = args.kicad4_compatible

    variants={
            (4,4): dict(A=11.18, B=3.81, C=7.62,  X=3.81, Y=7.62),
            (6,4): dict(A=13.41, B=3.81, C=10.16, X=3.81, Y=10.16),
            (6,6): dict(A=13.41, B=6.35, C=10.16, X=6.35, Y=10.16),
            (8,8): dict(A=15.24, B=8.89, C=11.43, X=8.89, Y=11.43),
        }

    for (p, c), conf in variants.items():
        configuration.update(conf)
        generate_one_footprint(positions=p, connected=c, variant='THT', config=configuration)
        generate_one_footprint(positions=p, connected=c, variant='SMT', config=configuration)
