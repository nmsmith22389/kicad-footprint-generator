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
# (C) 2024 by Kicad Library Generator contributors

import unittest

from kilibs.geom.geometric_util import geometricArc, geometricLine

# Useful arcs for tests (don't have to use these)
ARC_90_UPPER_RIGHT_QUADRANT = geometricArc(center=(0, 0), start=(100, 0), end=(0, 100))


class GeometricArc_TestCase(unittest.TestCase):

    def test_init_by_cse(self):

        arc = geometricArc(center=(0, 0), start=(100, 0), end=(0, 100))

        self.assertAlmostEqual(arc.getCenter(), (0, 0))
        self.assertAlmostEqual(arc.getStartPoint(), (100, 0))
        self.assertAlmostEqual(arc.getEndPoint(), (0, 100))

        self.assertAlmostEqual(arc.getRadius(), 100)
        self.assertAlmostEqual(arc.angle, 90)

    def test_init_by_cra(self):

        arc = geometricArc(center=(0, 0), start=(100, 0), angle=90)

        self.assertAlmostEqual(arc.getCenter(), (0, 0))
        self.assertAlmostEqual(arc.getStartPoint(), (100, 0))
        self.assertAlmostEqual(arc.getEndPoint(), (0, 100))

        self.assertAlmostEqual(arc.getRadius(), 100)
        self.assertAlmostEqual(arc.angle, 90)

    def test_init_by_cse_needs_cse(self):
        """
        Test that initializing an arc by center, start, and end points requires
        all three values.
        """

        with self.assertRaises(KeyError):
            arc = geometricArc(center=(0, 0), end=(0, 100))

        with self.assertRaises(KeyError):
            arc = geometricArc(center=(0, 0), start=(100, 0))

        with self.assertRaises(KeyError):
            arc = geometricArc(start=(100, 0), end=(0, 100))

    def test_isPointOnSelf(self):

        def obviousTests(arc):
            """
            Test that the start, end, and midpoint are on the arc.
            If the radius is greater than 0, the center should not be on the arc.
            """

            assert arc.isPointOnSelf(arc.getStartPoint())
            assert arc.isPointOnSelf(arc.getEndPoint())
            assert arc.isPointOnSelf(arc.getMidPoint())

            if arc.getRadius() > 0:
                assert not arc.isPointOnSelf(arc.getCenter())

        arc = ARC_90_UPPER_RIGHT_QUADRANT

        obviousTests(arc)

    def test_cutWithLine(self):

        arc = ARC_90_UPPER_RIGHT_QUADRANT

        # 45 degree line, up and right
        line = geometricLine(start=(0, 0), end=(100, 100))

        cut_arcs = arc.cut(line)

        assert len(cut_arcs) == 2

        self.assertAlmostEqual(cut_arcs[0].getStartPoint(), arc.getStartPoint())
        self.assertAlmostEqual(cut_arcs[0].getEndPoint(), arc.getMidPoint())
        self.assertAlmostEqual(cut_arcs[1].getStartPoint(), cut_arcs[0].getEndPoint())
        self.assertAlmostEqual(cut_arcs[1].getEndPoint(), arc.getEndPoint())
