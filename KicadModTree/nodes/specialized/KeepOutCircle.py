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
# Created by Stefan Thorlacius stts@sencius.se
#

#
# This module uses a kind of "ray tracing" with a line comming from lower left
# to find where it intersect with a circle, these intersection points is then
# used to draw an "keep put" area within in the circle
#
from KicadModTree.Point import *
from KicadModTree.PolygonPoints import *
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Circle import Circle

import math


class KeepOutCircle(Node):
    r"""Add a Circle as a keep put area to the render tree

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *center* (``Vector2D``) --
          center of the circle
        * *radius* (``float``) --
          radius of the circle
        * *layer* (``str``) --
          layer on which the circle is drawn (default: 'Dwgs.User')
        * *width* (``float``) --
          width of the circle line (default: None, which means auto detection)
        * *step* (``float``) --
          the step betwene the crossing lines (default: 1 mm)

    :Example:

        from KicadModTree import *
        KeepOutCircle(center=[0, 0], radius=1.5, layer='F.SilkS')
    """

    def __init__(self, **kwargs):
        Node.__init__(self)
        self.center_pos = Vector2D(kwargs['center'])
        self.radius = kwargs['radius']

        self.end_pos = Vector2D([self.center_pos.x+self.radius, self.center_pos.y])

        self.layer = kwargs.get('layer', 'Dwgs.User')
        self.width = kwargs.get('width')
        self.step = kwargs.get('step', 1.0)
        #
        self.virtual_childs = []
        #
        # Add the circle
        #
        self.virtual_childs.append(Circle(center=self.center_pos, 
                                    radius=self.radius, layer=self.layer, width=self.width))

        Ax = self.center_pos[0] + (self.radius)
        Ay = self.center_pos[1] + (self.radius * 1.1)
        Bx = Ax + (2.5 * self.radius)
        By = Ay - (2.5 * self.radius)
        Cx = self.center_pos[0]
        Cy = self.center_pos[1]
        R = self.radius
        while Bx > (self.center_pos[0] - self.radius):
            Bx = Ax + (2.5 * self.radius)
            By = Ay - (2.5 * self.radius)
            # compute the triangle area times 2 (area = area2/2)
            area2 = math.fabs((Bx-Ax)*(Cy-Ay) - (Cx-Ax)*(By-Ay))
            # compute the AB segment length
            LAB = math.sqrt(((Bx-Ax) * (Bx-Ax)) + ((By-Ay) * (By-Ay)))
            # compute the triangle height
            h = area2 / LAB
            # if the line intersects the circle
            if (h < R):
                Dx = (Bx-Ax)/LAB
                Dy = (By-Ay)/LAB
                # compute the distance from A toward B of closest point to C
                t = Dx*(Cx-Ax) + Dy*(Cy-Ay)
                # compute the intersection point distance from t
                dt = math.sqrt((R * R) - (h * h))
                # compute first intersection point coordinate
                Ex = Ax + (t-dt)*Dx
                Ey = Ay + (t-dt)*Dy
                # compute second intersection point coordinate
                Fx = Ax + (t+dt)*Dx
                Fy = Ay + (t+dt)*Dy
                self.virtual_childs.append(Line(start=[round(Ex, 2), round(Ey, 2)], 
                    end=[round(Fx, 2), round(Fy, 2)], 
                    layer=self.layer, width=self.width))
#            self.virtual_childs.append(Line(start=[Ax, Ay], end=[Bx, By], layer='F.SilkS'))
            Ax = Ax - self.step

    def getVirtualChilds(self):
        #
        #
        return self.virtual_childs

    def calculateBoundingBox(self):
        min_x = self.center_pos.x-self.radius
        min_y = self.center_pos.y-self.radius
        max_x = self.center_pos.x+self.radius
        max_y = self.center_pos.y+self.radius

        return Node.calculateBoundingBox({'min': ParseXY(min_x, min_y), 'max': ParseXY(max_x, max_y)})

    def _getRenderTreeText(self):

        render_strings = ['fp_circle']
        render_strings.append(self.center_pos.render('(center {x} {y})'))
        render_strings.append(self.end_pos.render('(end {x} {y})'))
        render_strings.append('(layer {layer})'.format(layer=self.layer))
        render_strings.append('(width {width})'.format(width=self.width))

        render_text = Node._getRenderTreeText(self)
        render_text += ' ({})'.format(' '.join(render_strings))

        return render_text
