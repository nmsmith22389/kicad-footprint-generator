#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
import argparse
import yaml
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

series = "WR-MM-SMT"
manufacturer = 'Wuerth'
orientation = 'V'
number_of_rows = 2
datasheet = 'https://www.we-online.de/katalog/datasheet/690367290476.pdf'
mpn_pattern = "69036729{n:02}76"

pad_size = [1.5, 3]

pitch = 2.54
pitch_y = 1.5 + pad_size[1]
height = 5
x_offset = 1.27
y_offset = 1.5 + 3

package_offset_x = (9.68 - 3.81) / 2
package_offset_y = (pitch_y - height) / 2


def roundToBase(value, base):
    return round(value / base) * base


def generate_one_footprint(pincount, configuration):
    mpn = mpn_pattern.format(n=pincount)
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_dual_pitch_format_string'] \
        .format(man=manufacturer,
                series=series,
                mpn=mpn,
                num_rows=number_of_rows,
                pins_per_row=pincount // number_of_rows,
                mounting_pad="",
                pitch_x=pitch,
                pitch_y=pitch,
                orientation=orientation_str)

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription(
        "{:s} {:s} series connector, {:s} ({:s}), generated with kicad-footprint-generator".format(
            manufacturer, series, mpn, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string']
                      .format(series=series,
                              orientation=orientation_str,
                              man=manufacturer,
                              entry=configuration['entry_direction'][orientation]))

    # physical outline for fab layer
    width = (pincount / 2 - 1) * pitch + x_offset + 2 * package_offset_x
    # upper left corner of fab-rectangle
    fab_offset = [-package_offset_x, package_offset_y]

    # fab outline
    kicad_mod.append(RectLine(start=fab_offset, end=[fab_offset[0] + width, fab_offset[1] + height],
                              layer='F.Fab', width=configuration['fab_line_width']))

    # Pads
    kicad_mod.append(PadArray(initial=1, increment=2,
                              start=[0, 0],
                              x_spacing=pitch,
                              pincount=pincount // 2,
                              size=pad_size,
                              type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))
    kicad_mod.append(PadArray(initial=2, increment=2,
                              start=[x_offset, y_offset],
                              x_spacing=pitch,
                              pincount=pincount // 2,
                              size=pad_size,
                              type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))

    # Silkscreen:
    silk_offset = 0.2  # configuration["silk_fab_offset"]
    silk_pin1_x = -pad_size[0] / 2 - silk_offset
    silk_pin2_x = silk_pin1_x + x_offset
    silk_pin9_x = (pincount / 2 - 1) * pitch + pad_size[0] / 2 + silk_offset
    silk_pin10_x = silk_pin9_x + x_offset
    silk_right_x = fab_offset[0] + width + silk_offset
    silk_left_x = fab_offset[0] - silk_offset
    silk_upper_y = fab_offset[1] - silk_offset
    silk_lower_y = fab_offset[1] + height + silk_offset

    silk_poly_1 = [
        {'x': silk_pin1_x, 'y': silk_upper_y},
        {'x': silk_left_x, 'y': silk_upper_y},
        {'x': silk_left_x, 'y': silk_lower_y},
        {'x': silk_pin2_x, 'y': silk_lower_y},
    ]
    silk_poly_2 = [
        {'x': silk_pin10_x, 'y': silk_lower_y},
        {'x': silk_right_x, 'y': silk_lower_y},
        {'x': silk_right_x, 'y': silk_upper_y},
        {'x': silk_pin9_x, 'y': silk_upper_y},
    ]

    kicad_mod.append(PolygoneLine(polygone=silk_poly_1, layer="F.SilkS"))
    kicad_mod.append(PolygoneLine(polygone=silk_poly_2, layer="F.SilkS"))

    # Pin1 marker on silkscreen
    kicad_mod.append(Text(
        type='user',
        text="1",
        at=[silk_pin1_x - 0.5, silk_upper_y - 0.6],
        size=[0.8, 0.8],
        layer="F.SilkS"))
    kicad_mod.append(Text(
        type='user',
        text="2",
        at=[silk_pin2_x - 0.5, silk_lower_y + 0.6],
        size=[0.8, 0.8],
        layer="F.SilkS"))

    # Courtyard
    body_edge = {'left': fab_offset[0],
                 'right': fab_offset[0] + width,
                 'top': fab_offset[1] - 1,
                 'bottom': fab_offset[1] + height + 1}
    courtyard_offset = configuration["courtyard_offset"]["connector"]
    cx1 = roundToBase(body_edge["left"] - courtyard_offset, configuration['courtyard_grid'])
    cx2 = roundToBase(body_edge["right"] + courtyard_offset, configuration['courtyard_grid'])

    cy1 = roundToBase(body_edge["top"] - courtyard_offset, configuration['courtyard_grid'])
    cy2 = roundToBase(body_edge["bottom"] + courtyard_offset, configuration['courtyard_grid'])
    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    # Text Fields
    addTextFields(kicad_mod=kicad_mod,
                  configuration=configuration,
                  body_edges=body_edge,
                  courtyard={'top': cy1, 'bottom': cy2},
                  fp_name=footprint_name)

    model3d_path_prefix = configuration.get('3d_model_prefix', '${KISYS3DMOD}/')

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    filename = '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?',
                        help='the config file defining how the footprint will look like. (KLC)',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.',
                        default='../conn_config_KLCv3.yaml')
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

    for pincount in range(4, 27, 2):
        generate_one_footprint(pincount, configuration)
