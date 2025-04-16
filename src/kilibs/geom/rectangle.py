from typing import List
from typing_extensions import Self  # After 3.11 -> typing.Self

from kilibs.geom.vector import Vector2D
from kilibs.geom.polygon_points import PolygonPoints
from kilibs.geom.geometric_util import geometricLine

from .rounding import round_to_grid_up, round_to_grid_down
from .bounding_box import BoundingBox


class Rectangle:
    """
    A simple 2D rectangle
    """

    def __init__(self, center: Vector2D, size: Vector2D):
        self.center = Vector2D(center)
        self.size = Vector2D(abs(size.x), abs(size.y))

    @classmethod
    def by_corners(cls, corner1: Vector2D, corner2: Vector2D) -> Self:
        corner1 = Vector2D(corner1)
        corner2 = Vector2D(corner2)
        size = corner2 - corner1
        center = corner1 + size / 2
        return cls(center, size)

    @classmethod
    def by_corner_and_size(cls, corner: Vector2D, size: Vector2D) -> Self:
        corner = Vector2D(corner)
        size = Vector2D(size)
        center = corner + size / 2
        return cls(center, size)

    def __str__(self):
        return f"Rectangle(center={self.center}, size={self.size})"

    def __repr__(self):
        return str(self)

    def get_corners(self) -> List[Vector2D]:
        """
        Return the four corners of the rectangle
        """
        half_size = self.size / 2
        return [
            self.center - half_size,
            self.center + Vector2D(half_size.x, -half_size.y),
            self.center + half_size,
            self.center + Vector2D(-half_size.x, half_size.y)
        ]

    def get_polygon_points(self) -> PolygonPoints:
        """
        Return the four corners of the rectangle as a closed polygon
        """
        nodes = self.get_corners()
        nodes.append(nodes[0])
        return PolygonPoints(nodes=nodes)

    def rounded(self, outwards: bool, grid: float) -> "Rectangle":
        tl = self.top_left
        br = self.bottom_right

        if outwards:
            # doesn't matter where the rectangle is, the top-left goes up and left,
            # the bottom-right goes down and right
            new_tl = Vector2D(round_to_grid_down(tl.x, grid), round_to_grid_down(tl.y, grid))
            new_br = Vector2D(round_to_grid_up(br.x, grid), round_to_grid_up(br.y, grid))
        else:
            # The other way
            new_tl = Vector2D(round_to_grid_up(tl.x, grid), round_to_grid_up(tl.y, grid))
            new_br = Vector2D(round_to_grid_down(br.x, grid), round_to_grid_down(br.y, grid))

        return Rectangle.by_corners(new_tl, new_br)

    @property
    def min_dimension(self) -> float:
        return min(self.size.x, self.size.y)

    @property
    def max_dimension(self) -> float:
        return max(self.size.x, self.size.y)

    @property
    def left(self) -> float:
        return self.center.x - self.size.x / 2

    @property
    def right(self) -> float:
        return self.center.x + self.size.x / 2

    @property
    def top(self) -> float:
        return self.center.y - self.size.y / 2

    @property
    def bottom(self) -> float:
        return self.center.y + self.size.y / 2

    @property
    def bottom_left(self) -> Vector2D:
        return self.center + Vector2D(-self.size.x / 2, self.size.y / 2)

    @property
    def bottom_right(self) -> Vector2D:
        return self.center + Vector2D(self.size.x / 2, self.size.y / 2)

    @property
    def top_left(self) -> Vector2D:
        return self.center + Vector2D(-self.size.x / 2, -self.size.y / 2)

    @property
    def top_right(self) -> Vector2D:
        return self.center + Vector2D(self.size.x / 2, -self.size.y / 2)

    @property
    def right_midpoint(self) -> Vector2D:
        return Vector2D(self.right, self.center.y)

    @property
    def left_midpoint(self) -> Vector2D:
        return Vector2D(self.left, self.center.y)

    @property
    def top_midpoint(self) -> Vector2D:
        return Vector2D(self.center.x, self.top)

    @property
    def bottom_midpoint(self) -> Vector2D:
        return Vector2D(self.center.x, self.bottom)

    @property
    def bounding_box(self) -> BoundingBox:
        return BoundingBox(
            Vector2D(self.left, self.top),
            Vector2D(self.right, self.bottom)
        )

    def outset(self, outset: float):
        """
        Outset this rectangle by the given amounts. Negatve is an inset
        """

        if outset < 0:
            if abs(outset) > self.min_dimension / 2:
                raise ValueError(
                    f"Cannot inset by more than half the size (asked for {outset}), "
                    "min dimension is {self.min_dimension})"
                )

        self.size = self.size + 2 * Vector2D(outset, outset)

    def with_outset(self, outset: float) -> "Rectangle":
        """
        Return a new rectangle that is this rectangle outset by the given amounts
        """
        new_rect = Rectangle(self.center, self.size)
        new_rect.outset(outset)
        return new_rect

    def get_lines(self):

        """
        Return the four lines of the rectangle
        """

        # These are in a slightly wierd order, only because it avoided
        # some diffs. Feel free to change if you want, it should make no
        # difference to the graphical outcome.
        return [
            geometricLine(start=self.top_left, end=self.top_right),
            geometricLine(start=self.top_right, end=self.bottom_right),
            geometricLine(start=self.bottom_left, end=self.bottom_right),
            geometricLine(start=self.top_left, end=self.bottom_left)
        ]
