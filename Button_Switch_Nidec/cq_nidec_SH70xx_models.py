#!/usr/bin/python
# -*- coding: utf8 -*-  
#

#****************************************************************************
#*                                                                          *
#* class for generating generic parameters for rotary coded switches        *
#* type Nidec SH-7000                                                       *
#*                                                                          *
#* This is part of FreeCAD & cadquery tools                                 *
#* to export generated models in STEP & VRML format.                        *
#*   Copyright (c) 2020                                                     *
#* Mountyrox   https://github.com/mountyrox                                 *
#*                                                                          *
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

import cadquery as cq
# from Helpers import show

# import ImportGui
# import FreeCAD #, Draft, FreeCADGui
# #import ImportGui
# import FreeCADGui


from math import sin, tan, cos, radians
# import os
# import glob

## base parametes & model

from .cq_base_model import PartBase, Polyline
from .cq_parameters import CodeFormat
from .cq_parameters import CodeFormat, ShapeOfTerminal
# from cq_base_parameters import CaseType
# from cq_parameters import partParams, CodeFormat, ShapeOfTerminal

## model generator

#
# Dimensions and style is from NIDEC COPAL ELECTRONICS GmbH:
# https://www.nidec-copal-electronics.com/e/catalog/switch/sh-7000.pdf
#
# NOTE: some are taken from on screen measurements
#

class PolylineExt (Polyline):
    r"""A class for creating a polyline wire (including RadiusArc) using **relative** moves (turtle graphics style)

    Additional function: `addRadiusArc(x, y, radius)`

    Overridden function: `make()`

    :param  plane: the workplane to add the polyline (as a wire)
    :type   plane: ``workplane``
    :param origin: point
    :type  origin: ``point``

    Most of the methods returns a reference to the class instance (self) which allows method chaining
    """

    def addRadiusArc(self, x, y, radius):
        r"""Adds an arc to the polygon wire.

        :param  x: the x coordinate of the starting point of the arc
        :type   x: ``float``
        :param  y: the y coordinate of the starting point of the arc
        :type   y: ``float``
        :param radius: radius of the arc
        :type  radius: ``float``

        :rtype: ``self``
        """
        self.x += x
        self.y += y
        self.commands.append((3, self.x, self.y, radius))

        return self

    def make(self):
        r""" Closes the polyline and creates a wire in the supplied plane
        Overrides the make function from base class Polyline.

        :rtype: ``wire``
        """
        plane = self.plane

        for point in self.commands:
            if point[0] == 0:
                plane = plane.moveTo(point[1], point[2])
            elif point[0] == 1:
                plane = plane.lineTo(point[1], point[2])
            elif point[0] == 2:
                plane = plane.threePointArc((point[3], point[4]), (point[1], point[2]))
            elif point[0] == 3:
                plane = plane.radiusArc((point[1], point[2]), point[3]) 

        return plane.wire() if self._is_equal(self.origin, (self.commands[-1])[1:3]) else plane.close().wire()


