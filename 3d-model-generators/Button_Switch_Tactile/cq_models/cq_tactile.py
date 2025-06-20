#!/usr/bin/env python3

# CadQuery script for generating tactile button 3D models
#
# Copyright (c) 2015 Maurice https://launchpad.net/~easyw
# Copyright (c) 2020 Mountyrox https://github.com/mountyrox
# Copyright (c) 2024-2025 Martin Sotirov <martin@libtec.org>
#
# All trademarks within this guide belong to their legitimate owners.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (LGPL)
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
# For detail see the LICENCE text file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import cadquery as cq

from _tools.utils import bodygen, make_z_chamfer, make_z_fillet, pingen, shellgen


def _make_body_gnd_straight_pin_pocket(params, gnd_pin_index, gnd_pin_params):
    direction = gnd_pin_params[1]
    px = gnd_pin_params[2]
    py = gnd_pin_params[3]
    bottom_height = gnd_pin_params[4]
    width = gnd_pin_params[5]

    height = params["shell_height"] - bottom_height
    thickness = params["shell_thickness"]

    if direction == 0:
        px -= thickness
        if px < params["body_width"] / 2:
            thickness = params["body_width"] / 2 - px
    elif direction == 180:
        px += thickness
        if -px < params["body_width"] / 2:
            thickness = params["body_width"] / 2 + px
    elif direction == 90:
        py -= thickness
        if py < params["body_length"] / 2:
            thickness = params["body_length"] / 2 - py
    elif direction == 270:
        py += thickness
        if -py < params["body_length"] / 2:
            thickness = params["body_length"] / 2 + py
    else:
        raise ValueError(
            f"gnd_pin {gnd_pin_index + 1}: Direction can only in steps of 90 degrees"
        )

    body = cq.Workplane("YZ", origin=(0, 0, bottom_height + height / 2))
    body = body.rect(width, height)
    body = body.extrude(thickness)

    body = body.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.translate((px, py, 0))

    return body


def _make_body_gnd_pin_pockets(body, params):
    gnd_pins = params.get("gnd_pin", [])

    for gnd_pin_index, gnd_pin_params in enumerate(gnd_pins):
        pin_type = gnd_pin_params[0]

        if pin_type == "straight":
            gnd_pin_pocket = _make_body_gnd_straight_pin_pocket(
                params, gnd_pin_index, gnd_pin_params
            )
            body = body.cut(gnd_pin_pocket)
        elif pin_type == "gullwing":
            continue
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index + 1}: Unknown pin type: {pin_type}"
            )

    return body


def make_body(params):
    body_board_distance = params.get("body_board_distance", 0)

    body = cq.Workplane("XY", origin=(0, 0, body_board_distance))
    body = body.rect(params["body_width"], params["body_length"])
    body = body.extrude(params["body_height"] - body_board_distance)

    body = make_z_chamfer(body, params.get("body_corner_chamfer"))
    body = make_z_fillet(body, params.get("body_corner_fillet"))
    body = bodygen.make_body_top_clip_pocket(body, params)
    body = bodygen.make_body_shell_sides(body, params)
    body = _make_body_gnd_pin_pockets(body, params)
    body = bodygen.make_body_pin_pockets(body, params)
    body = bodygen.make_body_features(body, params)
    # Pegs must be under features:
    body = bodygen.make_body_pegs(body, params)

    return body


