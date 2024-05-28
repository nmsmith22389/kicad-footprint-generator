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
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.specialized import RectLine
from KicadModTree.nodes.specialized import RectFill


class FPRect(Node):
    r"""Add a (filled) footprint rect ``fp_rect`` to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *start* (``Vector2D``) --
          start edge of the rect
        * *end* (``Vector2D``) --
          end edge of the rect
        * *layer* (``str``) --
          layer on which the rect is drawn (default: 'F.SilkS')
        * *width* (``float``) --
          width of the outer line (default: 0.15)
        * *fill* (``str, bool``) --
          valid values are 'solid', 'none' or True and False respectively

    :Example:

    >>> from KicadModTree import *
    >>> FilledRect(start=[-3, -2], end=[3, 2], layer='F.SilkS')
    """

    def __init__(self, **kwargs):
        Node.__init__(self)
        self.start_pos = Vector2D(kwargs['start'])
        self.end_pos = Vector2D(kwargs['end'])

        self.layer = kwargs.get('layer', 'F.SilkS')
        # TODO: better variation to get line width
        self.width = float(kwargs.get('width', 0.12))

        fill = kwargs.get('fill', 'none')
        if (fill == 'solid') or (isinstance(fill, bool) and fill):
            self.fill = 'solid'
        else:
            self.fill = 'none'

        # self.virtual_childs = [rect_line, rect_fill]

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)

        render_string = ['start: [x: {sx}, y: {sy}]'.format(sx=self.start_pos.x, sy=self.start_pos.y),
                         'end: [x: {ex}, y: {ey}]'.format(
                             ex=self.end_pos.x, ey=self.end_pos.y),
                         'style: [outline-width: {f}, fill: {ey}]'.format(
                             ex=self.width, ey=self.fill)
                         ]

        render_text += " [{}]".format(", ".join(render_string))

        return render_text
