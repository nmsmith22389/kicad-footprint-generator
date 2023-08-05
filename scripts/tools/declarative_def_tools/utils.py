import typing

def as_list(value):
    """
    Convert a value to a list, if it isn't already.
    """
    if (isinstance(value, str) or not isinstance(value, typing.Iterable)):
        return [value]
    return [v for v in value]