def _make_actuator_cover_round(params):
    body = cq.Workplane("XZ")

    top_height = params["actuator_cover_height"]
    mid_height = params.get("actuator_cover_mid_height")

    body = body.moveTo(0, params["shell_height"])

    if mid_height is None:
        r = params["actuator_cover_diameter"] / 2

        top_fillet = params.get("actuator_cover_top_fillet", 0)
        bot_fillet = params.get("actuator_cover_bottom_fillet", 0)

        body = body.lineTo(r + bot_fillet, params["shell_height"])
        if bot_fillet:
            body = body.radiusArc((r, params["shell_height"] + bot_fillet), bot_fillet)

        body = body.lineTo(r, top_height - top_fillet)
        if top_fillet:
            body = body.radiusArc((r - top_fillet, top_height), -top_fillet)
    else:
        mid_r = params["actuator_cover_diameter"] / 2
        top_r = params["actuator_cover_top_diameter"] / 2

        bot_fillet = params.get("actuator_cover_bottom_fillet", 0)
        mid_outer_fillet = params.get("actuator_cover_mid_outer_fillet", 0)
        mid_inner_fillet = params.get("actuator_cover_mid_inner_fillet", 0)

        body = body.lineTo(mid_r + bot_fillet, params["shell_height"])
        if bot_fillet:
            body = body.radiusArc(
                (mid_r, params["shell_height"] + bot_fillet), bot_fillet
            )

        body = body.lineTo(mid_r, mid_height - mid_outer_fillet)
        if mid_outer_fillet:
            body = body.radiusArc(
                (mid_r - mid_outer_fillet, mid_height), -mid_outer_fillet
            )

        body = body.lineTo(top_r + mid_inner_fillet, mid_height)
        if mid_inner_fillet:
            body = body.radiusArc(
                (top_r, mid_height + mid_inner_fillet), mid_inner_fillet
            )

        body = body.lineTo(top_r, top_height)

    body = body.lineTo(0, top_height)
    body = body.close()
    body = body.revolve()

    return body


def _make_actuator_cover_rectangular(params):
    corner_chamfer = params.get("actuator_cover_corner_chamfer")

    body = cq.Workplane("XY", origin=(0, 0, params["shell_height"]))
    body = body.rect(params["actuator_cover_length"], params["actuator_cover_width"])
    body = body.extrude(
        params["actuator_cover_height"] - params["shell_height"],
        taper=params.get("actuator_cover_taper"),
    )

    if corner_chamfer:
        body = body.edges("not(<Z or >Z)")
        body = body.chamfer(*corner_chamfer)

    return body


def _make_shell_top_actuator_hole(shell_body, params):
    actuator_type = params["actuator_type"]
    if actuator_type == "top-round":
        return _make_shell_top_round_actuator_hole(shell_body, params)
    elif actuator_type == "top-obround":
        return _make_shell_top_obround_actuator_hole(shell_body, params)
    elif actuator_type == "top-rectangle":
        return _make_shell_top_rectangle_actuator_hole(shell_body, params)
    elif actuator_type == "top-rectangle-round":
        return _make_shell_top_rectangle_round_actuator_hole(shell_body, params)
    elif actuator_type == "top-hex":
        return _make_shell_top_hex_actuator_hole(shell_body, params)
    elif actuator_type == "side-rectangle":
        return shell_body
    else:
        raise ValueError(f"Unknown actuator type: {actuator_type}")


