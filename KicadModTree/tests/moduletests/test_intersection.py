import pytest
import copy
from KicadModTree import RectLine, Circle


def test_polygonLineIntersections():

    rect1 = RectLine(start=[-2, -2], end=[2, 2], layer=None)
    rect2 = copy.copy(rect1).rotate(45)

    # Rectangle-Rectangle
    lines = rect1.cut(rect2)
    circumfence = 0

    for line in lines:
        circumfence += (line.end_pos - line.start_pos).norm()
        assert rect1.isPointOnSelf(line.getMidPoint())
        assert not rect2.isPointOnSelf(line.getMidPoint())

    assert circumfence == pytest.approx(16)
    assert len(lines) == 12

    # Rectangle-Circle
    circle = Circle(center=(0, 0), radius=2.5)
    lines = rect1.cut(circle)
    circumfence = 0

    for line in lines:
        circumfence += (line.end_pos - line.start_pos).norm()
        assert rect1.isPointOnSelf(line.getMidPoint())
        assert not circle.isPointOnSelf(line.getMidPoint())

    assert circumfence == pytest.approx(16)
    assert len(lines) == 12

    # Circle-Rectangle
    arcs = circle.cut(rect1)
    angle = 0

    for arc in arcs:
        angle += arc.angle
        assert circle.isPointOnSelf(arc.getMidPoint())
        assert not rect1.isPointOnSelf(arc.getMidPoint())

    assert angle == pytest.approx(360)
    assert len(arcs) == 9  # the arc including 0 deg is split into two
