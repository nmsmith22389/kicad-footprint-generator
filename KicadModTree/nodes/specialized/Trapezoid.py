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

"""Class definition for a trapezoid."""

from __future__ import annotations

from typing import cast

from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.NodeShape import NodeShape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomTrapezoid, Vec2DCompatible


class Trapezoid(NodeShape, GeomTrapezoid):
    """A trapezoid."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0.0,
        shape: Trapezoid | GeomTrapezoid | None = None,
        size: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        corner_radius: float | None = None,
        side_angle: float | None = None,
        rotation_angle: float = 0.0,
    ) -> None:
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
            side_angle: Angle as depicted in the figure above in degrees.
            rotation_angle: Rotation angle of the trapezoid in degrees.
        """
        NodeShape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomTrapezoid.__init__(
            self,
            shape=shape,
            size=size,
            center=center,
            start=start,
            corner_radius=corner_radius,
            side_angle=side_angle,
            rotation_angle=rotation_angle,
        )
        if offset:
            self.inflate(amount=offset)

    def get_flattened_nodes(self) -> list[Node]:
        """Return the nodes to serialize."""
        return cast(list[Node], self.to_child_nodes(list(self.get_shapes())))
