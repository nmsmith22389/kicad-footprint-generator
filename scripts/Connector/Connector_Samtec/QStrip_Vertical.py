#!/usr/bin/python

# This file is part of kicad-footprint-generator.
# 
# kicad-footprint-generator is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# kicad-footprint-generator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details. You should have received a copy of the GNU General Public
# License along with kicad-footprint-generator. If not, see
# <http://www.gnu.org/licenses/>.
# 
# Copyright (C) 2020 by Caleb Reister <calebreister@gmail.com>
#

import sys
import os
import argparse
from copy import deepcopy
import math
import yaml

# Load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))

from KicadModTree import *
from footprint_text_fields import addTextFields
from helpers import *
from dict_tools import *

def generate_one_footprint(param, config, default_lib):
    fp = Footprint(param['name'])
    
    # Terminal or Socket mode
    mode = param['layout']['type'].capitalize()
    if mode == "Terminal":
        x_inv = 1
    elif mode == "Socket":
        x_inv = -1
    else:
        raise ValueError("Connector type must be either 'Terminal' or 'Socket'")
    
    # Bank parameters
    banks  = param['banks']['n']
    bank_x = param['banks']['space']
    bank_w = param['banks']['width']
    bank_h = param['banks']['height']

    ############################################################################
    # Copper layer(s)
    
    # Signal pad parameters
    pitch = param['pads']['signal']['pitch']
    pad_w = param['pads']['signal']['width']
    pad_h = param['pads']['signal']['height']
    pad_y = param['pads']['signal']['y']
    pad_n = param['pads']['signal']['n']

    # Pin 1 position
    pin1 = Vector2D(0,0)
    pin1.x = -(pad_n / 4)*pitch + pitch/2 - ((banks-1) / 2)*bank_x
    pin1.y = -pad_y
    
    # Bank 1 center point
    bank1_mid = x_inv * (pin1.x - pitch/2 + (pad_n / 4)*pitch)

    # Place pads
    n = 1 # Pin counter
    pin = [] # Pin position list, organized by bank
    for b in range(banks):
        pin.append([])
        # Place signal pads
        for slot in range(pad_n):
            # Compute next pad location
            pos = {'x': x_inv * (pin1.x + (slot // 2)*pitch + b*bank_x),
                   'y': pin1.y - (slot  % 2)*(2*pin1.y),
                   'n': n+1, 'slot': slot}

            # Skip slots for differential banks
            if b < param['banks'].get('diff', 0):
                if ((slot+1) % 6 == 0 or # Skip every 3rd odd slot
                    (slot+2) % 6 == 0 or # Skip every 3rd even slot
                    # Only add end-of-bank pins if they are completing a pair
                    (slot+2 >= pad_n and
                     pin[b][-2]['slot'] != slot-2)):
                    continue

            # Create pad
            pin[b].append(pos) # Add position to list
            pad = Pad(number = str(n),
                      at = pos,
                      size = (pad_w, pad_h),
                      type = Pad.TYPE_SMT,
                      layers = Pad.LAYERS_SMT,
                      shape = Pad.SHAPE_RECT)
            fp.append(pad)
            n += 1
    
        # Place plane pads
        mid = bank1_mid + x_inv*b*bank_x # Bank midpoint
        for plane in param['pads'].get('planes', {}):
            pad = Pad(number = "P" + str(b+1),
                      at = (plane['x'] + mid, plane['y']),
                      size = (plane['width'], plane['height']),
                      type = Pad.TYPE_SMT,
                      layers = Pad.LAYERS_SMT,
                      shape = Pad.SHAPE_RECT)
            fp.append(pad)

    ############################################################################
    # Holes
    if 'holes' in param:
        for hole in param['holes']:
            drill = hole['drill']
            shape = Pad.SHAPE_CIRCLE if type(drill) is float else Pad.SHAPE_OVAL
            h = [Pad(number = "MP" if 'pad' in hole else "",
                     at     = (m*hole['space']/2, hole['y']),
                     drill  = drill,
                     size   = hole['pad'] if 'pad' in hole else drill,
                     type   = Pad.TYPE_THT if 'pad' in hole else Pad.TYPE_NPTH,
                     layers = Pad.LAYERS_THT if 'pad' in hole else Pad.LAYERS_NPTH,
                     shape  = shape) for m in (-1,1)]
            fp.extend(h)

    ############################################################################
    # Fabrication layer: F.Fab
    fab_line = config['fab_line_width']
    fab_mark = config['fab_pin1_marker_length']
    fab_w = param['layout']['width'] if 'width' not in param else param['width']
    fab_h = param['layout']['height']
    fab_y = fab_h / 2
    fab_edge = fab_w/2
    chamfer = fab_h / 4 # 1/4 connector height, cosmetic only

    if mode == 'Terminal':
        # End outline
        fab_end = [(-fab_edge, -fab_y),
                   (-fab_edge, fab_y-chamfer),
                   (-fab_edge+chamfer, fab_y)]
        fp.append(PolygoneLine(nodes = fab_end,
                               layer = "F.Fab",
                               width = fab_line))
        # Right end outline (mirrors left end)
        fp.append(PolygoneLine(nodes = fab_end,
                               layer = "F.Fab",
                               width = fab_line,
                               x_mirror = 0))
        # Top and bottom lines
        fp.append(Line(start = (-fab_edge, -fab_y),
                       end   = ( fab_edge, -fab_y),
                       layer = "F.Fab",
                       width = fab_line))
        fp.append(Line(start = (-fab_edge+chamfer, fab_y),
                       end   = ( fab_edge-chamfer, fab_y),
                       layer = "F.Fab",
                       width = fab_line))
        # Pin 1 marker
        fp.append(markerArrow(x = pin1.x,
                              y = (fab_mark-fab_h) / 2,
                              width = fab_mark,
                              angle = 180,
                              layer = "F.Fab",
                              close = False,
                              line_width = fab_line))
    elif mode == 'Socket':
        # Outline rectangle
        fp.append(RectLine(start = (-fab_edge, -fab_y),
                           end   = ( fab_edge,  fab_y),
                           layer = "F.Fab",
                           width = fab_line))
        # Chamfer lines
        fp.append(Line(start = (-fab_edge, fab_y-chamfer),
                       end   = (-fab_edge+chamfer, fab_y),
                       layer = "F.Fab",
                       width = fab_line))
        fp.append(Line(start = (fab_edge, fab_y-chamfer),
                       end   = (fab_edge-chamfer, fab_y),
                       layer = "F.Fab",
                       width = fab_line))
        # Pin 1 marker
        fp.append(markerArrow(x = -pin1.x,
                              y = -(fab_h-fab_mark) / 2,
                              width = fab_mark,
                              angle = 180,
                              layer = "F.Fab",
                              close = False,
                              line_width = fab_line))

    # Draw bank and ground plane outlines
    for b in range(banks):
        mid = bank1_mid + x_inv*b*bank_x
        # Bank outline
        fp.append(RectLine(start = (mid-bank_w/2, -bank_h/2),
                           end   = (mid+bank_w/2,  bank_h/2),
                           layer = "F.Fab",
                           width = fab_line))
    
    ############################################################################
    # Silkscreen: F.SilkS
    silk_offset = config['silk_fab_offset']
    silk_pad = {'x': config['silk_pad_clearance'] + pad_w/2,
                'y': config['silk_pad_clearance'] + pad_h/2}
    silk_line = config['silk_line_width']
    silk_y = fab_y + silk_offset
    silk_edge = fab_edge + silk_offset
    silk_chamfer = chamfer + silk_offset/2
    
    if mode == 'Terminal':
        # Polygon left end outline points
        silk_end = [[(pin[i][i]['x']+m*silk_pad['x'], -silk_y),
                     (m*silk_edge, -silk_y),
                     (m*silk_edge,  silk_y-silk_chamfer),
                     (m*(silk_edge-silk_chamfer), silk_y),
                     (pin[i][i]['x']+m*silk_pad['x'],  silk_y)]
                    for (i,m) in ((0,-1), (-1,1))]
        # Pin 1 indicator
        fp.append(Line(start = (pin[0][0]['x']-silk_pad['x'], pin1.y - pad_h/2),
                       end   = (pin[0][0]['x']-silk_pad['x'], -silk_y),
                       layer = "F.SilkS",
                       width = silk_line))
    elif mode == 'Socket':
        # Left end outline points
        silk_end = [[(pin[i][i]['x']+m*silk_pad['x'],  silk_y),
                     (m*silk_edge,  silk_y),
                     (m*silk_edge, -silk_y),
                     (pin[i][i]['x']+m*silk_pad['x'], -silk_y)]
                    for (i,m) in ((0,1), (-1,-1))]
        # Pin 1 indicator
        fp.append(markerArrow(x = pin[0][0]['x'],
                              y = pin[0][0]['y'] - silk_pad['y'],
                              width = fab_mark / 2,
                              line_width = silk_line,
                              angle = 180,
                              layer = "F.SilkS"))
    
    # Draw end outlines
    fp.extend([PolygoneLine(nodes = end,
                            layer = "F.SilkS",
                            width = silk_line) for end in silk_end])

    # Draw outlines between banks
    for b in range(banks-1):
        fp.extend([Line(start = (pin[b][-1]['x']  + x_inv*silk_pad['x'], m*silk_y),
                        end   = (pin[b+1][0]['x'] - x_inv*silk_pad['x'], m*silk_y),
                        layer = "F.SilkS",
                        width = silk_line) for m in (-1,1)])

    ############################################################################
    # Courtyard: F.CrtYd
    court_line = config['courtyard_line_width']
    court_grid = config['courtyard_grid']
    court_offset = config['courtyard_offset']['connector']

    court_x = roundToBase(fab_w/2 + court_offset, court_grid)
    court_y = roundToBase(max(fab_y, pad_y + pad_h/2) + court_offset, court_grid)

    fp.append(RectLine(start  = (-court_x, -court_y),
                       end    = ( court_x,  court_y),
                       layer  = "F.CrtYd",
                       width  = court_line))
    
    ############################################################################
    # Set Metadata
    
    # Draw reference and value
    text_y = court_y + 1.0
    fp.append(Text(type = 'reference', text = 'REF**',
                   at = (0, -text_y),
                   layer = "F.SilkS"))
    fp.append(Text(type = 'user', text = '${REFERENCE}',
                   at = (0, -text_y),
                   layer = "F.Fab"))
    fp.append(Text(type = 'value', text=param['name'],
                   at = (0, text_y),
                   layer="F.Fab"))
    
    # Set surface-mount attribute
    fp.setAttribute('smd')
    
    # Part number
    partnum = param['meta'].get('pn', param['name'].split('_')[1])

    # Pins or pairs/bank
    if param['banks'].get('diff', 0) == banks:
        # Differential mode: round up to nearest even number of pairs
        pins_or_pairs = (pad_n // 3) + (pad_n // 3) % 2
    else:
        pins_or_pairs = pad_n

    # Description
    desc = param['meta']['description']
    desc = desc.format(pn = partnum,
                       type = mode,
                       pitch = pitch,
                       banks = banks,
                       pins = pins_or_pairs)
    fp.setDescription(desc + ", generated with kicad-footprint-generator"
                      + ", " + param['meta']['datasheet'])

    # Tags
    tags = param['meta']['tags']
    fp.setTags(tags)

    # 3D model path
    library = param.get('library', default_lib)
    model_path = os.path.join("${KISYS3DMOD}",
                              library+".3dshapes",
                              param['name'] + ".wrl")
    fp.append(Model(filename = model_path))

    ############################################################################
    # Write kicad_mod file
    
    os.makedirs(library+'.pretty', exist_ok=True)
    filename = os.path.join(library+'.pretty', param['name']+'.kicad_mod')
    KicadFileHandler(fp).writeFile(filename)

################################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--global-config', type=str, nargs='?',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml',
                        help='Global KLC configuration YAML file')
    parser.add_argument('--series-config', type=str, nargs='?',
                        default='../conn_config_KLCv3.yaml',
                        help='Series KLC configuration YAML file')
    parser.add_argument('--library', type=str, nargs='?',
                        default='Connector_Samtec_QStrip',
                        help='Default KiCad library name (without extension)')
    parser.add_argument('files', metavar='file', type=str, nargs='*',
                        help='YAML file(s) containing footprint parameters')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            config = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)
    with open(args.series_config, 'r') as config_stream:
        try:
            config.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    if len(args.files) == 0:
        parser.print_help()
        sys.exit(1)

    print("Default Library:", args.library)
    for path in args.files:
        print("Reading", path)
        with open(path, 'r') as stream:
            try:
                footprints = yaml.safe_load(stream)
                if footprints is None:
                    print(path, "empty, skipping...")
                    continue
                dictInherit(footprints)
                for fp_name in footprints:
                    fp_params = footprints.get(fp_name)                    
                    if 'name' in fp_params:
                        print("WARNING: setting 'name' to", fp_name)
                    fp_params['name'] = fp_name
                    print("  - ",
                          fp_params.get('library', args.library), ".pretty/",
                          fp_name, ".kicad_mod", sep="")
                    generate_one_footprint(fp_params, config, args.library)
            except yaml.YAMLError as exc:
                print(exc)
