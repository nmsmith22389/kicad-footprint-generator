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
    mode = param['layout']['type'].capitalize()
    #if mode != "Terminal" or mode != "Socket":
    #    raise ValueError("Connector type must be either 'Terminal' or 'Socket'")

    # Pad parameters
    pitch = param['pads']['pitch']
    pad_w = param['pads']['width']
    pad_h = param['pads']['height']
    pins  = param['pads']['n'] # Pin count

    ############################################################################
    # Place pads
    pin = []
    for p in range(pins):
        # Compute next pad location
        pos = (-pins*pitch/2 + pitch/2 + p*pitch, 0)
        pin.append(pos)
        
        # Create pad
        pad = Pad(number = str(p+1),
                  at = pos,
                  size = (pad_w, pad_h),
                  type = Pad.TYPE_SMT,
                  layers = Pad.LAYERS_SMT,
                  shape = Pad.SHAPE_RECT)
        fp.append(pad)

    ############################################################################
    # Holes
    for p in param.get('holes', {}):
        h = [Pad(number = p.get('name', ""),
                 at     = (p['x'], p['y']),
                 drill  = p['drill'],
                 size   = p.get('pad', p['drill']),
                 type   = Pad.TYPE_THT   if 'pad' in p else Pad.TYPE_NPTH,
                 layers = Pad.LAYERS_THT if 'pad' in p else Pad.LAYERS_NPTH,
                 shape  = Pad.SHAPE_CIRCLE)]
        fp.extend(h)
    
    ############################################################################
    # Fabrication layer: F.Fab
    fab_line = config['fab_line_width']
    fab_mark = config['fab_pin1_marker_length']
    fab_w = param['layout']['width']
    fab_h = param['layout']['height']
    
    if mode == "Terminal":
        chamfer = 0.085*fab_h
        outline = [(-fab_w[0]/2 + chamfer, -fab_h/2),
                   (-fab_w[0]/2, -fab_h/2 + chamfer),
                   (-fab_w[0]/2,  fab_h/2),
                   ( fab_w[0]/2,  fab_h/2),
                   ( fab_w[0]/2, -fab_h/2),
                   (-fab_w[0]/2 + chamfer, -fab_h/2)]
    elif mode == "Socket":
        chamfer = 0.1*fab_h
        outline = [(-fab_w[0]/2, -fab_h/2),
                   (-fab_w[0]/2, -fab_h/2 + (fab_w[0]-fab_w[1])/2),
                   (-fab_w[1]/2, -fab_h/2 + (fab_w[0]-fab_w[1])/2),
                   (-fab_w[1]/2,  fab_h/2 - chamfer),
                   (-fab_w[1]/2 + chamfer, fab_h/2),
                   ( fab_w[1]/2,  fab_h/2),
                   ( fab_w[1]/2, -fab_h/2 + (fab_w[0]-fab_w[1])/2),
                   ( fab_w[0]/2, -fab_h/2 + (fab_w[0]-fab_w[1])/2),
                   ( fab_w[0]/2, -fab_h/2),
                   (-fab_w[0]/2, -fab_h/2)]
    
    fp.append(PolygoneLine(nodes = outline,
                               layer = "F.Fab",
                               width = fab_line))

    ############################################################################
    # Silkscreen: F.SilkS
    silk_offset = config['silk_fab_offset']
    silk_pad = {'x': config['silk_pad_clearance'] + pad_w/2,
                'y': config['silk_pad_clearance'] + pad_h/2}
    silk_line = config['silk_line_width']
    silk_w = [w + 2*silk_offset for w in fab_w]
    silk_h = fab_h + 2*silk_offset
    silk_chamfer = chamfer + silk_offset/2

    if mode == "Terminal":
        silk_outline = [(-silk_w[0]/2 + silk_chamfer, -silk_h/2),
                        (-silk_w[0]/2, -silk_h/2 + silk_chamfer),
                        (-silk_w[0]/2,  silk_h/2),
                        ( silk_w[0]/2,  silk_h/2),
                        ( silk_w[0]/2, -silk_h/2),
                        (-silk_w[0]/2 + silk_chamfer, -silk_h/2)]
    elif mode == "Socket":
        silk_outline = [(-silk_w[0]/2, -silk_h/2),
                        (-silk_w[0]/2, -silk_h/2 + (silk_w[0]-silk_w[1])/2 + 2*silk_offset),
                        (-silk_w[1]/2, -silk_h/2 + (silk_w[0]-silk_w[1])/2 + 2*silk_offset),
                        (-silk_w[1]/2,  silk_h/2 - silk_chamfer),
                        (-silk_w[1]/2 + silk_chamfer, silk_h/2),
                        ( silk_w[1]/2,  silk_h/2),
                        ( silk_w[1]/2, -silk_h/2 + (silk_w[0]-silk_w[1])/2 + 2*silk_offset),
                        ( silk_w[0]/2, -silk_h/2 + (silk_w[0]-silk_w[1])/2 + 2*silk_offset),
                        ( silk_w[0]/2, -silk_h/2),
                        (-silk_w[0]/2, -silk_h/2)]

    fp.append(PolygoneLine(nodes = silk_outline,
                           layer = "F.SilkS",
                           width = silk_line))
    
    ############################################################################
    # Courtyard: F.CrtYd
    court_line = config['courtyard_line_width']
    court_grid = config['courtyard_grid']
    court_offset = config['courtyard_offset']['connector']

    
    court_x = roundToBase(fab_w[0]/2 + court_offset, court_grid)
    court_y = roundToBase(fab_h/2 + court_offset, court_grid)

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
    
    # Description
    desc = param['meta']['description']
    desc = desc.format(pn = partnum,
                       pitch = pitch)
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
                        default='Connector_Samtec',
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
