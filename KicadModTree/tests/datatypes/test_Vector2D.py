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
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

import unittest
import math
from KicadModTree.Vector import *


class Vector2DTests(unittest.TestCase):

    def test_init(self):
        p1 = Vector2D([1, 2])
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)

        p2 = Vector2D((4, 5))
        self.assertEqual(p2.x, 4)
        self.assertEqual(p2.y, 5)

        p3 = Vector2D({'x': 7, 'y': 8})
        self.assertEqual(p3.x, 7)
        self.assertEqual(p3.y, 8)

        p3_empty = Vector2D({})
        self.assertEqual(p3_empty.x, 0)
        self.assertEqual(p3_empty.y, 0)

        p4 = Vector2D(p1)
        self.assertEqual(p4.x, 1)
        self.assertEqual(p4.y, 2)

        p5 = Vector2D(1, 2)
        self.assertEqual(p5.x, 1)
        self.assertEqual(p5.y, 2)

        # TODO: test float datatype
        # TODO: invalid type tests
        # TODO: tests if int is always converted to float

    def test_round_to(self):
        p1 = Vector2D([1.234, 5.678]).round_to(0)
        self.assertAlmostEqual(p1.x, 1.234)
        self.assertAlmostEqual(p1.y, 5.678)

        p2 = Vector2D([1.234, 5.678]).round_to(0.1)
        self.assertAlmostEqual(p2.x, 1.2)
        self.assertAlmostEqual(p2.y, 5.7)

        p3 = Vector2D([1.234, 5.678]).round_to(0.01)
        self.assertAlmostEqual(p3.x, 1.23)
        self.assertAlmostEqual(p3.y, 5.68)

        p4 = Vector2D([1.234, 5.678]).round_to(0.001)
        self.assertAlmostEqual(p4.x, 1.234)
        self.assertAlmostEqual(p4.y, 5.678)

        p5 = Vector2D([1.234, 5.678]).round_to(0.0001)
        self.assertAlmostEqual(p5.x, 1.234)
        self.assertAlmostEqual(p5.y, 5.678)

    def test_add(self):
        p1 = Vector2D([1, 2])
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)

        p2 = p1 + 5
        self.assertEqual(p2.x, 6)
        self.assertEqual(p2.y, 7)

        p3 = p1 + (-5)
        self.assertEqual(p3.x, -4)
        self.assertEqual(p3.y, -3)

        p4 = p1 + [4, 2]
        self.assertEqual(p4.x, 5)
        self.assertEqual(p4.y, 4)

        p5 = p1 + [-5, -3]
        self.assertEqual(p5.x, -4)
        self.assertEqual(p5.y, -1)

        # TODO: invalid type tests

    def test_sub(self):
        p1 = Vector2D([1, 2])
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)

        p2 = p1 - 5
        self.assertEqual(p2.x, -4)
        self.assertEqual(p2.y, -3)

        p3 = p1 - (-5)
        self.assertEqual(p3.x, 6)
        self.assertEqual(p3.y, 7)

        p4 = p1 - [4, 2]
        self.assertEqual(p4.x, -3)
        self.assertEqual(p4.y, 0)

        p5 = p1 - [-5, -3]
        self.assertEqual(p5.x, 6)
        self.assertEqual(p5.y, 5)

        # TODO: invalid type tests

    def test_mul(self):
        p1 = Vector2D([1, 2])
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)

        p2 = p1 * 5
        self.assertEqual(p2.x, 5)
        self.assertEqual(p2.y, 10)

        p3 = p1 * (-5)
        self.assertEqual(p3.x, -5)
        self.assertEqual(p3.y, -10)

        p4 = p1 * [4, 5]
        self.assertEqual(p4.x, 4)
        self.assertEqual(p4.y, 10)

        p5 = p1 * [-5, -3]
        self.assertEqual(p5.x, -5)
        self.assertEqual(p5.y, -6)

        # TODO: invalid type tests

    def test_div(self):
        p1 = Vector2D([1, 2])
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)

        p2 = p1 / 5
        self.assertEqual(p2.x, 0.2)
        self.assertEqual(p2.y, 0.4)

        p3 = p1 / (-5)
        self.assertEqual(p3.x, -0.2)
        self.assertEqual(p3.y, -0.4)

        p4 = p1 / [4, 5]
        self.assertEqual(p4.x, 0.25)
        self.assertEqual(p4.y, 0.4)

        p5 = p1 / [-5, -2]
        self.assertEqual(p5.x, -0.2)
        self.assertEqual(p5.y, -1)

        # TODO: division by zero tests
        # TODO: invalid type tests

    def test_polar(self):
        p1 = Vector2D.from_polar(math.sqrt(2), 45, use_degrees=True)
        self.assertAlmostEqual(p1.x, 1)
        self.assertAlmostEqual(p1.y, 1)

        p1 = Vector2D.from_polar(2, -90, use_degrees=True, origin=(6, 1))
        self.assertAlmostEqual(p1.x, 6)
        self.assertAlmostEqual(p1.y, -1)

        r, a = p1.to_polar(use_degrees=True, origin=(6, 1))
        self.assertAlmostEqual(r, 2)
        self.assertAlmostEqual(a, -90)

        p1.rotate(90, use_degrees=True, origin=(6, 1))
        self.assertAlmostEqual(p1.x, 8)
        self.assertAlmostEqual(p1.y, 1)

        p1 = Vector2D.from_polar(math.sqrt(2), 135, use_degrees=True)
        self.assertAlmostEqual(p1.x, -1)
        self.assertAlmostEqual(p1.y, 1)

        p1.rotate(90, use_degrees=True)
        self.assertAlmostEqual(p1.x, -1)
        self.assertAlmostEqual(p1.y, -1)

        r, a = p1.to_polar(use_degrees=True)
        self.assertAlmostEqual(r, math.sqrt(2))
        self.assertAlmostEqual(a, -135)

    def test_right_mul(self):
        p = 3 * Vector2D(1, 2)
        self.assertAlmostEqual(p.x, 3)
        self.assertAlmostEqual(p.y, 6)

    def test_norm_arg(self):
        self.assertAlmostEqual(Vector2D(1, 1).norm(), sqrt(2))
        self.assertAlmostEqual(Vector2D(1, 1).arg(), 45)
        self.assertAlmostEqual(Vector2D(1, 1).arg(use_degrees=False), math.pi/4)
        self.assertAlmostEqual(Vector2D(-1, -1).arg(), -135)
        self.assertAlmostEqual(Vector2D(-1, -1).arg(use_degrees=False), -3*math.pi/4)

    def test_inner(self):
        v1 = Vector2D(2, 3)
        v2 = Vector2D(4, 5)

        self.assertEqual(v1.inner(v2), 23)
        self.assertEqual(v2.inner(v1), 23)

        v2 = v1.orthogonal()
        self.assertEqual(v1.inner(v2), 0)
        self.assertEqual(v1.inner(-v2), 0)

    def test_normalize(self):
        v = Vector2D(0, 0)
        n = Vector2D.normalize(v)
        self.assertEqual(n.norm(), 0)

        v = Vector2D(sin(math.pi/6), cos(math.pi/6))
        n = Vector2D.normalize(v)
        self.assertEqual(n.norm(), 1)

        n1 = Vector2D(1, 2).normalize()
        n2 = Vector2D(0.1, 0.2).normalize()
        self.assertEqual(n1.norm(), 1)
        self.assertEqual(n2.norm(), 1)
        self.assertAlmostEqual((n1 - n2).norm(), 0)

    def test_min_max(self):
        v1 = Vector2D(3, 2)
        v2 = Vector2D(1, 4)

        v = v1.max(v2)
        self.assertEqual(v.x, 3)
        self.assertEqual(v.y, 4)
        v = v2.max(v1)
        self.assertEqual(v.x, 3)
        self.assertEqual(v.y, 4)

        v = v1.min(v2)
        self.assertEqual(v.x, 1)
        self.assertEqual(v.y, 2)
        v = v2.min(v1)
        self.assertEqual(v.x, 1)
        self.assertEqual(v.y, 2)

        # check for iterables
        v = Vector2D.min((3, 2), (1, 4))
        self.assertEqual(v.x, 1)
        self.assertEqual(v.y, 2)
