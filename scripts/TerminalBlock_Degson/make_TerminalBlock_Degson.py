#!/usr/bin/env python

import sys
import os
import math

# ensure that the kicad-footprint-generator directory is available
#sys.path.append(os.environ.get('KIFOOTPRINTGENERATOR'))  # enable package import from parent directory
#sys.path.append("D:\hardware\KiCAD\kicad-footprint-generator")  # enable package import from parent directory
sys.path.append("C:\\Users\\gegger\\Documents\\kicad-footprint-generator")
sys.path.append(os.path.join(sys.path[0],"..","..","kicad_mod")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","..")) # load kicad_mod path
sys.path.append(os.path.join(sys.path[0],"..","tools")) # load kicad_mod path

from KicadModTree import *  # NOQA
from footprint_scripts_terminal_blocks import *

if __name__ == '__main__':

    script_generated_note=""
    classname="TerminalBlock_Degson"
    pins=[1,2,3,4,5,6,7,8,9,10,12,13,14,15,16,18,19,20,24,44,45] # from manufacturer homepage, not all stores list all the poles
    rm=3.5  # pitch
    package_height=12 # overall extension in y-direction
    leftbottom_offset=[3.25, 9.7, 1.75]
    ddrill=1.2
    pad=[2,3]
    bevel_height=[4.7]
    vsegment_lines_offset=[-1.75]
    even_pin_offset = 5
    opening=[2.9,2.3]
    opening_xoffset=0
    opening_yoffset=2 # estimated
    opening_elliptic=True
    fabref_offset=[0,-1]
    for p in pins:
        name="DG250-3.5-{:02d}P".format(p);
        webpage="https://www.degson.com/content/details_552_879717.html?lang=en";
        classname_description="Terminal Block Degson {0}".format(name);
        footprint_name="TerminalBlock_Degson_{0}_1x{1:02}_P{2:3.2f}mm_45Degree".format(name, p, rm)
        makeTerminalBlock45Degree(footprint_name=footprint_name, 
                                  pins=p, rm=rm, 
                                  package_height=package_height, leftbottom_offset=leftbottom_offset, 
                                  ddrill=ddrill, pad=pad, even_pin_offset=even_pin_offset, vsegment_lines_offset=vsegment_lines_offset,
                                  opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset, opening_elliptic=opening_elliptic,
                                  bevel_height=bevel_height, fabref_offset=fabref_offset,
                                  tags_additional=[], lib_name="${KICAD6_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
     
     