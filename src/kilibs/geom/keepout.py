from typing import List, Optional, Callable, TypeAlias
from abc import ABC, abstractmethod

from kilibs.geom import (
    BoundingBox,
    geometricLine,
    geometricCircle,
    geometricArc,
    Vector2D,
)
from kilibs.geom.geometric_util import BaseNodeIntersection


class Keepout(ABC):
    """
    This is a geometric representation of a keepout  - not in the PCB sense, but in a
    geometric sense for limiting the extent of other geometric objects.

    The general idea is that a keepout can be applied to a line, circle or arc, and
    the result is either:
      - None: The object is entirely unaffected by the keepout (i.e. it is entirely outside)
      - An empty list: The object is entirely inside the keepout (i.e. it is entirely deleted)
      - A list of objects: The object is partially inside the keepout, and the list contains
        the parts of the object that are outside the keepout.

    For example: a rectangular keepout applied to these three lines:

      +--------------+
      |   -----(A)   |
      |          --------(B)
      |              |   -----(C)
      +--------------+

    The result would be:

      +--------------+
      |              |
      |              |---(B)
      |              |   -----(C)
      +--------------+
    """

    # A function that takes a point and returns True or False
    PointPredicate: TypeAlias = Callable[[Vector2D], bool]

    @abstractmethod
    def keepout_line(self, seg: geometricLine) -> Optional[List[geometricLine]]:
        """
        :return list of split lines (can be empty if the line is entirely inside the keepout)
                or None if the line is entirely unaffectected
        """
        raise NotImplementedError()

    @abstractmethod
    def keepout_circle(self, circle: geometricCircle) -> Optional[List[geometricArc]]:
        """
        :return list of arcs (can be empty if the circle is entirely inside the keepout)
                or None if the circle is entirely unaffected
        """
        raise NotImplementedError()

    @abstractmethod
    def keepout_arc(self, arc: geometricArc) -> Optional[List[geometricArc]]:
        """
        :return list of arcs (can be empty if the arc is entirely inside the keepout)
                or None if the arc is entirely unaffected
        """
        raise NotImplementedError()

    @abstractmethod
    def contains(self, pt: Vector2D) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def bounding_box(self) -> BoundingBox:
        raise NotImplementedError()

    @staticmethod
    def _cutSegmentByIntersections(
        seg: geometricLine, intersections, point_inside_func: PointPredicate
    ):
        """
        Cut a line segment by the given intersections

        This only works for up to two intersections (i.e. it assumes a convex shape) for now.

        :return the cut line segments, or None if the line is entirely unaffected
        """

        # Line entirely inside (convext shape)
        if point_inside_func(seg.start_pos) and point_inside_func(seg.end_pos):
            return []

        # Line bypasses entirely
        if len(intersections) == 0:
            return None

        # sort intersections by distance from the start of the segment
        intersections += [seg.start_pos, seg.end_pos]
        intersections.sort(key=lambda pt: (pt - seg.start_pos).norm())

        segs = []

        for i in range(len(intersections) - 1):
            # Skip very close intersections as null lines
            if intersections[i].distance_to(intersections[i + 1]) < 1e-7:
                continue

            # Exploit the convex shape to determine if the midpoint is inside
            midpoint = (intersections[i] + intersections[i + 1]) / 2
            if not point_inside_func(midpoint):
                segs.append(
                    geometricLine(start=intersections[i], end=intersections[i + 1])
                )

        return segs

    @staticmethod
    def _arcsFromIntersections(
        center: Vector2D,
        intersections: list,
        point_inside_func: PointPredicate,
    ):
        segments = []
        for i in range(len(intersections) - 1):
            start = intersections[i]
            end = intersections[i + 1]

            sa = (start - center).arg()
            ea = (end - center).arg()

            # Angles are sorted, so this must be the wrap-around case
            if ea < sa:
                angle = (ea + 180) + (180 - sa)
            else:
                angle = ea - sa

            arc = geometricArc(center=center, start=start, angle=angle)
            # reject if the arc midpoint is inside the keepout
            if not point_inside_func(arc.getMidPoint()):
                segments.append(arc)

        return segments

    @staticmethod
    def _arcsFromCircleIntersections(
        center, intersections: list, point_inside_func: PointPredicate
    ):
        # Sort intersections by angle around the circle, doesn't matter where the start is
        intersections.sort(key=lambda pt: (pt - center).arg())

        # Include the last intersection to first intersection to close the circle
        intersections.append(intersections[0])

        # It doesn't matter which way round we go, we cover the whole circle
        return Keepout._arcsFromIntersections(center, intersections, point_inside_func)

    @staticmethod
    def _arcsFromArcIntersections(
        arc: geometricArc, intersections: list, point_inside_func: PointPredicate
    ):
        arc_start_angle = (arc.start_pos - arc.center_pos).arg()
        c = arc.center_pos

        def _get_pt_angle_from_start(pt):
            a = (pt - arc.center_pos).arg() - arc_start_angle

            # Make sure the angle difference matches the arc's winding direction
            if arc.angle > 0:
                if a < 0:
                    a += 360
            else:
                if a > 0:
                    a -= 360

            return a

        # Sort intersections by angle around the arc, from the start
        # It doesn't actually matter which direction the list is in, as long as it
        # is monotonic in angle from start to end.
        intersections.append(arc.start_pos)
        intersections.append(arc.getEndPoint())
        intersections.sort(key=_get_pt_angle_from_start)

        return Keepout._arcsFromIntersections(c, intersections, point_inside_func)


