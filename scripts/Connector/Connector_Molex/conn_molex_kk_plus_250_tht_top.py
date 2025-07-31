#!/usr/bin/env python3

# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>


from __future__ import annotations

from math import sqrt
import argparse
import yaml

from KicadModTree import *
from scripts.tools.drawing_tools import round_to_grid
from scripts.tools.footprint_text_fields import addTextFields  # type: ignore
from scripts.tools.global_config_files import global_config as GC
from kilibs.geom import Vec2DCompatible

from typing import Any, Dict, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # Stubs so Pylance can resolve the symbols that KicadModTree creates at runtime
    from KicadModTree import (
        Pad,
        PadArray,
        Footprint,
        FootprintType,
        RectLine,
        # Line,
        PolygonLine,
        Model,
        KicadPrettyLibrary,
    )


series = "KK-Plus-250"
series_long = "KK Plus 250 Connector System"
manufacturer = "Molex"
orientation = "V"
number_of_rows = 1
datasheet = "https://www.molex.com/content/dam/molex/molex-dot-com/en_us/pdf/product-reference-guides/987652-7774.pdf"

pitch = 2.50
hole_diam = 0.9  # from datasheet
start_pos_x = 0  # Where should pin 1 be located.
pad_to_pad_clearance = 1.0
max_annular_ring = 0.3  # How much copper should be in y direction?
min_annular_ring = 0.15

pad_size = [pitch - pad_to_pad_clearance, hole_diam + 2 * max_annular_ring]
if pad_size[0] - hole_diam < 2 * min_annular_ring:
    pad_size[0] = hole_diam + 2 * min_annular_ring
if pad_size[0] - hole_diam > 2 * max_annular_ring:
    pad_size[0] = hole_diam + 2 * max_annular_ring

pad_shape = Pad.SHAPE_OVAL
if pad_size[1] == pad_size[0]:
    pad_shape = Pad.SHAPE_CIRCLE

part_number_template = "20784300{n:02d}"


