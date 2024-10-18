
from KicadModTree.util.corner_selection import CornerSelection


def test_corner_selection():

    cs = CornerSelection(corner_selection=None)

    assert cs.isAnySelected() is False

    cs = CornerSelection(corner_selection={CornerSelection.TOP_LEFT: True})

    assert cs.isAnySelected() is True

    cs.clearAll()

    assert cs.isAnySelected() is False
