#!/usr/bin/env python3

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
from footprint_keepout_area import addRectangularKeepout

series = 'FH48'
category = 'FFC-FPC'
manufacturer = 'Hirose'
orientation = 'V'
number_of_rows = 1
datasheet = 'https://www.hirose.com/product/document?clcode=&productname=&series=FH48&documenttype=Catalog&lang=en&documentid=D49363_en'

pins_per_row_range = [20,21,31,40,50,68]
sh_pins_per_row = [4,4,6,8,10,13]

part_code = 'FH48-{n:02d}S-0.5SV'

body_size_y = 4.1
rel_body_edge_x = 2.75

pitch = 0.5
sh_pitch = 2.5
pad_size = [0.3, 1.63]
paste_size = [0.28, 1.21]
sh_pad_size = [0.3,1.2]
sh_paste_size = [0.28,0.9]
mp_size = [1.6, 2.2]
pad_outer_span = 5.2

# some measured dimensions not given in the datasheet
corner_notch_width = 1 # width of notch on each side of body
corner_notch_height = 1.5 # height of corner notch from bottom edge of body (includes the sh_pin_notch_height below)
sh_pin_notch_width = 1 # width of plastic around each shield pin
sh_pin_notch_height = 0.5 # depth of notch around each shield pin in towards the body

def generate_one_footprint(idx, pins, configuration):
    mpn = part_code.format(n=pins)
    pad_silk_off = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    off = configuration['silk_fab_offset']
    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_no_series_format_string'].format(man=manufacturer,
        series=series, mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = '-1SH',
        pitch=pitch, orientation=orientation_str)

    footprint_name = footprint_name.replace('__','_')

    print(footprint_name)
    
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setAttribute('smd')
    kicad_mod.setDescription('{:s} {:s} {:s} connector, {:s}, {:d} Pins per row ({:s}), generated with kicad-footprint-generator'.format(manufacturer,
        series, category, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    A = (pins - 1) * pitch
    B = A + 2*rel_body_edge_x
    pad_y = -pad_outer_span/2 + pad_size[1]/2
    sh_pad_y = pad_y + pad_outer_span - pad_size[1]/2 - sh_pad_size[1]/2

    ########################### Pads #################################
    # create pads (stencil size is unique so use a loop)
    pad1_x = (pins - 1) * pitch / -2
    for pin in range(1, pins + 1):
        kicad_mod.append(Pad(number=pin, at=[pad1_x + (pin - 1) * pitch,pad_y],
            type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=pad_size, layers=['F.Cu', 'F.Mask']))
        kicad_mod.append(Pad(at=[pad1_x + (pin - 1) * pitch,pad_y],
            type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=paste_size, layers=['F.Paste']))
    
    # create shield pads
    sh_pad_left = (sh_pins_per_row[idx] - 1) * sh_pitch / -2
    for pin in range(sh_pins_per_row[idx]):
        kicad_mod.append(Pad(number='SH', at=[sh_pad_left + pin * sh_pitch,sh_pad_y],
            type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=sh_pad_size, layers=['F.Cu', 'F.Mask']))
        kicad_mod.append(Pad(at=[sh_pad_left + pin * sh_pitch,sh_pad_y],
            type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=sh_paste_size, layers=['F.Paste']))

    ########################### Outline #################################
    x1 = -B/2
    x2 = x1 + B
    y2 = body_size_y / 2
    y1 = y2 - body_size_y

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }

    # left fab line
    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': body_edge['left'],'y': body_edge['top']},
            {'x': body_edge['left'],'y': body_edge['bottom'] - corner_notch_height},
            {'x': body_edge['left'] + corner_notch_width,'y': body_edge['bottom'] - corner_notch_height},
            {'x': body_edge['left'] + corner_notch_width,'y': body_edge['bottom'] - sh_pin_notch_height},
            {'x': sh_pad_left - sh_pin_notch_width/2,'y': body_edge['bottom'] - sh_pin_notch_height}
        ],
        layer='F.Fab', width=configuration['fab_line_width']))

    # right fab line
    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': -sh_pad_left + sh_pin_notch_width/2,'y': body_edge['bottom'] - sh_pin_notch_height},
            {'x': body_edge['right'] - corner_notch_width,'y': body_edge['bottom'] - sh_pin_notch_height},
            {'x': body_edge['right'] - corner_notch_width,'y': body_edge['bottom'] - corner_notch_height},
            {'x': body_edge['right'],'y': body_edge['bottom'] - corner_notch_height},
            {'x': body_edge['right'],'y': body_edge['top']},
            {'x': body_edge['left'],'y': body_edge['top']}
        ],
        layer='F.Fab', width=configuration['fab_line_width']))

    # horizontal fab lines around and between shield pads
    for pin in range(sh_pins_per_row[idx]):
        kicad_mod.append(PolygoneLine(
            polygone=[
                {'x': sh_pad_left + pin * sh_pitch - sh_pin_notch_width/2, 'y': y2 - sh_pin_notch_height},
                {'x': sh_pad_left + pin * sh_pitch - sh_pin_notch_width/2, 'y': y2},
                {'x': sh_pad_left + pin * sh_pitch + sh_pin_notch_width/2, 'y': y2},
                {'x': sh_pad_left + pin * sh_pitch + sh_pin_notch_width/2, 'y': y2 - sh_pin_notch_height}
            ],
            layer='F.Fab', width=configuration['fab_line_width']))
        if pin <= sh_pins_per_row[idx] - 2:
            kicad_mod.append(Line(
                start=[sh_pad_left + pin * sh_pitch + sh_pin_notch_width/2, y2 - sh_pin_notch_height],
                end=[sh_pad_left + (pin + 1) * sh_pitch - sh_pin_notch_width/2, y2 - sh_pin_notch_height],
                layer='F.Fab', width=configuration['fab_line_width']))

    # pin 1 fab mark
    sl=1
    pin = [
        {'y': body_edge['top'], 'x': -A/2-sl/2},
        {'y': body_edge['top'] + sl/sqrt(2), 'x': -A/2},
        {'y': body_edge['top'], 'x': -A/2+sl/2}
    ]
    kicad_mod.append(PolygoneLine(polygone=pin,
        width=configuration['fab_line_width'], layer='F.Fab'))

