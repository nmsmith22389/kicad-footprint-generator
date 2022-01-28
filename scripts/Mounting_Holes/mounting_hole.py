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


import sys
import os
import re
import argparse
import yaml
import math

sys.path.append(os.path.join(sys.path[0], "..", ".."))  # load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0],"..","kicad_mod")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path

from KicadModTree import *

lib_name = 'MountingHole'
#during test
lib_name = 'KKKKK'

# Metric standart hole size for screws assembly
# https://cdn.standards.iteh.ai/samples/4183/1a8db2e6de054d2e9bed7d40be64d6e1/ISO-273-1979.pdf
ISO273 = {
                    # drill   nominal, fine, medium, coarse

          "M1.6":     {"drill":  ( 1.6,  1.7,  1.8,  2.0)  , "vias": (6,  0.3)},
          "M2.0":     {"drill":  ( 2.0,  2.2,  2.4,  2.6)  , "vias": (6,  0.4)},
          "M2.5":     {"drill":  ( 2.5,  2.7,  2.9,  3.1)  , "vias": (6,  0.4)},
          "M3.0":     {"drill":  ( 3.0,  3.2,  3.4,  3.6)  , "vias": (6,  0.6)},
          "M3.5":     {"drill":  ( 3.5,  3.7,  3.9,  4.2)  , "vias": (8,  0.6)},
          "M4.0":     {"drill":  ( 4.0,  4.3,  4.5,  4.8)  , "vias": (8,  0.8)},
          "M5.0":     {"drill":  ( 5.0,  5.3,  5.5,  5.8)  , "vias": (8,  1.0)},
          "M6.0":     {"drill":  ( 6.0,  6.4,  6.6,  7.0)  , "vias": (12, 1.1)},
          "M8.0":     {"drill":  ( 8.0,  8.4,  9.0, 10.0)  , "vias": (12, 1.4)},
         "M10.0":     {"drill":  (10.0, 10.5, 11.0, 12.0)  , "vias": (12, 1.5)},
}

drill_nom    = 0
drill_fine   = 1
drill_medium = 2
drill_coarse = 3
drill_type   = drill_medium                         # <== choose here what drill size for the hole

#Torx screws, this is the Head diameter that presses on the pcb
ISO14580 = {"data":[

    {  "Name": "M1.6",     "size":  3.0 },   # this one is not normalized
    {  "Name": "M2.0",     "size":  3.8 },
    {  "Name": "M2.5",     "size":  4.5 },
    {  "Name": "M3.0",     "size":  5.5 },
   #{  "Name": "M3.5",     "size":  6.0 },   # not recommended
    {  "Name": "M4.0",     "size":  7.0 },
    {  "Name": "M5.0",     "size":  8.5 },
    {  "Name": "M6.0",     "size": 10.0 },
    {  "Name": "M8.0",     "size": 13.0 },
    {  "Name": "M10.0",    "size": 16.0 }
               ],
    "dataSheet":  "https://www.newfastener.com/wp-content/uploads/2013/03/ISO-14580.pdf",
    "Description":"ISO-14580, ISO-1207, ISO-4762, DIN-82"
    }

#Hexagonal screws with collar
ISO7380_1 = {"data":[

    {  "Name": "M3.0",     "size":  5.7 },
    {  "Name": "M4.0",     "size":  7.6 },
    {  "Name": "M5.0",     "size":  9.5 },
    {  "Name": "M6.0",     "size": 10.5 },
    {  "Name": "M8.0",     "size": 14.0 },
    {  "Name": "M10.0",    "size": 17.5 }
                    ],
    "dataSheet":  "https://cdn.standards.iteh.ai/samples/53671/84df01c5fcce4a91896ac3b0c55ca128/ISO-7380-1-2011.pdf",
    "Description":"ISO-7380, ISO-7380-1"
    }

#Hexagonal screws with larger collar
ISO7380_2 = {"data":[

    {  "Name": "M3.0",     "size":  6.9 },
    {  "Name": "M4.0",     "size":  9.4 },
    {  "Name": "M5.0",     "size": 11.8 },
    {  "Name": "M6.0",     "size": 13.6 },
    {  "Name": "M8.0",     "size": 17.8 },
    {  "Name": "M10.0",    "size": 21.9 }
                    ],
    "dataSheet":  "https://cdn.standards.iteh.ai/samples/53672/801ec2c66dfc4359ba76493e3d01d97f/ISO-7380-2-2011.pdf",
    "Description":"ISO-7380-2"
    }

screws = [ISO14580, ISO7380_1]  #ISO73380_2


