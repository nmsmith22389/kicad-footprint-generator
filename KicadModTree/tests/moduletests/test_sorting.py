from KicadModTree import Footprint, Line, FootprintType, Pad
from kilibs.geom import Vector2D


from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


class TestSmallValueSerialisation(SerialisationTest):

    def testSortSmallValues(self):
        """
        Test that the small epsilon values get sorted correctly.

        Anything that rounds to the same nm should have the same sorting order.
        """
        kicad_mod = Footprint("test_sort_small_values", FootprintType.SMD)

        center = Vector2D(0, 0)
        kicad_mod.append(Line(start=Vector2D(1e-15, 1), end=center))
        kicad_mod.append(Line(start=Vector2D(-1e-15, 2), end=center))

        self.assert_serialises_as(kicad_mod, "test_sort_small_values.kicad_mod")

    def testSortPadNumbers(self):
        """
        Test that pad numbers gets sorted correctly
        """
        kicad_mod = Footprint("test_sort_pad_numbers", FootprintType.SMD)

        DEFAULT_PAD_KWARGS = {
            "at": Vector2D(0, 0),
            "size": Vector2D(1, 1),
            "shape": Pad.SHAPE_RECT,
            "type": Pad.TYPE_SMT,
            "layers": ["F.Cu"],
        }

        center = Vector2D(0, 0)

        kicad_mod.append(Pad(number="1", **DEFAULT_PAD_KWARGS))
        kicad_mod.append(Pad(number="a1", **DEFAULT_PAD_KWARGS))
        kicad_mod.append(Pad(number="a10", **DEFAULT_PAD_KWARGS))
        kicad_mod.append(Pad(number="a2", **DEFAULT_PAD_KWARGS))
        kicad_mod.append(Pad(number="", **DEFAULT_PAD_KWARGS))
        kicad_mod.append(Pad(number="2", **DEFAULT_PAD_KWARGS))

        self.assert_serialises_as(kicad_mod, "test_sort_pad_numbers.kicad_mod")
