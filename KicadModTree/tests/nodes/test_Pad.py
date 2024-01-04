from KicadModTree.nodes import Pad, Footprint, FootprintType
from KicadModTree import Vector2D

from node_test_utils import assert_serialises_as

RESULT_Basic = """(footprint padtest (version 20221018) (generator kicad-footprint-generator)
  (layer F.Cu)
  (attr smd)
  (pad 42 smd roundrect (at 0 0) (size 1 1) (property pad_prop_heatsink) (layers F.Cu) (roundrect_rratio 0.25))
)"""


def test_basic():

    pad = Pad(
        number="42", at=Vector2D(0, 0), size=Vector2D(1, 1),
        shape=Pad.SHAPE_ROUNDRECT, type=Pad.TYPE_SMT,
        layers=["F.Cu"],
        fab_property=Pad.FabProperty.HEATSINK,
    )

    assert pad.number == "42"
    assert pad.at == Vector2D(0, 0)
    assert pad.size == Vector2D(1, 1)
    assert pad.shape == Pad.SHAPE_ROUNDRECT
    assert pad.type == Pad.TYPE_SMT
    assert pad.layers == ["F.Cu"]
    assert pad.fab_property == Pad.FabProperty.HEATSINK

    kicad_mod = Footprint("padtest", FootprintType.SMD)
    kicad_mod.append(pad)
    assert_serialises_as(kicad_mod, RESULT_Basic)
