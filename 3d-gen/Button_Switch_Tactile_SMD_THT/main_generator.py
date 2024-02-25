#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating QFP models in
# X3D format.
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# Dimensions are from Jedec MS-026D document.
#
# Thanks to Frank Severinsen (Shack) for including the orignal vrml
# materials.
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
## These are CadQuery scripts that will generate STEP and VRML parametric 
## models.
#
#*                                                                          *
#* cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
#*   Copyright (c) 2015                                                     *
#* Maurice https://launchpad.net/~easyw                                     *
#* Copyright (c) 2021                                                       *
#*     Update 2021                                                          *
#*     jmwright (https://github.com/jmwright)                               *
#*     Work sponsored by KiCAD Services Corporation                         *
#*          (https://www.kipro-pcb.com/)                                    *
#*                                                                          *
#* All trademarks within this guide belong to their legitimate owners.      *
#*                                                                          *
#*   This program is free software; you can redistribute it and/or modify   *
#*   it under the terms of the GNU Lesser General Public License (LGPL)     *
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

__title__ = "make BGA ICs 3D models"
__author__ = "maurice, hyOzd, jmwright"
__Comment__ = 'make BGA ICs 3D models exported to STEP and VRML'

___ver___ = "2.0.0"

import os
from math import tan, radians

import cadquery as cq
from _tools import shaderColors, parameters, cq_color_correct, cq_globals, export_tools
from exportVRML.export_part_to_VRML import export_VRML

from .cq_base_tact_switches import cqMakerTactSwitch
from .cq_cuk_pts125sx import cqMakerCuKPTS125SxTactSwitch
from .cq_ultra_small_tact_switch import cqMakerUltraSmallTactSwitch
from .cq_cuk_kmr2x import cqMakerCuK_Kmr2xTactSwitch
from .cq_cuk_pts810x import cqMakerCuK_PTS810xTactSwitch

# dest_dir_prefix = "Package_BGA.3dshapes"

def make_models(model_to_build=None, output_dir_prefix=None, enable_vrml=True):
    """
    Main entry point into this generator.
    """
    models = []

    all_params = parameters.load_parameters("Button_Switch_Tactile_SMD_THT")

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
        cover_color = shaderColors.named_colors[all_params[model]["cover_color_key"]].getDiffuseFloat()
        body_color = shaderColors.named_colors[all_params[model]["body_color_key"]].getDiffuseFloat()
        pins_color = shaderColors.named_colors[all_params[model]["pins_color_key"]].getDiffuseFloat()
        button_color = shaderColors.named_colors[all_params[model]["button_color_key"]].getDiffuseFloat()

        # Generate the current model
        if all_params[model]["model_class"] == "cqMakerTactSwitch":
            cqm = cqMakerTactSwitch(all_params[model])
        elif all_params[model]["model_class"] == "cqMakerCuKPTS125SxTactSwitch":
            cqm = cqMakerCuKPTS125SxTactSwitch(all_params[model])
        elif all_params[model]["model_class"] == "cqMakerUltraSmallTactSwitch":
            cqm = cqMakerUltraSmallTactSwitch(all_params[model])
        elif all_params[model]["model_class"] == "cqMakerCuK_Kmr2xTactSwitch":
            cqm = cqMakerCuK_Kmr2xTactSwitch(all_params[model])
        elif all_params[model]["model_class"] == "cqMakerCuK_PTS810xTactSwitch":
            cqm = cqMakerCuK_PTS810xTactSwitch(all_params[model])
        else:
            print("ERROR: No match found for the model_class")
            continue

        case = cqm.makePlasticCase().translate((all_params[model]['body_setback_distance'], 0.0, all_params[model]['body_board_distance'])).rotate((0, 0, 0), (0, 0, 1), all_params[model]['rotation'])
        cover = cqm.makeCoverPlate ().translate((all_params[model]['body_setback_distance'], 0.0, all_params[model]['body_board_distance'])).rotate((0, 0, 0), (0, 0, 1), all_params[model]['rotation'])
        button = cqm.makeButton ().translate((all_params[model]['body_setback_distance'], 0.0, all_params[model]['body_board_distance'])).rotate((0, 0, 0), (0, 0, 1), all_params[model]['rotation'])
        pins = cqm.make_pins().translate((all_params[model]['body_setback_distance'], 0.0, 0.0)).rotate((0, 0, 0), (0, 0, 1), all_params[model]['rotation'])

        # Wrap the component parts in an assembly so that we can attach colors
        component = cq.Assembly(name=model)
        component.add(case, color=cq_color_correct.Color(body_color[0], body_color[1], body_color[2]))
        component.add(cover, color=cq_color_correct.Color(cover_color[0], cover_color[1], cover_color[2]))
        component.add(pins, color=cq_color_correct.Color(pins_color[0], pins_color[1], pins_color[2]))
        component.add(button, color=cq_color_correct.Color(button_color[0], button_color[1], button_color[2]))

        # Create the output directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the assembly to STEP
        component.save(os.path.join(output_dir, model + ".step"), cq.exporters.ExportTypes.STEP, mode=cq.exporters.assembly.ExportModes.FUSED, write_pcurves=False)

        # Check for a proper union
        export_tools.check_step_export_union(component, output_dir, model)

        # Export the assembly to VRML
        if enable_vrml:
            export_VRML(os.path.join(output_dir, model + ".wrl"), [case, cover, pins, button], [all_params[model]["cover_color_key"], all_params[model]["body_color_key"], all_params[model]["pins_color_key"], all_params[model]["button_color_key"]])

        # Update the license
        from _tools import add_license
        add_license.addLicenseToStep(output_dir, model + ".step",
                                        add_license.LIST_int_license,
                                        add_license.STR_int_licAuthor,
                                        add_license.STR_int_licEmail,
                                        add_license.STR_int_licOrgSys,
                                        add_license.STR_int_licPreProc)
