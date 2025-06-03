#!/usr/bin/env python3

import sys
import os

from KicadModTree import *
from scripts.tools.global_config_files import global_config as GC
global_config = GC.DefaultGlobalConfig()

#http://katalog.we-online.com/en/pbs/WE-MAPI]

#sizes,shapes,etc]
#name, L, W, pad-w, pad-gap, pad-h
inductors = [
[7050, 7.15, 7, 2, 3.3, 3.1],
[7070, 7.4, 7.2, 2.55, 2.5, 2.2],
[1050, 10.2, 7, 2, 6.35, 3.05],
[1070, 10.1, 7, 3.6, 4, 2.6],
[1078, 9.4, 6.2, 3.2, 4, 2.54],
[1052, 10.5, 10.3, 2.45, 5.8, 2.7],
[1190, 10.5, 11, 4, 4.2, 2.7],
[1240, 10, 11.8, 2.6, 6.8, 4.5],
[1350, 13.5, 13.3, 2.9, 8, 5.4],
[1390, 12.5, 13, 2.5, 10, 5]
]

output_dir = os.getcwd()

#if specified as an argument, extract the target directory for output footprints
if len(sys.argv) > 1:
    out_dir = sys.argv[1]

    if os.path.isabs(out_dir) and os.path.isdir(out_dir):
        output_dir = out_dir
    else:
        out_dir = os.path.join(os.getcwd(),out_dir)
        if os.path.isdir(out_dir):
            output_dir = out_dir

if output_dir and not output_dir.endswith(os.sep):
    output_dir += os.sep

prefix = "L_"
part = "Wuerth_HCM-{pn}"
dims = "{l:0.1f}mmx{w:0.1f}mm"

desc = "Inductor, Wuerth Elektronik, {pn}"
tags = "inductor wurth hcm smd"

for inductor in inductors:
    name,l,w,x,g,y = inductor

    #pad center pos
    c = g/2 + x/2

    fp_name = prefix + part.format(pn=str(name))

    fp = Footprint(fp_name, FootprintType.SMD)

    description = desc.format(pn = part.format(pn=str(name))) + ", " + dims.format(l=l,w=w)

    fp.setTags(tags)
    fp.setDescription(description)

    #add inductor courtyard
    cx = max(l/2, (c+x/2))
    cy = max(w/2, y/2)

    fp.append(RectLine(start=[-cx,-cy],end=[cx,cy],offset=0.35,width=0.05,layer="F.CrtYd"))

    # set general values
    fp.append(Property(name=Property.REFERENCE, text='REF**', at=[0,-cy - 1], layer='F.SilkS'))
    fp.append(Property(name=Property.VALUE, text=fp_name, at=[0,cy + 1.5], layer='F.Fab'))


    #calculate pad center
    #pad-width pw
    pw = x

    #add the component outline
    fp.append(RectLine(start=[-l/2,-w/2],end=[l/2,w/2],layer='F.Fab',width=0.1))

    layers = Pad.LAYERS_SMT

    #add pads
    fp.append(Pad(number=1,at=[-c,0],layers=layers,shape=Pad.SHAPE_RECT,type=Pad.TYPE_SMT,size=[x,y]))
    fp.append(Pad(number=2,at=[c,0],layers=layers,shape=Pad.SHAPE_RECT,type=Pad.TYPE_SMT,size=[x,y]))

    poly = [
        {'x': -l/2-0.1,'y': -y/2-0.3},
        {'x': -l/2-0.1,'y': -w/2-0.1},
        {'x': 0,'y': -w/2-0.1},
    ]

    fp.append(PolygonLine(shape=poly))
    fp.append(PolygonLine(shape=poly, x_mirror=0))
    fp.append(PolygonLine(shape=poly, y_mirror=0))
    fp.append(PolygonLine(shape=poly, x_mirror=0))

    #Add a model
    lib_name = "Inductor_SMD"
    fp.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + fp_name + global_config.model_3d_suffix))

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(fp)

    print(fp_name)
