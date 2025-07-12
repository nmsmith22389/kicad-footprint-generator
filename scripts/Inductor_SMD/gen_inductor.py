#!/usr/bin/env python3
# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

import argparse
import logging
import os
from pathlib import Path
from typing import Any
import yaml

from KicadModTree import Footprint, FootprintType, Line
from kilibs.declarative_defs.packages.smd_inductor_properties import (
    InductorSeriesProperties,
    SmdInductorProperties,
)
from kilibs.geom import Direction, Vector2D
from scripts.tools.drawing_tools_silk import SilkArrowSize
from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.nodes.layouts.n_pad_box_layout import (
    NPadBoxLayout,
    make_layout_for_smd_two_pad_dimensions,
)


class InductorGenerator(FootprintGenerator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_all_series(
        self, input_data: list[dict[str, Any]], csv_dir: Path
    ) -> None:

        # For each series block in the yaml file, process it
        for series_block in input_data:

            series_data = InductorSeriesProperties(series_block, csv_dir)

            for part_data in series_data.parts:
                self.generate_footprint(series_data, part_data)

    def generate_footprint(
        self, series_data: InductorSeriesProperties, part_data: SmdInductorProperties
    ) -> None:

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

        desc = [
            f"Inductor",
            series_data.manufacturer,
            part_data.part_number,
        ]

        if series_data.series_description:
            desc.append(f"{series_data.series_description} series")

        if series_data.additional_description:
            desc.append(series_data.additional_description)

        desc += [
            f"{part_data.width_x}x{part_data.length_y}x{part_data.height}mm",
            f"({datasheet_url})",
            self.global_config.get_generated_by_description(os.path.basename(__file__)),
        ]

        kicad_mod.description = ", ".join(desc)
        kicad_mod.tags = series_data.tags

        # For now, all supported inductors are two-pad SMD inductors,
        # but this is where we would dispatch to different layouts
        layout = make_layout_for_smd_two_pad_dimensions(
            global_config=self.global_config,
            pad_dims=part_data.landing_dims,
            body_size=part_dimension,
            silk_style=NPadBoxLayout.SilkStyle.BODY_RECT,
            is_polarized=series_data.has_orientation,
        )
        layout.silk_clearance = NPadBoxLayout.SilkClearance.KEEP_TOP_BOTTOM

        if part_dimension.min_val < 2:
            layout.silk_arrow_size = SilkArrowSize.SMALL
        else:
            layout.silk_arrow_size = SilkArrowSize.MEDIUM

        # We never want the arrow to point in from the left even if the pad
        # is entirely inside the body.
        layout.silk_arrow_direction_if_inside = Direction.SOUTH

        kicad_mod += layout

        # And add an extra fab orientation line if the inductor is polarized
        if series_data.has_orientation:
            # This will always produce a gap between the line and the body chamfer
            line_y = part_dimension.y * self.global_config.fab_bevel_size_relative

            # 10% of the way into the device, but don't let it get too close to the edge
            line_x = min(
                part_dimension.x * 0.4,
                part_dimension.x / 2 - self.global_config.fab_line_width * 2,
            )

            kicad_mod += Line(
                start=Vector2D.from_floats(-line_x, line_y),
                end=Vector2D.from_floats(-line_x, -line_y),
                width=self.global_config.fab_line_width,
                layer="F.Fab",
            )

        # No variants, so we can just use the footprint name
        self.add_standard_3d_model_to_footprint(
            kicad_mod, series_data.library_name, kicad_mod.name
        )

        self.write_footprint(kicad_mod, series_data.library_name)


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

    args = FootprintGenerator.add_standard_arguments(parser)

    generator = InductorGenerator(
        output_dir=args.output_dir, global_config=args.global_config
    )

    for data_file in args.files:
        with open(data_file, "r") as stream:
            data_loaded = yaml.safe_load(stream)
            csv_dir = data_file.parent
            generator.generate_all_series(data_loaded, csv_dir)
