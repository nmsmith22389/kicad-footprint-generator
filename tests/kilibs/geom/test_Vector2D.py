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

import pytest
import math
from kilibs.geom import Vector2D
from kilibs.test_utils.geom_test import vector_approx_equal


def test_init():
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = Vector2D((4, 5))
    assert p2.x == 4
    assert p2.y == 5

    p3 = Vector2D({'x': 7, 'y': 8})
    assert p3.x == 7
    assert p3.y == 8

    p3_empty = Vector2D({})
    assert p3_empty.x == 0
    assert p3_empty.y == 0

    p4 = Vector2D(p1)
    assert p4.x == 1
    assert p4.y == 2

    p5 = Vector2D(1, 2)
    assert p5.x == 1
    assert p5.y == 2

    # TODO: test float datatype
    # TODO: invalid type tests
    # TODO: tests if int is always converted to float

def test_round_to():
    p1 = Vector2D([1.234, 5.678]).round_to(0)
    print(p1)
    assert vector_approx_equal(p1, (1.234, 5.678))

    p2 = Vector2D([1.234, 5.678]).round_to(0.1)
    assert vector_approx_equal(p2, (1.2, 5.7))

    p3 = Vector2D([1.234, 5.678]).round_to(0.01)
    assert vector_approx_equal(p3, (1.23, 5.68))

    p4 = Vector2D([1.234, 5.678]).round_to(0.001)
    assert vector_approx_equal(p4, (1.234, 5.678))

    p5 = Vector2D([1.234, 5.678]).round_to(0.0001)
    assert vector_approx_equal(p5, (1.234, 5.678))

def test_add():
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 + 5
    assert p2.x == 6
    assert p2.y == 7

    p3 = p1 + (-5)
    assert p3.x == -4
    assert p3.y == -3

    p4 = p1 + [4, 2]
    assert p4.x == 5
    assert p4.y == 4

    p5 = p1 + [-5, -3]
    assert p5.x == -4
    assert p5.y == -1

    # TODO: invalid type tests

def test_sub():
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 - 5
    assert p2.x == -4
    assert p2.y == -3

    p3 = p1 - (-5)
    assert p3.x == 6
    assert p3.y == 7

    p4 = p1 - [4, 2]
    assert p4.x == -3
    assert p4.y == 0

    p5 = p1 - [-5, -3]
    assert p5.x == 6
    assert p5.y == 5

    # TODO: invalid type tests

def test_mul():
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 * 5
    assert p2.x == 5
    assert p2.y == 10

    p3 = p1 * (-5)
    assert p3.x == -5
    assert p3.y == -10

    p4 = p1 * [4, 5]
    assert p4.x == 4
    assert p4.y == 10

    p5 = p1 * [-5, -3]
    assert p5.x == -5
    assert p5.y == -6

    # TODO: invalid type tests

def test_div():
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 / 5
    assert p2.x == 0.2
    assert p2.y == 0.4

    p3 = p1 / (-5)
    assert p3.x == -0.2
    assert p3.y == -0.4

    p4 = p1 / [4, 5]
    assert p4.x == 0.25
    assert p4.y == 0.4

    p5 = p1 / [-5, -2]
    assert p5.x == -0.2
    assert p5.y == -1

    # TODO: division by zero tests
    # TODO: invalid type tests

def test_polar():
    p1 = Vector2D.from_polar(math.sqrt(2), 45, use_degrees=True)
    assert vector_approx_equal(p1, (1, 1))

    p1 = Vector2D.from_polar(2, -90, use_degrees=True, origin=(6, 1))
    assert vector_approx_equal(p1, (6, -1))

    r, a = p1.to_polar(use_degrees=True, origin=(6, 1))
    assert r == pytest.approx(2)
    assert a == pytest.approx(-90)

    p1.rotate(90, use_degrees=True, origin=(6, 1))
    assert vector_approx_equal(p1, (8, 1))

    p1 = Vector2D.from_polar(math.sqrt(2), 135, use_degrees=True)
    assert vector_approx_equal(p1, (-1, 1))

    p1.rotate(90, use_degrees=True)
    assert vector_approx_equal(p1, (-1, -1))

    r, a = p1.to_polar(use_degrees=True)
    assert r == pytest.approx(math.sqrt(2))
    assert a == pytest.approx(-135)

def test_right_mul():
    p = 3 * Vector2D(1, 2)
    assert vector_approx_equal(p, (3, 6))

def test_norm_arg():
    assert Vector2D(1, 1).norm() == pytest.approx(math.sqrt(2))
    assert Vector2D(1, 1).arg() == pytest.approx(45)
    assert Vector2D(1, 1).arg(use_degrees=False) == pytest.approx(math.pi/4)
    assert Vector2D(-1, -1).arg() == pytest.approx(-135)
    assert Vector2D(-1, -1).arg(use_degrees=False) == pytest.approx(-3*math.pi/4)

def test_inner():
    v1 = Vector2D(2, 3)
    v2 = Vector2D(4, 5)

    assert v1.dot_product(v2) == 23
    assert v2.dot_product(v1) == 23

    v2 = v1.orthogonal()
    assert v1.dot_product(v2) == 0
    assert v1.dot_product(-v2) == 0

def test_normalize():
    v = Vector2D(0, 0)
    n = Vector2D.normalize(v)
    assert n.norm() == 0

    v = Vector2D(math.sin(math.pi/6), math.cos(math.pi/6))
    n = Vector2D.normalize(v)
    assert n.norm() == 1

    n1 = Vector2D(1, 2).normalize()
    n2 = Vector2D(0.1, 0.2).normalize()
    assert n1.norm() == 1
    assert n2.norm() == 1
    assert (n1 - n2).norm() == pytest.approx(0)

def test_min_max():
    v1 = Vector2D(3, 2)
    v2 = Vector2D(1, 4)

    v = v1.max(v2)
    assert v.x == 3
    assert v.y == 4
    v = v2.max(v1)
    assert v.x == 3
    assert v.y == 4

    v = v1.min(v2)
    assert v.x == 1
    assert v.y == 2
    v = v2.min(v1)
    assert v.x == 1
    assert v.y == 2

    # check for iterables
    v = Vector2D.min((3, 2), (1, 4))
    assert v.x == 1
    assert v.y == 2


SQRT2 = math.sqrt(2)


@pytest.mark.parametrize(
    "v1, v2, exp",
    [
        ((0, 0), (0, 1), 1),
        ((0, 0), (1, 0), 1),
        ((0, 0), (1, 1), SQRT2),
    ],
)
def test_distance(v1, v2, exp):
    v1 = Vector2D(v1)
    v2 = Vector2D(v2)
    assert v1.distance_to(v2) == pytest.approx(exp)
    assert v2.distance_to(v1) == pytest.approx(exp)


@pytest.mark.parametrize(
    "v1, v2, exp",
    [
        ((0, 0),           (0, 0), True),
        ((0, 0.000000001), (0, 0), True),
    ],
)  # fmt: skip
def test_is_close(v1, v2, exp):
    v1 = Vector2D(v1)
    v2 = Vector2D(v2)

    assert v1.is_close(v2) == exp
    assert v2.is_close(v1) == exp