# https://stackoverflow.com/questions/4265546/python-round-to-nearest-05
def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int(n/precision+correction) * precision

def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

#
# function from the original script, place Via along a circle
# This function is a good candidate de be move in KiCadModTree
# via_count : number of via to create
# via_diameter
# x_size, y size : ovale to follow (circle when x=y)
#
def  doAnnularVia(via_count, via_diameter, x_size, y_size):

    circle_radius = min(x_size, y_size) / 2
    circle_scope = min(x_size, y_size) * math.pi

    if x_size > y_size:
        line_scope_x = 2 * (x_size - y_size)
        line_scope_y = 0
    else:
        line_scope_x = 0
        line_scope_y = 2 * (y_size - x_size)
    line_scope = line_scope_x + line_scope_y
    vias_scope = circle_scope + line_scope

    for step in range(via_count):
        scope_step = (vias_scope / via_count * step - line_scope_y / 4 + vias_scope) % vias_scope # align on right center

        if scope_step <= circle_scope / 4:
            local_scope_pos = scope_step
            circle_pos = local_scope_pos / circle_scope * 2 * math.pi
            step_x = math.cos(circle_pos) * circle_radius + line_scope_x / 4
            step_y = math.sin(circle_pos) * circle_radius + line_scope_y / 4
        elif scope_step <= circle_scope / 4 + line_scope_x / 2:
            local_scope_pos = scope_step - circle_scope / 4
            step_x = line_scope_x / 4 - local_scope_pos
            step_y = y_size / 2
        elif scope_step <= circle_scope / 2 + line_scope_x / 2:
            local_scope_pos = scope_step - line_scope_x / 2  # angle of circle already included
            circle_pos = local_scope_pos / circle_scope * 2 * math.pi
            step_x = math.cos(circle_pos) * circle_radius - line_scope_x / 4
            step_y = math.sin(circle_pos) * circle_radius + line_scope_y / 4
        elif scope_step <= circle_scope / 2 + line_scope_x / 2 + line_scope_y / 2:
            local_scope_pos = scope_step - circle_scope / 2 - line_scope_x / 2
            step_x = -x_size / 2
            step_y = line_scope_y / 4 - local_scope_pos
        elif scope_step <= 3 * circle_scope / 4 + line_scope_x / 2 + line_scope_y / 2:
            local_scope_pos = scope_step - line_scope_x / 2 -  line_scope_y / 2
            circle_pos = local_scope_pos / circle_scope * 2 * math.pi
            step_x = math.cos(circle_pos) * circle_radius - line_scope_x / 4
            step_y = math.sin(circle_pos) * circle_radius - line_scope_y / 4
        elif scope_step <= 3 * circle_scope / 4 + line_scope_x + line_scope_y / 2:
            local_scope_pos = scope_step - 3 * circle_scope / 4 - line_scope_x / 2 - line_scope_y / 2
            step_x = -line_scope_x / 4 + local_scope_pos
            step_y = -y_size / 2
        elif scope_step <= circle_scope + line_scope_x + line_scope_y / 2:
            local_scope_pos = scope_step - line_scope_x - line_scope_y / 2  # angle of circle already included
            circle_pos = local_scope_pos / circle_scope * 2 * math.pi
            step_x = math.cos(circle_pos) * circle_radius + line_scope_x / 4
            step_y = math.sin(circle_pos) * circle_radius - line_scope_y / 4
        elif scope_step < circle_scope + line_scope_x + line_scope_y:
            local_scope_pos = scope_step - circle_scope - line_scope_x - line_scope_y / 2
            step_x = x_size / 2
            step_y = -line_scope_y / 4 + local_scope_pos
        else: # error
            raise "invalid scope_step"

        kicad_mod.append(Pad(number='',
                             type=Pad.TYPE_THT,
                             shape=Pad.SHAPE_CIRCLE,
                             at=[step_x, step_y],
                             size=[via_diameter+0.3, via_diameter+0.3],
                             drill=via_diameter,
                             layers=['*.Cu', '*.Mask']
                             ))