########################### Silk #################################
    off = configuration['silk_fab_offset']
    x1 -= off
    y1 -= off
    x2 += off
    y2 += off

    silk_pad_x = -A/2 - pad_size[0]/2 - pad_silk_off
    silk_sh_pad_x = sh_pad_left - sh_pad_size[0]/2 - pad_silk_off
    
    # left side silk
    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': silk_pad_x, 'y': pad_y - pad_size[1]/2},
            {'x': silk_pad_x, 'y': y1},
            {'x': x1, 'y': y1},
            {'x': x1, 'y': y2 - corner_notch_height},
            {'x': x1 + corner_notch_width, 'y': y2 - corner_notch_height},
            {'x': x1 + corner_notch_width, 'y': y2 - sh_pin_notch_height},
            {'x': sh_pad_left - sh_pin_notch_width/2 - off, 'y': y2 - sh_pin_notch_height},
            {'x': sh_pad_left - sh_pin_notch_width/2 - off, 'y': y2},
            {'x': sh_pad_left - sh_pad_size[0]/2 - pad_silk_off, 'y': y2}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))
    
    # right side silk
    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': -silk_pad_x, 'y': y1},
            {'x': x2, 'y': y1},
            {'x': x2, 'y': y2 - corner_notch_height},
            {'x': x2 - corner_notch_width, 'y': y2 - corner_notch_height},
            {'x': x2 - corner_notch_width, 'y': y2 - sh_pin_notch_height},
            {'x': -sh_pad_left + sh_pin_notch_width/2 + off, 'y': y2 - sh_pin_notch_height},
            {'x': -sh_pad_left + sh_pin_notch_width/2 + off, 'y': y2},
            {'x': -sh_pad_left + sh_pad_size[0]/2 + pad_silk_off, 'y': y2}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    # horizontal silk lines between shield pads
    for pin in range(sh_pins_per_row[idx] - 1):
        kicad_mod.append(PolygoneLine(
            polygone=[
                {'x': sh_pad_left + pin * sh_pitch + sh_pad_size[0]/2 + pad_silk_off, 'y': y2},
                {'x': sh_pad_left + pin * sh_pitch + sh_pin_notch_width/2 + off, 'y': y2},
                {'x': sh_pad_left + pin * sh_pitch + sh_pin_notch_width/2 + off, 'y': y2 - sh_pin_notch_height},
                {'x': sh_pad_left + (pin + 1) * sh_pitch - sh_pin_notch_width/2 - off, 'y': y2 - sh_pin_notch_height},
                {'x': sh_pad_left + (pin + 1) * sh_pitch - sh_pin_notch_width/2 - off, 'y': y2},
                {'x': sh_pad_left + (pin + 1) * sh_pitch - sh_pad_size[0]/2 - pad_silk_off, 'y': y2}
            ],
            layer='F.SilkS', width=configuration['silk_line_width']))

    ########################### CrtYd #################################
    bounding_box = body_edge.copy()
    bounding_box['top'] = pad_y - pad_size[1]/2
    bounding_box['bottom'] = sh_pad_y + sh_pad_size[1]/2

    cx1 = roundToBase(bounding_box['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = roundToBase(bounding_box['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = roundToBase(bounding_box['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = roundToBase(bounding_box['bottom'] + configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')

    ##################### Output and 3D model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

    lib_name = configuration['lib_name_specific_function_format_string'].format(category=category)
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
    idx = 0
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(idx, pins_per_row, configuration)
        idx += 1
