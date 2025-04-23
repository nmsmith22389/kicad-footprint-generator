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
# Copyright The KiCad Developers.


from operator import itemgetter
from typing import Self

import pyclipper

from KicadModTree import (
    ExposedPad,
    Line,
    Node,
    Pad,
    PadArray,
    PolygonLine,
    Rect,
    RectLine,
    Vector2D,
)
from kilibs.geom import BoundingBox, PolygonPoints, Rectangle
from kilibs.geom.rounding import is_polygon_clockwise, round_to_grid_increasing_area
from scripts.tools.global_config_files.global_config import GlobalConfig


class CourtyardBuilder:
    SCALE_FACTOR = 1e6

    def __init__(self, global_config: GlobalConfig) -> Self:
        self.global_config = global_config
        self.src_pts: list[float] = []  # source points
        self.crt_pts: list[float] = []  # courtyard points
        self._node: Node | None = None
        self._bbox: BoundingBox | None = None

    @classmethod
    def from_node(
        cls,
        node: Node,
        global_config: GlobalConfig,
        offset_fab: float,
        offset_pads: float | None = None,
        outline: Node | Rectangle | BoundingBox | PolygonPoints | None = None,
    ) -> Self:
        """
        Derives a courtyard with minimal area from the pads and primitives on the
        fabrication layer of the footprint and adds it to the footprint. Alternatively,
        instead of using the primitives on the fabrication layer of the footprint, the
        outline given as a separate argument can be used.

        Args:
            node: a node (typically the footprint).
            global_config: the global config.
            offset_fab: minimum clearance between courtyard and primitives on the fabrication layer.
            offset_pads: minimum clearance between courtyard and the pads. If omitted, the value of offset_fab is used.
            outline: optional outline of the component body.

        Returns:
            the bounding box of the courtyard.
        """
        cb = cls(global_config)
        if outline is None:
            use_fab_layer = True
        else:
            cb.add_element(outline, offset_fab, offset_pads, True)
            use_fab_layer = False
        for n in node.normalChildItems():
            cb.add_element(n, offset_fab, offset_pads, use_fab_layer)
        cb._build()
        return cb

    @property
    def bbox(self) -> BoundingBox:
        """
        Get the bounding box of the courtyard
        """
        if self._bbox is None:
            top = min(self.crt_pts, key=itemgetter(1))[1]
            bottom = max(self.crt_pts, key=itemgetter(1))[1]
            left = min(self.crt_pts, key=itemgetter(0))[0]
            right = max(self.crt_pts, key=itemgetter(0))[0]
            p1 = Vector2D(left, top)
            p2 = Vector2D(right, bottom)
            self._bbox = BoundingBox(min_pt=p1, max_pt=p2)
            return self._bbox
        else:
            return self._bbox

    @property
    def node(self) -> Node:
        """
        Get the courtyard node
        """
        if self._node is None:
            return self._build()
        else:
            return self._node

    def _build(self) -> Node:
        """
        Calculate and return the courtyard node
        """
        if len(self.src_pts) == 0:
            raise RuntimeError("Insufficient shapes to build a courtyard from.")
        pc = pyclipper.Pyclipper()
        pc.AddPaths(
            pyclipper.scale_to_clipper(self.src_pts, CourtyardBuilder.SCALE_FACTOR),
            pyclipper.PT_SUBJECT,
            True,
        )
        result = pc.Execute(
            pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO
        )
        if len(result) != 1:
            result = CourtyardBuilder._remove_holes(result)
        if len(result) != 1:
            result = CourtyardBuilder._unite_disjunct_courtyards(result)
        round_to_grid_increasing_area(
            result[0],
            int(self.global_config.courtyard_grid * CourtyardBuilder.SCALE_FACTOR),
        )
        result = CourtyardBuilder._simplify(result)
        crt_pts = pyclipper.scale_from_clipper(result, CourtyardBuilder.SCALE_FACTOR)[0]
        self.crt_pts = crt_pts

        width = self.global_config.courtyard_line_width
        if len(crt_pts) == 4:
            p1 = crt_pts[0]
            p2 = crt_pts[2]
            self._node = Rect(width=width, layer="F.CrtYd", start=p1, end=p2)
        else:
            crt_pts.append(crt_pts[0])  # close the courtyard
            self._node = PolygonLine(polygon=crt_pts, width=width, layer="F.CrtYd")
        return self._node

    def add_element(
        self,
        node: Node | Rectangle | BoundingBox | PolygonPoints,
        offset_fab: float,
        offset_pads: float | None = None,
        use_fab_layer: bool = True,
    ):
        """
        Add an element (node or geometric primitive) to the list of courtyard points
        """
        if offset_pads is None:
            offset_pads = offset_fab
        if isinstance(node, Rectangle | BoundingBox):
            self.add_rectangle(node, offset_fab)
        if (
            isinstance(node, Rect | RectLine)
            and node.layer == "F.Fab"
            and use_fab_layer
        ):
            self.add_rect(node, offset_fab)
        elif (
            isinstance(node, PolygonLine | PolygonPoints)
            and node.layer == "F.Fab"
            and use_fab_layer
        ):
            self.add_polygon(node, offset_fab)
        elif isinstance(node, Line) and node.layer == "F.Fab" and use_fab_layer:
            self.add_line(node, offset_fab)
        elif isinstance(node, Pad | ExposedPad):
            self.add_pad(node, offset_pads)
        elif isinstance(node, PadArray):
            self.add_pad_array(node, offset_pads)

    def add_rectangle(self, rectangle: Rectangle | BoundingBox, offset: float):
        """
        Add a Rectangle or BoundingBox to the list of courtyard points
        """
        self.src_pts.append(
            [
                [rectangle.right + offset, rectangle.top - offset],
                [rectangle.right + offset, rectangle.bottom + offset],
                [rectangle.left - offset, rectangle.bottom + offset],
                [rectangle.left - offset, rectangle.top - offset],
            ]
        )
        self._node = None  # invalidate previous node calculations

    def add_rect(self, rect: Rect | RectLine, offset: float):
        """
        Add a Rect or RectLine to the list of courtyard points
        """
        left = min(rect.start_pos.x, rect.end_pos.x) - offset
        right = max(rect.start_pos.x, rect.end_pos.x) + offset
        top = min(rect.start_pos.y, rect.end_pos.y) - offset
        bottom = max(rect.start_pos.y, rect.end_pos.y) + offset
        self.src_pts.append(
            [[right, top], [right, bottom], [left, bottom], [left, top]]
        )
        self._node = None  # invalidate previous node calculations

    def add_polygon(self, pl: PolygonLine | PolygonPoints, offset: float):
        """
        Add a Polygon to the list of courtyard points
        """
        polygon = []
        for node in pl.nodes:
            if isinstance(node, Vector2D):
                polygon.append([node.x, node.y])

        if len(polygon) < 2:
            # ignore polygons with less than 2 vertices
            return
        elif len(polygon) == 2:
            # polygons with 2 vertices are just lines
            self.add_line(Line(start=polygon[0], end=polygon[1]), offset)
            return
        else:
            # add offset around polygon
            pco = pyclipper.PyclipperOffset()
            polygon = pyclipper.scale_to_clipper(polygon, CourtyardBuilder.SCALE_FACTOR)
            pco.AddPath(polygon, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
            polygon = pyclipper.scale_from_clipper(
                pco.Execute(int(offset * CourtyardBuilder.SCALE_FACTOR)),
                CourtyardBuilder.SCALE_FACTOR,
            )
            # make sure that the polygon is defined in clockwise direction
            if not is_polygon_clockwise(polygon[0]):
                polygon[0].reverse()
            self.src_pts.append(polygon[0])
            self._node = None  # invalidate previous node calculations

    def add_line(self, line: Line, offset: float):
        """
        Add a Line to the list of courtyard points
        """
        delta_parallel = (line.end_pos - line.start_pos).normalize() * offset
        delta_orthogonal = delta_parallel.orthogonal().normalize() * offset
        pts: list[Vector2D] = []
        pts.append(line.start_pos - delta_parallel - delta_orthogonal)
        pts.append(line.end_pos + delta_parallel - delta_orthogonal)
        pts.append(line.end_pos + delta_parallel + delta_orthogonal)
        pts.append(line.start_pos - delta_parallel + delta_orthogonal)
        self.src_pts.append([[pt.x, pt.y] for pt in pts])
        self._node = None  # invalidate previous node calculations

    def add_pad(self, pad: Pad | ExposedPad, offset: float):
        """
        Add a Pad or ExposedPad to the list of courtyard points
        """
        left = pad.at.x - pad.size.x / 2 - offset
        right = pad.at.x + pad.size.x / 2 + offset
        top = pad.at.y - pad.size.y / 2 - offset
        bottom = pad.at.y + pad.size.y / 2 + offset
        self.src_pts.append(
            [[right, top], [right, bottom], [left, bottom], [left, top]]
        )
        self._node = None  # invalidate previous node calculations

    def add_pad_array(self, padarray: PadArray, offset: float):
        """
        Add a PadArray to the list of courtyard points
        """
        children = padarray.getVirtualChilds()
        if not children:
            return
        first_pad = children[0]
        last_pad = children[-1]
        left = min(first_pad.at.x, last_pad.at.x) - first_pad.size.x / 2 - offset
        right = max(first_pad.at.x, last_pad.at.x) + first_pad.size.x / 2 + offset
        top = min(first_pad.at.y, last_pad.at.y) - first_pad.size.y / 2 - offset
        bottom = max(first_pad.at.y, last_pad.at.y) + first_pad.size.y / 2 + offset
        self.src_pts.append(
            [[right, top], [right, bottom], [left, bottom], [left, top]]
        )
        self._node = None  # invalidate previous node calculations

    @staticmethod
    def _unite_disjunct_courtyards(
        crts: list[list[list[float]]],
    ) -> list[list[list[float]]]:
        # increase offset around polygons, unite them, decrease offset around resulting polygon
        offset = 2e5  # 0.2 mm

        # increase offset around polygons and unite them
        # (PyclipperOffset automatically unites overlapping polygons)
        pco = pyclipper.PyclipperOffset()
        pco.AddPaths(crts, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        crts = pco.Execute(offset)

        # decrease offset around polygons
        pco.Clear()
        pco.AddPaths(crts, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        crts = pco.Execute(-offset)

        if len(crts) != 1:
            raise ValueError(f"Failed to unite courtyards.")
            # If this error is thrown, try increasing the value of 'offset'.

        return crts

    @staticmethod
    def _remove_holes(crts: list[list[list[float]]]) -> list[list[list[float]]]:
        crts_without_holes = []
        for crt in crts:
            if is_polygon_clockwise(crt):
                crts_without_holes.append(crt)
        return crts_without_holes

    @staticmethod
    def _simplify(crts: list[list[list[float]]]) -> list[list[list[float]]]:
        pc = pyclipper.Pyclipper()
        return pyclipper.SimplifyPolygons(crts, pyclipper.PFT_NONZERO)
