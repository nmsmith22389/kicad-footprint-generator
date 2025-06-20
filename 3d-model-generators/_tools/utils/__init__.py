#!/usr/bin/env python3

# CadQuery Helper Functions
#
# Copyright (C) 2025 Martin Sotirov <martin@libtec.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math


class V2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, i):
        return [self.x, self.y][i]

    def __add__(self, o):
        if type(o) is V2:
            return V2(self.x + o.x, self.y + o.y)
        else:
            return V2(self.x + o, self.y + o)

    def __sub__(self, o):
        if type(o) is V2:
            return V2(self.x - o.x, self.y - o.y)
        else:
            return V2(self.x - o, self.y - o)

    def __mul__(self, o):
        if type(o) is V2:
            return V2(self.x * o.x, self.y * o.y)
        else:
            return V2(self.x * o, self.y * o)

    def dist(self, o):
        return math.sqrt((self.x - o.x) ** 2 + (self.y - o.y) ** 2)

    def normalized(self):
        d = self.dist(V2(0, 0))
        return V2(self.x / d, self.y / d)


class Line:
    def __init__(self, m, b):
        self.m = m  # slope
        self.b = b  # intercept

    def get_line_intersection(self, l):
        x = (l.b - self.b) / (self.m - l.m)

        if abs(self.m) < 10000:
            y = self.m * x + self.b
        else:
            y = l.m * x + l.b

        return V2(x, y)


def get_side_to_tip_corner(side, tip, pt, ccw):
    w = side.x - tip.x
    h = side.y - tip.y
    a = math.atan2(h, w)

    tri_c = math.sqrt(w * w + h * h)
    tri_a = pt / 2
    tri_b = math.sqrt(tri_c**2 - tri_a**2)

    tri_B = math.asin(tri_b / tri_c)

    if ccw:
        tip_a = a + tri_B
    else:
        tip_a = a - tri_B

    corner = tip + V2(math.cos(tip_a), math.sin(tip_a)) * (pt / 2)

    return corner


def get_back_side(p0, p1, p2, th):
    # Get angles
    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)
    if a0 < 0:
        a0 += math.pi * 2
    if a1 < 0:
        a1 += math.pi * 2

    # Get slopes
    m0 = math.tan(a0)
    m1 = math.tan(a1)

    # Get perpendicular angles
    ap0 = a0 + math.pi / 2
    ap1 = a1 - math.pi / 2

    # Get back points
    p0_b = p1 + V2(math.cos(ap0), math.sin(ap0)) * th
    p1_b = p1 + V2(math.cos(ap1), math.sin(ap1)) * th

    # Get back lines
    l0 = Line(m0, p0_b.y - p0_b.x * m0)
    l1 = Line(m1, p1_b.y - p1_b.x * m1)

    # Get back corner
    c = l0.get_line_intersection(l1)

    return c


def make_rounded_corner(body, p0, p1, p2, r, pt):
    # Get angles
    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)
    if a0 < 0:
        a0 += math.pi * 2
    if a1 < 0:
        a1 += math.pi * 2

    # Get slopes
    m0 = math.tan(a0)
    m1 = math.tan(a1)

    # Get distance between angles
    d = a1 - a0
    # assert(d > 0)
    if d < 0:
        d += math.pi * 2

    # Check if it's inner corner
    if d >= math.pi:
        r -= pt

    if r <= 0:
        body = body.lineTo(p1.x, p1.y)
        return body

    # Get perpendicular angles
    if d < math.pi:
        ap0 = a0 + math.pi / 2
        ap1 = a1 - math.pi / 2
        rev = False
    else:
        ap0 = a0 - math.pi / 2
        ap1 = a1 + math.pi / 2
        rev = True

    p0_b = p1 + V2(math.cos(ap0), math.sin(ap0)) * r
    p1_b = p1 + V2(math.cos(ap1), math.sin(ap1)) * r
    l0 = Line(m0, p0_b.y - p0_b.x * m0)
    l1 = Line(m1, p1_b.y - p1_b.x * m1)

    c = l0.get_line_intersection(l1)
    s = c + V2(-math.cos(ap0), -math.sin(ap0)) * r
    e = c + V2(-math.cos(ap1), -math.sin(ap1)) * r

    if rev:
        r = -r
    if p0.dist(s) > 0.00001:
        body = body.lineTo(s.x, s.y)
    body = body.radiusArc((e.x, e.y), r)

    return body


def _make_z_operation(body, vals, func_name):
    if not vals:
        return body

    if type(vals) is not list:
        vals = [vals] * 4

    if len(vals) != 4:
        raise ValueError(f"z {func_name} operation must have exactly 4 numbers")

    if vals[0]:
        body = getattr(body.edges("|Z and >X and >Y"), func_name)(vals[0])
    if vals[1]:
        body = getattr(body.edges("|Z and <X and >Y"), func_name)(vals[1])
    if vals[2]:
        body = getattr(body.edges("|Z and <X and <Y"), func_name)(vals[2])
    if vals[3]:
        body = getattr(body.edges("|Z and >X and <Y"), func_name)(vals[3])

    return body


def make_z_chamfer(body, vals):
    return _make_z_operation(body, vals, "chamfer")


def make_z_fillet(body, vals):
    return _make_z_operation(body, vals, "fillet")
