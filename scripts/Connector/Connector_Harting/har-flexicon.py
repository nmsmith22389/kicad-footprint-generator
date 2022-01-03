from KicadModTree import *

# Create footprint for all configurations
max_configurations = 12
for configuration in range(2, max_configurations + 1):

    # Setting footprint name
    footprint_name = "flexicon" + str(configuration)

    # Init Kicad footprint
    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("har-flexicon")
    kicad_mod.setTags("example")

    # Basic dimensions
    l = 2.54 * (configuration - 1)
    a = l + 7.85
    b = l / 2
    c = b + 4.15

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
            at=[2.54 * (-1 - (configuration - 1) / 2), 0],
            size=[1.1, 6],
            layers=Pad.LAYERS_SMT,
        )
    )
    kicad_mod.append(
        Pad(
            number="MP",
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_RECT,
            at=[2.54 * ((configuration + 1) / 2), 0],
            size=[1.1, 6],
            layers=Pad.LAYERS_SMT,
        )
    )

    # Guide holes
    kicad_mod.append(
        Pad(
            type=Pad.TYPE_NPTH,
            shape=Pad.SHAPE_CIRCLE,
            at=[-b - 1.27, -0.2],
            drill=1,
            size=1,
            layers=Pad.LAYERS_NPTH,
        )
    )
    kicad_mod.append(
        Pad(
            type=Pad.TYPE_NPTH,
            shape=Pad.SHAPE_CIRCLE,
            at=[b + 1.27, 0.4],
            drill=1,
            size=1,
            layers=Pad.LAYERS_NPTH,
        )
    )

    # Minimal text references
    kicad_mod.append(Text(type="reference", text="REF**", at=[0, 0], layer="F.SilkS"))
    kicad_mod.append(Text(type="value", text=footprint_name, at=[0, 0], layer="F.Fab"))

    # Draw Courtyard
    kicad_mod.append(RectLine(start=[-c, -3.5], end=[+c, 4.1], layer="F.CrtYd"))

    # Draw Fabrication layer
    kicad_mod.append(RectLine(start=[-a / 2, -3.2], end=[+a / 2, 3.8], layer="F.Fab"))

    # Draw Silkscreen layer
    kicad_mod.append(RectLine(start=[-a / 2, -3.2], end=[+a / 2, 3.8], layer="F.SilkS"))
    # Draw pin 1 Silkscreen indicator
    kicad_mod.append(
        PolygoneLine(
            polygone=[[-c, -3.5 + 1.27], [-c, -3.5], [-c + 1.27, -3.5]], layer="F.SilkS"
        )
    )

    # Save file
    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(Footprint_name + ".kicad_mod")
