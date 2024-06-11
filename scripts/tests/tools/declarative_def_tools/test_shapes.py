from scripts.tools.declarative_def_tools import shape_properties as SP

import yaml
import pytest


def test_no_shape_type_key():

    # This should fail because there's no type
    spec = """
corners: [[a,b], [c,d]]
"""
    shape_yaml = yaml.safe_load(spec)

    with pytest.raises(ValueError):
        SP.construct_shape(shape_yaml)


def test_rect():

    spec = """
type: rect
corners: [[a,b], [c,d]]
"""
    rect_yaml = yaml.safe_load(spec)

    rp = SP.RectProperties(rect_yaml)

    assert(rp.exprs.x1_expr == 'a')
    assert(rp.exprs.y1_expr == 'b')
    assert(rp.exprs.x2_expr == 'c')
    assert(rp.exprs.y2_expr == 'd')


def test_rect_center_size():

    spec = """
type: rect
center: [a,b]
size: [c,d]
"""
    rect_yaml = yaml.safe_load(spec)

    rp = SP.RectProperties(rect_yaml)

    assert(rp.exprs.cx_expr == 'a')
    assert(rp.exprs.cy_expr == 'b')
    assert(rp.exprs.width_expr == 'c')
    assert(rp.exprs.height_expr == 'd')
