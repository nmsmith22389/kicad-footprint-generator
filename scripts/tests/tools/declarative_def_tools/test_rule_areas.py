from scripts.tools.declarative_def_tools import rule_area_properties as RAP

import yaml


def test_basic():

    spec = """
name: test
layers: F.Cu
keepouts:
    vias: allow
    tracks: deny
shapes:
    - type: rect
      corners: [[a,b], [c,1]]
"""
    spec_yaml = yaml.safe_load(spec)

    kp = RAP.RuleAreaProperties(spec_yaml)

    assert kp.name == 'test'

    assert kp.layers == ['F.Cu']

    assert kp.keepouts.vias == RAP.KeepoutProperties.ALLOW
    assert kp.keepouts.tracks == RAP.KeepoutProperties.DENY

    assert len(kp.shapes) == 1

    rect = kp.shapes[0]

    assert rect.exprs.x1_expr == 'a'
    assert rect.exprs.y1_expr == 'b'
    assert rect.exprs.x2_expr == 'c'
    assert rect.exprs.y2_expr == 1


def test_multilayer():

    spec = """
name: test
layers: [F.Cu, B.Cu]
keepouts:
    tracks: deny
shapes:
    - type: rect
      corners: [[a,b], [c,1]]
"""
    spec_yaml = yaml.safe_load(spec)

    kp = RAP.RuleAreaProperties(spec_yaml)

    assert kp.name == 'test'

    assert kp.layers == ['F.Cu', 'B.Cu']