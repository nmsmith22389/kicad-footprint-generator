#!/usr/bin/env python

import sys
import os
import math

# ensure that the kicad-footprint-generator directory is available
#sys.path.append(os.environ.get('KIFOOTPRINTGENERATOR'))  # enable package import from parent directory
sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","..")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path

from KicadModTree import *  # NOQA
from footprint_scripts_terminal_blocks import *


#
#               barrier_width   barrier_xoffset
#                       ◄──►     ◄───────►

#                       ┌──┬────────────┬──┬─────────────┬──┬─────────────┬──┐ ▲
#                       │  │            │  │             │  │             │  │ │
#                       │  │            │  │             │  │             │  │ │
#                       │  │            │  │             │  │             │  │ │
#                       │  │    Pad     │  │     Pad     │  │     Pad     │  │ │
#                       │  │            │  │             │  │             │  │ │package_height
#                       │  │    OOO     │  │     OOO     │  │     OOO     │  │ │
#                     ▲ │  │   OOOOO    │  │    OOOOO    │  │    OOOOO    │  │ │
#                     │ │  │    OOO     │  │     OOO     │  │     OOO     │  │ │
# leftbottom_offset[1]│ │  │            │  │             │  │             │  │ │
#                     │ │  │            │  │             │  │             │  │ │
#                     ▼ └──┴────────────┴──┴─────────────┴──┴─────────────┴──┘ ▼
#                                                         rm
#                        ◄───────►                ◄────────────────►
#             leftbottom_offset[0]
#
def makeBarrierTerminalBlock(footprint_name, pins, rm, package_height, leftbottom_offset, ddrill, pad, 
                             barrier_xoffset=0, barrier_width=0, 
                             fabref_offset=[0,0],
                             stackable=False,
                             tags_additional=[], lib_name="${{KICAD7_3DMODEL_DIR}}/Connectors_Terminal_Blocks", 
                             classname="Connectors_Terminal_Blocks", classname_description="terminal block", 
                             webpage="", script_generated_note=""):

    package_size=[2*leftbottom_offset[0]+(pins-1)*rm, package_height];
    if len(leftbottom_offset)==3:
        package_size=[leftbottom_offset[0]+leftbottom_offset[2]+(pins-1)*rm, package_height];

    h_fab = package_size[1]
    w_fab = package_size[0]
    l_fab = -leftbottom_offset[0]
    t_fab = -(h_fab-leftbottom_offset[1])

    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset

    h_crt = h_fab + 2 * crt_offset
    w_crt = w_fab + (0 if stackable else 2 * crt_offset)
    l_crt = l_fab - (0 if stackable else crt_offset)
    t_crt = t_fab - crt_offset


    text_size = w_fab*0.6
    fab_text_size_max = 1.0
    if text_size < fab_text_size_min:
        text_size = fab_text_size_min
    elif text_size > fab_text_size_max:
        text_size = fab_text_size_max
    text_size = round(text_size, 2)
    text_size = [text_size,text_size]
    text_t = text_size[0] * 0.15


    description = f"{classname_description}, {pins:d} pins, pitch {rm:.3g}mm, size {package_size[0]:.3g}x{package_size[1]:.3g}mm^2, drill diameter {ddrill:.3g}mm, pad diameter {max(pad):.3g}mm, see {webpage}"
    tags = f"THT pitch {rm:.3g}mm size {package_size[0]:.3g}x{package_size[1]:.3g}mm^2 drill {ddrill:.3g}mm pad {max(pad):.3g}mm"\

    if len(script_generated_note)>0:
        description=description+", "+script_generated_note

    if (len(tags_additional) > 0):
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags = tags + " " + t

    print(footprint_name)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription(description)
    kicad_mod.setTags(tags)

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset=[0,0]
    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(Text(type='reference', text='REF**', at=[l_fab+w_fab/2, t_slk - txt_offset], layer='F.SilkS'))
    if (type(fabref_offset) in (tuple, list)):
        kicad_modg.append(Text(type='user', text='${REFERENCE}', at=[l_fab+w_fab/2+fabref_offset[0], t_fab+h_fab/2+fabref_offset[1]], layer='F.Fab', size=text_size ,thickness=text_t))
    else:
        kicad_modg.append(Text(type='user', text='${REFERENCE}', at=[l_fab+w_fab/2,  t_slk - txt_offset], layer='F.Fab', size=text_size ,thickness=text_t))
    kicad_modg.append(Text(type='value', text=footprint_name, at=[l_fab+w_fab/2, t_slk + h_slk + txt_offset], layer='F.Fab'))

    # create pads
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_RECT
    pad_shapeother = Pad.SHAPE_CIRCLE
    if pad[0] != pad[1]:
        pad_shapeother = Pad.SHAPE_OVAL

    pad_layers = Pad.LAYERS_THT
    keepouts=[];

    for p in range(1, pins + 1):
        if p == 1:
            kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[x1, y1], size=pad, drill=ddrill, layers=pad_layers))
            keepouts=keepouts+addKeepoutRect(x1, y1, pad[0]+8*slk_offset, pad[1]+8*slk_offset)
        else:
            kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shapeother, at=[x1, y1], size=pad, drill=ddrill, layers=pad_layers))
            if pad[0]!=pad[1]:
                keepouts=keepouts+addKeepoutRect(x1, y1, pad[0]+8*slk_offset, pad[1]+8*slk_offset)
            else:
                keepouts=keepouts+addKeepoutRound(x1, y1, pad[0]+8*slk_offset, pad[0]+8*slk_offset)

        x1=x1+rm

    # create Body
    chamfer = min(h_fab/4, 2)
    bevelRectBL(kicad_modg,  [l_fab,t_fab], [w_fab,h_fab], 'F.Fab', lw_fab, bevel_size=chamfer)
    addRectWithKeepout(kicad_modg, l_slk, t_slk, w_slk, h_slk, layer='F.SilkS', width=lw_slk, keepouts=keepouts)

    #  Leftmost barrier
    addRectWith(kicad_modg, -barrier_xoffset - barrier_width/2, -package_height/2, barrier_width, package_height, layer='F.SilkS', width=lw_slk)

    # Barriers between pins
    if barrier_width > 0:
        for p in range(1, pins+1):
            addRectWith(kicad_modg, (p-1)*rm + barrier_xoffset - barrier_width/2, -package_height/2, barrier_width, package_height, layer='F.SilkS', width=lw_slk)

    # create SILKSCREEN-pin1-marker
    kicad_modg.append(Line(start=[l_slk-2*lw_slk, t_slk + h_slk-chamfer], end=[l_slk-2*lw_slk, t_slk + h_slk+2*lw_slk], layer='F.SilkS', width=lw_slk))
    kicad_modg.append(Line(start=[l_slk-2*lw_slk, t_slk + h_slk+2*lw_slk], end=[l_slk-2*lw_slk+chamfer, t_slk + h_slk+2*lw_slk], layer='F.SilkS', width=lw_slk))

    # create courtyard
    kicad_mod.append(RectLine(start=[roundCrt(l_crt + offset[0]), roundCrt(t_crt + offset[1])],
                              end=[roundCrt(l_crt + offset[0] + w_crt), roundCrt(t_crt + offset[1] + h_crt)],
                              layer='F.CrtYd', width=lw_crt))

    # add model
    kicad_modg.append(
        Model(filename=lib_name + ".3dshapes/" + footprint_name + ".wrl", at=[0,0,0], scale=[1,1,1], rotate=[0,0,0]))

    debug_draw_keepouts(kicad_modg,keepouts)

    # write file
    if "/" in lib_name:
        fp_lib_name = lib_name.split('/')[-1]
    elif "\\" in lib_name:
        fp_lib_name = lib_name.split('\\')[-1]

    output_dir = fp_lib_name + '.pretty' + os.sep
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(output_dir + footprint_name + '.kicad_mod')


