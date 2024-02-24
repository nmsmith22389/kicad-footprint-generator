#####
# Usage : python gen_inductor.py <inputfile.yaml> <outputPath>

#!/usr/bin/env python3

import sys
import os
import yaml
from pathlib import Path
import csv

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))
sys.path.append(os.path.join(sys.path[0], ".."))
from KicadModTree import *


if len(sys.argv) != 3:
    print(f'Usage : python gen_inductor.py <inputfile.yaml> <outputPath>')
    exit(0)
else:
    outputPath = Path(sys.argv[2])
    print(f'output folder is {outputPath}')
    batchInputFile = Path(sys.argv[1])

silkscreenOffset = 0.2
fabOffset = 0.0
courtyardOffset = 0.25              # 0.25 per KLC
silkLineThickness = 0.12            # Default silkscreen line is 0.12mm thick. Do not change.
tinyPartOffset = silkscreenOffset   # Arbitrary compensation for tiny part silkscreen logic below

def derive_landing_x(data: dict[str, str]) -> (float, float):
    """
    Handle the various methods of providing sufficient dimensions to
    derive the land X dimension, and the inside edge to edge distance
    that this script works with internally.
    :param data: a csvreader row
    :return: a tuple of the form (landingX, landingSpacing)
    """
    xin = data.get("landingX", None)
    spc_c = data.get("landingSpacingX", None)
    spc_ix = data.get("landingInsideX", None)
    spc_ox = data.get("landingOutsideX", None)

    if xin and spc_ix:
        return float(xin), float(spc_ix)
    if xin and spc_c:
        xin = float(xin)
        spc_ix = float(spc_c) - xin
        return xin, spc_ix
    if spc_ix and spc_ox:
        spc_ix = float(spc_ix)
        xin = (float(spc_ox) - spc_ix) / 2
        return xin, spc_ix
    raise RuntimeError("Unhandled combination of landingX dimensions, saw: " + ', '.join(data.keys()))


