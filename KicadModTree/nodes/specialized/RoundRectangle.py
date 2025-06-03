# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

from __future__ import annotations

from KicadModTree import LineStyle, NodeShape
from kilibs.geom import GeomRoundRectangle, Vec2DCompatible


class RoundRectangle(NodeShape, GeomRoundRectangle):
    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        shape: RoundRectangle | GeomRoundRectangle | None = None,
        size: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        corner_radius: float | None = None,
        angle: float = 0,
        use_degrees: bool = True,
    ):
        r"""Create a geometric round rectangle. That is a rectangle with all four
        corners rounded:

        .. aafig::
            :rounded:

              /--------\
              |        |
              |        |
              |        |
              |        |
              |        |
              \--------/

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the round rectangle is filled, `False` if only the outline
                is visible.
            offset: Amount by which the round rectangle is inflated or deflated (if
                offset is negative).
            shape: Shape from which to derive the parameters of the round rectangle.
            size: Width and height of the roundrect in mm.
            center: Coordinates of the center point of the round rectangle in mm.
            corner_radius: Radius of the rounding of the corners in mm.
            start: Coordinates of the first corner of the (round) rectangle in mm.
            angle: Rotation angle of the round rectangle (internally stored in degrees).
            use_degrees: `True` if the rotation angle is given in degrees, `False` if
                given in radians.
        """
        self.init_super(kwargs=locals())