def _make_shell_straight_pin(params, gnd_pin_index, gnd_pin_params):
    gnd_pin_params = gnd_pin_params[1:]
    direction = gnd_pin_params.pop(0) % 360
    px = gnd_pin_params.pop(0)
    py = gnd_pin_params.pop(0)
    bottom_height = gnd_pin_params.pop(0)
    w = gnd_pin_params.pop(0)

    top_height = params["shell_height"] - params["shell_thickness"]
    bridge_width = w

    tip_chamfer = None
    tip_fillet = None
    top_width = None
    mid_top_height = None
    mid_bottom_height = None

    while gnd_pin_params:
        param_name = gnd_pin_params.pop(0)
        param_value = gnd_pin_params.pop(0)
        if param_name == "tip_chamfer":
            tip_chamfer = param_value
        elif param_name == "tip_fillet":
            tip_fillet = param_value
        elif param_name == "top_width":
            top_width = param_value
            bridge_width = top_width
        elif param_name == "mid_top_height":
            mid_top_height = param_value
        elif param_name == "mid_bottom_height":
            mid_bottom_height = param_value
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index}: Unknown extra parameter: {param_name}"
            )

    if top_width is not None and None in [mid_top_height, mid_bottom_height]:
        raise ValueError(
            f"gnd_pin {gnd_pin_index}: The 'top_width' parameter also needs 'mid_top_height' and 'mid_bottom_height' parameters"
        )

    if direction == 0:
        bridge_shell_length = params["shell_width"]
        bridge_side_distance = px
        bridge_x = py
    elif direction == 180:
        bridge_shell_length = params["shell_width"]
        bridge_side_distance = -px
        bridge_x = -py
    elif direction == 90:
        bridge_shell_length = params["shell_length"]
        bridge_side_distance = py
        bridge_x = -px
    elif direction == 270:
        bridge_shell_length = params["shell_length"]
        bridge_side_distance = -py
        bridge_x = px
    else:
        raise ValueError(
            f"gnd_pin {gnd_pin_index + 1}: Direction can only in steps of 90 degrees"
        )

    body = cq.Workplane("YZ")
    body = body.moveTo(w / -2, bottom_height)
    if top_width is not None:
        body = body.lineTo(w / -2, mid_bottom_height)
        body = body.lineTo(top_width / -2, mid_top_height)
        body = body.lineTo(top_width / -2, top_height)
        body = body.lineTo(top_width / 2, top_height)
        body = body.lineTo(top_width / 2, mid_top_height)
        body = body.lineTo(w / 2, mid_bottom_height)
    else:
        body = body.lineTo(w / -2, top_height)
        body = body.lineTo(w / 2, top_height)
    body = body.lineTo(w / 2, bottom_height)
    body = body.close()

    body = body.extrude(-params["shell_thickness"])

    body = body.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.translate((px, py, 0))

    if tip_chamfer:
        body = body.edges("<Z and |Y").chamfer(tip_chamfer[1], tip_chamfer[0])
    if tip_fillet:
        body = body.edges("<Z and |Y").fillet(tip_fillet)

    bridge = shellgen._make_shell_side_bridge(
        params, bridge_shell_length, bridge_side_distance, bridge_width, bridge_x
    )
    bridge = bridge.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.union(bridge)

    return body


def _make_shell_gullwing_pin(params, gnd_pin_index, gnd_pin_params):
    gnd_pin_params = gnd_pin_params[1:]
    direction = gnd_pin_params.pop(0) % 360
    tip_x = gnd_pin_params.pop(0)
    tip_y = gnd_pin_params.pop(0)
    pin_width = gnd_pin_params.pop(0)

    top_width = pin_width
    bottom_width = pin_width
    mid_top_height = params["shell_height"] * 0.50
    mid_bottom_height = params["shell_height"] * 0.25

    top_height = None
    top_length = None
    bottom_length = None

    while gnd_pin_params:
        param_name = gnd_pin_params.pop(0)
        param_value = gnd_pin_params.pop(0)
        if param_name == "top_height":
            top_height = param_value
        elif param_name == "top_width":
            top_width = param_value
        elif param_name == "top_length":
            top_length = param_value
        elif param_name == "mid_top_height":
            mid_top_height = param_value
        elif param_name == "mid_bottom_height":
            mid_bottom_height = param_value
        elif param_name == "bottom_length":
            bottom_length = param_value
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index}: Unknown extra parameter: {param_name}"
            )

    if direction == 0:
        pin_length = tip_x - params["shell_width"] / 2
    elif direction == 180:
        pin_length = -params["shell_width"] / 2 - tip_x
    elif direction == 90:
        pin_length = tip_y - params["shell_length"] / 2
    elif direction == 270:
        pin_length = -params["shell_length"] / 2 - tip_y
    else:
        raise ValueError(
            f"gnd_pin {gnd_pin_index + 1}: Direction can only in steps of 90 degrees"
        )

    pt = params["shell_thickness"]

    if top_height is None:
        top_height = params["shell_height"]

    body = pingen.make_gullwing_pin(
        {
            "pin_width": top_width,
            "pin_thickness": pt,
            "pin_length": pin_length,
            "pin_top_height": top_height,
            "pin_top_length": top_length,
            "pin_bottom_length": bottom_length,
            "pin_corner_radius": pt,
        }
    )

    if bottom_width < top_width:
        cut = cq.Workplane("YZ")
        cut = cut.moveTo(bottom_width / 2, 0)
        cut = cut.lineTo(bottom_width / 2, mid_bottom_height)
        cut = cut.lineTo(top_width / 2, mid_top_height)
        cut = cut.lineTo(top_width / 2, 0)
        cut = cut.close()
        cut = cut.extrude(-pin_length)
        cut = cut.union(cut.mirror("XZ"))
        body = body.cut(cut)

    body = body.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.translate((tip_x, tip_y, 0))

    return body


