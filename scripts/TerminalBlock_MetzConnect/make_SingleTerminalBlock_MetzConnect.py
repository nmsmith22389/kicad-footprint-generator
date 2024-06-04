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

    script_generated_note="script-generated using https://gitlab.com/kicad/libraries/kicad-footprint-generator/-/tree/master/scripts/TerminalBlock_MetzConnect";
    classname="TerminalBlock_MetzConnect"
        
    block_size=[4,4]
    block_offset=[0,0]
    pins=[[1.5,0],[-1.5,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=3
    screw_offset=[0,0]
    slit_screw=True
    name="360272"
    webpage="https://www.metz-connect.com/externalfiles/360272/863850.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM2.6".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
       
    block_size=[5,4]
    block_offset=[0.5,0]
    name="360273"
    webpage="https://www.metz-connect.com/externalfiles/360273/863857.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM2.6_WireProtection".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
      
    block_size=[5,5]
    block_offset=[0,0]
    pins=[[2,0],[-2,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=4
    screw_offset=[0,0]
    slit_screw=True
    name="360410"
    webpage="https://www.metz-connect.com/externalfiles/360410/863875.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
    name="360381"
    webpage="https://www.metz-connect.com/externalfiles/360381/863870.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
       
    block_size=[6,4]
    block_offset=[1,0]
    name="360322"
    webpage="https://www.metz-connect.com/externalfiles/360322/863879.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0_WireProtection".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
      
    block_size=[9, 7.3]
    block_offset=[0,0]
    pins=[[2,0],[-2,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=4
    screw_offset=[0,0]
    slit_screw=True
    name="360291"
    webpage="https://www.metz-connect.com/externalfiles/360291/863863.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0_Boxed".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
                                       
    block_size=[9, 7.3]
    block_offset=[0,0]
    pins=[[0,0]]
    ddrill=1.5
    pad=[3,3]
    screw_diameter=4
    screw_offset=[0,0]
    slit_screw=True
    name="360271"
    webpage="https://www.metz-connect.com/externalfiles/360271/863846.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM3.0_Boxed".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
                                       
    block_size=[9,9]
    block_offset=[0,0]
    pins=[[4,4],[-4,4],[4,-4],[-4,-4]]
    ddrill=1.6
    pad=[3.2,3.2]
    screw_diameter=7
    screw_offset=[0,0]
    slit_screw=True
    name="360425"
    webpage="https://www.metz-connect.com/externalfiles/360425/863882.PDF"
    footprint_name="TerminalBlock_MetzConnect_{0}_1x01_Horizontal_ScrewM4.0_Boxed".format(name)
    classname_description="single screw terminal block Metz Connect {0}".format(name)
    makeScrewTerminalSingleStd(footprint_name, block_size=block_size, block_offset=block_offset, pins=pins, ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, screw_offset=screw_offset, slit_screw=slit_screw,
                        tags_additional=[], lib_name="${KICAD8_3DMODEL_DIR}/"+classname, classname=classname, classname_description=classname_description, webpage=webpage, script_generated_note=script_generated_note)
                                  