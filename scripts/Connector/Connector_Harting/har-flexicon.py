#! /usr/bin/env python3

import csv

from KicadModTree import *
from scripts.tools.global_config_files import global_config as GC

data = csv.DictReader(open("har-flexicon.csv"))

# Create footprint for all configurations
max_configurations = 12

lib_name = "Connector_Harting"
global_config = GC.DefaultGlobalConfig()

for series in data:
    for configuration in range(2, max_configurations + 1):

        # Setting footprint name
        vert = "Vertical" if series["vert"] == "True" else "Horizontal"

        footprint_name = (
            "Harting_har-flexicon_"
            + series["name_prefix"]
            + str(configuration).zfill(2)
            + series["name_suffix"]
            + "_1x"
            + str(configuration).zfill(2)
            + "-MP_P2.54mm_"
            + vert
        )

        # Init Kicad footprint properties
        kicad_mod = Footprint(footprint_name, FootprintType.SMD)
        kicad_mod.setDescription(
            "Harting har-flexicon series connector, "
            + series["name_prefix"]
            + str(configuration).zfill(2)
            + series["name_suffix"]
            + " ("
            + series["datasheet"]
            + "), generated with kicad-footprint-generator"
        )
        kicad_mod.setTags(
            "connector Harting har-flexicon "
            + ("vertical" if series["vert"] == "True" else "horizontal")
        )
        kicad_mod.append(
            Model(
                filename=global_config.model_3d_prefix + lib_name + ".3dshapes/"
                + footprint_name
                + global_config.model_3d_suffix
            )
        )

        # Basic dimensions from datasheet
        l = 2.54 * (configuration - 1)
        a = l + 7.85
        b = l / 2
        c = b + 4.15

        y_offset = float(series["anchor_offset"])
        kicad_modt = Translation(0, y_offset)
        kicad_mod.append(kicad_modt)

        # Guinding pin left/right spacing
        if series["gp"] == "True":
            gpl_spacing = float(series["gpl"])
            gpr_spacing = float(series["gpr"])

        courtyard_y_up = float(series["court_up"])
        courtyard_y_down = float(series["court_down"])

        fab_up = float(series["fab_up"])
        fab_down = float(series["fab_down"])

        # Connector pads
        kicad_modt.append(
            PadArray(
                start=[-b, 0],
                pincount=configuration,
                x_spacing=2.54,
                initial=1,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_RECT,
                size=[1.1, 6],
                layers=Pad.LAYERS_SMT,
            )
        )

        mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)

        # Mounting pads
        kicad_modt.append(
            Pad(
                number=mounting_pad_name,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_RECT,
                at=[-b - 2.54, 0],
                size=[1.1, 6],
                layers=Pad.LAYERS_SMT,
            )
        )
        kicad_modt.append(
            Pad(
                number=mounting_pad_name,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_RECT,
                at=[b + 2.54, 0],
                size=[1.1, 6],
                layers=Pad.LAYERS_SMT,
            )
        )

        # Draw Silkscreen layer
        # Draw dashed upper line
        for pins in range(-1, configuration):
            kicad_modt.append(
                Line(
                    start=[(2.54 * (pins - (configuration - 1) / 2)) + 0.762, fab_up-0.11],
                    end=[
                        (2.54 * (pins - (configuration - 1) / 2)) + 0.762 + 1.016,
                        fab_up-0.11,
                    ],
                    layer="F.SilkS",
                    width=global_config.silk_line_width,
                )
            )

        # Draw vertical lines
        kicad_modt.append(
            Line(
                start=[-a / 2-0.11, fab_up-0.11],
                end=[-a / 2-0.11, fab_down+0.11],
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )
        kicad_modt.append(
            Line(
                start=[+a / 2+0.11, fab_up-0.11],
                end=[+a / 2+0.11, fab_down+0.11],
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )

        # If lower fab layer overlaps pads, draw dashed line otherwise draw straight line
        if fab_down < 3.302:
            for pins in range(-1, configuration):
                kicad_modt.append(
                    Line(
                        start=[
                            (2.54 * (pins - (configuration - 1) / 2)) + 0.762,
                            fab_down+0.11,
                        ],
                        end=[
                            (2.54 * (pins - (configuration - 1) / 2)) + 0.762 + 1.016,
                            fab_down+0.11,
                        ],
                        layer="F.SilkS",
                        width=global_config.silk_line_width,
                    )
                )
        else:
            kicad_modt.append(
                Line(
                    start=[+a / 2+0.11, fab_down+0.11],
                    end=[-a / 2-0.11, fab_down+0.11],
                    layer="F.SilkS",
                    width=global_config.silk_line_width,
                )
            )

        # Draw pin 1 Silkscreen indicator on courtyard border
        kicad_modt.append(
            Line(
                start=[-b - 0.55, courtyard_y_up],
                end=[-b + 0.55, courtyard_y_up],
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )

        # Guide pin holes
        if series["gp"] == "True":
            kicad_modt.append(
                Pad(
                    type=Pad.TYPE_NPTH,
                    shape=Pad.SHAPE_CIRCLE,
                    at=[-b - 1.27, gpl_spacing],
                    drill=1,
                    size=1,
                    layers=Pad.LAYERS_NPTH,
                )
            )
            kicad_modt.append(
                Pad(
                    type=Pad.TYPE_NPTH,
                    shape=Pad.SHAPE_CIRCLE,
                    at=[b + 1.27, gpr_spacing],
                    drill=1,
                    size=1,
                    layers=Pad.LAYERS_NPTH,
                )
            )

        # Minimal text references
        kicad_modt.append(
            Property(
                name=Property.REFERENCE,
                text="REF**",
                at=[0, courtyard_y_up - 1],
                layer="F.SilkS",
            )
        )
        kicad_modt.append(
            Property(
                name=Property.VALUE,
                text=footprint_name,
                at=[0, fab_down + 1],
                layer="F.Fab",
            )
        )
        kicad_modt.append(
            Text(
                type="user",
                text="${REFERENCE}",
                at=[0, 0],
                layer="F.Fab",
            )
        )

        # Draw Courtyard
        kicad_modt.append(
            RectLine(
                start=[-c, courtyard_y_up],
                end=[+c, courtyard_y_down],
                layer="F.CrtYd",
                width=global_config.courtyard_line_width
            )
        )

        # Draw Fabrication layer
        kicad_modt.append(
            RectLine(
                start=[-a / 2, fab_up],
                end=[+a / 2, fab_down],
                layer="F.Fab",
                width=global_config.fab_line_width,
            )
        )
        # Pin 1 arrow
        kicad_modt.append(
            PolygonLine(
                shape=[
                    [-b - 0.5, fab_down],
                    [-b, fab_down - 0.5],
                    [-b + 0.5, fab_down],
                ],
                layer="F.Fab",
                width=global_config.fab_line_width,
            )
        )

        # Save file
        lib = KicadPrettyLibrary(lib_name, None)
        lib.save(kicad_mod)
