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


class Translation(Node):
    """Apply translation to the child tree

    :param x: change of x coordinate, or a whole Vector2D
    :type x: ``float``
    :param y: change of y coordinate
    :type y: ``float``

    :Example:

    >>> from KicadModTree import *
    >>> Translation(1, 2)
    """
    def __init__(self, x: float | Vector2D, y: float | None = None):
        Node.__init__(self)

        if isinstance(x, Vector2D):
            assert y is None, "If x is a Vector2D, y must be None"
            x, y = x.x, x.y

        # translation information
        self.offset_x = x
        self.offset_y = y

    def getRealPosition(self, coordinate, rotation=None):
        parsed_coordinate = Vector2D(coordinate)

        # calculate translation
        translation_coordinate = {'x': parsed_coordinate.x + self.offset_x,
                                  'y': parsed_coordinate.y + self.offset_y}

        if not self._parent:
            if rotation is None:
                return translation_coordinate
            else:
                return translation_coordinate, rotation
        else:
            return self._parent.getRealPosition(translation_coordinate, rotation)

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)
        render_text += " [x: {x}, y: {y}]".format(x=self.offset_x,
                                                  y=self.offset_y)

        return render_text

    def calculateBoundingBox(self):

        bbox = BoundingBox()

        for child in self.getAllChilds():
            child_bbox = child.calculateBoundingBox()
            bbox.include_bbox(child_bbox)

        offset = Vector2D(self.offset_x, self.offset_y)

        # translate the bounding box
        return BoundingBox(
            bbox.min + offset, bbox.max + offset
        )
