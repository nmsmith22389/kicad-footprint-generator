#!/usr/bin/env python3

import os
import sys

from KicadModTree import *
from scripts.tools.global_config_files import global_config as GC
global_config = GC.DefaultGlobalConfig()

"""
vishay IHSM series inductors
http://www.vishay.com/docs/34018/ihsm3825.pdf
http://www.vishay.com/docs/34019/ihsm4825.pdf
http://www.vishay.com/docs/34020/ihsm5832.pdf
http://www.vishay.com/docs/34021/ihsm7832.pdf
"""

#sizes,shapes,etc]
#name, L, W, pad-w, pad-w, pad-gap, pad-h, datasheet
inductors = [
[3825, 11.18, 6.35, 4.6, 5.6, 5.08, "http://www.vishay.com/docs/34018/ihsm3825.pdf"],
[4825, 13.72, 6.35, 4.6, 5.6, 7.62, "http://www.vishay.com/docs/34019/ihsm4825.pdf"],
[5832, 16.26, 8.13, 6.6, 7.4, 8.763, "http://www.vishay.com/docs/34020/ihsm5832.pdf"],
[7382, 21.34, 8.13, 6.6, 7.4, 13.462, "http://www.vishay.com/docs/34021/ihsm7832.pdf"]
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

lib_name = "Inductor_SMD"
prefix = "L_"
part = "Vishay_IHSM-{pn}"
dims = "{l:0.1f}mmx{w:0.1f}mm"

desc = "Inductor, Vishay, {pn}, {datasheet}"
tags = "inductor vishay icsm smd"

for inductor in inductors:
    name,l,w,x,y,g,datasheet = inductor

    #pad center pos
    c = g/2 + x/2

    fp_name = prefix + part.format(pn=str(name))

    fp = Footprint(fp_name, FootprintType.SMD)

    description = desc.format(pn = part.format(pn=str(name)), datasheet=datasheet) + ", " + dims.format(l=l,w=w)

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
    fp.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + fp_name + global_config.model_3d_suffix))

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(fp)

    print(fp_name)
