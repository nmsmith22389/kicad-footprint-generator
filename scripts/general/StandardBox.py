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

#
# This module Create a standard box in various layers including a pin 1 marker tap or chamfer
#
from KicadModTree import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Text import Text
from kilibs.geom import BoundingBox, Vector2D

from scripts.tools.drawing_tools import *
from scripts.tools.drawing_tools_fab import draw_chamfer_rect_fab
from scripts.tools.global_config_files.global_config import GlobalConfig


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
        * *automatic_pin1_mark* (``bool``) --
          Add a pin 1 marker to the footprint. If False, the pin 1 marker is not added (default: True)
        * *file3Dname* (``str``) --
          The path to the 3D model name

    :Example:

    #
    # pycodestyle complain over long lines so the complete on is placed in a comment instead
    #
    # StandardBox(footprint=f, description=description, datasheet=datasheet, at=at, size=size, tags=fptag,
    # extratexts=extratexts, pins=pins, file3Dname = file3dname)))
    #
    >>> from KicadModTree import *
    >>> StandardBox(footprint=f, description=description, ....)
    """

    courtyard_clearance: Vector2D
    fab_silk_clearance: Vector2D

    def __init__(self, global_config: GlobalConfig, **kwargs):
        Node.__init__(self)

        self.global_config = global_config

        default_ipc_courtyard_mm = self.global_config.get_courtyard_offset(
            GlobalConfig.CourtyardType.DEFAULT
        )

        self.courtyard_clearance = kwargs.get('courtyard_clearance', Vector2D(
            default_ipc_courtyard_mm, default_ipc_courtyard_mm))

        default_silk_fab_clearance = self.global_config.silk_fab_clearance

        # By default fab just touches the fab outline
        self.fab_silk_clearance = kwargs.get(
            "fab_to_silk_clearance",
            Vector2D(default_silk_fab_clearance, default_silk_fab_clearance),
        )

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

        self.automatic_pin1_mark = kwargs.get('automatic_pin1_mark', True)

        # Create footprint parts
        self._createPinsNode()
        self._createFFabLine()

        if self.automatic_pin1_mark:
            self._createPin1MarkerLine()

        self._createFSilkSLine()
        self._createFCrtYdLine()

    def getVirtualChilds(self):
        return self.virtual_childs

    def _initPosition(self, **kwargs):
        if 'at' not in kwargs:
            raise KeyError('Upper left position not declared (like "at: [0,0]")')
        self.at = Vector2D(kwargs.get('at'))
        self.at.y = 0.0 - self.at.y

    def _initSize(self, **kwargs):
        if 'size' not in kwargs:
            raise KeyError('Size not declared (like "size: [1,1]")')
        if type(kwargs.get('size')) in [int, float]:
            # when the attribute is a simple number, use it for x and y
            self.size = Vector2D([kwargs.get('size'), kwargs.get('size')])
        else:
            size_original = kwargs.get('size')

            if len(size_original ) > 2:
                raise ValueError(
                    "Size must be a list of 2 elements (corners are no longer handled in this way)"
                )

            self.size = Vector2D(size_original[0], size_original[1])

        # This is the transform that will be used to place an origin-centred
        # box in the right place
        self._box_transform = Translation(self.size / 2 + self.at)
        self.append(self._box_transform)

    def _createFSilkRefDesText(self):

        silk_ref_des_size = [1, 1]
        corner_pos = self._getPin1ChevronCorner()

        # No specific reason for this exact value, seems about right
        ref_des_x_inset = 2.5
        # place the silk avoiding the pin 1 marker
        silk_ref_des_pos = corner_pos + Vector2D(ref_des_x_inset, -silk_ref_des_size[1] / 2 - 2 * self.FSilkSWidth)

        new_node = Property(name=Property.REFERENCE, text='REF**', at=silk_ref_des_pos, size=silk_ref_des_size, layer='F.SilkS')
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
        new_node = Text(text='${REFERENCE}', at=fab_ref_des_pos, layer='F.Fab', size=[self.REF_P_w, self.REF_P_h])
        new_node._parent = self
        self.virtual_childs.append(new_node)

        self.virtual_childs.append(self._createFSilkRefDesText())

        # Get the fab value outside both the courtyard and silk
        fab_value_y_offset = max(self.courtyard_clearance.y, self.fab_silk_clearance.y)

        fab_value_pos = Vector2D(
            self.at.x + (self.size.x / 2.0),
            self.at.y + self.size.y + fab_value_y_offset + 1.0
        )

        new_node = Property(name=Property.VALUE, text=self.footprint_name, at=fab_value_pos, layer="F.Fab")
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

        tags = kwargs.get('tags')

        if compatible_mpns := kwargs.get('compatible_mpns'):
            tags += " " + " ".join(compatible_mpns)

        self.footprint.tags = tags

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
                new_node = Text(text=stss, at=at)
                #
                if len(n) > 3:
                    new_node.layer = n[3]
                if len(n) > 5:
                    new_node.size = Vector2D([n[4], n[5]])
                new_node._parent = self
                self.virtual_childs.append(new_node)

    def _createFFabLine(self):
        self.boxffabline = []

        x = self.at.x
        y = self.at.y
        w = self.size.x
        h = self.size.y
        self.boxffabline.append(koaLine(x, y, x + w, y, 'F.Fab', self.FFabWidth))
        self.boxffabline.append(koaLine(x + w, y, x + w, y + h, 'F.Fab', self.FFabWidth))
        self.boxffabline.append(koaLine(x + w, y + h, x, y + h, 'F.Fab', self.FFabWidth))
        self.boxffabline.append(koaLine(x, y + h, x, y, 'F.Fab', self.FFabWidth))

        # Also drive the fab chamfer from this parameter
        # If needed, a separate parameter could be added to control this independently
        self._box_transform.append(
            draw_chamfer_rect_fab(
                self.size, self.global_config, has_chamfer=self.automatic_pin1_mark
            )
        )

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

        # to determine in which direction to outset the silkscren line
        # we determine the center point of the box and use it to determine
        # if a given line is top/bottom/left/right

        n_lines = len (self.boxffabline)
        x0 = sum ([(n.sx + n.ex)/2 for n in self.boxffabline]) / n_lines
        y0 = sum ([(n.sy + n.ey)/2 for n in self.boxffabline]) / n_lines

        # Check all holes and pads, if a pad or hole is on the silk line
        # then jump over the pad/hole
        for n in self.boxffabline:
            x1 = min(n.sx, n.ex)
            y1 = min(n.sy, n.ey)
            x2 = max(n.sx, n.ex)
            y2 = max(n.sy, n.ey)
            #
            #
            if (x1 < x0 and y1 < y0 and y2 < y0) or (x1 < x0 and y1 > y0 and y2 > y0):
                #
                # Top and bottom line
                #
                x1_t = x1 - fab_silk_outset.x
                x2_t = x2 + fab_silk_outset.x
                x3_t = x1_t
                x4_t = x2_t
                #
                if y1 < y0:
                    # Top line
                    y1_t = y1 - fab_silk_outset.y
                    y2_t = y2 - fab_silk_outset.y
                    y3_t = y1_t
                    y4_t = y2_t
                else:
                    # Bottom line
                    y1_t = y1 + fab_silk_outset.y
                    y2_t = y2 + fab_silk_outset.y
                    y3_t = y1_t
                    y4_t = y2_t

                #
                EndLine = True
                foundPad = False

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
                        self.fsilksline.append(koaLine(x1_t, y1_t, x2_t, y2_t, 'F.SilkS', self.FSilkSWidth))
                        EndLine = False

                    if x1_t >= x2:
                        EndLine = False

            if (x1 < x0 and y1 < y0 and y2 > y0) or (x1 > x0 and y1 < y0 and y2 > y0):
                #
                # Left and right line
                #
                y1_t = y1 - fab_silk_outset.y
                y2_t = y2 + fab_silk_outset.y
                #
                if x1 < x0:
                    # Left line
                    x1_t = min(x1 - fab_silk_outset.x, x2 - fab_silk_outset.x)
                    x2_t = max(x1 - fab_silk_outset.x, x2 - fab_silk_outset.x)

                else:
                    # Right line
                    x1_t = min(x1 + fab_silk_outset.x, x2 + fab_silk_outset.x)
                    x2_t = max(x1 + fab_silk_outset.x, x2 + fab_silk_outset.x)

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

        for n in self.fsilksline:
            new_node = Line(start=Vector2D(n.sx, n.sy), end=Vector2D(n.ex, n.ey), layer=n.layer, width=n.width)
            if n.width < 0.0:
                new_node = Line(start=Vector2D(n.sx, n.sy), end=Vector2D(n.ex, n.ey), layer=n.layer)
            new_node._parent = self
            self.virtual_childs.append(new_node)

    def _createFCrtYdLine(self):
        self.fcrtydline = []
        #
        #
        #
        # Expand courtyard to include max of all pad copper plus clearance
        #
        clearance = self.courtyard_clearance

        cy_min_x = None
        cy_max_x = None
        cy_min_y = None
        cy_max_y = None

        for p in self.pad:
            p_min_x = p.at.x - (p.size.x / 2.0)
            p_min_y = p.at.y - (p.size.y / 2.0)
            p_max_x = p_min_x + p.size.x
            p_max_y = p_min_y + p.size.y
            if cy_min_x is None:
                cy_min_x = p_min_x
            else:
                cy_min_x = min(cy_min_x, p_min_x)
            if cy_min_y is None:
                cy_min_y = p_min_y
            else:
                cy_min_y = min(cy_min_y, p_min_y)
            if cy_max_x is None:
                cy_max_x = p_max_x
            else:
                cy_max_x = max(cy_max_x, p_max_x)
            if cy_max_y is None:
                cy_max_y = p_max_y
            else:
                cy_max_y = max(cy_max_y, p_max_y)

        for f in self.boxffabline:
            cy_min_x = min(f.sx, f.ex, cy_min_x)
            cy_min_y = min(f.sy, f.ey, cy_min_y)
            cy_max_x = max(f.sx, f.ex, cy_max_x)
            cy_max_y = max(f.sy, f.ey, cy_max_y)

        cy_min_x -= 0.005 # ensure that rounding of courtyard to nearest 0.01mm grid point below is always away from the part
        cy_min_x -= clearance.x
        cy_min_y -= 0.005
        cy_min_y -= clearance.y
        cy_max_x += 0.005
        cy_max_x += clearance.y
        cy_max_y += 0.005
        cy_max_y += clearance.x

        # (min, min) -> (min, max)
        new_node = Line(start=Vector2D(round_to_grid(cy_min_x, 0.01), round_to_grid(cy_min_y, 0.01)), end=Vector2D(round_to_grid(cy_min_x, 0.01), round_to_grid(cy_max_y, 0.01)), layer='F.CrtYd', width=self.FCrtYdWidth)
        new_node._parent = self
        self.virtual_childs.append(new_node)

        # (min, max) -> (max, max)
        new_node = Line(start=Vector2D(round_to_grid(cy_min_x, 0.01), round_to_grid(cy_max_y, 0.01)), end=Vector2D(round_to_grid(cy_max_x, 0.01), round_to_grid(cy_max_y, 0.01)), layer='F.CrtYd', width=self.FCrtYdWidth)
        new_node._parent = self
        self.virtual_childs.append(new_node)

        # (max, max) -> (max, min)
        new_node = Line(start=Vector2D(round_to_grid(cy_max_x, 0.01), round_to_grid(cy_max_y, 0.01)), end=Vector2D(round_to_grid(cy_max_x, 0.01), round_to_grid(cy_min_y, 0.01)), layer='F.CrtYd', width=self.FCrtYdWidth)
        new_node._parent = self
        self.virtual_childs.append(new_node)

        # (max, min) -> (min, min)
        new_node = Line(start=Vector2D(round_to_grid(cy_max_x, 0.01), round_to_grid(cy_min_y, 0.01)), end=Vector2D(round_to_grid(cy_min_x, 0.01), round_to_grid(cy_min_y, 0.01)), layer='F.CrtYd', width=self.FCrtYdWidth)
        new_node._parent = self
        self.virtual_childs.append(new_node)

    def calculateBoundingBox(self):
        min_x = self.at.x
        min_y = self.at.y
        max_x = min_x + self.size.x
        max_y = min_y + self.size.y

        bbox = BoundingBox(
            min_pt=Vector2D(min_x, min_y),
            max_pt=Vector2D(max_x, max_y),
        )

        for child in self.virtual_childs():
            child_bbox = child.calculateBoundingBox()
            bbox.include_bbox(child_bbox)

        return bbox

    def _createPinsNode(self):
        #
        # Add pin and holes
        #
        self.pad = []

        radius_handler = self.global_config.roundrect_radius_handler

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
                new_pad = Pad(number=c, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                                 round_radius_handler=radius_handler,
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
