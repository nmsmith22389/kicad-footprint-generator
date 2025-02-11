from kilibs.geom import Vector2D
from KicadModTree import Line, RectLine, Circle


def test_bounding_box():
    # for line
    p1 = Vector2D(3, 1)
    p2 = Vector2D(-2, 4)
    line = Line(start=p1, end=p2, layer=None)
    bbox = line.calculateBoundingBox()
    assert bbox["min"].x == min(p1.x, p2.x)
    assert bbox["min"].y == min(p1.y, p2.y)
    assert bbox["max"].x == max(p1.x, p2.x)
    assert bbox["max"].y == max(p1.y, p2.y)

    rect = RectLine(start=(p1.x, p2.y), end=(p2.x, p1.y), layer=None)
    bbox = rect.calculateBoundingBox()
    assert bbox["min"].x == min(p1.x, p2.x)
    assert bbox["min"].y == min(p1.y, p2.y)
    assert bbox["max"].x == max(p1.x, p2.x)
    assert bbox["max"].y == max(p1.y, p2.y)

    circle = Circle(center=(3, 1), radius=2)
    bbox = circle.calculateBoundingBox()
    assert bbox["min"].x == 1
    assert bbox["min"].y == -1
    assert bbox["max"].x == 5
    assert bbox["max"].y == 3