class PartBaseExt (PartBase):
    r"""Extended base class for model creation, to be subclassed, derived from PartBase

    .. document private functions
    .. automethod:: _make_angular_gullwing_pin
    """

    def _make_angular_gullwing_pin(self, pin_height, bottom_length, params, pin_angle=65.0, r_upper_i=None, r_lower_i=None):
        """ create an angular gull wing pin

        The pin will be placed at coordinate 0, 0 and with the base at Z = 0

        :param pin_height: overall pin height (measured from upper leg bottom to lower leg bottom)
        :type pin_height: ``float``
        :param bottom_length: bottom length of gullwing pin (measured from end of pin to begin of arc)
        :type bottom_length: ``float``
        :param pin_angle: angle between horizontal and mid part of pin (for vertical bent pin angle is 90 deg).
                          Minimum angle is 20 deg, lower angles will be set to default (65 deg)
        :type pin_angle: ``float``
        :rtype: ``solid``
        """

        # r_upper_i - pin upper corner, inner radius
        # r_lower_i - pin lower corner, inner radius
        # bottom_length - pin bottom flat part length (excluding corner arc)

        if r_lower_i is None:
            r_lower_i = params['pin_thickness'] / 2.0 if r_upper_i is None else r_upper_i

        if r_upper_i is None:
            r_upper_i = params['pin_thickness'] / 2.0

        if pin_angle <= 20.0:
             pin_angle = 65.0

        ca = cos(radians (pin_angle))
        sa = sin(radians (pin_angle))

        r_upper_o = r_upper_i + params['pin_thickness'] # pin upper corner, outer radius
        r_lower_o = r_lower_i + params['pin_thickness'] # pin lower corner, outer radius
        
        # The bottom length given to the function is the length from half the outer bend radius to end of pin.
        # The straight part has to be removed by this half outer bend radius.
        bottom_length = params['pin_bottom_length'] - (r_lower_o  * sin(radians (pin_angle/2.0)))
        top_length = params['pin_length'] - bottom_length - (r_upper_i + r_lower_o) * sa - (pin_height - (r_upper_i + r_lower_o) * (1.0 - ca))/tan(radians (pin_angle))
        if top_length < 0:
            self.say('\n###: Combination of pin length and pin angle not possible. Pin angle will be set to 90 deg')
            top_length = params['pin_length'] - bottom_length - (r_upper_i + r_lower_o)
            ca = 0.0
            sa = 1.0

        vert_center_length = pin_height - (r_upper_i + r_lower_o) * (1.0 - ca)  # vertical length of middle part of pin
        hor_center_length = params['pin_length'] - bottom_length - top_length - (r_upper_i + r_lower_o) * sa   # horizontal length of middle part of pin
        

        return PolylineExt(cq.Workplane("YZ"), origin=(0, pin_height))\
                          .addPoint(top_length, 0)\
                          .addRadiusArc(r_upper_i * sa, -r_upper_i * (1.0 - ca), r_upper_i)\
                          .addPoint(hor_center_length, -vert_center_length)\
                          .addRadiusArc(r_lower_o * sa, -r_lower_o * (1.0 - ca), -r_lower_o)\
                          .addPoint(bottom_length, 0)\
                          .addPoint(0, params['pin_thickness'])\
                          .addPoint(-bottom_length, 0)\
                          .addRadiusArc(-r_lower_i * sa, r_lower_i * (1.0 - ca), r_lower_i)\
                          .addPoint(-hor_center_length, vert_center_length)\
                          .addRadiusArc(-r_upper_o * sa, r_upper_o * (1.0 - ca), -r_upper_o)\
                          .addPoint(-top_length, 0).make().extrude(params['pin_width']).translate((-params['pin_width'] / 2.0, 0, 0))



