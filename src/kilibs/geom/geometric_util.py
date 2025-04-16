# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

import math
from typing import List, TypeAlias, TYPE_CHECKING

from kilibs.geom.vector import Vector2D

# Break circular import between BBox and geometric primitives
if TYPE_CHECKING:
    from kilibs.geom.bounding_box import BoundingBox


geometricPrimitive: TypeAlias = "geometricLine | geometricCircle | geometricArc"


def isGeometricPrimitive(obj):
    """
    Check if an object's (sub)class is a geometric object defined in here
    """
    return isinstance(obj, (geometricLine, geometricCircle, geometricArc))


def normalizeAngle(angle, use_degrees=True):
    if (use_degrees):
        return (angle + 180) % 360 - 180
    else:
        return (angle + math.pi) % (2 * math.pi) - math.pi


class geometricLine():
    r""" Handle the geometric side of lines

    :params:
        * *start* (``Vector2D``) --
          start point of the line
        * *end* (``Vector2D``) --
          end point of the line
    """

    start_pos: Vector2D
    end_pos: Vector2D

    def __init__(self, **kwargs):
        if 'geometry' in kwargs:
            geometry = kwargs['geometry']
            self.start_pos = Vector2D(geometry.start_pos)
            self.end_pos = Vector2D(geometry.end_pos)
        else:
            self.start_pos = Vector2D(kwargs['start'])
            self.end_pos = Vector2D(kwargs['end'])

    def copy(self):
        return geometricLine(geometry=self)

    @property
    def length(self):
        return abs(self.start_pos - self.end_pos)

    def rotate(self, angle, origin=(0, 0), use_degrees=True):
        r""" Rotate around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.start_pos.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        self.end_pos.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        return self

    def translate(self, distance_vector):
        r""" Translate

        :params:
            * *distance_vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.start_pos += distance_vector
        self.end_pos += distance_vector
        return self

    def isPointOnSelf(self, point, tolerance_angle=1e-7, tolerance_radius=1e-15):
        r"""is the given point on this line

        :params:
            * *point* (``Vector2D``)
                The point to be checked
            * *tolerance* (``float``)
                tolerance used to determine if the point is on the element
                default: 1e-7
        """

        ll, la = (self.end_pos - self.start_pos).to_polar()
        pl, pa = (point - self.start_pos).to_polar()
        return (
            abs(normalizeAngle(la - pa)) < tolerance_angle
            and pl <= ll + tolerance_radius
        )

    def sortPointsRelativeToStart(self, points):
        r""" sort given points relative to start point

        :params:
            * *points* (``[Vector2D]``)
                itterable of points
        """

        if len(points) < 2:
            return points

        if len(points) > 2:
            raise NotImplementedError("Sorting for more than 2 points not supported")

        if self.start_pos.distance_to(points[0]) < self.start_pos.distance_to(points[1]):
            return points
        else:
            return [points[1], points[0]]

    def getMidPoint(self):
        return (self.start_pos + self.end_pos) / 2

    def isPointInsideSelf(self, point: Vector2D, tolerance: float = 1e-7):
        return self.isPointOnSelf(point=point, tolerance=tolerance)

    def cut(self, *other):
        r""" cut line with given other element

        :params:
            * *other* (``Line``, ``Circle``, ``Arc``)
                cut the element on any intersection with the given geometric element
        """
        ip = BaseNodeIntersection.intersectTwoNodes(self, *other)
        cp = []
        for p in ip:
            # only keep those intersection points which are part of the line and
            # the other contour. This avoids to keep points which are intersecting
            # the extended edges of a rectange
            if self.isPointOnSelf(p) and any(o.isPointOnSelf(p) for o in other):
                cp.append(p)

        sp = self.sortPointsRelativeToStart(cp)
        sp.insert(0, self.start_pos)
        sp.append(self.end_pos)

        r = []
        for i in range(len(sp)-1):
            r.append(geometricLine(start=sp[i], end=sp[i+1]))

        return r

    def to_homogeneous(self):
        r""" Get homogeneous representation of the line
        """
        p1 = self.start_pos.to_homogeneous()
        p2 = self.end_pos.to_homogeneous()
        return p1.cross_product(p2)

    def is_approx(self, other, ordered, tol=1e-7):

        same_order_close = (
            self.start_pos.is_close(other.start_pos, tol) and
            self.end_pos.is_close(other.end_pos, tol)
        )  # fmt: skip

        if ordered:
            return same_order_close

        rev_order_close = (
            self.start_pos.is_close(other.end_pos, tol) and
            self.end_pos.is_close(other.start_pos, tol)
        )  # fmt: skip

        return same_order_close or rev_order_close

    def __iter__(self):
        yield self.start_pos
        yield self.end_pos

    def __len__(self):
        return 2

    def __getitem__(self, key):
        if key == 0 or key == 'start':
            return self.start_pos
        if key == 1 or key == 'end':
            return self.end_pos

        raise IndexError('Index {} is out of range'.format(key))

    def __setitem__(self, key, item):
        if key == 0 or key == 'start':
            self.start_pos = item
        elif key == 1 or key == 'end':
            self.end_pos = item
        else:
            raise IndexError('Index {} is out of range'.format(key))

    def __str__(self) -> str:
        return f"geometricLine({self.start_pos}, {self.end_pos})"

    def __repr__(self) -> str:
        return self.__str__()


