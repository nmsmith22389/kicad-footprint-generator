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

import pyclipper

from KicadModTree import (
    ExposedPad,
    Footprint,
    Node,
    Pad,
    PadArray,
    PolygonLine,
    Rect,
    RectLine,
    Vector2D,
)
from kilibs.geom.rounding import is_polygon_clockwise, round_to_grid_increasing_area


def add_courtyard(
    footprint: Footprint,
    crt_width: float,
    grid: float,
    offset_fab: float,
    offset_pads: float = None,
    outline: Rect | RectLine | PolygonLine = None,
):
    """
    Derives a courtyard with minimal area from the pads and primitives on the
    fabrication layer of the footprint and adds it to the footprint. Alternatively,
    instead of using the primitives on the fabrication layer of the footprint, the
    outline given as a separate argument can be used.

    Args:
        footprint: the footprint.
        crt_width: width of the courtyard line.
        grid: grid to which the corners of the courtyard shall be rounded to.
        offset_fab: minimum clearance between courtyard and primitives on the fabrication layer.
        offset_pads: minimum clearance between courtyard and the pads. If omitted, the value of offset_fab is used.
        outline: optional outline of the component body.

    Returns:
        the bounding box of the courtyard.
    """
    if offset_pads is None:
        offset_pads = offset_fab

    subj = []
    if outline is not None:
        pts = _node_to_pts_offset(outline, offset_fab, offset_pads, True)
        subj.append(pts)
        use_fab_layer = False
    else:
        use_fab_layer = True

    for n in footprint.normalChildItems():
        pts = _node_to_pts_offset(n, offset_fab, offset_pads, use_fab_layer)
        if pts:
            subj.append(pts)

    pc = pyclipper.Pyclipper()
    pc.AddPaths(pyclipper.scale_to_clipper(subj, 1e6), pyclipper.PT_SUBJECT, True)
    result = pc.Execute(
        pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO
    )
    if len(result) != 1:
        result = _unite_disjunct_courtyards(result)
    crt = pyclipper.scale_from_clipper(result, 1e6)

    round_to_grid_increasing_area(crt[0], grid)

    if len(crt[0]) == 4:
        p1 = crt[0][0]
        p2 = crt[0][2]
        footprint.append(Rect(width=crt_width, layer="F.CrtYd", start=p1, end=p2))
    else:
        crt[0].append(crt[0][0])  # close the courtyard
        footprint.append(PolygonLine(polygon=crt[0], width=crt_width, layer="F.CrtYd"))

    # calculate bounding box (typically needed in order to place some text above and
    # below the keepout outline)
    return _pts_to_bounding_box(crt[0])


def _pts_to_bounding_box(pts: list[list[float]]):
    top = min(pts, key=itemgetter(1))[1]
    bottom = max(pts, key=itemgetter(1))[1]
    left = min(pts, key=itemgetter(0))[0]
    right = max(pts, key=itemgetter(0))[0]
    return {"top": top, "bottom": bottom, "left": left, "right": right}


def _node_to_pts_offset(
    node: Node, offset_fab: float, offset_pads: float, use_fab_layer: bool
) -> list[list[float]]:
    if isinstance(node, Rect | RectLine) and node.layer == "F.Fab" and use_fab_layer:
        pts = _rect_to_pts_with_offset(node, offset_fab)
    elif isinstance(node, PolygonLine) and node.layer == "F.Fab" and use_fab_layer:
        pts = _polygonline_to_pts_with_offset(node, offset_fab)
    elif isinstance(node, Pad | ExposedPad):
        pts = _pad_to_pts_with_offset(node, offset_pads)
    elif isinstance(node, PadArray):
        pts = _pad_array_to_pts_with_offset(node, offset_pads)
    else:
        pts = []
    return pts


def _rect_to_pts_with_offset(rect: Rect | RectLine, offset: float) -> list[list[float]]:
    x_left = min(rect.start_pos.x, rect.end_pos.x) - offset
    x_right = max(rect.start_pos.x, rect.end_pos.x) + offset
    y_top = min(rect.start_pos.y, rect.end_pos.y) - offset
    y_bottom = max(rect.start_pos.y, rect.end_pos.y) + offset
    return [[x_right, y_top], [x_right, y_bottom], [x_left, y_bottom], [x_left, y_top]]


def _polygonline_to_pts_with_offset(
    pl: PolygonLine, offset: float
) -> list[list[float]]:
    polygon = []
    for node in pl.nodes:
        if isinstance(node, Vector2D):
            polygon.append([node.x, node.y])

    # add offset around polygon
    pco = pyclipper.PyclipperOffset()
    polygon = pyclipper.scale_to_clipper(polygon, 1e6)
    pco.AddPath(polygon, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
    polygon = pyclipper.scale_from_clipper(pco.Execute(int(offset * 1e6)), 1e6)

    # make sure that the polygon is defined in clockwise direction
    if not is_polygon_clockwise(polygon[0]):
        polygon[0].reverse()
    return polygon[0]


def _pad_to_pts_with_offset(pad: Pad | ExposedPad, offset: float) -> list[list[float]]:
    x_left = pad.at.x - pad.size.x / 2 - offset
    x_right = pad.at.x + pad.size.x / 2 + offset
    y_top = pad.at.y - pad.size.y / 2 - offset
    y_bottom = pad.at.y + pad.size.y / 2 + offset
    return [[x_right, y_top], [x_right, y_bottom], [x_left, y_bottom], [x_left, y_top]]


def _pad_array_to_pts_with_offset(
    padarray: PadArray, offset: float
) -> list[list[float]]:
    children = padarray.getVirtualChilds()
    if not children:
        return []
    padf = children[0]
    padl = children[-1]
    x_left = min(padf.at.x, padl.at.x) - padf.size.x / 2 - offset
    x_right = max(padf.at.x, padl.at.x) + padf.size.x / 2 + offset
    y_top = min(padf.at.y, padl.at.y) - padf.size.y / 2 - offset
    y_bottom = max(padf.at.y, padl.at.y) + padf.size.y / 2 + offset
    return [[x_right, y_top], [x_right, y_bottom], [x_left, y_bottom], [x_left, y_top]]


def _unite_disjunct_courtyards(crts: list[list[list[float]]]) -> list[list[list[float]]]:
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
