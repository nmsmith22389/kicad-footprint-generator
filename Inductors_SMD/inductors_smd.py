import cadquery as cq

def make_inductor(params):
    """
    Generates the model for the inductor.
    """

    L = params['L']    # package length
    W = params['W']    # package width
    T = params['T']    # package height

    pb = params['pb']  # pin band

    pt = params['pt']  # pin thickness

    series = params['series']  # series
    # modelName = params.modelName  # Model Name
    # rotation = params.rotation   # rotation

    if series == 'wuerth_MAPI':
        case = cq.Workplane("XY").box(L, W, T, (True, True, False))
        case = case.edges("|Z").fillet(min(L,W)/20)
        case = case.edges(">Z").fillet(min(L,W)/20)
        pin1 = cq.Workplane("XY").box(pb, W, pt, (True, True, False)).translate((-(L-pb)/2, 0, 0))
        pin2 = cq.Workplane("XY").box(pb, W, pt, (True, True, False)).translate(((L-pb)/2, 0, 0))
        pins = pin1.union(pin2)
        pins = pins.edges("|Z").edges(">X").fillet(min(L,W)/20)
        pins = pins.edges("|Z").edges("<X").fillet(min(L,W)/20)
        case = case.cut(pins)
    elif series == 'vishay_IHSM':
        case = cq.Workplane("XY").box(L-2*pt, W, T-2*pt, (True, True, False)).translate((0, 0, pt))
        pin1 = cq.Workplane("XY").box(pb[0], pb[1], T, (True, True, False)).translate((-(L-pb[0])/2, 0, 0))
        pin2 = cq.Workplane("XY").box(pb[0], pb[1], T, (True, True, False)).translate(((L-pb[0])/2, 0, 0))
        pins = pin1.union(pin2)
        pins = pins.edges("|Y").edges(">X").fillet(pt)
        pins = pins.edges("|Y").edges("<X").fillet(pt)
        pins = pins.cut(case)
    else:
        print("Series not recognized: {}".format(series))

    return (case, pins)