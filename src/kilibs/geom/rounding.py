
import math


# TODO: change the epsilon to 1e-7 once we are ready to review the affected changes
def round_to_grid_up(x: float, g: float, epsilon: float = 0) -> float:
    # epsilon should prevent values like 0.4 (aka 0.40000000000000002) being rounded up to 0.6
    return math.ceil(x / g - epsilon) * g


def round_to_grid_down(x: float, g: float, epsilon: float = 0) -> float:
    return math.floor(x / g + epsilon) * g


# round for grid g
def round_to_grid(x: float, g: float, epsilon: float = 0) -> float:
    """
    Round a number to a multiple of the grid size, _always_ rounding away
    from zero.

    This is the most suitable way to round for many outlines, especially simple
    outlines around objects centred at the origin (e.g. courtyards and silkscreen).
    """
    if g == 0:
        return x
    if isinstance(x, list):
        return_list = []
        for value in x:
            return_list.append(round_to_grid(value, g, epsilon))
        return return_list
    return (
        round(round_to_grid_up(x, g, epsilon), 6)
        if x > 0
        else round(round_to_grid_down(x, g, epsilon), 6)
    )


def round_to_grid_nearest(x: float, g: float) -> float:
    """
    Round a number to a multiple of the grid size, rounding to the nearest
    multiple of the grid size.

    This is the most suitable way to round in case where you are just rounding
    off floating point errors, and you want to round to the nearest grid point.
    """
    if g == 0:
        return x
    return round(round(x / g) * g, 6)
