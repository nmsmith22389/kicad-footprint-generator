# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

"""Dictionary tools."""

import copy
from collections.abc import Mapping
from typing import Any, cast


def dictMerge(a: dict[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    """Merge recursively the contents of two `dict` objects.

    This function is similar to the built-in dict.update() method, but instead
    of clobbering the contents of one dictionary with another, it recursively
    combines dictionaries. The result is a dictionary containing the combined
    contents of the arguments. If both dictionaries contain a key with the same
    name (at the same level), the value in `b` takes precedence.

    Args:
        a: Base dictionary used as the merge destination.
        b: Dictionary containing values to merge into `a`.

    Returns:
        The merged dictionaries (`a` with contents updated from `b`).

    Examples:
        >>> a = {'a': 1, 'b': 2, 'c': {'a': 1, 'b': 2}}
        >>> b = {'c': {'b': 3}, 'd': 4}
        >>> dictMerge(a, b)
        {'a': 1, 'b': 2, 'c': {'a': 1, 'b': 3}, 'd': 4}
    """
    for k, v in b.items():
        if isinstance(v, Mapping):
            a[k] = dictMerge(a.get(k, {}), cast(Mapping[str, Any], v))
        else:
            a[k] = v
    return a


def dictInherit(d: dict[str, Any]) -> None:
    """Merge recursively dictionaries within a hierarchy using 'inherit' entries.

    The top-level dictionary (`d`) can be thought of as a type of "namespace"
    containing a collection of objects (sub-dictionaries). Objects within the
    namespace may contain an 'inherit' entry, which stores the key for another
    object within the namespace.

    Inheritance is done recursively, so it is possible to have multiple levels
    of inheritance (object c can inherit b, which itself inherits from a). When
    this function is executed, it iterates through every entry in `d` and runs
    dictMerge() until all of the 'inherit' entries have been resolved. The
    result is applied to `d` in-place.

    Args:
        d: Top-level "namespace" dictionary containing other dictionaries, each of
            which may contain an 'inherit' key to be resolved; edited in-place.

    Raises:
        RecursionError: If two dictionaries attempt to inherit each other.
        KeyError: If a dictionary tries to inherit from a key that is not in `d`.

    Examples:
        Typical JSON/YAML file structure that can be processed by this function:

        .. code-block::

            {
                "1": {
                    "a": 1,
                    "b": {"c": 2, "d": 3, ...}
                },
                "2": {
                    "inherit": "1",
                    "b": {"c": 3}
                },
                ...
                "n": {
                    "inherit": "2",
                    "d": 4
                }
            }

        The result will look something like this:

        .. code-block::

            {
                "1": {
                    "a": 1,
                    "b": {"c": 2, "d": 3, ...}
                },
                "2": {
                    "a": 1,
                    "b": {"c": 3, "d": 3, ...}
                },
                ...
                "n": {
                    "a": 1,
                    "b": {"c": 3, "d": 3, ...},
                    "d": 4
                }
            }
    """

    def dictInherit(
        d: dict[str, Any], child: dict[str, Any], parent: dict[str, Any]
    ) -> dict[str, Any]:
        if "inherit" not in parent:
            del child["inherit"]
            p = copy.deepcopy(parent)
            return dictMerge(p, child)
        elif d[parent["inherit"]] is child:
            raise RecursionError
        else:
            return dictInherit(d, parent, d[parent["inherit"]])

    for k, v in d.items():
        if isinstance(v, Mapping) and "inherit" in v:
            d[k] = dictInherit(d, cast(dict[str, Any], v), d[v["inherit"]])
        else:
            continue