def generate_one_footprint(
    global_config: GC.GlobalConfig, pincount: int, configuration: Dict[str, Any]
) -> None:

    part_number = part_number_template.format(n=pincount)

    # handle arguments
    orientation_str = configuration["orientation_options"][orientation]
    footprint_name = configuration["fp_name_format_string"].format(
        man=manufacturer,
        series=series,
        mpn=part_number,
        num_rows=number_of_rows,
        pins_per_row=pincount,
        mounting_pad="",
        pitch=pitch,
        orientation=orientation_str,
    )

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    descr_format_str = "Molex {:s}, part number: {:s}, {:d} Pins ({:s}), generated with kicad-footprint-generator"
    kicad_mod.setDescription(
        descr_format_str.format(series_long, part_number, pincount, datasheet)
    )
    kicad_mod.setTags(
        configuration["keyword_fp_string"].format(
            series=series_long,
            orientation=orientation_str,
            man=manufacturer,
            entry=configuration["entry_direction"][orientation],
        )
    )

    # calculate working values
    end_pos_x = (pincount - 1) * pitch
    pin_center_x = (end_pos_x - start_pos_x) / 2.0
    silk_w = configuration["silk_line_width"]
    fab_w = configuration["fab_line_width"]
    nudge: float = silk_w / 2  # configuration["silk_fab_offset"]
    body_to_pin = 2.45  # from first/last pin to edge
    body_width = end_pos_x - start_pos_x + (2 * body_to_pin)
    body_height = 5.4  # from datasheet

    body_edge = {
        "left": start_pos_x - body_to_pin,
        "right": end_pos_x + body_to_pin,
        "bottom": 3.076,
    }
    body_edge["top"] = body_edge["bottom"] - body_height

    body_center_y = (body_edge["top"] + body_edge["bottom"]) / 2
    body_center = [pin_center_x, body_center_y]

    # ? create pads
    optional_pad_params: Dict[str, Any] = {}
    optional_pad_params["tht_pad1_shape"] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(
        PadArray(
            initial=1,
            start=[start_pos_x, 0],
            x_spacing=pitch,
            pincount=pincount,
            size=pad_size,
            drill=hole_diam,
            type=Pad.TYPE_THT,
            shape=pad_shape,
            layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params,
        )
    )

    # ? mounting peg hole (datasheet: Ø1.2 mm, centre -1.6 mm x, +1.6 mm y)
    kicad_mod.append(
        Pad(
            number="MP",
            type=Pad.TYPE_NPTH,
            shape=Pad.SHAPE_CIRCLE,
            at=[-1.6, 1.6],
            size=1.2,
            drill=1.2,
            layers=Pad.LAYERS_NPTH,
        )
    )

    # ? create fab outline
    kicad_mod.append(
        Rectangle(
            size=[body_width, body_height],
            center=body_center,
            layer="F.Fab",
            width=fab_w,
        )
    )

    # ? fab locking ramp
    # at top center of body
    lramp_width = 6.1
    lramp_height = 1.9

    kicad_mod.append(
        PolygonLine(
            shape=[
                {"x": pin_center_x - lramp_width / 2, "y": body_edge["top"]},
                {
                    "x": pin_center_x - lramp_width / 2,
                    "y": body_edge["top"] - lramp_height,
                },
                {
                    "x": pin_center_x + lramp_width / 2,
                    "y": body_edge["top"] - lramp_height,
                },
                {"x": pin_center_x + lramp_width / 2, "y": body_edge["top"]},
            ],
            layer="F.Fab",
            width=fab_w,
        )
    )

    # ? fab key slot
    kslot_width = 2.3
    kslot_height = 1.1

    if pincount <= 3:
        # ? for 2 & 3 pin the key slot is on bottom (bottom left corner)
        kslot_shape: list[Vec2DCompatible] = [
            {"x": body_edge["left"], "y": body_edge["bottom"]},
            {"x": body_edge["left"], "y": body_edge["bottom"] + kslot_height},
            {
                "x": body_edge["left"] + kslot_width,
                "y": body_edge["bottom"] + kslot_height,
            },
            {"x": body_edge["left"] + kslot_width, "y": body_edge["bottom"]},
        ]
    else:
        # ? for 4+ pin the key slot is on top (top left corner)
        kslot_shape = [
            {"x": body_edge["left"], "y": body_edge["top"]},
            {"x": body_edge["left"], "y": body_edge["top"] - kslot_height},
            {
                "x": body_edge["left"] + kslot_width,
                "y": body_edge["top"] - kslot_height,
            },
            {"x": body_edge["left"] + kslot_width, "y": body_edge["top"]},
        ]

    kicad_mod.append(
        PolygonLine(
            shape=kslot_shape,
            layer="F.Fab",
            width=fab_w,
        )
    )

    # create silkscreen
    kicad_mod.append(
        Rectangle(
            size=[body_width, body_height],
            offset=nudge,
            center=body_center,
            layer="F.SilkS",
            width=silk_w,
        )
    )

    # ? pin 1 markers
    marker_side_length = 1
    marker: Dict[str, float] = {
        "side_length": 1,
        "x_offset": -0.5 - (nudge / 2),
        "y_offset": 0,
    }
    marker["width"] = abs(marker["side_length"]) / sqrt(2)

    marker_coords: list[Vec2DCompatible] = [
        {
            "x": body_edge["left"] + marker["x_offset"] - marker["width"],
            "y": (-marker_side_length / 2) + marker["y_offset"],
        },
        {"x": body_edge["left"] + marker["x_offset"], "y": marker["y_offset"]},
        {
            "x": body_edge["left"] + marker["x_offset"] - marker["width"],
            "y": (marker_side_length / 2) + marker["y_offset"],
        },
    ]

    kicad_mod.append(
        # ? A small triangle pointing to pin 1 (to the right)
        Polygon(
            shape=marker_coords,
            layer="F.SilkS",
            width=silk_w,
            fill=True,
        )
    )

    sl = 1
    poly_pin1_marker: list[Vec2DCompatible] = [
        {"x": body_edge["left"], "y": -sl / 2},
        {"x": body_edge["left"] + sl / sqrt(2), "y": 0},
        {"x": body_edge["left"], "y": sl / 2},
    ]
    kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer="F.Fab", width=fab_w))

    # &########################## CrtYd #################################
    courtyard_grid: float = configuration["courtyard_offset"]["connector"]
    cx1 = round_to_grid(
        body_edge["left"] - courtyard_grid, configuration["courtyard_grid"]
    )
    cy1 = round_to_grid(
        body_edge["top"] - courtyard_grid, configuration["courtyard_grid"]
    )

    cx2 = round_to_grid(
        body_edge["right"] + courtyard_grid, configuration["courtyard_grid"]
    )
    cy2 = round_to_grid(
        body_edge["bottom"] + courtyard_grid, configuration["courtyard_grid"]
    )

    kicad_mod.append(
        RectLine(
            start=[cx1, cy1],
            end=[cx2, cy2],
            layer="F.CrtYd",
            width=configuration["courtyard_line_width"],
        )
    )

    # &######################## Text Fields ###############################
    addTextFields(
        kicad_mod=kicad_mod,
        configuration=configuration,
        body_edges=body_edge,
        courtyard={"top": cy1, "bottom": cy2},
        fp_name=footprint_name,
        text_y_inside_position="top",
    )

    # &#################### Output and 3d model ############################
    model3d_path_prefix = configuration.get(
        "3d_model_prefix", global_config.model_3d_prefix
    )
    model3d_path_suffix = configuration.get(
        "3d_model_suffix", global_config.model_3d_suffix
    )

    lib_name = configuration["lib_name_format_string"].format(
        series=series, man=manufacturer
    )
    model_name = "{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}".format(
        model3d_path_prefix=model3d_path_prefix,
        lib_name=lib_name,
        fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix,
    )
    kicad_mod.append(Model(filename=model_name))

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="use config .yaml files to create footprints."
    )
    parser.add_argument(
        "--global_config",
        type=str,
        nargs="?",
        help="the config file defining how the footprint will look like. (KLC)",
        default="../../tools/global_config_files/config_KLCv3.0.yaml",
    )
    parser.add_argument(
        "--series_config",
        type=str,
        nargs="?",
        help="the config file defining series parameters.",
        default="../conn_config_KLCv3.yaml",
    )
    args = parser.parse_args()
    configuration: Dict[str, Any] = {}
    global_config: Optional[GC.GlobalConfig] = None

    with open(args.global_config, "r") as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
            global_config = GC.GlobalConfig(configuration)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, "r") as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    assert global_config is not None, "global_config should have been initialised above"

    min_num_pins = 2
    max_num_pins = 8

    for pincount in range(min_num_pins, max_num_pins + 1):
        generate_one_footprint(global_config, pincount, configuration)
