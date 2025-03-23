#!/usr/bin/env python3

"""
Fiducial marking generator

@author Bence Csókás
"""

import argparse
from dataclasses import dataclass, asdict

from kilibs.geom import geometricCircle
from KicadModTree import *  # NOQA
from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.footprint_text_fields import addTextFields
from scripts.tools.global_config_files.global_config import GlobalConfig

class FiducialGenerator(FootprintGenerator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @dataclass
    class FPconfiguration():
        library_name: str
        fp_name: str
        # @param mask_diameter diameter of soldermask and F.Fab circle
        mask_diameter: float
        # @param marking_width diameter of marker circle or line width of cross
        marking_width: float
        # @param courtyard_offset extra radius around F.Fab circle for the courtyard
        courtyard_offset: float
        # @param variant sub-type eg. Cross
        variant: str
        # @param _variant sub-type prefixed with underscore eg. _Cross
        _variant: str
        # @param human_variant human-readable variant with commas eg. ', Cross variant'
        human_variant: str
        # @param description footprint description
        description: str
        # @param comment to be added to end of size description
        comment: str

        def __init__(self, spec: dict, global_config: GlobalConfig):
            self.library_name = spec.get("library", "Fiducial")
            self.fp_name = spec["fp_name"]
            self.mask_diameter = spec["mask_diameter"]
            self.marking_width = spec["marking_width"]
            self.setVariant(spec.get("variant", ""))
            self.comment = spec.get("comment", "")
            self.description = spec.get("description", "")
            self.courtyard_offset = spec.get('courtyard_offset',
                global_config.get_courtyard_offset(GlobalConfig.CourtyardType.DEFAULT))

        def setVariant(self, variant: str) -> dict:
            if variant:
                self.variant = variant
                self._variant = f"_{variant}"
                self.human_variant = f", {variant} variant"
            else:
                self.variant = self._variant = self.human_variant = ""

        def formatString(self, s: str) -> str:
            return s.format(**asdict(self))

        def getFootprintName(self) -> str:
            return self.formatString(self.fp_name)

        def getDescription(self) -> str:
            return self.formatString(self.description)

    def generateFootprint(self, spec: dict, pkg_id: str, header_info: dict):
        fp_config = self.FPconfiguration(spec, self.global_config)
        self.generateFootprintVariant(fp_config)

        for v in spec.get("variants", []):
            fp_config.setVariant(v)
            self.generateFootprintVariant(fp_config)

    def generateFootprintVariant(self, fp_config: FPconfiguration):
        # assemble footprint name
        fp_name = fp_config.getFootprintName()

        # information about what is generated
        print("  - %s" % fp_name)

        # create the footprint
        kicad_mod = Footprint(fp_name, FootprintType.SMD)
        kicad_mod.excludeFromBOM = True

        # set the FP description
        description = fp_config.getDescription()
        kicad_mod.description = description
        kicad_mod.tags = ["fiducial"]

        center = Vector2D(0, 0)

        # draw body outline on F.Fab
        radius = fp_config.mask_diameter / 2
        fab_outline = Circle(center=center, radius=radius, layer='F.Fab',
                     width=self.global_config.fab_line_width)
        kicad_mod.append(fab_outline)
        body_edges = geometricCircle(center=center, radius=radius).bounding_box

        # create Pad
        pad_radius = fp_config.marking_width / 2
        pad_clearance = radius - pad_radius
        pad = Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_CIRCLE, at=center,
              layers=['F.Cu', 'F.Mask'],
              size=fp_config.marking_width, solder_mask_margin=pad_clearance)
        kicad_mod.append(pad)

        # handle variants
        if fp_config.variant == "Cross":
            # cross in the middle

            # vertical: marking_width x mask_diameter
            r = Rect(start=[-pad_radius, -radius], end=[pad_radius, radius],
                 layer='F.Cu', width=0, fill=True)
            kicad_mod.append(r)

            # horizontal: mask_diameter x marking_width
            r = Rect(start=[-radius, -pad_radius], end=[radius, pad_radius],
                 layer='F.Cu', width=0, fill=True)
            kicad_mod.append(r)

        # calculate CourtYard
        cy_radius = radius + fp_config.courtyard_offset
        cy_outline = Circle(center=[0, 0], radius=cy_radius, layer='F.CrtYd',
                    width=self.global_config.courtyard_line_width)
        kicad_mod.append(cy_outline)
        courtyard = geometricCircle(center=center, radius=cy_radius).bounding_box

        # text fields
        addTextFields(kicad_mod, self.global_config, body_edges, courtyard, fp_name)

        lib_name = fp_config.library_name
        self.write_footprint(kicad_mod, lib_name)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='use config .yaml files to create footprints.')
    parser.add_argument(
        "files",
        metavar="file",
        type=str,
        nargs="*",
        help="list of files holding information about what devices should be created.",
    )
    args = FootprintGenerator.add_standard_arguments(parser)

    FootprintGenerator.run_on_files(FiducialGenerator, args)
