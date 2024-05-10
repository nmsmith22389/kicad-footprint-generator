from dataclasses import dataclass

from typing import Union, Callable
from .ast_evaluator import ASTevaluator

from KicadModTree import Vector2D
from scripts.tools.geometry.rectangle import Rectangle

RECT = 'rect'


@dataclass
class RectProperties():

    type = RECT
    # Expressions that define the coordinates of the rectangle
    # (these will be evaluated in the context of each footprint)
    # which can only happen much later when the variables are known
    @dataclass
    class CornerExprs:
        x1_expr: str
        y1_expr: str
        x2_expr: str
        y2_expr: str

    @dataclass
    class CenterSizeExprs:
        cx_expr: str
        cy_expr: str
        width_expr: str
        height_expr: str

    exprs: Union[CornerExprs, CenterSizeExprs]

    def __init__(self, rect: dict):

        if 'center' in rect:
            if not 'size' in rect:
                raise ValueError('Rectangular shape with "center" also needs "size" key')

            if len(rect['center']) != 2 or len(rect['size']) != 2:
                raise ValueError('Both "center" and "size" must have exactly two coordinates')

            self.exprs = self.CenterSizeExprs(
                cx_expr=rect['center'][0],
                cy_expr=rect['center'][1],
                width_expr=rect['size'][0],
                height_expr=rect['size'][1]
            )
        elif 'corners' in rect:
            corners = rect['corners']

            if len(corners) != 2 or len(corners[0]) != 2 or len(corners[1]) != 2:
                raise ValueError('Each point of the rectangular shape must have exactly two coordinates')

            self.exprs = self.CornerExprs(
                x1_expr=corners[0][0],
                y1_expr=corners[0][1],
                x2_expr=corners[1][0],
                y2_expr=corners[1][1]
            )
        else:
            raise ValueError('Rectangular shape must have either "center/size" or "corners" definition')


    def evaluate_expressions(self, expr_evaluator: Callable) -> Rectangle:
        if isinstance(self.exprs, RectProperties.CornerExprs):
            corner1 = Vector2D(expr_evaluator(self.exprs.x1_expr),
                           expr_evaluator(self.exprs.y1_expr))
            corner2 = Vector2D(expr_evaluator(self.exprs.x2_expr),
                            expr_evaluator(self.exprs.y2_expr))
            return Rectangle.by_corners(corner1, corner2)

        elif isinstance(self.exprs, RectProperties.CenterSizeExprs):

            center = Vector2D(expr_evaluator(self.exprs.cx_expr),
                              expr_evaluator(self.exprs.cy_expr))
            size = Vector2D(expr_evaluator(self.exprs.width_expr),
                            expr_evaluator(self.exprs.height_expr))
            return Rectangle(center, size)

        raise RuntimeError("Invalid rectangle expression type")


def construct_shape(shape_spec: dict):

    if not 'type' in shape_spec:
        raise ValueError('Shape must have a "type" key')

    type = shape_spec['type']

    if type == RECT:
        return RectProperties(shape_spec)

    raise ValueError(f'Unknown shape type {type}')
