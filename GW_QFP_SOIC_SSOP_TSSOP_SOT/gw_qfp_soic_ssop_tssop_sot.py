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
#* Copyright (c) 2015                                                       *
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

from math import tan, radians, sqrt
import cadquery as cq

max_cc1 = 1
color_pin_mark = False
place_pinMark = True

def make_gw(params):
    c  = params['c']
    the  = params['the']
    tb_s  = params['tb_s']
    ef  = params['ef']
    cc1 = params['cc1']
    fp_s = params['fp_s']
    fp_r  = params['fp_r']
    fp_d  = params['fp_d']
    fp_z  = params['fp_z']
    R1  = params['R1'] if 'R1' in params else None
    R2  = params['R2']
    S  = params['S'] if 'S' in params else None
    L = params['L'] if 'L' in params else None
    D1  = params['D1']
    E1  = params['E1']
    E   = params['E']
    A1  = params['A1']
    A2  = params['A2']
    b   = params['b']
    e   = params['e']
    npx = params['npx']
    npy = params['npy']

    if params['excluded_pins']:
        excluded_pins = params['excluded_pins']
    else:
        excluded_pins=() ##no pin excluded

    missingparam = [S, L, R1].count(None)
    if missingparam == 0:
        print("Warning: All of S, L, and R1 are provided. The system is overconstrained. Ignoring the value of S.")
        S = None
    if missingparam > 1:
        raise Exception("At least two of S, L, and R1 must be provided")

    if L is None:
        L = (E - E1) / 2 - (S + R1)
    if S is None:
        S = (E - E1) / 2 - (R1 + L)
    if R1 is None:
        R1 = (E - E1) / 2 - (S + L)

    if L<0:
        raise Exception("L cannot be negative")
    if S<0:
        raise Exception("S cannot be negative")
    if R1<0:
        raise Exception("R1 cannot be negative")
    if L<(c+R2):
        raise Exception("L must be greater than c + R1")

    A = A1 + A2
    A2_t = (A2-c)/2 # body top part height
    A2_b = A2_t     # body bottom part height
    D1_b = D1-2*tan(radians(the))*A2_b # bottom width
    E1_b = E1-2*tan(radians(the))*A2_b # bottom length
    D1_t1 = D1-tb_s # top part bottom width
    E1_t1 = E1-tb_s # top part bottom length
    D1_t2 = D1_t1-2*tan(radians(the))*A2_t # top part upper width
    E1_t2 = E1_t1-2*tan(radians(the))*A2_t # top part upper length

    epad_rotation = 0.0
    epad_offset_x = 0.0
    epad_offset_y = 0.0

    if params['epad']:
        #if isinstance(params.epad, float):
        if not isinstance(params['epad'], list):
            sq_epad = False
            epad_r = params['epad']
        else:
            sq_epad = True
            D2 = params['epad'][0]
            E2 = params['epad'][1]
            if len(params['epad']) > 2:
                epad_rotation = params['epad'][2]
            if len(params['epad']) > 3:
                if isinstance (params['epad'][3], str):
                    if params['epad'][3] == '-topin':
                        epad_offset_x = (D1_b/2-D2/2) * -1
                    elif params['epad'][3] == '+topin':
                        epad_offset_x = D1_b/2-D2/2
                else:
                    epad_offset_x = params['epad'][3]
            if len(params['epad']) > 4:
                if isinstance (params['epad'][4], str):
                    if params['epad'][4] == '-topin':
                        epad_offset_y = (E1_b/2-E2/2) * -1
                    elif params['epad'][4] == '+topin':
                        epad_offset_y = E1_b/2-E2/2
                else:
                    epad_offset_y = params['epad'][4]

    # calculate chamfers
    totpinwidthx = (npx-1)*e+b # total width of all pins on the X side
    totpinwidthy = (npy-1)*e+b # total width of all pins on the Y side

    if cc1!=0:
        cc1 = abs(min((D1-totpinwidthx)/2., (E1-totpinwidthy)/2.,cc1) - 0.5*tb_s)
        cc1 = min(cc1, max_cc1)

    cc=cc1

    def crect(wp, rw, rh, cv1, cv):
        """
        Creates a rectangle with chamfered corners.
        wp: workplane object
        rw: rectangle width
        rh: rectangle height
        cv1: chamfer value for 1st corner (lower left)
        cv: chamfer value for other corners
        """
        points = [
        #    (-rw/2., -rh/2.+cv1),
            (-rw/2., rh/2.-cv),
            (-rw/2.+cv, rh/2.),
            (rw/2.-cv, rh/2.),
            (rw/2., rh/2.-cv),
            (rw/2., -rh/2.+cv),
            (rw/2.-cv, -rh/2.),
            (-rw/2.+cv1, -rh/2.),
            (-rw/2., -rh/2.+cv1)
        ]
        #return wp.polyline(points)
        return wp.polyline(points, includeCurrent=True).wire() #, forConstruction=True)

    if cc1!=0:
        case = cq.Workplane(cq.Plane.XY()).workplane(centerOption="CenterOfMass", offset=A1).moveTo(-D1_b/2., -E1_b/2.+(cc1-(D1-D1_b)/4.))
        case = crect(case, D1_b, E1_b, cc1-(D1-D1_b)/4., cc-(D1-D1_b)/4.)  # bottom edges
        #show(case)
        case = case.pushPoints([(0,0)]).workplane(centerOption="CenterOfMass", offset=A2_b).moveTo(-D1/2, -E1/2+cc1)
        case = crect(case, D1, E1, cc1, cc)     # center (lower) outer edges
        #show(case)
        case = case.pushPoints([(0,0)]).workplane(centerOption="CenterOfMass", offset=c).moveTo(-D1/2,-E1/2+cc1)
        case = crect(case, D1,E1,cc1, cc)       # center (upper) outer edges
        #show(case)
        #case=cq.Workplane(cq.Plane.XY()).workplane(offset=c).moveTo(-D1_t1/2,-E1_t1/2+cc1-(D1-D1_t1)/4.)
        case=case.pushPoints([(0,0)]).workplane(centerOption="CenterOfMass", offset=0).moveTo(-D1_t1/2,-E1_t1/2+cc1-(D1-D1_t1)/4.)
        case = crect(case, D1_t1,E1_t1, cc1-(D1-D1_t1)/4., cc-(D1-D1_t1)/4.) # center (upper) inner edges
        #show(case)
        #stop
        cc1_t = cc1-(D1-D1_t2)/4. # this one is defined because we use it later
        case = case.pushPoints([(0,0)]).workplane(centerOption="CenterOfMass", offset=A2_t).moveTo(-D1_t2/2,-E1_t2/2+cc1_t)
        #cc1_t = cc1-(D1-D1_t2)/4. # this one is defined because we use it later
        case = crect(case, D1_t2,E1_t2, cc1_t, cc-(D1-D1_t2)/4.) # top edges
        #show(case)
        case = case.loft(ruled=True)
        if ef!=0:
            try:
                case = case.faces(">Z").fillet(ef)
            except Exception as exeption:
                print("Case top face failed failed.\n")
                print('{:s}\n'.format(exeption))


    else:
        case = cq.Workplane(cq.Plane.XY()).workplane(centerOption="CenterOfMass", offset=A1).rect(D1_b, E1_b). \
            workplane(centerOption="CenterOfMass", offset=A2_b).rect(D1, E1).workplane(centerOption="CenterOfMass", offset=c).rect(D1,E1). \
            rect(D1_t1,E1_t1).workplane(centerOption="CenterOfMass", offset=A2_t).rect(D1_t2,E1_t2). \
            loft(ruled=True)
        if ef!=0:
            try:
                case = case.faces(">Z").fillet(ef)
            except Exception as exeption:
                print("Case top face failed failed.\n")
                print('{:s}\n'.format(exeption))



        # fillet the corners
        if ef!=0:
            BS = cq.selectors.BoxSelector
            try:
                case = case.edges(BS((D1_t2/2, E1_t2/2, 0), (D1/2+0.1, E1/2+0.1, A2))).fillet(ef)
            except Exception as exeption:
                print("Case fillet 1 failed\n")
                print('{:s}\n'.format(exeption))

            try:
                case = case.edges(BS((-D1_t2/2, E1_t2/2, 0), (-D1/2-0.1, E1/2+0.1, A2))).fillet(ef)
            except Exception as exeption:
                print("Case fillet 2 failed\n")
                print('{:s}\n'.format(exeption))

            try:
                case = case.edges(BS((-D1_t2/2, -E1_t2/2, 0), (-D1/2-0.1, -E1/2-0.1, A2))).fillet(ef)
            except Exception as exeption:
                print("Case fillet 3 failed\n")
                print('{:s}\n'.format(exeption))

            try:
                case = case.edges(BS((D1_t2/2, -E1_t2/2, 0), (D1/2+0.1, -E1/2-0.1, A2))).fillet(ef)
            except Exception as exeption:
                print("Case fillet 4 failed\n")
                print('{:s}\n'.format(exeption))

    #fp_s = True
    if fp_r == 0:
            global place_pinMark
            place_pinMark=False
            fp_r = 0.1
    if fp_s == False:
        pinmark = cq.Workplane(cq.Plane.XY()).workplane(centerOption="CenterOfMass", offset=A).box(fp_r, E1_t2-fp_d, fp_z*2) #.translate((E1/2,0,A1)).rotate((0,0,0), (0,0,1), 90)
        #translate the object
        pinmark=pinmark.translate((-D1_t2/2+fp_r/2.+fp_d/2,0,0)) #.rotate((0,0,0), (0,1,0), 0)
    else:
        # first pin indicator is created with a spherical pocket

        sphere_r = (fp_r*fp_r/2 + fp_z*fp_z) / (2*fp_z)
        sphere_z = A + sphere_r * 2 - fp_z - sphere_r
        # Revolve a cylinder from a rectangle
        # Switch comments around in this section to try the revolve operation with different parameters
        ##cylinder =
        #pinmark=cq.Workplane("XZ", (-D1_t2/2+fp_d+fp_r, -E1_t2/2+fp_d+fp_r, A)).rect(sphere_r/2, -fp_z, False).revolve()
        pinmark=cq.Workplane("XZ", (-D1_t2/2+fp_d+fp_r, -E1_t2/2+fp_d+fp_r, A)).rect(fp_r/2, -fp_z, False).revolve()

    if (color_pin_mark==False) and (place_pinMark==True):
        case = case.cut(pinmark)

    # calculated dimensions for pin
    R1_o = R1+c # pin upper corner, outer radius
    R2_o = R2+c # pin lower corner, outer radius

    # Create a pin object at the center of top side.
    bpin = cq.Workplane("YZ", (0,E1/2,0,)). \
        moveTo(-tb_s, A1+A2_b). \
        line(S+tb_s, 0). \
        threePointArc((S+R1/sqrt(2), A1+A2_b-R1*(1-1/sqrt(2))),
                      (S+R1, A1+A2_b-R1)). \
        line(0, -(A1+A2_b-R1-R2_o)). \
        threePointArc((S+R1+R2_o*(1-1/sqrt(2)), R2_o*(1-1/sqrt(2))),
                      (S+R1+R2_o, 0)). \
        line(L-R2_o, 0). \
        line(0, c). \
        line(-(L-R2_o), 0). \
        threePointArc((S+R1+R2_o-R2/sqrt(2), c+R2*(1-1/sqrt(2))),
                      (S+R1+R2_o-R1, c+R2)). \
        lineTo(S+R1+c, A1+A2_b-R1). \
        threePointArc((S+R1_o/sqrt(2), A1+A2_b+c-R1_o*(1-1/sqrt(2))),
                      (S, A1+A2_b+c)). \
        line(-S-tb_s, 0).close().extrude(b).translate((-b/2,0,0))

    pins = []
    pincounter = 1
    first_pos_x = (npx-1)*e/2
    for i in range(npx):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_x-i*e, 0, 0)).\
                rotate((0,0,0), (0,0,1), 180)
            pins.append(pin)
        pincounter += 1

    first_pos_y = (npy-1)*e/2
    for i in range(npy):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_y-i*e, (D1-E1)/2, 0)).\
                rotate((0,0,0), (0,0,1), 270)
            pins.append(pin)
        pincounter += 1

    for i in range(npx):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_x-i*e, 0, 0))
            pins.append(pin)
        pincounter += 1

    for i in range(npy):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_y-i*e, (D1-E1)/2, 0)).\
                rotate((0,0,0), (0,0,1), 90)
            pins.append(pin)
        pincounter += 1

    # create exposed thermal pad if requested
    if params['epad']:
        if sq_epad:
            pins.append(cq.Workplane("XY").box(D2, E2, A1).translate((epad_offset_x,epad_offset_y,A1/2)).rotate((0,0,0), (0,0,1), epad_rotation))
        else:
            #epad = cq.Workplane("XY", (0,0,A1/2)). \
            epad = cq.Workplane("XY"). \
            circle(epad_r). \
            extrude(A1)#.translate((0,0,A1/2))
            #extrude(A1+A1/10)
            pins.append(epad)
    # merge all pins to a single object
    merged_pins = pins[0]
    for p in pins[1:]:
        merged_pins = merged_pins.union(p)
    pins = merged_pins

    # extract pins from case
    case = case.cut(pins)

    return (case, pins, pinmark)
