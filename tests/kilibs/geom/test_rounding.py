import pytest

from kilibs.geom import rounding as R


@pytest.mark.parametrize(
    "val, grid, expected",
    [
        (0, 0, 0),
        (0.6, 0.05, 0.60),
        # Check epsilon near grid points
        (0.600000001, 0.05, 0.60),
        (0.599999999, 0.05, 0.60),
        # And for the down rounding
        (-0.600000001, 0.05, -0.60),
        (-0.599999999, 0.05, -0.60),
    ],
)
def test_round_to_grid(val, grid, expected):
    result = R.round_to_grid(val, grid, epsilon=1e-7)
    assert result == pytest.approx(expected)
