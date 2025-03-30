from kilibs.geom import Rectangle
from KicadModTree import Circle, Node
from KicadModTree.nodes.specialized import Stadium
from scripts.tools.global_config_files import global_config as GC


def make_round_or_stadium_courtyard(
    global_config: GC.GlobalConfig, bounding_rectangle: Rectangle
) -> list[Node]:
    """
    Create a courtyard that fits within the given rectangle, using a stadium
    if the rectangle isn't square, or a circle if it is.

    This will do the necessary grid rounding per GC settings.
    """

    courtyard_rect = bounding_rectangle.rounded(outwards=True, grid=global_config.courtyard_grid)

    layer = "F.CrtYd"
    width = global_config.courtyard_line_width

    # Could make this parameterised, but do we need that?
    tolerance = global_config.courtyard_grid

    # create courtyard
    if abs(courtyard_rect.size.x - courtyard_rect.size.y) > tolerance:
        courtyard = Stadium.Stadium.by_inscription(
                courtyard_rect,
                layer=layer,
                width=width,
            )
    else:
        courtyard = Circle(
            center=courtyard_rect.center,
            radius=courtyard_rect.max_dimension / 2,
            layer=layer,
            width=width,
        )
    return [courtyard]
