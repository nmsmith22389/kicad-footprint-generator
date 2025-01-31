#!/usr/bin/env python3


import argparse
import logging
import math

import yaml
from tools import (
    addCircleLF,
    addHDLineWithKeepout,
    addHLineWithKeepout,
    addKeepoutRect,
    addKeepoutRound,
    addRectAngledBottom,
    addRectAngledTop,
    addRectAngledTopNoBottom,
    addVDLineWithKeepout,
    addVLineWithKeepout,
    round_to_grid,
    roundCrt,
)

from KicadModTree import (
    Arc,
    Circle,
    Footprint,
    FootprintType,
    Line,
    Pad,
    Property,
    RectLine,
    Text,
    Translation,
)
from scripts.tools.footprint_generator import FootprintGenerator


class ConfigurationConstants:
    """Class grouping KLC footprint constants"""

    def __init__(self, configuration: dict):
        self.courtyard_offset: float = configuration["courtyard_offset"]["default"]
        self.silk_fab_offset: float = (
            0.12  # XYZ TODO change to: configuration["silk_fab_offset"]
        )
        self.silk_pad_clearance: float = (
            0.15  # XYZ TODO change to: configuration["silk_pad_clearance"] and change in the code to additionally subtract half the width of the silkscreen line
        )
        self.fab_line_width: float = configuration["fab_line_width"]
        self.courtyard_line_width: float = configuration["courtyard_line_width"]
        self.silk_line_width: float = configuration["silk_line_width"]
        self.text_offset: float = 1


class CommonToPackage:
    """Class for properties common to both types of TO packages"""

    def __init__(self, device_params: dict, pkg_id: str):
        try:
            self.pins: int = device_params["number_of_pins"]
            self.pad_dimensions: list[float] = device_params["pad_dimensions_xy"]
            self.drill: float = device_params["pad_hole_diameter"]
        except Exception as e:
            msg = f"Error in '{pkg_id}': Parameter '{e.args[0]}' must be provided!"
            print("\n" + msg + "\n")
            raise KeyError(msg)

        self.name_base: str = ""
        self.additional_tags: list[str] = device_params.get("additional_tags", [])
        self.fpnametags = []
        self.webpage: str = device_params.get("size_source", "")
        self.additional_package_names: list[str] = device_params.get(
            "additional_package_names", []
        )
        self.manufacturer = device_params.get("manufacturer", "")
        self.part_number = device_params.get("part_number", "")
        self.device_type = device_params.get("device_type", "")

        if "device_type" in device_params:
            self.name_base = device_params["device_type"] + "-" + f"{self.pins}"
        else:
            self.name_base = pkg_id

    def init_footprint(self, description: str, tags: list[str], name: str):
        fp = Footprint(name, FootprintType.THT)
        fp.setDescription(description)
        fp.tags = tags
        return fp


class RectangularToPackage(CommonToPackage):
    """Class for properties of rectangular shaped TO packages"""

    def __init__(self, device_params: dict, pkg_id: str):
        super().__init__(device_params, pkg_id)
        try:
            self.plastic_dimensions: list[float] = device_params["plastic_dimensions_xyz"]  # fmt: skip
            self.pitch: float = device_params["pitch"]
        except Exception as e:
            msg = f"Error in '{pkg_id}': Parameter '{e.args[0]}' must be provided!"
            print("\n" + msg + "\n")
            raise KeyError(msg)

        self.metal_dimensions: list[float] = device_params.get(
            "metal_dimensions_xyz", [0, 0, 0]
        )
        self.metal_offset_x: float = device_params.get(
            "metal_offset_x", 0
        )  # offset of metal from left
        self.mounting_hole_position: list[int] = device_params.get(
            "mounting_hole_position", [0, 0]
        )
        self.mounting_hole_diameter: float = device_params.get(
            "mounting_hole_diameter_on_package", 0
        )
        self.mounting_hole_drill: float = device_params.get(
            "mounting_hole_diameter_on_pcb", 0
        )
        self.pin_min_length_before_90deg_bend: float = device_params.get(
            "pin_min_length_before_90deg_bend", 0
        )
        self.pin_width_height: list[float] = device_params.get(
            "pin_width_height", [0, 0]
        )
        self.pin_offset_x: float = 0
        self.pin_offset_z: float = device_params.get("pin_offset_z", 0)
        self.additional_pin_pad_position: list[float] = device_params.get(
            "additional_pin_pad_position", []
        )
        self.additional_pin_pad_position_size: list[float] = device_params.get(
            "additional_pin_pad_position_size", []
        )
        self.plastic_angled: list[float] = device_params.get("plastic_angled", [])
        self.metal_angled: list[float] = device_params.get("metal_angled", [])

        self.generate_footprint_type: int = device_params.get("generate_footprint_type")
        self.staggered_pitch: list[float] = device_params.get("staggered_pitch")
        self.pitch_list: list[float] = device_params.get("pitch_list", [])

        if self.pitch_list:
            self.pin_spread = sum(self.pitch_list)
        else:
            self.pin_spread = (self.pins - 1) * self.pitch
        self.pin_offset_x = (self.plastic_dimensions[0] - self.pin_spread) / 2

        # If pads are too wide, make them narrower for non-staggered devices
        if "staggered_pitch" not in device_params:
            self.pad_dimensions[0] = min(self.pad_dimensions[0], 0.75 * self.pitch)

    def init_footprint(self, orientation: str, modifier: str, staggered_type: int, config: dict):
        description, tags, name = self._get_descr_tags_fpname(
            orientation, modifier, staggered_type, config
        )
        return super().init_footprint(description, tags, name)

    def _get_descr_tags_fpname(
        self, orientation: str, modifier: str, staggered_type: int, config: dict
    ):
        # Tags
        tags = [
            self.name_base,
            orientation,
            f"RM {self.pitch}mm",
        ] + self.additional_tags
        fpnametags = self.fpnametags
        if staggered_type == 1:
            tags.append("staggered type-1")
            fpnametags = ["StaggeredType1"] + fpnametags
        elif staggered_type == 2:
            tags.append("staggered type-2")
            fpnametags = ["StaggeredType2"] + fpnametags

        # Description
        description = self.name_base
        for tag in tags[1:]:
            description += ", " + tag
        if self.webpage:
            description += ", see " + self.webpage

        # Footprint name
        if staggered_type > 0:
            name_format = config["fp_name_to_tht_staggered_format_string_no_trailing_zero"]
            if orientation == "Vertical":
                pitch_y = self.staggered_pitch[0]
                lead = pitch_y - self.plastic_dimensions[2] + self.pin_offset_z
            else:
                pitch_y = self.staggered_pitch[1]
                lead = pitch_y + self.pin_min_length_before_90deg_bend
            footprint_name = name_format.format(
                man = self.manufacturer,
                mpn = self.part_number,
                pkg = self.device_type,
                pincount = self.pins,
                pitch_x = 2*self.pitch,
                pitch_y = pitch_y,
                parity = "Odd" if staggered_type == 1 else "Even",
                lead = lead,
                orientation = orientation if orientation == "Vertical" else modifier,
            ).replace("__", "_").lstrip("_")
        else:
            footprint_name = self.name_base
            if orientation == "Horizontal" and self.additional_pin_pad_position_size:
                footprint_name += "-1EP"
            for t in self.additional_package_names:
                footprint_name += "_" + t
            footprint_name += "_" + orientation
            if modifier:
                footprint_name += "_" + modifier
            for t in fpnametags:
                footprint_name += "_" + t
        return description, tags, footprint_name


