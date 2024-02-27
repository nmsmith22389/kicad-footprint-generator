#!/usr/bin/env python

import sys
import os
import math

# ensure that the kicad-footprint-generator directory is available
#sys.path.append(os.environ.get('KIFOOTPRINTGENERATOR'))  # enable package import from parent directory
#sys.path.append("D:\hardware\KiCAD\kicad-footprint-generator")  # enable package import from parent directory
sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","..")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path

from KicadModTree import *  # NOQA
from footprint_scripts_terminal_blocks import *


if __name__ == '__main__':
    script_generated_note = ("script-generated using https://gitlab.com"
            "/kicad/libraries/kicad-footprint-generator/scripts/TerminalBlock_CUI")
    classname = "TerminalBlock_CUI"

    pins = range(2, 24+1)
    rm = 5.08
    package_height = 10.25
    leftbottom_offset = [rm/2, package_height-4.9, rm/2+0.6]
    ddrill = 1.6
    pad = [2.4, 2.4]
    screw_diameter = 3.7
    bevel_height = [1, 8.75]
    slit_screw = True
    screw_pin_offset = [0, 0]
    secondDrillDiameter = 0
    secondDrillOffset = [0, 0]
    secondDrillPad = [0, 0]
    secondHoleDiameter = 0
    secondHoleOffset = [0, 0]
    thirdHoleDiameter = 0
    thirdHoleOffset = [0, 0]
    fourthHoleDiameter = 0
    fourthHoleOffset = [0, 0]
    fabref_offset = [0, 0]
    nibbleSize = []
    nibblePos = []
    for p in pins:
        name = "TB007-508-{:02}".format(p)
        webpage = "https://www.cuidevices.com/product/resource/tb007-508.pdf"
        classname_description = "Terminal Block CUI {0}".format(name)
        footprint_name = "{}_{}_1x{:02}_P{:3.2f}mm_Horizontal".format(
                classname, name, p, rm)
        makeTerminalBlockStd(footprint_name=footprint_name,
                pins=p,
                rm=rm,
                package_height=package_height,
                leftbottom_offset=leftbottom_offset,
                ddrill=ddrill,
                pad=pad,
                screw_diameter=screw_diameter,
                bevel_height=bevel_height,
                slit_screw=slit_screw,
                screw_pin_offset=screw_pin_offset,
                secondHoleDiameter=secondHoleDiameter,
                secondHoleOffset=secondHoleOffset,
                thirdHoleDiameter=thirdHoleDiameter,
                thirdHoleOffset=thirdHoleOffset,
                fourthHoleDiameter=fourthHoleDiameter,
                fourthHoleOffset=fourthHoleOffset,
                secondDrillDiameter=secondDrillDiameter,
                secondDrillOffset=secondDrillOffset,
                secondDrillPad=secondDrillPad,
                nibbleSize=nibbleSize,
                nibblePos=nibblePos,
                fabref_offset=fabref_offset,
                tags_additional=[],
                lib_name='${KICAD8_3DMODEL_DIR}/'+classname,
                classname=classname,
                classname_description=classname_description,
                webpage=webpage,
                script_generated_note=script_generated_note)
