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

"""Class definition for a cruciform."""

from __future__ import annotations

from typing import cast

from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.NodeShape import NodeShape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomCruciform, Vec2DCompatible


class Cruciform(NodeShape, GeomCruciform):
    """A cruciform."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        shape: Cruciform | GeomCruciform | None = None,
        overall_w: float | None = None,
        overall_h: float | None = None,
        tail_w: float | None = None,
        tail_h: float | None = None,
        center: Vec2DCompatible = (0, 0),
        angle: float = 0.0,
    ) -> None:
        """Create a geometric cruciform.

        A cruciform is a cross-shaped object that is basically two rectangles
        that intersect at their centers.

        It looks like this:

        .. aafig::
                +-------+   -------------
                |       |               ^
            +---+       +---+ ----      |
            |               |    ^      |
            |       o       |    | t h  | overall h
            |               |    v      |
            +---+       +---+ ----      |
                |       |               v
            |   +-------+   +------------
            |   |<-t w->|   |
            |               |
            |<- overall w ->|

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the cruciform is filled, `False` if only the outline is
                visible.
            offset: Amount by which the cruciform is inflated or deflated (if offset is
                negative).
            shape: Shape from which to derive the parameters of the cruciform.
            overall_w: Overall width of the cruciform in mm.
            overall_h: Overall height of the cruciform in mm.
            tail_w: Width of the tail of the cruciform in mm.
            tail_h: Height of the tail of the cruciform in mm.
            center: Coordinates of the center point of the cruciform in mm.
            angle: Rotation angle of the cruciform in degrees.
        """
        NodeShape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomCruciform.__init__(
            self,
            shape=shape,
            overall_w=overall_w,
            overall_h=overall_h,
            tail_w=tail_w,
            tail_h=tail_h,
            center=center,
            angle=angle,
        )
        if offset:
            self.inflate(amount=offset)

    def get_flattened_nodes(self) -> list[Node]:
        """Return the nodes to serialize."""
        return cast(list[Node], self.to_child_nodes(list(self.get_shapes())))
