import yaml
from importlib import resources


class IpcRules:

    def __init__(self, data: dict):
        """
        Initialize the IpcRules class with the given data.

        :param data: Dictionary containing IPC rules. Probalby this comes from the
                     YAML file in the package, but you can provide your own.
        """
        self._data = data

        generic_rules = data.get("ipc_generic_rules", {})

        if "min_ep_to_pad_clearance" in generic_rules:
            self.min_ep_to_pad_clearance = float(generic_rules["min_ep_to_pad_clearance"])
        else:
            # This def doesn't specify a value for min_ep_to_pad_clearance
            # (is this really an IPC figure, not global config?)
            self.min_ep_to_pad_clearance = None

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

    @property
    def raw_data(self):
        """
        Legacy accessor for dict-based data.
        """
        return self._data
