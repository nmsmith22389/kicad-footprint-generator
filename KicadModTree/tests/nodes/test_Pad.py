from KicadModTree.nodes import Pad, Footprint, FootprintType
from KicadModTree import Vector2D

from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest

# Basic pad test arguments
DEFAULT_FCU_KWARGS = {
    "number": "42",
    "at": Vector2D(0, 0),
    "size": Vector2D(1, 1),
    "shape": Pad.SHAPE_RECT,
    "type": Pad.TYPE_SMT,
    "layers": ["F.Cu"],
}


class TestPadSerialisaion(SerialisationTest):

    def setUp(self):
        super().setUp(__file__, 'data')

    def test_basic(self):

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
        self.assert_serialises_as(kicad_mod, 'pad_basic.kicad_mod')

    def test_fab_property(self):

        pad = Pad(
            **DEFAULT_FCU_KWARGS,
            fab_property=Pad.FabProperty.HEATSINK,
        )

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)
        self.assert_serialises_as(kicad_mod, 'pad_heatsink.kicad_mod')

    def test_zone_connection(self):

        pad = Pad(
            **DEFAULT_FCU_KWARGS,
            zone_connection=Pad.ZoneConnection.SOLID,
        )

        assert pad._zone_connection == Pad.ZoneConnection.SOLID

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)
        self.assert_serialises_as(kicad_mod, 'pad_zone_connection.kicad_mod')