def _make_gnd_pin(params, gnd_pin_index, gnd_pin_params):
    pin_type = gnd_pin_params[0]

    if pin_type == "straight":
        body = _make_shell_straight_pin(params, gnd_pin_index, gnd_pin_params)
    elif pin_type == "gullwing":
        body = _make_shell_gullwing_pin(params, gnd_pin_index, gnd_pin_params)
    else:
        raise ValueError(f"gnd_pin {gnd_pin_index + 1}: Unknown pin type: {pin_type}")

    return body


def _make_shell_top(params):
    body = cq.Workplane(
        "XY", origin=(0, 0, params["shell_height"] - params["shell_thickness"])
    )
    body = body.rect(params["shell_width"], params["shell_length"])
    body = body.extrude(params["shell_thickness"])

    body = make_z_chamfer(body, params.get("shell_corner_chamfer"))
    body = make_z_fillet(body, params.get("shell_corner_fillet"))
    body = shellgen.make_shell_top_clip(body, params)
    body = shellgen.make_shell_top_lips(body, params)

    return body


def make_shell(params):
    body = _make_shell_top(params)

    actuator_cover_type = params.get("actuator_cover_type")
    if actuator_cover_type == "round":
        body = body.union(_make_actuator_cover_round(params))
    elif actuator_cover_type == "rectangular":
        body = body.union(_make_actuator_cover_rectangular(params))
    elif actuator_cover_type:
        raise ValueError(f"Unknown actuator cover type: {actuator_cover_type}")

    body = _make_shell_top_actuator_hole(body, params)
    body = shellgen.make_shell_sides(body, params)

    gnd_pins = params.get("gnd_pin", [])
    for gnd_pin_index, gnd_pin_params in enumerate(gnd_pins):
        gnd_pin_body = _make_gnd_pin(params, gnd_pin_index, gnd_pin_params)
        body = body.union(gnd_pin_body)

    return body


def make_base(params):
    if not params.get("base_width") and not params.get("base_height"):
        return

    w = params["base_width"]
    l = params["base_length"]

    body = cq.Workplane("XY", origin=(0, 0, params["body_height"]))
    body = body.rect(w, l)
    body = body.extrude(params["base_height"] - params["body_height"])

    if params.get("base_corner_chamfer"):
        body = body.edges("|Z").chamfer(*params["base_corner_chamfer"])
    if params.get("base_corner_fillet"):
        body = body.edges("|Z").fillet(params["base_corner_fillet"])

    if params.get("base_top_chamfer"):
        body = body.edges(">Z").chamfer(*params["base_top_chamfer"])
    if params.get("base_top_fillet"):
        body = body.edges(">Z").fillet(params["base_top_fillet"])

    return body


def _make_shell_top_round_actuator_hole(shell_body, params):
    p = params.copy()
    if type(p["actuator_height"]) is list:
        p["actuator_height"] = p["actuator_height"][0]
    if type(p["actuator_diameter"]) is list:
        p["actuator_diameter"] = p["actuator_diameter"][0]
    p["actuator_diameter"] += params["actuator_shell_gap"] * 2
    p["actuator_zcut"] = None
    p["actuator_top_chamfer"] = None
    p["actuator_top_fillet"] = None

    actuator_body = _make_top_round_actuator(p)
    shell_body = shell_body.cut(actuator_body)
    return shell_body


