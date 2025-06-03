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

from KicadModTree.nodes import Circle, Node, NodeShape, Pad, Rectangle
from kilibs.geom import GeomShape, GeomShapeAtomic, GeomShapeClosed


def _collectNodesAsGeometricShapes(
    node: Node,
    layer: str | list[str],
    select_drill: bool = False,
    silk_pad_clearance: float = 0.0,
) -> list[Node]:
    """Collect all geometric nodes and pads from a specific layer as geometric nodes
    (Arc, Line, Circle, Rectangle, etc.).

    Args:
        node: The root node of the tree to be converted.
        layer: The layer(s) to be selected.
        select_drill: Defines if also drill holes should be selected (to catch NPTHs).
        silk_pad_clearance: Additional clearance between silk and pad to be added to pad
            shapes.

    Returns:
        The list of collected nodes.

    Notes:
        - Pads are converted into rectangles or circles (other shapes are not yet
            supported).
        - Drills are (optionally) included as circles (other shapes not yet supported).
        - `silk_pad_clearance` is an additional offset around pads and holes.
    """
    if not isinstance(layer, str) and isinstance(layer, list):
        layers = layer
    else:
        layers = [layer]
    for layer in layers[:]:
        if layer.startswith("F.") or layer.startswith("B."):
            layers.append("*.%s" % layer.split(".", maxsplit=1)[-1])
    shapes = []
    for c in node:
        if isinstance(c, Pad):
            if any(_ in c.layers for _ in layers):
                if c.shape in (Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_OVAL):
                    shapes.append(
                        Rectangle(
                            start=c.at - 0.5 * c.size - silk_pad_clearance,
                            end=c.at + 0.5 * c.size + silk_pad_clearance,
                            layer=layer,
                            width=0.01,
                        ).rotate(angle=-c.rotation, origin=c.at)
                    )
                elif c.shape == Pad.SHAPE_CIRCLE:
                    shapes.append(
                        Circle(center=c.at, radius=c.size[0] / 2 + silk_pad_clearance)
                    )
                else:
                    sys.stderr.write(
                        "cleaning silk over pad is not implemented for pad shape '%s'\n"
                        % c.shape
                    )
            elif select_drill and c.drill:
                if c.drill.x != c.drill.y:
                    sys.stderr.write(
                        "cleaning silk over non-circular drills is not implemented\n"
                    )
                shapes.append(
                    Circle(center=c.at, radius=c.drill[0] * 0.5 + silk_pad_clearance)
                )
        elif (
            hasattr(c, "layer") and c.layer in layers and isinstance(c, GeomShapeAtomic)
        ):
            shapes.append(c)
        else:
            shapes += _collectNodesAsGeometricShapes(
                node=c,
                layer=layer,
                select_drill=select_drill,
                silk_pad_clearance=silk_pad_clearance,
            )
    return shapes


def _cleanSilkByMask(
    silk_shapes: list[GeomShape], mask_shapes: list[GeomShapeClosed]
) -> list[NodeShape]:
    """Applies the mask as a keepout to the silk screen shapes.

    Args:
        silk_shapes: The list of silk shapes (collected by
            `_collectNodesAsGeometricShapes()`).
        mask_shapes: The list of mask shapes (collected by
            `_collectNodesAsGeometricShapes()`).

    Returns:
        The cut silk shapes as a list of geometric primitives; this list can be appended
            to the module.
    """
    for mask in mask_shapes:
        kept_out_silk = []
        for silk in silk_shapes:
            kept_out_silk += mask.keepout(silk)
        silk_shapes = kept_out_silk
    return silk_shapes


def cleanSilkOverMask(
    footprint: Node,
    *,
    side: str,
    silk_pad_clearance: float,
    silk_line_width: float,
    ignore_paste: bool = False,
):
    """Clean the silkscreen contours by removing overlap with pads and holes.

    This is not perfect, but mostly does a very good job.

    Args:
        footprint: The KicadModTree footprint to clean up.
        side: `'F'` for front or `'B'` for back side of the footprint.
        silk_pad_clearance: The clearance between silk and pad.
        ignore_paste: If set to `True`, then paste is ignored in calculating the
            silk/mask overlap.
    """
    silk_shapes = _collectNodesAsGeometricShapes(footprint, layer=f"{side:s}.SilkS")
    mask_layers = [f"{side:s}.Mask"]
    if not ignore_paste:
        mask_layers.append(f"{side:s}.Paste")
    mask_shapes = _collectNodesAsGeometricShapes(
        footprint,
        layer=mask_layers,
        select_drill=True,
        silk_pad_clearance=silk_pad_clearance + 0.5 * silk_line_width,
    )
    tidy_silk = _cleanSilkByMask(silk_shapes, mask_shapes)
    for node in silk_shapes:
        footprint.remove(node, traverse=True, virtual=True)
    for node in tidy_silk:
        footprint.append(node)
    return footprint