class RoundToPackage(CommonToPackage):
    """Class for properties of round shaped TO packages"""

    def __init__(self, device_params: dict, pkg_id: str):
        super().__init__(device_params, pkg_id)
        try:
            self.pin_circle_diameter: float = device_params["pin_circle_diameter"]
            self.diameter_inner: float = device_params[
                "diameter_inner"
            ]  # diameter of top can
            self.diameter_outer: float = device_params[
                "diameter_outer"
            ]  # diameter of bottom can
        except Exception as e:
            msg = f"Error in '{pkg_id}': Parameter '{e.args[0]}' must be provided!"
            print("\n" + msg + "\n")
            raise KeyError(msg)

        self.mark_width: float = device_params.get("mark_width", 0)
        self.mark_length: float = device_params.get("mark_length", 0)
        self.pin1_angle: float = device_params.get("pin1_angle", 180)
        self.angle_between_pins: float = device_params.get(
            "angle_between_pins", -90 if self.pins == 3 else -360 / self.pins
        )
        self.mark_angle: float = device_params.get("mark_angle", self.pin1_angle + 45)
        self.window_diameter: float = device_params.get("window_diameter", 0)
        self.deleted_pins: list[int] = device_params.get("deleted_pins", [])

    def init_footprint(self, footprint_type: str):
        description, tags, name = self._get_descr_tags_fpname(footprint_type)
        return super().init_footprint(description, tags, name)

    def _get_descr_tags_fpname(self, footprint_type: str):
        # Tags
        name = self.name_base
        tags = []
        if footprint_type == "window" or footprint_type == "lens":
            name += "_" + footprint_type.capitalize()
            tags.append(footprint_type.capitalize())

        # Footprint name
        for t in self.additional_package_names:
            name += "_" + t
        for t in self.fpnametags:
            name += "_" + t

        # Description
        tags = (
            [name] + tags + self.additional_tags
        )  # XYZ TODO: change back to: self.name_base
        description = name  # XYZ TODO: change back to: self.name_base
        for t in tags[1:]:
            description += ", " + t
        if self.webpage:
            description += ", see " + self.webpage

        return description, tags, name


