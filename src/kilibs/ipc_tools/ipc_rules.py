import dataclasses
import enum
import yaml
from importlib import resources


class IpcDensity(enum.Enum):

    # The values are the values used in ipc_defintions.yaml
    # as the keys for the density values in the IPC tables.
    LOW_DENSITY_MOST_MATERIAL = 'most'
    NOMINAL = 'nominal'
    HIGH_DENSITY_LEAST_MATERIAL = 'least'

    @classmethod
    def from_str(cls, string: str):
        """
        Convert a string 'least/nominal/most' to an IPC density specifier.
        """
        if string == 'least':
            return cls.HIGH_DENSITY_LEAST_MATERIAL
        elif string == 'nominal':
            return cls.NOMINAL
        elif string == 'most':
            return cls.LOW_DENSITY_MOST_MATERIAL

        raise ValueError("Unknown IPC density specifier: {}".format(string))


@dataclasses.dataclass
class Roundoff:
    """
    Toe/heel/fillet roundoff values for an IPC class."""
    toe: float
    heel: float
    side: float


@dataclasses.dataclass
class Offsets:
    """
    Fillet and courtyard values for an IPC class."""
    toe: float
    heel: float
    side: float
    courtyard: float


@dataclasses.dataclass
class DeviceClass:
    """
    Class representing a device class (e.g. ipc_spec_smaller_0603)
    """
    offsets: dict[IpcDensity, Offsets]
    roundoff: Roundoff

    def get_offsets(self, density: IpcDensity) -> Offsets:
        """
        Get the offsets for the given density.
        """
        return self.offsets[density]

class IpcRules:

    classes: dict[str, DeviceClass]

    def __init__(self, data: dict):
        """
        Initialize the IpcRules class with the given data.

        :param data: Dictionary containing IPC rules. Probalby this comes from the
                     YAML file in the package, but you can provide your own.
        """
        self._data = data

        # This def doesn't specify a value for min_ep_to_pad_clearance
        # (is this really an IPC figure, not global config?)
        self.min_ep_to_pad_clearance = None

        generic_rules = data.get("ipc_generic_rules", None)

        if generic_rules is not None:
            if "min_ep_to_pad_clearance" in generic_rules:
                self.min_ep_to_pad_clearance = float(generic_rules["min_ep_to_pad_clearance"])

        self.classes = {}
        for key, class_data in data.items():
            # We did these already
            if key in ["ipc_generic_rules"]:
                continue

            self.classes[key] = self._construct_class(class_data)

    @classmethod
    def from_file(cls, file_name: str = "ipc_7351b"):
        """
        Load the rules from the package data.

        If the filename is a path (with a YAML extension), use it directly,
        otherwise use the package data with that name
        """
        if file_name.endswith(".yaml"):
            data_path = file_name
        else:
            with resources.path("kilibs.ipc_tools.data", file_name + ".yaml") as res_path:
                data_path = res_path

        with open(data_path, 'r') as file:
            data = yaml.safe_load(file)
            return cls(data)

    @staticmethod
    def _roundoff_from_dict(data: dict) -> Roundoff:
        """
        Create a Roundoff instance from a dictionary.
        """
        return Roundoff(
            toe=float(data["toe"]),
            heel=float(data["heel"]),
            side=float(data["side"]),
        )

    @staticmethod
    def _offsets_from_dict(data: dict) -> Offsets:
        """
        Create an Offsets instance from a dictionary.
        """
        return Offsets(
            toe=float(data["toe"]),
            heel=float(data["heel"]),
            side=float(data["side"]),
            courtyard=float(data["courtyard"]),
        )

    @staticmethod
    def _construct_class(data: dict) -> DeviceClass:
        """
        Create a DeviceClass instance from a dictionary.

        :param data: Dictionary containing the class data.
        :return: DeviceClass instance.
        """
        offsets = {}
        for key in ["most", "nominal", "least"]:
            fillet_data = data[key]
            density = IpcDensity.from_str(key)
            offsets[density] = IpcRules._offsets_from_dict(fillet_data)

        roundoff = IpcRules._roundoff_from_dict(data["round_base"])

        return DeviceClass(
            offsets=offsets,
            roundoff=roundoff,
        )

    def get_class(self, class_name: str) -> DeviceClass:
        """
        Get the DeviceClass instance for the given class name.
        """
        return self.classes[class_name]

    @property
    def raw_data(self):
        """
        Legacy accessor for dict-based data.

        Over time, reduce the use of this property in favour of typed
        members.
        """
        return self._data