class geometricCircle():
    r"""Handle the geometric side of circles

    :params:
        * *center* (``Vector2D``) --
          center of the circle
        * *radius* (``float``) --
          radius of the circle
    """

    def __init__(
        self,
        center: Vector2D | None = None,
        radius: float | None = None,
        geometry: "geometricCircle" = None,
    ):
        if geometry is not None:
            self.center_pos = Vector2D(geometry.center_pos)
            self.radius = float(geometry.radius)
        else:
            self.center_pos = Vector2D(center)
            self.radius = float(radius)

    def getRadius(self):
        return self.radius

    def rotate(self, angle, origin=(0, 0), use_degrees=True):
        r""" Rotate around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.center_pos.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        return self

    def translate(self, distance_vector):
        r""" Translate

        :params:
            * *distance_vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.center_pos += distance_vector
        return self

    def getMidPoint(self):
        # there is no mid-point on a cirular line
        pass

    def isPointInsideSelf(self, point: Vector2D, tolerance: float = 1e-7):
        return Vector2D.norm(point - self.center_pos) <= self.radius + tolerance

    def isPointOnSelf(self, point, tolerance=1e-7):
        r""" is the given point on this circle

        :params:
            * *point* (``Vector2D``)
                The point to be checked
            * *tolerance* (``float``)
                tolerance used to determine if the point is on the element
                default: 1e-7
        """

        rad_p, ang_p = Vector2D(point).to_polar(origin=self.center_pos)
        return abs(self.radius - rad_p) < tolerance

    def sortPointsRelativeToStart(self, points):
        r""" sort given points relative to start point

        :params:
            * *points* (``[Vector2D]``)
                itterable of points
        """

        pass

    def cut(self, *other):
        r""" cut line with given other element

        :params:
            * *other* (``Line``, ``Circle``, ``Arc``)
                cut the element on any intersection with the given geometric element
        """

        # re use arc implementation with angle set to 360 deg
        # and start point set to 0 deg (polar)
        arc = geometricArc(center=self.center_pos, start=self.center_pos + Vector2D(0, self.radius), angle=360)
        return arc.cut(*other)

    @property
    def bounding_box(self) -> "BoundingBox":
        from kilibs.geom import BoundingBox
        return BoundingBox(
            Vector2D(self.center_pos.x - self.radius, self.center_pos.y - self.radius),
            Vector2D(self.center_pos.x + self.radius, self.center_pos.y + self.radius),
        )

    def __iter__(self):
        yield self.center_pos

    def __len__(self):
        return 1

    def __getitem__(self, key):
        if key == 0 or key == 'center':
            return self.center_pos

        raise IndexError('Index {} is out of range'.format(key))

    def __setitem__(self, key, item):
        if key == 0 or key == 'center':
            self.center_pos = item
        else:
            raise IndexError('Index {} is out of range'.format(key))

    def __str__(self) -> str:
        return f"geometricCircle(c={self.center_pos}, r={self.radius})"

    def __repr__(self) -> str:
        return self.__str__()


