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
from KicadModTree import Footprint, FootprintType, Text, Line, Pad, RectLine, Vector2D, Property
from scripts.tools.drawing_tools import (
    draw_triangle_pointing_south,
    getStandardSilkArrowSize,
    roundGUp,
    roundGDown,
    SilkArrowSize,
)
from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.global_config_files.global_config import GlobalConfig

from smd_inductor_properties import InductorSeriesProperties, SmdInductorProperties


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


silkscreenOffset = 0.2
fabOffset = 0.0
tinyPartOffset = (
    silkscreenOffset  # Arbitrary compensation for tiny part silkscreen logic below
)


class InductorGenerator(FootprintGenerator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_all_series(self, input_data: dict, csv_dir: Path):

        # For each series block in the yaml file, process it
        for series_block in input_data:

            series_data = InductorSeriesProperties(series_block, csv_dir)

            for part_data in series_data.parts:
                self.generate_footprint(series_data, part_data)

    def generate_footprint(
        self, series_data: InductorSeriesProperties, part_data: SmdInductorProperties
    ):

        landing_pad_dimension = Vector2D(
            part_data.landing_dims.size_inline, part_data.landing_dims.size_crosswise
        )
        part_dimension = Vector2D(part_data.width_x, part_data.length_y)

        # If the CSV has unique data sheets, then use that. Otherwise, if the column
        # is missing, then use the series datasheet for all
        if part_data.datasheet is not None:
            datasheet_url = part_data.datasheet
        elif series_data.datasheet is not None:
            datasheet_url = series_data.datasheet
        else:
            # If datasheet was not defined in YAML nor CSV, terminate
            raise RuntimeError(
                f"No datasheet defined for {part_data.part_number} - terminating."
            )

        footprint_name = f"L_{series_data.manufacturer}_{part_data.part_number}"
        logging.info(f"Processing {footprint_name}")

        # init kicad footprint
        kicad_mod = Footprint(footprint_name, FootprintType.SMD)
        kicad_mod.setDescription(
            f"Inductor, "
            f"{series_data.manufacturer}, {part_data.part_number}, "
            f"{part_data.width_x}x{part_data.length_y}x{part_data.height}mm, "
            f"({datasheet_url}), "
            f"generated with kicad-footprint-generator {os.path.basename(__file__).replace('  ', ' ')}"
        )
        kicad_mod.tags = ["Inductor"] + series_data.tags

        # Create fab layer elements
        for elem in self._create_fab_elements(
            landing_pad_dimension=landing_pad_dimension,
            landing_pad_spacing=part_data.landing_dims.spacing_inside,
            part_dimension=part_dimension,
            ref_value=footprint_name,
            stroke_width=self.global_config.fab_line_width,
            has_orientation=bool(series_data.has_orientation),
        ):
            kicad_mod.append(elem)

        # Create courtyard layer elements
        for elem in self._create_courtyard_elements(
            landing_pad_dimension=landing_pad_dimension,
            landing_pad_spacing=part_data.landing_dims.spacing_inside,
            part_dimension=part_dimension,
            grid=self.global_config.courtyard_grid,
            clearance=self.global_config.get_courtyard_offset(
                GlobalConfig.CourtyardType.DEFAULT
            ),
            stroke_width=self.global_config.courtyard_line_width,
        ):
            kicad_mod.append(elem)

        # Create silkscreen layer elements
        for elem in self._create_silkscreen_elements(
            landing_pad_dimension=landing_pad_dimension,
            landing_pad_spacing=part_data.landing_dims.spacing_inside,
            part_dimension=part_dimension,
            clearance=silkscreenOffset,
            stroke_width=self.global_config.silk_line_width,
            has_orientation=bool(series_data.has_orientation),
        ):
            kicad_mod.append(elem)

        # Create copper elements
        for elem in self.create_pad_elements(
            landing_pad_dimension=landing_pad_dimension,
            landing_pad_spacing=part_data.landing_dims.spacing_inside,
            pad_shape=Pad.SHAPE_ROUNDRECT,
        ):
            kicad_mod.append(elem)

        # No variants, so we can just use the footprint name
        self.add_standard_3d_model_to_footprint(
            kicad_mod, series_data.library_name, kicad_mod.name
        )

        self.write_footprint(kicad_mod, series_data.library_name)

    @staticmethod
    def create_pad_elements(
        landing_pad_dimension: Vector2D, landing_pad_spacing: float, pad_shape: str
    ):
        return (
            Pad(
                number=pin_number,
                type=Pad.TYPE_SMT,
                shape=pad_shape,
                at=[position * (landing_pad_spacing + landing_pad_dimension.x) / 2, 0],
                size=landing_pad_dimension,
                layers=Pad.LAYERS_SMT,
            )
            for pin_number, position in enumerate((-1, 1), start=1)
        )

    @staticmethod
    def _create_silkscreen_elements(
        landing_pad_dimension: Vector2D,
        landing_pad_spacing: float,
        part_dimension: Vector2D,
        clearance: float,
        stroke_width: float,
        has_orientation: bool,
    ):
        # The silkscreen is drawn as a symmetrical rectangular shape. It has lines above and below the inductor and
        # lines drawn across the pads, omitting the pad copper area. Since it is symmetrical, only one corner coordinate
        # is required.
        silkscreen_corner = Vector2D(
            (part_dimension.x + 2 * clearance + stroke_width) / 2,
            (
                max(part_dimension.y, landing_pad_dimension.y)
                + 2 * clearance
                + stroke_width
            )
            / 2,
        )
        # Create silkscreen REF** and lines
        elements = [
            Property(
                name=Property.REFERENCE,
                text='REF**',
                at=[0, -max(landing_pad_dimension.y, part_dimension.y) / 2 - 1],
                layer='F.SilkS'),
            Line(  # Bottom line
                start=silkscreen_corner * (-1, 1),
                end=silkscreen_corner,
                layer="F.SilkS",
                width=stroke_width,
            ),
        ]

        # Create pin 1 marker if needed
        if has_orientation:
            # insert a pin 1 marker above the pad 1. Make a cutout of arrow_size + stroke_width to fit
            # the pin marker
            arrow_size = SilkArrowSize.MEDIUM  # The nominal arrow size
            # Adjust for the stroke width
            silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
                arrow_size, stroke_width
            )
            elements.append(
                Line(
                    start=-silkscreen_corner,
                    end=Vector2D(
                        -(
                            landing_pad_dimension.x
                            + landing_pad_spacing
                            + arrow_size.value
                            + stroke_width
                        )
                        / 2,
                        -silkscreen_corner.y,
                    ),
                    layer="F.SilkS",
                    width=stroke_width,
                )
            )

            elements.append(
                Line(
                    start=Vector2D(
                        -(
                            landing_pad_dimension.x
                            + landing_pad_spacing
                            - arrow_size.value
                            - stroke_width
                        )
                        / 2,
                        -silkscreen_corner.y,
                    ),
                    end=silkscreen_corner * (1, -1),
                    layer="F.SilkS",
                    width=stroke_width,
                )
            )

            elements.append(
                draw_triangle_pointing_south(
                    apex_position=Vector2D(
                        -(landing_pad_dimension.x + landing_pad_spacing) / 2,
                        -silkscreen_corner.y,
                    ),
                    size=silk_arrow_size,
                    length=silk_arrow_length,
                    layer="F.SilkS",
                    line_width_mm=stroke_width,
                )
            )
        else:
            # Draw uninterrupted top line if there is no marker
            elements.append(
                Line(
                    start=-silkscreen_corner,
                    end=silkscreen_corner * (1, -1),
                    layer="F.SilkS",
                    width=stroke_width,
                )
            )

        # If the part is smaller than the pad, no vertical lines are necessary.
        if part_dimension.y - clearance - stroke_width / 2 > landing_pad_dimension.y:
            # Draw vertical lines to the pads
            # This requires 4 lines, drawn upwards/downwards from each corner. Since the shape is symmetrical, we can
            # calculate the corners either via itertools.product() or directly as below
            for x, y in ((x, y) for x in (-1, 1) for y in (-1, 1)):
                elements.append(
                    Line(
                        start=(x, y) * silkscreen_corner,
                        end=[
                            x * silkscreen_corner.x,
                            y
                            * (
                                landing_pad_dimension.y / 2
                                + clearance
                                + stroke_width / 2
                            ),
                        ],
                        layer="F.SilkS",
                        width=stroke_width,
                    )
                )
        return elements

    @staticmethod
    def _create_courtyard_elements(
        landing_pad_dimension: Vector2D,
        landing_pad_spacing: float,
        part_dimension: Vector2D,
        grid: float,
        clearance: float,
        stroke_width: float,
    ):
        """
        The courtyard encloses both the part and its footprint. It is a rectangle drawn around the maximum dimension
        in both x- and y-direction.

        Parameters
        ----------
        grid: float
            The courtyard grid as per KLC F5.3
        clearance: float
            The courtyard clearance as per KLC F5.3

        Returns
        -------

        """
        # The maximum x- and y-coordinates. Hence, divide by 2.
        max_x, max_y = (
            max(landing_pad_spacing + (2 * landing_pad_dimension.x), part_dimension.x)
            / 2,
            max(landing_pad_dimension.y, part_dimension.y) / 2,
        )

        # Draw a rectangle around the part and its footprint staying on the courtyard grid as per KLC F5.3
        return (
            RectLine(
                start=[
                    roundGDown(-max_x - clearance, grid),
                    roundGDown(-max_y - clearance, grid),
                ],
                end=[
                    roundGUp(max_x + clearance, grid),
                    roundGUp(max_y + clearance, grid),
                ],
                layer="F.CrtYd",
                width=stroke_width,
            ),
        )

    @staticmethod
    def _create_fab_elements(
        landing_pad_dimension: Vector2D,
        landing_pad_spacing: float,
        part_dimension: Vector2D,
        ref_value: str,
        stroke_width: float,
        has_orientation: bool,
    ):
        # scale text size to match KLC F5.2
        text_size = clamp(landing_pad_dimension.x / 3, 0.5, 1)

        # Check if our part is so small that REF will overlap the pads. Rotate it to fit.
        rot = 90 if landing_pad_dimension.x + landing_pad_spacing < 2 else 0

        fab_rect = part_dimension / 2 + fabOffset
        elements = [
            Text(
                type="user",
                text="${REFERENCE}",
                at=[0, 0],
                rotation=rot,
                size=[text_size, text_size],
                thickness=text_size * 0.15,
                layer="F.Fab",
            ),
            # Fab ${value} placed below the footprint as per KLC F5.2
            # Calculate maximum size of the footprint in y-direction, add 1 mm and place the text there
            Property(
                name=Property.VALUE,
                text=ref_value,
                at=[0, max(landing_pad_dimension.y, part_dimension.y) / 2 + 1],
                layer="F.Fab",
            ),
        ]

        if has_orientation:
            # Part outline drawn as a rectangle with a chamfer applied to the top left corner and additionally a dash
            # to denote the orientation
            bevel_size = min(1, 0.25 * part_dimension.x, 0.25 * part_dimension.y)
            elements.extend(
                (
                    Line(
                        start=-fab_rect + bevel_size * Vector2D(1, 0),
                        end=fab_rect * (1, -1),
                        layer="F.Fab",
                        width=stroke_width,
                    ),
                    Line(
                        start=fab_rect * (1, -1),
                        end=fab_rect,
                        layer="F.Fab",
                        width=stroke_width,
                    ),
                    Line(
                        start=fab_rect,
                        end=fab_rect * (-1, 1),
                        layer="F.Fab",
                        width=stroke_width,
                    ),
                    Line(
                        start=fab_rect * (-1, 1),
                        end=-fab_rect + bevel_size * Vector2D(0, 1),
                        layer="F.Fab",
                        width=stroke_width,
                    ),
                    Line(
                        start=-fab_rect + bevel_size * Vector2D(0, 1),
                        end=-fab_rect + bevel_size * Vector2D(1, 0),
                        layer="F.Fab",
                        width=stroke_width,
                    ),
                    Line(
                        start=Vector2D(
                            -(landing_pad_dimension.x + landing_pad_spacing) / 2,
                            part_dimension.y * 0.4,
                        ),
                        end=Vector2D(
                            -(landing_pad_dimension.x + landing_pad_spacing) / 2,
                            part_dimension.y * -0.4,
                        ),
                        layer="F.Fab",
                        width=stroke_width,
                    ),
                )
            )
        else:
            # Part outline rectangle drawn on the fab layer
            elements.append(
                RectLine(
                    start=-fab_rect, end=fab_rect, width=stroke_width, layer="F.Fab"
                )
            )

        return elements


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Use .yaml files to create SMD inductor footprints."
    )

    parser.add_argument(
        "files",
        metavar="file",
        type=Path,
        nargs="+",
        help="list of files holding information about what devices should be created.",
    )
    # global_config is for backwards compatibility
    parser.add_argument(
        "--global-config",
        "--global_config",
        type=Path,
        nargs="?",
        help="the config file defining how the footprint will look like. (KLC)",
        default="../tools/global_config_files/config_KLCv3.0.yaml",
    )

    FootprintGenerator.add_standard_arguments(parser)

    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    global_config = GlobalConfig.load_from_file(args.global_config)

    generator = InductorGenerator(
        output_dir=args.output_dir, global_config=global_config
    )

    for data_file in args.files:
        with open(data_file, "r") as stream:
            data_loaded = yaml.safe_load(stream)
            csv_dir = data_file.parent
            generator.generate_all_series(data_loaded, csv_dir)
