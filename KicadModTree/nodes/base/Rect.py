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

from KicadModTree.Vector import Vector2D
from KicadModTree.nodes.Node import Node

from typing import Union, Literal


class Rect(Node):
    r"""Add a (filled) footprint rect ``fp_rect`` to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *start* (``Vector2D``) --
          start corner of the rect
        * *end* (``Vector2D``) --
          end corner of the rect
        * *layer* (``str``) --
          layer on which the rect is drawn
        * *width* (``float``) --
          width of the outer line, 0 for no outline
        * *fill* (``str, bool``) --
          fill the rectangle, (default: False)

    :Example:

    >>> from KicadModTree import *
    >>> Rect(start=[-3, -2], end=[3, 2], layer='F.SilkS')
    """

    start_pos: Vector2D
    end_pos: Vector2D
    layer: str
    width: float
    fill: bool

    def __init__(
        self,
        start: Vector2D,
        end: Vector2D,
        width: float,
        layer: str,
        fill: bool = False,
    ):
        Node.__init__(self)
        self.start_pos = Vector2D(start)
        self.end_pos = Vector2D(end)

        self.layer = layer
        self.width = width

        self.fill = fill

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)

        render_string = [
            f"start: [x: {self.start_pos.x}, y: {self.start_pos.x}], "
            f"end: [x: {self.end_pos.x}, y: {self.end_pos.y}], "
            f"style: [outline-width: {self.width}, fill: {self.fill}]"
        ]

        render_text += f" [{render_string}]"

        return render_text
