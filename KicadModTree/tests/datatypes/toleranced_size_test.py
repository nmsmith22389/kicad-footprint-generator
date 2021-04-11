# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

# %%
import itertools
import unittest
from collections import namedtuple
from parameterized import parameterized


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../"))

from KicadModTree.Size import Size, Unit, TolerancedSize  # NOQA

# %%


# %%


class SimpleTolerancedSizeTests(unittest.TestCase):
    TestVector = namedtuple('TestVectorStr', ['test_value', 'min', 'nom', 'max'])
    UnitSpec = namedtuple('UnitSpec', ['value', 'factor'])

    TEST_VECTOR_STR = ([
        TestVector('1.0', 1.0, 1.0, 1.0),
        TestVector('1.0 .. 1.2', 1.0, 1.1, 1.2),
        TestVector('1.0 .. 1.2 .. 2.5', 1.0, 1.2, 2.5),
        TestVector('1.1 +/- 0.1', 1.0, 1.1, 1.2),
        TestVector('1.0 +0.1 -0.2', 0.8, 1.0, 1.1),
        TestVector('1.0 -0.2 +0.1', 0.8, 1.0, 1.1)
    ], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ])

    @parameterized.expand(itertools.product(*TEST_VECTOR_STR))
    def test_from_string(self, test_vector, def_unit):
        r = TolerancedSize.from_string(test_vector.test_value, default_unit=def_unit.value)

        self.assertAlmostEqual(
            r.minimum, test_vector.min * def_unit.factor,
            msg="minimum differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )
        self.assertAlmostEqual(
            r.nominal, test_vector.nom * def_unit.factor,
            msg="nominal differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )
        self.assertAlmostEqual(
            r.maximum, test_vector.max * def_unit.factor,
            msg="maximum differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )

    @parameterized.expand(itertools.product([
        TestVector({'test': 1.0}, 1.0, 1.0, 1.0),
        TestVector({'test_min': 1.0, 'test_max': 1.2}, 1.0, 1.1, 1.2),
        TestVector({'test_min': 1.0, 'test': 1.1, 'test_max': 1.5}, 1.0, 1.1, 1.5),
        TestVector({'test': 1.0, 'test_tol': 0.1}, 0.9, 1.0, 1.1),
        TestVector({'test': 1.0, 'test_tol': [0.1, -0.2]}, 0.8, 1.0, 1.1),
        TestVector({'test': 1.0, 'test_tol': [-0.2, 0.1]}, 0.8, 1.0, 1.1),
        TestVector({'test': 1.0, 'test_tol': [0.2, 0.1]}, 0.8, 1.0, 1.1)
    ], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ]))
    def test_from_yaml_legacy_format(self, test_vector, def_unit):
        r = TolerancedSize.from_yaml(test_vector.test_value, base_name='test', default_unit=def_unit.value)
        self.assertAlmostEqual(
            r.minimum, test_vector.min * def_unit.factor,
            msg="minimum differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )
        self.assertAlmostEqual(
            r.nominal, test_vector.nom * def_unit.factor,
            msg="nominal differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )
        self.assertAlmostEqual(
            r.maximum, test_vector.max * def_unit.factor,
            msg="maximum differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )

    @parameterized.expand(itertools.product([
        TestVector({'test': {'nominal': 1.0}}, 1.0, 1.0, 1.0),
        TestVector({'test': {'minimum': 1.0, 'maximum': 1.2}}, 1.0, 1.1, 1.2),
        TestVector({'test': {'minimum': 1.0, 'nominal': 1.1, 'maximum': 1.5}}, 1.0, 1.1, 1.5),
        TestVector({'test': {'nominal': 1.0, 'tolerance': 0.1}}, 0.9, 1.0, 1.1),
        TestVector({'test': {'nominal': 1.0, 'tolerance': [0.1, -0.2]}}, 0.8, 1.0, 1.1),
        TestVector({'test': {'nominal': 1.0, 'tolerance': [-0.2, 0.1]}}, 0.8, 1.0, 1.1),
        TestVector({'test': {'nominal': 1.0, 'tolerance': [0.2, 0.1]}}, 0.8, 1.0, 1.1)
    ], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ]))
    def test_from_yaml_nested_dict_format(self, test_vector, def_unit):
        r = TolerancedSize.from_yaml(test_vector.test_value, base_name='test', default_unit=def_unit.value)
        self.assertAlmostEqual(
            r.minimum, test_vector.min * def_unit.factor,
            msg="minimum differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )
        self.assertAlmostEqual(
            r.nominal, test_vector.nom * def_unit.factor,
            msg="nominal differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )
        self.assertAlmostEqual(
            r.maximum, test_vector.max * def_unit.factor,
            msg="maximum differs for input {} with defaultUnit {}".format(test_vector.test_value, def_unit.value)
        )

    @parameterized.expand(itertools.product(*TEST_VECTOR_STR))
    def test_from_yaml_string_format(self, test_vector, def_unit):
        yml = {'test': test_vector.test_value}
        r = TolerancedSize.from_yaml(yml, base_name='test', default_unit=def_unit.value)

        self.assertAlmostEqual(
            r.minimum, test_vector.min * def_unit.factor,
            msg="minimum differs for input {} with defaultUnit {}".format(yml, def_unit.value)
        )
        self.assertAlmostEqual(
            r.nominal, test_vector.nom * def_unit.factor,
            msg="nominal differs for input {} with defaultUnit {}".format(yml, def_unit.value)
        )
        self.assertAlmostEqual(
            r.maximum, test_vector.max * def_unit.factor,
            msg="maximum differs for input {} with defaultUnit {}".format(yml, def_unit.value)
        )


# %%
if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=2, exit=False)

# %%
