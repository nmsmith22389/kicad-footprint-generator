# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

import unittest

from KicadModTree import *

# Trick pycodestyle into not assuming tab indents
if False:
    pass

RESULT_MINIMUM = """(footprint "test"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(attr smd)
)"""  # NOQA: W191

RESULT_BASIC_TAGS = """(footprint "test"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(descr "A example footprint")
	(tags "example example2 example3 example4")
	(attr smd)
)"""  # NOQA: W191

RESULT_SIMPLE_FOOTPRINT = """(footprint "test"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(descr "A example footprint")
	(tags "example")
	(property "Reference" "REF**"
		(at 0 -3 0)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Value" "test"
		(at 1.5 3 0)
		(layer "F.Fab")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(attr smd)
	(fp_line
		(start -2 -2)
		(end -2 2)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start -2 2)
		(end 5 2)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5 2)
		(end 5 -2)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 5 -2)
		(end -2 -2)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start -2.25 -2.25)
		(end -2.25 2.25)
		(stroke
			(width 0.05)
			(type solid)
		)
		(layer "F.CrtYd")
	)
	(fp_line
		(start -2.25 2.25)
		(end 5.25 2.25)
		(stroke
			(width 0.05)
			(type solid)
		)
		(layer "F.CrtYd")
	)
	(fp_line
		(start 5.25 2.25)
		(end 5.25 -2.25)
		(stroke
			(width 0.05)
			(type solid)
		)
		(layer "F.CrtYd")
	)
	(fp_line
		(start 5.25 -2.25)
		(end -2.25 -2.25)
		(stroke
			(width 0.05)
			(type solid)
		)
		(layer "F.CrtYd")
	)
	(pad "1" thru_hole rect
		(at 0 0)
		(size 2 2)
		(drill 1.2)
		(layers "*.Cu" "*.Mask")
	)
	(pad "2" thru_hole circle
		(at 3 0)
		(size 2 2)
		(drill 1.2)
		(layers "*.Cu" "*.Mask")
	)
	(model "example.3dshapes/example_footprint.wrl"
		(offset
			(xyz 0 0 0)
		)
		(scale
			(xyz 1 1 1)
		)
		(rotate
			(xyz 0 0 0)
		)
	)
)"""  # NOQA: W191

RESULT_BASIC_NODES = """(footprint "test"
	(version 20240108)
	(generator "kicad-footprint-generator")
	(layer "F.Cu")
	(property "Reference" "REF**"
		(at 0 -3 0)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Value" "footprint name"
		(at 0 3 0)
		(layer "F.Fab")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(attr smd)
	(fp_arc
		(start -1 0)
		(mid 0 -1)
		(end 1 0)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_circle
		(center 0 0)
		(end 1.5 0)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(fp_line
		(start 1 0)
		(end -1 0)
		(stroke
			(width 0.12)
			(type solid)
		)
		(layer "F.SilkS")
	)
	(pad "1" thru_hole rect
		(at 0 0)
		(size 2 2)
		(drill 1.2)
		(layers "*.Cu" "*.Mask")
	)
	(model "example.3dshapes/example_footprint.wrl"
		(offset
			(xyz 0 0 0)
		)
		(scale
			(xyz 1 1 1)
		)
		(rotate
			(xyz 0 0 0)
		)
	)
)"""  # NOQA: W191


class SimpleFootprintTests(unittest.TestCase):

    def testMinimum(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        file_handler = KicadFileHandler(kicad_mod)
        serialized = file_handler.serialize(timestamp=0)
        # print(serialized)
        self.assertEqual(serialized, RESULT_MINIMUM)

    def testBasicTags(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        kicad_mod.setDescription("A example footprint")
        kicad_mod.tags = "example"
        kicad_mod.tags += ["example2", "example3"]
        kicad_mod.tags.append("example4")

        file_handler = KicadFileHandler(kicad_mod)
        serialized = file_handler.serialize(timestamp=0)
        # print(serialized)
        self.assertEqual(serialized, RESULT_BASIC_TAGS)

    def testSampleFootprint(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        kicad_mod.setDescription("A example footprint")
        kicad_mod.tags = "example"

        kicad_mod.append(Text(type='reference', text='REF**', at=[0, -3], layer='F.SilkS'))
        kicad_mod.append(Text(type='value', text="test", at=[1.5, 3], layer='F.Fab'))
        kicad_mod.append(RectLine(start=[-2, -2], end=[5, 2], layer='F.SilkS'))
        kicad_mod.append(RectLine(start=[-2.25, -2.25], end=[5.25, 2.25], layer='F.CrtYd'))
        kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                             at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number=2, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                             at=[3, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT))
        kicad_mod.append(Model(filename="example.3dshapes/example_footprint.wrl",
                               at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

        file_handler = KicadFileHandler(kicad_mod)
        serialized = file_handler.serialize(timestamp=0)
        # print(serialized)
        self.assertEqual(serialized, RESULT_SIMPLE_FOOTPRINT)

    def testBasicNodes(self):
        kicad_mod = Footprint("test", FootprintType.SMD)

        kicad_mod.append(Text(type='reference', text='REF**', at=[0, -3], layer='F.SilkS'))
        kicad_mod.append(Text(type='value', text="footprint name", at=[0, 3], layer='F.Fab'))

        kicad_mod.append(Arc(center=[0, 0], start=[-1, 0], angle=180, layer='F.SilkS'))
        kicad_mod.append(Circle(center=[0, 0], radius=1.5, layer='F.SilkS'))
        kicad_mod.append(Line(start=[1, 0], end=[-1, 0], layer='F.SilkS'))
        kicad_mod.append(Model(filename="example.3dshapes/example_footprint.wrl",
                               at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))
        kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
                             at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT))

        file_handler = KicadFileHandler(kicad_mod)
        serialized = file_handler.serialize(timestamp=0)
        # print(serialized)
        self.assertEqual(serialized, RESULT_BASIC_NODES)
