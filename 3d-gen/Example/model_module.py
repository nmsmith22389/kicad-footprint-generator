import cadquery as cq

def pins_plugin(wp, params):
    """
    This plugin allows us to define a pin's geometry once, and reuse it in
    every location that it is needed.
    """

    def pins(loc):
        box = (cq.Workplane()
                    .rect(params["pin_thickness"], params["pin_width"])
                    .extrude(params["pin_length"] / 2.0)
                    .faces(">Z").workplane()
                    .rect(params["pin_thickness"] / 2.0, params["pin_width"] / 2.0)
                    .extrude(params["pin_length"] / 2.0))

        return box.findSolid().moved(loc)

    return wp.eachpoint(pins, useLocalCoordinates=True, combine=True)


def generate_part(params):
    """
    Generates the body (case) and leads for the component.
    """

    # Generate the case/body
    body = cq.Workplane().rect(params["body_width"], params["body_length"]).extrude(params["body_thickness"])

    # Hook the plugin above into CadQuery
    cq.Workplane.pins_plugin = pins_plugin

    # Generate the pins in the correct location
    # The 0.001 is added to fix a rendering artifact in the KiCAD viewer
    pins = (body.faces(">Z").workplane(offset=params["body_thickness"] / 2.0, invert=True)
                .rarray(params["body_width"] + params["pin_thickness"] + 0.001, params["body_length"] / 3.0, 2, 3)
                .pins_plugin(params)
            )

    return (body, pins)
