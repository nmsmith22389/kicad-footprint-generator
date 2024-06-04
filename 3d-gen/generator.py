#!/usr/bin/env python3

import os
import importlib
import argparse


# TODO: Add log file for warnings and error messages
def main():
    parser = argparse.ArgumentParser(
        description='Controls the generation and export of KiCAD 3D models.')
    # Older version used --output_dir, stay backward compatible with them
    parser.add_argument('-o', '--output-dir', '--output_dir', required=True,
                        help='Sets the directory to write the generated models to.')
    parser.add_argument('-l', '--library',
                        help='Selects a specific library to generate models for.')
    parser.add_argument('-p', '--package',
                        help='Selects a specific package configuration to generate models for.')
    parser.add_argument('--enable-vrml', default="True",
                        help='Sets whether or not to export the VRML files in addition to the STEP files.')
    args = parser.parse_args()

    # This is an odd CLI, but it's always been like this
    args.enable_vrml = args.enable_vrml.lower() == "true"

    # Helps filter out directories that should not be processed
    filter_dirs = ["_screenshots", "_tools", ".git", "Example"]

    # Get a list of the package directories so that we can work through them
    dir_list = [dir_name for dir_name in os.listdir(".")
                if os.path.isdir(dir_name) and dir_name not in filter_dirs]
    dir_list.sort()

    # If the user requests that a specific library be generated,
    # only generate that
    if args.library is not None:
        # Import the current package by name and run the generator
        mod = importlib.import_module(args.library + ".main_generator")

        # Generate all or a specific package based on the command
        # line arguments
        if args.package is None:
            mod.make_models("all", args.output_dir, args.enable_vrml)
        else:
            mod.make_models(args.package, args.output_dir, args.enable_vrml)
    else:
        # If the directory contains a __init__.py file we know it has been
        # updated, so process it
        for dir_name in dir_list:
            if os.path.exists(os.path.join(dir_name, "__init__.py")):
                # Import the current package by name and run the generator
                mod = importlib.import_module(dir_name + ".main_generator")
                mod.make_models("all", args.output_dir, args.enable_vrml)


if __name__ == "__main__":
    main()