def _make_top_round_actuator(params):
    body_height = params["body_height"]
    shell_bottom = params["shell_height"] - params["shell_thickness"]
    bot = shell_bottom if shell_bottom < body_height else body_height

    top_list = params["actuator_height"]
    if type(top_list) is not list:
        top_list = [top_list]

    dia_list = params["actuator_diameter"]
    if type(dia_list) is not list:
        dia_list = [dia_list]

    if len(top_list) != len(dia_list):
        raise ValueError(
            f"Parameters 'actuator_height' and 'actuator_diameter' must have the same amount elements"
        )

    body = cq.Workplane("XZ")
    body = body.moveTo(0, bot)
    body = body.lineTo(dia_list[0] / 2, bot)
    for index, dia in enumerate(dia_list):
        top = top_list[index]
        body = body.lineTo(dia / 2, top)
    body = body.lineTo(0, top_list[-1])
    body = body.close()
    body = body.revolve()

    actuator_zcut = params.get("actuator_zcut")
    if actuator_zcut:
        zcut_distance = actuator_zcut[0]
        zcut_direction = actuator_zcut[1]

        r = dia_list[0] / 2
        zcut = cq.Workplane("XY", origin=(zcut_distance + r, 0, 0))
        zcut = zcut.rect(r * 2, r * 2)
        zcut = zcut.extrude(params["actuator_height"])
        zcut = zcut.rotate((0, 0, 0), (0, 0, 1), 90.0)
        body = body.cut(zcut)

    if params.get("actuator_top_fillet"):
        body = body.edges("not <Z").fillet(params["actuator_top_fillet"])
    if params.get("actuator_top_chamfer"):
        body = body.edges("not <Z").chamfer(*params["actuator_top_chamfer"])

    return body


def _make_shell_top_obround_actuator_hole(shell_body, params):
    params = params.copy()
    params["actuator_width"] += params["actuator_shell_gap"] * 2
    params["actuator_length"] += params["actuator_shell_gap"] * 2
    params["actuator_top_chamfer"] = None
    params["actuator_top_fillet"] = None

    actuator_body = _make_top_obround_actuator(params)
    shell_body = shell_body.cut(actuator_body)
    return shell_body


def _make_top_obround_actuator(params):
    body_h = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if shell_bottom_h < body_h:
        body_h = shell_bottom_h

    w = params["actuator_width"]
    l = params["actuator_length"]
    r = l / 2

    body = cq.Workplane("XY", origin=(0, 0, body_h))
    body = body.moveTo(0, r)
    body = body.lineTo((w - l) / 2, r)
    body = body.radiusArc(((w - l) / 2, -r), r)
    body = body.lineTo(0, -r)
    body = body.close()

    body = body.extrude(params["actuator_height"] - body_h)
    body = body.union(body.mirror("YZ"))

    if params.get("actuator_top_fillet"):
        body = body.edges(">Z").fillet(params["actuator_top_fillet"])
    if params.get("actuator_top_chamfer"):
        body = body.edges(">Z").chamfer(*params["actuator_top_chamfer"])

    return body


def _make_shell_top_rectangle_actuator_hole(body, params):
    params = params.copy()

    if params.get("actuator_round_base_diameter"):
        params["actuator_round_base_diameter"] += params["actuator_shell_gap"] * 2
        params["actuator_round_base_chamfer"] = None
        params["actuator_round_base_fillet"] = None

    w = params["actuator_width"]
    w = w.copy() if type(w) is list else [w]
    for i in range(len(w)):
        w[i] += params["actuator_shell_gap"] * 2
    params["actuator_width"] = w

    if params.get("actuator_length") is not None:
        l = params["actuator_length"]
        l = l.copy() if type(l) is list else [l]
        for i in range(len(l)):
            l[i] += params["actuator_shell_gap"] * 2
        params["actuator_length"] = l

    params["actuator_chamfer"] = None
    params["actuator_fillet"] = None

    actuator = _make_top_rectangle_actuator(params)
    body = body.cut(actuator)

    return body


