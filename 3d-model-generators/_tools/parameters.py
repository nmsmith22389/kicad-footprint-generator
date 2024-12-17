import os
from pathlib import Path

import yaml


def load_parameters(module_dir_name):
    """
    Responsible for reading the package parameter values from the included yaml file.
    """
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = Path(this_dir).parent

        with open(
            os.path.join(modules_dir, module_dir_name, "cq_parameters.yaml"), "r"
        ) as f:
            all_params = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

    return all_params


def load_aux_parameters(file, yaml_name):
    """
    Sometimes there are auxiliary global parameters that need to be loaded from file,
    and this method does that.
    """

    try:
        this_dir = os.path.dirname(os.path.abspath(file))

        with open(os.path.join(this_dir, yaml_name), "r") as f:
            all_params = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

    return all_params
