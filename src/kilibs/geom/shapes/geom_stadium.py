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

"""Class definition for a geometric stadium."""

from __future__ import annotations

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomStadium(GeomShapeClosed):
    """A geometric stadium."""

    points: list[Vector2D]
    """The coordinates of the two arc centers in mm."""
    radius: float
    """The radius of the two arcs in mm."""
    _shapes: list[GeomLine | GeomArc]
    """The list of shapes the stadium is composed of."""

    def __init__(
        self,
        shape: GeomStadium | GeomRectangle | None = None,
        center_1: Vec2DCompatible | None = None,
        center_2: Vec2DCompatible | None = None,
        radius: float | None = None,
    ):
        """Create a geometric stadium.

        Args:
            shape: Shape from which to derive the parameters of the stadium. When a
                `GeomRectangle` is passed, then the stadium is inscribed in that
                rectangle.
            center_1: Coordinates (in mm) of the center of the first semi-circle.
            center_2: Coordinates (in mm) of the center of the second semi-circle.
            radius: The radius of the semi-circles in mm.
        """
        if shape is not None:
            if isinstance(shape, GeomStadium):
                self.points = [shape.points[0].copy(), shape.points[1].copy()]
                self.radius = shape.radius
            else:  # isinstance(shape, GeomRectangle):
                # The stadium is inscribed in a rectangle.
                if shape.size.x > shape.size.y:
                    self.radius = shape.size.y / 2
                    self.points = [
                        Vector2D(shape.left + self.radius, shape.center.y),
                        Vector2D(shape.right - self.radius, shape.center.y),
                    ]
                else:
                    self.radius = shape.size.x / 2
                    self.points = [
                        Vector2D(shape.center.x, shape.top + self.radius),
                        Vector2D(shape.center.x, shape.bottom - self.radius),
                    ]
        elif center_1 is not None and center_2 is not None and radius is not None:
            self.points = [Vector2D(center_1), Vector2D(center_2)]
            self.radius = radius
        else:
            raise KeyError(
                "Either `shape` or `center_1`, `center_2` and 'radius' must be provided."
            )
        self._shapes = []

    def get_shapes_back_compatible(self) -> list[GeomLine | GeomArc]:
        """Return a list containing the shapes that this shape is composed of."""
        c1 = self.points[0]
        c2 = self.points[1]
        # centre 1 to centre 2 vector
        c_vec = c2 - c1
        perp_vec = c_vec.orthogonal().resize(self.radius)
        # Vector from centre 2 to arc mid point
        c_to_arc_mid = c_vec.resize(self.radius)
        return [
            GeomArc(start=c1 + perp_vec, mid=c1 - c_to_arc_mid, end=c1 - perp_vec),
            GeomLine(start=c1 - perp_vec, end=c2 - perp_vec),
            GeomArc(start=c2 + perp_vec, end=c2 - perp_vec, mid=c2 + c_to_arc_mid),
            GeomLine(start=c1 + perp_vec, end=c2 + perp_vec),
        ]

    def get_shapes(self) -> list[GeomLine | GeomArc]:
        """Return a list containing the shapes that this shape is composed of in
        clockwise order."""
        if self._shapes:
            return self._shapes
        c1 = self.points[0]
        c2 = self.points[1]
        # centre 1 to centre 2 vector
        c_vec = c2 - c1
        perp_vec = c_vec.orthogonal().resize(self.radius)
        # Vector from centre 2 to arc mid point
        c_to_arc_mid = c_vec.resize(self.radius)
        self._shapes = [
            GeomArc(start=c1 + perp_vec, mid=c1 - c_to_arc_mid, end=c1 - perp_vec),
            GeomLine(start=c1 - perp_vec, end=c2 - perp_vec),
            GeomArc(start=c2 - perp_vec, mid=c2 + c_to_arc_mid, end=c2 + perp_vec),
            GeomLine(start=c2 + perp_vec, end=c1 + perp_vec),
        ]
        return self._shapes

    def invalidate_shapes(self) -> None:
        """Invalidate the computed shapes that this shape is composed of."""
        self._shapes = []

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the stadium.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the stadium, `False`
            otherwise.
        """
        if self.is_point_on_self(point=point, tol=tol):
            return not strictly_inside
        # Check if the point is inside the two circles of the stadium:
        if (point - self.points[0]).norm() <= (self.radius + tol) or (
            point - self.points[1]
        ).norm() <= (self.radius + tol):
            return True
        # Check if the point is inside the rectangular area of the stadium:
        # Check if the given point is always on the right side of its lines when the
        # lines are defining the rectangle in clockwise direction:
        c_vec = self.points[1] - self.points[0]
        perp_vec = c_vec.orthogonal().resize(self.radius)
        c = [
            self.points[0] - perp_vec,
            self.points[1] - perp_vec,
            self.points[1] + perp_vec,
            self.points[0] + perp_vec,
        ]
        lines = [GeomLine(start=c[i], end=c[(i + 1) % 4]) for i in range(len(c))]
        for line in lines:
            cp = line.direction.cross_product(point - line.start)
            if cp.z < 0:
                return False
        return True

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the stadium."""
        return BoundingBox(self.points[0] - self.radius, self.points[1] + self.radius)

    def __repr__(self) -> str:
        """Return the string representation of the stadium."""
        return (
            f"GeomStadium("
            f"center1={self.points[0]}, "
            f"center2={self.points[1]}, "
            f"radius={self.radius})"
        )
