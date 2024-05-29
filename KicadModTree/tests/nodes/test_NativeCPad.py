from KicadModTree.nodes import Pad, NativeCPad, Footprint, FootprintType
from KicadModTree.nodes.base.NativeCPad import CornerSelectionNative
from KicadModTree import Vector2D

from node_test_utils import assert_serialises_as

# Trick pycodestyle into not assuming tab indents
if False:
    pass

RESULT_Basic = """(footprint "padtest"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(pad "42" smd roundrect
		(at 0 0)
		(size 1 1)
		(layers "F.Cu")
		(roundrect_rratio 0.25)
		(chamfer_ratio 0.25)
		(chamfer bottom_left)
	)
)"""  # NOQA: W191


# Basic pad test arguments
DEFAULT_FCU_KWARGS = {
    "number": "42",
    "at": Vector2D(0, 0),
    "size": Vector2D(1, 1),
    "shape": Pad.SHAPE_ROUNDRECT,
    "type": Pad.TYPE_SMT,
    "layers": ["F.Cu"],
}


def test_corner_selection():

    cs = CornerSelectionNative(chamfer_select=None)

    assert cs.isAnySelected() is False

    cs = CornerSelectionNative(chamfer_select=[CornerSelectionNative.TOP_LEFT])

    assert cs.isAnySelected() is True

    cs.clearAll()

    assert cs.isAnySelected() is False


def test_basic_nativecpad():

    corner = CornerSelectionNative(chamfer_select=[CornerSelectionNative.BOTTOM_LEFT])

    pad = NativeCPad(chamfer_corners=corner, **DEFAULT_FCU_KWARGS)

    kicad_mod = Footprint("padtest", FootprintType.SMD)
    kicad_mod.append(pad)
    assert_serialises_as(kicad_mod, RESULT_Basic, dump=True)
