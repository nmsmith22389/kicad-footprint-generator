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
# This module uses a kind of "ray tracing" with a line comming from lower left
# to find where it intersect with a polygon, these intersection points is then
# used to draw an "keep put" area within in the polygon
#
from KicadModTree.Point import *
from KicadModTree.PolygonPoints import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Line import Line


class koaLine:

    def __init__(self, sx, sy, ex, ey):
        self.sx = sx
        self.sy = sy
        self.ex = ex
        self.ey = ey
        self.k = 0.0
        self.m = 0.0
        self.IsVertical = False

        if ex != sx:
            self.k = (ey - sy) / (ex - sx)
            self.m = sy - (self.k * sx)
        else:
            self.IsVertical = True


class KeepOutArea(Node):
    r"""Add a Polygone Line to the render tree
    :param \**kwargs:
        See below
    :Keyword Arguments:
        * *nodes* (``list(Point)``) --
          outer nodes of the polygon
        * *step* (``float``) --
          step increment between intersection lines (default: 1.5)
        * *layer* (``str``) --
          layer on which the line is drawn (default: 'Dwgs.User')
        * *width* (``float``) --
          width of the line (default: None, which means auto detection)
    :Example:
    >>> from KicadModTree import *
    >>> KeepOutArea(nodes=[[0, 0], [0, 1], [1, 1], [0, 0]])
    """

    def __init__(self, **kwargs):
        Node.__init__(self)

        self.virtual_childs = []
        self.lines = []

        self._initStep(**kwargs)
        self._initLayer(**kwargs)
        self._initWidth(**kwargs)
        self._initNodes(**kwargs)
        #
        # Start to intersect the polygon with lines
        #
        min_xy, max_xy = self.calculateBoundingBoxXX()
        #
        # Calculate the ray tracing line
        # The algorithm have a known weak spot and that is corners
        # Attempt to avoid this by adding fractions with more decimals
        # than people normally use (1.91145, 1.1524)
        #
        # ix1, iy1, ik, im is the line that comes from lower left and
        # interect with the polygon
        #
        ix1 = min_xy.x - ((3 * (max_xy.y - min_xy.y)) - 1.91145)
        iy1 = min_xy.y + (max_xy.y - min_xy.y) + 1.1524
        #
        ik = -1.0
        im = iy1 - (ik * ix1)
        #
        y2i = min_xy.y - 1.32544
        x2i = (y2i - im) / ik
        #
#        ix1 = ix1 + (7 * self.stepx)
        #
        # Step the ray tracing line over a number of x values so
        # the whole polygon is covered
        #
        while (ix1 <= max_xy.x):
            im = iy1 - (ik * ix1)
            x2i = (y2i - im) / ik
#            self.lines.append(koaLine(ix1, iy1, x2i, y2i))
            self.findIntersection(ix1, iy1, ik, im)
            ix1 = ix1 + self.stepx

#        self.virtual_childs = self._createChildNodes(self.lines)

    def getVirtualChilds(self):
        #
        #
        return self.virtual_childs

    def _initNodes(self, **kwargs):
        if not kwargs.get('nodes'):
            raise KeyError('No nodes are given')

        nodes = kwargs.get('nodes')
        #
        # Transform the polygon to an internal line format
        #
        for n in range(0, len(nodes) - 1):
            self._createChildNodes(nodes[n][0], nodes[n][1], nodes[n+1][0], nodes[n+1][1])
            self.lines.append(koaLine(nodes[n][0], nodes[n][1], nodes[n+1][0], nodes[n+1][1]))
        # Add first and second point as line
        self._createChildNodes(nodes[len(nodes)-1][0], nodes[len(nodes) - 1][1], nodes[0][0], nodes[0][1])
        self.lines.append(koaLine(nodes[len(nodes)-1][0], nodes[len(nodes) - 1][1], nodes[0][0], nodes[0][1]))

    def _initStep(self, **kwargs):
        self.stepx = 1.5
        if kwargs.get('step'):
            self.at = kwargs.get('step')

    def _initLayer(self, **kwargs):
        self.layer = 'Dwgs.User'
        if kwargs.get('layer'):
            self.layer = kwargs.get('layer')

    def _initWidth(self, **kwargs):
        self.width = -1.0
        if kwargs.get('width'):
            self.at = kwargs.get('width')

    def _createChildNodes(self, sx, sy, ex, ey):
        new_line = Line(start=Point2D(sx, sy), end=Point2D(ex, ey), layer=self.layer)
        if self.width > 0.0:
            new_line.width = self.width
        new_line._parent = self
        self.virtual_childs.append(new_line)

    def calculateBoundingBox(self):
        min_xy, max_xy = self.calculateBoundingBoxXX()

        return Node.calculateBoundingBox({'min': min_xy, 'max': max_xy})

    def findIntersection(self, ix1, iy1, ik, im):
        intP = []
        #
        # Find all points where the intersection line hits the lines
        # in the polygon and calculate the point
        #
        xab = 0.0
        yab = 0.0
        for polygon in self.lines:
            Para = False
            if not polygon.IsVertical:
                #
                # Use 4 different cases to calculate the intersetion point
                # between the polygon and the ray tracing line
                #
                if polygon.k == 0.0:
                    #
                    # Horizontal line
                    #
                    yab = polygon.m
                    xab = (yab - im) / ik
