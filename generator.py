#!/usr/bin/env python3

import os
import importlib
import argparse
from OCP.Message import Message, Message_Gravity
from _tools import parameters
import sys

def get_package_names(dir_name):
    try:
        all_params = parameters.load_parameters(dir_name)
        return all_params.keys()
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
    parser.add_argument('--dry-run',
                        help='Do not run the generators, only print the list of parts and libraries.', action="store_true")
    args = parser.parse_args()

    # This is an odd CLI, but it's always been like this
    args.enable_vrml = args.enable_vrml.lower() == "true"

    # Error out if only package has been specified without a library
    if args.library is None and args.package is not None:
        print("You need to specify -l/--library along with -p/--package.")
        sys.exit(1)

    # Helps filter out directories that should not be processed
    filter_dirs = ["_screenshots", "_tools", ".git", "Example", "WIP", "exportVRML"]

    # Get a list of the package directories so that we can work through them
    dir_list = [dir_name for dir_name in os.listdir(".")
                if os.path.isdir(dir_name) and dir_name not in filter_dirs and os.path.exists(os.path.join(dir_name, "__init__.py"))]
    dir_list.sort()
    if not args.verbose:
        Message.DefaultMessenger_s().Printers().First().SetTraceLevel(Message_Gravity.Message_Warning)

    if args.library is None:
        # If no library is specified, generate all available ones
        print(f"Found {len(dir_list)} generators to run.")
        libraries_to_generate = dir_list
    else:
        # If the user requests that a specific library be generated,
        # only generate that
        library = os.path.normpath(args.library)
        if not library in dir_list:
            print(f"{library} is not a valid library")
            sys.exit(1)
        libraries_to_generate = [library]

    for index, library in enumerate(libraries_to_generate):
        known_packages = get_package_names(library)
        # Import the current library to run the generator
        mod = importlib.import_module(library + ".main_generator")

        # Some libraries like Inductors_SMD don't list their parts, so they need special handling
        if known_packages is None:
            if args.package is None:
                print(f"Generating library {index+1}/{len(libraries_to_generate)}: {library} with unknown number of entries")
                if not args.dry_run:
                    mod.make_models("all", args.output_dir, args.enable_vrml)
            elif args.library is not None:
                print(f"    => Generating part '{args.package}' from library '{library}'")
                if not args.dry_run:
                    mod.make_models(args.package, args.output_dir, args.enable_vrml)
        else:
            # Generate all or a specific package based on the command line arguments
            if args.package is None:
                packages_to_generate = known_packages
            else:
                # If the part exists in that library, generate it, otherwise error out
                if args.package in known_packages:
                    packages_to_generate = [args.package]
                else:
                    print(f"Part '{args.package}' does not exist in library {library}")
                    sys.exit(1)

            if len(packages_to_generate) > 1:
                print(f"Generating library {index+1}/{len(libraries_to_generate)}: {library}")

            for package_index, package in enumerate(packages_to_generate):
                print(f"    => Generating part {package_index+1}/{len(packages_to_generate)}: '{package}' from library '{library}'")
                if not args.dry_run:
                    mod.make_models(package, args.output_dir, args.enable_vrml)

    print("Generation complete.")


if __name__ == "__main__":
    main()
