#!/usr/bin/env python
import sys
import os
# ensure that the kicad-footprint-generator directory is available
sys.path.append(os.path.join(sys.path[0],"..","..")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path
from KicadModTree import *  # NOQA
from footprint_scripts_terminal_blocks import *

script_generated_note="https://github.com/pointhi/kicad-footprint-generator/tree/master/scripts/TerminalBlock_Degson"
classname="TerminalBlock_Degson"


def make_DG212V_THR_3_5():
    """DG212V-THR-3.5 - http://www.degson.com/en/pro_detail/id/150"""
    pins=range(2,24+1)
    rm=3.5
    package_height=8.5
    leftbottom_offset=[2.10, 1.4]
    ddrill=1.2
    pad=[2.2,2.2]
    bevel_height=[1.5]
    opening=[2.7, 2.7]
    opening_xoffset=0
    opening_yoffset=1.5
    secondDrillDiameter=ddrill
    secondDrillOffset=[0,-5.5]
    secondDrillPad=pad
    secondHoleDiameter=[3,3]
    secondHoleOffset=[0,-5]
    thirdHoleDiameter=0
    thirdHoleOffset=[0,0]
    fourthHoleDiameter=0
    fourthHoleOffset=[0,0]
    fabref_offset=[0,3.6]
    nibbleSize=[]
    nibblePos=[]
    webpage="http://www.degson.com/en/downpdf/id/150.html"
    for p in pins:
        classname_description="Terminal Block Degson DG212V-THR-3.5-{:02d}P-1Y-00A(H)".format(p)
        footprint_name="DG212V-THR-3.5-{1:02d}P-1Y-00A_1x{1:02}_P{0:3.2f}mm_Vertical".format(rm, p)
        makeTerminalBlockVertical(footprint_name=footprint_name,
                                  pins=p, rm=rm,
                                  package_height=package_height, leftbottom_offset=leftbottom_offset, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset, opening=opening,
                                  ddrill=ddrill, pad=pad, bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                  secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                  nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                  tags_additional=[], lib_name='${KISYS3DMOD}/'+classname, classname=classname, classname_description=classname_description,
                                  webpage=webpage, script_generated_note=script_generated_note)


def make_DG242V_7_5():
    """DG242V-7.5 - http://www.degson.com/en/pro_detail/id/222"""
    pins=range(1,8+1)
    rm=7.5
    package_height=17
    leftbottom_offset=[4.2, 10.7]
    ddrill=1.3
    pad=[3.5, 3.5]
    bevel_height=[5]
    opening=[3.5, 4.5]
    opening_xoffset=0
    opening_yoffset=10.7
    secondDrillDiameter=ddrill
    secondDrillOffset=[0, -5.0]
    secondDrillPad=pad
    secondHoleDiameter=[4.7, 4]
    secondHoleOffset=[0, 12]
    thirdHoleDiameter=0
    thirdHoleOffset=[0,0]
    fourthHoleDiameter=0
    fourthHoleOffset=[0,0]
    fabref_offset=[0, 1]
    nibbleSize=[]
    nibblePos=[]
    webpage="http://www.degson.com/en/downpdf/id/222.html"
    for p in pins:
        classname_description="Terminal Block Degson DG242V-7.5-{:02d}P-1Y-00A(H)".format(p)
        footprint_name="DG242V-7.5-{1:02d}P-1Y-00A_1x{1:02}_P{0:3.2f}mm_Vertical".format(rm, p)
        makeTerminalBlockVertical(footprint_name=footprint_name,
                                  pins=p, rm=rm,
                                  package_height=package_height, leftbottom_offset=leftbottom_offset, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset, opening=opening,
                                  ddrill=ddrill, pad=pad, bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                  secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                  nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                  tags_additional=[], lib_name='${KISYS3DMOD}/'+classname, classname=classname, classname_description=classname_description,
                                  webpage=webpage, script_generated_note=script_generated_note)


def make_2CDGRM_5_08():
    """2CDGRM-5.08 - http://www.degson.com/en/pro_detail/id/689"""
    pins=range(2, 22+1)
    for p in pins:
        footprint_name = "2CDGRM-5.08-{0:02d}P-1Y-00A_1x{0:02d}_P5.08_Horizontal".format(p)
        print(footprint_name)

        dx = 5.08
        y_mounting = 1.9
        sx = (p - 1) * dx + 15.24  # X size without the flange
        sx_flange = sx + 2 * 1.4
        sy = 12
        drill_pins = 1.7
        drill_mounting = 2
        pad = 3

        # init kicad footprint
        kicad_mod = Footprint(footprint_name)
        kicad_mod.setDescription(
            "Terminal Block Degson 2CDGRM-5.08-{0:02d}P-1Y-00A(H) {0} pins, flanged,"
            " pitch 5.08mm, size {1}x{2}mm^2, drill diameter {3}mm, pad diameter {4}mm,"
            " see http://www.degson.com/en/pro_detail/id/689, script-generated using"
            " https://github.com/pointhi/kicad-footprint-generator/tree/master/scripts/TerminalBlock_Degson"
            .format(p, sx_flange, sy, drill_pins, pad)
            )
        kicad_mod.setTags(
            "THT Terminal Block Degson 2CDGRM-5.08-{:02d}P-1Y-00A(H) flanged pitch 5.08mm"
            .format(p))

        # create pads
        x = 0
        for p in range(1,p+1):
            if p == 1:
                shape = Pad.SHAPE_RECT
            else:
                shape = Pad.SHAPE_CIRCLE
            kicad_mod.append(Pad(number=p, type=Pad.TYPE_THT, shape=shape,
                                 at=[x, 0], size=pad, drill=drill_pins, layers=Pad.LAYERS_THT))
            x = x + dx

        # create mounting holes
        for p in [-1, p]:
            x = p * dx
            kicad_mod.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                                 at=[x, y_mounting], size=drill_mounting, drill=drill_mounting, layers=Pad.LAYERS_THT))

        #
        # Silkscreen
        #
        xc = (p-1)/2*dx
        kicad_mod.append(Text(type='reference', text='REF**', at=[xc, -3], layer='F.SilkS'))
        # Inside half
        x1 = -1.5 * dx
        x2 = (p-1)*dx-x1
        kicad_mod.append(RectLine(start=[x1, -2.1], end=[x2, 3.8], layer='F.SilkS'))
        # Pin-1 designator
        kicad_mod.append(Line(start=[x1-0.5, -2.6], end=[x1+2.5, -2.6], layer='F.SilkS'))
        kicad_mod.append(Line(start=[x1-0.5, -2.6], end=[x1-0.5, 0.4], layer='F.SilkS'))
        # Flange
        xf1 = -9.02
        xf2 = (p-1)*dx-xf1
        kicad_mod.append(RectLine(start=[xf1, 3.8], end=[xf2, 4.6], layer='F.SilkS'))
        # Foam
        kicad_mod.append(FilledRect(start=[xf1, 4.6], end=[xf2, 5.6], layer='F.SilkS'))
        # Outside half
        kicad_mod.append(RectLine(start=[x1, 5.6], end=[x2, 9.9], layer='F.SilkS'))
        kicad_mod.append(Line(start=[x1, 7], end=[x2, 7], layer='F.SilkS'))
        kicad_mod.append(Line(start=[x1, 8.7], end=[x2, 8.7], layer='F.SilkS'))
        for p in range(-1, p+1):
            x = p * dx
            kicad_mod.append(Line(start=[x-0.5, 8.7], end=[x-0.8, 9.9], layer='F.SilkS'))
            kicad_mod.append(Line(start=[x+0.5, 8.7], end=[x+0.8, 9.9], layer='F.SilkS'))

        #
        # Fabrication
        #
        yfab = 7.9
        if p < 6:
            yfab = 10.8
        kicad_mod.append(Text(type='value', text=footprint_name, at=[xc, yfab], layer='F.Fab'))
        kicad_mod.append(Text(type='user', text='%R', at=[xc, 4], layer='F.Fab'))
        # Simplified outline
        kicad_mod.append(RectLine(start=[x1, -2.1], end=[x2, 9.9], layer='F.Fab'))
        # Pin-1 designator
        kicad_mod.append(Line(start=[-1.9, -1.9], end=[1.1, -1.9], layer='F.Fab'))
        kicad_mod.append(Line(start=[-1.9, -1.9], end=[-1.9, 1.1], layer='F.Fab'))

        #
        # Courtyard
        #
        kicad_mod.append(RectLine(start=[xf1-0.5, -2.6], end=[xf2+.5, 30], layer='F.CrtYd'))

        # add model
        kicad_mod.append(Model(
            filename="${KISYS3DMOD}" + "/TerminalBlock_Degson.3dshapes/{}.wrl".format(footprint_name),
            at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

        # output kicad model
        file_handler = KicadFileHandler(kicad_mod)
        file_handler.writeFile('{}.kicad_mod'.format(footprint_name))


if __name__ == '__main__':
    make_DG212V_THR_3_5()
    make_DG242V_7_5()
    make_2CDGRM_5_08()
