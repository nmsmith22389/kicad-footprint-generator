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
from _tools import shaderColors, parameters, cq_color_correct, cq_globals, export_tools
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
                seriesManufacturer = data_loaded[yamlBlocks]['manufacturer']
                seriesCsv = data_loaded[yamlBlocks]['csv']

                # If the 3d section is defined, then this block will pick up some values
                try:
                    seriesBodyColor = data_loaded[yamlBlocks]['3d'].get('bodyColor', 'black body')
                    seriesPinColor = data_loaded[yamlBlocks]['3d'].get('pinColor', 'metal grey pins')
                    seriesPadThickness = data_loaded[yamlBlocks]['3d'].get('padThickness', 0.05)
                    seriesType = data_loaded[yamlBlocks]['3d'].get('type', 1)
                    seriesCornerRadius = data_loaded[yamlBlocks]['3d'].get('cornerRadius', 0)
                    seriesPadSpacing = data_loaded[yamlBlocks]['3d'].get('padSpacing', 'none')
                except:
                    # 3D section was not defined, set to default.
                    seriesBodyColor = 'black body'
                    seriesPinColor = 'metal grey pins'
                    seriesPadThickness = 0.05
                    seriesType = 1
                    seriesCornerRadius = 0
                    seriesPadSpacing = 'none'
                
                yamlFolder = os.path.split(yamlFile)[0]

                # Construct the final output directory
                output_dir = os.path.join(output_dir_prefix, data_loaded[yamlBlocks]['destination_dir'])

                with open(os.path.join(yamlFolder, seriesCsv), encoding='utf-8-sig') as csvfile:
                    print(f'Processing child {seriesCsv}')
                    reader = csv.DictReader(csvfile)

                    for row in reader:
                        partName = row['PartNumber']
                        # Physical dimensions
                        widthX = float(row['widthX'])
                        lengthY = float(row['lengthY'])
                        height = float(row['height'])
                        
                        if seriesPadSpacing != 'none':
                            try:
                                padSpacing = float(row['padSpacing'])
                            except:
                                print('\n\npadSpacing must be defined in CSV when seriesPadSpacing is not "none". Terminating.\n\n')
                                exit(1)

                        try:
                            padX  = float(row['padX'])
                            padY = float(row['padY'])
                            
                        except:
                            print(f'No physical pad dimensions (padX/padY) found - using PCB landing dimensions (landingX/landingY) as a substitute.')
                            padX = round(float(row['landingX']) - 0.05, 2)  # Round to 2 decimal places since sometimes we get a lot more
                            padY = round(float(row['landingY']) - 0.05, 2)

                        # Handy debug section to help copy/paste into CQ-editor to play with design
                        if False:
                            print(f'widthX = {widthX}')
                            print(f'lengthY = {lengthY}')
                            print(f'height = {height}')
                            print(f'padX = {padX}')
                            print(f'padY = {padY}')
                            #print(f'padSpacing = {padSpacing}')
                            print(f'seriesType = {seriesType}')
                            print(f'seriesPadSpacing = "{seriesPadSpacing}"')
                            print(f'seriesPadThickness = {seriesPadThickness}')
                            

                        rotation = 0

                        case = cq.Workplane("XY").box(widthX, lengthY, height, (True, True, False))
                        
                        if seriesCornerRadius == 0:
                            case = case.edges("|Z").fillet(min(lengthY,widthX)/20)
                        else:
                            case = case.edges("|Z").fillet(seriesCornerRadius)    
                        
                        case = case.edges(">Z").fillet(min(lengthY,widthX)/20)

                        if seriesType == 2:     # Exposed "wings"
                            seriesPadThickness = min(3, height * 0.3)

                        pin1 = cq.Workplane("XY").box(padX, padY, seriesPadThickness, (True, True, False))
                        pin2 = cq.Workplane("XY").box(padX, padY, seriesPadThickness, (True, True, False))

                        if seriesPadSpacing == 'none':   # Move pads to the edge
                            translateAmount = widthX/2 - padX/2
                        elif seriesPadSpacing == 'edge':
                            translateAmount = padX/2 + padSpacing/2
                        elif seriesPadSpacing == 'center':
                            translateAmount = padSpacing/2

                        if seriesType == 2:     # Exposed "wings", bump it out so it is visible
                            translateAmount += 0.01

                        pin1 = pin1.translate((-translateAmount, 0, 0))
                        pin2 = pin2.translate((translateAmount, 0, 0))

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
                        component.name = file_name
                        component.save(os.path.join(output_dir, file_name + ".step"), cq.exporters.ExportTypes.STEP, mode=cq.exporters.assembly.ExportModes.FUSED, write_pcurves=False)

                        # Check for a proper union
                        export_tools.check_step_export_union(component, output_dir, file_name)

                        # Export the assembly to VRML
                        # Dec 2022- do not use CadQuery VRML export, it scales/uses inches.
                        export_VRML(os.path.join(output_dir, file_name + ".wrl"), [case, pins], [seriesBodyColor, seriesPinColor])



