from scripts.tools.declarative_def_tools import additional_drawing as AD

import yaml
import pytest


def test_basic():

    spec = """
additional_drawings:
    port_inner:
        type: circle
        layer: mechanical
        center: [0, 0]
        diameter: 3.0
    port_outer:
        inherit: port_inner
        diameter: 1.0
"""

    ad_yaml = yaml.safe_load(spec)

    ads = AD.AdditionalDrawing.from_standard_yaml(ad_yaml)

    assert len(ads) == 2

    assert ads[0].type == 'circle'
    assert ads[0].layer == 'mechanical'
    assert ads[0].shape.exprs.cx_expr == 0
    assert ads[0].shape.exprs.cy_expr == 0

    assert ads[1].type == 'circle'
    assert ads[1].layer == 'mechanical'
    assert ads[1].shape.exprs.cx_expr == 0
    assert ads[1].shape.exprs.cy_expr == 0