from KicadModTree.KicadFileHandler import KicadFileHandler


def assert_serialises_as(kicad_mod, expected, dump=False):
    """
    Serialise the given kicad_mod and compare it to the expected value.

    If dump is True, print the serialised value to stdout.

    :param kicad_mod: The kicad_mod to serialise
    :param expected: The expected serialised value
    :param dump: If True, print the serialised value to stdout
    """
    file_handler = KicadFileHandler(kicad_mod)

    rendered = file_handler.serialize(timestamp=0)

    # can be used to get an updated version
    # but make sure the new one is right!
    if dump:
        print(rendered)

    expected = expected.strip()
    assert rendered == expected
