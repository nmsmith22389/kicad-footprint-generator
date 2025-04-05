#!/usr/bin/env python

from scripts.tools.drawing_tools import (
    getStandardSilkArrowSize,
    SilkArrowSize,
)
from scripts.tools.nodes import pin1_arrow
from KicadModTree import Pad
from scripts.tools.global_config_files.global_config import GlobalConfig
from kilibs.geom import Direction, Vector2D


def draw_silk_triangle_for_pad(
    pad: Pad, arrow_size: SilkArrowSize,
    arrow_direction: Direction,
    stroke_width: float,
    pad_silk_offset: float
):
    """
    Draw a silk arrow of the given size next to the given pad. This is a common
    idiom for drawing a pin 1 marker.

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
            pad.at.x - pad.size.x / 2 - pad_silk_offset - stroke_width / 2, pad.at.y
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


def draw_silk_triangle_clear_of_fab_hline_and_pad(
    global_config: GlobalConfig,
    pad: Pad,
    arrow_direction: Direction,
    line_y: float,
    line_clearance_y: float,
    arrow_size: SilkArrowSize,
):
    r"""
    Draw an arrow pointing towards a pad, but clear of some horizontal line.

    This is quite common for SMT parts with quite long gullwings, where putting
    the arrow at the end of the pad is a bit wasteful.

             +---+
    -------  |   |  ------- <-- nominal line
        |\   |   | <--\
        | >  +---+     \-- pad
        |/

    :param global_config: The global configuration
    :param pad: The pad to draw the arrow near
    :param arrow_direction: The direction the arrow points in (EAST or WEST)
    :param line_y: The y position of the line to clear
    :param line_clearance: How far to clear the line (this is the space from the
                           line centre to the node of the arrow)
    :param arrow_size: The size of the arrow
    """

    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, global_config.silk_line_width
    )

    # First figure out the apex y
    apex_offset = line_clearance_y + silk_arrow_size / 2
    apex_y = line_y - apex_offset if (line_clearance_y < 0) else line_y + apex_offset

    pad_center_to_node_offset_x  = pad.size.x / 2 + global_config.silk_pad_offset

    if arrow_direction == Direction.EAST:
        apex_x = pad.at.x - pad_center_to_node_offset_x
    elif arrow_direction == Direction.WEST:
        apex_x = pad.at.x + pad_center_to_node_offset_x
    else:
        raise ValueError(f"Unsupported arrow direction: {arrow_direction}")

    return pin1_arrow.Pin1SilkscreenArrow(
        apex_position=Vector2D(apex_x, apex_y),
        angle=arrow_direction,
        size=silk_arrow_size,
        length=silk_arrow_length,
        layer="F.SilkS",
        line_width_mm=global_config.silk_line_width
    )

def draw_silk_triangle45_clear_of_fab_hline_and_pad(
    global_config: GlobalConfig,
    pad: Pad,
    arrow_direction: Direction,
    line_y: float,
    line_clearance_y: float,
    arrow_size: SilkArrowSize,
):
    r"""
    Draw an arrow pointing towards a pad, but clear of some horizontal line.

    This is quite common for SMT parts with quite short gullwings, where putting
    the arrow at the end of the pad is a bit wasteful, but there isn't enough
    protruding pad for a 90 degree arrow.

             +---+
    -------  |   |  ------- <-- nominal line
        --+  |   | <--\
         \|  +---+     \-- pad

    :param global_config: The global configuration
    :param pad: The pad to draw the arrow near
    :param arrow_direction: The direction the arrow points in (NE, NW, SE, SW)
    :param line_y: The y position of the line to clear
    :param line_clearance: How far to clear the line (this is the space from the
                           line centre to the apex of the arrow)
    :param arrow_size: The size of the arrow
    """

    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, global_config.silk_line_width
    )

    line_width = global_config.silk_line_width

    # First figure out the apex y
    apex_offset = line_clearance_y
    apex_y = line_y - apex_offset if (line_clearance_y < 0) else line_y + apex_offset

    pad_center_to_node_offset_x  = pad.size.x / 2 + global_config.silk_pad_offset

    if arrow_direction in [Direction.NORTHEAST, Direction.SOUTHEAST]:
        apex_x = pad.at.x - pad_center_to_node_offset_x
    elif arrow_direction in [Direction.NORTHWEST, Direction.SOUTHWEST]:
        apex_x = pad.at.x + pad_center_to_node_offset_x
    else:
        raise ValueError(f"Unsupported arrow direction: {arrow_direction}")

    return pin1_arrow.Pin1SilkScreenArrow45Deg(
        apex_position=Vector2D(apex_x, apex_y),
        angle=arrow_direction,
        size=silk_arrow_size,
        layer="F.SilkS",
        line_width_mm=line_width,
    )
