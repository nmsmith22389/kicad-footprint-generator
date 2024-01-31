from dataclasses import dataclass

RECT = 'rect'


@dataclass
class RectProperties():

    type = RECT
    # Expressions that define the coordinates of the rectangle
    # (these will be evaluated in the context of each footprint)
    x1_expr: str
    y1_expr: str
    x2_expr: str
    y2_expr: str

    def __init__(self, rect_spec):

        try:
            rect = rect_spec['rect']
        except KeyError:
            raise ValueError('Rectangular shape must have a "rect" key')

        if len(rect) != 2:
            raise ValueError('Rectangular shape must have exactly two points')

        if len(rect[0]) != 2 or len(rect[1]) != 2:
            raise ValueError('Each point of the rectangular shape must have exactly two coordinates')

        self.x1_expr = rect[0][0]
        self.y1_expr = rect[0][1]

        self.x2_expr = rect[1][0]
        self.y2_expr = rect[1][1]


def construct_shape(shape_spec: dict):

    supported_shapes = [RECT]

    found_shape_types = [key for key in shape_spec.keys() if key in supported_shapes]

    if len(found_shape_types) != 1:
        raise ValueError(f'Exactly one shape type must be specified, found {len(found_shape_types)}')

    if found_shape_types[0] == RECT:
        return RectProperties(shape_spec)

    raise ValueError(f'Unknown shape type {type}')
