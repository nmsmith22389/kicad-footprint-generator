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
from cadquery import Vector


class _Line:
    def __init__(self, m, b):
        self.m = m  # slope
        self.b = b  # intercept

    def get_line_intersection(self, l):
        x = (l.b - self.b) / (self.m - l.m)

        if abs(self.m) < 10000:
            y = self.m * x + self.b
        else:
            y = l.m * x + l.b

        return Vector(x, y)


def _get_side_to_tip_corner(side, tip, thickness, ccw):
    w = side.x - tip.x
    h = side.y - tip.y
    angle = math.atan2(h, w)

    tri_c = math.sqrt(w * w + h * h)
    tri_a = thickness / 2
    tri_b = math.sqrt(tri_c**2 - tri_a**2)

    tri_B = math.asin(tri_b / tri_c)

    if ccw:
        tip_angle = angle + tri_B
    else:
        tip_angle = angle - tri_B

    corner = tip + Vector(math.cos(tip_angle), math.sin(tip_angle)).multiply(
        thickness / 2
    )

    return corner


def _get_back_side(p0, p1, p2, r):
    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)
    if a0 < 0:
        a0 += math.pi * 2
    if a1 < 0:
        a1 += math.pi * 2

    m0 = math.tan(a0)
    m1 = math.tan(a1)

    ap0 = a0 + math.pi / 2
    ap1 = a1 - math.pi / 2

    p0_b = p1.add(Vector(math.cos(ap0), math.sin(ap0)).multiply(r))
    p1_b = p1.add(Vector(math.cos(ap1), math.sin(ap1)).multiply(r))

    l0 = _Line(m0, p0_b.y - p0_b.x * m0)
    l1 = _Line(m1, p1_b.y - p1_b.x * m1)
    c = l0.get_line_intersection(l1)

    return c


def _make_rounded_corner(body, p0, p1, p2, r):
    if r <= 0:
        body = body.lineTo(p1.x, p1.y)
        return body

    a0 = math.atan2(p0.y - p1.y, p0.x - p1.x)
    a1 = math.atan2(p2.y - p1.y, p2.x - p1.x)
    if a0 < 0:
        a0 += math.pi * 2
    if a1 < 0:
        a1 += math.pi * 2

    m0 = math.tan(a0)
    m1 = math.tan(a1)

    d = a1 - a0
    if d < 0:
        d += math.pi * 2

    if d < math.pi:
        ap0 = a0 + math.pi / 2
        ap1 = a1 - math.pi / 2
        rev = False
    else:
        ap0 = a0 - math.pi / 2
        ap1 = a1 + math.pi / 2
        rev = True

    p0_b = p1.add(Vector(math.cos(ap0), math.sin(ap0)).multiply(r))
    p1_b = p1.add(Vector(math.cos(ap1), math.sin(ap1)).multiply(r))
    l0 = _Line(m0, p0_b.y - p0_b.x * m0)
    l1 = _Line(m1, p1_b.y - p1_b.x * m1)

    c = l0.get_line_intersection(l1)
    s = c.add(Vector(-math.cos(ap0), -math.sin(ap0)).multiply(r))
    e = c.add(Vector(-math.cos(ap1), -math.sin(ap1)).multiply(r))

    if rev:
        r = -r
    if p0.toPnt().Distance(s.toPnt()) > 0.00001:
        body = body.lineTo(s.x, s.y)
    body = body.radiusArc((e.x, e.y), r)

    return body


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

    tip_b = Vector(0, bot_h)
    ankle_b = Vector(-bot_l, bot_h)
    # knee_b
    start_b = Vector(-pl, top_h - pt)

    start_f = Vector(-pl, top_h)
    knee_f = Vector(-pl + top_l, top_h)
    # ankle_f
    tip_f = Vector(0, bot_h + pt)

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

    knee_b = Vector(ankle_b.x - (top_h - pt - bot_h) / slope, top_h - pt)
    ankle_f = Vector(knee_f.x + (top_h - pt - bot_h) / slope, bot_h + pt)

    body = cq.Workplane("XZ", origin=(0, 0, 0))

    body = body.moveTo(tip_b.x, tip_b.y)
    body = _make_rounded_corner(body, tip_b, ankle_b, knee_b, corner_r)
    body = _make_rounded_corner(body, ankle_b, knee_b, start_b, corner_r - pt)
    body = body.lineTo(start_b.x, start_b.y)

    body = body.lineTo(start_f.x, start_f.y)
    body = _make_rounded_corner(body, start_f, knee_f, ankle_f, corner_r)
    body = _make_rounded_corner(body, knee_f, ankle_f, tip_f, corner_r - pt)
    body = body.lineTo(tip_f.x, tip_f.y)

    body = body.close()
    body = body.extrude(pw / 2, both=True)

    return body


