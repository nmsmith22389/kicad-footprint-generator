#!/usr/bin/env python3

import os
from sys import argv
import importlib
import argparse
import cadquery as cq

def main():
    parser = argparse.ArgumentParser(description='Audits the generated KiCAD 3D models against known STEP files.')
    parser.add_argument('--new_step_dir', dest='new_step_dir', required=True,
                    help='Sets the directory where the new generated STEP files have been placed.')
    parser.add_argument('--ref_step_dir', dest='ref_step_dir', required=True,
                    help='Sets the directory where the reference STEP files have been placed.')
    parser.add_argument('--library', dest='library', required=False,
                    help='Selects a specific library to generate models for.')
    args = parser.parse_args()

    # Get a list of the package directories so that we can work through them
    new_dir_list = [ dir_name for dir_name in os.listdir(args.new_step_dir) ]
    ref_dir_list = [ dir_name for dir_name in os.listdir(args.ref_step_dir) ]

    # Check to make sure that all the directories exist in both the new and reference locations
    for nd in new_dir_list:
        if nd not in ref_dir_list:
            print("Directory {} exists in the new STEP directory, but not in the reference STEP directory.".format(nd))
        else:
            ref_files = [ dir_name for dir_name in os.listdir(os.path.join(args.ref_step_dir, nd)) ]
            for ref_file in ref_files:
                if not os.path.exists(os.path.join(args.new_step_dir, nd, ref_file)):
                    if ref_file.endswith('step') or ref_file.endswith('wrl'):
                        print("File {} exists in the new directory {}, but does not exist in the reference directory {}.".format(ref_file, os.path.join(args.new_step_dir, nd, ref_file), os.path.join(args.ref_step_dir, nd, ref_file)))
    for rd in ref_dir_list:
        if rd not in new_dir_list:
            print("Directory {} exists in the reference STEP directory, but not in the new STEP directory.".format(rd))
        else:
            ref_files = [ dir_name for dir_name in os.listdir(os.path.join(args.ref_step_dir, rd)) ]
            for ref_file in ref_files:
                if not os.path.exists(os.path.join(args.new_step_dir, rd, ref_file)):
                    if ref_file.endswith('step') or ref_file.endswith('wrl'):
                        print("File {} exists in the reference directory {}, but does not exist in the new directory {}.".format(ref_file, os.path.join(args.ref_step_dir, rd, ref_file), os.path.join(args.new_step_dir, rd, ref_file)))
                else:
                    if ref_file.endswith('step'):
                        # Import the reference and new STEP files
                        ref_step = cq.importers.importStep(os.path.join(args.ref_step_dir, rd, ref_file))
                        new_step = cq.importers.importStep(os.path.join(args.new_step_dir, rd, ref_file))

                        # Check the bounding boxes format(1.29578293, '.6f')
                        ref_x_len = format(ref_step.val().BoundingBox().xlen, '.3f')
                        new_x_len = format(new_step.val().BoundingBox().xlen, '.3f')
                        ref_y_len = format(ref_step.val().BoundingBox().ylen, '.3f')
                        new_y_len = format(new_step.val().BoundingBox().ylen, '.3f')
                        ref_z_len = format(ref_step.val().BoundingBox().zlen, '.3f')
                        new_z_len = format(new_step.val().BoundingBox().zlen, '.3f')
                        if ref_x_len != new_x_len or ref_y_len != new_y_len or ref_z_len != new_z_len:
                            print("File {} has a bounding box that does not match between the reference and new STEP files: ref_xlen {} vs new_xlen {}, ref_ylen {} vs new_ylen {}, ref_zlen {} vs new_zlen {}.".format(os.path.join(args.ref_step_dir, rd, ref_file), ref_x_len, new_x_len, ref_y_len, new_y_len, ref_z_len, new_z_len))

            # print(ref_files)

if __name__ == "__main__":
    main()
