"""
Tests for the graphical keepout classes.

These are not intended to be exhaustive, but mostly for a demonstration of how to use the classes,
as well as a place to put some simple tests to catch fiddly edge cases if needed.

Exhaustive tests are high maintenance, and regressions will normally be much more obvious by the
visual diffs of the generated graphics than by delicate stacks of numerical tests.
"""

from kilibs.geom import geometricArc, geometricLine, geometricCircle
from kilibs.geom.keepout import KeepoutRect, KeepoutRound
from scripts.tools.drawing_tools import applyKeepouts

import kilibs.test_utils.geom_test as GeomTest

import pytest
from itertools import product


# Some numbers to use for adding to integers to make sure you try round and non-round
# values in floating point values (0.1 can't be expressed exactly in FP).
FLOATING_POINT_OFFSETS = [0.0, 0.1, -0.1]


@pytest.mark.parametrize("center, size, line_start, line_end, expected_segs", [

    # Centred square, line from origin
    ((0, 0), (100, 100), (0, 0), (10, 10), []),  # Fully inside
    ((0, 0), (100, 100), (0, 0), (50, 50), []),  # Touching line
    ((0, 0), (100, 100), (0, 0), (50, 50), []),  # Touching corner

    # Centred square, line from origin to outside
    ((0, 0), (100, 100), (0, 0), (100, 0), [((50, 0), (100, 0))]),
])
def test_keepout_rect_vs_line(center, size, line_start, line_end, expected_segs):
    """
    Simple test for keepout rectangle vs line
    """
    ko = KeepoutRect(center=center, size=size)
    line = geometricLine(start=line_start, end=line_end)
    new_items = ko.keepout_line(line)

    assert len(new_items) == len(expected_segs)

    for i, seg in enumerate(expected_segs):

        gseg = geometricLine(start=seg[0], end=seg[1])

        assert GeomTest.seg_same_endpoints(new_items[i], gseg)


@pytest.mark.parametrize(
    "fp_fudge_x",
    FLOATING_POINT_OFFSETS,
)
def test_keepout_rect_coincident_line(fp_fudge_x):
    """
    Simple test for keepout rectangle vs line that lies on the keepout.

    These lines should NOT be trimmed, as they're common when computing
    offsets exactly on the keepout line.
    """
    ko = KeepoutRect(center=(0 + fp_fudge_x, 0), size=(100, 100))

    lines = [
        geometricLine(start=(-50 + fp_fudge_x, 50), end=(50 + fp_fudge_x, 50)),
        geometricLine(start=(-50 + fp_fudge_x, -50), end=(50 + fp_fudge_x, -50)),
        geometricLine(start=(50 + fp_fudge_x, -50), end=(50 + fp_fudge_x, 50)),
        geometricLine(start=(-50 + fp_fudge_x, -50), end=(-50 + fp_fudge_x, 50)),
    ]

    for line in lines:
        new_items = ko.keepout_line(line)

        assert new_items is None


def test_apply_keepout_1():

    # Four lines:
    # - Two cut by the keepout
    # - One fully inside - deleted
    # - One fully outside - retained
    #
    # Leaving 3 lines after keepout application

    items = [
        geometricLine(start=(0, 0), end=(100, 0)),
        geometricLine(start=(0, 0), end=(0, 100)),
        geometricLine(start=(10, 10), end=(20, 20)),  # Inside
        geometricLine(start=(60, 60), end=(70, 70)),  # Outside
    ]

    ko = KeepoutRect(center=(0, 0), size=(100, 100))

    new_items = applyKeepouts(items, [ko])
    assert len(new_items) == 3


def test_apply_circles_to_circle():

    # Two circular keeouts, at 0 and 180
    # Should split the circle into two arcs

    items = [
        geometricCircle(center=(0, 0), radius=1000),
    ]

    kos = [
        KeepoutRound(center=(-1000, 0), radius=100),
        KeepoutRound(center=(1000, 0), radius=100),
    ]

    new_items = applyKeepouts(items, kos)
    assert len(new_items) == 2


@pytest.mark.parametrize("fp_fudge_r, fp_fudge_x",
    product(FLOATING_POINT_OFFSETS, repeat=2),
)
def test_arc_tangent_to_circle(fp_fudge_r, fp_fudge_x):

    # If an arc just touches the circle, it's one intersection,
    # which can upset the odd/even splitting if not handled

    items = [
        geometricArc(
            start=(fp_fudge_x, 200 + fp_fudge_r),
            midpoint=(200 + fp_fudge_x + fp_fudge_r, 0),
            end=(fp_fudge_x, -200 - fp_fudge_r),
        ),
    ]

    kos = [
        KeepoutRound(
            center=(100 + fp_fudge_x, 0),
            radius=100 + fp_fudge_r,
        ),
    ]

    new_items = applyKeepouts(items, kos)

    assert len(new_items) == 1
    # The arc should be untouched
    assert new_items[0] == items[0]


