from typing import List
from typing_extensions import Self  # After 3.11 -> typing.Self

from KicadModTree import Vector2D
# Despite the name, this is a pure geometry class
from KicadModTree import PolygonPoints

from scripts.tools.drawing_tools import roundGUp, roundGDown

from .bounding_box import BoundingBox


class Rectangle:
    """
    A simple 2D rectangle
    """

    def __init__(self, center: Vector2D, size: Vector2D):
        self.center = center
        self.size = Vector2D(abs(size.x), abs(size.y))

    @classmethod
    def by_corners(cls, corner1: Vector2D, corner2: Vector2D) -> Self:
        size = corner2 - corner1
        center = corner1 + size / 2
        return cls(center, size)

    @classmethod
    def by_corner_and_size(cls, corner: Vector2D, size: Vector2D) -> Self:
        center = corner + size / 2
        return cls(center, size)

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

    def rounded(self, outwards: bool, grid: float) -> Self:
        tl = self.top_left
        br = self.bottom_right

        if outwards:
            # doesn't matter where the rectangle is, the top-left goes up and left,
            # the bottom-right goes down and right
            new_tl = Vector2D(roundGDown(tl.x, grid), roundGDown(tl.y, grid))
            new_br = Vector2D(roundGUp(br.x, grid), roundGUp(br.y, grid))
        else:
            # The other way
            new_tl = Vector2D(roundGUp(tl.x, grid), roundGUp(tl.y, grid))
            new_br = Vector2D(roundGDown(br.x, grid), roundGDown(br.y, grid))

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
    def bounding_box(self) -> BoundingBox:
        return BoundingBox(
            Vector2D(self.left, self.bottom),
            Vector2D(self.right, self.top)
        )
