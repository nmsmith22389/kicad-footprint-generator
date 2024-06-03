#!/usr/bin/env python3

import sys
import os
#sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path

# export PYTHONPATH="${PYTHONPATH}<path to kicad-footprint-generator directory>"
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
import argparse
import yaml
from helpers import *
from KicadModTree import *

sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

series = "XA"
manufacturer = 'JST'
orientation = 'H'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eXA1.pdf'


silk_pin1_marker_type = 1
fab_pin1_marker_type = 3


pitch = 2.5
drill_size = 0.95 #Datasheet: 0.9 +0.1/-0
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15

hook_size = [2.8, 2]    #oval hole

# Connector Parameters
y_max = 9.2
y_min = y_max-12.6
y_main_min = y_max - 9.7    #plastic body extent behind row of pins

body_back_protrusion_width=1

variant_parameters = {
    '1': {
        'hook':True,
        'descr_str':', with hook'
        },
    '1N-BN': {
        'hook':False,
        'descr_str':''
        }
}
def generate_one_footprint(pincount, variant, configuration):
    A = (pincount - 1)*pitch
    B = A + 5
    x_min = (A-B)/2
    x_mid = A/2
    x_max = x_min + B

    silk_x_min = x_min - configuration['silk_fab_offset']
    silk_y_min = y_min - configuration['silk_fab_offset']
    silk_y_main_min = y_main_min - configuration['silk_fab_offset']
    silk_y_max = y_max + configuration['silk_fab_offset']
    silk_x_max = x_max + configuration['silk_fab_offset']

    pad_size = [pitch - pad_to_pad_clearance, drill_size + 2*pad_copper_y_solder_length]
    if pad_size[0] - drill_size < 2*min_annular_ring:
        pad_size[0] = drill_size + 2*min_annular_ring

    # Through-hole type shrouded header, Side entry type
    mpn = "S{n:02}B-XASK-{suff}".format(n=pincount,suff=variant)
    hook = variant_parameters[variant]['hook']

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pincount, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("JST {:s} series connector, {:s} ({:s}), generated with kicad-footprint-generator".format(series, mpn, datasheet))
    tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation])
    if hook:
        tags += ' hook'
    kicad_mod.setTags(tags)


    ########################### Silkscreen ################################
    tmp_x1=x_min+body_back_protrusion_width+configuration['silk_fab_offset']
    tmp_x2=x_max-body_back_protrusion_width-configuration['silk_fab_offset']
    pad_silk_offset = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    poly_silk_outline= [
                    {'x':-pad_size[0]/2.0-pad_silk_offset, 'y':silk_y_main_min},
                    {'x':tmp_x1, 'y':silk_y_main_min},
                    {'x':tmp_x1, 'y':silk_y_min},
                    {'x':silk_x_min, 'y':silk_y_min},
                    {'x':silk_x_min, 'y':silk_y_max},
                    {'x':silk_x_max, 'y':silk_y_max},
                    {'x':silk_x_max, 'y':silk_y_min},
                    {'x':tmp_x2, 'y':silk_y_min},
                    {'x':tmp_x2, 'y':silk_y_main_min},
                    {'x':(pincount-1)*pitch+pad_size[0]/2.0+pad_silk_offset, 'y':silk_y_main_min}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_silk_outline, layer='F.SilkS', width=configuration['silk_line_width']))

    if configuration['allow_silk_below_part'] == 'tht' or configuration['allow_silk_below_part'] == 'both':
        if hook:
            poly_big_cutout=[{'x':x_min+1, 'y':silk_y_max}
                                  ,{'x':x_min+1, 'y':silk_y_max - 2.3}
                                  ,{'x':(A/2)-1.6, 'y':silk_y_max - 2.3}]
            kicad_mod.append(PolygoneLine(polygone=poly_big_cutout, layer='F.SilkS', width=configuration['silk_line_width']))
            poly_big_cutout=[{'x':(A/2)+1.6, 'y':silk_y_max-2.3}
                                  ,{'x':x_max-1, 'y':silk_y_max - 2.3}
                                  ,{'x':x_max-1, 'y':silk_y_max}]
        else:
            poly_big_cutout=[{'x':x_min+1, 'y':silk_y_max}
                                  ,{'x':x_min+1, 'y':silk_y_max - 2.3}
                                  ,{'x':x_max-1, 'y':silk_y_max - 2.3}
                                  ,{'x':x_max-1, 'y':silk_y_max}]
        kicad_mod.append(PolygoneLine(polygone=poly_big_cutout, layer='F.SilkS', width=configuration['silk_line_width']))


        #locking "dimple", centered
        if pincount == 2:
            dimple_w = 0.8
        else:
            dimple_w = 1.6
        dimple_h = 1.8
        dimple_y = y_max - 4.9  #middle of the dimple
        kicad_mod.append(RectLine(start=[(A-dimple_w)/2, dimple_y + dimple_h/2], end=[(A+dimple_w)/2, dimple_y - dimple_h/2],
            layer='F.SilkS', width=configuration['silk_line_width']))

        # top
        if pincount == 2:
            recess = 3.2
        elif pincount == 3:
            recess = 4.8
        else:
            recess = 5.4
        mid = 2.1
        cutout = 1.1
        wall = (mid - cutout)/2
        polygons = [[
            {'x': x_mid + recess/2, 'y': silk_y_max - 2.3},
            {'x': x_mid + recess/2, 'y': 2},
            {'x': x_mid + recess/2 + wall, 'y': 2},
            {'x': x_mid + recess/2 + wall, 'y': silk_y_max - 3.9},
            {'x': x_mid + recess/2 + wall + cutout, 'y': silk_y_max - 3.9},
            {'x': x_mid + recess/2 + wall + cutout, 'y': 2},
            {'x': silk_x_max, 'y': 2},
            ], [
            {'x': x_mid - recess/2, 'y': silk_y_max - 2.3},
            {'x': x_mid - recess/2, 'y': 2},
            {'x': x_mid - recess/2 - wall, 'y': 2},
            {'x': x_mid - recess/2 - wall, 'y': silk_y_max - 3.9},
            {'x': x_mid - recess/2 - wall - cutout, 'y': silk_y_max - 3.9},
            {'x': x_mid - recess/2 - wall - cutout, 'y': 2},
            {'x': silk_x_min, 'y': 2},
            ]]
        if pincount >= 6:
            side = 2.3
            polygons[0][-1:] = [
                {'x': x_mid + recess/2 + mid, 'y': 2},
                {'x': x_mid + recess/2 + mid, 'y': silk_y_max - 2.3},
                ]
            polygons[1][-1:] = [
                {'x': x_mid - recess/2 - mid, 'y': 2},
                {'x': x_mid - recess/2 - mid, 'y': silk_y_max - 2.3},
                ]
            polygons.append([
                {'x': x_max - side, 'y': silk_y_max - 2.3},
                {'x': x_max - side, 'y': 2},
                {'x': silk_x_max, 'y': 2},
                ])
            polygons.append([
                {'x': x_min + side, 'y': silk_y_max - 2.3},
                {'x': x_min + side, 'y': 2},
                {'x': silk_x_min, 'y': 2},
                ])
        for poly in polygons:
            kicad_mod.append(PolygoneLine(polygone = poly,
                layer='F.SilkS', width=configuration['silk_line_width']))

    ########################### CrtYd ################################
    part_x_min = x_min
    part_x_max = x_max
    part_y_min = y_min
    part_y_max = y_max
    offset = configuration['courtyard_offset']['connector']
    grid = configuration['courtyard_grid']

    cx1 = roundToBase(part_x_min - offset, grid)
    cy1 = roundToBase(part_y_min - offset, grid)

    cx2 = roundToBase(part_x_max + offset, grid)
    cy2 = roundToBase(part_y_max + offset, grid)

    cx3 = roundToBase(part_x_max - body_back_protrusion_width - offset, grid)
    cy3 = roundToBase(-pad_size[1]/2 - offset, grid)

    cx4 = roundToBase(part_x_min + body_back_protrusion_width + offset, grid)

    kicad_mod.append(PolygoneLine(polygone=[
            {'x':cx1, 'y':cy1},
            {'x':cx1, 'y':cy2},
            {'x':cx2, 'y':cy2},
            {'x':cx2, 'y':cy1},
            {'x':cx3, 'y':cy1},
            {'x':cx3, 'y':cy3},
            {'x':cx4, 'y':cy3},
            {'x':cx4, 'y':cy1},
            {'x':cx1, 'y':cy1},
            ],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ########################### Fab Outline ################################
    tmp_x1=x_min+body_back_protrusion_width
    tmp_x2=x_max-body_back_protrusion_width
    poly_fab_outline= [
                    {'x':tmp_x1, 'y':y_main_min},
                    {'x':tmp_x1, 'y':y_min},
                    {'x':x_min, 'y':y_min},
                    {'x':x_min, 'y':y_max},
                    {'x':x_max, 'y':y_max},
                    {'x':x_max, 'y':y_min},
                    {'x':tmp_x2, 'y':y_min},
                    {'x':tmp_x2, 'y':y_main_min},
                    {'x':tmp_x1, 'y':y_main_min}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_fab_outline, layer='F.Fab', width=configuration['fab_line_width']))

    ############################# Pads ##################################
    optional_pad_params = {}
    if configuration['kicad4_compatible']:
        optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_RECT
    else:
        optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(initial=1, start=[0, 0],
        x_spacing=pitch, pincount=pincount,
        size=pad_size, drill=drill_size,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        **optional_pad_params))

    #add mounting hole for hook
    if hook:
        kicad_mod.append(Pad(at={'x': A/2, 'y': 6.5}, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_NPTH,
            drill=hook_size, size=hook_size))

    ########################### Pin 1 marker ################################
    poly_pin1_marker = [
        {'x':0, 'y':-1.2},
        {'x':-0.4, 'y':-1.6},
        {'x':0.4, 'y':-1.6},
        {'x':0, 'y':-1.2}
    ]
    if silk_pin1_marker_type == 1:
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker, layer='F.SilkS', width=configuration['silk_line_width']))
    if silk_pin1_marker_type == 2:
        silk_pin1_marker_t2_x = -pad_size[0]/2.0-pad_silk_offset

        kicad_mod.append(Line(start=[silk_pin1_marker_t2_x, silk_y_main_min],
            end=[silk_pin1_marker_t2_x, -pad_size[1]/2.0-configuration['silk_pad_clearance']],layer='F.SilkS', width=configuration['silk_line_width']))

    if fab_pin1_marker_type == 1:
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 2:
        poly_pin1_marker_type2 = [
            {'x':-0.75, 'y':y_main_min},
            {'x':0, 'y':y_main_min+0.75},
            {'x':0.75, 'y':y_main_min}
        ]
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker_type2, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 3:
        fab_pin1_marker_t3_y = pad_size[1]/2.0
        poly_pin1_marker_type2 = [
            {'x':0, 'y':fab_pin1_marker_t3_y},
            {'x':-0.5, 'y':fab_pin1_marker_t3_y+0.5},
            {'x':0.5, 'y':fab_pin1_marker_t3_y+0.5},
            {'x':0, 'y':fab_pin1_marker_t3_y}
        ]
        kicad_mod.append(PolygoneLine(polygone=poly_pin1_marker_type2, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    text_center_y = 2.5
    body_edge={'left':part_x_min, 'right':part_x_max, 'top':part_y_min, 'bottom':part_y_max}
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position=text_center_y)


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

    for variant in variant_parameters:
        for pincount in range(2,14+1):
            generate_one_footprint(pincount, variant, configuration)
