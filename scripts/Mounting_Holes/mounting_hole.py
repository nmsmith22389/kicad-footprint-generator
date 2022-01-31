#!/usr/bin/env python3

# This is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
#
#  Mounting holes footprint generator fo KiCad
#
#  Holes:
#            sizes are standard ISO and ANSI. ISO-273 specifies adjustment
#            between the screw body and the hole. I did not find equivalent for ANSI.
#            This generator doen't generate oblong holes
#
#  Screws:
#            the screw serie defines the Pad diameter. For ANSI,
#            3 sizes are defined (small, normal, large)
#            for ISO, only normal and large.
#
#  2022 by Franck Bourdonnec, <>


import sys
import os
import re
import copy as syscopy
import argparse
import yaml
import math

sys.path.append(os.path.join(sys.path[0], "..", ".."))  # load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0],"..","kicad_mod")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path

from KicadModTree import *

lib_name = 'MountingHole'
#during test
#lib_name = 'KKKKK'

# Metric standart hole size for screws assembly
# https://cdn.standards.iteh.ai/samples/4183/1a8db2e6de054d2e9bed7d40be64d6e1/ISO-273-1979.pdf
im = 25.4
ISO273 = {
            # name              nominal, fine, medium, coarse
#ISO273 sizes                            H7    H9    H11 (synonyms adjustements ?)
          "M1.6":     {"drill":  ( 1.6,  1.7,  1.8,  2.0)  , "vias": (6,  0.3)},
          "M2.0":     {"drill":  ( 2.0,  2.2,  2.4,  2.6)  , "vias": (6,  0.4)},
          "M2.5":     {"drill":  ( 2.5,  2.7,  2.9,  3.1)  , "vias": (6,  0.4)},
          "M3.0":     {"drill":  ( 3.0,  3.2,  3.4,  3.6)  , "vias": (6,  0.4)},
          "M3.5":     {"drill":  ( 3.5,  3.7,  3.9,  4.2)  , "vias": (8,  0.4)},
          "M4.0":     {"drill":  ( 4.0,  4.3,  4.5,  4.8)  , "vias": (8,  0.8)},
          "M5.0":     {"drill":  ( 5.0,  5.3,  5.5,  5.8)  , "vias": (8,  0.8)},
          "M6.0":     {"drill":  ( 6.0,  6.4,  6.6,  7.0)  , "vias": (12, 0.8)},
          "M8.0":     {"drill":  ( 8.0,  8.4,  9.0, 10.0)  , "vias": (12, 1.2)},
         "M10.0":     {"drill":  (10.0, 10.5, 11.0, 12.0)  , "vias": (12, 1.2)},

#ANSI sizes            #                     H7          H9        H11 (found no info about that)
        "ANSI_0":      {"drill":  ( 0.06 *im,  0.06 *im, 0.06 *im, 0.06 *im  )  , "vias": (6,  0.25   )},
        "ANSI_1":      {"drill":  ( 5/64 *im,  5/64 *im, 5/64 *im, 5/64 *im  )  , "vias": (6,  0.3969 )},
        "ANSI_2":      {"drill":  ( 3/32 *im,  3/32 *im, 3/32 *im, 3/32 *im  )  , "vias": (6,  0.3969 )},
        "ANSI_3":      {"drill":  ( 7/64 *im,  7/64 *im, 7/64 *im, 7/64 *im  )  , "vias": (6,  0.4572 )},
        "ANSI_4":      {"drill":  ( 1/8  *im,  1/8  *im, 1/8  *im, 1/8  *im  )  , "vias": (6,  0.4572 )},
        "ANSI_5":      {"drill":  ( 1/8  *im,  1/8  *im, 1/8  *im, 1/8  *im  )  , "vias": (8,  0.5080 )},
        "ANSI_6":      {"drill":  ( 9/64 *im,  9/64 *im, 9/64 *im, 9/64 *im  )  , "vias": (8,  0.5080 )},
        "ANSI_7":      {"drill":  ( 5/32 *im,  5/32 *im, 5/32 *im, 5/32 *im  )  , "vias": (8,  0.8382 )},
        "ANSI_8":      {"drill":  (11/64 *im, 11/64 *im,11/64 *im,11/64 *im  )  , "vias": (8,  0.8382 )},
        "ANSI_9":      {"drill":  (11/64 *im, 11/64 *im,11/64 *im,11/64 *im  )  , "vias": (10, 0.8382 )}, #.4in
       "ANSI_10":      {"drill":  ( 3/16 *im,  3/16 *im, 3/16 *im, 3/16 *im  )  , "vias": (10, 0.8382 )},
       "ANSI_11":      {"drill":  ( 3/16 *im,  3/16 *im, 3/16 *im, 3/16 *im  )  , "vias": (10, 1.016  )}, #.41in
       "ANSI_12":      {"drill":  ( 7/32 *im,  7/32 *im, 7/32 *im, 7/32 *im  )  , "vias": (10, 1.016  )},
       "ANSI_14":      {"drill":  ( 1/4  *im,  1/4  *im, 1/4  *im, 1/4  *im  )  , "vias": (12, 1.016  )}, # 1/4

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
   #{  "Name": "M6.0",     "size": 10.0 },   # very similar 7380-1 M6
    {  "Name": "M8.0",     "size": 13.0 },
    {  "Name": "M10.0",    "size": 16.0 }
               ],
    "dataSheet":  "https://www.newfastener.com/wp-content/uploads/2013/03/ISO-14580.pdf",
    "Description":"ISO-14580, ISO-1207, ISO-4762, DIN-82 Normal Head Sizes (M3.5 and M6 removed)"
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
    "Description":"ISO-7380, ISO-7380-1 Large Head Sizes M3 M4 M5 M6 M8 M10"
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