def create_pad(configuration, kicad_mod, holeType, holeSize, padSize ):

    nudge = configuration['silk_fab_offset']
    silk_w = configuration['silk_line_width']
    fab_w = configuration['fab_line_width']

    #    TYPE_THT     = 'thru_hole'
    #    TYPE_SMT     = 'smd'
    #    TYPE_CONNECT = 'connect'
    #    TYPE_NPTH    = 'np_thru_hole'

    # Default NPTH (basic hole with no copper)
    myPad = Pad(
        number= "",
        type  = Pad.TYPE_NPTH,
        shape = Pad.SHAPE_CIRCLE,
        clearance = 0,
        at    = [0, 0],
        size  = [0.00000000001, 0.00000000001], #bug somewhere, no way to set that to zero
        drill = holeSize,
        #layers = ['*.Cu', '*.Mask'],
        #layers = ['*.Cu']
        #layers = ['*.Mask']
        layers = ['']
    )

    # Silk screen circle & courtyard around the screw head
    radius = padSize/2 + nudge
    kicad_mod.append(  Circle( center=[0, 0], radius=radius, layer='F.SilkS'))
    radius = roundToBase( radius + silk_w, configuration['courtyard_grid'])
    kicad_mod.append(  Circle( center=[0, 0], radius=radius, layer='F.CrtYd'))

    if holeType == '':
        # For hole with no copper, set a clearance that extands to the
        # courtyard. This protect from zone filling
        myPad.clearance = radius-holeSize/2
        kicad_mod.append(myPad)
        return # nothing more to do for NPTH


    # We have a Pad, one or both sides ?
    #myPad.size = [padSize, padSize] # this syntax is refused
    myPad.size[0] = padSize
    myPad.size[1] = padSize
    #myPad.type = Pad.TYPE_THT

    if holeType == '1PAD':
        myPad.layers = ['F.Cu', 'F.Mask']

    if re.match ('2PAD', holeType):
        myPad.layers = ['*.Cu', '*.Mask']
        myPad.type = Pad.TYPE_THT       # only biface are really THT

    kicad_mod.append(myPad)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use config .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?',
                         help='the config file defining how the footprint will look like. (KLC)',
                         default='../tools/global_config_files/config_KLCv3.0.yaml'
                       )
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)


    #for each Screw type, generate footprint
    for screw in screws:

        for screew_sizes  in screw["data"]:

            for variant in ('', '1PAD', '2PAD', '2PAD+V'):

                N = screew_sizes['Name']
                #print ("Name=", variant, N, "\n")

                footprint_name = '{n:s}_{sz:2.1f}mm_{var}'.format( n = N, sz=screew_sizes["size"], var=variant)
                footprint_name = re.sub ('_$', '', footprint_name)
                kicad_mod = Footprint(footprint_name)

                # init kicad footprint
                Description = '{des:s} (datasheet:{sheet:s})'.format (des=screw["Description"], 
                                                                    sheet=screw["dataSheet"])
                kicad_mod.setDescription(Description)
                kicad_mod.setTags('Mounting Hole')
                kicad_mod.setTags('through_hole')

                # insert the hole and the Pad
                create_pad(configuration, kicad_mod, variant,  ISO273[N]["drill"][drill_type] ,  screew_sizes["size"] )

                # doAnnularVia(via_count, via_diameter, x_size, y_size)
                r_vias = (screew_sizes["size"]+ISO273[N]["drill"][drill_type]) / 2
                if variant == '2PAD+V':
                    doAnnularVia( via_count    = ISO273[N]["vias"][0],
                                  via_diameter = ISO273[N]["vias"][1],
                                  x_size       = r_vias,
                                  y_size       = r_vias
                                   )

                body_edge={
                    'left'  : 0,
                    'right' : screew_sizes["size"],
                    'top'   : screew_sizes["size"],
                    'bottom': 0
                }

                cy1 = roundToBase(body_edge['top'], configuration['courtyard_grid'])
                cy1 = (cy1 / 2) + 1.5  # radius + big nudge

                ######################### Text Fields ###############################
                #addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
                #    courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')
                kicad_mod.append(Text(type='value',     text=footprint_name, at=[0, -cy1], layer='F.Fab'))
                kicad_mod.append(Text(type='reference', text='REF**',        at=[0, cy1],  layer='F.SilkS'))
                kicad_mod.append(Text(type='user', text='${REFERENCE}', at=[cy1, 0],    layer='F.Fab', size=[0.5, 0.5]))


                ##################### Output and 3d model ############################
                model3d_path_prefix = configuration.get('3d_model_prefix','${KICAD6_3DMODEL_DIR}/')
                #lib_name = 'ISO/xxxxx'       # could add subdir 'variant'
                model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
                            model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
                # KiCad fully handles it !
                kicad_mod.append(Model(filename=model_name))

                output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
                if not os.path.isdir(output_dir): #returns false if path does not 
                    os.makedirs(output_dir)       #yet exist!! (Does not check path validity)

                filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

                # write file
                file_handler = KicadFileHandler(kicad_mod)
                file_handler.writeFile(filename)

