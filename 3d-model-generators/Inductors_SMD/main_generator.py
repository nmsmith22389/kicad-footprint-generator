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
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# * Copyright (c) 2015                                                       *
# *     Maurice https://launchpad.net/~easyw                                 *
# * Copyright (c) 2022                                                       *
# *     Update 2022                                                          *
# *     jmwright (https://github.com/jmwright)                               *
# *     Work sponsored by KiCAD Services Corporation                         *
# *          (https://www.kipro-pcb.com/)                                    *
# *                                                                          *
# * All trademarks within this guide belong to their legitimate owners.      *
# *                                                                          *
# *   This program is free software; you can redistribute it and/or modify   *
# *   it under the terms of the GNU General Public License (GPL)             *
# *   as published by the Free Software Foundation; either version 2 of      *
# *   the License, or (at your option) any later version.                    *
# *   for detail see the LICENCE text file.                                  *
# *                                                                          *
# *   This program is distributed in the hope that it will be useful,        *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *   GNU Library General Public License for more details.                   *
# *                                                                          *
# *   You should have received a copy of the GNU Library General Public      *
# *   License along with this program; if not, write to the Free Software    *
# *   Foundation, Inc.,                                                      *
# *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA           *
# *                                                                          *
# ****************************************************************************

__title__ = "make SMD inductors 3D models exported to STEP and VRML"
__author__ = "scripts: maurice; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import abc
import glob
import os
from pathlib import Path
from typing import Any

import cadquery as cq
import yaml

from _tools import add_license, cq_color_correct, export_tools, shaderColors
from exportVRML.export_part_to_VRML import export_VRML

from kilibs.declarative_defs.packages.smd_inductor_properties import (
    InductorSeriesProperties,
    SmdInductorProperties,
)
from kilibs.declarative_defs.packages.two_pad_dimensions import TwoPadDimensions

from .src.make_coil_model import DSectionFootAirCoreCoil


class Inductor3DProperties:
    """
    Class that represents the result of declarative (e.g. YAML) definitions of
    SMD inductor 3D properties
    """

    def __init__(self, data: dict[str, Any]):

        self.has_body: bool
        """Whether the inductor has a body or not (some are bare coils)"""
        self.body_color: str
        """Color of the body, if there is one"""
        self.pad_color: str
        """Color of the pads"""
        self.pad_thickness: float
        """Thickness of the pads"""
        self.body_type: int | str | None
        """Type of the body, if there is one"""
        self.corner_radius: float | None
        """Corner radius (parallel to the Z axis) of the body, if any"""
        self.top_fillet_radius: float | None
        """Top fillet radius (parallel to the XY plane) of the body, if any"""
        self.coil_color: str | None
        """Color of the coil, if drawn"""
        self.coil_style: int | None
        """Style of the coil, if drawn"""
        self.wire_dia: float
        """Diameter of the wire, if drawn"""

        self.has_body = data.get("has_body", True)
        self.coil_style = data.get("coil_style", None)

        if self.has_body:
            self.body_color = data.get("bodyColor", "black body")
            self.body_type = data.get("type", 1)
        else:
            self.body_type = None

        if self.coil_style is not None:
            self.coil_color = data.get("wireColor", "metal dark cu")
            self.wire_dia = data.get("wireDia", 0)
        else:
            self.coil_color = None
            self.wire_dia = 0

        self.pad_color = data.get("pinColor", "metal grey pins")
        self.pad_thickness = data.get("padThickness", 0.05)

        self.corner_radius = data.get("cornerRadius", None)
        self.top_fillet_radius = data.get("topFilletRadius", None)


