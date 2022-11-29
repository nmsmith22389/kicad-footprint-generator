#!/usr/bin/env python

import collections.abc
import copy

def dictMerge(a, b):
    """Recursively merges the contents of two dict objects
    
    This function is similar to the built-in dict.update() method, but instead 
    of clobbering the contents of one dictionary with another, it recursively
    combines dictionaries. The result is a dictionary containing the combined
    contents of the arguments. If both dictionaries contain a key with the same
    name (at the same level), the value in `b` takes precedence. Keys prefixed
    with a "+" are added to the corresponding key in the base dictionary.
    
    Parameters
    ----------
    a : dict
        Base dictionary
    b : dict
        Dictionary containing values to merge into `a`
    
    Returns
    -------
    Merged dictionaries (copy of `a` with contents updated from `b`)
    
    Examples
    --------
    >>> a = {'a': 1, 'b': 2, 'c': {'a': 1, 'b': 2}}
    >>> b = {'c': {'b': 3}, 'd': 4}
    >>> dictMerge(a, b)
    {'a': 1, 'b': 2, 'c': {'a': 1, 'b': 3}, 'd': 4}
    """
    c = copy.deepcopy(a)
    for k in b:
        if isinstance(b[k], collections.abc.Mapping):
            c[k] = dictMerge(c.get(k, {}), b[k])
        elif k.startswith("+"):
            c[k[1:]] += b[k]
        else:
            c[k] = copy.copy(b[k])
    return c

def dictInherit(d):
    """Recursively merges dictionaries within a hierarchy using 'inherit' entries
    
    The top-level dictionary (`d`) can be thought of as a type of "namespace"
    containing a collection of objects (sub-dictionaries). Objects within the
    namespace may contain an 'inherit' entry, which stores the key for another
    object within the namespace.
    
    Inheritance is done recursively, so it is possible to have multiple levels
    of inheritance (object c can inherit b, which itself inherits from a). When
    this function is executed, it iterates through every entry in `d` and runs
    dictMerge() until all of the 'inherit' entries have been resolved. The 
    result is applied to `d` in-place.
    
    Parameters
    ----------
    d : dict
        Top-level "namespace" dictionary containing other dictionaries, each of
        which may contain an 'inherit' key to be resolved; edited in-place
    
    Raises
    ------
    RecursionError
        If two dictionaries attempt to inherit each other
    KeyError
        If a dictionary tries to inherit from a key that is not in `d`
    """
    
    def _dictInherit(d, child, parent):
        if 'inherit' not in parent:
            del child['inherit']
            return dictMerge(parent, child)
        elif d[parent['inherit']] is child:
            raise RecursionError
        else:
            return _dictInherit(d, parent, d[parent['inherit']])

    for (k, v) in d.items():
        if isinstance(v, collections.abc.Mapping) and 'inherit' in v:
            d[k] = _dictInherit(d, v, d[v['inherit']])
        else:
            continue
