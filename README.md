# KiCad footprint and 3D model generators

**License:** GNU GPLv3+

The repository contains code and libraries that are used to generate some of the footprints and
3D models in the [KiCad](https://kicad-pcb.org/) official libraries.

The code is written in Python. The footprint generators are based on the KicadModTree library, originally
developed by Thomas Pointhuber. The 3D model generators are mostly based on the
[CadQuery](https://github.com/CadQuery/cadquery) parametric CAD library.

All the code in this repository is licensed under the GNU GPLv3+ license.

API documentation for Python code in this repository is available at
[Read the Docs](https://kicad-footprint-generator.readthedocs.io/en/latest/).

Documentation for the generators themselves is being moved to the KiCad Library Wiki. This
includes information on how to run the generators and how to contribute new generators:

* [Footprint Generators](https://gitlab.com/groups/kicad/libraries/-/wikis/Footprint-Generators)
* [3D Model Generators](https://gitlab.com/groups/kicad/libraries/-/wikis/3D-Generators)

## Development

### Install development dependencies

You should install this in a virtual environment to avoid conflicts with other projects.
Create a virtual environment with the following command:

```sh
python -m venv /path/to/venv
```

You can choose where to create the virtual environment. `.venv` in the root of the repository
is a common choice.

Once the virtual environment is created, use this command to activate it (you need to
run this command in every new shell you want to use the virtual environment in):

```sh
source /path/to/venv/bin/activate
```

This installs the dependencies required for development and the package itself in editable mode.
You only need to run this command once per virtual environment:

```sh
./manage.sh update_dev_packages
```

If you get the error `ModuleNotFoundError: No module named 'KicadModTree'`, this means you need to run the
second command above. This can happen if you have an old virtual environment that hasn't had this command run
in it yet.

To uninstall the package, run the following command in the virtual environment:

```sh
pip uninstall kicad-footprint-generator
```

### Run tests

This runs the unit tests and the linter:

```sh
./manage.sh tests
```

### Configuring the git repository

To ignore formatting-only commits:

```sh
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

### Development workflow

* Create a new branch for your work.
* Install or activate the virtual environment.
* Make your changes.
* Run the relevant generator
* Verify the generated files are correct:
    * Check the generated files in KiCad.
    * Check the generated 3D models in FreeCAD.
* Copy the generated files to the appropriate output directory (if the generator doesn't do this for you).
* Run the tests:
    * `./manage.sh tests`
* Commit your changes.
* Push your branch to your GitLab fork.
* Create a merge request.

## Overview

The repository is structured as follows:

* `KicadModTree`: The KicadModTree framework which is used for footprint generation
* `scripts`: The footprint generators themselves
* `3d-model-generator`: The 3D model generators
* `docs`: The documentation, structured as a Sphinx project
