from kilibs.geom import geometricLine, geometricCircle, geometricArc, Vector2D
import pytest


def vector_approx_equal(a: Vector2D | tuple, b: Vector2D | tuple, rel=1e-6):
    """
    Check if two vectors are approximately equal
    """

    if isinstance(a, tuple):
        a = Vector2D(a)

    if isinstance(b, tuple):
        b = Vector2D(b)

    return a.x == pytest.approx(b.x, rel=rel) and a.y == pytest.approx(b.y, rel=rel)


def seg_same(a: geometricLine, b: geometricLine, rel=1e-6):
    """
    Check if two line segments are the same, including direction
    """

    return vector_approx_equal(
        a.start_pos, b.start_pos, rel=rel
    ) and vector_approx_equal(a.end_pos, b.end_pos, rel=rel)


def seg_same_endpoints(a: geometricLine, b: geometricLine, rel=1e-6):
    """
    Check if two line segments have the same endpoints, in either order
    """

    same = seg_same(a, b, rel=rel)

    # Check if the lines are the same but in reverse
    if not same:
        same = vector_approx_equal(
            a.start_pos, b.end_pos, rel=rel
        ) and vector_approx_equal(a.end_pos, b.start_pos, rel=rel)

    return same


def same_center(a: geometricCircle | geometricArc, b: geometricCircle | geometricArc, rel=1e-6):
    """
    Check if two circles/arcs have the same center.
    """
    return vector_approx_equal(a.center_pos, b.center_pos, rel=rel)
