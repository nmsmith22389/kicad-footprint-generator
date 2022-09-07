KiCad 3D Model Generator Scripts
===

## Introduction

This repository contains a number of scripts to generate STEP AP214 3D models and VRML 3D models for use with the KiCad EDA system.

The parametric scripts are derived from CadQuery scripts for generating QFP, DIP and pinHeaders models in X3D format.  
Original author: **hyOzd** [author site](https://bitbucket.org/hyOzd/freecad-macros/)

These were greatly extended by **easyw** in the repository <https://github.com/easyw/kicad-3d-models-in-freecad>

CadQuery 2.x update authors: [jmwright](https://github.com/jmwright) with work sponsored by [KiCAD Services Corporation](https://www.kipro-pcb.com/).

Requirements to run these scripts:  
[CadQuery 2](https://github.com/CadQuery/cadquery)  
[Python 3](https://www.python.org/)  
[OpenCascade 7](https://dev.opencascade.org/doc/overview/html/index.html)

## Usage

**Note**: CadQuery 2.2.0b1 or higher must be installed for this process to work. 

Here is a usage summary for the generator.py script:
```
usage: generator.py [-h] --output_dir OUTPUT_DIR [--library LIBRARY] [--package PACKAGE] [--enable-vrml ENABLE_VRML]

Controls the generation and export of KiCAD 3D models.

optional arguments:
  -h, --help            show this help message and exit
  --output_dir OUTPUT_DIR
                        Sets the directory to write the generated models to.
  --library LIBRARY     Selects a specific library to generate models for.
  --package PACKAGE     Selects a specific package configuration to generate models for.
  --enable-vrml ENABLE_VRML
                        Sets whether or not to export the VRML files in addition to the STEP files (False or True).
```

**Example 1**: Run the generator to create all models and store the output files in the system's temporary directory.
```
./generator.py --output_dir /tmp/3dmodels
```

**Example 2**: Run the generator to create the models from each package in a specific library.
```
./generator.py --output_dir /tmp/3dmodels --library Capacitor_THT
```

**Example 3**: Run the generator to create the models from a specific library and package.
```
./generator.py --output_dir /tmp/3dmodels --library Capacitor_THT --package CP_Axial_L10.0mm_D4.5mm_P15.00mm_Horizontal
```

**Example 4**: Run the generator to create models from a specific library and package, but exclude the VRML exports.
```
./generator.py --output_dir /tmp/3dmodels --library Capacitor_THT --package CP_Axial_L10.0mm_D4.5mm_P15.00mm_Horizontal --enable-vrml False
```

## Validation

Some simple validation can be done on the exported files via the `validator.py` script. Here is a usage summary of that script.

```
usage: validator.py [-h] --unvalidated_dir UNVALIDATED --validated_dir VALIDATED

Validates generated KiCAD 3D models against previously validated models.

optional arguments:
  -h, --help            show this help message and exit
  --unvalidated_dir UNVALIDATED
                        Root directory containing the generated models to be validated.
  --validated_dir VALIDATED
                        Root directory containing the previously validated models to check against.
```

**Example 1**: Validating all generated files against known good files in the KiCAD distribution.

```
./validator.py --unvalidated_dir /tmp/3dmodels --validated_dir /usr/share/kicad/3dmodels/
```

**NOTE**: The validator will not catch every type of problem with an exported file. For instance, it does not check to make sure that the color matches between the reference and new files.

## Adding New Generators

When adding generators to this repository, a developer may want to start by copying and renaming the `Example` directory. This directory contains 4 files.

* `__init__.py` - Tells the generator script that this directory is a generator that is ready for processing. Directories can be excluded (even if they have this file) by adding them to the `filter_dirs` list in `generator.py`.
* `cq_parameters.yaml` - YAML formatted file that contains things like color and dimension specifications. There is typically one entry for each type of part you wish to generate, but this does not have to be the case. For example, if a part requires variants with 6 to 20 pins, the number of pins from each variant can be added into an array within this file. Then the `main_generator.py` script can iterate over this array and create all the variants at once.
* `main_generator.py` - The `make_models` method within this module is what `generator.py` calls to create and output the models. Depending on the complexity of the model being generated, there may not be many changes required in this file. At the very least `generator_directory` should be set to the directory name for the generator. For more complex models, the solids returned from `generate_part` may need to be modified, and the way they are added to the assembly may need to be modified as well.
* `model_module.py` - This is the module that does most of the work of generating the CAD model via CadQuery. This module exists to keep `main_generator.py` from containing too much model code. Knowledge of CadQuery will be required to code this file, and the way it is done is up to the developer. There is not one single way to create any given 3D object. For help, please reach out to the CadQuery community on [Discord](https://discord.gg/Bj9AQPsCfx) or [Google Groups](https://groups.google.com/g/cadquery).

You can test your generator without running all others by specifying your library and package name. The library name comes from the directory your generator is in, and the package is the specific entry from `cq_parameters.yaml` you want to use for the specifications. For example:

```
./generator.py --output_dir /tmp/3dmodels --library [GENERATOR DIRECTORY] --package [YAML ENTRY NAME]
```

Credits
=======

Original author **hyOzd**  
Original author site: <https://bitbucket.org/hyOzd/freecad-macros/>  
FreeCAD & cadquery tools:  
libraries to export generated models in STEP & VRML format  
- cad tools functions  
Copyright (c) 2015 **Maurice** <https://launchpad.net/~easyw>

CadQuery 2.x update: [jmwright](https://github.com/jmwright) with work sponsored by [KiCAD Services Corporation](https://www.kipro-pcb.com/).

Copyright
=========

This document *README* and all the materials and files at the repository
are  
* Copyright © 2015 by Maurice
* Copyright © 2020 by the KiCad EDA project
* Copyright © 2022 by the KiCad EDA project 

License
=======
Please see the [LICENSE file](LICENSE) for licensing details