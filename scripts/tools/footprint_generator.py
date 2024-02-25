

from pathlib import Path
import os

from KicadModTree import Footprint, KicadFileHandler, Model
from scripts.tools.global_config_files.global_config import GlobalConfig


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

    def add_standard_3d_model_to_footprint(self, kicad_mod: Footprint, library_name: str,
                                           model_name: str):
        """
        Add the "usual" 3D model (with the global config path) to the given footprint
        """

        prefix = self.global_config.model_3d_prefix.rstrip("/")
        lib3d_dir = f"{library_name}.3dshapes"

        kicad_mod.append(Model(
            filename=f"{prefix}/{lib3d_dir}/{model_name}.wrl",
        ))

    @classmethod
    def add_standard_arguments(self, parser):
        """
        Helper function to add "standard" argument to a command line parser,
        which can then be used to init a FootprintGenerator.
        """
        parser.add_argument('-o', '--output-dir', type=Path,
                            help='Sets the directory to which to write the generated footprints')
