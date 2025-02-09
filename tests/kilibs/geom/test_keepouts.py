"""
Tests for the graphical keepout classes.

These are not intended to be exhaustive, but mostly for a demonstration of how to use the classes,
as well as a place to put some simple tests to catch fiddly edge cases if needed.

Exhaustive tests are high maintenance, and regressions will normally be much more obvious by the
visual diffs of the generated graphics than by delicate stacks of numerical tests.
"""

from kilibs.geom.geometric_util import geometricLine
from kilibs.geom.keepout import KeepoutRect
from scripts.tools.drawing_tools import applyKeepouts

import kilibs.test_utils.geom_test as GeomTest

import pytest


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
