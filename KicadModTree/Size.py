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
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

from __future__ import division

import enum
import re
import math

from future.utils import raise_from


class Unit(enum.Enum):
    r"""Helper class to convert between units
    """
    MIL = 25.4 / 1000
    INCH = 25.4
    MM = 1
    NONE = None

    @staticmethod
    def from_string(string):
        r"""Get the unit from a string

        :param string: The string to convert.
        :type string: str
        :return: Unit object corresponding to the string
        :rtype: Unit
        """
        unit = string.lower()
        if unit in ['inch', 'in', '"']:
            return Unit.INCH
        elif unit in ['mil', 'thou']:
            return Unit.MIL
        elif unit in ['mm']:
            return Unit.MM
        elif unit is "":
            return Unit.NONE
        else:
            raise ValueError('Unknown unit string supplied "{}"'.format(string))

    @property
    def conversion_factor(self):
        r"""Get the conversion factor of this unit
        """
        if self is Unit.NONE:
            return 1
        return self.value


class Size(float):
    r"""Extension of float to support unit conversion

    :param value: The value of the size.
    :type value: float
    :param unit: Unit specifier of the given value. Default: Unit.NONE
    :type unit: Unit
    """
    def __new__(cls, value, unit=Unit.NONE):
        return super().__new__(cls, float(value) * unit.conversion_factor)

    def __init__(self, _, unit=Unit.NONE):
        super().__init__()
        self.original_unit = unit

    @staticmethod
    def from_string(string, default_unit=Unit.NONE):
        r"""Get a Size object from a string.

        :param string: The string to convert consisiting of a floating point followed by an optional unit specifier.
        :type string: str
        :param default_unit: Default unit to use if the string does not contain a unit.
        :type default_unit: Unit
        :return: The size object as specified by the string.
        :rtype: Size

        :Example:
            '1', '1.0', '1mm', '1.0mm', '1 mm', '1.0 mm', '.1 mm', '.1"'
        """
        string = string.strip()
        str_unit = re.sub(r"[-+]?(\d|(?:\d*\.\d*))\s*", "", string)
        unit = Unit.from_string(str_unit)
        if unit is Unit.NONE:
            unit = default_unit

        str_value = string[:len(string) - len(str_unit)].strip()
        return Size(float(str_value), unit)

    def round_to_base(self, base):
        r""" Get Size object rounded to given base.

        :params base: Base to round self to
        :type base: Float or Integer
        :return: New Size object rounded to given base
        :rtype: Size
        """
        return Size(round(self / base) * base)

    def __add__(self, other):
        instance = Size(super().__add__(other))
        instance.original_unit = self.original_unit
        return instance

    __radd__ = __add__

    def __sub__(self, other):
        instance = Size(super().__sub__(other))
        instance.original_unit = self.original_unit
        return instance

    def __rsub__(self, other):
        instance = Size(super().__rsub__(other))
        instance.original_unit = self.original_unit
        return instance

    def __mul__(self, other):
        instance = Size(super().__mul__(other))
        instance.original_unit = self.original_unit
        return instance

    def __rmul__(self, other):
        instance = Size(super().__rmul__(other))
        instance.original_unit = self.original_unit
        return instance

    def __div__(self, other):
        return self.__truediv__(other)

    def __rdiv__(self, other):
        return self.__rtruediv__(other)

    def __truediv__(self, other):
        instance = Size(super().__truediv__(other))
        instance.original_unit = self.original_unit
        return instance

    def __rtruediv__(self, other):
        instance = Size(super().__rtruediv__(other))
        instance.original_unit = self.original_unit
        return instance

    def __floordiv__(self, other):
        instance = Size(super().__floordiv__(other))
        instance.original_unit = self.original_unit
        return instance

    def __rfloordiv__(self, other):
        instance = Size(super().__rfloordiv__(other))
        instance.original_unit = self.original_unit
        return instance

    def __neg__(self):
        instance = Size(super().__neg__())
        instance.original_unit = self.original_unit
        return instance


class SizeFactory(Size):
    r"""Factory class for creating Size objects from different input types.

    :param value: The value of the size.
    :type value: float, str or Size
    :param unit: Unit specifier of the given value. Default: Unit.NONE
    :type unit: Unit
    """
    def __new__(cls, value, default_unit=Unit.NONE):
        if isinstance(value, str):
            return Size.from_string(value, default_unit)
        if isinstance(value, Size):
            return value
        return Size(value, default_unit)