class KeepoutRect(Keepout):
    """
    A rectangular keepout area, defined by a center and size
    """

    def __init__(self, center: Vector2D, size: Vector2D):
        if not isinstance(center, Vector2D):
            center = Vector2D(center)
        if not isinstance(size, Vector2D):
            size = Vector2D(size)

        # Ensure the size is poitive
        if size.x < 0:
            center.x -= size.x
            size.x = abs(size.x)

        if size.y < 0:
            center.y -= size.y
            size.y = abs(size.y)

        self.x = center.x
        self.y = center.y
        self.w = size.x
        self.h = size.y

        # Pre-calculate useful values we will use a lot
        self.left = center.x - size.x / 2
        self.right = center.x + size.x / 2
        self.top = center.y - size.y / 2
        self.bottom = center.y + size.y / 2

        self.top_side = geometricLine(
            start=[self.left, self.top], end=[self.right, self.top]
        )
        self.bottom_side = geometricLine(
            start=[self.left, self.bottom], end=[self.right, self.bottom]
        )
        self.left_side = geometricLine(
            start=[self.left, self.top], end=[self.left, self.bottom]
        )
        self.right_side = geometricLine(
            start=[self.right, self.top], end=[self.right, self.bottom]
        )

        self._bbox = BoundingBox(
            Vector2D(self.left, self.top), Vector2D(self.right, self.bottom)
        )

    def __str__(self):
        return f"KeepoutRect(center=({self.x}, {self.y}), size=({self.w}, {self.h}))"

    def contains(self, pt: Vector2D, tol=1e-7) -> bool:
        """
        Does the rectangle contain a point?

        This excludes points on, or within tol of, the rectangle edges, as a keepout
        can have a line running excatly along the edge.
        """
        return (
            (self.left + tol < pt.x < self.right - tol)
            and (self.top + tol < pt.y < self.bottom - tol)
        )

    @property
    def bounding_box(self):
        return self._bbox

    def _circle_inside(self, circle: geometricCircle) -> bool:
        return (
            self.left <= circle.center_pos.x - circle.radius
            and self.right >= circle.center_pos.x + circle.radius
            and self.top <= circle.center_pos.y - circle.radius
            and self.bottom >= circle.center_pos.y + circle.radius
        )

    def keepout_line(self, seg: geometricLine):

        tol = 1e-7

        l1_inside = self.contains(seg.start_pos, tol=tol)
        l2_inside = self.contains(seg.end_pos, tol=tol)

        # if both points are inside the keepout, the line is completely inside
        # as this is a convex shape
        if l1_inside and l2_inside:
            return []

        intersections = []

        # Optimisation opportunity to find obvious bypasses when both points are
        # all to one side of the rectangle
        if (
            (seg.start_pos.x <= self.left + tol and seg.end_pos.x <= self.left + tol)
            or (seg.start_pos.x >= self.right - tol and seg.end_pos.x >= self.right - tol)
            or (seg.start_pos.y <= self.top + tol and seg.end_pos.y <= self.top + tol)
            or (seg.start_pos.y >= self.bottom - tol and seg.end_pos.y >= self.bottom - tol)
        ):
            return None

        for side in [self.top_side, self.bottom_side, self.left_side, self.right_side]:
            side_intersections = BaseNodeIntersection.intersectTwoSegments(seg, side)

            if side_intersections:
                intersections += side_intersections

        return Keepout._cutSegmentByIntersections(seg, intersections, self.contains)

    def keepout_circle(self, circle: geometricCircle):

        # Check if the circle is entirely inside the rectangle (i.e. entirely kept out)
        if self._circle_inside(circle):
            return []

        intersections = []

        # Check for intersections with each side of the rectangle
        for side in [self.top_side, self.bottom_side, self.left_side, self.right_side]:
            side_intersections = BaseNodeIntersection.intersectSegmentWithCircle(
                side, circle, reject_tangents=True,
            )

            if side_intersections:
                intersections += side_intersections

        # No intersections, so the circle must be entirely outside the rectangle
        # (as we already checked for the circle being entirely inside)
        if not intersections:
            return None

        arcs = Keepout._arcsFromCircleIntersections(
            circle.center_pos, intersections, self.contains
        )
        return arcs

    def keepout_arc(self, arc: geometricArc):

        intersections: list[Vector2D] = []

        # Check for intersections with each side of the rectangle
        for side in [self.top_side, self.bottom_side, self.left_side, self.right_side]:
            side_intersections = BaseNodeIntersection.intersectSegmentWithArc(
                side, arc, include_arc_endpoints=False
            )

            if side_intersections:
                intersections += side_intersections

        if not intersections:
            # The arc is entirely inside the rectangle or entirely outside

            # If the midpoint is inside, it is entirely inside
            # Don't check the start/end: they could be on the boundary
            if self.contains(arc.getMidPoint()):
                return []

            # none of the arc is inside, so it must be entirely outside
            return None

        return Keepout._arcsFromArcIntersections(arc, intersections, self.contains)