class buttonSwitchBody(): #partParams):
    r"""Class for creating the 3D model housing (without pins) of rotary coded switch.

    :param varParams: Member ``Params`` of class ``PartParametersBase->variableParams.Params`` containing the variable parameter for building the different 3D models
    :type  varParams: ``variableParams.Param``
    """

    def __init__(self, params):
        self.params = params
        # partParams.__init__(self, varParams)


    def __pocketCenterHoleBottom (self):
        return cq.Workplane("XY").circle(self.params['bottom_center_hole_dia']/2.0).extrude(self.params['bottom_pocket_depth'])

    def __pocketEdgePinBottom (self):
        return cq.Workplane("XY")\
                 .rect((self.params['body_length_without_pads'] - self.params['pocket_edge_pin_length']), (self.params['body_width'] - self.params['pocket_edge_pin_width']), forConstruction=True) \
                 .vertices().rect(self.params['pocket_edge_pin_length'], self.params['pocket_edge_pin_width']).extrude(self.params['bottom_pocket_depth'])

    def __pocketMidPinBottom (self):                                     
        return cq.Workplane("XY")\
                 .moveTo(0.0,(self.params['body_width'] - self.params['pocket_edge_pin_width'])/2.0).lineTo(0.0,-(self.params['body_width'] - self.params['pocket_edge_pin_width'])/2.0)\
                 .vertices().rect(self.params['pocket_mid_pin_length'], self.params['pocket_edge_pin_width']).extrude(self.params['bottom_pocket_depth'])


    def __padsSide (self):
        pocket = cq.Workplane("XY", origin=((self.params['body_length_without_pads'] + self.params['pad_side_length']) / 2.0, (self.params['body_width'] - self.params['pad_side_width'])/2.0, self.params['body_height'] - self.params['pad_side_height']))\
                    .rect(self.params['pad_side_length'], self.params['pad_side_width']).extrude(self.params['pad_side_height'])\
                    .edges(">X").edges("|Z").fillet(0.2)
        return pocket.union(pocket.mirror("YZ"))
    
    def __pocketTurnInset (self):   
        return cq.Workplane("XY", origin=((0.0, 0.0, self.params['body_height'])))\
                 .circle(self.params['turn_inset_dia']/2.0).extrude(-self.params['pocket_turn_inset_top_depth'])


    def __pocketsTopSide (self):
        pocket = cq.Workplane("XY", origin=((0.0, (self.params['body_width'] - self.params['pocket_top_side_width'])/2.0, self.params['body_height'])))\
                    .rect(self.params['body_length'], self.params['pocket_top_side_width']).extrude(-self.params['pocket_top_side_width'])
        return pocket.union(pocket.mirror("XZ"))
    

    def makePlasticBody (self, params):
        """ create the plastic body of rotary coded switch
        :rtype: ``solid``
        """
        body = cq.Workplane("XY")\
                 .rect(params['body_length_without_pads'], params['body_width']).extrude(params['body_height'])\
                 .edges("<Y").edges("|Z").fillet(0.1)

        body = body.union(self.__padsSide(), body)\
                 .edges(">Y").edges("|Z").fillet(0.1)\
                 .edges(">Z").fillet(0.1)

        # edgeFilter = '<({0:5.2f}, 0.0, 0.0)'.format(-(self.body_length/2.0-0.1))

        body = body.cut(self.__pocketCenterHoleBottom())\
                   .cut(self.__pocketEdgePinBottom())\
                   .cut(self.__pocketMidPinBottom())\
                   .cut(self.__pocketTurnInset())\
                   .cut(self.__pocketsTopSide())\

        return body.translate((0.0, 0.0, self.params['body_board_distance']))

    def makeTurnInset (self, params):
        """ create the tunn inset of rotary coded switch
        :rtype: ``solid``
        """
        body = cq.Workplane("XY")\
                 .circle(self.params['turn_inset_dia']/2.0).extrude(self.params['turn_inset_height'])

        arrow = Polyline (cq.Workplane("XY"))\
            .addMoveTo(-(self.params['arrowshaft_length'] + self.params['arrowhead_length'])/2.0, -self.params['arrowshaft_height']/2.0)\
            .addPoint(0.0, self.params['arrowshaft_height'])\
            .addPoint(self.params['arrowshaft_length'], 0.0)\
            .addPoint(0.0, self.params['arrow_barb_height'])\
            .addPoint(self.params['arrowhead_length'], -self.params['arrowhead_height'])\
            .addPoint(-self.params['arrowhead_length'], -self.params['arrowhead_height'])\
            .addPoint(0.0, self.params['arrow_barb_height'])\
            .addPoint(-self.params['arrowshaft_length'], 0.0)\
            .make().extrude(-self.params['arrow_pocket_depth']).translate((0.0, 0.0, self.params['turn_inset_height']))
        
        body = body.cut(arrow)

        return body.translate((0.0, 0.0, self.params['body_height']-self.params['pocket_turn_inset_top_depth'] + self.params['body_board_distance']))

    def __pocketCoverEdges (self):
        # length of polygon edges. Minimum is cover thickness, maximum is 1/2 .
        # We take the mean:
        c = (self.params['cover_thickness'] + self.params['pad_side_width']/2.0) / 2.0
        # The last variable diagonal line will be created when closing the polygon.
        pocket = Polyline (cq.Workplane("XY"))\
            .addMoveTo(self.params['body_length'] / 2.0 - self.params['pad_side_width'] + c, self.params['body_width'] /2.0 - c)\
            .addPoint(-c, 0.0)\
            .addPoint(0.0, c)\
            .addPoint(self.params['pad_side_width'], 0.0)\
            .addPoint(0.0, -self.params['pad_side_width'])\
            .addPoint(-c, 0.0)\
            .addPoint(0.0, c)\
            .make().extrude(self.params['body_height'])

        pocket = pocket.union(pocket.mirror("YZ"))
        return pocket.union(pocket.mirror("XZ"))

    def __pocketCoverSideClip (self):
        pocket = cq.Workplane("XY").box(self.params['body_length'], self.params['cover_side_pocket_width'], self.params['cover_side_pocket_height'])\
            .translate((0.0, 0.0, self.params['cover_height'] - self.params['cover_thickness'] - self.params['cover_side_pocket_height']/2.0))
        return pocket

    def makeCoverPlate (self, params):
        """ create the outer metal frame of rotary coded switch
        :rtype: ``solid``
        """
        body = cq.Workplane("XY")\
                 .rect(self.params['body_length'], self.params['body_width'])\
                 .circle(self.params['turn_inset_dia']/2.0)\
                 .extrude(self.params['cover_height'])\
                 .edges(">Z").edges("|X").fillet(0.25)\
                 .edges(">Z").edges("|Y").fillet(0.25)\
                 .edges(">Z").fillet(0.05)

        pocket = cq.Workplane("XY")\
                 .rect(self.params['body_length'] - self.params['cover_thickness'] * 2.0, self.params['body_width'] - self.params['cover_thickness'] * 2.0)\
                 .extrude(self.params['cover_height'] - self.params['cover_thickness'])\

        body = body.cut(pocket).cut(self.__pocketCoverEdges())\
                 .cut(cq.Workplane("XY").box(self.params['body_length'] - 2.0 * self.params['cover_thickness'], self.params['body_width'], (self.params['body_height'] - self.params['pad_side_height'])*2.0))\
                 .cut(self.__pocketCoverSideClip())\
                 .faces("<Z").edges("|X").chamfer(0.5)

        return body.translate((0.0, 0.0, self.params['body_height'] - self.params['cover_height'] + self.params['cover_thickness'] + self.params['body_board_distance']))

    # TODO when CADQuery 2.x is available in FreeCAD
    def makeNumberRing (self, params):
        """ create the ring with numbers (0..9) on cover frame of rotary coded switch. This function can be implemented not before CADQuery version 2 or higher
        is available within FreeCAD.
        :rtype: ``solid``
        """
        ring = cq.Workplane("XY")\
            .text("0", params['number_font_size'], 1.0)

        return ring

    # def importNumberRing10(self, modelName):
    #     """ imports a step file of the ring with numbers (0..9) for the rotary coded switch
    #     :rtype: ``solid``
    #     """
    #     cwd = os.path.dirname(os.path.realpath(__file__)) + "/NumberRing10.step"

    #     # ImportGui.insert(cwd, modelName)

    #     tmp = FreeCAD.ActiveDocument.Objects[-1]
    #     tmp.Placement=\
    #                 FreeCAD.Placement(FreeCAD.Vector(0, 0, self.body_height + self.cover_thickness + self.body_board_distance), FreeCAD.Rotation(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,0)))
    #     #App.Placement(App.Vector(0,0,5), App.Rotation(App.Vector(0,0,1),0), App.Vector(0,0,0))
    #     d = os.path.dirname(os.path.realpath(__file__)) + "/NumberRing10.step"