if __name__ == '__main__':

    script_generated_note="script-generated using https://gitlab.com/kicad/libraries/kicad-footprint-generator/-/tree/master/scripts/TerminalBlock_DEGSON";
    classname="TerminalBlock_DEGSON"

    #
    # DG35C-B-XXP-1Y-00A(H)
    #
    pins=[2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,24]
    rm = 8.25
    package_height = 13.60
    leftbottom_offset = [5.075, package_height/2]
    ddrill = 1.6
    pad = [3, 6]
    barrier_xoffset = 4.125
    barrier_width = 1.9
    fabref_offset=[0,-1]
    for p in pins:
        name=f"DG35C-B-{p:02}P-1Y-00AH"
        webpage="https://www.degson.com/content/details_552_878276.html?lang=en"
        classname_description=f"Terminal Block DEGSON {name}"
        footprint_name=f"TerminalBlock_DEGSON_{name}_1x{p:02}_P{rm:3.2f}mm"
        makeBarrierTerminalBlock(footprint_name=footprint_name, 
                                  pins=p, rm=rm, 
                                  package_height=package_height, leftbottom_offset=leftbottom_offset, 
                                  ddrill=ddrill, pad=pad, 
                                  barrier_xoffset=barrier_xoffset, barrier_width=barrier_width,
                                  fabref_offset=fabref_offset,
                                  tags_additional=['Horizontal'], lib_name="${KICAD7_3DMODEL_DIR}/"+classname, 
                                  classname=classname, classname_description=classname_description, 
                                  webpage=webpage, script_generated_note=script_generated_note)

