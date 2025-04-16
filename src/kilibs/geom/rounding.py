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


# round to grid with epsilon = 1e-7
def round_to_grid_e(x: float, g: float) -> float:
    return round_to_grid(x, g, 1e-7)


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


def round_polygon_to_grid(
    pts: list[list[float]], grid: float, clock_wise: bool, increase_area: bool
) -> list[list[float]]:
    """
    Round a polygon (defined by a list of points) to the grid such that the enclosed
    area will be either >= or <= as before, depending on the value of the parameter
    "increase_area". Operations are run in-place, i.e. overwriting the polygon points
    given as argument.

    Args:
        pts: the list of points definig the polygon.
        grid: the grid to which the rounding is made.
        clock_wise: True if pts define the polygon in clock-wise orientation, False otherwise.
        increase_area: True when rounding away from the polygon, False otherwise.

    Returns:
        the list of points defining the polygon rounded to the grid.
    """
    if clock_wise and increase_area or (not clock_wise and not increase_area):
        round_up = round_to_grid_up
        round_down = round_to_grid_down
    else:
        round_down = round_to_grid_up
        round_up = round_to_grid_down

    num = len(pts)
    for i, pt1 in enumerate(pts):
        pt2 = pts[(i + 1) % num]
        if pt1[0] < pt2[0]:  # going right
            pt1[1] = round_down(pt1[1], grid, 1e-7)
            pt2[1] = round_down(pt2[1], grid, 1e-7)
        elif pt1[0] > pt2[0]:  # going left
            pt1[1] = round_up(pt1[1], grid, 1e-7)
            pt2[1] = round_up(pt2[1], grid, 1e-7)
        if pt1[1] > pt2[1]:  # going up
            pt1[0] = round_down(pt1[0], grid, 1e-7)
            pt2[0] = round_down(pt2[0], grid, 1e-7)
        elif pt1[1] < pt2[1]:  # going down
            pt1[0] = round_up(pt1[0], grid, 1e-7)
            pt2[0] = round_up(pt2[0], grid, 1e-7)


def round_to_grid_increasing_area(
    pts: list[list[float]], grid: float
) -> list[list[float]]:
    """
    Round a polygon (defined by a list of points) to the grid such that the enclosed
    area will be at least as large as before. Operations are run in-place, i.e.
    overwriting the polygon points given as argument.
    """
    clock_wise = is_polygon_clockwise(pts)
    round_polygon_to_grid(pts, grid, clock_wise, increase_area=True)


def round_to_grid_decreasing_area(
    pts: list[list[float]], grid: float
) -> list[list[float]]:
    """
    Round a polygon (defined by a list of points) to the grid such that the enclosed
    area will be smaller or equal as before. Operations are run in-place, i.e.
    overwriting the polygon points given as argument.
    """
    clock_wise = is_polygon_clockwise(pts)
    round_polygon_to_grid(pts, grid, clock_wise, increase_area=False)


def is_polygon_clockwise(pts: list[list[float]]) -> bool:
    """
    Returns True if the polygon points are given in clockwise order, False otherwise.
    """
    sum = 0
    num = len(pts)
    for i, pt1 in enumerate(pts):
        pt2 = pts[(i + 1) % num]
        sum += (pt2[0] - pt1[0]) * (pt2[1] + pt1[1])

    if sum < 0:
        return True
    else:
        return False
