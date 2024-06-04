#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
#* CadQuery script for generating Stocko models in STEP AP214               *
#*   Copyright (c) 2016                                                     *
#* Bartosz Balcerzak  https://github.com/bartosz.maciej.balcerzak           *
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
__author__ = "scripts: bartosz.maciej.balcerzak and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = '''This generator loads cadquery model scripts and generates step/wrl files for the official kicad library.'''

___ver___ = "2.0.0"

import os
from math import tan, radians

import cadquery as cq
from _tools import shaderColors, parameters, cq_color_correct, cq_globals, export_tools
from exportVRML.export_part_to_VRML import export_VRML


def make_connector(name, params):
    """
    Originally created by Bartosz Balcerzak  https://github.com/bartosz.maciej.balcerzak
    Generates body and pins for a given Stocko connector.
    """
    model_name = name
    full_model_name = name + "-6-0-{}{:02d}_1x{}_P2.50mm_Vertical".format(params["pins"], params["pins"], params["pins"])

    body = cq.Workplane("XY").move(-params["outline_x"], 0).box((params["pitch"] * (params["pins"] - 1)) + 2 * params["outline_x"], \
    params["base_w"], params["base_h"], centered = (False,True,False))
    body = body.faces(">Z") \
    .workplane(centerOption="CenterOfMass").rect(params["pitch"] * (params["pins"] - 1) + 2 * params["outline_x"] - params["lr_sides_t"], \
    params["base_w"] - params["tb_sides_t"]) \
    .cutBlind(-params["depth"]) \
    .faces(">Z") \
    .edges("not(<X or >X or <Y or >Y)") \
    .chamfer(0.7)
    body = body.edges("|Z and >X").fillet(0.5)
    body = body.edges("|Z and <X").fillet(0.5)
    body = body.faces(">Z").workplane(centerOption="CenterOfMass").center(0, -params["base_w"] / 2 + params["base_cutout"] /2).rect( \
    params["pitch"] * (params["pins"] - 1) + 2 * (params["outline_x"] - params["leaf"]), \
    params["base_cutout"]) \
    .cutThruAll()
    if params["top_cutout"]:
        body = body.faces(">Y").workplane(centerOption="CenterOfMass").center(0, 6.5).rect(params["t_cutout_w"], params["t_cutout_h"] ).cutThruAll()
    for x in range(params["pins"]):
        temp = (params["b_cutout_long_w"] - params["b_cutout_short_w"]) / 2
        body = body.faces(">Y").workplane(centerOption='CenterOfBoundBox').center( \
            ((params["pitch"] * (params["pins"] - 1) + 2 * params["outline_x"]) / 2) - params["outline_x"] - (params["b_cutout_long_w"] / 2) - x*params["pitch"], \
            -7).lineTo(params["b_cutout_long_w"], 0).lineTo(params["b_cutout_long_w"] - temp, params["b_cutout_h"]).lineTo(temp, params["b_cutout_h"]).close().cutThruAll()

    total_pin_length = params["pin"]["length_above_board"] + params["pin"]["length_below_board"]
    pin = cq.Workplane("XY").workplane(centerOption="CenterOfMass", offset=-params["pin"]["length_below_board"]).box(params["pin"]["width"], \
             params["pin"]["width"], total_pin_length, centered = (True,True,False))

    pin = pin.edges("#Z").chamfer(params["pin"]["end_chamfer"])
    pins_union = cq.Workplane("XY").workplane(centerOption="CenterOfMass", offset=-params["pin"]["length_below_board"])

    for x in range(params["pins"]):
        pins_union = pins_union.union(pin.translate((x*params["pitch"], 0, 0)))

    return (body, pins_union)


def make_models(model_to_build=None, output_dir_prefix=None, enable_vrml=True):
    """
    Main entry point into this generator.
    """
    models = []

    all_params = parameters.load_parameters("Conn_Stocko")

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

    general_dict = all_params['general']

    # Step through the selected models
    for model in models:
        if model == 'general':
            continue

        # Combine the general and model specific parameters
        all_params[model].update(general_dict)


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
        pins_color = shaderColors.named_colors[all_params[model]["pins_color_key"]].getDiffuseFloat()

        # Generate the model
        body, pins = make_connector(model, all_params[model])

        # Used to wrap all the parts into an assembly
        component = cq.Assembly()

        # Add the parts to the assembly
        component.add(body, color=cq_color_correct.Color(body_color[0], body_color[1], body_color[2]))
        component.add(pins, color=cq_color_correct.Color(pins_color[0], pins_color[1], pins_color[2]))

        # Create the output directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create the file name based on the rows and pins
        file_name = model + "-6-0-{}{:02d}_1x{}_P2.50mm_Vertical".format(all_params[model]["pins"], all_params[model]["pins"], all_params[model]["pins"])

        # Export the assembly to STEP
        component.name = file_name
        component.save(os.path.join(output_dir, file_name + ".step"), cq.exporters.ExportTypes.STEP, mode=cq.exporters.assembly.ExportModes.FUSED, write_pcurves=False)

        # Check for a proper union
        export_tools.check_step_export_union(component, output_dir, file_name)

        # Export the assembly to VRML
        if enable_vrml:
            export_VRML(os.path.join(output_dir, file_name + ".wrl"), [body, pins], [all_params[model]["body_color_key"], all_params[model]["pins_color_key"]])

        # Update the license
        from _tools import add_license
        add_license.addLicenseToStep(output_dir, file_name + ".step",
                                        add_license.LIST_int_license,
                                        add_license.STR_int_licAuthor,
                                        add_license.STR_int_licEmail,
                                        add_license.STR_int_licOrgSys,
                                        add_license.STR_int_licPreProc)
