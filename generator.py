#!/usr/bin/env python3

import os
from sys import argv
import importlib
import argparse


# TODO: Add log file for warnings and error messages
def main():
    parser = argparse.ArgumentParser(description='Controls the generation and export of KiCAD 3D models.')
    parser.add_argument('--output_dir', dest='output_dir', required=True,
                    help='Sets the directory to write the generated models to.')
    parser.add_argument('--library', dest='library', required=False,
                    help='Selects a specific library to generate models for.')
    parser.add_argument('--package', dest='package', required=False,
                    help='Selects a specific package configuration to generate models for.')
    parser.add_argument('--enable-vrml', dest='enable_vrml', required=False,
                    help='Sets whether or not to export the VRML files in addition to the STEP files (False or True).')
    args = parser.parse_args()

    # Helps filter out directories that should not be processed
    filter_dirs = ["_screenshots", "_tools", ".git", "Example"]

    # Get a list of the package directories so that we can work through them
    dir_list = [ dir_name for dir_name in os.listdir(".") if os.path.isdir(dir_name) and dir_name not in filter_dirs ]

    # Handle the switch for whether or not to export VRML
    enable_vrml = True
    if args.enable_vrml:
        enable_vrml = True if args.enable_vrml == 'True' else False

    # If the user requests that a specific library be generated, only generate that
    if args.library is not None:
        # Import the current package by name and run the generator
        mod = importlib.import_module(args.library + ".main_generator")

        # Generate all or a specific package based on the command line arguments
        if args.package == None:
            mod.make_models("all", args.output_dir, enable_vrml)
        else:
            mod.make_models(args.package, args.output_dir, enable_vrml)
    else:
        # If the directory contains a __init__.py file we know it has been updated, so process it
        for dir_name in dir_list:
            if os.path.exists(os.path.join(dir_name, "__init__.py")):
                # Import the current package by name and run the generator
                mod = importlib.import_module(dir_name + ".main_generator")
                mod.make_models("all", args.output_dir, enable_vrml)

if __name__ == "__main__":
    main()