@pytest.mark.parametrize("fp_fudge_r, fp_fudge_cx",
    product(FLOATING_POINT_OFFSETS, repeat=2),
)
def test_circle_tangent_to_circle(fp_fudge_r, fp_fudge_cx):

    # As for arc-circle, one circle just touching shouldn't clip.

    items = [
        geometricCircle(center=(fp_fudge_cx, 0), radius=200 + fp_fudge_r),
    ]

    kos = [
        KeepoutRound(center=(100 + fp_fudge_cx, 0), radius=100 + fp_fudge_r),
    ]

    new_items = applyKeepouts(items, kos)

    assert len(new_items) == 1
    # The arc should be untouched
    assert new_items[0] == items[0]


@pytest.mark.parametrize("fp_fudge_r, fp_fudge_cx",
    product(FLOATING_POINT_OFFSETS, repeat=2),
)
def test_circle_tangent_to_rect(fp_fudge_r, fp_fudge_cx):

    # If a circle just touches the rectangle, it's one intersection,
    # and we reject it as a clip point

    items = [
        geometricCircle(
            center=(200 + fp_fudge_cx, 0),
            radius=100 + fp_fudge_r,
        ),
    ]

    kos = [
        KeepoutRect(
            center=(0 + fp_fudge_cx, 0),
            size=(100 + fp_fudge_r, 100 + fp_fudge_r),
        ),
    ]

    new_items = applyKeepouts(items, kos)

    assert len(new_items) == 1
    # The arc should be untouched
    assert new_items[0] == items[0]


def test_arc_to_circle_ko_reverse_angle():

    # Test a 180 arc with positive and negative angle
    # (in PCB land: 6-oclock to 12-oclock, mdpoint at 3-oclock)
    #
    # Cut it with a keepout circle such that the intersections are +-60 degrees
    # from the horizontal. Check that we do get two 30-degree chunks in both directions
    #
    # This exposes problems with angle ordering if not properly handled.

    def check_results(new_items: list):
        assert len(new_items) == 2

        for item in new_items:
            assert isinstance(item, geometricArc)
            assert abs(item.angle) == pytest.approx(30)

    # Left side
    arc_l = geometricArc(start=(0, 100), end=(0, -100), midpoint=(-100, 0))

    ko_l = KeepoutRound(center=(-100, 0), radius=100)

    new_items = applyKeepouts([arc_l], [ko_l])
    check_results(new_items)

    # Right side (opposite angle)
    arc_r = geometricArc(start=(0, 100), end=(0, -100), midpoint=(100, 0))

    ko_r = KeepoutRound(center=(100, 0), radius=100)

    # check that the angles are indeed opposite, or this test is bogus
    assert arc_l.angle == pytest.approx(-arc_r.angle)

    new_items = applyKeepouts([arc_r], [ko_r])
    check_results(new_items)


@pytest.mark.parametrize(
    "fp_fudge_x",
    FLOATING_POINT_OFFSETS,
)
def test_arc_with_endpoint_on_ko_bound(fp_fudge_x):
    """
    Make sure we don't flub the case where the end/startpoint of the arc is also
    an intersection with the keepout.

    Add some fudge to the x coordinate to make sure we test with +/- FP roundoffs.
    """

    arc = geometricArc(
        start=(fp_fudge_x, 100),
        end=(fp_fudge_x, -100),
        midpoint=(100 + fp_fudge_x, 0),
    )
    ko_outside = KeepoutRect(
        center=(-100 + fp_fudge_x, 0),
        size=(200, 200),
    )

    # Check that the start point is indeed on the keepout edge
    assert ko_outside.right == pytest.approx(arc.getStartPoint().x)

    new_items = applyKeepouts([arc], [ko_outside])

    assert len(new_items) == 1
    assert abs(new_items[0].angle) == pytest.approx(180)

    # and the other case where the arc is inside and touches
    # the keepout rectangle at the start/end points
    ko_inside = KeepoutRect(
        center=(100 + fp_fudge_x, 0),
        size=(200, 200),
    )

    # Check that the start point is indeed on the keepout edge
    assert ko_inside.left == pytest.approx(arc.getStartPoint().x)

    new_items = applyKeepouts([arc], [ko_inside])
    assert len(new_items) == 0
