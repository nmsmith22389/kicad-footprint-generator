

from pathlib import Path
import os
import yaml
import argparse
import logging

from KicadModTree import Footprint, KicadFileHandler, Model
from scripts.tools.global_config_files.global_config import GlobalConfig
from scripts.tools.dict_tools import dictInherit


class FootprintGenerator:

    # The output path (the directory that contains .pretty libraries)
    output_path: Path

    # The global config (e.g. KLC settings)
    global_config: GlobalConfig

    def __init__(self, output_dir: Path, global_config: GlobalConfig):
        self.output_path = output_dir
        self.global_config = global_config

    def write_footprint(self, kicad_mod: Footprint, library_name: str):
        output_library_path = self.output_path / f'{library_name}.pretty'

        os.makedirs(output_library_path, exist_ok=True)

        # output kicad model
        file_handler = KicadFileHandler(kicad_mod)
        file_handler.writeFile(output_library_path / f'{kicad_mod.name}.kicad_mod')
        
    def get_standard_3d_model_path(self, library_name: str, model_name: str) -> str:
        """
        Get the path of the the "usual" 3D model (with the global config path)
        for the given footprint
        """
        assert ".wrl" not in model_name, f"model_name should not contain the .wrl extension: {model_name}"
        assert "/" not in model_name, f"model_name should be only the model name, not a path: {model_name}"

        prefix = self.global_config.model_3d_prefix.rstrip("/")
        lib3d_dir = f"{library_name}.3dshapes"

        return f"{prefix}/{lib3d_dir}/{model_name}.wrl"

    def add_standard_3d_model_to_footprint(self, kicad_mod: Footprint, library_name: str,
                                           model_name: str):
        """
        Add the "usual" 3D model (with the global config path) to the given footprint
        """
        kicad_mod.append(Model(
            filename=self.get_standard_3d_model_path(library_name, model_name),
        ))

    @classmethod
    def add_standard_arguments(self, parser, file_autofind: bool=False) -> argparse.Namespace:
        """
        Helper function to add "standard" argument to a command line parser,
        which can then be used to init a FootprintGenerator.
        """
        parser.add_argument('-o', '--output-dir', type=Path,
                            default='.',
                            help='Sets the directory to which to write the generated footprints')

        if file_autofind:
            parser.add_argument('files', metavar='file', type=str, nargs='*',
                                help='list of files holding information about what devices should be created.' +
                                     ' If none are given, all .yaml files in the current directory are used (recursively).')

        parser.add_argument('-v', '--verbose', action='count', default=0,
                            help='Set debug level, use -vv for more debug.')

        args = parser.parse_args()

        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose > 1:
            logging.basicConfig(level=logging.DEBUG)

        return args

    @classmethod
    def run_on_files(self, generator, args: argparse.Namespace,
                     file_autofind_dir: str='.', **kwargs):

        # Load global config
        global_config = GlobalConfig.load_from_file(args.global_config)

        # If no files are given, find all YAML files in the current
        # directory recursively
        if not args.files:
            logging.info(f"No files given, searching for .yaml files in {file_autofind_dir}")
            args.files = list(Path(file_autofind_dir).rglob('*.yaml'))

        for filepath in args.files:
            generator_instance = generator(output_dir=args.output_dir,
                                           global_config=global_config,
                                           **kwargs)

            with open(filepath, 'r', encoding="utf-8") as command_stream:
                try:
                    cmd_file = yaml.safe_load(command_stream)
                except yaml.YAMLError as exc:
                    print(exc)

            dictInherit(cmd_file)

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