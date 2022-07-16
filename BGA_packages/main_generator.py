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
from _tools import shaderColors, parameters, cq_color_correct
from _tools import cq_globals

dest_dir_prefix = "Package_BGA.3dshapes"

#all_params= all_params_qfn
#all_params= kicad_naming_params_qfn

def make_plg(wp, rw, rh, cv1, cv):
    """
    Creates a rectangle with chamfered corners.
    wp: workplane object
    rw: rectangle width
    rh: rectangle height
    cv1: chamfer value for 1st corner (lower left)
    cv: chamfer value for other corners
    """
    points = [
        (-rw/2., -rh/2.+cv1),
        (-rw/2., rh/2.-cv),
        (-rw/2.+cv, rh/2.),
        (rw/2.-cv, rh/2.),
        (rw/2., rh/2.-cv),
        (rw/2., -rh/2.+cv),
        (rw/2.-cv, -rh/2.),
        (-rw/2.+cv1, -rh/2.)#,
        #(-rw/2., -rh/2.+cv1)
    ]
    #return wp.polyline(points)
    sp = points.pop()
    wp=wp.moveTo(sp[0],sp[1])
    wp=wp.polyline(points, includeCurrent=True).close().wire()

    return wp
    #return wp.polyline(points).wire() #, forConstruction=True)
##

def make_case(params):

    ef  = params['ef']
    cff = params['cff']
    cf = params['cf']
    fp_r  = params['fp_r']
    fp_d  = params['fp_d']
    fp_z  = params['fp_z']
    D  = params['D']
    E   = params['E']
    D1  = params['D1']
    E1  = params['E1']
    A1  = params['A1']
    A2  = params['A2']
    A  = params['A']
    molded = params['molded']
    b   = params['b']
    e   = params['e']
    ex   = params['ex']
    sp   = params['sp']
    npx = params['npx']
    npy = params['npy']
    # mN  = params['modelName']
    rot = params['rotation']

    if ex == None:
        ex = e
    if ex == 0:
        ex = e

    place_pinMark = False

    if params['excluded_pins'] is not None:
        epl = list(params['excluded_pins'])
        #expVRML.say(epl)
        i=0
        for i in range (0, len(epl)):
            if isinstance(epl[i], int): #long is not supported in python 3
                epl[i]=str(int(epl[i]))
                i=i+1
        excluded_pins=tuple(epl)
        #expVRML.say(excluded_pins)
        #stop
    else:
        excluded_pins=() ##no pin excluded


    sphere_r = b/2 *(1.05) #added extra 0.5% diameter for fusion
    s_center =(0,0,0)
    sphere = cq.Workplane("XY", s_center). \
             sphere(sphere_r)
    bpin=sphere.translate((0,0,b/2-sp))

    pins = []
    # create top, bottom side pins
    pincounter = 1
    first_pos_x = (npx-1)*e/2
    for j in range(npy):
        for i in range(npx):
            if "internals" in excluded_pins:
                if str(int(pincounter)) not in excluded_pins:
                    if j==0 or j==npy-1 or i==0 or i==npx-1:
                        pin = bpin.translate((first_pos_x-i*e, (npy*ex/2-ex/2)-j*ex, 0)).\
                                rotate((0,0,0), (0,0,1), 180)
                        pins.append(pin)
            elif str(int(pincounter)) not in excluded_pins:
                pin = bpin.translate((first_pos_x-i*e, (npy*ex/2-ex/2)-j*ex, 0)).\
                        rotate((0,0,0), (0,0,1), 180)
                pins.append(pin)
                #expVRML.say(j)
            pincounter += 1
    # expVRML.say(pincounter-1)

    # merge all pins to a single object
    merged_pins = pins[0]
    for p in pins[1:]:
        merged_pins = merged_pins.union(p)
    pins = merged_pins

    # first pin indicator is created with a spherical pocket
    if fp_r == 0:
        place_pinMark=False
        fp_r = 0.1
    if molded is not None:
        the=24
        if D1 is None:
            D1=D*(1-0.065)
            E1=E*(1-0.065)
        D1_t = D1-2*tan(radians(the))*(A-A1-A2)
        E1_t = E1-2*tan(radians(the))*(A-A1-A2)
        # draw the case
        cw = D-2*A1
        cl = E-2*A1
        case_bot = cq.Workplane("XY").workplane(offset=0)
        case_bot= make_plg(case_bot, cw, cl, cff, cf)
        case_bot = case_bot.extrude(A2-0.01)
        case_bot = case_bot.translate((0,0,A1))
        #show(case_bot)

        case = cq.Workplane("XY").workplane(offset=A1)
        #case = make_plg(case, cw, cl, cce, cce)
        case = make_plg(case, D1, E1, 3*cf, 3*cf)
        #case = case.extrude(c-A1)
        case = case.extrude(0.01)
        case = case.faces(">Z").workplane()
        case = make_plg(case, D1, E1, 3*cf, 3*cf).\
            workplane(offset=A-A2-A1)
        case = make_plg(case, D1_t, E1_t, 3*cf, 3*cf).\
            loft(ruled=True)
        # fillet the bottom vertical edges
        if ef!=0:
            case_bot = case_bot.edges("|Z").fillet(ef)
        # fillet top and side faces of the top molded part
        if ef!=0:
            BS = cq.selectors.BoxSelector
            case = case.edges(BS((-D1/2, -E1/2, A2+0.001), (D1/2, E1/2, A+0.001))).fillet(ef)
            #case = case.edges(BS((-D1/2, -E1/2, c+0.001), (D1/2, E1/2, A+0.001+A1/2))).fillet(ef)
        case = case.translate((0,0,A2-0.01))
        #show(case)
        #stop
        pinmark=cq.Workplane("XZ", (-D/2+fp_d+fp_r, -E/2+fp_d+fp_r, fp_z)).rect(fp_r/2, -2*fp_z, False).revolve().translate((0,0,A))#+fp_z))
        pinmark=pinmark.translate(((D-D1_t)/2+fp_d+cff,(E-E1_t)/2+fp_d+cff,-sp))
        #stop
        #if (color_pin_mark==False) and (place_pinMark==True):
        if place_pinMark==True:
            case = case.cut(pinmark)
        # extract pins from case
        #case = case.cut(pins)
        case_bot = case_bot.cut(pins)
        ##

    else:
        A2 = A - A1 #body height
        #if m == 0:
        #    case = cq.Workplane("XY").box(D-A1, E-A1, A2)  #margin to see fused pins
        #else:
        case = cq.Workplane("XY").box(D, E, A2)  #NO margin, pins don't emerge
        if ef!=0:
            case.edges("|X").fillet(ef)
            case.edges("|Z").fillet(ef)
        #translate the object
        case=case.translate((0,0,A2/2+A1-sp)).rotate((0,0,0), (0,0,1), 0)

        #sphere_r = (fp_r*fp_r/2 + fp_z*fp_z) / (2*fp_z)
        #sphere_z = A + sphere_r * 2 - fp_z - sphere_r

        pinmark=cq.Workplane("XZ", (-D/2+fp_d+fp_r, -E/2+fp_d+fp_r, fp_z)).rect(fp_r/2, -2*fp_z, False).revolve().translate((0,0,A2+A1-sp))#+fp_z))
        #pinmark=pinmark.translate((0,0,A1-sp))
        #stop
        # if (color_pin_mark==False) and (place_pinMark==True):
        if place_pinMark==True:
            case = case.cut(pinmark)
        # extract pins from case
        case = case.cut(pins)
        case_bot = None
    
    # See if rotation has been requested
    if (params['rotation'] != 0):
        # if case_bot != None:
        #     case_bot = case_bot.rotateAboutCenter((0, 1, 0), rot)
        case = case.rotateAboutCenter((0, 0, 1), rot)
        pins = pins.rotateAboutCenter((0, 0, 1), rot)
        pinmark = pinmark.rotate((0, 0, 0), (0, 0, 1), rot)

    return (case_bot, case, pins, pinmark)


