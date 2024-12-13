#!/usr/bin/env python

from scripts.tools.drawing_tools import (
    getStandardSilkArrowSize,
    SilkArrowSize,
)
from scripts.tools.nodes import pin1_arrow
from KicadModTree import Direction, Pad, Vector2D


def draw_silk_triangle_for_pad(
    pad: Pad, arrow_size: SilkArrowSize,
    arrow_direction: Direction,
    stroke_width: float,
    pad_silk_offset: float
):
    """
    Draw a south-pointing silk arrow of the given size next to the given
    pad. This is a common idiom for drawing a pin 1 marker.

    The arrow direction is the direction the arrow points in - 0 is rightwards.
    It will be placed pointing towards the pad, so a south-pointing arrow
    will be placed north of the pad.

    Only N/S/E/W directions are supported for now.
    45 degree directions should be OK, but will need the 45 degree arrow.

    This assumes the pad size is the right thing to use for the offsets,
    which is true for the normal shapes: rects, circles, ovals, etc.
    """

    if arrow_direction == Direction.SOUTH:
        apex = Vector2D(
            pad.at.x, pad.at.y - pad.size.y / 2 - pad_silk_offset - stroke_width / 2
        )
    elif arrow_direction == Direction.NORTH:
        apex = Vector2D(
            pad.at.x, pad.at.y + pad.size.y / 2 + pad_silk_offset + stroke_width / 2
        )
    elif arrow_direction == Direction.EAST:
        apex = Vector2D(
            pad.at.x - pad.size.x / 2 + pad_silk_offset + stroke_width / 2, pad.at.y
        )
    elif arrow_direction == Direction.WEST:
        apex = Vector2D(
            pad.at.x + pad.size.x / 2 + pad_silk_offset + stroke_width / 2, pad.at.y
        )
    else:
        raise ValueError(f"Unsupported arrow direction: {arrow_direction}")

    # Adjust for the stroke width
    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, stroke_width
    )

    return pin1_arrow.Pin1SilkscreenArrow(
        apex_position=apex,
        angle=arrow_direction,
        size=silk_arrow_size,
        length=silk_arrow_length,
        layer="F.SilkS",
        line_width_mm=stroke_width,
    )
