from kilibs.util.param_util import getOptionalNumberTypeParam, toVectorUseCopyIfNumber


class RoundRadiusHandler(object):
    r"""Handles round radius setting of a corner

    :Keyword Arguments:
        * *radius_ratio* (``float`` [0 <= r <= 0.5]``) --
          The radius ratio of the rounded rectangle.
        * *maximum_radius* (``float``) --
          The maximum radius for the rounded rectangle.
          If the radius produced by the radius_ratio parameter for the pad would
          exceed the maximum radius, the ratio is reduced to limit the radius.
          (This is useful for IPC-7351C compliance as it suggests 25% ratio with limit 0.25mm)
        * *round_radius_exact* (``float``) --
          Set an exact round radius for a pad.
    """

    radius_ratio: float
    # Maxiumum radius for the rounded rectangle, if any
    maximum_radius: float | None
    round_radius_exact: bool

    def __init__(
        self,
        radius_ratio: float,
        maximum_radius: float | None = None,
        round_radius_exact: float | None = None
    ):
        if radius_ratio < 0 or radius_ratio > 0.5:
            raise ValueError("radius_ratio must be in range [0, 0.5]")

        self.radius_ratio = radius_ratio
        self.maximum_radius = maximum_radius
        self.round_radius_exact = round_radius_exact

    def get_radius_ratio(self, shortest_sidelength: float) -> float:
        r"""get the resulting round radius ratio

        :param shortest_sidelength: shortest sidelength of a pad
        :return: the resulting round radius ratio to be used for the pad
        """
        if self.round_radius_exact is not None:
            if self.round_radius_exact > shortest_sidelength/2:
                raise ValueError(
                    "requested round radius of {} is too large for pad size of {}"
                    .format(self.round_radius_exact, shortest_sidelength)
                    )
            if self.maximum_radius is not None:
                return min(self.round_radius_exact, self.maximum_radius)/shortest_sidelength
            else:
                return self.round_radius_exact/shortest_sidelength

        if self.maximum_radius is not None:
            if self.radius_ratio*shortest_sidelength > self.maximum_radius:
                return self.maximum_radius/shortest_sidelength

        return self.radius_ratio

    def get_round_radius(self, shortest_sidelength: float) -> float:
        r"""get the resulting round radius

        :param shortest_sidelength: shortest sidelength of a pad
        :return: the resulting round radius to be used for the pad
        """
        return self.get_radius_ratio(shortest_sidelength)*shortest_sidelength

    def rounding_requested(self) -> bool:
        r"""Check if the pad has a rounded corner

        :return: True if rounded corners are required
        """
        if self.maximum_radius == 0:
            return False

        if self.round_radius_exact == 0:
            return False

        if self.radius_ratio == 0:
            return False

        return True

    def limit_max_radius(self, limit: float) -> None:
        r"""Set a new maximum limit

        :param limit: the new limit.
        """

        if not self.rounding_requested():
            return
        if self.maximum_radius is not None:
            self.maximum_radius = min(self.maximum_radius, limit)
        else:
            self.maximum_radius = limit

    def __str__(self):
        return "ratio {}, max {}, exact {}".format(
                    self.radius_ratio, self.maximum_radius,
                    self.round_radius_exact
                    )


class ChamferSizeHandler(object):
    r"""Handles chamfer setting of a pad

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *chamfer_ratio* (``float [0 <= r <= 0.5]``) --
          The chamfer ratio of the rounded rectangle. (default set by default_chamfer_ratio)
        * *maximum_chamfer* (``float``) --
          The maximum chamfer size.
          If the chamfer produced by the chamfer_ratio parameter for the pad would
          exceed the maximum size, the ratio is reduced to limit the size.
          (This is useful for IPC-7351C compliance as it suggests 25% ratio with limit 0.25mm)
        * *chamfer_exact* (``float``) --
          Set an exact round chamfer size for a pad.
        * *default_chamfer_ratio* (``float [0 <= r <= 0.5]``) --
          This parameter allows to set the default chamfer ratio
    """

    def __init__(self, **kwargs) -> None:
        default_chamfer_ratio = getOptionalNumberTypeParam(
            kwargs, 'default_chamfer_ratio', default_value=0.25,
            low_limit=0, high_limit=0.5)
        self.chamfer_ratio = getOptionalNumberTypeParam(
            kwargs, 'chamfer_ratio', default_value=default_chamfer_ratio,
            low_limit=0, high_limit=0.5)

        self.maximum_chamfer = getOptionalNumberTypeParam(
            kwargs, 'maximum_chamfer')

        if kwargs.get('chamfer_size', None) is not None:
            # Support the same vector or single number input as ChamferedPad
            # does, but native pads can only have a chamfer_size vector that is the
            # equal.
            chamfer_size = toVectorUseCopyIfNumber(
                kwargs["chamfer_size"], low_limit=0, must_be_larger=False
            )

            if chamfer_size.x != chamfer_size.y:
                raise ValueError("chamfer_size must be a square vector for native pads")

            chamfer_size = chamfer_size[0]
        else:
            chamfer_size = None

        # Override with chamfer_exact if it is set
        self.chamfer_exact = getOptionalNumberTypeParam(
            kwargs, 'chamfer_exact', default_value=chamfer_size)

    def get_chamfer_ratio(self, shortest_sidelength: float) -> float:
        r"""get the resulting chamfer ratio

        :param shortest_sidelength: shortest sidelength of a pad
        :return: the resulting chamfer ratio to be used for the pad
        """

        if self.chamfer_exact is not None:
            if self.chamfer_exact > shortest_sidelength/2:
                raise ValueError(
                    "requested chamfer of {} is too large for pad size of {}"
                    .format(self.chamfer_exact, shortest_sidelength)
                )
            if self.maximum_chamfer is not None:
                return min(self.chamfer_exact, self.maximum_chamfer)/shortest_sidelength
            else:
                return self.chamfer_exact/shortest_sidelength

        if self.maximum_chamfer is not None:
            if self.chamfer_ratio*shortest_sidelength > self.maximum_chamfer:
                return self.maximum_chamfer/shortest_sidelength

        return self.chamfer_ratio

    def get_chamfer_size(self, shortest_sidelength) -> float:
        r"""get the resulting chamfer size

        :param shortest_sidelength: shortest sidelength of a pad
        :return: the resulting chamfer size to be used for the pad
        """
        return self.get_chamfer_ratio(shortest_sidelength) * shortest_sidelength

    def chamfer_requested(self):
        r"""Check if the handler indicates a non-zero chamfer

        :return: True if a chamfer is requested
        """
        if self.maximum_chamfer == 0:
            return False

        if self.chamfer_exact == 0:
            return False

        if self.chamfer_ratio == 0:
            return False

        return True

    def limit_max_chamfer(self, limit) -> None:
        r"""Set a new maximum limit

        :param limit: the new limit.
        """
        if not self.chamfer_requested():
            return
        if self.maximum_chamfer is not None:
            self.maximum_chamfer = min(self.maximum_chamfer, limit)
        else:
            self.maximum_chamfer = limit

    def __str__(self) -> str:
        return "ratio {}, max {}, exact {}".format(
            self.chamfer_ratio, self.maximum_chamfer,
            self.chamfer_exact
        )
