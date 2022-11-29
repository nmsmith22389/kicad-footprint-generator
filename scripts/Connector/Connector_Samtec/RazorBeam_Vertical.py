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

    # Pad parameters
    pitch = param['pads']['pitch']
    pad_w = param['pads']['width']
    pad_h = param['pads']['height']
    pad_y = param['pads']['y']
    pins  = param['pads']['n'] # Pin count

    # Part number
    partnum = param['meta'].get('pn', param['name'].split('_')[1])
    
    # Description
    desc = param['meta']['description']
    desc = desc.format(pn = partnum, pitch = pitch)
    fp.setDescription(desc + ", generated with kicad-footprint-generator"
                      + ", " + param['meta']['datasheet'])

    # Tags
    tags = param['meta']['tags']
    fp.setTags(tags)

    ############################################################################
    # Place pads
    # Pin 1 position
    pin1 = Vector2D(-(pins/4)*pitch + pitch/2, -pad_y)
    
    pin = [] # Pin position list
    for p in range(pins):
        # Compute next pad location
        pos = {'x': pin1.x + (p // 2)*pitch,
               'y': pin1.y - (p  % 2)*(2*pin1.y)}
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
    # Fabrication layer: F.Fab
    fab_line = config['fab_line_width']
    fab_mark = config['fab_pin1_marker_length']
    fab_w = param['layout']['width']
    fab_h = param['layout']['height']
    fab_y = param['layout'].get('y', 0)
    lEdge = -fab_w / 2
    rEdge = lEdge + fab_w

    # Draw outline
    if "LSS" in tags:
        chamfer = fab_h / 3.5 # cosmetic only
        outline = [(lEdge + chamfer, -fab_h/2 + fab_y),
                   (lEdge, -fab_h/2 + chamfer + fab_y),
                   (lEdge, fab_h/2 + fab_y),
                   (rEdge, fab_h/2 + fab_y),
                   (rEdge, -fab_h/2 + chamfer + fab_y),
                   (rEdge - chamfer, -fab_h/2 + fab_y),
                   (lEdge + chamfer, -fab_h/2 + fab_y)]
    else:
        chamfer = fab_h / 10
        outline = [(lEdge + chamfer, -fab_h/2 + fab_y),
                   (lEdge, -fab_h/2 + chamfer + fab_y),
                   (lEdge,  fab_h/2 - chamfer + fab_y),
                   (lEdge + chamfer, fab_h/2 + fab_y),
                   (rEdge - chamfer, fab_h/2 + fab_y),
                   (rEdge,  fab_h/2 - chamfer + fab_y),
                   (rEdge, -fab_h/2 + chamfer + fab_y),
                   (rEdge - chamfer, -fab_h/2 + fab_y),
                   (lEdge + chamfer, -fab_h/2 + fab_y)]
    
    fp.append(PolygoneLine(nodes = outline,
                           layer = "F.Fab",
                           width = fab_line))

    # Pin 1 marker
    fp.append(markerArrow(x = pin1.x,
                          y = (fab_mark-fab_h) / 2  + fab_y,
                          width = fab_mark,
                          angle = 180,
                          layer = "F.Fab",
                          close = False,
                          line_width = fab_line))

    ############################################################################
    # Holes
    hole_list = param['holes']
    for p in hole_list:
        drill = p['drill']
        shape = Pad.SHAPE_CIRCLE if type(drill) is float else Pad.SHAPE_OVAL
        h = [Pad(number = p.get('name', ""),
                 at     = (m*p['space']/2, p['y']),
                 drill  = drill,
                 size   = p.get('pad', drill),
                 type   = Pad.TYPE_THT   if 'pad' in p else Pad.TYPE_NPTH,
                 layers = Pad.LAYERS_THT if 'pad' in p else Pad.LAYERS_NPTH,
                 shape  = shape) for m in (-1,1)]
        fp.extend(h)
        # Extend courtyard width for shield holes
        if p['space'] + p.get('pad', drill) > fab_w:
            fab_w = p['space'] + p.get('pad', drill)
            sh_x = p['space']/2
            sh_y = p['y']
            sh_r = p.get('pad', drill) / 2
    
    ############################################################################
    # Courtyard: F.CrtYd
    court_line = config['courtyard_line_width']
    court_grid = config['courtyard_grid']
    court_offset = config['courtyard_offset']['connector']
    
    court_x = roundToBase(fab_w/2 + court_offset, court_grid)
    court_y = roundToBase(max(fab_h/2+fab_y, pad_y+pad_h/2) + court_offset, court_grid)

    fp.append(RectLine(start  = (-court_x, -court_y),
                       end    = ( court_x,  court_y),
                       layer  = "F.CrtYd",
                       width  = court_line))

    ############################################################################
    # Silkscreen: F.SilkS
    silk_offset = config['silk_fab_offset']
    silk_y = fab_h/2 + silk_offset
    silk_pad = {'x': config['silk_pad_clearance'] + pad_w/2,
                'y': config['silk_pad_clearance'] + pad_y/2,
                'hole': config['silk_pad_clearance']}
    silk_line = config['silk_line_width']
    silk_lEdge = lEdge - silk_offset
    silk_rEdge = rEdge + silk_offset
    silk_chamfer = chamfer + silk_offset/2
    silk_pin1 = pin1.x - silk_pad['x']

    if "shield" in tags:
        silk_sh = math.sqrt((sh_r+silk_pad['hole'])**2 - (silk_rEdge-sh_x)**2)
        silk_lEnd = [[{'x': silk_pin1, 'y': -silk_y},
                      {'x': silk_lEdge + silk_chamfer, 'y': -silk_y},
                      {'x': silk_lEdge, 'y': -silk_y + silk_chamfer},
                      {'x': silk_lEdge, 'y': sh_y - silk_sh}],
                     [{'x': silk_lEdge, 'y': sh_y + silk_sh},
                      {'x': silk_lEdge, 'y': silk_y - silk_chamfer},
                      {'x': silk_lEdge + silk_chamfer, 'y': silk_y},
                      {'x': silk_pin1, 'y': silk_y}]]
    elif "LSS" in tags:
        silk_lEnd = [[{'x': silk_pin1,  'y': -silk_y + fab_y},
                      {'x': silk_lEdge + silk_chamfer, 'y': -silk_y + fab_y},
                      {'x': silk_lEdge, 'y': -silk_y + fab_y + silk_chamfer},
                      {'x': silk_lEdge, 'y':  silk_y + fab_y},
                      {'x': silk_pin1,  'y':  silk_y + fab_y}]]
    else:
        silk_lEnd = [[{'x': silk_pin1, 'y': -silk_y},
                      {'x': silk_lEdge + silk_chamfer, 'y': -silk_y},
                      {'x': silk_lEdge, 'y': -silk_y + silk_chamfer},
                      {'x': silk_lEdge, 'y':  silk_y - silk_chamfer},
                      {'x': silk_lEdge + silk_chamfer, 'y': silk_y},
                      {'x': silk_pin1, 'y': silk_y}]]

    # Generate right outline
    silk_rEnd = deepcopy(silk_lEnd)
    # Mirror about x axis
    for a in range(len(silk_lEnd)):
        for b in range(len(silk_lEnd[a])):
            silk_rEnd[a][b]['x'] = -silk_rEnd[a][b]['x']

    # Draw left and right outlines
    for i in range(len(silk_lEnd)):
        fp.append(PolygoneLine(nodes = silk_lEnd[i],
                               layer = "F.SilkS",
                               width = silk_line))
        fp.append(PolygoneLine(nodes = silk_rEnd[i],
                               layer = "F.SilkS",
                               width = silk_line))

    # Pin 1 indicator
    fp.append(markerArrow(x = pin1.x,
                          y = pin1.y - silk_pad['y'],
                          width = fab_mark / 2,
                          angle = 180,
                          line_width = silk_line,
                          layer = "F.SilkS"))
    
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
    
    # 3D model path
    library = param.get('library', default_lib)
    model_path = os.path.join('${KICAD6_3DMODEL_DIR}',
                              library+'.3dshapes',
                              param['name'] + '.wrl')
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
                        default='Connector_Samtec_RazorBeam',
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
