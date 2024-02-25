#!/usr/bin/env python3

#####
# Usage : python gen_inductor.py <inputfile.yaml> <outputPath>


import sys
import os
import yaml
from pathlib import Path
import argparse
import logging

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))
from KicadModTree import Footprint, FootprintType, Text, \
    Line, Pad, RectLine
from scripts.tools.drawing_tools import roundGUp, roundGDown
from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.global_config_files.global_config import GlobalConfig

from smd_inductor_properties import InductorSeriesProperties, SmdInductorProperties


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


silkscreenOffset = 0.2
fabOffset = 0.0
tinyPartOffset = silkscreenOffset   # Arbitrary compensation for tiny part silkscreen logic below


class InductorGenerator(FootprintGenerator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_all_series(self, input_data: dict, csv_dir: Path):

        # For each series block in the yaml file, process it
        for series_block in input_data:

            series_data = InductorSeriesProperties(series_block, csv_dir)

            for part_data in series_data.parts:
                self.generate_footprint(series_data, part_data)

    def generate_footprint(self, series_data: InductorSeriesProperties,
                           part_data: SmdInductorProperties):

        # All these variable are guaranteed by SmdInductorProperties
        widthX = part_data.width_x
        lengthY = part_data.length_y
        height = part_data.height
        landingY = part_data.landing_dims.size_crosswise
        landingX = part_data.landing_dims.size_inline
        landingSpacing = part_data.landing_dims.spacing_inside
        part_number = part_data.part_number

        # If the CSV has unique data sheets, then use that. Otherwise, if the column
        # is missing, then use the series datasheet for all
        if part_data.datasheet is not None:
            partDatasheet = part_data.datasheet
        elif series_data.datasheet is not None:
            partDatasheet = series_data.datasheet
        else:
            # If datasheet was not defined in YAML nor CSV, terminate
            raise RuntimeError(f"No datasheet defined for {part_number} - terminating.")

        footprint_name = f'L_{series_data.manufacturer}_{part_number}'
        logging.info(f'Processing {footprint_name}')

        # init kicad footprint
        kicad_mod = Footprint(footprint_name, FootprintType.SMD)
        kicad_mod.setDescription(
            f"Inductor, {series_data.manufacturer}, {part_number}, {widthX}x{lengthY}x{height}mm, {partDatasheet}")
        kicad_mod.tags = ["Inductor"] + series_data.tags

        # set general values

        scaling = landingX / 3
        clampscale = clamp(scaling, 0.5, 1)

        # Check if our part is so small that REF will overlap the pads. Rotate it to fit.
        if landingX + landingSpacing < 2:
            rot = 90
        else:
            rot = 0
        kicad_mod.append(Text(
            type='user', text='${REFERENCE}', at=[0, 0],
            layer='F.Fab', rotation=rot,
            size=[clampscale, clampscale],
            thickness=clampscale*0.15
        ))

        # Fab layer
        kicad_mod.append(RectLine(
            start=[0 - widthX / 2 - fabOffset, -lengthY / 2 - fabOffset],
            end=[widthX / 2 + fabOffset, lengthY / 2 + fabOffset],
            layer='F.Fab',
            width=self.global_config.fab_line_width))

        # create COURTYARD
        # Base it off the copper or physical, whichever is biggest. Need to check both X and Y.

        # Extreme right edge
        rightCopperMax = landingSpacing/2 + landingX
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
        bottomCopperMax = landingY / 2
        bottomPhysicalMax = lengthY / 2
        if bottomCopperMax > bottomPhysicalMax:
            tallest = landingY  # Copper is bigger
        else:
            tallest = lengthY

        cy_offset = self.global_config.get_courtyard_offset(GlobalConfig.CourtyardType.DEFAULT)
        cy_grid = self.global_config.courtyard_grid

        kicad_mod.append(RectLine(
            start=[
                roundGDown(-widest / 2 - cy_offset, cy_grid),
                roundGDown(-tallest / 2 - cy_offset, cy_grid)
            ],
            end=[
                roundGUp(widest/2 + cy_offset, cy_grid),
                roundGUp(tallest/2 + cy_offset, cy_grid)
            ],
            layer='F.CrtYd',
            width=self.global_config.courtyard_line_width
        ))

        # Silkscreen REF
        kicad_mod.append(Text(type='reference', text='REF**', at=[0, 0-tallest/2-1], layer='F.SilkS'))
        # Fab Value
        kicad_mod.append(Text(type='value', text=footprint_name, at=[0, tallest/2+1], layer='F.Fab'))

        silk_width = self.global_config.silk_line_width

        # Silkscreen corners
        vertLen = (tallest / 2 - landingY / 2) + silkscreenOffset - 0.2
        leftX = -widthX / 2 - silkscreenOffset - silk_width / 2
        rightX = widthX / 2 + silkscreenOffset + silk_width / 2
        upperY = -tallest / 2 - silkscreenOffset - silk_width / 2
        lowerY = tallest / 2 + silkscreenOffset + silk_width / 2
        # End of silkscreen vars

        # Create silkscreen

        # Full upper line
        kicad_mod.append(Line(
            start=[leftX, upperY],
            end=[rightX, upperY],
            layer='F.SilkS',
            width=silk_width
        ))
        # Full lower line
        kicad_mod.append(Line(
            start=[leftX, lowerY],
            end=[rightX, lowerY],
            layer='F.SilkS',
            width=silk_width
        ))

        # If the part is too small and we can't make vertical tick's, don't create 0 length lines.
        if (vertLen > 0):
            # Tick down left
            kicad_mod.append(Line(
                start=[leftX, upperY],
                end=[leftX, upperY + vertLen],
                layer='F.SilkS', width=silk_width
            ))
            # Tick down right
            kicad_mod.append(Line(
                start=[rightX, upperY],
                end=[rightX, upperY + vertLen],
                layer='F.SilkS', width=silk_width))
            # Tick up left
            kicad_mod.append(Line(
                start=[leftX, lowerY],
                end=[leftX, lowerY - vertLen],
                layer='F.SilkS', width=silk_width))
            # Tick up right
            kicad_mod.append(Line(
                start=[rightX, lowerY],
                end=[rightX, lowerY - vertLen],
                layer='F.SilkS', width=silk_width))

        # Copper Pads
        kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                             at=[0-landingSpacing/2-landingX/2, 0],
                             size=[landingX, landingY], layers=Pad.LAYERS_SMT))
        kicad_mod.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                             at=[landingSpacing/2+landingX/2, 0],
                             size=[landingX, landingY], layers=Pad.LAYERS_SMT))

        # No variants, so we can just use the footprint name
        self.add_standard_3d_model_to_footprint(kicad_mod, series_data.library_name,
                                                kicad_mod.name)

        self.write_footprint(kicad_mod, series_data.library_name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Use .yaml files to create SMD inductor footprints.')

    parser.add_argument('files', metavar='file', type=Path, nargs='+',
                        help='list of files holding information about what devices should be created.')
    # global_config is for backwards compatibility
    parser.add_argument('--global-config', '--global_config', type=Path, nargs='?',
                        help='the config file defining how the footprint will look like. (KLC)',
                        default='../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase output verbosity')

    FootprintGenerator.add_standard_arguments(parser)

    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    global_config = GlobalConfig.load_from_file(args.global_config)

    generator = InductorGenerator(output_dir=args.output_dir,
                                  global_config=global_config)

    for data_file in args.files:
        with open(data_file, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
            csv_dir = data_file.parent
            generator.generate_all_series(data_loaded, csv_dir)
