#!/usr/bin/env python3
'''
kicad-footprint-generator is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
kicad-footprint-generator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
'''
import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path
# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import sqrt
import argparse
import yaml
from KicadModTree import *
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields
from drawing_tools import *

series = 'Gecko'
series_long = 'Male Vertical Surface Mount Double Row 1.25mm (0.049 inch) Pitch PCB Connector'
manufacturer = 'Harwin'
datasheet = 'https://cdn.harwin.com/pdfs/G125-MS1XX05M2P.pdf'
pn = 'G125-MS1{n:02}05M2P'
number_of_rows = 2
orientation = 'V'

pitch = 1.25
mount_drill = 2.25
mount_pad = 4.4
pad_size = [0.7,2.5]

pincount_range = [6, 10, 12, 16, 20, 26, 34, 50]

def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

def generate_footprint(pins, configuration):

    mpn = pn.format(n=pins)
    pins_per_row = int(pins / 2)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    print(footprint_name)
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("Harwin {:s}, {:s}, {:d} Pins per row ({:s}), generated with kicad-footprint-generator".format(series_long, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    ########################## Dimensions ##############################

    x_body = pitch * (pins_per_row - 1) + 12.7
    x_pins = pitch * (pins_per_row - 1)
    y_body = 4.9
    y_max_pin_extent = 5.8
    mount_spacing = pitch * (pins_per_row - 1) + 7.8

    body_edge={
        'top': -y_body / 2,
        'bottom': y_body / 2,
        'left': -x_body / 2,
        'right': x_body / 2
    }

    ############################# Pads ##################################
    #
    # Mounting holes
    #
    kicad_mod.append(Pad(at=[-mount_spacing/2, 0], number="MP",
        type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=mount_pad,
        drill=mount_drill, layers=Pad.LAYERS_THT))
    kicad_mod.append(Pad(at=[mount_spacing/2, 0], number="MP",
        type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=mount_pad,
        drill=mount_drill, layers=Pad.LAYERS_THT))

    #
    # Add pads
    #
    kicad_mod.append(PadArray(start=[-x_pins/2, 1.85], initial=1,
        pincount=pins_per_row, increment=1,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))
    kicad_mod.append(PadArray(start=[-x_pins/2, -1.85], initial=pins_per_row+1,
        pincount=pins_per_row, increment=1,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))

    ######################## Fabrication Layer ###########################
    addArcByAngles(kicad_mod, -mount_spacing/2, 0, y_body/2, -180, 0,"F.Fab",configuration['fab_line_width'])
    addArcByAngles(kicad_mod, mount_spacing/2, 0, y_body/2, 180, 0,"F.Fab",configuration['fab_line_width'])

    for y in [-1, 1]:
        kicad_mod.append(PolygonLine(polygon=[
            {'y': y * (y_body / 2), 'x': mount_spacing/2},
            {'y': y * (y_body / 2), 'x': -mount_spacing/2},
        ],width=configuration['fab_line_width'], layer="F.Fab"))

    main_arrow_poly= [
        {'y': 2.54, 'x': -(x_pins/2) - .4},
        {'y': 1.9, 'x': -(x_pins/2)},
        {'y': 2.54, 'x': -(x_pins/2) + .4},
    ]
    kicad_mod.append(PolygonLine(polygon=main_arrow_poly,
        width=configuration['fab_line_width'], layer="F.Fab"))

    ######################## SilkS Layer ###########################
    addArcByAngles(kicad_mod, -mount_spacing/2, 0, y_body/2 + configuration['silk_fab_offset'], -180, 0,"F.SilkS",configuration['silk_line_width'])
    addArcByAngles(kicad_mod, mount_spacing/2, 0, y_body/2 + configuration['silk_fab_offset'], 180, 0,"F.SilkS",configuration['silk_line_width'])

    for y in [-1, 1]:
        for x in [-1, 1]:
            kicad_mod.append(PolygonLine(polygon=[
                {'y': y * (y_body / 2) + configuration['silk_fab_offset'] * y, 'x': x * mount_spacing/2},
                {'y': y * (y_body / 2) + configuration['silk_fab_offset'] * y, 'x': x * (x_pins/2) + x},
            ],width=configuration['silk_line_width'], layer="F.SilkS"))

    kicad_mod.append(PolygonLine(polygon=[
        {'y': (y_body / 2) + configuration['silk_fab_offset'], 'x': -(x_pins/2) - 1},
        {'y': (y_body / 2) + configuration['silk_fab_offset'] + .5, 'x': -(x_pins/2) - 1},
    ],width=configuration['silk_line_width'], layer="F.SilkS"))

    ######################## CrtYd Layer ###########################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    poly_yd = [
        {'y': roundToBase(-(y_max_pin_extent/2) - CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase((y_max_pin_extent/2) + CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase((y_max_pin_extent/2) + CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase(-(y_max_pin_extent/2) - CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase(-(y_max_pin_extent/2) - CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)}
    ]

    kicad_mod.append(PolygonLine(polygon=poly_yd,
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    cy1 = body_edge['top'] - configuration['courtyard_offset']['connector'] - 0.4
    cy2 = body_edge['bottom'] + configuration['courtyard_offset']['connector'] + 0.4

    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')

    ##################### Write to File ############################

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)


    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

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

    for pincount in pincount_range:
        generate_footprint(pincount, configuration)
