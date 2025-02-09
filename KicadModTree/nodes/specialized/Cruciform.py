from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base import Rect
from KicadModTree.nodes.specialized import Polygon
from kilibs.geom import Vector2D


class Cruciform(Node):
    """
    A cruciform is a cross-shaped object that is basically two rectangles
    that intersect at their centers.

    It looks like this:

            +-------+   -------------
            |       |               ^
        +---+       +---+ ---       |
        |       o       |  | t_h    | overall_h
        +---+       +---+ ---       |
            |       |               v
        |   +-------+   +------------
        |   |<-t_w->|   |
        |               |
        |<--overall_w-->|

    It is centred at the origin - you can use a Translate or Rotation transform
    node to move it to the desired location.
    """

    overall_w: float
    overall_h: float
    tail_w: float
    tail_h: float

    def __init__(
        self,
        overall_w: float,
        overall_h: float,
        tail_w: float,
        tail_h: float,
        layer: str,
        width: float,
        fill: bool,
    ):
        Node.__init__(self)

        self.overall_w = overall_w
        self.overall_h = overall_h
        self.tail_w = tail_w
        self.tail_h = tail_h

        if overall_w < tail_w:
            raise ValueError("overall_w must be greater than tail_w")

        if overall_h < tail_h:
            raise ValueError("overall_h must be greater than tail_h")

        self.layer = layer
        self.width = width
        self.fill = fill

    def getVirtualChilds(self):

        c = Vector2D(0, 0)

        if self.overall_w == self.tail_w or self.overall_h == self.tail_h:
            size = Vector2D(self.overall_w, self.overall_h)
            return [
                Rect(  # type: ignore
                    start=c - size / 2,
                    end=c + size / 2,
                    layer=self.layer,
                    width=self.width,
                    fill='solid' if self.fill else 'none',
                ),
            ]

        r1_size_2 = Vector2D(self.overall_w, self.tail_h) / 2
        r2_size_2 = Vector2D(self.tail_w, self.overall_h) / 2

        poly_pts = [
            Vector2D(-r1_size_2.x, -r1_size_2.y),
            Vector2D(-r1_size_2.x, r1_size_2.y),
            Vector2D(-r2_size_2.x, r1_size_2.y),
            Vector2D(-r2_size_2.x, r2_size_2.y),
            Vector2D(r2_size_2.x, r2_size_2.y),
            Vector2D(r2_size_2.x, r1_size_2.y),
            Vector2D(r1_size_2.x, r1_size_2.y),
            Vector2D(r1_size_2.x, -r1_size_2.y),
            Vector2D(r2_size_2.x, -r1_size_2.y),
            Vector2D(r2_size_2.x, -r2_size_2.y),
            Vector2D(-r2_size_2.x, -r2_size_2.y),
            Vector2D(-r2_size_2.x, -r1_size_2.y),
            Vector2D(-r1_size_2.x, -r1_size_2.y),
        ]

        poly = Polygon(
            nodes=poly_pts,
            layer=self.layer,
            width=self.width,
            fill=self.fill,
        )

        return [poly]
