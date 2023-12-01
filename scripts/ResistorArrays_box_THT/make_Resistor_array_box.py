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

from footprint_scripts_sip import *


if __name__ == '__main__':
    # Vishay 300144 resistor array
    pins = 3
    rm = 2.54
    w = 7.49
    h = 2.54
    makeResistorArray(
        pins=pins,
        rm=rm,
        w=w,
        h=h,
        ddrill=0.8,
        footprint_name=f"R_Array_Box{pins}_L{w:.1f}mm_W{h:.1f}mm_P{rm}mm_Vishay_300144",
        description="https://www.vishayfoilresistors.com/docs/63045/300144x.pdf",
        additional_tags=["Vishay", "300144"]
    )
