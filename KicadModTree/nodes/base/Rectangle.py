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
from kilibs.geom import BoundingBox, GeomRectangle, Vec2DCompatible, Vector2D


class Rectangle(NodeShape, GeomRectangle):
    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        shape: Rectangle | GeomRectangle | BoundingBox | None = None,
        start: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        size: Vec2DCompatible | None = None,
        angle: float = 0,
        use_degrees: bool = True,
    ):
        """Create a rectangle.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the rectangle is filled, `False` if only the outline is
                visible.
            offset: Amount by which the rectangle is inflated or deflated (if offset is
                negative).
            shape: Shape from which to derive the parameters of the rectangle.
            center: Coordinates (in mm) of the center point of the rectangle.
            size: Size in mm of the rectangle.
            start: Coordinates (in mm) of the top left corner of the rectangle.
            stop: Coordinates (in mm) of the bottom right corner of the rectangle.
            angle: Rotation angle of the rectangle.
            use_degrees: Whether the rotation angle is given in degrees or radians.
        """
        self.init_super(kwargs=locals())
        # for backwards compatibility:
        if start is not None:
            self.start = Vector2D(start)
        elif shape is not None:
            self.start = self.top_left
        if end is not None:
            self.end = Vector2D(end)
        elif shape is not None:
            self.end = self.bottom_right
