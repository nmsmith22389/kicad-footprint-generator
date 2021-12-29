#!/usr/bin/env python3
# coding: utf8
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
from footprint_keepout_area import addRectangularKeepout

# x position mounting inner mounting pad edge relative to nearest pad center
center_pad_to_mounting_pad_edge = 1
# y dimensions for pad given relative to mounting pad edge
rel_pad_y_outside_edge = 4.5
rel_pad_y_inside_edge = 3.3
pad_size_x = 0.3
# y position for body edge relative to mounting pad edge (positive -> body extends outside bounding box)
rel_body_edge_y = 1.4
body_size_y = 5
# body_fin_protrusion: 1.6
# body_fin_width: 0.8
# x body edge relative to nearest pin
rel_body_edge_x = 2.40


pitch = 0.5
pad_size = [pad_size_x, rel_pad_y_outside_edge - rel_pad_y_inside_edge]
mp_size = [1.6, 2.4] #L shape, first min val, second max value

def generate_footprint(pins_per_row_range, configuration, part_code): 
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(pins_per_row, configuration, part_code)

def generate_one_footprint(pins, configuration,part_code):
    series = ""
    series_long = '62684, FFC/FPC connector'
    manufacturer = 'Amphenol'
    orientation = 'H'
    number_of_rows = 1    
    conn_category = "Amphenol"    
    lib_by_conn_category = True
    datasheet = 'https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/62684.pdf'
    mpn = part_code.format(n=pins)
    pad_silk_off = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    off = configuration['silk_fab_offset']
    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "-1MP",
        pitch=pitch, orientation=orientation_str)

    footprint_name = footprint_name.replace("__",'_')

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setAttribute('smd')
    kicad_mod.setDescription("Amphenol {:s}, {:s}, {:d} Pins per row ({:s}), generated with kicad-footprint-generator".format(series_long, mpn, pins, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    A = (pins - 1) * pitch
    B = A + 2*rel_body_edge_x
    pad_y = -rel_pad_y_outside_edge/2 + pad_size[1]/2
    mpad_y = rel_pad_y_inside_edge/2 - (rel_pad_y_outside_edge-rel_pad_y_inside_edge)/2
    mpad_x = A/2 + center_pad_to_mounting_pad_edge + 2*pad_size_x

    kicad_mod.append(Pad(number=configuration['mounting_pad_number'], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                        at=[mpad_x, mpad_y], size=mp_size, layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                        at=[mpad_x+(mp_size[1]-mp_size[0])/2, mpad_y+(mp_size[1]-mp_size[0])/2], size=[mp_size[1]	,mp_size[0]], layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                        at=[-mpad_x, mpad_y], size=mp_size, layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=configuration['mounting_pad_number'], type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                        at=[-mpad_x-(mp_size[1]-mp_size[0])/2, mpad_y+(mp_size[1]-mp_size[0])/2], size=[mp_size[1],mp_size[0]], layers=Pad.LAYERS_SMT))
    # create pads
    #createNumberedPadsTHT(kicad_mod, pincount, pitch, drill, {'x':x_dia, 'y':y_dia})
    kicad_mod.append(PadArray(center=[0,pad_y], pincount=pins, x_spacing=pitch,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=pad_size, layers=Pad.LAYERS_SMT))

    x1 = -B/2
    x2 = x1 + B
    y2 = mpad_y + mp_size[1]/2 + rel_body_edge_y
    y1 = y2 - body_size_y

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }

    bounding_box = body_edge.copy()
    bounding_box['top'] = pad_y - pad_size[1]/2
    bb_x = mpad_x + mp_size[1]/2
    if  bb_x > x2:
        bounding_box['left'] = -bb_x
        bounding_box['right'] = bb_x


    main_body_bottom = body_edge['top'] + 4.2
    gap_body_hatch = 0.3
    gab_body_hatch_depth = 0.6
    hatch_reduced_width = -1.2

    poly_outline = [
        {'x': 0, 'y':  body_edge['top']},
        {'x': body_edge['left'], 'y':  body_edge['top']},
        {'x': body_edge['left'], 'y':  main_body_bottom},
        {'x': body_edge['left'] + gab_body_hatch_depth, 'y':  main_body_bottom},
        {'x': body_edge['left'] + gab_body_hatch_depth, 'y':  main_body_bottom + gap_body_hatch},
        {'x': body_edge['left'] + hatch_reduced_width/2, 'y':  main_body_bottom + gap_body_hatch},
        {'x': body_edge['left'] + hatch_reduced_width/2, 'y':  body_edge['bottom']},
        {'x': 0, 'y':  body_edge['bottom']}
    ]
    kicad_mod.append(PolygoneLine(
        polygone=poly_outline,
        layer='F.Fab', width=configuration['fab_line_width']))
    kicad_mod.append(PolygoneLine(
        polygone=poly_outline, x_mirror = 0.0000000001,
        layer='F.Fab', width=configuration['fab_line_width']))

    #line offset
    off = 0.1

    #x1 = -(mpad_x+(mp_size[1]-mp_size[0])/2+mp_size[1]/2) - off
    x1 -= off
    y1 -= off

    #x2 = (mpad_x+(mp_size[1]-mp_size[0])/2+mp_size[1]/2) + off
    x2 += off
    y2 = main_body_bottom + gap_body_hatch - off

    x3 = x1+hatch_reduced_width/2
    x4 = x2-hatch_reduced_width/2
    y4 = main_body_bottom + off + mp_size[0]/2
    x5 = x1+gab_body_hatch_depth
    x6 = x2-gab_body_hatch_depth

    #draw the main outline around the footprint
    silk_pad_x_left = -A/2 - pad_size[0]/2 - pad_silk_off
    silk_mp_top = mpad_y - mp_size[1]/2 - pad_silk_off
    silk_mp_bottom = mpad_y + mp_size[1]/2 + pad_silk_off
    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': silk_pad_x_left,'y':y1},
            {'x': x1,'y':y1},
            {'x': x1,'y':silk_mp_top}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': -silk_pad_x_left,'y':y1},
            {'x': x2,'y':y1},
            {'x': x2,'y':silk_mp_top}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygoneLine(
        polygone=[
            {'x': x1,'y':silk_mp_bottom},
            {'x': x1,'y':y2},            
            {'x': x5,'y':y2},
            {'x': x3,'y':y2},
            {'x': x3,'y':y4},
            {'x': x4,'y':y4},
            {'x': x4,'y':y2},
            {'x': x6,'y':y2},
            {'x': x2,'y':y2},
            {'x': x2,'y':silk_mp_bottom},

        ],
        layer='F.SilkS', width=configuration['silk_line_width']))


    #add pin-1 marker

    kicad_mod.append(Line(
        start=[silk_pad_x_left, y1], end=[silk_pad_x_left, pad_y - pad_size[1]/2],
                layer='F.SilkS', width=configuration['silk_line_width']))

    sl=1
    pin = [
        {'y': body_edge['top'], 'x': -A/2-sl/2},
        {'y': body_edge['top'] + sl/sqrt(2), 'x': -A/2},
        {'y': body_edge['top'], 'x': -A/2+sl/2}
    ]
    kicad_mod.append(PolygoneLine(polygone=pin,
        width=configuration['fab_line_width'], layer='F.Fab'))


    ########################### KEEPOUT #################################

    # k_top = pad_y + pad_size[1]/2 + 0.1
    # k_size = [A + pad_size[0], 2.37]
    # addRectangularKeepout(kicad_mod, [0, k_top+k_size[1]/2], k_size)


    ########################### CrtYd #################################
    cx1 = roundToBase(bounding_box['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = roundToBase(bounding_box['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = roundToBase(bounding_box['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = roundToBase(bounding_box['bottom'] + configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(RectLine(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='bottom')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')


    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
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
            configuration = yaml.load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)
    generate_footprint([32,34,36,40,43,45,50], configuration, "62684-{n:d}2100ALF")
    generate_footprint([55,57], configuration, "62684-{n:d}21N0ALF")
    generate_footprint([40,45,50], configuration, "62684-{n:d}2100AHLF")
    generate_footprint([50], configuration, "62684-{n:d}21C0AHLF")
    generate_footprint([45], configuration, "62684-{n:d}2160AHLF")
    generate_footprint([32,34,36,40,43,45,50], configuration, "62684-{n:d}210ALF")
    generate_footprint([55,57], configuration, "62684-{n:d}21NALF")
    generate_footprint([40,45,50], configuration, "62684-{n:d}210AHLF")
    generate_footprint([40,45,50], configuration, "62684-{n:d}212AHLF")
    generate_footprint([50], configuration, "62684-{n:d}21CAHLF")
    generate_footprint([45], configuration, "62684-{n:d}216AHLF")
    generate_footprint([32,38,40,45,50], configuration, "62684-{n:d}1100ALF")
    generate_footprint([55,57,60], configuration, "62684-{n:d}11N0ALF")
    generate_footprint([45,50], configuration, "62684-{n:d}1100AHLF")
    generate_footprint([55,57,60], configuration, "62684-{n:d}11N0AHLF")
    generate_footprint([45], configuration, "62684-{n:d}1160AHLF")
    generate_footprint([50], configuration, "62684-{n:d}1170AHLF")
    generate_footprint([32,38,40,45,50], configuration, "62684-{n:d}110ALF")
    generate_footprint([55,57,60], configuration, "62684-{n:d}11NALF")
    generate_footprint([45,50], configuration, "62684-{n:d}110AHLF")
    generate_footprint([55,57,60], configuration, "62684-{n:d}11NAHLF")
    generate_footprint([45], configuration, "62684-{n:d}116AHLF")
    generate_footprint([50], configuration, "62684-{n:d}117AHLF")