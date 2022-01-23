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

import sys
import os

sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","..")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path

from math import sqrt
import argparse
import yaml
from KicadModTree import *

from footprint_text_fields import addTextFields

series = "BL653"
series_long = 'BL653 Bluetooth modules 453-00039 (internal antenna) 453-00041 (external antenna)'
manufacturer = 'Blair'
orientation = 'V'
datasheet = 'https://www.lairdconnect.com/documentation/datasheet-bl653-series'

# a constant offset to shift the final footprint

# define the basic Pad, all square 0.5 x 0.5
pad_settings = { 'type': Pad.TYPE_SMT,
                'shape': Pad.SHAPE_RECT,
                 'size': [0.5, 0.5],
               'layers': Pad.LAYERS_SMT}

body_width  = 15.00
body_height = 10.00

offset = Point (body_width/2, body_height/2)
#offset = Point (body_height/2, body_width/2)
#offset = Point (0, 0)

P8 = 0.8  # basic pitch
P4 = 0.45 #
P9 = 0.95

blocks = [

        # 6 linear blocks
        { 'start':  1,  'end' : 21, 'pos_x': 15.00-9.25     , 'pos_y': P4                 , 'dx':P8, 'dy': 0 },
        { 'start':  2,  'end' : 22, 'pos_x': 15.00-9.25     , 'pos_y': P4+P8              , 'dx':P8, 'dy': 0 },

        { 'start': 25,  'end' : 41, 'pos_x': 15.00-P4       , 'pos_y': P4+P8+P9           , 'dx': 0, 'dy':P8 },
        { 'start': 26,  'end' : 40, 'pos_x': 15.00-P4-P8    , 'pos_y': P4+P8+P9           , 'dx': 0, 'dy':P8 },

        { 'start': 43,  'end' : 65, 'pos_x': 15.00-P4-P8    , 'pos_y': P4+P8+P9+7*P8+P9+P8, 'dx':-P8, 'dy':0 },  # can be 10.00-P4 !
        { 'start': 44,  'end' : 64, 'pos_x': 15.00-P4-P8    , 'pos_y': P4+P8+P9+7*P8+P9   , 'dx':-P8, 'dy':0 },  # can be 10.00-P4-P8 !

        # now 13 single annoying pads
        { 'start':  0,  'end' :  0, 'pos_x': 15.00-9.25-P8      , 'pos_y': P4   ,  'dx':0, 'dy':0 },
        { 'start': 66,  'end' : 66, 'pos_x': 15.00-9.25-P8-1.30 , 'pos_y': P4   ,  'dx':0, 'dy':0 },

        { 'start': 67,  'end' : 67, 'pos_x': 1.05 + 1.30        , 'pos_y': P4   ,  'dx':0, 'dy':0 },
        { 'start': 68,  'end' : 68, 'pos_x': 1.05               , 'pos_y': P4   ,  'dx':0, 'dy':0 },

        { 'start': 72,  'end' : 72, 'pos_x': 15.00-9.25-P8-0.65 , 'pos_y': P4+P8,  'dx':0, 'dy':0 },

        # Assuming those 3 are symetrical&centered
        { 'start': 71,  'end' : 71, 'pos_x': 15.00-9.25, 'pos_y': P4+P8+1.875*1,  'dx':0, 'dy':0 },
        { 'start': 69,  'end' : 69, 'pos_x': 15.00-9.25, 'pos_y': P4+P8+1.875*2,  'dx':0, 'dy':0 },
        { 'start': 68,  'end' : 68, 'pos_x': 15.00-9.25, 'pos_y': P4+P8+1.875*3,  'dx':0, 'dy':0 },

        # Those three are same block as 25-41 but numerotation is not in sequence
        { 'start': 23,  'end' : 23, 'pos_x': 15.00-P4, 'pos_y':P4+P8+P9-2*P8 ,  'dx':0, 'dy':P8 },
        { 'start': 24,  'end' : 24, 'pos_x': 15.00-P4, 'pos_y':P4+P8+P9-1*P8 ,  'dx':0, 'dy':P8 },
        { 'start': 42,  'end' : 42, 'pos_x': 15.00-P4, 'pos_y':P4+P8+P9+9*P8 ,  'dx':0, 'dy':P8 },
]



# Some format strings from old custom config KLC
footprint_name = "{man}_{fp}".format(man=manufacturer, fp=series)
keyword_fp_string = 'Module {man:s} {series:s} {entry:s}'
lib_name_format_string = 'Module'

kicad_mod      = Footprint(footprint_name)

def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base



def add_pad (pad_num, pad_pos):

    kicad_mod.append( Pad(number=pad_num, at=pad_pos-offset, **pad_settings) )


#cpos / pitch are type Point(0,0)
def gen_column (pos, start, stop, pitch):

    for num in range (start, stop+1, 2):   # all aligment are either pair or impair
       add_pad (num, pos)
       pos = pos + pitch

def generate_one_footprint(configuration):


    descr_format_str = "{sl:s}, (Datasheet:{ds:s}), KiCad-scripting"

    kicad_mod.setDescription(descr_format_str.format(sl=series_long,  ds=datasheet))

    kicad_mod.setTags(keyword_fp_string.format(series=series,
        orientation="", man=manufacturer,
        entry=""))

    kicad_mod.setAttribute('smd')

    nudge = configuration['silk_fab_offset']
    silk_w = configuration['silk_line_width']
    fab_w = configuration['fab_line_width']

    for b in blocks:
       gen_column ( Point (b['pos_x'], b['pos_y']) , b['start'], b['end'], Point (b['dx'], b['dy']) )

    body_edge={
        'left'  :0           - offset.x,
        'right' :body_width  - offset.x,
        'bottom':0           - offset.y,
        'top'   :body_height - offset.y
        }

    # create fab outline
    kicad_mod.append(RectLine(start=[body_edge['left'], body_edge['top']],\
        end=[body_edge['right'], body_edge['bottom']], layer='F.Fab', width=fab_w))

    # create silkscreen
    kicad_mod.append(RectLine(start=[body_edge['left']-nudge, body_edge['top']+nudge],\
        end=[body_edge['right']+nudge, body_edge['bottom']-nudge], layer='F.SilkS', width=silk_w))

    # Triangle pin1
    tSize = 0.5
    points = [
            (  body_edge['left']+1.05+3*1.30        ,body_edge['bottom'] -nudge*2        ),
            (  body_edge['left']+1.05+3*1.30 -tSize ,body_edge['bottom'] -nudge*2 -tSize     ),
            (  body_edge['left']+1.05+3*1.30 +tSize ,body_edge['bottom'] -nudge*2 -tSize    ),
            (  body_edge['left']+1.05+3*1.30        ,body_edge['bottom'] -nudge*2          )
                ]

    kicad_mod.append(PolygoneLine(polygone=points, layer='F.SilkS', width=silk_w))

    ########################### CrtYd #################################
    cx1 = roundToBase(body_edge['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = roundToBase(body_edge['top']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = roundToBase(body_edge['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = roundToBase(body_edge['bottom']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    configuration['references'][1]['size_min'] = [0.5,0.5]
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy2, 'bottom':cy1}, fp_name=footprint_name, text_y_inside_position='center')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KICAD6_3DMODEL_DIR}/')

    lib_name = lib_name_format_string.format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../tools/global_config_files/config_KLCv3.0.yaml')
    #parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='conn_config_KLCv3.yaml')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    #with open(args.series_config, 'r') as config_stream:
    #    try:
    #        configuration.update(yaml.safe_load(config_stream))
    #    except yaml.YAMLError as exc:
    #        print(exc)


    generate_one_footprint(configuration)
