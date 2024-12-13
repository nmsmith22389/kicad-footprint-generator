from KicadModTree import Line, Node
from kilibs.geom import Vector2D


class Cross(Node):
    """
    Represents a simple cross, centred at a points.

    Crosses are drawn with a lot, and using text is fiddly because the
    KiCad fon't doesn't put the centre of "+" on the baseline. Also a real
    cross, positioned exactly, allows users to snap to the centrepoint.
    """

    def __init__(
        self,
        center: Vector2D,
        size: Vector2D | float,
        angle: float,
        layer: str,
        width: float,
    ):
        """
        :param center the center of the cross
        :param the size of the cross in each dimension (or both)
        :param the angle of the cross
        """
        super().__init__()

        if isinstance(size, Vector2D):
            self.size = size
        else:
            self.size = Vector2D(size, size)

        self.center = center
        self.angle = angle
        self.layer = layer
        self.width = width

        self._children = self._rebuild()

    def _rebuild(self) -> list[Node]:

        pts = [
            Vector2D(-self.size.x / 2, 0),
            Vector2D(self.size.x / 2, 0),
            Vector2D(0, -self.size.y / 2),
            Vector2D(0, self.size.y / 2),
        ]

        pts = [p.with_rotation(self.angle) + self.center for p in pts]

        line_params = {
            "layer": self.layer,
            "width": self.width,
        }

        return [
            Line(start=pts[0], end=pts[1], **line_params),
            Line(start=pts[2], end=pts[3], **line_params),
        ]

    def getVirtualChilds(self):
        return self._rebuild()

    def __repr__(self):
        return f"Cross(c={self.center}, size={self.size}, angle={self.angle})"