class KeepoutRound(Keepout):
    """
    A circular keepout area, defined by a center and radius
    """

    def __init__(self, center: Vector2D, radius: float):
        self.center = Vector2D(center)
        self.radius = radius

        self._circle = geometricCircle(center=self.center, radius=self.radius)

        self._bbox = BoundingBox(
            Vector2D(self.center.x - radius, self.center.y - radius),
            Vector2D(self.center.x + radius, self.center.y + radius),
        )

    def __str__(self):
        return f"KeepoutRound(center=({self.center.x}, {self.center.y}), radius={self.radius})"

    def contains(self, pt) -> bool:
        return (pt - self.center).norm() <= self.radius

    @property
    def bounding_box(self):
        return self._bbox

    def keepout_line(self, seg: geometricLine):

        intersections = BaseNodeIntersection.intersectSegmentWithCircle(
            seg, self._circle, reject_tangents=True
        )

        # TODO: Optimisation opportunity to find obvious bypasses
        bits = Keepout._cutSegmentByIntersections(seg, intersections, self.contains)
        return bits

    def keepout_circle(self, circle: geometricCircle):
        tol = 1e-7

        if (self._circle.center_pos - circle.center_pos).norm() < tol:
            if self._circle.radius < circle.radius:
                # Circle outside
                return None
            # Circle inside
            return []

        def _circle_inside(circle: geometricCircle) -> bool:
            # Distance between the centers
            d_c = (self._circle.center_pos - circle.center_pos).norm()

            return d_c + circle.radius <= self.radius

        # Check if the circle is entirely inside the rectangle (i.e. entirely kept out)
        if _circle_inside(circle):
            return []

        intersections = BaseNodeIntersection.intersectTwoCircles(circle, self._circle)

        # No intersections, so the circle must be entirely outside the rectangle
        # (as we already checked for the circle being entirely inside)
        if not intersections:
            return None

        if len(intersections) == 1:
            # The circle is tangent to the keepout circle, so we can treat is as not clipping
            # out a section of the kept-out circle
            return None

        arcs = Keepout._arcsFromCircleIntersections(
            circle.center_pos, intersections, self.contains
        )
        return arcs

    def keepout_arc(self, arc: geometricArc):
        tol = 1e-7

        arc_rad = arc.getRadius()
        if (self._circle.center_pos - arc.center_pos).norm() < tol:
            if self._circle.radius < arc_rad:
                # Arc outside
                return None
            # Arc inside
            return []

        intersections = BaseNodeIntersection.intersectCircleWithArc(
            self._circle, arc, reject_tangents=True, tol=tol
        )

        if not intersections:
            # The arc is entirely inside the circle or entirely outside

            # If any part of it is inside, it is entirely inside
            if self.contains(arc.start_pos):
                return []

            # none of the arc is inside, so it must be entirely outside
            return None

        arcs = Keepout._arcsFromArcIntersections(arc, intersections, self.contains)
        return arcs
