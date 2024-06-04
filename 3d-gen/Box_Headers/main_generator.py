#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script to generate all pin header models
# in X3D format. It takes a bit long to run!
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
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
#* CadQuery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
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

__title__ = "make pin header 3D models"
__author__ = "maurice, hyOzd, jmwright"
__Comment__ = 'make pin header 3D models exported to STEP and VRML'

___ver___ = "2.0.0"

import os

import cadquery as cq
from _tools import shaderColors, parameters, cq_color_correct, cq_globals, export_tools
from exportVRML.export_part_to_VRML import export_VRML

dest_dir_prefix = "Connector_IDC.3dshapes"


def MakeBase(pins, highDetail=True):
    """
    Makes a single plastic base block (chamfered if required).
    Dimensions taken from Wurth Elektronik (WE) 612 0xx 216 21: http://katalog.we-online.de/em/datasheet/6120xx21621.pdf
    Dimensions not shown on drawing are estimated or taken from physical example
    """

    #length of the base block
    L = pins * 2.54 + 7.66
    #Width of base block
    W1 = 8.85
    #internal width
    W2 = 6.35
    #wall thickness
    T = (W1 - W2) / 2.0
    #length of pin array
    D = (pins - 1) * 2.54
    #height of the base
    H = 8.85 - 6.50
    base = cq.Workplane("XY").rect(W1, L).extrude(H)
    #wall height H2
    H2 = 6.50

    #extrude the edge up around the base
    wall = cq.Workplane("XY").workplane(offset=H).rect(W1, L).extrude(H2)
    wall = wall.cut(cq.Workplane("XY").rect(W2, (pins - 1) * 2.54 + 7.88).extrude(8.85))
    # add a chamfer to the wall inner (only for high detail version)
    # if (highDetail):
    #     wall = wall.faces(">Z").edges("not(<X or >X or <Y or >Y)").chamfer(0.5)
    base = base.union(wall)

    #cut a notch out of one side
    CW = 4.5

    # in detail version, this tab extends slightly below base top surface
    if (highDetail):
        undercut = 0.5
    else:
        undercut = 0.0

    cutout = cq.Workplane("XY").workplane(offset=H-undercut).rect(2*2.0, CW).extrude(H2+undercut).translate((-W1/2.0, 0, 0))
    base = base.cut(cutout)

    # add visual / non-critical details
    if (highDetail):
        # long bobbles
        bobbleR = 0.5
        bobbleH = 9.10 - 8.85
        longbobble1 = cq.Workplane("XY").center(W1/2.0-bobbleR+bobbleH, L/2.0-2.5).circle(bobbleR).extrude(8.5)
        longbobble2 = cq.Workplane("XY").center(W1/2.0-bobbleR+bobbleH, 0).circle(bobbleR).extrude(8.5)
        longbobble3 = cq.Workplane("XY").center(W1/2.0-bobbleR+bobbleH, -L/2.0+2.5).circle(bobbleR).extrude(8.5)
        base = base.union(longbobble1)
        base = base.union(longbobble2)
        base = base.union(longbobble3)

        # wee bobbles
        weebobbles = cq.Workplane("XY").center(2.85, L/2.0-2.5).circle(0.5).extrude(8.85-9.10)
        weebobbles = weebobbles.union(cq.Workplane("XY").center(2.85, 0).circle(0.5).extrude(8.85-9.10))
        weebobbles = weebobbles.union(cq.Workplane("XY").center(2.85, -L/2.0+2.5).circle(0.5).extrude(8.85-9.10))
        weebobbles = weebobbles.union(weebobbles.translate((-5.7, 0, 0)))
        base = base.union(weebobbles)

        # sidecuts
        sidecut = cq.Workplane("XY").rect(3.5, 1.25*2).extrude(H2).translate((0, L/2.0, 0))
        sidecut = sidecut.union(sidecut.translate((0, -L, 0)))
        base = base.cut(sidecut)

    #now offset the location of the base appropriately
    base = base.translate((1.27, (pins-1)*-1.27, 9.10-8.85))

    return base


def MakePin(Z, H):
    """
    Makes a single pin.
    """

    # Pin size
    size = 0.64
    # Pin distance below z=0
    #Z = -3.0
    # Pin height (above board)
    # H = 8.0
    pin = cq.Workplane("XY").workplane(offset=Z).rect(size,size).extrude(H - Z)
    # Chamfer C
    C = 0.2
    pin = pin.faces("<Z").chamfer(C)
    pin = pin.faces(">Z").chamfer(C)

    return pin


