from KicadModTree import *
import csv

data = csv.DictReader(open("har-flexicon.csv"))

# Create footprint for all configurations
max_configurations = 12

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

        # Init Kicad footprint
        kicad_mod = Footprint(footprint_name)
        kicad_mod.setDescription("har-flexicon")
        kicad_mod.setTags("example")

        # Basic dimensions
        l = 2.54 * (configuration - 1)
        a = l + 7.85
        b = l / 2
        c = b + 4.15

        # Guinding pin left/right spacing
        if series["gp"] == "True":
            gpl_spacing = float(series["gpl"])
            gpr_spacing = float(series["gpr"])

        courtyard_y_up = float(series["court_up"])
        courtyard_y_down = float(series["court_down"])

        fab_up = float(series["fab_up"])
        fab_down = float(series["fab_down"])

        # Pins pads
        for pins in range(0, configuration):
            kicad_mod.append(
                Pad(
                    number=pins + 1,
                    type=Pad.TYPE_SMT,
                    shape=Pad.SHAPE_RECT,
                    at=[2.54 * (pins - (configuration - 1) / 2), 0],
                    size=[1.1, 6],
                    layers=Pad.LAYERS_SMT,
                )
            )

        # Mounting pads
        kicad_mod.append(
            Pad(
                number="MP",
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_RECT,
                at=[-b - 2.54, 0],
                size=[1.1, 6],
                layers=Pad.LAYERS_SMT,
            )
        )
        kicad_mod.append(
            Pad(
                number="MP",
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_RECT,
                at=[b + 2.54, 0],
                size=[1.1, 6],
                layers=Pad.LAYERS_SMT,
            )
        )

        # Guide holes
        if series["gp"] == "True":
            kicad_mod.append(
                Pad(
                    type=Pad.TYPE_NPTH,
                    shape=Pad.SHAPE_CIRCLE,
                    at=[-b - 1.27, gpl_spacing],
                    drill=1,
                    size=1,
                    layers=Pad.LAYERS_NPTH,
                )
            )
            kicad_mod.append(
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
        kicad_mod.append(
            Text(type="reference", text="REF**", at=[0, 0], layer="F.SilkS")
        )
        kicad_mod.append(
            Text(type="value", text=footprint_name, at=[0, 0], layer="F.Fab")
        )

        # Draw Courtyard
        kicad_mod.append(
            RectLine(
                start=[-c, courtyard_y_up],
                end=[+c, courtyard_y_down],
                layer="F.CrtYd",
            )
        )

        # Draw Fabrication layer
        kicad_mod.append(
            RectLine(
                start=[-a / 2, courtyard_y_up + fab_up],
                end=[+a / 2, courtyard_y_down - fab_down],
                layer="F.Fab",
            )
        )
        kicad_mod.append(
            PolygoneLine(
                polygone=[
                    [-b - 0.5, courtyard_y_down - fab_down],
                    [-b, courtyard_y_down - fab_down - 0.5],
                    [-b + 0.5, courtyard_y_down - fab_down],
                ],
                layer="F.Fab",
            )
        )

        # Draw Silkscreen layer
        kicad_mod.append(
            RectLine(
                start=[-a / 2, courtyard_y_up + fab_up],
                end=[+a / 2, courtyard_y_down - fab_down],
                layer="F.SilkS",
            )
        )
        # Draw pin 1 Silkscreen indicator
        kicad_mod.append(
            PolygoneLine(
                polygone=[
                    [-c, courtyard_y_up + 1.27],
                    [-c, courtyard_y_up],
                    [-c + 1.27, courtyard_y_up],
                ],
                layer="F.SilkS",
            )
        )

        # Save file
        file_handler = KicadFileHandler(kicad_mod)
        file_handler.writeFile(footprint_name + ".kicad_mod")
