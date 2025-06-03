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
from kilibs.geom import GeomTrapezoid, Vec2DCompatible

# pep8: noqa
# flake8: noqa: E501


class Trapezoid(NodeShape, GeomTrapezoid):
    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        shape: Trapezoid | GeomTrapezoid | None = None,
        size: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        corner_radius: float | None = None,
        side_angle: float | None = None,
        rotation_angle: float = 0,
        use_degrees: bool = True,
    ):
        r"""Create a geometric isosceles trapezoid. That is a trapezoid with a symmetry
        axis. It has the option to round its corners.

        .. aafig::
            :rounded:

            angle<0
                  +---------------------+     ^
                 /                       \    |
                /            o            \  size.y
               /                           \  |
              +-----------------------------+ v
              <------------size.x----------->

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the trapezoid is filled, `False` if only the outline is
                visible.
            offset: Amount by which the trapezoid is inflated or deflated (if offset is
                negative).
            shape: Shape from which to derive the parameters of the trapezoid.
            size: Width and height of the trapezoid in mm.
            center: Coordinates of the center point of the trapezoid in mm.
            start: Coordinates of the top left corner of the trapezoid in mm.
            corner_radius: Radius of the rounding of the corners in mm. Defaults to zero
                if `None`.
            side_angle: Angle as depicted in the figure above (internally stored in
                degrees).
            rotation_angle: Rotation angle of the trapezoid (internally stored in
                degrees).
            use_degrees: `True` if the rotation angle is given in degrees, `False` if
                given in radians.
            use_degrees: bool = True,
        """
        self.init_super(kwargs=locals())