def make_models(
    model_to_build: str | None = None,
    output_dir_prefix: str | None = None,
    enable_vrml: bool = True,
):
    """
    Main entry point into this generator.
    """

    if output_dir_prefix is None:
        print("ERROR: An output directory must be provided.")
        return

    # model_to_build can be 'all', or a specific YAML file
    # find yaml files here, need to figure out the path to do so

    inductorPath = os.path.dirname(os.path.realpath(__file__))
    allYamlFiles = glob.glob(f"{inductorPath}/../../data/Inductor_SMD/*.yaml")

    if not allYamlFiles:
        print("No YAML files found to process.")
        return

    fileList = []

    if model_to_build != "all":
        for yamlFile in allYamlFiles:
            basefilename = os.path.splitext(os.path.basename(yamlFile))[0]
            if basefilename == model_to_build:
                fileList = [yamlFile]  # The file list will be just 1 item, our specific
                break

    # 2 possibilities now - fileList is a single file that we found,
    # or fileList is empty (didn't find file, or building all)

    # Trying to build a specific file and it was not found
    if model_to_build != "all" and not fileList:
        print(f"Could not find YAML for model {model_to_build}")
        return
    elif model_to_build == "all":
        fileList = allYamlFiles

    generator = SmdInductorGenerator(Path(output_dir_prefix))

    print(f"Files to process : {fileList}")

    for yamlFile in fileList:
        with open(yamlFile, "r") as stream:
            print(f"Processing file {yamlFile}")
            data_loaded = yaml.safe_load(stream)

            csv_dir = Path(yamlFile).parent

            # For each series block in the yaml file, we process the CSV
            for series_block in data_loaded:
                generator.generate_series(series_block, csv_dir)


class SmdInductorGenerator:

    output_prefix: Path

    def __init__(self, output_prefix: Path):
        self.output_prefix = output_prefix

    def generate_series(self, series_block: dict[str, Any], csv_dir: Path):
        series_data = InductorSeriesProperties(series_block, csv_dir)

        if "3d" not in series_block:
            # This series does not have 3D properties
            # (presumably a footprint-only definition)
            return

        # Construct an 3D properties object, which will use defaults
        # if not given
        series_3d_props = Inductor3DProperties(series_block["3d"])

        for part_data in series_data.parts:
            self._generate_model(series_data, series_3d_props, part_data)

    def _generate_model(
        self,
        series_data: InductorSeriesProperties,
        series_3d_props: Inductor3DProperties,
        part_data: SmdInductorProperties,
    ):

        # Used to wrap all the parts into an assembly
        component = cq.Assembly()
        # Add the parts to the assembly
        pins = None
        if series_3d_props.has_body:

            model_builder: InductorModelBuilder

            # Dispatch the body type to the appropriate function
            if series_3d_props.body_type in (1, 2):
                model_builder = CubicInductorBuilder(part_data, series_3d_props)
            elif series_3d_props.body_type == "shielded_drum_rounded_rectangular_base":
                model_builder = ShieldedDrumModelBuilder(part_data, series_3d_props)
            else:
                raise ValueError(f"Invalid body_type: {series_3d_props.body_type}")

            case, pins = model_builder.build()

            stepBodyColor = shaderColors.named_colors[
                series_3d_props.body_color
            ].getDiffuseFloat()

            component.add(
                case,
                color=cq_color_correct.Color(
                    stepBodyColor[0], stepBodyColor[1], stepBodyColor[2]
                ),
            )

        if series_3d_props.coil_style is not None:
            aCoil = DSectionFootAirCoreCoil(part_data, series_3d_props)
            (
                coil,
                pins,
            ) = aCoil.make_coil()

            stepCoilColor = shaderColors.named_colors[
                series_3d_props.coil_color
            ].getDiffuseFloat()
            component.add(
                coil,
                color=cq_color_correct.Color(
                    stepCoilColor[0], stepCoilColor[1], stepCoilColor[2]
                ),
            )

        stepPinColor = shaderColors.named_colors[
            series_3d_props.pad_color
        ].getDiffuseFloat()

        if pins is not None:
            component.add(
                pins,
                color=cq_color_correct.Color(
                    stepPinColor[0], stepPinColor[1], stepPinColor[2]
                ),
            )

        # Assemble the filename
        file_name = f"L_{series_data.manufacturer}_{part_data.part_number}"

        output_dir = os.path.join(
            self.output_prefix, (series_data.library_name + ".3dshapes")
        )
        # Create the output directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the assembly to STEP
        component.name = file_name
        component.save(
            os.path.join(output_dir, file_name + ".step"),
            cq.exporters.ExportTypes.STEP,
            mode=cq.exporters.assembly.ExportModes.FUSED,
            write_pcurves=False,
        )

        # Check for a proper union
        export_tools.check_step_export_union(component, output_dir, file_name)

        # Do STEP post-processing
        export_tools.postprocess_step(component, output_dir, file_name)

        # Export the assembly to VRML
        # Dec 2022- do not use CadQuery VRML export, it scales/uses inches.
        PartList = []
        ColorList = []
        if series_3d_props.has_body:
            PartList.append(case)
            ColorList.append(series_3d_props.body_color)
        if series_3d_props.coil_style is not None:
            PartList.append(coil)
            ColorList.append(series_3d_props.coil_color)
        if pins is not None:
            PartList.append(pins)
            ColorList.append(series_3d_props.pad_color)
        export_VRML(
            os.path.join(output_dir, file_name + ".wrl"),
            PartList,
            ColorList,
        )

        # Update the license
        add_license.addLicenseToStep(
            output_dir,
            file_name + ".step",
            add_license.LIST_int_license,
            add_license.STR_int_licAuthor,
            add_license.STR_int_licEmail,
            add_license.STR_int_licOrgSys,
            add_license.STR_int_licPreProc,
        )


