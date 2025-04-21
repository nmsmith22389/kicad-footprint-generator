import math

from KicadModTree import Arc, Line, PolygonLine, Rect
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.specialized.RoundRect import RoundRect
from kilibs.geom import Vector2D

# pep8: noqa
# flake8: noqa: E501


class Trapezoid(Node):
    # draw a trapezoid with a given angle of the vertical lines
    #
    # angle<0
    #      /---------------------\     ^
    #     /                       \    |
    #    /            o            \  size.y
    #   /                           \  |
    #  /-----------------------------\ v
    #  <------------size.x---------->
    def __init__(
        self,
        size: Vector2D,
        angle: float,
        layer: str,
        width: float,
        corner_radius: float = 0,
        start: Vector2D | None = None,
        center: Vector2D | None = None,
    ):
        Node.__init__(self)

        if center is not None:
            assert start is None, "start and center cannot be used together"
            self._start = center - size / 2
        else:
            assert start is not None, "start or center must be provided"
            self._start = start

        self.corner_radius = corner_radius
        self.angle = angle
        self.size = size
        self.layer = layer
        self.width = width

    def getVirtualChilds(self):

        childs: list[Node] = []

        at = self._start
        size = self.size

        dx = self.size.y * math.tan(math.radians(math.fabs(self.angle)))
        cr = self.corner_radius

        if cr == 0:
            if self.angle == 0:
                childs.append(
                    Rect(
                        fill=False,
                        start=0,
                        end=[at.x + size.x, at.y + size.y],
                        layer=self.layer,
                        width=self.width,
                    )
                )
            elif self.angle < 0:
                childs.append(
                    PolygonLine(
                        polygon=[
                            [at.x + dx, at.y],
                            [at.x + size.x - dx, at.y],
                            [at.x + size.x, at.y + size.y],
                            [at.x, at.y + size.y],
                            [at.x + dx, at.y],
                        ],
                        layer=self.layer,
                        width=self.width,
                    )
                )
            elif self.angle > 0:
                childs.append(
                    PolygonLine(
                        polygon=[
                            [at.x, at.y],
                            [at.x + size.x, at.y],
                            [at.x + size.x - dx, at.y + size.y],
                            [at.x + dx, at.y + size.y],
                            [at.x, at.y],
                        ],
                        layer=self.layer,
                        width=self.width,
                    )
                )

        else:
            dx = size[1] * math.tan(math.radians(math.fabs(self.angle)))
            dx2 = cr * math.tan(math.radians((90 - math.fabs(self.angle)) / 2))
            dx3 = cr / math.tan(math.radians((90 - math.fabs(self.angle)) / 2))
            ds2 = cr * math.sin(math.radians(math.fabs(self.angle)))
            dc2 = cr * math.cos(math.radians(math.fabs(self.angle)))

            # fmt: off
            if self.angle == 0:
                rr = RoundRect(size, cr, self.layer, self.width, start=at)
                childs.extend(rr.getVirtualChilds())

            elif self.angle < 0:
                ctl = [at.x + dx + dx2,          at.y + cr]
                ctr = [at.x + size.x - dx - dx2, at.y+cr]
                cbl = [at.x + dx3,               at.y + size.y - cr]
                cbr = [at.x + size.x - dx3,      at.y + size.y - cr]

                childs.append(Arc(center=ctl, start=[ctl[0], at.y],          angle=-(90 - math.fabs(self.angle)), layer=self.layer, width=self.width))  # NOQA
                childs.append(Arc(center=ctr, start=[ctr[0], at.y],          angle=(90 - math.fabs(self.angle)),  layer=self.layer, width=self.width))  # NOQA
                childs.append(Arc(center=cbl, start=[cbl[0], at.y + size.y], angle=(90 + math.fabs(self.angle)),  layer=self.layer, width=self.width))  # NOQA
                childs.append(Arc(center=cbr, start=[cbr[0], at.y + size.y], angle=-(90 + math.fabs(self.angle)), layer=self.layer, width=self.width))   # NOQA

                childs.append(Line(start=[ctl[0], at.y],               end=[ctr[0], at.y],               layer=self.layer, width=self.width))  # NOQA
                childs.append(Line(start=[cbl[0], at.y + size.y],      end=[cbr[0], at.y+size.y],        layer=self.layer, width=self.width))  # NOQA
                childs.append(Line(start=[ctr[0] + dc2, ctr[1] - ds2], end=[cbr[0] + dc2, cbr[1] - ds2], layer=self.layer, width=self.width))  # NOQA
                childs.append(Line(start=[ctl[0] - dc2, ctl[1] - ds2], end=[cbl[0] - dc2, cbl[1] - ds2], layer=self.layer, width=self.width))  # NOQA

            else:
                cbl = [at.x + dx + dx2,          at.y + size.y - cr]
                cbr = [at.x + size.x - dx - dx2, at.y + size.y - cr]
                ctl = [at.x + dx3,               at.y + cr]
                ctr = [at.x + size.x - dx3,      at.y + cr]

                childs.append(Arc(center=ctl, start=[ctl[0], at.y],          angle=-(90 + math.fabs(self.angle)), layer=self.layer, width=self.width))  # NOQA
                childs.append(Arc(center=ctr, start=[ctr[0], at.y],          angle=(90 + math.fabs(self.angle)),  layer=self.layer, width=self.width))  # NOQA
                childs.append(Arc(center=cbl, start=[cbl[0], at.y + size.y], angle=(90 - math.fabs(self.angle)),  layer=self.layer, width=self.width))  # NOQA
                childs.append(Arc(center=cbr, start=[cbr[0], at.y + size.y], angle=-(90 - math.fabs(self.angle)), layer=self.layer, width=self.width))  # NOQA

                childs.append(Line(start=[ctl[0], at.y],               end=[ctr[0], at.y],               layer=self.layer, width=self.width))  # NOQA
                childs.append(Line(start=[cbl[0], at.y + size.y],      end=[cbr[0], at.y + size.y],      layer=self.layer, width=self.width))  # NOQA
                childs.append(Line(start=[ctr[0] + dc2, ctr[1] + ds2], end=[cbr[0] + dc2, cbr[1] + ds2], layer=self.layer, width=self.width))  # NOQA
                childs.append(Line(start=[ctl[0] - dc2, ctl[1] + ds2], end=[cbl[0] - dc2, cbl[1] + ds2], layer=self.layer, width=self.width))  # NOQA
            # fmt: on

        for c in childs:
            c._parent = self

        return childs
