# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

"""Definition of the KiCad native shapes."""
from __future__ import annotations

from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_circle import GeomCircle
from kilibs.geom.shapes.geom_compound_polygon import GeomCompoundPolygon
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_polygon import GeomPolygon
from kilibs.geom.shapes.geom_rectangle import GeomRectangle

GeomShapeNative = (
    GeomArc | GeomCircle | GeomLine | GeomRectangle | GeomPolygon | GeomCompoundPolygon
)
"""A union for the basic shapes that are native to KiCad."""