#Torx screws with normal collar
Torx = {"data":[

    {  "Name": "ANSI_2",    "size":  .167 *im  },
    {  "Name": "ANSI_4",    "size":  .219 *im  },
    {  "Name": "ANSI_6",    "size":  .270 *im  },
    {  "Name": "ANSI_8",    "size":  .322 *im  },
    {  "Name": "ANSI_10",   "size":  .373 *im  },
    {  "Name": "ANSI_12",   "size":  .425 *im  },
    {  "Name": "ANSI_14",   "size":  .492 *im  }, # 1/4
                    ],
    "dataSheet":  "page 74: https://www.nationalengfasteners.com/images/TechnicalDocuments/selfTappingScrewsGuide.pdf",
    "Description":"Torx Pan Drive Heads #2 #4 #6 #8 #10 #12 ¼"
    }

#Small head diameter screws
Fillister = {"data":[

    {  "Name": "ANSI_0",    "size":  .096 *im  },
    {  "Name": "ANSI_2",    "size":  .140 *im  },
    {  "Name": "ANSI_4",    "size":  .183 *im  },
    {  "Name": "ANSI_6",    "size":  .226 *im  },
    {  "Name": "ANSI_8",    "size":  .270 *im  },
    {  "Name": "ANSI_10",   "size":  .313 *im  },
    {  "Name": "ANSI_12",   "size":  .357 *im  },
    {  "Name": "ANSI_14",   "size":  .414 *im  }, # 1/4
                    ],
    "dataSheet":  "page 16: https://www.nationalengfasteners.com/images/TechnicalDocuments/selfTappingScrewsGuide.pdf",
    "Description":"Fillister screws #0 #2 #4 #6 #8 #10 #12 ¼"
    }
#Large head
Phillips = {"data":[

    {  "Name": "ANSI_4",    "size":  .261 *im  },
    {  "Name": "ANSI_6",    "size":  .321 *im  },
    {  "Name": "ANSI_8",    "size":  .380 *im  },
    {  "Name": "ANSI_10",   "size":  .439 *im  },
    {  "Name": "ANSI_12",   "size":  .498 *im  },
    {  "Name": "ANSI_14",   "size":  .576 *im  }, # 1/4
                    ],
    "dataSheet":  "page 19: https://www.nationalengfasteners.com/images/TechnicalDocuments/selfTappingScrewsGuide.pdf",
    "Description":"Phillips Round Wahser Heads #4 #6 #8 #10 #12 ¼"
    }

