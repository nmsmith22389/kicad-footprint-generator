#!/usr/bin/env python3

# CadQuery Helper Functions
#
# Copyright (C) 2025 Martin Sotirov <martin@libtec.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


def _make_z_operation(body, vals, func_name):
    if not vals:
        return body

    if type(vals) is not list:
        vals = [vals] * 4

    if len(vals) != 4:
        raise ValueError(f"z {func_name} operation must have exactly 4 numbers")

    if vals[0]:
        body = getattr(body.edges("|Z and >X and >Y"), func_name)(vals[0])
    if vals[1]:
        body = getattr(body.edges("|Z and <X and >Y"), func_name)(vals[1])
    if vals[2]:
        body = getattr(body.edges("|Z and <X and <Y"), func_name)(vals[2])
    if vals[3]:
        body = getattr(body.edges("|Z and >X and <Y"), func_name)(vals[3])

    return body


def make_z_chamfer(body, vals):
    return _make_z_operation(body, vals, "chamfer")


def make_z_fillet(body, vals):
    return _make_z_operation(body, vals, "fillet")
