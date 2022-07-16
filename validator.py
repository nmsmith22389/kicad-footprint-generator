#!/usr/bin/env python3

import os
from sys import argv
import argparse
import cadquery as cq

def assert_eq(arg1, arg2, msg):
    if arg1 != arg2:
        raise AssertionError(str(arg1) + " and " + str(arg2) + " are not equal. " + msg)

def assert_almost_eq(arg1, arg2, tolerance, msg):
    if arg1 > arg2 + tolerance or arg1 < arg2 - tolerance:
        raise AssertionError(str(arg1) + " and " + str(arg2) + " are not equal within a tolerance of " + str(tolerance) + " " + msg)


def main():
    # The tolerance for the volume equality check
    tolerance = 1.0

    # Handle the command line arguments
    parser = argparse.ArgumentParser(description='Validates generated KiCAD 3D models against previously validated models.')
    parser.add_argument('--unvalidated_dir', dest='unvalidated', required=True,
                    help='Root directory containing the generated models to be validated.')
    parser.add_argument('--validated_dir', dest='validated', required=True,
                    help='Root directory containing the previously validated models to check against.')
    args = parser.parse_args()

    # List the directories
    dir_list = os.listdir(args.validated)

    # Step through all the directories in the validated root directory and check to see if they have equivalents in the unvalidated
    for valid_dir in dir_list:
        # See if there is a matching unvalidated directory
        unvalid_dir = os.path.join(args.unvalidated, valid_dir)
        if os.path.isdir(unvalid_dir):
            valid_path = os.path.join(args.validated, valid_dir)
            valid_files = os.listdir(valid_path)

            # Step through all the valid files and look for matches in the unvalidated directory
            for valid_file in valid_files:
                # We need the path to both the valid and unvalid files to check them against each other
                valid_file_path = os.path.join(args.validated, valid_dir, valid_file)
                unvalid_file_path = os.path.join(args.unvalidated, valid_dir, valid_file)

                # See if the file exists in the unvalidated models directory
                if os.path.isfile(unvalid_file_path):
                    # Filter out VRML files
                    if unvalid_file_path.endswith(".step"):
                        # Load the step file for each file
                        valid = cq.importers.importStep(valid_file_path)
                        unvalid = cq.importers.importStep(unvalid_file_path)

                        try:
                            # Check multiple aspects about the step files to make sure they are equivalent
                            assert_almost_eq(unvalid.combine().val().Volume(), valid.combine().val().Volume(), tolerance, "Unvalidated and validated STEP files should have similar volumes.")
                        except Exception as ex:
                            # Let the user know what is being checked
                            print("Validated file: " + valid_file_path)
                            print("Unvalidated file: " + unvalid_file_path)
                            print(ex)
                            print("")

if __name__ == "__main__":
    main()
