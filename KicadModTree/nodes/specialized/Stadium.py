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
from kilibs.geom import GeomRectangle, GeomStadium, Vec2DCompatible


class Stadium(NodeShape, GeomStadium):
    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        shape: Stadium | GeomStadium | GeomRectangle | None = None,
        center_1: Vec2DCompatible | None = None,
        center_2: Vec2DCompatible | None = None,
        radius: float | None = None,
    ):
        """Create a stadium shape, which is a rectangle with semi-circular ends.

        Sometimes called a racetrack shape, or oblong (that's also the name of a
        non-square rectangle), or obround, or oval. Stadium is about the only
        unambiguous name for this shape!

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the stadium is filled, `False` if only the outline is
                visible.
            offset: Amount by which the stadium is inflated or deflated (if offset is
                negative).
            shape: Shape from which to derive the parameters of the stadium. When a
                `GeomRectangle` is passed, then the stadium is inscribed in that
                rectangle.
            center_1: Coordinates (in mm) of the center of the first semi-circle.
            center_2: Coordinates (in mm) of the center of the second semi-circle.
            radius: The radius of the semi-circles in mm.

        Example:
            The following 3 stadiums are identical:

            .. code-block::

            >>> stadium1 = Stadium(center_1=(-1, 0), center_2=(+1, 0), radius = 1.0)
            >>> stadium2 = Stadium(shape=stadium1)
            >>> stadium3 = Stadium(shape=GeomRectangle(center=(0, 0), size=(4, 2)))
        """
        self.init_super(kwargs=locals())