def make_models(model_to_build=None, output_dir_prefix=None, enable_vrml=True):
    """
    Main entry point into this generator.
    """
    models = []

    all_params = parameters.load_parameters("BGA_packages")

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
        body_bot_color = shaderColors.named_colors[all_params[model]["body_bot_color_key"]].getDiffuseFloat()
        body_color = shaderColors.named_colors[all_params[model]["body_color_key"]].getDiffuseFloat()
        pins_color = shaderColors.named_colors[all_params[model]["pins_color_key"]].getDiffuseFloat()
        marking_color = shaderColors.named_colors[all_params[model]["marking_color_key"]].getDiffuseFloat()

        # Generate the current model
        case_bot, case, pins, pinmark = make_case(all_params[model])

        # Wrap the component parts in an assembly so that we can attach colors
        component = cq.Assembly()
        if case_bot != None:
            component.add(case_bot, color=cq_color_correct.Color(body_bot_color[0], body_bot_color[1], body_bot_color[2]))
        component.add(case, color=cq_color_correct.Color(body_color[0], body_color[1], body_color[2]))
        component.add(pins, color=cq_color_correct.Color(pins_color[0], pins_color[1], pins_color[2]))
        component.add(pinmark, color=cq_color_correct.Color(marking_color[0], marking_color[1], marking_color[2]))

        # Create the output directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the assembly to STEP
        component.save(os.path.join(output_dir, model + ".step"), cq.exporters.ExportTypes.STEP, write_pcurves=False)

        # Export the assembly to VRML
        if enable_vrml:
            cq.exporters.assembly.exportVRML(component, os.path.join(output_dir, model + ".wrl"), tolerance=cq_globals.VRML_DEVIATION, angularTolerance=cq_globals.VRML_ANGULAR_DEVIATION)

        # Update the license
        from _tools import add_license
        add_license.addLicenseToStep(output_dir, model + ".step",
                                        add_license.LIST_int_license,
                                        add_license.STR_int_licAuthor,
                                        add_license.STR_int_licEmail,
                                        add_license.STR_int_licOrgSys,
                                        add_license.STR_int_licPreProc)