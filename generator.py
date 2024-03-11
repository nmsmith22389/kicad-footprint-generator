#!/usr/bin/env python3

import os
import importlib
import argparse
from OCP.Message import Message, Message_Gravity
from _tools import parameters
import sys

def get_part_count(dir_name):
    try:
        all_params = parameters.load_parameters(dir_name)
        return len(all_params)
    except:
        return None

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
    parser.add_argument('-v', '--verbose',
                        help='Show OCCT output', action="store_true")
    parser.add_argument('--enable-vrml', default="True",
                        help='Sets whether or not to export the VRML files in addition to the STEP files.')
    args = parser.parse_args()

    # This is an odd CLI, but it's always been like this
    args.enable_vrml = args.enable_vrml.lower() == "true"

    # Helps filter out directories that should not be processed
    filter_dirs = ["_screenshots", "_tools", ".git", "Example", "WIP", "exportVRML"]

    # Get a list of the package directories so that we can work through them
    dir_list = [dir_name for dir_name in os.listdir(".")
                if os.path.isdir(dir_name) and dir_name not in filter_dirs and os.path.exists(os.path.join(dir_name, "__init__.py"))]
    dir_list.sort()
    if not args.verbose:
        Message.DefaultMessenger_s().Printers().First().SetTraceLevel(Message_Gravity.Message_Warning)
    # If the user requests that a specific library be generated,
    # only generate that
    if args.library is not None:
        library=os.path.normpath(args.library)
        if not library in dir_list:
            print(f"{library} is not a valid library")
            sys.exit(1)
        partcount = get_part_count(library) or "unknown number of"
        # Import the current package by name and run the generator
        mod = importlib.import_module(library + ".main_generator")

        # Generate all or a specific package based on the command
        # line arguments
        if args.package is None:
            print(f"Generating only library named {library} with {partcount} entries")
            mod.make_models("all", args.output_dir, args.enable_vrml)
        else:
            print(f"Generating part {args.package} from library named {library}")
            mod.make_models(args.package, args.output_dir, args.enable_vrml)
    else:

        print(f"Found {len(dir_list)} generators to run.")
        for index,dir_name in enumerate(dir_list):
            partcount = get_part_count(dir_name) or "unknown number of"

            print(f"Generating library {index+1}/{len(dir_list)}: {dir_name} with {partcount} entries")
            # Import the current package by name and run the generator
            mod = importlib.import_module(dir_name + ".main_generator")
            mod.make_models("all", args.output_dir, args.enable_vrml)
    print("Generation complete.")


if __name__ == "__main__":
    main()
