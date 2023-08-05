from scripts.tools.declarative_def_tools import shape_properties as SP

import yaml
import pytest

def test_rect():

    spec = """
rect: [[a,b], [c,d]]
"""
    rect_yaml = yaml.safe_load(spec)

    rp = SP.RectProperties(rect_yaml)

    assert(rp.x1_expr == 'a')
    assert(rp.y1_expr == 'b')
    assert(rp.x2_expr == 'c')
    assert(rp.y2_expr == 'd')

def test_rect_badkey():

    # This should fail because the key is not 'rect'
    spec = """
rect_bad: [[a,b], [c,d]]
"""
    rect_yaml = yaml.safe_load(spec)

    with pytest.raises(ValueError):
        SP.RectProperties(rect_yaml)