import pytest

from KicadModTree import Rect, Vector2D
from KicadModTree.tests.test_utils import custom_assertions as CA


@pytest.mark.parametrize(
    "start, end, layer, width",
    [
        ((0, 0), (1, 1), "F.SilkS", 0.1),
        ((1, 1), (0, 0), "B.SilkS", 0.2),
    ],
)
def test_Rect(start, end, layer, width):

    s = Vector2D(start)
    e = Vector2D(end)

    r = Rect(start=s, end=e, layer=layer, width=width)

    # Check that the properties are set correctly
    assert r.start_pos == s
    assert r.end_pos == e
    assert r.layer == layer
    assert r.width == width

    # Flatten the object and check the output
    #
    # Rect is a base object, so it should flatten to itself
    serialised = r.serialize()

    rects = CA.assert_contains_n_of_type(serialised, 1, Rect)
    assert rects[0] == r
