
import unittest

from pathlib import Path
import os

from KicadModTree.KicadFileHandler import KicadFileHandler


class SerialisationTest(unittest.TestCase):

    def setUp(self, testcase_file: str, test_data: Path):
        """
        Set up a test case with the given testcase file and test data directory.

        :param testcase_file: The file of the test case, which the test data directory is relative to
        :param test_data: The test data directory
        """

        test_dir = os.path.dirname(os.path.realpath(testcase_file))
        self.test_data_dir = os.path.join(test_dir, test_data)

        self.maxDiff = None

        self.write_golden_files = os.getenv('WRITE_GOLDEN_FILES', False)

    def assert_serialises_as(self, kicad_mod, exp_content_file: Path):
        """
        Serialise the given kicad_mod and compare it to the expected value.

        If the WRITE_GOLDEN_FILES environment variable is set, the expected value will be
        written to the test data directory instead of being compared.

        :param kicad_mod: The kicad_mod to serialise
        :param expected: The expected serialised value
        """
        file_handler = KicadFileHandler(kicad_mod)

        rendered = file_handler.serialize(timestamp=0)

        exp_file = os.path.join(self.test_data_dir, exp_content_file)

        if self.write_golden_files:
            with open(exp_file, 'w') as file:
                file.write(rendered)
        else:
            # load the expected file and do the test
            expected_content = open(exp_file, 'r').read()

            expected_content = expected_content.strip()
            assert rendered == expected_content