class TolerancedSize():
    r""" Class for handling toleranced size parameters as defined by IPC

    :params:
      * *minimum* (float, str) --
        Minimum size of the dimension. None if not specified.
        (default: None)
      * *nominal* (float, str) --
        Nominal size of the dimension. None if not specified.
        (default: None, str)
      * *maximum* (float, str) --
        Maximum size of the dimension. None if not specified.
        (default: None)
      * *tolerance* (float, str or list) --
        Tolerance of the dimension. Tolerance is symetrical if
        only a single number is given. Asymetrical tolerances use a list.
        If one of the values is negative then it is the negative tolerance.
        If both are postive then the first entry is the negative tolerance.
        None if not specified.
        (default: None)
      * *default_unit* (string) --
        Default unit of the given dimension to be used for any parameter that does not specify one.
    """

    def __init__(self, minimum=None, nominal=None, maximum=None, tolerance=None, default_unit=Unit.NONE):
        if minimum is not None and maximum is not None:
            self.minimum = SizeFactory(minimum, default_unit)
            self.maximum = SizeFactory(maximum, default_unit)

        if nominal is not None:
            self.nominal = SizeFactory(nominal, default_unit)
        else:
            if minimum is None or maximum is None:
                raise KeyError("Either nominal or minimum and maximum must be given")
            self.nominal = (self.minimum + self.maximum) / 2

        if tolerance is not None:
            self.__init_tolerance(tolerance, default_unit)
        elif minimum is None or maximum is None:
            self.minimum = self.nominal
            self.maximum = self.nominal

        if self.maximum < self.minimum:
            raise ValueError(
                "Maximum is smaller than minimum. Tolerance ranges given wrong or parameters confused.")

        self.ipc_tol = self.maximum - self.minimum
        self.ipc_tol_RMS = self.ipc_tol
        self.maximum_RMS = self.maximum
        self.minimum_RMS = self.minimum

    def __init_tolerance(self, tolerance, default_unit=Unit.NONE):
        if isinstance(tolerance, (list, tuple)):
            if len(tolerance) == 2:
                tol = [SizeFactory(t, default_unit) for t in tolerance]
                if tol[0] < 0:
                    self.minimum = self.nominal + tol[0]
                    self.maximum = self.nominal + tol[1]
                elif tol[1] < 0:
                    self.minimum = self.nominal + tol[1]
                    self.maximum = self.nominal + tol[0]
                else:
                    self.minimum = self.nominal - tol[0]
                    self.maximum = self.nominal + tol[1]
            else:
                raise TypeError("Tolerance is given as a list with length other than 2.")
        else:
            tol = SizeFactory(tolerance, default_unit)
            self.minimum = self.nominal - tol
            self.maximum = self.nominal + tol

    @staticmethod
    def __from_symetrical_tolerance(string, default_unit=Unit.NONE):
        tokens = string.split('+/-')
        return TolerancedSize(nominal=tokens[0], tolerance=tokens[1], default_unit=default_unit)

    @staticmethod
    def __from_asymetrical_tolerance(string, default_unit=Unit.NONE):
        nominal_sign = ''
        if string.startswith('-') or string.startswith('+'):
            nominal_sign = string[0]
            string = string[1:]

        if string.count('+') > 1 or string.count('-') > 1:
            raise ValueError(
                'Illegal dimension specifier: {}\n'
                '\tToo many tolerance specifiers. Expected "nom +tolp -toln"'
                .format(string)
            )

        idxp = string.find('+')
        idxn = string.find('-')
        return TolerancedSize(
            nominal=nominal_sign + string[0:min(idxp, idxn)],
            tolerance=[string[idxn: idxp if idxn < idxp else None], string[idxp:idxn if idxn > idxp else None]],
            default_unit=default_unit
        )

    @staticmethod
    def __from_min_max(string, default_unit=Unit.NONE):
        tokens = string.split('..')
        if len(tokens) > 3:
            raise ValueError(
                'Illegal dimension specifier: {}\n'
                '\tToo many tokens seperated by ".." (Valid options are "min .. max" or "min .. nom .. max")'
                .format(string)
            )

        return TolerancedSize(
            minimum=tokens[0],
            maximum=tokens[-1],
            nominal=tokens[1] if len(tokens) == 3 else None,
            default_unit=default_unit
        )

    @staticmethod
    def from_string(string, default_unit=Unit.NONE):
        r""" Generate new TolerancedSize instance from size string

        :params:
            * *input* (string) --
              Size string use to generate the instance. Options are:
                * <nominal>
                * <minimal> .. <nominal> .. <maximum>
                * <minimal> .. <maximum>
                * <nominal> +/- <tolerance>
                * <nominal> +<positive tolerance> -<negative tolerance>
              Whitespace is ignored. Both .. and ... can be used as separator.
              Positive and negative tolerance can be in any order.
            * *default_unit* (Unit) --
              Default unit of the given dimension. Default is Unit.NONE.
        """
        string = re.sub(r'\s+', '', str(string))
        string = string.replace('...', '..')

        if '+/-' in string:
            return TolerancedSize.__from_symetrical_tolerance(string, default_unit)

        if '..' in string:
            return TolerancedSize.__from_min_max(string, default_unit)

        if string.count('+') >= 1 or string.count('-') >= 1:
            return TolerancedSize.__from_asymetrical_tolerance(string, default_unit)

        try:
            return TolerancedSize(nominal=string, default_unit=default_unit)
        except ValueError as exception:
            raise_from(
                ValueError(
                    'Dimension specifier not recogniced: {}\n'
                    '\t Valid options are "nom", "nom +/- tol", "nom +tolp -toln", "min .. max" or "min .. nom .. max"'.
                    format(string)
                ), exception)

    @staticmethod
    def from_yaml(yaml, base_name=None, default_unit=Unit.NONE):
        r""" Create TolerancedSize instance from parsed yaml (=dict)

        :params:
            * *yaml* (dict or string) --
              The parsed yaml document as dict,
              extracted sub dict or the size string.
            * *base_name* (string) --
              Name of the parameter (dict key)
              This key is used to get the size string or sub dict for extracting the dimension parameters or None if
              the yaml already represents the leave notes of the format. (default: None)
            * *default_unit* (Unit) --
              Default unit to be used if the strings do not specify them.

        :yaml format:
            * *String-based* ({base_name:size_string}) --
              Size string use to generate the instance. Options are:
                * <nominal>
                * <minimal> .. <nominal> .. <maximum>
                * <minimal> .. <maximum>
                * <nominal> +/- <tolerance>
                * <nominal> +<positive tolerance> -<negative tolerance>
              Whitespace is ignored. Both .. and ... can be used as separator.
              Positive and negative tolerance can be in any order.
            * *Dict-based* ({base_name:size_dict})
              The size dict supports the keys minimum, nominal, maximum and tolerance

        """
        if base_name is not None:
            if base_name + "_min" in yaml or base_name + "_max" in yaml or base_name + "_tol" in yaml:
                return TolerancedSize(
                    minimum=yaml.get(base_name + "_min"),
                    nominal=yaml.get(base_name),
                    maximum=yaml.get(base_name + "_max"),
                    tolerance=yaml.get(base_name + "_tol"),
                    default_unit=default_unit
                )
            return TolerancedSize.from_yaml(yaml.get(base_name), default_unit=default_unit)

        if isinstance(yaml, dict):
            return TolerancedSize(
                minimum=yaml.get("minimum"),
                nominal=yaml.get("nominal"),
                maximum=yaml.get("maximum"),
                tolerance=yaml.get("tolerance"),
                default_unit=default_unit
            )

        return TolerancedSize.from_string(yaml, default_unit)

    def _update_RMS(self, tolerances):
        r"""Update root mean square values with given tolerance chain

        :params:
            * *tolerance* (itterable of floats) --
        """
        square_sum = 0
        for t in tolerances:
            square_sum += t**2
        self.ipc_tol_RMS = Size(math.sqrt(square_sum))

        if self.ipc_tol_RMS > self.ipc_tol:
            if self.ipc_tol_RMS.round_to_base(1e-6) > self.ipc_tol.round_to_base(1e-6):
                raise ValueError(
                    'RMS tolerance larger than normal tolerance.'
                    'Did you give the wrong tolerances?\n'
                    '\ttol(RMS): {} tol: {}'
                    .format(self.ipc_tol_RMS, self.ipc_tol)
                )
            # the discrepancy most likely comes from floating point errors. Ignore it.
            self.ipc_tol_RMS = self.ipc_tol

        self.maximum_RMS = self.maximum - (self.ipc_tol - self.ipc_tol_RMS) / 2
        self.minimum_RMS = self.minimum + (self.ipc_tol - self.ipc_tol_RMS) / 2

    def __add__(self, other):
        if isinstance(other, (int, float)):
            result = TolerancedSize(
                minimum=self.minimum + other,
                nominal=self.nominal + other,
                maximum=self.maximum + other
            )
            return result

        result = TolerancedSize(
            minimum=self.minimum + other.minimum,
            nominal=self.nominal + other.nominal,
            maximum=self.maximum + other.maximum
        )
        result._update_RMS([self.ipc_tol_RMS, other.ipc_tol_RMS])
        return result

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            result = TolerancedSize(
                minimum=self.minimum - other,
                nominal=self.nominal - other,
                maximum=self.maximum - other
            )
            return result

        result = TolerancedSize(
            minimum=self.minimum - other.maximum,
            nominal=self.nominal - other.nominal,
            maximum=self.maximum - other.minimum
        )
        result._update_RMS([self.ipc_tol_RMS, other.ipc_tol_RMS])
        return result

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError(
                "Multiplication is only implemented against float or int"
            )
        result = TolerancedSize(
            minimum=self.minimum * other,
            nominal=self.nominal * other,
            maximum=self.maximum * other
        )
        result._update_RMS([self.ipc_tol_RMS * math.sqrt(other)])
        return result

    __rmul__ = __mul__

    def __div__(self, other):
        return self.__truediv__(other)

    def __truediv__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError(
                "Division is only implemented against float or int"
            )
        result = TolerancedSize(
            minimum=self.minimum / other,
            nominal=self.nominal / other,
            maximum=self.maximum / other
        )
        result._update_RMS([self.ipc_tol_RMS / math.sqrt(other)])
        return result

    def __floordiv__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError(
                "Integer division is only implemented against float or int"
            )
        result = TolerancedSize(
            minimum=self.minimum // other,
            nominal=self.nominal // other,
            maximum=self.maximum // other
        )
        result._update_RMS([self.ipc_tol_RMS // math.sqrt(other)])
        return result

    def __str__(self):
        return 'nom: {}, min: {}, max: {}  | min_rms: {}, max_rms: {}'\
            .format(self.nominal, self.minimum, self.maximum, self.minimum_RMS, self.maximum_RMS)