def _make_top_rectangle_actuator(params):
    h = params["actuator_height"]
    h = h.copy() if type(h) is list else [h]

    if len(h) == 0:
        raise ValueError(f"Parameter 'actuator_height' must have at least one element")

    w = params["actuator_width"]
    w = w.copy() if type(w) is list else [w]

    l = params.get("actuator_length", w)
    l = l.copy() if type(l) is list else [l]

    if len(w) == 0:
        raise ValueError(f"Parameter 'actuator_width' must have at least one element")

    if len(l) != len(w):
        raise ValueError(
            f"Parameters 'actuator_length' and 'actuator_width' must have the same amount elements"
        )

    if len(w) == 1:
        w.append(w[0])
        l.append(l[0])
    if len(w) != len(h) + 1:
        raise ValueError(
            f"When 'actuator_width' is more than one element, then it must be exactly one element more than 'actuator_height'"
        )

    bot = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if bot > shell_bottom_h:
        bot = shell_bottom_h
    h.insert(0, bot)

    chamfers = params.get("actuator_chamfer", [])
    if type(chamfers) is not list:
        chamfers = [chamfers]

    fillets = params.get("actuator_fillet", [])
    if type(fillets) is not list:
        fillets = [fillets]

    body = None

    if params.get("actuator_round_base_height") is not None:
        base_h = params["actuator_round_base_height"]
        base_r = params["actuator_round_base_diameter"] / 2

        base = cq.Workplane("XY", origin=(0, 0, h[0]))
        base = base.circle(base_r)
        base = base.extrude(base_h - h[0])

        if params.get("actuator_round_base_fillet"):
            base = base.edges(">Z").fillet(params["actuator_round_base_fillet"])
        if params.get("actuator_round_base_chamfer"):
            base = base.edges(">Z").chamfer(*params["actuator_round_base_chamfer"])

        body = base

    def _make_edges(func_name, part, edges_list, edges_index):
        jobs = {"b": 0, "m": 0, "t": 0}

        if i >= 1 and w[i - 1] < w[i] and l[i - 1] < l[i]:
            jobs["b"] = edges_list[edges_index] if edges_index < len(edges_list) else 0
            edges_index += 1

        if h[i] < h[i + 1]:
            jobs["m"] = edges_list[edges_index] if edges_index < len(edges_list) else 0
            edges_index += 1

        if (i + 2 == len(h)) or (
            i + 2 < len(h) and w[i + 1] > w[i + 2] and l[i + 1] > l[i + 2]
        ):
            jobs["t"] = edges_list[edges_index] if edges_index < len(edges_list) else 0
            edges_index += 1

        if jobs["m"] and jobs["m"] == jobs["b"] and jobs["m"] == jobs["t"]:
            part = getattr(part.edges(), func_name)(jobs["m"])
        elif jobs["m"] and jobs["m"] == jobs["b"]:
            part = getattr(part.edges("not >Z"), func_name)(jobs["m"])
        elif jobs["m"] and jobs["m"] == jobs["t"]:
            part = getattr(part.edges("not <Z"), func_name)(jobs["m"])
        else:
            if jobs["m"]:
                part = getattr(part.edges("(not <Z) and (not >Z)"), func_name)(
                    jobs["m"]
                )
            if jobs["b"]:
                part = getattr(part.edges("<Z"), func_name)(jobs["b"])
            if jobs["t"]:
                part = getattr(part.edges(">Z"), func_name)(jobs["t"])

        return part, edges_index

    edges_index = 0

    for i in range(0, len(h) - 1):
        if h[i] == h[i + 1]:
            continue

        part = cq.Workplane(origin=(0, 0, h[i]))
        part = part.rect(w[i], l[i])
        part = part.workplane(offset=h[i + 1] - h[i])
        part = part.rect(w[i + 1], l[i + 1])
        part = part.loft()
        part, _ = _make_edges("chamfer", part, chamfers, edges_index)
        part, edges_index = _make_edges("fillet", part, fillets, edges_index)

        body = body.union(part) if body else part

    if params.get("actuator_top_hole_diameter"):
        hole = cq.Workplane("XY", origin=(0, 0, h[-1]))
        hole = hole.circle(params["actuator_top_hole_diameter"] / 2)
        hole = hole.extrude(-params["actuator_top_hole_depth"])

        body = body.cut(hole)
        if params.get("actuator_top_hole_chamfer"):
            body = body.edges("%CIRCLE and >Z").chamfer(
                *params["actuator_top_hole_chamfer"]
            )
        if params.get("actuator_top_hole_fillet"):
            body = body.edges("%CIRCLE and >Z").fillet(
                params["actuator_top_hole_fillet"]
            )

    return body