with open(batchInputFile, 'r') as stream:
    data_loaded = yaml.safe_load(stream)

    for yamlBlocks in range(0, len(data_loaded)): # For each series block in the yaml file, we process the CSV
        seriesName = data_loaded[yamlBlocks]['series']
        seriesManufacturer = data_loaded[yamlBlocks]['manufacturer']
        seriesDatasheet = data_loaded[yamlBlocks].get('datasheet', '')      # allow empty datasheet in case of unique per-part datasheets
        seriesCsv = data_loaded[yamlBlocks]['csv']
        seriesTags = data_loaded[yamlBlocks]['tags']                        # space delimited list of the tags
        seriesTagsString = ' '.join(seriesTags)

        with open(seriesCsv, encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                widthX = float(row['widthX'])
                lengthY = float(row['lengthY'])
                height = float(row['height'])
                landingY = float(row['landingY'])
                landingX, landingSpacing = derive_landing_x(row)
                partNumber = row['PartNumber']

                # If the CSV has unique data sheets, then use that. Otherwise, if the column
                # is missing, then use the series datasheet for all
                try:
                    partDatasheet = str(row['datasheet'])
                except:
                    partDatasheet = seriesDatasheet
                finally:
                    # If datasheet was not defined in YAML nor CSV, terminate
                    if partDatasheet == '':
                        print(f"No datasheet defined for {partNumber} - terminating.")
                        exit(1)




                footprint_name = f'L_{seriesManufacturer}_{partNumber}'
                print(f'Processing {footprint_name}')

                # init kicad footprint
                kicad_mod = Footprint(footprint_name, FootprintType.SMD)
                kicad_mod.setDescription(f"Inductor, {seriesManufacturer}, {partNumber}, {widthX}x{lengthY}x{height}mm, {partDatasheet}")
                kicad_mod.setTags(f"Inductor {seriesTagsString}")

                # set general values

                scaling = landingX/3
                clampscale = clamp(scaling, 0.5, 1)

                # Check if our part is so small that REF will overlap the pads. Rotate it to fit.
                if landingX + landingSpacing < 2:
                    y=lengthY/2+2
                    rot = 90
                else:
                    y=0
                    rot = 0
                kicad_mod.append(Text(type='user', text='${REFERENCE}', at=[0, 0], layer='F.Fab', rotation=rot, size=[clampscale, clampscale], thickness=clampscale*0.15))

                # Fab layer
                kicad_mod.append(RectLine(start=[0-widthX/2-fabOffset, 0-lengthY/2-fabOffset], end=[widthX/2+fabOffset, lengthY/2+fabOffset], layer='F.Fab'))

                # create COURTYARD
                # Base it off the copper or physical, whichever is biggest. Need to check both X and Y.

                # Extreme right edge
                rightCopperMax= landingSpacing/2 + landingX
                rightPhysicalMax = widthX / 2
                if rightCopperMax > rightPhysicalMax:
                    widest = landingSpacing + (landingX * 2)    # Copper is bigger
                else:
                    widest = widthX

                # Extreme top edge
                # Used for determining the courtyard
                # Also used for very tiny parts. Typically we see
                # that the solder pads are quite large for manufacturability, but the part itself is small, so
                # the silkscreen will overlap.
                bottomCopperMax= landingY / 2
                bottomPhysicalMax = lengthY / 2
                if bottomCopperMax > bottomPhysicalMax:    
                    tallest = landingY  # Copper is bigger
                else:
                    tallest = lengthY

                # Need to round so we stick to 0.01mm precision
                kicad_mod.append(RectLine(start=[round(0-widest/2-courtyardOffset, 2), round(0-tallest/2-courtyardOffset, 2)], end=[round(widest/2+courtyardOffset, 2), round(tallest/2+courtyardOffset, 2)], layer='F.CrtYd'))

                # Silkscreen REF
                kicad_mod.append(Text(type='reference', text='REF**', at=[0, 0-tallest/2-1], layer='F.SilkS'))
                # Fab Value
                kicad_mod.append(Text(type='value', text=footprint_name, at=[0, tallest/2+1], layer='F.Fab'))

                # Silkscreen corners
                vertLen = (tallest/2 - landingY/2) + silkscreenOffset - 0.2
                horzLen = (widthX/2 - landingX/2) + silkscreenOffset - 0.2
                leftX = 0-widthX/2-silkscreenOffset - silkLineThickness/2
                rightX = widthX/2+silkscreenOffset + silkLineThickness/2
                upperY = 0-tallest/2-silkscreenOffset - silkLineThickness/2
                lowerY = tallest/2+silkscreenOffset + silkLineThickness/2
                # End of silkscreen vars

                # Create silkscreen
                kicad_mod.append(Line(start=[leftX, upperY], end=[rightX, upperY], layer='F.SilkS'))        # Full upper line
                kicad_mod.append(Line(start=[leftX, lowerY], end=[rightX, lowerY], layer='F.SilkS'))        # Full lower line

                # If the part is too small and we can't make vertical tick's, don't create 0 length lines.
                if (vertLen > 0):
                    kicad_mod.append(Line(start=[leftX, upperY], end=[leftX, upperY + vertLen], layer='F.SilkS'))       # Tick down left
                    kicad_mod.append(Line(start=[rightX, upperY], end=[rightX, upperY + vertLen], layer='F.SilkS'))     # Tick down right
                    kicad_mod.append(Line(start=[leftX, lowerY], end=[leftX, lowerY - vertLen], layer='F.SilkS'))       # Tick up left
                    kicad_mod.append(Line(start=[rightX, lowerY], end=[rightX, lowerY - vertLen], layer='F.SilkS'))     # Tick up right

                # Copper Pads
                kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                                    at=[0-landingSpacing/2-landingX/2, 0], size=[landingX, landingY], layers=Pad.LAYERS_SMT))
                kicad_mod.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                                    at=[landingSpacing/2+landingX/2, 0], size=[landingX, landingY], layers=Pad.LAYERS_SMT))

                # add model
                kicad_mod.append(Model(filename="${KICAD8_3DMODEL_DIR}/" + f"Inductor_SMD.3dshapes/{footprint_name}.wrl",
                                    at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))

                # output kicad model
                file_handler = KicadFileHandler(kicad_mod)
                file_handler.writeFile(f'{outputPath}/{footprint_name}.kicad_mod')

