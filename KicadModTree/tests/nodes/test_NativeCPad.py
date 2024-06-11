from KicadModTree.nodes import Pad, NativeCPad, Footprint, FootprintType
from KicadModTree.nodes.base.NativeCPad import CornerSelectionNative
from KicadModTree import Vector2D

from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest

# Basic pad test arguments
DEFAULT_FCU_KWARGS = {
    "number": "42",
    "at": Vector2D(0, 0),
    "size": Vector2D(1, 1),
    "shape": Pad.SHAPE_ROUNDRECT,
    "type": Pad.TYPE_SMT,
    "layers": ["F.Cu"],
}


class TestNativeCPadSerialisation(SerialisationTest):

    def setUp(self):
        super().setUp(__file__, 'data')

    def test_corner_selection(self):

        cs = CornerSelectionNative(chamfer_select=None)

        assert cs.isAnySelected() is False

        cs = CornerSelectionNative(chamfer_select=[CornerSelectionNative.TOP_LEFT])

        assert cs.isAnySelected() is True

        cs.clearAll()

        assert cs.isAnySelected() is False

    def test_basic_nativecpad(self):

        corner = CornerSelectionNative(chamfer_select=[CornerSelectionNative.BOTTOM_LEFT])

        pad = NativeCPad(chamfer_corners=corner, **DEFAULT_FCU_KWARGS)

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)
        self.assert_serialises_as(kicad_mod, 'nativecpad_basic.kicad_mod')
