#!/usr/bin/env python3

# CadQuery helper functions for generating pins
#
# Copyright (c) 2017 Terje Io https://github.com/terjeio
# Copyright (c) 2017 Maurice https://launchpad.net/~easyw
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

import math

import cadquery as cq

from _tools.utils import V2, get_back_side, get_side_to_tip_corner, make_rounded_corner


def make_gullwing_pin(params, namespace="pin"):
    pw = params["pin_width"]
    pt = params["pin_thickness"]

    pl = params["pin_length"]
    top_h = params["pin_top_height"]
    top_l = params.get("pin_top_length")
    bot_h = params.get("pin_bottom_height", 0)
    bot_l = params.get("pin_bottom_length")
    corner_r = params.get("pin_corner_radius", 0)

    if top_l is None and bot_l is None:
        top_l = pl / 2 + pt / 2
        bot_l = pl / 2 + pt / 2
    elif top_l is None:
        top_l = pl - bot_l + pt
    elif bot_l is None:
        bot_l = pl - top_l + pt

    tip_b = V2(0, bot_h)
    ankle_b = V2(-bot_l, bot_h)
    start_b = V2(-pl, top_h - pt)

    start_f = V2(-pl, top_h)
    knee_f = V2(-pl + top_l, top_h)
    tip_f = V2(0, bot_h + pt)

    # Quadratic equation parameters:
    sw = knee_f.x - ankle_b.x
    sh = knee_f.y - ankle_b.y

    # Quadratic equation coefficients:
    a = sw**2 + sh**2
    b = -2 * sh * pt
    c = pt**2 - sw**2

    # Quadratic formula
    if sw < 0:
        slope_cos_a = (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)
    else:
        slope_cos_a = (-b - math.sqrt(b**2 - 4 * a * c)) / (2 * a)

    slope_a = math.acos(slope_cos_a)
    slope = math.tan(slope_a)

    knee_b = V2(ankle_b.x - (top_h - pt - bot_h) / slope, top_h - pt)
    ankle_f = V2(knee_f.x + (top_h - pt - bot_h) / slope, bot_h + pt)

    body = cq.Workplane("XZ", origin=(0, 0, 0))

    body = body.moveTo(*tip_b)
    body = make_rounded_corner(body, tip_b, ankle_b, knee_b, corner_r, pt)
    body = make_rounded_corner(body, ankle_b, knee_b, start_b, corner_r, pt)
    body = body.lineTo(*start_b)

    body = body.lineTo(*start_f)
    body = make_rounded_corner(body, start_f, knee_f, ankle_f, corner_r, pt)
    body = make_rounded_corner(body, knee_f, ankle_f, tip_f, corner_r, pt)
    body = body.lineTo(*tip_f)

    body = body.close()
    body = body.extrude(pw / 2, both=True)

    return body


def make_top_jbend_pin(params):
    pt = params["pin_thickness"]
    tr = params.get("pin_top_radius", 0)
    cr = params.get("pin_corner_radius", 0)

    start_f = V2(-params["pin_top_length"], params["pin_top_height"])
    top_f = V2(0, params["pin_top_height"])
    mid_f = V2(0, 0)
    tip_f = V2(-params["pin_bottom_length"], 0)

    tip_b = V2(tip_f.x, pt)
    mid_b = V2(mid_f.x - pt, pt)
    top_b = V2(top_f.x - pt, top_f.y - pt)
    start_b = V2(start_f.x, start_f.y - pt)

    body = cq.Workplane("XZ")

    body = body.moveTo(start_f.x, start_f.y)
    body = make_rounded_corner(body, start_f, top_f, mid_f, tr, pt)
    body = make_rounded_corner(body, top_f, mid_f, tip_f, cr, pt)
    body = body.lineTo(tip_f.x, tip_f.y)

    body = body.lineTo(tip_b.x, tip_b.y)
    body = make_rounded_corner(body, tip_b, mid_b, top_b, cr, pt)
    body = make_rounded_corner(body, mid_b, top_b, start_b, tr, pt)
    body = body.lineTo(start_b.x, start_b.y)

    body = body.close()
    body = body.extrude(params["pin_width"] / 2, both=True)

    return body


