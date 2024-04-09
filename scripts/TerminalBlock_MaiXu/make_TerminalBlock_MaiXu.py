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

class MaiXu_MX126_Generator(object):
    # Generic properties
    # Actually https://www.cnmaixu.com/Sites/maixu/static/upload/file/20240108/1704697250343193.pdf but connection refused
    fplib_name = "TerminalBlock_MaiXu" # Name of the footprint library
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2309150913_MAX-MX126-5-0-03P-GN01-Cu-S-A_C5188435.pdf"
    script_generated_note = f"script-generated using https://gitlab.com/kicad/libraries/kicad-footprint-generator/-/tree/master/scripts/{fplib_name}";

    available_pincounts = [2, 3]
    rm = 5.0 # Distance beteen any 
    package_height = 7.8 # Y size of footprint, not height above PCB!
    leftbottom_offset=[3, package_height-4]
    ddrill=1.3
    pad=[2.8,2.8] # Guess, Based on MetzConnect Type011
    screw_diameter=3.2 # Guess, Based on MetzConnect Type011
    bevel_height=[2,package_height-4.5,package_height-3.5] # Guess, Based on MetzConnect Type011
    slit_screw = True # Draw "slit" in F.Fab rendering
    screw_pin_offset=[0,0] # ?
    secondHoleDiameter=0 # ?
    secondHoleOffset=[0,0] # ?
    thirdHoleDiameter=0 # ?
    thirdHoleOffset=[0,-4] # ?
    fourthHoleDiameter=0 # ?
    fourthHoleOffset=[0,0] # ?
    fabref_offset=[0,4.5] # ?
    nibbleSize=[] # ?
    nibblePos=[] # ?
    
    def part_mpn(self, pincount):
        return f"MX126-{self.rm:.1f}-{pincount:02}P"
    
    def footprint_name(self, pincount: int):
        name = self.part_mpn(pincount)
        return f"TerminalBlock_MaiXu_{name}_1x{pincount:02}_P{self.rm:3.2f}mm"
    
    def classname_description(self, pincount: int):
        name = self.part_mpn(pincount)
        return f"terminal block MaiXu {name}"

    def generate(self):
        """Generate all footprints"""
        for pincount in self.available_pincounts:
            makeTerminalBlockStd(footprint_name=self.footprint_name(pincount),
                pins=pincount, rm=self.rm, 
                package_height=self.package_height,
                leftbottom_offset=self.leftbottom_offset, 
                ddrill=self.ddrill,
                pad=self.pad,
                screw_diameter=self.screw_diameter,
                bevel_height=self.bevel_height,
                slit_screw=self.slit_screw,
                screw_pin_offset=self.screw_pin_offset,
                secondHoleDiameter=self.secondHoleDiameter, 
                secondHoleOffset=self.secondHoleOffset,
                thirdHoleDiameter=self.thirdHoleDiameter,
                thirdHoleOffset=self.thirdHoleOffset,
                fourthHoleDiameter=self.fourthHoleDiameter,
                fourthHoleOffset=self.fourthHoleOffset,
                nibbleSize=self.nibbleSize,
                nibblePos=self.nibblePos,
                fabref_offset=self.fabref_offset,
                tags_additional=[], lib_name=f'${{KICAD8_3DMODEL_DIR}}/{self.fplib_name}',
                classname=self.fplib_name, classname_description=self.classname_description, 
                webpage=self.datasheet,
                script_generated_note=self.script_generated_note)
        
generators = [MaiXu_MX126_Generator]

if __name__ == '__main__':
    for Type_ in generators:
        generator = Type_()
        generator.generate()
        