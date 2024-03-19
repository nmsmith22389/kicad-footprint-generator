from KicadModTree.nodes import Pad, Footprint, FootprintType
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
	(pad "42" smd rect
		(at 0 0)
		(size 1 1)
		(layers "F.Cu")
	)
)"""  # NOQA: W191


RESULT_Heatsink = """(footprint "padtest"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(pad "42" smd rect
		(at 0 0)
		(size 1 1)
		(property pad_prop_heatsink)
		(layers "F.Cu")
	)
)"""  # NOQA: W191


RESULT_ZoneConnection = """(footprint "padtest"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
	(pad "42" smd rect
		(at 0 0)
		(size 1 1)
		(layers "F.Cu")
		(zone_connect 2)
	)
)"""  # NOQA: W191


# Basic pad test arguments
DEFAULT_FCU_KWARGS = {
    "number": "42",
    "at": Vector2D(0, 0),
    "size": Vector2D(1, 1),
    "shape": Pad.SHAPE_RECT,
    "type": Pad.TYPE_SMT,
    "layers": ["F.Cu"],
}


def test_basic():

    pad = Pad(**DEFAULT_FCU_KWARGS)

    assert pad.number == "42"
    assert pad.at == Vector2D(0, 0)
    assert pad.size == Vector2D(1, 1)
    assert pad.shape == Pad.SHAPE_RECT
    assert pad.type == Pad.TYPE_SMT
    assert pad.layers == ["F.Cu"]

    # Check defaults
    assert pad.fab_property is None
    assert pad.zone_connection == Pad.ZoneConnection.INHERIT_FROM_FOOTPRINT

    kicad_mod = Footprint("padtest", FootprintType.SMD)
    kicad_mod.append(pad)
    assert_serialises_as(kicad_mod, RESULT_Basic)


def test_fab_property():

    pad = Pad(
        **DEFAULT_FCU_KWARGS,
        fab_property=Pad.FabProperty.HEATSINK,
    )

    kicad_mod = Footprint("padtest", FootprintType.SMD)
    kicad_mod.append(pad)
    assert_serialises_as(kicad_mod, RESULT_Heatsink)


def test_zone_connection():

    pad = Pad(
        **DEFAULT_FCU_KWARGS,
        zone_connection=Pad.ZoneConnection.SOLID,
    )

    assert pad._zone_connection == Pad.ZoneConnection.SOLID

    kicad_mod = Footprint("padtest", FootprintType.SMD)
    kicad_mod.append(pad)
    assert_serialises_as(kicad_mod, RESULT_ZoneConnection, dump=True)
