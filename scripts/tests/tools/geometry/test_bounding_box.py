from scripts.tools.geometry.bounding_box import BoundingBox
from KicadModTree import Vector2D

import pytest


def test_failures():

    bb = BoundingBox()

    with pytest.raises(RuntimeError):
        bb.top

    # Must have both points or neither
    with pytest.raises(ValueError):
        BoundingBox(Vector2D(10, 20))

    with pytest.raises(ValueError):
        BoundingBox(min_pt=Vector2D(10, 20))

    with pytest.raises(ValueError):
        BoundingBox(max_pt=Vector2D(10, 20))


def test_bbox_include_pts():

    bb = BoundingBox(
        min_pt=Vector2D(10, 20),
        max_pt=Vector2D(30, 40)
    )

    assert bb.top == 20
    assert bb.bottom == 40
    assert bb.left == 10
    assert bb.right == 30

    # including internal point should not change bbox
    bb.include_point(Vector2D(15, 25))

    assert bb.top == 20
    assert bb.bottom == 40
    assert bb.left == 10
    assert bb.right == 30

    # include point above and left
    bb.include_point(Vector2D(5, 15))

    assert bb.top == 15
    assert bb.bottom == 40
    assert bb.left == 5
    assert bb.right == 30

    # to left only
    bb.include_point(Vector2D(0, 20))

    assert bb.top == 15
    assert bb.bottom == 40
    assert bb.left == 0
    assert bb.right == 30

    # to right only
    bb.include_point(Vector2D(35, 20))

    assert bb.top == 15
    assert bb.bottom == 40
    assert bb.left == 0
    assert bb.right == 35

    # to right and below
    bb.include_point(Vector2D(45, 45))

    assert bb.top == 15
    assert bb.bottom == 45
    assert bb.left == 0
    assert bb.right == 45


def test_bbox_include_bbox():

    bb = BoundingBox(
        min_pt=Vector2D(10, 20),
        max_pt=Vector2D(30, 40)
    )

    bb2 = BoundingBox(
        min_pt=Vector2D(100, 100),
        max_pt=Vector2D(110, 110)
    )

    bb.include_bbox(bb2)

    assert bb.top == 20
    assert bb.bottom == 110
    assert bb.left == 10
    assert bb.right == 110