def build_pins(
    pin_dims: TwoPadDimensions, pad_thickness: float, body_width: float | None
) -> cq.Workplane:
    """
    Build two simple rectangular pins based on the given dimensions.

    Parameters:
        - pin_dims: TwoPadDimensions object containing the dimensions of the pins.
        - pad_thickness: Thickness of the pads (in z)
        - body_width: Width of the body, used to adjust pin positions if necessary.
    """
    pin1 = (
        cq.Workplane("XY")
        .box(
            pin_dims.size_inline,
            pin_dims.size_crosswise,
            pad_thickness,
            (True, True, False),
        )
        .translate((-pin_dims.spacing_centre / 2, 0, 0))
    )
    pin2 = (
        cq.Workplane("XY")
        .box(
            pin_dims.size_inline,
            pin_dims.size_crosswise,
            pad_thickness,
            (True, True, False),
        )
        .translate((pin_dims.spacing_centre / 2, 0, 0))
    )

    # If the body and pins are the same, bump the pins out a bit so they are definitely visible
    if body_width is not None and abs(body_width - pin_dims.spacing_outside) < 0.01:
        translateAmount = 0.01
        pin1 = pin1.translate((-translateAmount, 0, 0))
        pin2 = pin2.translate((translateAmount, 0, 0))

    return pin1.union(pin2)


class InductorModelBuilder(abc.ABC):
    """
    Abstract base class for building inductor models.
    """

    def __init__(
        self, part_data: SmdInductorProperties, series_3d_props: Inductor3DProperties
    ):
        self.part_data = part_data
        self.series_3d_props = series_3d_props

    @abc.abstractmethod
    def build(self) -> tuple[cq.Workplane, cq.Workplane]:
        """
        Build the inductor model and return the case and pins.
        """
        pass


class CubicInductorBuilder(InductorModelBuilder):

    def __init__(
        self,
        part_data: SmdInductorProperties,
        series_3d_props: Inductor3DProperties,
    ):
        super().__init__(part_data, series_3d_props)

    def build(self) -> tuple[cq.Workplane, cq.Workplane]:

        # Physical dimensions
        widthX = self.part_data.width_x
        lengthY = self.part_data.length_y
        height = self.part_data.height
        landing = self.part_data.landing_dims
        pad_dims = self.part_data.device_pad_dims
        # Handy debug section to help copy/paste into CQ-editor to play with design
        if False:
            print(f"widthX = {widthX}")
            print(f"lengthY = {lengthY}")
            print(f"height = {height}")
            print(f"padX = {pad_dims.size_inline}")
            print(f"padY = {pad_dims.size_crosswise}")
            print(f"landingX = {landing.size_inline}")
            print(f"landingY = {landing.size_crosswise}")
            print(f"seriesType = {series_3d_props.body_type}")
            print(f"seriesPadThickness = {series_3d_props.pad_thickness}")
            print(f"seriesCornerRadius = {series_3d_props.corner_radius}")
        rotation = 0
        case = cq.Workplane("XY").box(widthX, lengthY, height, (True, True, False))

        corner_fillet_radius = self.part_data.corner_radius

        if corner_fillet_radius is None:
            corner_fillet_radius = self.series_3d_props.corner_radius

        if corner_fillet_radius is None:
            # If no corner fillet radius, the default is 5%
            corner_fillet_radius = min(lengthY, widthX) / 20

        if corner_fillet_radius > 0:
            case = case.edges("|Z").fillet(corner_fillet_radius)

        top_fillet_radius = self.part_data.top_fillet_radius

        if top_fillet_radius is None:
            top_fillet_radius = self.series_3d_props.top_fillet_radius

        if top_fillet_radius is None:
            # If no top fillet radius, the default is 5%
            top_fillet_radius = min(lengthY, widthX) / 20

        if top_fillet_radius > 0:
            case = case.edges(">Z").fillet(top_fillet_radius)

        if self.series_3d_props.body_type == 2:  # Exposed "wings"
            pad_thickness = min(3, height * 0.3)
        else:
            pad_thickness = self.series_3d_props.pad_thickness

        pins = build_pins(pad_dims, pad_thickness, widthX)
        case = case.cut(pins)

        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

        return case, pins


