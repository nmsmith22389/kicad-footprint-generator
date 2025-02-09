import unittest
import math
from KicadModTree import Footprint, Line, FootprintType
from KicadModTree.util import geometric_util as geo
from kilibs.geom import Vector2D

from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


class SmallValueSerialisation(SerialisationTest):

    def setUp(self):
        super().setUp(__file__, 'results')

    def testSortSmallValues(self):
        """
        Test that the small epsilon values get sorted correctly.

        Anything that rounds to the same nm should have the same sorting order.
        """
        kicad_mod = Footprint("test_sort_small_values", FootprintType.SMD)

        center = Vector2D(0, 0)
        kicad_mod.append(
            Line(start=Vector2D(1e-15, 1), end=center))
        kicad_mod.append(
            Line(start=Vector2D(-1e-15, 2), end=center))

        self.assert_serialises_as(kicad_mod, 'test_sort_small_values.kicad_mod')
