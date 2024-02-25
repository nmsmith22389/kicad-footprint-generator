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
    parser.add_argument('--error_on_non_matching', dest='error_on_non_matching', required=False,
                    help='Whether or not to show errors related to new files not having matching original refrence files.')
    args = parser.parse_args()

    # Get a list of the package directories so that we can work through them
    new_dir_list = [ dir_name for dir_name in os.listdir(args.new_step_dir) ]
    ref_dir_list = [ dir_name for dir_name in os.listdir(args.ref_step_dir) ]

    # Check the bounding box of the new file against the bounding box of the matching old file
    for nd in new_dir_list:
        if nd not in ref_dir_list:
            print("Directory {} exists in the new STEP directory, but not in the reference STEP directory.".format(nd))
            continue
        else:
            # Step through all the new files so they can be compared to the originals
            new_files = [ dir_name for dir_name in os.listdir(os.path.join(args.new_step_dir, nd)) ]
            for new_file in new_files:
                if new_file.endswith('step'):
                    # Make sure the matching reference file exists
                    ref_step_path = os.path.join(args.ref_step_dir, nd, new_file)
                    if not os.path.exists(ref_step_path):
                        if args.error_on_non_matching != None and args.error_on_non_matching == "true":
                            print("New STEP file {} does not have a matching reference STEP file.".format(new_file))
                        continue

                    # Import the reference and new STEP files
                    new_step = cq.importers.importStep(os.path.join(args.new_step_dir, nd, new_file))
                    ref_step = cq.importers.importStep(ref_step_path)

                    # If there is more than one solid in the new STEP, we must combine the bounding boxes
                    new_step_bb = new_step.solids().all()[0].val().BoundingBox()
                    if len(new_step.solids().all()) > 1:
                        # Work through all the solids, adding their bounding boxes together
                        for solid in new_step.solids().all()[1:-1]:
                            new_step_bb.add(solid.val().BoundingBox())

                    # If there is more than one solid in the reference STEP, we must combine the bounding boxes
                    ref_step_bb = ref_step.solids().all()[0].val().BoundingBox()
                    if len(ref_step.solids().all()) > 1:
                        # Work through all the solids, adding their bounding boxes together
                        for solid in ref_step.solids().all()[1:-1]:
                            ref_step_bb.add(solid.val().BoundingBox())

                    # Check the bounding boxes
                    ref_x_len = format(ref_step_bb.xlen, '.3f')
                    new_x_len = format(new_step_bb.xlen, '.3f')
                    ref_y_len = format(ref_step_bb.ylen, '.3f')
                    new_y_len = format(new_step_bb.ylen, '.3f')
                    ref_z_len = format(ref_step_bb.zlen, '.3f')
                    new_z_len = format(new_step_bb.zlen, '.3f')
                    if ref_x_len != new_x_len or ref_y_len != new_y_len or ref_z_len != new_z_len:
                        print("File {} has a bounding box that does not match between the reference and new STEP files: ref_xlen {} vs new_xlen {}, ref_ylen {} vs new_ylen {}, ref_zlen {} vs new_zlen {}.".format(ref_step_path, ref_x_len, new_x_len, ref_y_len, new_y_len, ref_z_len, new_z_len))

                    # Compare the centers of the bounding boxes to make sure there is no part drift
                    ref_bb_center_x = format(ref_step_bb.center.x, '.3f')
                    new_bb_center_x = format(new_step_bb.center.x, '.3f')
                    ref_bb_center_y = format(ref_step_bb.center.y, '.3f')
                    new_bb_center_y = format(new_step_bb.center.y, '.3f')
                    ref_bb_center_z = format(ref_step_bb.center.z, '.3f')
                    new_bb_center_z = format(new_step_bb.center.z, '.3f')
                    if float(ref_bb_center_x) != float(new_bb_center_x) or float(ref_bb_center_y) != float(new_bb_center_y) or float(ref_bb_center_z) != float(new_bb_center_z):
                        print("File {} has a bounding box center that does not match between the reference and new STEP files: Centers - Ref X: {} vs New X: {}, Ref Y: {} vs New Y: {}, Ref Z: {} vs New Z: {}".format(ref_step_path, ref_bb_center_x, new_bb_center_x, ref_bb_center_y, new_bb_center_y, ref_bb_center_z, new_bb_center_z))

if __name__ == "__main__":
    main()
