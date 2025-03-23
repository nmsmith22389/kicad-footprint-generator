"""
Simple test of some geometry functions, including confidence tests
of geom_test utility functions.
"""

import kilibs.test_utils.geom_test as geom_test
from kilibs.geom import geometricLine


def test_geom_line():

    line1 = geometricLine(start=(0, 0), end=(1, 1))
    line2 = geometricLine(start=(0, 0), end=(1, 1))

    assert geom_test.seg_same(line1, line2)

    line2 = geometricLine(start=(1, 1), end=(0, 0))

    assert geom_test.seg_same_endpoints(line1, line2)

    line2 = geometricLine(start=(1, 1), end=(1, 0))

    assert not geom_test.seg_same(line1, line2)
