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

Datasheet not found available online
See https://github.com/KiCad/kicad-footprints/files/3331008/ENG_CD_928492_B3.pdf

Generates only the gray color part numbers
Footprints are the same, but different colors have unique keying
Thus 3D models would be unique

"""

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

manufacturer = "TE-Connectivity"
partnumber = "928492"
datasheet = "https://github.com/KiCad/kicad-footprints/files/3331008/ENG_CD_928492_B3.pdf"

pincounts = [2,4,6,7,8,9,11,12]

def generate_one_footprint(pincount, configuration):
    pitch = 5
    drill = [1.2, 1.1] # pin row closest to open end is 1.1mm and back row is 1.2mm
    pad_size = [2.4, 2.4]
    
    body_overhang = 7.4 # body width increase over total pin width
    body_left = -body_overhang / 2
    body_right = (pincount - 1) * pitch + body_overhang / 2
    body_bottom = pitch + 8.5
    body_top = body_bottom - 17.4

    # for gray color, a leading "0" is for <10 pins and a leading "1" for >=10 pins (other leading numbers mean different colors)
    footprint_name = 'TE_{pnp}-{pn:s}-{pns}_1x{pc:02g}_P{p}mm_Horizontal'\
        .format(pnp="1" if pincount >= 10 else "0", pn=partnumber, pns=str(pincount)[-1], pc=pincount, p=pitch)
    print('Building {:s}'.format(footprint_name))

    body_edge = {
        'left': body_left,
        'right': body_right,
        'top': body_top,
        'bottom': body_bottom
    }

    # initialise footprint
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription('TE connector, shrouded, keyed, horizontal blade pins, {pc} pins, {pitch}mm pitch, {ds}, generated with kicad-footprint-generator'.format(pc=pincount, pitch=pitch, ds=datasheet))
    kicad_mod.setTags('te {:s}'.format(partnumber))

    # create pads
    for pos_y, drill in zip([0, pitch], drill):
        for pin in range(1, pincount + 1):
            pad_shape = Pad.SHAPE_ROUNDRECT if pin == 1 else Pad.SHAPE_CIRCLE
            
            # pins are linear for pins counts 1-6 and staggered for 7-12
            stagger = 2.5 if (pincount >= 7 and pin % 2 == 0) else 0
            
            kicad_mod.append(Pad(number=pin,
                at=[(pin - 1) * pitch, pos_y - stagger],
                type=Pad.TYPE_THT, shape=pad_shape,
                radius_ratio=0.25, maximum_radius=0.25,
                drill=drill, size=pad_size,
                layers=Pad.LAYERS_THT))

    # since pins are totally inside the part body, all fab, silk, and courtyard lines can be drawn together
    for offset, layer, line_width in zip([0, configuration['silk_fab_offset'], configuration['courtyard_offset']['connector']], ['F.Fab', 'F.SilkS', 'F.CrtYd'], [configuration['fab_line_width'], configuration['silk_line_width'], configuration['courtyard_line_width']]):
        kicad_mod.append(PolygoneLine(
            polygone=[
                [body_edge['left'] - offset, body_edge['top'] - offset],
                [body_edge['right'] + offset, body_edge['top'] - offset],
                [body_edge['right'] + offset, body_edge['bottom'] + offset],
                [body_edge['left'] - offset, body_edge['bottom'] + offset],
                [body_edge['left'] - offset, body_edge['top'] - offset]],
            layer=layer, width=line_width))

    # create silkscreen pin 1 marker
    pin1_mark_height = 1
    pin1_mark_width = 1
    pin1_mark_offset = 0.5
    
    kicad_mod.append(PolygoneLine(
        polygone=[
            [0, body_edge['top'] - pin1_mark_offset],
            [-pin1_mark_width / 2, body_edge['top'] - pin1_mark_offset - pin1_mark_height],
            [pin1_mark_width / 2, body_edge['top'] - pin1_mark_offset - pin1_mark_height],
            [0, body_edge['top'] - pin1_mark_offset]],
        layer='F.SilkS', width=configuration['silk_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':body_edge['top'] - configuration['courtyard_offset']['connector'],
        'bottom':body_edge['bottom'] + configuration['courtyard_offset']['connector']},
        fp_name=footprint_name)

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

    lib_name = configuration['lib_name_format_string'].format(man=manufacturer)

    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename = '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

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

    for pincount in pincounts:
        generate_one_footprint(pincount, configuration)