def _make_shell_top_rectangle_round_actuator_hole(shell_body, params):
    params = params.copy()
    params["actuator_width"] += params["actuator_shell_gap"] * 2
    params["actuator_length"] += params["actuator_shell_gap"] * 2
    params["actuator_diameter"] += params["actuator_shell_gap"] * 2
    params["actuator_top_chamfer"] = None
    params["actuator_top_fillet"] = None

    actuator_body = _make_top_rectangle_round_actuator(params)
    shell_body = shell_body.cut(actuator_body)
    return shell_body


def _make_top_rectangle_round_actuator(params):
    body_h = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if shell_bottom_h < body_h:
        body_h = shell_bottom_h

    w = params["actuator_width"]
    l = params["actuator_length"]
    r = params["actuator_diameter"] / 2

    rect = cq.Workplane("XY", origin=(0, 0, body_h))
    rect = rect.rect(w, l)
    rect = rect.extrude(params["actuator_height"] - body_h)

    if params.get("actuator_corner_fillet"):
        rect = rect.edges("|Z").fillet(params["actuator_corner_fillet"])
    if params.get("actuator_corner_chamfer"):
        rect = rect.edges("|Z").chamfer(*params["actuator_corner_chamfer"])

    circ = cq.Workplane("XY", origin=(0, 0, body_h))
    circ = circ.circle(r)
    circ = circ.extrude(params["actuator_height"] - body_h)

    body = rect.union(circ)

    if params.get("actuator_top_fillet"):
        body = body.edges(">Z").fillet(params["actuator_top_fillet"])
    if params.get("actuator_top_chamfer"):
        body = body.edges(">Z").chamfer(*params["actuator_top_chamfer"])

    return body


def _make_shell_top_hex_actuator_hole(shell_body, params):
    params = params.copy()
    params["actuator_width"] += params["actuator_shell_gap"] * 2
    params["actuator_mid_length"] += params["actuator_shell_gap"] * 2
    params["actuator_side_length"] += params["actuator_shell_gap"] * 2
    params["actuator_top_chamfer"] = None
    params["actuator_top_fillet"] = None

    actuator_body = _make_top_hex_actuator(params)
    shell_body = shell_body.cut(actuator_body)
    return shell_body


def _make_top_hex_actuator(params):
    body_h = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if shell_bottom_h < body_h:
        body_h = shell_bottom_h

    width = params["actuator_width"]
    mid_length = params["actuator_mid_length"]
    side_length = params["actuator_side_length"]

    body = cq.Workplane("XY", origin=(0, 0, body_h))
    body = body.move(0, mid_length / 2)
    body = body.lineTo(width / 2, side_length / 2)
    body = body.lineTo(width / 2, -side_length / 2)
    body = body.lineTo(0, -mid_length / 2)
    body = body.close()

    body = body.extrude(params["actuator_height"] - body_h)
    body = body.union(body.mirror("YZ"))

    corner_fillet = params.get("actuator_corner_fillet")
    if corner_fillet:
        body = body.edges("|Z").fillet(corner_fillet)

    if params.get("actuator_top_fillet"):
        body = body.edges(">Z").fillet(params["actuator_top_fillet"])
    if params.get("actuator_top_chamfer"):
        body = body.edges(">Z").chamfer(*params["actuator_top_chamfer"])

    return body