class geometricArc():
    r""" Handle the geometric side of arcs

    :params:
        * *center* (``Vector2D``) --
          center of arc
        * *start* (``Vector2D``) --
          start point of arc
        * *midpoint* (``Vector2D``) --
          alternative to start point
          point is on arc and defines point of equal distance to both arc ends
          arcs of this form are given as midpoint, center plus angle
        * *end* (``Vector2D``) --
          alternative to angle
          arcs of this form are given as start, end and center
        * *angle* (``float``) --
          angle of arc
    """

    def __init__(self, **kwargs):
        if 'geometry' in kwargs:
            geometry = kwargs['geometry']
            self.center_pos = Vector2D(geometry.center_pos)
            self.start_pos = Vector2D(geometry.start_pos)
            self.angle = float(geometry.angle)
        elif 'center' in kwargs:
            if 'angle' in kwargs:
                self._initFromCenterAndAngle(**kwargs)
            elif 'end' in kwargs:
                self._initFromCenterAndEnd(**kwargs)
            else:
                raise KeyError('Arcs defined with center point must define either an angle or endpoint')
        else:
            self._initFrom3PointArc(
                Vector2D(kwargs["start"]),
                Vector2D(kwargs["midpoint"]),
                Vector2D(kwargs["end"]),
            )

    @staticmethod
    def normalizeAngle(angle):
        a = angle % (2*360)
        if a > 360:
            a -= 2*360
        return a

    def _initAngle(self, angle):
        self.angle = geometricArc.normalizeAngle(angle)

    def _initFromCenterAndAngle(self, **kwargs):
        self.center_pos = Vector2D(kwargs['center'])
        self._initAngle(kwargs['angle'])

        if 'start' in kwargs:
            self.start_pos = Vector2D(kwargs['start'])
        elif 'midpoint' in kwargs:
            mp_r, mp_a = Vector2D(kwargs['midpoint']).to_polar(
                origin=self.center_pos, use_degrees=True)

            self.start_pos = Vector2D.from_polar(
                radius=mp_r, angle=mp_a-self.angle/2,
                origin=self.center_pos, use_degrees=True)
        else:
            raise KeyError('Arcs defined with center and angle must either define the start or midpoint.')

    def _initFromCenterAndEnd(self, **kwargs):

        if not all(arg in kwargs for arg in ['center', 'start', 'end']):
            raise KeyError('Arcs defined by center, start, and end points must define all three')

        self.center_pos = Vector2D(kwargs['center'])
        self.start_pos = Vector2D(kwargs['start'])
        sp_r, sp_a = self.start_pos.to_polar(
            origin=self.center_pos, use_degrees=True)
        ep_r, ep_a = Vector2D(kwargs['end']).to_polar(
            origin=self.center_pos, use_degrees=True)

        if abs(sp_r - ep_r) > 1e-7:
            raise ValueError(
                """Start and end point are not an same arc.
                Extended line from center to end point used to determine angle."""
            )
        self._initAngle(ep_a - sp_a)

        if kwargs.get('long_way', False):
            if abs(self.angle) < 180:
                self.angle = -math.copysign((360-abs(self.angle)), self.angle)
            if self.angle == -180:
                self.angle = 180
        else:
            if abs(self.angle) > 180:
                self.angle = -math.copysign((abs(self.angle) - 360), self.angle)
            if self.angle == 180:
                self.angle = -180

    def _initFrom3PointArc(self, start: Vector2D, midpoint: Vector2D, end: Vector2D):
        p1 = start
        p2 = midpoint
        p3 = end
        tol = 1e-7

        # prevent divide by zero
        if abs(p2.x - p1.x) < tol:
            # rotate points
            p1, p2, p3 = p2, p3, p1

        elif abs(p3.x - p2.x) < tol:
            # rotate point other direction
            p1, p2, p3 = p3, p1, p2

        # all Points are collinear in x
        if abs(p2.x - p1.x) < tol or abs(p3.x - p2.x) < tol:
            raise ValueError("This is not an arc")

        ma = (p2.y - p1.y) / (p2.x - p1.x)
        mb = (p3.y - p2.y) / (p3.x - p2.x)

        if abs(mb - ma) < 1e-7:
            raise ValueError("This is not an arc")

        center_x = ((ma*mb*(p1[1] - p3[1]) + mb*(p1[0] + p2[0]) - ma * (p2[0] + p3[0])) / (2*(mb - ma)))

        # prevent divide by zero
        if abs(ma) < tol:
            center_y = ((-1 / mb) * (center_x - (p2[0] + p3[0]) / 2) + (p2[1] + p3[1]) / 2)
        else:
            center_y = ((-1 / ma) * (center_x - (p1[0] + p2[0]) / 2) + (p1[1] + p2[1]) / 2)

        center = Vector2D(center_x, center_y)

        # Compute radius
        radius = (p1 - center).norm()

        # Compute start and end angles
        def _angle_from_center(pt):
            return math.atan2(pt.y - center.y, pt.x - center.x)

        start_angle = _angle_from_center(p1)
        end_angle = _angle_from_center(p3)

        def _midpoint_is_cw_from(center: Vector2D, start: Vector2D, mid: Vector2D):
            v1 = start - center
            v2 = mid - center
            cross = v1.x * v2.y - v1.y * v2.x
            return cross < 0

        # Determine if the arc is clockwise
        cw = _midpoint_is_cw_from(center, p1, p2)

        # Compute sweep angle
        if cw:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi

        sweep_angle = end_angle - start_angle

        # Store arc properties
        self.center_pos = center
        self.start_pos = p1
        self.radius = radius
        self._initAngle(math.degrees(sweep_angle))

    def rotate(self, angle, origin=(0, 0), use_degrees=True):
        r""" Rotate around given origin

        :params:
            * *angle* (``float``)
                rotation angle
            * *origin* (``Vector2D``)
                origin point for the rotation. default: (0, 0)
            * *use_degrees* (``boolean``)
                rotation angle is given in degrees. default:True
        """

        self.center_pos.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        self.start_pos.rotate(angle=angle, origin=origin, use_degrees=use_degrees)
        return self

    def translate(self, distance_vector):
        r""" Translate

        :params:
            * *distance_vector* (``Vector2D``)
                2D vector defining by how much and in what direction to translate.
        """

        self.center_pos += distance_vector
        self.start_pos += distance_vector
        return self

    def getRadius(self) -> float:
        r, _ = (self.start_pos - self.center_pos).to_polar()
        return r

    def getStartPoint(self) -> Vector2D:
        return Vector2D(self.start_pos)

    def getMidPoint(self) -> Vector2D:
        return Vector2D(self.start_pos).rotate(self.angle/2, origin=self.center_pos)

    def getEndPoint(self) -> Vector2D:
        return Vector2D(self.start_pos).rotate(self.angle, origin=self.center_pos)

    def getCenter(self) -> Vector2D:
        return self.center_pos

    def setRadius(self, radius: float):
        _, ang_s = self.start_pos.to_polar(origin=self.center_pos)
        self.start_pos = Vector2D.from_polar(radius=radius, angle=ang_s, origin=self.center_pos)
        return self

    def isPointInsideSelf(self, point: Vector2D, tolerance: float = 1e-7):
        raise NotImplementedError("isPointInsideSelf is not yet implemented for class geometricArc")

    def _calulateEndPos(self):
        radius, angle = self.start_pos.to_polar(
            origin=self.center_pos, use_degrees=True)

        return Vector2D.from_polar(
            radius=radius, angle=angle+self.angle,
            origin=self.center_pos, use_degrees=True)

    def _toLocalCoordinates(self, point):
        rad_s, ang_s = self.start_pos.to_polar(origin=self.center_pos)
        rad_p, ang_p = Vector2D(point).to_polar(origin=self.center_pos)

        ang_p_s = (ang_p - ang_s) % 360
        if self.angle < 0:
            ang_p_s -= 360
        return (rad_p, ang_p_s)

    def _compareAngles(self, a1, a2, tolerance=1e-7):
        r""" compare which of the two angles given in the local coordinate system

        :params:
            * *a1* (``float``)
                angle 1
            * *a2* (``float``)
                angle 2
            * *tolerance* (``float``)
                tolerance used to determine if the point is on the element
                default: 1e-7

        :return:
            * -1: angle 1 is closer to start
            *  0: both are of equal distance
            *  1: angle 2 is closer to start
        """

        if abs(a1-a2) < tolerance:
            return 0

        if self.angle < 0:
            if a1 < a2:
                return 1
        else:
            if a1 > a2:
                return 1
        return -1

    def isPointOnSelf(self, point, tolerance=1e-7):
        r""" is the given point on this arc

        :params:
            * *point* (``Vector2D``)
                The point to be checked
            * *tolerance* (``float``)
                tolerance used to determine if the point is on the element
                default: 1e-7
        """

        rad_p, ang_p_s = self._toLocalCoordinates(point)
        rad_s = (self.start_pos - self.center_pos).norm()

        # rotate to local coordinate system (start point is at 0 degree)
        ang_e_s = self.angle

        return self._compareAngles(ang_p_s, ang_e_s) in [0, -1] and abs(rad_s - rad_p) < tolerance

    def sortPointsRelativeToStart(self, points):
        r""" sort given points relative to start point on the arc

        :params:
            * *points* (``[Vector2D]``)
                itterable of points
        """
        local_points = []
        for p in points:
            r, phi = self._toLocalCoordinates(p)
            local_points.append((phi, (r, phi)))

        ps = []
        for _, p in sorted(local_points, reverse=(self.angle < 0)):
            ps.append(p)

        return ps

    def cut(self, *other):
        r""" cut line with given other element

        :params:
            * *other* (``Line``, ``Circle``, ``Arc``)
                cut the element on any intersection with the given geometric element
        """

        # calculate all intersection points of the underlying shapes
        ip = BaseNodeIntersection.intersectTwoNodes(self, *other)

        # only keep points lying on the contours themselves
        cp = []
        for p in ip:
            # if other is a rectangle we could end up in intersection points with
            # the lines formed by the edges of the rectangle, but which are outside
            if self.isPointOnSelf(p) and any(o.isPointOnSelf(p) for o in other):
                cp.append(p)

        sp = self.sortPointsRelativeToStart(cp)
        sp.insert(0, (self.getRadius(), 0))
        sp.append((self.getRadius(), self.angle))

        r = []
        for i in range(len(sp)-1):
            r.append(geometricArc(
                center=self.center_pos,
                start=Vector2D(self.start_pos).rotate(sp[i][1], origin=self.center_pos),
                angle=sp[i+1][1]-sp[i][1]
                ))

        return r

    def __iter__(self):
        yield self.center_pos
        yield self.start_pos

    def __len__(self):
        return 2

    def __getitem__(self, key):
        if key == 0 or key == 'center':
            return self.center_pos
        if key == 1 or key == 'start':
            return self.start_pos

        raise IndexError('Index {} is out of range'.format(key))

    def __setitem__(self, key, item):
        if key == 0 or key == 'center':
            self.center_pos = item
        if key == 1 or key == 'start':
            return self.start_pos
        else:
            raise IndexError('Index {} is out of range'.format(key))

    def __str__(self) -> str:
        return f"geometricArc(c={self.center_pos}, s={self.start_pos}, a={self.angle})"

    def __repr__(self) -> str:
        return self.__str__()


