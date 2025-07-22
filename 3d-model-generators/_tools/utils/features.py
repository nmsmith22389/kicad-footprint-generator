#!/usr/bin/env python3

# CadQuery helper functions for adding general details to a shape
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

import cadquery as cq


def _make_shape_feature(feature):
    shape_type = feature[1]
    pos = feature[2]
    dim = feature[3]
    extra = feature[4:]

    shape = cq.Workplane("XY", origin=pos)

    if shape_type == "box":
        shape = shape.box(*dim)
    elif shape_type == "cylinder":
        r = dim[0] / 2
        h = dim[1]
        shape = shape.cylinder(h, r)
    elif shape_type == "poly":
        dim = dim.copy()
        h = dim.pop(0)
        x = dim.pop(0)
        y = dim.pop(0)
        shape = shape.moveTo(x, y)
        while dim:
            x = dim.pop(0)
            y = dim.pop(0)
            shape = shape.lineTo(x, y)
        shape = shape.close()
        shape = shape.extrude(h / 2, both=True)
    else:
        raise ValueError(
            f"{namespace}[{feature_index}]: Unrecognized feature shape type: {shape_type}"
        )

    while extra:
        extra_name = extra.pop(0)
        if extra_name == "chamfer":
            edges, chamfer = extra.pop(0)
            shape = shape.edges(edges).chamfer(chamfer)
        elif extra_name == "fillet":
            edges, fillet = extra.pop(0)
            shape = shape.edges(edges).fillet(fillet)
        else:
            raise ValueError(
                f"{namespace}[{feature_index}]: Unrecognized extra parameter: {extra_name}"
            )

    return shape


def make_features(body, features, namespace):
    for feature_index, feature in enumerate(features):
        feature_type = feature[0]

        if feature_type == "add":
            shape = _make_shape_feature(feature)
            body = body.union(shape)
        elif feature_type == "cut":
            shape = _make_shape_feature(feature)
            body = body.cut(shape)
        elif feature_type == "chamfer":
            chamfer_edges = feature[1]
            chamfer_size = feature[2]
            body = body.edges(chamfer_edges).chamfer(chamfer_size)
        elif feature_type == "fillet":
            fillet_edges = feature[1]
            fillet_size = feature[2]
            body = body.edges(fillet_edges).fillet(fillet_size)
        else:
            raise ValueError(
                f"{namespace}[{feature_index}]: Unrecognized feature: {feature_type}"
            )

    return body
