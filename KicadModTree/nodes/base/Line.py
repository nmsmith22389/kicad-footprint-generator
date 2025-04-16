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

from kilibs.geom import BoundingBox, Vector2D
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.LineStyle import LineStyle
from kilibs.geom.geometric_util import geometricLine


class Line(Node, geometricLine):
    r"""Add a Line to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *start* (``Vector2D``) --
          start point of the line
        * *end* (``Vector2D``) --
          end point of the line
        * *layer* (``str``) --
          layer on which the line is drawn (default: 'F.SilkS')
        * *width* (``float``) --
          width of the line (default: None, which means auto detection)

    :Example:

    >>> from KicadModTree import *
    >>> Line(start=[1, 0], end=[-1, 0], layer='F.SilkS')
    """

    start_pos: Vector2D
    end_pos: Vector2D
    layer: str
    width: float
    style: LineStyle

    def __init__(self, **kwargs):
        Node.__init__(self)
        if 'geometry' in kwargs:
            geometry = kwargs['geometry']
            geometricLine.__init__(self, start=geometry.start_pos, end=geometry.end_pos)
        else:
            geometricLine.__init__(
                self,
                start=Vector2D(kwargs['start']),
                end=Vector2D(kwargs['end'])
                )

        self.layer = kwargs.get('layer', 'F.SilkS')
        self.width = kwargs.get('width')
        self.style = kwargs.get('style', LineStyle.SOLID)

    def copyReplaceGeometry(self, geometry):
        return Line(
            start=geometry.start_pos, end=geometry.end_pos,
            layer=self.layer, width=self.width
            )

    def copy(self):
        return Line(
            start=self.start_pos, end=self.end_pos,
            layer=self.layer, width=self.width
            )

    def cut(self, *other):
        r""" cut line with given other element

        :params:
            * *other* (``Line``, ``Circle``, ``Arc``)
                cut the element on any intersection with the given geometric element
        """
        result = []
        glines = geometricLine.cut(self, *other)
        for g in glines:
            if not (g.start_pos - g.end_pos).is_nullvec(1e-6):
                result.append(self.copyReplaceGeometry(g))

        return result

    def _getRenderTreeText(self):
        render_strings = ['fp_line']
        render_strings.append('(start {x} {y})'.format(**self.start_pos.to_dict()))
        render_strings.append('(end {x} {y})'.format(**self.end_pos.to_dict()))
        render_strings.append('(layer {layer})'.format(layer=self.layer))
        render_strings.append('(width {width})'.format(width=self.width))

        render_text = Node._getRenderTreeText(self)
        render_text += ' ({})'.format(' '.join(render_strings))

        return render_text

    def calculateBoundingBox(self):
        return BoundingBox(
            min_pt=self.start_pos,
            max_pt=self.end_pos,
        )
