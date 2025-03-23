from typing import Union

from KicadModTree import Node, Polygon
from kilibs.geom import Direction, Vector2D


class Pin1SilkscreenArrow(Node):

    pos: Vector2D
    angle: float
    size: float
    length: float
    layer: str
    line_width_mm: float

    def __init__(
        self,
        apex_position: Vector2D,
        angle: Union[float, Direction],
        size: float,
        length: float,
        layer: str,
        line_width_mm: float,
    ):
        """
        This is the generic constructor for a modern (2024-era) pin 1 silkscreen arrow.

               |<>|---length
        ------ +\
          |    | \
        size   |  +<--pos
          |    | /
        ------ +/

        :param pos: The position of the arrow
        :param angle: The angle of the arrow - this is the direction the arrow points in - 0 is rightwards
        :param size: size of the triangle (node to node, line width is not included)
        :param length: length of the triangle (node to node)
        :param layer: layer of the arrow
        :param line_width_mm: line width of the arrow (can be 0)
        """
        Node.__init__(self)

        pos = Vector2D(apex_position)

        if isinstance(angle, Direction):
            angle = angle.value

        arrow_pts = [
            pos,
            pos + [-length, size * 0.50],
            pos + [-length, -size * 0.50],
            pos
        ]

        self._poly = Polygon(nodes=arrow_pts, layer=layer, width=line_width_mm, fill=True)
        # Rotate the arrow backwards (so it points in the right direction)
        self._poly.rotate(angle=-angle, origin=pos)

    def getVirtualChilds(self):
        return [self._poly]


class Pin1SilkScreenArrow45Deg(Node):
    """
    Makea 45-degree filled triangle with H/V sides of equal length

    Size is between nodes, overall size will include 1*line_width overall

        + ---
       /|  |<-size   (this is a SE pointing arrow)
      +-+ ---

    :param size: size of the triangle
    :angle: angle of the arrow - this is the direction the arrow points in. This is usually NE/SE/SW/NW
    """

    def __init__(
        self, apex_position: Vector2D, angle: Union[float, Direction],
        size: float, layer: str, line_width_mm: float
    ):
        Node.__init__(self)

        arrow_pts = [
            apex_position,
            apex_position + [-size, 0],
            apex_position + [0, -size],
            apex_position,
        ]

        self._poly = Polygon(
            nodes=arrow_pts, layer=layer, width=line_width_mm, fill=True
        )

        if isinstance(angle, Direction):
            angle = angle.value

        # SE (315) is the default
        angle = angle - Direction.SOUTHEAST.value

        if angle != 0:
            self._poly.rotate(-angle, origin=apex_position)

    def getVirtualChilds(self):
        return [self._poly]
