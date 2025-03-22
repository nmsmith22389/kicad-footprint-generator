from pathlib import Path
import os
import yaml
import argparse
import logging
from importlib import resources
from typing import Optional

from KicadModTree import Footprint, KicadPrettyLibrary, Model
from scripts.tools.global_config_files.global_config import GlobalConfig
from kilibs.util import dict_tools


class FootprintGenerator:

    # The output path (the directory that contains .pretty libraries)
    output_path: Path | None

    # The global config (e.g. KLC settings)
    global_config: GlobalConfig

    def __init__(self, output_dir: Path | None, global_config: GlobalConfig):
        self.output_path = output_dir
        self.global_config = global_config

    def write_footprint(self, kicad_mod: Footprint, library_name: str):

        # This is the point in future where the FootprintGenerator can dispatch
        # to the IPC API instead of writing to disk ourselves.
        output_library = KicadPrettyLibrary(library_name, output_dir=self.output_path)
        output_library.save(kicad_mod)

    def get_standard_3d_model_path(self, library_name: str, model_name: str) -> str:
        """
        Get the path of the the "usual" 3D model (with the global config path)
        for the given footprint
        """
        assert self.global_config.model_3d_suffix not in model_name, f"model_name should not contain the {self.global_config.model_3d_suffix} extension: {model_name}"
        assert "/" not in model_name, f"model_name should be only the model name, not a path: {model_name}"

        prefix = self.global_config.model_3d_prefix.rstrip("/")
        lib3d_dir = f"{library_name}.3dshapes"

        return f"{prefix}/{lib3d_dir}/{model_name}{self.global_config.model_3d_suffix}"

    def add_standard_3d_model_to_footprint(self, kicad_mod: Footprint, library_name: str,
                                           model_name: str):
        """
        Add the "usual" 3D model (with the global config path) to the given footprint
        """
        kicad_mod.append(Model(
            filename=self.get_standard_3d_model_path(library_name, model_name),
        ))

    @classmethod
    def add_standard_arguments(
        self,
        parser,
        file_autofind: bool = False,
    ) -> argparse.Namespace:
        """
        Helper function to add "standard" argument to a command line parser,
        which can then be used to init a FootprintGenerator.
        """
        parser.add_argument('-o', '--output-dir', type=Path,
                            help='Sets the directory to which to write the generated footprints')

        if file_autofind:
            parser.add_argument('files', metavar='file', type=str, nargs='*',
                                help='list of files holding information about what devices should be created.' +
                                     ' If none are given, all .yaml files in the current directory are used (recursively).')

        parser.add_argument(
            "--global-config",
            type=Path,
            help="the config file defining how the footprint will look like. (KLC)",
        )

        parser.add_argument('-v', '--verbose', action='count', default=0,
                            help='Set debug level, use -vv for more debug.')

        args = parser.parse_args()

        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose > 1:
            logging.basicConfig(level=logging.DEBUG)

        if args.global_config is None:
            # If the user doesn't provide a global config file, use the default one
            # provided in the package data
            default_global_config_name = "config_KLCv3.0.yaml"

            with resources.path(
                "scripts.tools.global_config_files", default_global_config_name
            ) as default_global_config:
                args.global_config_file = default_global_config
        else:
            args.global_config_file = args.global_config

        # Some generators still load the global config themselves as a dict and then
        # extend it, which isn't very type-safe. But for now, allow access to both
        # the filename (so they can do that themselves) as well as the GlobalConfig
        # object which provides validation, type-checking, utility functions, etc.
        args.global_config = GlobalConfig.load_from_file(args.global_config_file)

        return args

    @classmethod
    def run_on_files(self, generator, args: argparse.Namespace,
                     file_autofind_dir: str='.', **kwargs):

        # If no files are given, find all YAML files in the current
        # directory recursively
        if not args.files:
            logging.info(f"No files given, searching for .yaml files in {file_autofind_dir}")
            args.files = list(Path(file_autofind_dir).rglob('*.yaml'))

        for filepath in args.files:
            generator_instance = generator(output_dir=args.output_dir,
                                           global_config=args.global_config,
                                           **kwargs)

            with open(filepath, 'r', encoding="utf-8") as command_stream:
                try:
                    cmd_file = yaml.safe_load(command_stream)
                except yaml.YAMLError as exc:
                    print(exc)

            # Skip empty/comment-only files
            if cmd_file is None:
                continue

            dict_tools.dictInherit(cmd_file)

            # The def file header, if there is one
            try:
                header = cmd_file.pop('FileHeader')
            except KeyError:
                header = None

            for pkg in cmd_file:
                logging.info("Generating part for parameter set {}".format(pkg))
                generator_instance.generateFootprint(cmd_file[pkg],
                                                     pkg_id=pkg,
                                                     header_info=header)
