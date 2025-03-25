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
# (C) 2022 by Armin Schoisswohl, @armin.sch

import sys

from KicadModTree.nodes import *
from kilibs.geom import geometric_util as geo
from typing import Sequence

from math import tan, radians


def calculateOffsetPolygonNodes(nodes: Sequence[Vector2D], offset: float, split_angle: float = 90):
    """
    Calculates the polygon with a specified offset from the given polygon.

    Args:
        nodes: the list of Vector2D nodes of the polygon to offset.
        offset: the offset in mm.

    Returns:
        the list of offset nodes.

    Notes:
        - the nodes must be sorted clockwise (in the left-handed KiCad
          coordinate system), otherwise the offset will have to be inverted
        - there is currently no detection of eventually resulting self
          intersections
        - the polygon is assumed to be closed by connecting start and end point
    """

    tol = 1e-7
    if (abs(offset) < tol):
        return nodes[:]

    def clean_duplicates(nodes):
        N = len(nodes)
        return [nodes[n] for n in range(N) if not (nodes[n] - nodes[(n + 1) % N]).is_nullvec(tol)]

    # check if the polygon in closed -- means that we have to close it again afterwards
    closed = (nodes[0] - nodes[-1]).is_nullvec(tol)

    # remove duplicates, these don't make life easier
    nodes = clean_duplicates(nodes)

    offset_polygon = []
    num_nodes = len(nodes)
    for n in range(num_nodes):
        node = Vector2D(nodes[n])

        # calculate directions (incoming and outgoing that node)
        dir_vec1 = (node - Vector2D(nodes[(n - 1) % num_nodes])).normalize(tol)
        dir_vec2 = (Vector2D(nodes[(n + 1) % num_nodes]) - node).normalize(tol)
        # special handling of start and end point if not closed
        if (not closed):
            if (n == 0):
                dir_vec1 = dir_vec2
            elif (n == num_nodes - 1):
                dir_vec2 = dir_vec1

        # calculate outwards-pointing normals
        # Note: we are assuming the polygon is given clockwise in the KiCad
        # coordinate system, which is left-handed (x to the right, y downwards)
        norm_vec1 = copy(dir_vec1).rotate(-90, use_degrees=True)
        norm_vec2 = copy(dir_vec2).rotate(-90, use_degrees=True)
        # calculate angular bisector
        bisec = (norm_vec1 + norm_vec2).normalize(tol)

        # calculate the angle between the incoming and outgoing line
        angle = geo.normalizeAngle(dir_vec2.arg() - dir_vec1.arg())

        if (angle > split_angle):
            # split sharp convex corners into two surrounding the initial corner
            forward = tan(radians(angle/4))
            offset_polygon.append(node + offset * (norm_vec1 + forward * dir_vec1))
            offset_polygon.append(node + offset * (norm_vec2 - forward * dir_vec2))
        else:
            # move point on the angular intersection the correct amount (which is the offset
            # divided by the cosine of the angle between the edges
            if (bisec.is_nullvec(tol) or (norm_vec1.is_nullvec(tol) and norm_vec2.is_nullvec(tol))):
                cos_phi = 1
            else:
                cos_phi = bisec.dot_product(norm_vec1 if not norm_vec1.is_nullvec(tol) else norm_vec2)
            offset_polygon.append(node + (offset / cos_phi) * bisec)

    # TODO: check if we get self-intersections and eliminate them
    # there may be duplicates; remove them before returning
    offset_polygon = clean_duplicates(offset_polygon)

    if (closed):    # close the polygon again in case it was closed before
        offset_polygon.append(offset_polygon[0])

    return offset_polygon


