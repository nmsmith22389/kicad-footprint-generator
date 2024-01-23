import os
import pytest

from generator_test_utils import GeneratorRunner, FootprintSexpComparator

generator_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ref_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_footprints")


def cmd_for_one_yaml(yaml: str):

    return [
        "python3",
        "Converter_DCDC.py",
        yaml
    ]


@pytest.mark.parametrize("spec_yaml, generated_fps", [
    ("Converter_DCDC.yml", ["Converter_DCDC_Murata_NCS1SxxxxSC_THT"]),
    ("traco.yml", [])
])
def test_converters(spec_yaml, generated_fps):
    """
    Test the outputs for the Coverter_ACDC_DCDC generator
    """

    runner = GeneratorRunner(generator_dir)
    cmd = cmd_for_one_yaml(spec_yaml)

    # Execute the generator
    runner.run(cmd)

    # Check the output
    comparator = FootprintSexpComparator(generator_dir, ref_dir)

    for fp in generated_fps:
        comparator.check(fp)