class TOGenerator(FootprintGenerator):
    def __init__(self, configuration, **kwargs):
        super().__init__(**kwargs)
        self.configuration = configuration
        self.configuration_constants = ConfigurationConstants(configuration)

    def save_footprint(self, fp: Footprint):
        self.add_standard_3d_model_to_footprint(fp, "Package_TO_SOT_THT", fp.name)
        self.write_footprint(fp, "Package_TO_SOT_THT")

    def generateFootprint(
        self, device_params: dict, pkg_id: str, header_info: dict = None
    ):
        footprint_type = device_params.get("generate_footprint_type", [])

        if isinstance(footprint_type, str):
            footprint_type = footprint_type.replace(" ", "")
            footprint_type = footprint_type.split(",")

        if "plastic_dimensions_xyz" in device_params:
            pkg = RectangularToPackage(device_params, pkg_id)
            if "vertical" in footprint_type:
                self.generate_rect_to_fp_vertical(pkg, pkg_id)
            if "horizontal" in footprint_type:
                self.generate_rect_to_fp_horizontal_tab_down(pkg, pkg_id)
                self.generate_rect_to_fp_horizontal_tab_up(pkg, pkg_id)
            if "vertical-odd" in footprint_type:
                self.generate_rect_to_fp_vertical(pkg, pkg_id, 1)
            if "vertical-even" in footprint_type:
                self.generate_rect_to_fp_vertical(pkg, pkg_id, 2)
            if "horizontal-odd" in footprint_type:
                self.generate_rect_to_fp_horizontal_tab_down(pkg, pkg_id, 1)
            if "horizontal-even" in footprint_type:
                self.generate_rect_to_fp_horizontal_tab_down(pkg, pkg_id, 2)
        elif "diameter_inner" in device_params:
            pkg = RoundToPackage(device_params, pkg_id)
            for type in footprint_type:
                self.generate_round_to_fp(pkg, pkg_id, type)

    def generate_rect_to_fp_vertical(
        self, pkg: RectangularToPackage, pkg_id: str, staggered_type: int = 0
    ):
        fp = pkg.init_footprint("Vertical", "", staggered_type, self.configuration)
        c = self.configuration_constants

        left_fab_plastic = -pkg.pin_offset_x
        top_fab_plastic = -pkg.pin_offset_z
        width_fab_plastic = pkg.plastic_dimensions[0]
        height_fab_plastic = pkg.plastic_dimensions[2]
        width_fab_metal = pkg.metal_dimensions[0]
        height_fab_metal = pkg.metal_dimensions[2]

        left_silk_plastic = left_fab_plastic - c.silk_fab_offset
        top_silk_plastic = top_fab_plastic - c.silk_fab_offset
        width_silk_plastic = width_fab_plastic + 2 * c.silk_fab_offset
        height_silk_plastic = height_fab_plastic + 2 * c.silk_fab_offset
        width_silk_metal = width_fab_metal + 2 * c.silk_fab_offset
        height_silk_metal = height_fab_metal + 2 * c.silk_fab_offset
        x_mount_hole = left_fab_plastic + pkg.mounting_hole_position[0]
        x_text = left_silk_plastic + max(width_silk_plastic, width_silk_metal) / 2

        # calculate pad positions
        pads = []
        yshift = 0
        y1 = 0
        y2 = 0
        y_pins_max = 0
        if staggered_type:
            if staggered_type == 1:
                y1 = pkg.staggered_pitch[0]
                yshift = -pkg.staggered_pitch[0]
            else:
                y2 = pkg.staggered_pitch[0]
            y_pins_max = pkg.staggered_pitch[0]

        leftop_crt = (
            min(-pkg.pad_dimensions[0] / 2, left_fab_plastic) - c.courtyard_offset
        )
        top_crt = min(-pkg.pad_dimensions[1] / 2, top_fab_plastic) - c.courtyard_offset
        widtheight_crt = (
            max(
                max(width_fab_plastic, width_fab_metal),
                pkg.pin_spread + pkg.pad_dimensions[0],
            )
            + 2 * c.courtyard_offset
        )
        heightop_crt = max(
            top_fab_plastic
            + max(height_fab_plastic, height_fab_metal)
            + c.courtyard_offset
            - top_crt,
            -top_crt + y_pins_max + pkg.pad_dimensions[1] / 2 + c.courtyard_offset,
        )

        y = y1
        x = 0
        for p in range(pkg.pins):
            y = y2 if p % 2 else y1
            pads.append((x, y))
            if pkg.pitch_list and p < len(pkg.pitch_list):
                x += pkg.pitch_list[p]
            else:
                x += pkg.pitch

        fpt = Translation(0, yshift)
        fp.append(fpt)

        # set general values
        fpt.append(
            Property(
                name=Property.REFERENCE,
                text="REF**",
                at=[x_text, top_silk_plastic - c.text_offset],
                layer="F.SilkS",
            )
        )
        fpt.append(
            Text(
                text="${REFERENCE}",
                at=[x_text, top_silk_plastic - c.text_offset],
                layer="F.Fab",
            )
        )
        fpt.append(
            Property(
                name=Property.VALUE,
                text=fp.name,
                at=[
                    x_text,
                    top_silk_plastic
                    + max(
                        height_silk_metal,
                        height_silk_plastic,
                        -top_silk_plastic + heightop_crt + top_crt,
                    )
                    + c.text_offset,
                ],
                layer="F.Fab",
            )
        )

        # create FAB layer
        fpt.append(
            RectLine(
                start=[left_fab_plastic, top_fab_plastic],
                end=[
                    left_fab_plastic + width_fab_plastic,
                    top_fab_plastic + height_fab_plastic,
                ],
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )
        if pkg.metal_dimensions[2] > 0:
            fpt.append(
                Line(
                    start=[left_fab_plastic, top_fab_plastic + height_fab_metal],
                    end=[
                        left_fab_plastic + width_fab_plastic,
                        top_fab_plastic + height_fab_metal,
                    ],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )
            if pkg.mounting_hole_diameter > 0:
                fpt.append(
                    Line(
                        start=[
                            x_mount_hole - pkg.mounting_hole_diameter / 2,
                            top_fab_plastic,
                        ],
                        end=[
                            x_mount_hole - pkg.mounting_hole_diameter / 2,
                            top_fab_plastic + height_fab_metal,
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )
                fpt.append(
                    Line(
                        start=[
                            x_mount_hole + pkg.mounting_hole_diameter / 2,
                            top_fab_plastic,
                        ],
                        end=[
                            x_mount_hole + pkg.mounting_hole_diameter / 2,
                            top_fab_plastic + height_fab_metal,
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )
        else:
            if pkg.mounting_hole_diameter > 0:
                fpt.append(
                    Line(
                        start=[
                            x_mount_hole - pkg.mounting_hole_diameter / 2,
                            top_fab_plastic,
                        ],
                        end=[
                            x_mount_hole - pkg.mounting_hole_diameter / 2,
                            top_fab_plastic + height_fab_plastic,
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )
                fpt.append(
                    Line(
                        start=[
                            x_mount_hole + pkg.mounting_hole_diameter / 2,
                            top_fab_plastic,
                        ],
                        end=[
                            x_mount_hole + pkg.mounting_hole_diameter / 2,
                            top_fab_plastic + height_fab_plastic,
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )
        for p in range(len(pads)):
            yl1 = top_fab_plastic + height_fab_plastic
            yl2 = pads[p][1]
            if yl2 > yl1:
                fpt.append(
                    Line(
                        start=[pads[p][0], yl1],
                        end=[pads[p][0], yl2],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )

        # create silkscreen layer
        keepouts = []
        for p in range(len(pads)):
            if p == 0:
                keepouts = keepouts + addKeepoutRect(
                    pads[p][0],
                    pads[p][1],
                    pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance,
                    pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance,
                )
            else:
                keepouts = keepouts + addKeepoutRound(
                    pads[p][0],
                    pads[p][1],
                    pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance,
                    pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance,
                )

        addHLineWithKeepout(
            fpt,
            left_silk_plastic,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addHLineWithKeepout(
            fpt,
            left_silk_plastic,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic + height_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            left_silk_plastic,
            top_silk_plastic,
            top_silk_plastic + height_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic,
            top_silk_plastic + height_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        if pkg.metal_dimensions[2] > 0:
            addHLineWithKeepout(
                fpt,
                left_silk_plastic,
                left_silk_plastic + width_silk_plastic,
                top_silk_plastic + height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            if pkg.mounting_hole_diameter > 0:
                addVLineWithKeepout(
                    fpt,
                    x_mount_hole - pkg.mounting_hole_diameter / 2,
                    top_silk_plastic,
                    top_silk_plastic + height_silk_metal,
                    "F.SilkS",
                    c.silk_line_width,
                    keepouts,
                )
                addVLineWithKeepout(
                    fpt,
                    x_mount_hole + pkg.mounting_hole_diameter / 2,
                    top_silk_plastic,
                    top_silk_plastic + height_silk_metal,
                    "F.SilkS",
                    c.silk_line_width,
                    keepouts,
                )
        else:
            if pkg.mounting_hole_diameter > 0:
                addVLineWithKeepout(
                    fpt,
                    x_mount_hole - pkg.mounting_hole_diameter / 2,
                    top_silk_plastic,
                    top_silk_plastic + height_silk_plastic,
                    "F.SilkS",
                    c.silk_line_width,
                    keepouts,
                )
                addVLineWithKeepout(
                    fpt,
                    x_mount_hole + pkg.mounting_hole_diameter / 2,
                    top_silk_plastic,
                    top_silk_plastic + height_silk_plastic,
                    "F.SilkS",
                    c.silk_line_width,
                    keepouts,
                )
        for p in range(len(pads)):
            yl1 = top_silk_plastic + height_silk_plastic
            yl2 = pads[p][1]
            if yl2 > yl1:
                addVLineWithKeepout(
                    fpt,
                    pads[p][0],
                    yl1,
                    yl2,
                    "F.SilkS",
                    c.silk_line_width,
                    keepouts,
                )

        # create courtyard
        fp.append(
            RectLine(
                start=[roundCrt(leftop_crt), roundCrt(top_crt + yshift)],
                end=[
                    roundCrt(leftop_crt + widtheight_crt),
                    roundCrt(top_crt + heightop_crt + yshift),
                ],
                layer="F.CrtYd",
                width=c.courtyard_line_width,
            )
        )

        # create pads
        for p in range(len(pads)):
            if p == 0:
                fpt.append(
                    Pad(
                        number=p + 1,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_RECT,
                        at=pads[p],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )
            else:
                fpt.append(
                    Pad(
                        number=p + 1,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_OVAL,
                        at=pads[p],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )

        self.save_footprint(fp)

    def generate_rect_to_fp_horizontal_tab_down(
        self, pkg: RectangularToPackage, pkg_id: str, staggered_type: int = 0
    ):
        fp = pkg.init_footprint("Horizontal", "TabDown", staggered_type, self.configuration)
        c = self.configuration_constants

        left_fab_plastic = -pkg.pin_offset_x
        top_fab_plastic = -pkg.pin_min_length_before_90deg_bend
        width_fab_plastic = pkg.plastic_dimensions[0]
        height_fab_plastic = pkg.plastic_dimensions[1]
        width_fab_metal = pkg.metal_dimensions[0]
        height_fab_metal = pkg.metal_dimensions[1]

        left_silk_plastic = left_fab_plastic - c.silk_fab_offset
        top_silk_plastic = top_fab_plastic + c.silk_fab_offset
        width_silk_plastic = width_fab_plastic + 2 * c.silk_fab_offset
        height_silk_plastic = height_fab_plastic + 2 * c.silk_fab_offset
        width_silk_metal = width_fab_metal + 2 * c.silk_fab_offset
        height_silk_metal = height_fab_metal + 2 * c.silk_fab_offset
        x_mount_hole = left_fab_plastic + pkg.mounting_hole_position[0]
        y_mount_hole = top_fab_plastic - pkg.mounting_hole_position[1]

        # calculate pad positions
        pads = []
        yshift = 0
        y1 = 0
        y2 = 0
        maxpiny = 0
        if staggered_type == 1:
            y1 = pkg.staggered_pitch[1]
            yshift = -pkg.staggered_pitch[1]
            y2 = 0
            maxpiny = pkg.staggered_pitch[1]
        elif staggered_type == 2:
            y1 = 0
            yshift = 0
            y2 = pkg.staggered_pitch[1]
            maxpiny = pkg.staggered_pitch[1]

        y = y1
        x = 0
        for p in range(1, pkg.pins + 1):
            if (p % 2) == 1:
                y = y1
            else:
                y = y2
            pads.append([x, y])
            if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
                x += pkg.pitch_list[p - 1]
            else:
                x += pkg.pitch

        addpad = 0
        leftop_crt = (
            min(-pkg.pad_dimensions[0] / 2, left_fab_plastic) - c.courtyard_offset
        )
        top_crt = (
            top_fab_plastic
            - max(height_fab_plastic, height_fab_metal)
            - c.courtyard_offset
        )
        height_crt = (
            -top_crt + maxpiny + pkg.pad_dimensions[1] / 2
        ) + c.courtyard_offset
        if len(pkg.additional_pin_pad_position_size) > 0:
            height_crt = height_crt + (
                pkg.additional_pin_pad_position[1]
                + pkg.additional_pin_pad_position_size[1] / 2
                - height_fab_metal
            )
            top_crt = top_crt - (
                pkg.additional_pin_pad_position[1]
                + pkg.additional_pin_pad_position_size[1] / 2
                - height_fab_metal
            )
            addpad = pkg.additional_pin_pad_position_size[0]
            addpadx = left_fab_plastic + pkg.additional_pin_pad_position[0]
            addpady = top_fab_plastic - pkg.additional_pin_pad_position[1]
        width_crt = (
            max(
                max(
                    max(width_fab_plastic, width_fab_metal),
                    pkg.pin_spread + pkg.pad_dimensions[0],
                ),
                addpad,
            )
            + 2 * c.courtyard_offset
        )

        txt_x = left_silk_plastic + max(width_silk_plastic, width_silk_metal) / 2
        txt_t = (
            top_silk_plastic - max(height_silk_metal, height_silk_plastic)
        ) - c.text_offset
        txt_b = maxpiny + pkg.pad_dimensions[1] / 2 + c.text_offset
        if len(pkg.additional_pin_pad_position_size) > 0:
            txt_t = txt_t - (
                pkg.additional_pin_pad_position[1]
                + pkg.additional_pin_pad_position_size[1] / 2
                - height_fab_metal
            )

        fpt = Translation(0, yshift)
        fp.append(fpt)

        # set general values
        fpt.append(
            Property(
                name=Property.REFERENCE,
                text="REF**",
                at=[txt_x, txt_t],
                layer="F.SilkS",
            )
        )
        fpt.append(Text(text="${REFERENCE}", at=[txt_x, txt_t], layer="F.Fab"))
        fpt.append(
            Property(
                name=Property.VALUE,
                text=fp.name,
                at=[txt_x, txt_b],
                layer="F.Fab",
            )
        )

        # create FAB layer
        if height_fab_metal > 0:
            if len(pkg.plastic_angled) > 0:
                if len(pkg.metal_angled) > 0:
                    addRectAngledTopNoBottom(
                        fpt,
                        [
                            left_fab_plastic + pkg.metal_offset_x,
                            top_fab_plastic
                            - height_fab_plastic
                            + pkg.plastic_angled[1],
                        ],
                        [
                            left_fab_plastic + pkg.metal_offset_x + width_fab_metal,
                            top_fab_plastic - height_fab_metal,
                        ],
                        pkg.metal_angled,
                        "F.Fab",
                        c.fab_line_width,
                    )
                else:
                    fpt.append(
                        RectLine(
                            start=[
                                left_fab_plastic + pkg.metal_offset_x,
                                top_fab_plastic
                                - height_fab_plastic
                                - pkg.plastic_angled[1],
                            ],
                            end=[
                                left_fab_plastic + pkg.metal_offset_x + width_fab_metal,
                                top_fab_plastic - height_fab_metal,
                            ],
                            layer="F.Fab",
                            width=c.fab_line_width,
                        )
                    )
            else:
                if len(pkg.metal_angled) > 0:
                    addRectAngledTop(
                        fpt,
                        [
                            left_fab_plastic + pkg.metal_offset_x,
                            top_fab_plastic - height_fab_plastic,
                        ],
                        [
                            left_fab_plastic + pkg.metal_offset_x + width_fab_metal,
                            top_fab_plastic - height_fab_metal,
                        ],
                        pkg.metal_angled,
                        "F.Fab",
                        c.fab_line_width,
                    )
                else:
                    fpt.append(
                        RectLine(
                            start=[
                                left_fab_plastic + pkg.metal_offset_x,
                                top_fab_plastic - height_fab_plastic,
                            ],
                            end=[
                                left_fab_plastic + pkg.metal_offset_x + width_fab_metal,
                                top_fab_plastic - height_fab_metal,
                            ],
                            layer="F.Fab",
                            width=c.fab_line_width,
                        )
                    )

        if len(pkg.plastic_angled) > 0:
            addRectAngledTop(
                fpt,
                [left_fab_plastic, top_fab_plastic],
                [
                    left_fab_plastic + width_fab_plastic,
                    top_fab_plastic - height_fab_plastic,
                ],
                pkg.plastic_angled,
                "F.Fab",
                c.fab_line_width,
            )
        else:
            fpt.append(
                RectLine(
                    start=[left_fab_plastic, top_fab_plastic],
                    end=[
                        left_fab_plastic + width_fab_plastic,
                        top_fab_plastic - height_fab_plastic,
                    ],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )
        if pkg.mounting_hole_diameter > 0:
            fpt.append(
                Circle(
                    center=[x_mount_hole, y_mount_hole],
                    radius=pkg.mounting_hole_diameter / 2,
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )

        for p in range(len(pads)):
            fpt.append(
                Line(
                    start=[pads[p][0], top_fab_plastic],
                    end=[pads[p][0], pads[p][1]],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )

        # create silkscreen layer
        keepouts = []
        for p in range(len(pads)):
            if p == 0:
                keepouts = keepouts + addKeepoutRect(
                    pads[p][0],
                    pads[p][1],
                    pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance,
                    pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance,
                )
            else:
                keepouts = keepouts + addKeepoutRound(
                    pads[p][0],
                    pads[p][1],
                    pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance,
                    pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance,
                )

        if len(pkg.additional_pin_pad_position_size) > 0:
            keepouts.append(
                [
                    addpadx
                    - pkg.additional_pin_pad_position_size[0] / 2
                    - c.silk_pad_clearance,
                    addpadx
                    + pkg.additional_pin_pad_position_size[0] / 2
                    + c.silk_pad_clearance,
                    addpady
                    - pkg.additional_pin_pad_position_size[1] / 2
                    - c.silk_pad_clearance,
                    addpady
                    + pkg.additional_pin_pad_position_size[1] / 2
                    + c.silk_pad_clearance,
                ]
            )

        addHLineWithKeepout(
            fpt,
            left_silk_plastic,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        if height_fab_metal > 0:
            addHLineWithKeepout(
                fpt,
                left_silk_plastic,
                left_silk_plastic + width_silk_plastic,
                top_silk_plastic - height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVLineWithKeepout(
                fpt,
                left_silk_plastic,
                top_silk_plastic,
                top_silk_plastic - height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVLineWithKeepout(
                fpt,
                left_silk_plastic + width_silk_plastic,
                top_silk_plastic,
                top_silk_plastic - height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
        else:
            addHLineWithKeepout(
                fpt,
                left_silk_plastic,
                left_silk_plastic + width_silk_plastic,
                top_silk_plastic - height_silk_plastic,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVLineWithKeepout(
                fpt,
                left_silk_plastic,
                top_silk_plastic,
                top_silk_plastic - height_silk_plastic,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVLineWithKeepout(
                fpt,
                left_silk_plastic + width_silk_plastic,
                top_silk_plastic,
                top_silk_plastic - height_silk_plastic,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )

        for p in range(len(pads)):
            addVLineWithKeepout(
                fpt,
                pads[p][0],
                top_silk_plastic,
                pads[p][1],
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )

        # create courtyard
        fp.append(
            RectLine(
                start=[roundCrt(leftop_crt), roundCrt(top_crt + yshift)],
                end=[
                    roundCrt(leftop_crt + width_crt),
                    roundCrt(top_crt + height_crt + yshift),
                ],
                layer="F.CrtYd",
                width=c.courtyard_line_width,
            )
        )

        # create mounting hole
        if pkg.mounting_hole_drill > 0:
            fpt.append(
                Pad(
                    type=Pad.TYPE_NPTH,
                    shape=Pad.SHAPE_OVAL,
                    at=[x_mount_hole, y_mount_hole],
                    size=[pkg.mounting_hole_drill, pkg.mounting_hole_drill],
                    drill=pkg.mounting_hole_drill,
                    layers=Pad.LAYERS_THT,
                )
            )

        if len(pkg.additional_pin_pad_position_size) > 0:
            fpt.append(
                Pad(
                    number=pkg.pins + 1,
                    type=Pad.TYPE_SMT,
                    shape=Pad.SHAPE_RECT,
                    at=[addpadx, addpady],
                    size=pkg.additional_pin_pad_position_size,
                    drill=0,
                    layers=Pad.LAYERS_SMT,
                )
            )

        # create pads
        for p in range(len(pads)):
            if p == 0:
                fpt.append(
                    Pad(
                        number=p + 1,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_RECT,
                        at=pads[p],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )
            else:
                fpt.append(
                    Pad(
                        number=p + 1,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_OVAL,
                        at=pads[p],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )

        self.save_footprint(fp)

    def generate_rect_to_fp_horizontal_tab_up(
        self, pkg: RectangularToPackage, pkg_id: str
    ):
        if pkg.additional_pin_pad_position:
            logging.info(
                f"{pkg_id}: Cannot create 'horizontal tab up' version of a package with additional pin pad."
            )
            return

        fp = pkg.init_footprint("Horizontal", "TabUp", 0, self.configuration)
        c = self.configuration_constants

        left_fab_plastic = -pkg.pin_offset_x
        top_fab_plastic = pkg.pin_min_length_before_90deg_bend
        width_fab_plastic = pkg.plastic_dimensions[0]
        height_fab_plastic = pkg.plastic_dimensions[1]

        width_fab_metal = pkg.metal_dimensions[0]
        height_fab_metal = pkg.metal_dimensions[1]

        left_silk_plastic = left_fab_plastic - c.silk_fab_offset
        top_silk_plastic = top_fab_plastic - c.silk_fab_offset
        width_silk_plastic = width_fab_plastic + 2 * c.silk_fab_offset
        height_silk_plastic = height_fab_plastic + 2 * c.silk_fab_offset
        width_silk_metal = width_fab_metal + 2 * c.silk_fab_offset
        height_silk_metal = height_fab_metal + 2 * c.silk_fab_offset

        leftop_crt = (
            min(-pkg.pad_dimensions[0] / 2, left_fab_plastic) - c.courtyard_offset
        )
        top_crt = -pkg.pad_dimensions[1] / 2 - c.courtyard_offset
        width_crt = (
            max(
                max(width_fab_plastic, width_fab_metal),
                pkg.pin_spread + pkg.pad_dimensions[0],
            )
            + 2 * c.courtyard_offset
        )
        height_crt = (
            -top_crt
            + top_fab_plastic
            + max(height_fab_plastic, height_fab_metal)
            + c.courtyard_offset
        )

        x_mount_hole = left_fab_plastic + pkg.mounting_hole_position[0]
        y_mount_hole = top_fab_plastic + pkg.mounting_hole_position[1]

        txt_x = left_silk_plastic + max(width_silk_plastic, width_silk_metal) / 2
        txt_t = (
            top_silk_plastic + max(height_silk_metal, height_silk_plastic)
        ) + c.text_offset
        txt_b = -pkg.pad_dimensions[1] / 2 - c.text_offset

        # set general values
        fp.append(
            Property(
                name=Property.REFERENCE,
                text="REF**",
                at=[txt_x, txt_t],
                layer="F.SilkS",
            )
        )
        fp.append(Text(text="${REFERENCE}", at=[txt_x, txt_t], layer="F.Fab"))
        fp.append(
            Property(
                name=Property.VALUE,
                text=fp.name,
                at=[txt_x, txt_b],
                layer="F.Fab",
            )
        )

        if height_fab_metal > 0:
            if len(pkg.metal_angled) > 0:
                addRectAngledBottom(
                    fp,
                    [
                        left_fab_plastic + pkg.metal_offset_x,
                        top_fab_plastic + height_fab_plastic,
                    ],
                    [
                        left_fab_plastic + pkg.metal_offset_x + width_fab_metal,
                        top_fab_plastic + height_fab_metal,
                    ],
                    pkg.metal_angled,
                    "F.Fab",
                    c.fab_line_width,
                )
            else:
                fp.append(
                    RectLine(
                        start=[
                            left_fab_plastic + pkg.metal_offset_x,
                            top_fab_plastic + height_fab_plastic,
                        ],
                        end=[
                            left_fab_plastic + pkg.metal_offset_x + width_fab_metal,
                            top_fab_plastic + height_fab_metal,
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )

        if len(pkg.plastic_angled) > 0:
            addRectAngledBottom(
                fp,
                [left_fab_plastic, top_fab_plastic],
                [
                    left_fab_plastic + width_fab_plastic,
                    top_fab_plastic + height_fab_plastic,
                ],
                pkg.plastic_angled,
                "F.Fab",
                c.fab_line_width,
            )
        else:
            fp.append(
                RectLine(
                    start=[left_fab_plastic, top_fab_plastic],
                    end=[
                        left_fab_plastic + width_fab_plastic,
                        top_fab_plastic + height_fab_plastic,
                    ],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )

        if pkg.mounting_hole_diameter > 0:
            fp.append(
                Circle(
                    center=[x_mount_hole, y_mount_hole],
                    radius=pkg.mounting_hole_diameter / 2,
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )
        x = 0
        for p in range(1, pkg.pins + 1):
            fp.append(
                Line(
                    start=[x, top_fab_plastic],
                    end=[x, 0],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )
            if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
                x = x + pkg.pitch_list[p - 1]
            else:
                x = x + pkg.pitch

        # create silkscreen layer
        keepouts = []
        x = 0
        for p in range(1, pkg.pins + 1):
            if p == 1:
                keepouts = keepouts + addKeepoutRect(
                    x,
                    0,
                    pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance,
                    pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance,
                )
            else:
                keepouts = keepouts + addKeepoutRound(
                    x,
                    0,
                    pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance,
                    pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance,
                )
            x = x + pkg.pitch

        addHLineWithKeepout(
            fp,
            left_silk_plastic,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addHLineWithKeepout(
            fp,
            left_silk_plastic,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic + height_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fp,
            left_silk_plastic,
            top_silk_plastic,
            top_silk_plastic + height_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fp,
            left_silk_plastic + width_silk_plastic,
            top_silk_plastic,
            top_silk_plastic + height_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        if height_fab_metal > 0:
            addHDLineWithKeepout(
                fp,
                left_silk_plastic + pkg.metal_offset_x,
                10 * c.silk_line_width,
                left_silk_plastic + pkg.metal_offset_x + width_silk_metal,
                top_silk_plastic + height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVDLineWithKeepout(
                fp,
                left_silk_plastic + pkg.metal_offset_x,
                top_silk_plastic + height_silk_plastic + c.silk_line_width * 2,
                10 * c.silk_line_width,
                top_silk_plastic + height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVDLineWithKeepout(
                fp,
                left_silk_plastic + pkg.metal_offset_x + width_silk_metal,
                top_silk_plastic + height_silk_plastic + c.silk_line_width * 2,
                10 * c.silk_line_width,
                top_silk_plastic + height_silk_metal,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
        x = 0
        for p in range(1, pkg.pins + 1):
            addVLineWithKeepout(
                fp,
                x,
                top_silk_plastic,
                pkg.pad_dimensions[1] / 2 + c.silk_pad_clearance,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
                x += pkg.pitch_list[p - 1]
            else:
                x += pkg.pitch

        # create courtyard
        fp.append(
            RectLine(
                start=[roundCrt(leftop_crt), roundCrt(top_crt)],
                end=[roundCrt(leftop_crt + width_crt), roundCrt(top_crt + height_crt)],
                layer="F.CrtYd",
                width=c.courtyard_line_width,
            )
        )

        # create mounting hole
        if pkg.mounting_hole_drill > 0:
            fp.append(
                Pad(
                    type=Pad.TYPE_NPTH,
                    shape=Pad.SHAPE_OVAL,
                    at=[x_mount_hole, y_mount_hole],
                    size=[pkg.mounting_hole_drill, pkg.mounting_hole_drill],
                    drill=pkg.mounting_hole_drill,
                    layers=Pad.LAYERS_THT,
                )
            )

        # create pads
        x = 0
        for p in range(1, pkg.pins + 1):
            if p == 1:
                fp.append(
                    Pad(
                        number=p,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_RECT,
                        at=[x, 0],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )
            else:
                fp.append(
                    Pad(
                        number=p,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_OVAL,
                        at=[x, 0],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )
            if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
                x += pkg.pitch_list[p - 1]
            else:
                x += pkg.pitch

        self.save_footprint(fp)

    def generate_round_to_fp(
        self, pkg: RoundToPackage, pkg_id: str, footprint_type: str
    ):
        fp = pkg.init_footprint(footprint_type)
        c = self.configuration_constants

        d_fab = pkg.diameter_outer
        d_slk = pkg.diameter_outer + 2 * c.silk_fab_offset

        # calculate pad positions
        pads = []
        yshift = 0
        xshift = 0
        a = pkg.pin1_angle
        firstPin = True
        for p in range(1, pkg.pins + 1):
            x = pkg.pin_circle_diameter / 2 * math.cos(a / 180 * math.pi)
            y = pkg.pin_circle_diameter / 2 * math.sin(a / 180 * math.pi)
            a += pkg.angle_between_pins
            if p in pkg.deleted_pins:
                continue
            pads.append([x, y])
            if firstPin:
                xshift = -x
                yshift = -y
                firstPin = False

        txt_t = -d_slk / 2 - c.text_offset
        txt_b = d_slk / 2 + c.text_offset

        fpt = Translation(xshift, yshift)
        fp.append(fpt)

        # set general values
        fpt.append(
            Property(
                name=Property.REFERENCE, text="REF**", at=[0, txt_t], layer="F.SilkS"
            )
        )
        fpt.append(Text(text="${REFERENCE}", at=[0, txt_t], layer="F.Fab"))
        fpt.append(
            Property(name=Property.VALUE, text=fp.name, at=[0, txt_b], layer="F.Fab")
        )

        # create FAB layer
        fpt.append(
            Circle(
                center=[0, 0],
                radius=pkg.diameter_inner / 2,
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )
        if pkg.mark_width > 0 and pkg.mark_length > 0:
            a = pkg.mark_angle
            da = math.asin(pkg.mark_width / d_fab) / math.pi * 180
            a1 = a + da
            a2 = a - da
            x1 = [
                (pkg.diameter_outer / 2) * math.cos(a1 / 180 * math.pi),
                (pkg.diameter_outer / 2) * math.sin(a1 / 180 * math.pi),
            ]
            x3 = [
                (pkg.diameter_outer / 2) * math.cos(a2 / 180 * math.pi),
                (pkg.diameter_outer / 2) * math.sin(a2 / 180 * math.pi),
            ]
            dx1 = (pkg.mark_length) * math.cos(a / 180 * math.pi)
            dx2 = (pkg.mark_length) * math.sin(a / 180 * math.pi)
            x2 = [x1[0] + dx1, x1[1] + dx2]
            x4 = [x3[0] + dx1, x3[1] + dx2]
            minx = min(x2[0], x4[0])
            miny = min(x2[1], x4[1])
            fpt.append(
                Arc(
                    center=[0, 0],
                    start=x1,
                    angle=(360 - 2 * da),
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )
            fpt.append(
                Line(start=x1, end=x2, angle=0, layer="F.Fab", width=c.fab_line_width)
            )
            fpt.append(
                Line(start=x2, end=x4, angle=0, layer="F.Fab", width=c.fab_line_width)
            )
            fpt.append(
                Line(start=x4, end=x3, angle=0, layer="F.Fab", width=c.fab_line_width)
            )
        else:
            fpt.append(
                Circle(
                    center=[0, 0],
                    radius=pkg.diameter_outer / 2,
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )
        if footprint_type == "window" or footprint_type == "lens":
            addCircleLF(
                fpt,
                [0, 0],
                pkg.window_diameter / 2,
                "F.Fab",
                c.fab_line_width,
                4 * c.fab_line_width,
            )

        # create silkscreen layer
        if pkg.mark_width > 0 and pkg.mark_length > 0:
            a = pkg.mark_angle
            da = (
                math.asin((pkg.mark_width + 2 * c.silk_fab_offset) / d_slk)
                / math.pi
                * 180
            )
            a1 = a + da
            a2 = a - da
            x1 = [
                (d_slk / 2) * math.cos(a1 / 180 * math.pi),
                (d_slk / 2) * math.sin(a1 / 180 * math.pi),
            ]
            x3 = [
                (d_slk / 2) * math.cos(a2 / 180 * math.pi),
                (d_slk / 2) * math.sin(a2 / 180 * math.pi),
            ]
            dx1 = (pkg.mark_length + c.silk_fab_offset) * math.cos(a / 180 * math.pi)
            dx2 = (pkg.mark_length + c.silk_fab_offset) * math.sin(a / 180 * math.pi)
            x2 = [x1[0] + dx1, x1[1] + dx2]
            x4 = [x3[0] + dx1, x3[1] + dx2]
            fpt.append(
                Arc(
                    center=[0, 0],
                    start=x1,
                    angle=(360 - 2 * da),
                    layer="F.SilkS",
                    width=c.silk_line_width,
                )
            )
            fpt.append(
                Line(
                    start=x1, end=x2, angle=0, layer="F.SilkS", width=c.silk_line_width
                )
            )
            fpt.append(
                Line(
                    start=x2, end=x4, angle=0, layer="F.SilkS", width=c.silk_line_width
                )
            )
            fpt.append(
                Line(
                    start=x4, end=x3, angle=0, layer="F.SilkS", width=c.silk_line_width
                )
            )
        else:
            fpt.append(
                Circle(
                    center=[0, 0],
                    radius=d_slk / 2,
                    layer="F.SilkS",
                    width=c.silk_line_width,
                )
            )

        if pkg.mark_width > 0 and pkg.mark_length > 0:
            fp.append(
                RectLine(
                    start=[
                        roundCrt(
                            xshift
                            + min(
                                minx - c.courtyard_offset,
                                -d_fab / 2 - c.courtyard_offset,
                            )
                        ),
                        roundCrt(
                            yshift
                            + min(
                                miny - c.courtyard_offset,
                                -d_fab / 2 - c.courtyard_offset,
                            )
                        ),
                    ],
                    end=[
                        roundCrt(xshift + d_fab / 2 + c.courtyard_offset),
                        roundCrt(yshift + d_fab / 2 + c.courtyard_offset),
                    ],
                    layer="F.CrtYd",
                    width=c.courtyard_line_width,
                )
            )
        else:
            fp.append(
                Circle(
                    center=[roundCrt(xshift), roundCrt(yshift)],
                    radius=roundCrt(d_fab / 2 + c.courtyard_offset),
                    layer="F.CrtYd",
                    width=c.courtyard_line_width,
                )
            )

        # create pads
        for p in range(len(pads)):
            if p == 0:
                fpt.append(
                    Pad(
                        number=p + 1,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_OVAL,
                        at=pads[p],
                        size=[
                            round_to_grid(pkg.pad_dimensions[0] * 1.3, 0.1),
                            pkg.pad_dimensions[1],
                        ],
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )
            else:
                fpt.append(
                    Pad(
                        number=p + 1,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_OVAL,
                        at=pads[p],
                        size=pkg.pad_dimensions,
                        drill=pkg.drill,
                        layers=Pad.LAYERS_THT,
                    )
                )

        self.save_footprint(fp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="use config .yaml files to create footprints."
    )
    parser.add_argument(
        "files",
        metavar="file",
        type=str,
        nargs="*",
        help="list of files holding information about what devices should be created.",
    )
    parser.add_argument(
        "--global_config",
        type=str,
        nargs="?",
        help="the config file defining how the footprint will look like. (KLC)",
        default="../../tools/global_config_files/config_KLCv3.0.yaml",
    )
    parser.add_argument('--naming_config', type=str, nargs='?',
                         help='the config file defining footprint naming.', default='../package_config_KLCv3.yaml')
    args = FootprintGenerator.add_standard_arguments(parser)

    with open(args.global_config, "r") as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.naming_config, "r") as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    FootprintGenerator.run_on_files(
        TOGenerator,
        args,
        file_autofind_dir="size_definitions",
        configuration=configuration,
    )
