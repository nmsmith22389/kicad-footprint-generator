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

from kilibs.geom import Rectangle, Vector2D
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.LineStyle import LineStyle


class Rect(Node):
    r"""Add a (filled) footprint rect ``fp_rect`` to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *start* (``Vector2D``) --
          start corner of the rect
        * *end* (``Vector2D``) --
          end corner of the rect
        * *rect* (``Rectangle``) --
          rectangle to use instead of start and end
        * *layer* (``str``) --
          layer on which the rect is drawn
        * *width* (``float``) --
          width of the outer line, 0 for no outline
        * *fill* (``bool``) --
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
    style: LineStyle

    def __init__(
        self,
        width: float,
        layer: str,
        start: Vector2D | None = None,
        end: Vector2D | None = None,
        rect: Rectangle | None = None,
        fill: bool = False,
        style: LineStyle = LineStyle.SOLID,
    ):
        Node.__init__(self)

        if rect is not None:
            self.start_pos = rect.top_left
            self.end_pos = rect.bottom_right
        else:
            if start is None or end is None:
                raise ValueError(
                    "Either start and end or rect must be provided."
                )
            self.start_pos = Vector2D(start)
            self.end_pos = Vector2D(end)

        self.layer = layer
        self.width = width

        self.fill = fill
        self.style = style

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)

        render_string = [
            f"start: [x: {self.start_pos.x}, y: {self.start_pos.x}], "
            f"end: [x: {self.end_pos.x}, y: {self.end_pos.y}], "
            f"style: [outline-width: {self.width}, fill: {self.fill}]"
        ]

        render_text += f" [{render_string}]"

        return render_text

    def __repr__(self):
        return (
            f"Rect(start={self.start_pos}, end={self.end_pos}, "
            f"layer={self.layer}, width={self.width}, fill={self.fill})"
        )

    def __str__(self):
        return self.__repr__()
