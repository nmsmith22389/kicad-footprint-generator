#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# # Dimensions are from Jedec MS-026D document.
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
#* These are cadquery tools to export                                       *
#* generated models in STEP & VRML format.                                  *
#*                                                                          *
#* cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
#* Copyright (c) 2015                                                       *
#*     Maurice https://launchpad.net/~easyw                                 *
#* Copyright (c) 2022                                                       *
#*     Update 2022                                                          *
#*     jmwright (https://github.com/jmwright)                               *
#*     Work sponsored by KiCAD Services Corporation                         *
#*          (https://www.kipro-pcb.com/)                                    *
#*                                                                          *
#* All trademarks within this guide belong to their legitimate owners.      *
#*                                                                          *
#*   This program is free software; you can redistribute it and/or modify   *
#*   it under the terms of the GNU General Public License (GPL)             *
#*   as published by the Free Software Foundation; either version 2 of      *
#*   the License, or (at your option) any later version.                    *
#*   for detail see the LICENCE text file.                                  *
#*                                                                          *
#*   This program is distributed in the hope that it will be useful,        *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
#*   GNU Library General Public License for more details.                   *
#*                                                                          *
#*   You should have received a copy of the GNU Library General Public      *
#*   License along with this program; if not, write to the Free Software    *
#*   Foundation, Inc.,                                                      *
#*   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA           *
#*                                                                          *
#****************************************************************************

__title__ = "make SMD inductors 3D models exported to STEP and VRML"
__author__ = "scripts: maurice; models: see cq_model files; update: jmwright"
__Comment__ = '''This generator loads cadquery model scripts and generates step/wrl files for the official kicad library.'''

___ver___ = "2.0.0"

import os
import yaml
import cadquery as cq
import csv
import glob
from _tools import shaderColors, parameters, cq_color_correct
from _tools import cq_globals
from exportVRML.export_part_to_VRML import export_VRML

def make_models(model_to_build=None, output_dir_prefix=None, enable_vrml=True):
    """
    Main entry point into this generator.
    """
    models = []


    if output_dir_prefix == None:
        print("ERROR: An output directory must be provided.")
        return
    
    # model_to_build can be 'all', or a specific YAML file
    # find yaml files here, need to figure out the path to do so

    inductorPath = os.path.dirname(os.path.realpath(__file__))
    allYamlFiles = glob.glob(f'{inductorPath}/*.yaml')

    if not allYamlFiles:
        print('No YAML files found to process.')
        return
    
    fileList = None

    if model_to_build != "all":
        for yamlFile in allYamlFiles:
            basefilename = os.path.splitext(os.path.basename(yamlFile))[0]
            if basefilename == model_to_build:
                fileList = [yamlFile]   # The file list will be just 1 item, our specific 
                break

    # 2 possibilities now - fileList is a single file that we found, or fileList is empty (didn't find file, or building all)
    
    # Trying to build a specific file and it was not found
    if model_to_build != "all" and fileList is None:
        print(f'Could not find YAML for model {model_to_build}')
        return
    elif model_to_build == "all":
        fileList = allYamlFiles

    print(f'Files to process : {fileList}')

    for yamlFile in fileList:
        with open(yamlFile, 'r') as stream:
            print(f'Processing file {yamlFile}')
            data_loaded = yaml.safe_load(stream)
            for yamlBlocks in range(0, len(data_loaded)): # For each series block in the yaml file, we process the CSV
                seriesName = data_loaded[yamlBlocks]['series']
                seriesManufacturer = data_loaded[yamlBlocks]['manufacturer']
                seriesDatasheet = data_loaded[yamlBlocks]['datasheet']
                seriesCsv = data_loaded[yamlBlocks]['csv']
                seriesSpacing = data_loaded[yamlBlocks].get('spacing', 'edge')   # default to edge
                seriesTags = data_loaded[yamlBlocks]['tags']      # space delimited list of the tags
                seriesTagsString = ' '.join(seriesTags)

                try:
                    seriesBodyColor = data_loaded[yamlBlocks]['3d'].get('bodyColor', 'black body')
                    seriesPinColor = data_loaded[yamlBlocks]['3d'].get('pinColor', 'metal grey pins')
                    seriesPadThickness = data_loaded[yamlBlocks]['3d'].get('padThickness', 0.05)
                    seriesType = data_loaded[yamlBlocks]['3d'].get('type', 1)
                except:
                    # 3D section was not defined, set to default.
                    seriesBodyColor = 'black body'
                    seriesPinColor = 'metal grey pins'
                    seriesPadThickness = 0.05
                    seriesType = 1
                
                yamlFolder = os.path.split(yamlFile)[0]

                # Construct the final output directory
                output_dir = os.path.join(output_dir_prefix, f'{seriesManufacturer}_{seriesName}')

                with open(os.path.join(yamlFolder, seriesCsv), encoding='utf-8-sig') as csvfile:
                    print(f'Processing child {seriesCsv}')
                    reader = csv.DictReader(csvfile)

                    for row in reader:
                        partName = row['PartNumber']
                        # Physical dimensions
                        widthX = float(row['widthX'])
                        lengthY = float(row['lengthY'])
                        height = float(row['height'])
                        padX  = float(row['padX'])
                        padY = float(row['padY'])
                        
                        rotation = 0

                        case = cq.Workplane("XY").box(widthX, lengthY, height, (True, True, False))
                        case = case.edges("|Z").fillet(min(lengthY,widthX)/20)
                        case = case.edges(">Z").fillet(min(lengthY,widthX)/20)

                        if seriesType == 1:
                            pin1 = cq.Workplane("XY").box(padX, padY, seriesPadThickness, (True, True, False)).translate((-(widthX-padX)/2, 0, 0))
                            pin2 = cq.Workplane("XY").box(padX, padY, seriesPadThickness, (True, True, False)).translate(((widthX-padX)/2, 0, 0))
                        else:
                            # Type 2 has visible side "wings". High is approximate since it's rarely specificed, and it shouldn't be more then 3mm probably so we use a min() function.
                            pin1 = cq.Workplane("XY").box(padX + 0.01, padY, min(3, height * 0.3), (True, True, False)).translate((-(widthX-padX)/2, 0, 0))
                            pin2 = cq.Workplane("XY").box(padX + 0.01, padY, min(3, height * 0.3), (True, True, False)).translate(((widthX-padX)/2, 0, 0))
    
                        pins = pin1.union(pin2)

                        case = case.cut(pins)
                        
                        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)
                        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

                        # Used to wrap all the parts into an assembly
                        component = cq.Assembly()

                        # Add the parts to the assembly
                        stepBodyColor = shaderColors.named_colors[seriesBodyColor].getDiffuseFloat()
                        stepPinColor = shaderColors.named_colors[seriesPinColor].getDiffuseFloat()

                        component.add(case, color=cq_color_correct.Color(stepBodyColor[0], stepBodyColor[1], stepBodyColor[2]))
                        component.add(pins, color=cq_color_correct.Color(stepPinColor[0], stepPinColor[1], stepPinColor[2]))

                        # Create the output directory if it does not exist
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)

                        # Assemble the filename
                        file_name = f'L_{seriesManufacturer}_{partName}'

                        # Export the assembly to STEP
                        component.save(os.path.join(output_dir, file_name + ".step"), cq.exporters.ExportTypes.STEP, write_pcurves=False)

                        # Export the assembly to VRML
                        # Dec 2022- do not use CadQuery VRML export, it scales/uses inches.
                        export_VRML(os.path.join(output_dir, file_name + ".wrl"), [case, pins], [seriesBodyColor, seriesPinColor])



