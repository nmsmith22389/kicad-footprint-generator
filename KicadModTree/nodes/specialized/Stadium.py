from KicadModTree import Arc, Line, Node
from kilibs.geom import (
    Rectangle,
    Vector2D,
    geometricArc,
    geometricLine,
    geometricPrimitive,
)


class Stadium(Node):
    """
    Draws a stadium shape, which is a rectangle with semi-circular ends.
    Sometimes called a racetrack shape, or oblong (that's also
    the name of a non-square rectangle), or obround, or oval.

    Stadium is about the only unambiguous name for this shape!
    """

    def __init__(
        self,
        center_1: Vector2D,
        center_2: Vector2D,
        radius: float,
        layer: str,
        width: float,
    ):
        """
        :param center_1: The center of the first semi-circle
        :param center_2: The center of the second semi-circle
        :param radius: The radius of the semi-circles
        :param layer: The layer to draw on
        :param width: The width of the lines
        """
        super().__init__()

        self.center_1 = Vector2D(center_1)
        self.center_2 = Vector2D(center_2)
        self.radius = radius
        self.layer = layer
        self.width = width

        self._children = self._rebuild()

    def by_inscription(rect: Rectangle, layer: str, width: float) -> "Stadium":
        """
        Build a stadium inscribed into the given rectangle. The rounded ends will
        be at the short edge of the rectangle.
        """

        if rect.size.x > rect.size.y:
            radius = rect.size.y / 2
            c1 = Vector2D(rect.left + radius, rect.center.y)
            c2 = Vector2D(rect.right - radius, rect.center.y)
        else:
            radius = rect.size.x / 2
            c1 = Vector2D(rect.center.x, rect.top + radius)
            c2 = Vector2D(rect.center.x, rect.bottom - radius)
        return Stadium(
            center_1=c1, center_2=c2, radius=radius, width=width, layer=layer
        )

    def get_primitives(self):
        """
        Yield the geometric primitives that make up this stadium.
        """

        # centre 1 to centre 2 vector
        c_vec = self.center_2 - self.center_1

        perp_vec = c_vec.orthogonal().resize(self.radius)

        # Vector from centre 2 to arc mid point
        c_to_arc_mid = c_vec.resize(self.radius)

        yield geometricArc(
            start=self.center_1 + perp_vec,
            end=self.center_1 - perp_vec,
            midpoint=self.center_1 - c_to_arc_mid,
        )

        yield geometricArc(
            start=self.center_2 + perp_vec,
            end=self.center_2 - perp_vec,
            midpoint=self.center_2 + c_to_arc_mid,
        )

        yield geometricLine(
            start=self.center_1 + perp_vec,
            end=self.center_2 + perp_vec,
        )

        yield geometricLine(
            start=self.center_1 - perp_vec,
            end=self.center_2 - perp_vec,
        )

    def _rebuild(self) -> list[Node]:

        nodes = []

        for primitive in self.get_primitives():
            if isinstance(primitive, geometricArc):
                nodes.append(
                    Arc(geometry=primitive, layer=self.layer, width=self.width)
                )
            elif isinstance(primitive, geometricLine):
                nodes.append(
                    Line(geometry=primitive, layer=self.layer, width=self.width)
                )

        return nodes

    def getVirtualChilds(self):
        return self._children

    def __repr__(self):
        return f"Stadium(c1={self.center_1}, c2={self.center_2}, r={self.radius}, {self.layer}, {self.width})"

    def __str__(self):
        return repr(self)
