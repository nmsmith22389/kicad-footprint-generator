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
# (C) 2018 by Rene Poeschl, github @poeschlr
from __future__ import division

from copy import copy

from kilibs.geom import Vector2D
from kilibs.util.param_util import toVectorUseCopyIfNumber
from KicadModTree.util.corner_selection import CornerSelection
from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.base.Pad import Pad, RoundRadiusHandler
from KicadModTree.nodes.Node import Node
from math import sqrt


class ChamferedPad(Node):
    r"""Add a ChamferedPad to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *number* (``int``, ``str``) --
          number/name of the pad (default: \"\")
        * *type* (``Pad.TYPE_THT``, ``Pad.TYPE_SMT``, ``Pad.TYPE_CONNECT``, ``Pad.TYPE_NPTH``) --
          type of the pad
        * *at* (``Vector2D``) --
          center position of the pad
        * *rotation* (``float``) --
          rotation of the pad
        * *size* (``float``, ``Vector2D``) --
          size of the pad
        * *offset* (``Vector2D``) --
          offset of the pad
        * *drill* (``float``, ``Vector2D``) --
          drill-size of the pad
        * *solder_paste_margin_ratio* (``float``) --
          solder paste margin ratio of the pad (default: 0)
        * *solder_paste_margin* (``float``) --
          solder paste margin of the pad (default: 0)
        * *solder_mask_margin* (``float``) --
          solder mask margin of the pad (default: 0)
        * *layers* (``Pad.LAYERS_SMT``, ``Pad.LAYERS_THT``, ``Pad.LAYERS_NPTH``) --
          layers on which are used for the pad
        * *corner_selection* (``CornerSelection``) --
          Select which corner(s) to chamfer. (top left, top right, bottom right, bottom left)
        * *chamfer_size* (``float``, ``Vector2D``) --
          Size of the chamfer.
        * *x_mirror* (``[int, float](mirror offset)``) --
          mirror x direction around offset "point"
        * *y_mirror* (``[int, float](mirror offset)``) --
          mirror y direction around offset "point"

        * *round_radius_handler* (``RoundRadiusHandler``) --
          An instance of the RoundRadiusHandler class
    """

    round_radius_handler: RoundRadiusHandler

    def __init__(self, **kwargs):
        Node.__init__(self)
        self._initPosition(**kwargs)
        self._initSize(**kwargs)
        self._initMirror(**kwargs)
        self._initPadSettings(**kwargs)

        self.pad = self._generatePad()

    def _initSize(self, **kwargs):
        if not kwargs.get('size'):
            raise KeyError('pad size not declared (like "size=[1,1]")')
        self.size = toVectorUseCopyIfNumber(kwargs.get('size'), low_limit=0)

    def _initPosition(self, **kwargs):
        if 'at' not in kwargs:
            raise KeyError('center position not declared (like "at=[0,0]")')
        self.at = Vector2D(kwargs.get('at'))

    def _initMirror(self, **kwargs):
        self.mirror = {}
        if 'x_mirror' in kwargs and type(kwargs['x_mirror']) in [float, int]:
            self.mirror['x_mirror'] = kwargs['x_mirror']
        if 'y_mirror' in kwargs and type(kwargs['y_mirror']) in [float, int]:
            self.mirror['y_mirror'] = kwargs['y_mirror']

    def _initPadSettings(self, **kwargs):
        if 'corner_selection' not in kwargs:
            raise KeyError('corner selection is required for chamfered pads (like "corner_selection=[1,0,0,0]")')

        self.corner_selection = CornerSelection(kwargs.get('corner_selection'))

        if 'chamfer_size' not in kwargs:
            self.chamfer_size = Vector2D(0, 0)
        else:
            self.chamfer_size = toVectorUseCopyIfNumber(
                kwargs.get('chamfer_size'), low_limit=0, must_be_larger=False)

        self.round_radius_handler = kwargs['round_radius_handler']

        self.padargs = copy(kwargs)
        self.padargs.pop('size', None)
        self.padargs.pop('shape', None)
        self.padargs.pop('at', None)
        self.padargs.pop('round_radius_handler', None)
        self.padargs.pop('corner_selection', None)
        self.padargs.pop('chamfer_size', None)

    def _generatePad(self):
        if self.chamfer_size[0] >= self.size[0] or self.chamfer_size[1] >= self.size[1]:
            raise ValueError('Chamfer size ({}) too large for given pad size ({})'.format(self.chamfer_size, self.size))

        is_chamfered = False
        if self.corner_selection.isAnySelected() and self.chamfer_size[0] > 0 and self.chamfer_size[1] > 0:
            is_chamfered = True

        radius = self.round_radius_handler.getRoundRadius(min(self.size))

        if is_chamfered:
            outside = Vector2D(self.size.x/2, self.size.y/2)

            inside = [Vector2D(outside.x, outside.y-self.chamfer_size.y),
                      Vector2D(outside.x-self.chamfer_size.x, outside.y)
                      ]

            polygon_width = 0
            if self.round_radius_handler.roundingRequested():
                if abs(self.chamfer_size[0] - self.chamfer_size[1]) > 1e-7:     # consider rounding errors
                    raise NotImplementedError(
                            'Rounded chamfered pads are only supported for 45 degree chamfers.'
                            ' Chamfer {}'.format(self.chamfer_size)
                            )
                # We prefer the use of rounded rectangle over chamfered pads.
                r_chamfer = self.chamfer_size[0] + sqrt(2)*self.chamfer_size[0]/2
                if radius >= r_chamfer:
                    is_chamfered = False
                elif radius > 0:
                    shortest_sidlength = min(min(self.size-self.chamfer_size), self.chamfer_size[0]*sqrt(2))
                    if radius > shortest_sidlength/2:
                        radius = shortest_sidlength/2
                    polygon_width = radius*2
                    outside -= radius
                    inside[0].y -= radius*(2/sqrt(2)-1)
                    inside[0].x -= radius
                    inside[1].x -= radius*(2/sqrt(2)-1)
                    inside[1].y -= radius

        if is_chamfered:
            points = []
            corner_vectors = [
                Vector2D(-1, -1), Vector2D(1, -1), Vector2D(1, 1), Vector2D(-1, 1)
                ]
            for i in range(4):
                if self.corner_selection[i]:
                    points.append(corner_vectors[i]*inside[i % 2])
                    points.append(corner_vectors[i]*inside[(i+1) % 2])
                else:
                    points.append(corner_vectors[i]*outside)

            primitives = [Polygon(shape=points, width=polygon_width, fill=True, **self.mirror)]
            # TODO make size calculation more resilient
            size = min(self.size.x, self.size.y)-max(self.chamfer_size[0], self.chamfer_size[1])/sqrt(2)
            if size <= 0:
                raise ValueError('Anchor pad size calculation failed.'
                                 'Chamfer size ({}) to large for given pad size ({})'
                                 .format(self.size, self.chamfer_size))
            return Pad(primitives=primitives, at=self.at,
                       shape=Pad.SHAPE_CUSTOM, size=size, **self.padargs)
        else:
            return Pad(
                    at=self.at, shape=Pad.SHAPE_ROUNDRECT, size=self.size,
                    round_radius_handler=self.round_radius_handler, **self.padargs
                )

    def chamferAvoidCircle(self, center, diameter, clearance=0):
        r""" set the chamfer such that the pad avoids a circle located at near corner.

        :param center: (``Vector2D``) --
           The center of the circle to avoid
        :param diameter: (``float``, ``Vector2D``) --
           The diameter of the circle. If Vector2D given only x direction is used.
        :param clearance: (``float``) --
           Additional clearance around circle. default:0
        """

        relative_center = Vector2D(center) - self.at
        # pad and circle are symmetric so we do not care which corner the
        # reference circle is located at.
        #  -> move it to bottom right to get only positive relative coordinates.
        relative_center = Vector2D([abs(v) for v in relative_center])
        d = diameter if type(diameter) in [float, int] else diameter.x

        # Where should the chamfer be if the center of the reference circle
        # would be in line with the pad edges
        # (meaning exactly at the bottom right corner)
        reference_point = relative_center - sqrt(2)*(clearance+d/2)
        self.chamfer_size = self.size/2 - reference_point

        # compensate for reference circles not placed exactly at the corner
        edge_to_center = relative_center - self.size/2
        self.chamfer_size -= [edge_to_center.y, edge_to_center.x]
        self.chamfer_size = Vector2D([x if x > 0 else 0 for x in self.chamfer_size])

        self.pad = self._generatePad()
        return self.chamfer_size

    def getVirtualChilds(self):
        return [self.pad]

    def getRoundRadius(self):
        return self.pad.getRoundRadius()
