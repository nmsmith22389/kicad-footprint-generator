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

"""Class definition for a line."""

from __future__ import annotations

from KicadModTree.nodes.NodeShape import NodeShape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomLine, Vec2DCompatible


class Line(NodeShape, GeomLine):
    """A line."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        shape: Line | GeomLine | None = None,
        start: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
    ) -> None:
        """Create a Line.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            shape: Shape from which to derive the parameters of the line.
            start: Coordinates (in mm) of the start point of the line.
            end: Coordinates (in mm) of the end point of the line.
        """
        self.init_super(kwargs=locals())

    def get_flattened_nodes(self) -> list[Line]:
        """Return the nodes to serialize."""
        return [self]
