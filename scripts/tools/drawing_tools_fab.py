#!/usr/bin/env python

from KicadModTree.nodes.specialized.ChamferedRect import (
    ChamferRect,
    ChamferSizeHandler,
    CornerSelection,
)
from kilibs.geom import Vector2D

from scripts.tools.global_config_files.global_config import GlobalConfig


def draw_chamfer_rect_fab(size: Vector2D, global_config: GlobalConfig) -> ChamferRect:
    """
    Constructor for a chamfered Fab-layer rectangle with a chamfer on the top-left corner,
    centered on the origin.

    Mostly just glue between the ChamferRect constructor and the global config.
    """

    return ChamferRect(
        size=size,
        chamfer=global_config.get_fab_bevel,
        corners=CornerSelection({CornerSelection.TOP_LEFT: True}),
        layer="F.Fab",
        width=global_config.fab_line_width,
        fill=False,
    )
