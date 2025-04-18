#! /usr/bin/env python

"""
This is the main script for generating footprints for the KiCad library.

It discovers generators in the `scripts` directory and runs them to generate footprints.
"""

import abc
import fnmatch
import logging
import os
import subprocess
import sys
import time
import traceback
from collections.abc import Generator
from multiprocessing import Pool
from pathlib import Path

try:
    # These are the dependencies of the generators, but check them here to allow
    # us to warn the user if they are missing before running the generators.
    import yaml  # NOQA

    import asteval  # NOQA
    import pyclipper
    import tabulate
except ImportError:
    print(
        "Import failed. Use 'pip install -e .' in the repository root to install dependencies. See the README.md file."
    )
    sys.exit(1)


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
        return time.perf_counter() - self.start


class FpGenerator(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def generate(self) -> "FpGenerationResult":
        """
        Run the generator, returning a FpGenerationResult.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        The name of the generator - this is used to filter generators to run.
        """
        pass

    @property
    def base_path(self) -> Path | None:
        """
        If this generator is usefully and uniquely mappable to a filesystem path, return it.
        (this mostly if to allow to filter libraries using shell path completion).

        Return None if the generator doesn't map to a filesystem path for some reason.
        """
        return None

    class GenerationError(Exception):
        """
        An exception that is raised when a generator fails to generate footprints.
        """

        pass

    class DiscoveryFactory(abc.ABC):
        """
        A class that discovers FpGenerators.
        """

        @abc.abstractmethod
        def discover(self) -> Generator["FpGenerator", None, None]:
            """
            Yield all generators found in "some context".

            For example, all generators found in a directory.
            """
            pass


class FpGenerationResult:
    """
    The result of a generation operation.

    Exentually, this will record all sorts of stats, like number of footprints generated,
    time taken, etc. But for now, with generate.sh generators, it's just a success flag.

    Some of this data by not be known by the generator itself (e.g. if the generator dies),
    so it is filled in by the runner.
    """

    generator: FpGenerator
    success: bool

    # An exception that was raised during generation, None if no exception
    exception: FpGenerator.GenerationError | None

    # Time taken to generate footprints, None if didn't start
    time: float | None

    # Number of series generated (None = FpGenerator didn't say)
    num_series: int | None
    # Number of footprints generated (None = FpGenerator didn't say)
    num_fps: int | None

    def __init__(self, generator: FpGenerator):
        self.generator = generator
        self.success = False
        self.time = 0
        self.num_series = None
        self.num_fps = None


class FpGenerateShGenerator(FpGenerator):
    """
    A generator that runs a generate.sh script.

    This is the most common type of generator as of early 2025, but eventually it
    can become a more "plugin-style" kind of generator using the FootprintGenerator
    class, without shelling out, which will allow richer generation capabilities such
    as parameter introspection (eventually leading to, say, KiCad integration).
    """

    # Path to the generate.sh script
    generate_sh: Path
    # Root path of scripts top level dir
    root_path: Path

    def __init__(self, root_path, generate_sh: Path):
        self.generate_sh = generate_sh
        self.root_path = root_path

    @property
    def base_path(self):
        return self.generate_sh.parent

    def generate(self, output_dir: Path | None) -> "FpGenerationResult":
        logging.info("Running generate.sh: %s" % self.generate_sh)

        cmd = ["sh", "-c", self.generate_sh.absolute().as_posix()]
        cwd = self.base_path

        env = os.environ.copy()
        if output_dir is not None:
            env.update({"KICAD_FP_GENERATOR_OUTPUT_DIR": output_dir})

        res = FpGenerationResult(self)

        try:
            subprocess.run(cmd, check=True, cwd=cwd, env=env)
            res.success = True
        except subprocess.CalledProcessError as e:
            res.exception = FpGenerator.GenerationError(
                f"Failed to run {self.generate_sh}: {e}"
            )

        # Calculating these is tricky, as there may be existing FPs in the directory
        # and generate.sh doesn't clear
        res.num_fps = None
        res.num_series = None
        return res

    @property
    def name(self):
        rel = self.generate_sh.parent.relative_to(self.root_path)
        return rel.as_posix()

    class DiscoveryFactory(FpGenerator.DiscoveryFactory):
        """
        Class to discover and construct FpGenerateShGenerator instances
        from files found under a root path.
        """

        root_path: Path

        def __init__(self, root_path):
            self.root_path = root_path

        def discover(self):
            """
            Yields all generators found under the root path
            """
            for gen_sh_path in self._find_shs():
                gen = FpGenerateShGenerator(self.root_path, gen_sh_path)
                yield gen

        SH_NAME = "generate.sh"

        def _find_shs(self):
            """
            Yields generate.sh filepaths under the root path
            """
            for dirpath, dirs, filenames in os.walk(self.root_path):
                for filename in filenames:
                    if filename == self.SH_NAME:
                        yield Path(dirpath) / self.SH_NAME


class GenerationFilter:
    """
    A filter that can be used to include or exclude libraries from generation.

    Eventually this will be an object that also handles series and footprints,
    but for now it's just libraries.
    """

    def __init__(self, lib_include: list[str], lib_exclude: list[str]):
        self.lib_include = lib_include
        self.lib_exclude = lib_exclude

    def matching_generators(self, lib: str, generators):
        """
        Yield all generators that match the filter.
        """

        # Resolve the current directory to a Path
        cwd = Path(os.curdir).absolute()

        def _gen_matches(gen: FpGenerator, pat: str):

            # Try a relative glob first
            if gen.base_path is not None:
                rel_base = gen.base_path.relative_to(cwd)

                if fnmatch.fnmatch(rel_base, Path(pat)):
                    return True

            # Try a match on just the name
            if fnmatch.fnmatch(gen.name, pat):
                return True

        def _matches_lib(gen: FpGenerator):

            included = True

            # No includes -> include all
            if self.lib_include:
                included = any(_gen_matches(gen, pat) for pat in self.lib_include)

            if included and self.lib_exclude:
                included = not any(_gen_matches(gen, pat) for pat in self.lib_exclude)

            return included

        if not self.lib_include and not self.lib_exclude:
            logging.info("No library filters specified, including all generators")
            yield from generators
            return

        for gen in generators:
            if _matches_lib(gen):
                yield gen


class GeneratorRunner:

    _generators: list[FpGenerator]
    output_dir: Path | None
    separate_outputs: bool

    def __init__(self, root, output_dir: Path | None):
        self.root = root
        self.output_dir = output_dir
        self.separate_outputs = False

        self._generators = []
        self._failures = []

        factories = [
            FpGenerateShGenerator.DiscoveryFactory(root),
        ]

        with Timer("Generator discovery"):
            # Discover generators
            for factory in factories:
                self._generators += list(factory.discover())

            logging.info("Discovered %d generators" % len(self._generators))

        # Prioritise generators that we know are slow
        # This is a bit of a hack and the real answer is to break the generators
        # up by series to keep all cores busy, but that needs generators to report
        # which series they generate.
        def _generator_sort_key(g):

            prio_prefixes = [
                "generator",  # the connector generator is slow
                "Pin-Headers",
                "Package_NoLead",
                "Connector_PinSocket",
                "Connector_Molex",
            ]

            for i, prefix in enumerate(prio_prefixes):
                if g.name.startswith(prefix):
                    return i
            # everything else just goes in whatever order
            return len(prio_prefixes)

        self._generators.sort(key=_generator_sort_key)

    def generate(self, filter: GenerationFilter, jobs: int) -> bool:
        """
        Generate footprints included by the filter.
        """

        gens = list(filter.matching_generators(filter, self._generators))

        logging.info("Generating footprints for %d libraries:" % len(gens))

        for g in gens:
            logging.info(f"  - {g.name}")

        def args_for_gen(g):
            gen_output_dir = self.output_dir
            # If we're not merging outputs (e.g. into kicad-footprints repo),
            # and not in-place, distribute the outputs into the same directory
            # structure as the generate.sh scripts themselves
            if self.separate_outputs and gen_output_dir:
                rel_path = g.base_path.relative_to(self.root)
                gen_output_dir /= rel_path

            return (g, gen_output_dir)

        results = []

        if jobs == 1 or len(gens) == 1:
            # In-process generation when single-threaded case for easier debugging
            # (generators may still shell out if they want, can't help that)
            for g in gens:
                result = self._do_generate(*args_for_gen(g))
                results.append(result)
        else:
            # Multiprocess jobs of 'None' means use the number of CPUs
            mp_jobs = jobs if jobs else None

            with Pool(mp_jobs) as p:
                results = p.starmap(self._do_generate, (args_for_gen(g) for g in gens))

        # Process results

        print("")
        print(self._format_results(results))
        print("")

        # Last of all: print the failed generators so they are easy to find in the log
        self._print_failures(results)

        return all(r.success for r in results)

    @staticmethod
    def _do_generate(gen: FpGenerator, output_dir: Path | None) -> FpGenerationResult:

        with Timer(f"Generating {gen.name}") as timer:
            result = gen.generate(output_dir)
            result.time = timer.duration

        return result

    @staticmethod
    def _format_results(results):
        rows = []

        for result in results:
            rows.append(
                (
                    result.generator.name,
                    "Success" if result.success else "Failure",
                    result.time,
                    result.num_series if result.num_series else "-",
                    result.num_fps if result.num_fps else "-",
                )
            )

        # Sort by name
        rows.sort(key=lambda x: x[0])

        rows.append(tabulate.SEPARATING_LINE)

        success = len([r for r in results if r.success])

        total_series = sum(r.num_series for r in results if r.num_series)
        total_fps = sum(r.num_fps for r in results if r.num_fps)

        rows.append(
            (
                "TOTAL",
                f"{success}/{len(results)}",
                sum(r.time for r in results),
                total_series if total_series else "-",
                total_fps if total_fps else "-",
            )
        )

        headers = ["Generator", "Result", "Time (s)", "Series", "Footprints"]

        return tabulate.tabulate(rows, headers=headers, floatfmt=".2f")

    @staticmethod
    def _print_failures(results):

        failed_gens = []

        for result in results:
            if not result.success:

                print(result)
                print(result.exception)

                if result.exception:

                    # This only works on Python 3.13+ but it does help readability
                    # if it works.
                    print_kwargs = {}
                    if sys.version_info >= (3, 13):
                        print_kwargs["colorize"] = True

                    traceback.print_exception(result.exception, **print_kwargs)

                failed_gens.append(result.generator)

        if failed_gens:
            logging.error(
                f"Generation failed for the following {len(failed_gens)} generators:"
            )

            for g in failed_gens:
                logging.error(f"  - {g.name}")
        else:
            logging.info(f"Generation completed with no failures.")


if __name__ == "__main__":

    import argparse
    import os

    parser = argparse.ArgumentParser(description="Generate KiCad footprints")

    parser.add_argument(
        "-l",
        "--library",
        type=str,
        nargs="*",
        default=[],
        help="Generator library name or globs (default: all)",
    )
    parser.add_argument(
        "-x",
        "--library-exclude",
        type=str,
        nargs="*",
        default=[],
        help="Exclude generator library name or globs (default: none)",
    )
    parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        help="List available generators and exit. Filter with --library.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Output directory for generated footprints",
    )
    parser.add_argument(
        "-S",
        "--separate-outputs",
        action="store_true",
        help="Place each generator's output in a separate directory",
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

    # This has to be an absolute path because we run the generate.sh scripts
    # from their own directories.
    output_dir = Path(args.output_dir).absolute() if args.output_dir else None

    generator = GeneratorRunner(root_dir, output_dir)

    generator.separate_outputs = args.separate_outputs

    filter = GenerationFilter(args.library, args.library_exclude)

    if args.list:
        matching = list(filter.matching_generators(filter, generator._generators))
        matching.sort(key=lambda g: g.name)
        for g in matching:
            print(g.name)
        sys.exit(0)

    success = generator.generate(filter, jobs=args.jobs)

    ret_code = 0 if success else 2

    if ret_code != 0:
        logging.error(f"Generation failed, returning exit code {ret_code}")
    else:
        logging.info(f"Generation successful, returning exit code {ret_code}")

    sys.exit(ret_code)