def make_top_jbend_pin(params):
    pt = params["pin_thickness"]
    tr = params.get("pin_top_radius", 0)
    cr = params.get("pin_corner_radius", 0)

    start_f = Vector(-params["pin_top_length"], params["pin_top_height"])
    top_f = Vector(0, params["pin_top_height"])
    mid_f = Vector(0, 0)
    tip_f = Vector(-params["pin_bottom_length"], 0)

    tip_b = Vector(tip_f.x, pt)
    mid_b = Vector(mid_f.x - pt, pt)
    top_b = Vector(top_f.x - pt, top_f.y - pt)
    start_b = Vector(start_f.x, start_f.y - pt)

    body = cq.Workplane("XZ")

    body = body.moveTo(start_f.x, start_f.y)
    body = _make_rounded_corner(body, start_f, top_f, mid_f, tr)
    body = _make_rounded_corner(body, top_f, mid_f, tip_f, cr)
    body = body.lineTo(tip_f.x, tip_f.y)

    body = body.lineTo(tip_b.x, tip_b.y)
    body = _make_rounded_corner(body, tip_b, mid_b, top_b, cr - pt)
    body = _make_rounded_corner(body, mid_b, top_b, start_b, tr - pt)
    body = body.lineTo(start_b.x, start_b.y)

    body = body.close()
    body = body.extrude(params["pin_width"] / 2, both=True)

    return body


