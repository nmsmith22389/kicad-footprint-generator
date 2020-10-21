#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools

from footprint_text_fields import addTextFields
import argparse
import yaml
from KicadModTree import *

series = 'M55-60'
series_long = 'Female Vertical Surface Mount Dual Row 1.27mm (0.05 inch) Pitch PCB Connector'
manufacturer = 'Harwin'
pitch = 1.27
datasheet = 'https://cdn.harwin.com/pdfs/M55-60X.pdf'
mpn = 'M55-60x{pincount:02g}42R'
padsize = [1.1, 0.8]

def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

def gen_footprint(pinnum, manpart, configuration):
    orientation_str = configuration['orientation_options']['V']
    footprint_name = configuration['fp_name_format_string'].format(
        man=manufacturer,
        series='',
        mpn=manpart,
        num_rows=2,
        pins_per_row=pinnum//2,
        mounting_pad="",
        pitch=pitch,
        orientation=orientation_str)
    footprint_name = footprint_name.replace('__','_')

    print(footprint_name)
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("{manufacturer} {series}, {mpn}{alt_mpn}, {pins_per_row} Pins per row ({datasheet}), generated with kicad-footprint-generator".format(
        manufacturer = manufacturer,
        series = series_long,
        mpn = manpart,
        alt_mpn = '',
        pins_per_row = pinnum,
        datasheet = datasheet))

    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry='vertical'))

    kicad_mod.setAttribute('smd')

    # Pads
    kicad_mod.append(PadArray(start=[ 5.5/2, -(pitch*(pinnum-2))/4], initial=2,
        pincount=pinnum//2, increment=2,  y_spacing=pitch, size=padsize,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT, drill=None))
    kicad_mod.append(PadArray(start=[-5.5/2, -(pitch*(pinnum-2))/4], initial=1,
        pincount=pinnum//2, increment=2,  y_spacing=pitch, size=padsize,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT, drill=None))

    # Holes
    kicad_mod.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                     at=[0, -(pitch*(pinnum))/4-1.575], size=[1.65, 1.65], drill=1.65, layers=Pad.LAYERS_NPTH))
    kicad_mod.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                      at=[0, (pitch*(pinnum))/4+1.575], size=[1.65, 1.65], drill=1.65, layers=Pad.LAYERS_NPTH))

    # Mounting pads
    kicad_mod.append(Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                     at=[2.45, -(pitch*(pinnum))/4-1.86], size=[2.7, 1.2], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                     at=[-2.45, -(pitch*(pinnum))/4-1.86], size=[2.7, 1.2], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                     at=[2.45, (pitch*(pinnum))/4+1.86], size=[2.7, 1.2], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                     at=[-2.45, (pitch*(pinnum))/4+1.86], size=[2.7, 1.2], layers=Pad.LAYERS_SMT))

    # Fab
    kicad_mod.append(RectLine(start=[-2.1, -(pitch*(pinnum))/4-1.86], end=[2.1, (pitch*(pinnum))/4+1.86], width=configuration['fab_line_width'], layer="F.Fab"))

    f_pin1 = [
        {'x': -2.1, 'y': -(pitch*(pinnum-2))/4+0.4},
        {'x': -1.7, 'y': -(pitch*(pinnum-2))/4},
        {'x': -2.1, 'y': -(pitch*(pinnum-2))/4-0.4},
    ]
    kicad_mod.append(PolygoneLine(polygone=f_pin1,
            width=configuration['fab_line_width'], layer="F.Fab"))

    # Draw pins to fab
    for y in range(0, pinnum//2):
        origy = -(pitch*(pinnum-2))/4 + y*pitch
        kicad_mod.append(RectLine(start=[-0.635-0.25, origy-0.25], end=[-0.635+0.25, origy+0.25], width=configuration['fab_line_width'], layer="F.Fab"))
        kicad_mod.append(RectLine(start=[ 0.635-0.25, origy-0.25], end=[ 0.635+0.25, origy+0.25], width=configuration['fab_line_width'], layer="F.Fab"))

    f_outline = [
        {'x': 1.5, 'y': -(pitch*(pinnum))/4 - 1},
        {'x': 1.5, 'y':  (pitch*(pinnum))/4 + 1},
        {'x': 0.1, 'y':  (pitch*(pinnum))/4 + 1},
        {'x': 0.1, 'y':  (pitch*(pinnum))/4 + 0.4},
        {'x':-1.5, 'y':  (pitch*(pinnum))/4 + 0.4},
        {'x':-1.5, 'y': -(pitch*(pinnum))/4 - 0.4},
        {'x': 0.1, 'y': -(pitch*(pinnum))/4 - 0.4},
        {'x': 0.1, 'y': -(pitch*(pinnum))/4 - 1},
        {'x': 1.5, 'y': -(pitch*(pinnum))/4 - 1},
    ]
    kicad_mod.append(PolygoneLine(polygone=f_outline,
            width=configuration['fab_line_width'], layer="F.Fab"))

    # SilkS
    silkslw = configuration['silk_line_width']

    kicad_mod.append(Line(start=[-3.65, -(pitch*(pinnum-2))/4-0.5], end=[-3.65, -(pitch*(pinnum+2))/4], layer='F.SilkS'))
    kicad_mod.append(Line(start=[-3.65, -(pitch*(pinnum-2))/4+0.5], end=[-3.65, (pitch*(pinnum+2))/4], layer='F.SilkS'))
    kicad_mod.append(Line(start=[3.65, +(pitch*(pinnum+2))/4], end=[3.65, -(pitch*(pinnum+2))/4], layer='F.SilkS'))

    s_pin1 = [
        {'x': -3.3 - (configuration['silk_pad_clearance']+configuration['silk_line_width']), 'y': -(pitch*(pinnum-2))/4},
        {'x': -3.7 - (configuration['silk_pad_clearance']+configuration['silk_line_width']), 'y': -(pitch*(pinnum-2))/4-0.4},
        {'x': -3.7 - (configuration['silk_pad_clearance']+configuration['silk_line_width']), 'y': -(pitch*(pinnum-2))/4+0.4},
        {'x': -3.3 - (configuration['silk_pad_clearance']+configuration['silk_line_width']), 'y': -(pitch*(pinnum-2))/4},
    ]
    kicad_mod.append(PolygoneLine(polygone=s_pin1,
            width=configuration['silk_line_width'], layer="F.SilkS"))

    # CrtYd
    cy_offset = configuration['courtyard_offset']['connector']
    cy_grid = configuration['courtyard_grid']
    bounding_box={
        'left':  -3.6,
        'right':  3.6,
        'top':   -(pitch*(pinnum))/4 - 2.54,
        'bottom': (pitch*(pinnum))/4 + 2.54,
    }
    cy_top = roundToBase(bounding_box['top'] - cy_offset, cy_grid)
    cy_bottom = roundToBase(bounding_box['bottom'] + cy_offset, cy_grid)
    cy_left = roundToBase(bounding_box['left'] - cy_offset, cy_grid)
    cy_right = roundToBase(bounding_box['right'] + cy_offset, cy_grid)
    poly_cy = [
        {'x': cy_left, 'y': cy_top},
        {'x': cy_right, 'y': cy_top},
        {'x': cy_right, 'y': cy_bottom},
        {'x': cy_left, 'y': cy_bottom},
        {'x': cy_left, 'y': cy_top},
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_cy,
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    # Text Fields
    body_edge={
        'left':  -3.6,
        'right':  3.6,
        'top':   -(pitch*(pinnum))/4 - 2.54,
        'bottom': (pitch*(pinnum))/4 + 2.54,
    }
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy_top, 'bottom':cy_bottom}, fp_name=footprint_name, text_y_inside_position='right', allow_rotation=True)

    # 3D model
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')
    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    # Output
    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)

def gen_family(configuration):
    for x in [12, 16, 20, 26, 32, 40, 50, 68, 80]:
        gen_footprint(x, mpn.format(pincount=x), configuration)

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

	gen_family(configuration)
