#!/usr/bin/env python

from math import sqrt

from KicadModTree import (
    Footprint,
    FootprintType,
    KicadPrettyLibrary,
    Line,
    Model,
    Pad,
    PadArray,
    PolygonLine,
    Property,
    Rectangle,
    RectLine,
    Text,
    Translation,
)
from kilibs.geom import Vec2DCompatible, Vector2D
from scripts.tools.drawing_tools import roundCrt
from scripts.tools.global_config_files import global_config as GC

txt_offset = 1


def makePinHeadStraight(
    global_config: GC.GlobalConfig,
    rows: int,
    cols: int,
    rm: float,
    coldist: float,
    package_width: float,
    overlen_top: float,
    overlen_bottom: float,
    ddrill: float,
    pad: Vec2DCompatible,
    tags_additional: list[str] = [],
    lib_name: str = "Pin_Headers",
    class_name: str = "PinHeader",
    classname_description: str = "pin header",
    isSocket: bool = False,
    name_format: str | None = None,
):

    gc = global_config

    pad = Vector2D(pad)

    crtyd_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)

    # This is set a bit further out than normal, not quite clear why.
    # silk_pad_offset = gc.silk_pad_offset
    silk_pad_offset = gc.silk_pad_clearance + gc.silk_fab_offset

    silk_line_width = gc.silk_line_width

    h_fab = (rows - 1) * rm + overlen_top + overlen_bottom
    w_fab = package_width
    l_fab = (coldist * (cols - 1) - w_fab) / 2
    t_fab = -overlen_top

    h_slk = h_fab + 2 * gc.silk_fab_offset
    w_slk = max(w_fab + 2 * gc.silk_fab_offset, coldist * (cols - 1) - pad.x - 4 * gc.silk_fab_offset)
    l_slk = (coldist * (cols - 1) - w_slk) / 2
    t_slk = -overlen_top - gc.silk_fab_offset

    w_crt = max(package_width, coldist * (cols - 1) + pad.x) + 2 * crtyd_offset
    h_crt = max(h_fab, (rows - 1) * rm + pad.y) + 2 * crtyd_offset
    l_crt = coldist * (cols - 1) / 2 - w_crt / 2
    t_crt = (rows - 1) * rm / 2 - h_crt / 2

    fab_text_props = gc.get_text_properties_for_layer("F.Fab")
    fabref_text_size, fabref_text_thickness = fab_text_props.clamp_size(w_fab * 0.6)
    # That causes diffs, use the old unrounded calc for now
    fabref_text_thickness = fabref_text_size.y * 0.15

    # Samtec HPM have a different name format for...reasons
    # This is the default
    if name_format is None:
        name_format = "{class_name}_{cols}x{rows:02}_P{pitch:03.2f}mm_Vertical"

    footprint_name = name_format.format(class_name=class_name, cols=cols, rows=rows, pitch=rm)

    description = "Through hole straight {3}, {0}x{1:02}, {2:03.2f}mm pitch".format(cols, rows, rm, classname_description)
    tags = "Through hole {3} THT {0}x{1:02} {2:03.2f}mm".format(cols, rows, rm, classname_description)
    if (cols == 1):
        description = description + ", single row"
        tags = tags + " single row"
    elif (cols == 2):
        description = description + ", double rows"
        tags = tags + " double row"
    elif (cols == 3):
        description = description + ", triple rows"
        tags = tags + " triple row"
    elif (cols == 4):
        description = description + ", quadruple rows"
        tags = tags + " quadruple row"

    if (len(tags_additional) > 0):
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags = tags + " " + t

    print(footprint_name)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.description = description
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = Vector2D(0, 0)
    if isSocket and cols>1:
        offset.x = -coldist
    kicad_modg = Translation(offset)
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(name=Property.REFERENCE, text='REF**', at=[coldist * (cols - 1) / 2, t_slk - txt_offset], layer='F.SilkS'))
    kicad_modg.append(
        Text(text='${REFERENCE}', at=[rm/2*(cols-1), t_crt + offset.x + (h_crt/2)], rotation=90, layer='F.Fab', size=fabref_text_size, thickness=fabref_text_thickness))
    kicad_modg.append(
        Property(name=Property.VALUE, text=footprint_name, at=[coldist * (cols - 1) / 2, t_slk + h_slk + txt_offset], layer='F.Fab'))

    # create FAB-layer
    chamfer = w_fab/4
    kicad_modg.append(Line(start=[l_fab + chamfer, t_fab], end=[l_fab + w_fab, t_fab], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fab + w_fab, t_fab], end=[l_fab + w_fab, t_fab+h_fab], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fab + w_fab, t_fab+h_fab], end=[l_fab, t_fab+h_fab], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fab, t_fab+h_fab], end=[l_fab, t_fab+chamfer], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fab, t_fab+chamfer], end=[l_fab + chamfer, t_fab], layer='F.Fab', width=gc.fab_line_width))

    # create SILKSCREEN-layer + pin1 marker

    # Silkscreen body
    body_min_x_square = pad.x/2 + silk_pad_offset
    body_min_y_square = pad.y/2 + silk_pad_offset
    # drawin bottom line

    if (rows-1)*rm + body_min_y_square < t_slk + h_slk:
        kicad_modg.append(Line(start=[l_slk, t_slk + h_slk], end=[l_slk + w_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
    else:
        if rows == 1:
            kicad_modg.append(Line(start=[l_slk, body_min_y_square], end=[l_slk + w_slk, body_min_y_square], layer='F.SilkS', width=silk_line_width))
        else:
            body_min_x_round = sqrt(((pad.x/2 + silk_pad_offset) * (pad.x/2 + silk_pad_offset) - (overlen_bottom + gc.silk_fab_offset) * (overlen_bottom + gc.silk_fab_offset)))
            kicad_modg.append(Line(start=[l_slk, t_slk + h_slk], end=[-body_min_x_round, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
            kicad_modg.append(Line(start=[(cols-1)*coldist+body_min_x_round, t_slk + h_slk], end=[l_slk + w_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
            for x in range(0, (cols-1)):
                kicad_modg.append(Line(start=[x*coldist+body_min_x_round, t_slk + h_slk], end=[(x+1)*coldist-body_min_x_round, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
    # drawin sidelines
    # calculate top Y position
    if rm < body_min_y_square*2:
        shoulder_y_pos = body_min_y_square
        shoulder_y_lines = 2
    else:
        shoulder_y_pos = rm/2
        shoulder_y_lines = 1
    if coldist < body_min_x_square*2:
        top_x_pos = body_min_x_square
        top_x_lines = 2
    else:
        top_x_pos = coldist/2
        top_x_lines = 1
    if l_slk + w_slk  > body_min_x_square+(cols-1)*coldist:
        kicad_modg.append(Line(start=[l_slk, shoulder_y_pos], end=[l_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
        if cols == 1:
            kicad_modg.append(Line(start=[l_slk + w_slk, shoulder_y_pos], end=[l_slk + w_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
        else:
            kicad_modg.append(Line(start=[l_slk + w_slk, t_slk], end=[l_slk + w_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
    elif rows != 1:
        body_min_y_round = sqrt(((pad.x/2 + silk_pad_offset) * (pad.x/2 + silk_pad_offset) - l_slk * l_slk))
        kicad_modg.append(Line(start=[l_slk, shoulder_y_pos], end=[l_slk, rm-body_min_y_round], layer='F.SilkS', width=silk_line_width))
        kicad_modg.append(Line(start=[l_slk, (rows-1)*rm+body_min_y_round], end=[l_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
        if cols == 1:
            kicad_modg.append(Line(start=[l_slk + w_slk, shoulder_y_pos], end=[l_slk + w_slk, rm-body_min_y_round], layer='F.SilkS', width=silk_line_width))
        else:
            kicad_modg.append(Line(start=[l_slk + w_slk, body_min_y_square], end=[l_slk + w_slk, rm-body_min_y_round], layer='F.SilkS', width=silk_line_width))
        kicad_modg.append(Line(start=[l_slk + w_slk, (rows-1)*rm+body_min_y_round], end=[l_slk + w_slk, t_slk + h_slk], layer='F.SilkS', width=silk_line_width))
        for x in range(1, (rows-1)):
            kicad_modg.append(Line(start=[l_slk, x*rm+body_min_y_round], end=[l_slk, (x+1)*rm-body_min_y_round], layer='F.SilkS', width=silk_line_width))
            kicad_modg.append(Line(start=[l_slk + w_slk, x*rm+body_min_y_round], end=[l_slk + w_slk, (x+1)*rm-body_min_y_round], layer='F.SilkS', width=silk_line_width))
    # drawin top

    if cols == 1:
        if shoulder_y_lines == 1:
            kicad_modg.append(Line(start=[l_slk, shoulder_y_pos], end=[l_slk + w_slk, shoulder_y_pos], layer='F.SilkS', width=silk_line_width))
        elif shoulder_y_lines == 2:
            top_x_round = sqrt(((pad.x/2 + silk_pad_offset) * (pad.x/2 + silk_pad_offset) - (shoulder_y_pos-rm) * (shoulder_y_pos-rm)))
            kicad_modg.append(Line(start=[l_slk, shoulder_y_pos], end=[l_slk + w_slk/2-top_x_round, shoulder_y_pos], layer='F.SilkS', width=silk_line_width))
            kicad_modg.append(Line(start=[l_slk + w_slk/2 + top_x_round, shoulder_y_pos], end=[l_slk + w_slk, shoulder_y_pos], layer='F.SilkS', width=silk_line_width))
    else:
        if shoulder_y_lines == 1:
            kicad_modg.append(Line(start=[l_slk, shoulder_y_pos], end=[top_x_pos, shoulder_y_pos], layer='F.SilkS', width=silk_line_width))
        elif shoulder_y_lines == 2:
            top_x_round = sqrt(((pad.x/2 + silk_pad_offset) * (pad.x/2 + silk_pad_offset) - (shoulder_y_pos-rm) * (shoulder_y_pos-rm)))
            if top_x_pos > coldist-top_x_round:
                top_x_end = coldist-top_x_round
            else:
                top_x_end = top_x_pos
            kicad_modg.append(Line(start=[l_slk, shoulder_y_pos], end=[-top_x_round, shoulder_y_pos], layer='F.SilkS', width=silk_line_width))
            if top_x_round*2 + gc.silk_line_width*2 < pad.x:
                kicad_modg.append(Line(start=[top_x_round, shoulder_y_pos], end=[top_x_end, shoulder_y_pos], layer='F.SilkS', width=silk_line_width))
        if top_x_lines == 1:
            kicad_modg.append(Line(start=[top_x_pos, shoulder_y_pos], end=[top_x_pos, t_slk], layer='F.SilkS', width=silk_line_width))
        elif top_x_lines == 2:
            shoulder_y_round = sqrt(((pad.x/2 + silk_pad_offset) * (pad.x/2 + silk_pad_offset) - (coldist-top_x_pos) * (coldist-top_x_pos)))
            if shoulder_y_pos > rm-shoulder_y_round:
                shoulder_y_pos = rm-shoulder_y_round
            if shoulder_y_round*2 + silk_line_width*2 < pad.y:
                kicad_modg.append(Line(start=[top_x_pos, shoulder_y_pos], end=[top_x_pos, shoulder_y_round], layer='F.SilkS', width=silk_line_width))
                kicad_modg.append(Line(start=[top_x_pos, -shoulder_y_round], end=[top_x_pos, t_slk], layer='F.SilkS', width=silk_line_width))
        # highest horizontal line
        if abs(t_slk) > body_min_y_square:
            kicad_modg.append(Line(start=[top_x_pos, t_slk], end=[l_slk + w_slk, t_slk], layer='F.SilkS', width=silk_line_width))
        else:
            top_x_round = sqrt(((pad.x/2 + silk_pad_offset) * (pad.x/2 + silk_pad_offset) - (abs(t_slk)) * (abs(t_slk))))
            if top_x_pos > coldist-top_x_round + 2*silk_line_width:
                kicad_modg.append(Line(start=[top_x_pos, t_slk], end=[coldist-top_x_round, t_slk], layer='F.SilkS', width=silk_line_width))
            kicad_modg.append(Line(start=[coldist+top_x_round, t_slk], end=[l_slk + w_slk, t_slk], layer='F.SilkS', width=silk_line_width))

    '''
    if cols == 1:
        kicad_modg.append(
            RectLine(start=[l_slk, 0.5 * rm], end=[l_slk + w_slk, t_slk + h_slk], layer='F.SilkS', width=gc.silk_line_width))
    else:
        if isSocket and cols>1:
            kicad_modg.append(PolygonLine(
                shape=[[l_slk+w_slk, 0.5 * rm], [l_slk+w_slk, t_slk + h_slk], [l_slk , t_slk + h_slk], [l_slk , t_slk],
                          [l_slk+w_slk/2, t_slk], [l_slk+w_slk/2, 0.5 * rm], [l_slk+w_slk, 0.5 * rm]], layer='F.SilkS', width=lw_slk))
        else:
            kicad_modg.append(PolygonLine(
                shape=[[l_slk, 0.5 * rm], [l_slk, t_slk + h_slk], [l_slk + w_slk, t_slk + h_slk], [l_slk + w_slk, t_slk],
                          [0.5 * rm, t_slk], [0.5 * rm, 0.5 * rm], [l_slk, 0.5 * rm]], layer='F.SilkS', width=lw_slk))
    '''
    # pin 1 marker
    pin1_min = -(pad.x/2 + silk_pad_offset)
    if pin1_min < l_slk:
        pin1_x = pin1_min
    else:
        pin1_x = l_slk
    if pin1_min < t_slk:
        pin1_y = pin1_min
    else:
        pin1_y = t_slk
    if isSocket and cols>1:
        kicad_modg.append(PolygonLine(shape=[[pin1_x + w_slk, 0], [pin1_x + w_slk, pin1_y], [pin1_x + w_slk - rm / 2, pin1_y]], layer='F.SilkS', width=silk_line_width))
    else:
        kicad_modg.append(PolygonLine(shape=[[pin1_x, 0], [pin1_x, pin1_y], [0, pin1_y]], layer='F.SilkS', width=silk_line_width))

    # create courtyard
    crt_rect = Rectangle(
        start=Vector2D(l_crt, t_crt),
        size=Vector2D(w_crt, h_crt),
    ).round_to_grid(outwards=True, grid=gc.courtyard_grid)

    kicad_modg.append(
        RectLine(
            start=crt_rect.top_left,
            end=crt_rect.bottom_right,
            layer="F.CrtYd",
            width=gc.courtyard_line_width,
        )
    )

    # create pads
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_RECT
    pad_shapeother = Pad.SHAPE_OVAL
    pad_layers = Pad.LAYERS_THT

    p = 1

    for r in range(1, rows + 1): # type: ignore

        if isSocket and cols>1:
            x1=coldist
        else:
            x1 = 0
        for c in range(1, cols + 1): # type: ignore
            if p == 1:
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[x1, y1], size=pad, drill=ddrill,
                                      layers=pad_layers))
            else:
                kicad_modg.append(
                    Pad(number=p, type=pad_type, shape=pad_shapeother, at=[x1, y1], size=pad, drill=ddrill,
                        layers=pad_layers))

            p = p + 1
            if isSocket and cols>1:
                x1 = x1 - coldist
            else:
                x1 = x1 + coldist

        y1 = y1 + rm

    # add model
    kicad_modg.append(
        Model(
            filename=gc.model_3d_prefix
            + lib_name
            + ".3dshapes/"
            + footprint_name
            + global_config.model_3d_suffix
        )
    )

    # write file
    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)


def makeIdcHeader(
    global_config: GC.GlobalConfig,
    rows: int,
    cols: int,
    rm: float,
    coldist: float,
    body_width: float,
    overlen_top: float,
    overlen_bottom: float,
    body_offset: float,
    ddrill: float,
    pad: Vec2DCompatible,
    mating_overlen: float,
    wall_thickness: float,
    notch_width: float,
    orientation: str,
    latching: float,
    latch_len: float,
    latch_width: float,
    mh_ddrill: float,
    mh_pad: Vec2DCompatible,
    mh_overlen: float,
    mh_offset: float,
    mh_number: str,
    tags_additional: list[str],
    extra_description: str,
    lib_name: str,
    classname: str,
    classname_description: str,
):
    # If ddrill is zero, then create a SMD footprint:
    #     SMT pads are created.
    #     rm is row pitch
    #     coldist is pad pitch for columns

    gc = global_config
    pad = Vector2D(pad)
    mh_pad = Vector2D(mh_pad)
    crtyd_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)

    pin_size = 0.64 # square pin side length; this appears to be the same for all connectors so use a fixed internal value

    mh_present = True if mh_ddrill > 0 and mh_pad.x > 0 and mh_pad.y > 0 and mh_overlen > 0 else False
    mh_y = Vector2D(-mh_overlen, (rows - 1) * rm + mh_overlen)

    h_fab = (rows - 1) * rm + overlen_top + overlen_bottom
    w_fab = body_width
    if ddrill == 0:
        # Body should be centered for SMT footprints
        l_fab = - w_fab / 2 if body_offset == 0 else body_offset
        t_fab = -overlen_top - (rows-1)*rm/2
    else:
        l_fab = (coldist * (cols - 1) - w_fab) / 2 if body_offset == 0 else body_offset
        t_fab = -overlen_top

    # these calculations are so tight that new body styles will probably break them
    h_crt = max(max(h_fab, (rows - 1) * rm + pad.y) + 2 * latch_len, (rows - 1) * rm + 2 * mh_overlen + mh_pad.y) + 2 * crtyd_offset
    w_crt = max(body_width, coldist * (cols - 1) + pad.x) + 2 * crtyd_offset if body_offset <= 0 else pad.x / 2 + body_offset + body_width + 2 * crtyd_offset
    if ddrill == 0:
        # Courtyard should be centered for SMT footprints
        l_crt =  -pad.x / 2 - coldist/2- crtyd_offset
        t_crt = min(t_fab - latch_len, -mh_overlen - mh_pad.y / 2) - crtyd_offset
    else:
        l_crt = l_fab - crtyd_offset if body_offset <= 0 else -pad.x / 2 - crtyd_offset
        t_crt = min(t_fab - latch_len, -mh_overlen - mh_pad.y / 2) - crtyd_offset
    # if orientation == 'Horizontal' and latching and mh_ddrill > 0:
    if mh_present and (mh_offset - mh_pad.x / 2 < l_fab):
        # horizontal latching with mounting holes is a special case
        l_crt = mh_offset - mh_pad.x / 2 - crtyd_offset
        w_crt = -l_crt + body_width + body_offset + crtyd_offset

    if ddrill == 0:
        # center is [0, 0] for SMD footprints
        center_fab = Vector2D(0, 0)
        center_fp = Vector2D(0, 0)
    else:
        # center of the body (horizontal: middle pin or the center of the middle pins for vertical)
        center_fab = Vector2D(coldist * (cols - 1) / 2 if orientation == 'Vertical' else body_offset + body_width / 2, t_fab + h_fab / 2)
        center_fp = Vector2D(l_crt + w_crt / 2, center_fab.y)

    fab_text_props = gc.get_text_properties_for_layer("F.Fab")
    text_size, text_thickness = fab_text_props.clamp_size(w_fab * 0.6)

    footprint_name = "{3}_{0}x{1:02}{7}_P{2:03.2f}mm{4}{5}_{6}{8}".format(cols, rows, rm, classname, "_Latch" if latching else "", "{0:03.1f}mm".format(latch_len) if latch_len > 0 else "", orientation, "-1MP" if mh_present else "", "_SMD"if ddrill==0 else "")
    # footprint_name = footprint_name_base + "_MountHole" if mh_present else footprint_name_base

    if cols == 1:
        description_rows = "single row"
        tags_rows = "single row"
    elif cols == 2:
        description_rows = "double rows"
        tags_rows = "double row"
    elif cols == 3:
        description_rows = "triple rows"
        tags_rows = "triple row"
    elif cols == 4:
        description_rows = "quadruple rows"
        tags_rows = "quadruple row"
    else:
        raise ValueError("Unsupported number of rows: {0}".format(cols))

    if ddrill == 0:
        description = "SMD"
        tags = "SMD"
        mounting_type = ""
    else:
        description = "Through hole"
        tags = "Through hole"
        mounting_type = "THT"

    description = description + " {3}, {0}x{1:02}, {2:03.2f}mm pitch, DIN 41651 / IEC 60603-13, {4}{5}{6}{7}".format(cols, rows, rm, classname_description, description_rows, ", {0:03.1f}mm".format(latch_len) if latch_len > 0 else "", " latches" if latching else "", ", mounting holes" if mh_present else "", orientation.lower())
    tags = tags + " {5} {3} {6} {0}x{1:02} {2:03.2f}mm {4}".format(cols, rows, rm, classname_description, tags_rows, orientation.lower(), mounting_type)

    if (len(tags_additional) > 0):
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags = tags + " " + t

    if extra_description:
        description = description + ", " + extra_description

    print(footprint_name)

    footprint_type = FootprintType.SMD if ddrill == 0 else FootprintType.THT

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, footprint_type)
    kicad_mod.description = description
    kicad_mod.tags = tags

    # instantiate footprint (SMD origin at center, THT at pin 1)
    kicad_modg = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(Property(name=Property.REFERENCE, text='REF**', at=[center_fp.x, t_crt - text_size.y / 2], layer='F.SilkS'))
    kicad_modg.append(Text(text='${REFERENCE}', at=[center_fab.x, center_fab.y], rotation=90, layer='F.Fab', size=text_size, thickness=text_thickness))
    kicad_modg.append(Property(name=Property.VALUE, text=footprint_name, at=[center_fp.x, t_crt + h_crt + text_size.y / 2], layer='F.Fab'))

    # for shrouded headers, fab and silk layers have very similar geometry
    # can use the same code to build lines on both layers with slight changes in values between layers
    # zip together lists with fab and then silk layer settings as the list elements so the same code can draw both layers
    for layer, line_width, lyr_offset, chamfer in zip(['F.Fab', 'F.SilkS'], [gc.fab_line_width, gc.silk_line_width], [0, gc.silk_fab_offset], [min(1, w_fab / 4), 0]):
        # body outline
        if orientation == 'Horizontal' and latching:
            # body outline taken from existing KiCad footprint
            body_polygon = [
                (body_offset - lyr_offset, t_fab - lyr_offset), (l_fab + 6.98 + lyr_offset, t_fab - lyr_offset),
                (l_fab + w_fab + lyr_offset, t_fab + 3.17 - lyr_offset), (l_fab + w_fab + lyr_offset, t_fab + 6.99 + lyr_offset),
                (l_fab + 12.7 + lyr_offset, t_fab + 9.14 + lyr_offset), (l_fab + 12.7 + lyr_offset, t_fab + h_fab - 9.14 - lyr_offset),
                (l_fab + w_fab + lyr_offset, t_fab + h_fab - 6.99 - lyr_offset), (l_fab + w_fab + lyr_offset, t_fab + h_fab - 3.17 + lyr_offset),
                (l_fab + 6.98 + lyr_offset, t_fab + h_fab + lyr_offset), (body_offset - lyr_offset, t_fab + h_fab + lyr_offset)
            ]
            # body outline taken from simplified 3M 3000 model (also modify arguments: body_offset=-1.24 and body_width=1.24+15.53)
            # https://www.3m.com/3M/en_US/company-us/all-3m-products/~/3M-Four-Wall-Header-3000-Series/?N=5002385+3290316872&preselect=8709318+8710652+8733900+8734573&rt=rud
            body_polygon = [
                (body_offset - lyr_offset, t_fab - lyr_offset), (l_fab + 7.11 + lyr_offset, t_fab - lyr_offset),
                (l_fab + 16.77 + lyr_offset, t_fab + 3.47 - lyr_offset), (l_fab + 16.77 + lyr_offset, t_fab + 7.44 + lyr_offset),
                (l_fab + 13.21 + lyr_offset, t_fab + 8.07 + lyr_offset), (l_fab + 13.21 + lyr_offset, t_fab + h_fab - 8.07 - lyr_offset),
                (l_fab + 16.77 + lyr_offset, t_fab + h_fab - 7.44 - lyr_offset), (l_fab + 16.77 + lyr_offset, t_fab + h_fab - 3.47 + lyr_offset),
                (l_fab + 7.11 + lyr_offset, t_fab + h_fab + lyr_offset), (body_offset - lyr_offset, t_fab + h_fab + lyr_offset)
            ]
            kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
            # now draw the left side vertical line, which may be broken on the silk layer around mounting holes
            if layer == 'F.SilkS' and mh_present and mh_pad.x/2 - mh_offset > -body_offset + gc.silk_fab_offset * 1.5:
                body_polygon = [(body_offset - lyr_offset, t_fab - lyr_offset), (body_offset - lyr_offset, mh_y.x - mh_pad.x/2)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                body_polygon = [(body_offset - lyr_offset, mh_y.x + mh_pad.x/2), (body_offset - lyr_offset, mh_y.y - mh_pad.x/2)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                body_polygon = [(body_offset - lyr_offset, mh_y.y + mh_pad.x/2), (body_offset - lyr_offset, t_fab + h_fab + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
            else:
                body_polygon = [(body_offset - lyr_offset, t_fab + h_fab + lyr_offset), (body_offset - lyr_offset, t_fab - lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
        else:
            # body outline silk lines need to clear the mounting hole on vertical headers
            if mh_present and layer == 'F.SilkS':
                body_polygon = [(mh_offset + mh_pad.x/2 - lyr_offset, t_fab - lyr_offset), (l_fab + w_fab + lyr_offset, t_fab - lyr_offset),
                    (l_fab + w_fab + lyr_offset, t_fab + h_fab + lyr_offset), (mh_offset + mh_pad.x/2 - lyr_offset, t_fab + h_fab + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                body_polygon = [(mh_offset - mh_pad.x/2 + lyr_offset, t_fab - lyr_offset), (l_fab - lyr_offset, t_fab - lyr_offset),
                    (l_fab - lyr_offset, t_fab + h_fab + lyr_offset), (mh_offset - mh_pad.x/2 + lyr_offset, t_fab + h_fab + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
            else:
                if layer == 'F.SilkS' and ddrill == 0:
                    # Break silkscreen for SMD pads
                    body_polygon = [(l_fab - lyr_offset, -((rows-1)*rm/2)-pad.y/2-0.5), (l_fab - lyr_offset, t_fab - lyr_offset),
                        (l_fab + w_fab + lyr_offset, t_fab - lyr_offset), (l_fab +w_fab + lyr_offset, -((rows-1)*rm/2)-pad.y/2-0.5)]
                    kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                    body_polygon = [(l_fab - lyr_offset, ((rows-1)*rm/2)+pad.y/2+0.5), (l_fab - lyr_offset, t_fab + h_fab + lyr_offset),
                        (l_fab + w_fab + lyr_offset, t_fab +h_fab + lyr_offset), (l_fab +w_fab + lyr_offset, ((rows-1)*rm/2)+pad.y/2+0.5)]
                    kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                else:
                    body_polygon = [(l_fab + chamfer - lyr_offset, t_fab - lyr_offset), (l_fab + w_fab + lyr_offset, t_fab - lyr_offset),
                        (l_fab + w_fab + lyr_offset, t_fab + h_fab + lyr_offset), (l_fab - lyr_offset, t_fab + h_fab + lyr_offset),
                        (l_fab - lyr_offset, t_fab + chamfer - lyr_offset)]
                    kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
        if chamfer > 0 and not (orientation == 'Horizontal' and latching):
            kicad_modg.append(Line(start=[l_fab, t_fab + chamfer], end=[l_fab + chamfer, t_fab], layer=layer, width=line_width))

        # vertical mating connector outline (this is the same for both layers)
        if orientation == 'Vertical':
            if ddrill == 0:
                mating_conn_polygon = [(l_fab - lyr_offset, center_fab.y - notch_width/2), (l_fab + wall_thickness, center_fab.y - notch_width/2),
                    (l_fab + wall_thickness, t_fab+wall_thickness), (l_fab + w_fab - wall_thickness, t_fab+wall_thickness),
                    (l_fab + w_fab - wall_thickness, t_fab+h_fab-wall_thickness), (l_fab + wall_thickness, t_fab+h_fab-wall_thickness),
                    (l_fab + wall_thickness, center_fab.y + notch_width/2), (l_fab + wall_thickness, center_fab.y + notch_width/2),
                    (l_fab - lyr_offset, center_fab.y + notch_width/2)]
                if layer == "F.Fab":
                    # Only append mating connector outline in F.Fab for SMD footprints (silkscreen would be on top of pads)
                    kicad_mod.append(PolygonLine(shape=mating_conn_polygon, layer=layer, width=line_width))
            else:
                mating_conn_polygon = [(l_fab - lyr_offset, center_fab.y - notch_width/2), (l_fab + wall_thickness, center_fab.y - notch_width/2),
                    (l_fab + wall_thickness, -mating_overlen), (l_fab + w_fab - wall_thickness, -mating_overlen),
                    (l_fab + w_fab - wall_thickness, (rows - 1) * rm + mating_overlen), (l_fab + wall_thickness, (rows - 1) * rm + mating_overlen),
                    (l_fab + wall_thickness, center_fab.y + notch_width/2), (l_fab + wall_thickness, center_fab.y + notch_width/2),
                    (l_fab - lyr_offset, center_fab.y + notch_width/2)]
                kicad_mod.append(PolygonLine(shape=mating_conn_polygon, layer=layer, width=line_width))

        # horizontal mating connector 'notch' lines
        if orientation == 'Horizontal' and not latching:
            kicad_modg.append(Line(start=[body_offset - lyr_offset, center_fab.y - notch_width / 2], end=[l_fab + w_fab + lyr_offset, center_fab.y - notch_width / 2], layer=layer, width=line_width))
            kicad_modg.append(Line(start=[body_offset - lyr_offset, center_fab.y + notch_width / 2], end=[l_fab + w_fab + lyr_offset, center_fab.y + notch_width / 2], layer=layer, width=line_width))

        # vertical latches (horizontal latches are off the PCB and not shown)
        if orientation == 'Vertical' and latching and latch_len > 0:
            # body outline silk lines need to clear the mounting hole on vertical headers
            if mh_present and layer == 'F.SilkS':
                # top latch
                latch_top_polygon = [(center_fab.x - latch_width/2 - lyr_offset, mh_y.x - mh_pad.y/2 + lyr_offset), (center_fab.x - latch_width/2 - lyr_offset, t_fab - latch_len - lyr_offset),
                    (center_fab.x + latch_width/2 + lyr_offset, t_fab - latch_len - lyr_offset), (center_fab.x + latch_width/2 + lyr_offset, mh_y.x - mh_pad.y/2 + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_top_polygon, layer=layer, width=line_width))
                # bottom latch
                latch_bottom_polygon = [(center_fab.x - latch_width/2 - lyr_offset, mh_y.y + mh_pad.y/2 - lyr_offset), (center_fab.x - latch_width/2 - lyr_offset, t_fab + h_fab + latch_len + lyr_offset),
                    (center_fab.x + latch_width/2 + lyr_offset, t_fab + h_fab + latch_len + lyr_offset), (center_fab.x + latch_width/2 + lyr_offset, mh_y.y + mh_pad.y/2 - lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_bottom_polygon, layer=layer, width=line_width))
            else:
                # top latch
                latch_top_polygon = [(center_fab.x - latch_width/2 - lyr_offset, t_fab - lyr_offset), (center_fab.x - latch_width/2 - lyr_offset, t_fab - latch_len - lyr_offset),
                    (center_fab.x + latch_width/2 + lyr_offset, t_fab - latch_len - lyr_offset), (center_fab.x + latch_width/2 + lyr_offset, t_fab - lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_top_polygon, layer=layer, width=line_width))
                # bottom latch
                latch_bottom_polygon = [(center_fab.x - latch_width/2 - lyr_offset, t_fab + h_fab + lyr_offset), (center_fab.x - latch_width/2 - lyr_offset, t_fab + h_fab + latch_len + lyr_offset),
                    (center_fab.x + latch_width/2 + lyr_offset, t_fab + h_fab + latch_len + lyr_offset), (center_fab.x + latch_width/2 + lyr_offset, t_fab + h_fab + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_bottom_polygon, layer=layer, width=line_width))

    # horizontal pin outlines (only applies if the body is right of the leftmost pin row)
    # if orientation == 'Horizontal' and not latching:
    if body_offset > 0:
        for row in range(rows):
            horiz_pin_polygon = [(body_offset, rm * row - pin_size / 2), (-pin_size / 2, rm * row - pin_size / 2),
                (-pin_size / 2, rm * row + pin_size / 2), (body_offset, rm * row + pin_size / 2)]
            kicad_modg.append(PolygonLine(shape=horiz_pin_polygon, layer='F.Fab', width=gc.fab_line_width))

    # silk pin 1 mark (triangle to the left of pin 1)
    slk_mark_height = 1
    slk_mark_width = 1
    if ddrill == 0:
        slk_polygon = [(l_fab - gc.silk_fab_offset, -((rows-1)*rm/2)-pad.y/2-0.5), (l_fab - gc.silk_fab_offset-1.5, -((rows-1)*rm/2)-pad.y/2-0.5)]
    else:
        slk_mark_tip = min(l_fab, -pad.x / 2) - 0.5 # offset 0.5mm from pin 1 or the body
        slk_polygon = [(slk_mark_tip, 0), (slk_mark_tip - slk_mark_width, -slk_mark_height / 2),
            (slk_mark_tip - slk_mark_width, slk_mark_height / 2), (slk_mark_tip, 0)]
    kicad_mod.append(PolygonLine(shape=slk_polygon, layer='F.SilkS', width=gc.silk_line_width))

    # create courtyard
    if ddrill == 0 and orientation == 'Vertical' and not latching:
        #         l_crt =  -pad.x / 2 - coldist/2- crt_offset
        crt_polygon = [
            (roundCrt(l_fab - crtyd_offset), roundCrt(t_crt)),
            (roundCrt(l_fab - crtyd_offset), roundCrt(-((rows-1)*rm/2)-pad.y/2 - crtyd_offset)),
            (roundCrt(l_crt), roundCrt(-((rows-1)*rm/2)-pad.y/2 - crtyd_offset)),
            (roundCrt(l_crt), roundCrt(((rows-1)*rm/2)+pad.y/2 + crtyd_offset)),
            (roundCrt(l_fab - crtyd_offset), roundCrt(((rows-1)*rm/2)+pad.y/2 + crtyd_offset)),
            (roundCrt(l_fab - crtyd_offset), roundCrt(-t_crt)),
            (roundCrt(-l_fab + crtyd_offset), roundCrt(-t_crt)),
            (roundCrt(-l_fab + crtyd_offset), roundCrt(((rows-1)*rm/2)+pad.y/2 + crtyd_offset)),
            (roundCrt(-l_crt), roundCrt(((rows-1)*rm/2)+pad.y/2 + crtyd_offset)),
            (roundCrt(-l_crt), roundCrt(-((rows-1)*rm/2)-pad.y/2 - crtyd_offset)),
            (roundCrt(-l_fab + crtyd_offset), roundCrt(-((rows-1)*rm/2)-pad.y/2 - crtyd_offset)),
            (roundCrt(-l_fab + crtyd_offset), roundCrt(t_crt)),
            (roundCrt(l_fab - crtyd_offset), roundCrt(t_crt))
        ]
        kicad_mod.append(PolygonLine(shape=crt_polygon, layer='F.CrtYd', width=gc.courtyard_line_width))
    else:
        kicad_mod.append(RectLine(start=[roundCrt(l_crt), roundCrt(t_crt)], end=[roundCrt(l_crt + w_crt),
                    roundCrt(t_crt + h_crt)], layer='F.CrtYd', width=gc.courtyard_line_width))

    # create pads (first the left row then the right row)
    if ddrill == 0:
        pad_type = Pad.TYPE_SMT
        pad_shape = Pad.SHAPE_ROUNDRECT
        pad_layers = Pad.LAYERS_SMT
    else:
        pad_type = Pad.TYPE_THT
        pad_shape = Pad.SHAPE_OVAL
        pad_layers = Pad.LAYERS_THT

    if ddrill == 0:
        # For SMD footprints, pad 1 location is not (0,0)
        for start_pos, initial in zip([-coldist/2, coldist/2], range(1, cols + 1)):
            kicad_modg.append(PadArray(pincount=rows, spacing=[0,rm], start=[start_pos,-(rows-1)*rm/2], initial=initial, increment=cols,
                type=pad_type, shape=pad_shape, size=pad, drill=ddrill, layers=pad_layers,
                round_radius_handler=global_config.roundrect_radius_handler))
    else:
        for start_pos, initial in zip([0, coldist], range(1, cols + 1)):
            kicad_modg.append(PadArray(pincount=rows, spacing=[0,rm], start=[start_pos,0], initial=initial, increment=cols,
                type=pad_type, shape=pad_shape, size=pad, drill=ddrill, layers=pad_layers,
                round_radius_handler=global_config.roundrect_radius_handler))

    # create mounting hole pads
    if mh_present:
        for mh_y_offset in mh_y:
            kicad_modg.append(Pad(number=mh_number, type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, at=[mh_offset, mh_y_offset], size=mh_pad,
                drill=mh_ddrill, layers=Pad.LAYERS_THT))

    # add model (even if there are mounting holes on the footprint do not include that in the 3D model)
    kicad_modg.append(
        Model(
            filename=global_config.model_3d_prefix
            + lib_name
            + ".3dshapes/"
            + footprint_name
            + global_config.model_3d_suffix
        )
    )

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)


#
#             <-->pack_offset
#                 <------->pack_width
#                          <------------------------------>pin_length
#    <-coldist>
# +---            +-------+
# | OOO      OOO  |       +-------------------------------+            ^
# | OOO ==== OOO  |       |                               +    ^       pin_width
#   OOO      OOO  |       +-------------------------------+    |       v
#                 +-------+                                    rm
#   OOO      OOO  |       +-------------------------------+    |
#   OOO ==== OOO  |       |                               +    v
#   OOO      OOO  |       +-------------------------------+
#                 +-------+                                    rm
#
def makePinHeadAngled(
    global_config: GC.GlobalConfig,
    rows: int,
    cols: int,
    rm: float,
    coldist: float,
    pack_width: float,
    pack_offset: float,
    pin_length: float,
    pin_width: float,
    ddrill: float,
    pad: Vec2DCompatible,
    tags_additional: list[str] = [],
    lib_name: str = "Pin_Headers",
    classname: str = "Pin_Header",
    classname_description: str = "pin header",
):
    gc = global_config
    pad = Vector2D(pad)
    crtyd_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)

    # This is set a bit further out than normal, not quite clear why.
    # silk_pad_offset = gc.silk_pad_offset
    silk_pad_offset = gc.silk_pad_clearance + gc.silk_fab_offset

    h_fabb = (rows - 1) * rm + rm / 2 + rm / 2
    w_fabb = pack_width
    l_fabb = coldist * (cols - 1) + pack_offset
    t_fabb = -rm / 2
    l_fabp = l_fabb + w_fabb
    t_fabp = -pin_width / 2

    fab_text_props = gc.get_text_properties_for_layer("F.Fab")
    fabref_text_size, fabref_text_thickness = fab_text_props.clamp_size(w_fabb * 0.6)
    # That causes diffs, use the old unrounded calc for now
    fabref_text_thickness = fabref_text_size.y * 0.15

    w_slkb = w_fabb + 2 * gc.silk_fab_offset
    l_slkb = l_fabb - gc.silk_fab_offset
    t_slkb = t_fabb - gc.silk_fab_offset
    l_slkp = l_slkb + w_slkb
    l_slk = -rm / 2
    t_slk = -rm / 2
    body_lines_y = False

    w_crt = rm / 2 + (cols - 1) * coldist + pack_offset + pack_width + pin_length + 2 * crtyd_offset
    h_crt = h_fabb + 2 * crtyd_offset
    l_crt = -rm / 2 - crtyd_offset
    t_crt = -rm / 2 - crtyd_offset

    # if rm == 2.54:
    #    footprint_name = "Pin_Header_Angled_{0}x{1:02}".format(cols, rows)
    # else:
    footprint_name = "{3}_{0}x{1:02}_P{2:03.2f}mm_Horizontal".format(cols, rows, rm, classname)

    description = "Through hole angled {4}, {0}x{1:02}, {2:03.2f}mm pitch, {3}mm pin length".format(cols, rows,
                                                                                                    rm,
                                                                                                    pin_length,
                                                                                                    classname_description)
    tags = "Through hole angled {3} THT {0}x{1:02} {2:03.2f}mm".format(cols, rows, rm, classname_description)
    if (cols == 1):
        description = description + ", single row"
        tags = tags + " single row"
    elif (cols == 2):
        description = description + ", double rows"
        tags = tags + " double row"
    elif (cols == 3):
        description = description + ", triple rows"
        tags = tags + " triple row"

    if (len(tags_additional) > 0):
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags = tags + " " + t

    print(footprint_name)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.description = description
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = Vector2D(0, 0)
    kicad_modg = Translation(offset)
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(name=Property.REFERENCE, text='REF**', at=[l_crt + w_crt / 2, t_crt + crtyd_offset - txt_offset], layer='F.SilkS'))
    kicad_modg.append(
        Text(text='${REFERENCE}', at=[l_fabb + (w_fabb/2), t_crt + offset.y + (h_crt/2)], rotation=90, layer='F.Fab', size=fabref_text_size, thickness=fabref_text_thickness))
    kicad_modg.append(
        Property(name=Property.VALUE, text=footprint_name, at=[l_crt + w_crt / 2, t_crt + h_crt - crtyd_offset + txt_offset],
             layer='F.Fab'))

    # create FAB-layer
    chamfer = w_fabb/4
    kicad_modg.append(Line(start=[l_fabb + chamfer, t_fabb], end=[l_fabb + w_fabb, t_fabb], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fabb + w_fabb, t_fabb], end=[l_fabb + w_fabb, t_fabb+rm*rows], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fabb + w_fabb, t_fabb+rm*rows], end=[l_fabb, t_fabb+rm*rows], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fabb, t_fabb+rm*rows], end=[l_fabb, t_fabb+chamfer], layer='F.Fab', width=gc.fab_line_width))
    kicad_modg.append(Line(start=[l_fabb, t_fabb+chamfer], end=[l_fabb + chamfer, t_fabb], layer='F.Fab', width=gc.fab_line_width))
    y1 = t_fabb
    yp = t_fabp
    for r in range(1, rows + 1):
        kicad_modg.append(Line(start=[-pin_width/2, yp], end=[l_fabb, yp], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[-pin_width/2, yp], end=[-pin_width/2, yp + pin_width], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[-pin_width/2, yp + pin_width], end=[l_fabb, yp + pin_width], layer='F.Fab', width=gc.fab_line_width))

        kicad_modg.append(Line(start=[l_fabb + w_fabb, yp], end=[l_fabp + pin_length, yp], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fabp + pin_length, yp], end=[l_fabp + pin_length, yp + pin_width], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fabb + w_fabb, yp + pin_width], end=[l_fabp + pin_length, yp + pin_width], layer='F.Fab', width=gc.fab_line_width))

        y1 = y1 + rm
        yp = yp + rm

    # create SILKSCREEN-layer + pin1 marker

    # calculate point to avoid collision with pad clearance
    pin_line_x = sqrt(((pad.x/2+ silk_pad_offset) * (pad.x/2+ silk_pad_offset) - (pin_width/2+gc.silk_fab_offset) * (pin_width/2+gc.silk_fab_offset)))
    # Silkscreen body
    body_min_x_square = pad.x/2+ silk_pad_offset
    body_min_y_square = pad.y/2+ silk_pad_offset

    if rm/2 < body_min_y_square:
        body_min_x_round = sqrt((((pad.x/2+ silk_pad_offset) * (pad.x/2+ silk_pad_offset)) - (rm/2 * rm/2)))
        if l_slkb > body_min_x_round + (cols-1)*coldist and l_slkb < body_min_x_square +(cols-1)*coldist:
            body_lines_y = sqrt((((pad.x/2+ silk_pad_offset) * (pad.x/2+ silk_pad_offset)) - ((l_slkb-(cols-1)*coldist) * (l_slkb-(cols-1)*coldist))))
    else:
        body_min_x_round  = 0
    if rm/2+gc.silk_fab_offset < body_min_y_square:
        bodyend_min_x_round = sqrt((((pad.x/2+ silk_pad_offset) * (pad.x/2+ silk_pad_offset)) - ((rm/2+gc.silk_fab_offset) * (rm/2+gc.silk_fab_offset))))
    else:
        bodyend_min_x_round = 0
    # if body is starting outside the pads
    if l_slkb-gc.silk_fab_offset > pad.x/2 + gc.silk_pad_clearance + (cols-1)*coldist:
        kicad_modg.append(RectLine(start=[l_slkb, t_slkb], end=[l_slkp, t_slkb+rm*rows+gc.silk_fab_offset*2], layer='F.SilkS', width=gc.silk_line_width))
    else:
        if l_slkb < body_min_x_square + (cols-1)*coldist and t_slkb-gc.silk_fab_offset > -(body_min_y_square + (cols-1)*coldist):
            if cols == 1:
                upper_body_x = body_min_x_square
            else:
                upper_body_x = bodyend_min_x_round + (cols-1)*coldist
        else:
            upper_body_x = l_slkb
        if rows == 1 and cols == 1:
            lower_body_x = body_min_x_square  + (cols-1)*coldist
        elif l_slkb < bodyend_min_x_round + (cols-1)*coldist and t_slkb-gc.silk_fab_offset > -(body_min_y_square + (cols-1)*coldist):
            lower_body_x = bodyend_min_x_round + (cols-1)*coldist
        else:
            lower_body_x = l_slkb
        if body_lines_y != False:
            if cols == 1:
                kicad_modg.append(PolygonLine(shape=[[upper_body_x, t_slkb], [l_slkp, t_slkb], [l_slkp, t_slkb + rm * rows + gc.silk_fab_offset * 2],
                                                        [lower_body_x, t_slkb+rm*rows+gc.silk_fab_offset*2], [lower_body_x, t_slkb+rm*rows-rm/2+gc.silk_fab_offset+body_lines_y]], layer='F.SilkS', width=gc.silk_line_width))
            else:
                kicad_modg.append(PolygonLine(shape=[[upper_body_x, -body_lines_y], [upper_body_x, t_slkb], [l_slkp, t_slkb], [l_slkp, t_slkb + rm * rows + gc.silk_fab_offset * 2],
                                                        [lower_body_x, t_slkb+rm*rows+gc.silk_fab_offset*2], [lower_body_x, t_slkb+rm*rows-rm/2+gc.silk_fab_offset+body_lines_y]], layer='F.SilkS', width=gc.silk_line_width))
        else:
            kicad_modg.append(PolygonLine(shape=[[upper_body_x, t_slkb], [l_slkp, t_slkb], [l_slkp, t_slkb + rm * rows + gc.silk_fab_offset * 2],
                                                    [lower_body_x, t_slkb+rm*rows+gc.silk_fab_offset*2]], layer='F.SilkS', width=gc.silk_line_width))

    for r in range(0, rows):
        if r != 0:
            if r == 1 and rm/2 < body_min_y_square and cols == 1:
                if l_slkb < body_min_x_square:
                    kicad_modg.append(Line(start=[body_min_x_square, (r-1)*rm+rm/2], end=[l_slkp, (r-1)*rm+rm/2], layer='F.SilkS',width=gc.silk_line_width))
                else:
                    kicad_modg.append(Line(start=[l_slkb, (r-1)*rm+rm/2], end=[l_slkp, (r-1)*rm+rm/2], layer='F.SilkS',width=gc.silk_line_width))
            else:
                # add line between rows
                if l_slkb < body_min_x_round + (cols-1)*coldist:
                    kicad_modg.append(Line(start=[body_min_x_round+ (cols-1)*coldist, (r-1)*rm+rm/2], end=[l_slkp, (r-1)*rm+rm/2], layer='F.SilkS',width=gc.silk_line_width))
                else:
                    kicad_modg.append(Line(start=[l_slkb, (r-1)*rm+rm/2], end=[l_slkp, (r-1)*rm+rm/2], layer='F.SilkS',width=gc.silk_line_width))
                    if body_lines_y != False:
                        kicad_modg.append(Line(start=[l_slkb, (r-1)*rm+body_lines_y], end=[l_slkb, (r)*rm-body_lines_y], layer='F.SilkS',width=gc.silk_line_width))

        # pin outline
        if r != 0:
            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [l_slkp, r * rm - pin_width / 2 - gc.silk_fab_offset],
                        [l_slkp + pin_length, r * rm - pin_width / 2 - gc.silk_fab_offset],
                        [l_slkp + pin_length, r * rm + pin_width / 2 + gc.silk_fab_offset],
                        [l_slkp, r * rm + pin_width / 2 + gc.silk_fab_offset],
                    ],
                    layer="F.SilkS",
                    width=gc.silk_line_width,
                )
            )
        else:
            # color the first pin
            kicad_modg.append(
                Rectangle(
                    start=Vector2D(l_slkp, -pin_width / 2 - gc.silk_fab_offset),
                    end=Vector2D(l_slkp + pin_length, pin_width / 2 + gc.silk_fab_offset),
                    layer="F.SilkS",
                    width=gc.silk_line_width,
                    fill=True,
                )
            )

        # if body is starting at the pads
        if l_slkb-gc.silk_fab_offset > pad.x/2 + gc.silk_pad_clearance + (cols-1)*coldist:
            if r == 0 and cols == 1:
                # add the lines between pads and silkscreenbody
                kicad_modg.append(Line(start=[pad.x/2+ silk_pad_offset, r*rm-pin_width/2-gc.silk_fab_offset],
                    end=[l_slkb, r*rm-pin_width/2-gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[pad.x/2+ silk_pad_offset, r*rm+pin_width/2+gc.silk_fab_offset],
                    end=[l_slkb, r*rm+pin_width/2+gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
            else:
                # add the lines between pads and silkscreenbody
                kicad_modg.append(Line(start=[(cols-1)*coldist + pin_line_x, r*rm-pin_width/2-gc.silk_fab_offset],
                    end=[l_slkb, r*rm-pin_width/2-gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[(cols-1)*coldist + pin_line_x, r*rm+pin_width/2+gc.silk_fab_offset],
                    end=[l_slkb, r*rm+pin_width/2+gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))

        if cols > 1:
            for c in range(1, cols):
                # add the lines between pads
                start_point_x = (c-1)*coldist+pin_line_x
                end_point_x = c*coldist-pin_line_x
                if start_point_x < end_point_x - gc.silk_line_width:
                    if r == 0 and c == 1:
                        kicad_modg.append(Line(start=[pad.x/2 + silk_pad_offset, r*rm-pin_width/2-gc.silk_fab_offset],
                            end=[end_point_x, r*rm-pin_width/2-gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                        kicad_modg.append(Line(start=[pad.x/2 + silk_pad_offset, r*rm+pin_width/2+gc.silk_fab_offset],
                            end=[end_point_x, r*rm+pin_width/2+gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                    else:
                        kicad_modg.append(Line(start=[start_point_x, r*rm-pin_width/2-gc.silk_fab_offset],
                        end=[end_point_x, r*rm-pin_width/2-gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                        kicad_modg.append(Line(start=[start_point_x, r*rm+pin_width/2+gc.silk_fab_offset],
                        end=[end_point_x, r*rm+pin_width/2+gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))

    # pin 1 marker
    pin1_min = -(pad.x/2 + silk_pad_offset)
    if pin1_min < l_slk:
        pin1_x = pin1_min
    else:
        pin1_x = l_slk
    if pin1_min < t_slk:
        pin1_y = pin1_min
    else:
        pin1_y = t_slk
    kicad_modg.append(PolygonLine(shape=[[pin1_x, 0], [pin1_x, pin1_y], [0, pin1_y]], layer='F.SilkS', width=gc.silk_line_width))

    # create courtyard
    kicad_mod.append(RectLine(start=[roundCrt(l_crt + offset.x), roundCrt(t_crt + offset.y)],
                              end=[roundCrt(l_crt + offset.x + w_crt), roundCrt(t_crt + offset.y + h_crt)],
                              layer='F.CrtYd', width=gc.courtyard_line_width))

    # create pads
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_RECT
    pad_shapeother = Pad.SHAPE_OVAL
    pad_layers = Pad.LAYERS_THT

    p = 1

    for r in range(1, rows + 1):
        x1 = 0
        for c in range(1, cols + 1):
            if p == 1:
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[x1, y1], size=pad, drill=ddrill,
                                      layers=pad_layers))
            else:
                kicad_modg.append(
                    Pad(number=p, type=pad_type, shape=pad_shapeother, at=[x1, y1], size=pad, drill=ddrill,
                        layers=pad_layers))

            p = p + 1
            x1 = x1 + coldist

        y1 = y1 + rm

    # add model
    kicad_modg.append(
        Model(
            filename=global_config.model_3d_prefix
            + lib_name
            + ".3dshapes/"
            + footprint_name
            + global_config.model_3d_suffix
        )
    )

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)


#
#                                                          <-->pack_offset
#                 <--------------pack_width--------------->
#                                                             <-coldist>
#                 +---------------------------------------+            ---+
#                 |                                       |  OOO      OOO |          ^
#                 |                                       |  OOO ==== OOO |  ^       pin_width
#                 |                                       |  OOO      OOO    |       v
#                 +---------------------------------------+                  rm
#                 |                                       |  OOO      OOO    |
#                 |                                       |  OOO ==== OOO    v
#                 |                                       |  OOO      OOO
#                 +---------------------------------------+
#
def makeSocketStripAngled(
    global_config: GC.GlobalConfig,
    rows: int,
    cols: int,
    rm: float,
    coldist: float,
    pack_width: float,
    pack_offset: float,
    pin_width: float,
    ddrill: float,
    pad: Vec2DCompatible,
    tags_additional: list[str] = [],
    lib_name: str = "Socket_Strips",
    classname: str = "Socket_Strip",
    classname_description: str = "socket strip",
):
    gc = global_config
    pad = Vector2D(pad)
    crtyd_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)

    h_fabb = (rows - 1) * rm + rm / 2 + rm / 2
    w_fabb = -pack_width
    l_fabb = -1*(coldist * (cols - 1) + pack_offset)
    t_fabb = -rm / 2
    t_fabp = -pin_width / 2

    w_slkb = w_fabb - 2 * gc.silk_fab_offset
    l_slkb = l_fabb + gc.silk_fab_offset
    t_slkb = t_fabb - gc.silk_fab_offset
    l_slkp = l_slkb + w_slkb
    t_slkp = t_fabp - gc.silk_fab_offset

    w_crt = -1*(rm / 2 + (cols - 1) * coldist + pack_offset + pack_width  + 2 * crtyd_offset)
    h_crt = h_fabb + 2 * crtyd_offset
    l_crt = rm / 2 + crtyd_offset
    t_crt = -rm / 2 - crtyd_offset

    # if rm == 2.54:
    #    footprint_name = "Pin_Header_Angled_{0}x{1:02}".format(cols, rows)
    # else:
    footprint_name = "{3}_Angled_{0}x{1:02}_Pitch{2:03.2f}mm".format(cols, rows, rm, classname)

    description = "Through hole angled {4}, {0}x{1:02}, {2:03.2f}mm pitch, {3}mm socket length".format(cols, rows,
                                                                                                    rm,
                                                                                                    pack_width,
                                                                                                    classname_description)
    tags = "Through hole angled {3} THT {0}x{1:02} {2:03.2f}mm".format(cols, rows, rm, classname_description)
    if (cols == 1):
        description = description + ", single row"
        tags = tags + " single row"
    elif (cols == 2):
        description = description + ", double rows"
        tags = tags + " double row"
    elif (cols == 3):
        description = description + ", triple rows"
        tags = tags + " triple row"

    if (len(tags_additional) > 0):
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags = tags + " " + t

    print(footprint_name)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.description = description
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = Vector2D(0, 0)
    kicad_modg = Translation(offset)
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(name=Property.REFERENCE, text='REF**', at=[l_crt + w_crt / 2, t_crt + crtyd_offset - txt_offset], layer='F.SilkS'))
    kicad_modg.append(
        Text(text='${REFERENCE}', at=[l_crt + w_crt / 2, t_crt + crtyd_offset - txt_offset], layer='F.Fab'))
    kicad_modg.append(
        Property(name=Property.VALUE, text=footprint_name, at=[l_crt + w_crt / 2, t_crt + h_crt - crtyd_offset + txt_offset],
             layer='F.Fab'))

    # create FAB-layer
    y1 = t_fabb
    yp = t_fabp
    for r in range(1, rows + 1):
        kicad_modg.append(RectLine(start=[l_fabb, y1], end=[l_fabb + w_fabb, y1 + rm], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(
            RectLine(start=[0, yp], end=[l_fabb , yp + pin_width], layer='F.Fab', width=gc.fab_line_width))
        y1 = y1 + rm
        yp = yp + rm

    # create SILKSCREEN-layer + pin1 marker
    y1 = t_slkb
    yp = t_slkp
    for r in range(1, rows + 1):
        if (rows == 1 and r == 1):
            kicad_modg.append(
                RectLine(start=[l_slkb, y1], end=[l_slkp, y1 + rm + 2 * gc.silk_fab_offset], layer='F.SilkS',
                         width=gc.silk_line_width))
        if (r == 1 or r == rows):
            kicad_modg.append(RectLine(start=[l_slkb, y1], end=[l_slkp, y1 + rm + gc.silk_fab_offset], layer='F.SilkS',
                                       width=gc.silk_line_width))
            y1 = y1 + gc.silk_fab_offset
        else:
            kicad_modg.append(RectLine(start=[l_slkb, y1], end=[l_slkp, y1 + rm], layer='F.SilkS', width=gc.silk_line_width))

        kicad_modg.append(Line(start=[-1*((cols - 1) * coldist + pad.x / 2 + gc.silk_fab_offset+gc.silk_line_width), yp], end=[l_slkb, yp], layer='F.SilkS',width=gc.silk_line_width))
        kicad_modg.append(Line(start=[-1*((cols - 1) * coldist + pad.x / 2 + gc.silk_fab_offset+gc.silk_line_width), yp + pin_width + 2 * gc.silk_fab_offset],end=[l_slkb, yp + pin_width + 2 * gc.silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
        if cols > 1:
            for c in range(2, cols + 1):
                kicad_modg.append(Line(start=[-1*((c - 2) * coldist + pad.x / 2 + gc.silk_fab_offset+gc.silk_line_width), yp],
                                       end=[-1*((c - 1) * coldist - pad.x / 2 - gc.silk_fab_offset-gc.silk_line_width), yp], layer='F.SilkS',
                                       width=gc.silk_line_width))
                kicad_modg.append(
                    Line(start=[-1*((c - 2) * coldist + pad.x / 2 + gc.silk_fab_offset+gc.silk_line_width), yp + pin_width + 2 * gc.silk_fab_offset],
                         end=[-1*((c - 1) * coldist - pad.x / 2 - gc.silk_fab_offset-gc.silk_line_width), yp + pin_width + 2 * gc.silk_fab_offset],
                         layer='F.SilkS', width=gc.silk_line_width))
        if r == 1:
            y = y1 + gc.silk_line_width
            while y < y1 + rm + 2 * gc.silk_fab_offset:
                kicad_modg.append(Line(start=[l_slkb, y], end=[l_slkp, y], layer='F.SilkS', width=gc.silk_line_width))
                y = y + gc.silk_line_width
        y1 = y1 + rm
        yp = yp + rm

    kicad_modg.append(PolygonLine(shape=[[0, -rm / 2], [rm / 2, -rm / 2], [rm / 2, 0]], layer='F.SilkS', width=gc.silk_line_width))

    # create courtyard
    kicad_mod.append(RectLine(start=[roundCrt(l_crt + offset.x), roundCrt(t_crt + offset.y)],
                              end=[roundCrt(l_crt + offset.x + w_crt), roundCrt(t_crt + offset.y + h_crt)],
                              layer='F.CrtYd', width=gc.courtyard_line_width))

    # create pads
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_RECT
    pad_shapeother = Pad.SHAPE_OVAL
    pad_layers = Pad.LAYERS_THT

    p = 1
    for r in range(1, rows + 1):
        x1 = 0
        for c in range(1, cols + 1):
            if p == 1:
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[x1, y1], size=pad, drill=ddrill,
                                      layers=pad_layers))
            else:
                kicad_modg.append(
                    Pad(number=p, type=pad_type, shape=pad_shapeother, at=[x1, y1], size=pad, drill=ddrill,
                        layers=pad_layers))

            p = p + 1
            x1 = x1 - coldist

        y1 = y1 + rm

    # add model
    kicad_modg.append(
        Model(
            filename=global_config.model_3d_prefix
            + lib_name
            + ".3dshapes/"
            + footprint_name
            + global_config.model_3d_suffix
        )
    )

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)


def makePinHeadStraightSMD(
    global_config: GC.GlobalConfig,
    rows: int,
    cols: int,
    rm: float,
    coldist: float,
    rmx_pad_offset: float,
    rmx_pin_length: float,
    pin_width: float,
    package_width: float,
    overlen_top: float,
    overlen_bottom: float,
    pad: Vec2DCompatible,
    start_left: bool = True,
    tags_additional: list[str] = [],
    lib_name: str = "Pin_Headers",
    classname: str = "Pin_Header",
    classname_description: str = "pin header",
    isSocket: bool = False,
):
    gc = global_config
    pad = Vector2D(pad)
    crtyd_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)

    # This is set a bit further out than normal, not quite clear why.
    # silk_pad_offset = gc.silk_pad_offset
    silk_pad_offset = gc.silk_pad_clearance + gc.silk_fab_offset

    ddrill=0.5
    h_fab = (rows - 1) * rm + overlen_top + overlen_bottom
    w_fab = package_width
    l_fab = (coldist * (cols - 1) - w_fab) / 2
    t_fab = -overlen_top

    h_slk = h_fab + 2 * gc.silk_fab_offset
    w_slk = max(w_fab + 2 * gc.silk_fab_offset, coldist * (cols - 1) - pad.x - 4 * gc.silk_fab_offset)
    l_slk = (coldist * (cols - 1) - w_slk) / 2
    t_slk = -overlen_top - gc.silk_fab_offset

    w_crt = max(package_width, coldist * (cols - 1)+2*rmx_pad_offset + pad.x) + 2 * crtyd_offset
    h_crt = max(h_fab, (rows - 1) * rm + pad.y) + 2 * crtyd_offset
    l_crt = coldist * (cols - 1) / 2 - w_crt / 2
    t_crt = (rows - 1) * rm / 2 - h_crt / 2

    # if rm == 2.54:
    #    footprint_name = "Pin_Header_Straight_{0}x{1:02}".format(cols, rows)
    # else:
    footprint_name = "{3}_{0}x{1:02}_P{2:03.2f}mm_Vertical_SMD".format(cols, rows, rm,classname)

    description = "surface-mounted straight {3}, {0}x{1:02}, {2:03.2f}mm pitch".format(cols, rows, rm,classname_description)
    tags = "Surface mounted {3} SMD {0}x{1:02} {2:03.2f}mm".format(cols, rows, rm,classname_description)
    if (cols == 1):
        description = description + ", single row"
        tags = tags + " single row"
        if start_left:
            description = description + ", style 1 (pin 1 left)"
            tags = tags + " style1 pin1 left"
            footprint_name = footprint_name + "_Pin1Left"
        else:
            description = description + ", style 2 (pin 1 right)"
            tags = tags + " style2 pin1 right"
            footprint_name = footprint_name + "_Pin1Right"
    elif (cols == 2):
        description = description + ", double rows"
        tags = tags + " double row"

    if (len(tags_additional) > 0):
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags = tags + " " + t

    print(footprint_name)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.description = description
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = Vector2D(-(cols-1)*coldist/2, -(rows-1)*rm/2.0)

    kicad_modg = Translation(offset)
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(name=Property.REFERENCE, text='REF**', at=[coldist * (cols - 1) / 2, t_slk - txt_offset], layer='F.SilkS'))
    kicad_modg.append(
        Text(text='${REFERENCE}', at=[rm/2*(cols-1),(rows-1)*rm/2.0], rotation=90, layer='F.Fab'))
    kicad_modg.append(
        Property(name=Property.VALUE, text=footprint_name, at=[coldist * (cols - 1) / 2, t_slk + h_slk + txt_offset], layer='F.Fab'))

    cleft = range(0, rows, 2)
    cright = range(1, rows, 2)
    if not start_left:
        cleft = range(1, rows, 2)
        cright = range(0, rows, 2)

    # create FAB-layer
    chamfer = (rm-pin_width)/2
    kicad_modg.append(Line(start=[l_fab + w_fab, t_fab+h_fab], end=[l_fab, t_fab+h_fab], layer='F.Fab', width=gc.fab_line_width))
    if start_left == True:
        kicad_modg.append(Line(start=[l_fab + chamfer, t_fab], end=[l_fab + w_fab, t_fab], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fab, t_fab+h_fab], end=[l_fab, t_fab+chamfer], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fab, t_fab+chamfer], end=[l_fab + chamfer, t_fab], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fab + w_fab, t_fab], end=[l_fab + w_fab, t_fab+h_fab], layer='F.Fab', width=gc.fab_line_width))
    else:
        kicad_modg.append(Line(start=[l_fab, t_fab], end=[l_fab + w_fab - chamfer, t_fab], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fab + w_fab, t_fab+h_fab], end=[l_fab + w_fab, t_fab+chamfer], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fab + w_fab, t_fab+chamfer], end=[l_fab + w_fab - chamfer, t_fab], layer='F.Fab', width=gc.fab_line_width))
        kicad_modg.append(Line(start=[l_fab, t_fab], end=[l_fab, t_fab+h_fab], layer='F.Fab', width=gc.fab_line_width))

    if cols==1:
        for c in cleft:
            kicad_modg.append(Line(start=[l_fab, c*rm-pin_width/2], end=[-rmx_pin_length, c*rm-pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[-rmx_pin_length, c*rm-pin_width/2], end=[-rmx_pin_length, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[-rmx_pin_length, c*rm+pin_width/2], end=[l_fab, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
        for c in cright:
            kicad_modg.append(Line(start=[l_fab + w_fab, c*rm-pin_width/2], end=[rmx_pin_length, c*rm-pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[rmx_pin_length, c*rm-pin_width/2], end=[rmx_pin_length, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[rmx_pin_length, c*rm+pin_width/2], end=[l_fab + w_fab, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
    elif cols == 2:
        for c in range(0,rows):
            kicad_modg.append(Line(start=[l_fab, c*rm-pin_width/2], end=[-rmx_pin_length+rm/2, c*rm-pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[-rmx_pin_length+rm/2, c*rm-pin_width/2], end=[-rmx_pin_length+rm/2, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[-rmx_pin_length+rm/2, c*rm+pin_width/2], end=[l_fab, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[l_fab + w_fab, c*rm-pin_width/2], end=[rm/2+rmx_pin_length, c*rm-pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[rm/2+rmx_pin_length, c*rm-pin_width/2], end=[rm/2+rmx_pin_length, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))
            kicad_modg.append(Line(start=[rm/2+rmx_pin_length, c*rm+pin_width/2], end=[l_fab + w_fab, c*rm+pin_width/2], layer='F.Fab', width=gc.fab_line_width))

    # create SILKSCREEN-layer + pin1 marker
    slk_offset_pad = pad.y/2 + silk_pad_offset
    kicad_modg.append(Line(start=[l_slk, t_slk], end=[l_slk + w_slk, t_slk], layer='F.SilkS', width=gc.silk_line_width))
    kicad_modg.append(Line(start=[l_slk, t_slk+h_slk], end=[l_slk + w_slk, t_slk+h_slk], layer='F.SilkS', width=gc.silk_line_width))

    if cols == 1:
        for c in cleft:
            if c == 0:
                kicad_modg.append(Line(start=[l_slk , -slk_offset_pad], end=[-rmx_pad_offset-pad.x/2+gc.silk_line_width/2 , -slk_offset_pad], layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk , t_slk], end=[l_slk, -slk_offset_pad], layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk+w_slk, (rows-1)*rm+slk_offset_pad],end=[l_slk+w_slk, t_slk+h_slk],layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk+w_slk, -slk_offset_pad], end=[l_slk+w_slk, min(t_slk+h_slk,(c+1) * rm - slk_offset_pad)], layer='F.SilkS', width=gc.silk_line_width))
            elif c == rows-1:
                kicad_modg.append(Line(start=[l_slk+w_slk, max(t_slk, (c-1) * rm + slk_offset_pad)], end=[l_slk+w_slk, t_slk+h_slk], layer='F.SilkS', width=gc.silk_line_width))
            else:
                kicad_modg.append(Line(start=[l_slk+w_slk, max(t_slk, (c-1) * rm + slk_offset_pad)], end=[l_slk+w_slk, min(t_slk+h_slk,(c+1) * rm - slk_offset_pad)], layer='F.SilkS', width=gc.silk_line_width))
        for c in cright:
            if c == 0:
                kicad_modg.append(Line(start=[l_slk+w_slk, -slk_offset_pad],end=[rmx_pad_offset+pad.x/2-gc.silk_line_width/2, -slk_offset_pad],layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk+w_slk, t_slk],end=[l_slk+w_slk, -slk_offset_pad],layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk, (rows-1)*rm+slk_offset_pad],end=[l_slk, t_slk+h_slk],layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk , -slk_offset_pad],end=[l_slk, min(t_slk+h_slk,(c+1) * rm - slk_offset_pad)], layer='F.SilkS',width=gc.silk_line_width))
            if c == rows-1:
                kicad_modg.append(Line(start=[l_slk , max(t_slk, (c-1) * rm + slk_offset_pad)],end=[l_slk, t_slk+h_slk], layer='F.SilkS',width=gc.silk_line_width))
            else:
                kicad_modg.append(Line(start=[l_slk , max(t_slk, (c-1) * rm + slk_offset_pad)],end=[l_slk, min(t_slk+h_slk,(c+1) * rm - slk_offset_pad)], layer='F.SilkS',width=gc.silk_line_width))
    if (cols==2):
        if isSocket:
            # print(pad.x/2+rmx_pad_offset,pad.x/2,rmx_pad_offset)
            kicad_modg.append(Line(start=[pad.x/2+rmx_pad_offset+coldist, -(pad.y / 2 + 2*gc.silk_line_width + gc.silk_fab_offset)], end=[l_slk+w_slk, -(pad.y / 2 + 2*gc.silk_line_width + gc.silk_fab_offset)], layer='F.SilkS', width=gc.silk_line_width))
        else:
            kicad_modg.append(Line(start=[-rmx_pad_offset+rm/2-pad.x/2+gc.silk_line_width/2, -slk_offset_pad], end=[l_slk, -slk_offset_pad], layer='F.SilkS', width=gc.silk_line_width))
            kicad_modg.append(Line(start=[l_slk , t_slk], end=[l_slk, -slk_offset_pad], layer='F.SilkS', width=gc.silk_line_width))
            kicad_modg.append(Line(start=[l_slk+w_slk , t_slk], end=[l_slk+w_slk, -slk_offset_pad], layer='F.SilkS', width=gc.silk_line_width))
            kicad_modg.append(Line(start=[l_slk, (rows-1)*rm+slk_offset_pad],end=[l_slk, t_slk+h_slk],layer='F.SilkS', width=gc.silk_line_width))
            kicad_modg.append(Line(start=[l_slk+w_slk, (rows-1)*rm+slk_offset_pad],end=[l_slk+w_slk, t_slk+h_slk],layer='F.SilkS', width=gc.silk_line_width))
        if slk_offset_pad*2 < rm - gc.silk_line_width*2:
            for c in range(0,rows-1):
                kicad_modg.append(Line(start=[l_slk, c*rm+slk_offset_pad],end=[l_slk, (c+1)*rm-slk_offset_pad],layer='F.SilkS', width=gc.silk_line_width))
                kicad_modg.append(Line(start=[l_slk+w_slk, c*rm+slk_offset_pad],end=[l_slk+w_slk, (c+1)*rm-slk_offset_pad],layer='F.SilkS', width=gc.silk_line_width))
    # create courtyard
    kicad_mod.append(RectLine(start=[roundCrt(l_crt + offset.x), roundCrt(t_crt + offset.y)],
                              end=[roundCrt(l_crt + offset.x + w_crt), roundCrt(t_crt + offset.y + h_crt)],
                              layer='F.CrtYd', width=gc.courtyard_line_width))

    # create pads
    pad_type = Pad.TYPE_SMT
    pad_shape1 = Pad.SHAPE_RECT
    pad_layers = Pad.LAYERS_SMT

    if cols==1:
        for c in cleft:
            kicad_modg.append(Pad(number=c+1, type=pad_type, shape=pad_shape1, at=[-rmx_pad_offset, c*rm], size=pad, drill=ddrill,layers=pad_layers))
        for c in cright:
            kicad_modg.append(Pad(number=c+1, type=pad_type, shape=pad_shape1, at=[rmx_pad_offset, c * rm], size=pad, drill=ddrill,layers=pad_layers))
    elif cols==2:
        p = 1
        for c in range(0,rows):
            if isSocket:
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[rm/2+rmx_pad_offset, c * rm], size=pad, drill=ddrill,layers=pad_layers))
                p=p+1
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[-rmx_pad_offset+rm/2, c * rm], size=pad, drill=ddrill, layers=pad_layers))
                p=p+1
            else:
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[-rmx_pad_offset+rm/2, c * rm], size=pad, drill=ddrill, layers=pad_layers))
                p=p+1
                kicad_modg.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[rmx_pad_offset+rm/2, c * rm], size=pad, drill=ddrill,layers=pad_layers))
                p=p+1

    # add model
    kicad_modg.append(
        Model(
            filename=global_config.model_3d_prefix
            + lib_name
            + ".3dshapes/"
            + footprint_name
            + global_config.model_3d_suffix
        )
    )

    lib = KicadPrettyLibrary(lib_name, None)
    lib.save(kicad_mod)
