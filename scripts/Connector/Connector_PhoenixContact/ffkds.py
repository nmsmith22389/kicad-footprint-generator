#!/usr/bin/env python3

import sys
import os
from helpers import *
import re
import fnmatch
import argparse
import yaml
sys.path.append(os.path.join(sys.path[0], "..", "..", "..")) # load KicadModTree path
from KicadModTree import *
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools")) # load parent path of tools
from footprint_text_fields import addTextFields
from ffkds_params import seriesParams, dimensions, generate_description, all_params

def generate_one_footprint(model, params, configuration):

    pitch_mpn = ''
    if params.pin_pitch == 2.54:
        pitch_mpn = '-2,54'
    elif params.pin_pitch == 3.81:
        pitch_mpn = '-3,81'
    elif params.pin_pitch == 5.08:
        pitch_mpn = '-5,08'
    elif params.pin_pitch == 7.62:
        pitch_mpn = '-7,62'
    lib_name = configuration['lib_name_format_str'].format(series='FFKDS', suffix='')
    mpn = configuration['mpn_format_string_no_rating'].format(subseries=params.subseries, style=params.style, num_pins=params.num_pins, pitch=pitch_mpn)
    footprint_name = configuration['fp_name_format_string'].format(man = configuration['manufacturer'], series='FFKDS', mpn=mpn, num_rows=1,
        num_pins = params.num_pins, mounting_pad = "", pitch = params.pin_pitch,
        orientation = configuration['orientation_str'][1] if params.angled else configuration['orientation_str'][0],
        flanged = configuration['flanged_str'][0], mount_hole = configuration['mount_hole_str'][0])

    length, width, upper_to_pin, left_to_pin, inner_len = dimensions(params)

    body_top_left=[left_to_pin,upper_to_pin]
    body_bottom_right=v_add(body_top_left,[length,width])

    body_edge={
        'left': body_top_left[0],
        'top': body_top_left[1],
        'right': body_bottom_right[0],
        'bottom': body_bottom_right[1],
    }

    silk_top_left=v_offset(body_top_left, configuration['silk_fab_offset'])
    silk_bottom_right=v_offset(body_bottom_right, configuration['silk_fab_offset'])

    center_x = (params.num_pins-1)/2.0*params.pin_pitch
    kicad_mod = Footprint(footprint_name, FootprintType.THT)

    mpn = configuration['mpn_format_string_description_no_rating'].format(subseries=params.subseries, style=params.style, num_pins=params.num_pins, pitch=pitch_mpn)
    kicad_mod.setDescription(generate_description(params, mpn))
    kicad_mod.setTags(configuration['keywords_format_string'].format(mpn=mpn, param_name=model, order_info = ', '.join(params.order_info)))


    ################################################# Pads #################################################
    optional_pad_params = {}
    if configuration['kicad4_compatible']:
        optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_RECT
    else:
        optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(initial=1, start=[0, 0],
        x_spacing=params.pin_pitch, pincount=params.num_pins,
        size=[params.pin_Sx, params.pin_Sy], drill=seriesParams.drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=configuration['pin_layers'],
        **optional_pad_params))
        
    kicad_mod.append(PadArray(initial=1, start=[0, 5.08 if params.pin_pitch == 2.54 else 7.62],
        x_spacing=params.pin_pitch, pincount=params.num_pins,
        size=[params.pin_Sx, params.pin_Sy], drill=seriesParams.drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=configuration['pin_layers'],
        **optional_pad_params))

    ################################################# Silk and Fab #################################################
    kicad_mod.append(RectLine(start=silk_top_left, end=silk_bottom_right, layer='F.SilkS', width=configuration['silk_line_width']))
    if configuration['with_fab_layer']:
        kicad_mod.append(RectLine(start=body_top_left, end=body_bottom_right, layer='F.Fab', width=configuration['fab_line_width']))
    if params.angled:
        lock_poly=[
            {'x':-1, 'y':0},
            {'x':1, 'y':0},
            {'x':1.5/2, 'y':-1.5},
            {'x':-1.5/2, 'y':-1.5},
            {'x':-1, 'y':0}
        ]
        lock_poly_fab=[
            {'x':-1, 'y':-configuration['silk_fab_offset']},
            {'x':1, 'y':-configuration['silk_fab_offset']},
            {'x':1.5/2, 'y':-1.5},
            {'x':-1.5/2, 'y':-1.5},
            {'x':-1, 'y':-configuration['silk_fab_offset']}
        ]

        for i in range(params.num_pins):
            lock_translation = Translation(i*params.pin_pitch + ((params.pin_pitch/2 + left_to_pin) if params.pin_pitch <= 3.81 else (3.81/2 + left_to_pin)), silk_bottom_right[1])
            lock_translation.append(PolygonLine(polygon=lock_poly, layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['inner_details_on_fab']:
                lock_translation.append(PolygonLine(polygon=lock_poly_fab, layer='F.Fab', width=configuration['fab_line_width']))
            kicad_mod.append(lock_translation)

    else:
    
        # line1 y not exact TODO
        line1=[
            {'x': silk_top_left[0], 'y': silk_bottom_right[1] / 2},
            {'x': silk_bottom_right[0], 'y': silk_bottom_right[1] / 2}
        ]
        kicad_mod.append(PolygonLine(polygon=line1, layer='F.SilkS', width=configuration['silk_line_width']))
        
        line2=[
            {'x': silk_top_left[0], 'y': silk_bottom_right[1] - 0.5},
            {'x': silk_bottom_right[0], 'y': silk_bottom_right[1] - 0.5}
        ]
        kicad_mod.append(PolygonLine(polygon=line2, layer='F.SilkS', width=configuration['silk_line_width']))
        
        for i in range(params.num_pins):
            lock_translation = Translation(silk_top_left[0] + params.pin_pitch * i, 0)
            lock_translation.append(RectLine(start=[0, silk_top_left[1]], end=[params.pin_pitch, 0] , layer='F.SilkS', width=configuration['silk_line_width']))
            lock_translation.append(Circle(center=[params.pin_pitch / 2, 2.015], radius=1.5, layer='F.SilkS', width=configuration['silk_line_width']))
            if configuration['inner_details_on_fab']:
                lock_translation.append(Circle(center=[0, 2.015], radius=1.5, layer='F.Fab', width=configuration['silk_line_width']))
            kicad_mod.append(lock_translation)

    ################################################## Courtyard ##################################################
    crtyd_top_left=v_offset(body_top_left, configuration['courtyard_offset']['connector'])
    crtyd_bottom_right=v_offset(body_bottom_right, configuration['courtyard_offset']['connector'])
    kicad_mod.append(RectLine(start=round_crty_point(crtyd_top_left, configuration['courtyard_grid']), end=round_crty_point(crtyd_bottom_right, configuration['courtyard_grid']), layer='F.CrtYd'))

    ################################################# Text Fields #################################################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':crtyd_top_left[1], 'bottom':crtyd_bottom_right[1]}, fp_name=footprint_name, text_y_inside_position='top')

    ################################################# Pin 1 Marker #################################################
    y_bottom_silk_marker = (silk_top_left[1] if silk_top_left[1] < -params.pin_Sy/2 else -params.pin_Sy/2) - 0.2
    kicad_mod.append(PolygonLine(polygon=create_pin1_marker_triangle(y_bottom_silk_marker), layer='F.SilkS', width=configuration['silk_line_width']))
    if configuration['with_fab_layer']:
        kicad_mod.append(PolygonLine(polygon=create_pin1_marker_triangle(bottom_y = -0.5, dimensions = [1.5, -body_top_left[1]-0.5], with_top_line = False),
            layer='F.Fab', width=configuration['fab_line_width']))
    
    #################################################### 3d file ###################################################
    p3dname = '{prefix:s}{lib_name:s}.3dshapes/{fp_name}.wrl'.format(prefix = configuration.get('3d_model_prefix', '${KISYS3DMOD}/'), lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=p3dname, at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

    file_handler = KicadFileHandler(kicad_mod)
    out_dir = '{:s}.pretty/'.format(lib_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    file_handler.writeFile('{:s}.pretty/{:s}.kicad_mod'.format(lib_name, footprint_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='config_phoenix_KLCv3.0.yaml')
    parser.add_argument('--model_filter', type=str, nargs='?', help='define a filter for what should be generated.', default="*")
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

    model_filter_regobj=re.compile(fnmatch.translate(args.model_filter))
    for model, params in all_params.items():
        if model_filter_regobj.match(model):
            generate_one_footprint(model, params, configuration)