def make_bottom_jbend_pin(params):
    pt = params["pin_thickness"]
    sr = params.get("pin_start_radius", 0)
    cr = params.get("pin_corner_radius", 0)

    start_f = V2(-params["pin_bottom_length"], 0)
    mid_f = V2(-params["pin_top_length"], 0)
    tip_f = V2(0, params["pin_top_height"])
    tip_b = tip_f + V2(mid_f.y - tip_f.y, tip_f.x - mid_f.x).normalized() * pt
    mid_b = get_back_side(tip_f, mid_f, start_f, pt)
    start_b = V2(start_f.x, pt)

    body = cq.Workplane("XZ")

    body = body.moveTo(tip_f.x, tip_f.y)
    body = make_rounded_corner(body, tip_f, mid_f, start_f, cr, pt)
    body = make_rounded_corner(body, mid_f, start_f, start_b, sr, pt)

    if sr < pt:
        body = body.lineTo(start_b.x, start_b.y)
    body = make_rounded_corner(body, start_b, mid_b, tip_b, cr, pt)
    body = body.lineTo(tip_b.x, tip_b.y)

    body = body.close()
    body = body.extrude(params["pin_width"] / 2, both=True)

    return body


def make_flat_pin(params):
    pt = params["pin_thickness"]
    px = params["pin_length"] / -2

    body = cq.Workplane("XY", origin=(px, 0))
    body = body.rect(params["pin_length"], params["pin_width"])
    body = body.extrude(params["pin_thickness"])

    return body


def make_through_hole_pin(params, pin_index=0):
    pt = params["pin_thickness"]

    base_h = params["pin_base_height"]
    if type(base_h) is list:
        base_h = params["pin_base_height"][pin_index]
    base = V2(params["pin_base_offset"], base_h)

    bot = V2(0, params["pin_bottom_height"])

    corners = params["pin_corners"]
    if corners and type(corners[0][0]) is list:
        corners = corners[pin_index]

    cr = params.get("pin_corner_radius", 0)

    f = map(lambda c: V2(*c), corners)
    f = list(f)
    f.insert(0, base)
    f.append(get_side_to_tip_corner(f[-1], bot, pt, False))

    b = []
    b.append(f[-1] + (bot - f[-1]).normalized() * pt)
    b.append(V2(base.x, base.y - pt))

    body = cq.Workplane("XZ")

    body = body.moveTo(*f[0])
    for i in range(1, len(f) - 1):
        b.insert(1, get_back_side(f[i - 1], f[i], f[i + 1], pt))
        body = make_rounded_corner(body, f[i - 1], f[i], f[i + 1], cr, pt)
    body = body.lineTo(*f[-1])

    body = body.lineTo(*b[0])
    for i in range(1, len(b) - 1):
        body = make_rounded_corner(body, b[i - 1], b[i], b[i + 1], cr, pt)
    body = body.lineTo(*b[-1])

    body = body.close()
    body = body.extrude(params["pin_width"] / 2, both=True)

    tip_chamfer = params.get("pin_tip_chamfer", 0)
    tip_fillet = params.get("pin_tip_fillet", 0)
    if tip_chamfer:
        body = body.faces("<Z").edges("not |Y").chamfer(tip_chamfer[1], tip_chamfer[0])
    if tip_fillet:
        body = body.faces("<Z").edges("not |Y").fillet(tip_fillet)

    return body


def make_pins(params):
    body = None
    for pin_index, pin_pos in enumerate(params["pins"]):
        pin_x, pin_y, pin_ori = pin_pos

        if params["pin_type"] == "gullwing":
            pin_body = make_gullwing_pin(params)
        elif params["pin_type"] == "top-jbend":
            pin_body = make_top_jbend_pin(params)
        elif params["pin_type"] == "bottom-jbend":
            pin_body = make_bottom_jbend_pin(params)
        elif params["pin_type"] == "through-hole":
            pin_body = make_through_hole_pin(params, pin_index)
        elif params["pin_type"] == "flat":
            pin_body = make_flat_pin(params)
        else:
            raise ValueError(f"Unknown pin_type: {params['pin_type']}")

        pin_body = pin_body.rotate((0, 0, 0), (0, 0, 1), pin_ori)
        pin_body = pin_body.translate((pin_x, pin_y, 0))
        body = body.union(pin_body) if body else pin_body

    pin_board_distance = params.get("pin_board_distance")
    if pin_board_distance:
        body = body.translate((0, 0, pin_board_distance))

    return body
