import unittest
from KicadModTree import *
from KicadModTree.tests.utility import *


def gen_footprint(offsets: list):
    kicad_mod = Footprint("test", FootprintType.SMD)

    # add a shape on Silk and Fab
    poly = PolygonLine(
        nodes=[
            # left contour
            (-3, 2), (-5, -2),
            # top contour
            (-5, -3), (-4, -3), (-4, -2.5), (4, -2.5), (4, -3), (5, -3),
            # right contour
            (5, -2.5), (6, -2), (6, -1.8), (5, -2),     # 1st ear
            (5, 2), (6, 2), (5, 2.05), (5, 3),
            # bottom contour
            (5, 3), (-4, 3), (-5, 2),
        ], layer="F.Fab", width=0.1)
    kicad_mod.append(poly)
    for offset in offsets:
        kicad_mod.append(poly.duplicate(offset=offset, layer="F.SilkS", width=0.1))

    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -5], layer='F.SilkS'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[0, -5], layer='F.Fab'))
    kicad_mod.append(Property(name=Property.VALUE, text="test", at=[0, 5], layer='F.Fab'))

    return kicad_mod


class PolygonOffsetTests(unittest.TestCase):

    def test_offset(self):
        kicad_mod = gen_footprint(offsets=[0.2, 0.4, 0.6])
        # save result to kicad_mod file
        file_handler = KicadFileHandler(kicad_mod)
        with open(regressionFilename(".kicad_mod"), "w") as file:
            file.write(file_handler.serialize())
        # create render-tree
        mod_tree = kicad_mod.getCompleteRenderTree()
        # compare with regression file
        self.assertTrue(compareWithRegressionFile(mod_tree, tol=1e-7))
