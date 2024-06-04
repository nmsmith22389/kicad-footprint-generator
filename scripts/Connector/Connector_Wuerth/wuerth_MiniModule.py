#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields
import cli

series = "WR-MM"
manufacturer = "Wuerth"
orientation = "V"
number_of_rows = 2
datasheet_pattern = "https://www.we-online.de/katalog/datasheet/{mpn}.pdf"
mpn_pattern = "69036719{n:02}72"

drill_size = 0.85
annular_ring = 0.25

pitch = 2.54
offset = 1.27

height = 5

# polarization hole to align wire-part of connector
align_hole_diameter = 1.5
align_hole_position = [1.4, 1.8]


def roundToBase(value, base):
    return round(value / base) * base


def generate_one_footprint(pincount, configuration):
    mpn = mpn_pattern.format(n=pincount)
    datasheet = datasheet_pattern.format(mpn=mpn)
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
        f"{manufacturer} {series} series connector, {mpn} ({datasheet}), generated with kicad-footprint-generator")
    kicad_mod.setTags(configuration['keyword_fp_string']
                      .format(series=f"Mini Module {series}",
                              orientation=orientation_str,
                              man=manufacturer,
                              entry=configuration['entry_direction'][orientation]))

    # physical outline for fab layer
    width = pincount * 1.27 + 4.6
    # upper right corner of fab-rectangle
    fab_offset = [(width - (pincount - 1) * offset) / 2, - (height - 2.54) / 2]

    # fab outline
    kicad_mod.append(RectLine(start=fab_offset, end=[fab_offset[0] - width, fab_offset[1] + height],
                              layer='F.Fab', width=configuration['fab_line_width']))

    # Pads
    kicad_mod.append(PadArray(initial=1, start=[0, 0], increment=2,
                              x_spacing=-pitch, pincount=pincount // 2,
                              size=drill_size + 2 * annular_ring, drill=drill_size,
                              type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT))
    kicad_mod.append(PadArray(initial=2, start=[-offset, pitch], increment=2,
                              x_spacing=-pitch, pincount=pincount // 2,
                              size=drill_size + 2 * annular_ring, drill=drill_size,
                              type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT))

    kicad_mod.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, drill=align_hole_diameter, at=align_hole_position,
                         size=align_hole_diameter, layers=Pad.LAYERS_NPTH))

    # Silkscreen: rectangle
    silk_offset = configuration["silk_fab_offset"]
    silk_right_x = fab_offset[0] + silk_offset
    silk_left_x = fab_offset[0] - width - silk_offset
    silk_upper_y = fab_offset[1] - silk_offset
    silk_lower_y = fab_offset[1] + height + silk_offset
    kicad_mod.append(RectLine(start=[silk_left_x, silk_lower_y], end=[silk_right_x, silk_upper_y], layer="F.SilkS"))

    # Courtyard
    body_edge = {'left': fab_offset[0] - width, 'right': fab_offset[0], 'top': fab_offset[1],
                 'bottom': fab_offset[1] + height}
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
    configuration = cli.get_config_from_commandline()
    for pincount in range(4, 27, 2):
        generate_one_footprint(pincount, configuration)
