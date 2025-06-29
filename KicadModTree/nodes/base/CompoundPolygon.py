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

"""Class definition for a compound polygon."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.NodeShape import NodeShape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import (
    GeomArc,
    GeomCompoundPolygon,
    GeomLine,
    GeomPolygon,
    GeomShape,
    Vec2DCompatible,
    Vector2D,
)


class CompoundPolygon(NodeShape, GeomCompoundPolygon):
    """A compound polygon."""

    _fp_poly_elements: list[Vector2D | Arc]

    def __init__(
        self,
        shape: (
            CompoundPolygon
            | GeomShape
            | Sequence[Vec2DCompatible]
            | Sequence[GeomPolygon | GeomLine | GeomArc]
        ),
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        serialize_as_fp_poly: bool = True,
        close: bool = True,
    ) -> None:
        """Create a geometric compound polygon.

        Args:
            shape: compound polygon, list of points, polygons, lines or arcs  from which
                to derive the compound polygon.
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the compound polygon is filled, `False` if only the outline
                is visible.
            offset: Amount by which the compound polygon is inflated or deflated (if
                offset is negative).
            serialize_as_fp_poly: If True, will serialize the compound polygon as
                fp_poly, leading to line-segment-appromimations of contained arcs in the
                FP editor (the file format already supports arcs, but the editor does
                not) if False, will break the polygon into free primitives, yielding
                true arcs in the FP editor but no single primitive. Grouping will be
                used.
            close: If `True` the polygon will form a closed shape. If `False` there
                won't be any connecting line between the last and the first point.
        """
        self._fp_poly_elements = []
        NodeShape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomCompoundPolygon.__init__(
            self, shape=shape, serialize_as_fp_poly=serialize_as_fp_poly, close=close
        )
        if offset:
            self.inflate(amount=offset)

    def get_flattened_nodes(self) -> list[Node]:
        """Return the nodes to serialize."""
        if self.serialize_as_fp_poly and self.close:
            return cast(list[Node], [self])
        else:
            return cast(list[Node], self.to_child_nodes(list(self.get_atomic_shapes())))

    def get_fp_poly_elements(self) -> list[Vector2D | Arc]:
        if not self._fp_poly_elements:
            self._fp_poly_elements: list[Vector2D | Arc] = []
            for geom in self.get_points_and_arcs():
                if isinstance(geom, Vector2D):
                    self._fp_poly_elements.append(geom)
                else:
                    arc = Arc(
                        shape=geom, layer=self.layer, width=self.width, style=self.style
                    )
                    arc._parent = self._parent
                    self._fp_poly_elements.append(arc)
        return self._fp_poly_elements
