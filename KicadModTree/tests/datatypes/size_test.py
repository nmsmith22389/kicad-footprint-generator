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

from KicadModTree.Size import Size, Unit  # NOQA

# %%


class SizeInit(unittest.TestCase):
    r""" Test initialization of Size object.

    """
    ValueSpec = namedtuple('ValueSpec', ['string', 'expected'])
    UnitSpec = namedtuple('UnitSpec', ['value', 'factor'])

    @parameterized.expand([[1], [3.14], [-42], ["1.0"], [".1"], ["1."], [" 25.4 "], ["+2.5"], ["-1.25"]])
    def test_init_only_value(self, value):
        r""" Test that the initializer behaves the same as float(value)

        """
        self.assertEqual(Size(value), float(value), "Given value was: {}".format(value))

    @parameterized.expand(itertools.product([
        ValueSpec("1", 1.0),
        ValueSpec("1.0", 1.0),
        ValueSpec(".0", 0.0),
        ValueSpec("367.125", 367.125),
    ], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ], [-1, 1]))
    def test_default_unit_value_string(self, value_def, unit_def, sign):
        r""" Test that the correct unit conversion is done on a string value

        """
        expected_value = sign * value_def.expected * unit_def.factor
        str_sign = '-' if sign == -1 else ''
        default_unit = unit_def.value

        test_string = str_sign + value_def.string
        self.assertEqual(Size(test_string, default_unit), expected_value,
                         "Given String was: {} with defaultUnit {}".format(test_string, default_unit))

    @parameterized.expand(itertools.product([
        1, 3.14
    ], [
        UnitSpec(Unit.MM, 1),
        UnitSpec(Unit.INCH, 25.4),
        UnitSpec(Unit.MIL, 25.4 / 1000),
        UnitSpec(Unit.NONE, 1)
    ], [-1, 1]))
    def test_default_unit_value(self, value_def, unit_def, sign):
        r""" Test that the correct unit conversion is done on the input value

        """
        expected_value = sign * value_def * unit_def.factor
        default_unit = unit_def.value

        test_value = sign * value_def
        self.assertEqual(Size(test_value, default_unit), expected_value,
                         "Given String was: {} with defaultUnit {}".format(test_value, default_unit))


# %%


class SizeOperatorTests(unittest.TestCase):
    TESTVECTOR_OPERATORS_DIV = [
        [Size(5, Unit.MM), Size(100, Unit.MIL)],
        [Size(0.1, Unit.MM), Size(1e-6)],
        [Size(250, Unit.MM), 5],
        [Size(2.25, Unit.MIL), -1],
        [Size(2.25, Unit.MM), 1]
    ]

    TESTVECTOR_OPERATORS = TESTVECTOR_OPERATORS_DIV + \
        [[Size(0, Unit.MM), 2.6], [Size(2.6, Unit.MM), 0], [Size(2.6, Unit.MM), Size(0, Unit.MIL)]]

    @parameterized.expand([[Size(1, Unit.MM)], [Size(-1)], [Size(0)]])
    def test_negate(self, value):
        r""" Test negation results in correctly negated value.

        :Additional requirements:
            * The value of the result is Size
            * The original unit indicator is preserved
        """
        r = -value
        self.assertIsInstance(r, Size)
        self.assertEqual(-float(value), float(r))
        self.assertEqual(r.original_unit, value.original_unit, "Unit does not match input parameter")

    @parameterized.expand(TESTVECTOR_OPERATORS)
    def test_aditive_operators(self, op1, op2):
        r""" Test addition results in correctly added values.

        :Additional requirements:
            * The value of the result is Size
            * The original unit indicator is preserved
        """
        expected_unit_2 = op2.original_unit if isinstance(op2, Size) else op1.original_unit

        descr = "Test: op1 + op2"
        r = op1 + op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) + float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: op2 + op1"
        r = op2 + op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) + float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

        descr = "Test: r += op1"
        r = op1
        r += op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) + float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: r += op2"
        r = op2
        r += op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) + float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

    @parameterized.expand(TESTVECTOR_OPERATORS)
    def test_subtractive_operators(self, op1, op2):
        r""" Test subtraction results in correctly subtracted values.

        :Additional requirements:
            * The value of the result is Size
            * The original unit indicator is preserved
        """
        expected_unit_2 = op2.original_unit if isinstance(op2, Size) else op1.original_unit

        descr = "Test: op1 - op2"
        r = op1 - op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) - float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: op2 - op1"
        r = op2 - op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) - float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

        descr = "Test: r -= op1"
        r = op1
        r -= op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) - float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: r -= op2"
        r = op2
        r -= op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) - float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

    @parameterized.expand(TESTVECTOR_OPERATORS)
    def test_mul_operators(self, op1, op2):
        r""" Test multiplication results in correctly multiplicated values.

        :Additional requirements:
            * The value of the result is Size
            * The original unit indicator is preserved
        """
        expected_unit_2 = op2.original_unit if isinstance(op2, Size) else op1.original_unit

        descr = "Test: op1 * op2"
        r = op1 * op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) * float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: op2 * op1"
        r = op2 * op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) * float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

        descr = "Test: r *= op1"
        r = op1
        r *= op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) * float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: r *= op2"
        r = op2
        r *= op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) * float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

    @parameterized.expand(TESTVECTOR_OPERATORS_DIV)
    def test_truediv_operators(self, op1, op2):
        r""" Test true-division results in correctly devided values.

        :Additional requirements:
            * The value of the result is Size
            * The original unit indicator is preserved
        """
        expected_unit_2 = op2.original_unit if isinstance(op2, Size) else op1.original_unit

        descr = "Test: op1 / op2"
        r = op1 / op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) / float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: op2 / op1"
        r = op2 / op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) / float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

        descr = "Test: r /= op1"
        r = op1
        r /= op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) / float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: r /= op2"
        r = op2
        r /= op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) / float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

    @parameterized.expand(TESTVECTOR_OPERATORS_DIV)
    def test_floordiv_operators(self, op1, op2):
        r""" Test floor-division results in correctly devided values.

        :Additional requirements:
            * The value of the result is Size
            * The original unit indicator is preserved
        """
        expected_unit_2 = op2.original_unit if isinstance(op2, Size) else op1.original_unit

        descr = "Test: op1 // op2"
        r = op1 // op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) // float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: op2 // op1"
        r = op2 // op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) // float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")

        descr = "Test: r //= op1"
        r = op1
        r //= op2
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op1) // float(op2), float(r), descr)
        self.assertEqual(r.original_unit, op1.original_unit, "Unit does not match input parameter")

        descr = "Test: r //= op2"
        r = op2
        r //= op1
        self.assertIsInstance(r, Size, descr)
        self.assertEqual(float(op2) // float(op1), float(r), descr)
        self.assertEqual(r.original_unit, expected_unit_2, "Unit does not match input parameter")


# %%
if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=2, exit=False)

# %%