def _collectNodesAsGeometricShapes(node: Node,
                                   layer: str | list[str],
                                   select_drill: bool = False,
                                   silk_pad_clearance: float = 0.0):
    """
    Collect all nodes from a specific layer as geometric shapes (Arcs, Circles, Lines, Rectangles)

    Args:
        node: the root node of the tree to be converted
        layer: the layer to be selected
        select_drill: defines if also drill should be selected (to catch NPTHs)
        silk_pad_clearance: additional clearance between silk and pad to be added to pad shapes

    Returns:
        the list of collected nodes.

    Notes:
        - pads are converted into rectangles or circles (other shapes are not yet supported)
        - drills are (optionally) included as circles (other shapes not yet supported)
        - silk_pad_clearance is an additional offset around pads and holes
    """
    if (not isinstance(layer, str) and isinstance(layer, list)):
        layers = layer
    else:
        layers = [layer]
    for layer in layers[:]:
        if (layer.startswith("F.") or layer.startswith("B.")):
            layers.append("*.%s" % layer.split(".", maxsplit=1)[-1])
    shapes = []
    for c in node:
        if isinstance(c, Pad):
            if any(_ in c.layers for _ in layers):
                if (c.shape in (Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_OVAL)):
                    shapes.append(RectLine(start=c.at - 0.5 * c.size - silk_pad_clearance,
                                           end=c.at + 0.5 * c.size + silk_pad_clearance,
                                           layer=layer, width=0.01).rotate(angle=-c.rotation, origin=c.at))
                elif (c.shape == Pad.SHAPE_CIRCLE):
                    shapes.append(Circle(center=c.at, radius=c.size[0] / 2 + silk_pad_clearance))
                else:
                    sys.stderr.write("cleaning silk over pad is not implemented for pad shape '%s'\n" % c.shape)
            elif (select_drill and c.drill):
                if (c.drill.x != c.drill.y):
                    sys.stderr.write("cleaning silk over non-circular drills is not implemented\n")
                shapes.append(Circle(center=c.at, radius=c.drill[0] * 0.5 + silk_pad_clearance))
        elif (hasattr(c, 'layer') and c.layer in layers and geo.isGeometricPrimitive(c)):
            shapes.append(c)
        else:
            shapes += _collectNodesAsGeometricShapes(
                node=c, layer=layer, select_drill=select_drill,
                silk_pad_clearance=silk_pad_clearance)
    return shapes


def _cleanSilkByMask(silk_shapes: list, mask_shapes: list):
    """

    Args:
        silk_shapes: the list of silk shapes (collected by _collectNodesAsGeometricShapes)
        mask_shapes: the list of mask shapes (collected by _collectNodesAsGeometricShapes)

    Returns:
    The cut silk shapes as a list of geometric primitives; this list can be appended to the module.
    """

    # iterate through all mask shapes
    for mask in mask_shapes:
        cut_silk = []   # initialize the result array
        # iterate through all silk shapes
        for silk in silk_shapes:
            # if we do not have a geometric object, just store it
            if (not hasattr(silk, "cut")):
                print("WARNING: cutting a %s with a %s is not implemented" % (type(silk), type(mask)))
                cut_silk.append(silk)
                continue
            # cut the geometric objects
            segments = silk.cut(mask)
            # store all segments which are not inside the mask
            for seg in segments:
                if not mask.isPointInsideSelf(seg.getMidPoint()):
                    cut_silk.append(seg)
        silk_shapes = cut_silk
    return silk_shapes


def cleanSilkOverMask(footprint: Node, *, side: str, silk_pad_clearance: float, silk_line_width: float,
                      ignore_paste: bool = False):
    """
    Clean SilkScreen contours by removing overlap with pads and holes.

    This is not perfect, but mostly does a very good job

    Args:
        footprint: the KicadModTree Footprint to clean up.
        side: `'F'` for front or `'B'` for back side of the footprint.
        silk_pad_clearance: the clearance between silk and pad.
        ignore_paste: if set to True, then paste is ignored in calculating the silk/mask overlap.
    """
    silk_shapes = _collectNodesAsGeometricShapes(footprint, layer=f"{side:s}.SilkS")
    mask_layers = [f"{side:s}.Mask"]
    if not ignore_paste:
        mask_layers.append(f"{side:s}.Paste")
    mask_shapes = _collectNodesAsGeometricShapes(footprint, layer=mask_layers, select_drill=True,
                                                 silk_pad_clearance=silk_pad_clearance + 0.5 * silk_line_width)
    tidy_silk = _cleanSilkByMask(silk_shapes, mask_shapes)
    for node in silk_shapes:
        footprint.remove(node, traverse=True, virtual=True)
    for node in tidy_silk:
        footprint.append(node)
    return footprint