#                    print('xab1 = ' + str(xab)  +  '   yab  = ' + str(yab))
                elif polygon.k != ik:
                    #
                    # "Normal" line
                    #
                    xab = (im - polygon.m) / (polygon.k - ik)
                    yab = (ik * xab) + im
#                    print('xab2 = ' + str(xab)  +  '   yab  = ' + str(yab))
                else:
                    #
                    # Parallel line
                    #
                    Para = True
            else:
                #
                # Special case, the polygon line goes straight up
                #
                xab = polygon.sx
                yab = (ik * xab) + im

            if not Para:
                #
                # Use brute force to check if the intersection point is on
                # the polygon line between end points.
                #
                if polygon.sx <= polygon.ex:
                    if xab >= polygon.sx and xab <= polygon.ex:
                        if polygon.sy < polygon.ey:
                            if yab >= polygon.sy and yab <= polygon.ey:
                                intP.append(Point2D(xab, yab))
                        else:
                            if yab >= polygon.ey and yab <= polygon.sy:
                                intP.append(Point2D(xab, yab))
                else:
                    if xab >= polygon.ex and xab <= polygon.sx:
                        if polygon.sy < polygon.ey:
                            if yab >= polygon.sy and yab <= polygon.ey:
                                intP.append(Point2D(xab, yab))
                        else:
                            if yab >= polygon.ey and yab <= polygon.sy:
                                intP.append(Point2D(xab, yab))
        #
        # Now we got all points where the intersection line hits the polygon
        # Remove duplicates
        #
        cp0 = []
        for polygon in intP:
            fd = False
            for cp in cp0:
                if polygon.x == cp.x and polygon.y == cp.y:
                    fd = True
            if not fd:
                cp0.append(Point2D(polygon.x, polygon.y))
        #
        # Find the point closest to the start point
        #
        cp = []
        for n in cp0:
            d = sqrt(((ix1 - n.x) * (ix1 - n.x)) + ((iy1 - n.y) * (iy1 - n.y)))
            c = 0
            f = True
            for t in cp:
                if f:
                    if t[2] < d:
                        cp.insert(c, [n.x, n.y, d])
                        f = False
                c = c + 1
            if f:
                cp.append([n.x, n.y, d])
        #
        # All intersection points have been sorted
        # regarding the distance from the intersection starting point
        # Add them now as lines
        #
        c = 0
        while ((c + 1) < len(cp)):
            self._createChildNodes(cp[c][0], cp[c][1], cp[c+1][0], cp[c+1][1])
            c = c + 2

    def calculateBoundingBoxXX(self):

        min_xy = Point2D(0, 0)
        max_xy = Point2D(0, 0)

        if len(self.lines) > 0:
            min_xy = Point2D(self.lines[0].x, self.lines[0].y)
            max_xy = Point2D(self.lines[0].x, self.lines[0].y)

            for n in self.lines:
                min_xy.x = min(min_xy.x, n.sx)
                min_xy.x = min(min_xy.x, n.ex)
                #
                min_xy.y = min(min_xy.y, n.sy)
                min_xy.y = min(min_xy.y, n.ey)
                #
                max_xy.x = max(max_xy.x, n.sx)
                max_xy.x = max(max_xy.x, n.ex)
                #
                max_xy.y = max(max_xy.y, n.sy)
                max_xy.y = max(max_xy.y, n.ey)

        return min_xy, max_xy

    def _getRenderTreeText(self):
        for n in self.lines:
            render_strings = ['fp_line']
            render_strings.append('(start {x})'.format(x=formatFloat(n.x)))
            render_strings.append('(end {y})'.format(y=formatFloat(n.y)))
            render_strings.append('(layer {layer})'.format(layer=self.layer))
            render_strings.append('(width {width})'.format(width=self.width))

            render_text = Node._getRenderTreeText(self)
            render_text += ' ({})'.format(' '.join(render_strings))

        return render_text
