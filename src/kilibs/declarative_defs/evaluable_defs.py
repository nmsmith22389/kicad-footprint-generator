from abc import ABC, abstractmethod
from typing import Callable, TypeAlias

from kilibs.geom import Vector2D


class Evaluable(ABC):
    """
    Something that can be evaluated as an expression. This is the basic type
    that most other evaluable types are composed from.

    For example, a vector that you want to be able to evaluate as an expression
    in x and y would have one EvaluableScalar for x and one for y, and itself
    would be an Evaluable that evaluates the two scalars and returns a Vector2D.
    """

    @abstractmethod
    def evaluate(self, expr_evaluator: Callable):
        """
        Evaluate the object and return it. Exact return type depends on the
        implementing class.
        """
        raise NotImplementedError("Evaluable.evaluate() must be implemented")


class EvaluableScalar(Evaluable):
    """
    A value that can be evaluated as an expression, or just be a literal number,
    eventually returning a float.
    """

    ExprType: TypeAlias = str | float | int

    def __init__(self, dict_entry: ExprType):
        self.value = dict_entry

    def evaluate(self, expr_evaluator: Callable) -> float:
        """
        Evaluate the scalar value and return it as a float.
        """
        val = expr_evaluator(self.value)
        return float(val)


class EvaluableInt(Evaluable):
    """
    A value that can be evaluated as an expression, or just be a literal number,
    eventually returning an int.
    """

    ExprType: TypeAlias = str | int

    def __init__(self, dict_entry: ExprType):
        self.value = dict_entry

    def evaluate(self, expr_evaluator: Callable) -> int:
        """
        Evaluate the scalar value and return it as a float.
        """
        val = expr_evaluator(self.value)
        return int(val)


class EvaluableList(list):
    """
    Simple wrapper around a list that checks the length and type of the entries.
    """

    def __init__(
        self, dict_entry: list, exp_len: int | None, exp_type: type | None = None
    ):
        """
        :param dict_entry: The list to wrap
        :param exp_len: The expected length of the list, or None if any length is allowed
        :param exp_type: The expected type of the entries, or None if any type is allowed (strings are always allowed)
        """

        if not isinstance(dict_entry, list):
            raise ValueError(
                f"EvaluableList must be initialized with a list, got {dict_entry}"
            )

        if exp_len is not None and len(dict_entry) != exp_len:
            raise ValueError(
                f"EvaluableList must have length {exp_len}, got {len(dict_entry)}"
            )

        if exp_type is not None:
            for i, entry in enumerate(dict_entry):
                # Strs are evaluated as expressions, so we can't check the type now, that will
                if not isinstance(entry, str):
                    if not isinstance(entry, exp_type):
                        raise ValueError(
                            f"EvaluableList entry {i} must be of type {exp_type}, got {type(entry)}"
                        )

        super().__init__(dict_entry)


class EvaluableVector2D:
    """
    A point with x and y coordinates that can be evaluated as expressions,
    or just be literal numbers.

    This is usually used like this:

        some_key: [x, y]
    """

    x: EvaluableScalar
    y: EvaluableScalar

    def __init__(self, dict_entry: dict):

        el = EvaluableList(dict_entry, exp_len=2, exp_type=EvaluableScalar.ExprType)
        assert len(el) == 2
        self.x = EvaluableScalar(el[0])
        self.y = EvaluableScalar(el[1])

    def evaluate(self, expr_evaluator: Callable) -> Vector2D:
        """
        Evaluate the x and y coordinates and return them as a Vector2D.
        """
        return Vector2D(
            self.x.evaluate(expr_evaluator), self.y.evaluate(expr_evaluator)
        )


class EvaluableVector2Int:
    """
    A point with x and y coordinates that can be evaluated as expressions,
    or just be literal numbers.

    Can be used for integer coordinates, e.g. for grid counts, etc.
    """

    x: EvaluableInt
    y: EvaluableInt

    def __init__(self, dict_entry: dict):

        el = EvaluableList(dict_entry, exp_len=2, exp_type=EvaluableInt.ExprType)
        assert len(el) == 2
        self.x = EvaluableInt(el[0])
        self.y = EvaluableInt(el[1])

    def evaluate(self, expr_evaluator: Callable) -> tuple[int, int]:
        """
        Evaluate the x and y coordinates and return them as a Vector2D.
        """
        return (self.x.evaluate(expr_evaluator), self.y.evaluate(expr_evaluator))
