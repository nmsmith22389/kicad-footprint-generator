from KicadModTree import Arc, Line, Rect
from KicadModTree.nodes.Node import Node
from kilibs.geom import Vector2D


class RoundRect(Node):
    # Draw a rectangle with rounded corners on all four corners.
    #
    #   /----\
    #  /      \
    # |        |
    # |        |
    # |        |
    # |        |
    # |        |
    #  \      /
    #   \----/
    def __init__(
        self,
        size: Vector2D,
        corner_radius: float,
        layer: str,
        width: float,
        start: Vector2D | None = None,
        center: Vector2D | None = None,
    ):
        Node.__init__(self)

        if center is not None:
            self._start = center - size / 2
        else:
            self._start = start

        self.size = size
        self.corner_radius = corner_radius
        self.layer = layer
        self.width = width

        if corner_radius < 0:
            raise ValueError("corner_radius must be >= 0")

    def getVirtualChilds(self):

        childs: list[Node] = []

        cr = self.corner_radius
        size = self.size
        at = self._start

        if self.corner_radius == 0:
            childs.append(
                Rect(
                    start=at,
                    end=[at.x + size[0], at.y + size[1]],
                    fill=False,
                    layer=self.layer,
                    width=self.width,
                )
            )
        else:
            # fmt: off
            childs.append(Line(start=[at.x + cr, at.y],                     end=[at.x + size[0] - cr, at.y],             layer=self.layer, width=self.width))  # NOQA
            childs.append(Line(start=[at.x + size[0], at.y + cr],           end=[at.x + size[0], at.y + size[1] - cr],   layer=self.layer, width=self.width))  # NOQA
            childs.append(Line(start=[at.x + size[0] - cr, at.y + size[1]], end=[at.x + cr, at.y + size[1]],             layer=self.layer, width=self.width))  # NOQA
            childs.append(Line(start=[at.x, at.y + size[1] - cr],           end=[at.x, at.y + cr],                       layer=self.layer, width=self.width))  # NOQA

            childs.append(Arc(center=[at.x + cr, at.y + cr],                     start=[at.x, at.y + cr],                     angle=90,  layer=self.layer, width=self.width))  # NOQA
            childs.append(Arc(center=[at.x + size[0] - cr, at.y + cr],           start=[at.x + size[0] - cr, at.y],           angle=90,  layer=self.layer, width=self.width))  # NOQA
            childs.append(Arc(center=[at.x + cr, at.y + size[1] - cr],           start=[at.x, at.y + size[1] - cr],           angle=-90, layer=self.layer, width=self.width))  # NOQA
            childs.append(Arc(center=[at.x + size[0] - cr, at.y + size[1] - cr], start=[at.x + size[0], at.y + size[1] - cr], angle=90,  layer=self.layer, width=self.width))  # NOQA
            # fmt: on

        for c in childs:
            c._parent = self

        return childs