class ShieldedDrumModelBuilder(InductorModelBuilder):

    def __init__(
        self,
        part_data: SmdInductorProperties,
        series_3d_props: Inductor3DProperties,
    ):
        super().__init__(part_data, series_3d_props)

    def build(self) -> tuple[cq.Workplane, cq.Workplane]:
        # Required model parameters
        assert (
            self.part_data.core_diameter is not None
            and self.part_data.corner_radius is not None
        )

        # Create a baseplate for the inductor to rest on
        baseplate = (
            cq.Workplane("XY")
            .box(
                self.part_data.width_x,
                self.part_data.length_y,
                1.2,
                (True, True, False),
            )
            .edges("|Z")
            .chamfer(
                (
                    self.part_data.length_y
                    - self.part_data.device_pad_dims.size_crosswise
                )
                / 2
            )
        )

        # Create the shield that encases the inductor. Start with a cuboid with rounded edges.
        shield = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=1.2)
            .box(
                self.part_data.width_x,
                self.part_data.length_y,
                self.part_data.height - 1.2,
                (True, True, False),
            )
            .edges("|Z")
            .fillet(self.part_data.corner_radius)
        )
        # Drill a hole in the center and four more into the corners
        # This is a guess and was measured for the MSS110 series
        drill_hole_diam = self.part_data.corner_radius
        shield = (
            shield.faces(">Z")
            .workplane()
            .cboreHole(
                self.part_data.core_diameter + 0.75,
                cboreDiameter=self.part_data.core_diameter + 1.25,
                cboreDepth=0.25,
            )
            .moveTo(0, 0)
            .rect(
                0.5**0.5 * (self.part_data.core_diameter + 0.75),
                0.5**0.5 * (self.part_data.core_diameter + 0.75),
                centered=True,
                forConstruction=True,
            )
            .vertices()
            .cboreHole(
                drill_hole_diam, cboreDiameter=drill_hole_diam + 0.5, cboreDepth=0.25
            )
        )

        # Add a cap that goes on top of the inductor located in the center.
        # The cap is 0.5 mm in diameter larger than the core, but has a chamfer of 0.5 mm to make it the same size on
        # top. There is also 0.75/2 mm clearance between the cap and the shield filled with glue.
        shield = shield.union(
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=1.2)
            .circle((self.part_data.core_diameter + 0.75) / 2)
            .extrude(self.part_data.height - 1.2 - 0.5)
            .faces(">Z")
            .workplane()
            .circle(self.part_data.core_diameter / 2)
            .workplane(offset=0.5)
            .circle((self.part_data.core_diameter - 1) / 2)
            .loft()
        )
        # We neither draw the actual inductor nor its core. So we are done.
        # Merge the baseplate with the shield
        case = shield.union(baseplate)

        # Create the pins
        pins = build_pins(
            self.part_data.device_pad_dims,
            self.series_3d_props.pad_thickness,
            self.part_data.width_x,
        )

        case = case.cut(pins)

        return case, pins
