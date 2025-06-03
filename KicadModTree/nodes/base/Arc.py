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

from KicadModTree.nodes.NodeShape import NodeShape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomArc, Vec2DCompatible


class Arc(NodeShape, GeomArc):
    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        shape: Arc | GeomArc | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        mid: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
        angle: float | None = None,
        use_degrees: float = True,
        long_way: float = False,
    ):
        """Create an arc.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            shape: Arc from which to derive the parameters.
            center: Coordinates (in mm) of the center of the arc.
            start: Coordinates (in mm) of the start point of the arc.
            mid: Coordinates (in mm) of the mid point of the arc.
            end: Coordinates (in mm) of the end point of the arc.
            angle: Angle of the arc in radians or degrees (internally stored in
                degrees).
            use_degrees: Whether to interpret the angle in degrees or in radians.
            long_way: Used when constructing the arc with the center, start and end
                point to specify if the longer of the 2 possible resulting arcs or the
                shorter one shall be constructed.
        """
        self.init_super(kwargs=locals())