class BaseNodeIntersection():
    @staticmethod
    def intersectTwoNodes(*nodes):
        from KicadModTree.nodes import Line
        if len(nodes) < 2 or len(nodes) > 3:
            raise KeyError("intersectTwoNodes expects two node objects or a node and two vectors")

        # if the node is not a geometric primitive, intersect all geometric primitives instead
        if not isGeometricPrimitive(nodes[0]) and not isinstance(nodes[0], Vector2D):
            ip = []
            for n in nodes[0]:
                ip += BaseNodeIntersection.intersectTwoNodes(n, *nodes[1:])
            return ip
        elif len(nodes) == 2 and not isGeometricPrimitive(nodes[1]):
            ip = []
            for n in nodes[1]:
                ip += BaseNodeIntersection.intersectTwoNodes(nodes[0], n)
            return ip

        circles = []
        lines = []
        vectors = []

        for n in nodes:
            if hasattr(n, 'getRadius') and hasattr(n, 'center_pos'):
                circles.append(n)
            elif hasattr(n, 'end_pos') and hasattr(n, 'start_pos'):
                lines.append(n)
            else:
                vectors.append(n)

        if len(vectors) == 2:
            lines.append(Line(start=vectors[0], end=vectors[1]))

        if len(lines) == 2:
            return BaseNodeIntersection.intersectTwoLines(*lines)

        if len(circles) == 2:
            return BaseNodeIntersection.intersectTwoCircles(*circles)

        if len(lines) == 1 and len(circles) == 1:
            return BaseNodeIntersection.intersectLineWithCircle(lines[0], circles[0])

        print(lines)
        print(circles)
        raise NotImplementedError('unsupported combination of parameter types')

    @staticmethod
    def intersectTwoLines(line1, line2):
        """
        Intersect two (infinitely long) lines
        """
        # we use homogeneous coordinates here.
        l1 = line1.to_homogeneous()
        l2 = line2.to_homogeneous()

        ip = l1.cross_product(l2)
        if ip.z == 0:
            return []

        return [Vector2D.from_homogeneous(ip)]

    @staticmethod
    def intersectTwoSegments(line1: geometricLine, line2: geometricLine) -> List[Vector2D]:

        p = BaseNodeIntersection.intersectTwoLines(line1, line2)
        if not p:
            return []

        if line1.isPointOnSelf(p[0]) and line2.isPointOnSelf(p[0]):
            return [p[0]]

        # The lines are not parallel, but the intersection point is not on either line
        return []

    @staticmethod
    def intersectLineWithCircle(line, circle, tol: float = 1e-7):
        # from http://mathworld.wolfram.com/Circle-LineIntersection.html
        # Equations are for circle center on (0, 0) so we translate everything
        # to the origin (well the line anyways as we do only need the radius of the circle)
        lt = line.copy().translate(-circle.center_pos)

        d = lt.end_pos - lt.start_pos
        dr = d.norm()
        if (dr < tol):     # line has length zero
            if (circle.isPointOnSelf(lt.start_pos)):
                return [lt.start_pos]
            else:
                return []
        D = lt.start_pos.x*lt.end_pos.y - lt.end_pos.x*lt.start_pos.y

        discriminant = circle.getRadius()**2 * dr**2 - D**2
        intersection: list[Vector2D] = []
        if discriminant < 0:
            return intersection

        def calcPoint(x):
            return Vector2D({
                'x': (D*d.y + x*math.copysign(1, d.y)*d.x*math.sqrt(discriminant))/dr**2,
                'y': (-D*d.x + x*abs(d.y)*math.sqrt(discriminant))/dr**2
                }) + circle.center_pos

        intersection.append(calcPoint(1))
        if discriminant == 0:
            return intersection

        intersection.append(calcPoint(-1))
        return intersection

    @staticmethod
    def intersectSegmentWithCircle(
        line: geometricLine, circle: geometricCircle,
        reject_tangents: bool = False,
        tol: float = 1e-7
    ) -> List[Vector2D]:

        line_intersections = BaseNodeIntersection.intersectLineWithCircle(line, circle, tol)

        if reject_tangents and len(line_intersections) == 1:
            return []

        ret = []

        # Discard points that are not on the line segment itself
        for p in line_intersections:
            if line.isPointOnSelf(p):
                ret.append(p)

        return ret

    @staticmethod
    def intersectTwoCircles(circle1: geometricCircle, circle2: geometricCircle, tol: float = 1e-7):
        # from https://mathworld.wolfram.com/Circle-CircleIntersection.html
        # Equations are for circle1 center on (0, 0) and circle2 center on (d, 0)
        # so we translate the results back accordingle
        R, r = circle1.getRadius(), circle2.getRadius()
        d, phi = (circle2.center_pos - circle1.center_pos).to_polar()

        # Circles are too far away to touch
        if (R + r < d):
            return []

        # One circle is inside the other
        if d < abs(R - r):
            return []

        if (abs(d) < tol):
            # circles have the same center
            if (abs(r) < tol and abs(R) < tol):
                # circles have both radius zero --> return common center
                x = y = 0
            else:
                raise ValueError("the two circles you are trying to intersect are identical")
        else:
            x = (d**2 - r**2 + R**2) / (2 * d)

            # The circles are tangent - the point lies R from the center of circle1
            # This defends against sqrt(negative), as well as returning two almost identical
            # points when the circles are tangent.
            if abs(abs(x) - R) < tol:
                y = 0
            else:
                numerator = 4 * d**2 * R**2 - (d**2 - r**2 + R**2)**2
                y = math.sqrt(numerator) / d

        signs = [0.0] if (y < tol) else [0.5, -0.5]
        return [Vector2D(x, s * y).rotate(angle=phi) + circle1.center_pos for s in signs]

    @staticmethod
    def intersectSegmentWithArc(
        line: geometricLine,
        arc: geometricArc,
        include_arc_endpoints=False,
        tol: float = 1e-7,
    ) -> List[Vector2D]:

        arc_circle = geometricCircle(center=arc.center_pos, radius=arc.getRadius())
        line_intersections = BaseNodeIntersection.intersectSegmentWithCircle(line, arc_circle, tol)

        ret = []

        # Discard points that are not on the arc itself
        for p in line_intersections:

            if not include_arc_endpoints:
                if (p - arc.start_pos).is_nullvec() or (p - arc.getEndPoint()).is_nullvec():
                    continue

            if arc.isPointOnSelf(p):
                ret.append(p)

        return ret

    @staticmethod
    def intersectCircleWithArc(
        circle: geometricCircle, arc: geometricArc,
        reject_tangents: bool = False,
        tol: float = 1e-7
    ) -> List[Vector2D]:

        arc_circle = geometricCircle(center=arc.center_pos, radius=arc.getRadius())
        circle_intersections = BaseNodeIntersection.intersectTwoCircles(circle, arc_circle, tol)

        if reject_tangents and len(circle_intersections) == 1:
            return []

        ret = []

        # Discard points that are not on the arc itself
        for p in circle_intersections:
            if arc.isPointOnSelf(p):
                ret.append(p)

        return ret
