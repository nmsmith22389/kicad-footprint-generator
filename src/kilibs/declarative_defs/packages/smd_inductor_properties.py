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
"""Classes for SMD inductor properties."""

import abc
import csv
import logging
from pathlib import Path
from typing import Any

from kilibs.declarative_defs.packages.two_pad_dimensions import TwoPadDimensions
from kilibs.geom import Vector3D
from kilibs.util import dict_tools


def _get_key_as_float_or_none(d: dict[str, Any], key: str) -> float | None:
    """Return the key as a `float` or, if the key is not present in the dictionary,
    then `None` is returned.

    Args:
        d: The dictionary.
        key: The key.
    """
    try:
        return float(d[key])
    except KeyError:
        return None


class InductorBodyParameters(abc.ABC):
    """Parameters for the body of an inductor."""

    @abc.abstractmethod
    def get_body_size(self) -> Vector3D:
        """Get the size of the body of the inductor for naming purposes."""
        pass


class TwoPadInductorParameters(InductorBodyParameters):
    """
    Parameters for any simple two-pad inductor model.
    """

    def __init__(self, data: dict[str, Any]):
        self.width_x: float
        """Width of the inductor in mm."""
        self.length_y: float
        """Length of the inductor in mm."""
        self.height: float
        """Overall height of the inductor in mm."""
        landing_dims: TwoPadDimensions
        """Dimensions of PCB landing pads in mm."""
        device_pad_dims: TwoPadDimensions
        """Dimensions of pads on the inductor in mm."""

        self.width_x = float(data["widthX"])
        self.length_y = float(data["lengthY"])
        self.height = float(data["height"])
        self.landing_dims = self._derive_landing_size(data)
        self.device_pad_dims = self._derive_pad_spacing(data)

    def get_body_size(self) -> Vector3D:
        """Get the size of the body of the inductor for naming purposes.

        Returns:
            The size of the body of the inductor as a `Vector2D`.
        """
        return Vector3D(self.width_x, self.length_y, self.height)

    def _derive_landing_size(self, data: dict[str, Any]) -> TwoPadDimensions:
        """Handle the various methods of providing sufficient dimensions to derive the
        land X dimension.

        Args:
            data: The dictionary containing the PCB landing pad dimensions.

        Returns:
            An instance of `TwoPadDimensions` containing the pad dimensions extracted
            from the given `dict`.
        """
        landing_y = float(data["landingY"])
        xin = _get_key_as_float_or_none(data, "landingX")
        spc_c = _get_key_as_float_or_none(data, "landingSpacingX")
        spc_ix = _get_key_as_float_or_none(data, "landingInsideX")
        spc_ox = _get_key_as_float_or_none(data, "landingOutsideX")
        try:
            return TwoPadDimensions(landing_y, xin, spc_c, spc_ix, spc_ox)
        except ValueError:
            raise RuntimeError(
                "Unhandled combination of landing dimensions, "
                "saw: " + ", ".join(data.keys())
            )

    def _derive_pad_spacing(self, data: dict[str, str]) -> TwoPadDimensions:
        """Handle the various methods of providing sufficient dimensions to derive the
        pad dimensions (this is the pad on the device, not on the PCB - that is the
        landing).

        If the parameters are not given, pads will be constructed from the landing sizes
        (is this an error?).

        Args:
            data: The dictionary from which to extract the pad dimensions of the
                inductor.

        Returns:
            An instance of `TwoPadDimensions` containing the pad dimensions extracted
            from the given `dict`.
        """
        pad_y = _get_key_as_float_or_none(data, "padY")
        if pad_y is None:
            logging.info(
                "No physical pad dimensions (padY) found - using body and PCB landing "
                "dimensions (lengthY, landingY) as a substitute."
            )
            pad_y = min(self.landing_dims.size_crosswise, self.length_y)

        spc_c = _get_key_as_float_or_none(data, "padSpacingX")
        spc_ix = _get_key_as_float_or_none(data, "padInsideX")
        spc_ox = _get_key_as_float_or_none(data, "padOutsideX")
        pad_x = _get_key_as_float_or_none(data, "padX")
        try:
            pad_dims = TwoPadDimensions(pad_y, pad_x, spc_c, spc_ix, spc_ox)
        except ValueError:
            # We don't have enough info here to construct the pad dimensions
            # So construct a pad width to be getting on with.
            logging.info(
                "No physical pad dimensions (padX) found - using landing dimensions "
                "as a substitute."
            )
            # limit the outside dim to the overall package size
            pad_ox = min(self.landing_dims.spacing_outside, self.width_x)
            pad_dims = TwoPadDimensions(
                pad_y,
                spacing_inside=self.landing_dims.spacing_inside,
                spacing_outside=pad_ox,
            )
        return pad_dims


class CuboidParameters(TwoPadInductorParameters):
    """
    Parameters for the cuboid inductor model.
    """

    def __init__(self, data: dict[str, Any], bottom_pads: bool):
        super().__init__(data)

        self.corner_radius: float | None
        """Optional corner radius of the inductor in mm."""
        self.top_fillet_radius: float | None
        """Optional top fillet radius of the inductor in mm."""
        self.bottom_pads: bool
        """Whether the inductor has pads on the bottom side of the body."""

        self.corner_radius = _get_key_as_float_or_none(data, "cornerRadius")
        self.top_fillet_radius = _get_key_as_float_or_none(data, "topFilletRadius")

        self.bottom_pads = bottom_pads


