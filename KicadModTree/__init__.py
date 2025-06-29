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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

"""The 'node' library."""

from KicadModTree.KicadFileHandler import KicadFileHandler, KicadPrettyLibrary
from KicadModTree.ModArgparser import ModArgparser
from KicadModTree.nodes import (
    Arc,
    ChamferedNativePad,
    ChamferedPad,
    ChamferedPadGrid,
    ChamferRect,
    ChamferSelPadGrid,
    Circle,
    CompoundPolygon,
    Cross,
    Cruciform,
    EmbeddedFonts,
    ExposedPad,
    Footprint,
    FootprintType,
    Group,
    Hatch,
    Keepouts,
    Line,
    Model,
    MultipleParentsError,
    Node,
    NodeShape,
    Pad,
    PadArray,
    PadConnection,
    Polygon,
    PolygonLine,
    Property,
    Rectangle,
    RectLine,
    RecursionDetectedError,
    ReferencedPad,
    RingPad,
    Rotation,
    RoundRectangle,
    Stadium,
    Text,
    Translation,
    Trapezoid,
    Zone,
    ZoneFill,
)
from KicadModTree.util import ChamferSizeHandler, LineStyle, RoundRadiusHandler, CornerSelection
from kilibs.geom.vector import Vector2D  # TODO remove this import.

__all__ = [
    "Arc",
    "ChamferRect",
    "ChamferSelPadGrid",
    "ChamferedNativePad",
    "ChamferedPad",
    "ChamferedPadGrid",
    "ChamferSizeHandler",
    "Circle",
    "CompoundPolygon",
    "CornerSelection",
    "Cross",
    "Cruciform",
    "EmbeddedFonts",
    "ExposedPad",
    "Footprint",
    "FootprintType",
    "Group",
    "Hatch",
    "Keepouts",
    "KicadFileHandler",
    "KicadPrettyLibrary",
    "Line",
    "LineStyle",
    "ModArgparser",
    "Model",
    "MultipleParentsError",
    "Node",
    "NodeShape",
    "Pad",
    "PadArray",
    "PadConnection",
    "Polygon",
    "PolygonLine",
    "Property",
    "RecursionDetectedError",
    "RectLine",
    "Rectangle",
    "ReferencedPad",
    "RingPad",
    "Rotation",
    "RoundRadiusHandler",
    "RoundRectangle",
    "Stadium",
    "Text",
    "Translation",
    "Trapezoid",
    "Vector2D",
    "Zone",
    "ZoneFill",
]
