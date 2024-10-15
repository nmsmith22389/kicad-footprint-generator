#!/usr/bin/env python

from scripts.tools.drawing_tools import (
    draw_triangle_pointing_south,
    getStandardSilkArrowSize,
    SilkArrowSize,
)
from KicadModTree import Pad, Vector2D


def draw_silk_triangle_north_of_pad(
    pad: Pad, arrow_size: SilkArrowSize, stroke_width: float,
    pad_silk_offset: float
):
    """
    Draw a south-pointing silk arrow of the given size north of the given
    pad. This is a common idiom for drawing a pin 1 marker.

    This assumes the pad size is the right thing to use for the offsets,
    which is true for the normal shapes: rects, circles, ovals, etc.
    """

    apex = Vector2D(
        pad.at.x, pad.at.y - pad.size.y / 2 - pad_silk_offset - stroke_width / 2
    )

    # Adjust for the stroke width
    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, stroke_width
    )

    return draw_triangle_pointing_south(
        apex_position=apex,
        size=silk_arrow_size,
        length=silk_arrow_length,
        layer="F.SilkS",
        line_width_mm=stroke_width,
    )
