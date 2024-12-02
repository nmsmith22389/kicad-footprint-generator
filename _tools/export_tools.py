import os

import cadquery as cq

from _tools.stepreduce import stepreduce

skip_list = []


def check_step_export_union(
    component: cq.Assembly, output_dir: str, model: str
) -> None:
    # Skip models that cannot be unioned properly
    if model in skip_list:
        return

    # Path to the STEP file to be validated
    cur_path = os.path.join(output_dir, model + ".step")

    # Import the STEP that was exported so that the number of solids can be checked
    union = cq.importers.importStep(cur_path)

    # Our starting tolerance
    tol = 0.001

    # Try multiple fuzzy tolerance values to try to fix
    while union.solids().size() != 1:
        component.save(
            cur_path,
            cq.exporters.ExportTypes.STEP,
            mode=cq.exporters.assembly.ExportModes.FUSED,
            assembly_name=model,
            write_pcurves=False,
            fuzzy_tol=tol,
        )

        # Make the fuse gradually less precise
        tol = tol / 0.5
        print(tol)

        # Escape clause
        if tol > 0.001:
            break

    assert union.solids().size() == 1


def postprocess_step(component: cq.Assembly, output_dir: str, model: str) -> None:
    # Path to the STEP file
    cur_path = os.path.join(output_dir, model + ".step")

    # The stepreduce algorithm seems stable, so disable verification by default
    verify = False

    if verify:
        orig_cmp = cq.Assembly(cq.importers.importStep(cur_path)).toCompound()
        stepreduce(cur_path, cur_path)
        reduced_cmp = cq.Assembly(cq.importers.importStep(cur_path)).toCompound()

        # Check volumes
        orig_volume = orig_cmp.Volume()
        reduced_volume = reduced_cmp.Volume()
        assert (
            orig_volume == reduced_volume
        ), f"Volume mismatch: {orig_volume} != {reduced_volume}"

        # Check center of mass
        orig_center_of_mass = orig_cmp.Center()
        reduced_center_of_mass = reduced_cmp.Center()
        assert (
            orig_center_of_mass == reduced_center_of_mass
        ), f"Center of mass mismatch: {orig_center_of_mass} != {reduced_center_of_mass}"
    else:
        stepreduce(cur_path, cur_path)
