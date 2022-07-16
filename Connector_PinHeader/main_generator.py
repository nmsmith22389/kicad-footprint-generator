#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
# This is a
# Dimensions are from Microchips Packaging Specification document:
# DS00000049BY. Body drawing is the same as QFP generator#
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
#* These are cadquery tools to export                                       *
#* generated models in STEP & VRML format.                                  *
#*                                                                          *
#* cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
#*   Copyright (c) 2015                                                     *
#*     Maurice https://launchpad.net/~easyw                                 *
#* Copyright (c) 2022                                                       *
#*     Update 2022                                                          *
#*     jmwright (https://github.com/jmwright)                               *
#*     Work sponsored by KiCAD Services Corporation                         *
#*          (https://www.kipro-pcb.com/)                                    *
#*                                                                          *
#* All trademarks within this guide belong to their legitimate owners.      *
#*                                                                          *
#*   This program is free software; you can redistribute it and/or modify   *
#*   it under the terms of the GNU General Public License (GPL)             *
#*   as published by the Free Software Foundation; either version 2 of      *
#*   the License, or (at your option) any later version.                    *
#*   for detail see the LICENCE text file.                                  *
#*                                                                          *
#*   This program is distributed in the hope that it will be useful,        *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
#*   GNU Library General Public License for more details.                   *
#*                                                                          *
#*   You should have received a copy of the GNU Library General Public      *
#*   License along with this program; if not, write to the Free Software    *
#*   Foundation, Inc.,                                                      *
#*   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA           *
#*                                                                          *
#****************************************************************************

__title__ = "main generator for capacitor tht model generators"
__author__ = "scripts: maurice and Shack; models: see cq_model files; update: jmwright"
__Comment__ = '''This generator loads cadquery model scripts and generates step/wrl files for the official kicad library.'''

___ver___ = "2.0.0"

import os
from math import tan, radians

import cadquery as cq
from _tools import shaderColors, parameters, cq_color_correct
from _tools import cq_globals

from .pinheader import make_Vertical_THT_base, make_Vertical_THT_pins, make_Horizontal_THT_base, make_Horizontal_THT_pins, make_Vertical_SMD_pins, make_Vertical_SMD_base

def make_models(model_to_build=None, output_dir_prefix=None, enable_vrml=True):
    """
    Main entry point into this generator.
    """
    models = []

    all_params = parameters.load_parameters("Connector_PinHeader")

    if all_params == None:
        print("ERROR: Model parameters must be provided.")
        return

    # Handle the case where no model has been passed
    if model_to_build is None:
        print("No variant name is given! building: {0}".format(model_to_build))

        model_to_build = all_params.keys()[0]

    # Handle being able to generate all models or just one
    if model_to_build == "all":
        models = all_params
    else:
        models = { model_to_build: all_params[model_to_build] }
    # Step through the selected models
    for model in models:
        if output_dir_prefix == None:
            print("ERROR: An output directory must be provided.")
            return
        else:
            # Construct the final output directory
            output_dir = os.path.join(output_dir_prefix, all_params[model]['destination_dir'])

        # Safety check to make sure the selected model is valid
        if not model in all_params.keys():
            print("Parameters for %s doesn't exist in 'all_params', skipping." % model)
            continue

        # Load the appropriate colors
        body_color = shaderColors.named_colors[all_params[model]["body_color_key"]].getDiffuseFloat()
        pins_color = shaderColors.named_colors[all_params[model]["pin_color_key"]].getDiffuseFloat()

        header_type = all_params[model]['type']
        pitch = all_params[model]['pitch']
        rows = all_params[model]['rows']
        base_width = all_params[model]['base_width']
        base_height = all_params[model]['base_height']
        base_chamfer = all_params[model]['base_chamfer']
        pin_width = all_params[model]['pin_width']
        pin_length_above_base = all_params[model]['pin_length_above_base']

        pin_end_chamfer = all_params[model]['pin_end_chamfer']
        rotation = all_params[model]['rotation']

        pin_num_start = all_params[model]['pins']['from']
        pin_num_end = all_params[model]['pins']['to']

        if base_chamfer == 'auto':
            base_chamfer = pitch/10.0

        if pin_end_chamfer == 'auto':
            pin_end_chamfer = pin_width/4.0

        for num_pins in range(pin_num_start, pin_num_end + 1):
            if header_type == 'Vertical_THT':
                pin_length_below_board = all_params[model]['pin_length_below_board']
                base = make_Vertical_THT_base(num_pins, pitch, rows, base_width, base_height, base_chamfer)
                pins = make_Vertical_THT_pins(num_pins, pitch, rows, pin_length_above_base, pin_length_below_board, base_height, pin_width, pin_end_chamfer)
            elif header_type == 'Horizontal_THT':
                pin_length_below_board = all_params[model]['pin_length_below_board']
                base_x_offset = all_params[model]['base_x_offset']
                base = make_Horizontal_THT_base(num_pins, pitch, rows, base_width, base_height, base_x_offset, base_chamfer)
                pins = make_Horizontal_THT_pins(num_pins, pitch, rows, pin_length_above_base, pin_length_below_board, base_height, base_width, pin_width, pin_end_chamfer, base_x_offset)
            elif header_type == 'Vertical_SMD':
                pin_length_horizontal = all_params[model]['pin_length_horizontal']
                base_z_offset = all_params[model]['base_z_offset']
                if rows == 1:
                    pin_1_start = all_params[model]['pin_1_start']
                else:
                    pin_1_start = None
                pins = make_Vertical_SMD_pins(num_pins, pitch, rows, pin_length_above_base, pin_length_horizontal, base_height, base_width, pin_width, pin_end_chamfer, base_z_offset, pin_1_start)
                base = make_Vertical_SMD_base(num_pins, pitch, base_width, base_height, base_chamfer, base_z_offset)
            else:
                print("Model {} is not recognized.".format(model))
                continue

            # Used to wrap all the parts into an assembly
            component = cq.Assembly()

            # Add the parts to the assembly
            component.add(base, color=cq_color_correct.Color(body_color[0], body_color[1], body_color[2]))
            component.add(pins, color=cq_color_correct.Color(pins_color[0], pins_color[1], pins_color[2]))

            # Create the output directory if it does not exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Create the file name based on the rows and pins
            if num_pins < 10:
                num_pins_str = "0" + str(num_pins)
            else:
                num_pins_str = str(num_pins)
            file_name = model.replace("yy", num_pins_str)

            # Export the assembly to STEP
            component.save(os.path.join(output_dir, file_name + ".step"), cq.exporters.ExportTypes.STEP, write_pcurves=False)

            # Export the assembly to VRML
            if enable_vrml:
                cq.exporters.assembly.exportVRML(component, os.path.join(output_dir, file_name + ".wrl"), tolerance=cq_globals.VRML_DEVIATION, angularTolerance=cq_globals.VRML_ANGULAR_DEVIATION)

            # Update the license
            from _tools import add_license
            add_license.addLicenseToStep(output_dir, file_name + ".step",
                                            add_license.LIST_int_license,
                                            add_license.STR_int_licAuthor,
                                            add_license.STR_int_licEmail,
                                            add_license.STR_int_licOrgSys,
                                            add_license.STR_int_licPreProc)