def make_bottom_jbend_pin(params):
    pt = params["pin_thickness"]
    sr = params.get("pin_start_radius", 0)
    cr = params.get("pin_corner_radius", 0)

    start_f = Vector(-params["pin_bottom_length"], 0)
    mid_f = Vector(-params["pin_top_length"], 0)
    tip_f = Vector(0, params["pin_top_height"])
    tip_b = tip_f + Vector(mid_f.y - tip_f.y, tip_f.x - mid_f.x).normalized() * pt
    mid_b = _get_back_side(tip_f, mid_f, start_f, pt)
    start_b = Vector(start_f.x, pt)

    body = cq.Workplane("XZ")

    body = body.moveTo(tip_f.x, tip_f.y)
    body = _make_rounded_corner(body, tip_f, mid_f, start_f, cr)
    body = _make_rounded_corner(body, mid_f, start_f, start_b, sr)

    if sr < pt:
        body = body.lineTo(start_b.x, start_b.y)
    body = _make_rounded_corner(body, start_b, mid_b, tip_b, cr - pt)
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
    tip = Vector(0, params["pin_bottom_height"])

    pin_top_height = params["pin_top_height"]
    if type(pin_top_height) is list:
        pin_top_height = pin_top_height[pin_index]

    knee_h = params.get("pin_knee_height")
    ankle_h = params.get("pin_ankle_height")

    top_r = params.get("pin_top_radius", 0)
    knee_r = params.get("pin_knee_radius", 0)
    ankle_r = params.get("pin_ankle_radius", 0)
    top_offset = params.get("pin_top_offset", pt / 2)

    start_x = params["pin_base_offset"]
    start_f = Vector(start_x, pin_top_height)
    top_f = Vector(top_offset, pin_top_height)

    body = cq.Workplane("XZ")

    if knee_h is None:
        foot_f = _get_side_to_tip_corner(top_f, tip, pt, False)
        foot_b = foot_f + (tip - foot_f).normalized() * pt

        top_b = _get_back_side(start_f, top_f, foot_f, pt)
        start_b = Vector(start_f.x, start_f.y - pt)

        body = body.moveTo(start_f.x, start_f.y)
        body = _make_rounded_corner(body, start_f, top_f, foot_f, top_r)
        body = body.lineTo(foot_f.x, foot_f.y)

        body = body.lineTo(foot_b.x, foot_b.y)
        if start_b != top_b:
            body = _make_rounded_corner(body, foot_b, top_b, start_b, top_r - pt)
            body = body.lineTo(start_b.x, start_b.y)
    elif ankle_h is None:
        knee_offset = params.get("pin_knee_offset", pt / 2)

        knee_f = Vector(knee_offset, params["pin_knee_height"])
        foot_f = _get_side_to_tip_corner(knee_f, tip, pt, False)

        foot_b = foot_f + (tip - foot_f).normalized() * pt
        knee_b = _get_back_side(top_f, knee_f, foot_f, pt)
        top_b = _get_back_side(start_f, top_f, knee_f, pt)
        start_b = Vector(start_f.x, start_f.y - pt)

        knee_a = math.atan2(top_f.y - knee_f.y, top_f.x - knee_f.x)
        foot_a = math.atan2(knee_f.y - foot_f.y, knee_f.x - knee_f.x)

        if knee_a < foot_a:
            knee_f_r = knee_r - pt
            knee_b_r = knee_r
        else:
            knee_f_r = knee_r
            knee_b_r = knee_r - pt

        body = body.moveTo(start_f.x, start_f.y)
        body = _make_rounded_corner(body, start_f, top_f, knee_f, top_r)
        body = _make_rounded_corner(body, top_f, knee_f, foot_f, knee_f_r)
        body = body.lineTo(foot_f.x, foot_f.y)

        body = body.lineTo(foot_b.x, foot_b.y)
        body = _make_rounded_corner(body, foot_b, knee_b, top_b, knee_b_r)
        if start_b != top_b:
            body = _make_rounded_corner(body, knee_b, top_b, start_b, top_r - pt)
            body = body.lineTo(start_b.x, start_b.y)
    else:
        knee_offset = params.get("pin_knee_offset", pt / 2)
        ankle_offset = params.get("pin_ankle_offset", pt / 2)

        knee_f = Vector(knee_offset, params["pin_knee_height"])
        ankle_f = Vector(ankle_offset, params["pin_ankle_height"])
        foot_f = _get_side_to_tip_corner(ankle_f, tip, pt, False)

        foot_b = foot_f + (tip - foot_f).normalized() * pt
        ankle_b = _get_back_side(knee_f, ankle_f, foot_f, pt)
        knee_b = _get_back_side(top_f, knee_f, ankle_f, pt)
        top_b = _get_back_side(start_f, top_f, knee_f, pt)
        start_b = Vector(start_f.x, start_f.y - pt)

        knee_a = math.atan2(top_f.y - knee_f.y, top_f.x - knee_f.x)
        ankle_a = math.atan2(knee_f.y - ankle_f.y, knee_f.x - ankle_f.x)
        foot_a = math.atan2(ankle_f.y - foot_f.y, ankle_f.x - foot_f.x)

        if knee_a < ankle_a:
            knee_f_r = knee_r - pt
            knee_b_r = knee_r
        else:
            knee_f_r = knee_r
            knee_b_r = knee_r - pt

        if ankle_a < foot_a:
            ankle_f_r = ankle_r - pt
            ankle_b_r = ankle_r
        else:
            ankle_f_r = ankle_r
            ankle_b_r = ankle_r - pt

        body = body.moveTo(start_f.x, start_f.y)
        body = _make_rounded_corner(body, start_f, top_f, knee_f, top_r)
        body = _make_rounded_corner(body, top_f, knee_f, ankle_f, knee_f_r)
        body = _make_rounded_corner(body, knee_f, ankle_f, foot_f, ankle_f_r)
        body = body.lineTo(foot_f.x, foot_f.y)

        body = body.lineTo(foot_b.x, foot_b.y)
        body = _make_rounded_corner(body, foot_b, ankle_b, knee_b, ankle_b_r)
        body = _make_rounded_corner(body, ankle_b, knee_b, top_b, knee_b_r)
        if start_b != top_b:
            body = _make_rounded_corner(body, knee_b, top_b, start_b, top_r - pt)
            body = body.lineTo(start_b.x, start_b.y)

    body = body.close()
    body = body.extrude(params["pin_width"] / 2, both=True)

    if params.get("pin_tip_chamfer"):
        body = (
            body.faces("<Z")
            .edges("not |Y")
            .chamfer(params["pin_tip_chamfer"][1], params["pin_tip_chamfer"][0])
        )

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
