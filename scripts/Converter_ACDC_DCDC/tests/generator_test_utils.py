import subprocess
import sexpdata
import os

class GeneratorRunner:
    """
    Simple wrapper to easily find and run the generator
    """

    def __init__(self, generator_dir: str):
        self.generator_dir = generator_dir

    def run(self, cmd: list):
        subprocess.run(cmd, cwd=self.generator_dir, check=True)


class FootprintSexpComparator:
    """
    This is a shoddy s-exp data comparison - it's not robust to things that
    don't affect the footprint, like order of elements.
    """

    def __init__(self, output_dir: str, ref_dir: str):
        self.output_dir = output_dir
        self.ref_dir = ref_dir

    def check(self, fp_name: str):
        """
        Check that the footprint has been generated and that it is valid
        """
        gen_path = os.path.join(self.output_dir, fp_name + ".kicad_mod")
        ref_path = os.path.join(self.ref_dir, fp_name + ".kicad_mod")

        assert os.path.exists(gen_path), "The generated footprint does not exist at {}".format(gen_path)
        assert os.path.exists(ref_path), "The reference footprint does not exist at {}".format(ref_path)

        # load both
        gen_fp = sexpdata.loads(open(gen_path, "r").read())
        ref_fp = sexpdata.loads(open(ref_path, "r").read())

        assert gen_fp == ref_fp, "The generated footprint does not match the reference footprint"
