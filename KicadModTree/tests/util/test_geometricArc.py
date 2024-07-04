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

from KicadModTree.util.geometric_util import geometricArc


def test_isPointOnSelf():

    def obviousTests(arc):

        assert arc.isPointOnSelf(arc.getStartPoint())
        assert arc.isPointOnSelf(arc.getEndPoint())
        assert arc.isPointOnSelf(arc.getMidPoint())

        if arc.getRadius() > 0:
            assert not arc.isPointOnSelf(arc.getCenter())

    arc = geometricArc(center=(0, 0), start=(100, 0), end=(0, 100))

    obviousTests(arc)