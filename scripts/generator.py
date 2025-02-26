#! /usr/bin/env python

"""
This is the main script for generating footprints for the KiCad library.

It discovers generators in the `scripts` directory and runs them to generate footprints.
"""

import abc
import fnmatch
import logging
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path


class Timer:
    """
    Simple RAII timer.
    """

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end = time.perf_counter()
        self._duration = self.end - self.start
        logging.debug(f"{self.name}: took {self._duration:.6f} seconds")

    @property
    def duration(self):
        return self.duration


class Generator(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def generate(self):
        """
        Run the generator
        """
        pass

    @property
    @abc.abstractmethod
    def name(self):
        """
        The name of the generator - this is used to filter generators to run.
        """
        pass

    def matches(self, lib_filter: str) -> bool:
        """
        Check if the generator matches the given library filter.

        By default just a glob match on the name.
        """
        return fnmatch.fnmatch(self.name, lib_filter)

    class GenerationError(Exception):
        """
        An exception that is raised when a generator fails to generate footprints.
        """

        pass


class FPGenerateShGenerator(Generator):
    """
    A generator that runs a generate.sh script.

    This is the most common type of generator as of early 2025, but eventually it
    can become a more "plugin-style" kind of generator using the FootprintGenerator
    class, without shelling out, which will allow richer generation capabilities such
    as parameter introspection (eventually leading to, say, KiCad integration).
    """

    # Path to the generate.sh script
    generate_sh: Path

    def __init__(self, root_path, generate_sh: Path):
        self.generate_sh = generate_sh
        self.root_path = root_path

    def generate(self):
        logging.info("Running generate.sh: %s" % self.generate_sh)

        cmd = [self.generate_sh.absolute()]
        cwd = self.generate_sh.parent

        try:
            subprocess.run(cmd, check=True, cwd=cwd)
        except subprocess.CalledProcessError as e:
            raise Generator.GenerationError(f"Failed to run {self.generate_sh}: {e}")

    def matches(self, lib_filter: str) -> bool:
        """
        generate.sh generators match on the directory name they are in
        as well as the path to the directory
        """

        our_dir = self.generate_sh.parent

        # Try a relative glob first
        if fnmatch.fnmatch(our_dir.relative_to(self.root_path), Path(lib_filter)):
            return True

        return super().matches(lib_filter)

    @property
    def name(self):
        return self.generate_sh.parent.name


class GeneratorRunner:

    _generators: list[Generator]

    def __init__(self, root):
        self.root = root

        self._generators = []

        with Timer("Generator discovery"):
            # Discover generators
            self._generators += self._discover_generate_sh_generators()

            logging.info("Discovered %d generators" % len(self._generators))

    def _discover_generate_sh_generators(self) -> list[Generator]:

        generate_shs = []

        # Walk the root dir, looking for generate.sh files
        for dirpath, dirs, filenames in os.walk(self.root):
            if "generate.sh" in filenames:
                generate_shs.append(os.path.join(dirpath, "generate.sh"))

        sh_gens: list[Generator] = []

        for generate_sh in generate_shs:
            gen_sh_path = Path(generate_sh)
            sh_gens.append(FPGenerateShGenerator(self.root, gen_sh_path))

        return sh_gens

    def generate(self, libraries: list[str], jobs: int):
        """
        Generate footprints for the given libraries
        """

        gens = []

        # strip lib names of path bits
        def strip_lib_name(l):
            l = l.strip().rstrip(os.sep)
            return l

        libraries = [strip_lib_name(l) for l in libraries]

        if not libraries:
            print("Generating footprints for all libraries")
            gens = self._generators
        else:
            logging.debug("Generating footprints for libraries: %s" % libraries)

            for lib_filter in libraries:
                gens += [g for g in self._generators if g.matches(lib_filter)]

        logging.info("Generating footprints for %d libraries:" % len(gens))

        for g in gens:
            logging.info(f"  - {g.name}")

        if jobs == 1 or len(gens) == 1:
            # In-process generation when single-threaded case for easier debugging
            # (generators may still shell out if they want, can't help that)
            for g in gens:
                self._do_generate(g)
        else:
            # Multiprocess jobs of 'None' means use the number of CPUs
            mp_jobs = jobs if jobs else None

            with Pool(mp_jobs) as p:
                p.map(self._do_generate, gens)

    @staticmethod
    def _do_generate(gen: Generator):
        with Timer(f"Generating {gen.name}"):
            try:
                gen.generate()
            except Generator.GenerationError as e:
                logging.error(f"Failed to generate footprints for {gen.name}: {e}")


if __name__ == "__main__":

    import argparse
    import os

    parser = argparse.ArgumentParser(description="Generate KiCad footprints")

    parser.add_argument(
        "-l",
        "--library",
        type=str,
        nargs="*",
        default=None,
        help="Generator library name or globs (default: all)",
    )
    parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        help="List available generators and exit. Filter with --library.",
    )
    parser.add_argument(
        "-j", "--jobs", type=int, default=1, help="Number of jobs to run in parallel"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity level"
    )

    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    root_dir = os.path.dirname(os.path.abspath(__file__))

    generator = GeneratorRunner(root_dir)

    if args.list:
        for g in generator._generators:
            if args.library and not any(g.matches(l) for l in args.library):
                continue
            print(g.name)
        sys.exit(0)

    generator.generate(args.library if args.library else [], jobs=args.jobs)