def _make_side_rectangle_actuator(params):
    btn_dir = params["actuator_direction"] % 360

    head_t = params["actuator_thickness"]
    head_w = params["actuator_width"]
    head_top_h = params["actuator_top_height"]
    head_bot_h = params["actuator_bottom_height"]
    head_h = head_top_h - head_bot_h
    head_dist = params["actuator_distance"]
    head_start_dist = head_dist - head_t
    head_corner_fillet = params.get("actuator_corner_fillet")
    head_corner_chamfer = params.get("actuator_corner_chamfer")
    head_bottom_fillet = params.get("actuator_bottom_fillet")
    head_bottom_chamfer = params.get("actuator_bottom_chamfer")

    neck_w = params["actuator_neck_width"]
    neck_top_h = params["actuator_neck_top_height"]
    neck_bot_h = params["actuator_neck_bottom_height"]
    neck_h = neck_top_h - neck_bot_h
    neck_gaps = params.get("actuator_neck_gaps", [])

    if btn_dir in [0, 180]:
        neck_start_dist = params["body_width"] / 2
    elif btn_dir in [90, 270]:
        neck_start_dist = params["body_length"] / 2
    else:
        raise ValueError(f"Side actuator direction can only in steps of 90 degrees")
    neck_l = head_start_dist - neck_start_dist

    head = cq.Workplane("YZ", origin=(head_start_dist, 0, head_bot_h + head_h / 2))
    head = head.rect(head_w, head_h)
    head = head.extrude(head_t)

    if head_corner_chamfer:
        head = head.edges(">X and |Z").chamfer(
            head_corner_chamfer[1], head_corner_chamfer[0]
        )
    if head_corner_fillet:
        head = head.edges(">X and |Z").fillet(head_corner_fillet)

    if head_bottom_chamfer:
        head = head.edges(">X and |Z").chamfer(*head_bottom_chamfer)
    if head_bottom_fillet:
        head = head.edges("<Z and >X").fillet(head_bottom_fillet)

    neck = cq.Workplane("YZ", origin=(neck_start_dist, 0, neck_bot_h + neck_h / 2))
    neck = neck.rect(neck_w, neck_h)
    neck = neck.extrude(neck_l)

    for [neck_gap_x, neck_gap_w] in neck_gaps:
        neck_gap = cq.Workplane(
            "YZ", origin=(neck_start_dist, neck_gap_x, neck_bot_h + neck_h / 2)
        )
        neck_gap = neck_gap.rect(neck_gap_w, neck_h)
        neck_gap = neck_gap.extrude(neck_l)
        neck = neck.cut(neck_gap)

    body = head.union(neck)
    body = body.rotate((0, 0, 0), (0, 0, 1), btn_dir)

    return body


def make_actuator(params):
    actuator_type = params["actuator_type"]
    if actuator_type == "top-round":
        body = _make_top_round_actuator(params)
    elif actuator_type == "top-obround":
        body = _make_top_obround_actuator(params)
    elif actuator_type == "top-rectangle":
        body = _make_top_rectangle_actuator(params)
    elif actuator_type == "top-rectangle-round":
        body = _make_top_rectangle_round_actuator(params)
    elif actuator_type == "top-hex":
        body = _make_top_hex_actuator(params)
    elif actuator_type == "side-rectangle":
        body = _make_side_rectangle_actuator(params)
    else:
        raise ValueError(f"Unknown actuator type: {actuator_type}")

    return body


def make_pins(params):
    body = pingen.make_pins(params)
    return body