# List a screws series to build
screws = [ISO14580, ISO7380_1, Torx, Fillister, Phillips]  #ISO73380_2


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

        kicad_mod.append(Pad(number='1',  #needed to connect them to the main pad !
                             type=Pad.TYPE_THT,
                             shape=Pad.SHAPE_CIRCLE,
                             at=[step_x, step_y],
                             #0.3 is minimum to silence footprint checker. But we need really
                             # smaller ring extension. Not a problem because the extension
                             # is merged in the main pad
                             size=[via_diameter+0.2, via_diameter+0.2],
                             drill=via_diameter,
                             layers=['*.Cu', '*.Mask']
                             ))


def create_pad(configuration, kicad_mod, holeType, holeSize, padSize ):

    silk_nudge = configuration['silk_fab_offset']
    crtd_nudge = configuration['courtyard_offset']['connector']
    silk_w = configuration['silk_line_width']
    fab_w = configuration['fab_line_width']

    #    TYPE_THT     = 'thru_hole'
    #    TYPE_SMT     = 'smd'
    #    TYPE_CONNECT = 'connect'
    #    TYPE_NPTH    = 'np_thru_hole'     # cannot use that when there is a PAD, see KiCad Issue #10637

    # Default NPTH (basic hole with no copper)
    myPad = Pad(
        number= "",
        type  = Pad.TYPE_NPTH,
        shape = Pad.SHAPE_CIRCLE,
        clearance = 0,
        at    = [0, 0],
        # The pad is not necessariliy copper and can be any layer
        size  = [padSize, padSize],  # so we need a size
        layers = [''],
        drill = holeSize
    )

    # Silk screen circle & courtyard around the screw head
    radius = padSize/2
    kicad_mod.append(  Circle( center=[0, 0], radius=radius, layer='F.Fab'))
    kicad_mod.append(  Circle( center=[0, 0], radius=radius+silk_nudge, layer='F.SilkS'))

    radius = roundToBase( radius + crtd_nudge, configuration['courtyard_grid'])
    kicad_mod.append(  Circle( center=[0, 0], radius=radius, layer='F.CrtYd'))
    kicad_mod.setAttribute('through_hole')

    if holeType == '':
        # This prevents Tenting of the hole on both sides
        myPad.layers = ['*.Mask']
        # For hole with no copper, set a clearance that extands to the
        myPad.clearance = radius-holeSize/2
        # hole courtyard. This protect from zone filling under the head screw
        kicad_mod.append(myPad)
        return # nothing more to do for NPTH


    # An electrical PAD
    myPad.number= "1"  # needed to route a track

    # We have a Pad, one or both sides ?
    myPad.type = Pad.TYPE_THT              # for now, it needs to be plated to be routed (issue #10637)

    if holeType == '1PADf':

        # Protect the other side from being filled by a zone
        myPad2 = syscopy.deepcopy(myPad)
        myPad2.layers = ['B.Mask']
        myPad2.clearance = radius-holeSize/2
        kicad_mod.append(myPad2)

        #myPad.layers = ['F.Cu', 'F.Mask']  # Logically, a hole is expected not to be tented
        myPad.layers = ['F.Cu', '*.Mask']  # so excluding mask for the screw head is enougth.
                                           # That is no true, we need to exclude on both sides
                                           # see https://gitlab.com/kicad/code/kicad/-/issues/10637

    if holeType == '1PADb':

        # Protect the other side from being filled by a zone
        myPad2 = syscopy.deepcopy(myPad)
        myPad2.layers = ['F.Mask']
        myPad2.clearance = radius-holeSize/2
        kicad_mod.append(myPad2)


        #myPad.layers = ['B.Cu', 'B.Mask']  # Logically, a hole is expected not to be tented
        myPad.layers = ['B.Cu', '*.Mask']  # so excluding mask for the screw head is enougth.
                                           # That is no true, we need to exclude on both sides
                                           # see https://gitlab.com/kicad/code/kicad/-/issues/10637

    if re.match ('2PAD', holeType):
        myPad.layers = ['*.Cu', '*.Mask']
        myPad.type = Pad.TYPE_THT          # only biface are really THT

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

            for variant in ('', '1PADf','1PADb', '2PAD', '2PAD+V'):

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

