from typing import Optional
from typing_extensions import Self  # After 3.11 -> typing.Self

from KicadModTree import Vector2D


class BoundingBox:

    min: Optional[Vector2D]
    max: Optional[Vector2D]

    def __init__(self, min_pt: Vector2D = None, max_pt: Vector2D = None):

        if (min_pt is None) != (max_pt is None):
            raise ValueError("Must provide both min and max or neither")

        self.min = min_pt
        self.max = max_pt

    def include_point(self, point: Vector2D):

        if self.min is None:
            self.min = point
            self.max = point
        else:
            self.min = Vector2D(min(self.min.x, point.x), min(self.min.y, point.y))
            self.max = Vector2D(max(self.max.x, point.x), max(self.max.y, point.y))

    def include_bbox(self, bbox: Self):
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
