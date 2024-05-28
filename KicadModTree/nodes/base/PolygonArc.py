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
# (C) 2024 by C. Kuhlmann, gitlab @CKuhlmann

from KicadModTree.Vector import *
from KicadModTree.nodes.Node import Node
import math
from KicadModTree.util.geometric_util import geometricArc, BaseNodeIntersection
from KicadModTree.nodes.base.Arc import *


class PolygonArc(Arc):
    r"""Add an PolygonArc for a CompoundPolygon

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *geometry* (``geometricArc``)
          alternative to using geometric parameters
        * *center* (``Vector2D``) --
          center of arc
        * *start* (``Vector2D``) --
          start point of arc
        * *midpoint* (``Vector2D``) --
          alternative to start point
          point is on arc and defines point of equal distance to both arc ends
          arcs of this form are given as midpoint, center plus angle
        * *end* (``Vector2D``) --
          alternative to angle
          arcs of this form are given as start, end and center
        * *angle* (``float``) --
          angle of arc
        * *layer* (``str``) --
          layer on which the arc is drawn (default: 'F.SilkS')
        * *width* (``float``) --
          width of the arc line (default: None, which means auto detection)

    :Example:

    >>> from KicadModTree import *
    >>> Arc(center=[0, 0], start=[-1, 0], angle=180, layer='F.SilkS')
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Node.__init__(self)
        # geometricArc.__init__(self, **kwargs)

        self.layer = None  # PolygonArc has no layer of its own
        self.width = None  # PolygonArc has no stroke width its own
