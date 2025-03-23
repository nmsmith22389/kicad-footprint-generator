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
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

from kilibs.geom import PolygonPoints
from KicadModTree.nodes.Node import Node

from typing import Optional


class Polygon(Node):
    r"""Add a Polygon to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *polygon* (``list(Point)``) --
          outer nodes of the polygon
        * *layer* (``str``) --
          layer on which the line is drawn (default: None, only useful for pad primitives)
        * *width* (``float``) --
          width of the line (default: 0, which mean no outline)
        * *x_mirror* (``[int, float](mirror offset)``) --
          mirror x direction around offset "point"
        * *y_mirror* (``[int, float](mirror offset)``) --
          mirror y direction around offset "point"
        * *fill* (``bool``) --
          is the polygon filled or just the outline

    :Example:

    >>> from KicadModTree import *
    >>> Polygon(nodes=[[-2, 0], [0, -2], [4, 0], [0, 2]], layer='F.SilkS', width=0.1, fill=True)
    """

    nodes: PolygonPoints
    layer: Optional[str]
    width: float
    fill: bool

    def __init__(
        self,
        nodes: list,
        fill: bool,
        width: float,
        layer: Optional[str] = None,
        mirror_x: bool = False,
        mirror_y: bool = False,
    ):
        Node.__init__(self)
        self.nodes = PolygonPoints(nodes=nodes, x_mirror=mirror_x, y_mirror=mirror_y)

        # If we are handed a closed polygon, don't double up the final point:
        # Polygons (not PolyLines!) are implicitly closed in KiCad
        if self.nodes.nodes[0] == self.nodes.nodes[-1]:
            self.nodes.nodes.pop()

        self.layer = layer
        self.width = width
        self.fill = fill

    def rotate(self, angle, origin=(0, 0), use_degrees=True):
        r""" Rotate polygon around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.nodes.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        return self

    def translate(self, distance_vector):
        r""" Translate polygon

        :params:
            * *distance_vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.nodes.translate(distance_vector)
        return self

    def calculateBoundingBox(self):
        return self.nodes.calculateBoundingBox()

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)
        render_text += " [nodes: ["

        node_strings = []
        for n in self.nodes:
            node_strings.append("[x: {x}, y: {y}]".format(x=n.x, y=n.y))

        if len(node_strings) <= 6:
            render_text += ", ".join(node_strings)
        else:
            # display only a few nodes of the beginning and the end of the polygon line
            render_text += ", ".join(node_strings[:3])
            render_text += ",... , "
            render_text += ", ".join(node_strings[-3:])

        render_text += "]"

        return render_text

    def cut(self, other):
        r""" Cut other polygon from this polygon

        More details see PolygonPoints.cut docstring.

        :param other: the other polygon
        """
        self.nodes.cut(other.nodes)
