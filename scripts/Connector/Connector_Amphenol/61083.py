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

#based on ../Connector_Molex/conn_molex_micro-fit-3.0_smd_top_dual_row.py

import sys
import os

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import sqrt
import argparse
import yaml
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

series = "BergStak"
manufacturer = 'Amphenol'
orientation = 'V'
number_of_rows = 2
datasheet = "https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/61083.pdf"

variant_params = {
    'no_peg':{
        'peg': 'no',
        'part_code': "61083-{n}xx2x"
        },
    'peg':{
        'peg': 'yes',
        'part_code': "61083-{n}xx0x"
        }
}

pins_per_row_range = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
pitch = 0.8


pad_size = [0.5, 2.0]
pitch_y = 6.4 - pad_size[1]

mount_pad_size = [3.43, 1.65]
mount_drill_left = 0.8
mount_drill_right = 1.2

def generate_one_footprint(pins_per_row, variant, configuration):
    is_peg = variant_params[variant]['peg'] == 'yes'

    if pins_per_row < 50:
        pincount_code = "0" + str(pins_per_row*2/10)[0]
    else:
        pincount_code = str(pins_per_row*2/10)[:2]

    mpn = variant_params[variant]['part_code'].format(n=pincount_code)

    # handle arguments
    mp_name = ""
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = mp_name,
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("{:s} {:s} {:d} Pins per row ({:s}), generated with kicad-footprint-generator".format(manufacturer, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    kicad_mod.setAttribute('smd')

    ########################## Dimensions ##############################
    A = (pins_per_row-1)*pitch
    B = A + 6.6
    C = A + 5

    pad_row_1_y = -pitch_y/2
    pad_row_2_y = pad_row_1_y + pitch_y
    pad1_x = -A/2

    mount_pad_x = C/2
    mount_pad_y = pad_row_1_y + pitch_y/2

    tab_w = 1.4
    tab_l = 1.4

    body_width = 6

    body_edge={
        'left': -B/2,
        'right': B/2,
        'bottom': body_width/2,
        'top': -body_width/2
        }

    bounding_box={
        'left': body_edge['left'],
        'right': body_edge['right'],
        'top': pad_row_1_y - pad_size[1]/2,
        'bottom': pad_row_2_y + pad_size[1]/2
    }

    ############################# Pads ##################################
    if is_peg:
        kicad_mod.append(Pad(at=[-mount_pad_x, mount_pad_y], number="",
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill_left,
            drill=mount_drill_left, layers=Pad.LAYERS_NPTH))
        kicad_mod.append(Pad(at=[mount_pad_x, mount_pad_y], number="",
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill_right,
            drill=mount_drill_right, layers=Pad.LAYERS_NPTH))

    #
    # Add pads
    #
    kicad_mod.append(PadArray(start=[pad1_x, pad_row_1_y], initial=1,
        pincount=pins_per_row, increment=2,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))
    kicad_mod.append(PadArray(start=[pad1_x, pad_row_2_y], initial=2,
        pincount=pins_per_row, increment=2, x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))


    ######################## Fabrication Layer ###########################
    main_body_poly= [
        {'x': body_edge['left'], 'y': body_edge['top']},
        {'x': body_edge['left'], 'y': body_edge['bottom']},
        {'x': body_edge['right'], 'y': body_edge['bottom']},
        {'x': body_edge['right'], 'y': body_edge['top']},
        {'x': body_edge['left'], 'y': body_edge['top']}
    ]
    kicad_mod.append(PolygoneLine(polygone=main_body_poly,
        width=configuration['fab_line_width'], layer="F.Fab"))

    p1m_sl = 1
    tab_poly = [
        {'x': pad1_x - p1m_sl/2, 'y': body_edge['top']},
        {'x': pad1_x, 'y': body_edge['top'] + p1m_sl/sqrt(2)},
        {'x': pad1_x + p1m_sl/2, 'y': body_edge['top']}
    ]
    kicad_mod.append(PolygoneLine(polygone=tab_poly,
        width=configuration['fab_line_width'], layer="F.Fab"))

    ############################ SilkS ##################################
    # Top left corner

    silk_pad_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    xp1_left = pad1_x - pad_size[0]/2 - silk_pad_off
    ymp_top = mount_pad_y - mount_pad_size[1]/2 - silk_pad_off
    ymp_bottom = mount_pad_y + mount_pad_size[1]/2 + silk_pad_off
    xpn_right = pad1_x + A + pad_size[0]/2 + silk_pad_off
    off = configuration['silk_fab_offset']

    poly_s_bl = [
        {'x': body_edge['left'] - off, 'y': ymp_bottom},
        {'x': body_edge['left'] - off, 'y': body_edge['bottom'] + off},
        {'x': xp1_left, 'y': body_edge['bottom'] + off}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_s_bl,
        width=configuration['silk_line_width'], layer="F.SilkS"))

    poly_s_br = [
        {'x': body_edge['right'] + off, 'y': ymp_bottom},
        {'x': body_edge['right'] + off, 'y': body_edge['bottom'] + off},
        {'x': xpn_right, 'y': body_edge['bottom'] + off}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_s_br,
        width=configuration['silk_line_width'], layer="F.SilkS"))

    poly_s_tl = [
        {'x': body_edge['left'] - off, 'y': ymp_top},
        {'x': body_edge['left'] - off, 'y': body_edge['top'] - off},
        {'x': xp1_left, 'y': body_edge['top'] - off},
        {'x': xp1_left, 'y': bounding_box['top']}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_s_tl,
        width=configuration['silk_line_width'], layer="F.SilkS"))

    poly_s_br = [
        {'x': body_edge['right'] + off, 'y': ymp_top},
        {'x': body_edge['right'] + off, 'y': body_edge['top'] - off},
        {'x': xpn_right, 'y': body_edge['top'] - off}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_s_br,
        width=configuration['silk_line_width'], layer="F.SilkS"))

    p1m_poly = [
        {'x': pad1_x - p1m_sl/2, 'y': bounding_box['top'] - p1m_sl/sqrt(2) - configuration['silk_pad_clearance']},
        {'x': pad1_x, 'y': bounding_box['top'] - configuration['silk_pad_clearance']},
        {'x': pad1_x + p1m_sl/2, 'y': bounding_box['top'] - p1m_sl/sqrt(2) - configuration['silk_pad_clearance']},
        {'x': pad1_x - p1m_sl/2, 'y': bounding_box['top'] - p1m_sl/sqrt(2) - configuration['silk_pad_clearance']}
    ]
    kicad_mod.append(PolygoneLine(polygone=p1m_poly,
        width=configuration['silk_line_width'], layer="F.SilkS"))
    ############################ CrtYd ##################################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    cy_top = roundToBase(bounding_box['top'] - CrtYd_offset, CrtYd_grid)
    cy_body_top = roundToBase(body_edge['top'] - CrtYd_offset, CrtYd_grid)
    cy_body_bottom = roundToBase(body_edge['bottom'] + CrtYd_offset, CrtYd_grid)
    cy_bottom = roundToBase(bounding_box['bottom'] + CrtYd_offset, CrtYd_grid)

    cy_left = roundToBase(bounding_box['left'] - CrtYd_offset, CrtYd_grid)
    cy_body_left = roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)
    cy_pad_left = roundToBase(pad1_x - pad_size[0]/2 - CrtYd_offset, CrtYd_grid)
    cy_pad_right = roundToBase(pad1_x + A + pad_size[0]/2 + CrtYd_offset, CrtYd_grid)
    cy_body_right = roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid)
    cy_right = roundToBase(bounding_box['right'] + CrtYd_offset, CrtYd_grid)

    CrtYd_poly_t = [
        {'x': pad1_x + A/2, 'y':cy_top},
        {'x': cy_pad_left, 'y':cy_top},
        {'x': cy_pad_left, 'y':cy_body_top},
        {'x': cy_body_left, 'y':cy_body_top}
        ]
    CrtYd_poly_b = [
        {'x': cy_body_left, 'y':cy_body_bottom},
        {'x': cy_pad_left, 'y':cy_body_bottom},
        {'x': cy_pad_left, 'y':cy_bottom},
        {'x': pad1_x + A/2, 'y':cy_bottom}
    ]
    CrtYd_poly = CrtYd_poly_t
    CrtYd_poly.extend(CrtYd_poly_b)

    kicad_mod.append(PolygoneLine(polygone=CrtYd_poly,
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    kicad_mod.append(PolygoneLine(polygone=CrtYd_poly,
        layer='F.CrtYd', width=configuration['courtyard_line_width'],
        x_mirror= 0.00000001 if pad1_x + A/2 == 0 else pad1_x + A/2))
    ######################### Text Fields ###############################


    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy_top, 'bottom':cy_bottom}, fp_name=footprint_name, text_y_inside_position='bottom')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
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
    for variant in variant_params:
        for pins_per_row in pins_per_row_range:
            generate_one_footprint(pins_per_row, variant, configuration)
