import os

import cadquery as cq

skip_list = []


def check_step_export_union(component, output_dir, model):
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