def MakeAnglePin(Z, H, L, highDetail=False):
    """
    Makes a single pin.
    """

    # Pin size
    size = 0.64
    pin = cq.Workplane("XY").workplane(offset=Z).rect(size,size).extrude(H - Z + size/2.0)
    pin = pin.union(cq.Workplane("YZ").workplane(offset=size/2.0).rect(size, size).extrude(L-size/2.0).translate((0, 0, H)))
    # Chamfer C
    C = 0.2
    pin = pin.faces("<Z").chamfer(C)
    pin = pin.faces(">X").chamfer(C)

    # Fillet on back of pin
    if (highDetail):
        R = size
        pin = pin.faces(">Z").edges("<X").fillet(R)

    return pin


def MakePinRow(n, Z, H):
    """
    Makes a row of straight pins.
    """

    # Make some pins
    pin = MakePin(Z, H)

    for i in range(1, n):
        pin = pin.union(MakePin(Z, H).translate((0, -2.54 * i, 0)))

    return pin


def MakeAnglePinRow(n, Z, H, L, highDetail=False):
    """
    Makes a row of angled (bent) pins.
    """

    pin = MakeAnglePin(Z, H, L, highDetail)

    for i in range(1, n):
        pin = pin.union(MakeAnglePin(Z, H, L, highDetail).translate((0, -2.54 * i, 0)))

    return pin


def make_models(model_to_build=None, output_dir_prefix=None, enable_vrml=True):
    """
    Main entry point into this generator.
    """
    models = []

    all_params = parameters.load_parameters("Box_Headers")

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

    if output_dir_prefix == None:
        print("ERROR: An output directory must be provided.")
        return
    else:
        # Construct the final output directory
        output_dir = os.path.join(output_dir_prefix, dest_dir_prefix)

    # Step through the selected models
    for model in models:
        # Safety check to make sure the selected model is valid
        if not model in all_params.keys():
            print("Parameters for %s doesn't exist in 'all_params', skipping." % model)
            continue

        # Load the appropriate colors
        body_color = shaderColors.named_colors[all_params[model]["body_color_key"]].getDiffuseFloat()
        pins_color = shaderColors.named_colors[all_params[model]["pins_color_key"]].getDiffuseFloat()

        # Set high detail mode to always be on
        highDetail = True

        # Get the number of pins from the parameters
        n = all_params[model]["pins"]

        # Generate the model of the part
        body = MakeBase(n, True)
        if all_params[model]["is_angled"]:
             pins = MakeAnglePinRow(n, -3, 5.94, 12.38, highDetail)
             pins = pins.union(MakeAnglePinRow(n, -3, 3.40, 9.84, highDetail).translate((2.54,0,0)))

             # Rotate the base into the angled position
             body = body.rotate((0,0,0),(0,1,0),90).translate((4.13,0,5.94))
        else:
            pins = MakePinRow(n, -3.0, 8.0)
            pins = pins.union(MakePinRow(n, -3.0, 8.0).translate((2.54,0,0)))

        # Wrap the component parts in an assembly so that we can attach colors
        component = cq.Assembly(name=model)
        component.add(body, color=cq_color_correct.Color(body_color[0], body_color[1], body_color[2]))
        component.add(pins, color=cq_color_correct.Color(pins_color[0], pins_color[1], pins_color[2]))

        # Create the output directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the assembly to STEP
        component.save(os.path.join(output_dir, model + ".step"), cq.exporters.ExportTypes.STEP, mode=cq.exporters.assembly.ExportModes.FUSED, write_pcurves=False)

        # Check for a proper union
        export_tools.check_step_export_union(component, output_dir, model)

        # Export the assembly to VRML
        if enable_vrml:
            export_VRML(os.path.join(output_dir, model + ".wrl"), [body, pins], [all_params[model]["body_color_key"], all_params[model]["pins_color_key"]])

        # Update the license
        from _tools import add_license
        add_license.addLicenseToStep(output_dir, model + ".step",
                                        add_license.LIST_int_license,
                                        add_license.STR_int_licAuthor,
                                        add_license.STR_int_licEmail,
                                        add_license.STR_int_licOrgSys,
                                        add_license.STR_int_licPreProc)
