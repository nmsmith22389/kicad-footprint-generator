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

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","tools")) # load kicad_mod path


#
# This module Create a standard box in various layers including a pin 1 marker tap or chamfer
#
from KicadModTree import *
from KicadModTree.Point import *
from KicadModTree.PolygonPoints import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Text import Text

from drawing_tools import *

class koaLine:

    def __init__(self, sx, sy, ex, ey, layer, width):
        self.sx = round(sx, 6)
        self.sy = round(sy, 6)
        self.ex = round(ex, 6)
        self.ey = round(ey, 6)
        self.k = 0.0
        self.m = 0.0
        self.l = 0.0
        self.IsVertical = False
        self.layer = layer
        self.width = width

        if ex != sx:
            self.k = round((ey - sy) / (ex - sx), 6)
            self.m = round(sy - (self.k * sx), 6)
        else:
            self.IsVertical = True

        #
        # Get the line length
        #
        x1 = min(self.sx, self.ex)
        x2 = max(self.sx, self.ex)
        y1 = min(self.sy, self.ey)
        y2 = max(self.sy, self.ey)

        x1 = round(x2 - x1, 6)
        y1 = round(y2 - y1, 6)

        self.l = round(sqrt((x1 * x1) + (y1 * y1)),6)


class StandardBox(Node):
    r"""Add a Polygon Line to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *footprint* (``list(Point)``) --
          The foot print
        * *description* (``str``) --
          The description
        * *datasheet* (``str``) --
          The url to the data sheet
        * *at* (``Point``) --
          Where is upper left corner, in Cartesian coordinate system (minus y below x axis)
        * *size* (``Point``) --
          The width and height of the rectangle
        * *tags* (``str``) --
          A footprints tag attribute
        * *extratexts* (``list(x, y, 'text', layer, sizex, sizey)``) --
          A list of extra txts to be placed on the footprint
        * *pins* (``list(type, number, x, y, sizex, sizey, drill)``) --
          List of THT/SMD/NPTH holes
        * *courtyard_clearance* (``Vector2D``) --
          Clearance between nominal body rectangle and courtyard outline in each axis (default (0.25, 0.25))
        * *fab_to_silk_clearance* (``Vector2D``) --
          Clearance between the edge of the fab line and edge of the silk line in each axis (default: (0, 0))
        * *file3Dname* (``str``) --
          The path to the 3D model name

    :Example:

    #
    # pycodestyle complain over long lines so the complete on is placed in a comment instead
    #
    # StandardBox(footprint=f, description=description, datasheet=datasheet, at=at, size=size, tags=fptag,
    # extratexts=extratexts, pins=pins, file3Dname = "${KICAD8_3DMODEL_DIR}/" + dir3D + "/" + footprint_name + ".wrl")))
    #
    >>> from KicadModTree import *
    >>> StandardBox(footprint=f, description=description, ....)
    """

    courtyard_clearance: Vector2D
    fab_silk_clearance: Vector2D

    def __init__(self, **kwargs):
        Node.__init__(self)

        default_ipc_courtyard_mm = 0.25

        self.courtyard_clearance = kwargs.get('courtyard_clearance', Vector2D(
            default_ipc_courtyard_mm, default_ipc_courtyard_mm))

        # By default fab just touches the fab outline
        self.fab_silk_clearance = kwargs.get('fab_to_silk_clearance', Vector2D(0, 0))

        self.extraffablines = kwargs.get('extraffablines')
        self.typeOfBox = str(kwargs.get('typeOfBox'))
        self.pins = kwargs.get('pins')

        self.virtual_childs = []

        self._initPosition(**kwargs)
        self._initSize(**kwargs)
        self._initFootPrint(**kwargs)

        self._initDesriptionNode(**kwargs)
        self._initTagNode(**kwargs)
        self._initFile3DNameNode(**kwargs)
        self._initExtraTextNode(**kwargs)

        #
        # Create foot print parts
        self._createPinsNode()
        self._createFFabLine()
        self._createPin1MarkerLine()
        self._createFSilkSLine()
        self._createFCrtYdLine()
        #

    def getVirtualChilds(self):
        #
        #
        return self.virtual_childs

    def _initPosition(self, **kwargs):
        if 'at' not in kwargs:
            raise KeyError('Upper left position not declared (like "at: [0,0]")')
        self.at = Point2D(kwargs.get('at'))
        self.at.y = 0.0 - self.at.y

    def _initSize(self, **kwargs):
        if 'size' not in kwargs:
            raise KeyError('Size not declared (like "size: [1,1]")')
        if type(kwargs.get('size')) in [int, float]:
            # when the attribute is a simple number, use it for x and y
            self.size = Point2D([kwargs.get('size'), kwargs.get('size')])
        else:
            size_original = kwargs.get('size')
            self.corners = []
            if len(size_original ) > 2:
                self.corners = size_original[2:]
            self.size = Point2D(size_original[0], size_original[1])

    def _createFSilkRefDesText(self):

        silk_ref_des_size = [1, 1]
        corner_pos = self._getPin1ChevronCorner()

        # No specific reason for this exact value, seems about right
        ref_des_x_inset = 2.5
        # place the silk avoiding the pin 1 marker
        silk_ref_des_pos = corner_pos + Point2D(ref_des_x_inset, -silk_ref_des_size[1] / 2 - 2 * self.FSilkSWidth)

        new_node = Text(type='reference', text='REF**', at=silk_ref_des_pos, size=silk_ref_des_size, layer='F.SilkS')
        new_node._parent = self
        return new_node

    def _initFootPrint(self, **kwargs):
        if 'footprint' not in kwargs:
            raise KeyError('footprint node is missing')

        self.footprint = kwargs.get('footprint')
        #
        self.footprint_name = self.footprint.name
        #
        self.FFabWidth = 0.10
        self.FSilkSWidth = 0.12
        self.FCrtYdWidth = 0.05
        #
        self.p1m = 3.0
        self.REF_P_w = 1.0
        self.REF_P_h = 1.0

        # Leave one line width between the lines
        self.pin1_mark_outset = Vector2D(self.FSilkSWidth, self.FSilkSWidth)

        if self.size.x < 8.0 or self.size.y < 8.0:
            dd = self.size.y / 3.0
            if self.size.x < self.size.y:
                dd = self.size.x / 3.0

            self.p1m = dd
            if dd < self.REF_P_w:
                self.REF_P_w = dd
                self.REF_P_h = self.REF_P_w

        fab_ref_des_pos = self.at + (self.size / 2)
        new_node = Text(type='user', text='${REFERENCE}', at=fab_ref_des_pos, layer='F.Fab', size=[self.REF_P_w, self.REF_P_h])
        new_node._parent = self
        self.virtual_childs.append(new_node)

        self.virtual_childs.append(self._createFSilkRefDesText())

        # Get the fab value outside both the courtyard and silk
        fab_value_y_offset = max(self.courtyard_clearance.y, self.fab_silk_clearance.y)

        fab_value_pos = Vector2D(
            self.at.x + (self.size.x / 2.0),
            self.at.y + self.size.y + fab_value_y_offset + 1.0
        )

        new_node = Text(type="value", text=self.footprint_name, at=fab_value_pos, layer="F.Fab")
        new_node._parent = self
        self.virtual_childs.append(new_node)

    def _initDesriptionNode(self, **kwargs):
        if 'description' not in kwargs:
            raise KeyError('Description not declared (like description: "Bul Holder )')
        if 'datasheet' not in kwargs:
            raise KeyError('datasheet not declared (like datasheet: http://www.bulgin.com/media/bulgin/data/Battery_holders.pdf)')
        self.description = str(kwargs.get('description')) + " (Script generated with StandardBox.py) (" + str(kwargs.get('datasheet')) + ")"
        self.footprint.setDescription(self.description)

    def _initTagNode(self, **kwargs):
        if 'tags' not in kwargs:
            raise KeyError('tags not declared (like "tags: "Bulgin Battery Holder, BX0033, Battery Type 1xPP3")')
        self.tags = str(kwargs.get('tags'))
        self.footprint.setTags(self.tags)

    def _initFile3DNameNode(self, **kwargs):
        if 'file3Dname' not in kwargs:
            raise KeyError('file3Dname not declared')
        self.file3Dname = str(kwargs.get('file3Dname'))
        self.footprint.append(Model(filename=self.file3Dname,
                                    at=[0.0, 0.0, 0.0],
                                    scale=[1.0, 1.0, 1.0],
                                    rotate=[0.0, 0.0, 0.0]))

    def _initExtraTextNode(self, **kwargs):
        if kwargs.get('extratexts'):
            self.extratexts = kwargs.get('extratexts')
            #
            for n in self.extratexts:
                at = [n[0], 0.0-n[1]]
                stss = n[2]
                new_node = Text(type="user", text=stss, at=at)
                #
                if len(n) > 3:
                    new_node.layer = n[3]
                if len(n) > 5:
                    new_node.size = Point2D([n[4], n[5]])
                new_node._parent = self
                self.virtual_childs.append(new_node)

    def _createFFabLine(self):
        ffabline = []
        self.boxffabline = []
        #
        #
        x = self.at.x
        y = self.at.y
        w = self.size.x
        h = self.size.y
        self.boxffabline.append(koaLine(x, y, x + w, y, 'F.Fab', self.FFabWidth))
        self.boxffabline.append(koaLine(x + w, y, x + w, y + h, 'F.Fab', self.FFabWidth))
        self.boxffabline.append(koaLine(x + w, y + h, x, y + h, 'F.Fab', self.FFabWidth))
        self.boxffabline.append(koaLine(x, y + h, x, y, 'F.Fab', self.FFabWidth))
        #
        # Add a chamfer
        #
        dd = w * 0.25
        if dd > 1.0:
            dd = 1.0
        if w < 2.0:
            dd = w / 3.0
        if h < 2.0:
            dd = h / 3.0
        #
        #
        x0 = x + dd
        y0 = y
        x9 = x0
        y9 = y0
        #
        x1 = x + w
        y1 = y
        x2 = x1
        y2 = y1
        #
        x3 = x + w
        y3 = y + h
        x4 = x3
        y4 = y3
        #
        x5 = x
        y5 = y + h
        x6 = x5
        y6 = y5
        #
        x7 = x
        y7 = y + dd
        x8 = x7
        y8 = y7
        #
        #
        for nn in self.corners:

            if nn[0] == 'ULP':
                x0 = x + nn[1]
                x9 = x0
                y8 = y + nn[2]
                y9 = y8
                y7 = y8
                new_node = Line(start=Point2D(x9, y9), end=Point2D(x0, y0), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)

            if nn[0] == 'ULR':
                x0 = x + nn[1]
                y7 = y + nn[1]
                x8 = x7
                x9 = x7
                y8 = y7
                y9 = y7
                new_node = Arc(center=Point2D(x0, y7), start=Point2D(x7, y7), layer='F.Fab', width=self.FFabWidth, angle=90.0)
                new_node._parent = self
                self.virtual_childs.append(new_node)


            if nn[0] == 'URP':
                x1 = (x + w) - nn[1]
                y2 = y + nn[2]
                new_node = Line(start=Point2D(x1, y1), end=Point2D(x1, y2), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)
                #
                new_node = Line(start=Point2D(x1, y2), end=Point2D(x2, y2), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)

            if nn[0] == 'URR':
                x1 = (x + w) - nn[1]
                y2 = y + nn[1]
                new_node = Arc(center=Point2D(x1, y2), start=Point2D(x1, y1), layer='F.Fab', width=self.FFabWidth, angle=90.0)
                new_node._parent = self
                self.virtual_childs.append(new_node)

            if nn[0] == 'LRP':
                x4 = (x + w) - nn[1]
                y3 = (y + h) - nn[1]
                new_node = Line(start=Point2D(x3, y3), end=Point2D(x4, y3), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)
                #
                new_node = Line(start=Point2D(x4, y3), end=Point2D(x4, y4), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)

            if nn[0] == 'LRR':
                x4 = (x + w) - nn[1]
                y3 = (y + h) - nn[1]
                new_node = Arc(center=Point2D(x4, y3), start=Point2D(x3, y3), layer='F.Fab', width=self.FFabWidth, angle=90.0)
                new_node._parent = self
                self.virtual_childs.append(new_node)

            if nn[0] == 'LLR':
                x5 = x + nn[1]
                y6 = (y + h) - nn[1]
                new_node = Arc(center=Point2D(x5, y6), start=Point2D(x5, y5), layer='F.Fab', width=self.FFabWidth, angle=90.0)
                new_node._parent = self
                self.virtual_childs.append(new_node)

            if nn[0] == 'LLP':
                x5 = x + nn[1]
                y6 = (y + h) - nn[2]
                new_node = Line(start=Point2D(x5, y5), end=Point2D(x5, y6), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)
                #
                new_node = Line(start=Point2D(x5, y6), end=Point2D(x6, y6), layer='F.Fab', width=self.FFabWidth)
                new_node._parent = self
                self.virtual_childs.append(new_node)

        ffabline.append(koaLine(x0, y0, x1, y1, 'F.Fab', self.FFabWidth))
        ffabline.append(koaLine(x2, y2, x3, y3, 'F.Fab', self.FFabWidth))
        ffabline.append(koaLine(x4, y4, x5, y5, 'F.Fab', self.FFabWidth))
        ffabline.append(koaLine(x6, y6, x7, y7, 'F.Fab', self.FFabWidth))
        ffabline.append(koaLine(x8, y8, x9, y9, 'F.Fab', self.FFabWidth))
        #
        #
        for n in ffabline:
            new_node = Line(start=Point2D(n.sx, n.sy), end=Point2D(n.ex, n.ey), layer=n.layer, width=n.width)
            if n.width < 0.0:
                new_node = Line(start=Point2D(n.sx, n.sy), end=Point2D(n.ex, n.ey), layer=n.layer)
            new_node._parent = self
            self.virtual_childs.append(new_node)

    def _getPin1ChevronCorner(self) -> Vector2D:
        main_silk_outset = self._getMainFSilkOutsetFromFabLineCentre()

        # The pin 1 is outset again from the main silk line to the left and up
        outset = self.pin1_mark_outset + main_silk_outset + self.FSilkSWidth
        return self.at - outset

    def _getMainFSilkOutsetFromFabLineCentre(self) -> Vector2D:
        # At the closest, don't overlap the fab line
        return Vector2D(
            max(self.fab_silk_clearance.x, self.FFabWidth / 2),
            max(self.fab_silk_clearance.y, self.FFabWidth / 2)
        ) + Vector2D(self.FSilkSWidth / 2, self.FSilkSWidth / 2)

    def _createPin1MarkerLine(self):
        #
        # Add pin 1 marker line
        #

        corner_pos = self._getPin1ChevronCorner()

        new_node = Line(start=corner_pos + Vector2D(0, self.p1m), end=corner_pos, layer='F.SilkS',
                        width=self.FSilkSWidth)
        new_node._parent = self
        self.virtual_childs.append(new_node)

        new_node = Line(start=corner_pos, end=corner_pos + Vector2D(self.p1m, 0), layer='F.SilkS',
                        width=self.FSilkSWidth)
        new_node._parent = self
        self.virtual_childs.append(new_node)

    def _createFSilkSLine(self):
        self.fsilksline = []

        fab_silk_outset = self._getMainFSilkOutsetFromFabLineCentre()

        # Check all holes and pads, if a pad or hole is on the silk line
        # then jump over the pad/hole
        for n in self.boxffabline:
            x1 = min(n.sx, n.ex)
            y1 = min(n.sy, n.ey)
            x2 = max(n.sx, n.ex)
            y2 = max(n.sy, n.ey)
            #
            #
            if (x1 < 0.0 and y1 < 0.0 and y2 < 0.0) or (x1 < 0.0 and y1 > 0.0 and y2 > 0.0):
                #
                # Top and bottom line
                #
                x1_t = x1 - fab_silk_outset.x
                x2_t = x2 + fab_silk_outset.x
                x3_t = x1_t
                x4_t = x2_t
                #
                if y1 < 0.0:
                    # Top line
                    y1_t = y1 - fab_silk_outset.y
                    y2_t = y2 - fab_silk_outset.y
                    y3_t = y1_t
                    y4_t = y2_t
                    #
                    for nn in self.corners:
                        if nn[0] == 'URR':
                            x2_t = x2_t - (nn[1] + fab_silk_outset.x)
                        if nn[0] == 'ULR':
                            x1_t = x1_t + (nn[1] + fab_silk_outset.x)
                        if nn[0] == 'ULP':
                            x3_t = x1_t
                            x1_t = x1_t + (nn[1])
                            y3_t = y1_t + (nn[2])
                        if nn[0] == 'URP':
                            x4_t = x2_t
                            x2_t = x2_t - (nn[1])
                            y4_t = y1_t + (nn[2])
                else:
                    # Bottom line
                    y1_t = y1 + fab_silk_outset.y
                    y2_t = y2 + fab_silk_outset.y
                    y3_t = y1_t
                    y4_t = y2_t
                    #
                    for nn in self.corners:
                        if nn[0] == 'LRR':
                            x2_t = x2_t - (nn[1] + fab_silk_outset.x)
                        if nn[0] == 'LLR':
                            x1_t = x1_t + (nn[1] + fab_silk_outset.x)
                        if nn[0] == 'LLP':
                            x3_t = x1_t
                            x1_t = x1_t + (nn[1])
                            y3_t = y1_t - (nn[2])
                        if nn[0] == 'LRP':
                            x4_t = x2_t
                            x2_t = x2_t - (nn[1])
                            y4_t = y1_t - (nn[2])

                #
                EndLine = True
                foundPad = False
                UseCorner = True
                while EndLine:
                    px1 = 10000000.0
                    px2 = 10000000.0
                    foundPad = False
                    for n in self.pad:
                        n_min_x = n.at.x - (n.size.x / 2.0)
                        n_min_y = n.at.y - (n.size.y / 2.0)
                        n_max_x = n_min_x + n.size.x
                        n_max_y = n_min_y + n.size.y
                        dd = max(0.25, n.solder_mask_margin)

                        if (n_min_y - 0.25) <= y1_t and (n_max_y + 0.25) > y1_t and n_max_x > x1_t and n_min_x < x2_t:
                            #
                            # This pad is in SilkS line's path
                            #
                            if n_min_x < px1:
                                px1 = n_min_x
                                px2 = n_max_x
                                foundPad = True
                    if foundPad:
                        #
                        # Found at least one pad that is in SilkS's line
                        #
                        if (px1 - 0.25) > x1_t:
                            #
                            # It does not cover the start point
                            #
                            self.fsilksline.append(koaLine(x1_t, y1_t, px1 - 0.25, y2_t, 'F.SilkS', self.FSilkSWidth))
                        x1_t = px2 + 0.25
                    else:
                        #
                        # No pads was in the way
                        #
                        if y1 < 0.0 and UseCorner:
                            # Top line
                            for nn in self.corners:
                                if nn[0] == 'ULR':
                                    urcdy0 = y1_t + (nn[1] + fab_silk_outset.y)
                                    urcdx1 = x1_t - (nn[1] + fab_silk_outset.x)
                                    new_node = Arc(center=Point2D(x1_t, urcdy0), start=Point2D(urcdx1, urcdy0), layer='F.SilkS', width=self.FSilkSWidth, angle=90.0)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)

                                if nn[0] == 'ULP':
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x1_t, y1_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x3_t, y3_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    #
                                if nn[0] == 'URP':
                                    urcdy0 = y4_t + (nn[2])
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x2_t, y2_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x4_t, y4_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)

                        if y1 > 0.0 and UseCorner:
                            # Bottom line
                            for nn in self.corners:
                                if nn[0] == 'LLR':
                                    urcdy0 = y1_t - (nn[1] + fab_silk_outset.y)
                                    new_node = Arc(center=Point2D(x1_t, urcdy0), start=Point2D(x1_t, y1_t), layer='F.SilkS', width=self.FSilkSWidth, angle=90.0)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)

                                if nn[0] == 'LLP':
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x1_t, y1_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x3_t, y3_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    #
                                if nn[0] == 'LRP':
                                    urcdy0 = y4_t + (nn[2])
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x2_t, y2_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x4_t, y4_t), layer='F.SilkS', width=self.FSilkSWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                        #
                        self.fsilksline.append(koaLine(x1_t, y1_t, x2_t, y2_t, 'F.SilkS', self.FSilkSWidth))
                        EndLine = False

                    if x1_t >= x2:
                        EndLine = False

                    UseCorner = False

                if not foundPad and y1 < 0:
                    #
                    for nn in self.corners:
                        if nn[0] == 'URR':
                            urcdy1 = y1_t + (nn[1] + fab_silk_outset.y)
                            new_node = Arc(center=Point2D(x2_t, urcdy1), start=Point2D(x2_t, y2_t), layer='F.SilkS', width=self.FSilkSWidth, angle=90.0)
                            new_node._parent = self
                            self.virtual_childs.append(new_node)


                if not foundPad and y1 > 0:
                    #
                    for nn in self.corners:
                        if nn[0] == 'LRR':
                            urcdx1 = x2_t + (nn[1] + fab_silk_outset.x)
                            urcdy1 = y2_t - (nn[1] + fab_silk_outset.y)
                            new_node = Arc(center=Point2D(x2_t, urcdy1), start=Point2D(urcdx1, urcdy1), layer='F.SilkS', width=self.FSilkSWidth, angle=90.0)
                            new_node._parent = self
                            self.virtual_childs.append(new_node)

            if (x1 < 0.0 and y1 < 0.0 and y2 > 0.0) or (x1 > 0.0 and y1 < 0.0 and y2 > 0.0):
                #
                # Left and right line
                #
                y1_t = y1 - fab_silk_outset.y
                y2_t = y2 + fab_silk_outset.y
                #
                if x1 < 0.0:
                    # Left line
                    x1_t = min(x1 - fab_silk_outset.x, x2 - fab_silk_outset.x)
                    x2_t = max(x1 - fab_silk_outset.x, x2 - fab_silk_outset.x)

                    for nn in self.corners:
                        if nn[0] == 'ULR':
                            y1_t = y1_t + (nn[1] + fab_silk_outset.y)
                        if nn[0] == 'LLR':
                            y2_t = y2_t - (nn[1] + fab_silk_outset.y)
                        if nn[0] == 'ULP':
                            y1_t = y1_t + (nn[2])
                        if nn[0] == 'LLP':
                            y2_t = y2_t - (nn[2])

                else:
                    # Right line
                    x1_t = min(x1 + fab_silk_outset.x, x2 + fab_silk_outset.x)
                    x2_t = max(x1 + fab_silk_outset.x, x2 + fab_silk_outset.x)

                    #
                    for nn in self.corners:
                        if nn[0] == 'URR':
                            y1_t = y1_t + (nn[1] + fab_silk_outset.y)
                        if nn[0] == 'LRR':
                            y2_t = y2_t - (nn[1] + fab_silk_outset.y)
                        if nn[0] == 'URP':
                            y1_t = y1_t + (nn[2])
                        if nn[0] == 'LRP':
                            y2_t = y2_t - (nn[2])

                #
                EndLine = True
                while EndLine:
                    py1 = 10000000.0
                    py2 = 10000000.0
                    foundPad = False

                    for n in self.pad:
                        n_min_x = n.at.x - (n.size.x / 2.0)
                        n_min_y = n.at.y - (n.size.y / 2.0)
                        n_max_x = n_min_x + n.size.x
                        n_max_y = n_min_y + n.size.y
                        dd = max(0.25, n.solder_mask_margin)

                        if (n_min_x <= x1_t) and (n_max_x > x1_t) and n_max_y > y1_t and n_min_y < y2_t:
                            #
                            # This pad is in SilkS line's path
                            #
                            if n_min_y < py1:
                                py1 = n_min_y
                                py2 = n_max_y
                                foundPad = True
                    if foundPad:
                        #
                        # Found at least one pad that is in SilkS's line
                        #
                        if (py1 - dd) > y1_t:
                            #
                            # It does not cover the start point
                            #
                            self.fsilksline.append(koaLine(x1_t, y1_t, x2_t, py1 - dd, 'F.SilkS', self.FSilkSWidth))
                        y1_t = py2 + dd
                    else:
                        #
                        # No pads was in the way
                        #
                        self.fsilksline.append(koaLine(x1_t, y1_t, x2_t, y2_t, 'F.SilkS', self.FSilkSWidth))
                        EndLine = False

                    if y1_t >= y2:
                        EndLine = False
        #
        #
        for n in self.fsilksline:
            new_node = Line(start=Point2D(n.sx, n.sy), end=Point2D(n.ex, n.ey), layer=n.layer, width=n.width)
            if n.width < 0.0:
                new_node = Line(start=Point2D(n.sx, n.sy), end=Point2D(n.ex, n.ey), layer=n.layer)
            new_node._parent = self
            self.virtual_childs.append(new_node)

    def _createFCrtYdLine(self):
        self.fcrtydline = []
        #
        #
        #
        # Check all holes and pads, if a pad or hole is on the crtyrd line
        # then jump over the pad/hole
        #
        clearance = self.courtyard_clearance

        for n in self.boxffabline:
            x1 = min(n.sx, n.ex)
            y1 = min(n.sy, n.ey)
            x2 = max(n.sx, n.ex)
            y2 = max(n.sy, n.ey)
            #
            #
            if (x1 < 0.0 and y1 < 0.0 and y2 < 0.0) or (x1 < 0.0 and y1 > 0.0 and y2 > 0.0):
                #
                # Top and bottom line
                #
                x1_t = x1 - clearance.x
                x2_t = x2 + clearance.x
                x3_t = x1_t
                x4_t = x2_t
                #
                if y1 < 0.0:
                    # Top line
                    y1_t = y1 - clearance.y
                    y2_t = y2 - clearance.y
                    y3_t = y1_t
                    y4_t = y2_t
                    #
                    for nn in self.corners:
                        if nn[0] == 'URR':
                            x2_t = x2_t - (nn[1] + clearance.x)
                        if nn[0] == 'ULR':
                            x1_t = x1_t + (nn[1] + clearance.x)
                        if nn[0] == 'ULP':
                            x3_t = x1_t
                            x1_t = x1_t + (nn[1])
                            y3_t = y1_t + (nn[2])
                        if nn[0] == 'URP':
                            x4_t = x2_t
                            x2_t = x2_t - (nn[1])
                            y4_t = y1_t + (nn[2])

                else:
                    # Bottom line
                    y1_t = y1 + clearance.y
                    y2_t = y2 + clearance.y
                    y3_t = y1_t
                    y4_t = y2_t
                    #
                    for nn in self.corners:
                        if nn[0] == 'LRR':
                            x2_t = x2_t - (nn[1] + clearance.x)
                        if nn[0] == 'LLR':
                            x1_t = x1_t + (nn[1] + clearance.x)
                        if nn[0] == 'LLP':
                            x3_t = x1_t
                            x1_t = x1_t + (nn[1])
                            y3_t = y1_t - (nn[2])
                        if nn[0] == 'LRP':
                            x4_t = x2_t
                            x2_t = x2_t - (nn[1])
                            y4_t = y1_t - (nn[2])
                #
                EndLine = True
                UseCorner = True
                while EndLine:
                    px1 = 10000000.0
                    py1 = 10000000.0
                    px2 = 10000000.0
                    py2 = 10000000.0
                    foundPad = False

                    for n in self.pad:
                        n_min_x = n.at.x - (n.size.x / 2.0)
                        n_min_y = n.at.y - (n.size.y / 2.0)
                        n_max_x = n_min_x + n.size.x
                        n_max_y = n_min_y + n.size.y
                        dd_x = max(clearance.x, n.solder_mask_margin)
                        dd_y = max(clearance.y, n.solder_mask_margin)

                        if (n_min_y - dd_y) <= y1_t and (n_max_y + dd_y) > y1_t and n_max_x > x1_t and n_min_x < x2_t:
                            #
                            # This pad is in CrtYd line's path
                            #
                            if n_min_x < px1:
                                px1 = n_min_x
                                py1 = n_min_y
                                px2 = n_max_x
                                py2 = n_max_y
                                foundPad = True
                    if foundPad:
                        #
                        # Found at least one pad that is in CrtYd's line
                        #
                        if (px1 - dd_x) > x1_t:
                            #
                            # It does not cover the start point
                            #
                            self.fcrtydline.append(koaLine(x1_t, y1_t, px1 - dd_x, y2_t, 'F.CrtYd', self.FCrtYdWidth))
                            if y1 < 0.0:
                                # Top line
                                self.fcrtydline.append(koaLine(px1 - dd_x, y2_t, px1 - dd_x, py1 - dd_y, 'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px1 - dd_x, py1 - dd_y, px2 + dd_x, py1 - dd_y, 'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px2 + dd_x, py1 - dd_y, px2 + dd_x, y2_t, 'F.CrtYd', self.FCrtYdWidth))
                            else:
                                # Bottom line
                                self.fcrtydline.append(koaLine(px1 - dd_x, y2_t, px1 - dd_x, py2 + dd_y, 'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px1 - dd_x, py2 + dd_y, px2 + dd_x, py2 + dd_y, 'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px2 + dd_x, py2 + dd_y, px2 + dd_x, y2_t, 'F.CrtYd', self.FCrtYdWidth))
                        x1_t = px2 + dd_x
                    else:
                        #
                        # No pads was in the way
                        #
                        #
                        # No pads was in the way
                        #
                        if y1 < 0.0 and UseCorner:
                            # Top line
                            for nn in self.corners:
                                if nn[0] == 'ULR':
                                    urcdy0 = y1_t + (nn[1] + clearance.y)
                                    urcdx1 = x1_t - (nn[1] + clearance.y)
                                    new_node = Arc(center=Point2D(x1_t, urcdy0), start=Point2D(urcdx1, urcdy0), layer='F.CrtYd', width=self.FCrtYdWidth, angle=90.0)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)

                                if nn[0] == 'ULP':
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x1_t, y1_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x3_t, y3_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    #
                                if nn[0] == 'URP':
                                    urcdy0 = y4_t + (nn[2])
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x2_t, y2_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x4_t, y4_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)

                        if y1 > 0.0 and UseCorner:
                            # Bottom line
                            for nn in self.corners:
                                if nn[0] == 'LLR':
                                    urcdy0 = y1_t - (nn[1] + clearance.y)
                                    new_node = Arc(center=Point2D(x1_t, urcdy0), start=Point2D(x1_t, y1_t), layer='F.CrtYd', width=self.FCrtYdWidth, angle=90.0)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)

                                if nn[0] == 'LLP':
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x1_t, y1_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x1_t, y3_t), end=Point2D(x3_t, y3_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    #
                                if nn[0] == 'LRP':
                                    urcdy0 = y4_t + (nn[2])
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x2_t, y2_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                                    new_node = Line(start=Point2D(x2_t, y4_t), end=Point2D(x4_t, y4_t), layer='F.CrtYd', width=self.FCrtYdWidth)
                                    new_node._parent = self
                                    self.virtual_childs.append(new_node)
                        #
                        self.fcrtydline.append(koaLine(x1_t, y1_t, x2_t, y2_t, 'F.CrtYd', self.FCrtYdWidth))
                        EndLine = False

                    UseCorner = False

                    if x1_t >= x2:
                        EndLine = False

                if not foundPad and y1 < 0:
                    #
                    for nn in self.corners:
                        if nn[0] == 'URR':
                            urcdy1 = y1_t + (nn[1] + clearance.y)
                            new_node = Arc(center=Point2D(x2_t, urcdy1), start=Point2D(x2_t, y2_t), layer='F.CrtYd', width=self.FCrtYdWidth, angle=90.0)
                            new_node._parent = self
                            self.virtual_childs.append(new_node)


                if not foundPad and y1 > 0:
                    #
                    for nn in self.corners:
                        if nn[0] == 'LRR':
                            urcdx1 = x2_t + (nn[1] + clearance.x)
                            urcdy1 = y2_t - (nn[1] + clearance.y)
                            new_node = Arc(center=Point2D(x2_t, urcdy1), start=Point2D(urcdx1, urcdy1), layer='F.CrtYd', width=self.FCrtYdWidth, angle=90.0)
                            new_node._parent = self
                            self.virtual_childs.append(new_node)

            if (x1 < 0.0 and y1 < 0.0 and y2 > 0.0) or (x1 > 0.0 and y1 < 0.0 and y2 > 0.0):
                #
                # Left and right line
                #
                y1_t = y1 - clearance.y
                y2_t = y2 + clearance.y
                #
                if x1 < 0.0:
                    # Left line
                    x1_t = x1 - clearance.x
                    x2_t = x1 - clearance.x
                    #
                    for nn in self.corners:
                        if nn[0] == 'ULR':
                            y1_t = y1_t + (nn[1] + clearance.y)
                        if nn[0] == 'LLR':
                            y2_t = y2_t - (nn[1] + clearance.y)
                        if nn[0] == 'ULP':
                            y1_t = y1_t + (nn[2])
                        if nn[0] == 'LLP':
                            y2_t = y2_t - (nn[2])

                else:

                    # Right line
                    x1_t = x1 + clearance.x
                    x2_t = x2 + clearance.x
                    #
                    for nn in self.corners:
                        if nn[0] == 'URR':
                            y1_t = y1_t + (nn[1] + clearance.y)
                        if nn[0] == 'LRR':
                            y2_t = y2_t - (nn[1] + clearance.y)
                        if nn[0] == 'URP':
                            y1_t = y1_t + (nn[2])
                        if nn[0] == 'LRP':
                            y2_t = y2_t - (nn[2])
                #
                EndLine = True
                while EndLine:
                    px1 = 10000000.0
                    py1 = 10000000.0
                    px2 = 10000000.0
                    py2 = 10000000.0
                    foundPad = False

                    for n in self.pad:
                        n_min_x = n.at.x - (n.size.x / 2.0)
                        n_min_y = n.at.y - (n.size.y / 2.0)
                        n_max_x = n_min_x + n.size.x
                        n_max_y = n_min_y + n.size.y
                        dd_x = max(clearance.x, n.solder_mask_margin)
                        dd_y = max(clearance.y, n.solder_mask_margin)

                        if (n_min_x <= x1_t) and (n_max_x >= x1_t) and n_max_y >= y1_t and n_min_y <= y2_t:
                            #
                            # This pad is in CrtYd line's path
                            #
                            if n_min_y < py1:
                                px1 = n_min_x
                                py1 = n_min_y
                                px2 = n_max_x
                                py2 = n_max_y
                                foundPad = True
                    if foundPad:
                        #
                        # Found at least one pad that is in CrtYd's line
                        #
                        if (py1 - dd_y) > y1_t:
                            #
                            # It does not cover the start point
                            #
                            self.fcrtydline.append(koaLine(x1_t, y1_t, x2_t, py1 - dd_y, 'F.CrtYd', self.FCrtYdWidth))
                            if x1 < 0.0:
                                # Left line
                                self.fcrtydline.append(koaLine(x2_t, py1 - dd_y, px1 - dd_x, py1 - dd_y,
                                                               'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px1 - dd_x, py1 - dd_y, px1 - dd_x, py2 + dd_y,
                                                               'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px1 - dd_x, py2 + dd_y, x2_t, py2 + dd_y,
                                                               'F.CrtYd', self.FCrtYdWidth))
                            else:
                                # Right line
                                self.fcrtydline.append(koaLine(x2_t, py1 - dd_y, px2 + dd_x, py1 - dd_y,
                                                               'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px2 + dd_x, py1 - dd_y, px2 + dd_x, py2 + dd_y,
                                                               'F.CrtYd', self.FCrtYdWidth))
                                self.fcrtydline.append(koaLine(px2 + dd_x, py2 + dd_y, x2_t, py2 + dd_y,
                                                               'F.CrtYd', self.FCrtYdWidth))

                        y1_t = py2 + dd_y
                    else:
                        #
                        # No pads was in the way
                        #
                        self.fcrtydline.append(koaLine(x1_t, y1_t, x2_t, y2_t, 'F.CrtYd', self.FCrtYdWidth))
                        EndLine = False

                    if y1_t >= y2:
                        EndLine = False
        #
        #
        for n in self.fcrtydline:
            new_node = Line(start=Point2D(roundG(n.sx, 0.01), roundG(n.sy, 0.01)), end=Point2D(roundG(n.ex, 0.01), roundG(n.ey, 0.01)), layer=n.layer, width=n.width)
            if n.width < 0.0:
                new_node = Line(start=Point2D(roundG(n.sx, 0.01), roundG(n.sy, 0.01)), end=Point2D(roundG(n.ex, 0.01), roundG(n.ey, 0.01)), layer=n.layer)
            new_node._parent = self
            self.virtual_childs.append(new_node)

    def calculateBoundingBox(self):
        min_x = self.at.x
        min_y = self.at.y
        max_x = min_x + self.size.x
        max_y = min_y + self.size.y

        for child in self.virtual_childs():
            child_outline = child.calculateBoundingBox()

            min_x = min([min_x, child_outline['min']['x']])
            min_y = min([min_y, child_outline['min']['y']])
            max_x = max([max_x, child_outline['max']['x']])
            max_y = max([max_y, child_outline['max']['y']])

        return {'min': Point2D(min_x, min_y), 'max': Point2D(max_x, max_y)}

    def _createPinsNode(self):
        #
        # Add pin and holes
        #
        self.pad = []

        c = 1
        for n in self.pins:
            c = n[1]
            x = n[2]
            y = n[3]
            sx = n[4]
            sy = n[5]
            dh = n[6]
            new_pad = False
            if n[0] == 'tht':
                if c == '1':
                    new_pad = Pad(number=c, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                                  at=[x, 0.0 - y], size=[sx, sy], drill=dh, layers=Pad.LAYERS_THT)
                else:
                    new_pad = Pad(number=c, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                                  at=[x, 0.0 - y], size=[sx, sy], drill=dh, layers=Pad.LAYERS_THT)
            if n[0] == 'thtr':
                if c == '1':
                    new_pad = Pad(number=c, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                                  at=[x, 0.0 - y], size=[sx, sy], drill=dh, layers=Pad.LAYERS_THT)
                else:
                    new_pad = Pad(number=c, type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL,
                                  at=[x, 0.0 - y], size=[sx, sy], drill=dh, layers=Pad.LAYERS_THT)
            elif n[0] == 'smd':
                    new_pad = Pad(number=c, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT, radius_ratio=0.25,
                                  at=[x, 0.0 - y], size=[sx, sy], drill=dh, layers=Pad.LAYERS_SMT)
            elif n[0] == 'npth':
                    if sy == 0:
                        new_pad = Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                                      at=[x, 0.0 - y], size=[sx, sx], drill=dh, layers=Pad.LAYERS_NPTH)
                    else:
                        new_pad = Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_RECT,
                                      at=[x, 0.0 - y], size=[sx, sy], drill=dh, layers=Pad.LAYERS_NPTH)
            if new_pad != False:
                    self.footprint.append(new_pad)
                    self.pad.append(new_pad)
            #
