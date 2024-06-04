#!/usr/bin/env python

import sys
import os

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))

# load scripts
sys.path.append(os.path.join(sys.path[0], ".."))

from KicadModTree import *
import math

# epsilon for float comparisons
eps = 1e-4

def fref_size(args):
	# four letters should fit inside the outline,
	# outline is drawn with 0.1 thickness
	w = (args["size"][0] - 0.1) / 4
	if w > 1.0:
		w = 1.0
	elif w < 0.5:
		print("ERROR: Footprint too small, can't fit REF on F.Fab")
		w = 0.5
	return [w, w], w*0.15

def ceiltogrid(x, grid):
	return math.ceil(x / grid) * grid

def inductor(args):
	footprint_name = args["name"]
	pad_dist = args["pad_step"] - args["pad_size"][0]

	# Append dimension specification to the description
	desc = "%s, %.1fx%.1fmm (%s)" % (args["description"], args["size"][0], args["size"][1], args["datasheet"])

	# init kicad footprint
	kicad_mod = Footprint(footprint_name)
	kicad_mod.setDescription(desc)
	kicad_mod.setTags(args["tags"])
	kicad_mod.setAttribute("smd")

	# draw outline on F.Fab, width is 0.10 as per F5.2 (1)
	x = args["size"][0] / 2
	y = args["size"][1] / 2
	kicad_mod.append(RectLine(start=[-x, -y], end=[x, y], layer='F.Fab', width=0.10))

	# draw outline on F.SilkS, width is 0.12 as per F5.1 (2)
	# position is 0.11 mm outwards of the outline on F.Fab
	silkx = x + 0.11
	silky = y + 0.11
	if (pad_dist / 2 + args["pad_size"][0]) - args["size"][0] / 2 > eps:
		# outline will intersect with the pad, clearance is recommended
		# to be 0.2 mm as per F3.1 (3a)
		lowy = args["pad_size"][1] / 2 + 0.2
		for p in [-1, 1]:
			kicad_mod.append(Line(start=[-silkx, p*lowy], end=[-silkx, p*silky],
					layer="F.SilkS", width=0.12))
			kicad_mod.append(Line(start=[-silkx, p*silky], end=[silkx, p*silky],
					layer="F.SilkS", width=0.12))
			kicad_mod.append(Line(start=[silkx, p*silky], end=[silkx, p*lowy],
					layer="F.SilkS", width=0.12))
	else:
		# outline can't intersect with the pad, just draw a rectangle:
		kicad_mod.append(RectLine(start=[-silkx, -silky], end=[silkx, silky],
				layer="F.SilkS", width=0.12))
	
	# inductors are not polarized, so we don't need a pin-1 designator

	# create courtyard, width is 0.05mm as per F5.3 (1)
	# clearance is 0.5 mm to avoid EMI by the inductor
	cx = ceiltogrid(x + 0.5, 0.01)
	cy = ceiltogrid(y + 0.5, 0.01)
	kicad_mod.append(RectLine(start=[-cx,-cy], end=[cx,cy],
				layer='F.CrtYd', width=0.05))

	# write general values outside of courtyard
	ly = ceiltogrid(cy + 0.5, 0.5)
	kicad_mod.append(Text(type="reference", text="REF**", at=[0, -ly], layer="F.SilkS"))
	kicad_mod.append(Text(type="value", text=footprint_name, at=[0, ly], layer="F.Fab"))

	# add another REF indicator on F.Fab in the center
	size, thickness = fref_size(args)
	kicad_mod.append(Text(type="user", text="${REFERENCE}", at=[0, 0], layer="F.Fab",
				size=size, thickness=thickness))

	# create pads
	px = pad_dist / 2 + args["pad_size"][0] / 2
	kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
				layers = Pad.LAYERS_SMT, at=[-px, 0], size=args["pad_size"]))
	kicad_mod.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
				layers = Pad.LAYERS_SMT, at=[px, 0], size=args["pad_size"]))

	# specify 3d model path
	kicad_mod.append(Model(filename="${KICAD6_3DMODEL_DIR}/Inductor_SMD.3dshapes/" + 
				footprint_name + ".wrl"))
	
	# write file
	file_handler = KicadFileHandler(kicad_mod)
	file_handler.writeFile(footprint_name + ".kicad_mod")
	
if __name__ == '__main__':
	parser = ModArgparser(inductor)
	# the root node of .yml files is parsed as name
	parser.add_parameter("name", type=str, required=True)
	parser.add_parameter("description", type=str, required=True)
	parser.add_parameter("datasheet", type=str, required=True)
	parser.add_parameter("tags", type=str, required=True)
	parser.add_parameter("size", type=list, required=True)
	parser.add_parameter("pad_size", type=list, required=True)
	parser.add_parameter("pad_step", type=float, required=True)

	parser.run()
