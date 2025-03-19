from typing import Optional
from typing_extensions import Self  # After 3.11 -> typing.Self

from kilibs.geom import Vector2D
from kilibs.geom.geometric_util import geometricLine


class BoundingBox:

    min: Optional[Vector2D]
    max: Optional[Vector2D]

    def __init__(
        self, min_pt: Optional[Vector2D] = None, max_pt: Optional[Vector2D] = None
    ):

        if (min_pt is None) != (max_pt is None):
            raise ValueError("Must provide both min and max or neither")

        self.min = min_pt
        self.max = max_pt

    def include_point(self, point: Vector2D):

        if self.min is None:
            self.min = point
            self.max = point
        else:
            assert self.max is not None
            self.min = Vector2D(min(self.min.x, point.x), min(self.min.y, point.y))
            self.max = Vector2D(max(self.max.x, point.x), max(self.max.y, point.y))

    def include_bbox(self, bbox: Self):

        if bbox.min is not None:
            assert bbox.max is not None
            self.include_point(bbox.min)
            self.include_point(bbox.max)

    def _expect_nonempty(self):
        if self.min is None or self.max is None:
            raise RuntimeError("Cannot access empty bounding box")

    @property
    def top(self):
        self._expect_nonempty()
        return self.min.y

    @property
    def bottom(self):
        self._expect_nonempty()
        return self.max.y

    @property
    def left(self):
        self._expect_nonempty()
        return self.min.x

    @property
    def right(self):
        self._expect_nonempty()
        return self.max.x

    @property
    def size(self) -> Vector2D:
        self._expect_nonempty()
        return self.max - self.min

    @property
    def center(self) -> Vector2D:
        self._expect_nonempty()
        return (self.min + self.max) / 2

    def contains_point(self, point: Vector2D) -> bool:
        """
        Test if a point is inside the bounding box
        """
        # A null bbox won't contain any point
        if self.min is None:
            return False

        return (
            self.min.x <= point.x <= self.max.x and self.min.y <= point.y <= self.max.y
        )

    def contains_bbox(self, bbox: Self) -> bool:
        """
        Test if another bounding box is completely inside this one
        """
        if self.min is None or bbox.min is None:
            return False

        return (
            self.min.x <= bbox.min.x
            and self.min.y <= bbox.min.y
            and self.max.x >= bbox.max.x
            and self.max.y >= bbox.max.y
        )

    def contains_seg(self, line: geometricLine) -> bool:
        """
        Test if a line segment is completely inside this bounding box
        """
        return self.contains_point(line.start) and self.contains_point(line.end)