class HorizontalAirCoreParameters(TwoPadInductorParameters):
    """
    Parameters for the horizontal air core D-foot inductor model.

    This is a special case of the two-pad inductor, where the pads are on the
    sides of the inductor, and the coil is mounted horizontally.
    """

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)

        # This default comes from what was used for the Coilcraft SQ series
        # Probably would be better to specify this.
        self.wire_size: float = data.get(
            "wireSize", self.landing_dims.size_inline * 0.5
        )
        """The size of the wire used in the coil in mm."""

        self.foot_shape: str = data["footShape"]
        """The shape of the foot of the inductor, e.g. 'd_section'"""

        # Round and rectangular foot shapes may be needed in the future,
        if self.foot_shape not in ["d_section"]:
            raise ValueError(
                f"Unknown foot shape '{self.foot_shape}' for horizontal air core inductor."
            )


class ShieldedDrumRoundedRectBlockParameters(TwoPadInductorParameters):
    """
    Parameters for the shielded drum block inductor model.

    Example series for this type: Coilcraft MSS1246:
    https://www.coilcraft.com/getmedia/960fadbe-0ca0-40e2-ae20-64edb15f3a07/mss1246.pdf
    """

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)

        self.core_diameter: float
        """Diameter of the core of the inductor in mm."""
        self.corner_radius: float
        """Optional corner radius of the inductor in mm."""

        self.core_diameter = float(data["coreDiameter"])
        self.corner_radius = float(data["cornerRadius"])


class SmdInductorProperties:
    """Object that represents the definition of a single inductor part.

    This is a complete defintion of a single inductor, which may be being
    constructed from a merged dictionary of series and part definitions.
    """

    def __init__(self, part_block: dict[str, str]) -> None:
        """Create an instance of `SmdInductorProperties`.

        Args:
            part_block: The dictionary containing the properties of the inductor.
        """

        self.part_number: str
        """Part number of the inductor."""
        self.datasheet: str | None
        """Datasheet of the inductor or `None` if the series datasheet is used."""
        self.body: InductorBodyParameters
        """The body parameters of the inductor, which determine both how the
        footprint may be drawn and how the 3D model is generated."""

        self.part_number = part_block["PartNumber"]
        self.datasheet = part_block.get("datasheet", None)

        body_type_key = part_block.get("3d", {}).get("type", 1)

        # Switch the inductor type based on the 'type' key
        match body_type_key:
            case 1 | 2:  # "cuboid":
                self.body = CuboidParameters(part_block, body_type_key == 1)
            case "horizontal_air_core":
                self.body = HorizontalAirCoreParameters(part_block)
            case "shielded_drum_rounded_rectangular_base":
                self.body = ShieldedDrumRoundedRectBlockParameters(part_block)
            case _:
                raise ValueError(
                    f"Unknown inductor type '{body_type_key}' for part {self.part_number}"
                )


class InductorSeriesProperties:
    """Object that represents the definition of a series of inductors, read from a dict,
    probably from a YAML file.

    A series is a collection of inductors that share some common properties,
    and can be generated from one CSV file or list of part definitions.

    A series may or may not correspond one-to-one with a manufacturer's series.
    For example, a manufacturer may have a series that contains different
    shapes of inductors and we can define a 'series' for each one, but they
    are all part of the same series in the manufacturer's catalog.
    """

    name: str
    """The name of the series."""
    manufacturer: str
    """The manufacturer of the inductors."""
    tags: list[str]
    """The tags."""
    has_orientation: bool
    """`True` if the inductors have an orientation and require a pin 1 marker."""
    library_name: str
    """The name of the library to store the output in."""
    series_description: str | None = None
    """Optional name of the series, used in the footprint description if the part
    number isn't enough."""
    additional_description: str | None = None
    """Optional additional description for the series, used in the footprint
    description, after the series. Can be useful when the 'series' def is only
    a subset of the manufacturer-described series."""
    parts: list[SmdInductorProperties]
    """List of the part definitions in the series."""

    def __init__(self, series_block: dict[str, Any], csv_dir: Path | None) -> None:
        """Create an instance of `InductorSeriesProperties` by loading the data from
        the given dictionary (and optionally additional CSV files).

        Args:
            series_block: The dictionary from which to extract the data of the series.
            csv_dir: Optionally, the path of the directory containing the CSV files that
                might be referenced by the dictionary.
        """
        self.name = series_block["series"]
        logging.info(f"Processing properties for series: {self.name}")
        self.manufacturer = series_block["manufacturer"]
        # space delimited list of the tags
        self.tags = series_block.get("tags", [])
        self.series_description = series_block.get("series_description", None)
        self.additional_description = series_block.get("additional_description", None)

        self.has_orientation = series_block.get("has_orientation", False)
        self.library_name = series_block["library_name"]

        def csv_line_filter(line: str) -> bool:
            """Filter function to remove lines that are comments or empty."""
            if line.startswith("#"):
                return False
            if not line.strip():
                return False
            return True

        def construct_part_properties(
            part_block: dict[str, str],
        ) -> SmdInductorProperties:
            """Combine the part dictionary with the series block to create a complete
            part definition.

            We do this because the series block may contain common parameters that
            all parts should inherit."""
            combined = dict_tools.dictMerge(series_block, part_block)
            return SmdInductorProperties(combined)

        if "csv" in series_block:
            csv_file = series_block["csv"]
            if csv_dir is not None:
                csv_file = csv_dir / csv_file
            with open(csv_file, encoding="utf-8-sig") as f:
                # Filter out rows that start with "#"
                filtered_rows = filter(csv_line_filter, f)
                # Read the CSV file and create SmdInductorProperties instances from each row
                self.parts = [
                    construct_part_properties(x) for x in csv.DictReader(filtered_rows)
                ]
        elif "parts" in series_block:
            # Load directly from the YAML (for a single-size series, for example)
            self.parts = [construct_part_properties(x) for x in series_block["parts"]]
        else:
            raise RuntimeError("Data block must contain a 'csv' or 'parts' key")
