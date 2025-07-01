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

"""Class definition for a cross."""

from __future__ import annotations

from typing import cast

from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.NodeShape import NodeShape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomCross, Vec2DCompatible


class Cross(NodeShape, GeomCross):
    """A cross.

    Crosses are drawn with a lot, and using text is fiddly because the KiCad font does
    not put the centre of "+" on the baseline. Also, a real cross, positioned exactly,
    allows users to snap to the center point.
    """

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        shape: Cross | GeomCross | None = None,
        center: Vec2DCompatible | None = None,
        size: Vec2DCompatible | float | None = None,
        angle: float = 0.0,
    ) -> None:
        """Create a cross node.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            shape: Shape from which to derive the parameters of the cross.
            center: Coordinates (in mm) of the center point of the cross.
            size: Size in mm of the cross. If a vector is given, the two lines of the
                cross have the length of the respective vector coordinates.
            angle: Angle of the cross in degrees.

        Example:
            The constructor either takes a `shape` argument or `center` and `size`.

            >>> cross1 = Cross(center=(0, 0), size=1)
            >>> cross2 = Cross(shape=cross1)
        """
        NodeShape.__init__(self, layer=layer, width=width, style=style)
        GeomCross.__init__(
            self,
            shape=shape,
            center=center,
            size=size,
            angle=angle,
        )

    def get_flattened_nodes(self) -> list[Node]:
        """Return the nodes to serialize."""
        return cast(list[Node], self.to_child_nodes(list(self.get_shapes())))
