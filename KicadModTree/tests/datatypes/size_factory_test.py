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

from KicadModTree.Size import Size, Unit, SizeFactory  # NOQA


# %%

class SizeFactoryTests(unittest.TestCase):
    r"""Tests if SizeFactory correctly creates a Size object from its possible input options.

    """
    ValueSpec = namedtuple('ValueSpec', ['string', 'expected'])
    UnitSpec = namedtuple('UnitSpec', ['value', 'factor'])

    TEST_VECTOR = ([
        ValueSpec("1", 1.0),
        ValueSpec("1.0", 1.0),
        ValueSpec(".0", 0.0),
        ValueSpec("367.125", 367.125),
    ], [
        UnitSpec("mm", 1),
        UnitSpec("in", 25.4),
        UnitSpec("inch", 25.4),
        UnitSpec('"', 25.4),
        UnitSpec('mil', 25.4 / 1000),
        UnitSpec('thou', 25.4 / 1000)
    ], [-1, 1])

    @parameterized.expand(itertools.product(*TEST_VECTOR))
    def test_init_with_string(self, value_def, unit_def, sign):
        r""" Test that the Size is initialized correctly from a string

        """
        # ------------------------------------------------------------------------------------------
        expected_value = sign * value_def.expected * unit_def.factor
        expected_unit = Unit.from_string(unit_def.value)
        str_sign = '-' if sign == -1 else ''

        test_string = str_sign + value_def.string + unit_def.value
        r = SizeFactory(test_string)
        self.assertEqual(r, expected_value, "Given String was: {}".format(test_string))
        self.assertEqual(r.original_unit, expected_unit, "Unit is not correct for given string: {}".format(test_string))

        test_string = str_sign + value_def.string + " " + unit_def.value
        r = SizeFactory(test_string)
        self.assertEqual(r, expected_value, "Given String was: {}".format(test_string))
        self.assertEqual(r.original_unit, expected_unit, "Unit is not correct for given string: {}".format(test_string))

    @parameterized.expand(itertools.product(*TEST_VECTOR, [Unit.MM, Unit.INCH, Unit.MIL]))
    def test_init_with_string_and_ignored_default_unit(self, value_def, unit_def, sign, default_unit):
        r""" Test that the defaultUnit is ignored if the string specifies one

        """
        str_sign = '-' if sign == -1 else ''
        test_string = str_sign + value_def.string + unit_def.value
        expected_value = sign * value_def.expected * unit_def.factor
        expected_unit = Unit.from_string(unit_def.value)

        r = SizeFactory(test_string, default_unit)
        self.assertEqual(r, expected_value,
                         "Given String was: {} with defaultUnit {}".format(test_string, default_unit))
        self.assertEqual(r.original_unit, expected_unit, "Unit is not correct for given string: {}".format(test_string))

    @parameterized.expand(itertools.product(TEST_VECTOR[0], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ], [-1, 1]))
    def test_init_with_string_default_unit(self, value_def, unit_def, sign):
        r"""Test default unit is used if the value does not itself define it.

        """
        expected_value = sign * value_def.expected * unit_def.factor
        str_sign = '-' if sign == -1 else ''
        default_unit = unit_def.value

        test_string = str_sign + value_def.string
        r = SizeFactory(test_string, default_unit)
        self.assertEqual(r, expected_value,
                         "Given String was: {} with defaultUnit {}".format(test_string, default_unit))
        self.assertEqual(r.original_unit, unit_def.value,
                         "Unit is not correct for given string: {}".format(test_string))

    @parameterized.expand(itertools.product([
        25, 42.396
    ], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ], [-1, 1]))
    def test_init_with_float_default_unit(self, value_def, unit_def, sign):
        r"""Test default unit is used if the value is given as a float or int.

        """
        expected_value = sign * value_def * unit_def.factor
        default_unit = unit_def.value

        test_value = sign * value_def
        r = SizeFactory(test_value, default_unit)
        self.assertEqual(r, expected_value,
                         "Given String was: {} with defaultUnit {}".format(test_value, default_unit))
        self.assertEqual(r.original_unit, unit_def.value,
                         "Unit is not correct for given string: {}".format(test_value))


# %%
if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=2, exit=False)
# %%
