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

from KicadModTree.Vector import *
from KicadModTree.PolygonPoints import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Line import Line


class PolygonLine(Node):
    r"""Add a Polygon Line to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *polygon* (``list(Point)``) --
          edges of the polygon
        * *layer* (``str``) --
          layer on which the polygon is drawn (default: 'F.SilkS')
        * *width* (``float``) --
          width of the line (default: None, which means auto detection)

    :Example:

    >>> from KicadModTree import *
    >>> PolygonLine(polygon=[[0, 0], [0, 1], [1, 1], [0, 0]], layer='F.SilkS')
    """

    def __init__(self, **kwargs):
        Node.__init__(self)

        self.layer = kwargs.get('layer', 'F.SilkS')
        self.width = kwargs.get('width')

        self._initPolyPoint(**kwargs)

        self.updateVirtualChilds()

    def _initPolyPoint(self, **kwargs):
        self.nodes = PolygonPoints(**kwargs)

    def _createChildNodes(self, polygon_line):
        nodes = []

        for line_start, line_end in zip(polygon_line, polygon_line[1:]):
            new_node = Line(start=line_start, end=line_end, layer=self.layer, width=self.width)
            new_node._parent = self
            nodes.append(new_node)

        return nodes

    def updateVirtualChilds(self):
        self.virtual_childs = self._createChildNodes(self.nodes)

    def getVirtualChilds(self):
        return self.virtual_childs

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)
        render_text += " ["

        node_strings = []
        for node in self.nodes:
            node_position = Vector2D(node)
            node_strings.append("[x: {x}, y: {y}]".format(x=node_position.x,
                                                          y=node_position.y))

        if len(node_strings) <= 6:
            render_text += " ,".join(node_strings)
        else:
            # display only a few nodes of the beginning and the end of the polygon line
            render_text += " ,".join(node_strings[:3])
            render_text += " ,... ,"
            render_text += " ,".join(node_strings[-3:])

        render_text += "]"

        return render_text

    def lineItems(self):
        return iter(self.virtual_childs)

    def pointItems(self):
        return iter(self.nodes.getPoints())

    def isPointOnSelf(self, point):
        return any(p.isPointOnSelf(point) for p in self.lineItems())

    def isPointInsideSelf(self, point, corner=True):
        # see, e.g. https://www.inf.usi.ch/hormann/papers/Hormann.2001.TPI.pdf
        point = Vector2D(point)
        poly_points = [Vector2D(p) for p in self.nodes.getPoints()]
        if (len(poly_points) == 0):
            return False
        # close the contour if not already closed
        if (poly_points[-1] != poly_points[0]):
            poly_points.append(poly_points[0])
        # calculate the winding number: if 0 the point is outside, otherwise inside
        p1 = poly_points[0] - point
        if p1.is_nullvec():
            return corner
        a1 = p1.arg()
        angle = 0
        for p in poly_points:
            p0, p1 = p1, p - point
            if p1.is_nullvec():
                return corner
            a0, a1 = a1, p1.arg()
            angle += (a0 - a1 + 180) % 360 - 180
        winding = round(angle / 360)
        return winding

    def cut(self, *other):
        lines = []
        for line in self.lineItems():
            lines += line.cut(*other)
        return lines

    def rotate(self, *args, **kwargs):
        self.nodes.rotate(*args, **kwargs)
        self.updateVirtualChilds()
        return self

    def translate(self, *args, **kwargs):
        self.nodes.translate(*args, **kwargs)
        self.updateVirtualChilds()
        return self

    def duplicate(self, *, offset: float = 0.0, layer: str = None, width: float = None, split_angle: float = 90):
        """
        Create a duplicate of the polygon.

        Args:
            offset: specifies an optional offset (in mm); if the polygon is sorted clockwise, the
                duplicate will be a polygon with parallel edges with the specific offset
            layer: defines the duplication layer (default is to keep the same layer)
            width: defines the line width of the duplicate (default: same as original)
            split_angle: defines the limit to maintain convex corners; any turn with an angle bigger than
                split_angle will be split into two corners (default 90 degree)

        Returns:
            an independent copy of the polygon with the specific modifications
        """
        points = self.nodes.getPoints()
        if layer is None:
            layer = self.layer
        if width is None:
            width = self.width
        if (offset):
            from KicadModTree.util.silkmask_util import calculateOffsetPolygonNodes
            points = calculateOffsetPolygonNodes(points, offset=offset, split_angle=max(0, min(150, split_angle)))
        return PolygonLine(nodes=points, layer=layer, width=width)