class switchNidecSH70x0x(PartBaseExt): # , partParams):
    r"""A class for creating the 3D model of rotary coded switches of different types.

    :param parameter: Member ``Params`` of class ``PartParametersBase->variableParams.Params`` containing the variable parameter for building the different 3D models
    :type  parameter: ``variableParams.Params``

    """
    #default_model = ""

    def __init__(self, parameter=None):
        pass

    #     PartBase.__init__(self, parameter)
    #     partParams.__init__(self, parameter)
    #     self.modelBody = buttonSwitchBody(parameter)

    #     # set params to 
    #     self.licAuthor = "Joerg Laukemper"
    #     self.licEmail = "https://github.com/MountyRox"
    #     if parameter.terminal_shape == ShapeOfTerminal.TH:
    #         self.destination_dir = "Button_Switch_THT.3dshapes"  
    #         self.footprints_dir = "Button_Switch_THT.pretty" 
    #     else:
    #         self.destination_dir = "Button_Switch_SMD.3dshapes"  
    #         self.footprints_dir = "Button_Switch_SMD.pretty" 

        # CheckedmodelName is the model name with following replacements: replace('.', '').replace('-', '_').replace('(', '').replace(')', '')
        # Necessary because FreeCAD does not like these character in a file name, but KiCAD often use these character in names of footprints
        # self.CheckedmodelName = None

        # make_me = True is the default value (inherited from PartBase). Must only be overridden if it should be False
        # self.make_me = True


        # Append the existing list from PartBase = self.color_keys = ["black body", "metal grey pins"] ...
        #self.color_keys.append("white body")   # buttons
        #self.color_keys.append("white body")   # pin mark
        # or define a complete new list self.color_keys = ["black body", "metal grey pins", "white body", "white body"].
        # However, the order of materials must correspont to the calls of show (..) in self.make()

        #                   v plastik body  v turn inset  v metallic cover   v pins             v numer ring
        # self.color_keys = ["black body",   "white body", "metal grey pins", "metal grey pins", "black body"]
    
    def _duplicatePins (self, onePin, params, codeFormat=CodeFormat.REAL, noPins=None, pitch=None):
        r"""Duplicates all pins from first pin.

        :param onePin: The first pin of the model
        :type  onePin: ``solid``

        :param codeFormat:
        :type  codeFormat: ``CodeFormat`` default: ``CodeFormat.REAL``

        :rtype: ``solid`` of all pins
        """

        if noPins is None:
            noPins = params['num_pins']
        if pitch is None:
            pitch = params['pin_pitch']

        m = noPins // 2
        pins = [onePin]       
        for i in range (1, noPins):
            nextPin = (onePin.translate((-pitch * (i % m), 0, 0)))
            nextPin = nextPin.rotate ((0,0,0), (0,0,1), 180.0 * (i // m))
            if not(i == 4 and codeFormat==CodeFormat.GRAY): 
                pins.append(nextPin)
        return self._union_all(pins)

    def _makeGwPin (self, params):
        return self._make_angular_gullwing_pin (params['pin_height'], params['pin_bottom_length'], params)

    def _makeJhPin (self, params):
        return self._make_Jhook_pin(params)

    def _makeThPin (self, params):
        return self._make_angled_pin (params, params['pin_height'], params['pin_top_length'], 0.0, 'THT')\
            .rotate ((0,0,0), (1,0,0), -90.0)\
            .translate ((0.0, 0.0, params['pin_z_shift']))

    _pinStyleSwitcher = {
        ShapeOfTerminal.GW: _makeGwPin,
        ShapeOfTerminal.JH: _makeJhPin,
        ShapeOfTerminal.TH: _makeThPin
        }


    def makePins (self, params):
        r"""Creates all pins of the rotary coded switch, depending on the ``code_format`` and ``terminal_shape`` defined in ``parameter``.
        :rtype: ``solid`` of all pins
        """
        # get the function from switcher dictionary making the pin defined by the terminal_shape key
        firstPin = self._pinStyleSwitcher.get(params['terminal_shape'])(self, params)
        pins = self._duplicatePins(firstPin.translate(params['first_pin_pos']), params, codeFormat=params['code_format'])
        return pins 

    def makeModelName(self, genericName):
        r"""Create the name of the body, corresponding to the name given in the KiCAD footprint.

        :param genericName: The name of the model, generally the value of class member default_model
        :type  genericName: ``str``

        :rtype: ``str``
        """
        modelName = ("Nidec_Copal_SH-" + genericName)
        self.CheckedmodelName = modelName.replace('.', '').replace('-', '_').replace('(', '').replace(')', '')
        return modelName


    #def make(self, freeCadDocName):
    def make(self, params):
        r"""Create the 3D model of the rotary coded switch and brings it on the FreeCAD screen
        """
        modelBody = buttonSwitchBody(params)

	    # Each show creates a part in FreeCAD and this part will be given a material color, within the method cq_model_generator.makeModel(...). 
		# For this reason there must be a list called color_keys[]. This list is defined in cq_base_model, with two entries, 
		#   one for the body material, one for the pin material. If this is not sufficient this list must be overridden by all classes 
		#   derived from cq_base_model. The number of entries must match the number of calling show()!!
        body = modelBody.makePlasticBody(params)
        inset = modelBody.makeTurnInset(params)
        plate = modelBody.makeCoverPlate(params)
        pins = self.makePins(params)
        ring = modelBody.makeNumberRing(params)
        # if self.CheckedmodelName is not None:
        #     ring = self.modelBody.importNumberRing10 (self.CheckedmodelName)

        return (body, inset, plate, pins, ring)

        
