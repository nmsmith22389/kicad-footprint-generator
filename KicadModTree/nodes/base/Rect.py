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
          layer on which the rect is drawn (default: 'F.SilkS')
        * *width* (``float``) --
          width of the outer line (default: 0.15)
        * *fill* (``str, bool``) --
          valid values are 'solid', 'none'

    :Example:

    >>> from KicadModTree import *
    >>> Rect(start=[-3, -2], end=[3, 2], layer='F.SilkS')
    """

    start_pos: Vector2D
    end_pos: Vector2D
    layer: str
    width: float
    fill: Union[Literal["solid"], Literal["none"]]

    def __init__(self, **kwargs):
        Node.__init__(self)
        self.start_pos = Vector2D(kwargs['start'])
        self.end_pos = Vector2D(kwargs['end'])

        self.layer = kwargs.get('layer', 'F.SilkS')
        # TODO: better variation to get line width
        self.width = float(kwargs.get('width', 0.12))

        self.fill = kwargs.get('fill', 'none')

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)

        render_string = [
            f"start: [x: {self.start_pos.x}, y: {self.start_pos.x}], "
            f"end: [x: {self.end_pos.x}, y: {self.end_pos.y}], "
            f"style: [outline-width: {self.width}, fill: {self.fill}]"
        ]

        render_text += f" [{render_string}]"

        return render_text
